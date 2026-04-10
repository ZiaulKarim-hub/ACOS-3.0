---
name: acos-start
description: Initializes an ACOS project and routes to the appropriate workflow based on current project state (new vision, existing planning, or active work).
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# ACOS Start

## Overview

This skill initializes ACOS in any directory that hasn't been set up yet, then routes to the appropriate workflow based on the current project state. Session management (new vs resume) is handled by the CLI (`acos start` for new sessions, `acos resume` for previous sessions).

## Protocol

### Step 0: Auto-Bootstrap (ALWAYS RUN FIRST)

**This step is mandatory and must execute before anything else.**

Run the ACOS bootstrap script to ensure the current project directory is initialized:

```bash
bash "$(find ~ -path "*/ACOS 3.0/.claude/scripts/acos-bootstrap.sh" -maxdepth 7 2>/dev/null | head -1)"
```

If the script path is already known (e.g., from `.acos/config/project.yaml` → `acos_source` field), use that directly:

```bash
bash "<acos_source>/.claude/scripts/acos-bootstrap.sh"
```

The bootstrap script is **idempotent** — it safely skips if ACOS is already initialized. It handles:
- Creating data directories (`.acos/`, `memory/`, `planning/`, `learning-curve/`)
- Symlinking agents, skills, and scripts from ACOS 3.0 source
- Auto-detecting project tech stack from `package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod`
- Generating `.acos/config/project.yaml` with project metadata
- Copying `review-rules/` directory (per-reviewer trigger rules, project-editable)
- Updating `.gitignore` to exclude ACOS symlinks and data directories

### Step 1: Check Project State

After bootstrap completes, check the project state:

1. Read `.acos/config/project.yaml` to understand the project
2. Check if `memory/source-of-truth/vision-document.md` exists (has a vision?)
3. Check if `planning/slices/` has any files (has planning?)
4. Check if `.acos/config/active-slice.yaml` exists (work in progress?)

### Step 1.5: Model Profile Selection (Optional)

If `.acos/state/model-session.yaml` does NOT already exist (no profile set this session):

1. Read the default profile from `.acos/config/model-profile.yaml` (key: `default_profile`)
2. Present the user with a model profile choice using AskUserQuestion:
   - **Budget** — Haiku for implementation, Sonnet for critical review. Lowest cost.
   - **Standard** — Sonnet across the board. Good balance of cost and quality.
   - **Premium** — Opus everywhere. Maximum quality. (Current default)
   - **Auto** — Opus for critical decisions, Sonnet for implementation, Haiku for support.
   - **Keep default** — Use whatever is configured in `model-profile.yaml` (show which profile)
3. If the user selects a profile, write to `.acos/state/model-session.yaml`:
   ```yaml
   active_profile: [selected]
   changed_at: "[timestamp]"
   changed_by: "acos-start"
   ```
4. If the selected profile's `main` model differs from the current conversation model, advise:
   > "This profile recommends **[model]** for the main conversation. Run `/model` and select **[model]** to match."

If `.acos/state/model-session.yaml` already exists, skip this step (profile already set for this session).

### Step 2: Route Based on State

**If no vision exists:**
- Welcome the user to ACOS
- Display detected project info from `project.yaml` (name, tech stack, toolchain)
- Explain the system briefly:
  > "ACOS v3.0 has been initialized in this project. I'll orchestrate planning, development, and review through specialized agents with mechanically-enforced quality gates."
- Ask if the user wants to:
  - Conduct a full vision interview (`/acos-interview`)
  - Jump to a specific task (`/acos-plan` with a quick description)
  - Run a targeted review (`/acos-review`)

**If vision exists but no planning:**
- Read the vision document
- Suggest starting with `/acos-plan` to create epics, stories, and slices

**If vision and planning exist:**
- Display current project status:
  - Total slices / completed / in-progress / pending
  - Current active slice (if any)
  - Recent reviews and their verdicts
- Suggest the next action based on state:
  - If slices are ready: suggest `/acos-execute-slice [SLICE-ID]`
  - If reviews are pending: suggest `/acos-review`
  - If all work is complete: suggest `/acos-learn` for retrospective

---

*ACOS Start — Auto-initializes and routes to the right workflow.*
