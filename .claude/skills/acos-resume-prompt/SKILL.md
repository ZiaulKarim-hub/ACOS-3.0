---
name: acos-resume-prompt
description: Generates a per-session one-shot resume prompt from the latest handoff, intended for auto-injection after a /clear or /compact reset (the cmux eternity flow uses /compact as of 2026-08-09). Lets a freshly-reset Claude session pick up the prior work seamlessly, now including the user's own last real message verbatim alongside the summary. Used standalone or as a step inside acos-eternity-protocol.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Glob, Bash
---

# ACOS Resume Prompt

## Overview

Reads the most recent handoff and produces a tight, self-contained "resume" prompt
that references it. Output is saved per-session to:

`~/Library/Application Support/acos-token-monitor/state/pending-resume-<session_id>.txt`

The post-reset AI receives the resume prompt as if the user had typed it, reads
the referenced handoff, and continues the prior work without losing context.

## Protocol

### Step 1: Locate the latest handoff

```bash
# 2026-08-09: selection now goes through the shared
# resolve-session-handoff.sh, matched against THIS session's own id —
# not just "whichever handoff is newest" (the old rule, which could select
# a DIFFERENT concurrent session's handoff; see
# .claude/scripts/resolve-session-handoff.sh for the full history). This
# also fixes Step 2.5 below, which used to independently re-derive
# SESSION_ID with an older, unscoped heuristic — it now reuses the
# session_id resolved here instead of guessing again.
# (This fix previously landed only in the project-local copy of this skill;
# synced here to the global copy the same day so the two can't drift again.)
SESSION_ID=$(bash .claude/scripts/resolve-session-id.sh)
test -n "$SESSION_ID" || { echo "ERROR: could not determine session_id"; exit 1; }
HANDOFF=$(bash .claude/scripts/resolve-session-handoff.sh "$SESSION_ID")
test -n "$HANDOFF" || { echo "ERROR: no handoff exists matching session_id '$SESSION_ID' — run /acos-handoff first"; exit 1; }
```

### Step 2: Extract key fields from handoff

Read the handoff and extract:
- `session_summary` — what was being worked on
- `completed_this_session[0]` — last meaningful action
- `next_actions[0]` — next step
- `blockers` — any open blockers

### Step 2.5: Build the in-flight subagent registry

Walk the active session JSONL to find any `Task()` invocations that were
spawned but have not yet returned a result.

```bash
SESSION_DIR="$HOME/.claude/projects/$(pwd | tr '/' '-' | tr ' ' '-' | tr '.' '-')"
# 2026-08-09 fix: this step used to re-derive SESSION_ID with
# `basename "$(ls -t "$SESSION_DIR"/*.jsonl | head -1)"` — the OLD,
# already-known-broken pattern (racy in a project worked on by several
# concurrent Claude sessions), never upgraded when the rest of this file got
# the session-scoped fix. It now calls the same shared resolver as Step 1
# (a separate call, not a reused variable — each fenced bash block in this
# skill runs in its own shell, so state doesn't carry over between steps).
SESSION_ID=$(bash .claude/scripts/resolve-session-id.sh)
[[ -n "$SESSION_ID" ]] || { echo "ERROR: could not determine session_id"; exit 1; }
JSONL="$SESSION_DIR/$SESSION_ID.jsonl"
```

Run this Python walk to identify in-flight Tasks — but ONLY if the JSONL
resolved (`[[ -s "$JSONL" ]]`). This step is best-effort enrichment: if the
session JSONL can't be found, SKIP the walk and continue with an empty
subagent registry rather than aborting (Step 1 already guaranteed a handoff).
NOTE: `"$JSONL"` below is a shell-variable placeholder, not literal Python —
substitute the resolved path from the bash block above (e.g. run the snippet
via `python3 - <<EOF` with an UNQUOTED heredoc delimiter so the shell
interpolates it, or inline the path):

