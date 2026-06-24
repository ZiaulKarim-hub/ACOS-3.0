#!/usr/bin/env python3
"""hca-route.py — Intake & Tier Router for acos-hypercore-ask.

Classifies a natural-language question into a verification tier:

  - "trivial-lookup"            single value / single record, no aggregation
  - "report/aggregation/analysis"   multi-record, math, list, cross-entity

This is a DETERMINISTIC, rule-based classifier. It does NOT fetch data, make any
network call, or talk to Hypercore. (SLICE-HCA-01; downstream stages are
forward-references — see SKILL.md and slices 02+.)

Ground rules (locked in memory/decisions/2026-06-18-hca-build-ground-rules.md):
  - Python 3 stdlib ONLY. No third-party deps. No network imports.
  - Subscription-only: never ANTHROPIC_API_KEY; no model API calls here.

Usage:
  python3 hca-route.py "What is the maturity date of loan L-001?"   -> prints tier
  python3 hca-route.py --selftest                                   -> runs self-test
  python3 hca-route.py --json "..."                                 -> prints JSON

NOTE on imports: this module intentionally imports ONLY `re`, `sys`, `json`,
`argparse`. There is deliberately NO `urllib`, `http`, `http.client`, `socket`,
`requests`, or `ssl` import — the router never touches the network.
"""

import argparse
import datetime
import importlib.util
import json
import os
import re
import sys

TIER_TRIVIAL = "trivial-lookup"
TIER_REPORT = "report/aggregation/analysis"


# --- shared vocabulary leaf (hyphenated filename -> import by file path, cached) -------------
# hca-vocab is a pure data LEAF that imports nothing from the skill, so sourcing the
# aggregation/analysis vocabulary from it cannot create a circular import. It is the single
# source of truth (superlatives + ratios + table terms live here so a whole-portfolio
# superlative/ratio question classifies as report-tier and is consensus-routed downstream).

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))


def _load(modname: str, filename: str):
    cached = sys.modules.get(modname)
    if cached is not None:
        return cached
    path = os.path.join(_THIS_DIR, filename)
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


def _vocab():
    return _load("hca_vocab", "hca-vocab.py")


# Signals that push a question toward the report/aggregation/analysis tier. Sourced from the
# shared vocabulary leaf (base aggregation words UNIONED with analysis triggers + superlatives
# + ratio + table terms). Whole-word matched for pure-word terms; substring-matched for terms
# carrying a space or a non-word char (e.g. "%", "over time").
_AGGREGATION_WORDS = _vocab().AGGREGATION_ANALYSIS_TERMS

_WORD_TERM_RE = re.compile(r"^[A-Za-z0-9]+$")

# Phrases that strongly indicate a single-record / single-value lookup. Used to
# *demote* an otherwise-ambiguous question back to trivial when no aggregation
# signal is present.
_TRIVIAL_SINGLE_PATTERNS = (
    r"\bloan\s+[A-Za-z]?-?\d+\b",          # "loan L-001", "loan 12"
    r"\bborrower\s+[A-Za-z0-9\-]+\b",       # "borrower B-204"
    r"\bid\s+[A-Za-z0-9\-]+\b",             # "id ABC-1"
)


def _has_aggregation_signal(question: str) -> bool:
    q = question.lower()
    for word in _AGGREGATION_WORDS:
        # Pure-word single tokens: whole-word match (avoids matching inside another word).
        # Anything carrying a space or a non-word char (e.g. "%", "over time", "at-risk"):
        # substring match — a word boundary either side would not fire (e.g. "\b%\b").
        if _WORD_TERM_RE.match(word):
            if re.search(r"\b" + re.escape(word) + r"\b", q):
                return True
        else:
            if word in q:
                return True
    return False


def _looks_like_single_record(question: str) -> bool:
    for pat in _TRIVIAL_SINGLE_PATTERNS:
        if re.search(pat, question, flags=re.IGNORECASE):
            return True
    return False


def classify(question: str) -> str:
    """Return the verification tier for a natural-language question.

    Rule precedence:
      1. Any aggregation/list/cross-entity signal -> report tier.
      2. Else, a question that names a single concrete record id/field and asks
         for one value -> trivial-lookup.
      3. Else (ambiguous, no aggregation signal) -> trivial-lookup (conservative:
         the trivial path still applies universal provenance + deterministic gates;
         it just does not mandate full adversarial consensus).
    """
    if not isinstance(question, str):
        raise TypeError("question must be a str")
    if _has_aggregation_signal(question):
        return TIER_REPORT
    # No aggregation signal. Single-record lookups and other simple value
    # questions route to the trivial tier.
    return TIER_TRIVIAL


