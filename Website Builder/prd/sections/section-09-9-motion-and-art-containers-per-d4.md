## 9. Motion and art containers (per D4)

**D4 is settled: motion is an ordinary design-system item, and animated pieces live in the same draggable containers as artwork.** No parallel motion subsystem. The editor manipulates an animated container exactly as it manipulates an art container.

### 9.1 The container contract (one contract, both kinds)

Every art/motion container implements:

```
{
  boxSizing, aspectPolicy (from the named ratio set), anchor, overflow, mask,
  schemeAware: bool, motionCapable: bool, reducedMotionPoster,
  focalPoint: {x, y}, altText | decorative: true, licenseRef,
  trigger, viewportThreshold, tokenRefs[]
}
```

Three rules make this work:

1. **Explicit `aspect-ratio` (or min-block-size from the ratio scale) is mandatory**, so the grid row is reserved before the asset or animation initialises. Otherwise entrance animations and late-loading media produce layout shift, which the CLS gate catches too late.
2. **Animation may only touch `transform`, `opacity`, `filter`** inside the container. It may **never** change the container's grid placement, width, or height. This makes the editor's handling of a WebGL canvas byte-identical to its handling of a JPEG — which is exactly what D4 asks for.
3. **Trigger + viewport-threshold fields, not container TYPE, determine which animation kind a container performs.** The same generic container becomes a hero entrance (trigger: page-load), a scroll reveal (trigger: viewport-enter at ~20%), or a hover micro-reaction (trigger: pointerenter). This is why the container inventory is small and the animation-kind inventory is where the variants live.

### 9.2 Container kinds — 11 structural types

| Container | Structural variants | Priority | Notes |
|---|---|---|---|
| Still-image container | **4** | v1 | contain, cover, bleed, masked. Visual identity lives in the Image Figure component that skins it |
| CSS/GSAP-driven DOM container (generic) | **8** | v1 | The highest-reuse container; hosts most animation kinds interchangeably, so it needs the widest generic preset bank |
| Decorative background layer | **10** | v1 | **Tier A, user-named.** Covers the largest pixel area of any component; still or animated in the same slot per D4 |
| Marquee / ticker | **6** | v1 | constant, pause-on-hover, speed-on-scroll, reverse-on-scroll, dual-counter-row, tilted. **WCAG 2.2.2 pause/hide is mandatory** |
| Reveal-on-enter | **8** | v1 | fade, rise, mask-wipe, clip-expand, scale, blur-in, stagger-children, split-line. **The most-used motion primitive on the whole site** |
| Global cursor-effect layer | **5** | v1 | A page-level singleton, not per-instance. Desktop-only; **must disable on coarse pointers** |
| Animated sprite / frame-sequence | **3** | v2 | autoplay-loop, play-on-enter, scroll-scrubbed. **Asset-supply gap — see §9.5** |
| Video-loop container | **3** | v2 | autoplay-loop, play-on-enter, hover-play. Muted is browser law, not style. **Asset-supply gap** |
| Vector animation (dotLottie / Rive) | **3** | v2 | loop, play-on-enter, interactive/state-machine |
| Scroll-driven pinned/scrubbed sequence | **4** | v2 | element-enters-view, element-pins, container-scroll, whole-page. **The one drag-fragile container — see §9.4** |
| SVG shape / mask container | **4** | v2 | clip, mask, overlay, seam |
| Canvas / WebGL slot | **3** | v3 | inline, section-background, full-viewport-fixed. **House-curated, not model-improvised** |
| Particle / ambient canvas layer | **5** | v3 | **Only ONE such layer should ever run per page** — continuous main-thread + GPU cost stacks additively |
| Kinetic type container | **8** | v2 | per-char stagger, mask-wipe, variable-axis, path-warp, marquee-type, scramble, 3D-extrude, cursor-repel. **Must declare that accessible text remains in the DOM unsplit** |
| Cursor-reactive container | **5** | v2 | parallax, tilt, magnetic, spotlight, distortion. All five no-op on touch and under reduced-motion |
| Sticky / pin container | **4** | v2 | Purely mechanical substrate |

### 9.3 Animation kinds — where the variants live

| Kind | Variants | Priority | Rationale |
|---|---|---|---|
| Hover micro-reactions | **10** | v1 | **The highest-FREQUENCY animation kind** — fires hundreds of times per session. lift+shadow, magnetic, underline-draw, fill-sweep, icon-morph, scale-pulse, border-trace, colour-shift, tilt-3d, cursor-glow. Each cheap to build and verify. **Must have a touch equivalent** — a hover-only affordance is a usability defect, not a stylistic choice |
| Hero entrance | **8** | v1 | The most-seen single moment per visit. fade-up, split-text, staggered cascade, mask-wipe, scale-in, parallax-layered, clip-path, typewriter |
| Section reveal choreography | **10** | v1 | **Tier A.** Choreography — the ORDER things arrive in — is what separates directed motion from every-element-fades-up, the single most recognisable AI-generated motion signature |
| Text reveal / kinetics | **10** | v1 | Tier A. GSAP SplitText became free April 2025 with AI-generated code explicitly permitted, so this is buildable without licence risk. **All 10 must preserve a single accessible text node** |
| Scroll reveal | **6** offered / **1–2** deployed | v1 | **Catalogue breadth ≠ deployment restraint.** Mixing multiple reveal styles on one page reads as inconsistent — itself an anti-slop tell. The editor flags 3+ distinct reveals as a soft warning |
| Marquee | **6** | v1 | Cheap (pure CSS transform loop), commonly reused |
| Loading states | **6** | v1 | skeleton shimmer, brand-mark pulse, progress bar, custom spinner, placeholder-fade, staged-reveal. **Over-designing fights the purpose** |
| Custom cursor | **10** | v1 | Tier A, user-named. Untitled UI ships cursors as a foundation component, confirming they belong in a design system |
| Background ambient motion | **8** | v1 | User-named. Mirrors the decorative background layer's presets; the heaviest sub-variant (particle field) is v3-gated |
| Parallax | **5** | v2 | Accessibility- and performance-sensitive, so below the 10 default. **35.4% of adults 40+ have vestibular dysfunction** |
| Sticky/pinned scroll sequence | **4** | v2 | Each architecturally distinct and expensive to verify |
| Page transitions | **6** | v2 | Feasibility-grounded, architecture-dependent |
| Signature moment | **2–3 concept candidates** | v1 | **NOT a swap catalogue.** Award-tier winners have exactly one, and treating identity-carrying choices as generic catalogue picks is the root mechanism of homogenisation. Generated as bespoke concepts tied to the brand narrative at Step 2, chosen at Step 4, handled under Step 6's custom-component allowance. **A lint flags a second one** |
| Smooth-scroll behaviour | **4** | v1 | native, lightly damped, Lenis-wrapped, per-section snap. Lenis wraps native scroll so accessibility survives; **ScrollSmoother is anti-recommended** because it restructures the DOM |
| Parallax depth rules | **5** | v2 | Picked once and applied everywhere, or layers fight each other |

