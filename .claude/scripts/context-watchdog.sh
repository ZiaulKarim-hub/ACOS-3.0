#!/bin/bash
# PreCompact hook — creates a mechanical handoff before context compaction
# Matcher: auto
# Parses the JSONL transcript to extract session state, saves to memory/handoffs/
# Exit 0 always (cannot block compaction)

set -euo pipefail

STATE_DIR=".acos/state"
HANDOFF_DIR="memory/handoffs"
mkdir -p "$STATE_DIR" "$HANDOFF_DIR"

# Read hook input from stdin
INPUT=$(cat)

# Extract transcript path from hook input
TRANSCRIPT_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('transcript_path', ''))
" 2>/dev/null)

# If no transcript, write a minimal handoff
if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
  DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  FILENAME="$(date -u +%Y-%m-%d)-auto-compact-handoff.yaml"
  cat > "$HANDOFF_DIR/$FILENAME" <<YAML
timestamp: "$DATE"
status: "mechanical"
type: mechanical-compact
trigger: pre-compact
session_summary: "Context compaction triggered. No transcript available for analysis."

files_modified: []
tool_call_count: 0
recent_tools: []

context_for_next_session: |
  This is an auto-generated mechanical handoff created before context compaction.
  The transcript was not accessible for detailed extraction.
YAML
  echo "$HANDOFF_DIR/$FILENAME" > "$STATE_DIR/last-compact-handoff"
  date +%s > "$STATE_DIR/last-auto-handoff-time"
  exit 0
fi

# Parse the JSONL transcript to extract session state
DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
FILENAME="$(date -u +%Y-%m-%d)-auto-compact-handoff.yaml"

python3 -c "
import json, sys, os
from collections import Counter

transcript_path = sys.argv[1]
files_modified = set()
tool_names = []
tool_count = 0

try:
    with open(transcript_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Look for tool use entries
            msg_type = entry.get('type', '')

            # Handle assistant messages with tool_use content blocks
            if msg_type == 'assistant':
                for block in entry.get('message', {}).get('content', []):
                    if block.get('type') == 'tool_use':
                        tool_count += 1
                        name = block.get('name', 'unknown')
                        tool_names.append(name)
                        inp = block.get('input', {})
                        # Extract file paths from common tool input fields
                        for key in ('file_path', 'path', 'filePath'):
                            fp = inp.get(key, '')
                            if fp and name in ('Write', 'Edit', 'NotebookEdit'):
                                files_modified.add(fp)

            # Handle tool_result entries that might contain file info
            if msg_type == 'tool_result':
                pass  # Results don't tell us what was modified

except Exception as e:
    print(f'# Error parsing transcript: {e}', file=sys.stderr)

# Build YAML output
files_yaml = ''
if files_modified:
    for fp in sorted(files_modified):
        files_yaml += f'  - \"{fp}\"\n'
else:
    files_yaml = '  []\n'

# Get recent tool names (last 20, deduplicated preserving order)
recent = []
seen = set()
for t in reversed(tool_names[-30:]):
    if t not in seen:
        seen.add(t)
        recent.append(t)
    if len(recent) >= 10:
        break
recent.reverse()
recent_yaml = ', '.join(recent) if recent else '[]'

# Tool frequency
freq = Counter(tool_names)
top_tools = freq.most_common(5)
top_yaml = ', '.join(f'{name}({count})' for name, count in top_tools) if top_tools else 'none'

# Estimate tokens from transcript size (~3 chars/token + 30k system overhead)
try:
    transcript_size = os.path.getsize(transcript_path)
    estimated_tokens = (transcript_size // 3) + 30000
except Exception:
    estimated_tokens = 0

yaml_out = f'''timestamp: \"$DATE\"
status: \"mechanical\"
type: mechanical-compact
trigger: pre-compact
session_summary: \"Auto-generated mechanical handoff before context compaction.\"
estimated_tokens: {estimated_tokens}

files_modified:
{files_yaml}
tool_call_count: {tool_count}
recent_tools: [{recent_yaml}]
tool_frequency: \"{top_yaml}\"

context_for_next_session: |
  This is a mechanical handoff auto-generated before context compaction.
  {tool_count} tool calls were made. {len(files_modified)} files were modified.
  Estimated context: ~{estimated_tokens} tokens at time of compaction.
  A semantic handoff (created by Claude via /acos-handoff-protocol) may also exist with
  richer context about decisions, blockers, and next actions.
'''

print(yaml_out)
" "$TRANSCRIPT_PATH" > "$HANDOFF_DIR/$FILENAME.tmp" 2>/dev/null
mv -f "$HANDOFF_DIR/$FILENAME.tmp" "$HANDOFF_DIR/$FILENAME"

# Write markers (atomic)
echo "$HANDOFF_DIR/$FILENAME" > "$STATE_DIR/last-compact-handoff.tmp"
mv -f "$STATE_DIR/last-compact-handoff.tmp" "$STATE_DIR/last-compact-handoff"
date +%s > "$STATE_DIR/last-auto-handoff-time.tmp"
mv -f "$STATE_DIR/last-auto-handoff-time.tmp" "$STATE_DIR/last-auto-handoff-time"

exit 0
