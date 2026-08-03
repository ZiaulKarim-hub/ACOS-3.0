#!/usr/bin/env python3
"""
orchestrate.py — the end-to-end pipeline driver (PLAN.md §3, Phases 2-7).

Runs each fact through: de-circularize -> grade -> fuse -> falsification gate ->
conflict resolution -> write to the single-writer ledger (promoting through the legal
state machine) -> coverage gate -> render -> ACOS mirror.

Model-dependent work (eliciting atomic claims, ACH, the independent different-family
refuter) is performed UPSTREAM and passed in as structured `fact` data, so the whole
pipeline is deterministic and testable offline. In live use, an orchestrating skill
fills the same `fact` structure from Task()-spawned agents.

Stdlib only.
"""

import os

import axiom_ledger as al
import decircularize as dc
import grade_fuse as gf
import falsify as fz
import resolve as rs
import coverage as cov
import mirror as mir
import checklist as chk
import volatility as vol


_CHECKLIST_CACHE = None
_VCFG_CACHE = None


def _checklist():
    """Load the boolean confidence checklist once per process (cached)."""
    global _CHECKLIST_CACHE
    if _CHECKLIST_CACHE is None:
        _CHECKLIST_CACHE = chk.load_checklist()
    return _CHECKLIST_CACHE


def _vcfg():
    """Load the volatility/recency config once per process (cached)."""
    global _VCFG_CACHE
    if _VCFG_CACHE is None:
        _VCFG_CACHE = vol.load_volatility()
    return _VCFG_CACHE


def _provenance(candidates, representatives):
    """Build the ledger provenance list from the post-de-circularization representatives."""
    by_src = {}
    for c in candidates:
        s = c["source"]
        by_src[s["id"]] = s
    prov = []
    for sid in representatives:
        s = by_src.get(sid, {"id": sid})
        entry = {
            "source": s.get("origin") or s.get("id"),
            "locator": s.get("locator", ""),
            "surfaced_by": s.get("id"),
            "family": s.get("family", ""),
        }
        if s.get("as_of"):                 # valid-time date, recorded for recency work
            entry["as_of"] = s.get("as_of")
        prov.append(entry)
    return prov


def _write(ledger, record, now):
    """Single-writer append. Returns (ok, error) — never raises past the caller."""
    try:
        al.append_claim(ledger, record, now=now)
        return True, None
    except al.LedgerError as exc:
        return False, exc


