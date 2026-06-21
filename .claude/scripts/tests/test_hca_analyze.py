#!/usr/bin/env python3
"""test_hca_analyze.py — stdlib unittest for the portfolio ANALYSIS layer (SLICE-HCA-15).

Proves on FIXTURES (a synthetic multi-loan bulk response served by a fake GraphQL client + a
synthetic KG CSV) that hca-analyze.py:

  THE ONE BULK FETCH
    - walks the loans list to COMPLETION and caches it as ONE Tier-1 record; an analysis over a
      TRUNCATED book REFUSES (PAGINATION_INCOMPLETE), never delivers a partial-book number.

  RANKINGS
    - top-N by outstanding returns rows in correct (descending) order, each with a provenance
      pointer into the bulk record that the binder can re-resolve.

  AGGREGATIONS
    - total outstanding RECONCILES (delivered total == sum of bound parts) and carries aggregate
      provenance (one contributor per source row).
    - a mixed-currency portfolio REFUSES (cannot sum across currencies).

  FILTERING
    - overdue filter returns exactly the loans with overdue>0.

  CONCENTRATION
    - top-N concentration math: top-N exposure / book == the reported pct.

  COVENANT SCAN
    - flags LTV / debt-yield / DSCR breaches vs the PRISM thresholds for KG-covered loans, AND
      lists loans with NO KG match as `unassessable` (NOT silently dropped).

  MISSING-FIGURE SURFACING (never drop)
    - a loan missing a needed figure is SURFACED in `skipped`, not dropped and not invented.

  INTERPRETIVE JUDGMENT
    - most_at_risk applies STATED criteria, always returns the deterministic at-risk set +
      evidence, and (with an injected blind-agent runner) routes the judgment through consensus:
      agreement DELIVERS, disagreement ESCALATES (no silent pick) with evidence retained.

Run:
  python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py' -v
"""

import importlib.util
import json
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
kg_mod = _load("hca_kg", "hca-kg.py")
analyze_mod = _load("hca_analyze", "hca-analyze.py")


# ---------------------------------------------------------------------------
# Synthetic multi-loan bulk portfolio (all values synthetic; loan NAMES only, no PII).
# ---------------------------------------------------------------------------

def _summary(total=None, principal=0.0, interest=0.0, fees=0.0, penalties=0.0,
             due=None, overdue=0.0, disbursed=0.0):
    return {
        "totalOutstanding": {"total": total, "principal": principal, "interest": interest,
                             "totalFees": fees, "totalPenalties": penalties},
        "totalDue": {"total": due if due is not None else total},
        "overdue": {"total": overdue},
        "totalDisbursed": disbursed,
    }


# 5 loans. Outstanding order (desc): Beehive 31.9M, Broadbent 10M, Marsh 5M, Rincon 2M, Acme 1M.
_LOANS = [
    {"id": "134", "name": "Beehive Waldorff", "status": "active", "currency": "USD",
     "commitment": 35000000.0, "scheduleEndDate": "2026-07-01",
     "scheduleExpectedEndDate": "2026-07-01", "annualInterestRate": 0.14,
     "summary": _summary(total=31888682.99, principal=27240937.50, interest=905000.0,
                         fees=904521.18, penalties=2838224.31, overdue=2838224.31,
                         disbursed=31000000.0)},
    {"id": "200", "name": "Broadbent Springville", "status": "active", "currency": "USD",
     "commitment": 12000000.0, "scheduleEndDate": "2027-01-15",
     "scheduleExpectedEndDate": "2027-01-15", "annualInterestRate": 0.12,
     "summary": _summary(total=10000000.0, principal=10000000.0, disbursed=9000000.0)},
    {"id": "300", "name": "Marsh Hollow", "status": "active", "currency": "USD",
     "commitment": 6000000.0, "scheduleEndDate": "2026-06-25",
     "scheduleExpectedEndDate": "2026-06-25", "annualInterestRate": 0.11,
     "summary": _summary(total=5000000.0, principal=5000000.0, disbursed=6000000.0)},
    {"id": "400", "name": "Rincon Mesa", "status": "repaid", "currency": "USD",
     "commitment": 3000000.0, "scheduleEndDate": "2028-03-01",
     "scheduleExpectedEndDate": "2028-03-01", "annualInterestRate": 0.10,
     "summary": _summary(total=2000000.0, principal=2000000.0, disbursed=1500000.0)},
    # Acme: MISSING outstanding total (None) -> must be SURFACED, never dropped.
    {"id": "500", "name": "Acme Standalone", "status": "active", "currency": "USD",
     "commitment": 1500000.0, "scheduleEndDate": "2026-08-10",
     "scheduleExpectedEndDate": "2026-08-10", "annualInterestRate": 0.09,
     "summary": _summary(total=None, principal=None, overdue=0.0, disbursed=1000000.0)},
]


