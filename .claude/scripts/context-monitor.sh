#!/bin/bash
# Stop hook — blocks Claude from stopping until a handoff exists
# Works with token-gate.sh (PreToolUse) as a two-layer defense:
#   Layer 1 (token-gate): proactively monitors every tool call, warns/blocks at thresholds
#   Layer 2 (this script): catches the stop event, ensures handoff exists before allowing exit
#
# Behavior:
#   - If stop_hook_active=true (second trigger): allow stop unconditionally
#   - If a handoff exists for today: allow stop
#   - If tokens < threshold: allow stop (normal low-usage session)
#   - If tokens >= threshold AND no handoff: block stop, write mechanical handoff, demand semantic one
#
# Output: JSON with decision/reason/additionalContext (not stderr like v1)
# Exit 0 always — uses JSON decision:"block" instead of exit 2

set -euo pipefail

STATE_DIR=".acos/state"
HANDOFF_DIR="memory/handoffs"
mkdir -p "$STATE_DIR" "$HANDOFF_DIR"

# Read hook input from stdin
INPUT=$(cat)

# --- Loop prevention ---
STOP_HOOK_ACTIVE=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(str(data.get('stop_hook_active', False)).lower())
" 2>/dev/null)

if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
  # Second trigger — allow stop. If token-gate wrote an emergency handoff, that's our safety net.
  exit 0
fi