```python
import json
spawned = {}
completed = set()
with open("$JSONL") as f:
    for line in f:
        try: d = json.loads(line.strip())
        except: continue
        msg = d.get("message", {}) or {}
        ts = d.get("timestamp", "")
        for block in (msg.get("content") or []):
            if not isinstance(block, dict): continue
            btype = block.get("type")
            if btype == "tool_use" and block.get("name") == "Task":
                inp = block.get("input", {}) or {}
                spawned[block.get("id")] = {
                    "spawned_at": ts,
                    "subagent_type": inp.get("subagent_type", "general-purpose"),
                    "description": inp.get("description", ""),
                    "prompt_excerpt": (inp.get("prompt") or "")[:300],
                }
            elif btype == "tool_result":
                completed.add(block.get("tool_use_id"))

active = {tid: meta for tid, meta in spawned.items() if tid not in completed}
```

### Step 2.6: Check for goals to carry forward (2026-08-08)

`/clear` silently drops BOTH kinds of "keep working toward X" state below —
neither survives on its own. Whether `/compact` also drops them has not been
confirmed either way (unlike `/clear`, it keeps the same session, so the goal
COULD plausibly survive on its own) — this step re-arms regardless, since
retyping an already-active goal is a safe, cheap no-op-ish action, not a new
risk. Check for each, and carry forward whatever is active. This step is
best-effort: if a check errors or a tool isn't available, skip that one goal
type and continue — never abort the resume prompt over this.

**Autopilot goal** — check whether a session-scoped sentinel exists for THIS
session (path is relative to the project root, same `cwd` assumption as Step
2.5):

```bash
AP_SENTINEL=".acos/state/autopilot-active-${SESSION_ID}"
test -f "$AP_SENTINEL" && cat "$AP_SENTINEL"
```

If it exists, read the JSON and capture `goal`, `goal_file` (if present), and
`max_iterations` (so a goal that was set with a raised cap, like 1000, doesn't
silently fall back to the 150 default on restart).

**Real `/goal` command** — run `/goal` with no arguments to check status. If it
reports an active goal (not "No goal set"), capture the condition text exactly
as shown — verbatim, do not paraphrase it.

If EITHER was found, carry it into Step 3's new "GOALS TO CARRY FORWARD"
section below. If NEITHER was found, omit that section entirely.

**Persist a machine-typeable re-arm command for native `/goal` (2026-08-08):**
the prose section below is delivered as hook `additionalContext` — background
information, not typed input. A `/goal <condition>` line inside it is read as
words, never runs as a command (slash commands only parse from real typed
input). The cmux in-pane Stop hook (`eternity-cmux-inpane.sh`) fixes this by
actually TYPING the command after the reset, but it needs the exact line to
type, on its own, with no surrounding prose. So — ONLY when a native `/goal`
condition was found above (never for an autopilot-only goal; autopilot's own
re-arm is a shell command Claude runs from reading the prose, which already
works) — also write it to a dedicated single-line file:

```bash
if [ -n "$GOAL_CONDITION" ]; then
    GOAL_REARM_FILE="$HOME/Library/Application Support/acos-token-monitor/state/.goal-rearm-${SESSION_ID}"
    # One line only — this file gets typed verbatim as a single command. Strip
    # any embedded newlines from the captured condition. Setting /goal starts
    # a turn immediately using the condition as the prompt, and that turn gets
    # NO other context (slash commands bypass additionalContext/UserPromptSubmit)
    # — so the condition must be self-sufficient. Point it at the handoff.
    CLEAN_CONDITION=$(printf '%s' "$GOAL_CONDITION" | tr '\n\r' '  ')
    printf '/goal read `%s` first, then: %s' "$HANDOFF" "$CLEAN_CONDITION" > "$GOAL_REARM_FILE"
fi
```

### Step 2.7: Capture the user's exact last real message (2026-08-09)

