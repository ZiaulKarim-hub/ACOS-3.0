# S04-o4-topology-spike-adr — Process-topology spike and ADR

| Field | Value |
|---|---|
| Epic / Story | E0 / ST-01 |
| Type · MoSCoW · Size | diagnostic · MUST · M `[I]` |
| Phase / Demo | Phase 0 / — |
| Depends on | S01-gate-16a-and-launcher-rung · S03-o8-substrate-spike |
| Requirements | FR-003 |
| Acceptance criteria | SL-S04-1 · SL-S04-2 |
| CQ / evidence | CQ3 |
| Blocking | Only invariants I1–I6 may be built until this lands |

## PM — slice definition

**Objective.** Decide single-origin proxy (one server proxies the preview) versus two-origin iframe plus message passing, on measured evidence rather than preference.

**In scope.** The **same** two-page vertical slice implemented on both topologies, one working session each; scoring on channel LOC, preview-only screenshot achievability, round-trip latency for a move operation, and behaviour after killing and restarting the preview process; ADR-04.

**Out of scope.** The real editor shell (S29). The security posture (S37) beyond noting how many origins each topology needs in the allowlist. Any product code.

**Allowed files / contexts.**
- `spikes/topology/{a-two-origin,b-single-origin}/**` (new, disposable)
- `docs/adr/ADR-04-topology.md` (new)
- **No product path.**

**Steps.**
1. Implement the same two-page slice on both topologies, each carrying the same minimal move operation.
2. Count the lines of channel code (message plumbing, origin handling, proxy) for each.
3. Capture a preview-only screenshot on each; record whether zero editor chrome is achievable, and how.
4. Measure round-trip latency for one move operation, median of five, on each.
5. Kill the preview process on each and record what the editor does — specifically whether unsaved state survives (invariant I5).
6. Write ADR-04, naming which of I1–I6 the decision changes and which it leaves untouched.

**Definition of Done.**
- Artifacts: both spikes, a scored table with measured values, both preview screenshots, ADR-04.
- Validation: latency is a median of five measured runs; the restart behaviour is observed, not reasoned about.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S04-1, SL-S04-2]`, `verification_method: manual-observation`.

## Dev — execution contract

Reuse the launcher rung that passed in S01 for both spikes; do not invent a second launch path. Evidence bundle: (1) summary with the decision; (2) traceability FR-003 → both spikes; (3) structural quality — both spikes implement the identical operation; (4) functional testing — the scored table, the two screenshots, the restart transcripts; (5) security/compliance — how many origins each topology puts in the allowlist and what that costs; (6) operational — which topology is easier to shut down cleanly, since two servers means two things to forget; (7) self-assessment.

## QA — zero-trust verification

- **Re-measure** the move-operation latency yourself on the chosen topology; a single Dev-reported number is not evidence.
- **Recompute** the preview-only screenshot claim: capture the preview yourself and grep the resulting image's source page for editor chrome markers.
- **Reject** if the two spikes implemented different operations.
- **Reject** if ADR-04 does not state which invariants it touches.
- **Reject** if the restart test was skipped — that is the test that decides invariant I5.

## Dev Learnings

_Not Done until filled. Required: which topology needed less channel code, and whether the preview-only capture was harder than expected on either._

## QA Learnings

_Not Done until filled. Required: whether the scoring dimensions predicted the real difficulty, and what an independent re-measure changed._
