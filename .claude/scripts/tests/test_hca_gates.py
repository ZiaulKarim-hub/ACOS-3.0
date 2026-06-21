#!/usr/bin/env python3
"""test_hca_gates.py — stdlib unittest for the deterministic gate suite (SLICE-HCA-05).

ADVERSARIAL by construction: for EACH of the six gates (+ schema_drift) there is a POSITIVE
test (a good fixture/record passes) AND a NEGATIVE test (a hostile fixture/record
demonstrably FAILS). The three required hard-failure proofs use the slice-02 adversarial
fixtures directly:

  - pagination_completeness FAILs on `list_loan_truncated__page1.json` (fetched 2 < total 3).
  - freshness            FAILs on `loan_stale__L-900.json` (timestamp 2024-01-01, far stale).
  - schema_drift         FAILs on `loan_drifted__L-901.json` (renamed/missing/extra fields).

Plus: GateSuite-level aggregate refusal (ANY hard FAIL => outcome == refuse), the
deterministic-only vs full tiered application, and the always-required provenance binding.

Run:
  python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py' -v
"""

import copy
import datetime
import importlib.util
import json
import os
import unittest


_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.abspath(os.path.join(_THIS_DIR, os.pardir))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPTS_DIR, os.pardir, os.pardir))
_FIXTURES = os.path.join(_REPO_ROOT, ".claude", "skills", "acos-hypercore-ask", "fixtures")
_SCHEMAS = os.path.join(_REPO_ROOT, ".claude", "skills", "acos-hypercore-ask", "schemas")


def _load(modname, filename):
    import sys
    cached = sys.modules.get(modname)
    if cached is not None:
        return cached
    path = os.path.join(_SCRIPTS_DIR, filename)
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


gates = _load("hca_gates", "hca-gates.py")
cache_mod = _load("hca_cache", "hca-cache.py")


