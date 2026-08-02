#!/usr/bin/env python3
"""
test_checklist.py — offline tests for the boolean confidence gate (Point-1).

Covers, with NO model calls and NO network:
  - config drift: the YAML file parses identically to the embedded DEFAULT;
  - the boss's threshold example (9/10 passes at 90%, 8/10 does not reach verified);
  - veto override: a single veto NO nullifies regardless of a perfect percentage;
  - fail-closed: a missing veto answer nullifies; a missing normal answer counts as no;
  - the single-source cap: >=90% yet capped at 'probable' when N1/N2 aren't both yes;
  - domain packs extend the denominator;
  - end-to-end through orchestrate: verified->ESTABLISHED, veto->quarantined,
    mid-band->CORROBORATED, and the legacy (no-checklist) path is unchanged.

Run:  python3 tests/test_checklist.py   (exit 0 = all pass)
"""

import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import checklist as chk          # noqa: E402
import orchestrate as orch       # noqa: E402

PASS, FAIL = 0, 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")


# All-yes semantic judge answers (the 4 vetoes + 5 semantic normals).
ALL_YES = {
    "V1-FALSIFIABLE": True, "V2-TRACEABLE-ORIGIN": True,
    "V3-NO-INTERNAL-CONTRADICTION": True, "V4-SURVIVES-REFUTER": True,
    "N4-CITATION-SUPPORTS": True, "N6-REPRODUCIBLE": True,
    "N7-SPECIFIC": True, "N8-NO-CONFLICT-OF-INTEREST": True,
    "N10-LATERAL-SUPPORT": True,
}


def sem(**overrides):
    d = dict(ALL_YES)
    d.update(overrides)
    return d


def src(sid, family="anthropic", origin=None, context_id=None):
    return {"id": sid, "family": family, "origin": origin, "context_id": context_id,
            "text": "", "value": None, "is_engine_output": False}


