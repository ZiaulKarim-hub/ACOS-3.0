#!/usr/bin/env python3
"""
test_substrate.py — offline fixture tests for the acos-axiom-synthesis substrate.

No model calls, no network. Proves the Phase-1 acceptance criteria (PLAN.md §11):
  - a hand-seeded ledger round-trips;
  - the verifier detects a tampered line;
  - ledger_writer REFUSES illegal writes (invariants + illegal transitions) by
    raising LedgerError with the right exit code;
  - killing mid-run and re-reading resumes from disk (pure-function frontier);
  - the renderer emits the three prominent sections + a verified claim.

Run:  python3 tests/test_substrate.py   (exit 0 = all pass)
"""

import json
import os
import sys
import tempfile

# make the sibling scripts/ importable
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import axiom_ledger as al  # noqa: E402

PASS, FAIL = 0, 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")


def refused(fn):
    """Return the LedgerError code if fn() raises one, else None (no refusal)."""
    try:
        fn()
        return None
    except al.LedgerError as exc:
        return exc.code


def claim(cid, statement, state, confidence, indep=None, families=None,
          falsification=None, depends_on=None, alternatives=None, superseded_by=None):
    rec = {"id": cid, "statement": statement, "state": state, "confidence": confidence}
    if indep is not None:
        rec["confidence_basis"] = {"independent_sources": indep}
    if families:
        rec["provenance"] = [{"source": f"src-{i}", "locator": "p.1", "family": fam}
                             for i, fam in enumerate(families)]
    if falsification is not None:
        rec["gates"] = {"falsification": falsification}
    if depends_on is not None:
        rec["depends_on"] = depends_on
    if alternatives is not None:
        rec["alternatives"] = alternatives
    if superseded_by is not None:
        rec["superseded_by"] = superseded_by
    return rec


