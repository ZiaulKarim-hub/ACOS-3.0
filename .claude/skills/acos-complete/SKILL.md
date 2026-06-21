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

Read all active handoffs to determine if any existing handoff already captures this session's work. Handoffs are emitted as `.md` (current format) with legacy `.yaml` also possible, so glob BOTH extensions and exclude `.resume.md` sibling files (a resume copy is never the handoff itself):

```bash
ls -t memory/handoffs/*.md memory/handoffs/*.yaml 2>/dev/null | grep -v '\.resume\.md$'
```

A handoff captures the current session if it references the same accomplishments, files, and decisions from this session.

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

Search both `.md` and `.yaml` handoffs (excluding `.resume.md` siblings) for files with a top-level `status: "active"` field or no status field (legacy handoffs treated as active):

```bash
ls -t memory/handoffs/*.md memory/handoffs/*.yaml 2>/dev/null | grep -v '\.resume\.md$'
```

Skip files that already have `status: "completed"`. Files with `status: "mechanical"` (PreCompact-created) are ALSO marked completed and archived here — a finished milestone supersedes them, and leaving them behind would violate the clean-context guarantee this skill makes.

For each active or mechanical handoff found (the `status:` field lives in the YAML front-matter block of a `.md` handoff, or at the top level of a `.yaml` handoff):
- If it has a top-level/front-matter `status:` field, change its value to `"completed"`
- If it has no `status:` field, add `status: "completed"` on the line after `timestamp:`

### Step 5: Move to Archive

Create `memory/handoffs/archive/` if it doesn't exist.

Move all completed handoffs (including the one created in Step 3) to the archive directory. Move the actual handoff files (`.md` and `.yaml`) but NOT `.resume.md` sibling files (those are per-session resume copies the eternity protocol still needs and must be preserved):
```bash
mkdir -p memory/handoffs/archive
# Move each completed handoff by name (.md or .yaml); never move *.resume.md
mv memory/handoffs/<filename> memory/handoffs/archive/
```

After each move, check for a paired resume sibling (`memory/handoffs/<basename>.resume.md` — same basename, `.resume.md` extension). If one exists, rewrite any occurrence of the handoff's OLD path inside it (`memory/handoffs/<filename>`) to the new archive path (`memory/handoffs/archive/<filename>`). The sibling embeds an absolute "Read `<handoff path>`" pointer written by the eternity protocol; without this rewrite, a later eternity resume would instruct the fresh session to Read a path that no longer exists. Do NOT move or delete the sibling itself — per-PID pointers reference it in place:

```bash
# <filename> = the handoff just moved; sibling stays in place, path rewritten
SIBLING="memory/handoffs/${filename%.*}.resume.md"
if [ -f "$SIBLING" ]; then
  python3 - "$SIBLING" "$filename" <<'PY'
import sys, pathlib
sib, fname = pathlib.Path(sys.argv[1]), sys.argv[2]
text = sib.read_text()
new = text.replace(f"memory/handoffs/{fname}", f"memory/handoffs/archive/{fname}")
if new != text:
    sib.write_text(new)
PY
fi
```

### Step 6: Cleanup

Remove any stale legacy session markers from `.acos/state/` (defensive cleanup — the currently registered Stop hook is `autopilot-stop-handler.py`, which does not write `handoff-triggered-*` markers; this rm only clears residue from older hook generations):
```bash
rm -f .acos/state/handoff-triggered-*
```

### Step 7: Confirm

Report to the user:
- Whether a new completion handoff was created for this session (Step 3) or an existing one was found (Step 2)
- How many total handoffs were archived
- The filenames that were moved
- Confirm that the next session will start with clean context

### Step 8: Exit Session (auto-typed `/exit`)

After confirmation, automatically close the session. The completion is the final
action — there is no reason to continue after archiving.

A skill cannot type `/exit` into its own terminal mid-turn — the same constraint
the eternity protocol works around for `/clear`: cmux's socket only accepts
connections from a process running *inside* a live pane, and the keystroke has to
land *after* the current turn ends. So this step reuses the eternity in-pane
injection mechanism. It does **not** shell out to `cmux send` directly; instead it
writes a **surface-keyed request flag**, and the already-wired in-pane Stop hook
(`eternity-cmux-inpane.sh`) does the actual `cmux send /exit` the moment this turn
ends. (See that hook's "Priority 0" branch.)

Run this as the **final action** of the skill:

```bash
MON="$HOME/Library/Application Support/acos-token-monitor"
STATE="$MON/state"
# cmux in-pane only: requires in-pane injection mode + a launched cmux surface.
if [ -f "$STATE/.cmux-inpane-inject" ] && [ -n "${CMUX_SURFACE_ID:-}" ]; then
  touch "$STATE/.exit-requested-surface-$CMUX_SURFACE_ID"
  echo "Queued /exit — the in-pane Stop hook will type it when this turn ends."
else
  echo "Not a cmux in-pane session — type /exit to close."
fi
```

Then end the turn normally with a one-line note that the session is closing. When
this response completes, the Stop hook fires, types `/exit` into the surface, and
the session exits — a clean boundary: `/acos-complete` means "we are done, close
everything." Outside cmux in-pane mode (e.g. Warp, plain terminal) the flag is a
no-op and the skill simply tells the user to type `/exit` themselves.

> **Why a flag, not a direct `cmux send` here?** Injecting mid-turn races against
> the active turn (typed-ahead input while Claude is generating is unreliable, and
> `/exit` can't be live-tested without killing the session). Deferring to the Stop
> hook guarantees post-turn timing and reuses the same battle-tested path that
> types `/clear`.

---

*ACOS Complete — Close a milestone and start fresh.*
