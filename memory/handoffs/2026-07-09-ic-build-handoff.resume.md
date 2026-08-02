Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `memory/handoffs/archive/2026-07-09-ic-build-handoff.md` for full session state, then continue.

Quick summary:
- Working on: building the `acos-investment-committee` ACOS skill in dependency waves (user wants it built fast via agents, then to EXPERIENCE using it).
- Done & VERIFIED: Wave 0 (vendored axiom-synthesis engine, 54/54 tests + scaffold), Wave 1 (roster.yaml/coverage-map.yaml, 11 `ic-*` agents registered, resolve_roster.py, extract_deal.py + fixtures/sample-deal — interop-tested), Wave 2 C-chain built (build_facts/run_synthesis/verdict/render_memo, 23/23 smoke).
- NEXT STEP (do first): the HARMONIZATION FIX — the seat objection output format doesn't match `build_facts.py`'s input contract (the fix-agent died on an API error and wrote NOTHING; files are clean). Pin seat defs `ic-01..08` + `ic-09-deal-advocate` to emit EXACTLY the JSON in build_facts.py's docstring (wrapper {seat,seat_name,role_family,objections[],mitigants[]}, evidence as list of dicts, a worked example); #9 advocate emits objections:[] + mitigants[]; #10 gap-hunter unchanged. AND add input-coercion to build_facts.py. Verify with a real-shaped seat-04.json + seat-09.json.
- THEN (the "experience it" milestone): wire SKILL.md Mode-A router + blind-opening-pass → REAL run on fixtures/sample-deal/ → produce ic-memo.md → SHOW THE USER. Then Wave 4 (Mode B: D1/D2/D3) + Wave 5 (E1 legal reuse, F1 guardrails).
- Discipline: VERIFY/recompute every gate yourself (agent self-reports hid 2 real bugs this session); vendored-engine scripts need sys.path→scripts/synthesis/scripts.
- Blockers: none. Autopilot must stay OFF (user guarantees). Build hands-off; interrupt user only for genuine design forks.

This prompt was auto-injected after /clear ran. The user has not typed anything since. Read the handoff and continue the build seamlessly — resume at the harmonization fix.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `7a04e77b3ed8`
- uncommitted changes: 74 file(s)

Uncommitted working-tree files (these are in NO handoff — inspect FIRST):
```
 M .claude/skills/acos-xl-update/SKILL.md
 M memory/handoffs/2026-06-16-emergency-handoff.resume.md
 D memory/handoffs/2026-06-16-emergency-handoff.yaml
 D memory/handoffs/2026-06-21-emergency-handoff.yaml
?? .claude/agents/ic-01-credit-valuation.md
?? .claude/agents/ic-02-finance.md
?? .claude/agents/ic-03-accounting.md
?? .claude/agents/ic-04-legal-structural.md
?? .claude/agents/ic-05-insurance-climate.md
?? .claude/agents/ic-06-sponsor-fraud-forensics.md
?? .claude/agents/ic-07-portfolio-concentration.md
?? .claude/agents/ic-08-strategy.md
?? .claude/agents/ic-09-deal-advocate.md
?? .claude/agents/ic-10-gap-hunter.md
?? .claude/agents/ic-research-bot.md
?? .claude/skills/acos-investment-committee/
?? .omx/
?? memory/decisions/2026-07-05-eternity-protocol-nonfiring-audit.md
?? memory/handoffs/2026-06-23-emergency-handoff.resume.md
?? memory/handoffs/2026-06-24-emergency-handoff-2.resume.md
?? memory/handoffs/2026-06-24-emergency-handoff.resume.md
?? memory/handoffs/2026-06-26-emergency-handoff-2.resume.md
?? memory/handoffs/2026-06-26-emergency-handoff-2.yaml
?? memory/handoffs/2026-06-26-emergency-handoff.resume.md
?? memory/handoffs/2026-06-26-emergency-handoff.yaml
?? memory/handoffs/2026-06-30-emergency-handoff.resume.md
?? memory/handoffs/2026-06-30-emergency-handoff.yaml
?? memory/handoffs/2026-07-02-emergency-handoff.resume.md
?? memory/handoffs/2026-07-06-emergency-handoff.resume.md
?? memory/handoffs/2026-07-06-emergency-handoff.yaml
?? memory/handoffs/2026-07-07-emergency-handoff-2.yaml
?? memory/handoffs/2026-07-07-emergency-handoff.resume.md
?? memory/handoffs/2026-07-07-emergency-handoff.yaml
?? memory/handoffs/archive/2026-07-09-ic-build-handoff.md
?? memory/handoffs/archive/2026-06-16-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-21-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-23-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-24-emergency-handoff-2.yaml
?? memory/handoffs/archive/2026-06-24-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-25-completion-handoff.yaml
```

Recent commits at fire time:
```
7a04e77 feat(axiom-synthesis): Phases 2-7 pipeline — decircularize→grade→falsify→resolve→lifecycle→coverage
a6eed67 feat(axiom-synthesis): substrate + blueprint for acos-axiom-synthesis (Phases 0-1, WIP)
edd63d5 chore(eternity): version-controlled reference copies of the two in-pane hooks
0bd85ab fix(eternity): pane-scoped session-id derivation + twin-disarm double-injection fix
cd56698 feat(xl-update): 2-week recency rule for the weekly narrative points
72413e5 feat(xl-update): mandatory per-bullet reference companion (separate file)
2e49e8b feat(xl-update): route drafts to dedicated OKOA output folder
6fb4908 feat(xl-update): acos-xl-update skill + deterministic Excel engine
```

**Drift check:** if `git rev-parse --short=12 HEAD` no longer equals `7a04e77b3ed8`, or the working tree is dirty, RECONCILE from `git log` / `git status` / `git diff` before trusting any "completed / all committed" claim in the handoff above. (This session learned the hard way: a 2026-06-24 resume arrived 3 commits + 1 uncommitted method stale.)
