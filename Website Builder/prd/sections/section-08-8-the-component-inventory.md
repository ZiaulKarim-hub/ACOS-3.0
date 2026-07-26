## 8. The component inventory

### 8.1 Definitional rule (must be in the glossary)

> **A variant is a structurally distinct composition of the same component within one design direction.**
> Size, theme, density, state, icon-slot, and semantic colour are **computed axes** derived from the direction's tokens. They are never generated as picks and never count against the variant budget.

Without this line the budget silently multiplies ~20×. Untitled UI reports "5 button components + 940 variants"; Tailwind Plus reports 8 buttons. Same product category, different definition. **[V — untitledui.com/components and tailwindcss.com/plus/ui-blocks, both fetched 2026-07-25]**

### 8.2 Three-tier variant budget

| Tier | What | Count | Why |
|---|---|---|---|
| **A** | Identity-carriers (~22 items) | **10**, or **12** for the six with the largest surface × frequency product | What a visitor reads as "the brand" |
| **B** | Structural / rare (~90 items) | **3–6** | Appear once or never; variation is mostly parametric |
| **C** | Artwork | **20** | "Which picture" — low stakes, high differentiation, parallel-scannable |

Assign the tier at inventory time; the number then follows mechanically and the list cannot drift.

**Market calibration:** Tailwind Plus (commercially curated) ships Hero 12, Feature 15, CTA 11, Pricing 12, Headers 11, Banners 13, Stats 8, Testimonials 8, FAQs 7, Footers 7, Team 9, Contact 7, Logo Clouds 6, Newsletter 6, 404 5, Bento 3; Application UI: Input Groups 21, Tables 19, Badges 16, Stacked Lists 15, Drawers 12, Radio Groups 12, Avatars 11, Navbars 11, Cards 10. Distribution 3–21, clustered 5–12, median ≈8. **The user's "10" is market-calibrated, not arbitrary. [V — fetched 2026-07-25]**

### 8.3 The variant-count table

**ARIA note.** Items marked **[APG]** map to one of the 30 W3C ARIA Authoring Practices Guide patterns **[V — w3.org/WAI/ARIA/apg/patterns/, full list retrieved 2026-07-25]**. Their variants are **skin-only**; behaviour comes from a single audited implementation, identical across all variants. ~25 of ~240 items qualify. Free-form items (hero, bento, marquee, CTA band, background layer) are where the design system gets to speak.

**Third-party note.** Items marked **[3P]** contain third-party marks with usage rules — platform CTA badges, social icons, trust/certification badges, press logos, map tiles. **These are not designable.** The variants are arrangement only. Generating a Steam button is a trademark violation.

#### Navigation

| Component | Variants | Priority | Rationale |
|---|---|---|---|
| Top ribbon / primary navigation | **10** | v1 | Tier A, seen on 100% of pages, user-named. Must satisfy WCAG 2.4.11 — a sticky ribbon must not entirely obscure a focused element |
| Nav scroll behaviour | **6** | v1 | static, sticky-solid, sticky-shrink, hide-down/show-up, blur-on-scroll, detach-to-pill. Exactly six exist; more are easing differences (a token) |
| Mega menu panel | **6** | v2 | Limited layout freedom (columns × featured slot); minority of sites |
| Dropdown / flyout menu **[APG]** | **7** | v1 | Tailwind ships exactly 7; freedom is panel skin + arrow/offset |
| Mobile drawer / full-screen overlay menu | **10** | v1 | Tier A on award sites — the open/close choreography IS brand. NN/g warns hidden nav halves discoverability, so all 10 bake in a visible-CTA rule |
| Mobile sticky action bar | **4** | v2 | Constrained by thumb reach and safe-area insets |
| Announcement / promo bar | **8** | v2 | Tailwind ships 13 but most differ only by dismissal affordance (a state) |
| Breadcrumb **[APG]** | **4** | v2 | Separator glyph, truncation, chip-vs-text. Genuinely small |
| In-page section rail / scroll-spy | **6** | v2 | left rail, right rail, top pills, dot column, numbered ticks, progress-linked |
| App sidebar navigation | **6** | v3 | App shell; budget deliberately restrained |
| Command palette (⌘K) | **4** | v3 | Tailwind ships 8 but they differ by result-row type; ~4 real shells |
| Skip link | **2** | v1 | Compliance requirement, near-zero design surface. **Sits at the top of the z-index ladder** |
| Language / region switcher | **4** | v2 | Correctness matters far more than skin; forces RTL to be real |
| Pagination | **4** | v2 | Rare and structural |
| Back-to-top control | **4** | v2 | Trivial surface, but the entrance choreography is a brand micro-moment |
| Reading / scroll progress indicator | **5** | v2 | Now cheaply native via CSS scroll-timeline |
| Search overlay + results dropdown | **6** | v2 | inline expand, dropdown panel, full-screen takeover, slide-down sheet, modal, sidebar |
| Tabs / in-page switcher **[APG]** | **8** | v1 | underline, pill, enclosed, segmented, boxed, minimal, icon+label, vertical |

