#!/bin/bash
# eternity-cmux-resume-inpane.sh — IN-PANE SessionStart(clear) hook that makes the
# post-/clear resume HANDS-FREE for cmux eternity auto-fire.
#
# WHY THIS EXISTS (2026-06-18):
# The in-pane Stop hook (eternity-cmux-inpane.sh) automates steps 1-2 of the
# eternity cycle: it triggers the handoff skill and injects `/clear`. But after
# the /clear there was NO automatic step that resumes the work — the resume
# content (pending-resume-<sid>.txt) only gets injected by the UserPromptSubmit
# hook (eternity-resume-prepend.sh), and that hook fires ONLY when a prompt is
# submitted. So the user had to manually type `/acos-eternity-protocol-resume`
# (or any prompt) just to make the prepend hook fire. That manual keystroke is
# the gap this hook closes.
#
# HOW: a SessionStart hook runs IN-PANE in the freshly-/clear'd session (child of
# claude, carries CMUX_SURFACE_ID), so — unlike the detached daemon, which gets
# "Broken pipe" from cmux's in-pane-only socket — its `cmux send` works. We submit
# ONE short trigger prompt into the surface. That submission fires the existing,
# battle-tested eternity-resume-prepend.sh, which supplies the full handoff as
# additionalContext and consumes it single-shot. We deliberately do NOT duplicate
# the prepend hook's project-scoping / pointer / consume logic — there is exactly
# one resume-content code path; this hook only provides the missing trigger.
#
# A SessionStart hook canNOT resume passively: additionalContext it emits is
# attached to the NEXT user turn, it never INITIATES a turn. Only an actual
# submitted prompt does — hence the `cmux send`.
#
# SAFETY GATES (all must hold, else silent no-op so normal startups are unaffected):
#   1. state/.cmux-inpane-inject exists           (in-pane mode enabled)
#   2. a cmux surface is resolvable               (CMUX_SURFACE_ID or surface file)
#   3. a recent (<30min) .clear-fired-<sid> exists for a session in THIS project
#      — written ONLY by the in-pane Stop hook when it sends /clear, so this
#      distinguishes an eternity auto-/clear from a manual /clear (a manual
#      /clear writes no .clear-fired and would therefore NOT auto-resume).
#   4. a project-scoped pending-resume exists      (something to resume)
#   5. .autoresume-fired-<newsid> guard absent     (fire exactly once per session)

set +e
MON="$HOME/Library/Application Support/acos-token-monitor"
STATE="$MON/state"

# Gate 1: in-pane mode must be enabled.
[ -f "$STATE/.cmux-inpane-inject" ] || exit 0

# Hook payload (JSON on stdin): session_id + cwd (+ source).
INPUT=$(cat 2>/dev/null)
HOOK_DATA=$(printf '%s' "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('session_id', ''))
    print(d.get('cwd', ''))
    print(d.get('source', ''))
except Exception:
    pass" 2>/dev/null)
SID=$(printf '%s\n' "$HOOK_DATA" | sed -n '1p')
CWD=$(printf '%s\n' "$HOOK_DATA" | sed -n '2p')
SOURCE=$(printf '%s\n' "$HOOK_DATA" | sed -n '3p')

[ -z "$SID" ] && exit 0
[[ "$SID" =~ ^[a-zA-Z0-9_-]{1,128}$ ]] || exit 0
[ -z "$CWD" ] && exit 0
# Defense-in-depth: only act on clear/compact (the settings.json matcher should
# already scope this, but an empty source from an older Claude Code build passes).
case "$SOURCE" in clear|compact|"") : ;; *) exit 0 ;; esac

# Opt-out + once-per-session guard.
[ -f "$STATE/stop-$SID" ] && exit 0
[ -f "$STATE/.autoresume-fired-$SID" ] && exit 0

# Gate 2: resolve the cmux surface (env first — the post-/clear surface file may
# not be written yet — then the file, mirroring eternity-cmux-inpane.sh).
SURF="${CMUX_SURFACE_ID:-$(cat "$STATE/cmux-surface-$SID" 2>/dev/null)}"
[ -z "$SURF" ] && exit 0

