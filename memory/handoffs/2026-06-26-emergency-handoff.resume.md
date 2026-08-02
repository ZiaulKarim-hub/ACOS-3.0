Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `memory/handoffs/2026-06-26-emergency-handoff.yaml` for full session state.

Quick summary:
- Working on: acos-hypercore-ask — Hypercore Data Catalog (COMPLETE) + per_diem_interest native sourcing. Branch acos-deficiency-fixes-2026-06-04.
- Last action: committed (6eda512) + pushed to BOTH remotes the COMPLETE Hypercore Data Catalog — 5,204 value fields mapped, 559 named, in .claude/skills/acos-hypercore-ask/catalog/. hca-catalog-lookup.py resolves any phrase -> path/working-query.
- Next step (OPTIONAL — catalog goal is DONE): wire hca-catalog-lookup into hca-ask.py smart_ask explorer fallback so the skill can fetch ANY cataloged field by phrase, not just built figures.
- Blockers: borrower (clients HTTP 500) + equity (HTTP 403) live-probe deferred; branch not merged to main.

Key invariants: prefer Hypercore NATIVE values (compute only as a double-check); interest rates are PERCENTS (14=14%); totalOutstanding.total is NET (use .principal for interest basis); 634 tests green; ALWAYS push BOTH remotes (origin + personal); autopilot ACTIVE (catalog goal complete) + ultracode ON (use workflows for substantive tasks).

On resume ALWAYS check git vs handoff — history was rewritten this session; verify HEAD=6eda512 with `git log --oneline -5`. This prompt was auto-injected after /clear; the user has not typed since. Read the handoff and continue seamlessly.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `6eda512d8594`
- uncommitted changes: 17 file(s)

Uncommitted working-tree files (these are in NO handoff — inspect FIRST):
```
 M memory/handoffs/2026-06-16-emergency-handoff.resume.md
 D memory/handoffs/2026-06-16-emergency-handoff.yaml
 D memory/handoffs/2026-06-21-emergency-handoff.yaml
?? memory/handoffs/2026-06-23-emergency-handoff.resume.md
?? memory/handoffs/2026-06-24-emergency-handoff-2.resume.md
?? memory/handoffs/2026-06-24-emergency-handoff.resume.md
?? memory/handoffs/2026-06-26-emergency-handoff.resume.md
?? memory/handoffs/2026-06-26-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-16-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-21-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-23-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-24-emergency-handoff-2.yaml
?? memory/handoffs/archive/2026-06-24-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-25-completion-handoff.yaml
?? memory/handoffs/archive/2026-06-25-emergency-handoff.resume.md
?? memory/handoffs/archive/2026-06-25-emergency-handoff.yaml
?? planning/acos-axiom-synthesis/
```

Recent commits at fire time:
```
6eda512 feat(hca): Hypercore Data Catalog complete — 5,204 fields mapped, 559 named, probed + verified
f3c556c feat(hca): Hypercore Data Catalog — Phase 1 harvest + probe tooling (proven)
2abd2d1 feat(hca): per_diem_interest now sourced DIRECTLY from Hypercore (native + cross-check)
99a3b98 feat(hca): per_diem_interest funding figure (computed, provenance-bound, day-count stated)
de77efa feat(hca): MCQ-selection + learned-routing loop (learn routing, never values)
39ef8fa fix(eternity): freeze-early arming marker + inform-only git-state capture
5974a4f feat(hca): reconciled portfolio_outstanding aggregate + routing (autopilot unit 4)
2c99b5e docs(hca): document explorer depth-1 nesting + investor-portfolio figures (autopilot unit 3)
```

**Drift check:** if `git rev-parse --short=12 HEAD` no longer equals `6eda512d8594`, or the working tree is dirty, RECONCILE from `git log` / `git status` / `git diff` before trusting any "completed / all committed" claim in the handoff above. (This session learned the hard way: a 2026-06-24 resume arrived 3 commits + 1 uncommitted method stale.)
