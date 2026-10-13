#!/usr/bin/env python3
"""Reaching The Oracle — and never failing to.

Zee, 2026-08-15: "If the oracle is unreachable, fall back to yolo is not good
because in that case, having the oracle mode would be useless. Make sure that
the oracle is never unreachable."

That is an availability instruction first and a policy instruction second, so
this module is mostly the former. "Unreachable" is dismantled into layers, and
each layer removes one way the judge could go missing:

  1. SOCKET      — the daemon is already up. The normal path, ~0ms of overhead.
  2. AUTO-START  — no daemon? Start one and wait for it. A machine that rebooted,
                   or a daemon someone killed, heals itself on the next tool call
                   instead of silently degrading.
  3. DIRECT      — the daemon will not start (bun missing, socket dir unwritable)?
                   Call the SAME model with the SAME charter straight from here.
                   The daemon is a convenience; Opus is the actual judge, and it
                   is reachable without any daemon at all.
  4. RETRY       — transient failure (network blip, CLI restart)? Try again, with
                   backoff, several times.
  5. DENY        — every layer above failed. NOT an allow.

Layer 5 is the part Zee's instruction forces, and it deserves saying out loud:
in Oracle mode an unjudged action is exactly the thing he rejected, so the last
resort is to refuse rather than to wave it through. The cost is real — a machine
with no working Claude CLI and no network would stop being able to run gated
tools. Layers 1-4 exist so that case is close to unreachable itself, and the
denial says precisely what broke so it can be fixed in one step.

Python (not TypeScript) because this is imported by oracle-evaluate.py, an
existing 1050-line Python hook — the "extending existing Python" exception.
"""

import json
import os
import socket
import subprocess
import time
from pathlib import Path

ORACLE_HOME = Path.home() / ".acos" / "oracle"
SOCK = ORACLE_HOME / "oracle.sock"
TOKEN_FILE = ORACLE_HOME / "token"
LOG = ORACLE_HOME / "verdicts.log"
DAEMON = "oracle/oracle-daemon.ts"

# Resolved to a REAL path: `claude` in an interactive shell is a zsh function
# wrapping _acos_cli, which does not exist in a non-interactive shell.
CLAUDE_CANDIDATES = [
    "/opt/homebrew/bin/claude",
    str(Path.home() / ".claude" / "local" / "claude"),
    "/usr/local/bin/claude",
]

# Layer 2/4 budgets. Generous on purpose: Zee chose correctness over speed
# ("think as long as needed"), so nothing here races the judge itself — these
# only bound how long we spend trying to REACH it.
DAEMON_BOOT_WAIT_S = 20.0
RETRY_ATTEMPTS = 3
RETRY_BACKOFF_S = [1.0, 3.0, 6.0]


def _claude_bin():
    for c in CLAUDE_CANDIDATES:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


MODE_FILE_NAME = "oracle-mode.json"


def load_mode(project_root):
    """Oracle mode state, or None when it is off.

    Oracle mode is a SWITCH, not a rung on the 1-12 dial (Zee, 2026-08-16:
    "12 is actually the wrong number for this"). A number implies a ladder where
    higher means looser, and the Oracle is not looser than anything — it is a
    different axis. So it lives in its own file and the dial keeps its meaning.

    Shape: {"active": true, "goal": "...", "started_at": "...", "prev_threshold": 10}
    """
    try:
        p = Path(project_root) / ".acos" / "state" / MODE_FILE_NAME
        if not p.is_file():
            return None
        state = json.loads(p.read_text(encoding="utf-8"))
        return state if state.get("active") else None
    except (OSError, ValueError):
        return None


def read_token():
    try:
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def is_oracle_child():
    """True when THIS process is the Oracle's own judging session.

    The Oracle judges by running Claude Code, and that child loads the same
    PreToolUse hook. Without this the child's first Read would ask the Oracle,
    which would spawn another child, forever.

    The env var must MATCH the 0600 token the daemon owns. A bare flag would be
    a permission bypass anything could set — the same reasoning that removed the
    old ORACLE_THRESHOLD env var (security: H3).
    """
    supplied = os.environ.get("ACOS_ORACLE_JUDGE", "")
    if not supplied:
        return False
    real = read_token()
    return bool(real) and supplied == real


# ── layer 1: the socket ────────────────────────────────────────────────────────

