# ACOS Learning Curve

The Learning Curve is ACOS's cross-project knowledge accumulation system. It stores learnings that apply globally across all projects.

## Directory Structure

```
learning-curve/
├── patterns/                  # Successful patterns to replicate
│   ├── architectural/         # System design patterns
│   ├── implementation/        # Code patterns
│   ├── review/               # Review patterns
│   └── workflow/             # Process patterns
│
├── anti-patterns/             # Patterns to avoid
│   ├── common-mistakes/      # Frequent errors
│   ├── failed-approaches/    # Strategies that don't work
│   └── pitfalls/             # Hidden traps
│
├── domain-knowledge/          # Domain-specific learnings
│   ├── web-development/
│   ├── api-design/
│   ├── database/
│   ├── security/
│   └── performance/
│
├── agent-effectiveness/       # Agent performance data
│   ├── agent-ratings/        # How well agents perform
│   ├── skill-effectiveness/  # Which skills work best
│   └── flow-success-rates/   # Flow performance metrics
│
├── project-retrospectives/    # Complete project analyses
│
└── index.yaml                 # Searchable index
```

## Learning Entry Format

Each learning is stored as a markdown file:

```markdown
# Learning: [Title]

**ID:** LEARN-[CATEGORY]-[NUMBER]
**Extracted From:** [Project ID]
**Date:** [YYYY-MM-DD]
**Category:** [pattern | anti-pattern | domain-knowledge]
**Domain:** [web | api | database | security | performance | workflow]
**Confidence:** [high | medium | low]
**Applications:** [count of successful applications]

## Context
[When this learning applies]

## The Learning
[Clear, actionable insight]

## Evidence
[Specific examples from the project]

## Application Guide
[How to apply this learning]

## Related Learnings
- [LEARN-XXX-NNN] - [Title]

## Success Rate
- Applied: [N] times
- Successful: [N] times
- Success Rate: [X]%
```

## Confidence Levels

| Level | Criteria |
|-------|----------|
| HIGH | 3+ successful applications, >80% success rate |
| MEDIUM | 1-2 successful applications, >50% success rate |
| LOW | New learning, unvalidated, or <50% success rate |

## When Learnings Are Extracted

Learnings are extracted at project completion by the Learning Curve Agent:

1. Analyze all decisions and their outcomes
2. Identify patterns in review feedback
3. Evaluate flow performance
4. Document what worked and what didn't
5. Create learning entries with evidence

## Using Learnings

1. **During Planning:** The Architect queries learnings for relevant insights
2. **During Implementation:** Developers can request applicable patterns
3. **During Review:** Reviewers can check for known issues

## Deprecation

Learnings are deprecated when:

- Success rate drops below 30%
- Technology becomes obsolete
- Superseded by better learning
- 5+ consecutive failed applications

Deprecated learnings are moved to `.archive/` with deprecation reason.

## Critical Rules

1. **Evidence required** - No learnings without project evidence
2. **Track applications** - Update success metrics after each use
3. **Maintain confidence** - Provide confidence levels with recommendations
4. **Regular review** - Learning Curve Agent reviews and updates ratings
