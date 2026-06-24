#!/usr/bin/env python3
"""test_hca_figures.py — stdlib unittest for the figure abstraction + the first figure
(payoff / early-redemption), SLICE-HCA-12.

Proves on FIXTURES (no network, no creds) — via a fake GraphQL client that serves a synthetic
`getLoanRepaymentDistribution` response — that the payoff figure:

  HAPPY PATH
    - delivers a DELIVERED envelope whose `total` is BOUND to a cached Tier-1 record (the
      binder can re-walk $.body.record.total and get the same number) and whose components
      RECONCILE to the total within $0.01; itemized components appear in the envelope meta.
    - uses the EXACT KNOWN-GOOD input shape (includeDraftChanges:false, repaymentType:
      "EarlyRedemption", applyExpectedRepaymentsUntilEarlyRedemption:false, isPrepayment:false).
    - default date == today when none supplied; explicit date honored.

  REFUSAL (REQUIRED — fail = REJECT)
    - a NON-reconciling response (components don't sum to total) -> REFUSED (RECONCILE_FAILED),
      never a number.
    - the resolver returns HTTP 500 on every attempt -> REFUSED (LIVE_500) after retries
      exhausted, stating the 500. NEVER fabricates a payoff.

  RETRY
    - a 500 on the first attempt then success -> DELIVERED (retry-on-500 works, bounded).

Run:
  python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py' -v
"""

import datetime
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
figures_mod = _load("hca_figures", "hca-figures.py")
resolve_mod = _load("hca_resolve", "hca-resolve.py")
deliver_mod = _load("hca_deliver", "hca-deliver.py")


# GROUND-TRUTH from the live verification (loan 134 "Beehive Waldorff", 2026-06-30):
#   total 31888682.99 = principal 27240937.50 + interest 905000 + totalFees 904521.18
#                     + totalPenalties 2838224.31 (+ compounding 0 + taxes 0)
_GROUND_TRUTH = {
    "total": 31888682.99,
    "totalWithTaxes": 31888682.99,
    "principal": 27240937.50,
    "indexedPrincipal": 0.0,
    "compoundingInterest": 0.0,
    "accruedCompoundingInterest": 0.0,
    "interest": 905000.0,
    "totalFees": 904521.18,
    "totalPenalties": 2838224.31,
    "totalTaxes": 0.0,
}

# A response whose components do NOT sum to total (fabrication / inconsistency simulation).
_NON_RECONCILING = dict(_GROUND_TRUTH)
_NON_RECONCILING = {**_GROUND_TRUTH, "total": 99999999.99}  # total inflated; components unchanged


class _Http500(RuntimeError):
    pass


class _FakeClient:
    """Fake LiveGraphQLClient for getLoanRepaymentDistribution.

    Records the variables it was called with (so we can assert the EXACT known-good input),
    and can simulate a configurable number of leading HTTP-500 failures before succeeding.
    """

    def __init__(self, components, *, fail_times=0):
        self.components = components
        self.fail_times = fail_times
        self.calls = []
        self._attempt = 0

    def raw_query(self, query, variables=None):
        self._attempt += 1
        self.calls.append((query, variables))
        if self._attempt <= self.fail_times:
            raise _Http500("GraphQL HTTP 500 Internal Server Error")
        return {"getLoanRepaymentDistribution": dict(self.components)}


def _no_sleep(_):
    return None


class _FigBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hca-fig-test-")
        self.cache = cache_mod.TwoTierCache(cache_dir=self.tmp)
        self.engine = prov_mod.ProvenanceEngine(cache=self.cache)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _figure(self, client):
        return figures_mod.PayoffFigure(client=client, cache=self.cache, engine=self.engine,
                                        sleep=_no_sleep)


class FigureAbstractionTest(unittest.TestCase):
    def test_registry_routes_synonyms_to_payoff_figure(self):
        reg = figures_mod.build_registry()
        self.assertIn("payoff_as_of", reg.names())
        for token in ("payoff_as_of", "early_redemption", "early redemption", "payoff",
                      "amount to redeem"):
            fig = reg.get(token)
            self.assertIsNotNone(fig, f"token {token!r} should route to a figure")
            self.assertEqual(fig.name, "payoff_as_of")

    def test_figure_declares_kind_and_synonyms(self):
        reg = figures_mod.build_registry()
        fig = reg.get("payoff_as_of")
        self.assertEqual(fig.kind, figures_mod.KIND_DERIVED)
        self.assertIn("early_redemption", fig.synonyms)


class PayoffHappyPathTest(_FigBase):
    def test_delivers_with_bound_total_and_reconciles(self):
        client = _FakeClient(_GROUND_TRUTH)
        env = self._figure(client).fetch_verify(loan_id="134", date="2026-06-30",
                                                loan_name="Beehive Waldorff")
        self.assertEqual(env["state"], figures_mod.STATE_DELIVERED, env.get("refusals"))
        v = env["values"][0]
        self.assertEqual(v["value"], 31888682.99)
        # provenance is RESOLVABLE: re-walk the cited Tier-1 path -> same value.
        rid = v["provenance"]["raw_response_id"]
        path = v["provenance"]["json_field_path"]
        resolved, ok = self.cache.resolve_binding({"raw_response_id": rid,
                                                   "json_field_path": path})
        self.assertTrue(ok)
        self.assertEqual(resolved, 31888682.99)
        # reconciliation passed; meta itemizes the components.
        self.assertTrue(env["meta"]["reconciles"])
        self.assertTrue(env["gate_verdict"]["reconciliation_ok"])
        comps = env["meta"]["components"]
        self.assertEqual(comps["principal"], 27240937.50)
        self.assertEqual(comps["totalPenalties"], 2838224.31)

    def test_uses_exact_known_good_input(self):
        client = _FakeClient(_GROUND_TRUTH)
        self._figure(client).fetch_verify(loan_id="134", date="2026-06-30")
        # the LAST (only) call carried the exact input shape
        _q, variables = client.calls[-1]
        inp = variables["input"]
        self.assertEqual(inp, {
            "loanId": "134", "includeDraftChanges": False, "date": "2026-06-30",
            "repaymentType": "EarlyRedemption",
            "applyExpectedRepaymentsUntilEarlyRedemption": False, "isPrepayment": False,
        })

    def test_default_date_is_today_when_none(self):
        client = _FakeClient(_GROUND_TRUTH)
        env = self._figure(client).fetch_verify(loan_id="134", date=None)
        today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        self.assertEqual(env["meta"]["date"], today)
        _q, variables = client.calls[-1]
        self.assertEqual(variables["input"]["date"], today)

    def test_single_source_confidence_capped_and_flagged(self):
        client = _FakeClient(_GROUND_TRUTH)
        env = self._figure(client).fetch_verify(loan_id="134", date="2026-06-30")
        conf = env["values"][0]["confidence"]
        self.assertLessEqual(conf, 0.7)  # single-source cap
        self.assertTrue(env["meta"]["confidence_record"]["single_source"])


