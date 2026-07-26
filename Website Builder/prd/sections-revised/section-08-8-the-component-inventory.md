## 8. The component inventory

> **Revision note (this pass).** Section 8 was never audited in the original critic pass (a pipeline bug limited the critics to sections 13–20). This revision closes ten gaps found in a later audit. The substantive changes are: a **Tier** and a **Pick** column on every row so §8.2's "the list cannot drift" claim is checkable; corrected tier sizes (Tier B was understated roughly two-fold); a **[BEH]** marking that gives every keyboard/focus/live-region component a named audited primitive; explicit WCAG gates for hover overlays (1.4.13), auto-moving content (2.2.2), input purpose (1.3.5) and charts (1.1.1); three added states; six added inventory rows; a **mechanically regenerated v1 cut list** with the arithmetic shown; and concrete, testable definitions for "structural distance" and "indistinguishable" in §8.5. Every number below is computed from the tables in this file, not asserted.

### 8.1 Definitional rule (must be in the glossary)

> **A variant is a structurally distinct composition of the same component within one design direction.**
> Size, theme, density, state, icon-slot, and semantic colour are **computed axes** derived from the direction's tokens. They are never generated as picks and never count against the variant budget.

Without this line the budget silently multiplies ~20×. Untitled UI reports "5 button components + 940 variants"; Tailwind Plus reports 8 buttons. Same product category, different definition. **[V — untitledui.com/components and tailwindcss.com/plus/ui-blocks, both fetched 2026-07-25]**

**"Structurally distinct" is now a machine-checkable predicate, not a judgement call.** Every component declares a **variant axis vector** (§8.6); two variants of the same component are structurally distinct if their axis vectors differ in at least one axis. This is what makes §8.5's sort order, its "label the differing axis" caption, and its indistinguishability rule implementable rather than aspirational.

### 8.2 Three-tier variant budget

**The assignment rule (mechanical, applied at inventory time):**

1. **Tier A — identity-carrier.** The component is one a visitor reads as "the brand": high surface area × high frequency, and the direction's voice is legible in it at a glance. Count = **10**, or **12** for the six with the largest surface × frequency product.
2. **Tier C — artwork.** The item is a *set* of pictures rather than a composition ("which picture"). Count = **20**.
3. **Tier B — everything else**, banded by how much structural freedom the component actually has once its contract is fixed:
   - **B1 = 7–8** — high frequency, real but bounded structural freedom (buttons below primary, tabs, accordions, wrappers, split layouts).
   - **B2 = 4–6** — recurs, moderate freedom, usually one dominant axis (position, orientation, or shell).
   - **B3 = 2–3** — rare, or legally/conventionally fixed, or behaviour-dominant.
4. **Not a tier: `derived` and `n/a` rows.** These carry a **Pick** value of `computed` or `n-a`, render no control in the editor (`com.acos.pick.pickable: false`), and contribute zero variants. Same key as §7 uses.

Assign the tier at inventory time; the number then follows mechanically. **The check that the list has not drifted is now runnable:** for every row, `tier(count)` must equal the declared Tier cell, and every row must carry a Pick value. A row whose count does not match its tier band is a lint failure, not a judgement call.

**Actual tier sizes, computed from §8.3 as written in this file:**

| Tier | What | Count rule | Rows | Variants |
|---|---|---|---|---|
| **A** | Identity-carriers | **10**, or **12** for the six largest | **21** | **222** |
| **B1** | Structural, high-frequency | **7–8** | **33** | **262** |
| **B2** | Structural, moderate | **4–6** | **111** | **554** |
| **B3** | Rare / fixed / behaviour-dominant | **2–3** | **38** | **110** |
| **C** | Artwork sets | **20** | **4** | **80** |
| **—** | `derived` / `n/a` policy and contract rows | not picked | **9** | **0** |
| | **§8.3 total** | | **216** | **1228** |

**Correction to the previous figures.** The prior text sized the tiers at "~22 Tier A + ~90 Tier B + artwork" and the ARIA note referred to "~240 items". Two of those three were wrong:

- **Tier A ≈ 22 was right** — it is **21** rows.
- **Tier B ≈ 90 was understated roughly two-fold** — B1 + B2 + B3 is **182** rows carrying **926** variants. **This is a real scope increase against what §18 and §13 were sized on, not a re-labelling — see the sign-off note in §8.4.**
- **"~240 items" was right, but only when §9 is included** — which the previous text never said, so the figure looked unreconcilable against a §8.3 that enumerated 210 rows. Before this revision: 210 §8.3 rows + 31 §9.2/§9.3 rows = **241**. After the six rows added here: **216** + **31** = **247**. The ARIA note now states the arithmetic instead of leaving the reader to guess at it.

**Pick-key reconciliation:** 207 rows are `pick`, 2 are `computed`, 7 are `n-a` — 216 total, with no unmarked rows. This is the per-row marking §7 already had and §8 previously lacked, and it is what makes D1's "identity-carrying-and-picked, or derived-and-not-picked" reviewable against §8 at all.

**Market calibration:** Tailwind Plus (commercially curated) ships Hero 12, Feature 15, CTA 11, Pricing 12, Headers 11, Banners 13, Stats 8, Testimonials 8, FAQs 7, Footers 7, Team 9, Contact 7, Logo Clouds 6, Newsletter 6, 404 5, Bento 3; Application UI: Input Groups 21, Tables 19, Badges 16, Stacked Lists 15, Drawers 12, Radio Groups 12, Avatars 11, Navbars 11, Cards 10. Distribution 3–21, clustered 5–12, median ≈8. **The user's "10" is market-calibrated, not arbitrary. [V — fetched 2026-07-25]**

### 8.3 The variant-count table

**Column key.**

| Column | Values | Meaning |
|---|---|---|
| **Tier** | `A` / `B1` / `B2` / `B3` / `C` / `—` | The §8.2 band. The variant count must fall inside the band or the row is a lint failure |
| **Pick** | `pick` / `computed` / `n-a` | `pick` = the editor renders a variant strip. `computed` = derived from the direction vector, no control (`com.acos.pick.pickable: false`). `n-a` = a policy, contract, or coverage checklist, not a choice. Same key as §7 |
| **Variants** | a number, `derived`, or `n/a` | Distinct pickable options. Never multiplied by size/theme/density/state (§8.1) |
| **Priority** | `v1` / `v2` / `v3` | **§8.4 is generated from this column mechanically.** Editing this cell changes v1 scope |

**ARIA note.** Items marked **[APG]** map to one of the 30 W3C ARIA Authoring Practices Guide patterns **[V — w3.org/WAI/ARIA/apg/patterns/, full list retrieved 2026-07-25]**. Their variants are **skin-only**; behaviour comes from a single audited implementation, identical across all variants. **22 rows** carry it, out of 216 rows here (247 including §9). Free-form items (hero, bento, marquee, CTA band, background layer) are where the design system gets to speak.

**Behavioural-primitive note (new in this revision).** The previous text said where behaviour came from for **[APG]** items and was silent for everything else — leaving roughly a hundred variants of drawers, overlays, toasts, banners, pickers and dropzones with real keyboard, focus-trap and live-region contracts and **no named source of truth**, so each skin would have re-invented them. Items marked **[BEH]** now declare "behaviour comes from a shared audited primitive; variants are skin-only", exactly as **[APG]** does, and name the primitive. **61 rows** carry it. The primitives:

| Primitive | Contract | Used by |
|---|---|---|
| `overlay.dismissible-layer` | Focus trap, Escape, focus return to trigger, background `inert`, scroll lock, `aria-modal` | Mobile drawer, Drawer/sheet, Cart drawer, Search takeover, Command palette, Cookie banner (blocking form), Cookie preferences centre, Age gate, App sidebar (overlay mode), Product gallery zoom |
| `overlay.popup-nonmodal` | Anchored positioning + collision/flip, Escape to close without moving the pointer, hover-intent open/close delays, safe-triangle traversal, **WCAG 1.4.13** | Popover, Hover card, Mega menu, Dropdown/flyout (hover form), Tooltip |
| `live.announcer` | Single page-level polite and assertive regions, message queue, dedupe, `role=status` vs `role=alert` selection, **WCAG 4.1.3** | Toast, Inline alert (injected), Contact form result, Cart drawer, Chip removal, Notification list, Search result counts, Code-block copy, Activity feed |
| `disclosure.dismissible-region` | APG Disclosure + persisted dismissal + defined post-dismiss focus destination | Announcement/promo bar, Removable chip, Notification row, Multi-select tokens |
| `nav.current-location` | `aria-current` value selection, throttled updates, accessible names on numeric links | Scroll-spy rail, Pagination, Stepper, Language switcher |
| `nav.focus-mover` | Viewport moves are paired with programmatic focus moves | Back-to-top, Skip link, in-page anchors under a sticky ribbon |
| `input.text-affordance` | Search semantics, clear control naming, expand-and-focus | Search input control |
| `input.file-dropzone` | **WCAG 2.5.7** — drag is decoration over a real file input; keyboard + single-pointer path; progress via `live.announcer` | File upload / dropzone |
| `input.date-time` | APG Date Picker Dialog grid, arrow-key navigation, typed-entry alternative | Date picker, Time picker, Calendar |
| `input.segmented-code` | Grouped naming, paste-fills-all, backspace traversal | OTP / PIN input |
| `input.two-dimensional` | Arrow-key operation of a 2D area + text alternative (**2.5.7**) | Colour picker |
| `form.validation` | Error summary focus, per-field association, `aria-describedby` wiring, announcement once | Contact form, Form error summary, Multi-step wizard |
| `form.step-sequence` | Focus + announcement on step change, position statement | Multi-step wizard, Checkout |
| `media.player-controls` | Labelled transport controls, captions, no keyboard trap, **2.2.2** satisfied by the transport itself | Video player skin, Audio player, Video testimonial, Background video loop |
| `motion.auto-started` | Registers with the page's **2.2.2** pause registry; exposes pause/stop; honours the site-wide motion toggle | Background video loop, Animated counter (scroll-linked), Marquee (§9), Ambient background motion (§9), Auto-advancing carousel |
| `overlay.sticky-obstruction` | **WCAG 2.4.11** focus-not-obscured check, scroll-padding contribution, form-field non-occlusion | Sticky ribbon, Mobile sticky action bar, Sticky mobile CTA |
| `scroll.pinned-sequence` | §9.4 drag restriction, keyboard-reachable content, works with scroll-driven animation absent | Sticky scroll stack, Horizontal scroll section, Split-screen scroll |
| `table.responsive-strategy` | Per-variant declared reflow strategy; focusable scroll container | Basic table, Data table, Comparison table, Feature comparison matrix |

