Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `memory/handoffs/2026-08-06-emergency-handoff-3.yaml` for
full session state. (Other 2026-08-06 handoffs exist from OTHER tabs — use the
`-3` file.)

Quick summary:
- Working on: the GLOBAL skill ~/.claude/skills/acos-logo-forge/app/editor.html
  — a logo builder. That repo is PRIVATE and pushes to PERSONAL only
  (git@github.com-personal:ZiaulKarim-hub/claude-skills-personal.git). It is NOT
  part of ACOS 3.0. This project is entirely about logo building — do NOT offer
  to switch to OKOA work.
- Last action: commit `25c49a5` — the shape library went from 44 to 264 shapes,
  driven by a 22-agent research workflow. Before it, `dfb3a8a` added a Symbols
  tool with 2,095 symbols extracted from system fonts as REAL VECTOR PATHS
  (never <text font-family=...>, which would break on any machine lacking the
  font).
- Next step: SEVEN commits (6b1679d, 0e0eabb, b41a4f0, ad0bee3, d12a47d,
  dfb3a8a, 25c49a5) are UNPUSHED — branch is 7 ahead of personal/main, parent
  bc0d302. Zee has NOT yet said to push. Ask before pushing; do not push
  unprompted.
- Blockers: none technical.

CARRIED-FORWARD WORK ZEE WAS OFFERED AND NEVER ANSWERED — do not silently drop:
Three clipboard-image fixes were researched, reported, and never applied.
  1. A settle-guarantee in `pngBlobOfSelection()` — a decode firing neither
     onload nor onerror hangs `write()` FOREVER (measured "STILL PENDING after
     3s"; no browser deadline exists), so the button dies with no message.
  2. A `clipboardWhy(e)` helper — three different causes all print
     "NotAllowedError" today.
  3. `ribbon-test.ts`'s clipboard permission note records the symptom but draws
     the wrong conclusion. The correct grant list is
     ['clipboard-read','clipboard-sanitized-write'].

TEST POSTURE — check the EXIT CODE, never just the printed tally:
NINE suites, 381 assertions: fill 27, ribbon 178, shapes 28, forge 19,
explode 12, gallery 38, reject 17, symbols 25, button 37. `bun audit.ts` = 0
findings. Ports/workspaces: fill/ribbon/shapes/forge/explode -> 8816 with
/tmp/forge-ws; gallery/reject -> 8817 with /tmp/rej-ws AND the workspace path
passed as process.argv[2]; symbols -> 8819 with /tmp/sym-ws; button -> 8815.
SIX suites are NOT idempotent — each needs its OWN fresh copy of
"ACOS 3.0/Logo Builder/brandsync". symbols, button and explode are safe.

DO NOT TOUCH: Zee's live Logo Forge server, PID 43272 on port 8815. Run
`lsof -i :8815` before starting anything.

LAYOUT GUARD: the Clipboard ribbon group must stay <= 113.3px tall (currently
112.3). Home tab 1260px of 1680, no wrap, ribbon 177.3px.

HOW ZEE WORKS — learned this session, do not re-litigate:
- He picks icons from RENDERED comparison sheets, never from descriptions.
- A path cannot be judged from its coordinates. RENDER it and LOOK at the image.
  Sound reasoning about a tipped paint bucket produced a desk lamp.
- Twice a FAILING TEST was the test's fault, not the code's, because it asserted
  the IMPLEMENTATION instead of the REQUIREMENT. Re-anchoring made both
  STRICTER — that is the tell.
- When he asks "did you insert them?", check the thing is actually IN the app
  before reporting it done.

This prompt was auto-injected after /clear ran. The user has not typed anything
since. Read the handoff document and continue the prior work seamlessly.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `d3ee7714ce0f`
- uncommitted changes: 25 file(s)

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
?? memory/handoffs/2026-08-06-emergency-handoff.resume.md
?? memory/handoffs/2026-08-06-emergency-handoff.yaml
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
