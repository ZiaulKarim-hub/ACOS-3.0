#!/usr/bin/env python3
"""ic-server — the browser bridge for the live chaired Investment-Committee meeting.

Architecture (validated by swarm-20260709-171108, a port of acos-guided-reader's gr-server):
  - A Claude Code session is the MODERATOR/engine (it alone can dispatch Task() seats). It
    writes the meeting state to `<session>/meeting-state.json` as the meeting progresses and
    reads chair commands from `<session>/chair-inbox.jsonl`.
  - This server is the CHAIR COCKPIT bridge. It serves the meeting UI, streams state changes to
    the browser over SSE, and appends the chair's commands to chair-inbox.jsonl. It NEVER calls
    Task(); it only moves bytes between the browser and disk.
  - The moderator waits for chair input with a zero-token blocking `tail -f chair-inbox.jsonl`
    (see `wait_for_chair` below and SKILL.md's Mode B loop).

Endpoints:
  GET  /               -> the meeting UI (meeting.html)
  GET  /state          -> current meeting-state.json (ETag / 304 supported)
  GET  /events         -> SSE stream; emits `state` events when meeting-state.json changes,
                          plus a heartbeat comment every ~15s so idle connections aren't reaped
  POST /chair-cmd      -> append one JSON command line to chair-inbox.jsonl, echo it back over SSE

Stdlib only. Runs under ThreadingHTTPServer so a parked SSE connection can't block other requests.

Usage:
  python3 ic-server.py --session <dir> [--port 0] [--page meeting.html]
"""
import argparse
import json
import os
import threading
import time
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))


class State:
    def __init__(self, session, page):
        self.session = session
        self.page_path = page if os.path.isabs(page) else os.path.join(HERE, page)
        self.state_path = os.path.join(session, "meeting-state.json")
        self.inbox_path = os.path.join(session, "chair-inbox.jsonl")
        self.lock = threading.Lock()
        self.last_mtime = 0
        self.subscribers = []  # list of queues (lists) for SSE fan-out

    def read_state(self):
        try:
            with open(self.state_path, "rb") as fh:
                return fh.read()
        except FileNotFoundError:
            return b'{"phase":"waiting","seats":[],"timeline":[]}'

    def etag(self, body):
        return '"' + hashlib.sha1(body).hexdigest()[:16] + '"'

    def append_chair(self, cmd):
        with self.lock:
            with open(self.inbox_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(cmd, ensure_ascii=False) + "\n")

    def broadcast(self, event, data):
        msg = "event: %s\ndata: %s\n\n" % (event, json.dumps(data, ensure_ascii=False))
        dead = []
        for q in list(self.subscribers):
            try:
                q.append(msg)
            except Exception:
                dead.append(q)
        for q in dead:
            if q in self.subscribers:
                self.subscribers.remove(q)


def watcher(state, stop):
    """Poll meeting-state.json mtime; broadcast on change."""
    while not stop.is_set():
        try:
            m = os.path.getmtime(state.state_path)
            if m != state.last_mtime:
                state.last_mtime = m
                body = state.read_state()
                try:
                    state.broadcast("state", json.loads(body))
                except Exception:
                    pass
        except FileNotFoundError:
            pass
        time.sleep(0.1)


def make_handler(state):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):  # quiet
            pass

        def _send(self, code, ctype, body, extra=None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-cache")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if body:
                self.wfile.write(body)

        def do_GET(self):
            if self.path == "/" or self.path.startswith("/index"):
                try:
                    with open(state.page_path, "rb") as fh:
                        self._send(200, "text/html; charset=utf-8", fh.read())
                except FileNotFoundError:
                    self._send(404, "text/plain", b"meeting page not found")
                return
            if self.path.startswith("/state"):
                body = state.read_state()
                etag = state.etag(body)
                if self.headers.get("If-None-Match") == etag:
                    self._send(304, "application/json", b"", {"ETag": etag})
                else:
                    self._send(200, "application/json", body, {"ETag": etag})
                return
            if self.path.startswith("/events"):
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.end_headers()
                q = []
                state.subscribers.append(q)
                # push current state immediately
                try:
                    q.append("event: state\ndata: %s\n\n" % state.read_state().decode("utf-8"))
                except Exception:
                    pass
                last_hb = time.time()
                try:
                    while True:
                        if q:
                            self.wfile.write(q.pop(0).encode("utf-8"))
                            self.wfile.flush()
                        else:
                            if time.time() - last_hb > 15:
                                self.wfile.write(b": heartbeat\n\n")
                                self.wfile.flush()
                                last_hb = time.time()
                            time.sleep(0.05)
                except (BrokenPipeError, ConnectionResetError):
                    pass
                finally:
                    if q in state.subscribers:
                        state.subscribers.remove(q)
                return
            self._send(404, "text/plain", b"not found")

        def do_POST(self):
            if self.path.startswith("/chair-cmd"):
                n = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(n) if n else b"{}"
                try:
                    cmd = json.loads(raw.decode("utf-8"))
                except Exception:
                    cmd = {"type": "message", "text": raw.decode("utf-8", "replace")}
                cmd.setdefault("ts", time.strftime("%H:%M:%S"))
                state.append_chair(cmd)
                state.broadcast("chair", {**cmd, "status": "queued"})
                self._send(200, "application/json", json.dumps({"ok": True, "queued": cmd}).encode("utf-8"))
                return
            self._send(404, "text/plain", b"not found")

    return H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--page", default="meeting.html")
    args = ap.parse_args()

    session = os.path.abspath(args.session)
    os.makedirs(session, exist_ok=True)
    state = State(session, args.page)
    # ensure inbox exists so the moderator's `tail -f` has a file to follow
    open(state.inbox_path, "a").close()

    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(state))
    port = httpd.server_address[1]
    stop = threading.Event()
    t = threading.Thread(target=watcher, args=(state, stop), daemon=True)
    t.start()

    print(json.dumps({
        "ok": True, "url": "http://127.0.0.1:%d/" % port, "port": port,
        "state_path": state.state_path, "inbox_path": state.inbox_path,
    }), flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()


if __name__ == "__main__":
    main()
