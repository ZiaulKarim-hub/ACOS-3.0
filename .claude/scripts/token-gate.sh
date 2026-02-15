#!/bin/bash
# PreToolUse hook — continuous token monitor that gates tool execution
# Runs on EVERY tool call to enforce context budget
#
# Thresholds (% of 200k context window):
#   < 55%  → silent pass-through
#   55-64% → allow tool, inject warning via additionalContext
#   65-69% → block non-handoff tools, demand /acos-handoff-protocol
#   70%+   → block ALL tools, write emergency mechanical handoff in bash
#
# Performance: uses a 30-second cache to avoid re-parsing transcript on rapid tool calls
# Exit 0 = allow (with optional JSON), Exit 2 = block (stderr feedback)

set -euo pipefail

STATE_DIR=".acos/state"
HANDOFF_DIR="memory/handoffs"
CACHE_FILE="$STATE_DIR/.token-gate-cache"
CACHE_TTL=30  # seconds

mkdir -p "$STATE_DIR" "$HANDOFF_DIR"

# Read hook input from stdin
INPUT=$(cat)

# Extract tool name, transcript path, and session ID
read -r TOOL_NAME TRANSCRIPT_PATH SESSION_ID <<< $(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
tool = data.get('tool_name', '')
tp = data.get('transcript_path', '')
sid = data.get('session_id', '')
print(tool, tp, sid)
" 2>/dev/null)

# If no transcript, can't measure — allow silently
if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
  exit 0
fi

# --- Performance: use cached token count if fresh enough ---
ESTIMATED_TOKENS=0
USE_CACHE=false

if [ -f "$CACHE_FILE" ]; then
  CACHE_AGE=$(( $(date +%s) - $(stat -f %m "$CACHE_FILE" 2>/dev/null || echo 0) ))
  if [ "$CACHE_AGE" -lt "$CACHE_TTL" ]; then
    ESTIMATED_TOKENS=$(cat "$CACHE_FILE" 2>/dev/null || echo 0)
    USE_CACHE=true
  fi
fi

if [ "$USE_CACHE" = "false" ]; then
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

  # Cache the result
  echo "$ESTIMATED_TOKENS" > "$CACHE_FILE"
fi

# --- Thresholds ---
CONTEXT_WINDOW=200000
WARN_THRESHOLD=$(( CONTEXT_WINDOW * 55 / 100 ))     # 110,000
BLOCK_THRESHOLD=$(( CONTEXT_WINDOW * 65 / 100 ))     # 130,000
EMERGENCY_THRESHOLD=$(( CONTEXT_WINDOW * 70 / 100 )) # 140,000

# Check if a handoff from THIS session already exists.
# Only bypass the gate if the handoff was created by the current session.
# Previous sessions' handoffs must NOT suppress the gate for new sessions.
TODAY=$(date -u +%Y-%m-%d)
THIS_SESSION_HANDOFF=false
if [ -n "$SESSION_ID" ] && [ "$SESSION_ID" != "" ]; then
  for f in "$HANDOFF_DIR"/${TODAY}*.yaml "$HANDOFF_DIR"/${TODAY}*.yml; do
    if [ -f "$f" ]; then
      # Extract session_id from the handoff YAML and compare.
      # Uses grep+sed for robustness — avoids bash/python quote-escaping issues.
      HANDOFF_SID=$(grep -m1 '^session_id:' "$f" 2>/dev/null | sed 's/^session_id:[[:space:]]*//; s/^"//; s/"[[:space:]]*$//' || true)
      if [ "$HANDOFF_SID" = "$SESSION_ID" ]; then
        THIS_SESSION_HANDOFF=true
        break
      fi
    fi
  done
fi

# If THIS session already created a handoff, allow everything — mission accomplished
if [ "$THIS_SESSION_HANDOFF" = "true" ]; then
  exit 0
fi

# --- Below warning threshold: silent pass ---
if [ "$ESTIMATED_TOKENS" -lt "$WARN_THRESHOLD" ]; then
  exit 0
fi

# --- Tools allowed during handoff creation ---
# These tools are needed for /acos-handoff-protocol skill to work
HANDOFF_TOOLS="Read|Write|Edit|Glob|Grep|Skill|LSP"

is_handoff_tool() {
  echo "$TOOL_NAME" | grep -qE "^($HANDOFF_TOOLS)$"
}

# --- EMERGENCY: 70%+ — block everything, write mechanical handoff ---
if [ "$ESTIMATED_TOKENS" -ge "$EMERGENCY_THRESHOLD" ]; then
  # Write emergency mechanical handoff directly
  EMERGENCY_FILE="$HANDOFF_DIR/${TODAY}-emergency-handoff.yaml"
  if [ ! -f "$EMERGENCY_FILE" ]; then
    python3 -c "
import json, sys, os
from collections import Counter
from datetime import datetime, timezone

transcript_path = sys.argv[1]
session_id = sys.argv[2]
files_modified = set()
tool_names = []
tool_count = 0
last_texts = []

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
                        if len(text) > 20:
                            last_texts.append(text[:200])
                            if len(last_texts) > 10:
                                last_texts.pop(0)
                    elif btype == 'tool_use':
                        tool_count += 1
                        name = block.get('name', 'unknown')
                        tool_names.append(name)
                        inp = block.get('input', {})
                        for key in ('file_path', 'path', 'filePath'):
                            fp = inp.get(key, '')
                            if fp and name in ('Write', 'Edit', 'NotebookEdit'):
                                files_modified.add(fp)

except Exception as e:
    pass

# Build YAML
now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
files_yaml = '\\n'.join(f'  - \"{fp}\"' for fp in sorted(files_modified)) if files_modified else '  []'
freq = Counter(tool_names)
top_tools = ', '.join(f'{n}({c})' for n, c in freq.most_common(8))

# Recent context from last assistant messages
recent_context = '\\n'.join(f'  - \"{t[:150]}...\"' for t in last_texts[-5:]) if last_texts else '  - \"No context captured\"'

yaml = f'''timestamp: \"{now}\"
status: \"active\"
type: emergency-mechanical
trigger: token-gate-emergency
session_id: \"{session_id}\"
session_summary: \"Emergency mechanical handoff — context window hit 70% ({sys.argv[3]} tokens). Session forcibly interrupted.\"

files_modified:
{files_yaml}

tool_call_count: {tool_count}
tool_frequency: \"{top_tools}\"

recent_assistant_context:
{recent_context}

context_for_next_session: |
  EMERGENCY HANDOFF: The previous session was forcibly interrupted at 70% context usage.
  {tool_count} tool calls were made. {len(files_modified)} files were modified.
  This is a mechanical extraction — a semantic handoff (/acos-handoff-protocol) was not created.
  Review the modified files and .acos/evidence/ directory for detailed session state.
  Check .acos/evidence/current/modifications.log for the full file modification timeline.
'''

with open(sys.argv[4], 'w') as f:
    f.write(yaml)

print('Emergency handoff written to ' + sys.argv[4], file=sys.stderr)
" "$TRANSCRIPT_PATH" "${SESSION_ID:-unknown}" "$ESTIMATED_TOKENS" "$EMERGENCY_FILE" 2>/dev/null
  fi

  # Block the tool
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Context at ${ESTIMATED_TOKENS} tokens (70%+ of 200k). Emergency handoff written to ${EMERGENCY_FILE}. Session should end now.",
    "additionalContext": "CRITICAL: Context window is at ${ESTIMATED_TOKENS} tokens (70%+). An emergency mechanical handoff has been written to ${EMERGENCY_FILE}. You MUST stop working immediately. Do NOT attempt any more tool calls. Inform the user that the session must end and a new session should be started."
  }
}
EOF
  exit 0
