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


def _learned():
    return _load("hca_learned", "hca-learned.py")


# A learned canonical metric word -> the figure that answers it (loan-level and portfolio-level).
_METRIC_TO_FUNDING = {
    "outstanding": "funding_outstanding", "receivable": "funding_receivable",
    "commitment": "funding_commitment", "participation": "funding_participation",
}
_METRIC_TO_PORTFOLIO = {
    "outstanding": "portfolio_outstanding", "receivable": "portfolio_receivable",
    "commitment": "portfolio_commitment",
}


# Funding metric keyword -> the funding figure that answers it. Ordered most-specific first, so
# the multi-word "per diem" is recognized before any single-word metric in the same question.
_FUNDING_FIGURE_BY_KEYWORD = (
    (("per diem", "perdiem", "per-diem", "daily interest"), "per_diem_interest"),
    (("outstanding",), "funding_outstanding"),
    (("commitment", "committed"), "funding_commitment"),
    (("participation", "participating", "participates"), "funding_participation"),
    (("receivable", "receivables", "owed"), "funding_receivable"),
)

# Words removed when isolating the entity names in a funding question (the metric words + 'amount'
# / 'balance' / 'contributed' + the per-diem terms). The remaining generic filler + tranche words +
# dates are stripped by reusing hca-deliver's helpers so the two paths can never drift. The
# per-diem terms (per[ -]diem, daily, interest) are stripped here so a question like "per diem
# interest for XL for Lux II" does not carry "per/diem/interest" into entity resolution (which the
# 2026-06-25 handoff flagged as breaking the name match).
_FUNDING_METRIC_RE = re.compile(
    r"(?i)\b(per[\s-]*diem|daily|interest|outstanding|commitment|committed|participation|"
    r"participating|participates|receivable|receivables|owed|amount|balance|contributed|due)\b")


def _funding_figure_for(q_lower: str) -> Optional[str]:
    for kws, fig in _FUNDING_FIGURE_BY_KEYWORD:
        if any(k in q_lower for k in kws):
            return fig
    return None