def main():
    cl = chk.load_checklist()

    # === config drift =========================================================
    print("\n[A] config drift (YAML == embedded DEFAULT)")
    d = chk.DEFAULT_CHECKLIST
    check("thresholds match", cl["thresholds"] == d["thresholds"], cl["thresholds"])
    check("veto ids match",
          [q["id"] for q in cl["veto_questions"]] == [q["id"] for q in d["veto_questions"]])
    check("normal ids match",
          [q["id"] for q in cl["normal_questions"]] == [q["id"] for q in d["normal_questions"]])
    check("verified_also_requires match",
          cl["verified_also_requires"] == d["verified_also_requires"])

    # === direct evaluate(): tiers & thresholds ================================
    print("\n[B] evaluate(): tiers, thresholds, the boss's 9/10 example")

    def ctx(indep=2, fams=2, primary=True, divergence=False, superseded=False,
            fresh=True, semantic=None, domain=None):
        c = chk.build_context(indep, fams, primary, divergence,
                              semantic_answers=semantic if semantic is not None else ALL_YES,
                              superseded=superseded, freshness_ok=fresh)
        c["domain"] = domain
        return c

    v = chk.evaluate(cl, ctx())
    check("all-yes, 2 indep/2 families -> verified", v["tier"] == "verified" and v["yes_share"] == 1.0, v)

    # 9 of 10 normal yes (turn N7 off) at threshold 0.90 -> verified (N1,N2 still yes)
    v = chk.evaluate(cl, ctx(semantic=sem(**{"N7-SPECIFIC": False})))
    check("9/10 yes at 90% -> verified (boss example passes)",
          v["tier"] == "verified" and round(v["yes_share"], 3) == 0.9, v)

    # 8 of 10 normal yes (turn N7 + N8 off) -> below verified_min -> probable (graded)
    v = chk.evaluate(cl, ctx(semantic=sem(**{"N7-SPECIFIC": False, "N8-NO-CONFLICT-OF-INTEREST": False})))
    check("8/10 yes -> NOT verified (rejected from verified), lands probable",
          v["tier"] == "probable" and round(v["yes_share"], 3) == 0.8, v)

    # below probable_min (0.70): weak claim, most NORMAL answers no -> unverified.
    # Vetoes MUST stay yes here, else it (correctly) nullifies before tiering.
    weak = sem(**{"N4-CITATION-SUPPORTS": False, "N6-REPRODUCIBLE": False,
                  "N7-SPECIFIC": False, "N8-NO-CONFLICT-OF-INTEREST": False,
                  "N10-LATERAL-SUPPORT": False})
    v = chk.evaluate(cl, ctx(indep=0, fams=0, primary=False, divergence=True,
                             superseded=True, fresh=False, semantic=weak))
    check("mostly-no weak claim (vetoes pass) -> unverified",
          v["tier"] == "unverified" and v["yes_share"] < 0.70, v)

    # === veto override ========================================================
    print("\n[C] veto override + fail-closed")
    # perfect normals but ONE veto = no -> nullified regardless of percentage
    v = chk.evaluate(cl, ctx(semantic=sem(**{"V2-TRACEABLE-ORIGIN": False})))
    check("single veto NO nullifies despite 100% normals",
          v["tier"] == "nullified" and v["nullified"] is True, v)
    # missing veto answer -> fail-closed nullify
    miss = sem()
    del miss["V3-NO-INTERNAL-CONTRADICTION"]
    v = chk.evaluate(cl, ctx(semantic=miss))
    check("missing veto answer -> nullified (fail-closed)", v["tier"] == "nullified", v)
    # missing normal answer -> counts as no (not yes)
    missn = sem()
    del missn["N6-REPRODUCIBLE"]
    v = chk.evaluate(cl, ctx(semantic=missn))
    check("missing normal answer counts as no", round(v["yes_share"], 3) == 0.9, v)

    # === single-source cap ====================================================
    print("\n[D] single-source cap (>=90% yet capped at probable)")
    # 2 independent sources but only 1 family: N2 fails (1 question), 9/10 = 0.90,
    # but verified_also_requires N2 -> cap at probable.
    v = chk.evaluate(cl, ctx(indep=2, fams=1))
    check("2 indep / 1 family: 9/10=0.90 but capped at probable",
          v["tier"] == "probable" and round(v["yes_share"], 3) == 0.9, v)

    # === domain packs =========================================================
    print("\n[E] domain packs extend the denominator")
    cl2 = {
        "thresholds": {"verified_min": 0.90, "probable_min": 0.70},
        "verified_also_requires": ["N1-TWO-INDEP-SOURCES", "N2-TWO-DISTINCT-FAMILIES"],
        "veto_questions": cl["veto_questions"],
        "normal_questions": cl["normal_questions"],
        "domain_packs": {"government": [
            {"id": "G1-OFFICIAL-GAZETTE", "text": "official record?", "evaluator": "semantic"},
            {"id": "G2-TWO-OUTLETS", "text": "two outlets?", "evaluator": "semantic"},
        ]},
    }
    c = chk.build_context(2, 2, True, False,
                          semantic_answers=sem(**{"G1-OFFICIAL-GAZETTE": True, "G2-TWO-OUTLETS": True}))
    c["domain"] = "government"
    v = chk.evaluate(cl2, c)
    check("domain pack raises normal_total to 12", v["normal_total"] == 12, v)
    check("all-yes with pack -> verified", v["tier"] == "verified", v)

    # === end-to-end through orchestrate =======================================
    print("\n[F] end-to-end via orchestrate (checklist mode)")
    tmp = tempfile.mkdtemp(prefix="axiom-checklist-")
    session_dir = os.path.join(tmp, "session")
    subqs = ["SQ1", "SQ2", "SQ3", "SQ4"]

    def fact(fid, sq, answers, extra=None):
        f = {"fact_id": fid, "statement": f"claim {fid}", "claim_type": "categorical",
             "sub_question": sq,
             "candidates": [{"value": "y", "source": src("a", "anthropic", origin="d1", context_id="P1")},
                            {"value": "y", "source": src("b", "openai", origin="d2", context_id="P2")}],
             "grading": {"has_primary_citation": True}, "falsifiable": True,
             "checklist_answers": answers}
        if extra:
            f.update(extra)
        return f

    facts = [
        # C1: all yes, 2 indep/2 families -> verified -> ESTABLISHED
        fact("C1", "SQ1", ALL_YES),
        # C2: a veto (traceable origin) = no -> quarantined
        fact("C2", "SQ2", sem(**{"V2-TRACEABLE-ORIGIN": False})),
        # C3: 8/10 (two normals no) -> probable -> CORROBORATED
        fact("C3", "SQ3", sem(**{"N7-SPECIFIC": False, "N8-NO-CONFLICT-OF-INTEREST": False})),
        # C4: legacy path (NO checklist_answers) must still behave as before -> ESTABLISHED
        {"fact_id": "C4", "statement": "legacy", "claim_type": "categorical", "sub_question": "SQ4",
         "candidates": [{"value": "y", "source": src("a", "anthropic", origin="d1", context_id="P1")},
                        {"value": "y", "source": src("b", "openai", origin="d2", context_id="P2")}],
         "grading": {"has_primary_citation": True}, "falsifiable": True},
    ]
    out = orch.run(session_dir, "Checklist test", subqs, facts,
                   now="2026-07-22T00:00Z", repo_root=tmp, date_str="2026-07-22", session="chk")
    states = {r["fact_id"]: r["final_state"] for r in out["per_fact"]}
    check("C1 all-yes verified -> ESTABLISHED", states["C1"] == "ESTABLISHED", states)
    check("C2 veto-fail -> quarantined", "quarantined" in states["C2"], states)
    check("C3 8/10 probable -> CORROBORATED", states["C3"] == "CORROBORATED", states)
    check("C4 legacy path unchanged -> ESTABLISHED", states["C4"] == "ESTABLISHED", states)
    check("ledger chain intact", out["summary"]["chain_intact"], out["chain_problems"])
    # the checklist verdict is recorded on the per-fact result for audit
    c1 = [r for r in out["per_fact"] if r["fact_id"] == "C1"][0]
    check("C1 carries a checklist verdict for audit", c1.get("checklist") and c1["checklist"]["tier"] == "verified", c1.get("checklist"))
    c4 = [r for r in out["per_fact"] if r["fact_id"] == "C4"][0]
    check("C4 legacy carries NO checklist verdict", c4.get("checklist") is None, c4.get("checklist"))

    print(f"\n==== {PASS} passed, {FAIL} failed ====")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
