# S31-typed-ops-autosave-history-undo — Typed-op engine, autosave, op log and transactional undo

| Field | Value |
|---|---|
| Epic / Story | E8 / ST-10 |
| Type · MoSCoW · Size | build · MUST · L `[I]` |
| Phase / Demo | Phase 2 / — |
| Depends on | S29-editor-shell-and-overlay |
| Requirements | FR-085, FR-086, FR-087 |
| Acceptance criteria | A31 · A32 · SL-S31-1 · SL-S31-2 · SL-S31-3 |
| CQ / evidence | CQ7 · CQ15 |
| Risk | **R22** — a naive per-mutation stack leaves a broken hybrid after one Cmd+Z. Transactional grouping is **mandatory and tested**, not a refinement |

## PM — slice definition

**Objective.** Make every edit a validated typed op applied atomically by the single writer, with one command stack over the document.

**In scope.** The typed-op catalogue validated **against its op schema and against the component library**; the browser's pending-op queue flushed to `POST /ops` debounced ~300 ms; the server deriving the RFC 6902 patch, applying it atomically (**write-temp → `fs.rename`**) and appending `{seq, ts, actor, op, target, patch, inverse, label, txn}` to `history.jsonl`; the write allowlist enforced by path shape with `realpath` then a `startsWith(sessionRoot)` assertion **re-checked after resolution**; **400** on a raw JSON Patch body, on a file path in a request body, on any path outside the allowlist and on any pointer starting `/systemLock`, each rejection logged; **422** on an op that fails library validation; undo/redo as a **single command stack over the doc** covering drags, inspector edits and text edits alike; a continuous drag coalescing into exactly one entry; `txn` grouping so a component swap or a section regeneration is **ONE** undo step.

**Out of scope.** Hash-journal reconciliation, the `409` stale-write rejection, `editor.lock` and the tab claim (S38) — the `etag` field is carried and its presence validated here, the conflict protocol is S38's. The `wb op` agent path and the ownership guard (S39). The recovery bin (S35).

**Allowed files / contexts.**
- `scripts/lib/ops/**`, `scripts/lib/op-schema.ts`, `scripts/lib/apply.ts`, `scripts/lib/history.ts`, `scripts/lib/allowlist.ts`, `app/editor/op-queue.ts`, `app/editor/history-ui.ts`.

**Steps.**
1. Declare each op's payload schema; validate the payload, then validate the resulting reference set against the library.
2. Derive the patch **server-side**; the browser never sends a patch and never sends a path.
3. Apply atomically: write to a temp file in the same directory, `fs.rename` over the target, then append to `history.jsonl` — the log entry is written only after the rename succeeds.
4. Compute and store the `inverse` at apply time; undo replays the inverse through the same path, never a special bypass.
5. Coalesce a continuous drag by pointer session into one entry; group swap and section-regeneration mutations under one `txn`.
6. Add the rejection tests: raw patch body, file path in body, `/systemLock` pointer, out-of-allowlist path, symlink and `..` escape.

**Definition of Done.**
- Artifacts: op schemas, the apply path, `history.jsonl` writer, the allowlist module, the queue, the undo stack.
- Validation: a swap and a section regeneration each undo in one step; a scripted continuous drag produces exactly one entry; every rejection case returns 400 and appears in the log; a killed process mid-write leaves no partial file.
- `slice.yaml` mapping — `acceptance_criteria: [A31, A32, SL-S31-1, SL-S31-2, SL-S31-3]`, `verification_method: exit-code`.

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-085, FR-086, FR-087 → file:line per op; (3) structural quality — one apply path; a grep proving no module writes a doc-owned file directly; (4) functional testing — the undo matrix (drag, inspector edit, text edit, swap, regeneration), the six rejection cases, and an interrupted-write test; (5) security/compliance — the allowlist table with the post-resolution re-check named explicitly; (6) operational — how to read `history.jsonl` when a user reports lost work; (7) self-assessment.

## QA — zero-trust verification

- **Post a raw JSON Patch yourself**, then a body containing a file path, then a `/systemLock` pointer, then a `..` path and a symlink; require 400 on each **and** find each in the log.
- **Drag continuously and count the entries yourself** in `history.jsonl`; two entries for one drag is a rejection.
- **Undo a component swap and inspect the document** — a broken hybrid after one undo is the exact failure this slice exists to prevent.
- **Recompute an inverse yourself** for one op and apply it manually; if the result is not the prior document hash, reject.
- **Kill the server mid-write** and confirm the target file is either the old version or the new one, never a truncated third thing.
- **Reject** if any op is validated against its schema but not against the component library.

## Dev Learnings

_Not Done until filled. Required: which op needed a hand-written inverse rather than a derived one, and where drag coalescing nearly split an entry._

## QA Learnings

_Not Done until filled. Required: the rejection case that was easiest to slip past validation, and whether the log alone was sufficient to reconstruct a lost edit._
