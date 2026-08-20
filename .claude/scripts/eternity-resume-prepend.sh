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

# Find the resume content for THIS pane, in priority order:
#   1. The current session's own pending-resume-<sid>.txt (PID-scoped by
#      construction — the file is keyed to this exact session id).
#   2. The per-claude-PID pointer for THIS pane (.eternity-pointer-pid-<pid>)
#      written by eternity-protocol-core.sh. This is the cross-pane-safe path:
#      claude PID is stable across /clear within a pane and differs between
#      concurrent panes of the same project, so it cannot misfire into the
#      wrong session the way the unscoped newest-in-project fallback can.
#   3. (LAST RESORT) The newest pending-resume-*.txt that belongs to this
#      project. This is NOT PID/pane-scoped, so with two concurrent panes of
#      the same project it can pick the OTHER pane's resume — hence it now only
#      runs when neither (1) nor (2) produced a match.
#
# Two carriers of resume content are possible:
#   - RESUME           : a pending-resume-*.txt file (legacy path).
#   - SIBLING          : a memory/handoffs/<basename>.resume.md sibling pointed
#                        to by the per-PID pointer (preferred, archival).
# CONTENT is populated from whichever carrier wins. On the pointer path we
# consume ONLY the pointer (mv → consumed/), never the .resume.md sibling and
# never any pending-resume file (preserve-pending-resumes invariant).
RESUME=""
SIBLING=""
POINTER_MATCHED=""

# (1) Current session's own pending-resume file.
if [[ -n "$SESSION_ID" ]]; then
    F="$STATE/pending-resume-${SESSION_ID}.txt"
    if [[ -s "$F" ]] && echo "$PROJECT_SESSIONS" | grep -Fxq "$SESSION_ID"; then
        RESUME="$F"
    fi
fi

