## 5. Step 1 — the interview question bank

**Delivery rules.** Chunked into waves of 5–8 questions per screen with a visible, shrinking progress count. Visual tasks alternate with verbal ones.

*Advertised time — revised and reconciled.* The bank is **90 questions** (see the row-count self-audit at the end of this section), not the "78" claimed in earlier drafts — that figure was a miscount that stopped at the end of Wave 4 and never added Wave 5's five questions; the correct original count was 83, and this revision adds 7 more to close gaps recorded below, for 90 total. In **fast mode** (`Z1 = "one sitting"`, see the retiered Wave 0 below), only Tier-1 questions are asked and Tier-3 items are bundled into one end-of-interview review screen; for the common single-language, single-surface, no-forms case this comes to **approximately 45–55 Tier-1 questions asked** plus one bundled 6-item review screen — **not the "~35–45" figure asserted in earlier drafts**, which had no dependency map behind it and could not be checked. At an estimated 25–30 seconds per standard closed-form question plus explicit budgets for the five heavy tasks in the bank (swipe-sort ≈4 min, two written taste sentences ≈1.5 min each, 8-item slider battery ≈2 min, the five-blank positioning statement ≈2 min), the honest estimate is **about 25–35 minutes in fast mode**, rising to **roughly 45–70 minutes in open-ended mode** (`Z1 = "open-ended"`) where every Tier-2 question is also asked. `[Inference — per-question timing budgets are estimated from the closed-vs-open-response shape of each question, not measured]`.
This is **narrower and more honest than, but not yet reconciled with,** two other sections that cite the old numbers: §17-R21 ("the bank is 78 questions; at 30–60s each that is 40–80 minutes") and §18's v1 scope-in line ("Full interview (78 bank …)"). **Flagged — requires cross-section reconciliation, not fixed unilaterally here:** whoever owns §17 and §18 should update both to the 90-question / 45–55-Tier-1-fast-mode / 25–35-minute figures derived here, and §19's acceptance criterion A19-A3 ("interview completes with ≤45 answered questions for a single-language, single-surface, no-forms marketing site") should be revised to **≤55**, which is the number this section can actually deliver — or the bank must be cut further to hit ≤45. This section does not have authority to edit §19's acceptance criteria and does not do so; it records the honest number and defers the reconciliation. **No known mitigation beyond instrumentation:** actual elapsed time must be measured from day one (see AC-5.4 below) because every estimate above is a projection, not a measurement.

**Tier notation — three states, disambiguated.** `[T1]` gates the Step-2 prompt. A Tier-1 question is satisfied by **exactly one of two resolutions**, and Step 1 does not exit until every Tier-1 question is in one of them:
  1. **Answered** — the user supplied a real value.
  2. **Explicitly defaulted** — the user took the visible "I don't know / surprise me" affordance (see Delivery rules note below and 5.1), and the skill recorded a **stated, concrete default value** (not a null) into `00-interview/answers.json` with `"source": "skill-default"`. This is what resolves the earlier contradiction between "Tier-1 must be answered" and "every taste question has a skip path" — Tier-1 is mandatory in the sense that the *question is always resolved*, not that the *user is forced to type an opinion*.

`[T2]` asked just-in-time at the moment the answer is needed; if that moment never arrives in the current build (e.g. because a dependent feature was declined), the question is not asked and is recorded as `"not-applicable"`, not defaulted.

`[T3]` inferred with a stated default and a visible "change this" affordance, presented pre-filled rather than asked open-ended, and in fast mode bundled with all other Tier-3 items into a single end-of-interview review screen. **Every row in the bank below now carries an explicit Default column**, closing the earlier gap where only 6 of 83 rows had a stated default despite Tier-3 being defined as "always has one." Six questions that already carried a stated fallback value in earlier drafts but were mistagged `[T1]` are retagged `[T3]` here for consistency with their own behavior: **C4, X2, M3, H1, H3, Z4**. Tier-3 is now used on 7 questions (was 1); the remaining admin rows either have no safe default (flagged "no default — hard block" below) or are genuinely Tier-2 with a not-applicable fallback.