def process_fact(ledger, fact, settled_path, now, today="1970-01-01", vcfg=None):
    """Run one fact through stages 2-6 and write its claim version(s). Returns a result.

    `today` is the run's reference date (ISO 'YYYY-MM-DD') for the recency/freshness
    computation; `vcfg` is the volatility config (defaults to the cached load)."""
    fid = fact["fact_id"]
    candidates = fact.get("candidates", [])
    sources = [c["source"] for c in candidates]
    claim_type = fact.get("claim_type", "categorical")

    # Stage 2 — de-circularize.
    decirc = dc.collapse(sources)
    indep = decirc["independent_sources"]
    families = decirc["families"]

    # Stage 2.5 — recency: classify volatility + compute freshness of the INDEPENDENT
    # sources. Inert by construction for durable claims and for low-confidence
    # (unclassifiable) claims — so pre-recency fixtures are unaffected.
    vcfg = vcfg or _vcfg()
    vclass = fact.get("volatility")
    if vclass in (None, ""):
        vinfo = vol.classify(fact["statement"], domain=fact.get("domain"),
                             judge_label=fact.get("volatility_judge"), cfg=vcfg)
        vclass, vconf = vinfo["volatility"], vinfo["confidence"]
    else:
        vconf = fact.get("volatility_confidence", "high")   # a fact-declared class is trusted
    by_src = {c["source"]["id"]: c["source"] for c in candidates}
    rep_dates = [by_src.get(sid, {}).get("as_of") for sid in decirc["representatives"]]
    fresh = vol.compute_freshness(vclass, rep_dates, today, cfg=vcfg, confidence=vconf)

    # Stage 3 — grade + fuse.
    g = fact.get("grading", {})
    grade = gf.grade_claim(indep, families,
                           has_primary_citation=g.get("has_primary_citation", False),
                           downgrades=g.get("downgrades"), upgrades=g.get("upgrades"),
                           volatility=vclass, freshness=fresh)
    fused = gf.fuse([{"value": c["value"], "source_id": c["source"]["id"]} for c in candidates],
                    claim_type=claim_type, weights=fact.get("weights"))

    # Stage 5 (peek) — is there a genuine conflict to resolve? For a NON-DURABLE
    # conflict, guarded supersession is consulted before the accumulation rungs.
    conflict = None
    if fact.get("conflict"):
        conflict = rs.resolve_conflict(fact["conflict"], polarity=fact.get("ladder_polarity", "quorum"),
                                       volatility=vclass)

    # Stage 4 — falsification gate.
    gate = fz.run_gate(
        {"falsifiable": fact.get("falsifiable", True),
         "independent_sources": indep,
         "flags": fact.get("flags", {})},
        refuter=fact.get("refuter"),
        settled_path=settled_path,
    )

    # Stage 4.5 — the boolean confidence checklist (Point-1 improvement, 2026-07).
    # Engaged ONLY when the fact carries semantic judge answers; otherwise the
    # legacy grade tier is used (keeps the pre-checklist fixtures/tests unchanged).
    # The gate still owns the falsification field + disconfirmers; the checklist
    # owns the confidence TIER and its own veto-nullify.
    verdict = None
    if fact.get("checklist_answers") is not None:
        cl = fact.get("_checklist") or _checklist()
        ctx = chk.build_context(
            independent_sources=indep,
            distinct_families=len(families),
            has_primary_citation=g.get("has_primary_citation", False),
            divergence=fused["divergence"],
            semantic_answers=fact.get("checklist_answers"),
            superseded=fact.get("superseded", False),
            freshness_ok=fresh["freshness_ok"],   # now COMPUTED from volatility, not hand-set
        )
        ctx["domain"] = fact.get("domain")
        verdict = chk.evaluate(cl, ctx)

    prov = _provenance(candidates, decirc["representatives"])
    basis = {"independent_sources": indep, "distinct_families": len(families)}
    covers = fact.get("covers") or ([fact["sub_question"]] if fact.get("sub_question") else [])
    base = {
        "id": fid, "statement": fact["statement"], "claim_type": claim_type,
        "value": fused["fused_value"], "provenance": prov, "confidence_basis": basis,
        "covers": covers, "depends_on": fact.get("depends_on", []),
        # Recency (bitemporal + volatility) — carried on every claim version so the
        # renderer can surface staleness and audits can see WHY a tier was capped.
        "volatility": vclass, "observed_at": today,
        "recency": {"stale": fresh["stale"], "newest_as_of": fresh["newest_as_of"],
                    "window_days": fresh["window_days"], "gate_applies": fresh["gate_applies"]},
    }

    # --- decide outcome ------------------------------------------------------
    result = {"fact_id": fid, "decirc": decirc, "grade": grade, "fused": fused,
              "gate": gate, "conflict": conflict, "checklist": verdict,
              "volatility": vclass, "freshness": fresh}

    # always create the CONJECTURE first (legal create).
    _write(ledger, {**base, "state": "CONJECTURE", "confidence": "unverified",
                    "gates": {"falsification": "pending"}}, now)

    checklist_nullified = bool(verdict and verdict["nullified"])
    if gate["disposition"] == "nullify" or checklist_nullified:
        nullified_by = list(gate["hard"])
        if checklist_nullified:
            nullified_by += ["veto:" + r["id"] for r in verdict["veto_results"]
                             if r["answer"] is not True]
        _write(ledger, {**base, "state": "CONJECTURE", "confidence": "unverified",
                        "gates": {"falsification": "failed"},
                        "disconfirmers": gate["new_disconfirmers"],
                        "nullified_by": nullified_by}, now)
        result["final_state"] = "CONJECTURE(quarantined)"
        return result

    if conflict and conflict["status"] in ("unresolved", "vetoed", "keep_all"):
        alts = [{"statement": str(a.get("value", a.get("statement"))),
                 "why_not_adopted": conflict["reason"]} for a in (conflict.get("alternatives") or [])]
        _write(ledger, {**base, "state": "CONTESTED", "confidence": "unverified",
                        "alternatives": alts, "gates": {"falsification": gate["gate_state"]}}, now)
        result["final_state"] = "CONTESTED"
        return result

    # keep / downgrade -> promote through the legal ladder.
    # In checklist mode the checklist tier is authoritative (it already encodes
    # the refuter/conflict-of-interest/etc. as questions); don't double-apply the
    # gate downgrade. In legacy mode, the gate downgrade still lowers the tier.
    if verdict is not None:
        conf = verdict["tier"]
        # Recency cap in CHECKLIST mode (F4 gap fix): losing only N5-NOT-STALE
        # leaves 9/10 = 90%, which still meets verified_min — so the checklist
        # percentage alone can NEVER block 'verified' for a stale claim. Mechanism
        # (f) therefore applies here too: a confidently non-durable claim with no
        # RECENT independent source caps at 'probable' (cap, never nullify).
        if conf == "verified" and vclass not in (None, "durable") \
                and fresh["gate_applies"] and not fresh["recent_independent"]:
            conf = "probable"
            result["recency_capped"] = True
    else:
        conf = grade["confidence"]
        if gate["disposition"] == "downgrade":
            conf = fz.downgrade_tier(conf)

    if conf == "unverified":
        result["final_state"] = "CONJECTURE"
        return result

    # promote to CORROBORATED (gate passed).
    ok, err = _write(ledger, {**base, "state": "CORROBORATED", "confidence": "probable",
                              "gates": {"falsification": "passed"},
                              "disconfirmers": gate["new_disconfirmers"]}, now)
    if not ok:
        result["final_state"] = "CONJECTURE"
        result["write_error"] = str(err)
        return result

    if conf == "verified":
        ok, err = _write(ledger, {**base, "state": "ESTABLISHED", "confidence": "verified",
                                  "gates": {"falsification": "passed"},
                                  "disconfirmers": gate["new_disconfirmers"]}, now)
        if ok:
            result["final_state"] = "ESTABLISHED"
        else:
            # e.g. dependency integrity refused establishment — stays corroborated.
            result["final_state"] = "CORROBORATED"
            result["establish_refused"] = str(err)
        return result

    result["final_state"] = "CORROBORATED"
    return result


