---
name: technology-research
description: Structured guidance for researching technologies, evaluating libraries, comparing approaches, and making informed technology decisions.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, WebSearch, WebFetch
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
2. Identify constraints: existing stack, performance requirements, team expertise, timeline

### Phase 2: Gather Information

1. **Official Documentation:** Library docs, framework guides, API references
2. **Community Resources:** GitHub repos (stars, issues, activity), Stack Overflow, blog posts
3. **Comparison Resources:** Benchmarks, feature comparisons, migration guides

### Phase 3: Evaluate Options

For each option, assess:
1. **Fit:** Solves the problem? Integrates with existing stack?
2. **Maturity:** How long existed? Actively maintained? Community size?
3. **Quality:** Documentation quality? TypeScript support? Test coverage?
4. **Risk:** Breaking changes frequency? Vendor lock-in? Learning curve?

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

## Output: Research Report

```markdown
# Technology Research: [Topic]

## Research Question
[Clear statement]

## Options Evaluated

### Option 1: [Name]
**Pros:** ...
**Cons:** ...
**Maturity:** GitHub Stars, Last Release, Contributors

## Comparison Matrix
| Criteria | Option 1 | Option 2 |
|----------|----------|----------|

## Recommendation
**Recommended:** [Option Name]
**Rationale:** [Why]
```

---

*Technology Research Skill - Informed decisions through thorough research.*