**ID grammar (new rule, closes a blocking ambiguity).** Every question ID is `<wave-prefix><n>`; prefixes are reserved per wave-section (`C`, `P`, `B`, `A`, `TS`, `D`, `M`, `N`, `X`, `L`, `G`, `H`, `U`, `Z`, `V`) and never collide with the tier labels `T1`/`T2`/`T3`. **Rename notice:** the ten Wave-2 taste questions were previously numbered `T1`–`T10`, which is indistinguishable in prose from tier label `[T1]`/`[T2]`/`[T3]` — a directive citing "T3" was ambiguous between "the negative-reference question" and "an inferred-with-default question," and this collided directly with A4's requirement that every Step-2 directive cite the interview question ID that produced it. They are renumbered **`TS1`–`TS10`** here. **Flagged — compatibility risk this section cannot resolve alone:** any other PRD section, prompt template, or `answers.json` from a prior project (relevant to Step 0 warm-start reuse) that cites bare `T1`–`T10` meaning a taste question must be updated to `TS1`–`TS10`; a cross-section grep pass is required and is out of this section's scope.

**Branch roots — corrected.** Earlier drafts claimed four gates "prune ~10–12 questions each," which was asserted, not computed, and is arithmetically impossible against an 83–90-question bank (four roots at 10–12 each would prune 40–48 questions, but at most ~20 questions in the whole bank are plausibly downstream of any of the four). The real, question-level dependency map is now given per row below (see the **Ask-if** column in every table); the corrected per-root totals are:

| Branch root | Root question | Real questions pruned | Note |
|---|---|---|---|
| Has an existing locked brand identity | **C6** (new — moved to Wave 0; see below) | 1–2 (`B4`, conditionally `D8`) | The root signal previously lived on `N7` in Wave 4, *after* the taste questions (`B4`, `D8`) it was supposed to gate — a genuine sequencing bug, fixed by adding `C6` as a cheap Wave-0 root; `N7`–`N12` remain in Wave 4 to capture the factual specifics (hex values, licences) regardless of `C6`, since those are hard data needed either way, not style-invention questions |
| More than one language at launch | `L1` | 3 (`L2`, `L3`, `L4`) | The one root that actually matches its original billing at this bank's size |
| Collects personal data | `G1` | 1 (`G2`), conditionally, jointly gated with the new `G0` jurisdiction question | `G3` (age-gate/industry) is **not** prunable by `G1` alone — an alcohol or gambling site needs an age-gate regardless of whether it collects personal data |
| Design-system scoped to this site only | `D4` | **0** | **Correction, not a fix-in-place:** this was listed as a question-pruning root in earlier drafts but has no downstream question dependents anywhere in the bank — `D4`'s four answers change *what Step 2/3 export as portable tokens*, a downstream deliverable-scope effect, not further interview questions. It should never have been framed as a branch root that prunes questions. If a future section needs `D4` to gate additional interview questions, those questions must be added there; none are invented here to make the old framing true. |

No-forms cases add one more real prune not previously named as a "root": `D7` (form types) is skipped when no form-bearing component is in scope, which also skips the newly added `D11` (form destination) — see Wave 3 below.

**Ordering principle.** Strategy before taste. Visual before taste within taste. Constraints and admin last — **with one deliberate exception**: `Z1` and `Z2` (time budget and variant-count preference) are promoted into Wave 0 in this revision (see below) because they are global branching policy inputs consumed by every later wave, and a policy input asked *after* the questions it is meant to prune has no effect on them. This is both elite-studio process (brief → references → concept → art direction → build) and standard questionnaire funnel technique arriving at the same answer independently. **[V — prior swarm report Finding 6, Obys/Locomotive/Awwwards Academy sequencing]**

---

