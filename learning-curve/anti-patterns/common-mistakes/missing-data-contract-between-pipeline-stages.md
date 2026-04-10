# Anti-Pattern: Missing Data Contract Between Pipeline Stages

**ID:** LEARN-ANTI-001
**Extracted From:** EPIC-001 (Loan Document Generator V2)
**Date:** 2026-04-10
**Category:** anti-pattern
**Subcategory:** common-mistakes
**Domain:** general
**Confidence:** high
**Occurrences:** 3

## Context

When building a multi-phase pipeline where each phase produces artifacts consumed by
subsequent phases, with the pipeline orchestrated by instructions in SKILL.md rather
than code that can be statically verified.

## The Anti-Pattern

Referencing intermediate artifacts in downstream agents without ensuring the upstream
agent actually produces them. Schema mismatches and missing file references in
instruction-based pipelines are only discovered at runtime.

## Why It's Wrong

In an LLM-orchestrated pipeline, there is no compiler to catch "file X is read here
but never produced anywhere." The first indication of the problem is a runtime crash
or silent failure when the downstream agent tries to access the file.

### Consequences

- Downstream pipeline stages fail completely and silently (no error surfaced to user)
- Debugging requires reading multiple agent instructions to trace data flow
- Cross-lens review catches these issues only if reviewers trace all data flows
- Bugs persist across many generations of the skill because they're hard to spot

### Root Causes

- SKILL.md instructions are written incrementally — new features reference new files
  that were never added to upstream phase outputs
- Schema evolution: a field is renamed in one place but not updated everywhere
- Copy-paste from a different document type creates schema mismatches

## Evidence

### Incident: SLICE-PPTX (Critical finding C1)

**What Happened:**
The PPTX pipeline in `data-to-pptx.py` expected a `verified-data.yaml` input file.
This file was never produced by any phase in the pipeline. The PPTX pipeline was
completely non-functional from the moment it was written.

**Impact:**
Critical C1 in the 2026-03-23 swarm review: "PPTX pipeline completely non-functional."
This was cross-confirmed by Integration, Error Handling, and QA lenses simultaneously,
giving it the highest possible confidence.

**How Discovered:**
8-lens swarm review (2026-03-23). No human had caught it because the PPTX feature
was new and hadn't been tested end-to-end.

**Fix Applied:**
Either transform `loan-data.yaml` → `verified-data.yaml` in Phase 2, or rewrite
`data-to-pptx.py` to accept `loan-data.yaml` schema directly.

### Incident: `sample_file` vs `sample_files` Schema Mismatch (High finding H3)

**What Happened:**
Phase 1 instructions used `sample_file` (scalar string). The session manifest template
used `sample_files` (array). SKILL.md used `sample_file` (scalar). Three different
representations of the same field across three files, none compatible.

**Impact:**
Phase 1 output could not be consumed by downstream phases that expected the array
form. Design library entries were inconsistently structured.

**How Discovered:**
Integration lens in 2026-03-23 swarm review.

**Fix Applied:**
Standardized on `sample_files: []` (array) across all files. Updated Phase 1
instructions to always produce an array (even for single-file entries).

### Incident: `template_pptx_path` Not in Session Manifest (High finding H2)

**What Happened:**
`data-to-pptx.py` required `template_pptx_path` to be available at runtime, but
Phase 1 never wrote this field to the session manifest. Phase 3 silently used a blank
presentation instead of the specified template.

**Impact:**
Generated PPTX slides had no template styling — blank white slides instead of
the specified design.

**How Discovered:**
Integration lens in 2026-03-23 swarm review.

**Fix Applied:**
Added `template_pptx_path` to session manifest schema and Phase 1 output instructions.

## The Correct Approach

### Do This Instead

For any new file or field that a downstream phase needs, explicitly:
1. Add the field to the session manifest schema
2. Update the upstream phase's output instructions to produce it
3. Update the downstream phase's input contract to read it
4. Add an existence check in the downstream phase before attempting to read

### Why It Works

- Session manifest serves as a machine-readable contract between phases
- Existence checks surface missing files as explicit errors (not silent failures)
- Schema is defined once (manifest template) and referenced everywhere

### Example

**Wrong:**
```yaml
# data-to-pptx.py reads verified-data.yaml
# But no phase ever produces verified-data.yaml
```

**Right:**
```yaml
# session-manifest.yaml schema:
verified_data_path: null    # populated by Phase 2 synthesis

# Phase 2 instructions:
# Step 2.5c: Write verified-data.yaml to session directory
# Set manifest.verified_data_path = "<session_dir>/verified-data.yaml"

# data-to-pptx.py:
# if not os.path.exists(manifest['verified_data_path']):
#     raise FileNotFoundError("verified-data.yaml not found — run Phase 2 first")
```

## Prevention Guide

### Warning Signs

- A script or agent instruction references a file path that you can't find being
  produced anywhere else in the pipeline
- A field name appears differently in different files (scalar vs array, snake_case variants)
- A new feature was added "quickly" by editing one file without reviewing dependencies

### Prevention Checklist

- [ ] For every file read in Phase N, verify it is written in Phase N-1
- [ ] Session manifest schema is the canonical list of all inter-phase artifacts
- [ ] All schema changes in manifest are propagated to all phases that use that field
- [ ] New scripts have explicit file-existence checks before reading inputs
- [ ] After adding a new capability, trace its data flow end-to-end in the instructions

### Review Focus

For reviewers — look for:
- File paths referenced in instructions or scripts that don't appear in upstream outputs
- Field names that differ between SKILL.md, phase files, and templates
- Any `load_data()` or `open()` call without a preceding existence check

## Related Anti-Patterns

- LEARN-ANTI-003 — Naive Contains-Digit Check for Text Classification

## Related Correct Patterns

- LEARN-ARCH-001 — Delegated Phase Orchestration (session manifest as contract)
- LEARN-IMPL-001 — XLSX Cell-Level Extraction (explicit input/output contracts)

## Occurrence History

| Date | Project | Caught By | Severity |
|------|---------|-----------|----------|
| 2026-03-23 | EPIC-001 PPTX pipeline | Swarm Review (Integration + Error Handling + QA) | CRITICAL |
| 2026-03-23 | EPIC-001 schema mismatch | Swarm Review (Integration) | HIGH |
| 2026-03-23 | EPIC-001 template_pptx_path | Swarm Review (Integration) | HIGH |

---

*Documented to prevent recurrence - ACOS Learning Curve Agent*
