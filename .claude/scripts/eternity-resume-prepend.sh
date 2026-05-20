#!/bin/bash
# UserPromptSubmit hook — fail-safe resume injection for ACOS Eternity Protocol.
#
# Purpose: if the daemon-driven post-/clear resume injection fails for any
# reason (PID missing, CGEvent failure, daemon dead, etc.), this hook catches
# the user on their next prompt and prepends the pending resume content as
# additional context. The hook fires inside the correct Claude Code process
# by construction — there is no way for it to inject into the wrong window.
#
# Project scoping (critical): the hook ONLY considers pending-resume files
# whose session_id is a JSONL that has ever lived in this project's
# Claude Code projects directory. Without this, a resume from project A
# could be consumed by a hook firing in project B. The state directory is
# shared across all projects; the project's JSONL directory is the only
# reliable signal for "is this resume mine?"
#
# Consumption: on first fire we move the pending-resume file + arming flags
# to state/consumed/ (NOT rm), so the hook will not fire a second time for
# the same resume. This is single-shot recovery; subsequent cycles produce
# their own resume.
#
# 2026-05-20 (PM) fix — Bug #5b. Previously this hook did `rm -f` on the
# three artifacts, mirroring the same bug that was fixed in
# /acos-eternity-protocol-resume SKILL.md Step 5 the same afternoon. Both
# code paths now use the same `mv → state/consumed/` discipline so the
# preserve-pending-resumes invariant holds whichever path consumes first.
# See feedback_preserve_pending_resumes.md and
# feedback_eternity_resume_step5_violates_preserve.md.
#
# Safe-by-default: if no matching pending resume exists, the hook outputs
# nothing and the user's prompt passes through unmodified.

set -e

STATE="$HOME/Library/Application Support/acos-token-monitor/state"

# Read hook input (JSON on stdin per Claude Code hook protocol).
INPUT=$(cat 2>/dev/null || echo "{}")

# Extract session_id and cwd. cwd is required for project scoping; if it's
# missing we bail safely (no injection).
HOOK_DATA=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('session_id', ''))
    print(d.get('cwd', ''))
except: pass
" 2>/dev/null)

SESSION_ID=$(echo "$HOOK_DATA" | sed -n '1p')
CWD=$(echo "$HOOK_DATA" | sed -n '2p')

# Without cwd we cannot scope to project. Bail safely.
[[ -z "$CWD" ]] && exit 0

# Compute the Claude Code project directory for THIS cwd. Uses the same
# sanitization Claude Code itself applies: slashes/spaces/dots → dashes.
SANITIZED=$(echo "$CWD" | tr '/' '-' | tr ' ' '-' | tr '.' '-')
PROJECT_DIR="$HOME/.claude/projects/$SANITIZED"

# Build set of session IDs that have ever lived in this project.
[[ -d "$PROJECT_DIR" ]] || exit 0
PROJECT_SESSIONS=$(ls "$PROJECT_DIR"/*.jsonl 2>/dev/null | xargs -I{} basename {} .jsonl 2>/dev/null)
[[ -z "$PROJECT_SESSIONS" ]] && exit 0

# Find pending resume files whose session_id is in this project.
# Prefer the current session's file; else most-recent that matches the project.
RESUME=""
if [[ -n "$SESSION_ID" ]]; then
    F="$STATE/pending-resume-${SESSION_ID}.txt"
    if [[ -s "$F" ]] && echo "$PROJECT_SESSIONS" | grep -Fxq "$SESSION_ID"; then
        RESUME="$F"
    fi
fi
if [[ -z "$RESUME" ]]; then
    # Walk pending-resume files newest-first, take first one that matches this
    # project (post-/clear case: file is keyed to the prior session ID).
    while IFS= read -r CANDIDATE; do
        [[ -z "$CANDIDATE" ]] && continue
        SID=$(basename "$CANDIDATE" .txt | sed 's/^pending-resume-//')
        if echo "$PROJECT_SESSIONS" | grep -Fxq "$SID"; then
            RESUME="$CANDIDATE"
            break
        fi
    done < <(ls -t "$STATE"/pending-resume-*.txt 2>/dev/null)
fi

# No matching pending resume in this project → silent passthrough.
if [[ -z "$RESUME" || ! -s "$RESUME" ]]; then
    exit 0
fi

# Read content BEFORE deleting (race-safety).
CONTENT=$(cat "$RESUME")

# Consume the resume file + flags so the hook fires exactly once for this
# cycle. Subsequent prompts pass through unmodified.
#
# Preserve-by-move (not rm). Mirror /acos-eternity-protocol-resume SKILL.md
# Step 5: mv each artifact to state/consumed/ with a unix-ts suffix on
# filename collisions. Atomic on the same filesystem. Future maintenance
# can prune state/consumed/ by mtime via a dedicated command — but never
# as a side effect of hook consumption.
RESUME_SID=$(basename "$RESUME" .txt | sed 's/^pending-resume-//')
CONSUMED="$STATE/consumed"
mkdir -p "$CONSUMED"
TS=$(date +%s)
for ARTIFACT in \
    "$RESUME" \
    "$STATE/.resume-pending-${RESUME_SID}" \
    "$STATE/.compact-fired-${RESUME_SID}"
do
    [[ -e "$ARTIFACT" ]] || continue
    BASENAME=$(basename "$ARTIFACT")
    DEST="$CONSUMED/$BASENAME"
    [[ -e "$DEST" ]] && DEST="${DEST}.${TS}"
    mv "$ARTIFACT" "$DEST"
done

# Emit hookSpecificOutput JSON. additionalContext is prepended to the user's
# prompt by Claude Code, preserving the user's original input verbatim.
# Content is piped via stdin to avoid shell quoting hazards.
printf '%s' "$CONTENT" | python3 -c '
import json, sys
content = sys.stdin.read()
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": content,
    }
}))
'

exit 0
