#!/bin/bash
# Stop hook — blocks Claude from stopping until a handoff exists
#
# Works with token-gate.sh (PreToolUse) as a two-layer defense:
#   Layer 1 (token-gate): proactively monitors every tool call, warns/blocks at thresholds
#   Layer 2 (this script): catches the stop event, ensures handoff exists before allowing exit
#
# Behavior:
#   - If stop_hook_active=true (second trigger): allow stop unconditionally
#   - If a handoff exists for this session: allow stop
#   - If tokens < threshold: allow stop (normal low-usage session)
#   - If tokens >= threshold AND no handoff: block stop, write mechanical, demand semantic
#
# BLOCKING MECHANISM: Uses BOTH exit 2 AND JSON decision:block for maximum
# compatibility. Exit 2 is the standard Claude Code hook denial mechanism.
# The JSON output provides context to the agent about what happened.
#
# RETRY TRACKING: Tracks stop attempts in state file. Each blocked stop
# increments the counter. After MAX_STOP_RETRIES, allows stop but ensures
# at least a mechanical handoff exists.

set -euo pipefail

STATE_DIR=".acos/state"
HANDOFF_DIR="memory/handoffs"
STOP_RETRY_FILE="$STATE_DIR/.stop-retry-count"
MAX_STOP_RETRIES=3

mkdir -p "$STATE_DIR" "$HANDOFF_DIR"

# Read hook input from stdin
INPUT=$(cat)

# ── Loop Prevention ────────────────────────────────────────────────────
STOP_HOOK_ACTIVE=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(str(data.get('stop_hook_active', False)).lower())
" 2>/dev/null || echo "false")

if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
  # Second trigger — allow stop unconditionally
  rm -f "$STOP_RETRY_FILE"
  exit 0
fi