class _FakeBulkClient:
    """Fake LiveGraphQLClient for the bulk loans walk. Serves `_LOANS` in pages of `page_size`.

    `truncate=True` reports a larger totalFilteredRecords than it serves (so the
    pagination-complete gate must REFUSE)."""

    def __init__(self, loans=_LOANS, *, page_size=2, truncate=False):
        self.loans = loans
        self.page_size = page_size
        self.truncate = truncate
        self.calls = 0

    def raw_query(self, query, variables=None):
        self.calls += 1
        skip = (variables or {}).get("skip", 0)
        limit = (variables or {}).get("limit", self.page_size)
        page = self.loans[skip:skip + limit]
        reported = len(self.loans) + (10 if self.truncate else 0)
        return {"loans": {"totalFilteredRecords": reported, "pageItems": page}}


# Synthetic KG: Beehive has a low appraised value (forces LTV breach) + NOI (forces debt-yield/
# DSCR). Broadbent has a high appraised value (no LTV breach). Others NOT in the KG.
_KG_HEADER = ["node_id", "canonical_name", "aliases", "node_type", "short_desc",
              "verification_status", "confidence", "importance", "tags", "source_ccii",
              "extraction_date", "embedding_group", "namespace", "canonical", "sameAs",
              "merge_confidence", "notes", "pii_risk", "security_sensitivity", "properties_json"]

_KG_ROWS = [
    # Beehive outstanding 31.89M / appraised 35M = LTV 0.911 > 0.75 BREACH.
    # NOI 1M / commitment 35M = debt_yield 0.0286 < 0.08 BREACH.
    # DSCR = 1M / (35M*0.14) = 0.204 < 1.25 BREACH.
    {"node_id": "deal:beehive", "node_type": "DEAL", "confidence": 0.95,
     "canonical_name": "Beehive Waldorff", "aliases": "Beehive",
     "props": {"appraised_value": 35000000, "noi": 1000000, "interest_rate": 0.14}},
    # Broadbent outstanding 10M / appraised 40M = LTV 0.25 (no breach).
    {"node_id": "deal:broadbent", "node_type": "DEAL", "confidence": 0.92,
     "canonical_name": "Broadbent Springville", "aliases": "Broadbent",
     "props": {"appraised_value": 40000000, "noi": 5000000, "interest_rate": 0.12}},
]


def _write_kg(dirpath, rows):
    import csv as _csv
    path = os.path.join(dirpath, "nodes.csv")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = _csv.writer(fh)
        w.writerow(_KG_HEADER)
        for r in rows:
            row = {h: "" for h in _KG_HEADER}
            row["node_id"] = r["node_id"]
            row["canonical_name"] = r.get("canonical_name", "")
            row["aliases"] = r.get("aliases", "")
            row["node_type"] = r.get("node_type", "")
            row["confidence"] = r.get("confidence", "")
            row["properties_json"] = json.dumps(r.get("props", {}))
            w.writerow([row[h] for h in _KG_HEADER])
    return path


