#!/usr/bin/env python3
"""
resolve.py — Phase 5: conflict resolution (PLAN.md §3 Stage 6, §6.4-6.5).

When several claims contend for the SAME atomic fact, apply the precedence ladder
top-down and stop at the first rung that decides. If nothing decides, emit UNRESOLVED —
never fabricate a winner. Consensus polarity is chosen per decision type.

Deterministic. Stdlib only. (De-circularization must already have run — PLAN.md Rung 0.)
"""

_RELIABILITY_RANK = {"A": 6, "B": 5, "C": 4, "D": 3, "E": 2, "F": 1}

# Ladder rungs, in priority order (each: higher value = stronger). PLAN.md §6.4 rungs 1-9.
_LADDER = [
    ("directness", lambda c: int(c.get("directness", 0))),
    ("originality", lambda c: int(c.get("originality", 0))),
    ("reliability", lambda c: _RELIABILITY_RANK.get(c.get("reliability", "C"), 4)),
    ("authority", lambda c: 1 if c.get("authority") else 0),
    ("independent_sources", lambda c: int(c.get("independent_sources", 0))),
    ("evidentiary_weight", lambda c: int(c.get("evidentiary_weight", 0))),
    ("specificity", lambda c: int(c.get("specificity", 0))),
    ("recency_correction", lambda c: 1 if c.get("recency_correction") else 0),
    ("coi", lambda c: int(c.get("coi", 0))),
]


def _ladder_key(claim):
    return tuple(fn(claim) for _, fn in _LADDER)


def _deciding_rung(a, b):
    """Name of the first rung on which a and b differ, or None if identical."""
    for name, fn in _LADDER:
        if fn(a) != fn(b):
            return name
    return None


def resolve_conflict(claims, polarity="quorum"):
    """claims = [claim_dict, ...] contending for one fact.

    polarity:
      "quorum"             -> precedence ladder decides (default).
      "asymmetric_veto"    -> any dissent blocks adoption (false-accept is catastrophic).
      "unanimous_or_keep_all" -> adopt only if all agree; else keep all as alternatives.

    Returns {status, winner, alternatives, reason, deciding_rung}.
      status in {"resolved","unresolved","vetoed","keep_all","trivial"}
    """
    if not claims:
        return {"status": "unresolved", "winner": None, "alternatives": [], "reason": "no claims", "deciding_rung": None}
    if len(claims) == 1:
        return {"status": "trivial", "winner": claims[0], "alternatives": [], "reason": "single claim", "deciding_rung": None}

    distinct_values = {c.get("value", c.get("statement")) for c in claims}

    if polarity == "asymmetric_veto" and len(distinct_values) > 1:
        return {"status": "vetoed", "winner": None, "alternatives": claims,
                "reason": "asymmetric-veto: a single dissent blocks adoption where false-accept is catastrophic",
                "deciding_rung": None}

    if polarity == "unanimous_or_keep_all" and len(distinct_values) > 1:
        return {"status": "keep_all", "winner": None, "alternatives": claims,
                "reason": "not unanimous — keeping all candidates (no winner selected)",
                "deciding_rung": None}

    if len(distinct_values) == 1:
        return {"status": "resolved", "winner": claims[0], "alternatives": [],
                "reason": "all claims agree on the value", "deciding_rung": None}

    # quorum -> precedence ladder
    ranked = sorted(claims, key=_ladder_key, reverse=True)
    top, second = ranked[0], ranked[1]
    if _ladder_key(top) == _ladder_key(second):
        return {"status": "unresolved", "winner": None, "alternatives": ranked,
                "reason": "TERMINAL RUNG: no rung decides between the top candidates — refusing to fabricate a winner",
                "deciding_rung": None}
    return {"status": "resolved", "winner": top, "alternatives": ranked[1:],
            "reason": f"precedence ladder decided at rung '{_deciding_rung(top, second)}'",
            "deciding_rung": _deciding_rung(top, second)}
