---
name: acos-execute-story
description: Completes a story by executing all its slices in dependency order, then performing story-level integration review. Use with $ARGUMENTS for the story ID.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
context: fork
agent: architect
---

# Story Execution

## Overview

This skill completes a full story by executing all its constituent slices in dependency order, then triggering a story-level integration review to verify that all slices work together correctly.

### Pre-flight: Auto-Bootstrap

Before proceeding, ensure ACOS is initialized in this project:

```bash
bash .claude/scripts/acos-preflight.sh
```

This is idempotent — it exits immediately if ACOS is already initialized. If not, it runs the full bootstrap (symlinks, directories, config, gitignore).

## Protocol

### Step 1: Read Story Specification

Read the story spec from `planning/stories/$ARGUMENTS.yaml`. Extract:
- Story objective and acceptance criteria
- List of slices with dependency order
- Story-level integration requirements

### Step 2: Build Slice Dependency Graph

Analyze slice dependencies to determine execution order. Slices without dependencies can potentially be executed first; dependent slices must wait.

### Step 3: Execute Slices in Order

For each slice in dependency order:
1. Invoke the `acos-execute-slice` skill with the slice ID
2. Wait for completion
3. Verify the slice passed review
4. If a slice fails and cannot be resolved, pause and escalate

### Step 4: Story-Level Integration Verification

**Model Resolution & Dispatch:** Before spawning any subagent, resolve its model:
```bash
RESOLVED=$(bash .claude/scripts/resolve-agent-model.sh <agent-name>)
```

**Dispatch rule:** If the resolved model is a bare Claude name (no `:`) → use `Task()`. If it contains `:` (e.g., `openai:gpt-4o`) → use `Bash` with `run-external-agent.py` (see acos-review skill for full dispatch pattern). For external models, pre-read relevant code files and pass them via `--context`. Developer always resolves to Claude (safety gate enforced).

After all slices are complete, delegate integration verification:
1. Use developer (always Claude via Task) to run integration tests across all slice boundaries
2. Use qa-reviewer via the dispatch rule above to verify story-level acceptance criteria
3. Use integration-reviewer via the dispatch rule above to verify cross-slice coherence

### Step 5: Aggregate Story Verdicts

- If ALL reviewers PASS: mark story complete
- If ANY REJECT: consolidate feedback and invoke `acos-feedback-resolution`

### Step 6: Completion

1. Update story status in `planning/stories/$ARGUMENTS.yaml` to `status: completed`
2. Write story completion summary to `memory/handoffs/`
3. Report completion to user

---

*Story Execution - User value delivered through coordinated slices.*
