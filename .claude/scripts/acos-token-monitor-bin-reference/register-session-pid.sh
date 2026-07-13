#!/bin/bash
# Register Claude Code PID for the current session.
# Triggered by SessionStart hook in .claude/settings.local.json.
#
# Hardening pass:
# - Walks up to 15 levels (was 8) for deeper terminal stacks
# - Matches `claude`, `claude.ex`, `node`/`npx` whose argv contains 'claude' (H10)
# - Atomic file write via tmp+mv
# - Validates session_id format
# - Records process start_time for identity verification (S3)
# - Picks OUTERMOST claude match in the ancestor chain (not the first/innermost) —
#   fixes a bug where a transient inner claude child (spawned for a tool call)
#   would be recorded and become invalid as soon as it exited, leaving the long-
#   lived top-level claude process unregistered (B11, 2026-05-20)

set -e

STATE_DIR="$HOME/Library/Application Support/acos-token-monitor/state"
mkdir -p "$STATE_DIR"

INPUT=$(cat 2>/dev/null || echo "{}")

# Extract session_id
SESSION_ID=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('session_id', ''))
except: pass
" 2>/dev/null)

if [[ -z "$SESSION_ID" ]]; then
    TP=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('transcript_path', ''))
except: pass
" 2>/dev/null)
    if [[ -n "$TP" ]]; then
        SESSION_ID=$(basename "$TP" .jsonl)
    fi
fi

[[ -z "$SESSION_ID" ]] && exit 0

