# ACOS v3.0 Quick Start Guide

Welcome to ACOS (Agentic Coding Orchestration System) v3.0!

## What is ACOS?

ACOS is a sophisticated, self-evolving coding system that:
- Interviews you to understand your vision
- Breaks it down into manageable pieces
- Implements code through specialized agents
- Reviews work with independent, rigorous reviewers
- Learns from every project to get smarter

## Getting Started

### Step 1: Open Claude Code

Navigate to your project directory and open Claude Code. ACOS uses native Claude Code primitives — `CLAUDE.md` auto-loads at session start, agents are in `.claude/agents/`, and skills are in `.claude/skills/`.

### Step 2: Start Your Project

In Claude Code, type:

```
/acos-start
```

This will:
- Initialize directories if needed (`.acos/`, `memory/`, `planning/`)
- Check for existing vision documents
- Route you to the appropriate next step

### Step 3: Conduct Vision Interview

If starting fresh, ACOS will begin a comprehensive vision interview. The Architect will:
1. Ask comprehensive questions about your vision
2. Create detailed requirements
3. Break it down into Epics → Stories → Slices
4. Orchestrate implementation and review

## How It Works

### The Five Pillars

1. **Agents** (the "who")
   - The Architect: Plans and orchestrates
   - Developer: Implements code
   - Reviewers: QA, Security, Performance, Integration
   - Support: Memory Agent, Learning Curve Agent

2. **Skills** (the "what")
   - Frontend/Backend coding
   - Database design
   - Testing
   - Security audits

3. **Orchestration Skills** (the "how")
   - Vision Interview (`/acos-interview`)
   - Slice Execution (`/acos-execute-slice`)
   - Feedback Resolution (internal)

4. **Memory** (the "context")
   - Source of Truth: Your original vision
   - Decisions, Reviews, Handoffs
   - Nothing is summarized

5. **Learning Curve** (the "evolution")
   - Cross-project knowledge
   - Patterns and anti-patterns
   - Continuous improvement

### The Workflow

```
1. YOU: Describe your vision
      ↓
2. ARCHITECT: Conducts interview
      ↓
3. ARCHITECT: Creates plan (Epics → Stories → Slices)
      ↓
4. DEVELOPER: Implements each slice
      ↓
5. REVIEWERS: Review independently (in parallel)
      ↓
6. If REJECTED: Architect resolves feedback → back to Developer
   If PASSED: Continue to next slice
      ↓
7. Repeat until complete
      ↓
8. LEARNING CURVE: Extracts learnings for future projects
```

## Key Concepts

### Slices

The atomic unit of work. A slice should be:
- Small enough to implement in one session
- Clear acceptance criteria
- Limited to specific files
- Independently reviewable

### Evidence Bundles

Every slice produces evidence proving it's complete:
- Before/after snapshots
- Modified files list
- Git diff
- Test results
- Verification log

### Independent Reviews

Reviewers cannot:
- See the Architect's decisions
- See other reviewers' feedback (before submitting)
- Be influenced to reduce rigor

Review rules are human-editable only (in `review-rules.yaml`).

## Commands Reference

All commands are native Claude Code skills, invocable from the `/` menu:

| Skill | Description |
|-------|-------------|
| `/acos-start` | Start or resume project |
| `/acos-plan` | Create planning documents |
| `/acos-execute-slice` | Execute a slice end-to-end |
| `/acos-execute-story` | Execute a full story |
| `/acos-execute-epic` | Execute a full epic |
| `/acos-complete-vision` | Complete entire vision |
| `/acos-review` | Trigger reviews |
| `/acos-status` | Show project status |
| `/acos-decide` | Create Architecture Decision Record |
| `/acos-handoff-protocol` | Create session handoff |
| `/acos-learn` | Extract learnings |
| `/acos-interview` | Conduct vision interview |

## Tips for Success

1. **Be thorough in the interview**
   - Don't rush - let the Architect ask questions
   - The more context, the better the result

2. **Trust the process**
   - Reviews are rigorous for a reason
   - Feedback makes the final product better

3. **Check the learning curve**
   - Before starting similar work, see what ACOS learned
   - Use `/acos-learn` in Claude Code to review learnings

4. **Stay in the loop**
   - You can always provide commands
   - Override decisions when needed
   - Say "that's enough" when done answering questions

## Directory Structure

```
Your Project/
├── .acos/
│   ├── config/
│   └── evidence/
├── memory/
│   ├── source-of-truth/
│   ├── decisions/
│   ├── reviews/
│   ├── handoffs/
│   └── ...
├── planning/
│   ├── epics/
│   ├── stories/
│   └── slices/
└── [your code]
```

## Getting Help

- Type `/` in Claude Code to see all available ACOS skills
- Agents are in `.claude/agents/` (auto-discovered)
- Skills are in `.claude/skills/` (auto-discovered)
- Run `acos help` from the terminal for a reference

---

*ACOS v3.0 - Building software through intelligent orchestration*
