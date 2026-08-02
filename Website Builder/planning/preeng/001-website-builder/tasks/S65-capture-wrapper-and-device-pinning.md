# S65-capture-wrapper-and-device-pinning — Capture wrapper with the inherited wait recipe and device-height pinning

| Field | Value |
|---|---|
| Epic / Story | E17 / ST-21 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 5 / — |
| Depends on | S63-gates-ts-verdicts-and-tiers |
| Requirements | FR-235, FR-236 |
| Acceptance criteria | SL-S65-1 · SL-S65-2 · SL-S65-3 · SL-S65-4 |
| CQ / evidence | CQ17 |
| Note | **A capture is evidence or it is decoration.** A tall full-page screenshot cannot judge a viewport-height layout, and the failure is invisible — the image looks fine |

## PM — slice definition

**Objective.** Produce captures that are valid evidence, especially for viewport-height layouts, with **zero npm dependencies**.

**In scope.** `capture.ts` on Bun driving plain Chrome CLI headless (`--headless=new --disable-gpu --no-sandbox --hide-scrollbars --virtual-time-budget=4000 --screenshot=<out> <url>`) and asserting `[ -s "$out" ]`; the inherited wait recipe re-expressed in TypeScript — **navigate rather than set content**, network-idle with a load fallback, strip `loading="lazy"`, `document.fonts.ready` **plus** per-image `decode()`, a 500ms deferred-CSS settle; device pinning of **both** the window **and** the preview frame with the **measured** frame height asserted; a `contentReviewOnly: true` label on every full-page tall capture; the breakpoint × light/dark × full/reduced-motion matrix driver used by the evidence bundle.

**Out of scope.** Scripted interaction capture (if ever needed: `bun add playwright` **inside the skill**, never via an evictable npx cache). Purity gate 4's screenshot diff itself (S67 consumes this wrapper). Any judgement of what a capture shows — machines do not judge aesthetics.

**Allowed files / contexts.**
- `scripts/lib/capture.ts`, `scripts/lib/wait-recipe.ts`, `scripts/capture-matrix.ts`, `07-lock/screenshots/` (write).
- **No `.py` file anywhere.** No package added to the live dependency tree by this slice.

**Steps.**
1. Wrap the browser command line; never shell-interpolate an unquoted path; assert the output file is non-empty and fail loudly if it is not.
2. Implement the wait recipe as an ordered, individually testable function chain; each step logs whether it fired or fell back.
3. Strip `loading="lazy"` before capture — a lazy image below the fold captures blank in headless.
4. `await document.fonts.ready` **before any `getBoundingClientRect`**, in the capture path *and* in the editor path; add the assertion to `selftest.ts` so a later measurement cannot skip it.
5. For any viewport-height judgement: set the window size, set the preview frame size, then **measure** the frame and assert the measured height equals the requested device height. A requested config that was silently not honoured is a failure, not a warning.
6. Label full-page tall captures `contentReviewOnly` in the capture manifest; the evidence bundler refuses them as hero-framing evidence.

**Definition of Done.**
- Artifacts: `capture.ts`, `wait-recipe.ts`, the capture manifest with per-shot `{breakpoint, scheme, motion, devicePinned, measuredFrameHeight}`, one full matrix run.
- Validation: `npm ls` / lockfile hash unchanged; a deliberately mis-sized frame fails the height assertion; a lazy-image fixture captures non-blank.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S65-1, SL-S65-2, SL-S65-3, SL-S65-4]`, `verification_method: exit-code` (SL-S65-2/4: `grep-assert`; SL-S65-3: `recompute`).

## Dev — execution contract

There is **no `timeout`/`gtimeout` binary** on this machine — it yields *empty output*, not an error — so long captures run under `run_in_background` plus polling, never under a timeout wrapper. Evidence bundle: (1) summary with the measured frame heights; (2) traceability FR-235, FR-236 → file:line per recipe step; (3) structural quality — the recipe is pure functions callable without a browser except the final drive; (4) functional testing — the matrix run plus the two negative fixtures; (5) security/compliance — no network fetch beyond the local URL; (6) operational — how to add a device to the pin table; (7) self-assessment.

## QA — zero-trust verification

- **Run the capture yourself** and confirm the output file is non-empty by your own `stat`; a logged byte count is not evidence.
- **Recompute the measured frame height** from your own capture and compare it to the recorded value — a mismatch is a rejection, because this is the exact failure the slice exists to catch.
- **Grep the source** for `getBoundingClientRect` and require an awaited `document.fonts.ready` on every path that reaches it.
- **Check the lockfile hash** before and after; a new dependency is a rejection (SL-S65-1 is a zero-dependency claim).
- **Reject** if any full-page tall capture is unlabelled, or if a labelled one is used as framing evidence.

## Dev Learnings

_Not Done until filled. Required: which wait-recipe step actually mattered on this substrate, and whether the frame ever silently ignored the requested size._

## QA Learnings

_Not Done until filled. Required: whether an independently taken capture reproduced the recorded height, and what a stale font cache did to the first run._
