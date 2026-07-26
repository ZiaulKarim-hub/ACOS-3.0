# Website Builder — Product Requirements Document

**Skill name:** `acos-website-builder`
**Status:** Draft for approval
**Date:** 2026-07-25
**Sources:** 12 independent research lenses + prior swarm report `/Users/zee/Documents/Vibe Coding/ACOS 3.0/.acos/swarm/swarm-20260718-022431/synthesis/report.md`

Throughout this document: **[V]** marks a verified fact with a named source. **[I]** marks inference. **[U]** marks an unsourced claim to be treated as inference. Disagreements between research lenses are footnoted and resolved in §20.

---

## 1. Summary

### What this is

Website Builder is an ACOS skill that turns a conversation into a distinctive, hand-adjustable website. It runs in eight steps:

1. It checks whether you already have a design system or a prior site (warm start).
2. It **interviews you** — about purpose, audience, positioning, taste, accessibility, performance, and constraints.
3. It **writes a prompt** for you to paste into claude.ai on the web, where Claude's design/artifact generation produces a complete design system: typography, colour, motion, artwork, components, and everything else the site needs.
4. You **hand-carry** the result back.
5. It **interviews you again** to select each component, then builds the site as a **live editable design surface** — gridlines you snap to, components you drag, text you edit in place, a component bar for swapping any element for a comparable variant, and a save button.
6. You can ask for **more variants** or a **redesigned system** at any point.
7. You can add **custom components** the standard system doesn't cover (charts, calculators, maps).
8. You say **LOCK** — the design toolbars and gridlines disappear and you get a clean static site with no editor code in it, while the editable version stays beside it. Then it publishes, with a licence-and-evidence bundle listing every font and asset.

The human is the aesthetic judge. There is no AI critic scoring screenshots in a loop. Machines enforce the things machines are good at — contrast ratios, token purity, reflow at 320px, licence completeness, "does the editor runtime actually not ship" — and the human decides everything about how it looks.

### What this is not

- **Not an autonomous site generator.** The prior swarm report designed an award-quality generator that judges its own screenshots and iterates. That architecture is explicitly replaced. Its rubrics, anti-slop lint, stack recommendations, licensing policy, performance gates, and capture protocol are reused; its judge loop is not.
- **Not Webflow.** The pixel canvas is the last thing built, not the first, and the layout model is constraint-based by default (D2), not free x/y.
- **Not a template picker.** Directions are generated per project against the interview answers, not chosen from a fixed gallery.
- **Not a claim of WCAG certification.** Automated accessibility tooling tops out around 57% of real issues [V — Deque Accessibility Coverage Report, 13,000+ pages/page-states]. The evidence bundle will say "passed N automated gates," never "AA compliant."
- **Not a raster art generator.** claude.ai cannot produce bitmap images [V — confirmed by Anthropic, April 2026]. Art comes from code-drawn SVG/CSS/canvas, from an ingested asset library, or from a separately-scoped external generator. See §7.9 and §17-R1.
- **Not award-winning by construction.** A swap-menu builder produces coherent, bespoke, hand-adjustable sites. Award juries recognise assembled output [V — prior swarm report Finding 2]. The one lever that raises the ceiling is the custom code block (§10.7, §14.4), and the PRD says so plainly rather than over-promising.

---

## 2. Goals, non-goals, and success criteria

### 2.1 Goals

| # | Goal | Why |
|---|---|---|
| G1 | A single human, in one working session, goes from "I need a site" to a locked, publishable site that looks deliberately designed | The whole product |
| G2 | Every visual decision traces to an interview answer or an explicit human pick | Makes the design defensible and re-derivable; operationalises the prior report's concept-gate traceability rule |
| G3 | The design system is coherent by construction — derived values are computed, never picked (D1) | Prevents the clash that ~80 independently-chosen items produces |
| G4 | The site works at 320px and 1440px without the human doing responsive work (D2) | Constraint dragging exists for this reason |
| G5 | LOCK produces a static site with provably zero editor runtime, reversibly (D3) | The export contract |
| G6 | Run N+1 starts warm from run N's reusable assets without inheriting run N's identity | Warm start that doesn't homogenise the user's portfolio |
| G7 | Every font and asset in the shipped site has a recorded licence class | Legal exposure is concentrated here |
| G8 | The tool is used more than twice | The manual hand-carry is the biggest threat to this |

### 2.2 Non-goals

| # | Non-goal | Reason |
|---|---|---|
| NG1 | AI aesthetic judging of any kind | Replaced by the human, per the product brief |
| NG2 | Multi-user real-time collaboration | Single-user product; comment schema is collaboration-ready but no second writer in v1–v3 |
| NG3 | A CMS or backend | Static output; forms use a third-party endpoint or a mailto fallback |
| NG4 | Application-shell UI (dashboards, auth, settings, data tables at scale) | 62 inventory items are app-shell/commerce/exotic-chart; gated behind the site-type answer and deferred to v3 |
| NG5 | Raster image generation inside the pipeline | Structurally impossible on the claude.ai leg |
| NG6 | Rewriting existing Python ACOS tooling | Read-only reference; new code is TypeScript per the standing language rule |

### 2.3 Success criteria

| # | Criterion | Measurement |
|---|---|---|
| S1 | Interview completes in ≤30 minutes for the common case | Wall-clock, single-language single-surface marketing site, ~35–45 answered questions |
| S2 | Hand-carry completes in ≤3 pastes per chunk, ≤6 chunks total | Count of `pbpaste` ingests per generation cycle |
| S3 | Zero `data-wb-*` strings in `dist/published/**` | Grep assertion, build-failing |
| S4 | Editor-installed build and editor-uninstalled build are byte-identical | `diff -r` of two dist trees |
| S5 | Locked site passes all Tier-1 lock gates (§13.4) | Gate suite exit code |
| S6 | The human can name why they chose their direction | The concept document records it; qualitative |
| S7 | A content-only edit six months later requires no dev server | Content mode (§15.5) |

---

## 3. Users and usage model

### 3.1 Primary user

