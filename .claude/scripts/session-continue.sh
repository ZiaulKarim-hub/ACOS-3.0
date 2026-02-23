#!/bin/bash
# session-continue.sh — Launches a fresh Claude session after the current one exits
# Called by /acos-continue skill after handoff is saved
#
# How it works:
#   1. Detects the parent TTY (walks process tree since Bash tool has no PTY)
#   2. Detaches from the current Claude process (nohup + disown)
#   3. Waits for the current Claude process to exit
#   4. RETRY LOOP: Keeps trying to launch a new Claude session until verified
#      - Tries multiple strategies: osascript (macOS), TTY redirect, open command
#      - Verifies a new claude process actually started after each attempt
#      - Retries up to MAX_RETRIES with backoff between attempts
#
# The new session will automatically load the handoff via auto-load-handoff.sh
#
# Environment:
#   ACOS_CONTINUE_DELAY=N    # Seconds to wait before starting new session (default: 5)
#   ACOS_CONTINUE_PROMPT=""  # Optional prompt for the new session
#   ACOS_CONTINUE_RETRIES=N  # Max launch retry attempts (default: 5)

set -euo pipefail

DELAY=${ACOS_CONTINUE_DELAY:-5}
PROMPT=${ACOS_CONTINUE_PROMPT:-""}
MAX_RETRIES=${ACOS_CONTINUE_RETRIES:-5}
STATE_DIR=".acos/state"
CWD="$(pwd)"
LOG_FILE="$STATE_DIR/continue.log"
PARENT_PID="$PPID"

# ── TTY Detection ──────────────────────────────────────────────────────
# IMPORTANT: `tty` fails in Claude Code's Bash tool (no PTY allocated).
# Walk the process tree via `ps` to find the ancestor's TTY.
PARENT_TTY=$(tty 2>/dev/null || echo "")
if [ -z "$PARENT_TTY" ] || [ "$PARENT_TTY" = "not a tty" ]; then
  WALK_PID=$$
  for _i in 1 2 3 4 5 6; do
    WALK_PID=$(ps -o ppid= -p "$WALK_PID" 2>/dev/null | tr -d ' ')
    if [ -z "$WALK_PID" ] || [ "$WALK_PID" = "1" ]; then
      break
    fi
    FOUND_TTY=$(ps -o tty= -p "$WALK_PID" 2>/dev/null | tr -d ' ')
    if [ -n "$FOUND_TTY" ] && [ "$FOUND_TTY" != "??" ] && [ "$FOUND_TTY" != "-" ]; then
      PARENT_TTY="/dev/$FOUND_TTY"
      break
    fi
  done
fi
if [ "$PARENT_TTY" = "not a tty" ]; then
  PARENT_TTY=""
fi

# ── Detect Platform ────────────────────────────────────────────────────
IS_MACOS=false
if [ "$(uname -s)" = "Darwin" ]; then
  IS_MACOS=true
fi

mkdir -p "$STATE_DIR"

# Write a marker so other hooks know a continuation is pending
echo "$$" > "$STATE_DIR/continue-pending"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) Continue requested from PID $PARENT_PID (TTY: ${PARENT_TTY:-none}, macOS: $IS_MACOS)" > "$LOG_FILE"

