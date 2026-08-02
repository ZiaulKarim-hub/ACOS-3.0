# S67-eight-purity-gates — The eight purity gates, with isolated two-build comparison

| Field | Value |
|---|---|
| Epic / Story | E14 / ST-22 |
| Type · MoSCoW · Size | build · MUST · L `[I]` |
| Phase / Demo | Phase 5 / — |
| Depends on | S66-lock-render-scrub-and-absence-mechanisms, S05-byte-reproducibility-spike, S65-capture-wrapper-and-device-pinning |
| Requirements | FR-202, FR-203 |
| Acceptance criteria | A51 · A52 · A53 · A57 · §12.17-A93 · §12.17-A94 · SL-S67-1 · SL-S67-2 |
| CQ / evidence | CQ9 · EL-022 · EL-088 · EL-085 |
| Note | **NA-03 — there are EIGHT gates, not five.** The three the carried set omits are gate 6 (unresolved references / unacknowledged migration flags), gate 7 (design-time origins) and gate 8 (`wb verify` clean with canonical re-serialisation) |

## PM — slice definition

**Objective.** **Prove** the published tree is clean rather than claim it, and run the two-build comparison **without touching the live dependency tree**.

**In scope.** All eight gates as structured verdicts `{gateId, tier, status, measured, threshold, evidenceRef}` written to `gate-report.json`, never a thrown exception on a normal fail, **INCONCLUSIVE blocking exactly like a fail**:
1. Zero editor strings — `grep -r 'data-wb-'` plus the dev-runtime patterns; any hit fails the build (A49, A50).
2. **Two-build equality** — sorted-path + SHA-256 manifest comparison from a **clean `git worktree`** with its own dependency tree, `SOURCE_DATE_EPOCH` / `TZ=UTC` / `LC_ALL=C` / pinned runtime for both builds (A51).
3. Published JS byte-size assertion against the threshold in `gate-report.json`.
4. **Screenshot diff** — editor preview at 1280 (chrome hidden) vs the built page at 1280, **zero pixels**, using S65's device-pinned wrapper (A52).
5. Interaction-manifest check — every declared motion/interaction behaviour exists in shipped code (A57).
6. **Zero unresolved references and zero unacknowledged `variantMigrated`/`orphaned` flags — failing with the node list, not a count.**
7. **Zero design-time origins** — grep `localhost`, `127.0.0.1`, `0.0.0.0`, `file://`, the session port and the session root path across `srcset`, `<meta>`, inline `style`, CSS `url()`/`@import`, JSON-LD and sourcemap comments (§12.17-A93).
8. **`wb verify` clean at lock time** — regenerate to temp, `diff -r` the text files, hash-compare binaries **separately**, re-serialise every document to canonical form requiring a zero diff (§12.17-A98, A53).

**Out of scope.** The 32-check checklist (S68). Snapshots and the tag (S69). Fixing what a gate finds — a gate reports and blocks; repair belongs to the owning slice.

**Allowed files / contexts.**
- `scripts/lib/gates/purity/*.ts`, `scripts/lib/gate-report.ts`, `.wb/tmp/gate2/` (scratch, git-ignored), `07-lock/{gate-report.json, manifest-a.json, manifest-b.json}` (write).
- **Gate 2 must never edit the live `package.json`, the live lockfile or the live dependency tree** — hash all three before and after and assert unchanged; a design server running in another terminal must be unaffected (§12.17-A94).

**Steps.**
1. Implement gates 1, 3, 5, 6, 7 as pure checks over the emitted tree; gate 6 collects and prints the **node list**.
2. Implement gate 2 in an isolated clean worktree with its own installed dependency set; pin the environment; produce `manifest-a.json` / `manifest-b.json`; diff by sorted path + SHA-256.
3. Apply S05's outcome: if the spike passed, record the exact pinning that achieved it. If it did not, run the **normalised comparison** fallback — identical file list, identical SHA-256 for every file except a **named, enumerated, individually justified** exception set recorded in `gate-report.json` — and state in the report that this **weakens D3's proof and requires sign-off** (`§12.5-O33`; the sign-off row is unsigned and contingent).
4. Time gate 2. Budget ≤3 min; **above 5 min it demotes to CI-only with an explicit `gate2: waived-local` entry** — a recorded waiver, never a silent skip.
5. Implement gate 4 through S65's wrapper at a pinned device size; a diff of one pixel is a fail.
6. Implement gate 8 by calling the same verify path S74 ships, so there is one implementation and not two.
7. Emit `gate-report.json` with `measured` **and** `threshold` on every row.

**Definition of Done.**
- Artifacts: eight gate modules, `gate-report.json` with eight rows, both build manifests, the screenshot pair and its diff, the before/after hashes of the live dependency surface.
- Validation: eight rows present (five is a fail of SL-S67-1); gate 6 output is a node list; a seeded design-time origin inside `srcset` is caught by gate 7; the live lockfile hash is unchanged.
- `slice.yaml` mapping — `acceptance_criteria: [A51, A52, A53, A57, "§12.17-A93", "§12.17-A94", SL-S67-1, SL-S67-2]`, `verification_method: exit-code` (A51/A53/§12.17-A94: `hash-compare`; A52: `screenshot-diff`; §12.17-A93: `grep-assert`).

**Assumption.** `[I]` Gate 2's installer invocation and publish-manifest filenames are **re-derived from the substrate spike's outcome** (S03), not copied from the source's package-manager-specific procedure (NA-B11, EL-085). If the substrate has not landed, gate 2 records INCONCLUSIVE — which blocks — rather than guessing an installer.

## Dev — execution contract

Never modify the live dependency tree; hash `package.json`, the lockfile and the dependency directory listing before and after and put both hashes in the bundle. Evidence bundle: (1) summary — eight gates, each pass/fail/inconclusive in one line; (2) traceability FR-202, FR-203 → file:line per gate; (3) structural quality — one gate per module, all returning verdicts, none throwing; (4) functional testing — one seeded failure per gate with its recorded verdict; (5) security/compliance — no credential used; the isolated worktree touched nothing live; (6) operational — how to re-run a single gate, and how the waiver is recorded; (7) self-assessment, stating **explicitly** that byte-identity across two installs is not established by any consulted source and what this run actually observed.

## QA — zero-trust verification

- **Count the gates yourself** in `gate-report.json`. Five rows, or eight rows where three are stubs, is a rejection.
- **Recompute at least twenty file hashes** from both build manifests and confirm they match the recorded values.
- **Re-hash the live `package.json`, lockfile and dependency listing** yourself; any change is a rejection.
- **Seed your own design-time origin** inside an inline `style` and inside `srcset` and confirm gate 7 catches both — the obvious `<script src>` case is the easy subset.
- **Force gate 6 to fail** and confirm the output is a node list, not a count.
- **Reject** if a normalised-comparison fallback was adopted without per-file justifications, or without the sign-off-owed statement; and **reject** any silent gate-2 skip — a waiver must be a row in the report.

## Dev Learnings

_Not Done until filled. Required: whether two builds were byte-identical on this toolchain, and which file classes differed if not (sourcemaps, hashed asset names, ordering)._

## QA Learnings

_Not Done until filled. Required: which gate was easiest to make look green while being hollow, and whether gate 2's runtime is near the 5-minute demotion edge — a gate that fails spuriously gets disabled by whoever is trying to ship._
