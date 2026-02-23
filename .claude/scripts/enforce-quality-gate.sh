#!/bin/bash
# TaskCompleted hook — validates evidence exists after task completion
#
# When a TodoWrite task is marked as completed, this hook checks whether
# the task appears to be an ACOS slice execution by looking for evidence
# in the expected locations. If evidence is missing for what looks like
# a slice task, it warns (but does not block — TaskCompleted cannot deny).
#
# This is a SOFT gate: it adds additionalContext warnings rather than
# blocking, because TaskCompleted hooks cannot prevent completion.
# The real hard gates are in the review process.
#
# Input: JSON with task details (subject, description, status)
# Output: Warning context if evidence appears missing

set -euo pipefail

STATE_DIR=".acos/state"
EVIDENCE_DIR=".acos/evidence"
mkdir -p "$STATE_DIR"

INPUT=$(cat)

# Extract task info
TASK_INFO=$(python3 -c "
import sys, json

try:
    data = json.load(sys.stdin)
    subject = data.get('subject', '')
    description = data.get('description', '')
    status = data.get('status', '')
    print(f'{status}|||{subject}|||{description}')
except Exception:
    print('|||||||')
" <<< "$INPUT" 2>/dev/null || echo "||||||")

IFS='|||' read -r TASK_STATUS _ TASK_SUBJECT _ TASK_DESC <<< "$TASK_INFO"

# Only check completed tasks
if [ "$TASK_STATUS" != "completed" ]; then
  exit 0
fi

# Detect if this looks like an ACOS slice task
# Slice tasks typically have slice IDs like "S-E1-ST1-SL1" in subject or description
IS_SLICE_TASK=false
if echo "$TASK_SUBJECT$TASK_DESC" | grep -qiE '(SL[0-9]|slice|execute.*slice|acos-execute-slice)'; then
  IS_SLICE_TASK=true
fi

# If not a slice task, nothing to check
if [ "$IS_SLICE_TASK" = "false" ]; then
  exit 0
fi

# ── Check for evidence ────────────────────────────────────────────────
# Look for today's evidence or current evidence directory
TODAY=$(date -u +%Y-%m-%d)
EVIDENCE_FOUND=false

if [ -d "$EVIDENCE_DIR/$TODAY" ]; then
  # Check if any evidence directories exist for today
  EVIDENCE_COUNT=$(find "$EVIDENCE_DIR/$TODAY" -name "Summary.md" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$EVIDENCE_COUNT" -gt 0 ]; then
    EVIDENCE_FOUND=true
  fi
fi

# Also check current evidence
if [ -d "$EVIDENCE_DIR/current" ]; then
  if [ -f "$EVIDENCE_DIR/current/modifications.log" ]; then
    EVIDENCE_FOUND=true
  fi
fi

if [ "$EVIDENCE_FOUND" = "false" ]; then
  # Warn about missing evidence
  echo "QUALITY GATE WARNING: Task '$TASK_SUBJECT' appears to be a slice execution but no evidence was found in $EVIDENCE_DIR/$TODAY/. Evidence bundles are required for review. If this is a false positive (not a slice task), ignore this warning." >&2
fi

exit 0
