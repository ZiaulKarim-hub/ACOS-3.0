#!/usr/bin/env python3
"""test_hca_ontology.py — stdlib unittest for the private-credit domain ontology (SLICE-HCA-13).

Proves the PRISM-seeded concept map:
  - resolves canonical names + synonyms + fuzzy phrasings to the right concept (no guessing),
  - declares the right kind (direct / derived / requires_external) and source for each concept,
  - carries PRISM covenant thresholds (LTV 75% max, DSCR 1.25x min, debt yield 8% min) as
    metadata on the leverage/coverage concepts,
  - derived concepts (utilization) name their input concepts + a transparent formula,
  - an unmapped phrasing is a clean miss (never an invented concept), and a close tie
    DISAMBIGUATES (never silently picks).

Run:
  python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py' -v
"""

import importlib.util
import os
import sys
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


ont_mod = _load("hca_ontology", "hca-ontology.py")


class OntologyShapeTest(unittest.TestCase):
    def setUp(self):
        self.ont = ont_mod.build_ontology()

    def test_seeds_the_core_private_credit_concepts(self):
        names = set(self.ont.names())
        for expected in ("outstanding_balance", "principal_outstanding", "accrued_interest",
                         "default_interest", "amount_due_today", "overdue_amount", "commitment",
                         "total_disbursed", "utilization", "maturity_date", "payoff_as_of",
                         "ltv", "dscr", "debt_yield", "cap_rate"):
            self.assertIn(expected, names, f"ontology should seed {expected!r}")

    def test_every_concept_has_definition_kind_source_unit(self):
        for c in self.ont.concepts():
            self.assertTrue(c.definition, f"{c.name} needs a plain-English definition")
            self.assertIn(c.kind, (ont_mod.KIND_DIRECT, ont_mod.KIND_DERIVED,
                                   ont_mod.KIND_REQUIRES_EXTERNAL))
            self.assertIsNotNone(c.source, f"{c.name} needs a source")
            self.assertTrue(c.unit, f"{c.name} needs a unit")


class OntologyKindAndSourceTest(unittest.TestCase):
    def setUp(self):
        self.ont = ont_mod.build_ontology()

    def test_direct_concepts_map_to_a_graphql_field_path(self):
        c = self.ont.get("outstanding_balance")
        self.assertEqual(c.kind, ont_mod.KIND_DIRECT)
        self.assertEqual(c.source, "summary.totalOutstanding.total")
        self.assertEqual(self.ont.get("commitment").source, "loan.commitment")
        self.assertEqual(self.ont.get("total_disbursed").source, "summary.totalDisbursed")
        self.assertEqual(self.ont.get("maturity_date").source, "loan.scheduleEndDate")

    def test_derived_utilization_names_inputs_and_formula(self):
        c = self.ont.get("utilization")
        self.assertEqual(c.kind, ont_mod.KIND_DERIVED)
        self.assertIsInstance(c.source, dict)
        self.assertEqual(c.source["formula"], "total_disbursed / commitment")
        self.assertEqual(set(c.input_concepts()), {"total_disbursed", "commitment"})

    def test_requires_external_concepts_name_the_kg_source(self):
        for name in ("ltv", "dscr", "debt_yield", "cap_rate"):
            c = self.ont.get(name)
            self.assertEqual(c.kind, ont_mod.KIND_REQUIRES_EXTERNAL,
                             f"{name} requires external KG data")
            self.assertIn("knowledge graph", c.source.lower())

    def test_covenant_thresholds_carried_from_prism(self):
        ltv = self.ont.get("ltv")
        self.assertEqual(ltv.covenant["threshold"], 0.75)
        self.assertEqual(ltv.covenant["direction"], "max")
        dscr = self.ont.get("dscr")
        self.assertEqual(dscr.covenant["threshold"], 1.25)
        self.assertEqual(dscr.covenant["direction"], "min")
        dy = self.ont.get("debt_yield")
        self.assertEqual(dy.covenant["threshold"], 0.08)
        self.assertEqual(dy.covenant["direction"], "min")


class OntologyResolveTest(unittest.TestCase):
    def setUp(self):
        self.ont = ont_mod.build_ontology()

    def test_resolves_synonyms_to_canonical_concept(self):
        for phrase, expect in (
            ("outstanding", "outstanding_balance"),
            ("upb", "outstanding_balance"),
            ("current balance", "outstanding_balance"),
            ("loan amount", "commitment"),
            ("drawn", "total_disbursed"),
            ("amount due", "amount_due_today"),
            ("past due", "overdue_amount"),
            ("penalties", "default_interest"),
            ("loan-to-value", "ltv"),
            ("debt service coverage ratio", "dscr"),
            ("maturity", "maturity_date"),
            ("utilization rate", "utilization"),
        ):
            res = self.ont.resolve(phrase)
            self.assertTrue(res["resolved"], f"{phrase!r} should resolve ({res['reason']})")
            self.assertEqual(res["concept"].name, expect, f"{phrase!r} -> {expect!r}")

    def test_fuzzy_phrasing_resolves(self):
        res = self.ont.resolve("what's the outstanding balance")
        self.assertTrue(res["resolved"])
        self.assertEqual(res["concept"].name, "outstanding_balance")

    def test_unmapped_phrase_is_clean_miss_not_invented(self):
        res = self.ont.resolve("the borrower's favorite color")
        self.assertFalse(res["resolved"])
        self.assertIsNone(res["concept"])

    def test_exact_name_always_wins(self):
        res = self.ont.resolve("debt_yield")
        self.assertTrue(res["resolved"])
        self.assertEqual(res["concept"].name, "debt_yield")

    def test_empty_query_is_clean_miss(self):
        res = self.ont.resolve("")
        self.assertFalse(res["resolved"])
        self.assertIsNone(res["concept"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