### Wave 0 — Continuity & global policy (always first, before anything else)

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| C1 | Have you used this skill before on this project, or is there an existing design system or prior site to build on? | T1 | always | no default — root gate, no safe assumption | Root gate. Three branches: fresh / reuse as-is / reuse-and-revise |
| C2 | If reusing — which parts stay locked and which are open for revision? | T1 | `C1 ≠ fresh` | if explicitly defaulted while asked: "all open for revision" (the conservative, maximally flexible choice) | Only if C1 ≠ fresh. Tells Step 2 which tokens are frozen |
| C3 | Is there an existing library of artwork, sprites, photography, or illustration I should use? Where? | T1 | always | "no — code-drawn art only" | **The binary that decides whether the art category is real.** Answering "no" scopes art to code-drawn only. Feeds `N12` (asset licence capture) when answered "yes" |
| C4 | Is this site a sibling of an existing site of yours — should it share that site's identity? | **T3** *(retagged from T1)* | always, bundled into end-of-interview review in fast mode | "no" | Default no. "Yes" is the only path that reuses hue anchors and type pairings |
| C5 | **NEW.** What is the primary language visitors will read this site in? | T1 | always | `[Inference]` the language the interview itself was conducted in | Closes a gap where `L1` only asks about *additional* languages and a single-language project never recorded which language it was in — needed for `<html lang>` (§13.6) on every single-language site, i.e. the common case the whole branching model is tuned for |
| C6 | **NEW.** Do you already have a locked visual identity — logo, and/or fixed brand colours/type — that this site must visually match? | T1 | always | "no" — asking `B4`/`D8` when unsure is safer than wrongly skipping them and defaulting to a generic invented identity | This is the real root for the "has-existing-logo" branch (see Branch roots table above); relocated here from its former implicit home on `N7` in Wave 4 specifically so it can gate `B4` and `D8`, which are asked *before* Wave 4 in question order |
| Z1 | **MOVED from Wave 4.** How much of your time can you give — one sitting / a few short sessions / open-ended? | T1 | always | if explicitly defaulted: "a few short sessions" `[Inference — conservative middle default]` | Sets how aggressively to branch and how many variant rounds to offer. **Concrete effect, previously unstated:** `one sitting` → only Tier-1 questions asked, all Tier-2 auto-deferred/defaulted, Tier-3 bundled into one review screen, variant rounds capped at 1. `a few short sessions` → Tier-1 + Tier-2 asked (can span sessions), Tier-3 shown individually, up to 2 variant rounds by default. `open-ended` → full bank, unlimited variant rounds bounded only by `Z2` and the Step 5/§6/§17 iteration budget |
| Z2 | **MOVED from Wave 4.** Do you want a small number of strong options, or many to compare? | T1 | always | if explicitly defaulted: "many to compare" | Directly sets the D1-settled variant multiplier (§ Settled Decisions D1: 10 variants per swappable component is the standing default). **Concrete effect, previously unstated:** "many to compare" → the full 10-variant-per-component default from D1 applies. "A small number of strong options" → 3 variants per swappable component per round, still computed from the direction's derived values per D1, never hand-picked independently |

*Row-count for this wave: 8 (`C1`–`C6`, `Z1`, `Z2`).*

### Wave 1 — Strategy

**Purpose & Goals**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| P1 | What is this website for — what's the one thing you want a visitor to DO after they arrive? | T1 | always | no default — hard block, this is the single most load-bearing answer in the bank | Drives section grammar and CTA placement |
| P2 | What outcome does this serve — revenue, leads, hiring, portfolio, awareness, other? | T1 | always | no default — hard block | 6 closed options; sets rubric weighting |
| P3 | Is this a brand-new venture, or an existing one getting a new site? | T1 | always | no default — hard block, gates brand-asset questions downstream | 2 options; gates brand-asset questions |
| P4 | Picture this site 12 months from now, succeeding beyond your hopes — what changed? | T2 | `Z1 ≠ "one sitting"` | not-applicable when skipped | JTBD aspirational framing |
| P5 | Why build this now, rather than 6 months ago or 6 months from now? | T2 | `Z1 ≠ "one sitting"` | not-applicable when skipped | JTBD push/pull; surfaces the real trigger |
| P6 | **NEW.** Which of these best describes the site — brochure/marketing site, product/app landing, e-commerce, portfolio, blog/publication, game or app promo, event, nonprofit/cause, documentation/knowledge base, other? | T1 | always | `[Inference]` inferred from `P2`, mapped 1:1 to the schema.org types §13.6 requires (Organization/WebSite for marketing, VideoGame for game promo, WebApplication for app shell, etc.) — always shown for confirmation, never silently applied | Closes a gap where §13.6 required JSON-LD "matched to the site-type answer" and its acceptance criterion A70 had no question to read from; `P2` (business outcome) does not map onto schema.org types and this is a distinct question |

**Positioning & Brand Strategy**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| B1 | Fill in the blank: For [target] who [need], [name] is the [category] that [benefit] — unlike [alternative], we [differentiator]. | T1 | always | no default — hard block, no safe substitute for this answer exists | Geoffrey Moore template **[V — Crossing the Chasm]**. Highest-leverage single question in the bank; seeds hero copy directly |
| B2 | Who are 2–3 direct competitors or alternatives, and what does each do better or worse? | T1 | always | no default — hard block, feeds the ≥3-reference concept gate | Feeds the ≥3-reference concept gate |
| B3 | In one sentence, what makes you different from every alternative? | T2 | always (cheap, low-friction) | if explicitly deferred: derived from `B1`'s differentiator clause | Portable line for hero + meta description |
| B4 | If your brand showed up as a person at a party, how would they act — which of these fits (or none)? | T1 *(previously T3; retagged because it now has a real ask-if, not just a default)* | `C6 == "no"` | when skipped (`C6 == "yes"`): `[Inference]` archetype inferred from the supplied logo's visual language (shape language, colour temperature, line weight), shown with a change-this affordance | 12 Jungian archetypes **[V — Mark & Pearson 2001]**. Explicit skip path required; alienates utilitarian sites |
| B5 | How should this brand sound in writing — pick up to 3 words? | T2 | always | if explicitly deferred: derived from `B1` + `T2`/`TS2` written taste sentences | Seeds voice/tone tokens |

