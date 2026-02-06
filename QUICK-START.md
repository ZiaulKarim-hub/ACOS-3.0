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

### Step 1: Setup

Add ACOS to your PATH:

```bash
export PATH="$PATH:/path/to/ACOS 3.0/automation-scripts"
```

Or create a symlink:

```bash
ln -s "/path/to/ACOS 3.0/automation-scripts/acos" /usr/local/bin/acos
```

### Step 2: Initialize Your Project

Navigate to your project directory and run:

```bash
acos init
```

This creates:
- `.acos/` - ACOS configuration and evidence
- `memory/` - Project memory storage
- `planning/` - Epic/Story/Slice plans

### Step 3: Start Your Vision

```bash
acos start
```

This automatically launches Claude Code with The Architect ready to talk. The Architect will:
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

3. **Flows** (the "how")
   - Vision Interview Flow
   - Slice Execution Flow
   - Feedback Resolution Flow

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

| Command | Description |
|---------|-------------|
| `acos init` | Initialize ACOS in current project |
| `acos start` | Begin vision interview |
| `acos status` | Show project status |
| `acos agents list` | List all agents |
| `acos skills list` | List all skills |
| `acos flows list` | List all flows |
| `acos memory search <term>` | Search project memory |
| `acos review rules` | Show review rules |

## Tips for Success

1. **Be thorough in the interview**
   - Don't rush - let the Architect ask questions
   - The more context, the better the result

2. **Trust the process**
   - Reviews are rigorous for a reason
   - Feedback makes the final product better

3. **Check the learning curve**
   - Before starting similar work, see what ACOS learned
   - `acos learn search <topic>`

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

- Run `acos help` for command reference
- Check `agents/` for agent documentation
- Check `skills/` for skill guides
- Check `agentic-flows/` for flow details

---

*ACOS v3.0 - Building software through intelligent orchestration*
