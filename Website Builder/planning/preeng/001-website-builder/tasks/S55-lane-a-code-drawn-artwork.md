# S55-lane-a-code-drawn-artwork — Lane A: code-drawn, token-parameterised artwork that re-skins with the direction

| Field | Value |
|---|---|
| Epic / Story | E11 / ST-18 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 4 / — |
| Depends on | S54-art-motion-container-contract |
| Requirements | FR-150, FR-155 |
| Acceptance criteria | A20 · A21 · A23 |
| CQ / evidence | CQ1 |
| Note | Lane A is **the artwork lane actually available from the generation channel**. Lane B is ingestion (S56); **Lane C is out of v1** with a runbook only |

## PM — slice definition

**Objective.** Deliver the artwork lane that is actually available from the generation channel, and make it move with the hue anchors.

**In scope.** Code-drawn, token-parameterised artwork: **≥60% of a 20-artwork set is token-referencing** via `currentColor` / `var(--*)` (A20); changing a direction's hue anchors **re-skins all token-referencing artwork with no regeneration** (A21); the **20-artwork quota is 20 TOTAL per direction for v1** (§17-OQ-02); custom cursors never exceeding 128×128 with a native keyword fallback on every `cursor: url()` (A23, FR-155); registration of every Lane A piece in `assets/manifest.json` with `lane: "A"`, `tokenReferencing: true|false` and a licence class; placement through the S54 container contract, never as a bare inline blob.

**Out of scope.** Asset-library ingestion, affinity chips and the no-library warning (S56). External raster generation — Lane C is out of v1. Any aesthetic scoring of an artwork.

**Assumption (recorded).** The 20-artwork quota is read as **20 total per direction**, per the adopted default at §17-OQ-02; a game-style site (the FruitSync exemplar's **231 sprites**) is stated plainly as needing a different artwork path, and that statement ships in the runbook rather than being solved here.

**Allowed files / contexts.**
- `scripts/lib/artwork-lane-a.ts`, `scripts/lib/cursors.ts`, `02-system/<directionId>/artwork/**`, `04-site/assets/manifest.json` (through the register-asset op only).
- TypeScript on Bun. **No `.py` file anywhere in the skill tree.**

**Steps.**
1. Emit each artwork as code that references tokens for every colour it can — `currentColor` and `var(--*)` only; no baked hex where a token exists.
2. Compute the token-referencing ratio over the delivered set mechanically and fail below 0.60.
3. Prove the re-skin: change the direction's hue anchors, re-render, and show the artwork changed **with no regeneration step in between**.
4. Register every piece in the asset manifest with lane, `tokenReferencing`, licence class and file hash.
5. Enforce the cursor rules: dimension assertion ≤128×128 and a native keyword fallback in every `cursor: url()` declaration.
6. Place at least one piece through a real container so the demo is a page, not a gallery of files.

**Definition of Done.**
- Artifacts: the Lane A artwork set, the ratio computation, the re-skin transcript, the manifest entries, the cursor rules.
- Validation: the ratio is recomputed and ≥0.60; a hue-anchor change produces a visibly different render with no regeneration; every `cursor: url()` has a fallback; no cursor exceeds 128×128.
- Demo-able increment: flip the direction's hue anchors in the editor and watch the artwork re-skin live.
- `slice.yaml` mapping — `acceptance_criteria: [A20, A21, A23]`, `verification_method: recompute` (A21: `screenshot-diff`, A23: `grep-assert`).

## Dev — execution contract

Evidence bundle: (1) summary with the computed ratio and the set size; (2) traceability FR-150, FR-155 → file:line; (3) structural quality — artwork emission is data-driven, not one function per piece; (4) functional testing — the ratio recomputation, the before/after re-skin captures, the cursor grep; (5) security/compliance — every piece carries a licence class and no remote origin; (6) operational — how a new Lane A piece is added and what it must declare; (7) self-assessment stating which pieces could not be fully tokenised and why.

## QA — zero-trust verification

- **Recompute the token-referencing ratio yourself** from the emitted files; a logged ratio is not evidence.
- **Change a hue anchor yourself**, re-render, and diff the captures; identical captures are a rejection, and so is any regeneration step appearing in the transcript.
- **Grep every `cursor: url()`** for a native keyword fallback and measure the cursor assets; one violation is a rejection.
- **Read the manifest**: an artwork entry without a licence class is a rejection.
- **Reject** any artifact implying Lane C shipped, or that a 20-artwork set is per style family rather than 20 total per direction.

## Dev Learnings

_Not Done until filled. Required: which artwork motifs resisted tokenisation, and whether the 60% floor forced a stylistic compromise._

## QA Learnings

_Not Done until filled. Required: whether the re-skin was genuinely regeneration-free or quietly re-ran a build step._
