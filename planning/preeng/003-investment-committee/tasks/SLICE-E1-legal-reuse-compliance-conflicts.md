# SLICE-E1-legal-reuse-compliance-conflicts — Legal-analyst reuse + compliance companion + conflicts-disclosure

**Parent story:** STORY-E1 · **Epic:** EPIC-E · **Effort:** M · **Demo:** post-demo hardening
**slice.yaml mapping:** Objective->`objective`; Allowed files->`files_allowed`;
DoD+evidence gates->`acceptance_criteria`; QA verification->`verification_method`.

## PM (Planner / LCE brief)

**Objective (single, narrow):** Wire the Legal & Structural seat to **reuse** `legal-analyst`
via `/acos-legal-analysis --mode lending`, re-project `red-flags.yaml` into IC voting format,
run the compliance companion for legal-analyst's four gaps, and emit the per-run
`conflicts-disclosure.yaml`.

**In-scope:** `legal_seat.py` — dispatch legal-analyst; parse `findings-manifest.yaml` +
`red-flags.yaml`; map each red flag to an Objection (+ Axis S + deal-breaker-vs-curable per
spec Appendix D); the compliance companion (lender-side usury/licensing per-deal jurisdiction
check + Utah CFR; AML/KYC/OFAC/beneficial-ownership; structured foreclosure fields
`foreclosure_type/timeline_days/deficiency_available`; Phase I **ASTM E1527-21** currency
gate); `conflicts_disclosure.py` emitter.

**Out-of-scope:** rebuilding legal logic legal-analyst already covers (re-derivation is
forbidden); non-legal seats.

**Allowed files/contexts:** `scripts/legal_seat.py`, `scripts/conflicts_disclosure.py`;
READ-ONLY: `legal-analyst` agent + `/acos-legal-analysis` outputs, spec Appendix D/E,
domain-lattice `proc-legal-delegation` + `engine-legal-analyst` + `conflicts-disclosure` +
`std-astm-e1527` + `std-utah-cfr` + `std-sec-2026`. NOTE: `Assumption` — do NOT hardcode
Advisers Act / SPE-threshold rules; surface OKOA governance unknowns as gaps.

**Step-by-step:**
1. Dispatch `/acos-legal-analysis --mode lending`; ingest `red-flags.yaml` and re-project each
   into an Objection with Axis S + deal-breaker/curable classification (Appendix D).
2. Run the compliance companion covering the four gaps; per-deal jurisdiction check for
   usury/licensing (footprint marked `Assumption`).
3. Emit `conflicts-disclosure.yaml` (each seat discloses before voting; process attestations;
   reduced-independence flag).

**Definition of Done:**
- Artifacts: `scripts/legal_seat.py`, `scripts/conflicts_disclosure.py`; `conflicts-disclosure.yaml`
  + re-projected legal objections for a fixture.
- Validation: legal objections trace back to legal-analyst `red-flags.yaml` (no parallel
  re-derivation); the four compliance gaps each produce a check; Phase I currency gate flags a
  pre-2024-02-13 / E1527-13 report; governance unknowns are `Assumption`-marked not hardcoded;
  conflicts-disclosure.yaml emitted per run.
- Evidence bundle: legal delegation transcript + the four-gap checks + the conflicts artifact.

## Dev (Executor)

**Execution notes:** REUSE, don't rebuild — re-derivation of legal-analyst's framework is a
defect. subscription-only via Task()/skill dispatch. Do not confabulate OKOA registration
status.

**Evidence Bundle:** 1) Summary; 2) Traceability (FR-M15, FR-M16, FR-M19); 3) Quality
(red-flag re-projection fidelity); 4) Testing (delegation + four-gap + conflicts transcript);
5) Compliance (no re-derivation; Assumption markers; ASTM currency); 6) Operational; 7)
Self-assessment.

## QA (Zero-Trust Verifier)

Verify: (a) confirm every legal Objection maps to a real `red-flags.yaml` entry (no invented
legal framework — recompute the mapping); (b) confirm all four compliance gaps produce a check
and the Phase I gate rejects a stale/E1527-13 report; (c) confirm OKOA governance unknowns are
`Assumption`-marked, NOT hardcoded as rules; (d) confirm `conflicts-disclosure.yaml` exists and
lists each seat's disclosure. Reject on re-derivation, hardcoded governance rules, or missing
conflicts record.

**Evidence gates:** red-flag traceability; four gaps checked; ASTM currency enforced;
Assumption-marked governance; conflicts artifact present.

## Dev Learnings
_(fill: legal-analyst A10 foreclosure drift; red-flag->voting mapping.)_

## QA Learnings
_(fill: any parallel re-derivation caught; governance-hardcode sniff.)_