#### Hero

| Component | Variants | Priority | Rationale |
|---|---|---|---|
| Marketing hero | **12** | v1 | Highest surface on the site; Tailwind ships 12; rubric double-weights the hero crop. **Above baseline is earned here and almost nowhere else** |
| Immersive media hero | **6** | v2 | Distinct class needing a GPU-tier ladder and poster frame; 6 bounds the render/verification cost |
| Interior page header | **8** | v1 | Used on every non-home page, so it carries real identity |
| Hero CTA cluster | **8** | v1 | Recombines across all 12 heroes; the conversion pivot |
| Preloader / intro sequence | **8** | v2 | Award signature moment absent from every mainstream library. **Hard-constrained: skippable, ≤2s, never blocking LCP.** An unskippable brand preloader is a pure conversion tax |

#### Content

| Component | Variants | Priority | Rationale |
|---|---|---|---|
| Section header block | **10** | v1 | Repeats 6–15× per page — Tier A despite looking trivial |
| Feature grid | **12** | v1 | Tailwind ships 15. **The anti-slop lint bans the "three icon-topped cards" tell, so extra variants are needed to route AROUND the cliché** |
| Feature split (alternating) | **8** | v1 | 50/50, 60/40, offset, overlap, full-bleed media, framed, in-device, bleed-edge |
| Bento grid | **6** | v1 | Tailwind ships 3, but bento is a saturated-template risk and the anti-slop rule caps simultaneous trend matches; 6 gives room for a non-obvious span pattern |
| Sticky scroll stack | **6** | v2 | pin-and-cover, pin-and-scale, pin-and-fade, card-deck, list-sync, image-swap |
| Horizontal scroll section | **5** | v2 | Scrolljacking constraints (no text-reading in altered scroll, disabled on mobile) prune the space |
| Split-screen scroll section | **5** | v2 | pin-left, pin-right, both-pin, mirrored, diagonal |
| Generic content card | **12** | v1 | Reused by blog, case study, team, product, feature — extra variants amortise across five categories |
| Card grid / collection layout | **8** | v1 | Separated from the card so skin and rhythm swap independently |
| Stacked list row | **10** | v2 | Tailwind's highest application count (15) because row density and meta arrangement genuinely vary |
| Rich text / prose body | **6** | v1 | measure-narrow serif, measure-wide sans, two-column, marginalia, drop-cap, technical-docs. Measure and rhythm are computed |
| Content + media section | **8** | v1 | The plain workhorse between marquee sections |
| Process / how-it-works steps | **8** | v1 | horizontal numbered, vertical connected, zigzag, card row, tabbed, scroll-synced, arc, diagram-anchored |
| Timeline | **6** | v2 | left rail, centre alternating, horizontal, scroll-driven, milestone-cards, compact list |
| Stat band | **8** | v1 | Fastest credibility signal. Anti-slop lint flags the generic stat banner, so variants must include non-obvious forms |
| Pull quote | **8** | v1 | Pure typography — where a direction's display face proves itself. Cheap to render, highly identity-revealing |
| FAQ / accordion **[APG]** | **8** | v1 | bordered, divided, card, plus-minus, chevron, numbered, two-column, first-open |
| Comparison table | **5** | v2 | Heavily constrained by data shape and the mobile-reflow problem; includes the required card-stack fallback |
| Section divider / seam | **10** | v1 | **Tier A. Juries read the seam between sections as craft.** Absent from every block library and one of the cheapest to render 10 of |
| Section wrapper | **8** | v1 | flat, tinted, inverted, gradient, textured, image, video, glass. Padding and width computed |
| CTA band | **12** | v1 | Recurs 2–4× per site at the conversion pivot |
| Newsletter block | **6** | v1 | Form geometry dominates, narrowing layout freedom |
| Footer | **10** | v1 | Tier A, second-most-seen component. **Also the mandatory home for the licence/attribution line** the evidence bundle requires |
| Blog index section | **7** | v2 | featured-hero, three-up, list, magazine, masonry, categorised, minimal |
| Blog post body layout | **5** | v2 | centred, left-TOC, right-marginalia, full-bleed-editorial, docs-style |
| Team section | **9** | v2 | Photo shape and hover reveal give genuine variety |
| About / story section | **6** | v2 | Largely a recomposition of prose + media + timeline |
| Careers / open roles | **4** | v3 | Data-driven and structurally constrained |
| Contact section | **7** | v2 | Form/map/detail arrangement genuinely varies |
| Legal / policy body | **3** | v1 | plain, TOC-sidebar, numbered-clause. **Deliberately un-art-directed** — any more is wasted budget |
| Changelog / release list | **3** | v3 | Data-shaped and rare |
| Feature callout / inline highlight | **6** | v2 | Six semantic treatments; colour mapping computed |

