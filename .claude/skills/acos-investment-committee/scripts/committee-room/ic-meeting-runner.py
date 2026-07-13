#!/usr/bin/env python3
"""ic-meeting-runner — the AUTONOMOUS meeting engine that makes the room feel like a real meeting.

The old failure mode: in live mode nothing advanced the meeting except the moderator LLM pushing a
turn inside a response — so every turn waited minutes on a human-in-the-render-loop. This runner
decouples playback from generation: it plays a PRE-BUILT deliberation (meeting-script.json) at
natural cadence, so turns follow one another every ~12-18s with reactions rippling and hands
raising — a meeting unfolding on its own — while the chair steers at any moment.

Sole consumer of chair-inbox.jsonl (subsumes ic-turn-daemon). Chair commands:
  pause / hold            -> stop auto-advance (floor holds on the current speaker)
  play / resume / next    -> resume (next also advances immediately)
  speak #n (bare)         -> jump: play seat n's next scripted beat NOW (or serve its cache)
  speak #n (+ argument)   -> can't pre-answer an unseen point: set THINKING + drop PENDING for the moderator
  close / verdict         -> play the closing beat, then stop

Cadence is estimated from the client's ~50ms/word typewriter so a turn never starts before the
previous finishes "speaking." Stdlib only.  Run:  python3 ic-meeting-runner.py --session <dir> &
"""
import argparse, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ic_turns as ic
import meeting_state as ms


def script_path(sess): return os.path.join(sess, "meeting-script.json")
def pending_path(sess): return os.path.join(ic.cache_dir(sess), "PENDING.json")
def offset_path(sess):  return os.path.join(ic.cache_dir(sess), ".inbox-offset")


def estimate_s(text, pace):
    """Seconds a turn occupies: typewriter delivery (~per_word_ms) + a reaction-ripple + a gap."""
    words = len((text or "").split())
    return (words * pace["per_word_ms"] + pace["react_ms"] + pace["gap_ms"]) / 1000.0


