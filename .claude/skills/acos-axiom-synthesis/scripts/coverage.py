#!/usr/bin/env python3
"""
coverage.py — Phase 7: the final coverage gate (PLAN.md §15.5).

Before declaring a synthesis done, confirm it covers every facet of the scoped
question — no sub-question left with zero (non-terminal) claims. The epistemic analog
of acos-synthesis-protocol's success-criteria coverage gate. Pure function. Stdlib only.
"""

import axiom_ledger as al

_TERMINAL = {"REFUTED", "SUPERSEDED"}


def coverage_gate(sub_questions, records):
    """sub_questions = [id, ...]; each current claim may carry a 'covers' list of
    sub-question ids (or a single 'sub_question'). Returns coverage + ok flag."""
    cur = al.current_states(records)
    covered = {sq: [] for sq in sub_questions}
    for cid, rec in cur.items():
        if rec.get("state") in _TERMINAL:
            continue  # a refuted/superseded claim does not cover anything
        covers = rec.get("covers")
        if covers is None and rec.get("sub_question") is not None:
            covers = [rec["sub_question"]]
        for sq in (covers or []):
            if sq in covered:
                covered[sq].append(cid)
    uncovered = [sq for sq, claims in covered.items() if not claims]
    return {"covered": covered, "uncovered": uncovered, "ok": len(uncovered) == 0}
