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