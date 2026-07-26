## 5. Step 1 — the interview question bank

**Delivery rules.** Chunked into waves of 5–8 questions per screen with a visible, shrinking progress count. Visual tasks alternate with verbal ones. Advertised time: "about 20–30 minutes." Full bank is 78 questions; branching prunes to ~35–45 for the common single-language, single-surface, no-forms case. Every taste question has an explicit "I don't know / surprise me" path that routes to the skill proposing options from the reference-swipe results rather than the user inventing a preference. **[V — survey-fatigue literature: opiniion.com, sprinklr.com; agency questionnaire norms: wayfront.com 30-question template, bradfrost.com design-system interview]**

**Tier notation.** `[T1]` gates the Step-2 prompt and must be answered. `[T2]` asked just-in-time at the moment the answer is needed. `[T3]` inferred with a stated default and a visible "change this" affordance.

**Branch roots.** Four gates prune ~10–12 questions each for the common case: has-existing-logo, needs-more-than-one-language, collects-personal-data, design-system-scoped-to-this-site-only. Each visibly shrinks the remaining count on screen.

**Ordering principle.** Strategy before taste. Visual before verbal within taste. Constraints and admin last. This is both elite-studio process (brief → references → concept → art direction → build) and standard questionnaire funnel technique arriving at the same answer independently. **[V — prior swarm report Finding 6, Obys/Locomotive/Awwwards Academy sequencing]**

---

### Wave 0 — Continuity check (always first, before anything else)

| ID | Question | Tier | Notes |
|---|---|---|---|
| C1 | Have you used this skill before on this project, or is there an existing design system or prior site to build on? | T1 | Root gate. Three branches: fresh / reuse as-is / reuse-and-revise |
| C2 | If reusing — which parts stay locked and which are open for revision? | T1 | Only if C1 ≠ fresh. Tells Step 2 which tokens are frozen |
| C3 | Is there an existing library of artwork, sprites, photography, or illustration I should use? Where? | T1 | **The binary that decides whether the art category is real.** Answering "no" scopes art to code-drawn only |
| C4 | Is this site a sibling of an existing site of yours — should it share that site's identity? | T1 | Default no. "Yes" is the only path that reuses hue anchors and type pairings |

### Wave 1 — Strategy

**Purpose & Goals**

| ID | Question | Tier | Notes |
|---|---|---|---|
| P1 | What is this website for — what's the one thing you want a visitor to DO after they arrive? | T1 | Drives section grammar and CTA placement |
| P2 | What outcome does this serve — revenue, leads, hiring, portfolio, awareness, other? | T1 | 6 closed options; sets rubric weighting |
| P3 | Is this a brand-new venture, or an existing one getting a new site? | T1 | 2 options; gates brand-asset questions |
| P4 | Picture this site 12 months from now, succeeding beyond your hopes — what changed? | T2 | JTBD aspirational framing |
| P5 | Why build this now, rather than 6 months ago or 6 months from now? | T2 | JTBD push/pull; surfaces the real trigger |

**Positioning & Brand Strategy**

| ID | Question | Tier | Notes |
|---|---|---|---|
| B1 | Fill in the blank: For [target] who [need], [name] is the [category] that [benefit] — unlike [alternative], we [differentiator]. | T1 | Geoffrey Moore template **[V — Crossing the Chasm]**. Highest-leverage single question in the bank; seeds hero copy directly |
| B2 | Who are 2–3 direct competitors or alternatives, and what does each do better or worse? | T1 | Feeds the ≥3-reference concept gate |
| B3 | In one sentence, what makes you different from every alternative? | T2 | Portable line for hero + meta description |
| B4 | If your brand showed up as a person at a party, how would they act — which of these fits (or none)? | T3 | 12 Jungian archetypes **[V — Mark & Pearson 2001]**. Explicit skip path required; alienates utilitarian sites |
| B5 | How should this brand sound in writing — pick up to 3 words? | T2 | Seeds voice/tone tokens |

**Audience**

