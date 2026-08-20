Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `/Users/zee/Documents/Vibe Coding/ACOS 3.0/memory/handoffs/2026-08-18-emergency-handoff.yaml` IN FULL before acting. Orchestrator-written (handoff-agent blocked by the 200-subagent cap), 8890 bytes, verified fresh with all content probes.

Quick summary:
- Working on: R2P at `/Users/zee/Documents/Vibe Coding/R2P`. LOCAL-ONLY, NO git remote — NEVER push. HEAD f400a06.
- THE DAY'S SHAPE: Zee ruled nearly the whole packet. Settings frozen (fd0783b). Two fixes landed through full pairs (4f5942f, 56570b2). Sealed-file correction executed under grant (f400a06). Only cards 1 (SBL-D3 label, explained, awaiting his A/B) and 2 (SBL-D4 freeze, awaiting the web-research half) remain his.
- Zee's order in force: "move to coding the next phase."
- THE BLOCKER THIS RESET CURES: the old session hit its 200-subagent cap. Four ruled production pairs waited on it. THIS fresh session has capacity — dispatch them EARLY: tasks 36 (card 4 producer — mind its stop-condition), 37 (card 5 mint check), 38 (card 6a atUtc), 40 (card 7 — specs for ALL 19 digests, Zee chose A). Also dispatch the 3 web seats for card 2 (session 2026-08-18-freeze-in-place-versus-* in ~/.acos-research, charters already rendered).
- Orchestrator-direct work also queued: task 35 (read-mutation-gate.ts tsc fix, byte-identical output proof) and task 41 (card 10 R-A: priority field + INV-001..006 marked P0 + audit re-run).

YOUR LAST MESSAGE BEFORE THIS RESET (exact words, not a paraphrase):

  now that all the decisions are resolved, please move to coding the next phase.

I had corrected the premise (cards 1 and 2 still open, held by Zee himself) and started coding: card 6b done, then this reset fired. Continue the coding order in the handoff's current_work.

GOALS TO CARRY FORWARD — a reset does not keep these; restart as your very first action:
  - AUTOPILOT GOAL was active (max 1000). Run this first:
      python3 .claude/scripts/autopilot-activate.py on "Complete the R2P project in /Users/zee/Documents/Vibe Coding/R2P to the end-state defined by docs/PRD_v0.4.txt: first finish EPIC-001 (all 24 DEV/QA pairs through the adversarial cycle - DEV, QA, holdout, orchestrator seal - then EVB-STORY bundles x8, 4-reviewer swarm review, EVB-EPIC-001, close packet), then plan and execute each subsequent PRD phase as new epics under the same adversarial cycle with sealed evidence throughout. At every epic close, present the ratification packet (ADRs, finding dispositions, disclosure queue) to Zee and continue non-dependent work (e.g. planning the next epic) while awaiting his decision. Never self-approve; never treat silence as approval; never push (local-only repo). Re-derive current position from repo state (planning/, git log) at each iteration." --goal-file "/Users/zee/Documents/Vibe Coding/R2P/docs/PRD_v0.4.txt" --max-iter 1000

STANDING CONSTRAINTS: AP-06 never weaken a test/invariant/tolerance. AP-07 no agent approves/seals/closes/ratifies; silence is never approval; Zee IS the gate ("Ben" is the PRD role name). Records ADDITIVE — supersede by SIBLING. NEVER AskUserQuestion for rulings while autopilot is active (OBS-AP1). Forbidden score levers per the frozen sheet. TS/Rust only. Scoped git add; read the staged list first. Never tsc during a live stryker run. Eden level 4 — gloss DOMAIN words, orient before every ruling (this unlocked 12+ rulings; keep it). reports/ is gitignored; evidence copies go task-stamped with sha256.

IMPORTANT: do not assume progress matches any summary above. Verify the REAL state on disk first (R2P git log; git status; the task list) before continuing. A freshly reset chat has no memory of how much was done — trust the disk.

This prompt was auto-injected after a reset. The user has not typed anything since.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `66b7b71a11f2`
- uncommitted changes: 157 file(s)

