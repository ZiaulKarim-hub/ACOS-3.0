# Story Review Report - [STORY-ID]

**Reviewer:** [ACOS-qa-reviewer | ACOS-integration-reviewer | etc.]
**Date:** [YYYY-MM-DD HH:MM:SS]
**Story:** [STORY-ID]
**Epic:** [EPIC-ID]
**Vision:** [VISION-ID]

## ═══════════════════════════════════════
## VERDICT: [PASS / REJECT]
## ═══════════════════════════════════════

---

## Review Summary

**Overall Assessment:** [Brief 1-2 sentence summary]

**Slices Reviewed:** [N] slices
**Integration Quality:** [Excellent | Good | Acceptable | Needs Work]
**Feature Completeness:** [Complete | Partial | Incomplete]

---

## Slice Review Summary

| Slice ID | Verdict | Key Issues |
|----------|---------|------------|
| [SLICE-XXX-001] | PASS/FAIL | [Brief summary] |
| [SLICE-XXX-002] | PASS/FAIL | [Brief summary] |
| [SLICE-XXX-003] | PASS/FAIL | [Brief summary] |

---

## User Story Verification

**User Story:**
> As a [user type], I want to [action], so that [benefit].

**Verification:**

| Aspect | Status | Notes |
|--------|--------|-------|
| User can perform the action | PASS/FAIL | [Notes] |
| Benefit is achieved | PASS/FAIL | [Notes] |
| Edge cases handled | PASS/FAIL | [Notes] |

---

## Acceptance Criteria Verification

| # | Criterion | Status | How Verified |
|---|-----------|--------|--------------|
| 1 | [Criterion] | PASS/FAIL | [Verification method] |
| 2 | [Criterion] | PASS/FAIL | [Verification method] |
| 3 | [Criterion] | PASS/FAIL | [Verification method] |

---

## Integration Check

**Status:** [PASS / FAIL]

### Slice Integration

- [ ] All slices work together correctly
- [ ] Data flows properly between slices
- [ ] No conflicts or race conditions
- [ ] Error states handled across slices

**Findings:**
- [Finding if any]

### Story-Level Functionality

- [ ] Feature works end-to-end
- [ ] User journey is complete
- [ ] All entry and exit points work

**Findings:**
- [Finding if any]

---

## [Reviewer-Specific Section]

### For QA Reviewer
- Feature Completeness: [Assessment]
- User Experience: [Assessment]
- Error Handling: [Assessment]

### For Integration Reviewer
- Slice Integration: [Assessment]
- Data Consistency: [Assessment]
- API Contracts: [Assessment]

### For Security Reviewer (if applicable)
- Authentication: [Assessment]
- Authorization: [Assessment]
- Data Protection: [Assessment]

### For Performance Reviewer (if applicable)
- Response Times: [Assessment]
- Resource Usage: [Assessment]
- Scalability: [Assessment]

---

## Issues Found

[For each issue:]

### Issue [N]: [Title]

**Severity:** CRITICAL | HIGH | MEDIUM | LOW
**Scope:** [Single slice | Multiple slices | Story-wide]
**Slices Affected:** [List of slice IDs]

**Description:**
[What's wrong]

**Impact:**
[How this affects the feature]

**Remediation:**
[How to fix]

---

## Positive Observations

- [What was done well]
- [Good patterns observed]
- [Effective approaches used]

---

## Recommendation

**Verdict:** [PASS / REJECT]

[If PASS:]
The story delivers the expected feature and all acceptance criteria are met.

[If REJECT:]

### Required Before Resubmission:

1. [Critical fix 1]
2. [Critical fix 2]

### Slices Requiring Rework:

| Slice ID | Required Changes |
|----------|------------------|
| [SLICE-XXX] | [What needs to change] |

---

## Review Metadata

- **Review Duration:** [X minutes]
- **Slices Reviewed:** [N]
- **Evidence Bundles Checked:** [N]

---

*Story Review completed by [Reviewer Name]*