def main():
    tmp = tempfile.mkdtemp(prefix="axiom-test-")
    ledger = os.path.join(tmp, "claims.jsonl")
    print(f"workspace: {tmp}")

    # 1. Round-trip: create a CONJECTURE, read it back, chain verifies.
    print("\n[1] round-trip + chain integrity")
    al.append_claim(ledger, claim("CLM-1", "The sky is blue.", "CONJECTURE", "unverified"), now="2026-07-06T00:00Z")
    recs = al.read_ledger(ledger)
    check("one claim persisted", len(recs) == 1, f"got {len(recs)}")
    ok, problems = al.verify_chain(ledger)
    check("chain intact after write", ok, str(problems))
    check("head is last entry_hash", al.ledger_head(ledger) == recs[-1]["entry_hash"])

    # 2. Legal promotion path with gates satisfied.
    print("\n[2] legal promotion CONJECTURE -> CORROBORATED -> ESTABLISHED")
    al.append_claim(ledger, claim("CLM-1", "The sky is blue.", "CORROBORATED", "probable",
                                  indep=1, families=["anthropic"], falsification="passed"), now="2026-07-06T00:01Z")
    al.append_claim(ledger, claim("CLM-1", "The sky is blue.", "ESTABLISHED", "verified",
                                  indep=2, families=["anthropic", "openai"], falsification="passed"), now="2026-07-06T00:02Z")
    cur = al.current_states(al.read_ledger(ledger))
    check("CLM-1 now ESTABLISHED/verified", cur["CLM-1"]["state"] == "ESTABLISHED" and cur["CLM-1"]["confidence"] == "verified")

    # 3. Tamper detection: mutate a stored line on disk.
    print("\n[3] tamper detection")
    lines = open(ledger, "r", encoding="utf-8").read().splitlines()
    obj = json.loads(lines[0])
    obj["statement"] = "The sky is green."          # alter content, keep old entry_hash
    lines[0] = json.dumps(obj, ensure_ascii=False)
    open(ledger, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    ok, problems = al.verify_chain(ledger)
    check("verifier flags the tampered line", (not ok) and any("line 1" in p for p in problems), str(problems))

    # fresh ledger for the refusal tests
    ledger2 = os.path.join(tmp, "claims2.jsonl")

    # 4. Single-source cap / corroboration gate: 'verified' with one source is refused.
    print("\n[4] invariant refusals (exit 3)")
    code = refused(lambda: al.append_claim(ledger2, claim("CLM-A", "x", "CONJECTURE", "verified", indep=1, families=["anthropic"])))
    check("verified w/ single source refused", code == al.CODE_INVARIANT, f"code={code}")

    code = refused(lambda: al.append_claim(ledger2, claim("CLM-A", "x", "CONJECTURE", "verified", indep=2, families=["anthropic"])))
    check("verified w/ single FAMILY refused", code == al.CODE_INVARIANT, f"code={code}")

    # falsification gate: promote to CORROBORATED without passing it
    al.append_claim(ledger2, claim("CLM-B", "y", "CONJECTURE", "unverified"))
    code = refused(lambda: al.append_claim(ledger2, claim("CLM-B", "y", "CORROBORATED", "probable", indep=1, families=["anthropic"])))
    check("promote w/o falsification refused", code == al.CODE_INVARIANT, f"code={code}")

    # 5. Illegal transition: CONJECTURE -> ESTABLISHED (must pass through CORROBORATED).
    print("\n[5] illegal transition refusals (exit 4)")
    al.append_claim(ledger2, claim("CLM-C", "z", "CONJECTURE", "unverified"))
    code = refused(lambda: al.append_claim(ledger2, claim("CLM-C", "z", "ESTABLISHED", "verified",
                                                          indep=2, families=["a", "b"], falsification="passed")))
    check("CONJECTURE->ESTABLISHED refused", code == al.CODE_TRANSITION, f"code={code}")

    # 6. Dependency integrity: ESTABLISH while a dependency is REFUTED.
    print("\n[6] dependency integrity (exit 3)")
    ledger3 = os.path.join(tmp, "claims3.jsonl")
    al.append_claim(ledger3, claim("DEP", "dep claim", "CONJECTURE", "unverified"))
    al.append_claim(ledger3, claim("DEP", "dep claim", "REFUTED", "unverified"))
    al.append_claim(ledger3, claim("MAIN", "main claim", "CONJECTURE", "unverified"))
    al.append_claim(ledger3, claim("MAIN", "main claim", "CORROBORATED", "probable", indep=2, families=["a", "b"], falsification="passed"))
    code = refused(lambda: al.append_claim(ledger3, claim("MAIN", "main claim", "ESTABLISHED", "verified",
                                                          indep=2, families=["a", "b"], falsification="passed", depends_on=["DEP"])))
    check("ESTABLISH w/ REFUTED dependency refused", code == al.CODE_INVARIANT, f"code={code}")

    # 7. Resumable frontier is a pure function of disk state.
    print("\n[7] pure-function resumable frontier")
    f1 = al.compute_frontier(al.read_ledger(ledger3))
    f2 = al.compute_frontier(al.read_ledger(ledger3))          # simulate kill + re-read
    check("frontier deterministic across re-read", f1 == f2)
    check("REFUTED DEP is terminal, not settled", "DEP" in f1["terminal"])
    check("MAIN (corroborated, 2 sources) is a promotion candidate", "MAIN" in f1["needs_corroboration"])

    # 8. Renderer emits the prominent sections.
    print("\n[8] renderer")
    ledger4 = os.path.join(tmp, "claims4.jsonl")
    al.append_claim(ledger4, claim("V1", "Water is wet.", "CONJECTURE", "probable", indep=1, families=["a"], falsification="passed"))
    al.append_claim(ledger4, claim("V1", "Water is wet.", "CORROBORATED", "probable", indep=1, families=["a"], falsification="passed"))
    al.append_claim(ledger4, claim("V1", "Water is wet.", "ESTABLISHED", "verified", indep=2, families=["a", "b"], falsification="passed"))
    al.append_claim(ledger4, claim("K1", "It rained Tuesday.", "CONJECTURE", "unverified"))
    al.append_claim(ledger4, claim("K1", "It rained Tuesday.", "CONTESTED", "unverified",
                                   alternatives=[{"statement": "It rained Monday.", "why_not_adopted": "weaker source"}]))
    md = al.render_markdown(al.read_ledger(ledger4), question="Test question")
    check("renders UNRESOLVED CONFLICTS section", "## UNRESOLVED CONFLICTS" in md)
    check("renders OPEN QUESTIONS section", "## OPEN QUESTIONS" in md)
    check("renders SUPERSESSION LOG section", "## SUPERSESSION LOG" in md)
    check("shows the verified claim", "Water is wet." in md and "Verified" in md)
    check("shows the contested alternative", "It rained Monday." in md)
    check("front-matter carries ledger_head", "ledger_head: sha256-" in md)

    print(f"\n==== {PASS} passed, {FAIL} failed ====")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