One person — the ACOS owner — building sites for their own projects (FruitSync, OKOA, future ventures). Technically capable, not a trained designer, has strong taste but limited design vocabulary. Owns a Claude subscription with web access. Works on macOS. **[V — established from repo context and the user's own prior work at `/Users/zee/Documents/Vibe Coding/website-design-okoa/`]**

### 3.2 Secondary users (design for, don't optimise for)

- A future collaborator reviewing a site before LOCK (read-only preview link, v2).
- The user themselves six months later, making a copy change (content mode, v2).

### 3.3 Usage model

| Mode | Trigger | What happens | Session shape |
|---|---|---|---|
| Cold start | `/acos-website-builder` in a project with no prior site | Full interview → prompt → hand-carry → build → edit → lock | One long session, resumable |
| Warm start | Prior design system detected at Step 0 | "What's changing?" interview (much shorter) → optionally reuse tokens → build | Half a session |
| Return-to-edit | `/acos-website-builder --resume` | Reads `state.json`, recomputes phase from disk, re-attaches to the running server or restarts it | Minutes |
| Content edit | `/acos-website-builder --content` (v2) | Text-only editing path, no dev server, no design layer | Minutes |
| Variant round | User clicks "more variants" in the editor | Deterministic generator produces 5–10 neighbours; no claude.ai hop | Seconds |
| System redesign | User asks for a new/partial design-system prompt | Back to Step 2 with prior parameters as negative constraints | New hand-carry cycle |

### 3.4 The human's role, stated plainly

The human supplies **taste** (which direction, which variant, where things go, what the copy says) and **acceptance** (LOCK). The machine supplies **coherence** (derived tokens, direction hashing, lint), **correctness** (contrast, reflow, licence, export purity), and **labour** (generation, layout, build, publish). The machine never overrides a taste decision; it may refuse to ship a correctness violation.

---

## 4. The pipeline — all 8 steps

### Step 0 — Warm start / continuity check

| | |
|---|---|
| **Inputs** | Target project path; glob of `.acos/design-library/*/design-system-spec.yaml`, `.acos/website-builder/systems/*/system.json`, the target project's own `.acos/`, and any asset library (sprite folders, photo folders, existing site trees) |
| **Process** | Scan for prior systems and prior sites. Scan for an **asset library** — this is the binary that decides whether artwork is real or theatre (§17-R1). Detect any existing site to mine for copy/structure. Present findings. Split what's offered into **reusable system assets** (always offered) and **identity** (offered only if the user declares a sibling site). |
| **Outputs** | `session.json` with `{warmStart: none\|system-only\|full, sourceSystemId, assetLibraryPath, minedSources[]}` |
| **Exit criteria** | User has explicitly chosen fresh / reuse-as-is / reuse-and-revise, and the asset-library question is answered |

The split matters. Reusable across projects: token-name schema, component slot contracts, motion-primitive library, font catalog, anti-slop deny-list, editor configuration, user-level interview answers (accessibility posture, device assumptions, decision style). Never reused by default: hue anchors, type pairings, radius/density, motion character, artwork. Prior identities are injected into Step 2 as **negative constraints** unless sibling mode is on. **[I — mitigates the portfolio-homogenisation risk identified in Lens 12]**

### Step 1 — Interview

| | |
|---|---|
| **Inputs** | Warm-start state; any mined sources (repo, old site, deck) |
| **Process** | Five hard-gated waves in fixed order: (0) Continuity — already done in Step 0; (1) Strategy; (2) Taste (visual before verbal); (3) Design-system specifics; (4) Constraints & admin; (5) Success criteria. Aggressive branching. Every answer keyed by stable question ID. Three tiers: Tier 1 gates the prompt, Tier 2 asked just-in-time, Tier 3 inferred with a visible overridable default. |
| **Outputs** | `00-interview/answers.json` (question-ID-keyed), `00-interview/concept.md` (200–300 words: point of view, ≥3 abstracted references, restraint budget, what it refuses to do) |
| **Exit criteria** | All Tier-1 questions answered or explicitly defaulted; concept document written and confirmed by the user |

Full question bank: §5.

### Step 2 — Generate the design-system prompt

| | |
|---|---|
| **Inputs** | `answers.json`, `concept.md`, the pinned font catalog, the token-name manifest, prior-identity negative constraints |
| **Process** | Render a multi-stage prompt. **Stage A** asks for ~10 lightweight direction capsules plus one gallery artifact. **Stage B** (run per shortlisted direction) asks for the full DTCG token expansion, the identity-carrying component instances, and the artwork with affinity tags. Every prompt embeds: the exact return-format schema, a worked micro-example, the closed font vocabulary, the frozen token-name manifest, the CSP constraint, and a self-audit instruction. The skill computes the chunking. |
| **Outputs** | `01-prompt/stage-a.md`, `01-prompt/stage-b-<directionId>.md`, `01-prompt/artwork.md`, plus a copy-ready display in the terminal |
| **Exit criteria** | Prompts written to disk and displayed; user confirms they have them |

Full prompt spec and return schema: §6.

### Step 3 — Hand-carry (manual)

| | |
|---|---|
| **Inputs** | The generated prompt(s), pasted by the user into claude.ai |
| **Process** | User pastes prompt → claude.ai generates → user copies the response (one `Cmd+A`/`Cmd+C` per chunk under the one-paste protocol) → runs a one-word skill command → skill ingests via `pbpaste`. Tolerant parser splits on fenced blocks with `FILE:` headers, validates against the envelope manifest (file list, line counts, sha256 prefixes, a per-run random terminator token), and runs the deterministic re-verification pass. |
| **Outputs** | `02-system/<directionId>/{tokens.json, tokens.css, components/*.html, artwork/*}`, `02-system/manifest.json`, `02-system/import-report.json`, `02-system/system.lock.json` |
| **Exit criteria** | Manifest present and parseable; declared counts match actual counts; terminator present; zero unquarantined security rejections; all contrast and licence claims independently recomputed |

**Escape hatch, first-class:** if claude.ai is unavailable, lossy, or the user simply doesn't want the round-trip, **Local Regeneration Mode** runs the identical prompt against a Claude Code subagent, producing output in the identical format with zero pastes. The hand-carry is a UX preference, not a technical dependency. **[I — the skill runs on the same model family]**

Full boundary spec: §6.

### Step 4 — Select and build the editable design surface

| | |
|---|---|
| **Inputs** | The ingested system; the interview's sitemap and content answers |
| **Process** | Direction selection as a **tournament** (3 at full size → pick → 3 → pick → head-to-head), not a 10-up grid. Then per-slot component selection, defaulting to the direction's canonical variant so the user only opens the component bar when dissatisfied. Then the skill generates `layout.json` + `content.json`, renders the site, and launches the editor. |
| **Outputs** | `04-site/{layout.json, content.json, provenance.json}`, a running local editor at a fixed port, `state.json` with `{port, pid, url, sessionId}` |
| **Exit criteria** | Editor serves HTTP 200, verified by a curl in a **separate tool call** after the turn boundary (see §16.6); the user can see and edit their site |

Full editor spec: §10. Layout model: §11.

### Step 5 — More variants / redesign

| | |
|---|---|
| **Inputs** | The current direction, a component id or a system scope, the current highest variant index per item |
| **Process** | "More like this" generates 5 deterministic neighbours of an approved variant. "More variants" generates the next N for a slot. "Redesign part of the system" re-enters Step 2 with the current parameters as constraints (keep these, change these). Full redesign is a new Step 2 cycle with prior identity as negative constraint. |
| **Outputs** | Appended variants with append-only indices; on redesign, a new `system.lock.json` and a migration report mapping old variant ids to new |
| **Exit criteria** | New variants visible in the component bar; on redesign, every existing node either remapped or explicitly reported as unmappable — never silently dropped |

### Step 6 — Custom components

| | |
|---|---|
| **Inputs** | A user request for a component the system doesn't have (chart, calculator, map, embed, game, signature moment) |
| **Process** | Route to one of three paths: (a) **registry component** — a whitelisted family (table, chart, embed, form) generated against the direction's tokens by a deterministic generator plus the dataviz sub-token set; (b) **agent-authored** — `Task(general-purpose)` returns code as text, main thread writes it, runs the six coherence lints before acceptance; (c) **custom code block** — an opaque draggable container holding hand-written HTML/CSS/JS that the editor positions but never introspects. Path (c) is where the signature moment lives. |
| **Outputs** | `06-custom/<componentId>/`, registration in the component registry, an entry in the coherence ledger if it introduces off-system values |
| **Exit criteria** | Component renders, satisfies the container contract, passes the coherence lints or is recorded as accepted debt |

### Step 7 — LOCK

| | |
|---|---|
| **Inputs** | `layout.json`, `content.json`, `system.lock.json`, the component library |
| **Process** | **Re-render**, never copy-and-strip. Same renderer, `editor: false`. Then: scrub any residual `data-wb-*` in `astro:build:done`; run the ordered lock-time checklist (§13.4); assert zero editor strings; byte-compare against an editor-uninstalled build; snapshot documents into `.wb/locks/<iso>/`; git-tag `wb-lock/<n>`. LOCK writes only to `dist/published/` and `.wb/locks/` — it never mutates the design project, so UNLOCK is simply restarting the design server. |
| **Outputs** | `07-lock/dist/`, `07-lock/lock-manifest.json`, gate report, screenshots at 320/390/768/1440 |
| **Exit criteria** | All Tier-1 gates pass; the two-build byte-equality check passes; the lock manifest records the layout hash so a later unlock can diff against hand-edits |

Full contract: §12.5.

### Step 8 — Publish + evidence bundle

| | |
|---|---|
| **Inputs** | `dist/published/`, the asset manifest, the gate report, the direction tour log |
| **Process** | Deploy via `wrangler pages deploy ./dist --project-name=<x>` with a stored scoped token (one-time credential setup). Assemble the evidence bundle: per-font `{family, foundry, licenceClass, fileHash, sourceUrl, attributionRequired}`; per-asset `{generator, model, planTier, licenceClass, prompt, alt}`; the gate report; the screenshots; the direction tour with the user's pick and stated reason; an explicit "manual accessibility review not performed" disclosure. Mirror a one-line verdict into `.acos/evidence/<date>/website-<session>/`. |
| **Outputs** | A live URL; `evidence/` bundle; a git tag |
| **Exit criteria** | Deploy returns success; evidence bundle is complete with zero unlicensed assets |

**If deploy is not automated in v1**, the PRD says so explicitly and emits a runbook. It does not leave the boundary ambiguous — the user's existing FruitSync deploy runbook already documents a manual Cloudflare dashboard drag-and-drop **[V — `/Users/zee/fruitsync-animated-variants/_release/DEPLOY-STEPS.md`]**, and silently repeating that is a friction tax on every future edit.

---

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

## 6. Step 2 — the design-system generation prompt

### 6.1 What the prompt must demand

| # | Demand | Why |
|---|---|---|
| 1 | **DTCG 2025.10 format verbatim**, with a literal worked example, not a description | The spec changed the colour token shape to an object with `colorSpace`/`components`/`alpha`/`hex`; any model working from pre-2025 examples emits a hex string and the pipeline breaks **[V — designtokens.org/TR/drafts/format/, version 2025.10, dated 17 June 2026]** |
| 2 | **OKLCH hue anchors, chroma ceiling, neutral temperature, scheme strategy — never hex swatches** | The colour solver (Leonardo model: declare target contrast ratios, solve for colours) runs locally. Asking for swatches gets swatches that fail contrast **[V — adobe/leonardo contrast-colors README]** |
| 3 | **An explicit statement that OKLCH hue ≠ HSL hue** — 0° is magenta, red is ≈41° | A prompt that says "hue 0 for red" silently produces a magenta-based palette across every direction **[V — MDN oklch(), Baseline May 2023]** |
| 4 | **Font pairings chosen from an embedded, pinned OFL shortlist** — never open-ended naming | Closes the hallucinated-foundry-licence failure and the off-shortlist-licence failure in one move, and makes the output trivially cross-checkable |
| 5 | **A base64 `data:font/woff2` @font-face for each direction's display face**, subset to the preview glyph set | The artifact CSP permits `fonts.googleapis.com` under `style-src` but restricts `font-src` to `data:` and `claudeusercontent.com` — the CSS loads and the WOFF2 is blocked, so a Google-Fonts direction previews in a system face. **You would pick a look you never saw.** A Latin-subset display WOFF2 is typically 8–20KB, ~11–27KB base64 **[V — content-security-policy.com + claude-artifacts-guide CSP list; size figures are inference]** ¹ |
| 6 | **Vanilla HTML + inline CSS + optional vanilla JS for every component variant — never React** | Sidesteps the unpublished, unstable React-artifact import allowlist, and vanilla fragments are what the editor's anchored DOM actually needs |
| 7 | **Everything self-contained** — inline `<style>`, data-URI images, no CDN links, no `@import` | The artifact CSP blocks all outbound requests; a `<link>` to Google Fonts silently fails |
| 8 | **A frozen token-name manifest, re-pasted verbatim in every chunk** | Across chunks/conversations the model re-invents names (`--color-accent` in chunk 1, `--accent` in chunk 3). Component swaps then resolve to nothing and render unstyled with no error. The ingest **hard-rejects** any key not on the manifest — no fuzzy remapping, which would be a new bug factory |
| 9 | **Prior-direction parameters as negative constraints in every subsequent chunk** | Divergence must be enforced by the skill, not hoped for from the model. "Do not produce a direction whose hue anchor is within 30° of any of these, or that reuses any of these type pairings" |
| 10 | **A per-item `com.acos.llm` extension block** — `{usage: string[], rules: string, antipatterns: string[]}` on every semantic token | Copied from GitHub Primer's shipped `org.primer.llm` pattern. This is what lets the building agent select the right token without guessing **[V — primer/primitives functional/*/\*.json5, quoted verbatim]** |
| 11 | **A `com.acos.pick` block** — `{pickable, slot, directionId, variantIndex, derivedFrom[]}` | The editor renders a control **only** where `pickable: true`. This is how D1's "derived values are never picked" becomes structurally enforced rather than documented |
| 12 | **A `com.acos.direction` block** — `{id, vectorHash}` | The builder rejects any token whose hash ≠ the active direction. Stops cross-contamination during component swaps |
| 13 | **A root capability manifest declaring expected counts per group** | Makes truncation detectable: the skill compares declared to actual on ingest |
| 14 | **A paired reduced-motion variant for every motion item**, art-directed with WCAG-exempt vocabulary (opacity/colour/blur), never `animation: none` | The editor cannot invent a good reduced variant for an animation it never saw the internals of. If this isn't demanded upstream, every animated element degrades to a generic freeze |
| 15 | **A 390px-wide preview frame inside every direction artifact**, alongside the desktop frame | Directions are otherwise judged only at desktop width; art tied to a 16:9 hero doesn't crop to 390×844 portrait, and the user selects a direction they've never seen at the viewport most visitors use |
| 16 | **A self-audit closing step**: recount the manifest against what was actually emitted and list any gaps | Cheap; reduces how often the ingest validator has work to do |

¹ **Verify before shipping the prompt spec.** Open a claude.ai artifact with a Google Fonts `<link>` and check computed `font-family` in devtools. This is a 60-second test that determines whether typography can be judged on the web side at all. See §17-O1.

### 6.2 The exact return-format schema

**Envelope (mandatory, per chunk):**

````
```json
FILE: manifest.json
{
  "templateVersion": "1.0.0",
  "chunk": { "index": 2, "of": 6, "kind": "direction-deep-dive", "directionIds": ["d03"] },
  "files": [
    { "path": "tokens/d03.tokens.json", "lines": 412, "sha256Prefix": "a91f0c" },
    { "path": "components/d03/button-primary/01.html", "lines": 38, "sha256Prefix": "77bd21" }
  ],
  "countsDeclared": { "directions": 1, "components": 22, "artwork": 0 },
  "terminator": "<<<ACOS-END-a7f3>>>"
}
```
````

Then every subsequent fenced block opens with a `FILE:` comment in that block's own comment syntax:

````
```json
// FILE: tokens/d03.tokens.json
{ ... }
```

```html
<!-- FILE: components/d03/button-primary/01.html -->
<!-- ACOS-COMPONENT id=d03.button-primary.01 item=button-primary direction=d03
     tokens-used=--color-accent,--radius-md,--motion-fast slots=label,icon? -->
<button class="btn-primary">…</button>
<style>…</style>
```
````

And the very last line of the response is the terminator token verbatim.

**Ingest contract.** The skill splits on triple-backtick fences, reads each block's `FILE:` line, writes to that path, then validates:

| Check | On failure |
|---|---|
| Manifest present and parseable | **Hard fail.** Name exactly what's missing; offer re-paste or Local Regeneration |
| Terminator line present as the final line | **Hard fail** — this is a truncation, and a truncated CSS block is still *valid CSS* that renders. This is the corruption-without-symptom class and the single most expensive failure at this boundary |
| Per-file line counts match declared | **Hard fail** on the mismatching file only; auto-draft a repair prompt naming it |
| `countsDeclared` == counts actual | Mark missing ids MISSING, ingest everything else, draft a targeted repair prompt |
| JSON parses strictly | Attempt a **tolerant repair pass** (trailing commas, obvious syntax slips) before declaring failure; log what was auto-fixed |
| Every token key ∈ frozen manifest | **Hard reject** the offending key. No fuzzy remapping |
| DTCG schema valid | Reject with the specific path that failed |
| No `fetch(`, `eval(`, `new Function`, non-local `import(`, `process.`, `child_process`, remote `<script src>`, remote `@import`/`url()`, inline event handlers | Quarantine that item; continue |
| Every contrast pair recomputed locally (WCAG 2 + APCA) | Auto-nudge OKLCH lightness deterministically; if the fix exceeds a delta threshold, flag for human confirm. Never trust a stated pass |
| Every font ∈ pinned OFL shortlist | Auto-substitute nearest OFL match in the same classification, log a licensing note, continue non-blocking |
| Every asset reference resolves inside the bundle | Mark that one variant DEGRADED, exclude it from the swap bar, don't block the rest |

Files are emitted **smallest-first** so a truncation loses the least.

### 6.3 Chunking strategy

Hard numbers from the user's own precedent: each FruitSync variant page is 35–43KB of self-contained HTML+CSS (~10–12K tokens); the shipped release index is 92KB **[V — `wc -c` on 6 variant files]**. A full direction at that fidelity is ~40KB minimum. Ten directions plus 20 artworks is ~400KB (~110K tokens) against a 200K claude.ai context that artifacts count against.

| Chunk | Content | Approx size |
|---|---|---|
| A | ~10 direction capsules (26-slot vector + 40–80 word manifesto each) + ONE gallery artifact previewing all 10 as hero cards at desktop AND 390px | Small; fits reliably |
| B₁…Bₙ | Full DTCG expansion + identity-carrying component instances for **one shortlisted direction** each. Run only for directions the user actually shortlists | ~40KB each |
| Art | The 20 artworks with `suitsDirections[]` tags | Variable |

**Why Stage A is thin:** it is what the user actually judges. Generating all 10 in full upfront wastes ~90% of the output because 9 expansions are discarded.

**claude.ai constraint:** the platform commits to one live-updating artifact per turn — a new reply iterates the *same* artifact in place, and separate artifacts accumulate *across* turns via a panel switcher. There is no documented mechanism for one response to open ten independently-addressable artifacts **[V — support.claude.com/en/articles/9487310 + multiple 2026 guides converging; medium confidence]**. So: at most ONE artifact per response (the gallery, for eyeballing), and the machine-readable payload in ordinary fenced code blocks, which have no such limit.

### 6.4 The one-paste protocol

Naive hand-carry is 35–60 discrete copy → switch app → paste → name → file operations at ~60–90s each: **45–90 minutes of the user's hands per generation cycle**, and Step 5 makes it a loop. This is the most likely way the product quietly dies.

The protocol: **one fenced block per chunk containing the manifest with inline file contents.** One `Cmd+A` / `Cmd+C` per chunk. The skill ingests via `pbpaste` on a one-word command. ~40 operations become ~5. **[I — sized against first-party artifact counts]**

### 6.5 Local Regeneration Mode (first-class, not a fallback of last resort)

The same prompt, the same schema, run against a Claude Code subagent. Zero pastes, deterministic filing, schema-validated at write time. The claude.ai hop becomes an opt-in "I want the web model's design sense for this one" path.

**If the PRD hard-wires the paste as mandatory, usage frequency is capped by the user's tolerance for clerical work.** Local Regeneration Mode ships in v1.

---

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

## 10. Step 4 — the editor: full feature set

Grouped by function, with v1/v2/v3 priority. **~35 of ~95 items are v1.** Canva — explicitly built for non-designers — ships by default only canvas + snap, layers, undo, basic text/image editing, one-click template swap, and a share link. Grids, rulers, breakpoint cascades, version diffing and comment pins are hidden or absent. **[U — product knowledge, treat as inference]**

### 10.1 Layout & placement

| Feature | Priority | Notes |
|---|---|---|
| Real-grid overlay (gridlines) | v1 | **Drawn by reading `getComputedStyle(section).gridTemplateColumns`** and painting those exact resolved tracks. Never decorative — it is the snap target, and it lives in the out-of-iframe overlay so it disappears at lock by construction |
| Snap engine | v1 | Two 1-D interval indexes per section over four prioritised target classes: grid lines > sibling edges/centres > section padding & content rails > spacing-scale increments. Tolerance 6–8 CSS px **divided by zoom** — a classic regression if missed |
| Smart alignment guides + distance labels | v1 | Dashed guides + live gap measurements in the accent colour; equal-spacing indicators when 3+ siblings match |
| Align tools | v1 | left/centre/right/top/middle/bottom, relative to siblings or parent |
| Distribute tools | v2 | Equalise gaps across 3+ selections, operating on **grid integers**, not pixels |
| Padding / gap drag handles | v1 | Draggable inner edges snapping to **discrete spacing-scale steps only**, showing the token name (`space-6`), never a raw pixel value. **This is the mechanic that stops direct manipulation destroying the token system** — no commercial builder does it |
| Drag-to-place (grid write) | v1 | Ghost preview follows the pointer continuously; commit writes `{col, colSpan, row, rowSpan}` integers for the active breakpoint. Pointer capture on the overlay so the drag survives leaving the iframe |
| Span resize | v1 | Edge handles change span in whole cells with a live "6 of 12 · 50%" readout so the user learns the fluid consequence |
| Section reorder | v1 | Vertical only, via the Navigator or a section rail. Sections are never dragged horizontally |
| Breakpoint switcher | v1 | 390 / 768 / 1280 / full, with **pinned device heights** (390×844, 768×1024, 1280×800) whenever the page contains any vh/svh/dvh rule |
| Per-breakpoint override + reset-to-inherited | v1 | Desktop-down cascade with sparse overrides. Every overridden property shows an "overridden here" dot and a one-click reset |
| Anchor/pin control | v1 | The core D2 primitive. **Three verbs only**: align to (left/centre/right/stretch), space above/below (stepper over the scale), order (up/down among siblings) |
| Free-position escape hatch | v2 | See §11.4. Deliberately v2 so the safe path ships and is proven first |
| Type-aware resize | v1 | Text reflows at fixed font size; images rescale aspect-locked; inline SVG rescales losslessly; tables scale uniformly with a separate per-column handle. **Reusable prior art from the ACOS HTML-to-PDF Visual Composer vision** |
| Canvas zoom + pan | v2 | 25–200%, snap tolerance ÷ zoom, space-drag pan. Deferred because a fixed-viewport iframe is usable without it |
| Drag-resizable canvas frame | v2 | Stress-test reflow at in-between widths (catches breakage at, say, 610px) |
| Rulers | v2 | |
| Custom drag-out guides | v2 | **Stored as fractions of the content-width rail, not pixels**, so they survive breakpoint switches |
| Flex/grid container controls | v2 | Direction, gap, wrap, justify/align as icons and steppers, never raw CSS |
| Keyboard nudge & grid stepping | v1 | Arrow = one cell, Shift+arrow = span ±1, Tab walks siblings. **Also the WCAG 2.5.7 single-pointer alternative — see §13.2** |

### 10.2 Structure & selection

| Feature | Priority | Notes |
|---|---|---|
| Selection overlay + handles | v1 | Drawn **outside the iframe** with `pointer-events: none`, so no editor node ever enters the exported DOM |
| Drill-in / drill-out selection | v1 | Click = nearest top-level block; Enter/double-click descends; Esc ascends. Hit-test via `elementFromPoint` inside the iframe, walking up to the nearest `[data-wb-node]`. **Known edge: `elementsFromPoint` does not return the iframe when something is fullscreened over it — never fullscreen the canvas while editing** |
| Breadcrumb ancestor bar | v1 | Ancestor chain under the canvas, selected element rightmost, every entry clickable |
| Navigator / layers tree | v1 | **Non-optional.** Canvas clicking provably cannot reach zero-height wrappers, covered elements, `pointer-events: none` decoration, or empty slots. Webflow ships all three selection channels for exactly this reason. A full-bleed background art container will otherwise swallow every click |
| Drag-to-reorder / reparent in tree | v1 | The only reliable way to fix z-order or nesting without canvas gymnastics |
| Hide/show toggle per layer | v1 | |
| Rename layer/component | v2 | Makes the tree navigable at 50+ elements |
| Multi-select | v1 | Shift-click, marquee, select-all-of-type |
| Group / ungroup | v2 | |
| Element lock | v1 | Prevents accidental move/resize/delete. **Must use a different verb from the site-wide LOCK** — "Lock Element" vs "Publish" / "Preview as Visitor". Two "lock" concepts sharing vocabulary is a real confusion risk |
| Duplicate with smart offset | v1 | |
| Cut/copy/paste incl. paste-to-replace | v1 | Clipboard round-trip as `layout.json` fragments **including all breakpoint overrides** |
| Delete with recovery bin | v1 | **Independent of the undo stack** — "I deleted this three edits ago" is common and chaining undo back would revert everything since |
| Global/shared component with instance overrides | v1 | **A prerequisite for safe variant swapping, not optional plumbing.** Without it, either every page-level edit drifts independently or every system-level edit needs manual re-application. Build this data model **before** the component-bar UI |
| Section boundary markers | v1 | Visible wrapper boundaries so "regenerate this section" has an unambiguous target. **A fuzzy boundary lets regeneration leak into neighbouring content** |
| Per-breakpoint visibility | v1 | Compiled to a display rule, not duplicate markup. Lint warns if hidden at every breakpoint |

### 10.3 Content

| Feature | Priority | Notes |
|---|---|---|
| Inline text editing (tier 1) | v1 | **`contenteditable="plaintext-only"`** on headings, eyebrows, buttons, nav items, labels, stat numbers — ~90% of a marketing page's text nodes. Strips all paste formatting, avoids cross-browser Enter-key markup divergence, and prevents Word markup entering an award-grade type system. Baseline newly-available **[V — web.dev, caniuse]** |
| Rich-text block (tier 2) | v2 | ProseMirror/TipTap (MIT) on **long-form prose blocks only**, restricted to an approved mark set (bold, italic, link, list, blockquote) — no font/colour/size controls |
| Plain-text swap mode | v1 | Editing a token-bound label changes only the string, never the styling |
| Image replace | v1 | Keeps container size/crop/position intact |
| Image crop + focal-point picker | v1 | **A single draggable dot, not a crop rectangle.** A single 2D point degrades gracefully across every container aspect ratio a reflow system produces; per-breakpoint manual crops do not. **Direct prior art from the ACOS HTML-to-PDF Visual Composer vision** |
| Alt-text field | v1 | Required-nudged; placing any image opens a micro-field for alt text **or an explicit "decorative" toggle**. Blocks the placement, not just the lock |
| Asset/media manager | v1 | Searchable library tagged by which direction each asset suits |
| Component-bar variant swap | v1 | Core Step-4d feature. See §8.5 for presentation rules and §10.8 for the coherence contract |
| Variant hover-preview before commit | v1 | Ghost-previews live in the actual page context (current copy, current neighbours). **Essential, not nice, once there are 10 variants** — an isolated thumbnail can't show fit |
| Icon picker | v2 | |
| Embeddable content blocks | v2 | Video, maps, forms |
| Custom-component insertion | v2 | Step 6 |
| Table/data editor for charts | v3 | Lightweight spreadsheet backing any chart |
| Link field with validation | v1 | href + URL validation + `target=_blank` toggle |
| Site-wide link manager | v2 | Every internal and external link with destination and status |
| Per-page SEO/meta fields | v1 | Title, description, OG image, favicon |
| Multi-page manager | v1 | Add, duplicate, delete, reorder |
| Site-wide global regions | v1 | Header/footer/nav edited once, reflected everywhere |

### 10.4 History & persistence

| Feature | Priority | Notes |
|---|---|---|
| Undo / redo | v1 | **A single JSON-patch command stack** over `layout.json`, covering canvas drags, inspector edits and text edits alike, so the surfaces cannot desync. Split stacks are a classic confusing regression. Coalesces a continuous drag into one entry |
| Transactional grouping for multi-mutation actions | v1 | **A component swap or a section regeneration must be ONE undo step.** Naive per-mutation undo leaves a broken hybrid state after one Cmd+Z — a known failure class in AI-editing tools, and it fails exactly when the safety net matters most. **Needs dedicated test coverage** |
| Autosave | v1 | Debounced ~300ms, atomic (write-temp then `fs.rename`). **A small JSON diff POSTed to the server and written to disk — never a base64 blob in localStorage.** (The image-builder precedent's `toDataURL` autosave does not scale to a multi-page site) |
| Named snapshots | v1 | Explicit "save as milestone" distinct from the autosave stream |
| Save-as-variation / branch | v1 | **The mechanism that makes Step 5 safe** — try a new direction without losing the current one |
| Automatic timestamped version history | v2 | |
| Visual version diff | v2 | Side-by-side render with changed blocks highlighted, driven by a JSON diff |
| Non-destructive restore | v2 | Restoring creates a new version rather than overwriting the timeline, so restoring is itself undoable |
| Explicit manual save affordance | v2 | For psychological closure even though autosave covers it technically |
| Per-section regeneration log | v2 | Which sections were regenerated, from what note, when |
| Crash-recovery draft restore | v2 | Recover the most recent autosave, not the last named snapshot |

### 10.5 Navigation & wayfinding

| Feature | Priority | Notes |
|---|---|---|
| Page navigator | v1 | Thumbnail strip or list |
| Canvas ↔ tree selection sync | v1 | |
| Find/search | v2 | Cmd+F across layer names and text content |
| In-edit-mode link-follow | v2 | Modifier+click a link to jump to that page for editing |
| Jump-to-section quick nav | v3 | |

### 10.6 Quality (ambient, non-blocking during editing)

| Feature | Priority | Notes |
|---|---|---|
| Design Health HUD | v1 | **One always-visible, non-modal bottom-corner pill**: three dots (A11y / Perf / SEO), a page-weight bar, and a projected-LCP number from `PerformanceObserver`'s live LCP-candidate entry. Click to expand a grouped issue list. **Never a stream of interrupting toasts** |
| Live contrast checker | v1 | WCAG 2 + APCA inline on the selection. Pure two-colour arithmetic — free to run live |
| Touch-target size warning | v1 | Flags <24×24 CSS px unless a WCAG 2.5.8 exception applies |
| Overflow/clipping warning | v1 | ResizeObserver + `scrollWidth > clientWidth` |
| Broken-link scanner | v1 | |
| Missing-alt-text badge | v1 | Persistent counter, non-blocking |
| Scoped axe-core run | v1 | `axe.run(node)` on the touched subtree only after any placement/swap/text edit: color-contrast, image-alt, label, button-name, aria-required-attr, duplicate-id. Page-level rules deferred to lock |
| Focus-not-obscured heuristic | v1 | Bounding-box intersect any placed sticky/fixed element against all focusables. Approximates WCAG 2.4.11 |
| Reading-order-vs-visual-order heuristic | v1 | After a reorder or free-position, walk the tabbable list and flag non-monotonic DOM-vs-rect pairs |
| Reduced-motion sibling presence | v1 | Confirm the placed item's catalog includes a tagged reduced variant; auto-apply a generated fallback and flag if missing |
| Image auto-optimisation on drop | v1 | Any image >~200KB or larger than its render box auto-recompresses to WebP/AVIF + srcset with a **visible undoable confirmation** ("−82% size, visually identical — Undo"). **Not silent** |
| Focus-order overlay | v2 | Optional numbered tab-order overlay |
| Live page-weight indicator | v2 | Running total against a soft budget |
| Off-token / design-drift warning | v2 | Advisory, non-blocking — a human-in-the-loop tool warns rather than mechanically forbids |
| Motion-property lint | v2 | Flags non-compositor properties, out-of-band durations, missing reduced-motion query in Step-6 custom animations |
| Text-spacing stress clone check | v2 | Off-screen clone with the WCAG 1.4.12 override stylesheet, diffed for overflow |
| Responsive-breakage warning | v2 | Flags elements only ever checked at one breakpoint |
| Spell-check | v2 | |

### 10.7 Collaboration & regeneration

| Feature | Priority | Notes |
|---|---|---|
| Per-section notes → regeneration | v1 | **The human-authored replacement for the rejected VLM critique loop.** A plain-language note ("make this pop more") becomes a scoped regeneration instruction |
| Regenerate-this-section-only | v1 | Replaces in place. **Accuracy depends entirely on clean section boundaries** — design the two together |
| Collaboration-ready comment schema | v1 | Author, timestamp, thread id from day one. Costs almost nothing now; a schema rewrite later costs a lot |
| Canvas-anchored comment pins | v2 | |
| Human-readable change/activity log | v2 | Plain-language: what changed, when, via manual edit vs swap vs regeneration |
| Share-for-review read-only link | v2 | Non-editable preview URL before LOCK |
| **Custom code block** | v2 | **An opaque draggable container holding hand-written HTML/CSS/JS that the editor positions but never introspects. The signature moment is built here, outside the menu — this is where the quality ceiling actually lives** (§14.4) |

### 10.8 Preview & export

| Feature | Priority | Notes |
|---|---|---|
| In-editor Preview mode | v1 | All chrome hidden, still inside the editor shell. A lighter, reversible rehearsal distinct from LOCK |
| Interaction preview | v1 | Hover/click states live and testable |
| Motion preview toggle | v2 | Play / pause / prefers-reduced-motion, per container and globally (§9.6) |
| Reduced-motion preview | v1 | Verify motion-sensitive visitors get a **designed** experience, not a deleted one |
| Real-device LAN preview | v2 | QR code / local URL. **Prioritised earlier than a typical v2** because D2 makes responsive correctness a hard constraint and resized-browser preview cannot substitute for real DPR, touch-target feel, font rendering, and scroll physics |
| Device-frame preview | v3 | |
| Lock / Publish flow | v1 | §12.5 |
| Lock verification gates | v1 | Four automated gates (§12.5) |
| Responsive preflight report | v1 | One command renders 320/390/768/1280/1440 and reports overlap collisions, horizontal overflow, fixed heights on text blocks, free-position counts, blocks with no mobile plan. **Blocking before lock** |
| Long-string reflow fuzz | v1 | Injects a 40-char unbroken token into every text block at 320px; enforces `overflow-wrap: anywhere`; forbids fixed heights on text-containing blocks |
| Evidence bundle export | v1 | §15.6 |
| Design-system re-export | v2 | Export current tokens so a future hand-carry starts from the live state |
| Raw code export / eject | v3 | |
| Individual asset export | v3 | |

### 10.9 Command palette & onboarding

| Feature | Priority | Notes |
|---|---|---|
| Command palette (⌘K) | v2 | The standard escape valve for power without menu bloat, once the surface is ~95 features deep |
| Progressive disclosure via selection state | v1 | **The single most load-bearing anti-overwhelm mechanism across every mature editor.** The inspector is empty until something is selected, then shows only type-relevant properties |
| First-run anchor-model walkthrough | v1 | **The highest-value teaching moment is the anchor concept, not a toolbar tour.** Anchoring has no equivalent in Canva or PowerPoint, both of which are free-drag. A short guided "drag this, watch it snap and pin" |
| Inspector panel (token-only) | v1 | **All non-geometric properties as selects over the design system's scales.** No free-text numerics, no colour picker. The lint wall expressed as UI — an off-token value must be **unreachable**, not merely flagged |

---

## 11. Layout and dragging model (D2, settled)

### 11.1 The four-level layout contract (normative)

1. **Page** = a vertical list of sections. Reorder-only.
2. **Section** = a real CSS Grid — 12/6/4 tracks with `fr` units.
3. **Block** = integer `grid-column` / `grid-row` placement, per breakpoint.
4. **Inside a block** = flow only (hug / fill / fixed). Never coordinates.

This is Figma's model expressed in CSS, and it gives the best freedom-to-safety ratio of anything surveyed. Figma is explicit that its two positioning systems do not mix: constraints (Left / Right / Left-and-Right / Center / Scale) apply **only** to children of plain frames — *"It's not possible to apply constraints to layers … in an auto layout frame."* Inside auto layout you get direction, wrap, gap, padding, alignment, and per-child Hug/Fill/Fixed with min/max. The escape hatch is a single per-child toggle, **"Ignore auto layout,"** which removes that one child from flow, keeps it inside the parent, and hands it back the constraint system. **[V — help.figma.com, both articles fetched, quote verbatim]** Framer copied the same shape.

### 11.2 The grid overlay must BE the grid

Draw the overlay by reading `getComputedStyle(section).gridTemplateColumns` — the browser resolves `fr` → px for you — and render those exact tracks. **Never a hand-authored decorative grid.**

Drag then becomes integer rounding:

```
col = clamp(1, round((x − gridLeft) / (colWidth + gap)) + 1, cols + 1)
```

and the persisted value is `grid-column: 3 / span 6`, which is **inherently fluid** (6-of-12 is 50% at every width). This single choice makes Step-4 dragging and Step-7 export the same data.

Wix Studio validates the approach: it ships a real advanced CSS grid with arbitrary row/column counts, units `fr` / `%` / `px` / `vw-vh` / `auto` / `minmax()` / `calc()`, placement by clicking a cell or typing column+row numbers, and explicit multi-cell spanning **[V — support.wix.com, fetched]**. Squarespace Fluid Engine is a 24-col desktop / 8-col mobile CSS grid **[V]**.

### 11.3 Breakpoint cascade: desktop-down, one direction

| Builder | Model | Outcome |
|---|---|---|
| Webflow | Base = Desktop 1280; tablet ≤991, mobile-landscape ≤767, mobile-portrait ≤479. Styles inherit downward; a smaller-breakpoint override permanently detaches that property | Works, with documented cascade confusion |
| Wix Studio | *"changes you make on larger breakpoints trickle down to smaller breakpoints, but changes on smaller breakpoints don't affect larger"* | Works |
| Framer | *"Changes made at a smaller breakpoint only affect that breakpoint and below"* | Works |
| **Squarespace Fluid Engine** | **Separate grid for mobile with independent block placement** | **Documented overlap epidemic**: *"Separate text boxes can easily end up overlapping on narrower screens, creating a real mess of unreadable letters"*; blocks *"mix-up or change order and position"*; Squarespace experts publicly campaigned for fixes |

**[V — all four, fetched from help.webflow.com, support.wix.com, framer.com/academy, engineering.squarespace.com + practitioner write-ups]**

**Verdict: desktop-down cascade with sparse per-breakpoint overrides. Never two independent layouts.**

Because the cascade is a documented beginner confusion source, the UI must make the current breakpoint **structurally prominent** — a persistent chrome element, not a dropdown the user can forget they set — and must show a **pre-commit chip** stating exactly which sizes an edit will affect, with a one-click "apply to all sizes instead."

Blocks with **no** small-breakpoint override compile to `grid-column: 1 / -1` in source order. That default alone prevents Squarespace's signature failure.

### 11.4 The free-position escape hatch

Practitioner documentation is blunt about the cost. Framer University: *"Your element won't adjust when the screen resizes. What looked perfect on desktop suddenly overlaps or disappears on mobile"*; Framer *"stops treating that element as part of the stack"*; *"Spacing gets weird. Alignments break. Responsiveness? Gone"*; and animations desync because *"elements no longer share the same reference points"* — which matters directly under D4. GrapesJS is equally explicit that its absolute mode is *"ideal for fixed-layout designs like documents for print, business cards, certificates, or static prototypes where responsiveness isn't required."* **[V — framer.university, app.grapesjs.com, quotes verbatim]**

The mechanics of naive absolute positioning: (1) the element leaves flow, so an auto-height parent collapses and the next section slides up under it; (2) `left: 812px` was measured in a 1512px editor viewport, so at 390px it sits 422px off-screen, creating body `overflow-x` or invisible clipping; (3) at 2560px it floats in dead space. Then the user does it fourteen more times and the site is a 1512px fixed canvas wearing a responsive costume.

**Design rules:**

1. **Not raw absolute.** Implement as **anchored-offset**: the element keeps a declared anchor (parent edge, sibling, or grid cell) and the free drag writes a **percentage / `clamp()` offset from that anchor**, so it scales.
2. The parent gets a reserved `min-block-size` at drop time so it cannot collapse.
3. Per-block **and** per-breakpoint.
4. **Auto-demotes to normal flow at ≤479px** unless the user explicitly opts in there too.
5. **Lint caps free-positioned blocks per section** (~2), with a visible counter ("4 elements are free-positioned").
6. **Hard LOCK gate**: render at 390/768/1440 and refuse to lock if any free-positioned element produces document `overflow-x` or leaves its parent's box.
7. Disabled by default for pinned/scrubbed sequence containers (§9.4).

**Honest caveat:** anchored-offset still fails for art whose composition depends on absolute relationships across the whole viewport (a scattered constellation of sprites). For that case the only answer is to treat the whole composition as **one component with its own internal responsive rules** — which means the user cannot drag its parts individually, which is exactly what they asked for. There is no better answer.

### 11.5 Container queries, not viewport media queries, inside components

Step 4(d) lets the user swap a component for a variant, and 4(b) lets them move it between slots of different widths. If component internals key off `@media`, a card that looks right in a 6-col slot breaks the moment it is dragged into a 3-col slot — an unbounded matrix of manual fixes.

**Put `container-type: inline-size` on every block wrapper and write component internals with `@container`.** A component then adapts to *the space it was dropped into*, which is the only sane contract for drag-and-swap.

Platform status as of 2026: container queries, `:has()`, `@property`, cascade layers, nesting, and logical properties are all **Baseline Widely Available**. Subgrid is universally supported (Chrome 117+, Firefox 71+, Safari 16+) and is the right tool for aligning a nested component's internals to the parent section's tracks. **Anchor positioning is still a carryover Interop 2026 item — use it only for editor chrome and progressive-enhancement decoration, never load-bearing layout.** **[V — web.dev/blog/interop-2026, webkit.org]**

### 11.6 grid-template-areas and integer placement, together

Named areas are the most readable and most mobile-safe form — the entire mobile layout of a section is one property rewrite. Their hard limit is that every area must be a **contiguous rectangle**, so they cannot express arbitrary drag results (an L-shape, or two blocks in one cell).

**Resolution:** the design system ships ~12 section archetypes as `grid-template-areas` per direction. The moment a user drags a block off its area, **that block only** is promoted to explicit `grid-column`/`grid-row` integers on the same grid. Both compile to identical CSS Grid, so export is unaffected and the archetype stays readable for every untouched block.

### 11.7 Preview must be a same-origin iframe

A scaled `<div>` cannot evaluate media queries against the simulated width; an iframe can, because the iframe's own viewport is what `@media` sees.

Puck ships exactly this: viewports as `{width, height: 'auto'|number, label, icon}`, defaults Small 360 / Medium 768 / Large 1280 / Full-width, *"rendered in a same-origin iframe that can be resized to simulate different viewports"* **[V — puckeditor.com/docs/integrating-puck/viewports, fetched]**.

**The trap:** all four Puck defaults use `height: 'auto'`, so any hero using `100vh`/`svh`/`dvh` measures the iframe's expanded height, not a phone's. Hero framing looks right in the editor and wrong on device. **Fix: pin device heights (390×844, 768×1024, 1280×800, 1440×900) whenever the page contains a viewport-height rule.** Also note that when Puck's compositional `<Puck.Preview />` is used directly, the viewports API has no effect at all.

### 11.8 Failure-mode catalogue — all twelve mechanically detectable

| # | Failure | Detector |
|---|---|---|
| 1 | Small-screen overlap (Squarespace's signature failure) | Per-breakpoint rectangle-intersection over resolved grid areas; default any block with no sm override to `1 / -1` |
| 2 | Horizontal overflow | Assert `documentElement.scrollWidth <= clientWidth` at 320/390/768/1280/1440 |
| 3 | Text reflow blowout | Fuzz every text block with a 40-char unbroken token at 320px; require `overflow-wrap: anywhere`; forbid fixed heights on text blocks |
| 4 | Z-order confusion | Z-order is an integer paint list per section in `layout.json`, compiled to `z-index` only where needed, with each section establishing a stacking context (`isolation: isolate`) so nothing leaks across sections |
| 5 | Nested scroll containers | Forbid `overflow: auto` inside blocks except one explicit "scroller" component |
| 6 | Absolute drift | Cap free-positioned blocks per section; auto-demote at sm |
| 7 | Unclickable / ghost elements | The Navigator tree is the guaranteed selection path |
| 8 | Zoom-broken snapping | Tolerance ÷ zoom |
| 9 | 100vh lying in the editor | Pin iframe device heights |
| 10 | Font-load measurement drift | `await document.fonts.ready` before **any** `getBoundingClientRect` in editor or capture |
| 11 | Split undo stacks | A single command stack over `layout.json` patches |
| 12 | Drag pointer leaving the iframe | `setPointerCapture` on the overlay; translate coordinates by the iframe rect rather than listening inside |

### 11.9 Zero DOM injection (architectural constraint, not a note)

The natural implementation of drag is to wrap each component in a `<div data-wb-id>` for hit-testing. **Do not.** Those wrappers get removed at LOCK, and the site uses `.grid > *` for auto-placement, `:first-child` for the hero's top margin, and flex `gap` between direct children. With wrappers the direct children were the wrappers; without them they are the components. Every one of those selectors now matches different elements. The locked site's spacing differs from the design surface by 8px here and a whole grid column there, **and there is no way to explain it to the user because "nothing changed."**

**Constraint:** hit-testing uses `data-wb-node` attributes on elements that **already exist**, plus a **single sibling overlay `<div>` outside the page's layout root**, positioned with `getBoundingClientRect()` + `ResizeObserver`. Handles, selection rings, snap guides and gridlines all live in that overlay. LOCK then removes exactly one element and one `<script>`, and **provably cannot move anything**.

**Corollary for Step 7's "gridlines removed":** the gridlines must visualise a **real CSS Grid** on the page (with named lines). If the grid is only an overlay and snapped positions are baked as margins, removing it is fine — but then "components snap to gridlines" (D2) is decoration, and changing the grid later reflows nothing. **Pick real-grid, and make removal a no-op by construction.**

---

## 12. Document model, persistence, and the LOCK/UNLOCK contract

### 12.1 Two-tier truth (the highest-leverage architectural decision in the PRD)

| Tier | What | Owner | Notes |
|---|---|---|---|
| **Composition** | Which component, which variant, order, slot, anchor, prop values, text | `pages/<id>.doc.json` (+ `content.json`) — **the only thing the editor mutates** | A scene graph |
| **Implementation** | `.astro` component sources, `tokens.json` (DTCG) + compiled `tokens.css`/Tailwind `@theme`, art assets | Real files on disk, versioned, arriving from the Step-3 hand-carry | Claude edits these |
| **Rendered site** | `.astro` page files under `src/generated/**` | Produced by a pure function `render(doc, systemLock, library) -> files` | **Never parsed back into JSON** |

**Rejecting HTML→JSON round-tripping is what makes drift structurally impossible rather than merely managed.** Every product that reconstructs a doc from rendered markup is lossy at exactly the places that matter — anchors, variants, intent. This is also the canonical WYSIWYG failure (Dreamweaver design view, FrontPage, Muse): the editor parses source into a DOM, the user edits, the editor re-serialises, and comments vanish, formatting normalises, hand-tuned CSS is rewritten. **Worse here, because Claude is also writing this source** — the next read sees reformatted markup it did not write, with its own comments gone, and diffs become unreviewable.

It also makes D1 cheap: swapping a variant is a single JSON field change, and "10 more variants" is a library operation, not a page rewrite.

**Prior art split.** Family A (JSON doc + pure render): Puck `{content[], root, zones}`, Craft.js, Builder.io. Family B (files-as-truth + annotation mapping): TinaCMS, Netlify/Stackbit Visual Editor, Onlook. **Anti-patterns:** Webflow export drops CMS collections, forms, site search, password protection and localisation — collection lists render empty, template pages don't generate. Framer ships no HTML export at all. Both are one-way doors, and D3 requires reversibility. **[V — puckeditor.com, builder.io, docs.netlify.com, tina.io, github.com/onlook-dev/onlook; Webflow gaps from brixtemplates/memberstack/thecssagency analyses, consistent across sources]**

### 12.2 The file set

| File | Purpose |
|---|---|
| `site.json` | Project record: formatVersion, projectId (ULID), breakpoints, grid, page list, and `systemLock {directionId, systemVersion, tokensSha256, librarySha256, source, importedAt}`. **The systemLock is what makes a re-run of Step 3 unable to silently change what a page renders** |
| `pages/<id>.doc.json` | The scene graph. Node: `{id, component, variant, region, layout, props, slots, text, override, locked, notes}`. **Serialised with stable key order, 2-space indent, one array element per line** — that formatting decision alone determines whether the git history is useful |
| `content.json` | Copy, separated so a content-only edit path exists |
| `history.jsonl` | Append-only op log: `{seq, ts, actor: 'user'\|'agent', op, target, patch: [RFC6902], inverse: [RFC6902], label}` |
| `system.lock.json` | Pins the imported direction like a package-lock: id, version, per-file hashes of tokens and every component |
| `assets/manifest.json` | Per-asset provenance and licence. **Also the allowlist the generator validates every asset reference against**, closing the hallucinated-URL class |
| `provenance.json` | Per component instance: direction id, variant id, generation timestamp, prompt hash |
| `inbound/import-report.json` | Per-item accept/reject/quarantine with reason and offending snippet |
| `.wb/inbox.jsonl` | Append-only agent intent channel |
| `.wb/editor.lock` | Single-writer pid + mtime heartbeat |
| `.wb/editor.token` | Per-session bearer token, mode 0600 |
| `lock-manifest.json` | Written at LOCK; records the layout hash so unlock can diff against hand-edits |

### 12.3 The layout node — where D2 lives

```json
{
  "id": "n_hero_art",
  "component": "ArtContainer",
  "variant": "background-scene@07",
  "layout": {
    "default": { "mode": "flow", "col": { "start": 1, "span": 12 },
                 "align": "stretch", "spaceBefore": "space-l", "spaceAfter": "space-xl" },
    "lg":      { "col": { "start": 2, "span": 10 } }
  },
  "props": { "motion": "entrance.mask-wipe@03", "aspect": "16:9",
             "focalPoint": { "x": 0.5, "y": 0.4 } },
  "text": {}, "slots": {}, "locked": false
}
```

Free-position escape hatch: `{ "mode": "free", "anchor": { "to": "parent"|nodeId, "edge": "top-left" }, "offset": { "x": "12%", "y": "clamp(1rem, 4vw, 3rem)" }, "z": 2 }`.

Per D4, **motion is not a separate structure** — an animated piece is an `ArtContainer` node whose `props.motion` is a token/preset id, manipulated identically to a static art container.

Borrow Puck's proven conventions: a `root` node with its own props, **named slots rather than the deprecated `zones` string-key hack** (`"HeadingBlock-1234:my-content"` — Puck deprecated exactly this in favour of slot fields, so start where they ended up), and ids that encode component type for debuggability.

### 12.4 DOM ↔ doc mapping

Copy Stackbit's annotation scheme **including its scoping rule**. Netlify Visual Editor's annotations are *"HTML data attributes … so that the visual editor can map content in the preview to the correct document and field"*; `data-sb-object-id` identifies the document *"along with all descendants of that element in the DOM tree"*; `data-sb-field-path` gives the path to the field. **Scoping-by-descent is the important detail** — annotate once at the node boundary and inherit. **[V — docs.netlify.com, quotes verbatim]**

Our attributes: `data-wb-node` (scopes descendants), `data-wb-field` (marks inline-editable), `data-wb-slot` (drop region), `data-wb-variant` (what the component bar reads), `data-wb-layout` / `data-wb-anchor` (what the drag handler reads). **All emitted only under `import.meta.env.WB_DESIGN`; all asserted absent from `dist/published`.**

Astro gives DOM→source-file mapping for free: it injects `data-astro-source-file` and `data-astro-source-loc` in development only (a filed issue confirms they appear in dev even when `devToolbar` is disabled — gated on dev, not on the toolbar). **[V — withastro/astro issue #9324; astro-click-to-source integration]** So no Babel instrumentation is needed.

### 12.5 The LOCK/UNLOCK contract (D3, settled)

**LOCK is a re-render, never a copy-and-strip.** Same renderer, `editor: false`. The FruitSync precedent proves what copy-and-strip costs: the release required rewriting every `/a01/` link to `/` and manually excluding the dev variant-chooser and four dev mockup pages from the shipped folder **[V — DEPLOY-STEPS.md]** — which is exactly the leakage D3 exists to prevent.

**Five layered enforcement mechanisms, four of them documented Astro/Vite features:**

1. **Two configs, two commands, two outDirs.** `astro dev --config astro.design.mjs` vs `astro build --config astro.publish.mjs --outDir dist/published`. **Only the design config registers the editor integration**, so the editor is not in the publish build graph at all.
2. **`astro:config:setup` receives `command: 'dev'|'build'|'preview'|'sync'` and `injectScript(stage, content)`.** Gating on `command === 'dev'` is the documented dev-only injection pattern.
3. **`addDevToolbarApp(entrypoint)`** for editor chrome. Astro's docs state the toolbar *"is a development tool only and will not appear on your published site"* — which makes the component bar, grid toggle and save button a class of UI that **physically cannot leak**.
4. **`import.meta.env.WB_DESIGN` guards** for anything inside a component. Vite statically replaces `import.meta.env.*` at build time so the dead branch is eliminated — **but the gotcha is real and filed (vite#15256): if the variable is undefined the branch may NOT be shaken.** `WB_DESIGN` must be explicitly defined as `false` in the publish config's `vite.define`.
5. **`astro:build:done`** receives `dir` (URL), `pages` (`{pathname}[]`) and `assets` (`Map<string, URL[]>`) — enough to post-scrub every emitted HTML file and then assert.

**[V — docs.astro.build integrations reference + dev-toolbar guide, direct quote; vite.dev env-and-mode; vitejs/vite #15256]**

**The gate is an executable assertion, not a claim.** `wb lock` = build → scrub → assert → snapshot:

| Gate | Check |
|---|---|
| 1 | Grep `dist/published/**` for `data-wb-`, `wb-editor`, `astro-dev-toolbar`, `data-astro-source-file`, `data-astro-source-loc`, `/@vite/client`, `import.meta.hot`, the editor token filename. **Any hit fails the build** |
| 2 | **Byte-equality**: build the same doc twice — once with the editor integration installed, once with it removed from `package.json` entirely — and require the two trees to be byte-identical. **This converts "the editor doesn't ship" from an intention into a CI fact** |
| 3 | `dist` JS byte-size assertion (an accidental editor import shows up as a step change) |
| 4 | Screenshot diff between editor-preview-at-1280 (chrome hidden) and built-page-at-1280 — proves LOCK changed nothing visual, and catches the residual case where a `data-wb-*` attribute participated in a CSS selector or affected intrinsic size |
| 5 | **Interaction-manifest check**: walk every declared motion/interaction behaviour against `dist/published` to prove it exists in shipped code. This is the Webflow-export lesson applied to a static target — no behaviour may exist only as editor state |

**LOCK is non-mutating.** It writes only `dist/published/` and `.wb/locks/<iso>/` (an immutable snapshot: every `*.doc.json`, `system.lock.json`, the dist hash, the scrub output, `lock-manifest.json`), then `git tag wb-lock/<n>`. **The editable project is untouched, so UNLOCK is nothing more than restarting the design server — there is no unlock transformation to get wrong.**

Going back to an older lock is `git checkout wb-lock/<n> -- pages/ site.json` (documents only, never `dist/`), which cannot lose manual code because manual code lives in human-owned zones the checkout does not target.

### 12.6 State-loss ledger (what LOCK/UNLOCK must explicitly handle)

| # | Lost / breaks | Handling |
|---|---|---|
| 1 | Undo/redo history (in-memory) | Persist as a capped operation log alongside `layout.json`; every save is a git commit so cross-session undo has an answer |
| 2 | Selection and scroll position | Persist in `.wb/session-ui.json` |
| 3 | Per-breakpoint override provenance if flattened into final CSS | LOCK is a re-render from the doc, so provenance lives in the doc and is never flattened away |
| 4 | Free-position pixel baselines (the viewport they were authored at) | Anchored-offset stores percentages, so there is no pixel baseline to lose |
| 5 | Placeholder flags on unfilled slots | Placeholders are a **typed state that blocks LOCK** |
| 6 | Hand-edits to the exported tree, silently overwritten on unlock | `lock-manifest.json` records the layout hash; unlock **diffs the exported tree and shows hand-edits** instead of discarding them |
| 7 | Editor scaffolding leaking into the shipped site | Killed by re-render + the five gates |
| 8 | Rich text pasted with `<span style=…>` and `<b>` from the source app | `contenteditable="plaintext-only"`; content stored as plain strings |
| 9 | Absolute `http://localhost:4321/...` URLs baked at design time | Post-ingest and pre-lint pass strips absolute local URLs |

### 12.7 Ownership zones and conflict handling

Copy Plasmic's owned/managed split verbatim. Plasmic emits two files per component: `plasmic/PlasmicButton.tsx` is *"owned by Plasmic, and shouldn't be edited by you. As you iterate … these files will be updated when you run plasmic sync"*; `Button.tsx` is the wrapper, for which Plasmic *"generates an initial scaffold"* and *"never touches it again."* **[V — docs.plasmic.app/learn/codegen-components, direct quotes]** This is the mechanism that makes a codegen product a tool rather than a toy.

| Zone | Paths | Writer |
|---|---|---|
| **Machine-owned** (regenerated wholesale) | `src/generated/**`, `src/styles/tokens.css` | The generator only |
| **Human/agent-owned** (never written after scaffold) | `src/pages/*.astro` thin wrappers, `src/overrides/**`, `src/lib/**` | Claude and the user |
| **Doc-owned** | `pages/*.doc.json`, `content.json`, `history.jsonl`, `site.json` | The editor process only |

**Enforcement:** `.gitattributes` marks `src/generated/** linguist-generated=true -diff` (GitHub collapses those diffs; `-diff` also hides them from the CLI) **[V — github/linguist behaviour]**; a pre-commit hook rejects a commit touching `src/generated/**` without a corresponding doc change; the generated banner names the file to edit instead; **a PreToolUse hook blocks Claude's `Write`/`Edit` on editor-owned files.

**When an illegal edit happens anyway, do not attempt a three-way merge.** Run `wb extract-override <nodeId>`, which lifts the current generated fragment into `src/overrides/<nodeId>.astro`, sets `node.override` in the doc, and re-points the generator to emit `<Override/>`. That turns an illegal edit into a legal, permanently-surviving one. This is Plasmic's split applied at node granularity.

**Overrides accumulate, and that is a real cost.** Each `src/overrides/<nodeId>.astro` is a piece of the page that no longer responds to variant swaps or token changes, so a heavily-overridden page quietly stops being a design-system site. The editor shows a visible override count and `wb doctor` warns above a threshold.

### 12.8 Determinism and drift control

Generation must be a **pure function of `(doc, system.lock.json, generator version)`**. Every generated file carries a header banner with `@generated`, `doc-sha256`, `system-lock-sha256`, `generator-version` — and **no timestamp** (a timestamp in the file body destroys determinism and pollutes every diff; put run metadata in a sidecar).

Two checks fall out:

- `wb verify` regenerates into a temp dir and `diff -r`s against `src/generated/**`. **Empty diff proves both determinism and that nobody hand-edited machine-owned files.** Run on editor start, before LOCK, and in CI.
- On editor start, a hash mismatch means someone hand-edited generated output.

**Determinism hazards to design out up front:** map/object iteration order (sort keys), absolute paths in output (relative only), locale-dependent sorting (fixed collator), random ids (derive node ids from a ULID stored in the doc, never regenerate).

**This is the load-bearing assumption of the whole drift story.** Any nondeterminism makes `wb verify` produce false positives, users learn to ignore it, and the guarantee silently dies.

### 12.9 History: op log + snapshots + git, and NOT a CRDT

Three layers with distinct jobs:

| Layer | Mechanism | Job |
|---|---|---|
| **a** | `history.jsonl`, append-only, one line per user action with `patch` and `inverse` as RFC 6902 JSON Patch | Undo = apply `inverse`; redo = apply `patch`. Plain diffable text; doubles as the agent-vs-human audit trail |
| **b** | Atomic doc writes — write temp then `fs.rename`, debounced ~300ms | A `kill -9` leaves either the pre-op or post-op file, never a truncated one |
| **c** | Git commits at **milestones only** (LOCK, variant-set import, named checkpoint, session end), `git tag wb-lock/<n>` per lock | Durability, and history stays readable |

**Reject CRDTs (Yjs, Automerge, Loro).** There is one human plus a sequential agent; concurrent multi-writer merge buys nothing and costs an opaque binary doc git cannot diff. Use a single-writer `.wb/editor.lock` (pid + mtime heartbeat) and route agent writes through the inbox instead.

### 12.10 Two writers, one lock

**Failure scenario, near-certain:** the editor is open with unsaved drags in memory. The user, in the terminal, asks Claude "make the features section tighter." Claude rewrites the section and, if it touches layout, writes `layout.json`. The browser holds stale state; the user hits Save; the browser clobbers Claude's change — or Claude clobbers the drags on the next reload. **Either way the loser's work vanishes silently.**

| Mitigation | Mechanism |
|---|---|
| **Single writer by file ownership** | §12.7, enforced by a PreToolUse hook |
| **Optimistic concurrency** | Every save carries the mtime/hash the client loaded; the server rejects a stale write with **409** and the editor shows "the file changed on disk — reload or force" |
| **Every save is a commit** | Auto-commit `layout.json` on save to a `design/` branch, squash on lock, so "undo the last thing" has a real answer across sessions |
| **Agent inbox** | Agents append intents to `.wb/inbox.jsonl`; the editor process is the single writer that validates, applies, appends to `history.jsonl` with `actor: 'agent'`, and pushes over SSE. Same typed ops as the UI, so **one code path for both** |

The FruitSync precedent gives no help here: that site tree is not under version control at all (`fatal: not a git repository`) **[V]**, so there is no rollback of any kind today. **`git init` at Step 0, no exceptions.**

### 12.11 Session state on disk

```
.acos/website-builder/sessions/WB-<ts>-<slug>/
  00-interview/{answers.json, concept.md}
  01-prompt/{stage-a.md, stage-b-<id>.md, artwork.md}
  02-system/{<directionId>/…, manifest.json, import-report.json, system.lock.json}
  03-selection/{tournament-log.json, picks.json}
  04-site/{site.json, pages/*.doc.json, content.json, provenance.json, assets/manifest.json}
  05-variants/
  06-custom/
  07-lock/{dist/, lock-manifest.json, gate-report.json, screenshots/}
  evidence/
  audit/config-snapshot.yaml
  state.json      ← {phase, step, awaiting, nextAction, port, pid, url, sessionId}
  events.jsonl
  ACTIVE          ← marker written at init, removed at close
.acos/website-builder/systems/<name>/{system.json, tokens.css, compliance-report.json, provenance}
.acos/website-builder/sessions/*/site/   ← in ACOS .gitignore, its own nested git repo
```

**The phase frontier is recomputed from which directories are populated and which gates passed — never from conversation memory.** The principle is stated best in the in-repo `acos-axiom-synthesis/STATE-MACHINE.md`: frontier is *"Computed purely from on-disk state, so the run is resumable by re-reading the ledger."* **[V — in-repo, line 66]** The `.current-session` pointer convention already exists at `.acos/sessions/loan-doc-finder/.current-session` **[V — verified by `ls`]**.

**`site/` must be its own git repo (or worktree), and the path must be in the ACOS `.gitignore`** — otherwise every drag operation pollutes ACOS history and every LOCK tag collides with ACOS tags, making the version-history layer unusable within a single session.

### 12.12 Local server security — localhost is NOT a trust boundary

This is the single most under-rated risk in the product.

**CVE-2025-24010 (Vite):** *"Vite allowed any websites to send any requests to the development server and read the response due to default CORS settings and lack of validation on the Origin header for WebSocket connections,"* and the advisory states explicitly that it *"applies to users that only run the Vite dev server on the local machine and does not expose the dev server to the network."* Fixed in 6.0.9 / 5.4.12 / 4.5.6. Separately, **CVE-2025-30208** let `?raw??` bypass `server.fs.deny` for arbitrary file read (that one only affected `--host`-exposed servers — which is why ours never is). Vite's own docs warn that `server.allowedHosts: true` *"allows any website to send requests to your dev server through DNS rebinding attacks, allowing them to download your source code and content."* **[V — GHSA-vg6x-rcgg-rjx6, GHSA-x574-m823-4x7w, vite.dev/config/server-options, quotes verbatim]**

**Required posture:**

| # | Control |
|---|---|
| 1 | Bind `127.0.0.1` explicitly, **never** `0.0.0.0` |
| 2 | Validate `Origin` on **every non-GET and on the SSE/WS upgrade** against a two-entry allowlist |
| 3 | `Access-Control-Allow-Origin` set to the exact editor origin, **never `*`** |
| 4 | **A per-session bearer token** — 32 random bytes, `.wb/editor.token` mode 0600, injected into the editor page at render, sent as `Authorization`. **This is what actually defeats DNS rebinding and drive-by CSRF** |
| 5 | Pin `vite.server.allowedHosts` to the explicit host; pin Vite ≥ 6.2.3 |
| 6 | Heartbeat from the editor page; exit after N idle minutes — **a forgotten dev server left running for days is the realistic exposure, not a targeted attack** |

**In-repo gap to not copy:** `ic-server.py` binds `127.0.0.1` correctly but performs **no Origin check on `do_POST`** **[V — grep, lines 107/156/187]**.

### 12.13 The write endpoint is an arbitrary-file-write primitive unless constrained

Two rules make it safe by construction:

1. **The client never sends a file path or a file body.** It sends a **typed semantic op** (`{op: 'swap-variant', node: 'n_hero', variant: 'hero-split@3'}`) and the server derives the JSON Patch. **Raw-JSON-Patch-over-HTTP is nearly as dangerous as raw paths** because `add`/`replace` on an arbitrary pointer can rewrite `systemLock` or inject an `override` path. Validate every op against a schema **and** against the component library before applying.
2. **The server may write exactly three path shapes** — `pages/*.doc.json`, `history.jsonl`, `.wb/**` — resolved with `realpath`, asserted `startsWith(sessionRoot)`, symlinks rejected. Everything else (generated files, dist) is written by the generator process from the doc, not by an HTTP handler.

### 12.14 The Step-3 importer is an unauthenticated code-import channel

Pasting component code and tokens back from claude.ai means arbitrary code lands in `src/`, is evaluated by `astro dev`, and is bundled into the published site. Treat it as untrusted input.

A forgiving parser (fenced-block extraction, per-item) feeds a strict validator that **rejects or quarantines** any item containing `fetch(`, `eval(`, `new Function`, `import(` of non-local specifiers, `process.`, `child_process`, remote `<script src>`, remote `@import`/`url()` in CSS, or inline event handlers; plus a schema check that `tokens.json` is valid DTCG.

Two secondary reasons this matters beyond security: **(a)** partial or malformed paste-backs will happen on most runs, and a hard-failing importer stalls the pipeline at paste #1, so per-item accept/reject with a "retry just these three" prompt is a **functional requirement**; **(b)** remote font/asset URLs sneaking in breaks offline determinism and the Step-8 licence evidence bundle.

### 12.15 The File System Access API is not a viable persistence path

`showDirectoryPicker()` requires a secure context (localhost qualifies) and a user gesture, but **Safari ships only the Origin Private File System (no directory picker) and Mozilla published a "harmful" position**; the documented Firefox fallback is `<input type="file">` for reads and `<a download>` for writes. A browser-writes-to-disk design would silently be Chrome-only and would still need a server fallback. **[V — MDN showDirectoryPicker, developer.chrome.com, WICG spec]** Keep it as an optional convenience (e.g. "export lock bundle to a folder"); the local server is the single persistence path.

---

## 13. Quality gates

### 13.1 The dividing line

Not "a11y vs performance" but **scoped arithmetic/DOM-read vs whole-document render pass**.

- **LIVE** (sub-100ms, fires on drop/mouseup — **never mid-drag, never per-frame** — scoped to the touched subtree)
- **LOCK-TIME** (seconds to tens of seconds, whole-document, batch)

`axe.run(context)` supports scoped runs natively **[V]**; Lighthouse's throttled multi-second run cannot happen per-frame **[V]**.

### 13.2 Two WCAG criteria apply to the EDITOR ITSELF — the most product-specific accessibility fact in this PRD

**WCAG 2.2 SC 2.5.7 Dragging Movements (AA, new in 2.2):** *"All functionality that uses a dragging movement for operation can be achieved by a single pointer without dragging, unless dragging is essential."* **[V — w3.org/WAI/WCAG22/Understanding/dragging-movements.html]**

The entire Step-4 design surface **is** a dragging interface. If the only way to move a component, resize it, or reorder it is a mouse drag, **the editor itself fails AA.** The fix is concrete and cheap, and it's already in the v1 feature list: select-then-click-destination, arrow-key nudge over grid cells, `+`/`−` span steppers, and — per D2's anchor model — a "move to: left of X / above Y" menu. This is a requirement for the editor's **own** UI, separate from what the published site does.

**WCAG 2.2 SC 2.5.8 Target Size (AA):** 24×24 CSS px minimum, with four exceptions (Spacing, Equivalent, Inline, Essential). Award-style editor chrome — thin drag handles, tiny corner resize grips, dense component-bar icon rows — violates this by default. **Every editor-chrome element needs a live bounding-rect check on render, not just at lock.**

### 13.3 Live checks (in-browser, scoped)

| Check | What |
|---|---|
| Contrast recompute | WCAG 2 relative-luminance ratio (4.5:1 normal, 3:1 large, 3:1 UI) **and** APCA Lc on every touched pair. Pure arithmetic on two colours — no DOM walk, no network |
| Target size | `getBoundingClientRect()` on every interactive element touched by a drag/resize; flag <24×24 unless an exception applies |
| Scoped axe-core | color-contrast, image-alt, label, button-name, aria-required-attr, duplicate-id on the touched subtree only |
| Overflow / clipping | ResizeObserver + `scrollWidth > clientWidth` |
| Focus-not-obscured | Bounding-box intersect newly-placed sticky/fixed elements against all focusables (SC 2.4.11) |
| Reading-order vs visual-order | Walk the tabbable list, flag non-monotonic DOM-vs-rect pairs (heuristic proxy for SC 2.4.3) |
| Reduced-motion sibling presence | Confirm the item's catalog has a tagged reduced variant; auto-apply a generated fallback and flag |
| Alt-text / decorative gate | **Blocks the placement**, not just the lock |
| Motion-property lint | Non-compositor properties, out-of-band durations, missing reduced-motion query (v2) |
| Text-spacing stress clone | WCAG 1.4.12 override stylesheet on a scoped off-screen clone (v2) |
| Image auto-optimisation | On drop, with a visible undoable confirmation |
| Budget HUD | Page weight vs budget; projected LCP from `PerformanceObserver`'s live LCP-candidate entry |

### 13.4 The ordered lock-time checklist

Ordering follows cheapest-and-most-foundational-first: the build must succeed before anything downstream is meaningful; deterministic gates before anything requiring a render pass.

| # | Gate | Threshold / pass condition |
|---|---|---|
| 1 | Build/export succeeds | Zero errors |
| 2 | `wb verify` — regenerate to temp, `diff -r` | Empty diff |
| 3 | Token/CSS lint (`stylelint-declaration-strict-value` + raw hex/px grep) | Zero raw values outside the token system |
| 4 | Six coherence lints (§7.12) | All pass; lint 6 (border-only ⇒ zero shadow tokens) is the one that catches human-visible incoherence |
| 5 | Full-page axe-core sweep (adds landmark-unique, region, heading-order, doc-wide duplicate-id) | **Zero critical/serious** |
| 6 | Pa11y cross-check (HTML_CodeSniffer WCAG2AA) | Second ruleset; raises coverage without claiming completeness |
| 7 | WCAG 2 + APCA contrast sweep, text **and** non-text (1.4.3, 1.4.11) | 4.5:1 / 3:1 / 3:1; APCA Lc75 body, Lc60 large-bold, Lc45 large-non-text ⁵ |
| 8 | Target-size sweep on published-site controls (2.5.8) | 24×24 CSS px, exceptions applied |
| 9 | Dragging-alternative audit for widgets built via Step 6 (2.5.7) | Every drag affordance has a documented single-pointer alternative |
| 10 | Reflow at 320 CSS px (1.4.10) + text-spacing stress (1.4.12) | No 2D scroll except exempted content (data tables, images, toolbars, maps). **Free-positioned elements get mandatory extra scrutiny** |
| 11 | Free-position breakpoint audit | Re-project at 320/390/768/1440; auto-demote anything with no narrow-viewport position; **refuse to lock on document `overflow-x` or parent-box escape** |
| 12 | Playwright keyboard tab-walk (2.4.3, 2.4.7, 2.4.11) | Focus order matches visual order; no traps; ring visible at every stop (≥3:1 against adjacent, non-zero outline); nothing obscured |
| 13 | Reduced-motion render diff | **Must differ where motion exists AND still look designed** |
| 14 | Photosensitivity scan (2.3.1) — **conditional** on strobe/glitch-tagged assets | ≤3 flashes/sec above the size/contrast threshold. Trace Center PEAT-equivalent frame analysis |
| 15 | Motion-actuation check (2.5.4) — **conditional** on device-orientation-driven assets | UI alternative exists and motion-triggering is disableable |
| 16 | Responsive preflight (overlap, overflow, fixed heights, free-position counts, no-mobile-plan blocks) at 320/390/768/1280/1440 | Zero blocking findings. **320 is added below the prior report's capture matrix because that is where text-reflow blowouts actually appear** |
| 17 | Long-string reflow fuzz (40-char unbroken token at 320px) | No overflow |
| 18 | 200% zoom reflow | No horizontal scroll, no content loss |
| 19 | Pseudolocalisation (+35% string expansion) | No overflow or truncation |
| 20 | `lhci` performance budget — median-of-3, mobile, simulated Slow-4G (1.6 Mbps down / 750 Kbps up / 150ms RTT, Lighthouse's documented default) + 4× CPU | **LCP ≤2.5s, CLS ≤0.1** (internal stretch 0.05), **INP ≤200ms** (or TBT ≤600ms floor / 300ms aspirational as proxy), **pre-LCP transfer ≤1.5–2MB** (not total page weight) |
| 21 | Font-loading audit | `font-display: swap` on every `@font-face`; preload only the committed 2–3 families; **blocks a 4th family sneaking in via a late component swap** |
| 22 | SEO / structured-data validation | §13.6 |
| 23 | Broken-link + console-error sweep, HTTPS/mixed-content check | Zero |
| 24 | No-JS render check | Content visible, nav usable, forms submittable. **Also the crawler's view** |
| 25 | Anti-slop advisory pass | **Non-blocking, logged** — see §13.7 |
| 26 | Asset licence-manifest completeness | Every font and image has a recorded licence class; commercial foundry faces emit a **pre-launch blocker** |
| 27 | LOCK purity gates 1–5 (§12.5) | All pass |
| 28 | Evidence bundle assembled | §15.6 |

### 13.5 Core Web Vitals as of 2026

| Metric | Good | Poor | Note |
|---|---|---|---|
| LCP | ≤2.5s | >4.0s | |
| CLS | ≤0.1 | >0.25 | Internal stretch target 0.05 ⁶ |
| INP | ≤200ms | >500ms | **Replaced FID in March 2024.** Now the most commonly failed vital (~43% of sites) — meaning main-thread cost from motion is a live risk, not theoretical |

Only ~43% of mobile origins and ~54% of desktop origins pass all three. **[V — web.dev/corewebvitals, 75th-percentile methodology; HTTP Archive Web Almanac 2024 pass rates]**

**A dragged-in unoptimised photo blows LCP single-handedly.** A modern phone shoots 4032×3024 at 2–5MB. Under Lighthouse's documented Slow-4G profile that is roughly **10–25 seconds of transfer alone** — instantly "poor." Since the product is explicitly about a human freely swapping in artwork, this is the **expected common path, not a corner case**. The fix belongs at **drop time**, not lock time. **[V — thresholds and throttling profile; file-size arithmetic is inference]**

### 13.6 SEO / structured-data gate (all mechanically verifiable)

Unique `<title>` per page; meta description 50–160 chars; canonical URL; Open Graph + Twitter Card including an image; `<html lang>` matching the interview language; **single `<h1>` with no skipped heading levels** (an accessibility overlap — screen-reader navigation depends on it); 100% image alt coverage; `robots.txt` + `sitemap.xml` generated from the page tree; **JSON-LD matched to the site-type answer** (Organization/WebSite for marketing, VideoGame for game promo, WebApplication for app shell, FAQPage/BreadcrumbList where those sections exist) validated against schema.org.

### 13.7 Severity tiers — what blocks what

| Tier | Blocks | Examples | Surfacing |
|---|---|---|---|
| **0** | The individual placement/edit from completing | Contrast <3:1 on placed text; target <24px with no valid exception; missing alt/decorative choice on a new image; duplicate ARIA id | Inline, immediate |
| **1** | LOCK only — never interrupts live editing | Full-page axe critical/serious; `lhci` budget miss beyond the floor; 320px reflow breakage; missing required structured-data fields; unresolved asset-licence gap | The gate report |
| **2** | Nothing — advisory, dismissible | APCA good-but-not-great; non-optimal image format; duration slightly out of band; **the anti-slop advisory** | Batched into the Design Health pill, **never a toast stream** |
| **3** | Nothing — silent telemetry | Minor spacing deviations under free-position; motion-library usage stats | End-of-session digest |

**Mechanics:** debounce live checks to fire on drop/mouseup (never mid-drag, never per-frame); collapse repeated violations of the same rule into one counted badge; gate all Tier-2 surfacing through the single Design Health pill.

**Ambient badges beat blocking dialogs during editing; hard gates belong only at LOCK.** Most problems are cheaply detectable without a model in the loop, and a non-designer will not tolerate hard blocks mid-edit.

### 13.8 The anti-slop lint changes role (argued both ways, resolved)

**For keeping it strict:** the human only chooses a *direction* among ~10; the editor still auto-places components from that direction before the human touches anything, and the claude.ai-side generation is itself subject to the same distributional-median pressure the prior report documented (Tailwind's 2019 indigo-500 default propagating into "every AI interface is purple"). An unlinted generation can hand the human a pre-homogenised menu where every "direction" still routes through the same three icon-card layouts.

**Against:** a human who saw 10 directions and deliberately picked the purple gradient one is exercising the exact taste-agency this product exists to enable. Mechanically blocking `bg-indigo-500` after a real choice contradicts the premise, and several "tells" (icon-topped 3-col grids, rounded cards) are legitimate patterns for specific content.

**Resolution:** demote to a **Tier-2 advisory at the human-edit layer** with a permanent per-element dismiss, and keep it as a **hard gate only upstream** — linting the claude.ai-generated design-system JSON **before the human ever sees the menu of choices**. The upstream gate is load-bearing, not optional, once the downstream gate is softened.

The 16 machine-detectable tells: purple-to-blue gradients (Tailwind blue-600/purple-500 defaults), Inter everywhere, uniform 16px radii + 24px padding, three-card layouts with tiny icons, badge-above-H1 heroes, serif-italic accents, generic stat banners, low-contrast dark mode, glassmorphism. Analysis of 1,590 Show HN pages: 22% heavy slop, 32% mild, 46% clean; ~75% of commercial pages launched Q1 2026 carry at least one strong signature. **[V — 925studios analysis, Hallmark's 57 detection gates, Developers Digest cataloguing]**

### 13.9 Never claim certification

Deque's own Accessibility Coverage Report (13,000+ pages/page-states, ~300,000 issues) found axe-based automated testing catches **57.38%** of real accessibility issues **[V]**. Running axe + Pa11y + Lighthouse + all the live checks raises the floor meaningfully but does not close the gap. Since this product replaces the AI *aesthetic* judge with a human but does **not** add a human *accessibility* judge, the honest claim is **"passed N automated + structural gates,"** never "WCAG 2.2 AA certified." The evidence bundle carries an explicit named gap for manual/screen-reader review.

### 13.10 APCA posture

APCA models perceived contrast more accurately for the dark, cinematic, large-type palettes award sites favour, but it is a candidate for WCAG 3.0 (still draft as of 2026) and **has no independent legal standing today**. The defensible posture is a **dual gate**: pass WCAG 2 (4.5:1 / 3:1) **and** compute APCA as a stricter internal target. Both are pure two-colour arithmetic, so both run live for free. **[V — APCA draft status, git.apcacontrast.com; the Lc75/60/45 bands are inherited from the prior swarm report and not independently re-verified — see §20.3]**

---

## 14. Steps 5 and 6 — regeneration, more variants, redesign, custom components

### 14.1 More variants (deterministic, no model call)

"Generate 10 variants of this component on demand" must **not** be implemented as parallel subagents writing files. **Subagents are policy-blocked from the `Write` tool in this environment — verified twice** (MEMORY.md `reference_subagent_write_blocked`, 2026-07-07, and a live re-confirmation on 2026-07-18 whose Write call was rejected with *"Subagents should return findings as text, not write report files"*). Bash heredoc writes are not blocked. **[V — first-party]**

**Correct design:** `variants.ts` — a deterministic generator that reads the chosen direction's tokens and emits parameterised component markup. No model call, no Write block, instant, and **it guarantees the variants stay inside the direction, which is D1's whole point**.

| Operation | Behaviour |
|---|---|
| **More variants** | Next N for the slot, using the skill-supplied current highest index so numbering is **append-only** and cannot collide with previously-ingested variants |
| **More like this** | 5 deterministic neighbours of the selected (already-approved) variant, appended to the bar. **Satisfies "ask for more variants" without ever presenting a 30-item wall, and keeps new options anchored to something the user already liked** |
| **Lazy generation** | Generate on first open of a family's swap panel; cache per direction; **never pre-generate families the site does not use**. Ten variants × ~12 families is ~120 component variants per direction — eager generation stalls Step 4 |

### 14.2 Redesign the system, or part of it

| Scope | Behaviour |
|---|---|
| **Partial** (e.g. "new colour, keep the type") | Re-enter Step 2 with the current direction vector, marking which of the 26 slots are frozen and which are open. Because ≥60% of artwork is token-referencing, most art re-skins for free |
| **Full** | A new Step-2 cycle with prior identity as **negative constraint** |

**Migration is mandatory and must never silently drop a node.** A new `system.lock.json` invalidates every variant reference. The migration report: map old variant ids to new; list unmappable nodes explicitly; the user resolves each. This is logged as an explicit operation, not an implicit side effect.

**Layout survives a direction swap** — placement is stored as grid integers and token indices, so a direction change can keep placement and re-resolve tokens, *provided both directions share the same grid spec*. That is why `layout.breakpoints` and `type.viewport-endpoints` are marked `n/a` (identical across all directions) in §7.

### 14.3 Cross-direction component swaps — the unresolvable tension, made visible

The user is in Direction 3 (warm paper, editorial serif, 600ms fades, 2px radius). They see Direction 7's neon pill button in the bar and want it. **Two implementations, both bad:**

| Option | What happens | Why it fails |
|---|---|---|
| **A — Re-skin** (button references roles) | The pill inherits Direction 3's terracotta, 2px radius, slow easing | It is no longer neon, no longer a pill, no longer the thing they pointed at. The swap "worked" and produced something they didn't want; they conclude the bar is broken |
| **B — Transplant** (button carries literal values) | The site now has two accent hues, two radius scales, two motion languages | The token lint fires; and every future direction-level change leaves this button behind, permanently |

**Resolution — make the tension visible rather than pretending it is solved:**

1. The swap UI shows **both renderings side by side**, labelled *"Fitted to your direction"* and *"Kept as designed (adds 6 off-system values)."* The user picks explicitly.
2. Transplants are recorded in a visible **coherence-debt ledger** with a count.
3. A soft cap (≈3 transplants) triggers the genuinely useful move: **"You have transplanted 4 components from Direction 7 — switch the whole site to Direction 7 and transplant these 4 back the other way?"** No existing tool offers this.
4. **Do not block cross-direction swaps.** Blocking is what makes the user abandon the direction model entirely.

### 14.4 Typed slot contracts and the content orphanage

**Failure scenario:** hero variant A has `{headline, subhead, cta}`. The user swaps to variant B with `{eyebrow, headline, subhead, cta_primary, cta_secondary, stat_row[3]}`. Where does their carefully-written CTA label go? What fills the eyebrow and the three stats? **If the tool auto-fills with lorem or an AI guess, the user now has fake statistics on a live page and may not notice.** Swap back to A and the eyebrow and stats are gone permanently. Do it twice and original copy is lost with no undo path across the swaps.

**Contract:**

1. Every component declares a typed slot contract: `{name, type, cardinality, required}`.
2. The component bar **only offers variants whose contract is a superset or exact match**, and states **before** the swap: *"this variant adds 4 slots"* / *"this variant has no place for: [stat_row]"*.
3. **Content orphanage:** anything the target cannot hold moves to a visible parked panel, **never deleted**, and is auto-restored if a later swap re-introduces the slot.
4. Newly-created empty slots render as **visibly-flagged placeholders that BLOCK LOCK** until filled or deleted. **This is what prevents fake stats shipping.**
5. Slot names are part of the component contract and validated on swap.

### 14.5 Custom components (Step 6)

Three paths:

| Path | When | Mechanism |
|---|---|---|
| **Registry** | Whitelisted families: table, chart, embed, form | Deterministic generator against the direction's tokens + the dataviz sub-token set. **v1 caps custom components to this whitelist; everything else is explicitly out of scope** |
| **Agent-authored** | A genuinely novel component | `Task(general-purpose)` with a role prompt from the skill's `prompts/` dir. **Returns code as TEXT; the main thread writes it** (subagent Write is blocked). Runs the six coherence lints before acceptance |
| **Custom code block** | The signature moment, or anything the system shouldn't own | An **opaque draggable container** holding hand-written HTML/CSS/JS. The editor positions it but **never introspects** it. **This is where the quality ceiling actually lives** |

**The `component.custom-slot` registration contract is the gate that makes this safe:** a custom component enters through a door that enforces token usage, or every custom addition is an incoherence vector.

### 14.6 Charts, specifically

A chart is not one component. It decomposes into four parts:

| Part | Content |
|---|---|
| **Marks** | 12 types: line, area, bar/column, pie/donut, gauge, scatter/bubble, heatmap, funnel, radar, waterfall, treemap, map |
| **Chrome kit** | axes, gridlines, ticks, labels, legend, tooltip, annotation/reference line, zero-line — **4 treatments applied across all 12 marks, which is what makes a site's charts read as one system** |
| **Colour ramps** | categorical / sequential / diverging, **derived from the direction's OKLCH anchors, never picked**, validated colourblind-safe in both schemes |
| **Data states** | empty, loading, partial (filter returned nothing), error, single-data-point — **required**, because charts fail more often here than in the happy path |

shadcn/ui ships "Chart" as a single registry entry; Untitled UI splits Line & bar (8), Pie (3), Radar (3), Gauges (3), Progress circles (1) — **both under-model the chrome. [V — fetched]** The local `dataviz` skill already encodes a form heuristic, a colour formula with a runnable validator, mark specs, interaction rules, and a palette reference at `references/palette.md`. **Reuse it as the chart sub-system spec rather than reinventing.**

**Decide early: build-time SVG or a client library.** A charting library is real client JavaScript on a static marketing page, and 12 marks at v2 may require a runtime that undermines the performance gate. **v1 default: build-time SVG.** Interactive/dashboard-grade charts are v3 and pull in tooltips, brushing, legends-as-filters, and a dependency the performance budget must absorb.

### 14.7 The signature moment is not a variant set

The prior report's Findings 2 and 6 are explicit that award-tier winners have exactly **one** bespoke signature moment, and that treating identity-carrying choices as generic catalogue picks is **the root mechanism of AI-design homogenisation** (Finding 5). If the component bar offers "10 signature-moment variants" the way it offers 10 button styles, **it mechanically reproduces the sameness problem the whole prior research effort diagnosed.**

Correct treatment: 2–3 bespoke **concept** candidates generated at Step 2 tied to the specific brand narrative, chosen and refined at Step 4, and handled thereafter through the custom code block. **A lint flags a second signature moment.** A system that lets the user pick five produces a worse site than one that lets them pick none.

---

## 15. Steps 0 and 8 — warm start, publish, licences

### 15.1 Warm start is a glob, not new infrastructure

`.acos/design-library/okoa-brand/` already holds a complete design system as five files: `design-system-spec.yaml` (883 lines; keys `meta, color, typography, spacing, grid, motion, iconography, components, patterns, data_visualization, globals, quality_control, test_runner, expressive_brand, motion_interaction, generative_parametric, naming_and_scope`), `IMPLEMENTATION.md` (250 lines), `compliance-report.json` (53 tests, per-test `{test_id, status, severity, message, evidence}`, `compliance_score: 0.92`), `source.html`, `design-influences-research.md`. **[V — verified by `ls` + reads]**

Step 0 = glob `.acos/design-library/*/design-system-spec.yaml` + `.acos/website-builder/systems/*/system.json` + the target project's `.acos/`, then offer them.

**The `compliance-report.json` shape is also the right return format for validating the Step-3 hand-carry.**

### 15.2 The user's own prior art is the closest existing thing to this product

`/Users/zee/Documents/Vibe Coding/website-design-okoa/` contains **13 named design lanes** (`ridgeline, stillness, voltage, japandi-dark/warm/sage/mauve/ocean, nordic-tech, studio-nordost, datum-tech, shibuya-light, art-of-zen`) × **3 sub-variants** (v1 institutional / v2 data-dense / v3 coffee-table) × 5 pages = **195 generated HTML files**; a distilled token bundle `_build/tokens/all_variants.json` carrying `bundle 1.2.0` and a sha256 token hash with per-variant keys `{description, display_family, google_font_display, google_font_body, google_font_weights, is_dark, colors{bg, bg_alt, bg_warm, chrome, fg1, fg2, fg_on_dark, border, accent, accent_secondary, tertiary}}`; a per-variant `README.md` acting as a **design + LICENCE REGISTER** with an asset-by-asset source/licence table; and `_build/visual-audit/iteration-1..13/` — thirteen recorded screenshot iterations. **[V — directory listing, JSON parse, `ls`]**

**This validates D1 with the user's own prior behaviour**, and the README licence register is a ready-made template for the Step-8 evidence bundle. It also shows the honest scale of a "direction": ~11 colour roles + 2 font families + a stated intent sentence.

**Mine this before finalising the direction model.**

### 15.3 The warm-start split (restated as a rule)

| Always carry forward | Never carry forward by default |
|---|---|
| Token-name schema | Hue anchors |
| Component slot contracts | Type pairings |
| Motion-primitive library | Radius / density |
| Font catalog | Motion character |
| Anti-slop deny-list | Artwork |
| Editor configuration | Grid personality |
| User-level interview answers (a11y posture, device assumptions, decision style) | Signature moment |

Prior identities are injected into Step 2 as **negative constraints** ("do not produce a direction within 30° of these hues or reusing these type pairings") unless the user answers "yes" to the sibling-site question (C4).

### 15.4 Publish

Default target: **Cloudflare Pages**, static, free bandwidth, via `wrangler pages deploy ./dist --project-name=<x>` with a scoped API token stored once. Cloudflare Pages Direct Upload has a documented CLI path.

**A one-time credential-setup step is part of the PRD.** The user's existing runbook says *"Claude cannot sign in or upload for you (your account + password). You perform steps 1–9"* **[V — DEPLOY-STEPS.md, verbatim]**. If v1 does not automate deploy, the PRD says so and emits a runbook. **It does not leave it ambiguous — the ambiguity is where the user discovers the gap.**

### 15.5 Content mode (v2, but high-leverage)

**90% of month-six edits are copy changes.** A text-only editing path that needs no dev server, no design layer, and no `node_modules` — edit `content.json`, re-render statically — is what prevents the failure where a user hand-edits built HTML because launching the design surface is too much friction, and the next unlock silently reverts it.

The precedent already rotted once: `/Users/zee/fruitsync-animated-variants` is **not a git repository**, contains 30 opaque variant directories with **no manifest saying what each one was**, and its 18 Python builder scripts include a deploy note admitting *"the website tree is outside git; the builder source is preserved at `_builders/buildsite.py` (and the working copy in the job tmp)"* — the authoritative copy was in a temp directory. **[V — `git status` failure, `ls`, DEPLOY-STEPS.md]**

Prevention: `git init` at Step 0; `provenance.json`; content mode; a machine-readable *"generated — do not hand-edit; run /website-builder unlock"* banner in the exported tree; unlock diffs against the lock manifest and **refuses to overwrite hand-edits without showing them**; pin exact versions and commit the lockfile.

### 15.6 The evidence bundle

| Section | Contents |
|---|---|
| **Fonts** | Per family: foundry, licence class (OFL / CDN-only / commercial-required), file hash, source URL, attribution requirement. **Commercial foundry faces emit a pre-launch blocker rather than being embedded** |
| **Assets** | Per asset: generator, model, plan tier, licence class, prompt, alt text, source |
| **Third-party marks** | Platform badges, social icons, trust badges, map tiles — with their usage rules recorded and confirmation they were used as supplied, not redrawn |
| **Gate report** | Every lock-time gate with pass/fail, thresholds, and measured values |
| **Contrast proof table** | Every text/surface pairing with WCAG ratio and APCA Lc |
| **Screenshots** | 320/390/768/1280/1440 × light/dark × full/reduced motion |
| **Direction tour** | All directions shown, the user's pick, and their stated reason. **The legal/creative record: "we showed 10 distinct directions; the user chose #5 because [principle]; all code conforms to direction-5 spec." Proof of intentional design** |
| **Reference triangulation** | Which ≥3 references informed which direction, and how they were abstracted ("Direction 4 abstracts Swiss modernism's grid discipline, Japanese minimalism's negative space, and brutalism's weight contrast — reference pixels discarded, attributes recombined") |
| **Disclosure** | *"Automated accessibility gates passed: N. Manual and screen-reader review not performed."* |
| **Substitution log** | Every auto-fix during ingest: font swaps, contrast nudges, image recompressions |

**The ≥3-reference rule is the legal boundary.** US copyright/trade-dress law treats look-and-feel as largely not copyrightable absent consumer confusion plus a trade-dress claim requiring integration of multiple nonfunctional elements. The safe pattern is ≥3 references from different eras/genres/cultures, abstracted to principles, recombined. With <3 the "derived from X" risk increases. **[V — UC Law Review, Michigan Studio Space guidance; agency practice at Sagmeister & Walsh, Pentagram]**

Add a post-generation check: **if a direction is >70% overlap with any single reference, regenerate against a different reference.**

---

## 16. Architecture

### 16.1 Shape: thin router skill + TS scripts + one Bun server + a browser editor

**Not** a phase-orchestrator agent pipeline. The loan-doc phase-agent architecture the prior swarm recommended exists to run an autonomous multi-hour generation loop; **this product's expensive loop is a human sitting in a browser**, which the local-server pattern already serves.

The in-repo template is `~/.claude/skills/acos-image-builder/`: 4 files — `SKILL.md` (6.9KB), `app/server.py` (105 lines, stdlib `ThreadingHTTPServer` on 127.0.0.1:8810), `app/index.html` (1,636 lines / 102KB, inline CSS + vanilla JS, no build step), `scripts/imagebuilder.sh`. Five routes: `GET /api/library`, `GET|POST /api/project`, `POST /api/export`, `POST /api/upload`, plus static serving. One global `state = {doc, layers, sel, tool, brush, color}` with `serialize()`/`restore()`, a 40-step undo stack, localStorage autosave, ⌘S → POST. **[V — full read]**

**Every structural element the Website Builder editor needs already exists there in working form.** The one thing that does not transfer is the substrate: image-builder composites raster pixels on a `<canvas>`; a website editor manipulates real DOM nodes with CSS anchors. **Reuse the shell and the server contract; do not reuse the canvas compositor.**

`acos-type-forge` proves the full loop this product needs: one server fronts a hub linking three browser tools; browser edits persist as plain JSON on disk (`glyph-edits.json`, `spacing.json`); a deterministic non-browser script (`vectorize.py`) compiles those edits into the real shipping artifact (a TTF); a separate `rename_export.py` finalizer enforces the licence rule; and a *"review IN THE BROWSER before finalizing"* gate is marked ⚠️ do-not-skip. **[V — full read of SKILL.md, 196 lines]** Map directly: `layout.json` ← browser editor; `build.ts` = `vectorize.py`; LOCK = `rename_export.py`; the licence step is precedent for Step 8.

Its SKILL.md also states the one-origin rule's reason explicitly: *"Web fonts can't load over `file://` in Chrome → always serve over localhost."*

### 16.2 Language: TypeScript on Bun

`/Users/zee/CLAUDE.md` lines 25–46 make TS/Rust the mandatory default for **all** new code; Python is allowed only for (1) editing existing Python, (2) a Python-only library, (3) extending an existing Python hook chain. **None covers a new skill's own server or editor.**

Compliance precedent: `.claude/skills/acos-reverse-cleanroom/scripts/` — 16 `.ts` files with `#!/usr/bin/env bun` shebangs, a `scripts/package.json` (`"type": "module"`, `"Run with bun (no build step)"`, one dependency: `playwright@^1.48.0`), pure decision-logic split into `lib/*.ts` so ~90% is unit-testable, and a `bun selftest.ts` harness reporting 67/67 pass. `acos-research-riffs` has 13 more `.ts`. **[V — `ls`, `head`]**

Against that: **122 `.py` files across project skills, 66 across global skills.** The estate is Python-first; **this skill must not be.** Toolchain verified present: bun 1.3.9 at `/Users/zee/.bun/bin/bun`, node v20.19.3, rustc 1.88.0. **Rust is unnecessary** — nothing here is perf-critical or needs a single binary.

**Python-gravity is a real risk** (§17-R12): the path of least resistance is copying `server.py` and violating the rule. **Mitigation: port `server.py` → `server.ts` first, before any other code, so the TS spine exists from day one.** It is ~105 lines mapping 1:1 onto `Bun.serve()`, which gives native static serving, `Bun.file`, WebSocket upgrade, and streaming with zero dependencies. **A one-hour port, not a rewrite.**

### 16.3 Skill files

```
.claude/skills/acos-website-builder/          ← git-tracked, authored here
  SKILL.md                                     ← thin router, 9 phases
  scripts/
    package.json                               ← type: module, bun, no build
    server.ts                                  ← Bun.serve, fixed port 8820
    lock.ts                                    ← build → scrub → assert → snapshot
    import-system.ts                           ← Step-3 tolerant parser + validator
    variants.ts                                ← deterministic variant generator
    gates.ts                                   ← structured verdicts, never throws on a normal fail
    capture.ts                                 ← Chrome --headless=new wrapper
    evidence.ts                                ← Step-8 bundler
    registry.ts                                ← v2, cross-site component/direction registry
    verify.ts                                  ← regenerate-to-temp + diff -r
    doctor.ts                                  ← hash mismatches, orphaned overrides, stale locks
    extract-override.ts                        ← the sanctioned escape hatch
    install.sh                                 ← SYMLINK to ~/.claude/skills/
    selftest.ts                                ← bun selftest.ts, cleanroom's 67/67 is the bar
    lib/
      site-model.ts, render.ts, anchors.ts, cascade.ts, snap.ts, tokens.ts,
      slots.ts, coherence.ts, security.ts
  app/
    index.html                                 ← editor shell (3-pane)
    editor/
      anchors.ts, text-edit.ts, component-bar.ts, containers.ts,
      history.ts, request-more.ts, lock-preview.ts, overlay.ts, navigator.ts
  references/
    interview-bank.md                          ← §5, as a reference file not inline prose
    prompt-template.md                         ← §6
    item-inventory.md                          ← §7–§8
    gotchas.md                                 ← §16.6
  prompts/
    interview-synthesizer.md
    custom-component-author.md
```

**Installed globally via symlink**, not a copy. `acos-type-forge` exists in both the ACOS repo and `~/.claude/skills/` with byte-identical SKILL.md — **copies, not symlinks** (`ls -la` shows no symlinks anywhere in `.claude/skills/`) **[V]**. Website Builder must be usable from any project but is real code that must be version-controlled. `install.sh` creates the symlink, breaking the drift pattern rather than repeating it.

### 16.4 Invocation contract

```yaml
disable-model-invocation: true
user-invocable: true
argument-hint: "[--project <path>] [--resume] [--system <name>] [--port 8820] [--content] [--local-gen]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
```

Precedent: `acos-reverse-cleanroom` and `acos-design-variants` both set `disable-model-invocation: true` + `user-invocable: true` + an `argument-hint` **[V — frontmatter reads]**. `Bash` is needed to launch the bun server; `AskUserQuestion` for the interview (`acos-interview` runs its Q&A in the main context precisely because it is interactive).

**Do NOT list `Task` in `allowed-tools`.** `acos-skill-maker/SKILL.md` (~line 109) states: *"Sub-agent spawning is NOT a skill-frontmatter tool. Never add `Agent` or `Task` to `allowed-tools` — the framework ignores it… set `context: fork` and `agent: architect`."* The estate contradicts itself here — `acos-reverse-cleanroom/SKILL.md` line 6 lists `Task` — **treat skill-maker as the authority and do not copy that line.** **[V — both reads]**

**Phase 0 is a mandatory Confirmation Gate.** Both `/Users/zee/CLAUDE.md` and `ACOS 3.0/CLAUDE.md` mandate it. Bake the restatement into SKILL.md rather than relying on the ambient rule, and make the interview itself the confirmation artifact: restate the brief, get an explicit yes, then write anything.

Per-project config at `.acos/config/website-builder.yaml`, mirroring `.acos/config/cleanroom.yaml`: version, default port, breakpoints, direction count (10), variants-per-component (10), artwork count (20), gate thresholds, licence policy tier, publish target — snapshotted to `audit/config-snapshot.yaml` at init.

### 16.5 Agents

**Zero new files in `.claude/agents/`.** `ACOS 3.0/CLAUDE.md` Restricted Files: *"`.claude/agents/` — Agent definitions are infrastructure. Modification requires human approval."* The estate shows agents **are** added in approval batches (12 `rc-*`, 17 `dr2-*`, 9 `ic-*`), but `acos-synthesis-protocol` explicitly avoids it by spawning `Task(general-purpose)` with role prompts in the skill's own `prompts/` dir. **[V]**

Website Builder's agentic surface is small and human-paced (interview synthesis, prompt authoring, custom-component generation), so the general-purpose route is right: zero approval events, zero roster churn.

| Prompt | Purpose | Constraint |
|---|---|---|
| `interview-synthesizer` | Raw answers → structured brief for the prompt template | Returns text; main thread writes |
| `custom-component-author` | Step-6 novel components against the direction's tokens | Returns code as text; main thread writes (Write is blocked in subagents) |

### 16.6 Local server and the harness

**FIRST-PARTY VERIFIED: long-running local servers die in this harness** — and the editor's entire premise is a long-running local server.

`acos-guided-reader-server-gotcha.md` documents this being hit and diagnosed on 2026-07-09:

| Attempt | Result |
|---|---|
| Script spawns a detached child and exits | **Orphan reaped instantly.** `server.log` 0 bytes, nothing in `lsof -iTCP -sTCP:LISTEN` |
| Bash `run_in_background: true` | Binds, curls HTTP 200, then **SIGTERM (exit 143) AT THE TURN BOUNDARY** because the harness reaps tracked background tasks |
| `setsid nohup … &` | `setsid: command not found` on macOS |
| **Python double-fork daemon** (fork → setsid → fork → exec) | **WORKS** |

**[V — first-party, four attempts with exit codes]**

**Failure scenario for this product:** the user says "open the design surface," Claude starts the server, replies, the turn ends, the server is SIGTERM'd, and the browser shows `ERR_CONNECTION_REFUSED` — **every single time, appearing intermittent because it depends on turn timing.**

**Mitigation (recipe already proven in-repo):**

1. Double-fork daemon pattern.
2. **FIXED port** (8820) so the URL is known up front — **not** gr-server's random-port design, which orphans the user's open browser tab after an eternity `/clear`.
3. Write `{port, pid, url, sessionId}` into `state.json` at boot.
4. `curl --retry 20 --retry-connrefused` to confirm bind.
5. **A SECOND curl in a SEPARATE tool call** to prove it survived the turn boundary before telling the user to open it.
6. Regenerate-if-stale on startup (gr-server served a frozen `page.html` with no freshness check and showed an old UI after the template changed).

**Language conflict to resolve:** the proven launcher is Python; the standing rule mandates TypeScript. The TS equivalent is `child_process.spawn(cmd, args, {detached: true, stdio: 'ignore'}).unref()`, which is **not proven in this harness and must be re-proven with the same curl-across-turn-boundary test** before the PRD assumes it works. See §17-O5.

**Alternative worth spiking:** the single-origin variant — one Bun server proxying `astro dev` — collapses the CORS/postMessage surface to zero at the cost of proxy complexity. Spike both before locking the architecture.

**Two-process arrangement (the shape Onlook, Stackbit and Tina all converged on):** Process 1 is `astro dev` on 127.0.0.1 rendering the site with the editor integration (doc write → generator rewrites `src/generated/**` → HMR reloads, ~100–300ms). Process 2 is `wb-server` (Bun) on 127.0.0.1, the single doc writer, exposing `GET /doc` (ETag), `POST /ops`, `GET /events` (SSE), `POST /variants`, `POST /lock`. The editor chrome is a parent page served by `wb-server`; the site renders in an `<iframe>`; the two talk over `postMessage` with an explicit `targetOrigin`. Onlook's published flow is the same shape: load code into a container, container serves it, *"our editor receives the preview link and displays it in an iFrame,"* then instruments the code to map elements to their place in code **[V — quoted]**.

Three concrete wins: the site page stays pristine so **a screenshot of the iframe is a screenshot of the real site with no toolbar in it**; the editor survives an Astro restart without losing unsaved state; and LOCK preview is literally "point the same iframe at `dist/published`."

**The SSE + JSONL inbox pattern is house doctrine.** `gr-server.py` (2,000+ lines) and its validated port `ic-server.py` implement stdlib `ThreadingHTTPServer`, port written into `state.json`, `GET /state` (ETag/304), `GET /events` SSE with ~15s keepalive, browser commands appended to `commands.jsonl`, `POST /internal/*` for Claude to write back. The guided-reader SKILL.md is explicit: *"Each `tail -f` blocks the bash thread; Claude does not consume tokens while waiting."* **[V — quoted]** The division of labour is settled: **the server is a dumb byte-mover that NEVER calls `Task()`; the Claude session is the only engine.** `riff-server.ts` documents its own rule: *"Read-only by construction: there is no route that writes to the session."*

This is exactly how Step 5 ("10 more variants of this button") and Step 6 ("add a chart") happen without the user leaving the browser, **at zero token cost while they design.**

### 16.7 Screenshots

**Plain Chrome CLI, zero npm dependencies.** `website-design-okoa/_build/screenshot.sh`:

```
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
  --window-size=1440,3000 --virtual-time-budget=4000 \
  --screenshot=<out> <url>
```

then `[ -s "$out" ]`. **[V — read]**

By contrast, the ACOS Puppeteer path is only reachable via `NODE_PATH=/Users/zee/.npm/_npx/7d92d9a2d2ccc630/node_modules` — an npx cache that can be evicted; ACOS 3.0's root `package.json` declares `puppeteer@^24.39.1` but **`node_modules/` is EMPTY (0 entries)** **[V]**.

**Inherit the capture waits from `.claude/scripts/html-to-pdf.js`** — each encodes a real production bug: `page.goto(fileURL)` not `setContent()`; `networkidle0` with fallback to `load`; **strip `loading="lazy"` before capture** (headless IntersectionObserver never fires below the fold); `await document.fonts.ready` **plus per-image `decode()`**; then a 500ms deferred-CSS settle. Re-express in TS; do not re-derive.

If scripted interaction/hover capture is later needed, follow the cleanroom precedent: `cd <skill>/scripts && bun add playwright && bunx playwright install chromium` — **the dependency lives inside the skill, not in an npx cache.**

### 16.8 Hooks

A skill **can** register its own hook dynamically: `acos-reverse-cleanroom` Phase −1 step 4 says *"Arm the egress guard: add the PreToolUse hook to `.claude/settings.local.json`… Verify with a probe call"*, and Phase 7 removes it at close. The guard is `scripts/egress-guard.ts` — **a TypeScript PreToolUse hook**, so TS hooks are already accepted. **[V — quoted]**

The existing PreToolUse chain has 5 entries, four ending in `|| printf '{"hookSpecificOutput"…allow'` (fail-open); the one hard gate is `block-review-rules-read.sh`. **Any Website Builder hook must be cheap and fail-open.**

| Hook | Purpose | Priority |
|---|---|---|
| **PreToolUse: editor-file-ownership guard** | Blocks Claude's `Write`/`Edit` on `pages/*.doc.json`, `content.json`, `history.jsonl` while the editor lock is held | v1 |
| **PostToolUse: evidence mirror** | One-line verdicts into `.acos/evidence/<date>/website-<session>/` so `/acos-status` sees the build | v3 |

**"No LOCK without gates passing" is better implemented as a script exit code than a hook.**

### 16.9 Reuse-versus-build table

| Item | Decision | Path / source |
|---|---|---|
| One-origin server contract, 5 routes | **Port Python→TS** | `~/.claude/skills/acos-image-builder/app/server.py` (105 lines) |
| Browser-edits-as-JSON → deterministic compiler | **Adopt pattern** | `~/.claude/skills/acos-type-forge/scripts/vectorize.py` flow |
| SSE + `commands.jsonl` + zero-token `tail -f` | **Adopt pattern** | `~/.claude/skills/acos-guided-reader/scripts/gr-server.py`; `.claude/skills/acos-investment-committee/scripts/committee-room/ic-server.py`; `.claude/skills/acos-research-riffs/scripts/riff-server.ts` (already TS) |
| Chrome headless capture recipe | **Adopt as-is** | `/Users/zee/Documents/Vibe Coding/website-design-okoa/_build/screenshot.sh` |
| Capture waits (lazy-strip, fonts.ready, decode, settle) | **Re-express in TS** | `.claude/scripts/html-to-pdf.js` |
| Design-system schema + QA framework | **Adopt** | `~/.claude/skills/acos-design-system-forge/references/01-template.yaml` + `07-qa-framework.md` + extension modules (`motion-interaction.md` is the right source for D4's animation item) |
| Warm-start store | **Adopt as-is** | `.acos/design-library/<name>/` |
| Per-variant licence register format | **Adopt as-is** | `website-design-okoa/okoa-design/*/v1/README.md` |
| Session dir + ACTIVE marker + config snapshot | **Adopt pattern** | `.claude/skills/acos-reverse-cleanroom/SKILL.md` Phase −1 |
| Frontier-recomputed-from-disk principle | **Adopt** | `.claude/skills/acos-axiom-synthesis/STATE-MACHINE.md` line 66 |
| 3-variant side-by-side comparison | **Adopt** | `~/.claude/skills/acos-design-variants/SKILL.md` Phase 2 |
| Chart form heuristic, colour formula, validator, palette | **Adopt** | local `dataviz` skill + `references/palette.md` |
| Puck Data/Render split, viewports config, slot `allow`/`disallow` | **Adopt patterns, not code** | puckeditor.com docs |
| Figma constraint + "Ignore auto layout" model | **Adopt pattern** | help.figma.com |
| Stackbit annotation scheme + descent scoping | **Adopt pattern** | docs.netlify.com |
| Plasmic owned/managed file split | **Adopt pattern** | docs.plasmic.app |
| dnd-kit (MIT, 17,437★, pushed 2026-07-13) | **Adopt as code** | Pointer + keyboard sensors and collision layer **ONLY** — never as the layout model |
| ProseMirror / TipTap (MIT) | **Adopt as code** | One long-form block only |
| Wigum fix-loop exit-code contract | **Port to structured verdicts** | `.claude/skills/acos-ultimate-designer/scripts/wigum-loop.py` → `gates.ts` (cleanroom `lib/gates.ts` is the model: return verdicts, never throw on a normal fail) |
| Genesis registry | **Port Python→TS** | `registry.py` → `registry.ts` over the same `registry.json` (v2) |
| **The VLM judge loop** | **DO NOT PORT** | The human replaced it; porting re-imports the rejected architecture |
| **Autonomous Wigum aesthetic iteration** | **DO NOT PORT** | Same |
| **`.claude/agents/` additions** | **DO NOT ADD** | Human-approval-restricted; `Task(general-purpose)` suffices |
| **`site.json` model + renderer** | **BUILD NEW** | Nothing in ACOS does DOM-level layout editing |
| **Editor runtime** (anchors, snap, contenteditable, component bar, containers) | **BUILD NEW** | " |
| **Design-system importer + repair-prompt emitter** | **BUILD NEW** | " |
| **Deterministic variant generator** | **BUILD NEW** | " |
| **LOCK/export compiler** | **BUILD NEW** | " |
| **Evidence + licence bundler** | **BUILD NEW** | " |
| **`install.sh` symlink installer** | **BUILD NEW** | Breaks the copy-drift pattern |

### 16.10 Frameworks explicitly rejected

| Candidate | Licence / health | Why rejected |
|---|---|---|
| **GrapesJS** | BSD-3-Clause (npm), 26,067★, pushed 2026-07-24 — healthy | Backbone + underscore era architecture; core `dragMode: 'absolute'` is coordinate dragging with no responsive story; **its own docs scope Absolute Mode to *"fixed-layout designs … where responsiveness isn't required"***; the polished version lives in the commercial Studio SDK, not the open core. **[V — registry.npmjs.org, GitHub API, app.grapesjs.com]** Also note GitHub's API reports NOASSERTION while npm reports BSD-3-Clause — **re-verify against the actual LICENSE file at pin time** |
| **Craft.js** | MIT, 8,700★, **last push 2025-02-14** — ~17 months stale as of 2026-07, 225 open issues | Unacceptable as a foundation for a system that must run for years **[V — GitHub API]** |
| **Plasmic** | SDKs and code components open; **core editor and studio proprietary** | Self-hosting exists, forking the editor does not **[V — forum.plasmic.app]** |
| **Builder.io** | Only Mitosis (the compiler) is open | The visual editor is SaaS |
| **TeleportHQ** | Open component/codegen layer around a hosted editor | Same shape |
| **Puck** | **MIT, 13,018★, pushed 2026-07-24, actively developed** — genuinely the right philosophy and licence, now positioning as *"the agentic visual editor for your design system"* | **Three gaps, each fatal here:** (1) **no grid-cell placement model** — Puck composes flow lists via slots and *"multi-column layouts using nested components,"* so D2's snap-to-gridlines and Step-4(a) gridlines have no home; (2) **no per-breakpoint override cascade** — viewports resize the iframe but the Data document has no breakpoint dimension; (3) **it is React**, whereas the settled build target is Astro static with zero shipped JS, so components would exist twice. **Mine it for API shapes and possibly vendor individual utilities; do not build the product inside it** **[V — GitHub API + docs read; the three gaps are inference from the docs]** |

**Figma Sites** (open beta, Config 2025) confirms the direction is mainstream and supplies two transferable ideas — name-matched responsive variant binding (breakpoints named Desktop/Tablet/Mobile bind to variant property values with those names), and the fact that Figma treats custom cursors, marquee and parallax as **first-class site primitives**, corroborating the user's Step-2 item list. Nothing else is reusable: closed, hosted, exports no ownable editor. **[V — figma.com/blog, help.figma.com]**

### 16.11 macOS / harness gotchas to encode in `references/gotchas.md`

| # | Gotcha |
|---|---|
| 1 | **No `timeout`/`gtimeout` binary** on this Mac — `timeout 25 cmd` silently yields **EMPTY output**, not an error. Guard long runs with `run_in_background: true` + poll |
| 2 | **Agent-thread cwd resets between Bash calls** — absolute paths everywhere |
| 3 | House rule: open previews with `open -a "Google Chrome" <url>` |
| 4 | Opus subagents stream-idle-timeout on heavy binary reads — keep rendering/screenshotting in the main thread or background Bash |
| 5 | **macOS APFS is case-insensitive** — sibling direction names must not differ only by case |
| 6 | Autosave must be a small JSON diff POSTed to the server, **never a base64 blob in localStorage** (image-builder's own logged gotcha) |
| 7 | The Oracle scores Bash/Write/Edit/Task at threshold 9 fail-open, so ordinary bun/chrome commands auto-approve; **destructive steps score +5 and will prompt** — implement export as **write-to-new-dir-then-swap**, never `rm -rf` |
| 8 | Eternity `/clear` at 400k (project config) / 500k (daemon config — **the daemon's own config wins; hardcode neither**) kills the `tail -f` loop. Fixed port + `state.json` + a resume prompt that says **re-attach, do NOT relaunch** |
| 9 | `session-cleanup.sh` runs at SessionEnd on `.acos/state/` only, so `.acos/website-builder/` artifacts are safe |
| 10 | Astro HMR does not reliably hot-reload when files are **added or removed** under `src/pages/` — a variant swap that changes the import graph may need a full reload. Budget a measured fast path and a hard-reload fallback |
| 11 | `claude-in-chrome` MCP availability inside spawned agents is **unverified** — do not design any capture path that depends on it |

---

## 17. Risks and open questions

Severity-ranked. **Risks with no known mitigation are marked ⛔ and stated plainly.**

### 17.1 Critical

**R1 — Artwork is structurally undeliverable from claude.ai.**
claude.ai has no raster generation **[V — Anthropic, April 2026]**. The user's cited exemplar came from a 231-PNG Unity export, not a chat **[V]**. The failure: the interview asks about background art, the prompt asks for 20 artworks, and 20 flat geometric SVGs come back — the exact AI-slop register the anti-slop lint detects. The user hates all 20 and a whole branch of D1 is dead weight.
**Mitigation:** three honestly-labelled lanes (§7.9). Lane A code-drawn (genuinely good, token-parameterised). Lane B asset ingestion (what actually made FruitSync work; Step-0 question C3 detects it). Lane C external raster generation as a **separate** hand-carry with its own licence manifest, explicitly scoped in or out. **Never let the PRD imply a single paste produces site art.**

**R2 — Directions are selected in a preview that cannot render their typefaces.**
The artifact CSP permits `fonts.googleapis.com` under `style-src` but restricts `font-src` to `data:` and `claudeusercontent.com` — the CSS loads, the WOFF2 is blocked, the artifact falls back to a system face. Typography is the largest identity carrier. **You pick a look you have never seen.**
First-party corroboration that this failure class is already live: the shipped FruitSync site has **zero `@font-face` and zero `fonts.googleapis` references**; its only font token is `--sans: ui-rounded,"SF Pro Rounded","Hiragino Maru Gothic ProN","Quicksand",system-ui,…`. `ui-rounded`/SF Pro Rounded is Apple-only; Quicksand is installed nowhere by default. **Every non-Apple visitor sees Segoe UI or Roboto — a completely different typographic personality from the one the user designed and signed off. The user has almost certainly never seen their own shipped site as a Windows or Android visitor sees it.** **[V — grep of both `index.html` files, 0 matches]**
**Mitigation:** mandate base64 `data:font/woff2` @font-face for the display face in every direction artifact, subset to the preview glyph set, with the pre-subsetted strings supplied by the skill's font catalog so claude.ai pastes rather than invents. **Verify the CSP behaviour in 60 seconds first (§17-O1).**

**R3 — Silent truncation produces valid, wrong CSS.**
A truncated JSON payload throws and is caught. A truncated CSS block, HTML fragment, or SVG path is syntactically fine — the browser drops the last incomplete rule and renders. Direction 6's tokens get cut after 40 of 62 properties; the skill accepts it; the user spends 25 minutes wondering why the footer and secondary buttons look wrong while everything above the fold looks right. **No error anywhere.** Diagnosing requires diffing against a direction they have never seen in full.
**Mitigation:** the envelope with a per-run random terminator, per-file line counts, sha256 prefixes, smallest-first ordering, and a hard ingest refusal (§6.2).

**R4 — If the DOM is the source of truth, this is Dreamweaver 2003.**
The canonical WYSIWYG failure. Worse here because Claude is also writing the source.
**Mitigation:** `layout.json` as the only source of truth; the page is a pure render; the editor never serialises DOM (§12.1). **This must be a hard PRD constraint, not a note.** Zero DOM injection for hit-testing (§11.9).

**R5 — Long-running local servers die at the turn boundary in this harness.**
**[V — first-party, four documented attempts]** The editor's entire premise is a long-running local server, and the failure appears intermittent because it depends on turn timing.
**Mitigation:** fully mitigated by the proven double-fork recipe + fixed port + `state.json` + curl-across-turn-boundary verification (§16.6). **But the proven recipe is Python and the language rule mandates TS — the TS equivalent must be re-proven before the PRD assumes it (§17-O5).**

**R6 — Two writers, no lock, silent work loss.**
Near-certain, not a corner case, because the product design encourages alternating between talking to Claude and dragging things.
**Mitigation:** file ownership + PreToolUse guard + optimistic concurrency with 409 + every-save-is-a-commit (§12.10).

### 17.2 High

**R7 — The hand-carry costs 45–90 minutes per cycle, and Step 5 makes it a loop.**
The most likely way the product quietly dies: the user builds site 1, enjoys it, starts site 2 three weeks later, hits the paste marathon at minute 20, and never finishes.
**Mitigation:** one-paste protocol (~40 ops → ~5), `pbpaste` ingest, and — the strongest lever — **Local Regeneration Mode makes the web hop optional**, not the spine.

**R8 — Constraint dragging: the market ran this experiment and the constraint editor is the one that died.**
Wix Editor X — the closest commercial analogue to D2 — began sunsetting April 2024 and was killed January 2025 with all sites force-migrated to Wix Studio. The Wix **Classic** editor, absolute free positioning, is still shipping in 2026. Adobe Muse was killed 2018/2020. Webflow's cascade runs in both directions from a desktop base and its forum has recurring threads titled *"Break points cascading both up and down."* **[V — support.wix.com transition FAQ, helpx.adobe.com, discourse.webflow.com]**
**Concrete daily friction:** the user wants the hero headline 12px higher. In a free canvas that is one drag. Under D2 they must work out whether the lever is the parent's `align-items`, the element's `margin-block-start`, a `gap` that also moves three siblings, or a grid-row change — and then learn it didn't fix 1440px, or did and broke tablet. **They will hit this on their fifth edit and it is the moment they decide the tool fights them.**
**Mitigation:** never present raw CSS concepts — exactly three verbs (align to / space above-below from the scale / order among siblings); a **persistent pre-commit chip** stating which sizes an edit affects with a one-click "apply to all sizes"; an overrides dot on any element with breakpoint-specific values plus a panel listing them. **Webflow's #1 confusion is invisible overrides — make them visible.**

**R9 — Free position doesn't degrade gracefully; it collapses parents and bakes in the authoring viewport.**
Slow-motion: nothing breaks until the user opens the site on their phone weeks later.
**Mitigation:** anchored-offset, reserved `min-block-size`, per-breakpoint, auto-demote at ≤479, a visible counter, a hard LOCK gate. **⛔ Partial only:** for art whose composition depends on absolute relationships across the whole viewport, the only answer is to treat the composition as one component with internal responsive rules — **which means the user cannot drag its parts individually, which is exactly what they asked for. There is no better answer.**

**R10 — Cross-direction swaps have no good implementation.**
Re-skin destroys what the user liked; transplant destroys the system.
**Mitigation:** make the tension visible — side-by-side, explicit pick, coherence-debt ledger, soft cap, and the switch-the-whole-site offer (§14.3). **Do not block.**

**R11 — Component swaps silently destroy copy.**
Fake AI-invented statistics can ship. Copy is the thing the user hand-wrote and cares most about.
**Mitigation:** typed slot contracts, superset-only offers, the content orphanage, placeholders that block LOCK (§14.4).

**R12 — Python-gravity vs the language rule.**
Every reusable server/QA script in the estate is Python (122 project + 66 global `.py`); the path of least resistance violates the rule.
**Mitigation:** port `server.py` → `server.ts` **first**, before any other code.

**R13 — Multi-viewport edit ambiguity.**
Show one viewport and the user never sees breakage; show several and dragging in the 390 pane is ambiguous.
**Mitigation:** the pre-commit chip + overrides indicator. **⛔ Partial only — the underlying model is genuinely hard and no builder has made it easy.**

**R14 — Editor runtime fights the site runtime, so you never see the motion you're designing.**
Lenis lerps `scrollTop` every frame; GSAP transforms make `getBoundingClientRect` return animated positions. Disabling motion in edit mode is the only workable answer, and it creates the problem.
**⛔ No known mitigation for judging motion FEEL while editing.** The prior report's Data Gap 2 states motion verification is unvalidated end-to-end anywhere in the industry. The human-in-the-loop design does not solve this — **it moves the unsolved problem from an AI judge to a human who also has to be in preview mode to see it.** Partial: PREVIEW MOTION toggle, per-container scrub slider, trigger-point markers (§9.6).

**R15 — Generation determinism is load-bearing and fragile.**
Any nondeterminism makes `wb verify` produce false positives, users learn to ignore it, and the whole drift guarantee silently dies.
**Mitigation:** the four named hazards designed out up front (§12.8).

**R16 — Localhost is not a trust boundary.**
CVE-2025-24010 proves a malicious page in the same browser can reach a localhost dev server. Getting Origin validation and the bearer token wrong turns a design tool into a remote-code-drop.
**Mitigation:** the six-control posture (§12.12) plus the semantic-op wire format (§12.13).

**R17 — Step-3 is an unauthenticated code-import channel.**
Arbitrary code lands in `src/`, is evaluated by `astro dev`, and is bundled into the published site.
**Mitigation:** the validating importer with quarantine (§12.14).

**R18 — Scope: this is four products, and the third one is Webflow.**

| Layer | Effort | Notes |
|---|---|---|
| L1 interview + prompt generator | 2–4 days | A question tree + a template renderer |
| L2 ingest/validate/normalise + token compiler + font catalog + variants | 8–12 days | |
| **L3a editor-lite** (inline text, section reorder, variant swap, save, multi-viewport preview — **no canvas**) | 8–12 days | |
| **L3b editor-full** (canvas drag, anchors, snapping, layers tree, per-breakpoint overrides with provenance, free-position, undo, marquee select, keyboard nudge) | **30–60 days, and it never feels finished** | The Webflow-class layer. GrapesJS, Craft.js and Puck exist precisely because this is hard |
| L4 lock/export/publish/evidence | 3–5 days | |
| L5 custom components | ~5 days per family | |

**[I — anchored on the existence and maturity curves of comparable open-source projects and on Webflow/Framer/Editor X being multi-year multi-team products]**

**Smallest genuinely useful thing: L1 + L2 (single direction, not ten) + L3a + L4 ≈ 3–4 weeks, delivering ~80% of the value** — because the operations the user actually performs on a marketing site are "change this text," "move this section up," "try the other hero," "ship it." **Pixel-dragging is the operation they *think* they want because that is what a design tool looks like.**
**Mitigation:** sequence L3a before L3b with a **real decision gate** — build L3a, use it for one real site end to end, then decide.
**Scope tripwire, flagged not traded:** under schedule pressure the tempting shortcut is to drop the grid model and go flow-only, which **silently deletes Step-4(a) gridlines and Step-4(b) precise placement.**

**R19 — Editor/export divergence is a silent killer.**
Any CSS existing only because the editor is mounted (a wrapper, a stacking context, an overlay-induced scrollbar) makes the locked site differ from what was designed.
**Mitigation:** zero DOM injection + the screenshot-diff gate. **Without that gate it ships undetected.**

**R20 — Month six: the precedent already rotted.**
Unversioned tree, 30 opaque variant directories, no manifest, builder source in a job tmp **[V]**.
**Mitigation:** `git init` at Step 0; `provenance.json`; content mode; do-not-hand-edit banner; unlock diffs against the lock manifest; pinned versions + committed lockfile.

**R21 — The interview is where the user's time is spent worst.**
Enumerated honestly, the bank is 78 questions; at 30–60s each that is 40–80 minutes before a single pixel. Then direction review, then up to 400 potential component decisions. The prior report's own show-don't-MCQ finding and Iyengar/Lepper both argue against a long questionnaire and a 10-up grid.
**Mitigation:** three tiers; aggressive pre-fill from mined sources; the tournament instead of a grid; canonical variants pre-selected so 400 decisions is a ceiling nobody reaches.

**R22 — Undo across AI-driven mutations is where editors fracture.**
A naive per-mutation undo leaves a broken hybrid after one Cmd+Z.
**Mitigation:** single JSON-patch stack + transactional grouping + **dedicated test coverage for undo against AI actions specifically**.

**R23 — Third-party marks will be invented.**
Platform CTA badges, social icons, trust badges, press logos, map tiles.
**Mitigation:** flagged `[3P]` in the inventory as non-designable deterministic embeds; variants are arrangement only. **Generating a Steam button is a trademark violation.**

### 17.3 Medium

**R24 — Charts break coherence by construction.** A direction with 3 brand hues cannot yield a 6-series categorical palette that is on-brand, distinguishable and colourblind-safe. Mitigation: dataviz sub-tokens from generation time, not retrofit; v1 whitelist caps custom components; decide build-time-SVG vs client-library early.

**R25 — No layers panel would be fatal.** A full-bleed background art container sits on top of everything and swallows every click; nested containers cannot be clicked. **Added to v1 with its own effort line.**

**R26 — Step-0 warm start and Step-5 redesign pull in opposite directions.** Anchoring turns site 2 into a recolour of site 1, giving the user a house style they never chose — the prior report's sameness failure reproduced at personal scale, caused by the tool built to prevent it. Invisible until there are three sites. Mitigation: the system/identity split + negative constraints (§15.3).

**R27 — The editor caps the quality ceiling below what the interview promises.** A component bar swapping pre-generated variants into a grid **is** template assembly. The user gets a very good, very coherent, entirely unremarkable page and concludes the design system was bad. Mitigation: calibrate the language ("bespoke, coherent, hand-adjustable" is deliverable; "award-winning" by swap-menu is not); ship the custom code block; reserve one bespoke signature-moment slot.

**R28 — Ten directions do not automatically increase distinctiveness.** Without forced-divergence constraints all 10 regress to the mean and the user picks from a false-choice set. Mitigation: assign opposing-axis positions in advance (minimal↔maximal type, cool↔warm palette, geometric↔organic layout, static↔kinetic motion), make them visible in the pick UI, seed each with ≥3 references from different eras/genres, and enforce per-direction negative constraints.

**R29 — Eager variant generation stalls Step 4.** 10 × ~12 families ≈ 120 variants per direction. Mitigation: lazy on first panel open, cached per direction, never for unused families.

**R30 — Token count drives editor performance.** ~800 CSS custom properties per scheme re-evaluated on every drag is a real reflow cost. Mitigation: compile to a flat CSS-variable layer once per direction change, not resolved at edit time.

**R31 — Motion variants are the least verifiable part of the inventory.** VLM recall of aesthetic animation from frame sequences measured at 0.16. Ten text-reveal variants are ten things a screenshot cannot tell apart. Mitigation: acceptance rests on the human plus deterministic motion lint, **never on an automated visual score**.

**R32 — Two components are legally shaped, not aesthetically shaped.** Six pretty cookie-banner variants whose reject path is harder than accept is a compliance defect that looks like a design success.

**R33 — Undifferentiated variants reproduce the jam study.** Mitigation: the 200×120px indistinguishability rule.

**R34 — Artwork at 20 exceeds the safe presentation ceiling without filters.** Filter chips are not a nice-to-have; **they are what makes 20 legal.**

**R35 — The app-shell tail can colonise the interview and the budget.** 62 v3 items gated behind the site-type answer.

**R36 — Text pasted into contenteditable carries source-app markup**, survives LOCK, violates the token lint, and is invisible in the editor. Mitigated by `plaintext-only`.

**R37 — Skill duplication drift.** `acos-type-forge` already exists as two independent copies. Mitigation: symlink installer.

**R38 — Two servers means two ports, two origins, two things to forget to shut down.** A dev server left running for days is a more likely real-world exposure than a targeted attack. Mitigation: idle shutdown.

**R39 — Spring tokens are outside DTCG.** Every tool in the chain must agree on the extension shape or springs silently degrade to no motion.

**R40 — Native scroll-driven animations have no Firefox support without a flag.** A "native-first" strategy needs a real, tested GSAP fallback, not an assumed one, or a meaningful minority see static or broken reveals.

**R41 — Deploy is a second manual boundary.** If not automated, every future content edit ends in a dashboard drag-and-drop.

**R42 — The prior swarm architecture is seductive.** Phase agents, blind opus reviewers, Wigum loops, judge calibration — all well-documented, and there is a real risk of importing them wholesale and rebuilding the autonomous product the user explicitly rejected.

**R43 — Step-3 output is non-deterministic and the model drifts.** The same prompt in three months produces a different system. **The prompt is not a build artifact; it is a lottery ticket.** Mitigation: persist the RESULT as the artifact of record; store the prompt only for provenance; never plan to re-derive a system from a stored prompt.

**R44 — Transformed art containers trap dropdowns.** Near-certain given D4, presents as "the menu is behind the picture" with no obvious cause. Mitigation: encode the rule in the token file as Primer does, and lint for overlay-layer content nested inside transformed containers.

**R45 — A user can make a bad pick.** They may choose a direction already slipping toward saturation, and the system cannot override taste. Mitigation: freshness-based confidence scores and time-decay warnings ("this aesthetic peaked ~8 months ago"). **Never block.**

**R46 — A claude.ai usage-tier surprise.** Two-stage × N directions consumes meaningfully more messages than a single-prompt mental model implies. Surface it up front.

### 17.4 Open questions

| # | Question | Why it matters | How to answer |
|---|---|---|---|
| **O1** | **Does a claude.ai artifact actually render a Google Font, or does `font-src` block the WOFF2 and fall back silently?** | Determines whether typography can be judged on the web side **at all** | **60-second devtools test. Run before writing the Step-2 prompt spec** |
| **O2** | What is the real per-message and per-conversation output ceiling on the user's plan in practice — how many ~40KB direction artifacts fit before "maximum length"? | Sets the chunk size; the difference between 2 conversations and 12. **The figures found in 2026 SEO "guide" content were unverifiable and some model names appear fabricated — do not design around them** | Empirical test against the real product |
| **O3** | Does the user actually want free pixel dragging, or "move this section up" and "nudge this 12px"? | **A 40× effort difference** | **Build L3a and watch which operations they reach for. Do not answer by assumption in the PRD** |
| **O4** | Single-origin proxy vs two-origin iframe + postMessage — which is less total complexity once auth, SSE and HMR are wired? | Foundational | Spike both before locking the architecture |
| **O5** | Does the TS detached-spawn survive the turn boundary the way the Python double-fork does? | The language rule vs the only proven recipe | Same curl-across-turn-boundary test |
| **O6** | Is LOCK a re-render from `layout.json` or a copy-and-strip of the design surface? | **The single most consequential architectural decision in the eight steps.** The PRD recommends re-render; the FruitSync precedent is copy-and-strip and already required hand-rewriting links and hand-excluding dev pages | Settled here as re-render; confirm with the user |
| **O7** | Where does raster art come from for a project that does **not** own a sprite library? | Decides whether the art category is real or theatre. **Step 0's check should arguably be "does an asset library exist," because that is the binary** | User decision |
| **O8** | Does the built site target Astro, or plain HTML/CSS from a TS renderer? | The user's own estate (`website-design-okoa`) ships plain generated HTML with no framework — **far simpler to make live-editable and to LOCK cleanly** | Spike |
| **O9** | Canonical design-system format: forge's `design-system-spec.yaml` (existing validator, 883-line precedent) or DTCG tokens JSON (W3C-stable 2025.10)? | **Emitting BOTH from one importer is cheap and may be the right answer** | Decide at build |
| **O10** | Is multi-page in scope for v1, or one page? | Section reordering, swapping and LOCK are page-scoped; cross-page shared regions introduce a partials model and a change-once-changes-everywhere contract not in the eight steps. **Roughly doubles editor scope** | User decision |
| **O11** | Does a component appear with **different** variants on different pages, or is a variant choice global? | Per-instance overrides are more powerful **and are also how a design system stops being a system** | User decision |
| **O12** | Should the component bar show only the current direction's variants, or also the same component in the other 9? | The second is more useful for exploration and **directly undermines D1's coherence guarantee.** A product decision, not a technical one | User decision |
| **O13** | How many sites will this really build — one flagship, or a portfolio? | If one, warm-start machinery, provenance and registry are premature and that effort belongs in the editor. If a portfolio, identity-homogenisation becomes the top design problem | User decision |
| **O14** | Charts: static presentation (build-time SVG) or live/interactive (client library)? | The latter pulls in a dependency the performance gate must absorb | v1 default: build-time SVG |
| **O15** | Does "20 artworks" mean 20 individual pieces or 20 candidate **style sets**? | The inventory assumes sets for icons/illustrations/spots/patterns because 20 individual icons is not a design choice — **but 20 individual hero illustrations might be exactly what was meant** | User decision |
| **O16** | Should the skill persist a cross-project **taste profile** so repeat users fast-confirm the swipe-sort? | Speeds run N+1 without inheriting identity | v3 |
| **O17** | Is 24 the right reference-image count for the swipe-sort? | Starting point covering major style families without fatigue; **needs empirical tuning on real projects** | Measure |
| **O18** | Should the interview split across sessions, mirroring the 30–45-min-per-stakeholder multi-session pattern real design-system engagements use? | The user wants award-adjacent quality and might benefit from reflection time between Taste and Design-System waves | Offer as an option |
| **O19** | Is AA the contractual floor only, or should select AAA numbers (2.4.13 Focus Appearance, 2.3.3 Animation from Interactions) be adopted as aspiration? | | User decision, defaults to AA |
| **O20** | When WCAG-2 and APCA disagree on a borderline pair, show both numbers or collapse to one badge — and which is authoritative? | | WCAG 2 is the pass/fail gate; APCA is advisory |
| **O21** | Does "regenerate this section" call back out to claude.ai as another hand-carry, or run inline via the skill's model access? | Materially changes whether the feature is synchronous or another async hand-off | Inline, via Local Regeneration Mode |
| **O22** | Does Step-5 redesign fork the whole project into a variation branch, or replace in place with the old state recoverable only through version history? | Determines whether branching is a first-class user-visible feature | Fork — save-as-variation is v1 |
| **O23** | Should agent ops go through the inbox even when the editor is not running? | Direct writes are simpler but create two write paths and two validation paths | Inbox always |
| **O24** | What happens if the user opens the same session in two browser tabs? | `editor.lock` covers processes, not tabs | Tab claim over SSE, or a read-only second tab |
| **O25** | Ownership of `tokens.css` — machine-owned (regenerate) or hand-tunable? | Machine-owned is cleaner, **but the user will want to nudge a value at 11pm without regenerating the system** | Machine-owned + `extract-override` |
| **O26** | Should lock snapshots include the built `dist/` (large, self-contained, instantly re-servable) or only doc + system lock (small, needs a rebuild to view)? | Affects `.wb/locks` growth over many locks | Doc + lock only; dist is reproducible |
| **O27** | Does the user's claude.ai plan include Projects/custom instructions? | If so, the schema + worked examples could live there persistently instead of being re-stated in every Stage-B prompt, **substantially shrinking prompt bulk** | Ask in the interview |
| **O28** | How should the skill react to a bundle pasted from an **older** prompt-template version? | Schema drift across skill updates | `templateVersion` field checked against a supported range, with a defined upgrade/repair path |
| **O29** | Should snapping offer optical alignment (glyph edges, not box edges)? | Adobe holds patents specifically on snap guides relative to glyphs of editable text, which suggests naive box-edge alignment **looks subtly wrong on large display type — the exact place an award-adjacent site is judged** | v3 |
| **O30** | How and when does filmstrip/interaction-manifest motion QA get built and budgeted, given the prior report states it has no validated end-to-end precedent anywhere? | | Deferred; §17-R14 stands |

---

## 18. Phased delivery plan

### v1 — "Editor-lite, one direction, provably clean lock"

**Scope in:**
- Full interview (78 bank, three-tiered, ~35–45 answered), concept document, Step-0 warm start with asset-library detection
- Step-2 prompt generator (Stage A + Stage B) with the full return schema, font catalog, frozen token manifest, envelope + terminator
- **Local Regeneration Mode** (zero-paste path) alongside the claude.ai hand-carry
- Tolerant importer + validator + deterministic re-verification + repair-prompt emitter
- **ONE direction generated in full** (Stage A capsules for ~10 to choose from; deep-dive for the pick only)
- Token compiler → CSS custom properties + Tailwind `@theme`, pinned compiler
- `layout.json` / `content.json` model + pure renderer
- **Editor-lite**: inline text editing (`plaintext-only`), image replace + focal point + alt gate, section reorder, component-bar variant swap with hover-preview and typed slot contracts + content orphanage, navigator tree, undo/redo with transactional grouping, autosave + named snapshots + save-as-variation, multi-page manager, global regions, per-page SEO fields, in-editor preview mode, Design Health HUD with the v1 live checks
- Deterministic `variants.ts` (10 per component within the direction, lazy)
- **LOCK** with all five purity gates including two-build byte-equality, re-render not copy-strip, reversible
- Full lock-time gate suite (§13.4) with Tier-0/1 enforcement
- Evidence bundle + licence manifest
- Publish (or an explicit runbook, stated)
- `git init`, provenance, session state, resume
- Security posture: 127.0.0.1, Origin allowlist, bearer token, semantic ops, path allowlist, idle shutdown
- Double-fork server + fixed port + curl-across-turn-boundary verification
- `bun selftest.ts`

**Scope cut (explicit):**
- **No canvas drag.** No gridlines, no snapping, no free-position, no zoom/pan. Layout is section reorder + anchor verbs only.
- No per-breakpoint override authoring (author at 1280, auto-derive 768 and 390, override only where preflight complains)
- No rich-text block, no command palette, no rulers/guides, no multi-select/align/distribute
- No custom components beyond the whitelist
- No app-shell, commerce, or exotic-chart inventory
- No version diff, comment pins, share links, real-device preview
- Charts: build-time SVG only, ≤4 mark types

**Exit criterion:** *One real site built end to end with editor-lite, locked, published, with a complete evidence bundle and a passing two-build byte-equality check — and the user reports which operations they reached for that editor-lite could not do.*

That last clause is the decision gate for v2.

---

### v2 — "The canvas, if the gate says yes"

**Scope in (conditional on the v1 exit criterion):**
- **The real-grid canvas**: gridline overlay read from `getComputedStyle`, snap engine with priority ordering and tolerance ÷ zoom, smart guides with distance labels, drag-to-place writing grid integers, span resize with the "6 of 12 · 50%" readout, padding/gap handles snapping to the spacing scale, keyboard nudge and grid stepping
- **Per-breakpoint override cascade** with the persistent pre-commit chip, overrides dots, and reset-to-inherited
- **Free-position escape hatch** as anchored-offset, with the counter, auto-demote, and the hard LOCK gate
- Zoom + pan, drag-resizable frame, rulers, fraction-stored guides, multi-select + align/distribute
- Rich-text block (TipTap/ProseMirror, restricted mark set)
- Motion preview toggle, per-container scrub, trigger markers
- Real-device LAN preview
- **Content mode** (no dev server, no design layer)
- Per-section notes → scoped regeneration, regeneration log
- Version history: timeline, visual diff, non-destructive restore, crash recovery
- Command palette, find/search, breadcrumb navigation, rename, group/ungroup
- Live a11y/contrast lint inline, motion-property lint, text-spacing stress clone, off-token advisory
- Custom code block (the signature moment container)
- **All 10 directions generated** (Stage A ~10 capsules + Stage B for 2–3 shortlisted, tournament selection)
- Cross-direction swaps with the coherence-debt ledger and the switch-the-whole-site offer
- Charts: full 12 marks + chrome kit + data states, build-time SVG
- Registry for cross-site component/direction reuse
- Share-for-review read-only link, comment pins
- Second-ruleset Pa11y cross-check, conditional photosensitivity and motion-actuation gates

**Scope cut:**
- No app-shell inventory
- No interactive/client-library charts
- No multi-user editing
- No external raster-generation lane (unless O7 forces it)

**Exit criterion:** *A site with at least four free-positioned elements and per-breakpoint overrides passes the responsive preflight at 320/390/768/1280/1440 with zero blocking findings, and the free-position usage counter shows the user reaching for the escape hatch fewer than 3 times per section on average.*

That second clause is the instrumentation that tells you whether constraint dragging is actually working (R8).

---

### v3 — "Breadth, on demand"

**Scope in:**
- App-shell inventory (62 gated items) generated **only** when the site-type answer requires it
- Commerce inventory beyond pricing
- Exotic charts (scatter, heatmap, funnel, radar, waterfall, treemap, map) and interactive/client-library charts
- Canvas/WebGL and particle containers with the GPU-tier ladder
- Gaussian splat embeds
- 3D product viewer
- Cross-project taste profile
- Raw code export / eject, individual asset export
- Device-frame preview, jump-to-section nav
- PostToolUse evidence-mirror hook
- Optical alignment snapping (O29)
- Print state, RTL/bidi state (unless the interview forces it earlier)
- Auth/dashboard/settings/docs page templates

**Exit criterion:** *An app-shell site type completes the pipeline with every dashboard view screenshot-verified in populated, empty, loading and error states, and the performance budget still passes with the chosen chart runtime.*

---

## 19. Acceptance criteria

Testable statements. Each maps to a gate, a script, or an observable behaviour.

### Pipeline

| # | Criterion |
|---|---|
| A1 | Running the skill in a project with an existing `.acos/design-library/*/design-system-spec.yaml` offers it as a warm start within the first three exchanges |
| A2 | Step 0 detects an asset library when one exists at a path the user names, and records `assetLibraryPath` in `session.json` |
| A3 | The interview completes with ≤45 answered questions for a single-language, single-surface, no-forms marketing site |
| A4 | Every emitted design directive in the Step-2 prompt cites the interview question ID that produced it |
| A5 | The concept document names at least one thing the site refuses to do, and the pipeline refuses to advance to Step 2 without it |
| A6 | The generated Stage-A prompt contains: the DTCG worked example, the OKLCH-hue warning, the pinned font shortlist with base64 display cuts, the frozen token manifest, the CSP constraint, the 390px preview requirement, and the self-audit instruction |
| A7 | Pasting a **complete** chunk ingests with zero manual file operations beyond one `pbpaste` command |
| A8 | Pasting a **truncated** chunk fails with a message naming the missing files, and does not write a partial system |
| A9 | Pasting a chunk containing `fetch(` in a component quarantines that item, ingests the rest, and reports it in `import-report.json` |
| A10 | A contrast pair claimed as passing but actually failing is detected, auto-nudged, and logged in the substitution log |
| A11 | A font not on the pinned shortlist is substituted with the nearest OFL match in the same classification and logged |
| A12 | Local Regeneration Mode produces a bundle that passes the identical validator with zero pastes |
| A13 | `--resume` after a context reset reconstructs the phase from disk alone, with no reliance on conversation memory |

### Design system

| # | Criterion |
|---|---|
| A14 | Every token in a direction carries `com.acos.llm`, `com.acos.pick`, and `com.acos.direction` extension blocks |
| A15 | The editor renders **no control** for any token with `com.acos.pick.pickable: false` |
| A16 | A token whose `com.acos.direction.vectorHash` differs from the active direction is rejected by the builder |
| A17 | A direction with `elevation.model: border-only` that references any shadow token fails coherence lint 6 |
| A18 | The contrast proof table is all-pass by construction; any failure is reported as evidence of a hand-edited value |
| A19 | Both light and dark schemes are independently solved, and the proof table covers both |
| A20 | ≥60% of the 20 artworks in a generated set are token-referencing (`currentColor` / `var(--*)`) |
| A21 | Changing a direction's hue anchors re-skins all token-referencing artwork with no regeneration |
| A22 | Every motion item has a paired reduced-motion sibling, and the reduced-motion render diff shows a **difference** where motion exists |
| A23 | No custom cursor exceeds 128×128, and every `cursor: url()` declaration has a native keyword fallback |
| A24 | Spacing, type steps, radius scale, shadow scale, and semantic colour roles are all marked `derived` and have no editor control |

### Editor

| # | Criterion |
|---|---|
| A25 | A component can be selected via canvas click, via the breadcrumb, and via the Navigator tree — including a zero-height wrapper and an element fully covered by a background art container |
| A26 | Every drag operation has a single-pointer equivalent (select + click destination, or arrow-key nudge), satisfying WCAG 2.5.7 for the editor itself |
| A27 | Every editor-chrome control measures ≥24×24 CSS px, or satisfies a documented WCAG 2.5.8 exception |
| A28 | A padding drag commits to a named spacing token and displays the token name, never a raw pixel value |
| A29 | A component swap that removes a slot parks the orphaned content in a visible panel; swapping back restores it |
| A30 | A component swap that adds a slot creates a flagged placeholder that **blocks LOCK** until filled or deleted |
| A31 | A component swap is a **single** undo step; one Cmd+Z restores the prior variant completely with no hybrid state |
| A32 | A "regenerate this section" action is a single undo step |
| A33 | Hovering a variant in the component bar previews it live in the real slot with the current copy and neighbours |
| A34 | No two variants offered in the same bar are indistinguishable at 200×120px |
| A35 | Dropping a 4MB photo triggers auto-recompression with a visible, undoable confirmation |
| A36 | Placing an image without alt text or a decorative toggle **blocks the placement** |
| A37 | The Design Health HUD is the only surfacing channel for Tier-2 findings; no Tier-2 finding produces a toast |
| A38 | A component swap replaces the node **in place** in the DOM tree; the tab order before and after the swap is identical for equivalent content |

### Layout

| # | Criterion |
|---|---|
| A39 | The gridline overlay's track positions match `getComputedStyle(section).gridTemplateColumns` exactly |
| A40 | A drag commits an integer `grid-column` / `grid-row`, and the same block occupies 50% width at both 768px and 1440px when spanning 6 of 12 |
| A41 | A block with no small-breakpoint override compiles to `grid-column: 1 / -1` in source order |
| A42 | An edit made at 390px shows a pre-commit chip naming exactly which sizes it will affect |
| A43 | A free-positioned block auto-demotes to normal flow at ≤479px unless explicitly opted in |
| A44 | A free-positioned block that produces document `overflow-x` at any of 320/390/768/1280/1440 **fails LOCK** |
| A45 | A free-positioned block's parent does not collapse (reserved `min-block-size` applied at drop) |
| A46 | Component internals use `@container`, not `@media`; moving a card from a 6-col to a 3-col slot requires no manual fix |
| A47 | Snap tolerance divided by zoom keeps snapping usable at 25% and 200% |
| A48 | Free-position is unavailable by default on a scroll-driven pinned/scrubbed container, and forcing it requires an explicit confirmation |

### Lock and export

| # | Criterion |
|---|---|
| A49 | `grep -r 'data-wb-' dist/published/` returns zero matches |
| A50 | `grep -rE 'astro-dev-toolbar\|/@vite/client\|import.meta.hot\|data-astro-source' dist/published/` returns zero matches |
| A51 | A build with the editor integration installed and a build with it removed from `package.json` produce **byte-identical** `dist/published/` trees |
| A52 | A screenshot of the editor preview at 1280 with chrome hidden and a screenshot of the built page at 1280 differ by zero pixels |
| A53 | `wb verify` produces an empty diff on a freshly generated project, and on the same project after ten drag operations |
| A54 | LOCK writes only to `dist/published/` and `.wb/locks/<iso>/`; `pages/*.doc.json` mtimes are unchanged |
| A55 | UNLOCK is restarting the design server; no transformation is applied to the design project |
| A56 | `git checkout wb-lock/<n> -- pages/ site.json` restores a prior lock's documents without touching `src/overrides/**` |
| A57 | Every declared motion/interaction behaviour is present in `dist/published` (interaction-manifest check) |
| A58 | Unlocking after a hand-edit to the exported tree **shows the diff** rather than silently overwriting |
| A59 | LOCK produces `dist/` via write-to-new-dir-then-swap; no `rm -rf` is executed |

### Quality

| # | Criterion |
|---|---|
| A60 | The locked site renders at 320 CSS px with no two-dimensional scroll except exempted content |
| A61 | A 40-char unbroken token injected into any text block at 320px produces no overflow |
| A62 | +35% pseudolocalised strings produce no overflow or truncation on any page |
| A63 | 200% zoom produces no horizontal scroll and no content loss |
| A64 | A Playwright tab-walk reaches every interactive element, in visual order, with a visible focus ring at ≥3:1 against adjacent colours, and no trap |
| A65 | Full-page axe-core reports zero critical and zero serious findings |
| A66 | LCP ≤2.5s, CLS ≤0.1, and TBT ≤600ms on a median-of-3 mobile Lighthouse run under the documented Slow-4G profile |
| A67 | Pre-LCP transfer is ≤2MB |
| A68 | Every `@font-face` declares `font-display: swap`; exactly the committed families are preloaded; a fourth family introduced by a late swap **fails the gate** |
| A69 | Every page has a unique title, a 50–160-char description, a canonical URL, OG + Twitter tags with an image, a matching `lang`, a single H1 with no skipped levels, and 100% alt coverage |
| A70 | `robots.txt` and `sitemap.xml` are generated from the page tree, and JSON-LD validates against schema.org for the interview's site type |
| A71 | The site renders usably with JavaScript disabled: content visible, nav operable, forms submittable |
| A72 | The evidence bundle contains a licence class for every font and every asset, and says "passed N automated gates" — **never "WCAG AA compliant"** |
| A73 | The evidence bundle contains an explicit "manual and screen-reader review not performed" line |
| A74 | Any commercial-foundry font emits a pre-launch blocker rather than being embedded |
| A75 | No third-party mark (platform badge, social icon, trust badge, map tile) has been redrawn; all are used as supplied |

### Architecture and safety

| # | Criterion |
|---|---|
| A76 | The server binds `127.0.0.1` only; a request from a non-allowlisted `Origin` is rejected on every non-GET and on the SSE upgrade |
| A77 | A request without the session bearer token is rejected |
| A78 | The server writes only to `pages/*.doc.json`, `history.jsonl`, and `.wb/**`, verified by `realpath` + prefix assertion; a symlinked path is rejected |
| A79 | The wire format carries typed semantic ops; a raw JSON Patch or a file path in a request body is rejected |
| A80 | A `curl` to the server's health endpoint in a **separate tool call after the turn boundary** returns HTTP 200 |
| A81 | Claude's `Write` on `pages/*.doc.json` while the editor lock is held is blocked by the PreToolUse hook |
| A82 | A stale save (mtime/hash mismatch) is rejected with 409 and surfaces "reload or force" in the editor |
| A83 | `site/` is its own git repo, and `.acos/website-builder/sessions/*/site/` is in the ACOS `.gitignore` |
| A84 | All new code is TypeScript run by bun; `find` over the skill's `scripts/` and `app/` returns zero `.py` files |
| A85 | `bun selftest.ts` passes with 100% of assertions |
| A86 | Zero files are added to `.claude/agents/` |
| A87 | `Task` does not appear in the skill's `allowed-tools` |
| A88 | The skill is installed globally as a symlink to the git-tracked repo copy, verified by `ls -la ~/.claude/skills/ | grep acos-website-builder` showing `->` |
| A89 | No subagent calls `Write`; all agent-produced code returns as text and is written by the main thread |
| A90 | Phase 0 restates the understood brief and waits for an explicit confirmation before any file write or server launch |

---

## 20. Appendix

### 20.1 Deliberately excluded items, with justification

| Item | Surfaced by | Why excluded |
|---|---|---|
| **VLM aesthetic judge loop / Wigum iteration** | Prior swarm report; Lens 10 | The human replaces the judge by product definition. Porting it re-imports the rejected architecture (R42) |
| **CRDTs (Yjs, Automerge, Loro)** | Lens 4, Lens 6 | One human + one sequential agent. Concurrent multi-writer merge buys nothing and costs an opaque binary doc git cannot diff (§12.9) |
| **File System Access API as the persistence path** | Lens 6 | Chromium-only; Safari has no directory picker, Mozilla published a "harmful" position. Would silently be Chrome-only and still need a server fallback (§12.15) |
| **Building inside GrapesJS / Craft.js / Plasmic / Builder.io / Puck** | Lens 4 | Five distinct sufficient reasons (§16.10). Puck is closest and still fails on grid placement, breakpoint cascade, and React-vs-Astro |
| **New `.claude/agents/` files** | Lens 10 | Human-approval-restricted; `Task(general-purpose)` with prompts in the skill's own dir is the established zero-approval route (§16.5) |
| **`Task` in `allowed-tools`** | Lens 10 | `acos-skill-maker` doctrine says the framework ignores it. The estate contradicts itself; skill-maker is the authority |
| **Puppeteer via the npx-cache `NODE_PATH`** | Lens 10 | The cache can be evicted; ACOS's root `node_modules/` is empty. Chrome CLI is dependency-free and proven in-repo (§16.7) |
| **Copying `server.py` rather than porting it** | Lens 10 | Violates the standing TS/Rust rule; none of the three Python exceptions applies |
| **Per-state colour tokens (Carbon's ~60)** | Lens 2 | M3's 4 state-layer opacities replace them at ~7% of the generation cost, with equivalent coverage. Documented as a lens disagreement (§20.2) |
| **Carbon's ~90 syntax-highlight tokens** | Lens 2 | 12 roles suffice for a marketing site; the granularity is unnecessary |
| **60 pickable state-suffixed tokens in the editor** | Lens 2 | Replaced by a 22-item coverage checklist plus 4 derived opacities |
| **Ten "signature moment" variants** | Lens 3, Lens 8, Lens 11 | Treating the identity-carrying choice as a catalogue pick is the root homogenisation mechanism. 2–3 bespoke concepts instead (§14.7) |
| **Independent per-item picks for derived values** | D1 (settled) | The whole reason D1 was restructured. Enforced structurally via `pickable: false`, not documented (§7) |
| **A separate motion subsystem** | D4 (settled) | Motion is an ordinary system item; animated pieces share the art container (§9) |
| **App-shell inventory in v1** | Lens 3 | 62 items gated behind the site-type answer; including them makes the interview unbearable and the direction prompt unusable |
| **Interactive/client-library charts in v1** | Lens 3, Lens 5 | A charting runtime is real client JS on a static page and may undermine the performance gate. Build-time SVG in v1 |
| **Hard anti-slop blocking at the human-edit layer** | Lens 9, Lens 11 | Contradicts the product premise once a human has deliberately chosen. Demoted to Tier-2 advisory; the hard gate moves upstream to the design-system JSON (§13.8) |
| **Hick's law as justification for small variant sets** | Lens 3 | The wrong model for a feature-sorted thumbnail grid, which supports parallel visual search (§8.5) |
| **A 10-up direction grid** | Lens 12, Lens 11 | Thumbnail grids systematically favour loud, high-contrast directions over subtle editorial ones. Replaced by a tournament (§4 Step 4) |
| **Raw contenteditable on every text node** | Lens 4 | Browser-divergent Enter-key markup and Word-paste pollution. `plaintext-only` on ~90%, a real editor on one block type |
| **`ScrollSmoother`** | Lens 3 | Restructures the DOM. Lenis wraps native scroll so accessibility survives |
| **Loading a Lottie or Rive runtime for a hover effect** | Lens 3 | CSS/GSAP covers micro-interactions at zero runtime cost |
| **A JS router for page transitions** | Lens 3 | Breaks the back button. CSS `::view-transition` degrading to instant navigation instead |
| **Absolute positioning as the free-position implementation** | Lens 12 | Collapses parents and bakes in the authoring viewport. Anchored-offset instead (§11.4) |
| **Two independent layouts (Squarespace Fluid Engine model)** | Lens 4 | Documented overlap epidemic. Desktop-down cascade with sparse overrides (§11.3) |
| **DOM wrappers for hit-testing** | Lens 12 | Removing them at LOCK silently shifts layout via `>`, `:first-child`, and `gap`. Zero DOM injection (§11.9) |
| **HTML→JSON round-tripping** | Lens 6, Lens 12 | The canonical WYSIWYG failure, worse here because Claude also writes the source (§12.1) |
| **Deriving reduced-motion at build time by zeroing duration** | Lens 8, Lens 9 | Produces a broken-looking experience. Art-directed siblings authored at generation time (§7.7) |
| **Rust** | Lens 10 | Nothing here is performance-critical or needs a single binary; the language rule's own guidance says TypeScript |

### 20.2 Disagreements between lenses, and how they were resolved

| # | Disagreement | Resolution | Note |
|---|---|---|---|
| **1** | **Direction count.** Lens 11 argued 6 (Iyengar & Lepper: 6 outperforms 24 on both satisfaction and selection). D1 settled 10. | **10 generated, 6 surfaced by default in a tournament, 7–10 on "see more."** Respects the working-memory ceiling while honouring the settled decision. The tournament format (3 → pick → 3 → pick → head-to-head) is the actual mitigation, not the count |
| **2** | **Whether 10 variants causes choice overload.** Lens 3 said no — the 2015 Chernev meta-analysis found a near-zero mean effect with four engineerable moderators. Lens 11 said yes, citing the jam study. | **Lens 3's reading is correct and more recent**: the jam study is one of the 99 observations in the meta-analysis, and its effect appears specifically under the four moderators. **10 is safe when the moderators are engineered away** (§8.5) — but the 200×120px indistinguishability rule is Lens 11's insight and is retained |
| **3** | **State tokens: Carbon (~60 named) vs Material 3 (4 opacities).** | **M3's state-layer model.** 4 numbers vs 60 tokens, equivalent coverage, dramatically cheaper to generate. The 22-item coverage checklist supplies what Carbon's naming supplied |
| **4** | **Motion duration count: M3's 16 steps vs Carbon's 6.** | **Carbon's 6, scaled by expressiveness.** Carbon's productive/expressive axis IS the derivation D1 needs; M3's 16 is more granularity than a marketing site can use |
| **5** | **Hero variant count: 12 (Lens 3, market-calibrated to Tailwind Plus) vs 10 (D1 default).** | **12.** Hero, CTA band, card, badge, feature grid and pricing get 12; everything else Tier-A gets 10. The rubric double-weights the hero crop |
| **6** | **Typeface.mono: 5 (Lens 2) vs one-per-direction 10.** | **5.** Mono occupies a small, low-identity surface; five moods span it and directions map many-to-one |
| **7** | **Breakpoint authoring: 4 viewports vs "author at 1280, derive the rest."** | **Author at 1280, auto-derive 768 and 390, override only where preflight complains** — in v1. Full per-breakpoint authoring is v2. Each authored breakpoint multiplies the override surface the user must maintain |
| **8** | **Whether the anti-slop lint should be a hard gate.** Prior report said yes; Lens 9 and Lens 11 argued both sides. | **Split by layer**: hard gate upstream on the generated design-system JSON; Tier-2 advisory downstream at the human-edit layer (§13.8) |
| **9** | **CLS target: 0.1 (official Core Web Vitals "good") vs 0.05 (prior swarm report).** | **0.1 is the pass bar; 0.05 is an internal stretch target.** The prior report's number is stricter than the standard and should not become a failing gate |
| **10** | **Whether to include a layers/Navigator panel.** The product brief's Step-4 list omits it; Lens 4, 5 and 12 all independently said it is mandatory. | **Mandatory, v1, with its own effort line.** Canvas clicking provably cannot reach every node |
| **11** | **Editor server: one process or two.** Lens 6 recommended two (astro dev + wb-server) with a note to spike single-origin; Lens 10 implied one. | **Spike both (O4).** Two-origin is the shape Onlook/Stackbit/Tina converged on; single-origin collapses the CORS and postMessage surface to zero |
| **12** | **Whether the claude.ai hand-carry is mandatory.** The product brief treats it as the spine; Lens 7 and Lens 12 both argued it should be optional. | **Both ship in v1.** The hand-carry is the default because the user asked for it; Local Regeneration Mode is a first-class alternative because the hand-carry is the single biggest threat to the tool being used twice |
| **13** | **Effort estimate for the canvas.** Lens 12 gave 30–60 days for L3b; no other lens estimated. | **Adopted with the L3a-first decision gate.** The estimate is inference, but it is anchored on Webflow/Framer/Editor X being multi-year multi-team products, and on GrapesJS/Craft.js/Puck existing precisely because this layer is hard |
| **14** | **Artwork: 20 individual pieces or 20 style sets.** Lens 2 implied pieces for background/hero/spot; Lens 3 implied sets for icons/illustrations/patterns. | **Sets for icons, illustrations, spot graphics and patterns; individual pieces for background scenes and hero artwork.** Flagged as O15 because 20 individual hero illustrations might be exactly what the user meant |

### 20.3 Unverified claims and inference flags

Claims used in this PRD that were **not** independently verified, listed so they can be checked before implementation depends on them:

| # | Claim | Source status |
|---|---|---|
| **U1** | APCA guideline bands (Lc75 body, Lc60 large/bold, Lc45 large-non-text) | Inherited from the prior swarm report's Agent 01, which cited DesignChecker/APCA documentation. **Not independently re-verified this pass.** Use as a stretch target only; WCAG 2 remains the pass/fail gate |
| **U2** | claude.ai per-message and per-conversation output ceilings | 2026 SEO "guide" content gave specific figures and at least one model name that could not be corroborated and appears fabricated. **Explicitly flagged as low-confidence / possibly invented.** Chunk sizes must be set empirically (O2) |
| **U3** | The claude.ai React-artifact import allowlist contents | Commonly reported to include recharts, lucide-react and a Tailwind-like runtime, but not publicly versioned and subject to change. **Sidestepped entirely by targeting vanilla HTML** |
| **U4** | "One live artifact per turn" | Multiple 2026 third-party guides plus support.claude.com converge on the same description, but this is someone else's product surface and can change. Medium confidence |
| **U5** | Rive vs dotLottie runtime sizes (200KB vs 60KB) and payload deltas (50–80% smaller, 40–70% recovered) | Vendor and third-party comparison posts. Directionally reliable; exact figures medium confidence |
| **U6** | Canva's default vs advanced feature surface | Product knowledge, not independently searched this pass. Used only to support the "~30–35 of ~95 features is v1" argument, which stands on other grounds |
| **U7** | Webflow's reputation as the steepest-learning-curve no-code builder | Widely-repeated community commentary, not a primary source. Used to motivate the curated-property-set recommendation, which is independently supported by Framer's Stack abstraction |
| **U8** | The 45–90 minute hand-carry estimate | Inference, sized against first-party artifact counts (30 variant directories, 47 HTML files, 231 PNGs) and observed ~40KB artifact size. The **direction** is certain; the magnitude is estimated |
| **U9** | Base64 WOFF2 subset sizes (8–20KB raw, 11–27KB encoded) | Inference from typical Latin-subset display-face sizes. Verify against the actual catalog before committing to per-artifact budgets |
| **U10** | The ~250-artifact Step-2/3 payload count | Inference from D1 arithmetic against the inventory in §7–§8 |
| **U11** | The "~80% of value from L1+L2+L3a" claim | Inference from what operations a user performs on a marketing site. **This is the claim the v1 exit criterion is designed to test** |
| **U12** | Effort estimates throughout §17-R18 | Inference. Anchored on comparable-project maturity curves, not on measured work |
| **U13** | Style Dictionary v5 / Terrazzo 2.0 DTCG 2025.10 support status | Fetched from vendor docs; version states move quickly. **Re-verify at pin time** |
| **U14** | GrapesJS licence | GitHub API reports NOASSERTION; npm reports BSD-3-Clause. **Re-verify against the actual LICENSE file at pin time** — this discrepancy class is exactly what bites later |
| **U15** | The claim that jurors "recognise builder output instantly" | Prior swarm report Finding 2. Load-bearing for §17-R27's ceiling argument |
| **U16** | VLM recall of aesthetic animation from frame sequences = 0.16 | Prior swarm report Finding 15 / Data Gap 2. The prior report itself flags this area as unvalidated end-to-end |
| **U17** | 35.4% of adults 40+ have vestibular dysfunction | Prior swarm report. Used to motivate reduced-motion as a first-class requirement, which stands regardless of the exact figure |
| **U18** | "~75% of commercial pages launched Q1 2026 carry at least one strong AI-slop signature" | 925studios / Developers Digest analysis. The 1,590-page Show HN breakdown (22/32/46) is the better-sourced figure |
| **U19** | Adobe dynamic-guides patent details (bin selection, candidate segments) | USPTO 7545392 and 11250607/11967010 exist; the described algorithm shape is a reading of them, and the priority ordering and 1/zoom rule are this PRD's inference |
| **U20** | The specific Astro HMR add/remove-file limitation | Reported behaviour; **measure round-trip latency for a move op end to end before designing the editor's live-preview strategy** |

### 20.4 Things to verify before implementation starts

In priority order, all cheap:

1. **The claude.ai artifact font test** (O1) — 60 seconds, determines whether Step 2 can ask for base64 fonts or whether direction selection needs a different mechanism entirely.
2. **The TS detached-spawn turn-boundary test** (O5) — determines whether the language rule and the only proven server recipe can coexist.
3. **Copy-paste fidelity from claude.ai's rendered chat view** — whether triple-backtick fences survive. The entire `FILE:`-header contract depends on it. Test all three paste paths a real user would use (rendered view, per-block copy button, conversation export).
4. **Empirical claude.ai output ceiling** (O2) — sets chunk sizes.
5. **Astro HMR round-trip latency for a move op** (U20) — determines whether the editor needs an optimistic local preview layer.
6. **Single-origin vs two-origin spike** (O4).
7. **The GrapesJS-class licence re-verification at pin time** for every adopted dependency (dnd-kit, TipTap/ProseMirror) — against the actual LICENSE file, not the marketing page.