Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `/Users/zee/Documents/Vibe Coding/ACOS 3.0/memory/handoffs/2026-08-12-emergency-handoff.yaml` in full. It was written BY HAND by the orchestrator, 14,436 bytes, because on the previous fire the handoff-agent wrote a 657-byte stub and the eternity freshness guard checks mtime only, not content.

Quick summary:
- Working on: R2P EPIC-001 in "/Users/zee/Documents/Vibe Coding/R2P" — a LOCAL-ONLY repo. NEVER push it. 15 of 24 pairs sealed; the other 9 moved a long way this session. 16 commits landed. Five holdout packs spent: 9/9, 9/9, 8/9, 7/9, 6/9.
- Last action: fired the eternity protocol at 524,332 tokens against a 500,000 threshold, with FIVE agents live.
- Next step: check disk for those five agents' banked work, then re-dispatch them fresh with exact numbered remainders.
- Blockers: none technical. All twelve ADRs remain status: proposed, awaiting Ben.

CRITICAL FIRST CHECK:
    cd "/Users/zee/Documents/Vibe Coding/R2P" && git log --oneline -8 && git status --short

FIVE AGENTS WERE LIVE AT FIRE TIME. Their context does not survive a reset, but
all five bank to disk as they go and every one was told to. Do NOT assume they
finished. Do NOT assume they did nothing. CHECK DISK FIRST, then re-dispatch
fresh with a remainder built from what is actually there:
  1. QA-001-008-03 pass 2 — pair 24 reviewer, reviewing revision 2 at 6c7bdfc
  2. QA-001-007-02 pass 3 — pair 20 reviewer, reviewing revision 3 at 2d45a03
  3. HLD-001-006-02-v1 custodian — pair 17, one-shot run UNSPENT
  4. HLD-001-007-03-v1 custodian — pair 21, one-shot run UNSPENT
  5. QA-001-007-01 pin conversion — pair 19, 3 failed | 54 passed (57)
The handoff carries each one's full brief. Items 3 and 4 are one-shot sealed
runs: establish spentness from the EVIDENCE BUNDLE (a spent pack has a
TESTRUN-*-holdout-run1.log AND a manifest.yaml), NEVER from `revealed_at`, which
is silent for 21 of 24 packs including ones demonstrably spent.

THE MUTATION GATE IS ONE RUN, NOT NINE. Pair 15's seal record shows a single
whole-codebase Stryker run read PER FILE against the 70% bar. ~2h16m55s, and it
requires ZERO agents live because stryker.config.mjs sets inPlace: true and
rewrites source. Six pairs are waiting on it.

GOALS TO CARRY FORWARD — a reset does not keep these. Restart as your first action:
- AUTOPILOT GOAL was active (session-scoped sentinel, iteration 3, max 1000). Run:
    python3 .claude/scripts/autopilot-activate.py on --goal-file "/Users/zee/Documents/Vibe Coding/R2P/docs/PRD_v0.4.txt" --max-iter 1000 "Complete the R2P project in /Users/zee/Documents/Vibe Coding/R2P to the end-state defined by docs/PRD_v0.4.txt: first finish EPIC-001 (all 24 DEV/QA pairs through the adversarial cycle - DEV, QA, holdout, orchestrator seal - then EVB-STORY bundles x8, 4-reviewer swarm review, EVB-EPIC-001, close packet), then plan and execute each subsequent PRD phase as new epics under the same adversarial cycle with sealed evidence throughout. At every epic close, present the ratification packet (ADRs, finding dispositions, disclosure queue) to Zee and continue non-dependent work (e.g. planning the next epic) while awaiting his decision. Never self-approve; never treat silence as approval; never push (local-only repo). Re-derive current position from repo state (planning/, git log) at each iteration."
- A native /goal CONDITION was also active. Run:
    /goal read `/Users/zee/Documents/Vibe Coding/ACOS 3.0/memory/handoffs/2026-08-12-emergency-handoff.yaml` first, then: complete all the slices, stories, epics and the vision for this app.

STANDING RULES, carry verbatim: R2P is LOCAL-ONLY, never push. AP-06 never weaken
a test, an invariant or a tolerance. AP-07 no agent approves, seals, closes or
ratifies anything; every finding stays pending_human_review, owner Ben; never
treat silence as approval. TypeScript only, ZERO python3 in R2P — an accidental
invocation is "one accidental, disclosed", never claimed as zero. qa-private/ is
custodian-only AND is gitignored, so an empty `git status --porcelain qa-private/`
proves nothing. Reviewers write to the MAIN checkout by ABSOLUTE path. Every YAML
needs artifact_type. macOS has no timeout; use find; `vitest -t` is a REGEX and
matching nothing exits 0. A tally with no exit code is a lie — never read $?
after a pipe to tail. `git show --stat` prints FULL commit messages and has
leaked builder narrative to two reviewers before they sealed their pre-reads;
warn every reviewer.

Agents stall at narration boundaries every 10-20 minutes. Check DISK first, then
resume with an exact numbered remainder. NEVER re-dispatch a stalled agent —
resume it. Roughly twenty stalls were handled that way this session with zero
work lost.

IMPORTANT: do not assume progress matches any summary above. Re-derive the REAL
position from R2P yourself — git log, planning/slices/, planning/evidence/ —
before continuing. ACOS 3.0's own dirty files are unrelated framework churn.

This prompt was auto-injected after a reset ran. The user has not typed anything
since. Read the handoff and continue the prior work seamlessly.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `fa1676201ad1`
- uncommitted changes: 104 file(s)

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
?? memory/handoffs/2026-08-11-emergency-handoff.resume.md
?? memory/handoffs/2026-08-11-emergency-handoff.yaml
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