**Audience**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| A1 | Who is the primary visitor — role, context, how technical? | T1 | always | no default — hard block | Core persona |
| A2 | Is there a second audience with meaningfully different needs? | T2 | always | "no" if skipped | Determines parallel sitemap tracks |
| A3 | What do visitors believe before they arrive, and what should they believe after? | T2 | always | not-applicable if skipped, narrative arc left to Step 2 inference from `P1`/`B1` | Narrative arc |
| A4 | What's the single most likely objection that stops a visitor converting? | T2 | always | not-applicable if skipped | Feeds FAQ / trust-signal placement |
| A5 | What device and setting will most visitors be in — mobile-on-the-go / desktop-at-work / tablet-in-store / mix? | T1 | always | no default — hard block, sets responsive priority and the performance budget | 4 options; sets responsive priority and performance budget |

*Row-count for this wave: 16 (Purpose 6, Positioning 5, Audience 5).*

### Wave 2 — Taste (visual first, verbal second — this ordering is load-bearing)

*Renamed from `T1`–`T10` to `TS1`–`TS10` this revision — see the ID Grammar rule above.*

**Visual**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| TS1 | Here are curated reference screenshots — sort each into love / neutral / hate. | T1 | always | no default — hard block; if the user cannot engage with this task at all, fall back to the style-family sort described in 5.1 | 24 images spanning minimal, maximal, brutalist, editorial, corporate, playful, dark-cinematic, retro. **Pre-seeded by the wave-1 vertical answers (`P2`, `P6`)**, not a generic set. **[V — NN/g mood-board + preference-testing research; arXiv 2511.20513 DesignPref]** |
| TS2 | Of the ones you loved, pick your top 3 and say one sentence on what specifically you love. | T1 | always | if the "I don't know / surprise me" affordance is used: skill proposes 2–3 candidate descriptions drawn from the loved images' shared attributes and asks the user to pick or edit one, rather than inventing an unattributed preference | Converts preference into design language; this is the reference-abstraction step |
| TS3 | Of the ones you hated, pick your top 3 and say one sentence on what turns you off. | T1 | always | same surprise-me mechanism as `TS2`, applied to the hated set | Negative references are more diagnostic than positive **[V — wayfront.com branding questionnaire; prior report Finding 4 deny-list mechanism]** |
| TS4 | Move each slider: Minimal↔Maximal, Playful↔Serious, Quiet↔Loud, Classic↔Futuristic, Corporate↔Handmade, Light-first↔Dark-first, Warm↔Cool, Dense↔Airy. | T1 | always | if explicitly deferred per-slider: midpoint, with a note that midpoint defaults reduce directional signal and should be revisited before Step 2 fires | 8 semantic-differential pairs. Research recommends 5–10 per battery |
| TS5 | Is there a competitor or peer site whose visual territory you want to actively avoid, even if it's well-made? | T2 | always | "none named" if skipped | Trade-dress proximity + negative constraint |

**Verbal (asked only after the visual tasks)**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| TS6 | Should imagery lean photography / illustration / 3D render / abstract-generative / mix? | T1 | always | no default — hard block, routes asset generation | 5 options; routes asset generation |
| TS7 | Icons from an existing set restyled to match, or fully custom-drawn? | T2 | always | "existing set, restyled" if skipped (cheaper default) | 2 options |
| TS8 | Custom cursor (dot, ring, magnetic, trail) or plain browser default? | T2 | always | "plain browser default" if skipped | 2 options; user-named item |
| TS9 | Top navigation feel — always visible / hide-on-scroll / transparent-over-hero / minimal corner menu? | T1 | always | no default — hard block, user-named item ("top ribbon") | 4 options; user-named item ("top ribbon") |
| TS10 | Should the background carry its own art/style, or stay a plain surface colour? | T1 | always | no default — hard block, user-named item (FruitSync example) | 5 options: plain / gradient / pattern / illustrated scene / generative particle. User-named item (FruitSync example) |

*Row-count for this wave: 10.*

### Wave 3 — Design-system specifics

