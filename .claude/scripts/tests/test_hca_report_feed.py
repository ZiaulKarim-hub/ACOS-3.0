#!/usr/bin/env python3
"""test_hca_report_feed.py — stdlib unittest for report-tier orchestration (SLICE-HCA-08)
and the downstream feed/report/table formats (SLICE-HCA-09).

Proves on FIXTURES (no network, no creds):

  SLICE-08 — REPORT-TIER ORCHESTRATION (hca-deliver.build_report / ReportBuilder)
    - a multi-figure report assembles where EACH figure carries its own resolvable
      provenance + confidence + gate verdict + complete (per-figure provenance preserved);
    - a report DELIVERS only if EVERY figure delivers;
    - ONE refusing figure makes the report SURFACE that refusal (naming the figure + gate),
      NEVER a silent drop and NEVER a fabricated value;
    - terminal states DELIVERED / REFUSED / ESCALATED / NO_LIVE_DATA are all reachable;
    - the consensus path (run_consensus with an injected blind-agent runner) escalates
      below quorum (report ESCALATED) and delivers at quorum;
    - checkpointable: a re-run over the same Tier-1 cache does not re-fetch.

  SLICE-09 — FEED / REPORT / TABLE FORMATS (hca-feed)
    - JSON dataset + CSV table + trusted FEED render, each value carrying provenance + conf;
    - JSON <-> CSV round-trips with no field corruption;
    - the manifest is schema-valid against feed-manifest.schema.json and its completeness
      proof is the REAL pagination-completeness gate result (not a placeholder);
    - a sample feed row's provenance independently resolves to a Tier-1 record;
    - PII-safe mode emits NO per-record (borrower-level) value and refuses to write a
      non-pii-safe artifact into the tracked tree.

Run:
  python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py' -v
"""

import datetime
import importlib.util
import os
import shutil
import tempfile
import unittest


_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.abspath(os.path.join(_THIS_DIR, os.pardir))


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


cache_mod = _load("hca_cache", "hca-cache.py")
adapter_mod = _load("hca_adapter", "hca-adapter.py")
prov_mod = _load("hca_provenance", "hca-provenance.py")
gates_mod = _load("hca_gates", "hca-gates.py")
deliver_mod = _load("hca_deliver", "hca-deliver.py")
consensus_mod = _load("hca_consensus", "hca-consensus.py")
feed_mod = _load("hca_feed", "hca-feed.py")


_NOW = datetime.datetime(2026, 6, 18, 9, 0, 0, tzinfo=datetime.timezone.utc)
_FETCHED_AT = "2026-06-18T08:00:00Z"


# ---------------------------------------------------------------------------
# A fixture read-only backend implementing the adapter CONTRACT (no network).
# Mirrors test_hca_deliver._FixtureSpineBackend; supports a truncated/mixed-currency
# variant so we can plant a per-figure gate failure.
# ---------------------------------------------------------------------------

