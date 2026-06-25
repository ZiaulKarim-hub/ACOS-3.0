#!/usr/bin/env python3
"""test_hca_per_diem.py — stdlib unittest for the PER-DIEM INTEREST funding figure.

Proves on FIXTURES (no network, no creds) that `per_diem_interest` honors the skill's trust
contract:

  COMPUTE (live-pinned, XL on Lux II — loanFunding 338, asset 171, fundingEntity "3"):
    outstanding principal 2,646,609.230893428 ; currentInterestRate 14 (a PERCENT, not 0.14).
    Actual/360 -> 2,646,609.23 × 14% ÷ 360 = 1,029.236923/day  (the user-confirmed answer)
    Actual/365 -> 1,015.137787/day

  PERCENT SCALE (the 100× landmine): the value uses rate/100. A value computed from the bare
    integer 14 (treating it as a fraction) would be 100× too large — explicitly excluded.

  BASIS: interest accrues on outstanding PRINCIPAL, never totalOutstanding.total (which is net of
    fee/credit components).

  PROVENANCE: BOTH inputs (principal + rate) re-resolve from their cited Tier-1 paths on the SAME
    cached LoanFunding record — the per-diem is derived, transparent, never cached.

  DAY-COUNT: Hypercore exposes no day-count field, so the convention is ASSUMED + STATED
    (day_count_assumed True, default Actual/360, parameterizable to 365).

  REFUSAL DISCIPLINE (fail = REJECT): absent/non-numeric principal or rate, a non-positive rate,
    a bad day_count, and a non-funding investor each REFUSE — never a fabricated per-diem.

  DISPATCH + ROUTING: run_funding_figure("per_diem_interest", ...) reaches the method; the smart
    orchestrator routes "per diem interest for XL for Lux II loan" to the figure with the per-diem
    terms stripped from entity resolution.

Run:
  python3 .claude/scripts/tests/test_hca_per_diem.py
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
ask_mod = _load("hca_ask", "hca-ask.py")


# ---------------------------------------------------------------------------
# Live-pinned XL-on-Lux-II ground truth (loanFunding 338, asset 171, fundingEntity "3" = XL)
# ---------------------------------------------------------------------------

_PRINCIPAL = 2646609.230893428
_RATE_PERCENT = 14                      # the field returns the INTEGER 14 (== 14%), not 0.14
_PD_360 = round(_PRINCIPAL * (_RATE_PERCENT / 100.0) / 360, 6)   # 1029.236923
_PD_365 = round(_PRINCIPAL * (_RATE_PERCENT / 100.0) / 365, 6)   # 1015.137787


def _xl_record(*, rate=_RATE_PERCENT, principal=_PRINCIPAL):
    """A STEP-2 LoanFunding record for the XL stake, shaped like the live HCAFundingByLfId query
    (now carrying currentInterestRate). `total` is the live NET total — deliberately != principal,
    to prove the per-diem uses PRINCIPAL, not total."""
    rec = {
        "id": "lf-xl-171",
        "fundingEntity": {"id": "3", "name": "XL"},
        "participationPercentage": 100.0,
        "commitmentAmount": 4410807.05,
        "currentInterestRate": rate,
        "receivables": {"total": 0.0, "principal": 0.0, "interest": 0.0},
        "repaymentSchedule": {
            "summary": {
                "totalOutstanding": {
                    "total": 881704.8190127312,            # NET (≠ principal) on purpose
                    "principal": principal,
                    "interest": 0.0, "compoundingInterest": 0.0,
                    "totalFees": 0.0, "totalPenalties": 0.0,
                },
                "outstandingPrincipalBeforeAmortization": principal,
                "totalDisbursed": principal,
            }
        },
    }
    if rate is _ABSENT:
        del rec["currentInterestRate"]
    return rec


_ABSENT = object()


class _FakeFundingClient:
    """Fake LiveGraphQLClient serving the reliable 2-step LoanFundings path (STEP 1 by assetId ->
    id+fundingEntity stubs; STEP 2 by loanFundingId -> full record)."""

    def __init__(self, records):
        self.records = list(records)
        self.calls = []

    def raw_query(self, query, variables=None):
        self.calls.append((query, variables))
        filt = (variables or {}).get("filter") or {}
        if "loanFundingId" in filt:
            lf_id = str(filt["loanFundingId"])
            items = [dict(r) for r in self.records if str(r.get("id")) == lf_id]
            return {"loanFundings": {"totalFilteredRecords": len(items), "pageItems": items}}
        if "assetId" in filt:
            stubs = [{"id": r.get("id"), "fundingEntity": dict(r.get("fundingEntity") or {})}
                     for r in self.records]
            return {"loanFundings": {"totalFilteredRecords": len(stubs), "pageItems": stubs}}
        return {"loanFundings": {"totalFilteredRecords": 0, "pageItems": []}}


def _no_sleep(_):
    return None


class _PerDiemBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hca-perdiem-test-")
        self.cache = cache_mod.TwoTierCache(cache_dir=self.tmp)
        self.engine = prov_mod.ProvenanceEngine(cache=self.cache)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _figure(self, client):
        return funding_mod.FundingFigure(client=client, cache=self.cache, engine=self.engine,
                                         sleep=_no_sleep)


class PerDiemHappyPathTest(_PerDiemBase):
    def test_delivers_actual_360_with_correct_value(self):
        client = _FakeFundingClient([_xl_record()])
        env = self._figure(client).per_diem_interest(
            loan_id="171", funding_entity_id="3", currency="USD", loan_name="Lux II")
        self.assertEqual(env["state"], funding_mod.STATE_DELIVERED, env.get("refusals"))
        v = env["values"][0]
        self.assertEqual(v["value"], _PD_360)
        self.assertEqual(round(v["value"], 2), 1029.24)         # the user-confirmed answer
        self.assertEqual(v["currency"], "USD")
        self.assertEqual(v["unit"], "currency_per_day")
        self.assertEqual(env["meta"]["day_count_convention"], "Actual/360")
        self.assertTrue(env["meta"]["day_count_assumed"])
        self.assertEqual(env["meta"]["outstanding_principal"], _PRINCIPAL)
        self.assertEqual(env["meta"]["current_interest_rate_percent"], 14.0)
        self.assertTrue(env["gate_verdict"]["day_count_assumed"])
        self.assertIn("ASSUMED", env["answer"])

    def test_rate_is_treated_as_percent_not_fraction(self):
        # The 100× landmine: value must be principal*0.14/360, NOT principal*14/360.
        client = _FakeFundingClient([_xl_record()])
        env = self._figure(client).per_diem_interest(loan_id="171", funding_entity_id="3")
        value = env["values"][0]["value"]
        self.assertAlmostEqual(value, _PRINCIPAL * 0.14 / 360, places=4)
        self.assertNotAlmostEqual(value, _PRINCIPAL * 14.0 / 360, places=2)

    def test_basis_is_principal_not_net_total(self):
        # total (881,704.82) != principal (2,646,609.23); the per-diem must use principal.
        client = _FakeFundingClient([_xl_record()])
        env = self._figure(client).per_diem_interest(loan_id="171", funding_entity_id="3")
        value = env["values"][0]["value"]
        self.assertAlmostEqual(value, _PRINCIPAL * 0.14 / 360, places=6)
        self.assertNotAlmostEqual(value, 881704.8190127312 * 0.14 / 360, places=2)

    def test_both_inputs_are_provenance_resolvable(self):
        client = _FakeFundingClient([_xl_record()])
        env = self._figure(client).per_diem_interest(loan_id="171", funding_entity_id="3")
        prov = env["values"][0]["provenance"]
        self.assertTrue(prov["derived"])
        ins = prov["inputs"]
        # re-walk each cited Tier-1 path -> the same input value (no fabrication).
        p = ins["outstanding_principal"]
        r = ins["currentInterestRate"]
        pv, ok_p = self.cache.resolve_binding(
            {"raw_response_id": p["raw_response_id"], "json_field_path": p["json_field_path"]})
        rv, ok_r = self.cache.resolve_binding(
            {"raw_response_id": r["raw_response_id"], "json_field_path": r["json_field_path"]})
        self.assertTrue(ok_p and ok_r)
        self.assertEqual(pv, _PRINCIPAL)
        self.assertEqual(rv, _RATE_PERCENT)
        self.assertEqual(r["scale"], "percent")
        self.assertEqual(p["json_field_path"],
                         "$.body.record.repaymentSchedule.summary.totalOutstanding.principal")
        self.assertEqual(r["json_field_path"], "$.body.record.currentInterestRate")

    def test_actual_365_parameterization(self):
        client = _FakeFundingClient([_xl_record()])
        env = self._figure(client).per_diem_interest(
            loan_id="171", funding_entity_id="3", day_count=365)
        self.assertEqual(env["state"], funding_mod.STATE_DELIVERED)
        self.assertEqual(env["values"][0]["value"], _PD_365)
        self.assertEqual(env["meta"]["day_count_convention"], "Actual/365")
        self.assertEqual(env["values"][0]["provenance"]["day_count"], 365)

    def test_single_source_confidence_capped(self):
        client = _FakeFundingClient([_xl_record()])
        env = self._figure(client).per_diem_interest(loan_id="171", funding_entity_id="3")
        self.assertLessEqual(env["values"][0]["confidence"], 0.7)
        self.assertTrue(env["meta"]["confidence_record"]["single_source"])


class PerDiemRefusalTest(_PerDiemBase):
    def test_missing_rate_refuses(self):
        client = _FakeFundingClient([_xl_record(rate=_ABSENT)])
        env = self._figure(client).per_diem_interest(loan_id="171", funding_entity_id="3")
        self.assertEqual(env["state"], funding_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], funding_mod.REASON_FETCH_EMPTY)

    def test_non_positive_rate_refuses(self):
        client = _FakeFundingClient([_xl_record(rate=0)])
        env = self._figure(client).per_diem_interest(loan_id="171", funding_entity_id="3")
        self.assertEqual(env["state"], funding_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], funding_mod.REASON_BAD_INPUT)

    def test_missing_principal_refuses(self):
        client = _FakeFundingClient([_xl_record(principal=None)])
        env = self._figure(client).per_diem_interest(loan_id="171", funding_entity_id="3")
        self.assertEqual(env["state"], funding_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], funding_mod.REASON_FETCH_EMPTY)

    def test_bad_day_count_refuses(self):
        client = _FakeFundingClient([_xl_record()])
        for bad in (0, -360, 360.0, "360", True):
            env = self._figure(client).per_diem_interest(
                loan_id="171", funding_entity_id="3", day_count=bad)
            self.assertEqual(env["state"], funding_mod.STATE_REFUSED, "day_count=%r" % (bad,))
            self.assertEqual(env["refusals"][0]["reason_code"], funding_mod.REASON_BAD_INPUT)

    def test_investor_not_funding_refuses(self):
        client = _FakeFundingClient([_xl_record()])
        env = self._figure(client).per_diem_interest(loan_id="171", funding_entity_id="999")
        self.assertEqual(env["state"], funding_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], funding_mod.REASON_NOT_FUNDING)


class PerDiemDispatchTest(_PerDiemBase):
    def test_run_funding_figure_dispatches_per_diem(self):
        client = _FakeFundingClient([_xl_record()])
        env = funding_mod.run_funding_figure(
            "per_diem_interest", loan_id="171", funding_entity_id="3",
            client=client, cache=self.cache, engine=self.engine, sleep=_no_sleep)
        self.assertEqual(env["state"], funding_mod.STATE_DELIVERED, env.get("refusals"))
        self.assertEqual(env["values"][0]["value"], _PD_360)

    def test_per_diem_in_canonical_names_and_registry(self):
        self.assertIn("per_diem_interest", funding_mod.FUNDING_FIGURE_NAMES)
        reg = funding_mod.FundingFigure(client=object()).registry()
        self.assertIn("per_diem_interest", reg)


class PerDiemOrchestratorRoutingTest(unittest.TestCase):
    """smart_ask routes a per-diem question to the figure, with per-diem terms stripped from the
    entity resolution (so 'XL' + 'Lux II' still resolve)."""

    def _resolved(self, eid, name):
        m = {"id": eid, "name": name, "score": 1.0}
        return {"query": name, "match": m, "resolved": True, "ambiguous": False,
                "candidates": [m], "echo": "ok", "reason": "single match"}

    def _no_match(self, name):
        return {"query": name, "match": None, "resolved": False, "ambiguous": False,
                "candidates": [], "echo": None, "reason": "no match"}

    def test_per_diem_question_routes_to_figure(self):
        def resolve_loan(name):
            return self._resolved("171", "Lux II") \
                if "lux" in name.strip().lower() else self._no_match(name)

        def resolve_entity(name, etype):
            return self._resolved("3", "XL") \
                if etype == "fundingEntity" and name.strip().lower() == "xl" \
                else self._no_match(name)

        captured = {}

        def run_funding(fig, loan_id, fe_id):
            captured.update(fig=fig, loan_id=loan_id, fe_id=fe_id)
            return {"state": "DELIVERED", "answer": "per diem = 1029.24",
                    "values": [{"value": _PD_360}], "meta": {}}

        out = ask_mod.smart_ask(
            "What is the per diem interest for XL for Lux II loan?",
            deliver_ask=lambda q: {"state": "REFUSED", "refusals": [{"reason_code": "UNMAPPABLE"}]},
            resolve_loan=resolve_loan, resolve_entity=resolve_entity,
            run_funding=run_funding)
        self.assertEqual(out["state"], "DELIVERED")
        self.assertEqual(out["tier"], "funding")
        self.assertEqual(captured, {"fig": "per_diem_interest", "loan_id": "171", "fe_id": "3"})
        self.assertEqual(out["meta"]["resolution"]["figure"], "per_diem_interest")
        self.assertEqual(out["meta"]["resolution"]["investor"]["id"], "3")
        self.assertEqual(out["meta"]["resolution"]["loan"]["id"], "171")


if __name__ == "__main__":
    unittest.main(verbosity=2)
