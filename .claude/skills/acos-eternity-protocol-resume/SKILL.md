---
name: acos-eternity-protocol-resume
description: Injects the pending resume prompt into the calling Warp pane after a /clear. This is the PRIMARY resume path for Warp sessions — the daemon NEVER auto-injects for Warp (manual-only since 2026-06-04) — and a fallback for cmux sessions when the daemon's auto-injection didn't fire. Reads ~/Library/Application Support/acos-token-monitor/state/pending-resume-<session_id>.txt (or the per-PID pointer's .resume.md sibling) and uses inject-keystroke.py with --session-id (AXTitle marker 'ACOS[<uuid>]') for precise targeting.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Bash
---

# ACOS Eternity Protocol Resume (manual fire)

## Overview

This skill fires the resume prompt into the calling Warp pane after `/clear`.

For **Warp** sessions this is the **PRIMARY** resume path: the daemon's
auto-injection has been manual-only since 2026-06-04 (the AXTitle marker race
makes daemon-driven keystroke injection unreliable across multi-Warp-window
setups), so the daemon never auto-injects for Warp — you invoke this skill
yourself after typing `/clear`.

For **cmux** sessions the daemon DOES auto-inject the resume content directly
into the surface over the Unix socket; there this skill is a manual **fallback**
for when that auto-injection didn't fire.

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

### Step 0.5: Try the handoff-paired pointer first (2026-06-04)

**Primary path — added to solve the "any time" resume problem.** The warp
and cmux variants write a per-claude-PID pointer at fire time
(`state/.eternity-pointer-pid-<pid>`) that records the handoff basename.
The associated resume content lives at
`memory/handoffs/<basename>.resume.md` — a sibling of the handoff yaml
that NEVER expires.

This step looks up the pointer for THIS pane's claude PID. Because claude
PID survives /clear within the same OS process (the same pane can /clear
many times across days; the PID stays stable), the pointer remains valid
regardless of when you type `/acos-eternity-protocol-resume`.

If the pointer is found:
  - inject the sibling .resume.md content
  - move the pointer to state/consumed/ (prevents stale re-injection on
    later /clears in this pane that DON'T fire a fresh warp/cmux first)
  - exit cleanly

If no pointer is found OR the sibling .resume.md is missing → fall through
to Step 1 (legacy state/pending-resume-*.txt lookup).

```bash
# Re-derive Step-0 vars: each fenced bash block runs in its OWN shell, so
# $SESSION_ID / $STATE set in Step 0 are EMPTY here. Re-derive self-containedly.
SESSION_DIR="$HOME/.claude/projects/$(pwd | tr '/' '-' | tr ' ' '-' | tr '.' '-')"
JSONL=$(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null | head -1)
test -n "$JSONL" || { echo "ERROR: no JSONL for current project"; exit 1; }
SESSION_ID=$(basename "$JSONL" .jsonl)
STATE="$HOME/Library/Application Support/acos-token-monitor/state"

# Resolve THIS pane's claude PID by walking the parent process tree.
# Up to 15 levels (matches register-session-pid.sh's walk depth).
CLAUDE_PID=""
PID=$$
for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
    PARENT=$(ps -o ppid= -p "$PID" 2>/dev/null | tr -d ' ' || echo "")
    [[ -z "$PARENT" || "$PARENT" -le 1 ]] && break
    COMM=$(ps -o comm= -p "$PARENT" 2>/dev/null || echo "")
    ARGS=$(ps -o command= -p "$PARENT" 2>/dev/null || echo "")
    case "$COMM" in
        claude|claude.ex|*/claude|*/claude.ex) CLAUDE_PID="$PARENT"; break ;;
    esac
    case "$ARGS" in
        *" claude"*|*"/claude"*|*"npx claude"*|*"bunx claude"*) CLAUDE_PID="$PARENT"; break ;;
    esac
    PID=$PARENT
done

POINTER_USED=""
if [[ -n "$CLAUDE_PID" ]]; then
    POINTER="$STATE/.eternity-pointer-pid-${CLAUDE_PID}"
    if [[ -s "$POINTER" ]]; then
        # PID-REUSE GUARD (2026-06-11): the OS can recycle a PID after the
        # original claude process exits. If that happens, this pointer was
        # written by a DIFFERENT (now-dead) claude instance and injecting its
        # handoff would resume the wrong work. core.sh stamps the process
        # start time into `claude_lstart:` precisely so we can detect reuse.
        #
        # The lstart value contains spaces (e.g. "Wed Jun 11 09:14:02 2026"),
        # so we take the FULL remainder of the line after the key, not just the
        # first token. Compare (trimmed) against the live process's lstart.
        # Backward-compat: pointers written before this field existed have no
        # claude_lstart line → we skip the check and proceed as before.
        PTR_LSTART=$(grep '^claude_lstart:' "$POINTER" \
            | head -1 | sed 's/^claude_lstart:[[:space:]]*//' \
            | sed 's/[[:space:]]*$//')
        if [[ -n "$PTR_LSTART" ]]; then
            LIVE_LSTART=$(ps -o lstart= -p "$CLAUDE_PID" 2>/dev/null \
                | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
            if [[ -n "$LIVE_LSTART" && "$PTR_LSTART" != "$LIVE_LSTART" ]]; then
                echo "WARN: pointer is from a previous claude instance with a recycled PID"
                echo "      (pointer lstart: '$PTR_LSTART'  vs  live PID $CLAUDE_PID lstart: '$LIVE_LSTART')"
                echo "      retiring stale pointer → consumed/ and falling through to legacy lookup"
                CONSUMED="$STATE/consumed"
                mkdir -p "$CONSUMED"
                TS=$(date +%s)
                DEST="$CONSUMED/$(basename "$POINTER").stale.${TS}"
                mv "$POINTER" "$DEST" 2>/dev/null || true
                POINTER=""   # force fall-through to Step 1
            fi
        fi
    fi
    if [[ -n "$POINTER" && -s "$POINTER" ]]; then
        # Extract handoff_basename from the pointer yaml
        BASENAME=$(grep '^handoff_basename:' "$POINTER" | sed 's/^handoff_basename:[[:space:]]*//')
        SIBLING="memory/handoffs/${BASENAME}.resume.md"
        if [[ -s "$SIBLING" ]]; then
            echo "─── Resuming from handoff-paired sibling ───"
            echo "    pointer:  $POINTER"
            echo "    handoff:  memory/handoffs/${BASENAME}.yaml"
            echo "    resume:   $SIBLING"
            echo "─── First 6 lines of resume prompt ───"
            head -6 "$SIBLING"
            echo "─── (full prompt: $(wc -l < "$SIBLING") lines) ───"

            INJECTOR="$HOME/Library/Application Support/acos-token-monitor/bin/inject-keystroke.py"
            cat "$SIBLING" | python3 "$INJECTOR" --from-stdin --session-id "$SESSION_ID" --no-verify
            INJECT_RC=$?

            if [[ $INJECT_RC -eq 0 ]]; then
                # Consume the pointer (mv to consumed/) so subsequent /clears
                # in this pane that don't fire a fresh warp/cmux first don't
                # re-inject this resume. The .resume.md sibling itself stays
                # in memory/handoffs/ forever for archival / manual re-load.
                CONSUMED="$STATE/consumed"
                mkdir -p "$CONSUMED"
                TS=$(date +%s)
                DEST="$CONSUMED/$(basename "$POINTER")"
                [[ -e "$DEST" ]] && DEST="${DEST}.${TS}"
                mv "$POINTER" "$DEST" 2>/dev/null || true
                echo "OK: resume injected from handoff-paired sibling; pointer consumed → $DEST"
                exit 0
            else
                # Injection FAILED. If we leave the pointer in place we'd retry
                # this exact same (failing) sibling on every future invocation —
                # an infinite identical-retry loop. Retire the pointer into
                # consumed/ with a .failed suffix: forensics preserved, loop
                # broken. The .resume.md SIBLING itself is NOT deleted — it lives
                # in memory/handoffs/ forever for the manual/pick-from-list path.
                echo "WARN: injector returned rc=$INJECT_RC for sibling path"
                CONSUMED="$STATE/consumed"
                mkdir -p "$CONSUMED"
                TS=$(date +%s)
                DEST="$CONSUMED/$(basename "$POINTER").failed.${TS}"
                mv "$POINTER" "$DEST" 2>/dev/null || true
                echo "       retired failing pointer → $DEST (retry loop broken)"
                echo "       resume content preserved at $SIBLING"
                echo "       falling through to legacy state/pending-resume-*.txt lookup"
                POINTER_USED="$POINTER"  # remember for diagnostic
            fi
        else
            echo "INFO: pointer $POINTER references basename '$BASENAME' but sibling $SIBLING is missing — falling through to legacy lookup"
        fi
    fi
fi
```

If Step 0.5 returned a resume (exit 0 above), we're done. Otherwise the
remaining steps below handle the legacy `state/pending-resume-*.txt` path.

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

# Re-derive SESSION_ID: separate bash blocks don't share variables, so the
# value Step 0 set is empty here. Newest JSONL in this project's dir = the
# current (post-/clear) session.
JSONL=$(ls -t "$PROJECT_DIR"/*.jsonl 2>/dev/null | head -1)
test -n "$JSONL" || { echo "ERROR: no JSONL in $PROJECT_DIR — refusing to inject"; exit 1; }
SESSION_ID=$(basename "$JSONL" .jsonl)

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
    echo ""
    echo "─── Available handoff-paired resume siblings (newest 5) ───"
    # Pick-from-list fallback: when neither the per-PID pointer (Step 0.5) nor
    # the legacy pending-resume (Step 1) produced a match, surface available
    # .resume.md siblings in memory/handoffs/ so the user can manually open one
    # and paste. Doesn't auto-inject — that would risk loading the wrong context.
    found=0
    while IFS= read -r SIBLING; do
        [[ -z "$SIBLING" ]] && continue
        BASENAME=$(basename "$SIBLING" .resume.md)
        SIZE=$(wc -l < "$SIBLING" | tr -d ' ')
        MTIME=$(stat -f '%Sm' -t '%Y-%m-%d %H:%M' "$SIBLING" 2>/dev/null)
        echo "  $MTIME  ${SIZE}L  $SIBLING"
        found=$((found + 1))
        [[ $found -ge 5 ]] && break
    done < <(ls -t memory/handoffs/*.resume.md 2>/dev/null)
    if [[ $found -eq 0 ]]; then
        echo "  (none — no handoff-paired siblings exist in memory/handoffs/ for this project)"
    else
        echo ""
        echo "To resume manually: \`cat <path>\` and paste into the conversation."
    fi
    exit 1
fi
# Record which session_id owned this resume (for cleanup + Step 5 guard).
RESUME_SID=$(basename "$RESUME" .txt | sed 's/^pending-resume-//')

# Persist the resolved RESUME path + RESUME_SID to a per-session sidecar so the
# following bash blocks (Steps 2–5, each its OWN shell) can recover them without
# re-running this whole lookup. Each block re-reads this sidecar instead of
# relying on shell-variable persistence (which does NOT exist across blocks).
HANDOFF_SIDECAR="$STATE/.resume-skill-context-${SESSION_ID}"
printf 'RESUME=%s\nRESUME_SID=%s\n' "$RESUME" "$RESUME_SID" > "$HANDOFF_SIDECAR"
```

### Step 2: Show preview

Each bash block runs in its own shell. Re-derive `$STATE` / `$SESSION_ID` and
recover `$RESUME` / `$RESUME_SID` from the Step 1 sidecar at the top of every
remaining block.

```bash
STATE="$HOME/Library/Application Support/acos-token-monitor/state"
PROJECT_DIR="$HOME/.claude/projects/$(pwd | tr '/' '-' | tr ' ' '-' | tr '.' '-')"
JSONL=$(ls -t "$PROJECT_DIR"/*.jsonl 2>/dev/null | head -1)
SESSION_ID=$(basename "$JSONL" .jsonl 2>/dev/null)
SIDECAR="$STATE/.resume-skill-context-${SESSION_ID}"
test -s "$SIDECAR" || { echo "ERROR: Step 1 sidecar missing ($SIDECAR) — re-run from Step 1"; exit 1; }
# shellcheck disable=SC1090
source "$SIDECAR"   # restores RESUME and RESUME_SID
test -s "$RESUME" || { echo "ERROR: resolved resume file $RESUME is empty/missing"; exit 1; }

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
STATE="$HOME/Library/Application Support/acos-token-monitor/state"
PROJECT_DIR="$HOME/.claude/projects/$(pwd | tr '/' '-' | tr ' ' '-' | tr '.' '-')"
JSONL=$(ls -t "$PROJECT_DIR"/*.jsonl 2>/dev/null | head -1)
SESSION_ID=$(basename "$JSONL" .jsonl 2>/dev/null)

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
STATE="$HOME/Library/Application Support/acos-token-monitor/state"
PROJECT_DIR="$HOME/.claude/projects/$(pwd | tr '/' '-' | tr ' ' '-' | tr '.' '-')"
JSONL=$(ls -t "$PROJECT_DIR"/*.jsonl 2>/dev/null | head -1)
SESSION_ID=$(basename "$JSONL" .jsonl 2>/dev/null)
SIDECAR="$STATE/.resume-skill-context-${SESSION_ID}"
test -s "$SIDECAR" || { echo "ERROR: Step 1 sidecar missing ($SIDECAR) — re-run from Step 1"; exit 1; }
# shellcheck disable=SC1090
source "$SIDECAR"   # restores RESUME and RESUME_SID
test -s "$RESUME" || { echo "ERROR: resolved resume file $RESUME is empty/missing"; exit 1; }

INJECTOR="$HOME/Library/Application Support/acos-token-monitor/bin/inject-keystroke.py"
# For a manual resume we skip verification — this is the user explicitly
# requesting injection, not a /clear that we need to confirm took effect.
# Capture rc + stdout: a FAILED injection must NOT let Step 5 consume the
# recovery artifacts (otherwise a botched fire silently destroys the only
# copy of the resume prompt).
INJECT_OUT=$(cat "$RESUME" | python3 "$INJECTOR" --from-stdin --session-id "$RESUME_SID" --no-verify 2>&1)
INJECT_RC=$?
echo "$INJECT_OUT"

# Record the rc into the sidecar so Step 5 (its own shell) can gate on it.
printf 'INJECT_RC=%s\n' "$INJECT_RC" >> "$SIDECAR"

if [[ $INJECT_RC -ne 0 ]]; then
    echo "ERROR: injection failed rc=$INJECT_RC — resume content is STILL at:"
    echo "       $RESUME"
    echo "       Paste it manually: \`cat \"$RESUME\"\` and paste into the conversation."
    echo "       Step 5 will be SKIPPED — artifacts are preserved for retry."
    exit 1
fi
echo "OK: injection succeeded (rc=0)."
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
# Re-derive Step-0/1 vars (separate shell) + recover sidecar state.
STATE="$HOME/Library/Application Support/acos-token-monitor/state"
PROJECT_DIR="$HOME/.claude/projects/$(pwd | tr '/' '-' | tr ' ' '-' | tr '.' '-')"
test -d "$PROJECT_DIR" || { echo "ERROR: no Claude Code project dir for cwd $(pwd)"; exit 1; }
JSONL=$(ls -t "$PROJECT_DIR"/*.jsonl 2>/dev/null | head -1)
SESSION_ID=$(basename "$JSONL" .jsonl 2>/dev/null)
SIDECAR="$STATE/.resume-skill-context-${SESSION_ID}"
test -s "$SIDECAR" || { echo "ERROR: Step 1 sidecar missing ($SIDECAR) — re-run from Step 1"; exit 1; }
# shellcheck disable=SC1090
source "$SIDECAR"   # restores RESUME, RESUME_SID, INJECT_RC

# Hard gate: only consume artifacts if Step 4 confirmed a successful injection.
# (Step 4 already exit 1's on failure, but if these blocks are run out of order
# this guard prevents destroying the recovery artifacts after a failed fire.)
if [[ "${INJECT_RC:-1}" != "0" ]]; then
    echo "ERROR: INJECT_RC=${INJECT_RC:-unset} — injection did not succeed."
    echo "       Refusing to consume artifacts; resume content stays at $RESUME"
    exit 1
fi

# Rebuild this project's session set for the cross-contamination guard below.
PROJECT_SESSIONS=$(ls "$PROJECT_DIR"/*.jsonl 2>/dev/null | xargs -I{} basename {} .jsonl 2>/dev/null)

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

# Remove the Step-1 sidecar — it was scratch state for cross-block recovery and
# must not linger to mislead a future invocation.
rm -f "$SIDECAR"
```

### Step 6: Report

Print injector return code, success message, and reminder that the resume
prompt has been consumed (subsequent invocations will fail with "no pending
resume" until the next eternity-protocol cycle generates a new one).

---

*ACOS Eternity Protocol Resume — primary resume path for Warp; manual fallback for cmux.*
