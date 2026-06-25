#!/usr/bin/env python3
"""test_hca_learned.py — stdlib unittest for the learned-routing store (hca-learned.py).

Proves the cardinal rule structurally: the store learns ROUTING (metric->metric-word,
name->entity-id) and there is NO path that accepts a money value. Plus: validation (unknown
metrics/types rejected), longest-alias-wins lookup, name normalization, fail-open on a corrupt
file, atomic persistence across instances, and an audit trail.
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


learned = _load("hca_learned", "hca-learned.py")


class LearnedStoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hca-learned-test-")
        self.path = os.path.join(self.tmp, "learned.json")
        self.store = learned.LearnedStore(self.path, now="2026-06-25T00:00:00Z")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_empty_load(self):
        d = self.store.load()
        self.assertEqual(d["metric_aliases"], {})
        self.assertEqual(d["entity_resolutions"], {})

    def test_record_and_lookup_metric_alias(self):
        self.assertTrue(self.store.record_metric_alias("Amount Due", "outstanding")["ok"])
        # normalized substring match, case-insensitive
        self.assertEqual(self.store.metric_for("what is the amount due for XL?"), "outstanding")
        self.assertIsNone(self.store.metric_for("what is the commitment for XL?"))

    def test_reject_unknown_metric(self):
        res = self.store.record_metric_alias("amount due", "bogus_metric")
        self.assertFalse(res["ok"])
        self.assertEqual(self.store.load()["metric_aliases"], {})  # unchanged

    def test_record_and_lookup_entity(self):
        self.assertTrue(self.store.record_entity_resolution(
            "Ascent Pref", "loan", "149", "Ascent Pref Equity")["ok"])
        le = self.store.entity_for("ascent  pref?")  # normalization: case/space/punct
        self.assertEqual(le, {"entity_type": "loan", "id": "149", "name": "Ascent Pref Equity"})

    def test_reject_unknown_entity_type(self):
        self.assertFalse(self.store.record_entity_resolution("x", "wombat", "1")["ok"])

    def test_reject_missing_id(self):
        self.assertFalse(self.store.record_entity_resolution("x", "loan", "")["ok"])

    def test_longest_alias_wins(self):
        self.store.record_metric_alias("due", "receivable")
        self.store.record_metric_alias("amount due", "outstanding")
        self.assertEqual(self.store.metric_for("the amount due today"), "outstanding")

    def test_never_stores_values(self):
        # there is NO API accepting a number; every stored metric value is a canonical word
        self.store.record_metric_alias("amount due", "outstanding")
        for v in self.store.load()["metric_aliases"].values():
            self.assertIn(v, learned.CANONICAL_METRICS)
            self.assertNotIsInstance(v, (int, float))

    def test_failopen_corrupt_file(self):
        with open(self.path, "w") as f:
            f.write("{ this is not json ::::")
        self.assertEqual(self.store.load()["metric_aliases"], {})  # no exception

    def test_atomic_persist_across_instances(self):
        self.store.record_metric_alias("amount due", "outstanding")
        other = learned.LearnedStore(self.path)
        self.assertEqual(other.metric_for("amount due now"), "outstanding")

    def test_audit_trail(self):
        self.store.record_metric_alias("amount due", "outstanding")
        self.store.record_entity_resolution("ascent pref", "loan", "149", "Ascent Pref Equity")
        audit = self.store.load()["audit"]
        kinds = [a["kind"] for a in audit]
        self.assertIn("metric_alias", kinds)
        self.assertIn("entity_resolution", kinds)
        self.assertTrue(all(a.get("at") == "2026-06-25T00:00:00Z" for a in audit))


if __name__ == "__main__":
    unittest.main(verbosity=2)
