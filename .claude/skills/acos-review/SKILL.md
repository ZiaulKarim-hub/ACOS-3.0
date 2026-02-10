---
name: acos-review
description: Triggers a review for completed work. Programmatically assigns reviewers using review-rules.yaml and spawns parallel review agents.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Glob, Grep, Bash
context: fork
agent: architect
---

# ACOS Review

## Overview

This skill triggers a review for completed work at any level (slice, story, epic, vision). It programmatically assigns reviewers using `review-rules.yaml` and spawns parallel, independent review agents.

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

The script reads `review-rules.yaml` mechanically and returns a JSON array of reviewer names.

### Step 4: Spawn Reviewers in Parallel

For each assigned reviewer, use `Task([reviewer-name])` simultaneously. Pass:
- Evidence bundle path
- Source of truth path: `memory/source-of-truth/vision-document.md`
- Work specification path

**Domain Security Profile Injection:** When spawning the `security-reviewer`, check for `.acos/config/security-profile.md`. If present, read its contents and include them in the `Task(security-reviewer)` prompt as an additional "Domain Security Context" section. This gives the security reviewer domain-specific threat awareness without modifying its core agent definition. If no profile file exists, spawn the security-reviewer with standard context only.

Each reviewer runs in an isolated context and returns a structured verdict.

### Step 5: Aggregate and Report

Collect all verdicts:
- Present each reviewer's verdict and findings
- If ALL PASS: mark work as reviewed and passed
- If ANY REJECT: present consolidated feedback with required fixes

Use review templates from `!cat templates/slice-review.md` (or story/epic/vision as appropriate) for storing results.

---

*ACOS Review - Independent verification through adversarial review.*
