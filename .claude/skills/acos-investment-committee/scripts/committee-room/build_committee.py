#!/usr/bin/env python3
"""Build the Swiss "committee room" (concept-08 lineage) from a real IC session.

Reads a completed session directory and emits a self-contained HTML room whose
COMMITTEE data object is populated from the actual on-disk artifacts:

  - deal      : from deal-brief/deal-brief.yaml
  - scrutiny  : seats 1-8 (rounds/round-NN/seat-0N.json) — each with a derived
                vote, an emotion, its SHARPEST objection as the headline opinion,
                and its FULL objection list (for the drill-down drawer)
  - advocate  : seat 9 (Deal Advocate) — headline mitigant
  - vote      : {for, against} where a seat counts AGAINST iff it holds an
                un-mitigated DEAL-BREAKER (Disqualifying) objection (the same
                signal that drives the asymmetric-veto verdict)
  - leaning   : the computed verdict word from verdict.json

Research-thread counts reflect real research breadcrumbs
(rounds/round-NN/research/seat-NN.json) when present, else 0 — unless
--demo-research seeds illustrative counts for a design-review view.

Usage:
  python3 build_committee.py --session <dir> [--out <file.html>] [--demo-research]
Stdlib only.
"""
import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TEMPLATE = os.path.join(HERE, "room_swiss_template.html")

SEAT_SHORT = {
    1: "Credit", 2: "Finance", 3: "Accounting", 4: "Legal", 5: "Insurance",
    6: "Fraud", 7: "Portfolio", 8: "Strategy", 9: "Advocate",
    11: "Construction", 12: "Tax", 13: "Market", 14: "Compliance", 15: "Environmental",
}

SEVERITY_MAP = {
    "deal-breaker-candidate": "disqualifying", "deal-breaker": "disqualifying",
    "material-risk": "material", "material": "material", "material-conditioned": "material",
    "limitation": "monitor", "monitor": "monitor",
    "informational": "info", "info": "info",
}
SEV_RANK = {"disqualifying": 4, "material": 3, "monitor": 2, "info": 1, "unscored": 0}
SEV_EMOJI = {"disqualifying": "\U0001F620", "material": "\U0001F61F", "monitor": "\U0001F914",
             "info": "\U0001F914", "unscored": "\U0001F610"}

DEMO_THREADS = {
    1: [
        {"topic": "Pull Boise 6-unit multifamily cap-rate comps (trailing 12 mo) to test the implied 65% LTV value.", "status": "running"},
        {"topic": "Find arm's-length sales for 1420 Alder St and adjacent parcels to corroborate the $1.45M basis.", "status": "running"},
    ],
    2: [
        {"topic": "Survey current 18-month bridge take-out refinance rates and availability for sub-1.0x DSCR multifamily.", "status": "running"},
    ],
    3: [
        {"topic": "Benchmark operating-expense ratios for 6-unit Boise multifamily to test the implied ~9.5% opex load.", "status": "running"},
        {"topic": "Locate any T-12 or county tax-assessor operating data to reconcile the reported $92k / $101k NOI.", "status": "running"},
        {"topic": "Check whether the $9k add-back to 'normalized' NOI ties to any documented one-time item.", "status": "done", "finding": "No add-back schedule found in the dataroom — uplift is unsupported."},
    ],
    4: [
        {"topic": "Search Ada County records for existing deeds of trust and liens on 1420 Alder St.", "status": "running"},
        {"topic": "Verify 1420 Alder SPE LLC formation and good standing with the Idaho Secretary of State.", "status": "running"},
    ],
    5: [
        {"topic": "Assess Boise / Ada County wildfire and flood-zone exposure and the current habitational insurance market.", "status": "running"},
    ],
    6: [
        {"topic": "Search litigation, judgment, and bankruptcy records for Marcus T. Whitfield and Alder Street Partners LLC.", "status": "running"},
        {"topic": "Corroborate the sponsor's claimed 640-unit / 3-prior-loan track record against public records.", "status": "running"},
    ],
    7: [
        {"topic": "Pull the OKOA-FUND-II loan tape to test sponsor, geographic, and maturity concentration limits.", "status": "running"},
    ],
    8: [
        {"topic": "Compare this deal's terms against OKOA's stated secured-lender mandate and recent originations.", "status": "running"},
    ],
    9: [
        {"topic": "Identify the strongest curable conditions (appraisal, audited T-12, title policy) that could de-risk the deal.", "status": "running"},
    ],
}


def strip_scalar(v):
    v = v.strip()
    if len(v) >= 2 and v[0] in "\"'" and v[-1] == v[0]:
        v = v[1:-1]
    return v


def parse_deal_brief(path):
    out, section = {}, None
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            line = raw.strip()
            if indent == 0 and line.endswith(":"):
                section = line[:-1].strip()
                continue
            if line.startswith("- "):
                continue
            if ":" in line:
                k, _, v = line.partition(":")
                v = strip_scalar(v)
                if v:
                    out[(section, k.strip())] = v
    return out


def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return default if default is not None else {}


def severity_of(axis_s):
    if not axis_s:
        return "unscored"
    return SEVERITY_MAP.get(str(axis_s).strip().lower(), "material")


def norm_evidence(raw):
    out = []
    for e in (raw or []):
        if isinstance(e, dict):
            out.append({"citation": e.get("citation", "") or e.get("source", ""),
                        "locator": e.get("locator", ""),
                        "text": e.get("text", "") or e.get("quote", "")})
        else:
            out.append({"citation": "", "locator": "", "text": str(e)})
    return out


