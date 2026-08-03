#!/usr/bin/env python3
"""
volatility.py — the volatility classifier + freshness computation for the
recency discipline (RESEARCH-recency-bias-2026-08-02.md §4, §6).

WHY THIS EXISTS. Grading confidence by independent corroboration structurally
favors OLD claims (more time to accumulate sources). This module is the lever
that corrects for that WITHOUT letting "newest wins": it labels each claim's
volatility and decides whether the claim is STALE, so downstream stages can cap
(never nullify) a stale, non-durable claim and surface it to the reader.

TWO PUBLIC PIECES:
  classify(statement, domain, judge_label, cfg)
      -> {volatility, confidence, flagged, basis}
      A cheap DETERMINISTIC lexical+domain pass yields a prior; an optional blind
      judge label is reconciled. ADVISORY + ASYMMETRIC: on any signal it may only
      move a claim toward MORE volatile (high recall), and it NEVER nullifies —
      it only produces a label + a confidence. Low confidence => flag, don't cap.

  compute_freshness(volatility, source_dates, today, cfg, confidence)
      -> {freshness_ok, recent_independent, stale, severity, gate_applies,
          newest_as_of, newest_age_days, window_days, reason}
      A source counts as "recent" only if its date is within the class window.
      DECISION B: a source with NO reliable date is unknown-age and CANNOT satisfy
      the "recent" requirement (but does not nullify the claim). Durable claims are
      exempt (freshness_ok always True — age is not a defect).

The freshness cap only BITES when the classifier is confident (gate_applies). An
unclassifiable claim (unknown default) is flagged, not penalized.

CONFIG. Knobs live in config/volatility.yaml (a FLAT file the minimal stdlib YAML
reader can actually parse). DEFAULT_VOLATILITY below is the embedded source-of-
truth fallback; load_volatility() overlays any values read from the file on top,
so a missing/edited/corrupt file degrades gracefully.

Stdlib only. Python 3.8+.
"""

import copy
import datetime
import os
import re

# Reuse the skill's minimal YAML reader (no third-party yaml dependency).
import checklist as _chk


CLASSES = ("durable", "slow", "fast", "volatile")
# Higher rank = MORE volatile. Used for "take the more volatile class" (high recall).
_RANK = {"durable": 0, "slow": 1, "fast": 2, "volatile": 3}


# ── Embedded canonical config (mirror of config/volatility.yaml) ──────────────
DEFAULT_VOLATILITY = {
    "version": 1,
    # None window = infinite (never stale).
    "windows": {"durable": None, "slow": 1095, "fast": 183, "volatile": 14},
    "stale_k": 1.0,
    "unknown_default": "slow",
    "flag_unknown": True,
    "lexical": {
        "volatile": [
            "as of today", "as of now", "currently", "right now", "today",
            "price", "prices", "interest rate", "exchange rate", "rates", "yield",
            "spot price", "intraday", "live", "breaking", "current standings",
            "as of this",
        ],
        "fast": [
            "latest", "newest", "current", "current best", "state-of-the-art",
            "state of the art", "sota", "leading", "record-breaking", "cutting-edge",
            "frontier", "this version", "deprecated", "preprint", "in beta",
            "just released", "emerging", "new release",
        ],
        "slow": [
            "population", "demographics", "gdp", "market share", "membership",
            "headcount", "median income", "workforce",
        ],
    },
    "domain_priors": {
        "math": "durable", "history": "durable", "geography": "durable",
        "definition": "durable", "physics": "durable", "constant": "durable",
        "biography": "durable",
        "law": "slow", "legal": "slow", "demographics": "slow", "medicine": "slow",
        "clinical": "slow", "government": "slow", "education": "slow",
        "technology": "fast", "software": "fast", "ai": "fast", "ml": "fast",
        "benchmark": "fast", "research": "fast",
        "security": "volatile", "cve": "volatile", "market": "volatile",
        "markets": "volatile", "price": "volatile", "prices": "volatile",
        "rate": "volatile", "rates": "volatile", "crypto": "volatile",
        "weather": "volatile",
    },
}


# ── Config loading (flat overlay onto the embedded default) ───────────────────

