#!/usr/bin/env python3
"""test_hca_funding_portfolio_outstanding.py — stdlib unittest for the investor-PORTFOLIO
OUTSTANDING figure (FundingPortfolioFigure.portfolio_outstanding in hca-funding.py).

Unlike portfolio_receivable (a single fundingEntities-record read), portfolio_outstanding is a
RECONCILED AGGREGATE over the investor's LoanFunding positions: it pages loanFundings(filter:
{fundingEntityId}) to completion, reconciles EACH position's totalOutstanding against the 5-component
identity, provenance-binds each contributor to its own Tier-1 record, and bind_aggregate-verifies the
sum. It REFUSES (never a partial sum) on any unreconciled contributor, a non-numeric total, an
incomplete fetch, or zero positions.

Fixture: two reconciling positions on XL (fundingEntity 3) —
  A (lf 10, Beehive): total 6,922,294.60 = 5,000,000 + 1,500,000 + 0 + 400,000 + 22,294.60
  B (lf 11, Granary): total 12,000,000.00 = 10,000,000 + 2,000,000 + 0 + 0 + 0
  portfolio outstanding = 18,922,294.60

Each test gets an ISOLATED Tier-1 cache dir (Tier-1 is write-once/immutable, content-addressed).
"""

import importlib.util
import os
import shutil
import sys
import tempfile
import unittest


_THIS = os.path.dirname(os.path.abspath(__file__))
_SCR = os.path.abspath(os.path.join(_THIS, os.pardir))


def _load(modname, filename):
    cached = sys.modules.get(modname)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(modname, os.path.join(_SCR, filename))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


funding = _load("hca_funding", "hca-funding.py")


def _pos(lf_id, loan_name, total, principal, interest, comp, fees, pen):
    """One loanFundings pageItem shaped exactly like the live HCAPortfolioOutstanding query."""
    return {
        "id": lf_id,
        "fundingEntity": {"id": "3", "name": "XL"},
        "asset": {"id": "L" + lf_id, "name": loan_name},
        "repaymentSchedule": {"summary": {"totalOutstanding": {
            "total": total, "principal": principal, "interest": interest,
            "compoundingInterest": comp, "totalFees": fees, "totalPenalties": pen}}},
    }


_POS_A = _pos("10", "Beehive Waldorff", 6922294.60, 5000000.0, 1500000.0, 0.0, 400000.0, 22294.60)
_POS_B = _pos("11", "Granary Row", 12000000.0, 10000000.0, 2000000.0, 0.0, 0.0, 0.0)
_PORTFOLIO_SUM = 18922294.60


class _Http500(RuntimeError):
    def __init__(self):
        super().__init__("GraphQL HTTP 500 Internal Server Error")


class _FakeLF:
    """Fake client answering the loanFundings list query, honouring skip/limit pagination.

    `report_total` overrides totalFilteredRecords (to simulate an incomplete fetch); `fail_times`
    fails the first N calls with a 500 (to exercise retry).
    """

    def __init__(self, *, positions, fail_times=0, report_total=None):
        self._positions = list(positions)
        self._fail = fail_times
        self._report_total = report_total
        self._n = 0
        self.calls = []

    def raw_query(self, query, variables=None):
        self.calls.append((query, variables))
        if "loanFundings(" in query.replace(" ", ""):
            self._n += 1
            if self._n <= self._fail:
                raise _Http500()
            v = variables or {}
            skip = int(v.get("skip", 0))
            limit = int(v.get("limit", 100))
            page = self._positions[skip:skip + limit]
            total = self._report_total if self._report_total is not None else len(self._positions)
            return {"loanFundings": {"totalFilteredRecords": total, "pageItems": page}}
        return {}


def _no_sleep(_):
    return None


class _OutstandingBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hca-portfolio-outstanding-test-")
        self.cache = funding._cache().TwoTierCache(cache_dir=self.tmp)
        self.engine = funding._provenance().ProvenanceEngine(cache=self.cache)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _fig(self, client):
        return funding.FundingPortfolioFigure(client=client, cache=self.cache, engine=self.engine,
                                              sleep=_no_sleep)


