---
name: acos-review
description: Triggers a review for completed work. Programmatically assigns reviewers using per-reviewer rule files and spawns parallel review agents.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Glob, Grep, Bash
context: fork
agent: architect
---

# ACOS Review

## Overview

This skill triggers a review for completed work at any level (slice, story, epic, vision). It programmatically assigns reviewers using per-reviewer rule files in `review-rules/` and spawns parallel, independent review agents.

### Pre-flight: Auto-Bootstrap

Before proceeding, ensure ACOS is initialized in this project:

```bash
bash .claude/scripts/acos-preflight.sh
```

This is idempotent — it exits immediately if ACOS is already initialized. If not, it runs the full bootstrap (symlinks, directories, config, gitignore).

## Protocol

### Step 1: Determine What to Review

If `$ARGUMENTS` is provided, use it as the slice/story/epic ID.
Otherwise:
- Check for slices with `status: ready_for_review`
- Check for stories where all slices are complete
- If multiple options, list them for the Architect to choose

### Step 2: Validate Evidence

Run `.claude/scripts/validate-evidence.sh [ID]` to ensure the evidence bundle is complete.
If validation fails, report what's missing and abort.

### Step 3: Assign Reviewers

Pipe a JSON manifest to `.claude/scripts/assign-reviewers.sh`:

```json
{
  "slice_id": "[ID]",
  "files_modified": ["list of modified files"],
  "code_snippets": ["key code patterns"],
  "review_level": "slice|story|epic|vision"
}
```

The script reads per-reviewer rule files from `review-rules/` mechanically and returns a JSON array of reviewer names.

### Step 4: Spawn Reviewers in Parallel

**CRITICAL: All assigned reviewers MUST be spawned simultaneously in a SINGLE message with multiple `Task()` calls.** Do not spawn them sequentially.

For each assigned reviewer, use `Task([reviewer-name])` with these settings:

```
Task([reviewer-name])
  - run_in_background: true    (non-blocking, true parallelism)
  - isolation: worktree        (each reviewer gets its own codebase copy)
  - model: opus                (maximum review quality)
```

**Prompt structure for each reviewer:**
- Evidence bundle path
- Source of truth path: `memory/source-of-truth/vision-document.md`
- Work specification path (slice/story/epic spec)

**Domain Security Profile Injection:** When spawning the `security-reviewer`, check for `.acos/config/security-profile.md`. If present, read its contents and include them in the `Task(security-reviewer)` prompt as an additional "Domain Security Context" section. This gives the security reviewer domain-specific threat awareness without modifying its core agent definition. If no profile file exists, spawn the security-reviewer with standard context only.

### Step 5: Collect Results with Failure Handling

After spawning all reviewers in the background, collect results:

1. **Poll for completion:** Check each background task for results.

2. **Handle reviewer failures gracefully:**
   - If a reviewer agent crashes or returns no verdict, treat it as **INCONCLUSIVE**, not as a pass.
   - Log the failure: `"[reviewer-name] returned no verdict — marking INCONCLUSIVE"`
   - An INCONCLUSIVE result blocks approval just like a REJECT.

3. **Handle partial results:**
   - If 3 of 4 reviewers complete but one is still running, wait for all.
   - Never aggregate partial results — all assigned reviewers must report.

4. **Result validation:** Each reviewer should return a structured verdict with:
   - `verdict: PASS | REJECT`
   - `reviewer: [name]`
   - `slice_id: [ID]`
   - Detailed scores and issues

### Step 6: Aggregate and Report

Collect all verdicts:
- Present each reviewer's verdict and findings
- If ALL PASS: mark work as reviewed and passed
- If ANY REJECT or INCONCLUSIVE: present consolidated feedback with required fixes
- Group issues by severity (CRITICAL > HIGH > MEDIUM > LOW)
- Deduplicate overlapping findings from different reviewers

Use review templates from `!cat templates/slice-review.md` (or story/epic/vision as appropriate) for storing results.

---

*ACOS Review - Independent verification through adversarial review.*
