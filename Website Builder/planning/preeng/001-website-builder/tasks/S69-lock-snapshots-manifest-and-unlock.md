# S69-lock-snapshots-manifest-and-unlock — Snapshots, lock manifest, git tag, non-mutating LOCK and the unlock path

| Field | Value |
|---|---|
| Epic / Story | E14 / ST-23 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 5 / — |
| Depends on | S67-eight-purity-gates |
| Requirements | FR-205, FR-207, FR-208, FR-209 |
| Acceptance criteria | A54 · A55 · A56 (amended) · A58 · A59 · SL-S69-1 · SL-S69-2 |
| CQ / evidence | CQ9 |
| Note | **The one uncovered case, named explicitly: hand-edits inside the exported tree.** The per-file SHA-256 manifest is what makes them detectable rather than silently overwritten |

## PM — slice definition

**Objective.** Make LOCK **reversible** and hand-edits inside the exported tree **detectable** rather than silently overwritten.

**In scope.** LOCK writes **only** `dist/published/` and `.wb/locks/<iso>/`, then tags `wb-lock/<n>`; `pages/*.doc.json` mtimes unchanged (A54); **UNLOCK is restarting the design server** (A55); export is **write-to-new-dir-then-swap** with **no `rm -rf` anywhere in the export path** (A59); `lock-manifest.json` = `{lockIndex, at, docSha256PerPage, siteSha256, systemLockSha256, gateReportRef, screenshotRefs, distFileHashes, gitTag}`; the snapshot set — every document, `site.json`, `content.json`, `system.lock.json`, `assets/manifest.json`, the dist hash manifest, the scrub output, `lock-manifest.json` and `gate-report.json`; the per-file SHA-256 diff run at **both** unlock and the next LOCK as a **blocking prompt** (A58); restore semantics that bring documents **and** the system lock back **together** (A56 amended to include `system.lock.json` and `content.json`), stopping with the migrate command when library files no longer hash-match; a best-effort, **explicitly fallible** `extract-override --from-dist` re-homing path **that refuses rather than guesses**.

**Out of scope.** Publishing (S70). The evidence bundle (S71). Semantic cross-direction variant matching on restore — `wb migrate` uses the **canonical fallback only, always reviewed** (`§12.16-O35`, NA-B04; "no known mitigation removes the risk"). Guessing where a hand-edit belongs.

**Allowed files / contexts.**
- `scripts/lib/snapshot.ts`, `scripts/lib/lock-manifest.ts`, `scripts/lib/unlock.ts`, `scripts/extract-override.ts`, `.wb/locks/<iso>/` (write), `07-lock/lock-manifest.json` (write).
- **`dist/` is deliberately excluded from the snapshot — it is reproducible**, and including it would make `.wb/locks` grow without bound. `.wb/locks/**` is **committed**; `.wb/tmp/**` and `.wb/conflicts/**` are git-ignored.

**Steps.**
1. Record document mtimes before LOCK; assert them unchanged after (A54). LOCK is non-mutating on the doc-owned set.
2. Write the snapshot set into `.wb/locks/<iso>/` — **doc + system lock + content + manifests only, never `dist/`**.
3. Compute `distFileHashes` per file into `lock-manifest.json`; this map is the hand-edit detector.
4. Tag `wb-lock/<n>` in the site's **own** git repo (NA-B11 — the site tree is a separate repository, so tags do not collide with the framework's).
5. Implement export as write-to-new-dir-then-swap; assert no `rm -rf` exists anywhere in the export path by grep, in code review **and** in `selftest.ts`.
6. Implement unlock = restart the design server; on unlock, diff `dist/published/**` against `distFileHashes` and raise a **blocking prompt** on any difference.
7. Implement restore: documents + `system.lock.json` + `content.json` together; if library files no longer hash-match the restored system lock, **stop and print the migrate command** rather than opening a half-resolved project.
8. Implement `extract-override --from-dist` as explicitly fallible: it re-homes what it can prove and **refuses** the rest with a named reason.

**Definition of Done.**
- Artifacts: snapshot writer, `lock-manifest.json`, the tag, the unlock diff prompt, the restore path, `extract-override --from-dist`.
- Validation: document mtimes unchanged across a LOCK; the snapshot contains all nine named members and **no `dist/`**; a hand-edited file in the exported tree raises the blocking prompt at unlock **and** at the next LOCK; a restore against a mismatched library stops with the migrate command; zero `rm -rf` in the export path.
- `slice.yaml` mapping — `acceptance_criteria: [A54, A55, A56, A58, A59, SL-S69-1, SL-S69-2]`, `verification_method: exit-code` (A54: `hash-compare`; A55/A58: `manual-observation`; A59: `grep-assert`).

## Dev — execution contract

Never `rm -rf` in the export path — the permission layer scores destructive commands +5 and, more importantly, a bad glob in an export path destroys the user's site. Evidence bundle: (1) summary; (2) traceability FR-205, FR-207, FR-208, FR-209 → file:line; (3) structural quality — snapshot contents are a declared list, not a directory walk that could silently start including `dist/`; (4) functional testing — the hand-edit detection transcript at both trigger points and the mismatched-library restore transcript; (5) security/compliance — the bearer token file is never snapshotted; (6) operational — how to restore an older lock and what it refuses to do; (7) self-assessment.

## QA — zero-trust verification

- **Recompute the document hashes** in `lock-manifest.json` yourself and compare; a manifest you cannot reproduce is a rejection.
- **Check the mtimes yourself** before and after a LOCK you run.
- **Hand-edit a file in the exported tree yourself**, then unlock, and confirm you are blocked — a warning that can be scrolled past is a rejection.
- **List the snapshot directory yourself**: nine members present, `dist/` absent. `dist/` present is a rejection even though it "feels safer".
- **Run your own** `grep -rn 'rm -rf' scripts/` over the export path and require zero.
- **Break the library hash deliberately** and confirm the restore stops and prints the migrate command rather than opening a half-resolved project.
- **Reject** if `extract-override --from-dist` ever guesses a home rather than refusing.

## Dev Learnings

_Not Done until filled. Required: what the hand-edit detector caught in practice, and whether excluding `dist/` from the snapshot ever felt unsafe._

## QA Learnings

_Not Done until filled. Required: whether the restore stop-and-migrate path is reachable without reading the code, and how a user would recover from a refused re-home._
