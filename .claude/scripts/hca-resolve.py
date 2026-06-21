#!/usr/bin/env python3
"""hca-resolve.py — FUZZY LOAN-NAME RESOLUTION for acos-hypercore-ask (SLICE-HCA-12).

Turns a human loan-name query ("beehive", "beehive senior", "Beehive Waldorff") into a
RANKED set of REAL loan candidates and — only when there is exactly ONE high-confidence
match — a single resolved loan. The policy is NON-NEGOTIABLE:

  - Exactly one high-confidence match  -> RESOLVE, but RECORD the resolution so the caller
    can ECHO it to the user ("matched 'beehive senior' -> 'Beehive Waldorff' (134)").
  - Multiple / low-confidence matches  -> return the candidate list for DISAMBIGUATION.
    NEVER silently pick one. The user (or caller) must choose.
  - No match                            -> empty candidates (a clean miss, never invented).

CANDIDATES ALWAYS COME FROM REAL API DATA. This module never invents a loan id or name —
it only fetches via the RELIABLE list query and scores client-side.

WHY THE LIST QUERY (verified live 2026-06-19, recorded in
memory/decisions/2026-06-19-hypercore-early-redemption-input.md):
  The single-loan resolver `loan(id)` and the transaction-PREVIEW resolvers are FLAKY
  (intermittent HTTP 500). The RELIABLE path is the LIST query
      loans(filter:{searchString:"..."}, skip, limit){ totalFilteredRecords pageItems{...} }
  so resolution rides exclusively on that.

SCORING (stdlib only — difflib.SequenceMatcher + token-set overlap):
  Each candidate name is scored against the query with a blend of:
    - difflib.SequenceMatcher ratio over normalized strings (character-level closeness), and
    - token-set overlap (Jaccard over word tokens; robust to word-order / extra qualifiers
      like "senior" / "USD"), with a bonus when the query tokens are a SUBSET of the name's
      (a partial name like "beehive" cleanly matches "Beehive Waldorff").
  An exact (normalized) match scores 1.0. A substring containment is boosted. The final
  score is in [0, 1].

GROUND RULES (memory/decisions/2026-06-18-hca-build-ground-rules.md):
  - Python 3 stdlib ONLY. No third-party deps. No model calls; never ANTHROPIC_API_KEY.
  - Read-only: the only API touch is the `loans` LIST query (a GraphQL `query`).
  - No real PII committed: this module fetches portfolio loan NAMES only; tests use fixtures.
"""

from __future__ import annotations

import argparse
import difflib
import importlib.util
import json
import os
import re
import sys
from typing import Any, Callable, Optional


# ---------------------------------------------------------------------------
# Tunables (resolution policy) — conservative defaults; safe to surface in config later.
# ---------------------------------------------------------------------------

# A single match must be at least this good to auto-resolve.
HIGH_CONFIDENCE = 0.82
# Two top candidates within this score gap are "too close to call" -> disambiguate, never pick.
AMBIGUITY_GAP = 0.08
# Candidates below this score are not even worth showing (a clean miss).
MIN_CANDIDATE_SCORE = 0.34
# How many loans to pull per searchString page (the list query is the reliable path).
DEFAULT_FETCH_LIMIT = 100


# ---------------------------------------------------------------------------
# Sibling module loading (hyphenated filenames -> import by file path, cached)
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


def _adapter():
    return _load("hca_adapter", "hca-adapter.py")


# ---------------------------------------------------------------------------
# Normalization + scoring (pure; stdlib only)
# ---------------------------------------------------------------------------

_WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _normalize(name: str) -> str:
    """Lowercase, collapse non-alphanumerics to single spaces, strip."""
    if not isinstance(name, str):
        return ""
    return " ".join(_WORD_RE.findall(name.lower()))


def _tokens(name: str) -> set:
    return set(_WORD_RE.findall(name.lower()))


