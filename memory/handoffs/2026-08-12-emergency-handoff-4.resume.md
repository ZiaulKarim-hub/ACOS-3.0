Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `/Users/zee/Documents/Vibe Coding/ACOS 3.0/memory/handoffs/2026-08-12-emergency-handoff-4.yaml` in full before acting. It was written this fire, verified fresh and parseable (16 keys).

Quick summary:
- Working on: R2P at `/Users/zee/Documents/Vibe Coding/R2P`. LOCAL-ONLY — NEVER push. 23 commits this session, none pushed. The transcript is filed under ACOS 3.0 but essentially ALL the work is in R2P; do not let a disk heuristic mis-scope this.
- Last action: started ONE whole-codebase mutation run (the PRD 16.7 gate) at 2026-08-12T11:17:55, pid 5918, detached, HEAD 0380537.
- Next step: DO NOTHING that touches the repo until that run finishes. See the hazard below.
- Blockers: three rulings that only Ben can make, plus the run.

>>> READ THIS BEFORE ANY TOOL CALL <<<
A STRYKER MUTATION RUN IS PROBABLY STILL LIVE. Check first:
    pgrep -f stryker | wc -l
    tail -1 "/Users/zee/Documents/Vibe Coding/R2P/planning/evidence/EVB-EPIC-001/close-packet/testruns/GATE-RERUN-latest.log"
WHILE IT IS LIVE:
  - Do NOT run tsc, vitest, biome or `pnpm run check`, and do NOT dispatch any agent that would. `inPlace: true` has prepended `// @ts-nocheck` to hundreds of files, so a type check reports SUCCESS regardless of real errors. That is a FALSE PASS — worse than a false failure, because nothing signals it.
  - Do NOT edit ANY file. The run restores what it instrumented; an edit now could be wiped or break the restore.
  - `git status` in R2P is MEANINGLESS right now. A long list of modified files under packages/ is instrumentation, NOT uncommitted work. Files outside the declared globs are instrumented too: tools/mutation-gate-rerun.ts, vitest.config.ts, stryker.config.mjs.
  - Two watcher shell jobs were armed (7.5h and 13h windows). They may or may not have survived the compaction — verify rather than assume. At the observed pace the run may outlast both. If neither is alive, re-arm one that polls for the line `RUN_EXIT=` in that log AND separately reports "processes gone with no exit code" as a CRASH, not a finish.

WHEN THE RUN LANDS, in this order:
  1. FIRST: did `packages/core/allocation/index.ts` and `packages/core/portfolio/index.ts` move off 0.00? That one reading settles both whether their new tests were collected AND a 10-test discrepancy recorded in OBS-MG14 ADDENDUM-1.
  2. `bun tools/mutation-gate-rerun.ts --report <log>` and read the table PER FILE against 70. NOT the run's exit code — `break: 70` applies to the AGGREGATE, so a run can exit 0 while individual files fail.
  3. Compare per-file mutant counts against `testruns/GATE-PREFIX-BASELINE-PARSED-from-full-run.json` to locate an UNEXPLAINED +73 mutant delta (30413 -> 30486 with no production source change). It is recorded as unexplained on purpose; do not invent a cause.
  4. Re-measure the full suite. Nothing has measured it since today's changes, and a stale PASS was already downgraded to unverified in SWARM-001-DESIGN ADDENDUM-1.
  5. Send ONE builder to answer the open BLOCK on `tests/unit/presentation-export-parity-contracts.test.ts` — two comment claims, no assertions.

WHERE TO START READING: `planning/evidence/EVB-EPIC-001/close-packet/READ-THIS-FIRST-SESSION-2026-08-12.yaml`.

THE THREE RULINGS WAITING ON BEN (a builder is idle on the first):
  1. compareManifestIdentity never consults the mint register while the module comment says every trusted-witness entry point does. Two forgeries can be compared and get a verdict. Fix the code or fix the comment — no test is true under both.
  2. A prior-cycle resolution is never checked for legality, so a break that was never legally owned can still be closed. Intended, or a bug? If a bug, what happens to breaks already closed?
  3. No digest in the codebase has a written format spec (19 functions, 13 files, only 6 reviewed, 7 never examined). Write specs, relabel every mirror honestly, or specify only cross-node digests.

GOALS TO CARRY FORWARD — a reset does not keep these; restart it yourself as your FIRST action:
  - AUTOPILOT GOAL was active. Run this first:
      python3 .claude/scripts/autopilot-activate.py on "Complete the R2P project in /Users/zee/Documents/Vibe Coding/R2P to the end-state defined by docs/PRD_v0.4.txt: first finish EPIC-001 (all 24 DEV/QA pairs through the adversarial cycle - DEV, QA, holdout, orchestrator seal - then EVB-STORY bundles x8, 4-reviewer swarm review, EVB-EPIC-001, close packet), then plan and execute each subsequent PRD phase as new epics under the same adversarial cycle with sealed evidence throughout. At every epic close, present the ratification packet (ADRs, finding dispositions, disclosure queue) to Zee and continue non-dependent work (e.g. planning the next epic) while awaiting his decision. Never self-approve; never treat silence as approval; never push (local-only repo). Re-derive current position from repo state (planning/, git log) at each iteration." --goal-file /Users/zee/Documents/Vibe Coding/R2P/docs/PRD_v0.4.txt --max-iter 1000

YOUR LAST MESSAGE BEFORE THIS RESET (exact words, not a paraphrase):

  of course until all the tests pass, i can't declare anything complete, you have to keep reiterating. Is there anythign specific that you need my input on? Somthing that is broken or doesn't make sense?

That was ANSWERED before the reset: three rulings needed, plus two things that do not make sense — the P0 rule that has nothing to check (43 slice files cite it, ZERO mark any invariant P0, so that gate can neither pass nor fail), and two exported functions with no callers anywhere. Do not re-answer it from scratch; check whether Zee has since replied.

STANDING RULES — do not relearn these the hard way:
  - AP-06: never weaken a test, an invariant or a tolerance.
  - AP-07: no agent approves, seals, closes or ratifies anything. Every record reads `owner: Ben`. Silence is NOT approval.
  - Records are ADDITIVE: supersede with a SIBLING key, never edit or delete prior text.
  - Scoped `git add` only, and READ THE STAGED LIST BEFORE WRITING THE COMMIT MESSAGE.
  - Never `git show --stat` or `git log --oneline` on a pair's commit near a reviewer — commit messages here carry both builder narrative AND reviewer verdicts.
  - macOS has no `timeout`/`gtimeout`. zsh does not word-split unquoted parameters. The repo path contains a SPACE. Never read `$?` after a pipe. `vitest -t` is a REGEX and matching nothing exits 0 — check the COUNT.
  - Grepping a long numeric literal by its bare digits MISSES separator-formatted copies (`9_007_199_254_740_991`). This produced a real false "absent" call today.
  - `pgrep -f "...biome"` matches the macOS daemons `biomed` and `biometrickitd`. Match install paths, not bare words.

IMPORTANT: do not assume progress matches this summary. Verify the real state on disk first — `pgrep -f stryker`, the gate log's last line, `git log --oneline -5` in R2P — before continuing.

This prompt was auto-injected after a reset ran. The user has not typed anything since.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `fa1676201ad1`
- uncommitted changes: 113 file(s)

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
?? memory/handoffs/2026-08-12-emergency-handoff.resume.md
?? memory/handoffs/2026-08-12-emergency-handoff.yaml
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