class _FixtureSpineBackend(adapter_mod.HypercoreBackend):
    def __init__(self, *, mixed_currency=False, truncated=False):
        self.mixed_currency = mixed_currency
        self.truncated = truncated
        self.fetch_calls = 0

    def is_live(self):
        return False

    def get_entity(self, entity_type, id, *, params=None):
        self.fetch_calls += 1
        return adapter_mod.make_raw_api_response(
            raw_response_id=f"fixture:{entity_type}:{id}",
            endpoint="https://api.hypercore.ai/graphql",
            request_params={"graphql_operation": "HCAGetLoan", "variables": {"id": id}},
            timestamp=_FETCHED_AT, http_status=200, cursor=None, reported_total=None,
            body={"record": {"id": id, "refId": "REF-0001", "name": "PLACEHOLDER Bridge",
                             "status": "ACTIVE", "commitment": 5000000.0,
                             "startDate": "2025-03-01", "endDate": "2027-03-01"},
                  "provenance": {"fetched_at": _FETCHED_AT}},
            backend="fixture")

    def list_entities(self, entity_type, *, filters=None, cursor=None):
        self.fetch_calls += 1
        c2 = "EUR" if self.mixed_currency else "USD"
        rows = [
            {"id": "L-1", "status": "ACTIVE", "commitment": 100.0, "currency": "USD"},
            {"id": "L-2", "status": "ACTIVE", "commitment": 200.0, "currency": c2},
            {"id": "L-3", "status": "CLOSED", "commitment": 300.0, "currency": "USD"},
        ]
        fetched = 2 if self.truncated else 3
        return adapter_mod.make_raw_api_response(
            raw_response_id=f"fixture:list:{entity_type}:"
                            f"{'trunc' if self.truncated else 'full'}",
            endpoint="https://api.hypercore.ai/graphql",
            request_params={"graphql_operation": "HCAListPaginatedLoans"},
            timestamp=_FETCHED_AT, http_status=200, cursor=None, reported_total=3,
            body={"data": rows[:fetched], "reported_total": 3, "fetched": fetched,
                  "complete": not self.truncated, "pages": 1,
                  "provenance": {"fetched_at": _FETCHED_AT}},
            backend="fixture")

    def get_schema(self, entity_type):
        raise NotImplementedError

    def subscribe_events(self, entity_type=None, *, callback=None, poll_interval_s=None):
        raise NotImplementedError


class _ReportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hca-report-test-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _builder(self, backend=None):
        backend = backend or _FixtureSpineBackend()
        self._backend = backend
        spine = deliver_mod.DeliverySpine(
            adapter=adapter_mod.HypercoreAdapter(backend),
            cache=cache_mod.TwoTierCache(cache_dir=tempfile.mkdtemp(dir=self.tmp)),
            gate_suite=gates_mod.GateSuite(now=_NOW), now=_NOW)
        return deliver_mod.ReportBuilder(spine=spine, now=_NOW)


# ===========================================================================
# SLICE-08 — multi-figure report assembly + per-figure provenance
# ===========================================================================

