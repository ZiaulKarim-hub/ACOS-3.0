# Learning: Wigum Loop for Iterative Quality Convergence

**ID:** LEARN-ARCH-003
**Extracted From:** EPIC-001 (Loan Document Generator V2), acos-financial-statement skill
**Date:** 2026-04-10
**Category:** pattern
**Subcategory:** architectural
**Domain:** general
**Confidence:** high
**Applications:** 2

## Context

When an AI-generated output must meet a hard quality bar (document structure, financial
accuracy, benchmark criteria) and a single generation pass is not reliable enough to
guarantee it. Particularly useful when a separate validation agent can objectively
assess output quality against defined criteria.

## The Learning

Use an iterative Wigum loop: generate → validate → (if fail) identify deficiencies
→ regenerate with targeted fixes → repeat up to N iterations. The validator never
provides the corrected values — it only identifies what is wrong and why. This
preserves the generative agent's autonomy while enforcing quality gates.

## Pattern Description

### Problem

Document generation and financial statement preparation both produce outputs that must
meet strict quality criteria. A single generation pass frequently produces outputs that
pass some criteria but fail others. Naive retry (just re-run everything) wastes tokens
and loses progress. Asking the validator to provide corrected values conflates validation
with generation (adversarial separation breaks down).

### Solution

The Wigum loop separates responsibilities:
1. **Generator** (phase34 orchestrator / fin-stmt-sandbox): produces the output
2. **Validator** (Phase 4 benchmarks / fin-stmt-accountant): identifies deficiencies ONLY,
   never provides values
3. **Loop controller**: feeds deficiency list back to generator for targeted fixes
4. **Convergence criteria**: all required benchmarks pass, OR max iterations reached

For financial statements specifically, the Primary Accountant never gives numbers —
only identifies structural or substance deficiencies. This is mechanically enforced
in the agent definition.

### Structure

```
Generator ──► Output
                │
                ▼
           Validator ──► PASS ──► Finalize
                │
                ▼ FAIL
           Deficiency List
                │
                ▼
           Generator (targeted re-work, iteration 2+)
                │
           [repeat up to max_iterations]
                │
                ▼ max iterations exceeded
           Escalate to user
```

### Benefits

- Quality improves each iteration because fixes are targeted (not full regeneration)
- Adversarial separation maintained: validator can't bias the generator
- Max iterations prevents runaway loops and infinite token spend
- Incremental mode (iterations 2+ skip re-extracting unchanged data) reduces cost

### Trade-offs

- Requires a clear, objective deficiency format that the generator can act on
- Loop coordination adds complexity (iteration counter in session manifest)
- Incremental mode is instruction-based, not mechanically enforced

## Evidence

### Project: EPIC-001 — Loan Document Generator V2

**Context:** Phase 4 validators check generated documents against benchmark criteria.
Documents that fail structural checks must be regenerated. Without a loop, failures
result in manual intervention.

**Applied:** Phase 4 benchmarks produce PASS/FAIL per criterion. On FAIL, the
`current_iteration` in session-manifest.yaml is incremented and the generator
re-runs. `max_iterations: 3` prevents infinite loops.

**Outcome:** Swarm reviewer praised "Wigum loop design is well-specified with clear
convergence criteria." The pattern was effective enough to be reused in the financial
statement skill without modification.

### Project: acos-financial-statement skill

**Context:** Three independent sandbox orchestrators each prepare complete GAAP financial
statements. The Primary Accountant reconciles them and identifies substance disagreements.

**Applied:** fin-stmt-accountant.md has explicit instructions: "You NEVER provide
numbers. You ONLY identify deficiencies." Loop terminates when all three sandboxes
produce substance-equivalent outputs (Actual mode) or when max 5 iterations hit.
Incremental mode for iterations 2+ avoids re-extracting unchanged data.

**Outcome:** 17-finding swarm review of the fin-stmt skill validated the loop design
after adding a 3-attempt retry cap (Fix 8) to prevent infinite loops within sandbox
internal validation.

## Application Guide

### When to Use

- Output must meet hard, objectively verifiable quality criteria
- Single-pass generation is unreliable (domain complexity, data variability)
- A validator can assess quality without needing to provide the "right" answer
- Token budget allows for 2-3 iterations (each iteration costs roughly as much as the first pass)

### When NOT to Use

- Quality criteria are subjective (human review needed instead)
- Single pass is already highly reliable (loop adds overhead without value)
- Time constraints prohibit multi-pass (hard latency requirements)

### Implementation Steps

1. Define convergence criteria as explicit PASS/FAIL benchmarks (not fuzzy)
2. Create a separate validator agent that outputs deficiency lists (never corrections)
3. Store iteration state in session manifest (`current_iteration`, `max_iterations`)
4. On FAIL: pass deficiency list back to generator with iteration context
5. For iterations 2+: implement incremental mode (only re-work flagged sections)
6. On max iterations exceeded: surface to user with full deficiency log

### Common Mistakes

- Validator provides corrections (breaks adversarial separation, biases output)
- No max iterations cap (can loop indefinitely on hard-to-fix deficiencies)
- Iteration 2+ regenerates everything (wastes tokens, loses convergence progress)
- Convergence criteria too vague (validator can't produce actionable deficiency list)

## Related Learnings

- LEARN-ARCH-001 — Delegated Phase Orchestration
- LEARN-REVIEW-001 — Multi-Round Swarm Review Remediation

## Success Rate

- Applied: 2 times
- Successful: 2 times
- Success Rate: 100%

## Update History

| Date | Update | By |
|------|--------|-----|
| 2026-04-10 | Initial creation | Learning Curve Agent |

---

*Extracted by ACOS Learning Curve Agent*
