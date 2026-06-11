#!/bin/bash
# PreToolUse hook — Token monitor with handoff enforcement loop
#
# PURPOSE: Monitors context window usage and enforces handoff creation
# before context exhaustion. Implements a persistent retry loop that
# escalates urgency until the handoff protocol actually executes.
#
# ARCHITECTURE:
#   This hook fires on EVERY tool call. It operates in two modes:
#   1. MONITORING — estimates context usage from transcript (below threshold)
#   2. ENFORCEMENT — retry loop demanding handoff with escalating urgency
#
# ENFORCEMENT PHASES (by retry count since threshold crossed):
#   Phase 1 NUDGE   (retries 1-3):   allow all tools, gentle warning
#   Phase 2 PRESS   (retries 4-8):   block non-handoff tools, urgent demand
#   Phase 3 FORCE   (retries 9-14):  block non-handoff tools, final warnings
#   Phase 4 FALLBACK (retries 15+):  auto-create mechanical handoff
#
# STALENESS-AWARE HANDOFF DETECTION:
#   If a handoff already exists but tokens grew >20k since it was created,
#   the handoff is considered stale. Enforcement re-activates to demand
#   a fresh handoff. This prevents the "one handoff satisfies forever" bug.
#
# THRESHOLDS (lowered Feb 2026 — user requirement: hard ceiling at 130k):
#   WARN:      50% (100k tokens) — enforcement begins
#   BLOCK:     60% (120k tokens) — non-handoff tools blocked
#   EMERGENCY: 65% (130k tokens) — hard ceiling, auto-fallback imminent
#
# HEALTH CHECK: On first enforcement activation, verifies all hook scripts
# are executable and properly configured. Also available via --health-check.
#
# STATE FILES:
#   .acos/state/.token-gate-cache        — cached token count (30s TTL)
#   .acos/state/.handoff-enforcement     — enforcement state (retries, etc.)
#
# Exit 0 always — uses hookSpecificOutput permissionDecision for deny/allow

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────
STATE_DIR=".acos/state"
HANDOFF_DIR="memory/handoffs"
CACHE_FILE="$STATE_DIR/.token-gate-cache"
ENFORCEMENT_FILE="$STATE_DIR/.handoff-enforcement"
CACHE_TTL=30  # seconds

# System context overhead: system prompt (tool definitions, agent descriptions),
# CLAUDE.md, MEMORY.md, auto-loaded handoffs, skill definitions, and system
# reminders injected mid-conversation. These tokens are NOT in the JSONL
# transcript but consume context window.
# Calibrated Feb 2026: 25k was undercounting by ~5k for ACOS projects.
SYSTEM_OVERHEAD=30000

# Characters per token ratio for estimation.
# Calibrated Feb 2026: started at 4.0 (way too high), tried 2.5 (overcounted),
# settled on 3.0 as a balanced middle ground for mixed code/text/JSON content.
CHARS_PER_TOKEN=3

CONTEXT_WINDOW=200000
WARN_PCT=50
BLOCK_PCT=60
EMERGENCY_PCT=65
WARN_THRESHOLD=$(( CONTEXT_WINDOW * WARN_PCT / 100 ))      # 100,000
BLOCK_THRESHOLD=$(( CONTEXT_WINDOW * BLOCK_PCT / 100 ))     # 120,000
EMERGENCY_THRESHOLD=$(( CONTEXT_WINDOW * EMERGENCY_PCT / 100 )) # 130,000

# Handoff staleness: if tokens grew by this much since the last handoff,
# the handoff is considered stale and enforcement re-activates
HANDOFF_STALE_DELTA=20000

# mtime-based freshness window (seconds) for handoffs that do NOT carry an
# `estimated_tokens:` field. The semantic handoff protocol (/acos-handoff-protocol)
# omits that field, so we can't compute a token delta. A same-session handoff
# whose file was written within this window is treated as fresh rather than
# stale-from-birth. Generous so a just-created handoff always counts.
HANDOFF_MTIME_FRESH_SECS=1800

# Enforcement phase boundaries (retry counts)
NUDGE_MAX=3
PRESS_MAX=8
FORCE_MAX=14
# After FORCE_MAX → auto-fallback

# Tools allowed during handoff enforcement
HANDOFF_TOOLS="Read|Write|Edit|Glob|Grep|Skill|LSP"

mkdir -p "$STATE_DIR" "$HANDOFF_DIR"

