#!/usr/bin/env python3
"""hca-adapter.py — the ONLY module that talks to Hypercore (read-only; live GraphQL via hca-live.py).

This is the single client/adapter isolation pillar of acos-hypercore-ask. Everything
downstream depends on the CONTRACT below, not on the live API. That is what makes the
whole skill buildable and testable on fixtures before credentials exist.

CONTRACT (read-only — tech_prd.md §2, data-model.md invariant 6):
    is_live() -> bool
    get_entity(entity_type, id, *, params=None) -> RawApiResponse
    list_entities(entity_type, *, filters=None, cursor=None) -> RawApiResponse  (paginated)
    get_schema(entity_type) -> SchemaDescriptor
    subscribe_events(...) -> EventStream            (signature only; TODO)

There is intentionally NO create/update/delete/post/put/patch/write/mutate method on
the contract. Read-only is enforced (a) by OMISSION and (b) by a guard test in
.claude/scripts/tests/test_hca_adapter.py that introspects the contract and rejects any
mutating verb. See README + SKILL.md.

BACKENDS:
    FixtureBackend  -> ACTIVE NOW. Serves canned RawApiResponse JSON from the skill
                       fixtures/ dir. Deterministic. backend label = "fixture".
    LiveBackend     -> ACTIVE — real, read-only GraphQL client (live access verified
                       2026-06-18). Reads credentials from env (Doppler injects them at
                       runtime); the network transport lives in the sibling hca-live.py,
                       imported LAZILY. backend label = "live". See SLICE-HCA-02 note below.

DEGRADATION (data-model.md invariant 7): when is_live() is False and live data is
requested, the public surface returns an explicit NO_LIVE_DATA envelope (and the
HypercoreAdapter convenience surface raises NoLiveDataError) — never a fabricated
record, never a crash.

GROUND RULES (memory/decisions/2026-06-18-hca-build-ground-rules.md):
    - Python 3 stdlib ONLY. No third-party deps.
    - NO network import is present in THIS module: there is deliberately NO top-level
      `urllib`, `http`, `http.client`, `socket`, `ssl`, or `requests` import. The real
      GraphQL transport (TLS 1.2+) lives in the sibling module `hca-live.py` and is
      imported LAZILY by LiveBackend's methods — so the FixtureBackend path can never
      reach a socket, and the no-network-import invariant for this module holds.
    - LiveBackend network code is reachable ONLY when is_live() is True (creds present).
    - Subscription-only Claude: this module makes no model calls; never ANTHROPIC_API_KEY.
    - No credential or URL is stored in this file; LiveBackend reads them from env only.

SLICE-HCA-02 UPGRADE (2026-06-18): LiveBackend is now a REAL read-only GraphQL client
(live access verified). It performs the 3-step JWT handshake, enforces TLS 1.2+, walks
OFFSET pagination (skip/limit) to COMPLETION, validates fields against the introspected
schema before sending, and refuses any non-`query` operation at the operation level.
"""

from __future__ import annotations

import abc
import inspect
import json
import os
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Errors & sentinels
# ---------------------------------------------------------------------------

NO_LIVE_DATA = "NO_LIVE_DATA"


class NoLiveDataError(RuntimeError):
    """Raised when live Hypercore data is requested but the adapter is not live.

    Carries the explicit NO_LIVE_DATA envelope so callers can degrade gracefully
    instead of fabricating. NEVER raised on the FixtureBackend happy path.
    """

    def __init__(self, message: str, envelope: Optional[dict] = None):
        super().__init__(message)
        self.envelope = envelope or no_live_data_envelope(reason=message)


def no_live_data_envelope(reason: str = "Hypercore access not yet provisioned",
                          *, entity_type: Optional[str] = None,
                          request: Optional[dict] = None) -> dict:
    """Build the explicit, structured NO_LIVE_DATA result envelope (no fabrication)."""
    return {
        "state": NO_LIVE_DATA,
        "live": False,
        "data": None,
        "reason": reason,
        "entity_type": entity_type,
        "request": request or {},
        "message": "no live data — Hypercore access not yet provisioned",
    }


class SchemaDescriptor:
    """Expected schema for an entity type (data-model.md B7). Loaded from schemas/."""

    def __init__(self, entity_type: str, expected_fields: dict, version: str,
                 required_fields: Optional[list] = None, raw: Optional[dict] = None):
        self.entity_type = entity_type
        self.expected_fields = expected_fields
        self.version = version
        self.required_fields = required_fields or []
        self.drift_detected = False
        self.drift_details: list = []
        self.raw = raw or {}

    def to_dict(self) -> dict:
        return {
            "entity_type": self.entity_type,
            "expected_fields": self.expected_fields,
            "version": self.version,
            "required_fields": self.required_fields,
            "drift_detected": self.drift_detected,
            "drift_details": self.drift_details,
        }


# ---------------------------------------------------------------------------
# RawApiResponse shape helper (Tier-1 truth — data-model.md B1)
# ---------------------------------------------------------------------------

_RAW_RESPONSE_FIELDS = (
    "raw_response_id", "endpoint", "request_params", "timestamp",
    "http_status", "cursor", "reported_total", "body", "backend",
)


def make_raw_api_response(*, raw_response_id: str, endpoint: str, request_params: dict,
                          timestamp: str, http_status: int, cursor: Optional[str],
                          reported_total: Optional[int], body: Any, backend: str) -> dict:
    """Wrap a payload into the canonical RawApiResponse-shaped dict (Tier-1 truth)."""
    return {
        "raw_response_id": raw_response_id,
        "endpoint": endpoint,
        "request_params": request_params,
        "timestamp": timestamp,
        "http_status": http_status,
        "cursor": cursor,
        "reported_total": reported_total,
        "body": body,
        "backend": backend,
    }


