---
name: agent-creation
description: Creates new native Claude Code agent definitions in .claude/agents/ format. Use when the Architect needs a specialized agent. Requires human approval.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Agent Creation Skill

## Purpose

This meta-skill provides structured guidance for creating new native Claude Code agent definitions when existing agents don't meet task requirements.

## When to Use

Apply this skill when:
- No existing agent can perform the required task
- A specialized agent would improve task execution
- A new domain requires dedicated expertise

## Skill Protocol

### Phase 1: Needs Analysis

1. **Identify the gap:** What task? Why can't existing agents do it? What specialized knowledge?
2. **Define the agent's role:** What will it do? What will it NOT do? How does it fit with other agents?

### Phase 2: Agent Design

1. **Determine category:**
   - `execution` — Does the work (gets Write/Edit tools)
   - `reviewer` — Reviews work (read-only, `disallowedTools: Write, Edit, Task`, `permissionMode: plan`)
   - `support` — Provides services to other agents

2. **Define capabilities:**
   - Required tools (minimal but sufficient)
   - Model (opus for complex reasoning, sonnet for simpler tasks)
   - Permission mode
   - Max turns
   - Memory scope (project or user)

3. **Define constraints:**
   - disallowedTools for safety boundaries
   - What the agent CANNOT do
   - What the agent MUST do
   - Independence requirements (for reviewers)

### Phase 3: Agent Creation

Create the agent definition at `.claude/agents/<name>.md` using the native format.

### Phase 4: Review

Agent creation requires human approval before the agent is used.

## Native Agent Definition Template

```markdown
---
name: [agent-name]
description: [One-line description for auto-discovery]
tools: [Tool1, Tool2, ...]
disallowedTools: [Tool1, Tool2, ...]  # Optional
model: [opus | sonnet | haiku]
permissionMode: [default | acceptEdits | plan]
maxTurns: [number]
skills:                                # Optional
  - [skill-name]
memory: [project | user]              # Optional
hooks:                                 # Optional
  PreToolUse:
    - matcher: "[pattern]"
      hooks:
        - type: command
          command: "[script path]"
---

# [Agent Name]

## Role
[2-3 sentences describing role and purpose]

## Core Responsibilities
### 1. [Responsibility]
[Details]

## Critical Constraints
### You CANNOT:
- [Constraint]

### You MUST:
- [Requirement]

## Return Value
[What the agent returns via Task()]

---
*[Agent Name] - [Tagline]*
```

## Agent Categories

### Execution Agents
- Have Write/Edit tools
- Create evidence bundles
- `permissionMode: acceptEdits`
- Preloaded with relevant coding skills

### Reviewer Agents
- **MUST have:** `disallowedTools: Write, Edit, Task` and `permissionMode: plan`
- These settings mechanically enforce independence (read-only, no communication)
- Cannot see Architect decisions (enforced by isolated Task() context)

### Support Agents
- Service-oriented (memory, learning)
- `disallowedTools: Task` (cannot spawn sub-agents)
- May have `memory: project` or `memory: user`

## Quality Checklist

- [ ] Name follows convention
- [ ] Description is clear for auto-discovery
- [ ] Tools are minimal but sufficient
- [ ] disallowedTools enforces boundaries
- [ ] permissionMode is appropriate
- [ ] Constraints are clear
- [ ] Return value format is specified
- [ ] Reviewer agents have mechanical independence enforcement

---

*Agent Creation Skill - Expanding ACOS capabilities thoughtfully.*
