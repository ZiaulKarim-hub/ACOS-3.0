#!/bin/bash
# PreToolUse hook — Independence Wall: blocks the Architect (agent OR interactive
# main conversation) from reading review-rules.
#
# Registered TWO ways:
#   - agent-level on the architect (matcher Read|Bash) — fires in Task(architect) mode
#   - project-settings global (matcher Read|Bash|Grep|Glob) — fires in interactive mode,
#     where the main conversation IS the architect and no agent boundary exists.
#
# Checks EVERY field of tool_input (serialized), so no read vector can slip a target
# through an uninspected field (file_path, command, path, pattern, glob, notebook_path).
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
    # Scan the ENTIRE tool_input, not a hardcoded subset of fields. Glob's primary
    # target is 'pattern' and Grep uses 'pattern'/'glob', so a Glob/Grep aimed at
    # the wall target via 'pattern' would bypass a file_path/command/path-only check.
    # Serializing the whole input catches every current and future target field.
    blob = json.dumps(inp)
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