def default_config_path():
    """The shipped volatility.yaml next to this scripts/ dir (../config/volatility.yaml)."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "config", "volatility.yaml")


def _split_phrases(value):
    """'a, b c, d' -> ['a', 'b c', 'd'] (comma-separated; phrases may hold spaces)."""
    if not isinstance(value, str):
        return None
    return [p.strip().lower() for p in value.split(",") if p.strip()]


def _parse_priors(value):
    """'math=durable, ai=fast' -> {'math':'durable','ai':'fast'} (valid classes only)."""
    if not isinstance(value, str):
        return None
    out = {}
    for pair in value.split(","):
        pair = pair.strip()
        if "=" not in pair:
            continue
        k, _, v = pair.partition("=")
        k, v = k.strip().lower(), v.strip().lower()
        if k and v in CLASSES:
            out[k] = v
    return out or None


def _overlay(cfg, parsed):
    """Overlay FLAT keys from a parsed volatility.yaml onto cfg (in place)."""
    if not isinstance(parsed, dict):
        return
    win_map = {"window_durable": "durable", "window_slow": "slow",
               "window_fast": "fast", "window_volatile": "volatile"}
    for flat_key, cls in win_map.items():
        if flat_key in parsed:
            v = parsed[flat_key]
            # int/None only; a bad value leaves the default in place.
            # bool is an int subclass in Python — `window_fast: true` must NOT
            # become a 1-day window (review fix F6).
            if v is None or (isinstance(v, int) and not isinstance(v, bool)):
                cfg["windows"][cls] = v
    if "stale_k" in parsed:
        try:
            cfg["stale_k"] = float(parsed["stale_k"])
        except (TypeError, ValueError):
            pass
    if isinstance(parsed.get("unknown_default"), str) and parsed["unknown_default"] in CLASSES:
        cfg["unknown_default"] = parsed["unknown_default"]
    if isinstance(parsed.get("flag_unknown"), bool):
        cfg["flag_unknown"] = parsed["flag_unknown"]
    for flat_key, cls in (("lexical_volatile", "volatile"),
                          ("lexical_fast", "fast"), ("lexical_slow", "slow")):
        phrases = _split_phrases(parsed.get(flat_key))
        if phrases is not None:
            cfg["lexical"][cls] = phrases
    priors = _parse_priors(parsed.get("domain_priors"))
    if priors is not None:
        cfg["domain_priors"] = priors


def load_volatility(path=None):
    """Return the volatility config dict.

    Deep-copies the embedded DEFAULT_VOLATILITY, then overlays any values it can
    read from the FLAT volatility.yaml. On ANY problem (missing file, parse error)
    the pure default is returned — recency knobs never block a run.
    """
    cfg = copy.deepcopy(DEFAULT_VOLATILITY)
    if path is None:
        path = default_config_path()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            parsed = _chk._parse_yaml(fh.read())
        _overlay(cfg, parsed)
    except Exception:
        pass
    return cfg


# ── Classification ────────────────────────────────────────────────────────────

def _lexical_class(text, cfg):
    """The MOST volatile class whose signal phrases appear in text (or None).

    WHOLE-WORD matching (review fix F2): raw substring matching fired 'sota'
    inside "Minnesota", 'rates' inside "operates", 'live' inside "delivered" —
    false volatile/fast hits at gate-applying confidence. \\b boundaries stop
    that; multi-word phrases still match normally."""
    low = (text or "").lower()
    for cls in ("volatile", "fast", "slow"):   # most volatile first
        for phrase in cfg["lexical"].get(cls, []):
            if phrase and re.search(r"\b" + re.escape(phrase) + r"\b", low):
                return cls, phrase
    return None, None


def classify(statement, domain=None, judge_label=None, cfg=None):
    """Classify one claim's volatility. ADVISORY + ASYMMETRIC (may only move a claim
    toward MORE volatile; never nullifies).

    Returns {volatility, confidence, flagged, basis}:
      volatility  one of CLASSES
      confidence  'high' | 'medium' | 'low' — the freshness cap only bites on
                  high/medium (see compute_freshness gate_applies).
      flagged     bool — surfaced to the reader (unknown default or judge conflict).
      basis       trace of what drove the decision.
    """
    cfg = cfg or DEFAULT_VOLATILITY
    lex_cls, lex_phrase = _lexical_class(statement, cfg)
    dom_cls = None
    if domain:
        dom_cls = cfg["domain_priors"].get(str(domain).strip().lower())

    signals = [c for c in (lex_cls, dom_cls) if c]
    flagged = False
    if len(signals) == 2 and lex_cls != dom_cls:
        # Review fix F1 — DISAGREEING signals WIDEN uncertainty (mirrors the judge
        # rule below): take the more volatile reading, but at LOW confidence (the
        # freshness cap stays disarmed) and flag it. Two clashing clues must never
        # count as MORE certainty than one clean clue.
        prior = max(signals, key=lambda c: _RANK[c])
        base_conf = "low"
        flagged = True
    elif signals:
        # One signal, or two that AGREE. Agreement is the only path to 'high'.
        prior = signals[0]
        base_conf = "high" if len(signals) == 2 else "medium"
    else:
        prior = cfg.get("unknown_default", "slow")
        base_conf = "low"
        flagged = bool(cfg.get("flag_unknown", True))

    volatility, confidence = prior, base_conf
    if judge_label in CLASSES:
        if not signals:
            # F4: the judge is the ONLY real signal — the prior was just the
            # unknown-default fallback, so this is NOT a disagreement. Take the
            # judge's class at one-signal confidence (medium, gate armed),
            # unflagged. Without this, a blind-judge label could never arm the
            # freshness gate on lexically-quiet claims, making the live wiring moot.
            volatility, confidence, flagged = judge_label, "medium", False
        elif judge_label == prior:
            confidence = "high"
        else:
            # Disagreement WIDENS uncertainty: take the more volatile reading but
            # drop confidence to low (so the cap does NOT bite) and flag it.
            volatility = max((prior, judge_label), key=lambda c: _RANK[c])
            confidence = "low"
            flagged = True

    return {
        "volatility": volatility,
        "confidence": confidence,
        "flagged": flagged,
        "basis": {
            "lexical": lex_cls, "lexical_phrase": lex_phrase,
            "domain": dom_cls, "judge": judge_label, "prior": prior,
        },
    }


# ── Date helpers ──────────────────────────────────────────────────────────────

def parse_date(s):
    """Parse a leading 'YYYY-MM-DD' (or full ISO) into a date, or None if unparseable."""
    if not isinstance(s, str) or len(s) < 10:
        return None
    try:
        return datetime.date.fromisoformat(s[:10])
    except ValueError:
        return None


def days_between(later, earlier):
    """Whole days from `earlier` to `later` (both ISO strings). None if either is
    unparseable. A negative result (source dated in the future) is clamped to 0."""
    a, b = parse_date(later), parse_date(earlier)
    if a is None or b is None:
        return None
    return max(0, (a - b).days)


# ── Freshness ─────────────────────────────────────────────────────────────────

def window_for(volatility, cfg=None):
    """The freshness window in days for a class (None = infinite / never stale)."""
    cfg = cfg or DEFAULT_VOLATILITY
    return cfg["windows"].get(volatility)


def compute_freshness(volatility, source_dates, today, cfg=None, confidence="high"):
    """Decide whether a claim is stale from the dates of its INDEPENDENT sources.

    source_dates : list of ISO date strings (one per independent source). A None or
                   unparseable entry is 'unknown-age' and cannot count as recent
                   (Decision B).
    today        : the run's reference date (ISO 'YYYY-MM-DD').
    confidence   : the classifier confidence — the cap only bites on high/medium.

    Returns a dict; the load-bearing keys downstream:
      freshness_ok      fed to the N5-NOT-STALE checklist question + the grade cap.
                        True when NOT stale, OR when the gate does not apply.
      recent_independent True iff >=1 independent source is dated within the window.
      stale             objective: no independent source within the window.
      severity          stale downgrade size (1 slow, 2 fast/volatile), else 0.
      gate_applies      whether staleness is allowed to lower the tier (confidence).
    """
    cfg = cfg or DEFAULT_VOLATILITY
    window = window_for(volatility, cfg)
    dates = list(source_dates or [])

    ages = [(d, days_between(today, d)) for d in dates]
    known = [(d, a) for (d, a) in ages if a is not None]
    newest_as_of, newest_age = None, None
    if known:
        d, a = min(known, key=lambda x: x[1])   # smallest age = most recent
        newest_as_of, newest_age = d, a

    # Durable / infinite window: age is not a defect.
    if volatility == "durable" or window is None:
        return {
            "freshness_ok": True, "recent_independent": True, "stale": False,
            "severity": 0, "gate_applies": False, "newest_as_of": newest_as_of,
            "newest_age_days": newest_age, "window_days": window,
            "reason": "durable / infinite window — age is not a defect",
        }

    k = float(cfg.get("stale_k", 1.0))
    limit = window * k
    recent = [(d, a) for (d, a) in known if a <= limit]
    recent_independent = len(recent) >= 1
    stale = not recent_independent
    gate_applies = confidence in ("high", "medium")
    severity = 0
    if stale:
        severity = 2 if volatility in ("fast", "volatile") else 1
    # freshness_ok caps the tier ONLY when the gate applies (confident classification).
    freshness_ok = (not stale) or (not gate_applies)

    if stale and not known:
        reason = "no independent source carries a reliable date -> cannot satisfy 'recent'"
    elif stale:
        reason = (f"newest independent source is {newest_age}d old, past the "
                  f"{int(limit)}d {volatility} window")
    else:
        reason = f"a recent independent source exists within the {int(limit)}d {volatility} window"

    return {
        "freshness_ok": freshness_ok, "recent_independent": recent_independent,
        "stale": stale, "severity": severity, "gate_applies": gate_applies,
        "newest_as_of": newest_as_of, "newest_age_days": newest_age,
        "window_days": window, "reason": reason,
    }


if __name__ == "__main__":
    import json as _json
    cfg = load_volatility()
    demo = {
        "durable fact": classify("The capital of Australia is Canberra.", domain="geography"),
        "fast fact": classify("GPT-5 is the current best model on the benchmark.", domain="ai"),
        "volatile fact": classify("The federal funds rate is 4.25% as of today.", domain="rates"),
        "unknown": classify("Widgets improve throughput.", domain=None),
    }
    print(_json.dumps(demo, indent=2))
    print(_json.dumps(compute_freshness("fast", ["2026-01-01", None], "2026-08-02", cfg), indent=2))
