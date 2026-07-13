#!/usr/bin/env python3
"""
falsify.py — Phase 4: the falsification gate + nullification checklist (PLAN.md §3 Stage 5, §6.3).

The load-bearing gate. Every candidate claim passes through here before it can be
promoted. Default disposition of an unprocessed claim is quarantine, NOT accept.

The model-dependent steps (ACH, the independent different-family refuter) are performed
UPSTREAM by an injected agent_runner; this module consumes their structured results and
applies the deterministic disposition logic + the oscillation guard.

Returns a disposition:
  "keep"     — survived cleanly; gate PASSED.
  "downgrade"— survived with a soft trigger; gate PASSED but tier is lowered one step.
  "nullify"  — a hard trigger fired; gate FAILED; claim dropped/quarantined.

gate_state ("passed"/"failed") is what the ledger writer's falsification-gate invariant
checks before allowing promotion above CONJECTURE.
"""

import oscillation_guard as og

HARD_TRIGGERS = [
    "unfalsifiable",
    "refuted_by_higher_tier",
    "internal_contradiction",
    "fabrication_no_origin",
    "ach_most_inconsistent",
]
SOFT_TRIGGERS = [
    "conflict_of_interest",
    "stale",
    "non_reproducible",
    "vertical_only",
    "non_independent_consensus",
    "refuter_unrebutted",
]
# NOTE: the single-source cap is deliberately NOT a falsification-gate trigger. It is
# owned by grade_claim() (caps at 'probable') and the ledger's corroboration-gate
# invariant. Re-penalizing it here would double-downgrade (probable -> unverified).

# lower -> higher tier
TIERS = ["unverified", "probable", "verified"]


def downgrade_tier(tier):
    i = TIERS.index(tier) if tier in TIERS else 0
    return TIERS[max(0, i - 1)]


def run_gate(claim, refuter=None, settled_path=None):
    """Apply the falsification gate to one claim.

    claim = {
      "falsifiable": bool,
      "independent_sources": int,
      "flags": { <trigger_name>: bool, ... },   # detections from earlier stages
    }
    refuter = {"objection": str|None, "credible": bool, "rebutted": bool} | None
      — the verdict from the independent, different-family refuter (via agent_runner).
    settled_path — path to settled-objections.jsonl for the oscillation guard.

    Returns {disposition, gate_state, hard, soft, new_disconfirmers, oscillation_skipped}.
    """
    flags = claim.get("flags", {}) or {}
    hard, soft, new_disconfirmers = [], [], []
    oscillation_skipped = False

    # Step 0 — admissibility (Popper): unfalsifiable claims are opinion, not truth.
    if not claim.get("falsifiable", True):
        hard.append("unfalsifiable")

    for k in HARD_TRIGGERS:
        if k == "unfalsifiable":
            continue
        if flags.get(k):
            hard.append(k)

    # Soft (flag-based) triggers. The single-source cap is intentionally absent here
    # (owned by grading + the ledger invariant) to avoid double-downgrading.
    for k in SOFT_TRIGGERS:
        if k == "refuter_unrebutted":
            continue
        if flags.get(k):
            soft.append(k)

    # Step 4 — independent refuter, mediated by the oscillation guard.
    if refuter and refuter.get("objection"):
        objection = refuter["objection"]
        already = settled_path and og.is_settled(settled_path, objection)
        if already:
            oscillation_skipped = True  # settled — do NOT act on it again
        elif refuter.get("credible") and not refuter.get("rebutted"):
            soft.append("refuter_unrebutted")
            new_disconfirmers.append(objection)
            if settled_path:
                og.record(settled_path, objection,
                          ruling="credible & unrebutted -> claim downgraded; disconfirmer recorded",
                          disposition="downgrade")

    if hard:
        disposition, gate_state = "nullify", "failed"
    elif soft:
        disposition, gate_state = "downgrade", "passed"
    else:
        disposition, gate_state = "keep", "passed"

    return {
        "disposition": disposition,
        "gate_state": gate_state,
        "hard": hard,
        "soft": soft,
        "new_disconfirmers": new_disconfirmers,
        "oscillation_skipped": oscillation_skipped,
    }
