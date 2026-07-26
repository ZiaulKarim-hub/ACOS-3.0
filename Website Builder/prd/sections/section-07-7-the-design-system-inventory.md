## 7. The design system inventory

**Structure.** A direction is a **26-slot identity vector**. Everything else in the system is a pure function of that vector plus shared seed tables (Utopia multipliers, Carbon/M3 motion matrices, Leonardo contrast targets). This is the shipped USWDS `$theme-*` architecture applied to a generated system, and it is what makes 10 coherent directions tractable instead of 10 × 800 independent decisions. **[V — uswds/uswds `_settings-typography.scss`; adobe/leonardo README; utopia.fyi calculators]**

**Scale reality check.** Real systems ship 250–350 *semantic* tokens, not 80. IBM Carbon v11: 258 named colour tokens + 24 layout + 34 type. Material 3: ~50 colour roles, 15 typescale roles × 5 properties, 16 durations + 10 easings, 12 shape, 6 elevation, 4 state-layer opacities. Fluent 2: ~300 alias tokens. **Budget ~600–900 resolved tokens per complete direction. [V — counted programmatically from carbon-design-system/carbon, material-web, microsoft/fluentui sources]** The user's "~80 items" is an *item* count; each item expands to 1–40 tokens.

### Variant-count key

- **A number** = distinct pickable options.
- **`derived`** = computed from the direction vector; the editor renders **no control** for it (`com.acos.pick.pickable: false`).
- **`n/a`** = a policy, contract, or coverage checklist, not a choice.

---

### 7.1 Category A — Direction core (the 26-slot identity vector)

| Item | Variants | Rationale |
|---|---|---|
| `direction.manifesto` | **10** | 40–80 words naming the point of view, the tension it resolves, what it refuses to do. One per direction — this IS the direction |
| `direction.mood-tags` | **10** | 3–6 tags from a closed ~30-term vocabulary, so tags are machine-comparable for artwork affinity and Step-5 queries |
| `direction.reference-triangulation` | **n/a** | ≥3 named references per direction, **abstracted attributes only** (proportion, contrast strategy, rhythm) — no reference pixels retained. Provenance metadata; also the trade-dress safety measure |
| `direction.signature-moment` | **10** | One per direction, specified as intent + trigger + duration budget. Award-tier work has exactly one; three reads as noise **[V — prior report Findings 2, 6]** |
| `typeface.display` | **10** | The loudest identity carrier. If two directions share it they are not two directions |
| `typeface.body` | **10** | Ten slots that may resolve to as few as 5 distinct faces — directions can legitimately share a body face |
| `typeface.mono` | **5** | Small, low-identity surface. Five moods span it: grotesque-mono, typewriter, terminal/bitmap, humanist, geometric |
| `typeface.accent` | **10** | One per direction *including "none"*. Making null explicit stops the generator adding a decorative face reflexively |
| `type.base-size-pair` | **10** | Min/max body size. "Big generous type" vs "small dense type" is identity, and Utopia takes it as explicit input |
| `type.scale-ratio-pair` | **10** | Min-viewport and max-viewport modular ratios. Where hierarchy drama lives; a pair, not a scalar |
| `color.hue-anchors` | **10** | OKLCH angles for primary/secondary/tertiary/accent. Hue *relationships* (analogous/complementary/split/mono+accent) are the defining colour decision |
| `color.chroma-policy` | **10** | Ceiling + curve across the lightness ramp. Separates muted-editorial from neon-arcade at identical hues |
| `color.neutral-temperature` | **4** | Pure grey / warm / cool / tinted-by-primary. Four genuinely distinct options; more is false precision |
| `color.scheme-strategy` | **10** | Light-first / dark-first / dual-equal, plus which scheme the art was authored against. Determines which gets the hand-tuned solve |
| `density.base-unit` | **4** | 2, 4, 6 or 8px. Only four are used in practice; 8 with a 4 half-step is the common default |
| `space.scale-ratio` | **10** | The multiplier table. Airy vs tight is identity — but only the *ratio* is picked; the 9 values are derived |
| `shape.radius-policy` | **6** | Sharp-0 / subtle / soft / pill-full / squircle / asymmetric-per-corner. Six distinct corner languages |
| `shape.border-policy` | **5** | Hairline / heavy rule / none / double-offset / plus base width. Interacts hard with elevation model — validate the pair |
| `elevation.model` | **5** | Shadow-physical (Fluent two-light) / tint+shadow (M3 dp) / layer-only (Carbon) / border-only / glass-backdrop. **The item whose mismatch causes the most invisible incoherence** — a border-only direction must reference zero shadow tokens, and lint enforces it |
| `motion.expressiveness` | **10** | A single 0–1 scalar plus a productive/expressive flag that scales the whole duration and easing matrix. Carbon ships exactly this axis, which is why 16 durations and 10 easings below are `derived` |
| `grid.personality` | **10** | Column intent, symmetry, whether content breaks the grid, gutter:margin proportion, baseline enforcement. Top-tier identity signal, not derivable |
| `surface.background-art-style` | **10** | The user's named FruitSync item. Medium (flat/gradient/illustrated/pattern/noise/canvas), density, scroll behaviour, token re-skinnability. Largest continuous surface on any page |
| `texture.grain-policy` | **5** | None / trace / film / coarse / halftone. Amplitude derived from level |
| `imagery.treatment` | **10** | Grade, duotone mapping, crop rules, subject distance, grain — *including "no photography"*. Making the null explicit prevents stock-photo default behaviour |
| `cursor.personality` | **6** | Native / custom-static / custom-follower / hybrid + visual language. **Hard browser limits:** capped at 128×128 in Firefox and Chromium (32×32 recommended), PNG or static SVG 1.1 only, hotspot x/y from top-left, and a native keyword fallback is **mandatory** — a url-only cursor is invalid CSS **[V — MDN cursor]** |
| `type.viewport-endpoints` | **n/a** | 360 → 1440. Device facts. Must be identical across all directions or they become non-comparable in the editor preview |

