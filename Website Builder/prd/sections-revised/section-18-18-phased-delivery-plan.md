## 18. Phased delivery plan

### Vision deviations requiring sign-off — read this before approving any phase

The phasing below is **not** a neutral schedule. It cuts features the user named directly in the
authoritative 8-step vision. §17-R18 explains *why* the cut is proposed (a 40× effort difference
between L3a and L3b), but the reasoning was written as a risk note, not as a decision put to the
user. It is put to the user here.

**Nothing in v1 may be built until the sign-off column below is resolved.** Each row marked
**requires user sign-off** is a deviation from a settled brief, not a sequencing detail.

| Vision step | What the user asked for | v1 delivers | Deviation | Sign-off |
|---|---|---|---|---|
| **0** Warm start | Reuse a prior design system if one exists | **Full** — Step-0 warm start + asset-library detection (A2) | none | — |
| **1** Interview | Interview about site + design system | **Full** — 78-question bank, three tiers, ~35–45 answered | none | — |
| **2** Prompt generation | A prompt producing the whole design system (font, front animation, button, colour schema, cursor, background art/style, top ribbon, arts — "only examples") | **Full** — Stage A + Stage B, full return schema, font catalog, frozen token manifest, envelope + terminator | none | — |
| **3** Manual paste on claude.ai | User pastes, generates, hands everything back | **Full** — plus Local Regeneration Mode as a zero-paste alternative (§20.2 disagreement 12) | none | — |
| **4(a)** Gridlines for precise placement, removable later | Visible grid the user places against | **NOT DELIVERED in v1.** Deferred to v2 | **Yes — a named vision feature is absent from the first shipping version** | **requires user sign-off** |
| **4(b)** Drag-movable components | Direct manipulation of position | **PARTIAL — reorder only.** Section reorder + anchor verbs; no pointer-drag placement. Deferred to v2 | **Yes — D2 (constraint dragging) is *inert* in v1: the only version that ships first contains no dragging of any kind** | **requires user sign-off** |
| **4(c)** Editable text | Inline text editing | **Full** — `plaintext-only` inline editing on ~90% of text nodes; the rich-text block is v2 | Rich-text formatting (bold/link/list inside a paragraph) is v2 | **requires user sign-off (minor)** |
| **4(d)** Component bar — swap any component for a comparable variant | Swap surface across the system | **Full within one direction** — 10 variants per component (12 for hero/CTA band/card/badge/feature grid/pricing per §20.2 disagreement 5). **Cross-direction swaps are v2** because only one direction is generated in full in v1 | Only one direction exists in v1, so "swap to a different direction's version of this component" is not reachable | **requires user sign-off** |
| **4(e)** A way to save changes | Save | **Full** — autosave + named snapshots + save-as-variation + every-save-is-a-commit | none | — |
| **4(f)** "Whatever else research says a tool at this level needs" | Open-ended | **Substantially expanded in this revision** — navigator tree, asset library pane, recovery bin, element freeze, duplicate/paste with overrides, per-breakpoint visibility, per-section notes → scoped regeneration (all now v1; see the v1 list) | The v1 editor is still editor-lite: no canvas, no zoom/pan, no rulers, no multi-select | **requires user sign-off** |
| **5** If nothing looks good | Generate more variants, or a brand-new design-system prompt | **Full, plus the middle gear** — per-section notes → scoped regeneration is moved into v1 by this revision so the answer is not only "swap one variant" or "regenerate everything" | none (was a gap; closed below) | — |
| **6** Custom components (graphs, charts) | User-added components the tool would not normally include | **PARTIAL** — build-time SVG charts, ≤4 mark types, whitelist only. Full 12-mark chart kit and the custom code block are v2; exotic and interactive charts are v3 | A user who wants a scatter, heatmap or interactive chart in v1 cannot have one | **requires user sign-off** |
| **7** LOCK / unlock | Toolbars and gridlines removed, visitor view, reversible | **Full** — five purity gates, two-build byte-equality, re-render not copy-strip, reversible (D3). Note: v1 has no gridlines to remove, so the "gridlines disappear" part of the LOCK experience is vacuous until v2 | Consequence of the 4(a) deviation, not a separate one | covered by the 4(a) sign-off |
| **8** Publish + evidence bundle with every font and asset licence | Publish + licence evidence | **Full** — evidence bundle + licence manifest + publish (or an explicit runbook, stated) | none | — |

