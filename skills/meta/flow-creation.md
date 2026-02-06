---
name: flow-creation
description: Meta-skill for creating new agentic flow definitions
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
rating_system: true
---

# Flow Creation Skill

## Purpose

This meta-skill provides structured guidance for The Architect to create new agentic flow definitions that orchestrate agent collaboration patterns.

## When to Use

Apply this skill when:
- No existing flow matches the required workflow pattern
- A new collaboration pattern would improve efficiency
- Complex multi-agent coordination is needed

## Understanding Flows

Flows define the "how" of agent collaboration:

| Aspect | Description |
|--------|-------------|
| Purpose | Orchestrate multiple agents working together |
| Types | Linear, Parallel, Circular, Hierarchical |
| Validation | Through use, with rating system |
| Evolution | Improved based on success/failure patterns |

## Flow Types

### Linear Flow

```
Agent A → Agent B → Agent C → Output
```

Use when: Tasks must complete in sequence

### Parallel Flow

```
        ┌→ Agent B ─┐
Agent A ─┼→ Agent C ─┼→ Agent E
        └→ Agent D ─┘
```

Use when: Independent tasks can run simultaneously

### Circular Flow

```
Agent A → Agent B → Agent C ─┐
   ↑                         │
   └─────────────────────────┘
```

Use when: Iterative refinement is needed

### Hierarchical Flow

```
        Agent A (Coordinator)
           ├────────┤
        ┌──┘        └──┐
     Agent B        Agent C
     ├──┬──┐        ├──┬──┐
     D  E  F        G  H  I
```

Use when: Work needs delegation and aggregation

## Skill Protocol

### Phase 1: Flow Analysis

1. **Identify the workflow:**
   - What needs to happen?
   - What agents are involved?
   - What are the dependencies?

2. **Determine flow type:**
   - Must things happen in order? (Linear)
   - Can things happen simultaneously? (Parallel)
   - Is iteration needed? (Circular)
   - Is there a hierarchy? (Hierarchical)

### Phase 2: Flow Design

1. **Map the stages:**
   - Entry point
   - Each processing stage
   - Exit conditions
   - Error handling

2. **Define handoffs:**
   - What data passes between stages?
   - What format is used?
   - What are the success criteria?

### Phase 3: Flow Creation

1. Create flow definition file
2. Follow the template structure
3. Include clear diagrams

### Phase 4: Validation

Flows are rated through use:
- Initial rating: UNRATED
- After 5+ uses: Calculate success rate
- Rating updated based on outcomes

## Flow Definition Template

```yaml
---
name: [flow-name]
description: [One-line description]
version: 1.0.0
created_by: architect
created_date: [YYYY-MM-DD]

type: [linear | parallel | circular | hierarchical]
rating: UNRATED  # Will be updated through use

stages:
  - name: [stage-1-name]
    agent: [agent-name]
    input: [what this stage receives]
    output: [what this stage produces]
    success_criteria:
      - [criterion 1]
      - [criterion 2]
    on_failure: [retry | escalate | abort]
    max_retries: 3

  - name: [stage-2-name]
    depends_on: [stage-1-name]
    agent: [agent-name]
    # ... same structure

# For parallel flows
parallel_stages:
  - group: 1
    stages: [stage-a, stage-b, stage-c]
    join_at: [stage-d]
    join_strategy: [all | any | majority]

# For circular flows
iteration:
  max_iterations: 5
  exit_condition: [condition for stopping]
  improvement_threshold: [metric threshold]

# For hierarchical flows
hierarchy:
  coordinator: [agent-name]
  delegation_strategy: [how work is divided]
  aggregation_strategy: [how results are combined]

error_handling:
  default: [retry | escalate | abort]
  on_max_retries: escalate_to_human
  notification: [who to notify]

metadata:
  typical_duration: [estimate]
  complexity: [low | medium | high]
  use_cases:
    - [use case 1]
    - [use case 2]
---

# [Flow Name]

## Overview

[2-3 sentences describing what this flow accomplishes and when to use it]

## Flow Diagram

```
[ASCII diagram of the flow]
```

## Stages

### Stage 1: [Name]

**Agent:** [agent-name]
**Purpose:** [What this stage does]

**Input:**
- [Input 1]
- [Input 2]

**Output:**
- [Output 1]
- [Output 2]

**Success Criteria:**
- [ ] [Criterion 1]
- [ ] [Criterion 2]

### Stage 2: [Name]

[Same structure as above]

## Handoff Specifications

### [Stage 1] → [Stage 2]

```yaml
handoff:
  from: [stage-1]
  to: [stage-2]
  data:
    - field: [field-name]
      type: [type]
      description: [what it contains]
```

## Error Handling

| Error Type | Response | Recovery |
|------------|----------|----------|
| [Error 1] | [Action] | [How to recover] |
| [Error 2] | [Action] | [How to recover] |

## Success Metrics

- **Completion Rate:** [target %]
- **Average Iterations:** [for circular]
- **Quality Score:** [how measured]

---

*[Flow Name] - [Tagline]*
```

## Flow Rating System

| Rating | Criteria |
|--------|----------|
| UNRATED | Fewer than 5 uses |
| EXCELLENT | >90% success rate |
| GOOD | 70-90% success rate |
| FAIR | 50-70% success rate |
| POOR | <50% success rate |
| DEPRECATED | Consistently failing, replaced |

## Quality Checklist

Before saving a new flow:

- [ ] Name is descriptive and follows convention
- [ ] Type is appropriate for the workflow
- [ ] All stages are defined
- [ ] Dependencies are clear
- [ ] Success criteria are measurable
- [ ] Error handling is specified
- [ ] Diagram is clear and accurate
- [ ] Handoffs are well-specified

## Constraints for The Architect

When creating flows:

### You CANNOT:

- Create flows that bypass review stages
- Create flows with undefined error handling
- Create flows that skip required handoffs

### You MUST:

- Include proper error handling
- Define clear success criteria
- Specify all handoffs
- Start with UNRATED status
- Track flow performance

---

*Flow Creation Skill - Orchestrating agents for complex tasks.*