The summary in Step 2 is a paraphrase — a reworded version of what happened.
A paraphrase can drift from what the user actually asked. This step adds the
user's OWN words, verbatim, alongside the summary — not instead of it — so a
still-open question survives in the exact form it was asked, not a
reconstruction of it.

**"Real" excludes a lot that also carries `role: user` in the transcript.**
Several things are stored with that same role but were never typed by a
person: a hook's own rewrite request ("Stop hook feedback: ..."), a slash
command's expanded body (`<command-message>`/`<command-name>` wrapper), a
background task finishing (`<task-notification>`), injected background
context (`<system-reminder>`), and a tool result being fed back (content
blocks that are all `type: tool_result`, not typed text). Walking backward
and grabbing the literal last `role: user` entry would very often grab one of
these instead of anything the user actually wrote.

```bash
SESSION_DIR="$HOME/.claude/projects/$(pwd | tr '/' '-' | tr ' ' '-' | tr '.' '-')"
SESSION_ID=$(bash .claude/scripts/resolve-session-id.sh)
[[ -n "$SESSION_ID" ]] || { echo "ERROR: could not determine session_id"; exit 1; }
JSONL="$SESSION_DIR/$SESSION_ID.jsonl"
```

```python
import json, re

LAST_MSG = ""
LAST_MSG_TRUNCATED = False
# 2026-08-17: brought back into REAL sync with
# .claude/scripts/precompact-handoff.ts. That file's comment claimed the two
# lists were "kept in sync deliberately" — they were not. The hook carried three
# entries this list lacked, and NEITHER carried "Skill /". A re-invoked skill is
# replayed as a role:"user" turn reading "Skill /<name> was loaded earlier ...
# this is a NEW invocation"; it was recorded live as Zee's last words in the
# Research to Portfolio handoff. Change one list, change the other.
SYNTHETIC_PREFIXES = (
    "<local-command-caveat>", "<command-message>", "<command-name>",
    "<task-notification>", "<system-reminder>", "<local-command-stdout>",
    "Stop hook feedback:", "[SYSTEM NOTIFICATION",
    "Base directory for this skill:", "ARGUMENTS:",
    "Resume the eternity-protocol handoff",
    "Skill /",
)
MAX_CHARS = 2000  # ~500 tokens; the base prompt budget below still applies

try:
    with open("$JSONL") as f:
        lines = f.readlines()
except OSError:
    lines = []

for line in reversed(lines):
    try:
        d = json.loads(line.strip())
    except Exception:
        continue
    msg = d.get("message", {}) or {}
    if msg.get("role") != "user":
        continue
    content = msg.get("content")
    if isinstance(content, list):
        # Skip pure tool-result turns (not something a person typed) —
        # only accept if at least one block is real, non-empty text.
        text_blocks = [b.get("text", "") for b in content
                       if isinstance(b, dict) and b.get("type") == "text"]
        if not text_blocks or all(not t.strip() for t in text_blocks):
            continue
        text = "\n".join(t for t in text_blocks if t.strip())
    elif isinstance(content, str):
        text = content
    else:
        continue
    text = text.strip()
    if not text:
        continue
    if any(text.startswith(p) for p in SYNTHETIC_PREFIXES):
        continue
    # Found the real one.
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]
        LAST_MSG_TRUNCATED = True
    LAST_MSG = text
    break

# Written to a side-file, not stdout — Step 3 reads it back. Keeping it out of
# the model's own turn output avoids re-typing a possibly-long message twice.
with open("$STATE/.last-user-message-${SESSION_ID}", "w") as f:
    f.write(LAST_MSG)
    if LAST_MSG_TRUNCATED:
        f.write("\n\n[...cut off at 2000 characters]")
print(f"Captured last real user message: {len(LAST_MSG)} chars"
      + (" (truncated)" if LAST_MSG_TRUNCATED else "")
      if LAST_MSG else "No real user message found (session may be entirely autonomous work) — omitting section")
```

If nothing was captured (a fully autonomous session with no direct human
turns since the last handoff), omit the section in Step 3 entirely — an
absent section is honest; an invented one is not.

