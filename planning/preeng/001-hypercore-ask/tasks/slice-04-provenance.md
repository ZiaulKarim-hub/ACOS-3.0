# slice-04-provenance — Provenance-binding engine (refuse-on-missing)

- **Parent story:** STORY-HCA-04 · **Parent epic:** EPIC-HCA-04 · **Demo:** -
- **Effort:** M · **Dependency order:** 5 · **Depends on:** slice-03-twotier-cache
- **Lattice refs:** meth-prov, proc-bind, ent-provbind, pat-refuse, anti-guess, metric-provcov, metric-fab, cq-03

## PM Section (Planner / Specifier — LCE)

### Objective
Implement the universal provenance-binding engine: bind **every** delivered value to a `ProvenanceBinding` = `{endpoint, request_params, timestamp, json_field_path, raw_response_id}` resolving to a cached Tier-1 `RawApiResponse`. **Missing or unresolvable binding => REFUSE delivery; never guess.** Aggregated values carry one binding per contributing source.

### Scope
**In scope:** `hca-provenance.py` (build a binding for a value from its Tier-2 record's `field_bindings`; verify it resolves to a real Tier-1 record at the cited path; emit a `REFUSED` result with reason when it cannot); aggregate binding (collect contributing bindings).
**Out of scope:** the deterministic gate suite (slice-05), consensus (slice-06), delivery rendering (slice-07/09).

### Guardrails / Allowed files
- `.claude/scripts/hca-provenance.py` (stdlib only)
- tests: `.claude/scripts/tests/test_hca_provenance.py` (incl. negative/refusal cases)
- this task file + `.acos/evidence/[DATE]/slice-04-provenance/`
- Prohibited: returning any value with an unresolvable binding; fabricating a binding to satisfy the check.

### Definition of Done
- [ ] For a bound value, the engine produces a `ProvenanceBinding` that **resolves** to a real Tier-1 record and the `json_field_path` points at the cited value — pass-condition: positive-case resolution test.
- [ ] For a value with missing/unresolvable binding, the engine returns `REFUSED` with a machine-readable reason — pass-condition: **negative-case refusal test (REQUIRED)**.
- [ ] Aggregates carry a `contributing[]` list with one resolvable binding per source — pass-condition: aggregate-binding test.
- [ ] Invariant enforced: no value object can leave the engine in a "deliverable" state without ≥1 resolvable binding — pass-condition: invariant test.
- [ ] `## Dev Learnings` / `## QA Learnings` updated.

## Dev Section (Executor)

### Approach
1. Read the Tier-2 record's `field_bindings`; for the requested value, construct the `ProvenanceBinding` pulling `endpoint`/`request_params`/`timestamp` from the resolved Tier-1 record.
2. Resolve-and-verify: load the Tier-1 record by `raw_response_id`, walk `json_field_path`, assert the value at the path matches the value being bound; mismatch => REFUSE.
3. Aggregate path: collect bindings for every contributor; if any contributor is unbindable => REFUSE the aggregate.
4. Tests: positive, negative (missing binding, wrong path, value mismatch), aggregate, invariant.

### Dev Evidence Bundle (7 parts — required)
Summary; Traceability (M2 provenance, NFR-Trust, metric-provcov/fab, pat-refuse); Code Quality (stdlib); Functional (positive + negative + aggregate + invariant tests); Security (no PII in binding beyond path); Operational; Self-assessment.

### Dev Learnings
- Built `hca-provenance.py` (`ProvenanceEngine`). `bind_and_verify(value, binding)` does THREE checks before it will call a value deliverable: (1) the binding has both `raw_response_id` + `json_field_path`; (2) the Tier-1 record exists and the path RESOLVES; (3) the resolved Tier-1 value MATCHES the bound value. Any failure -> a structured `REFUSED` result with a machine-readable `reason_code` (`NO_BINDING`/`RAW_RESPONSE_NOT_FOUND`/`PATH_UNRESOLVED`/`VALUE_MISMATCH`). This is what makes a fabricated binding impossible: the value is re-read from Tier-1 and compared, so a made-up value with a real path is caught as `VALUE_MISMATCH`.
- The value-mismatch comparison is type-faithful (`"5000000.0"` string != `5000000.0` number) but JSON-numeric-tolerant (5 == 5.0) and bool-strict (True is not 1). Used canonical JSON for structural equality so dict key-order doesn't cause false negatives.
- Two API styles on purpose: a soft form returning a `REFUSED` dict (`deliverable=False`, `binding=None`) for batch/inspection, and a strict `*_or_raise` form raising `ProvenanceRefusal` so the invariant ("no deliverable value without a resolvable binding") is enforceable as an exception, not a checkable flag a caller could ignore.
- Aggregates (`bind_aggregate`) require >=1 contributor and bind ONE resolvable binding per source; any unbindable/mismatched contributor refuses the WHOLE aggregate. Optional `contributing_values` lets a caller assert each source's value too.
- Reused slice-03's json-path walker (`hca_cache.walk_json_path` + the `_MISSING` sentinel) rather than re-implementing — one resolution path means the provenance engine and the Tier-2 binder can never disagree. `verify_normalized_record()` batch-verifies a whole Tier-2 record and passes ONLY when every field resolves+matches.
- `ConfidenceRecord`: single-source (count<=1) figures are forced to `<= single_source_cap` (config 0.7) and flagged `single_source: true` with `capped_at`; multi-source values are not capped by that rule. Cap is read from `config.yaml` via stdlib scan.
- The engine is strictly read-only and never writes Tier-1 — it only resolves+compares. Verified end-to-end on a REAL cached live record (the loans `id` field bound back to `$.body.data[0].id` -> VERIFIED), values never printed.

## QA Section (Zero-Trust Verifier)

### Verification steps
1. Re-author the **negative** cases: feed a value with no binding, a binding to a nonexistent `raw_response_id`, and a binding whose path does not contain the value — all three MUST yield `REFUSED`. Any silent delivery = REJECT.
2. For a positive case, independently walk the `json_field_path` in the cited Tier-1 record and confirm the value matches.
3. Attempt to coax a deliverable value past the engine without a binding; confirm impossible.
4. Confirm aggregates refuse when any contributor is unbindable.

### Evidence gates (all must pass)
- [ ] **Refuse-on-missing/unresolvable binding proven by negative tests** — fail = REJECT (hard; this is the core guarantee).
- [ ] Positive bindings independently re-resolved by QA.
- [ ] Aggregate refusal on any unbindable contributor.
- [ ] Invariant (no deliverable without binding) holds.
- [ ] Learnings updated.

### QA Learnings
- All THREE required negative cases re-authored and pass as REFUSED: (a) empty binding `{}` -> `NO_BINDING`; (b) binding to `hca:GHOST` (nonexistent raw_response_id) -> `RAW_RESPONSE_NOT_FOUND`; (c) binding whose path is `$.body.record.NOT_A_FIELD` -> `PATH_UNRESOLVED`. Plus the mismatch case (real path, wrong claimed value) -> `VALUE_MISMATCH`. None silently delivered.
- Positive case independently re-resolved by walking `$.body.record.commitment` in the cited Tier-1 record and confirming the value matches what the engine VERIFIED — done WITHOUT trusting the engine's own resolver.
- "Coax past without a binding" confirmed impossible: every refusal returns `deliverable=False` and `binding=None`, and the `*_or_raise` form raises `ProvenanceRefusal`. There is no code path that yields `deliverable=True` without a fully resolved+matched binding.
- Aggregate refusal verified three ways: a contributor pointing at `hca:GHOST` -> `CONTRIBUTOR_UNBINDABLE`; an empty contributor list -> `NO_CONTRIBUTORS`; and a contributor whose declared value is wrong (when `contributing_values` supplied) -> refused. A clean 2-source aggregate VERIFIES with 2 contributing bindings.
- Batch invariant verified: `verify_normalized_record` PASSES only when verified==checked on a real Tier-2 record; tampering one field's value to no longer match Tier-1 flips it to `ok=False`.
- Confidence cap verified: single-source -> confidence <= 0.7 even with agreement=0.99; multi-source (3) with agreement 0.9 -> not capped (>0.7, capped_at=None). Cap value 0.7 confirmed read from config.
