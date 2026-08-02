# S51-slot-contracts-and-swap-safety — Typed slot contracts, superset-only swaps, content orphanage and lock-blocking placeholders

| Field | Value |
|---|---|
| Epic / Story | E10 / ST-17 |
| Type · MoSCoW · Size | build · MUST · L `[I]` |
| Phase / Demo | Phase 4 / — |
| Depends on | S31-typed-ops-autosave-history-undo · S25-pure-renderer-and-resolution-policy |
| Requirements | FR-138, FR-139, FR-140, FR-141, FR-142 |
| Acceptance criteria | A29 · A30 · A38 · SL-S51-1 · SL-S51-2 |
| CQ / evidence | CQ14 · EL-037 |
| Note | **R11** — component swaps silently destroying hand-written copy is the named risk this slice exists to make structurally impossible |

## PM — slice definition

**Objective.** Make a variant swap incapable of destroying hand-written copy and incapable of shipping an unfilled placeholder.

**In scope.** The `SlotContract` shape `{name, type, cardinality, required}`; the bar offering **only** superset-or-exact contract matches; the pre-swap sentence stating the delta in words ("this variant adds N slots" / "this variant has no place for: [x]"); the `swap-variant` typed op rejecting `422 contract not a superset`; **content orphanage** — anything the target cannot hold moves to a visible parked panel, is never deleted, and auto-restores when a later swap re-introduces the slot; newly created empty slots rendering as visibly flagged placeholders that **BLOCK LOCK** until filled or deleted; in-place node replacement so tab order before and after is identical for equivalent content; the coherence-debt ledger file existing with no cross-direction producer in v1.

**Out of scope.** Cross-direction swaps (FR-142 is WON'T for v1 — only one direction is generated in full). Variant generation itself (S53). The lock-time gate that reads the placeholder flag (S68) — this slice sets the flag and proves it is readable.

**Allowed files / contexts.**
- `scripts/lib/slots.ts`, `scripts/lib/swap.ts`, the `swap-variant` op handler, `04-site/pages/<id>.doc.json` + `04-site/content.json` (through typed ops only), `04-site/coherence-ledger.json` (create).
- TypeScript on Bun. **No `.py` file anywhere in the skill tree.**

**Steps.**
1. Define `SlotContract` and a pure `isSupersetOrExact(source, target)` predicate; unit-test the cardinality and `required` edges.
2. Filter the component bar's offer list through that predicate; a non-matching variant is not merely disabled, it is not offered.
3. Render the delta sentence from the computed diff — never from a hand-written string per variant.
4. Implement orphanage: content the target cannot hold is moved into the parked panel with its `contentKey`, and re-homed automatically when a later swap re-introduces that slot name.
5. Flag every newly created empty required slot as a placeholder in the doc, so LOCK can refuse on the node list.
6. Replace the node **in place** in the tree; capture tab order before and after and assert equality for equivalent content.
7. Create the coherence-debt ledger with the v1 producer set (off-system values only) and assert by grep that no cross-direction transplant writer exists.

**Definition of Done.**
- Artifacts: `slots.ts`, `swap.ts`, the op-handler rejection path, the parked panel, the placeholder flag, `coherence-ledger.json`.
- Validation: a swap dropping a slot parks the copy and deletes nothing; the reverse swap restores it; a placeholder-bearing doc is refused by the LOCK precondition check; the tab-order sequence is byte-identical across the swap.
- Demo-able increment: swap a live section in the editor, watch the copy park and return.
- `slice.yaml` mapping — `acceptance_criteria: [A29, A30, A38, SL-S51-1, SL-S51-2]`, `verification_method: exit-code` (A38: `manual-observation`, SL-S51-1: `manual-observation`, SL-S51-2: `grep-assert`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-138…FR-142 → file:line; (3) structural quality — the superset predicate and the orphanage mapper are pure and unit-testable with no DOM; (4) functional testing — four fixtures: drop-a-slot swap, re-introduce swap, required-slot-created swap, equal-contract swap; (5) security/compliance — the swap runs as one typed op, never a raw patch, and never accepts a file path; (6) operational — where parked content lives on disk and how it survives a server restart; (7) self-assessment naming what orphanage does **not** cover.

## QA — zero-trust verification

- **Perform your own swap** through the op endpoint and then `diff` the content file: any deleted `contentKey` is an immediate rejection.
- **Recompute the tab order yourself** from the rendered document before and after; do not trust a logged "identical".
- **Construct a variant whose contract is a strict subset** and confirm it is absent from the offer list, not merely greyed.
- **Attempt LOCK with an unfilled placeholder** and require refusal with the node list, not a count.
- **Grep for a cross-direction transplant writer**; one hit is a rejection (v1 has none by construction).
- **Verify scope** against the allowed-files list; any edit outside it is a rejection regardless of quality.

## Dev Learnings

_Not Done until filled. Required: which slot-shape difference the superset predicate got wrong first, and whether auto-restore ever re-homed content into the wrong slot._

## QA Learnings

_Not Done until filled. Required: the cheapest swap sequence that produced silent content loss before the fix, and whether the delta sentence was actually intelligible._
