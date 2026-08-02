# SLICE-C1-objection-fact-adapter-axis-s — Objection->fact adapter + Axis S

**Parent story:** STORY-C1 · **Epic:** EPIC-C · **Effort:** M · **Demo:** Demo 1 (basic) -> Demo 2 (full Axis S)
**slice.yaml mapping:** Objective->`objective`; Allowed files->`files_allowed`;
DoD+evidence gates->`acceptance_criteria`; QA verification->`verification_method`.

## PM (Planner / LCE brief)

**Objective (single, narrow):** Build the IC **fact-builder adapter** that maps each expert
`Objection` onto an axiom-synthesis `fact` record and attaches the domain-owned **Axis S**
(`_ic_extension_severity`) — WITHOUT modifying any of the six engine scripts.

**In-scope:** `fact_builder.py` — read `rounds/round-00/opening/{seat}.json`; for each
objection emit a `fact` with `{fact_id, statement, claim_type, candidates, grading, flags,
refuter, conflict, depends_on, covers}` plus `_ic_extension_severity {axis_s_materiality,
raised_by_role, rationale}`; treat a refuter-surfaced mitigant as a NEW fact `depends_on` the
objection; carry `covers` tags for the 16-risk coverage assertion.

**Out-of-scope:** running the engine (C2); the verdict (C3); memo render (C4). No engine edits.

**Allowed files/contexts:** `scripts/fact_builder.py`; READ-ONLY: `acos-axiom-synthesis`
`orchestrate.py` signature + STATE-MACHINE.md, opening JSONs, spec §4.2 engine contract +
Appendix B/C, domain-lattice `method-severity-axis-s` + `metric-severity-ladder`.

**Step-by-step:**
1. Parse opening objections -> `fact` dicts matching `process_fact` exactly.
2. Attach Axis S on the fixed ordinal ladder `informational < limitation < material-risk <
   deal-breaker-candidate`, scored by the raising seat; store ALONGSIDE Axis A/B, never blended.
3. Emit mitigants as dependent facts; populate `covers` for coverage tagging.

**Definition of Done:**
- Artifacts: `scripts/fact_builder.py`; a `ledger/facts-input.json` for a fixture.
- Validation: every produced fact validates against `process_fact`'s expected fields; Axis S
  present and on the exact 4-rung ladder; Axis S is NOT arithmetically combined with Axis A/B
  anywhere; zero engine scripts modified.
- Evidence bundle: fact-builder transcript + a sample fact showing A/B/S kept separate.

## Dev (Executor)

**Execution notes:** the ONLY engine extension allowed is `_ic_extension_severity` on the
fact. Do NOT touch `decircularize/grade_fuse/falsify/resolve/lifecycle/coverage/orchestrate`.

**Evidence Bundle:** 1) Summary; 2) Traceability (FR-M5); 3) Quality (fact schema conformance
lint); 4) Testing (fixture build + a fact dump); 5) Compliance (no engine edits — `git diff
--stat` on engine); 6) Operational; 7) Self-assessment.

## QA (Zero-Trust Verifier)

Verify: (a) load produced facts and confirm each has the 10 `process_fact` fields + a
well-formed `_ic_extension_severity`; (b) confirm `axis_s_materiality` values are ONLY from the
4-rung ladder; (c) grep the adapter to prove Axis S is never averaged/summed with Axis A or B
(the load-bearing separation); (d) confirm `git diff --stat` shows ZERO changes under
`acos-axiom-synthesis/`. Reject if Axis S is blended or any engine script changed.

**Evidence gates:** fact-field conformance; ladder-only severities; A/B/S separation proven;
engine untouched.

## Dev Learnings
_(fill: process_fact field nuances; mitigant-as-dependent-fact modeling.)_

## QA Learnings
_(fill: any blending slippage; same-fact conflict edge cases surfaced.)_
