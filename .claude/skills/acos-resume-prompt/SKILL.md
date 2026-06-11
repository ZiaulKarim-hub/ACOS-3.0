---
name: acos-resume-prompt
description: Generates a per-session one-shot resume prompt from the latest handoff, intended for auto-injection after /clear. Lets a freshly-cleared Claude session pick up the prior work seamlessly. Used standalone or as a step inside acos-eternity-protocol.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Glob, Bash
---

# ACOS Resume Prompt

## Overview

Reads the most recent handoff and produces a tight, self-contained "resume" prompt
that references it. Output is saved per-session to:

`~/Library/Application Support/acos-token-monitor/state/pending-resume-<session_id>.txt`

The post-clear AI receives the resume prompt as if the user had typed it, reads
the referenced handoff, and continues the prior work without losing context.

## Protocol

### Step 1: Locate the latest handoff

```bash
HANDOFF=$(ls -t memory/handoffs/*.md memory/handoffs/*.yaml memory/handoffs/*.yml 2>/dev/null | grep -v '\.resume\.md$' | head -1)
test -n "$HANDOFF" || { echo "ERROR: no handoff exists — run /acos-handoff first"; exit 1; }
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
JSONL=$(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null | head -1)
SESSION_ID=$(basename "$JSONL" .jsonl)
```

Run this Python walk to identify in-flight Tasks (use the variables above):

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

<IF active subagents found in Step 2.5, append this section:>
IN-FLIGHT SUBAGENTS AT CLEAR TIME:
The following Task() invocations were running and had NOT returned when /clear
fired. Their tool_result blocks may land in this conversation after this resume
prompt. If they do — DO NOT discard them as orphaned.

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

This prompt was auto-injected after /clear ran. The user has not typed anything
since. Read the handoff document and continue the prior work seamlessly.
```

The output path MUST be:
`$HOME/Library/Application Support/acos-token-monitor/state/pending-resume-${SESSION_ID}.txt`

Do NOT write to `.acos/state/...` — that path is wrong; the daemon reads from
the Application Support state dir.

Keep the base prompt under 400 tokens. Registry section adds ~150 tokens per
active subagent — if many are active, write to side-file at
`pending-resume-registry-<session_id>.yaml` and reference it.

### Step 4: Report

Print:
- Path to the handoff used
- Path to the resume prompt (per-session)
- Token-count estimate of the resume prompt (chars / 3)
- First 5 lines as preview

---

*ACOS Resume Prompt — bridges handoff and post-clear session.*