def _ask_socket(payload, connect_timeout=2.0):
    """One attempt against a live daemon. None means 'not reachable this way'.

    No read timeout on purpose: once the daemon has the request, the judge may
    take as long as it needs. Only CONNECTING is bounded.
    """
    if not SOCK.exists():
        return None
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(connect_timeout)
        s.connect(str(SOCK))
        s.settimeout(None)  # the verdict itself is unbounded
        s.sendall(json.dumps(payload).encode("utf-8"))
        chunks = []
        while True:
            b = s.recv(65536)
            if not b:
                break
            chunks.append(b)
        s.close()
        raw = b"".join(chunks).decode("utf-8", "replace").strip()
        return json.loads(raw) if raw else None
    except (OSError, ValueError):
        return None


# ── layer 2: start the daemon and wait for it ─────────────────────────────────

def _daemon_alive():
    """True when the pid in oracle.pid is a live process."""
    try:
        pid = int((ORACLE_HOME / "oracle.pid").read_text().strip())
    except (OSError, ValueError):
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _start_daemon(scripts_dir):
    """Spawn the daemon detached, then wait for its socket to appear.

    Never spawn a SECOND daemon beside a live one (2026-10-12). Every new daemon
    unlinks the socket and rewrites the pid file, but the old process keeps
    running with nothing to serve — 77 of them had piled up. If the pid file
    names a live process, give it a moment to answer and leave it alone; if it
    truly cannot answer, consult() falls through to the direct judge instead.
    """
    if _daemon_alive():
        deadline = time.time() + DAEMON_BOOT_WAIT_S
        while time.time() < deadline:
            if SOCK.exists():
                return True
            time.sleep(0.25)
        return False
    daemon_path = Path(scripts_dir) / DAEMON
    if not daemon_path.is_file():
        return False
    bun = None
    for c in ["/opt/homebrew/bin/bun", str(Path.home() / ".bun" / "bin" / "bun"), "/usr/local/bin/bun"]:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            bun = c
            break
    if bun is None:
        return False
    try:
        ORACLE_HOME.mkdir(parents=True, exist_ok=True)
        out = open(ORACLE_HOME / "daemon-out.log", "a", encoding="utf-8")
        subprocess.Popen(
            [bun, str(daemon_path), "--model", "opus"],
            stdout=out, stderr=out, stdin=subprocess.DEVNULL,
            start_new_session=True,  # survives this hook process exiting
        )
    except OSError:
        return False
    deadline = time.time() + DAEMON_BOOT_WAIT_S
    while time.time() < deadline:
        if SOCK.exists():
            return True
        time.sleep(0.25)
    return False


# ── layer 3: no daemon needed — call the judge directly ───────────────────────

# ── D-14 (2026-10-08): unreadable replies are CLASSIFIED and RECOVERED, never allowed ──
#
# Zee: "make sure that the oracle finds the reason of a verdict being unreadable and finds
# a way to read this and then makes the decision, not just passes it to me." The direct
# layer used to discard stderr and return None, which the caller read as "unreachable".
# Now the prompt goes on STDIN (no E2BIG for big Writes), stderr is kept, the failure is
# classified, and each class has a recovery; the final deny names the class.

LAST_FAILURE = {"class": None, "error": "", "tried": []}


def classify_failure(stdout, stderr, code):
    import re
    both = f"{stdout}\n{stderr}"
    if re.search(r"E2BIG|argument list too long|prompt is too long|too many tokens|exceeds the (maximum|context)|context window", both, re.I):
        return "too_long"
    if re.search(r"usage limit|rate limit|rate_limit|quota|429|overloaded|too many requests|limit reached|You've reached", both, re.I):
        return "usage_limit"
    if re.search(r"not logged in|unauthori[sz]ed|invalid api key|authentication|please run /login|OAuth", both, re.I):
        return "auth"
    if not (stdout or "").strip():
        return "empty" if code == 0 else "crash"
    if re.search(r'\{[^{}]*"decision"', stdout):
        return "malformed"
    return "prose"


def _repair_json(text):
    import re
    t = re.sub(r"```(?:json)?", "", text)
    t = t.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
    t = re.sub(r",\s*([}\]])", r"\1", t)
    t = re.sub(r"'([^'\\]*)'\s*:", r'"\1":', t)
    t = re.sub(r":\s*'([^'\\]*)'", r': "\1"', t)
    return t.replace("True", "true").replace("False", "false").replace("None", "null")


def _spawn_judge(bin_, prompt, env):
    try:
        proc = subprocess.run([bin_, "-p", "--model", "opus"], input=prompt,
                              capture_output=True, text=True, env=env)
        return proc.stdout or "", proc.stderr or "", proc.returncode
    except OSError as e:
        return "", str(e), None


