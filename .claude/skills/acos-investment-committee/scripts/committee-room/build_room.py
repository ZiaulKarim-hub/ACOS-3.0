#!/usr/bin/env python3
"""Build a self-contained "committee room" HTML replay from a completed IC session.

Reads a session directory's deal-brief, per-seat round files, and verdict, and
emits ONE self-contained HTML file (all data embedded inline, no server, no
network) that animates the deliberation as a boardroom: avatars, accreting
speech bubbles, a word-level typing reveal, a speaking-state spotlight, an
honest "Replay" activity bar, and a running verdict panel.

This is the ROOM-FIRST deliverable: the rendering layer is written once here and
is reused unchanged when the data source later swaps from this embedded replay
array to live SSE events off `ic-server.py`.

Usage:
  python3 build_room.py --session <session-dir> [--out <file.html>] [--template <tpl>]

Stdlib only (json + os + re) — no PyYAML dependency.
"""
import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TEMPLATE = os.path.join(HERE, "room_template.html")

# --- Seat presentation metadata (styling only; names/content come from data) ---
# Numbering is stable per roster.yaml — do not renumber.
SEATS = {
    1:  {"short": "Credit & Valuation",      "emoji": "\U0001F4CA", "color": "#E8B04B", "role": "scrutiny"},
    2:  {"short": "Finance",                 "emoji": "\U0001F4B9", "color": "#5AA9E6", "role": "scrutiny"},
    3:  {"short": "Accounting",              "emoji": "\U0001F9EE", "color": "#7FB77E", "role": "scrutiny"},
    4:  {"short": "Legal & Structural",      "emoji": "⚖️", "color": "#C9915B", "role": "scrutiny"},
    5:  {"short": "Insurance & Climate",     "emoji": "\U0001F6E1️", "color": "#6BC5C9", "role": "scrutiny"},
    6:  {"short": "Sponsor & Fraud",         "emoji": "\U0001F575️", "color": "#E86A6A", "role": "scrutiny"},
    7:  {"short": "Portfolio & Concentration","emoji": "\U0001F4DA", "color": "#B08BD9", "role": "scrutiny"},
    8:  {"short": "Strategy",                "emoji": "♟️", "color": "#E0A3C7", "role": "scrutiny"},
    9:  {"short": "Deal Advocate",           "emoji": "\U0001F91D", "color": "#63C088", "role": "advocate"},
    10: {"short": "Gap-Hunter",              "emoji": "\U0001F50D", "color": "#9AA6B2", "role": "procedural"},
    11: {"short": "Construction",            "emoji": "\U0001F3D7️", "color": "#D9A55B", "role": "scrutiny"},
    12: {"short": "Tax",                     "emoji": "\U0001F4B0", "color": "#8FBF6B", "role": "scrutiny"},
    13: {"short": "Market / Macro",          "emoji": "\U0001F30D", "color": "#6BA3D9", "role": "scrutiny"},
    14: {"short": "Compliance",              "emoji": "\U0001F4DC", "color": "#C79BD9", "role": "scrutiny"},
    15: {"short": "Environmental",           "emoji": "\U0001F333", "color": "#79C08A", "role": "scrutiny"},
}

# axis_s (from seat JSON) -> display severity
SEVERITY_MAP = {
    "deal-breaker-candidate": "disqualifying",
    "deal-breaker": "disqualifying",
    "material-risk": "material",
    "material": "material",
    "material-conditioned": "material",
    "limitation": "monitor",
    "monitor": "monitor",
    "informational": "info",
    "info": "info",
}


def strip_scalar(v):
    v = v.strip()
    if len(v) >= 2 and v[0] in "\"'" and v[-1] == v[0]:
        v = v[1:-1]
    return v


def parse_deal_brief(path):
    """Targeted section/key parser for the flat-ish deal-brief.yaml (no PyYAML)."""
    out = {}
    if not os.path.exists(path):
        return out
    section = None
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
                k = k.strip()
                v = strip_scalar(v)
                if v == "":
                    continue
                out[(section, k)] = v
    return out


def deal_summary(brief):
    g = lambda s, k: brief.get((s, k), "")
    return {
        "name": g("deal_meta", "name") or "Investment Committee",
        "asset_type": g("deal_meta", "asset_type"),
        "fund_id": g("deal_meta", "fund_id"),
        "loan_amount": g("loan_terms", "loan_amount"),
        "interest_rate": g("loan_terms", "interest_rate"),
        "term": g("loan_terms", "term"),
        "lien": g("loan_terms", "lien_position"),
        "ltv": g("loan_terms", "ltv"),
        "ltc": g("loan_terms", "ltc"),
        "structure": g("loan_terms", "structure"),
        "sponsor": g("sponsor", "name"),
        "guarantor": g("sponsor", "guarantor"),
        "address": g("collateral", "address"),
    }


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
    """Evidence entries may be dicts {citation,locator,text} OR bare strings."""
    out = []
    for e in (raw or []):
        if isinstance(e, dict):
            out.append({
                "citation": e.get("citation", "") or e.get("source", ""),
                "locator": e.get("locator", ""),
                "text": e.get("text", "") or e.get("quote", ""),
            })
        else:
            out.append({"citation": "", "locator": "", "text": str(e)})
    return out


