# Learning: Managing Scope Expansion as Additive Stories Within an Epic

**ID:** LEARN-WORKFLOW-001
**Extracted From:** EPIC-001 (Loan Document Generator V2)
**Date:** 2026-04-10
**Category:** pattern
**Subcategory:** workflow
**Domain:** general
**Confidence:** medium
**Applications:** 1

## Context

When mid-epic, a significant new capability is identified that is adjacent to the current
epic scope and would meaningfully improve the deliverable. The question is whether to
scope-creep the current stories, start a new epic, or create an additive story within
the current epic.

## The Learning

Add the new capability as a new story within the current epic, with explicit dependencies
on completed stories noted. This keeps the planning artifact as the single source of truth
for the entire deliverable, avoids fork-and-reconcile complexity of a new epic, and
ensures the new work goes through the same review gates as the original scope.

## Pattern Description

### Problem

EPIC-001 was planned with 8 stories (STORY-001-001 through STORY-001-008) covering the
known scope. Mid-execution, the PPTX generation pipeline was identified as a high-value
addition. The options were:
1. Scope-creep Story 1 (DOCX+PDF pipeline) to include PPTX
2. Start a new EPIC-002 for PPTX
3. Add Story 9 within EPIC-001

Scope-creeping Story 1 would retroactively change a nearly-complete story's acceptance
criteria. Starting EPIC-002 would split a coherent deliverable across two epics.

### Solution

Treat PPTX as an additive capability that can be built on top of the existing pipeline.
It was added as a new SKILL.md section and new scripts (data-to-pptx.py, validate-pptx.py)
within the same epic's delivery context. The EPIC-001 planning artifact was updated to
reflect the expanded scope, and the PPTX pipeline went through the full swarm review
cycle alongside the rest of EPIC-001's deliverables.

### Benefits

- Single epic = single review cycle = coherent quality gate
- Planning artifact stays accurate and auditable
- New capability benefits from patterns already established in the epic
  (session manifest, phase orchestration, Wigum loop, two-tier data)
- No coordination overhead between two epics

### Trade-offs

- Epic becomes larger than originally scoped (harder to communicate completion)
- If the new capability blocks, the whole epic blocks
- Adding stories mid-epic can make velocity metrics meaningless

## Evidence

### Project: EPIC-001 — Loan Document Generator V2

**Context:** After Story 1 (DOCX+PDF pipeline) was substantially complete, the PPTX
pipeline was added. This was a meaningful scope expansion: `data-to-pptx.py`
(1049 lines) and `validate-pptx.py` (457 lines) are substantial scripts that
required their own 3-round swarm review cycle.

**Applied:** PPTX pipeline scripts were committed alongside EPIC-001 fixes (commits
1ba46db, 4b40471). The swarm review explicitly covered the PPTX pipeline as part of
the loan doc generator review, not as a separate review. All 99+ findings addressed
included PPTX-specific issues.

**Outcome:** PPTX pipeline went from "completely non-functional" (Critical C1 in
Round 1 review) to fully operational by the end of Round 3. The additive story
pattern meant it received full review rigor rather than being shipped as an
un-reviewed add-on.

## Application Guide

### When to Use

- New capability is adjacent to current epic scope (shares data models, pipelines)
- New capability can be built using patterns already established in the epic
- New capability would benefit from the same review gates as original scope
- Adding a new epic would split a coherent deliverable unnecessarily

### When NOT to Use

- New capability is fundamentally different domain (start a new epic)
- Current epic is nearly complete and adding work would delay delivery
- New capability is experimental (prototype it separately, add to epic only if proven)

### Implementation Steps

1. Identify whether the new capability shares data models/pipelines with existing epic
2. If yes, add it as a new story section in the epic YAML with explicit `dependencies`
3. Update acceptance criteria for the epic to include the new capability
4. Ensure the new capability goes through the same review gates
5. Document the scope expansion in the next session handoff

### Common Mistakes

- Shipping the new capability without a review gate (because "it's an add-on")
- Not updating the epic acceptance criteria (creates ambiguity about what "done" means)
- Adding so many stories mid-epic that the epic becomes undeliverable

## Related Learnings

- LEARN-REVIEW-001 — Multi-Round Swarm Review Remediation
- LEARN-ARCH-001 — Delegated Phase Orchestration

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
