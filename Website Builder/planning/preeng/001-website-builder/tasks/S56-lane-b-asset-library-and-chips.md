# S56-lane-b-asset-library-and-chips — Lane B ingestion, asset manifest, affinity filter chips, Lane C runbook and the honest warning

| Field | Value |
|---|---|
| Epic / Story | E11 / ST-18 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 4 / — |
| Depends on | S54-art-motion-container-contract · S10-warm-start-and-asset-library-detection |
| Requirements | FR-151, FR-152, FR-153, FR-154 |
| Acceptance criteria | SL-S56-1 · SL-S56-2 · SL-S56-3 · SL-S56-4 |
| CQ / evidence | CQ10 |
| Note | **§17-OQ-12 / R1** — when a project has no asset library there is **no known mitigation that preserves the paste-only path**. This slice states that; it does not soften it |

## PM — slice definition

**Objective.** Ingest a real asset library with licence classes and affinity tags, and tell the user the truth at interview time when there is none.

**In scope.** Lane B ingestion into `04-site/assets/manifest.json` — the allowlist — with `{id, lane, path, tokenReferencing, directionAffinity[], licenceClass, sourceUrl?, fileHash, generator?, model?, planTier?, prompt?, alt|decorative, derivatives[]}`; ingestion **refusing** any asset with no licence class; the asset pane with **direction-affinity filter chips** (the chips are what makes presenting 20 artworks legal — R34); the **Lane C runbook** at `docs/lane-c-raster-runbook.md` whose output ingests through this same manifest path, with **no external generation invoked by the skill in v1**; an explicit **interview-time warning** when a project has no asset library, fired **before** a design system the pipeline cannot fully deliver is generated.

**Out of scope.** Lane A emission (S55). Invoking any external raster generator. The lock-time asset-reference-resolution gate 23a (S68) — this slice supplies the manifest it reads.

**Two distinct gates read this manifest** and must not be conflated: **licence completeness** (every recorded asset has a class) and **reference resolution** (every referenced asset exists). A hallucinated path passes the first and ships a broken page.

**Allowed files / contexts.**
- `scripts/lib/assets-ingest.ts`, `scripts/lib/asset-pane.ts`, `04-site/assets/manifest.json` (through `register-asset` / `record-derivative` ops only), `docs/lane-c-raster-runbook.md`, the interview warning hook from S10.
- TypeScript on Bun. **No `.py` file anywhere in the skill tree.**

**Steps.**
1. Implement ingestion: hash every file, record the licence class, and **refuse** — with the file named — when the class is absent.
2. Tag each asset with a direction-affinity set; affinity is data on the asset, not a heuristic computed at render time.
3. Build the asset pane with affinity chips; presenting the set unchipped is a defect by requirement, not a style preference.
4. Write the Lane C runbook and prove its stated output shape ingests through this same path; grep to prove the skill invokes no external generator.
5. Fire the no-library warning at interview time through S10's detection, before system generation, and record that it fired.
6. State in the warning text that no known mitigation preserves the paste-only path — plainly, without hedging.

**Definition of Done.**
- Artifacts: the ingester, the manifest, the chipped asset pane, `docs/lane-c-raster-runbook.md`, the interview-time warning and its record.
- Validation: an asset with no licence class fails ingestion; every ingested asset carries hash + affinity + class; the chips filter the pane; a no-library project shows the warning before generation; no external-generation call exists.
- Demo-able increment: point the skill at a real asset folder, ingest it, and filter the pane by direction affinity.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S56-1, SL-S56-2, SL-S56-3, SL-S56-4]`, `verification_method: exit-code` (SL-S56-2 and SL-S56-4: `manual-observation`, SL-S56-3: `grep-assert`).

## Dev — execution contract

Evidence bundle: (1) summary with the ingested count and the licence-class histogram; (2) traceability FR-151…FR-154 → file:line; (3) structural quality — one ingest path, one manifest writer; (4) functional testing — a missing-licence fixture, a chip-filter run, a no-library session transcript; (5) security/compliance — assets are an allowlist; a path outside the session root is refused; (6) operational — how the runbook's output re-enters, and what happens to a re-ingested duplicate hash; (7) self-assessment.

## QA — zero-trust verification

- **Ingest your own asset with the licence class removed** and require refusal naming the file.
- **Recompute two file hashes yourself** and compare to the manifest.
- **Use the chips**: an unchipped 20-item pane is a rejection.
- **Grep the whole skill tree** for an external image-generation call; one hit is a rejection of the Lane-C-is-out claim.
- **Run a no-library session** and confirm the warning fires **before** system generation — order is the requirement, not the presence of the string.
- **Reject** any warning text that implies a workaround exists for the paste-only path.

## Dev Learnings

_Not Done until filled. Required: what real asset libraries contained that the manifest shape did not anticipate._

## QA Learnings

_Not Done until filled. Required: whether the licence-completeness and reference-resolution gates were kept genuinely separate._