### Step 3: Write the resume prompt to disk

Save to `~/Library/Application Support/acos-token-monitor/state/pending-resume-<session_id>.txt`
with this shape:

```
Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `<handoff-path>` for full session state.

Quick summary:
- Working on: <one-sentence topic>
- Last action: <last action>
- Next step: <first next_action>
- Blockers: <list, or "none">

<IF Step 2.7 captured a real last user message, append this section:>
YOUR LAST MESSAGE BEFORE THIS RESET (exact words, not a paraphrase):

  <the captured text, verbatim>

If this looks like it's still an open question — answer it directly, first.
But check it's not already answered before diving in: real work may have
happened, and been completed, between when this was typed and when this
reset fired. Verify against the real state on disk, don't assume this is
still pending just because it's the last thing you see here.

<IF a goal was found in Step 2.6, append this section:>
GOALS TO CARRY FORWARD — a reset does not keep these; you must restart them
yourself, as your very first action, before anything else:

  <IF an autopilot goal was found:>
  - AUTOPILOT GOAL was active. Run this first:
      bash .claude/scripts/autopilot-activate.py on "<goal text, exact>" --goal-file <goal_file> --max-iter <max_iterations>
    (drop --goal-file entirely if none was set; always keep --max-iter, using
    the exact number captured in Step 2.6, so a raised cap like 1000 is not
    silently lost back to the 150 default)

  <IF a /goal condition was found:>
  - A /goal CONDITION was active: "<condition text, exact>"
    Run this first: /goal <condition text, exact>

IMPORTANT: do not assume progress matches what any summary above says. Go
verify the REAL current state yourself first (recount files, re-check the
repo, re-run whatever the goal's condition depends on) before continuing the
work. A freshly reset chat has no memory of exactly how much was already
done — trust the real state on disk, not a remembered number.

<IF active subagents found in Step 2.5, append this section:>
IN-FLIGHT SUBAGENTS AT RESET TIME:
The following Task() invocations were running and had NOT returned when this
reset fired. Their tool_result blocks may land in this conversation after this
resume prompt. If they do — DO NOT discard them as orphaned.

  <for each active task:>
  - tool_use_id: <id>
    spawned_at: <timestamp>
    type: <subagent_type>
    description: <description>
    prompt_excerpt: <first 300 chars of prompt>

When a tool_result with one of these tool_use_ids arrives:
1. Match it to the entry above
2. Save the result content to `.acos/evidence/<slice-id>/subagent-<short-id>.md`
3. Note in your reply that a deferred subagent result was integrated
4. Update planning/evidence per the work the subagent was doing

This prompt was auto-injected after a reset ran. The user has not typed
anything since. Read the handoff document and continue the prior work
seamlessly.
```

The output path MUST be:
`$HOME/Library/Application Support/acos-token-monitor/state/pending-resume-${SESSION_ID}.txt`

Do NOT write to `.acos/state/...` — that path is wrong; the daemon reads from
the Application Support state dir.

Keep the base prompt under 400 tokens. Registry section adds ~150 tokens per
active subagent — if many are active, write to side-file at
`pending-resume-registry-<session_id>.yaml` and reference it. The Step 2.7
last-message section adds up to ~500 tokens on top of the base budget (capped
at 2000 characters in Step 2.7 itself) — this is deliberately outside the
400-token base budget, the same way the subagent registry is.

### Step 4: Report

Print:
- Path to the handoff used
- Path to the resume prompt (per-session)
- Token-count estimate of the resume prompt (chars / 3)
- First 5 lines as preview
- Whether a goal was found and carried forward, and which kind (autopilot,
  `/goal`, both, or neither)
- If a native `/goal` condition was found, the path of the `.goal-rearm-<sid>`
  file written for the in-pane Stop hook to type after the reset
- Whether a real last user message was captured (Step 2.7), and its length

---

*ACOS Resume Prompt — bridges handoff and post-reset session.*
