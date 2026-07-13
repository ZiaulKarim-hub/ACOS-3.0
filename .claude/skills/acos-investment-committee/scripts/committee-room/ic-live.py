#!/usr/bin/env python3
"""ic-live.py — the moderator-replacement consumer for the fully-live committee room.

Sole consumer of chair-inbox.jsonl. For each chair `speak` command it either serves an instantly-warm
pre-generated turn from the ic_turns cache, or builds the called seat's grounded prompt (persona +
its real objections + the transcript-so-far + the chair's argument + the burden-of-proof doctrine)
and dispatches it to the ic-pool.py worker pool, which generates the turn (~6-7s) and pushes it to
meeting-state.json. The main Claude session is entirely out of the loop.

Run:  python3 ic-live.py --session <dir> --socket /tmp/ic-pool.sock &
(Start ic-pool.py first; start ic-server.py to serve the room.)
"""
import argparse, json, os, socket, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ic_turns as ic
import meeting_state as ms

# per-seat voice, mirroring each ic-0N agent def's "Voice & register" block
VOICE = {
    1: "a deadpan valuation hawk — numbers-first, no adjectives; 'strip the story and the number is the number'; the least excitable voice in the room.",
    2: "a trading-desk voice — fast, clipped, talks in spread / bps / lender-IRR; 'net-net'; a little impatient, some swagger.",
    3: "a forensic reconciler — methodical, ties everything out, and corrects yourself on the record without defensiveness ('let me correct my own work'); careful, not cold.",
    4: "counsel — measured, hedged exactly where the document is silent; 'absent the instrument I can't opine'; you read to the four corners; dry wit.",
    5: "the actuary — you think in tails and bad states of the world; 'price the tail, not the base case'; you read the premium as the market's own opinion of the risk; unhurried, a touch grim.",
    6: "the investigator — blunt, prosecutorial, short declaratives; you assume fabricated until a third party corroborates ('until it's corroborated, it's a claim'); distrust is your default and you don't apologize for it.",
    7: "the allocator who sees the whole book — calm, big-picture, fund-level ('at the portfolio level…'); you care about the pattern more than the single deal.",
    8: "the contrarian partner — you ask the question nobody wants to ('is this even our deal?'); you frame in opportunity cost and thesis-fit; sharp, a bit dry.",
}

# reading-comprehension dial (0 = expert, 5 = very simple) — like /acos-knowledge-builder's abstraction levels.
# The pool runs --safe-mode (no session hook), so this is the ONLY thing that sets the seats' register.
LEVELS = {
    0: "READING LEVEL 0 (EXPERT — default): speak to sophisticated finance peers. Dense, precise; use jargon freely (LTV, DSCR, basis, BPO, pro forma, mortgage constant) with NO definitions.",
    1: "READING LEVEL 1 (ADVANCED): precise professional language, but briefly gloss an unusual term the first time you use it.",
    2: "READING LEVEL 2 (PLAIN PROFESSIONAL): plain business English; define each finance term in a few words the first time it appears.",
    3: "READING LEVEL 3 (GENERAL): short sentences, everyday words; define EVERY finance term simply the first time and give one quick concrete example.",
    4: "READING LEVEL 4 (SIMPLE): very plain, very short sentences; explain as if to someone new to finance.",
    5: "READING LEVEL 5 (VERY SIMPLE): the simplest possible language, tiny words, one idea per sentence.",
}
LEVEL_FIDELITY = (" Keep EVERY number, name, and your actual conclusion exactly the same — change only HOW "
                  "plainly you say it, never what is true, and never soften a warning or a deal-breaker.")

DOCTRINE = (
    "CHAIR-INPUT DOCTRINE (binding): YOU bring the evidence, not the chair. When the chair states a "
    "number or input, do NOT demand they prove it. If your own objections/evidence CONTRADICT it, "
    "challenge it — cite your evidence and ask 'is that a documented figure, or your own verification?'. "
    "If nothing you have contradicts it, ACCEPT it as a working assumption and update — log it as "
    "'to be confirmed by [document]', not a veto. A chair PERSONAL ASSURANCE ('I verified X myself') is "
    "evidence on the record and moves you to a condition-precedent. Absorb ALL prior discussion as known "
    "context — never make the chair repeat themselves."
)


