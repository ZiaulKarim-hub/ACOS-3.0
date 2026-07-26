## 7. The design system inventory

**Structure.** A direction is a **24-slot varying identity vector plus 2 invariant records** (§7.1 still lists 26 rows; two of them — `direction.reference-triangulation` and `type.viewport-endpoints` — are declared identical across all directions and therefore cannot vary). Everything else in the system is either (a) a pure function of that vector plus shared seed tables (Utopia multipliers, Carbon/M3 motion matrices, Leonardo contrast targets), or (b) a **direction-bound authored artefact** that carries a `directionId` and is validated against the vector but is not itself a scalar slot (icon family, logo lockup system, voice profile, artwork). This is the shipped USWDS `$theme-*` architecture applied to a generated system, and it is what makes 10 coherent directions tractable instead of 10 × 800 independent decisions. **[V — uswds/uswds `_settings-typography.scss`; adobe/leonardo README; utopia.fyi calculators]**

> **Correction recorded (this pass).** The previous text asserted "a 26-slot identity vector" and "everything else … is a pure function of that vector." Both were wrong as written: two of the 26 rows are invariant, and roughly thirty rows outside Category A carry pickable numbers rather than `derived`. The revision below adds a **Kind** column, a **Scope** column and a **Priority** column to every table in §7 so that neither claim has to be inferred. The architectural consequence — that direction-bound authored artefacts exist outside the hash-bearing vector — is stated explicitly in §7.0.3 and enforced by new lints 7–10 in §7.12.

**Scale reality check.** Real systems ship 250–350 *semantic* tokens, not 80. IBM Carbon v11: 258 named colour tokens + 24 layout + 34 type. Material 3: ~50 colour roles, 15 typescale roles × 5 properties, 16 durations + 10 easings, 12 shape, 6 elevation, 4 state-layer opacities. Fluent 2: ~300 alias tokens. **Budget ~600–900 resolved tokens per complete direction. [V — counted programmatically from carbon-design-system/carbon, material-web, microsoft/fluentui sources]** The user's "~80 items" is an *item* count; each item expands to 1–40 tokens.

---

### 7.0 How to read every table in §7

#### 7.0.1 Variant-count key (**Count** + **Kind**)

The single "Variants" number in the previous draft meant three different things in the same tables, and the key defined only one of them. It is now split into a **Count** and a **Kind**. Every numbered row in §7 carries exactly one Kind:

| Kind | What the number means | What the Step-2 prompt must request | What the editor renders |
|---|---|---|---|
| **`per-direction`** | **One value per direction. The count is 10 by construction** — it is the number of directions, not a menu the user chooses from. Writing 10 here is arithmetic, not a judgement | "Produce one of these for each of the 10 directions" | **No control inside a chosen direction.** The value is whatever this direction's value is |
| **`domain`** | **N mutually exclusive options.** Exactly one is in force at a time. Where N < 10 and the row is a direction slot, **several directions necessarily share a value** — this is expected, not a defect | "Choose one of the following N named options: …" (the N must be enumerated in the prompt) | A control **only** where Scope is `in-direction-repickable`; otherwise none |
| **`set`** | **N members, all delivered together.** Not alternatives. `color.gradient-set` **6** means *emit six gradients*, not *pick one of six* | "Emit all N members, named as follows: …" | A control only if the row is also `in-direction-repickable`, in which case the control picks *which member to use here*, never which members exist |
| **`derived`** | Computed from the direction vector + seed tables; the editor renders **no control** (`com.acos.pick.pickable: false`) | Not requested. Computed locally after ingest | Nothing |
| **`n/a`** | A policy, contract, or coverage checklist, not a choice | Requested as prose/JSON policy, never as options | Nothing |

**Worked disambiguation of the two rows that caused the confusion:**

- `color.gradient-set` **6** is Kind `set` — six named roles (hero wash, card sheen, text gradient, edge fade, radial glow, mesh base) that all ship in every direction. The correct prompt sentence is "emit six gradients".
- `cursor.personality` **6** is Kind `domain` — six mutually exclusive cursor personalities, of which each direction holds one. The correct prompt sentence is "pick one of six".

**Reconciliation with §20.1 (mandatory, was a live contradiction).** §7.1 gives `direction.signature-moment` a count of **10**, while §20.1 explicitly *excludes* "Ten 'signature moment' variants" in favour of 2–3 bespoke concepts. Both are now true and consistent because the Kind is stated: `direction.signature-moment` is **`per-direction`** — one signature moment *per direction*, ten in total because there are ten directions. What §20.1 excludes is a **`domain` of 10** — a catalogue the user picks a signature moment out of. §14.7's "2–3 bespoke concepts" describes how each single per-direction moment is *authored* (concept exploration inside one direction), not how many ship. **No further change required in §20.1; a one-line clarification there would be cheap and is recommended.**

#### 7.0.2 Scope key (**Scope**)

Scope answers the question the previous draft never answered per row: *once a direction is chosen, can the user change this?*

| Scope | Meaning | `$extensions['com.acos.pick'].scope` |
|---|---|---|
| **`direction-slot`** | Fixed by the chosen direction. One value per direction, authored or picked at generation time. **The editor renders no control.** Changing it means changing direction | `"direction-slot"` |
| **`site-global`** | Chosen once for the whole site and identical across all 10 directions. Survives a direction change. Examples: the contrast ladder, breakpoints, the token naming convention | `"site-global"` |
| **`in-direction-repickable`** | The user may re-pick inside a chosen direction, **but only from that direction's validity list**. This is what the Step-4 component/swap bar drives | `"in-direction-repickable"` |
| **`derived`** | Not a scope in the user-facing sense; recorded so the manifest is uniform. No control, ever | `"derived"` |

**The coherence rule (normative, and the thing that keeps D1 true).**

> Any row whose Scope is `in-direction-repickable` **must** ship a per-direction **validity list** in `token.capability-manifest`. Options absent from the active direction's list are **hidden from the editor UI, not merely warned about**. A row that cannot supply a validity list is **demoted to `direction-slot`** — it does not get a control "for now".

This is what stops the failure the audit named: a geometric-mono icon family being dropped onto an editorial-serif direction. `icon.family-spec` is `direction-slot`, so the control never exists; `art.background-scene` is `in-direction-repickable`, so the control exists but only shows pieces tagged for this direction. D1's guarantee ("derived values are computed from the direction, never picked independently") is therefore enforced by two mechanisms rather than one: `pickable: false` for derived values, and the validity list for repickable ones.

#### 7.0.3 Vector membership, and the "27th slot" problem

The audit correctly observed that if `icon.family-spec` is fixed by the direction then it is behaving as a 27th identity slot, and the vector definition is wrong. The resolution adopted here:

- **The hash-bearing identity vector is the 24 varying rows of §7.1.** Nothing else feeds `token.direction-hash`.
- **Direction-bound authored artefacts** (`icon.family-spec`, `mark.logo-lockups`, `mark.decorative-glyphs`, `system.voice-and-microcopy`, every `art.*` piece) are `direction-slot` in Scope, carry a `directionId`, and are **validated against** the vector by lints 7–10 — but they do **not** feed the hash.
- **Reason for the split (stated so it can be challenged):** the hash exists to detect cross-contamination during component swaps, and it must be cheap and stable to compute. Feeding a 6-lockup SVG system or a 40–80 word voice profile into the hash makes it brittle against whitespace, unicode and re-export noise for no detection benefit — the `directionId` already catches the contamination case. **[I — inference; this is a design decision made in this revision, not a cited practice]**

**Consequence to accept explicitly:** the identity of a direction is therefore *larger* than its hash. Two directions could share a vector hash and differ in icon family. Lint 8 (§7.12) catches that, and O34 records the residual risk.

#### 7.0.4 Priority key (**Priority**)

Same vocabulary as §8: **v1 / v2 / v3**. Added because §8 has a phase plan and §7 did not, which meant all 148 §7 items were implicitly v1 and implicitly requested in the Step-2 prompt — against a context budget §6.3 shows is already tight (~400KB / ~110K tokens against a 200K claude.ai context that artifacts count against). The v1 cut list, the resolved-token estimate, and what is deferred to Step-5 regeneration are in **§7.18**.

*Note on numbering: the audit suggested placing the cut list at "§7.14". It lands at §7.18 because three previously-missing categories (K, M and a new P) are restored at §7.14–§7.16 and the volume roll-up at §7.17. No existing §7.x number has moved, so cross-references into §7.1–§7.13 — including §20.1's reference to §7.7 — are unaffected.*

---

### 7.1 Category A — Direction core (the identity vector: 24 varying slots + 2 invariant records)