# Portfolio (fundingEntity-level, ACROSS ALL the investor's loans) figures by keyword — used when
# an investor resolves but NO loan is named ("XL's total receivable across the portfolio").
_PORTFOLIO_FIGURE_BY_KEYWORD = (
    (("outstanding",), "portfolio_outstanding"),
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


def _name_tokens(question: str, *, extra_strip=None) -> list:
    """The candidate ENTITY-NAME tokens in a question: drop dates, the funding metric words, and
    the generic figure filler (reused from hca-deliver so the vocabularies cannot drift).
    `extra_strip` is a list of LEARNED alias phrases to also remove (so a learned metric phrase
    like "amount due" doesn't pollute entity resolution, the same way the built-in metric words
    are stripped)."""
    d = _deliver()
    work = d._strip_date_phrases(question)
    work = re.sub(r"(?i)'s\b", " ", work)        # drop possessive 's  ("XL's" -> "XL")
    for phrase in (extra_strip or []):
        if phrase:
            work = re.sub(re.escape(phrase), " ", work, flags=re.IGNORECASE)
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


def _as_resolved(le: dict) -> dict:
    """Wrap a learned {entity_type, id, name} into a resolver-shaped RESOLVED result so the
    existing splitter logic consumes it transparently. The id is what routes; the live figure
    fetch downstream is the integrity gate (a stale id REFUSES — it can never fabricate)."""
    m = {"id": le["id"], "name": le.get("name"), "score": 1.0}
    return {"query": le.get("name"), "match": m, "resolved": True, "ambiguous": False,
            "candidates": [m], "echo": "learned", "reason": "learned routing"}


def _with_learned_loan(resolve_loan, learned):
    def _r(name):
        le = learned.entity_for(name)
        if le and le.get("entity_type") == "loan":
            return _as_resolved(le)
        return resolve_loan(name)
    return _r


def _with_learned_entity(resolve_entity, learned):
    def _r(name, entity_type):
        le = learned.entity_for(name)
        if le and le.get("entity_type") == entity_type:
            return _as_resolved(le)
        return resolve_entity(name, entity_type)
    return _r


def _unmapped_metric_phrase(q_lower: str) -> Optional[str]:
    """The contiguous metric-ish span in a question that has NO built-in figure mapping — the
    phrase we offer to LEARN. e.g. 'amount due' in 'what is the amount due for XL?'. Returns the
    LONGEST merged run of metric words so we learn a specific phrase, not a generic single word."""
    spans = [mt.span() for mt in _FUNDING_METRIC_RE.finditer(q_lower)]
    if not spans:
        return None
    merged = [list(spans[0])]
    for s, e in spans[1:]:
        if q_lower[merged[-1][1]:s].strip() == "":
            merged[-1][1] = e
        else:
            merged.append([s, e])
    best = max(merged, key=lambda se: se[1] - se[0])
    return q_lower[best[0]:best[1]].strip()


_METRIC_CHOICES = [
    ("outstanding", "Outstanding — amount currently owed on the position"),
    ("receivable", "Receivable — total amount receivable"),
    ("commitment", "Commitment — the committed amount"),
    ("participation", "Participation — participation amount / percentage"),
]


def _metric_selection_envelope(question, phrase, loan_m, investor_r) -> dict:
    """NEEDS_SELECTION offering the funding metric choices for a funding-shaped question whose
    metric we couldn't map. The user's pick is LEARNED as (phrase -> metric)."""
    cands = [{"label": label, "record": {"kind": "metric_alias", "phrase": phrase, "metric": m}}
             for m, label in _METRIC_CHOICES]
    inv = (investor_r or {}).get("match") if isinstance(investor_r, dict) else None
    return {"state": "NEEDS_SELECTION", "tier": "ask", "question": question, "answer": None,
            "selection": {"kind": "metric",
                          "prompt": "Which figure do you mean by \"%s\"?" % phrase,
                          "phrase": phrase, "candidates": cands},
            "meta": {"resolution": {"loan": loan_m, "investor": inv, "unmapped_phrase": phrase}}}


def _entity_selection_envelope(question, investor_r, loan_m) -> dict:
    """NEEDS_SELECTION offering the ambiguous entity candidates. The user's pick is LEARNED as
    (name -> entity id), so the same name resolves directly next time."""
    name = (investor_r or {}).get("query") or ""
    cands = [{"label": "%s (fundingEntity %s)" % (c.get("name"), c.get("id")),
              "record": {"kind": "entity_resolution", "name": name, "entity_type": "fundingEntity",
                         "id": c.get("id"), "label": c.get("name")}}
             for c in (investor_r or {}).get("candidates", [])]
    return {"state": "NEEDS_SELECTION", "tier": "funding", "question": question, "answer": None,
            "selection": {"kind": "entity",
                          "prompt": "Which \"%s\" did you mean?" % name,
                          "name": name, "candidates": cands},
            "meta": {"resolution": {"loan": loan_m, "investor_query": name}}}


def record_choice(record, *, learned=None) -> dict:
    """Persist a confirmed NEEDS_SELECTION candidate's `record`. Routing only — there is no path
    here that stores a value. Returns the store result."""
    store = learned if learned is not None else _learned().default_store()
    kind = (record or {}).get("kind")
    if kind == "metric_alias":
        return store.record_metric_alias(record.get("phrase", ""), record.get("metric", ""))
    if kind == "entity_resolution":
        return store.record_entity_resolution(
            record.get("name", ""), record.get("entity_type", ""),
            record.get("id", ""), record.get("label"))
    return {"ok": False, "reason": "unknown record kind %r" % kind}


def smart_ask(question, *, deliver_ask=None, resolve_loan=None, resolve_entity=None,
              run_funding=None, run_portfolio=None, explorer=None, learned=None) -> dict:
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

    # LEARNED ROUTING (only when a store is provided; None preserves the base deterministic
    # behavior the core tests assert). Wrap the resolvers so a CONFIRMED name->entity is applied
    # transparently everywhere downstream. NEVER applies a learned VALUE — routing only.
    if learned is not None:
        resolve_loan = _with_learned_loan(resolve_loan, learned)
        resolve_entity = _with_learned_entity(resolve_entity, learned)

    # 1) DETERMINISTIC SPINE — unchanged. A clean delivery wins outright.
    det = deliver_ask(question)
    if isinstance(det, dict) and det.get("state") == "DELIVERED":
        det.setdefault("tier", "deterministic")
        return det

    q_lower = question.lower()

    # 2) FUNDING / INVESTOR interpretation. Metric from built-in keywords first; if none, a
    # LEARNED alias (e.g. "amount due" -> outstanding) can supply it.
    fig = _funding_figure_for(q_lower)
    lm = None
    strip_phrase = None
    if not fig and learned is not None:
        lm = learned.metric_for(q_lower)
        if lm:
            fig = _METRIC_TO_FUNDING.get(lm)
            strip_phrase = learned.matched_alias_phrase(q_lower)
    if fig:
        tokens = _name_tokens(question, extra_strip=[strip_phrase] if strip_phrase else None)
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
        pfig = _portfolio_figure_for(q_lower) or (_METRIC_TO_PORTFOLIO.get(lm) if lm else None)
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
        # one side resolved but the other is ambiguous/missing.
        inv_cands = (investor_r or {}).get("candidates", []) if isinstance(investor_r, dict) else []
        if learned is not None and inv_cands:
            # surface the ambiguous investor as a SELECTION to learn from (not a dead-end refusal)
            return _entity_selection_envelope(question, investor_r, loan_m)
        if loan_m or inv_cands:
            return {"state": "REFUSED", "tier": "funding", "answer": None,
                    "refusals": [{"reason_code": "FUNDING_DISAMBIGUATION",
                                  "reason": "could not uniquely resolve both the investor and the "
                                            "loan for this funding question",
                                  "loan": loan_m, "investor_candidates": inv_cands}]}

    # UNMAPPED METRIC: a funding-shaped question (resolves an investor, +/- a loan) whose metric
    # we don't recognize -> offer the metric choices as a SELECTION to learn from, instead of
    # silently dropping to the best-effort explorer.
    if not fig and learned is not None:
        phrase = _unmapped_metric_phrase(q_lower)
        if phrase:
            tokens = _name_tokens(question)
            loan_m, investor_r = _split_loan_investor(
                tokens, resolve_loan=resolve_loan, resolve_entity=resolve_entity)
            inv_ok = isinstance(investor_r, dict) and investor_r.get("resolved")
            if inv_ok or loan_m:
                return _metric_selection_envelope(question, phrase, loan_m, investor_r)

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
    parser.add_argument("--record", dest="record", metavar="JSON",
                        help="persist a confirmed NEEDS_SELECTION choice (a candidate's 'record' "
                             "object), then re-run --ask if also given")
    args = parser.parse_args(argv)
    store = _learned().default_store()
    if args.record:
        try:
            rec = json.loads(args.record)
        except ValueError as e:
            parser.error("--record must be JSON: %s" % e)
        res = record_choice(rec, learned=store)
        if not args.ask:
            print(json.dumps({"recorded": res}, indent=2, default=str))
            return 0 if res.get("ok") else 1
    if not args.ask:
        parser.error("a question is required: --ask \"what is XL's outstanding on Beehive?\"")
    env = smart_ask(args.ask, learned=store)
    print(json.dumps(env, indent=2, default=str))
    state = env.get("state")
    return 0 if state in ("DELIVERED", "EXPLORED", "NEEDS_SELECTION") else 1


if __name__ == "__main__":
    sys.exit(main())