#### Social proof

| Component | Variants | Priority | Rationale |
|---|---|---|---|
| Logo wall **[3P]** | **8** | v1 | Logo normalisation (optical sizing) is computed, not a variant |
| Logo marquee **[3P]** | **6** | v1 | Shares the marquee container, so cost is low |
| Testimonial card | **10** | v1 | **Tier A — the most trust-loaded component on a B2B site**, and the quote typography carries the direction |
| Testimonial wall / masonry | **6** | v2 | Largely a composition of the card in a grid |
| Testimonial carousel **[APG]** | **6** | v2 | The APG contract (pause control, no auto-advance without it) constrains the space and must be identical across all six |
| Video testimonial | **4** | v3 | Needs the video facade underneath; own design surface is small |
| Rating / review summary **[3P]** | **5** | v2 | Source badges are fixed third-party marks |
| Press mentions row **[3P]** | **5** | v2 | Genuinely low-variance |
| Case-study / result callout | **8** | v2 | Highest-converting B2B proof unit; combines stat + quote + card |
| Trust / certification badges **[3P]** | **5** | v2 | Third-party marks with usage rules; variation is layout only |
| Award badge / laurels | **4** | v2 | Genuine identity moment on studio/portfolio sites |
| Animated counter | **6** | v2 | odometer, tabular-tick, blur-in, split-flap, ease-count, scroll-linked. **Must ship a reduced-motion static variant** |

#### Commerce

| Component | Variants | Priority | Rationale |
|---|---|---|---|
| Pricing section | **12** | v1 | Tailwind ships 12 — matching its hero count, which tells you the market treats pricing as hero-grade |
| Plan card | **10** | v1 | The emphasised-tier treatment is a real design decision |
| Pricing period toggle | **4** | v1 | pill switch, segmented, checkbox+label, tab |
| Feature comparison matrix | **5** | v2 | Includes the mandatory per-plan-column mobile fallback |
| Product card | **10** | v2 | Tier A for commerce — it tiles the whole catalogue |
| Product detail / gallery | **6** | v3 | Highly constrained by conventions users expect; deviating hurts conversion |
| Cart drawer / mini cart | **4** | v3 | drawer, dropdown, full-page, sheet |
| Checkout layout | **4** | v3 | **Novelty here is score-negative.** one-page, accordion, multi-step, express-first |
| Platform CTA badge registry **[3P]** | **5** | v1 | Steam/App Store/Play/itch/Epic marks are **deterministic embeds, never invented**. The 5 variants are arrangement only |
| Wishlist / preorder CTA | **4** | v2 | Hierarchy is fixed (Wishlist → Discord → press); only presentation varies |
| Booking / scheduling block | **4** | v3 | Usually a third-party iframe; the surface is the frame and loading state |
| Donation / support block | **3** | v3 | preset-row, preset-grid, slider |
| Promo / coupon field | **3** | v3 | Known UX trap (a visible coupon field increases abandonment) — one variant is collapsed-by-default |

