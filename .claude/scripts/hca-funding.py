#!/usr/bin/env python3
"""hca-funding.py — INVESTOR / FUNDING figures for acos-hypercore-ask.

A "funding figure" is a NAMED, verifiable quantity describing ONE INVESTOR'S stake in ONE
LOAN. The flagship figure is an investor's OUTSTANDING amount on a specific loan, delivered
with the SAME trust guarantees as the payoff figure in hca-figures.py:

    live fetch -> retry-on-flaky-500 -> provenance-bind to a cached Tier-1 record
    -> component reconciliation (within $0.01) -> standard answer envelope ; REFUSE rather
    than fabricate.

DATA MODEL (verified live 2026-06):
  An investor's stake in a loan is a `LoanFunding`. `LoanFundingsFilterInput` accepts
  `assetId` (the loan id), `fundingEntityId`, `loanFundingId`, `searchString`. A DUAL filter
  {assetId, fundingEntityId} intermittently HTTP-500s, so we use the RELIABLE 2-STEP PATH:

    STEP 1 — find the loanFundingId:
      query{ loanFundings(filter:{assetId:"<LOAN_ID>"}, skip:0, limit:100){
               totalFilteredRecords pageItems{ id fundingEntity{ id name } } } }
      -> client-side pick the pageItem whose fundingEntity.id == <FUNDING_ENTITY_ID>; that
         pageItem's `id` is the loanFundingId. If none -> REFUSE (investor does not fund loan).

    STEP 2 — the figure (by the resolved loanFundingId):
      query{ loanFundings(filter:{loanFundingId:"<LF_ID>"}, skip:0, limit:5){
               pageItems{ id fundingEntity{ id name } participationPercentage commitmentAmount
                 receivables{ total principal interest }
                 repaymentSchedule{ summary{
                   totalOutstanding{ total principal interest compoundingInterest totalFees
                     totalPenalties }
                   outstandingPrincipalBeforeAmortization totalDisbursed } } } } }

  OUTSTANDING is `repaymentSchedule.summary.totalOutstanding`. RECONCILE:
      total == principal + interest + compoundingInterest + totalFees + totalPenalties
  within $0.01. (Do NOT add capitalizedBalance — a non-additive memo, and it is intentionally
  NOT selected here.) VERIFIED live: XL (fundingEntity id 3) on Beehive loan 134 ->
  totalOutstanding.total = 6,922,294.60 = principal 6,000,000 + interest 303,289.29 +
  totalFees 46,288.47 + totalPenalties 572,716.84 (compounding 0). Reconciles to the cent.

PROVENANCE PATH:
  The STEP-2 pageItem we pick is cached as an IMMUTABLE Tier-1 record at $.body.record, so the
  outstanding total binds at:
      $.body.record.repaymentSchedule.summary.totalOutstanding.total
  and the lighter single-source figures bind at sibling paths on the SAME record:
      $.body.record.commitmentAmount
      $.body.record.participationPercentage
      $.body.record.receivables.total

GROUND RULES (memory/decisions/2026-06-18-hca-build-ground-rules.md):
  - Python 3 stdlib ONLY. No third-party deps. No model calls; never ANTHROPIC_API_KEY.
  - Read-only: the only API touch is GraphQL `query` (two reads).
  - No real PII committed: this module deals in money totals/components + entity ids only;
    tests use synthetic fixtures (the live XL/Beehive numbers above are non-PII money figures).

This module REUSES the figure spine from hca-figures.py (retry, envelope builders, terminal
state + reason constants, date helpers) rather than reinventing it — imported via the same
importlib `_load` seam the rest of the skill uses.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
from typing import Callable, Optional


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


def _figures():
    # The figure spine (PayoffFigure pattern): retry, envelopes, constants, helpers.
    return _load("hca_figures", "hca-figures.py")


def _adapter():
    return _load("hca_adapter", "hca-adapter.py")


def _cache():
    return _load("hca_cache", "hca-cache.py")


def _provenance():
    return _load("hca_provenance", "hca-provenance.py")


# ---------------------------------------------------------------------------
# Re-exported spine vocabulary (single source of truth: hca-figures.py).
# Re-exported as module attributes so callers + tests can reference
# funding_mod.STATE_DELIVERED / funding_mod.REASON_RECONCILE just like the figure module.
# ---------------------------------------------------------------------------

_fig = _figures()

STATE_DELIVERED = _fig.STATE_DELIVERED
STATE_REFUSED = _fig.STATE_REFUSED
STATE_NO_LIVE_DATA = _fig.STATE_NO_LIVE_DATA

REASON_LIVE_500 = _fig.REASON_LIVE_500
REASON_RECONCILE = _fig.REASON_RECONCILE
REASON_PROVENANCE = _fig.REASON_PROVENANCE
REASON_FETCH_EMPTY = _fig.REASON_FETCH_EMPTY
REASON_BAD_INPUT = _fig.REASON_BAD_INPUT
# Investor does not fund this loan: STEP-1 found no matching fundingEntity on the loan.
REASON_NOT_FUNDING = "NOT_FUNDING"

RECONCILE_TOLERANCE = _fig.RECONCILE_TOLERANCE
RETRY_ATTEMPTS = _fig.RETRY_ATTEMPTS
RETRY_BACKOFF_S = _fig.RETRY_BACKOFF_S

# Re-export the envelope builders + helpers verbatim from the spine.
_envelope = _fig._envelope
_refused = _fig._refused
_now_iso = _fig._now_iso
_today_iso = _fig._today_iso
_valid_date = _fig._valid_date
_call_with_retry = _fig._call_with_retry


# ---------------------------------------------------------------------------
# The 2-step LoanFundings query path (use EXACTLY these shapes — others 500)
# ---------------------------------------------------------------------------

# STEP 1 selection: just enough to find the loanFundingId for a given fundingEntity on a loan.
_STEP1_QUERY = (
    "query HCAFundingsByAsset($filter: LoanFundingsFilterInput, $skip: Int, $limit: Int) { "
    "loanFundings(filter: $filter, skip: $skip, limit: $limit) { "
    "totalFilteredRecords pageItems { id fundingEntity { id name } } "
    "} }"
)
_STEP1_LIMIT = 100

# STEP 2 selection: the full per-funding figure block, by the resolved loanFundingId.
# capitalizedBalance is INTENTIONALLY NOT selected — it is a non-additive memo and must not
# leak into the reconciliation identity.
_STEP2_QUERY = (
    "query HCAFundingByLfId($filter: LoanFundingsFilterInput, $skip: Int, $limit: Int) { "
    "loanFundings(filter: $filter, skip: $skip, limit: $limit) { "
    "pageItems { id fundingEntity { id name } participationPercentage commitmentAmount "
    "currentInterestRate "
    "receivables { total principal interest } "
    "repaymentSchedule { summary { "
    "totalOutstanding { total principal interest compoundingInterest totalFees totalPenalties } "
    "outstandingPrincipalBeforeAmortization totalDisbursed } } } "
    "} }"
)
_STEP2_LIMIT = 5

# STEP-2 selection WITH the repayment schedule table — used only by per_diem_interest so it can
# read Hypercore's NATIVE daily interest accrual (the schedule's "Int. Daily Accrual" column =
# scheduleTable[row].due.interest on each interest-accrual-date row). Carries currentInterestRate
# + totalOutstanding.principal too, so the figure has its computed-cross-check inputs on the SAME
# record. Verified live 2026-06-25 (loanFunding 338 = XL on Lux II, schedule 214570): the current
# accrual row (2026-06-18) due.interest = 1029.2369231252 == principal 2,646,609.23 × 14% ÷ 360,
# matching the UI's $1,029.24 and PROVING Hypercore's day-count is Actual/360.
_SCHEDULE_ROW_SELECTION = (
    "index date type isInterestAccrualDate interestRate "
    "outstanding { principal } due { total interest }"
)
_STEP2_SCHEDULE_QUERY = (
    "query HCAFundingScheduleByLfId($filter: LoanFundingsFilterInput, $skip: Int, $limit: Int) { "
    "loanFundings(filter: $filter, skip: $skip, limit: $limit) { "
    "pageItems { id fundingEntity { id name } currentInterestRate "
    "repaymentSchedule { id summary { totalOutstanding { principal } } scheduleTable { "
    + _SCHEDULE_ROW_SELECTION + " } } } } }"
)

# The components that, summed, MUST equal totalOutstanding.total (reconciliation identity).
# capitalizedBalance is NOT here (non-additive memo).
_OUTSTANDING_COMPONENTS = (
    "principal", "interest", "compoundingInterest", "totalFees", "totalPenalties",
)

# Tier-1 json paths for every bindable value on the cached STEP-2 record (stored at
# $.body.record). The OUTSTANDING total binds to the first; the lighter figures to siblings.
_PATH_OUTSTANDING_TOTAL = (
    "$.body.record.repaymentSchedule.summary.totalOutstanding.total"
)
_PATH_OUTSTANDING_PRINCIPAL = (
    "$.body.record.repaymentSchedule.summary.totalOutstanding.principal"
)
_PATH_CURRENT_INTEREST_RATE = "$.body.record.currentInterestRate"
_PATH_COMMITMENT = "$.body.record.commitmentAmount"
_PATH_PARTICIPATION = "$.body.record.participationPercentage"
_PATH_RECEIVABLE_TOTAL = "$.body.record.receivables.total"

# Per-diem interest is delivered DIRECTLY from Hypercore's repayment schedule (the "Int. Daily
# Accrual" column = scheduleTable[row].due.interest), which carries Hypercore's real day-count
# convention. The figure DERIVES the convention from that native value (implied = principal ×
# rate/100 ÷ native) rather than assuming one. Hypercore's accrual is Actual/360 (proven live
# 2026-06-25: every accrual row's due.interest == principal × rate% ÷ 360 to full precision). The
# computed FALLBACK (only when the native value is unavailable) assumes Actual/360 and says so.

def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


# ---------------------------------------------------------------------------
# The funding figure (mirrors PayoffFigure)
# ---------------------------------------------------------------------------

class FundingFigure:
    """Investor/funding figures for one (loan_id, funding_entity_id) pair.

    Construct with a `client` exposing raw_query(query, variables) -> data (the live
    LiveGraphQLClient satisfies this; tests inject a fake). `cache` + `engine` default to a
    fresh Tier-1 cache + provenance engine so a bound value is independently re-resolvable.

    The flagship `funding_outstanding(...)` mirrors PayoffFigure.fetch_verify exactly:
      STEP 1 (resolve loanFundingId) -> STEP 2 (figure block) with bounded retry on the flaky
      500 -> cache the picked STEP-2 record as immutable Tier-1 -> bind_and_verify the
      outstanding total at its Tier-1 path -> reconcile the 5 components within $0.01 ->
      standard answer envelope. A value reaches `answer` ONLY after BOTH the bind AND the
      reconciliation pass; otherwise the figure REFUSES (never fabricates).

    The lighter figures (commitment / participation / receivable) are SINGLE-SOURCE reads off
    the SAME cached STEP-2 record: each is provenance-bound to its Tier-1 field path (so it is
    re-resolvable) but carries NO reconciliation and a single-source confidence cap (<= 0.7).
    """

    NAME = "funding_outstanding"
    SYNONYMS = ("investor_outstanding", "funding outstanding", "investor outstanding",
                "outstanding to investor", "investor balance")

    def __init__(self, *, client=None, cache=None, engine=None,
                 currency: Optional[str] = None,
                 retry_attempts: int = RETRY_ATTEMPTS,
                 retry_backoff_s: float = RETRY_BACKOFF_S,
                 sleep: Callable[[float], None] = time.sleep):
        self._client = client
        self._cachelib = _cache()
        self._provlib = _provenance()
        self._cache = cache or self._cachelib.TwoTierCache()
        self._engine = engine or self._provlib.ProvenanceEngine(cache=self._cache)
        self._currency = currency
        self._attempts = int(retry_attempts)
        self._backoff = float(retry_backoff_s)
        self._sleep = sleep

    # --- live client (lazy) ------------------------------------------------
    def _ensure_client(self):
        if self._client is not None:
            return self._client
        ad = _adapter()
        self._client = ad.LiveBackend().live_client()
        return self._client

    # --- input guard -------------------------------------------------------
    @staticmethod
    def _check_inputs(loan_id, funding_entity_id):
        if not loan_id:
            return _refused(REASON_BAD_INPUT,
                            "no loan id supplied — cannot compute funding figure")
        if not funding_entity_id:
            return _refused(REASON_BAD_INPUT,
                            "no funding entity id supplied — cannot compute funding figure")
        return None

    # --- shared fetch: resolve loanFundingId then fetch the STEP-2 record ---
    def _fetch_funding_record(self, loan_id: str, funding_entity_id: str,
                              *, step2_query: str = _STEP2_QUERY) -> dict:
        """Run the reliable 2-step path and CACHE the picked STEP-2 record as Tier-1.

        Returns one of:
          {"ok": True, "row": <step2 pageItem>, "rid": <tier1 id>, "fetched_at": ...}
          {"ok": False, "state": ..., "reason_code": ..., "reason": ...}

        Never fabricates: a missing investor (STEP-1 no match) -> NOT_FUNDING refusal; a flaky
        500 surviving the retry budget -> LIVE_500 refusal; an empty/incomplete STEP-2 payload
        -> FETCH_EMPTY refusal.

        `step2_query` selects WHICH STEP-2 selection to fetch — defaults to the lean figure block
        (`_STEP2_QUERY`); the per-diem figure passes `_STEP2_SCHEDULE_QUERY` to additionally pull
        `repaymentSchedule.scheduleTable` so it can read Hypercore's NATIVE daily-accrual value
        without burdening the other funding figures with the 60+ schedule rows.
        """
        loan_id = str(loan_id)
        funding_entity_id = str(funding_entity_id)
        # Build the live client (missing creds -> NO_LIVE_DATA; never fabricate).
        try:
            client = self._ensure_client()
        except Exception as e:
            ad = _adapter()
            if isinstance(e, getattr(ad, "NoLiveDataError", ())):
                return {"ok": False, "state": STATE_NO_LIVE_DATA,
                        "reason_code": STATE_NO_LIVE_DATA, "reason": str(e)}
            return {"ok": False, "state": STATE_REFUSED, "reason_code": REASON_LIVE_500,
                    "reason": (f"could not build live client: {type(e).__name__}: "
                               f"{str(e)[:160]}")}

        # ---- STEP 1: find the loanFundingId for this fundingEntity on this loan ----
        lf_id = self._resolve_loan_funding_id(client, loan_id, funding_entity_id)
        if isinstance(lf_id, dict):  # a refusal dict bubbled up
            return lf_id

        # ---- STEP 2: fetch the full funding figure block by loanFundingId ----
        step2_vars = {"filter": {"loanFundingId": lf_id}, "skip": 0, "limit": _STEP2_LIMIT}
        try:
            data, _attempts, _errs = _call_with_retry(
                client, step2_query, step2_vars,
                attempts=self._attempts, backoff_s=self._backoff, sleep=self._sleep,
                # a transiently-empty page is re-fetched (same input); still empty -> refuse below.
                is_empty=lambda d: not (((d or {}).get("loanFundings") or {}).get("pageItems")))
        except Exception as e:
            return {"ok": False, "state": STATE_REFUSED, "reason_code": REASON_LIVE_500,
                    "reason": (f"loanFundings(loanFundingId) failed after {self._attempts} "
                               f"attempt(s): {type(e).__name__}: {str(e)[:200]} (the resolver "
                               "returns intermittent HTTP 500; refusing rather than fabricating)")}

        items = (((data or {}).get("loanFundings") or {}).get("pageItems")) or []
        row = next((it for it in items if str((it or {}).get("id")) == lf_id), None)
        if row is None:
            return {"ok": False, "state": STATE_REFUSED, "reason_code": REASON_FETCH_EMPTY,
                    "reason": (f"loanFundings(loanFundingId={lf_id!r}) returned no matching "
                               "funding record — refusing (never guess)")}

        # ---- cache the picked STEP-2 record as an immutable Tier-1 record ----
        fetched_at = _now_iso()
        ad = _adapter()
        raw = ad.make_raw_api_response(
            raw_response_id=f"live:loanFunding:{loan_id}:{funding_entity_id}:{lf_id}:{fetched_at}",
            endpoint="loanFundings",
            request_params={"graphql_operation": "HCAFundingByLfId",
                            "loanFundingId": lf_id, "asset_id": loan_id,
                            "funding_entity_id": funding_entity_id},
            timestamp=fetched_at, http_status=200, cursor=None, reported_total=None,
            body={"record": row,
                  "provenance": {"fetched_at": fetched_at, "operation": "loanFundings",
                                 "loan_funding_id": lf_id, "asset_id": loan_id,
                                 "funding_entity_id": funding_entity_id}},
            backend="live")
        rid = self._cache.put_raw(raw)
        stored = self._cache.get_raw(rid).get("body", {}).get("record", row)
        return {"ok": True, "row": stored, "rid": rid, "fetched_at": fetched_at,
                "loan_funding_id": lf_id}

    def _resolve_loan_funding_id(self, client, loan_id: str, funding_entity_id: str):
        """STEP 1 — page loanFundings(filter:{assetId}) and pick the pageItem whose
        fundingEntity.id == funding_entity_id; return its `id` (the loanFundingId).

        Returns the loanFundingId str on success, or a REFUSAL DICT (NOT_FUNDING / LIVE_500)
        on failure. Pages skip/limit to completion so an investor on a later page is still found.
        """
        skip = 0
        pages = 0
        while True:
            pages += 1
            if pages > 1000:  # defensive bound; never infinite-loop on a misbehaving endpoint
                break
            step1_vars = {"filter": {"assetId": loan_id}, "skip": skip, "limit": _STEP1_LIMIT}
            try:
                data, _attempts, _errs = _call_with_retry(
                    client, _STEP1_QUERY, step1_vars,
                    attempts=self._attempts, backoff_s=self._backoff, sleep=self._sleep,
                    is_empty=lambda d: (d or {}).get("loanFundings") is None)
            except Exception as e:
                return {"ok": False, "state": STATE_REFUSED, "reason_code": REASON_LIVE_500,
                        "reason": (f"loanFundings(assetId={loan_id!r}) failed after "
                                   f"{self._attempts} attempt(s): {type(e).__name__}: "
                                   f"{str(e)[:200]} (intermittent HTTP 500; refusing rather "
                                   "than fabricating)")}
            page = (data or {}).get("loanFundings") or {}
            items = page.get("pageItems") or []
            for it in items:
                fe = (it or {}).get("fundingEntity") or {}
                if str(fe.get("id")) == funding_entity_id:
                    lf_id = (it or {}).get("id")
                    if lf_id is None:
                        return {"ok": False, "state": STATE_REFUSED,
                                "reason_code": REASON_FETCH_EMPTY,
                                "reason": ("matched fundingEntity on the loan but the funding "
                                           "record has no id — refusing")}
                    return str(lf_id)
            total = page.get("totalFilteredRecords")
            got = skip + len(items)
            if not items or (total is not None and got >= total):
                break
            if len(items) < _STEP1_LIMIT:
                break
            skip += _STEP1_LIMIT
        # Exhausted the loan's fundings without a fundingEntity match -> investor doesn't fund it.
        return {"ok": False, "state": STATE_REFUSED, "reason_code": REASON_NOT_FUNDING,
                "reason": (f"funding entity {funding_entity_id!r} does not fund loan "
                           f"{loan_id!r} (no LoanFunding with that fundingEntity) — refusing")}

    # --- helper to surface a fetch refusal as a standard envelope ----------
    @staticmethod
    def _fetch_refusal_envelope(fetched: dict, *, figure: str, loan_id, funding_entity_id):
        state = fetched.get("state", STATE_REFUSED)
        meta = {"figure": figure, "loan_id": loan_id, "funding_entity_id": funding_entity_id}
        if state == STATE_NO_LIVE_DATA:
            return _envelope(STATE_NO_LIVE_DATA, answer=None, values=[], gate_verdict=None,
                             complete=False,
                             refusals=[{"reason_code": STATE_NO_LIVE_DATA,
                                        "reason": fetched.get("reason")}],
                             meta=meta)
        return _refused(fetched.get("reason_code", REASON_FETCH_EMPTY),
                        fetched.get("reason", "funding fetch failed"), meta=meta)

    # --- reconciliation (5 components -> total within $0.01) ----------------
    @staticmethod
    def _reconcile_outstanding(outstanding: dict, total: float) -> dict:
        """Sum the 5 OUTSTANDING components and compare to total within tolerance.

        An absent/null component contributes 0.0 (a null is a real 0 contribution).
        capitalizedBalance is deliberately NOT summed (non-additive memo).
        """
        itemized = {}
        comp_sum = 0.0
        for f in _OUTSTANDING_COMPONENTS:
            v = (outstanding or {}).get(f)
            num = float(v) if _is_number(v) else 0.0
            itemized[f] = num
            comp_sum += num
        comp_sum = round(comp_sum, 4)
        diff = round(abs(comp_sum - float(total)), 6)
        return {"ok": diff <= RECONCILE_TOLERANCE, "component_sum": comp_sum,
                "diff": diff, "components": itemized}

    # === FLAGSHIP: investor's OUTSTANDING on a loan (reconciled) ===========
    def funding_outstanding(self, *, loan_id: str, funding_entity_id: str,
                            currency: Optional[str] = None,
                            loan_name: Optional[str] = None,
                            **_ignored) -> dict:
        """The investor's OUTSTANDING amount on the loan (reconciled + provenance-bound).

        Returns the STANDARD ANSWER ENVELOPE. The total only reaches `answer` after it is
        bound to Tier-1 AND the 5 components reconcile to it within $0.01 — else REFUSE.
        Echoes participationPercentage + commitmentAmount in meta.
        """
        bad = self._check_inputs(loan_id, funding_entity_id)
        if bad is not None:
            return bad

        fetched = self._fetch_funding_record(str(loan_id), str(funding_entity_id))
        if not fetched.get("ok"):
            return self._fetch_refusal_envelope(fetched, figure=self.NAME, loan_id=loan_id,
                                                funding_entity_id=funding_entity_id)

        row = fetched["row"]
        rid = fetched["rid"]
        lf_id = fetched.get("loan_funding_id")
        summary = (((row or {}).get("repaymentSchedule") or {}).get("summary") or {})
        outstanding = summary.get("totalOutstanding") or {}
        total = outstanding.get("total")
        if not _is_number(total):
            return _refused(REASON_FETCH_EMPTY,
                            f"non-numeric/absent totalOutstanding.total ({total!r}) — refusing",
                            meta={"figure": self.NAME, "loan_id": loan_id,
                                  "funding_entity_id": funding_entity_id})

        # PROVENANCE: bind the total to its Tier-1 path. A mismatch/miss => REFUSE.
        prov = self._engine.bind_and_verify(
            total, {"raw_response_id": rid, "json_field_path": _PATH_OUTSTANDING_TOTAL},
            value_ref=f"loan.{loan_id}.funding.{funding_entity_id}.outstanding")
        if prov["outcome"] != self._provlib.VERIFIED:
            return _refused(REASON_PROVENANCE, prov["reason"],
                            meta={"figure": self.NAME, "loan_id": loan_id,
                                  "funding_entity_id": funding_entity_id,
                                  "reason_code_inner": prov["reason_code"]})

        # RECONCILE: 5 components must sum to total within tolerance, else REFUSE.
        recon = self._reconcile_outstanding(outstanding, total)
        if not recon["ok"]:
            return _refused(
                REASON_RECONCILE,
                (f"funding outstanding components do not reconcile to total within "
                 f"${RECONCILE_TOLERANCE}: sum(components)={recon['component_sum']} vs "
                 f"total={total} (diff={recon['diff']}) — refusing (an internally inconsistent "
                 "outstanding is never delivered)"),
                meta={"figure": self.NAME, "loan_id": loan_id,
                      "funding_entity_id": funding_entity_id,
                      "components": recon["components"], "component_sum": recon["component_sum"],
                      "total": total, "diff": recon["diff"], "reconciles": False})

        # CONFIDENCE: single-source figure -> capped + flagged via the engine.
        conf = self._engine.confidence_record(
            f"loan.{loan_id}.funding.{funding_entity_id}.outstanding", source_count=1,
            basis="single-source LoanFunding outstanding (reconciled)")

        cur = currency or self._currency
        fe = (row or {}).get("fundingEntity") or {}
        participation = (row or {}).get("participationPercentage")
        commitment = (row or {}).get("commitmentAmount")
        out_value = {
            "value": float(total),
            "currency": cur,
            "provenance": {
                "raw_response_id": rid,
                "json_field_path": _PATH_OUTSTANDING_TOTAL,
                "operation": "loanFundings",
                "loan_funding_id": lf_id,
                "asset_id": str(loan_id),
                "funding_entity_id": str(funding_entity_id),
                "fetched_at": fetched.get("fetched_at"),
            },
            "confidence": conf["confidence"],
        }
        inv_str = f" {fe.get('name')!r}" if fe.get("name") else ""
        name_str = f" on {loan_name!r}" if loan_name else ""
        cur_str = f" {cur}" if cur else ""
        answer = (f"Investor{inv_str} (funding entity {funding_entity_id}) outstanding on loan "
                  f"{loan_id}{name_str} is {float(total)}{cur_str}.")
        gate_verdict = {
            "outcome": "pass",
            "reconciliation_ok": True,
            "reconcile_tolerance": RECONCILE_TOLERANCE,
            "component_sum": recon["component_sum"],
            "total": float(total),
            "diff": recon["diff"],
            "single_source": conf["single_source"],
        }
        return _envelope(
            STATE_DELIVERED, answer=answer, values=[out_value],
            gate_verdict=gate_verdict, complete=True, refusals=[],
            meta={
                "figure": self.NAME,
                "loan_id": loan_id,
                "loan_name": loan_name,
                "funding_entity_id": funding_entity_id,
                "funding_entity_name": fe.get("name"),
                "loan_funding_id": lf_id,
                "currency": cur,
                "reconciles": True,
                "components": recon["components"],
                "participationPercentage": participation,
                "commitmentAmount": commitment,
                "confidence_record": conf,
            })

    # === LIGHTER FIGURES: single-source reads off the SAME STEP-2 record ===
    def _light_figure(self, *, figure: str, value_path: str, field_name: str,
                      unit: str, loan_id: str, funding_entity_id: str,
                      currency: Optional[str], loan_name: Optional[str]) -> dict:
        """Shared body for the non-reconciled single-source funding figures.

        Fetches (via the 2-step path) + caches the STEP-2 record, reads `field_name`, binds it
        to `value_path` on the SAME Tier-1 record (so it is re-resolvable), and caps confidence
        at the single-source ceiling (<= 0.7). No reconciliation. REFUSE on a missing/non-numeric
        value (never guess).
        """
        bad = self._check_inputs(loan_id, funding_entity_id)
        if bad is not None:
            return bad
        fetched = self._fetch_funding_record(str(loan_id), str(funding_entity_id))
        if not fetched.get("ok"):
            return self._fetch_refusal_envelope(fetched, figure=figure, loan_id=loan_id,
                                                funding_entity_id=funding_entity_id)
        row = fetched["row"]
        rid = fetched["rid"]
        lf_id = fetched.get("loan_funding_id")

        value = self._read_field(row, field_name)
        if value is _ABSENT or not _is_number(value):
            return _refused(REASON_FETCH_EMPTY,
                            f"{figure}: non-numeric/absent {field_name!r} ({value!r}) — refusing",
                            meta={"figure": figure, "loan_id": loan_id,
                                  "funding_entity_id": funding_entity_id})

        prov = self._engine.bind_and_verify(
            value, {"raw_response_id": rid, "json_field_path": value_path},
            value_ref=f"loan.{loan_id}.funding.{funding_entity_id}.{figure}")
        if prov["outcome"] != self._provlib.VERIFIED:
            return _refused(REASON_PROVENANCE, prov["reason"],
                            meta={"figure": figure, "loan_id": loan_id,
                                  "funding_entity_id": funding_entity_id,
                                  "reason_code_inner": prov["reason_code"]})

        conf = self._engine.confidence_record(
            f"loan.{loan_id}.funding.{funding_entity_id}.{figure}", source_count=1,
            basis=f"single-source LoanFunding read ({field_name})")
        cur = currency or self._currency
        fe = (row or {}).get("fundingEntity") or {}
        out_value = {
            "value": value,
            "currency": cur if unit == "currency" else None,
            "unit": unit,
            "provenance": {"raw_response_id": rid, "json_field_path": value_path,
                           "operation": "loanFundings", "field": field_name,
                           "loan_funding_id": lf_id, "asset_id": str(loan_id),
                           "funding_entity_id": str(funding_entity_id),
                           "fetched_at": fetched.get("fetched_at")},
            "confidence": conf["confidence"],
        }
        cur_str = f" {cur}" if (cur and unit == "currency") else ""
        answer = (f"{figure} for funding entity {funding_entity_id} on loan {loan_id} "
                  f"is {value}{cur_str}.")
        gate_verdict = {"outcome": "pass", "single_source": conf["single_source"],
                        "reconciliation_ok": None}
        return _envelope(STATE_DELIVERED, answer=answer, values=[out_value],
                         gate_verdict=gate_verdict, complete=True, refusals=[],
                         meta={"figure": figure, "loan_id": loan_id, "loan_name": loan_name,
                               "funding_entity_id": funding_entity_id,
                               "funding_entity_name": fe.get("name"),
                               "loan_funding_id": lf_id, "currency": cur, "unit": unit,
                               "confidence_record": conf})

    @staticmethod
    def _read_field(row: dict, field_name: str):
        """Read a STEP-2 field, supporting the one nested case (receivables.total)."""
        if "." in field_name:
            cur = row
            for k in field_name.split("."):
                if not isinstance(cur, dict) or k not in cur:
                    return _ABSENT
                cur = cur[k]
            return cur
        if not isinstance(row, dict) or field_name not in row:
            return _ABSENT
        return row[field_name]

    def funding_commitment(self, *, loan_id: str, funding_entity_id: str,
                           currency: Optional[str] = None, loan_name: Optional[str] = None,
                           **_ignored) -> dict:
        """The investor's commitmentAmount on the loan (single-source; no reconciliation)."""
        return self._light_figure(
            figure="funding_commitment", value_path=_PATH_COMMITMENT,
            field_name="commitmentAmount", unit="currency",
            loan_id=loan_id, funding_entity_id=funding_entity_id,
            currency=currency, loan_name=loan_name)

    def funding_participation(self, *, loan_id: str, funding_entity_id: str,
                              currency: Optional[str] = None, loan_name: Optional[str] = None,
                              **_ignored) -> dict:
        """The investor's participationPercentage in the loan (single-source; no reconciliation)."""
        return self._light_figure(
            figure="funding_participation", value_path=_PATH_PARTICIPATION,
            field_name="participationPercentage", unit="percent",
            loan_id=loan_id, funding_entity_id=funding_entity_id,
            currency=currency, loan_name=loan_name)

    def funding_receivable(self, *, loan_id: str, funding_entity_id: str,
                           currency: Optional[str] = None, loan_name: Optional[str] = None,
                           **_ignored) -> dict:
        """The investor's receivables.total on the loan (single-source; no reconciliation)."""
        return self._light_figure(
            figure="funding_receivable", value_path=_PATH_RECEIVABLE_TOTAL,
            field_name="receivables.total", unit="currency",
            loan_id=loan_id, funding_entity_id=funding_entity_id,
            currency=currency, loan_name=loan_name)

    # === investor's PER-DIEM (daily) interest — NATIVE from Hypercore's schedule ===========
    @staticmethod
    def _pick_current_accrual_row(table, as_of):
        """Return (list_index, row) for the CURRENT daily-accrual row in a scheduleTable.

        The current per-diem is the LATEST interest-accrual-date row (isInterestAccrualDate True)
        whose date <= as_of and whose due.interest is positive — that mirrors the UI's most-recent
        "Int. Accrued" row. If no accrual row is at/before as_of (a not-yet-accruing position), fall
        back to the EARLIEST upcoming accrual row so the question still answers. Returns
        (None, None) when there is no positive-interest accrual row at all. list_index is the
        POSITION in the returned scheduleTable (what the array-path provenance binds to), NOT the
        row's own `index` field."""
        accr = []
        for i, r in enumerate(table or []):
            if not isinstance(r, dict) or not r.get("isInterestAccrualDate"):
                continue
            di = (r.get("due") or {}).get("interest")
            if not _is_number(di) or di <= 0:
                continue
            accr.append((i, r, str(r.get("date") or "")))
        if not accr:
            return None, None
        at_or_before = [t for t in accr if t[2] and t[2] <= as_of]
        pool = at_or_before if at_or_before else accr
        # latest date wins (earliest if all future); the row `index` breaks date ties deterministically.
        chooser = max if at_or_before else min
        i, r, _d = chooser(pool, key=lambda t: (t[2], t[1].get("index") or 0))
        return i, r

    def per_diem_interest(self, *, loan_id: str, funding_entity_id: str,
                          currency: Optional[str] = None, loan_name: Optional[str] = None,
                          as_of: Optional[str] = None, **_ignored) -> dict:
        """The investor's PER-DIEM (daily) interest — DELIVERED DIRECTLY FROM HYPERCORE.

        PRIMARY (the delivered value): Hypercore's OWN daily accrual — `scheduleTable[row].due.interest`
        on the current interest-accrual row of the investor's repayment schedule (the UI's
        "Int. Daily Accrual" column under Lux II → XL → Schedule). It is provenance-bound to its exact
        Tier-1 array path (`$.body.record.repaymentSchedule.scheduleTable[K].due.interest`) so it is
        independently re-resolvable, and it carries Hypercore's real day-count convention baked in.

        CROSS-CHECK (double-check ONLY — never the delivered number): independently DERIVE the implied
        day-count from Hypercore's own value (implied = principal × rate/100 ÷ native). A clean 360 or
        365 CONFIRMS the convention (reported as confirmed, not assumed). A value that matches neither
        is FLAGGED in the gate — but the native value is STILL delivered, because it is the source of
        truth; the flag just surfaces that the convention is non-standard.

        FALLBACK (only when the native value is unavailable — no schedule / no positive accrual row):
        compute principal × rate/100 ÷ 360 from the funding record, CLEARLY LABELLED computed +
        Actual/360 ASSUMED. Preferred over refusing so the question still answers, but never presented
        as Hypercore's own figure.

        Live-verified 2026-06-25 (XL on Lux II, loanFunding 338, schedule 214570): native current
        accrual row (2026-06-18) due.interest = 1029.236923 == 2,646,609.23 × 14% ÷ 360 = the UI's
        $1,029.24.
        """
        bad = self._check_inputs(loan_id, funding_entity_id)
        if bad is not None:
            return bad
        as_of = as_of or _today_iso()
        meta_base = {"figure": "per_diem_interest", "loan_id": loan_id,
                     "funding_entity_id": funding_entity_id, "as_of": as_of}
        if not _valid_date(as_of):
            return _refused(REASON_BAD_INPUT,
                            "per_diem_interest: invalid as_of date %r (expected YYYY-MM-DD)"
                            % (as_of,), meta=meta_base)

        fetched = self._fetch_funding_record(str(loan_id), str(funding_entity_id),
                                             step2_query=_STEP2_SCHEDULE_QUERY)
        if not fetched.get("ok"):
            return self._fetch_refusal_envelope(fetched, figure="per_diem_interest",
                                                loan_id=loan_id,
                                                funding_entity_id=funding_entity_id)
        row = fetched["row"]
        rid = fetched["rid"]
        lf_id = fetched.get("loan_funding_id")
        fe = (row or {}).get("fundingEntity") or {}
        cur = currency or self._currency
        sched = (row or {}).get("repaymentSchedule") or {}
        table = sched.get("scheduleTable") or []
        k, arow = self._pick_current_accrual_row(table, as_of)

        # ------------------------------------------------------------------ NATIVE PATH (preferred)
        if arow is not None:
            native = (arow.get("due") or {}).get("interest")
            ar_principal = (arow.get("outstanding") or {}).get("principal")
            ar_rate = arow.get("interestRate")
            ar_date = str(arow.get("date") or "")
            npath = "$.body.record.repaymentSchedule.scheduleTable[%d].due.interest" % k
            prov = self._engine.bind_and_verify(
                native, {"raw_response_id": rid, "json_field_path": npath},
                value_ref="loan.%s.funding.%s.per_diem.native" % (loan_id, funding_entity_id))
            if prov["outcome"] != self._provlib.VERIFIED:
                return _refused(REASON_PROVENANCE, prov["reason"],
                                meta={**meta_base, "reason_code_inner": prov["reason_code"],
                                      "input": "native_due_interest"})

            # CROSS-CHECK: derive the implied day-count from Hypercore's own value (double-check only).
            cross = None
            convention = "unknown"
            convention_confirmed = False
            if (_is_number(ar_principal) and _is_number(ar_rate) and ar_rate > 0
                    and _is_number(native) and native > 0):
                annual = float(ar_principal) * (float(ar_rate) / 100.0)
                implied = round(annual / float(native), 4)
                computed_360 = round(annual / 360.0, 6)
                cross = {"computed_actual_360": computed_360, "implied_day_count": implied,
                         "matches_360": abs(float(native) - computed_360) <= RECONCILE_TOLERANCE}
                if abs(implied - 360) <= 0.5:
                    convention, convention_confirmed = "Actual/360", True
                elif abs(implied - 365) <= 0.5:
                    convention, convention_confirmed = "Actual/365", True
                else:
                    convention = "Actual/%s" % (int(round(implied)) if implied else "?")

            conf = self._engine.confidence_record(
                "loan.%s.funding.%s.per_diem_interest" % (loan_id, funding_entity_id),
                source_count=1,
                basis=("Hypercore-native daily accrual (scheduleTable.due.interest) with a computed "
                       "cross-check"))
            out_value = {
                "value": float(native),
                "currency": cur,
                "unit": "currency_per_day",
                "provenance": {
                    "source": "hypercore_native",
                    "raw_response_id": rid,
                    "json_field_path": npath,
                    "operation": "loanFundings",
                    "field": "repaymentSchedule.scheduleTable[].due.interest",
                    "schedule_id": sched.get("id"),
                    "accrual_row_date": ar_date,
                    "accrual_row_index": arow.get("index"),
                    "loan_funding_id": lf_id, "asset_id": str(loan_id),
                    "funding_entity_id": str(funding_entity_id),
                    "fetched_at": fetched.get("fetched_at"),
                    "cross_check": cross,
                    "day_count_convention": convention,
                    "day_count_confirmed": convention_confirmed,
                },
                "confidence": conf["confidence"],
            }
            inv_str = " %r" % fe.get("name") if fe.get("name") else ""
            name_str = " on %r" % loan_name if loan_name else ""
            cur_str = " %s" % cur if cur else ""
            conv_str = (("%s (confirmed by Hypercore's own accrual)" % convention)
                        if convention_confirmed
                        else ("%s (implied from Hypercore's value)" % convention))
            answer = (
                "Per-diem interest for investor%s (funding entity %s) on loan %s%s is %s%s per day "
                "(≈ %.2f) — read DIRECTLY from Hypercore's repayment schedule (Int. Daily "
                "Accrual, accrual row dated %s). Day-count convention: %s."
                % (inv_str, funding_entity_id, loan_id, name_str, float(native), cur_str,
                   round(float(native), 2), ar_date, conv_str))
            gate_verdict = {
                "outcome": "pass", "source": "hypercore_native",
                "single_source": conf["single_source"],
                "day_count_convention": convention, "day_count_confirmed": convention_confirmed,
                "cross_check": cross,
            }
            if cross is not None and not cross["matches_360"] and not convention_confirmed:
                gate_verdict["cross_check_flag"] = (
                    "Hypercore's native daily accrual matches neither a clean Actual/360 nor "
                    "Actual/365 computation — delivering the native value, flagging the convention")
            return _envelope(
                STATE_DELIVERED, answer=answer, values=[out_value],
                gate_verdict=gate_verdict, complete=True, refusals=[],
                meta={
                    "figure": "per_diem_interest", "loan_id": loan_id, "loan_name": loan_name,
                    "funding_entity_id": funding_entity_id, "funding_entity_name": fe.get("name"),
                    "loan_funding_id": lf_id, "schedule_id": sched.get("id"),
                    "currency": cur, "unit": "currency_per_day",
                    "source": "hypercore_native", "accrual_row_date": ar_date,
                    "outstanding_principal": (float(ar_principal) if _is_number(ar_principal) else None),
                    "current_interest_rate_percent": (float(ar_rate) if _is_number(ar_rate) else None),
                    "day_count_convention": convention, "day_count_confirmed": convention_confirmed,
                    "cross_check": cross, "confidence_record": conf, "as_of": as_of,
                })

        # ------------------------------------------------------------- FALLBACK PATH (computed)
        # No native accrual row available -> compute from the funding record, CLEARLY labelled.
        summary = (sched.get("summary") or {})
        rec_principal = ((summary.get("totalOutstanding") or {}).get("principal"))
        rec_rate = (row or {}).get("currentInterestRate")
        if not _is_number(rec_principal):
            return _refused(REASON_FETCH_EMPTY,
                            "per_diem_interest: no Hypercore-native accrual row AND no outstanding "
                            "principal to compute from — refusing (never fabricate)", meta=meta_base)
        if not _is_number(rec_rate):
            return _refused(REASON_FETCH_EMPTY,
                            "per_diem_interest: no Hypercore-native accrual row AND absent "
                            "currentInterestRate — refusing", meta=meta_base)
        if rec_rate <= 0:
            return _refused(REASON_BAD_INPUT,
                            "per_diem_interest: currentInterestRate non-positive (%r) — a per-diem "
                            "requires an interest-bearing position; refusing" % (rec_rate,),
                            meta=meta_base)
        prov_p = self._engine.bind_and_verify(
            rec_principal, {"raw_response_id": rid, "json_field_path": _PATH_OUTSTANDING_PRINCIPAL},
            value_ref="loan.%s.funding.%s.per_diem.principal" % (loan_id, funding_entity_id))
        if prov_p["outcome"] != self._provlib.VERIFIED:
            return _refused(REASON_PROVENANCE, prov_p["reason"],
                            meta={**meta_base, "input": "outstanding_principal"})
        prov_r = self._engine.bind_and_verify(
            rec_rate, {"raw_response_id": rid, "json_field_path": _PATH_CURRENT_INTEREST_RATE},
            value_ref="loan.%s.funding.%s.per_diem.rate" % (loan_id, funding_entity_id))
        if prov_r["outcome"] != self._provlib.VERIFIED:
            return _refused(REASON_PROVENANCE, prov_r["reason"],
                            meta={**meta_base, "input": "currentInterestRate"})
        per_diem = round(float(rec_principal) * (float(rec_rate) / 100.0) / 360, 6)
        conf = self._engine.confidence_record(
            "loan.%s.funding.%s.per_diem_interest" % (loan_id, funding_entity_id), source_count=1,
            basis=("computed per-diem (Hypercore-native daily accrual unavailable for this "
                   "position; Actual/360 ASSUMED)"))
        out_value = {
            "value": per_diem, "currency": cur, "unit": "currency_per_day",
            "provenance": {
                "source": "computed_fallback",
                "formula": "outstanding_principal * (currentInterestRate / 100) / 360",
                "inputs": {
                    "outstanding_principal": {"raw_response_id": rid,
                                              "json_field_path": _PATH_OUTSTANDING_PRINCIPAL,
                                              "value": float(rec_principal)},
                    "currentInterestRate": {"raw_response_id": rid,
                                            "json_field_path": _PATH_CURRENT_INTEREST_RATE,
                                            "value": float(rec_rate), "scale": "percent"},
                },
                "day_count": 360, "day_count_convention": "Actual/360", "day_count_assumed": True,
                "operation": "loanFundings", "loan_funding_id": lf_id, "asset_id": str(loan_id),
                "funding_entity_id": str(funding_entity_id), "fetched_at": fetched.get("fetched_at"),
            },
            "confidence": conf["confidence"],
        }
        inv_str = " %r" % fe.get("name") if fe.get("name") else ""
        name_str = " on %r" % loan_name if loan_name else ""
        cur_str = " %s" % cur if cur else ""
        answer = (
            "Per-diem interest for investor%s (funding entity %s) on loan %s%s is %s%s per day "
            "(≈ %.2f) — COMPUTED (Hypercore's native daily accrual was unavailable for this "
            "position): outstanding principal %s × %s%% ÷ 360. Day-count Actual/360 (ASSUMED)."
            % (inv_str, funding_entity_id, loan_id, name_str, per_diem, cur_str,
               round(per_diem, 2), float(rec_principal), float(rec_rate)))
        gate_verdict = {
            "outcome": "pass", "source": "computed_fallback",
            "formula": "outstanding_principal * (currentInterestRate / 100) / 360",
            "day_count": 360, "day_count_convention": "Actual/360", "day_count_assumed": True,
            "single_source": conf["single_source"],
        }
        return _envelope(
            STATE_DELIVERED, answer=answer, values=[out_value],
            gate_verdict=gate_verdict, complete=True, refusals=[],
            meta={
                "figure": "per_diem_interest", "loan_id": loan_id, "loan_name": loan_name,
                "funding_entity_id": funding_entity_id, "funding_entity_name": fe.get("name"),
                "loan_funding_id": lf_id, "currency": cur, "unit": "currency_per_day",
                "source": "computed_fallback",
                "outstanding_principal": float(rec_principal),
                "current_interest_rate_percent": float(rec_rate),
                "day_count": 360, "day_count_convention": "Actual/360", "day_count_assumed": True,
                "confidence_record": conf, "as_of": as_of,
            })

    # --- registry: figure name -> callable ---------------------------------
    def registry(self) -> dict:
        """Map of funding-figure name -> bound callable(loan_id, funding_entity_id, ...)."""
        return {
            "funding_outstanding": self.funding_outstanding,
            "funding_commitment": self.funding_commitment,
            "funding_participation": self.funding_participation,
            "funding_receivable": self.funding_receivable,
            "per_diem_interest": self.per_diem_interest,
        }