**A [BEH] row is not a weaker [APG] row.** The rule is identical: behaviour is written once, audited once, and identical across every variant of every component that names the primitive. The distinction is only that **[APG]** points at a published W3C pattern and **[BEH]** points at a primitive this project owns.

**Third-party note.** Items marked **[3P]** contain third-party marks with usage rules — platform CTA badges, social icons, trust/certification badges, press logos, map tiles. **These are not designable.** The variants are arrangement only. Generating a Steam button is a trademark violation. **8 rows** carry it.

#### Navigation

| Component | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Top ribbon / primary navigation **[BEH]** | A | pick | **10** | v1 | Tier A, seen on 100% of pages, user-named. Must satisfy WCAG 2.4.11 — a sticky ribbon must not entirely obscure a focused element. **[BEH] `overlay.sticky-obstruction`** — the 2.4.11 check, the `scroll-padding-top` contribution and the "does not cover the field being typed into" rule are one audited implementation shared with the mobile action bar and the sticky mobile CTA, not re-solved in each of the 10 skins |
| Nav scroll behaviour | B2 | pick | **6** | v1 | static, sticky-solid, sticky-shrink, hide-down/show-up, blur-on-scroll, detach-to-pill. Exactly six exist; more are easing differences (a token) |
| Mega menu panel **[BEH]** | B2 | pick | **6** | v2 | Limited layout freedom (columns × featured slot); minority of sites. **[BEH] `overlay.popup-nonmodal`** — Disclosure-per-top-item, not a Menubar, because the panel contains links and text rather than menu commands. **1.4.13 applies (§8.7-A1): dismissable via Esc without moving the pointer, hoverable across the gap between trigger and panel, persistent until dismissed. Coarse pointer: tap-to-open, tap-outside or an explicit close control to dismiss** |
| Dropdown / flyout menu **[APG]** | B1 | pick | **7** | v1 | Tailwind ships exactly 7; freedom is panel skin + arrow/offset. **[APG] Menu/Menubar or Disclosure depending on trigger.** All 7 carry the WCAG 2.2 SC 1.4.13 contract (§8.7-A1) if any of them opens on hover. **Coarse pointer: opens on tap, never on hover; the trigger is a real button with `aria-expanded`** |
| Mobile drawer / full-screen overlay menu **[BEH]** | A | pick | **10** | v1 | Tier A on award sites — the open/close choreography IS brand. NN/g warns hidden nav halves discoverability, so all 10 bake in a visible-CTA rule. **[BEH] `overlay.dismissible-layer`** — the same audited focus trap, Escape handler, focus return and background `inert` as Modal dialog; identical across all 10 skins |
| Mobile sticky action bar **[BEH]** | B2 | pick | **4** | v2 | Constrained by thumb reach and safe-area insets. **[BEH] `overlay.sticky-obstruction`** — must satisfy WCAG 2.4.11 against focused elements and must not cover the form field being typed into |
| Announcement / promo bar **[BEH]** | B1 | pick | **8** | v2 | Tailwind ships 13 but most differ only by dismissal affordance (a state). **[BEH] `disclosure.dismissible-region`** — APG Disclosure plus a persisted dismissal and a defined focus destination after dismiss (focus moves to the following landmark, never to `<body>`) |
| Breadcrumb **[APG]** | B2 | pick | **4** | v2 | Separator glyph, truncation, chip-vs-text. Genuinely small |
| In-page section rail / scroll-spy **[BEH]** | B2 | pick | **6** | v2 | left rail, right rail, top pills, dot column, numbered ticks, progress-linked. **[BEH] `nav.current-location`** — `aria-current="true"` on the active entry, updated without announcing on every scroll tick (the throttle rule lives in the primitive, not the skin) |
| App sidebar navigation **[BEH]** | B2 | pick | **6** | v3 | App shell; budget deliberately restrained. **[BEH] `overlay.dismissible-layer` in its collapsed/overlay mode**, plain landmark navigation when docked |
| Command palette (⌘K) **[BEH]** | B2 | pick | **4** | v3 | Tailwind ships 8 but they differ by result-row type; ~4 real shells. **[BEH] `overlay.dismissible-layer` + APG Combobox** (dialog-wrapped listbox with `aria-activedescendant`); the keyboard contract is identical across all 4 |
| Skip link **[BEH]** | B3 | pick | **2** | v1 | Compliance requirement, near-zero design surface. **Sits at the top of the z-index ladder.** **[BEH] `nav.focus-mover`** — the target must receive focus, not merely be scrolled to, and it must clear the sticky ribbon's scroll padding |
| Language / region switcher **[BEH]** | B2 | pick | **4** | v2 | Correctness matters far more than skin; forces RTL to be real. **[BEH] `nav.current-location`** — each option carries `lang` and `hreflang`; the current language is programmatically marked |
| Pagination **[BEH]** | B2 | pick | **4** | v2 | Rare and structural. **[BEH] `nav.current-location`** — `<nav aria-label>` + `aria-current="page"`; the accessible name of a bare number link must not be just "3" |
| Back-to-top control **[BEH]** | B2 | pick | **4** | v2 | Trivial surface, but the entrance choreography is a brand micro-moment. **[BEH] `nav.focus-mover`** — moving the viewport must also move focus to the top landmark, or keyboard users are returned visually but not programmatically |
| Reading / scroll progress indicator **[BEH]** | B2 | pick | **5** | v2 | Now cheaply native via CSS scroll-timeline. **[BEH] decorative-by-default: `aria-hidden="true"` unless it doubles as a real `progressbar`, in which case the APG Meter/Progressbar contract applies. A scroll indicator that announces on every frame is a screen-reader denial-of-service** |
| Search overlay + results dropdown **[BEH]** | B2 | pick | **6** | v2 | inline expand, dropdown panel, full-screen takeover, slide-down sheet, modal, sidebar. **[BEH] `overlay.dismissible-layer` (takeover/modal/sheet forms) + APG Combobox (inline/dropdown forms)**; results count announced once via `live.announcer`, not per keystroke |
| Tabs / in-page switcher **[APG]** | B1 | pick | **8** | v1 | underline, pill, enclosed, segmented, boxed, minimal, icon+label, vertical |

#### Hero

| Component | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Marketing hero | A | pick | **12** | v1 | Highest surface on the site; Tailwind ships 12; rubric double-weights the hero crop. **Above baseline is earned here and almost nowhere else** |
| Immersive media hero | B2 | pick | **6** | v2 | Distinct class needing a GPU-tier ladder and poster frame; 6 bounds the render/verification cost |
| Interior page header | B1 | pick | **8** | v1 | Used on every non-home page, so it carries real identity |
| Hero CTA cluster | B1 | pick | **8** | v1 | Recombines across all 12 heroes; the conversion pivot |
| Preloader / intro sequence **[BEH]** | B1 | pick | **8** | v2 | Award signature moment absent from every mainstream library. **Hard-constrained: skippable, ≤2s, never blocking LCP.** An unskippable brand preloader is a pure conversion tax. **[BEH] `live.announcer` + focus parking** — the skip control is the first focusable element; content behind it is not `inert` to crawlers |

#### Content

| Component | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Section header block | A | pick | **10** | v1 | Repeats 6–15× per page — Tier A despite looking trivial |
| Feature grid | A | pick | **12** | v1 | Tailwind ships 15. **The anti-slop lint bans the "three icon-topped cards" tell, so extra variants are needed to route AROUND the cliché** |
| Feature split (alternating) | B1 | pick | **8** | v1 | 50/50, 60/40, offset, overlap, full-bleed media, framed, in-device, bleed-edge |
| Bento grid | B2 | pick | **6** | v1 | Tailwind ships 3, but bento is a saturated-template risk and the anti-slop rule caps simultaneous trend matches; 6 gives room for a non-obvious span pattern |
| Sticky scroll stack **[BEH]** | B2 | pick | **6** | v2 | pin-and-cover, pin-and-scale, pin-and-fade, card-deck, list-sync, image-swap. **[BEH] `scroll.pinned-sequence`** — shares §9.4's drag restriction; content must remain reachable and readable with scroll-driven animation unsupported or disabled |
| Horizontal scroll section **[BEH]** | B2 | pick | **5** | v2 | Scrolljacking constraints (no text-reading in altered scroll, disabled on mobile) prune the space. **[BEH] `scroll.pinned-sequence`** — a horizontally scrolling region needs a keyboard-operable scroll container (`tabindex="0"` + accessible name) or its content is unreachable without a pointer |
| Split-screen scroll section | B2 | pick | **5** | v2 | pin-left, pin-right, both-pin, mirrored, diagonal |
| Generic content card | A | pick | **12** | v1 | Reused by blog, case study, team, product, feature — extra variants amortise across five categories |
| Card grid / collection layout | B1 | pick | **8** | v1 | Separated from the card so skin and rhythm swap independently |
| Stacked list row | A | pick | **10** | v2 | Tailwind's highest application count (15) because row density and meta arrangement genuinely vary |
| Rich text / prose body | B2 | pick | **6** | v1 | measure-narrow serif, measure-wide sans, two-column, marginalia, drop-cap, technical-docs. Measure and rhythm are computed |
| Content + media section | B1 | pick | **8** | v1 | The plain workhorse between marquee sections |
| Process / how-it-works steps | B1 | pick | **8** | v1 | horizontal numbered, vertical connected, zigzag, card row, tabbed, scroll-synced, arc, diagram-anchored |
| Timeline | B2 | pick | **6** | v2 | left rail, centre alternating, horizontal, scroll-driven, milestone-cards, compact list |
| Stat band | B1 | pick | **8** | v1 | Fastest credibility signal. Anti-slop lint flags the generic stat banner, so variants must include non-obvious forms |
| Pull quote | B1 | pick | **8** | v1 | Pure typography — where a direction's display face proves itself. Cheap to render, highly identity-revealing |
| FAQ / accordion **[APG]** | B1 | pick | **8** | v1 | bordered, divided, card, plus-minus, chevron, numbered, two-column, first-open |
| Comparison table **[BEH]** | B2 | pick | **5** | v2 | Heavily constrained by data shape and the mobile-reflow problem; includes the required card-stack fallback. **[BEH] `table.responsive-strategy`** — the reflow strategy is declared per variant and the scroll container is keyboard-focusable |
| Section divider / seam | A | pick | **10** | v1 | **Tier A. Juries read the seam between sections as craft.** Absent from every block library and one of the cheapest to render 10 of |
| Section wrapper | B1 | pick | **8** | v1 | flat, tinted, inverted, gradient, textured, image, video, glass. Padding and width computed |
| CTA band | A | pick | **12** | v1 | Recurs 2–4× per site at the conversion pivot |
| Newsletter block | B2 | pick | **6** | v1 | Form geometry dominates, narrowing layout freedom |
| Footer | A | pick | **10** | v1 | Tier A, second-most-seen component. **Also the mandatory home for the licence/attribution line** the evidence bundle requires |
| Blog index section | B1 | pick | **7** | v2 | featured-hero, three-up, list, magazine, masonry, categorised, minimal |
| Blog post body layout | B2 | pick | **5** | v2 | centred, left-TOC, right-marginalia, full-bleed-editorial, docs-style |
| Team section | B1 | pick | **9** | v2 | Photo shape and hover reveal give genuine variety |
| About / story section | B2 | pick | **6** | v2 | Largely a recomposition of prose + media + timeline |
| Careers / open roles | B2 | pick | **4** | v3 | Data-driven and structurally constrained |
| Contact section | B1 | pick | **7** | v2 | Form/map/detail arrangement genuinely varies |
| Legal / policy body | B3 | pick | **3** | v1 | plain, TOC-sidebar, numbered-clause. **Deliberately un-art-directed** — any more is wasted budget |
| Changelog / release list | B3 | pick | **3** | v3 | Data-shaped and rare |
| Feature callout / inline highlight | B2 | pick | **6** | v2 | Six semantic treatments; colour mapping computed |

