# S23-versioned-coherence-lint-set — The versioned coherence-lint set, run at ingest and at LOCK

| Field | Value |
|---|---|
| Epic / Story | E6 / ST-07 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 1 / — |
| Depends on | S21-token-compiler-dtcg-and-forge |
| Requirements | FR-063 |
| Acceptance criteria | A17 · SL-S23-1 · SL-S23-2 |
| CQ / evidence | CQ5 · EL-087 |
| Note | **NA-05** — the lint count is stated three different ways in the source; this slice replaces the count with a **versioned set with named members** |

## PM — slice definition

**Objective.** Make coherence enforcement citable by name and version rather than by an unstable count, and enforce logical properties only.

**In scope.** A lint registry with a version number and named members; required members at minimum — the elevation-model lint (a border-only direction referencing any shadow token fails), the logical-properties-only lint, and the four direction-identity lints that validate authored artefacts against the identity vector; execution at ingest **and** at LOCK; a machine-readable lint report.

**Out of scope.** Aesthetic judgement of any kind. Blocking on an aesthetic finding — the anti-slop lint is a hard gate upstream (S19) and a dismissible advisory at the human-edit layer (S64).

**Allowed files / contexts.**
- `scripts/lib/lints/**`, `scripts/lib/lint-registry.ts`, the import path (S19) and the lock path (S68) as call sites only.

**Steps.**
1. Build the registry: each lint has an id, a version, a description, a severity and a pure check function.
2. Implement the elevation-model lint.
3. Implement the logical-properties-only lint: reject physical-direction declarations anywhere in generated CSS.
4. Implement the four direction-identity lints validating authored artefacts against the identity vector.
5. Wire the registry into ingest and into the lock-time checklist; the report cites `lintSetVersion` and each member id.
6. Record explicitly that "six lints" / "seven lints" / "lints 7–10" in the source are reconciled here as one versioned set.

**Definition of Done.**
- Artifacts: registry, the named lints, the report shape, both call sites.
- Validation: a border-only fixture referencing a shadow token fails; a physical-direction fixture fails at ingest **and** at lock; the report names the set version.
- `slice.yaml` mapping — `acceptance_criteria: [A17, SL-S23-1, SL-S23-2]`, `verification_method: exit-code` (SL-S23-1/2: `grep-assert`).

## Dev — execution contract

Evidence bundle: (1) summary listing every member with its version; (2) traceability FR-063 → file:line; (3) structural quality — every check is pure and unit-tested; (4) functional testing — both fixtures at both call sites; (5) security/compliance — n/a, note it; (6) operational — how a lint is added without renumbering anything; (7) self-assessment.

## QA — zero-trust verification

- **Run your own** `grep -rnE '(^|[^-])(left|right|top|bottom)\s*:' <generated css>` plus the margin/text-align patterns, and require zero.
- **Run the border-only fixture yourself.**
- **Confirm both call sites execute** by forcing a failure at LOCK and observing the block.
- **Reject** if any artifact cites a lint *count* rather than the set version and member ids.

## Dev Learnings

_Not Done until filled. Required: which physical-direction declarations slipped in from generated payloads, and whether the logical-only rule created any real authoring friction._

## QA Learnings

_Not Done until filled. Required: whether the versioned-set approach actually removed the counting ambiguity downstream._
