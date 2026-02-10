# Vision Review Report - [VISION-ID]

**Reviewer:** [ACOS-qa-reviewer | ACOS-security-reviewer | etc.]
**Date:** [YYYY-MM-DD HH:MM:SS]
**Vision:** [VISION-ID]
**Project Name:** [Project Name]

## ═══════════════════════════════════════
## VERDICT: [PASS / REJECT]
## ═══════════════════════════════════════

---

## Review Summary

**Overall Assessment:** [3-4 sentence comprehensive summary]

**Vision Fulfilled:** [Yes / No / Partial]
**System Quality:** [Excellent | Good | Acceptable | Needs Work]
**Ready for User:** [Yes / No]

---

## Project Scope Summary

| Metric | Count |
|--------|-------|
| Epics Completed | [N] |
| Stories Completed | [N] |
| Slices Completed | [N] |
| Total Reviews Conducted | [N] |

---

## Vision Fulfillment Check

**Source of Truth:** `memory/source-of-truth/vision-document.md`

### Original Vision Statement
> [The original vision statement from the interview]

### Fulfillment Assessment

| Original Requirement | Status | Implementation Notes |
|---------------------|--------|---------------------|
| [Requirement 1] | ✓ MET / ✗ NOT MET / ⚠ PARTIAL | [How it was implemented] |
| [Requirement 2] | ✓ MET / ✗ NOT MET / ⚠ PARTIAL | [Notes] |
| [Requirement 3] | ✓ MET / ✗ NOT MET / ⚠ PARTIAL | [Notes] |

### Success Criteria Verification

| Success Criterion | Measurable Target | Actual Result | Status |
|-------------------|-------------------|---------------|--------|
| [Criterion 1] | [Target] | [Result] | PASS/FAIL |
| [Criterion 2] | [Target] | [Result] | PASS/FAIL |

---

## Epic Review Summary

| Epic ID | Title | Verdict | Capability Delivered |
|---------|-------|---------|---------------------|
| [EPIC-001] | [Title] | PASS/FAIL | [Yes/No/Partial] |
| [EPIC-002] | [Title] | PASS/FAIL | [Yes/No/Partial] |
| [EPIC-003] | [Title] | PASS/FAIL | [Yes/No/Partial] |

---

## System-Wide Integration

**Status:** [PASS / FAIL]

### Cross-Epic Integration

- [ ] All epics work together as a complete system
- [ ] Data flows correctly across the entire system
- [ ] User can achieve end-to-end goals
- [ ] No conflicting behaviors between epics

**Integration Test Results:**

| Integration Point | Epics Involved | Status | Notes |
|-------------------|----------------|--------|-------|
| [System Integration 1] | [EPIC-A, EPIC-B] | PASS/FAIL | [Notes] |
| [System Integration 2] | [All] | PASS/FAIL | [Notes] |

---

## System-Wide Quality Assessment

### Functionality
**Status:** [PASS / FAIL]

- [ ] All features work as specified
- [ ] Edge cases handled appropriately
- [ ] Error handling is comprehensive
- [ ] User journeys are complete

### Performance
**Status:** [PASS / FAIL]

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Page load time | [<Xs] | [Ys] | PASS/FAIL |
| API response time | [<Xms] | [Yms] | PASS/FAIL |
| Concurrent users | [>X] | [Y] | PASS/FAIL |

### Security
**Status:** [PASS / FAIL]

- [ ] Authentication is secure
- [ ] Authorization is properly enforced
- [ ] Data is protected
- [ ] No critical vulnerabilities
- [ ] OWASP Top 10 addressed

### Scalability
**Status:** [PASS / FAIL / N/A]

- [ ] System can handle expected load
- [ ] Horizontal scaling is possible
- [ ] No single points of failure

---

## User Journey Verification

**Complete User Journeys:**

| Journey | User Type | Description | Status |
|---------|-----------|-------------|--------|
| Primary Journey 1 | [User type] | [Full description] | PASS/FAIL |
| Primary Journey 2 | [User type] | [Full description] | PASS/FAIL |
| Secondary Journey 1 | [User type] | [Description] | PASS/FAIL |

---

## Platform Verification

| Platform | Required | Implemented | Status | Notes |
|----------|----------|-------------|--------|-------|
| Web (Desktop) | Yes/No | Yes/No | PASS/FAIL/N/A | [Notes] |
| Web (Mobile) | Yes/No | Yes/No | PASS/FAIL/N/A | [Notes] |
| iOS App | Yes/No | Yes/No | PASS/FAIL/N/A | [Notes] |
| Android App | Yes/No | Yes/No | PASS/FAIL/N/A | [Notes] |

---

## Issues Found

[For each issue:]

### Issue [N]: [Title]

**Severity:** CRITICAL | HIGH | MEDIUM | LOW
**Scope:** [System-wide | Epic-specific | Localized]
**Epics Affected:** [List of epic IDs]

**Description:**
[What's wrong at the system level]

**Impact:**
[How this affects the overall vision fulfillment]

**Remediation:**
[How to fix - may require changes across multiple epics]

---

## Deviations from Vision

[Any approved or unapproved deviations from the original vision]

| Deviation | Original | Actual | Approved | Reason |
|-----------|----------|--------|----------|--------|
| [Deviation 1] | [Original spec] | [What was built] | Yes/No | [Why] |

---

## Positive Observations

- [What was done exceptionally well]
- [Good architectural decisions at system level]
- [Effective approaches that should be documented as learnings]

---

## Recommendation

**Verdict:** [PASS / REJECT]

[If PASS:]
The system fulfills the original vision. All requirements are met, the system is secure, performant, and ready for user acceptance.

**Recommended for User Acceptance Testing:** Yes

[If REJECT:]

### Critical Issues Blocking Approval:

1. [Critical issue 1]
2. [Critical issue 2]

### Epics Requiring Rework:

| Epic ID | Required Changes |
|---------|------------------|
| [EPIC-XXX] | [What needs to change] |

### Recommendation:

[Specific guidance on what must be addressed before resubmission]

---

## Pre-Launch Checklist

- [ ] All acceptance criteria met
- [ ] All user journeys verified
- [ ] Security review passed
- [ ] Performance targets met
- [ ] Documentation complete
- [ ] Deployment plan ready

---

## Review Metadata

- **Review Duration:** [X hours]
- **Epics Reviewed:** [N]
- **Stories Reviewed:** [N]
- **Total Slices:** [N]
- **Evidence Bundles Checked:** [N]
- **Source of Truth Verified:** Yes

---

*Vision Review completed by [Reviewer Name]*

---

## Sign-Off

This system has been reviewed against the original vision document and is:

**[ ] APPROVED** for user acceptance
**[ ] REJECTED** - requires rework

**Reviewer Signature:** [Reviewer Name]
**Date:** [YYYY-MM-DD]