fi

# --- BLOCK: 65-69% — only allow handoff tools ---
if [ "$ESTIMATED_TOKENS" -ge "$BLOCK_THRESHOLD" ]; then
  if is_handoff_tool; then
    # Allow handoff-related tools with urgent context
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "additionalContext": "URGENT: Context at ${ESTIMATED_TOKENS}/${CONTEXT_WINDOW} tokens (65%+). You are in HANDOFF MODE — only handoff-related tools are allowed. Complete the handoff document NOW using /acos-handoff-protocol (or /acos-continue to auto-start a new session), then stop."
  }
}
EOF
    exit 0
  else
    # Block non-handoff tools
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Context at ${ESTIMATED_TOKENS} tokens (65%+). Only handoff tools (Read, Write, Edit, Glob, Grep, Skill) are allowed. Create handoff first.",
    "additionalContext": "MANDATORY: Context window is at ${ESTIMATED_TOKENS} tokens (65%+ of ${CONTEXT_WINDOW}). You MUST create a session handoff NOW using /acos-handoff-protocol (or /acos-continue to auto-start a new session) before context is exhausted. All non-handoff tools are blocked. Only Read, Write, Edit, Glob, Grep, and Skill tools are permitted until the handoff is complete."
  }
}
EOF
    exit 0
  fi
fi

# --- WARN: 55-64% — allow tool but inject warning ---
if [ "$ESTIMATED_TOKENS" -ge "$WARN_THRESHOLD" ]; then
  PCT=$(( ESTIMATED_TOKENS * 100 / CONTEXT_WINDOW ))
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "additionalContext": "Context usage: ${ESTIMATED_TOKENS}/${CONTEXT_WINDOW} tokens (~${PCT}%). Begin wrapping up your current work unit. After completing the current slice, create a session handoff using /acos-handoff-protocol or /acos-continue before starting new work."
  }
}
EOF
  exit 0
fi

# Should not reach here, but allow just in case
exit 0
