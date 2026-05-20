---
name: acos-eternity-protocol-resume
description: Manually injects the pending resume prompt into the active Warp pane. Fallback for when the daemon-driven post-clear resume injection didn't fire. Reads ~/Library/Application Support/acos-token-monitor/state/pending-resume-<session_id>.txt and uses inject-keystroke.py with --pid for precise targeting.
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

### Step 1: Locate pending resume file

First look for one keyed to the *current* session ID. If absent, fall back to
the most recent `pending-resume-*.txt` (this is the common case — the resume
file is keyed to the PRE-/clear session ID, while this skill runs in the
POST-/clear session with a new ID).

```bash
STATE="$HOME/Library/Application Support/acos-token-monitor/state"
RESUME="$STATE/pending-resume-${SESSION_ID}.txt"
if [[ ! -s "$RESUME" ]]; then
    RESUME=$(ls -t "$STATE"/pending-resume-*.txt 2>/dev/null | head -1)
fi
test -s "$RESUME" || { echo "ERROR: no pending resume found"; exit 1; }
# Record which session_id owned this resume (for cleanup)
RESUME_SID=$(basename "$RESUME" .txt | sed 's/^pending-resume-//')
```

### Step 2: Show preview

```bash
echo "─── About to inject this resume prompt ───"
head -6 "$RESUME"
echo "─── (full prompt: $(wc -l < "$RESUME") lines) ───"
```

### Step 3: Read PID for targeted injection (PID-targeted ONLY)

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