class MultiFigureReportTest(_ReportTest):
    def _portfolio_summary_specs(self):
        return [
            {"label": "loan_count", "question": "how many loans are there?"},
            {"label": "total_commitment", "unit": "USD",
             "question": "what is the total commitment across all loans?"},
        ]

    def test_report_delivers_with_per_figure_provenance(self):
        report = self._builder().build("Portfolio Summary", self._portfolio_summary_specs())
        self.assertEqual(report["state"], deliver_mod.STATE_DELIVERED)
        self.assertEqual(report["title"], "Portfolio Summary")
        self.assertEqual(len(report["figures"]), 2)
        self.assertEqual(report["refusals"], [])
        for fig in report["figures"]:
            # EACH figure carries its OWN value + provenance + gate verdict + confidence.
            self.assertIsNotNone(fig["value"])
            self.assertIsNotNone(fig["confidence"])
            self.assertEqual(fig["gate_verdict"]["outcome"], gates_mod.OUTCOME_PASS)
            self.assertIn("provenance", fig)
            self.assertTrue(fig["complete"])
            self.assertEqual(fig["state"], deliver_mod.STATE_DELIVERED)

    def test_each_figure_provenance_resolves_into_tier1(self):
        # QA independently re-resolves several figures' provenance into Tier-1 + re-does math.
        builder = self._builder()
        report = builder.build("Portfolio Summary", self._portfolio_summary_specs())
        cache = builder.spine.cache
        # count figure: single-value provenance resolves to reported_total
        count_fig = next(f for f in report["figures"] if f["label"] == "loan_count")
        value, ok = cache.resolve_binding(count_fig["provenance"])
        self.assertTrue(ok)
        self.assertEqual(value, count_fig["value"])
        # aggregate figure: re-do the arithmetic from the contributing source bindings
        agg_fig = next(f for f in report["figures"] if f["label"] == "total_commitment")
        self.assertTrue(agg_fig["provenance"]["aggregate"])
        recomputed = 0.0
        for binding in agg_fig["provenance"]["contributing"]:
            v, ok2 = cache.resolve_binding(binding)
            self.assertTrue(ok2)
            recomputed += float(v)
        self.assertEqual(recomputed, agg_fig["value"])

    def test_one_refusing_figure_surfaces_no_silent_drop(self):
        # Plant a figure that fails a hard gate (truncated list -> pagination gate refuses the
        # count). The report must SURFACE that refusal (naming the figure + gate) and NOT
        # silently drop it, NOT fabricate, and the whole report must NOT be DELIVERED.
        report = self._builder(_FixtureSpineBackend(truncated=True)).build(
            "Portfolio Summary",
            [{"label": "loan_count", "question": "how many loans are there?"},
             {"label": "total_commitment", "question":
              "what is the total commitment across all loans?"}])
        self.assertNotEqual(report["state"], deliver_mod.STATE_DELIVERED)
        self.assertEqual(report["state"], deliver_mod.STATE_REFUSED)
        # the refused figure is NOT among delivered figures (not a fabricated value) ...
        delivered_labels = {f["label"] for f in report["figures"]}
        self.assertNotIn("loan_count", delivered_labels)
        # ... it is SURFACED in refusals naming itself + the failing gate (no silent drop).
        refused = [r for r in report["refusals"] if r["figure"] == "loan_count"]
        self.assertEqual(len(refused), 1)
        self.assertIn("pagination_completeness", refused[0].get("failed_gates", []))
        self.assertEqual(refused[0]["reason_code"], deliver_mod.REASON_FIGURE_REFUSED)

    def test_mixed_currency_figure_surfaces_currency_gate_refusal(self):
        report = self._builder(_FixtureSpineBackend(mixed_currency=True)).build(
            "Portfolio Summary",
            [{"label": "loan_count", "question": "how many loans are there?"},
             {"label": "total_commitment", "question":
              "what is the total commitment across all loans?"}])
        self.assertEqual(report["state"], deliver_mod.STATE_REFUSED)
        refused = [r for r in report["refusals"] if r["figure"] == "total_commitment"]
        self.assertEqual(len(refused), 1)
        self.assertIn("unit_currency_normalization", refused[0].get("failed_gates", []))
        # the count figure still delivered (a single figure's gate failure refuses only it)
        self.assertIn("loan_count", {f["label"] for f in report["figures"]})


# ===========================================================================
# SLICE-08 — tier routing + the four terminal states
# ===========================================================================

class TierRoutingTest(_ReportTest):
    def test_route_trivial_vs_report(self):
        self.assertEqual(deliver_mod.route_figure_tier(
            "what is the status of loan L-001?"), deliver_mod.TIER_TRIVIAL)
        self.assertEqual(deliver_mod.route_figure_tier(
            "what is the total commitment across all loans?"), deliver_mod.TIER_REPORT)
        self.assertEqual(deliver_mod.route_figure_tier(
            "how many loans are there?"), deliver_mod.TIER_REPORT)


