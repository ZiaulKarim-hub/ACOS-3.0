#!/usr/bin/env python3
"""Moderator's live state-writer for the chaired meeting. The Claude Code moderator calls this to
mutate <session>/meeting-state.json as the meeting runs; ic-server.py's watcher broadcasts each
change to the browser over SSE. Also consumes chair-inbox.jsonl.

Subcommands:
  init      --session S                       # (re)generate base state from the session openings
  phase     --session S --value in-session
  add-turn  --session S --seat N --name NAME --short SHORT --text "..."   # sets the floor + appends transcript
  reactions --session S --json '{"1":"👍","5":"🤔"}'
  hands     --session S --seats 1,3
  inbox     --session S                        # print + clear pending chair commands (one JSON per line)
"""
import argparse, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))

def state_path(sess): return os.path.join(sess, "meeting-state.json")

def load(sess):
    p = state_path(sess)
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    # bootstrap from openings
    subprocess.run([sys.executable, os.path.join(HERE, "build_meeting.py"), "--session", sess, "--state-only"],
                   capture_output=True, text=True)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"seats": [], "timeline": []}

def save(sess, st):
    tmp = state_path(sess) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(st, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, state_path(sess))   # atomic — the poller never reads a torn file

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("init", "phase", "add-turn", "reactions", "hands", "inbox"):
        p = sub.add_parser(c); p.add_argument("--session", required=True)
        if c == "phase": p.add_argument("--value", required=True)
        if c == "add-turn":
            for f in ("seat", "name", "short", "text"): p.add_argument("--" + f, required=True)
        if c == "reactions": p.add_argument("--json", required=True)
        if c == "hands": p.add_argument("--seats", default="")
    a = ap.parse_args(); sess = os.path.abspath(a.session)

    if a.cmd == "inbox":
        p = os.path.join(sess, "chair-inbox.jsonl")
        lines = open(p, encoding="utf-8").read().splitlines() if os.path.exists(p) else []
        open(p, "w").close()  # consume
        for ln in lines:
            if ln.strip(): print(ln)
        return

    st = load(sess)
    if a.cmd == "init":
        save(sess, st); print("initialized"); return
    if a.cmd == "phase":
        st["phase"] = a.value
    elif a.cmd == "add-turn":
        ev = {"type": "turn", "seat": int(a.seat), "name": a.name, "short": a.short, "text": a.text,
              "reactions": {}, "hands": []}
        st.setdefault("timeline", []).append(ev)
        st["floor"] = {"seat": int(a.seat), "text": a.text}
        st["phase"] = "in-session"
    elif a.cmd == "reactions":
        st["reactions"] = json.loads(a.json)
        if st.get("timeline"): st["timeline"][-1]["reactions"] = st["reactions"]
    elif a.cmd == "hands":
        hands = [int(x) for x in a.seats.split(",") if x.strip()]
        st["hands"] = hands
        if st.get("timeline"): st["timeline"][-1]["hands"] = hands
    save(sess, st); print(a.cmd, "ok")

if __name__ == "__main__":
    main()
