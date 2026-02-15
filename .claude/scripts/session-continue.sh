#!/bin/bash
# session-continue.sh — Launches a fresh Claude session after the current one exits
# Called by /acos-continue skill after handoff is saved
#
# How it works:
#   1. Detaches from the current Claude process (nohup + disown)
#   2. Waits for the current Claude process to exit (polls /proc or ps)
#   3. Waits a brief cooldown for terminal cleanup
#   4. Launches a fresh `claude` session in the same directory
#
# The new session will automatically load the handoff via auto-load-handoff.sh
#
# Environment:
#   ACOS_CONTINUE_DELAY=N    # Seconds to wait before starting new session (default: 5)
#   ACOS_CONTINUE_PROMPT=""  # Optional prompt for the new session

set -euo pipefail

DELAY=${ACOS_CONTINUE_DELAY:-5}
PROMPT=${ACOS_CONTINUE_PROMPT:-""}
HANDOFF_DIR="memory/handoffs"
STATE_DIR=".acos/state"
CWD="$(pwd)"
LOG_FILE="$STATE_DIR/continue.log"
PARENT_PID="$PPID"

# Capture the controlling TTY before nohup detaches us from it.
# The TTY device (e.g. /dev/ttys003) persists after the parent exits —
# it's owned by the terminal emulator, not the Claude process.
PARENT_TTY=$(tty 2>/dev/null || echo "")

mkdir -p "$STATE_DIR"

# Write a marker so other hooks know a continuation is pending
echo "$$" > "$STATE_DIR/continue-pending"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) Continue requested from PID $PARENT_PID" > "$LOG_FILE"

# Detach and run the continuation in the background
# Use nohup + subshell + disown to fully detach from the parent process
nohup bash -c "
  LOG_FILE='$LOG_FILE'
  CWD='$CWD'
  DELAY='$DELAY'
  PROMPT='$PROMPT'
  STATE_DIR='$STATE_DIR'
  PARENT_PID='$PARENT_PID'
  PARENT_TTY='$PARENT_TTY'

  log() {
    echo \"\$(date -u +%Y-%m-%dT%H:%M:%SZ) \$1\" >> \"\$LOG_FILE\"
  }

  log \"Background continuation process started (PID \$\$)\"
  log \"Waiting for parent Claude process (PID \$PARENT_PID) to exit...\"

  # Wait for the parent Claude process to exit (up to 120 seconds)
  WAIT_COUNT=0
  while kill -0 \"\$PARENT_PID\" 2>/dev/null; do
    sleep 1
    WAIT_COUNT=\$((WAIT_COUNT + 1))
    if [ \"\$WAIT_COUNT\" -ge 120 ]; then
      log 'Timeout waiting for parent to exit after 120s. Aborting.'
      rm -f \"\$STATE_DIR/continue-pending\"
      exit 1
    fi
  done

  log \"Parent process exited. Waiting \${DELAY}s cooldown...\"
  sleep \"\$DELAY\"

  # Clean up the pending marker
  rm -f \"\$STATE_DIR/continue-pending\"

  # Check if the original TTY is still available for interactive launch.
  # nohup detaches stdin, so [ ! -t 0 ] is always true here.
  # Instead, check the captured PARENT_TTY device.
  HAS_TTY=false
  if [ -n \"\$PARENT_TTY\" ] && [ -e \"\$PARENT_TTY\" ] && [ -w \"\$PARENT_TTY\" ]; then
    HAS_TTY=true
  fi

  if [ \"\$HAS_TTY\" = \"false\" ] && [ -z \"\$PROMPT\" ]; then
    log 'No terminal attached and no prompt provided. Writing resume hint instead.'
    echo ''
    echo '=== ACOS Continue ==='
    echo 'Session handoff saved. To continue in a new session, run:'
    echo '  claude'
    echo 'The handoff will be auto-loaded.'
    echo '===================='
    exit 0
  fi

  log \"Launching fresh Claude session in \$CWD (TTY: \$PARENT_TTY)\"

  cd \"\$CWD\"

  if [ -n \"\$PROMPT\" ]; then
    if [ \"\$HAS_TTY\" = \"true\" ]; then
      exec claude \"\$PROMPT\" < \"\$PARENT_TTY\" > \"\$PARENT_TTY\" 2>&1
    else
      exec claude \"\$PROMPT\"
    fi
  else
    if [ \"\$HAS_TTY\" = \"true\" ]; then
      exec claude < \"\$PARENT_TTY\" > \"\$PARENT_TTY\" 2>&1
    else
      exec claude
    fi
  fi
" >> "$LOG_FILE" 2>&1 &

# Disown the background process so it survives when the parent exits
disown $! 2>/dev/null || true

echo "Continuation process launched (background PID: $!)"
echo "A new Claude session will start ~${DELAY}s after this session ends."
echo "Log: $LOG_FILE"
