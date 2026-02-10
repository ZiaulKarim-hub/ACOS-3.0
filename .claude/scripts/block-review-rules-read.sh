#!/bin/bash
# PreToolUse hook scoped to the Architect agent
# Blocks Read operations targeting review-rules.yaml
# Exit 0 = allow, Exit 2 = block

FILE_PATH=$(cat | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)

if echo "$FILE_PATH" | grep -q "review-rules"; then
  echo "INDEPENDENCE WALL: Architect cannot read review-rules.yaml" >&2
  exit 2
fi

exit 0
