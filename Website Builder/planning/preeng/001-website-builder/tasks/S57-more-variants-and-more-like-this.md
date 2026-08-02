# S57-more-variants-and-more-like-this — More variants and more like this

| Field | Value |
|---|---|
| Epic / Story | E12 / ST-19 |
| Type · MoSCoW · Size | build · MUST · S `[I]` |
| Phase / Demo | Phase 4 / — |
| Depends on | S53-deterministic-lazy-variant-generator |
| Requirements | FR-134 |
| Acceptance criteria | SL-S57-1 · SL-S57-2 |
| CQ / evidence | CQ14 |
| Note | These are the two **cheapest regeneration gears**. The middle gear is section-scoped regeneration (S58); the heaviest is a redesign fork (S59) |

## PM — slice definition

**Objective.** Give the two cheapest regeneration gears: extend the set, or explore the neighbourhood of something already approved.

**In scope.** "More variants" — appends the next N starting from the **skill-supplied current highest index**, append-only and collision-free; "more like this" — appends **exactly five deterministic neighbours** of an already-approved variant, where a neighbour is a single-axis perturbation of the approved variant's axis vector; both paths re-running the **200×120px indistinguishability rule against everything already offered in the same bar**, not merely against each other; both writing through the same cache and provenance path as S53 so nothing bypasses the generator.

**Out of scope.** Any model call — both gears are pure functions over tokens and the axis schema, exactly as S53 is. Section-scoped regeneration (S58). Changing the axis schema (S52).

**Allowed files / contexts.**
- `scripts/lib/variants.ts` (extend only), `scripts/lib/neighbours.ts`, the `POST /variants` route, `05-variants/**` (write).
- TypeScript on Bun. **No `.py` file anywhere in the skill tree.**

**Steps.**
1. Read the current highest index from the skill-supplied value, never by scanning and guessing; append from there.
2. Implement neighbour selection as a deterministic single-axis walk over the approved variant's vector, returning exactly five.
3. Run both outputs through the indistinguishability check against the **full** current bar contents, discarding and continuing on a failure.
4. Persist each new variant with its `indistinguishabilityCheck.against` list so the decision is auditable later.
5. Assert index disjointness across three consecutive invocations mixing both gears.

**Definition of Done.**
- Artifacts: the two entry points, the neighbour function, the disjointness test, the audit records.
- Validation: three mixed rounds produce disjoint index sets; "more like this" returns exactly five; a near-duplicate neighbour is discarded by recomputation; two runs of each gear are byte-identical.
- Demo-able increment: approve a variant in the editor, press "more like this", and get five distinguishable neighbours in the same bar.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S57-1, SL-S57-2]`, `verification_method: exit-code` (SL-S57-2: `recompute`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-134 → file:line; (3) structural quality — both gears reuse the S53 generator; no second generation path exists; (4) functional testing — the three-round disjointness run, the exactly-five assertion, the near-duplicate fixture, the two-run determinism check; (5) security/compliance — grep evidence of no model call on this path; (6) operational — what happens when the axis space is exhausted before five neighbours are found; (7) self-assessment.

## QA — zero-trust verification

- **Invoke both gears yourself** three times and intersect the index sets; any overlap is a rejection.
- **Count the neighbours yourself** — four or six is a rejection.
- **Recompute one indistinguishability decision** against the full bar, not just the newly added items; checking only against siblings is a rejection.
- **Grep for a second generator implementation**; a duplicated code path is a rejection even if it produces correct output.
- **Reject** if the highest index was discovered by directory scan rather than taken from the skill-supplied value.

## Dev Learnings

_Not Done until filled. Required: how often the axis space ran out before five neighbours were found, and what was returned then._

## QA Learnings

_Not Done until filled. Required: whether "more like this" produced neighbours a human could actually tell apart from the approved original._