class _AnalyzeBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hca-analyze-test-")
        self.cache = cache_mod.TwoTierCache(cache_dir=self.tmp)
        self.engine = prov_mod.ProvenanceEngine(cache=self.cache)
        self.kgdir = tempfile.mkdtemp(prefix="hca-analyze-kg-")
        _write_kg(self.kgdir, _KG_ROWS)
        self.kg_store = kg_mod.KGStore(kg_dir=self.kgdir)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        shutil.rmtree(self.kgdir, ignore_errors=True)

    def _analyzer(self, *, client=None, truncate=False, loans=_LOANS):
        client = client or _FakeBulkClient(loans=loans, truncate=truncate)
        fetcher = analyze_mod.PortfolioFetcher(client=client, cache=self.cache, page_limit=2)
        return analyze_mod.PortfolioAnalyzer(fetcher=fetcher, cache=self.cache,
                                             engine=self.engine, kg_store=self.kg_store)


# ---------------------------------------------------------------------------
# THE ONE BULK FETCH + completeness gate
# ---------------------------------------------------------------------------

class BulkFetchTest(_AnalyzeBase):
    def test_bulk_fetch_walks_to_completion_one_tier1_record(self):
        client = _FakeBulkClient(page_size=2)
        fetcher = analyze_mod.PortfolioFetcher(client=client, cache=self.cache, page_limit=2)
        res = fetcher.fetch()
        self.assertTrue(res["ok"])
        self.assertEqual(len(res["rows"]), 5)
        self.assertTrue(res["complete"])
        # ONE Tier-1 record holds the WHOLE walk (3 pages: 2+2+1).
        self.assertTrue(self.cache.has_raw(res["rid"]))
        self.assertEqual(client.calls, 3)
        # memoized: a second fetch does not re-hit the client.
        res2 = fetcher.fetch()
        self.assertEqual(res2["rid"], res["rid"])
        self.assertEqual(client.calls, 3)

    def test_truncated_walk_refuses_analysis(self):
        env = self._analyzer(truncate=True).rank("outstanding", top_n=3)
        self.assertEqual(env["state"], analyze_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], analyze_mod.REASON_INCOMPLETE)

    def test_no_loans_refuses(self):
        env = self._analyzer(loans=[]).rank("outstanding")
        self.assertEqual(env["state"], analyze_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], analyze_mod.REASON_FETCH_EMPTY)


# ---------------------------------------------------------------------------
# RANKINGS
# ---------------------------------------------------------------------------

class RankingTest(_AnalyzeBase):
    def test_top_by_outstanding_order_and_provenance(self):
        env = self._analyzer().rank("outstanding", top_n=3)
        self.assertEqual(env["state"], analyze_mod.STATE_DELIVERED)
        names = [r["name"] for r in env["rows"]]
        self.assertEqual(names, ["Beehive Waldorff", "Broadbent Springville", "Marsh Hollow"])
        vals = [r["value"] for r in env["rows"]]
        self.assertEqual(vals, sorted(vals, reverse=True))
        # each ranked row's provenance pointer re-resolves to the same value in Tier-1.
        for r in env["rows"]:
            prov = r["provenance"]
            res = self.engine.bind_and_verify(
                r["value"], {"raw_response_id": prov["bulk_raw_response_id"],
                             "json_field_path": prov["json_field_path"]})
            self.assertEqual(res["outcome"], prov_mod.VERIFIED)

    def test_ranking_surfaces_missing_figure_loan(self):
        env = self._analyzer().rank("outstanding", top_n=10)
        # Acme has no outstanding total -> surfaced in skipped, not ranked.
        ranked_ids = {r["loan_id"] for r in env["rows"]}
        self.assertNotIn("500", ranked_ids)
        skipped_ids = {s["loan_id"] for s in env["skipped"]}
        self.assertIn("500", skipped_ids)

    def test_unknown_rank_figure_refuses(self):
        env = self._analyzer().rank("not_a_figure")
        self.assertEqual(env["state"], analyze_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], analyze_mod.REASON_UNKNOWN_ANALYSIS)

    def test_closest_to_maturity_orders_soonest_first(self):
        env = self._analyzer().rank_by_maturity(top_n=3, as_of=__import__("datetime").date(2026, 6, 19))
        self.assertEqual(env["state"], analyze_mod.STATE_DELIVERED)
        days = [r["days_to_maturity"] for r in env["rows"]]
        self.assertEqual(days, sorted(days))
        # Marsh (2026-06-25) is soonest.
        self.assertEqual(env["rows"][0]["name"], "Marsh Hollow")

    def test_highest_utilization_skips_zero_commitment(self):
        env = self._analyzer().rank_by_utilization(top_n=5)
        self.assertEqual(env["state"], analyze_mod.STATE_DELIVERED)
        # Marsh: 6M disbursed / 6M commitment = 1.0 (highest).
        self.assertEqual(env["rows"][0]["name"], "Marsh Hollow")
        self.assertAlmostEqual(env["rows"][0]["value"], 1.0, places=6)


