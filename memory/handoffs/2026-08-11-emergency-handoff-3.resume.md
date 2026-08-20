Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `/Users/zee/Documents/Vibe Coding/ACOS 3.0/memory/handoffs/2026-08-11-emergency-handoff-3.yaml` for full session state.

Quick summary:
- Working on: R2P EPIC-001 in "/Users/zee/Documents/Vibe Coding/R2P" — a LOCAL-ONLY repo. NEVER push it. 15 of 24 DEV/QA pairs are SEALED. Four are frozen and in review (pairs 16, 19, 20, 22). One is being built. Four are not yet started.
- Last action: fired the eternity protocol at 517,631 tokens against a 500,000 threshold, with four agents in flight.
- Next step: land those four agents, commit each as its own freeze point, then holdout -> mutation gate -> seal.
- Blockers: none technical. Seven items await Ben/Zee's ruling (listed in the handoff).

CRITICAL FIRST CHECK — do this before anything else:
    cd "/Users/zee/Documents/Vibe Coding/R2P" && git log --oneline -3 && git status --short

At fire time HEAD was 8d451f8 and the tree held three untracked pre-read files
belonging to the in-flight reviewers. Those are their blind-derivation artifacts,
written BEFORE they read the builders' answers. Do not delete them and do not
regenerate them — the ordering is what makes them evidence.

GOALS TO CARRY FORWARD — a reset does not keep these. Restart as your first action:
- A /goal CONDITION was active. Run this first:
    /goal complete all the slices, stories, epics and the vision for this app.
  There is NO autopilot sentinel for this session — the native /goal Stop hook is
  what has been driving continuation. Do not run autopilot-activate.py.

IMPORTANT: do not assume progress matches the summary above. Re-derive the real
position from the repo yourself — `git log`, `planning/slices/`, `planning/evidence/` —
before continuing. A freshly reset chat has no memory of how much was actually done.

IN-FLIGHT SUBAGENTS AT RESET TIME — four were running and had NOT returned.
DO NOT RE-DISPATCH ANY OF THEM. Their work survives a reset. Check DISK first, then
resume by message if one is idle. Re-running them duplicates or overwrites real work.

  1. QA-001-007-02 adversarial pass 1 — pair 20's FIRST review. It was built and
     committed at 7146476 but had never been reviewed; that was the biggest open gap.
     Mid-attack it found: `coefficientText` is float-free (builder's digest claim
     VERIFIED), but line 1794 compares a float for exact equality
     (`standardErrorApprox === 0`) and that comparison shapes output, while
     `ratioToNumber` can underflow. It was told to probe that cliff.
     Artifacts: planning/evidence/EVB-PAIR-001-007-02/QA-PASS1-BLIND-DERIVATION.yaml,
     and planning/slices/qa/QA-001-007-02.yaml when written.

  2. QA-001-006-01 re-verification pass 4 — re-verifying revision 3's F13/F14 fixes
     and its tagged published-figure sweep. Told to attack the INSTRUMENT first by
     running it against the rev-1 snapshot, which is known dirty.
     Artifact: planning/evidence/EVB-PAIR-001-006-01/QA-PASS4-EXPECTATIONS-PREREAD.yaml

  3. QA-001-007-01 re-verification pass 3 — re-verifying revision 3's QA2-F14 fix and
     its 22-site aggregate-collapse sweep. Told to hunt a 23rd site and to rule on
     OBS-16, which is demonstrated and NOT fixed.
     Artifact: planning/evidence/EVB-PAIR-001-007-01/QA-PASS3-EXPECTATIONS-PREREAD.yaml

  4. DEV-001-006-02 build — first of the four not-yet-started slices.
     Artifact: planning/slices/dev/DEV-001-006-02.yaml and its testruns directory.

When a tool_result for one of these arrives, do NOT discard it as orphaned. Verify
its claims on DISK rather than trusting the agent's narration, then commit it as its
own freeze point with a message recording what was verified and what was disclosed.

STANDING RULES that must not be lost:
- R2P is LOCAL-ONLY. NEVER push. Never use a bare `git push` anywhere.
- TypeScript only. ZERO python3 in R2P's own code, tests or commands. An accidental
  invocation is disclosed as "one accidental, disclosed" — never claimed as zero.
