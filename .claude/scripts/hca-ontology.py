#!/usr/bin/env python3
"""hca-ontology.py — the PRIVATE-CREDIT DOMAIN ONTOLOGY for acos-hypercore-ask (SLICE-HCA-13).

A concept map that lets the deliver planner turn a human phrasing ("what's the UPB on
Beehive?", "how much is drawn vs committed?") into a NAMED, sourceable concept — or a clean
REFUSAL when the concept is real but not yet sourceable. It is the bridge between OKOA's PRISM
domain vocabulary and the Hypercore figures registry (`hca-figures.py`).

Seeded from:
  - planning/preeng/001-hypercore-ask/_prism-domain-learnings.md (the domain source of truth:
    PRISM metric definitions, formulas, covenant thresholds, Hypercore field mapping)
  - ~/okoa-labs/.../prism-financial-modeler/templates/bridge-loan.yaml (OKOA's product spec;
    read-only — the covenant defaults LTV 75% / DSCR 1.25x / Debt Yield 8% come from here).

EACH CONCEPT declares:
  - name          : canonical concept name (snake_case; matches a figure name when one exists)
  - synonyms      : alternate terms a user might actually say (lowercased on match)
  - definition    : plain-English, one-paragraph definition (no jargon left unexplained)
  - kind          : one of
                      KIND_DIRECT          — a value read straight off ONE GraphQL field
                      KIND_DERIVED         — computed from other concepts via a TRANSPARENT
                                             formula (the formula + input concepts are carried)
                      KIND_REQUIRES_EXTERNAL — a real metric that Hypercore CANNOT source on
                                             its own (it needs collateral/income data from the
                                             OKOA knowledge graph); these REFUSE cleanly, never
                                             fabricate. PRISM covenant thresholds are carried as
                                             metadata for later comparison once the KG join lands.
  - source        : for DIRECT  -> the GraphQL field path (e.g. "summary.totalOutstanding.total")
                    for DERIVED -> {"formula": "...", "inputs": [concept, ...]}
                    for REQUIRES_EXTERNAL -> a human string naming the required external source
  - unit          : "currency" | "percent" | "ratio" | "date" | "rate" (display hint)
  - covenant      : optional {threshold, direction, basis} carried from PRISM for the metrics
                    that have covenants (LTV/DSCR/Debt Yield). Direction is "max" or "min".

The ontology is data, not behavior: it RESOLVES a phrasing to a concept and reports the
concept's sourceability. The actual fetch+verify is owned by `hca-figures.py`; the planner in
`hca-deliver.py` wires the two together (synonym/fuzzy route -> figure -> envelope).

GROUND RULES (memory/decisions/2026-06-18-hca-build-ground-rules.md):
  - Python 3 stdlib ONLY. No third-party deps. No model calls; never ANTHROPIC_API_KEY.
  - Read-only: this module touches no network and no Tier-1 cache; it is a pure concept map.
  - No real PII: it carries metric DEFINITIONS + field paths only, never borrower data.
"""

from __future__ import annotations

import argparse
import difflib
import importlib.util
import json
import os
import re
import sys
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Sibling module loading (hyphenated filename -> import by file path, cached)
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
    # hca-vocab is a pure data LEAF (imports nothing from the skill) -> sourcing the KIND_*
    # constants from it cannot create a circular import.
    return _load("hca_vocab", "hca-vocab.py")


# ---------------------------------------------------------------------------
# Concept kinds — single source of truth in the shared vocabulary leaf (these were duplicated
# identically here and in hca-figures.py). Re-exported as module attributes so existing
# `ont_mod.KIND_DIRECT` references (tests + planner) keep working unchanged.
# ---------------------------------------------------------------------------

KIND_DIRECT = _vocab().KIND_DIRECT                      # one GraphQL field
KIND_DERIVED = _vocab().KIND_DERIVED                    # transparent formula over concepts
KIND_REQUIRES_EXTERNAL = _vocab().KIND_REQUIRES_EXTERNAL  # needs the OKOA KG (appraised / NOI)