class PayoffReconcileRefusalTest(_FigBase):
    def test_non_reconciling_response_refuses_no_number(self):
        client = _FakeClient(_NON_RECONCILING)
        env = self._figure(client).fetch_verify(loan_id="134", date="2026-06-30")
        self.assertEqual(env["state"], figures_mod.STATE_REFUSED)
        self.assertEqual(env["values"], [])  # NEVER a number on a refusal
        codes = {r["reason_code"] for r in env["refusals"]}
        self.assertIn(figures_mod.REASON_RECONCILE, codes)


class PayoffRetryTest(_FigBase):
    def test_retry_on_500_then_success_delivers(self):
        # fail once (HTTP 500) then succeed -> still delivers (retry works)
        client = _FakeClient(_GROUND_TRUTH, fail_times=1)
        env = self._figure(client).fetch_verify(loan_id="134", date="2026-06-30")
        self.assertEqual(env["state"], figures_mod.STATE_DELIVERED, env.get("refusals"))
        self.assertEqual(env["values"][0]["value"], 31888682.99)
        self.assertEqual(env["meta"]["attempts"], 2)  # 1 failed + 1 success

    def test_500_on_every_attempt_refuses_stating_500(self):
        client = _FakeClient(_GROUND_TRUTH, fail_times=99)  # always fail
        env = self._figure(client).fetch_verify(loan_id="134", date="2026-06-30")
        self.assertEqual(env["state"], figures_mod.STATE_REFUSED)
        self.assertEqual(env["values"], [])
        codes = {r["reason_code"] for r in env["refusals"]}
        self.assertIn(figures_mod.REASON_LIVE_500, codes)
        # the refusal states the 500 + the attempt count
        self.assertIn("500", env["refusals"][0]["reason"])
        # exactly RETRY_ATTEMPTS tries were made (bounded)
        self.assertEqual(len(client.calls), figures_mod.RETRY_ATTEMPTS)


class PayoffBadInputTest(_FigBase):
    def test_missing_loan_id_refuses(self):
        client = _FakeClient(_GROUND_TRUTH)
        env = self._figure(client).fetch_verify(loan_id="", date="2026-06-30")
        self.assertEqual(env["state"], figures_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], figures_mod.REASON_BAD_INPUT)

    def test_invalid_date_refuses(self):
        client = _FakeClient(_GROUND_TRUTH)
        env = self._figure(client).fetch_verify(loan_id="134", date="June 30")
        self.assertEqual(env["state"], figures_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], figures_mod.REASON_BAD_INPUT)


# ---------------------------------------------------------------------------
# End-to-end through the deliver spine: payoff intent routes resolve -> figure.
# This is the fix for the earlier `no_lookup_target` refusal on payoff questions.
# ---------------------------------------------------------------------------

_SPINE_LOANS = [
    {"id": "134", "name": "Beehive Waldorff", "status": "ACTIVE"},
    {"id": "303", "name": "Maple Grove Senior", "status": "ACTIVE"},
    {"id": "304", "name": "Maple Grove Junior", "status": "ACTIVE"},
]


class _ResolveFakeClient:
    def __init__(self, loans):
        self.loans = loans

    def raw_query(self, query, variables=None):
        variables = variables or {}
        ss = ((variables.get("filter") or {}).get("searchString") or "").strip().lower()
        rows = [l for l in self.loans if ss in l["name"].lower()] if ss else list(self.loans)
        return {"loans": {"totalFilteredRecords": len(rows), "pageItems": rows}}


class PayoffViaSpineTest(_FigBase):
    """The deliver spine routes a payoff question: plan(payoff) -> resolve -> figure."""

    def _spine(self, *, figure_client, resolve_loans):
        resolver = resolve_mod.LoanResolver(client=_ResolveFakeClient(resolve_loans))
        # a figures registry whose payoff figure uses our fake getLoanRepaymentDistribution
        registry = figures_mod.FigureRegistry()
        payoff = figures_mod.PayoffFigure(client=figure_client, cache=self.cache,
                                          engine=self.engine, sleep=_no_sleep)
        registry.register(figures_mod.Figure(
            figures_mod.PayoffFigure.NAME, synonyms=figures_mod.PayoffFigure.SYNONYMS,
            kind=figures_mod.KIND_DERIVED, fetch_verify=payoff.fetch_verify))
        return deliver_mod.DeliverySpine(cache=self.cache, engine=self.engine,
                                         resolver=resolver, figures=registry)

    def test_payoff_question_resolves_and_delivers(self):
        spine = self._spine(figure_client=_FakeClient(_GROUND_TRUTH),
                            resolve_loans=_SPINE_LOANS)
        env = spine.ask("what is the payoff for beehive as of 2026-06-30")
        self.assertEqual(env["state"], "DELIVERED", env.get("refusals"))
        self.assertEqual(env["values"][0]["value"], 31888682.99)
        # the resolution echo is surfaced for the caller to display
        self.assertIsNotNone(env["meta"]["echo"])
        self.assertIn("Beehive Waldorff", env["meta"]["echo"])
        self.assertEqual(env["meta"]["loan_id"], "134")
        self.assertEqual(env["plan"]["intent"], "payoff")

    def test_ambiguous_payoff_disambiguates_no_silent_pick(self):
        spine = self._spine(figure_client=_FakeClient(_GROUND_TRUTH),
                            resolve_loans=_SPINE_LOANS)
        env = spine.ask("what is the payoff for maple grove")
        self.assertEqual(env["state"], "REFUSED")
        self.assertEqual(env["values"], [])  # never auto-picks a candidate
        # the candidate list is surfaced for disambiguation
        cands = env["refusals"][0]["candidates"]
        self.assertEqual({c["id"] for c in cands}, {"303", "304"})

    def test_no_match_payoff_refuses(self):
        spine = self._spine(figure_client=_FakeClient(_GROUND_TRUTH),
                            resolve_loans=_SPINE_LOANS)
        env = spine.ask("what is the payoff for nonexistent zzz loan")
        self.assertEqual(env["state"], "REFUSED")
        self.assertEqual(env["values"], [])

    def test_payoff_question_no_longer_unmappable(self):
        # regression: a payoff question must NOT fall through to the old no_lookup_target /
        # unmappable refusal. It must reach the payoff intent.
        plan = deliver_mod.plan_question("what is the payoff for Beehive Waldorff")
        self.assertEqual(plan["intent"], "payoff")
        self.assertEqual(plan["loan_name"], "Beehive Waldorff")


