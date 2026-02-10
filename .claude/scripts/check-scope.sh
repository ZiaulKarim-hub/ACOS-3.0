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

# If we can't parse the input, fail open
if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Always allow writes to .acos/ (evidence, config) and memory/ (handoff logs)
if [[ "$FILE_PATH" == .acos/* ]] || [[ "$FILE_PATH" == memory/* ]]; then
  exit 0
fi

# Extract allowed files list from active slice YAML
ALLOWED=$(python3 -c "
import yaml, sys
try:
    with open('$ACTIVE_SLICE') as f:
        data = yaml.safe_load(f)
    allowed = data.get('files_allowed', [])
    for f in allowed:
        print(f)
except Exception:
    sys.exit(1)
" 2>/dev/null)

# If YAML parsing fails, fail open
if [ $? -ne 0 ]; then
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