# PRISM covenant thresholds (OKOA bridge-loan defaults — bridge-loan.yaml Assumptions/Covenants;
# carried as metadata so the analysis slice can flag breaches without re-discovering them).
COVENANT_MAX_LTV = 0.75       # bridge-loan.yaml max_ltv default (OKOA default; market 65-80%)
COVENANT_MIN_DSCR = 1.25      # bridge-loan.yaml min_dscr default (market standard)
COVENANT_MIN_DEBT_YIELD = 0.08  # bridge-loan.yaml min_debt_yield default (OKOA default)


# The clean-refusal reason used when a concept exists but Hypercore cannot source it.
KG_PENDING_REASON = (
    "requires external collateral data (appraised value / NOI) from the OKOA knowledge "
    "graph — the KG-join slice is pending; refusing rather than fabricating"
)


# ---------------------------------------------------------------------------
# Normalization + scoring helpers (shared style with hca-resolve.py; stdlib only)
# ---------------------------------------------------------------------------

_WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _normalize(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return " ".join(_WORD_RE.findall(text.lower()))


def _tokens(text: str) -> set:
    return set(_WORD_RE.findall((text or "").lower()))


def _score_phrase(query: str, term: str) -> float:
    """Score how well `query` matches a concept term in [0, 1].

    Blend of difflib character-ratio + token-set overlap, with an exact-match short-circuit
    and a query-is-subset bonus (so "drawn" matches "total drawn / disbursed" strongly). Mirrors
    the resolver's scoring philosophy but is tuned for short metric phrasings.
    """
    nq, nt = _normalize(query), _normalize(term)
    if not nq or not nt:
        return 0.0
    if nq == nt:
        return 1.0
    ratio = difflib.SequenceMatcher(None, nq, nt).ratio()
    qt, tt = _tokens(query), _tokens(term)
    inter = len(qt & tt)
    union = len(qt | tt)
    jaccard = inter / union if union else 0.0
    subset_bonus = 1.0 if qt and qt <= tt else (inter / len(qt) if qt else 0.0)
    containment = 0.0
    if nq in nt or nt in nq:
        shorter, longer = (nq, nt) if len(nq) <= len(nt) else (nt, nq)
        containment = len(shorter) / len(longer) if longer else 0.0
    score = (0.30 * ratio) + (0.30 * jaccard) + (0.25 * subset_bonus) + (0.15 * containment)
    if qt and qt <= tt:
        coverage = len(qt) / len(tt) if tt else 0.0
        score = max(score, 0.80 + 0.20 * coverage)
    return max(0.0, min(1.0, round(score, 4)))


# ---------------------------------------------------------------------------
# Concept
# ---------------------------------------------------------------------------

class Concept:
    """A single private-credit concept in the ontology."""

    __slots__ = ("name", "synonyms", "definition", "kind", "source", "unit", "covenant")

    def __init__(self, name: str, *, synonyms=(), definition: str = "",
                 kind: str = KIND_DIRECT, source: Any = None,
                 unit: str = "currency", covenant: Optional[dict] = None):
        self.name = name
        self.synonyms = tuple(synonyms)
        self.definition = definition
        self.kind = kind
        self.source = source
        self.unit = unit
        self.covenant = covenant

    # --- matching ----------------------------------------------------------
    def terms(self) -> list:
        """Every phrasing that names this concept (canonical name + synonyms)."""
        return [self.name] + list(self.synonyms)

    def matches(self, token: str) -> bool:
        """Exact (normalized) match on the canonical name or any synonym."""
        t = _normalize(token)
        if not t:
            return False
        return any(_normalize(term) == t for term in self.terms())

    def best_score(self, query: str) -> float:
        """The best fuzzy score of `query` against any of this concept's terms."""
        return max((_score_phrase(query, term) for term in self.terms()), default=0.0)

    # --- serialization -----------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "synonyms": list(self.synonyms),
            "definition": self.definition,
            "kind": self.kind,
            "source": self.source,
            "unit": self.unit,
            "covenant": self.covenant,
        }

    def input_concepts(self) -> list:
        """For a derived concept, the list of concept names it is computed from."""
        if self.kind == KIND_DERIVED and isinstance(self.source, dict):
            return list(self.source.get("inputs") or [])
        return []