# ── Utility Functions ──────────────────────────────────────────────────

get_mtime() {
  stat -f %m "$1" 2>/dev/null || stat -c %Y "$1" 2>/dev/null || echo 0
}

is_handoff_tool() {
  echo "$1" | grep -qE "^($HANDOFF_TOOLS)$"
}

# Emit allow with optional additionalContext
emit_allow() {
  local ctx="${1:-}"
  if [ -n "$ctx" ]; then
    # Escape special characters for JSON
    ctx=$(echo "$ctx" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip())[1:-1])" 2>/dev/null || echo "$ctx")
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "additionalContext": "$ctx"
  }
}
EOF
  fi
  exit 0
}

# Emit deny with reason and additionalContext
emit_deny() {
  local reason="$1"
  local ctx="$2"
  reason=$(echo "$reason" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip())[1:-1])" 2>/dev/null || echo "$reason")
  ctx=$(echo "$ctx" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip())[1:-1])" 2>/dev/null || echo "$ctx")
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "$reason",
    "additionalContext": "$ctx"
  }
}
EOF
  exit 0
}

# Read enforcement state (returns JSON)
get_enforcement() {
  if [ -f "$ENFORCEMENT_FILE" ]; then
    cat "$ENFORCEMENT_FILE"
  else
    echo '{"retries":0,"active":false}'
  fi
}

# Write enforcement state
set_enforcement() {
  local retries="$1"
  local active="$2"
  local tokens="${3:-0}"
  # Atomic write: tmp file + mv prevents partial reads from concurrent hooks
  local tmpfile="${ENFORCEMENT_FILE}.tmp.$$"
  echo "{\"retries\":$retries,\"active\":$active,\"tokens\":$tokens,\"updated\":$(date +%s)}" > "$tmpfile"
  mv -f "$tmpfile" "$ENFORCEMENT_FILE"
}

# Reset enforcement (handoff found or auto-fallback completed)
reset_enforcement() {
  rm -f "$ENFORCEMENT_FILE"
}

# ── Health Check Mode ──────────────────────────────────────────────────
# Run with: bash .claude/scripts/token-gate.sh --health-check

