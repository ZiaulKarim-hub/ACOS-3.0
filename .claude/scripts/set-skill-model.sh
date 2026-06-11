#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# set-skill-model.sh — Switch model profile for a skill session
# ═══════════════════════════════════════════════════════════════════════════════
#
# Usage:
#   bash .claude/scripts/set-skill-model.sh <profile-name>
#   bash .claude/scripts/set-skill-model.sh glm-review
#   bash .claude/scripts/set-skill-model.sh --reset
#
# Writes the selected profile to .acos/state/model-session.yaml so that
# resolve-agent-model.sh picks it up for all subsequent agent spawns.
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATE_DIR="$PROJECT_ROOT/.acos/state"
SESSION_FILE="$STATE_DIR/model-session.yaml"

mkdir -p "$STATE_DIR"

if [[ "${1:-}" == "--reset" ]]; then
    rm -f "$SESSION_FILE"
    echo "Model profile reset to config default."
    exit 0
fi

PROFILE="${1:?Usage: set-skill-model.sh <profile-name|--reset>}"

# Validate profile exists in config
CONFIG="$PROJECT_ROOT/.acos/config/model-profile.yaml"
if [[ -f "$CONFIG" ]]; then
    if ! grep -qE "^[[:space:]]{2}$(printf '%s' "$PROFILE" | sed 's/[.[*^$\\]/\\&/g'):" "$CONFIG" 2>/dev/null; then
        echo "Warning: Profile '$PROFILE' not found in model-profile.yaml" >&2
        echo "Available profiles:" >&2
        grep -E '^  [A-Za-z0-9]' "$CONFIG" | sed 's/:.*//' | sed 's/^  /    /' >&2
        exit 1
    fi
fi

cat > "$SESSION_FILE" <<EOF
# Session model override — set by skill model chooser
# Cleared by session-cleanup.sh at SessionEnd
active_profile: ${PROFILE}
EOF

echo "Model profile switched to: $PROFILE"
