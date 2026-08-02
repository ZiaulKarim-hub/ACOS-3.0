Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `memory/handoffs/archive/2026-07-02-emergency-handoff.yaml` for full session state.

Quick summary:
- Working on: acos-xl-update — a new skill automating OKOA's weekly "XL Ant" investor Excel report (combines acos-hypercore-ask + acos-fireflies-ask).
- Last action: BUILT + validated the skill. Engine `.claude/skills/acos-xl-update/scripts/xl_update.py` + `SKILL.md` (both UNCOMMITTED on disk). Engine tested on a temp copy: prepare/apply/verify, formula-guard, appearance 100% preserved (identical 36-page pagination), non-destructive. All 4 Hypercore figures validated live: Utah Shoe payoff via `hca-figures.py --loan-id 88`; Ascent Senior=134 / Ascent Pref=149 / Lux II=171 via hca-ask (XL = funding entity 3).
- Next step: (a) COMMIT the acos-xl-update skill (2 files); (b) a DRY-RUN of the 07/05/2026 report was OFFERED for user review — the Fireflies narrative half is NOT yet exercised — awaiting user go-ahead; (c) resolve the user's OPEN request: "commit ONLY hypercore-ask stuff to my BUSINESS (okoateam) git account, isolated" (options: new repo okoateam/acos-hypercore-ask vs clean branch; business-only vs mirror-to-personal).
- Blockers: none.

ON RESUME ALWAYS CHECK GIT VS HANDOFF: branch `acos-deficiency-fixes-2026-06-04`, HEAD 57a081c (~54 ahead of main). The acos-xl-update files are UNCOMMITTED on disk — verify with `git status` before acting. Do NOT auto-run the XL dry-run or the business-account commit without the user's explicit go-ahead (both were awaiting the user).

This prompt was auto-injected after /clear ran. The user has not typed anything since. Read the handoff document and continue the prior work seamlessly.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `57a081cabc5b`
- uncommitted changes: 25 file(s)

Uncommitted working-tree files (these are in NO handoff — inspect FIRST):
```
 M .claude/scripts/eternity-resume-prepend.sh
 M memory/handoffs/2026-06-16-emergency-handoff.resume.md
 D memory/handoffs/2026-06-16-emergency-handoff.yaml
 D memory/handoffs/2026-06-21-emergency-handoff.yaml
?? .claude/skills/acos-xl-update/
?? memory/handoffs/2026-06-23-emergency-handoff.resume.md
?? memory/handoffs/2026-06-24-emergency-handoff-2.resume.md
?? memory/handoffs/2026-06-24-emergency-handoff.resume.md
?? memory/handoffs/2026-06-26-emergency-handoff-2.resume.md
?? memory/handoffs/2026-06-26-emergency-handoff-2.yaml
?? memory/handoffs/2026-06-26-emergency-handoff.resume.md
?? memory/handoffs/2026-06-26-emergency-handoff.yaml
?? memory/handoffs/2026-06-30-emergency-handoff.resume.md
?? memory/handoffs/2026-06-30-emergency-handoff.yaml
?? memory/handoffs/archive/2026-07-02-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-16-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-21-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-23-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-24-emergency-handoff-2.yaml
?? memory/handoffs/archive/2026-06-24-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-25-completion-handoff.yaml
?? memory/handoffs/archive/2026-06-25-emergency-handoff.resume.md
?? memory/handoffs/archive/2026-06-25-emergency-handoff.yaml
?? planning/acos-axiom-synthesis/
?? research/
```

Recent commits at fire time:
```
57a081c feat(hca): progressive-disclosure loan resolution (learned alias + partial-signal + tranche drill-down)
e9f91bb test(hca): pin provenance citation + path-safety guard for catalog wiring
402e81c feat(hca): wire Hypercore Data Catalog into smart_ask explorer fallback
6eda512 feat(hca): Hypercore Data Catalog complete — 5,204 fields mapped, 559 named, probed + verified
f3c556c feat(hca): Hypercore Data Catalog — Phase 1 harvest + probe tooling (proven)
2abd2d1 feat(hca): per_diem_interest now sourced DIRECTLY from Hypercore (native + cross-check)
99a3b98 feat(hca): per_diem_interest funding figure (computed, provenance-bound, day-count stated)
de77efa feat(hca): MCQ-selection + learned-routing loop (learn routing, never values)
```

**Drift check:** if `git rev-parse --short=12 HEAD` no longer equals `57a081cabc5b`, or the working tree is dirty, RECONCILE from `git log` / `git status` / `git diff` before trusting any "completed / all committed" claim in the handoff above. (This session learned the hard way: a 2026-06-24 resume arrived 3 commits + 1 uncommitted method stale.)
