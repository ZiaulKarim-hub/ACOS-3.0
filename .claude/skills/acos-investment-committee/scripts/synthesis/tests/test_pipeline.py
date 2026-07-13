#!/usr/bin/env python3
"""
test_pipeline.py — offline tests for Phases 2-7 (no model calls, no network).

Unit-tests each stage module, then runs the full orchestrator end-to-end over the
adversarial cases the skill exists to defend against (PLAN.md §13):
  - correlated agreement must NOT reach 'verified';
  - an unfalsifiable claim must be nullified;
  - an irreducible conflict must land CONTESTED (never a fabricated winner);
  - a single-source claim caps at probable/CORROBORATED.

Run:  python3 tests/test_pipeline.py   (exit 0 = all pass)
"""

import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import axiom_ledger as al          # noqa: E402
import decircularize as dc         # noqa: E402
import grade_fuse as gf            # noqa: E402
import falsify as fz               # noqa: E402
import oscillation_guard as og     # noqa: E402
import resolve as rs               # noqa: E402
import lifecycle as lc             # noqa: E402
import coverage as cov             # noqa: E402
import orchestrate as orch         # noqa: E402

PASS, FAIL = 0, 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")


def src(sid, family="anthropic", origin=None, context_id=None, text="", value=None, engine=False):
    return {"id": sid, "family": family, "origin": origin, "context_id": context_id,
            "text": text, "value": value, "is_engine_output": engine}


