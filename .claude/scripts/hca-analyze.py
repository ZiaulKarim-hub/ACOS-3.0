#!/usr/bin/env python3
"""hca-analyze.py — PORTFOLIO ANALYSIS on provenance-bound figures (SLICE-HCA-15).

The figures layer (hca-figures.py) answers ONE loan at a time. This module answers questions
ABOUT THE WHOLE PORTFOLIO — rankings, roll-ups, filters, concentration, and covenant-breach
scans — WITHOUT giving up the no-hallucination contract the rest of the skill enforces.

THE ONE BULK FETCH (the spine of this module)
  A portfolio question needs every loan's key figures. Rather than N per-loan fetches, this
  module does ONE efficient bulk walk of the `loans(skip,limit){...}` list path to COMPLETION
  (the list query returns every loan's headline summary in pages), and caches the WHOLE walked
  result as a SINGLE immutable Tier-1 RawApiResponse:

      loans(skip,limit){ totalFilteredRecords pageItems{
        id name status currency commitment scheduleEndDate scheduleExpectedEndDate
        summary{ totalOutstanding{total principal interest totalFees totalPenalties}
                 totalDue{total} overdue{total} totalDisbursed } } }

  Provenance for EVERY analysis value = a json_field_path into THAT one Tier-1 record
  ($.body.data[i].<field>), so any ranking row / aggregate contributor / breach flag is
  independently re-resolvable. The pagination-complete gate applies to the bulk fetch: a
  truncated walk REFUSES the analysis (an analysis over a partial book is never delivered).

WHAT IT COMPUTES (all on the in-memory bulk rows, all provenance-bound)
  - RANKINGS / TOP-N    : top loans by outstanding / closest to maturity / largest overdue /
                          highest utilization. Each ranked row carries its figure value + a
                          provenance pointer into the bulk response.
  - AGGREGATIONS        : total outstanding / commitment / overdue, weighted-average rate,
                          weighted-average maturity (WAM), count by status. Each aggregate
                          RECONCILES (sum of parts == the reported total it claims) and carries
                          aggregate provenance (one contributor binding per source row).
  - FILTERING           : overdue loans / maturing within N days / over $X outstanding / active.
  - CONCENTRATION       : exposure by status (and by client when a client linkage exists),
                          top-N concentration (% of book in the top 5/10 loans).
  - COVENANT-BREACH SCAN: for KG-covered loans, compute LTV (+ debt yield / DSCR where NOI
                          exists) via hca-kg and flag breaches vs the PRISM thresholds
                          (LTV>0.75, debt_yield<0.08, DSCR<1.25). Loans NOT in the KG are listed
                          as "not assessable (no collateral data)" — NEVER silently dropped.

NEVER FABRICATE
  A loan missing a figure a given analysis needs is SURFACED (in a `skipped`/`unassessable`
  list with the reason) — it is never silently dropped and a value is never invented. A
  non-reconciling aggregate REFUSES.

INTERPRETIVE CONCLUSIONS (analytical judgments) -> CONSENSUS + STATED CRITERIA
  For an analytical JUDGMENT ("which loans are most at-risk?", "is the book concentrated?")
  this module does NOT emit an opaque opinion. It applies STATED, surfaced criteria (e.g.
  at-risk = overdue>0 OR within 30d of maturity OR LTV>threshold), shows the criteria + the
  supporting figures, and routes the CONCLUSION through hca-consensus.run_consensus so blind
  agents must agree before the judgment is delivered (no silent pick). The deterministic
  evidence (the rows + criteria) is always returned alongside.

GROUND RULES (memory/decisions/2026-06-18-hca-build-ground-rules.md):
  - Python 3 stdlib ONLY. No third-party deps. No model calls; never ANTHROPIC_API_KEY.
    (Consensus blind agents are spawned by the orchestrator's Task() — not a model API key.)
  - Read-only: the only API touch is the `loans` LIST query (a GraphQL `query`).
  - No real borrower PII committed: totals / rankings / loan NAMES are portfolio reference data
    and are safe; no borrower-level PII is printed or stored. Tests use synthetic fixtures.

Slices 01-14 modules are COMPOSE-ONLY here (imported, never edited).
"""

from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import os
import sys
from typing import Any, Callable, Optional


# ---------------------------------------------------------------------------
# Terminal states + refusal reason codes (mirror the spine envelope vocabulary)
# ---------------------------------------------------------------------------

STATE_DELIVERED = "DELIVERED"
STATE_REFUSED = "REFUSED"
STATE_NO_LIVE_DATA = "NO_LIVE_DATA"
STATE_ESCALATED = "ESCALATED"            # interpretive judgment: agents did not reach quorum

REASON_BAD_INPUT = "BAD_INPUT"
REASON_FETCH_EMPTY = "FETCH_EMPTY"           # bulk fetch returned no loans
REASON_INCOMPLETE = "PAGINATION_INCOMPLETE"  # the bulk walk did not reach totalFilteredRecords
REASON_PROVENANCE = "PROVENANCE_REFUSED"     # an analysis value could not bind to Tier-1
REASON_RECONCILE = "RECONCILE_FAILED"        # an aggregate's parts do not sum to its claimed total
REASON_UNKNOWN_ANALYSIS = "UNKNOWN_ANALYSIS" # the analysis kind is not supported
REASON_NO_CONSENSUS = "NO_CONSENSUS"         # interpretive judgment: < quorum after re-dispatch


# Reconciliation tolerance (dollars). Sum-of-parts == claimed total to the cent.
RECONCILE_TOLERANCE = 0.01

# PRISM covenant thresholds (planning/preeng/001-hypercore-ask/_prism-domain-learnings.md §1.3).
PRISM_MAX_LTV = 0.75       # LTV above this is a breach (OKOA bridge-loan max)
PRISM_MIN_DEBT_YIELD = 0.08  # debt yield below this is a breach
PRISM_MIN_DSCR = 1.25      # DSCR below this is a breach

# Default "near maturity" window (days) for the stated at-risk criteria.
DEFAULT_NEAR_MATURITY_DAYS = 30


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


def _cache():
    return _load("hca_cache", "hca-cache.py")


def _provenance():
    return _load("hca_provenance", "hca-provenance.py")


def _kg():
    return _load("hca_kg", "hca-kg.py")


def _consensus():
    return _load("hca_consensus", "hca-consensus.py")


def _gates():
    return _load("hca_gates", "hca-gates.py")


def _figures():
    return _load("hca_figures", "hca-figures.py")


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> datetime.date:
    return datetime.datetime.now(datetime.timezone.utc).date()


def _parse_date(s: Any) -> Optional[datetime.date]:
    """Parse a YYYY-MM-DD(...) date string to a date, or None. Tolerant of a time suffix."""
    if not isinstance(s, str) or not s.strip():
        return None
    raw = s.strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    # ISO with offset / fromisoformat fallback
    try:
        return datetime.date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


# ---------------------------------------------------------------------------
# Envelope builders (the standard analysis envelope — report-shaped)
# ---------------------------------------------------------------------------

def _envelope(state: str, *, answer, analysis: str, rows: list, aggregates: Optional[dict],
              provenance: Optional[dict], gate_verdict, complete: bool, refusals: list,
              skipped: Optional[list] = None, meta: Optional[dict] = None) -> dict:
    """The analysis envelope. Mirrors the spine's envelope shape and adds analysis fields.

    Shape:
        { state, answer, analysis,
          rows: [ {label/name, loan_id, value..., provenance} ],   # ranked / filtered rows
          aggregates: { <name>: {value, provenance, reconciles} },
          skipped: [ {loan_id, name, reason} ],   # loans surfaced (never silently dropped)
          provenance: {bulk_raw_response_id, ...},
          gate_verdict, complete, refusals, meta }
    """
    return {
        "state": state,
        "answer": answer,
        "analysis": analysis,
        "rows": rows,
        "aggregates": aggregates,
        "skipped": skipped or [],
        "provenance": provenance,
        "gate_verdict": gate_verdict,
        "complete": complete,
        "refusals": refusals,
        "meta": meta or {},
    }


def _refused(analysis: str, reason_code: str, reason: str, *,
             provenance: Optional[dict] = None, meta: Optional[dict] = None,
             skipped: Optional[list] = None) -> dict:
    return _envelope(STATE_REFUSED, answer=None, analysis=analysis, rows=[], aggregates=None,
                     provenance=provenance, gate_verdict=None, complete=False,
                     refusals=[{"reason_code": reason_code, "reason": reason}],
                     skipped=skipped, meta=meta)


def _no_live(analysis: str, reason: str) -> dict:
    return _envelope(STATE_NO_LIVE_DATA, answer=None, analysis=analysis, rows=[],
                     aggregates=None, provenance=None, gate_verdict=None, complete=False,
                     refusals=[{"reason_code": STATE_NO_LIVE_DATA, "reason": reason}],
                     meta={"message": "no live data — Hypercore access not provisioned"})


# ---------------------------------------------------------------------------
# The bulk-portfolio fetch + Tier-1 cache (the ONE fetch)
# ---------------------------------------------------------------------------

# The list selection the brief specifies: every loan's key figures in ONE walk. Each money block
# is an InstallmentComponents-shaped object carrying `total` + components.
_BULK_SELECTION = (
    "id name status currency commitment scheduleEndDate scheduleExpectedEndDate "
    "annualInterestRate "
    "summary { "
    "totalOutstanding { total principal interest totalFees totalPenalties } "
    "totalDue { total } "
    "overdue { total } "
    "totalDisbursed "
    "}"
)