| ID | Question | Tier | Notes |
|---|---|---|---|
| A1 | Who is the primary visitor — role, context, how technical? | T1 | Core persona |
| A2 | Is there a second audience with meaningfully different needs? | T2 | Determines parallel sitemap tracks |
| A3 | What do visitors believe before they arrive, and what should they believe after? | T2 | Narrative arc |
| A4 | What's the single most likely objection that stops a visitor converting? | T2 | Feeds FAQ / trust-signal placement |
| A5 | What device and setting will most visitors be in — mobile-on-the-go / desktop-at-work / tablet-in-store / mix? | T1 | 4 options; sets responsive priority and performance budget |

### Wave 2 — Taste (visual first, verbal second — this ordering is load-bearing)

**Visual**

| ID | Question | Tier | Notes |
|---|---|---|---|
| T1 | Here are curated reference screenshots — sort each into love / neutral / hate. | T1 | 24 images spanning minimal, maximal, brutalist, editorial, corporate, playful, dark-cinematic, retro. **Pre-seeded by the wave-1 vertical answers**, not a generic set. **[V — NN/g mood-board + preference-testing research; arXiv 2511.20513 DesignPref]** |
| T2 | Of the ones you loved, pick your top 3 and say one sentence on what specifically you love. | T1 | Converts preference into design language; this is the reference-abstraction step |
| T3 | Of the ones you hated, pick your top 3 and say one sentence on what turns you off. | T1 | Negative references are more diagnostic than positive **[V — wayfront.com branding questionnaire; prior report Finding 4 deny-list mechanism]** |
| T4 | Move each slider: Minimal↔Maximal, Playful↔Serious, Quiet↔Loud, Classic↔Futuristic, Corporate↔Handmade, Light-first↔Dark-first, Warm↔Cool, Dense↔Airy. | T1 | 8 semantic-differential pairs. Research recommends 5–10 per battery |
| T5 | Is there a competitor or peer site whose visual territory you want to actively avoid, even if it's well-made? | T2 | Trade-dress proximity + negative constraint |

**Verbal (asked only after the visual tasks)**

| ID | Question | Tier | Notes |
|---|---|---|---|
| T6 | Should imagery lean photography / illustration / 3D render / abstract-generative / mix? | T1 | 5 options; routes asset generation |
| T7 | Icons from an existing set restyled to match, or fully custom-drawn? | T2 | 2 options |
| T8 | Custom cursor (dot, ring, magnetic, trail) or plain browser default? | T2 | 2 options; user-named item |
| T9 | Top navigation feel — always visible / hide-on-scroll / transparent-over-hero / minimal corner menu? | T1 | 4 options; user-named item ("top ribbon") |
| T10 | Should the background carry its own art/style, or stay a plain surface colour? | T1 | 5 options: plain / gradient / pattern / illustrated scene / generative particle. User-named item (FruitSync example) |

### Wave 3 — Design-system specifics

**Theming & Density**

| ID | Question | Tier | Notes |
|---|---|---|---|
| D1 | Light/dark toggle, dark-only, light-only, or follow system with no toggle? | T1 | 4 options. Determines whether every token needs a dual-mode value from day one |
| D2 | How dense should the UI feel — spacious/editorial or compact/information-dense? | T1 | 3 options; drives the spacing and type scale base multiplier |
| D3 | How many distinct page templates does this need (landing, article, gallery, pricing, dashboard…)? | T2 | Distinct from how many pages exist today |
| D4 | Will this system extend beyond this site — a future app, email, decks, social? | T2 | 4 options; changes whether tokens export portably |
| D5 | Full interaction-state coverage everywhere (hover/focus/active/disabled/loading/error), or lighter where non-critical? | T2 | 2 options; roughly doubles variant cost per interactive component |

**Component breadth**

| ID | Question | Tier | Notes |
|---|---|---|---|
| D6 | Which do you need — pricing table, testimonial carousel, FAQ accordion, stat counter, timeline, comparison table, embedded map, gallery/lightbox, newsletter signup, search, tag/filter, rating display? | T1 | 12-item checklist. **The single biggest gap between a website brief and a design-system brief.** Unchecked items are simply not built |
| D7 | Form types beyond a simple contact form — multi-step, file upload, payment, booking, survey? | T2 | Forms concentrate accessibility and validation work |

