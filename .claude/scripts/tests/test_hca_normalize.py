#!/usr/bin/env python3
"""test_hca_normalize.py — stdlib unittest for Tier-2 derivation (SLICE-HCA-03).

Focuses on hca-normalize.py directly (the cache tests exercise it via read_tier2):
  - derivation across all THREE Tier-1 body shapes (GraphQL single/list + REST single)
  - per-field json_field_path correctness for each shape
  - bindings re-resolve to the exact Tier-1 value (round-trip via the shared walker)
  - PII minimization in the derived view (raw retains everything)
  - the verify_bindings_against_tier1 hard gate (100% must resolve; any failure = REJECT)

Run:
  python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py' -v
"""

import importlib.util
import os
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


def _gql_single(rid="hca:s"):
    return {
        "raw_response_id": rid, "entity_type": "loan",
        "endpoint": "https://api.hypercore.ai/graphql",
        "request_params": {}, "timestamp": "2026-06-18T08:00:00Z",
        "http_status": 200, "cursor": None, "reported_total": None, "backend": "fixture",
        "body": {"record": {"id": "L-1", "commitment": 5000000.0, "status": "ACTIVE"},
                 "provenance": {"fetched_at": "2026-06-18T08:00:00Z"}},
    }


def _gql_list(rid="hca:l"):
    return {
        "raw_response_id": rid, "entity_type": "loan",
        "endpoint": "https://api.hypercore.ai/graphql",
        "request_params": {}, "timestamp": "2026-06-18T08:00:00Z",
        "http_status": 200, "cursor": None, "reported_total": 2, "backend": "fixture",
        "body": {"data": [{"id": "L-1", "commitment": 100.0},
                          {"id": "L-2", "commitment": 200.0}],
                 "reported_total": 2, "fetched": 2, "complete": True, "pages": 1,
                 "provenance": {"fetched_at": "2026-06-18T08:00:00Z"}},
    }


def _rest_single(rid="hca:r"):
    # legacy REST-shaped fixture: body IS the record (no .record / .data wrapper)
    return {
        "raw_response_id": rid, "entity_type": "loan",
        "endpoint": "FIXTURE", "request_params": {}, "timestamp": "2026-06-18T08:00:00Z",
        "http_status": 200, "cursor": None, "reported_total": None, "backend": "fixture",
        "body": {"loan_id": "L-001", "outstanding_principal": 1234.5, "currency": "USD"},
    }


class GqlSingleShapeTest(unittest.TestCase):
    def test_paths_target_body_record(self):
        n2 = normalize_mod.normalize_record(_gql_single(), entity_type="loan")
        self.assertEqual(n2["field_bindings"]["commitment"]["json_field_path"],
                         "$.body.record.commitment")
        self.assertEqual(n2["fields"]["commitment"], 5000000.0)
        self.assertEqual(n2["derived_from"], ["hca:s"])

    def test_round_trip_resolves(self):
        raw = _gql_single()
        n2 = normalize_mod.normalize_record(raw, entity_type="loan")
        for field, b in n2["field_bindings"].items():
            val = cache_mod.walk_json_path(raw, b["json_field_path"])
            self.assertIsNot(val, cache_mod._MISSING)
            self.assertEqual(val, n2["fields"][field])


class GqlListShapeTest(unittest.TestCase):
    def test_paths_index_into_body_data(self):
        n2 = normalize_mod.normalize_record(_gql_list(), entity_type="loan")
        self.assertEqual(n2["record_count"], 2)
        rec0, rec1 = n2["records"]
        self.assertEqual(rec0["field_bindings"]["commitment"]["json_field_path"],
                         "$.body.data[0].commitment")
        self.assertEqual(rec1["field_bindings"]["id"]["json_field_path"],
                         "$.body.data[1].id")

    def test_every_list_binding_resolves(self):
        raw = _gql_list()
        n2 = normalize_mod.normalize_record(raw, entity_type="loan")
        for rec in normalize_mod.iter_normalized_records(n2):
            for field, b in rec["field_bindings"].items():
                val = cache_mod.walk_json_path(raw, b["json_field_path"])
                self.assertEqual(val, rec["fields"][field])