# ---------------------------------------------------------------------------
# AGGREGATIONS
# ---------------------------------------------------------------------------

class AggregationTest(_AnalyzeBase):
    def test_total_outstanding_reconciles_and_binds(self):
        env = self._analyzer().total("outstanding")
        self.assertEqual(env["state"], analyze_mod.STATE_DELIVERED)
        agg = env["aggregates"]["outstanding"]
        # 31888682.99 + 10000000 + 5000000 + 2000000 (Acme excluded — surfaced).
        self.assertAlmostEqual(agg["value"], 48888682.99, places=2)
        self.assertTrue(agg["reconciles"])
        self.assertEqual(agg["parts"], 4)
        # Acme surfaced as missing, not dropped silently.
        self.assertIn("500", {s["loan_id"] for s in env["skipped"]})
        # aggregate provenance binds (each contributor resolves + matches Tier-1).
        contributing = agg["provenance"]["contributing"]
        res = self.engine.bind_aggregate(agg["value"], contributing)
        self.assertEqual(res["outcome"], prov_mod.VERIFIED)

    def test_mixed_currency_total_refuses(self):
        loans = [dict(_LOANS[0]), dict(_LOANS[1])]
        loans[1] = {**loans[1], "currency": "EUR"}
        env = self._analyzer(loans=loans).total("outstanding")
        self.assertEqual(env["state"], analyze_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], analyze_mod.REASON_RECONCILE)

    def test_count_by_status_reconciles(self):
        env = self._analyzer().count_by_status()
        self.assertEqual(env["state"], analyze_mod.STATE_DELIVERED)
        by = env["aggregates"]["by_status"]
        self.assertEqual(by.get("active"), 4)
        self.assertEqual(by.get("repaid"), 1)
        self.assertTrue(env["aggregates"]["reconciles"])

    def test_weighted_average_rate(self):
        env = self._analyzer().weighted_average_rate()
        self.assertEqual(env["state"], analyze_mod.STATE_DELIVERED)
        # Σ(out×rate)/Σ(out) over the 4 loans carrying both outstanding + rate.
        outs = [(31888682.99, 0.14), (10000000.0, 0.12), (5000000.0, 0.11), (2000000.0, 0.10)]
        num = sum(o * r for o, r in outs)
        den = sum(o for o, _ in outs)
        self.assertAlmostEqual(env["aggregates"]["weighted_average_rate"]["value"],
                               round(num / den, 6), places=6)

    def test_weighted_average_maturity(self):
        import datetime
        env = self._analyzer().weighted_average_maturity(as_of=datetime.date(2026, 6, 19))
        self.assertEqual(env["state"], analyze_mod.STATE_DELIVERED)
        self.assertGreater(env["aggregates"]["weighted_average_maturity_days"]["value"], 0)


# ---------------------------------------------------------------------------
# FILTERING
# ---------------------------------------------------------------------------

