---
name: acos-feedback-resolution
description: Resolves reviewer feedback by creating a unified fix plan, delegating implementation, and triggering re-review. Handles conflicts between reviewers. Max 3 iterations.
disable-model-invocation: true
user-invocable: false
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
context: fork
agent: architect
---

# Feedback Resolution

## Overview

This internal skill resolves reviewer feedback after a rejection. It analyzes all feedback, creates a unified fix plan that addresses all issues without conflicts, delegates the fix to the developer, and triggers a re-review. It iterates up to 3 times before escalating to the human.

**This skill is internal only** — it is called by `acos-execute-slice` when reviews fail, not invoked directly by users.

## Protocol

### Step 1: Analyze All Feedback

Receive consolidated feedback from all rejecting reviewers. For each issue:
- Categorize by severity (CRITICAL, HIGH, MEDIUM, LOW)
- Identify the affected files and code locations
- Note specific fix requirements

### Step 2: Detect Conflicts

Check for conflicts between reviewer feedback:
- Does fixing one issue contradict another reviewer's requirement?
- Are there mutually exclusive recommendations?
- If conflicts exist, create a resolution strategy that satisfies both concerns

### Step 3: Create Unified Fix Plan

Create ONE coherent plan that addresses ALL issues:
- Prioritize CRITICAL and HIGH issues
- Group related fixes
- Ensure fixes don't conflict with each other
- Specify exact changes needed

### Step 4: Delegate Fix to Developer

Use `Task(developer)` with:
- The unified fix plan
- Original slice spec (for context)
- Specific issues to address with their locations
- Files allowed to modify
- Updated evidence bundle path

### Step 5: Re-Review

After the developer returns with fixes:
1. Run reviewer assignment again (same reviewers as original)
2. Spawn reviewers in parallel with updated evidence
3. Collect verdicts

### Step 6: Decision

- If ALL PASS: return success to caller
- If ANY REJECT and iteration < 3: loop back to Step 1 with new feedback
- If ANY REJECT and iteration >= 3: escalate to human

### Step 7: Escalation (if needed)

If 3 iterations fail:
- Summarize all attempts and remaining issues
- Present to the user for manual intervention
- Return failure with context

## Iteration Tracking

```yaml
iteration: [1-3]
original_issues: [count]
resolved_issues: [count]
remaining_issues: [count]
new_issues: [count]  # Issues introduced by fixes
```

---

*Feedback Resolution - Converging on quality through iteration.*
