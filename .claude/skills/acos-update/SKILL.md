---
name: acos-update
description: Researches latest vibe coding developments, identifies ACOS improvement opportunities, plans safe upgrades, and implements approved changes with verification. A self-evolution skill for the ACOS framework.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch, Skill
argument-hint: "[focus-area]"
---

# ACOS Update — Self-Evolution Protocol

## Overview

This skill researches the latest developments in vibe coding, AI-assisted development,
and Claude Code capabilities, then identifies improvements that can be safely incorporated
into ACOS without compromising existing functionality.

**Safety principle:** Research and planning are autonomous. Implementation requires
explicit user approval for each change. Every change is verified before and after.

**Optional argument:** `$ARGUMENTS` narrows the research focus (e.g., "hooks", "agents",
"context management", "security"). If empty, performs broad research across all areas.

### Pre-flight

```bash
bash .claude/scripts/acos-preflight.sh
```

---

## Phase 1: BASELINE — Snapshot Current State

Before any research, capture the current ACOS health baseline so we can verify
nothing breaks after changes.

### Step 1.1: Run Health Check

```bash
bash .claude/scripts/token-gate.sh --health-check
```

Save output as the **pre-update baseline**.

### Step 1.2: Inventory Current Capabilities

Read and catalog:
- Hook count and types from `.claude/settings.local.json`
- Agent count and capabilities from `.claude/agents/*.md`
- Skill count from `.claude/skills/*/SKILL.md`
- Script count from `.claude/scripts/*.sh`
- Current CLAUDE.md directives
- Any quality gates in `.acos/config/quality-gates.yaml`
- Oracle configuration from `.acos/config/oracle.yaml`

Write the inventory to `.acos/state/update-baseline.yaml` with timestamp.

---

## Phase 2: RESEARCH — Parallel Intelligence Gathering

Launch **parallel research agents** using Task() to gather intelligence across
multiple domains simultaneously. Each agent returns structured findings.

**IMPORTANT:** Use `subagent_type: "general-purpose"` for all research agents.
Run them in parallel (multiple Task() calls in one message) for speed.

### Research Agent 1: Claude Code Platform Updates

Search for the latest Claude Code features, changelog entries, new hook types,
new agent capabilities, SDK updates, MCP improvements, and configuration options.

Key queries:
- "Claude Code changelog 2026"
- "Claude Code hooks documentation"
- "Claude Code agent SDK updates"
- "Claude Code new features"
- "site:code.claude.com docs"

### Research Agent 2: Vibe Coding Industry Trends

Search for developments in AI-assisted coding tools, multi-agent patterns,
context management techniques, and workflow innovations.

Key queries:
- "vibe coding techniques 2026"
- "agentic coding trends"
- "AI coding agents multi-agent"
- "context window management AI coding"
- "AI code review automation"

### Research Agent 3: Security & Quality Patterns

Search for developments in AI security scanning, automated testing,
quality gate automation, and code review patterns.

Key queries:
- "AI code security scanning 2026"
- "automated code review AI agents"
- "quality gates AI development"
- "OWASP AI coding security"

### Research Agent 4 (if $ARGUMENTS specified): Focused Research

If the user provided a focus area, launch a fourth agent that deeply researches
that specific topic with targeted queries.

---

## Phase 3: ANALYZE — Gap Identification

After all research agents return, synthesize findings into a gap analysis.

### Step 3.1: Categorize Findings

For each finding, determine:

1. **Already in ACOS** — We have this. Note if our implementation differs.
2. **Available but not adopted** — Claude Code supports it, we don't use it.
3. **Industry pattern** — A technique used by others that ACOS could benefit from.
4. **Not applicable** — Doesn't fit ACOS's architecture or principles.

### Step 3.2: Impact Assessment

For each gap (categories 2 and 3), assess:

| Factor | Scale |
|--------|-------|
| **Impact** | How much would this improve ACOS? (low / medium / high) |
| **Effort** | How much work to implement? (trivial / moderate / significant) |
| **Risk** | Could this break existing functionality? (none / low / medium / high) |
| **Urgency** | Is this blocking or time-sensitive? (low / medium / high) |

### Step 3.3: Filter by Safety

**REJECT** any change that:
- Weakens the Independence Wall (reviewer isolation)
- Removes or reduces adversarial review capabilities
- Breaks backward compatibility with existing planning artifacts
- Requires removing existing skills or agents (only adding/enhancing)
- Modifies `review-rules.yaml` (human-editable only)
- Requires untested experimental features without stable documentation

