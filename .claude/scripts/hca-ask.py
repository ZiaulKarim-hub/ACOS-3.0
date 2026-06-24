#!/usr/bin/env python3
"""hca-ask.py — the SMART ask orchestrator for acos-hypercore-ask.

The deterministic spine (hca-deliver.ask) answers the questions it has a BUILT figure for, and
REFUSES everything else. This orchestrator wraps it with two additional layers so a question can
be answered WITHOUT the user pointing the skill at the right entity/figure:

  1. DETERMINISTIC SPINE first (unchanged) — if it DELIVERS, return it verbatim. This preserves
     every existing trust guarantee for the questions the skill already handles.
  2. FUNDING / INVESTOR interpretation — if the question names a funding metric (outstanding /
     commitment / participation / receivable) AND splits into a resolvable INVESTOR + LOAN, route
     to the reconciled, provenance-bound funding figure (hca-funding). e.g. "XL's outstanding on
     the Beehive loan" -> resolve "Beehive" -> loan, "XL" -> fundingEntity -> funding_outstanding.
  3. CONFIDENCE-GRADED EXPLORER fallback — when nothing above maps, resolve the entity the
     question names and let hca-explorer introspect its fields, fetch the matching ones LIVE, and
     return them with a confidence grade + provenance, clearly marked best-effort. This is the
     "find values and show them with varying degrees of confidence" layer.

TRUST INVARIANTS (unchanged): READ-ONLY; never fabricate (funding figures reconcile + bind or
REFUSE; the explorer returns only fetched-real values, graded on field-match certainty, never on
value authenticity); Python 3 stdlib only; secrets via env/Doppler.

CLI:  doppler run ... -- python3 hca-ask.py --ask "what is XL's outstanding on the Beehive loan?"
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
from typing import Optional


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


def _deliver():
    return _load("hca_deliver", "hca-deliver.py")


def _resolve():
    return _load("hca_resolve", "hca-resolve.py")


def _entities():
    return _load("hca_entities", "hca-entities.py")


def _funding():
    return _load("hca_funding", "hca-funding.py")


def _explorer():
    return _load("hca_explorer", "hca-explorer.py")


# Funding metric keyword -> the funding figure that answers it. Ordered most-specific first.
_FUNDING_FIGURE_BY_KEYWORD = (
    (("outstanding",), "funding_outstanding"),
    (("commitment", "committed"), "funding_commitment"),
    (("participation", "participating", "participates"), "funding_participation"),
    (("receivable", "receivables", "owed"), "funding_receivable"),
)

# Words removed when isolating the entity names in a funding question (the metric words + 'amount'
# / 'balance' / 'contributed'). The remaining generic filler + tranche words + dates are stripped
# by reusing hca-deliver's helpers so the two paths can never drift.
_FUNDING_METRIC_RE = re.compile(
    r"(?i)\b(outstanding|commitment|committed|participation|participating|participates|"
    r"receivable|receivables|owed|amount|balance|contributed|due)\b")


def _funding_figure_for(q_lower: str) -> Optional[str]:
    for kws, fig in _FUNDING_FIGURE_BY_KEYWORD:
        if any(k in q_lower for k in kws):
            return fig
    return None


# Portfolio (fundingEntity-level, ACROSS ALL the investor's loans) figures by keyword — used when
# an investor resolves but NO loan is named ("XL's total receivable across the portfolio").
_PORTFOLIO_FIGURE_BY_KEYWORD = (
    (("receivable", "receivables"), "portfolio_receivable"),
    (("commitment", "committed"), "portfolio_commitment"),
    (("disbursement", "disbursed", "disbursements"), "portfolio_disbursement"),
    (("contributed", "contribution"), "portfolio_contributed"),
    (("active loans", "number of loans", "loan count"), "portfolio_active_loans"),
)


def _portfolio_figure_for(q_lower: str) -> Optional[str]:
    for kws, fig in _PORTFOLIO_FIGURE_BY_KEYWORD:
        if any(k in q_lower for k in kws):
            return fig
    return None


def _name_tokens(question: str) -> list:
    """The candidate ENTITY-NAME tokens in a question: drop dates, the funding metric words, and
    the generic figure filler (reused from hca-deliver so the vocabularies cannot drift)."""
    d = _deliver()
    work = d._strip_date_phrases(question)
    work = re.sub(r"(?i)'s\b", " ", work)        # drop possessive 's  ("XL's" -> "XL")
    work = _FUNDING_METRIC_RE.sub(" ", work)
    work = d._FIGURE_FILLER_RE.sub(" ", work)
    work = re.sub(r"[?.,:;!%'\"]", " ", work)
    return [t for t in work.split() if t]


def _split_loan_investor(tokens, *, resolve_loan, resolve_entity):
    """Split entity-name tokens into a (loan_match, investor_match) by trying the tokens as a LOAN
    (the full string, then each drop-one-token variant) and resolving the LEFTOVER tokens as a
    fundingEntity. Returns (loan_match|None, investor_result|None). Never invents — both come from
    real resolver rows; ambiguity is carried through (not silently picked)."""
    if not tokens:
        return None, None
    variants = [tokens]
    if len(tokens) > 1:
        variants += [tokens[:i] + tokens[i + 1:] for i in range(len(tokens))]
    best = None  # {"match":..., "used":[...]}
    for v in variants:
        if not v:
            continue
        r = resolve_loan(" ".join(v))
        if r.get("resolved"):
            sc = r["match"]["score"]
            if best is None or sc > best["match"]["score"]:
                best = {"match": r["match"], "used": v}
    if best is None:
        return None, None
    loan_name_toks = set(re.findall(r"[a-z0-9]+", str(best["match"].get("name", "")).lower()))
    leftover = [t for t in tokens if t.lower() not in loan_name_toks]
    investor = resolve_entity(" ".join(leftover), "fundingEntity") if leftover else None
    return best["match"], investor


def _resolve_any_entity(tokens, *, resolve_loan, resolve_entity):
    """Find the entity a question names, trying the full token string then each drop-one-token
    variant (so 'irr XL' still resolves 'XL' once the metric word is dropped), across funding
    entities, clients, then loans. Returns (entity_type, match) or (None, None). Never invents."""
    if not tokens:
        return None, None
    variants = [tokens]
    if len(tokens) > 1:
        variants += [tokens[:i] + tokens[i + 1:] for i in range(len(tokens))]
    for v in variants:
        if not v:
            continue
        nm = " ".join(v)
        for etype in ("fundingEntity", "client"):
            r = resolve_entity(nm, etype)
            if r.get("resolved"):
                return etype, r["match"]
        rl = resolve_loan(nm)
        if rl.get("resolved"):
            return "loan", rl["match"]
    return None, None


def _explorer_envelope(explore_result: dict, *, entity, question: str) -> dict:
    """Wrap an hca-explorer result in an envelope-shaped dict so the caller treats it uniformly.
    Clearly marked best-effort (tier='explorer') — these are confidence-graded, not verified."""
    results = explore_result.get("results") or []
    return {
        "state": "EXPLORED" if results else "NO_MATCH",
        "tier": "explorer",
        "answer": None,
        "question": question,
        "entity": entity,
        "results": results,
        "notes": explore_result.get("notes") or [],
        "meta": {"best_effort": True, "skill": "acos-hypercore-ask",
                 "graphql_type": explore_result.get("graphql_type")},
    }


def smart_ask(question, *, deliver_ask=None, resolve_loan=None, resolve_entity=None,
              run_funding=None, run_portfolio=None, explorer=None) -> dict:
    """Answer a question via: deterministic spine -> funding interpretation -> explorer fallback.

    All collaborators are injectable for testing; live defaults wire to the real modules.
    """
    if not isinstance(question, str) or not question.strip():
        return {"state": "REFUSED", "tier": "ask", "answer": None,
                "refusals": [{"reason_code": "EMPTY_QUESTION", "reason": "empty question"}]}

    deliver_ask = deliver_ask or (lambda q: _deliver().ask(q))
    resolve_loan = resolve_loan or (lambda n: _resolve().resolve_loan(n))
    resolve_entity = resolve_entity or (lambda n, t: _entities().resolve_entity(n, t))
    run_funding = run_funding or (
        lambda fig, loan_id, fe_id: _funding().run_funding_figure(
            fig, loan_id=loan_id, funding_entity_id=fe_id))
    run_portfolio = run_portfolio or (
        lambda fig, fe_id, name: _funding().run_portfolio_figure(
            fig, funding_entity_id=fe_id, name_hint=name))
    if explorer is None:
        explorer = _explorer().EntityExplorer()

    # 1) DETERMINISTIC SPINE — unchanged. A clean delivery wins outright.
    det = deliver_ask(question)
    if isinstance(det, dict) and det.get("state") == "DELIVERED":
        det.setdefault("tier", "deterministic")
        return det

    q_lower = question.lower()

    # 2) FUNDING / INVESTOR interpretation.
    fig = _funding_figure_for(q_lower)
    if fig:
        tokens = _name_tokens(question)
        loan_m, investor_r = _split_loan_investor(
            tokens, resolve_loan=resolve_loan, resolve_entity=resolve_entity)
        if loan_m and isinstance(investor_r, dict) and investor_r.get("resolved"):
            inv = investor_r["match"]
            env = run_funding(fig, loan_m["id"], inv["id"])
            if isinstance(env, dict):
                env.setdefault("tier", "funding")
                meta = env.setdefault("meta", {})
                meta["resolution"] = {
                    "loan": {"id": loan_m["id"], "name": loan_m.get("name")},
                    "investor": {"id": inv["id"], "name": inv.get("name")},
                    "figure": fig}
                return env
        # PORTFOLIO interpretation: a funding metric + an investor that resolves, but NO loan ->
        # the fundingEntity-level (across-all-loans) reconciled/verified figure.
        pfig = _portfolio_figure_for(q_lower)
        if pfig and not loan_m:
            etype, m = _resolve_any_entity(
                tokens, resolve_loan=resolve_loan, resolve_entity=resolve_entity)
            if etype == "fundingEntity" and m:
                penv = run_portfolio(pfig, m["id"], m.get("name"))
                if isinstance(penv, dict) and penv.get("state") == "DELIVERED":
                    penv.setdefault("tier", "portfolio")
                    penv.setdefault("meta", {})["resolution"] = {
                        "investor": {"id": m["id"], "name": m.get("name")}, "figure": pfig}
                    return penv
        # one side resolved but the other is ambiguous/missing -> surface for disambiguation
        if loan_m or (isinstance(investor_r, dict) and investor_r.get("candidates")):
            return {"state": "REFUSED", "tier": "funding", "answer": None,
                    "refusals": [{"reason_code": "FUNDING_DISAMBIGUATION",
                                  "reason": "could not uniquely resolve both the investor and the "
                                            "loan for this funding question",
                                  "loan": loan_m,
                                  "investor_candidates": (investor_r or {}).get("candidates", [])}]}

    # 3) CONFIDENCE-GRADED EXPLORER fallback.
    etype, m = _resolve_any_entity(
        _name_tokens(question), resolve_loan=resolve_loan, resolve_entity=resolve_entity)
    if m:
        entity = {"entity_type": etype, "id": m["id"], "name": m.get("name")}
        ex = explorer.explore_question(question, entity)
        if (ex or {}).get("results"):
            return _explorer_envelope(ex, entity=entity, question=question)

    # 4) nothing better than the deterministic refusal.
    if isinstance(det, dict):
        det.setdefault("tier", "deterministic")
    return det


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Smart ask: deterministic -> funding -> explorer")
    parser.add_argument("--ask", dest="ask", metavar="QUESTION", help="the question to answer")
    args = parser.parse_args(argv)
    if not args.ask:
        parser.error("a question is required: --ask \"what is XL's outstanding on Beehive?\"")
    env = smart_ask(args.ask)
    print(json.dumps(env, indent=2, default=str))
    state = env.get("state")
    return 0 if state in ("DELIVERED", "EXPLORED") else 1


if __name__ == "__main__":
    sys.exit(main())
