# SLICE-40-dr1 — DR-1 ship gate: one recorded close->resume round-trip on a real project
**Epic EPIC-4 / Story STORY-4.1 — Demo: Demo 3 (DR-1 SHIP GATE)**
_Vertical value:_ Permission-to-close is the product and it must be a demonstration, not a promise; one silent loss ends the tool.

## PM (Planner / Specifier) — Lean Context Engineering
**Single objective:** DR-1 ship gate: one recorded close->resume round-trip on a real project

**In scope:**
- Full cycle: /acos-safe-close -> receipt SAFE TO CLOSE THIS TAB -> tab gone -> later /acos-resurrect -> pick -> work demonstrably continues -> USER confirms continuity
- Save the recording/receipts to .acos/evidence/

**Out of scope (guardrails):**
- Shipping on a promise/placebo
- Any step that is not on a real project

**Allowed files / contexts:** A real project; /acos-safe-close then later /acos-resurrect; .acos/evidence/ for the recording.

**Definition of Done:** all acceptance criteria below pass; required artifacts written under the repo path; the evidence bundle at `.acos/evidence/[DATE]/SLICE-40-dr1/` is populated; `## Dev Learnings` and `## QA Learnings` are updated (a slice is not Done until they are — §0.7).

## Dev (Executor) — steps + 7-part Evidence Bundle
**Steps (execute EXACTLY; no scope expansion, only allowed files):**
- Run the full cycle on a real project.
- Capture the recording and receipts.
- Obtain explicit user confirmation of continuity.

**Evidence Bundle to produce:** 1) Implementation Summary; 2) Requirements Traceability (to spec FR-* / tech_prd TR-*); 3) Structural Quality Evidence; 4) Functional/structural checks (the verification method below); 5) Security/Compliance notes; 6) Operational/Runtime considerations; 7) Self-assessment (confidence + known limitations).

## QA (Zero-Trust Verifier)
Assume the Dev did **not** do the work correctly. Verify scope respect, evidence authenticity (no fabricated logs — spot-check and recompute), and that every acceptance criterion + evidence gate is satisfied. QA may **REJECT** and require rework until the gates pass (a reject blocks the slice like an INCONCLUSIVE reviewer).

**QA checks:**
- Confirm the round-trip was on a REAL project, not a throwaway
- Confirm continuity was USER-confirmed, not self-asserted
- Confirm the recording is archived; if any piece is missing, the gate is NOT met and nothing ships

## Definition of Done (maps to ACOS `slice.yaml`)
**acceptance_criteria:**
- A real project: receipt SAFE, tab gone, later resume, work demonstrably continues, USER confirms continuity
- Recording/receipts archived to .acos/evidence/
- Until this exists, the skill is NOT shipped

**verification_method:** The full recording + receipts archived; the user's explicit continuity confirmation captured.

**evidence bundle:** `.acos/evidence/[DATE]/SLICE-40-dr1/`

## Dev Learnings
_(fill at execution — the slice is NOT Done until this is updated: what worked, what surprised, what to reuse.)_

## QA Learnings
_(fill at execution — the slice is NOT Done until this is updated: what nearly slipped through, which check caught it, what to harden.)_