### 7.2 Category B — Colour tokens (all derived)

| Item | Variants | Rationale |
|---|---|---|
| `color.primitive-ramps` | derived | Leonardo model: declare colorKeys + target ratios, **solve** for colours. Picking swatches by eye is the exact failure Leonardo removes |
| `color.ramp-step-count` | derived | Falls out of the contrast ladder: as many steps as distinct targets plus interpolation headroom (10–13 typical) |
| `color.surface-roles` | derived | background, surface, surface-dim, surface-bright + a **5-step container ladder** (lowest/low/base/high/highest). The ladder is what makes dark mode readable; a single background+card pair is the #1 amateur tell |
| `color.text-roles` | derived | 12 roles: primary, secondary, tertiary, placeholder, helper, disabled, inverse, on-color, on-color-disabled, error, link, visited |
| `color.border-roles` | derived | subtle (per layer 00–03), strong (per layer), interactive, disabled, inverse, tile, focus, divider — ~16, all lightness offsets from their layer |
| `color.icon-roles` | derived | 7 roles at a fixed +0.5:1 contrast offset from text (thin strokes need more) |
| `color.brand-roles` | derived | ~20: primary/on-primary/primary-container/on-primary-container × 3, plus M3's `fixed` and `fixed-dim` variants that persist across schemes |
| `color.status-roles` | derived | error, warning, success, info, caution-major, caution-minor + inverse + container + on-container. Status hues are near-universal; only chroma and temperature adjust |
| `color.state-layer-opacities` | derived | **4 numbers replace Carbon's ~60 state-suffixed colour tokens.** M3 verified: hover 0.08, focus 0.12, pressed 0.12, dragged 0.16. Seeded from M3, scaled by expressiveness ² |
| `color.focus-ring` | derived | Outer + inner ring (two-tone so it reads on any surface — Fluent ships `colorStrokeFocus1/2`), width, offset, style, radius-follow, on-image variant. **Geometry fixed by WCAG 2.2 SC 2.4.13**: ≥ the area of a 2px perimeter, ≥3:1 focused-vs-unfocused. Never pickable |
| `color.selection` | derived | `::selection` bg + fg with **per-scheme alpha**. Primer ships 0.2 light / 0.7 dark — nobody guesses this **[V — primer selection.json5]** |
| `color.caret` | derived | One value, contrast-checked against field backgrounds. Trivial, universally forgotten |
| `color.scrollbar` | derived | `scrollbar-color` thumb + track + hover + width. Baseline newly-available Dec 2025; auto-reverts under forced-colors. A default OS scrollbar on a dark cinematic site is an immediate tell **[V — MDN scrollbar-color]** |
| `color.accent-color` | derived | One declaration themes every unstyled native checkbox/radio/range/progress |
| `color.overlay-scrim` | derived | Backdrop colour + alpha + optional blur. Glass model gets blur, flat model gets flat alpha |
| `color.skeleton` | derived | Base + shimmer. Needed the moment any component has a loading state |
| `color.shadow` | derived | Ambient + key colours, tinted not pure black. Pure-black shadows are the flattest default and should be impossible to emit |
| `color.gradient-set` | **6** | hero wash, card sheen, text gradient, edge fade, radial glow, mesh base. Six named roles covers real usage without becoming an unaudited library |
| `color.dark-scheme-values` | derived | **A full second solve, not an inversion.** M3 ships per-scheme role values; Carbon ships four themes (white/g10/g90/g100), not two inverted ones. Flipping L produces the classic over-saturated halating dark mode |
| `color.high-contrast-scheme` | derived | Third solve at an elevated contrast multiplier via `prefers-contrast: more`. Literally one parameter change in Leonardo |
| `color.forced-colors-mapping` | n/a | Which elements opt out of `forced-color-adjust`, where borders must be re-added, which decorative layers hide. Dictated by OS keywords, but must be an explicit checklist — forced-colors silently deletes background-based affordances |
| `color.print-scheme` | derived | Light scheme with chroma flattened, link URLs expanded, page breaks, decorative layers suppressed |
| `color.syntax-highlight` | **4** | light-classic, light-muted, dark-classic, dark-vivid, mapped from direction hues. Carbon ships ~90 syntax tokens; 12 roles suffice for a marketing site |

