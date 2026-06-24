#!/usr/bin/env python3
"""hca-cache.py — the two-tier data store for acos-hypercore-ask (SLICE-HCA-03).

This module owns BOTH tiers of the data model (data-model.md §0, B1, B2):

  Tier-1  RawApiResponse        = IMMUTABLE source of truth. The exact raw GraphQL
                                  response (operation_name, query, variables, raw body,
                                  timestamp, reported_total, pages_walked, complete),
                                  content-addressed by a STABLE id (hash of
                                  operation+variables). Append-only; NEVER mutated after
                                  write. ALL provenance points here.

  Tier-2  NormalizedAnswerRecord = DERIVED view. Normalized fields, each carrying a
                                  back-pointer {raw_response_id, json_field_path} to its
                                  Tier-1 source. Built ONLY from Tier-1 (never invented).
                                  Tier-2 derivation lives in the sibling hca-normalize.py;
                                  this module persists the result and resolves bindings.

PII SAFETY (critical — slice-03 acceptance + data-model.md D):
  Tier-1 raw responses contain REAL borrower data on the live path. The cache lives ONLY
  in a GIT-IGNORED runtime dir (default `.acos/state/hca-cache/`). It is NEVER written to
  the git-tracked tree. `.acos/state/` is already covered by the repo `.gitignore`; a
  defensive `.gitignore` is also dropped into the cache dir on first write. NO real PII is
  ever committed; unit-test fixtures remain synthetic/placeholder.

FRESHNESS (data-model.md invariant 4 — "stale never delivered silently"):
  Each cache entry records `fetched_at` + the entity-class freshness window (config
  `freshness_windows_days`). `read_fresh()` returns the cached Tier-1 ONLY if it is within
  the window; otherwise it triggers a refetch via the adapter. If it cannot refetch (no
  creds / not live), it returns an explicit NO_LIVE_DATA / STALE_REFUSED envelope —
  NEVER the stale value silently.

TWO-TIER DISCIPLINE (token efficiency):
  `read_tier2()` returns only the normalized view (token-efficient for agents); a caller
  can DRILL to Tier-1 via `resolve_binding()` / `get(raw_response_id)` for full provenance.

GROUND RULES (memory/decisions/2026-06-18-hca-build-ground-rules.md):
  - Python 3 stdlib ONLY. No third-party deps. No network import in THIS module (the
    adapter owns all transport; this module imports it lazily and only when refetching).
  - Subscription-only Claude: no model calls; never ANTHROPIC_API_KEY.
  - No credential or URL stored here.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Errors & sentinels
# ---------------------------------------------------------------------------

STALE_REFUSED = "STALE_REFUSED"
NO_LIVE_DATA = "NO_LIVE_DATA"


class ImmutableCacheError(RuntimeError):
    """Raised when a write would mutate an already-written Tier-1 record.

    Tier-1 is append-only: re-writing the same key with DIFFERENT content is refused
    (immutability). Re-writing with IDENTICAL content is a no-op (idempotent resume).
    """


class CacheMissError(KeyError):
    """Raised when a Tier-1 record is requested by id and is not present in the store."""


class StaleRefusedError(RuntimeError):
    """Raised when fresher data is required than the cache holds and a refetch is not
    possible (not live). Carries the explicit STALE_REFUSED envelope — never the stale
    value (data-model.md invariant 4: stale never served silently)."""

    def __init__(self, message: str, envelope: Optional[dict] = None):
        super().__init__(message)
        self.envelope = envelope or {}


# ---------------------------------------------------------------------------
# Time helpers (stdlib only; no network)
# ---------------------------------------------------------------------------

_ISO_FORMATS = ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S")


def _now_utc() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _now_iso() -> str:
    return _now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(ts: str) -> Optional[datetime.datetime]:
    """Parse a stored ISO timestamp to an aware UTC datetime. Returns None if unparseable.

    Tolerant of a trailing 'Z', a '+00:00' offset, and date-only stamps.
    """
    if not ts or not isinstance(ts, str):
        return None
    raw = ts.strip()
    # date-only -> midnight UTC
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        try:
            d = datetime.datetime.strptime(raw, "%Y-%m-%d")
            return d.replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            return None
    # normalise trailing Z to +00:00 for fromisoformat
    iso = raw.replace("Z", "+00:00") if raw.endswith("Z") else raw
    try:
        dt = datetime.datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(datetime.timezone.utc)
    except ValueError:
        pass
    for fmt in _ISO_FORMATS:
        try:
            dt = datetime.datetime.strptime(raw, fmt)
            return dt.replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# Content-addressed Tier-1 id
# ---------------------------------------------------------------------------

def _canonical_json(obj: Any) -> str:
    """Deterministic JSON for hashing (sorted keys, no whitespace, stable separators)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_raw_response_id(operation_name: str, variables: Optional[dict]) -> str:
    """Stable content-address for a Tier-1 record.

    Derived from operation_name + the request variables (NOT from fetched_at), so a
    re-fetch of the same query maps to the SAME id — enabling durable/resumable lookup
    (acceptance: re-run finds prior Tier-1 without re-fetch). Pure hash; no PII echoed.
    """
    payload = _canonical_json({"op": operation_name or "", "vars": variables or {}})
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]
    return f"hca:{digest}"