def main():
    tmp = tempfile.mkdtemp(prefix="axiom-pipe-")

    # === Phase 2: de-circularization =========================================
    print("\n[2] de-circularization (citogenesis firewall)")
    # two copies from the same upstream origin collapse to ONE independent vote
    r = dc.collapse([src("a", "anthropic", origin="docA", text="x"),
                     src("b", "openai", origin="docA", text="x")])
    check("shared origin collapses to 1 independent", r["independent_sources"] == 1, r)
    # same family + same context = correlated -> 1
    r = dc.collapse([src("a", "anthropic", origin="d1", context_id="P1"),
                     src("b", "anthropic", origin="d2", context_id="P1")])
    check("same family+context collapses to 1", r["independent_sources"] == 1, r)
    # genuinely independent -> 2, two families
    r = dc.collapse([src("a", "anthropic", origin="d1", context_id="P1"),
                     src("b", "openai", origin="d2", context_id="P2")])
    check("independent sources counted as 2", r["independent_sources"] == 2 and len(r["families"]) == 2, r)
    # no-provenance + self-citation excluded from corroboration
    r = dc.collapse([src("a", "anthropic", origin="d1"),
                     src("np", "openai", origin=None),
                     src("self", "anthropic", origin="d9", engine=True)])
    check("no-provenance + self-citation not corroborators", r["independent_sources"] == 1, r)

    # === Phase 3: grading + fusion ===========================================
    print("\n[3] grading + fusion")
    g = gf.grade_claim(2, ["anthropic", "openai"], has_primary_citation=True)
    check("2 indep + 2 families + primary -> verified", g["confidence"] == "verified", g)
    g = gf.grade_claim(1, ["anthropic"])
    check("single source capped at probable", g["confidence"] == "probable", g)
    g = gf.grade_claim(0, [])
    check("no support -> unverified", g["confidence"] == "unverified", g)
    f = gf.fuse([{"value": 10.0, "source_id": "a"}, {"value": 11.0, "source_id": "b"},
                 {"value": 100.0, "source_id": "c"}], claim_type="numeric")
    check("numeric outlier doesn't move the median", f["fused_value"] == 11.0, f)
    f = gf.fuse([{"value": "yes", "source_id": "a"}, {"value": "yes", "source_id": "b"},
                 {"value": "no", "source_id": "c"}], claim_type="categorical",
                weights={"c": 10.0})
    check("weighting can flip the winner -> divergence flag", f["divergence"] is True and f["weighted_result"] == "no", f)

    # === Phase 4: falsification gate + oscillation guard =====================
    print("\n[4] falsification gate + oscillation guard")
    settled = os.path.join(tmp, "settled.jsonl")
    gt = fz.run_gate({"falsifiable": False, "independent_sources": 2, "flags": {}})
    check("unfalsifiable -> nullify", gt["disposition"] == "nullify" and "unfalsifiable" in gt["hard"], gt)
    gt = fz.run_gate({"falsifiable": True, "independent_sources": 2, "flags": {"fabrication_no_origin": True}})
    check("fabrication -> nullify", gt["disposition"] == "nullify", gt)
    gt = fz.run_gate({"falsifiable": True, "independent_sources": 1, "flags": {}})
    check("single source alone -> keep (cap owned by grading, not the gate)", gt["disposition"] == "keep", gt)
    gt = fz.run_gate({"falsifiable": True, "independent_sources": 2, "flags": {"conflict_of_interest": True}})
    check("conflict-of-interest -> downgrade", gt["disposition"] == "downgrade" and "conflict_of_interest" in gt["soft"], gt)
    gt = fz.run_gate({"falsifiable": True, "independent_sources": 2, "flags": {}},
                     refuter={"objection": "sample too small", "credible": True, "rebutted": False},
                     settled_path=settled)
    check("credible unrebutted refuter -> downgrade + disconfirmer", gt["disposition"] == "downgrade" and gt["new_disconfirmers"], gt)
    check("objection recorded as settled", og.is_settled(settled, "sample too small"))
    gt2 = fz.run_gate({"falsifiable": True, "independent_sources": 2, "flags": {}},
                      refuter={"objection": "sample too small", "credible": True, "rebutted": False},
                      settled_path=settled)
    check("re-raised settled objection is skipped (oscillation guard)", gt2["oscillation_skipped"] and gt2["disposition"] == "keep", gt2)
    gt = fz.run_gate({"falsifiable": True, "independent_sources": 2, "flags": {}})
    check("clean claim -> keep, gate passed", gt["disposition"] == "keep" and gt["gate_state"] == "passed", gt)

    # === Phase 5: conflict resolution ========================================
    print("\n[5] conflict resolution (precedence ladder)")
    res = rs.resolve_conflict([{"value": "A", "directness": 3}, {"value": "B", "directness": 1}])
    check("ladder decides by directness", res["status"] == "resolved" and res["winner"]["value"] == "A", res)
    res = rs.resolve_conflict([{"value": "A", "directness": 2}, {"value": "B", "directness": 2}])
    check("all-rungs tie -> UNRESOLVED (no fabricated winner)", res["status"] == "unresolved", res)
    res = rs.resolve_conflict([{"value": "A"}, {"value": "B"}], polarity="asymmetric_veto")
    check("asymmetric veto blocks on dissent", res["status"] == "vetoed", res)
    res = rs.resolve_conflict([{"value": "A"}, {"value": "A"}])
    check("agreement -> resolved", res["status"] == "resolved", res)

    # === Phase 6: demotion cascade ===========================================
    print("\n[6] demotion cascade (truth-maintenance)")
    lg = os.path.join(tmp, "cascade.jsonl")
    al.append_claim(lg, {"id": "B", "statement": "b", "state": "CONJECTURE", "confidence": "unverified"})
    al.append_claim(lg, {"id": "A", "statement": "a", "state": "CONJECTURE", "confidence": "unverified", "depends_on": ["B"]})
    al.append_claim(lg, {"id": "B", "statement": "b", "state": "REFUTED", "confidence": "unverified"})
    plan = lc.cascade_plan(al.read_ledger(lg))
    check("refuting B flags dependent A for re-eval", plan.get("B") == ["A"], plan)

    # === Phase 7: end-to-end orchestration over adversarial cases ============
    print("\n[7] end-to-end pipeline (adversarial cases)")
    session_dir = os.path.join(tmp, "session")
    subqs = ["SQ1", "SQ2", "SQ3", "SQ4", "SQ5", "SQ6"]
    facts = [
        # F1: correlated agreement (3 same-family+context) must NOT reach verified.
        {"fact_id": "F1", "statement": "Correlated claim.", "claim_type": "categorical", "sub_question": "SQ1",
         "candidates": [{"value": "y", "source": src(f"m{i}", "anthropic", origin=f"d{i}", context_id="P1")} for i in range(3)],
         "grading": {"has_primary_citation": True}, "falsifiable": True},
        # F2: genuinely independent + primary + clean -> ESTABLISHED/verified.
        {"fact_id": "F2", "statement": "Well-supported claim.", "claim_type": "categorical", "sub_question": "SQ2",
         "candidates": [{"value": "y", "source": src("a", "anthropic", origin="d1", context_id="P1")},
                        {"value": "y", "source": src("b", "openai", origin="d2", context_id="P2")}],
         "grading": {"has_primary_citation": True}, "falsifiable": True},
        # F3: unfalsifiable -> nullified/quarantined.
        {"fact_id": "F3", "statement": "Unfalsifiable opinion.", "claim_type": "categorical", "sub_question": "SQ3",
         "candidates": [{"value": "y", "source": src("a", "anthropic", origin="d1", context_id="P1")},
                        {"value": "y", "source": src("b", "openai", origin="d2", context_id="P2")}],
         "grading": {"has_primary_citation": True}, "falsifiable": False},
        # F4: irreducible conflict (ladder tie) -> CONTESTED.
        {"fact_id": "F4", "statement": "Contested claim.", "claim_type": "categorical", "sub_question": "SQ4",
         "candidates": [{"value": "A", "source": src("a", "anthropic", origin="d1", context_id="P1")},
                        {"value": "B", "source": src("b", "openai", origin="d2", context_id="P2")}],
         "grading": {"has_primary_citation": True}, "falsifiable": True,
         "conflict": [{"value": "A", "directness": 2}, {"value": "B", "directness": 2}]},
        # F5: single source -> capped at CORROBORATED/probable.
        {"fact_id": "F5", "statement": "Single-source claim.", "claim_type": "categorical", "sub_question": "SQ5",
         "candidates": [{"value": "y", "source": src("a", "anthropic", origin="d1", context_id="P1")}],
         "grading": {"has_primary_citation": False}, "falsifiable": True},
        # F6: strong claim but a credible refuter -> downgraded to CORROBORATED + settled objection.
        {"fact_id": "F6", "statement": "Refuted-down claim.", "claim_type": "categorical", "sub_question": "SQ6",
         "candidates": [{"value": "y", "source": src("a", "anthropic", origin="d1", context_id="P1")},
                        {"value": "y", "source": src("b", "openai", origin="d2", context_id="P2")}],
         "grading": {"has_primary_citation": True}, "falsifiable": True,
         "refuter": {"objection": "confounder unaddressed", "credible": True, "rebutted": False}},
    ]
    out = orch.run(session_dir, "Adversarial test question", subqs, facts,
                   now="2026-07-06T00:00Z", repo_root=tmp, date_str="2026-07-06", session="test")
    states = {r["fact_id"]: r["final_state"] for r in out["per_fact"]}

    check("F1 correlated agreement capped at CORROBORATED (not ESTABLISHED)", states["F1"] == "CORROBORATED", states)
    check("F2 independent+clean reached ESTABLISHED", states["F2"] == "ESTABLISHED", states)
    check("F3 unfalsifiable was quarantined", "quarantined" in states["F3"], states)
    check("F4 irreducible conflict landed CONTESTED", states["F4"] == "CONTESTED", states)
    check("F5 single-source capped at CORROBORATED", states["F5"] == "CORROBORATED", states)
    check("F6 credible refuter downgraded to CORROBORATED", states["F6"] == "CORROBORATED", states)
    check("ledger chain intact after full run", out["summary"]["chain_intact"], out["chain_problems"])
    check("coverage gate satisfied (all sub-questions covered)", out["summary"]["coverage_ok"], out["coverage"]["uncovered"])
    check("F6 objection persisted to settled-objections", og.is_settled(os.path.join(session_dir, "settled-objections.jsonl"), "confounder unaddressed"))
    # mirror + render artifacts exist
    check("source-of-truth.md rendered", os.path.exists(os.path.join(session_dir, "source-of-truth.md")))
    check("ACOS evidence mirror written", os.path.exists(os.path.join(tmp, ".acos", "evidence", "2026-07-06", "axiom-test", "run.log")))
    check("ACOS metrics mirror written", os.path.exists(os.path.join(tmp, ".acos", "metrics", "agent-completions.log")))

    # coverage gate must FAIL when a sub-question is uncovered
    cg = cov.coverage_gate(subqs + ["SQ_MISSING"], al.read_ledger(out["ledger"]))
    check("coverage gate flags an uncovered sub-question", (not cg["ok"]) and "SQ_MISSING" in cg["uncovered"], cg)

    print(f"\n==== {PASS} passed, {FAIL} failed ====")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