### 7.3 Category C — Typography

| Item | Variants | Rationale |
|---|---|---|
| `type.role-set` | derived | ~18 roles (display/headline/title/body/label L·M·S + caption, overline, quote, code, lede) × 5 properties = ~90 values, all computable from typeface picks + scale ratio |
| `type.scale-steps` | derived | Pure Utopia math from 6 inputs. Hand-picking a step is how a scale loses its ratio |
| `type.weight-plan` | derived | Hard-capped at 4 static weights or 1 variable file per family. A weight exists only if a role references it |
| `type.line-height-map` | derived | Deterministic inverse function of size. M3 verified: display-large ≈1.12, body-small ≈1.33 |
| `type.tracking-map` | derived | **Sign flips with size** — M3 verified: display-large −0.015625rem, body-small +0.025rem. One derived curve reproduces the whole map |
| `type.measure` | derived | 60–75ch body, 45–60ch lede, ~40ch pull quote. Enforceable as a lint on the built page |
| `type.fallback-metrics` | derived | Local `@font-face` with `size-adjust`, `ascent-override`, `descent-override`, `line-gap-override` from the **real font file's metrics**. **Computed by the skill after the typeface pick, never requested from claude.ai** — it needs the actual file. Highest-leverage invisible token family for CLS |
| `type.loading-strategy` | **3** | swap+preload / optional / block-with-100ms-cap. Constrained by licence class: OFL may be self-hosted; Fontshare-class must be CDN-linked and never vendored |
| `type.text-wrap-policy` | **n/a** | `balance` for headings, `pretty` for prose, `stable` for editable. Baseline Oct 2024, and the correct answer is universal. Hard limits make it non-negotiable: `balance` applies only to ≤6 lines in Chromium / ≤10 in Firefox; `pretty` has a documented performance cost **[V — MDN text-wrap-style]** |
| `type.numeral-style` | **4** | lining-proportional (prose), lining-tabular (data), oldstyle-proportional (editorial), oldstyle-tabular. Validate against the chosen face's support |
| `type.emphasis-policy` | **6** | True italics / small caps / weight shift / colour shift / letterspaced uppercase / forbidden-list. **Declaring the forbidden ones matters more** — faux-italic on a face without an italic is a visible defect |
| `type.underline-style` | derived | thickness, offset, skip-ink, hover/visited transitions, from the body face's stroke weight and x-height. Default browser underlines are one of the most reliable amateur signals |
| `type.list-marker-style` | **6** | disc, dash, custom glyph, numeral-in-shape, icon, none-with-indent. Lists appear on every content page; default markers undo a lot of typographic work |
| `type.quote-treatment` | **6** | Rule / quotation mark / indent / colour block, plus attribution styling and the quote glyph set |
| `type.lede-and-dropcap` | **5** | Lede bump / drop cap / raised cap / none / small-caps-opening. Editorial directions use it; product directions must not |
| `type.prose-rhythm` | derived | Heading-to-body margins, list spacing, figure/caption spacing. Hand-tuning is how rhythm dies |
| `type.script-and-rtl-coverage` | **n/a** | Declared coverage per face, logical properties (`inline-start`/`end`, never left/right), RTL mirroring rules. A correctness requirement — retrofitting logical properties is expensive, and this project has already paid that bill once |

