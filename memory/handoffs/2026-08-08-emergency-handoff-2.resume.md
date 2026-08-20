Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `memory/handoffs/2026-08-08-emergency-handoff-2.yaml` for full
session state, the VERBATIM standing /goal text, and the durable lessons list.

*** VERIFY THE COUNT FIRST — THIS NOTE HAS BEEN STALE THREE TIMES. ***
Before authoring anything, run:
  git -C ~/.claude/skills log --oneline -3
  git -C ~/.claude/skills status --short acos-logo-forge/
  bun -e 'console.log(JSON.parse(require("fs").readFileSync(process.env.HOME+"/.claude/skills/acos-logo-forge/app/shapes.json","utf8")).length)'

- Working on: the ACOS Logo Forge shape library, in the SEPARATE GLOBAL repo
  ~/.claude/skills (app at ~/.claude/skills/acos-logo-forge/app/). Branch main,
  remote `personal` ONLY. NOT the ACOS 3.0 repo, NOT OKOA work — never offer to
  switch to OKOA work.
- Last action: batch 17 finished all eight goal steps. Ten suites exit 0 (420
  assertions), audit.ts 0 findings, shape-audit.ts 0 failures / 3 pre-existing
  warnings. Batch 17 ships 38 shapes.
- State at clear time (VERIFY, do not trust): 1,277 shapes = 264 base + 1,013
  authored. Floor 2,500 authored (2,764 total); target 3,200+. HEAD 900a7b6.
  Batches 16 (39 shapes) and 17 (38 shapes) are COMPLETE but UNCOMMITTED ON
  PURPOSE — goal step 8 forbids commit and push.
  Uncommitted: shapes-src/batch16.ts, shapes-src/batch17.ts, shapes.json.
  The same repo also holds UNRELATED dirty files (acos-okoa-works,
  acos-create-skill, and untracked acos-communication-tracker/,
  acos-deal-summary/, acos-payoff-letter/). NEVER stage those.
- Next step: report batches 16 and 17 to Zee and WAIT. Do NOT commit, do NOT
  push, do NOT start batch 18 unprompted — goal step 8 is literal. If Zee asks
  for batch 18, start at goal step 1 (name-check before drawing).
- Blockers: none.

DO NOT REDISCOVER (all also in shapes-src/AUTHORING.md):
- EXIT CODE, never the printed tally — a suite that dies mid-run still prints "N/N passed".
- Suite ports differ: fill/ribbon/shapes/forge/explode/shapelib/button = 8816;
  symbols = 8819; gallery + reject = 8817 AND take an ABSOLUTE workspace path as
  argv[2]. Six suites are NOT idempotent and need a fresh brandsync copy each.
- NEVER touch Zee's live server, PID 43272 on port 8815 — lsof first.
- shapes.json is a BUILD ARTIFACT. Edit shapes-src/, never the json.
- build-shapes.ts SORTS; "the last N records" is NOT the batch you wrote.
- WINDING (AUTHORING cause 5): C()/E() wind anticlockwise, L() takes its own
  direction, R()/P()/NGON()/STAR()/TRAP()/WEDGE()/ARCBAND() are clockwise.
  Opposite windings CANCEL under plain nonzero fill — a silent hole with no e:1.
  Do not use L() or PL().
- REDRAWING FIXES A FAULT, NOT A COLLISION. If a shape reads as another NAMED
  shape, cut it.
- COUNT FORMS, NOT NAMES, WHILE DRAFTING. Batch 17 collided with itself: four
  domes, three triangles, three guns.
- EDEN PROTOCOL is active at Level 3 — chat replies in plain middle-school
  language, every number verbatim, every caveat kept.

This prompt was auto-injected after /clear ran. The user has not typed anything
since. Read the handoff document and continue the prior work seamlessly.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `d3ee7714ce0f`
- uncommitted changes: 39 file(s)

Uncommitted working-tree files (these are in NO handoff — inspect FIRST):
```
 M .claude/scripts/_autopilot_eternity.py
 M .claude/scripts/autopilot-activate.py
 M .claude/scripts/autopilot-context-injector.py
 M .claude/scripts/autopilot-stop-handler.py
 M .claude/scripts/git-manager/ids.json
 M .claude/scripts/html-to-pdf.js
 M "Logo Builder/brandsync/commands.jsonl"
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
?? memory/handoffs/2026-08-08-emergency-handoff-2.yaml
?? memory/handoffs/2026-08-08-emergency-handoff.resume.md
?? memory/handoffs/2026-08-08-emergency-handoff.yaml
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
```

Recent commits at fire time:
```
d3ee771 fix(safe-close): zsh does not word-split $LEARN_ARG — pass --learnings-file explicitly
aa1553d fix(resurrection): mark folder-level rows [folder] — a basename is not a name
3f73cc8 fix(resurrection): a display name that points at two rows resolves nothing
092fcb8 feat(resurrection): MW-E touch feeder + auto project resolution
ef22b3e chore: save the 2026-08-03 through 2026-08-05 session handoffs
275989d feat(resurrection): per-project knowledge base + multi-window support
0deaf79 chore(git-manager): withdraw the Rubin bundle do-not-track ruling
5bc4c8f chore: save the 2026-08-03 session handoffs
```

**Drift check:** if `git rev-parse --short=12 HEAD` no longer equals `d3ee7714ce0f`, or the working tree is dirty, RECONCILE from `git log` / `git status` / `git diff` before trusting any "completed / all committed" claim in the handoff above. (This session learned the hard way: a 2026-06-24 resume arrived 3 commits + 1 uncommitted method stale.)
