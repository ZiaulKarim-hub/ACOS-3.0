#!/usr/bin/env python3
"""
verdict.py — C3: the DETERMINISTIC committee verdict (no LLM, ever).

Reads the resolved, hash-chained ledger (`<session>/ledger/claims.jsonl`) and the Axis-S
side-channel (`<session>/synthesis/severity-map.json`) and computes the verdict purely by
rule. The verdict WORD is read off the ledger by predicate — it is never narrated by a
model. Re-running over the same ledger yields a byte-identical verdict.json (NFR-3).

--- The deal-breaker predicate (derived AFTER truth settles; tech_prd §1.5) ----------
Per objection:
  deal_breaker = (claim.state in {ESTABLISHED, CORROBORATED})
                 AND (axis_s in {material-risk, deal-breaker-candidate})
                 AND (no mitigant fact that depends_on this objection reached
                      {CORROBORATED, ESTABLISHED})
"Is it true" (engine/mechanical, from the ledger state) stays separate from "is it fatal"
(domain, from Axis S + surviving mitigants).

--- The overall verdict (asymmetric-veto on deal-breakers) --------------------------
  any surviving deal_breaker                       -> DECLINE   (asymmetric veto: a single
                                                                 unmitigated fatal risk vetoes)
  else a material objection is CONTESTED (truth     -> UNRESOLVED (no deciding rung — refuse
       genuinely unresolved, no deciding rung)                    to fabricate a proceed)
  else deal-breakers all mitigated but material     -> PROCEED-WITH-CONDITIONS
       risk remains (conditions = surviving             (conditions = the surviving mitigant
       mitigants retiring those risks)                   facts that retire the material risks)
  else nothing material survives                    -> PROCEED

The per-discipline roll-up is formalized through the vendored resolve.resolve_conflict()
with polarity="asymmetric_veto" (each objection-raising seat votes DECLINE if it holds a
surviving deal-breaker, else PROCEED; a single DECLINE vetoes). The Deal Advocate (#9)
raises no objection and casts NO scrutiny vote, so it is NOT in the roll-up — its only
influence is indirect, via whether its mitigant facts reached CORROBORATED+ during falsify.

Stdlib only. Python 3.8+.
"""

import argparse
import json
import os
import sys

_ENGINE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "synthesis", "scripts")
sys.path.insert(0, _ENGINE_DIR)

import axiom_ledger as al           # noqa: E402  (read the ledger with engine conventions)
import resolve as rs                # noqa: E402  (asymmetric-veto roll-up)

_COUNTS = {"ESTABLISHED", "CORROBORATED"}          # a claim/mitigant "counts" at these states
_MATERIAL = {"material-risk", "deal-breaker-candidate"}
# Kill-criteria (F1 guardrail). Risk categories where a CORROBORATED objection is UN-MITIGABLE:
# a document-request condition cannot cure fabrication, so a kill finding vetoes even if a
# mitigant reached CORROBORATED. Project-tunable; fraud/misrepresentation is the default — this
# is the teeth behind the ROCO normalized-NOI tripwire (a fabricated income figure is not a
# "condition precedent to obtain a T-12"; it is a reason to walk).
_KILL_CATEGORIES = {"Fraud/Misrepresentation"}


def _current(records):
    return al.current_states(records)


