# S47-reading-order-and-stack-preview — Reading-order invariant, focusable-node hard block and numbered mobile stack preview

| Field | Value |
|---|---|
| Epic / Story | E9 / ST-15 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 3 / — |
| Depends on | S46-override-cascade-and-precommit-chip |
| Requirements | FR-114, FR-115 |
| Acceptance criteria | SL-S47-1 · SL-S47-2 · SL-S47-3 |
| CQ / evidence | CQ11 · CQ2 |
| Note | **NA-18** — §11.3.1 supplies a **normative** reading-order invariant, a **hard block** on `order` for focusable nodes and a numbered mobile stack preview, none of which was in the carried requirements. This slice owns all three |

## PM — slice definition

**Objective.** Guarantee document order is reading order, and make any mobile reordering visible before it is committed.

**In scope.** The invariant: **DOM order *is* the reading order**, and visual order is achieved **only by grid placement** — no editor path may reorder the document tree to achieve a visual effect. The single sanctioned exception, a per-breakpoint `order: {bp, value}` override, which (a) raises a **persistent** *"Reading order will differ from what's shown here"* chip, (b) is **hard-blocked on any focusable node** — `set-order-override` returns **403** with an explanation naming WCAG 2.4.3, and (c) **warns** on a non-focusable node under WCAG 1.3.2 while still raising the persistent chip. Before **any** commit that changes mobile stacking, a **numbered list preview** of the resulting top-to-bottom mobile sequence, rendered from the resolved `sm` layout. The focusable set is computed from the rendered subtree — tabbable elements and anything with a non-negative `tabindex` — not from a component-name list.

**Out of scope.** Legitimate document reordering: `reorder-siblings` (section reorder, S34) and the *order* verb's sibling move (S45) change reading order **and** visual order together, which is the intended behaviour and is not what SL-S47-1 forbids. The lock-time re-check of the same invariant (S68) — this slice supplies the checker and its fixtures. Free-position stacking at `sm` (S48).

**Allowed files / contexts.**
- `scripts/lib/canvas/reading-order.ts`, `scripts/lib/canvas/order-override.ts`, `scripts/lib/canvas/stack-preview.ts`, the `set-order-override` op validator (S31), the cascade resolver from S46 (read-only).

**Steps.**
1. Implement a reading-order walk that compares document order against resolved visual order per breakpoint and reports every divergence with its node id.
2. Add the invariant test: drive every editor mutation path and assert that none rewrites sibling order in the tree except the two sanctioned reordering ops, which change reading order deliberately.
3. Implement the focusable check at op time; return **403** on a focusable target with a message that names the criterion and says what the user should do instead (move it on the grid).
4. On a non-focusable target, apply the override, warn, and raise the persistent chip; the chip survives reload because it is derived from the document, not from session state.
5. Implement the numbered stack preview: resolve the `sm` layout, order the nodes top-to-bottom, render a numbered list, and require acknowledgement **before** the commit is dispatched.
6. Fire the preview on **any** commit that changes mobile stacking, including a drag or span change whose `sm` consequence reorders the stack — not only on an explicit `order` edit.

**Definition of Done.**
- Artifacts: reading-order walker, order-override validator, stack-preview component, the no-tree-reorder test, focusable and non-focusable fixtures.
- Validation: `set-order-override` on a focusable node returns 403; on a non-focusable node it warns and the chip persists across reload; a stacking-changing commit renders the numbered preview first; the invariant test passes over every mutation path.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S47-1, SL-S47-2, SL-S47-3]`, `verification_method: exit-code` (SL-S47-3: `manual-observation`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-114, FR-115 → file:line; (3) structural quality — one focusable-set computation shared by the op validator and the live check; (4) functional testing — the 403 transcript, the warn-plus-chip case, the preview screenshot, the mutation-path sweep; (5) security/compliance — state the accessibility claim ceiling: automated checks catch a minority of real issues, so no conformance is claimed anywhere in the UI copy; (6) operational — what the preview shows for a page with a single section, and how the chip is cleared; (7) self-assessment.

## QA — zero-trust verification

- **Compute the focusable set yourself** from the rendered subtree, then POST `set-order-override` against **each** member and require 403 for every one. A component-name allowlist standing in for a real focusability test is a rejection.
- **Attempt a visual reorder by tree mutation yourself** through every editor path you can reach; one path that reorders siblings to fake placement is a rejection.
- **Confirm the numbered preview renders before dispatch**, by cancelling at the preview and verifying the document is unchanged (recompute its sha256).
- **Reload the page** and confirm the persistent chip is still present on the warned node.
- **Reject** if the preview fires only on explicit `order` edits and not on a drag whose `sm` consequence reorders the stack.

## Dev Learnings

_Not Done until filled. Required: which mutation path came closest to reordering the tree for a visual effect, and how focusability was determined for custom components._

## QA Learnings

_Not Done until filled. Required: which focusable node the hard block would have missed, and whether the stack preview matched the rendered mobile order exactly._