_BULK_QUERY = (
    "query HCAPortfolio($skip: Int, $limit: Int, $filter: LoansFilterInput) { "
    "loans(skip: $skip, limit: $limit, filter: $filter) { "
    f"totalFilteredRecords pageItems {{ {_BULK_SELECTION} }} "
    "} }"
)

_BULK_PAGE_LIMIT = 100
_MAX_PAGES = 10_000


class PortfolioFetcher:
    """Does ONE bulk walk of the loans list to completion, caches it as a single Tier-1 record.

    Construct with a `client` exposing raw_query(query, variables) -> data (LiveGraphQLClient
    satisfies this; tests inject a fake). The walked pageItems list is cached as ONE immutable
    Tier-1 RawApiResponse so every downstream analysis value binds to a json_field_path into it
    ($.body.data[i].<field>). The pagination-complete flag rides on the record so the analysis
    can REFUSE on a truncated book.
    """

    def __init__(self, *, client=None, cache=None, page_limit: int = _BULK_PAGE_LIMIT,
                 retry_attempts: Optional[int] = None, retry_backoff_s: Optional[float] = None,
                 sleep: Optional[Callable[[float], None]] = None):
        self._client = client
        self._cachelib = _cache()
        self._cache = cache or self._cachelib.TwoTierCache()
        self._page_limit = int(page_limit)
        self._memo: Optional[dict] = None  # one fetch per fetcher instance
        # Bulk pages are subject to the same intermittent HTTP 500 as the other live paths;
        # wrap each page fetch in the shared figures retry helper (on top of the universal
        # transport-level retry). Defaults mirror the figures module so the policy is uniform.
        fig = _figures()
        self._retry_attempts = int(retry_attempts) if retry_attempts is not None \
            else fig.RETRY_ATTEMPTS
        self._retry_backoff_s = float(retry_backoff_s) if retry_backoff_s is not None \
            else fig.RETRY_BACKOFF_S
        self._sleep = sleep

    def _ensure_client(self):
        if self._client is not None:
            return self._client
        ad = _adapter()
        self._client = ad.LiveBackend().live_client()
        return self._client

    def fetch(self) -> dict:
        """Walk the loans list to completion and cache it as ONE Tier-1 record.

        Returns {"ok":True,"rows":[...],"rid":<tier1 id>,"complete":bool,"reported_total":int,
        "fetched_at":...} or {"ok":False,"state":..,"reason_code":..,"reason":..}. Memoized.
        """
        if self._memo is not None:
            return self._memo
        try:
            client = self._ensure_client()
        except Exception as e:  # noqa: BLE001 — classified below
            ad = _adapter()
            if isinstance(e, getattr(ad, "NoLiveDataError", ())):
                res = {"ok": False, "state": STATE_NO_LIVE_DATA, "reason_code": STATE_NO_LIVE_DATA,
                       "reason": str(e)}
            else:
                res = {"ok": False, "state": STATE_REFUSED, "reason_code": REASON_FETCH_EMPTY,
                       "reason": f"could not build live client: {type(e).__name__}: {str(e)[:160]}"}
            self._memo = res
            return res

        rows: list = []
        skip = 0
        reported_total: Optional[int] = None
        pages = 0
        complete = False
        fig = _figures()
        retry_kwargs = {"attempts": self._retry_attempts, "backoff_s": self._retry_backoff_s}
        if self._sleep is not None:
            retry_kwargs["sleep"] = self._sleep
        try:
            while True:
                pages += 1
                if pages > _MAX_PAGES:
                    break
                variables = {"skip": skip, "limit": self._page_limit, "filter": {}}
                # Retry each bulk page on the intermittent HTTP 500 before refusing.
                data, _attempts, _errs = fig._call_with_retry(
                    client, _BULK_QUERY, variables, **retry_kwargs)
                page = (data or {}).get("loans") or {}
                reported_total = page.get("totalFilteredRecords")
                items = page.get("pageItems") or []
                rows.extend(items)
                if reported_total is not None and len(rows) >= reported_total:
                    complete = True
                    break
                if len(items) < self._page_limit:
                    # short page: complete only if we matched a known total (else truncation)
                    complete = (reported_total is None) or (len(rows) >= (reported_total or 0))
                    break
                skip += self._page_limit
        except Exception as e:  # noqa: BLE001 — surface, never fabricate
            res = {"ok": False, "state": STATE_REFUSED, "reason_code": REASON_FETCH_EMPTY,
                   "reason": (f"bulk portfolio fetch failed: {type(e).__name__}: "
                              f"{str(e)[:200]} (refusing rather than analyzing a partial book)")}
            self._memo = res
            return res

        # Cache the WHOLE walked result as ONE immutable Tier-1 record.
        fetched_at = _now_iso()
        ad = _adapter()
        raw = ad.make_raw_api_response(
            raw_response_id=f"live:portfolioBulk:{fetched_at}",
            endpoint="loans",
            request_params={"graphql_operation": "HCAPortfolio", "page_limit": self._page_limit},
            timestamp=fetched_at, http_status=200, cursor=None, reported_total=reported_total,
            body={"data": rows, "complete": complete, "pages": pages,
                  "reported_total": reported_total,
                  "provenance": {"fetched_at": fetched_at, "operation": "loans",
                                 "selection": "portfolio-bulk"}},
            backend="live")
        rid = self._cache.put_raw(raw)
        stored = self._cache.get_raw(rid)
        res = {"ok": True, "rows": stored.get("body", {}).get("data", rows), "rid": rid,
               "raw": stored, "complete": complete, "reported_total": reported_total,
               "pages": pages, "fetched_at": fetched_at}
        self._memo = res
        return res


# ---------------------------------------------------------------------------
# Per-loan figure extraction off a bulk row (provenance path into the bulk record)
# ---------------------------------------------------------------------------

# Logical figure name -> (dotted path inside the loan row, unit). The dotted path is also the
# suffix of the Tier-1 json_field_path ($.body.data[i].<path>).
_ROW_FIGURES = {
    "outstanding": ("summary.totalOutstanding.total", "currency"),
    "principal_outstanding": ("summary.totalOutstanding.principal", "currency"),
    "accrued_interest": ("summary.totalOutstanding.interest", "currency"),
    "fees_outstanding": ("summary.totalOutstanding.totalFees", "currency"),
    "penalties_outstanding": ("summary.totalOutstanding.totalPenalties", "currency"),
    "amount_due": ("summary.totalDue.total", "currency"),
    "overdue": ("summary.overdue.total", "currency"),
    "total_disbursed": ("summary.totalDisbursed", "currency"),
    "commitment": ("commitment", "currency"),
    "annual_interest_rate": ("annualInterestRate", "rate"),
    "maturity_date": ("scheduleEndDate", "date"),
}

_ABSENT = object()


def _walk_dotted(obj, dotted: str):
    """Walk a simple dotted path over nested dicts. Returns the value or _ABSENT."""
    if not dotted:
        return obj
    cur = obj
    for key in dotted.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return _ABSENT
        cur = cur[key]
    return cur


def _bulk_path(index: int, dotted: str) -> str:
    """The Tier-1 json_field_path for a figure on bulk row `index`."""
    return f"$.body.data[{index}].{dotted}"


def _row_value(row: dict, figure: str):
    """Resolve a logical figure on a bulk row. Returns (value, dotted_path) or (_ABSENT, path)."""
    dotted, _unit = _ROW_FIGURES[figure]
    return _walk_dotted(row, dotted), dotted


# ---------------------------------------------------------------------------
# The analyzer
# ---------------------------------------------------------------------------

# Analyses that rank/filter/concentrate on a single numeric per-loan figure.
_NUMERIC_FIGURE_ANALYSES = {
    "outstanding", "overdue", "commitment", "amount_due", "total_disbursed",
    "accrued_interest", "principal_outstanding", "penalties_outstanding",
}