### Step 3.4: Prioritize

Rank remaining improvements by: Impact × (1/Effort) × (1/Risk) × Urgency

---

## Phase 4: PLAN — Plain-English Change Proposal

**This is the most important phase.** The output must be readable by someone with
zero knowledge of ACOS internals. No jargon. No assumptions. Every proposed change
must be self-explanatory.

### Step 4.1: Build the Change Cards

For EACH proposed improvement, create a **Change Card** using this exact format.
Use simple, everyday language. Explain like the reader has never seen the codebase.

```
╔══════════════════════════════════════════════════════════════════╗
║  CHANGE #[N]: [Short descriptive title]                        ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  WHAT IS THIS?                                                   ║
║  [2-3 sentences in plain English. What does this change do?      ║
║   No technical jargon. A non-programmer should understand this.] ║
║                                                                  ║
║  WHY SHOULD WE ADD THIS?                                         ║
║  [2-3 sentences explaining the problem this solves or the        ║
║   benefit it brings. Use concrete examples.]                     ║
║                                                                  ║
║  WHAT HAPPENS IF WE ADD IT?                                      ║
║  [Before vs After comparison. What changes in daily workflow?    ║
║   What becomes possible that wasn't before?]                     ║
║                                                                  ║
║  WHAT HAPPENS IF WE SKIP IT?                                     ║
║  [What's the cost of not doing this? Is it just a nice-to-have  ║
║   or are we missing something important?]                        ║
║                                                                  ║
║  WHAT FILES CHANGE?                                              ║
║  [List every file that will be created or modified]              ║
║                                                                  ║
║  CAN IT BREAK ANYTHING?                                          ║
║  [Honest risk assessment. "No" if truly safe. If there's any    ║
║   risk, explain what could go wrong and how we'd fix it.]        ║
║                                                                  ║
║  EFFORT: [Quick fix / A few hours / Significant work]            ║
║  RISK:   [None / Low / Medium — with explanation]                ║
║  VALUE:  [Nice-to-have / Useful / Important / Critical]          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

**Rules for writing Change Cards:**
- NO acronyms without explanation (write "hook (a script that runs automatically)" not "hook")
- NO assumed knowledge (write "the file that controls permissions" not "settings.local.json")
- Use analogies where helpful ("Like adding a security camera" vs "Adding a SubagentStart hook")
- Be honest about risks — never minimize them
- If a change is complex, break it into multiple smaller Change Cards

### Step 4.2: Group Into Tiers

Organize the Change Cards into three groups:

**SAFE & QUICK** — Changes that are simple, carry no risk, and can be done in minutes.
These are configuration tweaks, adding a single line, or enabling an existing feature.

**WORTHWHILE** — Changes that take some work but bring clear value.
Moderate effort, low risk, meaningful improvement.

**BIG MOVES** — Changes that require significant design or carry some risk.
High value but need careful implementation.

### Step 4.3: Write the Full Report

Save to `memory/decisions/acos-update-[DATE].md`:

```markdown
# ACOS Update Report — [DATE]

## What We Found
[3-5 sentence summary in plain English. What's new in the world of AI coding
that could help our system? No jargon.]

## What ACOS Already Does Well
[Brief list of things we researched that ACOS already has. Shows we're not
behind on everything — builds confidence.]

## Proposed Changes

### SAFE & QUICK
[Change Cards for this tier]

### WORTHWHILE
[Change Cards for this tier]

### BIG MOVES
[Change Cards for this tier]