run_health_check() {
  local errors=0
  local warnings=0

  echo "=== ACOS Handoff Hook Health Check ==="
  echo ""

  # Check all hook scripts
  echo "--- Hook Scripts ---"
  declare -a SCRIPTS=(
    ".claude/scripts/token-gate.sh:PreToolUse:required"
    ".claude/scripts/oracle-evaluate.py:PreToolUse:required"
    ".claude/scripts/check-scope.sh:PreToolUse:required"
    ".claude/scripts/context-monitor.sh:Stop:required"
    ".claude/scripts/context-watchdog.sh:PreCompact:required"
    ".claude/scripts/post-write-evidence.sh:PostToolUse:optional"
    ".claude/scripts/log-agent-completion.sh:SubagentStop:optional"
    ".claude/scripts/inject-agent-context.sh:SubagentStart:required"
    ".claude/scripts/log-agent-spawn.sh:SubagentStart:optional"
    ".claude/scripts/enforce-quality-gate.sh:TaskCompleted:optional"
    ".claude/scripts/session-cleanup.sh:SessionEnd:optional"
  )

  for entry in "${SCRIPTS[@]}"; do
    IFS=':' read -r script hook importance <<< "$entry"
    if [ ! -f "$script" ]; then
      if [ "$importance" = "required" ]; then
        echo "  FAIL:  $script — MISSING ($hook hook)"
        errors=$((errors + 1))
      else
        echo "  WARN:  $script — missing ($hook hook, optional)"
        warnings=$((warnings + 1))
      fi
    elif [ ! -x "$script" ] && [[ "$script" == *.sh ]]; then
      echo "  FAIL:  $script — not executable ($hook hook)"
      errors=$((errors + 1))
    else
      echo "  OK:    $script ($hook)"
    fi
  done

  # Check settings.local.json
  echo ""
  echo "--- Configuration ---"
  if [ -f ".claude/settings.local.json" ]; then
    local hook_info
    hook_info=$(python3 -c "
import json
with open('.claude/settings.local.json') as f:
    d = json.load(f)
hooks = d.get('hooks', {})
for name, entries in hooks.items():
    print(f'  {name}: {len(entries)} hook(s)')
" 2>/dev/null || echo "  ERROR: Could not parse settings.local.json")
    echo "$hook_info"

    # Verify critical hooks are present
    for required_hook in "PreToolUse" "Stop" "PreCompact" "SessionStart"; do
      if ! python3 -c "
import json, sys
with open('.claude/settings.local.json') as f:
    d = json.load(f)
if '$required_hook' not in d.get('hooks', {}):
    sys.exit(1)
" 2>/dev/null; then
        echo "  FAIL:  Missing '$required_hook' hook section in settings.local.json"
        errors=$((errors + 1))
      fi
    done
  else
    echo "  FAIL:  .claude/settings.local.json — MISSING"
    errors=$((errors + 1))
  fi

  # Check state files
  echo ""
  echo "--- Enforcement State ---"
  if [ -f "$ENFORCEMENT_FILE" ]; then
    local retries
    retries=$(python3 -c "import json; print(json.load(open('$ENFORCEMENT_FILE')).get('retries',0))" 2>/dev/null || echo "?")
    echo "  Enforcement: ACTIVE (retries: $retries)"
  else
    echo "  Enforcement: INACTIVE"
  fi

  if [ -f "$CACHE_FILE" ]; then
    local cached_tokens
    cached_tokens=$(cat "$CACHE_FILE" 2>/dev/null || echo "?")
    local cache_age=$(( $(date +%s) - $(get_mtime "$CACHE_FILE") ))
    echo "  Token cache: $cached_tokens tokens (age: ${cache_age}s)"
  else
    echo "  Token cache: EMPTY"
  fi

  # Check handoff directory
  echo ""
  echo "--- Handoff Files ---"
  local active_count=0
  local mechanical_count=0
  for f in "$HANDOFF_DIR"/*.yaml "$HANDOFF_DIR"/*.yml; do
    if [ -f "$f" ]; then
      local status
      status=$(grep -m1 '^status:' "$f" 2>/dev/null | sed 's/^status:[[:space:]]*//; s/^"//; s/".*$//' || echo "unknown")
      local basename
      basename=$(basename "$f")
      echo "  $basename (status: $status)"
      case "$status" in
        active) active_count=$((active_count + 1)) ;;
        mechanical*) mechanical_count=$((mechanical_count + 1)) ;;
      esac
    fi
  done
  if [ "$active_count" -eq 0 ] && [ "$mechanical_count" -eq 0 ]; then
    echo "  (no active handoffs)"
  fi

  # Summary
  echo ""
  echo "=== Summary ==="
  if [ "$errors" -eq 0 ]; then
    echo "  PASSED — all hooks functional ($warnings warning(s))"
  else
    echo "  FAILED — $errors critical issue(s), $warnings warning(s)"
  fi

  return $errors
}

if [ "${1:-}" = "--health-check" ]; then
  run_health_check
  exit $?
fi

# ── Main Hook Logic ────────────────────────────────────────────────────

# Read hook input from stdin
INPUT=$(cat)

# Extract tool name, transcript path, and session ID.
# Print each field on its OWN line so values containing spaces (paths, ids)
# are not word-split/truncated by the shell. Read each line separately.
PARSED_FIELDS=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
tool = data.get('tool_name', '')
tp = data.get('transcript_path', '')
sid = data.get('session_id', '')
print(tool)
print(tp)
print(sid)
" 2>/dev/null)

{
  IFS= read -r TOOL_NAME
  IFS= read -r TRANSCRIPT_PATH
  IFS= read -r SESSION_ID
} <<< "$PARSED_FIELDS"

# If no transcript, can't measure — allow silently
if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
  exit 0
fi

# ── Token Estimation (with 30s cache) ─────────────────────────────────
ESTIMATED_TOKENS=0
USE_CACHE=false

if [ -f "$CACHE_FILE" ]; then
  CACHE_AGE=$(( $(date +%s) - $(get_mtime "$CACHE_FILE") ))
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

print(int(total_chars / $CHARS_PER_TOKEN))
" "$TRANSCRIPT_PATH" 2>/dev/null)

  if [ -z "$ESTIMATED_TOKENS" ]; then
    ESTIMATED_TOKENS=0
  fi

  # Add system context overhead (CLAUDE.md, MEMORY.md, handoffs, system prompt)
  ESTIMATED_TOKENS=$(( ESTIMATED_TOKENS + SYSTEM_OVERHEAD ))

  # Cache the result (atomic write)
  cache_tmp="${CACHE_FILE}.tmp.$$"
  echo "$ESTIMATED_TOKENS" > "$cache_tmp"
  mv -f "$cache_tmp" "$CACHE_FILE"