class PortfolioAnalyzer:
    """Runs portfolio analyses on the ONE bulk Tier-1 record, every value provenance-bound.

    Construct with a `fetcher` (PortfolioFetcher), a shared cache + provenance engine, and an
    optional kg_store (for the covenant-breach scan). Each public analysis returns the standard
    analysis envelope: rows/aggregates carry a provenance pointer into the bulk record, the
    pagination-complete gate is enforced, and a loan missing a needed figure is SURFACED in
    `skipped` (never dropped, never invented).
    """

    def __init__(self, *, fetcher: Optional[PortfolioFetcher] = None, client=None,
                 cache=None, engine=None, kg_store=None):
        self._cachelib = _cache()
        self._provlib = _provenance()
        self._cache = cache or self._cachelib.TwoTierCache()
        self._fetcher = fetcher or PortfolioFetcher(client=client, cache=self._cache)
        self._engine = engine or self._provlib.ProvenanceEngine(cache=self._cache)
        self._kglib = _kg()
        self._kg_store = kg_store

    # --- shared: fetch + verify the bulk record (pagination-complete gate) ---
    def _load_portfolio(self, analysis: str):
        """Fetch the bulk record. Returns (rows, rid, fetched) on success, or an envelope on
        failure (NO_LIVE_DATA / FETCH_EMPTY / PAGINATION_INCOMPLETE)."""
        fetched = self._fetcher.fetch()
        if not fetched.get("ok"):
            if fetched.get("state") == STATE_NO_LIVE_DATA:
                return None, None, _no_live(analysis, fetched.get("reason", "no live data"))
            return None, None, _refused(analysis, fetched.get("reason_code", REASON_FETCH_EMPTY),
                                        fetched.get("reason", "bulk fetch failed"))
        rows = fetched.get("rows") or []
        if not rows:
            return None, None, _refused(analysis, REASON_FETCH_EMPTY,
                                        "no loans returned by the bulk fetch — cannot analyze "
                                        "an empty portfolio")
        # PAGINATION-COMPLETE GATE: an analysis over a truncated book is never delivered.
        if not fetched.get("complete"):
            return None, None, _refused(
                analysis, REASON_INCOMPLETE,
                (f"the bulk portfolio walk did not reach totalFilteredRecords "
                 f"({len(rows)} fetched / {fetched.get('reported_total')} reported) — refusing "
                 "(an analysis over a partial book is never delivered)"),
                provenance={"bulk_raw_response_id": fetched.get("rid")})
        return rows, fetched.get("rid"), fetched

    def _bind(self, value, rid: str, index: int, dotted: str, value_ref: str) -> Optional[dict]:
        """Provenance-bind a per-row value to the bulk Tier-1 record. Returns the provenance
        pointer dict on VERIFIED, or None on refusal (caller surfaces / refuses)."""
        tpath = _bulk_path(index, dotted)
        prov = self._engine.bind_and_verify(
            value, {"raw_response_id": rid, "json_field_path": tpath}, value_ref=value_ref)
        if prov["outcome"] != self._provlib.VERIFIED:
            return None
        return {"bulk_raw_response_id": rid, "json_field_path": tpath, "operation": "loans"}

    # --- collect a numeric figure across the portfolio (surfacing missing) --
    def _collect_figure(self, rows: list, rid: str, figure: str):
        """Return (present, skipped) where present = [{index,row,value,provenance}] for loans
        carrying a numeric `figure` (provenance-bound), and skipped = [{loan_id,name,reason}]
        for loans missing/non-numeric/unbindable that figure. Never drops a loan silently."""
        present, skipped = [], []
        for i, row in enumerate(rows):
            value, dotted = _row_value(row, figure)
            lid = str(row.get("id"))
            name = row.get("name")
            if value is _ABSENT or not _is_number(value):
                skipped.append({"loan_id": lid, "name": name,
                                "reason": f"{figure} absent/non-numeric on this loan"})
                continue
            prov = self._bind(value, rid, i, dotted, f"loan.{lid}.{figure}")
            if prov is None:
                skipped.append({"loan_id": lid, "name": name,
                                "reason": f"{figure} could not be provenance-bound to Tier-1"})
                continue
            present.append({"index": i, "row": row, "loan_id": lid, "name": name,
                            "value": float(value), "currency": row.get("currency"),
                            "provenance": prov})
        return present, skipped

    # =====================================================================
    # RANKINGS / TOP-N
    # =====================================================================
    def rank(self, figure: str, *, top_n: Optional[int] = 10, ascending: bool = False) -> dict:
        """Rank loans by a numeric figure (descending by default). top_n=None ranks all.

        Each ranked row carries its value + a provenance pointer into the bulk response. Loans
        missing the figure are surfaced in `skipped` (never dropped)."""
        analysis = f"rank_by_{figure}"
        if figure not in _NUMERIC_FIGURE_ANALYSES:
            return _refused(analysis, REASON_UNKNOWN_ANALYSIS,
                            f"cannot rank by {figure!r} (supported: "
                            f"{sorted(_NUMERIC_FIGURE_ANALYSES)})")
        rows, rid, res = self._load_portfolio(analysis)
        if rows is None:
            return res
        present, skipped = self._collect_figure(rows, rid, figure)
        present.sort(key=lambda r: (r["value"], str(r["name"])), reverse=not ascending)
        ranked = present[:top_n] if top_n else present
        out_rows = [{"rank": idx + 1, "loan_id": r["loan_id"], "name": r["name"],
                     "value": r["value"], "currency": r["currency"], "figure": figure,
                     "provenance": r["provenance"]}
                    for idx, r in enumerate(ranked)]
        direction = "ascending" if ascending else "descending"
        answer = (f"Top {len(out_rows)} loans by {figure} ({direction}). "
                  f"{len(present)} of {len(rows)} loans carried {figure}; "
                  f"{len(skipped)} surfaced as missing.")
        gate_verdict = {"outcome": "pass", "pagination_complete": True,
                        "ranked": len(out_rows), "assessed": len(present)}
        return _envelope(STATE_DELIVERED, answer=answer, analysis=analysis, rows=out_rows,
                         aggregates=None,
                         provenance={"bulk_raw_response_id": rid}, gate_verdict=gate_verdict,
                         complete=True, refusals=[], skipped=skipped,
                         meta={"figure": figure, "top_n": top_n, "direction": direction,
                               "total_loans": len(rows), "assessed": len(present)})

    def rank_by_maturity(self, *, top_n: Optional[int] = 10,
                         as_of: Optional[datetime.date] = None) -> dict:
        """Rank loans by how CLOSE they are to maturity (soonest first). Loans without a parseable
        maturity date are surfaced in `skipped`."""
        analysis = "loans_closest_to_maturity"
        rows, rid, res = self._load_portfolio(analysis)
        if rows is None:
            return res
        as_of = as_of or _today()
        present, skipped = [], []
        for i, row in enumerate(rows):
            value, dotted = _row_value(row, "maturity_date")
            lid = str(row.get("id"))
            name = row.get("name")
            d = _parse_date(value) if value is not _ABSENT else None
            if d is None:
                skipped.append({"loan_id": lid, "name": name,
                                "reason": "no parseable maturity date (scheduleEndDate) on this loan"})
                continue
            prov = self._bind(value, rid, i, dotted, f"loan.{lid}.maturity_date")
            if prov is None:
                skipped.append({"loan_id": lid, "name": name,
                                "reason": "maturity date could not be provenance-bound to Tier-1"})
                continue
            present.append({"index": i, "loan_id": lid, "name": name, "maturity_date": value,
                            "days_to_maturity": (d - as_of).days, "provenance": prov})
        present.sort(key=lambda r: (r["days_to_maturity"], str(r["name"])))
        ranked = present[:top_n] if top_n else present
        out_rows = [{"rank": idx + 1, "loan_id": r["loan_id"], "name": r["name"],
                     "maturity_date": r["maturity_date"],
                     "days_to_maturity": r["days_to_maturity"], "provenance": r["provenance"]}
                    for idx, r in enumerate(ranked)]
        answer = (f"{len(out_rows)} loans closest to maturity as of {as_of.isoformat()}. "
                  f"{len(present)} of {len(rows)} loans carried a maturity date; "
                  f"{len(skipped)} surfaced as missing.")
        gate_verdict = {"outcome": "pass", "pagination_complete": True, "ranked": len(out_rows)}
        return _envelope(STATE_DELIVERED, answer=answer, analysis=analysis, rows=out_rows,
                         aggregates=None, provenance={"bulk_raw_response_id": rid},
                         gate_verdict=gate_verdict, complete=True, refusals=[], skipped=skipped,
                         meta={"as_of": as_of.isoformat(), "top_n": top_n,
                               "total_loans": len(rows), "assessed": len(present)})

    def rank_by_utilization(self, *, top_n: Optional[int] = 10) -> dict:
        """Rank loans by utilization = total_disbursed / commitment (highest first). A loan with
        an absent/zero commitment or absent disbursed is surfaced in `skipped` (no div-by-zero)."""
        analysis = "highest_utilization"
        rows, rid, res = self._load_portfolio(analysis)
        if rows is None:
            return res
        present, skipped = [], []
        for i, row in enumerate(rows):
            disb, disb_path = _row_value(row, "total_disbursed")
            commit, commit_path = _row_value(row, "commitment")
            lid = str(row.get("id"))
            name = row.get("name")
            if disb is _ABSENT or not _is_number(disb):
                skipped.append({"loan_id": lid, "name": name,
                                "reason": "total_disbursed absent/non-numeric on this loan"})
                continue
            if commit is _ABSENT or not _is_number(commit) or float(commit) == 0.0:
                skipped.append({"loan_id": lid, "name": name,
                                "reason": "commitment absent/zero — utilization undefined"})
                continue
            p_disb = self._bind(disb, rid, i, disb_path, f"loan.{lid}.total_disbursed")
            p_commit = self._bind(commit, rid, i, commit_path, f"loan.{lid}.commitment")
            if p_disb is None or p_commit is None:
                skipped.append({"loan_id": lid, "name": name,
                                "reason": "utilization input could not be provenance-bound"})
                continue
            util = round(float(disb) / float(commit), 6)
            present.append({"loan_id": lid, "name": name, "value": util,
                            "total_disbursed": float(disb), "commitment": float(commit),
                            "provenance": {"derived": True,
                                           "formula": "total_disbursed / commitment",
                                           "total_disbursed": p_disb, "commitment": p_commit}})
        present.sort(key=lambda r: (r["value"], str(r["name"])), reverse=True)
        ranked = present[:top_n] if top_n else present
        out_rows = [{"rank": idx + 1, "loan_id": r["loan_id"], "name": r["name"],
                     "value": r["value"], "unit": "ratio", "figure": "utilization",
                     "total_disbursed": r["total_disbursed"], "commitment": r["commitment"],
                     "provenance": r["provenance"]}
                    for idx, r in enumerate(ranked)]
        answer = (f"Top {len(out_rows)} loans by utilization (total_disbursed / commitment). "
                  f"{len(present)} of {len(rows)} loans were assessable; "
                  f"{len(skipped)} surfaced as missing/undefined.")
        gate_verdict = {"outcome": "pass", "pagination_complete": True, "ranked": len(out_rows)}
        return _envelope(STATE_DELIVERED, answer=answer, analysis=analysis, rows=out_rows,
                         aggregates=None, provenance={"bulk_raw_response_id": rid},
                         gate_verdict=gate_verdict, complete=True, refusals=[], skipped=skipped,
                         meta={"figure": "utilization", "top_n": top_n,
                               "total_loans": len(rows), "assessed": len(present)})

    # =====================================================================
    # AGGREGATIONS / ROLL-UPS
    # =====================================================================
    def total(self, figure: str) -> dict:
        """Sum a numeric figure across the portfolio. The aggregate RECONCILES (sum of the bound
        per-loan parts == the delivered total) and carries aggregate provenance (one contributor
        binding per source row). A mixed-currency portfolio REFUSES (cannot sum across currencies).
        Loans missing the figure are surfaced (never dropped)."""
        analysis = f"total_{figure}"
        if figure not in _NUMERIC_FIGURE_ANALYSES:
            return _refused(analysis, REASON_UNKNOWN_ANALYSIS,
                            f"cannot total {figure!r} (supported: "
                            f"{sorted(_NUMERIC_FIGURE_ANALYSES)})")
        rows, rid, res = self._load_portfolio(analysis)
        if rows is None:
            return res
        present, skipped = self._collect_figure(rows, rid, figure)
        if not present:
            return _refused(analysis, REASON_FETCH_EMPTY,
                            f"no loan carried a numeric {figure} — cannot total",
                            provenance={"bulk_raw_response_id": rid}, skipped=skipped)
        currencies = {p["currency"] for p in present if p["currency"]}
        if len(currencies) > 1:
            return _refused(analysis, REASON_RECONCILE,
                            (f"portfolio {figure} spans mixed currencies {sorted(currencies)} — "
                             "refusing to sum across currencies"),
                            provenance={"bulk_raw_response_id": rid}, skipped=skipped,
                            meta={"currencies": sorted(currencies)})
        currency = (sorted(currencies) or [None])[0]
        parts = [p["value"] for p in present]
        total = round(sum(parts), 4)
        # AGGREGATE PROVENANCE: bind each contributor; verifies parts resolve + match Tier-1.
        contributing = [{"raw_response_id": rid, "json_field_path": p["provenance"]["json_field_path"]}
                        for p in present]
        agg = self._engine.bind_aggregate(total, contributing, contributing_values=parts,
                                          value_ref=f"portfolio.total_{figure}")
        if agg["outcome"] != self._provlib.VERIFIED:
            return _refused(analysis, REASON_PROVENANCE, agg.get("reason", "aggregate unbindable"),
                            provenance={"bulk_raw_response_id": rid}, skipped=skipped)
        # RECONCILIATION: the delivered total must equal the sum of the bound parts to the cent.
        recon_sum = round(sum(parts), 4)
        diff = round(abs(recon_sum - total), 6)
        reconciles = diff <= RECONCILE_TOLERANCE
        if not reconciles:
            return _refused(analysis, REASON_RECONCILE,
                            (f"total {figure} {total} does not reconcile to the sum of its "
                             f"{len(parts)} parts ({recon_sum}, diff={diff})"),
                            provenance={"bulk_raw_response_id": rid}, skipped=skipped)
        cur_str = f" {currency}" if currency else ""
        answer = (f"Total {figure} across {len(present)} of {len(rows)} loans is "
                  f"{total}{cur_str} (reconciles to the sum of {len(parts)} parts; "
                  f"{len(skipped)} loans surfaced as missing).")
        aggregates = {figure: {"value": total, "currency": currency, "reconciles": True,
                               "parts": len(parts), "diff": diff,
                               "provenance": {"aggregate": True, "bulk_raw_response_id": rid,
                                              "contributing": contributing}}}
        gate_verdict = {"outcome": "pass", "pagination_complete": True, "reconciliation_ok": True,
                        "single_currency": True, "sources": len(parts)}
        return _envelope(STATE_DELIVERED, answer=answer, analysis=analysis, rows=[],
                         aggregates=aggregates, provenance={"bulk_raw_response_id": rid},
                         gate_verdict=gate_verdict, complete=True, refusals=[], skipped=skipped,
                         meta={"figure": figure, "currency": currency, "total": total,
                               "assessed": len(present), "total_loans": len(rows)})

    def weighted_average_rate(self) -> dict:
        """Weighted-average interest rate = Σ(outstanding_i × rate_i) / Σ(outstanding_i)
        (PRISM blended-rate definition). Loans missing rate OR outstanding are surfaced."""
        return self._weighted_average("annual_interest_rate", "weighted_average_rate",
                                      "weighted-average interest rate")

    def weighted_average_maturity(self, *, as_of: Optional[datetime.date] = None) -> dict:
        """Weighted-average maturity (WAM) in days = Σ(outstanding_i × days_to_maturity_i) /
        Σ(outstanding_i) (PRISM WAM definition). Loans missing maturity OR outstanding surfaced."""
        analysis = "weighted_average_maturity"
        rows, rid, res = self._load_portfolio(analysis)
        if rows is None:
            return res
        as_of = as_of or _today()
        num = 0.0
        den = 0.0
        contributing = []
        used = 0
        skipped = []
        for i, row in enumerate(rows):
            out_v, out_path = _row_value(row, "outstanding")
            mat_v, mat_path = _row_value(row, "maturity_date")
            lid = str(row.get("id"))
            name = row.get("name")
            d = _parse_date(mat_v) if mat_v is not _ABSENT else None
            if out_v is _ABSENT or not _is_number(out_v) or d is None:
                skipped.append({"loan_id": lid, "name": name,
                                "reason": "missing outstanding or maturity date — excluded from WAM"})
                continue
            p_out = self._bind(out_v, rid, i, out_path, f"loan.{lid}.outstanding")
            if p_out is None:
                skipped.append({"loan_id": lid, "name": name,
                                "reason": "outstanding could not be provenance-bound"})
                continue
            days = (d - as_of).days
            num += float(out_v) * days
            den += float(out_v)
            contributing.append({"raw_response_id": rid,
                                 "json_field_path": p_out["json_field_path"]})
            used += 1
        if den == 0:
            return _refused(analysis, REASON_FETCH_EMPTY,
                            "no loan carried both outstanding and a maturity date — cannot weight",
                            provenance={"bulk_raw_response_id": rid}, skipped=skipped)
        wam_days = round(num / den, 2)
        answer = (f"Weighted-average maturity (WAM) across {used} of {len(rows)} loans is "
                  f"{wam_days} days from {as_of.isoformat()} "
                  f"(weighted by outstanding; {len(skipped)} loans surfaced as excluded).")
        aggregates = {"weighted_average_maturity_days": {
            "value": wam_days, "unit": "days", "as_of": as_of.isoformat(),
            "weighted_by": "outstanding", "weight_total": round(den, 4), "sources": used,
            "provenance": {"weighted_aggregate": True, "formula":
                           "Σ(outstanding×days_to_maturity)/Σ(outstanding)",
                           "bulk_raw_response_id": rid, "contributing": contributing}}}
        gate_verdict = {"outcome": "pass", "pagination_complete": True, "sources": used}
        return _envelope(STATE_DELIVERED, answer=answer, analysis=analysis, rows=[],
                         aggregates=aggregates, provenance={"bulk_raw_response_id": rid},
                         gate_verdict=gate_verdict, complete=True, refusals=[], skipped=skipped,
                         meta={"wam_days": wam_days, "as_of": as_of.isoformat(),
                               "sources": used, "total_loans": len(rows)})

    def _weighted_average(self, figure: str, analysis: str, label: str) -> dict:
        """Σ(outstanding_i × figure_i) / Σ(outstanding_i), weighted by outstanding."""
        rows, rid, res = self._load_portfolio(analysis)
        if rows is None:
            return res
        num = 0.0
        den = 0.0
        contributing = []
        used = 0
        skipped = []
        for i, row in enumerate(rows):
            out_v, out_path = _row_value(row, "outstanding")
            fig_v, fig_path = _row_value(row, figure)
            lid = str(row.get("id"))
            name = row.get("name")
            if (out_v is _ABSENT or not _is_number(out_v)
                    or fig_v is _ABSENT or not _is_number(fig_v)):
                skipped.append({"loan_id": lid, "name": name,
                                "reason": f"missing outstanding or {figure} — excluded from {label}"})
                continue
            p_out = self._bind(out_v, rid, i, out_path, f"loan.{lid}.outstanding")
            p_fig = self._bind(fig_v, rid, i, fig_path, f"loan.{lid}.{figure}")
            if p_out is None or p_fig is None:
                skipped.append({"loan_id": lid, "name": name,
                                "reason": f"{label} input could not be provenance-bound"})
                continue
            num += float(out_v) * float(fig_v)
            den += float(out_v)
            contributing.append({"raw_response_id": rid,
                                 "json_field_path": p_fig["json_field_path"]})
            used += 1
        if den == 0:
            return _refused(analysis, REASON_FETCH_EMPTY,
                            f"no loan carried both outstanding and {figure} — cannot weight",
                            provenance={"bulk_raw_response_id": rid}, skipped=skipped)
        wavg = round(num / den, 6)
        answer = (f"{label} across {used} of {len(rows)} loans is {wavg} "
                  f"(weighted by outstanding; {len(skipped)} loans surfaced as excluded).")
        aggregates = {analysis: {
            "value": wavg, "weighted_by": "outstanding", "weight_total": round(den, 4),
            "sources": used,
            "provenance": {"weighted_aggregate": True,
                           "formula": f"Σ(outstanding×{figure})/Σ(outstanding)",
                           "bulk_raw_response_id": rid, "contributing": contributing}}}
        gate_verdict = {"outcome": "pass", "pagination_complete": True, "sources": used}
        return _envelope(STATE_DELIVERED, answer=answer, analysis=analysis, rows=[],
                         aggregates=aggregates, provenance={"bulk_raw_response_id": rid},
                         gate_verdict=gate_verdict, complete=True, refusals=[], skipped=skipped,
                         meta={"value": wavg, "sources": used, "total_loans": len(rows)})

    def count_by_status(self) -> dict:
        """Count loans by status. Each status bucket carries the contributing loan ids + a
        per-loan provenance path to its status field. The bucket counts reconcile to the total."""
        analysis = "count_by_status"
        rows, rid, res = self._load_portfolio(analysis)
        if rows is None:
            return res
        buckets: dict = {}
        skipped = []
        for i, row in enumerate(rows):
            status = row.get("status")
            lid = str(row.get("id"))
            name = row.get("name")
            if status is None:
                skipped.append({"loan_id": lid, "name": name, "reason": "no status on this loan"})
                continue
            prov = self._bind(status, rid, i, "status", f"loan.{lid}.status")
            if prov is None:
                skipped.append({"loan_id": lid, "name": name,
                                "reason": "status could not be provenance-bound"})
                continue
            b = buckets.setdefault(str(status), {"count": 0, "loan_ids": [], "contributing": []})
            b["count"] += 1
            b["loan_ids"].append(lid)
            b["contributing"].append(prov)
        counted = sum(b["count"] for b in buckets.values())
        # reconcile: counted + skipped == total rows
        reconciles = (counted + len(skipped)) == len(rows)
        out_rows = sorted(
            ({"status": s, "count": b["count"], "loan_ids": b["loan_ids"],
              "provenance": {"bulk_raw_response_id": rid, "contributing": b["contributing"]}}
             for s, b in buckets.items()),
            key=lambda r: (-r["count"], r["status"]))
        answer = (f"{len(rows)} loans across {len(buckets)} status(es): "
                  + ", ".join(f"{r['status']}={r['count']}" for r in out_rows)
                  + (f"; {len(skipped)} surfaced as missing status." if skipped else "."))
        gate_verdict = {"outcome": "pass", "pagination_complete": True,
                        "reconciliation_ok": reconciles, "counted": counted}
        return _envelope(STATE_DELIVERED, answer=answer, analysis=analysis, rows=out_rows,
                         aggregates={"by_status": {s: b["count"] for s, b in buckets.items()},
                                     "counted": counted, "reconciles": reconciles},
                         provenance={"bulk_raw_response_id": rid}, gate_verdict=gate_verdict,
                         complete=True, refusals=[], skipped=skipped,
                         meta={"total_loans": len(rows), "statuses": len(buckets)})

    # =====================================================================
    # FILTERING
    # =====================================================================
    def filter_overdue(self) -> dict:
        """Loans with overdue.total > 0. Each carries its overdue value + provenance."""
        return self._filter_numeric("overdue", lambda v: v > 0.0, "overdue loans",
                                    "overdue_loans")

    def filter_over_outstanding(self, threshold: float) -> dict:
        """Loans with outstanding > threshold. Each carries its outstanding value + provenance."""
        return self._filter_numeric(
            "outstanding", lambda v: v > float(threshold),
            f"loans over {threshold} outstanding", f"over_{threshold}_outstanding",
            extra_meta={"threshold": float(threshold)})

    def filter_active(self) -> dict:
        """Loans whose status is 'active' (case-insensitive). Status path is provenance-bound."""
        analysis = "active_loans"
        rows, rid, res = self._load_portfolio(analysis)
        if rows is None:
            return res
        out_rows, skipped = [], []
        for i, row in enumerate(rows):
            status = row.get("status")
            lid = str(row.get("id"))
            name = row.get("name")
            if status is None:
                skipped.append({"loan_id": lid, "name": name, "reason": "no status on this loan"})
                continue
            if str(status).strip().lower() != "active":
                continue
            prov = self._bind(status, rid, i, "status", f"loan.{lid}.status")
            if prov is None:
                skipped.append({"loan_id": lid, "name": name,
                                "reason": "status could not be provenance-bound"})
                continue
            out_rows.append({"loan_id": lid, "name": name, "status": status,
                             "provenance": prov})
        answer = (f"{len(out_rows)} active loans of {len(rows)} "
                  f"({len(skipped)} surfaced as missing status).")
        gate_verdict = {"outcome": "pass", "pagination_complete": True, "matched": len(out_rows)}
        return _envelope(STATE_DELIVERED, answer=answer, analysis=analysis, rows=out_rows,
                         aggregates={"matched": len(out_rows)},
                         provenance={"bulk_raw_response_id": rid}, gate_verdict=gate_verdict,
                         complete=True, refusals=[], skipped=skipped,
                         meta={"total_loans": len(rows), "matched": len(out_rows)})

    def filter_maturing_within(self, days: int, *,
                               as_of: Optional[datetime.date] = None) -> dict:
        """Loans maturing within N days of `as_of`. Each carries days_to_maturity + provenance.
        Already-matured loans (days_to_maturity < 0) are excluded from this window by definition
        but surfaced separately in meta.overdue_maturity_count."""
        analysis = f"maturing_within_{days}_days"
        rows, rid, res = self._load_portfolio(analysis)
        if rows is None:
            return res
        as_of = as_of or _today()
        out_rows, skipped = [], []
        past_due = 0
        for i, row in enumerate(rows):
            mat_v, mat_path = _row_value(row, "maturity_date")
            lid = str(row.get("id"))
            name = row.get("name")
            d = _parse_date(mat_v) if mat_v is not _ABSENT else None
            if d is None:
                skipped.append({"loan_id": lid, "name": name,
                                "reason": "no parseable maturity date on this loan"})
                continue
            dtm = (d - as_of).days
            if dtm < 0:
                past_due += 1
                continue
            if dtm > int(days):
                continue
            prov = self._bind(mat_v, rid, i, mat_path, f"loan.{lid}.maturity_date")
            if prov is None:
                skipped.append({"loan_id": lid, "name": name,
                                "reason": "maturity date could not be provenance-bound"})
                continue
            out_rows.append({"loan_id": lid, "name": name, "maturity_date": mat_v,
                             "days_to_maturity": dtm, "provenance": prov})
        out_rows.sort(key=lambda r: (r["days_to_maturity"], str(r["name"])))
        answer = (f"{len(out_rows)} loans maturing within {days} days of {as_of.isoformat()} "
                  f"({len(skipped)} surfaced as missing a date; {past_due} already past maturity).")
        gate_verdict = {"outcome": "pass", "pagination_complete": True, "matched": len(out_rows)}
        return _envelope(STATE_DELIVERED, answer=answer, analysis=analysis, rows=out_rows,
                         aggregates={"matched": len(out_rows)},
                         provenance={"bulk_raw_response_id": rid}, gate_verdict=gate_verdict,
                         complete=True, refusals=[], skipped=skipped,
                         meta={"days": int(days), "as_of": as_of.isoformat(),
                               "total_loans": len(rows), "matched": len(out_rows),
                               "overdue_maturity_count": past_due})

    def _filter_numeric(self, figure: str, predicate: Callable[[float], bool],
                        label: str, analysis: str, *,
                        extra_meta: Optional[dict] = None) -> dict:
        rows, rid, res = self._load_portfolio(analysis)
        if rows is None:
            return res
        present, skipped = self._collect_figure(rows, rid, figure)
        matched = [p for p in present if predicate(p["value"])]
        matched.sort(key=lambda r: (r["value"], str(r["name"])), reverse=True)
        out_rows = [{"loan_id": p["loan_id"], "name": p["name"], "value": p["value"],
                     "currency": p["currency"], "figure": figure,
                     "provenance": p["provenance"]}
                    for p in matched]
        answer = (f"{len(out_rows)} {label} of {len(rows)} loans "
                  f"({len(skipped)} surfaced as missing {figure}).")
        gate_verdict = {"outcome": "pass", "pagination_complete": True, "matched": len(out_rows)}
        meta = {"figure": figure, "total_loans": len(rows), "matched": len(out_rows),
                "assessed": len(present)}
        if extra_meta:
            meta.update(extra_meta)
        return _envelope(STATE_DELIVERED, answer=answer, analysis=analysis, rows=out_rows,
                         aggregates={"matched": len(out_rows)},
                         provenance={"bulk_raw_response_id": rid}, gate_verdict=gate_verdict,
                         complete=True, refusals=[], skipped=skipped, meta=meta)

    # =====================================================================
    # CONCENTRATION
    # =====================================================================
    def concentration_by_status(self) -> dict:
        """Exposure (sum of outstanding) by status, with each bucket's % of the total book.
        Bucket sums reconcile to the assessed book total. Loans missing outstanding surfaced."""
        analysis = "concentration_by_status"
        rows, rid, res = self._load_portfolio(analysis)
        if rows is None:
            return res
        present, skipped = self._collect_figure(rows, rid, "outstanding")
        if not present:
            return _refused(analysis, REASON_FETCH_EMPTY,
                            "no loan carried outstanding — cannot compute exposure concentration",
                            provenance={"bulk_raw_response_id": rid}, skipped=skipped)
        currencies = {p["currency"] for p in present if p["currency"]}
        if len(currencies) > 1:
            return _refused(analysis, REASON_RECONCILE,
                            (f"exposure spans mixed currencies {sorted(currencies)} — refusing"),
                            provenance={"bulk_raw_response_id": rid}, skipped=skipped)
        book = round(sum(p["value"] for p in present), 4)
        buckets: dict = {}
        for p in present:
            status = str(p["row"].get("status"))
            b = buckets.setdefault(status, {"exposure": 0.0, "count": 0, "contributing": []})
            b["exposure"] = round(b["exposure"] + p["value"], 4)
            b["count"] += 1
            b["contributing"].append({"raw_response_id": rid,
                                      "json_field_path": p["provenance"]["json_field_path"]})
        out_rows = sorted(
            ({"status": s, "exposure": b["exposure"], "count": b["count"],
              "pct_of_book": round(b["exposure"] / book, 6) if book else None,
              "provenance": {"aggregate": True, "bulk_raw_response_id": rid,
                             "contributing": b["contributing"]}}
             for s, b in buckets.items()),
            key=lambda r: (-r["exposure"], r["status"]))
        bucket_sum = round(sum(r["exposure"] for r in out_rows), 4)
        reconciles = abs(bucket_sum - book) <= RECONCILE_TOLERANCE
        currency = (sorted(currencies) or [None])[0]
        cur_str = f" {currency}" if currency else ""
        answer = (f"Exposure by status across {len(present)} of {len(rows)} loans "
                  f"(book {book}{cur_str}): "
                  + ", ".join(f"{r['status']}={r['exposure']} "
                              f"({round((r['pct_of_book'] or 0) * 100, 1)}%)" for r in out_rows)
                  + (f"; {len(skipped)} surfaced as missing outstanding." if skipped else "."))
        gate_verdict = {"outcome": "pass", "pagination_complete": True,
                        "reconciliation_ok": reconciles}
        return _envelope(STATE_DELIVERED, answer=answer, analysis=analysis, rows=out_rows,
                         aggregates={"book_total": book, "currency": currency,
                                     "reconciles": reconciles},
                         provenance={"bulk_raw_response_id": rid}, gate_verdict=gate_verdict,
                         complete=True, refusals=[], skipped=skipped,
                         meta={"book_total": book, "currency": currency, "buckets": len(buckets),
                               "assessed": len(present), "total_loans": len(rows)})

    def top_n_concentration(self, n: int = 5) -> dict:
        """Top-N concentration: the % of the book held by the largest-N loans by outstanding.
        Carries the top-N rows (each with provenance) + the book total."""
        analysis = f"top_{n}_concentration"
        rows, rid, res = self._load_portfolio(analysis)
        if rows is None:
            return res
        present, skipped = self._collect_figure(rows, rid, "outstanding")
        if not present:
            return _refused(analysis, REASON_FETCH_EMPTY,
                            "no loan carried outstanding — cannot compute top-N concentration",
                            provenance={"bulk_raw_response_id": rid}, skipped=skipped)
        currencies = {p["currency"] for p in present if p["currency"]}
        if len(currencies) > 1:
            return _refused(analysis, REASON_RECONCILE,
                            (f"exposure spans mixed currencies {sorted(currencies)} — refusing"),
                            provenance={"bulk_raw_response_id": rid}, skipped=skipped)
        book = round(sum(p["value"] for p in present), 4)
        present.sort(key=lambda p: (p["value"], str(p["name"])), reverse=True)
        top = present[:int(n)]
        top_sum = round(sum(p["value"] for p in top), 4)
        pct = round(top_sum / book, 6) if book else None
        currency = (sorted(currencies) or [None])[0]
        out_rows = [{"rank": idx + 1, "loan_id": p["loan_id"], "name": p["name"],
                     "value": p["value"], "currency": p["currency"],
                     "provenance": p["provenance"]} for idx, p in enumerate(top)]
        cur_str = f" {currency}" if currency else ""
        answer = (f"The top {len(top)} loans by outstanding hold {top_sum}{cur_str} of a "
                  f"{book}{cur_str} book — {round((pct or 0) * 100, 1)}% concentration "
                  f"({len(present)} of {len(rows)} loans assessed; {len(skipped)} surfaced).")
        aggregates = {"top_n_exposure": top_sum, "book_total": book,
                      "concentration_pct": pct, "currency": currency, "n": int(n),
                      "provenance": {"aggregate": True, "bulk_raw_response_id": rid,
                                     "contributing": [{"raw_response_id": rid,
                                                       "json_field_path":
                                                       p["provenance"]["json_field_path"]}
                                                      for p in top]}}
        gate_verdict = {"outcome": "pass", "pagination_complete": True}
        return _envelope(STATE_DELIVERED, answer=answer, analysis=analysis, rows=out_rows,
                         aggregates=aggregates, provenance={"bulk_raw_response_id": rid},
                         gate_verdict=gate_verdict, complete=True, refusals=[], skipped=skipped,
                         meta={"n": int(n), "concentration_pct": pct, "book_total": book,
                               "currency": currency, "assessed": len(present),
                               "total_loans": len(rows)})

    def concentration_by_client(self) -> dict:
        """Exposure by client when a client linkage exists on the loan rows.

        The bulk selection does not request client linkage by default; if no loan row carries a
        client identifier this REFUSES with a clear reason (client linkage not available) rather
        than fabricating a grouping. When a linkage IS present (clientId/client.id/clientName),
        it groups exposure by it exactly like concentration_by_status."""
        analysis = "concentration_by_client"
        rows, rid, res = self._load_portfolio(analysis)
        if rows is None:
            return res

        def _client_key(row):
            for k in ("clientId", "client_id"):
                if row.get(k) is not None:
                    return str(row.get(k)), k
            c = row.get("client")
            if isinstance(c, dict) and c.get("id") is not None:
                return str(c.get("id")), "client.id"
            for k in ("clientName", "client_name"):
                if row.get(k):
                    return str(row.get(k)), k
            return None, None

        if not any(_client_key(r)[0] is not None for r in rows):
            return _refused(analysis, REASON_UNKNOWN_ANALYSIS,
                            ("client linkage is not available on the loan rows (the bulk "
                             "selection carries no clientId/client/clientName) — refusing rather "
                             "than fabricating a client grouping"),
                            provenance={"bulk_raw_response_id": rid})
        present, skipped = self._collect_figure(rows, rid, "outstanding")
        currencies = {p["currency"] for p in present if p["currency"]}
        if len(currencies) > 1:
            return _refused(analysis, REASON_RECONCILE,
                            (f"exposure spans mixed currencies {sorted(currencies)} — refusing"),
                            provenance={"bulk_raw_response_id": rid}, skipped=skipped)
        book = round(sum(p["value"] for p in present), 4)
        buckets: dict = {}
        for p in present:
            key, _src = _client_key(p["row"])
            key = key or "<unlinked>"
            b = buckets.setdefault(key, {"exposure": 0.0, "count": 0, "contributing": []})
            b["exposure"] = round(b["exposure"] + p["value"], 4)
            b["count"] += 1
            b["contributing"].append({"raw_response_id": rid,
                                      "json_field_path": p["provenance"]["json_field_path"]})
        out_rows = sorted(
            ({"client": c, "exposure": b["exposure"], "count": b["count"],
              "pct_of_book": round(b["exposure"] / book, 6) if book else None,
              "provenance": {"aggregate": True, "bulk_raw_response_id": rid,
                             "contributing": b["contributing"]}}
             for c, b in buckets.items()),
            key=lambda r: (-r["exposure"], str(r["client"])))
        currency = (sorted(currencies) or [None])[0]
        answer = (f"Exposure by client across {len(present)} of {len(rows)} loans "
                  f"({len(buckets)} clients; book {book}).")
        gate_verdict = {"outcome": "pass", "pagination_complete": True}
        return _envelope(STATE_DELIVERED, answer=answer, analysis=analysis, rows=out_rows,
                         aggregates={"book_total": book, "currency": currency,
                                     "clients": len(buckets)},
                         provenance={"bulk_raw_response_id": rid}, gate_verdict=gate_verdict,
                         complete=True, refusals=[], skipped=skipped,
                         meta={"book_total": book, "clients": len(buckets),
                               "assessed": len(present), "total_loans": len(rows)})

    # =====================================================================
    # COVENANT-BREACH SCAN (KG-joined)
    # =====================================================================
    def _kg_lookup(self, loan_name: Optional[str]) -> Optional[dict]:
        if not loan_name:
            return None
        if self._kg_store is not None:
            return self._kg_store.lookup(loan_name)
        return self._kglib.kg_lookup(loan_name)

    def covenant_breach_scan(self) -> dict:
        """Scan the portfolio for covenant breaches against the PRISM thresholds.

        For each loan, JOIN its name to the OKOA KG (hca-kg). When the KG supplies the collateral
        inputs, compute:
          - LTV       = outstanding / appraised_value   (breach if > 0.75)
          - debt_yield= NOI / commitment                 (breach if < 0.08, when NOI present)
          - DSCR      = NOI / (commitment × rate)        (breach if < 1.25, when NOI + rate present)
        Each computed ratio carries DUAL provenance (the Hypercore bulk-row json_field_path AND
        the KG node_id/field). Loans NOT in the KG (or missing appraised_value) are listed as
        `unassessable` with the reason — NEVER silently dropped. A breach row names which covenant
        and the threshold it crossed."""
        analysis = "covenant_breach_scan"
        rows, rid, res = self._load_portfolio(analysis)
        if rows is None:
            return res
        assessed = []
        breaches = []
        unassessable = []
        for i, row in enumerate(rows):
            lid = str(row.get("id"))
            name = row.get("name")
            kg = self._kg_lookup(name)
            if kg is None:
                unassessable.append({"loan_id": lid, "name": name,
                                     "reason": "not assessable (no collateral data — no confident "
                                               "OKOA knowledge-graph match)"})
                continue
            appraised = kg.get("appraised_value")
            noi = kg.get("noi")
            kg_prov = kg.get("provenance") or {}
            kg_node = kg.get("node_id")
            # LTV needs outstanding (Hypercore) + appraised_value (KG).
            out_v, out_path = _row_value(row, "outstanding")
            commit_v, commit_path = _row_value(row, "commitment")
            rate_v, rate_path = _row_value(row, "annual_interest_rate")
            if appraised is None or not _is_number(appraised) or float(appraised) == 0.0:
                unassessable.append({"loan_id": lid, "name": name, "kg_node_id": kg_node,
                                     "reason": "not assessable (no appraised_value in the KG for "
                                               "this loan)"})
                continue
            if out_v is _ABSENT or not _is_number(out_v):
                unassessable.append({"loan_id": lid, "name": name, "kg_node_id": kg_node,
                                     "reason": "not assessable (no outstanding on the Hypercore "
                                               "loan)"})
                continue
            p_out = self._bind(out_v, rid, i, out_path, f"loan.{lid}.outstanding")
            if p_out is None:
                unassessable.append({"loan_id": lid, "name": name, "kg_node_id": kg_node,
                                     "reason": "not assessable (outstanding could not be "
                                               "provenance-bound)"})
                continue
            ltv = round(float(out_v) / float(appraised), 6)
            loan_breaches = []
            if ltv > PRISM_MAX_LTV:
                loan_breaches.append({"covenant": "ltv", "value": ltv, "threshold": PRISM_MAX_LTV,
                                      "direction": "max", "basis": "PRISM max_ltv (OKOA 75%)"})
            record = {
                "loan_id": lid, "name": name, "kg_node_id": kg_node,
                "kg_confidence": kg.get("confidence"),
                "ltv": ltv,
                "provenance": {
                    "ltv": {"derived": True, "formula": "outstanding / appraised_value",
                            "outstanding": {"source": "hypercore", **p_out},
                            "appraised_value": {"source": "kg", **(kg_prov.get("appraised_value")
                                                or {"node_id": kg_node, "field": "appraised_value",
                                                    "file": kg.get("kg_file")})}}}}
            # debt yield + DSCR only when NOI present.
            if noi is not None and _is_number(noi):
                if commit_v is not _ABSENT and _is_number(commit_v) and float(commit_v) != 0.0:
                    p_commit = self._bind(commit_v, rid, i, commit_path, f"loan.{lid}.commitment")
                    dy = round(float(noi) / float(commit_v), 6)
                    record["debt_yield"] = dy
                    record["provenance"]["debt_yield"] = {
                        "derived": True, "formula": "NOI / commitment",
                        "noi": {"source": "kg", **(kg_prov.get("noi")
                                or {"node_id": kg_node, "field": "noi", "file": kg.get("kg_file")})},
                        "commitment": {"source": "hypercore", **(p_commit or {})}}
                    if dy < PRISM_MIN_DEBT_YIELD:
                        loan_breaches.append({"covenant": "debt_yield", "value": dy,
                                              "threshold": PRISM_MIN_DEBT_YIELD, "direction": "min",
                                              "basis": "PRISM min_debt_yield (8%)"})
                    # DSCR = NOI / (commitment × rate) when a rate is available.
                    rate = kg.get("interest_rate")
                    rate_src = "kg"
                    if rate is None and rate_v is not _ABSENT and _is_number(rate_v):
                        rate = float(rate_v)
                        rate_src = "hypercore"
                    if rate is not None and _is_number(rate) and float(rate) > 0:
                        debt_service = float(commit_v) * float(rate)
                        if debt_service > 0:
                            dscr = round(float(noi) / debt_service, 6)
                            record["dscr"] = dscr
                            record["provenance"]["dscr"] = {
                                "derived": True,
                                "formula": "NOI / (commitment × interest_rate)",
                                "noi": {"source": "kg"},
                                "commitment": {"source": "hypercore", **(p_commit or {})},
                                "interest_rate": {"source": rate_src, "value": float(rate)}}
                            if dscr < PRISM_MIN_DSCR:
                                loan_breaches.append({"covenant": "dscr", "value": dscr,
                                                      "threshold": PRISM_MIN_DSCR,
                                                      "direction": "min",
                                                      "basis": "PRISM min_dscr (1.25x)"})
            record["breaches"] = loan_breaches
            assessed.append(record)
            if loan_breaches:
                breaches.append(record)
        answer = (f"Covenant scan over {len(rows)} loans: {len(assessed)} assessable (KG-covered), "
                  f"{len(breaches)} with at least one breach, "
                  f"{len(unassessable)} not assessable (no collateral data — surfaced, not dropped).")
        gate_verdict = {"outcome": "pass", "pagination_complete": True,
                        "assessed": len(assessed), "breaches": len(breaches),
                        "unassessable": len(unassessable)}
        return _envelope(STATE_DELIVERED, answer=answer, analysis=analysis, rows=breaches,
                         aggregates={"assessed": len(assessed), "breached": len(breaches),
                                     "unassessable": len(unassessable),
                                     "thresholds": {"ltv_max": PRISM_MAX_LTV,
                                                    "debt_yield_min": PRISM_MIN_DEBT_YIELD,
                                                    "dscr_min": PRISM_MIN_DSCR}},
                         provenance={"bulk_raw_response_id": rid}, gate_verdict=gate_verdict,
                         complete=True, refusals=[], skipped=unassessable,
                         meta={"total_loans": len(rows), "assessed": len(assessed),
                               "breaches": len(breaches), "unassessable": len(unassessable),
                               "assessed_rows": assessed})

    # =====================================================================
    # INTERPRETIVE JUDGMENT: at-risk loans (stated criteria + consensus)
    # =====================================================================
    def most_at_risk(self, *, agent_runner: Optional[Callable[[str, int], list]] = None,
                     near_maturity_days: int = DEFAULT_NEAR_MATURITY_DAYS,
                     as_of: Optional[datetime.date] = None,
                     quorum: Any = None, n: Optional[int] = None,
                     max_redispatch: Optional[int] = None) -> dict:
        """Identify the MOST AT-RISK loans using STATED, surfaced criteria, and (when an
        agent_runner is supplied) route the CONCLUSION through blind-agent consensus.

        STATED CRITERIA (a loan is at-risk if ANY holds):
          1. overdue.total > 0                                   (it has arrears)
          2. within `near_maturity_days` of maturity (or past)  (refinance / payoff pressure)
          3. LTV > PRISM max (0.75), where the KG supplies appraised_value

        The deterministic at-risk SET + the supporting figures are ALWAYS returned (rows +
        criteria). When `agent_runner` is given, the JUDGMENT "the at-risk set is {ids}" is put to
        N blind agents via hca-consensus.run_consensus; below quorum it ESCALATES (no silent
        pick) — the deterministic evidence still returns. With no agent_runner the deterministic
        criteria stand alone (the judgment is fully transparent and reproducible)."""
        analysis = "most_at_risk"
        rows, rid, res = self._load_portfolio(analysis)
        if rows is None:
            return res
        as_of = as_of or _today()
        criteria = {
            "overdue": "overdue.total > 0",
            "near_maturity": f"days_to_maturity <= {near_maturity_days} (or past maturity)",
            "high_ltv": f"LTV > {PRISM_MAX_LTV} (KG appraised_value required)",
        }
        at_risk = []
        unassessable_ltv = []
        for i, row in enumerate(rows):
            lid = str(row.get("id"))
            name = row.get("name")
            reasons = []
            evidence = {}
            # criterion 1: overdue
            ov_v, ov_path = _row_value(row, "overdue")
            if _is_number(ov_v) and float(ov_v) > 0.0:
                prov = self._bind(ov_v, rid, i, ov_path, f"loan.{lid}.overdue")
                if prov is not None:
                    reasons.append("overdue")
                    evidence["overdue"] = {"value": float(ov_v), "provenance": prov}
            # criterion 2: near / past maturity
            mat_v, mat_path = _row_value(row, "maturity_date")
            d = _parse_date(mat_v) if mat_v is not _ABSENT else None
            if d is not None:
                dtm = (d - as_of).days
                if dtm <= int(near_maturity_days):
                    prov = self._bind(mat_v, rid, i, mat_path, f"loan.{lid}.maturity_date")
                    if prov is not None:
                        reasons.append("near_maturity")
                        evidence["maturity"] = {"maturity_date": mat_v, "days_to_maturity": dtm,
                                                "provenance": prov}
            # criterion 3: high LTV (KG-joined)
            kg = self._kg_lookup(name)
            if kg is not None and _is_number(kg.get("appraised_value")) \
                    and float(kg.get("appraised_value")) != 0.0:
                out_v, out_path = _row_value(row, "outstanding")
                if _is_number(out_v):
                    p_out = self._bind(out_v, rid, i, out_path, f"loan.{lid}.outstanding")
                    if p_out is not None:
                        ltv = round(float(out_v) / float(kg["appraised_value"]), 6)
                        if ltv > PRISM_MAX_LTV:
                            reasons.append("high_ltv")
                        evidence["ltv"] = {"value": ltv, "threshold": PRISM_MAX_LTV,
                                           "provenance": {"outstanding": {"source": "hypercore",
                                                                          **p_out},
                                                          "appraised_value": {"source": "kg",
                                                                              "node_id":
                                                                              kg.get("node_id")}}}
            else:
                unassessable_ltv.append({"loan_id": lid, "name": name,
                                         "reason": "LTV criterion not assessable (no KG "
                                                   "appraised_value)"})
            if reasons:
                at_risk.append({"loan_id": lid, "name": name, "reasons": reasons,
                                "evidence": evidence})
        at_risk.sort(key=lambda r: (-len(r["reasons"]), str(r["name"])))
        at_risk_ids = sorted(r["loan_id"] for r in at_risk)

        # Deterministic evidence is always present. Now optionally adjudicate the JUDGMENT.
        #
        # The judgment's value is a SET of loan ids — a derived conclusion, NOT a single raw
        # Tier-1 field. So we run consensus for its core guarantee — AGREEMENT on the substance
        # (the set) with NO silent pick and bounded blind re-dispatch — and judge the outcome by
        # whether quorum was reached. We do NOT route the SET through the numeric Tier-1 binder
        # (there is no single field to bind a set to); the conclusion's PROVENANCE is instead the
        # per-loan, already-bound supporting evidence attached to each at-risk row. Below quorum
        # the engine ESCALATES (state != DELIVERED) and we surface that, never picking a plurality.
        consensus_meta = None
        state = STATE_DELIVERED
        if agent_runner is not None:
            cons = _consensus()
            judgment_q = (
                "Using ONLY these stated at-risk criteria — a loan is at-risk if it is overdue "
                f"(overdue.total>0) OR within {near_maturity_days} days of maturity (or past) OR "
                f"its LTV exceeds {PRISM_MAX_LTV} — identify the set of at-risk loan ids in this "
                "portfolio. Return the SET of loan ids.")
            # Each blind agent returns its at-risk id set; consensus agrees on the SET (order-free).

            def _runner(question, count):
                return agent_runner(judgment_q, count)

            # gate_source=None -> no deterministic gate suite for a derived-set judgment; the
            # engine still does substance grouping + bounded blind re-dispatch + ESCALATE.
            result = cons.run_consensus(
                judgment_q, _runner, quorum=quorum, n=n, max_redispatch=max_redispatch,
                binder=self._engine, value_ref="portfolio.most_at_risk")
            reached = (result.get("state") == cons.STATE_DELIVERED) or (
                (result.get("agreeing_count") or 0) >= (result.get("quorum") or 1)
                and result.get("agreeing_count") is not None)
            consensus_meta = {
                "engine_state": result.get("state"),
                "quorum_reached": bool(reached),
                "agreeing_count": result.get("agreeing_count"),
                "quorum": result.get("quorum"), "n": result.get("n"),
                "redispatches": result.get("redispatches"),
                "agreed_value": result.get("value") if reached else None,
                "disagreement": result.get("disagreement"),
                "note": ("substance agreement reached; the judgment's provenance is the per-loan "
                         "bound evidence (a derived set has no single Tier-1 field to bind)"),
            }
            # When quorum IS reached, surface the agents' agreed set (or fall back to the
            # deterministic set when the engine did not echo it through its numeric binder).
            if reached and result.get("value") is not None:
                consensus_meta["agreed_value"] = result.get("value")
            if not reached:
                state = STATE_ESCALATED
        answer = (f"{len(at_risk)} of {len(rows)} loans are at-risk by the stated criteria "
                  f"(criteria shown; supporting figures attached). "
                  f"{len(unassessable_ltv)} loans' LTV criterion was not assessable (no KG data, "
                  "surfaced not dropped)."
                  + (" Judgment routed through blind-agent consensus."
                     if agent_runner is not None else
                     " Judgment is fully deterministic (no opaque opinion)."))
        gate_verdict = {"outcome": "pass" if state == STATE_DELIVERED else "escalated",
                        "pagination_complete": True, "criteria_stated": True,
                        "at_risk_count": len(at_risk)}
        return _envelope(state, answer=answer, analysis=analysis, rows=at_risk,
                         aggregates={"at_risk_count": len(at_risk), "at_risk_ids": at_risk_ids,
                                     "criteria": criteria},
                         provenance={"bulk_raw_response_id": rid}, gate_verdict=gate_verdict,
                         complete=(state == STATE_DELIVERED),
                         refusals=([] if state == STATE_DELIVERED else
                                   [{"reason_code": REASON_NO_CONSENSUS,
                                     "reason": "blind agents did not reach quorum on the at-risk "
                                               "set — escalating (deterministic evidence retained)"}]),
                         skipped=unassessable_ltv,
                         meta={"criteria": criteria, "as_of": as_of.isoformat(),
                               "near_maturity_days": int(near_maturity_days),
                               "total_loans": len(rows), "at_risk_count": len(at_risk),
                               "consensus": consensus_meta})


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

