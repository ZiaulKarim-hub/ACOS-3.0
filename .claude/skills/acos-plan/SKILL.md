---
name: acos-plan
description: Creates or updates planning documents (vision, epics, stories, slices). Use /acos-plan [level] to plan at a specific level of the hierarchy.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# ACOS Plan

## Overview

This skill creates and manages planning documents at all levels of the ACOS hierarchy: Vision > Epic > Story > Slice. Each level references its parent and produces verifiable acceptance criteria.

### Pre-flight: Auto-Bootstrap

Before proceeding, ensure ACOS is initialized in this project:

```bash
bash .claude/scripts/acos-preflight.sh
```

This is idempotent — it exits immediately if ACOS is already initialized. If not, it runs the full bootstrap (symlinks, directories, config, gitignore).

## Protocol

### Step 1: Determine Planning Level

If `$ARGUMENTS` is provided, use it as the planning level (vision, epic, story, slice).
Otherwise, ask the user what they want to plan, or detect from context.

### Step 1.5: Retrieve Prior Learnings (RAG)

Before planning, query the memory index so the plan builds on past experience instead of starting cold. This closes the learning loop — captured retrospectives, decisions, and handoffs are only valuable if they are retrieved at planning time.

```bash
bash .claude/scripts/rag-query.sh --query "<capability / feature / topic being planned>" --top-k 8
```

- Derive the query from the planning subject (the user's description, the epic capability, or the parent document's objective).
- Review `results[]` — each result has `path`, `section`, `excerpt`, `relevance`, and `category`. Prioritize `category: decision` (prior ADRs to honor or supersede), `category: learning` (retrospectives, patterns, anti-patterns), and `category: handoff` (prior gotchas).
- Fold applicable lessons into the plan: reuse prior decisions, avoid documented anti-patterns, and cite the source `path` in the plan's `technical_notes` / rationale.
- **Fallback:** if the JSON has `"fallback": true` (index or Ollama unavailable), grep `memory/` and `learning-curve/` for the topic instead. Do **not** skip this step silently.

### Step 2: Plan at the Appropriate Level

#### Vision Planning
1. Read the vision interview from `memory/source-of-truth/vision-interview.md`
2. Break the vision into major capabilities (epics)
3. Create the vision plan using template at `!cat templates/vision.yaml`
4. Save to `planning/vision/`

#### Epic Planning
1. Read the vision document for alignment
2. Use template at `!cat templates/epic.yaml`
3. Break down the epic into user stories
4. Define epic acceptance criteria
5. Save to `planning/epics/EPIC-XXX-[name].yaml`

#### Story Planning
1. Read the parent epic
2. Use template at `!cat templates/story.yaml`
3. Define user story (As a... I want... So that...)
4. Break down into atomic slices
5. Define story acceptance criteria
6. Save to `planning/stories/STORY-XXX-[name].yaml`

#### Slice Planning
1. Read the parent story
2. Use template at `!cat templates/slice.yaml`
3. Define specific acceptance criteria
4. List files allowed to modify
5. Identify required skills
6. Define verification method
7. Estimate effort (S/M/L)
8. Save to `planning/slices/SLICE-XXX-[name].yaml`

### Step 3: Confirm and Save

1. Present the plan to the user for confirmation
2. Save to the appropriate location
3. Update parent document references if needed
4. Suggest next steps

## Planning Principles

- **Epics** deliver capabilities (large, multi-session)
- **Stories** deliver user value (medium, 1-3 sessions)
- **Slices** are atomic work units (small, completable in one session)
- Each level references its parent
- Acceptance criteria must be independently verifiable
- Slices must specify `files_allowed` for scope enforcement

---

*ACOS Plan - From vision to actionable work.*
