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


def _learned():
    return _load("hca_learned", "hca-learned.py")


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

# Hierarchy selection for drill-down. Uses the RELIABLE parentLoan edge (child -> parent). The
# reverse edge groupSubLoans is present in the schema but returned EMPTY by the backend
# (verified live 2026-07 on the North Carolina II facility), so tranche enumeration keys on
# parentLoan.id, never on groupSubLoans.
_TREE_SELECTION = "id name status parentLoan { id name status }"


def _build_loans_query(selection: str = _RESOLVE_SELECTION) -> str:
    """The RELIABLE list query (searchString filter + offset paging), with a caller-chosen field
    selection (defaults to the minimal id/name/status used for resolution)."""
    return (
        "query HCAResolveLoans($filter: LoansFilterInput, $skip: Int, $limit: Int) { "
        "loans(filter: $filter, skip: $skip, limit: $limit) { "
        f"totalFilteredRecords pageItems {{ {selection} }} "
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
                 fetch_limit: int = DEFAULT_FETCH_LIMIT,
                 learned=None):
        self._client = client
        self._high = float(high_confidence)
        self._gap = float(ambiguity_gap)
        self._min = float(min_candidate_score)
        self._limit = int(fetch_limit)
        # Optional LearnedStore (hca-learned). When present, a CONFIRMED alias resolves the name
        # directly ("learn routing, never values" — the id is re-fetched live downstream). None
        # preserves the pure-fuzzy behavior the existing resolver tests assert.
        self._learned = learned

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
    def _fetch_loans(self, search_string: Optional[str],
                     selection: str = _RESOLVE_SELECTION) -> list:
        """Fetch real loan rows via loans(filter:{searchString}) with a chosen field selection.

        Walks offset pages to completion (bounded by totalFilteredRecords). Returns the
        raw pageItems list. Raises ResolveError on a live failure (never fabricates rows).
        """
        client = self._ensure_client()
        query = _build_loans_query(selection)
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
        """Progressively broader searchStrings to try against the server-side filter — a
        substance-preserving retry: every variant is built ONLY from the user's own words (a
        subset of the normalized query), so a loan is never invented, only searched-for more
        loosely when a stricter filter found nothing.

        Order, narrow -> wide: the full query (most specific); the two most-distinctive tokens
        joined; each individual token (longest first, so 'beehive senior' still pulls 'Beehive
        Waldorff' which lacks 'senior'); then an UNFILTERED fetch as the final fallback so a real
        loan is never missed because the server-side searchString filter was too strict.
        """
        nq = _normalize(name_query)
        toks = [t for t in nq.split() if len(t) >= 3] or nq.split()
        # longest tokens tend to be the most distinctive loan-name roots.
        toks_sorted = sorted(set(toks), key=lambda t: -len(t))
        out = []
        if nq:
            out.append(nq)                                  # full query (most specific)
        if len(toks_sorted) >= 2:
            out.append(" ".join(toks_sorted[:2]))           # two most-distinctive tokens
        out.extend(toks_sorted)                             # each token alone, longest first
        out.append(None)                                    # unfiltered fallback (never miss)
        # de-dup preserving order
        seen, ordered = set(), []
        for s in out:
            key = s if s is not None else "__ALL__"
            if key not in seen:
                seen.add(key)
                ordered.append(s)
        return ordered

    def _live_loan_by_id(self, loan_id, name_hint) -> Optional[dict]:
        """Fetch the CURRENT row for a known loan id via the RELIABLE list query — searchString
        built from the name_hint, with the unfiltered fallback so the loan is found even if the
        hint is stale. Returns the live {id, name, status} row, or None if the id no longer
        resolves to any loan. Never fabricates: only a row the API actually returned."""
        target = str(loan_id)
        for st in self._search_tokens(name_hint or ""):
            for r in self._fetch_loans(st):
                if str(r.get("id")) == target:
                    return r
        return None

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

        # LEARNED ALIAS (routing only). A CONFIRMED name -> loan id resolves directly, WITHOUT
        # re-scoring — this is how an off-name query like "409 Hodson" (which shares no distinctive
        # token with "North Carolina II - 409 High Point") resolves next time. The learned id is
        # RE-VERIFIED live here: we fetch the current row and return its LIVE name/status (never the
        # stored label, which could drift). A dangling alias (id no longer resolves) is NOT trusted
        # — we fall through to fuzzy/partial resolution rather than return a stale id.
        if self._learned is not None:
            le = self._learned.entity_for_query(name_query)
            if le and le.get("entity_type") == "loan" and str(le.get("id") or "").strip():
                lid = str(le["id"])
                live = self._live_loan_by_id(lid, le.get("name"))
                if live is not None:
                    m = {"id": lid, "name": live.get("name"), "score": 1.0,
                         "status": live.get("status")}
                    return {"query": name_query, "match": m, "resolved": True, "ambiguous": False,
                            "candidates": [m], "via": "learned",
                            "echo": (f"learned routing: {name_query!r} -> "
                                     f"{(live.get('name') or lid)!r} ({lid}) [verified live]"),
                            "reason": "resolved via a learned (confirmed) alias, re-verified live"}
                # dangling learned alias -> do not trust it; continue to fuzzy/partial below.

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
            # PARTIAL-SIGNAL FALLBACK: no candidate cleared the full-name threshold, but the query
            # may still name a real loan by an attribute (a street number, a distinctive word).
            # Surface loans that share such a DISCRIMINATOR token so the caller can offer them for
            # drill-down, instead of a dead-end miss. These are capped below high-confidence and
            # ALWAYS disambiguate — never auto-resolve.
            partial = self._partial_signal_candidates(name_query, rows)
            if partial:
                return {"query": name_query, "match": None, "resolved": False,
                        "ambiguous": True, "candidates": partial, "echo": None, "partial": True,
                        "reason": ("no full-name match; showing partial/attribute matches on a "
                                   "shared discriminator token — disambiguation required "
                                   "(never auto-picked)")}
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


    # --- partial-signal surfacing (Layer 1) --------------------------------
    def _partial_signal_candidates(self, name_query: str, rows: list) -> list:
        """Surface loans sharing a DISCRIMINATOR token with the query when no full-name match
        cleared the threshold. Discriminators = numeric tokens (a street number like '409' is
        very selective) + alpha tokens of length >= 3 (drops noise like 'st'/'of'). Scored by the
        fraction of discriminators matched, CAPPED below high-confidence so these always
        disambiguate (never auto-resolve). Returns a ranked list (may be empty)."""
        qtoks = _tokens(name_query)
        disc = {t for t in qtoks if t.isdigit() or len(t) >= 3}
        if not disc:
            return []
        out = []
        for r in rows:
            name = r.get("name")
            if not name:
                continue
            hits = disc & _tokens(name)
            if not hits:
                continue
            num_hit = any(h.isdigit() for h in hits)
            frac = len(hits) / len(disc)
            # 0.40 base + up to 0.39 for coverage + 0.10 if a numeric discriminator matched;
            # hard-capped at 0.79 (< HIGH_CONFIDENCE) so a partial hit can never auto-resolve.
            score = min(0.79, round(0.40 + 0.39 * frac + (0.10 if num_hit else 0.0), 4))
            out.append({"id": r.get("id"), "name": name, "score": score,
                        "status": r.get("status"), "partial": True,
                        "matched_tokens": sorted(hits)})
        out.sort(key=lambda c: (-c["score"], str(c.get("name"))))
        return out

    # --- native hierarchical drill-down (Layer 2) --------------------------
    def group_tree(self, name_query: str, *, seed_id: Optional[str] = None) -> dict:
        """The multi-tranche facility tree for a loan name (or a seed id), via the RELIABLE
        parentLoan edge. Returns:
            {query, state ∈ {OK, SINGLE, NO_MATCH}, root:{id,name}|None,
             tranches:[{id,name,status,is_root}], via, is_multi_tranche, reason}
        Enumerates tranches by matching parentLoan.id == root.id (the reverse groupSubLoans edge
        is not populated by the backend). Read-only; real rows only, never invented."""
        # 1) gather rows matching the query (with the hierarchy selection).
        rows_by_id: dict = {}
        for st in self._search_tokens(name_query):
            for r in self._fetch_loans(st, selection=_TREE_SELECTION):
                rid = r.get("id")
                if rid is not None and str(rid) not in rows_by_id:
                    rows_by_id[str(rid)] = r
        if not rows_by_id:
            return {"query": name_query, "state": "NO_MATCH", "root": None, "tranches": [],
                    "via": "parentLoan", "is_multi_tranche": False,
                    "reason": "no loans matched the query"}

        # 2) choose the seed: an explicit id if given, else the best name-scored row that clears
        #    the minimum score. (The searchString fetch includes an UNFILTERED fallback so a real
        #    loan is never missed — which means rows_by_id is rarely empty; the score gate, not
        #    empty rows, is what distinguishes a real facility from a genuine miss.)
        seed = None
        if seed_id is not None:
            seed = rows_by_id.get(str(seed_id))
        if seed is None:
            best = sorted(rows_by_id.values(),
                          key=lambda r: -score_name(name_query, r.get("name") or ""))[0]
            if score_name(name_query, best.get("name") or "") >= self._min:
                seed = best
        if seed is None:
            return {"query": name_query, "state": "NO_MATCH", "root": None, "tranches": [],
                    "via": "parentLoan", "is_multi_tranche": False,
                    "reason": "no loan matched the query above the minimum score"}

        # 3) the facility ROOT: the seed's parent if it has one, else the seed itself.
        par = seed.get("parentLoan") or None
        if par and par.get("id"):
            root_id, root_name = str(par["id"]), par.get("name")
        else:
            root_id, root_name = str(seed.get("id")), seed.get("name")

        # 4) enumerate the tranches: broaden the search by the root's name prefix so every sibling
        #    is pulled, then keep the root + every loan whose parentLoan.id == root_id.
        prefix = (root_name or name_query).split(" - ")[0].strip() or name_query
        tree_rows: dict = dict(rows_by_id)
        for st in self._search_tokens(prefix):
            for r in self._fetch_loans(st, selection=_TREE_SELECTION):
                rid = r.get("id")
                if rid is not None and str(rid) not in tree_rows:
                    tree_rows[str(rid)] = r

        # Prefer the LIVE fetched row's name for the root over the (possibly stale) name carried
        # on the child's parentLoan edge, and use that ONE value everywhere so the same root id
        # never appears with two different names in the same response.
        root_row = tree_rows.get(root_id)
        root_display = root_row.get("name") if root_row else root_name
        root_status = root_row.get("status") if root_row else None
        tranches = [{"id": root_id, "name": root_display, "status": root_status, "is_root": True}]
        for rid, r in tree_rows.items():
            p = r.get("parentLoan") or {}
            if str(p.get("id")) == root_id and rid != root_id:
                tranches.append({"id": rid, "name": r.get("name"),
                                 "status": r.get("status"), "is_root": False})

        tranches.sort(key=lambda t: (not t["is_root"],
                                     int(t["id"]) if str(t["id"]).isdigit() else 0))
        is_multi = len(tranches) > 1
        return {"query": name_query, "state": "OK" if is_multi else "SINGLE",
                "root": {"id": root_id, "name": root_display}, "tranches": tranches,
                "via": "parentLoan", "is_multi_tranche": is_multi,
                "reason": (f"multi-tranche facility: {len(tranches) - 1} tranche(s) under the root"
                           if is_multi else "no sub-tranches found (standalone loan)")}


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
    parser.add_argument("--group-tree", dest="group_tree", metavar="LOAN_NAME",
                        help="show the multi-tranche facility tree (root + tranches) for a name")
    parser.add_argument("--no-learned", dest="no_learned", action="store_true",
                        help="ignore the learned-alias store (pure fuzzy resolution)")
    args = parser.parse_args(argv)
    if not args.resolve and not args.group_tree:
        parser.error('provide --resolve "beehive" or --group-tree "North Carolina II"')
    # Consult the learned-alias store by default so a CONFIRMED off-name query resolves directly.
    learned = None if args.no_learned else _learned().default_store()
    resolver = LoanResolver(learned=learned)
    try:
        if args.group_tree:
            result = resolver.group_tree(args.group_tree)
            print(json.dumps(result, indent=2, default=str))
            return 0 if result.get("state") in ("OK", "SINGLE") else 1
        result = resolver.resolve_loan(args.resolve)
    except ResolveError as e:
        print(json.dumps({"error": str(e), "resolved": False, "candidates": []}, indent=2))
        return 2
    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("resolved") else 1


if __name__ == "__main__":
    sys.exit(main())