def score_name(query: str, candidate_name: str) -> float:
    """Score how well `candidate_name` matches `query` in [0, 1].

    Blend of character-level closeness (difflib) and token-set overlap, with an
    exact-match short-circuit, a containment boost, and a query-is-subset bonus
    (so a partial name like "beehive" matches "Beehive Waldorff" strongly).
    """
    nq = _normalize(query)
    nc = _normalize(candidate_name)
    if not nq or not nc:
        return 0.0
    if nq == nc:
        return 1.0

    ratio = difflib.SequenceMatcher(None, nq, nc).ratio()

    qt, ct = _tokens(query), _tokens(candidate_name)
    if qt and ct:
        inter = len(qt & ct)
        union = len(qt | ct)
        jaccard = inter / union if union else 0.0
        subset_bonus = 1.0 if qt and qt <= ct else (inter / len(qt) if qt else 0.0)
    else:
        jaccard = 0.0
        subset_bonus = 0.0

    # Containment: query string appears verbatim inside the candidate (or vice-versa).
    containment = 0.0
    if nq in nc or nc in nq:
        shorter, longer = (nq, nc) if len(nq) <= len(nc) else (nc, nq)
        containment = len(shorter) / len(longer) if longer else 0.0

    # Weighted blend. token subset/overlap is the most robust signal for loan names
    # (qualifiers like "senior"/"USD" or word-order shouldn't tank a real match).
    score = (0.30 * ratio) + (0.30 * jaccard) + (0.25 * subset_bonus) + (0.15 * containment)

    # Domain rule: when EVERY query token is a clean subset of the candidate's tokens (a
    # partial loan name like "beehive" against "Beehive Waldorff"), that is a strong,
    # high-confidence match — a partial name uniquely identifying a loan should resolve. Lift
    # the floor toward the fraction of the candidate the query covers (so a 1-of-2 token match
    # like "beehive"/"Beehive Waldorff" clears the high-confidence bar, while a 1-of-4 partial
    # stays lower / disambiguates).
    if qt and qt <= ct:
        coverage = len(qt) / len(ct) if ct else 0.0
        subset_floor = 0.80 + 0.20 * coverage   # 1-of-2 -> 0.90; 1-of-3 -> ~0.867; full -> 1.0
        score = max(score, subset_floor)
    elif ct and ct <= qt:
        # The candidate name is a SUBSET of the query tokens: the user supplied the full loan
        # name PLUS extra qualifier word(s) the name lacks ("beehive senior" -> "Beehive
        # Waldorff" has neither — but "beehive plaza" -> "Beehive" would). Lift toward the
        # fraction of the QUERY the candidate covers (a candidate that matches every word but
        # one is a strong, high-confidence resolution).
        coverage_q = len(ct) / len(qt) if qt else 0.0
        score = max(score, 0.70 + 0.25 * coverage_q)

    return max(0.0, min(1.0, round(score, 4)))


# ---------------------------------------------------------------------------
# The resolver
# ---------------------------------------------------------------------------

class ResolveError(RuntimeError):
    """A live fetch failed (transport/auth/GraphQL error) — surfaced, never fabricated."""


# Minimal selection for resolution: id + name (+ status for the candidate display).
_RESOLVE_SELECTION = "id name status"


def _build_loans_query() -> str:
    """The RELIABLE list query (searchString filter + offset paging)."""
    return (
        "query HCAResolveLoans($filter: LoansFilterInput, $skip: Int, $limit: Int) { "
        "loans(filter: $filter, skip: $skip, limit: $limit) { "
        f"totalFilteredRecords pageItems {{ {_RESOLVE_SELECTION} }} "
        "} }"
    )


