---
name: acos-skill-maker
description: Creates production-ready ACOS skills from completed work, conversations, or specifications. Extracts the methodology, builds the SKILL.md with full protocol, templates, and supporting files. Invoke explicitly with /acos-skill-maker.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep
---

# ACOS Skill Maker

## Purpose

Turns completed work, proven workflows, or user specifications into reusable ACOS skills.
Unlike a methodology guide, this skill **actively builds** the skill files — SKILL.md,
templates, supporting scripts — ready to invoke immediately.

## When to Use

Invoke `/acos-skill-maker` when:
- A completed exercise should be preserved as a repeatable process
- The user describes a workflow gap that needs a new skill
- A proven pattern needs to be packaged for reuse across projects
- The user points to existing code/scripts that should become a skill

## Restricted Boundaries

**NEVER read, reference, or write to these paths:**
- `review-rules/` — ACOS restricted (Independence Wall)
- `.acos/config/oracle.yaml` — Oracle configuration is human-editable only

**Read-only access (verification only, never modify):**
- `.claude/agents/` — May read to verify agent definitions exist (Phase 5), but never create or modify agent files. Agent definitions require human approval.

**Coexistence with `acos-create-skill`:** A global skill `acos-create-skill` exists at `~/.claude/skills/`. It is a lightweight methodology guide that auto-triggers. This skill (`acos-skill-maker`) is the heavy builder — explicit invocation only, creates all files. Use `acos-create-skill` for quick guidance, `/acos-skill-maker` when you need production-ready output.

If the user's specification involves these areas, explain the restriction and refuse.

## Skill Protocol

### Phase 1: Source Analysis

Determine where the skill definition comes from. Exactly one of:

**A) From completed work** (most common) — The user just finished something and wants it codified.
1. Analyze the context available in the current conversation (messages, tool calls, files created/modified)
2. If the current conversation lacks sufficient context, ask the user to describe the workflow: inputs, steps, outputs, and what made it work
3. Identify: inputs, outputs, phases/steps, quality gates, tools used, agent patterns
4. Note any parameters that should be configurable

**B) From specification** — The user describes what the skill should do.
1. Ask clarifying questions if the spec is ambiguous (max 3 questions)
2. Identify: purpose, trigger conditions, inputs, outputs, phases
3. If the user references external systems or tools, verify they exist before proceeding

**C) From existing code/scripts** — The user points to files that implement a workflow.
1. Verify the referenced files exist and are readable (halt with error if not)
2. Read the referenced files
3. Reverse-engineer the methodology from the implementation
4. Abstract into a repeatable protocol

**On failure:** If none of the above produces enough information to design a skill, tell the user what's missing and ask them to provide it. Do not proceed with incomplete information.

### Phase 2: Overlap Check

Before creating anything, verify no existing skill already covers this:

```
Glob: .claude/skills/*/SKILL.md
Glob: ~/.claude/skills/*/SKILL.md
```

Read the description of any skill with a similar name or domain. Overlap means >50% functional overlap in the protocol steps, not just similar names.

**If overlap exists**, ask the user: **extend the existing skill or create a new one?**

- **If extending:** Read the existing SKILL.md in full. Identify the gaps (missing phases, missing patterns, missing document types). Use the Edit tool to add new sections while preserving the existing protocol structure. Skip to Phase 5 after editing.
- **If creating new:** Proceed to Phase 3. The new skill MUST have a clearly distinct purpose documented in its description (explain what it does that the overlapping skill does not).

### Phase 3: Skill Design

**Step 0 — Name Validation (MANDATORY):**

Validate the skill name before anything else. The name MUST match:
```
^[a-z][a-z0-9]*(-[a-z0-9]+)*$
```
Rules: lowercase letters, digits, and hyphens only. No dots, slashes, backslashes, spaces, or underscores. 2–50 characters. Must start with a letter. No trailing hyphens, no consecutive hyphens (`--`). Each hyphen-separated segment must contain at least one character.