class Runner:
    def __init__(self, sess, speed):
        self.sess = sess
        self.speed = speed
        sc = json.load(open(script_path(sess), encoding="utf-8"))
        self.beats = sc.get("beats", [])
        self.closing = sc.get("closing")
        # default MUST match the client typewriter (~135ms/word, meeting_template.html) or the next
        # turn fires early and clearTimeout truncates the current one mid-sentence
        self.pace = {"per_word_ms": 135, "react_ms": 600, "gap_ms": 2200}
        self.pace.update(sc.get("pace", {}))
        self.played = set()
        self.paused = False
        self.closed = False
        self.next_at = time.monotonic()  # play the first beat right away
        # start reading the inbox from its current end (don't replay old commands)
        inbox = os.path.join(sess, "chair-inbox.jsonl")
        self.inbox = inbox
        self.off = os.path.getsize(inbox) if os.path.exists(inbox) else 0

    # ---- beat selection ----
    def next_unplayed(self, seat=None):
        for i, b in enumerate(self.beats):
            if i in self.played:
                continue
            if seat is None or int(b.get("seat")) == int(seat):
                return i
        return None

    def play(self, idx):
        b = self.beats[idx]
        ic.append_turn(self.sess, int(b["seat"]), b.get("name", ""), b.get("short", ""),
                       b["text"], b.get("reactions"), b.get("hands"))
        self.played.add(idx)
        self.next_at = time.monotonic() + estimate_s(b["text"], self.pace) * self.speed
        print("PLAY beat %d  seat %s  (%d words)" % (idx, b.get("seat"), len(b["text"].split())), flush=True)

    def do_close(self):
        if self.closing:
            b = self.closing
            ic.append_turn(self.sess, int(b.get("seat", 0)) or 0, b.get("name", "Chair"),
                           b.get("short", "Chair"), b["text"], b.get("reactions"), b.get("hands"))
        st = ms.load(self.sess); st["phase"] = "closed"; ms.save(self.sess, st)
        self.closed = True
        print("CLOSE meeting", flush=True)

    # ---- chair steering ----
    def handle(self, cmd):
        typ = (cmd.get("type") or "").lower()
        raw = (cmd.get("text") or "").lower()
        if typ in ("pause", "hold") or raw in ("pause", "hold", "stop"):
            self.paused = True; print("PAUSE", flush=True); return
        if typ in ("play", "resume") or raw in ("play", "resume"):
            self.paused = False; print("RESUME", flush=True); return
        if typ == "next" or raw == "next":
            self.paused = False; self.next_at = time.monotonic(); print("NEXT", flush=True); return
        if typ in ("close", "verdict") or raw in ("close", "verdict"):
            self.do_close(); return
        if typ == "speak" and cmd.get("seat") is not None:
            seat = int(cmd["seat"]); chair = (cmd.get("chair") or "").strip()
            if chair:  # a genuinely-new argument -> can't pre-answer; hand to the moderator
                ic.set_thinking(self.sess, seat)
                json.dump({"seat": seat, "chair": chair, "hash": ic.transcript_hash(ms.load(self.sess)),
                           "ts": cmd.get("ts")}, open(pending_path(self.sess), "w", encoding="utf-8"),
                          ensure_ascii=False)
                print("MISS seat %d (new argument) -> thinking + PENDING" % seat, flush=True)
                return
            idx = self.next_unplayed(seat)
            if idx is not None:
                self.play(idx); print("JUMP seat %d -> beat %d" % (seat, idx), flush=True); return
            # no scripted beat left for this seat -> try the pre-gen cache, else think
            e = ic.read_valid(self.sess, seat, ic.transcript_hash(ms.load(self.sess)))
            if e:
                ic.append_turn(self.sess, e["seat"], e.get("name", ""), e.get("short", ""),
                               e["text"], e.get("reactions"), e.get("hands"))
                self.next_at = time.monotonic() + estimate_s(e["text"], self.pace) * self.speed
                print("SERVE seat %d from cache" % seat, flush=True); return
            ic.set_thinking(self.sess, seat)
            json.dump({"seat": seat, "chair": "", "hash": ic.transcript_hash(ms.load(self.sess)),
                       "ts": cmd.get("ts")}, open(pending_path(self.sess), "w", encoding="utf-8"),
                      ensure_ascii=False)
            print("MISS seat %d (no beat) -> thinking + PENDING" % seat, flush=True)

    def drain_inbox(self):
        if not os.path.exists(self.inbox):
            return
        sz = os.path.getsize(self.inbox)
        if sz < self.off:
            self.off = sz
        if sz > self.off:
            with open(self.inbox, encoding="utf-8") as fh:
                fh.seek(self.off); chunk = fh.read(); self.off = fh.tell()
            for ln in chunk.splitlines():
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    self.handle(json.loads(ln))
                except Exception as ex:
                    print("cmd-err:", ex, file=sys.stderr, flush=True)

    def loop(self, poll=0.25):
        print(json.dumps({"runner": "ic-meeting", "session": self.sess, "beats": len(self.beats),
                          "speed": self.speed}), flush=True)
        while not self.closed:
            try:
                self.drain_inbox()
                if not self.paused and time.monotonic() >= self.next_at:
                    idx = self.next_unplayed()
                    if idx is not None:
                        self.play(idx)
                    else:
                        # script exhausted — hold (chair can still call seats / close)
                        self.paused = True
                        print("SCRIPT END — holding (chair may call seats or close)", flush=True)
                time.sleep(poll)
            except KeyboardInterrupt:
                break
            except Exception as ex:
                print("loop-err:", ex, file=sys.stderr, flush=True); time.sleep(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    ap.add_argument("--speed", type=float, default=1.0, help="cadence multiplier (0.2 = 5x faster, for testing)")
    a = ap.parse_args()
    sess = os.path.abspath(a.session)
    claim = ic.claim_inbox(sess, "meeting-runner")
    if not claim["ok"]:
        print(json.dumps({"error": "chair-inbox already has a live consumer — refusing to double-run",
                          "owner": claim["owner"]}), file=sys.stderr, flush=True)
        sys.exit(3)
    import atexit; atexit.register(lambda: ic.release_inbox(sess))
    Runner(sess, a.speed).loop()


if __name__ == "__main__":
    main()