class FilterTest(_AnalyzeBase):
    def test_overdue_filter(self):
        env = self._analyzer().filter_overdue()
        self.assertEqual(env["state"], analyze_mod.STATE_DELIVERED)
        # Only Beehive has overdue > 0.
        self.assertEqual([r["name"] for r in env["rows"]], ["Beehive Waldorff"])

    def test_over_outstanding_threshold(self):
        env = self._analyzer().filter_over_outstanding(4000000.0)
        self.assertEqual(env["state"], analyze_mod.STATE_DELIVERED)
        names = {r["name"] for r in env["rows"]}
        self.assertEqual(names, {"Beehive Waldorff", "Broadbent Springville", "Marsh Hollow"})

    def test_active_filter(self):
        env = self._analyzer().filter_active()
        self.assertEqual(env["state"], analyze_mod.STATE_DELIVERED)
        self.assertEqual(len(env["rows"]), 4)  # 4 active, Rincon is repaid

    def test_maturing_within(self):
        import datetime
        env = self._analyzer().filter_maturing_within(30, as_of=datetime.date(2026, 6, 19))
        self.assertEqual(env["state"], analyze_mod.STATE_DELIVERED)
        # Marsh (6/25) and Beehive (7/1) are within 30d; Acme (8/10) is not.
        names = {r["name"] for r in env["rows"]}
        self.assertEqual(names, {"Marsh Hollow", "Beehive Waldorff"})


# ---------------------------------------------------------------------------
# CONCENTRATION
# ---------------------------------------------------------------------------

class ConcentrationTest(_AnalyzeBase):
    def test_top_n_concentration_math(self):
        env = self._analyzer().top_n_concentration(2)
        self.assertEqual(env["state"], analyze_mod.STATE_DELIVERED)
        agg = env["aggregates"]
        top2 = 31888682.99 + 10000000.0
        book = 31888682.99 + 10000000.0 + 5000000.0 + 2000000.0
        self.assertAlmostEqual(agg["top_n_exposure"], top2, places=2)
        self.assertAlmostEqual(agg["book_total"], book, places=2)
        self.assertAlmostEqual(agg["concentration_pct"], round(top2 / book, 6), places=6)

    def test_concentration_by_status_reconciles(self):
        env = self._analyzer().concentration_by_status()
        self.assertEqual(env["state"], analyze_mod.STATE_DELIVERED)
        self.assertTrue(env["aggregates"]["reconciles"])
        bucket_sum = round(sum(r["exposure"] for r in env["rows"]), 4)
        self.assertAlmostEqual(bucket_sum, env["aggregates"]["book_total"], places=2)

    def test_concentration_by_client_refuses_without_linkage(self):
        env = self._analyzer().concentration_by_client()
        self.assertEqual(env["state"], analyze_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], analyze_mod.REASON_UNKNOWN_ANALYSIS)

    def test_concentration_by_client_groups_when_linkage_present(self):
        loans = [{**l, "clientId": ("C1" if l["id"] in ("134", "200") else "C2")}
                 for l in _LOANS]
        env = self._analyzer(loans=loans).concentration_by_client()
        self.assertEqual(env["state"], analyze_mod.STATE_DELIVERED)
        clients = {r["client"] for r in env["rows"]}
        self.assertEqual(clients, {"C1", "C2"})


# ---------------------------------------------------------------------------
# COVENANT-BREACH SCAN
# ---------------------------------------------------------------------------

