#!/usr/bin/env python3
"""ic-pool.py — warm `claude -p` subprocess pool for the IC committee room.

Removes the moderator LLM from the live loop. A small pool of long-lived `claude -p` workers —
authenticated by the logged-in Max session, NO API key — generates each seat's spoken turn in
~6-7s off the main thread, then pushes it into meeting-state.json (which ic-server broadcasts over
SSE). Ported from acos-guided-reader's gr-pool.py (research wf_f6e73071-729).

Wire (Unix socket, line-delimited JSON):
  Request : {"action":"turn","session":"<abs>","seat":N,"name":"..","short":"..","prompt":"<full>","model":"sonnet|haiku|opus"}
            {"action":"ping"}
  Response: {"ok":true}   — fire-and-forget; on the worker's per-turn `result` the pool calls
            ic_turns.append_turn(session, seat, name, short, text) + clears `thinking` + sets a light
            reaction set, so the browser renders the turn with the moderator entirely out of the loop.

LOAD-BEARING (research): frame every user message as a CONTENT-BLOCK ARRAY and treat the per-turn
`result` event as end-of-turn — a bare-string `content` can defer `result` to stdin-EOF and stall
multi-turn. Run NON-bare (inherits keychain OAuth); ANTHROPIC_API_KEY must stay UNSET (a set key would
silently bill per-token and bypass the subscription — the pool refuses to start if it sees one).
"""
import argparse, json, os, queue, signal, socket, subprocess, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ic_turns as ic
import meeting_state as ms

CLAUDE_BIN = os.environ.get("ACOS_CLAUDE_BIN", os.path.expanduser("~/.claude/local/claude"))
RESET_AFTER_TURNS = 20   # restart a worker after N turns to bound conversation TTFT


def compute_reactions(sess, speaker):
    """Light aliveness: other seats react by vote alignment with the speaker."""
    try:
        seats = ms.load(sess).get("seats", [])
        sv = next((s.get("vote") for s in seats if s.get("n") == int(speaker)), None)
        r = {}
        for s in seats:
            n = s.get("n")
            if n == int(speaker):
                continue
            if s.get("vote") == sv:
                r[str(n)] = "🔥" if sv == "against" else "👍"
            else:
                r[str(n)] = "🤔" if s.get("vote") == "for" else "😬"
        return r
    except Exception:
        return {}