#### Social proof

| Component | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Logo wall **[3P]** | B1 | pick | **8** | v1 | Logo normalisation (optical sizing) is computed, not a variant |
| Logo marquee **[3P]** | B2 | pick | **6** | v1 | Shares the marquee container, so cost is low |
| Testimonial card | A | pick | **10** | v1 | **Tier A — the most trust-loaded component on a B2B site**, and the quote typography carries the direction |
| Testimonial wall / masonry | B2 | pick | **6** | v2 | Largely a composition of the card in a grid |
| Testimonial carousel **[APG]** | B2 | pick | **6** | v2 | The APG contract (pause control, no auto-advance without it) constrains the space and must be identical across all six. **WCAG 2.2.2 (Level A) applies to every auto-advancing variant — see §8.7-A2** |
| Video testimonial **[BEH]** | B2 | pick | **4** | v3 | Needs the video facade underneath; own design surface is small. **[BEH] `media.player-controls`** — captions, keyboard-operable controls and a real accessible name on the player |
| Rating / review summary **[3P]** | B2 | pick | **5** | v2 | Source badges are fixed third-party marks |
| Press mentions row **[3P]** | B2 | pick | **5** | v2 | Genuinely low-variance |
| Case-study / result callout | B1 | pick | **8** | v2 | Highest-converting B2B proof unit; combines stat + quote + card |
| Trust / certification badges **[3P]** | B2 | pick | **5** | v2 | Third-party marks with usage rules; variation is layout only |
| Award badge / laurels | B2 | pick | **4** | v2 | Genuine identity moment on studio/portfolio sites |
| Animated counter **[BEH]** | B2 | pick | **6** | v2 | odometer, tabular-tick, blur-in, split-flap, ease-count, scroll-linked. **Must ship a reduced-motion static variant.** **[BEH] `motion.auto-started` (§8.7-A2).** WCAG 2.2.2 (Level A) exempts motion that stops within 5 seconds, so a one-shot count-up under 5s is compliant without a control; **the scroll-linked variant, which can restart on every re-entry, is NOT exempt and must delegate to the Auto-motion pause/stop control.** `prefers-reduced-motion` does not satisfy 2.2.2 — it is an OS preference, not a mechanism on the page |

#### Commerce

| Component | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Pricing section | A | pick | **12** | v1 | Tailwind ships 12 — matching its hero count, which tells you the market treats pricing as hero-grade |
| Plan card | A | pick | **10** | v1 | The emphasised-tier treatment is a real design decision |
| Pricing period toggle | B2 | pick | **4** | v1 | pill switch, segmented, checkbox+label, tab |
| Feature comparison matrix | B2 | pick | **5** | v2 | Includes the mandatory per-plan-column mobile fallback |
| Product card | A | pick | **10** | v2 | Tier A for commerce — it tiles the whole catalogue |
| Product detail / gallery **[BEH]** | B2 | pick | **6** | v3 | Highly constrained by conventions users expect; deviating hurts conversion. **[BEH] `overlay.dismissible-layer` for the zoom/lightbox path; thumbnail rail is a Tablist or a Listbox, never bare divs** |
| Cart drawer / mini cart **[BEH]** | B2 | pick | **4** | v3 | drawer, dropdown, full-page, sheet. **[BEH] `overlay.dismissible-layer` + `live.announcer`** — "added to cart" must be announced; the drawer's focus trap and Escape behaviour are the modal primitive's, not re-invented per skin |
| Checkout layout **[BEH]** | B2 | pick | **4** | v3 | **Novelty here is score-negative.** one-page, accordion, multi-step, express-first. **[BEH] `form.step-sequence`** — step changes move focus to the new step heading and announce position ("Step 2 of 4") |
| Platform CTA badge registry **[3P]** | B2 | pick | **5** | v1 | Steam/App Store/Play/itch/Epic marks are **deterministic embeds, never invented**. The 5 variants are arrangement only. **Present in the v1 set (§8.4) — it was missing from the previous hand-written v1 list** |
| Wishlist / preorder CTA | B2 | pick | **4** | v2 | Hierarchy is fixed (Wishlist → Discord → press); only presentation varies |
| Booking / scheduling block **[BEH]** | B2 | pick | **4** | v3 | Usually a third-party iframe; the surface is the frame and loading state. **[BEH] every iframe carries a `title`; the loading state is announced once. Third-party iframe accessibility is outside our control — record it as an accepted, disclosed limitation in the evidence bundle rather than claiming conformance** |
| Donation / support block | B3 | pick | **3** | v3 | preset-row, preset-grid, slider |
| Promo / coupon field | B3 | pick | **3** | v3 | Known UX trap (a visible coupon field increases abandonment) — one variant is collapsed-by-default |

#### Form

| Component | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Primary button | A | pick | **10** | v1 | Tier A. The 10 are shape/fill/edge/motion treatments; size and state are computed |
| Secondary button | A | pick | **10** | v1 | **Its relationship to the primary is a design decision, not a derivation** — outline, tinted, elevated and ghost all read differently against the same primary |
| Ghost / tertiary button | B1 | pick | **8** | v1 | Risk is that it stops reading as interactive; all 8 checked against a hit-affordance rule |
| Icon button | B1 | pick | **8** | v1 | Touch-target minimum and accessible-name requirement apply to all eight. **Every icon button pairs with a Tooltip, so all eight inherit the 1.4.13 contract (§8.7-A1); the `aria-label` is authoritative and the tooltip is supplementary, never the only carrier of the label** |
| Destructive button | B2 | pick | **4** | v2 | Semantics dominate aesthetics; all 4 must pass contrast against the danger ramp |
| Split button | B3 | pick | **3** | v3 | Rare outside app shells |
| Button group / segmented control | B2 | pick | **6** | v2 | joined, spaced, pill, boxed, underline, icon-only |
| Floating action button | B2 | pick | **4** | v3 | The Material 3 canonical set: mini, standard, extended, speed-dial |
| Inline text link | A | pick | **10** | v1 | **Tier A and consistently underrated** — the link hover animation is one of the cheapest, most-repeated craft signals on an award site. Underline thickness/offset stay tokens |
| Text input | A | pick | **10** | v1 | **Tier A: input chrome defines a system's voice as strongly as the button.** Tailwind ships 21 input groups |
| Textarea | B2 | pick | **5** | v1 | Inherits input chrome; only sizing/resize/counter vary |
| Select **[APG]** | B2 | pick | **6** | v1 | Native-vs-custom is a capability flag, not a variant |
| Combobox / autocomplete **[APG]** | B2 | pick | **5** | v2 | Behaviour dominates and must be identical across skins |
| Multi-select / token field **[BEH]** | B2 | pick | **4** | v3 | Overflow behaviour ("+3 more") is the only real decision beyond chip skin. **[BEH] APG Combobox (multi-select pattern) + `disclosure.dismissible-region` for token removal; each token's remove control needs its own accessible name ("Remove <token>")** |
| Checkbox **[APG]** | B1 | pick | **8** | v1 | The check animation is a small identity moment |
| Radio group **[APG]** | B1 | pick | **8** | v1 | Tailwind ships 12 because card-style and table-style radios are structurally different. **Present in the v1 set (§8.4) — it was missing from the previous hand-written v1 list, which would have shipped a form system with no radio group** |
| Toggle switch **[APG]** | B1 | pick | **8** | v1 | Knob motion and track treatment are visible brand micro-moments. **Present in the v1 set (§8.4) — it was missing from the previous hand-written v1 list** |
| Slider / range **[APG]** | B2 | pick | **6** | v2 | Dual-thumb is a capability flag across all six, not a separate family |
| Number stepper **[APG]** | B2 | pick | **4** | v3 | Low identity surface |
| Date picker **[BEH]** | B2 | pick | **5** | v2 | Locale/RTL correctness matters far more than skin. **[BEH] `input.date-time` — APG Date Picker Dialog: grid role, arrow-key navigation, `aria-selected`, Escape returns focus to the trigger. A text input alternative must always exist (2.5.7 / 1.3.5 `autocomplete="bday"` family where applicable)** |
| Time picker **[BEH]** | B3 | pick | **3** | v3 | Almost never on a marketing site. **[BEH] `input.date-time`; typed entry always available** |
| File upload / dropzone **[BEH]** | B2 | pick | **6** | v2 | The drop-target and the file-row are two design surfaces. **[BEH] `input.file-dropzone` — WCAG 2.5.7 Dragging Movements (AA): the drop target is a decoration on top of a real `<input type=file>`; keyboard and single-pointer upload must work with no drag. Upload progress and completion go through `live.announcer`** |
| OTP / PIN input **[BEH]** | B3 | pick | **3** | v3 | Behaviour (paste, backspace, `autocomplete=one-time-code`) matters more than skin. **[BEH] `input.segmented-code` — the segmented boxes are a presentation over one field or a labelled group; each box needs a name, and paste must fill the whole code** |
| Rating input **[BEH]** | B2 | pick | **4** | v3 | Must expose a real radio group underneath. **[BEH] APG Radio Group; the star glyphs are `aria-hidden` decoration over labelled radios** |
| Colour picker **[BEH]** | B3 | pick | **3** | v3 | Untitled ships 6 but they are mode variations, not designs. **[BEH] `input.two-dimensional` — a 2D saturation/value area needs arrow-key operation and a text entry alternative (2.5.7)** |
| Field group (label / help / error) | B2 | pick | **6** | v1 | **Tier A adjacent: this single decision reshapes every form on the site.** shadcn now ships it as a first-class "Field" |
| Form layout | B2 | pick | **6** | v1 | Tailwind ships only 4 because single-column is near-universally correct; 6 adds sectioned and inline |
| Multi-step form wizard **[BEH]** | B2 | pick | **5** | v3 | Composes stepper + form layout. **[BEH] `form.step-sequence` — focus and announcement on step change; errors from a failed step land in the Form error summary** |
| Inline email capture | B2 | pick | **6** | v1 | The smallest conversion unit; appears 2–4× per site |
| Contact form **[BEH]** | B2 | pick | **6** | v1 | Needs designed success/error/submitting — those are **states, not variants**. **[BEH] `live.announcer` for submit result + `form.validation` for the error path; the failed-submit path renders the Form error summary and moves focus to it. Every field carries its 1.3.5 `autocomplete` token (§8.7-A3)** |
| Form error summary **[BEH]** | B2 | pick | **4** | v1 | The list of errors rendered at the top of a failed form, each entry linking to its field. **Newly added — the inventory previously had only per-field errors (Field group), leaving the form-level error presentation undefined.** The standard remediation for WCAG 3.3.1 Error Identification and 3.3.3 Error Suggestion on multi-field forms, and the one form surface a design system must art-direct because it appears at the top of the page after a failed submit. The 4: bordered banner, inline list, card, sidebar-anchored. **[BEH] `form.validation` — focus moves to the summary on failed submit; each entry is a link to the field; the count is announced once** |
| Required / optional indicator policy | — | n-a | **n/a** | v1 | **Newly added policy row.** Asterisk-on-required vs "(optional)"-on-optional is a system-wide decision, not a per-form one, and it has an accessible-name consequence: a bare `*` must not end up inside the accessible name as "asterisk". The policy fixes the glyph, its `aria-hidden` treatment, the legend text, and the `required`/`aria-required` pairing. Not pickable — one answer applies to every form on the site |
| `autocomplete` field-purpose mapping | — | n-a | **n/a** | v1 | **Newly added policy row.** WCAG 2.2 SC 1.3.5 Identify Input Purpose (Level AA) requires the standard `autocomplete` token on every input collecting information about the user — name, email, tel, organization, street-address, country, postal-code, bday, and the rest of the WCAG-listed input-purpose set. Before this row, `autocomplete` appeared exactly once in the whole inventory (`one-time-code` on the OTP row), so every contact form and newsletter block in the v1 cut list would have shipped non-conformant. The mapping is a table, not a design choice. **The paired token item `interaction.autocomplete-map` is requested from §7 — see §8.8-X1** |
| Consent checkbox | B3 | pick | **3** | v1 | Legally constrained (unchecked by default, explicit, not bundled) |
| Search input control **[BEH]** | B2 | pick | **6** | v2 | Includes the expanding form (Carbon ships `ExpandableSearch` as a distinct component for this reason). **[BEH] `input.text-affordance` — `role="searchbox"` or `<input type=search>` in a labelled `<form role=search>`; the clear button has its own name; the expanded state moves focus into the field. `autocomplete="off"` here is deliberate and is the documented exception to §8.7-A3** |

