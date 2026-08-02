# S59-redesign-fork-and-migration — Redesign as a fork, reviewed application, and the migration report

| Field | Value |
|---|---|
| Epic / Story | E12 / ST-19 |
| Type · MoSCoW · Size | build · MUST · L `[I]` |
| Phase / Demo | Phase 4 / — |
| Depends on | S25-pure-renderer-and-resolution-policy · S58-section-notes-scoped-regeneration |
| Requirements | FR-181, FR-182, FR-183, FR-184 |
| Acceptance criteria | §12.17-A99 · SL-S59-1 · SL-S59-2 · SL-S59-3 · SL-S59-4 |
| CQ / evidence | CQ16 · CQ15 |
| Note | **§12.16-O35 / NA-B04** — v1 adopts **canonical fallback only, always reviewed**. Semantic slot-signature matching is a v2 question and no known mitigation removes its risk |

## PM — slice definition

**Objective.** Make a new direction a reviewed operation that never silently substitutes and never silently drops a node.

**In scope.** Redesign as a **fork** via save-as-variation — it does **not** replace in place (FR-181); partial redesign re-entering Step 2 with the current direction vector marking frozen vs open slots, full redesign as a new Step-2 cycle with prior identity as a **negative constraint**; migration that **snapshots documents before touching anything**, shows a plan with counts before applying, and applies through the same typed-op path so every change is individually undoable; `04-site/migration-report.json` `{at, fromSystemLockSha, toSystemLockSha, changes[{nodeId, kind, from, to, rule, auto}], unmappable[{nodeId, reason}], counts}`; per-node `variantMigrated` flags with the editor listing them, **LOCK refused until acknowledged**, bulk-acknowledge requiring a confirmation naming the count (§12.17-A99); unmappable nodes listed explicitly for human resolution; **canonical fallback matching only** in v1.

**Out of scope.** Semantic slot-signature variant matching (v2). Cross-direction component swaps (v1 WON'T). Layout re-authoring — placement survives because it is stored as grid integers and token indices, **provided both directions share the same grid spec**, which is why `layout.breakpoints` and `type.viewport-endpoints` are invariant.

**Allowed files / contexts.**
- `scripts/lib/migrate.ts`, `scripts/lib/redesign-fork.ts`, the `acknowledge-migration` op handler, `04-site/migration-report.json` (write), `04-site/pages/<id>.doc.json` + `site.json` through typed ops only.
- TypeScript on Bun. **No `.py` file anywhere in the skill tree.**

**Steps.**
1. Implement fork-first: a redesign creates a variation and leaves the original documents byte-identical.
2. Snapshot before any mutation; refuse to proceed if the snapshot fails.
3. Compute the migration plan and present counts by kind **before** applying anything.
4. Apply through typed ops with a per-change inverse so each is individually undoable.
5. Write every changed reference — old value, new value and the rule that decided it — into the migration report; list unmappable nodes with reasons.
6. Flag affected nodes, list them in the editor, and refuse LOCK until acknowledged; bulk-acknowledge must name the count.
7. Assert by grep that no semantic slot-signature matcher exists on this path in v1.

**Definition of Done.**
- Artifacts: `migrate.ts`, the fork path, `migration-report.json`, the flag list UI, the LOCK refusal.
- Validation: original documents hash-identical after a fork; a node with no canonical target appears in `unmappable` and nowhere else; LOCK refuses with the node list until acknowledged; every change in the report names its deciding rule.
- Demo-able increment: import a second direction, review the plan, apply it, and see the flag list block LOCK until acknowledged.
- `slice.yaml` mapping — `acceptance_criteria: ["§12.17-A99", SL-S59-1, SL-S59-2, SL-S59-3, SL-S59-4]`, `verification_method: exit-code` (SL-S59-3: `grep-assert`, SL-S59-4: `hash-compare`).

## Dev — execution contract

Evidence bundle: (1) summary with the plan counts; (2) traceability FR-181…FR-184 → file:line; (3) structural quality — planning and applying are separate pure/impure halves; (4) functional testing — the fork hash check, an unmappable-node fixture, the LOCK refusal, an undo of a single migrated node; (5) security/compliance — migration writes only through the allowlisted paths and never touches `/systemLock` via a doc patch; (6) operational — how a half-applied migration is recovered from the snapshot; (7) self-assessment stating the canonical-fallback limitation plainly.

## QA — zero-trust verification

- **Hash the original documents yourself** before and after a fork; any change is a rejection of the fork claim.
- **Introduce a node the canonical rule cannot map** and require it in `unmappable`; a silently dropped node is an immediate rejection.
- **Attempt LOCK with unacknowledged flags** and require refusal listing nodes, not a count.
- **Undo one migrated node** and confirm the rest stay migrated.
- **Grep for a slot-signature matcher**; its presence in v1 is a rejection.
- **Recount the plan totals yourself** against the report's `counts` block.

## Dev Learnings

_Not Done until filled. Required: which reference kinds (variant, slot, prop, motion, token) migrated cleanly and which needed human resolution most often._

## QA Learnings

_Not Done until filled. Required: whether the pre-apply plan counts actually matched what was applied._
