---
name: acos-eternity-protocol-cmux
description: Eternity protocol — cmux variant. Fully automatic. At 400k tokens, generates the handoff + resume prompt, signals the daemon via state/.clear-requested-<sid> + state/cmux-surface-<sid>; daemon uses cmux Unix-socket RPC (cmux rpc <method> with surface/text JSON payload fields) to inject /clear into the cmux surface, then — after compaction — injects the RAW pending-resume content directly into the surface (it does NOT type /acos-eternity-protocol-resume; the resume skill is never invoked in this auto path). Loops forever — sessions never end. Designed for cmux surfaces where the Unix-socket IPC eliminates the AXTitle marker race that breaks Warp.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Skill
---

# ACOS Eternity Protocol — cmux Variant (fully automatic)

## Overview

The cmux variant realizes the original eternity-protocol vision: an infinite
Claude conversation that auto-clears at 400k tokens and auto-resumes the
prior work in the next session — with zero human keystrokes.

Why it works on cmux but not Warp: cmux exposes a **Unix-domain-socket RPC
interface** for keystroke injection. The injector talks to the cmux GUI app
over that socket and asks "send these characters to surface S." No AXTitle
marker race, no Warp-vs-Node binary mismatch, no synthetic CGEventPost.

For the manual-fallback variant (Warp, no IPC), use
`/acos-eternity-protocol-warp`. To disable auto-fire for this session, use
`/acos-eternity-protocol-stop`.

## Architecture

```
PRE-CLEAR (this skill)                  CLEAR + POST-CLEAR (daemon)
──────────────────────────              ─────────────────────────────────────
1. Resolve session_id +                 7. Daemon kqueue tick detects
   confirm we're inside a                   .clear-requested-<sid>
   cmux surface (CMUX_SURFACE_ID
   captured by SessionStart hook)       8. Daemon reads state/cmux-surface-<sid>
2. Skill: acos-handoff                      to learn the cmux surface ID
3. Skill: acos-resume-prompt
4. eternity-protocol-core.sh:           9. Daemon fires inject-via-cmux.py,
   verify artifacts +                       which calls cmux RPC:
   write .resume-pending-<sid>                cmux rpc <method>
5. Write .clear-requested-<sid>                '{"surface":"<id>","text":"/clear\n"}'
6. EXIT cleanly                            (surface + text are JSON PAYLOAD
                                            fields; there are NO --surface /
                                            --text CLI flags. <method> defaults
                                            to surface.send-input, override via
                                            CMUX_INJECT_METHOD.)
                                        10. Daemon detects token drop ≥ 35%
                                            (compaction confirmed)
                                        11. Daemon reads pending-resume-<sid>.txt
                                            and injects its RAW CONTENT directly
                                            into the surface via the same RPC:
                                              cmux rpc <method>
                                                '{"surface":"<id>",
                                                  "text":"<resume prompt>\n"}'
                                            NB: the daemon does NOT type the slash
                                            command /acos-eternity-protocol-resume.
                                            The resume SKILL is never invoked in
                                            the cmux auto path — the new session
                                            just receives the prompt as turn 1.
                                        12. New session continues prior work
                                            directly from the injected prompt
                                        13. Next 400k crossing → step 1 again
                                            (forever, until /clear marker is
                                             written or user stops protocol)
```

## Execution Policy

Autonomous — invoking IS authorization. End-to-end execution with no
confirmation prompts. After Step 5, exit immediately and **do not continue
any reasoning** — the daemon needs Claude's input field idle for the
upcoming RPC injection.

## Configuration

Threshold and other config live at
`~/Library/Application Support/acos-token-monitor/config.yaml`. Change via
`/acos-eternity-protocol-threshold N`. Default: 400k.

## Pre-requisites

1. **cmux app must be running.** The cmux Unix socket only exists when the
   cmux GUI app is open. If it's not running, the daemon's `inject-via-cmux.py`
   will log an error and skip the fire (no destructive fallback to keystroke
   synthesis — better to fail loud than corrupt context).