#### Form

| Component | Variants | Priority | Rationale |
|---|---|---|---|
| Primary button | **10** | v1 | Tier A. The 10 are shape/fill/edge/motion treatments; size and state are computed |
| Secondary button | **10** | v1 | **Its relationship to the primary is a design decision, not a derivation** — outline, tinted, elevated and ghost all read differently against the same primary |
| Ghost / tertiary button | **8** | v1 | Risk is that it stops reading as interactive; all 8 checked against a hit-affordance rule |
| Icon button | **8** | v1 | Touch-target minimum and accessible-name requirement apply to all eight |
| Destructive button | **4** | v2 | Semantics dominate aesthetics; all 4 must pass contrast against the danger ramp |
| Split button | **3** | v3 | Rare outside app shells |
| Button group / segmented control | **6** | v2 | joined, spaced, pill, boxed, underline, icon-only |
| Floating action button | **4** | v3 | The Material 3 canonical set: mini, standard, extended, speed-dial |
| Inline text link | **10** | v1 | **Tier A and consistently underrated** — the link hover animation is one of the cheapest, most-repeated craft signals on an award site. Underline thickness/offset stay tokens |
| Text input | **10** | v1 | **Tier A: input chrome defines a system's voice as strongly as the button.** Tailwind ships 21 input groups |
| Textarea | **5** | v1 | Inherits input chrome; only sizing/resize/counter vary |
| Select **[APG]** | **6** | v1 | Native-vs-custom is a capability flag, not a variant |
| Combobox / autocomplete **[APG]** | **5** | v2 | Behaviour dominates and must be identical across skins |
| Multi-select / token field | **4** | v3 | Overflow behaviour ("+3 more") is the only real decision beyond chip skin |
| Checkbox **[APG]** | **8** | v1 | The check animation is a small identity moment |
| Radio group **[APG]** | **8** | v1 | Tailwind ships 12 because card-style and table-style radios are structurally different |
| Toggle switch **[APG]** | **8** | v1 | Knob motion and track treatment are visible brand micro-moments |
| Slider / range **[APG]** | **6** | v2 | Dual-thumb is a capability flag across all six, not a separate family |
| Number stepper **[APG]** | **4** | v3 | Low identity surface |
| Date picker | **5** | v2 | Locale/RTL correctness matters far more than skin |
| Time picker | **3** | v3 | Almost never on a marketing site |
| File upload / dropzone | **6** | v2 | The drop-target and the file-row are two design surfaces |
| OTP / PIN input | **3** | v3 | Behaviour (paste, backspace, `autocomplete=one-time-code`) matters more than skin |
| Rating input | **4** | v3 | Must expose a real radio group underneath |
| Colour picker | **3** | v3 | Untitled ships 6 but they are mode variations, not designs |
| Field group (label / help / error) | **6** | v1 | **Tier A adjacent: this single decision reshapes every form on the site.** shadcn now ships it as a first-class "Field" |
| Form layout | **6** | v1 | Tailwind ships only 4 because single-column is near-universally correct; 6 adds sectioned and inline |
| Multi-step form wizard | **5** | v3 | Composes stepper + form layout |
| Inline email capture | **6** | v1 | The smallest conversion unit; appears 2–4× per site |
| Contact form | **6** | v1 | Needs designed success/error/submitting — those are **states, not variants** |
| Consent checkbox | **3** | v1 | Legally constrained (unchecked by default, explicit, not bundled) |
| Search input control | **6** | v2 | Includes the expanding form (Carbon ships `ExpandableSearch` as a distinct component for this reason) |

