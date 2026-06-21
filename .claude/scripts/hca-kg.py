#!/usr/bin/env python3
"""hca-kg.py — OKOA KNOWLEDGE-GRAPH JOIN for acos-hypercore-ask (SLICE-HCA-14).

Hypercore holds the LIABILITY side of a loan (balance, payments, maturity, fees) but NOT the
property/income side (appraised value, NOI). The leverage / coverage ratios — LTV, DSCR,
debt-yield, cap-rate — need that second source. This module is the READ-ONLY bridge to it: the
OKOA knowledge graph (`~/okoa-labs/okoa_ops/knowledge-graph/nodes.csv`).

WHAT IT DOES
  `kg_lookup(loan_name)` fuzzy-matches a Hypercore loan name against the KG's DEAL / PROPERTY /
  CLAIM nodes (on canonical_name + aliases, stdlib difflib + token overlap — the SAME scoring
  philosophy as hca-resolve.py), parses the matched node's `properties_json`, and extracts the
  collateral facts the ratio figures need:

      appraised_value | noi | purchase_price | ltv_latest | interest_rate | appraisal_date

  Each returned fact carries PROVENANCE = the exact source node_id + the field it came from (+
  the KG file), and the matched node's own `confidence`. CLAIM-based values are resolved via the
  claim's `subject_node_id` so the provenance points at the underlying subject, not just the
  claim wrapper.

NON-NEGOTIABLE GROUND RULES
  - READ-ONLY. This module NEVER writes to ~/okoa-labs. It only reads two CSVs.
  - Python 3 stdlib ONLY (csv, json, difflib, re, os). No third-party deps. No model calls;
    never ANTHROPIC_API_KEY.
  - NEVER fabricate. If there is no confident node match, or the specific field is absent for
    the matched loan, the relevant key is simply ABSENT from the result (None / missing) — the
    caller (hca-figures.py) then returns a clean structured REFUSAL. A value is never invented.
  - No borrower PII leaves this module beyond what the figures need: provenance carries the KG
    `node_id` + field name only (NOT names, addresses, or other PII).

The KG path is configurable (default `~/okoa-labs/okoa_ops/knowledge-graph/`); see `KGStore`.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import os
import re
import sys
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Config — where the KG lives (read-only). Override via env or KGStore(kg_dir=...).
# ---------------------------------------------------------------------------

DEFAULT_KG_DIR = os.path.expanduser("~/okoa-labs/okoa_ops/knowledge-graph")
NODES_FILENAME = "nodes.csv"
EDGES_FILENAME = "edges.csv"  # not needed for the current join, but part of the contract dir

# The node types that can carry collateral / valuation facts (ranked by how authoritative they
# are for a loan-level join: DEAL is the deal-level roll-up, PROPERTY the collateral asset,
# CLAIM a normalized single fact). FINANCIAL_INSTRUMENT can hold loan-amount/rate facts.
VALUE_NODE_TYPES = ("DEAL", "PROPERTY", "FINANCIAL_INSTRUMENT", "CLAIM")

# Allow a small CSV cell to hold a large properties_json blob.
csv.field_size_limit(min(sys.maxsize, 2_000_000_000))


# ---------------------------------------------------------------------------
# Match policy (mirrors hca-resolve.py thresholds; conservative so a near-miss refuses).
# ---------------------------------------------------------------------------

HIGH_CONFIDENCE = 0.82       # a single match must clear this to be "confident"
AMBIGUITY_GAP = 0.08         # top two within this gap -> too close to call -> no confident match
MIN_CANDIDATE_SCORE = 0.40   # below this is not even a plausible candidate

# Generic words that do NOT make two node names "the same deal" (so a tie between, say, two
# unrelated "... Commercial" deals is still treated as ambiguous, while a DEAL + its collateral
# PROPERTY that share a distinctive root like "lakeside"/"springville" are recognised as one).
_STOPWORD_TOKENS = {
    "the", "of", "a", "an", "llc", "lp", "inc", "co", "utah", "ut", "park", "city",
    "commercial", "residential", "land", "loan", "deal", "property", "properties",
    "investors", "capital", "holdings", "development", "apartments", "estates",
}


# ---------------------------------------------------------------------------
# Field extraction maps — the KG property keys that carry each fact we need.
# Ordered by preference; first present wins. Kept explicit (no guessing) so the
# provenance always names the EXACT field the number came from.
# ---------------------------------------------------------------------------

# Appraised / collateral value (the LTV / cap-rate denominator).
_APPRAISED_VALUE_KEYS = (
    "appraised_value", "as_is_value", "as_stabilized_value",
    "current_value_estimate", "prospective_appraisal_74_lots",
)

# Net operating income (the DSCR / debt-yield / cap-rate numerator).
_NOI_KEYS = (
    "noi", "net_operating_income", "noi_dollars", "noi_basis", "stabilized_noi",
)

_PURCHASE_PRICE_KEYS = ("purchase_price",)
_LTV_LATEST_KEYS = ("ltv_latest",)
_INTEREST_RATE_KEYS = ("interest_rate", "annual_interest_rate")
_APPRAISAL_DATE_KEYS = ("appraisal_date", "as_of_date", "valuation_date")

# CLAIM classification — a financial CLAIM whose node_id/canonical_name reads like one of these
# is mapped to the corresponding fact. (CLAIM nodes carry a single normalized_value, so we route
# by what the claim is ABOUT.)
_CLAIM_APPRAISED_HINTS = ("appraised-value", "appraised value", "appraisal", "as-is-value")
_CLAIM_NOI_HINTS = ("noi", "net-operating-income", "net operating income")
_CLAIM_PURCHASE_HINTS = ("purchase-price", "purchase price")


# ---------------------------------------------------------------------------
# Normalization + scoring (pure; stdlib only — shared philosophy with hca-resolve.py)
# ---------------------------------------------------------------------------

_WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _normalize(name: str) -> str:
    if not isinstance(name, str):
        return ""
    return " ".join(_WORD_RE.findall(name.lower()))


def _tokens(name: str) -> set:
    return set(_WORD_RE.findall((name or "").lower()))


def score_name(query: str, candidate_name: str) -> float:
    """Score how well `candidate_name` matches `query` in [0, 1].

    Blend of difflib character-ratio + token-set overlap, with an exact-match short-circuit, a
    containment boost, and a query-is-subset bonus (so a partial loan name like "broadbent"
    matches "Broadbent Springville (Lakeside Landing)" strongly). Same shape as the loan
    resolver so KG matching and Hypercore resolution behave consistently.
    """
    nq = _normalize(query)
    nc = _normalize(candidate_name)
    if not nq or not nc:
        return 0.0
    if nq == nc:
        return 1.0

    ratio = difflib.SequenceMatcher(None, nq, nc).ratio()

    qt, ct = _tokens(query), _tokens(candidate_name)
    if qt and ct:
        inter = len(qt & ct)
        union = len(qt | ct)
        jaccard = inter / union if union else 0.0
        subset_bonus = 1.0 if qt <= ct else (inter / len(qt) if qt else 0.0)
    else:
        jaccard = 0.0
        subset_bonus = 0.0

    containment = 0.0
    if nq in nc or nc in nq:
        shorter, longer = (nq, nc) if len(nq) <= len(nc) else (nc, nq)
        containment = len(shorter) / len(longer) if longer else 0.0

    score = (0.30 * ratio) + (0.30 * jaccard) + (0.25 * subset_bonus) + (0.15 * containment)

    # A clean subset (every query token appears in the candidate) is a strong signal: lift the
    # floor toward the fraction of the candidate the query covers.
    if qt and qt <= ct:
        coverage = len(qt) / len(ct) if ct else 0.0
        score = max(score, 0.80 + 0.20 * coverage)
    elif ct and ct <= qt:
        coverage_q = len(ct) / len(qt) if qt else 0.0
        score = max(score, 0.70 + 0.25 * coverage_q)

    return max(0.0, min(1.0, round(score, 4)))


# ---------------------------------------------------------------------------
# Value helpers
# ---------------------------------------------------------------------------

def _to_float(v: Any) -> Optional[float]:
    """Coerce a KG property/claim value to float, or None if not numeric.

    KG numbers arrive as ints, floats, or numeric strings ("38100000.000000", "$38,100,000").
    Booleans are NOT numbers here (a True must never become 1.0). Non-numeric -> None.
    """
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace("$", "").replace(",", "").replace("%", "")
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _first_present(props: dict, keys: tuple) -> tuple:
    """Return (field_name, float_value) for the first key in `keys` present + numeric in props,
    else (None, None). Never guesses — only reads declared keys."""
    for k in keys:
        if k in props:
            f = _to_float(props.get(k))
            if f is not None:
                return k, f
    return None, None


def _parse_props(cell: str) -> dict:
    """Parse the properties_json CSV cell into a dict. Malformed -> {} (never raises)."""
    if not cell:
        return {}
    try:
        obj = json.loads(cell)
        return obj if isinstance(obj, dict) else {}
    except (ValueError, TypeError):
        return {}


def _claim_fact_kind(node_id: str, canonical_name: str) -> Optional[str]:
    """Classify what a financial CLAIM is about -> 'appraised_value' | 'noi' | 'purchase_price'.

    Routes by the claim's node_id + canonical_name (the only place a CLAIM declares its subject
    matter — its normalized_value is a bare number). Returns None when the claim is about
    something we don't map (ownership %, interest rate, taxes, ...) so it is ignored, not guessed.
    """
    blob = f"{node_id} {canonical_name}".lower()
    if any(h in blob for h in _CLAIM_APPRAISED_HINTS):
        return "appraised_value"
    if any(h in blob for h in _CLAIM_NOI_HINTS):
        return "noi"
    if any(h in blob for h in _CLAIM_PURCHASE_HINTS):
        return "purchase_price"
    return None


# ---------------------------------------------------------------------------
# KG store (read-only)
# ---------------------------------------------------------------------------

class KGStore:
    """Read-only view over the OKOA knowledge-graph node CSV.

    Loads nodes.csv once (lazy, cached) and exposes a fuzzy loan->facts lookup. NEVER writes.
    `kg_dir` defaults to ~/okoa-labs/okoa_ops/knowledge-graph/ and is configurable for tests
    (point it at a fixture dir) and for relocated graphs.
    """

    def __init__(self, *, kg_dir: Optional[str] = None,
                 high_confidence: float = HIGH_CONFIDENCE,
                 ambiguity_gap: float = AMBIGUITY_GAP,
                 min_candidate_score: float = MIN_CANDIDATE_SCORE):
        self.kg_dir = kg_dir or os.environ.get("HCA_KG_DIR") or DEFAULT_KG_DIR
        self.nodes_path = os.path.join(self.kg_dir, NODES_FILENAME)
        self._high = float(high_confidence)
        self._gap = float(ambiguity_gap)
        self._min = float(min_candidate_score)
        self._nodes: Optional[list] = None          # cached parsed rows
        self._by_id: Optional[dict] = None           # node_id -> row (for subject resolution)

    # --- load (read-only, cached) ------------------------------------------
    def _load(self) -> None:
        if self._nodes is not None:
            return
        rows: list = []
        by_id: dict = {}
        if not os.path.isfile(self.nodes_path):
            self._nodes, self._by_id = rows, by_id
            return
        with open(self.nodes_path, "r", encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                nid = (r.get("node_id") or "").strip()
                if not nid:
                    continue
                row = {
                    "node_id": nid,
                    "canonical_name": r.get("canonical_name") or "",
                    "aliases": r.get("aliases") or "",
                    "node_type": (r.get("node_type") or "").strip().upper(),
                    "confidence": _to_float(r.get("confidence")),
                    "verification_status": r.get("verification_status") or "",
                    "props": _parse_props(r.get("properties_json") or ""),
                }
                rows.append(row)
                by_id[nid] = row
        self._nodes, self._by_id = rows, by_id

    def _alias_terms(self, row: dict) -> list:
        """All match terms for a node: canonical_name + pipe-separated aliases."""
        terms = [row["canonical_name"]]
        aliases = row.get("aliases") or ""
        terms.extend(a for a in aliases.split("|") if a.strip())
        return [t for t in terms if t]

    def _best_score(self, query: str, row: dict) -> float:
        return max((score_name(query, t) for t in self._alias_terms(row)), default=0.0)

    # --- candidate ranking -------------------------------------------------
    def rank_nodes(self, loan_name: str) -> list:
        """Rank value-bearing nodes by fuzzy match to `loan_name`.

        Returns a list of {node_id, node_type, canonical_name, score, confidence}, highest
        first, restricted to nodes that can carry valuation facts and score >= the floor.
        """
        self._load()
        scored = []
        for row in self._nodes:  # type: ignore[union-attr]
            if row["node_type"] not in VALUE_NODE_TYPES:
                continue
            s = self._best_score(loan_name, row)
            if s >= self._min:
                scored.append({"node_id": row["node_id"], "node_type": row["node_type"],
                               "canonical_name": row["canonical_name"], "score": s,
                               "confidence": row["confidence"], "_row": row})
        # Prefer score, then node-type authority (DEAL > PROPERTY > FIN_INSTR > CLAIM), then id.
        type_rank = {t: i for i, t in enumerate(VALUE_NODE_TYPES)}
        scored.sort(key=lambda c: (-c["score"], type_rank.get(c["node_type"], 99),
                                   c["node_id"]))
        return scored

    # --- the join ----------------------------------------------------------
    def lookup(self, loan_name: str) -> Optional[dict]:
        """Fuzzy-join a Hypercore loan name to its KG collateral facts.

        Returns a dict (see module docstring) on a CONFIDENT match, else None. The returned dict
        always carries `node_id` + `provenance` (the source file + node + field for the primary
        value) and the KG node's own `confidence`. Facts that are absent for the matched loan are
        simply omitted — the caller refuses rather than fabricating.
        """
        if not isinstance(loan_name, str) or not loan_name.strip():
            return None
        ranked = self.rank_nodes(loan_name)
        if not ranked:
            return None
        top = ranked[0]
        second = ranked[1] if len(ranked) > 1 else None
        # Confident == clears the high bar AND is not effectively tied with a DIFFERENT DEAL.
        # Two nodes for the SAME deal (e.g. the DEAL node + its collateral PROPERTY node, or a
        # CLAIM about it) routinely tie — that is NOT a real ambiguity; they describe one loan.
        # We only refuse-as-ambiguous when the runner-up is a genuinely different subject: it
        # shares NO distinctive token with the top match's name.
        close = False
        if second is not None and (top["score"] - second["score"]) < self._gap:
            shared = (_tokens(top["canonical_name"]) & _tokens(second["canonical_name"])
                      ) - _STOPWORD_TOKENS
            if not shared:
                close = True   # different name with nothing in common -> truly ambiguous
        if top["score"] < self._high or close:
            return None

        # Gather facts across the matched node AND its same-deal siblings (DEAL + its PROPERTY +
        # the financial CLAIMs that point at either), so a value living on a sibling node is found.
        return self._assemble_facts(loan_name, top, ranked)

    def _assemble_facts(self, loan_name: str, top: dict, ranked: list) -> dict:
        """Pull appraised_value / noi / purchase_price / ltv_latest / rate / date from the matched
        node and its same-deal sibling nodes + claims. Each fact records its own source node+field.
        """
        self._load()
        primary_row = top["_row"]
        primary_props = primary_row["props"]

        # The set of node_ids that belong to the same deal/property cluster as the match: the
        # match itself, plus any other ranked node whose name is (near-)identical, plus the
        # claims whose subject points at any of them.
        cluster_ids = {top["node_id"]}
        for c in ranked[1:]:
            if (c["score"] >= self._high
                    and _normalize(c["canonical_name"]) == _normalize(top["canonical_name"])):
                cluster_ids.add(c["node_id"])

        result: dict = {
            "node_id": top["node_id"],
            "canonical_name": top["canonical_name"],
            "node_type": top["node_type"],
            "match_score": top["score"],
            "confidence": top["confidence"],
            "verification_status": primary_row.get("verification_status"),
            "kg_file": self.nodes_path,
        }

        # --- direct facts off the primary node's properties_json -------------
        self._extract_direct(result, top["node_id"], primary_props)

        # --- direct facts off PROPERTY siblings (subject of the deal's claims, or co-ranked) ---
        # Resolve subject nodes referenced by financial claims that point at the cluster, AND any
        # high-scoring PROPERTY node sharing the deal name (e.g. lakeside-landing for broadbent).
        self._extract_from_property_siblings(result, top, ranked, cluster_ids)

        # --- CLAIM-based normalized facts (resolve via subject_node_id) ------
        self._extract_from_claims(result, cluster_ids, top)

        return result

    def _extract_direct(self, result: dict, node_id: str, props: dict) -> None:
        """Extract the direct facts from a single node's properties_json (no overwrite of a
        fact already set by a higher-priority source)."""
        for fact, keys in (("appraised_value", _APPRAISED_VALUE_KEYS),
                           ("noi", _NOI_KEYS),
                           ("purchase_price", _PURCHASE_PRICE_KEYS),
                           ("ltv_latest", _LTV_LATEST_KEYS),
                           ("interest_rate", _INTEREST_RATE_KEYS)):
            if fact in result:
                continue
            field, val = _first_present(props, keys)
            if field is not None:
                result[fact] = val
                result.setdefault("provenance", {})[fact] = {
                    "file": self.nodes_path, "node_id": node_id, "field": field}
        # appraisal_date is a string, handled separately (not a float).
        if "appraisal_date" not in result:
            for k in _APPRAISAL_DATE_KEYS:
                if isinstance(props.get(k), str) and props[k].strip():
                    result["appraisal_date"] = props[k].strip()
                    result.setdefault("provenance", {})["appraisal_date"] = {
                        "file": self.nodes_path, "node_id": node_id, "field": k}
                    break

    def _extract_from_property_siblings(self, result: dict, top: dict, ranked: list,
                                        cluster_ids: set) -> None:
        """Pull facts from PROPERTY (and other value) nodes that belong to the same deal.

        Two routes to a sibling: (1) a co-ranked node with the same/near name, (2) the subject
        node of a financial claim that points at the matched deal.
        """
        sibling_ids = set()
        for c in ranked:
            if c["node_id"] in cluster_ids:
                continue
            # Co-ranked, decent score, and shares a distinctive token with the match name.
            if c["score"] >= self._min:
                top_toks = _tokens(top["canonical_name"])
                c_toks = _tokens(c["canonical_name"])
                shared = top_toks & c_toks
                if shared and c["score"] >= self._high * 0.75:
                    sibling_ids.add(c["node_id"])
        # subject nodes of financial claims pointing at the cluster
        for row in self._nodes:  # type: ignore[union-attr]
            if row["node_type"] != "CLAIM":
                continue
            subj = row["props"].get("subject_node_id")
            if subj in cluster_ids:
                # the claim's subject is a sibling worth scanning (e.g. property:lakeside-landing)
                sibling_ids.add(subj)
        for sid in sibling_ids:
            sib = self._by_id.get(sid)  # type: ignore[union-attr]
            if sib is not None:
                self._extract_direct(result, sid, sib["props"])

    def _extract_from_claims(self, result: dict, cluster_ids: set, top: dict) -> None:
        """Resolve financial CLAIM nodes whose subject is in the cluster into normalized facts.

        Each financial claim carries ONE normalized_value; `_claim_fact_kind` classifies what it
        is about (appraised value / NOI / purchase price). Provenance points at the CLAIM node
        (its normalized_value) AND records the subject it resolves to.
        """
        self._load()
        for row in self._nodes:  # type: ignore[union-attr]
            if row["node_type"] != "CLAIM":
                continue
            props = row["props"]
            if props.get("claim_type") != "financial":
                continue
            subj = props.get("subject_node_id")
            # The claim must point at the matched cluster (or, if the match itself IS the claim's
            # subject by name, at a node sharing the deal name).
            if subj not in cluster_ids:
                continue
            kind = _claim_fact_kind(row["node_id"], row["canonical_name"])
            if kind is None or kind in result:
                continue
            val = _to_float(props.get("normalized_value"))
            if val is None:
                continue
            result[kind] = val
            result.setdefault("provenance", {})[kind] = {
                "file": self.nodes_path, "node_id": row["node_id"],
                "field": "normalized_value", "subject_node_id": subj}
            # carry the claim's own confidence if the primary node had none
            if result.get("confidence") is None and row.get("confidence") is not None:
                result["confidence"] = row["confidence"]


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

_DEFAULT_STORE: Optional[KGStore] = None


def default_store() -> KGStore:
    global _DEFAULT_STORE
    if _DEFAULT_STORE is None:
        _DEFAULT_STORE = KGStore()
    return _DEFAULT_STORE


def kg_lookup(loan_name: str, *, kg_dir: Optional[str] = None) -> Optional[dict]:
    """One-shot fuzzy join of a Hypercore loan name to its KG collateral facts.

    Returns the facts dict on a confident match (always carrying node_id + provenance), else
    None. Read-only; never fabricates. Pass `kg_dir` to point at a fixture/relocated graph.
    """
    store = KGStore(kg_dir=kg_dir) if kg_dir is not None else default_store()
    return store.lookup(loan_name)


# ---------------------------------------------------------------------------
# CLI — `--loan "<name>"` prints the joined facts; `--rank "<name>"` shows candidates.
# Collateral VALUES + node_ids are portfolio reference data (not borrower PII), safe to print.
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="acos-hypercore-ask KG join — collateral value / NOI for a loan name.")
    parser.add_argument("--loan", dest="loan", metavar="LOAN_NAME",
                        help="loan name (or partial) to join against the KG")
    parser.add_argument("--rank", dest="rank", metavar="LOAN_NAME",
                        help="show ranked KG node candidates for a loan name (diagnostic)")
    parser.add_argument("--kg-dir", dest="kg_dir", default=None,
                        help=f"KG directory (default {DEFAULT_KG_DIR})")
    args = parser.parse_args(argv)
    store = KGStore(kg_dir=args.kg_dir)
    if args.rank:
        ranked = [{k: v for k, v in c.items() if k != "_row"} for c in store.rank_nodes(args.rank)]
        print(json.dumps(ranked, indent=2, default=str))
        return 0
    if args.loan:
        res = store.lookup(args.loan)
        print(json.dumps(res, indent=2, default=str))
        return 0 if res else 1
    parser.error('supply --loan "<name>" or --rank "<name>"')
    return 2


if __name__ == "__main__":
    sys.exit(main())