**Identity details**

| ID | Question | Tier | Notes |
|---|---|---|---|
| D8 | Serif, sans, or display/expressive for headlines — or should the system propose? | T1 | 4 options; user-named item ("a font") |
| D9 | How much personality should the front-of-site animation carry — signature entrance moment / subtle ambient / none? | T1 | 3 options; user-named item ("an animation for the front") |
| D10 | Primary buttons flat/minimal, with depth, or fully custom/illustrated? | T2 | 3 options; user-named item ("a button") |

**Motion appetite**

| ID | Question | Tier | Notes |
|---|---|---|---|
| M1 | On a scale from "nothing moves" to "everything moves," how much motion? | T1 | 5-point scale; sets the single motion-expressiveness dial |
| M2 | A specific site whose motion you want to emulate — or specifically avoid? | T2 | Motion is hard to describe, easy to point at |
| M3 | Should motion automatically reduce for visitors who've asked for less motion, with a visible toggle as fallback? | T1 | Default yes. Asking confirms informed consent and surfaces the rare force-motion case |

### Wave 4 — Constraints & admin

**Content reality**

| ID | Question | Tier | Notes |
|---|---|---|---|
| N1 | Do you have final copy, or does content need drafting? | T1 | 3 options |
| N2 | Do you have final photography/video, or does imagery need generating or sourcing? | T1 | 3 options; interacts hard with C3 |
| N3 | Roughly how many pages or sections? | T1 | 4 tiers: single / 2–5 / 6–15 / 15+ |
| N4 | Which pages are must-have for launch, which can wait? | T1 | v1 sitemap vs backlog |
| N5 | Existing material to mine — old site, deck, one-pager? | T2 | Enables auto-mining |
| N6 | Will content change often after launch, or is it mostly static? | T1 | Determines whether the editor needs an ongoing content model |

**Brand assets already owned**

| ID | Question | Tier | Notes |
|---|---|---|---|
| N7 | Do you have a logo? Is it final, or open to refinement? | T1 | 3 branches |
| N8 | Do you have brand colours? Hex values? | T1 | Hard constraint on the colour solver |
| N9 | Do you have a brand typeface? Do you hold a web-embedding licence? | T1 | Gates the three-tier font policy |
| N10 | Existing marketing materials the site must stay consistent with? | T2 | |
| N11 | Do you have a style guide or brand book, even informal? | T1 | Short-circuits much of waves 1–2 |

**Accessibility**

| ID | Question | Tier | Notes |
|---|---|---|---|
| X1 | Legal/organisational accessibility requirement (ADA, Section 508, EN 301 549), or best-effort? | T1 | 3 options; sets gate strictness |
| X2 | Target WCAG 2.2 AA (default), or further? | T1 | Default AA. Auto-answered "AA" if declined — never silently omitted |
| X3 | For dark/cinematic palettes, also check against APCA in addition to WCAG 2? | T2 | Only surfaced when wave-2 answers point dark |

**Performance & device**

| ID | Question | Tier | Notes |
|---|---|---|---|
| X4 | Lowest-end device/network you expect — flagship+wifi / mid-range+data / budget+slow? | T1 | 3 options; sets the performance budget and GPU-tier ladder |
| X5 | Any hard performance ceiling (kiosk on venue wifi, expensive-data market)? | T2 | Can override visual ambition outright |
| X6 | Should heavy visuals (3D, video, particles) degrade on low-end devices, or must the experience be uniform? | T2 | 2 options; determines whether the tier ladder is built |

**Localisation**

| ID | Question | Tier | Notes |
|---|---|---|---|
| L1 | More than one language at launch? Which? | T1 | Root; "no" skips the rest of this section |
| L2 | Do any read right-to-left (Arabic, Hebrew)? | T1 | **Structural, must be known before the grid is built.** This project's own FruitSync Arabic RTL rework is direct first-party evidence of the retrofit cost **[V — repo commits 7dd7544, 060a9af; fruitsync-localization memory]** |
| L3 | Localise currency/date/number formats per region? | T2 | |
| L4 | Who provides translations — professional / MT you'll review / placeholder flagged for review? | T2 | Prevents machine translation shipping as final |

