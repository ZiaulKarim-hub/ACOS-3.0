# S34-reorder-duplicate-paste-freeze — Section reorder, duplicate, copy/paste with overrides, and element freeze

| Field | Value |
|---|---|
| Epic / Story | E8 / ST-10 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 2 / — |
| Depends on | S31-typed-ops-autosave-history-undo |
| Requirements | FR-089, FR-090 |
| Acceptance criteria | SL-S34-1 · SL-S34-2 · SL-S34-3 |
| CQ / evidence | — (no CQ binds this slice) |
| Note | **`§17-O33`** — "Lock" is the terminal publish verb. The element-level protection verb is **Freeze**, and overloading the word is a support-cost defect, not a copy preference |

## PM — slice definition

**Objective.** Give the structural edits that precede the canvas, without losing breakpoint overrides or overloading the word lock.

**In scope.** `reorder-siblings` over the page's reorder-only vertical section list; `duplicate-node`; cut / copy / paste and **paste-to-replace** via `paste-fragment`, round-tripping a document fragment **including every breakpoint override** (`base`, `md`, `sm`, flow and free entries alike); `freeze-node` / `unfreeze-node` writing `node.locked`; a frozen node **rejecting move, resize, swap, reorder and delete with a stated reason**; a grep over all user-visible strings proving the verb is **Freeze** and that "Lock" never names element protection.

**Out of scope.** Canvas drag placement and the drop algorithm (S43). Cross-direction transplants and coherence debt (v2). Variant swapping and slot contracts (S51) — freeze must reject a swap here, but the swap itself is S51's. Tree drag affordances beyond the reorder op's UI hook.

**Allowed files / contexts.**
- `scripts/lib/ops/structure-ops.ts`, `scripts/lib/fragment.ts`, `app/editor/clipboard.ts`, `app/editor/freeze.ts`, the user-visible string table.

**Steps.**
1. Implement `reorder-siblings` as an order rewrite over `sectionOrder` / `slots`, never a tree splice that regenerates ids.
2. Implement fragment extraction: the subtree with all `layout` keys, `props`, `text` refs and node ids re-minted **only** where a duplicate would collide, recorded in the op.
3. Implement `duplicate-node` and `paste-fragment` on the same extractor, so there is one round-trip path and one place for an override to be dropped.
4. Prove the round trip by a **document diff of the pasted subtree** against the source subtree, normalised for ids and anchor position.
5. Implement freeze: every mutating op consults `node.locked` first and returns a refusal naming the node and the verb.
6. Run the string grep; the only permitted "Lock" strings are the terminal publish verb's own.

**Definition of Done.**
- Artifacts: the structure ops, the fragment extractor, the clipboard binding, the freeze check, the string-grep transcript.
- Validation: a fragment with `md` and `sm` overrides and a free-mode entry pastes byte-identical modulo ids; a frozen node refuses all five verbs with a reason; the user-visible string grep shows zero element-protection uses of "Lock"; each of these is one undo entry.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S34-1, SL-S34-2, SL-S34-3]`, `verification_method: hash-compare` (SL-S34-2: `grep-assert`; SL-S34-3: `exit-code`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-089, FR-090 → file:line; (3) structural quality — one extractor shared by duplicate and paste; a second copy of the traversal is a defect; (4) functional testing — the override round-trip diff, the five freeze refusals, and a paste-to-replace into a node with a different override set; (5) security/compliance — a pasted fragment is validated against the library exactly like a placed node; (6) operational — what the user sees when they try to move a frozen node, and how they unfreeze; (7) self-assessment.

## QA — zero-trust verification

- **Build your own fragment** carrying `md` and `sm` overrides plus a free-mode entry with a `flowFallback`, paste it, and **diff the subtrees yourself**; a dropped `sm` key is the exact failure this slice exists to prevent.
- **Hash the source subtree before and after the copy** and confirm the source was not mutated.
- **Try all five verbs against a frozen node** and record each refusal message.
- **Run your own grep over user-visible strings** for "Lock", "Locked" and "Unlock"; any hit describing element protection is a rejection.
- **Reorder and then re-render**, confirming node ids are unchanged — a reorder that re-mints ids breaks determinism downstream.
- **Reject** if duplicate and paste use two different traversals.

## Dev Learnings

_Not Done until filled. Required: which override key was hardest to carry through the fragment path, and how id re-minting interacted with the recovery bin and the op log._

## QA Learnings

_Not Done until filled. Required: where the word "Lock" tried to come back, and which freeze refusal message was least intelligible._
