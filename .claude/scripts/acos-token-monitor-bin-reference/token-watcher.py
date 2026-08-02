#!/usr/bin/env python3
"""kqueue-based per-session token watcher (production-hardened).

Watches a single Claude Code session JSONL via macOS kernel filesystem events.
Parses the latest `usage` block on each write, computes deterministic token
count + rolling-average forward-looking estimate, fires fire_command when
threshold is crossed, and injects the resume prompt after compaction.

Hardening pass applied:
- Per-session RESUME_PROMPT (no cross-session collision)
- Atomic FIRED_FLAG creation via O_CREAT|O_EXCL
- FIRED_FLAG age-out so a single failed cycle doesn't permanently disable a session
- Consistent metric (`total`) for pre/post comparison
- Tail-seek in parse_last_usage (only scan new bytes)
- Self-healing on malformed RESUME_PENDING
- Config caching by mtime
- Log rotation (size-based, ~5MB cap)
- fire_command regex validation
- All file I/O wrapped in try/except OSError
- subprocess.run with timeout for inject error capture
- PID identity bound to (pid, start_time) for safer reuse detection
"""
import json
import os
import re
import select
import subprocess
import sys
import time
import traceback
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────
MONITOR_HOME = Path.home() / "Library" / "Application Support" / "acos-token-monitor"
BIN_DIR    = MONITOR_HOME / "bin"
STATE_DIR  = MONITOR_HOME / "state"
LOGS_DIR   = MONITOR_HOME / "logs"
CONFIG_FILE = MONITOR_HOME / "config.yaml"
INJECTOR    = BIN_DIR / "inject-keystroke.py"
PID_RESOLVER = BIN_DIR / "resolve-session-pid.py"

JSONL = Path(sys.argv[1])
LOG   = Path(sys.argv[2])

SESSION_ID = JSONL.stem

# Validate session_id format to prevent path traversal
if not re.match(r'^[a-zA-Z0-9_-]{1,128}$', SESSION_ID):
    sys.stderr.write(f"ERROR: invalid session_id format: {SESSION_ID!r}\n")
    sys.exit(1)

# Per-session state files (B1: RESUME_PROMPT now per-session too)
FIRED_FLAG       = STATE_DIR / f".compact-fired-{SESSION_ID}"
RESUME_PENDING   = STATE_DIR / f".resume-pending-{SESSION_ID}"
RESUME_PROMPT    = STATE_DIR / f"pending-resume-{SESSION_ID}.txt"
PID_FILE         = STATE_DIR / f"pid-{SESSION_ID}"
CYCLE_HISTORY    = STATE_DIR / f".cycle-history-{SESSION_ID}"
PARSE_OFFSET     = STATE_DIR / f".parse-offset-{SESSION_ID}"
# 2026-06-11 (Fix 1): shared-contract sidecar. Single line, ASCII integer =
# the latest `approximate` token value, written atomically on every processed
# JSONL event. Read at fire time by eternity-protocol-core.sh — replaces the
# brittle log-scraping of `approx=` lines from the watcher log.
LAST_TOTAL       = STATE_DIR / f".last-total-{SESSION_ID}"
HEARTBEAT        = STATE_DIR / "heartbeat"
# 2026-05-20: skill-to-daemon /clear request channel. The acos-eternity-protocol
# skill writes this flag instead of firing /clear directly — because a running
# Claude agent (skill executing) cannot reliably keystroke-inject into its own
# input field (the input is busy receiving tool output). The daemon, which fires
# from outside the agent loop, hits an idle/ready input field and the keystrokes
# land. So: skill writes flag, exits; daemon polls flag every event, fires /clear.
CLEAR_REQUESTED  = STATE_DIR / f".clear-requested-{SESSION_ID}"
# 2026-05-20 (PM): positive proof marker. Written by check_clear_request() AFTER
# a /clear inject is posted. The NEW session's watcher reads this in
# claim_orphan_resume_if_any() as authoritative evidence that the OLD session
# was committed-dead by *this daemon* — bypassing the unreliable
# "is the old JSONL still being written?" mtime heuristic, which false-positives
# on the trailing writes a Claude process emits to the old JSONL in the second
# or two after /clear lands. Cleared by the new watcher after a successful
# orphan claim. Independent per-session file: writing it does not race with
# any other watcher (each watcher only writes its own SESSION_ID marker).
CLEAR_FIRED      = STATE_DIR / f".clear-fired-{SESSION_ID}"

# ── Constants ─────────────────────────────────────────────────────────
ROLLING_WINDOW = 10
DELTA_CAP = 8000
MIN_SAMPLES_FOR_FIRE = 1  # Lowered from 3 — was blocking cold-start fires

DEFAULT_THRESHOLD = 400_000
# 2026-06-11: fire_command is INFORMATIONAL-ONLY. dispatch_threshold_fire()
# selects the actual slash command per-session by variant (-cmux vs -warp)
# and ignores this value entirely. Retained only for log diagnostics.
# 2026-06-18: cmux engine skill renamed back to "/acos-eternity-protocol".
DEFAULT_FIRE_COMMAND = "/acos-eternity-protocol"
DEFAULT_POST_COMPACT_DROP_PCT = 35

# B5: FIRED_FLAG ages out after this if no resume completion → unblocks daemon
FIRED_FLAG_MAX_AGE_SEC = 600

# 2026-06-11 (Fix 5): INVARIANT — the aborted-compaction suspension window in
# loop_guard_check() MUST coincide with the FIRED_FLAG age-out. Otherwise a
# gap opens where loop_guard_check permits a re-fire but the still-present stale
# FIRED_FLAG blocks try_claim_fire_flag() (the old 300s-vs-600s dead zone).
# Both transitions are now driven by FIRED_FLAG_MAX_AGE_SEC, so the moment the
# guard releases is exactly the moment the flag is eligible to be aged out.
LOOP_WINDOW_SEC = FIRED_FLAG_MAX_AGE_SEC
LOOP_DROP_THRESHOLD_PCT = 20
LOOP_SUSPEND_SEC = 1800

# H7: log rotation
LOG_MAX_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 2

# S2: fire_command must match this pattern
FIRE_COMMAND_REGEX = re.compile(r'^/[A-Za-z][A-Za-z0-9_-]{0,63}$')

# ── Logging (with rotation + try/except wrapping) ──────────────────────
_log_fp = None

def _open_log():
    global _log_fp
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        _log_fp = open(LOG, "a", buffering=1)
    except OSError as e:
        _log_fp = None
        # 2026-06-11: surface the open failure instead of failing silently —
        # otherwise the watcher runs fully blind with no clue why.
        try:
            sys.stderr.write(f"# LOG OPEN FAILED ({LOG}): {e}\n")
        except Exception:
            pass

def _rotate_log_if_needed():
    global _log_fp
    try:
        if LOG.exists() and LOG.stat().st_size > LOG_MAX_BYTES:
            if _log_fp:
                _log_fp.close()
                _log_fp = None
            for i in range(LOG_BACKUP_COUNT - 1, 0, -1):
                src = LOG.with_suffix(LOG.suffix + f".{i}")
                dst = LOG.with_suffix(LOG.suffix + f".{i+1}")
                if src.exists():
                    src.replace(dst)
            LOG.replace(LOG.with_suffix(LOG.suffix + ".1"))
            _open_log()
    except OSError as e:
        # 2026-06-11: surface rotation failure on stderr before giving up.
        try:
            sys.stderr.write(f"# LOG ROTATE FAILED ({LOG}): {e}\n")
        except Exception:
            pass

def log(msg):
    """Safe append to log; never raises."""
    try:
        global _log_fp
        if _log_fp is None:
            _open_log()
        if _log_fp:
            _log_fp.write(msg + "\n")
        else:
            # 2026-06-11: re-open still failed — fall back to stderr so the
            # watcher is never fully blind.
            try:
                sys.stderr.write(msg + "\n")
            except Exception:
                pass
        _rotate_log_if_needed()
    except OSError:
        pass

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-3] + "Z"

# ── Config loading (cached by mtime per H8) ───────────────────────────
_cfg_cache = None
_cfg_mtime = 0

def load_config():
    global _cfg_cache, _cfg_mtime
    defaults = {
        "threshold": DEFAULT_THRESHOLD,
        "fire_command": DEFAULT_FIRE_COMMAND,
        "post_compact_drop_pct": DEFAULT_POST_COMPACT_DROP_PCT,
    }
    try:
        if not CONFIG_FILE.exists():
            return defaults
        mtime = CONFIG_FILE.stat().st_mtime
        if _cfg_cache is not None and mtime == _cfg_mtime:
            return _cfg_cache
        # Cap file size to prevent DoS via huge config (S5/H6)
        if CONFIG_FILE.stat().st_size > 64 * 1024:
            log(f"# CONFIG WARN: file too large, using defaults")
            return defaults
        cfg = dict(defaults)
        text = CONFIG_FILE.read_text(encoding="utf-8", errors="replace")
        for raw in text.splitlines():
            # Strip comments only outside quotes (rough but sufficient)
            if raw.strip().startswith("#"):
                continue
            line = raw.split("#", 1)[0].strip() if '"' not in raw and "'" not in raw else raw.strip()
            if not line or ":" not in line:
                continue
            k, v = (s.strip() for s in line.split(":", 1))
            v = v.strip().strip('"').strip("'")
            if k in ("threshold", "post_compact_drop_pct"):
                try:
                    cfg[k] = int(v)
                except ValueError:
                    log(f"# CONFIG WARN: invalid {k}={v!r}, using default")
            elif k == "fire_command":
                if FIRE_COMMAND_REGEX.match(v):
                    cfg[k] = v
                else:
                    log(f"# CONFIG WARN: fire_command {v!r} failed regex validation, using default")
        # Clamp drop_pct
        cfg["post_compact_drop_pct"] = max(1, min(99, cfg["post_compact_drop_pct"]))
        # 2026-07-05 (P1-G): clamp threshold in the CONSUMER. Range validation
        # lives only in the /acos-eternity-protocol-threshold skill (the WRITER),
        # which is bypassable — a hand-edited or stale config with a too-high
        # threshold parses cleanly and SILENTLY disables all auto-fire (the token
        # count never reaches it); a zero/negative value churns. Out-of-range →
        # fall back to the default so firing can't be silently wedged. To DISABLE
        # eternity, use /acos-eternity-protocol-stop, not a giant threshold.
        if not (50_000 <= cfg["threshold"] <= 2_000_000):
            log(f"# CONFIG WARN: threshold={cfg['threshold']} out of range "
                f"[50000, 2000000]; falling back to default {DEFAULT_THRESHOLD}")
            cfg["threshold"] = DEFAULT_THRESHOLD
        _cfg_cache = cfg
        _cfg_mtime = mtime
        return cfg
    except OSError as e:
        log(f"# CONFIG ERROR: {e}")
        return defaults