### 7.4 Category D — Space, size, layout

| Item | Variants | Rationale |
|---|---|---|
| `space.scale-steps` | derived | 9 fluid steps 3xs…3xl. Utopia default multipliers verified: 0.25 / 0.5 / 0.75 / 1 / 1.5 / 2 / 3 / 4 / 6 relative to base **[V — utopia.fyi/space/calculator]** |
| `space.one-up-pairs` | derived | 8 pairs that grow one step across the viewport range. What makes *spacing* responsive, not just type |
| `space.custom-pairs` | derived | Named non-adjacent pairs (e.g. s-l) for section padding. Typically 2–4 per site |
| `space.section-rhythm` | derived | **The single value most responsible for whether a page reads as composed or as stacked blocks** |
| `layout.breakpoints` | **n/a** | 320 / 390 / 768 / 1280 / 1440 authored; Primer's shipped set (320, 544, 768, 1012, 1280, 1400) as reference. Shared across all directions so the editor preview and D2's constraint model mean the same thing everywhere ³ |
| `layout.container-widths` | derived | prose (= measure × body size), wide, full-bleed, editorial-narrow — multiples of the column module |
| `layout.grid-definition` | derived | Columns, gutters, margins per breakpoint + named area templates. **Critical for D2: these are what components SNAP to**, so they must be a real token set the editor reads, not decorative overlay |
| `layout.gap-scale` | derived | Subset of the space scale, called out because gap and padding get conflated then drift |
| `layout.aspect-ratio-set` | **8** | 1:1, 4:3, 3:2, 16:9, 21:9, 4:5, 9:16, golden. Constraining media to a named set is what keeps a gallery from looking hand-assembled |
| `size.icon-sizes` | derived | From cap-height of the adjacent type role, not from the space scale — so icons optically match text |
| `size.control-heights` | derived | line-height + padding + border, floor-clamped by the 24×24 target minimum |
| `size.min-target-size` | **n/a** | 24×24 CSS px (WCAG 2.2 SC 2.5.8, AA) with five exceptions: spacing, inline, user-agent control, equivalent, essential. The **spacing** exception (a 24px circle on each target must not intersect another) is what the editor checks after a drag |
| `size.avatar-sizes` | derived | Diameter steps + overlap offset for groups. Only if the site has people on it |
| `layout.safe-area-and-viewport` | **n/a** | `env(safe-area-inset-*)`, dvh/svh/lvh, scroll-padding for sticky headers. 100vh on mobile and anchor links landing under a sticky header are two of the most common shipped defects |

### 7.5 Category E — Layers & plumbing

| Item | Variants | Rationale |
|---|---|---|
| `layout.z-index-scale` | **n/a** | Primer's verified ladder adopted verbatim: behind (−1), default, sticky (100), dropdown (200), overlay (300), modal (400), popover, skipLink (top). **Note the two non-obvious orderings**: dropdowns above sticky headers but below modals, and skipLink outranks everything because accessibility wins **[V — primer z-index.json5, quoted]** |
| `layout.stacking-context-rules` | **n/a** | Which properties create stacking contexts (transform, opacity<1, filter, will-change, backdrop-filter) and the rule that animated/parallax art containers must not enclose overlay-layer content. **This bites hard here specifically because D4 puts animations inside draggable containers** — a transformed art container silently traps every dropdown inside it, and presents as "the menu is behind the picture" with no obvious cause |
| `layout.editor-chrome-band` | **n/a** | A reserved band **above** skipLink for gridlines, drag handles, snap guides, component bar — plus the guarantee that LOCK strips the entire band. If editor chrome shares the site's ladder there is no clean way to *prove* it was removed (D3) |

