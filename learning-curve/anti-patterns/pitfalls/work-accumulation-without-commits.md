# Anti-Pattern: Large Work Accumulation Without Intermediate Commits

**ID:** LEARN-ANTI-003
**Extracted From:** EPIC-001 (Loan Document Generator V2)
**Date:** 2026-04-10
**Category:** anti-pattern
**Subcategory:** pitfalls
**Domain:** general
**Confidence:** high
**Occurrences:** 2

## Context

During active multi-session development where each session builds significantly on the
previous one. When work is complex and sessions are long, there is a temptation to
defer commits until a "natural stopping point." This temptation leads to large
uncommitted work accumulations.

## The Anti-Pattern

Allowing multiple sessions (days) of substantial work — new scripts, agents, skills,
and modified tracked files — to accumulate without committing. The "I'll commit when
it's more complete" reasoning creates an increasing crash-loss risk.

## Why It's Wrong

Each session handoff creates a `.yaml` file noting uncommitted work. But handoff files
are not git history. If the working tree is cleaned (accidental `git checkout .`,
corrupted local repo, machine failure), all uncommitted work is permanently lost.
The more sessions accumulate without commits, the larger the potential loss.

### Consequences

- Risk of permanent loss of all uncommitted work if working tree is wiped
- Handoff files become blockers: every new session inherits the "please commit this"
  action item, adding cognitive load
- Git history becomes misleading: large features appear as single monolithic commits
  rather than incremental steps, making debugging and rollback harder
- `git diff` becomes an unreadably large diff that's hard to review

### Root Causes

- Working tree feels "messy" during development — easier to defer than to stage
- Desire to commit only "complete" features (but features are never fully complete)
- Multi-session context: each session ends with handoff, commit gets de-prioritized
- New agents/skills feel like they need more testing before committing

## Evidence

### Incident: 2026-03-23 Session (10 days without commits)

**What Happened:**
The 2026-03-23 handoff notes: "CRITICAL: All session work is UNTRACKED/UNCOMMITTED.
No git commits since 2026-03-16 (a6b51b1). Everything built this session will be lost
if the working tree is wiped."

The uncommitted work included:
- 3 new agent definitions (fin-stmt-sandbox.md, fin-stmt-accountant.md, general-purpose.md)
- 4 new Python scripts (xlsx-extract.py, generate-chart.py, html-to-docx.py, compute-recommendation-score.py)
- 3 new complete skills (acos-financial-statement/, acos-pdf-xlsx-converter/, acos-skill-maker/)
- 13 tracked-file modifications (1076 insertions, 170 deletions across loan-doc-generator)
- 1 complete planning artifact (EPIC-001-loan-doc-generator-v2.yaml)

All of this was at risk for 7 days before eventually being committed.

**Impact:**
No actual data loss in this case. But the risk was significant — any accidental
`git checkout .` or `git clean -fd` would have lost weeks of work.

**How Discovered:**
Documented explicitly in session handoff as a CRITICAL blocker.

### Incident: 2026-03-30 Handoff (Persistent uncommitted state)

**What Happened:**
The 2026-03-30 handoff (after 5 PPTX-pipeline commits had been made) still noted
uncommitted changes to `acos-financial-statement/SKILL.md`, `acos-skill-maker/SKILL.md`,
and two untracked new skills (`acos-file-converter/`, `security-review-ultimate/`).
The uncommitted files were being carried forward session-over-session.

**Impact:**
Cognitive overhead: every session started with "remember to commit these 4 files."
The files were eventually committed but only after multiple sessions of risk exposure.

**How Discovered:**
Session handoff tracking.

## The Correct Approach

### Do This Instead

Commit at the end of every session, even if the work is incomplete. Use descriptive
`wip:` prefix for work-in-progress commits that clearly signal incompleteness.

A working incomplete commit is safer than uncommitted complete work.

**Commit cadence guidelines:**
- End of every session: commit all tracked changes and new files
- After any new script/agent/skill is created and passes basic verification
- After any swarm review remediation round (natural commit boundary)
- Before starting a new feature that touches the same files

### Why It Works

- Git commits are the only crash-safe persistent store for work in progress
- Small, frequent commits make `git bisect` and rollback trivially easy
- Handoff files focus on current state, not "don't forget to commit X"

### Example

**Wrong:**
```
# Day 1: create xlsx-extract.py (no commit)
# Day 2: create generate-chart.py (no commit)
# Day 3: create html-to-docx.py (no commit)
# Day 7: "I'll commit everything together when it's all done"
```

**Right:**
```bash
# Day 1: after creating xlsx-extract.py
git add .claude/scripts/xlsx-extract.py
git commit -m "feat: Add XLSX cell-level extraction script"

# Day 2: after creating generate-chart.py
git add .claude/scripts/generate-chart.py
git commit -m "feat: Add SVG chart generation script"
```

## Prevention Guide

### Warning Signs

- A session handoff file lists uncommitted work under "blockers" or "next_actions"
- `git status` shows more than ~5 untracked files or modified files at session start
- A next-action item says "commit X" and has appeared in 2+ consecutive handoffs

### Prevention Checklist

- [ ] At end of every session: run `git status` and commit all modified/new files
- [ ] For large new features: commit each agent/script/skill independently
- [ ] Never start a new session with uncommitted work unless it's a genuine WIP
- [ ] If work is truly incomplete: use `wip:` prefix and commit anyway

### Review Focus

For reviewers — this is a process issue, not a code review issue. But:
- Flag any handoff that lists uncommitted work as "CRITICAL" if it's been carried
  over from a previous session
- Recommend committing before proceeding with new feature work

## Related Anti-Patterns

- LEARN-ANTI-001 — Missing Data Contract Between Pipeline Stages

## Related Correct Patterns

- LEARN-WORKFLOW-001 — Scope Expansion as Additive Stories (uses commits as phase gates)

## Occurrence History

| Date | Project | Caught By | Severity |
|------|---------|-----------|----------|
| 2026-03-23 | EPIC-001 (7 days uncommitted) | Session handoff | CRITICAL |
| 2026-03-30 | EPIC-001 (persistent uncommitted skills) | Session handoff | MEDIUM |

---

*Documented to prevent recurrence - ACOS Learning Curve Agent*
