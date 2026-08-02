# S54-art-motion-container-contract — One container contract for art and motion, with the pause affordance field

| Field | Value |
|---|---|
| Epic / Story | E11 / ST-18 |
| Type · MoSCoW · Size | build · MUST · L `[I]` |
| Phase / Demo | Phase 4 / — |
| Depends on | S21-token-compiler-dtcg-and-forge · S25-pure-renderer-and-resolution-policy |
| Requirements | FR-160, FR-161, FR-162, FR-163, FR-164, FR-165, FR-166, FR-167, FR-168, FR-169, FR-170 |
| Acceptance criteria | A22 · SL-S54-1 · SL-S54-2 · SL-S54-3 · SL-S54-4 |
| CQ / evidence | CQ12 · EL-044 · EL-062 · EL-064 |
| Note | **R14 has no known mitigation.** Motion is disabled in edit mode and judged in preview; human-in-the-loop relocates the problem rather than solving it. The UI states the limitation |

## PM — slice definition

**Objective.** Implement the container contract and its seven rules so unpausable or unreduced motion is structurally unbuildable.

**In scope.** One contract covering art and motion, carrying `boxSizing, aspectPolicy, anchor, overflow, mask, schemeAware, motionCapable, reducedMotionPoster, reducedMotionVariantRef, focalPoint, altText|decorative, licenseRef, trigger, viewportThreshold, source{kind, ref, poster}, playback{autoplay, muted, loop, iterationCount}, costClass, tokenRefs[]` **plus `pauseAffordanceRef`** (§13.4 gate 13a); the seven validation-time rules — (1) mandatory explicit `aspect-ratio` or `min-block-size` from the ratio scale; (2) animation may touch only `transform`, `opacity`, `filter` and may never change grid placement, width or height; (3) `trigger` as a closed enum `page-load | viewport-enter | viewport-scrub | pointerenter | click | always` with `viewportThreshold ∈ [0,1]` default 0.2, meaningful only for `viewport-enter`; (4) `reducedMotionVariantRef` mandatory whenever `motionCapable: true`, with the reduced-motion render **differing** where motion exists and still looking designed (A22); (5) `source.ref` resolving against `assets/manifest.json`, or `source.kind: 'none'`; (6) `muted` true whenever `source.kind: 'video'` and `autoplay: true`; (7) `costClass ∈ {free, cheap, heavy, gpu}` assigned per container **kind**, not per instance; Style and Motion as **two tabbed pickers** for dual-axis kinds, never a flattened cross-product; motion disabled in edit mode with the limitation stated in the UI.

**Out of scope.** The live motion-concurrency counter (S64) — this slice supplies `costClass` as the quantity it counts. Artwork content itself (S55, S56). Any automated visual scoring of motion: VLM recall of aesthetic animation measured **0.16** `[U — EL-044]`, so acceptance rests on the human plus deterministic lint.

**Allowed files / contexts.**
- `scripts/lib/containers.ts`, `scripts/lib/container-validate.ts`, the renderer's container branch, the component-bar tabbed picker, `04-site/pages/<id>.doc.json` through typed ops only.
- TypeScript on Bun. **No `.py` file anywhere in the skill tree.**

**Steps.**
1. Encode the contract as one type with every field above, `pauseAffordanceRef` included from the first commit.
2. Implement the seven rules as validators returning structured results, not thrown errors.
3. Make the `pauseAffordanceRef` requirement constructive: a container kind that needs one cannot be built without it.
4. Assign `costClass` per kind in a data table and expose it for the concurrency counter.
5. Build the two tabbed pickers; assert the picker never enumerates a Style×Motion cross-product.
6. Disable motion in edit mode, route motion judgement to preview, and print the R14 limitation in the UI text.
7. Record the concurrency caps as **provisional** `[I — EL-062]` and the motion-kind homogeneity threshold as a carried default `[I — EL-064]`.

**Definition of Done.**
- Artifacts: the contract type, the seven validators, the cost-class table, the tabbed picker, the stated-limitation UI text.
- Validation: motion-capable container with no reduced-motion sibling fails; autoplay video that is not muted fails; a rule touching width/height/grid placement is rejected; a needs-pause container without `pauseAffordanceRef` cannot be constructed; the reduced-motion render **differs** from the full-motion render.
- Demo-able increment: place a motion container in the editor, see it inert in edit mode and animating in preview with a working pause control.
- `slice.yaml` mapping — `acceptance_criteria: [A22, SL-S54-1, SL-S54-2, SL-S54-3, SL-S54-4]`, `verification_method: exit-code` (A22: `screenshot-diff`, SL-S54-4: `manual-observation`).

## Dev — execution contract

Evidence bundle: (1) summary listing each rule with its enforcement point; (2) traceability FR-160…FR-170 → file:line; (3) structural quality — validators pure, cost classes as data; (4) functional testing — one failing fixture per rule plus the reduced-motion screenshot pair; (5) security/compliance — `source.ref` cannot escape the asset allowlist; (6) operational — how motion is toggled between edit and preview, and what the user is told; (7) self-assessment stating R14 plainly as unmitigated.

## QA — zero-trust verification

- **Build your own** motion-capable container with `reducedMotionVariantRef` omitted and require a fail verdict, not an exception.
- **Diff the two renders yourself** — a reduced-motion capture identical to the full-motion capture is a rejection.
- **Attempt an animation rule on `height`** and require rejection.
- **Point `source.ref` at a path absent from `assets/manifest.json`** and require refusal.
- **Reject** any claim that motion feel was judged in edit mode, or any artifact asserting the concurrency caps are validated ceilings rather than carried defaults `[I]`.

## Dev Learnings

_Not Done until filled. Required: which of the seven rules was hardest to enforce constructively rather than after the fact._

## QA Learnings

_Not Done until filled. Required: whether the stated R14 limitation was actually visible to a user, or buried in a tooltip._
