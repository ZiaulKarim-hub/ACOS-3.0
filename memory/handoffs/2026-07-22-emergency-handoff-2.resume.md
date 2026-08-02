Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `memory/handoffs/2026-07-22-emergency-handoff-2.yaml` for full state.

Quick summary:
- Working on: BUILT /acos-reverse-cleanroom (reverse app -> tool-agnostic INTENT -> N blind models rebuild -> backbone-first fused spec into ACOS Vision/Epic/Story/Slice + Genesis; fail-closed clean-room egress guard). Authoring complete; selftest 12/12; cross-ref audit passed.
- Last action: wrote planning/acos-reverse-cleanroom/axiom-synthesis-reuse-map.md + memory file project_acos_reverse_cleanroom.md.
- Next step: (1) wire acos-axiom-synthesis as the Phase-5 FACT lane per the reuse map (de-circularization + corroboration gate + hash-chained ledger + falsification gate), keep rc-fusion-synthesizer for the DESIGN lane; (2) fix .acos/config/cleanroom.yaml roster to `zai:glm-4.7` + `google:gemini-flash-latest`.
- Blockers: live run gated on user prereqs (Playwright, API keys) + target choice.

Auto-injected after /clear; the user typed nothing. Read the handoff and continue seamlessly.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `1c127b46a31c`
- uncommitted changes: 138 file(s)

