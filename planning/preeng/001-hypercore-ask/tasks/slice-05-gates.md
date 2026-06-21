# slice-05-gates — Deterministic gate suite

- **Parent story:** STORY-HCA-05 · **Parent epic:** EPIC-HCA-05 · **Demo:** -
- **Effort:** L · **Dependency order:** 6 · **Depends on:** slice-04-provenance
- **Lattice refs:** proc-gate, meth-pregate, meth-schemaval, meth-pagecheck, meth-freshpolicy, meth-recon, meth-normalize, ent-gateresult, ent-confidence, metric-pagecomplete, metric-freshwin, metric-sscap, anti-silenttrunc, anti-singletrust, cq-05, cq-06, cq-07, cq-08, cq-09

## PM Section (Planner / Specifier — LCE)

### Objective
Implement the six deterministic gates that sit **underneath** consensus and run on the consensus-agreed value(s) before binding/delivery. Any hard failure => **REFUSE**. Gates: (1) schema validation, (2) pagination-completeness, (3) freshness window, (4) cross-field reconciliation, (5) unit/currency normalization, (6) single-source confidence cap ≤ 0.7.

### Scope
**In scope:** `hca-gates.py` producing a `VerificationGateResult` (`schema_ok`, `pagination_complete`, `freshness_ok`, `reconciliation_ok`, `normalization_applied`, `confidence_capped`, `outcome`, `failures[]`) + a `ConfidenceRecord`; uses the expected schemas (slice-02) and `config.yaml` freshness windows + `single_source_cap`.
**Out of scope:** consensus dispatch (slice-06); schema-drift *detection* hardening (slice-11 hardens it; basic schema validation here); delivery rendering.

### Guardrails / Allowed files
- `.claude/scripts/hca-gates.py` (stdlib only; the six gates + ConfidenceRecord)
- `.claude/skills/acos-hypercore-ask/schemas/*.json` (read; may extend expected schemas)
- tests: `.claude/scripts/tests/test_hca_gates.py` (one positive + one failing fixture per gate)
- this task file + `.acos/evidence/[DATE]/slice-05-gates/`
- Prohibited: passing a value when any hard gate fails; silently truncating lists; serving stale data.

### Definition of Done
- [ ] **Schema gate** validates the source record against the expected entity schema; invalid => fail — pass-condition: positive + failing-fixture tests.
- [ ] **Pagination-completeness gate** reconciles fetched count / cursor exhaustion against `reported_total`; mismatch => fail (no silent truncation) — pass-condition: passes on complete fixture, **fails on the deliberately-truncated fixture** (REQUIRED).
- [ ] **Freshness gate** checks Tier-1 `timestamp` within the configured window for the entity class; stale => fail/flag-refresh — pass-condition: passes fresh fixture, **fails the stale fixture** (REQUIRED).
- [ ] **Reconciliation gate** checks related fields agree (e.g. drawdowns − repayments vs outstanding; sum-of-parts vs reported total) — pass-condition: passes consistent fixture, fails an inconsistent one.
- [ ] **Unit/currency normalization** applied before any comparison/aggregation; mixed units normalized — pass-condition: normalization test.
- [ ] **Single-source confidence cap** forces confidence ≤ 0.7 and flags single-source values — pass-condition: cap test (a single-source value never exceeds 0.7).
- [ ] `VerificationGateResult.outcome == refuse` whenever any hard gate fails; `failures[]` names the gate(s) — pass-condition: aggregate refusal test.
- [ ] `## Dev Learnings` / `## QA Learnings` updated.

## Dev Section (Executor)

### Approach
1. Implement each gate as a pure function returning `(ok: bool, detail: str)`.
2. Compose into `run_gates(value, source, schema, config) -> VerificationGateResult`; outcome = `refuse` if any hard gate fails.
3. Implement unit/currency normalization (canonical currency + scale) reused from `hca-normalize.py`.
4. Implement `ConfidenceRecord` with single-source cap from config.
5. Author one passing + one failing fixture per gate (reuse the truncated/stale/drifted fixtures from slice-02).

### Dev Evidence Bundle (7 parts — required)
Summary; Traceability (M4 gate suite, NFR-Completeness/Freshness, metrics, anti-silenttrunc/singletrust, cq-05..09); Code Quality (stdlib, pure functions); Functional (positive+failing per gate); Security; Operational; Self-assessment.

### Dev Learnings
- **Two schema vocabularies coexist by design.** Each entity has a live-introspection
  `*.gql.schema.json` (camelCase GraphQL, e.g. `loan.gql.schema.json` `id`/`commitment`/
  `fundingSources`) AND a pre-access `*.schema.json` placeholder (snake_case, e.g.
  `loan.schema.json` `loan_id`/`outstanding_principal`/`currency`). The slice-02 adversarial
  fixtures (`loan__L-001`, `loan_stale`, `loan_drifted`, `list_loan_truncated`) all use the
  REST/snake_case body shape, so schema_validation + schema_drift for THOSE compare against
  the placeholder descriptor; the `gql_*` fixtures compare against the `.gql` schema (and the
  drift gate re-derives the authoritative type-map straight from `_introspection.json`).
  `load_expected_schema(entity, prefer_graphql=...)` picks the right one.
