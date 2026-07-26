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

