# S35-snapshots-variations-recovery-bin — Named snapshots, save-as-variation and the recovery bin

| Field | Value |
|---|---|
| Epic / Story | E8 / ST-11 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 2 / — |
| Depends on | S31-typed-ops-autosave-history-undo |
| Requirements | FR-088 |
| Acceptance criteria | SL-S35-1 · SL-S35-2 · SL-S35-3 |
| CQ / evidence | CQ15 |
| Note | **NA-B07** — durability is **the op log + atomic writes + hash reconciliation, not a commit per save**. Git commits happen at milestones and `wb autosave --git` is opt-in; nothing in this slice may make git the recovery mechanism |

## PM — slice definition

**Objective.** Make experimenting cheap and deletion non-destructive, with a recovery path independent of undo.

**In scope.** Named snapshots of the document set taken on demand; **save-as-variation** forking the document set without mutating the source; the recovery bin — a `TrashEntry {nodeSubtree, restoreAnchor: {parentId, index, sectionId}, deletedAt, deletedBy}` written on every `delete-node`, **independent of the undo stack**, retained unbounded within the project, **restore-in-place** via `restore-node`, and **stripped at LOCK**; autosave persisting **small document diffs through the server**, never a base64 blob in browser storage.

**Out of scope.** LOCK snapshots and `lock-manifest.json` (S69). `wb migrate`'s pre-migration snapshot (S59) — same shape, different owner. Conflict copies under `.wb/conflicts/` (S38). Any git operation: milestone commits are not this slice's mechanism and must not be called from it.

**Assumption.** No path is published for named snapshots; they are written under `.wb/snapshots/<name>/` and treated as **read-only to the op path** the way `.wb/locks/**` is, written only by the snapshot command `[I]`, low confidence.

**Allowed files / contexts.**
- `scripts/lib/snapshot.ts`, `scripts/lib/trash.ts`, `scripts/lib/ops/delete-restore.ts`, `.wb/snapshots/**` (command only), `04-site/**` (fork target, through the writer).

**Steps.**
1. Implement snapshot as a canonical-serialisation copy of the doc-owned set plus the source hashes; a snapshot that cannot be hash-verified is not written.
2. Implement save-as-variation as a fork of the document set into a new variation root, leaving the source untouched — proven by unchanged source hashes.
3. Write a `TrashEntry` on every delete, capturing the subtree **and** its restore anchor before the delete is applied.
4. Implement `restore-node` as a placement at the recorded anchor, applied as a typed op, so it lands in the op log like everything else and does **not** rewind unrelated edits.
5. Make the bin visible in the editor with its entries listed and restorable individually.
6. Assert autosave writes diffs through `POST /ops` only; grep browser storage code for any base64 blob.

**Definition of Done.**
- Artifacts: the snapshot command, the fork path, the trash writer, `restore-node`, the recovery-bin panel.
- Validation: a subtree deleted, then ten unrelated edits, then restored in place with those ten edits intact; the source document hashes are unchanged after a variation fork; a grep finds no base64 blob written to browser storage; the bin is empty in a LOCK-bound tree.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S35-1, SL-S35-2, SL-S35-3]`, `verification_method: exit-code` (SL-S35-2: `grep-assert`; SL-S35-3: `hash-compare`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-088 → file:line; (3) structural quality — the bin is independent of the undo stack; name the file that enforces the independence; (4) functional testing — the ten-edit restore transcript, the fork hash table, and a restore whose anchor parent was itself deleted; (5) security/compliance — snapshot paths are inside the session root and are not writable by any HTTP op; (6) operational — what a user does when they want the whole page back, and how snapshots relate to milestone commits; (7) self-assessment.

## QA — zero-trust verification

- **Delete a subtree, make ten unrelated edits yourself, then restore** — if the restore reverts any of the ten, that is the failure this slice exists to prevent.
- **Hash the source document set before and after a variation fork** and compare yourself; a logged "unchanged" is not evidence.
- **Grep the browser-side code** for `localStorage`, `sessionStorage`, `indexedDB` and `base64`, and require the autosave path to touch none of them.
- **Delete a node whose parent is later deleted**, then restore the child; record what the anchor did.
- **Confirm the bin survives a server restart** and is stripped at LOCK.
- **Reject** if any recovery path calls git.

## Dev Learnings

_Not Done until filled. Required: how the restore anchor behaved when its parent no longer existed, and the measured cost of a snapshot on the real document set._

## QA Learnings

_Not Done until filled. Required: whether the bin is discoverable without being told it exists, and any case where undo and the bin disagreed about the truth._
