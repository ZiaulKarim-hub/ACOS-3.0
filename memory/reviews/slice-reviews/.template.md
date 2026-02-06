# Review Report - [SLICE-ID]

**Reviewer:** [ACOS-qa-reviewer | ACOS-security-reviewer | etc.]
**Date:** [YYYY-MM-DD HH:MM:SS]
**Slice:** [SLICE-ID]
**Story:** [STORY-ID]
**Epic:** [EPIC-ID]

## ═══════════════════════════════════════
## VERDICT: [PASS / REJECT]
## ═══════════════════════════════════════

---

## Review Summary

**Overall Assessment:** [Brief 1-2 sentence summary]

**Evidence Quality:** [Excellent | Good | Fair | Poor]
**Scope Compliance:** [Compliant | Minor Violations | Major Violations]
**Code Quality:** [Excellent | Good | Acceptable | Needs Work | Unacceptable]

---

## Verification Against Source of Truth

**Source of Truth Reference:** `memory/source-of-truth/vision-document.md`

| User Intent | Implementation | Alignment |
|-------------|----------------|-----------|
| [Intent 1] | [How implemented] | [Aligned / Partially / Misaligned] |
| [Intent 2] | [How implemented] | [Aligned / Partially / Misaligned] |

---

## Acceptance Criteria Verification

| # | Criterion | Status | Verification Method | Notes |
|---|-----------|--------|---------------------|-------|
| 1 | [Criterion] | PASS/FAIL | [How verified] | [Notes] |
| 2 | [Criterion] | PASS/FAIL | [How verified] | [Notes] |
| 3 | [Criterion] | PASS/FAIL | [How verified] | [Notes] |

---

## Evidence Bundle Verification

**Evidence Path:** `.acos/evidence/[DATE]/[SLICE-ID]/`

### Files Present

- [x] `before/baseline-status.log`
- [x] `after/modified-files.txt`
- [x] `after/git-diff.patch`
- [x] `verify.log`
- [x] `Summary.md`

### Evidence Authenticity

| Check | Status | Notes |
|-------|--------|-------|
| Timestamps logical | PASS/FAIL | [Notes] |
| Results match independent verification | PASS/FAIL | [Notes] |
| No signs of fabrication | PASS/FAIL | [Notes] |

---

## Scope Compliance

**Files Modified:**
| File | Allowed | Changes |
|------|---------|---------|
| [file1] | Yes/No | [Brief description] |
| [file2] | Yes/No | [Brief description] |

**Scope Violations:** [None | List violations]

---

## [Reviewer-Specific Section]

### [For QA Reviewer]
- Code Quality: [Assessment]
- Error Handling: [Assessment]
- Test Coverage: [Assessment]

### [For Security Reviewer]
- Authentication: [N/A | PASS | FAIL]
- Authorization: [N/A | PASS | FAIL]
- Input Validation: [N/A | PASS | FAIL]
- Data Protection: [N/A | PASS | FAIL]

### [For Performance Reviewer]
- Time Complexity: [Assessment]
- Space Complexity: [Assessment]
- Database Queries: [N/A | Efficient | Needs Optimization]

### [For Integration Reviewer]
- API Contracts: [N/A | PASS | FAIL]
- Data Flow: [Assessment]
- Error Propagation: [Assessment]

---

## Issues Found

[For each issue, copy this block:]

### Issue [N]: [Title]

**Severity:** CRITICAL | HIGH | MEDIUM | LOW
**Category:** [security | performance | quality | scope | correctness]
**Location:** [File:Line or Component]

**Description:**
[Clear description of what's wrong]

**Expected:**
[What should be]

**Actual:**
[What was found]

**Impact:**
[What could go wrong if not fixed]

**Remediation:**
[Specific steps to fix]

**Code Example (if applicable):**

Current:
```
[problematic code]
```

Fixed:
```
[corrected code]
```

---

## Positive Observations

- [What was done well]
- [Good practices observed]

---

## Recommendation

**Verdict:** [PASS / REJECT]

[If PASS:]
The implementation meets all acceptance criteria and passes quality checks.

[If REJECT:]

### Required Before Resubmission:

1. [Critical fix 1]
2. [Critical fix 2]
3. [Critical fix 3]

### Recommended Improvements:

1. [Optional improvement 1]
2. [Optional improvement 2]

---

## Review Metadata

- **Review Duration:** [X minutes]
- **Independent Verification:** [Yes/No - what was tested]
- **Tools Used:** [Any tools used for analysis]

---

*Review completed by [Reviewer Name]*
