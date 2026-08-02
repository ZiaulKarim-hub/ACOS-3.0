# S15-font-catalog-and-snapshot — Font catalog with pre-subsetted cuts, and the per-session snapshot

| Field | Value |
|---|---|
| Epic / Story | E4 — Step 2 prompt generator / ST-05 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 1 / — |
| Depends on | S02-o1-font-policy-probe |
| Requirements | FR-040 |
| Acceptance criteria | SL-S15-1 · SL-S15-2 |
| CQ / evidence | CQ10 · CQ5 · EL-067 |
| Risk | R2 — a direction judged in a preview that cannot render its typeface is a look the user has never seen |

## PM — slice definition

**Objective.** Build a skill-owned, cross-project font catalog whose base64 cuts are computed **locally, ahead of time, never by the generation model**, and pin a hash-stamped snapshot per session.

**In scope.** `.acos/website-builder/library/font-catalog.json` with 24–32 open-licensed families curated by role; per entry `{familyId, classification, role, foundry, licenceClass, sourceUrl, fileHash, glyphCoverage, preSubsettedCuts:{latin, latinExtended}, attributionRequired}`; local subsetting; the session snapshot into `01-prompt/font-catalog.snapshot.json`; a build-failing check for a missing licence class.

**Out of scope.** Embedding commercial-foundry faces (they emit a pre-launch blocker, S71). Prompt text (S16). Font fallback metrics — those are a derived token family and belong to the compiler (S21).

**Allowed files / contexts.**
- `scripts/lib/font-catalog.ts`, `scripts/tools/subset-font.ts`, the library catalog path, `01-prompt/font-catalog.snapshot.json`.

**Steps.**
1. Curate the family list by role (display, text, mono, accent), recording licence class and source for each.
2. Subset locally to the preview glyph set; store base64 cuts and the source file hash.
3. Fail the build on any entry missing a licence class — the licence field is not optional.
4. At Step-2 start, snapshot the catalog with a content hash into the session; compare the hash at prompt emission so a mid-run library refresh cannot change what the session is judging.
5. Record the count actually shipped; 24–32 is a starting number, not a measured optimum.

**Definition of Done.**
- Artifacts: the catalog, the subsetting tool, the session snapshot, the licence assertion.
- Validation: every entry has a licence class and a file hash; the snapshot hash is compared at emission; a deliberately licence-less entry fails the build.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S15-1, SL-S15-2]`, `verification_method: exit-code` (SL-S15-2: `hash-compare`).

## Dev — execution contract

Base64 cuts are computed by this tool, never requested from a model. Evidence bundle: (1) summary with the shipped family count; (2) traceability FR-040 → file:line; (3) structural quality — the catalog is data with one writer; (4) functional testing — the licence-less fixture failing, and a snapshot hash comparison across a simulated library refresh; (5) security/compliance — every source URL and licence class recorded, ready for the evidence bundle; (6) operational — how a family is added; (7) self-assessment.

## QA — zero-trust verification

- **Recompute** three entries' file hashes yourself from the source binaries.
- **Decode one base64 cut** and confirm it is a real font binary of the claimed family, not a placeholder.
- **Run the licence-less fixture yourself** and require a non-zero exit.
- **Simulate a library refresh** and confirm the session snapshot comparison detects it.
- **Reject** if any entry's licence class was inferred rather than read from a licence file.

## Dev Learnings

_Not Done until filled. Required: subsetting pitfalls, and whether the preview glyph set was sufficient in practice._

## QA Learnings

_Not Done until filled. Required: whether any catalog entry could ship without an attribution note that it needs._
