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

# Quick exit if already initialized
if [[ -d ".acos" && -f ".acos/config/project.yaml" ]]; then
  exit 0
fi

# Not initialized — find and run bootstrap
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOOTSTRAP="$SCRIPT_DIR/acos-bootstrap.sh"

if [[ -f "$BOOTSTRAP" ]]; then
  bash "$BOOTSTRAP"
else
  # Fallback: search for ACOS 3.0 installation
  BOOTSTRAP_FOUND="$(find "$HOME/Documents" -maxdepth 5 -path "*/ACOS 3.0/.claude/scripts/acos-bootstrap.sh" 2>/dev/null | head -1)"
  if [[ -n "$BOOTSTRAP_FOUND" ]]; then
    bash "$BOOTSTRAP_FOUND"
  else
    echo "⚠ ACOS 3.0 not found. Please ensure ACOS 3.0 is installed in ~/Documents/Vibe Coding/ACOS 3.0/"
    exit 1
  fi
fi