### 7.6 Category F — Shape, surface, effect

| Item | Variants | Rationale |
|---|---|---|
| `shape.radius-scale` | derived | M3 verified: none 0, xs 4, s 8, m 12, l 16, xl 28, full 9999 + directional variants (top, start, end) for sheets and grouped controls |
| `shape.per-corner-recipes` | **8** | leaf, ticket, tab-top, notch, chamfer, squircle, single-cut, pill-end. Cheap distinctiveness; more than 8 is an unusable menu |
| `shape.border-width-scale` | derived | Four steps doubling from base. Must be integer px at 1× to avoid sub-pixel hairline blur |
| `shape.stroke-style-set` | **4** | DTCG supports a custom `dashArray`/`lineCap` object, which is what makes a *designed* dash possible rather than the browser default |
| `shape.divider-treatment` | **8** | hairline, heavy rule, gradient fade, shape/wave cut, colour-block change, whitespace only, overlap, ticket-notch. **Section transitions are where long pages read as one composition or as a stack** |
| `shape.clip-and-mask-shapes` | **10** | blob, arc, angle, wave, torn, circle-reveal, hex, custom-brand + 2. Normalised path data so they scale; directly reusable by D4's art containers |
| `elevation.shadow-scale` | derived | Multi-layer via the **DTCG shadow ARRAY form** — a realistic 3-layer shadow is ONE token, which is exactly what separates designed depth from `box-shadow` defaults |
| `elevation.inner-shadow` | derived | Inverted and reduced from the outer scale. Needed for pressed states in physical models |
| `effect.blur-scale` | derived | From the space scale. **Carries a performance note**: `backdrop-filter` on a large scrolling surface is main-thread cost, and main-thread work is the actual performance failure axis |
| `effect.backdrop-recipe` | **6** | Glass/frost combinations of blur + saturation + tint alpha + border highlight. **Lint rejects these in a border-only or flat direction** |
| `effect.opacity-scale` | derived | 5–7 steps from the state-layer opacities. Ad-hoc opacity is a top source of contrast failures because it bypasses the solver |
| `effect.noise-grain` | **8** | Prefer SVG `feTurbulence` over raster tiles — grain re-colours with the direction and costs no bytes |
| `effect.gradient-mesh` | **8** | Specified as **blob positions + hue assignments, not baked images**, so the mesh re-skins when hues change in Step 5 |
| `effect.pattern-tiles` | **12** | grid, dot, hatch, halftone, isometric, topographic, stripe, chevron, scatter, weave, circuit, custom-brand. SVG using `currentColor`. The cheapest way to make a large empty surface feel authored |
| `effect.blend-mode-policy` | **6** | Must be a POLICY because blend modes create stacking contexts and can silently break the overlay ladder |

### 7.7 Category G — Motion (system items, per D4)

See §9 for the full motion/container treatment. Token-level items:

| Item | Variants | Rationale |
|---|---|---|
| `motion.duration-scale` | derived | Seed from **Carbon's verified 6-step set**: fast01 70ms, fast02 110, moderate01 150, moderate02 240, slow01 400, slow02 700; scale by expressiveness. **Primer's hard lint applies as a build gate**: UI interactions ≤300ms, never >500ms; decorative motion exempt but must be tagged **[V — carbon packages/motion/src/index.ts; primer motion.json5 quoted]** |
| `motion.easing-set` | derived | **Carbon's 3×2 matrix IS the derivation**: standard/entrance/exit × productive/expressive; one expressiveness flag selects the whole column. Verified values at both endpoints so interpolation is safe |
| `motion.spring-presets` | derived | Tension/friction/mass + a mapping from each easing token to its nearest spring. **DTCG has no native spring type** — requires a `$extensions.acos.spring` namespace, and every tool in the chain must agree on its shape or springs silently degrade |
| `motion.transition-presets` | derived | DTCG `transition` composite bundling duration+delay+timingFunction. One token = one CSS declaration, which stops a builder pairing a fast duration with a slow curve |
| `motion.stagger-policy` | derived | Delay increment as a fraction of base duration, plus **the cap** beyond which stagger becomes a single group animation. The cap is the important part — uncapped stagger on a 40-item grid makes the last item arrive seconds late |
| `motion.distance-tokens` | derived | **Bound to the spacing scale**, never arbitrary translateY values, so motion moves a visually consistent amount relative to the same grid the layout snaps to. Extends D1's computed-not-picked rule into motion |
| `motion.choreography-rules` | **n/a** | Meta-rules: exits use accelerate and finish faster than entrances use decelerate; stagger follows reading order; only one pinned sequence and one ambient layer per viewport |
| `motion.reduced-motion-variants` | **n/a** | **Mandatory pairing.** Art-directed (cross-fades, poster frames, instant states), not `animation: none`. Must be authored at generation time — the editor cannot invent a good one |