# ---------------------------------------------------------------------------
# Path resolution (no git dependency — matches ACOS hook policy)
# ---------------------------------------------------------------------------

def _repo_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))          # .../.claude/scripts
    return os.path.abspath(os.path.join(here, os.pardir, os.pardir))


def _skill_dir() -> str:
    return os.path.join(_repo_root(), ".claude", "skills", "acos-hypercore-ask")


def _default_fixtures_dir() -> str:
    return os.path.join(_skill_dir(), "fixtures")


def _default_schemas_dir() -> str:
    return os.path.join(_skill_dir(), "schemas")


# ---------------------------------------------------------------------------
# Contract (read-only). Read methods ONLY — no mutating verb exists by design.
# ---------------------------------------------------------------------------

class HypercoreBackend(abc.ABC):
    """Read-only Hypercore backend contract.

    Implementations: FixtureBackend (active), LiveBackend (stubbed). The set of
    abstract methods below is the ENTIRE contract surface — it is read-only by
    omission. No create/update/delete/post/put/patch/write/mutate method is declared
    here or on any subclass; a guard test enforces this structurally.
    """

    # --- read methods only -------------------------------------------------
    @abc.abstractmethod
    def is_live(self) -> bool:
        """True only when credentials + endpoint config are present and valid."""

    @abc.abstractmethod
    def get_entity(self, entity_type: str, id: str, *, params: Optional[dict] = None) -> dict:
        """Single-record read -> RawApiResponse-shaped dict."""

    @abc.abstractmethod
    def list_entities(self, entity_type: str, *, filters: Optional[dict] = None,
                      cursor: Optional[str] = None) -> dict:
        """Paginated read -> RawApiResponse-shaped dict (carries cursor + reported_total)."""

    @abc.abstractmethod
    def get_schema(self, entity_type: str) -> SchemaDescriptor:
        """Declared/expected schema for the entity type (drift detection)."""

    @abc.abstractmethod
    def subscribe_events(self, entity_type: Optional[str] = None, *,
                         callback=None, poll_interval_s: Optional[int] = None):
        """Webhook/polling hook for freshness invalidation. Signature only (TODO)."""


# Canonical read-only contract surface. The guard test asserts every public method
# of HypercoreBackend / its subclasses is in this allow-list (no mutating verb).
READ_ONLY_CONTRACT_METHODS = frozenset({
    "is_live",
    "get_entity",
    "list_entities",
    "get_schema",
    "subscribe_events",
})

# Verbs that MUST NOT appear as a method name anywhere on the contract / backends.
FORBIDDEN_MUTATING_VERBS = (
    "create", "update", "delete", "post", "put", "patch", "write", "mutate",
    "insert", "remove", "drop", "set", "save", "upsert", "modify", "edit", "add",
)




# ---------------------------------------------------------------------------
# Belt-and-suspenders read-only guard (SLICE-HCA-10 reinforcement)
# ---------------------------------------------------------------------------

def assert_read_only(*classes) -> None:
    """Assert that no public method on any of the given classes/instances has a
    name that contains a forbidden mutating verb.

    Intended as a standing quality gate called from tests and optionally at
    module import time. Raises ReadOnlyViolationError on any match.
    This is the belt-and-suspenders check on top of the contract-by-omission
    approach (READ_ONLY_CONTRACT_METHODS allow-list).
    """
    for cls in classes:
        for name, _ in inspect.getmembers(cls, predicate=callable):
            if name.startswith("_"):
                continue
            name_lo = name.lower()
            for verb in FORBIDDEN_MUTATING_VERBS:
                if verb in name_lo:
                    raise ReadOnlyViolationError(
                        f"Read-only violation: {cls!r} exposes public method ''{name}''"
                        f" which contains the mutating verb ''{verb}''"
                    )


class ReadOnlyViolationError(RuntimeError):
    """Raised by assert_read_only() when a mutating method name is detected.

    This is a STRUCTURAL integrity failure (not a runtime data error) — it
    means something added a forbidden method to the contract or a backend.
    """


# ---------------------------------------------------------------------------
# RBAC scope pass-through hook (SLICE-HCA-10)
# ---------------------------------------------------------------------------

class RBACScope:
    """Lightweight holder for an RBAC scope / role.

    Passes an optional OAuth scope string and/or role tag through to the
    live transport (carried on the adapter call; never mutates Hypercore).
    The contract is unchanged — this is an OPTIONAL advisory annotation.

    When scope is None, the transport uses whatever the bearer token already
    grants (default behavior; no functional change).
    """
    __slots__ = ("scope", "role", "source")

    def __init__(self, scope: Optional[str] = None, role: Optional[str] = None,
                 source: str = "caller"):
        object.__setattr__(self, "scope", scope)
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "source", source)

    def __setattr__(self, name, value):
        raise AttributeError("RBACScope is immutable")

    def __repr__(self) -> str:
        return f"RBACScope(scope={self.scope!r}, role={self.role!r}, source={self.source!r})"

    def to_dict(self) -> dict:
        return {"scope": self.scope, "role": self.role, "source": self.source}


