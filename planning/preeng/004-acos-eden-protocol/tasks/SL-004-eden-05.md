# SL-004-eden-05 — Fidelity Floor & exempt-content classifier

**Story:** ST-004-eden-3 · **Epic:** EP-004-eden-3 · **Demo:** 2 · **Effort:** L · **Priority:** P0

## PM (Planner / LCE)
- **Objective (single):** Encode the 8-invariant Fidelity Floor and the exempt-content rules so no
  simplification can corrupt protected content.
- **In-scope:** the 8 invariants in SKILL.md + the directive; the exempt-content classes (data-model
  E3); optional stdlib helper for QA-time detection.
- **Out-of-scope:** the reading-level engine (SL-07) — this slice only guarantees fidelity, not register.
- **Allowed files:** `~/.claude/skills/acos-eden-protocol/SKILL.md`, optional
  `.claude/scripts/eden-exempt-check.py` (QA helper).
- **Definition of Done:** on a finance-flavored test battery (exact figures, a pending-lien caveat, a
  shell command, a legal term, a citation), a simplified answer preserves every one verbatim; confidence
  never inflated; no added claims; never re-simplifies a prior simplified answer.

## Dev — Evidence Bundle
1. Invariants + exempt classes as encoded. 2. Traceability (M6, S-fidelityfloor). 3. Test battery with
before/after showing each protected span survived. 4. Negative test: an attempted over-simplification is
caught. 5. Runtime notes. 6. Self-assessment (esp. classifier gaps). 7. Limitations.

## QA (Zero-Trust) — this is the gate that underwrites the 0-violation metric
- Independently run the finance battery; recompute that every number/caveat/exempt span is byte-for-byte.
- Probe edge cases: a rounded number, a dropped "subject to", a paraphrased "fee simple".
- **Evidence gates:** ANY fidelity violation = REJECT. Classifier heuristic gaps must be documented.

## Dev Learnings
_(to be filled)_

## QA Learnings
_(to be filled)_
