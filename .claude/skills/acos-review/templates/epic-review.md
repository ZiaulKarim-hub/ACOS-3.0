# Epic Review Report - [EPIC-ID]

**Reviewer:** [ACOS-qa-reviewer | ACOS-integration-reviewer | etc.]
**Date:** [YYYY-MM-DD HH:MM:SS]
**Epic:** [EPIC-ID]
**Vision:** [VISION-ID]

## ═══════════════════════════════════════
## VERDICT: [PASS / REJECT]
## ═══════════════════════════════════════

---

## Review Summary

**Overall Assessment:** [Brief 2-3 sentence summary]

**Capability Delivered:** [Yes/No/Partial]
**Stories Reviewed:** [N] stories ([N] slices total)
**Integration Quality:** [Excellent | Good | Acceptable | Needs Work]

---

## Capability Assessment

**Epic Objective:**
> [What capability this epic was supposed to deliver]

**Capability Delivered:**

| Aspect | Status | Notes |
|--------|--------|-------|
| Core functionality works | PASS/FAIL | [Notes] |
| All user journeys complete | PASS/FAIL | [Notes] |
| Performance acceptable | PASS/FAIL | [Notes] |
| Security requirements met | PASS/FAIL | [Notes] |

---

## Story Review Summary

| Story ID | Title | Verdict | Key Issues |
|----------|-------|---------|------------|
| [STORY-XXX-001] | [Title] | PASS/FAIL | [Brief summary] |
| [STORY-XXX-002] | [Title] | PASS/FAIL | [Brief summary] |
| [STORY-XXX-003] | [Title] | PASS/FAIL | [Brief summary] |

---

## Acceptance Criteria Verification

| # | Epic Criterion | Status | Evidence |
|---|----------------|--------|----------|
| 1 | [Criterion] | PASS/FAIL | [How verified] |
| 2 | [Criterion] | PASS/FAIL | [How verified] |
| 3 | [Criterion] | PASS/FAIL | [How verified] |

---

## Cross-Story Integration

**Status:** [PASS / FAIL]

### Story Integration Check

- [ ] All stories work together as a capability
- [ ] Data flows correctly between stories
- [ ] Shared components work consistently
- [ ] No conflicting behaviors

**Integration Test Results:**

| Integration Point | Stories Involved | Status | Notes |
|-------------------|------------------|--------|-------|
| [Integration 1] | [STORY-A, STORY-B] | PASS/FAIL | [Notes] |
| [Integration 2] | [STORY-B, STORY-C] | PASS/FAIL | [Notes] |

**Findings:**
- [Finding if any]

---

## Performance at Scale

**Status:** [PASS / FAIL / N/A]

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| [Response time] | [<Xms] | [Yms] | PASS/FAIL |
| [Throughput] | [>X/sec] | [Y/sec] | PASS/FAIL |
| [Resource usage] | [<X%] | [Y%] | PASS/FAIL |

**Findings:**
- [Finding if any]

---

## Security Assessment

**Status:** [PASS / FAIL / N/A]

- [ ] Authentication properly implemented
- [ ] Authorization checks in place
- [ ] Sensitive data protected
- [ ] No known vulnerabilities

**Findings:**
- [Finding if any]

---

## User Journey Verification

**Primary User Journeys:**

| Journey | Description | Status | Notes |
|---------|-------------|--------|-------|
| Journey 1 | [User can do X] | PASS/FAIL | [Notes] |
| Journey 2 | [User can do Y] | PASS/FAIL | [Notes] |

---

## Issues Found

[For each issue:]

### Issue [N]: [Title]

**Severity:** CRITICAL | HIGH | MEDIUM | LOW
**Scope:** [Single story | Multiple stories | Epic-wide]
**Stories Affected:** [List of story IDs]

**Description:**
[What's wrong at the capability level]

**Impact:**
[How this affects the overall capability]

**Remediation:**
[How to fix - may require changes to multiple stories]

---

## Positive Observations

- [What was done well at the epic level]
- [Good architectural decisions]
- [Effective integration approaches]

---

## Recommendation

**Verdict:** [PASS / REJECT]

[If PASS:]
The epic delivers the expected capability. All stories integrate correctly and acceptance criteria are met.

[If REJECT:]

### Required Before Resubmission:

1. [Critical fix 1 - may span multiple stories]
2. [Critical fix 2]

### Stories Requiring Rework:

| Story ID | Required Changes |
|----------|------------------|
| [STORY-XXX] | [What needs to change] |

---

## Comparison with Source of Truth

**Vision Document Reference:** `memory/source-of-truth/vision-document.md`

| Original Requirement | Implementation | Alignment |
|---------------------|----------------|-----------|
| [Requirement 1] | [How implemented] | [Aligned/Deviated] |
| [Requirement 2] | [How implemented] | [Aligned/Deviated] |

---

## Review Metadata

- **Review Duration:** [X minutes]
- **Stories Reviewed:** [N]
- **Total Slices in Epic:** [N]
- **Evidence Bundles Checked:** [N]

---

*Epic Review completed by [Reviewer Name]*