# ── Detach and run continuation in background ──────────────────────────
nohup bash -c '
  LOG_FILE='"'$LOG_FILE'"'
  CWD='"'$CWD'"'
  DELAY='"'$DELAY'"'
  PROMPT='"'$PROMPT'"'
  STATE_DIR='"'$STATE_DIR'"'
  PARENT_PID='"'$PARENT_PID'"'
  PARENT_TTY='"'$PARENT_TTY'"'
  IS_MACOS='"'$IS_MACOS'"'
  MAX_RETRIES='"'$MAX_RETRIES'"'

  log() {
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $1" >> "$LOG_FILE"
  }

  # Snapshot existing claude PIDs so we can detect new ones
  get_claude_pids() {
    pgrep -f "claude" 2>/dev/null | sort || true
  }

  # Check if a new claude process appeared since the snapshot
  verify_claude_launched() {
    local before_pids="$1"
    sleep 3  # Give the process time to start
    local after_pids
    after_pids=$(get_claude_pids)
    # Check if any new PIDs appeared
    local new_pids
    new_pids=$(comm -13 <(echo "$before_pids") <(echo "$after_pids") 2>/dev/null || true)
    if [ -n "$new_pids" ]; then
      log "Verified: new claude process(es) detected: $new_pids"
      return 0
    else
      log "Verification failed: no new claude process detected"
      return 1
    fi
  }

  log "Background continuation process started (PID $$)"
  log "Waiting for parent Claude process (PID $PARENT_PID) to exit..."

  # Wait for parent Claude process to exit (up to 120 seconds)
  WAIT_COUNT=0
  while kill -0 "$PARENT_PID" 2>/dev/null; do
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
    if [ "$WAIT_COUNT" -ge 120 ]; then
      log "Timeout waiting for parent to exit after 120s. Aborting."
      rm -f "$STATE_DIR/continue-pending"
      exit 1
    fi
  done

  log "Parent process exited after ${WAIT_COUNT}s. Waiting ${DELAY}s cooldown..."
  sleep "$DELAY"

  rm -f "$STATE_DIR/continue-pending"

  # ══════════════════════════════════════════════════════════════════════
  # RETRY LOOP — Keep trying to launch Claude until verified or exhausted
  # ══════════════════════════════════════════════════════════════════════

  # Build the command to run in the new session
  # Use single quotes around the path to avoid breaking AppleScript double-quote strings.
  # (Paths with spaces like "Vibe Coding" break osascript when double-quoted inside do script "...")
  # printf \047 = single quote character (avoids breaking the outer bash -c heredoc)
  SQ=$(printf "\047")
  if [ -n "$PROMPT" ]; then
    CLAUDE_CMD="cd ${SQ}${CWD}${SQ} && claude \"$PROMPT\""
  else
    CLAUDE_CMD="cd ${SQ}${CWD}${SQ} && claude"
  fi

  LAUNCHED=false
  ATTEMPT=0

  while [ "$LAUNCHED" = "false" ] && [ "$ATTEMPT" -lt "$MAX_RETRIES" ]; do
    ATTEMPT=$((ATTEMPT + 1))
    BACKOFF=$((ATTEMPT * 2))  # 2s, 4s, 6s, 8s, 10s between retries
    log "=== Launch attempt $ATTEMPT/$MAX_RETRIES ==="

    # Snapshot current claude processes before attempting launch
    BEFORE_PIDS=$(get_claude_pids)

    # ── Strategy 1: macOS osascript (opens new tab/window) ──────────
    if [ "$IS_MACOS" = "true" ] && [ "$LAUNCHED" = "false" ]; then

      # Try Warp first (if running) — uses Warp AppleScript support
      # Note: Warp binary is named "stable", so pgrep by name fails.
      # Match the full path of the running process instead.
      if pgrep -qf "Warp.app" 2>/dev/null; then
        log "[$ATTEMPT] Trying Warp new tab..."
        if osascript -e "
          tell application \"Warp\"
            activate
          end tell
          delay 0.5
          tell application \"System Events\"
            tell process \"Warp\"
              keystroke \"t\" using command down
              delay 0.3
              keystroke \"$CLAUDE_CMD\"
              key code 36
            end tell
          end tell
        " >> "$LOG_FILE" 2>&1; then
          if verify_claude_launched "$BEFORE_PIDS"; then
            LAUNCHED=true
            log "[$ATTEMPT] SUCCESS: Launched via Warp new tab (verified)"
          else
            log "[$ATTEMPT] Warp tab opened but claude process not detected"
          fi
        else
          log "[$ATTEMPT] Warp osascript failed"
        fi

        # Warp fallback: open -a with launcher script
        if [ "$LAUNCHED" = "false" ]; then
          log "[$ATTEMPT] Trying open -a Warp with launcher script..."
          LAUNCHER="$STATE_DIR/.continue-launcher-warp-${ATTEMPT}.command"
          cat > "$LAUNCHER" << INNEREOF
#!/bin/bash
$CLAUDE_CMD
INNEREOF
          chmod +x "$LAUNCHER"
          if open -a "Warp" "$LAUNCHER" >> "$LOG_FILE" 2>&1; then
            if verify_claude_launched "$BEFORE_PIDS"; then
              LAUNCHED=true
              log "[$ATTEMPT] SUCCESS: Launched via open -a Warp (verified)"
            else
              log "[$ATTEMPT] Warp open command ran but claude process not detected"
            fi
          else
            log "[$ATTEMPT] open -a Warp failed"
          fi
        fi
      fi

      # Try iTerm2 (if running)
      if [ "$LAUNCHED" = "false" ] && pgrep -q iTerm2 2>/dev/null; then
        log "[$ATTEMPT] Trying iTerm2 new tab..."
        if osascript -e "
          tell application \"iTerm2\"
            tell current window
              create tab with default profile
              tell current session
                write text \"$CLAUDE_CMD\"
              end tell
            end tell
          end tell
        " >> "$LOG_FILE" 2>&1; then
          if verify_claude_launched "$BEFORE_PIDS"; then
            LAUNCHED=true
            log "[$ATTEMPT] SUCCESS: Launched via iTerm2 new tab (verified)"
          else
            log "[$ATTEMPT] iTerm2 tab opened but claude process not detected"
          fi
        else
          log "[$ATTEMPT] iTerm2 osascript failed"
        fi
      fi

      # Try Terminal.app new window (last resort for macOS GUI)
      if [ "$LAUNCHED" = "false" ]; then
        log "[$ATTEMPT] Trying Terminal.app new window..."
        if osascript -e "
          tell application \"Terminal\"
            activate
            do script \"$CLAUDE_CMD\"
          end tell
        " >> "$LOG_FILE" 2>&1; then
          if verify_claude_launched "$BEFORE_PIDS"; then
            LAUNCHED=true
            log "[$ATTEMPT] SUCCESS: Launched via Terminal.app (verified)"
          else
            log "[$ATTEMPT] Terminal.app window opened but claude process not detected"
          fi
        else
          log "[$ATTEMPT] Terminal.app osascript failed"
        fi
      fi

      # Try `open` with a .command launcher script
      if [ "$LAUNCHED" = "false" ]; then
        log "[$ATTEMPT] Trying open .command file (default terminal)..."
        LAUNCHER="$STATE_DIR/.continue-launcher-${ATTEMPT}.command"
        cat > "$LAUNCHER" << INNEREOF
