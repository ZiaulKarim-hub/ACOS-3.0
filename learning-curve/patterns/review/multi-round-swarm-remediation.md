# Learning: Multi-Round Swarm Review Remediation

**ID:** LEARN-REVIEW-001
**Extracted From:** EPIC-001 (Loan Document Generator V2)
**Date:** 2026-04-10
**Category:** pattern
**Subcategory:** review
**Domain:** general
**Confidence:** high
**Applications:** 1

## Context

When a swarm review returns a large number of findings (20+) across multiple lenses,
and those findings span several independent subsystems. A single remediation pass
frequently introduces new issues or misses cross-cutting findings. Running the swarm
again after remediating the first batch is standard practice, but requires discipline
to converge efficiently.

## The Learning

Structure multi-round remediation as: (1) triage findings by severity and cross-lens
confirmation, (2) remediate in severity-ordered batches, (3) re-run swarm to find
regression and second-order issues, (4) repeat until zero Critical/High remain.
Cross-lens confirmed findings (flagged by 2+ lenses independently) should be treated
as highest priority because they represent true defects, not lens-specific noise.

## Pattern Description

### Problem

The 2026-03-23 swarm review of the loan doc generator returned 56 findings (9 Critical,
18 High, 29 Medium/Low) across 8 lenses. Fixing all 56 in one pass is error-prone:
fixes for integration issues can break error handling; domain logic fixes can conflict
with documentation improvements. Moreover, fixing lower-severity issues before higher-
severity ones risks wasting effort if Critical fixes invalidate the context around
Medium findings.

### Solution

Three-round remediation:
- **Round 1** (commit 9783b58): Fix all Critical + highest-priority High findings,
  especially those confirmed by 2+ lenses. 56+ findings addressed.
- **Round 2** (commit b5ab8a0): Re-run swarm on the remediated code. Fix newly
  surfaced issues and remaining High/Medium items. 30+ findings.
- **Round 3** (commit deddb4e): Final cleanup pass. 13 remaining items — domain logic,
  PPTX pipeline edge cases, UX. All cleared.

Cross-lens findings (PPTX pipeline broken, skip_phase_1 shortcut, step numbering)
were prioritized in Round 1 because they represented hard functional failures.

### Structure

```
Initial Swarm Review
    │
    ▼
Round 1: Fix Critical + Cross-Lens Confirmed Highs
    │
    ▼
Round 2 Swarm: Find regressions + remaining items
    │
    ▼
Round 2: Fix remaining High/Medium
    │
    ▼
Round 3 Swarm: Final verification
    │
    ▼
Round 3: Close tail items
    │
    ▼
Zero Critical/High remaining → PASS
```

### Benefits

- Each round surfaces second-order issues introduced by the previous round's fixes
- Diminishing finding count (56 → 30 → 13) provides a clear convergence signal
- Cross-lens confirmation provides objective prioritization signal
- Evidence bundles per round make audit trail clear

### Trade-offs

- 3 rounds of swarm review takes significant time (~3-4 sessions)
- Late-round findings are often edge cases that require domain judgment
- Re-running a full swarm on partially-fixed code may flag previously-accepted items

## Evidence

### Project: EPIC-001 — Loan Document Generator V2

**Context:** The loan doc generator underwent three explicit review-and-remediation
rounds between commits 9783b58, b5ab8a0, and deddb4e. The git commit messages
document each round explicitly: "Remediate 56 swarm review findings", "round-2
review findings — 30+ fixes", "Close all 13 remaining review items."

**Applied:** Evidence bundles written for each remediation round
(.acos/evidence/2026-03-23/, 2026-03-24/). The 2026-03-30 handoff confirms all
three rounds completed and zero Critical/High findings remain.

**Outcome:** Total of 99+ findings remediated across three rounds. The PPTX pipeline
went from "completely non-functional" (Critical C1) to fully operational. Domain
logic gaps (bridge lending specifics) were addressed in Round 3. Zero open items
at completion.

## Application Guide

### When to Use

- Swarm review returns 20+ findings
- Findings span multiple subsystems (integration + error handling + domain logic)
- Critical findings were found that may invalidate Medium-level fixes
- The codebase is complex enough that fixes in one area can break another

### When NOT to Use

- Small finding count (<10) — single remediation pass is sufficient
- Findings are all in one domain (a single targeted fix may close all of them)
- Time pressure doesn't allow for multi-round (accept remaining risk explicitly)

### Implementation Steps

1. Sort findings by: (a) severity, (b) cross-lens confirmation count
2. Group findings by subsystem (integration, error handling, domain logic, etc.)
3. Fix Critical and cross-lens-confirmed High findings first (Round 1)
4. Re-run swarm on the modified codebase (not just the changed files)
5. Repeat until zero Critical/High — typically 2-3 rounds
6. In final round, close Medium/Low tail items and UX polish
7. Write evidence bundles after each round documenting what was fixed

### Common Mistakes

- Fixing Medium findings before Critical findings (Critical may invalidate Medium context)
- Not re-running the full swarm (running only affected-area tests misses regressions)
- Treating each round's findings as independent (they build on each other)
- Declaring victory after Round 1 (second-order issues are real)

## Related Learnings

- LEARN-ARCH-003 — Wigum Loop for Iterative Quality Convergence
- LEARN-WORKFLOW-001 — Scope Expansion Managed as Additive Stories

## Success Rate

- Applied: 1 time
- Successful: 1 time
- Success Rate: 100%

## Update History

| Date | Update | By |
|------|--------|-----|
| 2026-04-10 | Initial creation | Learning Curve Agent |

---

*Extracted by ACOS Learning Curve Agent*
