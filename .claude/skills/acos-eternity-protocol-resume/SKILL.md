---
name: acos-eternity-protocol-resume
description: Manually injects the pending resume prompt into the active Warp pane. Fallback for when the daemon-driven post-clear resume injection didn't fire. Reads ~/Library/Application Support/acos-token-monitor/state/pending-resume-<session_id>.txt and uses inject-keystroke.py with --session-id (AXTitle marker 'ACOS[<uuid>]') for precise targeting.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Bash
---

# ACOS Eternity Protocol Resume (manual fire)

## Overview

The daemon normally injects the resume prompt automatically after `/clear`
completes. When that fails, invoke this skill to fire the resume prompt
manually into the calling Warp pane.

## Execution Policy

This skill is **autonomous** — invoking it IS authorization. Do NOT pause to
confirm. Run all steps in sequence and exit.

## Protocol

### Step 0: Self-write PID file for current (post-/clear) session

Because /clear mints a new session ID inside the same OS process, the daemon's
SessionStart hook may not have written a `pid-<new_session_id>` file yet, or
may have raced. Write it ourselves before injecting — that way future cycles
also have a valid PID file on disk.

```bash
SESSION_DIR="$HOME/.claude/projects/$(pwd | tr '/' '-' | tr ' ' '-' | tr '.' '-')"
JSONL=$(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null | head -1)
test -n "$JSONL" || { echo "ERROR: no JSONL for current project"; exit 1; }
SESSION_ID=$(basename "$JSONL" .jsonl)

echo "{\"session_id\":\"$SESSION_ID\"}" | \
    "$HOME/Library/Application Support/acos-token-monitor/bin/register-session-pid.sh" 2>/dev/null || true
```

### Step 1: Locate pending resume file (project-scoped)

First look for one keyed to the *current* session ID. If absent, fall back to
the most recent `pending-resume-*.txt` **whose `<sid>` belongs to this
project** — the common post-/clear case is that the resume file is keyed to
the PRE-/clear session ID, which lives in this project's
`~/.claude/projects/<sanitized-cwd>/` JSONL dir, while this skill runs in the
POST-/clear session with a new (also in-project) ID.

**2026-05-20 (PM) fix — Bug #5c.** Previously the fallback was an unscoped
`ls -t pending-resume-*.txt | head -1`, which would silently inject a resume
from a completely different project if this project had no pending resume of
its own. The Wigum-style misrouting that resulted made the post-/clear session
believe it was resuming a different deal entirely. See
[`feedback_eternity_resume_stale_cross_contamination.md`](../../memory/feedback_eternity_resume_stale_cross_contamination.md).
The project-scoping pattern below mirrors `eternity-resume-prepend.sh` lines
56–87 verbatim so both code paths share one failure-mode surface.

```bash
STATE="$HOME/Library/Application Support/acos-token-monitor/state"

# Compute the Claude Code project dir for THIS cwd (same sanitization the
# hook uses: slashes/spaces/dots → dashes).
PROJECT_DIR="$HOME/.claude/projects/$(pwd | tr '/' '-' | tr ' ' '-' | tr '.' '-')"
test -d "$PROJECT_DIR" || { echo "ERROR: no Claude Code project dir for cwd $(pwd) — refusing to scan globally"; exit 1; }

# Set of session IDs that have ever lived in this project. Used to scope
# both the primary lookup and the newest-first fallback so we never pick up
# a sibling project's pending resume.
PROJECT_SESSIONS=$(ls "$PROJECT_DIR"/*.jsonl 2>/dev/null | xargs -I{} basename {} .jsonl 2>/dev/null)
test -n "$PROJECT_SESSIONS" || { echo "ERROR: no JSONLs in $PROJECT_DIR — refusing to inject"; exit 1; }

# Prefer the current session's pending resume IF that SID belongs to this
# project (it should — SESSION_ID came from this project's JSONL dir — but
# the explicit check is cheap defense-in-depth).
RESUME=""
F="$STATE/pending-resume-${SESSION_ID}.txt"
if [[ -s "$F" ]] && echo "$PROJECT_SESSIONS" | grep -Fxq "$SESSION_ID"; then
    RESUME="$F"
fi

# Fallback (post-/clear common case): walk pending-resume files newest-first,
# take the first one whose <sid> is in this project's session set.
if [[ -z "$RESUME" ]]; then
    while IFS= read -r CANDIDATE; do
        [[ -z "$CANDIDATE" ]] && continue
        SID=$(basename "$CANDIDATE" .txt | sed 's/^pending-resume-//')
        if echo "$PROJECT_SESSIONS" | grep -Fxq "$SID"; then
            RESUME="$CANDIDATE"
            break
        fi
    done < <(ls -t "$STATE"/pending-resume-*.txt 2>/dev/null)
fi

if ! test -s "$RESUME"; then
    # 2026-05-21 fix — defect (d) in the cross-session-misfire investigation.
    # Before declaring failure, check state/consumed/ for a recently-mv'd
    # pending-resume keyed to ANY session ID in this project. If found
    # within the last 10 minutes, the UserPromptSubmit hook
    # (eternity-resume-prepend.sh) already injected the resume content as
    # additionalContext and we have NOTHING to do — exit 0 with a clear
    # "auto-resume already completed" message rather than the previously
    # misleading "ERROR: no pending resume found" that implied failure.
    #
    # Window choice: 10 min covers the typical /clear → daemon-claim →
    # skill-typed → skill-body-runs path (seconds to a couple of minutes
    # in practice), with margin for slow terminals or paused sessions.
    # Outside that window, a stale consumed/ entry should NOT mask a
    # genuine "no pending resume" error — return the original exit-1.
    CONSUMED="$STATE/consumed"
    if [[ -d "$CONSUMED" ]]; then
        while IFS= read -r RECENT; do
            [[ -z "$RECENT" ]] && continue
            SID=$(basename "$RECENT" .txt | sed 's/^pending-resume-//')
            if echo "$PROJECT_SESSIONS" | grep -Fxq "$SID"; then
                MTIME=$(stat -f '%Sm' -t '%Y-%m-%dT%H:%M:%SZ' "$RECENT" 2>/dev/null || echo "unknown")
                echo "OK: auto-resume already completed for session $SID at $MTIME"
                echo "    (UserPromptSubmit hook injected $(basename "$RECENT") as additionalContext;"
                echo "     skill body has nothing further to do)"
                exit 0
            fi
        done < <(find "$CONSUMED" -name 'pending-resume-*.txt' -mmin -10 2>/dev/null)
    fi
    echo "ERROR: no pending resume found for this project (refusing cross-project fallback)"
    exit 1
fi
# Record which session_id owned this resume (for cleanup + Step 5 guard).
RESUME_SID=$(basename "$RESUME" .txt | sed 's/^pending-resume-//')
```

