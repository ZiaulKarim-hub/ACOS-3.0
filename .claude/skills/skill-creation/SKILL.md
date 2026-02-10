---
name: skill-creation
description: Creates new native Claude Code skill definitions in .claude/skills/ format. Use when a new methodology or technique needs codification.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Skill Creation Skill

## Purpose

This meta-skill provides structured guidance for creating new native Claude Code skill definitions when existing skills don't cover the required methodology.

## When to Use

Apply this skill when:
- No existing skill covers the required technique
- A specialized approach would improve task quality
- A new domain requires documented methodology

## Key Difference from Agents

| Aspect | Agents | Skills |
|--------|--------|--------|
| What | The "who" - specialized workers | The "how" - task methodology |
| Independence | Each has own context via Task() | Applied within agent context |
| Creation | Reviewed by human | Validated through use |
| Lifecycle | Persist until deprecated | Discarded if ineffective |

## Skill Protocol

### Phase 1: Needs Analysis

1. **Identify the gap:** What methodology is needed? Why don't existing skills cover it?
2. **Define the skill's scope:** What does it teach? What are the boundaries?

### Phase 2: Skill Design

1. **Choose invocation mode:**
   - `disable-model-invocation: false` — Claude auto-invokes when relevant work detected
   - `disable-model-invocation: true` — Only invoked explicitly
   - `user-invocable: true` — Appears in `/` menu for user invocation

2. **Define tools:** Only the tools the skill actually needs
3. **Consider context:** Does it need `context: fork`? Does it need `agent: architect`?

### Phase 3: Skill Creation

Create at `.claude/skills/<name>/SKILL.md` using the native format.

### Phase 4: Validation

Skills are validated through use — track application success, gather feedback, refine or deprecate.

## Native Skill Definition Template

```markdown
---
name: [skill-name]
description: [Enhanced description for auto-discovery — be specific about what it does]
disable-model-invocation: [true | false]
user-invocable: [true | false]
allowed-tools: [Tool1, Tool2, ...]
context: fork                          # Optional: run in isolated context
agent: architect                       # Optional: which agent runs this
---

# [Skill Name]

## Purpose
[2-3 sentences describing what this skill teaches]

## When to Use
Apply this skill when:
- [Condition 1]
- [Condition 2]

## Skill Protocol
### Phase 1: [Name]
[Step-by-step instructions]

### Phase 2: [Name]
[Step-by-step instructions]

## Quality Checklist
- [ ] [Criterion 1]
- [ ] [Criterion 2]

## Common Patterns
### [Pattern Name]
[Code example or methodology]

## Output Requirements
[What should be produced]

---
*[Skill Name] - [Tagline]*
```

## Supporting Files

Skills can include supporting files in their directory:
- `templates/` — Template files the skill uses
- `examples/` — Code examples referenced via `!cat examples/file.ts`

## Quality Checklist

- [ ] Name is descriptive and follows convention
- [ ] Description is specific for auto-discovery
- [ ] allowed-tools are specified
- [ ] Protocol is step-by-step and actionable
- [ ] Examples are practical and correct
- [ ] Output requirements are clear

---

*Skill Creation Skill - Codifying expertise for reuse.*