#### Feedback

| Component | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Toast / snackbar **[BEH]** | B2 | pick | **6** | v2 | Position and stacking are configuration; semantic colour computed. **[BEH] `live.announcer` — `role="status"`/`aria-live="polite"` for informational, `role="alert"` for errors; auto-dismiss timing must satisfy WCAG 2.2.1 Timing Adjustable or not auto-dismiss at all when the toast carries an action** |
| Inline alert **[BEH]** | B2 | pick | **6** | v1 | Semantic colour computed from the ramp; only the shell varies. **[BEH] `live.announcer` when injected after load; a statically rendered alert is not a live region and must not be one** |
| Modal dialog **[APG]** | B1 | pick | **8** | v1 | The enter/exit choreography and scrim treatment are genuine identity choices |
| Confirm / alert dialog **[APG]** | B2 | pick | **4** | v2 | Deliberately constrained — the decision, not the design, is the point |
| Drawer / sheet **[BEH]** | B2 | pick | **6** | v2 | Tailwind ships 12 but half differ only by edge (config, not variant). **[BEH] `overlay.dismissible-layer` — identical focus trap, Escape, focus return and `inert` background as Modal dialog. This is the same primitive as Mobile drawer and Cart drawer; three skins, one audited behaviour** |
| Popover **[BEH]** | B2 | pick | **5** | v2 | arrow, arrow-less, elevated, bordered, glass. Collision logic shared. **[BEH] `overlay.popup-nonmodal` + WCAG 1.4.13 (§8.7-A1) for any hover-triggered instance. Coarse pointer: click/tap-triggered with an explicit close control** |
| Tooltip **[APG]** | B2 | pick | **6** | v1 | High frequency, small surface, low render cost. **A required companion to every icon button.** **WCAG 1.4.13 (AA) governs all 6 (§8.7-A1): dismissable with Escape without moving the pointer, hoverable (the pointer can travel into the tooltip without it vanishing), persistent until dismissed or invalid. Coarse pointer: the tooltip content must also be reachable another way — the icon button keeps its `aria-label`, and any information carried ONLY by the tooltip is a defect, because there is no reliable hover on touch** |
| Hover card **[BEH]** | B2 | pick | **4** | v3 | Desktop-only in origin, but **"degrade" is now defined, not assumed**: under `@media (hover: none)` or `pointer: coarse` the trigger becomes an explicitly tappable control that opens the same content as a dismissible popover with a visible close control; if the content is purely supplementary the variant may instead inline it. **Silently unavailable is not a permitted degradation** (§9 already forbids hover-only affordances). **[BEH] `overlay.popup-nonmodal` + WCAG 1.4.13 (§8.7-A1)** |
| Progress bar **[APG]** | B2 | pick | **5** | v2 | Indeterminate animation must respect reduced-motion |
| Spinner / loader | B1 | pick | **8** | v1 | **Tier A adjacent — one of the few components a visitor stares at.** arc, dots, bars, morph, logo-mark, orbit, pulse, custom-glyph, all with reduced-motion fallbacks |
| Skeleton placeholder **[BEH]** | B2 | pick | **5** | v2 | Per-component shapes derived from component geometry. **[BEH] `aria-busy` on the region being replaced; the shimmer is decorative and respects reduced motion** |
| Empty state | B1 | pick | **8** | v2 | NN/g treats empty states as a design discipline |
| Error state | B2 | pick | **6** | v2 | **Each must include a real recovery action** — that's a gate, not a variant |
| Success / confirmation state | B2 | pick | **5** | v2 | Animated check needs a reduced-motion equivalent |
| Cookie / consent banner **[BEH]** | B2 | pick | **6** | v1 | **The first thing a visitor sees, so it must be art-directed** — but legally constrained (reject as easy as accept) to 6. **[BEH] `overlay.dismissible-layer` in its blocking form / `disclosure.dismissible-region` in its non-blocking form; focus moves into the banner on appearance and returns to the document start on dismissal. It must not trap focus without offering a decision path** |
| Notification list / inbox **[BEH]** | B3 | pick | **3** | v3 | App-shell only. **[BEH] `live.announcer` for new arrivals (polite, batched) + `disclosure.dismissible-region` per row** |
| Badge / tag / pill | A | pick | **12** | v1 | Highest small-element count anywhere (Tailwind 16, Untitled 380 permutations) because it's combinatorially cheap. **12 shape-and-treatment variants; semantic colour and size computed** — this flag alone removes ~40% of a naive budget |
| Removable chip / filter chip **[BEH]** | B2 | pick | **6** | v2 | Material 3's four chip types plus dismiss-glyph treatments. **[BEH] `disclosure.dismissible-region` — each remove control carries "Remove <label>" as its accessible name, and removal announces the new result count through `live.announcer`. Backspace-to-remove is an addition, never the only route** |
| Status indicator dot | B2 | pick | **4** | v2 | **Must never be colour-only** |
| Avatar | B1 | pick | **8** | v2 | 8 shape-and-treatment designs; the rest computed |
| Avatar group / stack | B2 | pick | **4** | v2 | Derives skin from avatar |
| Kbd / keyboard key | B3 | pick | **3** | v3 | Docs and app-shell micro-surface |
| Toolbar **[APG]** | B2 | pick | **4** | v3 | Keyboard contract fixed by APG |

#### Data display