# ===========================================================================
# HYPERCORE-NATIVE FIGURES (SLICE-HCA-13)
# ===========================================================================

# A synthetic loan SUMMARY row for loan 134 "Beehive Waldorff". The reconciliation identity
# for outstanding_balance: total = principal + interest + compoundingInterest + totalFees +
# totalPenalties (the native outstanding figure reconciles these). Synthetic numbers, not real.
_SUMMARY_BEEHIVE = {
    "id": "134", "name": "Beehive Waldorff", "currency": "USD",
    "commitment": 30000000.0, "scheduleEndDate": "2027-01-31",
    "scheduleExpectedEndDate": "2027-01-31", "status": "ACTIVE", "annualInterestRate": 0.12,
    "summary": {
        "totalOutstanding": {
            "total": 28145000.0, "principal": 27000000.0, "interest": 905000.0,
            "compoundingInterest": 0.0, "totalFees": 240000.0, "totalPenalties": 0.0,
            "capitalizedBalance": 0.0,
        },
        "totalDue": {"total": 905000.0, "principal": 0.0, "interest": 905000.0},
        "overdue": {"total": 0.0},
        "totalPaid": {"total": 1200000.0},
        "totalDisbursed": 24000000.0,
        "unutilizedPrincipal": 6000000.0,
        "distributedPrincipal": 24000000.0,
        "interestRate": 0.12,
    },
}

_SUMMARY_MAPLE = {
    "id": "303", "name": "Maple Grove Senior", "currency": "USD",
    "commitment": 10000000.0, "scheduleEndDate": "2026-12-31",
    "scheduleExpectedEndDate": "2026-12-31", "status": "ACTIVE", "annualInterestRate": 0.10,
    "summary": {
        "totalOutstanding": {
            "total": 5500000.0, "principal": 5000000.0, "interest": 500000.0,
            "compoundingInterest": 0.0, "totalFees": 0.0, "totalPenalties": 0.0,
            "capitalizedBalance": 0.0,
        },
        "totalDue": {"total": 500000.0, "principal": 0.0, "interest": 500000.0},
        "overdue": {"total": 0.0},
        "totalPaid": {"total": 0.0},
        "totalDisbursed": 5000000.0,
        "unutilizedPrincipal": 5000000.0,
        "distributedPrincipal": 5000000.0,
        "interestRate": 0.10,
    },
}


class _SummaryFakeClient:
    """Fake client serving BOTH loans+summary (native figures) and getLoanRepaymentDistribution
    (payoff). Returns the matching summary rows for the loans list query (filtered by id/name).
    """

    def __init__(self, rows, *, components=None, currency_override=None):
        self.rows = rows
        self.components = components
        self.currency_override = currency_override
        self.calls = []

    def raw_query(self, query, variables=None):
        self.calls.append((query, variables))
        if "getLoanRepaymentDistribution" in query:
            return {"getLoanRepaymentDistribution": dict(self.components or _GROUND_TRUTH)}
        # loans+summary list query
        variables = variables or {}
        ss = ((variables.get("filter") or {}).get("searchString") or "")
        ss = (ss or "").strip().lower()
        if ss:
            rows = [r for r in self.rows
                    if ss in r["name"].lower() or ss == str(r["id"])]
        else:
            rows = list(self.rows)
        return {"loans": {"totalFilteredRecords": len(rows), "pageItems": rows}}


class _NativeFigBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hca-native-test-")
        self.cache = cache_mod.TwoTierCache(cache_dir=self.tmp)
        self.engine = prov_mod.ProvenanceEngine(cache=self.cache)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _registry(self, client):
        return figures_mod.build_registry(client=client, cache=self.cache, engine=self.engine,
                                          sleep=_no_sleep)


