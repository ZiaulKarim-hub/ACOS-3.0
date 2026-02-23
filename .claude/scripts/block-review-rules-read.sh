#!/bin/bash
# PreToolUse hook scoped to the Architect agent (matcher: Read|Bash)
# Blocks Read operations AND Bash commands targeting review-rules files.
# Covers both the legacy review-rules.yaml and the review-rules/ directory.
# Exit 0 = allow, Exit 2 = block

INPUT=$(cat)

# Check both file_path (Read tool) and command (Bash tool) for review-rules
HAS_VIOLATION=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    inp = d.get('tool_input', {})
    file_path = inp.get('file_path', '')
    command = inp.get('command', '')
    # Block the legacy file and the entire review-rules/ directory
    if 'review-rules' in file_path or 'review-rules' in command:
        print('BLOCKED')
except Exception:
    pass
" 2>/dev/null)

if [ "$HAS_VIOLATION" = "BLOCKED" ]; then
  echo "INDEPENDENCE WALL: Architect cannot access review rules (review-rules.yaml or review-rules/ directory)" >&2
  exit 2
fi

exit 0
