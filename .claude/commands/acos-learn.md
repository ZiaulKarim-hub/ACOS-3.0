# ACOS Learn Command

Extract and document learnings from project work.

## Instructions

When this command is invoked:

1. **Determine learning scope:**
   - After a slice: Extract slice-level learnings
   - After a story: Extract story-level patterns
   - After an epic: Extract epic-level insights
   - After project: Full learning extraction

2. **For Slice-Level Learning:**
   - Review the evidence bundle
   - Review the review feedback
   - Identify what worked and what didn't
   - Update relevant skills if patterns emerge

3. **For Story/Epic-Level Learning:**
   - Aggregate learnings from child items
   - Identify cross-cutting patterns
   - Note integration challenges and solutions

4. **For Full Learning Extraction:**
   - Execute the learning-extraction-flow
   - Read `/Users/zee/Documents/Vibe Coding/ACOS 3.0/agentic-flows/learning-extraction-flow.yaml`
   - Analyze all memory: decisions, reviews, feedback
   - Identify patterns in agent effectiveness
   - Document insights for future projects

5. **Update Skills (if applicable):**
   - If a new technique was discovered, consider creating a skill
   - If an existing skill needs refinement, update it
   - Skills go in `/Users/zee/Documents/Vibe Coding/ACOS 3.0/skills/[category]/`

6. **Document in Feedback History:**
   - Save learnings to `memory/feedback-history/`
   - Include:
     - What was learned
     - Evidence/examples
     - How to apply it
     - Related decisions or reviews

## Learning Template

```markdown
# Learning: [Title]

**Date:** [YYYY-MM-DD]
**Context:** [Slice/Story/Epic ID]
**Category:** [Technical | Process | Communication | Architecture]

## What Happened

[Description of the situation]

## What We Learned

[Key insight or lesson]

## Evidence

[Links to reviews, decisions, or code that supports this]

## Application

[How this learning should be applied in future work]

## Related

- [Related decisions]
- [Related skills]
```

## Key Files

- `/Users/zee/Documents/Vibe Coding/ACOS 3.0/agentic-flows/learning-extraction-flow.yaml` - Full extraction flow
- `/Users/zee/Documents/Vibe Coding/ACOS 3.0/agents/learning-curve-agent.md` - Learning agent
- `./memory/feedback-history/` - Learning storage
- `./memory/decisions/` - Decisions to analyze
- `./memory/reviews/` - Reviews to analyze
