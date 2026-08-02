# S44-span-resize-and-spacing-handles — Span resize, padding/gap handles on the scale, and smart guides

| Field | Value |
|---|---|
| Epic / Story | E9 / ST-14 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 3 / — |
| Depends on | S43-drag-to-place-and-drop-algorithm |
| Requirements | FR-108, FR-109, FR-110 |
| Acceptance criteria | A28 · SL-S44-1 · SL-S44-2 · SL-S44-3 |
| CQ / evidence | CQ4 |
| Note | The token-named readout is **the mechanic that stops direct manipulation destroying the token system**. Smart-guide distance labels and the padding/gap handles sit late in the trade-back-out order — after the canvas tail and the free-position hatch — and are traded only in that order |

## PM — slice definition

**Objective.** Make direct manipulation teach the token system rather than erode it, with token-named readouts and fluid-consequence feedback.

**In scope.** Span resize by **whole cells only**, with a live "6 of 12 · 50%" fraction-and-percentage readout during the drag, so the user learns the fluid consequence rather than memorising a pixel number. Padding and gap drag handles that snap to **discrete spacing-scale steps only** and display the **token name** (`space-6`), never a raw pixel value — and where an off-scale value is **impossible by construction**: the `set-space` / `set-align` op rejects a value that is not on the scale or not a token with 400, so the handle cannot commit one even if the UI is bypassed. Smart alignment guides with **live distance labels in the accent colour**, plus an **equal-spacing indicator when three or more siblings match**.

**Out of scope.** Keyboard span stepping — Shift+Arrow is S45's, and this slice must not ship a partial keyboard path. Drag-to-place itself (S43). Drag-out rulers and guides stored as fractions (S49). Free-position offsets, which are not on the spacing scale at all (S48). Per-breakpoint blast-radius language on the chip (S46).

**Allowed files / contexts.**
- `scripts/lib/canvas/resize.ts`, `scripts/lib/canvas/spacing-handles.ts`, `scripts/lib/canvas/guides.ts`, the snap engine (S42) and the op client (S31), read-only; the spacing-scale tokens from the token compiler (S21), read-only.

**Steps.**
1. Implement span resize over the snap engine's grid-line class; commit whole cells through `set-span`; render the fraction-and-percentage readout from the resolved track count, not from a constant 12.
2. Implement padding/gap handles that resolve a pointer delta to the **nearest scale step** and display that step's token name; the readout never shows a computed pixel value.
3. Make the server the enforcement point: post an off-scale value directly and require 400. The UI restriction is convenience; the op rejection is the construction.
4. Implement guides with live distance labels in the accent colour, computed from measured rects after `document.fonts.ready`.
5. Detect equal spacing across three or more siblings and raise the indicator.
6. Record every commit through the typed-op path so undo and the history entry behave exactly as they do for a drag.

**Definition of Done.**
- Artifacts: resize module, spacing-handle module, guide module, the off-scale rejection test, the equal-spacing detector.
- Validation: a resize commits whole cells and the readout matches the recomputed fraction; an off-scale `set-space` POST returns 400; a `grep` of the handle path finds no raw-pixel readout; the equal-spacing indicator fires at three matching siblings and not at two.
- `slice.yaml` mapping — `acceptance_criteria: [A28, SL-S44-1, SL-S44-2, SL-S44-3]`, `verification_method: grep-assert` (SL-S44-2: `exit-code`; SL-S44-1/3: `manual-observation`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-108, FR-109, FR-110 → file:line; (3) structural quality — step resolution is a pure function of `(delta, scale)`; (4) functional testing — the readout table, the 400 transcript, the equal-spacing cases at two and three siblings; (5) security/compliance — the off-scale rejection is server-side, evidenced by transcript; (6) operational — what a handle does when the direction's scale has no adjacent step in range; (7) self-assessment.

## QA — zero-trust verification

- **Recompute the fraction and percentage yourself** from the persisted `colSpan` and the resolved track count; a readout you cannot reproduce is a rejection.
- **POST an off-scale spacing value directly to the server**, bypassing the UI, and require 400. A UI-only restriction is a rejection of SL-S44-2.
- **`grep` the handle and readout code** for pixel formatting; a token name shown alongside a raw pixel value is still a rejection.
- **Construct a three-sibling equal-spacing case and a two-sibling case** yourself and confirm the indicator fires only on the first.
- **Reject** if any handle commits without going through the typed-op path, or if a resize produces a non-integer span.

## Dev Learnings

_Not Done until filled. Required: where the scale had no usable adjacent step and what the handle did, and whether the token-name readout changed how spacing was chosen._

## QA Learnings

_Not Done until filled. Required: whether any path could still commit an off-scale value, and how it was found._
