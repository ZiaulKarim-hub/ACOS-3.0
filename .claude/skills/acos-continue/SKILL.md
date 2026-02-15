---
name: acos-continue
description: Creates a session handoff and seamlessly continues work in a fresh context window. Use when context is getting high or you want a clean slate.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Skill
---

# ACOS Continue — Seamless Session Continuation

## Overview

This skill creates a session handoff document and launches a fresh Claude session that will automatically load the handoff. Use it when:
- Context window is getting high and you want to proactively transition
- You want a clean context slate while preserving all state
- The token-gate warns you to wrap up

**Key difference from `/acos-handoff-protocol`:** This skill doesn't just save the handoff — it also launches a new session to continue the work automatically.

### Pre-flight: Auto-Bootstrap

Before proceeding, ensure ACOS is initialized in this project:

```bash
bash .claude/scripts/acos-preflight.sh
```

## Protocol

### Step 1: Create the Handoff

Follow the `/acos-handoff-protocol` to create a full semantic handoff:

1. Gather session context:
   - What slice/story/epic was being worked on
   - What was accomplished this session
   - What decisions were made
   - Current state and blockers
   - Clear next actions

2. Write the handoff document to `memory/handoffs/[timestamp]-session-handoff.yaml`:

```yaml
timestamp: "[ISO timestamp]"
status: "active"
session_summary: "[Brief description of what was done]"

current_work:
  slice_id: "[SLICE-XXX]"
  story_id: "[STORY-XXX]"
  epic_id: "[EPIC-XXX]"
  status: "[in_progress | blocked | ready_for_review | completed]"

completed_this_session:
  - "[Specific accomplishment 1]"
  - "[Specific accomplishment 2]"

files_modified:
  - path: "[file path]"
    changes: "[what changed]"

decisions_made:
  - "[Decision and rationale]"

blockers:
  - "[Any blocking issues]"

next_actions:
  - "[Clear next step 1]"
  - "[Clear next step 2]"

context_for_next_session: |
  [Any important context the next session needs]
```

### Step 2: Launch Continuation

After the handoff is saved, run the continuation script:

```bash
bash .claude/scripts/session-continue.sh
```

This launches a detached background process that will start a fresh Claude session after a brief delay. The new session's `auto-load-handoff.sh` SessionStart hook will automatically inject the handoff context.

### Step 3: Inform and End

Tell the user:
- The handoff has been saved (show the filename)
- A new session will start automatically in ~5 seconds
- They can also manually run `claude` if the auto-start doesn't work

Then STOP responding. Do not make any more tool calls. The current session must end so the new session can take over the terminal.

---

*ACOS Continue — Seamless transitions between context windows.*
