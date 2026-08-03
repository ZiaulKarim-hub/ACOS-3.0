Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `memory/handoffs/2026-08-02-emergency-handoff-3.yaml` for
full session state. (Use THAT file — two unrelated same-day handoffs exist:
`-emergency-handoff.yaml` is a git-manager session, `-2.yaml` is axiom-synthesis.
Do not read those.)

Quick summary:
- Working on: the GLOBAL skill `~/.claude/skills/acos-logo-forge/` (OUTSIDE this
  git repo — it never shows in `git status` here), driving the in-repo untracked
  workspace `Logo Builder/brandsync/` via `app/server.py` on 127.0.0.1:8815
  (PID 43272 at handoff time; restart it if dead).
- Last action: added the per-card ✕ Reject button — inline reason panel (9 tags +
  free text, no native dialogs), `POST /api/reject` MOVES the file to
  `<kind>/rejected/round-<N>/` (never deletes), appends to workspace `avoid.json`,
  writes a `reject`/`unreject` bridge command, 7-second Undo. reject-test.ts 17/17.
- Next step: promote `forge-test.ts` and `reject-test.ts` from the session
  scratchpad into `~/.claude/skills/acos-logo-forge/app/` as permanent regression
  gates (like button-test.ts / seed-forges.ts / ink-check.ts). They exist ONLY in
  /private/tmp scratchpad right now and will be lost when it is cleaned.
- Blockers: none technical. Procedural: per ~/CLAUDE.md, ANY GitHub-reaching
  action requires asking Zee which account (okoateam vs ZiaulKarim-hub) FIRST —
  never a bare `git push`. This session made ZERO commits and ZERO pushes. The
  repo working tree is shared by several concurrent sessions (git-manager,
  axiom-synthesis, research-riffs, Website Builder, Zermatt Credit Memo), so never
  sweep unrelated changes into a commit.

STALE-CLAIM CORRECTION: a new-style `fanout` HAS now run live (r1-54e1 → symbol
round-2, 10 genuinely distinct ideas, not a numeric sweep) — the fan-out rewrite
is proven in production. `combine` and `reject` remain unproven against live data:
no `avoid.json` and no `rejected/` directories exist yet.

Standing user directives to honour: Eden Protocol Level 2 for chat replies
(plain language, sentences ≤22 words, define every term, keep all numbers and
caveats verbatim). Verify visual claims by looking at PIXELS, not container
boxes — a container-overflow test cannot see art clipped by its own viewBox
(this session shipped cropped art twice before catching it that way).

This prompt was auto-injected after /clear ran. The user has not typed anything
since. Read the handoff document and continue the prior work seamlessly.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `757a414e4317`
- uncommitted changes: 34 file(s)

Uncommitted working-tree files (these are in NO handoff — inspect FIRST):
```
 M .claude/scripts/git-manager/README.md
 M .claude/scripts/git-manager/inventory.ts
 M .claude/scripts/git-manager/render-html.ts
 M .claude/scripts/git-manager/render-terminal.ts
 M .claude/scripts/git-manager/scan.ts
 M .claude/scripts/git-manager/types.ts
 M .claude/skills/acos-axiom-synthesis/SKILL.md
 M .claude/skills/acos-axiom-synthesis/prompts/elicitor.md
 M .claude/skills/acos-axiom-synthesis/scripts/orchestrate.py
 M .claude/skills/acos-research-riffs/SKILL.md
 M .claude/skills/acos-research-riffs/scripts/lib/claims.ts
 M .claude/skills/acos-research-riffs/scripts/lib/ledger.ts
 M .claude/skills/acos-research-riffs/scripts/lib/report.ts
 M .claude/skills/acos-research-riffs/scripts/riff.ts
 M .claude/skills/acos-research-riffs/scripts/test-riff.ts
 M .claude/skills/acos-research-riffs/templates/probe-charter.md
 M "Logo Builder/brandsync/commands.jsonl"
 M planning/acos-axiom-synthesis/WAKE-UP-2026-07-22.md
 M planning/acos-research-riffs/ARCHITECTURE.md
?? .claude/scripts/git-manager/recommend.ts
?? .claude/skills/acos-axiom-synthesis/RUNBOOK.md
?? .claude/skills/acos-axiom-synthesis/scripts/conductor.py
?? .claude/skills/acos-axiom-synthesis/tests/test_conductor.py
?? "Logo Builder/brandsync/avoid.json"
?? "Logo Builder/brandsync/smooth/"
?? "Logo Builder/brandsync/symbol/"
?? "Logo Builder/brandsync/wordmark/"
?? memory/handoffs/2026-08-01-emergency-handoff.yaml
?? memory/handoffs/2026-08-02-emergency-handoff-2.resume.md
?? memory/handoffs/2026-08-02-emergency-handoff-2.yaml
?? memory/handoffs/2026-08-02-emergency-handoff-3.yaml
?? memory/handoffs/2026-08-02-emergency-handoff.resume.md
?? memory/handoffs/2026-08-02-emergency-handoff.yaml
?? planning/acos-axiom-synthesis/RESEARCH-recency-bias-2026-08-02.md
```

Recent commits at fire time:
```
757a414 chore: back up working tree — git-manager skill + accumulated session work
551301a feat(website-builder): promote the PRD out of swarm scratch into a real project
88c1597 feat(resurrection): adopt-in-place — a pick lands in the tab it was typed in
d5f352a feat(research-riffs): live responder — seats answer on their own in ~5-7s
42fdc51 fix(research-riffs): room now reuses IC's real committee-room page
f435d3e feat(research-riffs): verify-first guardrails + IC-style live room
1c127b4 feat(resurrection): sidebar-name-first identity + global resurrect skill
7080062 fix(eternity+resurrection): post-clear misfire guard + safe-close session identity
```

**Drift check:** if `git rev-parse --short=12 HEAD` no longer equals `757a414e4317`, or the working tree is dirty, RECONCILE from `git log` / `git status` / `git diff` before trusting any "completed / all committed" claim in the handoff above. (This session learned the hard way: a 2026-06-24 resume arrived 3 commits + 1 uncommitted method stale.)