2. **Session must be inside a cmux surface.** `$CMUX_SURFACE_ID` must be set
   at session start. The SessionStart hook captures it into
   `state/cmux-surface-<sid>`. If absent, this skill refuses to run and
   redirects you to the warp variant.
3. **cmux socket password.** If your cmux instance is password-protected,
   set `CMUX_SOCKET_PASSWORD` in your shell init or save it in cmux Settings.
   `inject-via-cmux.py` reads it on each fire.

## Protocol

### Step 0: Pre-flight (more checks than warp variant — IPC matters)

```bash
SESSION_DIR="$HOME/.claude/projects/$(pwd | tr '/' '-' | tr ' ' '-' | tr '.' '-')"
JSONL=$(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null | head -1)
SESSION_ID=$(basename "$JSONL" .jsonl 2>/dev/null)
test -n "$SESSION_ID" || { echo "ERROR: could not determine session_id"; exit 1; }

STATE="$HOME/Library/Application Support/acos-token-monitor/state"

# Self-write PID file (idempotent — matches the legacy skill's pattern)
echo "{\"session_id\":\"$SESSION_ID\"}" | \
    "$HOME/Library/Application Support/acos-token-monitor/bin/register-session-pid.sh" 2>/dev/null || true

# Opt-out marker?
if [[ -f "$STATE/stop-${SESSION_ID}" ]]; then
    echo "Eternity protocol is disabled for this session (stop marker present)."
    echo "  Remove: rm \"$STATE/stop-${SESSION_ID}\""
    exit 0
fi

# Are we inside cmux at all? If the SessionStart hook didn't capture
# CMUX_SURFACE_ID, the daemon doesn't know which surface to inject into.
# Redirect to the warp variant rather than fire blindly.
CMUX_SURFACE_FILE="$STATE/cmux-surface-${SESSION_ID}"
if [[ ! -s "$CMUX_SURFACE_FILE" ]]; then
    echo "ERROR: no cmux surface recorded for this session."
    echo "       This session was not launched inside a cmux surface."
    echo "       Use /acos-eternity-protocol-warp instead."
    exit 1
fi

# Is the cmux app running? Quick socket-existence probe — full RPC ping
# happens daemon-side at fire time.
CMUX_SOCKET="$HOME/Library/Application Support/cmux/cmux.sock"
if [[ ! -S "$CMUX_SOCKET" ]]; then
    echo "ERROR: cmux socket not found at $CMUX_SOCKET"
    echo "       The cmux app is not running. Launch cmux first, then retry."
    echo "       (Or use /acos-eternity-protocol-warp for the manual-fallback flow.)"
    exit 1
fi

# Heartbeat freshness — daemon must be alive to consume our flags.
# 2026-06-11: threshold raised 90s → 150s (the daemon's kqueue loop can
# legitimately idle-sleep ~60s, so 90s was a tight margin prone to false
# aborts). Also guard the mtime read: stat output that is empty/non-numeric
# (BSD vs GNU stat, missing file race) would otherwise feed the numeric test
# garbage and behave unpredictably — so we compute with a portable fallback
# and skip the staleness check (rather than abort) if we can't read a number.
HEARTBEAT="$HOME/Library/Application Support/acos-token-monitor/state/heartbeat"
if [[ -f "$HEARTBEAT" ]]; then
    HB_MTIME=$(stat -f%m "$HEARTBEAT" 2>/dev/null || stat -c%Y "$HEARTBEAT" 2>/dev/null)
    if [[ -z "$HB_MTIME" || ! "$HB_MTIME" =~ ^[0-9]+$ ]]; then
        echo "WARN: could not read heartbeat mtime — skipping staleness check"
    else
        HB_AGE=$(( $(date +%s) - HB_MTIME ))
        if [[ $HB_AGE -gt 150 ]]; then
            echo "ERROR: daemon heartbeat is ${HB_AGE}s old (>150s) — refusing to fire /clear."
            echo "       Daemon stalled or dead; the post-/clear resume injection would never fire."
            echo "       Restart: launchctl kickstart -k gui/\$UID/com.acos.token-monitor"
            exit 1
        fi
    fi
fi

# Injectors must exist
test -f "$HOME/Library/Application Support/acos-token-monitor/bin/inject-via-cmux.py" \
    || { echo "ERROR: cmux injector missing"; exit 1; }
# Auto-create memory/handoffs if missing — makes this skill work in any
# project, not just ones with ACOS infrastructure already in place.
mkdir -p memory/handoffs 2>/dev/null || { echo "ERROR: could not create memory/handoffs in $(pwd)"; exit 1; }
```