# ── PID resolution (B3 + S3 hardening) ────────────────────────────────
# After the 2026-05-20 swarm-research rewrite, PID is no longer required for
# keystroke injection itself — inject-keystroke.py targets the Warp window
# via session-UUID AXTitle marker, not by PID. PID file is still useful for
# diagnostic / liveness checks and to confirm the session is alive before
# firing. The lsof Strategy 2 fallback (resolve-session-pid.py) was deleted
# as Improvement #2 — Agent 09 noted it "rarely works" and caused 30s stalls;
# Agent 10 confirmed no objection to dropping it. The B11 outermost-claude
# parent-walk in register-session-pid.sh is the sole PID resolution path now.
def _process_start_time(pid):
    """Returns process start time as a stable identity attribute."""
    try:
        result = subprocess.run(
            ["ps", "-o", "lstart=", "-p", str(pid)],
            capture_output=True, text=True, timeout=2,
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        return None

def resolve_session_pid(timeout=8):
    """Read the SessionStart-hook-written PID file. Verify (pid, lstart) match
    to defeat PID recycling. The lstart binding is load-bearing — drop it
    only at the cost of catastrophic mis-injection risk. Returns int|None.
    No fallback; if the pid file is missing/invalid, return None and let the
    caller log + skip — do NOT block on lsof tricks."""
    if not PID_FILE.exists():
        return None
    try:
        content = PID_FILE.read_text(encoding="utf-8").strip().splitlines()
        pid = int(content[0])
        if pid <= 1:
            raise ValueError(f"invalid pid {pid}")
        os.kill(pid, 0)
        # Verify identity if start_time was recorded (S3) — defeats PID recycling
        if len(content) > 1:
            expected_start = content[1].strip()
            actual_start = _process_start_time(pid)
            if actual_start and expected_start and actual_start != expected_start:
                log(f"# PID identity mismatch (PID recycled): clearing pid file")
                PID_FILE.unlink(missing_ok=True)
                return None
        return pid
    except (ValueError, OSError, ProcessLookupError, IndexError):
        try: PID_FILE.unlink(missing_ok=True)
        except OSError: pass
        return None

# ── Keystroke injection (B4: error capture; 2026-05-20: CGEvent+AXRaise) ──
def fire_inject(text, log_label, target_session_id=None, verify=True):
    """Inject text into the Claude Code process for a session.

    2026-05-20 rewrite (post-swarm-research): inject-keystroke.py now targets
    the Warp window by session-UUID AXTitle marker (stamped by OSC 2 in
    register-session-pid.sh) and raises it via AX before posting keystrokes
    via CGEventPost(kCGHIDEventTap). PID is logged for diagnostics but not
    passed to the injector — the injector finds Warp's PID itself.

    The injector also performs post-injection JSONL verification (Improvement
    #1) — rc=5 means keystrokes were posted but /clear was not observed within
    3 seconds. In that case we leave RESUME_PENDING/RESUME_PROMPT on disk so
    the UserPromptSubmit hook recovers on the user's next prompt.

    Args:
      target_session_id: override the injection target (defaults to this
        watcher's own SESSION_ID). Used by orphan-claim path on the rare
        case where we want to target a sibling session — but in practice
        we always target our own session.
      verify: pass --no-verify to the injector when False. The injector's
        verification logic specifically looks for `/clear` evidence in the
        JSONL; when injecting anything other than /clear (e.g. typing the
        slash command `/acos-eternity-protocol-resume`), verification would
        always fail with rc=5. Use verify=False in those cases.

    Returns True if injection (and verification, if requested) succeeded.
    """
    target_sid = target_session_id or SESSION_ID
    # Diagnostic PID (not passed to injector)
    pid = resolve_session_pid(timeout=3)
    if pid:
        log(f"# inject mode: CGEvent+AXRaise session_id={target_sid} (target claude pid={pid}, log_label={log_label}, verify={verify})")
    else:
        log(f"# inject mode: CGEvent+AXRaise session_id={target_sid} (pid unknown — injector will rely on AX window-marker match; {log_label}, verify={verify})")

    cmd = [sys.executable, str(INJECTOR),
           "--session-id", target_sid,
           "--from-stdin"]
    if not verify:
        cmd.append("--no-verify")
    try:
        result = subprocess.run(
            cmd, input=text, text=True,
            capture_output=True, timeout=20,
        )
        if result.returncode == 0:
            label = "OK + VERIFIED" if verify else "OK (verification skipped)"
            log(f"# INJECT {label} ({log_label})")
            return True
        elif result.returncode == 5:
            log(f"# INJECT POSTED but UNVERIFIED ({log_label}): no /clear evidence in JSONL — "
                f"keeping pending-resume state for hook recovery. stderr: {result.stderr.strip()[:200]}")
            return False
        else:
            log(f"# INJECT FAILED rc={result.returncode} ({log_label}): {result.stderr.strip()[:200]}")
            return False
    except subprocess.TimeoutExpired:
        log(f"# INJECT TIMEOUT after 20s ({log_label})")
        return False
    except OSError as e:
        log(f"# INJECT ERROR ({log_label}): {e}")
        return False

# ── 2026-05-28: Eternity-protocol variant dispatch ────────────────────
# Replaces the single-skill /acos-eternity-protocol fire with a dispatcher
# that picks the right injection mechanism + skill based on per-session
# environment markers. See feedback_eternity_protocol_variants.md.
#
# Decision tree at threshold-cross:
#   1. state/stop-<sid> exists?         → SKIP (user opted out)
#   2. state/cmux-surface-<sid> exists? → cmux variant via socket RPC
#   3. otherwise                         → warp variant via CGEventPost
CMUX_INJECTOR = STATE_DIR.parent / "bin" / "inject-via-cmux.py"

def is_cmux_session(sid):
    """True if this session was launched inside a cmux surface — the
    SessionStart hook wrote state/cmux-surface-{sid} capturing
    $CMUX_SURFACE_ID."""
    return (STATE_DIR / f"cmux-surface-{sid}").exists()

def read_surface_ref(sid):
    """Return the cmux SURFACE ref for a session id, or None if this session
    is not a cmux session / the ref was never captured.

    The surface ref identifies the PANE, not the session: a /clear mints a
    NEW session UUID inside the SAME cmux surface, so cmux-surface-<old_sid>
    and cmux-surface-<new_sid> hold the SAME ref. It is therefore the correct
    key for deciding whether an orphan resume belongs to THIS pane (see
    claim_orphan_resume_if_any's pane-identity gate, 2026-06-26)."""
    try:
        ref = (STATE_DIR / f"cmux-surface-{sid}").read_text(encoding="utf-8").strip()
        return ref or None
    except OSError:
        return None

def is_session_opted_out(sid):
    """True if /acos-eternity-protocol-stop wrote state/stop-<sid> earlier
    in this session. Cleaned ONLY by an explicit user action (or, historically,
    by SessionEnd — fixed 2026-06-15: see self-terminate cleanup below)."""
    return (STATE_DIR / f"stop-{sid}").exists()

# ── 2026-06-15: cmux health gate (broken-pipe storm prevention) ───────
# Background: the 2026-06-10 Auto-Blogger postmortem showed a single dead
# cmux socket triggering an unbounded fire/fail loop. Every ~625s the
# FIRED_FLAG aged out and the daemon re-fired the same broken RPC against
# the same dead socket, never escalating. This gate:
#   (a) tracks consecutive cmux-fault inject failures in state/.cmux-failures-<sid>
#   (b) writes state/cmux-unhealthy-<sid> after CMUX_MAX_CONSECUTIVE_FAILURES
#   (c) blocks subsequent dispatches until cmux is provably healthy again
#   (d) auto-recovers via `cmux ping` probe when marker is present + socket alive
# The autopilot subordination layer (_autopilot_eternity.py) treats the
# cmux-unhealthy marker as an in-flight eternity marker, so autopilot also
# stands down — preventing further token burn while we can't /clear.
# 2026-07-17: cmux 0.64.x moved its IPC socket from ~/Library/Application Support/cmux/
# to the XDG state dir ~/.local/state/cmux/ — probe both, newest scheme first. Each
# location may hold a `last-socket-path` pointer naming the live socket; a pointer is
# trusted only when the path it names actually exists (the App Support one goes stale
# after the move and kept naming the old location).
_CMUX_SOCKET_CANDIDATES = (
    Path.home() / ".local" / "state" / "cmux" / "cmux.sock",
    Path.home() / "Library" / "Application Support" / "cmux" / "cmux.sock",
)

def _cmux_socket_path():
    """Best-known cmux socket path: a valid last-socket-path pointer wins, then
    the first fixed candidate that exists, else the newest-scheme default (which
    then fails the .exists() checks downstream, as it should)."""
    for cand in _CMUX_SOCKET_CANDIDATES:
        try:
            pointed = Path((cand.parent / "last-socket-path").read_text(encoding="utf-8").strip())
            if pointed.exists():
                return pointed
        except OSError:
            pass
    for cand in _CMUX_SOCKET_CANDIDATES:
        if cand.exists():
            return cand
    return _CMUX_SOCKET_CANDIDATES[0]
CMUX_FAILURES = STATE_DIR / f".cmux-failures-{SESSION_ID}"
CMUX_UNHEALTHY = STATE_DIR / f"cmux-unhealthy-{SESSION_ID}"
CMUX_MAX_CONSECUTIVE_FAILURES = 2

def _read_cmux_failures():
    try:
        return int(CMUX_FAILURES.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return 0

def _write_cmux_failures(n):
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = CMUX_FAILURES.with_suffix(".tmp")
        tmp.write_text(str(n), encoding="utf-8")
        try: os.chmod(tmp, 0o600)
        except OSError: pass
        tmp.replace(CMUX_FAILURES)
    except OSError:
        pass

def cmux_socket_alive():
    """Cheap presence check: does the cmux socket file exist (at any known
    location)? Does NOT prove the listener is alive — that requires `cmux ping`.
    But when no socket file exists we know nothing else needs probing."""
    return _cmux_socket_path().exists()

def cmux_ping_ok(timeout=1.5):
    """Authoritative probe: does the cmux app respond to ping?
    Returns False on timeout / any non-zero exit / OSError launching the CLI."""
    try:
        result = subprocess.run(
            ["cmux", "ping"], capture_output=True, text=True, timeout=timeout,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False

def is_cmux_unhealthy():
    """True if the cmux-unhealthy marker is on disk for this session."""
    return CMUX_UNHEALTHY.exists()

# ── User-visible escalation (P2-H, 2026-07-05) ────────────────────────
# 1391 silent dispatch failures produced ZERO user-facing signal. This makes a
# repeated / hard dispatch failure LOUD: a global alert file (read by the doctor)
# plus a one-shot macOS notification. One-shot per session (ALERTED_MARKER, reset
# on recovery) so it never spams. Every step is wrapped so an alert failure can
# NEVER break the fire path.
ETERNITY_ALERT = STATE_DIR / ".eternity-ALERT"
ALERTED_MARKER = STATE_DIR / f".alerted-{SESSION_ID}"

def _escalate_cmux_alert(reason, log_label):
    try:
        with ETERNITY_ALERT.open("a", encoding="utf-8") as f:
            f.write(f"{now_iso()}  session={SESSION_ID}  {reason}  ({log_label})\n")
    except OSError:
        pass
    if ALERTED_MARKER.exists():
        return
    try:
        ALERTED_MARKER.write_text(now_iso(), encoding="utf-8")
        try: os.chmod(ALERTED_MARKER, 0o600)
        except OSError: pass
    except OSError:
        pass
    try:
        note = f"Eternity dispatch failing: {reason}".replace('"', "'")
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{note}" with title "ACOS Eternity Protocol"'],
            capture_output=True, timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass
    log(f"# ESCALATION: user alert raised — {reason} ({log_label})")

def mark_cmux_failure(log_label, hard=False):
    """Increment the consecutive-failure counter. Writes the unhealthy marker
    once the threshold is crossed (or immediately when hard=True). Call for
    cmux-fault classes (rc=1/3/5/-2/-3). 2026-07-05 (P1-E): hard=True for faults
    that will NOT self-cure by waiting (rc=2 cmux CLI not found, rc=-1 injector
    missing) — mark unhealthy + escalate on the FIRST occurrence. Do NOT call for
    rc=4 no-surface or rc=6 multi-line-rejected (request faults)."""
    n = _read_cmux_failures() + 1
    _write_cmux_failures(n)
    if (hard or n >= CMUX_MAX_CONSECUTIVE_FAILURES) and not CMUX_UNHEALTHY.exists():
        try:
            CMUX_UNHEALTHY.write_text(
                f"marked_at: {now_iso()}\n"
                f"consecutive_failures: {n}\n"
                f"hard_fault: {hard}\n"
                f"log_label: {log_label}\n"
                f"recovery: restart the cmux app — the next dispatch will probe via\n"
                f"          `cmux ping` and auto-clear this marker if cmux responds.\n"
                f"          Manual clear: rm {CMUX_UNHEALTHY}\n",
                encoding="utf-8",
            )
            try: os.chmod(CMUX_UNHEALTHY, 0o600)
            except OSError: pass
            log(f"# CMUX UNHEALTHY MARKER WRITTEN after {n} failure(s) "
                f"(hard={hard}) ({log_label}). Daemon will not attempt cmux injection "
                f"for session {SESSION_ID} until cmux responds to ping or marker is removed.")
        except OSError as e:
            log(f"# CMUX UNHEALTHY MARKER write failed ({log_label}): {e}")
        _escalate_cmux_alert(
            "cmux/injector unresolvable (hard fault)" if hard
            else f"cmux inject failed {n}x consecutively", log_label)

def reset_cmux_failures(log_label):
    """Clear failure counter and unhealthy marker after a successful inject."""
    had_state = CMUX_FAILURES.exists() or CMUX_UNHEALTHY.exists()
    for p in (CMUX_FAILURES, CMUX_UNHEALTHY, ALERTED_MARKER):
        try:
            p.unlink(missing_ok=True)
        except OSError:
            pass
    if had_state:
        log(f"# CMUX HEALTHY: cleared failure counter + unhealthy marker + alert one-shot after successful inject ({log_label})")

def cmux_pre_dispatch_check(log_label):
    """Pre-flight gate before any cmux inject attempt.

    Returns (allow_inject: bool, skip_reason: str|None).
    - allow_inject=True, skip_reason=None: proceed to inject
    - allow_inject=False, skip_reason='...': skip without firing, log the reason

    Side effect: if the unhealthy marker is present but `cmux ping` now
    succeeds, clears the marker (auto-recovery) and returns allow_inject=True.
    This is the only place that does `cmux ping` from the daemon; the
    inject-via-cmux.py does its own ping pre-flight too.
    """
    if not is_cmux_session(SESSION_ID):
        return (True, None)  # not cmux, no gate
    if not cmux_socket_alive():
        return (False, "cmux socket missing (checked "
                + " and ".join(str(c) for c in _CMUX_SOCKET_CANDIDATES) + ")")
    if is_cmux_unhealthy():
        if cmux_ping_ok():
            for p in (CMUX_UNHEALTHY, CMUX_FAILURES):
                try: p.unlink(missing_ok=True)
                except OSError: pass
            log(f"# CMUX RECOVERED: ping OK at {log_label}; cleared unhealthy marker; allowing inject")
            return (True, None)
        return (False, "cmux-unhealthy marker present + ping still failing")
    return (True, None)

def update_cmux_health_after_inject(success: bool, rc: int, log_label: str):
    """Update health tracking based on inject return code.

    Counts toward the consecutive-failure threshold:
        rc=3 (cmux unhealthy / ping failed in injector)
        rc=5 (cmux send returned non-zero)
    Does NOT count (request faults, not cmux faults):
        rc=4 (no surface recorded for session)
        rc=6 (multi-line payload rejected)
        rc=-1/-2/-3 (subprocess launch failure)
    """
    if success:
        reset_cmux_failures(log_label)
        return
    # 2026-07-05 (P1-E): class-independent breaker. Before, only rc in (3,5)
    # counted — so the two failures that ACTUALLY happened (rc=2 cmux CLI not
    # found ×1391, rc=1 injector crash ×718) never tripped the breaker and the
    # daemon retried forever with no escalation. Now every non-request failure is
    # accounted:
    #   rc=2 (cmux CLI not found) / rc=-1 (injector missing) = HARD faults that
    #        will NOT self-cure — mark unhealthy + escalate on the FIRST failure.
    #   rc in (1,3,5,-2,-3) = soft cmux/transport faults — count toward the breaker.
    #   rc in (4,6) = request faults (no surface / multi-line rejected) — NOT counted.
    if rc in (2, -1):
        mark_cmux_failure(log_label, hard=True)
    elif rc in (1, 3, 5, -2, -3):
        mark_cmux_failure(log_label)
    elif rc in (4, 6):
        pass  # request faults, not a cmux health problem
    else:
        log(f"# INJECT unhandled rc={rc} ({log_label}) — counting as soft cmux fault")
        mark_cmux_failure(log_label)

def fire_inject_cmux(text, log_label, target_session_id=None, send_return=True):
    """cmux-variant counterpart to fire_inject. Delegates to
    inject-via-cmux.py which uses cmux's Unix socket RPC (no CGEventPost,
    no AXTitle race, no synthetic keystrokes).

    2026-06-11: returns a (success, rc) tuple instead of a bare bool so
    callers (notably check_clear_request) can distinguish "RPC succeeded"
    from the actual subprocess returncode and avoid writing success markers
    on failure. rc is the injector returncode, or a synthetic negative
    sentinel for pre-subprocess failures:
      -1  = cmux injector missing
      -2  = subprocess timeout
      -3  = OSError launching subprocess
    """
    target_sid = target_session_id or SESSION_ID
    log(f"# inject mode: cmux-rpc session_id={target_sid} ({log_label})")
    if not CMUX_INJECTOR.exists():
        log(f"# INJECT FAILED ({log_label}): cmux injector missing at {CMUX_INJECTOR}")
        return (False, -1)
    cmd = [sys.executable, str(CMUX_INJECTOR),
           "--session-id", target_sid,
           "--from-stdin"]
    if not send_return:
        cmd.append("--no-return")
    try:
        result = subprocess.run(
            cmd, input=text, text=True,
            capture_output=True, timeout=20,
        )
        if result.returncode == 0:
            log(f"# INJECT OK cmux-rpc ({log_label})")
            return (True, 0)
        log(f"# INJECT FAILED cmux-rpc rc={result.returncode} ({log_label}): {result.stderr.strip()[:200]}")
        return (False, result.returncode)
    except subprocess.TimeoutExpired:
        log(f"# INJECT TIMEOUT cmux-rpc after 20s ({log_label})")
        return (False, -2)
    except OSError as e:
        log(f"# INJECT ERROR cmux-rpc ({log_label}): {e}")
        return (False, -3)

# ── Carrier arbitration (2026-07-05) ──────────────────────────────────
# The in-pane hooks (eternity-cmux-inpane.sh Stop, eternity-cmux-resume-inpane.sh
# SessionStart), enabled by the global marker state/.cmux-inpane-inject, perform
# /acos-eternity-protocol, /clear and resume from INSIDE the cmux pane — where
# cmux's in-pane-only Unix socket is reachable. The DETACHED daemon CANNOT reach
# that socket, and when in-pane mode is on it must NOT also inject, or both carriers
# fire and you get a double-/clear / duplicate resume. So when in-pane mode is on
# for a cmux session the daemon is DETECTION-ONLY (it still writes .last-total-<sid>
# for the in-pane Stop hook to read). This matches the documented split in
# eternity-cmux-inpane.sh: "the daemon DETECTS ... this hook does the INJECTION."
INPANE_INJECT_MARKER = STATE_DIR / ".cmux-inpane-inject"
_inpane_standdown_logged = [False]

def inpane_carrier_active():
    """True when the in-pane hooks own cmux injection for THIS session, so the
    daemon must stand down from injecting (detection-only). Logs once per process."""
    active = INPANE_INJECT_MARKER.exists() and is_cmux_session(SESSION_ID)
    if active and not _inpane_standdown_logged[0]:
        log(f"# CARRIER: in-pane inject marker present + cmux session {SESSION_ID} — "
            f"daemon is DETECTION-ONLY; in-pane hooks own /clear + fire + resume")
        _inpane_standdown_logged[0] = True
    return active

def dispatch_threshold_fire(cfg, log_label):
    """Dispatch the threshold-cross fire to the right variant.

    Replaces the single fire_inject(cfg['fire_command']) call. cfg['fire_command']
    is ignored — the variant decides which slash command fires.

    2026-06-11: returns a tri-state string instead of a bool so the caller
    can record cycle history ONLY for fires that actually happened:
      "FIRED"  = cmux injection succeeded (rc==0)
      "NOOP"   = nothing attempted by design (warp manual-only, or opted out)
      "FAILED" = cmux injection was attempted but failed
    """
    if inpane_carrier_active():
        return "NOOP"
    if is_session_opted_out(SESSION_ID):
        log(f"# OPT-OUT: stop-{SESSION_ID} present — skipping threshold fire ({log_label})")
        return "NOOP"
    if is_cmux_session(SESSION_ID):
        # 2026-06-15: pre-gate via cmux health check. Skip dispatch entirely
        # (no FIRED_FLAG burn) when cmux is provably unhealthy.
        allow, reason = cmux_pre_dispatch_check(f"threshold {log_label}")
        if not allow:
            log(f"# DISPATCH: cmux variant suppressed for session {SESSION_ID} — {reason} ({log_label})")
            return "NOOP"
        log(f"# DISPATCH: cmux variant for session {SESSION_ID} ({log_label})")
        success, rc = fire_inject_cmux("/acos-eternity-protocol",
                                       log_label=f"cmux-threshold {log_label}")
        update_cmux_health_after_inject(success, rc, f"threshold {log_label}")
        return "FIRED" if success else "FAILED"
    # 2026-06-04: warp variant is MANUAL-ONLY now.
    #
    # Why: the original design auto-fired the Warp manual-handoff skill via
    # CGEventPost+AXRaise at the 400k crossing. In multi-Warp-window setups
    # (the user has 14+ alive claude PIDs across many windows), the AXTitle
    # marker race makes that injection fail rc=4 essentially every time
    # (verified live in ca7fd322 daemon log on 2026-06-04). The May 28
    # OK_SOLE_WINDOW fallback would only help in single-window setups, which
    # the user doesn't have.
    #
    # Instead of theatrical failed injections cluttering the log, the daemon
    # now just logs a heads-up and lets the user manually invoke the skill
    # when they decide to /clear. The handoff-paired pointer + sibling
    # mechanism (2026-06-04 build) makes manual invocation actually useful
    # across days — the user types the slash command themselves, artifacts
    # are produced + persisted, and any later /acos-eternity-protocol-resume
    # in the same pane (even days later) picks up the right handoff.
    log(f"# DISPATCH: warp variant THRESHOLD CROSSED for session {SESSION_ID} ({log_label}) — "
        f"auto-fire disabled in this configuration; manual invocation required. "
        f"Type /acos-continue in the conversation before /clear.")
    return "NOOP"

# ── Cycle history (atomic via tmp+replace, with locking) ──────────────
def read_cycle_history():
    if not CYCLE_HISTORY.exists():
        return []
    try:
        return json.loads(CYCLE_HISTORY.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

def write_cycle_history(history):
    try:
        CYCLE_HISTORY.parent.mkdir(parents=True, exist_ok=True)
        tmp = CYCLE_HISTORY.with_suffix(CYCLE_HISTORY.suffix + ".tmp")
        tmp.write_text(json.dumps(history), encoding="utf-8")
        try: os.chmod(tmp, 0o600)
        except OSError: pass
        tmp.replace(CYCLE_HISTORY)
    except OSError as e:
        log(f"# CYCLE HISTORY WRITE FAILED: {e}")

def loop_guard_check(approximate):
    """Returns True if firing is suspended (inside cooldown)."""
    history = read_cycle_history()
    if not history:
        return False
    now = time.time()
    last = history[-1]
    last_fired = last.get("fired_at", 0)
    # Aborted-compaction detection (H3): if last fire never resolved AND we're
    # still within the suspension window, suspend. 2026-06-11 (Fix 5):
    # LOOP_WINDOW_SEC == FIRED_FLAG_MAX_AGE_SEC by definition, so the instant
    # this guard releases is the instant fired_flag_age_out() becomes eligible
    # to clear the stale FIRED_FLAG — no dead zone where the guard says "go" but
    # the flag still says "blocked".
    if last.get("post_total") is None and (now - last_fired) < LOOP_WINDOW_SEC:
        return True
    # Ineffective compaction guard (use float division per finding)
    if last.get("post_total") is not None:
        pre = last.get("pre_total", 0)
        post = last.get("post_total", 0)
        if pre > 0:
            drop_pct = (pre - post) * 100.0 / pre
            if drop_pct < LOOP_DROP_THRESHOLD_PCT and (now - last_fired) < LOOP_SUSPEND_SEC:
                log(f"# LOOP GUARD: prev drop {drop_pct:.1f}% < {LOOP_DROP_THRESHOLD_PCT}%, suspended")
                return True
    return False

CYCLE_COUNTER = STATE_DIR / f".cycle-counter-{SESSION_ID}"

def _read_cycle_counter():
    """Monotonic cycle counter, separate from history (which caps at 50)."""
    try:
        return int(CYCLE_COUNTER.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return 0

def _write_cycle_counter(n):
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = CYCLE_COUNTER.with_suffix(".tmp")
        tmp.write_text(str(n), encoding="utf-8")
        try: os.chmod(tmp, 0o600)
        except OSError: pass
        tmp.replace(CYCLE_COUNTER)
    except OSError:
        pass

def record_fire_event(pre_total):
    cycle_n = _read_cycle_counter() + 1
    _write_cycle_counter(cycle_n)
    history = read_cycle_history()
    history.append({
        "cycle": cycle_n,
        "fired_at": time.time(),
        "pre_total": pre_total,
        "post_total": None,
    })
    history = history[-50:]
    write_cycle_history(history)
    return cycle_n

def record_compaction_complete(post_total):
    history = read_cycle_history()
    if history and history[-1].get("post_total") is None:
        history[-1]["post_total"] = post_total
        history[-1]["resumed_at"] = time.time()
        write_cycle_history(history)

# ── FIRED_FLAG: atomic creation + age-out ─────────────────────────────
def try_claim_fire_flag(content):
    """Atomic flag creation using O_CREAT|O_EXCL (H1).
    Returns True iff this caller created the flag."""
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        # Mode 0o600: only owner can read/write
        fd = os.open(str(FIRED_FLAG), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.write(fd, content.encode("utf-8"))
            os.fchmod(fd, 0o600)
        finally:
            os.close(fd)
        return True
    except FileExistsError:
        return False
    except OSError as e:
        log(f"# FIRED_FLAG write error: {e}")
        return False

def fired_flag_age_out():
    """B5: clear FIRED_FLAG if it's stale.
    Stale = older than FIRED_FLAG_MAX_AGE_SEC AND either:
      (a) cycle history's last entry has post_total=None (cycle never completed), OR
      (b) cycle history is empty/missing (no record of any cycle — flag is orphaned)."""
    if not FIRED_FLAG.exists():
        return
    try:
        age = time.time() - FIRED_FLAG.stat().st_mtime
        if age <= FIRED_FLAG_MAX_AGE_SEC:
            return
        history = read_cycle_history()
        is_orphaned = not history
        is_unresolved = history and history[-1].get("post_total") is None
        if is_orphaned or is_unresolved:
            reason = "orphaned (no cycle history)" if is_orphaned else "unresolved cycle"
            log(f"# FIRED_FLAG aged out after {int(age)}s — {reason} — clearing")
            FIRED_FLAG.unlink(missing_ok=True)
            RESUME_PENDING.unlink(missing_ok=True)
    except OSError:
        pass

# ── Watcher self-termination (Fix 6: fleet has no reaper) ─────────────
# 2026-06-11: the eternity-protocol fleet spawns one watcher per claude
# session but nothing reaps a watcher when its claude CLI exits. This leaves
# orphaned python processes accumulating. The claude PID is stable across
# /clear within a pane, so a dead PID reliably means the CLI exited — no grace
# period needed beyond requiring the pid file to exist.
def self_terminate_if_owner_dead():
    """If pid-<sid> exists, parses as an int, and os.kill(pid, 0) raises
    ProcessLookupError (the owning claude CLI is gone), clean up THIS
    session's EPHEMERAL state files and sys.exit(0). PermissionError counts
    as ALIVE (we just can't signal it). Recovery artifacts owned by other
    mechanisms (.resume-pending-*, pending-resume-*.txt, .eternity-pointer-pid-*,
    .clear-fired-*, consumed/) are NEVER deleted here."""
    if not PID_FILE.exists():
        return
    try:
        first = PID_FILE.read_text(encoding="utf-8").strip().splitlines()
        if not first:
            return
        pid = int(first[0])
    except (OSError, ValueError, IndexError):
        return
    if pid <= 1:
        return
    try:
        os.kill(pid, 0)
        return  # alive
    except PermissionError:
        return  # exists but not ours to signal — treat as ALIVE
    except ProcessLookupError:
        pass    # dead — fall through to cleanup
    except OSError:
        return  # any other signalling error: be conservative, do nothing
    log(f"# SELF-TERMINATE: owning claude pid {pid} is gone (ProcessLookupError) — "
        f"cleaning up this session's ephemeral state and exiting")
    # ONLY ephemeral, this-session-owned state. NOT resume/recovery artifacts.
    #
    # 2026-06-15: `stop-{SESSION_ID}` REMOVED from this cleanup tuple. Background:
    # the 2026-06-10 Auto-Blogger storm showed the prior watcher tearing down
    # the user's opt-out marker when its locally-tracked claude PID went away,
    # then a fresh watcher coming up clean with no opt-out and re-firing the
    # broken cmux RPC. Stop markers represent an EXPLICIT user intent ("do not
    # fire eternity-protocol for this session") and must outlive any one
    # watcher process. They are now only cleared by an explicit user action
    # (e.g., `rm state/stop-<sid>`). Leaving stop markers behind across watcher
    # restarts is the correct behavior — if the session is genuinely gone, the
    # marker is harmless garbage; if the session is alive under a re-spawned
    # watcher, the opt-out is preserved.
    # 2026-07-05 (P1-F): cmux-surface-{SESSION_ID} REMOVED from this cleanup tuple.
    # The surface ref is STABLE pane identity (used by the cross-pane resume guard),
    # not ephemeral state. A stale/empty pid-<sid> could make self_terminate fire
    # spuriously and delete a surface still needed to gate an orphan-resume claim.
    # Session ids are unique UUIDs (never reused), so leaving it is harmless.
    for p in (PID_FILE,
              PARSE_OFFSET,
              LAST_TOTAL):
        try:
            p.unlink(missing_ok=True)
        except OSError as e:
            log(f"# self-terminate cleanup: failed to remove {p.name}: {e} (harmless)")
    sys.exit(0)

# ── Heartbeat (atomic write) ──────────────────────────────────────────
def heartbeat():
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = HEARTBEAT.with_suffix(".tmp")
        tmp.write_text(f"{time.time():.0f}\n", encoding="utf-8")
        try: os.chmod(tmp, 0o600)
        except OSError: pass
        tmp.replace(HEARTBEAT)
    except OSError:
        pass

# ── JSONL parsing (B7: tail-seek) ─────────────────────────────────────
def _read_persistent_offset():
    try:
        return int(PARSE_OFFSET.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return 0

def _write_persistent_offset(offset):
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        PARSE_OFFSET.write_text(str(offset), encoding="utf-8")
    except OSError:
        pass

def _write_last_total(approximate):
    """2026-06-11 (Fix 1): publish the latest `approximate` token value to the
    shared-contract sidecar .last-total-<sid> for eternity-protocol-core.sh to
    read at fire time. Atomic (tmp + os.replace), cheap (plain str(int), no
    formatting/commas). Never raises."""
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = LAST_TOTAL.with_suffix(LAST_TOTAL.suffix + ".tmp")
        tmp.write_text(str(int(approximate)), encoding="utf-8")
        try: os.chmod(tmp, 0o600)
        except OSError: pass
        os.replace(str(tmp), str(LAST_TOTAL))
    except OSError:
        pass

# Module-level state for the most recent usage seen this run
_latest_usage = None

def parse_latest_usage_incremental(path):
    """Tail-seek: only read NEW bytes since last call. Returns the latest
    (input, cache_read, cache_create, output) tuple seen so far this run.
    Falls back to a full scan on first call or after rotation."""
    global _latest_usage
    try:
        size = path.stat().st_size
    except OSError:
        return _latest_usage

    last_offset = _read_persistent_offset()
    # Detect rotation/truncation: file shrunk
    if size < last_offset:
        last_offset = 0
        _latest_usage = None

    # 2026-06-11 (Fix 8): bound the offset-0 full-scan cost. The JSONL can be
    # hundreds of MB at 400k tokens; reading+decoding the whole thing on a
    # cold start (or post-rotation reset) is wasteful since only the LATEST
    # usage block matters. If we'd start from 0 on a large file, jump near the
    # end, discard the partial first line, and parse from the next newline.
    # The persisted offset is set to that seek point so the incremental path
    # continues correctly from there afterward.
    TAIL_SCAN_BYTES = 262144  # 256 KB
    if last_offset == 0 and size > TAIL_SCAN_BYTES:
        seek_to = size - TAIL_SCAN_BYTES
        try:
            with open(path, "rb") as f:
                f.seek(seek_to)
                # Discard bytes through the first newline so we never parse a
                # truncated JSON line. If there is no newline in the tail window
                # (a single >256KB line — pathological), fall back to scanning
                # the whole tail window as-is.
                first_chunk = f.read(TAIL_SCAN_BYTES)
            nl = first_chunk.find(b"\n")
            # last_offset now points at a clean line boundary (just after a
            # newline), so the partial-last-line trim logic below stays correct.
            last_offset = seek_to + (nl + 1 if nl >= 0 else 0)
        except OSError:
            return _latest_usage

    try:
        with open(path, "rb") as f:
            f.seek(last_offset)
            new_bytes = f.read()
        new_offset = last_offset + len(new_bytes)
        # Decode and process line by line
        try:
            text = new_bytes.decode("utf-8", errors="replace")
        except Exception:
            return _latest_usage
        # Handle partial last line: only commit offset up to last \n
        if not new_bytes.endswith(b"\n"):
            last_nl = text.rfind("\n")
            if last_nl >= 0:
                text = text[:last_nl + 1]
                new_offset = last_offset + len(text.encode("utf-8"))
            else:
                # Entire chunk is partial; defer
                return _latest_usage
        for line in text.splitlines():
            # Pre-filter: only parse lines that look like they have usage
            if '"usage"' not in line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            u = d.get("message", {}).get("usage")
            if u and "input_tokens" in u:
                _latest_usage = (
                    u.get("input_tokens", 0),
                    u.get("cache_read_input_tokens", 0),
                    u.get("cache_creation_input_tokens", 0),
                    u.get("output_tokens", 0),
                )
        _write_persistent_offset(new_offset)
        return _latest_usage
    except OSError:
        return _latest_usage

# ── Event logging ─────────────────────────────────────────────────────
def log_event(evt_n, total, delta, ms_since_last, components, avg_delta, approximate):
    i, cr, cc, o = components
    msg = (f"{now_iso()}  evt={evt_n:<3}  total={total:>7,}  "
           f"+out={total+o:>7,}  approx={approximate:>7,}  "
           f"delta={delta:>+7}  avg={int(avg_delta):>5}  ms={ms_since_last:>6}")
    log(msg)

# ── Post-/clear orphan resume adoption ────────────────────────────────
#
# When the eternity-protocol skill fires `/clear`, Claude Code mints a NEW
# session UUID inside the same Warp process. The skill wrote per-session
# state files keyed to the OLD SID:
#
#     pending-resume-<old_sid>.txt    (the resume prompt content)
#     .resume-pending-<old_sid>       (the sidecar with pre_compact_total)
#
# A fresh watcher then spawns for the NEW SID. Its `check_post_compact()`
# looks for `.resume-pending-<new_sid>` — which doesn't exist — and exits
# without doing anything. The resume injection never happens autonomously.
# Until 2026-05-20 this gap was papered over by relying on a UserPromptSubmit
# hook to recover the resume on the user's next keystroke, but that requires
# a human stimulus — defeating the "eternity" property of the protocol.
#
# This function closes the gap: at startup, scan for orphan
# `.resume-pending-*` sidecars whose `project_dir_key` matches THIS watcher's
# project directory, and whose original SID's JSONL is no longer being
# actively written (i.e., the original session is dead). For the most recent
# matching orphan, type `/acos-eternity-protocol-resume` into THIS session
# via the same CGEvent+AXRaise injector. The resume skill takes over from
# there — it finds the pending-resume file, injects the content, and cleans
# up the sidecar/prompt files.
#
def claim_orphan_resume_if_any():
    """Returns True if an orphan was claimed (and slash command typed)."""
    if inpane_carrier_active():
        # In-pane SessionStart resume hook owns autonomous post-/clear resume for
        # cmux; the daemon must not also claim + inject (double-resume race).
        return False
    project_dir_key = JSONL.parent.name  # e.g., -Users-zee-Documents-Vibe-Coding-ACOS-3-0
    if not project_dir_key:
        return False
    try:
        candidates = sorted(
            (p for p in STATE_DIR.glob(".resume-pending-*") if p.is_file()),
            key=lambda p: p.stat().st_mtime,
            reverse=True,  # newest first
        )
    except OSError:
        return False
    for cand in candidates:
        # Skip our own sidecar (check_post_compact handles that)
        if cand.name == f".resume-pending-{SESSION_ID}":
            continue
        try:
            text = cand.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        cand_project = None
        cand_resume_path = None
        for raw in text.splitlines():
            if raw.startswith("project_dir_key:"):
                cand_project = raw.split(":", 1)[1].strip()
            elif raw.startswith("resume_prompt_file:"):
                cand_resume_path = raw.split(":", 1)[1].strip()
        # Backwards compat: sidecars written before project_dir_key was added
        # have no project_dir_key. We cannot safely claim those (could be from
        # a different project). Skip them — the user can fall back to the
        # manual /acos-eternity-protocol-resume skill.
        if not cand_project:
            log(f"# orphan candidate {cand.name} lacks project_dir_key — skipping (pre-2026-05-20 format)")
            continue
        if cand_project != project_dir_key:
            continue
        # ── Pane-identity gate (2026-06-26) ───────────────────────────────
        # project_dir_key is NOT a sufficient identity. Two Claude panes can run
        # in the SAME project directory at once — the 2026-06-26 incident had an
        # "SEO" pane and a "Hypercore" pane both under ACOS 3.0. The 2026-05-20
        # project-scoping fix stops cross-PROJECT leakage but NOT cross-PANE-
        # same-project leakage: the SEO pane's post-/clear watcher claimed the
        # Hypercore pane's armed resume sidecar and resumed the wrong handoff.
        #
        # The cmux SURFACE ref is stable across /clear (a new SID is minted in
        # the SAME pane) and distinct across panes, so it identifies the PANE.
        # If THIS watcher and the orphan both have a known surface and they
        # DIFFER, the orphan belongs to another pane — never claim it. When
        # either surface is unknown (e.g. a Warp session, which is manual-fire
        # only) we fall through to the prior project-only behavior.
        orphan_sid_probe = cand.name.replace(".resume-pending-", "", 1)
        my_surface = read_surface_ref(SESSION_ID)
        orphan_surface = read_surface_ref(orphan_sid_probe)
        # 2026-07-05 (P1-F): fail CLOSED for cmux sessions whose surface we cannot
        # read — without a known surface we cannot prove the orphan belongs to our
        # pane, so refuse rather than fall through to project-only matching (the
        # exact hole that let a sibling pane's resume get adopted). Warp sessions
        # (no surface concept) keep the prior project-only behavior.
        if is_cmux_session(SESSION_ID) and not my_surface:
            log(f"# orphan {cand.name}: cmux session but my surface is unknown — "
                f"refusing cross-SID claim (fail-closed pane guard)")
            continue
        if my_surface and orphan_surface and my_surface != orphan_surface:
            log(f"# orphan {cand.name}: surface {orphan_surface[:8]} "
                f"!= my surface {my_surface[:8]} — different pane in same "
                f"project, NOT claiming (cross-pane contamination guard)")
            continue
        # Verify the resume prompt file still exists
        if not cand_resume_path or not Path(cand_resume_path).exists():
            log(f"# orphan {cand.name}: resume_prompt_file missing — skipping")
            continue
        # 2026-05-20 (PM): Two-tier liveness check for the source session.
        # The OLD mtime-only heuristic false-positives on the 1–2 trailing
        # writes Claude emits to the old JSONL after /clear lands, which is
        # exactly the window where the new watcher does its startup orphan
        # scan. Result: legitimate post-/clear orphans got skipped, breaking
        # autonomous resume (Jason had to manually fire
        # /acos-eternity-protocol-resume — see daemon logs 2026-05-20 17:30).
        #
        # New logic:
        #   (1) Prefer .clear-fired-<orphan_sid> marker as positive proof
        #       the daemon committed to /clear for that session. If present,
        #       claim is safe regardless of JSONL mtime.
        #   (2) Fall back to the original 60s mtime heuristic when no marker
        #       exists (e.g., user typed /clear manually, or skill→flag→daemon
        #       path was bypassed). Preserves the multi-pane safety net.
        orphan_sid = cand.name.replace(".resume-pending-", "", 1)
        orphan_jsonl = JSONL.parent / f"{orphan_sid}.jsonl"
        clear_fired_marker = STATE_DIR / f".clear-fired-{orphan_sid}"
        marker_present = clear_fired_marker.exists()
        if marker_present:
            log(f"# orphan {cand.name}: .clear-fired marker present — positive proof of /clear, claiming")
        else:
            # No marker → fall back to mtime heuristic. Same behavior as pre-fix
            # for the manual-/clear or pre-skill-rewrite flows.
            try:
                if orphan_jsonl.exists() and (time.time() - orphan_jsonl.stat().st_mtime) < 60:
                    log(f"# orphan {cand.name}: no .clear-fired marker and source JSONL still active — skipping")
                    continue
            except OSError:
                pass
        # 2026-06-11: ATOMIC CLAIM. Two watchers can start near-simultaneously
        # (e.g. SessionStart self-spawn + a launcher reconcile) and both scan
        # the same orphan sidecar. Atomically rename the sidecar to a
        # ".claimed-by-<SESSION_ID>" name via os.rename (POSIX-atomic on the
        # same filesystem). Exactly one watcher's rename wins; the loser gets
        # FileNotFoundError and skips this candidate. On injection failure we
        # rename the sidecar back so a later watcher can retry.
        claimed = cand.with_name(cand.name + f".claimed-by-{SESSION_ID}")
        try:
            os.rename(str(cand), str(claimed))
        except FileNotFoundError:
            log(f"# orphan {cand.name}: already claimed by another watcher — skipping")
            continue
        except OSError as e:
            log(f"# orphan {cand.name}: claim rename failed ({e}) — skipping")
            continue

        log(f"# ORPHAN RESUME CLAIM: sibling session {orphan_sid[:8]} "
            f"(project_dir_key={cand_project}, marker={'yes' if marker_present else 'no'}) — "
            f"claimed sidecar as {claimed.name}; typing /acos-eternity-protocol-resume into my session")
        # We type the slash command (not the resume content). The skill
        # already knows how to find the orphan pending-resume-*.txt by mtime
        # and types it via inject-keystroke.py. Single source of truth for
        # resume mechanics; small reliable keystroke payload.
        #
        # 2026-06-11: variant-aware injection — cmux sessions use the
        # Unix-socket RPC injector (no CGEventPost / AXTitle race), mirroring
        # dispatch_threshold_fire() and check_post_compact().
        if is_cmux_session(SESSION_ID):
            success, _rc = fire_inject_cmux(
                "/acos-eternity-protocol-resume",
                log_label=f"orphan-claim cmux from {orphan_sid[:8]}",
            )
        else:
            success = fire_inject(
                "/acos-eternity-protocol-resume\n",
                log_label=f"orphan-claim from {orphan_sid[:8]}",
                verify=False,  # we're not firing /clear; skip /clear-evidence verify
            )
        if success:
            log(f"# orphan-claim slash command typed; resume skill will complete injection + cleanup")
            # The resume skill finds the pending-resume by mtime; the claimed
            # sidecar is left in place (renamed) as a record. Clean up the
            # .clear-fired-<orphan_sid> marker now that the orphan has been
            # claimed. The resume skill handles pending-resume-<orphan_sid>.txt
            # cleanup itself (its Step 5).
            try:
                clear_fired_marker.unlink(missing_ok=True)
                log(f"# .clear-fired-{orphan_sid[:8]} marker cleaned up post-claim")
            except OSError as e:
                log(f"# .clear-fired marker cleanup failed: {e} (harmless)")
        else:
            # Injection failed: rename the sidecar back to its original name so
            # a later watcher (or this one on a future tick) can retry the claim.
            try:
                os.rename(str(claimed), str(cand))
                log(f"# orphan-claim injection FAILED — sidecar restored to {cand.name}; "
                    f"state preserved; a later watcher can retry / user can invoke manually")
            except OSError as e:
                log(f"# orphan-claim injection FAILED and sidecar restore failed ({e}); "
                    f"sidecar left as {claimed.name} — user can invoke manually")
        return success
    return False

# ── Resume-payload sanitization (Fix E, 2026-06-11) ───────────────────
# SMOOTHNESS-SAFE form ONLY. This must be INCAPABLE of altering or blocking a
# legitimate resume prompt. A normal resume prompt is a few KB of UTF-8 markdown
# containing no NUL and no C0 control chars other than tab/newline/CR — so it
# passes through byte-for-byte. The two guards below only ever trigger on
# genuinely corrupt content, and even then we LOG-AND-PROCEED (truncate, never
# abort) so a degraded payload can't break the loop.
INJECT_PAYLOAD_MAX_BYTES = 262144  # 256 KB — generous; a real prompt is a few KB

# Allow tab(0x09), newline(0x0A), carriage-return(0x0D). Strip NUL + all other
# C0 controls (0x00-0x1F) and DEL (0x7F). Normal prompts contain none of these.
_DANGEROUS_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

def sanitize_inject_payload(text, log_label="event"):
    """Return text safe to type/inject into the surface.

    - Strips only genuinely dangerous control characters (NUL + C0 controls
      except \\t \\n \\r, plus DEL). Legit multi-KB markdown is untouched.
    - Caps size at 256 KB; over the cap (corruption only) → loud WARNING +
      truncate, NEVER abort. Under the cap = pass through byte-for-byte.
    """
    if not text:
        return text
    cleaned = _DANGEROUS_CTRL_RE.sub("", text)
    if cleaned != text:
        removed = len(text) - len(cleaned)
        log(f"# WARNING: sanitize_inject_payload stripped {removed} dangerous "
            f"control char(s) from resume payload ({log_label}) — legit prompts "
            f"contain none; this implies upstream corruption")
    # Size cap measured in bytes (UTF-8), matching the contract.
    encoded = cleaned.encode("utf-8")
    if len(encoded) > INJECT_PAYLOAD_MAX_BYTES:
        log(f"# WARNING: resume payload {len(encoded)} bytes exceeds "
            f"{INJECT_PAYLOAD_MAX_BYTES}-byte ceiling ({log_label}) — TRUNCATING "
            f"(injection still proceeds; this implies upstream corruption)")
        truncated = encoded[:INJECT_PAYLOAD_MAX_BYTES]
        # Decode back, dropping any byte that the truncation split mid-codepoint.
        cleaned = truncated.decode("utf-8", errors="ignore")
    return cleaned

# ── Post-compact resume injection ─────────────────────────────────────
def check_post_compact(total, cfg, log_label="event"):
    """Returns True if resume was fired."""
    if inpane_carrier_active():
        # In-pane SessionStart resume hook (eternity-cmux-resume-inpane.sh) owns
        # the post-/clear resume; leave RESUME_PENDING/RESUME_PROMPT on disk for it.
        return False
    if not RESUME_PENDING.exists():
        return False
    # Refuse to fire if total is 0 (cold start with stale flag scenario, H3)
    if total <= 0:
        return False
    try:
        content = RESUME_PENDING.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    pre_compact_total = 0
    # 2026-06-11 (Fix 2): core.sh may now mark the baseline as a guess (it
    # could not obtain a real measured pre-clear total) by writing the line
    # `pre_compact_total_defaulted: true` into the sidecar. Absent = real
    # measurement. This is observability only — behavior is unchanged.
    pre_compact_defaulted = False
    for raw in content.splitlines():
        if raw.startswith("pre_compact_total:"):
            try:
                pre_compact_total = int(raw.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif raw.startswith("pre_compact_total_defaulted:"):
            if raw.split(":", 1)[1].strip().lower() == "true":
                pre_compact_defaulted = True
    # H4: malformed RESUME_PENDING — self-heal
    # 2026-06-10: split the original "<=0 or >10M" check into two clauses.
    # - >10M is still treated as definitive corruption (impossibly large
    #   token count) → delete marker.
    # - <=0 is now treated as a recoverable derivation failure. The artifacts
    #   (handoff + resume prompt) might still be valid; the upstream skill
    #   may have failed to parse the watcher log for an `approx=` line
    #   (e.g., very early in a session before tokens were logged). Falling
    #   back to cfg["threshold"] as a sane default lets resume injection
    #   still proceed instead of silently losing the work.
    if pre_compact_total > 10_000_000:
        log(f"# RESUME_PENDING malformed (pre_compact_total={pre_compact_total} > 10M); deleting")
        try: RESUME_PENDING.unlink(missing_ok=True)
        except OSError: pass
        return False
    if pre_compact_total <= 0:
        pre_compact_total = cfg.get("threshold", 400_000)
        log(f"# RESUME_PENDING had pre_compact_total<=0 (derivation failed upstream); "
            f"defaulting to threshold {pre_compact_total} for drop calculation")
    # 2026-06-11 (Fix 2): if core.sh flagged the baseline as defaulted, warn that
    # the drop gate is comparing against a GUESS, not a measurement. We still
    # honor it (no behavior change) — this just makes the log honest about it.
    if pre_compact_defaulted:
        log(f"# WARNING: pre_compact_total={pre_compact_total} is a DEFAULTED baseline "
            f"(core.sh could not measure a real pre-clear total) — the "
            f"{cfg['post_compact_drop_pct']}%-drop gate is operating on a guess, "
            f"not a measurement ({log_label})")
    # 2026-06-11 (Fix 3): off-by-one. An exactly-{drop_pct}% drop must register.
    # Use the exact-integer comparison total*100 <= pre*(100-drop_pct) which is
    # equivalent to `total <= pre*(100-drop_pct)//100` but avoids the
    # floor-division skew that made the boundary case (exactly drop_pct)
    # silently fail.
    if (total * 100 <= pre_compact_total * (100 - cfg["post_compact_drop_pct"])
            and RESUME_PROMPT.exists()):
        try:
            prompt_text = RESUME_PROMPT.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            return False
        if prompt_text:
            # Fix E (2026-06-11): sanitize before any injection. Smoothness-safe:
            # a normal multi-KB markdown resume prompt passes through unchanged.
            prompt_text = sanitize_inject_payload(prompt_text, log_label=log_label)
            record_compaction_complete(total)
            # 2026-05-28: variant-aware post-/clear resume injection.
            # - cmux variant: auto-inject the resume prompt via cmux RPC
            #   (continues the fully-automatic infinite-session loop).
            # - warp variant: SKIP auto-injection. Per the variant design,
            #   the user manually types /acos-eternity-protocol-resume in
            #   the new session, and THAT skill loads the pending-resume
            #   file. The daemon doing this would race with the user's
            #   typing and cause the misfires that broke session 75254de0.
            if is_cmux_session(SESSION_ID):
                # 2026-06-15: pre-gate via cmux health check.
                allow, reason = cmux_pre_dispatch_check(f"resume {log_label}")
                if not allow:
                    # Cmux is unhealthy — DO NOT attempt the inject. Leave the
                    # artifacts on disk (same as warp variant) so the
                    # UserPromptSubmit hook (eternity-resume-prepend.sh)
                    # resurrects the resume content on the user's next prompt.
                    success = False
                    log(f"# COMPACTION DETECTED at {log_label}: pre={pre_compact_total} now={total} "
                        f"(drop>={cfg['post_compact_drop_pct']}%) — cmux resume auto-inject SKIPPED ({reason}); "
                        f"resume artifacts persist on disk for UserPromptSubmit hook recovery.")
                else:
                    success, _rc = fire_inject_cmux(prompt_text, log_label=f"cmux resume-prompt {log_label}")
                    update_cmux_health_after_inject(success, _rc, f"resume {log_label}")
                    # 2026-06-15: if the injector rejected with rc=6 (multi-line
                    # rejected by design), this is the expected fall-through —
                    # the resume content is multi-line markdown and the new
                    # injector refuses to type it as N separate Enter-submitted
                    # messages. Leave artifacts on disk; same recovery path as
                    # the warp variant.
                    if not success and _rc == 6:
                        log(f"# COMPACTION DETECTED at {log_label}: pre={pre_compact_total} now={total} "
                            f"(drop>={cfg['post_compact_drop_pct']}%) — cmux resume payload is multi-line; "
                            f"injector refused (rc=6). Resume artifacts persist on disk for UserPromptSubmit "
                            f"hook recovery (same path the warp variant uses).")
                    else:
                        log(f"# COMPACTION DETECTED at {log_label}: pre={pre_compact_total} now={total} "
                            f"(drop>={cfg['post_compact_drop_pct']}%) — cmux resume injection {'OK' if success else 'FAILED'}")
            else:
                # Warp variant: do NOT auto-inject. Leave the pending-resume
                # artifacts on disk for the manual /acos-eternity-protocol-resume
                # skill to pick up when the user invokes it. Mark "success" so
                # the cleanup branch below doesn't fire — we want the artifacts
                # to PERSIST until the manual resume skill consumes them.
                success = False
                log(f"# COMPACTION DETECTED at {log_label}: pre={pre_compact_total} now={total} "
                    f"(drop>={cfg['post_compact_drop_pct']}%) — warp variant: SKIPPING auto-inject; "
                    f"waiting for user to type /acos-eternity-protocol-resume manually. "
                    f"Pending-resume artifacts left on disk for that skill to consume.")
            # Only delete state on confirmed success — failed injections must
            # leave RESUME_PENDING/RESUME_PROMPT on disk so the UserPromptSubmit
            # hook can recover on the user's next prompt.
            if success:
                try:
                    RESUME_PENDING.unlink(missing_ok=True)
                    FIRED_FLAG.unlink(missing_ok=True)
                    RESUME_PROMPT.unlink(missing_ok=True)
                except OSError: pass
            return success
    return False

# ── Skill-to-daemon /clear request handler ───────────────────────────
# 2026-05-20: split keystroke firing of /clear off the skill onto the daemon.
# The skill cannot reliably inject /clear from inside its own running turn —
# Warp's input field is busy receiving tool output, so CGEventPost'd keystrokes
# either drop or queue and land at the wrong moment (after the skill returns,
# during the user's next prompt). The daemon, firing from outside the agent
# loop on an idle JSONL transcript, hits a ready input field — same code path
# that already works for typing /acos-eternity-protocol itself. So: the skill
# writes CLEAR_REQUESTED and exits cleanly; this function picks it up on the
# next kqueue event (which fires when Claude writes its skill-exit message)
# and injects /clear via the same fire_inject() used elsewhere.
def check_clear_request(log_label="event"):
    """Returns True if /clear was fired."""
    if not CLEAR_REQUESTED.exists():
        return False
    if inpane_carrier_active():
        # In-pane Stop hook (eternity-cmux-inpane.sh) consumes .clear-requested-<sid>
        # and sends /clear from inside the pane. Leave the flag for it; the daemon
        # must NOT also fire /clear (double-/clear race).
        return False
    # Read the flag content (optional metadata — ts, requested_by, etc.)
    try:
        flag_content = CLEAR_REQUESTED.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        flag_content = "(unreadable)"
    log(f"# CLEAR_REQUESTED flag seen at {log_label} — content: {flag_content!r}")
    # 2026-06-04 warp manual-only policy (enforced 2026-06-11 here too):
    # NON-CMUX SESSIONS MUST NEVER BE KEYSTROKE-INJECTED. The /clear-via-daemon
    # channel is ONLY valid for cmux sessions (clean Unix-socket RPC, no race).
    # The warp variant is manual-only — the user types /clear themselves. The
    # old "defense-in-depth" CGEventPost fire for non-cmux sessions could
    # misfire into the wrong Warp window (the exact 2026-05-21 misfire class).
    # So for non-cmux: log, delete the flag, and do NOT fire anything.
    if not is_cmux_session(SESSION_ID):
        log(f"# CLEAR_REQUESTED present for non-cmux session {SESSION_ID} — warp is "
            f"manual-only, NOT injecting; flag removed ({log_label})")
        try:
            CLEAR_REQUESTED.unlink(missing_ok=True)
        except OSError:
            pass
        return False

    # cmux variant: fire /clear via cmux send.
    # 2026-06-15: pre-gate via cmux health check.
    allow, reason = cmux_pre_dispatch_check(f"clear-requested {log_label}")
    if not allow:
        log(f"# CLEAR_REQUESTED present for session {SESSION_ID} but cmux unhealthy ({reason}) "
            f"({log_label}); renaming flag to .failed sidecar so refire loop is suppressed.")
        try:
            failed_path = CLEAR_REQUESTED.with_name(CLEAR_REQUESTED.name + ".failed")
            CLEAR_REQUESTED.replace(failed_path)
        except OSError:
            try:
                CLEAR_REQUESTED.unlink(missing_ok=True)
            except OSError:
                pass
        return False
    success, rc = fire_inject_cmux("/clear", log_label=f"clear-requested cmux {log_label}")
    update_cmux_health_after_inject(success, rc, f"clear-requested {log_label}")

    if not success:
        # 2026-06-11: do NOT write CLEAR_FIRED on failure — a failed /clear that
        # still wrote the marker made the orphan-claim path treat a never-cleared
        # session as cleared. Also do NOT delete CLEAR_REQUESTED (a bare delete
        # would tick-loop refire on the next event); instead rename it to a
        # ".failed" sidecar to preserve evidence AND suppress the refire loop.
        try:
            failed_path = CLEAR_REQUESTED.with_name(CLEAR_REQUESTED.name + ".failed")
            CLEAR_REQUESTED.replace(failed_path)
            log(f"# CLEAR_REQUESTED injection FAILED rc={rc} ({log_label}): cmux RPC did not "
                f"succeed; flag renamed to {failed_path.name} (no CLEAR_FIRED written, "
                f"orphan-claim will NOT treat this session as cleared)")
        except OSError as e:
            # Could not rename — fall back to deleting so we don't refire forever.
            log(f"# CLEAR_REQUESTED injection FAILED rc={rc} ({log_label}) and rename "
                f"failed ({e}); deleting flag to prevent refire loop (no CLEAR_FIRED written)")
            try:
                CLEAR_REQUESTED.unlink(missing_ok=True)
            except OSError:
                pass
        return False

    # Success: delete the flag so we don't refire on subsequent events.
    try:
        CLEAR_REQUESTED.unlink(missing_ok=True)
    except OSError:
        pass
    # 2026-05-20 (PM): Drop a positive proof marker for the post-/clear
    # orphan-claim path — written ONLY on a confirmed-successful /clear (cmux
    # rc==0). The marker says "this watcher successfully fired /clear for this
    # SID", which the new sibling session's watcher reads as authoritative
    # evidence in claim_orphan_resume_if_any().
    try:
        CLEAR_FIRED.write_text(
            f"fired_at: {now_iso()}\n"
            f"session_id: {SESSION_ID}\n"
            f"inject_reported: OK\n"
            f"log_label: {log_label}\n"
        )
        try: os.chmod(CLEAR_FIRED, 0o600)
        except OSError: pass
    except OSError as e:
        log(f"# CLEAR_FIRED marker write failed: {e} (orphan-claim will fall back to mtime heuristic)")
    log(f"# CLEAR_REQUESTED handled at {log_label} — inject OK; CLEAR_FIRED marker written")
    return success

# ── Main event loop ──────────────────────────────────────────────────
def main():
    # 2026-06-11 (Fix 7): main() resets the module-level usage cache in the
    # rotation branch, so declare it global up-front (must precede any binding).
    global _latest_usage
    # 2026-07-05: repair PATH for cmux/python3 resolution. The launchd-spawned
    # watcher inherits a bare PATH (/usr/bin:/bin:/usr/sbin:/sbin) with no
    # /opt/homebrew/bin, so bare "cmux" (cmux_ping_ok + the injector's cmux
    # calls) failed to resolve and EVERY threshold dispatch died rc=2/rc=3.
    # Prepend the homebrew/local bindirs once so all child subprocess calls
    # (injector, cmux ping) resolve. This is the process-wide root fix; the
    # injector and the plist EnvironmentVariables are belt-and-suspenders.
    for _p in ("/usr/local/bin", "/opt/homebrew/bin"):
        if _p not in os.environ.get("PATH", "").split(os.pathsep):
            os.environ["PATH"] = _p + os.pathsep + os.environ.get("PATH", "")
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    _open_log()
    log(f"# token-watcher started {now_iso()}")
    log(f"# session_id: {SESSION_ID}")
    log(f"# watching: {JSONL}")

    initial = parse_latest_usage_incremental(JSONL)
    if initial is None:
        log("# WARNING: no usage in JSONL at startup")
        prev_total = 0
    else:
        prev_total = sum(initial[:3])
        log(f"# baseline at startup: total_input={prev_total:,}")

    # Startup post-compact check
    cfg = load_config()
    if check_post_compact(prev_total, cfg, log_label="STARTUP"):
        log("# fired resume at startup")
    else:
        # Post-/clear orphan adoption: if a sibling session in this same
        # project left a pending-resume behind (because /clear minted a new
        # SID and the watcher for the new SID — that's us — has no SID-keyed
        # state of its own), claim that orphan. See the long comment above
        # claim_orphan_resume_if_any() for the full rationale.
        if claim_orphan_resume_if_any():
            log("# claimed orphan resume at startup")

    # Setup kqueue
    flags = (select.KQ_NOTE_WRITE | select.KQ_NOTE_EXTEND |
             select.KQ_NOTE_DELETE | select.KQ_NOTE_RENAME)

    def open_jsonl():
        for attempt in range(20):
            try:
                return os.open(str(JSONL), os.O_RDONLY)
            except FileNotFoundError:
                time.sleep(0.25)
        sys.stderr.write(f"JSONL never came back: {JSONL}\n")
        sys.exit(0)

    fd = open_jsonl()
    kq = select.kqueue()
    kev = select.kevent(fd, filter=select.KQ_FILTER_VNODE,
                        flags=select.KQ_EV_ADD | select.KQ_EV_CLEAR,
                        fflags=flags)

    evt_n = 0
    last_evt_ts = time.time()
    recent_deltas = deque(maxlen=ROLLING_WINDOW)

    # 2026-06-11 (Fix 4): cold-start fire gate for the backfill case. A watcher
    # attached to an ALREADY-over-threshold session normally cannot fire until a
    # SECOND JSONL write: recent_deltas excludes the first real delta (the
    # prev_total==0 first-delta guard), and MIN_SAMPLES_FOR_FIRE requires >=1
    # sample. If such a session then goes idle, it would never fire at all.
    # Seed one zero sample so the fire gate (len(recent_deltas) >= 1) is already
    # satisfied on the first observed event when the startup baseline is itself
    # already at/over threshold. avg_delta stays 0 (a single 0 sample), which is
    # the correct neutral forecast for an idle-but-already-huge session.
    if prev_total >= cfg["threshold"]:
        recent_deltas.append(0)
        log(f"# COLD-START FIRE GATE: startup baseline total={prev_total:,} already "
            f">= threshold {cfg['threshold']:,} — seeded recent_deltas with one zero "
            f"sample so a fire can pass on the first observed event")

    def cleanup_fds():
        """Close kq and the JSONL fd cleanly on any exit."""
        nonlocal fd
        try: os.close(fd)
        except OSError: pass
        fd = -1
        try: kq.close()
        except (OSError, AttributeError): pass

    import atexit
    atexit.register(cleanup_fds)

    try:
        while True:
          # 2026-06-11 (Fix 4b): make the steady-state loop survive unexpected
          # exceptions. Previously any uncaught error here propagated to the
          # top-level handler which logged + re-raised, KILLING the watcher.
          # Now: log the error (with traceback tail), sleep a 5s backoff, and
          # continue the loop. Genuinely unrecoverable startup failures occur
          # before this loop and still hard-exit.
          try:
            # Wait for events with a 60s timeout so we can run periodic tasks
            events = kq.control([kev], 1, 60)
            heartbeat()
            fired_flag_age_out()  # B5: clear stale FIRED_FLAG
            # Poll the /clear-requested flag every loop tick, including idle
            # 60s-timeouts where no JSONL activity occurred. This ensures
            # skill-requested clears are picked up promptly even if Claude
            # has gone fully silent between the skill exit and any further
            # writes (which is the common case — skill exits → Claude idle).
            check_clear_request(log_label="loop-tick")
            # 2026-06-11 (Fix 6): liveness self-check, once per tick (cheap).
            # If our owning claude CLI has exited, clean up our own ephemeral
            # state and exit — the fleet has no external reaper. Runs in the
            # idle 60s-timeout path AND after event batches; either way at most
            # once per loop iteration.
            self_terminate_if_owner_dead()

            if not events:
                continue

            for ev in events:
              # 2026-06-11 (Fix 4a): wrap each event's processing so one bad
              # JSONL event / transient error cannot propagate out and kill the
              # watcher. The body keeps its original `continue` control flow.
              try:
                now = time.time()
                ms = int((now - last_evt_ts) * 1000)
                last_evt_ts = now
                evt_n += 1

                # File rotation handling with retry (C-3 fix)
                if ev.fflags & (select.KQ_NOTE_DELETE | select.KQ_NOTE_RENAME):
                    log(f"# file rotated at evt {evt_n} — reopening")
                    try: os.close(fd)
                    except OSError: pass
                    time.sleep(0.05)
                    fd = open_jsonl()
                    kev = select.kevent(fd, filter=select.KQ_FILTER_VNODE,
                                        flags=select.KQ_EV_ADD | select.KQ_EV_CLEAR,
                                        fflags=flags)
                    # Reset cold-start state on rotation (Domain Logic finding 1)
                    prev_total = 0
                    recent_deltas.clear()
                    _write_persistent_offset(0)
                    # 2026-06-11 (Fix 7): also reset the module-level usage cache,
                    # mirroring the truncation branch in
                    # parse_latest_usage_incremental(). Without this, a rotation
                    # to a smaller/empty file would keep returning the stale
                    # pre-rotation usage tuple until a new usage block is parsed.
                    _latest_usage = None
                    continue

                comp = parse_latest_usage_incremental(JSONL)
                if comp is None:
                    continue

                total = sum(comp[:3])
                output_tokens = comp[3]
                delta = total - prev_total
                is_first_real_delta = (prev_total == 0 and delta > 0)
                if delta > 0 and not is_first_real_delta:
                    recent_deltas.append(min(delta, DELTA_CAP))
                avg_delta = sum(recent_deltas) / len(recent_deltas) if recent_deltas else 0
                approximate = total + output_tokens + int(avg_delta)
                log_event(evt_n, total, delta, ms, comp, avg_delta, approximate)
                # 2026-06-11 (Fix 1): publish latest approximate to the shared
                # sidecar so core.sh can read a real measured total at fire time
                # instead of scraping `approx=` lines out of the watcher log.
                _write_last_total(approximate)
                prev_total = total

                cfg = load_config()

                # Forward-trigger: cross threshold → fire eternity-protocol
                # B6: use `total` consistently (not approximate) for pre-compact recording
                if (approximate >= cfg["threshold"]
                        and len(recent_deltas) >= MIN_SAMPLES_FOR_FIRE
                        and not loop_guard_check(approximate)):
                    # 2026-06-15: early-return on cmux-unhealthy BEFORE
                    # try_claim_fire_flag. Otherwise we'd claim the flag,
                    # dispatch returns NOOP (because the inner gate also
                    # blocks), and the unclaimed FIRED_FLAG sits idle for
                    # ~625s before age-out — the exact burn window we are
                    # trying to eliminate. The inner gate (inside
                    # dispatch_threshold_fire) still runs for warp sessions
                    # and as defense in depth.
                    # 2026-06-18 fix: gate via cmux_pre_dispatch_check (NOT a raw is_cmux_unhealthy
                    # check). The pre-dispatch check AUTO-RECOVERS — if the unhealthy marker is set
                    # but `cmux ping` now succeeds, it clears the marker and allows the inject. The
                    # old raw skip never re-probed, so one transient failure wedged the breaker forever.
                    cmux_skip_reason = None
                    if is_cmux_session(SESSION_ID):
                        _allow, cmux_skip_reason = cmux_pre_dispatch_check(f"evt {evt_n}")
                    if cmux_skip_reason is not None:
                        log(f"# THRESHOLD met at evt {evt_n}: approx={approximate} (total={total}) — "
                            f"{cmux_skip_reason}; skipping dispatch (no FIRED_FLAG burn).")
                        # fall through to check_post_compact / check_clear_request below
                        pass  # placeholder so the next 'if' is a sibling
                    elif try_claim_fire_flag(flag_content := (
                        f"{now_iso()} fired at evt {evt_n} "
                        f"approx={approximate} total={total} cmd={cfg['fire_command']}\n"
                    )):
                        # 2026-05-28: variant dispatch (see dispatch_threshold_fire).
                        # cfg['fire_command'] is now retained only for log diagnostics —
                        # the dispatcher hardcodes -cmux or -warp based on per-session
                        # markers and ignores the config value.
                        #
                        # 2026-06-11: dispatch returns a tri-state. Only record the
                        # cycle when a fire actually FIRED — warp manual-only / opt-out
                        # NOOPs were polluting cycle history and triggering 5-minute
                        # loop-guard windows for fires that never happened. Log the
                        # actual outcome rather than an unconditional "dispatched".
                        result = dispatch_threshold_fire(
                            cfg, log_label=f"threshold-cross evt {evt_n}")
                        if result == "FIRED":
                            cycle_n = record_fire_event(total)  # B6: use total for consistency
                            log(f"# THRESHOLD CROSSED cycle={cycle_n} at evt {evt_n}: "
                                f"approx={approximate} (total={total}) — FIRED")
                        elif result == "NOOP":
                            # 2026-07-13: distinguish the THREE reasons dispatch_threshold_fire
                            # returns NOOP. The old code lumped in-pane-standdown in with warp and
                            # logged "warp manual-only" for BOTH — a red herring that made the
                            # IC-session investigation much harder (a cmux session with the in-pane
                            # carrier active looked like a warp session refusing to fire). Mirror the
                            # dispatcher's own precedence: opted-out, then in-pane-carrier, then warp.
                            if is_session_opted_out(SESSION_ID):
                                log(f"# THRESHOLD CROSSED at evt {evt_n}: approx={approximate} "
                                    f"(total={total}) — NO DISPATCH (opted out)")
                            elif inpane_carrier_active():
                                log(f"# THRESHOLD CROSSED at evt {evt_n}: approx={approximate} "
                                    f"(total={total}) — NO DISPATCH (in-pane carrier owns /clear + fire; "
                                    f"daemon detection-only — NOT a warp session)")
                            else:
                                log(f"# THRESHOLD CROSSED at evt {evt_n}: approx={approximate} "
                                    f"(total={total}) — NO DISPATCH (warp manual-only)")
                        else:  # "FAILED"
                            # 2026-06-18 fix: RELEASE the claimed fire flag on a FAILED dispatch so
                            # the NEXT event retries. A transient cmux socket spike (terminal under
                            # load) would otherwise leave the flag held and wedge the protocol
                            # permanently until a human removed the marker by hand.
                            FIRED_FLAG.unlink(missing_ok=True)
                            log(f"# THRESHOLD CROSSED at evt {evt_n}: approx={approximate} "
                                f"(total={total}) — DISPATCH FAILED (flag released for retry; cycle NOT recorded)")
                    else:
                        # 2026-06-11: previously a completely silent skip. Log when the
                        # threshold is met but the fire flag is already held (an in-flight
                        # cycle is suppressing spam) so the log isn't mysteriously quiet.
                        log(f"# THRESHOLD met at evt {evt_n}: approx={approximate} "
                            f"(total={total}) — fire flag already held; suppressing duplicate dispatch")

                # Post-compact-trigger
                check_post_compact(total, cfg, log_label=f"evt {evt_n}")

                # Skill-requested /clear trigger (idle-state injection path)
                check_clear_request(log_label=f"evt {evt_n}")
              except Exception as e:
                # 2026-06-11 (Fix 4a): one bad event must not kill the watcher.
                tb = traceback.format_exc().strip().splitlines()
                tb_tail = " | ".join(tb[-3:]) if tb else ""
                log(f"# EVENT ERROR at evt {evt_n}: {type(e).__name__}: {e} :: {tb_tail}")
                continue
          except Exception as e:
            # 2026-06-11 (Fix 4b): steady-state loop resilience. Log + backoff +
            # continue instead of dying. KeyboardInterrupt is NOT caught here
            # (it's not an Exception subclass) so Ctrl-C / SIGINT still exits.
            tb = traceback.format_exc().strip().splitlines()
            tb_tail = " | ".join(tb[-3:]) if tb else ""
            log(f"# LOOP ERROR: {type(e).__name__}: {e} :: {tb_tail} — 5s backoff, continuing")
            time.sleep(5)
            continue
    finally:
        cleanup_fds()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        log(f"# CRASH: {type(e).__name__}: {e}")
        raise