fi

# ── Handoff Detection (Staleness-Aware) ───────────────────────────────
# Check if a FRESH handoff from THIS session exists.
# A handoff is "stale" if tokens have grown by >HANDOFF_STALE_DELTA since
# the handoff was created. Stale handoffs do NOT satisfy enforcement.
#
# Token count at handoff creation is read from:
#   1. The handoff YAML itself (estimated_tokens: field)
#   2. Fallback: the file's mtime mapped to the token cache at that time
THIS_SESSION_HANDOFF=false
HANDOFF_TOKENS_AT_CREATION=0
HANDOFF_HAS_TOKENS=false
NEWEST_HANDOFF_MTIME=0

if [ -n "$SESSION_ID" ] && [ "$SESSION_ID" != "" ]; then
  # Find the NEWEST matching handoff (most recent = most relevant)
  NEWEST_HANDOFF=""
  NEWEST_MTIME=0
  for f in "$HANDOFF_DIR"/*.yaml "$HANDOFF_DIR"/*.yml; do
    if [ -f "$f" ]; then
      HANDOFF_SID=$(grep -m1 '^session_id:' "$f" 2>/dev/null | sed 's/^session_id:[[:space:]]*//; s/^"//; s/"[[:space:]]*$//' || true)
      if [ "$HANDOFF_SID" = "$SESSION_ID" ]; then
        THIS_SESSION_HANDOFF=true
        FILE_MTIME=$(get_mtime "$f")
        if [ "$FILE_MTIME" -gt "$NEWEST_MTIME" ]; then
          NEWEST_MTIME=$FILE_MTIME
          NEWEST_HANDOFF="$f"
        fi
      fi
    fi
  done

  # Extract token count at handoff creation from the newest matching handoff.
  # The semantic handoff protocol does NOT emit estimated_tokens:, so absence
  # is expected and must NOT be coerced to a stale-from-birth delta. We record
  # whether the field was present (HANDOFF_HAS_TOKENS) and the file mtime so the
  # freshness evaluator can fall back to mtime-based freshness when it's absent.
  if [ -n "$NEWEST_HANDOFF" ]; then
    NEWEST_HANDOFF_MTIME=$(get_mtime "$NEWEST_HANDOFF")
    RAW_TOKENS=$(grep -m1 '^estimated_tokens:' "$NEWEST_HANDOFF" 2>/dev/null | sed 's/^estimated_tokens:[[:space:]]*//' | tr -d '"' || true)
    if [ -n "$RAW_TOKENS" ] && [[ "$RAW_TOKENS" =~ ^[0-9]+$ ]]; then
      HANDOFF_TOKENS_AT_CREATION=$RAW_TOKENS
      HANDOFF_HAS_TOKENS=true
    else
      HANDOFF_TOKENS_AT_CREATION=0
      HANDOFF_HAS_TOKENS=false
    fi
  fi
fi

# Evaluate handoff freshness
if [ "$THIS_SESSION_HANDOFF" = "true" ]; then
  if [ "$HANDOFF_HAS_TOKENS" = "true" ]; then
    # Token-delta path: handoff recorded its creation-token count (mechanical
    # fallback handoffs write estimated_tokens:).
    TOKEN_DELTA=$(( ESTIMATED_TOKENS - HANDOFF_TOKENS_AT_CREATION ))

    if [ "$TOKEN_DELTA" -lt "$HANDOFF_STALE_DELTA" ]; then
      # Handoff is fresh — enforcement satisfied
      reset_enforcement
      exit 0
    else
      # Handoff is STALE — tokens grew significantly since it was created.
      echo "TOKEN-GATE: Handoff stale — created at ~${HANDOFF_TOKENS_AT_CREATION} tokens, now at ~${ESTIMATED_TOKENS} (delta: ${TOKEN_DELTA} > threshold: ${HANDOFF_STALE_DELTA})" >&2
      THIS_SESSION_HANDOFF=false
    fi
  else
    # mtime-based freshness path: the semantic handoff protocol omits
    # estimated_tokens:, so we cannot compute a token delta. A same-session
    # handoff written recently is FRESH — judging it stale-from-birth (the old
    # behavior) meant every correctly-created semantic handoff failed
    # enforcement. Map the file mtime to recency instead.
    NOW=$(date +%s)
    HANDOFF_AGE=$(( NOW - NEWEST_HANDOFF_MTIME ))
    if [ "$NEWEST_HANDOFF_MTIME" -gt 0 ] && [ "$HANDOFF_AGE" -lt "$HANDOFF_MTIME_FRESH_SECS" ]; then
      # Recent same-session handoff with unknown creation-tokens — treat as fresh
      reset_enforcement
      exit 0
    else
      echo "TOKEN-GATE: Handoff lacks estimated_tokens and mtime is stale (age: ${HANDOFF_AGE}s > ${HANDOFF_MTIME_FRESH_SECS}s) — re-activating enforcement" >&2
      THIS_SESSION_HANDOFF=false
    fi
  fi
