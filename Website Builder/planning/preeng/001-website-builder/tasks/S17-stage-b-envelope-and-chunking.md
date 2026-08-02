# S17-stage-b-envelope-and-chunking — Stage-B prompt, envelope manifest, terminator and runtime chunk computation

| Field | Value |
|---|---|
| Epic / Story | E4 / ST-05 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 1 / — |
| Depends on | S16-token-manifest-and-stage-a-prompt · S06-channel-fidelity-and-ceiling-battery |
| Requirements | FR-045, FR-047, FR-048 |
| Acceptance criteria | SL-S17-1 · SL-S17-2 · SL-S17-3 |
| CQ / evidence | CQ18 (**unsolved**) · CQ13 · EL-066 |
| Risk | R3 — silent truncation produces syntactically valid, semantically wrong output with no error anywhere |

## PM — slice definition

**Objective.** Make truncation detectable by construction, and size chunks from measured artifacts rather than any published ceiling.

**In scope.** The Stage-B prompt (sections 0, 2, 4, 5 reused verbatim; section 3 replaced with the full token expansion plus identity-carrying component instances for one direction); the envelope manifest (declared file list, per-file line counts, hash prefixes, smallest-first ordering, per-run random terminator); chunk computation from measured artifact sizes at runtime; up-front surfacing of the usage-tier cost of a two-stage run across N directions.

**Out of scope.** The importer (S18/S19). Any hardcoded ceiling constant. Promising a paste count — the success criterion treats three pastes as a **retry budget**, not the mechanism.

**Allowed files / contexts.**
- `scripts/lib/prompt-stage-b.ts`, `scripts/lib/envelope.ts`, `scripts/lib/chunker.ts`, `01-prompt/**`, `02-system/manifest.json` (write).

**Steps.**
1. Assemble Stage B by reusing the shared sections byte-for-byte from Stage A; assert equality by hash.
2. Generate the envelope: file list, per-file line counts, hash prefixes, smallest-first ordering, a per-run random terminator string.
3. Compute chunk sizes from the measured artifact sizes for this run; assert by grep that no ceiling constant exists in the source.
4. Surface the usage-tier cost before the first chunk is emitted.
5. Emit the copy-ready terminal display, one chunk at a time, each carrying the manifest and the terminator.

**Definition of Done.**
- Artifacts: Stage-B assembler, envelope generator, chunker, a generated envelope sample.
- Validation: the shared-section hash equality; the no-constant grep; a chunking run recorded against measured sizes.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S17-1, SL-S17-2, SL-S17-3]`, `verification_method: exit-code` (SL-S17-2: `grep-assert`, SL-S17-3: `manual-observation`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-045, FR-047, FR-048 → file:line; (3) structural quality — the envelope is one module used by both the emitter and the importer; (4) functional testing — a full emission with the envelope and the terminator, plus the hash equality proof; (5) security/compliance — the terminator is per-run random, so a replayed old payload fails validation; (6) operational — what to do when a chunk exceeds the measured ceiling; (7) self-assessment: the channel ceiling is unknown and this design deliberately does not depend on knowing it.

## QA — zero-trust verification

- **Hash the shared sections yourself** from both prompts and require equality.
- **Grep the source yourself** for any numeric ceiling constant.
- **Verify the terminator differs** across two runs.
- **Recompute** one file's line count and hash prefix from the emitted envelope.
- **Reject** if the usage-tier cost is surfaced after emission rather than before.

## Dev Learnings

_Not Done until filled. Required: the measured chunk count for a real direction, and whether smallest-first ordering helped detection._

## QA Learnings

_Not Done until filled. Required: whether a hand-truncated payload was actually caught by the envelope alone._
