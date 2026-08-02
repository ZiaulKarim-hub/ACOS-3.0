# S74-verify-and-doctor — `verify` and `doctor`

| Field | Value |
|---|---|
| Epic / Story | E18 / ST-25 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 6 / — |
| Depends on | S27-determinism-contract, S69-lock-snapshots-manifest-and-unlock |
| Requirements | FR-242 |
| Acceptance criteria | A53 · SL-S74-1 · SL-S74-2 · SL-S74-3 |
| CQ / evidence | CQ9 · EL-063 |
| Note | **R15's warning, restated:** a false-positive `verify` kills the guarantee **silently** — a check users learn to ignore removes the guarantee while appearing to keep it. That is the risk this slice is judged on |

## PM — slice definition

**Objective.** Ship the two diagnostics that keep the drift guarantee real and name **month-six rot** before it is fatal.

**In scope.** `verify.ts` — regenerate to a **temporary** directory, `diff -r` the text files, **hash-compare binaries separately** (a binary diff is noise), and **re-serialise every document into canonical form requiring a zero diff**; the empty-diff bar both **fresh** and **after ten drags** (A53); `doctor.ts` — hash mismatches against `.wb/doc-hashes.json`, orphaned overrides, stale locks, and override-accumulation escalation at the thresholds **read from the project record** (`site.json`), whose starting values are `≥5 per page` amber, `≥15` red, `≥40 per site`, `≥25% of a page's nodes` `[I — stated starting numbers, tunable; EL-063, confidence 0.5]`; a structured report from both, never a prose summary; `verify` is also purity gate 8's implementation, called from S67 so there is **one** verify in the codebase.

**Out of scope.** Repairing what `doctor` finds. Tuning the thresholds on the tool's own authority — they live in the project record and the human moves them. Any judgement of design quality; `doctor` reports rot, never taste.

**Allowed files / contexts.**
- `scripts/verify.ts`, `scripts/doctor.ts`, `scripts/lib/canonical-serialise.ts`, `.wb/tmp/verify/` (scratch, git-ignored), the doctor report path.
- **Regeneration goes to a temp directory only** — `verify` never overwrites the live tree, and never `rm -rf`s anything.

**Steps.**
1. `verify`: regenerate to `.wb/tmp/verify/`; `diff -r` text; hash-compare binaries in a separate pass; report the two result classes separately so a hashed asset name cannot masquerade as a content drift.
2. Re-serialise every doc-owned JSON through `canonical-serialise.ts` and require a **zero diff** — this is the same canonicalisation purity gate 8 asserts (§12.17-A98).
3. Run `verify` at three moments — session start, lock time and in the selftest — so drift is caught at the point it appears, not at the point it hurts.
4. Prove the A53 bar: empty diff on a fresh generate **and** empty diff after ten drags.
5. `doctor`: report hash mismatches, orphaned overrides and stale locks; read thresholds from `site.json` and escalate amber/red accordingly; every finding names the node or file, never a bare count.
6. Treat any **false positive** as a defect of the **highest severity** and record each one with its root cause; the slice's own bug log is an artifact.
7. Emit both reports as structured JSON consumable by the evidence bundle.

**Definition of Done.**
- Artifacts: `verify.ts`, `doctor.ts`, the canonical serialiser, both report shapes, the ten-drag transcript, the false-positive log.
- Validation: empty diff fresh and after ten drags; a seeded out-of-band edit is caught by `doctor` as a hash mismatch; a seeded orphan override is listed by node id; a re-serialisation diff of one byte fails.
- `slice.yaml` mapping — `acceptance_criteria: [A53, SL-S74-1, SL-S74-2, SL-S74-3]`, `verification_method: hash-compare` (SL-S74-2: `exit-code`; SL-S74-3: `manual-observation`).

## Dev — execution contract

Never write into the live tree from `verify`; use `.wb/tmp/verify/` and never `rm -rf` it (delete by moving aside, or write to a fresh timestamped path). Evidence bundle: (1) summary — verify clean yes/no, doctor findings by class; (2) traceability FR-242 → file:line; (3) structural quality — one verify implementation shared with purity gate 8, provable by call site; (4) functional testing — the fresh and ten-drag transcripts, plus one seeded failure per doctor class; (5) security/compliance — no credential read, no network; (6) operational — how a user acts on each doctor class, in one sentence each; (7) self-assessment listing **every false positive observed and its cause**, because that list is the real deliverable.

## QA — zero-trust verification

- **Run `verify` yourself** on an untouched project and require an empty diff; then **make ten drags yourself** and re-run.
- **Deliberately provoke a false positive** — touch an mtime, reorder a JSON key, re-save a binary — and confirm none of these alone trips `verify`. A `verify` that fires on key ordering is a rejection, because it will be disabled by whoever is trying to ship.
- **Recompute two document hashes yourself** and compare to `.wb/doc-hashes.json`.
- **Seed an orphaned override** and confirm `doctor` names the node, not a count.
- **Change a threshold in `site.json`** and confirm `doctor` reads it rather than a hardcoded constant.
- **Reject** if `verify` and purity gate 8 are two separate implementations — two implementations means two behaviours and one of them is wrong.

## Dev Learnings

_Not Done until filled. Required: every false positive observed, its cause, and what made the binary/text split necessary._

## QA Learnings

_Not Done until filled. Required: which provocation nearly produced a false positive, and whether a user would trust this `verify` after a month._