**Theming & Density**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| D1 | Light/dark toggle, dark-only, light-only, or follow system with no toggle? | T1 | always | no default — hard block, determines whether every token needs a dual-mode value from day one | 4 options. Determines whether every token needs a dual-mode value from day one |
| D2 | How dense should the UI feel — spacious/editorial or compact/information-dense? | T1 | always | no default — hard block, drives the spacing and type scale base multiplier | 3 options; drives the spacing and type scale base multiplier |
| D3 | How many distinct page templates does this need (landing, article, gallery, pricing, dashboard…)? | T2 | always | `[Inference]` inferred from `P6` site type + `N3` page count | Distinct from how many pages exist today |
| D4 | Will this system extend beyond this site — a future app, email, decks, social? | T2 | always | "no — this site only" | 4 options; changes whether tokens export portably. **See Branch-roots correction above: this question has zero downstream question dependents in this bank; its effect is scoped entirely to Step 2/3 export-format deliverables, not further interview questions** |
| D5 | Full interaction-state coverage everywhere (hover/focus/active/disabled/loading/error), or lighter where non-critical? | T2 | always | "lighter where non-critical" if skipped | 2 options; roughly doubles variant cost per interactive component |

**Component breadth**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| D6 | Which do you need — pricing table, testimonial carousel, FAQ accordion, stat counter, timeline, comparison table, embedded map, gallery/lightbox, newsletter signup, search, tag/filter, rating display? | T1 | always | no default — hard block, unchecked items are simply not built | 12-item checklist. **The single biggest gap between a website brief and a design-system brief.** Unchecked items are simply not built |
| D7 | Form types beyond a simple contact form — multi-step, file upload, payment, booking, survey? | T2 | any form-bearing component selected in `D6`, or `P1`/`U1` implies a form CTA | "simple contact form only, no advanced type" if skipped — this is one of the concrete prunes for the "no-forms" common case named in A19-A3 | Forms concentrate accessibility and validation work |
| D11 | **NEW.** Where should form submissions go — a third-party form endpoint, a mailto fallback, or none? | T1 | same trigger as `D7` (any form in scope) | **no safe silent default** — if a form is in scope and this is explicitly deferred, the only zero-configuration fallback is a `mailto:` to the account holder's contact address, and it is surfaced as a **blocking pre-publish check**, not silently applied | Closes a gap where §2-NG3 names third-party-endpoint-or-mailto as the only two supported destinations, `D7` asked which form *types* were needed but nothing asked *where submissions go*, so a contact form was buildable and unshippable |

**Identity details**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| D8 | Serif, sans, or display/expressive for headlines — or should the system propose? | T1 | `C6 == "no"` | when skipped (`C6 == "yes"`): "use the brand's existing typeface family," confirmed later against the licence captured at `N9` | 4 options; user-named item ("a font") |
| D9 | How much personality should the front-of-site animation carry — signature entrance moment / subtle ambient / none? | T1 | always | no default — hard block, user-named item ("an animation for the front") | 3 options; user-named item ("an animation for the front"). Per Settled Decision D4, this and its variants live in the same draggable art-style containers as static artwork, not a parallel motion subsystem |
| D10 | Primary buttons flat/minimal, with depth, or fully custom/illustrated? | T2 | always | "flat/minimal" if skipped | 3 options; user-named item ("a button") |

**Motion appetite**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| M1 | On a scale from "nothing moves" to "everything moves," how much motion? | T1 | always | no default — hard block, sets the single motion-expressiveness dial | 5-point scale; sets the single motion-expressiveness dial |
| M2 | A specific site whose motion you want to emulate — or specifically avoid? | T2 | always | "none named" if skipped | Motion is hard to describe, easy to point at |
| M3 | Should motion automatically reduce for visitors who've asked for less motion, with a visible toggle as fallback? | **T3** *(retagged from T1)* | always, bundled into end-of-interview review in fast mode | "yes" | Default yes. Asking confirms informed consent and surfaces the rare force-motion case |

*Row-count for this wave: 14 (Theming 5, Component 3, Identity 3, Motion 3).*

### Wave 4 — Constraints & admin

**Content reality**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| N1 | Do you have final copy, or does content need drafting? | T1 | always | no default — hard block | 3 options |
| N2 | Do you have final photography/video, or does imagery need generating or sourcing? | T1 | always | no default — hard block, interacts hard with C3 | 3 options; interacts hard with C3. Feeds `N12` licence capture when "yes" |
| N3 | Roughly how many pages or sections? | T1 | always | no default — hard block | 4 tiers: single / 2–5 / 6–15 / 15+ |
| N4 | Which pages are must-have for launch, which can wait? | T1 | always | no default — hard block, v1 sitemap vs backlog | v1 sitemap vs backlog |
| N5 | Existing material to mine — old site, deck, one-pager? | T2 | always | "none" if skipped | Enables auto-mining |
| N6 | Will content change often after launch, or is it mostly static? | T1 | always | no default — hard block, determines whether the editor needs an ongoing content model | Determines whether the editor needs an ongoing content model |

