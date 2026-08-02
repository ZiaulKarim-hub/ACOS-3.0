Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `memory/handoffs/archive/2026-06-25-emergency-handoff.yaml` for full session state.

Quick summary:
- Working on: acos-hypercore-ask — added an MCQ-selection + learned-routing loop (learn the ROUTING, never the value). Committed de77efa; 619 tests green. hca-learned.py is the new persistent store (metric_aliases + entity_resolutions).
- Last action: built + LIVE-verified the learning loop; seeded the real learned store with {"amount due":"outstanding"} from the user's MCQ pick. "amount due for XL on Ascent Pref" -> DELIVERED $3,313,999.996.
- Next step: the user asked "What is the per diem interest for XL for Lux II loan?" The skill REFUSES per-diem (no built-in figure; "per diem" also breaks name resolution). Manually derived ≈ $1,015.14/day (14% x $2,646,609.23 outstanding principal / 365; Actual/360 -> $1,029.24/day; loanFunding 338). FIRST: ask the user whether to build a dedicated per_diem_interest figure (fetch rate + outstanding principal, both provenance-bound; principal x rate / day-count; confidence-capped; day-count stated). Then build it if yes.
- Blockers: none for the skill. NOTE: git history was REWRITTEN this session (bloat cleanup) — current tip is de77efa; any SHAs in pre-2026-06-25 handoffs are stale. Check git vs handoff on resume.

This prompt was auto-injected after /clear ran. The user has not typed anything since. Read the handoff document and continue the prior work seamlessly.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `de77efa424ec`
- uncommitted changes: 12 file(s)

Uncommitted working-tree files (these are in NO handoff — inspect FIRST):
```
 M memory/handoffs/2026-06-16-emergency-handoff.resume.md
 D memory/handoffs/2026-06-16-emergency-handoff.yaml
 D memory/handoffs/2026-06-21-emergency-handoff.yaml
?? memory/handoffs/2026-06-23-emergency-handoff.resume.md
?? memory/handoffs/2026-06-24-emergency-handoff-2.resume.md
?? memory/handoffs/2026-06-24-emergency-handoff.resume.md
?? memory/handoffs/archive/2026-06-25-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-16-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-21-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-23-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-24-emergency-handoff-2.yaml
?? memory/handoffs/archive/2026-06-24-emergency-handoff.yaml
```

Recent commits at fire time:
```
de77efa feat(hca): MCQ-selection + learned-routing loop (learn routing, never values)
39ef8fa fix(eternity): freeze-early arming marker + inform-only git-state capture
5974a4f feat(hca): reconciled portfolio_outstanding aggregate + routing (autopilot unit 4)
2c99b5e docs(hca): document explorer depth-1 nesting + investor-portfolio figures (autopilot unit 3)
fb53718 feat(hca): reconciled investor-portfolio figures + orchestrator routing (autopilot unit 2)
c156de9 feat(hca): explorer depth-1 nested-object support (autopilot unit 1)
1623a53 docs(hca): document smart-ask entry + investor/funding/explorer modules in SKILL.md
16717f0 feat(hca): investor/funding capability + smart-ask orchestrator + confidence explorer
```

**Drift check:** if `git rev-parse --short=12 HEAD` no longer equals `de77efa424ec`, or the working tree is dirty, RECONCILE from `git log` / `git status` / `git diff` before trusting any "completed / all committed" claim in the handoff above. (This session learned the hard way: a 2026-06-24 resume arrived 3 commits + 1 uncommitted method stale.)