def rbac_scope_hook(scope: Optional["RBACScope"] = None,
                    *, params: Optional[dict] = None) -> dict:
    """Merge the RBAC scope into the request params dict (read-only pass-through).

    Called by the adapter BEFORE forwarding a read to the live transport.
    Returns an updated params copy with the scope annotation injected under
    the key '_rbac_scope'. The live transport can use this to append an
     header or a GraphQL variable — or ignore it if not yet wired.

    NO mutation of Hypercore state. Pure request annotation.

    Parameters
    ----------
    scope : RBACScope | None
        The caller-supplied RBAC context. When None, params are returned unchanged.
    params : dict | None
        The existing request params dict. A shallow copy is made; the original
        is never mutated.

    Returns
    -------
    dict
        Updated params copy. Always returns a dict (never None).
    """
    out = dict(params or {})
    if scope is not None:
        out["_rbac_scope"] = scope.to_dict()
    return out


# ---------------------------------------------------------------------------
# Freshness-invalidation hook (SLICE-HCA-11 — READ-ONLY)
# ---------------------------------------------------------------------------

class FreshnessInvalidationHook:
    """Webhook stub + polling-interval fallback for cache-freshness invalidation.

    This hook is the read-only invalidation surface wired on the adapter.
    It MARKS cached entries stale; it NEVER writes to Hypercore.

    Two modes:
      Webhook  — on_change_event(event) is called when Hypercore emits a
                 change notification. It records which entity+id are stale in
                 a small in-memory set. The cache layer consults this set via
                 is_stale() before serving a cached entry.

      Polling  — poll() can be called on a schedule (e.g. a background thread)
                 to mark ALL cached entries for an entity_type stale based on a
                 configurable max_age_seconds. The cache layer then refetches on
                 next access.

    READ-ONLY invariant: this class never calls any adapter/backend write method
    and never sends any request to Hypercore. It only updates the in-process
    stale set.

    Integration: the adapter passes this hook to the cache layer; the cache calls
    is_stale(entity_type, id) before returning a cached result. This replaces the
    always-serve behaviour with a proactive refresh signal.
    """

    def __init__(self, *, default_poll_interval_s: int = 300):
        # entity_type -> set of stale ids (or None meaning "all stale")
        self._stale: dict = {}
        self._default_poll_interval_s = default_poll_interval_s
        # For polling: entity_type -> (last_polled_ts, max_age_s)
        self._poll_state: dict = {}

    # --- webhook stub --------------------------------------------------------
    def on_change_event(self, event: dict) -> None:
        """Handle a Hypercore change event and mark the affected entity stale.

        Expected event shape (Hypercore webhook / subscription payload):
            {"entity_type": "loan", "id": "L-001", "change_type": "updated"}

        The id field may be absent for bulk changes — in that case ALL entries
        for the entity_type are marked stale (conservative / safe).

        READ-ONLY: this method modifies ONLY the in-process stale set; it
        never calls any Hypercore write endpoint or any adapter mutating method.
        """
        if not isinstance(event, dict):
            return
        entity_type = event.get("entity_type") or event.get("entityType") or ""
        entity_id = event.get("id") or event.get("entityId")
        if not entity_type:
            return  # malformed event; ignore
        stale_ids = self._stale.setdefault(entity_type, set())
        if entity_id:
            stale_ids.add(str(entity_id))
        else:
            # No specific id -> mark entity_type entirely stale (None sentinel)
            self._stale[entity_type] = None  # type: ignore[assignment]

    # --- polling fallback ----------------------------------------------------
    def poll(self, entity_type: str, *, max_age_s: int = 0,
             now_ts: Optional[float] = None) -> int:
        """Mark cached entries for entity_type stale based on age.

        This is the polling-fallback path: if the webhook is unavailable, a
        background caller invokes poll() on a schedule. Any cached entry whose
        age exceeds max_age_s is considered stale. Returns the number of entries
        newly marked stale (0 or a sentinel count for 'all').

        READ-ONLY: marks stale in the in-process set; never calls Hypercore.

        Parameters
        ----------
        entity_type : str
            The entity class to age-out (e.g. 'loan').
        max_age_s : int
            If 0 (default), mark ALL entries for this entity_type stale immediately
            (a conservative flush). If > 0, only mark stale if last_polled elapsed
            time > max_age_s.
        now_ts : float | None
            Override for the current time (float Unix epoch; for testing).

        Returns
        -------
        int
            Number of entity IDs newly marked stale (or -1 if all were marked).
        """
        import time as _time
        now = now_ts if now_ts is not None else _time.time()
        last_polled, _ = self._poll_state.get(entity_type, (0.0, max_age_s))
        elapsed = now - last_polled
        if max_age_s > 0 and elapsed < max_age_s:
            return 0  # not yet due
        # Mark all entries for entity_type stale (bulk poll: no per-id resolution).
        prev = self._stale.get(entity_type)
        prev_count = len(prev) if isinstance(prev, set) else 0
        self._stale[entity_type] = None   # type: ignore[assignment]
        self._poll_state[entity_type] = (now, max_age_s)
        return -1 if prev is None else prev_count

    # --- cache consult -------------------------------------------------------
    def is_stale(self, entity_type: str, entity_id: Optional[str] = None) -> bool:
        """Return True if the given entity (or any entry for the type) is marked stale.

        Called by the cache layer before returning a cached entry. A result of
        True means the cache must refetch before serving; it MUST NOT serve stale.
        """
        stale_val = self._stale.get(entity_type)
        if stale_val is None and entity_type in self._stale:
            # None sentinel means ALL entries for this type are stale
            return True
        if isinstance(stale_val, set):
            if entity_id is not None:
                return str(entity_id) in stale_val
            return bool(stale_val)  # any stale id present => True
        return False

    def clear_stale(self, entity_type: str, entity_id: Optional[str] = None) -> None:
        """Clear the stale marker after a successful refetch (read-only maintenance)."""
        if entity_id is not None:
            ids = self._stale.get(entity_type)
            if isinstance(ids, set):
                ids.discard(str(entity_id))
        else:
            self._stale.pop(entity_type, None)

    def stale_snapshot(self) -> dict:
        """Return a loggable copy of the current stale set (no PII — only type/id tokens)."""
        out = {}
        for k, v in self._stale.items():
            out[k] = "ALL" if v is None else sorted(v)
        return out