def build_analyzer(*, client=None, cache=None, engine=None, kg_store=None,
                   page_limit: int = _BULK_PAGE_LIMIT) -> PortfolioAnalyzer:
    """Build a PortfolioAnalyzer wired to a (lazily-live) bulk fetcher + shared cache/engine."""
    cachelib = _cache()
    shared_cache = cache or cachelib.TwoTierCache()
    fetcher = PortfolioFetcher(client=client, cache=shared_cache, page_limit=page_limit)
    return PortfolioAnalyzer(fetcher=fetcher, cache=shared_cache, engine=engine,
                             kg_store=kg_store)


# ---------------------------------------------------------------------------
# CLI — analysis selectors. Totals / rankings / loan NAMES are portfolio reference
# data (not borrower PII), safe to print. No borrower-level PII is emitted.
# ---------------------------------------------------------------------------

def _summarize(env: dict, *, limit: int = 10) -> dict:
    """PII-safe console summary: state/answer/analysis + capped rows + aggregates + provenance
    pointers + the skipped/unassessable count (surfaced, never silently dropped)."""
    rows = env.get("rows") or []
    return {
        "state": env.get("state"),
        "analysis": env.get("analysis"),
        "answer": env.get("answer"),
        "row_count": len(rows),
        "rows": rows[:limit],
        "aggregates": env.get("aggregates"),
        "skipped_count": len(env.get("skipped") or []),
        "skipped_sample": (env.get("skipped") or [])[:5],
        "provenance": env.get("provenance"),
        "gate_verdict": env.get("gate_verdict"),
        "complete": env.get("complete"),
        "refusals": env.get("refusals"),
        "meta": {k: (env.get("meta") or {}).get(k)
                 for k in ("figure", "total", "currency", "total_loans", "assessed",
                           "at_risk_count", "breaches", "unassessable", "concentration_pct",
                           "wam_days", "book_total")},
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="acos-hypercore-ask portfolio analysis (rankings / roll-ups / filters / "
                    "concentration / covenant scan) on the ONE bulk Tier-1 fetch.")
    parser.add_argument("--top", dest="top", metavar="FIGURE",
                        help="top-N loans by FIGURE (outstanding/overdue/commitment/amount_due/"
                             "total_disbursed/...)")
    parser.add_argument("--total", dest="total", metavar="FIGURE",
                        help="portfolio total of FIGURE (reconciled)")
    parser.add_argument("--overdue", action="store_true", help="list overdue loans")
    parser.add_argument("--maturing-within", dest="maturing", type=int, default=None,
                        help="loans maturing within N days")
    parser.add_argument("--closest-maturity", action="store_true",
                        help="loans closest to maturity")
    parser.add_argument("--utilization", action="store_true", help="highest-utilization loans")
    parser.add_argument("--concentration", action="store_true",
                        help="exposure concentration by status")
    parser.add_argument("--top-n-concentration", dest="topn_conc", type=int, default=None,
                        help="%% of book in the top-N loans")
    parser.add_argument("--count-by-status", action="store_true", help="count loans by status")
    parser.add_argument("--wam", action="store_true", help="weighted-average maturity (days)")
    parser.add_argument("--wa-rate", action="store_true", help="weighted-average interest rate")
    parser.add_argument("--covenant-scan", action="store_true",
                        help="covenant-breach scan (KG-joined)")
    parser.add_argument("--at-risk", action="store_true",
                        help="most at-risk loans (stated criteria; deterministic)")
    parser.add_argument("--n", dest="n", type=int, default=10, help="top-N size (default 10)")
    parser.add_argument("--threshold", dest="threshold", type=float, default=None,
                        help="numeric threshold for --over-outstanding")
    parser.add_argument("--over-outstanding", action="store_true",
                        help="loans over --threshold outstanding")
    parser.add_argument("--full", action="store_true", help="print the full envelope JSON")
    args = parser.parse_args(argv)

    analyzer = build_analyzer()
    env = None
    if args.top:
        env = analyzer.rank(args.top, top_n=args.n)
    elif args.total:
        env = analyzer.total(args.total)
    elif args.overdue:
        env = analyzer.filter_overdue()
    elif args.maturing is not None:
        env = analyzer.filter_maturing_within(args.maturing)
    elif args.closest_maturity:
        env = analyzer.rank_by_maturity(top_n=args.n)
    elif args.utilization:
        env = analyzer.rank_by_utilization(top_n=args.n)
    elif args.concentration:
        env = analyzer.concentration_by_status()
    elif args.topn_conc is not None:
        env = analyzer.top_n_concentration(args.topn_conc)
    elif args.count_by_status:
        env = analyzer.count_by_status()
    elif args.wam:
        env = analyzer.weighted_average_maturity()
    elif args.wa_rate:
        env = analyzer.weighted_average_rate()
    elif args.covenant_scan:
        env = analyzer.covenant_breach_scan()
    elif args.at_risk:
        env = analyzer.most_at_risk()
    elif args.over_outstanding:
        if args.threshold is None:
            parser.error("--over-outstanding requires --threshold")
        env = analyzer.filter_over_outstanding(args.threshold)
    else:
        parser.error("choose an analysis (e.g. --top outstanding --n 5, --total outstanding, "
                     "--overdue, --covenant-scan)")

    out = env if args.full else _summarize(env)
    print(json.dumps(out, indent=2, default=str))
    return 0 if env.get("state") == STATE_DELIVERED else 1


if __name__ == "__main__":
    sys.exit(main())
