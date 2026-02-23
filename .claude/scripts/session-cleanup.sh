#!/bin/bash
# SessionEnd hook — cleans up ephemeral runtime state when a session ends
#
# Removes temporary files from .acos/state/ that should not persist across sessions:
#   - Token gate cache (stale estimates from previous session)
#   - Enforcement state (retry counters from previous enforcement loop)
#   - Stop retry counter (blocked-stop tracking)
#   - Continue-pending markers
#   - Continue launcher scripts
#
# Files that ARE preserved:
#   - oracle-audit.log (persistent audit trail)
#   - agent-lifecycle.log (persistent agent history)
#   - oracle-session-threshold (intentional session override)
#   - continue.log (useful for debugging launch failures)
#
# This hook runs synchronously at session end. It should be fast (<1s).

set -euo pipefail

STATE_DIR=".acos/state"

# Guard: if state dir doesn't exist, nothing to clean
if [ ! -d "$STATE_DIR" ]; then
  exit 0
fi

# ── Remove ephemeral state files ──────────────────────────────────────

# Token estimation cache (will be re-computed by next session's token-gate)
rm -f "$STATE_DIR/.token-gate-cache"

# Handoff enforcement state (retries, active flag — session-specific)
rm -f "$STATE_DIR/.handoff-enforcement"

# Stop hook retry counter
rm -f "$STATE_DIR/.stop-retry-count"

# Continuation markers and launcher scripts
rm -f "$STATE_DIR/continue-pending"
rm -f "$STATE_DIR/continue-success"
rm -f "$STATE_DIR/continue-failed"
rm -f "$STATE_DIR"/.continue-launcher-*.command
rm -f "$STATE_DIR"/.continue-launcher.sh

# Session-specific handoff trigger markers (handoff-triggered-*)
rm -f "$STATE_DIR"/handoff-triggered-*

exit 0
