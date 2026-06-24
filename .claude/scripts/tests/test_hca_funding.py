#!/usr/bin/env python3
"""test_hca_funding.py — stdlib unittest for the INVESTOR/FUNDING figures (hca-funding.py).

Proves on FIXTURES (no network, no creds) — via a fake GraphQL client that serves the RELIABLE
2-step LoanFundings path — that the funding figures honor the SAME trust guarantees as the
payoff figure:

  HAPPY PATH (funding_outstanding)
    - delivers a DELIVERED envelope whose totalOutstanding.total is BOUND to a cached Tier-1
      record (the binder re-walks $.body.record.repaymentSchedule.summary.totalOutstanding.total
      and gets the same number) and whose 5 components RECONCILE to the total within $0.01;
      itemized components + participationPercentage + commitmentAmount appear in the meta.
    - uses the EXACT 2-step path: STEP 1 loanFundings(filter:{assetId}) -> pick the pageItem
      whose fundingEntity.id matches -> loanFundingId; STEP 2 loanFundings(filter:{loanFundingId}).

  REFUSAL (REQUIRED — fail = REJECT)
    - a NON-reconciling summary (components don't sum to total) -> REFUSED (RECONCILE_FAILED),
      never a number.
    - an investor NOT funding the loan (no fundingEntity match in STEP 1) -> REFUSED
      (NOT_FUNDING), never a number.

  PROVENANCE
    - re-walking the bound json_field_path resolves to the SAME value (no fabrication).

  LIGHTER FIGURES (single-source, confidence <= 0.7, no reconciliation)
    - funding_commitment / funding_participation / funding_receivable each deliver, bound to
      their own Tier-1 field path on the same record, with single-source confidence cap.

Fixture values are the LIVE-VERIFIED XL/Beehive numbers so the reconciliation is realistic:
  loan 134, fundingEntity id "3" (XL), loanFundingId "lf-xl-134":
    totalOutstanding.total 6,922,294.60 = principal 6,000,000 + interest 303,289.29
      + compoundingInterest 0 + totalFees 46,288.47 + totalPenalties 572,716.84.

Run:
  python3 .claude/scripts/tests/test_hca_funding.py
  python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py' -v
"""

import importlib.util
import os
import shutil
import sys
import tempfile
import unittest


_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.abspath(os.path.join(_THIS_DIR, os.pardir))


def _load(modname, filename):
    cached = sys.modules.get(modname)
    if cached is not None:
        return cached
    path = os.path.join(_SCRIPTS_DIR, filename)
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


cache_mod = _load("hca_cache", "hca-cache.py")
prov_mod = _load("hca_provenance", "hca-provenance.py")
funding_mod = _load("hca_funding", "hca-funding.py")


# ---------------------------------------------------------------------------
# Live-verified XL-on-Beehive ground truth (loan 134, fundingEntity "3" = XL)
# ---------------------------------------------------------------------------

# STEP-2 funding record for the XL stake — reconciles to the cent.
_XL_OUTSTANDING = {
    "total": 6922294.60,
    "principal": 6000000.0,
    "interest": 303289.29,
    "compoundingInterest": 0.0,
    "totalFees": 46288.47,
    "totalPenalties": 572716.84,
}

_XL_RECORD = {
    "id": "lf-xl-134",
    "fundingEntity": {"id": "3", "name": "XL"},
    "participationPercentage": 75.0,
    "commitmentAmount": 6000000.0,
    "receivables": {"total": 922294.60, "principal": 350000.0, "interest": 303289.29},
    "repaymentSchedule": {
        "summary": {
            "totalOutstanding": dict(_XL_OUTSTANDING),
            "outstandingPrincipalBeforeAmortization": 6000000.0,
            "totalDisbursed": 6000000.0,
        }
    },
}

# A second funder on the same loan, to prove STEP-1 picks the RIGHT pageItem by fundingEntity.id.
_OTHER_RECORD = {
    "id": "lf-other-134",
    "fundingEntity": {"id": "9", "name": "Other Capital"},
    "participationPercentage": 25.0,
    "commitmentAmount": 2000000.0,
    "receivables": {"total": 111111.11, "principal": 90000.0, "interest": 21111.11},
    "repaymentSchedule": {
        "summary": {
            "totalOutstanding": {"total": 2307431.53, "principal": 2000000.0,
                                 "interest": 101096.43, "compoundingInterest": 0.0,
                                 "totalFees": 15429.49, "totalPenalties": 190905.61},
            "outstandingPrincipalBeforeAmortization": 2000000.0,
            "totalDisbursed": 2000000.0,
        }
    },
}

