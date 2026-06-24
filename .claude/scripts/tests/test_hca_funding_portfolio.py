#!/usr/bin/env python3
"""test_hca_funding_portfolio.py — stdlib unittest for the INVESTOR-PORTFOLIO figures
(FundingPortfolioFigure in hca-funding.py): the fundingEntity-level RECONCILED receivable plus
the single-source portfolio scalars. Fakes the fundingEntities list query; no creds. Each test
gets an ISOLATED Tier-1 cache dir (Tier-1 is write-once/immutable, content-addressed).

Reconciliation fixture mirrors live XL (fundingEntity 3): receivables.total 27,040,395.55 =
principal 14,167,189.09 + interest 10,867,126.51 + totalFees 1,420,903.11 + totalPenalties
585,176.84 (other InstallmentComponents are None/0). Proves: reconciled receivable DELIVERS +
binds + reconciles; non-reconciling REFUSES; missing investor REFUSES; scalar figures deliver
single-source (cap <= 0.7); retry-on-500; and run_portfolio_figure dispatch.
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


_FE_RECORD = {
    "id": "3", "name": "XL",
    "totalCommitment": 66447274.13, "totalDisbursement": 50000000.0,
    "contributed": 0.0, "activeLoansCount": 7,
    "receivables": {
        "total": 27040395.55, "principal": 14167189.09, "indexedPrincipal": None,
        "interest": 10867126.51, "compoundingInterest": 0.0, "accruedCompoundingInterest": None,
        "totalFees": 1420903.11, "totalPenalties": 585176.84, "totalTaxes": 0.0,
    },
}


class _Http500(RuntimeError):
    def __init__(self):
        super().__init__("GraphQL HTTP 500 Internal Server Error")


class _FakeFE:
    """Fake client: answers the fundingEntities list query; can fail the first N calls with 500."""

    def __init__(self, *, record=_FE_RECORD, fail_times=0):
        self._record = record
        self._fail = fail_times
        self._n = 0
        self.calls = []

    def raw_query(self, query, variables=None):
        self.calls.append((query, variables))
        if "fundingEntities(" in query.replace(" ", ""):
            self._n += 1
            if self._n <= self._fail:
                raise _Http500()
            items = [dict(self._record)] if self._record is not None else []
            return {"fundingEntities": {"totalFilteredRecords": len(items), "pageItems": items}}
        return {}


def _no_sleep(_):
    return None


class _PortfolioBase(unittest.TestCase):
    """Each test gets a fresh ISOLATED Tier-1 cache dir (avoids cross-test immutability clashes)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hca-portfolio-test-")
        self.cache = funding._cache().TwoTierCache(cache_dir=self.tmp)
        self.engine = funding._provenance().ProvenanceEngine(cache=self.cache)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _fig(self, client):
        return funding.FundingPortfolioFigure(client=client, cache=self.cache, engine=self.engine,
                                              sleep=_no_sleep)


class PortfolioReceivableTest(_PortfolioBase):
    def test_reconciled_receivable_delivers(self):
        env = self._fig(_FakeFE()).portfolio_receivable(funding_entity_id="3", name_hint="XL")
        self.assertEqual(env["state"], funding.STATE_DELIVERED)
        self.assertTrue(env["gate_verdict"]["reconciliation_ok"])
        self.assertEqual(env["values"][0]["value"], 27040395.55)
        self.assertEqual(env["meta"]["funding_entity_name"], "XL")

    def test_provenance_resolvable(self):
        env = self._fig(_FakeFE()).portfolio_receivable(funding_entity_id="3", name_hint="XL")
        v = env["values"][0]
        resolved, ok = self.cache.resolve_binding(
            {"raw_response_id": v["provenance"]["raw_response_id"],
             "json_field_path": v["provenance"]["json_field_path"]})
        self.assertTrue(ok)
        self.assertEqual(resolved, 27040395.55)

    def test_non_reconciling_refuses(self):
        rec = dict(_FE_RECORD)
        rec["receivables"] = dict(rec["receivables"])
        rec["receivables"]["principal"] = 999.0  # breaks the identity (total left unchanged)
        env = self._fig(_FakeFE(record=rec)).portfolio_receivable(funding_entity_id="3")
        self.assertEqual(env["state"], funding.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], funding.REASON_RECONCILE)

    def test_investor_not_found_refuses(self):
        env = self._fig(_FakeFE()).portfolio_receivable(funding_entity_id="999")
        self.assertEqual(env["state"], funding.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], funding.REASON_FETCH_EMPTY)

    def test_retry_on_500_then_succeeds(self):
        env = self._fig(_FakeFE(fail_times=1)).portfolio_receivable(funding_entity_id="3")
        self.assertEqual(env["state"], funding.STATE_DELIVERED)


class PortfolioScalarsTest(_PortfolioBase):
    def test_commitment_single_source_capped(self):
        env = self._fig(_FakeFE()).portfolio_commitment(funding_entity_id="3")
        self.assertEqual(env["state"], funding.STATE_DELIVERED)
        self.assertEqual(env["values"][0]["value"], 66447274.13)
        self.assertLessEqual(env["values"][0]["confidence"], 0.7)
        self.assertIsNone(env["gate_verdict"]["reconciliation_ok"])

    def test_active_loans_count_unit(self):
        env = self._fig(_FakeFE()).portfolio_active_loans(funding_entity_id="3")
        self.assertEqual(env["values"][0]["value"], 7)
        self.assertEqual(env["values"][0]["unit"], "count")
        self.assertIsNone(env["values"][0]["currency"])


class RunPortfolioFigureTest(_PortfolioBase):
    def test_unknown_figure_refuses(self):
        env = funding.run_portfolio_figure("nope", funding_entity_id="3",
                                           client=_FakeFE(), cache=self.cache, engine=self.engine,
                                           sleep=_no_sleep)
        self.assertEqual(env["state"], funding.STATE_REFUSED)

    def test_dispatch_receivable(self):
        env = funding.run_portfolio_figure("portfolio_receivable", funding_entity_id="3",
                                           client=_FakeFE(), cache=self.cache, engine=self.engine,
                                           name_hint="XL", sleep=_no_sleep)
        self.assertEqual(env["state"], funding.STATE_DELIVERED)
        self.assertEqual(env["values"][0]["value"], 27040395.55)


if __name__ == "__main__":
    unittest.main(verbosity=2)
