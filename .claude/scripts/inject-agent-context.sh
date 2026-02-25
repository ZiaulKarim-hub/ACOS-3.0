#!/bin/bash
# SubagentStart hook — injects relevant project context into subagent startup
#
# When a subagent is spawned, this hook provides additionalContext with:
#   1. The currently active slice (if any) from .acos/state/
#   2. The project's source of truth (vision document path)
#   3. Active planning context (current epic/story)
#
# This ensures subagents (especially developer and reviewer agents) have
# awareness of what slice they're working on without the Architect needing
# to manually repeat this in every Task() prompt.
#
# This hook runs synchronously (not async) because the context needs to be
# available when the subagent starts. It should complete in <500ms.
#
# Input: JSON with agent_name, agent_type, session_id
# Output: JSON with additionalContext (or empty for no injection)

set -euo pipefail

STATE_DIR=".acos/state"
PLANNING_DIR="planning"

INPUT=$(cat)

# Extract agent info
AGENT_INFO=$(python3 -c "
import sys, json

try:
    data = json.load(sys.stdin)
    agent_name = data.get('agent_name', '')
    agent_type = data.get('agent_type', '')
    print(f'{agent_name}\t{agent_type}')
except Exception:
    print('\t')
" <<< "$INPUT" 2>/dev/null || echo "")

IFS=$'\t' read -r AGENT_NAME AGENT_TYPE <<< "$AGENT_INFO"

# Only inject context for agents that benefit from it
# Skip for memory-agent, learning-agent (they have their own context)
case "$AGENT_NAME" in
  memory-agent|learning-agent)
    exit 0
    ;;
esac

# ── Gather context ────────────────────────────────────────────────────
CONTEXT_PARTS=()

# 1. Active slice (from active-slice.yaml config)
SCOPE_FILE=".acos/config/active-slice.yaml"
if [ -f "$SCOPE_FILE" ]; then
  ACTIVE_SCOPE=$(python3 -c "
import sys, re
try:
    with open(sys.argv[1]) as f:
        text = f.read()
    m = re.search(r'slice_id:\s*[\"'\''']?([^\"'\'''\n]+)', text)
    if m: print(m.group(1).strip())
except Exception: pass
" "$SCOPE_FILE" 2>/dev/null || true)
  if [ -n "$ACTIVE_SCOPE" ]; then
    CONTEXT_PARTS+=("Active slice: $ACTIVE_SCOPE")
  fi
fi

# 2. Current planning state (check for project.yaml)
if [ -f "$PLANNING_DIR/project.yaml" ]; then
  # Extract current epic/story/slice from project.yaml
  CURRENT_STATE=$(python3 -c "
import sys
try:
    with open('$PLANNING_DIR/project.yaml', 'r') as f:
        content = f.read()
    # Simple extraction — look for current_epic, current_story, current_slice
    parts = []
    for line in content.split('\n'):
        line = line.strip()
        for key in ('current_epic:', 'current_story:', 'current_slice:'):
            if line.startswith(key):
                val = line.split(':', 1)[1].strip().strip('\"').strip(\"'\")
                if val and val != 'null':
                    parts.append(f'{key[:-1]}={val}')
    print(' | '.join(parts) if parts else '')
except Exception:
    print('')
" 2>/dev/null || true)
  if [ -n "$CURRENT_STATE" ]; then
    CONTEXT_PARTS+=("Planning state: $CURRENT_STATE")
  fi
fi

# 3. Source of truth (vision document — check both locations)
for vdoc in "memory/source-of-truth/vision-document.md" "$PLANNING_DIR/vision-document.md" "$PLANNING_DIR/vision.md"; do
  if [ -f "$vdoc" ]; then
    CONTEXT_PARTS+=("Vision document: $vdoc")
    break
  fi
done

# If no context to inject, exit silently
if [ ${#CONTEXT_PARTS[@]} -eq 0 ]; then
  exit 0
fi

# ── Emit context ──────────────────────────────────────────────────────
CONTEXT_STR=$(printf '%s. ' "${CONTEXT_PARTS[@]}")

# Escape for JSON
CONTEXT_JSON=$(python3 -c "import sys,json; print(json.dumps(sys.argv[1]))" "$CONTEXT_STR" 2>/dev/null || echo "\"$CONTEXT_STR\"")

cat <<EOF
{
  "hookSpecificOutput": {
    "additionalContext": $CONTEXT_JSON
  }
}
EOF

exit 0
