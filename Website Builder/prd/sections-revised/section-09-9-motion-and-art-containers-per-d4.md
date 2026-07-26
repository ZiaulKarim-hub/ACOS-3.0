## 9. Motion and art containers (per D4)

**D4 is settled: motion is an ordinary design-system item, and animated pieces live in the same draggable containers as artwork.** No parallel motion subsystem. The editor manipulates an animated container exactly as it manipulates an art container.

*Revision note (this pass): the earlier draft of this section left the swappable "motion variant" unit undefined, understated the container-kind count, left the video/sprite asset-supply decision unresolved, and understated the touch/keyboard story for hover- and cursor-driven items. All four are closed below. Nothing in D1–D4 or in the settled 8-step vision is reopened.*

### 9.1 The container contract (one contract, both kinds)

Every art/motion container implements:

```
{
  boxSizing, aspectPolicy (from the named ratio set), anchor, overflow, mask,
  schemeAware: bool, motionCapable: bool, reducedMotionPoster,
  reducedMotionVariantRef,               // NEW — see rule 4 below
  focalPoint: {x, y}, altText | decorative: true, licenseRef,
  trigger, viewportThreshold,            // NEW — both now typed, see rule 3
  source: {                              // NEW — see rule 5
    kind: 'raster' | 'vector-lottie' | 'vector-rive' | 'video'
        | 'sprite-sequence' | 'svg' | 'canvas-program' | 'none',
    ref,          // asset id — MUST resolve against assets/manifest.json
    poster        // asset id, optional — distinct from reducedMotionPoster
  },
  playback: {                            // NEW — see rule 6
    autoplay: bool, muted: bool, loop: bool,
    iterationCount: number | 'infinite'
  },
  costClass: 'free' | 'cheap' | 'heavy' | 'gpu',   // NEW — see rule 7
  tokenRefs[]
}
```

Seven rules make this work:

1. **Explicit `aspect-ratio` (or min-block-size from the ratio scale) is mandatory**, so the grid row is reserved before the asset or animation initialises. Otherwise entrance animations and late-loading media produce layout shift, which the CLS gate catches too late.
2. **Animation may only touch `transform`, `opacity`, `filter`** inside the container. It may **never** change the container's grid placement, width, or height. This makes the editor's handling of a WebGL canvas byte-identical to its handling of a JPEG — which is exactly what D4 asks for.
3. **Trigger + viewport-threshold fields, not container TYPE, determine which animation kind a container performs.** `trigger` is a closed enum — **`page-load`, `viewport-enter`, `viewport-scrub`, `pointerenter`, `click`, `always`** — no other value is legal. `viewportThreshold` is a fraction in `[0, 1]`, meaningful only for `viewport-enter` (default **0.2**, i.e. the "~20%" figure used elsewhere in this section is now the stated default, not a stray prose number) and ignored for every other trigger. `viewport-scrub` does not use a single threshold at all — its progress is driven by the pinned/scrubbed sequence's own scroll-range mechanism, defined in §9.4. `page-load`, `click`, and `always` fire without a threshold. The same generic container becomes a hero entrance (trigger: `page-load`), a scroll reveal (trigger: `viewport-enter` at its threshold), or a hover micro-reaction (trigger: `pointerenter`). This is why the container inventory is small and the animation-kind inventory is where the variants live.
4. **`reducedMotionVariantRef` is mandatory whenever `motionCapable: true`.** It is a node/asset id pointing at the tagged reduced-motion treatment in the catalogue — this is the field §10.6's v1 check ("confirm the placed item's catalog includes a tagged reduced variant") actually reads. `reducedMotionPoster` remains a separate, narrower field: a still frame shown only for `source.kind` values that have no meaningful reduced-motion *animation* at all (e.g. a video-loop reduced to a poster frame). A container may carry either or both, but `motionCapable: true` without `reducedMotionVariantRef` fails validation.
5. **`source` is what the generator validates against the asset allowlist.** Every reference resolves against `assets/manifest.json` (§12.2); a container with no distinct asset of its own — e.g. a CSS/GSAP-driven DOM container animating existing child content rather than an image or file — sets `source.kind: 'none'` and omits `ref`. This is also the field the §9.5 asset-supply decision below is written against.
6. **`playback` governs autoplaying/looping media.** `muted` **must** be `true` whenever `source.kind: 'video'` and `autoplay: true` — "muted is browser law, not style" (unchanged from the original text, now enforced as a field-level constraint rather than a prose aside). `iterationCount` is `'infinite'` for true loops and a finite number for anything that plays out and stops (e.g. a hero entrance).
7. **`costClass` is what §9.5's concurrency caps are computed against.** It is assigned per container *kind* in §9.2's new Axis/Cost column, not authored per instance — an instance inherits its kind's class. `gpu`-class containers (Canvas/WebGL, Particle/ambient) are the ones the "max 1 WebGL slot, max 1 particle layer" caps in §9.5 enforce; `heavy`-class containers (video-loop, sprite/frame-sequence, pinned/scrubbed) are what the "max 2 autoplay video loops, max 2–3 pinned sequences" caps enforce.

