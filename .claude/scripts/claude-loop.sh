#!/bin/bash
# claude-loop.sh — Auto-continuation wrapper for Claude Code sessions
# Automatically restarts Claude after session ends (context overflow, natural stop, etc.)
# Handoff context is loaded manually next session via /acos-handoff (no auto-load hook).
#
# Usage:
#   ./claude-loop.sh                    # Start fresh, auto-continue on exit
#   ./claude-loop.sh --max-sessions 5   # Limit to 5 consecutive sessions
#   ./claude-loop.sh --resume <id>      # Start by resuming a specific session
#   ./claude-loop.sh --prompt "..."     # Pass initial prompt to first session
#   ./claude-loop.sh --cooldown 10      # Wait 10 seconds between sessions (default: 5)
#
# Environment:
#   CLAUDE_LOOP_MAX=N          # Max sessions (overridden by --max-sessions)
#   CLAUDE_LOOP_COOLDOWN=N     # Seconds between sessions (overridden by --cooldown)
#   CLAUDE_LOOP_NOTIFY=1       # Enable macOS notifications between sessions

set -euo pipefail

# --- Defaults ---
MAX_SESSIONS=${CLAUDE_LOOP_MAX:-0}  # 0 = unlimited
COOLDOWN=${CLAUDE_LOOP_COOLDOWN:-5}
NOTIFY=${CLAUDE_LOOP_NOTIFY:-1}
INITIAL_PROMPT=""
RESUME_ID=""
SESSION_COUNT=0
HANDOFF_DIR="memory/handoffs"

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
  case $1 in
    --max-sessions)
      MAX_SESSIONS="$2"
      shift 2
      ;;
    --resume)
      RESUME_ID="$2"
      shift 2
      ;;
    --prompt)
      INITIAL_PROMPT="$2"
      shift 2
      ;;
    --cooldown)
      COOLDOWN="$2"
      shift 2
      ;;
    --no-notify)
      NOTIFY=0
      shift
      ;;
    --help|-h)
      echo "Usage: claude-loop.sh [OPTIONS]"
      echo ""
      echo "Auto-continuation wrapper for Claude Code sessions."
      echo "Automatically restarts Claude when a session ends."
      echo ""
      echo "Options:"
      echo "  --max-sessions N   Maximum consecutive sessions (0 = unlimited, default: 0)"
      echo "  --resume ID        Resume a specific session ID on first run"
      echo "  --prompt TEXT      Initial prompt for the first session"
      echo "  --cooldown N       Seconds to wait between sessions (default: 5)"
      echo "  --no-notify        Disable macOS notifications"
      echo "  -h, --help         Show this help"
      echo ""
      echo "Environment variables:"
      echo "  CLAUDE_LOOP_MAX=N        Same as --max-sessions"
      echo "  CLAUDE_LOOP_COOLDOWN=N   Same as --cooldown"
      echo "  CLAUDE_LOOP_NOTIFY=1     Enable notifications (default: 1)"
      echo ""
      echo "The loop stops when:"
      echo "  - User presses Ctrl+C"
      echo "  - Max sessions reached"
      echo "  - A .acos/state/loop-stop marker file is created"
      echo "  - Claude exits with code 0 and no handoff was created (clean exit)"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

# --- Notification helper ---
notify() {
  local title="$1"
  local message="$2"
  if [ "$NOTIFY" = "1" ] && command -v osascript &>/dev/null; then
    # Use stdin to avoid AppleScript injection via string interpolation
    osascript <<APPLESCRIPT 2>/dev/null || true
display notification "$(/usr/bin/sed 's/["\]/\\&/g' <<< "$message")" with title "$(/usr/bin/sed 's/["\]/\\&/g' <<< "$title")"
APPLESCRIPT
  fi
}

# --- Cleanup ---
cleanup() {
  echo ""
  echo "=== Claude Loop ended after $SESSION_COUNT session(s) ==="
  notify "Claude Loop" "Ended after $SESSION_COUNT sessions"
  exit 0
}
trap cleanup SIGINT SIGTERM

# --- Check for stop marker ---
should_stop() {
  [ -f ".acos/state/loop-stop" ]
}

# --- Count today's handoffs ---
count_handoffs() {
  local today=$(date -u +%Y-%m-%d)
  local count=0
  for f in "$HANDOFF_DIR"/${today}*.yaml "$HANDOFF_DIR"/${today}*.yml "$HANDOFF_DIR"/${today}*.md; do
    [ -f "$f" ] && count=$((count + 1))
  done
  echo "$count"
}

# --- Main loop ---
echo "=== Claude Loop starting ==="
echo "    Max sessions: ${MAX_SESSIONS:-unlimited}"
echo "    Cooldown: ${COOLDOWN}s"
echo "    Handoff dir: $HANDOFF_DIR"
echo ""

# Remove any previous stop marker
rm -f ".acos/state/loop-stop"

while true; do
  SESSION_COUNT=$((SESSION_COUNT + 1))

  # Check max sessions
  if [ "$MAX_SESSIONS" -gt 0 ] && [ "$SESSION_COUNT" -gt "$MAX_SESSIONS" ]; then
    echo "=== Max sessions ($MAX_SESSIONS) reached ==="
    break
  fi

  # Check stop marker
  if should_stop; then
    echo "=== Stop marker found (.acos/state/loop-stop) ==="
    break
  fi

  HANDOFFS_BEFORE=$(count_handoffs)

  echo "=== Session #${SESSION_COUNT} starting at $(date) ==="
  notify "Claude Loop" "Session #${SESSION_COUNT} starting"

  # Build claude command as an array (no eval — prevents shell injection)
  CLAUDE_ARGS=()

  if [ "$SESSION_COUNT" -eq 1 ] && [ -n "$RESUME_ID" ]; then
    # First session: resume specific session
    CLAUDE_ARGS+=(--resume "$RESUME_ID")
  elif [ "$SESSION_COUNT" -gt 1 ]; then
    # Subsequent sessions: continue most recent
    CLAUDE_ARGS+=(--continue)
  fi

  if [ "$SESSION_COUNT" -eq 1 ] && [ -n "$INITIAL_PROMPT" ]; then
    CLAUDE_ARGS+=("$INITIAL_PROMPT")
  fi

  # Run Claude
  set +e
  claude "${CLAUDE_ARGS[@]}"
  EXIT_CODE=$?
  set -e

  echo ""
  echo "=== Session #${SESSION_COUNT} ended (exit code: $EXIT_CODE) at $(date) ==="

  HANDOFFS_AFTER=$(count_handoffs)

  # Check if a new handoff was created during this session
  if [ "$HANDOFFS_AFTER" -gt "$HANDOFFS_BEFORE" ]; then
    echo "    Handoff created during session — will auto-load in next session"
    notify "Claude Loop" "Session ended with handoff. Restarting in ${COOLDOWN}s..."
  else
    # No handoff created — this was likely a clean exit or short session
    if [ "$EXIT_CODE" -eq 0 ]; then
      echo "    Clean exit with no handoff — session likely completed naturally"
      echo "    Continue loop? (auto-continuing in ${COOLDOWN}s, Ctrl+C to stop)"
    fi
  fi

  # Check stop marker again
  if should_stop; then
    echo "=== Stop marker found (.acos/state/loop-stop) ==="
    break
  fi

  # Cooldown
  echo "    Waiting ${COOLDOWN}s before next session..."
  sleep "$COOLDOWN"
done

echo "=== Claude Loop finished: $SESSION_COUNT session(s) ==="
notify "Claude Loop" "Finished after $SESSION_COUNT sessions"
