Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `memory/handoffs/2026-08-02-emergency-handoff-2.yaml` for full session state. Also see `planning/acos-axiom-synthesis/WAKE-UP-2026-07-22.md` for the running log.

Quick summary:
- Working on: the acos-axiom-synthesis skill. This session built (1) the boolean confidence checklist (veto + percentage -> tier: scripts/checklist.py + config/checklist.yaml, wired into orchestrate.py), (2) the four-family fan-out (Claude/Gemini/GLM/ChatGPT; prompts in prompts/, providers in .acos/config/providers.yaml), and (3) the live-run conductor (scripts/conductor.py + RUNBOOK.md + tests/test_conductor.py). The elicitor was upgraded to require real cited sources with dates.
- Last action: SECOND live end-to-end run (.acos/axiom/live-sourced-2026-08-02/) — claim C1 "The capital of Australia is Canberra" reached ESTABLISHED / verified, cited by TWO distinct real sources from TWO families (nca.gov.au [anthropic] + britannica.com [openai-web]). Offline test suite is 99/99 passing (test_substrate 19 + test_pipeline 35 + test_checklist 21 + test_conductor 24).
- Next step: ASK the user which to do next — do NOT assume. Options they were weighing: (a) build the recency/old-information fix per planning/acos-axiom-synthesis/RESEARCH-recency-bias-2026-08-02.md (volatility classification + freshness gate + guarded supersession; source dates already recorded in provenance as `as_of`); (b) add web access to the Gemini/GLM external runner (run-external-agent.py has no web, so only Claude+ChatGPT can cite live sources); or (c) pause.
- Blockers: none. Known limits (documented, not bugs): re-running a synthesis over an existing ledger needs a fresh ledger (illegal-transition refusal is the engine working correctly); v1 clustering is exact-normalized-text so paraphrase-merge is a manual orchestrator step (raw replies kept in collected/elicitor-raw/).
- Env: provider keys in Doppler (project ai-model-api, config dev_personal): GOOGLE_API_KEY, ZAI_CODING_PLAN_API_KEY. Gemini model = gemini-flash-latest; GLM = glm-4.7 via https://api.z.ai/api/coding/paas/v4. ChatGPT via Claude-in-Chrome browser (Browser 1). All work stayed scoped to acos-axiom-synthesis paths.

This prompt was auto-injected after /clear ran. The user has not typed anything since. Read the handoff document and continue the prior work seamlessly. Because there is an open decision, ASK the user which next step they want rather than picking one.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `757a414e4317`
- uncommitted changes: 31 file(s)

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
?? "Logo Builder/brandsync/smooth/"
?? "Logo Builder/brandsync/symbol/"
?? "Logo Builder/brandsync/wordmark/"
?? memory/handoffs/2026-08-01-emergency-handoff.yaml
?? memory/handoffs/2026-08-02-emergency-handoff-2.yaml
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