# A NON-reconciling XL record: total inflated, components unchanged (fabrication simulation).
_XL_NON_RECONCILING = {
    **_XL_RECORD,
    "repaymentSchedule": {
        "summary": {
            "totalOutstanding": {**_XL_OUTSTANDING, "total": 99999999.99},
            "outstandingPrincipalBeforeAmortization": 6000000.0,
            "totalDisbursed": 6000000.0,
        }
    },
}


class _FakeFundingClient:
    """Fake LiveGraphQLClient serving the reliable 2-step LoanFundings path.

    STEP 1 — loanFundings(filter:{assetId}) -> a page of {id, fundingEntity{id,name}} stubs
             built from `records` (the full STEP-2 records; STEP 1 only exposes id+fundingEntity).
    STEP 2 — loanFundings(filter:{loanFundingId}) -> the one full record whose id matches.

    Can simulate a configurable number of leading HTTP-500 failures before succeeding (to
    exercise the bounded retry-on-500). Records the variables it was called with.
    """

    def __init__(self, records, *, fail_times=0):
        self.records = list(records)
        self.fail_times = fail_times
        self.calls = []
        self._attempt = 0

    def raw_query(self, query, variables=None):
        self._attempt += 1
        self.calls.append((query, variables))
        if self._attempt <= self.fail_times:
            raise RuntimeError("GraphQL HTTP 500 Internal Server Error")
        filt = (variables or {}).get("filter") or {}
        if "loanFundingId" in filt:
            lf_id = str(filt["loanFundingId"])
            items = [dict(r) for r in self.records if str(r.get("id")) == lf_id]
            return {"loanFundings": {"totalFilteredRecords": len(items),
                                     "pageItems": items}}
        if "assetId" in filt:
            stubs = [{"id": r.get("id"),
                      "fundingEntity": dict(r.get("fundingEntity") or {})}
                     for r in self.records]
            return {"loanFundings": {"totalFilteredRecords": len(stubs),
                                     "pageItems": stubs}}
        return {"loanFundings": {"totalFilteredRecords": 0, "pageItems": []}}


def _no_sleep(_):
    return None


class _FundingBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hca-funding-test-")
        self.cache = cache_mod.TwoTierCache(cache_dir=self.tmp)
        self.engine = prov_mod.ProvenanceEngine(cache=self.cache)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _figure(self, client):
        return funding_mod.FundingFigure(client=client, cache=self.cache, engine=self.engine,
                                         sleep=_no_sleep)


class FundingOutstandingHappyPathTest(_FundingBase):
    def test_delivers_with_bound_total_and_reconciles(self):
        client = _FakeFundingClient([_XL_RECORD, _OTHER_RECORD])
        env = self._figure(client).funding_outstanding(
            loan_id="134", funding_entity_id="3", currency="USD", loan_name="Beehive Waldorff")
        self.assertEqual(env["state"], funding_mod.STATE_DELIVERED, env.get("refusals"))
        v = env["values"][0]
        self.assertEqual(v["value"], 6922294.60)
        self.assertEqual(v["currency"], "USD")
        # provenance is RESOLVABLE: re-walk the cited Tier-1 path -> same value.
        rid = v["provenance"]["raw_response_id"]
        path = v["provenance"]["json_field_path"]
        self.assertEqual(path,
                         "$.body.record.repaymentSchedule.summary.totalOutstanding.total")
        resolved, ok = self.cache.resolve_binding({"raw_response_id": rid,
                                                    "json_field_path": path})
        self.assertTrue(ok)
        self.assertEqual(resolved, 6922294.60)
        # reconciliation passed; meta itemizes the 5 components + echoes participation/commitment.
        self.assertTrue(env["meta"]["reconciles"])
        self.assertTrue(env["gate_verdict"]["reconciliation_ok"])
        comps = env["meta"]["components"]
        self.assertEqual(comps["principal"], 6000000.0)
        self.assertEqual(comps["interest"], 303289.29)
        self.assertEqual(comps["totalFees"], 46288.47)
        self.assertEqual(comps["totalPenalties"], 572716.84)
        self.assertEqual(comps["compoundingInterest"], 0.0)
        self.assertEqual(env["meta"]["participationPercentage"], 75.0)
        self.assertEqual(env["meta"]["commitmentAmount"], 6000000.0)
        self.assertEqual(env["meta"]["funding_entity_name"], "XL")
        self.assertEqual(env["meta"]["loan_funding_id"], "lf-xl-134")

    def test_uses_two_step_path_picks_right_funding(self):
        client = _FakeFundingClient([_XL_RECORD, _OTHER_RECORD])
        self._figure(client).funding_outstanding(loan_id="134", funding_entity_id="3")
        # STEP 1 by assetId, then STEP 2 by the RESOLVED loanFundingId (XL's, not Other's).
        step1 = client.calls[0][1]["filter"]
        self.assertEqual(step1, {"assetId": "134"})
        step2 = client.calls[-1][1]["filter"]
        self.assertEqual(step2, {"loanFundingId": "lf-xl-134"})

    def test_single_source_confidence_capped_and_flagged(self):
        client = _FakeFundingClient([_XL_RECORD, _OTHER_RECORD])
        env = self._figure(client).funding_outstanding(loan_id="134", funding_entity_id="3")
        conf = env["values"][0]["confidence"]
        self.assertLessEqual(conf, 0.7)  # single-source cap
        self.assertTrue(env["meta"]["confidence_record"]["single_source"])


