#!/usr/bin/env python3
"""hca-entities.py — GENERALIZED ENTITY-NAME RESOLUTION for acos-hypercore-ask.

Generalizes the loan-name resolver (hca-resolve.py) to resolve ANY searchable entity by
name — funding entities (investors), clients, equities, AND loans — so a question like
"XL's outstanding" can resolve "XL" to the funding entity named "XL" (id 3), not just a
loan. Today only loans resolve via hca-resolve.LoanResolver; this module covers the rest
while REUSING that module's scoring + policy verbatim (imported, never re-implemented).

The resolution policy is the SAME NON-NEGOTIABLE one the loan resolver enforces:

  - Exactly one high-confidence match  -> RESOLVE, and RECORD the resolution so the caller
    can ECHO it ("matched 'XL' -> 'XL' (3)").
  - Multiple / low-confidence matches  -> return the candidate list for DISAMBIGUATION.
    NEVER silently pick one. The user (or caller) must choose.
  - No match                            -> empty candidates (a clean miss, never invented).

CANDIDATES ALWAYS COME FROM REAL API ROWS. This module never invents an id or a name —
it only fetches via each entity's RELIABLE list query and scores client-side.

WHY THE LIST QUERY (mirrors hca-resolve's rationale, verified live 2026-06-23):
  Single-record resolvers + some queries intermittently HTTP 500. The RELIABLE path is the
  per-entity LIST query, e.g.
      fundingEntities(filter:{searchString:"XL"}, skip:0, limit:50){
          totalFilteredRecords pageItems{ id name ... } }
  -> returns the funding entity named "XL" (id 3). So resolution rides exclusively on the
  list query, with a small bounded retry around each call (the list path 500s intermittently).

SEARCHABLE ENTITIES + their HUMAN-NAME field (from hca-live.ENTITY_REGISTRY):
    loan          -> list_query "loans",           name field "name"
    client        -> list_query "clients",          name field "displayName"
    equity        -> list_query "equities",         name field "name"
    fundingEntity -> list_query "fundingEntities",   name field "name"
  (loanFunding / loanTransaction have NO human name and are excluded from name resolution.)

REUSE (no duplicated logic — imported from hca-resolve via the existing importlib seam):
  - score_name + thresholds HIGH_CONFIDENCE / AMBIGUITY_GAP / MIN_CANDIDATE_SCORE
  - _normalize
  - the SAME progressive searchString broadening idea (full -> tokens -> unfiltered)
  - the SAME offset-pagination walk shape (skip/limit to totalFilteredRecords completion)
  - the SAME no-silent-pick disambiguation outcome logic

GROUND RULES (memory/decisions/2026-06-18-hca-build-ground-rules.md):
  - Python 3 stdlib ONLY. No third-party deps. No model calls; never ANTHROPIC_API_KEY.
  - Read-only: the only API touch is each entity's LIST query (a GraphQL `query`).
  - No real PII committed: this module fetches portfolio entity NAMES only; tests use fixtures.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from typing import Optional


# ---------------------------------------------------------------------------
# Sibling module loading (hyphenated filenames -> import by file path, cached).
# Mirrors hca-resolve._load so every module shares ONE instance in sys.modules
# (so e.g. ResolveError identity holds across imports).
# ---------------------------------------------------------------------------

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))


def _load(modname: str, filename: str):
    cached = sys.modules.get(modname)
    if cached is not None:
        return cached
    path = os.path.join(_THIS_DIR, filename)
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


def _resolve_mod():
    return _load("hca_resolve", "hca-resolve.py")


def _adapter():
    return _load("hca_adapter", "hca-adapter.py")


def _live_mod():
    return _load("hca_live", "hca-live.py")


# ---------------------------------------------------------------------------
# Reuse scoring + thresholds + normalization from hca-resolve (NOT re-implemented).
# Re-exported at module level so callers/tests can reference them the same way.
# ---------------------------------------------------------------------------

_R = _resolve_mod()
score_name = _R.score_name
_normalize = _R._normalize
HIGH_CONFIDENCE = _R.HIGH_CONFIDENCE
AMBIGUITY_GAP = _R.AMBIGUITY_GAP
MIN_CANDIDATE_SCORE = _R.MIN_CANDIDATE_SCORE
DEFAULT_FETCH_LIMIT = _R.DEFAULT_FETCH_LIMIT
# Reuse the loan resolver's surfaced-failure error type so a single `except ResolveError`
# catches failures from BOTH resolvers.
ResolveError = _R.ResolveError


# Bounded retry budget for the intermittently-500ing list query (per hard constraints:
# 4-6 tries; never invent rows on failure -> raise/refuse).
_RETRY_TRIES = 5


# ---------------------------------------------------------------------------
# Entity catalog: which entity types are name-resolvable + their human-name field.
# The list_query / paginated_return are pulled from hca-live.ENTITY_REGISTRY at runtime
# (single source of truth — cannot drift). loanFunding/loanTransaction are excluded:
# they carry no human name to resolve against.
# ---------------------------------------------------------------------------

# entity_type -> the field on each pageItem that holds the human-readable name.
_NAME_FIELD = {
    "loan": "name",
    "client": "displayName",
    "equity": "name",
    "fundingEntity": "name",
}

# Resolvable entity types (in a stable, documented order for CLI help / error messages).
RESOLVABLE_ENTITY_TYPES = ("loan", "client", "equity", "fundingEntity")


def _registry_for(entity_type: str) -> dict:
    """Return the hca-live ENTITY_REGISTRY row for a resolvable entity type.

    Raises ValueError for an unknown / non-resolvable type (loanFunding, loanTransaction,
    or anything not in the catalog) — never silently picks a default.
    """
    if entity_type not in _NAME_FIELD:
        raise ValueError(
            f"entity_type {entity_type!r} is not name-resolvable "
            f"(resolvable: {list(RESOLVABLE_ENTITY_TYPES)})"
        )
    registry = _live_mod().ENTITY_REGISTRY
    reg = registry.get(entity_type)
    if not reg or not reg.get("list_query"):
        raise ValueError(
            f"entity_type {entity_type!r} has no list query in ENTITY_REGISTRY"
        )
    return reg


# ---------------------------------------------------------------------------
# The resolver
# ---------------------------------------------------------------------------

class EntityResolver:
    """Fuzzy entity-name resolver over each entity's RELIABLE list query.

    Mirrors hca-resolve.LoanResolver, but parameterized by `entity_type` so the SAME
    fetch/score/disambiguate machinery works for funding entities, clients, equities, and
    loans. Construct with a `client` exposing `raw_query(query, variables) -> data` (the
    LiveGraphQLClient from hca-live.py satisfies this). Tests inject a fake client backed by
    fixtures. When no client is supplied, a live one is built lazily from a LiveBackend
    (requires Doppler-injected creds).

    Scoring + thresholds + the no-silent-pick policy are REUSED from hca-resolve (imported),
    so this resolver can never diverge from the loan resolver's behavior.
    """

    def __init__(self, *, client=None,
                 high_confidence: float = HIGH_CONFIDENCE,
                 ambiguity_gap: float = AMBIGUITY_GAP,
                 min_candidate_score: float = MIN_CANDIDATE_SCORE,
                 fetch_limit: int = DEFAULT_FETCH_LIMIT,
                 retry_tries: int = _RETRY_TRIES):
        self._client = client
        self._high = float(high_confidence)
        self._gap = float(ambiguity_gap)
        self._min = float(min_candidate_score)
        self._limit = int(fetch_limit)
        self._retry_tries = max(1, int(retry_tries))

    # --- live client (lazy) ------------------------------------------------
    def _ensure_client(self):
        if self._client is not None:
            return self._client
        ad = _adapter()
        try:
            self._client = ad.LiveBackend().live_client()
        except getattr(ad, "NoLiveDataError", Exception):
            # Missing creds -> a clean ResolveError (NO live data; never fabricates rows).
            raise ResolveError(
                "no live Hypercore credentials (CLIENT_ID / HYPERCORE_CLIENT_SECRET absent) "
                "— run via `doppler run --project hypercore-ask --config dev_personal -- ...`"
            ) from None
        return self._client

    # --- query builder for one entity's reliable list query ----------------
    def _build_list_query(self, entity_type: str, name_field: str) -> str:
        """Build the RELIABLE list query for `entity_type` from its ENTITY_REGISTRY row.

        Selects ONLY id + the human-name field (minimal, read-only). The variable decls /
        arg passing come straight from the registry so the filter-input type name + paging
        args match the live schema exactly. The searchString filter rides on `$filter`.
        """
        reg = _registry_for(entity_type)
        qname = reg["list_query"]
        var_decls = reg["list_var_decls"]
        arg_passing = reg["list_arg_passing"]
        op_name = f"HCAResolve{(reg.get('paginated_return') or qname)}"
        # Minimal selection: id + the human name. (status only exists on loans; we add it
        # opportunistically below for loans so the candidate display matches the loan resolver.)
        sel_fields = ["id", name_field]
        if entity_type == "loan" and name_field != "status":
            sel_fields.append("status")
        selection = " ".join(sel_fields)
        return (
            f"query {op_name}({var_decls}) {{ "
            f"{qname}({arg_passing}) {{ "
            f"totalFilteredRecords pageItems {{ {selection} }} "
            f"}} }}"
        )

    # --- bounded retry around a single raw_query (list path 500s intermittently) ---
    def _raw_query_retry(self, client, query: str, variables: dict):
        """Run client.raw_query with a bounded retry budget.

        Mirrors the spirit of hca-resolve: surface a ResolveError on persistent failure;
        NEVER invent rows. The list path 500s intermittently, so we retry a few times
        before refusing. The last exception is reported (truncated, no secret values).
        """
        last_exc = None
        for _attempt in range(self._retry_tries):
            try:
                return client.raw_query(query, variables)
            except Exception as e:  # transport/auth/GraphQL error — retry, then surface
                last_exc = e
        raise ResolveError(
            f"entity list fetch failed after {self._retry_tries} tries: "
            f"{type(last_exc).__name__}: {str(last_exc)[:200]}"
        ) from None

    # --- fetch real rows via the reliable list query -----------------------
    def _fetch_entities(self, entity_type: str, name_field: str,
                        search_string: Optional[str]) -> list:
        """Fetch real entity rows (id + human name [+ status for loans]) via the list query.

        Walks offset pages to completion (bounded by totalFilteredRecords, with a hard page
        cap). Returns the raw pageItems list. Raises ResolveError on a live failure that
        survives the retry budget (never fabricates rows). Mirrors hca-resolve._fetch_loans.
        """
        client = self._ensure_client()
        reg = _registry_for(entity_type)
        qname = reg["list_query"]
        query = self._build_list_query(entity_type, name_field)
        filt = {"searchString": search_string} if search_string else {}
        rows: list = []
        skip = 0
        pages = 0
        while True:
            pages += 1
            if pages > 1000:  # safety bound (matches hca-resolve)
                break
            variables = {"filter": filt, "skip": skip, "limit": self._limit}
            data = self._raw_query_retry(client, query, variables)
            page = (data or {}).get(qname) or {}
            reported_total = page.get("totalFilteredRecords")
            items = page.get("pageItems") or []
            rows.extend(items)
            if reported_total is not None and len(rows) >= reported_total:
                break
            if len(items) < self._limit:
                break
            skip += self._limit
        return rows

    def _search_tokens(self, name_query: str) -> list:
        """Progressively broader searchStrings — REUSED from a throwaway LoanResolver.

        The broadening logic (full -> two most-distinctive tokens -> each token -> unfiltered)
        is pure string manipulation over the user's OWN words and is identical for every
        entity type, so we borrow hca-resolve.LoanResolver._search_tokens rather than
        re-implementing it. A row is never invented — only searched-for more loosely.
        """
        return _R.LoanResolver(client=None)._search_tokens(name_query)

    # --- public: resolve a name query for an entity type -------------------
    def resolve_entity(self, name_query: str, entity_type: str) -> dict:
        """Resolve a name query for `entity_type` into {match, candidates, ...}.

        Returns the SAME dict shape as hca-resolve.resolve_loan:
            {
              "query": <original query>,
              "match": {id, name, score, status?} | None,  # set ONLY on a high-confidence
                                                            #  single match (auto-resolve)
              "resolved": bool,                              # True iff `match` is populated
              "ambiguous": bool,                             # True when >1 plausible candidate
              "candidates": [ {id, name, score, status?}, ...],  # ranked, real API rows
              "echo": <str|None>,   # human echo string when resolved (for the caller to print)
              "reason": <str>,      # why this outcome (resolved/ambiguous/no_match)
            }
        (For loans, candidates carry `status`; other entity types omit it — it does not exist
        on their schema.)

        Policy (REUSED verbatim from the loan resolver): exactly one high-confidence match
        -> resolve + echo. Multiple/low-confidence -> candidates for disambiguation (NEVER
        silently pick). No match -> empty candidates.
        """
        # Validate the entity type up front (raises ValueError for non-resolvable types).
        _registry_for(entity_type)
        name_field = _NAME_FIELD[entity_type]
        is_loan = entity_type == "loan"

        if not isinstance(name_query, str) or not name_query.strip():
            return {"query": name_query, "match": None, "resolved": False,
                    "ambiguous": False, "candidates": [], "echo": None,
                    "reason": "empty query"}

        # Fetch via the reliable list query; try progressively broader searchStrings so a
        # real entity is never missed by an over-strict server-side filter.
        rows_by_id: dict = {}
        for st in self._search_tokens(name_query):
            for r in self._fetch_entities(entity_type, name_field, st):
                rid = r.get("id")
                if rid is not None and rid not in rows_by_id:
                    rows_by_id[rid] = r
        rows = list(rows_by_id.values())

        scored = []
        for r in rows:
            name = r.get(name_field)
            if not name:
                continue
            sc = score_name(name_query, name)
            cand = {"id": r.get("id"), "name": name, "score": sc}
            if is_loan:
                cand["status"] = r.get("status")
            scored.append(cand)
        scored.sort(key=lambda c: (-c["score"], str(c.get("name"))))

        candidates = [c for c in scored if c["score"] >= self._min]

        if not candidates:
            return {"query": name_query, "match": None, "resolved": False,
                    "ambiguous": False, "candidates": [], "echo": None,
                    "reason": "no candidate scored above the minimum threshold (no match)"}

        top = candidates[0]
        second = candidates[1] if len(candidates) > 1 else None

        # A high-confidence single match: top is strong AND not effectively tied with #2.
        close_runner_up = (second is not None and
                           (top["score"] - second["score"]) < self._gap)
        if top["score"] >= self._high and not close_runner_up:
            echo = (f"matched {name_query!r} -> {top['name']!r} ({top['id']})")
            return {"query": name_query, "match": top, "resolved": True,
                    "ambiguous": False, "candidates": candidates, "echo": echo,
                    "reason": (f"single high-confidence match (score={top['score']}, "
                               f"runner-up gap >= {self._gap})")}

        # Otherwise: ambiguous / low-confidence -> hand back candidates, never pick.
        reason = ("multiple plausible candidates (top is not clearly best) — "
                  "disambiguation required; NOT auto-resolving") if close_runner_up else (
                  f"best score {top['score']} below high-confidence {self._high} — "
                  "disambiguation required; NOT auto-resolving")
        return {"query": name_query, "match": None, "resolved": False,
                "ambiguous": True, "candidates": candidates, "echo": None,
                "reason": reason}


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

def resolve_entity(name_query: str, entity_type: str, *, client=None, **kw) -> dict:
    """One-shot: build a resolver and resolve a single entity-name query for `entity_type`."""
    return EntityResolver(client=client, **kw).resolve_entity(name_query, entity_type)


# ---------------------------------------------------------------------------
# CLI — `--resolve "<name>" --type fundingEntity`. Prints the ranked candidates /
# resolution as JSON. Entity NAMES are portfolio reference data (not borrower PII),
# safe to print. Mirrors hca-resolve.main().
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="acos-hypercore-ask generalized entity-name resolver "
                    "(reliable per-entity list query).")
    parser.add_argument("--resolve", dest="resolve", metavar="NAME",
                        help="entity name (or partial) to resolve to a real id")
    parser.add_argument("--type", dest="entity_type", default="fundingEntity",
                        choices=list(RESOLVABLE_ENTITY_TYPES),
                        help="entity type to resolve against (default: fundingEntity)")
    args = parser.parse_args(argv)
    if not args.resolve:
        parser.error('an entity name is required: --resolve "XL" --type fundingEntity')
    try:
        result = resolve_entity(args.resolve, args.entity_type)
    except (ResolveError, ValueError) as e:
        print(json.dumps({"error": str(e), "resolved": False, "candidates": []}, indent=2))
        return 2
    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("resolved") else 1


if __name__ == "__main__":
    sys.exit(main())
