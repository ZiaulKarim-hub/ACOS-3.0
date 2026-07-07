#!/usr/bin/env python3
"""
lifecycle.py — Phase 6: living re-synthesis helpers (PLAN.md §4, §3 Stage 7).

The state machine, supersede-not-overwrite, and archival all live in axiom_ledger.py
(the substrate). This module adds the DEMOTION CASCADE: when a claim is demoted
(REFUTED / SUPERSEDED / CONTESTED), every claim that depends on it must be re-evaluated
(truth-maintenance). Pure functions over the ledger. Stdlib only.
"""

import axiom_ledger as al

_DEMOTED = {"REFUTED", "SUPERSEDED", "CONTESTED"}


def reverse_deps(records):
    """Map claim_id -> [ids of current claims that depend_on it]."""
    cur = al.current_states(records)
    rev = {}
    for cid, rec in cur.items():
        for dep in (rec.get("depends_on") or []):
            rev.setdefault(dep, []).append(cid)
    return rev


def cascade_targets(records, demoted_id):
    """Transitive set of claim ids that must be re-evaluated because `demoted_id`
    was demoted. BFS over the reverse-dependency graph (excludes the demoted claim)."""
    rev = reverse_deps(records)
    seen, queue, out = {demoted_id}, list(rev.get(demoted_id, [])), []
    while queue:
        cid = queue.pop(0)
        if cid in seen:
            continue
        seen.add(cid)
        out.append(cid)
        queue.extend(rev.get(cid, []))
    return out


def newly_demoted(records):
    """Current claims whose state is a demotion — the roots of any cascade."""
    cur = al.current_states(records)
    return [cid for cid, rec in cur.items() if rec.get("state") in _DEMOTED]


def cascade_plan(records):
    """For every currently-demoted claim, the dependents that need re-evaluation."""
    plan = {}
    for did in newly_demoted(records):
        targets = cascade_targets(records, did)
        if targets:
            plan[did] = targets
    return plan
