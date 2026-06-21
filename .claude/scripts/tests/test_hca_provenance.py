#!/usr/bin/env python3
"""test_hca_provenance.py — stdlib unittest for the provenance-binding engine (SLICE-HCA-04).

Proves the CORE NO-HALLUCINATION guarantee with POSITIVE and (critically) NEGATIVE tests:

  POSITIVE
    - bind_and_verify produces a ProvenanceBinding that resolves to a real Tier-1 record
      and the json_field_path points at the cited value (value matches).
    - aggregate binding collects one resolvable binding per contributing source.
    - single-source confidence capped at <= single_source_cap (0.7) and flagged.

  NEGATIVE (REQUIRED — fail = REJECT; this is the engine's whole reason to exist)
    - missing binding (no raw_response_id / no path)         -> REFUSED.
    - binding to a nonexistent raw_response_id               -> REFUSED.
    - binding whose path does not resolve                    -> REFUSED.
    - VALUE-MISMATCH: path resolves but the value differs    -> REFUSED.
    - a fabricated binding cannot be coaxed past the engine  -> REFUSED.
    - aggregate with ANY unbindable contributor              -> REFUSED.
    - invariant: no value leaves in a deliverable state without >=1 resolvable binding.

Run:
  python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py' -v
"""

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
normalize_mod = _load("hca_normalize", "hca-normalize.py")
prov_mod = _load("hca_provenance", "hca-provenance.py")


def _raw(rid="hca:p", commitment=5000000.0):
    return {
        "raw_response_id": rid, "entity_type": "loan",
        "endpoint": "https://api.hypercore.ai/graphql",
        "request_params": {"graphql_operation": "HCAGetLoan", "variables": {"id": "L-1"}},
        "timestamp": "2026-06-18T08:00:00Z",
        "http_status": 200, "cursor": None, "reported_total": None, "backend": "fixture",
        "body": {"record": {"id": "L-1", "commitment": commitment, "status": "ACTIVE"},
                 "provenance": {"fetched_at": "2026-06-18T08:00:00Z"}},
    }


class _EngineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hca-prov-test-")
        self.cache = cache_mod.TwoTierCache(cache_dir=self.tmp)
        self.engine = prov_mod.ProvenanceEngine(cache=self.cache)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


# ===========================================================================
# POSITIVE
# ===========================================================================

class PositiveBindTest(_EngineTest):
    def test_bind_and_verify_resolves_and_matches(self):
        self.cache.put_raw(_raw("hca:pos"))
        res = self.engine.bind_and_verify(
            5000000.0, {"raw_response_id": "hca:pos",
                        "json_field_path": "$.body.record.commitment"})
        self.assertEqual(res["outcome"], prov_mod.VERIFIED)
        self.assertTrue(res["deliverable"])
        b = res["binding"]
        # binding pulls endpoint/request_params/timestamp from the resolved Tier-1 record
        self.assertEqual(b["raw_response_id"], "hca:pos")
        self.assertEqual(b["json_field_path"], "$.body.record.commitment")
        self.assertEqual(b["endpoint"], "https://api.hypercore.ai/graphql")
        self.assertEqual(b["timestamp"], "2026-06-18T08:00:00Z")
        self.assertIn("request_params", b)

    def test_qa_independently_walks_path_and_confirms_value(self):
        # QA re-resolution: independently walk the cited path in Tier-1 and confirm match.
        self.cache.put_raw(_raw("hca:qa", commitment=777.0))
        raw = self.cache.get_raw("hca:qa")
        self.assertEqual(cache_mod.walk_json_path(raw, "$.body.record.commitment"), 777.0)
        res = self.engine.bind_and_verify(
            777.0, {"raw_response_id": "hca:qa",
                    "json_field_path": "$.body.record.commitment"})
        self.assertEqual(res["outcome"], prov_mod.VERIFIED)

    def test_or_raise_returns_on_verified(self):
        self.cache.put_raw(_raw("hca:ok"))
        res = self.engine.bind_and_verify_or_raise(
            5000000.0, {"raw_response_id": "hca:ok",
                        "json_field_path": "$.body.record.commitment"})
        self.assertEqual(res["outcome"], prov_mod.VERIFIED)

    def test_module_level_convenience(self):
        self.cache.put_raw(_raw("hca:mod"))
        res = prov_mod.bind_and_verify(
            5000000.0, {"raw_response_id": "hca:mod",
                        "json_field_path": "$.body.record.commitment"},
            cache=self.cache)
        self.assertEqual(res["outcome"], prov_mod.VERIFIED)


