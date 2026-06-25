#!/usr/bin/env python3
"""test_hca_per_diem.py — stdlib unittest for the PER-DIEM INTEREST funding figure.

The figure delivers Hypercore's OWN daily accrual (the schedule's "Int. Daily Accrual" column =
`scheduleTable[row].due.interest` on each interest-accrual row), provenance-bound to its exact
array path, with an independent computed cross-check that DERIVES the day-count convention from
Hypercore's value. When the native value is unavailable it FALLS BACK to a clearly-labelled
computed figure (Actual/360 assumed).

Live-pinned ground truth (XL on Lux II — loanFunding 338, asset 171, fundingEntity "3", schedule
214570):
  current accrual row 2026-06-18: outstanding principal 2,646,609.230893428, rate 14% ->
    native due.interest = 1029.2369231252  (== principal × 14% ÷ 360 == the UI's $1,029.24)
  earlier accrual row 2025-09-01: principal 2,979,174.52334263 -> due.interest = 1158.5678701888

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
# Live-pinned schedule rows
# ---------------------------------------------------------------------------
_PRINCIPAL_CUR = 2646609.230893428
_NATIVE_CUR = 1029.2369231252            # Hypercore's own due.interest (current accrual row)
_PRINCIPAL_OLD = 2979174.52334263
_NATIVE_OLD = 1158.5678701888

_ACCRUAL_OLD = {"index": 10, "date": "2025-09-01", "type": "PreRepaymentDue",
                "isInterestAccrualDate": True, "interestRate": 14,
                "outstanding": {"principal": _PRINCIPAL_OLD},
                "due": {"total": _NATIVE_OLD, "interest": _NATIVE_OLD}}
_NONACCRUAL = {"index": 11, "date": "2025-09-15", "type": "Repayment",
               "isInterestAccrualDate": False, "interestRate": 14,
               "outstanding": {"principal": _PRINCIPAL_OLD},
               "due": {"total": 0.0, "interest": 0.0}}
_ACCRUAL_CUR = {"index": 60, "date": "2026-06-18", "type": "PreRepaymentDue",
                "isInterestAccrualDate": True, "interestRate": 14,
                "outstanding": {"principal": _PRINCIPAL_CUR},
                "due": {"total": _NATIVE_CUR, "interest": _NATIVE_CUR}}


def _record_with_schedule(rows=(_ACCRUAL_OLD, _NONACCRUAL, _ACCRUAL_CUR)):
    return {
        "id": "lf-xl-171",
        "fundingEntity": {"id": "3", "name": "XL"},
        "currentInterestRate": 14,
        "repaymentSchedule": {
            "id": "214570",
            "summary": {"totalOutstanding": {"principal": _PRINCIPAL_CUR}},
            "scheduleTable": [dict(r) for r in rows],
        },
    }


def _record_no_schedule():
    """Record with the funding-record inputs but NO accrual rows -> fallback path."""
    return {
        "id": "lf-xl-171",
        "fundingEntity": {"id": "3", "name": "XL"},
        "currentInterestRate": 14,
        "repaymentSchedule": {
            "id": "214570",
            "summary": {"totalOutstanding": {"principal": _PRINCIPAL_CUR}},
            "scheduleTable": [dict(_NONACCRUAL)],   # present but no interest-accrual rows
        },
    }


class _FakeFundingClient:
    """Fake serving the 2-step LoanFundings path (STEP 1 by assetId -> stubs; STEP 2 by
    loanFundingId -> full record, regardless of which field selection the query requests)."""

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


class _Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hca-perdiem-test-")
        self.cache = cache_mod.TwoTierCache(cache_dir=self.tmp)
        self.engine = prov_mod.ProvenanceEngine(cache=self.cache)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _figure(self, client):
        return funding_mod.FundingFigure(client=client, cache=self.cache, engine=self.engine,
                                         sleep=_no_sleep)


class NativePathTest(_Base):
    def test_delivers_native_value_from_hypercore(self):
        client = _FakeFundingClient([_record_with_schedule()])
        env = self._figure(client).per_diem_interest(
            loan_id="171", funding_entity_id="3", currency="USD", loan_name="Lux II",
            as_of="2026-06-25")
        self.assertEqual(env["state"], funding_mod.STATE_DELIVERED, env.get("refusals"))
        v = env["values"][0]
        self.assertEqual(v["value"], _NATIVE_CUR)             # Hypercore's own number, verbatim
        self.assertEqual(round(v["value"], 2), 1029.24)       # == the UI's $1,029.24
        self.assertEqual(v["provenance"]["source"], "hypercore_native")
        self.assertEqual(env["meta"]["source"], "hypercore_native")
        self.assertEqual(env["meta"]["accrual_row_date"], "2026-06-18")
        self.assertEqual(env["meta"]["schedule_id"], "214570")
        self.assertIn("DIRECTLY from Hypercore", env["answer"])

    def test_native_value_provenance_resolves_via_array_path(self):
        client = _FakeFundingClient([_record_with_schedule()])
        env = self._figure(client).per_diem_interest(
            loan_id="171", funding_entity_id="3", as_of="2026-06-25")
        prov = env["values"][0]["provenance"]
        path = prov["json_field_path"]
        self.assertIn("scheduleTable[", path)                 # array-indexed Tier-1 path
        self.assertTrue(path.endswith(".due.interest"))
        resolved, ok = self.cache.resolve_binding(
            {"raw_response_id": prov["raw_response_id"], "json_field_path": path})
        self.assertTrue(ok)
        self.assertEqual(resolved, _NATIVE_CUR)               # re-walk -> same native value

    def test_cross_check_confirms_actual_360(self):
        client = _FakeFundingClient([_record_with_schedule()])
        env = self._figure(client).per_diem_interest(
            loan_id="171", funding_entity_id="3", as_of="2026-06-25")
        gv = env["gate_verdict"]
        self.assertEqual(gv["day_count_convention"], "Actual/360")
        self.assertTrue(gv["day_count_confirmed"])
        cross = gv["cross_check"]
        self.assertAlmostEqual(cross["implied_day_count"], 360.0, places=1)
        self.assertTrue(cross["matches_360"])
        self.assertNotIn("cross_check_flag", gv)

    def test_picks_current_row_at_or_before_as_of(self):
        # as_of in late 2025 -> the older (higher-principal) accrual row is current.
        client = _FakeFundingClient([_record_with_schedule()])
        env = self._figure(client).per_diem_interest(
            loan_id="171", funding_entity_id="3", as_of="2025-12-01")
        self.assertEqual(env["values"][0]["value"], _NATIVE_OLD)
        self.assertEqual(env["meta"]["accrual_row_date"], "2025-09-01")
        self.assertTrue(env["gate_verdict"]["day_count_confirmed"])  # 360 holds for that row too

    def test_skips_non_accrual_rows(self):
        # only a non-accrual row + the current accrual row; must pick the accrual one.
        client = _FakeFundingClient([_record_with_schedule(rows=(_NONACCRUAL, _ACCRUAL_CUR))])
        env = self._figure(client).per_diem_interest(
            loan_id="171", funding_entity_id="3", as_of="2026-06-25")
        self.assertEqual(env["values"][0]["value"], _NATIVE_CUR)
        self.assertEqual(env["meta"]["accrual_row_date"], "2026-06-18")

    def test_single_source_confidence_capped(self):
        client = _FakeFundingClient([_record_with_schedule()])
        env = self._figure(client).per_diem_interest(
            loan_id="171", funding_entity_id="3", as_of="2026-06-25")
        self.assertLessEqual(env["values"][0]["confidence"], 0.7)


class FallbackPathTest(_Base):
    def test_falls_back_to_computed_when_no_accrual_row(self):
        client = _FakeFundingClient([_record_no_schedule()])
        env = self._figure(client).per_diem_interest(
            loan_id="171", funding_entity_id="3", as_of="2026-06-25")
        self.assertEqual(env["state"], funding_mod.STATE_DELIVERED, env.get("refusals"))
        v = env["values"][0]
        self.assertEqual(v["provenance"]["source"], "computed_fallback")
        self.assertEqual(v["value"], round(_PRINCIPAL_CUR * 0.14 / 360, 6))
        self.assertEqual(round(v["value"], 2), 1029.24)
        self.assertTrue(v["provenance"]["day_count_assumed"])
        self.assertIn("COMPUTED", env["answer"])
        self.assertEqual(env["meta"]["source"], "computed_fallback")

    def test_fallback_rate_is_percent_not_fraction(self):
        client = _FakeFundingClient([_record_no_schedule()])
        env = self._figure(client).per_diem_interest(
            loan_id="171", funding_entity_id="3", as_of="2026-06-25")
        value = env["values"][0]["value"]
        self.assertAlmostEqual(value, _PRINCIPAL_CUR * 0.14 / 360, places=4)
        self.assertNotAlmostEqual(value, _PRINCIPAL_CUR * 14.0 / 360, places=2)

    def test_fallback_missing_principal_refuses(self):
        rec = _record_no_schedule()
        rec["repaymentSchedule"]["summary"]["totalOutstanding"]["principal"] = None
        env = self._figure(_FakeFundingClient([rec])).per_diem_interest(
            loan_id="171", funding_entity_id="3", as_of="2026-06-25")
        self.assertEqual(env["state"], funding_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], funding_mod.REASON_FETCH_EMPTY)

    def test_fallback_non_positive_rate_refuses(self):
        rec = _record_no_schedule()
        rec["currentInterestRate"] = 0
        env = self._figure(_FakeFundingClient([rec])).per_diem_interest(
            loan_id="171", funding_entity_id="3", as_of="2026-06-25")
        self.assertEqual(env["state"], funding_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], funding_mod.REASON_BAD_INPUT)


class RefusalTest(_Base):
    def test_investor_not_funding_refuses(self):
        client = _FakeFundingClient([_record_with_schedule()])
        env = self._figure(client).per_diem_interest(
            loan_id="171", funding_entity_id="999", as_of="2026-06-25")
        self.assertEqual(env["state"], funding_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], funding_mod.REASON_NOT_FUNDING)

    def test_bad_as_of_refuses(self):
        client = _FakeFundingClient([_record_with_schedule()])
        env = self._figure(client).per_diem_interest(
            loan_id="171", funding_entity_id="3", as_of="not-a-date")
        self.assertEqual(env["state"], funding_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], funding_mod.REASON_BAD_INPUT)


class DispatchAndRoutingTest(_Base):
    def test_run_funding_figure_dispatches_per_diem_native(self):
        client = _FakeFundingClient([_record_with_schedule()])
        env = funding_mod.run_funding_figure(
            "per_diem_interest", loan_id="171", funding_entity_id="3",
            client=client, cache=self.cache, engine=self.engine, sleep=_no_sleep,
            as_of="2026-06-25")
        self.assertEqual(env["state"], funding_mod.STATE_DELIVERED, env.get("refusals"))
        self.assertEqual(env["values"][0]["value"], _NATIVE_CUR)
        self.assertEqual(env["values"][0]["provenance"]["source"], "hypercore_native")

    def test_per_diem_in_canonical_names_and_registry(self):
        self.assertIn("per_diem_interest", funding_mod.FUNDING_FIGURE_NAMES)
        self.assertIn("per_diem_interest", funding_mod.FundingFigure(client=object()).registry())


class OrchestratorRoutingTest(unittest.TestCase):
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
            return {"state": "DELIVERED", "answer": "native per diem",
                    "values": [{"value": _NATIVE_CUR}], "meta": {}}

        out = ask_mod.smart_ask(
            "What is the per diem interest for XL for Lux II loan?",
            deliver_ask=lambda q: {"state": "REFUSED", "refusals": [{"reason_code": "UNMAPPABLE"}]},
            resolve_loan=resolve_loan, resolve_entity=resolve_entity, run_funding=run_funding)
        self.assertEqual(out["state"], "DELIVERED")
        self.assertEqual(captured, {"fig": "per_diem_interest", "loan_id": "171", "fe_id": "3"})
        self.assertEqual(out["meta"]["resolution"]["figure"], "per_diem_interest")


if __name__ == "__main__":
    unittest.main(verbosity=2)
