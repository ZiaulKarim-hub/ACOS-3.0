---
name: technology-research
description: Skill for researching technologies, libraries, and implementation approaches
version: 1.0.0
created_by: architect
created_date: 2026-01-31

category: research

applicable_to:
  - the-architect
  - any-agent

tools_required:
  - WebSearch
  - WebFetch
  - Read
---

# Technology Research Skill

## Purpose

This skill provides structured guidance for researching technologies, evaluating libraries, and determining implementation approaches.

## When to Use

Apply this skill when:
- Evaluating technology options
- Researching library choices
- Understanding best practices
- Finding implementation examples
- Comparing approaches

## Skill Protocol

### Phase 1: Define Research Scope

1. Clearly state the question/problem
2. Identify constraints:
   - Existing technology stack
   - Performance requirements
   - Team expertise
   - Project timeline

### Phase 2: Gather Information

1. **Official Documentation:**
   - Library docs
   - Framework guides
   - API references

2. **Community Resources:**
   - GitHub repos (stars, issues, activity)
   - Stack Overflow discussions
   - Blog posts and tutorials

3. **Comparison Resources:**
   - Benchmark results
   - Feature comparisons
   - Migration guides

### Phase 3: Evaluate Options

For each option, assess:

1. **Fit:**
   - Does it solve the problem?
   - Does it integrate with existing stack?

2. **Maturity:**
   - How long has it existed?
   - Is it actively maintained?
   - What's the community size?

3. **Quality:**
   - Documentation quality
   - TypeScript support
   - Test coverage

4. **Risk:**
   - Breaking changes frequency
   - Vendor lock-in
   - Learning curve

### Phase 4: Document Findings

Create a research report with recommendations.

## Research Checklist

### Information Gathering

- [ ] Official docs reviewed
- [ ] GitHub activity checked
- [ ] Community resources found
- [ ] Example implementations reviewed

### Evaluation

- [ ] Pros and cons listed
- [ ] Risks identified
- [ ] Alternatives compared
- [ ] Recommendation made

## Research Queries Template

```
# For library evaluation
[library name] vs alternatives 2024
[library name] production usage
[library name] performance benchmarks
[library name] TypeScript support

# For implementation approaches
[technology] best practices
[technology] common patterns
[problem] implementation [framework]

# For troubleshooting
[error message] [technology]
[technology] [specific problem] solution
```

## Output: Research Report

Create in `memory/research/`:

```markdown
# Technology Research: [Topic]

**Date:** [YYYY-MM-DD]
**Researched By:** [Agent Name]

## Research Question

[Clear statement of what was researched]

## Context

[Why this research was needed]

## Options Evaluated

### Option 1: [Name]

**Description:** [What it is]

**Pros:**
- [Pro 1]
- [Pro 2]

**Cons:**
- [Con 1]
- [Con 2]

**Maturity:**
- GitHub Stars: [N]
- Last Release: [Date]
- Contributors: [N]

**Resources:**
- [Documentation URL]
- [Example repo URL]

### Option 2: [Name]

[Same structure as above]

## Comparison Matrix

| Criteria | Option 1 | Option 2 | Option 3 |
|----------|----------|----------|----------|
| Performance | Good | Better | Best |
| Ease of Use | Easy | Moderate | Hard |
| Documentation | Excellent | Good | Fair |
| Community | Large | Medium | Small |
| TypeScript | Native | Partial | None |

## Recommendation

**Recommended:** [Option Name]

**Rationale:**
[Why this is the best choice for our context]

**Implementation Notes:**
[Any specific guidance for implementation]

## Sources

1. [Source 1 - URL]
2. [Source 2 - URL]
3. [Source 3 - URL]
```

---

*Technology Research Skill - Informed decisions through thorough research.*
