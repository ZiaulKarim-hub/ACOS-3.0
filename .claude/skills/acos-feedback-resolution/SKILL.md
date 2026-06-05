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

### Step 5: Re-Review (BLIND)

Re-review must be **blind**: reviewers must NOT be told what previously failed, or they anchor on "is the prior issue fixed?" instead of independently re-assessing the whole slice. (A fix can resolve the flagged issue while introducing a new one a primed reviewer skips past.)

1. Run reviewer assignment again on the UPDATED files (`assign-reviewers.sh` — same trigger rules typically yield the same set).
2. Spawn reviewers in parallel. Pass each **ONLY**: the updated code / evidence bundle, the original slice spec, and the acceptance criteria. Do **NOT** pass the prior round's consolidated feedback, prior reviewer verdicts, the fix plan, or the developer's fix rationale. Each reviewer re-evaluates from scratch against the acceptance criteria as if seeing the slice for the first time.
3. Record each raw verdict to `.acos/state/review-verdicts/<slice_id>/<reviewer>.json` (overwriting the prior round) and the assigned list to `expected.json`.

### Step 6: Decision (Mechanical Gate)

Run the authoritative gate — do not judge it yourself (same binding gate as acos-execute-slice Step 8):

```bash
bash .claude/scripts/aggregate-verdicts.sh <slice_id>
```

- exit 0 (`decision: PASS`): return success to caller.
- exit 2 and iteration < 3: loop back to Step 1 with the new feedback.
- exit 2 and iteration >= 3: escalate to human (Step 7).

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
