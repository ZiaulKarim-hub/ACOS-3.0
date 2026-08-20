Resuming session via acos-eternity-protocol auto-resume (fire #2).

CONTEXT HANDOFF: Read "/Users/zee/Documents/Vibe Coding/ACOS 3.0/memory/handoffs/2026-08-06-emergency-handoff-4.yaml" (mirror: "/Users/zee/Documents/Vibe Coding/R2P/memory/handoffs/2026-08-06-emergency-handoff-4.yaml") for full state.

Quick summary:
- Working on: R2P build in "/Users/zee/Documents/Vibe Coding/R2P" — EPIC-001, 8 stories, 24 DEV/QA pairs ("keep going until the whole epic is done").
- Last landed: holdout run 2 (7/8) + STORY-001-001 pair-02/03 manifests committed (HEAD 5559dec at fire time).
- In flight at clear: (1) DEV-001-001-01 REVISION 4 (F03 respell 'instrumentId'→'instrument_id') — mapping.ts fix confirmed green on disk but DEV yaml still version: 3, full gates/evidence unrecorded, UNCOMMITTED; (2) STORY-001-003 custodian — ZERO trace on disk at fire time (no qa-private/HLD-001-003-* and no manifests); respawn it if still absent.
- Next: verify rev4 on disk (run pnpm test / check / qa:parity / test:mutation yourself, EXIT CODES), complete/commit rev4 evidence; holdout run 3 (expect 8/8) → seal EVB-PAIR-001-001-01; implement pairs 001-001-02/03; then stories 002-008; swarm review; epic closeout — present close decision + ADR-001 ratification to Zee. Never push. Eden L3 plain language.
- Gotchas: agents stall after interim messages — SendMessage "continue in ONE pass"; test:mutation mutates in place (no concurrent code work); qa-private/ custodian/evaluator-only.

This prompt was auto-injected after /clear ran. Read the handoff and continue seamlessly.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `d3ee7714ce0f`
- uncommitted changes: 24 file(s)

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
