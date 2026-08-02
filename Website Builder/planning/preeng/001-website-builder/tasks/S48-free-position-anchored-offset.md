# S48-free-position-anchored-offset — Free-position escape hatch: anchored offset, authored flow fallback, demotion and lock gate

| Field | Value |
|---|---|
| Epic / Story | E9 / ST-15 |
| Type · MoSCoW · Size | build · MUST · L `[I]` |
| Phase / Demo | Phase 3 / — |
| Depends on | S46-override-cascade-and-precommit-chip |
| Requirements | FR-116, FR-117 |
| Acceptance criteria | A43 (amended, NA-06) · A44 · A45 · A48 · SL-S48-1 · SL-S48-2 · SL-S48-3 |
| CQ / evidence | CQ2 · CQ4 · EL-072 |
| Note | **NA-06** — the auto-demote trigger is **≤390px** while the `sm` media-query boundary is **≤479px**. They are **not the same number**; 479 is a width no switcher, preview frame or gate ever renders, so a user could never watch the demotion fire there. Both call sites are a required cross-section fix (`§12.3-O31`) |

## PM — slice definition

**Objective.** Ship the escape hatch narrowly: parent or grid-cell anchors only, with reserved space, an authored fallback, a visible counter and a hard lock gate.

**In scope.** Free mode as **anchored offset, never raw absolute**: `{mode: "free", anchor: {target: "parent" | "grid-cell", edge, cell?}, offset: {x, y as % or clamp()}, z?, minBlockSizeReserved, flowFallback: {col, colSpan, row, order, z?}}`. Anchor targets restricted to `parent` or a grid line/cell — **sibling anchoring is absent from the schema, not merely hidden in the UI**. Reservation of `min-block-size` on the parent at drop time (A45). Per-block **and** per-breakpoint application. **Auto-demotion to normal flow at ≤390px** (A43) using the **authored** `flowFallback` written at drop time and independently editable in the Navigator; z-stacking is dropped at the small key unless `flowFallback` carries an explicit `z`; absence of an `sm` key **means flow at `sm`**, which is exactly how demotion is represented. A per-section cap of 2 with a **visible counter** (`set-free-position` → 422 when exceeded). Disabled by default on pinned/scrubbed containers, forcing requires explicit confirmation (A48 → 422 without it). A LOCK-gate check that **fails** if free positioning produces document `overflow-x` or leaves its parent's box at any checked width (A44), plus a grep proving the locked export carries **no runtime positioning script**.

**Stated limit, not solved.** Sibling anchoring is held **behind a prototype**: the subgrid-promotion compile strategy behind it is **UNPROTOTYPED with no known mitigation** (`§11.4`-linked open question, DECISIONS item 6), and CSS anchor positioning is ruled out for load-bearing layout. The R9 residual also stands unsolved: for art whose composition depends on absolute relationships across the viewport, the only answer is to treat the composition as **one component with internal responsive rules** — which means the user cannot drag its parts individually, which is exactly what they asked for.

**Out of scope.** Sibling anchoring in any form. The lock-time checklist wiring (S68) — this slice supplies the A44 check as a callable function plus its fixtures. Zoom, rulers and multi-select (S49).

**Allowed files / contexts.**
- `scripts/lib/canvas/free-position.ts`, `scripts/lib/canvas/flow-fallback.ts`, `scripts/lib/gates/free-position-gate.ts`, the `set-free-position` / `clear-free-position` op validators (S31), the Navigator from S30 (fallback editing surface).

**Assumption (recorded).** The per-section cap is stated as "~2"; this slice enforces **2**, read from the project record rather than hardcoded, and records the value used `[I]`. The "checked widths" for A44 are taken to be the previewed widths of the breakpoint vocabulary — 390, 768, 1280 and the preview-only 1440 `[I]`.

**Definition of Done.**
- Artifacts: free-position module, fallback writer and Navigator editing surface, the counter, the A44 gate function, schema and op validators.
- Validation: a sibling anchor value is rejected by the **schema**, not by the UI; every free drop writes a `flowFallback` and a reserved `min-block-size`; demotion fires at ≤390px and not at 479px; the third free block in a section returns 422; a forced pinned-container placement without confirmation returns 422; an overflow-producing fixture fails the gate; the locked export greps clean of positioning script.
- `slice.yaml` mapping — `acceptance_criteria: [A43, A44, A45, A48, SL-S48-1, SL-S48-2, SL-S48-3]`, `verification_method: exit-code` (A45: `recompute`; A48: `manual-observation`; SL-S48-1/3: `grep-assert`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-116, FR-117 → file:line; (3) structural quality — one anchor resolver, one fallback writer; (4) functional testing — the demotion observed at 390 with a screenshot, the cap, the two 422 cases, the overflow fixture; (5) security/compliance — the locked export contains no runtime positioning JS, evidenced by grep; (6) operational — what happens to a free block when its anchor cell disappears after a grid change; (7) self-assessment, stating the unprototyped sibling-anchoring limit and the R9 residual plainly rather than implying they are handled.

## QA — zero-trust verification

- **Grep the schema yourself** for any sibling anchor target; presence anywhere in the schema — even unreachable from the UI — is a rejection.
- **Render at 391px and at 390px** and confirm demotion fires at the trigger width; then render at 479px and confirm the trigger is **not** conflated with the media-query boundary.
- **Recompute the reserved `min-block-size`** from the parent's measured box; a reservation claimed but not applied is a rejection.
- **Place a third free block** in a section yourself and require 422 plus a counter that was visible before the attempt.
- **Run your own** `grep -rn` over `dist/published/**` for positioning script; one hit is a rejection.
- **Reject** if any evidence describes sibling anchoring as deferred-but-designed; the compile strategy is unprototyped and has no known mitigation.

## Dev Learnings

_Not Done until filled. Required: whether the authored `flowFallback` was ever wrong enough that the user had to edit it by hand, and what the demotion looked like at 390._

## QA Learnings

_Not Done until filled. Required: which of the two widths the implementation reached for first, and whether any call site still treats 390 and 479 as the same number._
