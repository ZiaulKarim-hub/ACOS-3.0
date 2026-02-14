---
name: acos-complete
description: Marks all active handoffs as completed and archives them. Use when a milestone is finished and you want the next session to start with a clean context.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Bash
---

# ACOS Complete

## Overview

Marks the current work as complete and archives all active handoffs. The next session will start with a clean context — no prior handoffs auto-loaded.

Completed handoffs are moved to `memory/handoffs/archive/` where they remain searchable by the memory-agent via RAG but are no longer auto-injected into new sessions.

**Key guarantee**: Every `/acos-complete` invocation ensures the current session is documented before closing. If no handoff exists for this session's work, one is created automatically.

## Protocol

### Step 1: Assess Current Session

Review the conversation context to identify what was accomplished in this session:
- What files were created or modified
- What decisions were made
- What is the current project state
- What should happen next

### Step 2: Check for Existing Current-Session Handoff

Read all `memory/handoffs/*.yaml` files to determine if any existing handoff already captures this session's work.

A handoff captures the current session if it references the same accomplishments, files, and decisions from this session. Also check `.acos/state/handoff-triggered-*` markers as a secondary signal that the Stop hook auto-created a handoff.

**Decision criteria:**
- If an existing handoff clearly describes this session's work → skip creation, proceed to Step 4
- If no handoff covers this session → proceed to Step 3

### Step 3: Create Completion Handoff

Create a handoff for the current session using this format:

```yaml
timestamp: "[ISO timestamp]"
status: "completed"
session_summary: "[Brief description of what was done]"

current_work:
  slice_id: "[SLICE-XXX or null]"
  story_id: "[STORY-XXX or null]"
  epic_id: "[EPIC-XXX or null]"
  status: "completed"

completed_this_session:
  - "[Specific accomplishment 1]"
  - "[Specific accomplishment 2]"

files_modified:
  - path: "[file path]"
    changes: "[what changed]"

decisions_made:
  - "[Decision and rationale]"

blockers: []

next_actions:
  - "[Clear next step 1]"
  - "[Clear next step 2]"

context_for_next_session: |
  [Any important context the next session needs]
```

Write to `memory/handoffs/[YYYY-MM-DD]-completion-handoff.yaml`.

Note: This handoff is created with `status: "completed"` immediately — it is a closing record, not a continuation handoff.

### Step 4: Mark Remaining Active Handoffs as Completed

Search `memory/handoffs/*.yaml` for files with a top-level `status: "active"` field or no status field (legacy handoffs treated as active).

Skip files that already have `status: "completed"` or `status: "mechanical"`.

For each active handoff found:
- If it has a top-level `status:` field, change its value to `"completed"`
- If it has no top-level `status:` field, add `status: "completed"` on the line after `timestamp:`

### Step 5: Move to Archive

Create `memory/handoffs/archive/` if it doesn't exist.

Move all completed handoffs (including the one created in Step 3) to the archive directory:
```bash
mkdir -p memory/handoffs/archive
mv memory/handoffs/<filename>.yaml memory/handoffs/archive/
```

### Step 6: Cleanup

Remove stale session markers from `.acos/state/`:
```bash
rm -f .acos/state/handoff-triggered-*
```

### Step 7: Confirm

Report to the user:
- Whether a new completion handoff was created for this session (Step 3) or an existing one was found (Step 2)
- How many total handoffs were archived
- The filenames that were moved
- Confirm that the next session will start with clean context

---

*ACOS Complete — Close a milestone and start fresh.*
