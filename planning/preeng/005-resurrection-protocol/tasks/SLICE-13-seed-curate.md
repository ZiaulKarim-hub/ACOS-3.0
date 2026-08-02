# SLICE-13-seed-curate — Seed + one ~10-minute human curation pass (DP5)
**Epic EPIC-1 / Story STORY-1.1 — Demo: Demo 1 (enrollment)**
_Vertical value:_ Day-one value covering everything; a human confirms each row is a real project (explicit enrollment spirit).

## PM (Planner / Specifier) — Lean Context Engineering
**Single objective:** Seed + one ~10-minute human curation pass (DP5)

**In scope:**
- Run the seeder
- One ~10-min human curation pass; junk/anomaly rows tombstoned by hand

**Out of scope (guardrails):**
- Any age-based reaper
- Auto-deletion of rows (deletion is a human act only)

**Allowed files / contexts:** The seeder (rebuild-registry.py) + the menu for tombstoning. Human curation only for deletions.

**Definition of Done:** all acceptance criteria below pass; required artifacts written under the repo path; the evidence bundle at `.acos/evidence/[DATE]/SLICE-13-seed-curate/` is populated; `## Dev Learnings

### 2026-07-18 build run
- Seeded 21/22 candidates (anomaly excluded); okoa-website worktrees appear only as hint-only paths — worktree dirs carry no markers, which is the correct outcome.
` and `## QA Learnings

### 2026-07-18 build run
- Post-apply verification = row count + audit JSONL validity + field-checked sample; curation intentionally NOT automated (deletion is a human act).
` are updated (a slice is not Done until they are — §0.7).

## Dev (Executor) — steps + 7-part Evidence Bundle
**Steps (execute EXACTLY; no scope expansion, only allowed files):**
- Run the seeder to populate the book.
- Curate: tombstone junk/anomaly rows by hand.

**Evidence Bundle to produce:** 1) Implementation Summary; 2) Requirements Traceability (to spec FR-* / tech_prd TR-*); 3) Structural Quality Evidence; 4) Functional/structural checks (the verification method below); 5) Security/Compliance notes; 6) Operational/Runtime considerations; 7) Self-assessment (confidence + known limitations).

## QA (Zero-Trust Verifier)
Assume the Dev did **not** do the work correctly. Verify scope respect, evidence authenticity (no fabricated logs — spot-check and recompute), and that every acceptance criterion + evidence gate is satisfied. QA may **REJECT** and require rework until the gates pass (a reject blocks the slice like an INCONCLUSIVE reviewer).

**QA checks:**
- Confirm tombstoned rows still exist on disk (tombstone-never-delete)
- Confirm no row was auto-deleted

## Definition of Done (maps to ACOS `slice.yaml`)
**acceptance_criteria:**
- Book lists the real active projects
- Anomaly rows (incl. the Vibe Coding-root row) tombstoned, not deleted

**verification_method:** Before/after row listing archived; tombstone events visible in the audit log.

**evidence bundle:** `.acos/evidence/[DATE]/SLICE-13-seed-curate/`

## Dev Learnings
_(fill at execution — the slice is NOT Done until this is updated: what worked, what surprised, what to reuse.)_

## QA Learnings
_(fill at execution — the slice is NOT Done until this is updated: what nearly slipped through, which check caught it, what to harden.)_
