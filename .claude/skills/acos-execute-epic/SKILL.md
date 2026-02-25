---
name: acos-execute-epic
description: Completes an epic by executing all its stories in order, then performing epic-level review with all reviewers. Use with $ARGUMENTS for the epic ID.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
context: fork
agent: architect
---

# Epic Execution

## Overview

This skill completes a full epic by executing all its constituent stories in order, then triggering an epic-level review with all four reviewers to verify that the entire capability works correctly.

### Pre-flight: Auto-Bootstrap

Before proceeding, ensure ACOS is initialized in this project:

```bash
bash .claude/scripts/acos-preflight.sh
```

This is idempotent — it exits immediately if ACOS is already initialized. If not, it runs the full bootstrap (symlinks, directories, config, gitignore).

## Protocol

### Step 1: Read Epic Specification

Read the epic spec from `planning/epics/$ARGUMENTS.yaml`. Extract:
- Epic objective and capability description
- List of stories in execution order
- Epic-level acceptance criteria

### Step 2: Execute Stories in Order

For each story in the epic:
1. Invoke the `acos-execute-story` skill with the story ID
2. Wait for completion
3. Verify the story passed all reviews
4. If a story fails and cannot be resolved, pause and escalate

### Step 3: Epic-Level Review

**Model Resolution & Dispatch:** Before spawning any reviewer, resolve its model:
```bash
RESOLVED=$(bash .claude/scripts/resolve-agent-model.sh <reviewer-name>)
```

**Dispatch rule:** If the resolved model is a bare Claude name (no `:`) → use `Task()`. If it contains `:` (e.g., `openai:gpt-4o`) → use `Bash` with `run-external-agent.py` (see acos-review skill for full dispatch pattern). For external models, pre-read relevant code files and pass them via `--context`.

After all stories are complete, trigger epic-level review (all spawned simultaneously):
1. qa-reviewer — verify epic-level acceptance criteria
2. security-reviewer — verify security across the capability
3. performance-reviewer — verify performance at epic scale
4. integration-reviewer — verify all stories integrate correctly

Pass to each reviewer:
- All evidence bundles from constituent stories
- Epic specification
- Source of truth

### Step 4: Aggregate Epic Verdicts

- ALL must PASS for epic completion
- ANY REJECT triggers feedback resolution at the epic level

### Step 5: Completion

1. Update epic status in `planning/epics/$ARGUMENTS.yaml` to `status: completed`
2. Write epic completion summary to `memory/handoffs/`
3. Report completion

---

*Epic Execution - Delivering complete capabilities.*
