#!/usr/bin/env python3
"""
grade_fuse.py — Phase 3: two-axis grading + claim-level fusion (PLAN.md §3 Stage 3-4).

Deterministic. No model calls (the LLM's job is upstream — producing the candidate
claims + defect/upgrade flags; here we score and fuse them arithmetically).

GRADING (two SEPARATE axes, never blended — PLAN.md §6.1):
  Axis A — source reliability (A-F prior).
  Axis B — claim certainty (GRADE machine: baseline -> downgrade -> upgrade -> ordinal).
Confidence tier is DERIVED from independent cross-family agreement + provenance —
never model self-report. Single-source is capped at 'probable' (never 'verified').

FUSION (claim-level, PLAN.md §3 Stage 4):
  numeric -> median / trimmed mean (one hallucinated outlier can't move the median);
  categorical -> (weighted) majority;
  dual-track tally -> compute BOTH the equal-weighted and believability-weighted result;
  divergence between them raises a flag for the falsification gate.
"""

import statistics

# Axis B ordinal ladder, low -> high.
CERTAINTY = ["Very Low", "Low", "Moderate", "High"]


# --- grading -----------------------------------------------------------------

def _baseline_certainty(independent_sources, distinct_families, has_primary_citation):
    if has_primary_citation and independent_sources >= 2 and distinct_families >= 2:
        return "High"
    if has_primary_citation or (independent_sources >= 2 and distinct_families >= 2):
        return "Moderate"
    if independent_sources >= 1:
        return "Low"
    return "Very Low"


def _step(level, delta):
    i = CERTAINTY.index(level)
    return CERTAINTY[max(0, min(len(CERTAINTY) - 1, i + delta))]


def grade_claim(independent_sources, families, has_primary_citation=False,
                downgrades=None, upgrades=None, source_reliability=None,
                volatility=None, freshness=None):
    """Return {confidence, axis_a, axis_b, confidence_basis, reasons}.

    downgrades / upgrades are lists of (label, severity) where severity in {1,2}.
    source_reliability optionally overrides Axis A (an Admiralty A-F letter).

    RECENCY (opt-in; RESEARCH-recency-bias-2026-08-02.md §6.2 mechanisms e+f):
      volatility  the claim's class ('durable'|'slow'|'fast'|'volatile'), from
                  volatility.classify. None or 'durable' => recency is inert.
      freshness   the dict from volatility.compute_freshness (stale, severity,
                  recent_independent, gate_applies). None => recency is inert.
    When the classifier is confident (freshness['gate_applies']) and the claim is
    non-durable and STALE, a ('stale', severity) downgrade steps Axis B down AND
    the top tier requires >=1 RECENT independent source — otherwise 'verified'
    caps at 'probable'. Recency only ever CAPS; it never nullifies and never
    lowers the independence floor. Absent volatility+freshness, behavior is
    byte-for-byte the legacy path (every pre-recency test stays green).
    """
    downgrades = list(downgrades or [])
    upgrades = upgrades or []
    distinct_families = len(set(f for f in (families or []) if f))
    reasons = []

    # Recency (opt-in): a confident, non-durable, stale claim earns a stale downgrade.
    apply_recency = (freshness is not None and volatility not in (None, "durable")
                     and bool(freshness.get("gate_applies")))
    if apply_recency and freshness.get("stale"):
        sev = int(freshness.get("severity", 1)) or 1
        downgrades = downgrades + [("stale", sev)]

    # Axis B — baseline then modifiers.
    axis_b = _baseline_certainty(independent_sources, distinct_families, has_primary_citation)
    reasons.append(f"baseline certainty {axis_b} (indep={independent_sources}, families={distinct_families}, primary={has_primary_citation})")
    for label, sev in downgrades:
        axis_b = _step(axis_b, -int(sev))
        reasons.append(f"downgrade -{sev}: {label} -> {axis_b}")
    for label, sev in upgrades:
        axis_b = _step(axis_b, +int(sev))
        reasons.append(f"upgrade +{sev}: {label} -> {axis_b}")

    # Axis A — source reliability prior (default C = "fairly reliable/unknown").
    axis_a = source_reliability or "C"

    # Confidence tier — DERIVED, with the single-source cap.
    if independent_sources >= 2 and distinct_families >= 2 and axis_b in ("High", "Moderate"):
        confidence = "verified"
    elif independent_sources >= 1:
        confidence = "probable"
    else:
        confidence = "unverified"
    # Hard single-source cap (belt-and-suspenders; the ledger writer also enforces it).
    if confidence == "verified" and (independent_sources < 2 or distinct_families < 2):
        confidence = "probable"
        reasons.append("single-source/single-family cap applied -> probable")
    # Recent-corroboration requirement (mechanism f): a non-durable claim needs a
    # RECENT independent source to be 'verified'. Caps at 'probable', never lower.
    if confidence == "verified" and apply_recency and not freshness.get("recent_independent"):
        confidence = "probable"
        reasons.append("volatile-claim: no recent independent corroboration -> capped at probable")

    return {
        "confidence": confidence,
        "axis_a_source_reliability": axis_a,
        "axis_b_claim_certainty": axis_b,
        "confidence_basis": {
            "independent_sources": independent_sources,
            "distinct_families": distinct_families,
        },
        "volatility": volatility,
        "freshness": freshness,
        "reasons": reasons,
    }