#### Feedback

| Component | Variants | Priority | Rationale |
|---|---|---|---|
| Toast / snackbar | **6** | v2 | Position and stacking are configuration; semantic colour computed |
| Inline alert | **6** | v1 | Semantic colour computed from the ramp; only the shell varies |
| Modal dialog **[APG]** | **8** | v1 | The enter/exit choreography and scrim treatment are genuine identity choices |
| Confirm / alert dialog **[APG]** | **4** | v2 | Deliberately constrained — the decision, not the design, is the point |
| Drawer / sheet | **6** | v2 | Tailwind ships 12 but half differ only by edge (config, not variant) |
| Popover | **5** | v2 | arrow, arrow-less, elevated, bordered, glass. Collision logic shared |
| Tooltip **[APG]** | **6** | v1 | High frequency, small surface, low render cost. **A required companion to every icon button** |
| Hover card | **4** | v3 | Desktop-only with no touch equivalent — must always degrade |
| Progress bar **[APG]** | **5** | v2 | Indeterminate animation must respect reduced-motion |
| Spinner / loader | **8** | v1 | **Tier A adjacent — one of the few components a visitor stares at.** arc, dots, bars, morph, logo-mark, orbit, pulse, custom-glyph, all with reduced-motion fallbacks |
| Skeleton placeholder | **5** | v2 | Per-component shapes derived from component geometry |
| Empty state | **8** | v2 | NN/g treats empty states as a design discipline |
| Error state | **6** | v2 | **Each must include a real recovery action** — that's a gate, not a variant |
| Success / confirmation state | **5** | v2 | Animated check needs a reduced-motion equivalent |
| Cookie / consent banner | **6** | v1 | **The first thing a visitor sees, so it must be art-directed** — but legally constrained (reject as easy as accept) to 6 |
| Notification list / inbox | **3** | v3 | App-shell only |
| Badge / tag / pill | **12** | v1 | Highest small-element count anywhere (Tailwind 16, Untitled 380 permutations) because it's combinatorially cheap. **12 shape-and-treatment variants; semantic colour and size computed** — this flag alone removes ~40% of a naive budget |
| Removable chip / filter chip | **6** | v2 | Material 3's four chip types plus dismiss-glyph treatments |
| Status indicator dot | **4** | v2 | **Must never be colour-only** |
| Avatar | **8** | v2 | 8 shape-and-treatment designs; the rest computed |
| Avatar group / stack | **4** | v2 | Derives skin from avatar |
| Kbd / keyboard key | **3** | v3 | Docs and app-shell micro-surface |
| Toolbar **[APG]** | **4** | v3 | Keyboard contract fixed by APG |

#### Data display

| Component | Variants | Priority | Rationale |
|---|---|---|---|
| Basic table **[APG]** | **8** | v2 | **Each variant declares its own responsive strategy** (scroll container vs stacked cards) — otherwise this is the one component that breaks 390px |
| Data table **[APG]** | **5** | v3 | Behaviour-dominant; skin derives from basic table |
| Description / spec list | **6** | v2 | stacked, inline, two-column, bordered, striped, card-wrapped |
| Stat tile / KPI card | **10** | v2 | Tier A for data-heavy sites. **The delta treatment must never be colour-only** |
| Sparkline | **4** | v2 | line, area, bar, win-loss — the complete standard set |
| Line chart | **6** | v2 | single, multi-series, stepped, smoothed, confidence-band, annotated |
| Area chart | **4** | v2 | single, stacked, 100% stacked, stream |
| Bar / column chart | **8** | v2 | vertical/horizontal × plain/grouped/stacked/100% |
| Pie / donut chart | **4** | v2 | Deliberately small — only defensible for ≤5 categories and should be discouraged beyond |
| Gauge / progress ring | **6** | v2 | arc, full ring, segmented, multi-ring, needle, bullet |
| Scatter / bubble | **3** | v3 | scatter, bubble, with-trendline |
| Heatmap | **3** | v3 | matrix, calendar, density. Ramp computed and colourblind-checked |
| Funnel chart | **3** | v3 | tapered, stepped-bar, sankey-lite |
| Radar chart | **3** | v3 | single, overlaid, filled |
| Waterfall chart | **3** | v3 | Finance-standard, specialised |
| Treemap | **2** | v3 | flat, nested-with-headers |
| Map (pin / choropleth) **[3P]** | **4** | v3 | **Tile-provider licensing is a hard gate, not a design choice** |
| Chart chrome kit | **4** | v2 | minimal, gridded, bordered-technical, editorial. **One decision applied across all 12 marks — this is what makes a site's charts read as one system** |
| Chart colour ramps | derived | v2 | From OKLCH anchors per D1. The `dataviz` skill ships a runnable validator |
| Progress steps / stepper | **6** | v2 | Untitled reports 489 permutations, mostly state × orientation; 6 distinct designs |
| Tree view **[APG]** | **3** | v3 | Behaviour-dominant, app-shell only |
| Calendar | **4** | v3 | month, week, day, agenda-list |
| Kanban board | **3** | v3 | App-shell only |
| Code block | **5** | v2 | **Highlight theme derived from the direction's palette**, never imported, or it clashes with everything |
| Activity feed | **4** | v3 | timeline, compact-list, grouped-by-day, with-comments |