def _ask_direct(payload, charter):
    """The daemon is a convenience. Opus is the judge, and it is reachable here.

    Returns a verdict dict, or None after classify + recover both failed (LAST_FAILURE
    then says why, and consult() puts that into the denial).
    """
    bin_ = _claude_bin()
    if bin_ is None:
        LAST_FAILURE.update({"class": "crash", "error": "claude binary not found", "tried": []})
        return None
    env = dict(os.environ)
    env["ACOS_ORACLE_JUDGE"] = read_token() or "direct"
    env.pop("ANTHROPIC_API_KEY", None)  # standing rule: subscription, never a key
    out, err, code = _spawn_judge(bin_, charter, env)
    v = parse_verdict(out)
    if v:
        return v
    cls = classify_failure(out, err, code)
    tried = []
    prompt = charter
    plans = {
        "empty": ["retry_direct", "shrink_to_file"], "crash": ["retry_direct", "shrink_to_file"],
        "usage_limit": ["wait_then_retry"], "too_long": ["shrink_to_file", "retry_direct"],
        "prose": ["extract_from_prose", "json_only_reask"], "malformed": ["repair_json", "json_only_reask"],
        "auth": ["retry_direct"],
    }
    for action in plans.get(cls, ["retry_direct"]):
        tried.append(action)
        if action == "repair_json":
            v = parse_verdict(_repair_json(out))
            if v:
                return v
            continue
        if action == "shrink_to_file":
            tmp = ORACLE_HOME / "tmp"
            tmp.mkdir(parents=True, exist_ok=True)
            f = tmp / f"prompt-{int(time.time() * 1000)}.txt"
            f.write_text(prompt)
            os.chmod(f, 0o600)
            prompt = (f"Your full instructions and the request to judge are in the file {f}. Read it with the "
                      "Read tool, then answer exactly as its final section says: ONE line of JSON and nothing else.")
            out, err, code = _spawn_judge(bin_, prompt, env)
        elif action == "wait_then_retry":
            time.sleep(30)
            out, err, code = _spawn_judge(bin_, prompt, env)
        elif action == "extract_from_prose":
            ask = ("A permission judge answered in prose instead of JSON. Convert it FAITHFULLY into the required "
                   "JSON and output ONLY the JSON. If the prose says the action is acceptable/ordinary/safe, the "
                   "decision is \"allow\". If it says the action would do real, lasting damage and should not run, "
                   "the decision is \"deny\". Do not add judgement of your own.\n\nRequired shape: "
                   "{\"decision\":\"allow\"|\"deny\",\"reason\":\"<short>\"}\n\n--- THE PROSE ---\n" + out[:20000] + "\n--- END ---")
            out, err, code = _spawn_judge(bin_, ask, env)
        elif action == "json_only_reask":
            out, err, code = _spawn_judge(bin_, prompt + "\n\nREMINDER: output ONLY the single-line JSON object. No prose, no code fences.", env)
        else:
            out, err, code = _spawn_judge(bin_, prompt, env)
        v = parse_verdict(out) or parse_verdict(_repair_json(out))
        if v:
            return v
        cls2 = classify_failure(out, err, code)
        if cls2 != cls:
            cls = cls2
    LAST_FAILURE.update({"class": cls, "error": (err or out)[:300], "tried": tried})
    return None


def parse_verdict(raw):
    """Pull the verdict out of a reply, wherever it sits. None if absent."""
    import re
    text = (raw or "").strip()
    if not text:
        return None
    matches = re.findall(r'\{[^{}]*"decision"\s*:\s*"(?:allow|deny)"[^{}]*\}', text)
    if not matches:
        return None
    try:
        o = json.loads(matches[-1])  # a thinking-aloud reply ends with its answer
    except ValueError:
        return None
    if o.get("decision") in ("allow", "deny"):
        return {"decision": o["decision"], "reason": str(o.get("reason", ""))[:500]}
    return None


