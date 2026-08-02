# S28-demo-1-static-direction-render — DEMO 1: interview → prompt → ingest → one direction rendered static

| Field | Value |
|---|---|
| Epic / Story | E7 / ST-08 |
| Type · MoSCoW · Size | demo · MUST · M `[I]` |
| Phase / Demo | Phase 1 / **Demo 1** |
| Depends on | S14-concept-document-synthesis · S20-local-regeneration-mode · S22-flat-variable-layer-and-extract-override · S26-breakpoint-vocabulary-and-cascade · S27-determinism-contract |
| Requirements | — (demo slice; re-exercises S14, S20, S22, S26, S27 end to end) |
| Acceptance criteria | A4 · A5 · A7 · A12 · SL-S28-1 |
| CQ / evidence | CQ1 · CQ5 · CQ13 |
| Note | **H7 is untested until this runs** — whether the chosen direction survives contact with real typography and real artwork. A demo slice writes **no new product code**; every defect found is routed back to its owning slice |

## PM — slice definition

**Objective.** Prove end to end that a conversation becomes a coherent, licence-clean design system and a page a human can look at.

**In scope.** One recorded run of the whole Phase-1 pipeline producing `00-interview/answers.json`, `00-interview/concept.md`, the Stage-A and Stage-B prompts, an ingested design system and a **rendered static page**; screenshots at **390** and **1280** captured at **pinned device heights** (390×844, 1280×800); the Local Regeneration Mode leg run on the identical prompt through the identical validator with **zero pastes** (A12); the ingest leg proving a complete chunk lands with zero manual file operations beyond one `pbpaste` (A7); the check that every emitted design directive **cites the interview question id that produced it** (A4); the check that `concept.md` carries its refusal line (A5).

**Out of scope.** Any editing whatsoever — no selection, no ops, no autosave (S29). Any new module: a bug found lands in the owning slice and the demo is re-run.

**Assumption.** No evidence path is published for demo slices; the run is recorded under `evidence/demo-1/<sessionId>/` with the transcript, both screenshots and the artifact hashes `[I]`, low confidence.

**Allowed files / contexts.**
- `evidence/demo-1/**` (write), the session directory (read), the capture wrapper. **No file under `scripts/` may be modified by this slice.**

**Steps.**
1. Run the interview to `answers.json` and synthesise `concept.md`; confirm the refusal line exists before advancing.
2. Emit Stage A, cut the capsules to the chosen direction, emit Stage B; confirm each directive carries its question id.
3. Ingest the returned bundle via the `FILE:`-block parser with one `pbpaste`; record the paste count and chunk count.
4. Re-run the identical prompt through Local Regeneration Mode; require the **identical validator** to pass with **zero pastes**, and record both reports.
5. Compile tokens, render the page statically, and capture 390 and 1280 at pinned device heights.
6. Assemble the run record: every artifact path, its sha256, and the two screenshots side by side.

**Definition of Done.**
- Artifacts: `answers.json`, `concept.md`, both prompt stages, the ingested system, the rendered page, both screenshots, the run record with hashes.
- Validation: the A4 grep over emitted directives; the refusal-line check; the one-`pbpaste` ingest; the zero-paste regeneration leg; both screenshots at pinned heights; a human verdict in words.
- `slice.yaml` mapping — `acceptance_criteria: [A4, A5, A7, A12, SL-S28-1]`, `verification_method: manual-observation` (A4: `grep-assert`; A5, A7, A12: `exit-code`).

## Dev — execution contract

Evidence bundle: (1) summary — one paragraph a non-engineer can read; (2) traceability — each demo step to the slice that owns it; (3) structural quality — proof that **no product file changed** during the run (`git status` before and after); (4) functional testing — the full transcript with paste count, chunk count and both validator reports; (5) security/compliance — the licence position of every font and asset that reached the page; (6) operational — wall-clock time of the hand-carry leg, recorded because R7 is the likeliest quiet death of this product; (7) self-assessment, including whether the direction actually looks deliberate.

## QA — zero-trust verification

- **Re-run the pipeline yourself** from the recorded answers; a demo you cannot reproduce is a rejection.
- **Recompute the artifact hashes** in the run record; do not trust the recorded values.
- **Check the pinned heights in both screenshots yourself** — an auto-height capture approves a hero at a height no device has.
- **Grep the emitted directives** for question ids and compute the coverage fraction yourself.
- **Read `concept.md`** and find the refusal line; if it is absent, the pipeline should have refused to advance.
- **Diff the Local Regeneration Mode output against the pasted output** through the same validator.
- **Reject** if any product file changed during the demo run.

## Dev Learnings

_Not Done until filled. Required: the measured wall-clock cost of the hand-carry leg, and the first place the pipeline needed a human nudge the design did not anticipate._

## QA Learnings

_Not Done until filled. Required: whether the rendered page reads as designed or as assembled, in the reviewer's own words, and what evidence would have changed that verdict._
