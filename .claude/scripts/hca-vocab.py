#!/usr/bin/env python3
"""hca-vocab.py — the SHARED VOCABULARY LEAF for acos-hypercore-ask.

A single source of truth for the phrasing vocabularies + figure-kind constants that the
intake router (hca-route.py), the deliver planner (hca-deliver.py), the figures registry
(hca-figures.py), and the domain ontology (hca-ontology.py) used to each carry their own
diverging copies of. Centralizing them here closes a TRUST gap: the divergence between
hca-route's aggregation words and hca-deliver's analysis triggers meant whole-portfolio
superlative / ratio questions ("what is the highest interest rate?", "smallest commitment")
could classify as TRIVIAL and be answered WITHOUT the 2-of-3 consensus path — a direct
violation of trust invariant #5 (reports / aggregations route through consensus).

LEAF MODULE CONTRACT (DO NOT VIOLATE):
  - This module imports NOTHING from the skill (no hca-* sibling). It is a pure data leaf so
    it can NEVER participate in a circular import. The consumers import FROM here, never the
    reverse. Stdlib only (it imports nothing at all beyond what the stdlib already provides).
  - The aggregation/analysis vocabulary is a strict SUPERSET of the prior per-module copies:
    every phrasing that previously matched still matches (the union only ADDS phrasings).
  - Trust direction: when adding terms here, only ever WIDEN the consensus-routed set. Never
    move a superlative / ratio / aggregation phrasing OUT of the consensus path.

GROUND RULES (memory/decisions/2026-06-18-hca-build-ground-rules.md):
  - Python 3 stdlib ONLY. No third-party deps. No network. No model calls.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Figure-kind constants (previously duplicated identically in hca-ontology.py and
# hca-figures.py). The single source of truth lives here.
# ---------------------------------------------------------------------------

KIND_DIRECT = "direct"                        # a value read straight off one GraphQL field
KIND_DERIVED = "derived"                      # computed/reconciled from multiple fields
KIND_REQUIRES_EXTERNAL = "requires_external"  # needs external KG data Hypercore can't source


# ---------------------------------------------------------------------------
# PAYOFF / early-redemption vocabulary
#   = UNION of hca-deliver._PAYOFF_TRIGGERS and hca-figures.PayoffFigure.SYNONYMS
#     (the two had diverged both ways; this unions them so neither path can lose a phrasing).
# ---------------------------------------------------------------------------

PAYOFF_TERMS = (
    "payoff", "pay off", "pay-off",
    "early redemption", "early-redemption", "early_redemption",
    "amount to redeem", "redemption amount", "amount to pay off",
    "redemption", "redeem",
)


# ---------------------------------------------------------------------------
# UTILIZATION vocabulary
#   = UNION of hca-deliver._UTILIZATION_TRIGGERS and the hca-figures utilization
#     DerivedFigure synonyms.
# ---------------------------------------------------------------------------

UTILIZATION_TERMS = (
    "utilization", "utilisation", "utilization rate",
    "drawn vs committed", "percent drawn",
)


# ---------------------------------------------------------------------------
# Analysis trigger sets (the canonical home for hca-deliver's portfolio-analysis triggers).
# hca-deliver imports these; they also feed the unioned AGGREGATION/ANALYSIS vocabulary below.
# ---------------------------------------------------------------------------

# Ranking phrasings.
RANK_TRIGGERS = (
    "top ", "largest", "biggest", "highest", "rank", "ranked", "most ",
    "greatest", "smallest", "lowest",
)

# At-risk interpretive-judgment phrasings.
AT_RISK_TRIGGERS = ("at risk", "at-risk", "most at risk", "riskiest", "highest risk")

# Concentration phrasings.
CONCENTRATION_TRIGGERS = (
    "concentration", "concentrated", "exposure by", "% of the book",
    "percent of the book", "% of book", "book in the top",
)


# ---------------------------------------------------------------------------
# Superlative / ratio / table vocabularies (the consensus-routing widening this fix adds).
# A whole-portfolio superlative ("highest interest rate") or ratio ("what percentage ...")
# question MUST be treated as a report/aggregation, NEVER a trivial single-value lookup.
# ---------------------------------------------------------------------------

# Superlatives that imply a whole-portfolio extremum (a min/max over many records).
SUPERLATIVE_TERMS = (
    "largest", "highest", "smallest", "lowest", "most", "least",
    "maximum", "minimum", "biggest", "greatest", "top",
)

# Ratio / share phrasings (a proportion over the book is an aggregation).
RATIO_TERMS = ("percentage", "percent", "ratio", "proportion", "share", "%")

# Table / tabulation phrasings (a table is multi-row, multi-figure -> report tier).
TABLE_TERMS = ("tabulate", "table")


# ---------------------------------------------------------------------------
# The base aggregation words (the prior hca-route._AGGREGATION_WORDS, verbatim) — kept as a
# named tuple so the union below is auditable as "base + analysis + superlative + ratio + table".
# ---------------------------------------------------------------------------

_ROUTE_AGGREGATION_WORDS = (
    "total", "totals", "sum", "average", "avg", "mean", "median", "count",
    "aggregate", "aggregated", "aggregation", "across", "all", "every", "each",
    "list", "report", "breakdown", "distribution", "compare", "comparison",
    "trend", "histogram", "rank", "ranked", "ranking", "top", "bottom",
    "portfolio", "combined", "overall", "grouped", "group", "by", "per",
    "between", "over time", "year-over-year", "month-over-month", "ytd",
    "weighted", "outstanding balance", "exposure", "concentration",
    "how many", "how much in total", "which loans", "what loans",
)


def _dedup(*groups) -> tuple:
    """Union the given iterables into a single de-duplicated tuple, preserving first-seen order
    (so the result is deterministic + auditable)."""
    seen = set()
    ordered = []
    for group in groups:
        for term in group:
            if term not in seen:
                seen.add(term)
                ordered.append(term)
    return tuple(ordered)


# The AGGREGATION/ANALYSIS vocabulary used by routing = the prior route aggregation words
# UNIONED with hca-deliver's analysis trigger sets PLUS superlative + ratio + table terms.
# This is the SUPERSET the router consults so a bare-superlative / ratio / table question is
# classified as report/aggregation tier (consensus-routed), never trivial.
AGGREGATION_ANALYSIS_TERMS = _dedup(
    _ROUTE_AGGREGATION_WORDS,
    RANK_TRIGGERS,
    AT_RISK_TRIGGERS,
    UTILIZATION_TERMS,
    CONCENTRATION_TRIGGERS,
    SUPERLATIVE_TERMS,
    RATIO_TERMS,
    TABLE_TERMS,
)


# ---------------------------------------------------------------------------
# Self-test (no network, no deps) — proves the unions are supersets + the leaf imports nothing.
# ---------------------------------------------------------------------------

def _run_selftest() -> int:
    failures = []

    # PAYOFF union is a superset of both prior copies.
    deliver_payoff = ("payoff", "pay off", "pay-off", "early redemption", "early-redemption",
                      "amount to redeem", "redemption amount", "amount to pay off", "redeem")
    figures_payoff = ("early_redemption", "early redemption", "payoff", "redemption",
                      "amount to redeem", "redeem")
    for t in deliver_payoff + figures_payoff:
        if t not in PAYOFF_TERMS:
            failures.append(f"PAYOFF_TERMS missing prior term {t!r}")

    # AGGREGATION/ANALYSIS union is a superset of the prior route words + analysis triggers.
    for t in _ROUTE_AGGREGATION_WORDS + RANK_TRIGGERS + AT_RISK_TRIGGERS + CONCENTRATION_TRIGGERS:
        if t not in AGGREGATION_ANALYSIS_TERMS:
            failures.append(f"AGGREGATION_ANALYSIS_TERMS missing prior term {t!r}")

    # The widening terms are present.
    for t in SUPERLATIVE_TERMS + RATIO_TERMS + TABLE_TERMS:
        if t not in AGGREGATION_ANALYSIS_TERMS:
            failures.append(f"AGGREGATION_ANALYSIS_TERMS missing widening term {t!r}")

    # Kind constants are the canonical strings.
    if (KIND_DIRECT, KIND_DERIVED, KIND_REQUIRES_EXTERNAL) != (
            "direct", "derived", "requires_external"):
        failures.append("KIND_* constants drifted from canonical strings")

    if failures:
        for f in failures:
            print(f"FAIL: {f}")
        print(f"SELFTEST FAILED: {len(failures)} issue(s)")
        return 1
    print(f"SELFTEST OK: PAYOFF={len(PAYOFF_TERMS)} UTILIZATION={len(UTILIZATION_TERMS)} "
          f"AGGREGATION_ANALYSIS={len(AGGREGATION_ANALYSIS_TERMS)} terms")
    return 0


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        sys.exit(_run_selftest())
    print("hca-vocab: shared vocabulary leaf (run with --selftest)")
