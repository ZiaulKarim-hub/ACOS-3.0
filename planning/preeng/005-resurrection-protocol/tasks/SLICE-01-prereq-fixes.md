# SLICE-01-prereq-fixes — Close the pre-existing bugs the registry would make routine
**Epic EPIC-0 / Story STORY-0.1 — Demo: Diagnostic (blocks all builds)**
_Vertical value:_ Fixes residual #10 BEFORE the registry makes two-panes-one-project routine; removes two live silent-failure sources.

## PM (Planner / Specifier) — Lean Context Engineering
**Single objective:** Close the pre-existing bugs the registry would make routine

**In scope:**
- Pane-scope or remove the pane-blind tier-3 resume at eternity-resume-prepend.sh:158-169
- Fix head -40 silent truncation at eternity-protocol-core.sh:139 in repo copy AND the byte-identical bin twin; regenerate the bin-manifest
- Make token-watcher.py:1113 orphan-surface branch fail CLOSED; regenerate the bin-manifest
- 0.6 provenance of the 147 /acos-complete runs (hand vs hook)
- 0.7 --command internal-handling probe; optional 0.8 archive-project.sh --yes

**Out of scope (guardrails):**
- Any registry/close/menu code
- Deleting or moving pending-resume-*.txt / RESCUED-resume-*.txt
- Touching register-session-pid.sh or the rest of the token-monitor bin

**Allowed files / contexts:** .claude/scripts/eternity-resume-prepend.sh; .claude/scripts/eternity-protocol-core.sh + its byte-identical Application Support bin twin + bin-manifest; ~/Library/Application Support/acos-token-monitor/bin/token-watcher.py + bin-manifest; optionally archive-project.sh.

**Definition of Done:** all acceptance criteria below pass; required artifacts written under the repo path; the evidence bundle at `.acos/evidence/2026-07-16/resurrection-phase0/prereq-fixes/` is populated; `## Dev Learnings

### 2026-07-18 build run
- The Application Support copy of eternity-protocol-core.sh is a SYMLINK to the repo file — edit once, both sides move; manifest hashes the resolved content.
- Pane gate implemented fail-CLOSED for Warp (empty CMUX_SURFACE_ID skips tier-3 entirely); Warp's primary path is the manual resume skill.
` and `## QA Learnings

### 2026-07-18 build run
- Never run eternity-protocol-core.sh end-to-end as a test — it arms a real resume cycle; verify its blocks in standalone simulation.
- Running daemons keep the old watcher code until natural replacement; note the code/runtime split in any watcher fix.
` are updated (a slice is not Done until they are — §0.7).

## Dev (Executor) — steps + 7-part Evidence Bundle
**Steps (execute EXACTLY; no scope expansion, only allowed files):**
- Edit eternity-resume-prepend.sh path (3) to be pane-scoped or removed; simulate two sessions on one project and confirm session B is never offered session A's resume.
- Fix head -40 in BOTH copies (list all, or print an explicit '... (listed 40 of N - TRUNCATED)' line); regenerate the bin-manifest.
- Make the orphan-surface branch fail CLOSED; regenerate the bin-manifest; confirm renaming/restoring the 90-byte marker no longer re-arms fail-open.
- Grep settings + registered hooks for automation invoking acos-complete; write the provenance answer.
- Probe --command with '; touch /tmp/resurrection-cmd-probe;'; document shell-parse vs exec.

**Evidence Bundle to produce:** 1) Implementation Summary; 2) Requirements Traceability (to spec FR-* / tech_prd TR-*); 3) Structural Quality Evidence; 4) Functional/structural checks (the verification method below); 5) Security/Compliance notes; 6) Operational/Runtime considerations; 7) Self-assessment (confidence + known limitations).

## QA (Zero-Trust Verifier)
Assume the Dev did **not** do the work correctly. Verify scope respect, evidence authenticity (no fabricated logs — spot-check and recompute), and that every acceptance criterion + evidence gate is satisfied. QA may **REJECT** and require rework until the gates pass (a reject blocks the slice like an INCONCLUSIVE reviewer).

**QA checks:**
- Confirm the bin twin and repo copy are byte-identical after the head -40 fix and the manifest was regenerated (doc-drift lesson)
- Confirm no pending-resume-*.txt / RESCUED-resume-*.txt was deleted or moved (diff)
- Re-run the residual #10 simulation independently
- Confirm token-watcher.py now fails CLOSED, not merely 'looks fixed'

## Definition of Done (maps to ACOS `slice.yaml`)
**acceptance_criteria:**
- With two sessions on one project, session B is never offered session A's resume via path (3) (transcript archived)
- A handoff generated now lists count == git status --porcelain | wc -l, or prints the explicit truncation line; both copies fixed; bin-manifest regenerated
- A surface-less artifact is now REJECTED by the gate; the marker rename/restore no longer re-arms fail-open; bin-manifest regenerated
- 147-run provenance answer written to evidence (adjust adoption expectation if hook-fired)
- --command shell-parse-vs-exec result documented

**verification_method:** Archived before/after transcripts for each fix; git diff of the two repo-tracked scripts; bin-manifest regen confirmed; pending-resume population unchanged (diff).

**evidence bundle:** `.acos/evidence/2026-07-16/resurrection-phase0/prereq-fixes/`

## Dev Learnings
_(fill at execution — the slice is NOT Done until this is updated: what worked, what surprised, what to reuse.)_

## QA Learnings
_(fill at execution — the slice is NOT Done until this is updated: what nearly slipped through, which check caught it, what to harden.)_
