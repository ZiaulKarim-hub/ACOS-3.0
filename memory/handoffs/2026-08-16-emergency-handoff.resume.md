Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `memory/handoffs/2026-08-16-emergency-handoff.yaml` for full session state.

Quick summary:
- Working on: Eternity Protocol — migrated from cmux keystroke injection to Claude Code's own auto-compaction, plus a PreCompact/PostCompact handoff chain that restores handoff depth.
- Last action: Fixed the native-arm pane lookup in eternity-cmux-inpane.sh. It used `pgrep -f`, which silently matches NOTHING for cmux panes (their command line carries a huge --settings blob). Replaced with `ps -eo pid,command | grep`, verified live against all 9 panes. 253 checks pass across three suites, all exit 0.
- Next step: Nothing is blocked. One decision remains OPEN and is Zee's alone: six older panes still use the typed fire path because they started before the settings landed and cannot see them; only a restart moves them onto native auto-compaction. Do NOT restart anything without him saying so.
- Blockers: none.

YOUR LAST MESSAGE BEFORE THIS RESET (exact words, not a paraphrase):

  did you look at To Do Tree? I had to manually press yes for something, can you confirm that it is not something that relates to the eternity protocol.

That question WAS answered in full before this reset — do not re-investigate it.
The answer: the manual yes-press in ToDoTree was NOT related to the Eternity
Protocol. It was the Oracle (the guard that scores every command for risk)
asking about a delete command, `rm -rf` on a throwaway test folder. Four such
prompts have ever appeared in that window, all with reason `destructive_cmd +5`.
The last was at 2026-08-15T22:55:56Z, 680 seconds BEFORE that window's shrink at
23:07:16Z. ToDoTree is the one pane that shrinks itself natively; the typed
command was never sent there.

If Zee asks something new, answer that instead — the above is closed.

IMPORTANT: do not assume progress matches any summary above. Verify the REAL
state on disk before continuing.

UNTRACKED-IN-GIT RISK (flagged by the handoff agent): the two scripts this work
depends on — `.claude/scripts/precompact-handoff.ts` and
`.claude/scripts/handoff-enrich.ts` — plus the out-of-repo
`~/Library/Application Support/acos-token-monitor/bin/eternity-cmux-inpane.sh`,
are NOT committed. A clean would lose them. Backup + rollback lives at
`~/Library/Application Support/acos-token-monitor/.migration-backup-2026-08-12/rollback.sh`.

A background monitor is watching for the next auto-compaction and will report
only failures now: a summary that comes back flagged, or a handoff stuck at
"pending" because the after-shrink step did not run.

This prompt was auto-injected after a reset ran. The user has not typed anything
since. Read the handoff document and continue the prior work seamlessly.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `7f11ce2ffb40`
- uncommitted changes: 140 file(s)

Uncommitted working-tree files (these are in NO handoff — inspect FIRST):
```
 M .claude/scripts/eternity-protocol-core.sh
 M .claude/scripts/git-manager/ids.json
 M .claude/scripts/html-to-pdf.js
 M .claude/scripts/oracle-evaluate.py
 M .claude/skills/acos-eternity-protocol/SKILL.md
 M .claude/skills/acos-oracle-protocol/SKILL.md
 M .claude/skills/acos-resume-prompt/SKILL.md
 M .claude/skills/investigate/SKILL.md
 M "Logo Builder/brandsync/avoid.json"
 M "Logo Builder/brandsync/commands.jsonl"
 D "Logo Builder/brandsync/symbol/candidates/round-3/r3-04.svg"
 D "Logo Builder/brandsync/symbol/candidates/round-4/r4-02.svg"
 D "Logo Builder/brandsync/symbol/candidates/round-4/r4-04.svg"
 D "Logo Builder/brandsync/symbol/candidates/round-4/r4-06.svg"
 D "Logo Builder/brandsync/symbol/candidates/round-4/r4-09.svg"
?? .claude/scripts/_oracle_judge.py
?? .claude/scripts/handoff-enrich.ts
?? .claude/scripts/oracle/
?? .claude/scripts/precompact-handoff.ts
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
?? memory/handoffs/2026-08-16-emergency-handoff.yaml
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
```

Recent commits at fire time:
```
7f11ce2 feat(xl-update): Phase 3b — read-only email sweep across both work mailboxes
71ca4a1 feat(investigate): /investigate — the inward twin of /research, on the riff engine
fa16762 fix(research-riffs): close all three-review must-fix items; trust-chain HIGHs → SHIP-WITH-NOTES
82188f0 feat(safe-close): capture learnings across every /clear cycle, not just the closer's own memory
14343bd fix(eternity-protocol): resolve session-id/handoff selection through one shared script, not 10 copies
bf8cfda fix(autopilot/eternity): resume-prompt SKILL.md + autopilot session-scoping fixes
930b552 fix(handoff-agent): read the invoking session's own transcript first
d3ee771 fix(safe-close): zsh does not word-split $LEARN_ARG — pass --learnings-file explicitly
```

**Drift check:** if `git rev-parse --short=12 HEAD` no longer equals `7f11ce2ffb40`, or the working tree is dirty, RECONCILE from `git log` / `git status` / `git diff` before trusting any "completed / all committed" claim in the handoff above. (This session learned the hard way: a 2026-06-24 resume arrived 3 commits + 1 uncommitted method stale.)