def _fx(name):
    with open(os.path.join(_FIXTURES, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _schema(name):
    with open(os.path.join(_SCHEMAS, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# DATE-INDEPENDENCE helpers
# ---------------------------------------------------------------------------
# The freshness gate compares a record's fetched_at against `now` and a config window
# (loans: 1 day). A "fresh"/within-window fixture MUST therefore have a timestamp computed
# RELATIVE TO NOW at test time, or the test rots as the wall clock advances past the window.
#
# Two complementary primitives keep the suite date-independent:
#   * _fresh_now(ts) returns a `now` pinned 1 hour AFTER a fixture's fetched_at, so a fixture
#     stamped at any (even far-past) instant is judged fresh deterministically. Use this when
#     the fixture timestamp is the contract under test.
#   * _freshly_stamped(fx) returns a deep copy of a fixture whose every fetched_at/timestamp
#     field has been rewritten to (real now - 1 hour). The copy is fresh against the REAL
#     wall clock on ANY date, so it can be fed to a bare GateSuite() (now=None) and still pass.
# Together they ensure no "fresh" assertion depends on a hardcoded calendar date.

_ISO_Z = "%Y-%m-%dT%H:%M:%SZ"


def _real_now():
    return datetime.datetime.now(datetime.timezone.utc)


def _parse_ts(ts):
    """Tolerant parse of a fixture ISO timestamp (trailing Z or +00:00 or date-only)."""
    raw = (ts or "").strip()
    if not raw:
        return None
    iso = raw.replace("Z", "+00:00") if raw.endswith("Z") else raw
    try:
        dt = datetime.datetime.fromisoformat(iso)
    except ValueError:
        try:
            dt = datetime.datetime.strptime(raw, "%Y-%m-%d")
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(datetime.timezone.utc)


def _fresh_now(fetched_at):
    """A `now` 1 hour AFTER the given fetched_at — guarantees within-window regardless of
    the real date. Falls back to real-now+1h if the timestamp cannot be parsed."""
    dt = _parse_ts(fetched_at)
    if dt is None:
        return _real_now()
    return dt + datetime.timedelta(hours=1)


def _restamp(obj, new_iso):
    """Recursively rewrite every 'timestamp'/'fetched_at' string to new_iso (in place)."""
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if k in ("timestamp", "fetched_at") and isinstance(v, str):
                obj[k] = new_iso
            else:
                _restamp(v, new_iso)
    elif isinstance(obj, list):
        for it in obj:
            _restamp(it, new_iso)
    return obj


def _freshly_stamped(name_or_dict, *, minutes_ago=60):
    """Load a fixture (by name) or copy a dict, restamping all freshness timestamps to
    (real now - minutes_ago). The result is fresh against the REAL wall clock on ANY date,
    so it survives a bare GateSuite()/gate_freshness() call with no injected `now`."""
    fx = _fx(name_or_dict) if isinstance(name_or_dict, str) else copy.deepcopy(name_or_dict)
    when = (_real_now() - datetime.timedelta(minutes=minutes_ago)).strftime(_ISO_Z)
    return _restamp(fx, when)


# The canonical clean-fixture fetched_at the synthetic fixtures ship with. Tests that pin a
# deterministic `now` against the *unmodified* fixture use _fresh_now(_FIXTURE_FETCHED_AT) so
# the pin tracks the fixture, not a calendar date.
_FIXTURE_FETCHED_AT = "2026-06-18T08:00:00Z"


# ===========================================================================
# GATE 1 — schema_validation
# ===========================================================================

class SchemaValidationTest(unittest.TestCase):
    def setUp(self):
        self.schema = _schema("loan.schema.json")

    def test_PASS_clean_loan_matches_schema(self):
        res = gates.gate_schema_validation(_fx("loan__L-001.json"), self.schema)
        self.assertEqual(res["status"], gates.PASS, res["reason"])

    def test_FAIL_drifted_record_has_unknown_fields(self):
        # principal_outstanding (renamed) + legacy_balance (new) are unknown to the schema.
        res = gates.gate_schema_validation(_fx("loan_drifted__L-901.json"), self.schema)
        self.assertEqual(res["status"], gates.FAIL, res["reason"])
        unknown = {u["field"] for u in res["evidence"]["unknown_fields"]}
        self.assertIn("principal_outstanding", unknown)
        self.assertIn("legacy_balance", unknown)

    def test_FAIL_missing_required_field(self):
        rec = _fx("loan__L-001.json")
        del rec["body"]["loan_id"]  # required PK removed -> FAIL
        res = gates.gate_schema_validation(rec, self.schema)
        self.assertEqual(res["status"], gates.FAIL)
        missing = {m["field"] for m in res["evidence"]["missing_required"]}
        self.assertIn("loan_id", missing)


# ===========================================================================
# GATE 2 — pagination_completeness  (REQUIRED hard check)
# ===========================================================================

class PaginationCompletenessTest(unittest.TestCase):
    def test_PASS_gql_complete_list(self):
        # body.complete == True AND fetched == reported_total
        res = gates.gate_pagination_completeness(_fx("gql_list_loan__complete.json"))
        self.assertEqual(res["status"], gates.PASS, res["reason"])

    def test_FAIL_rest_truncated_fixture_required(self):
        # list_loan_truncated: reported_total=3 but only 2 items + cursor null -> must FAIL.
        res = gates.gate_pagination_completeness(_fx("list_loan_truncated__page1.json"))
        self.assertEqual(res["status"], gates.FAIL, res["reason"])
        self.assertEqual(res["evidence"]["fetched"], 2)
        self.assertEqual(res["evidence"]["reported_total"], 3)

    def test_FAIL_gql_truncated_complete_false(self):
        # GraphQL truncated fixture: complete=false, fetched 3 < total 5 -> must FAIL.
        res = gates.gate_pagination_completeness(_fx("gql_list_loan_truncated__short.json"))
        self.assertEqual(res["status"], gates.FAIL, res["reason"])

    def test_FAIL_near_miss_one_short_cannot_pass(self):
        # QA adversarial near-miss: fetched_count exactly one short of reported_total.
        near = {
            "entity_type": "loan", "list": True,
            "body": {"data": [{"loan_id": "L-1"}, {"loan_id": "L-2"}],
                     "fetched": 2, "reported_total": 3, "complete": True},
        }
        res = gates.gate_pagination_completeness(near)
        self.assertEqual(res["status"], gates.FAIL,
                         "pagination MUST NOT pass when fetched < reported_total")

    def test_FAIL_nonnull_cursor_with_matching_count(self):
        # Even if fetched==reported_total, a live next_cursor contradicts completeness.
        contradiction = {
            "entity_type": "loan", "list": True,
            "body": {"data": [{"loan_id": "L-1"}], "fetched": 1, "reported_total": 1,
                     "next_cursor": "MORE"},
        }
        res = gates.gate_pagination_completeness(contradiction)
        self.assertEqual(res["status"], gates.FAIL)

    def test_PASS_single_record_not_applicable(self):
        res = gates.gate_pagination_completeness(_fx("loan__L-001.json"))
        self.assertEqual(res["status"], gates.PASS)


# ===========================================================================
# GATE 3 — freshness  (REQUIRED hard check; window from config)
# ===========================================================================

class FreshnessTest(unittest.TestCase):
    def test_PASS_fresh_loan(self):
        # loan__L-001 timestamp is 2026-06-18 -> within the 1d balances window relative to now
        import datetime
        now = datetime.datetime(2026, 6, 18, 12, 0, 0, tzinfo=datetime.timezone.utc)
        res = gates.gate_freshness(_fx("loan__L-001.json"), "loan", now=now)
        self.assertEqual(res["status"], gates.PASS, res["reason"])

    def test_FAIL_stale_fixture_required(self):
        # loan_stale: 2024-01-01 -> far outside any window -> must FAIL.
        res = gates.gate_freshness(_fx("loan_stale__L-900.json"), "loan")
        self.assertEqual(res["status"], gates.FAIL, res["reason"])
        self.assertTrue(res["evidence"]["flag_refresh"])

    def test_window_comes_from_config_not_hardcoded(self):
        # The window the gate reports MUST equal the value hca-cache reads from config.yaml.
        from_config = cache_mod.freshness_window_days("loan")
        res = gates.gate_freshness(_fx("loan__L-001.json"), "loan")
        self.assertEqual(res["evidence"]["window_days"], from_config)
        # And the config value for the loan (balances_servicing) class is 1 day.
        self.assertEqual(from_config, 1)

    def test_FAIL_missing_timestamp(self):
        rec = _fx("loan__L-001.json")
        del rec["timestamp"]
        rec["body"].pop("provenance", None)
        res = gates.gate_freshness(rec, "loan")
        self.assertEqual(res["status"], gates.FAIL)

    def test_reference_static_window_is_longer(self):
        # A client/borrower (reference_static) gets the 30d window from config, not 1d.
        self.assertEqual(cache_mod.freshness_window_days("client"), 30)


# ===========================================================================
# GATE 4 — cross_field_reconciliation
# ===========================================================================

class ReconciliationTest(unittest.TestCase):
    def test_PASS_payment_allocation_sums_to_amount(self):
        # P-001: 100000 + 23000 + 2000 == 125000 == amount.
        res = gates.gate_cross_field_reconciliation(_fx("payment__P-001.json"))
        self.assertEqual(res["status"], gates.PASS, res["reason"])
        self.assertGreaterEqual(res["evidence"]["rules_fired"], 1)

    def test_FAIL_planted_allocation_inconsistency(self):
        bad = _fx("payment__P-001.json")
        bad["body"]["allocation"]["fees"] = 9999  # 100000+23000+9999 != 125000
        res = gates.gate_cross_field_reconciliation(bad)
        self.assertEqual(res["status"], gates.FAIL, res["reason"])

    def test_PASS_loan_funded_reconciles_to_outstanding_plus_repaid(self):
        loan = _fx("loan__L-001.json")
        # funded 4_200_000 == outstanding 3_900_000 + repaid 300_000
        loan["body"]["repaid_principal"] = 300000
        res = gates.gate_cross_field_reconciliation(loan)
        self.assertEqual(res["status"], gates.PASS, res["reason"])

    def test_FAIL_planted_loan_arithmetic_inconsistency(self):
        loan = _fx("loan__L-001.json")
        loan["body"]["repaid_principal"] = 1  # 3_900_000 + 1 != 4_200_000
        res = gates.gate_cross_field_reconciliation(loan)
        self.assertEqual(res["status"], gates.FAIL)

    def test_PASS_vacuous_when_no_rule_applies(self):
        # A bare record with no reconcilable fields -> vacuously consistent (rules_fired 0).
        res = gates.gate_cross_field_reconciliation(
            {"entity_type": "loan", "body": {"loan_id": "L-X", "status": "active"}})
        self.assertEqual(res["status"], gates.PASS)
        self.assertEqual(res["evidence"]["rules_fired"], 0)


# ===========================================================================
# GATE 5 — unit_currency_normalization
# ===========================================================================

class NormalizationTest(unittest.TestCase):
    def test_PASS_per_record_known_currency(self):
        res = gates.gate_unit_currency_normalization(_fx("loan__L-001.json"))
        self.assertEqual(res["status"], gates.PASS, res["reason"])

    def test_FAIL_aggregate_mixed_currencies(self):
        mixed = {"entity_type": "loan", "list": True, "body": {"data": [
            {"loan_id": "L-1", "outstanding_principal": 100, "currency": "USD"},
            {"loan_id": "L-2", "outstanding_principal": 200, "currency": "EUR"},
        ]}}
        res = gates.gate_unit_currency_normalization(mixed, aggregating=True)
        self.assertEqual(res["status"], gates.FAIL, res["reason"])
        self.assertEqual(sorted(res["evidence"]["currencies"]), ["EUR", "USD"])

    def test_PASS_aggregate_single_currency(self):
        same = {"entity_type": "loan", "list": True, "body": {"data": [
            {"loan_id": "L-1", "outstanding_principal": 100, "currency": "USD"},
            {"loan_id": "L-2", "outstanding_principal": 200, "currency": "USD"},
        ]}}
        res = gates.gate_unit_currency_normalization(same, aggregating=True)
        self.assertEqual(res["status"], gates.PASS, res["reason"])

    def test_FAIL_present_but_unknown_currency(self):
        bad = {"entity_type": "loan",
               "body": {"loan_id": "L-X", "outstanding_principal": 100, "currency": "ZZZ"}}
        res = gates.gate_unit_currency_normalization(bad)
        self.assertEqual(res["status"], gates.FAIL)

    def test_FAIL_non_numeric_money(self):
        bad = {"entity_type": "loan",
               "body": {"loan_id": "L-X", "outstanding_principal": "lots", "currency": "USD"}}
        res = gates.gate_unit_currency_normalization(bad)
        self.assertEqual(res["status"], gates.FAIL)

    def test_normalize_money_canonicalizes_currency_case(self):
        norm = gates.normalize_money(100, "usd")
        self.assertEqual(norm["currency"], "USD")
        self.assertTrue(norm["ok"])

    def test_can_aggregate_mixed_returns_false(self):
        ok, currencies, _ = gates.can_aggregate([
            gates.normalize_money(1, "USD"), gates.normalize_money(2, "GBP")])
        self.assertFalse(ok)
        self.assertEqual(currencies, ["GBP", "USD"])


# ===========================================================================
# GATE 6 — single_source_confidence_cap
# ===========================================================================

class ConfidenceCapTest(unittest.TestCase):
    def test_PASS_single_source_capped_and_flagged(self):
        res = gates.gate_single_source_confidence_cap("val:x", source_count=1, agreement=0.99)
        self.assertEqual(res["status"], gates.PASS)
        rec = res["evidence"]["confidence_record"]
        self.assertTrue(rec["single_source"])
        self.assertLessEqual(rec["confidence"], 0.7)

    def test_single_source_never_exceeds_cap_regardless_of_self_confidence(self):
        # Adversarial: agent claims 1.0 self-confidence; cap MUST still hold.
        for claimed in (0.8, 0.9, 0.95, 1.0):
            res = gates.gate_single_source_confidence_cap(
                "val:x", source_count=1, agreement=claimed)
            self.assertLessEqual(
                res["evidence"]["confidence_record"]["confidence"], 0.7,
                f"single-source confidence exceeded cap for claimed={claimed}")

    def test_multi_source_not_capped(self):
        res = gates.gate_single_source_confidence_cap("val:x", source_count=3, agreement=0.9)
        rec = res["evidence"]["confidence_record"]
        self.assertFalse(rec["single_source"])
        self.assertGreater(rec["confidence"], 0.7)

    def test_cap_value_comes_from_config(self):
        res = gates.gate_single_source_confidence_cap("val:x", source_count=1)
        self.assertEqual(res["evidence"]["cap"], 0.7)


# ===========================================================================
# GATE 7 (drift) — schema_drift  (REQUIRED hard check on loan_drifted)
# ===========================================================================

class SchemaDriftTest(unittest.TestCase):
    def test_PASS_clean_loan_no_drift(self):
        res = gates.gate_schema_drift(_fx("loan__L-001.json"), "loan")
        self.assertEqual(res["status"], gates.PASS, res["reason"])

    def test_FAIL_drifted_fixture_required(self):
        # loan_drifted: outstanding_principal -> principal_outstanding, currency missing,
        # legacy_balance appears -> must FAIL.
        res = gates.gate_schema_drift(_fx("loan_drifted__L-901.json"), "loan")
        self.assertEqual(res["status"], gates.FAIL, res["reason"])
        added = {a["field"] for a in res["evidence"]["added_fields"]}
        missing = {m["field"] for m in res["evidence"]["missing_fields"]}
        self.assertIn("principal_outstanding", added)
        self.assertIn("legacy_balance", added)
        self.assertIn("currency", missing)  # required field dropped

    def test_FAIL_type_changed_field(self):
        # Coarse type-drift vs placeholder schema: commitment_amount as a string.
        rec = _fx("loan__L-001.json")
        rec["body"]["commitment_amount"] = "5000000"  # string where schema says number
        res = gates.gate_schema_drift(rec, "loan")
        self.assertEqual(res["status"], gates.FAIL)
        changed = {(t["field"], t["expected"], t["observed"])
                   for t in res["evidence"]["type_changed"]}
        self.assertIn(("commitment_amount", "number", "string"), changed)

    def test_introspection_map_matches_gql_schema_file(self):
        # The drift gate's introspection-derived type map for `Loan` must reproduce the
        # authoritative loan.gql.schema.json type strings (proves the live reference is used).
        gql_schema = _schema("loan.gql.schema.json")
        intro = gates._introspection_field_map("loan", gql_schema)
        self.assertIsNotNone(intro, "introspection map should resolve for GraphQL Loan type")
        for field in ("id", "refId", "status", "commitment", "currency", "fundingSources"):
            self.assertEqual(intro[field], gql_schema["expected_fields"][field],
                             f"type drift in {field}")

    def test_PASS_gql_single_loan_against_introspection(self):
        # The GraphQL single-loan fixture's fields all exist in the live Loan introspection.
        res = gates.gate_schema_drift(_fx("gql_loan__L-GQL-1.json"), "loan",
                                      schema=_schema("loan.gql.schema.json"))
        self.assertEqual(res["status"], gates.PASS, res["reason"])


# ===========================================================================
# GateSuite — aggregate refusal + tiered application + provenance binding
# ===========================================================================

class GateSuiteTest(unittest.TestCase):
    def setUp(self):
        # Pin `now` to the fixtures' fetched_at so within-window cases are deterministic and
        # date-independent (the suite never compares against the moving wall clock here).
        self.now = _fresh_now(_FIXTURE_FETCHED_AT)
        self.suite = gates.GateSuite(now=self.now)

    def test_full_suite_PASSES_clean_gql_complete_report(self):
        # DATE-INDEPENDENT: freshly restamp the fixture to (real now - 1h) AND run with a
        # bare GateSuite() (now=None -> real wall clock). The freshness gate therefore sees a
        # 1-hour-old record on whatever the current date is, so this PASSES on ANY date.
        fresh_fx = _freshly_stamped("gql_list_loan__complete.json")
        suite = gates.GateSuite()  # no injected now -> uses the real clock
        v = suite.run_all(fresh_fx, entity_type="loan",
                          prefer_graphql=True, source_count=2)
        self.assertEqual(v["outcome"], gates.OUTCOME_PASS, v["failures"])
        self.assertEqual(v["failures"], [])
        # Every per-gate boolean is reported.
        for key in ("schema_ok", "pagination_complete", "freshness_ok",
                    "reconciliation_ok", "normalization_applied", "confidence_capped",
                    "schema_drift_ok"):
            self.assertIn(key, v)

    def test_full_suite_REFUSES_on_truncated_list(self):
        v = self.suite.run_all(_fx("list_loan_truncated__page1.json"), entity_type="loan",
                               source_count=2)
        self.assertEqual(v["outcome"], gates.OUTCOME_REFUSE)
        self.assertIn(gates.GATE_PAGINATION, v["failures"])

    def test_full_suite_REFUSES_on_stale(self):
        v = self.suite.run_all(_fx("loan_stale__L-900.json"), entity_type="loan",
                               source_count=2)
        self.assertEqual(v["outcome"], gates.OUTCOME_REFUSE)
        self.assertIn(gates.GATE_FRESHNESS, v["failures"])

    def test_full_suite_REFUSES_on_drift(self):
        v = self.suite.run_all(_fx("loan_drifted__L-901.json"), entity_type="loan",
                               source_count=2)
        self.assertEqual(v["outcome"], gates.OUTCOME_REFUSE)
        self.assertIn(gates.GATE_DRIFT, v["failures"])

    def test_any_single_hard_fail_forces_refuse(self):
        # A clean single loan but with a planted reconciliation break -> refuse.
        loan = _fx("loan__L-001.json")
        loan["body"]["repaid_principal"] = 1  # breaks funded == outstanding + repaid
        v = self.suite.run_all(loan, entity_type="loan", source_count=2)
        self.assertEqual(v["outcome"], gates.OUTCOME_REFUSE)
        self.assertIn(gates.GATE_RECONCILIATION, v["failures"])

    def test_confidence_cap_alone_does_not_refuse(self):
        # Single-source value: confidence_capped is True (cap applied) but it is NOT a hard
        # gate, so a clean single-source single-record lookup still PASSES.
        import datetime
        now = datetime.datetime(2026, 6, 18, 12, 0, 0, tzinfo=datetime.timezone.utc)
        suite = gates.GateSuite(now=now)
        v = suite.run_all(_fx("loan__L-001.json"), entity_type="loan", source_count=1)
        self.assertEqual(v["outcome"], gates.OUTCOME_PASS, v["failures"])
        self.assertTrue(v["confidence_capped"])
        self.assertLessEqual(v["confidence"]["confidence"], 0.7)

    # --- tiered application ------------------------------------------------
    def test_deterministic_subset_skips_pagination_and_reconciliation(self):
        import datetime
        now = datetime.datetime(2026, 6, 18, 12, 0, 0, tzinfo=datetime.timezone.utc)
        suite = gates.GateSuite(now=now)
        v = suite.deterministic_subset(_fx("loan__L-001.json"), entity_type="loan")
        self.assertEqual(v["tier"], "deterministic-only")
        ran = {g["gate"] for g in v["gates"]}
        self.assertIn(gates.GATE_SCHEMA, ran)
        self.assertIn(gates.GATE_FRESHNESS, ran)
        self.assertIn(gates.GATE_DRIFT, ran)
        self.assertIn(gates.GATE_CONFIDENCE, ran)
        self.assertNotIn(gates.GATE_PAGINATION, ran)
        self.assertNotIn(gates.GATE_RECONCILIATION, ran)
        self.assertEqual(v["outcome"], gates.OUTCOME_PASS, v["failures"])

    def test_deterministic_subset_still_refuses_stale(self):
        v = self.suite.deterministic_subset(_fx("loan_stale__L-900.json"), entity_type="loan")
        self.assertEqual(v["outcome"], gates.OUTCOME_REFUSE)
        self.assertIn(gates.GATE_FRESHNESS, v["failures"])

    def test_full_tier_runs_all_seven_gates(self):
        v = self.suite.run_all(_fx("gql_list_loan__complete.json"), entity_type="loan",
                               prefer_graphql=True, source_count=2)
        self.assertEqual(v["tier"], "full")
        ran = {g["gate"] for g in v["gates"]}
        self.assertEqual(ran, {
            gates.GATE_SCHEMA, gates.GATE_PAGINATION, gates.GATE_FRESHNESS,
            gates.GATE_RECONCILIATION, gates.GATE_NORMALIZATION,
            gates.GATE_CONFIDENCE, gates.GATE_DRIFT})

    # --- provenance binding always required regardless of tier -------------
    def test_failed_provenance_report_forces_refuse_even_when_gates_pass(self):
        import datetime
        now = datetime.datetime(2026, 6, 18, 12, 0, 0, tzinfo=datetime.timezone.utc)
        suite = gates.GateSuite(now=now)
        prov = {"ok": False, "checked": 1, "verified": 0,
                "refusals": [{"field": "outstanding_principal", "reason": "unbound"}]}
        v = suite.run_all(_fx("loan__L-001.json"), entity_type="loan", source_count=2,
                          provenance_report=prov)
        self.assertEqual(v["outcome"], gates.OUTCOME_REFUSE)
        self.assertIn("provenance_binding", v["failures"])

    def test_passing_provenance_report_allows_pass(self):
        import datetime
        now = datetime.datetime(2026, 6, 18, 12, 0, 0, tzinfo=datetime.timezone.utc)
        suite = gates.GateSuite(now=now)
        prov = {"ok": True, "checked": 3, "verified": 3, "refusals": []}
        v = suite.run_all(_fx("loan__L-001.json"), entity_type="loan", source_count=2,
                          provenance_report=prov)
        self.assertEqual(v["outcome"], gates.OUTCOME_PASS, v["failures"])
        self.assertTrue(v["provenance_ok"])


# ===========================================================================
# QA-re-authored adversarial fixtures (independent of slice-02 fixtures)
# ===========================================================================

class QAReauthoredAdversarialTest(unittest.TestCase):
    """QA independently re-authors the truncated + stale hostile cases (not reusing the
    slice-02 fixture files) to prove the gates catch the failure mode, not the fixture."""

    def test_qa_truncated_list_fails(self):
        truncated = {
            "entity_type": "loan", "list": True, "timestamp": "2026-06-18T08:00:00Z",
            "reported_total": 10,
            "body": {"data": [{"loan_id": f"L-{i}"} for i in range(7)],  # 7 of 10
                     "fetched": 7, "reported_total": 10, "complete": False},
        }
        res = gates.gate_pagination_completeness(truncated)
        self.assertEqual(res["status"], gates.FAIL)

    def test_qa_stale_record_fails(self):
        stale = {
            "entity_type": "loan", "timestamp": "2020-05-05T00:00:00Z",
            "body": {"loan_id": "L-QA", "outstanding_principal": 1, "currency": "USD"},
        }
        res = gates.gate_freshness(stale, "loan")
        self.assertEqual(res["status"], gates.FAIL)


if __name__ == "__main__":
    unittest.main(verbosity=2)