_ABSENT = object()


# Canonical figure-name list (single source of truth for callers/tests).
FUNDING_FIGURE_NAMES = (
    "funding_outstanding",
    "funding_commitment",
    "funding_participation",
    "funding_receivable",
    "per_diem_interest",
)


# ---------------------------------------------------------------------------
# Module-level convenience: run ONE figure by (loan_id, funding_entity_id)
# ---------------------------------------------------------------------------

def run_funding_figure(figure: str, *, loan_id: str, funding_entity_id: str,
                       client=None, cache=None, engine=None,
                       currency: Optional[str] = None, loan_name: Optional[str] = None,
                       sleep: Callable[[float], None] = time.sleep,
                       **kwargs) -> dict:
    """Run a single named funding figure by (loan_id, funding_entity_id).

    `figure` is one of FUNDING_FIGURE_NAMES (or a funding_outstanding synonym). Returns the
    STANDARD ANSWER ENVELOPE, or a REFUSED envelope naming an unknown figure. `client` defaults
    to the live read-only backend; tests inject a fake.
    """
    fig = FundingFigure(client=client, cache=cache, engine=engine, currency=currency,
                        sleep=sleep)
    reg = fig.registry()
    fn = reg.get(figure)
    if fn is None:
        # honor the flagship's synonyms (route them to funding_outstanding)
        token = (figure or "").strip().lower()
        if token == FundingFigure.NAME or token in {s.lower() for s in FundingFigure.SYNONYMS}:
            fn = reg["funding_outstanding"]
    if fn is None:
        return _refused(REASON_BAD_INPUT,
                        f"unknown funding figure {figure!r} (known: {list(reg)})",
                        meta={"loan_id": loan_id, "funding_entity_id": funding_entity_id})
    return fn(loan_id=loan_id, funding_entity_id=funding_entity_id,
             currency=currency, loan_name=loan_name, **kwargs)