class NativeFigureTest(_NativeFigBase):
    def test_each_native_figure_returns_value_currency_provenance(self):
        client = _SummaryFakeClient([_SUMMARY_BEEHIVE])
        reg = self._registry(client)
        expected = {
            "outstanding_balance": 28145000.0,
            "principal_outstanding": 27000000.0,
            "accrued_interest": 905000.0,
            "default_interest": 0.0,
            "amount_due_today": 905000.0,
            "overdue_amount": 0.0,
            "commitment": 30000000.0,
            "total_disbursed": 24000000.0,
        }
        for name, want in expected.items():
            fig = reg.get(name)
            self.assertIsNotNone(fig, f"{name} should be registered")
            env = fig.run(loan_id="134", loan_name="Beehive Waldorff")
            self.assertEqual(env["state"], figures_mod.STATE_DELIVERED,
                             f"{name}: {env.get('refusals')}")
            v = env["values"][0]
            self.assertEqual(v["value"], want, f"{name} value")
            self.assertEqual(v["currency"], "USD", f"{name} currency")
            # provenance is RESOLVABLE: re-walk the cited Tier-1 path -> same value.
            resolved, ok = self.cache.resolve_binding({
                "raw_response_id": v["provenance"]["raw_response_id"],
                "json_field_path": v["provenance"]["json_field_path"]})
            self.assertTrue(ok, f"{name} provenance must resolve")
            self.assertEqual(resolved, want, f"{name} provenance value must match")

    def test_outstanding_balance_reconciles_components(self):
        client = _SummaryFakeClient([_SUMMARY_BEEHIVE])
        reg = self._registry(client)
        env = reg.get("outstanding_balance").run(loan_id="134", loan_name="Beehive Waldorff")
        self.assertEqual(env["state"], figures_mod.STATE_DELIVERED)
        self.assertTrue(env["gate_verdict"]["reconciliation_ok"])
        # 27000000 + 905000 + 0 + 240000 + 0 == 28145000
        self.assertEqual(env["meta"]["reconcile"]["component_sum"], 28145000.0)

    def test_outstanding_balance_reconciles_with_nonzero_capitalized_balance(self):
        # Regression (round-1 robust review, MEDIUM): capitalizedBalance is fetched in
        # _SUMMARY_SELECTION and IS part of the additive totalOutstanding identity. Before the fix
        # it was excluded from the reconcile component tuple, so a NON-ZERO capitalizedBalance made
        # component_sum != total and FALSELY REFUSED valid data (RECONCILE_FAILED). Every shipped
        # fixture pins it 0.0, so this non-zero case is what locks the fix.
        capbal = {
            "id": "777", "name": "Capital Heights", "currency": "USD",
            "commitment": 20000000.0, "scheduleEndDate": "2027-06-30",
            "scheduleExpectedEndDate": "2027-06-30", "status": "ACTIVE",
            "annualInterestRate": 0.11,
            "summary": {
                "totalOutstanding": {
                    # 9,000,000 + 300,000 + 0 + 50,000 + 0 + 1,000,000 == 10,350,000
                    "total": 10350000.0, "principal": 9000000.0, "interest": 300000.0,
                    "compoundingInterest": 0.0, "totalFees": 50000.0, "totalPenalties": 0.0,
                    "capitalizedBalance": 1000000.0,  # NON-ZERO — the regression case
                },
                "totalDue": {"total": 300000.0, "principal": 0.0, "interest": 300000.0},
                "overdue": {"total": 0.0},
                "totalPaid": {"total": 0.0},
                "totalDisbursed": 9000000.0,
                "unutilizedPrincipal": 11000000.0,
                "distributedPrincipal": 9000000.0,
                "interestRate": 0.11,
            },
        }
        client = _SummaryFakeClient([capbal])
        reg = self._registry(client)
        env = reg.get("outstanding_balance").run(loan_id="777", loan_name="Capital Heights")
        self.assertEqual(env["state"], figures_mod.STATE_DELIVERED, env.get("refusals"))
        self.assertTrue(env["gate_verdict"]["reconciliation_ok"])
        self.assertEqual(env["values"][0]["value"], 10350000.0)
        # the non-zero capitalizedBalance (1,000,000) is summed into the components
        self.assertEqual(env["meta"]["reconcile"]["component_sum"], 10350000.0)

    def test_maturity_date_is_a_date_string(self):
        client = _SummaryFakeClient([_SUMMARY_BEEHIVE])
        reg = self._registry(client)
        env = reg.get("maturity_date").run(loan_id="134", loan_name="Beehive Waldorff")
        self.assertEqual(env["state"], figures_mod.STATE_DELIVERED)
        self.assertEqual(env["values"][0]["value"], "2027-01-31")
        self.assertEqual(env["values"][0]["unit"], "date")
        self.assertIsNone(env["values"][0]["currency"])  # a date carries no currency

    def test_native_figures_are_single_source_capped(self):
        client = _SummaryFakeClient([_SUMMARY_BEEHIVE])
        reg = self._registry(client)
        env = reg.get("commitment").run(loan_id="134", loan_name="Beehive Waldorff")
        self.assertLessEqual(env["values"][0]["confidence"], 0.7)
        self.assertTrue(env["meta"]["confidence_record"]["single_source"])

    def test_missing_loan_row_refuses_no_number(self):
        client = _SummaryFakeClient([_SUMMARY_BEEHIVE])
        reg = self._registry(client)
        env = reg.get("commitment").run(loan_id="999", loan_name="Nonexistent")
        self.assertEqual(env["state"], figures_mod.STATE_REFUSED)
        self.assertEqual(env["values"], [])


class DerivedUtilizationTest(_NativeFigBase):
    def test_utilization_computes_and_shows_formula(self):
        client = _SummaryFakeClient([_SUMMARY_BEEHIVE])
        reg = self._registry(client)
        env = reg.get("utilization").run(loan_id="134", loan_name="Beehive Waldorff")
        self.assertEqual(env["state"], figures_mod.STATE_DELIVERED, env.get("refusals"))
        # 24000000 / 30000000 = 0.8
        self.assertEqual(env["values"][0]["value"], 0.8)
        self.assertEqual(env["values"][0]["unit"], "ratio")
        self.assertIsNone(env["values"][0]["currency"])  # a ratio carries no currency
        # the transparent formula + the input values are surfaced
        self.assertEqual(env["meta"]["formula"], "total_disbursed / commitment")
        self.assertEqual(env["meta"]["inputs"]["total_disbursed"], 24000000.0)
        self.assertEqual(env["meta"]["inputs"]["commitment"], 30000000.0)
        # per-input provenance preserved (each input was itself bound+verified)
        self.assertIn("total_disbursed", env["values"][0]["provenance"]["inputs"])
        self.assertIn("commitment", env["values"][0]["provenance"]["inputs"])

    def test_utilization_refuses_when_an_input_refuses(self):
        # a loan that the list query won't return -> total_disbursed input REFUSES -> derived REFUSES
        client = _SummaryFakeClient([_SUMMARY_BEEHIVE])
        reg = self._registry(client)
        env = reg.get("utilization").run(loan_id="999", loan_name="Nope")
        self.assertEqual(env["state"], figures_mod.STATE_REFUSED)
        self.assertEqual(env["values"], [])
        codes = {r["reason_code"] for r in env["refusals"]}
        self.assertIn(figures_mod.REASON_DERIVE_FAILED, codes)


