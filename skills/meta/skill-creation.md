---
name: skill-creation
description: Meta-skill for creating new skill definitions
version: 1.0.0
created_by: human
created_date: 2026-01-31

category: meta

applicable_to:
  - the-architect

tools_required:
  - Read
  - Write
  - Edit

requires_review: false
validation: through_use
---

# Skill Creation Skill

## Purpose

This meta-skill provides structured guidance for The Architect to create new skill definitions when existing skills don't cover the required task.

## When to Use

Apply this skill when:
- No existing skill covers the required technique
- A specialized approach would improve task quality
- A new domain requires documented methodology

## Key Difference from Agents

| Aspect | Agents | Skills |
|--------|--------|--------|
| What | The "who" - specialized workers | The "what" - task definitions |
| Independence | Each has own session/context | Applied within agent context |
| Creation | Reviewed by QA | Validated through use |
| Lifecycle | Persist until deprecated | Discarded if ineffective |

## Skill Protocol

### Phase 1: Needs Analysis

1. **Identify the gap:**
   - What methodology is needed?
   - Why don't existing skills cover it?
   - What makes this approach unique?

2. **Define the skill's scope:**
   - What does this skill teach?
   - What are the boundaries?
   - Who should use it?

### Phase 2: Skill Design

1. **Determine category:**
   - `coding` - Implementation techniques
   - `research` - Investigation methods
   - `security` - Security practices
   - `documentation` - Documentation standards
   - `meta` - System-level skills

2. **Define applicability:**
   - Which agents can use it?
   - What tools are required?
   - What frameworks/technologies?

### Phase 3: Skill Creation

1. Create skill definition file
2. Follow the template structure
3. Include practical examples

### Phase 4: Validation

Skills are validated through use:
- Track application success
- Gather feedback from agents
- Refine or deprecate as needed

## Skill Definition Template

```yaml
---
name: [skill-name]
description: [One-line description]
version: 1.0.0
created_by: architect
created_date: [YYYY-MM-DD]

category: [coding | research | security | documentation | meta]

applicable_to:
  - [agent-name-1]
  - [agent-name-2]
  - any-execution-agent  # or any-agent

tools_required:
  - [Tool1]
  - [Tool2]

# Optional: frameworks/technologies this skill covers
frameworks_supported:
  - [Framework1]
  - [Framework2]
---

# [Skill Name]

## Purpose

[2-3 sentences describing what this skill teaches and why it's valuable]

## When to Use

Apply this skill when:
- [Condition 1]
- [Condition 2]
- [Condition 3]

## Skill Protocol

### Phase 1: [First Phase Name]

[Step-by-step instructions]

### Phase 2: [Second Phase Name]

[Step-by-step instructions]

### Phase 3: [Third Phase Name]

[Step-by-step instructions]

## Quality Checklist

- [ ] [Quality criterion 1]
- [ ] [Quality criterion 2]
- [ ] [Quality criterion 3]

## Common Patterns

### [Pattern Name]

```[language]
[Code example]
```

## Output Requirements

[What should be produced when applying this skill]

---

*[Skill Name] - [Tagline]*
```

## Skill Categories

### Coding Skills

Purpose: Guide implementation techniques

Examples:
- frontend-coding
- backend-coding
- database-design
- testing

### Research Skills

Purpose: Guide investigation methods

Examples:
- codebase-analysis
- technology-research
- bug-investigation

### Security Skills

Purpose: Guide security practices

Examples:
- security-audit
- vulnerability-assessment
- secure-coding

### Documentation Skills

Purpose: Guide documentation creation

Examples:
- api-documentation
- code-documentation
- user-guides

### Meta Skills

Purpose: Guide system-level operations

Examples:
- agent-creation (this requires review)
- skill-creation (this skill)
- flow-creation

## Quality Checklist

Before saving a new skill:

- [ ] Name is descriptive and follows convention
- [ ] Description is clear and specific
- [ ] Category is appropriate
- [ ] Applicable agents are listed
- [ ] Tools required are specified
- [ ] Protocol is step-by-step and actionable
- [ ] Examples are practical and correct
- [ ] Output requirements are clear

## Skill Validation Criteria

A skill is considered effective if:

1. **Adoption:** Agents successfully apply it
2. **Quality:** Outputs meet quality standards
3. **Efficiency:** Improves task completion
4. **Consistency:** Produces consistent results

A skill should be deprecated if:

1. No agents use it
2. Outputs consistently fail review
3. Better alternatives exist
4. Technology becomes obsolete

## Constraints for The Architect

When creating skills:

### You CANNOT:

- Create skills that bypass review processes
- Create skills with inaccurate information
- Create duplicate skills

### You MUST:

- Base skills on proven methodologies
- Include practical examples
- Test examples for accuracy
- Track skill effectiveness

---

*Skill Creation Skill - Codifying expertise for reuse.*