#!/bin/bash
$CLAUDE_CMD
INNEREOF
        chmod +x "$LAUNCHER"
        if open "$LAUNCHER" >> "$LOG_FILE" 2>&1; then
          if verify_claude_launched "$BEFORE_PIDS"; then
            LAUNCHED=true
            log "[$ATTEMPT] SUCCESS: Launched via open .command file (verified)"
          else
            log "[$ATTEMPT] .command file opened but claude process not detected"
          fi
        else
          log "[$ATTEMPT] open command failed"
        fi
      fi
    fi

    # ── Strategy 2: TTY redirect with script(1) PTY wrapper ─────────
    if [ "$LAUNCHED" = "false" ] && [ -n "$PARENT_TTY" ] && [ -e "$PARENT_TTY" ] && [ -w "$PARENT_TTY" ]; then
      log "[$ATTEMPT] Trying TTY redirect via $PARENT_TTY..."
      LAUNCHER="$STATE_DIR/.continue-launcher.sh"
      cat > "$LAUNCHER" << INNEREOF
#!/bin/bash
cd "$CWD"
exec claude $PROMPT
INNEREOF
      chmod +x "$LAUNCHER"

      if command -v script >/dev/null 2>&1; then
        script -q /dev/null "$LAUNCHER" < "$PARENT_TTY" > "$PARENT_TTY" 2>&1 &
      else
        bash "$LAUNCHER" < "$PARENT_TTY" > "$PARENT_TTY" 2>&1 &
      fi

      if verify_claude_launched "$BEFORE_PIDS"; then
        LAUNCHED=true
        log "[$ATTEMPT] SUCCESS: Launched via TTY redirect (verified)"
      else
        log "[$ATTEMPT] TTY redirect did not produce a claude process"
      fi
    fi

    # ── If not launched yet, wait before retrying ────────────────────
    if [ "$LAUNCHED" = "false" ] && [ "$ATTEMPT" -lt "$MAX_RETRIES" ]; then
      log "[$ATTEMPT] All strategies failed this round. Waiting ${BACKOFF}s before retry..."
      sleep "$BACKOFF"
    fi
  done

  # ══════════════════════════════════════════════════════════════════════
  # POST-LOOP: Write results
  # ══════════════════════════════════════════════════════════════════════

  if [ "$LAUNCHED" = "true" ]; then
    log "Session continuation SUCCEEDED after $ATTEMPT attempt(s)"
    # Write success marker
    echo "$ATTEMPT" > "$STATE_DIR/continue-success"
  else
    log "Session continuation FAILED after $MAX_RETRIES attempts"
    # Write failure marker with instructions
    echo "failed:$MAX_RETRIES" > "$STATE_DIR/continue-failed"

    # Best-effort: write instructions to the TTY
    HINT="
══════════════════════════════════════════════════════════
  ACOS Continue — Auto-launch failed after $MAX_RETRIES attempts

  Run this manually to continue:
    cd $CWD && claude

  The handoff will be auto-loaded by the SessionStart hook.
  Check $LOG_FILE for detailed failure logs.
══════════════════════════════════════════════════════════
"
    if [ -n "$PARENT_TTY" ] && [ -w "$PARENT_TTY" ]; then
      echo "$HINT" > "$PARENT_TTY"
    fi
    echo "$HINT" >> "$LOG_FILE"

    # macOS: show a notification as last resort
    if [ "$IS_MACOS" = "true" ]; then
      osascript -e "display notification \"Auto-launch failed after $MAX_RETRIES attempts. Run: claude\" with title \"ACOS Continue\"" 2>/dev/null || true
    fi
  fi

  log "Continuation process complete"
' >> "$LOG_FILE" 2>&1 &

# Disown the background process so it survives when the parent exits
disown $! 2>/dev/null || true

echo "Continuation process launched (background PID: $!)"
echo "Detected TTY: ${PARENT_TTY:-none} | Platform: $(uname -s)"
echo "Will retry up to ${MAX_RETRIES} times to start a new Claude session."
echo "A new session will start ~${DELAY}s after this session ends."
echo "Log: $LOG_FILE"