def compute(session_dir):
    ledger = os.path.join(session_dir, "ledger", "claims.jsonl")
    sev_path = os.path.join(session_dir, "synthesis", "severity-map.json")
    with open(sev_path, "r", encoding="utf-8") as fh:
        severity = json.load(fh)

    cur = _current(al.read_ledger(ledger))
    ledger_head = al.ledger_head(ledger)

    # reverse-dependency: objection_id -> [mitigant facts that depend_on it]
    mitigants_of = {}
    for cid, rec in cur.items():
        for dep in (rec.get("depends_on") or []):
            mitigants_of.setdefault(dep, []).append(cid)

    # objections = the facts carrying an Axis-S entry (the C1 objection contract).
    objections = []
    for oid, sev in severity.items():
        rec = cur.get(oid)
        state = rec.get("state") if rec else "MISSING"
        axis_s = sev.get("axis_s")
        mits = []
        surviving_mit = []
        for mid in mitigants_of.get(oid, []):
            mstate = cur.get(mid, {}).get("state", "MISSING")
            mits.append({"mitigant_id": mid, "state": mstate})
            if mstate in _COUNTS:
                surviving_mit.append(mid)
        mitigated = len(surviving_mit) > 0
        is_material = axis_s in _MATERIAL
        covers = (rec or {}).get("covers") or []
        # Kill finding: a CORROBORATED objection in an un-mitigable category. It vetoes even when
        # a mitigant survives — you cannot condition away fabrication.
        is_kill = (state in _COUNTS) and bool(set(covers) & _KILL_CATEGORIES)
        deal_breaker = (state in _COUNTS) and is_material and (not mitigated or is_kill)
        objections.append({
            "objection_id": oid,
            "state": state,
            "axis_s": axis_s,
            "raised_by_seat": sev.get("raised_by_seat"),
            "is_material": is_material,
            "is_kill": is_kill,
            "covers": covers,
            "mitigated": mitigated,
            "mitigants": mits,
            "surviving_mitigants": surviving_mit,
            "deal_breaker": deal_breaker,
            "contested": state == "CONTESTED",
        })

    deal_breakers = [o for o in objections if o["deal_breaker"]]
    kill_findings = [o for o in objections if o["is_kill"]]
    contested_material = [o for o in objections if o["is_material"] and o["contested"]]
    material_survivors = [o for o in objections
                          if o["is_material"] and o["state"] in _COUNTS and not o["deal_breaker"]]

    # --- formal asymmetric-veto roll-up over per-seat objection votes -----------
    votes_by_seat = {}
    for o in objections:
        seat = o["raised_by_seat"]
        vote = "DECLINE" if o["deal_breaker"] else "PROCEED"
        # a seat votes DECLINE if ANY of its objections is a surviving deal-breaker
        if votes_by_seat.get(seat) != "DECLINE":
            votes_by_seat[seat] = vote
    rollup_claims = [{"value": v, "seat": s} for s, v in sorted(votes_by_seat.items(), key=lambda kv: str(kv[0]))]
    rollup = rs.resolve_conflict(rollup_claims, polarity="asymmetric_veto") if rollup_claims else \
        {"status": "trivial", "reason": "no objections raised", "deciding_rung": None}

    # --- deterministic decision -------------------------------------------------
    surviving_conditions = sorted({mid for o in material_survivors for mid in o["surviving_mitigants"]})
    if deal_breakers:
        verdict = "DECLINE"
        polarity = "asymmetric_veto"
        decided_by = [o["objection_id"] for o in deal_breakers]
        rationale = ("asymmetric veto: {} surviving deal-breaker(s) with no CORROBORATED+ mitigant "
                     "-> a single unmitigated fatal risk declines the deal".format(len(deal_breakers)))
        if kill_findings:
            rationale += ("; {} UN-MITIGABLE kill-criteria finding(s) (categories {}) veto "
                          "regardless of any proposed mitigant".format(
                              len(kill_findings), sorted(_KILL_CATEGORIES)))
        surviving_conditions = []
    elif contested_material:
        verdict = "UNRESOLVED"
        polarity = "quorum"
        decided_by = [o["objection_id"] for o in contested_material]
        rationale = ("a material objection is CONTESTED with no deciding rung — refusing to "
                     "fabricate a PROCEED (truth genuinely unresolved)")
        surviving_conditions = []
    elif material_survivors:
        verdict = "PROCEED-WITH-CONDITIONS"
        polarity = "quorum"
        decided_by = [o["objection_id"] for o in material_survivors]
        rationale = ("no surviving deal-breakers; {} material risk(s) remain but each is retired "
                     "by a CORROBORATED+ mitigant -> proceed subject to those conditions".format(
                         len(material_survivors)))
    else:
        verdict = "PROCEED"
        polarity = "quorum"
        decided_by = []
        rationale = "no material risk survives at CORROBORATED+ and no deal-breaker -> clean proceed"

    result = {
        "verdict": verdict,
        "polarity": polarity,
        "rationale": rationale,
        "decided_by": decided_by,
        "deal_breakers": [o["objection_id"] for o in deal_breakers],
        "kill_findings": [o["objection_id"] for o in kill_findings],
        "surviving_conditions": surviving_conditions,
        "contested": [o["objection_id"] for o in objections if o["contested"]],
        "rollup": {"votes_by_seat": votes_by_seat, "resolve_status": rollup["status"],
                   "resolve_reason": rollup.get("reason"), "deciding_rung": rollup.get("deciding_rung")},
        "objection_trace": objections,
        "ledger_head": ledger_head,
    }
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description="Compute the deterministic IC verdict from the ledger + Axis S.")
    ap.add_argument("--session", required=True, help="IC session directory")
    ap.add_argument("--print-only", action="store_true", help="print without writing verdict.json")
    args = ap.parse_args(argv)

    res = compute(args.session)
    if not args.print_only:
        out_path = os.path.join(args.session, "verdict.json")
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=2, sort_keys=True, ensure_ascii=False)
        print("wrote {}".format(out_path))
    print("VERDICT: {}  (polarity={})".format(res["verdict"], res["polarity"]))
    print("  rationale: {}".format(res["rationale"]))
    print("  decided_by: {}".format(res["decided_by"]))
    print("  deal_breakers: {}".format(res["deal_breakers"]))
    print("  kill_findings (un-mitigable): {}".format(res["kill_findings"]))
    print("  surviving_conditions: {}".format(res["surviving_conditions"]))
    print("  ledger_head: {}".format(res["ledger_head"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