Uncommitted working-tree files (these are in NO handoff — inspect FIRST):
```
 M .DS_Store
 M .claude/scripts/acos-token-monitor-bin-reference/token-watcher.py
 M .claude/scripts/eternity-protocol-core.sh
 M .claude/scripts/eternity-resume-prepend.sh
 M .claude/scripts/resurrection/launch-project.sh
 M .claude/scripts/resurrection/resurrect-view.py
 M .claude/scripts/run-external-agent.py
 M .claude/scripts/session-cleanup.sh
 M .claude/skills/acos-axiom-synthesis/SKILL.md
 M .claude/skills/acos-axiom-synthesis/prompts/README.md
 M .claude/skills/acos-axiom-synthesis/scripts/orchestrate.py
 M .claude/skills/acos-complete/SKILL.md
RM .claude/skills/deep-research/SKILL.md -> .claude/skills/acos-deep-research/SKILL.md
 M .claude/skills/acos-resurrect/SKILL.md
 M .claude/skills/acos-xl-update/SKILL.md
 M .claude/skills/document-processing/SKILL.md
 M .claude/skills/knowledge-graph/SKILL.md
 M .claude/skills/prism-research/SKILL.md
 M memory/handoffs/2026-06-16-emergency-handoff.resume.md
 D memory/handoffs/2026-06-16-emergency-handoff.yaml
 D memory/handoffs/2026-06-21-emergency-handoff.yaml
 M planning/acos-axiom-synthesis/PLAN.md
?? .claude/agents/rc-capture-orchestrator.md
?? .claude/agents/rc-fusion-synthesizer.md
?? .claude/agents/rc-intent-extractor.md
?? .claude/agents/rc-intent-qa.md
?? .claude/agents/rc-intent-synthesizer.md
?? .claude/agents/rc-prioritizer.md
?? .claude/agents/rc-rebuild-proposer.md
?? .claude/agents/rc-red-team.md
?? .claude/agents/rc-spec-wall.md
?? .claude/scripts/cleanroom/
?? .claude/scripts/resurrection/rename-workspace.sh
?? .claude/skills/acos-axiom-synthesis/config/
?? .claude/skills/acos-axiom-synthesis/prompts/elicitor.md
?? .claude/skills/acos-axiom-synthesis/prompts/grader.md
?? .claude/skills/acos-axiom-synthesis/prompts/refuter.md
?? .claude/skills/acos-axiom-synthesis/prompts/synthesizer.md
?? .claude/skills/acos-axiom-synthesis/scripts/checklist.py
?? .claude/skills/acos-axiom-synthesis/tests/test_checklist.py
?? .claude/skills/acos-research-riffs/
?? .claude/skills/acos-reverse-cleanroom/
?? .omx/
?? "Zermatt Credit Memo/"
?? memory/decisions/2026-07-05-eternity-protocol-nonfiring-audit.md
?? memory/handoffs/2026-06-23-emergency-handoff.resume.md
?? memory/handoffs/2026-06-24-emergency-handoff-2.resume.md
?? memory/handoffs/2026-06-24-emergency-handoff.resume.md
?? memory/handoffs/2026-06-26-emergency-handoff-2.resume.md
?? memory/handoffs/2026-06-26-emergency-handoff.resume.md
?? memory/handoffs/2026-06-30-emergency-handoff.resume.md
?? memory/handoffs/2026-07-02-emergency-handoff.resume.md
?? memory/handoffs/2026-07-06-emergency-handoff.resume.md
?? memory/handoffs/2026-07-07-emergency-handoff.resume.md
?? memory/handoffs/2026-07-09-ic-build-handoff.resume.md
?? memory/handoffs/2026-07-14-emergency-handoff.resume.md
?? memory/handoffs/2026-07-22-emergency-handoff-2.yaml
?? memory/handoffs/2026-07-22-emergency-handoff.resume.md
?? memory/handoffs/2026-07-22-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-16-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-21-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-23-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-24-emergency-handoff-2.yaml
?? memory/handoffs/archive/2026-06-24-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-25-completion-handoff.yaml
?? memory/handoffs/archive/2026-06-25-emergency-handoff.resume.md
?? memory/handoffs/archive/2026-06-25-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-26-emergency-handoff-2.yaml
?? memory/handoffs/archive/2026-06-26-emergency-handoff.yaml
?? memory/handoffs/archive/2026-06-30-emergency-handoff.yaml
?? memory/handoffs/archive/2026-07-02-completion-handoff.yaml
?? memory/handoffs/archive/2026-07-02-emergency-handoff.yaml
?? memory/handoffs/archive/2026-07-06-emergency-handoff.yaml
?? memory/handoffs/archive/2026-07-07-completion-handoff.yaml
?? memory/handoffs/archive/2026-07-07-emergency-handoff-2.yaml
?? memory/handoffs/archive/2026-07-07-emergency-handoff.yaml
?? memory/handoffs/archive/2026-07-09-ic-build-handoff.md
?? memory/handoffs/archive/2026-07-13-completion-handoff-2.yaml
?? memory/handoffs/archive/2026-07-13-completion-handoff.yaml
?? memory/handoffs/archive/2026-07-13-emergency-handoff-2.yaml
?? memory/handoffs/archive/2026-07-13-emergency-handoff.yaml
?? memory/handoffs/archive/2026-07-13-keychain-eternity-diagnosis.md
?? memory/handoffs/archive/2026-07-13-session-handoff.yaml
?? memory/handoffs/archive/2026-07-14-emergency-handoff.yaml
?? memory/handoffs/archive/2026-07-16-completion-handoff.yaml
?? memory/handoffs/archive/2026-07-16-emergency-handoff-2.yaml
?? memory/handoffs/archive/2026-07-16-emergency-handoff.yaml
?? memory/handoffs/archive/2026-07-18-completion-handoff.yaml
?? memory/handoffs/archive/2026-07-20-completion-handoff.yaml
?? memory/handoffs/closed/
?? planning/acos-axiom-synthesis/WAKE-UP-2026-07-22.md
?? planning/acos-okoa-works/
?? planning/acos-research-riffs/
?? planning/acos-reverse-cleanroom/
?? planning/preeng/003-investment-committee/
?? planning/preeng/004-acos-eden-protocol/
?? planning/preeng/005-resurrection-protocol/
?? planning/slices/SLICE-EDEN-01-command-grammar-state.yaml
?? planning/slices/SLICE-EDEN-02-spike-multihook-additionalcontext.yaml
?? planning/slices/SLICE-EDEN-03-injector-hook.yaml
?? planning/slices/SLICE-EDEN-04-rearm-across-clear.yaml
?? planning/slices/SLICE-EDEN-05-fidelity-floor-exempt-classifier.yaml
?? planning/slices/SLICE-EDEN-06-precision-appendix.yaml
?? planning/slices/SLICE-EDEN-07-reading-level-engine.yaml
?? planning/slices/SLICE-EDEN-08-self-verification-heuristic.yaml
?? planning/slices/SLICE-EDEN-09-per-message-override.yaml
?? planning/slices/SLICE-EDEN-10-persistence-status-docs.yaml
?? planning/slices/SLICE-IC-A1-roster-coverage-map.yaml
?? planning/slices/SLICE-IC-A2-expert-agent-defs.yaml
?? planning/slices/SLICE-IC-A3-optionals-advocate-separation.yaml
?? planning/slices/SLICE-IC-B1-deal-intake.yaml
?? planning/slices/SLICE-IC-B2-blind-opening-pass.yaml
?? planning/slices/SLICE-IC-B3-expert-research-swarms.yaml
?? planning/slices/SLICE-IC-C1-objection-fact-adapter-axis-s.yaml
?? planning/slices/SLICE-IC-C2-axiom-synthesis-run.yaml
?? planning/slices/SLICE-IC-C3-deterministic-verdict.yaml
?? planning/slices/SLICE-IC-C4-ic-memo-render.yaml
?? planning/slices/SLICE-IC-D1-moderator-loop-transcript.yaml
?? planning/slices/SLICE-IC-D2-tally-chair-hitl.yaml
?? planning/slices/SLICE-IC-D3-resume-durability.yaml
?? planning/slices/SLICE-IC-DIAG-01.yaml
?? planning/slices/SLICE-IC-E1-legal-reuse-compliance-conflicts.yaml
?? planning/slices/SLICE-IC-F1-guardrails-governance.yaml
?? planning/slices/SLICE-RES-00-probe.yaml
?? planning/slices/SLICE-RES-01-prereq-fixes.yaml
?? planning/slices/SLICE-RES-10-registry-lib.yaml
?? planning/slices/SLICE-RES-11-enroll.yaml
?? planning/slices/SLICE-RES-12-rebuild.yaml
?? planning/slices/SLICE-RES-13-seed-curate.yaml
?? planning/slices/SLICE-RES-20-close.yaml
?? planning/slices/SLICE-RES-21-safe-close-skill.yaml
?? planning/slices/SLICE-RES-22-blind-roundtrip.yaml
?? planning/slices/SLICE-RES-30-resurrect-view.yaml
?? planning/slices/SLICE-RES-31-launch.yaml
?? planning/slices/SLICE-RES-32-menu-skill-loop.yaml
?? planning/slices/SLICE-RES-40-dr1.yaml
?? planning/slices/SLICE-RES-50-browser.yaml
?? research/
```

Recent commits at fire time:
```
1c127b4 feat(resurrection): sidebar-name-first identity + global resurrect skill
7080062 fix(eternity+resurrection): post-clear misfire guard + safe-close session identity
cc62ecd feat(investment-committee): live pool-backed committee room, 8 tooled seats, reading-level dial
df1b0ca fix(eternity): learned-dead-surface — stop re-binding to a dead cmux surface (self-expiring)
daf36ae fix(eternity): de-mislead the 'warp manual-only' NOOP log + Priority-2 fire escalation
6654c06 fix(eternity): invalidate stale cmux-surface binding + escalate dead-surface /clear
7a04e77 feat(axiom-synthesis): Phases 2-7 pipeline — decircularize→grade→falsify→resolve→lifecycle→coverage
a6eed67 feat(axiom-synthesis): substrate + blueprint for acos-axiom-synthesis (Phases 0-1, WIP)
```

**Drift check:** if `git rev-parse --short=12 HEAD` no longer equals `1c127b46a31c`, or the working tree is dirty, RECONCILE from `git log` / `git status` / `git diff` before trusting any "completed / all committed" claim in the handoff above. (This session learned the hard way: a 2026-06-24 resume arrived 3 commits + 1 uncommitted method stale.)