# --- Extract transcript path and session ID ---
read -r TRANSCRIPT_PATH SESSION_ID <<< $(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
tp = data.get('transcript_path', '')
sid = data.get('session_id', '')
print(tp, sid)
" 2>/dev/null)

# If no transcript path available, can't measure — allow stop
if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
  exit 0
fi

# --- Check if handoff already exists for today ---
TODAY=$(date -u +%Y-%m-%d)
HANDOFF_EXISTS=false
for f in "$HANDOFF_DIR"/${TODAY}*.yaml "$HANDOFF_DIR"/${TODAY}*.yml; do
  if [ -f "$f" ]; then
    HANDOFF_EXISTS=true
    break
  fi
done

if [ "$HANDOFF_EXISTS" = "true" ]; then
  # Handoff exists — allow stop
  exit 0
fi

# --- Token estimation ---
ESTIMATED_TOKENS=$(python3 -c "
import json, sys

transcript_path = sys.argv[1]
total_chars = 0

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

            msg_type = entry.get('type', '')

            if msg_type == 'assistant':
                for block in entry.get('message', {}).get('content', []):
                    if not isinstance(block, dict):
                        continue
                    btype = block.get('type', '')
                    if btype == 'text':
                        total_chars += len(block.get('text', ''))
                    elif btype == 'tool_use':
                        inp = block.get('input', {})
                        total_chars += len(json.dumps(inp))

            elif msg_type == 'user':
                for block in entry.get('message', {}).get('content', []):
                    if isinstance(block, str):
                        total_chars += len(block)
                    elif isinstance(block, dict):
                        btype = block.get('type', '')
                        if btype == 'text':
                            total_chars += len(block.get('text', ''))
                        elif btype == 'tool_result':
                            content = block.get('content', '')
                            if isinstance(content, str):
                                total_chars += len(content)
                            elif isinstance(content, list):
                                for item in content:
                                    if isinstance(item, dict):
                                        total_chars += len(item.get('text', ''))
                                    elif isinstance(item, str):
                                        total_chars += len(item)

except Exception:
    print('0')
    sys.exit(0)

print(total_chars // 4)
" "$TRANSCRIPT_PATH" 2>/dev/null)

if [ -z "$ESTIMATED_TOKENS" ]; then
  ESTIMATED_TOKENS=0
fi

# Threshold: 110,000 tokens (~55% of 200k context window)
# Lower than before because token-gate.sh handles the 65%+ case proactively
TOKEN_THRESHOLD=110000

if [ "$ESTIMATED_TOKENS" -lt "$TOKEN_THRESHOLD" ]; then
  # Low usage session — allow stop normally
  exit 0
fi

# --- High usage session with no handoff: write mechanical + block stop ---

# Write a rich mechanical handoff as safety net
MECHANICAL_FILE="$HANDOFF_DIR/${TODAY}-mechanical-stop-handoff.yaml"

python3 -c "
import json, sys, os
from collections import Counter
from datetime import datetime, timezone

transcript_path = sys.argv[1]
session_id = sys.argv[2]
estimated_tokens = sys.argv[3]
output_file = sys.argv[4]

files_modified = set()
files_read = set()
tool_names = []
tool_count = 0
last_texts = []
skill_invocations = []

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

            msg_type = entry.get('type', '')

            if msg_type == 'assistant':
                for block in entry.get('message', {}).get('content', []):
                    if not isinstance(block, dict):
                        continue
                    btype = block.get('type', '')
                    if btype == 'text':
                        text = block.get('text', '')
                        if len(text) > 30:
                            last_texts.append(text[:300])
                            if len(last_texts) > 15:
                                last_texts.pop(0)
                    elif btype == 'tool_use':
                        tool_count += 1
                        name = block.get('name', 'unknown')
                        tool_names.append(name)
                        inp = block.get('input', {})

                        # Track file modifications
                        for key in ('file_path', 'path', 'filePath'):
                            fp = inp.get(key, '')
                            if fp:
                                if name in ('Write', 'Edit', 'NotebookEdit'):
                                    files_modified.add(fp)
                                elif name == 'Read':
                                    files_read.add(fp)

                        # Track skill invocations
                        if name == 'Skill':
                            skill_invocations.append(inp.get('skill', 'unknown'))

                        # Track Task agent descriptions
                        if name == 'Task':
                            desc = inp.get('description', '')
                            if desc:
                                last_texts.append(f'[Agent: {desc}]')

except Exception:
    pass

# Build YAML
now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

files_mod_yaml = '\\n'.join(f'  - \"{fp}\"' for fp in sorted(files_modified)) if files_modified else '  []'
files_read_yaml = '\\n'.join(f'  - \"{fp}\"' for fp in sorted(files_read)[:20]) if files_read else '  []'

freq = Counter(tool_names)
top_tools = ', '.join(f'{n}({c})' for n, c in freq.most_common(8))
skills_yaml = ', '.join(skill_invocations) if skill_invocations else 'none'

# Extract last 8 meaningful assistant texts as context breadcrumbs
breadcrumbs = []
for t in last_texts[-8:]:
    clean = t.replace('\"', \"'\").replace('\\n', ' ')[:200]
    breadcrumbs.append(f'  - \"{clean}\"')
breadcrumbs_yaml = '\\n'.join(breadcrumbs) if breadcrumbs else '  - \"No context captured\"'

yaml = f'''timestamp: \"{now}\"
status: \"active\"
type: mechanical-stop
trigger: context-monitor-stop-hook
session_id: \"{session_id}\"
estimated_tokens: {estimated_tokens}
session_summary: >
  Mechanical handoff created by Stop hook. Session had {tool_count} tool calls
  and modified {len(files_modified)} files. Context was at {estimated_tokens} tokens
  when Claude attempted to stop without creating a semantic handoff.

files_modified:
{files_mod_yaml}

files_read_recently:
{files_read_yaml}

tool_call_count: {tool_count}
tool_frequency: \"{top_tools}\"
skills_used: \"{skills_yaml}\"

session_breadcrumbs:
{breadcrumbs_yaml}

next_actions:
  - \"Review files_modified list above to understand what changed\"
  - \"Check .acos/evidence/ for any evidence summaries from completed slices\"
  - \"Check .acos/evidence/current/modifications.log for timestamped file changes\"
  - \"If ACOS was running, check project.yaml for current epic/story/slice state\"
  - \"Consider running /acos-status to see overall project state\"

context_for_next_session: |
  MECHANICAL HANDOFF: The previous session ended at {estimated_tokens} tokens without
  creating a proper semantic handoff. This mechanical extraction was created by the
  Stop hook as a safety net. It contains file lists and context breadcrumbs but lacks
  the detailed decisions, blockers, and next-action analysis that /acos-handoff-protocol provides.

  Review the breadcrumbs and modified files to reconstruct session context.
  The auto-load-handoff.sh SessionStart hook will inject this into your next session.
'''

with open(output_file, 'w') as f:
    f.write(yaml)

" "$TRANSCRIPT_PATH" "${SESSION_ID:-unknown}" "$ESTIMATED_TOKENS" "$MECHANICAL_FILE" 2>/dev/null

# Mark as fired
date +%s > "$STATE_DIR/handoff-triggered-${SESSION_ID:-$(echo "$TRANSCRIPT_PATH" | md5 -q 2>/dev/null || echo "$TRANSCRIPT_PATH" | md5sum 2>/dev/null | cut -d' ' -f1)}"

# Block stop with structured JSON — demand semantic handoff
cat <<EOF
{
  "decision": "block",
  "reason": "Context at ${ESTIMATED_TOKENS} tokens with no handoff. A mechanical handoff was saved to ${MECHANICAL_FILE}. Please create a proper semantic handoff using /acos-handoff-protocol (or /acos-continue) for richer context preservation.",
  "additionalContext": "IMPORTANT: You are about to stop but no session handoff exists. A mechanical handoff has been auto-saved to ${MECHANICAL_FILE}, but it lacks decisions, blockers, and detailed next-actions. Please invoke /acos-handoff-protocol NOW to create a semantic handoff (or /acos-continue to handoff and auto-start a new session), then you may stop. If you cannot create one (context too low), the mechanical handoff will serve as the safety net."
}
EOF

exit 0
