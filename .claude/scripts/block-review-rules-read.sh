#!/bin/bash
# PreToolUse hook — Independence Wall: blocks the Architect (agent OR interactive
# main conversation) from reading review-rules.
#
# Registered TWO ways:
#   - agent-level on the architect (matcher Read|Bash) — fires in Task(architect) mode
#   - project-settings global (matcher Read|Bash|Grep|Glob) — fires in interactive mode,
#     where the main conversation IS the architect and no agent boundary exists.
#
# Checks every read vector's target: Read.file_path, Bash.command, Grep/Glob.path.
# Covers the legacy review-rules.yaml AND the review-rules/ directory, and the
# underscore variant review_rules. The legitimate reader assign-reviewers.sh reads
# the dir internally and is invoked as `.../assign-reviewers.sh` (no review-rules in
# the command string), so it is NOT blocked.
#
# MUST be registered BARE (no `|| printf allow` wrapper) — the wrapper would fire on
# exit 2 and emit an allow envelope, negating the block.
#
# Exit 0 = allow, Exit 2 = block.

INPUT=$(cat)

HAS_VIOLATION=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    inp = d.get('tool_input', {})
    # All target fields across read vectors: Read(file_path), Bash(command), Grep/Glob(path)
    blob = ' '.join(str(inp.get(k, '')) for k in ('file_path', 'command', 'path'))
    if 'review-rules' in blob or 'review_rules' in blob:
        print('BLOCKED')
except Exception:
    pass
" 2>/dev/null)

if [ "$HAS_VIOLATION" = "BLOCKED" ]; then
  echo "INDEPENDENCE WALL: the Architect cannot access review rules (review-rules.yaml or the review-rules/ directory). These are human-editable only." >&2
  exit 2
fi

exit 0
