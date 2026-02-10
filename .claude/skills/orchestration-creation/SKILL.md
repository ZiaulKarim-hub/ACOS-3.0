---
name: orchestration-creation
description: Creates orchestration skills that coordinate multi-agent workflows. Replaces YAML flow definitions with executable skill definitions using context fork and Task() delegation.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Orchestration Creation Skill

## Purpose

This meta-skill provides structured guidance for creating orchestration skills — skills that coordinate multiple agents working together on complex tasks. This replaces the old YAML flow definition system with executable, native skill definitions.

## When to Use

Apply this skill when:
- A multi-agent workflow needs to be defined
- Complex coordination between agents is required
- A repeatable orchestration pattern would improve efficiency

## Understanding Orchestration Skills

Orchestration skills are regular skills that use `context: fork` and `agent: architect` to run in an isolated context with access to `Task()` for delegating work to sub-agents.

### Key Properties

| Property | Purpose |
|----------|---------|
| `context: fork` | Runs in isolated context, separate from main conversation |
| `agent: architect` | Gets the Architect's tools including Task() delegation |
| `user-invocable: true/false` | Whether users can invoke directly or only internally |

### Orchestration Patterns

#### Linear: Task A then Task B then Task C
```
Task(developer) → collect results → Task(reviewer) → aggregate
```

#### Parallel: Multiple tasks simultaneously
```
Task(qa-reviewer) + Task(security-reviewer) + Task(performance-reviewer)
→ aggregate all verdicts
```

#### Iterative: Loop until condition met
```
Task(developer) → Task(reviewers) → if REJECT → Task(developer) → repeat (max N)
```

#### Hierarchical: Coordinator delegates sub-workflows
```
For each story → invoke acos-execute-slice for each slice → aggregate
```

## Skill Protocol

### Phase 1: Workflow Analysis

1. **What needs to happen?** Map the complete workflow from start to finish
2. **What agents are involved?** List all agents and their roles
3. **What are the dependencies?** Which steps depend on others?
4. **What's the iteration/exit condition?** When does the workflow complete?

### Phase 2: Orchestration Design

1. **Choose pattern:** Linear, parallel, iterative, or hierarchical
2. **Define Task() calls:** What context to pass to each agent
3. **Define aggregation:** How to combine results from multiple agents
4. **Define error handling:** What happens on failure (retry, escalate, abort)

### Phase 3: Skill Creation

Create at `.claude/skills/<name>/SKILL.md` with:
- `context: fork` and `agent: architect` in frontmatter
- Step-by-step protocol in body that makes Task() calls
- Clear context-passing instructions for each Task()

### Phase 4: Testing

Test the orchestration end-to-end with a real or mock task.

## Orchestration Skill Template

```markdown
---
name: [orchestration-name]
description: [What this orchestration does]
disable-model-invocation: [true | false]
user-invocable: [true | false]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
context: fork
agent: architect
---

# [Orchestration Name]

## Protocol

### Step 1: [Preparation]
[Read specs, set up context]

### Step 2: [Delegation]
Use Task([agent]) to delegate work. Pass:
- [What context to include]

### Step 3: [Aggregation]
Collect results from all Task() calls.

### Step 4: [Decision]
Based on results, decide next action.

### Step 5: [Completion]
Update status, write audit logs.
```

## Quality Checklist

- [ ] All Task() calls specify what context to pass
- [ ] Error handling defined for each step
- [ ] Exit conditions are clear
- [ ] Max iterations specified for loops
- [ ] Audit logging included for traceability

---

*Orchestration Creation Skill - Coordinating agents for complex workflows.*