### 7.8 Category H — Iconography & marks

| Item | Variants | Rationale |
|---|---|---|
| `icon.family-spec` | **10** | Grid size, keyline shapes, stroke weight, terminal style, corner radius, optical-size behaviour, whether strokes scale. Icons appear everywhere so a mismatched family is the most pervasive incoherence available |
| `icon.style-variants` | derived | Outline / filled / duotone **plus the selection rule** (filled = active nav, outline = inactive). The rule is the load-bearing part; mixing arbitrarily is a common tell |
| `icon.core-set` | **n/a** | ~50-glyph coverage checklist: menu, close, chevron ×4, arrow ×4, external-link, search, check, minus, plus, info, warning, error, success, user, mail, phone, location, calendar, clock, download, upload, share, copy, link, play, pause, mute, fullscreen, filter, sort, grid, list, settings, star, heart, cart, bookmark, edit, trash, refresh, lock, eye, eye-off, drag-handle, more-h, more-v + social. **Missing icons are discovered at build time and force an off-system substitution** |
| `icon.alignment-rules` | derived | Optical centring, cap-height vs x-height alignment, inline gap. The **RTL mirroring list is explicit data** (arrows mirror, clocks do not) and cannot be inferred |
| `mark.logo-lockups` | **10** ⁴ | Wordmark, symbol, horizontal, stacked, monogram + clear-space, min-size, mono/inverse. Clear-space and min-size derive from the mark's geometry |
| `mark.favicon-set` | derived | `favicon.svg` with a dark-mode media query **inside the SVG**, 32px ICO, 180px apple-touch, 192/512 maskable (safe zone required), manifest theme colours. Routinely missing from AI-built sites |
| `mark.social-share-image` | **6** | 1200×630 OG + Twitter card, **parameterised template not a static file** so per-page images generate automatically. One generic OG image across a whole site is a visible shortcut |
| `mark.decorative-glyphs` | **10** | Bullets, section symbols, ornaments, decorative arrows, underline squiggles, highlight strokes, asterisks, corner ticks. What makes a page feel drawn rather than assembled, at near-zero cost as inline SVG |

### 7.9 Category I — Imagery & artwork

**Read §17-R1 first.** claude.ai cannot produce raster images **[V — Anthropic, April 2026]**. The user's own cited exemplar (the FruitSync site background) is 231 PNGs exported from Unity by a hand-written batchmode exporter pulling the game's real procedural sprites **[V — `SiteAngryExport.cs`; `ls` of `/Users/zee/fruitsync-animated-variants/assets`]**. That art came from a pre-existing hand-drawn library, not from a chat.

Three honestly-labelled lanes:

- **Lane A — code-drawn art.** SVG scenes, CSS gradient meshes, canvas/WebGL noise fields, generative patterns. claude.ai is genuinely good at this, and it is on-brand-able because it is parameterised by tokens.
- **Lane B — asset ingestion.** Point the skill at an existing sprite/photo/illustration folder. **This is what actually made the FruitSync site work**, and Step 0 question C3 detects it.
- **Lane C — external raster generation.** Midjourney / FLUX / Recraft, per the prior report's asset-routing matrix. A **separate** hand-carry with its own licence manifest, explicitly scoped in or out per release.