class RestSingleShapeTest(unittest.TestCase):
    def test_paths_target_body_root(self):
        n2 = normalize_mod.normalize_record(_rest_single(), entity_type="loan")
        self.assertEqual(n2["field_bindings"]["outstanding_principal"]["json_field_path"],
                         "$.body.outstanding_principal")
        self.assertEqual(n2["fields"]["outstanding_principal"], 1234.5)


class PiiMinimizationTest(unittest.TestCase):
    def test_pii_dropped_in_derived_view(self):
        raw = {
            "raw_response_id": "hca:pii", "entity_type": "client",
            "endpoint": "x", "request_params": {}, "timestamp": "2026-06-18T08:00:00Z",
            "http_status": 200, "cursor": None, "reported_total": None, "backend": "fixture",
            "body": {"record": {"id": "C-1", "email": "placeholder@example.invalid",
                                "displayName": "PLACEHOLDER Co", "numOfActiveLoans": 1},
                     "provenance": {"fetched_at": "2026-06-18T08:00:00Z"}},
        }
        n2 = normalize_mod.normalize_record(raw, entity_type="client")
        self.assertNotIn("email", n2["fields"])
        self.assertIn("email", n2["_pii_minimized"])
        self.assertIn("displayName", n2["fields"])  # displayName is NOT in the PII deny-set

    def test_keep_pii_flag_retains_everything(self):
        raw = {
            "raw_response_id": "hca:pii2", "entity_type": "client",
            "endpoint": "x", "request_params": {}, "timestamp": "2026-06-18T08:00:00Z",
            "http_status": 200, "cursor": None, "reported_total": None, "backend": "fixture",
            "body": {"record": {"id": "C-1", "email": "placeholder@example.invalid"},
                     "provenance": {"fetched_at": "2026-06-18T08:00:00Z"}},
        }
        n2 = normalize_mod.normalize_record(raw, entity_type="client", keep_pii=True)
        self.assertIn("email", n2["fields"])  # explicit opt-in (drill-down only)


class HardGateVerifierTest(unittest.TestCase):
    def test_all_bindings_resolve_passes(self):
        raws = {r["raw_response_id"]: r for r in [_gql_list("hca:g")]}
        n2 = normalize_mod.normalize_record(raws["hca:g"], entity_type="loan")
        report = normalize_mod.verify_bindings_against_tier1(
            n2, tier1_lookup=lambda rid: raws.get(rid))
        self.assertTrue(report["ok"], msg=report["failures"])

    def test_unresolvable_binding_is_rejected(self):
        raw = _gql_single("hca:bad")
        raws = {raw["raw_response_id"]: raw}
        n2 = normalize_mod.normalize_record(raw, entity_type="loan")
        # corrupt one binding's path
        list(n2["field_bindings"].values())[0]["json_field_path"] = "$.body.record.GONE"
        report = normalize_mod.verify_bindings_against_tier1(
            n2, tier1_lookup=lambda rid: raws.get(rid))
        self.assertFalse(report["ok"])

    def test_missing_tier1_source_is_rejected(self):
        raw = _gql_single("hca:orphan")
        n2 = normalize_mod.normalize_record(raw, entity_type="loan")
        report = normalize_mod.verify_bindings_against_tier1(
            n2, tier1_lookup=lambda rid: None)  # nothing in Tier-1
        self.assertFalse(report["ok"])


class WalkerEdgeCaseTest(unittest.TestCase):
    def test_walker_handles_quoted_keys_and_indices(self):
        root = {"body": {"data": [{"a-b": {"c": 7}}]}}
        self.assertEqual(cache_mod.walk_json_path(root, "$.body.data[0]['a-b'].c"), 7)

    def test_walker_returns_missing_for_bad_index(self):
        root = {"body": {"data": [{"id": "x"}]}}
        self.assertIs(cache_mod.walk_json_path(root, "$.body.data[5].id"),
                      cache_mod._MISSING)

    def test_walker_returns_missing_for_bad_key(self):
        root = {"body": {"record": {"id": "x"}}}
        self.assertIs(cache_mod.walk_json_path(root, "$.body.record.nope"),
                      cache_mod._MISSING)


if __name__ == "__main__":
    unittest.main(verbosity=2)
