# ACOS Status Command

Display the current status of the ACOS project.

## Instructions

When this command is invoked:

1. **Check if ACOS is initialized:**
   - Look for `.acos/` and `memory/` directories
   - If not found, inform user to run `/acos-start` first

2. **Gather status information:**

   **Vision Status:**
   - Check if `memory/source-of-truth/vision-document.md` exists
   - Read the vision title and summary

   **Planning Status:**
   - Count epics in `planning/epics/` (exclude templates)
   - Count stories in `planning/stories/` (exclude templates)
   - Count slices in `planning/slices/` (exclude templates)
   - Identify which are complete vs in-progress vs pending

   **Current Work:**
   - Find any slices with status: in_progress
   - Find the current handoff in `memory/handoffs/`

   **Memory Status:**
   - Count decisions in `memory/decisions/`
   - Count reviews in `memory/reviews/`
   - Count code rationale in `memory/code-rationale/`

   **Evidence Status:**
   - Check `.acos/evidence/` for pending evidence bundles

3. **Format the output:**

```
ACOS Project Status
═══════════════════════════════════════

Vision: [Vision title]
Status: [In Progress | Complete]

Planning:
  Epics:   [X] total, [Y] complete, [Z] in progress
  Stories: [X] total, [Y] complete, [Z] in progress
  Slices:  [X] total, [Y] complete, [Z] in progress

Current Work:
  Active Slice: [SLICE-XXX] - [Title]
  Last Handoff: [Date] - [Status]

Memory:
  Decisions: [X] recorded
  Reviews:   [Y] completed
  Rationale: [Z] documented

Next Steps:
  - [Recommendation based on current state]
```

## Key Directories

- `./memory/source-of-truth/` - Vision documents
- `./planning/` - Epics, stories, slices
- `./memory/decisions/` - ADRs
- `./memory/reviews/` - Review records
- `./memory/handoffs/` - Session handoffs
- `./.acos/evidence/` - Evidence bundles
