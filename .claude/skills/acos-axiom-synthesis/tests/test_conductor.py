#!/usr/bin/env python3
"""
test_conductor.py — offline tests for the live-run conductor (no models, no network).

Covers:
  - extract_json tolerates raw JSON, ```json fences, and prose-wrapped objects;
  - the three reply parsers validate + coerce, and report (not swallow) errors;
  - combine_graders does per-question majority, fail-closed on ties;
  - assemble_fact derives V4 from the refuter and engages checklist mode;
  - cluster_claims groups same-statement claims and flags value conflicts;
  - run_from_collected reads a fixture collection dir and drives the real engine
    end-to-end (a strong claim reaches ESTABLISHED; a veto-failed claim quarantines).

Run:  python3 tests/test_conductor.py   (exit 0 = all pass)
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import conductor as cond   # noqa: E402
import axiom_ledger as al   # noqa: E402

PASS, FAIL = 0, 0


def check(name, cond_, detail=""):
    global PASS, FAIL
    if cond_:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")


ALL_YES_SEM = {
    "V1-FALSIFIABLE": True, "V2-TRACEABLE-ORIGIN": True,
    "V3-NO-INTERNAL-CONTRADICTION": True, "N4-CITATION-SUPPORTS": True,
    "N6-REPRODUCIBLE": True, "N7-SPECIFIC": True,
    "N8-NO-CONFLICT-OF-INTEREST": True, "N10-LATERAL-SUPPORT": True,
}


def grader_reply(claim_id, family, answers, primary=True, fals=True,
                 volatility=None, legacy_freshness=None):
    flags = {"has_primary_citation": primary, "falsifiable": fals}
    if volatility is not None:
        flags["volatility"] = volatility
    if legacy_freshness is not None:
        flags["freshness_ok"] = legacy_freshness   # retired field — parser must ignore
    return json.dumps({
        "grader_id": f"g-{family}", "family": family, "claim_id": claim_id,
        "checklist_answers": answers,
        "grading_flags": flags,
    })


def main():
    # === extract_json ========================================================
    print("\n[A] extract_json tolerance")
    check("raw JSON parses", cond.extract_json('{"a":1}') == {"a": 1})
    fenced = "Here you go:\n```json\n{\"a\": 2, \"b\": [1,2]}\n```\nHope that helps!"
    check("fenced JSON parses", cond.extract_json(fenced) == {"a": 2, "b": [1, 2]})
    prose = 'Sure — {"a": 3} is my answer.'
    check("prose-wrapped object parses", cond.extract_json(prose) == {"a": 3})
    nested = 'noise {"x": {"y": 1}, "z": "}"} trailing'
    check("nested braces + brace-in-string parse", cond.extract_json(nested) == {"x": {"y": 1}, "z": "}"})
    try:
        cond.extract_json("no json here at all")
        check("no-JSON raises", False)
    except cond.ParseError:
        check("no-JSON raises", True)

    # === parsers =============================================================
    print("\n[B] reply parsers")
    e_obj, e_err = cond.parse_elicitor(json.dumps({
        "elicitor_id": "e1", "family": "google",
        "claims": [{"statement": "The sky is blue.", "value": "blue", "origin": "docA", "sub_question": "SQ1"},
                   {"no_statement": True}]}))
    check("elicitor keeps valid claim, flags bad one", e_obj and len(e_obj["claims"]) == 1 and e_err, (e_obj, e_err))

    g_obj, g_err = cond.parse_grader(grader_reply("C1", "openai-web", ALL_YES_SEM))
    check("grader coerces all 8 semantic answers", g_obj and len(g_obj["checklist_answers"]) == 8, (g_obj, g_err))
    g_obj2, g_err2 = cond.parse_grader(grader_reply("C1", "x", {"V1-FALSIFIABLE": "yes"}))
    check("grader flags missing answers", g_obj2 and any("missing" in e for e in g_err2), g_err2)

    r_obj, _ = cond.parse_refuter(json.dumps({"claim_id": "C1", "family": "zai",
                                              "objection": "sample too small", "credible": True,
                                              "rebutted": False, "fatal": False}))
    check("refuter parses verdict", r_obj and r_obj["objection"] == "sample too small" and r_obj["credible"], r_obj)
    r_none, _ = cond.parse_refuter(json.dumps({"claim_id": "C1", "objection": "none"}))
    check("refuter null objection normalized", r_none["objection"] is None, r_none)
    # F4 — the grader's blind volatility label
    gv, gv_err = cond.parse_grader(grader_reply("C1", "a", ALL_YES_SEM, volatility=" Fast "))
    check("F4: volatility label parsed + normalized (' Fast ' -> 'fast')",
          gv["grading_flags"]["volatility"] == "fast", gv["grading_flags"])
    gl, gl_err = cond.parse_grader(grader_reply("C1", "a", ALL_YES_SEM, legacy_freshness=True))
    check("F4: legacy freshness_ok ignored without error, no volatility signal",
          gl["grading_flags"]["volatility"] is None and not any("freshness" in e for e in gl_err), (gl, gl_err))
    gb, _ = cond.parse_grader(grader_reply("C1", "a", ALL_YES_SEM, volatility="sometimes"))
    check("F4: invalid volatility label -> None", gb["grading_flags"]["volatility"] is None, gb["grading_flags"])

    # === combine_graders =====================================================
    print("\n[C] grader consensus (majority, fail-closed)")
    g_yes = cond.parse_grader(grader_reply("C1", "a", ALL_YES_SEM))[0]
    g_yes2 = cond.parse_grader(grader_reply("C1", "b", ALL_YES_SEM))[0]
    g_no = cond.parse_grader(grader_reply("C1", "c", {**ALL_YES_SEM, "N7-SPECIFIC": False}))[0]
    con = cond.combine_graders([g_yes, g_yes2, g_no])
    check("2-of-3 yes wins the question", con["checklist_answers"]["N7-SPECIFIC"] is True, con)
    con_tie = cond.combine_graders([g_yes, g_no])   # 1 yes, 1 no on N7 -> tie -> False
    check("tie resolves False (fail-closed)", con_tie["checklist_answers"]["N7-SPECIFIC"] is False, con_tie)
    # F4 — volatility vote across graders
    gv1 = cond.parse_grader(grader_reply("C1", "a", ALL_YES_SEM, volatility="fast"))[0]
    gv2 = cond.parse_grader(grader_reply("C1", "b", ALL_YES_SEM, volatility="fast"))[0]
    gv3 = cond.parse_grader(grader_reply("C1", "c", ALL_YES_SEM, volatility="durable"))[0]
    check("F4: 2-of-3 volatility vote wins ('fast')",
          cond.combine_graders([gv1, gv2, gv3])["grading_flags"]["volatility"] == "fast")
    check("F4: 1-1 volatility tie -> None (no judge signal)",
          cond.combine_graders([gv1, gv3])["grading_flags"]["volatility"] is None)

    # === assemble_fact =======================================================
    print("\n[D] assemble_fact derives V4 + engages checklist mode")
    cluster = {"statement": "s", "claim_type": "categorical", "sub_question": "SQ1",
               "candidates": [{"value": "y", "source": {"id": "a", "family": "google", "origin": "d1", "context_id": "P1"}},
                              {"value": "y", "source": {"id": "b", "family": "zai", "origin": "d2", "context_id": "P2"}}]}
    consensus = cond.combine_graders([g_yes, g_yes2])
    fatal_ref = {"objection": "fabricated", "credible": True, "rebutted": False, "fatal": True}
    f = cond.assemble_fact("C1", cluster, consensus, fatal_ref)
    check("fatal refuter sets V4 = False", f["checklist_answers"]["V4-SURVIVES-REFUTER"] is False, f["checklist_answers"])
    f2 = cond.assemble_fact("C1", cluster, consensus, None)
    check("no refuter sets V4 = True", f2["checklist_answers"]["V4-SURVIVES-REFUTER"] is True, f2["checklist_answers"])
    check("assembled fact carries checklist_answers (mode on)", "checklist_answers" in f2)
    # F4 — volatility_judge + domain threading; retired freshness_ok is gone
    con_v = cond.combine_graders([gv1, gv2])
    fv = cond.assemble_fact("C1", cluster, con_v, None, domain="rates")
    check("F4: grader volatility vote attached as volatility_judge",
          fv.get("volatility_judge") == "fast", fv)
    check("F4: domain threaded onto the fact", fv.get("domain") == "rates", fv)
    check("F4: retired freshness_ok absent from grading", "freshness_ok" not in fv["grading"], fv["grading"])

    # === cluster_claims ======================================================
    print("\n[E] cluster_claims groups + flags conflicts")
    elicited = [
        {"family": "google", "elicitor_id": "e1", "claim": {"statement": "Rate is 5%.", "value": "5%", "origin": "d1", "sub_question": "SQ1"}},
        {"family": "zai", "elicitor_id": "e2", "claim": {"statement": "rate is 5%", "value": "5%", "origin": "d2", "sub_question": "SQ1"}},
        {"family": "openai-web", "elicitor_id": "e3", "claim": {"statement": "Rate is 7%.", "value": "7%", "origin": "d3", "sub_question": "SQ1"}},
    ]
    clusters = cond.cluster_claims(elicited)
    same = [c for c in clusters if "5" in c["statement"]][0]
    check("same statement across families -> one cluster, 2 candidates", len(same["candidates"]) == 2, same)
    check("differing statements stay separate", len(clusters) == 2, [c["statement"] for c in clusters])
    # numeric claim with a STRING value (e.g. "5,638,830") must coerce to float,
    # not crash the engine's median/mean fusion.
    num = cond.cluster_claims([{"family": "anthropic", "elicitor_id": "e1",
        "claim": {"statement": "Sydney population is 5,638,830.", "value": "5,638,830",
                  "claim_type": "numeric", "origin": "abs", "sub_question": "SQ1"}}])
    check("numeric string value coerced to float", num[0]["candidates"][0]["value"] == 5638830.0, num[0]["candidates"][0]["value"])

    # === run_from_collected (end-to-end via real engine) =====================
    print("\n[F] run_from_collected end-to-end")
    tmp = tempfile.mkdtemp(prefix="axiom-cond-")
    coll = os.path.join(tmp, "collected")
    for sub in ("elicitor", "grader", "refuter"):
        os.makedirs(os.path.join(coll, sub))
    # Two families elicit the SAME strong claim (independent origins/families) -> C1.
    for fam, oid in (("google", "d1"), ("zai", "d2")):
        with open(os.path.join(coll, "elicitor", f"{fam}.json"), "w") as fh:
            fh.write(json.dumps({"elicitor_id": f"e-{fam}", "family": fam,
                                 "claims": [{"statement": "The capital is Metropolis.", "value": "Metropolis",
                                             "origin": oid, "sub_question": "SQ1"}]}))
    # Two blind graders, all-yes -> verified.
    for fam in ("claude", "openai-web"):
        with open(os.path.join(coll, "grader", f"C1__{fam}.json"), "w") as fh:
            fh.write(grader_reply("C1", fam, ALL_YES_SEM))
    # Refuter finds nothing fatal.
    with open(os.path.join(coll, "refuter", "C1.json"), "w") as fh:
        fh.write(json.dumps({"claim_id": "C1", "family": "gemini", "objection": None,
                             "credible": False, "rebutted": False, "fatal": False}))
    out = cond.run_from_collected(tmp, "What is the capital?", ["SQ1"],
                                  now="2026-08-02T00:00Z", repo_root=tmp,
                                  date_str="2026-08-02", session="condtest")
    states = {r["fact_id"]: r["final_state"] for r in out["per_fact"]}
    check("strong 2-family claim reached ESTABLISHED", states.get("C1") == "ESTABLISHED", states)
    check("ledger chain intact", out["summary"]["chain_intact"], out.get("chain_problems"))
    check("facts_built == 1", out["facts_built"] == 1, out["facts_built"])

    # veto-fail variant: grader says origin not traceable -> quarantined
    tmp2 = tempfile.mkdtemp(prefix="axiom-cond2-")
    coll2 = os.path.join(tmp2, "collected")
    for sub in ("elicitor", "grader", "refuter"):
        os.makedirs(os.path.join(coll2, sub))
    for fam, oid in (("google", "d1"), ("zai", "d2")):
        with open(os.path.join(coll2, "elicitor", f"{fam}.json"), "w") as fh:
            fh.write(json.dumps({"elicitor_id": f"e-{fam}", "family": fam,
                                 "claims": [{"statement": "Unsourced rumor.", "value": "x",
                                             "origin": oid, "sub_question": "SQ1"}]}))
    veto_fail = {**ALL_YES_SEM, "V2-TRACEABLE-ORIGIN": False}
    for fam in ("claude", "openai-web"):
        with open(os.path.join(coll2, "grader", f"C1__{fam}.json"), "w") as fh:
            fh.write(grader_reply("C1", fam, veto_fail))
    out2 = cond.run_from_collected(tmp2, "Q", ["SQ1"], now="2026-08-02T00:00Z",
                                   repo_root=tmp2, date_str="2026-08-02", session="condtest2")
    states2 = {r["fact_id"]: r["final_state"] for r in out2["per_fact"]}
    check("veto-failed claim quarantined", "quarantined" in states2.get("C1", ""), states2)

    # === real cited sources reach verified + carry dates =====================
    print("\n[G] distinct cited sources -> verified; source_date recorded")
    tmp3 = tempfile.mkdtemp(prefix="axiom-cond3-")
    coll3 = os.path.join(tmp3, "collected")
    for sub in ("elicitor", "grader", "refuter"):
        os.makedirs(os.path.join(coll3, sub))
    # Two families cite DIFFERENT real sources (distinct source_url) + dates.
    sources = {"google": ("https://www.britannica.com/place/Canberra", "2026-05-01"),
               "zai": ("https://www.australia.gov.au/canberra", "2026-06-15")}
    for fam, (url, date) in sources.items():
        with open(os.path.join(coll3, "elicitor", f"{fam}.json"), "w") as fh:
            fh.write(json.dumps({"elicitor_id": f"e-{fam}", "family": fam, "claims": [
                {"statement": "The capital of Australia is Canberra.", "value": "Canberra",
                 "origin": "ref", "source_url": url, "source_date": date,
                 "sub_question": "SQ1", "locator": "intro"}]}))
    for fam in ("claude", "openai-web"):
        with open(os.path.join(coll3, "grader", f"C1__{fam}.json"), "w") as fh:
            fh.write(grader_reply("C1", fam, ALL_YES_SEM))
    with open(os.path.join(coll3, "refuter", "C1.json"), "w") as fh:
        fh.write(json.dumps({"claim_id": "C1", "family": "gemini", "objection": None,
                             "credible": False, "rebutted": False, "fatal": False}))
    out3 = cond.run_from_collected(tmp3, "Capital?", ["SQ1"], now="2026-08-02T00:00Z",
                                   repo_root=tmp3, date_str="2026-08-02", session="condtest3")
    st3 = {r["fact_id"]: r["final_state"] for r in out3["per_fact"]}
    check("two DISTINCT cited sources -> ESTABLISHED/verified", st3.get("C1") == "ESTABLISHED", st3)
    # the source date must be recorded in the ledger provenance
    ledger = al.read_ledger(os.path.join(tmp3, "claims.jsonl"))
    est = [r for r in ledger if r["id"] == "C1" and r["state"] == "ESTABLISHED"][-1]
    as_ofs = [p.get("as_of") for p in est.get("provenance", [])]
    check("source_date carried into provenance (as_of)", any(a for a in as_ofs), as_ofs)

    # === F4 end-to-end: judge volatility label arms the recency cap ===========
    print("\n[H] F4 e2e — grader volatility vote + undated sources -> capped")
    tmp4 = tempfile.mkdtemp(prefix="axiom-cond4-")
    coll4 = os.path.join(tmp4, "collected")
    for sub in ("elicitor", "grader", "refuter"):
        os.makedirs(os.path.join(coll4, sub))
    # Lexically-quiet statement (no signal words), NO source dates, NO domain —
    # the graders' blind volatility vote is the ONLY recency signal.
    for fam, oid in (("google", "d1"), ("zai", "d2")):
        with open(os.path.join(coll4, "elicitor", f"{fam}.json"), "w") as fh:
            fh.write(json.dumps({"elicitor_id": f"e-{fam}", "family": fam,
                                 "claims": [{"statement": "The reference figure is 42.",
                                             "value": "42", "origin": oid,
                                             "sub_question": "SQ1"}]}))
    for fam in ("claude", "openai-web"):
        with open(os.path.join(coll4, "grader", f"C1__{fam}.json"), "w") as fh:
            fh.write(grader_reply("C1", fam, ALL_YES_SEM, volatility="volatile"))
    with open(os.path.join(coll4, "refuter", "C1.json"), "w") as fh:
        fh.write(json.dumps({"claim_id": "C1", "family": "gemini", "objection": None,
                             "credible": False, "rebutted": False, "fatal": False}))
    out4 = cond.run_from_collected(tmp4, "Q", ["SQ1"], now="2026-08-02T00:00Z",
                                   repo_root=tmp4, date_str="2026-08-02", session="condtest4")
    st4 = {r["fact_id"]: r for r in out4["per_fact"]}
    check("F4 e2e: judge-only volatile + undated sources -> capped at CORROBORATED (not ESTABLISHED)",
          st4["C1"]["final_state"] == "CORROBORATED", {k: v["final_state"] for k, v in st4.items()})
    check("F4 e2e: claim classified 'volatile' from the graders' vote alone",
          st4["C1"]["volatility"] == "volatile", st4["C1"]["volatility"])
    check("F4 e2e: checklist-mode recency cap fired (the 9/10=90% gap fix)",
          st4["C1"].get("recency_capped") is True, st4["C1"].get("recency_capped"))
    # Same collection but with a run-level domain tag: the domain prior reaches the fact.
    facts4, _ = cond.build_facts(cond.load_collected(tmp4), domain="rates")
    check("F4: run-level domain reaches every assembled fact", facts4[0].get("domain") == "rates", facts4[0].get("domain"))

    print(f"\n==== {PASS} passed, {FAIL} failed ====")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