# ---------------------------------------------------------------------------
# Ontology
# ---------------------------------------------------------------------------

# Match policy (mirrors resolver thresholds; conservative so a near-miss disambiguates).
HIGH_CONFIDENCE = 0.82
AMBIGUITY_GAP = 0.08
MIN_CANDIDATE_SCORE = 0.34


class Ontology:
    """The private-credit concept map. Resolves a phrasing -> concept (named, no guessing)."""

    def __init__(self, concepts: Optional[list] = None,
                 *, high_confidence: float = HIGH_CONFIDENCE,
                 ambiguity_gap: float = AMBIGUITY_GAP,
                 min_candidate_score: float = MIN_CANDIDATE_SCORE):
        self._concepts: list = list(concepts or [])
        self._high = float(high_confidence)
        self._gap = float(ambiguity_gap)
        self._min = float(min_candidate_score)

    # --- registry ----------------------------------------------------------
    def add(self, concept: Concept) -> None:
        self._concepts.append(concept)

    def concepts(self) -> list:
        return list(self._concepts)

    def names(self) -> list:
        return [c.name for c in self._concepts]

    def get(self, token: str) -> Optional[Concept]:
        """Exact-match lookup by canonical name or synonym (no fuzzy). None on miss."""
        for c in self._concepts:
            if c.matches(token):
                return c
        return None

    # --- fuzzy resolution --------------------------------------------------
    def resolve(self, query: str) -> dict:
        """Resolve a free-text phrasing to a concept.

        Returns:
            {
              "query": <original>,
              "concept": <Concept|None>,   # set only on a high-confidence single match
              "resolved": bool,
              "ambiguous": bool,
              "candidates": [ {name, score, kind}, ... ],  # ranked, above the min threshold
              "reason": <str>,
            }

        Policy mirrors the loan resolver: exactly one high-confidence match (clearly best) ->
        resolve; multiple close / low-confidence -> ambiguous (hand back candidates, never pick);
        nothing above the floor -> a clean miss. An unmapped concept is NEVER guessed.
        """
        if not isinstance(query, str) or not query.strip():
            return {"query": query, "concept": None, "resolved": False,
                    "ambiguous": False, "candidates": [], "reason": "empty query"}

        # Exact match always wins (e.g. the planner passes a canonical figure name).
        exact = self.get(query)
        if exact is not None:
            return {"query": query, "concept": exact, "resolved": True, "ambiguous": False,
                    "candidates": [{"name": exact.name, "score": 1.0, "kind": exact.kind}],
                    "reason": "exact concept name/synonym match"}

        # Verbatim-substring fast path: a concept's multi-word synonym phrase appearing as a
        # whole-word substring of a filler-laden query ("what's the outstanding balance") is a
        # strong, unambiguous signal — resolve to the concept with the LONGEST matching term
        # (most specific). Single short tokens (<=3 chars) are excluded to avoid noise.
        nq_spaced = " " + _normalize(query) + " "
        sub_best = None  # (concept, matched_term_len)
        for c in self._concepts:
            for term in c.terms():
                nt = _normalize(term)
                if not nt or len(nt) <= 3:
                    continue
                if (" " + nt + " ") in nq_spaced:
                    if sub_best is None or len(nt) > sub_best[1]:
                        sub_best = (c, len(nt))
        if sub_best is not None:
            c = sub_best[0]
            return {"query": query, "concept": c, "resolved": True, "ambiguous": False,
                    "candidates": [{"name": c.name, "score": 1.0, "kind": c.kind}],
                    "reason": "concept synonym appears verbatim in the query"}

        scored = []
        for c in self._concepts:
            s = c.best_score(query)
            scored.append({"name": c.name, "score": s, "kind": c.kind, "_c": c})
        scored.sort(key=lambda d: (-d["score"], d["name"]))
        candidates = [d for d in scored if d["score"] >= self._min]
        if not candidates:
            return {"query": query, "concept": None, "resolved": False, "ambiguous": False,
                    "candidates": [], "reason": "no concept scored above the minimum (no match)"}

        top = candidates[0]
        second = candidates[1] if len(candidates) > 1 else None
        close = second is not None and (top["score"] - second["score"]) < self._gap
        pub = [{"name": d["name"], "score": d["score"], "kind": d["kind"]} for d in candidates]
        if top["score"] >= self._high and not close:
            return {"query": query, "concept": top["_c"], "resolved": True, "ambiguous": False,
                    "candidates": pub,
                    "reason": (f"single high-confidence concept (score={top['score']}, "
                               f"runner-up gap >= {self._gap})")}
        reason = ("multiple plausible concepts (top not clearly best) — NOT auto-resolving"
                  if close else
                  f"best score {top['score']} below high-confidence {self._high} — "
                  "NOT auto-resolving")
        return {"query": query, "concept": None, "resolved": False, "ambiguous": True,
                "candidates": pub, "reason": reason}