# Project scoping: compute this cwd's Claude Code project dir + its session set
# (same sanitization the prepend hook uses: slashes/spaces/dots -> dashes).
SANITIZED=$(printf '%s' "$CWD" | tr '/' '-' | tr ' ' '-' | tr '.' '-')
PROJECT_DIR="$HOME/.claude/projects/$SANITIZED"
[ -d "$PROJECT_DIR" ] || exit 0
PROJECT_SESSIONS=$(ls "$PROJECT_DIR"/*.jsonl 2>/dev/null | xargs -I{} basename {} .jsonl 2>/dev/null)
[ -z "$PROJECT_SESSIONS" ] && exit 0

# Gate 3: a recent eternity /clear happened in THIS project (.clear-fired-<sid>
# written by the in-pane Stop hook, mtime within 30 min, sid in this project).
# 2026-07-05: widened 5min -> 30min. Slow compaction / machine sleep / a late
# SessionStart could push the SessionStart past a 5-min window and silently drop
# the resume. The other gates (pending-resume present + once-per-session guard)
# bound staleness, so a wider window is safe.
CLEAR_OK=""
while IFS= read -r CF; do
    [ -z "$CF" ] && continue
    CFSID=$(basename "$CF" | sed 's/^\.clear-fired-//')
    if printf '%s\n' "$PROJECT_SESSIONS" | grep -Fxq "$CFSID"; then
        CLEAR_OK=1; break
    fi
done < <(find "$STATE" -maxdepth 1 -name '.clear-fired-*' -mmin -30 2>/dev/null)
[ -z "$CLEAR_OK" ] && exit 0

# Gate 4: a project-scoped pending-resume exists (the prepend hook will need it).
# Mirror the prepend hook's two carriers: a pending-resume-<sid>.txt OR a per-
# claude-PID pointer whose .resume.md sibling exists.
RESUME_AVAILABLE=""
while IFS= read -r PR; do
    [ -z "$PR" ] && continue
    PRSID=$(basename "$PR" .txt | sed 's/^pending-resume-//')
    if printf '%s\n' "$PROJECT_SESSIONS" | grep -Fxq "$PRSID"; then
        RESUME_AVAILABLE=1; break
    fi
done < <(ls -t "$STATE"/pending-resume-*.txt 2>/dev/null)

if [ -z "$RESUME_AVAILABLE" ]; then
    # Pointer carrier: resolve this pane's claude PID and check for a live sibling.
    CLAUDE_PID=""
    WALK_PID=$$
    for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
        PARENT=$(ps -o ppid= -p "$WALK_PID" 2>/dev/null | tr -d ' ')
        [ -z "$PARENT" ] && break
        [ "$PARENT" -le 1 ] 2>/dev/null && break
        COMM=$(ps -o comm= -p "$PARENT" 2>/dev/null)
        case "$COMM" in
            *claude-loop*) WALK_PID=$PARENT; continue ;;
            claude|claude.ex|*/claude|*/claude.ex) CLAUDE_PID="$PARENT"; break ;;
        esac
        WALK_PID=$PARENT
    done
    if [ -n "$CLAUDE_PID" ] && [ -s "$STATE/.eternity-pointer-pid-$CLAUDE_PID" ]; then
        BASENAME=$(grep '^handoff_basename:' "$STATE/.eternity-pointer-pid-$CLAUDE_PID" 2>/dev/null | head -1 | sed 's/^handoff_basename:[[:space:]]*//')
        [ -n "$BASENAME" ] && [ -s "$CWD/memory/handoffs/${BASENAME}.resume.md" ] && RESUME_AVAILABLE=1
    fi
fi
[ -z "$RESUME_AVAILABLE" ] && exit 0

# CLAIM the once-per-session guard BEFORE sending so a concurrent SessionStart
# can't double-submit even if the send below is slow. CRITICAL (2026-07-05 audit):
# the previous version armed this guard and then did a BLIND send — if the send
# failed (cmux app down / stale socket) the guard stayed armed forever and the
# resume was SILENTLY DROPPED with no retry (the cycle-2 stall). So we now RELEASE
# the claim on any failure, letting a later SessionStart or the UserPromptSubmit
# prepend hook resume instead.
touch "$STATE/.autoresume-fired-$SID" 2>/dev/null

CMUX="${CMUX_CLAUDE_HOOK_CMUX_BIN:-cmux}"
command -v "$CMUX" >/dev/null 2>&1 || CMUX="cmux"

# Health gate: only submit if cmux is actually reachable. A blind send to a dead
# or stale socket would never land yet still arm the guard. If cmux is unhealthy,
# release the claim and bail — the prepend hook / next SessionStart can retry.
if ! "$CMUX" ping >/dev/null 2>&1; then
    rm -f "$STATE/.autoresume-fired-$SID" 2>/dev/null
    exit 0
fi

# Give the freshly-/clear'd session a moment to reach its prompt loop before we
# submit. /clear + compaction can keep the new session briefly busy; 3s is a
# conservative margin (keystrokes also buffer in the PTY if claude isn't yet at
# its readline).
sleep 3
TRIGGER="Resume the eternity-protocol handoff and continue exactly where the previous session left off."
# Submit with SEPARATE Enter keypresses (2026-07-06 fix). cmux turns a trailing \n
# into Enter but delivers "text\n" as ONE burst, which Claude Code's TUI can treat as
# a bracketed PASTE — absorbing the newline as a soft-newline so the trigger text
# lands in the box but is NEVER entered (observed live on the FruitSync pane; the user
# had to press Enter manually). Sending the Enter as its own delayed send(s) makes it
# a distinct keypress after the paste settles; a second Enter backstops a still-busy
# frame. Guard success keys on the TEXT send; the Enters are best-effort (a stray
# Enter is a no-op, and the prepend hook / next SessionStart still backstop a miss).
if "$CMUX" send --surface "$SURF" -- "$TRIGGER" >/dev/null 2>&1; then
    sleep 0.5; "$CMUX" send --surface "$SURF" -- '\n' >/dev/null 2>&1
    sleep 0.5; "$CMUX" send --surface "$SURF" -- '\n' >/dev/null 2>&1
    # Verified text send — confirm the guard with a timestamp.
    date -u +%Y-%m-%dT%H:%M:%SZ > "$STATE/.autoresume-fired-$SID" 2>/dev/null
else
    # Text send FAILED — release the claim so a later SessionStart / prepend hook
    # retries instead of the resume being permanently lost.
    rm -f "$STATE/.autoresume-fired-$SID" 2>/dev/null
fi
exit 0
