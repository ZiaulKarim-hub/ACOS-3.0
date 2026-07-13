#!/usr/bin/env python3
"""ic-turn-daemon — makes the chaired room feel INSTANT.

Sole consumer of chair-inbox.jsonl (the browser POSTs `speak` commands there via ic-server).
For each new `speak seat N`:
  • bare floor-give AND a cache entry valid for the current transcript  -> SERVE it instantly
    (append the pre-generated turn; no model in the loop; ~0.5s end-to-end over SSE).
  • new chair argument, OR cold / stale cache                           -> set the seat's THINKING
    state (browser shows it typing immediately) and drop turn-cache/PENDING.json for the moderator
    (Claude) to generate the genuinely-fresh turn.

So the room NEVER sits dead: a hit is instant, a miss shows life instantly and is filled by the
moderator moments later. Offset-based tail so it never re-serves an old line. Stdlib only.

Run (background):  python3 ic-turn-daemon.py --session <dir>
"""
import argparse, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ic_turns as ic
import meeting_state as ms


def pending_path(sess):
    return os.path.join(ic.cache_dir(sess), "PENDING.json")


def offset_path(sess):
    return os.path.join(ic.cache_dir(sess), ".inbox-offset")


def process(sess, cmd):
    if cmd.get("type") != "speak":
        return
    seat = cmd.get("seat")
    if seat is None:
        return
    chair = (cmd.get("chair") or "").strip()
    st = ms.load(sess)
    thash = ic.transcript_hash(st)
    if not chair:                                   # bare "give seat N the floor" — cache is eligible
        e = ic.read_valid(sess, seat, thash)
        if e:
            ic.append_turn(sess, e["seat"], e.get("name", ""), e.get("short", ""),
                           e["text"], e.get("reactions"), e.get("hands"))
            print("HIT  seat %s served from cache" % seat, flush=True)
            return
    # miss: instant thinking-state + a marker the moderator picks up to generate the fresh turn
    ic.set_thinking(sess, seat)
    with open(pending_path(sess), "w", encoding="utf-8") as fh:
        json.dump({"seat": int(seat), "chair": chair, "hash": thash, "ts": cmd.get("ts")},
                  fh, ensure_ascii=False)
    print("MISS seat %s -> thinking + PENDING (%s)" % (seat, "new-argument" if chair else "cold-cache"),
          flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    ap.add_argument("--poll", type=float, default=0.4)
    a = ap.parse_args()
    sess = os.path.abspath(a.session)
    ic.cache_dir(sess)  # ensure exists
    claim = ic.claim_inbox(sess, "turn-daemon")
    if not claim["ok"]:
        print(json.dumps({"error": "chair-inbox already has a live consumer — refusing to double-run",
                          "owner": claim["owner"]}), file=sys.stderr, flush=True)
        sys.exit(3)
    import atexit; atexit.register(lambda: ic.release_inbox(sess))
    inbox = os.path.join(sess, "chair-inbox.jsonl")

    # resume from persisted offset, clamped to the current file size (handles external truncation)
    off = 0
    try:
        off = int(open(offset_path(sess)).read().strip())
    except Exception:
        off = os.path.getsize(inbox) if os.path.exists(inbox) else 0
    if os.path.exists(inbox):
        off = min(off, os.path.getsize(inbox))
    print(json.dumps({"daemon": "ic-turn", "session": sess, "watching": inbox, "start_offset": off}),
          flush=True)

    while True:
        try:
            if os.path.exists(inbox):
                sz = os.path.getsize(inbox)
                if sz < off:            # someone truncated it — the bytes are gone, don't reprocess
                    off = sz
                if sz > off:
                    with open(inbox, encoding="utf-8") as fh:
                        fh.seek(off)
                        chunk = fh.read()
                        off = fh.tell()
                    for ln in chunk.splitlines():
                        ln = ln.strip()
                        if not ln:
                            continue
                        try:
                            process(sess, json.loads(ln))
                        except Exception as ex:
                            print("parse/err:", ex, file=sys.stderr, flush=True)
                    try:
                        open(offset_path(sess), "w").write(str(off))
                    except Exception:
                        pass
            time.sleep(a.poll)
        except KeyboardInterrupt:
            break
        except Exception as ex:
            print("loop-err:", ex, file=sys.stderr, flush=True)
            time.sleep(1)


if __name__ == "__main__":
    main()
