---
name: acos-eternity-protocol
description: Eternity protocol — cmux variant. Fully automatic. At the configured token threshold (500k as of 2026-08-09; read config.yaml, don't trust a hardcoded number), generates the handoff + resume prompt, signals the in-pane Stop hook (eternity-cmux-inpane.sh) via state/.clear-requested-<sid> + state/cmux-surface-<sid>; that hook types /compact (switched from /clear on 2026-08-09 — same session id survives, closing the whole "wrong session's handoff got loaded" bug class) into the cmux surface via `cmux send`, then — once compaction completes — the paired SessionStart(clear|compact) hook (eternity-cmux-resume-inpane.sh) submits a short trigger prompt into that SAME surface, which fires eternity-resume-prepend.sh to supply the full handoff as additionalContext. Loops forever — sessions never end. Designed for cmux surfaces where the Unix-socket IPC eliminates the AXTitle marker race that breaks Warp. NOTE (2026-08-09): the Architecture diagram below still describes an older detached-daemon RPC-injection design (inject-via-cmux.py via kqueue) that the in-pane Stop hook appears to have superseded in practice — Step 5's own code already arms a surface-keyed flag specifically for the in-pane hook to consume. That diagram was not rewritten as part of this change; treat eternity-cmux-inpane.sh and eternity-cmux-resume-inpane.sh as the current source of truth for what actually runs.
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
`/acos-continue`. To disable auto-fire for this session, use
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
`/acos-eternity-protocol-threshold N`. Current value: 500k (2026-08-09 —
do not hardcode a number here; read the live file, since this line will
drift out of date exactly like the "400k" it replaced did).

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
_ETS="$HOME/Library/Application Support/acos-token-monitor/state"
# 2026-08-09: derivation now lives in ONE shared script,
# .claude/scripts/resolve-session-id.sh, instead of being copy-pasted into
# every step of every skill file. That duplication (this exact ~30-line
# block used to be pasted into Step 0, Step 4, AND Step 5 of this file alone)
# was the actual root cause of a recurring mis-scoped-session bug: fixing one
# copy never fixed the others. See that script's header comment for the full
# history, including why it now prefers the authoritative
# $CLAUDE_CODE_SESSION_ID over this file's own pane-matching guesswork.
SESSION_ID=$(bash .claude/scripts/resolve-session-id.sh)
test -n "$SESSION_ID" || { echo "ERROR: could not determine session_id"; exit 1; }
JSONL="$SESSION_DIR/$SESSION_ID.jsonl"

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

# ── Post-clear misfire guard (2026-07-19) ────────────────────────────────
# Bug (observed live 2026-07-20): a BARE /clear (typed by hand, no handoff
# saved first) was followed by a manual /acos-eternity-protocol in the fresh,
# near-empty session. Eternity SAVES-then-clears; firing it on a just-cleared
# chat checkpoints a blank session and re-clears nothing useful — the RESUME
# belongs in that slot, not another fire. Detect a near-empty session and
# REFUSE with recovery guidance (never auto-inject — the user acts themselves,
# per the "refuse + guide" decision).
#
# "Near-empty" = live context tokens well below threshold (.last-total-<sid>),
# or, when the watcher hasn't written that yet, a tiny transcript. A session
# that worked back up to ~400k (the legitimate re-fire case) is NOT near-empty,
# so the normal eternity loop is never blocked. Fail-open: if nothing is
# measurable, do not block. Explicit override: CMUX_ETERNITY_FORCE=1.
if [[ "${CMUX_ETERNITY_FORCE:-}" != "1" ]]; then
    _MISFIRE_TOK_FLOOR=20000        # tokens; any real work far exceeds this
    _MISFIRE_LINE_FLOOR=100         # fallback when .last-total-<sid> absent
    _tok=$(cat "$STATE/.last-total-${SESSION_ID}" 2>/dev/null)
    _near_empty=0; _measure=""
    if [[ "$_tok" =~ ^[0-9]+$ ]]; then
        _measure="${_tok} context tokens"
        (( _tok < _MISFIRE_TOK_FLOOR )) && _near_empty=1
    else
        _lines=$(wc -l < "$JSONL" 2>/dev/null | tr -d ' ')
        if [[ "$_lines" =~ ^[0-9]+$ ]]; then
            _measure="${_lines} transcript lines"
            (( _lines < _MISFIRE_LINE_FLOOR )) && _near_empty=1
        fi
    fi
    if (( _near_empty == 1 )); then
        # Point recovery at the most-recent OTHER transcript on THIS surface.
        _prev=""
        if [[ -n "${CMUX_SURFACE_ID:-}" ]]; then
            while IFS= read -r _j; do
                [[ -n "$_j" ]] || continue
                _s=$(basename "$_j" .jsonl)
                [[ "$_s" == "$SESSION_ID" ]] && continue
                [[ "$(head -1 "$_ETS/cmux-surface-$_s" 2>/dev/null)" == "$CMUX_SURFACE_ID" ]] || continue
                _prev="$_s"; break
            done < <(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null)
        fi
        # Newest saved resume note in this project, if any (recovery target).
        _note=$(ls -t memory/handoffs/*.resume.md 2>/dev/null | head -1)
        echo "REFUSING TO FIRE — this session is near-empty (${_measure:-unmeasurable}),"
        echo "  far below the configured threshold. Eternity SAVES-then-resets, so firing"
        echo "  now would checkpoint a blank chat. A /clear or /compact likely just ran,"
        echo "  and the RESUME — not another fire — belongs in this slot."
        echo
        echo "  Recover instead (nothing here is lost):"
        echo "    - Pending resume, if any:   /acos-eternity-protocol-resume"
        echo "      (After a BARE /clear or /compact nothing was saved, so this may also find nothing.)"
        if [[ -n "$_prev" ]]; then
            echo "    - Previous chat in this pane (its full work is on disk):"
            echo "        session $_prev  ->  $SESSION_DIR/$_prev.jsonl"
        fi
        if [[ -n "$_note" ]]; then
            echo "    - Newest saved handoff note (open and read it):"
            echo "        $_note"
        fi
        echo
        echo "  To fire eternity on THIS session anyway: re-run with CMUX_ETERNITY_FORCE=1"
        exit 1
    fi
fi

# Are we inside cmux at all? If the SessionStart hook didn't capture
# CMUX_SURFACE_ID, the daemon doesn't know which surface to inject into.
# Redirect to the warp variant rather than fire blindly.
CMUX_SURFACE_FILE="$STATE/cmux-surface-${SESSION_ID}"
if [[ ! -s "$CMUX_SURFACE_FILE" ]]; then
    echo "ERROR: no cmux surface recorded for this session."
    echo "       This session was not launched inside a cmux surface."
    echo "       Use /acos-continue instead."
    exit 1
fi

# Is the cmux app running? Quick socket-existence probe — full RPC ping
# happens daemon-side at fire time.
# 2026-07-17: cmux 0.64.x moved its IPC socket from ~/Library/Application Support/cmux/
# to the XDG state dir ~/.local/state/cmux/. Probe the `last-socket-path` pointer files
# first (trusted only when the path they name is a live socket — the App Support pointer
# goes stale after the move), then both fixed locations, newest scheme first.
CMUX_SOCKET=""
for _cand in \
    "$(cat "$HOME/.local/state/cmux/last-socket-path" 2>/dev/null)" \
    "$(cat "$HOME/Library/Application Support/cmux/last-socket-path" 2>/dev/null)" \
    "$HOME/.local/state/cmux/cmux.sock" \
    "$HOME/Library/Application Support/cmux/cmux.sock"; do
    [[ -n "$_cand" && -S "$_cand" ]] && { CMUX_SOCKET="$_cand"; break; }
done
if [[ -z "$CMUX_SOCKET" ]]; then
    echo "ERROR: cmux socket not found (checked ~/.local/state/cmux/ and"
    echo "       ~/Library/Application Support/cmux/, plus their last-socket-path pointers)"
    echo "       The cmux app is not running. Launch cmux first, then retry."
    echo "       (Or use /acos-continue for the manual-fallback flow.)"
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
            echo "ERROR: daemon heartbeat is ${HB_AGE}s old (>150s) — refusing to fire the reset."
            echo "       Daemon stalled or dead; the post-reset resume injection would never fire."
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

# 2026-06-24 FREEZE-EARLY: arm subordination as the FIRST mutation of this fire — BEFORE
# acos-handoff (Step 1). From now until the Step-5 disarm, both the Oracle and the autopilot
# Stop hook subordinate (via _autopilot_eternity.is_eternity_protocol_active), so NO new
# continuation work can land between the handoff snapshot (Step 1) and /clear — closing the
# stale-handoff gap. Best-effort: a failed write must NEVER abort the fire. The marker
# self-expires (age-GC, 10 min, in _autopilot_eternity.py) so a crashed fire can never freeze
# the autopilot, and it is explicitly removed in Step 5 so it can't outlive the fire.
ARMING_MARKER="$STATE/.eternity-arming-${SESSION_ID}"
if printf 'armed_at: "%s"\nsession_id: %s\nby: acos-eternity-protocol\n' \
        "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$SESSION_ID" > "$ARMING_MARKER" 2>/dev/null; then
    echo "Freeze-early armed (autopilot + Oracle subordinate; self-expires 10m): $ARMING_MARKER"
else
    echo "WARN: could not write freeze-early arming marker — proceeding (fire NOT blocked)."
fi
```

### Step 1: Create the handoff

Invoke the `acos-handoff` skill via the `Skill` tool. After it returns,
mechanically verify a fresh handoff was written:

```bash
# 2026-08-09: selection now goes through the shared
# resolve-session-handoff.sh, matched against THIS session's own id —
# not just "whichever handoff is newest" (the old rule, which grabbed a
# DIFFERENT concurrent session's handoff on 2026-08-08/09; see
# .claude/scripts/resolve-session-handoff.sh for the full history).
SESSION_ID=$(bash .claude/scripts/resolve-session-id.sh)
test -n "$SESSION_ID" || { echo "ERROR: could not determine session_id"; exit 1; }
HANDOFF=$(bash .claude/scripts/resolve-session-handoff.sh "$SESSION_ID")
test -s "$HANDOFF" || { echo "ERROR: no handoff produced matching session_id '$SESSION_ID'"; exit 1; }
# 2026-06-21 FRESHNESS GUARD. `test -s` only proves a handoff EXISTS, not that
# THIS fire wrote it. When the handoff-agent fails silently (observed live), the
# line above binds $HANDOFF to a STALE prior handoff → the protocol would /clear
# and resume the WRONG (old) work. Require the handoff to be <10 min old.
# stat-based age, NOT `find -mmin` (find exits 0 even on no match → always-true).
HO_MTIME=$(stat -f %m "$HANDOFF" 2>/dev/null || stat -c %Y "$HANDOFF" 2>/dev/null)
if [[ -z "$HO_MTIME" ]] || [[ $(( ($(date +%s) - HO_MTIME) / 60 )) -gt 10 ]]; then
    echo "ERROR: newest handoff ($HANDOFF) is STALE (not from this fire) — the"
    echo "       handoff-agent likely failed to write. ABORTING before /clear so this"
    echo "       session is NOT cleared and resumed with the wrong handoff."
    exit 1
fi
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
# 2026-08-09: single shared resolver — see .claude/scripts/resolve-session-id.sh
# (this step used to carry its own copy of the ~30-line derivation logic;
# that duplication is exactly what let this bug keep resurfacing).
SESSION_ID=$(bash .claude/scripts/resolve-session-id.sh)
test -n "$SESSION_ID" || { echo "ERROR: could not determine session_id"; exit 1; }
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
│  Next: the in-pane Stop hook will type /compact within ~60s.          │
│        Once compaction finishes, the paired SessionStart hook types   │
│        a short resume trigger into the same pane. You don't need to   │
│        do anything.                                                   │
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

> **Daemon counterpart (2026-06-11, post-swarm-re-review).** The out-of-repo
> injector `inject-via-cmux.py` resolves the method `env CMUX_INJECT_METHOD >
> cached .cmux-method-verified > default`, and on an "unknown method" RPC error
> it self-heals: it runs `cmux capabilities`, retries the best candidate, and
> caches the winner. Hardening from the re-review: `read_verified_method()` now
> shape-validates the cached value (`_looks_like_method`) before trusting it, so
> a corrupted/hand-edited cache cannot "stick" and silently fail every fire — a
> non-method-shaped value falls through to the default, which the self-heal can
> then correct. The cache file format is a single bare method-name line, written
> atomically by both this skill's probe and the injector.

```bash
# Re-derive base vars (own shell) + recover Step 3 exports from the sidecar.
# 2026-08-09: single shared resolver — see .claude/scripts/resolve-session-id.sh
# (this step used to carry its own copy of the ~30-line derivation logic;
# that duplication is exactly what let this bug keep resurfacing).
SESSION_ID=$(bash .claude/scripts/resolve-session-id.sh)
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
│  This probe is a legacy check against a method the in-pane hook does  │
│  not actually use (it calls `cmux send` directly) — kept as belt-and- │
│  suspenders, not because a failure here is currently expected. No     │
│  reset has been requested — your handoff + resume prompt are safe on  │
│  disk for the manual path.                                            │
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
                # SHARED CONTRACT with the daemon's injector: this file MUST
                # contain a SINGLE bare line = the method name, nothing else
                # (no trailing commentary, no `method=` prefix). The injector
                # reads it verbatim to skip re-probing on a seamless first fire.
                # Write atomically (tmp + mv) so the injector never sees a
                # half-written file on a concurrent read.
                VC_TMP=$(mktemp "${VERIFIED_CACHE}.XXXXXX")
                printf '%s\n' "$METHOD" > "$VC_TMP"
                mv "$VC_TMP" "$VERIFIED_CACHE"
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
requested_by: acos-eternity-protocol
pre_clear_total: ${PRE_CLEAR_TOTAL}
variant: cmux
EOF
mv "$TMP" "$CLEAR_FLAG"
chmod 600 "$CLEAR_FLAG" 2>/dev/null || true
test -s "$CLEAR_FLAG" || { echo "ERROR: failed to write clear-request flag"; exit 1; }
echo "Clear-request armed: $CLEAR_FLAG"

# ALSO arm a SURFACE-keyed flag (2026-06-19 fix for session-id churn). One cmux
# pane cycles through MANY session ids (multiple transcripts, /clear cycles,
# sometimes two written seconds apart with several panes open), so a sid-keyed
# flag can miss the id the in-pane Stop hook actually receives. The surface is
# STABLE per pane and both sides read CMUX_SURFACE_ID reliably; the hook
# (eternity-cmux-inpane.sh Priority 1) prefers this flag. Match-by-surface is
# sid-churn-proof. (Resume side is already project-scoped, so only the clear
# trigger needed this.)
MY_SURFACE="${CMUX_SURFACE_ID:-$CMUX_PANEL_ID}"
if [[ -n "$MY_SURFACE" ]]; then
    SURF_FLAG="$STATE/.clear-requested-surface-${MY_SURFACE}"
    cp -f "$CLEAR_FLAG" "$SURF_FLAG" 2>/dev/null && chmod 600 "$SURF_FLAG" 2>/dev/null || true
    echo "Surface-keyed clear-request armed: $SURF_FLAG"
fi
echo "In-pane Stop hook fires /compact on next turn-end (surface-keyed; sid-churn-proof)."

# 2026-06-24 FREEZE-EARLY DISARM: pending-resume-<sid> (Step 2) and .clear-requested-<sid>
# (just written) now carry subordination through /clear and are daemon-managed (consumed
# after the resume injects), so the in-repo arming marker is no longer needed. Remove it
# BEFORE exit so it can never linger and subordinate the freshly-resumed NEXT session (whose
# project still lists this session's transcript). Age-GC would clear it within 10 min
# regardless — this just makes the common path instant. Best-effort; never abort on failure.
rm -f "$STATE/.eternity-arming-${SESSION_ID}" 2>/dev/null || true
echo "Freeze-early disarmed (subordination now continues via daemon-managed markers)."
```

### Step 6: Exit cleanly

The post-skill turn-end (Stop event) wakes `eternity-cmux-inpane.sh`. It sees
`.clear-requested-<sid>` (or the surface-keyed copy), and sends `/compact`
directly into the cmux surface via `cmux send`. Once compaction finishes,
Claude Code fires a SessionStart event with `source: "compact"` in that same
pane; `eternity-cmux-resume-inpane.sh` catches it and submits a short trigger
prompt, which fires `eternity-resume-prepend.sh` to supply the full handoff as
additionalContext — it does NOT type `/acos-eternity-protocol-resume`; that
skill is a manual fallback only, never invoked in this auto path. No
reasoning, no tool calls after this point — keep the input idle.

---

*ACOS Eternity Protocol — cmux Variant. Fully automatic infinite-session loop.*
