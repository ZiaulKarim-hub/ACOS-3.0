# SLICE-F1-guardrails-governance — Guardrail suite + autopilot pre-flight assertion + governance

**Parent story:** STORY-F1 · **Epic:** EPIC-F · **Effort:** M · **Demo:** post-demo hardening
**slice.yaml mapping:** Objective->`objective`; Allowed files->`files_allowed`;
DoD+evidence gates->`acceptance_criteria`; QA verification->`verification_method`.

## PM (Planner / LCE brief)

**Objective (single, narrow):** Mechanically enforce the anti-groupthink guardrail suite and an
autopilot-active pre-flight assertion so accuracy rests on structure, not persona: independence
enforcement, kill criteria FIRST, anti-sycophancy schema, 10th-man on lopsided distribution,
reduced-independence flag, and an autopilot pre-flight ABORT (no fallback branch).

**In-scope:** `guardrails.py` — (1) independence enforcement (assert no cross-seat context in
round 0); (2) `kill_criteria.py` run FIRST before any narrative mitigant reasoning (override =
separately-logged policy exception); (3) anti-sycophancy schema: forbid agreement without a
named new fact, use *derived* (not self-reported) confidence, hide mid-debate numeric
confidence; (4) consensus-triggered 10th-man contrarian pass on a lopsided approve-leaning
distribution; (5) `reduced_independence` flag when single-provider; (6) autopilot pre-flight
assertion: `test -f .acos/state/autopilot-active` at Mode B entry -> if the file exists, ABORT
immediately with a clear message and take NO fallback action (no batch mode, no degraded-pause
path) — the user is expected to guarantee autopilot is off before running Mode B; (7) per-slice
evidence-bundle convention. Standing hole-checklist (concentration, leverage exceptions,
statement veracity, tenant concentration, refi/maturity) explicitly cleared.

**Out-of-scope:** the seats (A2), the tally (D2), synthesis (C2/C3) — this slice enforces
around them.

**Allowed files/contexts:** `scripts/guardrails.py`, `scripts/kill_criteria.py`; SKILL.md
guardrail hooks; READ-ONLY: spec FR-M20/M21 + FR-S1/S3/S8/S9, domain-lattice
`proc-autopilot-detection` + `method-kill-criteria` + `method-devils-advocate` +
`anti-sycophancy` + `metric-independence-flag`, CLAUDE.md autopilot notes.

**Step-by-step:**
1. Independence enforcement assertion (fails the run if any round-0 seat context contained a
   sibling output).
2. `kill_criteria.py` runs FIRST; a kill match short-circuits to a logged deal-breaker;
   override requires an explicit policy-exception log entry.
3. Anti-sycophancy schema hooks; 10th-man trigger on lopsided distribution; reduced-independence
   flag; the autopilot pre-flight assertion (hard ABORT, no fallback branch); standing
   hole-checklist clearance.

**Definition of Done:**
- Artifacts: `scripts/guardrails.py`, `scripts/kill_criteria.py`; SKILL.md hooks; a
  guardrail-fixture proof set.
- Validation: a cross-seat-context fixture is REJECTED by independence enforcement; kill
  criteria run before mitigant reasoning; a lopsided approve fixture triggers the 10th-man; a
  single-provider run sets the flag; with `autopilot-active` present, Mode B entry ABORTS
  immediately with a clear message and executes NO fallback branch (no batch mode, no menu is
  ever shown); the standing hole-checklist is explicitly cleared.
- Evidence bundle: each guardrail's fire/no-fire transcript + the autopilot pre-flight-abort
  proof.

## Dev (Executor)

**Execution notes:** guardrails are ASSERTIONS, not advice — a violated guardrail fails the
run. The autopilot check is a simple pre-flight assertion, not a mode-detection branch — it has
exactly one behavior (abort) and no fallback code path to test beyond that. subscription-only.

**Evidence Bundle:** 1) Summary; 2) Traceability (FR-M20, FR-M21, FR-S1, FR-S3, FR-S8, FR-S9);
3) Quality (each guardrail unit-fixture); 4) Testing (fire/no-fire transcripts + autopilot
pre-flight-abort proof); 5) Compliance (kill-criteria-first; autopilot abort has no fallback);
6) Operational; 7) Self-assessment.

## QA (Zero-Trust Verifier)

Verify each guardrail by trying to BREAK it: (a) feed a cross-seat-context round-0 and confirm
independence enforcement rejects it; (b) confirm `kill_criteria.py` runs before any mitigant
reasoning (ordering check) and that an override leaves a logged policy exception; (c) feed a
lopsided approve distribution and confirm the 10th-man fires; (d) force single-provider and
confirm the flag; (e) create `.acos/state/autopilot-active` and confirm Mode B entry ABORTS
immediately with a clear message and that NO fallback branch (batch mode or otherwise)
executes; (f) confirm the standing hole-checklist cannot be silently skipped. Reject if any
guardrail can be bypassed or if the autopilot check takes any action other than a clean abort.

**Evidence gates:** independence rejection fires; kill-criteria-first; 10th-man fires; flag
correct; autopilot pre-flight ABORT with zero fallback behavior; hole-checklist enforced.

## Dev Learnings
_(fill: autopilot state-file detection reliability; kill-criteria ordering.)_

## QA Learnings
_(fill: any bypassable guardrail; confirmation that no fallback code path exists for the
autopilot check.)_
