# S52-variant-axis-schema — Hand-authored variant-axis schema

| Field | Value |
|---|---|
| Epic / Story | E10 / ST-17 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 4 / — |
| Depends on | S21-token-compiler-dtcg-and-forge |
| Requirements | FR-130, FR-131, FR-132 |
| Acceptance criteria | SL-S52-1 · SL-S52-2 |
| CQ / evidence | CQ14 · EL-037 |
| Note | **§8.6-OQ-11** — the schema is hand-authored in the skill for determinism, and §18 carries **no effort line for it**. That gap is recorded here, not silently absorbed |

## PM — slice definition

**Objective.** Define structural distinctness machine-checkably, per component, so the variant budget stays finite.

**In scope.** A hand-authored `VariantAxisVector` per component, committed in the skill (never model-generated, because determinism is the reason it is hand-authored); the distinctness rule — two variants are distinct iff their vectors differ in ≥1 axis; the **computed-axis exclusion set** (size, theme, density, state, icon slot, semantic colour) which never counts against the budget; a coverage selftest over the v1 target; the missing **skip-link row** added with a **single canonical variant** (NA-B08 — §13.4 gate 11a requires the component and the inventory does not contain it); a recorded effort line for the authoring work itself, tagged `[I]` low confidence.

**Out of scope.** Generating any variant (S53). The component-bar UI (S51). Re-deriving the v1 cut list — that must be regenerated **mechanically from the priority column**, never asserted here.

**Volumes (do not restate loosely).** Inventory of record is **216 rows / 1,228 variants** `[V — §8.2/§8.3; EL-037; NA-02]`. **87 rows / 674 variants is the v1 CUT CANDIDATE** from DECISIONS item 2 (unsigned), and ~50 / ~430 is only what §18 and §13 were originally sized against. The coverage target asserted by this slice is **88 rows / 675 variants** `[I on the cut mapping]` = 87/674 plus the skip-link row.

**Allowed files / contexts.**
- `scripts/lib/variant-axes.ts`, `scripts/data/variant-axes/*.json` (the hand-authored vectors), `scripts/lib/distinctness.ts`, the coverage selftest.
- TypeScript on Bun. **No `.py` file anywhere in the skill tree.**

**Steps.**
1. Author one axis vector per component row in the v1 set; every axis is named, enumerated and documented.
2. Encode the computed-axis set as data, not as scattered conditionals, and exclude it from the budget by construction.
3. Implement `areDistinct(a, b)` as a pure vector comparison.
4. Add the skip-link row with exactly one variant and mark it non-demotable in the same sense radio group and toggle switch are.
5. Write the coverage selftest: every row in the v1 target declares a vector; a missing vector fails the run with the row name.
6. Record the authoring effort as an explicit line tagged `[I]`, and state plainly that §18 does not currently carry it.

**Definition of Done.**
- Artifacts: the vector data set, `variant-axes.ts`, `distinctness.ts`, the coverage selftest, the recorded effort line.
- Validation: coverage selftest green at 88 rows; a fixture pair differing only on a computed axis is reported as the **same** variant; the skip-link row is present with exactly one variant.
- Demo-able increment: `bun selftest.ts --axes` prints the coverage table and the excluded-axis list.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S52-1, SL-S52-2]`, `verification_method: exit-code`.

## Dev — execution contract

Evidence bundle: (1) summary with the coverage table; (2) traceability FR-130…FR-132 → file:line; (3) structural quality — the vectors are data, the rule is one pure function; (4) functional testing — the computed-axis pair fixture and a genuinely distinct pair; (5) security/compliance — n/a, note it; (6) operational — how a new component row is added without renumbering anything, and where the effort line lives; (7) self-assessment stating which rows were the hardest to axis honestly.

## QA — zero-trust verification

- **Count the rows yourself** from the vector data set and compare to 88; a logged count is not evidence.
- **Write your own pair** that differs only on `density` and require the distinctness function to return false.
- **Grep the vector data** for any model-generated provenance marker; the schema is hand-authored by requirement.
- **Confirm the skip-link row exists** with exactly one variant, and reject if it was given a ten-variant family.
- **Reject** any artifact that presents 87/674 or ~50/~430 as the inventory of record rather than as a cut candidate / stale sizing basis.

## Dev Learnings

_Not Done until filled. Required: which components resisted a clean axis decomposition, and the real authoring time against the `[I]` effort line._

## QA Learnings

_Not Done until filled. Required: whether any axis was smuggled in that is actually a computed axis in disguise._