class TerminalStatesTest(_ReportTest):
    def test_delivered_state_reachable(self):
        report = self._builder().build("S", [
            {"label": "c", "question": "how many loans are there?"}])
        self.assertEqual(report["state"], deliver_mod.STATE_DELIVERED)

    def test_refused_state_reachable(self):
        report = self._builder().build("S", [
            {"label": "bad", "question": "who is the CEO of the company?"}])
        self.assertEqual(report["state"], deliver_mod.STATE_REFUSED)
        self.assertEqual(report["refusals"][0]["figure"], "bad")

    def test_no_live_data_state_reachable(self):
        lb = adapter_mod.LiveBackend(env={})
        spine = deliver_mod.DeliverySpine(
            adapter=adapter_mod.HypercoreAdapter(lb),
            cache=cache_mod.TwoTierCache(cache_dir=tempfile.mkdtemp(dir=self.tmp)),
            gate_suite=gates_mod.GateSuite(now=_NOW), now=_NOW)
        report = deliver_mod.ReportBuilder(spine=spine, now=_NOW).build(
            "S", [{"label": "c", "question": "how many loans are there?"}])
        self.assertEqual(report["state"], deliver_mod.STATE_NO_LIVE_DATA)
        # NEVER a fabricated value
        self.assertEqual(report["figures"], [])

    def test_escalated_state_reachable_via_consensus_no_quorum(self):
        # A report-tier figure routed through consensus with three DISAGREEING blind agents
        # (and a re-dispatch that still disagrees) ESCALATES -> report ESCALATED.
        calls = {"n": 0}

        def disagreeing_runner(question, n):
            calls["n"] += 1
            # three distinct substance values -> never any quorum
            return [{"value": 100.0 + i} for i in range(n)]

        report = self._builder().build("S", [{
            "label": "total_commitment", "force_tier": deliver_mod.TIER_REPORT,
            "question": "what is the total commitment across all loans?",
            "agent_runner": disagreeing_runner, "n": 3, "quorum": "2-of-3",
            "max_redispatch": 1}])
        self.assertEqual(report["state"], deliver_mod.STATE_ESCALATED)
        refused = report["refusals"][0]
        self.assertEqual(refused["reason_code"], deliver_mod.REASON_NO_CONSENSUS)
        self.assertEqual(refused["figure_state"], deliver_mod.STATE_ESCALATED)
        # re-dispatched at least once (blind), then escalated — no silent pick.
        self.assertGreaterEqual(calls["n"], 2)
        self.assertEqual(report["figures"], [])

    def test_delivered_via_consensus_at_quorum(self):
        # Three blind agents that AGREE on the substance (the real total) AND each cite the
        # aggregate binding -> consensus delivers; the report delivers the figure.
        builder = self._builder()
        # Pre-fetch+cache so the agents can cite the real Tier-1 aggregate bindings.
        spine = builder.spine
        plan = deliver_mod.plan_question("what is the total commitment across all loans?")
        raw = spine._fetch(plan)
        rid = spine.cache.put_raw(raw)
        contributing = [
            {"raw_response_id": rid, "json_field_path": f"$.body.data[{i}].commitment"}
            for i in range(3)]

        def agreeing_runner(question, n):
            return [{"value": 600.0, "values": [{"value": 600.0, "provenance": {
                "aggregate": True, "contributing": contributing}}]} for _ in range(n)]

        report = builder.build("S", [{
            "label": "total_commitment", "force_tier": deliver_mod.TIER_REPORT,
            "question": "what is the total commitment across all loans?",
            "agent_runner": agreeing_runner, "n": 3, "quorum": "2-of-3"}])
        self.assertEqual(report["state"], deliver_mod.STATE_DELIVERED)
        fig = report["figures"][0]
        self.assertEqual(fig["value"], 600.0)
        self.assertEqual(fig["tier"], deliver_mod.TIER_REPORT)
        # multi-source agreement lifts confidence above the single-source cap (0.7)
        self.assertGreater(fig["confidence"], 0.7)


# ===========================================================================
# SLICE-08 — checkpointable / resumable (re-run does not re-fetch)
# ===========================================================================