### Step 1: Create the handoff

Invoke the `acos-handoff` skill via the `Skill` tool. After it returns,
mechanically verify a fresh handoff was written:

```bash
# 2026-06-11 fix: accept BOTH .md and .yaml handoffs (mirrors the Jun-10
# core.sh / warp-skill fix — acos-handoff now emits .md; older runs emit .yaml).
HANDOFF=$(ls -t memory/handoffs/*.md memory/handoffs/*.yaml 2>/dev/null | head -1)
test -s "$HANDOFF" || { echo "ERROR: no handoff produced"; exit 1; }
```

### Step 2: Generate the resume prompt

Invoke the `acos-resume-prompt` skill via the `Skill` tool. It writes the
prompt to `state/pending-resume-<session_id>.txt`.

### Step 3: Arm the daemon via the shared core script

```bash
export ETERNITY_PROTOCOL_VARIANT="cmux"
# Source the core script from the user-global location so this works in
# ANY project (not just ACOS 3.0). The script is a symlink to the ACOS 3.0
# source — single source of truth, but reachable from anywhere.
CORE_SCRIPT="$HOME/Library/Application Support/acos-token-monitor/bin/eternity-protocol-core.sh"
if [[ ! -f "$CORE_SCRIPT" ]]; then
    CORE_SCRIPT="$(pwd)/.claude/scripts/eternity-protocol-core.sh"
fi
source "$CORE_SCRIPT" \
    || { echo "ERROR: eternity-protocol-core.sh failed (path: $CORE_SCRIPT)"; exit 1; }
# After source, core.sh has exported: $SESSION_ID, $HANDOFF, $RESUME_FILE,
# $PRE_CLEAR_TOTAL, $RESUME_PENDING, $RESUME_SIBLING, $HANDOFF_BASENAME, and
# (only when the per-claude-PID pointer file was written) $ETERNITY_POINTER.
# Step 4 references $RESUME_SIBLING and $ETERNITY_POINTER in its status block.

# Persist the exports Steps 4 & 5 need to a per-session sidecar: each fenced
# bash block runs in its OWN shell, so those later blocks cannot see these
# values otherwise (and re-sourcing core.sh would needlessly re-verify the
# handoff). The later blocks `source` this sidecar to recover state.
STATE="$HOME/Library/Application Support/acos-token-monitor/state"
CMUX_SIDECAR="$STATE/.cmux-skill-context-${SESSION_ID}"
{
    printf 'SESSION_ID=%q\n'      "$SESSION_ID"
    printf 'PRE_CLEAR_TOTAL=%q\n' "${PRE_CLEAR_TOTAL:-0}"
    printf 'HANDOFF=%q\n'         "${HANDOFF:-}"
    printf 'RESUME_FILE=%q\n'     "${RESUME_FILE:-}"
    printf 'RESUME_SIBLING=%q\n'  "${RESUME_SIBLING:-}"
    printf 'ETERNITY_POINTER=%q\n' "${ETERNITY_POINTER:-}"
} > "$CMUX_SIDECAR"
```

### Step 4: Print a brief status line (NOT a wall of text)

The cmux variant is meant to be silent-then-disappear — the user doesn't
need to see the resume prompt because the daemon is going to inject it
automatically post-/clear. A one-block status is enough.