| Component | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Basic table **[APG]** | B1 | pick | **8** | v2 | **Each variant declares its own responsive strategy** (scroll container vs stacked cards) — otherwise this is the one component that breaks 390px |
| Data table **[APG]** | B2 | pick | **5** | v3 | Behaviour-dominant; skin derives from basic table |
| Description / spec list | B2 | pick | **6** | v2 | stacked, inline, two-column, bordered, striped, card-wrapped |
| Stat tile / KPI card | A | pick | **10** | v2 | Tier A for data-heavy sites. **The delta treatment must never be colour-only** — the arrow glyph or the sign is the non-colour carrier, per the same rule as Status indicator dot. **Chart accessible-alternative contract applies where a tile embeds a sparkline (§8.7-A4)** |
| Sparkline | B2 | pick | **4** | v2 | line, area, bar, win-loss — the complete standard set. **Non-text content: each ships an accessible name plus either a visually-hidden value summary or `aria-hidden` when the adjacent number already states the value (§8.7-A4)** |
| Line chart | B2 | pick | **6** | v2 | single, multi-series, stepped, smoothed, confidence-band, annotated |
| Area chart | B2 | pick | **4** | v2 | single, stacked, 100% stacked, stream |
| Bar / column chart | B1 | pick | **8** | v2 | vertical/horizontal × plain/grouped/stacked/100% |
| Pie / donut chart | B2 | pick | **4** | v2 | Deliberately small — only defensible for ≤5 categories and should be discouraged beyond |
| Gauge / progress ring | B2 | pick | **6** | v2 | arc, full ring, segmented, multi-ring, needle, bullet |
| Scatter / bubble | B3 | pick | **3** | v3 | scatter, bubble, with-trendline |
| Heatmap | B3 | pick | **3** | v3 | matrix, calendar, density. Ramp computed and colourblind-checked |
| Funnel chart | B3 | pick | **3** | v3 | tapered, stepped-bar, sankey-lite |
| Radar chart | B3 | pick | **3** | v3 | single, overlaid, filled |
| Waterfall chart | B3 | pick | **3** | v3 | Finance-standard, specialised |
| Treemap | B3 | pick | **2** | v3 | flat, nested-with-headers |
| Map (pin / choropleth) **[3P]** | B2 | pick | **4** | v3 | **Tile-provider licensing is a hard gate, not a design choice.** **[BEH] a map is exempt from 1.4.10 reflow but not from 1.1.1 — a text list of the plotted locations is the required alternative** |
| Chart chrome kit | B2 | pick | **4** | v2 | minimal, gridded, bordered-technical, editorial. **One decision applied across all 12 marks — this is what makes a site's charts read as one system.** **The chrome kit is also where the accessible-alternative slot lives (caption, source line, and the visually-hidden data table container), so it ships once and every mark inherits it (§8.7-A4)** |
| Chart colour ramps | — | computed | derived | v2 | From OKLCH anchors per D1. The `dataviz` skill ships a runnable validator |
| Chart accessible-alternative contract | — | n-a | **n/a** | v2 — ships with the first chart | **Newly added contract row.** WCAG 1.1.1 Non-text Content is Level A and a chart is non-text content by definition, yet §7.11 covers only colour. Every chart mark (the 12 marks + Sparkline + any Step-6 custom chart) must emit: (1) an accessible name and a short description — `role="img"` with `aria-label`/`aria-labelledby` for a static SVG, or a `<figure>`/`<figcaption>` pair; (2) either a visually-hidden data table or a one-sentence text summary carrying the same information as the mark; (3) a non-colour carrier for every distinction the mark makes — series identity, delta sign, threshold crossing — matching the existing stat-tile and status-dot rules. **Because §20.1/§17-O14 put v1 charts on a build-time SVG path, the alternative must be emitted at build time or it does not exist at all.** Gated at LOCK by proposed gate 31 (§8.7-A4). **The user named graphs and charts explicitly (vision step 6), so this is a named feature that was heading for release without its Level A floor** |
| Progress steps / stepper **[BEH]** | B2 | pick | **6** | v2 | Untitled reports 489 permutations, mostly state × orientation; 6 distinct designs. **[BEH] `nav.current-location` — `aria-current="step"`; a numbered circle is not a name** |
| Tree view **[APG]** | B3 | pick | **3** | v3 | Behaviour-dominant, app-shell only |
| Calendar **[BEH]** | B2 | pick | **4** | v3 | month, week, day, agenda-list. **[BEH] `input.date-time` grid contract; the same primitive as Date picker** |
| Kanban board **[BEH]** | B3 | pick | **3** | v3 | App-shell only. **[BEH] WCAG 2.5.7 — every card move available without dragging (a "move to column" menu); this is the clearest 2.5.7 case in the inventory** |
| Code block **[BEH]** | B2 | pick | **5** | v2 | **Highlight theme derived from the direction's palette**, never imported, or it clashes with everything. **[BEH] the copy control announces success through `live.announcer`; the pre/code region is keyboard-scrollable when it overflows** |
| Activity feed **[BEH]** | B2 | pick | **4** | v3 | timeline, compact-list, grouped-by-day, with-comments. **[BEH] `live.announcer` only when the feed streams; a static feed is not a live region** |

#### Media

| Component | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Image figure / frame | A | pick | **10** | v1 | **Tier A** — the frame (bleed, inset, masked, tilted, layered, bordered, shadowed) is where the direction shows on every photo |
| Image gallery grid | B1 | pick | **8** | v2 | Portfolio and case-study sites live on this |
| Lightbox **[APG]** | B2 | pick | **4** | v2 | Focus-trap and keyboard contract fixed; only chrome and transition vary |
| Carousel / slider **[APG]** | B1 | pick | **8** | v2 | peek, full-bleed, centred, coverflow, thumbnail-synced, drag-only, ticker-hybrid, stacked |
| Before/after slider **[BEH]** | B3 | pick | **3** | v3 | All three need a keyboard-accessible fallback. **[BEH] APG Slider + WCAG 2.5.7 — arrow keys move the divider; a drag-only implementation fails at AA** |
| Video player skin **[BEH]** | B2 | pick | **6** | v2 | Captions and keyboard control non-negotiable across all six; **the poster frame is what most visitors actually see**. **[BEH] `media.player-controls` — labelled controls, captions track, no keyboard trap, and 2.2.2 satisfied by the transport controls themselves** |
| Third-party video facade **[BEH]** | B2 | pick | **4** | v2 | **Saves ~500KB–1MB of pre-interaction JS.** Exists for the performance gate as much as for design — the naive embed is a Lighthouse killer. **[BEH] the facade is a real button with an accessible name ("Play <video title>"); activating it must move focus into the loaded player** |
| Background video loop **[BEH]** | B2 | pick | **5** | v2 | Loop engineering and a 4–16s cap constrain all five. **WCAG 2.2.2 Pause, Stop, Hide (Level A) is mandatory on all five (§8.7-A2): a 4–16s auto-playing loop exceeds the 5-second exemption, so every variant ships a visible pause/stop control — placed inside the container's bottom-inline-end safe zone, ≥24×24 CSS px (2.5.8), ≥3:1 against the busiest frame of the loop (1.4.11), and persistent (not hover-revealed, because hover does not exist on touch).** The control may delegate to the site-wide Auto-motion pause/stop control but must be reachable in the tab order near the video. `prefers-reduced-motion` alone does NOT satisfy 2.2.2. **[BEH] `motion.auto-started` + `media.player-controls`** |
| Audio player **[BEH]** | B3 | pick | **3** | v3 | Rare on marketing sites. **[BEH] `media.player-controls`; any auto-playing audio longer than 3 seconds also triggers WCAG 1.4.2 Audio Control (Level A) — default to not autoplaying** |
| Icon set | C | pick | **20** | v1 | Artwork tier. 20 candidate **SETS**, not 20 icons. Recraft V4 is the only true native-SVG generator per the prior report. Grid, stroke width, corner style are tokens shared by all icons in a set |
| Illustration set | C | pick | **20** | v2 | Artwork tier; parallel-scannable as a filtered grid |
| Decorative spot-graphic set | C | pick | **20** | v1 | Artwork tier, **disproportionately high identity return per unit of effort** — the marks that make a page feel hand-made |
| Pattern / texture library | C | pick | **20** | v1 | Artwork tier. **The single cheapest anti-slop move available** — the flat-gradient-card look is an enumerated AI tell |
| Logo lockup set | B2 | pick | **6** | v1 | The standard brand deliverable set; arrangements of a fixed mark |
| Photography treatment | B1 | pick | **8** | v2 | Applied globally — a direction-level decision. **The implementation of the ban on unstyled stock** |
| 3D model / product viewer **[BEH]** | B3 | pick | **3** | v3 | GPU-tier ladder is a gate, not a variant. **[BEH] WCAG 2.5.7 — orbit/zoom must have non-drag equivalents; a static poster image with alt text is the required fallback** |
| Gaussian splat embed | B3 | pick | **2** | v3 | Differentiation lives in the captured content, not the container; bandwidth caps how many can exist |

#### Motion / art containers — see §9

The 16 container kinds and 15 animation kinds live in §9 per **D4** — motion is an ordinary design-system item and animated pieces sit in the same draggable containers as artwork, so they are inventoried there rather than duplicated here. **They are counted in this section's totals wherever a total is stated** (§8.2's ~240 items, §8.4's v1 arithmetic), because the previous text's figures silently included them and the reconciliation failed as a result. Tier and Pick columns apply to §9's rows on the same rule: `motion.expressiveness` and the easing/duration matrices are `computed`, container kinds and animation kinds are `pick`, and the signature moment is deliberately **not** a swap catalogue.

#### Utility

| Component | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Layout container widths | — | computed | derived | v1 | **Also what the editor's gridlines snap to per D2** — must be data, not decoration |
| Editor grid overlay | — | n-a | **n/a** | v1 | Editor chrome, not a site component |
| Theme toggle **[BEH]** | B2 | pick | **6** | v2 | icon switch, segmented tri-state, animated sun/moon, text link, in-menu, auto-with-override. **The transition between themes is a visible craft moment**; needs a no-flash first-paint strategy. **[BEH] a real control with state (`aria-pressed` for binary, radio group for tri-state); the change is announced once. The tri-state variant is what exposes `prefers-contrast: more` where a direction ships the third solve (§7.2)** |
| Motion toggle **[BEH]** | B3 | pick | **3** | v1 | Compliance item, minimal latitude. footer, header, first-visit prompt. **[BEH] persisted preference that overrides `prefers-reduced-motion` in both directions; it is the site-wide half of the 2.2.2 story but does NOT replace per-component pause controls (§8.7-A2)** |
| Auto-motion pause/stop control | B3 | pick | **3** | v1 | **Newly added component.** The single shared control that satisfies WCAG 2.2.2 Pause, Stop, Hide (Level A) for every auto-moving thing on the page: marquee/ticker (§9), background video loop, auto-advancing carousel, scroll-linked counters, ambient background motion. The 3: in-container corner control, section-level control in the section chrome, page-level floating control. Each is ≥24×24 CSS px (2.5.8), ≥3:1 against the busiest frame behind it (1.4.11), keyboard-reachable adjacent to the thing it controls, and persistent rather than hover-revealed. **It is a component, not a token, because its placement is a composition decision — but its behaviour is one audited primitive `motion.auto-started`** |
| Pointer / hover capability policy | — | n-a | **n/a** | v1 | **Newly added policy row.** The site-wide rule for `@media (hover: hover)`, `@media (hover: none)`, `pointer: fine` / `pointer: coarse` and `any-pointer`: which affordances may be hover-only (none that carry information), what each hover-triggered family does on a coarse pointer, and the fact that a hybrid device can report both. Consumed by Tooltip, Popover, Hover card, Dropdown/flyout, Mega menu, the cursor-effect layer and every §9.3 hover micro-reaction. **The paired token item `interaction.pointer-capability-policy` is requested from §7.4 — see §8.8-X1** |
| Sound toggle **[BEH]** | B3 | pick | **3** | v2 | Must default off and persist. **[BEH] state-carrying control; WCAG 1.4.2 for any sound over 3 seconds** |
| Age gate **[BEH]** | B3 | pick | **3** | v2 | Legally shaped; must not block crawlers or LCP unnecessarily. **[BEH] `overlay.dismissible-layer` without an Escape dismissal (the decision is the exit); focus starts inside it** |
| Social links row **[3P]** | B2 | pick | **5** | v1 | Marks must not be redrawn to match the direction |
| Social share row | B2 | pick | **4** | v2 | Privacy-preserving implementation (plain intent URLs, no SDKs) constrains all four |
| Sticky mobile CTA **[BEH]** | B2 | pick | **4** | v2 | Must not obscure the footer or form fields — a gate, not a design choice. **[BEH] `overlay.sticky-obstruction` — the same 2.4.11 contract as the sticky ribbon and the mobile action bar** |
| Cookie preferences centre **[BEH]** | B3 | pick | **3** | v2 | modal, drawer, page. Reject as easy as accept in all three. **[BEH] `overlay.dismissible-layer` for the modal and drawer forms; each category is a labelled group of real switches, and "save" announces the result** |
| OG / social share card template | B3 | pick | **3** | v1 | Generated at build time from the direction's type and colour |
| Favicon / app-icon set | — | n-a | **n/a** | v1 | Derived export from the logo mark. Routinely missing from AI-built sites |
| Anti-spam honeypot / timing check | — | n-a | **n/a** | v2 | A contact form without it is a delivery defect; CAPTCHA is an accessibility and privacy cost |