| Item | Variants | Rationale |
|---|---|---|
| `art.container-contract` | **n/a** | **THE load-bearing item for D4.** Box sizing, aspect policy, anchor/pin, overflow, mask, scheme-awareness, motion-capable flag, reduced-motion poster, focal point, alt text, licence ref. Because animated pieces live in the same draggable containers as static art, **both must satisfy one contract** — otherwise the editor needs two drag models and the lock/export path forks. Must be specified BEFORE any artwork is generated |
| `art.background-scene` | **20** | Per D1, tagged by direction affinity. Each declares `palette-mode`: **token-referencing** art (`currentColor` / `var(--*)`) suits many directions and re-skins free; **baked-palette** art suits only its tagged directions. **Require ≥60% token-referencing** — that is what makes Step 5 cheap instead of a full art regeneration |
| `art.hero-artwork` | **20** | This asset IS the LCP element on most sites, so each variant carries a **pre-LCP transfer budget** |
| `art.spot-illustrations` | **20** | Built from a shared component vocabulary (same stroke, same palette slots) so the set reads as one hand |
| `art.section-divider-shapes` | **12** | wave, angle, arc, torn, layered, notch, blob, zigzag + flipped/inverted. Normalised SVG paths that stretch; token-coloured for both schemes |
| `art.texture-plates` | **12** | paper, canvas, concrete, film-grain, halftone, riso misregistration, scan-lines, foil, gradient-map, fabric, ink-bleed, dust. **What breaks the flat-vector-gradient look that reads instantly as machine-generated** |
| `art.photo-grade-recipe` | **8** | CSS/SVG filter chain: exposure, contrast curve, duotone, grain, vignette, hue-shift toward the anchors. **The highest-leverage way to make sourced imagery look commissioned**, and the implementation of the ban on unstyled stock |
| `art.crop-and-focal-policy` | derived | `object-fit`/`object-position` defaults + **per-image focal point** (a single draggable dot, not a crop rectangle — it degrades gracefully across every aspect ratio a reflow system produces) + `<picture>` art direction. Focal metadata is captured in the editor, not designed |
| `art.placeholder-strategy` | **4** | LQIP / blurhash / dominant-colour / skeleton + reveal transition. **Must reserve the exact final box** via `aspect-ratio` or the placeholder causes the CLS it was meant to prevent |
| `art.avatar-style` | **8** | photo, illustrated, monogram, generated-geometric, silhouette + shape/ring. Generated-geometric matters because it needs no assets |
| `art.3d-or-canvas-scene` | **6** | WebGL/three.js or Gaussian-splat spec with a **mandatory GPU-tier ladder**: full / reduced / static poster via detect-gpu. Without it a 3D hero is a guaranteed gate failure on low-end devices |
| `art.empty-state` | **10** | Cheap once the spot-illustration vocabulary exists; always ships, never designed |
| `art.error-state` | **10** | 404 + 500 art plus recovery layout. A real page a visitor will see; the host default undoes the whole system in one view |

### 7.10 Category J — Accessibility & compliance (system-level)

| Item | Variants | Rationale |
|---|---|---|
| `color.contrast-ladder` | **3** | AA-floor / AA-generous / AAA. **Site-level policy chosen once and applied to all directions** — per-direction would let a pretty direction ship illegible text |
| `token.contrast-proof-table` | **n/a** | Every text/surface pairing with WCAG 2 ratio and APCA Lc, pass/fail against the ladder. Because Leonardo solves *to* the targets, this is all-pass by construction — **so any failure means a value was hand-edited, making the table a tamper detector as well as a proof** |
| `system.alt-text-policy` | **n/a** | Decorative (`alt=""`) vs informative rules + a **required alt field on every artwork record**, captured at generation time. Retrofitting at lock time fails because nobody remembers what the illustration was meant to convey |

### 7.11 Category L — Data visualisation

| Item | Variants | Rationale |
|---|---|---|
| `color.data-vis-categorical` | **3** | Hues derive from the direction; the **ordering strategy** is the real pick: harmonic rotation / maximum perceptual distance / brand-first-then-distance. Three strategies, not ten palettes |
| `color.data-vis-sequential` | derived | Monotonic lightness is a mathematical requirement; OKLCH makes it computable from the hue anchor |
| `color.data-vis-diverging` | derived | Two hues around a neutral midpoint **pinned to the actual surface colour** — that pinning is what stops diverging charts looking pasted on |
| `chart.structural-tokens` | derived | gridline, axis, tick, axis-label, annotation, reference-line, zero-line, tooltip surface, max-series cap. From border/text roles at reduced emphasis. **Without them charts read as a foreign component** |

