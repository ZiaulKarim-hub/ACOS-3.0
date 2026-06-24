#!/usr/bin/env python3
"""hca-deliver.py — the THIN end-to-end deterministic answer SPINE (SLICE-HCA-07, Demo 1).

Wires Waves A/B/C into ONE deterministic vertical for a natural-language portfolio
question, with NO consensus (that is slice-06, which WRAPS this spine):

    NL question
      -> [plan]        map question -> (intent, entity_type, query) via the live entity
                       registry + introspected schema digest. UNMAPPABLE => REFUSE (never guess).
      -> [fetch]       hca-adapter (read-only). LIVE when creds present (paginates to
                       COMPLETION via LiveBackend); else explicit NO_LIVE_DATA (never fabricate).
      -> [cache]       Tier-1 immutable raw write + Tier-2 normalized derivation (hca-cache).
      -> [provenance]  bind_and_verify EVERY delivered value to its Tier-1 source
                       (hca-provenance). Any undeliverable value => REFUSE.
      -> [gates]       deterministic_subset for trivial single-value lookups / run_all for
                       counts + aggregations (hca-gates). A `refuse` verdict => a structured
                       REFUSAL naming the failing gate — NEVER a number.
      -> [envelope]    { answer, values:[{value, provenance:{raw_response_id, json_field_path},
                         confidence}], gate_verdict, complete, refusals[] }

This is the spine slices 06 (consensus) and 08 (report/aggregation orchestration) will wrap.
It supports three trivial-tier intents today:
  - count       "how many loans/clients are there?"      -> totalFilteredRecords, gated by run_all
  - lookup      "what is the status of loan L-001?"       -> a single field, deterministic_subset
  - aggregate   "what is the total commitment?"           -> a SUM exercising reconciliation +
                                                             currency gates (run_all, aggregating)

NON-BYPASSABLE GUARANTEE: a value reaches the `answer` field ONLY after (a) its provenance
binding VERIFIED against Tier-1 AND (b) the gate suite returned `outcome == pass`. Either
failing forces a REFUSED / NO_LIVE_DATA envelope with no number. There is no code path that
emits `answer` while skipping the binder or the gates.

GROUND RULES (memory/decisions/2026-06-18-hca-build-ground-rules.md):
  - Python 3 stdlib ONLY. No third-party deps.
  - Subscription-only Claude: the deterministic path makes NO model call; never ANTHROPIC_API_KEY.
  - Read-only: composes slice 01-05 modules; never writes Tier-1 outside the cache facade.
  - Live access is read-only (GraphQL `query` only, enforced three ways in hca-live.py).
  - No real PII is printed by the CLI/envelope summary — counts, aggregates, field NAMES only.

Slices 01-05 scripts are COMPOSE-ONLY here (imported, never edited).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Terminal states
# ---------------------------------------------------------------------------

STATE_DELIVERED = "DELIVERED"
STATE_REFUSED = "REFUSED"
STATE_NO_LIVE_DATA = "NO_LIVE_DATA"
STATE_ESCALATED = "ESCALATED"          # report tier: a figure could not reach consensus quorum

# Refusal reason codes specific to the spine (provenance/gate codes are surfaced verbatim).
REASON_UNMAPPABLE = "UNMAPPABLE_QUESTION"     # plan could not map the question to an entity/query
REASON_GATE_FAIL = "GATE_FAIL"               # the deterministic gate suite returned `refuse`
REASON_PROVENANCE = "PROVENANCE_REFUSED"     # a value could not be bound+verified to Tier-1
REASON_FETCH_EMPTY = "FETCH_EMPTY"           # fetch returned no record/items to answer from
REASON_NO_CONSENSUS = "NO_CONSENSUS"         # report tier: < quorum agreement after re-dispatch
REASON_FIGURE_REFUSED = "FIGURE_REFUSED"     # report tier: a constituent figure refused (see inner)


# ---------------------------------------------------------------------------
# Sibling module loading (hyphenated filenames -> import by file path, cached)
# ---------------------------------------------------------------------------

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
    # hca-vocab is a pure data LEAF (imports nothing from the skill) -> sourcing the payoff /
    # utilization / analysis trigger vocabularies from it cannot create a circular import.
    return _load("hca_vocab", "hca-vocab.py")


def _route():
    return _load("hca_route", "hca-route.py")


def _adapter():
    return _load("hca_adapter", "hca-adapter.py")


def _cache():
    return _load("hca_cache", "hca-cache.py")


def _provenance():
    return _load("hca_provenance", "hca-provenance.py")


def _gates():
    return _load("hca_gates", "hca-gates.py")


def _consensus():
    return _load("hca_consensus", "hca-consensus.py")


def _resolve():
    return _load("hca_resolve", "hca-resolve.py")


def _figures():
    return _load("hca_figures", "hca-figures.py")


def _ontology():
    return _load("hca_ontology", "hca-ontology.py")


def _analyze():
    return _load("hca_analyze", "hca-analyze.py")


# ---------------------------------------------------------------------------
# Plan — map an NL question to (intent, entity_type, query_kind). No guessing.
# ---------------------------------------------------------------------------

# Adapter entity_type -> the plural noun(s) a question might use. The entity registry in
# hca-live.py (ENTITY_REGISTRY) is the authority for what is fetchable; we map natural-language
# nouns onto those registry keys. An entity not in the registry is UNMAPPABLE (cannot fetch).
_ENTITY_NOUNS = {
    "loan": ("loans", "loan"),
    "client": ("clients", "client", "borrowers", "borrower"),
    "equity": ("equities", "equity"),
    "fundingEntity": ("funding entities", "funding entity", "fundingentities"),
    "loanFunding": ("loan fundings", "loan funding", "fundings"),
}

# Monetary aggregate field per entity (for the "total X" intent). Only fields known to exist
# on the live list selection / fixtures and that are summable (single currency) are eligible.
_AGGREGATE_FIELDS = {
    ("loan", "commitment"): {"field": "commitment", "currency_field": "currency",
                             "synonyms": ("commitment", "committed")},
}

# Single-field lookup synonyms -> the GraphQL field name to read for a named record.
_LOOKUP_FIELDS = {
    "loan": {
        "status": "status",
        "name": "name",
        "commitment": "commitment",
        "ref": "refId",
        "reference": "refId",
        "start": "startDate",
        "start date": "startDate",
        "end": "endDate",
        "end date": "endDate",
        "maturity": "endDate",
    },
}

_COUNT_TRIGGERS = ("how many", "number of", "count of", "count the", "how much in count")
_TOTAL_TRIGGERS = ("total", "sum", "sum of", "aggregate")

# ---------------------------------------------------------------------------
# PORTFOLIO-ANALYSIS intent triggers (SLICE-HCA-15) — rankings / roll-ups / filters /
# concentration / covenant scan. These route a WHOLE-PORTFOLIO question to hca-analyze.py
# (ONE bulk Tier-1 fetch, in-memory analysis, provenance-bound). Checked AFTER payoff but the
# analysis planner is conservative: it only fires on an explicit analysis phrasing so the
# existing trivial count/lookup/aggregate fast paths keep their behavior.
# ---------------------------------------------------------------------------

# Logical analysis figure -> the user phrasings that name it (for rank/total/filter analyses).
_ANALYSIS_FIGURE_SYNONYMS = {
    "outstanding": ("outstanding", "outstanding balance", "balance", "exposure",
                    "current balance"),
    "overdue": ("overdue", "arrears", "past due"),
    "commitment": ("commitment", "loan amount", "loan size", "committed", "face amount"),
    "amount_due": ("amount due", "due", "total due"),
    "total_disbursed": ("disbursed", "drawn", "funded", "advanced"),
    "accrued_interest": ("accrued interest", "interest accrued"),
    "principal_outstanding": ("principal outstanding", "outstanding principal", "principal"),
    "penalties_outstanding": ("penalties", "default interest", "penalty interest"),
}

# Ranking phrasings (sourced from the shared vocabulary leaf — single source of truth).
_RANK_TRIGGERS = _vocab().RANK_TRIGGERS
# Maturity-proximity phrasings.
_MATURITY_TRIGGERS = ("closest to maturity", "nearest maturity", "soonest to mature",
                      "closest maturity", "maturing soonest", "next to mature")
# Utilization ranking (shared vocabulary leaf).
_UTILIZATION_TRIGGERS = _vocab().UTILIZATION_TERMS
# Concentration phrasings (shared vocabulary leaf).
_CONCENTRATION_TRIGGERS = _vocab().CONCENTRATION_TRIGGERS
# Covenant-scan phrasings.
_COVENANT_TRIGGERS = ("covenant", "breach", "in breach", "covenant breach",
                      "covenant violation", "ltv breach")
# At-risk interpretive judgment (shared vocabulary leaf).
_AT_RISK_TRIGGERS = _vocab().AT_RISK_TRIGGERS
# Weighted-average / portfolio roll-up phrasings.
_WAVG_RATE_TRIGGERS = ("weighted average rate", "weighted-average rate", "weighted average "
                       "interest", "blended rate", "average rate", "average interest rate")
_WAM_TRIGGERS = ("weighted average maturity", "weighted-average maturity", "wam",
                 "average maturity")
# Filters.
_OVERDUE_FILTER_TRIGGERS = ("overdue loans", "which loans are overdue", "loans that are overdue",
                            "loans in arrears", "loans past due", "are overdue")
_ACTIVE_FILTER_TRIGGERS = ("active loans", "which loans are active", "loans that are active")
_MATURING_WITHIN_RE = re.compile(
    r"matur\w*\s+(?:with)?in\s+(?:the\s+next\s+)?(\d+)\s*days?", re.IGNORECASE)
# count by status
_COUNT_BY_STATUS_TRIGGERS = ("count by status", "loans by status", "how many loans by status",
                             "breakdown by status", "count of loans by status")
# top-N concentration size, e.g. "top 5 loans" -> N, "top 10" -> N.
_TOP_N_RE = re.compile(r"\btop\s+(\d+)\b", re.IGNORECASE)
# over-$X outstanding, e.g. "loans over $5,000,000 outstanding" / "over 5000000 outstanding".
_OVER_THRESHOLD_RE = re.compile(
    r"\b(?:over|above|greater than|more than|exceeding)\s+\$?\s*([\d,]+(?:\.\d+)?)",
    re.IGNORECASE)

# Payoff / early-redemption intent triggers. A question containing any of these routes to the
# payoff figure (resolve loan -> getLoanRepaymentDistribution). This fixes the earlier
# `no_lookup_target` refusal for payoff questions. Sourced from the shared vocabulary leaf
# (UNION of the prior deliver triggers + the figures PayoffFigure.SYNONYMS — single source).
_PAYOFF_TRIGGERS = _vocab().PAYOFF_TERMS

# A concrete record id like "L-001", "L-GQL-1", "12" following the entity noun.
_RECORD_ID_RE = re.compile(r"\b([A-Za-z]+-[A-Za-z0-9\-]+|\d+)\b")

# "as of 2026-06-30" / "as-of 2026/06/30" / "on 2026-06-30" date extraction.
_ASOF_DATE_RE = re.compile(
    r"\b(?:as[\s-]?of|on|for|by|at)\s+(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", re.IGNORECASE)
_BARE_DATE_RE = re.compile(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b")


def _extract_asof_date(question: str) -> Optional[str]:
    """Pull an explicit as-of date (YYYY-MM-DD) from the question, or None for 'today'.

    Prefers an 'as of <date>' phrasing; falls back to any bare ISO-ish date in the text.
    Normalizes to zero-padded YYYY-MM-DD. Returns None when no date is present.
    """
    m = _ASOF_DATE_RE.search(question) or _BARE_DATE_RE.search(question)
    if not m:
        return None
    y, mo, d = m.group(1), int(m.group(2)), int(m.group(3))
    if not (1 <= mo <= 12 and 1 <= d <= 31):
        return None
    return f"{y}-{mo:02d}-{d:02d}"


def _extract_loan_name_for_payoff(question: str) -> Optional[str]:
    """Extract the loan-name query from a payoff question.

    Strips the payoff trigger phrases, common filler ("what is the ... for/of <NAME>"), and any
    trailing 'as of <date>' clause, leaving the loan name token(s) to hand to the resolver.
    Returns None when nothing name-like remains (caller refuses: needs a loan).
    """
    q = question.strip()
    # drop a trailing "as of <date>" / "on <date>" clause
    q = _ASOF_DATE_RE.sub(" ", q)
    q = _BARE_DATE_RE.sub(" ", q)
    low = q.lower()
    # remove payoff trigger phrases
    for t in sorted(_PAYOFF_TRIGGERS, key=lambda s: -len(s)):
        low = low.replace(t, " ")
    # rebuild q preserving original case by mapping: simplest is to re-extract from original
    # after removing the same spans, but a case-insensitive token strip is sufficient here.
    work = q
    for t in sorted(_PAYOFF_TRIGGERS, key=lambda s: -len(s)):
        work = re.sub(re.escape(t), " ", work, flags=re.IGNORECASE)
    # strip leading filler words/punctuation
    work = re.sub(r"(?i)\b(what|whats|what's|how|much|is|are|the|of|for|on|loan|amount|to|me|tell|"
                  r"give|please|current|total|early|redemption|by|at|do|we|have|show|"
                  r"senior|junior|mezzanine|mezz|tranche)\b", " ", work)
    work = re.sub(r"[?.,:;!]", " ", work)
    work = re.sub(r"\s+", " ", work).strip()
    return work or None


# Figure-concept phrasings that should NOT be treated as a loan name when stripping. These are
# the words the ontology may use inside a concept term — removing them leaves the loan name.
_FIGURE_FILLER_RE = re.compile(
    r"(?i)\b(what|whats|what's|is|are|the|of|for|on|loan|loans|amount|to|me|tell|give|please|"
    r"current|total|how|much|s|in|across|portfolio|all|by|at|do|we|have|show|give)\b")


def _strip_concept_terms(question: str, concept) -> str:
    """Remove a matched concept's terms (canonical name + synonyms) + filler from the question,
    leaving the loan-name token(s). Returns '' when nothing name-like remains (portfolio-level)."""
    work = question
    work = _ASOF_DATE_RE.sub(" ", work)
    work = _BARE_DATE_RE.sub(" ", work)
    terms = sorted(concept.terms(), key=lambda s: -len(s))
    for t in terms:
        work = re.sub(re.escape(t), " ", work, flags=re.IGNORECASE)
    work = _FIGURE_FILLER_RE.sub(" ", work)
    work = re.sub(r"[?.,:;!%]", " ", work)
    work = re.sub(r"\s+", " ", work).strip()
    return work


def _detect_figure_concept(question: str):
    """Resolve a question to an ontology concept (via synonyms + fuzzy match). Returns the
    Concept on a high-confidence resolve, the ambiguous resolve dict on a tie, or None on miss.

    The whole question is offered to the ontology resolver; its scoring already favors a concept
    whose synonym phrase appears in the question (token-subset bonus), so "what's the outstanding
    balance on Beehive" resolves to outstanding_balance even with the loan name attached.
    """
    ont = _ontology().default_ontology()
    # Try the question as-is, then a date-stripped variant (so a trailing 'as of <date>' or a
    # loan name doesn't dilute the score). The resolver returns the best concept either way.
    candidates = []
    for q in (question, _ASOF_DATE_RE.sub(" ", _BARE_DATE_RE.sub(" ", question))):
        res = ont.resolve(q)
        candidates.append(res)
        # Also probe each concept term's presence directly: if a concept's synonym phrase is a
        # clean substring of the question, treat it as a strong signal.
    # Prefer a resolved (high-confidence) result; else surface the best ambiguous one.
    for res in candidates:
        if res.get("resolved"):
            return res
    # substring fallback: a concept synonym appearing verbatim in the question is a strong match.
    ql = " " + re.sub(r"[^a-z0-9 ]", " ", question.lower()) + " "
    ql = re.sub(r"\s+", " ", ql)
    best = None
    for c in ont.concepts():
        for term in c.terms():
            nt = re.sub(r"[^a-z0-9 ]", " ", term.lower()).strip()
            nt = re.sub(r"\s+", " ", nt)
            if nt and (" " + nt + " ") in ql:
                # longest matching term wins (most specific)
                if best is None or len(nt) > best[1]:
                    best = (c, len(nt))
    if best is not None:
        return {"resolved": True, "concept": best[0], "ambiguous": False,
                "candidates": [{"name": best[0].name, "score": 1.0, "kind": best[0].kind}],
                "reason": "concept synonym appears verbatim in the question"}
    # return the best ambiguous resolve (if any) so the caller can disambiguate
    for res in candidates:
        if res.get("candidates"):
            return res
    return None


class PlanError(ValueError):
    """The question could not be mapped to a fetchable entity/query — UNMAPPABLE."""

    def __init__(self, message: str, *, detail: Optional[dict] = None):
        super().__init__(message)
        self.detail = detail or {}


def _detect_entity(q: str) -> Optional[str]:
    """Return the adapter entity_type named in the question, or None. Longest-noun-first so
    'funding entities' wins over 'funding'."""
    pairs = []
    for et, nouns in _ENTITY_NOUNS.items():
        for n in nouns:
            pairs.append((n, et))
    for noun, et in sorted(pairs, key=lambda p: -len(p[0])):
        if re.search(r"\b" + re.escape(noun) + r"\b", q):
            return et
    return None


# Native currency-unit figures that aggregate sensibly across the portfolio (a SUM of a
# per-loan money figure). Derived ratios + requires_external metrics do NOT portfolio-sum.
_PORTFOLIO_SUMMABLE_FIGURES = frozenset({
    "outstanding_balance", "principal_outstanding", "accrued_interest", "default_interest",
    "amount_due_today", "overdue_amount", "commitment", "total_disbursed",
})

# Phrasings that signal a PORTFOLIO-level (no single loan) figure question.
_PORTFOLIO_TRIGGERS = ("across the portfolio", "across portfolio", "across all loans",
                       "across all", "portfolio", "total", "all loans", "every loan",
                       "whole portfolio", "entire portfolio", "sum of", "aggregate")


def _plan_figure(question: str, q_lower: str, tier: str):
    """Plan a FIGURE question via the ontology. Returns a plan dict or None (not a figure).

    - Resolves the question to a concept (ontology synonyms + fuzzy + verbatim-substring).
    - If a loan name remains after stripping the concept terms -> a per-loan figure plan.
    - Else, if the figure is portfolio-summable AND a portfolio trigger is present ->
      a portfolio-aggregate figure plan (sum across loans).
    - An AMBIGUOUS concept -> a plan that carries the ambiguity so the spine can disambiguate.
    Returns None when the question names no concept at all (let the caller's other paths run).
    """
    res = _detect_figure_concept(question)
    if res is None:
        return None
    concept = res.get("concept")
    if concept is None:
        # ambiguous concept resolve -> surface candidates for disambiguation (REFUSE, no guess).
        cands = res.get("candidates") or []
        if not cands:
            return None
        return {"intent": "figure", "figure_ambiguous": True, "tier": tier,
                "concept_candidates": cands, "value_path_kind": "figure",
                "reason": res.get("reason")}

    figure_name = concept.name
    # Payoff is handled by its own dedicated path; never re-route it here.
    if figure_name == "payoff_as_of":
        return None

    loan_name = _strip_concept_terms(question, concept)
    portfolio_signal = any(t in q_lower for t in _PORTFOLIO_TRIGGERS)

    if loan_name:
        return {
            "intent": "figure", "figure_name": figure_name, "entity_type": "loan",
            "tier": tier, "loan_name": loan_name,
            "as_of_date": _extract_asof_date(question),
            "concept_kind": concept.kind, "value_path_kind": "figure",
        }

    # No loan named -> portfolio level. Only currency-summable native figures aggregate.
    if figure_name in _PORTFOLIO_SUMMABLE_FIGURES and portfolio_signal:
        return {
            "intent": "figure_portfolio", "figure_name": figure_name, "entity_type": "loan",
            "tier": tier, "concept_kind": concept.kind, "value_path_kind": "figure_portfolio",
        }

    # A requires_external / derived concept with no loan named -> still answerable as a per-loan
    # figure refusal needs a loan; surface a clear refusal that a loan (or portfolio scope for a
    # summable figure) is required.
    return {
        "intent": "figure", "figure_name": figure_name, "entity_type": "loan", "tier": tier,
        "loan_name": None, "concept_kind": concept.kind, "value_path_kind": "figure",
        "needs_loan": True,
    }


def _analysis_figure(q_lower: str) -> Optional[str]:
    """Return the analysis figure named in the question (longest synonym wins), or None."""
    best = None
    best_len = 0
    for fig, syns in _ANALYSIS_FIGURE_SYNONYMS.items():
        for s in syns:
            if s in q_lower and len(s) > best_len:
                best, best_len = fig, len(s)
    return best


def _plan_analysis(question: str, q_lower: str, tier: str) -> Optional[dict]:
    """Plan a PORTFOLIO-ANALYSIS question (SLICE-HCA-15) or return None (not an analysis).

    Conservative: fires ONLY on an explicit analysis phrasing (top/largest/rank/concentration/
    breach/maturing/overdue-loans/weighted-average/...). A trivial 'how many loans' or a single
    'total commitment across all loans' keeps its existing fast path (this planner is consulted
    AFTER those). Routes to hca-analyze via {intent:"analysis", analysis:<kind>, ...}.
    """
    has_loans = ("loan" in q_lower or "portfolio" in q_lower or "book" in q_lower)
    # TRUST FIX (consensus bypass): a bare-superlative figure question ("highest interest rate",
    # "smallest commitment") with NO explicit loan/portfolio/book noun is STILL a whole-portfolio
    # extremum (a min/max over many records) — it must route to analysis/report-tier (and thus
    # the consensus path), NEVER fall through to a trivial single figure. We treat the presence of
    # a superlative term + a recognizable numeric figure as an implicit portfolio scope.
    _voc = _vocab()
    # A whole-portfolio extremum/filter/statistical question must route here (analysis/report)
    # rather than fall through to _plan_figure (which would mis-resolve "fewest"/"worst" as a
    # loan name). Detect it by the allowlisted superlatives OR by SHAPE (an "-est" superlative,
    # a comparator+threshold filter, a statistical term) so an unenumerated synonym still lands.
    has_superlative = any(
        re.search(r"\b" + re.escape(s) + r"\b", q_lower) for s in _voc.SUPERLATIVE_TERMS
    ) or _voc.has_structural_aggregation_shape(q_lower)

    # An analysis is by definition a WHOLE-PORTFOLIO, multi-record operation, so every analysis
    # plan must carry the consensus-routed report tier — NEVER the trivial tier that classify()
    # may have returned for filter phrasings like "active loans" / "overdue loans" (round-2
    # tier/intent-divergence fix: an analysis intent must not ride the trivial single-source path).
    tier = TIER_REPORT

    # covenant-breach scan (highest priority — distinctive phrasing).
    if any(t in q_lower for t in _COVENANT_TRIGGERS):
        return {"intent": "analysis", "analysis": "covenant_breach_scan", "tier": tier,
                "value_path_kind": "analysis"}
    # at-risk interpretive judgment.
    if any(t in q_lower for t in _AT_RISK_TRIGGERS):
        return {"intent": "analysis", "analysis": "most_at_risk", "tier": tier,
                "value_path_kind": "analysis"}
    # count by status.
    if any(t in q_lower for t in _COUNT_BY_STATUS_TRIGGERS):
        return {"intent": "analysis", "analysis": "count_by_status", "tier": tier,
                "value_path_kind": "analysis"}
    # weighted-average maturity (check before generic rate so 'average maturity' wins).
    if any(t in q_lower for t in _WAM_TRIGGERS):
        return {"intent": "analysis", "analysis": "weighted_average_maturity", "tier": tier,
                "value_path_kind": "analysis"}
    # weighted-average rate.
    if any(t in q_lower for t in _WAVG_RATE_TRIGGERS):
        return {"intent": "analysis", "analysis": "weighted_average_rate", "tier": tier,
                "value_path_kind": "analysis"}
    # concentration (by status / top-N).
    if any(t in q_lower for t in _CONCENTRATION_TRIGGERS):
        m = _TOP_N_RE.search(q_lower)
        if m or "top" in q_lower:
            n = int(m.group(1)) if m else 5
            return {"intent": "analysis", "analysis": "top_n_concentration", "n": n,
                    "tier": tier, "value_path_kind": "analysis"}
        if "client" in q_lower:
            return {"intent": "analysis", "analysis": "concentration_by_client", "tier": tier,
                    "value_path_kind": "analysis"}
        return {"intent": "analysis", "analysis": "concentration_by_status", "tier": tier,
                "value_path_kind": "analysis"}
    # maturing within N days.
    mw = _MATURING_WITHIN_RE.search(question)
    if mw:
        return {"intent": "analysis", "analysis": "filter_maturing_within",
                "days": int(mw.group(1)), "tier": tier, "value_path_kind": "analysis"}
    # closest to maturity ranking.
    if any(t in q_lower for t in _MATURITY_TRIGGERS):
        m = _TOP_N_RE.search(q_lower)
        return {"intent": "analysis", "analysis": "rank_by_maturity",
                "n": int(m.group(1)) if m else 10, "tier": tier, "value_path_kind": "analysis"}
    # highest utilization ranking.
    if any(t in q_lower for t in _UTILIZATION_TRIGGERS) and (
            any(t in q_lower for t in _RANK_TRIGGERS) or has_loans):
        m = _TOP_N_RE.search(q_lower)
        return {"intent": "analysis", "analysis": "rank_by_utilization",
                "n": int(m.group(1)) if m else 10, "tier": tier, "value_path_kind": "analysis"}
    # overdue-loans filter (a LIST of overdue loans, not the overdue total).
    if any(t in q_lower for t in _OVERDUE_FILTER_TRIGGERS):
        return {"intent": "analysis", "analysis": "filter_overdue", "tier": tier,
                "value_path_kind": "analysis"}
    # active-loans filter.
    if any(t in q_lower for t in _ACTIVE_FILTER_TRIGGERS):
        return {"intent": "analysis", "analysis": "filter_active", "tier": tier,
                "value_path_kind": "analysis"}
    # over-$X outstanding filter.
    over = _OVER_THRESHOLD_RE.search(question)
    if over and has_loans and ("outstanding" in q_lower or "balance" in q_lower):
        threshold = float(over.group(1).replace(",", ""))
        return {"intent": "analysis", "analysis": "filter_over_outstanding",
                "threshold": threshold, "tier": tier, "value_path_kind": "analysis"}
    # ranking by a numeric figure (top/largest/highest/rank ... loans by <figure>). A
    # superlative (highest/smallest/largest/...) implies a whole-portfolio extremum, so it
    # routes here EVEN WITHOUT an explicit loan/portfolio/book noun (the consensus-bypass fix:
    # "what is the highest interest rate?" / "smallest commitment" must NOT become a trivial
    # single figure). Ranking by a named numeric figure when recognized, else outstanding.
    # A superlative ALONE (worst/best/least/maximum/minimum/... — not just the rank words) implies
    # a whole-portfolio extremum and MUST route here, so "worst DSCR" / "best loan" become an
    # analysis (consensus-tier) and never fall through to _plan_figure (which would mis-resolve
    # "worst" as a loan name). A bare rank word still also needs a portfolio noun.
    if has_superlative or (any(t in q_lower for t in _RANK_TRIGGERS) and has_loans):
        figure = _analysis_figure(q_lower) or "outstanding"
        m = _TOP_N_RE.search(q_lower)
        ascending = (any(w in q_lower for w in ("smallest", "lowest", "least", "minimum"))
                     or "closest to maturity" in q_lower)
        return {"intent": "analysis", "analysis": "rank", "figure": figure,
                "n": int(m.group(1)) if m else 10, "ascending": ascending, "tier": tier,
                "value_path_kind": "analysis"}
    # NOTE: a portfolio TOTAL of a summable figure ("total outstanding across the portfolio") is
    # intentionally NOT intercepted here — the established figure_portfolio path (_plan_figure)
    # already sums it with full provenance + reconciliation + mixed-currency refusal. The
    # analyzer's own total() (ONE bulk fetch) is still callable directly + via the CLI
    # (--total outstanding); the NL planner defers to the figure_portfolio path so the
    # existing SLICE-HCA-13 routing/behavior is preserved.
    return None


def plan_question(question: str) -> dict:
    """Deterministically map a question to a fetch+verify plan. Never fabricates an intent.

    Returns a plan dict:
        {intent: count|lookup|aggregate|analysis, entity_type, tier, record_id?, field?,
         aggregate_field?, currency_field?, analysis?, value_path_kind}
    Raises PlanError (=> REFUSE, never guess) when the question names no fetchable entity or
    no supported intent.
    """
    if not isinstance(question, str) or not question.strip():
        raise PlanError("empty question")
    q = question.strip().lower()

    # --- payoff / early-redemption intent (checked FIRST) ------------------
    # A payoff question names a LOAN BY NAME ("payoff for Beehive Waldorff"), not by a
    # registry noun, so it is detected before the generic entity requirement. It routes to
    # the payoff figure: resolve the loan name -> getLoanRepaymentDistribution.
    if any(t in q for t in _PAYOFF_TRIGGERS):
        loan_name = _extract_loan_name_for_payoff(question)
        if not loan_name:
            raise PlanError(
                "payoff question names no loan to resolve (need a loan name, e.g. "
                "'what is the payoff for Beehive Waldorff')",
                detail={"reason": "no_payoff_loan"},
            )
        return {
            "intent": "payoff", "entity_type": "loan", "tier": _route().classify(question),
            "loan_name": loan_name, "as_of_date": _extract_asof_date(question),
            "value_path_kind": "early_redemption_total",
        }

    tier = _route().classify(question)

    entity_type = _detect_entity(q)

    # --- count intent (requires an entity noun) ---------------------------
    if entity_type is not None and any(t in q for t in _COUNT_TRIGGERS):
        return {
            "intent": "count", "entity_type": entity_type, "tier": tier,
            "value_path_kind": "reported_total",
        }

    # --- aggregate intent (total/sum of a known summable field across an entity list) ----
    # Only the explicitly-registered summable fields (commitment) take this fast path; it must
    # win for "total commitment across all loans" (an entity-list SUM with currency gates).
    if entity_type is not None and any(
            re.search(r"\b" + re.escape(t) + r"\b", q) for t in _TOTAL_TRIGGERS):
        agg = None
        for (et, _fname), spec in _AGGREGATE_FIELDS.items():
            if et != entity_type:
                continue
            if any(s in q for s in spec["synonyms"]):
                agg = spec
                break
        if agg is not None:
            return {
                "intent": "aggregate", "entity_type": entity_type, "tier": tier,
                "aggregate_field": agg["field"], "currency_field": agg["currency_field"],
                "value_path_kind": "aggregate_sum",
            }
        # not a registered summable field -> may still be a portfolio analysis / FIGURE below.

    # --- PORTFOLIO-ANALYSIS intent (SLICE-HCA-15) -------------------------
    # Rankings / roll-ups / filters / concentration / covenant scan over the WHOLE portfolio,
    # routed to hca-analyze (ONE bulk Tier-1 fetch, in-memory, provenance-bound). Checked AFTER
    # the trivial count + the registered commitment-aggregate fast paths so those keep their
    # behavior, but BEFORE the per-loan figure planner (which would try to resolve a loan name).
    analysis_plan = _plan_analysis(question, q, tier)
    if analysis_plan is not None:
        return analysis_plan

    # --- FIGURE intent (ontology-driven; SLICE-HCA-13) --------------------
    # A question naming a private-credit concept (outstanding balance, utilization, LTV, ...)
    # routes to the figures registry. Loan named -> per-loan figure; no loan -> portfolio
    # aggregation where the figure is summable. An UNMAPPED concept REFUSES (named), not guesses.
    fig_plan = _plan_figure(question, q, tier)
    if fig_plan is not None:
        return fig_plan

    if entity_type is None:
        raise PlanError(
            "question names no entity the adapter can fetch and no known concept "
            f"(known entities: {sorted(_ENTITY_NOUNS)})",
            detail={"reason": "no_entity"},
        )

    # an aggregate trigger was present but matched no registered field AND no figure concept
    if any(re.search(r"\b" + re.escape(t) + r"\b", q) for t in _TOTAL_TRIGGERS):
        raise PlanError(
            f"aggregate requested for {entity_type!r} but no supported summable field or "
            f"concept matched the question",
            detail={"reason": "no_aggregate_field", "entity_type": entity_type},
        )

    # --- lookup intent (a single field of a named record) -----------------
    field_map = _LOOKUP_FIELDS.get(entity_type, {})
    field = None
    for phrase, gql_field in sorted(field_map.items(), key=lambda kv: -len(kv[0])):
        if re.search(r"\b" + re.escape(phrase) + r"\b", q):
            field = gql_field
            break
    record_id = None
    # take the first id-shaped token that is not the entity noun itself
    for m in _RECORD_ID_RE.finditer(question):  # original case for ids like L-GQL-1
        tok = m.group(1)
        if tok.lower() in (n for nouns in _ENTITY_NOUNS.values() for n in nouns):
            continue
        record_id = tok
        break
    if field is None or record_id is None:
        raise PlanError(
            "question is not a supported single-value lookup "
            "(need both a recognizable field and a record id)",
            detail={"reason": "no_lookup_target", "entity_type": entity_type,
                    "field": field, "record_id": record_id},
        )
    return {
        "intent": "lookup", "entity_type": entity_type, "tier": tier,
        "record_id": record_id, "field": field, "value_path_kind": "single_field",
    }


# ---------------------------------------------------------------------------
# Envelope builders
# ---------------------------------------------------------------------------

def _envelope(state: str, *, answer, values: list, gate_verdict, complete: bool,
              refusals: list, plan: Optional[dict] = None, meta: Optional[dict] = None) -> dict:
    return {
        "state": state,
        "answer": answer,
        "values": values,
        "gate_verdict": gate_verdict,
        "complete": complete,
        "refusals": refusals,
        "plan": plan,
        "meta": meta or {},
    }


def _refused_envelope(reason_code: str, reason: str, *, gate_verdict=None,
                      plan: Optional[dict] = None, extra: Optional[dict] = None) -> dict:
    refusal = {"reason_code": reason_code, "reason": reason}
    if extra:
        refusal.update(extra)
    return _envelope(STATE_REFUSED, answer=None, values=[], gate_verdict=gate_verdict,
                     complete=False, refusals=[refusal], plan=plan)


def _no_live_data_envelope(plan: Optional[dict], reason: str, *,
                           inner: Optional[dict] = None) -> dict:
    return _envelope(
        STATE_NO_LIVE_DATA, answer=None, values=[], gate_verdict=None, complete=False,
        refusals=[{"reason_code": STATE_NO_LIVE_DATA, "reason": reason,
                   "envelope": inner}],
        plan=plan,
        meta={"message": "no live data — Hypercore access not yet provisioned"},
    )


# ---------------------------------------------------------------------------
# The spine
# ---------------------------------------------------------------------------

class DeliverySpine:
    """The thin deterministic answer path. Construct once; call `ask(question)`.

    Backend selection follows hca-adapter.select_backend (explicit arg > HCA_ADAPTER_BACKEND
    env > config.yaml > fixture). Tests inject an explicit `adapter` (FixtureBackend) so they
    never touch the network; the live CLI lets config.yaml select LiveBackend under Doppler.
    """

    def __init__(self, *, adapter=None, cache=None, gate_suite=None,
                 engine=None, page_limit: Optional[int] = None, now=None,
                 resolver=None, figures=None, analyzer=None):
        self._ad = _adapter()
        self._cachelib = _cache()
        self._provlib = _provenance()
        self._gatelib = _gates()
        self.adapter = adapter or self._ad.HypercoreAdapter()
        self.cache = cache or self._cachelib.TwoTierCache()
        self.engine = engine or self._provlib.ProvenanceEngine(cache=self.cache)
        self.gate_suite = gate_suite or self._gatelib.GateSuite(now=now)
        self._page_limit = page_limit
        self._now = now
        # Payoff vertical: a fuzzy loan-name resolver + a figures registry. Injected by tests
        # (fixtures, no network); built lazily for the live CLI path.
        self.resolver = resolver
        self.figures = figures
        # Portfolio-analysis layer (SLICE-HCA-15): a PortfolioAnalyzer over the ONE bulk Tier-1
        # fetch. Injected by tests (fake bulk client + temp cache); built lazily for the CLI.
        self.analyzer = analyzer

    # --- public entry ------------------------------------------------------
    def ask(self, question: str) -> dict:
        """Run the full spine for one NL question and return an answer envelope (or a
        terminal REFUSED / NO_LIVE_DATA envelope). Never raises on a normal data/plan/fetch
        problem — every failure is a structured envelope."""
        # 1) PLAN ----------------------------------------------------------
        try:
            plan = plan_question(question)
        except PlanError as e:
            return _refused_envelope(REASON_UNMAPPABLE, str(e), plan=None,
                                     extra={"detail": e.detail})

        # 1b) PAYOFF intent has its OWN vertical (resolve loan -> figure), not the generic
        #     fetch/cache path. Branch before the generic fetch.
        if plan["intent"] == "payoff":
            return self._answer_payoff(plan)

        # 1c) FIGURE intents (ontology-routed: per-loan figure / portfolio aggregation).
        if plan["intent"] == "figure":
            return self._answer_figure(plan)
        if plan["intent"] == "figure_portfolio":
            return self._answer_figure_portfolio(plan)

        # 1d) ANALYSIS intent (SLICE-HCA-15): a whole-portfolio ranking / roll-up / filter /
        #     concentration / covenant scan, served by hca-analyze (ONE bulk Tier-1 fetch).
        if plan["intent"] == "analysis":
            return self._answer_analysis(plan)

        # 2) FETCH ---------------------------------------------------------
        try:
            raw = self._fetch(plan)
        except self._ad.NoLiveDataError as e:
            return _no_live_data_envelope(plan, str(e), inner=getattr(e, "envelope", None))
        except FileNotFoundError as e:
            # A fixture/record genuinely absent is a refusal, never a fabricated answer.
            return _refused_envelope(REASON_FETCH_EMPTY, f"fetch found no data: {e}", plan=plan)

        # 3) CACHE (Tier-1 immutable) -------------------------------------
        rid = self.cache.put_raw(raw)
        raw = self.cache.get_raw(rid)  # canonical stored copy

        # 4/5/6) PROVENANCE + GATES + ENVELOPE per intent -----------------
        if plan["intent"] == "count":
            return self._answer_count(plan, raw, rid)
        if plan["intent"] == "lookup":
            return self._answer_lookup(plan, raw, rid)
        if plan["intent"] == "aggregate":
            return self._answer_aggregate(plan, raw, rid)
        # Unreachable: plan_question only emits the three intents above.
        return _refused_envelope(REASON_UNMAPPABLE,
                                 f"unsupported intent {plan['intent']!r}", plan=plan)

    # --- fetch -------------------------------------------------------------
    def _fetch(self, plan: dict) -> dict:
        et = plan["entity_type"]
        # Degradation contract: when the SELECTED backend is the live GraphQL backend but it
        # is not live (creds absent), we DEMAND live and let NoLiveDataError propagate -> the
        # explicit NO_LIVE_DATA envelope (never a fabricated number). The FixtureBackend
        # (is_live()==False by design) legitimately serves clearly-labeled fixture data, so we
        # do NOT force require_live there.
        require_live = self._is_live_backend_but_not_live()
        # singular registry key for the adapter (matches hca-live.ENTITY_REGISTRY)
        if plan["intent"] == "lookup":
            return self.adapter.get_entity(et, plan["record_id"], require_live=require_live)
        filters = {}
        if self._page_limit is not None:
            filters["limit"] = self._page_limit
        if plan["intent"] == "aggregate":
            # ensure the currency field is selected so the currency gate can see it
            filters["fields"] = self._aggregate_fields(plan)
        return self.adapter.list_entities(et, filters=filters or None,
                                          require_live=require_live)

    def _is_live_backend_but_not_live(self) -> bool:
        """True when the adapter's backend is the LiveBackend AND is_live() is False (no
        creds). In that state any fetch must degrade to NO_LIVE_DATA — never fabricate."""
        backend = getattr(self.adapter, "backend", None)
        if backend is None:
            return False
        if not isinstance(backend, self._ad.LiveBackend):
            return False
        try:
            return not backend.is_live()
        except Exception:
            return True

    def _aggregate_fields(self, plan: dict) -> list:
        # ask for id + the summed field + currency + every REQUIRED schema field; the
        # LiveBackend validates these against the introspected schema before sending
        # (unknown field -> refuse, never guess). Including the required fields is essential:
        # the schema_validation + schema_drift gates REFUSE a record missing a required field,
        # so a too-thin projection would (correctly) block delivery of a real aggregate.
        fields = ["id", plan["aggregate_field"]]
        cf = plan.get("currency_field")
        if cf:
            fields.append(cf)
        schema = self.gate_suite._schema_for(plan["entity_type"], True) or {}
        for req in (schema.get("required_fields") or []):
            if req not in fields:
                fields.append(req)
        # de-dup, preserve order
        seen = set()
        ordered = []
        for f in fields:
            if f not in seen:
                seen.add(f)
                ordered.append(f)
        return ordered

    # --- intent: count -----------------------------------------------------
    def _answer_count(self, plan: dict, raw: dict, rid: str) -> dict:
        body = raw.get("body") if isinstance(raw.get("body"), dict) else {}
        count = body.get("reported_total")
        if count is None:
            count = raw.get("reported_total")
        if count is None:
            return _refused_envelope(
                REASON_FETCH_EMPTY,
                "list response carries no reported_total — cannot prove a count", plan=plan)

        # PROVENANCE: bind the count to the Tier-1 reported_total path.
        path = "$.body.reported_total"
        prov = self.engine.bind_and_verify(count, {"raw_response_id": rid,
                                                   "json_field_path": path},
                                           value_ref=f"{plan['entity_type']}.count")
        if prov["outcome"] != self._provlib.VERIFIED:
            return _refused_envelope(REASON_PROVENANCE, prov["reason"], plan=plan,
                                     extra={"reason_code_inner": prov["reason_code"]})

        # GATES: a count is a LIST result -> run_all (pagination-completeness is the headline
        # gate here; a truncated walk must REFUSE the count). source_count=1 (single API list).
        verdict = self.gate_suite.run_all(
            raw, entity_type=plan["entity_type"], prefer_graphql=True,
            value_ref=f"{plan['entity_type']}.count", source_count=1,
            provenance_report={"ok": True},  # the count's own binding verified above
        )
        if verdict["outcome"] != self._gatelib.OUTCOME_PASS:
            return self._gate_refusal(plan, verdict)

        complete = bool(body.get("complete"))
        confidence = (verdict.get("confidence") or {}).get("confidence")
        value = {
            "value": int(count),
            "provenance": {"raw_response_id": rid, "json_field_path": path},
            "confidence": confidence,
        }
        answer = (f"There are {int(count)} {self._noun(plan['entity_type'])}.")
        return _envelope(STATE_DELIVERED, answer=answer, values=[value],
                         gate_verdict=verdict, complete=complete, refusals=[], plan=plan,
                         meta={"reported_total": int(count),
                               "fetched": body.get("fetched"),
                               "pages": body.get("pages"),
                               "backend": raw.get("backend")})

    # --- intent: lookup ----------------------------------------------------
    def _answer_lookup(self, plan: dict, raw: dict, rid: str) -> dict:
        body = raw.get("body") if isinstance(raw.get("body"), dict) else {}
        record = body.get("record") if isinstance(body, dict) else None
        if not isinstance(record, dict):
            return _refused_envelope(
                REASON_FETCH_EMPTY,
                f"no record found for {plan['entity_type']} {plan.get('record_id')!r}",
                plan=plan)
        field = plan["field"]
        if field not in record:
            return _refused_envelope(
                REASON_FETCH_EMPTY,
                f"field {field!r} absent from the fetched record — refusing (never guess)",
                plan=plan)
        value = record[field]
        path = f"$.body.record.{field}"
        prov = self.engine.bind_and_verify(value, {"raw_response_id": rid,
                                                   "json_field_path": path},
                                           value_ref=f"{plan['entity_type']}.{field}")
        if prov["outcome"] != self._provlib.VERIFIED:
            return _refused_envelope(REASON_PROVENANCE, prov["reason"], plan=plan,
                                     extra={"reason_code_inner": prov["reason_code"]})

        # GATES: a single-record lookup -> deterministic_subset (cheap structural gates).
        verdict = self.gate_suite.deterministic_subset(
            raw, entity_type=plan["entity_type"], prefer_graphql=True,
            value_ref=f"{plan['entity_type']}.{field}", source_count=1,
            provenance_report={"ok": True})
        if verdict["outcome"] != self._gatelib.OUTCOME_PASS:
            return self._gate_refusal(plan, verdict)

        confidence = (verdict.get("confidence") or {}).get("confidence")
        out_value = {
            "value": value,
            "provenance": {"raw_response_id": rid, "json_field_path": path},
            "confidence": confidence,
        }
        answer = (f"The {field} of {plan['entity_type']} "
                  f"{plan.get('record_id')} is {value}.")
        return _envelope(STATE_DELIVERED, answer=answer, values=[out_value],
                         gate_verdict=verdict, complete=True, refusals=[], plan=plan,
                         meta={"backend": raw.get("backend")})

    # --- intent: aggregate -------------------------------------------------
    def _answer_aggregate(self, plan: dict, raw: dict, rid: str) -> dict:
        body = raw.get("body") if isinstance(raw.get("body"), dict) else {}
        items = body.get("data") if isinstance(body, dict) else None
        if not isinstance(items, list):
            return _refused_envelope(
                REASON_FETCH_EMPTY, "aggregate fetch returned no list body", plan=plan)
        field = plan["aggregate_field"]
        cf = plan.get("currency_field")

        # Build contributing bindings (one per source row) + collect values for the sum.
        contributing = []
        contributing_values = []
        currencies = []
        total = 0.0
        for i, rec in enumerate(items):
            if not isinstance(rec, dict) or field not in rec:
                continue
            v = rec[field]
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                return _refused_envelope(
                    REASON_PROVENANCE,
                    f"non-numeric {field!r} on row {i} — refusing to aggregate", plan=plan)
            total += float(v)
            contributing.append({"raw_response_id": rid,
                                 "json_field_path": f"$.body.data[{i}].{field}"})
            contributing_values.append(v)
            if cf and cf in rec:
                currencies.append(rec.get(cf))

        if not contributing:
            return _refused_envelope(
                REASON_FETCH_EMPTY,
                f"no rows carried the summable field {field!r}", plan=plan)

        # PROVENANCE: aggregate must bind one resolvable+matching source per contributor.
        prov = self.engine.bind_aggregate(
            total, contributing, contributing_values=contributing_values,
            value_ref=f"{plan['entity_type']}.total_{field}")
        if prov["outcome"] != self._provlib.VERIFIED:
            return _refused_envelope(REASON_PROVENANCE, prov["reason"], plan=plan,
                                     extra={"reason_code_inner": prov["reason_code"]})

        # GATES: aggregation over a LIST -> run_all with aggregating=True so the
        # mixed-currency refusal + pagination-completeness + reconciliation gates apply.
        records_currencies = [{"amount": v, "currency": c}
                              for v, c in zip(contributing_values, currencies)] if cf else None
        verdict = self.gate_suite.run_all(
            raw, entity_type=plan["entity_type"], prefer_graphql=True,
            value_ref=f"{plan['entity_type']}.total_{field}",
            source_count=len(contributing), aggregating=True,
            records_currencies=records_currencies,
            provenance_report={"ok": True})
        if verdict["outcome"] != self._gatelib.OUTCOME_PASS:
            return self._gate_refusal(plan, verdict)

        complete = bool(body.get("complete"))
        confidence = (verdict.get("confidence") or {}).get("confidence")
        currency = (sorted({c for c in currencies if c}) or [None])[0] if cf else None
        out_value = {
            "value": total,
            "currency": currency,
            "provenance": {"aggregate": True, "raw_response_id": rid,
                           "contributing": [b for b in contributing]},
            "confidence": confidence,
        }
        cur_str = f" {currency}" if currency else ""
        answer = (f"The total {field} across {len(contributing)} "
                  f"{self._noun(plan['entity_type'])} is {total}{cur_str}.")
        return _envelope(STATE_DELIVERED, answer=answer, values=[out_value],
                         gate_verdict=verdict, complete=complete, refusals=[], plan=plan,
                         meta={"sources": len(contributing), "currency": currency,
                               "backend": raw.get("backend")})

    # --- intent: payoff / early redemption ---------------------------------
    def _lazy_resolver(self):
        if self.resolver is not None:
            return self.resolver
        self.resolver = _resolve().LoanResolver()
        return self.resolver

    def _lazy_figures(self):
        if self.figures is not None:
            return self.figures
        self.figures = _figures().build_registry()
        return self.figures

    def _answer_payoff(self, plan: dict) -> dict:
        """Resolve the loan name (echo single match / disambiguate ambiguous — NEVER silently
        pick), then run the early-redemption payoff figure. Reshapes the figure envelope into
        the spine envelope, carrying the resolver echo + candidates for the caller to display.
        """
        figmod = _figures()
        resolver = self._lazy_resolver()
        # 1) RESOLVE the loan name (real API candidates only).
        try:
            res = resolver.resolve_loan(plan["loan_name"])
        except Exception as e:
            # A live resolution failure (transport/500) — refuse, never fabricate.
            return _refused_envelope(
                REASON_FETCH_EMPTY,
                f"could not resolve loan {plan['loan_name']!r}: {type(e).__name__}: "
                f"{str(e)[:160]}", plan=plan)

        if not res.get("resolved"):
            # Ambiguous or no match -> REFUSE with the candidate list (disambiguation).
            cands = res.get("candidates") or []
            if not cands:
                reason = (f"no loan matches {plan['loan_name']!r} — refusing (never invent a "
                          "loan)")
                code = REASON_FETCH_EMPTY
            else:
                reason = (f"loan name {plan['loan_name']!r} is ambiguous — "
                          f"{len(cands)} candidate(s); choose one (NOT auto-picking): "
                          + ", ".join(f"{c['name']} ({c['id']}, score={c['score']})"
                                      for c in cands[:5]))
                code = REASON_UNMAPPABLE
            env = _refused_envelope(code, reason, plan=plan,
                                    extra={"candidates": cands,
                                           "resolver_reason": res.get("reason")})
            env["meta"] = {"resolution": res}
            return env

        match = res["match"]
        loan_id = match["id"]

        # 2) RUN the payoff figure for the resolved id + (optional) date.
        figures = self._lazy_figures()
        figure = figures.get("payoff_as_of")
        if figure is None:  # defensive — the registry always seeds payoff_as_of
            return _refused_envelope(REASON_UNMAPPABLE,
                                     "payoff figure not registered", plan=plan)
        fig_env = figure.run(loan_id=loan_id, date=plan.get("as_of_date"),
                             loan_name=match.get("name"))

        # 3) RESHAPE the figure envelope into the spine envelope (carry echo + resolution).
        state = fig_env.get("state")
        base_meta = {"resolution": res, "echo": res.get("echo"),
                     "loan_id": loan_id, "loan_name": match.get("name"),
                     "candidates": res.get("candidates")}
        base_meta.update(fig_env.get("meta") or {})
        if state == figmod.STATE_DELIVERED:
            return _envelope(STATE_DELIVERED, answer=fig_env.get("answer"),
                             values=fig_env.get("values") or [],
                             gate_verdict=fig_env.get("gate_verdict"),
                             complete=bool(fig_env.get("complete")), refusals=[], plan=plan,
                             meta=base_meta)
        if state == figmod.STATE_NO_LIVE_DATA:
            env = _no_live_data_envelope(
                plan, (fig_env.get("refusals") or [{}])[0].get("reason", "no live data"))
            env["meta"].update(base_meta)
            return env
        # REFUSED (e.g. LIVE_500 after retries, reconcile failure, provenance refusal).
        inner = (fig_env.get("refusals") or [{}])[0]
        env = _refused_envelope(inner.get("reason_code") or REASON_FIGURE_REFUSED,
                                inner.get("reason") or "payoff figure refused",
                                gate_verdict=fig_env.get("gate_verdict"), plan=plan,
                                extra={"figure_state": state})
        env["meta"] = base_meta
        return env

    # --- intent: figure (ontology-routed, per-loan) ------------------------
    def _answer_figure(self, plan: dict) -> dict:
        """Per-loan figure: resolve the loan name (echo / disambiguate — never silently pick),
        run the named figure, reshape the figure envelope into the spine envelope. An UNMAPPED
        concept never reaches here (plan_question would have refused) — an unregistered figure
        REFUSES naming itself; a requires_external figure refuses with the KG-pending reason."""
        figmod = _figures()

        # An ambiguous CONCEPT (not loan) -> disambiguate the concept, never guess.
        if plan.get("figure_ambiguous"):
            cands = plan.get("concept_candidates") or []
            reason = ("the metric is ambiguous — choose one (NOT auto-picking): "
                      + ", ".join(f"{c['name']} (score={c['score']})" for c in cands[:5]))
            return _refused_envelope(REASON_UNMAPPABLE, reason, plan=plan,
                                     extra={"concept_candidates": cands})

        figure_name = plan["figure_name"]
        figures = self._lazy_figures()
        figure = figures.get(figure_name)
        if figure is None:
            return _refused_envelope(
                REASON_UNMAPPABLE,
                f"concept {figure_name!r} has no registered figure — refusing (never guess)",
                plan=plan)

        # Leverage figures (LTV/DSCR/debt_yield/cap_rate) are KG-JOINED (SLICE-HCA-14): they now
        # COMPUTE from Hypercore loan amounts × the OKOA-KG collateral value/NOI. They therefore
        # need a REAL resolved Hypercore loan id (to fetch outstanding/commitment) AND the loan
        # name (to join the KG) — so they fall through to the SAME resolve-then-run path as the
        # native figures below (no special early-return). They still refuse cleanly when the KG
        # input is absent; a missing loan name is handled by the needs_loan guard.
        if plan.get("needs_loan") or not plan.get("loan_name"):
            return _refused_envelope(
                REASON_UNMAPPABLE,
                (f"the {figure_name!r} figure needs a loan (name it, e.g. 'what is the "
                 f"{figure_name.replace('_', ' ')} for Beehive') — or ask for the portfolio "
                 "total of a summable figure"),
                plan=plan)

        # Resolve the loan name (real API candidates only; echo / disambiguate).
        resolver = self._lazy_resolver()
        try:
            res = resolver.resolve_loan(plan["loan_name"])
        except Exception as e:
            return _refused_envelope(
                REASON_FETCH_EMPTY,
                f"could not resolve loan {plan['loan_name']!r}: {type(e).__name__}: "
                f"{str(e)[:160]}", plan=plan)
        if not res.get("resolved"):
            cands = res.get("candidates") or []
            if not cands:
                reason = (f"no loan matches {plan['loan_name']!r} — refusing (never invent a "
                          "loan)")
                code = REASON_FETCH_EMPTY
            else:
                reason = (f"loan name {plan['loan_name']!r} is ambiguous — "
                          f"{len(cands)} candidate(s); choose one (NOT auto-picking): "
                          + ", ".join(f"{c['name']} ({c['id']}, score={c['score']})"
                                      for c in cands[:5]))
                code = REASON_UNMAPPABLE
            env = _refused_envelope(code, reason, plan=plan,
                                    extra={"candidates": cands,
                                           "resolver_reason": res.get("reason")})
            env["meta"] = {"resolution": res}
            return env

        match = res["match"]
        loan_id = match["id"]
        fig_env = figure.run(loan_id=loan_id, loan_name=match.get("name"),
                             date=plan.get("as_of_date"))
        base_meta = {"resolution": res, "echo": res.get("echo"), "loan_id": loan_id,
                     "loan_name": match.get("name"), "candidates": res.get("candidates"),
                     "figure": figure_name}
        return self._reshape_figure_env(plan, fig_env, base_meta=base_meta)

    def _reshape_figure_env(self, plan: dict, fig_env: dict, *, base_meta: dict) -> dict:
        """Reshape a figure envelope (delivered/refused/no-live) into the spine envelope."""
        figmod = _figures()
        state = fig_env.get("state")
        meta = dict(base_meta)
        meta.update(fig_env.get("meta") or {})
        if state == figmod.STATE_DELIVERED:
            return _envelope(STATE_DELIVERED, answer=fig_env.get("answer"),
                             values=fig_env.get("values") or [],
                             gate_verdict=fig_env.get("gate_verdict"),
                             complete=bool(fig_env.get("complete")), refusals=[], plan=plan,
                             meta=meta)
        if state == figmod.STATE_NO_LIVE_DATA:
            env = _no_live_data_envelope(
                plan, (fig_env.get("refusals") or [{}])[0].get("reason", "no live data"))
            env["meta"].update(meta)
            return env
        inner = (fig_env.get("refusals") or [{}])[0]
        env = _refused_envelope(inner.get("reason_code") or REASON_FIGURE_REFUSED,
                                inner.get("reason") or "figure refused",
                                gate_verdict=fig_env.get("gate_verdict"), plan=plan,
                                extra={"figure_state": state,
                                       "required_source": inner.get("required_source")})
        env["meta"] = meta
        return env

    # --- intent: figure_portfolio (sum a per-loan figure across the portfolio) ----
    def _answer_figure_portfolio(self, plan: dict) -> dict:
        """Aggregate a summable per-loan figure across all loans (e.g. total outstanding).

        Runs the figure per loan (each value provenance-bound + reconciled), then sums. Any
        loan whose figure REFUSES makes the portfolio total REFUSE (never a silent partial). A
        mixed-currency portfolio REFUSES (the currencies cannot be summed). No live data ->
        NO_LIVE_DATA.
        """
        figmod = _figures()
        figure_name = plan["figure_name"]
        figures = self._lazy_figures()
        figure = figures.get(figure_name)
        if figure is None:
            return _refused_envelope(REASON_UNMAPPABLE,
                                     f"concept {figure_name!r} has no registered figure",
                                     plan=plan)

        # Enumerate the portfolio via the reliable list query (unfiltered = all loans).
        resolver = self._lazy_resolver()
        try:
            res = resolver.resolve_loan("")  # empty -> the resolver returns 'empty query'
        except Exception:
            res = None
        loans = self._list_all_loans()
        if loans is None:
            return _no_live_data_envelope(
                plan, "no live data — cannot enumerate the portfolio for a figure total")
        if not loans:
            return _refused_envelope(REASON_FETCH_EMPTY,
                                     "no loans returned — cannot total an empty portfolio",
                                     plan=plan)

        total = 0.0
        per_loan = []
        currencies = set()
        contributing = []
        for ln in loans:
            lid = str(ln.get("id"))
            env = figure.run(loan_id=lid, loan_name=ln.get("name"))
            if env.get("state") != figmod.STATE_DELIVERED:
                state = env.get("state")
                if state == figmod.STATE_NO_LIVE_DATA:
                    return _no_live_data_envelope(
                        plan, (env.get("refusals") or [{}])[0].get("reason", "no live data"))
                inner = (env.get("refusals") or [{}])[0]
                return _refused_envelope(
                    inner.get("reason_code") or REASON_FIGURE_REFUSED,
                    (f"portfolio total of {figure_name!r} refused: loan {lid} "
                     f"({ln.get('name')}) did not deliver: {inner.get('reason')}"),
                    plan=plan, extra={"failed_loan": lid})
            v = env["values"][0]
            total += float(v["value"])
            cur = v.get("currency")
            if cur:
                currencies.add(cur)
            per_loan.append({"loan_id": lid, "name": ln.get("name"), "value": v["value"]})
            contributing.append(v.get("provenance"))

        if len(currencies) > 1:
            return _refused_envelope(
                REASON_GATE_FAIL,
                (f"portfolio total of {figure_name!r} spans mixed currencies {sorted(currencies)} "
                 "— refusing to sum across currencies"),
                plan=plan, extra={"failed_gates": ["currency_consistency"]})
        currency = (sorted(currencies) or [None])[0]
        total = round(total, 4)
        out_value = {
            "value": total, "currency": currency, "unit": "currency",
            "provenance": {"aggregate": True, "figure": figure_name,
                           "contributing": contributing, "per_loan": per_loan},
            "confidence": 0.7,  # aggregated single-source figures stay capped
        }
        cur_str = f" {currency}" if currency else ""
        answer = (f"The total {figure_name.replace('_', ' ')} across {len(per_loan)} loans "
                  f"is {total}{cur_str}.")
        gate_verdict = {"outcome": "pass", "aggregate": True, "loans": len(per_loan),
                        "single_currency": len(currencies) <= 1}
        return _envelope(STATE_DELIVERED, answer=answer, values=[out_value],
                         gate_verdict=gate_verdict, complete=True, refusals=[], plan=plan,
                         meta={"figure": figure_name, "loans": len(per_loan),
                               "currency": currency, "per_loan": per_loan})

    def _list_all_loans(self):
        """Enumerate all portfolio loans (id + name + currency) via the reliable list query.

        Reuses the loan resolver's fetch path (its client + unfiltered list walk). Returns the
        list of loan rows, or None when live data is unavailable (NO_LIVE_DATA upstream)."""
        resolver = self._lazy_resolver()
        try:
            rows = resolver._fetch_loans(None)  # unfiltered fetch -> all loans
        except Exception:
            return None
        return rows or []

    # --- intent: analysis (SLICE-HCA-15, portfolio analysis layer) ---------
    def _lazy_analyzer(self):
        if self.analyzer is not None:
            return self.analyzer
        # Build a live analyzer that shares THIS spine's cache (so the bulk Tier-1 fetch lands
        # in the same content-addressed store). Lazily-live: no network until fetch().
        self.analyzer = _analyze().build_analyzer(cache=self.cache, engine=self.engine)
        return self.analyzer

    def _answer_analysis(self, plan: dict) -> dict:
        """Dispatch a portfolio-analysis plan to the PortfolioAnalyzer and reshape its analysis
        envelope into the spine envelope (carrying rows/aggregates/skipped/provenance verbatim).

        The analyzer enforces its own contract (ONE bulk Tier-1 fetch, pagination-complete gate,
        provenance-bound values, reconciled aggregates, surfaced-not-dropped missing loans), so
        this method only routes by `analysis` kind and translates the terminal state."""
        analyzer = self._lazy_analyzer()
        analysis = plan.get("analysis")
        try:
            if analysis == "rank":
                env = analyzer.rank(plan.get("figure", "outstanding"),
                                    top_n=plan.get("n", 10),
                                    ascending=bool(plan.get("ascending")))
            elif analysis == "rank_by_maturity":
                env = analyzer.rank_by_maturity(top_n=plan.get("n", 10))
            elif analysis == "rank_by_utilization":
                env = analyzer.rank_by_utilization(top_n=plan.get("n", 10))
            elif analysis == "total":
                env = analyzer.total(plan.get("figure", "outstanding"))
            elif analysis == "weighted_average_rate":
                env = analyzer.weighted_average_rate()
            elif analysis == "weighted_average_maturity":
                env = analyzer.weighted_average_maturity()
            elif analysis == "count_by_status":
                env = analyzer.count_by_status()
            elif analysis == "filter_overdue":
                env = analyzer.filter_overdue()
            elif analysis == "filter_active":
                env = analyzer.filter_active()
            elif analysis == "filter_over_outstanding":
                env = analyzer.filter_over_outstanding(plan.get("threshold", 0.0))
            elif analysis == "filter_maturing_within":
                env = analyzer.filter_maturing_within(plan.get("days", 30))
            elif analysis == "concentration_by_status":
                env = analyzer.concentration_by_status()
            elif analysis == "concentration_by_client":
                env = analyzer.concentration_by_client()
            elif analysis == "top_n_concentration":
                env = analyzer.top_n_concentration(plan.get("n", 5))
            elif analysis == "covenant_breach_scan":
                env = analyzer.covenant_breach_scan()
            elif analysis == "most_at_risk":
                # The deterministic at-risk set + criteria; the orchestrator may re-run with an
                # injected agent_runner to add blind consensus (the spine itself spawns no agents).
                env = analyzer.most_at_risk()
            else:
                return _refused_envelope(
                    REASON_UNMAPPABLE,
                    f"unknown analysis kind {analysis!r} — refusing (never guess)", plan=plan)
        except Exception as e:  # noqa: BLE001 — surface as a refusal, never fabricate
            return _refused_envelope(
                REASON_FETCH_EMPTY,
                f"analysis {analysis!r} failed: {type(e).__name__}: {str(e)[:160]}", plan=plan)
        return self._reshape_analysis_env(plan, env)

    def _reshape_analysis_env(self, plan: dict, env: dict) -> dict:
        """Translate an hca-analyze analysis envelope into the spine envelope shape.

        DELIVERED carries rows/aggregates/skipped/provenance into the spine envelope meta + a
        single representative value (the headline aggregate or the row count). NO_LIVE_DATA /
        REFUSED / ESCALATED pass through with their reasons (the analyzer never fabricates)."""
        amod = _analyze()
        state = env.get("state")
        meta = {"analysis": env.get("analysis"), "rows": env.get("rows"),
                "aggregates": env.get("aggregates"), "skipped": env.get("skipped"),
                "analysis_meta": env.get("meta")}
        if state == amod.STATE_DELIVERED:
            # Surface a single representative value for the spine envelope `values`: the headline
            # aggregate when present, else the matched/ranked row count.
            values = []
            aggs = env.get("aggregates") or {}
            headline = None
            for k in ("outstanding", "overdue", "commitment", "amount_due", "total_disbursed",
                      "book_total", "top_n_exposure", "weighted_average_rate",
                      "weighted_average_maturity_days", "at_risk_count", "matched", "assessed"):
                if k in aggs:
                    headline = aggs[k]
                    break
            if isinstance(headline, dict) and "value" in headline:
                values = [{"value": headline.get("value"),
                           "currency": headline.get("currency"),
                           "provenance": headline.get("provenance"),
                           "confidence": 0.7}]
            elif isinstance(headline, (int, float)) and not isinstance(headline, bool):
                values = [{"value": headline, "currency": aggs.get("currency"),
                           "provenance": env.get("provenance"), "confidence": 0.7}]
            return _envelope(STATE_DELIVERED, answer=env.get("answer"), values=values,
                             gate_verdict=env.get("gate_verdict"),
                             complete=bool(env.get("complete")), refusals=[], plan=plan,
                             meta=meta)
        if state == amod.STATE_NO_LIVE_DATA:
            e = _no_live_data_envelope(
                plan, (env.get("refusals") or [{}])[0].get("reason", "no live data"))
            e["meta"].update(meta)
            return e
        if state == amod.STATE_ESCALATED:
            return _envelope(STATE_ESCALATED, answer=env.get("answer"), values=[],
                             gate_verdict=env.get("gate_verdict"), complete=False,
                             refusals=env.get("refusals") or [], plan=plan, meta=meta)
        inner = (env.get("refusals") or [{}])[0]
        e = _refused_envelope(inner.get("reason_code") or REASON_FETCH_EMPTY,
                              inner.get("reason") or "analysis refused",
                              gate_verdict=env.get("gate_verdict"), plan=plan)
        e["meta"] = meta
        return e

    # --- gate-fail refusal: name the failing gate, NEVER a number ----------
    def _gate_refusal(self, plan: dict, verdict: dict) -> dict:
        failures = verdict.get("failures") or ["<unknown>"]
        reason = ("delivery refused — deterministic gate(s) failed: "
                  + ", ".join(failures) + " (no value is delivered while a hard gate fails)")
        return _refused_envelope(REASON_GATE_FAIL, reason, gate_verdict=verdict, plan=plan,
                                 extra={"failed_gates": failures})

    @staticmethod
    def _noun(entity_type: str) -> str:
        return {"loan": "loans", "client": "clients", "equity": "equities",
                "fundingEntity": "funding entities",
                "loanFunding": "loan fundings"}.get(entity_type, entity_type + "s")


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

def ask(question: str, *, adapter=None, cache=None, gate_suite=None, engine=None,
        page_limit: Optional[int] = None, now=None, resolver=None, figures=None,
        analyzer=None) -> dict:
    """One-shot: build a spine and answer a single question. Returns an envelope dict."""
    spine = DeliverySpine(adapter=adapter, cache=cache, gate_suite=gate_suite,
                          engine=engine, page_limit=page_limit, now=now,
                          resolver=resolver, figures=figures, analyzer=analyzer)
    return spine.ask(question)


# ===========================================================================
# REPORT-TIER ORCHESTRATION (SLICE-HCA-08)
# ===========================================================================
#
# A REPORT / TABLE is assembled from MULTIPLE figures. EACH figure carries its OWN
# {label, value, unit/currency, provenance, gate_verdict, confidence, complete}. The report
# composes the same per-figure vertical the thin spine proves (plan -> fetch -> Tier-1 cache
# -> provenance bind+verify -> deterministic gates), once PER FIGURE, and binds the figures
# into one report envelope.
#
# THE REPORT CONTRACT (hard, mirrors the per-figure spine contract one level up):
#   - A report DELIVERS only if EVERY figure delivers. ANY figure that REFUSES surfaces as a
#     refusal in the report — the report NAMES which figure / which gate failed. A refusing
#     figure is NEVER silently dropped and a missing figure is NEVER fabricated.
#   - Per-figure provenance is preserved verbatim: a delivered report figure always carries a
#     resolvable {raw_response_id, json_field_path} (or aggregate contributing[]) so QA can
#     independently re-resolve each figure into Tier-1 and re-do the arithmetic.
#   - The report's terminal state is the WORST of its figures' states:
#       all DELIVERED                         -> DELIVERED
#       any figure NO_LIVE_DATA               -> NO_LIVE_DATA (whole report; no live data)
#       any figure ESCALATED (no quorum)      -> ESCALATED
#       otherwise any figure REFUSED          -> REFUSED
#
# THE TIER STATE MACHINE (documented in SKILL.md + demos/demo-report-pipeline.md):
#
#   RECEIVED
#     -> TIER_ROUTED        route_figure_tier(question) -> "trivial" | "report"
#         |  trivial single value  -> DETERMINISTIC SPINE (DeliverySpine.ask, this module)
#         |  report/aggregation/high-stakes -> CONSENSUS (run_consensus over N blind agents)
#     -> FETCH_OR_CACHE -> RAW_CACHED -> EXTRACT -> [CONSENSUS] -> GATES -> BOUND
#         -> DELIVERED | REFUSED | ESCALATED | NO_LIVE_DATA   (per figure)
#     -> report = bind the per-figure terminal states (DELIVERED only if every figure did)
#
# CONSENSUS vs SPINE — WHO SPAWNS THE BLIND AGENTS:
#   The REAL blind-agent Task() spawning is the MAIN Claude conversation's job (the only
#   context with the Task tool; documented in SKILL.md from slice-06). A Python script cannot
#   spawn Task() agents. So `run_consensus(question, agent_runner, ...)` takes an INJECTED
#   `agent_runner` callable; the orchestrator wires it to N blind general-purpose agents.
#   For THIS orchestration's own live/offline demo (and for unit tests of the report binder)
#   each figure is assembled via the deterministic spine per figure — consensus is unit-tested
#   separately in test_hca_consensus.py with injected runners. A figure spec may opt into the
#   consensus path by supplying its own `agent_runner` (see build_report below).

# Per-figure terminal states reuse the spine's DELIVERED/REFUSED/NO_LIVE_DATA and add the
# consensus ESCALATED. A report figure is the spine envelope PLUS the figure label + units.

TIER_TRIVIAL = "trivial"
TIER_REPORT = "report"


def route_figure_tier(question: str) -> str:
    """Route ONE figure's question to a verification tier (the TIER_ROUTED transition).

    Delegates to the deterministic intake router (hca-route.classify), then maps its class
    onto the two delivery tiers this orchestration drives:

      - a TRIVIAL single-value lookup  -> TIER_TRIVIAL: the deterministic spine is sufficient
        (one extraction, gated; no consensus required).
      - a report / aggregation / high-stakes value -> TIER_REPORT: a single extraction is NOT
        trusted; the figure REQUIRES blind N-agent consensus before any value is delivered.

    Pure + deterministic; makes no data fetch and no model call (mirrors hca-route).
    """
    cls = _route().classify(question)
    # hca-route.classify returns a tier label; anything that is not the trivial-lookup class
    # is treated as report-tier (consensus-required). This is the conservative default: when
    # in doubt, demand consensus.
    trivial = str(cls).strip().lower() in (
        "trivial", "trivial-lookup", "trivial_lookup", "lookup", "single", "single-value")
    return TIER_TRIVIAL if trivial else TIER_REPORT


# ---------------------------------------------------------------------------
# Report envelope builders
# ---------------------------------------------------------------------------

def _report_envelope(state: str, *, title: str, figures: list, refusals: list,
                     generated_at: str, meta: Optional[dict] = None) -> dict:
    """Assemble the report/table envelope.

    Shape (slice-08 + the surface slices 09/10/11 build on):
        { state, title,
          figures: [ {label, value, unit, currency, provenance, gate_verdict,
                      confidence, complete, tier, state} ],
          refusals: [ {figure, reason_code, reason, ...} ],
          generated_at, meta }
    Only DELIVERED figures appear in `figures`; every non-delivered figure appears in
    `refusals` naming itself + its inner reason (never silently dropped).
    """
    return {
        "state": state,
        "title": title,
        "figures": figures,
        "refusals": refusals,
        "generated_at": generated_at,
        "meta": meta or {},
    }


def _figure_from_envelope(label: str, unit: Optional[str], tier: str, env: dict) -> dict:
    """Project a single delivered spine/consensus envelope into a report FIGURE.

    Carries the figure's own value + provenance + gate verdict + confidence + complete so the
    report figure is independently verifiable (per-figure provenance preserved verbatim).
    """
    # spine envelope: values[0]; consensus envelope: top-level value/provenance/confidence.
    if env.get("values"):
        v = env["values"][0]
        value = v.get("value")
        currency = v.get("currency")
        provenance = v.get("provenance")
        confidence = v.get("confidence")
    else:  # consensus-shaped envelope
        value = env.get("value")
        currency = (env.get("meta") or {}).get("currency")
        provenance = env.get("provenance")
        confidence = (env.get("confidence") or {}).get("confidence") \
            if isinstance(env.get("confidence"), dict) else env.get("confidence")
    return {
        "label": label,
        "value": value,
        "unit": unit,
        "currency": currency,
        "provenance": provenance,
        "gate_verdict": env.get("gate_verdict"),
        "confidence": confidence,
        "complete": bool(env.get("complete")),
        "tier": tier,
        "state": STATE_DELIVERED,
    }


def _refusal_from_envelope(label: str, tier: str, env: dict) -> dict:
    """Project a non-delivered figure envelope into a report REFUSAL that NAMES the figure
    and surfaces the inner reason (which gate / why) — never a silent drop, never a number."""
    state = env.get("state")
    inner = (env.get("refusals") or [{}])[0]
    reason_code = inner.get("reason_code")
    reason = inner.get("reason")
    # Normalize the report-level reason_code by figure terminal state.
    if state == STATE_NO_LIVE_DATA:
        report_code = STATE_NO_LIVE_DATA
    elif state == STATE_ESCALATED or reason_code == REASON_NO_CONSENSUS:
        report_code = REASON_NO_CONSENSUS
    else:
        report_code = REASON_FIGURE_REFUSED
    out = {
        "figure": label,
        "tier": tier,
        "figure_state": state,
        "reason_code": report_code,
        "reason": (f"figure {label!r} did not deliver "
                   f"({state}): {reason or reason_code or 'no inner reason'}"),
        "inner_reason_code": reason_code,
        "inner_reason": reason,
    }
    # Surface the named failing gate(s) when present (so the report says which gate failed).
    if inner.get("failed_gates"):
        out["failed_gates"] = inner["failed_gates"]
    return out


def _report_state_from_figures(figure_states: list) -> str:
    """The report's terminal state is the WORST of its figures' states (safe default)."""
    if not figure_states:
        return STATE_REFUSED
    if all(s == STATE_DELIVERED for s in figure_states):
        return STATE_DELIVERED
    if any(s == STATE_NO_LIVE_DATA for s in figure_states):
        return STATE_NO_LIVE_DATA
    if any(s == STATE_ESCALATED for s in figure_states):
        return STATE_ESCALATED
    return STATE_REFUSED


# ---------------------------------------------------------------------------
# The report builder
# ---------------------------------------------------------------------------

class ReportBuilder:
    """Assembles a multi-figure REPORT / TABLE from per-figure verticals.

    Construct with a shared spine (so every figure reads through the SAME Tier-1 cache — this
    is what makes the state machine CHECKPOINTABLE: a re-run of the same figures resolves
    each query to the same content-addressed Tier-1 id and the immutable cache returns the
    prior record without re-fetch). Call `build(title, figures)`.

    Each `figures` entry is a dict spec:
        { "label": "<human label>",                 # required
          "question": "<NL question for one value>", # required
          "unit": "<unit/currency hint>",            # optional, surfaced on the figure
          "agent_runner": <callable(question,n)->[..]>,  # optional: opt into the consensus
                                                          #  path for THIS figure (report tier)
          "force_tier": "trivial"|"report" }          # optional: override route_figure_tier
    """

    def __init__(self, *, spine: Optional["DeliverySpine"] = None,
                 adapter=None, cache=None, gate_suite=None, engine=None,
                 page_limit: Optional[int] = None, now=None):
        self.spine = spine or DeliverySpine(
            adapter=adapter, cache=cache, gate_suite=gate_suite, engine=engine,
            page_limit=page_limit, now=now)
        self._now = now

    def _generated_at(self) -> str:
        import datetime
        if self._now is not None:
            try:
                return self._now.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                pass
        return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # --- one figure --------------------------------------------------------
    def build_figure(self, spec: dict) -> dict:
        """Run ONE figure's vertical and return its (figure, refusal, state) projection.

        Returns a dict {figure?, refusal?, state, tier, raw_envelope} where exactly one of
        figure/refusal is populated. The raw spine/consensus envelope is carried for
        diagnostics + evidence (never trimmed away).
        """
        label = spec.get("label") or spec.get("question") or "<unnamed figure>"
        question = spec.get("question")
        unit = spec.get("unit")
        if not question:
            env = _refused_envelope(REASON_UNMAPPABLE,
                                    f"figure {label!r} has no question to answer", plan=None)
            return {"refusal": _refusal_from_envelope(label, TIER_TRIVIAL, env),
                    "state": STATE_REFUSED, "tier": TIER_TRIVIAL, "raw_envelope": env}

        tier = spec.get("force_tier") or route_figure_tier(question)

        agent_runner = spec.get("agent_runner")
        if tier == TIER_REPORT and agent_runner is not None:
            env = self._figure_via_consensus(question, agent_runner, spec)
        else:
            # The deterministic spine per figure. (Report-tier figures without an injected
            # agent_runner are assembled via the spine for the orchestration's own demo;
            # consensus is unit-tested separately with injected runners — see SKILL.md.)
            env = self.spine.ask(question)

        state = env.get("state")
        if state == STATE_DELIVERED:
            return {"figure": _figure_from_envelope(label, unit, tier, env),
                    "state": STATE_DELIVERED, "tier": tier, "raw_envelope": env}
        return {"refusal": _refusal_from_envelope(label, tier, env),
                "state": state, "tier": tier, "raw_envelope": env}

    def _figure_via_consensus(self, question: str, agent_runner, spec: dict) -> dict:
        """Run a report-tier figure through blind N-agent consensus, then re-shape the
        ConsensusEnvelope into a spine-compatible envelope the report binder understands.

        The figure is first PLANNED + FETCHED + CACHED via the spine's read-only path so a
        real gate_source (the Tier-1 RawApiResponse) + entity_type are available to the
        consensus engine (consensus is ADDITIVE — the agreed value still passes the binder +
        the deterministic gate suite). The blind agents themselves are the orchestrator's
        injected `agent_runner`; THIS module never spawns Task() agents.
        """
        consensus = _consensus()
        # PLAN + FETCH + CACHE (reuse the spine vertical; no model call, read-only).
        try:
            plan = plan_question(question)
        except PlanError as e:
            return _refused_envelope(REASON_UNMAPPABLE, str(e), plan=None,
                                     extra={"detail": e.detail})
        try:
            raw = self.spine._fetch(plan)
        except self.spine._ad.NoLiveDataError as e:
            return _no_live_data_envelope(plan, str(e), inner=getattr(e, "envelope", None))
        except FileNotFoundError as e:
            return _refused_envelope(REASON_FETCH_EMPTY, f"fetch found no data: {e}", plan=plan)
        rid = self.spine.cache.put_raw(raw)
        raw = self.spine.cache.get_raw(rid)

        gate_mode = "run_all" if plan["intent"] in ("count", "aggregate") else \
            "deterministic_subset"
        result = consensus.run_consensus(
            question, agent_runner,
            quorum=spec.get("quorum"), n=spec.get("n"),
            max_redispatch=spec.get("max_redispatch"),
            binder=self.spine.engine, gate_suite=self.spine.gate_suite,
            value_ref=f"{plan['entity_type']}.{plan.get('field') or plan['intent']}",
            entity_type=plan["entity_type"], gate_mode=gate_mode,
            gate_source=raw,
            gate_kwargs={"aggregating": plan["intent"] == "aggregate"})
        return self._consensus_to_spine_envelope(result, plan, raw)

    @staticmethod
    def _consensus_to_spine_envelope(result: dict, plan: dict, raw: dict) -> dict:
        """Translate a ConsensusEnvelope into the spine envelope shape the report binder reads.

        DELIVERED keeps value + provenance + gate_verdict + confidence. A consensus
        escalation (NO_CONSENSUS) becomes the report ESCALATED state; pass-through
        GATE_FAIL / PROVENANCE_REFUSED stay REFUSED.
        """
        if result.get("state") == STATE_DELIVERED:
            return _envelope(
                STATE_DELIVERED, answer=result.get("answer"),
                values=[{
                    "value": result.get("value"),
                    "currency": (result.get("meta") or {}).get("currency"),
                    "provenance": result.get("provenance"),
                    "confidence": (result.get("confidence") or {}).get("confidence")
                    if isinstance(result.get("confidence"), dict) else result.get("confidence"),
                }],
                gate_verdict=result.get("gate_verdict"),
                complete=True, refusals=[], plan=plan,
                meta={"consensus": True, "agreeing_count": result.get("agreeing_count"),
                      "quorum": result.get("quorum"), "n": result.get("n"),
                      "redispatches": result.get("redispatches")})
        # refused / escalated
        inner = (result.get("refusals") or [{}])[0]
        reason_code = inner.get("reason_code")
        if reason_code == REASON_NO_CONSENSUS:
            env = _envelope(STATE_ESCALATED, answer=None, values=[],
                            gate_verdict=result.get("gate_verdict"), complete=False,
                            refusals=result.get("refusals") or [], plan=plan,
                            meta={"consensus": True, "escalated": True,
                                  "agreeing_count": result.get("agreeing_count"),
                                  "quorum": result.get("quorum"), "n": result.get("n")})
            return env
        return _envelope(STATE_REFUSED, answer=None, values=[],
                         gate_verdict=result.get("gate_verdict"), complete=False,
                         refusals=result.get("refusals") or [], plan=plan,
                         meta={"consensus": True})

    # --- the whole report --------------------------------------------------
    def build(self, title: str, figures: list) -> dict:
        """Assemble a multi-figure report. DELIVERS only if EVERY figure delivers; any
        refusing figure surfaces in refusals[] (naming the figure + gate) — never dropped."""
        delivered_figures = []
        refusals = []
        states = []
        for spec in figures:
            res = self.build_figure(spec)
            states.append(res["state"])
            if res.get("figure") is not None:
                delivered_figures.append(res["figure"])
            if res.get("refusal") is not None:
                refusals.append(res["refusal"])
        state = _report_state_from_figures(states)
        meta = {
            "figure_count": len(figures),
            "delivered_count": len(delivered_figures),
            "refused_count": len(refusals),
            "figure_states": states,
            "skill": "acos-hypercore-ask",
        }
        return _report_envelope(state, title=title, figures=delivered_figures,
                                refusals=refusals, generated_at=self._generated_at(),
                                meta=meta)


def build_report(title: str, figures: list, *, adapter=None, cache=None, gate_suite=None,
                 engine=None, page_limit: Optional[int] = None, now=None,
                 spine: Optional["DeliverySpine"] = None) -> dict:
    """One-shot: build a multi-figure report/table envelope from figure specs.

    Each figure spec is {label, question, unit?, agent_runner?, force_tier?, quorum?, n?,
    max_redispatch?}. Returns the report envelope (DELIVERED only if every figure delivered;
    a refusing figure surfaces in refusals[] naming itself + the failing gate).
    """
    builder = ReportBuilder(spine=spine, adapter=adapter, cache=cache, gate_suite=gate_suite,
                            engine=engine, page_limit=page_limit, now=now)
    return builder.build(title, figures)


# ---------------------------------------------------------------------------
# CLI — `--ask "<question>"`. Prints the envelope as JSON. Counts/field-names only; NO PII.
# ---------------------------------------------------------------------------

def _summarize_for_print(env: dict) -> dict:
    """A PII-safe console summary. Surfaces state/answer/value/provenance pointers/gate
    outcome/complete only — never a raw borrower record. For lookups the `value` of a single
    NON-PII field (status/commitment/dates/refId) is shown; the spine only ever LOOKS UP
    non-PII fields by design (see _LOOKUP_FIELDS)."""
    vals = []
    for v in env.get("values", []):
        prov = v.get("provenance", {})
        vals.append({
            "value": v.get("value"),
            "currency": v.get("currency"),
            "confidence": v.get("confidence"),
            "provenance": {
                "raw_response_id": prov.get("raw_response_id"),
                "json_field_path": prov.get("json_field_path"),
                "aggregate": prov.get("aggregate"),
                "contributing_count": len(prov.get("contributing", []))
                if prov.get("contributing") else None,
            },
        })
    gv = env.get("gate_verdict") or {}
    gate_summary = None
    if gv:
        gate_summary = {
            "outcome": gv.get("outcome"), "tier": gv.get("tier"),
            "failures": gv.get("failures"),
            "schema_ok": gv.get("schema_ok"),
            "pagination_complete": gv.get("pagination_complete"),
            "freshness_ok": gv.get("freshness_ok"),
            "reconciliation_ok": gv.get("reconciliation_ok"),
            "normalization_applied": gv.get("normalization_applied"),
            "schema_drift_ok": gv.get("schema_drift_ok"),
            "provenance_ok": gv.get("provenance_ok"),
        }
    return {
        "state": env.get("state"),
        "answer": env.get("answer"),
        "values": vals,
        "gate_verdict": gate_summary,
        "complete": env.get("complete"),
        "refusals": env.get("refusals"),
        "plan": {k: env.get("plan", {}).get(k) for k in ("intent", "entity_type", "tier",
                                                         "field", "record_id",
                                                         "aggregate_field",
                                                         "loan_name", "as_of_date",
                                                         "figure_name", "concept_kind",
                                                         "analysis", "figure")}
        if env.get("plan") else None,
        "meta": env.get("meta"),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="acos-hypercore-ask thin end-to-end deterministic answer spine (Demo 1).")
    parser.add_argument("--ask", dest="ask", metavar="QUESTION",
                        help="natural-language question to answer end-to-end")
    parser.add_argument("--backend", choices=["fixture", "live"], default=None,
                        help="force a backend (default: config.yaml / HCA_ADAPTER_BACKEND)")
    parser.add_argument("--page-limit", type=int, default=None,
                        help="page size for live list pagination (default: backend default)")
    parser.add_argument("--full", action="store_true",
                        help="print the full envelope JSON (default: a PII-safe summary)")
    args = parser.parse_args(argv)

    if not args.ask:
        parser.error("a question is required: --ask \"how many loans are there?\"")

    ad = _adapter()
    adapter = ad.HypercoreAdapter(ad.select_backend(backend=args.backend)) \
        if args.backend else None
    env = ask(args.ask, adapter=adapter, page_limit=args.page_limit)

    out = env if args.full else _summarize_for_print(env)
    print(json.dumps(out, indent=2, default=str))
    # Exit non-zero on a non-delivered terminal state so shell callers can branch.
    return 0 if env.get("state") == STATE_DELIVERED else 1


if __name__ == "__main__":
    sys.exit(main())