#### Page templates

| Template | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Home / landing | B2 | pick | **6** | v1 | proof-early, story-led, product-led, comparison-led, single-scroll-narrative, directory-style |
| About | B2 | pick | **4** | v2 | Largely recomposition |
| Product / feature | B2 | pick | **5** | v2 | Most-duplicated on B2B sites; the sequence must survive being repeated 6–10× |
| Pricing | B2 | pick | **4** | v1 | Order (cards → matrix → FAQ → CTA) close to fixed by conversion evidence |
| Blog index | B2 | pick | **4** | v2 | Drives CMS collection wiring |
| Blog post | B2 | pick | **4** | v2 | Prose treatment is a separate component; the template decides furniture placement |
| Case study | B2 | pick | **4** | v2 | Highest-value page type on an agency/B2B site |
| Contact | B2 | pick | **4** | v2 | Conventional by design — visitors arrive with a task |
| Team | B3 | pick | **3** | v3 |  |
| Careers + job detail | B3 | pick | **3** | v3 | Usually ATS-fed, which constrains layout |
| Legal | B3 | pick | **2** | v1 | plain, TOC-sidebar. Required for Play/App Store and GDPR, deliberately un-art-directed |
| 404 | B2 | pick | **6** | v1 | **All six required to carry a working search or nav back to real content** |
| 500 / error | B3 | pick | **3** | v2 | **All self-contained (inline critical CSS)** because the failure may be in the asset pipeline itself |
| Coming soon / waitlist | B2 | pick | **4** | v2 | Often the first thing shipped |
| Press kit | B3 | pick | **3** | v2 | The dopresskit() convention journalists expect; novelty is counterproductive |
| Search results | B3 | pick | **3** | v3 | The zero-result state is what actually matters |
| Auth screens | B2 | pick | **5** | v3 | App-shell only; backend-free via MSW mocking |
| Dashboard shell | B2 | pick | **4** | v3 | Every state must be screenshot-QA'd |
| Settings | B3 | pick | **3** | v3 | tabbed, sidebar-nav, single-scroll |
| Docs | B3 | pick | **3** | v3 | Heavily standardised; deviation costs comprehension |
#### States — not variants, never picked

| State set | Pick | Rationale |
|---|---|---|
| Interactive state matrix (default / hover / active / focus-visible / disabled / loading / selected / error) | n-a | **`focus-visible` is the state AI-generated sites most often omit, and its absence is a WCAG 2.4.7 failure** |
| Full 22-state coverage checklist (adds focus-within, read-only, checked, indeterminate, expanded, current-page, visited, warning, success, dragging, drop-target, empty, skeleton) | n-a | The state layer supplies the VALUES (4 opacities); this supplies the COVERAGE. Missing states are the most common completeness failure in generated systems |
| Data state set (empty / loading / partial / error / success) | n-a | Required for every list, grid, table and chart |
| Chart data states (+ single-data-point) | n-a | Charts fail more often in these states than in the happy path |
| Responsive breakpoint set (320 / 390 / 768 / 1280 / 1440) | n-a | **The enforcement mechanism for D2** |
| Theme state set (light / dark / forced-colors) | n-a | Low-contrast dark mode is an enumerated AI-slop tell |
| **High-contrast state (`prefers-contrast: more`)** — *added in this revision* | n-a | **§7.2 generates a third colour solve at an elevated contrast multiplier, and before this row nothing ever rendered, captured or verified it.** A generated-but-never-viewed scheme is worse than none, because §13's proof tables would report the direction as compliant while no human or gate had ever seen that scheme. Render condition: **spot-checked, not swept** — 2 captures per selected variant (390 and 1280, light-source scheme), plus the full §13.4 gate-7 contrast sweep run against the elevated solve |
| **Text-spacing override state (WCAG 1.4.12, Level AA)** — *added in this revision* | n-a | Line-height 1.5×, paragraph spacing 2×, letter-spacing 0.12em, word-spacing 0.16em applied as a user stylesheet. §13.4 gate 10 already tests it at page level; this row makes it a **component-level** coverage state, because fluid type, computed `size.control-heights` and drag-positioned blocks are all clipping candidates and the page-level gate only catches the ones that happen to be on the page at LOCK. Render condition: **spot-checked** — 2 captures (320 and 1280) |
| **Pointer / hover capability state (`hover: hover` / `hover: none` + `pointer: coarse`)** — *added in this revision* | n-a | Every hover-triggered row in §8 (Tooltip, Popover, Hover card, Dropdown/flyout, Mega menu — 28 variants between them), the custom cursor and the §9.3 hover micro-reactions render differently or must not render at all under a coarse pointer. Without this state nothing ever proves the touch path exists. Render condition: **spot-checked** — 1 capture at 390 with `hover: none, pointer: coarse` emulated, plus a keyboard/tap interaction check for each hover-triggered family |
| Motion state set (full / prefers-reduced-motion) | n-a | The reduced render must **differ** where motion exists AND still look designed |
| RTL / bidi state | n-a | Only if multi-language, but then it must be built with logical properties from the start |
| Long-content / pseudolocalisation (+35% string expansion) | n-a | The cheapest way to catch fragile-layout defects that QA on ideal copy never sees |
| 200% zoom reflow (WCAG 1.4.10) | n-a | Level AA, and a common failure for fluid type scales — which is exactly what Utopia generates |
| Print state | n-a | The alternative is a page that prints unusably on legal and pricing pages |
| No-JS / progressive enhancement | n-a | **Also the crawler's view, so SEO depends on it** — and reveal-on-enter animations are the classic way an AI-built page ships invisible content to a no-JS client |
| State transition map | n-a | Derived. **The instant list matters: focus rings must appear instantly; animating a focus ring is an accessibility defect** |

#### Render-cost arithmetic (corrected and disambiguated)

The previous single line — *"True render cost per selected variant: ~20 captures (5 breakpoints × 2 themes × 2 motion)"* — was read by a later auditor as applying to every **generated** variant, which would put v1 QA at ~11,000 captures. It does not, and the ambiguity was the defect. There are **two** budgets and they are different by an order of magnitude:

| Budget | Formula | v1 figure | Notes |
|---|---|---|---|
| **Generation-time thumbnails** — one per generated variant, per theme, at 200×120 for the component bar | `variants × 2` | **1,348 renders** (674 v1 variants × 2) | Cheap, headless, cached per direction. §17-R29's lazy generation means only opened families are paid for |
| **Generation-time differentiation comparisons** — the §8.5 indistinguishability rule, run pairwise inside each component | `Σ n(n−1)/2` per component | **2,784 comparisons** | Pure image math on thumbnails already rendered above; no extra renders |
| **Lock-time verification captures** — per **selected** variant actually placed on the page | `20 swept + up to 10 conditional` | **≤30 per placed variant** | Swept: 5 breakpoints × 2 themes × 2 motion = 20. Conditional spot-checks added by this revision: high-contrast 2, text-spacing 2, coarse-pointer 1; already present: forced-colors 1, RTL 2 (multi-language only), print 1, no-JS 1, 200% zoom 1 |

**Open question O31 (new): how many distinct selected variants does a real v1 page carry?** The lock-time figure cannot be turned into a total until that number exists, and it depends on the page template. **No known mitigation beyond measuring it on the first real build — do not put a total in §13's budget until it is measured.** [I — inference; the per-variant figures above are arithmetic, the page total is not yet knowable.]

Budget for both, and gate the lock-time set at LOCK, not during editing.

### 8.4 The v1 cut list — **generated from the Priority column, not hand-written**

The previous v1 list was written by hand and drifted from the table it claimed to summarise. It omitted four components that the table itself marks **v1** — **Dropdown / flyout menu (7)**, **Radio group (8)**, **Toggle switch (8)** and **Platform CTA badge registry (5)** — which would have shipped a form system with no radio group and no toggle switch, and a commerce CTA with no badge registry. Its stated totals ("~50 pickable items, ~430 generated variants") were also below what its own named entries summed to.

**The fix is procedural, not editorial: §8.4 is regenerated from the Priority column on every PRD build.** If a row's Priority cell says v1, it is in this list; there is no second place to edit.

**Arithmetic, shown.**