# --- Evidence-bundle wiring (STUB) -------------------------------------------
# Minimal, dependency-free helper that creates the per-slice evidence bundle
# directory under .acos/evidence/[DATE]/[SLICE-ID]/. Full 7-part bundle authoring
# is handled by the executing slice; this is the wiring stub required by
# SLICE-HCA-01 (it only ensures the directory exists and returns its path).


def _repo_root() -> str:
    """Resolve the repo root from this file's location (.claude/scripts/ -> root).

    No git dependency (consistent with ACOS hook path-resolution policy).
    """
    here = os.path.dirname(os.path.abspath(__file__))          # .../.claude/scripts
    return os.path.abspath(os.path.join(here, os.pardir, os.pardir))


def hca_evidence_bundle_dir(slice_id: str, date: str = None, create: bool = True) -> str:
    """Return (and optionally create) .acos/evidence/[DATE]/[SLICE-ID]/.

    date defaults to today's UTC date (YYYY-MM-DD). Pure stdlib; no network.
    """
    if not slice_id or not isinstance(slice_id, str):
        raise ValueError("slice_id must be a non-empty str")
    if date is None:
        date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    path = os.path.join(_repo_root(), ".acos", "evidence", date, slice_id)
    if create:
        os.makedirs(path, exist_ok=True)
    return path


# --- Self-test ---------------------------------------------------------------
# DEV truth set. QA re-authors its own independent truth set and must NOT trust
# this one (per slice-01 QA gate). These are illustrative, synthetic questions —
# no real borrower PII.
_SELFTEST_CASES = [
    # trivial-lookup
    ("What is the maturity date of loan L-001?", TIER_TRIVIAL),
    ("Show the outstanding principal for loan 12.", TIER_TRIVIAL),
    ("What is the interest rate on borrower B-204's facility?", TIER_TRIVIAL),  # single value, single record, no aggregation signal
    ("Who is the relationship manager for borrower B-77?", TIER_TRIVIAL),
    ("What currency is loan L-9 denominated in?", TIER_TRIVIAL),
    ("Give me the status of loan L-003.", TIER_TRIVIAL),
    # report/aggregation/analysis
    ("What is the total outstanding principal across all loans?", TIER_REPORT),
    ("List every loan maturing in 2026.", TIER_REPORT),
    ("Sum the drawdowns by borrower.", TIER_REPORT),
    ("Show a breakdown of exposure per collateral type.", TIER_REPORT),
    ("How many loans are in breach of covenant?", TIER_REPORT),
    ("Compare funded amount between bridge and construction loans.", TIER_REPORT),
    ("What is the portfolio average interest rate?", TIER_REPORT),
    ("Rank the top 10 loans by commitment amount.", TIER_REPORT),
]


def _run_selftest() -> int:
    failures = []
    for question, expected in _SELFTEST_CASES:
        got = classify(question)
        status = "OK " if got == expected else "FAIL"
        if got != expected:
            failures.append((question, expected, got))
        print(f"[{status}] {got:<26} | {question}")
    print("-" * 60)
    if failures:
        print(f"SELFTEST FAILED: {len(failures)} mismatch(es)")
        for q, exp, got in failures:
            print(f"  expected={exp!r} got={got!r} :: {q}")
        return 1
    print(f"SELFTEST OK: {len(_SELFTEST_CASES)} cases passed")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="acos-hypercore-ask tier router (deterministic, no network)."
    )
    parser.add_argument("question", nargs="?", help="natural-language question to classify")
    parser.add_argument("--selftest", action="store_true", help="run the inline self-test")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of plain tier")
    args = parser.parse_args(argv)

    if args.selftest:
        return _run_selftest()

    if not args.question:
        parser.error("a question is required (or pass --selftest)")

    tier = classify(args.question)
    if args.json:
        print(json.dumps({"question": args.question, "tier": tier}))
    else:
        print(tier)
    return 0


if __name__ == "__main__":
    sys.exit(main())