- **The drift gate's introspection type-renderer must exactly match the schema-file
  convention.** The recursive `kind/ofType` walk in `_gql_type_string` reproduces `ID!`,
  `[LoanFunding!]`, `Float` etc. byte-for-byte vs `loan.gql.schema.json` (asserted in
  `test_introspection_map_matches_gql_schema_file`). This means the live `_introspection.json`
  is the single source of truth for drift, not a hand-maintained copy.
- **Per-record vs aggregation currency handling are different failure modes.** A GraphQL list
  projection legitimately carries `commitment` with NO per-row `currency` — that is a *skip*
  (currency not in this projection), not an integrity failure. A present-but-unknown/blank
  currency or a non-numeric amount IS a hard FAIL. The headline hard check is the
  aggregation path: refuse to sum mixed/unknown currencies (`can_aggregate`). Without this
  split the clean GraphQL complete report wrongly refused.
- **Confidence cap is a FLAGGING gate, not a hard gate.** A correctly-capped+flagged
  single-source value is a valid deliverable-with-flag state, so it must NOT force REFUSE on
  its own (only the six structural gates + drift are hard). It only FAILs if the cap was
  somehow not applied. Delegated entirely to `ProvenanceEngine.confidence_record` (single
  authority) so the 0.7 cap stays config-driven and consistent with slice-04.
- **Reconciliation rules fire only when all referenced fields are present + numeric.** A
  missing field is the schema gate's job, not reconciliation's — so reconciliation passes
  *vacuously* (rules_fired=0) when nothing is reconcilable, and only FAILs a FIRING rule that
  breaks beyond tolerance. This keeps the loan-funded and payment-allocation identities
  independent and avoids false positives on sparse records.
- **Data problems are FAIL results, never exceptions.** `GateError` is reserved strictly for
  programmer misuse (non-dict source). An integrity failure can never be swallowed as
  "errored, treat as pass" — it always surfaces as a FAIL gate + REFUSE verdict.

## QA Section (Zero-Trust Verifier)

### Verification steps
1. For each of the six gates, run the **failing** fixture and confirm the gate fails and `outcome == refuse`. QA re-authors the truncated and stale fixtures independently.
2. Confirm pagination gate cannot pass when `fetched_count < reported_total` (no silent truncation) — adversarially craft a near-miss.
3. Confirm freshness gate uses the per-entity-class window from config, not a hardcoded value.
4. Confirm a single-source value's confidence is never > 0.7 regardless of agent self-confidence.
5. Confirm reconciliation catches a planted arithmetic inconsistency.

### Evidence gates (all must pass)
- [ ] **Each gate fails its failing fixture; aggregate outcome == refuse** — fail = REJECT.
- [ ] **Pagination gate blocks silent truncation; freshness gate blocks stale** — REQUIRED hard checks.
- [ ] Single-source cap ≤ 0.7 enforced.
- [ ] Reconciliation catches planted inconsistency.
- [ ] Learnings updated.

### QA Learnings
- **All three REQUIRED hard checks proven on the slice-02 adversarial fixtures directly:**
  pagination FAILs `list_loan_truncated__page1.json` (fetched 2 < reported_total 3) AND
  `gql_list_loan_truncated__short.json` (complete=False); freshness FAILs
  `loan_stale__L-900.json` (2024-01-01, outside the config 1d window); schema_drift FAILs
  `loan_drifted__L-901.json` (`principal_outstanding`/`legacy_balance` unexpected, `currency`
  missing). Captured per-gate in `.acos/evidence/2026-06-18/SLICE-HCA-05/verify.log`.
- **Near-miss adversarial confirmed:** pagination CANNOT pass with `fetched < reported_total`
  even when `complete=True` is (falsely) asserted, and CANNOT pass when fetched==total but a
  non-null `next_cursor` contradicts completeness. (`test_FAIL_near_miss_one_short_cannot_pass`,
  `test_FAIL_nonnull_cursor_with_matching_count`.)
- **Freshness window is config-driven, not hardcoded:** the gate's reported `window_days`
  equals `hca-cache.freshness_window_days('loan')` (=1) and `client`=30 (reference_static),
  both read from `config.yaml`. (`test_window_comes_from_config_not_hardcoded`.)
- **Single-source confidence never exceeds 0.7 regardless of agent self-confidence:** swept
  claimed self-confidence 0.8/0.9/0.95/1.0 — every result <= 0.7.
  (`test_single_source_never_exceeds_cap_regardless_of_self_confidence`.)
- **Reconciliation catches planted arithmetic inconsistency** on both the payment-allocation
  identity and the loan funded==outstanding+repaid identity.
- **QA independently re-authored** the truncated + stale hostile cases (NOT reusing the
  slice-02 fixture files) and confirmed the gates catch the failure MODE, not the fixture.
  (`QAReauthoredAdversarialTest`.)
- **Aggregate verdict + tiers verified:** ANY hard gate FAIL => `outcome==refuse` with the
  gate named in `failures[]`; deterministic-only tier still refuses stale; failed provenance
  binding forces refuse even when all gates pass (Wave B always required). 170/170 tests
  green (122 prior + 48 new), no regressions.