# ---------------------------------------------------------------------------
# FixtureBackend — ACTIVE. Loads canned RawApiResponse JSON from fixtures/.
# ---------------------------------------------------------------------------

class FixtureBackend(HypercoreBackend):
    """Serves deterministic canned responses from the fixtures/ directory.

    Fixture filename convention:
        <entity_type>__<id>.json                 single record  (e.g. loan__L-001.json)
        list_<entity_type>__<pagekey>.json       paginated list page
    Each fixture carries endpoint/request_params/timestamp/http_status/cursor/
    reported_total/body. FixtureBackend wraps each into the RawApiResponse shape and
    stamps backend="fixture". NO network call is made on this path.
    """

    BACKEND_LABEL = "fixture"

    def __init__(self, fixtures_dir: Optional[str] = None,
                 schemas_dir: Optional[str] = None):
        self.fixtures_dir = fixtures_dir or _default_fixtures_dir()
        self.schemas_dir = schemas_dir or _default_schemas_dir()

    # --- contract impl -----------------------------------------------------
    def is_live(self) -> bool:
        # Fixtures are never "live" — they are clearly labeled fixture data.
        return False

    def get_entity(self, entity_type: str, id: str, *, params: Optional[dict] = None) -> dict:
        fname = f"{entity_type}__{id}.json"
        fx = self._load_fixture(fname)
        if fx is None:
            raise FileNotFoundError(
                f"no fixture for entity_type={entity_type!r} id={id!r} "
                f"(expected {fname} in {self.fixtures_dir})"
            )
        return self._wrap(fx, raw_response_id=f"fixture:{entity_type}:{id}",
                          request_params=params or fx.get("request_params", {"id": id}))

    def list_entities(self, entity_type: str, *, filters: Optional[dict] = None,
                      cursor: Optional[str] = None) -> dict:
        """Cursor-based paging over fixture pages.

        Page selection:
          - cursor is None -> first page  (list_<entity_type>__page1.json), unless a
            filter selects a named adversarial variant (e.g. _truncated).
          - cursor set     -> find the page whose returned cursor equals it.
        """
        variant = (filters or {}).get("variant")  # e.g. "truncated" for adversarial test
        prefix = f"list_{entity_type}"
        if variant:
            prefix = f"list_{entity_type}_{variant}"

        page_fx = self._select_page(prefix, cursor)
        if page_fx is None:
            raise FileNotFoundError(
                f"no list fixture page for entity_type={entity_type!r} "
                f"variant={variant!r} cursor={cursor!r} (prefix {prefix} in {self.fixtures_dir})"
            )
        rid = f"fixture:list:{entity_type}:{page_fx.get('page_key', 'page1')}"
        req = {"filters": filters or {}, "cursor": cursor}
        return self._wrap(page_fx, raw_response_id=rid, request_params=req)

    def get_schema(self, entity_type: str) -> SchemaDescriptor:
        path = os.path.join(self.schemas_dir, f"{entity_type}.schema.json")
        if not os.path.isfile(path):
            raise FileNotFoundError(f"no schema for entity_type={entity_type!r} (expected {path})")
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        return SchemaDescriptor(
            entity_type=raw.get("entity_type", entity_type),
            expected_fields=raw.get("expected_fields", {}),
            version=raw.get("version", "unknown"),
            required_fields=raw.get("required_fields", []),
            raw=raw,
        )

    def subscribe_events(self, entity_type: Optional[str] = None, *,
                         callback=None, poll_interval_s: Optional[int] = None):
        # Fixtures emit no events. Real freshness-invalidation hook is TODO (SLICE-HCA-08).
        raise NotImplementedError(
            "subscribe_events: fixture backend emits no events; "
            "live polling/webhook hook is TODO (SLICE-HCA-08)"
        )

    # --- helpers -----------------------------------------------------------
    def _load_fixture(self, filename: str) -> Optional[dict]:
        path = os.path.join(self.fixtures_dir, filename)
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def _select_page(self, prefix: str, cursor: Optional[str]) -> Optional[dict]:
        pages = []
        if os.path.isdir(self.fixtures_dir):
            for name in sorted(os.listdir(self.fixtures_dir)):
                if name.startswith(prefix + "__") and name.endswith(".json"):
                    fx = self._load_fixture(name)
                    if fx is not None:
                        pages.append(fx)
        if not pages:
            return None
        if cursor is None:
            # first page = the one whose inbound request cursor is null/absent
            for fx in pages:
                rp = fx.get("request_params", {})
                if rp.get("cursor") in (None, ""):
                    return fx
            return pages[0]
        # subsequent page = the one whose inbound request cursor matches
        for fx in pages:
            rp = fx.get("request_params", {})
            if rp.get("cursor") == cursor:
                return fx
        return None

    def _wrap(self, fx: dict, *, raw_response_id: str, request_params: dict) -> dict:
        return make_raw_api_response(
            raw_response_id=raw_response_id,
            endpoint=fx.get("endpoint", "FIXTURE"),
            request_params=request_params,
            timestamp=fx.get("timestamp", "1970-01-01T00:00:00Z"),
            http_status=fx.get("http_status", 200),
            cursor=fx.get("cursor"),
            reported_total=fx.get("reported_total"),
            body=fx.get("body"),
            backend=self.BACKEND_LABEL,
        )


