# ACOS v3.0 - Product Requirements Document

## Agentic Coding Orchestration System

**Version:** 3.0
**Date:** 2026-01-31
**Status:** Final Architecture

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Vision & Philosophy](#2-vision--philosophy)
3. [System Architecture](#3-system-architecture)
4. [The Five Pillars](#4-the-five-pillars)
5. [Agents](#5-agents)
6. [Skills](#6-skills)
7. [Agentic Flows](#7-agentic-flows)
8. [Memory System](#8-memory-system)
9. [Learning Curve System](#9-learning-curve-system)
10. [Review System](#10-review-system)
11. [Vision Interview Process](#11-vision-interview-process)
12. [User Interaction Model](#12-user-interaction-model)
13. [Folder Structure](#13-folder-structure)
14. [CLI Commands](#14-cli-commands)
15. [Safeguards & Constraints](#15-safeguards--constraints)
16. [Glossary](#16-glossary)

---

## 1. Executive Summary

ACOS v3.0 (Agentic Coding Orchestration System) is a self-evolving, perpetual coding engine that transforms user visions into production-ready software through autonomous agent collaboration.

### Core Value Proposition

**"You describe it. ACOS builds it."**

The user provides a vision in plain English. ACOS:
1. Interviews the user to fully understand requirements
2. Creates a comprehensive plan (Epics → Stories → Slices)
3. Executes the plan through specialized agents
4. Verifies all work through independent, rigorous review
5. Learns from each project to improve future performance

### What's New in v3.0

| Feature | v2.0 | v3.0 |
|---------|------|------|
| Agent Creation | Fixed set | Dynamic (Architect creates new agents) |
| Skills | Embedded in agents | Separate, granular, reusable |
| Flows | Implicit | Explicit, rated, evolvable |
| Memory | Session-based | Persistent, RAG-based, tiered |
| Learning | None | Cross-project learning curve |
| Review Control | Architect decides | Rules-based, human-controlled |
| Vision Input | One-liner accepted | Comprehensive interview required |

---

## 2. Vision & Philosophy

### Core Principles

1. **Modularity**: Agents, skills, and flows are interchangeable building blocks
2. **Adaptability**: The system creates new components when needed
3. **Quality Obsession**: Maximum rigor at every level, no shortcuts
4. **Independence**: Reviewers operate outside the Architect's influence
5. **Transparency**: Full memory, audit trails, nothing hidden
6. **Evolution**: System learns and improves over time
7. **Human Control**: User controls critical safeguards

### The Adversarial Model

ACOS operates on a trust-but-verify model:

- **The Architect** plans and orchestrates
- **Execution Agents** implement the plan
- **Review Agents** verify independently (they don't trust the Architect)
- **The Loop** continues until reviewers are satisfied

This adversarial approach catches errors before they propagate.

### Memory Philosophy

**"Nothing is lost. Nothing is summarized."**

Every interaction, decision, review, and handoff is stored in full. Agents access relevant context through RAG (Retrieval-Augmented Generation), ensuring they have the information they need without context limits.

---

## 3. System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ACOS v3.0                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        USER (Vibe Coder)                             │    │
│  │  • Provides vision via interview                                     │    │
│  │  • Edits review-rules.yaml (only human can)                          │    │
│  │  • Approves Architect evolution                                      │    │
│  │  • Intervenes when needed                                            │    │
│  └──────────────────────────────┬──────────────────────────────────────┘    │
│                                 │                                            │
│                                 ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      THE ARCHITECT (Super Agent)                     │    │
│  │                                                                      │    │
│  │  • Conducts vision interview                                         │    │
│  │  • Creates plans (Vision → Epic → Story → Slice)                     │    │
│  │  • Selects/creates agents, skills, flows                             │    │
│  │  • Responds to review feedback                                       │    │
│  │  • CANNOT influence review process                                   │    │
│  └──────────────────────────────┬──────────────────────────────────────┘    │
│                                 │                                            │
│           ┌─────────────────────┼─────────────────────┐                      │
│           │                     │                     │                      │
│           ▼                     ▼                     ▼                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   EXECUTION     │  │    SUPPORT      │  │    REVIEWERS    │              │
│  │   AGENTS        │  │    AGENTS       │  │   (Independent) │              │
│  │                 │  │                 │  │                 │              │
│  │  • Developer    │  │  • Memory Agent │  │  • QA Reviewer  │              │
│  │  • Data         │  │    (RAG-based)  │  │  • Security     │              │
│  │    Collector    │  │                 │  │  • Performance  │              │
│  │  • Analyzer     │  │  • Learning     │  │  • Integration  │              │
│  │  • Writer       │  │    Curve Agent  │  │                 │              │
│  │  • [Custom]     │  │                 │  │  Assigned by    │              │
│  │                 │  │                 │  │  RULES only     │              │
│  └────────┬────────┘  └─────────────────┘  └────────┬────────┘              │
│           │                     │                   │                        │
│           └─────────────────────┼───────────────────┘                        │
│                                 │                                            │
│                                 ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         MEMORY SYSTEM                                │    │
│  │                                                                      │    │
│  │  • Tier 1: Source of Truth (always loaded)                           │    │
│  │  • Tier 2: Role-based access                                         │    │
│  │  • Tier 3: On-demand via RAG                                         │    │
│  │  • Full history, nothing summarized                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      LEARNING CURVE (Global)                         │    │
│  │                                                                      │    │
│  │  • Cross-project knowledge                                           │    │
│  │  • Technical + Process learnings                                     │    │
│  │  • Flow effectiveness ratings                                        │    │
│  │  • Extracted at project end                                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. The Five Pillars

ACOS v3.0 is built on five foundational pillars:

### Pillar 1: Agents (Who)

Specialized workers that execute atomic tasks. Can be created dynamically by the Architect.

### Pillar 2: Skills (What)

Granular task definitions that describe objectives, requirements, and success criteria. Agents use skills as blueprints.

### Pillar 3: Flows (How)

Execution patterns that define how work moves between agents. Rated based on success/failure history.

### Pillar 4: Memory (Context)

Tiered storage system with RAG-based retrieval. Nothing is lost or summarized. Full audit trail.

### Pillar 5: Learning (Evolution)

Cross-project knowledge accumulation. System improves over time by learning from successes and failures.

---

## 5. Agents

### 5.1 Agent Categories

#### Super Agents

| Agent | Description | Special Status |
|-------|-------------|----------------|
| The Architect | Strategic brain of the system | Evolution requires HUMAN approval |

#### Execution Agents

| Agent | Description |
|-------|-------------|
| ACOS-developer | Implements code following plans |
| ACOS-data-collector | Gathers data from sources/internet |
| ACOS-data-analyzer | Processes and analyzes data |
| ACOS-report-writer | Creates reports and documentation |
| [Custom] | Created by Architect as needed |

#### Review Agents

| Agent | Description |
|-------|-------------|
| ACOS-qa-reviewer | General quality assurance (ALWAYS required) |
| ACOS-security-reviewer | Security vulnerabilities and best practices |
| ACOS-performance-reviewer | Speed, efficiency, scalability |
| ACOS-integration-reviewer | How components work together |
| [Custom] | Created by Architect as needed |

#### Support Agents

| Agent | Description |
|-------|-------------|
| ACOS-memory-agent | Neutral retrieval of relevant memory via RAG |
| ACOS-learning-curve-agent | Manages cross-project learnings |

### 5.2 Agent Creation

The Architect can create new agents when needed:

1. Architect identifies need ("I need a Security Expert Agent")
2. Architect uses agent-creation skill
3. Draft agent definition created
4. QA Reviewer reviews the agent definition
5. If approved → saved to agents/ folder
6. If rejected → Architect adjusts and resubmits

### 5.3 Agent Definition Format

```yaml
---
name: ACOS-agent-name
description: What this agent does
version: 1.0.0
created_by: architect | human
created_date: YYYY-MM-DD
reviewed_by: qa-reviewer
review_date: YYYY-MM-DD

category: execution | reviewer | support

tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - WebSearch
  - WebFetch

model: opus | sonnet | haiku

memory_access:
  tier_1: true  # Source of truth
  tier_2:       # Role-based
    - decisions/
    - handoffs/
  tier_3: true  # On-demand via Memory Agent
---

# Agent Name

## Role

[Description of the agent's role]

## Responsibilities

- [Responsibility 1]
- [Responsibility 2]

## Constraints

- [What this agent cannot do]

## Protocols

[Detailed instructions for the agent]
```

---

## 6. Skills

### 6.1 Skill Philosophy

Skills are **task definitions**, not execution instructions. They describe:
- What the task is
- What the objective is
- What success looks like
- What agents might be needed

The Architect interprets skills and decides how to execute them.

### 6.2 Skill Categories

```
skills/
├── coding/
│   ├── frontend-coding.md
│   ├── backend-coding.md
│   ├── database-design.md
│   ├── api-design.md
│   ├── testing-unit.md
│   ├── testing-integration.md
│   └── testing-e2e.md
│
├── research/
│   ├── data-collection.md
│   ├── data-analysis.md
│   ├── report-writing.md
│   └── literature-review.md
│
├── security/
│   ├── penetration-testing.md
│   ├── vulnerability-assessment.md
│   └── compliance-checking.md
│
├── documentation/
│   ├── technical-writing.md
│   ├── api-documentation.md
│   └── user-guide-creation.md
│
└── meta/
    ├── agent-creation.md
    ├── flow-creation.md
    ├── skill-creation.md
    └── vision-interview.md
```

### 6.3 Skill Definition Format

```markdown
# Skill: [Name]

## Objective

[What this skill accomplishes]

## Scope

### In Scope
- [What's included]

### Out of Scope
- [What's not included]

## Success Criteria

- [ ] [Criterion 1]
- [ ] [Criterion 2]

## Typical Agents Involved

- [Agent 1]: [Role in this skill]
- [Agent 2]: [Role in this skill]

## Quality Gates

- [Gate 1]
- [Gate 2]

## Notes for the Architect

[Guidance on how to use this skill]
```

### 6.4 Skill Creation

The Architect can create new skills:

1. Architect identifies need
2. Creates skill definition
3. Skill is saved immediately (no review required)
4. If skill proves ineffective in practice → discarded

---

## 7. Agentic Flows

### 7.1 Flow Philosophy

Flows define **execution patterns** - how work moves between agents. They are:
- Reusable across projects
- Rated based on success/failure
- Can be created by the Architect
- Discarded if ineffective

### 7.2 Base Flows

| Flow | Pattern | Best For |
|------|---------|----------|
| Linear | A → B → C → D | Sequential dependencies |
| Parallel | A,B,C simultaneously → D | Independent tasks |
| Circular | A → B → C → A (until done) | Quality-critical, iterative |
| Hierarchical | Manager → Workers → Aggregator | Complex decomposition |

### 7.3 Flow Definition Format

```yaml
---
name: flow-name
description: What this flow does
created_by: architect | human
created_date: YYYY-MM-DD
last_updated: YYYY-MM-DD

stats:
  total_uses: 0
  successes: 0
  failures: 0
  rating: UNRATED  # Shows percentage after minimum_threshold uses
  minimum_threshold: 10

best_for:
  - [Use case 1]
  - [Use case 2]

not_recommended_for:
  - [Anti-pattern 1]
---

# Flow: [Name]

## Pattern

[Visual representation]

## Stages

1. [Stage 1]: [Description]
2. [Stage 2]: [Description]

## Transitions

- [Stage 1] → [Stage 2]: [Condition]

## Termination

- Success: [Condition]
- Failure: [Condition]
```

### 7.4 Flow Rating System

- **Rating Calculation**: successes / total_uses
- **Minimum Threshold**: 10 uses before rating is shown
- **Selection**: Architect prefers higher-rated flows for similar tasks
- **Deletion**: Flows that consistently fail are discarded

---

## 8. Memory System

### 8.1 Memory Philosophy

**"Nothing is lost. Nothing is summarized."**

All interactions, decisions, reviews, and handoffs are stored in full. Agents access context through RAG-based retrieval.

### 8.2 Memory Structure

```
memory/
├── source-of-truth/                    # Tier 1: Always loaded
│   ├── vision-interview.md             # Complete Q&A transcript
│   ├── vision-document.md              # Synthesized requirements
│   └── user-commands.md                # Additional user instructions
│
├── interviews/                         # Interview history
│   ├── initial-vision-interview.md
│   └── clarification-interviews/
│
├── decisions/                          # Architectural decisions
│   ├── architectural-decisions.md
│   ├── flow-selections.md
│   └── agent-assignments.md
│
├── reviews/                            # Review audit trail
│   ├── slice-reviews/
│   ├── story-reviews/
│   ├── epic-reviews/
│   └── vision-reviews/
│
├── handoffs/                           # Agent-to-agent communication
│   ├── architect-to-developer/
│   ├── developer-to-reviewer/
│   └── reviewer-to-architect/
│
├── agent-communications/               # All inter-agent messages
│
├── code-rationale/                     # Why code decisions were made
│
└── feedback-history/                   # All feedback and resolutions
```

### 8.3 Tiered Access Model

| Tier | Access | Description |
|------|--------|-------------|
| Tier 1 | Always loaded | Source of truth - every agent always has this |
| Tier 2 | Role-based | Automatic access based on agent category |
| Tier 3 | On-demand | Retrieved via Memory Agent using RAG |

### 8.4 Role-Based Access (Tier 2)

| Agent | Automatic Access |
|-------|------------------|
| The Architect | source-of-truth/, decisions/, handoffs/, feedback-history/, learning-curve/ |
| Developer | source-of-truth/, decisions/, handoffs/, code-rationale/ |
| Reviewers | source-of-truth/, reviews/, feedback-history/ (NOT decisions/) |
| Memory Agent | ALL (for retrieval purposes) |
| Learning Curve Agent | learning-curve/, reviews/, feedback-history/ |

### 8.5 RAG Implementation

The Memory Agent uses Retrieval-Augmented Generation:

1. All memory files are chunked and embedded
2. Stored in a vector database
3. When an agent needs context, Memory Agent:
   - Receives the query
   - Searches for semantically similar chunks
   - Returns relevant content
4. Original files remain untouched

---

## 9. Learning Curve System

### 9.1 Purpose

Cross-project knowledge accumulation. The system improves over time by learning from both successes and failures.

### 9.2 Structure

```
learning-curve/
├── technical-learnings.md      # Technical patterns, libraries, approaches
├── process-learnings.md        # Workflow patterns, agent combinations
├── flow-effectiveness.md       # Which flows work for which tasks
└── user-preference-patterns.md # User interaction patterns
```

### 9.3 What Gets Learned

- **Successful outcomes**: What worked and why
- **Failures to avoid**: What didn't work and why
- **Technical learnings**: Architectural patterns, library choices
- **Process learnings**: Effective agent combinations, flow selections

### 9.4 Learning Extraction

**Trigger**: Project end (success OR failure)

**Process**:
1. Learning Curve Agent analyzes the project
2. Identifies key patterns (successes and failures)
3. Extracts learnings with full context
4. Adds to learning-curve/ files

### 9.5 Learning Entry Format

```markdown
## Learning: [Title]

**Date:** YYYY-MM-DD
**Project:** [Project name]
**Context:** [Situation where this applies]
**Type:** SUCCESS | FAILURE | PATTERN

### What Happened

[Description of the situation]

### Key Takeaway

[Actionable insight]

### Applicability

[When to apply this learning]
```

### 9.6 Conflict Resolution

When learnings conflict:
- Keep BOTH with full context
- If contexts are similar → most recent wins
- If contexts differ → both remain (context-dependent)

### 9.7 Scope

Learnings are **GLOBAL** - they apply to all future projects.

---

## 10. Review System

### 10.1 Core Principles

1. **Maximum rigor at ALL levels** - No shortcuts, ever
2. **Rules-based assignment** - Architect has ZERO control
3. **Human-editable rules only** - No agent can modify review-rules.yaml
4. **Parallel and independent** - Reviewers don't see each other's feedback
5. **All must pass** - Single failure = rejection

### 10.2 The Independence Wall

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARCHITECT'S DOMAIN                            │
│                                                                  │
│  • Vision interview                                              │
│  • Planning (epics/stories/slices)                               │
│  • Selecting execution agents                                    │
│  • Selecting flows                                               │
│  • Creating new agents/skills/flows                              │
│  • Responding to feedback                                        │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│  ════════════════ INDEPENDENCE WALL ════════════════════════════ │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│                    REVIEW SYSTEM (Architect cannot touch)        │
│                                                                  │
│  • Which reviewers are assigned (determined by RULES)            │
│  • Review depth (ALWAYS maximum)                                 │
│  • Review process (fixed protocol)                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.3 Review Rules File

Location: `ACOS 3.0/review-rules.yaml`

**Only humans can edit this file.** No agent can read, modify, or influence it.

### 10.4 Reviewer Assignment Rules

```yaml
slice_level_rules:
  - Security-sensitive code → QA + Security Reviewer
  - Database code → QA + Performance Reviewer
  - API endpoints → QA + Security + Performance Reviewer
  - Payment code → QA + Security + Performance Reviewer
  - Multi-component → QA + Integration Reviewer
  - Default → QA Reviewer (minimum)

story_level_rules:
  - Always: QA + Integration + all reviewers from slices

epic_level_rules:
  - Always: QA + Integration + Performance + all reviewers from stories

vision_level_rules:
  - Always: QA + Integration + Performance + Security (maximum scrutiny)
```

### 10.5 Review Process

1. Work is completed by execution agent
2. System reads review-rules.yaml
3. Matching rules determine which reviewers are assigned
4. All assigned reviewers work in PARALLEL
5. Reviewers work INDEPENDENTLY (can't see each other's feedback)
6. All reviewers submit verdicts
7. If ALL pass → work approved
8. If ANY fail → all feedback sent to Architect
9. Architect creates ONE coherent fix addressing ALL concerns
10. Repeat until all pass

### 10.6 Permissions Matrix

| Entity | Read Rules | Edit Rules | Influence Review | Bypass Review |
|--------|------------|------------|------------------|---------------|
| Human User | Yes | Yes | No | No |
| The Architect | No | No | No | No |
| Reviewers | No | No | No | No |
| Other Agents | No | No | No | No |

---

## 11. Vision Interview Process

### 11.1 Philosophy

ACOS does NOT accept one-line visions. Every project begins with a comprehensive interview.

### 11.2 Interview Flow

```
User: "I want to build a todo app"

ACOS: "Let me understand your vision fully..."

ACOS asks about:
• Users: Who will use this?
• Devices: Web? Mobile? Desktop?
• Features: Must-have vs nice-to-have?
• Scale: Expected users/data volume?
• Integrations: External services?
• Security: Sensitive data?
• Performance: Speed requirements?
• Design: Visual preferences?
• Tech: Preferred stack?
• Constraints: Budget/timeline?
• Success: How do we know it's done?
• ... continues until satisfied ...

User can say: "That's enough, start building"

Output:
• vision-interview.md (complete transcript)
• vision-document.md (synthesized requirements)
```

### 11.3 Interview Completion

- **Default**: Architect decides when interview is complete
- **Override**: User can say "that's enough, start building"

### 11.4 Output Documents

**vision-interview.md**: Complete Q&A transcript (nothing omitted)

**vision-document.md**: Synthesized, structured requirements document

Both become the **Source of Truth** for the entire project.

---

## 12. User Interaction Model

### 12.1 User Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Provide vision | Describe what you want to build |
| Answer interview | Respond to Architect's questions |
| Edit review rules | Customize review-rules.yaml if needed |
| Resolve escalations | Help when things fail 3+ times |
| Approve Architect evolution | Required for Architect changes |

### 12.2 User Commands

| Command | Description |
|---------|-------------|
| `acos vision` | Start a new project with interview |
| `acos status` | Check current state |
| `acos progress` | See completion percentage |
| `acos list` | List all work items |
| `acos logs` | View activity logs |
| `acos memory` | Browse memory files |
| `acos intervene` | Pause and provide guidance |
| `acos rules` | View/edit review rules |

### 12.3 Automatic Escalation

User is automatically notified when:
- Slice/Story/Epic fails review 3+ times
- Architect cannot find/create suitable agent
- Architect cannot find/create suitable flow
- Critical ambiguity in requirements
- Architect evolution is proposed

### 12.4 User Can Always

- Check progress at any time
- Intervene at any time
- Add instructions (saved to user-commands.md)
- Edit review-rules.yaml

---

## 13. Folder Structure

```
ACOS 3.0/
│
├── PRD.md                               # This document
├── review-rules.yaml                    # HUMAN-EDITABLE ONLY
│
├── agents/                              # Agent definitions
│   ├── super/
│   │   └── the-architect.md
│   ├── execution/
│   │   ├── ACOS-developer.md
│   │   ├── ACOS-data-collector.md
│   │   ├── ACOS-data-analyzer.md
│   │   └── ACOS-report-writer.md
│   ├── reviewers/
│   │   ├── ACOS-qa-reviewer.md
│   │   ├── ACOS-security-reviewer.md
│   │   ├── ACOS-performance-reviewer.md
│   │   └── ACOS-integration-reviewer.md
│   └── support/
│       ├── ACOS-memory-agent.md
│       └── ACOS-learning-curve-agent.md
│
├── skills/                              # Skill definitions
│   ├── coding/
│   │   ├── frontend-coding.md
│   │   ├── backend-coding.md
│   │   ├── database-design.md
│   │   ├── api-design.md
│   │   ├── testing-unit.md
│   │   ├── testing-integration.md
│   │   └── testing-e2e.md
│   ├── research/
│   │   ├── data-collection.md
│   │   ├── data-analysis.md
│   │   ├── report-writing.md
│   │   └── literature-review.md
│   ├── security/
│   │   ├── penetration-testing.md
│   │   ├── vulnerability-assessment.md
│   │   └── compliance-checking.md
│   ├── documentation/
│   │   ├── technical-writing.md
│   │   ├── api-documentation.md
│   │   └── user-guide-creation.md
│   └── meta/
│       ├── agent-creation.md
│       ├── flow-creation.md
│       ├── skill-creation.md
│       └── vision-interview.md
│
├── agentic-flows/                       # Flow definitions
│   ├── linear-flow.md
│   ├── parallel-flow.md
│   ├── circular-review-flow.md
│   └── hierarchical-flow.md
│
├── memory/                              # Project memory
│   ├── source-of-truth/
│   │   ├── vision-interview.md
│   │   ├── vision-document.md
│   │   └── user-commands.md
│   ├── interviews/
│   ├── decisions/
│   ├── reviews/
│   │   ├── slice-reviews/
│   │   ├── story-reviews/
│   │   ├── epic-reviews/
│   │   └── vision-reviews/
│   ├── handoffs/
│   ├── agent-communications/
│   ├── code-rationale/
│   └── feedback-history/
│
├── learning-curve/                      # Cross-project learnings
│   ├── technical-learnings.md
│   ├── process-learnings.md
│   ├── flow-effectiveness.md
│   └── user-preference-patterns.md
│
├── planning/                            # Project planning
│   ├── vision/
│   ├── epics/
│   ├── stories/
│   └── slices/
│
├── automation-scripts/                  # CLI tools
│   ├── acos                             # Main CLI
│   ├── orchestrator.sh
│   └── hooks/
│
└── .acos/                               # Runtime state
    ├── queue.yaml
    ├── current-state.yaml
    └── project-config.yaml
```

---

## 14. CLI Commands

### Project Commands

| Command | Description |
|---------|-------------|
| `acos vision` | Start new project with vision interview |
| `acos init` | Initialize ACOS in current folder |
| `acos start` | Launch Claude Code with The Architect (auto-skips permissions) |
| `acos pause` | Pause after current work completes |
| `acos resume` | Resume from paused state |
| `acos stop` | Stop immediately |

### Status Commands

| Command | Description |
|---------|-------------|
| `acos status` | Show current state |
| `acos progress` | Show completion percentage |
| `acos list` | List all work items by status |
| `acos logs` | View activity logs |

### Memory Commands

| Command | Description |
|---------|-------------|
| `acos memory` | Browse memory files |
| `acos memory search <query>` | Search memory via RAG |
| `acos truth` | View source of truth files |

### Review Commands

| Command | Description |
|---------|-------------|
| `acos rules` | View current review rules |
| `acos rules edit` | Open review-rules.yaml for editing |

### Intervention Commands

| Command | Description |
|---------|-------------|
| `acos intervene` | Pause and provide guidance |
| `acos command <instruction>` | Add instruction to user-commands.md |

### Learning Commands

| Command | Description |
|---------|-------------|
| `acos learnings` | View learning curve |
| `acos learnings extract` | Manually trigger learning extraction |

---

## 15. Safeguards & Constraints

### 15.1 Critical Safeguards

| Safeguard | Implementation |
|-----------|----------------|
| Architect evolution | Requires HUMAN approval |
| Review rules | HUMAN-EDITABLE ONLY |
| Review depth | ALWAYS maximum (no discretion) |
| Reviewer assignment | Rules-based only |
| Reviewer independence | Cannot see each other's feedback |

### 15.2 What Architect CANNOT Do

- Read review-rules.yaml
- Modify review-rules.yaml
- Influence which reviewers are assigned
- Reduce review depth
- Bypass review process
- Evolve without human approval

### 15.3 What Reviewers CANNOT Do

- See Architect's decisions/reasoning
- See other reviewers' feedback (until submitted)
- Modify review rules
- Be influenced by Architect

### 15.4 What Humans CANNOT Do

- Bypass reviews (can only edit rules)
- Approve their own work

### 15.5 System Constraints

- Maximum 3 retry attempts before escalation
- Minimum 10 uses before flow rating is shown
- All memory stored in full (no summarization)
- Source of truth always accessible to all agents

---

## 16. Glossary

| Term | Definition |
|------|------------|
| **Agent** | Specialized AI worker that executes atomic tasks |
| **Architect** | Super agent that plans and orchestrates the system |
| **Skill** | Task definition describing objectives and requirements |
| **Flow** | Execution pattern defining how work moves between agents |
| **Memory** | Persistent storage of all project context |
| **Learning Curve** | Cross-project knowledge accumulation |
| **Slice** | Atomic unit of work (hours of effort) |
| **Story** | User-facing feature (days of effort) |
| **Epic** | Major capability (weeks of effort) |
| **Vision** | User's description of what they want to build |
| **Source of Truth** | Core documents (interview + vision + commands) |
| **RAG** | Retrieval-Augmented Generation for memory access |
| **Review Rules** | Human-defined rules for reviewer assignment |
| **Independence Wall** | Separation between Architect and review system |
| **Vibe Coder** | The human user of ACOS |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 3.0 | 2026-01-31 | Initial v3.0 architecture |

---

*ACOS v3.0 - You describe it. We build it.*