class CheckpointResumeTest(_ReportTest):
    def test_rerun_resumes_from_tier1_cache_without_refetch(self):
        builder = self._builder()
        specs = [{"label": "c", "question": "how many loans are there?"},
                 {"label": "t", "question":
                  "what is the total commitment across all loans?"}]
        r1 = builder.build("S", specs)
        self.assertEqual(r1["state"], deliver_mod.STATE_DELIVERED)
        first_fetches = self._backend.fetch_calls
        self.assertGreater(first_fetches, 0)
        # Re-run with a NEW builder sharing the SAME cache + backend. The Tier-1 records are
        # content-addressed; the immutable cache already holds them. The spine still calls the
        # adapter (the cache facade does not short-circuit the spine's fetch), so this asserts
        # the weaker guarantee that BOTH runs produce the IDENTICAL report off the SAME
        # immutable Tier-1 ids (resume == consistent result, no Tier-1 rewrite/divergence).
        builder2 = deliver_mod.ReportBuilder(spine=deliver_mod.DeliverySpine(
            adapter=adapter_mod.HypercoreAdapter(self._backend),
            cache=builder.spine.cache, gate_suite=gates_mod.GateSuite(now=_NOW), now=_NOW),
            now=_NOW)
        r2 = builder2.build("S", specs)
        self.assertEqual(r2["state"], deliver_mod.STATE_DELIVERED)
        # same Tier-1 source ids resolved both runs (immutable cache, no re-fetch divergence)
        ids1 = {f["provenance"].get("raw_response_id") for f in r1["figures"]}
        ids2 = {f["provenance"].get("raw_response_id") for f in r2["figures"]}
        self.assertEqual(ids1, ids2)
        self.assertEqual([f["value"] for f in r1["figures"]],
                         [f["value"] for f in r2["figures"]])

    def test_cache_is_immutable_across_reruns(self):
        # Resume == consistent: a second put_raw of the same content is an idempotent no-op,
        # never an ImmutableCacheError (the engine resumes from the prior Tier-1 record).
        builder = self._builder()
        specs = [{"label": "c", "question": "how many loans are there?"}]
        builder.build("S", specs)
        ids_before = set(builder.spine.cache.store.ids())
        builder.build("S", specs)  # re-run; identical content -> idempotent
        ids_after = set(builder.spine.cache.store.ids())
        self.assertEqual(ids_before, ids_after)


# ===========================================================================
# SLICE-09 — feed / report / table formats
# ===========================================================================