# ===========================================================================
# NEGATIVE — refuse-on-missing (REQUIRED; the three QA-re-authored cases + mismatch)
# ===========================================================================

class NegativeRefusalTest(_EngineTest):
    def test_no_binding_is_refused(self):
        res = self.engine.bind_and_verify(5000000.0, {})  # no raw_response_id / path
        self.assertEqual(res["outcome"], prov_mod.REFUSED)
        self.assertEqual(res["reason_code"], prov_mod.REASON_NO_BINDING)
        self.assertFalse(res["deliverable"])

    def test_binding_to_nonexistent_raw_response_id_is_refused(self):
        res = self.engine.bind_and_verify(
            5000000.0, {"raw_response_id": "hca:GHOST",
                        "json_field_path": "$.body.record.commitment"})
        self.assertEqual(res["outcome"], prov_mod.REFUSED)
        self.assertEqual(res["reason_code"], prov_mod.REASON_RAW_NOT_FOUND)

    def test_binding_whose_path_does_not_resolve_is_refused(self):
        self.cache.put_raw(_raw("hca:np"))
        res = self.engine.bind_and_verify(
            5000000.0, {"raw_response_id": "hca:np",
                        "json_field_path": "$.body.record.NOT_A_FIELD"})
        self.assertEqual(res["outcome"], prov_mod.REFUSED)
        self.assertEqual(res["reason_code"], prov_mod.REASON_PATH_UNRESOLVED)

    def test_value_mismatch_is_refused(self):
        # path resolves to 5000000.0 but caller claims a different value -> REFUSE
        self.cache.put_raw(_raw("hca:mm"))
        res = self.engine.bind_and_verify(
            9999999.0, {"raw_response_id": "hca:mm",
                        "json_field_path": "$.body.record.commitment"})
        self.assertEqual(res["outcome"], prov_mod.REFUSED)
        self.assertEqual(res["reason_code"], prov_mod.REASON_VALUE_MISMATCH)

    def test_fabricated_binding_cannot_pass(self):
        # A made-up value with a real path is caught because the value is re-read + compared.
        self.cache.put_raw(_raw("hca:fab"))
        res = self.engine.bind_and_verify(
            "TOTALLY FABRICATED", {"raw_response_id": "hca:fab",
                                   "json_field_path": "$.body.record.commitment"})
        self.assertEqual(res["outcome"], prov_mod.REFUSED)

    def test_or_raise_raises_on_refusal(self):
        with self.assertRaises(prov_mod.ProvenanceRefusal) as ctx:
            self.engine.bind_and_verify_or_raise(1.0, {})
        self.assertEqual(ctx.exception.result["outcome"], prov_mod.REFUSED)

    def test_type_change_is_a_mismatch(self):
        # "5000000.0" (string) must NOT match 5000000.0 (number) — type-faithful compare.
        self.cache.put_raw(_raw("hca:tc"))
        res = self.engine.bind_and_verify(
            "5000000.0", {"raw_response_id": "hca:tc",
                          "json_field_path": "$.body.record.commitment"})
        self.assertEqual(res["outcome"], prov_mod.REFUSED)


# ===========================================================================
# AGGREGATES
# ===========================================================================

class AggregateBindTest(_EngineTest):
    def _seed_two(self):
        self.cache.put_raw(_raw("hca:a1", commitment=100.0))
        self.cache.put_raw(_raw("hca:a2", commitment=200.0))

    def test_aggregate_binds_one_per_source(self):
        self._seed_two()
        res = self.engine.bind_aggregate(
            300.0,  # the (notional) sum
            [{"raw_response_id": "hca:a1", "json_field_path": "$.body.record.commitment"},
             {"raw_response_id": "hca:a2", "json_field_path": "$.body.record.commitment"}],
        )
        self.assertEqual(res["outcome"], prov_mod.VERIFIED)
        self.assertEqual(len(res["contributing"]), 2)

    def test_aggregate_refused_if_any_contributor_unbindable(self):
        self._seed_two()
        res = self.engine.bind_aggregate(
            300.0,
            [{"raw_response_id": "hca:a1", "json_field_path": "$.body.record.commitment"},
             {"raw_response_id": "hca:GHOST", "json_field_path": "$.body.record.commitment"}],
        )
        self.assertEqual(res["outcome"], prov_mod.REFUSED)
        self.assertEqual(res["reason_code"], prov_mod.REASON_CONTRIBUTOR_UNBINDABLE)

    def test_aggregate_with_no_contributors_refused(self):
        res = self.engine.bind_aggregate(0.0, [])
        self.assertEqual(res["outcome"], prov_mod.REFUSED)
        self.assertEqual(res["reason_code"], prov_mod.REASON_NO_CONTRIBUTORS)

    def test_aggregate_verifies_contributor_values_when_supplied(self):
        self._seed_two()
        res = self.engine.bind_aggregate(
            300.0,
            [{"raw_response_id": "hca:a1", "json_field_path": "$.body.record.commitment"},
             {"raw_response_id": "hca:a2", "json_field_path": "$.body.record.commitment"}],
            contributing_values=[100.0, 999.0],  # second is WRONG -> refuse
        )
        self.assertEqual(res["outcome"], prov_mod.REFUSED)


