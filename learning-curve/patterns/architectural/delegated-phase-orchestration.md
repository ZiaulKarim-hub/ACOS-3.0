# Learning: Delegated Phase Orchestration

**ID:** LEARN-ARCH-001
**Extracted From:** EPIC-001 (Loan Document Generator V2)
**Date:** 2026-04-10
**Category:** pattern
**Subcategory:** architectural
**Domain:** general
**Confidence:** high
**Applications:** 1

## Context

When building multi-step document generation or data processing pipelines where each
phase has distinct responsibilities, significant token requirements, and different
optimal model choices — and where a single context window cannot hold the full pipeline
execution.

## The Learning

Split pipeline execution across dedicated phase agents, each running in its own context
window. The orchestrating skill coordinates handoffs via a shared session manifest
(YAML), not shared state. This enables parallelism, model-tier optimization, and
resilience against context exhaustion.

## Pattern Description

### Problem

A long-running pipeline (loan document generation: extract → analyze → design → validate)
accumulates too much context for a single agent to handle reliably. Intermediate outputs
are large (loan-data.yaml, HTML drafts). Different phases benefit from different models
(fast/cheap for triage, powerful for design). A crash in Phase 3 should not require
re-running Phases 1 and 2.

### Solution

Each phase is a dedicated agent definition (loan-doc-phase1, loan-doc-phase2,
loan-doc-phase34). The orchestrating skill invokes them sequentially via Task().
All state is written to a session manifest (session-manifest.yaml) in the session
directory. Any phase can be resumed independently by reading the manifest.

### Structure

```
Orchestrating Skill (SKILL.md)
  │
  ├─► Task(loan-doc-phase1) → writes phase1-outputs/ + manifest.phase1_complete=true
  │
  ├─► Task(loan-doc-phase2) → reads phase1-outputs/, writes loan-data.yaml + manifest.phase2_complete=true
  │
  └─► Task(loan-doc-phase34) → reads loan-data.yaml, writes output/ (PDF + DOCX)
                               Uses manifest.current_iteration for Wigum loop state
```

### Benefits

- Crash resilience: any phase can be re-run independently
- Model optimization: cheap model for triage, expensive model for document design
- Context management: each phase operates within its own token budget
- Testability: phases can be unit-tested independently
- Parallelism: batch mode can run multiple Phase 3 instances simultaneously

### Trade-offs

- More complex coordination logic in the orchestrating skill
- Session manifest becomes a critical shared file (must be written atomically)
- Debugging cross-phase issues requires correlating multiple agent logs

## Evidence

### Project: EPIC-001 — Loan Document Generator V2

**Context:** The loan doc generator needed to process entire deal folders (hundreds of
files, gigabytes of data) and produce institutional-quality DOCX+PDF output. A single
agent context would be exhausted before completing the design phase.

**Applied:** Three dedicated agent files (loan-doc-phase1.md, loan-doc-phase2.md,
loan-doc-phase34.md) each with their own `maxTurns` settings (phase1: default,
phase2: default, phase34: higher for Wigum loop). Session manifest tracks
`phase1_complete`, `phase2_complete`, `current_iteration`, `output_destination`.

**Outcome:** The swarm reviewer explicitly praised this as "architecturally excellent"
in the 2026-03-23 swarm review report. Phase resumability was validated in practice
when sessions were interrupted mid-generation (handoff evidence, Mar 16).

## Application Guide

### When to Use

- Pipeline has 3+ distinct phases with different responsibilities
- Intermediate outputs are large files, not in-memory state
- Different phases benefit from different model tiers
- Pipeline duration exceeds typical context window capacity
- Failure in later phases should not require re-running earlier phases

### When NOT to Use

- Simple 2-step workflows where a single context is sufficient
- Phases are tightly coupled and cannot produce meaningful intermediate artifacts
- Latency is critical (agent spawning adds overhead)

### Implementation Steps

1. Define phase boundaries by natural data handoffs (what artifact does each phase produce?)
2. Create one agent .md file per phase with explicit input/output contracts
3. Define a session-manifest.yaml schema that tracks completion flags and paths
4. Each phase reads its inputs from manifest paths, writes outputs to manifest paths
5. Orchestrating skill checks manifest completion flags to skip already-done phases
6. Add `resume` mode: if manifest exists for a session_id, skip completed phases

### Common Mistakes

- Sharing state in memory instead of writing to manifest (breaks resume)
- Not writing manifest atomically (corruption risk under concurrent batch execution)
- Over-splitting: 6+ micro-phases adds coordination overhead without benefit

## Code Example

```yaml
# session-manifest.yaml pattern
session_id: "20260316-130000"
phase1_complete: true
phase2_complete: false
current_iteration: 0
loan_data_path: ".acos/loan-doc-generator/sessions/20260316-130000/loan-data.yaml"
design_spec_path: null   # set by Phase 1
output_destination: "/Users/zee/Desktop/"
```

## Related Learnings

- LEARN-ARCH-002 — Wigum Loop for Iterative Quality Convergence
- LEARN-IMPL-001 — Session Manifest as Phase Coordination Contract
- LEARN-WORKFLOW-001 — Multi-Round Swarm Review Remediation

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