### Step 2: Show preview

```bash
echo "─── About to inject this resume prompt ───"
head -6 "$RESUME"
echo "─── (full prompt: $(wc -l < "$RESUME") lines) ───"
```

### Step 3: Liveness check — confirm session process is still alive

Note: as of the 2026-05-20 rewrite the injector targets by **session UUID**
(via the `ACOS[<uuid>]` AXTitle marker stamped by `register-session-pid.sh`),
not by PID. This step's PID read is therefore **defensive only** — it refuses
to inject if the `claude` process for this session is already dead (stale
PID file), preventing the injector from typing into an unrelated window that
later takes Warp focus. The PID itself is never passed to the injector.

```bash
PID_FILE="$STATE/pid-${SESSION_ID}"
test -f "$PID_FILE" || { echo "ERROR: no PID file at $PID_FILE — Step 0 should have written one. claude ancestor not found in process tree?"; exit 1; }
PID=$(head -1 "$PID_FILE")
kill -0 "$PID" 2>/dev/null || { echo "ERROR: PID $PID not alive — stale pid file?"; exit 1; }
```

The AppleScript-frontmost fallback has been removed by design — if precise
injection isn't possible, this skill aborts cleanly rather than typing into
whichever window has focus.

### Step 4: Inject

Per the 2026-05-20 rewrite, the injector targets by session UUID (AXTitle marker
stamped by register-session-pid.sh at session start) rather than by PID. The
injector internally enumerates Warp's AXWindows, finds the one with the
`ACOS[<SESSION_ID>]` marker, raises it, and posts via CGEventPost(kCGHIDEventTap).

```bash
INJECTOR="$HOME/Library/Application Support/acos-token-monitor/bin/inject-keystroke.py"
# For a manual resume we skip verification — this is the user explicitly
# requesting injection, not a /clear that we need to confirm took effect.
cat "$RESUME" | python3 "$INJECTOR" --from-stdin --session-id "$RESUME_SID" --no-verify
```

### Step 5: Move consumed flags to state/consumed/ (preserve, don't delete)

**2026-05-20 (PM) fix.** Previously this step `rm`-ed all three artifacts. That
violated the standing preserve-pending-resumes rule
([`feedback_preserve_pending_resumes.md`](../../memory/feedback_preserve_pending_resumes.md)
and [`feedback_eternity_resume_step5_violates_preserve.md`](../../memory/feedback_eternity_resume_step5_violates_preserve.md))
— each pending-resume file represents a real project waiting to resume, and a
silent `rm` made post-mortem investigation of failed injections impossible
(no replay, no forensic trail). Today's daemon-clear-arch verification ran
into exactly this: the resume file Jason wanted to inspect had already been
`rm`-ed by a prior manual-resume run.

New behavior: `mv` to `state/consumed/` with a unix-timestamp suffix on
filename collisions. Atomic on the same filesystem. Preserves the file for
audit/replay. Future cleanup (if state/consumed/ ever grows unmanageable) can
prune by mtime via a separate maintenance command — but never as a side
effect of resume injection.

```bash
# Defense-in-depth: Step 1 should already guarantee RESUME_SID belongs to
# this project, but verify once more before mv-ing artifacts that might
# belong to a sibling project's pending resume. Costs one grep, prevents
# the worst class of Step 5 misbehavior if Step 1's invariant is ever
# broken by a future refactor.
if ! echo "$PROJECT_SESSIONS" | grep -Fxq "$RESUME_SID"; then
    echo "ERROR: RESUME_SID $RESUME_SID is not in this project's session set"
    echo "       refusing to mv artifacts (cross-contamination guard)"
    exit 1
fi

CONSUMED="$STATE/consumed"
mkdir -p "$CONSUMED"
TS=$(date +%s)
for ARTIFACT in \
    "$STATE/.resume-pending-${RESUME_SID}" \
    "$STATE/.compact-fired-${RESUME_SID}" \
    "$STATE/pending-resume-${RESUME_SID}.txt"
do
    [[ -e "$ARTIFACT" ]] || continue
    BASENAME=$(basename "$ARTIFACT")
    DEST="$CONSUMED/$BASENAME"
    # Collision-safe: if a prior consumed copy exists, suffix with unix ts.
    # Same pattern token-watcher.py uses for aged-out .compact-fired-* files.
    [[ -e "$DEST" ]] && DEST="${DEST}.${TS}"
    mv "$ARTIFACT" "$DEST"
done
```

### Step 6: Report

Print injector return code, success message, and reminder that the resume
prompt has been consumed (subsequent invocations will fail with "no pending
resume" until the next eternity-protocol cycle generates a new one).

---

*ACOS Eternity Protocol Resume — manual fallback for daemon-driven resume injection.*