# Validate session_id (S3 / B3 path traversal protection)
if [[ ! "$SESSION_ID" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    exit 0
fi

# Walk parent process tree to find Claude Code ancestor.
# Retry up to 5 times with 200ms gaps between attempts — on post-/clear
# SessionStart the hook can fire before the claude process tree is fully
# wired up, so a one-shot ancestor walk sometimes returns no match for a
# session that the SAME bash subshell would find a moment later.
for attempt in 1 2 3 4 5; do
    PID=$$
    LAST_MATCH_PID=""
    LAST_MATCH_START=""
    for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
        PARENT=$(ps -o ppid= -p "$PID" 2>/dev/null | tr -d ' ' || echo "")
        [[ -z "$PARENT" || "$PARENT" -le 1 ]] && break
        COMM=$(ps -o comm= -p "$PARENT" 2>/dev/null || echo "")
        ARGS=$(ps -o command= -p "$PARENT" 2>/dev/null || echo "")

        # Match exact command name OR argv containing 'claude' (H10)
        MATCH=0
        case "$COMM" in
            claude|claude.ex|*/claude|*/claude.ex) MATCH=1 ;;
        esac
        if [[ $MATCH -eq 0 ]]; then
            case "$ARGS" in
                *" claude"*|*"/claude"*|*"npx claude"*|*"bunx claude"*) MATCH=1 ;;
            esac
        fi

        if [[ $MATCH -eq 1 ]]; then
            # Record this match but KEEP WALKING — the walk goes from leaf
            # (this script) toward root (the terminal), so the LAST claude
            # encountered is the outermost / longest-lived one. Stopping at
            # the first match would record a transient inner claude child
            # that exits as soon as its tool call returns, leaving an
            # invalid PID file (B11, 2026-05-20).
            LAST_MATCH_PID="$PARENT"
            LAST_MATCH_START=$(ps -o lstart= -p "$PARENT" 2>/dev/null | sed 's/^[ \t]*//;s/[ \t]*$//' || echo "")
        fi
        PID=$PARENT
    done
    if [[ -n "$LAST_MATCH_PID" ]]; then
        # ─── cmux surface capture (2026-05-28) ───────────────────
        # If this hook is running inside a cmux surface (cmux GUI app sets
        # $CMUX_SURFACE_ID for any process spawned inside one of its panes),
        # record the surface ref so the daemon knows to dispatch to
        # inject-via-cmux.py (Unix socket RPC) instead of inject-keystroke.py
        # (CGEventPost) at threshold-fire time.
        #
        # Benign if not in cmux — file simply isn't written; daemon falls
        # back to the legacy CGEventPost path for the warp variant. This is
        # the clean, narrow successor to the failed tmux integration: ONE
        # env var, ONE marker file, no socket discovery.
        # 2026-07-13: GC old learned-dead-surface + failure-counter markers (14-day
        # window; just bounded cleanup — behavior is gated on FRESHNESS below, not GC).
        find "$STATE_DIR" -maxdepth 1 \( -name '.cmux-surface-dead-*' -o -name '.cmux-surface-failures-*' \) -mtime +14 -delete 2>/dev/null || true
        # Is $CMUX_SURFACE_ID a surface the in-pane hook has LEARNED is dead? A
        # long-lived claude process keeps its LAUNCH $CMUX_SURFACE_ID even after a cmux
        # restart kills that surface, so a merely-present env var is NOT proof the surface
        # is live. The in-pane hook writes .cmux-surface-dead-<surf> after >=2 failures.
        # Honor it ONLY while FRESH (<30min): a genuinely-dead surface keeps failing, so the
        # in-pane hook keeps refreshing the mark → it stays honored; a wrongly-marked or
        # since-revived surface stops failing → the mark goes stale → we re-capture and give
        # it another chance (the in-pane hook clears the mark on the next successful send).
        # This BOUNDS a false positive to ~the window + the next SessionStart (auto-capture
        # only runs here, so a heavy pane heals on its next auto-compact) instead of a
        # PERMANENT warp demotion — critical because the only un-mark path runs in-pane BELOW
        # the cmux-surface-file gate, so once the surface file is gone it could never run
        # again (2026-07-13 review: the earlier hard-suppress version deadlocked here).
        # Guard the id shape so a hostile value can never build a bad marker path.
        _SURF_DEAD=""; _DEAD_MARK="$STATE_DIR/.cmux-surface-dead-$CMUX_SURFACE_ID"
        if [[ -n "$CMUX_SURFACE_ID" ]] && [[ "$CMUX_SURFACE_ID" =~ ^[A-Za-z0-9._-]+$ ]] && [[ -e "$_DEAD_MARK" ]]; then
            _dm=$(stat -f %m "$_DEAD_MARK" 2>/dev/null || echo 0)
            _now=$(date +%s 2>/dev/null || echo 0)
            [[ $(( _now - _dm )) -lt 1800 ]] && _SURF_DEAD=1
        fi
        if [[ -n "$CMUX_SURFACE_ID" ]] && [[ -z "$_SURF_DEAD" ]]; then
            # In a live cmux surface (and NOT a learned-dead one) → (re)capture the
            # CURRENT surface ref. Because this runs on EVERY SessionStart
            # (startup/resume/clear/compact), it also REFRESHES a stale binding after a
            # cmux restart (which mints brand-new surface ids): the newest SessionStart
            # overwrites with the live surface.
            TMP_CMUX=$(mktemp "$STATE_DIR/cmux-surface-${SESSION_ID}.XXXXXX")
            printf "%s\n" "$CMUX_SURFACE_ID" > "$TMP_CMUX"
            mv "$TMP_CMUX" "$STATE_DIR/cmux-surface-$SESSION_ID"
            chmod 600 "$STATE_DIR/cmux-surface-$SESSION_ID" 2>/dev/null || true
        else
            # 2026-07-09 fix (+2026-07-13): NOT in a cmux surface right now, OR
            # $CMUX_SURFACE_ID names a LEARNED-DEAD surface (see above) → INVALIDATE any
            # stale cmux-surface-<sid> binding for THIS session. Without this, a session that
            # was once in cmux but is now resumed OUTSIDE it (or that survived a cmux
            # restart which killed its surface) keeps a DEAD surface ref on disk.
            # is_cmux_session() trusts the file's mere existence, so the session stays
            # misclassified as "cmux" forever and the eternity skill arms a /clear at a
            # dead surface — the in-pane `cmux send` fails silently and the session
            # never clears or resumes (root cause of the IC-session 6e82feac stall:
            # surface F47FF27D died on the 2026-07-08 cmux restart, file never refreshed).
            # CMUX_SURFACE_ID is inherited by every process cmux spawns in a pane, so an
            # unset value here is AUTHORITATIVE: this process is genuinely not in a cmux
            # pane → drop the binding so it correctly falls back to warp (manual-only),
            # which actually works, instead of a silent cmux dead-surface stall.
            rm -f "$STATE_DIR/cmux-surface-$SESSION_ID" 2>/dev/null || true
        fi

        # Eviction (2026-05-21 fix — cross-session keystroke misfire).
        # Each claude PID hosts at MOST one live session at a time. /clear
        # mints a new session_id inside the same OS process, immediately
        # superseding the previous one. Without eviction, the old
        # pid-<dead_sid> file stays on disk pointing at our PID — and the
        # dormant token-watcher daemon for that dead session will happily
        # look up the stale file later and route a keystroke into our
        # window. That's exactly how the 2026-05-21 misfire happened:
        # ten pid-<other_sid> files all claimed PID 45454; one of their
        # daemons crossed threshold and typed /acos-eternity-protocol into
        # the live session's window, destroying its context.
        #
        # Rule: when registering pid-X=P, remove any pid-Y=P where Y!=X.
        # Cheap, idempotent, safe — a session whose PID is currently held
        # by someone else is already dead anyway; the file is garbage.
        for OTHER in "$STATE_DIR"/pid-*; do
            [[ -f "$OTHER" ]] || continue
            OTHER_BASE=$(basename "$OTHER")
            [[ "$OTHER_BASE" == "pid-$SESSION_ID" ]] && continue
            OTHER_PID=$(head -1 "$OTHER" 2>/dev/null)
            if [[ "$OTHER_PID" == "$LAST_MATCH_PID" ]]; then
                rm -f "$OTHER"
            fi
        done

        TMP=$(mktemp "$STATE_DIR/pid-${SESSION_ID}.XXXXXX")
        printf "%s\n%s\n" "$LAST_MATCH_PID" "$LAST_MATCH_START" > "$TMP"
        mv "$TMP" "$STATE_DIR/pid-$SESSION_ID"
        chmod 600 "$STATE_DIR/pid-$SESSION_ID" 2>/dev/null || true

        # Stamp the controlling terminal's window title via OSC 2 with a
        # session-UUID marker. inject-keystroke.py uses this marker (via
        # macOS Accessibility API enumeration of Warp's AXWindows) to
        # identify which Warp window hosts this session and raise it
        # before posting /clear.
        #
        # Routing detail (learned 2026-05-20): we CANNOT write to /dev/tty
        # because this script runs as a Claude Code hook subprocess, which
        # has no controlling tty — /dev/tty returns "Device not configured."
        # Instead, derive the absolute device path from the claude PID's
        # ps -o tty= output (e.g., "ttys000" → "/dev/ttys000") and write
        # there directly. This bytes-into-the-pty-from-outside path is
        # what Warp reads from the master end and processes as terminal
        # output (including OSC escape sequences).
        TTY_DEV=$(ps -o tty= -p "$LAST_MATCH_PID" 2>/dev/null | tr -d ' ')
        if [[ -n "$TTY_DEV" ]] && [[ "$TTY_DEV" != "??" ]] && [[ -e "/dev/$TTY_DEV" ]]; then
            printf '\033]2;ACOS[%s] claude\007' "$SESSION_ID" > "/dev/$TTY_DEV" 2>/dev/null || true
        fi

        # ─── Self-spawn token-watcher (2026-06-09) ──────────────────────
        # Universal coverage fix: when this script is wired as a user-global
        # SessionStart hook (~/.claude/settings.json), every claude session
        # in every project automatically gets a watcher — no per-project
        # launchd plist required for new projects to be protected.
        #
        # Idempotent via pgrep guard: if a watcher is already running for
        # this SESSION_ID (e.g., spawned by a legacy per-project launcher),
        # we silently skip. Safe to run concurrently with the legacy
        # com.acos.token-monitor / com.acos.token-monitor.okoa launchers.
        TRANSCRIPT_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('transcript_path', ''))
