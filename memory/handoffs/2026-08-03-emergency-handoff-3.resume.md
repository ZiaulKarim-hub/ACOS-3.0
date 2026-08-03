Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `/Users/zee/Documents/Vibe Coding/ACOS 3.0/memory/handoffs/2026-08-03-emergency-handoff-3.yaml` for full session state.
(The sibling file `...-2.yaml` is a 467-byte STUB the handoff-agent failed to enrich — ignore it.)

Quick summary:
- Working on: /acos-git-manager — a backup sweep of every project on the machine, plus three rounds of feature work on the git-manager tool itself. Untracked folders went 7 -> 3; safe repos 16 -> 33. Everything pushed to PERSONAL (ZiaulKarim-hub), private.
- Last action: fixed a FALSE-ALARM bug found at handoff time. otherBranchWork() asked whether `<remote>/<branch>` exists; when absent it counted the whole branch as unprotected. That wrongly reported STEPS `fix/archived-tasks-safe` as 26 lost commits and OKOA Website/dev `main` as 1 — both are fully reachable from pushed personal branches. New G.commitsOnNoRemoteRef() asks the honest question. Need-attention fell 8 -> 2.
- Next step: COMMIT AND PUSH the uncommitted git-manager work to personal. Stage BY EXACT PATH — other live sessions share the ACOS 3.0 working tree.
    .claude/scripts/git-manager/{types,scan,recommend,render-terminal,render-html,git}.ts
    .claude/scripts/git-manager/README.md
    memory/handoffs/2026-08-03-emergency-handoff-{2,3}.yaml
    and separately: ~/.claude/skills/acos-git-manager/SKILL.md  (repo: claude-skills-personal)
- Blockers:
    1. handoff-agent writes a 467-byte stub and never enriches — TWICE in a row now. Author handoffs from the main thread.
    2. `gh repo create` uses whichever GitHub account is ACTIVE, and it DRIFTS. Always run `gh api user --jq '.login'` first.
    3. Other live sessions are editing acos-axiom-synthesis, acos-logo-forge and acos-research-riffs in the same tree. Never `git add -A` in ACOS 3.0.

Still open, all offered to Zee with no answer yet:
- /Users/zee/Documents/private_credit_design_reference (NOT the OKOA copy) is the fuller one — it holds the 6 renderer files the OKOA copy lacks. Outside the scan roots, so the report never sees it. Still unbacked. 67 keepable files, 22.0M.
- SEO Plan/Blog/README.md still says "no remote… nothing here is pushed anywhere". That is now false.
- 8 optional pushes available: 6 to okoateam (work), 2 to OKOA-Labs. Zee has NOT named the work account — do not push them.

Running in the background: the live git-manager page at http://127.0.0.1:8787/ (read-only). Stop with: pkill -f "git-manager.ts serve"
Note: a long-running serve holds the code it started with, so restart it after any code change or the page shows stale behaviour.

Eden Protocol Level 2 is active: plain high-school-level replies, 22-word sentence cap, gloss every term on first use, every number verbatim, keep every caveat, end with ONE action.

This prompt was auto-injected after /clear ran. The user has not typed anything
since. Read the handoff document and continue the prior work seamlessly.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `a3ece39d2b5c`
- uncommitted changes: 9 file(s)

Uncommitted working-tree files (these are in NO handoff — inspect FIRST):
```
 M .claude/scripts/git-manager/README.md
 M .claude/scripts/git-manager/git.ts
 M .claude/scripts/git-manager/recommend.ts
 M .claude/scripts/git-manager/render-html.ts
 M .claude/scripts/git-manager/render-terminal.ts
 M .claude/scripts/git-manager/scan.ts
 M .claude/scripts/git-manager/types.ts
?? memory/handoffs/2026-08-03-emergency-handoff-2.yaml
?? memory/handoffs/2026-08-03-emergency-handoff-3.yaml
```

Recent commits at fire time:
```
a3ece39 chore: save the 2026-08-03 session handoff
aa6ea92 docs(git-manager): document permanent row numbers
b8660c7 fix(git-manager): row numbers are permanent, not positions
5934bc1 chore: snapshot working tree — git-manager, axiom-synthesis, research-riffs, logo-forge workspace
0452552 feat(git-manager): remember what the human ruled out, and fit the browser table
757a414 chore: back up working tree — git-manager skill + accumulated session work
551301a feat(website-builder): promote the PRD out of swarm scratch into a real project
88c1597 feat(resurrection): adopt-in-place — a pick lands in the tab it was typed in
```

**Drift check:** if `git rev-parse --short=12 HEAD` no longer equals `a3ece39d2b5c`, or the working tree is dirty, RECONCILE from `git log` / `git status` / `git diff` before trusting any "completed / all committed" claim in the handoff above. (This session learned the hard way: a 2026-06-24 resume arrived 3 commits + 1 uncommitted method stale.)
