# S29-editor-shell-and-overlay — Three-pane editor shell with the out-of-iframe overlay and same-origin preview

| Field | Value |
|---|---|
| Epic / Story | E8 / ST-09 |
| Type · MoSCoW · Size | build · MUST · L `[I]` |
| Phase / Demo | Phase 2 / — |
| Depends on | S25-pure-renderer-and-resolution-policy · S08-server-ts-port |
| Requirements | FR-080, FR-082, FR-120 |
| Acceptance criteria | SL-S29-1 · SL-S29-2 |
| CQ / evidence | CQ3 · CQ17 |
| Note | **Invariant I4** — preview isolation is a **requirement, not a mechanism**: a capture of the preview contains zero editor chrome. **Gotcha 12** — an auto-height iframe makes `100vh` resolve to the iframe height, so a hero gets approved at a height no device has |

## PM — slice definition

**Objective.** Stand up the editing surface with zero DOM injection for hit-testing and a preview that can be captured without chrome.

**In scope.** The three-pane shell; hit-testing via `data-wb-node` on elements that **already exist**, plus a **single sibling overlay `<div>` outside the page's layout root**; the selection overlay and handles drawn **outside the iframe** with `pointer-events: none`; selection reachable by canvas click and by breadcrumb; the preview as a **same-origin iframe** — a scaled `<div>` cannot evaluate media queries; device heights **pinned** (390×844, 768×1024, 1280×800, 1440×900) whenever the page contains any `vh`/`svh`/`dvh` rule, with the **measured** iframe height asserted rather than assumed; the SSE connection to `GET /events` with `Last-Event-ID` reconnect; the editor **proposes ops only** and writes nothing.

**Out of scope.** The Navigator tree — the third selection route (S30). Typed ops, autosave and undo (S31). The gridline overlay (S41). The eight security controls (S37); this slice inherits S08's loopback bind and must say so.

**Assumption.** The sources fix the pane **count** at three but do not name the assignment; this slice ships Navigator rail (left), preview + overlay (centre) and inspector (right), and records that layout as the reference for later slices `[I]`, low confidence.

**Allowed files / contexts.**
- `app/editor/**`, `app/editor/overlay.ts`, `app/editor/preview-frame.ts`, `scripts/lib/routes.ts` (static + SSE wiring only).

**Steps.**
1. Build the shell with the preview mounted as a same-origin iframe; never a scaled `<div>`.
2. Implement hit-testing by reading `data-wb-node` from existing elements; **inject nothing** into the page tree.
3. Draw selection, handles and breadcrumb in one sibling overlay outside the page's layout root, with `pointer-events: none`.
4. Detect any `vh`/`svh`/`dvh` rule on the page and pin the iframe to the device height for the active switcher entry.
5. **Measure** the iframe height after layout and assert it equals the pinned height; a mismatch is an error, not a warning.
6. Wire SSE and prove the shell survives a preview-process restart with no state loss (invariant I5 — the pending queue is server-side).

**Definition of Done.**
- Artifacts: the shell, the overlay module, the preview frame module, the height-assertion transcript, a capture of the preview.
- Validation: a grep proves no injected hit-test node; the overlay is a sibling outside the layout root; the measured height equals the pinned height on a `vh` fixture; a preview capture contains zero editor chrome; a preview restart loses nothing.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S29-1, SL-S29-2]`, `verification_method: grep-assert` (SL-S29-2: `recompute`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-080, FR-082, FR-120 → file:line; (3) structural quality — the overlay never touches the iframe document; state that as an enforced boundary with the file that enforces it; (4) functional testing — the `vh` fixture with measured heights at all four devices, the capture, the restart test; (5) security/compliance — which of the eight controls are **not** yet implemented and that S37 owns them; (6) operational — what the user sees when the preview process dies mid-edit; (7) self-assessment.

## QA — zero-trust verification

- **Measure the iframe height yourself** on a `100vh` fixture at 390 and at 1280; a hero approved against an auto-height iframe is a rejection.
- **Capture the preview yourself** and inspect the image for chrome pixels; a claim of isolation is not evidence.
- **Grep the iframe document** for any element created by the editor, and confirm the overlay node's parent is outside the page's layout root.
- **Click through selection yourself** on a zero-height wrapper and on an element fully covered by a background art container, and record what canvas clicking could **not** reach — that list is S30's input.
- **Reject** if `pointer-events: none` is absent from any overlay layer, or if hit-testing depends on a node the editor added.

## Dev Learnings

_Not Done until filled. Required: what the out-of-iframe overlay made harder than an injected approach would have, and whether the measured-height assertion ever disagreed with the pinned value._

## QA Learnings

_Not Done until filled. Required: the list of things canvas clicking provably could not reach, recorded verbatim for S30._
