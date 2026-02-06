# ACOS Decide Command

Record an architectural or design decision.

## Instructions

When this command is invoked:

1. **Gather decision context:**
   - Ask the user what decision needs to be recorded
   - Understand the context and alternatives considered
   - Identify the rationale for the chosen approach

2. **Read the decision template:**
   - Use `memory/decisions/.template.md` as the base

3. **Create the ADR (Architectural Decision Record):**
   - Generate appropriate ID (ADR-XXX)
   - Fill in all sections:
     - Title
     - Status (proposed, accepted, deprecated, superseded)
     - Context (why this decision is needed)
     - Decision (what was decided)
     - Alternatives considered
     - Consequences (positive and negative)
     - Related decisions

4. **Save the decision:**
   - Write to `memory/decisions/ADR-XXX-[title-slug].md`
   - Confirm save to user

## Decision Template

```markdown
# ADR-XXX: [Decision Title]

**Status:** [Proposed | Accepted | Deprecated | Superseded by ADR-YYY]
**Date:** [YYYY-MM-DD]
**Deciders:** [Who made this decision]

## Context

[Why is this decision needed? What is the problem or situation?]

## Decision

[What is the decision that was made?]

## Alternatives Considered

### Option 1: [Name]
- Pros: [advantages]
- Cons: [disadvantages]

### Option 2: [Name]
- Pros: [advantages]
- Cons: [disadvantages]

## Consequences

### Positive
- [Good outcome 1]
- [Good outcome 2]

### Negative
- [Trade-off 1]
- [Trade-off 2]

## Related Decisions

- [ADR-XXX: Related decision]
```

## Key Files

- `./memory/decisions/.template.md` - Decision template
- `./memory/decisions/` - Existing decisions for reference
- `./memory/source-of-truth/` - Vision for alignment check