Prefix with `acos-` only for ACOS orchestration skills. Use kebab-case for all names.

**If the name fails validation**, reject it and suggest a corrected version.

**Step 1 — Design Parameters** (ask user only if ambiguous):

| Parameter | Options | Default |
|-----------|---------|---------|
| **Scope** | `project` (.claude/skills/) or `global` (~/.claude/skills/) | project |
| **User-invocable** | `true` (appears in `/` menu) or `false` (internal only) | true |
| **Auto-trigger** | `yes` (fires on matching context) or `no` (explicit `/name` only) | no |
| **Tools needed** | List of tools the skill requires | Minimum necessary |
| **Agent pattern** | Single agent, multi-agent swarm, or no agents | Match the source workflow |
| **Templates** | Config files, output formats, schemas | Extract from source work |
| **Arguments** | What $ARGUMENTS the skill accepts | Based on workflow inputs |

**Tool grant rules:**
- Start with the minimum: `Read, Glob, Grep` for read-only skills
- Add `Write, Edit` only if the skill creates/modifies files
- Add `Bash` only if the skill needs to run shell commands (e.g., execute scripts, install deps)
- **Sub-agent spawning is NOT a skill-frontmatter tool.** Never add `Agent` or `Task` to `allowed-tools` — the framework ignores it and it misleads readers. To let a skill spawn sub-agents, set `context: fork` and `agent: architect` so the skill inherits `Task()` from the Architect's context.
- Add `WebSearch, WebFetch` only if the skill needs external information
- **If both Bash and auto-trigger are requested**, warn the user: "This creates a high-privilege auto-triggering skill. Are you sure?" Require explicit confirmation.

### Phase 4: Build the Skill

Create all files in this order. **If any step fails, delete all files created in prior steps and report the failure to the user.**

**Step 1: Create the skill directory**

Verify the target directory does not already exist:
```
Glob: .claude/skills/{name}/SKILL.md   (or ~/.claude/skills/{name}/ for global)
```
If it exists, halt and inform the user (the overlap check in Phase 2 should have caught this, but verify).

Create the directory: `.claude/skills/{name}/` (or `~/.claude/skills/{name}/`).

**Step 2: Write SKILL.md** — The main skill definition.

Use this template structure:
```markdown
---
name: [skill-name]
description: [Clear, specific description for auto-discovery. State WHAT it does and WHEN to use it.]
disable-model-invocation: [true | false]
user-invocable: [true | false]
allowed-tools: [Tool1, Tool2, ...]
argument-hint: "[describe expected arguments]"    # Optional: shown in /help
# context: fork                                   # Optional: run in isolated context
# agent: architect                                # Optional: restrict to specific agent
---

# [Skill Name]

## Purpose
[2-3 sentences describing what this skill does]

## When to Use
Apply this skill when:
- [Condition 1]
- [Condition 2]

## Arguments
[What $ARGUMENTS accepts, with examples]

## Skill Protocol

### Phase 1: [Name]
[Numbered steps with clear actions]
[Include: what to do if this step fails]

### Phase 2: [Name]
[Numbered steps]

### Phase N: [Name]
[Numbered steps]

## Quality Checklist
- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]

## Output
[What the skill produces and where it saves output]

---
*[Skill Name] — [Tagline]*
```

**After writing SKILL.md**, immediately validate:
1. Read the file back with the Read tool
2. Verify the YAML frontmatter is parseable: `name`, `description`, `allowed-tools`, `disable-model-invocation`, and `user-invocable` must all be present
3. If any required field is missing or the YAML looks malformed (unquoted colons, missing dashes), fix it immediately with Edit

**Step 3: Create templates** (if needed) — Write files to `{skill-dir}/templates/`.
- Config schemas (YAML)
- Output format templates
- Reference documents

**Step 4: Create supporting scripts** (if needed) — Write to `{skill-dir}/scripts/`.

**IMPORTANT:** Place scripts in the skill's own directory (`{skill-dir}/scripts/`), NOT in the shared `.claude/scripts/` directory. The shared scripts directory contains ACOS infrastructure — never write there.