#### Media

| Component | Variants | Priority | Rationale |
|---|---|---|---|
| Image figure / frame | **10** | v1 | **Tier A** — the frame (bleed, inset, masked, tilted, layered, bordered, shadowed) is where the direction shows on every photo |
| Image gallery grid | **8** | v2 | Portfolio and case-study sites live on this |
| Lightbox **[APG]** | **4** | v2 | Focus-trap and keyboard contract fixed; only chrome and transition vary |
| Carousel / slider **[APG]** | **8** | v2 | peek, full-bleed, centred, coverflow, thumbnail-synced, drag-only, ticker-hybrid, stacked |
| Before/after slider | **3** | v3 | All three need a keyboard-accessible fallback |
| Video player skin | **6** | v2 | Captions and keyboard control non-negotiable across all six; **the poster frame is what most visitors actually see** |
| Third-party video facade | **4** | v2 | **Saves ~500KB–1MB of pre-interaction JS.** Exists for the performance gate as much as for design — the naive embed is a Lighthouse killer |
| Background video loop | **5** | v2 | Loop engineering and a 4–16s cap constrain all five |
| Audio player | **3** | v3 | Rare on marketing sites |
| Icon set | **20** | v1 | Artwork tier. 20 candidate **SETS**, not 20 icons. Recraft V4 is the only true native-SVG generator per the prior report. Grid, stroke width, corner style are tokens shared by all icons in a set |
| Illustration set | **20** | v2 | Artwork tier; parallel-scannable as a filtered grid |
| Decorative spot-graphic set | **20** | v1 | Artwork tier, **disproportionately high identity return per unit of effort** — the marks that make a page feel hand-made |
| Pattern / texture library | **20** | v1 | Artwork tier. **The single cheapest anti-slop move available** — the flat-gradient-card look is an enumerated AI tell |
| Logo lockup set | **6** | v1 | The standard brand deliverable set; arrangements of a fixed mark |
| Photography treatment | **8** | v2 | Applied globally — a direction-level decision. **The implementation of the ban on unstyled stock** |
| 3D model / product viewer | **3** | v3 | GPU-tier ladder is a gate, not a variant |
| Gaussian splat embed | **2** | v3 | Differentiation lives in the captured content, not the container; bandwidth caps how many can exist |

#### Motion / art containers — see §9

#### Utility

