Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `memory/handoffs/2026-08-07-emergency-handoff.yaml` for full session state.

Quick summary:
- Working on: the ACOS Logo Forge shape library, in the SEPARATE GLOBAL repo
  ~/.claude/skills (app at ~/.claude/skills/acos-logo-forge/app/). Remote
  `personal` ONLY. It is NOT part of ACOS 3.0 and is NOT OKOA work — do not
  offer to switch to OKOA work.
- Standing goal (Zee set it via /goal, still active): grow the library from 264
  by AT LEAST 2,500 new shapes, target 3,200+, ALL AUTHORED FROM SCRATCH — no
  third-party icon sets. Weight toward objects, technology, tools, buildings,
  transport, food and diagram shapes; animals/nature stylised only, capped at
  300. Batches of ~200: author, verify, RENDER EVERY SHAPE AND LOOK AT IT,
  sweep near-duplicates across ALL categories, commit. Never pad with variants.
- Last action: committed and pushed 39a90b0 — batch 03 (123 diagram shapes) plus
  a Dropper button in the Home tab's Drawing group.
- Progress: 264 -> 698 shapes. 434 of the 2,500 new-shape floor. Batch 04 next.
- Next step: READ shapes-src/AUTHORING.md FIRST, then author batch 04 into
  shapes-src/batch04.ts, then: bun build-shapes.ts -> bun shape-audit.ts ->
  bun shape-sheet.ts and LOOK AT THE IMAGE -> redraw failures -> ten suites at
  exit 0 + audit.ts 0 findings -> commit -> push personal main.
- Blockers: none.

HARD-WON FACTS THE NEXT SESSION MUST NOT REDISCOVER:
- Check the EXIT CODE, never the printed tally. Ten suites, 420 assertions.
  audit.ts and shape-audit.ts BOTH need a live server on 8816 or they exit 1
  for the wrong reason. Six suites are NOT idempotent — each needs its own
  fresh copy of "ACOS 3.0/Logo Builder/brandsync".
- DO NOT TOUCH Zee's live server, PID 43272 on port 8815. Check lsof first.
- shapes.json is a BUILD ARTIFACT. Edit shapes-src/, never the json.
- A scripted splice over shapes-src/*.ts ATE A SHAPE SILENTLY once. Always
  compare the build's per-batch count against what you intended.
- Layout guard: Clipboard group <= 113.3px (currently 112.3), Drawing group
  290.6px x 112.3px, ribbon 177.3px, Home tab 1260px of 1680, no wrap.
- Known weak, recorded not hidden: piston, pulley, pump, croissant, pretzel.
- CROSS-CONTAMINATION: an autopilot goal about "R2P EPIC-001" in
  /Users/zee/Documents/Vibe Coding/R2P keeps arriving from a DIFFERENT session.
  It is NOT this project. Stay on the Logo Forge shape library.

This prompt was auto-injected after /clear ran. The user has not typed anything
since. Read the handoff document and continue the prior work seamlessly.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `d3ee7714ce0f`
- uncommitted changes: 29 file(s)

Uncommitted working-tree files (these are in NO handoff — inspect FIRST):
```
 M .claude/scripts/_autopilot_eternity.py
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
?? memory/handoffs/2026-08-07-emergency-handoff.resume.md
?? memory/handoffs/2026-08-07-emergency-handoff.yaml
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