### 9.4 The pinned/scrubbed exception (important)

Most containers re-target cleanly under drag because their trigger is viewport-intersection-based and their transform origin is relative to their own bounding box. **A scroll-driven pinned/scrubbed sequence is different**: its timeline is a function of absolute scroll distance travelled while pinned, which depends on its position in document flow and the room its parent has to scroll through. Dragging it into a narrow column or a section with different surrounding height silently breaks the composition — pin without room to scroll, or a scrub that completes too fast.

**Rule:** the D2 free-position escape hatch is **disabled by default** for this container kind. It is restricted to anchor reordering (move between sections), and forcing free-position requires an explicit confirmation. Re-anchoring triggers a scroll-length resimulation before the preview is shown accurate.

### 9.5 Format and platform rules

| Decision | Rule | Evidence |
|---|---|---|
| Vector animation format | **dotLottie by default** (60KB runtime, ZIP-compressed JSON). **Rive only when a state machine or input-reactive behaviour is required** (200KB WASM runtime, but 50–80% smaller payloads). Threshold: >6 vector animations OR any state-machine requirement ⇒ Rive. **Neither runtime loads for a hover effect** — CSS/GSAP covers micro-interactions | **[V — rive.app blog, unicornicons, pkgpulse 2026; medium confidence on exact figures]** |
| Scroll-driven animation | **Native CSS `animation-timeline: scroll()/view()` as the primary path** (zero main-thread JS — directly serves the finding that main-thread work is the real performance axis), **GSAP ScrollTrigger as the `@supports`-not fallback**. Chrome/Edge 115+, Safari 18+, Firefox behind a flag; ~84% global as of mid-2026, Baseline-blocked pending Firefox. **The fallback must be real and tested, not assumed** | **[V — MDN, web-features-explorer, caniuse]** |
| Page transitions | **CSS `::view-transition-group/-old/-new` choreographies**, progressive-enhancement-safe by construction. Same-document VT is Baseline Newly Available (Chrome 111+, Firefox 133+, Safari 18+); **cross-document ships in Chrome 126+ and Safari 18.2+ but is still absent in Firefox as of mid-2026** — degrade to instant navigation, never a JS router hack that breaks the back button | **[V]** |
| Motion lint | UI interactions ≤300ms, never >500ms (Primer's shipped rule). Compositor-only properties (`transform`/`opacity`/`filter`); animating `width`/`height`/`top`/`left`/`margin` forces layout+paint every frame | **[V — primer motion.json5]** |
| Concurrency caps | Max 1 WebGL slot, max 1 particle/ambient layer, max 2 autoplay video loops, max 2–3 pinned sequences per page. Unlimited transform/opacity-only CSS reveals | **[I]** |
| Asset-supply gap | **Video-loop and image-sequence containers cannot be populated by the claude.ai leg.** Either the user supplies footage/frames, or they route to an external provider with its own licence manifest, or they are out of scope for v1. The PRD must state which — see §17-R1 | **[V — the generation-surface limitation]** |

### 9.6 The motion-editing contradiction (stated plainly, mitigated partially)

A draggable container must be measurable. `getBoundingClientRect()` on a GSAP-transformed element returns the **animated** position, not the layout position, so drag maths is wrong mid-tween. Lenis lerps `scrollTop` every frame, so scroll measurement is unreliable while it runs. Every real implementation therefore disables animation in edit mode — which is also what the prior report's capture protocol mandates for screenshots.

**Consequence:** the user arranges an animated hero with all motion frozen, locks, sees the real motion for the first time, finds it wrong, unlocks, and the motion turns off again. **They cannot debug the thing they are trying to fix, in the tool built to fix it.**

**Partial mitigations (a mode toggle, not a fix):**

- **PREVIEW MOTION** — re-enables Lenis + ScrollTrigger + all tweens and **disables all editing**. The page becomes the locked site in place, one keypress away.
- **Per-container scrub slider** setting the tween to normalised progress 0→1, so start/mid/end poses are visible statically.
- **Trigger-point markers** rendered in the overlay showing where the scroll trigger fires.

**There is no known mitigation for judging motion FEEL while editing.** The prior report's Data Gap 2 states motion verification is unvalidated end-to-end anywhere in the industry; the human-in-the-loop design does not change that, it moves the unsolved problem from an AI judge to a human who also has to be in preview mode to see it. This is stated in §17 as a risk with no mitigation.

---