**Brand assets already owned**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| N7 | Do you have a logo? Is it final, or open to refinement? | T1 | always (factual detail follow-up to `C6`, asked regardless of `C6`'s value) | no default — hard block | 3 branches |
| N8 | Do you have brand colours? Hex values? | T1 | always | no default — hard block, hard constraint on the colour solver | Hard constraint on the colour solver |
| N9 | Do you have a brand typeface? Do you hold a web-embedding licence? | T1 | always | no default — hard block, gates the three-tier font policy | Gates the three-tier font policy |
| N10 | Existing marketing materials the site must stay consistent with? | T2 | always | "none" if skipped | |
| N11 | Do you have a style guide or brand book, even informal? | T1 | always | no default — hard block; short-circuits much of waves 1–2 when "yes" | Short-circuits much of waves 1–2 |
| N12 | **NEW.** For every visual asset you supply (photos, illustrations, sprites, existing marketing art) — who made it, under what licence, and is public-site redistribution permitted? Options per source: own work / commissioned with rights transferred / licensed stock (name the licence + seat count) / unknown. | T1 | `C3` answered "yes" (a library exists) OR `N2` indicates existing final photography/video OR `N10` names existing materials | **"unknown" is an explicit, blocking answer** — it is recorded into `assets/manifest.json` and surfaced as a blocking condition at intake, not discovered later at LOCK | Closes a gap where the only asset class with a licence question was the brand typeface (`N9`); Step 8's evidence bundle (per the user's vision) and gate 26 (§13) require licence completeness for *every* asset, and raster/photo/illustration assets — the more common case — had no supply path for that data at all |

**Accessibility**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| X1 | Legal/organisational accessibility requirement (ADA, Section 508, EN 301 549), or best-effort? | T1 | always | `[Inference]` **pre-answered from `G0`'s jurisdiction derivation where possible** (e.g. an EU-serving business is flagged toward the European Accessibility Act) rather than asking the user to self-assess legal exposure blind; still shown for confirmation | 3 options; sets gate strictness. Closes a gap where the user was expected to already know which accessibility regime applies to them |
| X2 | Target WCAG 2.2 AA (default), or further? | **T3** *(retagged from T1)* | always, bundled into end-of-interview review in fast mode | "AA" | Default AA. Auto-answered "AA" if declined — never silently omitted |
| X3 | For dark/cinematic palettes, also check against APCA in addition to WCAG 2? | T2 | wave-2 (`TS4`/`TS10`) answers point dark | "no" if not triggered | Only surfaced when wave-2 answers point dark |

**Performance & device**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| X4 | Lowest-end device/network you expect — flagship+wifi / mid-range+data / budget+slow? | T1 | always | no default — hard block, sets the performance budget and GPU-tier ladder | 3 options; sets the performance budget and GPU-tier ladder |
| X5 | Any hard performance ceiling (kiosk on venue wifi, expensive-data market)? | T2 | always | "none" if skipped | Can override visual ambition outright |
| X6 | Should heavy visuals (3D, video, particles) degrade on low-end devices, or must the experience be uniform? | T2 | always | "degrade gracefully" if skipped | 2 options; determines whether the tier ladder is built |

**Localisation**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| L1 | More than one language at launch? Which? | T1 | always | "no" | Root; "no" skips the rest of this section (`L2`–`L4`) |
| L2 | Do any read right-to-left (Arabic, Hebrew)? | T1 | `L1 ≠ "no"` | no default when asked — hard block, structural | **Structural, must be known before the grid is built.** This project's own FruitSync Arabic RTL rework is direct first-party evidence of the retrofit cost **[V — repo commits 7dd7544, 060a9af; fruitsync-localization memory]** |
| L3 | Localise currency/date/number formats per region? | T2 | `L1 ≠ "no"` | "no localisation, single format" if skipped | |
| L4 | Who provides translations — professional / MT you'll review / placeholder flagged for review? | T2 | `L1 ≠ "no"` | "MT you'll review, flagged" if skipped — prevents machine translation shipping as final silently | Prevents machine translation shipping as final |

