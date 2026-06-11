#!/bin/bash
# PreToolUse hook for Write/Edit
# Reads JSON from stdin: {"tool_input": {"file_path": "..."}}
# Checks against .acos/config/active-slice.yaml files_allowed
# Exit 0 = allow, Exit 2 = block

ACTIVE_SLICE=".acos/config/active-slice.yaml"

# Read stdin once
INPUT=$(cat)

# No active slice = no restrictions (allow all writes)
if [ ! -f "$ACTIVE_SLICE" ]; then
  exit 0
fi

# Extract file_path from stdin JSON
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)

# If we can't parse the input, fail open (log for diagnostics)
if [ -z "$FILE_PATH" ]; then
  echo "check-scope: FAIL-OPEN — could not parse file_path from hook input" >&2
  exit 0
fi

# Always allow writes to .acos/evidence/ and .acos/state/ (runtime data)
# Block .acos/config/ (requires explicit scope allowance like any other file)
if [[ "$FILE_PATH" == .acos/evidence/* ]] || [[ "$FILE_PATH" == .acos/state/* ]]; then
  exit 0
fi
# Allow memory/ writes (handoff logs, decisions)
if [[ "$FILE_PATH" == memory/* ]]; then
  exit 0
fi

# Extract allowed files list from active slice YAML (stdlib only — no PyYAML)
# The files_allowed section is a simple YAML list:
#   files_allowed:
#     - "src/foo.ts"
#     - "src/bar.ts"
ALLOWED=$(python3 -c "
import sys, re
# Exit codes (consumed by the bash caller):
#   0 = success — files_allowed parsed (list printed on stdout). An EMPTY list
#       here is meaningful: a slice that allows NO files. We print nothing and
#       exit 0 so the caller fails CLOSED (blocks the write).
#   2 = genuine parse error (file unreadable / regex blew up) — caller fails OPEN.
try:
    with open(sys.argv[1]) as f:
        text = f.read()
    # Find the files_allowed block and extract list items
    m = re.search(r'files_allowed:\s*\n((?:\s+-\s+.*\n?)*)', text)
    if not m:
        # No files_allowed block (or it is empty) — a VALID slice that allows
        # nothing. Emit an empty allow-list and exit 0 → caller blocks all writes.
        sys.exit(0)
    for line in m.group(1).strip().split('\n'):
        line = line.strip()
        if line.startswith('- '):
            val = line[2:].strip().strip('\"').strip(\"'\")
            if val:
                print(val)
    sys.exit(0)
except Exception:
    # Genuine parse failure — fail open so a malformed YAML doesn't lock out writes.
    sys.exit(2)
" "$ACTIVE_SLICE" 2>/dev/null)
PARSE_RC=$?

# Only a GENUINE parse error (exit 2) fails open. Exit 0 with an empty list means
# "this slice allows nothing" → fall through to the matcher, which blocks (fail-closed).
if [ "$PARSE_RC" -eq 2 ]; then
  echo "check-scope: FAIL-OPEN — could not parse files_allowed from $ACTIVE_SLICE" >&2
  exit 0
fi

# Check if FILE_PATH matches any allowed pattern (supports glob)
while IFS= read -r pattern; do
  [ -z "$pattern" ] && continue
  if [[ "$FILE_PATH" == $pattern ]]; then
    exit 0
  fi
done <<< "$ALLOWED"

echo "BLOCKED: $FILE_PATH is not in active slice's files_allowed" >&2
exit 2
