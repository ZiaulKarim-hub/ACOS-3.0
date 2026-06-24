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
  - This module imports NOTHING from the skill (no hca-* sibling). It is a pure leaf so it can
    NEVER participate in a circular import. The consumers import FROM here, never the reverse.
    Stdlib only (imports just `re`, used by the shape-detection heuristics below).
  - The aggregation/analysis vocabulary is a strict SUPERSET of the prior per-module copies:
    every phrasing that previously matched still matches (the union only ADDS phrasings).
  - Trust direction: when adding terms here, only ever WIDEN the consensus-routed set. Never
    move a superlative / ratio / aggregation phrasing OUT of the consensus path.
  - A flat allowlist CANNOT bound natural language: rounds 1-3 each missed a different extremum
    synonym (worst/best, then fewest/shortest/safest/...). So consensus routing ALSO uses
    has_structural_aggregation_shape() below — it detects the SHAPE of a portfolio operation
    (an "-est" superlative suffix, a comparator+threshold filter, a statistical term) rather than
    enumerating every word. Conservative by design: over-routing to consensus is safe; the only
    unsafe direction is a whole-portfolio question slipping to the trivial (no-consensus) path.

GROUND RULES (memory/decisions/2026-06-18-hca-build-ground-rules.md):
  - Python 3 stdlib ONLY. No third-party deps. No network. No model calls.
"""

from __future__ import annotations

import re


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
# Includes the natural credit-extremum words "worst"/"best" (and price extremes) — round-2
# review found "worst DSCR" / "best loan" bypassed consensus because they were omitted here.
SUPERLATIVE_TERMS = (
    "largest", "highest", "smallest", "lowest", "most", "least",
    "maximum", "minimum", "biggest", "greatest", "top",
    "worst", "best", "priciest", "cheapest",
)

# Ratio / share phrasings (a proportion over the book is an aggregation). "fraction"/"portion"
# added in round 2 ("what fraction of loans are overdue" must be consensus-routed).
RATIO_TERMS = ("percentage", "percent", "ratio", "proportion", "share", "%",
               "fraction", "portion")

# Table / tabulation phrasings (a table is multi-row, multi-figure -> report tier).
TABLE_TERMS = ("tabulate", "table")

# Statistical-dispersion phrasings (a statistic computed across many records is an aggregation).
# ("mean"/"median"/"average" already live in the base aggregation words; these ADD the rest.)
STATISTICAL_TERMS = (
    "mode", "spread", "dispersion", "variance", "standard deviation", "std dev", "stdev",
    "percentile", "quartile", "skew", "kurtosis",
)


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
    STATISTICAL_TERMS,
)


# ---------------------------------------------------------------------------
# Structural shape detection — the part that does NOT depend on a flat allowlist.
# Rounds 1-3 each missed a different extremum synonym; a curated word list cannot bound an
# open-ended synonym space. These rules detect the SHAPE of a whole-portfolio operation so the
# router/planner route it to consensus regardless of the exact word used.
# ---------------------------------------------------------------------------

# Words ending in "-est" that are NOT superlatives — they must not trip the suffix rule.
# "interest" is the critical one (ubiquitous in loan queries); the rest are common English
# -est nouns/verbs/adjectives that can legitimately appear in a single-record question.
_EST_NONSUPERLATIVE = frozenset({
    "interest", "request", "test", "contest", "protest", "invest", "harvest", "honest",
    "modest", "rest", "guest", "forest", "west", "vest", "suggest", "digest", "manifest",
    "midwest", "conquest", "behest", "arrest", "unrest", "bequest", "ingest", "attest",
    "detest", "infest", "molest", "crest", "quest", "nest", "pest", "fest", "jest", "zest",
    "wrest", "lest", "gest", "earnest", "tempest",
})

# An "-est" superlative (fewest/shortest/longest/safest/tightest/soonest/highest/...). The
# exclusion set above removes the non-superlative -est words.
_EST_SUPERLATIVE_RE = re.compile(r"\b([a-z]{3,}est)\b")

# A comparator + threshold-number filter ("loans below 1.2", "under $1m", "more than 3 loans").
# Requires a comparator word AND a nearby number, so a bare "above"/"over time" does NOT fire.
_THRESHOLD_FILTER_RE = re.compile(
    r"\b(?:below|under|over|above|less than|greater than|more than|fewer than|"
    r"at least|at most|no more than|no less than|exceeding|exceeds|in excess of)\b"
    r"[^.\n]{0,15}?\$?\d"
)


def has_structural_aggregation_shape(q_lower: str) -> bool:
    """True when a question has the SHAPE of a whole-portfolio operation, independent of the flat
    vocabulary allowlists. Detects: (1) any '-est' superlative suffix (minus the non-superlative
    -est words); (2) a comparator + threshold-number filter; (3) a statistical-dispersion term.
    Conservative by design — over-routing to consensus is safe; under-routing is a trust bypass.
    Expects an already-lowercased question."""
    for m in _EST_SUPERLATIVE_RE.finditer(q_lower):
        if m.group(1) not in _EST_NONSUPERLATIVE:
            return True
    if _THRESHOLD_FILTER_RE.search(q_lower):
        return True
    for t in STATISTICAL_TERMS:
        if " " in t:
            if t in q_lower:
                return True
        elif re.search(r"\b" + re.escape(t) + r"\b", q_lower):
            return True
    return False


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

    # Structural shape detection catches the open-ended extremum/filter/stat phrasings the flat
    # allowlist omitted across rounds 1-3, WITHOUT false-firing on the ubiquitous word "interest".
    for q in ("fewest days to maturity", "shortest tenor", "the safest loan",
              "loans under $1m", "loans below 1.2x coverage", "spread of rates",
              "standard deviation of balances", "tightest covenant headroom"):
        if not has_structural_aggregation_shape(q):
            failures.append(f"structural shape MISSED a portfolio operation: {q!r}")
    for q in ("what is the interest rate of loan 134",
              "what is the accrued interest on loan 5"):
        if has_structural_aggregation_shape(q):
            failures.append(f"structural shape FALSE-FIRED on a single-loan question: {q!r}")

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
