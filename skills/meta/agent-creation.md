---
name: agent-creation
description: Meta-skill for creating new agent definitions
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

requires_review: true
reviewer: ACOS-qa-reviewer
---

# Agent Creation Skill

## Purpose

This meta-skill provides structured guidance for The Architect to create new agent definitions when existing agents don't meet task requirements.

## When to Use

Apply this skill when:
- No existing agent can perform the required task
- A specialized agent would improve task execution
- A new domain requires dedicated expertise

## Skill Protocol

### Phase 1: Needs Analysis

1. **Identify the gap:**
   - What task needs to be done?
   - Why can't existing agents do it?
   - What specialized knowledge is needed?

2. **Define the agent's role:**
   - What will this agent do?
   - What will it NOT do?
   - How does it fit with other agents?

### Phase 2: Agent Design

1. **Determine category:**
   - `execution` - Does the work
   - `reviewer` - Reviews work (special constraints)
   - `support` - Provides services to other agents

2. **Define capabilities:**
   - Required tools
   - Memory access needs
   - Special permissions

3. **Define constraints:**
   - What the agent CANNOT do
   - What the agent MUST do
   - Independence requirements (for reviewers)

### Phase 3: Agent Creation

1. Create agent definition file
2. Follow the template structure
3. Be specific and comprehensive

### Phase 4: Review

1. Submit to QA Reviewer
2. Address feedback
3. Finalize agent

## Agent Definition Template

```yaml
---
name: [agent-name]
description: [One-line description]
version: 1.0.0
created_by: architect
created_date: [YYYY-MM-DD]

category: [execution | reviewer | support]

tools:
  - [Tool1]
  - [Tool2]

model: [opus | sonnet | haiku]

memory_access:
  tier_1: true
  tier_2:
    - [directory1/]
    - [directory2/]
  tier_3: true

# For reviewers only:
independence:
  cannot_see_architect_decisions: true
  cannot_see_other_reviewer_feedback: true
  cannot_be_influenced_by_architect: true

# For special agents:
special_status:
  [special_permission]: [true/false]
---

# [Agent Name]

## Role

[2-3 sentences describing the agent's role and purpose]

## Core Responsibilities

### 1. [Responsibility 1]

[Description and details]

### 2. [Responsibility 2]

[Description and details]

## Critical Constraints

### You CANNOT:

- [Constraint 1]
- [Constraint 2]

### You MUST:

- [Requirement 1]
- [Requirement 2]

## Protocol

[Step-by-step protocol for how the agent operates]

## Output Format

[What the agent produces and in what format]

---

*[Agent Name] - [Tagline]*
```

## Agent Categories

### Execution Agents

Purpose: Perform actual work tasks

Examples:
- ACOS-developer (writes code)
- ACOS-data-analyst (analyzes data)
- ACOS-test-writer (writes tests)

Characteristics:
- Have write access to code
- Create evidence bundles
- Follow assigned plans

### Reviewer Agents

Purpose: Independently verify work quality

Examples:
- ACOS-qa-reviewer
- ACOS-security-reviewer
- ACOS-performance-reviewer

Characteristics:
- **MUST have independence block**
- Cannot see Architect decisions
- Cannot see other reviewers' feedback
- Maximum rigor always

### Support Agents

Purpose: Provide services to other agents

Examples:
- ACOS-memory-agent
- ACOS-learning-curve-agent

Characteristics:
- Service-oriented
- React to requests
- Maintain system infrastructure

## Quality Checklist

Before submitting for review:

- [ ] Name follows convention (ACOS-[function])
- [ ] Description is clear and specific
- [ ] Category is appropriate
- [ ] Tools are minimal but sufficient
- [ ] Memory access is properly scoped
- [ ] Constraints are clear
- [ ] Responsibilities are well-defined
- [ ] Protocol is actionable
- [ ] Output format is specified

## Constraints for The Architect

When creating agents:

### You CANNOT:

- Create agents that bypass review
- Create agents that modify review-rules.yaml
- Create reviewers without independence constraints
- Create agents with unnecessary permissions

### You MUST:

- Submit new agents for QA review
- Document why the agent is needed
- Follow the template exactly
- Scope permissions minimally

---

*Agent Creation Skill - Expanding ACOS capabilities thoughtfully.*
