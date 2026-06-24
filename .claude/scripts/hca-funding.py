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
    "receivables { total principal interest } "
    "repaymentSchedule { summary { "
    "totalOutstanding { total principal interest compoundingInterest totalFees totalPenalties } "
    "outstandingPrincipalBeforeAmortization totalDisbursed } } } "
    "} }"
)
_STEP2_LIMIT = 5

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
_PATH_COMMITMENT = "$.body.record.commitmentAmount"
_PATH_PARTICIPATION = "$.body.record.participationPercentage"
_PATH_RECEIVABLE_TOTAL = "$.body.record.receivables.total"


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
    def _fetch_funding_record(self, loan_id: str, funding_entity_id: str) -> dict:
        """Run the reliable 2-step path and CACHE the picked STEP-2 record as Tier-1.

        Returns one of:
          {"ok": True, "row": <step2 pageItem>, "rid": <tier1 id>, "fetched_at": ...}
          {"ok": False, "state": ..., "reason_code": ..., "reason": ...}

        Never fabricates: a missing investor (STEP-1 no match) -> NOT_FUNDING refusal; a flaky
        500 surviving the retry budget -> LIVE_500 refusal; an empty/incomplete STEP-2 payload
        -> FETCH_EMPTY refusal.
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
                client, _STEP2_QUERY, step2_vars,
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

    # --- registry: figure name -> callable ---------------------------------
    def registry(self) -> dict:
        """Map of funding-figure name -> bound callable(loan_id, funding_entity_id, ...)."""
        return {
            "funding_outstanding": self.funding_outstanding,
            "funding_commitment": self.funding_commitment,
            "funding_participation": self.funding_participation,
            "funding_receivable": self.funding_receivable,
        }


_ABSENT = object()


# Canonical figure-name list (single source of truth for callers/tests).
FUNDING_FIGURE_NAMES = (
    "funding_outstanding",
    "funding_commitment",
    "funding_participation",
    "funding_receivable",
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