except: pass
" 2>/dev/null)

        # Fallback: locate the JSONL by SID anywhere under projects/.
        if [[ -z "$TRANSCRIPT_PATH" ]]; then
            TRANSCRIPT_PATH=$(find "$HOME/.claude/projects" -name "${SESSION_ID}.jsonl" -type f 2>/dev/null | head -1)
        fi

        if [[ -n "$TRANSCRIPT_PATH" && -f "$TRANSCRIPT_PATH" ]]; then
            BIN_DIR="$HOME/Library/Application Support/acos-token-monitor/bin"
            WATCHER="$BIN_DIR/token-watcher.py"
            LOGS_DIR="$HOME/Library/Application Support/acos-token-monitor/logs"
            LOG_PATH="$LOGS_DIR/${SESSION_ID}.log"

            # ─── Fix F (2026-06-11): per-session spawn lock ──────────────
            # The pgrep guard is racy: two SessionStart hooks (or a hook + a
            # backfill) can both pass it and spawn duplicate watchers that then
            # corrupt the shared parse-offset/log. macOS has no `flock` binary,
            # so use an atomic mkdir lock (mkdir fails if the dir exists). The
            # pgrep check is KEPT as a secondary guard inside the lock. CRITICAL:
            # the lock must NEVER block SessionStart — any lock error falls back
            # to the original pgrep-only behavior (fail-open).
            LOCKDIR="$STATE_DIR/.watcher-spawn-${SESSION_ID}.lockdir"
            # Clean a stale lockdir (crashed spawner) older than 60s so a dead
            # lock can't permanently block spawns. find -prune keeps it cheap.
            if [[ -d "$LOCKDIR" ]]; then
                if find "$LOCKDIR" -prune -mmin +1 >/dev/null 2>&1; then
                    rmdir "$LOCKDIR" 2>/dev/null || true
                fi
            fi
            mkdir -p "$LOGS_DIR"
            if mkdir "$LOCKDIR" 2>/dev/null; then
                # We hold the lock. Ensure it's released no matter how we exit.
                trap 'rmdir "$LOCKDIR" 2>/dev/null || true' EXIT
                # Already watching this SID? pgrep on argv match (secondary guard).
                if ! pgrep -f "token-watcher\.py.*${SESSION_ID}" >/dev/null 2>&1; then
                    # Detach: nohup + background + disown so the watcher outlives
                    # this hook subprocess. 2026-06-11 (Fix 7b): stderr appends to
                    # the per-session log so crash tracebacks are discoverable.
                    nohup python3 "$WATCHER" "$TRANSCRIPT_PATH" "$LOG_PATH" \
                        >/dev/null 2>>"$LOG_PATH" </dev/null &
                    disown $! 2>/dev/null || true
                fi
                rmdir "$LOCKDIR" 2>/dev/null || true
                trap - EXIT
            elif [[ -d "$STATE_DIR" ]]; then
                # mkdir failed because the lockdir exists → another spawner is
                # mid-flight. Skip spawning (one-liner note). The other spawner
                # owns this SID's watcher creation.
                printf '%s spawn skipped: lock held by concurrent spawner for %s\n' \
                    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$SESSION_ID" >> "$LOG_PATH" 2>/dev/null || true
            else
                # Lock path itself unusable (STATE_DIR gone?) — FAIL OPEN to the
                # original pgrep-only behavior so SessionStart is never blocked.
                if ! pgrep -f "token-watcher\.py.*${SESSION_ID}" >/dev/null 2>&1; then
                    nohup python3 "$WATCHER" "$TRANSCRIPT_PATH" "$LOG_PATH" \
                        >/dev/null 2>>"$LOG_PATH" </dev/null &
                    disown $! 2>/dev/null || true
                fi
            fi
        fi

        exit 0
    fi
    [[ $attempt -lt 5 ]] && sleep 0.2
done

# No claude ancestor found after 5 attempts — silent
exit 0
