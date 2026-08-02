# S41-gridline-overlay — Gridline overlay derived from computed styles

| Field | Value |
|---|---|
| Epic / Story | E9 / ST-13 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 3 / — |
| Depends on | S29-editor-shell-and-overlay · S26-breakpoint-vocabulary-and-cascade |
| Requirements | FR-100 |
| Acceptance criteria | A39 · SL-S41-1 · SL-S41-2 |
| CQ / evidence | CQ4 |
| Note | **First slice of the canvas (DECISION-1 option B pulls E9 into v1).** Gridlines are named in the trade-back-out order as part of the **irreducible core** — not tradable. The ordering of this epic is deliberate: overlay → snap (S42) → drag (S43) → handles (S44) |

## PM — slice definition

**Objective.** Paint the real resolved grid tracks as the snap target, in the out-of-iframe overlay so they vanish at LOCK by construction.

**In scope.** Reading `getComputedStyle(section).gridTemplateColumns` and painting **those exact resolved tracks**; the same for the row axis (`grid-auto-rows: var(--wb-row-unit)`) and the gaps; re-derivation on layout change, container resize and breakpoint switch; rendering in the **out-of-iframe overlay** established by S29, aligned to the same-origin preview iframe's measured box; a per-archetype test proving painted positions equal the computed template columns for three different section archetypes; a capture proving zero overlay pixels appear inside the preview.

**Out of scope.** Snapping and tolerance (S42). Any drag, drop or commit (S43). Rulers, guides and zoom (S49). A hand-authored or decorative grid of any kind — the overlay **is** the snap target, so a drawn approximation is a defect, not a shortcut. Scrubbing the overlay at LOCK: it lives outside the iframe and therefore disappears by construction, and the evidence must state that rather than adding a removal step.

**Allowed files / contexts.**
- `scripts/lib/canvas/overlay-grid.ts`, `scripts/lib/canvas/measure.ts`, the S29 overlay mount point, the breakpoint vocabulary from S26 (read-only).

**Steps.**
1. Measure the section's box and its computed `gridTemplateColumns` / row unit / gaps; never re-derive tracks from the document model, because the resolved value is what the user is aiming at.
2. **`await document.fonts.ready` before any `getBoundingClientRect`** — an unsettled font changes the measured box and produces a grid that is subtly wrong everywhere.
3. Paint track edges and gap bands into the overlay layer, positioned in overlay coordinates derived from the iframe's measured rect.
4. Subscribe to layout changes: `ResizeObserver` on the iframe and on the section, plus the breakpoint-switch event; recompute on each, never per animation frame.
5. Add the three-archetype test: for each, assert painted x-positions equal the computed template columns within one device pixel.
6. Capture the preview with the overlay active and assert zero overlay pixels in the captured image.

**Definition of Done.**
- Artifacts: the overlay module, the measurement module, the three-archetype test, the capture and its assertion.
- Validation: painted tracks equal computed tracks for three archetypes at `base`, `md` and `sm`; the preview capture contains no overlay pixels; no overlay DOM node exists inside the iframe.
- `slice.yaml` mapping — `acceptance_criteria: [A39, SL-S41-1, SL-S41-2]`, `verification_method: recompute` (SL-S41-2: `screenshot-diff`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-100 → file:line; (3) structural quality — measurement is a pure function of a rect plus a computed style, unit-testable without a browser paint; (4) functional testing — the per-archetype comparison table with measured numbers, not prose; (5) security/compliance — n/a, note it, and confirm the overlay reads the same-origin iframe only; (6) operational — what happens when the section is not a grid container at all, and how the overlay behaves during a breakpoint switch; (7) self-assessment.

## QA — zero-trust verification

- **Read `getComputedStyle(section).gridTemplateColumns` yourself** for each of the three archetypes and compare to the painted positions you measure from the overlay DOM. A logged match you cannot reproduce is a rejection.
- **Query the iframe document yourself** for any overlay element; one hit is a rejection.
- **Take your own capture** of the preview and inspect it for overlay pixels rather than trusting the attached image.
- **Resize the preview and switch breakpoints** and confirm the tracks follow; a grid painted once at mount is a rejection.
- **Reject** if any track position is computed from the document model rather than from resolved styles.

## Dev Learnings

_Not Done until filled. Required: where the resolved tracks disagreed with what the document model implied, and what that disagreement would have cost the snap engine._

## QA Learnings

_Not Done until filled. Required: which archetype exposed the largest measurement error, and whether font settling was the cause._