| Family | Pickable v1 items | v1 variants | v1 items |
|---|---|---|---|
| **Navigation** | 6 | 43 | Top ribbon / primary navigation 10; Nav scroll behaviour 6; Dropdown / flyout menu 7; Mobile drawer / full-screen overlay menu 10; Skip link 2; Tabs / in-page switcher 8 |
| **Hero** | 3 | 28 | Marketing hero 12; Interior page header 8; Hero CTA cluster 8 |
| **Content** | 18 | 151 | Section header block 10; Feature grid 12; Feature split (alternating) 8; Bento grid 6; Generic content card 12; Card grid / collection layout 8; Rich text / prose body 6; Content + media section 8; Process / how-it-works steps 8; Stat band 8; Pull quote 8; FAQ / accordion 8; Section divider / seam 10; Section wrapper 8; CTA band 12; Newsletter block 6; Footer 10; Legal / policy body 3 |
| **Social proof** | 3 | 24 | Logo wall 8; Logo marquee 6; Testimonial card 10 |
| **Commerce** | 4 | 31 | Pricing section 12; Plan card 10; Pricing period toggle 4; **Platform CTA badge registry 5** |
| **Form** | 17 | 122 | Primary button 10; Secondary button 10; Ghost / tertiary button 8; Icon button 8; Inline text link 10; Text input 10; Textarea 5; Select 6; Checkbox 8; **Radio group 8**; **Toggle switch 8**; Field group (label / help / error) 6; Form layout 6; Inline email capture 6; Contact form 6; **Form error summary 4**; Consent checkbox 3; *plus two n-a policy rows: Required/optional indicator policy, `autocomplete` field-purpose mapping* |
| **Feedback** | 6 | 46 | Inline alert 6; Modal dialog 8; Tooltip 6; Spinner / loader 8; Cookie / consent banner 6; Badge / tag / pill 12 |
| **Media** | 5 | 76 | Image figure / frame 10; Icon set 20; Decorative spot-graphic set 20; Pattern / texture library 20; Logo lockup set 6 |
| **Utility** | 4 | 14 | Motion toggle 3; **Auto-motion pause/stop control 3**; Social links row 5; OG / social share card template 3; *plus four non-pick rows: Layout container widths (derived), Editor grid overlay (n/a), **Pointer / hover capability policy (n/a)**, Favicon / app-icon set (n/a)* |
| **Page templates** | 4 | 18 | Home / landing 6; Pricing 4; Legal 2; 404 6 |
| **§8.3 subtotal** | **70** | **553** | 76 rows including 6 `computed`/`n-a` rows |
| **§9 motion and art containers (v1 rows in §9.2 + §9.3)** | **17** | **121** | Still container 4; generic CSS/GSAP container 8; background layer 10; marquee container 6; reveal-on-enter 8; cursor-effect layer 5; hover micro-reactions 10; hero entrance 8; section reveal 10; text reveal 10; scroll reveal 6; marquee 6; loading states 6; custom cursor 10; background ambient motion 8; signature moment 2 (concept candidates, not a swap catalogue); smooth-scroll 4 |
| **v1 TOTAL** | **87 pickable items** | **674 variants** | |

`70 + 17 = 87`. `553 + 121 = 674`.

**Everything else is v2/v3:** 93 rows / 508 variants at v2 and 47 rows / 167 variants at v3 in §8.3, plus §9's v2/v3 rows. **Sixty-two items are app-shell, commerce, or exotic-chart and generate only when the interview's site-type answer requires them** (§17-R35).

> **⚠ REQUIRES USER SIGN-OFF — v1 scope correction.**
> The mechanically-generated v1 set is **87 pickable items / 674 variants**. The figure §18's phasing and §13's render budget were built on was **"~50 items / ~430 variants"**. That is a **~74% increase in items and ~57% in variants** — it is a real scope change, not a re-count of the same thing, and it arrives from three sources: (a) four v1-priority components the hand-written list simply missed; (b) §9's 17 v1 motion/art items, which the old list named inline but never counted; (c) three components/policies added by this revision (Form error summary, Auto-motion pause/stop control, plus four non-pick policy rows).
> **Three options, and this is the user's call, not the PRD's:**
> 1. **Accept 87/674 as v1** and re-baseline §18's phase sizing and §13's budget against it.
> 2. **Demote specific rows to v2** — each demotion must be made in the Priority cell with a stated reason, and §8.4 then regenerates itself. The four previously-missing items are the obvious candidates *except* Radio group and Toggle switch, which cannot be demoted without shipping an incomplete form system.
> 3. **Split v1 into v1a/v1b** inside the same Priority column.
> **No option is chosen here.** Until one is, §18 and §13 are sized against a number this section does not support.

### 8.5 Component-bar presentation rules

Choice overload is **not** automatic. Chernev, Böckenholt & Goodman (2015, *Journal of Consumer Psychology* 25:333–358) meta-analysed 99 observations (N=7,202) and found the mean effect of assortment size **not reliably different from zero** — it appears only under four moderators: set complexity, task difficulty, preference uncertainty, and decision goal. **[V]** Every one is engineerable away — **and, as of this revision, each engineering fix is defined precisely enough to build and to test**, which §20.2 #2 records as the condition the whole 10-variant decision rests on:

| Moderator | Engineering fix | How it is measured |
|---|---|---|
| Preference uncertainty | Render variants **in the real page slot at real scale**, with the current copy and neighbours | Binary: the strip renders in-slot or it does not |
| Set complexity | Sort by **structural distance** from the current pick (§8.5.1); **label the differing axis** (§8.6 supplies the axis names); skeleton filter chips at and above 12 items | Distance is a computed integer; the label is the argmax axis. Both are assertable in a unit test |
| Task difficulty | Pre-select the direction's canonical variant; Esc reverts in one key | Binary |
| Decision goal | Not-choosing is free and costless | Binary |

**Under those conditions 10 is safe.** The failure case is real when variants are undifferentiated — Iyengar & Lepper (2000): 24 jams attracted 60% of passers but converted 3%; 6 jams attracted 40% and converted 30%, with higher post-choice satisfaction **[V]**. The mitigation is not fewer options but **more different** options.

#### 8.5.1 Structural distance — defined

Previously "structural distance" was named as the mitigation for the set-complexity moderator and never defined, which made both the sort order and the "label the differing axis" caption unbuildable. It is now a function of the variant axis vector declared in §8.6.

Given two variants `a`, `b` of the same component with axis vector `A = [a₁…aₖ]`:

```
distance(a, b) = Σᵢ wᵢ · dᵢ(aᵢ, bᵢ)

  dᵢ = 0 or 1                      for a NOMINAL axis (media-side, framing, …)
  dᵢ = |rank(aᵢ) − rank(bᵢ)| / (levelsᵢ − 1)   for an ORDINAL axis (density, column-count, …)
  wᵢ = the axis's declared weight, default 1
```

- **Sort order:** the current pick is pinned first; the remainder ascend by distance, so the strip reads left-to-right as "nearly this" → "nothing like this". Ties break by generation index for determinism (§17-R15 requires the strip order to be reproducible).
- **"Label the differing axis":** the caption under each thumbnail names the axis with the largest `wᵢ · dᵢ` contribution, rendered as `axis: value` (e.g. `media: left` / `density: airy`). When two axes tie, both are shown. **This is why §8.6 exists** — without a declared axis vector there is nothing to name.
- **Filter chips** are generated from the axis vector as well: one chip group per axis whose values vary across the set. This is what makes the 20-item artwork tier legal (§17-R34) rather than a wall of thumbnails.

#### 8.5.2 "Indistinguishable at 200×120px" — defined

The hard rule stood as *"if two variants are indistinguishable at 200×120px, one must be regenerated or deleted"* with no metric, no threshold, no judge, and no stated render conditions — so the failure mode the section itself identifies (§17-R33, the jam study) had no enforceable gate. It is now a two-stage check, run **at generation time** (proposed gate 34 below), and deliberately **deterministic**: §20.1 excludes the VLM aesthetic judge, so no model opinion is in this loop.

**Stage 1 — structural (free, exact, runs first).** If two variants of the same component have **identical axis vectors** (§8.6), they are by definition not structurally distinct (§8.1) and one is deleted before rendering. This alone catches the common generator failure of emitting the same composition twice with different copy.

**Stage 2 — perceptual (runs on the pairs that survive stage 1).** Render both thumbnails at exactly **200×120 CSS px, at 2× device pixel ratio, in the light and dark schemes, at the 1280 breakpoint, with identical placeholder copy and identical placeholder imagery** (holding copy and image constant is what makes the comparison about structure rather than content). A pair is **flagged** when, in **both** schemes:

- **SSIM ≥ T_ssim** on the greyscale thumbnails, **and**
- **mean CIEDE2000 ΔE00 ≤ T_colour** across the thumbnail.

**Seed values: `T_ssim = 0.98`, `T_colour = 2.0`. [I — inference, not a validated threshold.]** The ΔE00 side has a conventional anchor (ΔE00 ≈ 1.0 is the commonly cited just-noticeable-difference for a trained observer under controlled viewing, and 2.0 is a conventional "close match" tolerance); **the SSIM figure has no source and is an engineering guess.** Both must be calibrated against a real generated set before the rule can be called enforced — **new open question O32.** Until calibration, the check runs in **advisory** mode (it flags, it does not delete) and the flag is shown in the component bar as a "these two are near-identical" affordance, which is honest and still better than the previous unenforceable prose.