def build_prompt(st, seat, chair_msg):
    seats = {s.get("n"): s for s in st.get("seats", [])}
    s = seats.get(int(seat), {})
    name = s.get("name") or s.get("short") or ("Seat %s" % seat)
    short = s.get("short") or name
    # the seat's real blind-opening objections (grounding)
    objs = s.get("objections", []) or []
    obj_lines = []
    for o in objs[:4]:
        q = (o.get("question") or "").strip()
        ctx = (o.get("statement") or "").strip()
        mit = ""
        m = (o.get("mitigants") or o.get("suggested_mitigants") or [])
        if m and isinstance(m[0], dict):
            mit = (m[0].get("statement") or "").strip()
        if q or ctx:
            obj_lines.append("- Q: %s\n  Context: %s%s" % (q, ctx[:400], ("\n  Cure: " + mit[:200]) if mit else ""))
    obj_block = "\n".join(obj_lines) if obj_lines else "(form your sharpest concern from the deal brief)"
    # transcript so far
    tl = st.get("timeline", []) or []
    t_lines = []
    for t in tl[-12:]:
        who = t.get("short") or ("Seat %s" % t.get("seat"))
        t_lines.append("%s: %s" % (who, (t.get("text") or "")))
    transcript = "\n\n".join(t_lines) if t_lines else "(the meeting has just opened — no turns yet)"
    voice = VOICE.get(int(seat), "in your own distinct professional voice")
    spoke_before = any(t.get("seat") == int(seat) for t in tl)
    level = int(st.get("reading_level", 0) or 0)

    parts = [
        "You are the %s seat (#%s) on OKOA Capital's adversarial AI Investment Committee, reviewing a "
        "real-estate lending deal. Your job is to find the holes from your discipline — not to sell the deal." % (name, seat),
        "VOICE — speak as %s Write in the first person, human, varied sentence length; never a memo." % voice,
        "YOUR REAL POSITION (your blind-opening objections on THIS deal — stay grounded in these, cite specifics):\n" + obj_block,
        "THE DISCUSSION SO FAR:\n" + transcript,
        LEVELS.get(level, LEVELS[0]) + LEVEL_FIDELITY,
    ]
    if chair_msg:
        parts.append('THE CHAIR JUST ADDRESSED YOU:\n"%s"' % chair_msg)
        parts.append(DOCTRINE)
        parts.append("TASK: Respond to the chair directly, in character and grounded in your real position, following the doctrine. "
                     "If nothing you hold contradicts what they said, accept it and move; if your evidence cuts against it, say exactly where and ask the refinement question. "
                     "~110-170 words. Return ONLY your spoken turn — no preamble, no name label.")
    else:
        parts.append(DOCTRINE)
        verb = "Continue — add your next point given the discussion above" if spoke_before else "Deliver your opening statement — your single sharpest concern"
        parts.append("TASK: %s, in character, grounded in your objections. ~110-160 words. "
                     "Return ONLY your spoken turn — no preamble, no name label." % verb)
    return name, short, "\n\n".join(parts)


def pick_model(chair_msg, seat, st):
    # sonnet for real arguments and numeric/adversarial seats; haiku for a plain first opening
    spoke = any(t.get("seat") == int(seat) for t in (st.get("timeline") or []))
    if not chair_msg and not spoke and int(seat) not in (1, 2, 3):
        return "haiku"
    return "sonnet"


def dispatch_pool(sock_path, req):
    try:
        c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        c.settimeout(10)
        c.connect(sock_path)
        c.sendall((json.dumps(req) + "\n").encode())
        ack = c.recv(4096).decode().strip()
        c.close()
        return json.loads(ack) if ack else {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def handle(sess, sock_path, cmd):
    typ = (cmd.get("type") or "").lower()
    if typ == "level":                                   # reading-level dial — set-and-forget, no turn generated
        st = ms.load(sess)
        st["reading_level"] = max(0, min(5, int(cmd.get("value", 0))))
        ms.save(sess, st)
        print("LEVEL set to", st["reading_level"], flush=True)
        return
    if typ != "speak" or cmd.get("seat") is None:
        return
    seat = int(cmd["seat"])
    chair = (cmd.get("chair") or "").strip()
    st = ms.load(sess)
    thash = ic.transcript_hash(st)
    if not chair:                                        # bare floor-give → warm cache may serve instantly
        e = ic.read_valid(sess, seat, thash)
        if e:
            ic.append_turn(sess, e["seat"], e.get("name", ""), e.get("short", ""),
                           e["text"], e.get("reactions"), e.get("hands"))
            print("HIT  seat %s from cache" % seat, flush=True)
            return
    ic.set_thinking(sess, seat)                          # instant feedback
    name, short, prompt = build_prompt(st, seat, chair)
    req = {"action": "turn", "session": sess, "seat": seat, "name": name, "short": short,
           "prompt": prompt, "model": pick_model(chair, seat, st)}
    resp = dispatch_pool(sock_path, req)
    print("DISPATCH seat %s (%s) chair=%s -> %s" % (seat, req["model"], bool(chair), resp), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    ap.add_argument("--socket", default="/tmp/ic-pool.sock")
    ap.add_argument("--poll", type=float, default=0.15)
    a = ap.parse_args()
    sess = os.path.abspath(a.session)
    ic.cache_dir(sess)
    claim = ic.claim_inbox(sess, "ic-live")
    if not claim["ok"]:
        print(json.dumps({"error": "chair-inbox already has a live consumer", "owner": claim["owner"]}),
              file=sys.stderr, flush=True)
        sys.exit(3)
    import atexit
    atexit.register(lambda: ic.release_inbox(sess))
    inbox = os.path.join(sess, "chair-inbox.jsonl")
    off = os.path.getsize(inbox) if os.path.exists(inbox) else 0
    print(json.dumps({"consumer": "ic-live", "session": sess, "socket": a.socket, "start_offset": off}), flush=True)
    while True:
        try:
            if os.path.exists(inbox):
                sz = os.path.getsize(inbox)
                if sz < off:
                    off = sz
                if sz > off:
                    with open(inbox, encoding="utf-8") as fh:
                        fh.seek(off); chunk = fh.read(); off = fh.tell()
                    for ln in chunk.splitlines():
                        ln = ln.strip()
                        if not ln:
                            continue
                        try:
                            handle(sess, a.socket, json.loads(ln))
                        except Exception as ex:
                            print("cmd-err:", ex, file=sys.stderr, flush=True)
            time.sleep(a.poll)
        except KeyboardInterrupt:
            break
        except Exception as ex:
            print("loop-err:", ex, file=sys.stderr, flush=True); time.sleep(1)


if __name__ == "__main__":
    main()