| Component | Variants | Priority | Rationale |
|---|---|---|---|
| Layout container widths | derived | v1 | **Also what the editor's gridlines snap to per D2** — must be data, not decoration |
| Editor grid overlay | **n/a** | v1 | Editor chrome, not a site component |
| Theme toggle | **6** | v2 | icon switch, segmented tri-state, animated sun/moon, text link, in-menu, auto-with-override. **The transition between themes is a visible craft moment**; needs a no-flash first-paint strategy |
| Motion toggle | **3** | v1 | Compliance item, minimal latitude. footer, header, first-visit prompt |
| Sound toggle | **3** | v2 | Must default off and persist |
| Age gate | **3** | v2 | Legally shaped; must not block crawlers or LCP unnecessarily |
| Social links row **[3P]** | **5** | v1 | Marks must not be redrawn to match the direction |
| Social share row | **4** | v2 | Privacy-preserving implementation (plain intent URLs, no SDKs) constrains all four |
| Sticky mobile CTA | **4** | v2 | Must not obscure the footer or form fields — a gate, not a design choice |
| Cookie preferences centre | **3** | v2 | modal, drawer, page. Reject as easy as accept in all three |
| OG / social share card template | **3** | v1 | Generated at build time from the direction's type and colour |
| Favicon / app-icon set | **n/a** | v1 | Derived export from the logo mark. Routinely missing from AI-built sites |
| Anti-spam honeypot / timing check | **n/a** | v2 | A contact form without it is a delivery defect; CAPTCHA is an accessibility and privacy cost |

#### Page templates

| Template | Variants | Priority | Rationale |
|---|---|---|---|
| Home / landing | **6** | v1 | proof-early, story-led, product-led, comparison-led, single-scroll-narrative, directory-style |
| About | **4** | v2 | Largely recomposition |
| Product / feature | **5** | v2 | Most-duplicated on B2B sites; the sequence must survive being repeated 6–10× |
| Pricing | **4** | v1 | Order (cards → matrix → FAQ → CTA) close to fixed by conversion evidence |
| Blog index | **4** | v2 | Drives CMS collection wiring |
| Blog post | **4** | v2 | Prose treatment is a separate component; the template decides furniture placement |
| Case study | **4** | v2 | Highest-value page type on an agency/B2B site |
| Contact | **4** | v2 | Conventional by design — visitors arrive with a task |
| Team | **3** | v3 | |
| Careers + job detail | **3** | v3 | Usually ATS-fed, which constrains layout |
| Legal | **2** | v1 | plain, TOC-sidebar. Required for Play/App Store and GDPR, deliberately un-art-directed |
| 404 | **6** | v1 | **All six required to carry a working search or nav back to real content** |
| 500 / error | **3** | v2 | **All self-contained (inline critical CSS)** because the failure may be in the asset pipeline itself |
| Coming soon / waitlist | **4** | v2 | Often the first thing shipped |
| Press kit | **3** | v2 | The dopresskit() convention journalists expect; novelty is counterproductive |
| Search results | **3** | v3 | The zero-result state is what actually matters |
| Auth screens | **5** | v3 | App-shell only; backend-free via MSW mocking |
| Dashboard shell | **4** | v3 | Every state must be screenshot-QA'd |
| Settings | **3** | v3 | tabbed, sidebar-nav, single-scroll |
| Docs | **3** | v3 | Heavily standardised; deviation costs comprehension |

#### States — not variants, never picked

| State set | Rationale |
|---|---|
| Interactive state matrix (default / hover / active / focus-visible / disabled / loading / selected / error) | **`focus-visible` is the state AI-generated sites most often omit, and its absence is a WCAG 2.4.7 failure** |
| Full 22-state coverage checklist (adds focus-within, read-only, checked, indeterminate, expanded, current-page, visited, warning, success, dragging, drop-target, empty, skeleton) | The state layer supplies the VALUES (4 opacities); this supplies the COVERAGE. Missing states are the most common completeness failure in generated systems |
| Data state set (empty / loading / partial / error / success) | Required for every list, grid, table and chart |
| Chart data states (+ single-data-point) | Charts fail more often in these states than in the happy path |
| Responsive breakpoint set (320 / 390 / 768 / 1280 / 1440) | **The enforcement mechanism for D2** |
| Theme state set (light / dark / forced-colors) | Low-contrast dark mode is an enumerated AI-slop tell |
| Motion state set (full / prefers-reduced-motion) | The reduced render must **differ** where motion exists AND still look designed |
| RTL / bidi state | Only if multi-language, but then it must be built with logical properties from the start |
| Long-content / pseudolocalisation (+35% string expansion) | The cheapest way to catch fragile-layout defects that QA on ideal copy never sees |
| 200% zoom reflow (WCAG 1.4.10) | Level AA, and a common failure for fluid type scales — which is exactly what Utopia generates |
| Print state | The alternative is a page that prints unusably on legal and pricing pages |
| No-JS / progressive enhancement | **Also the crawler's view, so SEO depends on it** — and reveal-on-enter animations are the classic way an AI-built page ships invisible content to a no-JS client |
| State transition map | Derived. **The instant list matters: focus rings must appear instantly; animating a focus ring is an accessibility defect** |

