#!/usr/bin/env python3
"""
render_memo.py — C4: render the 13-section IC memo, projected FROM the ledger.

Reads the hash-chained ledger (`<session>/ledger/claims.jsonl`), the Axis-S side-channel
(`<session>/synthesis/severity-map.json`), the mitigant metadata
(`<session>/synthesis/mitigant-map.json`), and the deterministic verdict
(`<session>/verdict.json`), and writes `<session>/ic-memo.md`.

The memo is a PROJECTION of the ledger, never authored prose (`rendered_from_ledger: true`).
The BLUF verdict box mirrors verdict.json exactly. Extends the vendored render.py convention
(read the ledger with axiom_ledger.current_states; group by section).

13-section canon (tech_prd §1.6) + a DEAL-BREAKERS section + an UNRESOLVED section:
  1 VERDICT box (BLUF) | 2 Executive Summary | 3 Transaction/Loan Summary |
  4 Sponsor & Guarantor | 5 Collateral & Valuation | 6 Market | 7 Financial Analysis |
  8 Sensitivities/Downside | 9 Risks & Mitigants (Risk->Mitigant->Residual triplet) |
  10 Structure & Covenants | 11 Conditions Precedent (each CP tagged to the risk it retires) |
  12 Legal/Title/Environmental | 13 Exit/Repayment | Recommendation (+ Key Judgment Calls).

Every triplet row carries a NON-EMPTY residual (bare "Mitigated" is disallowed): an
objection with no surviving mitigant shows the risk standing in full.

Stdlib only. Python 3.8+.
"""

import argparse
import json
import os
import sys

_ENGINE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "synthesis", "scripts")
sys.path.insert(0, _ENGINE_DIR)

import axiom_ledger as al           # noqa: E402  (extends render.py conventions)

_COUNTS = {"ESTABLISHED", "CORROBORATED"}
_MATERIAL = {"material-risk", "deal-breaker-candidate"}

# 16-risk category -> narrative section key.
_CATEGORY_SECTION = {
    "Credit/Borrower": "financial", "Cash-Flow/DSCR": "financial",
    "Concentration/Portfolio": "financial",
    "Collateral/Valuation": "collateral", "Construction/Completion": "collateral",
    "Market/Macro": "market",
    "Sponsor/Track-Record": "sponsor", "Fraud/Misrepresentation": "sponsor",
    "Structural/Legal": "legal", "Title/Survey": "legal", "Tax": "legal",
    "Regulatory/Compliance": "legal", "Environmental": "legal",
    "ESG/Physical-Climate": "sensitivities", "Insurance": "sensitivities",
    "Interest-Rate/Refi/Exit": "exit",
}


def _tier(axis_s, state, deal_breaker, mitigated):
    """4-tier plain-English severity language (tech_prd §1.6)."""
    if deal_breaker:
        return "Disqualifying"
    if axis_s in _MATERIAL and mitigated:
        return "Material-Conditioned"
    if axis_s in _MATERIAL:
        return "Mitigated"           # material but not established at CORROBORATED+ -> monitored
    return "Monitor"                 # limitation / informational


def _load(session_dir):
    with open(os.path.join(session_dir, "verdict.json"), "r", encoding="utf-8") as fh:
        verdict = json.load(fh)
    with open(os.path.join(session_dir, "synthesis", "severity-map.json"), "r", encoding="utf-8") as fh:
        severity = json.load(fh)
    with open(os.path.join(session_dir, "synthesis", "mitigant-map.json"), "r", encoding="utf-8") as fh:
        mit_map = json.load(fh)
    cur = al.current_states(al.read_ledger(os.path.join(session_dir, "ledger", "claims.jsonl")))
    return verdict, severity, mit_map, cur