def _log(entry):
    try:
        ORACLE_HOME.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def build_charter(tool_name, tool_input, cwd, context, goal=""):
    """Kept byte-identical in meaning to the daemon's charter.

    Layer 3 must judge by the SAME standard as layer 1, or the answer would
    depend on which layer happened to serve it.

    THE GOAL IS EVIDENCE, NOT A GATE. Zee asked for a stated goal on Oracle mode
    (2026-08-16), and it genuinely sharpens the judgement: the live test caught
    `rm -rf ~/Documents` only because the stated task was "clean temp files in
    the build folder", and the mismatch is what exposed the harm. But it must
    never become an "is this on-task?" test — he explicitly rejected that bar
    ("give permission to everything unless it is truly going to cause harm").
    Off-task and harmless is still ALLOW. The charter says so in as many words,
    because this is the exact place the design would rot back into the old one.
    """
    detail = json.dumps(tool_input or {}, indent=1)[:4000]
    goal_block = (
        f"\n--- THE SESSION'S STATED GOAL ---\n{goal[:1500]}\n"
        "Use this as EVIDENCE, not as a test. A command that is off-topic but harmless is "
        "still ALLOW — wandering is not damage. What the goal buys you is the mismatch case: "
        "when a command would destroy something and the stated work does not explain why "
        "anyone would want that destroyed, the gap itself is the warning.\n"
        if goal else ""
    )
    return (
        "You are THE ORACLE. You hold the permission door for Zee's machine, and he is not "
        "going to be asked. Your answer is final and it executes.\n\n"
        "Zee's standing instruction, verbatim:\n"
        '"give permission to everything unless it is truly going to cause harm to my system"\n'
        '"just because an operation is outside the work directory doesn\'t automatically mean it is '
        'harmful, it could still be necessary, touching keys or credentials could be necessary too"\n\n'
        "SO YOUR DEFAULT IS ALLOW. Deleting files, force pushes, editing config, writing outside the "
        "project, reading credentials, installing packages — these are ordinary work. None of them is a "
        "reason to deny on its own.\n\n"
        "DENY only when the command would do REAL, LASTING damage to his computer or his data, and the "
        "surrounding work does not explain why that damage would be wanted. If a mistake here could be "
        "undone, allow.\n\n"
        "You may investigate before answering: read files, inspect the repo. Take as long as you need. "
        "Read only — change nothing.\n\n"
        "Denying ordinary work breaks the promise this is built on and is the failure to fear. "
        "Reserve deny for what you could defend to him in one sentence.\n\n"
        f"{goal_block}"
        f"\n--- THE REQUEST ---\ntool: {tool_name}\ncwd: {cwd}\ninput: {detail}\n\n"
        f"--- RECENT CONVERSATION ---\n{(context or '(none supplied)')[:6000]}\n\n"
        "--- YOUR ANSWER ---\nReply with ONE line of JSON and nothing else:\n"
        '{"decision":"allow","reason":"<short>"}\n'
        'or\n{"decision":"deny","reason":"<the one sentence you would defend to Zee>"}'
    )


def consult(tool_name, tool_input, cwd, context, scripts_dir, goal=""):
    """Get a real verdict. Walks the layers; never silently degrades to allow.

    Returns (decision, reason, layer).
    """
    payload = {"tool_name": tool_name, "tool_input": tool_input, "cwd": cwd,
               "context": context, "goal": goal}

    # Layer 1 — the daemon is already up.
    v = _ask_socket(payload)
    if v and v.get("decision") in ("allow", "deny"):
        return v["decision"], v.get("reason", ""), "socket"

    # Layer 2 — bring it up, then ask again.
    if _start_daemon(scripts_dir):
        v = _ask_socket(payload)
        if v and v.get("decision") in ("allow", "deny"):
            return v["decision"], v.get("reason", ""), "autostart"

    # Layer 3 — skip the daemon entirely; ask the judge directly.
    charter = build_charter(tool_name, tool_input, cwd, context, goal)
    v = _ask_direct(payload, charter)
    if v:
        return v["decision"], v.get("reason", ""), "direct"

    # Layer 4 — transient trouble; try the direct path again with backoff.
    for i in range(RETRY_ATTEMPTS):
        time.sleep(RETRY_BACKOFF_S[min(i, len(RETRY_BACKOFF_S) - 1)])
        v = _ask_direct(payload, charter)
        if v:
            return v["decision"], v.get("reason", ""), f"retry{i + 1}"

    # Layer 5 — no judgement was possible. Refuse, loudly and specifically.
    # Allowing here would be the silent YOLO fallback Zee rejected: the mode
    # would look active while judging nothing at all.
    why = (
        "THE ORACLE COULD NOT OBTAIN A READABLE VERDICT. Every layer failed: no daemon, the daemon "
        "would not start, and a direct judge call failed "
        f"{RETRY_ATTEMPTS + 1} times. Cause class: {LAST_FAILURE.get('class') or 'unknown'}. "
        f"Last error: {LAST_FAILURE.get('error') or '(none)'}. Recovery tried: "
        f"{' -> '.join(LAST_FAILURE.get('tried') or []) or '(none)'}. claude binary: {_claude_bin() or 'NOT FOUND'}. "
        "Refusing rather than allowing unjudged — Oracle mode allows nothing it has "
        "not actually judged. Fix the cause, or set threshold <= 11 to leave Oracle mode."
    )
    _log({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "tool": tool_name,
          "decision": "deny", "reason": why, "layer": "unreachable"})
    return "deny", why, "unreachable"