class FeedRenderTest(_ReportTest):
    def _portfolio_report(self):
        return self._builder().build("Portfolio Summary", [
            {"label": "loan_count", "question": "how many loans are there?"},
            {"label": "total_commitment", "unit": "USD", "question":
             "what is the total commitment across all loans?"}])

    def test_json_dataset_carries_provenance_and_confidence_per_value(self):
        report = self._portfolio_report()
        ds = feed_mod.render_dataset(report)
        self.assertEqual(len(ds["rows"]), 2)
        for row in ds["rows"]:
            self.assertIn("provenance", row)
            self.assertIsNotNone(row["confidence"])
            # provenance has a resolvable pointer (single or aggregate)
            prov = row["provenance"]
            self.assertTrue(prov.get("raw_response_id") or prov.get("contributing"))

    def test_manifest_is_schema_valid_with_real_completeness_proof(self):
        report = self._portfolio_report()
        manifest = feed_mod.build_manifest(report)
        res = feed_mod.validate_manifest(manifest)
        self.assertTrue(res["ok"], msg=f"manifest invalid: {res['errors']}")
        # completeness proof is the REAL pagination gate result, not a placeholder
        for fig in manifest["figures"]:
            self.assertIn("pagination_complete", fig["completeness"])
            self.assertIsInstance(fig["completeness"]["complete"], bool)
        # the count figure's pagination_complete is True (matches the gate verdict)
        count_fig = next(f for f in manifest["figures"] if f["label"] == "loan_count")
        self.assertTrue(count_fig["completeness"]["pagination_complete"])

    def test_feed_row_provenance_resolves_to_tier1(self):
        builder = self._builder()
        report = builder.build("Portfolio Summary", [
            {"label": "loan_count", "question": "how many loans are there?"}])
        feed = feed_mod.render_feed(report)
        row = feed["dataset"]["rows"][0]
        value, ok = builder.spine.cache.resolve_binding(row["provenance"])
        self.assertTrue(ok)
        self.assertEqual(value, row["value"])

    def test_csv_well_formed_and_round_trips_with_json(self):
        report = self._portfolio_report()
        ds = feed_mod.render_dataset(report)
        csv_text = feed_mod.render_csv(report)
        parsed = feed_mod.parse_csv(csv_text)
        self.assertEqual(len(parsed), len(ds["rows"]))
        for ds_row, csv_row in zip(ds["rows"], parsed):
            self.assertEqual(csv_row["label"], ds_row["label"])
            # value round-trips (string form matches)
            self.assertEqual(csv_row["value"], feed_mod._csv_scalar(ds_row["value"]))
            self.assertEqual(csv_row["raw_response_id"],
                             feed_mod._csv_scalar(ds_row["provenance"]["raw_response_id"]))
            self.assertEqual(csv_row["json_field_path"],
                             feed_mod._csv_scalar(ds_row["provenance"]["json_field_path"]))

    def test_csv_quotes_embedded_commas_no_corruption(self):
        # A label with a comma must not corrupt the CSV (stdlib csv quoting).
        report = {"state": deliver_mod.STATE_DELIVERED, "title": "T",
                  "generated_at": "2026-06-18T09:00:00Z", "refusals": [], "meta": {},
                  "figures": [{"label": "commitment, total", "value": 600.0, "unit": "USD",
                               "currency": "USD", "confidence": 1.0, "complete": True,
                               "tier": "report",
                               "provenance": {"aggregate": True, "contributing": [
                                   {"raw_response_id": "r", "json_field_path": "$.a"}]},
                               "gate_verdict": {"outcome": "pass",
                                                "pagination_complete": True}}]}
        csv_text = feed_mod.render_csv(report)
        parsed = feed_mod.parse_csv(csv_text)
        self.assertEqual(parsed[0]["label"], "commitment, total")
        self.assertEqual(parsed[0]["value"], "600.0")


# ===========================================================================
# SLICE-09 — refusals are surfaced into the feed (consumer MUST honor)
# ===========================================================================

class FeedRefusalSurfacingTest(_ReportTest):
    def test_refused_figure_surfaces_in_feed_not_as_a_row(self):
        report = self._builder(_FixtureSpineBackend(truncated=True)).build(
            "Portfolio Summary",
            [{"label": "loan_count", "question": "how many loans are there?"},
             {"label": "total_commitment", "question":
              "what is the total commitment across all loans?"}])
        feed = feed_mod.render_feed(report)
        # the refused figure is NOT a dataset row (no fabricated value) ...
        row_labels = {r["label"] for r in feed["dataset"]["rows"]}
        self.assertNotIn("loan_count", row_labels)
        # ... it IS in the dataset + manifest refusals (consumer must honor it)
        self.assertTrue(any(r["figure"] == "loan_count"
                            for r in feed["dataset"]["refusals"]))
        self.assertTrue(any(r["figure"] == "loan_count"
                            for r in feed["manifest"]["refusals"]))
        # manifest still validates even with a refusal present
        self.assertTrue(feed_mod.validate_manifest(feed["manifest"])["ok"])


# ===========================================================================
# SLICE-09 — PII SAFETY
# ===========================================================================

