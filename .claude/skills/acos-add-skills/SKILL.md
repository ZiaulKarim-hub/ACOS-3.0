---
name: acos-add-skills
description: Add methodology skills to the current project mid-session. Use after planning reveals the tech stack, or anytime you need additional skills.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash
---

# ACOS Add Skills

## Overview

Adds methodology skills to the current project during an active session. This is essential for **new projects** where the tech stack isn't known at bootstrap time — the vision interview or planning phase reveals what technologies will be used, and the right skills need to be linked before development begins.

Can also be used anytime the user needs a skill that wasn't auto-linked.

## Protocol

### Step 1: Discover What's Available

Find the ACOS source directory from the project config:

```bash
grep 'acos_source:' .acos/config/project.yaml | sed 's/.*acos_source: *//' | tr -d '"'
```

Then list all skills in the ACOS source that are NOT already linked in this project:

```bash
# For each skill directory in ACOS source
for skill_dir in <ACOS_SOURCE>/.claude/skills/*/; do
    name=$(basename "$skill_dir")
    # Skip if already linked
    [ -e ".claude/skills/$name" ] && continue
    # Read description
    desc=$(sed -n 's/^description: *//p' "$skill_dir/SKILL.md" 2>/dev/null | head -1)
    echo "$name: $desc"
done
```

### Step 2: Present to User

Show the user the available skills organized by category:

**Development methodology:**
- `frontend-coding` — Frontend components, UI, client-side logic
- `backend-coding` — Server-side logic, APIs, services
- `database-design` — Schema design, migrations, data access
- `api-documentation` — API docs, OpenAPI specs

**Operations & quality:**
- `deployment` — Production deployment guidance
- `ci-cd-generation` — Generate CI/CD workflows
- `quality-gates` — Automated lint/test/typecheck gates
- `domain-security-profile` — Domain-specific security profiles

**Research & documentation:**
- `technology-research` — Tech evaluation and comparison
- `user-guide-writing` — User documentation
- `mcp-setup` — MCP server configuration

**Meta (ACOS internals):**
- `agent-creation` — Create new agents
- `acos-create-skill` — Create new skills (global skill)
- `orchestration-creation` — Create new orchestration skills

Only show skills that are actually available (not already linked). If a category has no available skills, skip it.

### Step 3: Smart Suggestion (if planning exists)

If `memory/source-of-truth/vision-document.md` or planning documents exist, read them and suggest which skills are likely needed based on the planned tech stack. For example:
- Vision mentions "React" or "Vue" → suggest `frontend-coding`
- Vision mentions "PostgreSQL" or "database" → suggest `database-design`
- Vision mentions "REST API" or "GraphQL" → suggest `api-documentation`
- Vision mentions "deploy" or "production" → suggest `deployment`

Present suggestions first, then show the full list.

### Step 4: Link Selected Skills

For each skill the user wants to add:

```bash
bash .claude/scripts/add-skills.sh <skill1> <skill2> ...
```

This handles symlinking and .gitignore updates.

### Step 5: Confirm

Report what was linked. Remind the user these skills are now available as `/skill-name` commands.

---

*ACOS Add Skills — Expand your toolkit mid-session.*