# ── Extract transcript path and session ID ─────────────────────────────
read -r TRANSCRIPT_PATH SESSION_ID <<< $(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
tp = data.get('transcript_path', '')
sid = data.get('session_id', '')
print(tp, sid)
" 2>/dev/null || echo "")

# If no transcript path available, can't measure — allow stop
if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
  exit 0
fi

# ── Check if a FRESH handoff exists for this session ───────────────────
# Staleness-aware: if tokens grew >20k since the handoff was created,
# it's stale and doesn't count. Matches token-gate.sh logic.
HANDOFF_STALE_DELTA=20000
HANDOFF_EXISTS=false
HANDOFF_TOKENS_AT_CREATION=0

if [ -n "$SESSION_ID" ] && [ "$SESSION_ID" != "" ]; then
  NEWEST_HANDOFF=""
  NEWEST_MTIME=0
  for f in "$HANDOFF_DIR"/*.yaml "$HANDOFF_DIR"/*.yml; do
    if [ -f "$f" ]; then
      HANDOFF_SID=$(grep -m1 '^session_id:' "$f" 2>/dev/null | sed 's/^session_id:[[:space:]]*//; s/^"//; s/"[[:space:]]*$//' || true)
      if [ "$HANDOFF_SID" = "$SESSION_ID" ]; then
        HANDOFF_EXISTS=true
        FILE_MTIME=$(stat -f %m "$f" 2>/dev/null || stat -c %Y "$f" 2>/dev/null || echo 0)
        if [ "$FILE_MTIME" -gt "$NEWEST_MTIME" ]; then
          NEWEST_MTIME=$FILE_MTIME
          NEWEST_HANDOFF="$f"
        fi
      fi
    fi
  done

  # Check staleness
  if [ "$HANDOFF_EXISTS" = "true" ] && [ -n "$NEWEST_HANDOFF" ]; then
    HANDOFF_TOKENS_AT_CREATION=$(grep -m1 '^estimated_tokens:' "$NEWEST_HANDOFF" 2>/dev/null | sed 's/^estimated_tokens:[[:space:]]*//' | tr -d '"' || echo 0)
    if [ -z "$HANDOFF_TOKENS_AT_CREATION" ] || ! [[ "$HANDOFF_TOKENS_AT_CREATION" =~ ^[0-9]+$ ]]; then
      HANDOFF_TOKENS_AT_CREATION=0
    fi
  fi
fi

# Also check by date (fallback for handoffs without session_id)
if [ "$HANDOFF_EXISTS" = "false" ]; then
  TODAY=$(date -u +%Y-%m-%d)
  for f in "$HANDOFF_DIR"/${TODAY}*.yaml "$HANDOFF_DIR"/${TODAY}*.yml; do
    if [ -f "$f" ]; then
      HANDOFF_EXISTS=true
      break
    fi
  done
fi

if [ "$HANDOFF_EXISTS" = "true" ]; then
  # Check freshness — if we have token data, compare
  if [ "$HANDOFF_TOKENS_AT_CREATION" -gt 0 ] && [ "$ESTIMATED_TOKENS" -gt 0 ]; then
    TOKEN_DELTA=$(( ESTIMATED_TOKENS - HANDOFF_TOKENS_AT_CREATION ))
    if [ "$TOKEN_DELTA" -ge "$HANDOFF_STALE_DELTA" ]; then
      # Handoff is stale — proceed as if no handoff exists
      echo "STOP HOOK: Handoff stale — created at ~${HANDOFF_TOKENS_AT_CREATION}, now ~${ESTIMATED_TOKENS} (delta: ${TOKEN_DELTA})" >&2
      HANDOFF_EXISTS=false
    fi
  fi

  if [ "$HANDOFF_EXISTS" = "true" ]; then
    # Fresh handoff exists — allow stop, clean up retry counter
    rm -f "$STOP_RETRY_FILE"
    exit 0
  fi
fi

# ── Token Estimation ───────────────────────────────────────────────────
# Use cached value from token-gate if fresh, otherwise re-estimate
ESTIMATED_TOKENS=0
CACHE_FILE="$STATE_DIR/.token-gate-cache"

if [ -f "$CACHE_FILE" ]; then
  CACHE_AGE=$(( $(date +%s) - $(stat -f %m "$CACHE_FILE" 2>/dev/null || stat -c %Y "$CACHE_FILE" 2>/dev/null || echo 0) ))
  if [ "$CACHE_AGE" -lt 60 ]; then
    ESTIMATED_TOKENS=$(cat "$CACHE_FILE" 2>/dev/null || echo 0)
  fi
fi

# If no cached value, estimate from transcript
if [ "$ESTIMATED_TOKENS" -eq 0 ]; then
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
" "$TRANSCRIPT_PATH" 2>/dev/null || echo 0)
fi

if [ -z "$ESTIMATED_TOKENS" ]; then
  ESTIMATED_TOKENS=0
fi

# Threshold: 100,000 tokens (~50% of 200k context window)
# Aligned with token-gate.sh WARN_PCT=50 (lowered Feb 2026)
TOKEN_THRESHOLD=100000

if [ "$ESTIMATED_TOKENS" -lt "$TOKEN_THRESHOLD" ]; then
  # Low usage session — allow stop normally
  rm -f "$STOP_RETRY_FILE"
  exit 0
fi

# ── High usage session with no handoff ─────────────────────────────────
# Track stop retry count
STOP_RETRIES=$(cat "$STOP_RETRY_FILE" 2>/dev/null || echo 0)
STOP_RETRIES=$((STOP_RETRIES + 1))
echo "$STOP_RETRIES" > "$STOP_RETRY_FILE"

# Write mechanical handoff as safety net
TODAY=$(date -u +%Y-%m-%d)
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

                        for key in ('file_path', 'path', 'filePath'):
                            fp = inp.get(key, '')
                            if fp:
                                if name in ('Write', 'Edit', 'NotebookEdit'):
                                    files_modified.add(fp)
                                elif name == 'Read':
                                    files_read.add(fp)

                        if name == 'Skill':
                            skill_invocations.append(inp.get('skill', 'unknown'))

except Exception:
    pass

now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

files_mod_yaml = chr(10).join(f'  - \"{fp}\"' for fp in sorted(files_modified)) if files_modified else '  []'
files_read_yaml = chr(10).join(f'  - \"{fp}\"' for fp in sorted(files_read)[:20]) if files_read else '  []'

freq = Counter(tool_names)
top_tools = ', '.join(f'{n}({c})' for n, c in freq.most_common(8))
skills_yaml = ', '.join(skill_invocations) if skill_invocations else 'none'

breadcrumbs = []
for t in last_texts[-8:]:
    clean = t.replace('\"', \"'\").replace(chr(10), ' ')[:200]
    breadcrumbs.append(f'  - \"{clean}\"')
breadcrumbs_yaml = chr(10).join(breadcrumbs) if breadcrumbs else '  - \"No context captured\"'

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

# Mark stop hook as fired
date +%s > "$STATE_DIR/handoff-triggered-${SESSION_ID:-unknown}"

# ── Decide: block or allow after max retries ───────────────────────────
if [ "$STOP_RETRIES" -ge "$MAX_STOP_RETRIES" ]; then
  # After MAX_STOP_RETRIES, allow the stop — we have a mechanical handoff at least
  echo "STOP HOOK: Allowing stop after ${STOP_RETRIES} blocked attempts. Mechanical handoff at ${MECHANICAL_FILE}." >&2
  rm -f "$STOP_RETRY_FILE"
  # Output context but allow (exit 0)
  cat <<EOF
{
  "decision": "allow",
  "reason": "Allowing stop after ${STOP_RETRIES} blocked attempts. Mechanical handoff saved to ${MECHANICAL_FILE}.",
  "additionalContext": "Stop was blocked ${STOP_RETRIES} times requesting /acos-handoff-protocol. A mechanical handoff has been saved as a fallback. The session is ending now."
}
EOF
  exit 0
fi

# ── Block the stop — demand semantic handoff ───────────────────────────
REMAINING=$((MAX_STOP_RETRIES - STOP_RETRIES))

echo "STOP HOOK: Blocking stop attempt ${STOP_RETRIES}/${MAX_STOP_RETRIES}. No handoff exists. Mechanical saved to ${MECHANICAL_FILE}." >&2

# Output context for the agent
cat <<EOF
{
  "decision": "block",
  "reason": "Stop blocked [${STOP_RETRIES}/${MAX_STOP_RETRIES}]: Context at ${ESTIMATED_TOKENS} tokens with no handoff. Mechanical handoff saved to ${MECHANICAL_FILE}. Run /acos-handoff-protocol for a proper semantic handoff.",
  "additionalContext": "STOP BLOCKED [${STOP_RETRIES}/${MAX_STOP_RETRIES}]: You tried to stop but no session handoff exists. A mechanical handoff was auto-saved to ${MECHANICAL_FILE}, but it lacks decisions, blockers, and next-actions. Run /acos-handoff-protocol NOW to create a semantic handoff (or /acos-continue to handoff + auto-restart). After ${REMAINING} more stop attempt(s), stop will be FORCED with only the mechanical handoff."
}
EOF

# EXIT 2 = BLOCK the stop (Claude Code hook convention)
exit 2
