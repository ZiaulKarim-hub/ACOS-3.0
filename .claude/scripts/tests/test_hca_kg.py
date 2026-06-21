#!/usr/bin/env python3
"""test_hca_kg.py — stdlib unittest for the OKOA knowledge-graph join (SLICE-HCA-14).

Proves on FIXTURE CSV ROWS (no dependency on the live ~/okoa-labs knowledge graph) that
hca-kg.py:

  HIT
    - fuzzy-matches a Hypercore loan name to a DEAL/PROPERTY/CLAIM node (canonical_name +
      aliases) and PARSES its properties_json into the collateral facts the ratio figures need
      (appraised_value / noi / purchase_price / ltv_latest / interest_rate), each with
      provenance = the source node_id + field.
    - resolves a CLAIM-based value via its subject_node_id and points provenance at the claim.
    - pulls a value living on a same-deal sibling PROPERTY node.

  MISS (refuse, never fabricate)
    - no confident match -> None.
    - a genuinely ambiguous match (two different deals tied) -> None.
    - the matched node lacks the requested field -> that fact is simply absent.

  READ-ONLY
    - the module never writes to the KG dir.

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


kg_mod = _load("hca_kg", "hca-kg.py")


_HEADER = ["node_id", "canonical_name", "aliases", "node_type", "short_desc",
           "verification_status", "confidence", "importance", "tags", "source_ccii",
           "extraction_date", "embedding_group", "namespace", "canonical", "sameAs",
           "merge_confidence", "notes", "pii_risk", "security_sensitivity", "properties_json"]


def _write_kg(dirpath, rows):
    """Write a synthetic nodes.csv mirroring the real KG schema. All values synthetic."""
    import csv as _csv
    path = os.path.join(dirpath, "nodes.csv")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = _csv.writer(fh)
        w.writerow(_HEADER)
        for r in rows:
            row = {h: "" for h in _HEADER}
            row["node_id"] = r["node_id"]
            row["canonical_name"] = r.get("canonical_name", "")
            row["aliases"] = r.get("aliases", "")
            row["node_type"] = r.get("node_type", "")
            row["verification_status"] = r.get("verification_status", "")
            row["confidence"] = r.get("confidence", "")
            row["properties_json"] = json.dumps(r.get("props", {}))
            w.writerow([row[h] for h in _HEADER])
    return path


# A small synthetic KG: a deal with everything, a deal+property where the value lives on the
# property (and a financial claim), a property-only appraised value, and two unrelated deals
# that share only a stopword (to prove a genuine ambiguity is refused).
_ROWS = [
    {"node_id": "deal:fixture-broadbent", "node_type": "DEAL", "confidence": 0.95,
     "verification_status": "verified",
     "canonical_name": "Broadbent Springville (Lakeside Landing)",
     "aliases": "Broadbent|Broadbent Springville",
     "props": {"appraised_value": 38100000, "ltv_latest": 0.427, "interest_rate": 0.14,
               "maturity_date": "2026-04-03", "purchase_price": 20000000}},
    # the property collateral for a deal whose DEAL node has NO direct appraised_value:
    {"node_id": "deal:fixture-marsh", "node_type": "DEAL", "confidence": 0.9,
     "verification_status": "corroborated",
     "canonical_name": "Marsh Hollow Deal", "aliases": "Marsh Hollow",
     "props": {"interest_rate": 0.11}},
    {"node_id": "property:fixture-marsh-hollow", "node_type": "PROPERTY", "confidence": 0.9,
     "verification_status": "corroborated",
     "canonical_name": "Marsh Hollow Property", "aliases": "Marsh Hollow",
     "props": {"as_is_value": 15000000}},
    {"node_id": "claim:fixture-marsh-noi", "node_type": "CLAIM", "confidence": 0.85,
     "verification_status": "corroborated",
     "canonical_name": "Marsh Hollow NOI is $900K",
     "props": {"claim_type": "financial", "normalized_value": "900000.000000",
               "subject_node_id": "deal:fixture-marsh"}},
    # a CLAIM-as-subject appraisal value pointing at a PROPERTY (resolve via subject):
    {"node_id": "deal:fixture-rincon", "node_type": "DEAL", "confidence": 0.92,
     "verification_status": "verified",
     "canonical_name": "Rincon Mesa Deal", "aliases": "Rincon Mesa",
     "props": {"ltv_latest": 0.6}},
    {"node_id": "claim:fixture-rincon-appraised", "node_type": "CLAIM", "confidence": 0.88,
     "verification_status": "corroborated",
     "canonical_name": "Rincon Mesa appraised-value is $50M",
     "props": {"claim_type": "financial", "normalized_value": "50000000.000000",
               "subject_node_id": "deal:fixture-rincon"}},
    # two genuinely-different deals tied only by a stopword ("Commercial") -> ambiguous -> None:
    {"node_id": "deal:fixture-acme-commercial", "node_type": "DEAL", "confidence": 0.9,
     "canonical_name": "Acme Commercial", "aliases": ""},
    {"node_id": "deal:fixture-zenith-commercial", "node_type": "DEAL", "confidence": 0.9,
     "canonical_name": "Zenith Commercial", "aliases": ""},
]


class _KGBase(unittest.TestCase):
    def setUp(self):
        self.kgdir = tempfile.mkdtemp(prefix="hca-kg-unit-")
        self.path = _write_kg(self.kgdir, _ROWS)
        self.store = kg_mod.KGStore(kg_dir=self.kgdir)

    def tearDown(self):
        shutil.rmtree(self.kgdir, ignore_errors=True)


class KGHitTest(_KGBase):
    def test_deal_with_all_facts_parses_properties_json(self):
        res = self.store.lookup("Broadbent Springville")
        self.assertIsNotNone(res)
        self.assertEqual(res["node_id"], "deal:fixture-broadbent")
        self.assertEqual(res["appraised_value"], 38100000.0)
        self.assertEqual(res["ltv_latest"], 0.427)
        self.assertEqual(res["interest_rate"], 0.14)
        self.assertEqual(res["purchase_price"], 20000000.0)
        # provenance points at the exact source node + field.
        prov = res["provenance"]["appraised_value"]
        self.assertEqual(prov["node_id"], "deal:fixture-broadbent")
        self.assertEqual(prov["field"], "appraised_value")
        self.assertTrue(prov["file"].endswith("nodes.csv"))
        # the KG node's own confidence is carried.
        self.assertEqual(res["confidence"], 0.95)

    def test_partial_name_matches(self):
        res = self.store.lookup("broadbent")
        self.assertIsNotNone(res)
        self.assertEqual(res["node_id"], "deal:fixture-broadbent")

    def test_value_on_sibling_property_node_is_found(self):
        # the DEAL "Marsh Hollow Deal" has no appraised_value; its sibling PROPERTY does.
        res = self.store.lookup("Marsh Hollow")
        self.assertIsNotNone(res)
        self.assertEqual(res["appraised_value"], 15000000.0)  # from the property's as_is_value
        # NOI comes from the financial claim pointing at the deal.
        self.assertEqual(res["noi"], 900000.0)
        self.assertEqual(res["provenance"]["noi"]["node_id"], "claim:fixture-marsh-noi")
        self.assertEqual(res["provenance"]["noi"]["field"], "normalized_value")
        self.assertEqual(res["provenance"]["noi"]["subject_node_id"], "deal:fixture-marsh")

    def test_claim_based_appraised_value_resolves_via_subject(self):
        res = self.store.lookup("Rincon Mesa")
        self.assertIsNotNone(res)
        self.assertEqual(res["appraised_value"], 50000000.0)
        self.assertEqual(res["provenance"]["appraised_value"]["node_id"],
                         "claim:fixture-rincon-appraised")
        self.assertEqual(res["ltv_latest"], 0.6)


class KGMissTest(_KGBase):
    def test_no_match_returns_none(self):
        self.assertIsNone(self.store.lookup("Nonexistent Quux Loan 12345"))

    def test_empty_query_returns_none(self):
        self.assertIsNone(self.store.lookup(""))
        self.assertIsNone(self.store.lookup(None))

    def test_genuinely_ambiguous_match_returns_none(self):
        # "Commercial" ties two unrelated deals sharing only a stopword -> refuse (no guess).
        self.assertIsNone(self.store.lookup("Commercial"))

    def test_matched_node_missing_field_is_absent_not_fabricated(self):
        # Rincon Mesa has no purchase_price -> the key is simply absent (never invented).
        res = self.store.lookup("Rincon Mesa")
        self.assertIsNotNone(res)
        self.assertNotIn("purchase_price", res)

    def test_missing_kg_file_returns_none(self):
        empty = tempfile.mkdtemp(prefix="hca-kg-empty-")
        try:
            store = kg_mod.KGStore(kg_dir=empty)  # no nodes.csv present
            self.assertIsNone(store.lookup("Broadbent"))
        finally:
            shutil.rmtree(empty, ignore_errors=True)


class KGReadOnlyTest(_KGBase):
    def test_lookup_does_not_mutate_the_csv(self):
        before = os.path.getmtime(self.path)
        with open(self.path, "r", encoding="utf-8") as fh:
            content_before = fh.read()
        for q in ("Broadbent Springville", "Marsh Hollow", "Rincon Mesa", "nope"):
            self.store.lookup(q)
        with open(self.path, "r", encoding="utf-8") as fh:
            content_after = fh.read()
        self.assertEqual(content_before, content_after)  # byte-identical
        self.assertEqual(before, os.path.getmtime(self.path))  # untouched mtime


class KGValueCoercionTest(unittest.TestCase):
    def test_to_float_handles_strings_and_rejects_bool(self):
        self.assertEqual(kg_mod._to_float("38100000.000000"), 38100000.0)
        self.assertEqual(kg_mod._to_float("$38,100,000"), 38100000.0)
        self.assertEqual(kg_mod._to_float("0.427"), 0.427)
        self.assertEqual(kg_mod._to_float(12150000), 12150000.0)
        self.assertIsNone(kg_mod._to_float(True))   # a bool is NOT a number
        self.assertIsNone(kg_mod._to_float("n/a"))
        self.assertIsNone(kg_mod._to_float(None))


if __name__ == "__main__":
    unittest.main(verbosity=2)
