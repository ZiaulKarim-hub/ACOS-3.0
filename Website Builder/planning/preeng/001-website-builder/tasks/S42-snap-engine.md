# S42-snap-engine — Snap engine with prioritised target classes and zoom-scaled tolerance

| Field | Value |
|---|---|
| Epic / Story | E9 / ST-13 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 3 / — |
| Depends on | S41-gridline-overlay |
| Requirements | FR-107 |
| Acceptance criteria | A47 · SL-S42-1 · SL-S42-2 |
| CQ / evidence | CQ4 |
| Note | Second rung of the deliberate canvas ordering (overlay → **snap** → drag → handles). Snap is part of the **irreducible core** and is not in the trade-back-out order |

## PM — slice definition

**Objective.** Snap to the four target classes in priority order with tolerance divided by zoom, using interval indexes rather than per-frame scans.

**In scope.** Two 1-D interval indexes per section — one horizontal, one vertical — built **once per layout change**, not per pointer move; four prioritised target classes in strict order: (1) grid lines, (2) sibling edges and centres, (3) section padding and content rails, (4) spacing-scale increments; tolerance of 6–8 CSS px **divided by the current zoom factor**, so snapping stays usable at 25% and at 200%; a instrumentation counter proving no full sibling scan occurs per pointer move; a priority test that constructs a pointer position where two classes are both within tolerance and asserts the higher class wins.

**Out of scope.** Committing anything to the document — this slice resolves a pointer position to a snapped candidate and returns it; the drop algorithm and every write are S43. Distance labels and equal-spacing indicators (S44). The zoom and pan **controls** (S49) — this engine consumes a zoom factor supplied by the shell and must be correct at 0.25 and 2.0 before the control exists. Free-position offsets (S48).

**Allowed files / contexts.**
- `scripts/lib/canvas/snap.ts`, `scripts/lib/canvas/interval-index.ts`, the overlay measurements from S41 (read-only).

**Steps.**
1. Build the interval index from the resolved measurements S41 already produces; index construction is triggered by the same layout-change signal the overlay subscribes to.
2. Query is `O(log n)` over the index; add a counter that increments on any full sibling traversal and assert it stays flat across a synthetic 200-move drag.
3. Resolve candidates class by class in priority order and return the first class that has a hit within tolerance — never a distance comparison across classes, which would let a near sibling edge beat an exact grid line.
4. Divide tolerance by the zoom factor at query time; test at 0.25, 1.0 and 2.0.
5. Return a structured result `{class, axis, value, distance}` so the caller can render the reason for the snap, not just the position.
6. Rebuild both indexes on breakpoint switch, because the track count changes with the direction's breakpoint vocabulary.

**Definition of Done.**
- Artifacts: the snap module, the interval index, the move counter, the priority test, the zoom test.
- Validation: the counter is flat across a 200-move synthetic drag; priority is asserted by a constructed collision per adjacent class pair; tolerance measured at 25% and 200% equals the base tolerance divided by zoom.
- `slice.yaml` mapping — `acceptance_criteria: [A47, SL-S42-1, SL-S42-2]`, `verification_method: exit-code` (A47: `manual-observation`; SL-S42-1: `recompute`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-107 → file:line; (3) structural quality — the engine is pure over `(indexes, point, zoom)` and unit-testable with no DOM; (4) functional testing — the counter output, the three priority-collision cases, the three zoom levels, with numbers; (5) security/compliance — n/a, note it; (6) operational — index rebuild cost per layout change, and what happens on a section with hundreds of siblings; (7) self-assessment.

## QA — zero-trust verification

- **Instrument the counter yourself** and drive your own synthetic drag; a per-move sibling scan hiding behind a cached array is a rejection.
- **Recompute the effective tolerance** at 0.25 and 2.0 from the returned distances rather than trusting the logged tolerance.
- **Construct your own collision** where a sibling centre is closer than a grid line and require the grid line to win; then repeat for classes 2 vs 3 and 3 vs 4.
- **Switch breakpoints** and confirm the indexes were rebuilt, by observing the changed track count in the returned results.
- **Reject** if any snap decision compares distances across classes instead of resolving by priority.

## Dev Learnings

_Not Done until filled. Required: whether strict priority ever produced a snap the user would call wrong, and where the index rebuild cost landed._

## QA Learnings

_Not Done until filled. Required: which class boundary was easiest to get subtly wrong, and how the counter exposed it._