# ---------------------------------------------------------------------------
# INVESTOR-PORTFOLIO figures (fundingEntity-level: across ALL the investor's loans)
# ---------------------------------------------------------------------------

# The investor's portfolio receivable lives on fundingEntity.receivables (InstallmentComponents).
# Reconciliation identity = the FULL InstallmentComponents identity (None -> 0). Verified live
# 2026-06-24: ALL 62 funding entities reconcile under this identity to the cent. (capitalizedBalance
# is not an InstallmentComponents field and never enters the sum.)
_RECEIVABLE_COMPONENTS = (
    "principal", "indexedPrincipal", "interest", "compoundingInterest",
    "accruedCompoundingInterest", "totalFees", "totalPenalties", "totalTaxes",
)
# The RELIABLE fundingEntities list query — fetch ONE entity by id (match client-side), paging to
# completion. (The single fundingEntity(id) resolver is flaky; the list path is the proven one.)
_PORTFOLIO_QUERY = (
    "query HCAFundingEntity($filter: FundingEntitiesFilterInput, $skip: Int, $limit: Int) { "
    "fundingEntities(filter: $filter, skip: $skip, limit: $limit) { "
    "totalFilteredRecords pageItems { id name totalCommitment totalDisbursement contributed "
    "activeLoansCount receivables { total principal indexedPrincipal interest compoundingInterest "
    "accruedCompoundingInterest totalFees totalPenalties totalTaxes } } "
    "} }"
)
_PORTFOLIO_LIMIT = 200
_PPATH_RECEIVABLE_TOTAL = "$.body.record.receivables.total"
_PPATH_COMMITMENT = "$.body.record.totalCommitment"
_PPATH_DISBURSEMENT = "$.body.record.totalDisbursement"
_PPATH_CONTRIBUTED = "$.body.record.contributed"
_PPATH_ACTIVE_LOANS = "$.body.record.activeLoansCount"

