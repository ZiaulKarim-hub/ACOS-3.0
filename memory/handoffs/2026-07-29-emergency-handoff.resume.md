Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `/Users/zee/Documents/Vibe Coding/ACOS 3.0/memory/handoffs/2026-07-29-emergency-handoff.yaml` for full session state.

Quick summary:
- Working on: Ascent / Wolfgramm misrepresentation evidence for OKOA — a personal-financial-statement (PFS) completeness audit plus a 73-episode podcast corpus, both now filed in Dropbox "External Data Rooms -- EXTERNALLY SHARED/Phil Wolfgramm Lawsuit/".
- Last action: OCR'd every scanned file the text audit could not read (335 unique PDFs / 4,665 pages, plus 138 unique images). Seven files scored; all seven were reviewed and are NOT personal financial statements. David Tafuna — one of the four individual Ascent guarantors — still has NO PFS anywhere.
- Next step: fix the Dropbox "Phil Wolfgramm Lawsuit" folder inconsistency. Its README lists artifacts that the folder move left behind ("statement-ledger (machine-readable).json" and "build (reproducible source)/"). Either copy them in from the local working copies, or correct the README. Do this BEFORE anyone outside the firm is pointed at that folder. Ask Zee which he wants.
- Blockers:
  1. (highest) The Dropbox folder above is inconsistent with its own documentation.
  2. The draft email to the legal team about that folder exists only in the prior chat, never saved to disk — redraft it from MANIFEST.md if it cannot be recovered. It must keep the "ONE GAP WORTH FLAGGING" paragraph covering the OCR results and the David Tafuna gap.
  3. Zee has not decided whether to publish the unpublished XL Ant 20260726 draft alongside the new 20260802 draft (the Dropbox published series still ends at 20260719). Both drafts are in /Users/zee/Documents/OKOA/XL Ant Weekly Update Draft.
  4. CARRIED OVER AND STILL BLOCKING: Zee has not picked option 1, 2 or 3 for the Thurston Reserve/carve-out conflict in /Users/zee/Documents/OKOA/Thurston Memo/CHANGE NOTE 20260728.md section 2.1. No Thurston workout document goes out until he decides.

Key facts to carry (verified this session, do not re-derive):
- 4 individual Ascent guarantors per the executed guaranties: Philip Wolfgramm, Koloa Wolfgramm, David Tafuna, Russell Handy. Only 3 have a PFS. Searched 12 Ascent roots / 4,685 readable files + 4,665 OCR'd pages.
- Podcast corpus: 73 episodes, 677 minutes, 150,472 words. Report "Koloa Wolfgramm Public Statement Record.pdf" = 15 pages, 25 statements, 25/25 verified verbatim and at-timestamp.
- Every figure in that report is a MACHINE transcription and must be confirmed by ear at its timestamp before anyone relies on it. That confirmation pass has NOT been done.
- Build scripts: /Users/zee/Documents/OKOA/Ascent Podcast Search/build/ and /Users/zee/Documents/OKOA/Ascent PFSs/audit/

This prompt was auto-injected after /clear ran. The user has not typed anything
since. Read the handoff document and continue the prior work seamlessly.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `551301a42576`
- uncommitted changes: 194 file(s)

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
 M .claude/skills/acos-safe-close/SKILL.md
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
?? .claude/scripts/git-manager/
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
?? memory/handoffs/2026-07-28-emergency-handoff.resume.md
?? memory/handoffs/2026-07-28-emergency-handoff.yaml
?? memory/handoffs/2026-07-29-emergency-handoff.yaml
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