def build_events(session):
    """Walk rounds/round-NN/seat-MM.json -> ordered bubble events."""
    events = []
    seq = 0
    files = sorted(glob.glob(os.path.join(session, "rounds", "round-*", "seat-*.json")))
    # order: round asc, seat asc
    def keyf(p):
        m = re.search(r"round-(\d+).*seat-(\d+)", p)
        return (int(m.group(1)), int(m.group(2))) if m else (99, 99)
    for path in sorted(files, key=keyf):
        m = re.search(r"round-(\d+)", path)
        rnd = int(m.group(1)) if m else 1
        d = load_json(path, {})
        seat = d.get("seat")
        name = d.get("seat_name", SEATS.get(seat, {}).get("short", f"Seat {seat}"))
        rolefam = d.get("role_family", "")
        for o in d.get("objections", []):
            seq += 1
            events.append({
                "id": f"e{seq}",
                "kind": "objection",
                "seat": seat,
                "seat_name": name,
                "role_family": rolefam,
                "round": rnd,
                "objection_id": o.get("objection_id", ""),
                "statement": o.get("statement", ""),
                "severity": severity_of(o.get("axis_s")),
                "covers": o.get("covers", []) or [],
                "evidence": norm_evidence(o.get("evidence")),
            })
        for mt in d.get("mitigants", []):
            seq += 1
            events.append({
                "id": f"e{seq}",
                "kind": "mitigant",
                "seat": seat,
                "seat_name": name,
                "role_family": rolefam,
                "round": rnd,
                "objection_id": mt.get("retires_objection_id", "") or mt.get("objection_id", ""),
                "statement": mt.get("statement", "") or mt.get("text", ""),
                "severity": "mitigant",
                "covers": mt.get("covers", []) or [],
                "evidence": norm_evidence(mt.get("evidence")),
            })
    return events


def build_seats_rail(events):
    """All roster seats for the avatar rail, flagged by whether they spoke."""
    spoke = {}
    for e in events:
        spoke.setdefault(e["seat"], e["seat_name"])
    rail = []
    for n in sorted(SEATS.keys()):
        # show core seats 1-10 always; optionals only if they spoke
        if n > 10 and n not in spoke:
            continue
        meta = SEATS[n]
        rail.append({
            "n": n,
            "name": spoke.get(n, meta["short"]),
            "short": meta["short"],
            "emoji": meta["emoji"],
            "color": meta["color"],
            "role": meta["role"],
            "spoke": n in spoke,
        })
    return rail


def verdict_summary(v):
    if not v:
        return {}
    return {
        "verdict": v.get("verdict", "UNRESOLVED"),
        "polarity": v.get("polarity", ""),
        "rationale": v.get("rationale", ""),
        "deal_breakers": len(v.get("deal_breakers", []) or []),
        "kill_findings": len(v.get("kill_findings", []) or []),
        "conditions": len(v.get("surviving_conditions", []) or []),
        "objection_count": len(v.get("objection_trace", []) or []),
        "ledger_head": v.get("ledger_head", ""),
        "rollup": v.get("rollup", {}) or {},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True, help="path to a completed IC session directory")
    ap.add_argument("--out", default=None, help="output HTML path (default: <session>/committee-room.html)")
    ap.add_argument("--template", default=DEFAULT_TEMPLATE)
    args = ap.parse_args()

    session = os.path.abspath(args.session)
    if not os.path.isdir(session):
        print(f"ERROR: session dir not found: {session}", file=sys.stderr)
        sys.exit(1)

    brief = parse_deal_brief(os.path.join(session, "deal-brief", "deal-brief.yaml"))
    deal = deal_summary(brief)
    verdict = verdict_summary(load_json(os.path.join(session, "verdict.json"), {}))
    events = build_events(session)
    seats = build_seats_rail(events)

    replay = {
        "mode": "replay",
        "session_id": os.path.basename(session.rstrip("/")),
        "deal": deal,
        "verdict": verdict,
        "seats": seats,
        "events": events,
        "counts": {
            "events": len(events),
            "objections": sum(1 for e in events if e["kind"] == "objection"),
            "mitigants": sum(1 for e in events if e["kind"] == "mitigant"),
            "seats_spoke": len({e["seat"] for e in events}),
            "rounds": len({e["round"] for e in events}),
        },
    }

    with open(args.template, encoding="utf-8") as fh:
        tpl = fh.read()

    payload = json.dumps(replay, ensure_ascii=False).replace("</", "<\\/")
    html = tpl.replace("/*__REPLAY_JSON__*/null", payload)

    out = args.out or os.path.join(session, "committee-room.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)

    print(json.dumps({
        "ok": True,
        "out": out,
        "events": replay["counts"]["events"],
        "objections": replay["counts"]["objections"],
        "mitigants": replay["counts"]["mitigants"],
        "seats_spoke": replay["counts"]["seats_spoke"],
        "verdict": verdict.get("verdict", "?"),
    }))


if __name__ == "__main__":
    main()
