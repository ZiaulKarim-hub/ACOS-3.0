# Learning: Pre-Generation Data Verification Gate

**ID:** LEARN-WORKFLOW-002
**Extracted From:** EPIC-001 (Loan Document Generator V2), Story 5
**Date:** 2026-04-10
**Category:** pattern
**Subcategory:** workflow
**Domain:** general
**Confidence:** high
**Applications:** 1

## Context

When an AI system generates documents from extracted data where the documents will be
used for business-critical decisions (credit committee presentations, counterparty
submissions, regulatory filings). Errors in generated documents are costly — they
destroy credibility and may have legal consequences.

## The Learning

Introduce a mandatory human-in-the-loop verification gate between data extraction and
document generation. Display ALL data points with their source documents, page numbers,
clickable file:// links, and confidence scores. The user must explicitly approve before
generation proceeds. This gate is not optional and cannot be auto-bypassed.

## Pattern Description

### Problem

The loan doc generator was extracting data from dozens of source documents and using
that data to populate institutional-grade credit memos and term sheets. Agents
occasionally misread figures (especially from complex XLSX models with nested formulas)
or pulled data from outdated document versions. These errors would propagate silently
into the final PDF/DOCX without any human checkpoint.

For a PE real estate lender, an incorrect LTV figure or wrong interest rate on a term
sheet sent to a counterparty is a serious credibility failure.

### Solution

Add Step 2.5 between Phase 2 (data extraction) and Phase 3 (document design):
1. Generate a `verification-table.yaml` from `loan-data.yaml`
2. Display a structured table to the user: Data Point | Value | Type | Source Doc | Page/Cell | Link | Confidence
3. For calculated values: show the calculation formula and all input values
4. Pause and wait for explicit user approval
5. User can: (a) approve all, (b) flag specific values for correction, (c) override values manually
6. Overridden values become ground truth (supersede extracted values in loan-data.yaml)
7. Only after explicit approval does Phase 3 begin

Single-source figures (extracted from only one document, not cross-validated) are capped
at `confidence: ≤0.7` and highlighted for extra scrutiny.

### Benefits

- Human catches extraction errors before they propagate to final documents
- Clickable provenance links let user verify any figure with one click
- Calculated values show their inputs (user can spot formula errors)
- User override mechanism provides escape hatch for known-wrong extractions
- Creates audit trail: what values were approved, by whom, when

### Trade-offs

- Adds a human waiting step to the pipeline (not fully automated)
- Verification table can be very long for complex loan folders (50+ data points)
- Must be designed carefully to be scannable, not overwhelming

## Evidence

### Project: EPIC-001 — Loan Document Generator V2

**Context:** SLICE-S5-001 through S5-003 formalized the verification gate. The design
decision document (2026-03-23 handoff) states: "Verification table gate added between
Phase 2 and Phase 3: every data point displayed with provenance, confidence, and
cross-validation status before generation proceeds. Single-source figures capped at
confidence <= 0.7."

**Applied:** `loan-data.yaml` carries `source_document`, `page`, `cell_address`, and
`confidence` for every field. Phase 2 generates `verification-table.yaml`. The SKILL.md
wizard includes the verification gate as a required step. Overridden values are
written back to `loan-data.yaml` with `override: true` and `override_reason`.

**Outcome:** Explicitly called out in EPIC-001 acceptance criteria as a critical
accuracy feature. The pattern was recognized as domain-appropriate for PE real estate
lending where "zero tolerance for numerical errors" is a stated requirement.

## Application Guide

### When to Use

- Documents will be used for business-critical decisions (financial, legal, medical)
- Source data is complex and may be misread (XLSX, scanned PDFs, multi-document sets)
- Errors in output would be costly (credibility, legal, regulatory)
- A human is available in the loop (not fully automated pipeline)

### When NOT to Use

- Documents are internal drafts with low stakes
- Data sources are clean and well-structured (API responses, database queries)
- Fully automated pipeline where human review is not feasible
- High-volume batch processing where per-item verification is impractical

### Implementation Steps

1. Design `verification-table.yaml` schema with all required provenance fields
2. Add synthesis step after Phase 2 to generate the table from extracted data
3. Display table in a scannable format (group by document section)
4. Highlight single-source figures and calculated values
5. Implement override mechanism: user can correct any value inline
6. Write overridden values back to loan-data.yaml before Phase 3
7. Log all overrides in session manifest for audit trail

### Common Mistakes

- Displaying only the data point and value (no provenance = useless for verification)
- Not making source document links clickable (user can't verify without friction)
- Auto-approving after a timeout (defeats the purpose of the gate)
- Not surfacing calculated values' inputs (user can't check formula correctness)

## Related Learnings

- LEARN-IMPL-001 — XLSX Cell-Level Extraction with Formula Provenance
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