# ---------------------------------------------------------------------------
# KG-JOINED LEVERAGE FIGURES (SLICE-HCA-14). These tests use a FIXTURE KG (synthetic CSV
# written to a temp dir) so they never depend on the live ~/okoa-labs knowledge graph.
# ---------------------------------------------------------------------------

kg_mod = _load("hca_kg", "hca-kg.py")


def _write_fixture_kg(dirpath, rows):
    """Write a synthetic nodes.csv (the KG schema) with the given rows into `dirpath`.

    `rows` is a list of dicts with keys: node_id, canonical_name, aliases, node_type,
    confidence, verification_status, props (a dict -> properties_json). All values synthetic.
    """
    import csv as _csv
    import json as _json
    header = ["node_id", "canonical_name", "aliases", "node_type", "short_desc",
              "verification_status", "confidence", "importance", "tags", "source_ccii",
              "extraction_date", "embedding_group", "namespace", "canonical", "sameAs",
              "merge_confidence", "notes", "pii_risk", "security_sensitivity", "properties_json"]
    path = os.path.join(dirpath, "nodes.csv")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = _csv.writer(fh)
        w.writerow(header)
        for r in rows:
            row = {h: "" for h in header}
            row["node_id"] = r["node_id"]
            row["canonical_name"] = r.get("canonical_name", "")
            row["aliases"] = r.get("aliases", "")
            row["node_type"] = r.get("node_type", "")
            row["verification_status"] = r.get("verification_status", "")
            row["confidence"] = r.get("confidence", "")
            row["properties_json"] = _json.dumps(r.get("props", {}))
            w.writerow([row[h] for h in header])
    return path


# A synthetic DEAL node carrying appraised_value + ltv_latest + interest_rate + NOI (so all four
# ratios can compute) and a no-NOI sibling deal (so DSCR/debt_yield refuse). PURELY SYNTHETIC.
_FIXTURE_KG_ROWS = [
    {"node_id": "deal:fixture-springwater", "node_type": "DEAL", "confidence": 0.95,
     "verification_status": "verified",
     "canonical_name": "Springwater Landing Fixture",
     "aliases": "Springwater|Springwater Fixture Loan",
     "props": {"appraised_value": 40000000, "ltv_latest": 0.50, "interest_rate": 0.12,
               "noi": 3200000, "purchase_price": 30000000}},
    # a deal WITH appraised_value but NO NOI (DSCR / debt_yield must refuse; LTV / cap_rate split)
    {"node_id": "deal:fixture-novalueloan", "node_type": "DEAL", "confidence": 0.9,
     "verification_status": "corroborated",
     "canonical_name": "Drycreek Commercial Fixture",
     "aliases": "Drycreek|Drycreek Fixture",
     "props": {"appraised_value": 20000000, "ltv_latest": 0.40}},
    # a deal with NO appraised_value at all (LTV / cap_rate must refuse: KG_FIELD_MISSING)
    {"node_id": "deal:fixture-novalue", "node_type": "DEAL", "confidence": 0.8,
     "verification_status": "asserted",
     "canonical_name": "Hollow Ridge Fixture",
     "aliases": "Hollow Ridge|Hollow Ridge Loan",
     "props": {"noi": 1000000}},
]


# A Hypercore summary row whose name + id line up with the fixture KG deal "Springwater".
_SUMMARY_SPRINGWATER = {
    "id": "777", "name": "Springwater Fixture Loan", "currency": "USD",
    "commitment": 25000000.0, "scheduleEndDate": "2027-06-30",
    "scheduleExpectedEndDate": "2027-06-30", "status": "ACTIVE", "annualInterestRate": 0.12,
    "summary": {
        "totalOutstanding": {
            "total": 24000000.0, "principal": 23000000.0, "interest": 1000000.0,
            "compoundingInterest": 0.0, "totalFees": 0.0, "totalPenalties": 0.0,
            "capitalizedBalance": 0.0,
        },
        "totalDue": {"total": 1000000.0, "principal": 0.0, "interest": 1000000.0},
        "overdue": {"total": 0.0},
        "totalPaid": {"total": 0.0},
        "totalDisbursed": 24000000.0,
        "unutilizedPrincipal": 1000000.0,
        "distributedPrincipal": 24000000.0,
        "interestRate": 0.12,
    },
}

_SUMMARY_DRYCREEK = {
    "id": "778", "name": "Drycreek Fixture", "currency": "USD",
    "commitment": 8000000.0, "scheduleEndDate": "2027-03-31",
    "scheduleExpectedEndDate": "2027-03-31", "status": "ACTIVE", "annualInterestRate": 0.11,
    "summary": {
        "totalOutstanding": {
            "total": 8000000.0, "principal": 8000000.0, "interest": 0.0,
            "compoundingInterest": 0.0, "totalFees": 0.0, "totalPenalties": 0.0,
            "capitalizedBalance": 0.0,
        },
        "totalDue": {"total": 0.0, "principal": 0.0, "interest": 0.0},
        "overdue": {"total": 0.0},
        "totalPaid": {"total": 0.0},
        "totalDisbursed": 8000000.0,
        "unutilizedPrincipal": 0.0,
        "distributedPrincipal": 8000000.0,
        "interestRate": 0.11,
    },
}


class _LeverageFigBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hca-lev-test-")
        self.kgdir = tempfile.mkdtemp(prefix="hca-kgfix-")
        _write_fixture_kg(self.kgdir, _FIXTURE_KG_ROWS)
        self.cache = cache_mod.TwoTierCache(cache_dir=self.tmp)
        self.engine = prov_mod.ProvenanceEngine(cache=self.cache)
        self.kg_store = kg_mod.KGStore(kg_dir=self.kgdir)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        shutil.rmtree(self.kgdir, ignore_errors=True)

    def _registry(self, client):
        return figures_mod.build_registry(client=client, cache=self.cache, engine=self.engine,
                                          sleep=_no_sleep, kg_store=self.kg_store)