**R47 (new risk, continuing §17's numbering) — v1 ships without exercising D2 at all.**
D2 was negotiated specifically to make dragging safe. If v1 contains no dragging, the constraint
model's day-to-day usability is **unvalidated at the moment of first ship**, and §17-R8's concrete
friction scenario ("the hero headline 12px higher") is not encountered until v2 — after the
constraint machinery has already been designed around. **Mitigation:** the v1 exit criterion below
requires the user to report which operations they reached for and could not perform; that report is
the empirical input to the v2 canvas design (§17-O3). **This mitigation is partial, not complete —
it detects the problem late by construction, and there is no known way to validate a constraint
drag model without building a drag model. [I]**

---

### Cross-cutting decisions this section resolves (previously open)

Two items were simultaneously listed as committed v1 scope and as unresolved open questions. A PRD
cannot do both. They are resolved here, in the scope section, per the critics' instruction — one by
decision, one by an explicit branch that **requires user decision before build starts**.

**§17-O10 — multi-page in v1? — REQUIRES USER DECISION, and the decision must be made before the
v1 build starts, not during it.** This revision does *not* fabricate an answer. It removes the
contradiction instead: multi-page is listed in the v1 scope below as **PROVISIONAL (O10-gated)**,
and both branches are costed so the decision is a priced choice rather than an open item that
silently defaults to "yes" because it appeared in a bullet list.

| Branch | v1 contains | L3a effort (revising §17-R18) | Consequences |
|---|---|---|---|
| **Branch A — single page (recommended default) [I]** | One page. No multi-page manager. No global regions as a *shared partial* — header/footer are ordinary sections of the one page | **8–12 days** (§17-R18's published L3a figure, unchanged) | A69 (per-page SEO) is satisfied trivially by the single page; A70's `sitemap.xml` contains one URL and `robots.txt` is still generated — **neither acceptance criterion is weakened, they are simply scoped to a one-page tree**. §17-O11 (per-page variant divergence) does not become live at all in v1 |
| **Branch B — multi-page in v1** | Multi-page manager, page tree, global regions as real partials, change-once-changes-everywhere contract, cross-page variant consistency | **16–24 days [I]** — O10's own words are "roughly doubles editor scope"; doubling §17-R18's 8–12 is the only honest reading of that estimate, and it is **inference, not a measured figure** | Requires the global-regions contract to be written (below) **and** forces §17-O11 to be answered in v1, because a global region that renders a different variant on page 3 is not a global region |
| **Branch A+ — single page with a page-tree-ready data model (available at no extra cost) [I]** | Branch A, but `layout.json` carries a `pages[]` array of length 1 and every op is page-scoped from day one | **8–12 days + ~0.5 day** | Makes Branch B a v2 feature addition rather than a v2 data migration. **This is the recommendation if the user does not want to decide now.** |

**Global-regions contract (required only under Branch B, written here so Branch B is not
under-specified):** a global region is a named node subtree stored **once** in `layout.json` under
`regions[]` and referenced by id from each page's tree. Editing it anywhere edits it everywhere.
Per-page *content* overrides are forbidden in v1-Branch-B (that is what a section is for); per-page
*variant* overrides are forbidden pending §17-O11. Deleting a page never deletes a region. LOCK
in-lines each region into every page at export so no runtime include ships.

**§17-O7 — where does raster art come from? — resolved for v1 by lane scoping (below), and only
the residual case remains open.** See the artwork line in the v1 scope.

---

### v1 — "Editor-lite, one direction, provably clean lock"

**Scope in:**
- Full interview (78 bank, three-tiered, ~35–45 answered), concept document, Step-0 warm start with asset-library detection
- **Structural-RTL gate in the interview (new, v1):** one Tier-1 question — "will this site ever be published in Arabic, Hebrew, Farsi or Urdu?" — asked *before* the direction prompt is generated. A "yes" does not pull RTL layout work into v1 (that stays v3), it flips the pseudolocalisation and 200%-zoom state sets to mandatory and records the answer in `session.json` so v3's RTL work has a known starting point. **First-party rationale [V]:** FruitSync shipped an English-fallback Arabic workaround because multi-line RTL was discovered late, then needed a full redo (commits `060a9af`, `7dd7544` in this repo)
- Step-2 prompt generator (Stage A + Stage B) with the full return schema, font catalog, frozen token manifest, envelope + terminator
- **Local Regeneration Mode** (zero-paste path) alongside the claude.ai hand-carry
- Tolerant importer + validator + deterministic re-verification + repair-prompt emitter
- **ONE direction generated in full** (Stage A capsules for ~10 to choose from; deep-dive for the pick only)
- Token compiler → CSS custom properties + Tailwind `@theme`, pinned compiler
- **Logical properties only (new, v1 — hard constraint).** The token compiler and every generated component emit `margin-inline-start` / `padding-block-end` / `inset-inline` / `border-inline-start` and never `left` / `right` / `top` / `bottom` / `margin-left` / `text-align: left` in generated CSS. Enforced by **coherence lint 7 (new)**, which rejects physical direction keywords in generated CSS at ingest and at LOCK. **This amends §7.12 and §13 gate 4, which currently read "six coherence lints" — both must be updated to seven; flagged as a cross-section edit this section requires.** RTL *layout and mirroring* stay in v3 (see the v3 list); this line only makes reaching v3 cheap. **[I — that retrofitting logical properties is substantially more expensive than emitting them from the start is Lens 2's assessment, not a measured figure; the FruitSync redo is corroborating first-party evidence, not a measurement of this specific cost]**
- `layout.json` / `content.json` model + pure renderer
- **Section boundary markers (new, v1).** Every section node carries a stable `sectionId` that survives reorder, variant swap and regeneration. **Scoped regeneration accuracy depends entirely on clean boundaries**, so the markers are listed as their own deliverable rather than assumed
- **Editor-lite**: inline text editing (`plaintext-only`), image replace + focal point + alt gate, section reorder, component-bar variant swap with hover-preview and typed slot contracts + content orphanage, navigator tree, undo/redo with transactional grouping, autosave + named snapshots + save-as-variation, **multi-page manager (PROVISIONAL — O10-gated; present under Branch B, absent under Branch A / A+)**, **global regions (PROVISIONAL — O10-gated, same branch)**, per-page SEO fields, in-editor preview mode, Design Health HUD with the v1 live checks
- **Asset library pane (new, v1).** A left-pane searchable library of every uploaded and generated image, icon, pattern and art container, backed by `assets/manifest.json`, with **direction-affinity filter chips**. D1 tags 20 artworks by direction; that tagging is inert without a surface that reads it, and per-slot replacement gives the user no way to see what exists, reuse one asset across sections, or find the token-referencing subset that survives a direction change (A20/A21). The filter chips are also the mechanism §17-R34 names as "what makes 20 legal." Pattern precedent: the `acos-image-builder` left-pane parts library (§16.1)
- **Recovery bin (new, v1).** A persistent deleted-nodes panel backed by a `trash[]` array in the document, with **restore-in-place**. Undo alone cannot answer "I deleted that three edits ago" without also reverting everything since; §12.9's history model is an op log with inverse patches — a time machine, not a bin. A31/A32 cover swap and regeneration undo but not delete recovery. Cheap, because the op log already carries the inverse patch. Retention: unbounded within a project; the bin is stripped at LOCK by purity gate 1
- **Element freeze (new, v1) + the naming rule.** `node.locked` in the document schema, with a per-element freeze affordance that blocks drag, edit and swap on a settled node. **The UI copy for this action is "Freeze" (never "Lock"), because LOCK is this product's terminal publish verb and the collision is a guaranteed confusion source once both concepts exist in one product.** The rule — *element level says Freeze/Unfreeze; site level says LOCK/Unlock; no string in the product may use "lock" for the element concept* — belongs in §11 and in the glossary. Freeze matters even without a canvas, because reorder and swap can also disturb a settled section
- **Duplicate / copy / paste of a block including all its breakpoint overrides (new, v1).** Standard in every builder; it is what stops the user redoing responsive work on every reused block
- **Per-breakpoint visibility (new, v1).** Hide/show a block at a breakpoint, compiled to a `display` rule, **not** to duplicate markup. §20.1 explicitly rejects the two-independent-layouts (Squarespace Fluid Engine) model; rejecting the alternative without shipping the sanctioned mechanism leaves a hole. A lint warns when a block is hidden at *every* breakpoint
- **Per-section notes → scoped regeneration + regeneration log (moved from v2 into v1).** An in-editor note attached to a section ("this hero is too shouty, keep the type, calm the colour") that drives a scoped regeneration of that section only. This is the human-authored replacement for the autonomous VLM critique loop the user rejected (§20.1). Without it, v1's answer to vision Step 5 is only "swap a variant" or "regenerate the whole system" — **there is no middle gear.** It needs no canvas: it works on the section boundaries that reorder already requires. Mechanism is settled by §17-O21 — inline, via Local Regeneration Mode, not another hand-carry. A32 already requires a section regeneration to be a single undo step
- **Artwork — lane decision stated, not deferred (new, v1; closes the scope list's silence on the user's named "background art/style" category):**
  - **Lane A — code-drawn art: IN v1.** SVG scenes, CSS gradient meshes, canvas noise fields, generative patterns, all token-parameterised. **≥60% of the 20 artworks in a generated set must be token-referencing (`currentColor` / `var(--*)`) per A20**, and changing a direction's hue anchors must re-skin them with no regeneration (A21)
  - **Lane B — asset-library ingestion: IN v1.** Detected at Step 0 (A2, question C3), ingested into `assets/manifest.json` with direction-affinity tags and licence class. **This is the lane that actually made the cited FruitSync exemplar work [V — 231 PNGs exported from Unity by `SiteAngryExport.cs`, not produced in a chat]**
  - **Lane C — external raster generation (Midjourney / FLUX / Recraft): OUT of v1**, explicitly, with a named runbook shipped in the skill at `docs/lane-c-raster-runbook.md` covering the separate hand-carry, the per-asset licence manifest entries, and the ingest path. Lane C art that arrives via the runbook is ingested through Lane B's manifest, so nothing in the editor forks
  - **Residual open item — §17-O32 (new):** *for a project that owns no asset library and whose direction genuinely needs photographic or painterly raster art, who produces it?* Lane A cannot, Lane B has nothing to read, Lane C is out of v1. **Requires user decision per project.** The honest v1 answer is "that project either accepts code-drawn art, licences stock through the photo-grade recipe (§7.9 `art.photo-grade-recipe`), or runs the Lane C runbook manually." **No known mitigation that keeps the paste-only path intact.** §17-O7 is narrowed to this residual case and remains open
- **Component additions to the v1 inventory (four items the critics found with no v1 home).** Three of the four already carry a v1 tier in §8.3/§8.4; the other two need a tier change, which is an amendment to §8.3's tier column and is flagged as such:
  | Component | Variants | §8.3 tier today | v1 status here | Rationale |
  |---|---|---|---|---|
  | Third-party video facade | **4** | v2 | **Promoted to v1, conditional** — ships whenever the interview answers indicate any embedded third-party video | A naive YouTube/Vimeo embed costs ~500KB–1MB of pre-interaction third-party JS and can fail gate 20 by itself. **Amends §8.3 (v2 → v1-conditional); requires sign-off as a scope addition** |
  | Cookie / consent banner | **6** | v1 | v1 (confirmed, and now visible in the phase plan) | Legally required where the interview says personal data is collected; it is the first thing a visitor sees. §17-R32 names the risk that six pretty variants whose reject path is harder than accept is a compliance defect that looks like a design success — **reject-as-easy-as-accept is a hard constraint on all six variants, not a guideline** |
  | Cookie preferences centre | **3** | v2 | **Promoted to v1, conditional** — ships whenever the consent banner ships | A consent banner with no preferences surface is not a consent mechanism. **Amends §8.3 (v2 → v1-conditional); requires sign-off as a scope addition** |
  | Visible motion toggle | **3** | v1 | v1 (confirmed) | Required by the prior report's accessibility position **independent of** `prefers-reduced-motion`, because a visitor whose OS setting is off must still be able to stop motion |
  | Favicon / app-icon manifest set | **n/a — derived** from the logo mark: 16/32 ICO+PNG, `apple-touch-icon` 180, maskable 192 and 512, monochrome mask icon, `theme-color` for light and dark, `site.webmanifest` | v1 | v1 (confirmed) + **gate change** | Missing favicons are a classic AI-built-site tell. **§13.6 / gate 22 currently does not check them — favicon and web-manifest completeness is added to gate 22's checklist by this section** |
- Deterministic `variants.ts` (10 per component within the direction — 12 for hero, CTA band, card, badge, feature grid and pricing per §20.2 disagreement 5 — lazy)
- **LOCK** with all five purity gates including two-build byte-equality, re-render not copy-strip, reversible
- **LOCK also strips, and is gated on stripping:** the recovery bin, `node.locked` freeze flags, per-section notes, the asset-library pane and `assets/manifest.json` (the manifest stays in the project and in the evidence bundle, never in the published output). These are new editor-only state introduced above, and D3 requires no editor runtime or editor state reach a visitor
- Full lock-time gate suite (§13.4) with Tier-0/1 enforcement
- Evidence bundle + licence manifest
- Publish (or an explicit runbook, stated)
- `git init`, provenance, session state, resume
- Security posture: 127.0.0.1, Origin allowlist, bearer token, semantic ops, path allowlist, idle shutdown
- Double-fork server + fixed port + curl-across-turn-boundary verification
- `bun selftest.ts`

**Scope cut (explicit):**
- **No canvas drag.** No gridlines, no snapping, no free-position, no zoom/pan. Layout is section reorder + anchor verbs only. **This is vision Step 4(a) and Step 4(b) — see the sign-off table above. It is a deviation from the brief, not a sequencing detail, and D2 is inert in v1 as a direct consequence**
- No per-breakpoint override *authoring* (author at 1280, auto-derive 768 and 390, override only where preflight complains). **Note the deliberate asymmetry:** v1 *does* ship copy/paste-with-overrides and per-breakpoint visibility, because both operate on overrides the preflight already produced; what v1 lacks is a UI for authoring new ones freely
- No rich-text block, no command palette, no rulers/guides, no multi-select/align/distribute
- No custom components beyond the whitelist
- No app-shell, commerce, or exotic-chart inventory
- No version diff, comment pins, share links, real-device preview
- Charts: build-time SVG only, ≤4 mark types
- **No Lane C external raster generation** (runbook only, per the artwork line above)
- **No cross-direction swaps** — only one direction exists in full
- **No RTL layout or mirroring** — but logical properties are mandatory in v1, so v3's RTL work is an addition rather than a rewrite

**Revised v1 effort (amending §17-R18, which does not yet price the additions above) [I — every figure in this table is inference in the same class as §17-R18's own numbers, anchored on comparable open-source editors; none is measured]:**

| Line | §17-R18 as published | Delta from this section | Revised |
|---|---|---|---|
| L1 interview + prompt generator | 2–4 days | +0.25 day (the structural-RTL gate is one question) | 2.25–4.25 days |
| L2 ingest/validate/normalise + token compiler + font catalog + variants | 8–12 days | +0.5 day (coherence lint 7); +1–2 days (Lane A/B artwork ingest + `assets/manifest.json` with direction tags) | 9.5–14.5 days |
| **L3a editor-lite** — Branch A / A+ (single page) | 8–12 days | +0.5 day recovery bin; +0.5 day freeze; +1 day asset-library pane; +1 day duplicate/paste-with-overrides + per-breakpoint visibility; +1–2 days per-section notes → scoped regeneration + boundary markers; +0.5 day page-tree-ready model (Branch A+ only) | **12.5–17.5 days** |
| **L3a editor-lite** — Branch B (multi-page in v1) | not separately priced | O10's "roughly doubles editor scope" applied to the revised L3a | **~25–35 days** |
| **L3b editor-full** (v2 canvas layer) | 30–60 days, and it never feels finished | unchanged | 30–60 days |
| L4 lock/export/publish/evidence | 3–5 days | +0.5 day (favicon/manifest set into gate 22; stripping the new editor-only state at LOCK) | 3.5–5.5 days |
| L5 custom components | ~5 days per family | unchanged | ~5 days per family |

**Smallest genuinely useful v1 (Branch A+): L1 + L2 + L3a + L4 ≈ 28–42 days of the above lines**,
against §17-R18's published "≈ 3–4 weeks." **The published figure is now understated because this
section added scope; that is stated rather than hidden, and the additions are individually
listed above so any of them can be traded back out by the user.**

**Exit criterion:** *One real site built end to end with editor-lite, locked, published, with a
complete evidence bundle and a passing two-build byte-equality check — and the user reports which
operations they reached for that editor-lite could not do.*

**Additional v1 exit conditions added by this revision:**
- *The user has explicitly signed off, before build start, on every row marked **requires user
  sign-off** in the deviations table — in particular that v1 ships with no gridlines and no
  dragging.*
- *§17-O10 has been answered (Branch A, A+ or B) and the v1 scope list's PROVISIONAL markers have
  been resolved to present or absent.*
- *At least one section has been improved via the per-section note → scoped regeneration loop, so
  the "middle gear" answer to vision Step 5 is demonstrated and not merely listed.*
- *The published site passes gate 22 including the favicon / app-icon / web-manifest completeness
  check, and contains zero physical-direction CSS properties in generated output (coherence lint 7).*

That first clause — "which operations they reached for" — is the decision gate for v2.

---

### v2 — "The canvas, if the gate says yes"

**Scope in (conditional on the v1 exit criterion):**
- **The real-grid canvas**: gridline overlay read from `getComputedStyle`, snap engine with priority ordering and tolerance ÷ zoom, smart guides with distance labels, drag-to-place writing grid integers, span resize with the "6 of 12 · 50%" readout, padding/gap handles snapping to the spacing scale, keyboard nudge and grid stepping — **this is where vision Step 4(a) and 4(b) are actually delivered**
- **Per-breakpoint override cascade** with the persistent pre-commit chip, overrides dots, and reset-to-inherited
- **Free-position escape hatch** as anchored-offset, with the counter, auto-demote, and the hard LOCK gate
- Zoom + pan, drag-resizable frame, rulers, fraction-stored guides, multi-select + align/distribute
- Rich-text block (TipTap/ProseMirror, restricted mark set)
- Motion preview toggle, per-container scrub, trigger markers
- Real-device LAN preview
- **Content mode** (no dev server, no design layer)
- **Multi-page manager + global regions, if §17-O10 resolved to Branch A or A+** (under Branch B they shipped in v1). Branch A+ makes this an addition rather than a data migration
- ~~Per-section notes → scoped regeneration, regeneration log~~ — **moved to v1 by this revision.** What remains in v2: the **regeneration timeline UI** (browsing and comparing past regenerations of the same section) and **batch regeneration** across multiple noted sections in one pass
- Version history: timeline, visual diff, non-destructive restore, crash recovery
- Command palette, find/search, breadcrumb navigation, rename, group/ungroup
- Live a11y/contrast lint inline, motion-property lint, text-spacing stress clone, off-token advisory
- Custom code block (the signature moment container) — **this is where vision Step 6's "components not normally included" becomes fully open-ended**
- **All 10 directions generated** (Stage A ~10 capsules + Stage B for 2–3 shortlisted, tournament selection)
- Cross-direction swaps with the coherence-debt ledger and the switch-the-whole-site offer
- Charts: full 12 marks + chrome kit + data states, build-time SVG
- Video player skin (6) and background video loop (5) — the facade was promoted to v1; these two remain v2
- Registry for cross-site component/direction reuse
- Share-for-review read-only link, comment pins
- Second-ruleset Pa11y cross-check, conditional photosensitivity and motion-actuation gates
- **Freeze extended to the canvas**: `node.locked` blocks drag and marquee selection, not only edit and swap

**Scope cut:**
- No app-shell inventory
- No interactive/client-library charts
- No multi-user editing
- No external raster-generation lane (unless §17-O7 / the new §17-O32 forces it)
- No RTL layout/mirroring (v3) — logical properties continue to be enforced by coherence lint 7

**Exit criterion:** *A site with at least four free-positioned elements and per-breakpoint overrides
passes the responsive preflight at 320/390/768/1280/1440 with zero blocking findings, and the
free-position usage counter shows the user reaching for the escape hatch fewer than 3 times per
section on average.*

That second clause is the instrumentation that tells you whether constraint dragging is actually
working (§17-R8). **It is also the first empirical test D2 ever receives (R47), which is why it must
not be softened when v2 runs late.**

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
- Optical alignment snapping (§17-O29)
- Print state
- **RTL / bidi layout and mirroring** (unless the interview's structural-RTL gate forces it earlier). **Cheap to reach by construction**, because v1 mandated logical properties and coherence lint 7 has been rejecting physical properties since the first generated component. What v3 adds is bidi text handling, mirrored iconography and directional motion, **not** a CSS retrofit
- **Lane C external raster generation as a first-class lane** (if §17-O32 is answered in its favour), with its own licence manifest lane in the evidence bundle
- Auth/dashboard/settings/docs page templates

**Exit criterion:** *An app-shell site type completes the pipeline with every dashboard view
screenshot-verified in populated, empty, loading and error states, and the performance budget still
passes with the chosen chart runtime.*

---

### New cross-reference ids introduced by this section

Continuing the existing numbering; nothing is renumbered.

| Id | Type | Statement |
|---|---|---|
| **R47** | Risk (§17) | v1 ships without exercising D2 at all; the constraint drag model is unvalidated at first ship. Mitigation is partial and detects the problem late by construction **[I]** |
| **O31** | Open question (§17) | Which O10 branch — A (single page), A+ (single page, page-tree-ready model) or B (multi-page in v1)? **Requires user decision before the v1 build starts.** Both branches are costed above; no default is applied silently |
| **O32** | Open question (§17) | For a project with no asset library whose direction needs photographic or painterly raster art, who produces it in v1? **Requires user decision per project. No known mitigation that keeps the paste-only path intact** |
| **O33** | Open question (§17) | Final UI wording for the element-level freeze — "Freeze", "Pin", or another word. **The constraint is settled** (it must not be "Lock"); the word itself is cosmetic and **requires user preference** |
| **A91** | Acceptance criterion (§19) | The asset library pane lists every ingested and generated asset from `assets/manifest.json` and filters by direction affinity |
| **A92** | Acceptance criterion (§19) | A node deleted three or more edits ago is restorable in place from the recovery bin without reverting any intervening edit |
| **A93** | Acceptance criterion (§19) | A frozen node rejects edit, swap and reorder; and no user-visible string in the product uses the word "lock" for the element-level concept |
| **A94** | Acceptance criterion (§19) | Generated CSS contains zero physical-direction declarations; coherence lint 7 fails a component that emits one |
| **A95** | Acceptance criterion (§19) | A section's `sectionId` is unchanged after reorder, variant swap and scoped regeneration |
| **A96** | Acceptance criterion (§19) | Pasting a copied block reproduces all of its per-breakpoint overrides, not only its 1280 state |
| **A97** | Acceptance criterion (§19) | Per-breakpoint visibility compiles to a `display` rule with no duplicated markup, and a block hidden at every breakpoint raises a lint warning |
| **A98** | Acceptance criterion (§19) | Gate 22 fails a site missing any of: 16/32 favicon, `apple-touch-icon`, maskable 192 and 512, monochrome mask icon, `theme-color` for both schemes, `site.webmanifest` |
| **A99** | Acceptance criterion (§19) | A page containing a third-party video loads zero third-party JS before user interaction |
| **A100** | Acceptance criterion (§19) | In all six consent-banner variants, rejecting is reachable in no more interactions than accepting, and the preferences centre is reachable from the banner |
| **A101** | Acceptance criterion (§19) | No v1 evidence bundle contains a Lane C asset unless the Lane C runbook was invoked and every such asset carries a licence-manifest entry |

**Cross-section edits this section requires (flagged, not silently assumed):** §7.12 and §13 gate 4
change from six coherence lints to seven; §13.6 / gate 22 gains favicon and web-manifest
completeness; §8.3's tier column changes for the third-party video facade and the cookie
preferences centre (v2 → v1-conditional); §11 and the glossary gain the Freeze-vs-LOCK naming
rule; §12 gains `trash[]` and `node.locked`; §17 gains R47 and O31–O33 and marks O10 as branched
rather than open-ended; §19 gains A91–A101.

---

