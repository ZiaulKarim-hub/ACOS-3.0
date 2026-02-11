---
name: acos-complete
description: Marks all active handoffs as completed and archives them. Use when a milestone is finished and you want the next session to start with a clean context.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Edit, Glob, Bash
---

# ACOS Complete

## Overview

Marks the current work as complete and archives all active handoffs. The next session will start with a clean context — no prior handoffs auto-loaded.

Completed handoffs are moved to `memory/handoffs/archive/` where they remain searchable by the memory-agent via RAG but are no longer auto-injected into new sessions.

## Protocol

### Step 1: Find Active Handoffs

Search `memory/handoffs/*.yaml` for files with a top-level `status: "active"` field or no status field (legacy handoffs treated as active).

Skip files that already have `status: "completed"` or `status: "mechanical"`.

### Step 2: Mark as Completed

For each active handoff found:
- If it has a top-level `status:` field, change its value to `"completed"`
- If it has no top-level `status:` field, add `status: "completed"` on the line after `timestamp:`

### Step 3: Move to Archive

Create `memory/handoffs/archive/` if it doesn't exist.

Move all newly-completed handoffs to the archive directory:
```bash
mkdir -p memory/handoffs/archive
mv memory/handoffs/<filename>.yaml memory/handoffs/archive/
```

### Step 4: Confirm

Report to the user:
- How many handoffs were archived
- The filenames that were moved
- Confirm that the next session will start with clean context

---

*ACOS Complete — Close a milestone and start fresh.*