Script requirements:
- Self-contained (no external dependencies beyond Python/Node stdlib where possible)
- If external packages are needed (e.g., openpyxl), document the dependency in the skill's SKILL.md under a "Dependencies" section
- Make scripts executable if they're meant to be run directly

**Rollback on failure:** If Step 3 or Step 4 fails after Step 2 succeeded, inform the user: "Skill creation failed at [step]. A partial skill exists at `{skill-dir}/`. Please delete this directory manually or I can overwrite it on the next attempt. Error: [details]." Do NOT leave a broken skill without warning the user.

### Phase 5: Verification

1. **Read back** the SKILL.md file to confirm it was written correctly
2. **Verify** the frontmatter YAML is valid (all required fields present and properly formatted)
3. If the skill spawns sub-agents (`context: fork` + `agent: architect`), verify the referenced agent definitions exist in `.claude/agents/`
4. Tell the user how to invoke: `/[skill-name]` for user-invocable skills, or describe auto-trigger conditions if `disable-model-invocation: false`
5. Inform the user of the new skill count if they want to update CLAUDE.md (do not modify CLAUDE.md directly — let the user decide)

### Phase 6: Quality Gate

Before declaring the skill complete, verify it passes the quality standards:

- [ ] **Self-contained**: Someone with no context can follow the protocol and get results
- [ ] **Actionable**: Every step is a concrete action, not a vague guideline
- [ ] **Parameterized**: Configurable inputs, not hardcoded values
- [ ] **Error-aware**: Steps include what to do when things go wrong
- [ ] **Output-defined**: Clear specification of what gets produced and where
- [ ] **Least-privilege tools**: Only the tools actually needed are in allowed-tools
- [ ] **No overlap**: Confirmed no existing skill covers the same ground (Phase 2 passed)
- [ ] **Description is specific**: Auto-discovery can match it to the right situations
- [ ] **Name is valid**: Matches `^[a-z][a-z0-9-]{1,49}$`
- [ ] **Restricted files respected**: No references to `review-rules/`, `.claude/agents/`, or Oracle config

If any criterion fails, fix the issue before declaring completion.

### Phase 7: Smoke Test (Recommended for complex skills)

Ask the user if they'd like a quick test run. For complex skills (multi-agent, multi-phase), this is strongly recommended. For simple skills, it's optional.

## Common Patterns

### Single-Agent Skill
Most skills. One agent follows the protocol steps sequentially.
```yaml
allowed-tools: Read, Write, Edit, Glob, Grep
```

### Multi-Agent Swarm Skill
For parallel work (extraction, review, analysis).
```yaml
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
context: fork
agent: architect
```
**Note:** Sub-agent spawning (`Task()`) is inherited from the invoking agent's context via `context: fork` + `agent: architect`; do NOT list `Task` or `Agent` in `allowed-tools`. Requires explicit justification for the `Bash` grant.

### Review/Validation Skill
Read-only verification. No write access.
```yaml
allowed-tools: Read, Glob, Grep
```

### Research Skill
Needs web access for external information.
```yaml
allowed-tools: Read, Write, Glob, Grep, WebSearch, WebFetch
```

### Orchestration Skill
Coordinates multi-phase pipelines with agent spawning and file I/O.
```yaml
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
context: fork
agent: architect
disable-model-invocation: true
```
Orchestration capability (`Task()`) comes from `context: fork` + `agent: architect`, NOT from `allowed-tools` — matching the verified mechanism in `orchestration-creation/SKILL.md`. Orchestration skills should always be explicit-only due to their powerful tool grants.

## Output

- `{skill-dir}/SKILL.md` — The complete skill definition
- `{skill-dir}/templates/*` — Supporting templates (if applicable)
- `{skill-dir}/scripts/*` — Supporting scripts (if applicable)
- Confirmation message with invocation instructions

---
*ACOS Skill Maker — Turning proven work into reusable skills.*