class LoanResolver:
    """Fuzzy loan-name resolver over the RELIABLE `loans` list query.

    Construct with a `client` exposing `raw_query(query, variables) -> data` (the
    LiveGraphQLClient from hca-live.py satisfies this). Tests inject a fake client
    backed by fixtures. When no client is supplied, a live one is built lazily from a
    LiveBackend (requires Doppler-injected creds).
    """

    def __init__(self, *, client=None,
                 high_confidence: float = HIGH_CONFIDENCE,
                 ambiguity_gap: float = AMBIGUITY_GAP,
                 min_candidate_score: float = MIN_CANDIDATE_SCORE,
                 fetch_limit: int = DEFAULT_FETCH_LIMIT):
        self._client = client
        self._high = float(high_confidence)
        self._gap = float(ambiguity_gap)
        self._min = float(min_candidate_score)
        self._limit = int(fetch_limit)

    # --- live client (lazy) ------------------------------------------------
    def _ensure_client(self):
        if self._client is not None:
            return self._client
        ad = _adapter()
        try:
            self._client = ad.LiveBackend().live_client()
        except getattr(ad, "NoLiveDataError", Exception) as e:
            # Missing creds -> a clean ResolveError (NO live data; never fabricates rows).
            raise ResolveError(
                "no live Hypercore credentials (CLIENT_ID / HYPERCORE_CLIENT_SECRET absent) "
                "— run via `doppler run --project hypercore-ask --config dev_personal -- ...`"
            ) from None
        return self._client

    # --- fetch real loans via the reliable list query ----------------------
    def _fetch_loans(self, search_string: Optional[str]) -> list:
        """Fetch real loan rows (id, name, status) via loans(filter:{searchString}).

        Walks offset pages to completion (bounded by totalFilteredRecords). Returns the
        raw pageItems list. Raises ResolveError on a live failure (never fabricates rows).
        """
        client = self._ensure_client()
        query = _build_loans_query()
        filt = {"searchString": search_string} if search_string else {}
        rows: list = []
        skip = 0
        reported_total = None
        pages = 0
        while True:
            pages += 1
            if pages > 1000:  # safety bound
                break
            variables = {"filter": filt, "skip": skip, "limit": self._limit}
            try:
                data = client.raw_query(query, variables)
            except Exception as e:  # transport/auth/GraphQL error — surface, never invent
                raise ResolveError(
                    f"loan list fetch failed: {type(e).__name__}: {str(e)[:200]}"
                ) from None
            page = (data or {}).get("loans") or {}
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
        """Candidate searchString tokens to try against the server-side filter.

        The full query first (most specific), then the single most-distinctive token
        (so 'beehive senior' still pulls 'Beehive Waldorff' which lacks 'senior'), then
        an UNFILTERED fetch as a final fallback so a real loan is never missed because the
        server-side searchString filter was too strict.
        """
        nq = _normalize(name_query)
        toks = [t for t in nq.split() if len(t) >= 3] or nq.split()
        # longest token tends to be the most distinctive loan name root.
        toks_sorted = sorted(set(toks), key=lambda t: -len(t))
        out = []
        if nq:
            out.append(nq)
        if toks_sorted:
            out.append(toks_sorted[0])
        out.append(None)  # unfiltered fallback
        # de-dup preserving order
        seen, ordered = set(), []
        for s in out:
            key = s if s is not None else "__ALL__"
            if key not in seen:
                seen.add(key)
                ordered.append(s)
        return ordered

    # --- public: resolve a name query --------------------------------------
    def resolve_loan(self, name_query: str) -> dict:
        """Resolve a loan-name query into {match, candidates, ...}.

        Returns a dict:
            {
              "query": <original query>,
              "match": {id, name, score, status} | None,   # set ONLY on a high-confidence
                                                            #  single match (auto-resolve)
              "resolved": bool,                              # True iff `match` is populated
              "ambiguous": bool,                             # True when >1 plausible candidate
              "candidates": [ {id, name, score, status}, ...],  # ranked, real API rows
              "echo": <str|None>,   # human echo string when resolved (for the caller to print)
              "reason": <str>,      # why this outcome (resolved/ambiguous/no_match)
            }

        Policy: exactly one high-confidence match -> resolve + echo. Multiple/low-confidence
        -> candidates for disambiguation (NEVER silently pick). No match -> empty candidates.
        """
        if not isinstance(name_query, str) or not name_query.strip():
            return {"query": name_query, "match": None, "resolved": False,
                    "ambiguous": False, "candidates": [], "echo": None,
                    "reason": "empty query"}

        # Fetch via the reliable list query; try progressively broader searchStrings so a
        # real loan is never missed by an over-strict server-side filter.
        rows_by_id: dict = {}
        for st in self._search_tokens(name_query):
            for r in self._fetch_loans(st):
                rid = r.get("id")
                if rid is not None and rid not in rows_by_id:
                    rows_by_id[rid] = r
            # Once we have a clearly-strong hit from a specific filter we could stop early,
            # but pooling all rows then ranking is simplest + safest (still bounded).
        rows = list(rows_by_id.values())

        scored = []
        for r in rows:
            name = r.get("name")
            if not name:
                continue
            sc = score_name(name_query, name)
            scored.append({"id": r.get("id"), "name": name, "score": sc,
                           "status": r.get("status")})
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

def resolve_loan(name_query: str, *, client=None, **kw) -> dict:
    """One-shot: build a resolver and resolve a single loan-name query."""
    return LoanResolver(client=client, **kw).resolve_loan(name_query)


# ---------------------------------------------------------------------------
# CLI — `--resolve "<loan name>"`. Prints the ranked candidates / resolution as JSON.
# Loan NAMES are portfolio reference data (not borrower PII), safe to print.
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="acos-hypercore-ask fuzzy loan-name resolver (reliable list query).")
    parser.add_argument("--resolve", dest="resolve", metavar="LOAN_NAME",
                        help="loan name (or partial) to resolve to a real loan id")
    args = parser.parse_args(argv)
    if not args.resolve:
        parser.error('a loan name is required: --resolve "beehive"')
    try:
        result = resolve_loan(args.resolve)
    except ResolveError as e:
        print(json.dumps({"error": str(e), "resolved": False, "candidates": []}, indent=2))
        return 2
    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("resolved") else 1


if __name__ == "__main__":
    sys.exit(main())