class FundingReconcileRefusalTest(_FundingBase):
    def test_non_reconciling_summary_refuses_no_number(self):
        client = _FakeFundingClient([_XL_NON_RECONCILING, _OTHER_RECORD])
        env = self._figure(client).funding_outstanding(loan_id="134", funding_entity_id="3")
        self.assertEqual(env["state"], funding_mod.STATE_REFUSED)
        self.assertEqual(env["values"], [])  # NEVER a number on a refusal
        codes = {r["reason_code"] for r in env["refusals"]}
        self.assertIn(funding_mod.REASON_RECONCILE, codes)


class FundingNotInvestingRefusalTest(_FundingBase):
    def test_investor_not_funding_loan_refuses(self):
        # fundingEntity "3" (XL) is NOT among the loan's fundings -> NOT_FUNDING refusal.
        client = _FakeFundingClient([_OTHER_RECORD])
        env = self._figure(client).funding_outstanding(loan_id="134", funding_entity_id="3")
        self.assertEqual(env["state"], funding_mod.STATE_REFUSED)
        self.assertEqual(env["values"], [])
        codes = {r["reason_code"] for r in env["refusals"]}
        self.assertIn(funding_mod.REASON_NOT_FUNDING, codes)
        # STEP 2 was never reached (only the STEP-1 assetId query ran).
        self.assertEqual(len(client.calls), 1)
        self.assertEqual(client.calls[0][1]["filter"], {"assetId": "134"})


class FundingBadInputTest(_FundingBase):
    def test_missing_loan_id_refuses(self):
        client = _FakeFundingClient([_XL_RECORD])
        env = self._figure(client).funding_outstanding(loan_id="", funding_entity_id="3")
        self.assertEqual(env["state"], funding_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], funding_mod.REASON_BAD_INPUT)

    def test_missing_funding_entity_id_refuses(self):
        client = _FakeFundingClient([_XL_RECORD])
        env = self._figure(client).funding_outstanding(loan_id="134", funding_entity_id="")
        self.assertEqual(env["state"], funding_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], funding_mod.REASON_BAD_INPUT)


class FundingRetryTest(_FundingBase):
    def test_retry_on_500_then_success_delivers(self):
        # fail once (HTTP 500) on the first (STEP-1) call, then succeed -> still delivers.
        client = _FakeFundingClient([_XL_RECORD, _OTHER_RECORD], fail_times=1)
        env = self._figure(client).funding_outstanding(loan_id="134", funding_entity_id="3")
        self.assertEqual(env["state"], funding_mod.STATE_DELIVERED, env.get("refusals"))
        self.assertEqual(env["values"][0]["value"], 6922294.60)