#### 9.1.1 The motion-variant model — what the component bar actually swaps *(new — closes a blocking gap)*

The layout-node example in §12.3 shows two independent fields on an `ArtContainer` node: `variant` (e.g. `"background-scene@07"`) and `props.motion` (e.g. `"entrance.mask-wipe@03"`). Neither §9.2 nor §9.3, as originally written, stated which of these each section's variant *count* populates, or what the component bar shows. This subsection is the missing definition.

**The rule:**

- **`variant` always selects the container's structural/rendering implementation** — the §9.2 count for that container kind. This is "how the container is built and skinned," and it is present on every container, motion-capable or not.
- **`props.motion`, present only when `motionCapable: true`, selects the choreography/behaviour** — a token of the form `<kind>.<slug>@<version>` drawn from a §9.3 animation kind. Combined with `trigger` (§9.1 rule 3), it determines what plays and when.

**Not every container kind needs both fields independently.** Cross-checking §9.2's per-kind counts against §9.3's per-kind counts surfaces two genuinely different situations, and the original draft did not distinguish them. Every row in the revised §9.2 table now carries an explicit **Axis type**:

| Axis type | Meaning | Component bar behaviour |
|---|---|---|
| **Dual** | `variant` (structural skin) and `props.motion` (behaviour, drawn from one or more compatible §9.3 kinds) are genuinely independent choices that compose | Two tabs: **Style** (lists the §9.2 count) and **Motion** (lists the compatible §9.3 kind(s)' variants). Selecting in one tab never changes the other. |
| **Single** | The container kind's own §9.2 variant list *is* its complete motion catalogue — there is no separate `props.motion` token, or the token namespace is identical to `variant` | One tab: **Style**, labelled as such but understood to set both look and behaviour together, since they were never separable for this kind. |
| **Static** | The container kind is not independently motion-capable (a purely mechanical substrate, or house-curated content that defines its own motion internally) | One tab: **Style**. No **Motion** tab is shown; `motionCapable` defaults to `false` for these unless the hosted content declares otherwise (e.g. Sticky/pin hosting a Sticky/pinned-scroll-sequence timeline authored on a *child* node). |

**Do the §9.2 and §9.3 counts multiply? — answered explicitly, per axis type:**

- **For Dual-axis kinds, yes, in *state-space* terms only.** The number of *reachable look+behaviour combinations* for one container instance is `(§9.2 count) × (sum of variants across its compatible §9.3 kinds)`. This is **never** rendered as one flattened cross-product list in the UI (an 8-structural × 47-eligible-motion container would be a 376-row list, which is unusable) — the bar always presents Style and Motion as two separate, tabbed pickers, and the user makes two independent choices that compose.
- **For Single-axis kinds, no.** Picking the container's one `variant` fully determines both look and behaviour; there is nothing to multiply against.
- **For Static kinds, the question does not apply.**

**Per-kind disposition** (feeds the Axis-type column added to §9.2's table):

| Container kind | Axis type | `props.motion`-eligible §9.3 kind(s) | Reconciliation note |
|---|---|---|---|
| Still-image container | Dual | Hero entrance, Reveal-on-enter (via Section reveal choreography / Scroll reveal), Parallax | `variant` = contain/cover/bleed/masked crop treatment (the only row in §9.2 whose names were already given). `motionCapable` defaults `false` — a still image is not required to move. |
| CSS/GSAP-driven DOM container (generic) | Dual | Hero entrance, Section reveal choreography, Text reveal/kinetics, Scroll reveal, Hover micro-reactions, Loading states, Background ambient motion, Page transitions, Signature moment | Highest-reuse container; its 8 structural variants are generic wrapper shapes, not enumerated by name in this pass (they are derived per direction, not fixed catalogue names — stating specific names here would be fabrication). |
| Decorative background layer | Dual | Background ambient motion, Parallax, Hero entrance (as backdrop), Reveal-on-enter | Tier A, user-named. |
| Marquee / ticker | Single | — (identical list) | The container's 6 structural variants (constant, pause-on-hover, speed-on-scroll, reverse-on-scroll, dual-counter-row, tilted) **are** the "Marquee" animation kind's 6 variants in §9.3, restated once per table for readability. This is the earlier draft's clearest accidental double-count; there is exactly one list of 6, not two lists of 6. |
| Reveal-on-enter | Dual (tightly coupled) | Section reveal choreography, Scroll reveal | `variant` picks the base reveal treatment (fade, rise, mask-wipe, clip-expand, scale, blur-in, stagger-children, split-line); `props.motion` (when set to a Section-reveal-choreography or Scroll-reveal token) picks the ORDER/timing multiple reveal-on-enter instances play in relative to each other. The two are coupled — a choreography token is meaningless without at least one placed reveal-on-enter instance to sequence. |
| Global cursor-effect layer | Dual, AND-composed | Custom cursor (exclusively) | **[I — new synthesis, not independently confirmed]** The 5 structural variants are rendering *mechanisms* (e.g. dot-follow / outline-follow / blend-mode / trail / magnetic-snap — mechanism names are inferred, not sourced); the 10 Custom-cursor variants in §9.3 are behaviour *presets* layered on the chosen mechanism. Both fields are required together when `motionCapable: true`; this is the one kind where Style and Motion are non-optional together rather than independently optional. |
| Animated sprite / frame-sequence | Single | — | `variant` (autoplay-loop / play-on-enter / scroll-scrubbed) fully determines playback. **Asset-supply gap — see §9.5, decided below.** |
| Video-loop container | Single | — | `variant` (autoplay-loop / play-on-enter / hover-play) fully determines playback. Muted is enforced via `playback.muted` (§9.1 rule 6). **Asset-supply gap — decided below.** |
| Vector animation (dotLottie / Rive) | Single | — | `variant` (loop / play-on-enter / interactive-state-machine). When the state-machine variant is chosen, its input trigger may itself resemble a hover micro-reaction, but that binding is authored *inside* the Lottie/Rive file, not exposed as a separate `props.motion` token. |
| Scroll-driven pinned/scrubbed sequence | Single | — (matches "Sticky/pinned scroll sequence" 1:1, 4=4) | See §9.4 for the resimulation rule governing re-anchoring. |
| SVG shape / mask container | Dual | Reveal-on-enter (mask/clip variants), Text reveal/kinetics (path-warp) | `variant` = clip/mask/overlay/seam structural treatment. |
| Canvas / WebGL slot | Single | — | House-curated per the original note; the WebGL program itself defines its motion, so there is no separate catalogue to swap. |
| Particle / ambient canvas layer | Single | — | Same reasoning as Canvas/WebGL; its 5 variants **are** its motion presets. |
| Kinetic type container | Single, with an open mapping question | — | **OPEN QUESTION — no known mitigation in this pass.** The container's 8 named variants (per-char stagger, mask-wipe, variable-axis, path-warp, marquee-type, scramble, 3D-extrude, cursor-repel) plainly overlap with the "Text reveal / kinetics" animation kind's separately-counted 10 variants in §9.3, but no source material establishes whether the kind-level 10 is a superset, a recombination, or an independent list. This requires a build-time reconciliation pass before the component bar can be implemented for this kind; recorded here rather than silently resolved. |
| Cursor-reactive container | Single, with a partial-overlap open question | — | **OPEN QUESTION — no known mitigation in this pass.** Its 5 variants (parallax, tilt, magnetic, spotlight, distortion) partially overlap named entries in Hover micro-reactions ("magnetic," "tilt-3d," "cursor-glow"); the overlap is not reconciled by the source material. |
| Sticky / pin container | Static | Sticky/pinned scroll sequence (hosted, on a child node) | Purely mechanical substrate — matches its original note unchanged. |

This table is additive to, not a replacement for, §9.2's own table below, which now carries the Axis-type column inline for at-a-glance reference.

### 9.2 Container kinds — 16 structural types

*(Corrected: the earlier heading said "11 structural types" while its own table listed 16 rows, with no note explaining the discrepancy. There is no v1-only subset that totals 11 either — the accurate split by Priority is **6 v1 / 8 v2 / 2 v3 = 16**. The heading now matches the table it introduces.)*

| Container | Structural variants | Priority | Axis type | Cost class | Notes |
|---|---|---|---|---|---|
| Still-image container | **4** | v1 | Dual | free | contain, cover, bleed, masked. Visual identity lives in the Image Figure component that skins it |
| CSS/GSAP-driven DOM container (generic) | **8** | v1 | Dual | cheap | The highest-reuse container; hosts most animation kinds interchangeably, so it needs the widest generic preset bank |
| Decorative background layer | **10** | v1 | Dual | cheap (heavy if its Background-ambient-motion `props.motion` selects a particle sub-variant — see §9.3's note) | **Tier A, user-named.** Covers the largest pixel area of any component; still or animated in the same slot per D4 |
| Marquee / ticker | **6** | v1 | Single | cheap | constant, pause-on-hover, speed-on-scroll, reverse-on-scroll, dual-counter-row, tilted. **WCAG 2.2.2 pause/hide is mandatory**; `pause-on-hover`'s touch counterpart is a visible tap-to-pause control (§9.3.1) |
| Reveal-on-enter | **8** | v1 | Dual (coupled) | cheap | fade, rise, mask-wipe, clip-expand, scale, blur-in, stagger-children, split-line. **The most-used motion primitive on the whole site** |
| Global cursor-effect layer | **5** | v1 | Dual, AND-composed | cheap | A page-level singleton, not per-instance. Desktop-only; **must disable on coarse pointers** — see §9.3.1 for the required non-cursor touch signature |
| Animated sprite / frame-sequence | **3** | v2 | Single | heavy | autoplay-loop, play-on-enter, scroll-scrubbed. **Asset-supply gap — DECIDED, see §9.5** |
| Video-loop container | **3** | v2 | Single | heavy | autoplay-loop, play-on-enter, hover-play. Muted is browser law, not style. **Asset-supply gap — DECIDED, see §9.5** |
| Vector animation (dotLottie / Rive) | **3** | v2 | Single | cheap (dotLottie) / heavy (Rive, per §9.5's payload note) | loop, play-on-enter, interactive/state-machine |
| Scroll-driven pinned/scrubbed sequence | **4** | v2 | Single | heavy | element-enters-view, element-pins, container-scroll, whole-page. **The one drag-fragile container — see §9.4** |
| SVG shape / mask container | **4** | v2 | Dual | cheap | clip, mask, overlay, seam |
| Canvas / WebGL slot | **3** | v3 | Single | gpu | inline, section-background, full-viewport-fixed. **House-curated, not model-improvised** |
| Particle / ambient canvas layer | **5** | v3 | Single | gpu | **Only ONE such layer should ever run per page** — continuous main-thread + GPU cost stacks additively |
| Kinetic type container | **8** | v2 | Single (open mapping question, §9.1.1) | cheap | per-char stagger, mask-wipe, variable-axis, path-warp, marquee-type, scramble, 3D-extrude, cursor-repel. **Must declare that accessible text remains in the DOM unsplit** |
| Cursor-reactive container | **5** | v2 | Single (open overlap question, §9.1.1) | cheap | parallax, tilt, magnetic, spotlight, distortion. All five no-op on touch and under reduced-motion — see §9.3.1 for the required substitute |
| Sticky / pin container | **4** | v2 | Static | free | Purely mechanical substrate |

**Cost-class ↔ concurrency-cap linkage (new, closes a §9.5 traceability gap):** the `gpu` row above (Canvas/WebGL, Particle/ambient) is exactly what §9.5's "max 1 WebGL slot, max 1 particle layer" caps enforce; the `heavy` row (sprite, video-loop, pinned/scrubbed, Rive-mode vector) is exactly what "max 2 autoplay video loops, max 2–3 pinned sequences" enforces. A page-level validator sums `costClass` across placed instances and blocks placement past the cap rather than warning after the fact.

### 9.3 Animation kinds — where the variants live

| Kind | Variants | Priority | Touch/keyboard equivalent | Rationale |
|---|---|---|---|---|
| Hover micro-reactions | **10** | v1 | **See §9.3.1 — per-variant table, not "n/a."** | **The highest-FREQUENCY animation kind** — fires hundreds of times per session. lift+shadow, magnetic, underline-draw, fill-sweep, icon-morph, scale-pulse, border-trace, colour-shift, tilt-3d, cursor-glow. Each cheap to build and verify. **Must have a touch equivalent** — a hover-only affordance is a usability defect, not a stylistic choice |
| Hero entrance | **8** | v1 | n/a — `page-load` trigger, device-independent | The most-seen single moment per visit. fade-up, split-text, staggered cascade, mask-wipe, scale-in, parallax-layered, clip-path, typewriter |
| Section reveal choreography | **10** | v1 | n/a — `viewport-enter` trigger, device-independent | **Tier A.** Choreography — the ORDER things arrive in — is what separates directed motion from every-element-fades-up, the single most recognisable AI-generated motion signature |
| Text reveal / kinetics | **10** | v1 | n/a | Tier A. GSAP SplitText became free April 2025 with AI-generated code explicitly permitted, so this is buildable without licence risk. **All 10 must preserve a single accessible text node**. See §9.1.1's open mapping question against the Kinetic type container's 8 |
| Scroll reveal | **6** offered / **1–2** deployed | v1 | n/a | **Catalogue breadth ≠ deployment restraint.** Mixing multiple reveal styles on one page reads as inconsistent — itself an anti-slop tell. The editor flags 3+ distinct reveals as a soft warning |
| Marquee | **6** | v1 | Tap-to-pause control for the `pause-on-hover` variant — WCAG 2.2.2 | Cheap (pure CSS transform loop), commonly reused. **Same 6-item list as the Marquee/ticker container's structural variants — see §9.1.1, this is one catalogue, not two** |
| Loading states | **6** | v1 | n/a | skeleton shimmer, brand-mark pulse, progress bar, custom spinner, placeholder-fade, staged-reveal. **Over-designing fights the purpose** |
| Custom cursor | **10** | v1 | **Disabled entirely on coarse pointers (unchanged) — see §9.3.1 for the required non-cursor touch signature** | Tier A, user-named. Untitled UI ships cursors as a foundation component, confirming they belong in a design system |
| Background ambient motion | **8** | v1 | n/a | User-named. Mirrors the decorative background layer's presets; the heaviest sub-variant (particle field) is v3-gated and inherits `costClass: gpu` when selected |
| Parallax | **5** | v2 | n/a (device-independent trigger; vestibular concern is independent of input device) | Accessibility- and performance-sensitive, so below the 10 default. **35.4% of adults 40+ have vestibular dysfunction** |
| Sticky/pinned scroll sequence | **4** | v2 | n/a — native touch scroll drives the same pin mechanism as wheel scroll | Each architecturally distinct and expensive to verify |
| Page transitions | **6** | v2 | n/a | Feasibility-grounded, architecture-dependent |
| Signature moment | **1 concept per direction (10 total) at Step 2, refined into 2–3 candidate treatments of that single concept for the shortlisted direction only, at Step 4** | v1 | Case-by-case — no default; whatever the chosen concept renders on touch must be specified with it | **NOT a swap catalogue.** Award-tier winners have exactly one, and treating identity-carrying choices as generic catalogue picks is the root mechanism of homogenisation. Handled under Step 6's custom-component allowance. **A lint flags a second one.** *(Reconciled count — see note below.)* |
| Smooth-scroll behaviour | **4** | v1 | n/a — Lenis wraps touch scroll the same as wheel scroll | native, lightly damped, Lenis-wrapped, per-section snap. Lenis wraps native scroll so accessibility survives; **ScrollSmoother is anti-recommended** because it restructures the DOM |
| Parallax depth rules | **5** | v2 | n/a | Picked once and applied everywhere, or layers fight each other |

**Signature-moment count, reconciled *(closes a minor gap)*:** §7's design-system inventory prices `direction.signature-moment` at **10**, "one per direction." This row originally said "2–3 concept candidates" with no stated relationship to that 10. Both are correct at different pipeline stages, restated as one sentence: **Stage A (Step 2) generates one signature-moment concept per direction — 10 total, matching §7's count exactly. Stage B (Step 4) takes only the shortlisted direction's one concept and produces 2–3 candidate treatments of it for the user to choose among.** §7 should be edited to quote this same sentence rather than restating "10" without the two-stage context — **cross-section fix required in §7, not made in this pass**, since this pass is scoped to §9.

#### 9.3.1 Touch and hover-parity requirements *(new subsection — closes a major gap)*

The original text asserted hover micro-reactions "must have a touch equivalent" and that the cursor-effect layer and cursor-reactive containers disable on touch, without defining any of the equivalents or gating them. Two user-named, Tier-A items (custom cursor, hover set) are affected. This subsection makes the requirement checkable.

**Per-variant touch/focus equivalents for the 10 Hover micro-reactions:**

| Hover micro-reaction | Touch/keyboard equivalent |
|---|---|
| lift+shadow | Same treatment retriggered on `:active` (press) plus `:focus-visible` ring for keyboard |
| magnetic | **No direct touch equivalent** — magnetic pull requires continuous pointer position with no touch analogue. Substitute: a brief `:active` scale-down "press" cue, plus `:focus-visible` ring |
| underline-draw | Same draw animation retriggered by `:active`/tap instead of `pointerenter` |
| fill-sweep | Same sweep retriggered on `:active`/tap |
| icon-morph | Same morph retriggered on `:active`/tap |
| scale-pulse | Same pulse retriggered on `:active`/tap |
| border-trace | Same trace retriggered on `:active`/tap |
| colour-shift | Same shift retriggered on `:active`/tap; persists under `:focus-visible` for keyboard users |
| tilt-3d | **No direct touch equivalent.** Substitute: a flat `:active` scale-down cue |
| cursor-glow | Touch **does** have a tap coordinate, so this one has a real equivalent: a radial `:active` flash centred on the touch point, fading over ~200ms |

**Custom cursor / Global cursor-effect layer (touch = fully disabled, unchanged):** because the entire item is desktop-decoration by construction, the direction must nominate a **non-cursor touch signature** so identity isn't solely desktop-borne — recommended default: reuse the direction's `signature-moment` treatment, or retarget one Tier-A hover-set entry to `:active`, as the thing that carries identity on touch. **This pairing is not yet recorded anywhere** — it requires either a new §5 interview question ("what should mobile visitors see in place of the custom cursor?") or a §7 direction-spec field; **cross-section addition required, not made in this pass.**

**Cursor-reactive container (all 5 variants no-op on touch, unchanged):** substitute is the container's base static or reduced-motion pose; the same non-cursor touch signature above is what carries identity in its place.

**Lint 9.T1 (hover-parity, new local id — first use in this document, continue this numbering if more section-9-local checks are added):** every interactive element carrying a hover treatment must also declare a `:focus-visible` treatment and a `:active` treatment (from the table above, or an author override). Elements failing this check are flagged the same way the existing "3+ distinct reveals" soft warning is flagged in the Scroll-reveal row. **[I — general WCAG hover/focus-content awareness informs this row; not independently re-verified against exact Success Criterion text in this pass, so no specific SC number is cited as fact.]**

### 9.4 The pinned/scrubbed exception (important)

Most containers re-target cleanly under drag because their trigger is viewport-intersection-based and their transform origin is relative to their own bounding box. **A scroll-driven pinned/scrubbed sequence is different**: its timeline is a function of absolute scroll distance travelled while pinned, which depends on its position in document flow and the room its parent has to scroll through. Dragging it into a narrow column or a section with different surrounding height silently breaks the composition — pin without room to scroll, or a scrub that completes too fast.

**Rule:** the D2 free-position escape hatch is **disabled by default** for this container kind. It is restricted to anchor reordering (move between sections), and forcing free-position requires an explicit confirmation. Re-anchoring triggers a scroll-length resimulation before the preview is shown accurate.

**What "resimulation" computes *(newly specified — closes a major gap)*:** on any re-anchor (move between sections, or a breakpoint change), the editor:

1. Recomputes the parent's total scrollable height contributed by the sibling sections between the pin's start position and its natural release point, at the current breakpoint.
2. Requires **`pinDuration ≤ availableScroll(breakpoint) × k`**, where `pinDuration` is the scroll distance the sequence's timeline is authored to consume, and `k` is a buffer factor. **`k`'s recommended default is 0.9** — leaving a 10% margin against sub-pixel rounding and dynamic content reflow — but this is a tuning choice made in this pass, not a cited standard; treat it as adjustable, not fixed. **[I]**
3. On failure, the editor **rejects the drop** with a named reason (`insufficient-scroll-room:<nodeId>@<breakpoint>`) and offers a one-click **"extend section to fit"** remediation, which pads the target section's `min-block-size` by the shortfall rather than silently truncating or stretching the animation timeline. This is a decision made in this pass to resolve the previously-unstated failure behaviour (the alternatives — silently shorten the timeline, or warn-and-proceed — were rejected because a pin-without-room failure is otherwise invisible until LOCK, which is exactly the "plays wrong, does not error" failure mode this exception exists to prevent).

**New lock-time gate (extends §13's gate list):** **Gate — pinned-sequence scroll-room.** At LOCK, assert the inequality in step 2 holds for every pinned/scrubbed node at all three reference breakpoints used elsewhere in this PRD — **390 / 768 / 1280** (matching §11.4's free-position gate level of detail). Any violation blocks LOCK with the same named reason as the drop-time check, so a sequence that passed at drop time but was later invalidated by an unrelated edit to a sibling section's height cannot ship silently.

### 9.5 Format and platform rules

| Decision | Rule | Evidence |
|---|---|---|
| Vector animation format | **dotLottie by default** (60KB runtime, ZIP-compressed JSON). **Rive only when a state machine or input-reactive behaviour is required** (200KB WASM runtime, but 50–80% smaller payloads). Threshold: >6 vector animations OR any state-machine requirement ⇒ Rive. **Neither runtime loads for a hover effect** — CSS/GSAP covers micro-interactions | **[V — rive.app blog, unicornicons, pkgpulse 2026; medium confidence on exact figures]** |
| Scroll-driven animation | **Native CSS `animation-timeline: scroll()/view()` as the primary path** (zero main-thread JS — directly serves the finding that main-thread work is the real performance axis), **GSAP ScrollTrigger as the `@supports`-not fallback**. Chrome/Edge 115+, Safari 18+, Firefox behind a flag; ~84% global as of mid-2026, Baseline-blocked pending Firefox. **The fallback must be real and tested, not assumed** | **[V — MDN, web-features-explorer, caniuse]** |
| Page transitions | **CSS `::view-transition-group/-old/-new` choreographies**, progressive-enhancement-safe by construction. Same-document VT is Baseline Newly Available (Chrome 111+, Firefox 133+, Safari 18+); **cross-document ships in Chrome 126+ and Safari 18.2+ but is still absent in Firefox as of mid-2026** — degrade to instant navigation, never a JS router hack that breaks the back button | **[V]** |
| Motion lint | UI interactions ≤300ms, never >500ms (Primer's shipped rule). Compositor-only properties (`transform`/`opacity`/`filter`); animating `width`/`height`/`top`/`left`/`margin` forces layout+paint every frame | **[V — primer motion.json5]** |
| Concurrency caps | Max 1 WebGL slot, max 1 particle/ambient layer, max 2 autoplay video loops, max 2–3 pinned sequences per page. Unlimited transform/opacity-only CSS reveals. **Enforced via the `costClass` field added to the container contract in §9.1 — `gpu` caps the first two, `heavy` caps the latter two** | **[I]** |
| Asset-supply gap | **DECIDED — v1 scope cut, requires explicit user sign-off (see below). This deviates from the breadth the user asked for at Step 2 and is flagged as such, not silently applied.** | **[V — the generation-surface limitation]** |

**Asset-supply decision, resolved *(closes a major gap — the earlier draft posed the question and deferred it to §17-R1 without answering it):**

Video-loop and animated sprite/frame-sequence containers **ship as fully-implemented containers that the generator never fills with a fabricated asset.** Concretely:

- The container kind, its `variant` list (autoplay-loop / play-on-enter / hover-play or scroll-scrubbed), its `trigger`/`playback` fields, and its editor UI are all in scope for v2 as already priced in §9.2.
- **The claude.ai design-system generation leg (Step 2/3) cannot produce the underlying footage, video file, or frame sequence itself** — this is a hard limitation of the generation surface, not a build-effort choice.
- The user must either **supply their own asset** (validated against `assets/manifest.json` exactly like any other asset, per §9.1 rule 5), or leave containers of these kinds unplaced.
- **Routing to an external stock-footage/photo-sequence provider with its own licence-manifest chain is explicitly OUT OF SCOPE for v1.** Building that integration is a separate, larger scope item (a third-party licence chain feeding the Step-8 evidence bundle) and is not undertaken here.
- **Requires a new §5 interview question** ("Do you have existing brand video footage or photo sequences you want animated on the site?"), so the gap is surfaced to the user at Step 1 rather than discovered when a container comes up empty at Step 4 — **cross-section addition required in §5, not made in this pass.**

**Requires user sign-off — naming the deviation:** the user's Step-2 vision named "an animation for the front" among other examples and explicitly said the examples were illustrative, not exhaustive; if the user's intended hero treatment is video-based, this decision means the design-system generation step cannot produce it for them, and they must supply the footage themselves or accept a non-video hero. This is a real scope narrowing relative to the breadth the user asked for, and is called out here for explicit confirmation rather than assumed.

### 9.6 The motion-editing contradiction (stated plainly, mitigated partially)

A draggable container must be measurable. `getBoundingClientRect()` on a GSAP-transformed element returns the **animated** position, not the layout position, so drag maths is wrong mid-tween. Lenis lerps `scrollTop` every frame, so scroll measurement is unreliable while it runs. Every real implementation therefore disables animation in edit mode — which is also what the prior report's capture protocol mandates for screenshots.

**Consequence:** the user arranges an animated hero with all motion frozen, locks, sees the real motion for the first time, finds it wrong, unlocks, and the motion turns off again. **They cannot debug the thing they are trying to fix, in the tool built to fix it.**

**Partial mitigations (a mode toggle, not a fix) — re-prioritised in this pass:**

- **PREVIEW MOTION — moved to v1 priority** *(closes a major gap: the original draft left all three mitigations at v2/§18 while placing eight v1 motion kinds — marquee, reveal-on-enter, hero entrance, hover micro-reactions, custom cursor, background ambient motion, smooth scroll, section reveal choreography — into the editor with no way to see any of them move. §9.6's own claim that the contradiction is "mitigated partially" was not true under that phasing; it is the cheapest of the three mitigations to build (re-enable Lenis/ScrollTrigger/tweens, disable all editing — no new measurement code) and belongs with the v1 motion kinds it exists to debug).* Re-enables Lenis + ScrollTrigger + all tweens and **disables all editing**. The page becomes the locked site in place, one keypress away. **This priority change requires a matching edit in §10.8 and §18, where "Motion preview toggle" currently sits at v2 — not made in this pass, since this pass is scoped to §9, but flagged as a required follow-up so the three sections don't disagree.**
- **Per-container scrub slider** setting the tween to normalised progress 0→1, so start/mid/end poses are visible statically. **Remains v2.**
- **Trigger-point markers** rendered in the overlay showing where the scroll trigger fires. **Remains v2.**

**Open question, explicitly unresolved (unchanged from the prior draft, restated so it isn't lost): does §10.8's v1 "In-editor Preview mode" play motion, or freeze it like edit mode?** No source material in this section answers this — it is a decision that belongs in §10.8, not fabricated here. **Requires a decision in §10.8.**

**There is no known mitigation for judging motion FEEL while editing.** The prior report's Data Gap 2 states motion verification is unvalidated end-to-end anywhere in the industry; the human-in-the-loop design does not change that, it moves the unsolved problem from an AI judge to a human who also has to be in preview mode to see it. This is stated in §17 as a risk with no mitigation.

### 9.7 Cross-check against §8's v1 motion component list *(new — closes a major gap)*

§8 line 319 enumerates a v1 component set that includes: *"still container + background layer + marquee + reveal container + section reveal + text reveal + hover set + custom cursor + smooth scroll + reduced-motion + easing matrix; motion toggle."* This was never mapped onto §9.2/§9.3's ids, so the two inventories were not provably the same set. Row-by-row:

| §8 v1 term | §9.2/§9.3 id | Status |
|---|---|---|
| still container | §9.2 Still-image container | Matched |
| background layer | §9.2 Decorative background layer | Matched |
| marquee | §9.2 Marquee/ticker container **and** §9.3 Marquee animation kind | Matched — confirmed as one 6-item list (§9.1.1) |
| reveal container | §9.2 Reveal-on-enter | Matched |
| section reveal | §9.3 Section reveal choreography | Matched |
| text reveal | §9.3 Text reveal / kinetics | Matched |
| hover set | §9.3 Hover micro-reactions | Matched |
| custom cursor | §9.2 Global cursor-effect layer **and** §9.3 Custom cursor | Matched — AND-composed per §9.1.1 |
| smooth scroll | §9.3 Smooth-scroll behaviour | Matched |
| reduced-motion | §9.1's `reducedMotionPoster` / `reducedMotionVariantRef` fields | Matched, but **cross-cutting, not a container or kind** — it is a field on every motion-capable container, not a separate inventory row. No fix needed, noted for completeness. |
| easing matrix | **Not found in §9.2 or §9.3.** | **OPEN QUESTION — no known mitigation in this pass.** An easing matrix (which easing curve pairs with which trigger/kind) reads as a design-token artifact — most likely it belongs beside the direction's other derived-value scales in §7, not as a container or animation kind here. This section does not have the authority to place it; recorded as unresolved and requiring a decision in §7 or a new token-inventory section. |
| motion toggle | **Not found in §9.2 or §9.3.** | **OPEN QUESTION — no known mitigation in this pass.** Distinct from "reduced-motion" above (which is a per-container field); "motion toggle" reads as a site-facing, visitor-usable control (e.g. a persistent on/off switch overriding `prefers-reduced-motion`), which would be a published-site UI component, not an editor container. Not specified anywhere located in this pass. Requires a decision in §8 or §10 as to whether this is a real v1 deliverable or a mis-transcribed duplicate of "reduced-motion." |

Fourteen of §8's sixteen v1 motion terms are now traceably matched to a §9.2/§9.3 id. The remaining two ("easing matrix," "motion toggle") are real gaps in the inventory, not naming mismatches, and are left open rather than silently assigned a home that isn't backed by this section's source material.

---
