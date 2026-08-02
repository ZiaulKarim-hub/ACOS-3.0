# S06-channel-fidelity-and-ceiling-battery — Channel-fidelity, output-ceiling, latency and licence battery

| Field | Value |
|---|---|
| Epic / Story | E0 / ST-01 |
| Type · MoSCoW · Size | diagnostic · MUST · M `[I]` |
| Phase / Demo | Phase 0 / — |
| Depends on | none |
| Requirements | FR-007, FR-008 |
| Acceptance criteria | SL-S06-1 · SL-S06-2 · SL-S06-3 · SL-S06-4 |
| CQ / evidence | CQ18 (confidence 0.25 — **unsolved**) · CQ10 · EL-066 · EL-068 |
| Blocking | SL-S06-2's measurement feeds chunk computation (S17) |

## PM — slice definition

**Objective.** Measure what the hand-carry channel actually does, and re-verify every adopted dependency's licence against its real licence file — replacing four unverified assumptions with four measurements.

**In scope.** (a) Copy-paste fidelity across all three realistic paste paths — rendered view, per-block copy control, conversation export — against a fixture containing fenced blocks, long lines and non-ASCII; (b) an empirical output ceiling measured from real artifacts; (c) round-trip latency for a move operation on the chosen topology; (d) licence re-verification against the actual `LICENSE` file for every adopted dependency; (e) the ~10-minute mid-skill subagent-availability probe.

**Out of scope.** Designing the envelope (S17). Adopting or rejecting a dependency. Treating (e) as a v1 blocker — it is explicitly not one.

**Allowed files / contexts.**
- `spikes/channel/**`, `docs/adr/ADR-06-subagent-availability.md`, `docs/licences/verification-<date>.md` (all new)
- Read-only: any dependency's `LICENSE` file.

**Steps.**
1. Build the fidelity fixture; carry it through each of the three paste paths; diff each result against the source byte for byte; record which paths preserve fenced blocks.
2. Generate progressively larger real artifacts and record where output is truncated or refused. **Do not consult any published ceiling figure** — the ones found in circulated guides were unverifiable and at least one referenced model name appears fabricated.
3. Measure move-operation round-trip latency, median of five.
4. For each adopted dependency, open its actual `LICENSE` file and record the licence string, the commit/tag inspected and the date. Registry summaries are not evidence — one adopted candidate shows two different licences on two registries.
5. Run the subagent-availability probe; record the answer as ADR-06 and mark it non-blocking.

**Definition of Done.**
- Artifacts: three fidelity diffs, the ceiling measurement table, the latency median, the per-dependency licence record, ADR-06.
- Validation: every number is measured; every licence is quoted from the file with its path.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S06-1, SL-S06-2, SL-S06-3, SL-S06-4]`, `verification_method: probe` (SL-S06-3: `grep-assert`).

## Dev — execution contract

Evidence bundle: (1) summary with four one-line answers; (2) traceability FR-007, FR-008 → artifacts; (3) structural quality — fixtures are disposable; (4) functional testing — raw diffs and raw measurements; (5) security/compliance — the licence table, with any discrepancy called out explicitly; (6) operational — how often each measurement decays (the ceiling and the paste paths decay fastest); (7) self-assessment — state that the ceiling is a point-in-time observation of a third-party surface.

## QA — zero-trust verification

- **Re-diff** at least one paste path yourself.
- **Recompute** the latency median from Dev's raw timings; a stated median without five raw values is a rejection.
- **Open** two `LICENSE` files yourself and confirm the recorded strings match; a registry summary in the record is a rejection.
- **Reject** if any published ceiling figure appears anywhere in the artifacts.
- **Reject** if ADR-06 is treated as blocking or as licence to depend on mid-skill subagents.

## Dev Learnings

_Not Done until filled. Required: which paste path preserved fenced blocks, and where the real output ceiling sat relative to a typical chunk._

## QA Learnings

_Not Done until filled. Required: which of the four measurements was most fragile, and what re-verification cadence the licence table needs._
