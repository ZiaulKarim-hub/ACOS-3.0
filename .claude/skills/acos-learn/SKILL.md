---
name: acos-learn
description: Extracts learnings from completed work. Delegates memory collection to memory-agent, delegates analysis to learning-agent. Creates retrospectives and updates the learning curve.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
context: fork
agent: architect
---

# Learning Extraction

## Overview

This skill extracts learnings from completed work. It delegates memory collection to the memory-agent and analysis to the learning-agent, producing retrospective documents and updating the learning curve knowledge base.

### Pre-flight: Auto-Bootstrap

Before proceeding, ensure ACOS is initialized in this project:

```bash
bash .claude/scripts/acos-preflight.sh
```

This is idempotent — it exits immediately if ACOS is already initialized. If not, it runs the full bootstrap (symlinks, directories, config, gitignore).

## Protocol

### Step 1: Gather Project Context

Read the current project state:
- Vision document from `memory/source-of-truth/`
- All decisions from `memory/decisions/`
- All reviews from `memory/reviews/`
- Evidence bundles from `.acos/evidence/`
- Agent metrics from `.acos/metrics/`

### Step 2: Delegate Memory Collection

**Model Resolution & Dispatch:** Before spawning subagents, resolve their models:
```bash
MEMORY_MODEL=$(bash .claude/scripts/resolve-agent-model.sh memory-agent)
LEARNING_MODEL=$(bash .claude/scripts/resolve-agent-model.sh learning-agent)
```

**Dispatch rule:** If the resolved model is a bare Claude name (no `:`) → use `Task()`. If it contains `:` (e.g., `openai:gpt-4o`) → use `Bash` with `run-external-agent.py`. For external models, pre-read relevant files and pass them via `--context`.

Use memory-agent (via appropriate dispatch path) to:
- Collect all project memory artifacts
- Organize by category (decisions, reviews, feedback)
- Identify key events and turning points
- Return structured summary of project history

### Step 3: Delegate Learning Analysis

Use learning-agent (via appropriate dispatch path) with the memory summary to:
- Analyze decisions: which worked, which failed, why
- Analyze review patterns: common issues, effective solutions
- Analyze workflow: what was efficient, what was slow
- Extract patterns and anti-patterns
- Create learning entries using the learning entry format
- Create project retrospective

### Step 4: Store Learnings

Using the learning-agent's output:
1. Save new patterns to `learning-curve/patterns/`
2. Save anti-patterns to `learning-curve/anti-patterns/`
3. Save retrospective to `learning-curve/project-retrospectives/`
4. Update `learning-curve/index.yaml`

Use templates from:
- `!cat templates/pattern.md`
- `!cat templates/anti-pattern.md`
- `!cat templates/retrospective.md`

### Step 5: Report

Present a summary of extracted learnings:
- Number of patterns identified
- Number of anti-patterns identified
- Key insights
- Recommendations for future projects

---

*Learning Extraction - Every project makes us smarter.*
