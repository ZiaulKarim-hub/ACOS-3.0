Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `memory/handoffs/2026-07-28-emergency-handoff.yaml` for full session state.

Quick summary:
- Working on: OKOA Works — three threads. (1) Ascent entity register, (2) Mountain West Pest loan diligence, (3) Thurston workout document update. ALL business output lives OUTSIDE this git repo, in ~/Documents/OKOA/.
- Last action: Rebuilt "Wright Thurston Summary 20260728.html/.pdf" (5pp letter) from a PDF-only original, applying the new 18%/19%/20% stepped rate and the three named carve-out properties. Also built the 28 July memo (.html/.pdf/.docx), the deck (.html/.pdf 960x540pt/.pptx native editable), and CHANGE NOTE 20260728.md — all in ~/Documents/OKOA/Thurston Memo/. The 23 July originals are untouched.
- Next step: Wait for Zee on TWO Thurston decisions (below). Do not proceed on Thurston without them.
- Blockers:
  1. BLOCKING — Reserve / carve-out conflict. Silver Falls (4200 Anini Vista Dr #D) and the Sundance Big Cabin are BOTH Reserve Sale Properties carrying "Mandatory acceptance of bona fide offers at or above Reserve Price — refusal is a Milestone Default", which cannot coexist with their new 90-day protection. It also strands the Day 90 milestone, since only 17 Dorado Beach Estates stays freely forceable. Three options are set out in CHANGE NOTE 20260728.md section 2.1; option 3 (start mandatory acceptance at Day 91) is most internally consistent but is NOT applied. Needs Zee's business call.
  2. Confirm "Sundance Big Cabin" = 3060 E Deer Run Rd ($7,000,000), not 3093 E Deer Run Rd ($5,000,000). Assumption only, based on Tyler Corbridge's "$7 million" remark on the 2026-07-20 call.
  3. Mountain West Pest: the diligence request list at "~/Documents/OKOA/Mountain West Pest Diligence/Diligence Request List - Blocking Items - 2026-07-28.md" is COMPLETE but NOT SENT. Open question for Zee: keep the framing at $1.5M-$2.0M or revert to the borrower's $5,000,000 pending their confirmation.
  4. Ascent entity register is complete but was verified structurally only — never opened in Excel to check formatting.

Key facts to carry forward:
- Zee CONFIRMED "Anini big house" = 4200 Anini Vista Dr #D (Silver Falls, initial list $28,000,000). TRAP: the 2026-07-20 meeting used "the big house" for a DIFFERENT property (2818 Kamookoa Rd #1, $23,000,000). Team speech diverges from the document. Do NOT re-litigate — Zee decided.
- Boss instruction driving the Thurston change: "18% for the first month, 19% second month and then 20% thereafter. They deed all properties and list as previously planned but Wright wants a little flexibility on three properties for the first 90 days: Sundance big cabin, Charleston, and Anini big house."
- Pre-existing and unresolved: the term summary frames the rate as a FLOOR with 25% still accruing; the memo frames it as an effective STEP-DOWN. Different mechanics, same deal point. Needs counsel, not a drafting fix.
- render-deck.mjs exists because ~/.claude/scripts/html-to-pdf.js forces Letter, adds a page footer, and never sets preferCSSPageSize — that letterboxed the 16:9 deck. Use render-deck.mjs for the deck and the term summary; use html-to-pdf.js for the memo.
- Ascent register: 184 records (73 person / 62 entity / 49 asset), zero rows without provenance, scope PRE-LOAN only (post-2024-02-09 meetings still unauthorised).
- Mountain West Pest headline: ask collapsed $5,000,000 -> $1-2M; churn admitted at 15-20%/yr against a 0.5%/month claim; 4 of 9 blocking items never raised on the call; peak-season (March-August 2025) bank statements still missing.
- NOTHING from this session belongs in the ACOS 3.0 git repo. Its ~190 modified files are unrelated leftovers from other sessions (research-riffs, axiom-synthesis, Website Builder PRD, resurrection scripts). Do not conflate.
- Memory gap noted: the Thurston memo was built in a PRIOR session and did not surface in this session's memory index. Worth a memory entry.

This prompt was auto-injected after /clear ran. The user has not typed anything
since. Read the handoff document and continue the prior work seamlessly.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `551301a42576`
- uncommitted changes: 190 file(s)

Uncommitted working-tree files (these are in NO handoff — inspect FIRST):
```
 M .DS_Store
 M .claude/scripts/acos-token-monitor-bin-reference/token-watcher.py
 M .claude/scripts/eternity-protocol-core.sh
 M .claude/scripts/eternity-resume-prepend.sh
 M .claude/scripts/run-external-agent.py
 M .claude/scripts/session-cleanup.sh
 M .claude/skills/.DS_Store
 M .claude/skills/acos-axiom-synthesis/SKILL.md
 M .claude/skills/acos-axiom-synthesis/prompts/README.md
 M .claude/skills/acos-axiom-synthesis/scripts/orchestrate.py
 M .claude/skills/acos-complete/SKILL.md
 M .claude/skills/acos-deep-research/SKILL.md
 M .claude/skills/acos-investment-committee/scripts/committee-room/meeting_template.html
 M .claude/skills/acos-research-riffs/SKILL.md
 M .claude/skills/acos-research-riffs/agents/riff-researcher.md
 M .claude/skills/acos-research-riffs/scripts/lib/claims.ts
 M .claude/skills/acos-research-riffs/scripts/lib/coverage.ts
 M .claude/skills/acos-research-riffs/scripts/lib/ledger.ts
 M .claude/skills/acos-research-riffs/scripts/lib/panel.ts
 M .claude/skills/acos-research-riffs/scripts/lib/report.ts
 M .claude/skills/acos-research-riffs/scripts/lib/room.ts
 M .claude/skills/acos-research-riffs/scripts/lib/session.ts
 M .claude/skills/acos-research-riffs/scripts/lib/tree.ts
 M .claude/skills/acos-research-riffs/scripts/lib/util.ts
 M .claude/skills/acos-research-riffs/scripts/riff-live.ts
 M .claude/skills/acos-research-riffs/scripts/riff-server.ts
 M .claude/skills/acos-research-riffs/scripts/riff.ts
 M .claude/skills/acos-research-riffs/scripts/room/room.html
 M .claude/skills/acos-research-riffs/scripts/test-riff.ts
 M .claude/skills/acos-research-riffs/templates/auditor-charter.md
 M .claude/skills/acos-research-riffs/templates/citer-charter.md
 M .claude/skills/acos-research-riffs/templates/dimensions-example.json
 M .claude/skills/acos-research-riffs/templates/eval-rubric.md
 M .claude/skills/acos-research-riffs/templates/panel-example.json
 M .claude/skills/acos-research-riffs/templates/probe-charter.md
 M .claude/skills/acos-xl-update/SKILL.md
 M .claude/skills/document-processing/SKILL.md
 M .claude/skills/knowledge-graph/SKILL.md
 M .claude/skills/prism-research/SKILL.md
 M "Website Builder/DECISIONS.md"
 M "Website Builder/INDEX.md"
 M "Website Builder/memory/handoffs/closed/2026-07-26-Website-builder-close/2026-07-26-Website-builder-close.reentry.md"
 M "Website Builder/memory/handoffs/closed/2026-07-26-Website-builder-close/handoff.yaml"
 M "Website Builder/prd/OPEN-ITEMS.md"
 M memory/handoffs/2026-06-16-emergency-handoff.resume.md
 D memory/handoffs/2026-06-16-emergency-handoff.yaml
 D memory/handoffs/2026-06-21-emergency-handoff.yaml
 M package.json
 M planning/acos-axiom-synthesis/PLAN.md
 M planning/acos-research-riffs/ARCHITECTURE.md
?? .claude/agents/rc-capture-orchestrator.md
?? .claude/agents/rc-cut-defender.md
?? .claude/agents/rc-fusion-synthesizer.md
?? .claude/agents/rc-intent-extractor.md
?? .claude/agents/rc-intent-qa.md
?? .claude/agents/rc-intent-synthesizer.md
?? .claude/agents/rc-prd-drafter.md
?? .claude/agents/rc-prd-synthesizer.md
?? .claude/agents/rc-prioritizer.md
?? .claude/agents/rc-rebuild-proposer.md
?? .claude/agents/rc-red-team.md
?? .claude/agents/rc-spec-wall.md
?? .claude/scripts/.DS_Store
?? .claude/skills/acos-axiom-synthesis/config/
?? .claude/skills/acos-axiom-synthesis/prompts/elicitor.md
?? .claude/skills/acos-axiom-synthesis/prompts/grader.md
?? .claude/skills/acos-axiom-synthesis/prompts/refuter.md
?? .claude/skills/acos-axiom-synthesis/prompts/synthesizer.md
?? .claude/skills/acos-axiom-synthesis/scripts/checklist.py
?? .claude/skills/acos-axiom-synthesis/tests/test_checklist.py
?? .claude/skills/acos-research-riffs/.DS_Store
?? .claude/skills/acos-reverse-cleanroom/
?? .claude/skills/acos-skill-breakdown/
?? .omx/
?? "Logo Builder/"
?? "Website Builder/planning/"
?? "Zermatt Credit Memo/"
?? bun.lock
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
?? memory/handoffs/2026-07-22-emergency-handoff-2.resume.md
?? memory/handoffs/2026-07-22-emergency-handoff-2.yaml
?? memory/handoffs/2026-07-22-emergency-handoff.resume.md
?? memory/handoffs/2026-07-22-emergency-handoff.yaml
?? memory/handoffs/2026-07-23-emergency-handoff-2.resume.md
?? memory/handoffs/2026-07-23-emergency-handoff-2.yaml
?? memory/handoffs/2026-07-23-emergency-handoff.resume.md
?? memory/handoffs/2026-07-23-emergency-handoff.yaml
?? memory/handoffs/2026-07-24-emergency-handoff.resume.md
?? memory/handoffs/2026-07-24-emergency-handoff.yaml
?? memory/handoffs/2026-07-25-emergency-handoff-2.resume.md
?? memory/handoffs/2026-07-25-emergency-handoff-2.yaml
?? memory/handoffs/2026-07-25-emergency-handoff.resume.md
?? memory/handoffs/2026-07-25-emergency-handoff.yaml
?? memory/handoffs/2026-07-27-emergency-handoff-2.resume.md
?? memory/handoffs/2026-07-27-emergency-handoff-2.yaml
?? memory/handoffs/2026-07-27-emergency-handoff.resume.md
?? memory/handoffs/2026-07-27-emergency-handoff.yaml
?? memory/handoffs/2026-07-28-emergency-handoff.yaml
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
?? planning/acos-research-riffs/RECENCY-DESIGN-PROPOSAL.md
?? planning/acos-research-riffs/REVIEW-2026-07-25.md
?? planning/acos-research-riffs/REVIEW-2026-07-27.md
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
551301a feat(website-builder): promote the PRD out of swarm scratch into a real project
88c1597 feat(resurrection): adopt-in-place — a pick lands in the tab it was typed in
d5f352a feat(research-riffs): live responder — seats answer on their own in ~5-7s
42fdc51 fix(research-riffs): room now reuses IC's real committee-room page
f435d3e feat(research-riffs): verify-first guardrails + IC-style live room
1c127b4 feat(resurrection): sidebar-name-first identity + global resurrect skill
7080062 fix(eternity+resurrection): post-clear misfire guard + safe-close session identity
cc62ecd feat(investment-committee): live pool-backed committee room, 8 tooled seats, reading-level dial
```

**Drift check:** if `git rev-parse --short=12 HEAD` no longer equals `551301a42576`, or the working tree is dirty, RECONCILE from `git log` / `git status` / `git diff` before trusting any "completed / all committed" claim in the handoff above. (This session learned the hard way: a 2026-06-24 resume arrived 3 commits + 1 uncommitted method stale.)