class CovenantScanTest(_AnalyzeBase):
    def test_scan_flags_breaches_and_lists_unassessable(self):
        env = self._analyzer().covenant_breach_scan()
        self.assertEqual(env["state"], analyze_mod.STATE_DELIVERED)
        # Beehive (in KG, low appraised) breaches; Broadbent (in KG, high appraised) does not.
        breach_ids = {r["loan_id"] for r in env["rows"]}
        self.assertIn("134", breach_ids)
        self.assertNotIn("200", breach_ids)
        # Beehive flags ALL THREE covenants.
        beehive = next(r for r in env["rows"] if r["loan_id"] == "134")
        covs = {b["covenant"] for b in beehive["breaches"]}
        self.assertEqual(covs, {"ltv", "debt_yield", "dscr"})
        # loans NOT in the KG are listed as unassessable — NOT silently dropped.
        unassessable_ids = {u["loan_id"] for u in env["skipped"]}
        self.assertIn("300", unassessable_ids)  # Marsh: no KG
        self.assertIn("400", unassessable_ids)  # Rincon: no KG
        self.assertIn("500", unassessable_ids)  # Acme: no KG
        for u in env["skipped"]:
            self.assertIn("not assessable", u["reason"])
        # every loan is accounted for: assessed + unassessable == total.
        self.assertEqual(env["meta"]["assessed"] + env["meta"]["unassessable"],
                         env["meta"]["total_loans"])

    def test_ltv_dual_provenance(self):
        env = self._analyzer().covenant_breach_scan()
        beehive = next(r for r in env["rows"] if r["loan_id"] == "134")
        ltv_prov = beehive["provenance"]["ltv"]
        self.assertEqual(ltv_prov["outstanding"]["source"], "hypercore")
        self.assertEqual(ltv_prov["appraised_value"]["source"], "kg")
        # the hypercore side re-resolves to the bound outstanding value in Tier-1.
        hp = ltv_prov["outstanding"]
        res = self.engine.bind_and_verify(
            31888682.99, {"raw_response_id": hp["bulk_raw_response_id"],
                          "json_field_path": hp["json_field_path"]})
        self.assertEqual(res["outcome"], prov_mod.VERIFIED)


# ---------------------------------------------------------------------------
# INTERPRETIVE JUDGMENT: most_at_risk (stated criteria + consensus)
# ---------------------------------------------------------------------------

class AtRiskTest(_AnalyzeBase):
    def test_deterministic_at_risk_with_stated_criteria(self):
        import datetime
        env = self._analyzer().most_at_risk(as_of=datetime.date(2026, 6, 19))
        self.assertEqual(env["state"], analyze_mod.STATE_DELIVERED)
        # criteria are STATED + surfaced.
        self.assertIn("overdue", env["meta"]["criteria"])
        self.assertIn("high_ltv", env["meta"]["criteria"])
        # Beehive: overdue + near maturity + high LTV -> at-risk with 3 reasons.
        beehive = next(r for r in env["rows"] if r["loan_id"] == "134")
        self.assertEqual(set(beehive["reasons"]), {"overdue", "near_maturity", "high_ltv"})
        # Marsh: near maturity (6/25) -> at-risk.
        self.assertIn("300", {r["loan_id"] for r in env["rows"]})

    def test_at_risk_consensus_agreement_delivers(self):
        import datetime
        at_set = None

        def runner(question, n):
            # all agents agree on the same at-risk id set.
            return [{"value": ["134", "300"]} for _ in range(n)]

        env = self._analyzer().most_at_risk(
            as_of=datetime.date(2026, 6, 19), agent_runner=runner)
        self.assertEqual(env["state"], analyze_mod.STATE_DELIVERED)
        self.assertTrue(env["meta"]["consensus"]["quorum_reached"])
        self.assertEqual(env["meta"]["consensus"]["agreeing_count"], 3)
        # deterministic evidence still present.
        self.assertTrue(env["rows"])

    def test_at_risk_consensus_disagreement_escalates_with_evidence(self):
        import datetime

        seq = iter([["134"], ["300"], ["400"], ["134"], ["500"], ["200"]])

        def runner(question, n):
            return [{"value": next(seq)} for _ in range(n)]

        env = self._analyzer().most_at_risk(
            as_of=datetime.date(2026, 6, 19), agent_runner=runner, quorum="2-of-3", n=3,
            max_redispatch=1)
        self.assertEqual(env["state"], analyze_mod.STATE_ESCALATED)
        self.assertEqual(env["refusals"][0]["reason_code"], analyze_mod.REASON_NO_CONSENSUS)
        # the deterministic at-risk evidence is RETAINED even on escalation (no silent loss).
        self.assertTrue(env["rows"])
        self.assertIn("criteria", env["aggregates"])


if __name__ == "__main__":
    unittest.main()