class LeverageLTVTest(_LeverageFigBase):
    def test_ltv_computes_with_dual_provenance_and_crosscheck(self):
        client = _SummaryFakeClient([_SUMMARY_SPRINGWATER])
        reg = self._registry(client)
        env = reg.get("ltv").run(loan_id="777", loan_name="Springwater Fixture Loan")
        self.assertEqual(env["state"], figures_mod.STATE_DELIVERED, env.get("refusals"))
        v = env["values"][0]
        # LTV = outstanding 24,000,000 / appraised 40,000,000 = 0.6
        self.assertEqual(v["value"], 0.6)
        self.assertIsNone(v["currency"])  # a ratio carries no currency
        # DUAL provenance: a Hypercore numerator + a KG denominator.
        num = v["provenance"]["numerator"]
        den = v["provenance"]["denominator"]
        self.assertEqual(num["source"], "hypercore")
        self.assertIn("raw_response_id", num)
        self.assertEqual(den["source"], "kg")
        self.assertEqual(den["node_id"], "deal:fixture-springwater")
        self.assertEqual(den["field"], "appraised_value")
        # the Hypercore numerator is resolvable back to its Tier-1 record.
        resolved, ok = self.cache.resolve_binding({
            "raw_response_id": num["raw_response_id"],
            "json_field_path": num["json_field_path"]})
        self.assertTrue(ok)
        self.assertEqual(resolved, 24000000.0)
        # CROSS-CHECK against the KG's stored ltv_latest 0.50: gap |0.6-0.5|=0.1 > 0.05 -> flagged.
        cc = env["gate_verdict"]["ltv_crosscheck"]
        self.assertEqual(cc["kg_ltv_latest"], 0.5)
        self.assertEqual(cc["computed_ltv"], 0.6)
        self.assertTrue(cc["diverges"])
        self.assertIn("CROSS-CHECK DIVERGENCE", env["answer"])
        # threshold breach: 0.6 < 0.75 max -> NOT breached
        self.assertFalse(env["gate_verdict"]["breach"]["breached"])

    def test_ltv_flags_covenant_breach_when_over_threshold(self):
        # a loan whose outstanding pushes LTV above the 0.75 max covenant.
        over = dict(_SUMMARY_SPRINGWATER)
        over = {**_SUMMARY_SPRINGWATER, "id": "779",
                "summary": {**_SUMMARY_SPRINGWATER["summary"],
                            "totalOutstanding": {**_SUMMARY_SPRINGWATER["summary"]["totalOutstanding"],
                                                 "total": 36000000.0}}}
        client = _SummaryFakeClient([over])
        reg = self._registry(client)
        env = reg.get("ltv").run(loan_id="779", loan_name="Springwater Fixture Loan")
        self.assertEqual(env["state"], figures_mod.STATE_DELIVERED, env.get("refusals"))
        # 36,000,000 / 40,000,000 = 0.9 > 0.75
        self.assertEqual(env["values"][0]["value"], 0.9)
        self.assertTrue(env["gate_verdict"]["breach"]["breached"])
        self.assertEqual(env["gate_verdict"]["breach"]["direction"], "max")
        self.assertIn("COVENANT BREACH", env["answer"])

    def test_ltv_refuses_when_no_kg_match(self):
        client = _SummaryFakeClient([_SUMMARY_BEEHIVE])
        reg = self._registry(client)
        env = reg.get("ltv").run(loan_id="134", loan_name="Beehive Waldorff Not In Fixture KG")
        self.assertEqual(env["state"], figures_mod.STATE_REFUSED)
        self.assertEqual(env["values"], [])  # NEVER a number
        self.assertEqual(env["refusals"][0]["reason_code"], figures_mod.REASON_KG_NO_MATCH)
        self.assertIn("knowledge graph", env["refusals"][0]["reason"].lower())

    def test_ltv_refuses_when_appraised_value_absent(self):
        # "Hollow Ridge" matches a KG node that has NO appraised_value -> KG_FIELD_MISSING.
        client = _SummaryFakeClient([{**_SUMMARY_SPRINGWATER, "id": "780",
                                      "name": "Hollow Ridge Loan"}])
        reg = self._registry(client)
        env = reg.get("ltv").run(loan_id="780", loan_name="Hollow Ridge Loan")
        self.assertEqual(env["state"], figures_mod.STATE_REFUSED)
        self.assertEqual(env["values"], [])
        self.assertEqual(env["refusals"][0]["reason_code"], figures_mod.REASON_KG_FIELD_MISSING)
        self.assertIn("appraised_value", env["refusals"][0]["reason"])


