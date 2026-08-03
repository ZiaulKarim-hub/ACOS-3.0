Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `/Users/zee/Documents/Vibe Coding/ACOS 3.0/memory/handoffs/2026-08-02-emergency-handoff.yaml` for full session state.

Quick summary:
- Working on: built and hardened /acos-git-manager — one table showing which repo hosts which skill or project, what is not saved or pushed anywhere, and what to do about each row; then pushed everything to the PERSONAL GitHub account.
- Last action: committed and pushed ACOS 3.0 757a414 and ~/.claude/skills bab2b29 to ZiaulKarim-hub (personal); origin/okoateam deliberately left with 3 commits waiting.
- Next step: ASK Zee whether to update ~/CLAUDE.md and acos-git-manager SKILL.md Step 4 — both still say "ALWAYS ASK FIRST" about the repo, which contradicts his 2026-08-01 standing rule that "git commit push" means push to personal without asking. Do NOT edit either file unprompted; they are his governance files.
- Blockers:
    1. SESSION LIMIT — the handoff-agent died on "You've hit your session limit · resets 2:10am (America/Denver)". Subagent spawning may fail again; prefer main-thread work.
    2. ~/CLAUDE.md still ask-first; Zee was offered an update and has NOT answered.
    3. acos-git-manager SKILL.md Step 4 still ask-every-time; same, no answer yet.

Also open, all offered to Zee with no answer yet:
- Row 19 "Fastest Decision tree" is a repo with ZERO commits and 3 unsaved files, flagged as a possible duplicate of row 38 "fastest-decision-tree" which is already SAFE. Cheapest win — offer the comparison again.
- 9 untracked real projects marked "git init -> personal": Font-Forge, HearMeTalk, lux2-slide-extension, Auto-Blogger, Jobsync, private-equity-hedge-fund-strategy, preeng, private_credit_design_reference, font-foundry.

HARD CONSTRAINTS carried forward:
- DO NOT commit the acos-research-riffs files in ACOS 3.0 — ANOTHER LIVE SESSION is editing them.
- DO NOT push ACOS 3.0's 3 waiting commits to origin (okoateam) unless Zee names the work account.
- Run /acos-git-manager to see current state; it opens the browser view in Chrome automatically.

This prompt was auto-injected after /clear ran. The user has not typed anything
since. Read the handoff document and continue the prior work seamlessly.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `757a414e4317`
- uncommitted changes: 17 file(s)

Uncommitted working-tree files (these are in NO handoff — inspect FIRST):
```
 M .claude/scripts/git-manager/README.md
 M .claude/scripts/git-manager/inventory.ts
 M .claude/scripts/git-manager/render-html.ts
 M .claude/scripts/git-manager/render-terminal.ts
 M .claude/scripts/git-manager/scan.ts
 M .claude/scripts/git-manager/types.ts
 M .claude/skills/acos-research-riffs/SKILL.md
 M .claude/skills/acos-research-riffs/scripts/lib/claims.ts
 M .claude/skills/acos-research-riffs/scripts/lib/ledger.ts
 M .claude/skills/acos-research-riffs/scripts/lib/report.ts
 M .claude/skills/acos-research-riffs/scripts/riff.ts
 M .claude/skills/acos-research-riffs/scripts/test-riff.ts
 M .claude/skills/acos-research-riffs/templates/probe-charter.md
 M planning/acos-research-riffs/ARCHITECTURE.md
?? .claude/scripts/git-manager/recommend.ts
?? memory/handoffs/2026-08-01-emergency-handoff.yaml
?? memory/handoffs/2026-08-02-emergency-handoff.yaml
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
