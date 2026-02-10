---
name: acos-decide
description: Creates an Architecture Decision Record (ADR). Documents decision context, options considered, choice made, and rationale.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep
---

# ACOS Decide

## Overview

This skill creates Architecture Decision Records (ADRs) to document significant decisions. Every important architectural, design, or technology choice should be recorded for future reference and learning extraction.

### Pre-flight: Auto-Bootstrap

Before proceeding, ensure ACOS is initialized in this project:

```bash
bash .claude/scripts/acos-preflight.sh
```

This is idempotent — it exits immediately if ACOS is already initialized. If not, it runs the full bootstrap (symlinks, directories, config, gitignore).

## Protocol

### Step 1: Gather Decision Context

Ask the user (or extract from context):
- What decision needs to be recorded?
- What prompted this decision?
- What alternatives were considered?
- What was chosen and why?

### Step 2: Determine ADR Number

Check existing ADRs in `memory/decisions/` to determine the next number.

### Step 3: Create the ADR

Use the template at `!cat templates/adr.md` and fill in:
- Title
- Status (proposed, accepted, deprecated, superseded)
- Context (why this decision is needed)
- Decision (what was decided)
- Alternatives considered (with pros/cons for each)
- Consequences (positive and negative)
- Related decisions

### Step 4: Save

Write to `memory/decisions/ADR-[NNN]-[title-slug].md`
Confirm save to user.

---

*ACOS Decide - Decisions documented are decisions defensible.*