**A direction with 3 brand hues cannot yield a 6-series categorical palette that is simultaneously on-brand, distinguishable, and colourblind-safe.** Every direction must therefore carry the dataviz sub-token set **from generation time**, not as a retrofit. The local `dataviz` skill already ships a form heuristic, a colour formula with a runnable validator, and a palette reference — reuse it rather than reinventing.

### 7.12 Category N — Token file contract

| Item | Variants | Rationale |
|---|---|---|
| `token.tier-architecture` | **n/a** | Three tiers: **primitive** (raw ramps, never referenced by components), **semantic** (role-named, the only tier components may reference), **component** (overrides only where a component genuinely deviates). Enforceable rule: no component CSS may reference a tier-1 token |
| `token.file-format` | **n/a** | DTCG 2025.10 JSON, `$type` declared or group-inherited, references via `{group.token}`, composite types wherever CSS has a composite property. **JSON-Schema-validatable — which is precisely what makes the Step-3 boundary safe** |
| `token.llm-extension-block` | **n/a** | `$extensions['com.acos.llm'] = {usage[], rules, antipatterns[]}` on every semantic token |
| `token.pick-extension-block` | **n/a** | `$extensions['com.acos.pick'] = {pickable, slot, directionId, variantIndex, derivedFrom[]}`. The editor reads this to decide what to render a control for |
| `token.direction-hash` | **n/a** | `$extensions['com.acos.direction'] = {id, vectorHash}`. Builder rejects mismatches |
| `token.naming-convention` | **3** | Carbon role-state-suffix / Fluent camelCase-compound / Primer dotted-group. **Pick ONE globally**; mixing is why token files stop being greppable |
| `token.theme-structure` | **n/a** | Recommend the per-mode override pattern (Primer's `org.primer.overrides`) over separate files — the selection token proves it handles per-scheme alpha differences a file split makes easy to forget to mirror |
| `token.capability-manifest` | **n/a** | Root manifest: direction id + hash, expected token count per group, schemes present, breakpoints, pickable slot list, artwork index with affinity tags, font licence classes |
| `token.compiler-target` | **n/a** | **Pinned explicitly.** Style Dictionary v4 has first-class DTCG support but **not** full 2025.10 (in progress in v5); Terrazzo supports the full format today. Emitting 2025.10 colour objects into v4 will fail **[V — styledictionary.com/info/dtcg; terrazzo.app docs; medium confidence on current version state]** |
| `token.raw-value-lint` | **n/a** | `stylelint-declaration-strict-value` + a raw-hex/px grep. Without it every generated component gradually reintroduces literals and the token layer becomes decorative |
| `token.coherence-lints` | **n/a** | Six purity checks: (1) no font-family outside the direction's slots; (2) no raw colour values; (3) every colour resolves to this direction's ramps; (4) every duration/easing from this direction's motion set; (5) every radius from this direction's scale; (6) **if `elevation.model` is border-only or flat, zero shadow tokens referenced**. Lint 6 is the one that catches the incoherence humans actually notice |
| `token.license-manifest` | **n/a** | Per-font: family, foundry, licence class, file hash, source URL, attribution. Per-image: generator, model, plan tier, licence class, prompt. **Fonts are where the risk concentrates**: OFL permits self-hosting and bundling; Fontshare-class permits free commercial use but **forbids redistribution** (CDN link only, never vendored); commercial foundry faces are per-project and pageview-metered and must emit a **pre-launch blocker** |

### 7.13 Category O — Voice & delivery

| Item | Variants | Rationale |
|---|---|---|
| `system.voice-and-microcopy` | **10** | Tone descriptors, sentence-length target, **capitalisation rule** (sentence vs title case), button verb pattern, error-message pattern, forbidden-phrase list. Capitalisation alone is a token-level decision no colour system compensates for |
| `system.headline-length-budget` | derived | Character budgets per type role from measure × role size. **Prevents the classic failure where a beautiful hero breaks the moment real copy replaces the placeholder** |

---