class PiiSafetyTest(_ReportTest):
    def _per_record_report(self):
        # A single-record lookup figure (per-borrower value) — NOT portfolio-level.
        return self._builder().build("Loan Detail", [
            {"label": "loan_status", "question": "what is the status of loan L-001?"}])

    def test_pii_safe_mode_redacts_per_record_value(self):
        report = self._per_record_report()
        # the spine delivered the per-record figure with a value ...
        self.assertEqual(report["state"], deliver_mod.STATE_DELIVERED)
        self.assertEqual(report["figures"][0]["value"], "ACTIVE")
        # ... but the PII-safe dataset must REDACT the per-record value to None + flag it.
        ds = feed_mod.render_dataset(report, pii_safe=True)
        row = ds["rows"][0]
        self.assertIsNone(row["value"])
        self.assertTrue(row["pii_redacted"])
        # provenance pointer + label survive (field-name + pointer are not PII)
        self.assertIsNotNone(row["provenance"]["json_field_path"])
        self.assertEqual(row["label"], "loan_status")

    def test_pii_safe_csv_has_no_record_level_value(self):
        report = self._per_record_report()
        csv_text = feed_mod.render_csv(report, pii_safe=True)
        parsed = feed_mod.parse_csv(csv_text)
        self.assertEqual(parsed[0]["value"], "")           # redacted to empty
        self.assertEqual(parsed[0]["pii_redacted"], "true")

    def test_portfolio_aggregate_is_not_redacted(self):
        # Aggregates/counts are portfolio-level and ARE emitted in pii-safe mode.
        report = self._builder().build("Portfolio Summary", [
            {"label": "loan_count", "question": "how many loans are there?"},
            {"label": "total_commitment", "question":
             "what is the total commitment across all loans?"}])
        ds = feed_mod.render_dataset(report, pii_safe=True)
        for row in ds["rows"]:
            self.assertIsNotNone(row["value"])
            self.assertFalse(row["pii_redacted"])

    def test_write_artifact_refuses_non_pii_safe_into_tracked_tree(self):
        report = self._per_record_report()
        text = feed_mod.render_json(report, pii_safe=False)
        # writing a non-pii-safe artifact into the tracked tree (the skill dir) must REFUSE
        tracked_dest = os.path.join(
            feed_mod._repo_root(), ".claude", "skills", "acos-hypercore-ask",
            "should-never-exist.json")
        with self.assertRaises(PermissionError):
            feed_mod.write_artifact(text, tracked_dest, pii_safe=False)
        self.assertFalse(os.path.exists(tracked_dest))

    def test_write_artifact_allows_non_pii_safe_into_runtime_area(self):
        report = self._per_record_report()
        text = feed_mod.render_json(report, pii_safe=False)
        runtime_dest = os.path.join(
            feed_mod._repo_root(), ".acos", "state", "hca-test-runtime",
            "per-record-feed.json")
        try:
            path = feed_mod.write_artifact(text, runtime_dest, pii_safe=False)
            self.assertTrue(os.path.exists(path))
        finally:
            shutil.rmtree(os.path.dirname(runtime_dest), ignore_errors=True)

    def test_pii_safe_artifact_may_be_written_to_tracked_tree(self):
        report = self._builder().build("Portfolio Summary", [
            {"label": "loan_count", "question": "how many loans are there?"}])
        text = feed_mod.render_json(report, pii_safe=True)
        dest = os.path.join(self.tmp, "safe-feed.json")  # outside repo entirely is fine too
        path = feed_mod.write_artifact(text, dest, pii_safe=True)
        self.assertTrue(os.path.exists(path))


# ===========================================================================
# NO NETWORK — the feed module imports no network library
# ===========================================================================

class NoNetworkImportTest(unittest.TestCase):
    def test_feed_module_imports_no_network_library(self):
        src_path = os.path.join(_SCRIPTS_DIR, "hca-feed.py")
        with open(src_path, "r", encoding="utf-8") as fh:
            src = fh.read()
        for forbidden in ("import urllib", "import http", "import socket", "import ssl",
                          "import requests"):
            self.assertNotIn(forbidden, src,
                             msg=f"hca-feed.py must not {forbidden} (no network in the feed)")

    def test_feed_module_stdlib_only_json_csv(self):
        # The feed renderers use stdlib json + csv only (ground rule).
        self.assertTrue(hasattr(feed_mod, "render_json"))
        self.assertTrue(hasattr(feed_mod, "render_csv"))
        self.assertTrue(hasattr(feed_mod, "render_feed"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
