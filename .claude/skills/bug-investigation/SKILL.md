---
name: bug-investigation
description: Systematic approach to investigating bugs, identifying root causes, and documenting findings for resolution. Covers bisection, log debugging, stack trace analysis.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash
---

# Bug Investigation Skill

## Purpose

This skill provides a systematic approach to investigating bugs, identifying root causes, and documenting findings for resolution.

## When to Use

Apply this skill when:
- A bug has been reported
- Tests are failing unexpectedly
- Unexpected behavior is observed
- Reviewers report issues
- Users report problems

## Skill Protocol

### Phase 1: Bug Definition

1. **Clarify the bug:** Expected vs actual behavior, reproducibility, steps to reproduce
2. **Gather context:** When did it start? What changed recently? What's the impact?

### Phase 2: Reproduction

1. Follow exact steps provided, note variations, confirm the bug exists
2. Isolate conditions: What inputs trigger it? What environment factors matter?

### Phase 3: Investigation

1. **Form hypotheses:** List possible causes, rank by likelihood
2. **Investigate systematically:** Start with most likely, trace code path, check logs
3. **Narrow down:** Eliminate hypotheses, pinpoint location, identify root cause

### Phase 4: Documentation

Document findings: root cause, code location, why it happens, how to fix

## Investigation Techniques

### 1. Binary Search (Bisection)
Find known good version, find known bad version, test the middle, repeat.

### 2. Print/Log Debugging
Trace execution flow with strategic log statements.

### 3. Stack Trace Analysis
Read error message, find first line in YOUR code, examine that location, trace back.

### 4. State Inspection
Log state at entry, after each transformation, find where state diverges from expected.

## Common Bug Patterns

| Pattern | Symptoms | Common Cause |
|---------|----------|--------------|
| Off-by-one | Wrong count, missing item | Loop bounds, array indices |
| Null reference | Crash, undefined | Missing null check |
| Race condition | Intermittent | Async timing |
| State mutation | Unexpected values | Shared mutable state |
| Type coercion | Wrong comparisons | Loose equality, implicit conversion |

## Output: Bug Investigation Report

```markdown
# Bug Investigation Report

**Expected:** [What should happen]
**Actual:** [What happens]
**Reproducible:** [Always | Sometimes | Rarely]

## Root Cause
**Location:** `path/to/file.ts:123`
**Cause:** [Explanation]

## Proposed Fix
[Approach and code change]
```

---

*Bug Investigation Skill - Finding the needle in the haystack.*
