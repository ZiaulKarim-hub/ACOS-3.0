# Anti-Pattern: Generic Document Templates Missing Domain-Critical Fields

**ID:** LEARN-ANTI-004
**Extracted From:** EPIC-001 (Loan Document Generator V2)
**Date:** 2026-04-10
**Category:** anti-pattern
**Subcategory:** common-mistakes
**Domain:** general
**Confidence:** high
**Occurrences:** 4

## Context

When building document generation for a specialized domain (PE real estate lending,
medical records, legal contracts) using document templates designed by a generalist
developer. The templates look structurally complete but miss domain-specific fields
that practitioners consider mandatory.

## The Anti-Pattern

Designing document templates and data schemas based on what seems complete to a
generalist, without systematic validation against domain practitioner standards.
The result is documents that look professional but are functionally incomplete for
their intended use.

## Why It's Wrong

Domain practitioners evaluate documents against a specific mental checklist.
For a PE real estate bridge lender reviewing a credit memo, "Exit Strategy" is
not optional — it's the central question. Missing it signals that the document
was not prepared by someone who understands bridge lending. The document may look
complete but fails the practitioner's first-pass review.

### Consequences

- Documents fail professional review immediately ("this is missing X")
- Credibility damage disproportionate to the amount of correct information included
- Fixing late-stage domain gaps requires updating templates, data schemas, agent
  instructions, AND swarm review benchmarks simultaneously

### Root Causes

- Templates designed bottom-up (what fields can we extract?) vs top-down (what does
  a practitioner need to see?)
- Domain knowledge is implicit in the practitioner's head, not written down
- Generalist reviewers in swarm catch structural issues but miss domain gaps

## Evidence

### Incident: Exit Strategy Missing from Internal Credit Memo (High H9)

**What Happened:**
The Internal Credit Memo document template omitted the "Exit Strategy" section.
In bridge lending, the exit strategy is how the borrower repays the loan at maturity —
it is the primary credit question for any bridge loan. An internal credit memo
without it is fundamentally incomplete.

**Impact:**
High finding H9 in the 2026-03-23 swarm review: "Internal Credit Memo missing Exit
Strategy section — the central question in bridge lending."

**Fix Applied:**
"Exit Strategy" section added to Internal Credit Memo default_sections. Section
ordering updated to reflect analytical flow (after Stress Testing, before Mitigants).
Fix committed in domain-logic-fixes remediation (evidence: .acos/evidence/2026-03-24/).

### Incident: Missing Bridge Lending Fields (Critical C6)

**What Happened:**
Critical underwriting figures (LTC — Loan-to-Cost ratio, loan_purpose, recourse_type,
interest_reserve) were absent from ALL credit underwriting document types. LTC is the
primary sizing metric for construction/bridge loans; without it, an underwriting
document cannot be reviewed.

**Impact:**
Critical C6 in swarm review. The domain logic lens identified this as a gap
"calibrated for stabilized lending, not transitional bridge."

**Fix Applied:**
Added ltc, loan_purpose, recourse_type, interest_reserve to critical_figures for
A4 Deal Memo and other credit underwriting document types. See domain-logic-fixes
evidence (2026-03-24).

### Incident: Draw Request Missing Core Fields

**What Happened:**
The Draw Request document template (a standard construction loan disbursement document)
was missing: inspector_name, inspection_date, contractor_name, retainage_amount,
approved_change_orders, lien_waiver_status. Every actual draw request must include these.

**Impact:**
High finding. A Draw Request without lien waiver status and retainage tracking is not
approvable by a construction lender.

**Fix Applied:**
Added 6 critical_figures and 3 structural benchmark items to the Draw Request template.

### Incident: LTV/DSCR Scoring Bands Calibrated for Stabilized Lending (High H10)

**What Happened:**
The recommendation matrix used LTV and DSCR thresholds calibrated for stabilized
income-producing properties. For bridge/transitional loans (pre-stabilization), these
thresholds are inappropriate — bridge loans routinely have higher LTC and lower current
DSCR than the matrix considered acceptable.

**Impact:**
The recommendation matrix would mis-score valid bridge loans as "DECLINE" based on
metrics that don't apply to their loan type.

**Fix Applied:**
Added `bridge_loan` entry to `edge_case_weights` with sponsor-heavy weighting (0.35)
and bridge-specific scoring bands. Added `loan_type_context` to recommendation matrix.

## The Correct Approach

### Do This Instead

Before designing any document template for a specialized domain:
1. Source the practitioner's "completeness checklist" for that document type
2. Use domain-expert reviewers (real practitioners, not generalists) to validate templates
3. Include a "domain logic" lens in every swarm review for specialized documents
4. For PE real estate lending: require LTC, exit strategy, recourse type, interest
   reserve, guarantor structure as baseline fields for all credit documents

### Why It Works

Practitioners accept documents that contain their complete mental checklist.
A document missing one critical field is worse than a simpler document that
covers the right fields — incompleteness is more visible than simplicity.

## Prevention Guide

### Warning Signs

- Document templates were designed without input from a domain practitioner
- Swarm review does not include a "domain logic" lens
- LTV is the only loan sizing metric (LTC should also be present for construction/bridge)
- No "Exit Strategy" section in any bridge lending document
- Document template critical_figures list < 10 items (most loan docs need 15-30)

### Prevention Checklist

- [ ] Source completeness checklists from domain practitioners BEFORE designing templates
- [ ] Include "domain logic" or "domain expert" lens in every swarm review
- [ ] For PE bridge lending: verify LTC, exit strategy, recourse type are present
- [ ] Cross-check document schema against peer documents from actual transactions
- [ ] After adding a new document type: have a practitioner review the critical_figures list

### Review Focus

For reviewers in the domain logic lens — check:
- Does the document include every field that a practitioner needs to make a decision?
- Are sizing metrics appropriate for the loan type (LTC for construction, LTV for stabilized)?
- Is there an Exit Strategy section for any bridge or transitional loan document?
- Are draw request documents complete for construction lender approval workflows?

## Related Anti-Patterns

- LEARN-ANTI-001 — Missing Data Contract Between Pipeline Stages

## Related Correct Patterns

- LEARN-REVIEW-001 — Multi-Round Swarm Review Remediation
- LEARN-WORKFLOW-002 — Pre-Generation Data Verification Gate

## Occurrence History

| Date | Project | Caught By | Severity |
|------|---------|-----------|----------|
| 2026-03-23 | EPIC-001 (Exit Strategy) | Swarm Review (Domain Logic) | HIGH |
| 2026-03-23 | EPIC-001 (LTC/bridge fields) | Swarm Review (Domain Logic) | CRITICAL |
| 2026-03-23 | EPIC-001 (Draw Request fields) | Swarm Review (Domain Logic) | HIGH |
| 2026-03-23 | EPIC-001 (scoring calibration) | Swarm Review (Domain Logic) | HIGH |

---

*Documented to prevent recurrence - ACOS Learning Curve Agent*