**Legal**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| G0 | **NEW.** Where is the business established, and which regions will visitors come from? | T1 | always, root of the legal branch, asked before `G1` | no default — hard block, no safe assumption of jurisdiction | Closes a gap where `G1`–`G3` asked about data collection, legal pages, and age-gates/regulated industries without ever asking *which regime* governs them — the interview otherwise drafts a privacy policy, terms, and cookie banner that satisfy no regulator, or silently assumes one jurisdiction. **This question records region only; mapping specific regions to specific regimes (GDPR/ePrivacy, UK GDPR, CCPA/CPRA, the EU Accessibility Act, or none) is a legal-accuracy question this PRD cannot answer with certainty — flagged as "requires user/legal sign-off," no known mitigation beyond routing the recorded answer to whatever document-drafting step handles `G2`, which must itself carry the same disclaimer that generated legal text is not a substitute for counsel** |
| G1 | Does this site collect personal data — forms, cookies, analytics, newsletter? | T1 | always | no default — hard block, root of the legal-pages branch | Root of the legal-pages branch |
| G2 | Need privacy policy, terms, cookie banner at launch? | T1 | `G1 == "yes"` OR `G0`'s derived regime mandates disclosures regardless of data collection | "not needed" only when both `G1 == "no"` AND `G0`'s region has no mandatory-disclosure regime; otherwise no default — hard block | 3 options: draft-for-me / I'll-supply / not-needed. Also drives whether a consent banner is a blocking (ePrivacy-style, must block non-essential cookies before load) vs advisory (CCPA-style opt-out) vs absent element — **derived from `G0`, not a free style choice** |
| G3 | Age-gate, region-block, or industry-specific requirement (alcohol, gambling, finance, healthcare)? | T2 | always — **not** prunable by `G1` alone, since an age-gated industry site may need this with zero personal-data collection | "none" if skipped | |

**Hosting & maintenance**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| H1 | Where should the finished site be hosted? | **T3** *(retagged from T1)* | always, bundled into end-of-interview review in fast mode | Cloudflare Pages, static, free bandwidth | Default recommendation: Cloudflare Pages, static, free bandwidth |
| H2 | Do you own a domain? Which? | T1 | always | no default — hard block | |
| H3 | Do you want the site's own git history, or is the ACOS session history enough? | **T3** *(retagged from T1)* | always, bundled into end-of-interview review in fast mode | its own nested repo | Default: its own nested repo |
| H4 | Who maintains it after launch — you in the editor / a developer / nobody? | T1 | always | no default — hard block, calibrates editor investment | 3 options; calibrates editor investment |
| H5 | How often will you come back into the design surface — often / occasionally / rarely? | T2 | always | "occasionally" if skipped | |
| H6 | How much of the page do you expect to hand-edit in code afterwards? | T2 | always | "little to none" if skipped | Calibrates how much wrapper scaffolding to generate |

**Custom & unusual**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| U1 | Anything beyond standard marketing components — live chart, calculator, embedded game, data table, interactive map, booking widget? | T1 | always | "none" if skipped | Scopes Step 6 early |
| U2 | Is there a signature interaction you already have in mind? | T2 | always | "none named — skill may propose one" if skipped | Award-tier sites have exactly one; asking directly can save inventing one |

**Decision process & tooling** *(renamed from "Time & decision process" — `Z1`/`Z2`, the time-budget items, moved to Wave 0; see Ordering principle above)*

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| Z3 | Does anyone else need to approve before you say LOCK? | T2 | always | "no" if skipped | Determines whether a shareable review step is needed |
| Z4 | Do you have any image-generation connector active in your claude.ai session? | **T3** *(retagged from T2)* | always, bundled into end-of-interview review in fast mode | assume no | Changes what Stage B can reasonably request. Default assume no |
| Z5 | **NEW.** Do you have access to claude.ai Projects or custom instructions in your session? | T2 | always | assume no | Closes a gap where §17-O27's stated resolution was literally "ask in the interview" and no such question existed; sits beside `Z4` since both gate what the Step-2/Step-3 hand-back can assume about the user's claude.ai environment |

*Row-count for this wave: 37 (Content 6, Brand 6, Accessibility 3, Performance 3, Localisation 4, Legal 4, Hosting 6, Custom 2, Decision process 3).*

