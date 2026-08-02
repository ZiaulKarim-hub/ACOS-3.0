# S64-live-checks-scoped — Live checks: scoped, sub-100ms, drop and mouseup only

| Field | Value |
|---|---|
| Epic / Story | E17 / ST-21 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 5 / — |
| Depends on | S63-gates-ts-verdicts-and-tiers · S43-drag-to-place-and-drop-algorithm |
| Requirements | FR-231, FR-234 |
| Acceptance criteria | A27 · SL-S64-1 · SL-S64-2 · SL-S64-3 |
| CQ / evidence | CQ11 · CQ12 · EL-005 · EL-064 |
| Note | The dividing line is **scoped arithmetic/DOM-read vs whole-document render pass** — not "a11y vs performance". Live checks never fight the drag |

## PM — slice definition

**Objective.** Run the live half of the gate suite without ever fighting the drag, including the running motion-concurrency counter.

**In scope.** The live set, scoped to the touched subtree and firing on **drop and mouseup only** (never mid-drag, never per-frame), under the sub-100ms budget: contrast recompute on every touched pair (**WCAG 2 ratio is the gate**, APCA Lc is advisory `[U — EL-005]`); target size via `getBoundingClientRect()` flagging <24×24 unless a documented exception applies (A27, editor chrome checked live on render, not only at lock); a scoped accessibility-engine run on the touched subtree; overflow/clipping via `ResizeObserver` + `scrollWidth > clientWidth`; focus-not-obscured intersection; reading-order-vs-visual-order walk; reduced-motion sibling presence; the **alt/decorative gate that blocks the placement**; image auto-optimisation on drop; the budget HUD; and the **motion-concurrency running counter** accumulating visibly turn by turn rather than surfacing at LOCK. The **anti-slop lint appears here only as a dismissible Tier-2 advisory with permanent per-element dismiss — never as a block** (its hard-gate role is upstream at ingest, S19).

**Out of scope.** Whole-document lock-time checks (S68). Capture (S65). Any aesthetic judgement — the motion-kind homogeneity signal at 3+ distinct variants of the same kind is a carried default `[I — EL-064]`, not a validated threshold.

**Allowed files / contexts.**
- `scripts/lib/live-checks.ts`, `scripts/lib/contrast.ts` (reuse), `scripts/lib/motion-counter.ts`, the drop/mouseup handlers from S43, the Design Health pill.
- TypeScript on Bun. **No `.py` file anywhere in the skill tree.** `await document.fonts.ready` before ANY `getBoundingClientRect`.

**Steps.**
1. Bind the live set to drop and mouseup only; instrument every check invocation with a timestamp and a phase so mid-drag runs are detectable.
2. Scope every check to the touched subtree; a whole-document pass here is a defect by definition.
3. Recompute contrast for every touched pair in both measures; the WCAG 2 ratio decides pass/fail, APCA is recorded as advisory.
4. Implement the target-size check on render for editor chrome as well as content, honouring the four documented exceptions.
5. Make the alt/decorative gate block the placement, not warn after it.
6. Ship the motion-concurrency counter as a visible running total attributed per container, using S54's `costClass`.
7. Wire the anti-slop lint as Tier 2 with a permanent per-element dismiss.
8. Measure the scoped run on the reference fixture and record the latency against the budget.

**Definition of Done.**
- Artifacts: the live check set, the instrumentation trace, the motion counter, the Tier-2 anti-slop wiring, the latency record.
- Validation: the trace shows zero checks mid-drag and zero per-frame; the scoped run is under the latency budget on the reference fixture; a touched pair's contrast is recomputed in both measures; a missing alt blocks the placement; the counter increments visibly on each motion container placed.
- Demo-able increment: drag a low-contrast text block onto the canvas and be blocked at drop, with the pill showing the batched advisories.
- `slice.yaml` mapping — `acceptance_criteria: [A27, SL-S64-1, SL-S64-2, SL-S64-3]`, `verification_method: recompute` (SL-S64-3: `manual-observation`).

## Dev — execution contract

Evidence bundle: (1) summary listing every live check with its scope and tier; (2) traceability FR-231, FR-234 → file:line; (3) structural quality — every check is a pure function over a scoped node set plus measured DOM reads; (4) functional testing — the instrumentation trace, the latency measurement, a contrast fixture, an alt-missing fixture, a motion-counter run; (5) security/compliance — no check writes the document; (6) operational — what happens when a check exceeds its budget on a pathological subtree; (7) self-assessment marking APCA advisory `[U]` and the homogeneity threshold `[I]`.

## QA — zero-trust verification

- **Read the instrumentation trace yourself** and search for any invocation between mousedown and mouseup; one is a rejection.
- **Recompute two contrast pairs yourself** from the rendered values; a logged pass you cannot reproduce is a rejection, and APCA used as the gate is a rejection.
- **Measure the scoped run yourself** on the reference fixture; trust no logged latency.
- **Place an image with no alt or decorative choice** and require the placement blocked, not warned.
- **Place three motion containers** and confirm the counter accumulated turn by turn rather than appearing at LOCK.
- **Reject** if the anti-slop lint blocks anything at this layer, or if its dismissal is not permanent per element.

## Dev Learnings

_Not Done until filled. Required: which check dominated the latency budget, and whether font readiness had to be awaited before every measurement._

## QA Learnings

_Not Done until filled. Required: whether any check quietly widened its scope beyond the touched subtree under real drags._
