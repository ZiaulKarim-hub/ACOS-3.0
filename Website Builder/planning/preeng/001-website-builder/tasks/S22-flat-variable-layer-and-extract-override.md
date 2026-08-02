# S22-flat-variable-layer-and-extract-override — Flat variable layer per direction change, machine-owned stylesheet, extract-override

| Field | Value |
|---|---|
| Epic / Story | E6 / ST-07 |
| Type · MoSCoW · Size | build · MUST · S `[I]` |
| Phase / Demo | Phase 1 / — |
| Depends on | S21-token-compiler-dtcg-and-forge |
| Requirements | FR-062, FR-067 |
| Acceptance criteria | SL-S22-1 · SL-S22-2 |
| CQ / evidence | CQ5 |
| Risk | R30 — hundreds of custom properties re-evaluated per drag is a real reflow cost |

## PM — slice definition

**Objective.** Keep drag-time cost off the token graph, and give hand-tuning exactly one sanctioned door.

**In scope.** Compiling the full custom-property set to a **flat variable layer once per direction change**; an instrumentation counter proving zero re-resolutions during a drag; a machine-owned compiled stylesheet with a do-not-hand-edit banner; `extract-override.ts` producing an override file that survives regeneration.

**Out of scope.** Making the stylesheet human-editable. Any per-drag token resolution "for convenience".

**Allowed files / contexts.**
- `scripts/lib/flatten-tokens.ts`, `scripts/tools/extract-override.ts`, `02-system/<directionId>/tokens.css` (machine-owned), `src/overrides/**` (created by the tool only).

**Steps.**
1. Flatten the resolved token graph into a single variable layer at direction-change time; store the direction hash alongside it.
2. Add a counter incremented on every resolution; assert it stays constant across a scripted ten-drag sequence.
3. Write the do-not-hand-edit banner naming the file to edit instead.
4. Implement `extract-override`: given a token path and a desired value, emit an override file entry that the generator will not overwrite.
5. Prove an override survives a full regeneration.

**Definition of Done.**
- Artifacts: flattener, override tool, banner, the drag counter assertion.
- Validation: the counter is unchanged across ten drags; an override survives regeneration byte-identically.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S22-1, SL-S22-2]`, `verification_method: recompute` (SL-S22-2: `exit-code`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-062, FR-067 → file:line; (3) structural quality — flattening is pure; (4) functional testing — the counter transcript and the override survival test; (5) security/compliance — the override path cannot escape the project tree; (6) operational — what to do at 11pm when one value needs nudging without regenerating the system; (7) self-assessment.

## QA — zero-trust verification

- **Run the ten-drag sequence yourself** and read the counter before and after.
- **Regenerate yourself** and diff the override file; any loss is a rejection.
- **Grep the compiled stylesheet** for the banner.
- **Reject** if any code path resolves a token during pointer movement.

## Dev Learnings

_Not Done until filled. Required: the measured flatten cost per direction change, and whether the override path felt safe enough to use._

## QA Learnings

_Not Done until filled. Required: whether the counter is a sufficient proxy for reflow cost or a real measurement is needed._
