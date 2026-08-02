# S49-canvas-tail-zoom-rulers-multiselect — Canvas tail: zoom/pan, rulers, guides, marquee multi-select, align and distribute

| Field | Value |
|---|---|
| Epic / Story | E9 / ST-16 |
| Type · MoSCoW · Size | build · COULD · L `[I]` |
| Phase / Demo | Phase 3 / — |
| Depends on | S44-span-resize-and-spacing-handles · S45-keyboard-parity-and-target-size |
| Requirements | FR-119, FR-121 |
| Acceptance criteria | A47 · SL-S49-1 · SL-S49-2 · SL-S49-3 |
| CQ / evidence | CQ4 |
| Note | **This slice is explicitly first in the trade-back-out order** (canvas tail → free-position hatch → smart-guide distance labels → padding/gap handles). Gridlines, snap, drag-to-place, keyboard parity and the override cascade are the irreducible core of DECISION-1 B and are **not** tradable |

## PM — slice definition

**Objective.** Deliver the tail of the canvas if budget allows, knowing it is the first scope traded back out.

**In scope.** Canvas zoom across the documented 25–200% range with **tolerance divided by zoom** (the snap engine from S42 already consumes a zoom factor; this slice supplies the control that moves it) and **space-drag panning**. Rulers along both axes. Drag-out guides **stored as fractions, never pixels**, so a guide survives a canvas resize and a breakpoint switch. Marquee and multi-select over the section's blocks. Align and distribute across a multi-selection, committed through the same typed ops a single-block edit uses. The ~12 section archetypes shipped as `grid-template-areas` **per direction**, where dragging a block off its area promotes **that block only** to explicit integer placement on the same grid — never the whole section.

**Out of scope.** Anything in the irreducible core. Re-implementing snap, drag or the drop algorithm — this slice adds a viewport transform and a selection model on top of them. Free positioning (S48). If the canvas overruns and this slice is dropped, the drop is **recorded** in the plan's trade-back-out record rather than silently omitted, and that record is itself a deliverable of this slice's decision.

**Allowed files / contexts.**
- `scripts/lib/canvas/viewport.ts`, `scripts/lib/canvas/rulers.ts`, `scripts/lib/canvas/guides-store.ts`, `scripts/lib/canvas/selection.ts`, `scripts/lib/canvas/align-distribute.ts`, `scripts/lib/canvas/archetypes/**`, the snap engine and drop algorithm (read-only).

**Steps.**
1. Implement the viewport transform once, at the overlay layer, so the gridline overlay, rulers and hit-testing all read the same zoom and pan values.
2. Feed the zoom factor into the snap engine's tolerance divisor; assert usable snapping at 25% and at 200% (A47).
3. Store each drag-out guide as an axis plus a **fraction of the section's resolved extent**; recompute its pixel position on every layout change.
4. Implement marquee selection with a selection model that the keyboard path from S45 can also drive; align and distribute commit as one transaction so undo restores the whole selection in one step.
5. Author the archetypes as `grid-template-areas` per direction; on the first off-area drag, promote **only** the dragged block to explicit integers on the same grid and leave every sibling on its area.
6. If the slice is traded out, write the drop record naming what was dropped, when and why.

**Definition of Done.**
- Artifacts: viewport, rulers, fraction-stored guides, selection model, align/distribute, the archetype set, and — if traded out — the recorded drop.
- Validation: snapping is usable at 25% and 200% with measured tolerance; a stored guide survives a canvas resize at the same fraction; an off-area drag promotes exactly one block; align/distribute is one undo step.
- `slice.yaml` mapping — `acceptance_criteria: [A47, SL-S49-1, SL-S49-2, SL-S49-3]`, `verification_method: manual-observation` (SL-S49-2: `exit-code`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-119, FR-121 → file:line; (3) structural quality — one viewport transform consumed by every overlay-space consumer, proven by call graph; (4) functional testing — measured tolerance at three zoom levels, the guide round-trip across a resize, the single-block promotion diff, the one-entry undo check; (5) security/compliance — n/a, note it; (6) operational — pan/zoom behaviour on a long page, and archetype authoring cost per direction `[I]`; (7) self-assessment, stating explicitly whether this slice was delivered or traded out.

## QA — zero-trust verification

- **Measure snap tolerance yourself** at 25%, 100% and 200% from the returned snap distances and require the divide-by-zoom relationship to hold.
- **Read a stored guide out of the document yourself** and confirm it is a fraction; a pixel value is a rejection.
- **Resize the canvas** and recompute the guide's position from its fraction; a guide that drifts is a rejection.
- **Diff the document after an off-area drag** and require that exactly one block gained explicit integer placement; a section-wide promotion is a rejection.
- **Count `history.jsonl` entries** after one align-and-distribute over a multi-selection; more than one is a rejection.
- **If the slice was traded out**, verify the drop record exists and names what was dropped; a silent omission is a rejection.

## Dev Learnings

_Not Done until filled. Required: whether the viewport transform leaked into any consumer that should have been zoom-agnostic, and the real authoring cost of the archetype set._

## QA Learnings

_Not Done until filled. Required: which tail feature was closest to disturbing a core mechanic, and how it was caught._