# ===========================================================================
# INVARIANT — no deliverable value without a resolvable binding
# ===========================================================================

class InvariantTest(_EngineTest):
    def test_no_deliverable_without_binding(self):
        # Every refusal path returns deliverable=False; every VERIFIED returns True.
        refusals = [
            self.engine.bind_and_verify(1.0, {}),
            self.engine.bind_and_verify(1.0, {"raw_response_id": "x"}),
            self.engine.bind_and_verify(1.0, {"raw_response_id": "ghost",
                                              "json_field_path": "$.a"}),
        ]
        for r in refusals:
            self.assertFalse(r["deliverable"])
            self.assertIsNone(r["binding"])

    def test_verify_normalized_record_pass_only_if_all_resolve(self):
        # Build a real Tier-2 record from a cached Tier-1, then batch-verify it.
        raw = {
            "raw_response_id": "hca:n2", "entity_type": "loan",
            "endpoint": "x", "request_params": {}, "timestamp": "2026-06-18T08:00:00Z",
            "http_status": 200, "cursor": None, "reported_total": 2, "backend": "fixture",
            "body": {"data": [{"id": "L-1", "commitment": 1.0},
                              {"id": "L-2", "commitment": 2.0}],
                     "provenance": {"fetched_at": "2026-06-18T08:00:00Z"}},
        }
        self.cache.put_raw(raw)
        n2 = self.cache.read_tier2("hca:n2", entity_type="loan")
        report = self.engine.verify_normalized_record(n2)
        self.assertTrue(report["ok"], msg=report["refusals"])
        self.assertEqual(report["verified"], report["checked"])

    def test_verify_normalized_record_fails_on_any_bad_binding(self):
        raw = {
            "raw_response_id": "hca:n3", "entity_type": "loan",
            "endpoint": "x", "request_params": {}, "timestamp": "2026-06-18T08:00:00Z",
            "http_status": 200, "cursor": None, "reported_total": None, "backend": "fixture",
            "body": {"record": {"id": "L-1", "commitment": 1.0},
                     "provenance": {"fetched_at": "2026-06-18T08:00:00Z"}},
        }
        self.cache.put_raw(raw)
        n2 = self.cache.read_tier2("hca:n3", entity_type="loan")
        # tamper a value so it no longer matches Tier-1 -> the batch verifier must fail
        n2["fields"]["commitment"] = 99.0
        report = self.engine.verify_normalized_record(n2)
        self.assertFalse(report["ok"])


# ===========================================================================
# CONFIDENCE — single-source cap
# ===========================================================================

class ConfidenceTest(_EngineTest):
    def test_single_source_capped_and_flagged(self):
        rec = self.engine.confidence_record("val:x", source_count=1)
        self.assertTrue(rec["single_source"])
        self.assertLessEqual(rec["confidence"], 0.7)
        self.assertEqual(rec["capped_at"], 0.7)

    def test_single_source_high_input_still_capped(self):
        rec = self.engine.confidence_record("val:x", source_count=1, agreement=0.99)
        self.assertLessEqual(rec["confidence"], 0.7)  # 0.99 forced down to <=0.7

    def test_multi_source_not_capped_by_single_source_rule(self):
        rec = self.engine.confidence_record("val:x", source_count=3, agreement=0.9)
        self.assertFalse(rec["single_source"])
        self.assertGreater(rec["confidence"], 0.7)
        self.assertIsNone(rec["capped_at"])

    def test_cap_read_from_config(self):
        # The engine's cap defaults to the config value (0.7).
        self.assertEqual(self.engine._cap, 0.7)


if __name__ == "__main__":
    unittest.main(verbosity=2)
