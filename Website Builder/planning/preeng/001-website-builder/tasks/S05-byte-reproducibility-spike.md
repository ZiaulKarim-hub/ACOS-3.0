# S05-byte-reproducibility-spike — Two-build byte-reproducibility spike

| Field | Value |
|---|---|
| Epic / Story | E0 / ST-01 |
| Type · MoSCoW · Size | diagnostic · MUST · S `[I]` |
| Phase / Demo | Phase 0 / — |
| Depends on | S03-o8-substrate-spike |
| Requirements | FR-006 |
| Acceptance criteria | SL-S05-1 · SL-S05-2 |
| CQ / evidence | CQ9 · `§12.5-O33` — **no consulted source establishes bundler byte reproducibility across two installs** |
| Blocking | Success criterion S4 and purity gate 2 are written against this outcome |

## PM — slice definition

**Objective.** Establish whether two clean builds of the same source produce byte-identical trees on the selected toolchain — and if not, specify the fallback honestly rather than claiming a guarantee the toolchain cannot give.

**In scope.** Two builds from a clean worktree with a pinned environment (`SOURCE_DATE_EPOCH`, `TZ=UTC`, `LC_ALL=C`, pinned runtime version); a sorted-path + SHA-256 manifest comparison; if it fails, an **enumerated, individually justified** exception set and an explicit statement that the export proof is weakened and needs sign-off.

**Out of scope.** Implementing purity gate 2 (S67). Modifying the live dependency tree. Accepting the fallback on the Dev's own authority — the fallback requires the user's signature and this slice records that it is owed.

**Allowed files / contexts.**
- `spikes/repro/**` (new, disposable), `docs/adr/ADR-05-byte-reproducibility.md` (new)
- **The live manifest, lockfile and dependency tree must be byte-unchanged when this slice ends** — verify by hashing them before and after.

**Steps.**
1. Hash the live manifest, lockfile and dependency directory listing. Record.
2. Build twice in isolated clean worktrees with the pinned environment.
3. Produce a sorted-path + SHA-256 manifest per build; diff them.
4. If identical: record the exact pinning that achieved it — the pinning **is** the result.
5. If not: enumerate every differing file, give each a written justification, and state plainly that normalised comparison weakens the proof and requires sign-off.
6. Re-hash the live manifest, lockfile and dependency listing; assert unchanged.

**Definition of Done.**
- Artifacts: both manifests, the diff, ADR-05, the before/after hashes of the live dependency surface.
- Validation: the comparison is a hash diff, not an inspection.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S05-1, SL-S05-2]`, `verification_method: hash-compare`.

## Dev — execution contract

Never modify the live dependency tree; a design server running in another terminal must be unaffected. Evidence bundle: (1) summary — identical or not, in one sentence; (2) traceability FR-006 → manifests; (3) structural quality — the two builds differ only in build directory; (4) functional testing — the raw manifests and the diff; (5) security/compliance — no credential used, no network fetch beyond the pinned install; (6) operational — the exact command sequence to repeat; (7) self-assessment — including that a pass today does not guarantee a pass after any dependency upgrade.

## QA — zero-trust verification

- **Recompute** at least twenty file hashes from both manifests yourself and confirm they match the recorded values.
- **Re-run** the third build yourself if feasible; two builds prove less than three.
- **Reject** if the live lockfile or manifest hash changed.
- **Reject** if a failure was reported as a pass by loosening the comparison (e.g. comparing only file names).
- **Reject** if a fallback exception set exists without per-file justifications, or without the explicit sign-off-owed statement.

## Dev Learnings

_Not Done until filled. Required: which environment variables mattered, and which file classes differed if any (sourcemaps, hashed asset names, ordering)._

## QA Learnings

_Not Done until filled. Required: whether an independent third build agreed, and what would make a spurious failure likely later — because a gate that fails spuriously gets disabled by whoever is trying to ship._
