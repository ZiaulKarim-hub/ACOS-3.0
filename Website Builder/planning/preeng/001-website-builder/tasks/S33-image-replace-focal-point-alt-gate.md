# S33-image-replace-focal-point-alt-gate — Image replace, focal point, blocking alt gate and auto-recompression

| Field | Value |
|---|---|
| Epic / Story | E8 / ST-10 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 2 / — |
| Depends on | S31-typed-ops-autosave-history-undo |
| Requirements | FR-084 |
| Acceptance criteria | A35 · A36 · SL-S33-1 · SL-S33-2 |
| CQ / evidence | CQ11 |
| Note | **Research F16** — two distinct gates read `assets/manifest.json`: **licence completeness** (every recorded asset has a class) and **reference resolution** (every referenced asset exists). A hallucinated path passes the first and ships a broken page |

## PM — slice definition

**Objective.** Make image handling preserve composition and make missing alt text impossible to place, not merely impossible to ship.

**In scope.** Replace-in-place preserving container size, crop and position; cropping by a **single draggable focal-point dot** written to `props.focalPoint`, **never a crop rectangle**; placing any image without alt text or an explicit decorative toggle **blocks the placement itself** — not the lock, not a warning; oversized photos triggering **auto-recompression with a visible, undoable confirmation**; the `register-asset`, `set-asset-meta`, `set-alt-text` and `record-derivative` ops; every derived image recording `{encoder, encoderVersion, settingsHash, outputSha256}` in `assets/manifest.json`; the manifest as the **allowlist** — an asset id absent from it hard-fails at render.

**Out of scope.** Lane A code-drawn artwork and Lane B ingestion (S55, S56) — this slice handles replacement of an image already in an art or media slot. Art-container motion (S54). The LOCK-time alt-coverage gate (S68); the point here is that the placement never happens without alt in the first place.

**Assumption.** No oversize threshold is published; the recompression trigger ships as a configured value in the project config, recorded in the evidence bundle with its measured effect, rather than a literal in the code path `[I]`, low confidence.

**Allowed files / contexts.**
- `app/editor/image-panel.ts`, `scripts/lib/ops/asset-ops.ts`, `scripts/lib/recompress.ts`, `04-site/assets/manifest.json` (through the op path only), `04-site/assets/**` (derived files).

**Steps.**
1. Implement replace as a props-level op: the container's size, crop and position are untouched; only the asset reference and `focalPoint` change.
2. Implement the focal point as one draggable dot with a live preview at all four device widths; no rectangle handles anywhere in the UI.
3. Gate placement on `alt` text **or** an explicit decorative toggle; the commit is refused with a message naming which is missing.
4. Detect oversize on drop, recompress with the pinned encoder, show the confirmation, and make the whole thing one undo entry.
5. Record the derivative record on every derived file, and refuse to register an asset with no licence class (400).
6. Assert both manifest gates: every recorded asset has a licence class, **and** every referenced asset resolves on disk.

**Definition of Done.**
- Artifacts: the image panel, the asset ops, the recompressor, the manifest entries with derivative records.
- Validation: a replace leaves container geometry byte-identical in the document; a placement without alt is refused; an oversize drop recompresses, confirms and undoes cleanly; both manifest gates run and a hallucinated path is caught by the second.
- `slice.yaml` mapping — `acceptance_criteria: [A35, A36, SL-S33-1, SL-S33-2]`, `verification_method: manual-observation` (A36 and SL-S33-2: `exit-code`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-084 → file:line; (3) structural quality — one asset write path through the ops layer; (4) functional testing — before/after document diffs for a replace, screenshots of the focal point at 390 and 1280, the refused placement, and the recompression undo; (5) security/compliance — licence class per asset and the two-gate distinction stated explicitly; (6) operational — what the user does when the only available image has no licence class; (7) self-assessment.

## QA — zero-trust verification

- **Replace an image yourself and diff the document**; any change to container size, crop or position is a rejection.
- **Try to place an image with no alt and no decorative toggle** — if the placement lands and a warning appears, that is the rejection, regardless of what the copy says.
- **Recompute one derivative's `outputSha256` yourself** from the file on disk and compare it to the manifest record; do not trust the logged value.
- **Add a manifest entry pointing at a path that does not exist** and confirm the reference-resolution gate catches it while the licence gate passes — that gap is the point.
- **Undo a recompression** and confirm the original bytes return.

## Dev Learnings

_Not Done until filled. Required: the measured recompression threshold and its effect on page weight, and whether focal-point-only cropping was sufficient for a real hero image._

## QA Learnings

_Not Done until filled. Required: which alt-gate bypass was easiest to find, and whether the two manifest gates were genuinely independent._