class LeverageCoverageTest(_LeverageFigBase):
    def test_debt_yield_computes_noi_over_commitment(self):
        client = _SummaryFakeClient([_SUMMARY_SPRINGWATER])
        reg = self._registry(client)
        env = reg.get("debt_yield").run(loan_id="777", loan_name="Springwater Fixture Loan")
        self.assertEqual(env["state"], figures_mod.STATE_DELIVERED, env.get("refusals"))
        # debt_yield = NOI 3,200,000 / commitment 25,000,000 = 0.128
        self.assertEqual(env["values"][0]["value"], 0.128)
        # 0.128 >= 0.08 min -> NOT breached
        self.assertFalse(env["gate_verdict"]["breach"]["breached"])
        # numerator from KG, denominator from Hypercore.
        self.assertEqual(env["values"][0]["provenance"]["numerator"]["source"], "kg")
        self.assertEqual(env["values"][0]["provenance"]["denominator"]["source"], "hypercore")

    def test_dscr_computes_noi_over_annual_debt_service(self):
        client = _SummaryFakeClient([_SUMMARY_SPRINGWATER])
        reg = self._registry(client)
        env = reg.get("dscr").run(loan_id="777", loan_name="Springwater Fixture Loan")
        self.assertEqual(env["state"], figures_mod.STATE_DELIVERED, env.get("refusals"))
        # DSCR = NOI 3,200,000 / (commitment 25,000,000 * rate 0.12 = 3,000,000) = 1.066667
        self.assertEqual(env["values"][0]["value"], round(3200000 / (25000000 * 0.12), 6))
        # 1.0667 < 1.25 min -> BREACH
        self.assertTrue(env["gate_verdict"]["breach"]["breached"])
        self.assertEqual(env["gate_verdict"]["breach"]["direction"], "min")
        # denominator is the derived annual debt service.
        self.assertEqual(env["values"][0]["provenance"]["denominator"]["formula"],
                         "annual_debt_service = commitment * interest_rate")

    def test_cap_rate_computes_noi_over_appraised(self):
        client = _SummaryFakeClient([_SUMMARY_SPRINGWATER])
        reg = self._registry(client)
        env = reg.get("cap_rate").run(loan_id="777", loan_name="Springwater Fixture Loan")
        self.assertEqual(env["state"], figures_mod.STATE_DELIVERED, env.get("refusals"))
        # cap_rate = NOI 3,200,000 / appraised 40,000,000 = 0.08
        self.assertEqual(env["values"][0]["value"], 0.08)
        # cap_rate has no covenant -> no breach record
        self.assertIsNone(env["gate_verdict"].get("breach"))

    def test_dscr_refuses_cleanly_when_noi_absent(self):
        # "Drycreek" matches a KG node WITH appraised_value but NO NOI -> DSCR refuses.
        client = _SummaryFakeClient([_SUMMARY_DRYCREEK])
        reg = self._registry(client)
        env = reg.get("dscr").run(loan_id="778", loan_name="Drycreek Fixture")
        self.assertEqual(env["state"], figures_mod.STATE_REFUSED)
        self.assertEqual(env["values"], [])
        self.assertEqual(env["refusals"][0]["reason_code"], figures_mod.REASON_KG_FIELD_MISSING)
        self.assertIn("NOI", env["refusals"][0]["reason"])

    def test_debt_yield_refuses_cleanly_when_noi_absent(self):
        client = _SummaryFakeClient([_SUMMARY_DRYCREEK])
        reg = self._registry(client)
        env = reg.get("debt_yield").run(loan_id="778", loan_name="Drycreek Fixture")
        self.assertEqual(env["state"], figures_mod.STATE_REFUSED)
        self.assertEqual(env["values"], [])
        self.assertEqual(env["refusals"][0]["reason_code"], figures_mod.REASON_KG_FIELD_MISSING)
        self.assertIn("NOI", env["refusals"][0]["reason"])


class LeverageMetaTest(_LeverageFigBase):
    def test_leverage_figures_carry_covenant_thresholds(self):
        client = _SummaryFakeClient([_SUMMARY_SPRINGWATER])
        reg = self._registry(client)
        env = reg.get("ltv").run(loan_id="777", loan_name="Springwater Fixture Loan")
        self.assertEqual(env["meta"]["covenant"]["threshold"], 0.75)
        self.assertEqual(env["meta"]["covenant"]["direction"], "max")
        env = reg.get("dscr").run(loan_id="777", loan_name="Springwater Fixture Loan")
        self.assertEqual(env["meta"]["covenant"]["threshold"], 1.25)
        env = reg.get("debt_yield").run(loan_id="777", loan_name="Springwater Fixture Loan")
        self.assertEqual(env["meta"]["covenant"]["threshold"], 0.08)

    def test_leverage_confidence_bounded_by_kg_node_confidence(self):
        # dual-source ratio is NOT single-source-capped, but it cannot exceed the KG node's own
        # confidence (0.95 here). It should equal min(kg_conf, 1.0) = 0.95.
        client = _SummaryFakeClient([_SUMMARY_SPRINGWATER])
        reg = self._registry(client)
        env = reg.get("ltv").run(loan_id="777", loan_name="Springwater Fixture Loan")
        self.assertEqual(env["values"][0]["confidence"], 0.95)
        self.assertFalse(env["meta"]["confidence_record"]["single_source"])

    def test_no_loan_id_refuses(self):
        client = _SummaryFakeClient([_SUMMARY_SPRINGWATER])
        reg = self._registry(client)
        env = reg.get("ltv").run(loan_id="", loan_name="Springwater Fixture Loan")
        self.assertEqual(env["state"], figures_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], figures_mod.REASON_BAD_INPUT)


class PayoffCurrencyTest(_NativeFigBase):
    def test_payoff_value_carries_currency_from_the_loan(self):
        # the payoff figure should attach currency=loan.currency via the summary fetcher.
        client = _SummaryFakeClient([_SUMMARY_BEEHIVE], components=_GROUND_TRUTH)
        reg = figures_mod.build_registry(client=client, cache=self.cache, engine=self.engine,
                                         sleep=_no_sleep)
        env = reg.get("payoff_as_of").run(loan_id="134", date="2026-06-30",
                                          loan_name="Beehive Waldorff")
        self.assertEqual(env["state"], figures_mod.STATE_DELIVERED, env.get("refusals"))
        self.assertEqual(env["values"][0]["value"], 31888682.99)
        self.assertEqual(env["values"][0]["currency"], "USD")  # carried from loan.currency


# ===========================================================================
# ONTOLOGY-DRIVEN PLANNER ROUTING THROUGH THE DELIVER SPINE (SLICE-HCA-13)
# ===========================================================================

class FigurePlannerRoutingTest(unittest.TestCase):
    def test_planner_routes_synonyms_to_the_right_figure(self):
        cases = {
            "what is the outstanding balance for Beehive": "outstanding_balance",
            "how much is drawn on Beehive": "total_disbursed",
            "what is the utilization for Beehive": "utilization",
            "what is the LTV for Beehive": "ltv",
            "what is the maturity date for Beehive": "maturity_date",
        }
        for q, fig in cases.items():
            plan = deliver_mod.plan_question(q)
            self.assertEqual(plan["intent"], "figure", q)
            self.assertEqual(plan["figure_name"], fig, q)
            self.assertEqual(plan["loan_name"], "Beehive", q)

    def test_portfolio_total_routes_to_figure_portfolio(self):
        plan = deliver_mod.plan_question("total outstanding across the portfolio")
        self.assertEqual(plan["intent"], "figure_portfolio")
        self.assertEqual(plan["figure_name"], "outstanding_balance")

    def test_existing_intents_unchanged(self):
        # regression: the slice-A intents must NOT be hijacked by figure routing.
        self.assertEqual(deliver_mod.plan_question(
            "what is the total commitment across all loans?")["intent"], "aggregate")
        self.assertEqual(deliver_mod.plan_question(
            "how many loans are there?")["intent"], "count")
        self.assertEqual(deliver_mod.plan_question(
            "what is the status of loan L-001?")["intent"], "lookup")
        self.assertEqual(deliver_mod.plan_question(
            "what is the payoff for Beehive Waldorff")["intent"], "payoff")

    def test_unmapped_concept_still_refuses(self):
        for q in ("who is the CEO of the company?", "how many giraffes are there?"):
            with self.assertRaises(deliver_mod.PlanError):
                deliver_mod.plan_question(q)