**Legal**

| ID | Question | Tier | Notes |
|---|---|---|---|
| G1 | Does this site collect personal data — forms, cookies, analytics, newsletter? | T1 | Root of the legal-pages branch |
| G2 | Need privacy policy, terms, cookie banner at launch? | T1 | 3 options: draft-for-me / I'll-supply / not-needed |
| G3 | Age-gate, region-block, or industry-specific requirement (alcohol, gambling, finance, healthcare)? | T2 | |

**Hosting & maintenance**

| ID | Question | Tier | Notes |
|---|---|---|---|
| H1 | Where should the finished site be hosted? | T1 | Default recommendation: Cloudflare Pages, static, free bandwidth |
| H2 | Do you own a domain? Which? | T1 | |
| H3 | Do you want the site's own git history, or is the ACOS session history enough? | T1 | Default: its own nested repo |
| H4 | Who maintains it after launch — you in the editor / a developer / nobody? | T1 | 3 options; calibrates editor investment |
| H5 | How often will you come back into the design surface — often / occasionally / rarely? | T2 | |
| H6 | How much of the page do you expect to hand-edit in code afterwards? | T2 | Calibrates how much wrapper scaffolding to generate |

**Custom & unusual**

| ID | Question | Tier | Notes |
|---|---|---|---|
| U1 | Anything beyond standard marketing components — live chart, calculator, embedded game, data table, interactive map, booking widget? | T1 | Scopes Step 6 early |
| U2 | Is there a signature interaction you already have in mind? | T2 | Award-tier sites have exactly one; asking directly can save inventing one |

**Time & decision process**

| ID | Question | Tier | Notes |
|---|---|---|---|
| Z1 | How much of your time can you give — one sitting / a few short sessions / open-ended? | T1 | Sets how aggressively to branch and how many variant rounds to offer |
| Z2 | Do you want a small number of strong options, or many to compare? | T1 | Directly sets the D1 variant multiplier |
| Z3 | Does anyone else need to approve before you say LOCK? | T2 | Determines whether a shareable review step is needed |
| Z4 | Do you have any image-generation connector active in your claude.ai session? | T2 | Changes what Stage B can reasonably request. Default assume no |

### Wave 5 — Negative constraints & success criteria

| ID | Question | Tier | Notes |
|---|---|---|---|
| V1 | Is there a colour, symbol, font, or visual cliché that must never appear? | T1 | Per-project deny-list layered on the standing anti-slop list |
| V2 | Is there a past design — yours or a competitor's — you're actively moving away from? | T1 | Concrete "not this" anchor for the concept gate |
| V3 | Are there tone, imagery, or humour lines this brand must never cross? | T2 | Brand-safety, distinct from visual constraints |
| V4 | When you look at the finished site, what will tell you it was worth doing this way instead of picking a template? | T1 | The qualitative acceptance bar the human applies at LOCK |
| V5 | What would make you say LOCK today, versus asking for one more round of variants? | T1 | Operationalises the Step-5-vs-Step-7 branch |

**Total: 78 questions. Common-case answered: ~35–45.**

### 5.1 Fallback flows

- **User can't name any reference site they like** — a documented real failure mode. Auto-suggest a curated reference set by detected vertical, and if that fails, run a broader first-pass style-family sort (8 families) before individual-site references. **[V — practitioner reports; the fallback design is inference]**
- **User declines the accessibility questions** — auto-answer "AA, no known legal requirement." Never silently omit the gate.
- **User gives vague strategy answers** ("I want it to look nice") — the concept gate will produce a generic document and all 10 directions inherit that blandness. Mitigation: the interview pushes with concrete follow-ups ("what would you *not* want it to look like?") and refuses to advance to Step 2 until the concept document names at least one thing the site refuses to do.

---

