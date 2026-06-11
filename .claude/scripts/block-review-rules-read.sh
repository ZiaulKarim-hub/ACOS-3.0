#!/bin/bash
# PreToolUse hook - Independence Wall: blocks the Architect (agent OR interactive
# main conversation) from reading review rules.
#
# Registered TWO ways:
#   - agent-level on the architect (matcher Read|Bash) - fires in Task(architect) mode
#   - project-settings global (matcher Read|Bash|Grep|Glob) - fires in interactive mode,
#     where the main conversation IS the architect and no agent boundary exists.
#
# Checks EVERY field of tool_input (serialized), so no read vector can slip a target
# through an uninspected field (file_path, command, path, pattern, glob, notebook_path).
# Covers the legacy YAML pointer AND the directory, and the underscore variant.
# The legitimate reader assign-reviewers.sh reads the dir internally and is invoked as
# `.../assign-reviewers.sh` (protected substring not in the command string), so it is
# NOT blocked.
#
# MUST be registered BARE (no `|| printf allow` wrapper) - the wrapper would fire on
# exit 2 and emit an allow envelope, negating the block.
#
# This is an independence WALL: it FAILS CLOSED, independently of python. The python
# helper ALWAYS prints an explicit decision token ('ALLOW' on the clean no-target
# path, 'BLOCKED' otherwise). The bash layer treats ANYTHING other than the exact
# 'ALLOW' token - including empty output, a missing/erroring python3 interpreter
# (swallowed by 2>/dev/null), OOM, or malformed JSON - as BLOCKED. Only a positive,
# explicit 'ALLOW' from a successfully-run inspection lets the call through.
#
# Exit 0 = allow, Exit 2 = block.

INPUT=$(cat)

DECISION=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    raw = sys.stdin.read()
    if not raw.strip():
        # Empty stdin: cannot prove this is safe -> fail CLOSED.
        print('BLOCKED')
        sys.exit(0)
    d = json.loads(raw)
except Exception:
    # Could not parse stdin (malformed JSON): fail CLOSED.
    print('BLOCKED')
    sys.exit(0)

# Parsed valid JSON: inspect for a protected target.
inp = d.get('tool_input', {})
# Scan the ENTIRE tool_input, not a hardcoded subset of fields. Glob's primary
# target is 'pattern' and Grep uses 'pattern'/'glob', so a Glob/Grep aimed at
# the wall target via 'pattern' would bypass a file_path/command/path-only check.
# Serializing the whole input catches every current and future target field.
blob = json.dumps(inp)
if 'review-rules' in blob or 'review_rules' in blob:
    print('BLOCKED')
else:
    # Clean: no protected target found. Emit the POSITIVE allow token so the bash
    # layer can distinguish 'inspected, safe' from 'python never ran'.
    print('ALLOW')
" 2>/dev/null)

# Fail CLOSED: anything that is not an exact, positive 'ALLOW' is a block. This
# covers BLOCKED, empty output (python missing/crashed/OOM), and any stray text.
if [ "$DECISION" != "ALLOW" ]; then
  echo "INDEPENDENCE WALL: the Architect cannot access review rules (the YAML pointer or the review rules directory). These are human-editable only." >&2
  exit 2
fi

exit 0