# ---------------------------------------------------------------------------
# The seed (PRISM-derived). This IS the OKOA private-credit concept map.
# ---------------------------------------------------------------------------

def _seed_concepts() -> list:
    """Build the seeded concept list from PRISM domain learnings + bridge-loan.yaml.

    The canonical names line up 1:1 with the figures registered in hca-figures.py so a resolved
    concept routes straight to its figure (the derived utilization concept's inputs name the
    direct concepts that feed it).
    """
    return [
        # --- Balance / outstanding (DIRECT off LoanSummary) -----------------
        Concept(
            "outstanding_balance",
            synonyms=("outstanding", "total outstanding", "current balance", "unpaid principal",
                      "upb", "balance", "loan balance", "outstanding amount"),
            definition=("The total amount the borrower still owes on the loan right now — "
                        "unpaid principal plus accrued interest, fees, and penalties. The "
                        "single 'what's owed today' number."),
            kind=KIND_DIRECT, source="summary.totalOutstanding.total", unit="currency"),
        Concept(
            "principal_outstanding",
            synonyms=("principal", "outstanding principal", "principal balance",
                      "unpaid principal balance", "remaining principal"),
            definition=("The unpaid principal portion of the balance only — the original "
                        "advanced money still owed, excluding interest, fees, and penalties."),
            kind=KIND_DIRECT, source="summary.totalOutstanding.principal", unit="currency"),
        Concept(
            "accrued_interest",
            synonyms=("interest", "accrued interest", "interest outstanding", "running interest",
                      "interest owed", "interest accrued"),
            definition=("Interest that has accumulated on the loan but has not yet been paid. "
                        "Includes both ordinary interest and any compounding interest accrued."),
            kind=KIND_DIRECT, source="summary.totalOutstanding.interest", unit="currency"),
        Concept(
            "default_interest",
            synonyms=("default interest", "penalties", "penalty interest", "late charges",
                      "default penalties", "total penalties", "penalty"),
            definition=("Penalty / default interest charged on top of the note rate after a "
                        "default or late payment — the extra cost of being past due."),
            kind=KIND_DIRECT, source="summary.totalOutstanding.totalPenalties", unit="currency"),
        Concept(
            "amount_due_today",
            synonyms=("amount due", "due today", "total due", "amount due today", "due now",
                      "currently due", "total amount due"),
            definition=("The amount currently due and payable — the portion of the balance the "
                        "borrower is obligated to pay as of today (a subset of total owed)."),
            kind=KIND_DIRECT, source="summary.totalDue.total", unit="currency"),
        Concept(
            "overdue_amount",
            synonyms=("overdue", "overdue amount", "past due", "arrears", "amount overdue",
                      "delinquent amount"),
            definition=("The amount that is past its due date and unpaid — money the borrower "
                        "should already have paid but has not."),
            kind=KIND_DIRECT, source="summary.overdue.total", unit="currency"),

        # --- Sizing / commitment / disbursement ----------------------------
        Concept(
            "commitment",
            synonyms=("commitment", "loan amount", "loan size", "face amount", "committed",
                      "committed amount", "facility amount", "total commitment"),
            definition=("The face amount the lender committed to the loan — the ceiling on how "
                        "much can ever be drawn. PRISM's loan_amount / senior_loan."),
            kind=KIND_DIRECT, source="loan.commitment", unit="currency"),
        Concept(
            "total_disbursed",
            synonyms=("disbursed", "total disbursed", "drawn", "total drawn", "advanced",
                      "funded", "amount funded", "amount drawn", "total advanced", "disbursement"),
            definition=("The total amount actually advanced/funded to the borrower so far "
                        "(cumulative draws against the commitment)."),
            kind=KIND_DIRECT, source="summary.totalDisbursed", unit="currency"),

        # --- DERIVED (transparent formula) ---------------------------------
        Concept(
            "utilization",
            synonyms=("utilization", "utilisation", "utilization rate", "drawn vs committed",
                      "percent drawn", "% drawn", "draw rate", "usage", "utilization ratio"),
            definition=("How much of the commitment has been drawn, as a fraction: total "
                        "disbursed divided by commitment. 1.0 (100%) means fully drawn. A "
                        "transparent ratio computed from two direct figures (inputs shown)."),
            kind=KIND_DERIVED,
            source={"formula": "total_disbursed / commitment",
                    "inputs": ["total_disbursed", "commitment"]},
            unit="ratio"),

        # --- Duration / maturity (DIRECT) ----------------------------------
        Concept(
            "maturity_date",
            synonyms=("maturity", "maturity date", "due date", "balloon date", "loan end date",
                      "end date", "expiry", "scheduleenddate", "schedule end date"),
            definition=("The date the loan is scheduled to be repaid in full — its balloon / "
                        "end date. Hypercore's scheduleEndDate."),
            kind=KIND_DIRECT, source="loan.scheduleEndDate", unit="date"),

        # --- Payoff / early redemption (DERIVED — already a figure) ---------
        Concept(
            "payoff_as_of",
            synonyms=("payoff", "early redemption", "early_redemption", "amount to redeem",
                      "redemption", "redeem", "payoff amount", "total payoff",
                      "redemption amount", "amount to pay off"),
            definition=("The all-in amount required to fully retire the loan as of a given date "
                        "— principal + accrued interest + fees + any penalties, exactly as the "
                        "Hypercore Early-Redemption calculation reports it. Reconciled to its "
                        "components to the cent."),
            kind=KIND_DERIVED,
            source={"formula": ("getLoanRepaymentDistribution.total = principal + "
                                "indexedPrincipal + interest + compoundingInterest + "
                                "accruedCompoundingInterest + totalFees + totalPenalties + "
                                "totalTaxes"),
                    "inputs": ["principal_outstanding", "accrued_interest", "default_interest"]},
            unit="currency"),

        # --- Leverage / coverage (REQUIRES_EXTERNAL — KG join pending) ------
        Concept(
            "ltv",
            synonyms=("ltv", "loan to value", "loan-to-value", "ltv ratio", "leverage ratio"),
            definition=("Loan-to-Value: the loan balance divided by the property's appraised "
                        "value. Measures how much of the collateral's worth is lent against. "
                        "Requires the appraised value, which lives outside Hypercore (in the "
                        "OKOA knowledge graph / appraisal docs)."),
            kind=KIND_REQUIRES_EXTERNAL,
            source="OKOA knowledge graph (appraised_value / as_is_value)",
            unit="percent",
            covenant={"threshold": COVENANT_MAX_LTV, "direction": "max",
                      "basis": "PRISM bridge-loan max_ltv (OKOA default 75%)"}),
        Concept(
            "dscr",
            synonyms=("dscr", "debt service coverage", "debt service coverage ratio",
                      "debt coverage ratio", "dsc", "dcr"),
            definition=("Debt Service Coverage Ratio: net operating income divided by the loan's "
                        "debt service (annual interest for an interest-only bridge loan). Above "
                        "1.0 means the property's income covers its debt payments. Requires NOI, "
                        "which lives outside Hypercore (OKOA knowledge graph / operating data)."),
            kind=KIND_REQUIRES_EXTERNAL,
            source="OKOA knowledge graph (NOI / net operating income)",
            unit="ratio",
            covenant={"threshold": COVENANT_MIN_DSCR, "direction": "min",
                      "basis": "PRISM bridge-loan min_dscr (1.25x)"}),
        Concept(
            "debt_yield",
            synonyms=("debt yield", "debt_yield", "debt yield %", "dy"),
            definition=("Debt Yield: net operating income divided by the loan amount — the "
                        "unleveraged return the lender would earn if it took title, independent "
                        "of cap-rate assumptions. Requires NOI, which lives outside Hypercore "
                        "(OKOA knowledge graph)."),
            kind=KIND_REQUIRES_EXTERNAL,
            source="OKOA knowledge graph (NOI / net operating income)",
            unit="percent",
            covenant={"threshold": COVENANT_MIN_DEBT_YIELD, "direction": "min",
                      "basis": "PRISM bridge-loan min_debt_yield (OKOA default 8%)"}),
        Concept(
            "cap_rate",
            synonyms=("cap rate", "cap_rate", "capitalization rate", "capitalisation rate"),
            definition=("Capitalization Rate: net operating income divided by the property "
                        "value — the market yield on the asset. Requires both NOI and property "
                        "value, which live outside Hypercore (OKOA knowledge graph / appraisal)."),
            kind=KIND_REQUIRES_EXTERNAL,
            source="OKOA knowledge graph (NOI + property value / appraised_value)",
            unit="percent"),
    ]


