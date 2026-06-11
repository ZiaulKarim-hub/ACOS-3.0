#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# ACOS v3.0 - Pre-flight Check
# ═══════════════════════════════════════════════════════════════════════════
#
# Lightweight check that runs at the start of every ACOS skill.
# If ACOS is not initialized in the current directory, runs bootstrap.
# If already initialized, exits immediately (< 1ms overhead).
#
# Usage: bash .claude/scripts/acos-preflight.sh
#    or: bash "<ACOS_SOURCE>/.claude/scripts/acos-preflight.sh"
#
# ═══════════════════════════════════════════════════════════════════════════

# Quick exit if already initialized AND hooks are complete
if [[ -d ".acos" && -f ".acos/config/project.yaml" ]]; then
  # Validate hook completeness — these 5 commands are critical ACOS infrastructure
  SETTINGS=".claude/settings.local.json"
  if [[ -f "$SETTINGS" ]]; then
    HOOKS_OK=true
    # Hooks may live in the project OR the user-global settings file (Claude Code merges both).
    # auto-load-handoff.sh was removed Apr 2026 and is intentionally NOT checked here.
    for cmd in "token-gate.sh" "oracle-evaluate.py" "check-scope.sh" "context-monitor.sh"; do
      if ! grep -qs "$cmd" "$SETTINGS" "$HOME/.claude/settings.local.json"; then
        HOOKS_OK=false
        break
      fi
    done
    if [[ "$HOOKS_OK" == true ]]; then
      exit 0
    fi
    # Missing hooks detected — re-run bootstrap to add them (merge is idempotent)
    echo "ACOS preflight: missing hooks detected, running bootstrap --force to repair..."
  else
    # settings.local.json absent means NO hooks are installed — fall through to
    # the bootstrap-repair path below instead of falsely declaring ready.
    echo "ACOS preflight: settings.local.json missing (no hooks installed), running bootstrap --force to repair..."
  fi
fi

# Not initialized or needs repair — find and run bootstrap
# Use --force if .acos/ exists (repair mode) to bypass the already-initialized guard
BOOTSTRAP_FLAGS=""
[[ -d ".acos" ]] && BOOTSTRAP_FLAGS="--force"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOOTSTRAP="$SCRIPT_DIR/acos-bootstrap.sh"

if [[ -f "$BOOTSTRAP" ]]; then
  bash "$BOOTSTRAP" $BOOTSTRAP_FLAGS
else
  # Fallback: search for ACOS 3.0 installation
  BOOTSTRAP_FOUND="$(find "$HOME/Documents" -maxdepth 5 -path "*/ACOS 3.0/.claude/scripts/acos-bootstrap.sh" 2>/dev/null | head -1)"
  if [[ -n "$BOOTSTRAP_FOUND" ]]; then
    bash "$BOOTSTRAP_FOUND" $BOOTSTRAP_FLAGS
  else
    echo "⚠ ACOS 3.0 not found. Please ensure ACOS 3.0 is installed in ~/Documents/Vibe Coding/ACOS 3.0/"
    exit 1
  fi
fi
