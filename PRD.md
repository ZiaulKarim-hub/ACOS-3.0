# ACOS v3.0 - Product Requirements Document

## Agentic Coding Orchestration System

**Version:** 3.0 (Native Claude Code Edition)
**Date:** 2026-02-07
**Status:** Final Architecture - Fully Migrated

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Vision & Philosophy](#2-vision--philosophy)
3. [System Architecture](#3-system-architecture)
4. [The Five Pillars](#4-the-five-pillars)
5. [Agents](#5-agents)
6. [Skills](#6-skills)
7. [Orchestration Skills](#7-orchestration-skills)
8. [Memory System](#8-memory-system)
9. [Learning Curve System](#9-learning-curve-system)
10. [Review System](#10-review-system)
11. [Vision Interview Process](#11-vision-interview-process)
12. [User Interaction Model](#12-user-interaction-model)
13. [Mechanical Enforcement](#13-mechanical-enforcement)
14. [Folder Structure](#14-folder-structure)
15. [Safeguards & Constraints](#15-safeguards--constraints)
16. [Glossary](#16-glossary)

---

## 1. Executive Summary

ACOS v3.0 (Agentic Coding Orchestration System) is a multi-agent orchestration system for software development built entirely on **native Claude Code primitives** — agents, skills, hooks, and scripts. It transforms user visions into production-ready software through autonomous agent collaboration with mechanically enforced quality gates.

### Core Value Proposition

**"You describe it. ACOS builds it."**

The user provides a vision in plain English. ACOS:
1. Interviews the user to fully understand requirements
2. Creates a comprehensive plan (Epics > Stories > Slices)
3. Executes the plan through specialized agents
4. Verifies all work through independent, rigorous review
5. Learns from each project to improve future performance

### Native Claude Code Implementation

ACOS v3.0 uses zero custom infrastructure. Everything is built on native Claude Code features:

| Concept | Implementation |
|---------|----------------|
| Agents | `.claude/agents/*.md` with YAML frontmatter |
| Skills | `.claude/skills/*/SKILL.md` with auto-discovery |
| Orchestration | Skills with `context: fork` + `agent: architect` |
| Enforcement | PreToolUse/PostToolUse/SubagentStop hooks in `.claude/settings.local.json` |
| Scope control | Shell scripts in `.claude/scripts/` |
| Project context | `CLAUDE.md` at project root (auto-loads) |
| Memory | Native `memory: project` and `memory: user` fields |

---

## 2. Vision & Philosophy

### Core Principles

1. **Modularity**: Agents, skills, and orchestration skills are interchangeable building blocks
2. **Adaptability**: The system creates new components when needed
3. **Quality Obsession**: Maximum rigor at every level, no shortcuts
4. **Independence**: Reviewers operate outside the Architect's influence
5. **Transparency**: Full memory, audit trails, nothing hidden
6. **Evolution**: System learns and improves over time
7. **Human Control**: User controls critical safeguards
8. **Mechanical Enforcement**: Trust boundaries are enforced by tool restrictions and hooks, not by instructions alone

### The Adversarial Model

ACOS operates on a trust-but-verify model:

- **The Architect** plans and orchestrates (via `Task()`)
- **The Developer** implements the plan (scoped by `check-scope.sh`)
- **Reviewers** verify independently (read-only, isolated, parallel)
- **The Loop** continues until reviewers are satisfied (max 3 iterations)

This adversarial approach catches errors before they propagate. The **Independence Wall** between the Architect and the review system is mechanically enforced — the Architect literally cannot read `review-rules.yaml` (blocked by a PreToolUse hook), and reviewers literally cannot write files (blocked by `disallowedTools` and `permissionMode: plan`).

### Memory Philosophy

**"Nothing is lost. Nothing is summarized."**

Every interaction, decision, review, and handoff is stored in full. Agents access relevant context through the Memory Agent, ensuring they have the information they need without context limits.

---

## 3. System Architecture

### High-Level Overview

```
+-----------------------------------------------------------------------+
|                           ACOS v3.0                                    |
|                   (Native Claude Code Primitives)                      |
+-----------------------------------------------------------------------+
|                                                                        |
|  +------------------------------------------------------------------+ |
|  |                    USER (Vibe Coder)                               | |
|  |  - Provides vision via interview                                   | |
|  |  - Edits review-rules.yaml (only human can)                        | |
|  |  - Approves agent changes                                          | |
|  +-------------------------------+----------------------------------+ |
|                                  |                                     |
|                                  v                                     |
|  +------------------------------------------------------------------+ |
|  |               ARCHITECT (architect.md)                             | |
|  |  model: opus | permissionMode: default | maxTurns: 100            | |
|  |                                                                    | |
|  |  - Conducts vision interviews                                      | |
|  |  - Plans: Vision > Epic > Story > Slice                            | |
|  |  - Delegates via Task(developer), Task(reviewer)                   | |
|  |  - Responds to review feedback                                     | |
|  |  - BLOCKED from reading review-rules.yaml (hook enforced)          | |
|  |                                                                    | |
|  |  Skills: acos-plan, acos-interview, acos-feedback-resolution,      | |
|  |          agent-creation, skill-creation                            | |
|  +------+----------+----------+----------+--------------------------+ |
|         |          |          |          |                              |
|    Task(dev)  Task(qa)  Task(sec)  Task(perf)  Task(intg)              |
|         |          |          |          |          |                   |
|         v          v          v          v          v                   |
|  +-----------+ +--------------------------------------------------+   |
|  | DEVELOPER | |              REVIEWERS (Independent)              |   |
|  | opus      | |  qa-reviewer     | permissionMode: plan           |  |
|  | acceptEdit| |  security-reviewer| disallowedTools: Write,Edit,  |  |
|  | maxT: 50  | |  performance-rev  |   Task,WebSearch,WebFetch     |  |
|  |           | |  integration-rev  | maxTurns: 30                  |  |
|  | check-    | |                   |                               |  |
|  | scope.sh  | |  Assigned by review-rules.yaml (script-mediated)  |  |
|  | enforced  | |  Run in parallel, isolated contexts               |  |
|  +-----------+ +--------------------------------------------------+   |
|                                                                        |
|  +------------------------------------------------------------------+ |
|  |                    SUPPORT AGENTS                                  | |
|  |  memory-agent (sonnet, memory: project) - RAG retrieval           | |
|  |  learning-agent (opus, memory: user) - Cross-project learning     | |
|  +------------------------------------------------------------------+ |
|                                                                        |
|  +------------------------------------------------------------------+ |
|  |               ENFORCEMENT LAYER (.claude/scripts/)                 | |
|  |  check-scope.sh        - Blocks writes outside active slice        | |
|  |  block-review-rules.sh - Blocks Architect from review-rules.yaml   | |
|  |  post-write-evidence.sh - Logs all file modifications              | |
|  |  assign-reviewers.sh   - Programmatic reviewer assignment          | |
|  |  create-evidence-bundle.sh - Initializes evidence structure        | |
|  |  validate-evidence.sh  - Verifies evidence completeness            | |
|  |  log-agent-completion.sh - Tracks agent completions                | |
|  |  archive-project.sh    - Archives completed projects               | |
|  +------------------------------------------------------------------+ |
|                                                                        |
|  +------------------------------------------------------------------+ |
|  |               HOOKS (.claude/settings.local.json)                  | |
|  |  PreToolUse[Write|Edit]  -> check-scope.sh                        | |
|  |  PostToolUse[Write|Edit] -> post-write-evidence.sh                | |
|  |  SubagentStop            -> log-agent-completion.sh               | |
|  +------------------------------------------------------------------+ |
|                                                                        |
+-----------------------------------------------------------------------+
```

### How Delegation Works

The Architect orchestrates all work through Claude Code's native `Task()` primitive:

```
Architect
    |
    +-- Task(developer) -----> Developer works in isolated context
    |                          - Receives: slice spec, acceptance criteria, files_allowed
    |                          - Returns: structured YAML with status, files_modified, evidence_path
    |
    +-- Task(qa-reviewer) ---> QA works in isolated context (parallel)
    |                          - Receives: evidence bundle, source of truth, slice spec
    |                          - Returns: structured YAML with verdict, scores, issues
    |
    +-- Task(security-reviewer) -> Security works in isolated context (parallel)
    |
    +-- Task(memory-agent) ---> Memory retrieval
    |
    +-- Task(learning-agent) -> Learning extraction
```

Each `Task()` call creates an **isolated subprocess**. The sub-agent cannot see the parent's conversation, other sub-agents' output, or anything outside its own context. This is the mechanical basis of the Independence Wall.

---

## 4. The Five Pillars

ACOS v3.0 is built on five foundational pillars:

### Pillar 1: Agents (Who)

8 specialized agents defined in `.claude/agents/*.md`. Each has tool restrictions, permission modes, and hooks that mechanically enforce their boundaries. The Architect spawns all others via `Task()`.

### Pillar 2: Skills (What)

27 skills defined in `.claude/skills/*/SKILL.md`. Auto-discovered by Claude Code. Cover methodology (backend-coding, testing, security-audit) and orchestration (slice execution, review, learning extraction).

### Pillar 3: Orchestration Skills (How)

13 orchestration skills replace the old YAML flow system. They use `context: fork` to run in isolated contexts and `agent: architect` to run as the Architect persona. They orchestrate multi-agent workflows by calling `Task()` to delegate work.

### Pillar 4: Memory (Context)

Project memory stored in `memory/` with structured directories. Agents access memory through the Memory Agent or directly via file reads. Source-of-truth documents are always accessible. Cross-project persistence via `memory: user` field.

### Pillar 5: Learning (Evolution)

Cross-project knowledge accumulation in `learning-curve/`. The Learning Agent (`memory: user`) extracts patterns from completed work and applies them to new projects. Knowledge persists across projects via Claude Code's native user-scoped memory.

---

## 5. Agents

### 5.1 Agent Roster

All agents are defined in `.claude/agents/` and auto-discovered by Claude Code.

| Agent | Model | Mode | Max Turns | Role |
|-------|-------|------|-----------|------|
| `architect` | opus | default | 100 | Strategic orchestrator. Plans, delegates, responds to feedback. |
| `developer` | opus | acceptEdits | 50 | Implements code within scope boundaries. Creates evidence. |
| `qa-reviewer` | opus | plan (read-only) | 30 | Adversarial quality verification. |
| `security-reviewer` | opus | plan (read-only) | 30 | OWASP-focused security analysis. |
| `performance-reviewer` | opus | plan (read-only) | 30 | Algorithmic/resource efficiency. |
| `integration-reviewer` | opus | plan (read-only) | 30 | Cross-component coherence. |
| `memory-agent` | sonnet | default | 20 | RAG retrieval and memory organization. |
| `learning-agent` | opus | default | 30 | Cross-project knowledge extraction. |

### 5.2 Agent Categories

**Orchestration (Architect)**
- Has `Task()` access to spawn ALL other agents
- Has PreToolUse hook blocking `review-rules.yaml` reads
- Has 5 preloaded skills (acos-plan, acos-interview, acos-feedback-resolution, agent-creation, skill-creation)
- Uses `memory: project` for project-scoped persistence

**Execution (Developer)**
- Has Write/Edit tools but scoped by `check-scope.sh` hook
- Has `disallowedTools: WebSearch, WebFetch, Task` (cannot browse or delegate)
- Has 4 preloaded skills (backend-coding, frontend-coding, database-design, testing)
- Returns structured evidence on completion

**Review (4 reviewers)**
- **Mechanically read-only**: `disallowedTools: Write, Edit, Task, WebSearch, WebFetch`
- **Mechanically isolated**: `permissionMode: plan` prevents any modifications at runtime
- Each runs in isolated `Task()` context — cannot see Architect decisions, other reviewers, or each other
- Each returns structured YAML verdict with scores, issues, and required fixes

**Support (memory-agent, learning-agent)**
- Have Write/Edit for their own domains
- `disallowedTools: Task, WebSearch, WebFetch` (cannot delegate or browse)
- memory-agent uses `memory: project`, learning-agent uses `memory: user` (cross-project)

### 5.3 Agent Definition Format (Native)

```markdown
---
name: agent-name
description: One-line description for auto-discovery
tools: Read, Write, Edit, Glob, Grep, Bash
disallowedTools: Task, WebSearch, WebFetch
model: opus
permissionMode: default | acceptEdits | plan
maxTurns: 30
skills:
  - skill-name
memory: project | user
hooks:
  PreToolUse:
    - matcher: "Read"
      hooks:
        - type: command
          command: ".claude/scripts/block-review-rules-read.sh"
---

# Agent Name

## Role
[Description of the agent's role and purpose]

## Core Responsibilities
### 1. [Responsibility]
[Details and instructions]

## Critical Constraints
### You CANNOT:
- [Mechanically enforced constraint]

### You MUST:
- [Required behavior]

## Return Value
[Structured YAML format the agent returns via Task()]

---
*[Agent Name] - [Tagline]*
```

### 5.4 Agent Creation

The Architect can create new agents when needed:

1. Architect identifies need ("I need a specialized agent")
2. Architect uses the `agent-creation` skill
3. Agent definition drafted following the native format
4. **Human approval required** before the agent is deployed
5. Definition saved to `.claude/agents/`

---

## 6. Skills

### 6.1 Skill Philosophy

Skills are **methodology guides** — they describe how to approach a type of work. There are two categories:

- **Methodology Skills** (14): Describe how to do a type of work (coding, testing, security auditing)
- **Orchestration Skills** (13): Orchestrate multi-agent workflows (slice execution, review, learning)

### 6.2 Methodology Skills

All skills live in `.claude/skills/*/SKILL.md` and are auto-discovered by Claude Code.

| Skill | Description |
|-------|-------------|
| `backend-coding` | Server-side logic, APIs, services (Express, Django, FastAPI, etc.) |
| `frontend-coding` | UI components, client-side logic (React, Vue, Svelte, etc.) |
| `database-design` | Schema design, migrations, data access (PostgreSQL, MongoDB, etc.) |
| `testing` | Unit, integration, E2E tests (Jest, Playwright, pytest, etc.) |
| `bug-investigation` | Systematic bug investigation and root cause analysis |
| `codebase-analysis` | Analyzing existing codebases and mapping architecture |
| `technology-research` | Evaluating libraries, comparing approaches |
| `api-documentation` | API docs, OpenAPI specs, usage examples |
| `user-guide-writing` | User documentation and getting-started guides |
| `deployment` | Deploying to production (Vercel, AWS, Docker, K8s, etc.) |
| `security-audit` | OWASP Top 10 security auditing |
| `agent-creation` | Creating new ACOS agent definitions (requires human approval) |
| `skill-creation` | Creating new ACOS skill definitions |
| `orchestration-creation` | Creating new orchestration skills |

### 6.3 Skill Definition Format (Native)

```markdown
---
name: skill-name
description: Enhanced description for auto-discovery
disable-model-invocation: true | false
user-invocable: true | false
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
context: fork                          # Optional: isolated execution
agent: architect                       # Optional: which agent persona
---

# Skill Name

## Purpose
[What this skill teaches/guides]

## When to Use
Apply this skill when:
- [Condition 1]
- [Condition 2]

## Skill Protocol
### Phase 1: [Name]
[Step-by-step instructions]

## Quality Checklist
- [ ] [Criterion 1]

---
*[Skill Name] - [Tagline]*
```

Skills can include supporting files:
- `templates/` — Template files referenced via `!cat templates/file.md`
- `examples/` — Code examples for reference

---

## 7. Orchestration Skills

### 7.1 What Are Orchestration Skills?

Orchestration skills replace the old YAML flow system. They are skills that use `context: fork` (isolated execution) and `agent: architect` (Architect persona) to orchestrate multi-agent workflows through `Task()` delegation.

Unlike methodology skills (which are guidance documents), orchestration skills **actively execute** — they spawn sub-agents, collect results, make decisions, and handle failures.

### 7.2 Orchestration Skill Roster

| Skill | User-Invocable | Description |
|-------|:---:|-------------|
| `/acos-start` | Yes | Initialize project and route to next step based on current state. |
| `/acos-interview` | Yes | Comprehensive vision interview (9 question categories, max 10 rounds). |
| `/acos-plan` | Yes | Create planning documents at any level (vision/epic/story/slice). |
| `/acos-execute-slice` | Yes | **Core workflow.** Developer -> Evidence -> Reviewer Assignment -> Parallel Review -> Pass/Reject loop. |
| `/acos-execute-story` | Yes | Execute all slices in dependency order, then story-level integration review. |
| `/acos-execute-epic` | Yes | Execute all stories, then epic-level review with all 4 reviewers. |
| `/acos-complete-vision` | Yes | Execute all epics, vision-level review, user acceptance, learning extraction, archival. |
| `/acos-review` | Yes | Trigger reviews for completed work at any level. |
| `/acos-decide` | Yes | Create Architecture Decision Records (ADRs). |
| `/acos-handoff` | Yes | Create session handoff documents for continuity. |
| `/acos-status` | Yes | Display comprehensive project dashboard. |
| `/acos-learn` | Yes | Extract learnings from completed work. |
| `acos-feedback-resolution` | No (internal) | Resolve reviewer feedback. Max 3 iterations before human escalation. |

### 7.3 The Core Execution Flow

The most important orchestration skill is `acos-execute-slice`. Here's how it works:

```
1. Read Slice Spec (planning/slices/SLICE-XXX.yaml)
   |
2. Set Active Slice (.acos/config/active-slice.yaml)
   |  - Enables check-scope.sh hook enforcement
   |
3. Create Evidence Bundle (.acos/evidence/[DATE]/[SLICE-ID]/)
   |
4. Task(developer) --> Developer implements in isolated context
   |                    Returns: files_modified, evidence_bundle_path
   |
5. Run assign-reviewers.sh with file/code manifest
   |  - Script reads review-rules.yaml (Architect cannot)
   |  - Returns JSON array of reviewer names
   |
6. Task(qa-reviewer) + Task(security-reviewer) + ... (in parallel)
   |  Each receives: evidence bundle, source of truth, slice spec
   |  Each returns: verdict (PASS/REJECT), scores, issues
   |
7. Aggregate Verdicts
   |  ALL PASS --> Step 9 (Completion)
   |  ANY REJECT --> Step 8 (Feedback Resolution)
   |
8. acos-feedback-resolution (max 3 iterations)
   |  - Consolidate all feedback
   |  - Create unified fix plan
   |  - Task(developer) implements fixes
   |  - Re-review with same reviewers
   |  - If still failing after 3: escalate to human
   |
9. Completion
   - Update slice status to completed
   - Clear active-slice.yaml
   - Write handoff summary
```

---

## 8. Memory System

### 8.1 Memory Philosophy

**"Nothing is lost. Nothing is summarized."**

All interactions, decisions, reviews, and handoffs are stored in full. The Memory Agent provides retrieval services across all memory directories.

### 8.2 Memory Structure

```
memory/
+-- source-of-truth/              # Core project documents
|   +-- vision-interview.md       # Complete Q&A transcript
|   +-- vision-document.md        # Synthesized requirements
|
+-- decisions/                    # Architecture Decision Records
|   +-- ADR-001-[title].md
|   +-- ADR-002-[title].md
|
+-- reviews/                      # Review audit trail
|   +-- slice-reviews/
|   +-- story-reviews/
|   +-- epic-reviews/
|   +-- vision-reviews/
|
+-- handoffs/                     # Session continuity
|   +-- [timestamp]-session-handoff.yaml
|
+-- code-rationale/               # Why code decisions were made
|
+-- feedback-history/             # All feedback and resolutions
```

### 8.3 Memory Access Model

Memory access is controlled by agent-level tool restrictions and isolated `Task()` contexts:

| Agent | Access Mechanism | Scope |
|-------|-----------------|-------|
| Architect | Direct file reads + `Task(memory-agent)` | All memory except review-rules.yaml |
| Developer | Receives relevant context in `Task()` prompt | Slice-specific context only |
| Reviewers | Receives evidence bundle in `Task()` prompt | Evidence + source of truth + spec only |
| Memory Agent | `memory: project` + direct file access | All memory (for retrieval) |
| Learning Agent | `memory: user` + direct file access | Learning curve + reviews + feedback |

### 8.4 Cross-Project Persistence

Two levels of memory persistence via native Claude Code primitives:

- **`memory: project`** — Persists within the current project across sessions. Used by the Architect and Memory Agent.
- **`memory: user`** — Persists across ALL projects for the user. Used by the Learning Agent, enabling cross-project knowledge transfer.

---

## 9. Learning Curve System

### 9.1 Purpose

Cross-project knowledge accumulation. The system improves over time by learning from both successes and failures. The Learning Agent uses `memory: user` for TRUE cross-project persistence.

### 9.2 Structure

```
learning-curve/
+-- patterns/                     # What works
|   +-- architectural/
|   +-- implementation/
|   +-- review/
|   +-- workflow/
|
+-- anti-patterns/                # What doesn't work
|   +-- common-mistakes/
|   +-- failed-approaches/
|   +-- pitfalls/
|
+-- domain-knowledge/             # Domain-specific insights
|
+-- agent-effectiveness/          # How well agents performed
|
+-- project-retrospectives/       # Post-project analysis
|
+-- index.yaml                    # Master index
```

### 9.3 What Gets Learned

- **Patterns**: Successful architectural decisions, implementation approaches, effective agent configurations
- **Anti-patterns**: Failed approaches, common mistakes, pitfalls to avoid
- **Domain knowledge**: Technology-specific insights
- **Agent effectiveness**: Which agent configurations work best for which tasks
- **Process insights**: Effective workflows, review patterns, feedback resolution strategies

### 9.4 Learning Extraction

**Trigger**: Project completion (via `/acos-learn` skill)

**Process**:
1. Architect invokes `acos-learn` skill
2. `Task(memory-agent)` collects all project memory artifacts
3. `Task(learning-agent)` analyzes decisions, reviews, and workflow
4. Learning Agent extracts patterns and anti-patterns with evidence
5. Entries saved to `learning-curve/` with confidence levels
6. Index updated

### 9.5 Confidence Levels

| Level | Criteria |
|-------|----------|
| **HIGH** | 3+ successful applications, >80% success rate |
| **MEDIUM** | 1-2 applications, >50% success rate |
| **LOW** | New/unvalidated, <50% success rate |

Learnings with <30% success rate are deprecated. Conflicting learnings are kept with full context.

---

## 10. Review System

### 10.1 Core Principles

1. **Maximum rigor at ALL levels** — No shortcuts, ever
2. **Rules-based assignment** — Architect has ZERO control
3. **Human-editable rules only** — No agent can read or modify `review-rules.yaml`
4. **Parallel and independent** — Reviewers don't see each other's feedback
5. **All must pass** — Single failure = rejection
6. **Mechanically enforced** — Not just instructions, but `disallowedTools` + `permissionMode: plan` + hooks

### 10.2 The Independence Wall

```
+=================================================================+
|                  ARCHITECT'S DOMAIN                              |
|                                                                  |
|  - Vision interview                                              |
|  - Planning (epics/stories/slices)                               |
|  - Selecting execution agents                                    |
|  - Creating new agents/skills                                    |
|  - Responding to feedback                                        |
|                                                                  |
|  MECHANICALLY BLOCKED FROM:                                      |
|  - Reading review-rules.yaml (PreToolUse hook)                   |
|  - Influencing reviewer assignment (script-mediated)             |
|  - Seeing review process internals                               |
+==================================================================+
|  ================ INDEPENDENCE WALL ============================  |
|  Enforced by: hooks + disallowedTools + permissionMode + Task()   |
+==================================================================+
|                                                                  |
|                  REVIEW SYSTEM (Architect cannot touch)           |
|                                                                  |
|  - Which reviewers assigned (determined by review-rules.yaml)    |
|  - Review depth (ALWAYS maximum)                                 |
|  - Review process (fixed protocol)                               |
|  - Reviewer isolation (permissionMode: plan, no Write/Edit/Task) |
|  - Review verdicts (structured YAML, not prose)                  |
|                                                                  |
+=================================================================+
```

### 10.3 Review Rules File

**Location**: `review-rules.yaml` at project root

**Only humans can edit this file.** The Architect is mechanically blocked from reading it by `.claude/scripts/block-review-rules-read.sh` (configured as a PreToolUse hook on the Architect agent).

### 10.4 Reviewer Assignment

The `assign-reviewers.sh` script reads `review-rules.yaml` and determines reviewers based on 7 trigger types:

| Trigger Type | Example |
|-------------|---------|
| `file_path_contains` | `["auth", "login", "password"]` |
| `code_contains` | `["SELECT", "encrypt", "express"]` |
| `files_modified_count_greater_than` | `3` |
| `imports_from_multiple_modules` | `true` |
| `always` | `true` (fallback) |

Rules are additive — all matching rules apply. The file contains 9 slice-level rules covering: security-sensitive code, database code, API endpoints, payment code, file operations, external integrations, multi-component changes, performance-critical code, and a default fallback.

Higher-level reviews (story/epic/vision) aggregate reviewers from lower levels plus additional mandatory reviewers.

### 10.5 Review Process

1. Developer completes work and creates evidence bundle
2. `assign-reviewers.sh` reads `review-rules.yaml` (script-mediated, Architect cannot see)
3. Matching rules determine which reviewers are assigned
4. All assigned reviewers run via `Task()` in PARALLEL, ISOLATED contexts
5. Each reviewer returns structured YAML verdict (PASS/REJECT with scores and issues)
6. If ALL pass -> work approved
7. If ANY reject -> `acos-feedback-resolution` consolidates feedback
8. Architect creates ONE coherent fix addressing ALL concerns
9. Developer implements fix, re-review runs
10. Max 3 iterations before human escalation

### 10.6 Reviewer Verdicts

Each reviewer returns a structured YAML verdict:

```yaml
verdict: PASS | REJECT
reviewer: qa-reviewer
slice_id: SLICE-XXX
scores:
  evidence_authenticity: PASS
  acceptance_criteria: PASS
  scope_compliance: PASS
  code_quality: PASS
  total: PASS
issues:
  - severity: CRITICAL | HIGH | MEDIUM | LOW
    description: "..."
    location: "file:line"
    fix_required: "..."
required_before_resubmission:
  - "Fix description"
overall_feedback: "..."
```

### 10.7 Permissions Matrix

| Entity | Read Rules | Edit Rules | Influence Review | Bypass Review |
|--------|:---:|:---:|:---:|:---:|
| Human User | Yes | Yes | No | No |
| Architect | **Blocked (hook)** | No | No | No |
| Reviewers | No | No | No | No |
| Developer | No | No | No | No |
| Support Agents | No | No | No | No |

---

## 11. Vision Interview Process

### 11.1 Philosophy

ACOS does NOT accept one-line visions. Every project begins with a comprehensive interview conducted by the Architect using the `acos-interview` skill.

### 11.2 Interview Protocol

The interview covers 9 question categories:

1. **Users & Audience** — Who will use this? Technical level? Primary vs secondary users?
2. **Platforms & Devices** — Web? Mobile? Desktop? Responsive? Offline support?
3. **Features & Scope** — Must-have? Nice-to-have? Explicitly excluded? MVP vs full vision?
4. **Scale & Performance** — Expected users? Data volume? Growth? Performance requirements?
5. **Integrations** — External services? Third-party APIs? Existing systems?
6. **Security & Compliance** — Sensitive data? Compliance (HIPAA, GDPR)? Auth needs?
7. **Design & UX** — Visual style? Brand guidelines? Accessibility?
8. **Technology Preferences** — Preferred languages? Frameworks? Hosting? Existing infrastructure?
9. **Success Criteria** — How do we know it's done? Key metrics? Launch criteria?

### 11.3 Interview Loop

- Max 10 rounds of 3-5 questions each
- Each round targets remaining gaps in the 9 categories
- Interview ends when: Architect is satisfied, user says "that's enough", or max iterations reached

### 11.4 Output Documents

**`memory/source-of-truth/vision-interview.md`** — Complete Q&A transcript organized by round (template at `.claude/skills/acos-interview/templates/vision-interview.md`)

**`memory/source-of-truth/vision-document.md`** — Synthesized requirements with users, platforms, features (prioritized), technical requirements, integrations, design, tech stack, success criteria (template at `.claude/skills/acos-interview/templates/vision-document.md`)

Both become the **Source of Truth** for the entire project.

---

## 12. User Interaction Model

### 12.1 User Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Provide vision | Describe what you want to build |
| Answer interview | Respond to the Architect's questions |
| Edit review rules | Customize `review-rules.yaml` if needed |
| Resolve escalations | Help when things fail 3+ times |
| Approve agent changes | Required for new agent definitions |

### 12.2 CLI Commands

The `acos` CLI is a thin wrapper for launching Claude Code sessions:

| Command | Description |
|---------|-------------|
| `acos start` | Start a **new** Claude Code session (fresh conversation) |
| `acos resume` | Resume the **previous** session (restores conversation history) |
| `acos help` | Show available commands |

### 12.3 User Commands (Native Skills)

All commands are native Claude Code skills, invoked from the `/` menu inside a session:

| Skill | Description |
|-------|-------------|
| `/acos-start` | Initialize project and route to next step |
| `/acos-interview` | Conduct vision interview |
| `/acos-plan [level]` | Create planning documents |
| `/acos-execute-slice [ID]` | Execute a single slice |
| `/acos-execute-story [ID]` | Execute a full story |
| `/acos-execute-epic [ID]` | Execute a full epic |
| `/acos-complete-vision` | Complete entire vision |
| `/acos-review` | Trigger reviews |
| `/acos-status` | Show project dashboard |
| `/acos-decide` | Create Architecture Decision Record |
| `/acos-handoff` | Create session handoff |
| `/acos-learn` | Extract learnings |

### 12.4 Automatic Escalation

User is automatically notified when:
- Slice/Story/Epic fails review 3+ times
- Architect cannot find/create suitable agent
- Critical ambiguity in requirements
- Agent modification is proposed

### 12.5 User Can Always

- Check progress at any time (`/acos-status`)
- Intervene at any time
- Provide additional instructions
- Edit `review-rules.yaml`

---

## 13. Mechanical Enforcement

### 13.1 Why Mechanical Enforcement?

Instructions alone are not sufficient for adversarial trust. ACOS uses Claude Code's native enforcement mechanisms to make trust violations **mechanically impossible**, not just forbidden.

### 13.2 Enforcement Mechanisms

| Mechanism | What It Does | Where Configured |
|-----------|-------------|-----------------|
| `disallowedTools` | Prevents agent from using specific tools | Agent `.md` frontmatter |
| `permissionMode: plan` | Makes agent read-only at runtime | Agent `.md` frontmatter |
| PreToolUse hooks | Runs script before tool execution, can block | `.claude/settings.local.json` + agent hooks |
| PostToolUse hooks | Runs script after tool execution, logs evidence | `.claude/settings.local.json` |
| SubagentStop hooks | Runs script when sub-agent completes | `.claude/settings.local.json` |
| `Task()` isolation | Each sub-agent runs in isolated context | Native Claude Code primitive |
| Scope scripts | Block writes outside allowed files | `.claude/scripts/check-scope.sh` |

### 13.3 Scripts

| Script | Trigger | Purpose |
|--------|---------|---------|
| `check-scope.sh` | PreToolUse (Write/Edit) | Reads `.acos/config/active-slice.yaml`, blocks writes to files not in `files_allowed` |
| `block-review-rules-read.sh` | PreToolUse (Read) on Architect | Blocks any read of `review-rules.yaml` |
| `post-write-evidence.sh` | PostToolUse (Write/Edit) | Logs every file modification to evidence bundle |
| `assign-reviewers.sh` | Called by orchestration skills | Reads `review-rules.yaml`, returns JSON array of reviewer names |
| `create-evidence-bundle.sh` | Called by orchestration skills | Creates evidence directory structure for a slice |
| `validate-evidence.sh` | Called by orchestration skills | Verifies evidence bundle completeness |
| `log-agent-completion.sh` | SubagentStop | Logs agent completion to `.acos/metrics/agent-completions.log` |
| `archive-project.sh` | Called by orchestration skills | Archives completed project artifacts |

---

## 14. Folder Structure

```
Project Root/
|
+-- CLAUDE.md                        # Project context (auto-loads at session start)
+-- review-rules.yaml                # HUMAN-EDITABLE ONLY
+-- PRD.md                           # This document
+-- QUICK-START.md                   # Quick start guide
+-- BEGINNERS-GUIDE.md               # Beginner's guide
|
+-- .claude/                         # Native Claude Code configuration
|   +-- agents/                      # Agent definitions (auto-discovered)
|   |   +-- architect.md
|   |   +-- developer.md
|   |   +-- qa-reviewer.md
|   |   +-- security-reviewer.md
|   |   +-- performance-reviewer.md
|   |   +-- integration-reviewer.md
|   |   +-- memory-agent.md
|   |   +-- learning-agent.md
|   |
|   +-- skills/                      # Skill definitions (auto-discovered)
|   |   +-- acos-start/SKILL.md
|   |   +-- acos-interview/
|   |   |   +-- SKILL.md
|   |   |   +-- templates/
|   |   |       +-- vision-interview.md
|   |   |       +-- vision-document.md
|   |   +-- acos-plan/
|   |   |   +-- SKILL.md
|   |   |   +-- templates/
|   |   |       +-- vision.yaml, epic.yaml, story.yaml, slice.yaml
|   |   +-- acos-execute-slice/
|   |   |   +-- SKILL.md
|   |   |   +-- templates/
|   |   |       +-- developer-assignment.yaml
|   |   +-- acos-execute-story/SKILL.md
|   |   +-- acos-execute-epic/SKILL.md
|   |   +-- acos-complete-vision/SKILL.md
|   |   +-- acos-review/
|   |   |   +-- SKILL.md
|   |   |   +-- templates/
|   |   |       +-- slice-review.md, story-review.md, epic-review.md, vision-review.md
|   |   +-- acos-decide/
|   |   |   +-- SKILL.md
|   |   |   +-- templates/
|   |   |       +-- adr.md
|   |   +-- acos-handoff/SKILL.md
|   |   +-- acos-status/SKILL.md
|   |   +-- acos-learn/
|   |   |   +-- SKILL.md
|   |   |   +-- templates/
|   |   |       +-- pattern.md, anti-pattern.md, retrospective.md
|   |   +-- acos-feedback-resolution/SKILL.md
|   |   +-- backend-coding/SKILL.md
|   |   +-- frontend-coding/SKILL.md
|   |   +-- database-design/SKILL.md
|   |   +-- testing/SKILL.md
|   |   +-- bug-investigation/SKILL.md
|   |   +-- codebase-analysis/SKILL.md
|   |   +-- technology-research/SKILL.md
|   |   +-- api-documentation/SKILL.md
|   |   +-- user-guide-writing/SKILL.md
|   |   +-- deployment/SKILL.md
|   |   +-- security-audit/SKILL.md
|   |   +-- agent-creation/SKILL.md
|   |   +-- skill-creation/SKILL.md
|   |   +-- orchestration-creation/SKILL.md
|   |
|   +-- scripts/                     # Enforcement scripts
|   |   +-- check-scope.sh
|   |   +-- block-review-rules-read.sh
|   |   +-- post-write-evidence.sh
|   |   +-- assign-reviewers.sh
|   |   +-- create-evidence-bundle.sh
|   |   +-- validate-evidence.sh
|   |   +-- log-agent-completion.sh
|   |   +-- archive-project.sh
|   |
|   +-- settings.local.json          # Hooks configuration
|
+-- .acos/                           # Runtime state
|   +-- config/
|   |   +-- project.yaml
|   |   +-- active-slice.yaml        # Current scope (read by check-scope.sh)
|   +-- evidence/                    # Evidence bundles
|   |   +-- [DATE]/[SLICE-ID]/
|   |       +-- before/
|   |       +-- after/
|   |       +-- verify.log
|   |       +-- Summary.md
|   +-- metrics/
|       +-- agent-completions.log
|
+-- memory/                          # Project memory
|   +-- source-of-truth/
|   +-- decisions/
|   +-- reviews/
|   |   +-- slice-reviews/
|   |   +-- story-reviews/
|   |   +-- epic-reviews/
|   |   +-- vision-reviews/
|   +-- handoffs/
|   +-- code-rationale/
|   +-- feedback-history/
|
+-- planning/                        # Planning hierarchy
|   +-- vision/
|   +-- epics/
|   +-- stories/
|   +-- slices/
|
+-- learning-curve/                  # Cross-project learnings
|   +-- patterns/
|   +-- anti-patterns/
|   +-- domain-knowledge/
|   +-- agent-effectiveness/
|   +-- project-retrospectives/
|   +-- index.yaml
|
+-- automation-scripts/              # Thin CLI wrapper
    +-- acos                         # CLI: `acos start` (new session), `acos resume` (continue previous)
```

---

## 15. Safeguards & Constraints

### 15.1 Critical Safeguards

| Safeguard | Enforcement Mechanism |
|-----------|----------------------|
| Architect cannot read review rules | PreToolUse hook -> `block-review-rules-read.sh` |
| Architect cannot modify review rules | No Write access to that file (script blocks it) |
| Reviewers are read-only | `disallowedTools: Write, Edit, Task` + `permissionMode: plan` |
| Reviewers are isolated | Each runs in separate `Task()` context |
| Reviewers cannot communicate | `disallowedTools: Task` prevents spawning sub-agents |
| Developer stays in scope | PreToolUse hook -> `check-scope.sh` |
| All writes create evidence | PostToolUse hook -> `post-write-evidence.sh` |
| Agent changes need human approval | Stated in CLAUDE.md restricted files |
| Review depth is always maximum | Global setting in `review-rules.yaml` |

### 15.2 What Architect CANNOT Do

- Read `review-rules.yaml` (mechanically blocked by hook)
- Modify `review-rules.yaml`
- Influence which reviewers are assigned (script-mediated)
- Reduce review depth
- Bypass review process
- See reviewer feedback before submission
- Evolve agent definitions without human approval

### 15.3 What Reviewers CANNOT Do

- Write or edit any files (`disallowedTools: Write, Edit`)
- Spawn sub-agents (`disallowedTools: Task`)
- Browse the web (`disallowedTools: WebSearch, WebFetch`)
- See Architect's decisions (isolated `Task()` context)
- See other reviewers' feedback (isolated `Task()` context)
- Modify review rules

### 15.4 What Humans CANNOT Do

- Bypass reviews (can only edit rules)
- Approve their own work

### 15.5 System Constraints

- Maximum 3 feedback resolution iterations before human escalation
- All memory stored in full (no summarization)
- Source of truth always accessible to all agents
- QA reviewer always assigned (global rule)
- All reviewers must pass for work to proceed

---

## 16. Glossary

| Term | Definition |
|------|------------|
| **Agent** | Specialized AI worker defined in `.claude/agents/` with tool restrictions and permissions |
| **Architect** | The orchestrating agent that plans and delegates via `Task()` |
| **Developer** | Execution agent that implements code within scope boundaries |
| **Reviewer** | Read-only agent that independently verifies work quality |
| **Skill** | Methodology guide defined in `.claude/skills/*/SKILL.md` |
| **Orchestration Skill** | Skill with `context: fork` + `agent: architect` that orchestrates multi-agent workflows |
| **Memory** | Persistent storage of all project context in `memory/` |
| **Learning Curve** | Cross-project knowledge accumulation in `learning-curve/` |
| **Slice** | Atomic unit of work — small enough for one session, independently reviewable |
| **Story** | User-facing feature composed of multiple slices |
| **Epic** | Major capability composed of multiple stories |
| **Vision** | User's complete project description (captured via interview) |
| **Source of Truth** | Core documents (vision-interview.md + vision-document.md) in `memory/source-of-truth/` |
| **Evidence Bundle** | Proof of completed work (before/after snapshots, diffs, test results) in `.acos/evidence/` |
| **Independence Wall** | Mechanical separation between Architect and review system |
| **Review Rules** | Human-defined rules for reviewer assignment in `review-rules.yaml` |
| **Task()** | Claude Code primitive that spawns an agent in an isolated subprocess |
| **Hook** | Script that runs before/after tool execution for enforcement |
| **Scope** | The set of files a developer is allowed to modify for a given slice |
| **Vibe Coder** | The human user of ACOS |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 3.0 | 2026-01-31 | Initial v3.0 architecture |
| 3.0.1 | 2026-02-07 | Updated to reflect native Claude Code primitives migration. Replaced old agent/skill/flow formats with native `.claude/agents/` and `.claude/skills/` formats. Added Mechanical Enforcement section. Updated folder structure, commands, and glossary. |
| 3.0.2 | 2026-02-10 | Split CLI: `acos start` now always starts a fresh session, `acos resume` continues previous session. Added CLI commands section (12.2). Updated `/acos-start` descriptions to clarify it handles project routing, not session management. |

---

*ACOS v3.0 - You describe it. We build it.*