fi

# ── Below Warning Threshold: Silent Pass ──────────────────────────────
if [ "$ESTIMATED_TOKENS" -lt "$WARN_THRESHOLD" ]; then
  # If enforcement was somehow active but tokens dropped (compaction), reset
  if [ -f "$ENFORCEMENT_FILE" ]; then
    reset_enforcement
  fi
  exit 0
fi

# ══════════════════════════════════════════════════════════════════════
# ENFORCEMENT LOOP — We're above threshold with no handoff
# ══════════════════════════════════════════════════════════════════════

# Read current enforcement state
ENFORCEMENT_JSON=$(get_enforcement)
RETRIES=$(echo "$ENFORCEMENT_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('retries',0))" 2>/dev/null || echo 0)
WAS_ACTIVE=$(echo "$ENFORCEMENT_JSON" | python3 -c "import sys,json; print(str(json.load(sys.stdin).get('active',False)).lower())" 2>/dev/null || echo "false")

# ── First Activation: Health Check ────────────────────────────────────
if [ "$WAS_ACTIVE" = "false" ]; then
  HEALTH_ISSUES=""
  for script in ".claude/scripts/token-gate.sh" ".claude/scripts/context-monitor.sh" \
                ".claude/scripts/context-watchdog.sh"; do
    if [ ! -f "$script" ]; then
      HEALTH_ISSUES="${HEALTH_ISSUES}MISSING:$script "
    elif [ ! -x "$script" ] && [[ "$script" == *.sh ]]; then
      HEALTH_ISSUES="${HEALTH_ISSUES}NOT_EXECUTABLE:$script "
    fi
  done
  if [ -n "$HEALTH_ISSUES" ]; then
    echo "HANDOFF ENFORCEMENT: Hook health issues detected: ${HEALTH_ISSUES}" >&2
  fi
fi

# Increment retry counter
RETRIES=$((RETRIES + 1))
set_enforcement "$RETRIES" "true" "$ESTIMATED_TOKENS"

PCT=$(( ESTIMATED_TOKENS * 100 / CONTEXT_WINDOW ))

# ── PHASE 1: NUDGE (retries 1-3) — Allow all tools, gentle warning ───
if [ "$RETRIES" -le "$NUDGE_MAX" ]; then
  emit_allow "HANDOFF REMINDER [${RETRIES}/${NUDGE_MAX}]: Context at ${ESTIMATED_TOKENS}/${CONTEXT_WINDOW} tokens (~${PCT}%). Please create a session handoff using /acos-handoff-protocol when your current task unit completes. After ${NUDGE_MAX} more tool calls, non-handoff tools will be BLOCKED."

# ── PHASE 2: PRESS (retries 4-8) — Block non-handoff tools ───────────
elif [ "$RETRIES" -le "$PRESS_MAX" ]; then
  if is_handoff_tool "$TOOL_NAME"; then
    emit_allow "HANDOFF ENFORCEMENT [${RETRIES}/${FORCE_MAX}]: Context at ~${PCT}%. You are in HANDOFF MODE. Complete your handoff NOW using /acos-handoff-protocol. Non-handoff tools are BLOCKED until a handoff is created."
  else
    emit_deny \
      "Handoff enforcement active [attempt ${RETRIES}/${FORCE_MAX}]. Tool '${TOOL_NAME}' blocked — only handoff tools (Read, Write, Edit, Glob, Grep, Skill, LSP) are allowed." \
      "MANDATORY HANDOFF [${RETRIES}/${FORCE_MAX}]: Context at ${ESTIMATED_TOKENS} tokens (~${PCT}%). You MUST run /acos-handoff-protocol NOW. This is attempt ${RETRIES} — the system has been asking since attempt 1. Allowed tools: Read, Write, Edit, Glob, Grep, Skill, LSP. All other tools are BLOCKED until handoff is created."
  fi