class PoolMember:
    def __init__(self, model_name):
        self.model_name = model_name
        self.proc = None
        self.ready = threading.Event()
        self.queue = queue.Queue()
        self.current = None
        self.current_lock = threading.Lock()
        self.turn_count = 0
        self.in_warmup = False
        self.start()

    def start(self):
        self.ready.clear()
        self.proc = subprocess.Popen(
            # --safe-mode: disable this project's hooks / CLAUDE.md / skills (keeps auth + model) so
            # (a) seats aren't reshaped by a session reading-level filter and (b) warmup skips the
            # ~9.5s ACOS SessionStart hooks. Still NO api key — OAuth from the logged-in Max session.
            [CLAUDE_BIN, "-p", "--safe-mode",
             "--input-format", "stream-json", "--output-format", "stream-json",
             "--verbose", "--model", self.model_name],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
        threading.Thread(target=self._stdout_loop, daemon=True,
                         name="icpool-%s" % self.model_name).start()
        self._send_warmup()

    @staticmethod
    def _user_msg(text):
        # CONTENT-BLOCK ARRAY framing (load-bearing) — NOT a bare string
        return {"type": "user", "message": {"role": "user",
                                            "content": [{"type": "text", "text": text}]}}

    def _write(self, msg):
        try:
            self.proc.stdin.write((json.dumps(msg) + "\n").encode())
            self.proc.stdin.flush()
            return True
        except (BrokenPipeError, ValueError, AttributeError):
            return False

    def _send_warmup(self):
        self.in_warmup = True
        self._write(self._user_msg("Reply with only the word: ok"))

    def _stdout_loop(self):
        for raw in self.proc.stdout:
            try:
                line = raw.decode("utf-8", "replace").strip()
            except Exception:
                continue
            if not line:
                continue
            try:
                evt = json.loads(line)
            except json.JSONDecodeError:
                continue
            try:
                self._handle(evt)
            except Exception as e:
                sys.stderr.write("icpool-%s event err: %s\n" % (self.model_name, e)); sys.stderr.flush()

    def _handle(self, evt):
        t = evt.get("type")
        if t == "result" and self.in_warmup:
            self.in_warmup = False
            self.ready.set()
            self._drain()
            return
        if self.in_warmup:
            return
        with self.current_lock:
            cur = self.current
        if cur is None:
            return
        if t == "assistant":
            for block in evt.get("message", {}).get("content", []):
                if block.get("type") == "text":
                    cur["acc"] += block.get("text", "")
        elif t == "result":
            self._finish(cur, cur["acc"].strip())
            with self.current_lock:
                self.current = None
            self._maybe_reset()
            self._drain()

    def _finish(self, cur, text):
        if not text:
            text = "(the seat returned no response)"
        try:
            ic.append_turn(cur["session"], cur["seat"], cur["name"], cur["short"],
                           text, compute_reactions(cur["session"], cur["seat"]), [])
        except Exception as e:
            sys.stderr.write("icpool push failed: %s\n" % e); sys.stderr.flush()

    def submit(self, req):
        self.queue.put(req)
        with self.current_lock:
            idle = self.current is None
        if idle:
            self._drain()

    def _drain(self):
        with self.current_lock:
            if self.current is not None:
                return
            try:
                req = self.queue.get_nowait()
            except queue.Empty:
                return
            self.current = {"session": req["session"], "seat": int(req["seat"]),
                            "name": req.get("name", ""), "short": req.get("short", ""), "acc": ""}
        self.turn_count += 1
        if not self._write(self._user_msg(req["prompt"])):
            self.start()
            with self.current_lock:
                self.current = None
            self.queue.put(req)

    def _maybe_reset(self):
        if self.turn_count >= RESET_AFTER_TURNS:
            try:
                if self.proc:
                    self.proc.terminate(); self.proc.wait(timeout=2)
            except Exception:
                pass
            self.turn_count = 0
            self.start()


class Pool:
    def __init__(self, models):
        self.members = {m: PoolMember(m) for m in models}

    def wait_ready(self, timeout=120.0):
        for name, m in self.members.items():
            if not m.ready.wait(timeout=timeout):
                sys.stderr.write("icpool: '%s' not ready in %ss\n" % (name, timeout)); return False
        return True

    def dispatch(self, req):
        model = req.get("model", "sonnet")
        m = self.members.get(model) or self.members.get("sonnet") or next(iter(self.members.values()))
        try:
            ic.set_thinking(req["session"], int(req["seat"]))   # instant feedback before generation
        except Exception:
            pass
        m.submit(req)
        return {"ok": True, "model": m.model_name}

    def shutdown(self):
        for m in self.members.values():
            try:
                if m.proc:
                    m.proc.terminate()
            except Exception:
                pass


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--socket-path", required=True)
    p.add_argument("--models", default="sonnet,haiku")
    args = p.parse_args(argv)

    if os.environ.get("ANTHROPIC_API_KEY"):
        sys.stdout.write(json.dumps({"event": "pool_failed",
                                     "error": "ANTHROPIC_API_KEY is set — refusing (Max-subscription only; a set key bills per-token)"}) + "\n")
        sys.stdout.flush()
        return 2

    sp = args.socket_path
    if os.path.exists(sp):
        try:
            os.unlink(sp)
        except OSError:
            pass
    sys.stdout.write(json.dumps({"event": "pool_starting", "pid": os.getpid()}) + "\n"); sys.stdout.flush()

    pool = Pool([m.strip() for m in args.models.split(",") if m.strip()])
    if not pool.wait_ready():
        sys.stdout.write(json.dumps({"event": "pool_failed", "error": "init timeout"}) + "\n"); sys.stdout.flush()
        pool.shutdown()
        return 1
    sys.stdout.write(json.dumps({"event": "pool_ready", "pid": os.getpid(), "socket": sp}) + "\n"); sys.stdout.flush()

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(sp); sock.listen(8)

    def handle(conn):
        try:
            data = b""
            while not data.endswith(b"\n") and len(data) < 1_000_000:
                chunk = conn.recv(8192)
                if not chunk:
                    break
                data += chunk
            if not data:
                return
            req = json.loads(data.decode().strip())
            action = req.get("action")
            if action == "turn":
                resp = pool.dispatch(req)
            elif action == "ping":
                resp = {"ok": True, "pong": True}
            else:
                resp = {"ok": False, "error": "unknown action %r" % action}
            conn.sendall((json.dumps(resp) + "\n").encode())
        except Exception as e:
            try:
                conn.sendall((json.dumps({"ok": False, "error": str(e)}) + "\n").encode())
            except Exception:
                pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def sh(*_):
        pool.shutdown()
        try:
            sock.close()
        except Exception:
            pass
        try:
            os.unlink(sp)
        except OSError:
            pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, sh)
    signal.signal(signal.SIGINT, sh)
    while True:
        try:
            conn, _ = sock.accept()
            threading.Thread(target=handle, args=(conn,), daemon=True).start()
        except Exception:
            time.sleep(0.1)


if __name__ == "__main__":
    sys.exit(main())
