#!/bin/bash
# Stop hook — safety net that triggers a semantic handoff before context exhaustion
# Uses Python-based token estimation on the JSONL transcript (not raw file size)
# Fires ONCE per session — the PreCompact hook is the guaranteed backup
# Exit 0 = allow stop, Exit 2 = block stop (stderr message shown to Claude)

STATE_DIR=".acos/state"
mkdir -p "$STATE_DIR"

# Read hook input from stdin
INPUT=$(cat)

# --- Loop prevention ---
# If stop_hook_active is true, this is a re-entry after we already blocked once.
# Claude has (hopefully) created the handoff. Let it stop.
STOP_HOOK_ACTIVE=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(str(data.get('stop_hook_active', False)).lower())
" 2>/dev/null)

if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
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

# --- Fire-once check ---
# Use session_id if available, otherwise fall back to transcript path hash
if [ -n "$SESSION_ID" ]; then
  MARKER_KEY="$SESSION_ID"
else
  MARKER_KEY=$(echo "$TRANSCRIPT_PATH" | md5 -q 2>/dev/null || echo "$TRANSCRIPT_PATH" | md5sum 2>/dev/null | cut -d' ' -f1)
fi

MARKER_FILE="$STATE_DIR/handoff-triggered-${MARKER_KEY}"

if [ -f "$MARKER_FILE" ]; then
  # Already fired this session — allow stop silently
  exit 0
fi

# --- Token estimation ---
# Parse the JSONL transcript, extract text content, estimate tokens at ~4 chars/token
# JSONL format: entries have type 'assistant' or 'user', with content in message.content[]
# User messages contain tool_result blocks (content can be string or list) and raw strings
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

            # Assistant messages: text blocks and tool_use inputs
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

            # User messages: text blocks, tool_result blocks, and raw strings
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

except Exception as e:
    print('0', file=sys.stdout)
    sys.exit(0)

# Estimate tokens at ~4 chars per token
estimated_tokens = total_chars // 4
print(estimated_tokens)
" "$TRANSCRIPT_PATH" 2>/dev/null)

# Default to 0 if estimation failed
if [ -z "$ESTIMATED_TOKENS" ]; then
  ESTIMATED_TOKENS=0
fi

# Threshold: 130,000 tokens (~65% of 200k context window)
# Compaction fires at 69% (~138k), so this gives ~8k tokens to create the handoff
TOKEN_THRESHOLD=130000

if [ "$ESTIMATED_TOKENS" -ge "$TOKEN_THRESHOLD" ]; then
  # Mark as fired for this session — will never fire again
  date +%s > "$MARKER_FILE"

  echo "Context usage is high (~${ESTIMATED_TOKENS} estimated tokens, threshold: ${TOKEN_THRESHOLD}). Please create a session handoff now using /acos-handoff to preserve session state before context compaction." >&2
  exit 2
fi

exit 0
