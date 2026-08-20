Resuming session via acos-eternity-protocol auto-resume (fire #3).

CONTEXT HANDOFF: Read "/Users/zee/Documents/Vibe Coding/ACOS 3.0/memory/handoffs/2026-08-06-emergency-handoff-5.yaml" (mirror: "/Users/zee/Documents/Vibe Coding/R2P/memory/handoffs/2026-08-06-emergency-handoff-5.yaml") for full state.

Quick summary:
- Working on: R2P build in "/Users/zee/Documents/Vibe Coding/R2P" — EPIC-001, 8 stories, 24 DEV/QA pairs ("keep going until the whole epic is done"). Never push (no remote). Eden L3 active.
- Done: pairs 1 (seal be2a968) and 2 (seal 44dccca) of 24 CLOSED+SEALED. All 24 holdout packs sealed. HASHING.md (f012ce6+b0ac805) documents hash methods + audit baselines for the 5 UNRESOLVED packs.
- In flight at clear: pair 3 DEV candidate committed 6ffc7db (395/395, mutation 89.20); adversarial QA-001-001-03 agent was running with ZERO disk trace at handoff time — if tests/unit/qa-001-001-03.adversarial.test.ts still absent and QA-001-001-03.yaml still version 1/draft, RESPAWN QA from scratch (assignment template in handoff next_actions); if partial work landed, verify first-hand and continue.
- Next: QA-001-001-03 verdict loop (BLOCK→revision→re-verify / PASS→holdout eval HLD-001-001-03-v1 with UNRESOLVED-hash baseline protocol→seal pair 3), then stories 002-008 (3 pairs each, same G.1→G.2→G.3→seal cycle), then epic close: swarm review, EVB-EPIC-001, present close decision + ADR-001 ratification + queued disclosure items to Zee — never self-approve.
- Gotchas: agents stall after interim messages (SendMessage "continue in ONE pass, no narration"); old agent ids are dead after clear — check disk, respawn if absent; verify claims first-hand (exit codes, git show --stat); scoped git adds only; test:mutation mutates in place — killed runs leave .stryker-tmp that HANGS the suite (rm -rf .stryker-tmp); qa-private/ custodian/evaluator-only; TypeScript only, no python3 one-liners.

This prompt was auto-injected after /clear ran. Read the handoff and continue seamlessly.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `d3ee7714ce0f`
- uncommitted changes: 26 file(s)

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
?? memory/handoffs/2026-08-06-emergency-handoff-5.yaml
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