# ---------------------------------------------------------------------------
# Default ontology builder (the public entry the planner uses)
# ---------------------------------------------------------------------------

_DEFAULT: Optional[Ontology] = None


def build_ontology() -> Ontology:
    """Build the default OKOA private-credit ontology (seeded from PRISM)."""
    return Ontology(_seed_concepts())


def default_ontology() -> Ontology:
    """Process-wide singleton (cheap to share; the concept list is immutable in practice)."""
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = build_ontology()
    return _DEFAULT


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

def resolve_concept(query: str, *, ontology: Optional[Ontology] = None) -> dict:
    """One-shot: resolve a phrasing against the default ontology. Returns the resolve dict
    with `concept` serialized to a plain dict (CLI/JSON-friendly)."""
    ont = ontology or default_ontology()
    res = ont.resolve(query)
    c = res.get("concept")
    res = dict(res)
    res["concept"] = c.to_dict() if isinstance(c, Concept) else None
    return res


# ---------------------------------------------------------------------------
# CLI — `--resolve "<phrase>"` or `--list`. Prints the concept map / a resolution as JSON.
# Concept DEFINITIONS + field paths only — no PII, no live call.
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="acos-hypercore-ask private-credit domain ontology (PRISM-seeded).")
    parser.add_argument("--resolve", dest="resolve", metavar="PHRASE",
                        help="resolve a free-text metric phrasing to a concept")
    parser.add_argument("--list", dest="list_all", action="store_true",
                        help="print the full concept map")
    args = parser.parse_args(argv)
    ont = build_ontology()
    if args.list_all:
        print(json.dumps([c.to_dict() for c in ont.concepts()], indent=2, default=str))
        return 0
    if args.resolve:
        res = resolve_concept(args.resolve, ontology=ont)
        print(json.dumps(res, indent=2, default=str))
        return 0 if res.get("resolved") else 1
    parser.error('supply --resolve "<phrase>" or --list')
    return 2


if __name__ == "__main__":
    sys.exit(main())