# ---------------------------------------------------------------------------
# LiveBackend — REAL read-only GraphQL client (live access verified 2026-06-18).
# Network code lives in the sibling module hca-live.py, imported LAZILY below.
# ---------------------------------------------------------------------------

def _load_hca_secrets():
    """Load the sibling credential module hca-secrets.py (hyphenated filename).

    hca-secrets.py is the SINGLE SOURCE OF TRUTH for credential env var NAMES and the
    is_provisioned() check. Loaded via importlib (matching the _load_hca_live seam) and
    cached under the stable name "hca_secrets" in sys.modules so every caller and the
    tests share ONE module instance. No network/secret value is read at import time.
    """
    import sys
    import importlib.util
    cached = sys.modules.get("hca_secrets")
    if cached is not None:
        return cached
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "hca-secrets.py")
    spec = importlib.util.spec_from_file_location("hca_secrets", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["hca_secrets"] = mod
    spec.loader.exec_module(mod)
    return mod


# Default credential ENV VAR NAMES (Doppler injects the VALUES; never stored here).
# SINGLE SOURCE OF TRUTH: hca-secrets.py owns these names. We import them lazily (the
# sibling has a hyphenated filename) rather than re-declaring the literals, so the names
# can never drift. See _load_hca_secrets() above.
_secrets = _load_hca_secrets()
DEFAULT_CLIENT_ID_ENV = _secrets.CLIENT_ID_ENV
DEFAULT_API_KEY_ENV = _secrets.API_KEY_ENV            # OAuth client SECRET (Doppler name)
DEFAULT_BASE_URL_ENV = _secrets.BASE_URL_ENV          # optional override for the GraphQL URL

# Public (non-secret) Hypercore endpoint constants (also in config.yaml; not credentials).
DEFAULT_GQL_URL = "https://api.hypercore.ai/graphql"
DEFAULT_TOKEN_URL = "https://auth.hypercore.ai/identity/resources/auth/v1/api-token"
DEFAULT_REFRESH_URL = (
    "https://auth.hypercore.ai/identity/resources/auth/v1/api-token/token/refresh"
)
DEFAULT_REFRESH_SKEW_SECONDS = 60
DEFAULT_INTROSPECTION_PATH = "planning/preeng/001-hypercore-ask/_introspection.json"


def _load_hca_live():
    """Lazily import the sibling network module hca-live.py (hyphenated filename).

    Done inside LiveBackend methods so the adapter module's import block stays
    network-import-free (FixtureBackend path can never reach a socket).

    Cached in sys.modules under the stable name "hca_live" so every caller (and tests)
    shares ONE module instance — otherwise its exception classes would not be identical
    across separate loads (isinstance/except mismatch).
    """
    import sys
    import importlib.util
    cached = sys.modules.get("hca_live")
    if cached is not None:
        return cached
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "hca-live.py")
    spec = importlib.util.spec_from_file_location("hca_live", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["hca_live"] = mod
    spec.loader.exec_module(mod)
    return mod


def _now_iso() -> str:
    """UTC timestamp for provenance (stdlib only; no network)."""
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class LiveBackend(HypercoreBackend):
    """REAL read-only Hypercore GraphQL backend. Import-safe; creds from env ONLY.

    Credentials are injected at runtime by Doppler (`doppler run --project hypercore-ask
    --config dev_personal`). This class NEVER stores or logs a key or token; it only reads
    the configured env var NAMES. The actual transport (urllib + TLS 1.2+) lives in the
    sibling `hca-live.py`, imported lazily, so no network import exists in this module and
    no socket is reachable while is_live() is False.

    Read-only is enforced THREE ways: (1) the contract has no mutating method; (2) only
    GraphQL `query` operations are ever constructed; (3) `assert_query_only` refuses any
    operation text that is a mutation/subscription before it can be sent.
    """

    BACKEND_LABEL = "live"

    def __init__(self, client_id_env: str = DEFAULT_CLIENT_ID_ENV,
                 api_key_env: str = DEFAULT_API_KEY_ENV,
                 base_url_env: str = DEFAULT_BASE_URL_ENV,
                 env: Optional[dict] = None,
                 *,
                 gql_url: Optional[str] = None,
                 token_url: str = DEFAULT_TOKEN_URL,
                 refresh_url: str = DEFAULT_REFRESH_URL,
                 refresh_skew_seconds: int = DEFAULT_REFRESH_SKEW_SECONDS,
                 introspection_path: Optional[str] = None,
                 page_limit: int = 50,
                 opener=None):
        self.client_id_env = client_id_env
        self.api_key_env = api_key_env
        self.base_url_env = base_url_env
        self._env = env if env is not None else os.environ
        self._token_url = token_url
        self._refresh_url = refresh_url
        self._refresh_skew_seconds = refresh_skew_seconds
        self._page_limit = page_limit
        self._opener = opener  # test seam: mock HTTP layer (no real network in unit tests)
        # GraphQL URL: explicit arg > env override > config default.
        self._gql_url = (gql_url or self._env.get(self.base_url_env, "").strip()
                         or DEFAULT_GQL_URL)
        self._introspection_path = introspection_path or os.path.join(
            _repo_root(), DEFAULT_INTROSPECTION_PATH
        )
        self._client = None  # lazily built LiveGraphQLClient

    # --- credential check --------------------------------------------------
    def is_live(self) -> bool:
        """Live only when BOTH credentials (client id + client secret) are present.

        Reads env (Doppler-injected). Absent/partial creds -> False, which drives the
        graceful NO_LIVE_DATA degradation upstream. NEVER returns/echoes the values.
        """
        # Delegate to hca-secrets.is_provisioned — the single source of truth for the
        # provisioned check — so the logic lives in exactly one place. NEVER echoes values.
        return _load_hca_secrets().is_provisioned(
            client_id_env=self.client_id_env,
            api_key_env=self.api_key_env,
            env=self._env,
        )

    # --- live client construction (lazy; only when is_live()) --------------
    def _ensure_client(self):
        if self._client is not None:
            return self._client
        if not self.is_live():
            raise NoLiveDataError(
                "LiveBackend invoked without credentials (CLIENT_ID / client secret absent)"
            )
        live = _load_hca_live()
        introspection = self._load_introspection(live)
        token_mgr = live.TokenManager(
            token_url=self._token_url,
            refresh_url=self._refresh_url,
            client_id=self._env.get(self.client_id_env, ""),
            client_secret=self._env.get(self.api_key_env, ""),
            refresh_skew_seconds=self._refresh_skew_seconds,
            opener=self._opener,
        )
        transport = live.GraphQLTransport(
            gql_url=self._gql_url, token_manager=token_mgr, opener=self._opener,
        )
        schema_index = live.SchemaIndex(introspection)
        self._client = live.LiveGraphQLClient(transport=transport,
                                              schema_index=schema_index)
        return self._client

    def _load_introspection(self, live) -> dict:
        if not os.path.isfile(self._introspection_path):
            raise live.SchemaValidationError(
                f"introspection file not found at {self._introspection_path} — run "
                f"hca-introspect-full.py first"
            )
        with open(self._introspection_path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    # --- generic live client accessor (for figure/resolver modules) --------
    def live_client(self):
        """Return the underlying read-only LiveGraphQLClient (building it lazily).

        Exposed so higher-level modules (hca-resolve.py, hca-figures.py) can run
        ARBITRARY read-only GraphQL queries (e.g. `loans(filter:{searchString})`,
        `getLoanRepaymentDistribution`) through the SAME authenticated, TLS-enforced,
        READ-ONLY-guarded transport — instead of re-implementing auth/transport.

        Raises NoLiveDataError when credentials are absent (never fabricates a client).
        """
        return self._ensure_client()

    # --- contract impl -----------------------------------------------------
    def get_entity(self, entity_type: str, id: str, *, params: Optional[dict] = None) -> dict:
        client = self._ensure_client()
        fields = (params or {}).get("fields")
        result = client.get_entity(entity_type, id, fields=fields)
        fetched_at = _now_iso()
        record = result["record"]
        provenance = {
            "operation_name": result["operation_name"],
            "query": result["query"],
            "variables": result["variables"],
            "response_json_path": result["response_json_path"],
            "fetched_at": fetched_at,
        }
        body = {"record": record, "provenance": provenance} if record is not None else None
        return make_raw_api_response(
            raw_response_id=f"live:{entity_type}:{id}:{fetched_at}",
            endpoint=self._gql_url,
            request_params={
                "graphql_operation": result["operation_name"],
                "variables": result["variables"],
            },
            timestamp=fetched_at,
            http_status=200 if record is not None else 404,
            cursor=None,                 # GraphQL list uses offset (skip/limit), not cursor
            reported_total=None,
            body=body,
            backend=self.BACKEND_LABEL,
        )

    def list_entities(self, entity_type: str, *, filters: Optional[dict] = None,
                      cursor: Optional[str] = None) -> dict:
        """Paginated read. Walks OFFSET pages (skip/limit) to COMPLETION.

        GraphQL pagination here is offset-based, NOT cursor-based — the contract's
        `cursor` param is accepted for interface compatibility but is unused on live
        (we walk skip/limit internally and never return a partial page silently).
        """
        client = self._ensure_client()
        filters = filters or {}
        fields = filters.get("fields")
        filter_input = filters.get("filter")
        sort_by = filters.get("sortBy")
        page_limit = int(filters.get("limit") or self._page_limit)
        # Non-positive limit footgun: a negative limit is truthy so `or` won't catch it,
        # and downstream a limit <= 0 makes offset pagination never advance. Clamp to the
        # configured default before handing off (hca-live also clamps as a second guard).
        if page_limit <= 0:
            page_limit = self._page_limit
        result = client.list_entities(
            entity_type, fields=fields, filter_input=filter_input,
            sort_by=sort_by, page_limit=page_limit,
        )
        fetched_at = _now_iso()
        items = result["items"]
        provenance = {
            "operation_name": result["operation_name"],
            "query": result["query"],
            "variables_template": result["variables_template"],
            "response_json_path": result["response_json_path"],
            "fetched_at": fetched_at,
        }
        body = {
            "data": items,
            "reported_total": result["reported_total"],
            "fetched": result["fetched"],
            "complete": result["complete"],   # never a silent partial — surfaced explicitly
            "pages": result["pages"],
            "provenance": provenance,
        }
        return make_raw_api_response(
            raw_response_id=f"live:list:{entity_type}:{fetched_at}",
            endpoint=self._gql_url,
            request_params={
                "graphql_operation": result["operation_name"],
                "filter": filter_input, "sortBy": sort_by, "limit": page_limit,
            },
            timestamp=fetched_at,
            http_status=200,
            cursor=None,                       # offset pagination: no cursor
            reported_total=result["reported_total"],
            body=body,
            backend=self.BACKEND_LABEL,
        )

    def get_schema(self, entity_type: str) -> SchemaDescriptor:
        """Return the introspected GraphQL type for an entity (from cached introspection)."""
        client = self._ensure_client()
        type_desc = client.get_schema(entity_type)
        expected_fields = {}
        for fl in (type_desc.get("fields") or []):
            expected_fields[fl["name"]] = _render_graphql_type(fl.get("type"))
        required = [fl["name"] for fl in (type_desc.get("fields") or [])
                    if _is_non_null(fl.get("type"))]
        return SchemaDescriptor(
            entity_type=entity_type,
            expected_fields=expected_fields,
            version=f"live-introspection:{type_desc.get('name')}",
            required_fields=required,
            raw=type_desc,
        )

    def subscribe_events(self, entity_type: Optional[str] = None, *,
                         callback=None, poll_interval_s: Optional[int] = None):
        # Live polling/webhook freshness hook is a later slice (SLICE-HCA-08).
        raise NotImplementedError(
            "subscribe_events: live polling/webhook freshness hook is TODO (SLICE-HCA-08)"
        )


def _render_graphql_type(type_ref: Optional[dict]) -> str:
    """Render a GraphQL type ref like `[Loan!]!` (stdlib; for SchemaDescriptor display)."""
    if not type_ref:
        return "?"
    stack = []
    name = None
    cur = type_ref
    while cur:
        k = cur.get("kind")
        if k == "NON_NULL":
            stack.append("!")
        elif k == "LIST":
            stack.append("[]")
        else:
            name = cur.get("name")
            break
        cur = cur.get("ofType")
    out = name or "?"
    for s in reversed(stack):
        out = f"[{out}]" if s == "[]" else f"{out}!"
    return out


def _is_non_null(type_ref: Optional[dict]) -> bool:
    return bool(type_ref) and type_ref.get("kind") == "NON_NULL"


# ---------------------------------------------------------------------------
# Backend selection (config/env-driven; default fixture) + public adapter surface
# ---------------------------------------------------------------------------

def _read_config_backend() -> Optional[str]:
    """Best-effort read of adapter.backend from config.yaml WITHOUT a YAML lib.

    stdlib-only: scans for a top-level `adapter:` block and a `backend: "<x>"` line.
    Returns the backend string or None if unreadable. (A real YAML parse is not needed
    for this single scalar and we keep the no-third-party-dep rule.)
    """
    cfg_path = os.path.join(_skill_dir(), "config.yaml")
    if not os.path.isfile(cfg_path):
        return None
    in_adapter = False
    try:
        with open(cfg_path, "r", encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                # top-level key (no leading whitespace)
                if not line[:1].isspace():
                    in_adapter = stripped.startswith("adapter:")
                    continue
                if in_adapter and stripped.startswith("backend:"):
                    val = stripped.split(":", 1)[1].strip().strip('"').strip("'")
                    # strip trailing inline comment
                    if "#" in val:
                        val = val.split("#", 1)[0].strip().strip('"').strip("'")
                    return val or None
    except OSError:
        return None
    return None


def select_backend(*, backend: Optional[str] = None,
                   env: Optional[dict] = None) -> HypercoreBackend:
    """Choose a backend. Resolution order:

        explicit `backend` arg  ->  HCA_ADAPTER_BACKEND env  ->  config.yaml  ->  "fixture".

    Default is always "fixture". "live" yields the (stubbed) LiveBackend.
    """
    env = env if env is not None else os.environ
    choice = (backend
              or env.get("HCA_ADAPTER_BACKEND")
              or _read_config_backend()
              or "fixture")
    choice = choice.strip().lower()
    if choice == "live":
        return LiveBackend(env=env)
    return FixtureBackend()


class HypercoreAdapter:
    """Public convenience surface over a selected backend.

    Enforces the graceful-degradation contract: if the underlying backend is not live
    and a caller demands live data (require_live=True), it raises NoLiveDataError with
    the explicit NO_LIVE_DATA envelope rather than fabricating. With the default
    FixtureBackend, reads succeed and are clearly labeled backend="fixture".

    This surface is also read-only — it exposes ONLY the contract's read methods.
    """

    def __init__(self, backend: Optional[HypercoreBackend] = None,
                 *,
                 rbac_scope: Optional["RBACScope"] = None,
                 invalidation_hook: Optional["FreshnessInvalidationHook"] = None):
        self.backend = backend or select_backend()
        self.rbac_scope = rbac_scope          # optional RBAC scope pass-through
        self.invalidation_hook = invalidation_hook  # optional freshness invalidation hook

    def is_live(self) -> bool:
        return self.backend.is_live()

    def get_entity(self, entity_type: str, id: str, *, params: Optional[dict] = None,
                   require_live: bool = False,
                   rbac_scope: Optional["RBACScope"] = None) -> dict:
        self._guard_live(require_live, entity_type, {"id": id, "params": params})
        merged_params = rbac_scope_hook(rbac_scope or self.rbac_scope, params=params)
        return self.backend.get_entity(entity_type, id, params=merged_params)

    def list_entities(self, entity_type: str, *, filters: Optional[dict] = None,
                      cursor: Optional[str] = None, require_live: bool = False,
                      rbac_scope: Optional["RBACScope"] = None) -> dict:
        self._guard_live(require_live, entity_type, {"filters": filters, "cursor": cursor})
        # RBAC scope is advisory — not injected into filters (separate concern)
        _ = rbac_scope_hook(rbac_scope or self.rbac_scope)
        return self.backend.list_entities(entity_type, filters=filters, cursor=cursor)

    def get_schema(self, entity_type: str, *, require_live: bool = False) -> SchemaDescriptor:
        self._guard_live(require_live, entity_type, {})
        return self.backend.get_schema(entity_type)

    def subscribe_events(self, entity_type: Optional[str] = None, *,
                         callback=None, poll_interval_s: Optional[int] = None):
        return self.backend.subscribe_events(
            entity_type, callback=callback, poll_interval_s=poll_interval_s
        )

    # --- freshness invalidation pass-through (READ-ONLY) --------------------
    def on_change_event(self, event: dict) -> None:
        """Forward a Hypercore change event to the invalidation hook (if wired).

        READ-ONLY: marks the affected entity stale in the in-process set only.
        Never calls any Hypercore write method.
        """
        if self.invalidation_hook is not None:
            self.invalidation_hook.on_change_event(event)

    def is_cache_stale(self, entity_type: str,
                       entity_id: Optional[str] = None) -> bool:
        """Return True if the invalidation hook has marked this entity stale."""
        if self.invalidation_hook is None:
            return False
        return self.invalidation_hook.is_stale(entity_type, entity_id)

    # --- degradation guard -------------------------------------------------
    def _guard_live(self, require_live: bool, entity_type: str, request: dict) -> None:
        if require_live and not self.backend.is_live():
            raise NoLiveDataError(
                "live data requested but adapter is not live "
                "(Hypercore access not yet provisioned)",
                envelope=no_live_data_envelope(entity_type=entity_type, request=request),
            )


def _selftest_live(entity_type: str = "loans") -> int:
    """READ-ONLY live self-test. Authenticates, runs the SMALLEST list query, and prints
    ONLY counts + field names present (NEVER raw values, never the token/secret).

    Run via Doppler:
        doppler run --project hypercore-ask --config dev_personal -- \
            python3 .claude/scripts/hca-adapter.py --selftest-live
    """
    # Derive the plural(list_query) -> singular(entity_type) map from the live
    # ENTITY_REGISTRY at runtime so it can never drift from the source of truth.
    _registry = _load_hca_live().ENTITY_REGISTRY
    singular = {reg["list_query"]: k for k, reg in _registry.items()
                if reg.get("list_query")}
    et = singular.get(entity_type, entity_type)
    backend = LiveBackend()  # reads creds from env (Doppler-injected)
    print(f"is_live = {backend.is_live()}")
    if not backend.is_live():
        print("FAIL: not live — CLIENT_ID / HYPERCORE_CLIENT_SECRET not in env. "
              "Run via `doppler run --project hypercore-ask --config dev_personal -- ...`.")
        return 2
    print(f"gql_url = {backend._gql_url}")
    print(f"entity  = {et}")
    try:
        # smallest possible page to confirm auth + pagination wiring
        resp = backend.list_entities(et, filters={"limit": 2})
    except Exception as e:  # structured failure, no fabrication, no secret in message
        print(f"FAIL list_entities: {type(e).__name__}: {str(e)[:300]}")
        return 3
    body = resp.get("body") or {}
    data = body.get("data") or []
    field_names = sorted({k for rec in data if isinstance(rec, dict) for k in rec.keys()})
    print("OK  live read succeeded (READ-ONLY query).")
    print(f"  http_status        = {resp.get('http_status')}")
    print(f"  reported_total     = {resp.get('reported_total')}")
    print(f"  fetched (this run) = {body.get('fetched')}")
    print(f"  pages_walked       = {body.get('pages')}")
    print(f"  complete_flag      = {body.get('complete')}")
    print(f"  field_names_present = {field_names}")  # NAMES only, never values
    # Confirm pagination walk reaches completion when limited to a tiny page (full walk).
    try:
        full = backend.list_entities(et, filters={"limit": 2})
        fb = full.get("body") or {}
        print(f"  full_walk: fetched={fb.get('fetched')} of reported_total="
              f"{fb.get('reported_total')} over {fb.get('pages')} page(s), "
              f"complete={fb.get('complete')}")
    except Exception as e:
        print(f"  full_walk: FAIL {type(e).__name__}: {str(e)[:200]}")
    return 0


if __name__ == "__main__":
    import sys
    if "--selftest-live" in sys.argv:
        # optional entity arg: --selftest-live clients
        et = "loans"
        for i, a in enumerate(sys.argv):
            if a == "--selftest-live" and i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("-"):
                et = sys.argv[i + 1]
        sys.exit(_selftest_live(et))
    # Tiny smoke surface (no network). Prints whether the default adapter is live and
    # the NO_LIVE_DATA envelope shape. Real CLI is owned by SKILL.md / later slices.
    adapter = HypercoreAdapter()
    print(json.dumps({
        "selected_backend": type(adapter.backend).__name__,
        "is_live": adapter.is_live(),
        "no_live_data_envelope_example": no_live_data_envelope(entity_type="loan",
                                                               request={"id": "L-001"}),
    }, indent=2))