Uncommitted working-tree files (these are in NO handoff — inspect FIRST):
```
 M .claude/scripts/eternity-protocol-core.sh
 M .claude/scripts/git-manager/ids.json
 M .claude/scripts/html-to-pdf.js
 M .claude/scripts/oracle-evaluate.py
 M .claude/skills/acos-eternity-protocol/SKILL.md
 M .claude/skills/acos-resume-prompt/SKILL.md
 M .claude/skills/investigate/SKILL.md
 M "Logo Builder/brandsync/avoid.json"
 M "Logo Builder/brandsync/commands.jsonl"
 D "Logo Builder/brandsync/symbol/candidates/round-3/r3-04.svg"
 D "Logo Builder/brandsync/symbol/candidates/round-4/r4-02.svg"
 D "Logo Builder/brandsync/symbol/candidates/round-4/r4-04.svg"
 D "Logo Builder/brandsync/symbol/candidates/round-4/r4-06.svg"
 D "Logo Builder/brandsync/symbol/candidates/round-4/r4-09.svg"
?? .claude/scripts/handoff-enrich.ts
?? .claude/scripts/precompact-handoff.ts
?? .claude/scripts/tests/test_oracle_hard_blocks.py
?? .claude/skills/investigate/templates/researcher-charter.md
?? .claude/skills/research/
?? "Logo Builder/brandsync/symbol/rejected/round-3/"
?? "Logo Builder/brandsync/symbol/rejected/round-4/r4-02.svg"
?? "Logo Builder/brandsync/symbol/rejected/round-4/r4-04.svg"
?? "Logo Builder/brandsync/symbol/rejected/round-4/r4-06.svg"
?? "Logo Builder/brandsync/symbol/rejected/round-4/r4-09.svg"
?? memory/decisions/2026-08-10-communication-tracker-privilege-policy.md
?? memory/handoffs/.harvested/
?? memory/handoffs/2026-08-05-emergency-handoff-2.yaml
?? memory/handoffs/2026-08-06-emergency-handoff-2.resume.md
?? memory/handoffs/2026-08-06-emergency-handoff-2.yaml
?? memory/handoffs/2026-08-06-emergency-handoff-3.resume.md
?? memory/handoffs/2026-08-06-emergency-handoff-3.yaml
?? memory/handoffs/2026-08-06-emergency-handoff-4.resume.md
?? memory/handoffs/2026-08-06-emergency-handoff-4.yaml
?? memory/handoffs/2026-08-06-emergency-handoff-5.resume.md
?? memory/handoffs/2026-08-06-emergency-handoff-5.yaml
?? memory/handoffs/2026-08-06-emergency-handoff.resume.md
?? memory/handoffs/2026-08-06-emergency-handoff.yaml
?? memory/handoffs/2026-08-07-emergency-handoff-2.resume.md
?? memory/handoffs/2026-08-07-emergency-handoff-2.yaml
?? memory/handoffs/2026-08-07-emergency-handoff.resume.md
?? memory/handoffs/2026-08-07-emergency-handoff.yaml
?? memory/handoffs/2026-08-08-emergency-handoff-2.resume.md
?? memory/handoffs/2026-08-08-emergency-handoff-2.yaml
?? memory/handoffs/2026-08-08-emergency-handoff-3.yaml
?? memory/handoffs/2026-08-08-emergency-handoff-4.resume.md
?? memory/handoffs/2026-08-08-emergency-handoff-4.yaml
?? memory/handoffs/2026-08-08-emergency-handoff-5.resume.md
?? memory/handoffs/2026-08-08-emergency-handoff-5.yaml
?? memory/handoffs/2026-08-08-emergency-handoff-6.resume.md
?? memory/handoffs/2026-08-08-emergency-handoff-6.yaml
?? memory/handoffs/2026-08-08-emergency-handoff.resume.md
?? memory/handoffs/2026-08-08-emergency-handoff.yaml
?? memory/handoffs/2026-08-09-emergency-handoff-2.yaml
?? memory/handoffs/2026-08-09-emergency-handoff-3.resume.md
?? memory/handoffs/2026-08-09-emergency-handoff-3.yaml
?? memory/handoffs/2026-08-09-emergency-handoff-4.resume.md
?? memory/handoffs/2026-08-09-emergency-handoff-4.yaml
?? memory/handoffs/2026-08-09-emergency-handoff-5.resume.md
?? memory/handoffs/2026-08-09-emergency-handoff-5.yaml
?? memory/handoffs/2026-08-09-emergency-handoff.resume.md
?? memory/handoffs/2026-08-09-emergency-handoff.yaml
?? memory/handoffs/2026-08-10-emergency-handoff-2.resume.md
?? memory/handoffs/2026-08-10-emergency-handoff-2.yaml
?? memory/handoffs/2026-08-10-emergency-handoff-3.resume.md
?? memory/handoffs/2026-08-10-emergency-handoff-3.yaml
?? memory/handoffs/2026-08-10-emergency-handoff-4.resume.md
?? memory/handoffs/2026-08-10-emergency-handoff-4.yaml
?? memory/handoffs/2026-08-10-emergency-handoff.resume.md
?? memory/handoffs/2026-08-10-emergency-handoff.yaml
?? memory/handoffs/2026-08-11-emergency-handoff-2.resume.md
?? memory/handoffs/2026-08-11-emergency-handoff-2.yaml
?? memory/handoffs/2026-08-11-emergency-handoff-3.resume.md
?? memory/handoffs/2026-08-11-emergency-handoff-3.yaml
?? memory/handoffs/2026-08-11-emergency-handoff-4.resume.md
?? memory/handoffs/2026-08-11-emergency-handoff-4.yaml
?? memory/handoffs/2026-08-11-emergency-handoff-5.resume.md
?? memory/handoffs/2026-08-11-emergency-handoff-5.yaml
?? memory/handoffs/2026-08-11-emergency-handoff.resume.md
?? memory/handoffs/2026-08-11-emergency-handoff.yaml
?? memory/handoffs/2026-08-12-emergency-handoff-2.resume.md
?? memory/handoffs/2026-08-12-emergency-handoff-2.yaml
?? memory/handoffs/2026-08-12-emergency-handoff-3.resume.md
?? memory/handoffs/2026-08-12-emergency-handoff-3.yaml
?? memory/handoffs/2026-08-12-emergency-handoff-4.resume.md
?? memory/handoffs/2026-08-12-emergency-handoff-4.yaml
?? memory/handoffs/2026-08-12-emergency-handoff-5.resume.md
?? memory/handoffs/2026-08-12-emergency-handoff-5.yaml
?? memory/handoffs/2026-08-12-emergency-handoff.resume.md
?? memory/handoffs/2026-08-12-emergency-handoff.yaml
?? memory/handoffs/2026-08-13-autocompact-handoff-2.yaml
?? memory/handoffs/2026-08-13-autocompact-handoff.yaml
?? memory/handoffs/2026-08-14-autocompact-handoff.yaml
?? memory/handoffs/2026-08-16-emergency-handoff.resume.md
?? memory/handoffs/2026-08-16-emergency-handoff.yaml
?? memory/handoffs/2026-08-17-autocompact-handoff-2.yaml
?? memory/handoffs/2026-08-17-autocompact-handoff-3.yaml
?? memory/handoffs/2026-08-17-autocompact-handoff.yaml
?? memory/handoffs/2026-08-17-emergency-handoff-2.resume.md
?? memory/handoffs/2026-08-17-emergency-handoff-2.yaml
?? memory/handoffs/2026-08-17-emergency-handoff-3.resume.md
?? memory/handoffs/2026-08-17-emergency-handoff-3.yaml
?? memory/handoffs/2026-08-17-emergency-handoff.resume.md
?? memory/handoffs/2026-08-17-emergency-handoff.yaml
?? memory/handoffs/2026-08-18-autocompact-handoff.yaml
?? memory/handoffs/2026-08-18-emergency-handoff.yaml
?? memory/handoffs/closed/2026-07-21-OKOA-Works-close/.reentry-consumed
?? memory/handoffs/closed/2026-07-22-OKOA-Works-close/.reentry-consumed
?? memory/handoffs/closed/2026-07-26-OKOA-Works-close/.reentry-consumed
?? memory/handoffs/closed/2026-07-28-OKOA-Works-close/.reentry-consumed
?? memory/handoffs/closed/2026-08-02-OKOA-Works-close/.reentry-consumed
?? memory/handoffs/closed/2026-08-04-OKOA-Works-close/.reentry-consumed
?? memory/handoffs/closed/2026-08-05-OKOA-Works-close-2/
?? memory/handoffs/closed/2026-08-05-OKOA-Works-close/
?? memory/handoffs/closed/2026-08-05-Resurrection-Protocol-close/
?? memory/handoffs/closed/2026-08-06-OKOA-Works-close-2/
?? memory/handoffs/closed/2026-08-06-OKOA-Works-close/
?? memory/handoffs/closed/2026-08-06-Resurrection-Protocol-close/
?? memory/handoffs/closed/2026-08-07-OKOA-Works-close-2/
?? memory/handoffs/closed/2026-08-07-OKOA-Works-close/
?? memory/handoffs/closed/2026-08-08-Skill-Workshop-close-2/
?? memory/handoffs/closed/2026-08-08-Skill-Workshop-close/
?? memory/handoffs/closed/2026-08-09-Skill-Workshop-close-2/
?? memory/handoffs/closed/2026-08-09-Skill-Workshop-close/
?? memory/handoffs/closed/2026-08-10-OKOA-Works-close-2/
?? memory/handoffs/closed/2026-08-10-OKOA-Works-close-3/
?? memory/handoffs/closed/2026-08-10-OKOA-Works-close-4/
?? memory/handoffs/closed/2026-08-10-OKOA-Works-close/
?? memory/handoffs/closed/2026-08-10-Research-Riffs-close-2/
?? memory/handoffs/closed/2026-08-10-Research-Riffs-close/
?? memory/handoffs/closed/2026-08-10-Skill-Workshop-close-2/
?? memory/handoffs/closed/2026-08-10-Skill-Workshop-close/
?? memory/handoffs/closed/2026-08-11-OKOA-Works-close-2/
?? memory/handoffs/closed/2026-08-11-OKOA-Works-close/
?? memory/handoffs/closed/2026-08-11-Skill-Workshop-close-2/
?? memory/handoffs/closed/2026-08-11-Skill-Workshop-close-3/
?? memory/handoffs/closed/2026-08-11-Skill-Workshop-close-4/
?? memory/handoffs/closed/2026-08-11-Skill-Workshop-close/
?? memory/handoffs/closed/2026-08-12-OKOA-Works-close-2/
?? memory/handoffs/closed/2026-08-12-OKOA-Works-close-3/
?? memory/handoffs/closed/2026-08-12-OKOA-Works-close-4/
?? memory/handoffs/closed/2026-08-12-OKOA-Works-close/
?? memory/handoffs/closed/2026-08-13-Skill-Workshop-close-2/
?? memory/handoffs/closed/2026-08-13-Skill-Workshop-close/
?? memory/handoffs/closed/2026-08-14-OKOA-Works-close-2/
?? memory/handoffs/closed/2026-08-14-OKOA-Works-close/
?? memory/handoffs/closed/2026-08-15-OKOA-Works-close-2/
?? memory/handoffs/closed/2026-08-15-OKOA-Works-close-3/
?? memory/handoffs/closed/2026-08-15-OKOA-Works-close-4/
?? memory/handoffs/closed/2026-08-15-OKOA-Works-close/
?? memory/handoffs/closed/2026-08-15-Skill-Workshop-close-2/
?? memory/handoffs/closed/2026-08-15-Skill-Workshop-close/
?? memory/handoffs/closed/2026-08-17-OKOA-Works-close-2/
?? memory/handoffs/closed/2026-08-17-OKOA-Works-close/
?? memory/handoffs/closed/2026-08-17-Skill-Workshop-close-2/
?? memory/handoffs/closed/2026-08-17-Skill-Workshop-close-3/
?? memory/handoffs/closed/2026-08-17-Skill-Workshop-close-4/
?? memory/handoffs/closed/2026-08-17-Skill-Workshop-close/
```

Recent commits at fire time:
```
66b7b71 fix(riffs): a half-installed charter overlay throws instead of aiming panel seats at the web
9367960 feat(oracle): a missing goal asks instead of refusing
ee8be86 feat(oracle): a real AI at the permission door — four settings, one ever on
7f11ce2 feat(xl-update): Phase 3b — read-only email sweep across both work mailboxes
71ca4a1 feat(investigate): /investigate — the inward twin of /research, on the riff engine
fa16762 fix(research-riffs): close all three-review must-fix items; trust-chain HIGHs → SHIP-WITH-NOTES
82188f0 feat(safe-close): capture learnings across every /clear cycle, not just the closer's own memory
14343bd fix(eternity-protocol): resolve session-id/handoff selection through one shared script, not 10 copies
```

**Drift check:** if `git rev-parse --short=12 HEAD` no longer equals `66b7b71a11f2`, or the working tree is dirty, RECONCILE from `git log` / `git status` / `git diff` before trusting any "completed / all committed" claim in the handoff above. (This session learned the hard way: a 2026-06-24 resume arrived 3 commits + 1 uncommitted method stale.)