def _safe_key(raw_response_id: str) -> str:
    """Filesystem-safe filename stem for a raw_response_id (hash of the id; collision-safe).

    The id itself may contain ':' / timestamps; we never trust it as a path. We hash it to
    a fixed stem so traversal is impossible and lookup is O(1).
    """
    return hashlib.sha256(raw_response_id.encode("utf-8")).hexdigest()[:40]


# ---------------------------------------------------------------------------
# Path resolution (no git dependency — matches ACOS hook policy)
# ---------------------------------------------------------------------------

def _repo_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))            # .../.claude/scripts
    return os.path.abspath(os.path.join(here, os.pardir, os.pardir))


def default_cache_dir() -> str:
    """Git-ignored runtime cache dir. `.acos/state/` is covered by the repo .gitignore."""
    return os.path.join(_repo_root(), ".acos", "state", "hca-cache")


# Entity-class freshness windows (days) — read from config.yaml (stdlib scan; no YAML lib).
# Conservative fallbacks match config defaults (data-model.md E / OQ3).
_DEFAULT_FRESHNESS_WINDOWS = {
    "balances_servicing": 1,
    "payments_drawdowns": 1,
    "reference_static": 30,
}

# Map entity_type -> freshness class. Conservative: anything not listed uses the SHORTEST
# window (balances_servicing) so we err toward refetch, never toward serving stale.
_ENTITY_FRESHNESS_CLASS = {
    "loan": "balances_servicing",
    "balance": "balances_servicing",
    "servicing": "balances_servicing",
    "payment": "payments_drawdowns",
    "drawdown": "payments_drawdowns",
    "funding": "payments_drawdowns",
    "loanFunding": "payments_drawdowns",
    "client": "reference_static",
    "borrower": "reference_static",
    "equity": "reference_static",
    "fundingEntity": "reference_static",
}