# ── PHASE 3: FORCE (retries 9-14) — Block + countdown to fallback ────
elif [ "$RETRIES" -le "$FORCE_MAX" ]; then
  REMAINING=$((FORCE_MAX - RETRIES + 1))
  if is_handoff_tool "$TOOL_NAME"; then
    emit_allow "FINAL WARNING [${RETRIES}/${FORCE_MAX}]: A mechanical handoff will be AUTO-CREATED in ${REMAINING} more tool call(s) if you do not complete /acos-handoff-protocol. Run it NOW for a proper semantic handoff. This is your LAST CHANCE."
  else
    emit_deny \
      "Handoff enforcement FINAL PHASE [${RETRIES}/${FORCE_MAX}]. Auto-fallback in ${REMAINING} tool call(s)." \
      "CRITICAL [${RETRIES}/${FORCE_MAX}]: Context at ${ESTIMATED_TOKENS} tokens (~${PCT}%). AUTO-FALLBACK in ${REMAINING} tool call(s). You have been asked ${RETRIES} times to create a handoff. Run /acos-handoff-protocol IMMEDIATELY. After ${REMAINING} more tool calls, a mechanical handoff will be auto-created and your session should end."
  fi

# ── PHASE 4: AUTO-FALLBACK (retries 15+) — Create mechanical handoff ─
else
  # Scope the collision guard to THIS session. A global glob over
  # *-enforced-handoff.yaml lets a stale fallback from a PRIOR session suppress
  # creation of a fresh one for the current session (it sees the old file, skips,
  # resets, allows — and the current session ends with no handoff). Embedding the
  # session id in the filename + globbing on that prefix keeps the guard correct.
  SAFE_SID=$(printf '%s' "${SESSION_ID:-unknown}" | tr -c 'A-Za-z0-9._-' '_')
  FALLBACK_FILE="$HANDOFF_DIR/$(date -u +%Y-%m-%dT%H:%M:%SZ)-${SAFE_SID}-enforced-handoff.yaml"

  # Only create if we haven't already created one this round FOR THIS SESSION
  if ! ls "$HANDOFF_DIR"/*-"${SAFE_SID}"-enforced-handoff.yaml 1>/dev/null 2>&1; then
    python3 -c "
import json, sys, os
from collections import Counter
from datetime import datetime, timezone

transcript_path = sys.argv[1]
session_id = sys.argv[2]
estimated_tokens = sys.argv[3]
output_file = sys.argv[4]
retry_count = sys.argv[5]

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
type: enforced-mechanical
trigger: handoff-enforcement-auto-fallback
session_id: \"{session_id}\"
estimated_tokens: {estimated_tokens}
enforcement_retries: {retry_count}
session_summary: >
  Auto-created mechanical handoff after {retry_count} enforcement attempts.
  The handoff protocol was requested {retry_count} times but never executed.
  Session had {tool_count} tool calls and modified {len(files_modified)} files.
  Context was at {estimated_tokens} tokens when auto-fallback triggered.

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
  - \"Review files_modified list to understand what changed\"
  - \"Check .acos/evidence/ for any evidence summaries\"
  - \"Run /acos-status to see overall project state\"
  - \"This was an AUTO-CREATED fallback — consider why /acos-handoff-protocol did not execute\"

context_for_next_session: |
  ENFORCED MECHANICAL HANDOFF: The previous session hit the context threshold
  and the enforcement loop requested a semantic handoff {retry_count} times,
  but /acos-handoff-protocol was never executed. This mechanical extraction
  was auto-created as a fallback. It contains file lists and breadcrumbs but
  lacks decisions, blockers, and next-action analysis.

  Review the breadcrumbs and modified files to reconstruct session context.
'''

with open(output_file, 'w') as f:
    f.write(yaml)

print(f'Enforced handoff written to {output_file}', file=sys.stderr)
" "$TRANSCRIPT_PATH" "${SESSION_ID:-unknown}" "$ESTIMATED_TOKENS" "$FALLBACK_FILE" "$RETRIES" 2>/dev/null
  fi

  # Reset enforcement — we've done what we can
  reset_enforcement

  emit_allow "AUTO-FALLBACK COMPLETE: After ${RETRIES} enforcement attempts, a mechanical handoff was auto-created. The /acos-handoff-protocol skill was never executed despite ${RETRIES} requests. Session should end soon."
fi
