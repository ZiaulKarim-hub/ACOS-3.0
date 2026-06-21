# slice-08-dedup-apn — Dedup on APN + per-owner aggregation

- **Parent story:** STORY-APS-08 · **Parent epic:** EPIC-APS-08 · **Demo:** -
- **Effort:** M · **Dependency order:** 9 · **Depends on:** slice-07-entity-discovery-loop-integration
- **Lattice refs:** cq-02, ent-parcel, proc-channels, meth-union, std-provenance

## PM Section (Planner / Specifier — LCE)

### Objective
Implement `dedup.py`: canonicalize **APN** and merge cross-channel duplicate parcels — **unioning**
provenance + freshness across the channels that found them — then aggregate holdings per owner / controlled
entity. (One parcel found via assessor + recorder + ArcGIS becomes one row carrying all three sources.)

### Scope
**In scope:** `scripts/dedup.py` (APN canonicalization across county formats; merge dup parcels unioning
`source_refs` + freshness; per-owner aggregation).
**Out of scope:** scoring (slice-09); equity rollup (slice-10).

### Guardrails / Allowed files
- `.claude/skills/acos-property-search/scripts/dedup.py` (stdlib only)
- `.claude/skills/acos-property-search/scripts/tests/test_dedup.py`
- this task file + `.acos/evidence/[DATE]/slice-08-dedup-apn/`
- Prohibited: dropping provenance on merge; collapsing distinct APNs; fabricating an APN.

### Definition of Done
- [ ] The same parcel found via 3 channels collapses to one record that retains all 3 `source_refs` + the freshest stamp — pass-condition: **merge-unions-provenance test (REQUIRED; dropped provenance = REJECT)**.
- [ ] APN canonicalization handles county format variants (dashes/spaces/leading zeros) deterministically — pass-condition: canonicalization test.
- [ ] Distinct APNs are never merged — pass-condition: no-false-merge test.
- [ ] Holdings aggregate per owner / controlled entity — pass-condition: aggregation test.
- [ ] `## Dev Learnings` / `## QA Learnings` updated.

## Dev Section (Executor)

### Approach
1. Canonical APN function (normalize separators/zeros) — deterministic.
2. Merge by canonical APN; union `source_refs`; keep the freshest `date_last_verified`.
3. Aggregate per owner/entity node.
4. Tests: merge-unions-provenance, canonicalization, no-false-merge, aggregation.

### Dev Evidence Bundle (7 parts — required)
Summary; Traceability (ent-parcel, std-provenance, meth-union, EV-002); Quality (stdlib, deterministic);
Functional (the four DoD tests); Security; Operational; Self-assessment.

### Dev Learnings
- (fill at execution) APN format edge cases encountered.

## QA Section (Zero-Trust Verifier)

### Verification steps
1. Re-author a 3-channel duplicate; confirm one row with all three sources + freshest stamp.
2. Feed two near-identical-but-distinct APNs; confirm they do NOT merge.
3. Independently recompute the canonical APN for a tricky format.

### Evidence gates (all must pass)
- [ ] **Merge unions provenance (no dropped source)** (hard; fail = REJECT).
- [ ] APN canonicalization deterministic; no false merges.
- [ ] Per-owner aggregation correct.
- [ ] Learnings updated.

### QA Learnings
- (fill at execution) Any provenance lost on merge.
