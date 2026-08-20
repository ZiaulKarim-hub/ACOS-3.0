Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `/Users/zee/Documents/Vibe Coding/ACOS 3.0/memory/handoffs/2026-08-06-emergency-handoff.yaml` for full session state.

FOLDER TRAP — READ BEFORE ANY FILE OPERATION: your shell cwd is
"/Users/zee/Documents/Vibe Coding/ACOS 3.0" but ALL work is in the SEPARATE repo
"/Users/zee/Documents/Vibe Coding/FruitSync" (Unity 6 C# fruit-merge game).
Use ABSOLUTE paths under the FruitSync root for every read, edit and git command.

Quick summary:
- Working on: an 11-item change list for FruitSync — burned-fruit phase, economy
  retune, save/score rules, and per-level instructions. 10 of 12 tracked tasks done.
- Last action: finished the sell-items feature and the LevelGuide core + tests;
  suite at 201 passing, exit code 0.
- Next step: finish task 10 — add the Loc.cs entries for every
  level_title_N / level_about_N / level_next_N / level_anim_N / help_tool_* /
  help_power_* key that Assets/Scripts/Core/Lifecycle/LevelGuide.cs already looks
  up, then build the HUD panel in Assets/Scripts/Unity/HudView.cs that shows them
  with the short per-level animation. Then task 12: a runId debug readout and an
  in-editor blast-radius preview.
- Blockers:
  1. Autopilot never runs. autopilot-stop-handler.py stands down whenever ANY
     .compact-fired-* / .clear-requested-* marker exists in
     ~/Library/Application Support/acos-token-monitor/state/. 10 stale markers
     sit there, oldest Jun 15; the blocking one belongs to a DIFFERENT session.
     Fix is NOT applied and needs the user: move foreign markers to consumed/.
  2. Left-side "cushion" visual issue: no physics bug found (physics is
     mood-blind). Leading theory is the darker angry rim. UNCONFIRMED, needs a repro.
  3. Unity-tree compile risk: the .NET test mirror compiles Assets/Scripts/Core
     ONLY. Nine files under Assets/Scripts/Unity were edited and are NOT
     compile-verified. Open Unity to confirm they build. Sell-button positions in
     HudView.cs were placed by arithmetic, never seen rendered.
  4. dotnet is not on PATH. Every test run needs, from
     /Users/zee/Documents/Vibe Coding/FruitSync/build/dotnet:
       export DOTNET_ROOT=$HOME/.dotnet && export PATH=$HOME/.dotnet:$PATH
       dotnet test FruitSync.Core.Tests/FruitSync.Core.Tests.csproj
     ALWAYS check the real exit code, never just the printed tally.

FruitSync is a PERSONAL repo (github.com/ZiaulKarim-hub/FruitSync). NEVER push it
to the okoateam account. All changes are uncommitted in the working tree.

This prompt was auto-injected after /clear ran. The user has not typed anything
since. Read the handoff document and continue the prior work seamlessly.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `d3ee7714ce0f`
- uncommitted changes: 15 file(s)

Uncommitted working-tree files (these are in NO handoff — inspect FIRST):
```
 M "Logo Builder/brandsync/commands.jsonl"
?? memory/handoffs/2026-08-05-emergency-handoff-2.yaml
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
