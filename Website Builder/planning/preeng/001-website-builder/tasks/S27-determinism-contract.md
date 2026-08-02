# S27-determinism-contract — Determinism contract: six hazards designed out

| Field | Value |
|---|---|
| Epic / Story | E7 / ST-08 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 1 / — |
| Depends on | S25-pure-renderer-and-resolution-policy |
| Requirements | FR-075 |
| Acceptance criteria | A53 · SL-S27-1 · SL-S27-2 · SL-S27-3 |
| CQ / evidence | CQ9 |
| Risk | **R15** — a `verify` that produces false positives teaches the user to ignore it, after which the drift guarantee is gone **while still appearing to exist** (NFR-12) |

## PM — slice definition

**Objective.** Make generation a pure function of documents, system lock and generator version, so verify can be trusted.

**In scope.** The six hazards designed out rather than tested for — (1) one fixed key comparator applied everywhere; (2) relative paths only, no absolute path in any output; (3) a fixed collator / `LC_ALL=C` for every sort; (4) ULID-derived node ids **never regenerated**; (5) binary assets compared by their recorded `{encoder, encoderVersion, settingsHash, outputSha256}` and **never re-encoded** during verification, because encoders are not bit-stable; (6) no clock, no network, no `Math.random`, no `process.env`, no outside-session-root reads at generate time, with a frozen `SOURCE_DATE_EPOCH`. Every generated file carries `@generated`, `doc-sha256`, `system-lock-sha256`, `generator-version` and **no timestamp**. `verify` produces an empty diff on a freshly generated project **and** after ten drag operations.

**Out of scope.** Bundler byte-reproducibility (the S05 spike and the purity gates, S67). `doctor.ts` and the shipped `verify` CLI surface (S74) — this slice owns the contract and the in-tree check that proves it.

**Assumption.** The ten-drag sequence is specified here but cannot be driven through the canvas until S43; it is replayed from a recorded typed-op fixture representing ten `move-node` ops, and re-run against the real canvas when S43 lands `[I]`, low confidence.

**Allowed files / contexts.**
- `scripts/lib/determinism.ts`, `scripts/lib/generate.ts` (marker emission only), `scripts/lib/asset-hash.ts`, `scripts/lib/verify-generate.ts`, the generate-time grep gate.

**Steps.**
1. Route every sort and every object iteration through the shared comparator and the fixed collator.
2. Emit the four-part marker header into every generated file; assert no timestamp token appears anywhere in the output tree.
3. Compare binary assets by recorded hash record only; make re-encoding at verify time impossible rather than discouraged.
4. Freeze `SOURCE_DATE_EPOCH` and assert the generate path reads no clock, no network, no random source, no environment and no path outside the session root — as a **grep gate over the generate-time module graph**, not a code review note.
5. Generate twice from an unchanged input and require an empty diff.
6. Apply the ten-op fixture, regenerate and require an empty diff again.

**Definition of Done.**
- Artifacts: the determinism module, the marker emitter, the asset hash comparator, the grep gate, both empty-diff transcripts.
- Validation: two consecutive generates diff empty; generate-then-ten-ops-then-generate diffs empty; the marker header is present in 100% of generated files; a timestamp grep returns zero; the ambient-input grep returns zero.
- `slice.yaml` mapping — `acceptance_criteria: [A53, SL-S27-1, SL-S27-2, SL-S27-3]`, `verification_method: hash-compare` (SL-S27-1 and SL-S27-3: `grep-assert`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-075 → file:line, one line per hazard; (3) structural quality — the generate path is a closed module graph; (4) functional testing — both diff transcripts plus a deliberately-nondeterministic fixture (an object built from an unsorted map) proving the check *fails* when it should; (5) security/compliance — the no-network property is asserted, not assumed; (6) operational — what an engineer does when `verify` reports a diff: read the marker hashes first, re-encode nothing; (7) self-assessment.

## QA — zero-trust verification

- **Generate twice yourself** and diff; then apply the ten-op fixture, generate again and diff again. A logged empty diff is not evidence.
- **Recompute one asset hash yourself** from the recorded `settingsHash` path and confirm the comparator never invokes an encoder — read the code path, do not trust the log.
- **Run your own greps** for a clock, `fetch`, `Math.random`, `process.env` and an absolute path across the generate-time module graph, and for any timestamp in the output tree.
- **Break determinism on purpose** — introduce an unsorted iteration in a scratch copy — and confirm `verify` reports it; a check that never fails is not a check.
- **Count the marker headers yourself** against the generated file count; anything short of 100% is a rejection.

## Dev Learnings

_Not Done until filled. Required: which of the six hazards actually fired during the build, and whether the ten-op fixture was a faithful stand-in for real drags._

## QA Learnings

_Not Done until filled. Required: the cheapest false-positive source found, and whether the grep gate is tight enough to survive a new dependency._