class PortfolioOutstandingTest(_OutstandingBase):
    def test_reconciled_aggregate_delivers(self):
        env = self._fig(_FakeLF(positions=[_POS_A, _POS_B])).portfolio_outstanding(
            funding_entity_id="3")
        self.assertEqual(env["state"], funding.STATE_DELIVERED)
        self.assertEqual(env["values"][0]["value"], _PORTFOLIO_SUM)
        gv = env["gate_verdict"]
        self.assertTrue(gv["reconciliation_ok"])
        self.assertTrue(gv["aggregate"])
        self.assertEqual(gv["contributors"], 2)
        self.assertTrue(gv["completeness_ok"])
        self.assertEqual(env["meta"]["funding_entity_name"], "XL")
        self.assertEqual(env["meta"]["positions"], 2)
        self.assertEqual(len(env["meta"]["breakdown"]), 2)

    def test_aggregate_provenance_resolvable(self):
        env = self._fig(_FakeLF(positions=[_POS_A, _POS_B])).portfolio_outstanding(
            funding_entity_id="3")
        contributing = env["values"][0]["provenance"]["contributing"]
        self.assertEqual(len(contributing), 2)
        resolved_sum = 0.0
        for b in contributing:
            resolved, ok = self.cache.resolve_binding(b)
            self.assertTrue(ok)
            resolved_sum += float(resolved)
        self.assertEqual(round(resolved_sum, 2), _PORTFOLIO_SUM)

    def test_one_nonreconciling_position_refuses(self):
        bad = dict(_POS_B)
        bad["repaymentSchedule"] = {"summary": {"totalOutstanding": dict(
            _POS_B["repaymentSchedule"]["summary"]["totalOutstanding"])}}
        bad["repaymentSchedule"]["summary"]["totalOutstanding"]["principal"] = 1.0  # break identity
        env = self._fig(_FakeLF(positions=[_POS_A, bad])).portfolio_outstanding(
            funding_entity_id="3")
        self.assertEqual(env["state"], funding.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], funding.REASON_RECONCILE)

    def test_partial_fetch_refuses_never_partial_sum(self):
        # server reports 3 records but only 2 are returned -> refuse, never deliver a partial sum
        env = self._fig(_FakeLF(positions=[_POS_A, _POS_B], report_total=3)).portfolio_outstanding(
            funding_entity_id="3")
        self.assertEqual(env["state"], funding.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], funding.REASON_FETCH_EMPTY)

    def test_no_positions_refuses(self):
        env = self._fig(_FakeLF(positions=[])).portfolio_outstanding(funding_entity_id="3")
        self.assertEqual(env["state"], funding.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], funding.REASON_FETCH_EMPTY)

    def test_nonnumeric_total_refuses(self):
        bad = dict(_POS_A)
        bad["repaymentSchedule"] = {"summary": {"totalOutstanding": dict(
            _POS_A["repaymentSchedule"]["summary"]["totalOutstanding"])}}
        bad["repaymentSchedule"]["summary"]["totalOutstanding"]["total"] = None
        env = self._fig(_FakeLF(positions=[bad])).portfolio_outstanding(funding_entity_id="3")
        self.assertEqual(env["state"], funding.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], funding.REASON_FETCH_EMPTY)

    def test_no_funding_entity_id_refuses(self):
        env = self._fig(_FakeLF(positions=[_POS_A])).portfolio_outstanding(funding_entity_id="")
        self.assertEqual(env["state"], funding.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], funding.REASON_BAD_INPUT)

    def test_pagination_accumulates_all_positions(self):
        # force a 1-per-page limit so the two positions span two pages; the sum must still be whole
        orig = funding._PORTFOLIO_OUTSTANDING_LIMIT
        funding._PORTFOLIO_OUTSTANDING_LIMIT = 1
        self.addCleanup(setattr, funding, "_PORTFOLIO_OUTSTANDING_LIMIT", orig)
        client = _FakeLF(positions=[_POS_A, _POS_B])
        env = self._fig(client).portfolio_outstanding(funding_entity_id="3")
        self.assertEqual(env["state"], funding.STATE_DELIVERED)
        self.assertEqual(env["values"][0]["value"], _PORTFOLIO_SUM)
        loanfunding_calls = [c for c in client.calls if "loanFundings(" in c[0].replace(" ", "")]
        self.assertGreaterEqual(len(loanfunding_calls), 2)

    def test_retry_on_500_then_succeeds(self):
        env = self._fig(_FakeLF(positions=[_POS_A, _POS_B], fail_times=1)).portfolio_outstanding(
            funding_entity_id="3")
        self.assertEqual(env["state"], funding.STATE_DELIVERED)
        self.assertEqual(env["values"][0]["value"], _PORTFOLIO_SUM)


class RunPortfolioOutstandingDispatchTest(_OutstandingBase):
    def test_dispatch_portfolio_outstanding(self):
        env = funding.run_portfolio_figure(
            "portfolio_outstanding", funding_entity_id="3",
            client=_FakeLF(positions=[_POS_A, _POS_B]), cache=self.cache, engine=self.engine,
            sleep=_no_sleep)
        self.assertEqual(env["state"], funding.STATE_DELIVERED)
        self.assertEqual(env["values"][0]["value"], _PORTFOLIO_SUM)

    def test_name_registered(self):
        self.assertIn("portfolio_outstanding", funding.PORTFOLIO_FIGURE_NAMES)
        self.assertIn("portfolio_outstanding",
                      funding.FundingPortfolioFigure(client=_FakeLF(positions=[])).registry())


if __name__ == "__main__":
    unittest.main(verbosity=2)
