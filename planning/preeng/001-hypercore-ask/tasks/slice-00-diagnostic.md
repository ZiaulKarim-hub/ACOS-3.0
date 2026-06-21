# slice-00-diagnostic — Diagnostics + validation (problem-before-solution)

- **Parent story:** STORY-HCA-00 · **Parent epic:** EPIC-HCA-00 · **Demo:** Demo 0
- **Effort:** S · **Dependency order:** 1 · **Depends on:** (none)
- **Lattice refs:** risk-aggerr, risk-truncation, risk-stale, anti-guess, meth-subonly, cq-10, cq-11, cq-15

## PM Section (Planner / Specifier — LCE)

### Objective
Confirm the trust-failure diagnosis and lock build ground rules **before** writing any solution code. Validate hypothesis **H1** (the dominant trust failure is aggregation / units / currency / silent-truncation errors that look plausible — not raw text fabrication), and record the Python 3 stdlib and stubbed-access decisions.

### Scope
**In scope:** a written diagnostic record (symptoms S1–S4, affected roles, current-vs-desired table, hypotheses H1–H3, unknowns U1–U5); a decision log entry confirming Python 3 stdlib and the stubbed-client-until-access ground rules; a gate-priority recommendation derived from H1.
**Out of scope:** any solution code, any adapter/cache/gate implementation, any Hypercore API call.

### Guardrails / Allowed files
- `planning/preeng/001-hypercore-ask/tasks/slice-00-diagnostic.md` (this file — update learnings)
- `.acos/evidence/[DATE]/slice-00-diagnostic/` (evidence bundle)
- `memory/decisions/` (one new decision record: Python 3 stdlib + stubbed-access ground rules)
- READ-ONLY refs: `spec.md`, `plan.md`, `tech_prd.md`, `data-model.md`, `domain-brief.md`, `research.md`
- Prohibited: writing any file under `.claude/skills/acos-hypercore-ask/` or `.claude/scripts/` in this slice.

### Definition of Done
- [ ] Diagnostic record produced covering symptoms, roles, current-vs-desired, hypotheses, unknowns — artifact: diagnostic section in this task's evidence bundle.
- [ ] H1 explicitly marked confirmed or still-`Assumption`; if still-Assumption, a validation hook is pointed at slice-11-completeness-hardening — pass-condition: H1 status recorded with rationale.
- [ ] Decision record written confirming **Python 3 stdlib only** (no third-party deps) and the **stubbed-client-until-access** ground rules — artifact: `memory/decisions/<id>-hca-build-ground-rules.md`.
- [ ] Gate-priority recommendation recorded (which gates are highest-leverage given H1) — pass-condition: ranked list present.
- [ ] `## Dev Learnings` and `## QA Learnings` updated (slice not Done otherwise).

## Dev Section (Executor)

### Approach
1. Read the upstream PRD/plan/research; extract symptoms, roles, hypotheses, unknowns into a single diagnostic record.
2. Evaluate H1 against the success metrics and risk register: confirm that reconciliation + completeness + adversarial recompute are higher-leverage than text-similarity checks; if evidence is insufficient, mark H1 `Assumption` and route validation to slice-11.
3. Write the decision record (Python 3 stdlib + stubbed-access ground rules), citing the plan-time decisions (OQ5, OQ1).
4. Produce a ranked gate-priority recommendation.
5. Assemble the 7-part evidence bundle.

### Dev Evidence Bundle (7 parts — required)
1. Implementation Summary · 2. Requirements Traceability (S1–S4, H1, OQ1/OQ5) · 3. Content Quality Evidence · 4. Structural checks (record completeness) · 5. Security/Compliance notes (none beyond no-PII-in-record) · 6. Operational considerations · 7. Self-assessment (confidence + limitations).

### Dev Learnings
- **H1 held for gate-ordering purposes (CONFIRMED), magnitude routed to slice-11.** The spec's
  own S2 names three of four failure modes (stale, silent-truncation, aggregation) inside the H1
  class, and the desired-state table already prescribes the H1 mitigations as the trust controls —
  so the *ranking* (reconciliation/completeness/freshness/normalization over text-similarity) is
  derivable from the spec without measuring live error rates. What we cannot confirm without the
  live API is the *relative magnitude* of each class; that stays `Assumption` and is validated in
  SLICE-HCA-11-completeness-hardening against real captured responses.
- **No unknown became blocking for the foundation.** U1 (API specifics) is the only one that gates
  real value, and the stubbed-client-until-access ground rule fully decouples it from the build:
  everything downstream depends on the adapter *contract*, not the live endpoint.
- **Decision record is the right home for the ground rules** (not the skill dir) — keeps slice-00
  scope-clean (zero files under `.claude/skills/` or `.claude/scripts/`) while still being the
  citable source slices 01/02 trace back to.
- Executed 2026-06-18 as part of the SLICE-HCA-00..02 foundation bundle; decision record:
  `memory/decisions/2026-06-18-hca-build-ground-rules.md`.

## QA Section (Zero-Trust Verifier)

### Verification steps
1. Confirm scope respected: NO files created under `.claude/skills/` or `.claude/scripts/`.
2. Independently re-derive symptoms/hypotheses from `spec.md` §Diagnostics; verify the record did not invent new claims.
3. Verify the decision record exists and unambiguously states Python 3 stdlib + stubbed-access.
4. Verify H1 status (confirmed vs Assumption) is justified and, if Assumption, validation is routed to slice-11.
5. Spot-check evidence bundle authenticity (no fabricated logs).

### Evidence gates (all must pass)
- [ ] No solution code written (scope) — fail = REJECT.
- [ ] Decision record present and concrete — artifact check.
- [ ] H1 status recorded with rationale + validation routing if Assumption.
- [ ] Gate-priority recommendation present and consistent with H1.
- [ ] Learnings updated.

### QA Learnings
- Re-derivation check: every symptom (S1–S4), hypothesis (H1–H3), and unknown (U1–U5) in the
  decision record is a verbatim-faithful restatement of `spec.md` §Diagnostics (lines 28–81) — no
  invented claims. The current-vs-desired table matches the spec table row-for-row.
- Scope check: zero files written under `.claude/skills/acos-hypercore-ask/` or `.claude/scripts/`
  for slice-00 — the only artifacts are the decision record under `memory/decisions/`, this
  learnings update, and the evidence bundle. Scope clean.
- H1-status check: the record marks H1 CONFIRMED for ordering but explicitly routes the magnitude
  validation to slice-11 with a stated rationale — acceptable per the "if still-Assumption, route
  validation" gate (it goes further: ranking confirmed, magnitude routed).
- Gate-priority list is present, ranked, and consistent with H1 (truncation/reconciliation/
  normalization/freshness lead; text-similarity trails).
