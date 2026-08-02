# S21-token-compiler-dtcg-and-forge — Token compiler: DTCG JSON, forge YAML, custom properties and theme layer

| Field | Value |
|---|---|
| Epic / Story | E6 — Token compiler and coherence lints / ST-07 |
| Type · MoSCoW · Size | build · MUST · L `[I]` |
| Phase / Demo | Phase 1 / — |
| Depends on | S19-ast-validator-quarantine-and-reverification |
| Requirements | FR-060, FR-061, FR-064, FR-065, FR-066, FR-068 |
| Acceptance criteria | A14 · A15 · A16 · A18 · A19 · A24 · SL-S21-1 · SL-S21-2 |
| CQ / evidence | CQ5 |
| Settled decision | **D1** — derived values are computed from anchors, never independently picked |

## PM — slice definition

**Objective.** Emit both design-system consumers from one importer and make derived values structurally un-pickable rather than merely discouraged.

**In scope.** DTCG token JSON **and** the forge specification YAML from one pass; compilation to CSS custom properties plus a theme layer; the three extension blocks on every token; rejection of any token whose direction vector hash differs from the active direction; the derived families (spacing, type steps, radius scale, shadow scale, semantic colour roles, **and font fallback metrics computed from the real font binary**); per-direction validity lists for repickable rows with automatic demotion when one cannot be supplied; independently solved light and dark schemes with a contrast proof table covering both; a pinned compiler version and a committed lockfile.

**Out of scope.** The flat variable layer (S22). The lint set (S23). Any editor UI.

**Allowed files / contexts.**
- `scripts/lib/token-compiler.ts`, `scripts/lib/derive.ts`, `scripts/lib/contrast-table.ts`, `02-system/<directionId>/{tokens.json,tokens.css}`, the forge YAML output path.

**Steps.**
1. Compile tokens to DTCG JSON with the three extension blocks per token.
2. Emit the forge YAML from the same pass — both consumers exist and the second is cheap.
3. Mark every derived family `pickable: false` and assert the editor renders no control for them (asserted here by data, enforced in the editor).
4. Compute font fallback metrics from the selected font binary and emit them as a derived family (the taxonomy does not yet name this family — record it as an amendment owed).
5. Emit a per-direction validity list for every repickable row; demote any row that cannot supply one to a direction-slot **in the compiler**, not by hand.
6. Solve light and dark independently; build the contrast proof table for both; a failure in the table is evidence of a hand-edited value, not a compiler bug.
7. Reject any token whose direction vector hash mismatches the active direction.

**Definition of Done.**
- Artifacts: compiler, derive module, contrast table, both emitted formats, the pinned version and lockfile.
- Validation: extension blocks present on 100% of tokens; a mismatched-hash fixture is rejected; the proof table is all-pass by construction on a clean import.
- `slice.yaml` mapping — `acceptance_criteria: [A14, A15, A16, A18, A19, A24, SL-S21-1, SL-S21-2]`, `verification_method: exit-code` (A18/A19: `recompute`).

## Dev — execution contract

Evidence bundle: (1) summary with the resolved token count for one direction (expect roughly 600–900 `[V]`); (2) traceability FR-060…FR-068 → file:line; (3) structural quality — derivation is a pure function of anchors plus seed tables; (4) functional testing — the mismatched-hash fixture, the demotion fixture, the two-scheme proof table; (5) security/compliance — no remote fetch during compile; (6) operational — how a compiler upgrade is pinned and rolled; (7) self-assessment.

## QA — zero-trust verification

- **Recompute** five derived values yourself from the anchors and seed tables; a "derived" value you can only get by copying the output is not derived.
- **Recompute** ten contrast pairs from the emitted tokens in both schemes.
- **Count** tokens missing any extension block; the answer must be zero.
- **Run the hash-mismatch fixture yourself**.
- **Reject** if any derived family exposes a pickable flag of true, or if font fallback metrics were omitted because the taxonomy does not name them yet.

## Dev Learnings

_Not Done until filled. Required: the resolved token count, and which family was hardest to derive rather than pick._

## QA Learnings

_Not Done until filled. Required: whether any "derived" value was in fact hand-authored upstream._