# (2) Per-claude-PID pointer for THIS pane (only if (1) found nothing).
# Resolve THIS pane's claude PID by walking the parent process tree (up to 15
# levels — matches register-session-pid.sh / the resume skill). The current
# session's pid-<sid> file may not exist yet post-/clear, so derive live.
if [[ -z "$RESUME" ]]; then
    CLAUDE_PID=""
    WALK_PID=$$
    for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
        PARENT=$(ps -o ppid= -p "$WALK_PID" 2>/dev/null | tr -d ' ' || echo "")
        [[ -z "$PARENT" || "$PARENT" -le 1 ]] && break
        COMM=$(ps -o comm= -p "$PARENT" 2>/dev/null || echo "")
        ARGS=$(ps -o command= -p "$PARENT" 2>/dev/null || echo "")
        # The auto-loop wrapper `claude-loop.sh` (argv like `/bin/bash
        # ./claude-loop.sh` or `/path/claude-loop.sh`) must NOT be mistaken for
        # the real claude process — otherwise CLAUDE_PID resolves to the bash
        # wrapper and the per-PID pointer (keyed by the real claude PID in
        # core.sh) is missed, silently dropping the cross-pane-safe path.
        case "$COMM" in
            *claude-loop*) WALK_PID=$PARENT; continue ;;
            claude|claude.ex|*/claude|*/claude.ex) CLAUDE_PID="$PARENT"; break ;;
        esac
        case "$ARGS" in
            *claude-loop*) WALK_PID=$PARENT; continue ;;
            *" claude"|*"/claude"|*"npx claude"*|*"bunx claude"*) CLAUDE_PID="$PARENT"; break ;;
        esac
        WALK_PID=$PARENT
    done

    if [[ -n "$CLAUDE_PID" ]]; then
        POINTER="$STATE/.eternity-pointer-pid-${CLAUDE_PID}"
        if [[ -s "$POINTER" ]]; then
            # PID-reuse guard: if the OS recycled this PID after the original
            # claude exited, the pointer belongs to a different (dead) instance.
            # core.sh stamps claude_lstart precisely so we can detect this.
            # Backward-compat: pointers without claude_lstart skip the check.
            PTR_LSTART=$(grep '^claude_lstart:' "$POINTER" 2>/dev/null \
                | head -1 | sed 's/^claude_lstart:[[:space:]]*//' \
                | sed 's/[[:space:]]*$//')
            STALE_POINTER=false
            if [[ -n "$PTR_LSTART" ]]; then
                LIVE_LSTART=$(ps -o lstart= -p "$CLAUDE_PID" 2>/dev/null \
                    | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
                if [[ -n "$LIVE_LSTART" && "$PTR_LSTART" != "$LIVE_LSTART" ]]; then
                    STALE_POINTER=true
                fi
            fi
            if [[ "$STALE_POINTER" == "false" ]]; then
                BASENAME=$(grep '^handoff_basename:' "$POINTER" 2>/dev/null \
                    | head -1 | sed 's/^handoff_basename:[[:space:]]*//')
                CAND_SIBLING="memory/handoffs/${BASENAME}.resume.md"
                if [[ -n "$BASENAME" && -s "$CAND_SIBLING" ]]; then
                    SIBLING="$CAND_SIBLING"
                    POINTER_MATCHED="$POINTER"
                fi
            fi
        fi
    fi
fi

# (3) LAST RESORT — newest pending-resume in this project, PANE-SCOPED.
# Only when neither the current session's file nor the per-PID pointer matched.
#
# 2026-07-18 (SLICE-RES-01) pane-scope gate: project scoping alone lets two
# panes on the SAME project steal each other's resume (the 2026-06-26 incident
# class; flagged by the 2026-07-14 swarm as the most important pre-existing
# bug to close before per-project tooling makes two-panes-one-project routine).
# A candidate is claimable ONLY when its session's recorded surface binding
# (state/cmux-surface-<sid>) equals THIS pane's live $CMUX_SURFACE_ID.
# Unverifiable (either side unknown — e.g. a Warp pane, or an age-GC'd
# binding) => fail CLOSED: skip the candidate. Warp recovery keeps its
# documented PRIMARY path, the manual /acos-eternity-protocol-resume skill.
#
# 2026-08-18 PROJECT-KEY gate (Zee's Rule 1: no intermingling inside a shared
# folder). $PROJECT_SESSIONS is derived from the sanitized CWD, so it is a
# FOLDER set, not a project set. Research to Portfolio, FruitSync, Skill
# Workshop, Website-builder and Logo Builder all live in "ACOS 3.0", so all of
# their sessions pass that test. The surface gate above was meant to narrow it
# further, but cmux-surface-<sid> bindings are never pruned — on 2026-08-18
# there were 1034 of them mapping onto 105 surfaces, with EIGHT sessions
# (including R2P's a6b28886) all claiming surface F354478B. Both discriminators
# therefore collapsed and `ls -t` decided by mtime, which served FruitSync's
# handoff (session ff036fd7, 17:01:11Z) to the R2P pane.
#
# A folder cannot distinguish those projects; only the project_uuid can. So a
# candidate is claimable ONLY when its recorded project binding
# (state/project-<sid>, written by enroll-project.sh at SessionStart) equals
# THIS session's. Unknown on either side => fail CLOSED, exactly like the
# surface gate. Failing closed here is safe: it only disables the LAST-RESORT
# path, while the session's own pending-resume file and the per-PID pointer —
# both already identity-scoped — keep working untouched.
if [[ -z "$RESUME" && -z "$SIBLING" ]]; then
    MY_PROJECT=$(cat "$STATE/project-$SESSION_ID" 2>/dev/null | head -1)
    while IFS= read -r CANDIDATE; do
        [[ -z "$CANDIDATE" ]] && continue
        SID=$(basename "$CANDIDATE" .txt | sed 's/^pending-resume-//')
        if echo "$PROJECT_SESSIONS" | grep -Fxq "$SID"; then
            CAND_SURFACE=$(cat "$STATE/cmux-surface-$SID" 2>/dev/null | head -1)
            if [[ -z "$CMUX_SURFACE_ID" || -z "$CAND_SURFACE" \
                  || "$CAND_SURFACE" != "$CMUX_SURFACE_ID" ]]; then
                continue
            fi
            CAND_PROJECT=$(cat "$STATE/project-$SID" 2>/dev/null | head -1)
            if [[ -z "$MY_PROJECT" || -z "$CAND_PROJECT" \
                  || "$CAND_PROJECT" != "$MY_PROJECT" ]]; then
                continue
            fi
            RESUME="$CANDIDATE"
            break
        fi
    done < <(ls -t "$STATE"/pending-resume-*.txt 2>/dev/null)
fi

# No matching resume in this project → silent passthrough.
if [[ -z "$SIBLING" && ( -z "$RESUME" || ! -s "$RESUME" ) ]]; then
    exit 0
fi

# Read content BEFORE consuming (race-safety). Sibling (pointer path) wins.
if [[ -n "$SIBLING" ]]; then
    CONTENT=$(cat "$SIBLING")
else
    CONTENT=$(cat "$RESUME")
fi

# Consume so the hook fires exactly once for this cycle. Subsequent prompts
# pass through unmodified.
#
# Preserve-by-move (not rm). Mirror /acos-eternity-protocol-resume SKILL.md
# Step 5: mv each artifact to state/consumed/ with a unix-ts suffix on
# filename collisions. Atomic on the same filesystem. Future maintenance
# can prune state/consumed/ by mtime via a dedicated command — but never
# as a side effect of hook consumption.
CONSUMED="$STATE/consumed"
mkdir -p "$CONSUMED"
TS=$(date +%s)

if [[ -n "$POINTER_MATCHED" ]]; then
    # Pointer path: consume the per-PID pointer AND its same-cycle twin
    # pending-resume file. Both carriers hold IDENTICAL content — core.sh cp's
    # pending-resume-<sid>.txt into the .resume.md sibling — so consuming only
    # the pointer used to leave the twin live, and the very next prompt re-fired
    # it via the last-resort path (3): the double-injection bug. The pointer
    # records session_id_at_write, which is exactly the sid that keys the twin
    # (core.sh: RESUME_FILE=pending-resume-${SESSION_ID}.txt and pointer
    # session_id_at_write=${SESSION_ID}), so we disarm precisely THIS pane's own
    # twin — never another concurrent pane's resume.
    #
    # The .resume.md sibling in memory/handoffs/ is archival and is STILL never
    # consumed. The twin is MOVED to consumed/ (never rm'd), so the
    # preserve-pending-resumes invariant holds.
    PTR_SID=$(grep '^session_id_at_write:' "$POINTER_MATCHED" 2>/dev/null \
        | head -1 | sed 's/^session_id_at_write:[[:space:]]*//' \
        | sed 's/[[:space:]]*$//')

    if [[ -e "$POINTER_MATCHED" ]]; then
        DEST="$CONSUMED/$(basename "$POINTER_MATCHED")"
        [[ -e "$DEST" ]] && DEST="${DEST}.${TS}"
        mv "$POINTER_MATCHED" "$DEST"
    fi

    # Disarm the twin (+ its arming sidecars) so path (3) cannot re-inject it on
    # the next prompt. Guard the sid shape so a corrupt pointer can never build a
    # bad path or glob the state dir.
    if [[ "$PTR_SID" =~ ^[0-9a-fA-F-]+$ ]]; then
        for ARTIFACT in \
            "$STATE/pending-resume-${PTR_SID}.txt" \
            "$STATE/.resume-pending-${PTR_SID}" \
            "$STATE/.compact-fired-${PTR_SID}"
        do
            [[ -e "$ARTIFACT" ]] || continue
            DEST="$CONSUMED/$(basename "$ARTIFACT")"
            [[ -e "$DEST" ]] && DEST="${DEST}.${TS}"
            mv "$ARTIFACT" "$DEST"
        done
    fi
else
    # Legacy path: move the matched pending-resume file + its arming flags to
    # consumed/ (preserve-by-move, never rm).
    RESUME_SID=$(basename "$RESUME" .txt | sed 's/^pending-resume-//')
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
fi

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