# --- fusion ------------------------------------------------------------------

def _median(values):
    return statistics.median(values)


def _trimmed_mean(values):
    if len(values) >= 3:
        s = sorted(values)
        return statistics.fmean(s[1:-1])
    return statistics.fmean(values)


def _weighted_winner(pairs):
    """pairs = [(value, weight)] -> value with the greatest total weight (stable)."""
    tally = {}
    order = []
    for value, w in pairs:
        if value not in tally:
            tally[value] = 0.0
            order.append(value)
        tally[value] += w
    best = max(order, key=lambda v: tally[v])
    return best, tally


def fuse(candidates, claim_type="categorical", weights=None):
    """candidates = [{value, source_id}]. weights: optional {source_id: float}.

    Returns {fused_value, method, equal_result, weighted_result, divergence, detail}.
    Divergence (equal-track vs believability-weighted-track) is a confidence signal
    that must escalate to the falsification gate (PLAN.md §3 Stage 4).
    """
    values = [c["value"] for c in candidates]
    if weights is None:
        weights = {}

    if claim_type == "numeric":
        med = _median(values)
        tm = _trimmed_mean(values)
        # weighted track: weighted mean if weights given, else same as median-anchored
        if any(weights.values()):
            wsum = sum(weights.get(c["source_id"], 1.0) for c in candidates)
            wmean = sum(c["value"] * weights.get(c["source_id"], 1.0) for c in candidates) / wsum
        else:
            wmean = tm
        divergence = abs(med - wmean) > (abs(med) * 0.05 if med else 0.5)
        return {
            "fused_value": med, "method": "median",
            "equal_result": med, "weighted_result": wmean,
            "divergence": divergence,
            "detail": {"median": med, "trimmed_mean": tm, "weighted_mean": wmean},
        }

    # categorical / textual -> majority
    equal_pairs = [(c["value"], 1.0) for c in candidates]
    weighted_pairs = [(c["value"], weights.get(c["source_id"], 1.0)) for c in candidates]
    equal_winner, equal_tally = _weighted_winner(equal_pairs)
    weighted_winner, weighted_tally = _weighted_winner(weighted_pairs)
    divergence = equal_winner != weighted_winner
    return {
        "fused_value": equal_winner, "method": "majority",
        "equal_result": equal_winner, "weighted_result": weighted_winner,
        "divergence": divergence,
        "detail": {"equal_tally": equal_tally, "weighted_tally": weighted_tally},
    }
