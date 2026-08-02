# S03-o8-substrate-spike — Build-substrate spike: framework versus plain generated HTML

| Field | Value |
|---|---|
| Epic / Story | E0 / ST-01 |
| Type · MoSCoW · Size | diagnostic · MUST · M `[I]` |
| Phase / Demo | Phase 0 / — |
| Depends on | none |
| Requirements | FR-005 |
| Acceptance criteria | SL-S03-1 · SL-S03-2 |
| CQ / evidence | CQ9 · EL-085 (toolchain conflict in the two-build gate procedure) |
| Blocking | Gates nothing, but **invariant I6 holds until it lands**: no code may hard-depend on any framework |

## PM — slice definition

**Objective.** Decide the preview/build substrate on measured evidence — a framework dev-server, or plain generated HTML from a TypeScript renderer — or confirm that the choice stays open under I6.

**In scope.** The same one-page render produced twice, once per candidate; scoring on live-editability, LOCK cleanliness (how much has to be scrubbed), dependency surface, and what each implies for the two-build comparison's installer invocation; ADR-03.

**Out of scope.** Choosing the process topology (S04). Building the real renderer (S25). Adopting any framework into the product tree.

**Allowed files / contexts.**
- `spikes/substrate/{a-framework,b-plain}/**` (new, disposable)
- `docs/adr/ADR-03-substrate.md` (new)
- **No file under `scripts/` or `app/` may be modified.**

**Steps.**
1. Build the same page on both candidates from the same token set and the same content.
2. Measure, for each: number of third-party runtime artifacts appearing in the built output; number of distinct strings a scrub would have to remove; time from source change to visible update; and whether a byte-comparable build is even conceivable on it.
3. Record the installer/manifest invocation each candidate implies, because the carried two-build procedure is written against a different package manager than the skill's own runtime (NA-11).
4. Write ADR-03 with the decision **or** an explicit "still open, I6 remains in force".

**Definition of Done.**
- Artifacts: both spike trees, a scored comparison table with measured values, ADR-03.
- Validation: every score is a measured number or a counted string, never an impression.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S03-1, SL-S03-2]`, `verification_method: manual-observation`.

## Dev — execution contract

Absolute paths everywhere. No product path touched. Evidence bundle: (1) summary with the decision or the explicit non-decision; (2) traceability FR-005 → spike trees; (3) structural quality — both spikes produce the identical rendered page, proven by a screenshot diff; (4) functional testing — the scored table with raw measurements; (5) security/compliance — note any remote origin either substrate introduces by default, since a remote origin is simultaneously a determinism and a licence-evidence violation; (6) operational — what re-running costs; (7) self-assessment — including which score is the weakest measurement.

## QA — zero-trust verification

- **Recompute** at least two scores yourself (the scrub-string count and the built-output artifact count) with your own `grep -r` and record the commands.
- **Reject** if the two spikes did not render the identical page — an unequal comparison is not a comparison.
- **Reject** if ADR-03 selects a substrate without stating what it implies for the two-build gate's installer invocation.
- **Reject** if any product file was modified.

## Dev Learnings

_Not Done until filled. Required: which substrate produced fewer strings to scrub, and whether live-editability differed enough to matter._

## QA Learnings

_Not Done until filled. Required: whether the scoring criteria were the right ones, and which one you would replace next time._
