# S43-drag-to-place-and-drop-algorithm — Drag-to-place writing grid integers, with the normative drop algorithm

| Field | Value |
|---|---|
| Epic / Story | E9 / ST-13 |
| Type · MoSCoW · Size | build · MUST · XL `[I]` |
| Phase / Demo | Phase 3 / — |
| Depends on | S42-snap-engine · S31-typed-ops-autosave-history-undo |
| Requirements | FR-101, FR-102, FR-103, FR-104, FR-105, FR-106 |
| Acceptance criteria | A40 · SL-S43-1 · SL-S43-2 |
| CQ / evidence | CQ4 · CQ2 |
| Note | **NA-17** — §11.2.1 supplies a **normative** drop algorithm with **nine acceptance branches AC1–AC9** that the carried technical requirements did not represent. They are adopted here as criteria, branch by branch, and may not be paraphrased away |

## PM — slice definition

**Objective.** Implement the full normative drop algorithm including row derivation, span preservation, displace-down occupancy with ghost preview, re-parenting and the three legal rejections.

**In scope — the nine branches, each separately tested.**
1. **Column derivation** — `col = clamp(1, round((x − gridLeft) / (colWidth + gap)) + 1, cols + 1)`; persisted as `grid-column: <start> / span <n>`, integers, inherently fluid (A40: 6 of 12 is 50% at both 768 and 1440).
2. **Row derivation** — `row = clamp(1, round((y − gridTop) / (rowUnit + rowGap)) + 1, sanityRowCap)` over the explicit row axis sized from the direction's spacing scale via `grid-auto-rows: var(--wb-row-unit)`; `sanityRowCap ≈ 200` is a **runaway-drag reject, not a layout constraint**.
3. **Span preservation** — the dragged block keeps `colSpan`/`rowSpan`; `colSpan` clamps to `min(colSpan, targetCols)` anchored at the drop column when the target section is narrower, and **the clamp is shown in the pre-commit chip before commit**; `rowSpan` is never clamped.
4. **Displace-down cascade** — overlapped siblings shift by the dragged block's `rowSpan + rowGap`, cascading, with a **live ghost preview of every block that will move, before pointer release**.
5. **Art z-order** — `role: "art"` blocks resolve overlap by z-order instead of displacing.
6. **Opt-in overlap** — a per-drop "Allow overlap here" writes an explicit `z` and increments a **visible overlap counter**.
7. **Cross-section re-parenting** — the node re-parents with **no auto-compaction anywhere in the document**.
8. **Boundary-zone append** — a drop in a boundary zone appends to the nearer section's near edge and **never merges grids**.
9. **The three rejections** — snap back with an outline flash **and an inline message, never a silent clamp**: onto another block's internal flow-only region; where the cascade would reflow a step inside a reflow-forbidding pinned/scrubbed container; where `row` would exceed `sanityRowCap`.

Also in scope: dispatching `move-node` / `set-span` through the S31 typed-op engine (400 on non-integer placement, 409 on a stale etag), and **coalescing a continuous drag into one undo entry**.

**Out of scope.** Span-resize and padding/gap handles (S44). Keyboard equivalents (S45) — this slice ships pointer drag only and S45 supplies the WCAG 2.5.7 alternative. Per-breakpoint override writes and the chip's cascade behaviour (S46) — the chip renders here, its blast-radius language is S46's. Free positioning (S48). Multi-select drag (S49).

**Allowed files / contexts.**
- `scripts/lib/canvas/drop.ts`, `scripts/lib/canvas/occupancy.ts`, `scripts/lib/canvas/ghost.ts`, `scripts/lib/canvas/precommit-chip.ts`, the snap engine (S42) and the op client (S31), both read-only.

**Assumption (recorded).** FR-106 labels the three rejections `§11.2.1 AC7–AC9` while the slice-local criterion enumerates nine branches with the rejections as the ninth; test ids follow the nine-branch enumeration above and each rejection carries its own case `[I]`.

**Definition of Done.**
- Artifacts: drop algorithm, occupancy model, ghost preview, pre-commit chip, nine branch tests, the integers-only grep.
- Validation: all nine branches pass; a drag produces exactly one `history.jsonl` entry; `grep` proves no pixel coordinate is written to any document; a 6-of-12 block measures 50% at 768 and at 1440.
- `slice.yaml` mapping — `acceptance_criteria: [A40, SL-S43-1, SL-S43-2]`, `verification_method: exit-code` (A40: `recompute`; SL-S43-2: `grep-assert`).

## Dev — execution contract

Evidence bundle: (1) summary naming each of the nine branches and its test; (2) traceability FR-101…FR-106 → file:line; (3) structural quality — occupancy is a pure function of the sibling set, testable without a browser; (4) functional testing — one recorded case per branch with the resulting document diff; (5) security/compliance — every write goes through the typed op and the allowlist, never a file path; (6) operational — behaviour at `sanityRowCap`, and cost of the cascade on a dense section; (7) self-assessment.

## QA — zero-trust verification

- **Recompute `col` and `row` yourself** from a recorded pointer position, `gridLeft`, `colWidth` and `gap`, and compare to the persisted integers.
- **Measure the 6-of-12 block yourself** at 768 and 1440 and require 50% at both.
- **Run your own** `grep -rnE '"(x|y|left|top)":\s*[0-9]+(\.[0-9]+)?' pages/*.doc.json` and any `px` search over doc-owned JSON; one pixel coordinate is a rejection.
- **Construct each of the three rejection cases yourself** and require an inline message; a silent clamp is a rejection.
- **Force `row` past `sanityRowCap`** and confirm the reject, not a clamp.
- **Count `history.jsonl` entries** after one continuous drag; more than one is a rejection.
- **Confirm the ghost preview renders before pointer release**, not after commit.

## Dev Learnings

_Not Done until filled. Required: which of the nine branches was hardest to make deterministic, and whether the cascade ever produced a layout the user did not predict._

## QA Learnings

_Not Done until filled. Required: which branch's test would have passed against a wrong implementation, and what tightened it._