**Judge:** the metric flags; **regeneration is automatic, deletion is not.** A flagged pair triggers one regeneration attempt of the later-indexed variant with a forced axis change (the generator is given the pair's axis vector and told which axis to move). If the regenerated variant flags again, the variant is **dropped from the set and the set ships short** with the shortfall recorded in the direction's provenance record — a set of 9 differentiated variants is worth more than 10 with a twin, and the recorded shortfall is what stops the "cannot drift" claim from quietly becoming false.

#### 8.5.3 Presentation by set size

Hick's law is the **wrong** model for a thumbnail grid and must not be used to justify small sets. Hick–Hyman is robust for random serial search; a grid of visually distinct rendered thumbnails supports **parallel feature-based visual search** — "the one with the image on the left" is found in parallel. A feature-sorted 10-thumbnail grid scans near-constant-time; a 10-item unordered text dropdown does not. **The component bar must be visual and feature-sorted, never a text dropdown. [V — visual-search literature; IxDF on Hick–Hyman limits]**

The previous presentation spec covered only the 10-variant case, leaving the six 12-variant Tier A components sitting exactly on the filter-chip boundary, the four 20-item artwork sets (plus §7.9's 20-piece background/hero artwork) with no spec at all, and the post-append state of "More like this" undefined. The ladder:

| Set size | Presentation | Filter chips | Notes |
|---|---|---|---|
| **2–10** (Tier B, Tier A at 10) | **Strip** — 5 thumbnails visible, arrow/scroll to reach the rest | No | The original spec, unchanged |
| **11–14** (the six Tier A 12s; also a 10-set after one "More like this" append) | **Two-row strip** — 6 visible per row, 12 visible without scrolling | **Yes, from 12** — the boundary is resolved as *chips appear at ≥12*, so all six Tier A 12-variant components get them | Chips are generated from the varying axes (§8.5.1) |
| **15–25** (a 20-set after one append; a 12-set after two) | **Filtered grid**, not a strip — 4 columns × as many rows as needed, scrolls within the panel | Yes | The strip metaphor breaks here; converting to a grid is a mode change the panel makes automatically and announces ("showing 20 of 20") |
| **20** (Tier C artwork: icon sets, illustration sets, spot graphics, patterns, §7.9 artwork) | **Filtered grid from the start** — never a strip. §8.3 #Media already describes artwork as "parallel-scannable as a filtered grid"; this makes it the specified behaviour rather than an aside | **Yes, mandatory** — per §17-R34, *filters are what make 20 legal* | Chips for artwork come from the artwork tags (direction tag per D1, plus subject, technique, density). Hover preview still renders in the real slot |
| **>25** | Not reachable by design | — | See the append cap below |

**Append behaviour ("More like this").** Generates 5 neighbours of the selected variant — neighbours meaning *small* structural distance (one axis moved), which is what "like this" means once §8.5.1 exists — and appends them. Appended items are visually separated by a divider labelled "new", are sorted by distance from the seed, and are subject to the same §8.5.2 differentiation check against the whole existing set, not just against each other. The panel converts strip → grid automatically when the count crosses 15.

**Append cap: a set may not exceed 25 items. [I — inference; the number is an engineering choice, not a researched threshold. Requires user decision if it proves wrong in use.]** At the cap, "More like this" is replaced by "Replace the 5 lowest-distance items" — because the failure being avoided is a set that grows toward the mean, which is exactly the jam-study condition the section exists to prevent.

**Unchanged from the original spec:** hover previews live in the slot, click commits, Esc reverts, the current variant is pinned first and pre-selected, **"Compare 3"** opens a full-width triptych (3 is the number for deliberate comparison — matching the existing `acos-design-variants` skill precedent).

### 8.6 The variant axis schema (new in this revision)

§8.5's sort order, its axis captions, its filter chips and its stage-1 differentiation check all require something the PRD never specified: **a declared, enumerated set of axes per component.** Without it, "structural distance" and "label the differing axis" are prose. With it, both are arithmetic.

**Contract.** Every `pick` row in §8.3 and §9 declares 3–7 axes. Each axis has a name, a type (`nominal` | `ordinal`), an enumerated value list, and an optional weight. The vector is emitted with the variant, stored in the design-system artifact, and is what the editor sorts, filters, captions and dedupes on. **A variant with no axis vector cannot enter the component bar** — this is the mechanical enforcement of §8.1's definition.

**Worked examples** (illustrative; the full per-component schema is a build artifact, not PRD prose):

| Component | Axes |
|---|---|
| Marketing hero (12) | `media-position` {none, left, right, background, below, split} · `column-count` {1,2} *(ordinal)* · `alignment` {left, centre} · `density` {compact, regular, airy} *(ordinal)* · `framing` {flat, framed, bleed} · `cta-arrangement` {inline, stacked, single} |
| Generic content card (12) | `media-position` {none, top, left, background} · `elevation` {flat, bordered, shadowed, layered} *(ordinal)* · `meta-placement` {none, top, bottom, overlay} · `aspect` {from the §7.4 ratio set} · `hover-treatment` {none, lift, reveal, zoom} |
| Primary button (10) | `fill` {solid, gradient, tinted, glass} · `edge` {sharp, soft, pill} *(ordinal)* · `border` {none, hairline, heavy} *(ordinal)* · `motion` {none, lift, sweep, morph} · `icon-slot` — **not an axis: computed per §8.1** |
| Section divider / seam (10) | `geometry` {rule, shape, wave, angle, notch, overlap} · `weight` {hairline, medium, heavy} *(ordinal)* · `bleed` {inset, full} · `texture` {none, grain, pattern} |
| Icon set (20, Tier C) | `stroke-style` {line, solid, duotone, hand} · `corner` {sharp, rounded} · `grid` {16, 20, 24} *(ordinal)* · `weight` {light, regular, bold} *(ordinal)* — *set-level axes, shared by every icon in the set* |

**Open question O33 (new): who writes the axis schema?** Three candidates — (a) hand-authored once per component family in the skill (~90 pickable families at v1, so a real one-time cost); (b) generated by claude.ai as part of the Step-2 design-system prompt, which risks drift between directions and would break cross-direction comparison; (c) inferred post-hoc from the generated variants, which is the least reliable and cannot enforce stage-1 dedupe because the inference would just describe whatever was produced. **The PRD's inference is (a), because determinism matters more here than effort (§17-R15) — but this is a real effort line that §18 does not currently carry, and it requires user decision.**

### 8.7 Accessibility contracts carried by this inventory (new in this revision)

Four WCAG criteria are load-bearing for components specified in §8 and were named nowhere. Each is stated here with the components it binds and the gate that proves it. **Gate numbers continue §13.4's existing sequence (which ends at 28); these are proposed additions to that checklist, not a renumbering of it.**

| Id | Criterion | Binds | Proposed gate |
|---|---|---|---|
| **A1** | **WCAG 2.2 SC 1.4.13 Content on Hover or Focus (Level AA)** — content that appears on hover or focus must be **dismissable** (without moving the pointer), **hoverable** (the pointer can move into it without it vanishing), and **persistent** (until dismissed, invalid, or no longer relevant) | Tooltip 6, Popover 5, Hover card 4, Dropdown/flyout 7, Mega menu 6 — **28 variants**; plus every Icon button, which is specified as always pairing with a tooltip | **Gate 29 (proposed, lock-time):** for every hover/focus overlay family, a Playwright assertion that Escape dismisses without pointer movement, that the pointer can traverse trigger → overlay without dismissal, and that no timed auto-dismiss fires while hovered. **Direct manipulation makes this worse, not better**: a user can drag a tooltip-bearing control against a viewport edge, and the resulting flip/reposition is exactly where dismissability and hoverability break — so the assertion runs against the *edited* layout, not a canonical one |
| **A2** | **WCAG 2.2.2 Pause, Stop, Hide (Level A)** — auto-moving, blinking or scrolling content lasting **more than 5 seconds** and presented in parallel with other content must have a mechanism to pause, stop or hide it | Background video loop 5 (a 4–16s loop is squarely inside the criterion), Animated counter's scroll-linked variant, auto-advancing Testimonial carousel, §9's Marquee/ticker 6 and Background ambient motion 8. **Discharged by the new Auto-motion pause/stop control (§8.3 #Utility)** | **Gate 30 (proposed, lock-time):** enumerate every element on the page registered with the `motion.auto-started` primitive and assert each has a reachable, visible, ≥24×24px, ≥3:1-contrast pause control. **`prefers-reduced-motion` does not discharge 2.2.2** — it is an OS preference, not a mechanism on the page — and the site-wide motion toggle only discharges it for users who find it |
| **A3** | **WCAG 2.2 SC 1.3.5 Identify Input Purpose (Level AA)** — inputs collecting information about the user must expose the purpose programmatically | Every field in Contact form 6, Inline email capture 6, Newsletter block 6, Checkout, Booking. Before this revision `autocomplete` appeared **once** in the whole section (`one-time-code` on the OTP row) | **Gate 32 (proposed, lock-time):** every `input`/`select`/`textarea` whose name matches the WCAG input-purpose list carries the correct `autocomplete` token, with a declared exception list (site search is the documented exception). Backed by the new `autocomplete` field-purpose mapping row |
| **A4** | **WCAG 1.1.1 Non-text Content (Level A)** — charts are non-text content by definition | The 12 chart marks + Sparkline 4 + Chart chrome kit 4, and any Step-6 custom chart. **The user named graphs and charts explicitly (vision step 6)** | **Gate 31 (proposed, lock-time):** every chart in the exported static site has an accessible name, a description or visually-hidden data table, and no colour-only distinction. **Must be emitted at build time**, because §17-O14 puts v1 charts on a build-time SVG path — a client-side alternative would not exist in the exported site at all |

Two further gates fall out of the states added above and the rule defined in §8.5.2:

| Id | What | Proposed gate |
|---|---|---|
| **A5** | The `prefers-contrast: more` third solve from §7.2 is rendered and contrast-swept, not merely generated | **Gate 33 (proposed, lock-time):** run the §13.4 gate-7 contrast sweep a second time against the elevated solve; fail on the same thresholds |
| **A6** | Variant differentiation (§8.5.2) | **Gate 34 (proposed — generation-time, NOT lock-time).** It runs when variants are emitted, not at LOCK, because a twin variant is a generation defect and LOCK is far too late to fix it. Advisory until O32 calibrates the thresholds |

**Not closed here.** WCAG 2.2 SC 2.5.7 Dragging Movements is already gated (§13.4 gate 9) and 1.4.12 Text Spacing at page level (gate 10); this section adds the component-level coverage state for 1.4.12 but does **not** add a second gate for it.

### 8.8 What this section asks of other sections

| Id | Ask | Of |
|---|---|---|
| **X1** | Add two `n/a` token items: **`interaction.pointer-capability-policy`** (hover/pointer media-query rules and the required touch equivalent for every hover-only affordance) and **`interaction.autocomplete-map`** (the WCAG 1.3.5 field-purpose token table). §8 now carries policy rows for both, but the token-side homes belong in §7.4 | §7 |
| **X2** | Add proposed gates **29–34** to the §13.4 ordered checklist (29 hover-overlay 1.4.13; 30 auto-motion 2.2.2 coverage; 31 chart non-text alternative; 32 `autocomplete` audit; 33 high-contrast solve sweep; 34 variant differentiation, generation-time). Numbering continues §13.4's existing 1–28 — **no existing gate is renumbered** | §13 |
| **X3** | Re-baseline phase sizing against **87 v1 items / 674 v1 variants**, or record the demotions that reduce it (see the sign-off note in §8.4) | §18 |
| **X4** | Record new risks **R46** (the axis schema is an unbudgeted one-time authoring cost that §8.5, §8.6 and the differentiation gate all depend on), **R47** (the §8.5.2 thresholds are uncalibrated, so the differentiation rule ships advisory-only at first and §17-R33's jam-study failure is only partly mitigated until O32 closes), and **R48** (four v1-priority components were missing from a hand-written summary for an entire PRD cycle without anyone noticing — the class of defect, not the instance, is what R48 records: any hand-maintained restatement of a machine-checkable table will drift again) | §17 |
| **X5** | Record new open questions **O31** (distinct selected variants per real page — needed before the lock-time capture total is knowable), **O32** (calibrate `T_ssim` / `T_colour`), and **O33** (who authors the variant axis schema) | §17.4 |

---
