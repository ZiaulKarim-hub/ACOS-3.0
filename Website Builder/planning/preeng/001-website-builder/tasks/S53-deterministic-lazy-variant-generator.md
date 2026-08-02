# S53-deterministic-lazy-variant-generator — Deterministic, lazy, append-only variant generator with the indistinguishability rule

| Field | Value |
|---|---|
| Epic / Story | E10 / ST-17 |
| Type · MoSCoW · Size | build · MUST · L `[I]` |
| Phase / Demo | Phase 4 / — |
| Depends on | S52-variant-axis-schema · S51-slot-contracts-and-swap-safety |
| Requirements | FR-133, FR-135, FR-136, FR-137 |
| Acceptance criteria | A33 · A34 · SL-S53-1 · SL-S53-2 · SL-S53-3 |
| CQ / evidence | CQ14 · EL-037 |
| Note | **R29** — eager generation stalls Step 4 at ~120 variants per direction, which is why laziness is a requirement and not an optimisation |

## PM — slice definition

**Objective.** Generate variants from tokens with no model call, only on first panel open, and never offer two the eye cannot tell apart.

**In scope.** `variants.ts` as a **pure deterministic function** of `(direction tokens, axis vector)` — **no model call, no subagent write** (subagents are policy-blocked from `Write`; verified twice, first-party `[V]`); lazy generation on **first open of a family's swap panel**, cached per direction under `05-variants/`, never pre-generated for unused families; append-only, collision-free indices across repeated rounds; the **200×120px indistinguishability rule** (A34) rejecting any candidate the eye cannot separate from one already offered in the same bar; hover-preview that ghosts the variant live in the real slot with current copy and neighbours (A33); an instrumentation counter proving unused families generated zero variants.

**Out of scope.** "More variants" and "more like this" (S57). Cross-direction anything. Any aesthetic scoring of a variant — NG1 forbids AI aesthetic judgement; the rule here is mechanical distinguishability, not quality.

**Allowed files / contexts.**
- `scripts/lib/variants.ts`, `scripts/lib/indistinguishability.ts`, `scripts/lib/variant-cache.ts`, `05-variants/**` (write), the `POST /variants` route as a call site.
- TypeScript on Bun. **No `.py` file anywhere in the skill tree.**

**Steps.**
1. Implement the generator as a pure function; identical inputs must yield byte-identical output across two runs in different processes.
2. Persist `{componentFamily, index, axisValues, directionId, generatedAt, indistinguishabilityCheck: {against, passed, method: "200x120px"}}` per variant.
3. Gate generation on first panel open; record a counter of generation events per family and assert zero for untouched families.
4. Make indices append-only: a second round starts from the skill-supplied current highest index and never reuses one.
5. Implement the indistinguishability check at the stated 200×120px scale against every variant already offered in the same bar; a failing candidate is discarded and the next axis combination is tried.
6. Wire hover-preview to ghost the candidate in the real slot with the real copy and real neighbours — never in an isolated swatch.

**Definition of Done.**
- Artifacts: `variants.ts`, the indistinguishability module, the per-direction cache, the instrumentation counter, the two-run determinism transcript.
- Validation: two runs produce identical bytes; an untouched family shows a zero counter; two rounds produce disjoint index sets; a deliberately near-duplicate candidate is rejected by recomputation.
- Demo-able increment: open a family panel in the editor and see generated variants with live ghosting.
- `slice.yaml` mapping — `acceptance_criteria: [A33, A34, SL-S53-1, SL-S53-2, SL-S53-3]`, `verification_method: exit-code` (A33: `manual-observation`, A34 and SL-S53-2: `recompute`, SL-S53-1: `grep-assert`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-133…FR-137 → file:line; (3) structural quality — the generator has no I/O other than the cache writer, so it is unit-testable without a browser; (4) functional testing — the two-run determinism check, the laziness counter, the collision check across three rounds, the near-duplicate fixture; (5) security/compliance — grep evidence that no network call and no `Task(` spawn exists on this path; (6) operational — how the cache is invalidated when the direction changes, and what happens on a partially written cache; (7) self-assessment.

## QA — zero-trust verification

- **Run the generator twice yourself** in separate processes and `sha256` both outputs; equal hashes or reject.
- **Recompute the indistinguishability decision** for at least two offered pairs at the stated scale; a logged `passed: true` you cannot reproduce is a rejection.
- **Grep the whole path** for a model call, a network fetch or a `Task(` spawn; one hit is a rejection.
- **Open one family only**, then read the counters: any generation event for another family is a rejection of the laziness claim.
- **Run two generation rounds** and intersect the index sets yourself; a non-empty intersection is a rejection.

## Dev Learnings

_Not Done until filled. Required: how many axis combinations were discarded by the indistinguishability rule before the bar filled, and whether determinism survived the cache layer._

## QA Learnings

_Not Done until filled. Required: the first place non-determinism leaked in (ordering, timestamps or map iteration)._
