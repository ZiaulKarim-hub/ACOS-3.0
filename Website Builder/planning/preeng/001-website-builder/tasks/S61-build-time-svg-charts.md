# S61-build-time-svg-charts — Build-time SVG charts with dataviz sub-tokens and two shipped data states

| Field | Value |
|---|---|
| Epic / Story | E13 / ST-20 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 4 / — |
| Depends on | S60-registry-table-embed-form |
| Requirements | FR-192, FR-193 |
| Acceptance criteria | SL-S61-1 · SL-S61-2 · SL-S61-3 · SL-S61-4 |
| CQ / evidence | CQ1 |
| Note | **R24** — charts break coherence by construction. The mitigation is dataviz sub-tokens derived from the direction's anchors, validated colourblind-safe in both schemes |

## PM — slice definition

**Objective.** Make charts read as one system with the site, colourblind-safe in both schemes, and ship no chart runtime.

**In scope.** Charts emitted as **build-time SVG with ≤4 mark types**; **no chart runtime ships** — the performance gate depends on this, so it is a hard constraint and not a preference; the decomposition into marks, a **chrome kit** (axes, gridlines, ticks, labels, legend, tooltip, annotation/reference line, zero-line) whose **4 treatments are applied consistently across all mark types**, which is what makes a site's charts read as one system; colour ramps **derived from the direction's OKLCH anchors** and **validated colourblind-safe in both light and dark schemes**; of the five data states, only **empty** and **single-data-point** ever ship; **loading and error are editor-only previews** labelled "Preview only — not shown to visitors"; interactive "partial" is v3.

**Out of scope.** Any client-side charting library. Interactive charts. The chart-data field and placement path (S60). Tooltip interactivity beyond the static chrome treatment.

**Allowed files / contexts.**
- `scripts/lib/charts/{marks,chrome,ramps,states,index}.ts`, `scripts/lib/dataviz-tokens.ts`, `06-custom/charts/**` (write), the chart node's renderer branch.
- TypeScript on Bun. **No `.py` file anywhere in the skill tree.**

**Steps.**
1. Implement the ≤4 mark types as pure SVG emitters taking data plus dataviz sub-tokens; assert the mark-type count in code.
2. Derive the dataviz sub-tokens from the direction's OKLCH anchors — never independently picked values.
3. Validate every ramp colourblind-safe in **both** schemes and record the computed separations, not a claim.
4. Build the chrome kit once and apply its treatments across all mark types; a mark type that styles its own axis is a defect.
5. Ship empty and single-data-point states; render loading and error only in the editor behind the fixed "Preview only — not shown to visitors" label.
6. Grep the published tree to prove zero chart runtime and zero chart-library import.

**Definition of Done.**
- Artifacts: the mark emitters, the chrome kit, the ramp derivation and its validation record, the two shipped states, the editor-only previews.
- Validation: published output contains SVG and no chart script; the ramp validation is recomputed in both schemes; a fifth mark type is rejected; loading/error strings are absent from published output.
- Demo-able increment: paste a small table of numbers into a chart node and see a token-styled chart render statically on the page.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S61-1, SL-S61-2, SL-S61-3, SL-S61-4]`, `verification_method: grep-assert` (SL-S61-2: `recompute`, SL-S61-4: `manual-observation`).

## Dev — execution contract

Evidence bundle: (1) summary listing the mark types and the chrome treatments; (2) traceability FR-192, FR-193 → file:line; (3) structural quality — one chrome kit, no per-mark styling; (4) functional testing — the runtime grep, the ramp validation in both schemes, the empty and single-point states, a rejected fifth mark type; (5) security/compliance — charts embed no remote origin and no external font; (6) operational — how a chart is regenerated when the direction's anchors change; (7) self-assessment.

## QA — zero-trust verification

- **Grep the published tree yourself** for any chart runtime, library import or `<script>` inside a chart subtree; one hit is a rejection.
- **Recompute the colourblind separation yourself** for at least two ramp pairs in **both** schemes; a logged "validated" you cannot reproduce is a rejection.
- **Count the mark types** in the emitted code; five is a rejection.
- **Grep published output** for the loading and error state markup; presence is a rejection.
- **Compare two charts of different mark types** for chrome consistency — divergent axis or label treatment is a rejection.
- **Reject** any ramp whose colours were picked rather than derived from the direction's anchors.

## Dev Learnings

_Not Done until filled. Required: which mark type most resisted the shared chrome kit, and whether the colourblind validation forced a ramp away from the direction's anchors._

## QA Learnings

_Not Done until filled. Required: whether "no chart runtime" survived the whole build path or reappeared through a transitive import._
