#!/bin/bash
# PostToolUse hook for Write/Edit
# Logs file modification to evidence trail

EVIDENCE_DIR=".acos/evidence/current"
mkdir -p "$EVIDENCE_DIR"

# Extract file path from stdin; newlines stripped so a hostile/odd path can't
# split the single-line log entry
FILE_PATH=$(python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path','').replace('\n',' ').replace('\r',' '))" 2>/dev/null)

if [ -n "$FILE_PATH" ]; then
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) MODIFIED $FILE_PATH" >> "$EVIDENCE_DIR/modifications.log"
fi

exit 0