```bash
# Re-derive base vars (own shell) + recover Step 3 exports from the sidecar.
SESSION_DIR="$HOME/.claude/projects/$(pwd | tr '/' '-' | tr ' ' '-' | tr '.' '-')"
JSONL=$(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null | head -1)
SESSION_ID=$(basename "$JSONL" .jsonl 2>/dev/null)
STATE="$HOME/Library/Application Support/acos-token-monitor/state"
CMUX_SURFACE_FILE="$STATE/cmux-surface-${SESSION_ID}"
CMUX_SIDECAR="$STATE/.cmux-skill-context-${SESSION_ID}"
# shellcheck disable=SC1090
[[ -s "$CMUX_SIDECAR" ]] && source "$CMUX_SIDECAR"   # HANDOFF, RESUME_FILE, RESUME_SIBLING, ETERNITY_POINTER

SHORT_ID="${SESSION_ID:0:8}"
CMUX_SURFACE=$(cat "$CMUX_SURFACE_FILE" 2>/dev/null | head -1)
cat <<EOF

┌───────────────────────────────────────────────────────────────────────┐
│  ETERNITY PROTOCOL — cmux VARIANT (fully automatic)                   │
├───────────────────────────────────────────────────────────────────────┤
│  Session:           ${SHORT_ID}…                                           │
│  cmux surface:      ${CMUX_SURFACE}
│  Handoff:           ${HANDOFF}                                             │
│  Resume prompt:     ${RESUME_FILE}                                         │
│  Resume sibling:    ${RESUME_SIBLING:-(none)}                              │
│  Per-PID pointer:   ${ETERNITY_POINTER:-(none)}                            │
│                                                                       │
│  Next: daemon will inject /clear via cmux RPC within ~60s.            │
│        Post-/clear, daemon injects the RAW resume prompt content      │
│        directly into the surface. You don't need to do anything.      │
└───────────────────────────────────────────────────────────────────────┘
EOF
```

### Step 5: Pre-flight the RPC method, then request /clear via daemon-side flag

The skill cannot fire RPC injection from inside its own running turn (the
input field is busy). Routing through the daemon is the same architectural
fix as the legacy `/acos-eternity-protocol`. Difference: the daemon dispatches
to `inject-via-cmux.py` (Unix socket RPC), not `inject-keystroke.py`
(CGEventPost), because we know this is a cmux surface.