class FundingLightFiguresTest(_FundingBase):
    def test_commitment_delivers_single_source_bound(self):
        client = _FakeFundingClient([_XL_RECORD, _OTHER_RECORD])
        env = self._figure(client).funding_commitment(loan_id="134", funding_entity_id="3")
        self.assertEqual(env["state"], funding_mod.STATE_DELIVERED, env.get("refusals"))
        v = env["values"][0]
        self.assertEqual(v["value"], 6000000.0)
        self.assertLessEqual(v["confidence"], 0.7)
        # no reconciliation on a single-source figure
        self.assertIsNone(env["gate_verdict"]["reconciliation_ok"])
        # provenance re-resolves to the same value at the commitment path
        self.assertEqual(v["provenance"]["json_field_path"], "$.body.record.commitmentAmount")
        resolved, ok = self.cache.resolve_binding(
            {"raw_response_id": v["provenance"]["raw_response_id"],
             "json_field_path": v["provenance"]["json_field_path"]})
        self.assertTrue(ok)
        self.assertEqual(resolved, 6000000.0)

    def test_participation_delivers_single_source_bound(self):
        client = _FakeFundingClient([_XL_RECORD, _OTHER_RECORD])
        env = self._figure(client).funding_participation(loan_id="134", funding_entity_id="3")
        self.assertEqual(env["state"], funding_mod.STATE_DELIVERED, env.get("refusals"))
        v = env["values"][0]
        self.assertEqual(v["value"], 75.0)
        self.assertEqual(v["unit"], "percent")
        self.assertLessEqual(v["confidence"], 0.7)
        self.assertEqual(v["provenance"]["json_field_path"],
                         "$.body.record.participationPercentage")
        resolved, ok = self.cache.resolve_binding(
            {"raw_response_id": v["provenance"]["raw_response_id"],
             "json_field_path": v["provenance"]["json_field_path"]})
        self.assertTrue(ok)
        self.assertEqual(resolved, 75.0)

    def test_receivable_delivers_single_source_bound(self):
        client = _FakeFundingClient([_XL_RECORD, _OTHER_RECORD])
        env = self._figure(client).funding_receivable(loan_id="134", funding_entity_id="3")
        self.assertEqual(env["state"], funding_mod.STATE_DELIVERED, env.get("refusals"))
        v = env["values"][0]
        self.assertEqual(v["value"], 922294.60)
        self.assertLessEqual(v["confidence"], 0.7)
        self.assertEqual(v["provenance"]["json_field_path"], "$.body.record.receivables.total")
        resolved, ok = self.cache.resolve_binding(
            {"raw_response_id": v["provenance"]["raw_response_id"],
             "json_field_path": v["provenance"]["json_field_path"]})
        self.assertTrue(ok)
        self.assertEqual(resolved, 922294.60)


class FundingRegistryTest(_FundingBase):
    def test_registry_maps_all_figure_names(self):
        client = _FakeFundingClient([_XL_RECORD])
        reg = self._figure(client).registry()
        self.assertEqual(set(reg), set(funding_mod.FUNDING_FIGURE_NAMES))
        for name in funding_mod.FUNDING_FIGURE_NAMES:
            self.assertTrue(callable(reg[name]))

    def test_run_funding_figure_convenience_delivers(self):
        client = _FakeFundingClient([_XL_RECORD, _OTHER_RECORD])
        env = funding_mod.run_funding_figure(
            "funding_outstanding", loan_id="134", funding_entity_id="3",
            client=client, cache=self.cache, engine=self.engine, sleep=_no_sleep)
        self.assertEqual(env["state"], funding_mod.STATE_DELIVERED, env.get("refusals"))
        self.assertEqual(env["values"][0]["value"], 6922294.60)

    def test_run_funding_figure_unknown_name_refuses(self):
        client = _FakeFundingClient([_XL_RECORD])
        env = funding_mod.run_funding_figure(
            "funding_bogus", loan_id="134", funding_entity_id="3",
            client=client, cache=self.cache, engine=self.engine, sleep=_no_sleep)
        self.assertEqual(env["state"], funding_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], funding_mod.REASON_BAD_INPUT)

    def test_run_funding_figure_synonym_routes_to_outstanding(self):
        client = _FakeFundingClient([_XL_RECORD, _OTHER_RECORD])
        env = funding_mod.run_funding_figure(
            "investor outstanding", loan_id="134", funding_entity_id="3",
            client=client, cache=self.cache, engine=self.engine, sleep=_no_sleep)
        self.assertEqual(env["state"], funding_mod.STATE_DELIVERED, env.get("refusals"))
        self.assertEqual(env["values"][0]["value"], 6922294.60)


if __name__ == "__main__":
    unittest.main(verbosity=2)