def _read_freshness_windows() -> dict:
    """Best-effort scan of config.yaml `freshness_windows_days` (stdlib; no YAML lib)."""
    cfg = os.path.join(_repo_root(), ".claude", "skills", "acos-hypercore-ask", "config.yaml")
    windows = dict(_DEFAULT_FRESHNESS_WINDOWS)
    if not os.path.isfile(cfg):
        return windows
    in_block = False
    try:
        with open(cfg, "r", encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if not line[:1].isspace():
                    in_block = stripped.startswith("freshness_windows_days:")
                    continue
                if in_block and ":" in stripped:
                    key, _, rest = stripped.partition(":")
                    val = rest.split("#", 1)[0].strip()
                    try:
                        windows[key.strip()] = int(val)
                    except ValueError:
                        continue
    except OSError:
        return windows
    return windows


def freshness_window_days(entity_type: Optional[str],
                          windows: Optional[dict] = None) -> int:
    """Return the freshness window (days) for an entity type. Unknown -> shortest window."""
    windows = windows or _read_freshness_windows()
    cls = _ENTITY_FRESHNESS_CLASS.get(entity_type or "", "balances_servicing")
    return int(windows.get(cls, _DEFAULT_FRESHNESS_WINDOWS.get(cls, 1)))


def is_fresh(fetched_at: str, entity_type: Optional[str], *,
             now: Optional[datetime.datetime] = None,
             windows: Optional[dict] = None) -> bool:
    """True if a record fetched at `fetched_at` is still within its freshness window."""
    fetched = parse_iso(fetched_at)
    if fetched is None:
        return False  # unparseable timestamp -> treat as stale (never serve silently)
    now = now or _now_utc()
    age_days = (now - fetched).total_seconds() / 86400.0
    return age_days <= freshness_window_days(entity_type, windows)


def stale_refused_envelope(*, raw_response_id: Optional[str], entity_type: Optional[str],
                           fetched_at: Optional[str], reason: str,
                           refetch_attempted: bool, state: str = STALE_REFUSED) -> dict:
    """Explicit refusal envelope for a stale-without-refetch read. NEVER carries the value."""
    return {
        "state": state,
        "live": False,
        "data": None,                       # never the stale value
        "reason": reason,
        "entity_type": entity_type,
        "raw_response_id": raw_response_id,
        "stale_fetched_at": fetched_at,
        "refetch_attempted": refetch_attempted,
        "message": "stale cache and could not refetch — refusing to serve stale data",
    }


# ---------------------------------------------------------------------------
# Tier-1 immutable, content-addressed store
# ---------------------------------------------------------------------------

class RawResponseStore:
    """Write-once, append-only JSON store for Tier-1 RawApiResponse records.

    On-disk layout (all under the git-ignored cache dir):
        <cache_dir>/tier1/<safe_key>.json   one Tier-1 record per file
        <cache_dir>/.gitignore              defensive `*` ignore (belt-and-suspenders)

    Immutability: `put` of an EXISTING key with DIFFERENT content raises
    ImmutableCacheError. `put` with IDENTICAL content is an idempotent no-op (resume).
    There is intentionally NO update/delete method (read + append only).
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or default_cache_dir()
        self.tier1_dir = os.path.join(self.cache_dir, "tier1")

    # --- dir bootstrap + defensive gitignore -------------------------------
    def _ensure_dirs(self) -> None:
        os.makedirs(self.tier1_dir, exist_ok=True)
        gi = os.path.join(self.cache_dir, ".gitignore")
        if not os.path.isfile(gi):
            # Belt-and-suspenders: even if the parent .gitignore changes, this dir's
            # contents (real PII on the live path) are never committed.
            with open(gi, "w", encoding="utf-8") as fh:
                fh.write("# acos-hypercore-ask runtime cache — NEVER commit (may hold real PII).\n*\n")

    def _path_for(self, raw_response_id: str) -> str:
        return os.path.join(self.tier1_dir, _safe_key(raw_response_id) + ".json")

    # --- write (append-only / immutable) -----------------------------------
    def put(self, raw_api_response: dict) -> str:
        """Append-only write of a Tier-1 record. Returns its raw_response_id.

        The record MUST carry a `raw_response_id`. If a record with the same id already
        exists with different content -> ImmutableCacheError. Identical content -> no-op.
        """
        if not isinstance(raw_api_response, dict):
            raise TypeError("raw_api_response must be a dict (RawApiResponse shape)")
        rid = raw_api_response.get("raw_response_id")
        if not rid:
            raise ValueError("raw_api_response is missing 'raw_response_id' (required PK)")
        self._ensure_dirs()
        path = self._path_for(rid)
        if os.path.isfile(path):
            existing = self._read_path(path)
            if _canonical_json(existing) == _canonical_json(raw_api_response):
                return rid  # idempotent: identical re-write is a no-op (resume)
            raise ImmutableCacheError(
                f"refused: Tier-1 record {rid!r} already exists with different content; "
                f"Tier-1 is immutable (write-once, append-only)"
            )
        # Atomic write (tmp + rename) so a crash never leaves a half-written record.
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(_canonical_json(raw_api_response))
        os.replace(tmp, path)
        return rid

    # --- read --------------------------------------------------------------
    def has(self, raw_response_id: str) -> bool:
        return os.path.isfile(self._path_for(raw_response_id))

    def get(self, raw_response_id: str) -> dict:
        """Return the Tier-1 record for an id. Raises CacheMissError if absent."""
        path = self._path_for(raw_response_id)
        if not os.path.isfile(path):
            raise CacheMissError(f"no Tier-1 record for raw_response_id={raw_response_id!r}")
        return self._read_path(path)

    def get_or_none(self, raw_response_id: str) -> Optional[dict]:
        try:
            return self.get(raw_response_id)
        except CacheMissError:
            return None

    def _read_path(self, path: str) -> dict:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def ids(self) -> list:
        """List all Tier-1 raw_response_ids currently stored (for diagnostics/tests)."""
        out = []
        if not os.path.isdir(self.tier1_dir):
            return out
        for name in sorted(os.listdir(self.tier1_dir)):
            if name.endswith(".json"):
                rec = self._read_path(os.path.join(self.tier1_dir, name))
                rid = rec.get("raw_response_id")
                if rid:
                    out.append(rid)
        return out


# ---------------------------------------------------------------------------
# JSON-path walker (Tier-1 binding resolution) — shared with provenance engine
# ---------------------------------------------------------------------------

_PATH_TOKEN_RE = re.compile(r"\.([A-Za-z_][\w]*)|\[(\d+)\]|\['([^']*)'\]|\[\"([^\"]*)\"\]")

_MISSING = object()


def walk_json_path(root: Any, json_field_path: str) -> Any:
    """Resolve a `$.a.b[3].c` style path into a (possibly nested) structure.

    Supported tokens: `$` root, `.key`, `[index]`, `['key']`, `["key"]`.
    Returns the value at the path, or the sentinel `_MISSING` if any step is absent.
    Pure structural walk — never coerces, never fabricates.
    """
    if not isinstance(json_field_path, str) or not json_field_path:
        return _MISSING
    p = json_field_path.strip()
    if p.startswith("$"):
        p = p[1:]
    cur = root
    pos = 0
    n = len(p)
    while pos < n:
        m = _PATH_TOKEN_RE.match(p, pos)
        if not m:
            return _MISSING
        key_dot, idx, key_sq1, key_sq2 = m.group(1), m.group(2), m.group(3), m.group(4)
        if idx is not None:
            if not isinstance(cur, (list, tuple)):
                return _MISSING
            i = int(idx)
            if i < 0 or i >= len(cur):
                return _MISSING
            cur = cur[i]
        else:
            key = key_dot if key_dot is not None else (key_sq1 if key_sq1 is not None else key_sq2)
            if not isinstance(cur, dict) or key not in cur:
                return _MISSING
            cur = cur[key]
        pos = m.end()
    return cur


def path_resolves(root: Any, json_field_path: str) -> bool:
    return walk_json_path(root, json_field_path) is not _MISSING


# ---------------------------------------------------------------------------
# Two-tier cache facade: Tier-1 store + Tier-2 derivation + freshness reads
# ---------------------------------------------------------------------------

class TwoTierCache:
    """Public two-tier facade.

      put_raw(raw_api_response)            -> rid           (Tier-1 immutable write)
      get_raw(rid)                         -> RawApiResponse (Tier-1 drill-down)
      read_tier2(rid, entity_type=...)     -> NormalizedAnswerRecord (Tier-2 view only)
      read_fresh(rid, entity_type, adapter=..., refetch=...) -> Tier-1 honoring freshness
      resolve_binding({raw_response_id, json_field_path}) -> (value, ok)
      minimal_slice(rid, fields)           -> minimal Tier-1 slice for an agent (PII-min)

    Tier-2 derivation is delegated to the sibling hca-normalize.py (imported lazily so
    this module stays import-light and the two slices can be reasoned about separately).
    """

    def __init__(self, cache_dir: Optional[str] = None,
                 windows: Optional[dict] = None):
        self.store = RawResponseStore(cache_dir)
        self.cache_dir = self.store.cache_dir
        self._windows = windows or _read_freshness_windows()

    # --- Tier-1 -------------------------------------------------------------
    def put_raw(self, raw_api_response: dict) -> str:
        return self.store.put(raw_api_response)

    def get_raw(self, raw_response_id: str) -> dict:
        return self.store.get(raw_response_id)

    def has_raw(self, raw_response_id: str) -> bool:
        return self.store.has(raw_response_id)

    # --- Tier-2 (derived view only — token efficient) ----------------------
    def read_tier2(self, raw_response_id: str, *, entity_type: Optional[str] = None) -> dict:
        """Return ONLY the Tier-2 NormalizedAnswerRecord (no raw body) for a Tier-1 id.

        Token-efficient for agents: the normalized fields + their back-pointers, NOT the
        full raw cache. Drill to Tier-1 with get_raw()/resolve_binding() when full
        provenance is needed.
        """
        raw = self.store.get(raw_response_id)
        normalize = _load_normalize()
        return normalize.normalize_record(raw, entity_type=entity_type)

    # --- freshness-aware read (never serves stale silently) ----------------
    def read_fresh(self, raw_response_id: str, entity_type: str, *,
                   adapter=None, refetcher=None,
                   now: Optional[datetime.datetime] = None) -> dict:
        """Return a FRESH Tier-1 record, refetching if the cached copy is stale.

        Flow (data-model.md invariant 4):
          1. If cached and within the freshness window -> return cached.
          2. If stale (or absent) -> attempt a refetch:
               - `refetcher` (callable() -> RawApiResponse) if provided, OR
               - `adapter` (the HypercoreAdapter contract): only used when it is_live().
             A successful refetch is written to Tier-1 (immutable, new id) and returned.
          3. If a refetch is impossible (no adapter/refetcher, or adapter not live) ->
             raise StaleRefusedError with the explicit STALE_REFUSED / NO_LIVE_DATA
             envelope. NEVER returns the stale value silently.
        """
        cached = self.store.get_or_none(raw_response_id)
        if cached is not None:
            fetched_at = cached.get("timestamp") or _tier1_fetched_at(cached)
            if is_fresh(fetched_at, entity_type, now=now, windows=self._windows):
                return cached
            # stale -> fall through to refetch
            stale_fetched_at = fetched_at
        else:
            stale_fetched_at = None

        # --- attempt refetch -------------------------------------------------
        refreshed = self._attempt_refetch(adapter, refetcher)
        if refreshed is not None:
            self.store.put(refreshed)
            return refreshed

        # --- cannot refetch: refuse (never serve stale) ----------------------
        refetch_possible = bool(refetcher) or (adapter is not None and getattr(adapter, "is_live", lambda: False)())
        state = STALE_REFUSED if cached is not None else NO_LIVE_DATA
        reason = ("cache is stale and no live refetch is possible (adapter not live / "
                  "no refetcher)") if cached is not None else (
                  "no cached Tier-1 record and no live refetch is possible")
        raise StaleRefusedError(
            reason,
            envelope=stale_refused_envelope(
                raw_response_id=raw_response_id, entity_type=entity_type,
                fetched_at=stale_fetched_at, reason=reason,
                refetch_attempted=refetch_possible, state=state,
            ),
        )

    def _attempt_refetch(self, adapter, refetcher) -> Optional[dict]:
        if refetcher is not None:
            res = refetcher()
            return res if isinstance(res, dict) else None
        if adapter is not None and getattr(adapter, "is_live", lambda: False)():
            # The adapter contract is read-only; we never construct a mutation. We don't
            # know the entity id here, so a bare adapter cannot self-refetch — callers that
            # want adapter-driven refetch should pass an explicit `refetcher` closure that
            # calls adapter.get_entity / list_entities. We return None to force a refusal
            # rather than guessing.
            return None
        return None

    # --- binding resolution (drill Tier-2 -> Tier-1) -----------------------
    def resolve_binding(self, binding: dict) -> tuple:
        """Resolve a {raw_response_id, json_field_path} back-pointer to its Tier-1 value.

        Returns (value, True) on success, or (None, False) if the Tier-1 record is absent
        or the path does not resolve. Never fabricates.
        """
        rid = (binding or {}).get("raw_response_id")
        path = (binding or {}).get("json_field_path")
        if not rid or not path:
            return None, False
        raw = self.store.get_or_none(rid)
        if raw is None:
            return None, False
        val = walk_json_path(raw, path)
        if val is _MISSING:
            return None, False
        return val, True

    # --- minimal Tier-1 slice for an agent (PII / token minimization) ------
    def minimal_slice(self, raw_response_id: str, fields: list, *,
                      max_records: int = 1) -> dict:
        """Return the MINIMAL Tier-1 slice for a given value/question.

        Hands an agent ONLY the requested `fields` from at most `max_records` items of the
        Tier-1 body — never the full cache, never extra PII. Carries the source id +
        per-field json_field_path so the agent can still cite provenance. PII-bearing
        fields not in `fields` are simply absent (not redacted-in-place — omitted).
        """
        raw = self.store.get(raw_response_id)
        items, base_path, single = _tier1_items(raw)
        sliced = []
        for i, item in enumerate(items[:max(0, int(max_records))]):
            if not isinstance(item, dict):
                continue
            picked = {}
            field_paths = {}
            for f in fields:
                if f in item:
                    picked[f] = item[f]
                    field_paths[f] = _join_path(base_path, i, f, single=single)
            sliced.append({"fields": picked, "field_paths": field_paths})
        return {
            "raw_response_id": raw_response_id,
            "entity_type": raw.get("entity_type") or _tier1_entity_type(raw),
            "requested_fields": list(fields),
            "slice": sliced,
            "_note": "MINIMAL Tier-1 slice — not the full cache; only requested fields.",
        }


# ---------------------------------------------------------------------------
# Tier-1 body-shape helpers (handles BOTH the GraphQL live shape and REST fixtures)
# ---------------------------------------------------------------------------

def _tier1_fetched_at(raw: dict) -> Optional[str]:
    """Best-effort fetched_at: top-level timestamp, else body.provenance.fetched_at."""
    if raw.get("timestamp"):
        return raw["timestamp"]
    body = raw.get("body") or {}
    if isinstance(body, dict):
        prov = body.get("provenance") or {}
        if isinstance(prov, dict) and prov.get("fetched_at"):
            return prov["fetched_at"]
    return None


def _tier1_entity_type(raw: dict) -> Optional[str]:
    return raw.get("entity_type")


def _tier1_items(raw: dict) -> tuple:
    """Return (items_list, base_json_path, single) for the records inside a Tier-1 body.

    `single` is the authoritative single-record flag (matches hca-normalize._items_and_base):
    True when the body is a lone record (dict-shaped), False when it is a list of records.
    Provenance paths MUST use this flag — re-deriving it from a `base_path.endswith("record")`
    string heuristic is WRONG for the REST-single shape (base "$.body"), which produced an
    unresolvable `$.body[0].<field>` path and a false provenance refusal.

    Handles three shapes:
      - GraphQL list:   body.data = [...]          base = "$.body.data"   single=False
      - GraphQL single: body.record = {...}        base = "$.body.record" single=True  (wrapped to [rec])
      - REST single:    body = {loan_id: ...}       base = "$.body"        single=True  (wrapped to [body])
    """
    body = raw.get("body")
    if isinstance(body, dict):
        if isinstance(body.get("data"), list):
            return body["data"], "$.body.data", False
        if isinstance(body.get("record"), dict):
            return [body["record"]], "$.body.record", True
        return [body], "$.body", True
    if isinstance(body, list):
        return body, "$.body", False
    return [], None, True


def _join_path(base_path: Optional[str], index: int, field: str, *, single: bool) -> str:
    """Build a json_field_path for a field inside a Tier-1 body."""
    if base_path is None:
        return f"$.{field}"
    if single:
        return f"{base_path}.{field}"
    return f"{base_path}[{index}].{field}"


# ---------------------------------------------------------------------------
# Lazy sibling loader (hca-normalize.py has a hyphen in its filename)
# ---------------------------------------------------------------------------

def _load_normalize():
    import sys
    import importlib.util
    cached = sys.modules.get("hca_normalize")
    if cached is not None:
        return cached
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "hca-normalize.py")
    spec = importlib.util.spec_from_file_location("hca_normalize", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["hca_normalize"] = mod
    spec.loader.exec_module(mod)
    return mod


if __name__ == "__main__":
    # Tiny no-network smoke surface: prints the cache dir + its freshness windows.
    cache = TwoTierCache()
    print(json.dumps({
        "cache_dir": cache.cache_dir,
        "git_ignored_under": ".acos/state/ (repo .gitignore) + defensive cache .gitignore",
        "freshness_windows_days": _read_freshness_windows(),
        "tier1_records_present": len(cache.store.ids()),
    }, indent=2))
