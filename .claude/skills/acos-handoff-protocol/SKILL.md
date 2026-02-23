---
name: acos-handoff-protocol
description: Creates a session handoff document capturing current state for future sessions. Partially automated by agent memory persistence.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep
---

# ACOS Handoff Protocol

## Overview

This skill creates a session handoff document that captures the current state for continuity in future sessions. With native agent `memory: project`, much of this context persists automatically — handoff documents now serve primarily as an audit trail and for structured context sharing.

### Pre-flight: Auto-Bootstrap

Before proceeding, ensure ACOS is initialized in this project:

```bash
bash .claude/scripts/acos-preflight.sh
```

This is idempotent — it exits immediately if ACOS is already initialized. If not, it runs the full bootstrap (symlinks, directories, config, gitignore).

## Protocol

### Step 1: Gather Session Context

Collect information about the current session:
- What slice/story/epic was being worked on
- What was accomplished this session
- What decisions were made
- What is the current state
- What should happen next
- Any blockers or questions

### Step 2: Create Handoff Document

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

### Step 3: Save

Write to `memory/handoffs/[timestamp]-session-handoff.yaml`
Confirm save to user.

### Step 4: Auto-Continue at High Context

After saving the handoff, check the current token usage. If context is at or above **60%** (~120k tokens), automatically invoke `/acos-continue` to seamlessly launch a fresh session with the handoff pre-loaded.

This ensures the handoff protocol doesn't just save state — it acts on it. At 60%+ context, there's no reason to stay in a degraded session.

If context is below 60%, simply confirm the handoff was saved and continue working in the current session.

---

*ACOS Handoff - Continuity across sessions.*
