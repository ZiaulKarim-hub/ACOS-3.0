---
name: acos-status
description: Displays current ACOS project status including vision, planning progress, active work, memory stats, and evidence status.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash
---

# ACOS Status

## Overview

This skill displays a comprehensive dashboard of the current ACOS project state.

### Pre-flight: Auto-Bootstrap

Before proceeding, ensure ACOS is initialized in this project:

```bash
bash .claude/scripts/acos-preflight.sh
```

This is idempotent — it exits immediately if ACOS is already initialized. If not, it runs the full bootstrap (symlinks, directories, config, gitignore).

## Protocol

### Step 1: Check Initialization

Verify `.acos/` and `memory/` directories exist. If not, inform user to run `/acos-start`.

### Step 2: Gather Status Information

Collect data from all project directories:

**Vision Status:**
- Read `memory/source-of-truth/vision-document.md` for title and summary

**Planning Status:**
- Count epics in `planning/epics/` (exclude .template files)
- Count stories in `planning/stories/` (exclude .template files)
- Count slices in `planning/slices/` (exclude .template files)
- Read each to check status field (pending, in_progress, completed)

**Current Work:**
- Check `.acos/config/active-slice.yaml` for active slice
- Find recent handoffs in `memory/handoffs/`

**Memory Status:**
- Count decisions in `memory/decisions/`
- Count reviews in `memory/reviews/` subdirectories
- Count handoff records

**Evidence Status:**
- Check `.acos/evidence/` for evidence bundles

**Model Profile:**
- Check `.acos/state/model-session.yaml` for active session profile
- If no session state, check `.acos/config/model-profile.yaml` for default profile
- Resolve models for all 8 agents using `bash .claude/scripts/resolve-agent-model.sh <agent-name>`

**Agent Metrics:**
- Check `.acos/metrics/agent-completions.log` for recent agent activity

### Step 3: Display Dashboard

```
ACOS Project Status
═══════════════════════════════════════

Vision: [Vision title]
Status: [In Progress | Complete]

Planning:
  Epics:   [X] total, [Y] complete, [Z] in progress
  Stories: [X] total, [Y] complete, [Z] in progress
  Slices:  [X] total, [Y] complete, [Z] in progress

Current Work:
  Active Slice: [SLICE-XXX] - [Title] (or "None")
  Last Activity: [Date]

Memory:
  Decisions: [X] recorded
  Reviews:   [Y] completed
  Handoffs:  [Z] documented

Model Profile:
  Active: [premium/standard/budget/auto] ([session override / project default])
  Main:   [opus/sonnet/haiku] (advisory)
  Agents: architect→[model] developer→[model] qa→[model] sec→[model]
          perf→[model] integ→[model] memory→[model] learn→[model]

Evidence:
  Bundles: [N] total

Next Steps:
  - [Recommendation based on current state]
```

---

*ACOS Status - Know where you stand.*
