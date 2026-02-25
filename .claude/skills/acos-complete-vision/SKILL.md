---
name: acos-complete-vision
description: Master orchestrator that completes an entire vision by executing all epics, running vision-level review, obtaining user acceptance, extracting learnings, and archiving.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
context: fork
agent: architect
---

# Vision Completion

## Overview

This is the master orchestration skill. It completes an entire project vision by executing all epics in order, running a vision-level review with all reviewers, obtaining user acceptance, extracting learnings, and archiving the project.

### Pre-flight: Auto-Bootstrap

Before proceeding, ensure ACOS is initialized in this project:

```bash
bash .claude/scripts/acos-preflight.sh
```

This is idempotent — it exits immediately if ACOS is already initialized. If not, it runs the full bootstrap (symlinks, directories, config, gitignore).

## Protocol

### Step 1: Read Vision Document

Read `memory/source-of-truth/vision-document.md`. Extract:
- All epics in execution order
- Vision-level success criteria
- Overall project scope

### Step 2: Execute Epics in Order

For each epic in the vision:
1. Invoke the `acos-execute-epic` skill with the epic ID
2. Wait for completion
3. Verify the epic passed all reviews
4. Report progress to user between epics

### Step 3: Vision-Level Review

**Model Resolution & Dispatch:** Before spawning any reviewer, resolve its model:
```bash
RESOLVED=$(bash .claude/scripts/resolve-agent-model.sh <reviewer-name>)
```

**Dispatch rule:** If the resolved model is a bare Claude name (no `:`) → use `Task()`. If it contains `:` (e.g., `openai:gpt-4o`) → use `Bash` with `run-external-agent.py` (see acos-review skill for full dispatch pattern). For external models, pre-read relevant code files and pass them via `--context`.

After all epics are complete, trigger vision-level review (all spawned simultaneously):
1. qa-reviewer — verify all vision success criteria are met
2. security-reviewer — verify security across entire project
3. performance-reviewer — verify performance at project scale
4. integration-reviewer — verify all epics integrate correctly

Pass to each reviewer:
- Complete project evidence
- Vision document (source of truth)
- All epic specifications

### Step 4: User Acceptance

Present the completed vision to the user:
- Summary of what was built
- All epics and their status
- Review verdicts
- Any notable decisions or trade-offs

Obtain user sign-off.

### Step 5: Learning Extraction

Invoke the `acos-learn` skill to:
- Extract patterns from completed work
- Identify what worked well and what didn't
- Create project retrospective
- Update the learning curve knowledge base

### Step 6: Project Archival

Run `.claude/scripts/archive-project.sh` to:
- Archive all memory, planning, and evidence
- Create manifest document
- Optionally clear current project state

### Step 7: Completion

Report final project completion with summary statistics.

---

*Vision Completion - From idea to reality.*