def headline(statement, limit=190):
    """Strip a leading [BRACKET] tag; take the first sentence or a clean truncation."""
    s = re.sub(r"^\s*\[[^\]]*\]\s*", "", (statement or "").strip())
    if len(s) <= limit:
        return s
    # prefer first sentence boundary within limit
    cut = s[:limit]
    m = re.search(r"[.;:]\s", cut)
    if m and m.end() > 60:
        return cut[:m.start() + 1]
    return cut.rsplit(" ", 1)[0].rstrip(",;:") + "…"


def research_threads(session, seat_n, demo):
    """Real research breadcrumbs (rounds/*/research/seat-NN.json -> bots[]) or demo threads."""
    if demo:
        return [dict(t) for t in DEMO_THREADS.get(seat_n, [])]
    threads = []
    for path in sorted(glob.glob(os.path.join(session, "rounds", "round-*", "research", f"seat-{seat_n:02d}.json"))):
        d = load_json(path, {})
        for b in d.get("bots", []) or []:
            threads.append({
                "topic": b.get("question", "") or b.get("topic", ""),
                "status": b.get("status", "running"),
                "finding": b.get("result_one_line", "") or b.get("finding", ""),
            })
    return threads


def norm_mitigants(o):
    """Per-objection suggested cures. New format = suggested_mitigants[]; fall back to
    a single mitigant_hypothesis (older seat files)."""
    raw = o.get("suggested_mitigants")
    if not raw:
        mh = o.get("mitigant_hypothesis")
        raw = [mh] if mh else []
    out = []
    for m in raw:
        if isinstance(m, dict):
            out.append({
                "statement": m.get("statement", "") or m.get("text", ""),
                "type": m.get("mitigant_type", "") or m.get("type", ""),
                "residual": m.get("residual_risk", "") or m.get("residual", ""),
            })
        elif m:
            out.append({"statement": str(m), "type": "", "residual": ""})
    return out


def seat_objections(d):
    objs = []
    for o in d.get("objections", []) or []:
        stmt = o.get("statement", "")
        objs.append({
            "objection_id": o.get("objection_id", ""),
            "question": o.get("question", "") or headline(stmt, 150),
            "statement": stmt,
            "severity": severity_of(o.get("axis_s")),
            "evidence": norm_evidence(o.get("evidence")),
            "mitigants": norm_mitigants(o),
        })
    # sharpest first
    objs.sort(key=lambda o: SEV_RANK.get(o["severity"], 0), reverse=True)
    return objs


def build_committee(session, demo):
    brief = parse_deal_brief(os.path.join(session, "deal-brief", "deal-brief.yaml"))
    g = lambda s, k: brief.get((s, k), "")
    verdict = load_json(os.path.join(session, "verdict.json"), {})

    scrutiny, vote_for, vote_against = [], 0, 0
    for n in range(1, 9):
        files = sorted(glob.glob(os.path.join(session, "rounds", "round-*", f"seat-{n:02d}.json")))
        if not files:
            continue
        d = load_json(files[-1], {})
        objs = seat_objections(d)
        max_sev = max((SEV_RANK.get(o["severity"], 0) for o in objs), default=0)
        sev_name = next((k for k, v in SEV_RANK.items() if v == max_sev), "unscored")
        has_dealbreaker = any(o["severity"] == "disqualifying" for o in objs)
        vote = "against" if has_dealbreaker else "for"
        vote_against += 1 if vote == "against" else 0
        vote_for += 1 if vote == "for" else 0
        threads = research_threads(session, n, demo)
        scrutiny.append({
            "n": n,
            "name": d.get("seat_name", SEAT_SHORT.get(n, f"Seat {n}")),
            "short": SEAT_SHORT.get(n, d.get("seat_name", f"Seat {n}")),
            "vote": vote,
            "emoji": SEV_EMOJI.get(sev_name, "\U0001F610"),
            "research": len(threads),
            "threads": threads,
            "opinion": objs[0]["question"] if objs else "No objection recorded.",
            "objections": objs,
        })

    asset = g("deal_meta", "asset_type")
    addr = g("collateral", "address")
    sub_bits = [b for b in [asset, addr] if b]
    sub = " · ".join(sub_bits + ["8 voting scrutiny seats"])

    return {
        "deal": {
            "name": g("deal_meta", "name") or "Investment Committee",
            "amount": g("loan_terms", "loan_amount") or "",
            "ltv": g("loan_terms", "ltv") or "",
            "leaning": verdict.get("verdict", "UNRESOLVED"),
            "sub": sub,
        },
        "vote": {"for": vote_for, "against": vote_against},
        "scrutiny": scrutiny,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--template", default=DEFAULT_TEMPLATE)
    ap.add_argument("--demo-research", action="store_true",
                    help="seed illustrative research-thread counts (design-review view)")
    args = ap.parse_args()

    session = os.path.abspath(args.session)
    if not os.path.isdir(session):
        print(f"ERROR: session dir not found: {session}", file=sys.stderr)
        sys.exit(1)

    committee = build_committee(session, args.demo_research)
    with open(args.template, encoding="utf-8") as fh:
        tpl = fh.read()
    payload = json.dumps(committee, ensure_ascii=False).replace("</", "<\\/")
    html = tpl.replace("/*__COMMITTEE_JSON__*/null", payload)

    out = args.out or os.path.join(session, "committee-room.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)

    print(json.dumps({
        "ok": True, "out": out,
        "seats": len(committee["scrutiny"]),
        "vote": committee["vote"],
        "verdict": committee["deal"]["leaning"],
        "demo_research": args.demo_research,
    }))


if __name__ == "__main__":
    main()
