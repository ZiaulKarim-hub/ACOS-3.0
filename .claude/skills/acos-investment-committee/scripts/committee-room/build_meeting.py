#!/usr/bin/env python3
"""Build the chaired-meeting state for the committee room.

Meeting flow (per user spec):
  1. Blind openings (each seat's question/context/mitigants) are synthesized into a
     single **Committee Briefing** document -> shown in the SIDEBAR (chair's prep,
     NOT part of the spoken conversation).
  2. The chair runs the meeting agent-by-agent: calls on a seat, that seat delivers a
     fresh spoken turn; the other seats REACT with big evolving (non-face) emojis;
     seats RAISE HANDS to be called next; the chair controls the floor.
  3. Tally -> computed verdict.

This script emits `meeting-state.json` (and a self-contained `meeting.html`). When the
live engine runs, `ic-server.py` regenerates the same state shape from the moderator's
on-disk writes, so the UI is identical live vs. demo.

Reactions vocabulary (non-face, per spec): 👍 👎 ❤️ 💩 🤔 🙌 😐 (+ 🔥 💯 😬).

Usage:
  python3 build_meeting.py --session <dir> [--out meeting.html] [--state-only] [--demo]
Stdlib only. Reuses build_committee for the committee data.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_committee as bc  # noqa: E402

DEFAULT_TEMPLATE = os.path.join(HERE, "meeting_template.html")

# reaction glyphs (non-face, evolving)
R = {"agree": "\U0001F44D", "strong": "\U0001F4AF", "fire": "\U0001F525", "love": "❤️",
     "disagree": "\U0001F44E", "bad": "\U0001F4A9", "think": "\U0001F914", "hand": "✋",
     "neutral": "\U0001F642", "wince": "\U0001F62C", "raise": "\U0001F64C", "happy": "\U0001F642"}


def default_reaction(seat_vote, speaker_vote):
    """A seat's resting reaction to a speaker: aligned stance -> agree, opposed -> think/disagree."""
    if seat_vote == speaker_vote:
        return R["agree"]
    return R["think"]


def build_briefing(committee):
    """One-go summary: every seat's sharpest question + its top suggested mitigant."""
    rows = []
    for s in committee["scrutiny"]:
        objs = s.get("objections", [])
        top = objs[0] if objs else None
        rows.append({
            "seat": s["n"], "short": s["short"], "name": s["name"], "vote": s["vote"],
            "question": (top or {}).get("question", s.get("opinion", "")),
            "context": (top or {}).get("statement", ""),
            "mitigant": ((top or {}).get("mitigants") or [{}])[0].get("statement", ""),
            "n_objections": len(objs),
        })
    return rows


def demo_timeline(committee):
    """A scripted chaired meeting for the demo: chair calls seats in turn; each delivers a
    fresh turn (grounded elaboration of its opening); others react with evolving emojis.
    The live engine replaces this with real per-turn generation."""
    byn = {s["n"]: s for s in committee["scrutiny"]}
    # fresh-turn scripts (grounded elaborations)
    turns = [
        (1, "Let me be concrete. The 65% LTV is not an appraisal — it's a back-solve from the sponsor's own $101k normalized NOI. Against the arm's-length $1.45M purchase price, OKOA is really at 79%. Strip the story and the equity cushion under us is about $300k, not 35%."),
        (3, "And that NOI is fiction. Four occupied units bill $74,400 a year gross; a $92k in-place NOI is arithmetically impossible. Seat 1's LTV is therefore built on a number that cannot exist — the two objections compound."),
        (4, "Structurally it's worse. We have no title commitment and, for a 'refinance,' no payoff of the prior deed of trust. I cannot confirm we hold a first lien at all — and a nominal SPE with no separateness covenants invites substantive consolidation with the sponsor."),
        (6, "From my seat, the whole file is self-attested. The 640-unit record, the $8.4M net worth — none of it is corroborated, and no background or litigation search was run. Under a default-fabricated posture, the guarantee could be worthless."),
    ]
    # evolving reaction map per turn: seat_n -> emoji
    events = []
    for i, (spk, text) in enumerate(turns):
        speaker = byn.get(spk, {})
        reactions = {}
        for s in committee["scrutiny"]:
            if s["n"] == spk:
                continue
            # agreement grows as the against-case compounds; the 'for' seats wince
            if s["vote"] == "against":
                reactions[s["n"]] = [R["agree"], R["strong"], R["fire"], R["fire"]][min(i, 3)]
            else:
                reactions[s["n"]] = [R["neutral"], R["think"], R["wince"], R["wince"]][min(i, 3)]
        # who raises a hand next (a couple of against-seats want in)
        hands = [s["n"] for s in committee["scrutiny"] if s["vote"] == "against" and s["n"] not in [t[0] for t in turns[:i + 1]]][:2]
        events.append({
            "type": "turn", "seat": spk, "name": speaker.get("name", ""), "short": speaker.get("short", ""),
            "text": text, "reactions": reactions, "hands": hands,
        })
    return events


def build_state(session, demo):
    committee = bc.build_committee(session, demo)
    return {
        "deal": committee["deal"],
        "vote": committee["vote"],
        "seats": [{"n": s["n"], "short": s["short"], "name": s["name"], "vote": s["vote"],
                   "emoji": s["emoji"], "research": s.get("research", 0), "threads": s.get("threads", []),
                   "objections": s.get("objections", [])} for s in committee["scrutiny"]],
        "briefing": build_briefing(committee),
        "timeline": demo_timeline(committee) if demo else [],
        "phase": "briefing",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--template", default=DEFAULT_TEMPLATE)
    ap.add_argument("--state-only", action="store_true", help="write meeting-state.json only")
    ap.add_argument("--demo", action="store_true", help="include the scripted demo timeline + demo research")
    args = ap.parse_args()

    session = os.path.abspath(args.session)
    state = build_state(session, args.demo)

    if args.state_only:
        out = args.out or os.path.join(session, "meeting-state.json")
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2, ensure_ascii=False)
        print(json.dumps({"ok": True, "state": out, "seats": len(state["seats"]), "turns": len(state["timeline"])}))
        return

    with open(args.template, encoding="utf-8") as fh:
        tpl = fh.read()
    payload = json.dumps(state, ensure_ascii=False).replace("</", "<\\/")
    html = tpl.replace("/*__MEETING_JSON__*/null", payload)
    out = args.out or os.path.join(session, "meeting.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(json.dumps({"ok": True, "out": out, "seats": len(state["seats"]), "turns": len(state["timeline"])}))


if __name__ == "__main__":
    main()
