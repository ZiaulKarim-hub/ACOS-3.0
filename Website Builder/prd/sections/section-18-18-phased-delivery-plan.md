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

