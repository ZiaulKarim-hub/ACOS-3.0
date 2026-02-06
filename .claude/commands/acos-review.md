# ACOS Review Command

Trigger a review for completed work.

## Instructions

When this command is invoked:

1. **Determine what to review:**
   - Check for slices with status: ready_for_review
   - Check for stories where all slices are complete
   - Check for epics where all stories are complete
   - Ask user what level of review they want if multiple options

2. **For Slice Review:**
   - Read the slice specification from `planning/slices/`
   - Read the evidence bundle from `.acos/evidence/`
   - Run `./automation-scripts/validate-evidence.sh` if available
   - Load the Independent Reviewer agent
   - Execute the slice-review process
   - Record results in `memory/reviews/slice-reviews/`

3. **For Story Review:**
   - Verify all slices in the story are complete and reviewed
   - Read the story specification from `planning/stories/`
   - Use the story review template from `memory/reviews/story-reviews/.template.md`
   - Evaluate story completion against acceptance criteria
   - Record results in `memory/reviews/story-reviews/`

4. **For Epic Review:**
   - Verify all stories in the epic are complete and reviewed
   - Read the epic specification from `planning/epics/`
   - Use the epic review template from `memory/reviews/epic-reviews/.template.md`
   - Evaluate epic completion against capability requirements
   - Record results in `memory/reviews/epic-reviews/`

5. **For Vision Review:**
   - Verify all epics are complete and reviewed
   - Read the vision document from `memory/source-of-truth/`
   - Use the vision review template from `memory/reviews/vision-reviews/.template.md`
   - Evaluate overall project against original vision
   - Record results in `memory/reviews/vision-reviews/`

## Key Files

- `/Users/zee/Documents/Vibe Coding/ACOS 3.0/agents/independent-reviewer.md` - Reviewer agent
- `/Users/zee/Documents/Vibe Coding/ACOS 3.0/agentic-flows/slice-review-flow.yaml` - Review process
- `./memory/reviews/` - Review templates and records
- `./.acos/evidence/` - Evidence bundles

## Review Outputs

All reviews should:
- Reference the specific work being reviewed
- Provide clear PASS/FAIL/REVISE verdict
- Include specific feedback if revisions needed
- Be stored in the appropriate memory location
