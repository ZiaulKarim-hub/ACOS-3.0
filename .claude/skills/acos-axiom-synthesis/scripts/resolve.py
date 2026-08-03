#!/usr/bin/env python3
"""
resolve.py — Phase 5: conflict resolution (PLAN.md §3 Stage 6, §6.4-6.5).

When several claims contend for the SAME atomic fact, apply the precedence ladder
top-down and stop at the first rung that decides. If nothing decides, emit UNRESOLVED —
never fabricate a winner. Consensus polarity is chosen per decision type.

Deterministic. Stdlib only. (De-circularization must already have run — PLAN.md Rung 0.)
"""

_RELIABILITY_RANK = {"A": 6, "B": 5, "C": 4, "D": 3, "E": 2, "F": 1}
_TIER_RANK = {"verified": 3, "probable": 2, "unverified": 1}

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

# The "upper" rungs that OUTRANK guarded supersession (directness/originality/
# reliability/authority). Supersession sits BELOW these and ABOVE independent_sources,
# so a lone fresh low-tier source can never beat a stronger, more-direct one.
_UPPER = _LADDER[:4]


def _ladder_key(claim):
    return tuple(fn(claim) for _, fn in _LADDER)


def _upper_key(claim):
    return tuple(fn(claim) for _, fn in _UPPER)


def _deciding_rung(a, b):
    """Name of the first rung on which a and b differ, or None if identical."""
    for name, fn in _LADDER:
        if fn(a) != fn(b):
            return name
    return None


# ── Guarded supersession (recency; RESEARCH-recency-bias-2026-08-02.md §6.2) ───
# For NON-DURABLE conflicts only, a newer claim may retire an older one, but only
# under a strict three-part guard. This is the direct fix to "old accumulated
# corroboration out-scores a fresher, better claim" — WITHOUT letting a single
# fresh source win.

def _date_key(claim):
    """A comparable ISO 'YYYY-MM-DD' date for the claim's as_of, or '' if absent.
    Well-formed ISO dates sort chronologically as strings."""
    d = claim.get("as_of")
    return d[:10] if isinstance(d, str) and len(d) >= 10 else ""


def _tier(claim):
    return _TIER_RANK.get(claim.get("confidence") or claim.get("tier"), 1)


def _corroborated(claim):
    """The supersession corroboration gate: >=2 independent sources, OR an
    authoritative/primary source. A lone fresh source fails this."""
    return int(claim.get("independent_sources", 0)) >= 2 or bool(claim.get("authority"))


def _try_supersession(claims):
    """Return a resolved-by-supersession verdict, or None to fall through to the
    normal ladder. Fires ONLY when the NEWEST claim and the INCUMBENT tie on the
    upper rungs (so a higher rung isn't already deciding between that pair) and the
    guard holds; a failed guard falls through (the well-corroborated older claim can
    still win on independent_sources)."""
    dated = [c for c in claims if _date_key(c)]
    if len(dated) < 2:
        return None  # need two dated claims to compare recency
    newest = max(dated, key=_date_key)
    incumbents = [c for c in claims if c is not newest]
    # The incumbent = the OLDER claim with the most accumulated corroboration/tier.
    incumbent = max(incumbents, key=lambda c: (int(c.get("independent_sources", 0)), _tier(c)))
    # Review fix F3: compare the upper rungs on the NEWEST-vs-INCUMBENT pair — not
    # the top two overall. In a 3+-claim conflict the old check let a newest
    # reliability-D claim supersede a reliability-A incumbent because two OTHER
    # claims happened to tie at the top. If any upper rung separates this pair,
    # supersession abstains and the classic ladder decides.
    if _upper_key(newest) != _upper_key(incumbent):
        return None
    if _date_key(newest) <= _date_key(incumbent):
        return None  # not strictly newer than the strongest older claim
    # THE GUARD: newer AND equal-or-higher tier AND independently corroborated.
    if _tier(newest) >= _tier(incumbent) and _corroborated(newest):
        alts = [dict(c, why_not_adopted="superseded by a newer, corroborated, "
                     "equal-or-higher-tier claim") for c in claims if c is not newest]
        return {"status": "resolved", "winner": newest, "alternatives": alts,
                "reason": "guarded supersession: a newer, independently-corroborated, "
                          "equal-or-higher-tier claim retires the older one",
                "deciding_rung": "supersession",
                "superseded": [c.get("id") for c in incumbents if c.get("id")]}
    return None  # guard fails -> fall through to the existing ladder (no fabricated winner)


def resolve_conflict(claims, polarity="quorum", volatility=None):
    """claims = [claim_dict, ...] contending for one fact.

    polarity:
      "quorum"             -> precedence ladder decides (default).
      "asymmetric_veto"    -> any dissent blocks adoption (false-accept is catastrophic).
      "unanimous_or_keep_all" -> adopt only if all agree; else keep all as alternatives.

    volatility: the conflict's claim class. For a NON-DURABLE conflict ('slow'|
      'fast'|'volatile'), a guarded supersession rung is consulted BEFORE the
      accumulation-based rungs, so a newer, corroborated, equal-or-higher-tier
      claim can retire an older well-corroborated one. None or 'durable' leaves the
      classic ladder untouched (old accumulated evidence legitimately wins).

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

    # Guarded supersession (recency) — only for non-durable conflicts, and only as
    # a rung below directness/originality/reliability/authority and above
    # independent_sources. A failed guard falls through to the classic ladder.
    if volatility not in (None, "durable"):
        superseded = _try_supersession(claims)
        if superseded is not None:
            return superseded

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