- qa-private/ is custodian-only. No DEV, QA or orchestrator reads pack content,
  the holdout harness, or holdout run logs.
- AP-06: never weaken a test, invariant or tolerance. AP-07: no agent self-approves,
  seals, closes or ratifies. All findings stay pending_human_review, owner Ben.
- The holdout runs EXACTLY once per candidate, by an independent custodian, with
  8 pack-hash checks (4 pre, 4 post).
- The mutation gate is the orchestrator's: `pnpm run test:mutation`, per-file score
  >= 70 (PRD 16.7), launched DETACHED, and the repo must stay untouched during it.
  It took 2h16m55s last time — do not under-estimate it.
- macOS has no timeout/gtimeout. zsh aborts on unmatched globs — use find.
- The environment guard fires on shell COMPOUNDING (a loop with a redirect, a pipe
  plus a status chain). NOT on ordinary code tokens and NOT on here-documents.
- qa-reviewer agents have Read + Bash and NO Write tool. They must use printf.
- Agents stall at narration boundaries constantly. Check DISK first, then send an
  exact numbered remainder checklist and say "continue in ONE pass".

This prompt was auto-injected after a reset ran. The user has not typed anything
since. Read the handoff and continue the prior work seamlessly.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `fa1676201ad1`
- uncommitted changes: 98 file(s)

Uncommitted working-tree files (these are in NO handoff — inspect FIRST):
```
 M .claude/scripts/eternity-protocol-core.sh
 M .claude/scripts/git-manager/ids.json
 M .claude/scripts/html-to-pdf.js
 M .claude/skills/acos-eternity-protocol/SKILL.md
 M .claude/skills/acos-resume-prompt/SKILL.md
 M "Logo Builder/brandsync/avoid.json"
 M "Logo Builder/brandsync/commands.jsonl"
 D "Logo Builder/brandsync/symbol/candidates/round-3/r3-04.svg"
 D "Logo Builder/brandsync/symbol/candidates/round-4/r4-02.svg"
 D "Logo Builder/brandsync/symbol/candidates/round-4/r4-04.svg"
 D "Logo Builder/brandsync/symbol/candidates/round-4/r4-06.svg"
 D "Logo Builder/brandsync/symbol/candidates/round-4/r4-09.svg"
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
?? memory/handoffs/2026-08-11-emergency-handoff-3.yaml
?? memory/handoffs/2026-08-11-emergency-handoff.resume.md
?? memory/handoffs/2026-08-11-emergency-handoff.yaml
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
?? memory/handoffs/closed/2026-08-11-Skill-Workshop-close-2/
?? memory/handoffs/closed/2026-08-11-Skill-Workshop-close-3/
?? memory/handoffs/closed/2026-08-11-Skill-Workshop-close-4/
?? memory/handoffs/closed/2026-08-11-Skill-Workshop-close/
```

Recent commits at fire time:
```
fa16762 fix(research-riffs): close all three-review must-fix items; trust-chain HIGHs → SHIP-WITH-NOTES
82188f0 feat(safe-close): capture learnings across every /clear cycle, not just the closer's own memory
14343bd fix(eternity-protocol): resolve session-id/handoff selection through one shared script, not 10 copies
bf8cfda fix(autopilot/eternity): resume-prompt SKILL.md + autopilot session-scoping fixes
930b552 fix(handoff-agent): read the invoking session's own transcript first
d3ee771 fix(safe-close): zsh does not word-split $LEARN_ARG — pass --learnings-file explicitly
aa1553d fix(resurrection): mark folder-level rows [folder] — a basename is not a name
3f73cc8 fix(resurrection): a display name that points at two rows resolves nothing
```

**Drift check:** if `git rev-parse --short=12 HEAD` no longer equals `fa1676201ad1`, or the working tree is dirty, RECONCILE from `git log` / `git status` / `git diff` before trusting any "completed / all committed" claim in the handoff above. (This session learned the hard way: a 2026-06-24 resume arrived 3 commits + 1 uncommitted method stale.)