class FigureViaSpineTest(_NativeFigBase):
    """End-to-end: a figure question routes plan -> resolve loan -> figure -> envelope."""

    def _spine(self, *, client, resolve_loans, kg_store=None):
        resolver = resolve_mod.LoanResolver(client=_ResolveFakeClient(resolve_loans))
        registry = figures_mod.build_registry(client=client, cache=self.cache,
                                              engine=self.engine, sleep=_no_sleep,
                                              kg_store=kg_store)
        return deliver_mod.DeliverySpine(cache=self.cache, engine=self.engine,
                                         resolver=resolver, figures=registry)

    def test_outstanding_balance_question_delivers(self):
        spine = self._spine(client=_SummaryFakeClient([_SUMMARY_BEEHIVE]),
                            resolve_loans=_SPINE_LOANS)
        env = spine.ask("what is the outstanding balance for beehive")
        self.assertEqual(env["state"], "DELIVERED", env.get("refusals"))
        self.assertEqual(env["values"][0]["value"], 28145000.0)
        self.assertEqual(env["values"][0]["currency"], "USD")
        self.assertEqual(env["plan"]["intent"], "figure")
        self.assertEqual(env["plan"]["figure_name"], "outstanding_balance")
        self.assertIsNotNone(env["meta"]["echo"])  # resolution echo surfaced

    def test_utilization_question_delivers_with_formula(self):
        spine = self._spine(client=_SummaryFakeClient([_SUMMARY_BEEHIVE]),
                            resolve_loans=_SPINE_LOANS)
        env = spine.ask("what is the utilization for beehive")
        self.assertEqual(env["state"], "DELIVERED", env.get("refusals"))
        self.assertEqual(env["values"][0]["value"], 0.8)
        self.assertEqual(env["meta"]["formula"], "total_disbursed / commitment")

    def test_ltv_question_computes_through_the_spine_with_kg_join(self):
        # KG-JOINED (SLICE-HCA-14): an LTV question now resolves the loan AND joins the KG, then
        # COMPUTES the ratio with dual provenance + cross-check (fixture KG -> deterministic).
        kgdir = tempfile.mkdtemp(prefix="hca-kgfix-spine-")
        self.addCleanup(shutil.rmtree, kgdir, True)
        _write_fixture_kg(kgdir, _FIXTURE_KG_ROWS)
        kg_store = kg_mod.KGStore(kg_dir=kgdir)
        spine_loans = [{"id": "777", "name": "Springwater Fixture Loan", "status": "ACTIVE"}]
        spine = self._spine(client=_SummaryFakeClient([_SUMMARY_SPRINGWATER]),
                            resolve_loans=spine_loans, kg_store=kg_store)
        env = spine.ask("what is the LTV for Springwater Fixture Loan")
        self.assertEqual(env["state"], "DELIVERED", env.get("refusals"))
        self.assertEqual(env["values"][0]["value"], 0.6)  # 24M / 40M
        self.assertEqual(env["plan"]["figure_name"], "ltv")
        # dual provenance + cross-check survive the reshape into the spine envelope.
        self.assertEqual(env["values"][0]["provenance"]["numerator"]["source"], "hypercore")
        self.assertEqual(env["values"][0]["provenance"]["denominator"]["source"], "kg")
        self.assertTrue(env["gate_verdict"]["ltv_crosscheck"]["diverges"])
        self.assertIsNotNone(env["meta"]["echo"])  # resolution echo surfaced

    def test_ltv_question_refuses_when_loan_not_in_kg(self):
        # a loan that resolves on Hypercore but has NO KG match -> clean KG_NO_MATCH refusal.
        kgdir = tempfile.mkdtemp(prefix="hca-kgfix-spine2-")
        self.addCleanup(shutil.rmtree, kgdir, True)
        _write_fixture_kg(kgdir, _FIXTURE_KG_ROWS)
        kg_store = kg_mod.KGStore(kg_dir=kgdir)
        spine = self._spine(client=_SummaryFakeClient([_SUMMARY_BEEHIVE]),
                            resolve_loans=_SPINE_LOANS, kg_store=kg_store)
        env = spine.ask("what is the LTV for beehive")
        self.assertEqual(env["state"], "REFUSED")
        self.assertEqual(env["values"], [])
        self.assertEqual(env["refusals"][0]["reason_code"], figures_mod.REASON_KG_NO_MATCH)
        self.assertIn("knowledge graph", env["refusals"][0]["reason"].lower())

    def test_portfolio_total_outstanding_aggregates(self):
        # the resolver-enumerated portfolio must match the loans the summary client can serve
        # (in production both ride the SAME live client; the fixtures mirror that here).
        portfolio = [{"id": "134", "name": "Beehive Waldorff", "status": "ACTIVE"},
                     {"id": "303", "name": "Maple Grove Senior", "status": "ACTIVE"}]
        spine = self._spine(client=_SummaryFakeClient([_SUMMARY_BEEHIVE, _SUMMARY_MAPLE]),
                            resolve_loans=portfolio)
        env = spine.ask("total outstanding across the portfolio")
        self.assertEqual(env["state"], "DELIVERED", env.get("refusals"))
        # 28145000 + 5500000 == 33645000
        self.assertEqual(env["values"][0]["value"], 33645000.0)
        self.assertEqual(env["values"][0]["currency"], "USD")
        self.assertEqual(env["meta"]["loans"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