### Wave 5 — Negative constraints & success criteria

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| V1 | Is there a colour, symbol, font, or visual cliché that must never appear? | T1 | always | "none named" if skipped, but flagged as a weaker deny-list than an explicit answer | Per-project deny-list layered on the standing anti-slop list |
| V2 | Is there a past design — yours or a competitor's — you're actively moving away from? | T1 | always | "none named" if skipped | Concrete "not this" anchor for the concept gate |
| V3 | Are there tone, imagery, or humour lines this brand must never cross? | T2 | always | "none named" if skipped | Brand-safety, distinct from visual constraints |
| V4 | When you look at the finished site, what will tell you it was worth doing this way instead of picking a template? | T1 | always | no default — hard block, this is the qualitative acceptance bar the human applies at LOCK and cannot be safely invented | The qualitative acceptance bar the human applies at LOCK |
| V5 | What would make you say LOCK today, versus asking for one more round of variants? | T1 | always | no default — hard block | Operationalises the Step-5-vs-Step-7 branch |

*Row-count for this wave: 5.*

---

### 5.1 Row-count self-audit (must be re-verified any time a row is added or removed)

| Wave | Rows | Detail |
|---|---|---|
| Wave 0 | 8 | C1–C6 (6) + Z1, Z2 moved in (2) |
| Wave 1 | 16 | Purpose 6 (P1–P6) + Positioning 5 (B1–B5) + Audience 5 (A1–A5) |
| Wave 2 | 10 | TS1–TS10 |
| Wave 3 | 14 | Theming 5 (D1–D5) + Component 3 (D6, D7, D11) + Identity 3 (D8–D10) + Motion 3 (M1–M3) |
| Wave 4 | 37 | Content 6 (N1–N6) + Brand 6 (N7–N12) + Accessibility 3 (X1–X3) + Performance 3 (X4–X6) + Localisation 4 (L1–L4) + Legal 4 (G0–G3) + Hosting 6 (H1–H6) + Custom 2 (U1–U2) + Decision process 3 (Z3–Z5) |
| Wave 5 | 5 | V1–V5 |
| **Total** | **90** | 83 original rows (corrected count; earlier drafts said 78, which under-counted by omitting Wave 5) + 7 new rows added by this revision: `C5`, `C6`, `P6`, `D11`, `G0`, `Z5`, `N12` |

### 5.2 Fallback flows

- **User can't name any reference site they like** — a documented real failure mode. Auto-suggest a curated reference set by detected vertical, and if that fails, run a broader first-pass style-family sort (8 families) before individual-site references. **[V — practitioner reports; the fallback design is inference]**
- **User declines the accessibility questions** — auto-answer "AA, no known legal requirement" unless `G0`'s jurisdiction derivation already flagged a real requirement, in which case that requirement is recorded instead of the generic default. Never silently omit the gate.
- **User gives vague strategy answers** ("I want it to look nice") — the concept gate will produce a generic document and all 10 directions inherit that blandness. Mitigation: the interview pushes with concrete follow-ups ("what would you *not* want it to look like?") and refuses to advance to Step 2 until the concept document names at least one thing the site refuses to do.
- **"I don't know / surprise me" affordance** — present on every Tier-1 and Tier-2 taste question (Wave 2, plus `B4`, `B5`, `D8`–`D10`, `M1`–`M2`). Taking it routes the skill to propose options derived from the reference-swipe results (`TS1`–`TS3`) rather than the user inventing an unattributed preference, and always records a concrete default value per the Tier notation's "explicitly defaulted" state — never a null.

### 5.3 Acceptance criteria (new — closes the untestable-claim gap)

- **AC-5.1 (defaulting is real, not silent).** Every Tier-1 question in a completed interview is either answered by the user or carries a `"source": "skill-default"` entry with a concrete value in `00-interview/answers.json`. No Tier-1 field may be null or absent at Step-1 exit.
- **AC-5.2 (row-count integrity).** A script cross-checks the total row count in this section's tables against the number asserted in the self-audit table (90) on every edit to this file, so the count cannot silently drift the way "78" did.
- **AC-5.3 (common-case count, honestly bounded).** A simulated run with `C1="fresh"`, `C6="no"`, `L1="no"`, no form-bearing component selected, `G1="no"`/no jurisdiction trigger, no dark taste signal, and `Z1="one sitting"` should ask **45–55** Tier-1 questions plus the single 6-item Tier-3 review screen. **This revises A19-A3's "≤45" bound** — flagged for §19's owner to reconcile; this section does not edit §19 directly.
- **AC-5.4 (measured, not estimated, duration).** Median wall-clock interview duration for the common case is instrumented from the first release and compared against the 25–35 minute (fast mode) / 45–70 minute (open-ended mode) estimates above. **No known mitigation besides measurement** — every time figure in this section is a projection until real sessions are logged.

---