Every row here is Scope `direction-slot` by definition — that is what "identity vector" means. Kind still varies: `per-direction` rows hold a freely-authored value; `domain` rows hold one of N named options, so with N < 10 several directions necessarily share a value, and the divergence enforcement in §6.1 demand 9 must therefore work on the *combination*, not on any single slot.

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `direction.manifesto` | **10** | per-direction | direction-slot | v1 | 40–80 words naming the point of view, the tension it resolves, what it refuses to do. One per direction — this IS the direction. **10 = the direction count** |
| `direction.mood-tags` | **10** | per-direction | direction-slot | v1 | 3–6 tags from a closed ~30-term vocabulary, so tags are machine-comparable for artwork affinity and Step-5 queries. The closed vocabulary is itself `site-global`; the *selection* is per-direction |
| `direction.reference-triangulation` | **n/a** | n/a | site-global (invariant record) | v1 | ≥3 named references per direction, **abstracted attributes only** (proportion, contrast strategy, rhythm) — no reference pixels retained. Provenance metadata; also the trade-dress safety measure. **Not a varying slot** — it is a record attached to each direction, which is why the vector is 24 varying, not 26 |
| `direction.signature-moment` | **10** | per-direction | direction-slot | v1 | One per direction, specified as intent + trigger + duration budget. Award-tier work has exactly one; three reads as noise **[V — prior report Findings 2, 6]**. **Kind is `per-direction`, which is why this is compatible with §20.1's exclusion of a 10-option catalogue** — see §7.0.1 |
| `typeface.display` | **10** | per-direction | direction-slot | v1 | The loudest identity carrier. If two directions share it they are not two directions. **10 = the direction count**, drawn from the pinned OFL shortlist (§6.1 demand 4) |
| `typeface.body` | **10** | per-direction | direction-slot | v1 | Ten slots that may resolve to as few as 5 distinct faces — directions can legitimately share a body face |
| `typeface.mono` | **5** | domain | direction-slot | v1 | Small, low-identity surface. Five moods span it: grotesque-mono, typewriter, terminal/bitmap, humanist, geometric. **Directions map many-to-one onto these five** (§20.2 #6) |
| `typeface.accent` | **10** | per-direction | direction-slot | v1 | One per direction *including "none"*. Making null explicit stops the generator adding a decorative face reflexively |
| `type.base-size-pair` | **10** | per-direction | direction-slot | v1 | Min/max body size. "Big generous type" vs "small dense type" is identity, and Utopia takes it as explicit input |
| `type.scale-ratio-pair` | **10** | per-direction | direction-slot | v1 | Min-viewport and max-viewport modular ratios. Where hierarchy drama lives; a pair, not a scalar |
| `color.hue-anchors` | **10** | per-direction | direction-slot | v1 | OKLCH angles for primary/secondary/tertiary/accent. Hue *relationships* (analogous/complementary/split/mono+accent) are the defining colour decision |
| `color.chroma-policy` | **10** | per-direction | direction-slot | v1 | Ceiling + curve across the lightness ramp. Separates muted-editorial from neon-arcade at identical hues |
| `color.neutral-temperature` | **4** | domain | direction-slot | v1 | Pure grey / warm / cool / tinted-by-primary. Four genuinely distinct options; more is false precision. **Ten directions draw from four options, so sharing is expected** |
| `color.scheme-strategy` | **10** | per-direction | direction-slot | v1 | Light-first / dark-first / dual-equal, plus which scheme the art was authored against. Determines which gets the hand-tuned solve. *(The three strategy names are a domain of 3; the slot value is the strategy **plus** the authored-against declaration, which is per-direction — hence Kind `per-direction`.)* |
| `density.base-unit` | **4** | domain | direction-slot | v1 | 2, 4, 6 or 8px. Only four are used in practice; 8 with a 4 half-step is the common default. **Ten directions over four options** |
| `space.scale-ratio` | **10** | per-direction | direction-slot | v1 | The multiplier table. Airy vs tight is identity — but only the *ratio* is picked; the 9 values are derived |
| `shape.radius-policy` | **6** | domain | direction-slot | v1 | Sharp-0 / subtle / soft / pill-full / squircle / asymmetric-per-corner. Six distinct corner languages |
| `shape.border-policy` | **5** | domain | direction-slot | v1 | Hairline / heavy rule / none / double-offset / plus base width. Interacts hard with elevation model — validate the pair |
| `elevation.model` | **5** | domain | direction-slot | v1 | Shadow-physical (Fluent two-light) / tint+shadow (M3 dp) / layer-only (Carbon) / border-only / glass-backdrop. **The item whose mismatch causes the most invisible incoherence** — a border-only direction must reference zero shadow tokens, and lint 6 enforces it |
| `motion.expressiveness` | **10** | per-direction | direction-slot | v1 | A single 0–1 scalar plus a productive/expressive flag that scales the whole duration and easing matrix. Carbon ships exactly this axis, which is why 16 durations and 10 easings below are `derived` |
| `grid.personality` | **10** | per-direction | direction-slot | v1 | Column intent, symmetry, whether content breaks the grid, gutter:margin proportion, baseline enforcement. Top-tier identity signal, not derivable. **10 = the direction count** |
| `surface.background-art-style` | **10** | per-direction | direction-slot | v1 | The user's named FruitSync item. Medium (flat/gradient/illustrated/pattern/noise/canvas), density, scroll behaviour, token re-skinnability. Largest continuous surface on any page |
| `texture.grain-policy` | **5** | domain | direction-slot | v1 | None / trace / film / coarse / halftone. Amplitude derived from level. *Distinct from `effect.noise-grain` (§7.6), which is the set of generator recipes this policy selects an amplitude on* |
| `imagery.treatment` | **10** | per-direction | direction-slot | v1 | Grade, duotone mapping, crop rules, subject distance, grain — *including "no photography"*. Making the null explicit prevents stock-photo default behaviour. **Resolves to one of the 8 `art.photo-grade-recipe` chains (§7.9) plus per-direction crop/distance rules — see §7.19** |
| `cursor.personality` | **6** | domain | direction-slot | v1 | **The six (enumerated, was missing):** (1) native-only, (2) custom-static single cursor, (3) custom-static with a hover/pressed cursor set, (4) follower-dot (native hidden, JS-tracked element), (5) follower-with-morph (magnetic snap to interactive targets), (6) hybrid (native cursor retained + decorative trailing layer). **Hard browser limits:** capped at 128×128 in Firefox and Chromium (32×32 recommended), PNG or static SVG 1.1 only, hotspot x/y from top-left, and a native keyword fallback is **mandatory** — a url-only cursor is invalid CSS **[V — MDN cursor]**. Options 4–6 additionally require a pointer-coarse opt-out and a reduced-motion variant |
| `type.viewport-endpoints` | **n/a** | n/a | site-global (invariant record) | v1 | 360 → 1440. Device facts. Must be identical across all directions or they become non-comparable in the editor preview. **Not a varying slot** — second of the two invariant records |

**Vector membership statement (feeds `token.direction-hash`, §7.12):** the 24 rows above excluding `direction.reference-triangulation` and `type.viewport-endpoints`, hashed **in the exact table order above** over a canonical serialisation defined in §7.12. Nothing outside this table feeds the hash.

### 7.2 Category B — Colour tokens (mostly derived)

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `color.primitive-ramps` | derived | derived | derived | v1 | Leonardo model: declare colorKeys + target ratios, **solve** for colours. Picking swatches by eye is the exact failure Leonardo removes |
| `color.ramp-step-count` | derived | derived | derived | v1 | Falls out of the contrast ladder: as many steps as distinct targets plus interpolation headroom (10–13 typical) |
| `color.surface-roles` | derived | derived | derived | v1 | background, surface, surface-dim, surface-bright + a **5-step container ladder** (lowest/low/base/high/highest). The ladder is what makes dark mode readable; a single background+card pair is the #1 amateur tell |
| `color.text-roles` | derived | derived | derived | v1 | 12 roles: primary, secondary, tertiary, placeholder, helper, disabled, inverse, on-color, on-color-disabled, error, link, visited |
| `color.border-roles` | derived | derived | derived | v1 | subtle (per layer 00–03), strong (per layer), interactive, disabled, inverse, tile, focus, divider — ~16, all lightness offsets from their layer |
| `color.icon-roles` | derived | derived | derived | v1 | 7 roles at a fixed +0.5:1 contrast offset from text (thin strokes need more) |
| `color.brand-roles` | derived | derived | derived | v1 | ~20: primary/on-primary/primary-container/on-primary-container × 3, plus M3's `fixed` and `fixed-dim` variants that persist across schemes |
| `color.status-roles` | derived | derived | derived | v1 | error, warning, success, info, caution-major, caution-minor + inverse + container + on-container. Status hues are near-universal; only chroma and temperature adjust |
| `color.state-layer-opacities` | derived | derived | derived | v1 | **4 numbers replace Carbon's ~60 state-suffixed colour tokens.** M3 verified: hover 0.08, focus 0.12, pressed 0.12, dragged 0.16. Seeded from M3, scaled by expressiveness ² |
| `color.focus-ring` | derived | derived | derived | v1 | Outer + inner ring (two-tone so it reads on any surface — Fluent ships `colorStrokeFocus1/2`), width, offset, style, radius-follow, on-image variant. **Geometry fixed by WCAG 2.2 SC 2.4.13**: ≥ the area of a 2px perimeter, ≥3:1 focused-vs-unfocused. Never pickable |
| `color.scheme-declaration` | derived | derived | derived | v1 | **NEW (closes the sixth "invisible surface" — the one still missing after the previous pass).** The root `color-scheme` declaration (`light`, `dark`, or `light dark`) emitted from `color.scheme-strategy`. **It is the token the other five depend on:** `accent-color` on native controls and any `scrollbar-color: auto` fallback resolve against the UA scheme, so without it a dark direction renders light native selects, date pickers and scrollbars — the exact one-second amateur tell `color.scrollbar`/`color.accent-color` were added to prevent. It is also the enabling declaration for `light-dark()`. **Emission form:** `color-scheme` on `:root` always; `light-dark()` used for role values **only** where the compiler target supports it — Style Dictionary/Terrazzo output shape must be checked against `token.compiler-target`, and where it is not safe, per-scheme role values are emitted instead (the existing `color.dark-scheme-values` path) **[I — the dependency chain is inference from how UA scheme resolution works; verify the emitted form against the pinned compiler at pin time, O33]** |
| `color.selection` | derived | derived | derived | v1 | `::selection` bg + fg with **per-scheme alpha**. Primer ships 0.2 light / 0.7 dark — nobody guesses this **[V — primer selection.json5]** |
| `color.caret` | derived | derived | derived | v1 | One value, contrast-checked against field backgrounds. Trivial, universally forgotten |
| `color.scrollbar` | derived | derived | derived | v1 | `scrollbar-color` thumb + track + hover + width. Baseline newly-available Dec 2025; auto-reverts under forced-colors. A default OS scrollbar on a dark cinematic site is an immediate tell **[V — MDN scrollbar-color]** |
| `color.accent-color` | derived | derived | derived | v1 | One declaration themes every unstyled native checkbox/radio/range/progress. **Resolves against `color.scheme-declaration`** |
| `color.overlay-scrim` | derived | derived | derived | v1 | Backdrop colour + alpha + optional blur. Glass model gets blur, flat model gets flat alpha |
| `color.skeleton` | derived | derived | derived | v1 | Base + shimmer. Needed the moment any component has a loading state |
| `color.shadow` | derived | derived | derived | v1 | Ambient + key colours, tinted not pure black. Pure-black shadows are the flattest default and should be impossible to emit |
| `color.gradient-set` | **6** | **set** | direction-slot | v1 | **Six named roles, all six shipped in every direction — not a menu.** hero wash, card sheen, text gradient, edge fade, radial glow, mesh base. Six named roles covers real usage without becoming an unaudited library. Prompt sentence: "emit six gradients, named as above" |
| `color.dark-scheme-values` | derived | derived | derived | v1 | **A full second solve, not an inversion.** M3 ships per-scheme role values; Carbon ships four themes (white/g10/g90/g100), not two inverted ones. Flipping L produces the classic over-saturated halating dark mode |
| `color.high-contrast-scheme` | derived | derived | derived | v2 | Third solve at an elevated contrast multiplier via `prefers-contrast: more`. Literally one parameter change in Leonardo |
| `color.forced-colors-mapping` | **n/a** | n/a | site-global | v1 | Which elements opt out of `forced-color-adjust`, where borders must be re-added, which decorative layers hide. Dictated by OS keywords, but must be an explicit checklist — forced-colors silently deletes background-based affordances. **A forced-colors render check belongs in the LOCK gates (§13); it is a media-query render, not a new tool. Recorded as required §13 addition — see A91** |
| `color.print-scheme` | derived | derived | derived | v2 | Light scheme with chroma flattened, link URLs expanded, page breaks, decorative layers suppressed |
| `color.syntax-highlight` | **4** | domain | direction-slot | v2 | light-classic, light-muted, dark-classic, dark-vivid, mapped from direction hues. Each direction resolves to one light + one dark member of this domain. Carbon ships ~90 syntax tokens; 12 roles suffice for a marketing site |

### 7.3 Category C — Typography

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `type.role-set` | derived | derived | derived | v1 | ~18 roles (display/headline/title/body/label L·M·S + caption, overline, quote, code, lede) × 5 properties = ~90 values, all computable from typeface picks + scale ratio |
| `type.scale-steps` | derived | derived | derived | v1 | Pure Utopia math from 6 inputs. Hand-picking a step is how a scale loses its ratio |
| `type.weight-plan` | derived | derived | derived | v1 | Hard-capped at 4 static weights or 1 variable file per family. A weight exists only if a role references it |
| `type.line-height-map` | derived | derived | derived | v1 | Deterministic inverse function of size. M3 verified: display-large ≈1.12, body-small ≈1.33 |
| `type.tracking-map` | derived | derived | derived | v1 | **Sign flips with size** — M3 verified: display-large −0.015625rem, body-small +0.025rem. One derived curve reproduces the whole map |
| `type.measure` | derived | derived | derived | v1 | 60–75ch body, 45–60ch lede, ~40ch pull quote. Enforceable as a lint on the built page |
| `type.fallback-metrics` | derived | derived | derived | v1 | Local `@font-face` with `size-adjust`, `ascent-override`, `descent-override`, `line-gap-override` from the **real font file's metrics**. **Computed by the skill after the typeface pick, never requested from claude.ai** — it needs the actual file. Highest-leverage invisible token family for CLS |
| `type.loading-strategy` | **3** | domain | site-global (per-face override permitted) | v1 | swap+preload / optional / block-with-100ms-cap. **Chosen once for the site**, because a mixed strategy across faces produces inconsistent first paint. Constrained by licence class: OFL may be self-hosted; Fontshare-class must be CDN-linked and never vendored — so a per-face override is permitted **only** where the licence class forces it, and the override is recorded in `token.license-manifest` |
| `type.text-wrap-policy` | **n/a** | n/a | site-global | v1 | `balance` for headings, `pretty` for prose, `stable` for editable. Baseline Oct 2024, and the correct answer is universal. Hard limits make it non-negotiable: `balance` applies only to ≤6 lines in Chromium / ≤10 in Firefox; `pretty` has a documented performance cost **[V — MDN text-wrap-style]**. **Lint: reject `text-wrap: balance` on any block that renders >6 lines at any of the five breakpoints** — see A92 |
| `type.numeral-style` | **4** | domain | direction-slot | v1 | lining-proportional (prose), lining-tabular (data), oldstyle-proportional (editorial), oldstyle-tabular. The direction holds the *default*; **tabular is forced by context in tables, stat bands and price columns regardless of the direction's default** — that override is derived, not picked. Validate the pick against the chosen face's support |
| `type.emphasis-policy` | **6** | domain | direction-slot | v1 | True italics / small caps / weight shift / colour shift / letterspaced uppercase / forbidden-list. **Declaring the forbidden ones matters more** — faux-italic on a face without an italic is a visible defect. *(The "forbidden-list" member is the policy's escape hatch and is always present alongside whichever of the other five is chosen.)* |
| `type.underline-style` | derived | derived | derived | v1 | thickness, offset, skip-ink, hover/visited transitions, from the body face's stroke weight and x-height. Default browser underlines are one of the most reliable amateur signals |
| `type.list-marker-style` | **6** | domain | direction-slot | v1 | disc, dash, custom glyph, numeral-in-shape, icon, none-with-indent. Lists appear on every content page; default markers undo a lot of typographic work |
| `type.quote-treatment` | **6** | domain | direction-slot | v1 | **The six (enumerated):** (1) hairline rule + indent, (2) oversized quotation mark, (3) plain indent with size bump, (4) colour block / tinted panel, (5) hanging-punctuation editorial, (6) full-bleed display quote. Each carries attribution styling and the quote glyph set for the direction's faces |
| `type.lede-and-dropcap` | **5** | domain | direction-slot | v1 | Lede bump / drop cap / raised cap / none / small-caps-opening. Editorial directions use it; product directions must not |
| `type.prose-rhythm` | derived | derived | derived | v1 | Heading-to-body margins, list spacing, figure/caption spacing. Hand-tuning is how rhythm dies |
| `type.script-and-rtl-coverage` | **n/a** | n/a | site-global | v1 | Declared coverage per face, logical properties (`inline-start`/`end`, never left/right), RTL mirroring rules. A correctness requirement — retrofitting logical properties is expensive, and this project has already paid that bill once. **Extended by Category K (§7.14)** |

### 7.4 Category D — Space, size, layout

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `space.scale-steps` | derived | derived | derived | v1 | 9 fluid steps 3xs…3xl. Utopia default multipliers verified: 0.25 / 0.5 / 0.75 / 1 / 1.5 / 2 / 3 / 4 / 6 relative to base **[V — utopia.fyi/space/calculator]** |
| `space.one-up-pairs` | derived | derived | derived | v1 | 8 pairs that grow one step across the viewport range. What makes *spacing* responsive, not just type |
| `space.custom-pairs` | derived | derived | derived | v1 | Named non-adjacent pairs (e.g. s-l) for section padding. Typically 2–4 per site |
| `space.section-rhythm` | derived | derived | derived | v1 | **The single value most responsible for whether a page reads as composed or as stacked blocks** |
| `layout.breakpoints` | **n/a** | n/a | site-global | v1 | 320 / 390 / 768 / 1280 / 1440 authored; Primer's shipped set (320, 544, 768, 1012, 1280, 1400) as reference. Shared across all directions so the editor preview and D2's constraint model mean the same thing everywhere ³ |
| `layout.container-breakpoints` | **3** | **set** | site-global | v1 | **NEW — closes the container-query hole.** §11.5 mandates `container-type: inline-size` on every block wrapper with component internals written in `@container`, and A46 gates it, but no container-size thresholds existed anywhere. **The three named thresholds, derived from the 12-column module at the 1280 authoring breakpoint** (content 1200px, gap 24px → column 78px; a 3-col slot = 282px, a 6-col slot = 588px, a 12-col slot = 1200px): `cq-narrow` **< 20rem/320px** (≈ a 3-col slot and everything below), `cq-medium` **20rem–37.5rem / 320–600px** (≈ a 4–6-col slot), `cq-wide` **≥ 37.5rem/600px** (≈ 7-col and up). Emitted as literal `rem` in the `@container` conditions. **Constraint:** container-query size conditions do not accept `var()`, so these thresholds cannot be referenced as custom properties inside the condition — the build step must inline them, and `token.raw-value-lint` must **exempt** `@container` preludes or every component will fail the raw-value grep **[I — the `var()` limitation is stated from working knowledge and is load-bearing; verify before implementation, O33]** |
| `layout.container-name-registry` | **n/a** | n/a | site-global | v1 | **NEW.** The closed list of `container-name` values a component may query (`wb-section`, `wb-block`, `wb-media`, `wb-card`, `wb-form`), plus the rule that a component queries only its **nearest named ancestor**. Without a registry, two components pick the same generic name and one silently queries the wrong ancestor — a defect with no error and no visual signal until a drag moves the component. **Lint 10 (§7.12) enforces membership** |
| `layout.container-widths` | derived | derived | derived | v1 | prose (= measure × body size), wide, full-bleed, editorial-narrow — multiples of the column module |
| `layout.grid-definition` | derived | derived | derived | v1 | Columns, gutters, margins per breakpoint + named area templates. **Critical for D2: these are what components SNAP to**, so they must be a real token set the editor reads, not decorative overlay. **The column module here is the basis for `layout.container-breakpoints` above** |
| `layout.gap-scale` | derived | derived | derived | v1 | Subset of the space scale, called out because gap and padding get conflated then drift |
| `layout.aspect-ratio-set` | **8** | **set** | in-direction-repickable (validity list = all 8 in every direction) | v1 | 1:1, 4:3, 3:2, 16:9, 21:9, 4:5, 9:16, golden. **All eight ship in every direction; the per-instance choice of which to use is the repickable part.** Constraining media to a named set is what keeps a gallery from looking hand-assembled |
| `size.icon-sizes` | derived | derived | derived | v1 | From cap-height of the adjacent type role, not from the space scale — so icons optically match text |
| `size.control-heights` | derived | derived | derived | v1 | line-height + padding + border, floor-clamped by the 24×24 target minimum |
| `size.min-target-size` | **n/a** | n/a | site-global | v1 | 24×24 CSS px (WCAG 2.2 SC 2.5.8, AA) with five exceptions: spacing, inline, user-agent control, equivalent, essential. The **spacing** exception (a 24px circle on each target must not intersect another) is what the editor checks after a drag |
| `size.avatar-sizes` | derived | derived | derived | v2 | Diameter steps + overlap offset for groups. Only if the site has people on it |
| `layout.safe-area-and-viewport` | **n/a** | n/a | site-global | v1 | `env(safe-area-inset-*)`, dvh/svh/lvh, scroll-padding for sticky headers. 100vh on mobile and anchor links landing under a sticky header are two of the most common shipped defects |

### 7.5 Category E — Layers & plumbing

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `layout.z-index-scale` | **n/a** | n/a | site-global | v1 | Primer's verified ladder adopted verbatim: behind (−1), default, sticky (100), dropdown (200), overlay (300), modal (400), popover, skipLink (top). **Note the two non-obvious orderings**: dropdowns above sticky headers but below modals, and skipLink outranks everything because accessibility wins **[V — primer z-index.json5, quoted]** |
| `layout.stacking-context-rules` | **n/a** | n/a | site-global | v1 | Which properties create stacking contexts (transform, opacity<1, filter, will-change, backdrop-filter) and the rule that animated/parallax art containers must not enclose overlay-layer content. **This bites hard here specifically because D4 puts animations inside draggable containers** — a transformed art container silently traps every dropdown inside it, and presents as "the menu is behind the picture" with no obvious cause |
| `layout.editor-chrome-band` | **n/a** | n/a | site-global | v1 | A reserved band **above** skipLink for gridlines, drag handles, snap guides, component bar — plus the guarantee that LOCK strips the entire band. If editor chrome shares the site's ladder there is no clean way to *prove* it was removed (D3) |

### 7.6 Category F — Shape, surface, effect

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `shape.radius-scale` | derived | derived | derived | v1 | M3 verified: none 0, xs 4, s 8, m 12, l 16, xl 28, full 9999 + directional variants (top, start, end) for sheets and grouped controls |
| `shape.per-corner-recipes` | **8** | **set** | in-direction-repickable (validity list per direction) | v1 | leaf, ticket, tab-top, notch, chamfer, squircle, single-cut, pill-end. Cheap distinctiveness; more than 8 is an unusable menu. **A sharp-0 direction's validity list will legitimately be short — that is the coherence rule working, not a bug** |
| `shape.border-width-scale` | derived | derived | derived | v1 | Four steps doubling from base. Must be integer px at 1× to avoid sub-pixel hairline blur |
| `shape.stroke-style-set` | **4** | **set** | direction-slot | v1 | **The four (enumerated, was missing):** (1) `solid`, (2) `dash-designed` — an explicit `dashArray` tuned to the direction's radius scale so dashes land on corners rather than being cut by them, (3) `dot-round` — round `lineCap` dot rhythm, (4) `tick-segmented` — long-short repeating rule for technical/editorial directions. DTCG supports a custom `dashArray`/`lineCap` object, which is what makes a *designed* dash possible rather than the browser default |
| `shape.divider-treatment` | **8** | domain | in-direction-repickable (validity list per direction) | v1 | hairline, heavy rule, gradient fade, shape/wave cut, colour-block change, whitespace only, overlap, ticket-notch. **Section transitions are where long pages read as one composition or as a stack.** *This is the CSS/token-level seam treatment. It is a different layer from `art.section-divider-shapes` (the SVG path library it may reference) and from §8's "Section divider / seam" component (the composed block) — see §7.19* |
| `shape.clip-and-mask-shapes` | **10** | **set** | in-direction-repickable (validity list per direction) | v1 | **All ten now named — the previous "+2" TBD is resolved:** blob, arc, angle, wave, torn, circle-reveal, hex, custom-brand, **stadium-slab**, **stepped-stair**. Normalised path data so they scale; directly reusable by D4's art containers |
| `elevation.shadow-scale` | derived | derived | derived | v1 | Multi-layer via the **DTCG shadow ARRAY form** — a realistic 3-layer shadow is ONE token, which is exactly what separates designed depth from `box-shadow` defaults |
| `elevation.inner-shadow` | derived | derived | derived | v1 | Inverted and reduced from the outer scale. Needed for pressed states in physical models |
| `effect.blur-scale` | derived | derived | derived | v1 | From the space scale. **Carries a performance note**: `backdrop-filter` on a large scrolling surface is main-thread cost, and main-thread work is the actual performance failure axis |
| `effect.backdrop-recipe` | **6** | domain | direction-slot | v2 | **The six (enumerated):** (1) clear-glass (blur only), (2) frosted (blur + saturation), (3) tinted-glass (blur + tint alpha), (4) frosted-with-edge (blur + saturation + border highlight), (5) heavy-frost (high blur, low transparency), (6) dark-glass (blur + darkening overlay for light-on-dark chrome). **Lint 6 rejects all six in a border-only or flat direction** |
| `effect.opacity-scale` | derived | derived | derived | v1 | 5–7 steps from the state-layer opacities. Ad-hoc opacity is a top source of contrast failures because it bypasses the solver |
| `effect.noise-grain` | **8** | **set** | in-direction-repickable (validity list per direction) | v2 | **The eight (enumerated, was missing):** fine-film, coarse-film, halftone-dot, halftone-line, riso-speckle, paper-fibre, dust-and-scratch, chroma-noise. Prefer SVG `feTurbulence` over raster tiles — grain re-colours with the direction and costs no bytes. *Amplitude comes from `texture.grain-policy`; this row is the recipe library that policy selects from* |
| `effect.gradient-mesh` | **8** | **set** | in-direction-repickable (validity list per direction) | v2 | **The eight (enumerated, was missing) — named by blob topology, not by colour:** two-pole, three-pole-triangle, corner-wash, radial-core, ribbon-diagonal, aurora-band, orbit-cluster, edge-halo. Specified as **blob positions + hue assignments, not baked images**, so the mesh re-skins when hues change in Step 5 |
| `effect.pattern-tiles` | **12** | **set** | in-direction-repickable (validity list per direction) | v1 | grid, dot, hatch, halftone, isometric, topographic, stripe, chevron, scatter, weave, circuit, custom-brand. SVG using `currentColor`. The cheapest way to make a large empty surface feel authored |
| `effect.blend-mode-policy` | **6** | domain | direction-slot | v2 | **The six (enumerated):** (1) none-permitted, (2) multiply-only (ink/print directions), (3) screen/lighten-only (dark cinematic), (4) overlay-on-imagery-only, (5) difference/exclusion for a single signature moment, (6) luminosity-for-duotone. Must be a POLICY because blend modes create stacking contexts and can silently break the overlay ladder |

### 7.7 Category G — Motion (system items, per D4)

See §9 for the full motion/container treatment. Token-level items:

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `motion.duration-scale` | derived | derived | derived | v1 | Seed from **Carbon's verified 6-step set**: fast01 70ms, fast02 110, moderate01 150, moderate02 240, slow01 400, slow02 700; scale by expressiveness. **Primer's hard lint applies as a build gate**: UI interactions ≤300ms, never >500ms; decorative motion exempt but must be tagged **[V — carbon packages/motion/src/index.ts; primer motion.json5 quoted]** |
| `motion.easing-set` | derived | derived | derived | v1 | **Carbon's 3×2 matrix IS the derivation**: standard/entrance/exit × productive/expressive; one expressiveness flag selects the whole column. Verified values at both endpoints so interpolation is safe |
| `motion.spring-presets` | derived | derived | derived | v2 | Tension/friction/mass + a mapping from each easing token to its nearest spring. **DTCG has no native spring type** — requires a `$extensions.acos.spring` namespace, and every tool in the chain must agree on its shape or springs silently degrade |
| `motion.transition-presets` | derived | derived | derived | v1 | DTCG `transition` composite bundling duration+delay+timingFunction. One token = one CSS declaration, which stops a builder pairing a fast duration with a slow curve |
| `motion.stagger-policy` | derived | derived | derived | v1 | Delay increment as a fraction of base duration, plus **the cap** beyond which stagger becomes a single group animation. The cap is the important part — uncapped stagger on a 40-item grid makes the last item arrive seconds late |
| `motion.distance-tokens` | derived | derived | derived | v1 | **Bound to the spacing scale**, never arbitrary translateY values, so motion moves a visually consistent amount relative to the same grid the layout snaps to. Extends D1's computed-not-picked rule into motion |
| `motion.choreography-rules` | **n/a** | n/a | site-global | v1 | Meta-rules: exits use accelerate and finish faster than entrances use decelerate; stagger follows reading order; only one pinned sequence and one ambient layer per viewport |
| `motion.reduced-motion-variants` | **n/a** | n/a | site-global | v1 | **Mandatory pairing.** Art-directed (cross-fades, poster frames, instant states), not `animation: none`. Must be authored at generation time — the editor cannot invent a good one |

### 7.8 Category H — Iconography & marks

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `icon.family-spec` | **10** | per-direction | **direction-slot** | v1 | **One family spec per direction; 10 = the direction count, not a menu.** Grid size, keyline shapes, stroke weight, terminal style, corner radius, optical-size behaviour, whether strokes scale. Icons appear everywhere so a mismatched family is the most pervasive incoherence available — **which is exactly why Scope is `direction-slot` and the editor renders no re-pick control.** This is a direction-bound authored artefact (§7.0.3): identity-carrying but outside the hash-bearing vector, validated by lint 7. *Reconciles with §8's "Icon set 20" — see §7.19* |
| `icon.style-variants` | derived | derived | derived | v1 | Outline / filled / duotone **plus the selection rule** (filled = active nav, outline = inactive). The rule is the load-bearing part; mixing arbitrarily is a common tell |
| `icon.core-set` | **~50** | **set** | site-global | v1 | **A coverage checklist, not alternatives — all ~50 glyphs ship in every family.** menu, close, chevron ×4, arrow ×4, external-link, search, check, minus, plus, info, warning, error, success, user, mail, phone, location, calendar, clock, download, upload, share, copy, link, play, pause, mute, fullscreen, filter, sort, grid, list, settings, star, heart, cart, bookmark, edit, trash, refresh, lock, eye, eye-off, drag-handle, more-h, more-v + social. **Missing icons are discovered at build time and force an off-system substitution** |
| `icon.alignment-rules` | derived | derived | derived | v1 | Optical centring, cap-height vs x-height alignment, inline gap. The **RTL mirroring list is explicit data** (arrows mirror, clocks do not) and cannot be inferred |
| `mark.logo-lockups` | **10 × 6** | per-direction, each a set of 6 | direction-slot | v1 ⁴ | **Ten lockup *systems*, one per direction; each system ships the same six arrangements:** wordmark, symbol, horizontal, stacked, monogram, mono/inverse — plus clear-space, min-size and mono/inverse rules. Clear-space and min-size derive from the mark's geometry. **This is the reconciliation of §7's "10" with §8's "Logo lockup set 6": 10 systems × 6 members. Neither number was wrong; the axis was unstated** |
| `mark.favicon-set` | derived | derived | derived | v1 | `favicon.svg` with a dark-mode media query **inside the SVG**, 32px ICO, 180px apple-touch, 192/512 maskable (safe zone required), manifest theme colours. Routinely missing from AI-built sites |
| `mark.social-share-image` | **6** | **set** | direction-slot | v1 (3 of 6) / v2 (remaining 3) | 1200×630 OG + Twitter card, **parameterised template not a static file** so per-page images generate automatically. **The six templates:** hero-title, title+mark, quote, stat, product-shot, article-with-author. §8's "OG / social share card template **3**" is the **v1 cut** of these six (hero-title, title+mark, article-with-author) — see §7.19. One generic OG image across a whole site is a visible shortcut |
| `mark.decorative-glyphs` | **10** | **set** | in-direction-repickable (validity list per direction) | v1 | **All ten now named — the previous list stopped at 8:** bullets, section symbols, ornaments, decorative arrows, underline squiggles, highlight strokes, asterisks, corner ticks, **end-of-article mark (colophon)**, **paired quote ornaments**. What makes a page feel drawn rather than assembled, at near-zero cost as inline SVG |

### 7.9 Category I — Imagery & artwork

**Read §17-R1 first.** claude.ai cannot produce raster images **[V — Anthropic, April 2026]**. The user's own cited exemplar (the FruitSync site background) is 231 PNGs exported from Unity by a hand-written batchmode exporter pulling the game's real procedural sprites **[V — `SiteAngryExport.cs`; `ls` of `/Users/zee/fruitsync-animated-variants/assets`]**. That art came from a pre-existing hand-drawn library, not from a chat.

Three honestly-labelled lanes:

- **Lane A — code-drawn art.** SVG scenes, CSS gradient meshes, canvas/WebGL noise fields, generative patterns. claude.ai is genuinely good at this, and it is on-brand-able because it is parameterised by tokens. **Also the only lane that Local Regeneration Mode (§6.5) can produce without any hand-carry**, which is what makes the volume roll-up in §7.17 survivable.
- **Lane B — asset ingestion.** Point the skill at an existing sprite/photo/illustration folder. **This is what actually made the FruitSync site work**, and Step 0 question C3 detects it. Zero hand-carry cost; the artwork already exists on disk.
- **Lane C — external raster generation.** Midjourney / FLUX / Recraft, per the prior report's asset-routing matrix. A **separate** hand-carry with its own licence manifest, explicitly scoped in or out per release. **Out of scope for v1 unless the user opts in (§7.17).**

**Volume warning (do not read this table as a v1 shopping list).** The counts below are the **full library targets**, and they sum to **130 pieces** — against §6.3's chunk budget of "ten directions plus 20 artworks ≈ 400KB" and D1's settled "20 artworks tagged by direction". That contradiction is real, it is quantified in **§7.17**, and its resolution **requires user sign-off (O31)**. Every row therefore carries a Priority and a lane, and the v1 hand-carry quota is fixed at 20 pieces in §7.18.

| Item | Count | Kind | Scope | Lane | Priority | Rationale |
|---|---|---|---|---|---|---|
| `art.container-contract` | **n/a** | n/a | site-global | — | v1 | **THE load-bearing item for D4.** Box sizing, aspect policy, anchor/pin, overflow, mask, scheme-awareness, motion-capable flag, reduced-motion poster, focal point, alt text, licence ref. Because animated pieces live in the same draggable containers as static art, **both must satisfy one contract** — otherwise the editor needs two drag models and the lock/export path forks. Must be specified BEFORE any artwork is generated |
| `art.background-scene` | **20** | **set** (library) | in-direction-repickable (filtered by affinity tag) | A (primary), B | v1 — **quota 8 of 20 hand-carried**; remainder Lane A on demand | Per D1, tagged by direction affinity. Each declares `palette-mode`: **token-referencing** art (`currentColor` / `var(--*)`) suits many directions and re-skins free; **baked-palette** art suits only its tagged directions. **Require ≥60% token-referencing** — that is what makes Step 5 cheap instead of a full art regeneration |
| `art.hero-artwork` | **20** | **set** (library) | in-direction-repickable (filtered by affinity tag) | A, B, C | v1 — **quota 6 of 20 hand-carried** | This asset IS the LCP element on most sites, so each variant carries a **pre-LCP transfer budget** |
| `art.spot-illustrations` | **20** | **set** (library) | in-direction-repickable (filtered by affinity tag) | A, B | v1 — **quota 6 of 20 hand-carried** | Built from a shared component vocabulary (same stroke, same palette slots) so the set reads as one hand. *Same deliverable as §8 Media's "Decorative spot-graphic set 20" — see §7.19* |
| `art.section-divider-shapes` | **12** | **set** | in-direction-repickable (validity list per direction) | A | v1 — Lane A, generated locally | wave, angle, arc, torn, layered, notch, blob, zigzag + flipped/inverted. Normalised SVG paths that stretch; token-coloured for both schemes. *The SVG path library referenced by `shape.divider-treatment`'s "shape/wave cut" option — see §7.19* |
| `art.texture-plates` | **12** | **set** | in-direction-repickable (validity list per direction) | A | v2 | paper, canvas, concrete, film-grain, halftone, riso misregistration, scan-lines, foil, gradient-map, fabric, ink-bleed, dust. **What breaks the flat-vector-gradient look that reads instantly as machine-generated** |
| `art.photo-grade-recipe` | **8** | domain | direction-slot (resolved from `imagery.treatment`) | A (filter chain, no assets) | v1 | CSS/SVG filter chain: exposure, contrast curve, duotone, grain, vignette, hue-shift toward the anchors. **The highest-leverage way to make sourced imagery look commissioned**, and the implementation of the ban on unstyled stock. *Identical deliverable to §8 Media's "Photography treatment 8"* |
| `art.crop-and-focal-policy` | derived | derived | derived | — | v1 | `object-fit`/`object-position` defaults + **per-image focal point** (a single draggable dot, not a crop rectangle — it degrades gracefully across every aspect ratio a reflow system produces) + `<picture>` art direction. Focal metadata is captured in the editor, not designed |
| `art.placeholder-strategy` | **4** | domain | site-global | A | v1 | LQIP / blurhash / dominant-colour / skeleton + reveal transition. **Chosen once for the site** — a mixed placeholder strategy reads as inconsistency during loading, which is exactly when a visitor is watching. **Must reserve the exact final box** via `aspect-ratio` or the placeholder causes the CLS it was meant to prevent |
| `art.avatar-style` | **8** | domain | direction-slot | A, B | v2 | **All eight now named — the previous list stopped at 5:** photo-circle, photo-rounded-square, illustrated, monogram, generated-geometric, silhouette, **ringed/status-bordered**, **duotone-graded photo**. Generated-geometric matters because it needs no assets |
| `art.3d-or-canvas-scene` | **6** | domain | direction-slot | A, C | v3 | **The six (enumerated, was missing):** (1) rotating product/object, (2) ambient particle field, (3) shader gradient plane, (4) scroll-scrubbed camera path, (5) Gaussian-splat capture embed, (6) 2D-canvas generative plane (no WebGL). WebGL/three.js or Gaussian-splat spec with a **mandatory GPU-tier ladder**: full / reduced / static poster via detect-gpu. Without it a 3D hero is a guaranteed gate failure on low-end devices |
| `art.empty-state` | **10** | **set** (art pieces) | in-direction-repickable (filtered by affinity tag) | A | v2 | Cheap once the spot-illustration vocabulary exists; always ships, never designed. *These are 10 **artwork pieces**; §8's "Empty state 8" is 8 **component layouts** that place one — see §7.19* |
| `art.error-state` | **10** | **set** (art pieces) | in-direction-repickable (filtered by affinity tag) | A | v2 | 404 + 500 art plus recovery layout. A real page a visitor will see; the host default undoes the whole system in one view. *§8 ships 404 **6** and 500 **3** as component layouts; these 10 are the art they place — see §7.19* |

### 7.10 Category J — Accessibility & compliance (system-level)

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `color.contrast-ladder` | **3** | domain | **site-global** | v1 | AA-floor / AA-generous / AAA. **Site-level policy chosen once and applied to all directions** — per-direction would let a pretty direction ship illegible text |
| `token.contrast-proof-table` | **n/a** | n/a | site-global | v1 | Every text/surface pairing with WCAG 2 ratio and APCA Lc, pass/fail against the ladder. Because Leonardo solves *to* the targets, this is all-pass by construction — **so any failure means a value was hand-edited, making the table a tamper detector as well as a proof** |
| `system.alt-text-policy` | **n/a** | n/a | site-global | v1 | Decorative (`alt=""`) vs informative rules + a **required alt field on every artwork record**, captured at generation time. Retrofitting at lock time fails because nobody remembers what the illustration was meant to convey |

### 7.11 Category L — Data visualisation

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `color.data-vis-categorical` | **3** | domain | **site-global** | v2 | Hues derive from the direction; the **ordering strategy** is the real pick: harmonic rotation / maximum perceptual distance / brand-first-then-distance. Three strategies, not ten palettes. **Site-global** because charts across a site must order series identically or the same series changes colour between pages |
| `color.data-vis-sequential` | derived | derived | derived | v2 | Monotonic lightness is a mathematical requirement; OKLCH makes it computable from the hue anchor |
| `color.data-vis-diverging` | derived | derived | derived | v2 | Two hues around a neutral midpoint **pinned to the actual surface colour** — that pinning is what stops diverging charts looking pasted on |
| `chart.structural-tokens` | derived | derived | derived | v2 | gridline, axis, tick, axis-label, annotation, reference-line, zero-line, tooltip surface, max-series cap. From border/text roles at reduced emphasis. **Without them charts read as a foreign component** |

**A direction with 3 brand hues cannot yield a 6-series categorical palette that is simultaneously on-brand, distinguishable, and colourblind-safe.** Every direction must therefore carry the dataviz sub-token set **from generation time**, not as a retrofit. The local `dataviz` skill already ships a form heuristic, a colour formula with a runnable validator, and a palette reference — reuse it rather than reinventing.

### 7.12 Category N — Token file contract

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `token.tier-architecture` | **n/a** | n/a | site-global | v1 | Three tiers: **primitive** (raw ramps, never referenced by components), **semantic** (role-named, the only tier components may reference), **component** (overrides only where a component genuinely deviates). Enforceable rule: no component CSS may reference a tier-1 token |
| `token.file-format` | **n/a** | n/a | site-global | v1 | DTCG 2025.10 JSON, `$type` declared or group-inherited, references via `{group.token}`, composite types wherever CSS has a composite property. **JSON-Schema-validatable — which is precisely what makes the Step-3 boundary safe** |
| `token.llm-extension-block` | **n/a** | n/a | site-global | v1 | `$extensions['com.acos.llm'] = {usage[], rules, antipatterns[]}` on every semantic token |
| `token.pick-extension-block` | **n/a** | n/a | site-global | v1 | **Extended this pass.** `$extensions['com.acos.pick'] = {pickable, slot, directionId, variantIndex, derivedFrom[], `**`countKind`**`, `**`scope`**`, `**`validityList`**`}`. `countKind` ∈ {`per-direction`, `domain`, `set`, `derived`, `n/a`} (§7.0.1); `scope` ∈ {`direction-slot`, `site-global`, `in-direction-repickable`, `derived`} (§7.0.2); `validityList` is **required and non-empty whenever `scope === "in-direction-repickable"`** and lists the option ids valid for `directionId`. The editor reads this to decide what to render a control for **and what to put in it** — without `scope` it could not decide at all, which is the defect this closes |
| `token.direction-hash` | **n/a** | n/a | site-global | v1 | `$extensions['com.acos.direction'] = {id, vectorHash}`. Builder rejects mismatches. **Hash input now specified (was undefined):** the **24 varying slots of §7.1 in table order**, excluding `direction.reference-triangulation` and `type.viewport-endpoints`; serialised as a JSON array of `[slotId, value]` pairs with **UTF-8 NFC normalisation, `\n` line endings, leading/trailing whitespace trimmed, internal whitespace runs collapsed to one space, and no case folding** (case is meaningful in a manifesto); numbers serialised with no trailing zeros; hashed with **SHA-256**, recorded as the first 12 hex characters. Direction-bound authored artefacts (§7.0.3) do **not** feed the hash. Without this paragraph two implementations disagree and every ingest fails the mismatch check with an error message that explains nothing |
| `token.naming-convention` | **3** | domain | **site-global** | v1 | Carbon role-state-suffix / Fluent camelCase-compound / Primer dotted-group. **Pick ONE globally**; mixing is why token files stop being greppable |
| `token.theme-structure` | **n/a** | n/a | site-global | v1 | Recommend the per-mode override pattern (Primer's `org.primer.overrides`) over separate files — the selection token proves it handles per-scheme alpha differences a file split makes easy to forget to mirror |
| `token.capability-manifest` | **n/a** | n/a | site-global | v1 | Root manifest: direction id + hash, **expected token count per group**, **expected artefact count per §7 row (Count × Kind, so the validator knows whether to expect 10 members or 1 of 10 options)**, **the per-direction validity list for every `in-direction-repickable` row**, schemes present, breakpoints, container-breakpoints, pickable slot list, artwork index with affinity tags, font licence classes. **The Count/Kind/Scope columns exist so this manifest can be generated mechanically from §7 rather than hand-maintained** |
| `token.compiler-target` | **n/a** | n/a | site-global | v1 | **Pinned explicitly.** Style Dictionary v4 has first-class DTCG support but **not** full 2025.10 (in progress in v5); Terrazzo supports the full format today. Emitting 2025.10 colour objects into v4 will fail **[V — styledictionary.com/info/dtcg; terrazzo.app docs; medium confidence on current version state]**. **Also decides whether `light-dark()` is a safe emission form for `color.scheme-declaration`** |
| `token.raw-value-lint` | **n/a** | n/a | site-global | v1 | `stylelint-declaration-strict-value` + a raw-hex/px grep. Without it every generated component gradually reintroduces literals and the token layer becomes decorative. **Documented exemptions (each must be narrow and listed, or the lint gets disabled wholesale): (1) `@container` size conditions, which cannot take `var()`; (2) `@media` breakpoint conditions, same reason; (3) `0` and `1px` hairlines in the border-width primitive; (4) the base64 font `src` in `@font-face`** |
| `token.coherence-lints` | **n/a** | n/a | site-global | v1 | **Ten purity checks (six existing, four added this pass):** (1) no font-family outside the direction's slots; (2) no raw colour values; (3) every colour resolves to this direction's ramps; (4) every duration/easing from this direction's motion set; (5) every radius from this direction's scale; (6) **if `elevation.model` is border-only or flat, zero shadow tokens referenced**; (7) **the icon family id on every emitted icon equals the active direction's `icon.family-spec` id** — this is what stops a geometric-mono family landing on an editorial-serif direction; (8) **every `in-direction-repickable` pick is present on the active direction's `validityList`** (a pick absent from the list is a hard fail, not a warning); (9) **every referenced artwork carries an affinity tag including the active direction id**; (10) **every `container-name` used is in `layout.container-name-registry` and every `@container` threshold is one of the three in `layout.container-breakpoints`**. Lint 6 is the one that catches the incoherence humans actually notice; lints 7–9 are what make the D1 coherence guarantee structural rather than aspirational |
| `token.license-manifest` | **n/a** | n/a | site-global | v1 | Per-font: family, foundry, licence class, file hash, source URL, attribution. Per-image: generator, model, plan tier, licence class, prompt. **Fonts are where the risk concentrates**: OFL permits self-hosting and bundling; Fontshare-class permits free commercial use but **forbids redistribution** (CDN link only, never vendored); commercial foundry faces are per-project and pageview-metered and must emit a **pre-launch blocker** |

### 7.13 Category O — Voice & delivery

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `system.voice-and-microcopy` | **10** | per-direction | direction-slot | v1 | **One voice profile per direction; 10 = the direction count, not a menu of 10 tones.** Tone descriptors, sentence-length target, **capitalisation rule** (sentence vs title case), button verb pattern, error-message pattern, forbidden-phrase list. Capitalisation alone is a token-level decision no colour system compensates for. Direction-bound authored artefact (§7.0.3) — identity-carrying, outside the hash |
| `system.headline-length-budget` | derived | derived | derived | v1 | Character budgets per type role from measure × role size. **Prevents the classic failure where a beautiful hero breaks the moment real copy replaces the placeholder** |

---

### 7.14 Category K — Internationalisation, locale & content shape (**restored**)

> **Why this subsection exists.** The category letters in §7 skipped **K** and **M**: A, B, C, D, E, F, G, H, I, J, **L**, **N**, O. Neither letter appears anywhere in the PRD and neither is listed in §20.1's deliberate-exclusions table, which exists precisely so that dropped items are *traded, not lost*. Two missing letters in a lettered scheme is direct evidence that two categories were cut during editing without passing through the exclusions table. **This pass cannot recover what K and M originally contained — that information is not in the surviving text, and no source for it exists. What follows is a reconstruction, not a recovery**, populated from the families the audit identified as having no home anywhere in §7. **Requires user sign-off (O35): confirm that internationalisation and sonic identity are the intended contents, or supply what K and M actually were.** Subsection numbers are appended (7.14, 7.15) rather than inserted so no existing §7.x cross-reference moves; the letters are therefore out of numeric order, which is recorded deliberately.

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `i18n.locale-set` | **n/a** | n/a | site-global | v1 | The declared list of locales the site ships, each with script, direction (ltr/rtl), and date/number formats. Everything else in this category is a function of it. Declaring "en only" explicitly is a valid and cheap answer — what is expensive is discovering a second locale after LOCK |
| `i18n.string-expansion-budget` | **n/a** | n/a | site-global | v1 | +35% string expansion allowance applied to every component's text slot, matching §8's pseudolocalisation state. Without a stated budget, "it fits" is measured against English and a German nav breaks the ribbon. This is the token-level counterpart of §8's state |
| `i18n.rtl-mirroring-rules` | **n/a** | n/a | site-global | v1 | Explicit per-icon and per-component mirroring data (arrows mirror, clocks and logos do not), logical-property enforcement, and the rule that a mirrored layout is a **render target in the LOCK gate**, not a CSS afterthought. Overlaps `type.script-and-rtl-coverage` (§7.3) by design: that row owns *font coverage*, this row owns *layout mirroring* |
| `i18n.font-script-coverage` | derived | derived | derived | v1 | Per declared locale, whether the direction's chosen faces cover the script, and the named fallback stack where they do not. Computed from the real font files after the typeface pick, like `type.fallback-metrics`. **A direction whose display face lacks the script must fail loudly at generation time, not render tofu at LOCK** |
| `i18n.content-shape-policy` | **n/a** | n/a | site-global | v2 | Date/number/currency formatting, name-order assumptions, address shape, and the ban on string concatenation for sentences. Cheap to state, expensive to retrofit into generated components |
| `i18n.locale-switching-surface` | **3** | domain | site-global | v2 | header switcher / footer switcher / path-prefix-only-no-switcher. Maps directly onto §8's "Language / region switcher **4**" component variants — the component has four skins; the site has one placement policy |

### 7.15 Category M — Sound & sensory identity (**restored**)

> Same caveat as §7.14: this is a reconstruction of a missing letter, not a recovery. It is included because §8 ships a **Sound toggle (3, v2)** and an **Audio player (3, v3)** with nothing anywhere in §7 defining what they control — sound is currently a component with no system behind it, which is precisely the "component that reads as foreign" failure §7.11 warns about for charts.

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `sound.presence-policy` | **3** | domain | site-global | v2 | none / ambient-optional / interaction-cues. **`none` must be the default and must be a real, first-class option** — most marketing sites should ship silent. Declaring the null explicitly is the same discipline `typeface.accent` and `imagery.treatment` already apply |
| `sound.interaction-cue-set` | **6** | **set** | direction-slot | v3 | If `presence-policy` is `interaction-cues`, the direction ships six cues: hover, press, success, error, open, close. A partial set is worse than none — an unmatched close sound reads as a bug |
| `sound.ambient-bed` | **1 per direction** | per-direction | direction-slot | v3 | If `presence-policy` is `ambient-optional`, one loop per direction with a stated loop length and a documented seam. **Gated on `sound.consent-and-controls` below; autoplay with sound is blocked by every modern browser anyway** |
| `sound.consent-and-controls` | **n/a** | n/a | site-global | v2 | Default-off, persisted preference, a visible control, and no audio before an explicit user gesture. This is what §8's "Sound toggle — must default off and persist" is enforcing; the policy belongs here |
| `sound.reduced-and-assistive-pairing` | **n/a** | n/a | site-global | v2 | Every audio cue must have a non-audio equivalent (the same rule as "status must never be colour-only"), and audio must not be the sole channel for any state change. Also the hook for future haptics if a native shell is ever added — **explicitly out of scope for web v1, recorded so it is traded rather than lost** |

### 7.16 Category P — SEO, metadata & the sharing surface (**new**)

> Added because the audit found metadata had no home: `mark.favicon-set` and `mark.social-share-image` sit in Category H as *marks*, which covers the images but not the document-level metadata contract that determines whether they are ever used. §8 ships an "OG / social share card template" component with nothing specifying the head tags it depends on. The letter continues the existing scheme (O was the last used).

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `seo.head-contract` | **n/a** | n/a | site-global | v1 | The required per-page head set: `<title>` pattern, meta description, canonical, `og:*`, `twitter:*`, `theme-color` per scheme, viewport, and language attributes. **A LOCK gate check, because a static export with no canonical and no OG tags is a shipped defect a visitor never sees and the owner discovers on first share** |
| `seo.title-pattern` | **3** | domain | site-global | v1 | `page — site` / `page \| site` / `site: page`. Trivial, and exactly the kind of inconsistency that appears when each page is generated separately |
| `seo.structured-data-policy` | **n/a** | n/a | site-global | v2 | Which schema.org types the site emits (Organization, WebSite, Article, Product, FAQPage, BreadcrumbList) and the rule that structured data must match visible content. **Emitting a Product schema with invented ratings is the failure mode to ban explicitly** |
| `seo.crawlability-contract` | **n/a** | n/a | site-global | v1 | robots.txt, sitemap.xml, the no-JS/progressive-enhancement requirement (already a §8 state) restated as a build gate, and the rule that reveal-on-enter animations must not hide content from a no-JS client. **Ties directly to §8's note that the no-JS view is the crawler's view** |
| `seo.social-preview-proof` | **n/a** | n/a | site-global | v2 | A rendered proof of the OG card at 1200×630 in the evidence bundle, so the sharing surface is verified rather than assumed. Cheap: it is a render of an existing template |
| `seo.url-and-slug-policy` | **3** | domain | site-global | v2 | flat / sectioned / dated. Chosen once because changing it after publish costs redirects |

---

### 7.17 Artwork and artefact volume roll-up (closes the §6.3 ↔ §7.9 ↔ §8 contradiction)

**The problem, stated numerically.** No total artwork volume was ever stated, and the two places that imply one disagree by roughly an order of magnitude.

| Source | What it implies | Number |
|---|---|---|
| **D1 (settled)** | "20 artworks tagged by direction" | **20** |
| **§6.3 chunk budget** | "Ten directions plus 20 artworks is ~400KB (~110K tokens)" — the sizing behind the whole Step-2/3 hand-carry | **20** |
| **§20.3 U8** | 45–90 minute hand-carry estimate, anchored on that budget | (derived from 20) |
| **§20.3 U10** | ~250-artifact Step-2/3 payload, "inference from D1 arithmetic against the inventory in §7–§8" | (derived from 20) |
| **§7.9 as written** | 20 + 20 + 20 + 12 + 12 + 8 + 8 + 6 + 4 + 10 + 10 | **130 pieces** |
| **§8 #Media artwork tier** | Icon set 20 + Illustration set 20 + Decorative spot-graphic set 20 + Pattern/texture library 20 | **80 more** |
| **Overlap between the two** | `art.spot-illustrations` 20 ≡ §8 "Decorative spot-graphic set" 20; `effect.pattern-tiles` 12 + `art.texture-plates` 12 ≈ §8 "Pattern / texture library" 20 | −20 to −24 |

**§20.2 #14 resolves only the pieces-versus-sets axis, not the volume.** The volume question is untouched anywhere in the PRD.

#### 7.17.1 The full-library roll-up, by lane and phase

Lane assignment follows §7.9's three lanes. **Lane A pieces can be produced by Local Regeneration Mode (§6.5) with zero hand-carry**, which is the only reason the full library is reachable at all.

| Family | Full-library count | Lane | v1 | v2 | v3 |
|---|---|---|---|---|---|
| `art.background-scene` | 20 | A / B | 8 | 8 | 4 |
| `art.hero-artwork` | 20 | A / B / C | 6 | 8 | 6 |
| `art.spot-illustrations` (= §8 spot-graphic set) | 20 | A / B | 6 | 10 | 4 |
| `art.section-divider-shapes` | 12 | A | 12 | — | — |
| `art.texture-plates` | 12 | A | — | 12 | — |
| `effect.pattern-tiles` (§7.6) | 12 | A | 12 | — | — |
| `effect.noise-grain` (§7.6) | 8 | A | — | 8 | — |
| `effect.gradient-mesh` (§7.6) | 8 | A | — | 8 | — |
| `art.photo-grade-recipe` (= §8 photography treatment) | 8 | A (filter chain only, no assets) | 8 | — | — |
| `art.avatar-style` | 8 | A / B | — | 8 | — |
| `art.3d-or-canvas-scene` | 6 | A / C | — | — | 6 |
| `art.placeholder-strategy` | 4 | A | 4 | — | — |
| `art.empty-state` | 10 | A | — | 10 | — |
| `art.error-state` | 10 | A | — | 10 | — |
| `icon.core-set` × `icon.family-spec` (§7.8) | ~50 glyphs × 10 families = **~500 glyphs** | A | ~50 (one family for the chosen direction) | +~200 (4 more families) | +~250 |
| `mark.logo-lockups` (§7.8) | 10 systems × 6 members = **60** | A / B | 6 (chosen direction only) | 24 | 30 |
| `mark.decorative-glyphs` (§7.8) | 10 | A | 10 | — | — |
| `mark.social-share-image` (§7.8) | 6 | A | 3 | 3 | — |
| `shape.clip-and-mask-shapes` (§7.6) | 10 | A | 10 | — | — |
| **Artwork-family total (excluding icon glyphs)** | **~204 artefacts** | | **~85** | **~85** | **~34** |
| **Including icon glyphs** | **~704** | | **~135** | **~285** | **~284** |

**[I — every count above is arithmetic over the §7 rows; the phase split is this revision's proposal and has no external source. The icon-glyph line is what makes the total explode, and it is the number most likely to be wrong in practice because one family is almost certainly enough for v1.]**

#### 7.17.2 Payload estimate, and why the §6.3 budget does not survive contact with it

| Quantity | Value | Basis |
|---|---|---|
| Median size of one code-drawn SVG art piece, inlined | **~8KB** | **[I — no measured basis. This is a placeholder. O32 requires it to be measured against real generator output before any chunk plan depends on it]** |
| Full §7.9 artwork library at that median (130 pieces) | **~1.04MB** | Arithmetic on a placeholder |
| §6.3's entire stated hand-carry budget | **~400KB** | **[V — §6.3, anchored on `wc -c` of first-party FruitSync variant files]** |
| Ratio | **~2.6×** the whole budget, for §7.9 alone | |

**Conclusion: §6.3's "Ten directions plus 20 artworks is ~400KB" is not off by a rounding error.** Three things follow, and they are stated rather than papered over:

1. **§6.3's chunk table needs a real "Art" row.** It currently reads `Art | The 20 artworks with suitsDirections[] tags | Variable`. "Variable" is the entire sizing. **Required §6.3 edit:** replace with the v1 quota below and its byte estimate. Recorded as a cross-section change this revision cannot make.
2. **U8 (45–90 min) and U10 (~250 artifacts) must be re-derived** from whichever volume the user signs off on. Both are explicitly flagged in §20.3 as inference anchored on the 20-artwork reading. **Required §20.3 edit.**
3. **The v1 hand-carry quota is capped at 20 artwork pieces** (§7.18), which is the only reading that keeps D1, §6.3, U8 and U10 mutually consistent. Everything above that quota is Lane A / Local Regeneration Mode or Lane B ingestion, neither of which consumes hand-carry time.

#### 7.17.3 What requires user sign-off

> **O31 — requires user decision (blocking for the Step-2 prompt).** Does "about 20 artworks" mean **20 pieces in total** (the D1 and §6.3 reading, which this revision adopts as the v1 hand-carry quota), or **20 pieces per artwork family** (the §7.9 reading, ≈130 pieces)? If the second, the hand-carry cycle multiplies by roughly 6× and §6.3's one-paste protocol, U8's 45–90 minutes and U10's ~250 artifacts all become wrong by that factor. **No known mitigation other than routing the overage to Lane A / Local Regeneration Mode, which changes who generates the art — and therefore its character — not just how it arrives.**

> **Deviation notice — requires user sign-off.** The user named "arts to use in the website" and "background art/style" as first-class design-system items and cited the FruitSync site, which shipped **231 exported sprites**. Capping v1 hand-carried artwork at **20 pieces** is therefore a real reduction against the cited exemplar. It is proposed only because §6.4 identifies clerical load as "the most likely way the product quietly dies", and because Lane B (ingest an existing folder — exactly what FruitSync did) reaches 231 pieces at zero hand-carry cost. **The user should confirm they are content with: 20 hand-carried pieces + unlimited Lane B ingestion + on-demand Lane A generation, rather than a larger hand-carry.**

### 7.18 The v1 cut list for §7, and the phase policy

*(This is the subsection the audit suggested numbering §7.14; it lands here because §7.14–§7.16 restore the missing categories. Nothing previously numbered has moved.)*

**Rule.** Only `v1` rows are requested in the Step-2 prompt. `v2` and `v3` rows are generated on demand in Step 5 (§14) via Local Regeneration Mode or a targeted follow-up chunk. **A v2/v3 row is not "cut" — it is deferred, and the capability manifest records it as `deferred`, so a later regeneration knows it is missing rather than assuming the system is complete.**

| Measure | v1 | v2 | v3 | Total |
|---|---|---|---|---|
| §7 inventory rows | **~126** | **~32** | **~10** | **168** |
| Of which `derived` (no generation cost, computed locally) | ~63 | ~6 | 0 | ~69 |
| Of which `n/a` policy/contract rows (prose, small) | ~40 | ~9 | ~1 | ~50 |
| Of which carry a Count and must be enumerated in the prompt | **~23** | ~17 | ~9 | ~49 |
| Expected resolved tokens for the chosen direction | **~600–900** | +~80 | +~40 | ~720–1,020 |
| Hand-carried artwork pieces | **20 (quota, O31)** | Lane A on demand | Lane A / C on demand | see §7.17 |

**[I — row counts are counted from the tables in this revision; the resolved-token figure is the §7 preamble's verified 600–900 budget carried forward, and the v2/v3 deltas are inference.]**

**v1 §7 set, stated positively:** all of Category A (26 rows — the direction is not divisible); Category B except `color.high-contrast-scheme`, `color.print-scheme` and `color.syntax-highlight`; all of Category C; all of Category D including the two new container-query rows; all of Category E; Category F except `effect.backdrop-recipe`, `effect.noise-grain`, `effect.gradient-mesh` and `effect.blend-mode-policy`; Category G except `motion.spring-presets`; all of Category H (marks are what a site cannot ship without); Category I limited to `art.container-contract`, the v1 quotas in §7.17.1, `art.photo-grade-recipe`, `art.crop-and-focal-policy`, `art.placeholder-strategy`, `art.section-divider-shapes`; all of Category J; **none** of Category L (charts are v2 per §8); all of Category N; all of Category O; Category K rows marked v1; Category M `sound.presence-policy` and `sound.consent-and-controls` only (both of which will usually resolve to "none", which is the point); Category P rows marked v1.

### 7.19 §7 ↔ §8 ownership reconciliation

**The rule.** For every artefact that appears in both inventories: **§7 owns the system-level specification (`specified-by`), §8 owns the component that renders it (`renders`).** Where the counts differ, the axis is now stated. The Step-2 prompt requests each deliverable **exactly once**, from the §7 side.

| Deliverable | §7 item and count | §8 row and count | Reconciliation | Action required |
|---|---|---|---|---|
| Icon families / sets | `icon.family-spec` **10** (one spec per direction) | #Media "Icon set **20** … 20 candidate SETS" | **10 family *specs*, one per direction. §8's 20 is an artwork-tier candidate library — roughly two drawn sets per direction.** Both survive, but the prompt asks for one spec per direction and then N sets *within* the chosen direction's spec | **§8 edit:** change the rationale to "20 candidate sets **drawn to the active direction's `icon.family-spec`**", so 20 is never read as 20 competing families |
| Logo lockups | `mark.logo-lockups` **10 × 6** | #Media "Logo lockup set **6**" | **10 systems (one per direction) × 6 arrangements each.** §8's 6 = the members of one system | None — §7 now states the axis |
| Social / OG images | `mark.social-share-image` **6** | #Utility "OG / social share card template **3**" | **§8's 3 is the v1 cut of §7's 6.** The remaining 3 are v2 | **§8 edit:** annotate as "3 of 6 (§7.8), v1 cut" |
| Section seams | `shape.divider-treatment` **8** (token/CSS treatment) + `art.section-divider-shapes` **12** (SVG path library) | #Content "Section divider / seam **10**" | **Three layers, not three counts of one thing:** 8 treatments (how the seam is made) × an optional shape from the 12-path library × 10 composed component variants. A component variant selects a treatment and, where the treatment is "shape/wave cut", a path | **§8 edit:** add "composes §7.6 `shape.divider-treatment` + §7.9 `art.section-divider-shapes`" |
| Patterns / textures | `effect.pattern-tiles` **12** + `art.texture-plates` **12** = **24 defined** | #Media "Pattern / texture library **20**" | **24 defined in §7 (12 SVG token-coloured tiles + 12 texture plates); §8's 20 is the v1+v2 shipped library.** The 4-item difference is the v3 tail | **§8 edit:** change 20 → "24 (12 §7.6 tiles + 12 §7.9 plates)", or state which 4 are deferred |
| Photography | `imagery.treatment` **10** (identity slot: grade + crop + distance, one per direction) + `art.photo-grade-recipe` **8** (filter-chain domain) | #Media "Photography treatment **8**" | **Consistent already:** each direction's `imagery.treatment` resolves to one of the 8 chains plus per-direction crop rules. §8's 8 = the same 8 chains | None |
| Empty / error art | `art.empty-state` **10**, `art.error-state` **10** (art pieces) | #Feedback "Empty state **8**", "Error state **6**"; #Page templates "404 **6**", "500 **3**" | **§7 counts art; §8 counts layouts.** A layout places a piece. Neither count is derivable from the other, and both are needed | **§8 edit:** add "places one of §7.9 `art.empty-state` / `art.error-state`" |
| Container widths / gridlines | `layout.container-widths` derived, `layout.grid-definition` derived, `layout.container-breakpoints` **3** | #Utility "Layout container widths — derived" | Consistent; §8 already says "must be data, not decoration". **The new `layout.container-breakpoints` row is the missing half that §11.5 and A46 depend on** | **§11.5 edit:** cross-reference `layout.container-breakpoints` |
| Sound | Category M (§7.15, restored) | #Utility "Sound toggle **3**"; #Media "Audio player **3**" | §8 shipped a control with no system behind it. §7.15 supplies the policy | None beyond §7.15 existing |
| Team page template | — | #Page templates "Team \| **3** \| v3 \| *(empty)*" | **The only wholly blank Rationale cell in either inventory.** Suggested text: *"Photo grid + bio; structurally a recomposition of card grid + avatar, so three arrangements (grid, list-with-bio, feature-lead) exhaust the real variation."* | **§8 edit:** fill the cell |

### 7.20 Open questions and required sign-offs raised by this section

Continuing the existing numbering (§17 ended at O30; §19 ended at A90).

| # | Question / criterion | Status |
|---|---|---|
| **O31** | Does "about 20 artworks" mean 20 total or 20 per family? Determines the hand-carry budget, U8 and U10 (§7.17.3) | **Requires user decision.** Blocking for the Step-2 prompt |
| **O32** | Measure the real median byte size of one generated code-drawn SVG art piece and one full direction's token file, and re-derive §7.17.2 | **Open — currently a placeholder number, explicitly marked as such.** Cheap: one generation run |
| **O33** | Verify (a) that container-query size conditions reject `var()`, and (b) whether the pinned compiler target emits `light-dark()` safely | **Open.** Both are stated from working knowledge in this revision and are load-bearing for `layout.container-breakpoints` and `color.scheme-declaration` |
| **O34** | Residual risk accepted in §7.0.3: two directions can share a `vectorHash` and differ in direction-bound authored artefacts (icon family, voice, lockups). Lint 8 catches misuse, but the hash alone is not a complete identity | **Accepted risk, recorded.** Alternative (hash the artefacts too) is brittle against re-export noise |
| **O35** | What were categories **K** and **M** before they were cut? §7.14/§7.15 are a reconstruction, not a recovery | **Requires user decision, or an explicit §20.1 entry recording the cut.** No known way to recover the original contents |
| **O36** | Should `icon.family-spec`, `mark.logo-lockups` and `system.voice-and-microcopy` be promoted into the hash-bearing vector (making it 27 slots) rather than treated as direction-bound authored artefacts? | **Open design question.** This revision chose the artefact treatment and stated why; the promotion is defensible |
| **A91** | A forced-colors render of every v1 page passes the LOCK gate: no affordance is conveyed by background alone, and every element on `color.forced-colors-mapping`'s opt-out list re-adds a border | **New acceptance criterion — requires a §13 gate row** |
| **A92** | No block that renders more than 6 lines at any of the five breakpoints carries `text-wrap: balance` | **New acceptance criterion** |
| **A93** | Every `$extensions['com.acos.pick']` block carries `countKind` and `scope`; every `scope: "in-direction-repickable"` block carries a non-empty `validityList`. Ingest hard-fails otherwise | **New acceptance criterion** |
| **A94** | Two independent implementations of `token.direction-hash` over the same 24 slots produce the same 12-character prefix (fixture test with a manifesto containing non-ASCII, double spaces and CRLF) | **New acceptance criterion** |
| **A95** | The editor renders **zero** controls for any row whose Scope is `direction-slot` or `derived`, verified by walking the manifest rather than by inspection | **New acceptance criterion** |
| **A96** | Moving a card from a 6-col to a 3-col slot switches it across `cq-medium` → `cq-narrow` with no manual fix, and `grep`ping the built CSS finds no `@media` inside a component stylesheet (the enforcement half of A46) | **New acceptance criterion** |
| **A97** | `token.capability-manifest` is generated mechanically from §7's Count/Kind/Scope columns, and the count it declares for every group matches what was ingested | **New acceptance criterion** |

---