def run(session_dir, question, sub_questions, facts, now, repo_root=".", date_str="1970-01-01", session="dev"):
    """Drive the full pipeline. Writes claims.jsonl + source-of-truth.md, runs the
    coverage gate, mirrors the run. Returns a summary dict."""
    os.makedirs(session_dir, exist_ok=True)
    ledger = os.path.join(session_dir, "claims.jsonl")
    settled_path = os.path.join(session_dir, "settled-objections.jsonl")

    # `date_str` (the run date) is the reference "today" for the freshness computation.
    vcfg = _vcfg()
    per_fact = [process_fact(ledger, f, settled_path, now, today=date_str, vcfg=vcfg) for f in facts]

    records = al.read_ledger(ledger)
    coverage = cov.coverage_gate(sub_questions, records)
    md = al.render_markdown(records, question=question)
    with open(os.path.join(session_dir, "source-of-truth.md"), "w", encoding="utf-8") as fh:
        fh.write(md + "\n")

    states = {}
    for r in per_fact:
        states[r["final_state"]] = states.get(r["final_state"], 0) + 1
    ok_chain, problems = al.verify_chain(ledger)

    summary = {
        "facts": len(facts),
        "states": states,
        "coverage_ok": coverage["ok"],
        "uncovered": coverage["uncovered"],
        "chain_intact": ok_chain,
        "ledger_head": al.ledger_head(ledger),
        "status": "coverage_incomplete" if not coverage["ok"] else "complete",
    }
    mir.mirror_run(repo_root, session, date_str, summary)
    return {"summary": summary, "per_fact": per_fact, "coverage": coverage,
            "chain_problems": problems, "ledger": ledger}
