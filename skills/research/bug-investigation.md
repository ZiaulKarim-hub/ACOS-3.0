---
name: bug-investigation
description: Skill for systematically investigating and diagnosing bugs
version: 1.0.0
created_by: architect
created_date: 2026-01-31

category: research

applicable_to:
  - ACOS-developer
  - the-architect
  - any-agent

tools_required:
  - Read
  - Glob
  - Grep
  - Bash
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

1. **Clarify the bug:**
   - What is the expected behavior?
   - What is the actual behavior?
   - Can it be reproduced consistently?
   - What are the steps to reproduce?

2. **Gather context:**
   - When did it start?
   - What changed recently?
   - Who reported it?
   - What's the impact?

### Phase 2: Reproduction

1. **Reproduce the bug:**
   - Follow exact steps provided
   - Note any variations
   - Confirm the bug exists

2. **Isolate the conditions:**
   - What inputs trigger it?
   - What environment factors matter?
   - Is it intermittent or consistent?

### Phase 3: Investigation

1. **Form hypotheses:**
   - What could cause this behavior?
   - List possible causes
   - Rank by likelihood

2. **Investigate systematically:**
   - Start with most likely cause
   - Trace the code path
   - Check logs and error messages
   - Add debug output if needed

3. **Narrow down:**
   - Eliminate hypotheses
   - Pinpoint the location
   - Identify the root cause

### Phase 4: Documentation

1. **Document findings:**
   - Root cause identified
   - Code location
   - Why it happens
   - How to fix

## Investigation Checklist

### Information Gathering

- [ ] Bug clearly defined
- [ ] Steps to reproduce documented
- [ ] Expected vs actual behavior clear
- [ ] Environment details captured

### Reproduction

- [ ] Bug successfully reproduced
- [ ] Minimal reproduction case found
- [ ] Conditions isolated

### Root Cause

- [ ] Code path traced
- [ ] Root cause identified
- [ ] Understanding verified

### Documentation

- [ ] Finding documented
- [ ] Fix approach proposed
- [ ] Related issues noted

## Investigation Techniques

### 1. Binary Search (Bisection)

When: Bug was introduced at some point

```
1. Find a known good version
2. Find a known bad version
3. Test the middle
4. Repeat until you find the introducing change
```

### 2. Print/Log Debugging

When: Need to trace execution flow

```javascript
console.log('[DEBUG] Function entered:', { param1, param2 });
console.log('[DEBUG] State at checkpoint:', state);
console.log('[DEBUG] Result:', result);
```

### 3. Rubber Duck Debugging

When: Stuck and need fresh perspective

```
1. Explain the code line by line
2. Explain what you expect to happen
3. Explain what actually happens
4. The discrepancy often reveals the bug
```

### 4. Stack Trace Analysis

When: Error with stack trace

```
1. Read the error message carefully
2. Find the first line in YOUR code
3. Examine that location
4. Trace back to find the cause
```

### 5. State Inspection

When: Unexpected state

```
1. Log state at entry
2. Log state after each transformation
3. Find where state diverges from expected
```

### 6. Dependency Check

When: Bug might be external

```
1. Check dependency versions
2. Look for known issues
3. Test with different versions
4. Check for breaking changes
```

## Common Bug Patterns

| Pattern | Symptoms | Common Cause |
|---------|----------|--------------|
| Off-by-one | Wrong count, missing item | Loop bounds, array indices |
| Null reference | Crash, undefined | Missing null check |
| Race condition | Intermittent | Async timing |
| State mutation | Unexpected values | Shared mutable state |
| Type coercion | Wrong comparisons | Loose equality, implicit conversion |
| Scope issues | Wrong variable | Variable shadowing, closure |

## Investigation Commands

```bash
# Search for recent changes to a file
git log --oneline -10 path/to/file.ts

# Find when a line was added
git log -S "problematic code" --oneline

# Compare versions
git diff commit1..commit2 path/to/file.ts

# Find all uses of a function
grep -r "functionName" --include="*.ts"

# Check for similar patterns
grep -r "similar pattern" --include="*.ts"
```

## Output: Bug Investigation Report

```markdown
# Bug Investigation Report

**Bug ID:** [If applicable]
**Investigator:** [Agent name]
**Date:** [YYYY-MM-DD]

## Bug Description

**Expected:** [What should happen]
**Actual:** [What happens]
**Reproducible:** [Always | Sometimes | Rarely]

## Steps to Reproduce

1. [Step 1]
2. [Step 2]
3. [Step 3]

## Investigation Process

### Hypotheses Tested

1. **[Hypothesis 1]:** [Result - confirmed/rejected]
2. **[Hypothesis 2]:** [Result - confirmed/rejected]

### Evidence Gathered

- [Evidence 1]
- [Evidence 2]

## Root Cause

**Location:** `path/to/file.ts:123`

**Cause:**
[Explanation of why the bug occurs]

**Code:**
```
[Problematic code snippet]
```

## Proposed Fix

**Approach:**
[How to fix it]

**Code Change:**
```
[Fixed code snippet]
```

## Related Issues

- [Any related bugs or considerations]

## Prevention

[How to prevent similar bugs in the future]
```

---

*Bug Investigation Skill - Finding the needle in the haystack.*
