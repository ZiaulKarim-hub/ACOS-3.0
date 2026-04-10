# Learning: Two-Tier Data Model for Token-Efficient Multi-Agent Pipelines

**ID:** LEARN-ARCH-002
**Extracted From:** EPIC-001 (Loan Document Generator V2)
**Date:** 2026-04-10
**Category:** pattern
**Subcategory:** architectural
**Domain:** general
**Confidence:** high
**Applications:** 1

## Context

When multiple agents need to work with a large extracted dataset (e.g., loan data from
dozens of documents), but most agents only need a subset of the data for their specific
task. Passing the full dataset to every agent wastes tokens and increases latency.

## The Learning

Maintain two representations of extracted data: a full canonical YAML (all fields with
provenance) and a brief summary YAML (only what's needed for design/validation). Each
agent receives only the tier it needs. The full tier is the source of truth; the brief
tier is derived for token efficiency.

## Pattern Description

### Problem

A loan folder analysis produces a `loan-data.yaml` with hundreds of fields, provenance
chains, confidence scores, cross-references, and raw extracted text. Passing this entire
file to Phase 3 design agents consumes 10,000+ tokens per agent spawn, and those agents
only need 20-30 key fields to populate a document template.

### Solution

Phase 2 synthesis produces two files:
- `loan-data.yaml` — complete extraction with all metadata, provenance, formulas
- `loan-data-brief.yaml` — condensed version with only the fields needed for the
  document type being generated

Phase 3 design agents receive `loan-data-brief.yaml`. Phase 4 validators and the
verification gate use `loan-data.yaml` for authoritative checks.

### Structure

```
Phase 2 Synthesis
  │
  ├─► loan-data.yaml         (full: all fields + provenance + confidence scores)
  │
  └─► loan-data-brief.yaml   (derived: only critical_figures for this doc type)

Phase 3 Agents ────────────────────────────────► loan-data-brief.yaml (cheap spawn)
Phase 4 Validators ─────────────────────────────► loan-data.yaml      (authoritative)
Verification Gate ──────────────────────────────► loan-data.yaml      (user-facing)
```

### Benefits

- Dramatically reduces token consumption for design agents (often 80% reduction)
- Cheaper haiku-tier model can be used for structural validation (reads brief tier)
- Full provenance preserved in source of truth for auditing and user verification
- Document-type-specific brief tiers can be generated for each batch item independently

### Trade-offs

- Brief tier must be kept in sync with full tier (extra generation step)
- Schema mismatch between tiers can cause subtle bugs if agents cross-reference them
- Brief tier must not lose confidence scores needed for quality decisions

## Evidence

### Project: EPIC-001 — Loan Document Generator V2

**Context:** The loan doc generator was spawning Phase 3 designer agents with the full
loan-data.yaml. As XLSX extraction added more provenance fields, the file grew
substantially. The swarm review praised this as a "smart token optimization."

**Applied:** Phase 2 synthesis step generates both tiers. The doc-type-catalog.yaml
`critical_figures` field defines exactly which fields go into the brief tier for
each document type. Validation agents use the full tier to confirm figures.

**Outcome:** Reviewer explicitly identified this as a positive architectural decision
in the 2026-03-23 swarm review. Cost efficiency for batch mode (5+ documents
concurrently) was a direct beneficiary.

## Application Guide

### When to Use

- Extracted dataset is large (500+ lines of YAML or JSON)
- Multiple downstream agents need the data but each only uses a subset
- Cost optimization is important (e.g., batch mode, frequent runs)
- Different agents have different accuracy requirements (some need provenance, some just need values)

### When NOT to Use

- Dataset is small enough that full tier is cheap to pass
- All agents need all fields (no subset pattern exists)
- Provenance is required at every step (no tiering benefit)

### Implementation Steps

1. Identify which fields each downstream agent type actually needs
2. Define `critical_figures` per document type in the catalog/schema
3. Add a synthesis step after full extraction to generate the brief tier
4. Configure each agent to receive the appropriate tier
5. Add a check: if brief tier is missing, fall back to full tier with a warning

### Common Mistakes

- Generating the brief tier in Phase 3 (should be Phase 2's job)
- Omitting confidence scores from brief tier (validators need them)
- Using brief tier for user-facing verification table (loses provenance)

## Related Learnings

- LEARN-ARCH-001 — Delegated Phase Orchestration
- LEARN-IMPL-002 — XLSX Cell-Level Extraction with Provenance

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
