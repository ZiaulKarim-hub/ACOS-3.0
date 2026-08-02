# S45-keyboard-parity-and-target-size — Keyboard parity for every drag, three verbs, and editor target size

| Field | Value |
|---|---|
| Epic / Story | E9 / ST-14 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 3 / — |
| Depends on | S43-drag-to-place-and-drop-algorithm |
| Requirements | FR-111, FR-112, FR-232 |
| Acceptance criteria | A26 · A27 · SL-S45-1 · SL-S45-2 · SL-S45-3 |
| CQ / evidence | CQ4 · CQ11 |
| Note | **Two WCAG criteria apply to the editor itself** — 2.5.7 Dragging Movements and 2.5.8 Target Size. Keyboard parity is part of the **irreducible core** and is not tradable; thin drag handles, tiny corner grips and dense icon rows violate 2.5.8 by default |

## PM — slice definition

**Objective.** Satisfy the two accessibility criteria that apply to the tool itself, and keep the anchor vocabulary to exactly three verbs.

**In scope.** Keyboard grid stepping as the **single-pointer alternative for every drag**: Arrow moves one cell, Shift+Arrow changes span by one, Tab walks siblings; plus a **select-then-click-destination** path so every drag operation shipped by S43 and S44 has a non-drag equivalent. The anchor/pin control exposing **exactly three verbs** — *align to* (left/centre/right/stretch), *space above/below* (a stepper over the spacing scale), *order* (up/down among siblings) — and no fourth verb anywhere in the UI. A **live bounding-rect check on render** across all editor chrome that reports any control below 24×24 CSS px together with its documented exception, if any.

**Out of scope.** The site's own accessibility gates and the lock-time checklist (S63, S68) — this slice is about the tool, not the output. The reading-order invariant and the `order` hard block (S47) — the *order* verb here reorders siblings in the document, which is a real content-order change; overriding visual order per breakpoint is S47's and is blocked on focusable nodes there. Free-position keyboard handling (S48).

**Allowed files / contexts.**
- `scripts/lib/canvas/keyboard.ts`, `scripts/lib/canvas/anchor-control.ts`, `scripts/lib/a11y/target-size.ts`, the editor chrome components from S29, the drag entry points from S43/S44 (read-only).

**Steps.**
1. Map every drag operation to a keyboard or select-then-click equivalent and record the mapping as a table in the module, so a new drag added later without a partner is visible.
2. Implement Arrow / Shift+Arrow / Tab over the same typed ops the pointer path uses; a keyboard move and a pointer move must produce **identical** document diffs.
3. Build the anchor control with three verbs; enumerate them from one source array so a fourth cannot be added in a template without failing the test.
4. Implement the target-size check with `getBoundingClientRect()` on render, **after `await document.fonts.ready`**, reporting `{selector, width, height, exception?}`.
5. Record the four documented exceptions explicitly; a control claiming an undocumented exception fails.
6. Make the report visible in the editor's own health surface, not only in a test log.

**Definition of Done.**
- Artifacts: keyboard module, anchor control, target-size checker, the drag→keyboard mapping table, the render-time report.
- Validation: every S43/S44 drag has a recorded non-drag path; keyboard and pointer produce identical diffs for the same move; exactly three verbs enumerated; the bounding-rect report lists every chrome control with measured size.
- `slice.yaml` mapping — `acceptance_criteria: [A26, A27, SL-S45-1, SL-S45-2, SL-S45-3]`, `verification_method: recompute` (A26 and SL-S45-1: `manual-observation`; SL-S45-2: `grep-assert`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-111, FR-112, FR-232 → file:line; (3) structural quality — pointer and keyboard share one op-dispatch path; (4) functional testing — the diff-equality comparison per operation, and the full measured-size table; (5) security/compliance — n/a for security; state the accessibility claim ceiling and that no conformance is claimed; (6) operational — how the check behaves on a collapsed panel or a hidden control; (7) self-assessment.

## QA — zero-trust verification

- **Drive every drag operation by keyboard only** and record your own transcript; one drag without a partner is a rejection.
- **Diff the documents yourself** after a pointer move and after the equivalent keyboard move; any difference is a rejection.
- **Recompute the bounding rects yourself** over the chrome after fonts settle; do not trust the logged sizes. Any control under 24×24 without a documented exception is a rejection.
- **Count the verbs in the rendered DOM**, not in the source array; a fourth verb reachable in the UI is a rejection.
- **Reject** if the target-size check runs only at lock, or only in tests rather than on render.

## Dev Learnings

_Not Done until filled. Required: which drag was hardest to give a keyboard equivalent, and which chrome control failed 2.5.8 first._

## QA Learnings

_Not Done until filled. Required: whether measuring before font settling changed any pass/fail verdict._
