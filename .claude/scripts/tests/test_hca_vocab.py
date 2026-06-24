#!/usr/bin/env python3
"""test_hca_vocab.py — stdlib unittest for the shared vocabulary leaf (hca-vocab.py) and the
TRUST-CRITICAL routing consequence it exists to fix.

Background (round-1 robust review, HIGH): hca-route's aggregation words had DRIFTED from
hca-deliver's analysis triggers, so whole-portfolio superlative / ratio questions
("what is the highest interest rate?", "smallest commitment") classified as TRIVIAL and were
answered WITHOUT the mandatory 2-of-3 consensus path — a direct violation of trust invariant #5
(reports / aggregations route through consensus). The fix hoists ONE shared vocabulary leaf
(hca-vocab.py) consumed by route / deliver / figures / ontology, and WIDENS the consensus-routed
set to include superlatives / ratios / tables.

These tests lock:
  (1) the leaf is a pure data module that imports NOTHING from the skill (no circular-import risk);
  (2) the unioned vocabularies are SUPERSETS of every prior per-module copy (no phrasing lost);
  (3) the figure-kind constants are the canonical strings;
  (4) [BEHAVIORAL] superlative / ratio / extremum whole-portfolio questions route to the
      consensus-required REPORT tier, NEVER trivial; genuine single-value lookups stay trivial.

Run:
  python3 .claude/scripts/tests/test_hca_vocab.py
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


vocab_mod = _load("hca_vocab", "hca-vocab.py")
route_mod = _load("hca_route", "hca-route.py")
deliver_mod = _load("hca_deliver", "hca-deliver.py")


class VocabLeafContractTest(unittest.TestCase):
    def test_leaf_imports_nothing_from_the_skill(self):
        # A pure data leaf cannot participate in a circular import. Guard against any future edit
        # that wires a sibling import (the consumers import FROM here, never the reverse).
        with open(os.path.join(_SCRIPTS_DIR, "hca-vocab.py"), encoding="utf-8") as fh:
            src = fh.read()
        for needle in ("import hca", "hca_route", "hca_deliver", "hca_figures",
                       "hca_ontology", "spec_from_file_location"):
            self.assertNotIn(needle, src,
                             msg=f"hca-vocab must be a pure leaf; found {needle!r}")

    def test_kind_constants_are_canonical(self):
        self.assertEqual(
            (vocab_mod.KIND_DIRECT, vocab_mod.KIND_DERIVED, vocab_mod.KIND_REQUIRES_EXTERNAL),
            ("direct", "derived", "requires_external"))

    def test_payoff_vocab_is_superset_of_prior_copies(self):
        prior_deliver = ("payoff", "pay off", "pay-off", "early redemption", "early-redemption",
                         "amount to redeem", "redemption amount", "amount to pay off", "redeem")
        prior_figures = ("early_redemption", "early redemption", "payoff", "redemption",
                         "amount to redeem", "redeem")
        for t in set(prior_deliver) | set(prior_figures):
            self.assertIn(t, vocab_mod.PAYOFF_TERMS, msg=f"payoff vocab lost prior term {t!r}")

    def test_aggregation_vocab_contains_superlatives_ratios_tables(self):
        for t in ("highest", "smallest", "largest", "lowest", "most", "least", "maximum",
                  "minimum", "biggest", "greatest", "top"):
            self.assertIn(t, vocab_mod.AGGREGATION_ANALYSIS_TERMS,
                          msg=f"superlative {t!r} missing from aggregation vocab")
        for t in ("percentage", "percent", "ratio", "proportion", "share", "%"):
            self.assertIn(t, vocab_mod.AGGREGATION_ANALYSIS_TERMS,
                          msg=f"ratio term {t!r} missing from aggregation vocab")
        for t in ("tabulate", "table"):
            self.assertIn(t, vocab_mod.AGGREGATION_ANALYSIS_TERMS,
                          msg=f"table term {t!r} missing from aggregation vocab")

    def test_leaf_selftest_passes(self):
        self.assertEqual(vocab_mod._run_selftest(), 0)


class ConsensusRoutingTrustTest(unittest.TestCase):
    """Invariant #5: a whole-portfolio superlative / ratio / extremum question MUST route to the
    consensus-required report tier, NEVER the trivial single-source path. This is the behavioral
    lock for the round-1 HIGH consensus-bypass finding."""

    # All probe-verified to route report-tier post-fix.
    SUPERLATIVE_RATIO = (
        "What is the highest interest rate?",
        "What is the smallest commitment?",
        "Which loan has the largest outstanding balance?",
        "What percentage of loans are overdue?",
        "What is the average DSCR ratio across the book?",
    )
    # Genuine single-value lookups that must NOT be forced through consensus.
    SINGLE_LOOKUPS = (
        "what is the maturity date of loan 134?",
        "what is the payoff for Beehive Waldorff?",
    )

    def test_superlative_and_ratio_questions_are_consensus_routed(self):
        for q in self.SUPERLATIVE_RATIO:
            tier = deliver_mod.route_figure_tier(q)
            self.assertNotEqual(tier, "trivial",
                                msg=f"CONSENSUS BYPASS: {q!r} routed trivial (must be consensus)")
            self.assertEqual(tier, "report",
                             msg=f"{q!r} should route to report tier, got {tier!r}")

    def test_single_value_lookups_stay_trivial(self):
        for q in self.SINGLE_LOOKUPS:
            tier = deliver_mod.route_figure_tier(q)
            self.assertEqual(tier, "trivial", msg=f"{q!r} should stay trivial, got {tier!r}")

    def test_classify_agrees_superlatives_are_not_trivial(self):
        for q in self.SUPERLATIVE_RATIO:
            c = route_mod.classify(q)
            tier = getattr(c, "tier", c)
            self.assertNotIn("trivial", str(tier).lower(),
                             msg=f"classify routed {q!r} trivial: {tier!r}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