**Pre-flight probe (2026-06-11).** The cmux RPC method name
(`surface.send-input`, overridable via `CMUX_INJECT_METHOD`) is an unverified
guess. If it is wrong, the daemon would clear the session and then silently
fail to resume — the worst failure mode. Before arming `.clear-requested`, we
probe `cmux capabilities` to confirm the method exists. If the probe returns
output that does NOT list the method, we ABORT (do not write the flag; the
handoff + resume artifacts stay on disk for the manual path). If the probe
command is missing or errors, we WARN and proceed (don't hard-block on a
probe we can't run). A successful probe is cached in
`state/.cmux-method-verified` so we skip it next time the method is unchanged.

```bash
# Re-derive base vars (own shell) + recover Step 3 exports from the sidecar.
SESSION_DIR="$HOME/.claude/projects/$(pwd | tr '/' '-' | tr ' ' '-' | tr '.' '-')"
JSONL=$(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null | head -1)
SESSION_ID=$(basename "$JSONL" .jsonl 2>/dev/null)
test -n "$SESSION_ID" || { echo "ERROR: could not determine session_id"; exit 1; }
STATE="$HOME/Library/Application Support/acos-token-monitor/state"
CMUX_SIDECAR="$STATE/.cmux-skill-context-${SESSION_ID}"
PRE_CLEAR_TOTAL=0
# shellcheck disable=SC1090
[[ -s "$CMUX_SIDECAR" ]] && source "$CMUX_SIDECAR"   # restores PRE_CLEAR_TOTAL etc.

# --- RPC method pre-flight ---
METHOD="${CMUX_INJECT_METHOD:-surface.send-input}"
VERIFIED_CACHE="$STATE/.cmux-method-verified"

if [[ -f "$VERIFIED_CACHE" ]] && grep -Fxq "$METHOD" "$VERIFIED_CACHE" 2>/dev/null; then
    echo "RPC method '$METHOD' already verified (cached) — skipping probe."
else
    if command -v cmux >/dev/null 2>&1; then
        # Capture capabilities (best-effort; cmux has no native short-timeout
        # flag, so we background + poll to avoid hanging the skill).
        CAP_OUT=""
        CAP_TMP=$(mktemp)
        ( cmux capabilities >"$CAP_TMP" 2>&1 ) &
        CAP_PID=$!
        for _ in 1 2 3 4 5 6 7 8 9 10; do
            kill -0 "$CAP_PID" 2>/dev/null || break
            sleep 0.5
        done
        if kill -0 "$CAP_PID" 2>/dev/null; then
            kill "$CAP_PID" 2>/dev/null || true
            echo "WARN: 'cmux capabilities' did not return within ~5s — could not verify"
            echo "      RPC method '$METHOD'. Proceeding without verification."
        else
            CAP_OUT=$(cat "$CAP_TMP" 2>/dev/null)
            if [[ -n "$CAP_OUT" ]] && ! printf '%s' "$CAP_OUT" | grep -Fq "$METHOD"; then
                rm -f "$CAP_TMP"
                cat <<EOF
┌───────────────────────────────────────────────────────────────────────┐
│  ABORT: cmux RPC method '$METHOD' is NOT in 'cmux capabilities'        │
├───────────────────────────────────────────────────────────────────────┤
│  The daemon would clear this session and then fail to resume it.      │
│  No /clear has been requested — your handoff + resume prompt are safe  │
│  on disk for the manual path.                                          │
│                                                                       │
│  Fix: inspect the method list above and either                        │
│    • export CMUX_INJECT_METHOD=<correct-method>  and re-run, OR        │
│    • update the default in inject-via-cmux.py.                         │
└───────────────────────────────────────────────────────────────────────┘
EOF
                exit 1
            fi
            # Probe succeeded (method found, or capabilities gave no usable
            # output to contradict it) → cache the verified method.
            if [[ -n "$CAP_OUT" ]] && printf '%s' "$CAP_OUT" | grep -Fq "$METHOD"; then
                printf '%s\n' "$METHOD" > "$VERIFIED_CACHE"
                echo "RPC method '$METHOD' verified via 'cmux capabilities' — cached."
            else
                echo "WARN: 'cmux capabilities' produced no usable output — could not"
                echo "      verify RPC method '$METHOD'. Proceeding without verification."
            fi
        fi
        rm -f "$CAP_TMP"
    else
        echo "WARN: 'cmux' CLI not found on PATH — could not verify RPC method"
        echo "      '$METHOD'. Proceeding without verification."
    fi
fi

# --- Arm the daemon ---
CLEAR_FLAG="$STATE/.clear-requested-${SESSION_ID}"
TMP=$(mktemp "${CLEAR_FLAG}.XXXXXX")
cat > "$TMP" <<EOF
requested_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
session_id: ${SESSION_ID}
requested_by: acos-eternity-protocol-cmux
pre_clear_total: ${PRE_CLEAR_TOTAL}
variant: cmux
EOF
mv "$TMP" "$CLEAR_FLAG"
chmod 600 "$CLEAR_FLAG" 2>/dev/null || true
test -s "$CLEAR_FLAG" || { echo "ERROR: failed to write clear-request flag"; exit 1; }
echo "Clear-request armed: $CLEAR_FLAG"
echo "Daemon will fire /clear via cmux RPC on next kqueue tick (≤60s)."
```

### Step 6: Exit cleanly

The post-skill JSONL turn-end marker wakes the daemon's kqueue. The daemon
sees `.clear-requested-<sid>`, reads `cmux-surface-<sid>`, and calls
`inject-via-cmux.py`, which issues `cmux rpc <method> '{"surface":"<id>",
"text":"/clear\n"}'` (surface/text are JSON payload fields, not CLI flags).
After compaction confirms, the daemon injects the RAW pending-resume content
the same way — it does NOT type `/acos-eternity-protocol-resume`; the resume
skill is never invoked in this auto path. No reasoning, no tool calls after
this point — keep the input idle.

---

*ACOS Eternity Protocol — cmux Variant. Fully automatic infinite-session loop.*