def render(session_dir):
    verdict, severity, mit_map, cur = _load(session_dir)
    trace = {o["objection_id"]: o for o in verdict.get("objection_trace", [])}

    # CP numbering: one CP per surviving condition, tagged to the risk it retires.
    cp_by_mit = {}
    cps = []
    for i, mid in enumerate(verdict.get("surviving_conditions", []), 1):
        meta = mit_map.get(mid, {})
        cp_id = "CP-{}".format(i)
        cp_by_mit[mid] = cp_id
        cps.append({"cp_id": cp_id, "mitigant_id": mid, "retires": meta.get("retires"),
                    "text": meta.get("statement", ""), "type": meta.get("mitigant_type", "")})

    # Build a per-objection view for the triplet table + section routing.
    rows = []
    for oid, sev in severity.items():
        rec = cur.get(oid, {})
        o = trace.get(oid, {})
        axis_s = sev.get("axis_s")
        deal_breaker = o.get("deal_breaker", False)
        mitigated = o.get("mitigated", False)
        surviving = o.get("surviving_mitigants", [])
        all_mits = o.get("mitigants", [])

        if surviving:
            mit_texts = [mit_map.get(m, {}).get("statement", m) for m in surviving]
            residuals = [mit_map.get(m, {}).get("residual_risk", "").strip() for m in surviving]
            residuals = [r for r in residuals if r]
            residual = " ".join(residuals) if residuals else \
                "Mitigant reached CORROBORATED+ but no residual was stated by the raising seat (author must supply)."
            cp_refs = [cp_by_mit[m] for m in surviving if m in cp_by_mit]
        elif all_mits:
            mit_texts = ["Proposed but UNPROVEN (did not reach CORROBORATED): "
                         + mit_map.get(m["mitigant_id"], {}).get("statement", m["mitigant_id"]) for m in all_mits]
            residual = ("Proposed mitigant is aspirational/undocumented (stayed {}); the risk is "
                        "NOT retired.".format("/".join(sorted({m["state"] for m in all_mits}))))
            cp_refs = []
        else:
            mit_texts = ["None proposed"]
            if deal_breaker:
                residual = "Unmitigated — the risk stands in full (Disqualifying)."
            elif axis_s in _MATERIAL:
                residual = "Risk not established at CORROBORATED+; carry as a monitored exposure."
            else:
                residual = "Accepted as a {}; residual = ongoing monitoring item.".format(
                    "limitation" if axis_s == "limitation" else "note")
            cp_refs = []

        rows.append({
            "oid": oid, "statement": rec.get("statement", oid), "state": rec.get("state", "?"),
            "axis_s": axis_s, "raised_by_seat": sev.get("raised_by_seat"),
            "tier": _tier(axis_s, rec.get("state"), deal_breaker, mitigated),
            "deal_breaker": deal_breaker, "mitigated": mitigated,
            "mitigant_text": "; ".join(mit_texts), "residual": residual, "cp_refs": cp_refs,
            "section": _section_for(sev, rec),
        })

    reduced_independence = _reduced_independence(cur)
    lines = _compose(session_dir, verdict, rows, cps, cur, mit_map, reduced_independence)
    out_path = os.path.join(session_dir, "ic-memo.md")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return {"path": out_path, "sections": 13, "triplet_rows": len(rows), "cps": len(cps)}


def _section_for(sev, rec):
    for c in (rec.get("covers") or []):
        if c in _CATEGORY_SECTION:
            return _CATEGORY_SECTION[c]
    return "exec"


def _reduced_independence(cur):
    fams = set()
    for rec in cur.values():
        for p in (rec.get("provenance") or []):
            if p.get("family"):
                fams.add(p["family"])
    return len(fams) < 2


def _rows_for(rows, section):
    return [r for r in rows if r["section"] == section]


def _section_block(rows, section, title, empty="_No committee findings recorded in this category._"):
    out = ["## {}".format(title), ""]
    sel = _rows_for(rows, section)
    if not sel:
        out.append(empty)
    else:
        for r in sel:
            out.append("- **[{tier} · {state}]** {statement}  `({oid}, seat #{seat})`".format(
                tier=r["tier"], state=r["state"], statement=r["statement"],
                oid=r["oid"], seat=r["raised_by_seat"]))
    out.append("")
    return out


