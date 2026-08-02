# SLICE-00-probe — cmux 0.64.19 probe battery + DP2 sacrificial tests
**Epic EPIC-0 / Story STORY-0.1 — Demo: Diagnostic (blocks all builds)**
_Vertical value:_ Settles the UNVERIFIED platform behaviors every downstream guard depends on; without it the close skill cannot ship.

## PM (Planner / Specifier) — Lean Context Engineering
**Single objective:** cmux 0.64.19 probe battery + DP2 sacrificial tests

**In scope:**
- in-pane hook firing on 0.64.19 (#5427 regression class)
- rpc workspace.list JSON shape; workspace list --json
- new-workspace --name/--description/--cwd/--command round-trip; --description verbatim round-trip
- rpc workspace.select focus behavior
- DP2: workspace.close against a live sacrificial Claude session; last-workspace-in-window close; customDescription survival across one controlled restart; DP4 hibernation on a throwaway

**Out of scope (guardrails):**
- Any registry/close/menu code
- Enabling auto-naming (DP3 stays OFF)
- Any write to the daemon state dir

**Allowed files / contexts:** Throwaway RESURRECTION-PROBE-* workspaces; read-only reads of the daemon state dir; .acos/evidence/2026-07-16/resurrection-phase0/. No production scripts.

**Definition of Done:** all acceptance criteria below pass; required artifacts written under the repo path; the evidence bundle at `.acos/evidence/2026-07-16/resurrection-phase0/` is populated; `## Dev Learnings
### 2026-07-18 build run (non-disruptive scope)
- This session itself runs inside cmux 0.64.19 — hook firing (#5427 class) was proven from the session's OWN SessionStart/watcher artifacts; no sacrificial session needed.
- Canonical close verb is `cmux workspace close <ws>` (rpc `workspace.close`); `workspace-action` has NO plain close (only close-others/above/below).
- Description round-trips verbatim incl. em-dash, `[key:...]`, quotes, unicode. Creation does not steal focus. Shell-only close is silent and keeps focus.
- Refs renumber across lifecycle (new ws got `workspace:8` in a 6-ref window) — never persist refs.
- Capabilities now 260 methods; surface.resume.get/set/clear + session.restore_previous present but behavior unprobed.
` and `## QA Learnings
### 2026-07-18 build run (non-disruptive scope)
- All archived outputs are raw `tee` captures; spot-checked DESCRIPTION VERBATIM MATCH computed by python equality, not eyeballed.
- Probe workspace verified closed (count 5->4, list re-read). Daemon state dir: read-only (ls/cat only).
- DEFERRED (DP2/DP4): live-close prompt, last-workspace close, description restart survival, hibernation — Phase-2 guards stay fail-closed until answered.
` are updated (a slice is not Done until they are — §0.7).

## Dev (Executor) — steps + 7-part Evidence Bundle
**Steps (execute EXACTLY; no scope expansion, only allowed files):**
- Open a throwaway Claude session in a new cmux pane; confirm SessionStart/UserPromptSubmit/Stop hook artifacts appear (read-only daemon-dir check + in-session context injection).
- Run the CLI battery on throwaway workspaces; paste each command output.
- DP2-gated disruptive tests at a user-scheduled moment; record whether workspace.close prompts.
- Archive every pasted output; close each probe workspace after.

**Evidence Bundle to produce:** 1) Implementation Summary; 2) Requirements Traceability (to spec FR-* / tech_prd TR-*); 3) Structural Quality Evidence; 4) Functional/structural checks (the verification method below); 5) Security/Compliance notes; 6) Operational/Runtime considerations; 7) Self-assessment (confidence + known limitations).

## QA (Zero-Trust Verifier)
Assume the Dev did **not** do the work correctly. Verify scope respect, evidence authenticity (no fabricated logs — spot-check and recompute), and that every acceptance criterion + evidence gate is satisfied. QA may **REJECT** and require rework until the gates pass (a reject blocks the slice like an INCONCLUSIVE reviewer).

**QA checks:**
- Re-open the archived outputs and confirm they are real pastes, not composed summaries
- Confirm no probe workspace was left open
- Confirm the daemon state dir was only read, never written
- Confirm every UNVERIFIED item in tech_prd §6 is now answered or explicitly still-open

## Definition of Done (maps to ACOS `slice.yaml`)
**acceptance_criteria:**
- In-pane hook firing on 0.64.19 observed and archived
- rpc workspace.list JSON shape captured; text form never parsed
- --description verbatim round-trip captured
- workspace.select focus behavior recorded
- DP2 results (live-close prompt?, last-workspace behavior, customDescription restart survival) recorded and used to parameterize the Phase-2 guards

**verification_method:** Pasted command outputs archived to .acos/evidence/2026-07-16/resurrection-phase0/; each probe workspace closed after; written answers for the DP2 questions.

**evidence bundle:** `.acos/evidence/2026-07-16/resurrection-phase0/`

## Dev Learnings
_(fill at execution — the slice is NOT Done until this is updated: what worked, what surprised, what to reuse.)_

## QA Learnings
_(fill at execution — the slice is NOT Done until this is updated: what nearly slipped through, which check caught it, what to harden.)_