**True render cost per selected variant: ~20 captures** (5 breakpoints × 2 themes × 2 motion), not 1. Budget for it, and gate on it at LOCK, not during editing.

### 8.4 The v1 cut list

**~50 pickable items, ~430 generated variants.** Everything else is v2/v3. Sixty-two items are app-shell, commerce, or exotic-chart and generate **only** when the interview's site-type answer requires them.

v1 set: top ribbon + nav scroll behaviour + mobile drawer + skip link + tabs; marketing hero + interior page header + hero CTA cluster; section header + feature grid + feature split + bento + card + card grid + prose body + content+media + process steps + stat band + pull quote + FAQ + divider + section wrapper + CTA band + newsletter + footer + legal body; logo wall + logo marquee + testimonial card; pricing + plan card + period toggle; primary/secondary/ghost/icon button + inline link + state matrix + text input + textarea + select + checkbox + field group + form layout + inline email capture + contact form + consent checkbox; inline alert + modal + tooltip + spinner + cookie banner + badge; image figure + icon set + spot graphics + patterns + logo lockups; still container + background layer + marquee + reveal container + section reveal + text reveal + hover set + custom cursor + smooth scroll + reduced-motion + easing matrix; motion toggle + social links + OG card + favicons; home + pricing + legal + 404 templates; responsive/motion/zoom/no-JS state sets.

### 8.5 Component-bar presentation rules

Choice overload is **not** automatic. Chernev, Böckenholt & Goodman (2015, *Journal of Consumer Psychology* 25:333–358) meta-analysed 99 observations (N=7,202) and found the mean effect of assortment size **not reliably different from zero** — it appears only under four moderators: set complexity, task difficulty, preference uncertainty, and decision goal. **[V]** Every one is engineerable away:

| Moderator | Engineering fix |
|---|---|
| Preference uncertainty | Render variants **in the real page slot at real scale**, with the current copy and neighbours |
| Set complexity | Sort by structural distance from the current pick; label the differing axis; skeleton filter chips above 12 items |
| Task difficulty | Pre-select the direction's canonical variant; Esc reverts in one key |
| Decision goal | Not-choosing is free and costless |

**Under those conditions 10 is safe.** The failure case is real when variants are undifferentiated — Iyengar & Lepper (2000): 24 jams attracted 60% of passers but converted 3%; 6 jams attracted 40% and converted 30%, with higher post-choice satisfaction **[V]**. The mitigation is not fewer options but **more different** options.

**Hard rule: if two variants are indistinguishable at 200×120px, one must be regenerated or deleted.**

Hick's law is the **wrong** model for a thumbnail grid and must not be used to justify small sets. Hick–Hyman is robust for random serial search; a grid of visually distinct rendered thumbnails supports **parallel feature-based visual search** — "the one with the image on the left" is found in parallel. A feature-sorted 10-thumbnail grid scans near-constant-time; a 10-item unordered text dropdown does not. **The component bar must be visual and feature-sorted, never a text dropdown. [V — visual-search literature; IxDF on Hick–Hyman limits]**

Presentation spec: **5 thumbnails visible** in the strip, arrow/scroll to reach all 10, **hover previews live in the slot**, click commits, Esc reverts, current variant pinned first and pre-selected, **"Compare 3"** opens a full-width triptych (3 is the number for deliberate comparison — matching the existing `acos-design-variants` skill precedent), **"More like this"** generates 5 neighbours of the selected variant and appends them.

---