### Things We Looked At But Decided Against
[For each rejected finding: one sentence on what it was, one sentence on
why we're not doing it. Transparency builds trust.]

## Rollback Safety Net
[For each approved change: how to undo it if something goes wrong.
Written so anyone can follow the steps.]
```

### Step 4.4: Present for Selection

After displaying the report, use `AskUserQuestion` with `multiSelect: true`
to let the user **pick exactly which changes they want**. List EVERY Change Card
as a selectable option grouped by tier.

Example:

```
Question: "Which improvements do you want to implement?"
multiSelect: true
Options:
  - "SAFE #1: [title] — [one-line summary]"
  - "SAFE #2: [title] — [one-line summary]"
  - "WORTH #1: [title] — [one-line summary]"
  - "WORTH #2: [title] — [one-line summary]"
  - "BIG #1: [title] — [one-line summary]"
```

If there are more than 4 changes total, use multiple AskUserQuestion calls
(max 4 options each) grouped by tier:
- First question: "Which SAFE & QUICK changes?" (multiSelect)
- Second question: "Which WORTHWHILE changes?" (multiSelect)
- Third question: "Which BIG MOVES?" (multiSelect)

**Only implement the changes the user explicitly selects.**
If the user selects "Other" with custom text, respect their instructions.

### Step 4.5: Confirm Before Starting

After selection, show a final confirmation summary:

```
You selected [N] changes to implement:
  1. [title]
  2. [title]
  3. [title]

Estimated time: [rough estimate]
Files that will be modified: [list]

Proceed with implementation?
```

Use `AskUserQuestion` with options:
- "Yes, implement all selected"
- "Let me review the list again"
- "Save the plan but don't implement yet"

---

## Phase 5: IMPLEMENT — Incremental Safe Changes

**Only execute approved changes.** Implement ONE change at a time.

### For each approved change:

#### Step 5.1: Pre-Change Verification

Before modifying anything:
- Read the file(s) to be changed
- Verify current state matches expectations
- Note the exact lines being modified (for rollback)

#### Step 5.2: Implement

Make the change. Follow existing ACOS conventions:
- Hook scripts: bash + Python stdlib only (no pip dependencies)
- Agent definitions: follow `.claude/agents/` frontmatter format
- Settings: update `.claude/settings.local.json` preserving existing structure
- Skills: follow `.claude/skills/*/SKILL.md` format

#### Step 5.3: Post-Change Verification

After each change:
- Run `bash .claude/scripts/token-gate.sh --health-check`
- If the change involved hooks: verify hook syntax with `bash -n`
- If the change involved settings.json: verify JSON is valid
- If the change involved agents: verify frontmatter is valid YAML
- Confirm the change works as intended

#### Step 5.4: Document

For each implemented change:
- Update the plan document with "IMPLEMENTED" status
- If the change is significant (new hook, new capability), create an ADR
  using `/acos-decide` with the decision context

#### Step 5.5: Gate Check

If post-change verification fails:
- **STOP implementation immediately**
- Revert the failing change
- Report the failure to the user
- Do NOT continue to the next change

---

## Phase 6: VERIFY — Full System Health Check

After all approved changes are implemented:

### Step 6.1: Run Full Health Check

```bash
bash .claude/scripts/token-gate.sh --health-check
```

Compare against the Phase 1 baseline. All existing checks must still pass.

### Step 6.2: Verify Existing Capabilities

Spot-check that existing functionality is intact:
- Oracle still evaluates correctly: `python3 .claude/scripts/oracle-evaluate.py --diagnose`
- Hook scripts are all executable: `ls -la .claude/scripts/*.sh`
- Settings JSON is valid: `python3 -c "import json; json.load(open('.claude/settings.local.json'))"`
- All agent definitions parse: check frontmatter of each `.claude/agents/*.md`

### Step 6.3: Summary Report

Present a final summary to the user:

```
=== ACOS Update Complete ===

Baseline: [X] hooks, [Y] agents, [Z] skills
Updated:  [X'] hooks, [Y'] agents, [Z'] skills

Changes implemented:
  ✓ [Change 1] — verified
  ✓ [Change 2] — verified
  ✗ [Change 3] — failed, reverted (reason)
  ○ [Change 4] — deferred to next update

Health check: PASSED
Oracle diagnose: PASSED

Next update recommended: [timeframe based on rate of change]
```

---

## Phase 7: PERSIST — Update Memory

### Step 7.1: Update MEMORY.md

Add a brief entry to the auto-memory documenting what was updated and when.
Only add entries for changes that were actually implemented and verified.

### Step 7.2: Archive Research

The research findings and gap analysis are valuable even for rejected items.
They're preserved in the plan document at `memory/decisions/acos-update-[DATE].md`.

---

## Safety Invariants

These must NEVER be violated by any update:

1. **Independence Wall** — Reviewers never see Architect decisions. Architect never sees review-rules.yaml.
2. **Adversarial Review** — All assigned reviewers must PASS. Reviews are parallel and isolated.
3. **Evidence-Based** — All work produces evidence bundles.
4. **Planning Hierarchy** — Vision > Epic > Story > Slice structure is preserved.
5. **Fail-Open Philosophy** — Missing config or errors default to allow, not crash.
6. **No PyYAML** — All scripts use Python stdlib only.
7. **Human-Editable Only** — `review-rules.yaml` and `.claude/agents/` require human approval.

---

*ACOS Update — Continuous self-improvement with safety guarantees.*
