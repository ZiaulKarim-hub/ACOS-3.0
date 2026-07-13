#!/usr/bin/env python3
"""
run_synthesis.py — C2: drive the VENDORED axiom-synthesis engine over the IC facts.

Loads `<session>/synthesis/facts.json` (built by C1) and runs the vendored
orchestrate.run() pipeline (stages 2->7: de-circularize -> grade -> fuse -> falsify ->
resolve -> hash-chained ledger) over every fact, writing the append-only, hash-chained
ledger to `<session>/ledger/claims.jsonl` (+ source-of-truth.md, settled-objections.jsonl).

The Deal Advocate's mitigant facts are ordinary `fact` dicts in facts.json, so they pass
through orchestrate.process_fact() and the SAME falsification gate as every objection —
no special-casing here. A mitigant only reaches CORROBORATED+ (and therefore "counts"
downstream in C3) if it carries traceable documentary evidence; an aspirational mitigant
with no origin stays CONJECTURE.

--- ENGINE INVOCATION (the layout trap) ---------------------------------------------
The vendored engine modules import each other by BARE name (import axiom_ledger, etc.)
and live in `./synthesis/scripts/` relative to this file. We must put THAT directory on
sys.path before importing orchestrate; we import ONLY from the local vendored copy and
NEVER from `.claude/skills/acos-axiom-synthesis/` (no runtime dependency on the source
skill — the IC skill is standalone by design, tech_prd §1.4).

--- SEAM (model-produced fields) ----------------------------------------------------
orchestrate consumes fact["refuter"] = {objection, credible, rebutted} and fact["flags"]
= {<trigger>: bool}. Those are produced UPSTREAM by Task()-spawned DIFFERENT-discipline
refuter agents in the live skill; C1 passes them onto the fact when the seat file supplies
them, else they default to None / {} (a clean gate). This driver is unchanged whether the
fields are stubbed (smoke) or agent-filled (production) — the call structure is the seam.

--- Axis S orthogonality ------------------------------------------------------------
Axis S lives only in `<session>/synthesis/severity-map.json` and is NEVER passed into the
engine here. Truth-grading cannot see it; it rides alongside.

Stdlib only. Python 3.8+.
"""

import argparse
import json
import os
import sys

# --- put the vendored engine dir on sys.path (bare-name imports; local copy only) ---
_ENGINE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "synthesis", "scripts")
sys.path.insert(0, _ENGINE_DIR)

import orchestrate as orch          # noqa: E402  (vendored copy only)
import axiom_ledger as al           # noqa: E402


def _sub_questions(facts):
    """Coverage-gate facets = the union of every OBJECTION's `covers` tags (16-risk map).
    Mitigant facts carry no coverage assertion of their own."""
    sqs = []
    for f in facts:
        if f.get("depends_on"):        # a mitigant (depends_on an objection) covers nothing itself
            continue
        for c in f.get("covers", []) or []:
            if c not in sqs:
                sqs.append(c)
    return sqs or ["_uncategorized"]


def run(session_dir, question="IC synthesis", now="1970-01-01T00:00Z",
        date_str="1970-01-01", session="ic"):
    facts_path = os.path.join(session_dir, "synthesis", "facts.json")
    with open(facts_path, "r", encoding="utf-8") as fh:
        facts = json.load(fh)["facts"]

    ledger_dir = os.path.join(session_dir, "ledger")
    os.makedirs(ledger_dir, exist_ok=True)
    subqs = _sub_questions(facts)

    # FRESH REBUILD (idempotency, 2026-07-09). run_synthesis regenerates the ledger
    # deterministically from facts.json, so any prior artifacts from an earlier invocation
    # MUST be cleared first. Otherwise orchestrate.run APPENDS to claims.jsonl (stacking stale
    # state versions — current_states is last-line-wins, so re-runs silently mix runs) AND the
    # oscillation guard reads a prior run's settled-objections, treating THIS run's refuters as
    # already-settled and suppressing them. Clearing makes re-running a true rebuild.
    for _stale in ("claims.jsonl", "settled-objections.jsonl", "source-of-truth.md"):
        _p = os.path.join(ledger_dir, _stale)
        if os.path.exists(_p):
            os.remove(_p)

    # orchestrate.run writes claims.jsonl into its session_dir -> point it at ledger/.
    out = orch.run(ledger_dir, question, subqs, facts, now=now,
                   repo_root=session_dir, date_str=date_str, session=session)

    # per-fact final states, split objections vs mitigants for the summary
    obj_ids = {f["fact_id"] for f in facts if not f.get("depends_on")}
    per_fact = {r["fact_id"]: r["final_state"] for r in out["per_fact"]}
    decirc_flags = []
    for r in out["per_fact"]:
        for fl in r["decirc"].get("flags", []):
            decirc_flags.append("{}: {}".format(r["fact_id"], fl))

    summary = out["summary"]
    print("=== run_synthesis (vendored engine, stages 2-7) ===")
    print("ledger:        {}".format(out["ledger"]))
    print("facts:         {} ({} objections, {} mitigants)".format(
        summary["facts"], len(obj_ids), summary["facts"] - len(obj_ids)))
    print("final states:  {}".format(summary["states"]))
    print("chain_intact:  {}".format(summary["chain_intact"]))
    print("ledger_head:   {}".format(summary["ledger_head"]))
    print("coverage_ok:   {}  (uncovered: {})".format(summary["coverage_ok"], summary["uncovered"]))
    print("reduced-independence / de-circularization flags:")
    if decirc_flags:
        for fl in decirc_flags:
            print("   - {}".format(fl))
    else:
        print("   (none)")
    print("per-fact:")
    for f in facts:
        kind = "MITIGANT (depends_on {})".format(f["depends_on"][0]) if f.get("depends_on") else "objection"
        print("   {:<28} {:<24} [{}]".format(f["fact_id"], per_fact.get(f["fact_id"], "?"), kind))

    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run the vendored axiom-synthesis engine over IC facts.")
    ap.add_argument("--session", required=True, help="IC session directory (contains synthesis/facts.json)")
    ap.add_argument("--question", default="Should the committee approve this deal?")
    ap.add_argument("--now", default="1970-01-01T00:00Z", help="ISO timestamp for ledger stamping")
    ap.add_argument("--date", default="1970-01-01", help="date_str for the ACOS mirror")
    ap.add_argument("--session-name", default="ic", help="session label for the ACOS mirror")
    args = ap.parse_args(argv)
    run(args.session, question=args.question, now=args.now,
        date_str=args.date, session=args.session_name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