# Portfolio OUTSTANDING is computed as a RECONCILED AGGREGATE over the investor's LoanFunding
# positions (loanFundings filter:{fundingEntityId}) — a reliable path, unlike the flaky
# fundingEntity.mergedLoanFundingsSummary (which 500s). Each position's totalOutstanding is itself
# reconciled (the 5-component _OUTSTANDING_COMPONENTS identity) and provenance-bound to its own
# Tier-1 record; the sum is bind_aggregate-verified; the page set is completeness-checked.
_PORTFOLIO_OUTSTANDING_QUERY = (
    "query HCAPortfolioOutstanding($filter: LoanFundingsFilterInput, $skip: Int, $limit: Int) { "
    "loanFundings(filter: $filter, skip: $skip, limit: $limit) { "
    "totalFilteredRecords pageItems { id fundingEntity { id name } asset { id name } "
    "repaymentSchedule { summary { totalOutstanding { total principal interest "
    "compoundingInterest totalFees totalPenalties } } } } "
    "} }"
)
_PORTFOLIO_OUTSTANDING_LIMIT = 100


class FundingPortfolioFigure:
    """fundingEntity-level (PORTFOLIO) figures for ONE investor across ALL their loans.

    Flagship `portfolio_receivable` is RECONCILED (the InstallmentComponents identity) +
    provenance-bound, mirroring FundingFigure's trust contract. The lighter portfolio scalars
    (commitment / disbursement / contributed / active_loans) are single-source provenance-bound
    reads (no reconciliation; confidence cap <= 0.7). Fetch is the reliable fundingEntities list
    query filtered by name_hint (or unfiltered, paged), matched by id. Never fabricates.
    """

    NAME = "portfolio_receivable"

    def __init__(self, *, client=None, cache=None, engine=None,
                 currency: Optional[str] = None,
                 retry_attempts: int = RETRY_ATTEMPTS,
                 retry_backoff_s: float = RETRY_BACKOFF_S,
                 sleep: Callable[[float], None] = time.sleep):
        self._client = client
        self._cachelib = _cache()
        self._provlib = _provenance()
        self._cache = cache or self._cachelib.TwoTierCache()
        self._engine = engine or self._provlib.ProvenanceEngine(cache=self._cache)
        self._currency = currency
        self._attempts = int(retry_attempts)
        self._backoff = float(retry_backoff_s)
        self._sleep = sleep

    def _ensure_client(self):
        if self._client is not None:
            return self._client
        self._client = _adapter().LiveBackend().live_client()
        return self._client

    def _fetch_entity_record(self, funding_entity_id: str, name_hint: Optional[str] = None) -> dict:
        """Fetch ONE fundingEntity by id via the reliable list query (paged), cache it as Tier-1.
        Returns {ok, row, rid, fetched_at} or a refusal dict. Never fabricates a row."""
        fe_id = str(funding_entity_id)
        try:
            client = self._ensure_client()
        except Exception as e:
            ad = _adapter()
            if isinstance(e, getattr(ad, "NoLiveDataError", ())):
                return {"ok": False, "state": STATE_NO_LIVE_DATA,
                        "reason_code": STATE_NO_LIVE_DATA, "reason": str(e)}
            return {"ok": False, "state": STATE_REFUSED, "reason_code": REASON_LIVE_500,
                    "reason": f"could not build live client: {type(e).__name__}: {str(e)[:160]}"}
        filt = {"searchString": name_hint} if name_hint else {}
        skip = 0
        pages = 0
        row = None
        while True:
            pages += 1
            if pages > 1000:
                break
            variables = {"filter": filt, "skip": skip, "limit": _PORTFOLIO_LIMIT}
            try:
                data, _a, _e = _call_with_retry(
                    client, _PORTFOLIO_QUERY, variables,
                    attempts=self._attempts, backoff_s=self._backoff, sleep=self._sleep,
                    is_empty=lambda d: (d or {}).get("fundingEntities") is None)
            except Exception as e:
                return {"ok": False, "state": STATE_REFUSED, "reason_code": REASON_LIVE_500,
                        "reason": (f"fundingEntities fetch failed after {self._attempts} "
                                   f"attempt(s): {type(e).__name__}: {str(e)[:200]}")}
            page = (data or {}).get("fundingEntities") or {}
            items = page.get("pageItems") or []
            row = next((it for it in items if str((it or {}).get("id")) == fe_id), None)
            if row is not None:
                break
            total = page.get("totalFilteredRecords")
            got = skip + len(items)
            if not items or (total is not None and got >= total) or len(items) < _PORTFOLIO_LIMIT:
                break
            skip += _PORTFOLIO_LIMIT
        if row is None:
            return {"ok": False, "state": STATE_REFUSED, "reason_code": REASON_FETCH_EMPTY,
                    "reason": (f"funding entity {fe_id!r} not found via fundingEntities — "
                               "refusing (never invent)")}
        fetched_at = _now_iso()
        ad = _adapter()
        raw = ad.make_raw_api_response(
            raw_response_id=f"live:fundingEntity:{fe_id}:{fetched_at}",
            endpoint="fundingEntities",
            request_params={"graphql_operation": "HCAFundingEntity", "funding_entity_id": fe_id},
            timestamp=fetched_at, http_status=200, cursor=None, reported_total=None,
            body={"record": row,
                  "provenance": {"fetched_at": fetched_at, "operation": "fundingEntities",
                                 "funding_entity_id": fe_id}},
            backend="live")
        rid = self._cache.put_raw(raw)
        stored = self._cache.get_raw(rid).get("body", {}).get("record", row)
        return {"ok": True, "row": stored, "rid": rid, "fetched_at": fetched_at}

    @staticmethod
    def _reconcile_receivable(receivables: dict, total: float) -> dict:
        """Sum the full InstallmentComponents identity (None -> 0) and compare to total."""
        itemized = {}
        comp_sum = 0.0
        for f in _RECEIVABLE_COMPONENTS:
            v = (receivables or {}).get(f)
            num = float(v) if _is_number(v) else 0.0
            itemized[f] = num
            comp_sum += num
        comp_sum = round(comp_sum, 4)
        diff = round(abs(comp_sum - float(total)), 6)
        return {"ok": diff <= RECONCILE_TOLERANCE, "component_sum": comp_sum,
                "diff": diff, "components": itemized}

    def _refusal_envelope(self, fetched: dict, *, figure: str, funding_entity_id) -> dict:
        meta = {"figure": figure, "funding_entity_id": funding_entity_id}
        if fetched.get("state") == STATE_NO_LIVE_DATA:
            return _envelope(STATE_NO_LIVE_DATA, answer=None, values=[], gate_verdict=None,
                             complete=False,
                             refusals=[{"reason_code": STATE_NO_LIVE_DATA,
                                        "reason": fetched.get("reason")}], meta=meta)
        return _refused(fetched.get("reason_code", REASON_FETCH_EMPTY),
                        fetched.get("reason", "portfolio fetch failed"), meta=meta)

    # === FLAGSHIP: investor's portfolio RECEIVABLE (reconciled) ============
    def portfolio_receivable(self, *, funding_entity_id: str, currency: Optional[str] = None,
                             name_hint: Optional[str] = None, **_ignored) -> dict:
        """The investor's total RECEIVABLE across all loans (reconciled + provenance-bound)."""
        if not funding_entity_id:
            return _refused(REASON_BAD_INPUT,
                            "no funding entity id supplied — cannot compute portfolio receivable")
        fetched = self._fetch_entity_record(str(funding_entity_id), name_hint=name_hint)
        if not fetched.get("ok"):
            return self._refusal_envelope(fetched, figure=self.NAME,
                                          funding_entity_id=funding_entity_id)
        row = fetched["row"]
        rid = fetched["rid"]
        receivables = (row or {}).get("receivables") or {}
        total = receivables.get("total")
        if not _is_number(total):
            return _refused(REASON_FETCH_EMPTY,
                            f"portfolio receivable: non-numeric/absent receivables.total "
                            f"({total!r}) — refusing",
                            meta={"figure": self.NAME, "funding_entity_id": funding_entity_id})
        prov = self._engine.bind_and_verify(
            total, {"raw_response_id": rid, "json_field_path": _PPATH_RECEIVABLE_TOTAL},
            value_ref=f"fundingEntity.{funding_entity_id}.portfolio_receivable")
        if prov["outcome"] != self._provlib.VERIFIED:
            return _refused(REASON_PROVENANCE, prov["reason"],
                            meta={"figure": self.NAME, "funding_entity_id": funding_entity_id,
                                  "reason_code_inner": prov["reason_code"]})
        recon = self._reconcile_receivable(receivables, total)
        if not recon["ok"]:
            return _refused(
                REASON_RECONCILE,
                (f"portfolio receivable components do not reconcile to total within "
                 f"${RECONCILE_TOLERANCE}: sum(components)={recon['component_sum']} vs "
                 f"total={total}"),
                meta={"figure": self.NAME, "funding_entity_id": funding_entity_id,
                      "component_sum": recon["component_sum"], "total": total,
                      "diff": recon["diff"], "reconciles": False})
        conf = self._engine.confidence_record(
            f"fundingEntity.{funding_entity_id}.portfolio_receivable", source_count=1,
            basis="single-source fundingEntity receivable (reconciled)")
        cur = currency or self._currency
        fe_name = (row or {}).get("name")
        out_value = {
            "value": total, "currency": cur, "unit": "currency",
            "provenance": {"raw_response_id": rid, "json_field_path": _PPATH_RECEIVABLE_TOTAL,
                           "operation": "fundingEntities", "field": "receivables.total",
                           "funding_entity_id": str(funding_entity_id),
                           "fetched_at": fetched.get("fetched_at")},
            "confidence": conf["confidence"]}
        answer = (f"Investor {fe_name or funding_entity_id} portfolio receivable (across all "
                  f"loans) is {total}{(' ' + cur) if cur else ''}.")
        gate_verdict = {"outcome": "pass", "reconciliation_ok": True,
                        "reconcile_tolerance": RECONCILE_TOLERANCE,
                        "component_sum": recon["component_sum"], "total": float(total),
                        "diff": recon["diff"], "single_source": conf["single_source"]}
        return _envelope(STATE_DELIVERED, answer=answer, values=[out_value],
                         gate_verdict=gate_verdict, complete=True, refusals=[],
                         meta={"figure": self.NAME, "funding_entity_id": funding_entity_id,
                               "funding_entity_name": fe_name, "currency": cur,
                               "reconciles": True, "components": recon["components"],
                               "confidence_record": conf})

    # === investor PORTFOLIO OUTSTANDING (reconciled AGGREGATE over positions) =====
    def portfolio_outstanding(self, *, funding_entity_id: str, currency: Optional[str] = None,
                              name_hint: Optional[str] = None, **_ignored) -> dict:
        """The investor's total OUTSTANDING across ALL loans = SUM of each LoanFunding position's
        reconciled totalOutstanding. AGGREGATE figure: every contributor is provenance-bound to its
        own Tier-1 record AND reconciles its 5 components; the page set is completeness-checked; the
        sum is bind_aggregate-verified. REFUSE on any unreconciled/unbindable contributor or an
        incomplete fetch (never a partial sum)."""
        if not funding_entity_id:
            return _refused(REASON_BAD_INPUT, "no funding entity id supplied")
        fe_id = str(funding_entity_id)
        meta0 = {"figure": "portfolio_outstanding", "funding_entity_id": fe_id}
        try:
            client = self._ensure_client()
        except Exception as e:
            ad = _adapter()
            if isinstance(e, getattr(ad, "NoLiveDataError", ())):
                return _envelope(STATE_NO_LIVE_DATA, answer=None, values=[], gate_verdict=None,
                                 complete=False,
                                 refusals=[{"reason_code": STATE_NO_LIVE_DATA, "reason": str(e)}],
                                 meta=meta0)
            return _refused(REASON_LIVE_500,
                            f"could not build live client: {type(e).__name__}: {str(e)[:160]}",
                            meta=meta0)
        # fetch ALL positions, paged to completion
        skip = 0
        pages = 0
        positions: list = []
        reported_total = None
        while True:
            pages += 1
            if pages > 1000:
                break
            variables = {"filter": {"fundingEntityId": fe_id}, "skip": skip,
                         "limit": _PORTFOLIO_OUTSTANDING_LIMIT}
            try:
                data, _a, _e = _call_with_retry(
                    client, _PORTFOLIO_OUTSTANDING_QUERY, variables,
                    attempts=self._attempts, backoff_s=self._backoff, sleep=self._sleep,
                    is_empty=lambda d: (d or {}).get("loanFundings") is None)
            except Exception as e:
                return _refused(REASON_LIVE_500,
                                (f"loanFundings(fundingEntityId={fe_id!r}) failed after "
                                 f"{self._attempts} attempt(s): {type(e).__name__}: {str(e)[:200]}"),
                                meta=meta0)
            page = (data or {}).get("loanFundings") or {}
            items = page.get("pageItems") or []
            reported_total = page.get("totalFilteredRecords")
            positions.extend(items)
            got = len(positions)
            if not items or (reported_total is not None and got >= reported_total) \
                    or len(items) < _PORTFOLIO_OUTSTANDING_LIMIT:
                break
            skip += _PORTFOLIO_OUTSTANDING_LIMIT
        if not positions:
            return _refused(REASON_FETCH_EMPTY,
                            f"funding entity {fe_id!r} has no funding positions — refusing", meta=meta0)
        # completeness: never deliver a PARTIAL sum
        if reported_total is not None and len(positions) != reported_total:
            return _refused(REASON_FETCH_EMPTY,
                            (f"incomplete fetch: got {len(positions)} of {reported_total} "
                             "positions — refusing (never a partial sum)"), meta=meta0)
        # cache each position, reconcile each, collect the aggregate bindings + values
        fetched_at = _now_iso()
        ad = _adapter()
        contributing: list = []
        contributing_values: list = []
        total_sum = 0.0
        breakdown: list = []
        fe_name = None
        for pos in positions:
            lf_id = str((pos or {}).get("id"))
            fe = (pos or {}).get("fundingEntity") or {}
            fe_name = fe_name or fe.get("name")
            summ = (((pos or {}).get("repaymentSchedule") or {}).get("summary") or {})
            outstanding = summ.get("totalOutstanding") or {}
            t = outstanding.get("total")
            if not _is_number(t):
                return _refused(REASON_FETCH_EMPTY,
                                f"position {lf_id} has non-numeric outstanding total ({t!r}) — refusing",
                                meta={**meta0, "loan_funding_id": lf_id})
            recon = FundingFigure._reconcile_outstanding(outstanding, t)
            if not recon["ok"]:
                return _refused(REASON_RECONCILE,
                                (f"position {lf_id} outstanding components do not reconcile "
                                 f"(sum={recon['component_sum']} vs total={t})"),
                                meta={**meta0, "loan_funding_id": lf_id})
            raw = ad.make_raw_api_response(
                raw_response_id=f"live:fundingOutstanding:{fe_id}:{lf_id}:{fetched_at}",
                endpoint="loanFundings",
                request_params={"graphql_operation": "HCAPortfolioOutstanding",
                                "funding_entity_id": fe_id, "loan_funding_id": lf_id},
                timestamp=fetched_at, http_status=200, cursor=None, reported_total=None,
                body={"record": pos,
                      "provenance": {"fetched_at": fetched_at, "operation": "loanFundings",
                                     "funding_entity_id": fe_id, "loan_funding_id": lf_id}},
                backend="live")
            rid = self._cache.put_raw(raw)
            contributing.append({"raw_response_id": rid, "json_field_path": _PATH_OUTSTANDING_TOTAL})
            contributing_values.append(float(t))
            total_sum += float(t)
            breakdown.append({"loan_funding_id": lf_id,
                              "loan": (pos.get("asset") or {}).get("name"), "outstanding": float(t)})
        total_sum = round(total_sum, 2)
        agg = self._engine.bind_aggregate(
            total_sum, contributing, value_ref=f"fundingEntity.{fe_id}.portfolio_outstanding",
            contributing_values=contributing_values)
        if agg["outcome"] != self._provlib.VERIFIED:
            return _refused(REASON_PROVENANCE, agg.get("reason", "aggregate binding failed"),
                            meta={**meta0, "reason_code_inner": agg.get("reason_code")})
        conf = self._engine.confidence_record(
            f"fundingEntity.{fe_id}.portfolio_outstanding", source_count=len(contributing),
            basis=f"reconciled aggregate over {len(contributing)} funding positions")
        cur = currency or self._currency
        out_value = {
            "value": total_sum, "currency": cur, "unit": "currency",
            "provenance": {"aggregate": True, "operation": "loanFundings",
                           "contributing": contributing, "funding_entity_id": fe_id,
                           "fetched_at": fetched_at},
            "confidence": conf["confidence"]}
        answer = (f"Investor {fe_name or fe_id} total outstanding across {len(contributing)} "
                  f"loans is {total_sum}{(' ' + cur) if cur else ''}.")
        gate_verdict = {"outcome": "pass", "reconciliation_ok": True, "aggregate": True,
                        "contributors": len(contributing), "completeness_ok": True,
                        "single_source": conf["single_source"]}
        return _envelope(STATE_DELIVERED, answer=answer, values=[out_value],
                         gate_verdict=gate_verdict, complete=True, refusals=[],
                         meta={**meta0, "funding_entity_name": fe_name, "currency": cur,
                               "positions": len(contributing), "reported_total": reported_total,
                               "breakdown": breakdown, "confidence_record": conf})

    # === LIGHTER portfolio scalars (single-source, no reconciliation) ======
    def _light(self, *, figure: str, value_path: str, field_name: str, unit: str,
               funding_entity_id: str, currency: Optional[str], name_hint: Optional[str]) -> dict:
        if not funding_entity_id:
            return _refused(REASON_BAD_INPUT, "no funding entity id supplied")
        fetched = self._fetch_entity_record(str(funding_entity_id), name_hint=name_hint)
        if not fetched.get("ok"):
            return self._refusal_envelope(fetched, figure=figure,
                                          funding_entity_id=funding_entity_id)
        row = fetched["row"]
        rid = fetched["rid"]
        value = (row or {}).get(field_name)
        if not _is_number(value):
            return _refused(REASON_FETCH_EMPTY,
                            f"{figure}: non-numeric/absent {field_name!r} ({value!r}) — refusing",
                            meta={"figure": figure, "funding_entity_id": funding_entity_id})
        prov = self._engine.bind_and_verify(
            value, {"raw_response_id": rid, "json_field_path": value_path},
            value_ref=f"fundingEntity.{funding_entity_id}.{figure}")
        if prov["outcome"] != self._provlib.VERIFIED:
            return _refused(REASON_PROVENANCE, prov["reason"],
                            meta={"figure": figure, "funding_entity_id": funding_entity_id,
                                  "reason_code_inner": prov["reason_code"]})
        conf = self._engine.confidence_record(
            f"fundingEntity.{funding_entity_id}.{figure}", source_count=1,
            basis=f"single-source fundingEntity read ({field_name})")
        cur = currency or self._currency
        fe_name = (row or {}).get("name")
        out_value = {
            "value": value, "currency": cur if unit == "currency" else None, "unit": unit,
            "provenance": {"raw_response_id": rid, "json_field_path": value_path,
                           "operation": "fundingEntities", "field": field_name,
                           "funding_entity_id": str(funding_entity_id),
                           "fetched_at": fetched.get("fetched_at")},
            "confidence": conf["confidence"]}
        cur_str = f" {cur}" if (cur and unit == "currency") else ""
        answer = f"{figure} for investor {fe_name or funding_entity_id} is {value}{cur_str}."
        gate_verdict = {"outcome": "pass", "single_source": conf["single_source"],
                        "reconciliation_ok": None}
        return _envelope(STATE_DELIVERED, answer=answer, values=[out_value],
                         gate_verdict=gate_verdict, complete=True, refusals=[],
                         meta={"figure": figure, "funding_entity_id": funding_entity_id,
                               "funding_entity_name": fe_name, "currency": cur, "unit": unit,
                               "confidence_record": conf})

    def portfolio_commitment(self, *, funding_entity_id, currency=None, name_hint=None, **_ig):
        return self._light(figure="portfolio_commitment", value_path=_PPATH_COMMITMENT,
                           field_name="totalCommitment", unit="currency",
                           funding_entity_id=funding_entity_id, currency=currency,
                           name_hint=name_hint)

    def portfolio_disbursement(self, *, funding_entity_id, currency=None, name_hint=None, **_ig):
        return self._light(figure="portfolio_disbursement", value_path=_PPATH_DISBURSEMENT,
                           field_name="totalDisbursement", unit="currency",
                           funding_entity_id=funding_entity_id, currency=currency,
                           name_hint=name_hint)

    def portfolio_contributed(self, *, funding_entity_id, currency=None, name_hint=None, **_ig):
        return self._light(figure="portfolio_contributed", value_path=_PPATH_CONTRIBUTED,
                           field_name="contributed", unit="currency",
                           funding_entity_id=funding_entity_id, currency=currency,
                           name_hint=name_hint)

    def portfolio_active_loans(self, *, funding_entity_id, currency=None, name_hint=None, **_ig):
        return self._light(figure="portfolio_active_loans", value_path=_PPATH_ACTIVE_LOANS,
                           field_name="activeLoansCount", unit="count",
                           funding_entity_id=funding_entity_id, currency=currency,
                           name_hint=name_hint)

    def registry(self) -> dict:
        return {
            "portfolio_receivable": self.portfolio_receivable,
            "portfolio_outstanding": self.portfolio_outstanding,
            "portfolio_commitment": self.portfolio_commitment,
            "portfolio_disbursement": self.portfolio_disbursement,
            "portfolio_contributed": self.portfolio_contributed,
            "portfolio_active_loans": self.portfolio_active_loans,
        }


