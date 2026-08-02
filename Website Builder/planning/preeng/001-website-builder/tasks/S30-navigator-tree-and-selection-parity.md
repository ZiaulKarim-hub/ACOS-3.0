# S30-navigator-tree-and-selection-parity — Navigator/layers tree and three-way selection parity

| Field | Value |
|---|---|
| Epic / Story | E8 / ST-09 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 2 / — |
| Depends on | S29-editor-shell-and-overlay |
| Requirements | FR-081 |
| Acceptance criteria | A25 · SL-S30-1 |
| CQ / evidence | CQ3 |
| Note | **R24–R35 cluster, "no layers panel would be fatal."** The Navigator is **non-optional in v1** because canvas clicking *provably* cannot reach zero-height wrappers, fully covered elements, `pointer-events: none` decoration or empty slots (§10.2, §20.2 row 10) |

## PM — slice definition

**Objective.** Guarantee everything is reachable, including what canvas clicking provably cannot reach.

**In scope.** The layers tree rendered **from the document**, never from the DOM; three-way selection parity — canvas click, breadcrumb and tree all set and reflect the same selection, in both directions; hide/show per layer as an editor-only view state; section boundary markers; the reachability fixture carrying a zero-height wrapper, a fully covered element, a `pointer-events: none` decoration and an empty slot, with each case recorded as selected from the tree.

**Out of scope.** Drag-reorder inside the tree (S34). Multi-select and marquee (S49). The page list and page-scoped ops (S36). Any tree node that exists only in the DOM — if it is not in the document, it is not in the tree.

**Allowed files / contexts.**
- `app/editor/navigator/**`, `app/editor/selection.ts`, `app/editor/breadcrumb.ts`, `.wb/session-ui.json` (`selection`, `openPanels` — ephemeral state only).

**Steps.**
1. Build the tree by walking `doc.root` and `sectionOrder`; label each row by component and variant, not by tag name.
2. Make selection one piece of state with three writers and three readers; a selection set anywhere is visible everywhere in the same frame.
3. Reflect the selection into the out-of-iframe overlay only — the tree never injects into the page.
4. Implement hide/show as an editor view state that **never** reaches the document or the rendered output.
5. Build the four-case reachability fixture and record a selection from the tree for each.
6. Record the canvas-click result for the same four cases — the point of the slice is the gap between the two columns.

**Definition of Done.**
- Artifacts: the tree, the selection module, the breadcrumb binding, the four-case fixture, the two-column reachability record.
- Validation: every fixture case selectable from the tree; selection parity demonstrated in both directions for each of the three routes; hide/show leaves the document and the rendered output byte-identical.
- `slice.yaml` mapping — `acceptance_criteria: [A25, SL-S30-1]`, `verification_method: manual-observation` (SL-S30-1 recorded case by case, with the document diff for hide/show by `hash-compare`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-081 → file:line; (3) structural quality — the tree is a pure function of the document; state where that purity is enforced; (4) functional testing — the four-case table with tree result and canvas result side by side, plus the parity matrix (3 routes × set/reflect); (5) security/compliance — n/a, note it; (6) operational — what the tree shows when a node carries a `variantMigrated` flag or parked `orphaned` content, since those are the states a user must find; (7) self-assessment.

## QA — zero-trust verification

- **Build your own fixture** — a zero-height wrapper, a covered element, a `pointer-events: none` decoration and an empty slot — and select each from the tree yourself.
- **Try each case by canvas click** and record the failures; a slice that claims parity without showing what clicking cannot reach has not made the argument.
- **Test parity in both directions** for all three routes; selecting in the tree must move the breadcrumb, and selecting via breadcrumb must scroll and highlight in the tree.
- **Toggle hide/show, then hash the document and the rendered output**; any change is a rejection.
- **Confirm the tree is built from the document** — grep for any DOM query used to construct a row.
- **Reject** if a node with parked orphan content or a migration flag is invisible in the tree.

## Dev Learnings

_Not Done until filled. Required: which of the four unreachable classes was hardest to represent as a tree row, and whether the tree stayed a pure function of the document under real editing._

## QA Learnings

_Not Done until filled. Required: any element class found in practice that neither the canvas nor the tree could reach._
