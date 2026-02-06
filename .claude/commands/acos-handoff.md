# ACOS Handoff Command

Create a handoff document for session continuity.

## Instructions

When this command is invoked:

1. **Gather session context:**
   - What slice/story/epic was being worked on
   - What was accomplished this session
   - What decisions were made
   - What is the current state
   - What should happen next

2. **Read the handoff template:**
   - Use `memory/handoffs/.template.yaml` as the base

3. **Create the handoff document:**
   - Generate timestamp-based filename
   - Fill in all sections thoroughly
   - Include specific file paths and line numbers
   - Document any blockers or questions
   - List clear next actions

4. **Save the handoff:**
   - Write to `memory/handoffs/[timestamp]-handoff.yaml`
   - Confirm save to user

## Handoff Contents

The handoff should include:

```yaml
timestamp: [ISO timestamp]
session_summary: [Brief description of what was done]

current_work:
  slice_id: [SLICE-XXX]
  story_id: [STORY-XXX]
  epic_id: [EPIC-XXX]
  status: [in_progress | blocked | ready_for_review]

completed_this_session:
  - [Specific accomplishment 1]
  - [Specific accomplishment 2]

files_modified:
  - path: [file path]
    changes: [what changed]

decisions_made:
  - [Decision and rationale]

blockers:
  - [Any blocking issues]

next_actions:
  - [Clear next step 1]
  - [Clear next step 2]

context_for_next_session:
  [Any important context the next session needs]
```

## Key Files

- `./memory/handoffs/.template.yaml` - Handoff template
- `./memory/handoffs/` - Existing handoffs for reference
- `./planning/slices/` - Current slice details