PORTFOLIO_FIGURE_NAMES = (
    "portfolio_receivable", "portfolio_outstanding", "portfolio_commitment",
    "portfolio_disbursement", "portfolio_contributed", "portfolio_active_loans",
)


def run_portfolio_figure(figure: str, *, funding_entity_id: str, client=None, cache=None,
                         engine=None, currency: Optional[str] = None,
                         name_hint: Optional[str] = None,
                         sleep: Callable[[float], None] = time.sleep, **kwargs) -> dict:
    """Run a single named portfolio (fundingEntity-level) figure by funding_entity_id."""
    fig = FundingPortfolioFigure(client=client, cache=cache, engine=engine, currency=currency,
                                 sleep=sleep)
    reg = fig.registry()
    fn = reg.get(figure)
    if fn is None:
        return _refused(REASON_BAD_INPUT,
                        f"unknown portfolio figure {figure!r} (known: {list(reg)})",
                        meta={"funding_entity_id": funding_entity_id})
    return fn(funding_entity_id=funding_entity_id, currency=currency, name_hint=name_hint,
              **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run an investor/funding figure for a (loan, funding entity) pair.")
    parser.add_argument("--figure", default="funding_outstanding",
                        help=f"one of: {', '.join(FUNDING_FIGURE_NAMES)}")
    parser.add_argument("--loan-id", required=False, help="the loan (asset) id")
    parser.add_argument("--funding-entity-id", required=False, help="the investor / funding entity id")
    parser.add_argument("--currency", default=None)
    parser.add_argument("--loan-name", default=None)
    args = parser.parse_args()
    if not args.loan_id or not args.funding_entity_id:
        # No-network smoke surface: print the figure names + their Tier-1 binding paths.
        print(json.dumps({
            "module": "hca-funding",
            "figure_names": list(FUNDING_FIGURE_NAMES),
            "outstanding_components": list(_OUTSTANDING_COMPONENTS),
            "tier1_paths": {
                "funding_outstanding": _PATH_OUTSTANDING_TOTAL,
                "funding_commitment": _PATH_COMMITMENT,
                "funding_participation": _PATH_PARTICIPATION,
                "funding_receivable": _PATH_RECEIVABLE_TOTAL,
            },
            "reconcile_tolerance": RECONCILE_TOLERANCE,
        }, indent=2))
        raise SystemExit(0)
    env = run_funding_figure(args.figure, loan_id=args.loan_id,
                             funding_entity_id=args.funding_entity_id,
                             currency=args.currency, loan_name=args.loan_name)
    print(json.dumps(env, indent=2, default=str))