def _compose(session_dir, verdict, rows, cps, cur, mit_map, reduced_independence):
    v = verdict["verdict"]
    L = []
    # front-matter
    L += ["---",
          "artifact: ic-memo",
          "rendered_from_ledger: true",
          "verdict: {}".format(v),
          "polarity: {}".format(verdict.get("polarity")),
          "ledger_head: {}".format(verdict.get("ledger_head")),
          "reduced_independence: {}".format(str(reduced_independence).lower()),
          "confidence_tiers:",
          "  verified: \">=2 distinct-family sources AND >=2 independent sources\"",
          "  probable: \"single-source OR single-family agreement\"",
          "  unverified: \"one source, weak/absent provenance, or contested\"",
          "severity_language: \"Monitor < Mitigated < Material-Conditioned < Disqualifying\"",
          "---", ""]

    # 1. VERDICT box (BLUF)
    L += ["# Investment Committee Recommendation", "",
          "## 1. VERDICT (BLUF)", "",
          "> ## ** {} **".format(v),
          "> ",
          "> - **Polarity:** {}".format(verdict.get("polarity")),
          "> - **Basis:** {}".format(verdict.get("rationale")),
          "> - **Decided by:** {}".format(", ".join(verdict.get("decided_by") or []) or "(none)"),
          "> - **Deal-breakers:** {}".format(", ".join(verdict.get("deal_breakers") or []) or "none"),
          "> - **Conditions:** {}".format(", ".join(verdict.get("surviving_conditions") or []) or "none"),
          "> - **Ledger head:** `{}`".format(verdict.get("ledger_head")),
          ""]
    if reduced_independence:
        L += ["> **INDEPENDENCE NOTE:** reduced independence — sources span <2 distinct "
              "families; corroboration strength is capped accordingly.", ""]

    # 2. Executive Summary
    L += ["## 2. Executive Summary", "",
          "This recommendation is a deterministic projection of the committee's hash-chained "
          "claim ledger (head `{}`); the verdict word is computed by rule, never narrated. "
          "The committee recorded {} scrutiny finding(s); {} reached a settled truth state "
          "(CORROBORATED/ESTABLISHED). {}".format(
              verdict.get("ledger_head"), len(rows),
              sum(1 for r in rows if r["state"] in _COUNTS),
              verdict.get("rationale")),
          ""]
    execs = _rows_for(rows, "exec")
    if execs:
        L += ["Cross-cutting / strategy findings:"]
        for r in execs:
            L.append("- **[{tier} · {state}]** {statement}  `({oid})`".format(**r))
        L.append("")

    # 3-8, 10, 12, 13 narrative sections (ledger projections by risk category)
    L += ["## 3. Transaction / Loan Summary", "",
          "_Terms are carried from the deal-brief; committee findings on the transaction "
          "structure appear in Sections 9-11._", ""]
    L += _section_block(rows, "sponsor", "4. Sponsor & Guarantor")
    L += _section_block(rows, "collateral", "5. Collateral & Valuation")
    L += _section_block(rows, "market", "6. Market")
    L += _section_block(rows, "financial", "7. Financial Analysis")
    L += _section_block(rows, "sensitivities", "8. Sensitivities / Downside")

    # 9. Risks & Mitigants — the repeating Risk -> Mitigant -> Residual triplet table
    L += ["## 9. Risks & Mitigants", "",
          "Every finding is shown as a Risk -> Mitigant -> Residual triplet. A blank residual "
          "is disallowed: an unmitigated risk shows the exposure standing in full.", "",
          "| # | Risk (finding) | Severity | Truth state | Mitigant | Residual risk | CP |",
          "|---|----------------|----------|-------------|----------|---------------|----|"]
    for i, r in enumerate(rows, 1):
        L.append("| {i} | {risk} `({oid})` | {tier} ({axis}) | {state} | {mit} | {res} | {cp} |".format(
            i=i, risk=_cell(r["statement"]), oid=r["oid"], tier=r["tier"], axis=r["axis_s"],
            state=r["state"], mit=_cell(r["mitigant_text"]), res=_cell(r["residual"]),
            cp=", ".join(r["cp_refs"]) or "-"))
    L.append("")

    # 10. Structure & Covenants
    L += ["## 10. Structure & Covenants", "",
          "_Covenant package is carried from the deal-brief; risk-retiring structural controls "
          "are enumerated as Conditions Precedent in Section 11._", ""]

    # 11. Conditions Precedent — each CP tagged to the risk it retires
    L += ["## 11. Conditions Precedent", ""]
    if not cps:
        L += ["_None. " + ("The deal was declined; conditions are moot." if verdict["verdict"] == "DECLINE"
                           else "No surviving mitigant rose to a binding pre-funding condition.") + "_", ""]
    else:
        L += ["Each condition is a surviving (CORROBORATED+) mitigant, tagged to the risk it retires.", "",
              "| CP | Condition | Type | Retires risk | Source mitigant |",
              "|----|-----------|------|--------------|-----------------|"]
        for cp in cps:
            L.append("| {id} | {text} | {typ} | `{ret}` | `{mid}` |".format(
                id=cp["cp_id"], text=_cell(cp["text"]), typ=cp["type"],
                ret=cp["retires"], mid=cp["mitigant_id"]))
        L.append("")

    # 12. Legal / Title / Environmental
    L += _section_block(rows, "legal", "12. Legal / Title / Environmental")

    # 13. Exit / Repayment
    L += _section_block(rows, "exit", "13. Exit / Repayment")

    # DEAL-BREAKERS section
    L += ["## DEAL-BREAKERS", ""]
    dbs = [r for r in rows if r["deal_breaker"]]
    if not dbs:
        L += ["_None surviving._", ""]
    else:
        L += ["The following are CORROBORATED+ material risks with NO surviving mitigant — each "
              "vetoes approval (asymmetric veto):", ""]
        for r in dbs:
            L.append("- **{statement}**  `({oid}, seat #{seat}, {axis}, {state})` — {res}".format(
                statement=r["statement"], oid=r["oid"], seat=r["raised_by_seat"],
                axis=r["axis_s"], state=r["state"], res=r["residual"]))
        L.append("")

    # UNRESOLVED section
    L += ["## UNRESOLVED", ""]
    unresolved = verdict.get("contested") or []
    if not unresolved:
        L += ["_No claim landed CONTESTED; no irreducible conflict was preserved unresolved._", ""]
    else:
        L += ["The following claims are CONTESTED — a comparably-supported contradiction with no "
              "deciding rung; both sides are preserved, no winner fabricated:", ""]
        for oid in unresolved:
            rec = cur.get(oid, {})
            L.append("- **{}**  `({})`".format(rec.get("statement", oid), oid))
            for alt in (rec.get("alternatives") or []):
                L.append("    - alternative: {} — {}".format(
                    alt.get("statement", "?"), alt.get("why_not_adopted", "")))
        L.append("")

    # Recommendation + Key Judgment Calls
    L += ["## Recommendation", "",
          "**{}.** {}".format(v, verdict.get("rationale")), ""]
    if v == "DECLINE":
        L.append("The committee recommends **declining** the transaction as presented. "
                 "See DEAL-BREAKERS above for the vetoing finding(s).")
    elif v == "PROCEED-WITH-CONDITIONS":
        L.append("The committee recommends proceeding **subject to the Conditions Precedent** "
                 "in Section 11; each retires a specific material risk. Residual risks in "
                 "Section 9 are accepted post-condition.")
    elif v == "PROCEED":
        L.append("The committee recommends **proceeding**; no material risk survives at "
                 "CORROBORATED+ and no deal-breaker was found.")
    else:
        L.append("The committee reached **UNRESOLVED**: a material claim is contested with no "
                 "deciding rung. Resolve the contested claim (Section UNRESOLVED) before a "
                 "proceed/decline can be computed.")
    L += ["",
          "### Key Judgment Calls",
          "- Verdict is computed deterministically from ledger state + Axis S; re-running "
          "over the same ledger (head `{}`) reproduces it exactly (NFR-3).".format(verdict.get("ledger_head")),
          "- \"Is it true\" (engine truth state) is kept separate from \"is it fatal\" (Axis-S "
          "materiality + surviving mitigants).",
          "- The Deal Advocate (#9) casts no scrutiny vote; its mitigants influence the verdict "
          "only by whether they reached CORROBORATED+ under the same falsification gate.",
          ""]
    return L


def _cell(text):
    """Escape a value for a Markdown table cell."""
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render the 13-section IC memo from the ledger.")
    ap.add_argument("--session", required=True, help="IC session directory")
    args = ap.parse_args(argv)
    res = render(args.session)
    print("render_memo: wrote {path} ({triplet_rows} triplet rows, {cps} CP(s))".format(**res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
