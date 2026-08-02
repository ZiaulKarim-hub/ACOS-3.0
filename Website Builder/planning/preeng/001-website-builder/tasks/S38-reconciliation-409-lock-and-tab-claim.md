# S38-reconciliation-409-lock-and-tab-claim — Hash-journal reconciliation, 409 concurrency, process lock and tab claim

| Field | Value |
|---|---|
| Epic / Story | E16 / ST-12 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 2 / — |
| Depends on | S31-typed-ops-autosave-history-undo · S37-eight-control-security-posture |
| Requirements | FR-222, FR-225, FR-226 |
| Acceptance criteria | A82 · §12.17-A95 · SL-S38-1 · SL-S38-2 |
| CQ / evidence | CQ7 |
| Note | **Reconciliation is rank 1, the ownership guard is rank 4.** The guard (S39) is a heuristic defeatable by indirection; this slice is the mechanism that actually holds, and the ranking must survive into the skill's own documentation |

## PM — slice definition

**Objective.** Make silent work loss impossible in either direction, with reconciliation as the authoritative mechanism rather than the guard hook.

**In scope.** `.wb/doc-hashes.json` as `{path, sha256, mtimeMs, seq}[]` over the doc-owned set (`pages/*.doc.json`, `content.json`, `site.json`, `assets/manifest.json`, `provenance.json`); a watch on that set; any divergence from the journal **without a server-issued write** raises a conflict **before the next save is accepted**, and the divergent version is copied to `.wb/conflicts/<iso>/` **first**; the stated fallback — if the watch API is unreliable, a hash re-check immediately before every save and on window focus, **announced in the status bar**; optimistic concurrency — every save carries the etag/hash it loaded and a stale write is rejected **409** with reload / force / open-the-conflict-copy; `.wb/editor.lock` as `{pid, startedAt, heartbeatAt}`; a **tab claim over SSE** as `{tabId, claimedAt}` with the second tab read-only.

**Out of scope.** The ownership guard hook, `wb op` and the inbox (S39). `chmod 0444` while the lock is held — it is a speed bump only, the same uid can chmod back, and `§12.7-O34` records no in-scope mitigation; this slice must not present it as protection. Durability by commit-per-save — durability here is **the op log plus atomic writes plus hashing** (NA-B07).

**Allowed files / contexts.**
- `scripts/lib/reconcile.ts`, `scripts/lib/hash-journal.ts`, `scripts/lib/editor-lock.ts`, `scripts/lib/tab-claim.ts`, the save path and SSE handler from S31/S29.
- Runtime-only: `.wb/doc-hashes.json`, `.wb/editor.lock`, `.wb/conflicts/**`.

**Steps.**
1. Write the journal entry as part of every server-issued write, inside the same write-temp → `fs.rename` sequence, so a write and its hash can never disagree.
2. On watch event, on window focus and immediately before every save, recompute the on-disk sha256 and compare to the journal.
3. On divergence: copy the divergent file to `.wb/conflicts/<iso>/` **before anything else**, then refuse the save and surface both versions with reload / keep-mine / merge-by-hand.
4. Reject a stale save with **409** and a body naming the loaded hash and the current hash.
5. Implement the lock with a heartbeat; a dead pid's lock is reclaimable, a live one is not.
6. Implement the tab claim over the existing SSE stream; the second tab renders read-only and says why.
7. Make the degraded mode loud: if the watch is unavailable, the status bar states that hash re-check is in force.

**Assumption (recorded).** The heartbeat interval and the staleness window that makes a lock reclaimable are not fixed by the record; this slice reads both from the project config and records the values used `[I]`.

**Definition of Done.**
- Artifacts: journal writer, reconciler, conflict-copy path, 409 save path, lock, tab claim.
- Validation: a heredoc write to a doc-owned file while the lock is held is detected before the next save, the divergent version exists under `.wb/conflicts/<iso>/`, and **both** versions are byte-recoverable; a stale save returns 409; a second tab is read-only.
- `slice.yaml` mapping — `acceptance_criteria: [A82, "§12.17-A95", SL-S38-1, SL-S38-2]`, `verification_method: exit-code` (§12.17-A95: `hash-compare`; SL-S38-1/2: `manual-observation`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-222, FR-225, FR-226 → file:line; (3) structural quality — one hashing implementation shared by journal, save and reconciler; (4) functional testing — the heredoc scenario, the `sed -i` scenario, the second-editor scenario, the stale-save scenario, the two-tab scenario, each with recorded hashes; (5) security/compliance — state the rank order explicitly and that the guard hook cannot catch what this catches; (6) operational — how a user recovers from a conflict directory, and what happens if the watch dies mid-session; (7) self-assessment.

## QA — zero-trust verification

- **Perform the out-of-band write yourself** with a Bash heredoc while the editor holds the lock, then attempt a save and require the conflict.
- **Recompute both sha256 values yourself** (`shasum -a 256`) — the journal value and the on-disk value. A logged divergence you cannot reproduce is a rejection.
- **Confirm the conflict copy was written before the refusal**, by timestamp order, not by prose.
- **Disable the watch** and confirm the fallback engages **and the status bar says so**; a silently degraded detector fails the slice.
- **Open a second tab yourself** and attempt an edit.
- **Reject** if any evidence describes `chmod 0444` as a protection rather than a speed bump.

## Dev Learnings

_Not Done until filled. Required: which out-of-band write path was hardest to detect, and whether the watch API held on this machine or the fallback carried the slice._

## QA Learnings

_Not Done until filled. Required: the scenario where reconciliation almost let a divergence through, and what made it visible._
