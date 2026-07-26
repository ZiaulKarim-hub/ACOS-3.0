## 10. Step 4 — the editor: full feature set

Grouped by function. **One Priority column, and it is now derived mechanically from §18** (see §10.10 for the method and the full count reconciliation) — the pre-reconciliation draft's priority tags disagreed with §18's phase plan on roughly a seventh of the rows, and §18 is the phase plan actually used to scope and staff a build, so §18 wins every disagreement. Every row whose priority changed as a result carries an inline **"Reconciled with §18"** tag naming the old value; rows with no tag were already consistent and are unchanged.

Mechanical recount of the pre-reconciliation draft (before this revision touched it): **113 rows, 71 v1 / 37 v2 / 5 v3.** The draft's own prose claimed "~35 of ~95 items are v1" — off by roughly 2× on the v1 count and ~19% on the total. This revision does not delete or shorten any pre-existing row; it corrects priorities in place and **adds 3 new rows** where a gap could only be closed by splitting a feature into a v1-scoped slice and a v2/v3 full slice (§10.1 per-breakpoint override, §10.3 custom-component insertion, §10.3 chart data). That brings the table to **116 rows**. Under the §18-reconciled priorities: **56 v1 / 55 v2 / 5 v3** — see §10.10 for the per-subsection breakdown and for every row whose priority moved.

Canva — explicitly built for non-designers — ships by default only canvas + snap, layers, undo, basic text/image editing, one-click template swap, and a share link. Grids, rulers, breakpoint cascades, version diffing and comment pins are hidden or absent. **[U — product knowledge, treat as inference]** Under the reconciled v1 scope this comparison reads differently than in the pre-reconciliation draft: v1 here has **no canvas drag, no gridlines, no snapping at all** (§18's explicit v1 cut) — which is *more* restrained than Canva's snap-enabled canvas, not less. The v1/v2 split in this table should be read as "editor-lite first, canvas second," matching §18's own framing, not as "everything in one release."

### 10.1 Layout & placement

**Breakpoint sets used throughout this section** (adopted from §11's own revision, not re-derived here, so the two sections state one set instead of two): **authoring breakpoints 390 / 768 / 1280 / full**, with pinned device heights 390×844 / 768×1024 / 1280×800 whenever the page contains a `vh`/`svh`/`dvh` rule (§11.7); **verification/detection breakpoints 320 / 390 / 768 / 1280 / 1440** (§11.8, §10.8 below); **free-position auto-demotion at ≤390px** (§11.4 rule 4, revised down from the pre-reconciliation draft's 479px, which no switcher, iframe, or gate in the product ever actually renders). §10.8's Hard LOCK gate additionally renders 1440 (§11.4 rule 6: "render at 390/768/1440"). **Open item, no known mitigation beyond what's stated here:** 1440 is checked by the Hard LOCK gate and by the Responsive preflight report (§10.8) but is **not** one of the switcher's own preview options below, so a user cannot live-preview a 1440-only failure while editing — they discover it only via the preflight report or at LOCK itself. Adding 1440 as a fifth switcher option is a plausible fix but is not decided here; **requires user decision.**

| Feature | Priority | Notes |
|---|---|---|
| Real-grid overlay (gridlines) | v2 **(Reconciled with §18 — was v1)** | **Drawn by reading `getComputedStyle(section).gridTemplateColumns`** and painting those exact resolved tracks. Never decorative — it is the snap target, and it lives in the out-of-iframe overlay so it disappears at lock by construction. §18's v1 scope cut states "No canvas drag. No gridlines, no snapping, no free-position, no zoom/pan" outright; §18's v2 scope-in restates it as "the real-grid canvas: gridline overlay read from `getComputedStyle`" |
| Snap engine | v2 **(Reconciled with §18 — was v1)** | Two 1-D interval indexes per section over four prioritised target classes: grid lines > sibling edges/centres > section padding & content rails > spacing-scale increments. Tolerance 6–8 CSS px **divided by zoom** — a classic regression if missed. Moves with the grid overlay per §18's v1 cut |
| Smart alignment guides + distance labels | v2 **(Reconciled with §18 — was v1)** | Dashed guides + live gap measurements in the accent colour; equal-spacing indicators when 3+ siblings match. §18 v2 scope-in names this explicitly: "smart guides with distance labels" |
| Align tools | v2 **(Reconciled with §18 — was v1)** | left/centre/right/top/middle/bottom, relative to siblings or parent. Bundled with Distribute tools (already v2) under §18 v2's "multi-select + align/distribute" |
| Distribute tools | v2 | Equalise gaps across 3+ selections, operating on **grid integers**, not pixels. Unchanged — already consistent with §18 |
| Padding / gap drag handles | v2 **(Reconciled with §18 — was v1)** | Draggable inner edges snapping to **discrete spacing-scale steps only**, showing the token name (`space-6`), never a raw pixel value. **This is the mechanic that stops direct manipulation destroying the token system** — no commercial builder does it. §18 v2 scope-in names it explicitly: "padding/gap handles snapping to the spacing scale" |
| Drag-to-place (grid write) | v2 **(Reconciled with §18 — was v1)** | Ghost preview follows the pointer continuously; commit writes `{col, colSpan, row, rowSpan}` integers for the active breakpoint (per §11.2.1's drop algorithm, once §11's revision ships). Pointer capture on the overlay so the drag survives leaving the iframe. §18 v2 scope-in: "drag-to-place writing grid integers." **v1 has no canvas drag at all**, so v1 layout changes go through §10.2's Navigator tree and this table's Anchor/pin control only |
| Span resize | v2 **(Reconciled with §18 — was v1)** | Edge handles change span in whole cells with a live "6 of 12 · 50%" readout so the user learns the fluid consequence. §18 v2 scope-in: "span resize with the … readout" |
| Section reorder | v1 | Vertical only, via the Navigator or a section rail. Sections are never dragged horizontally. Confirmed v1 by §18's Editor-lite scope-in: "section reorder" |
| Breakpoint switcher | v1 **[I — not itemised by name in §18; kept v1 by inference]** | 390 / 768 / 1280 / full, with **pinned device heights** (390×844, 768×1024, 1280×800) whenever the page contains any vh/svh/dvh rule. §18 does not name a "breakpoint switcher" in either its v1 or v2 lists. Kept v1 on the reasoning that it is a plain iframe resize (no dependency on the real-grid canvas, snap engine, or per-breakpoint override authoring, all of which are v2), and v1 needs *some* way to view the auto-derived 768/390 renders before running the Responsive preflight report (also v1) or acting on one of its findings. This is an inference, not a §18 citation — **flagged for confirmation when §18 is next updated** |
| Per-breakpoint override — scoped exception only, preflight-triggered | v1 **(new row, added to close a gap)** | The one authoring path §18's v1 cut explicitly leaves open: "override only where preflight complains." When the Responsive preflight report (v1, §10.8) flags a specific node at a specific breakpoint, the editor offers a single scoped fix limited to that node/breakpoint pair — not the general cascade UI below. No dot indicator, no "reset to inherited" browsing UI; this is a narrow, gated escape valve, not authoring |
| Per-breakpoint override + reset-to-inherited (full cascade UI) | v2 **(Reconciled with §18 — was v1; split into the scoped-exception row above)** | Desktop-down cascade with sparse overrides, browsable at any breakpoint. Every overridden property shows an "overridden here" dot and a one-click reset. §18's v1 cut: "No per-breakpoint override authoring (author at 1280, auto-derive 768 and 390, override only where preflight complains)" — the general browsing/authoring UI described here is exactly what that cut removes; the exception clause is the new row above |
| Anchor/pin control | v1 | The core D2 primitive. **Three verbs only**: align to (left/centre/right/stretch), space above/below (stepper over the scale), order (up/down among siblings). Confirmed v1 — this is the row §18's v1 scope cut is describing verbatim: "Layout is section reorder + anchor verbs only" |
| Free-position escape hatch | v2 | See §11.4 (as revised: anchor restricted to parent/grid-cell only in v1 scope, auto-demotes at ≤390px). Deliberately v2 so the safe path ships and is proven first. Unchanged — already consistent with §18's "free-position escape hatch as anchored-offset" v2 listing |
| Type-aware resize | v1 **[I — not itemised by name in §18; kept v1 by inference]** | Text reflows at fixed font size; images rescale aspect-locked; inline SVG rescales losslessly; tables scale uniformly with a separate per-column handle. **Reusable prior art from the ACOS HTML-to-PDF Visual Composer vision.** §18 doesn't name this row, but v1's own auto-derive behaviour ("author at 1280, auto-derive 768 and 390") has nothing else in this table governing how content *inside* a block reflows when that auto-derivation resizes it — without this row, v1's auto-derived breakpoints would have undefined content behaviour. Kept v1 on that basis; this is inference, not a §18 citation |
| Canvas zoom + pan | v2 | 25–200%, snap tolerance ÷ zoom, space-drag pan. Deferred because a fixed-viewport iframe is usable without it. Unchanged — already consistent with §18 |
| Drag-resizable canvas frame | v2 | Stress-test reflow at in-between widths (catches breakage at, say, 610px). Unchanged — already consistent with §18 |
| Rulers | v2 | Unchanged — already consistent with §18 |
| Custom drag-out guides | v2 | **Stored as fractions of the content-width rail, not pixels**, so they survive breakpoint switches. Unchanged — already consistent with §18's "fraction-stored guides" |
| Flex/grid container controls | v2 | Direction, gap, wrap, justify/align as icons and steppers, never raw CSS. Unchanged — not named individually by §18 but bundled with the rest of the v2 canvas surface it depends on |
| Keyboard nudge & grid stepping | v2 **(Reconciled with §18 — was v1)** | Arrow = one cell, Shift+arrow = span ±1, Tab walks siblings. §18 v2 scope-in names this explicitly: "keyboard nudge and grid stepping." **This is also the WCAG 2.5.7 single-pointer alternative for drag (§13.2)** — moving it to v2 alongside the canvas drag it is the alternative *for* is actually self-consistent: v1 has no canvas drag at all (anchor verbs are click/stepper-based and need no pointer alternative), so the alternative isn't needed until the drag mechanism it substitutes for ships. **Verify §13.2's gate wording doesn't assume this alternative exists in v1** before v1 ships — that check is outside this section's authority |

### 10.2 Structure & selection

| Feature | Priority | Notes |
|---|---|---|
| Selection overlay + handles | v1 | Drawn **outside the iframe** with `pointer-events: none`, so no editor node ever enters the exported DOM |
| Drill-in / drill-out selection | v1 | Click = nearest top-level block; Enter/double-click descends; Esc ascends. Hit-test via `elementFromPoint` inside the iframe, walking up to the nearest `[data-wb-node]`. **Known edge: `elementsFromPoint` does not return the iframe when something is fullscreened over it — never fullscreen the canvas while editing** |
| Breadcrumb ancestor bar | v2 **(Reconciled with §18 — was v1)** | Ancestor chain under the canvas, selected element rightmost, every entry clickable. §18 v2 scope-in names "breadcrumb navigation" alongside command palette, find/search, rename, group/ungroup — none of which are in v1's Editor-lite list |
| Navigator / layers tree | v1 | **Non-optional.** Canvas clicking provably cannot reach zero-height wrappers, covered elements, `pointer-events: none` decoration, or empty slots. Webflow ships all three selection channels for exactly this reason. A full-bleed background art container will otherwise swallow every click. Confirmed v1 — §18's Editor-lite scope-in names "navigator tree" explicitly |
| Drag-to-reorder / reparent in tree | v2 **[I — not itemised by name in §18; demoted by inference]** | The only reliable way to fix z-order or nesting without canvas gymnastics. §18's v1 cut is "no canvas drag," and while this is tree-UI drag rather than canvas drag, **v1's actual reorder need is already covered by the Section reorder row (§10.1, v1, "via the Navigator or a section rail")** — that only requires list-reorder-by-button/drag within the tree at the section level, not general arbitrary-node reparenting. Demoted the general case to v2; the section-level case remains v1 via the row above. This split is inference, not a §18 citation |
| Hide/show toggle per layer | v1 | Cheap, no canvas-drag dependency |
| Rename layer/component | v2 | Makes the tree navigable at 50+ elements. Unchanged — already consistent with §18's v2 "rename" |
| Multi-select | v2 **(Reconciled with §18 — was v1)** | Shift-click, marquee, select-all-of-type. §18's v1 cut states "no multi-select/align/distribute" outright; §18 v2 scope-in restates it as "multi-select + align/distribute" |
| Group / ungroup | v2 | Unchanged — already consistent with §18's v2 "group/ungroup" |
| Element lock | v1 | Prevents accidental move/resize/delete. **Must use a different verb from the site-wide LOCK** — "Lock Element" vs "Publish" / "Preview as Visitor". Two "lock" concepts sharing vocabulary is a real confusion risk |
| Duplicate with smart offset | v1 | |
| Cut/copy/paste incl. paste-to-replace | v1 | Clipboard round-trip as **`pages/<id>.doc.json`** fragments **[renamed — see §10.4's file-naming note]** **including all breakpoint overrides** |
| Delete with recovery bin | v1 | **Independent of the undo stack** — "I deleted this three edits ago" is common and chaining undo back would revert everything since |
| Global/shared component with instance overrides | v1 | **A prerequisite for safe variant swapping, not optional plumbing.** Without it, either every page-level edit drifts independently or every system-level edit needs manual re-application. Build this data model **before** the component-bar UI |
| Section boundary markers | v1 | Visible wrapper boundaries so "regenerate this section" has an unambiguous target. **Independently justified for v1 even though per-section regeneration itself is now v2** (§10.7): section boundaries are also what Section reorder (v1) and the Navigator tree (v1) need to show the user an unambiguous structure, so the row stays v1 on that separate basis. **A fuzzy boundary lets regeneration leak into neighbouring content** once regeneration does arrive in v2 |
| Per-breakpoint visibility | v2 **[I — not itemised by name in §18; demoted by inference]** | Compiled to a display rule, not duplicate markup. Lint warns if hidden at every breakpoint. §18's v1 cut is a blanket "no per-breakpoint override authoring," and a visibility toggle is a form of per-breakpoint override even though it's cheaper than the full cascade UI. Demoted to v2 on that basis; this is inference, not a §18 citation, and a case could be made for keeping a "hide on mobile" toggle in v1 as a low-cost exception similar to §10.1's scoped-override row — **not decided here, open for reconsideration** |

### 10.3 Content

**Sign-off note — Custom-component insertion and chart data, read before implementing either row below.** §18's v1 scope cut removes "custom-component insertion" entirely, and separately ships "Charts: build-time SVG only, ≤4 mark types" in v1. Taken literally, v1 renders charts nobody has any way to place, because placing a component the base direction doesn't already include is exactly what "custom-component insertion" means. Charts are also the user's own named example for Step 6 ("the user may add custom components not normally included — for example graphs or charts" — see the vision's Step 6). Shipping charts with no insertion path in v1 would silently cut a capability the user named. **This revision proposes closing that hole with a v1 slice narrower than the cut §18 states — see the two new/split rows below — and that narrowing is a deviation from §18's literal text that REQUIRES USER SIGN-OFF before implementation**, distinct from the ordinary priority reconciliations elsewhere in this section.

| Feature | Priority | Notes |
|---|---|---|
| Inline text editing (tier 1) | v1 | **`contenteditable="plaintext-only"`** on headings, eyebrows, buttons, nav items, labels, stat numbers — ~90% of a marketing page's text nodes. Strips all paste formatting, avoids cross-browser Enter-key markup divergence, and prevents Word markup entering an award-grade type system. Baseline newly-available **[V — web.dev, caniuse]** |
| Rich-text block (tier 2) | v2 | ProseMirror/TipTap (MIT) on **long-form prose blocks only**, restricted to an approved mark set (bold, italic, link, list, blockquote) — no font/colour/size controls. Unchanged — already consistent with §18's v2 "rich-text block" |
| Plain-text swap mode | v1 | Editing a token-bound label changes only the string, never the styling |
| Image replace | v1 | Keeps container size/crop/position intact. Confirmed by §18's Editor-lite scope-in: "image replace" |
| Image crop + focal-point picker | v1 | **A single draggable dot, not a crop rectangle.** A single 2D point degrades gracefully across every container aspect ratio a reflow system produces; per-breakpoint manual crops do not. **Direct prior art from the ACOS HTML-to-PDF Visual Composer vision.** Confirmed by §18's Editor-lite scope-in: "focal point" |
| Alt-text field | v1 | Required-nudged; placing any image opens a micro-field for alt text **or an explicit "decorative" toggle**. Blocks the placement, not just the lock. Confirmed by §18's Editor-lite scope-in: "alt gate" |
| Asset/media manager | v1 | Searchable library tagged by which direction each asset suits |
| Component-bar variant swap | v1 | Core Step-4d feature. See §8.5 for presentation rules and §10.8 for the coherence contract. Confirmed by §18's Editor-lite scope-in: "component-bar variant swap with hover-preview and typed slot contracts + content orphanage" |
| Variant hover-preview before commit | v1 | Ghost-previews live in the actual page context (current copy, current neighbours). **Essential, not nice, once there are 10 variants** — an isolated thumbnail can't show fit. Confirmed by §18 (bundled with the row above) |
| Icon picker | v2 | Unchanged |
| Embeddable content blocks | v2 | Video, maps, forms. Unchanged |
| Custom-component insertion — minimal whitelisted registry (table, chart, embed, form) | v1 **(new row — see the sign-off note above this table)** | Placement only, from a **fixed catalog of four component kinds sourced from the system library**, no arbitrary Step-6 code, no free-form "insert anything." This is the minimal path that lets a v1 site actually place the chart component the next row and §14.6 both assume exists. **Requires user sign-off** — see the note above the table |
| Custom-component insertion — full Step-6 authoring | v2 **(renamed from the original "Custom-component insertion" row; Reconciled with §18 — was v1, i.e. undifferentiated)** | Free-form addition of components not in the base registry, arbitrary Step-6 custom code, per-section notes-driven generation of new component types. §18's v1 cut ("no custom-component insertion") applies in full to this row; only the minimal registry row above is proposed as a v1 exception |
| Minimal chart-data field (CSV/table paste bound to a chart node's props) | v1 **(new row — see the sign-off note above this table)** | A single paste-a-table-of-numbers field wired directly to the chart component's data prop. Not a spreadsheet: no formulas, no multi-sheet, no cell formatting — just the minimum surface that lets a v1 SVG chart (§18: "build-time SVG only, ≤4 mark types") receive real data instead of shipping with placeholder numbers. **Requires user sign-off** — see the note above the table |
| Table/data editor for charts (full spreadsheet-grade) | v3 | Lightweight spreadsheet backing any chart. **Relationship to the row above:** this is the eventual replacement for the v1 paste field, not a second unrelated feature — the v1 field's data model should be a strict subset of this editor's, so upgrading doesn't require a migration |
| Link field with validation | v1 | href + URL validation + `target=_blank` toggle |
| Site-wide link manager | v2 | Every internal and external link with destination and status |
| Per-page SEO/meta fields | v1 | Title, description, OG image, favicon. Confirmed by §18's Editor-lite scope-in: "per-page SEO fields" |
| Multi-page manager | v1 | Add, duplicate, delete, reorder. Confirmed by §18's Editor-lite scope-in: "multi-page manager" |
| Site-wide global regions | v1 | Header/footer/nav edited once, reflected everywhere. Confirmed by §18's Editor-lite scope-in: "global regions" |

### 10.4 History & persistence

**File-naming note (applies to every row below and to §10.2's clipboard row above).** The pre-reconciliation draft referred to the persisted scene graph as `layout.json` throughout this subsection. §12.2's file set has no `layout.json` — the canonical scene graph is **`pages/<id>.doc.json`, one file per page** — and §12.13's write allowlist only permits writes to `pages/*.doc.json`, `history.jsonl`, and `.wb/**`. This revision renames every reference in this section to `pages/<id>.doc.json` to match §12.2/§12.13. **§4, §11, §12.6 and §12.10 still say `layout.json` as of this revision** (verified by grep at the time of writing) — those are outside this section's edit authority, so this is flagged here as a required follow-up rather than silently fixed everywhere. **Open question, no known mitigation beyond flagging it:** whether the command stack, op log, and editor lock below are scoped **per-page** (one stack per `doc.json`) or **site-wide** (one stack spanning all pages, keyed by page id) is not stated anywhere in §10 or §12 as of this revision. Since multi-page management is v1 scope (§10.3), "undo an edit on a page I've since navigated away from" is a real v1 scenario with no defined behaviour today. This revision's inference/recommendation (not yet ratified): **a single site-wide command stack keyed by page id**, so cross-page undo has an answer — but ratifying this requires a matching update to §12.9 (which currently describes `history.jsonl` without stating its scope) and is outside this section's authority to make binding.

| Feature | Priority | Notes |
|---|---|---|
| Undo / redo | v1 | **A single JSON-patch command stack** over **`pages/<id>.doc.json`** (renamed — see the file-naming note above), covering canvas drags, inspector edits and text edits alike, so the surfaces cannot desync. Split stacks are a classic confusing regression. Coalesces a continuous drag into one entry. **The client-side stack mirrors, rather than independently computes, the server-authoritative op log**: per §12.9 layer (a), `history.jsonl` holds the `patch`/`inverse` pair the server derives from each typed op, and undo/redo replays those, consistent with §12.13 rule 1 (the client never sends a raw patch, only a typed op) |
| Transactional grouping for multi-mutation actions | v1 | **A component swap or a section regeneration must be ONE undo step.** Naive per-mutation undo leaves a broken hybrid state after one Cmd+Z — a known failure class in AI-editing tools, and it fails exactly when the safety net matters most. **Needs dedicated test coverage** |
| Autosave | v1 **(mechanism rewritten — was described as a raw diff POST, which §12.13 forbids)** | Debounced ~300ms: the client flushes its **pending typed-op queue** to `POST /ops` (the same typed-op channel §12.13 specifies for every write — `{op: 'move-block', node: 'n_hero', …}`, never a raw path or a raw JSON Patch); the server validates each op against its schema and the component library, derives the RFC 6902 patch, applies it to `pages/<id>.doc.json` atomically (write-temp then `fs.rename`), and appends the op + patch + inverse to `history.jsonl`. **This is a deliberate change from the pre-reconciliation draft's "small JSON diff POSTed to the server," which is exactly the "raw-JSON-Patch-over-HTTP" pattern §12.13 rule 1 calls "nearly as dangerous as raw paths"** (an `add`/`replace` on an arbitrary pointer could rewrite `systemLock` or inject an `override` path). Never a base64 blob in localStorage either — the image-builder precedent's `toDataURL` autosave does not scale to a multi-page site |
| Named snapshots | v1 | Explicit "save as milestone" distinct from the autosave stream |
| Save-as-variation / branch | v1 | **The mechanism that makes Step 5 safe** — try a new direction without losing the current one |
| Automatic timestamped version history | v2 | Unchanged — already consistent with §18's v2 "version history: timeline" |
| Visual version diff | v2 | Side-by-side render with changed blocks highlighted, driven by a JSON diff. Unchanged — already consistent with §18's v2 "visual diff" |
| Non-destructive restore | v2 | Restoring creates a new version rather than overwriting the timeline, so restoring is itself undoable. Unchanged — already consistent with §18's v2 "non-destructive restore" |
| Explicit manual save affordance | v2 | For psychological closure even though autosave covers it technically |
| Per-section regeneration log | v2 | Which sections were regenerated, from what note, when. Unchanged — already consistent with §18's v2 "regeneration log," and moves together with §10.7's regeneration rows |
| Crash-recovery draft restore | v2 | Recover the most recent autosave, not the last named snapshot |

### 10.5 Navigation & wayfinding

| Feature | Priority | Notes |
|---|---|---|
| Page navigator | v1 | Thumbnail strip or list |
| Canvas ↔ tree selection sync | v1 | |
| Find/search | v2 | Cmd+F across layer names and text content. Unchanged — already consistent with §18's v2 "find/search" |
| In-edit-mode link-follow | v2 | Modifier+click a link to jump to that page for editing |
| Jump-to-section quick nav | v3 | Unchanged — already consistent with §18's v3 "jump-to-section nav" |

### 10.6 Quality (ambient, non-blocking during editing)

**Reconciliation note for the whole subsection.** §18's v1 scope-in names "Design Health HUD with the v1 live checks" without listing which checks those are, and §18's v2 scope-in separately names "Live a11y/contrast lint inline, motion-property lint, text-spacing stress clone, off-token advisory." Read together, the v1 HUD is fed by **cheap, structural, non-axe heuristics** (bounding-box checks, DOM-order walks, counters), and the v2 HUD gains the **engine-backed checks** (axe-core, the full contrast algorithm suite, motion-property static analysis, the text-spacing stress clone). That split is applied below. One row needed disambiguation rather than a straight move: "Reduced-motion sibling presence" (kept v1) checks that a placed animated `ArtContainer`'s catalog entry *includes* a tagged reduced-motion variant — a catalog-completeness check against v1's own component library, unrelated to "Motion-property lint" (v2), which statically analyses arbitrary CSS/JS for non-compositor properties and is only meaningful once Step-6 custom motion code (v2) exists to lint.

| Feature | Priority | Notes |
|---|---|---|
| Design Health HUD | v1 | **One always-visible, non-modal bottom-corner pill**: three dots (A11y / Perf / SEO), a page-weight bar, and a projected-LCP number from `PerformanceObserver`'s live LCP-candidate entry. Click to expand a grouped issue list. **Never a stream of interrupting toasts.** In v1 the A11y dot is fed by the structural heuristic rows below, not by the axe-core/contrast engine rows, which arrive in v2 — see the reconciliation note above |
| Live contrast checker | v2 **(Reconciled with §18 — was v1)** | WCAG 2 + APCA inline on the selection. Pure two-colour arithmetic — free to run live, which is why it was originally scoped v1, but §18 v2 scope-in groups it explicitly under "Live a11y/contrast lint inline" |
| Touch-target size warning | v1 | Flags <24×24 CSS px unless a WCAG 2.5.8 exception applies. Cheap structural heuristic — kept v1 per the reconciliation note above |
| Overflow/clipping warning | v1 | ResizeObserver + `scrollWidth > clientWidth`. Cheap structural heuristic — kept v1 |
| Broken-link scanner | v1 | Cheap structural heuristic — kept v1 |
| Missing-alt-text badge | v1 | Persistent counter, non-blocking. Cheap structural heuristic — kept v1 |
| Scoped axe-core run | v2 **(Reconciled with §18 — was v1)** | `axe.run(node)` on the touched subtree only after any placement/swap/text edit: color-contrast, image-alt, label, button-name, aria-required-attr, duplicate-id. Page-level rules deferred to lock. §18 v2 scope-in's "Live a11y/contrast lint inline" is read as covering this row together with the Live contrast checker above |
| Focus-not-obscured heuristic | v1 | Bounding-box intersect any placed sticky/fixed element against all focusables. Approximates WCAG 2.4.11. Cheap structural heuristic — kept v1 |
| Reading-order-vs-visual-order heuristic | v1 | After a reorder or free-position, walk the tabbable list and flag non-monotonic DOM-vs-rect pairs. Cheap structural heuristic — kept v1. Once §11's revision ships, this pairs with §11.3.1's `order`-override lint |
| Reduced-motion sibling presence | v1 | Confirm the placed item's catalog includes a tagged reduced variant; auto-apply a generated fallback and flag if missing. **Distinct from "Motion-property lint" (v2) — see the reconciliation note above.** Kept v1 because D4 requires every v1-catalog animated piece to ship with a reduced-motion fallback from day one, and this is a catalog-membership check, not a code-analysis engine |
| Image auto-optimisation on drop | v1 | Any image >~200KB or larger than its render box auto-recompresses to WebP/AVIF + srcset with a **visible undoable confirmation** ("−82% size, visually identical — Undo"). **Not silent** |
| Focus-order overlay | v2 | Optional numbered tab-order overlay |
| Live page-weight indicator | v2 | Running total against a soft budget |
| Off-token / design-drift warning | v2 | Advisory, non-blocking — a human-in-the-loop tool warns rather than mechanically forbids. Unchanged — already consistent with §18's v2 "off-token advisory" |
| Motion-property lint | v2 | Flags non-compositor properties, out-of-band durations, missing reduced-motion query in Step-6 custom animations. Unchanged — already consistent with §18's v2 "motion-property lint," and only meaningful once Step-6 custom code (v2) exists |
| Text-spacing stress clone check | v2 | Off-screen clone with the WCAG 1.4.12 override stylesheet, diffed for overflow. Unchanged — already consistent with §18's v2 "text-spacing stress clone" |
| Responsive-breakage warning | v2 | Flags elements only ever checked at one breakpoint |
| Spell-check | v2 | |

### 10.7 Collaboration & regeneration

**Reconciliation note for the whole subsection.** All seven rows below are v2 after reconciliation — this subsection contributes **zero v1 rows**, which is worth stating plainly since the pre-reconciliation draft had three of its seven rows marked v1. §18's v1 Editor-lite scope-in does not mention notes, regeneration, comments, or activity logs anywhere; §18's v2 scope-in explicitly lists "Per-section notes → scoped regeneration, regeneration log" and, separately, "comment pins" alongside "Share-for-review read-only link." The comment **schema** (distinct from the comment **pins UI**, which was already v2 in the pre-reconciliation draft) is demoted here too: nothing in v1 consumes a comment schema once regeneration-via-notes and comment pins are both v2, so defining the schema early buys nothing user-visible in v1. Implementers may still choose to write the schema at zero marginal cost whenever the v1 data model is being built — that's a scheduling choice, not a phase-gate requirement, and doesn't change its v2 priority tag here.

| Feature | Priority | Notes |
|---|---|---|
| Per-section notes → regeneration | v2 **(Reconciled with §18 — was v1)** | **The human-authored replacement for the rejected VLM critique loop.** A plain-language note ("make this pop more") becomes a scoped regeneration instruction. §18 v2 scope-in: "Per-section notes → scoped regeneration" |
| Regenerate-this-section-only | v2 **(Reconciled with §18 — was v1)** | Replaces in place. **Accuracy depends entirely on clean section boundaries** — design the two together (§10.2's Section boundary markers, kept v1 on an independent basis). Bundled with the row above |
| Collaboration-ready comment schema | v2 **(Reconciled with §18 — was v1)** | Author, timestamp, thread id from day one. Costs almost nothing now; a schema rewrite later costs a lot — but see the subsection note above: nothing consumes it until comment pins (v2) ship, so it moves with them rather than staying v1 alone |
| Canvas-anchored comment pins | v2 | Unchanged |
| Human-readable change/activity log | v2 | Plain-language: what changed, when, via manual edit vs swap vs regeneration |
| Share-for-review read-only link | v2 | Non-editable preview URL before LOCK |
| **Custom code block** | v2 | **An opaque draggable container holding hand-written HTML/CSS/JS that the editor positions but never introspects. The signature moment is built here, outside the menu — this is where the quality ceiling actually lives** (§14.4). Unchanged — already consistent with §18's v2 "Custom code block (the signature moment container)" |

### 10.8 Preview & export

| Feature | Priority | Notes |
|---|---|---|
| In-editor Preview mode | v1 | All chrome hidden, still inside the editor shell. A lighter, reversible rehearsal distinct from LOCK. Confirmed by §18's Editor-lite scope-in: "in-editor preview mode" |
| Interaction preview | v1 | Hover/click states live and testable — needed to verify a v1 component-bar swap actually behaves, not just looks, right |
| Motion preview toggle | v2 | Play / pause / prefers-reduced-motion, per container and globally (§9.6). Unchanged — already consistent with §18's v2 "Motion preview toggle" |
| Reduced-motion preview | v1 | Verify motion-sensitive visitors get a **designed** experience, not a deleted one. Distinct from the Motion preview toggle above (v2) — pairs with §10.6's v1 "Reduced-motion sibling presence" check as the minimum v1 motion-accessibility pair |
| Real-device LAN preview | v2 | QR code / local URL. **Prioritised earlier than a typical v2** because D2 makes responsive correctness a hard constraint and resized-browser preview cannot substitute for real DPR, touch-target feel, font rendering, and scroll physics. Unchanged — already consistent with §18's v2 "Real-device LAN preview" |
| Device-frame preview | v3 | Unchanged — already consistent with §18's v3 "Device-frame preview" |
| Lock / Publish flow | v1 | §12.5. Confirmed by §18's v1 scope-in: "LOCK with all five purity gates" |
| Lock verification gates | v1 | **Five automated purity gates (§12.5), not four** — this row previously undercounted them. In order: (1) forbidden-marker grep across `dist/published/**`, (2) two-build byte-equality (build with the editor integration installed vs. removed, require byte-identical trees), (3) `dist` JS byte-size assertion, (4) screenshot diff between editor-preview-at-1280 and the built page, (5) **the interaction-manifest check** — walks every declared motion/interaction behaviour against `dist/published` to prove it exists in shipped code, which is the gate that verifies D4's motion actually survives LOCK. §13's gate 27 already refers to "LOCK purity gates 1–5," so this row now matches §13 and §12.5 rather than contradicting them |
| Responsive preflight report | v1 | One command renders 320/390/768/1280/1440 (the verification set defined at the top of §10.1) and reports overlap collisions, horizontal overflow, fixed heights on text blocks, free-position counts, blocks with no mobile plan. **Blocking before lock** |
| Long-string reflow fuzz | v1 | Injects a 40-char unbroken token into every text block at 320px; enforces `overflow-wrap: anywhere`; forbids fixed heights on text-containing blocks |
| Evidence bundle export | v1 | §15.6. Confirmed by §18's v1 scope-in: "Evidence bundle" |
| Design-system re-export | v2 | Export current tokens so a future hand-carry starts from the live state |
| Raw code export / eject | v3 | Unchanged — already consistent with §18's v3 "Raw code export / eject" |
| Individual asset export | v3 | Unchanged — already consistent with §18's v3 "individual asset export" |

### 10.9 Command palette & onboarding

| Feature | Priority | Notes |
|---|---|---|
| Command palette (⌘K) | v2 | The standard escape valve for power without menu bloat, once the surface is ~95 features deep. Unchanged — already consistent with §18's v2 "Command palette" |
| Progressive disclosure via selection state | v1 | **The single most load-bearing anti-overwhelm mechanism across every mature editor.** The inspector is empty until something is selected, then shows only type-relevant properties |
| First-run anchor-model walkthrough | v1 | **The highest-value teaching moment is the anchor concept, not a toolbar tour.** Anchoring has no equivalent in Canva or PowerPoint, both of which are free-drag. A short guided "drag this, watch it snap and pin." Teaches exactly the v1 anchor-verb mechanic (§10.1) — nothing in it depends on the v2 canvas |
| Inspector panel (token-only) | v1 | **All non-geometric properties as selects over the design system's scales.** No free-text numerics, no colour picker. The lint wall expressed as UI — an off-token value must be **unreachable**, not merely flagged |

### 10.10 Reconciliation notes for this revision

**Method.** Every row in §10.1–§10.9 was checked against §18's v1 "Scope in" / "Scope cut (explicit)" text and v2/v3 "Scope in" text. A row was reconciled to v1 only where §18 names it (or an unambiguous synonym) in v1's scope-in, or where §18's v1 scope-cut text does not remove it *and* it has no dependency on something §18's cut does remove (e.g., §10.1's Anchor/pin control: verb/stepper-based, not drag, so the "no canvas drag" cut doesn't touch it). Four rows had no §18 citation either way and were kept at their pre-reconciliation value on stated inference, marked **[I]** in their Notes cell — Breakpoint switcher, Type-aware resize, Drag-to-reorder/reparent in tree (partially — see its row), Per-breakpoint visibility. These four should be treated as the first things to re-check the next time §18 itself is revised.

**Count reconciliation, by subsection (rows / v1 / v2 / v3):**

| Subsection | Rows | v1 | v2 | v3 |
|---|---|---|---|---|
| 10.1 Layout & placement | 21 | 5 | 16 | 0 |
| 10.2 Structure & selection | 16 | 10 | 6 | 0 |
| 10.3 Content | 20 | 14 | 5 | 1 |
| 10.4 History & persistence | 11 | 5 | 6 | 0 |
| 10.5 Navigation & wayfinding | 5 | 2 | 2 | 1 |
| 10.6 Quality | 18 | 9 | 9 | 0 |
| 10.7 Collaboration & regeneration | 7 | 0 | 7 | 0 |
| 10.8 Preview & export | 14 | 8 | 3 | 3 |
| 10.9 Command palette & onboarding | 4 | 3 | 1 | 0 |
| **Total** | **116** | **56** | **55** | **5** |

Pre-reconciliation, for comparison: 113 rows, 71 v1 / 37 v2 / 5 v3 (mechanical recount of the draft this revision started from — see §10's opening paragraph). This revision added 3 rows and reassigned 15 rows' priority (14 v1→v2, 1 implicitly v1→v2 split into two rows in §10.3); no row's priority moved to a *lower* number of restrictions (nothing moved v2→v1 or v3→v2), because §18's v1 scope-cut is strictly a removal list, never an addition beyond what its own scope-in already states — except the two rows this revision explicitly proposes as v1 exceptions in §10.3 (custom-component insertion's minimal registry slice, and the minimal chart-data field), both flagged **REQUIRES USER SIGN-OFF** since they deviate from §18's literal text in the direction of restoring a user-named capability.

**Rows whose priority changed (15, all v1→v2 except where noted as a new split):**

| Row | Old | New | Subsection |
|---|---|---|---|
| Real-grid overlay | v1 | v2 | 10.1 |
| Snap engine | v1 | v2 | 10.1 |
| Smart alignment guides + distance labels | v1 | v2 | 10.1 |
| Align tools | v1 | v2 | 10.1 |
| Padding / gap drag handles | v1 | v2 | 10.1 |
| Drag-to-place (grid write) | v1 | v2 | 10.1 |
| Span resize | v1 | v2 | 10.1 |
| Per-breakpoint override + reset-to-inherited | v1 | v2 (+ new v1-scoped-exception row) | 10.1 |
| Keyboard nudge & grid stepping | v1 | v2 | 10.1 |
| Breadcrumb ancestor bar | v1 | v2 | 10.2 |
| Drag-to-reorder / reparent in tree | v1 | v2 (section-level case stays v1 via §10.1's Section reorder) | 10.2 |
| Multi-select | v1 | v2 | 10.2 |
| Per-breakpoint visibility | v1 | v2 | 10.2 |
| Custom-component insertion | v1 (undifferentiated) | split: v1 (minimal registry, new row, sign-off required) / v2 (full) | 10.3 |
| Live contrast checker | v1 | v2 | 10.6 |
| Scoped axe-core run | v1 | v2 | 10.6 |
| Per-section notes → regeneration | v1 | v2 | 10.7 |
| Regenerate-this-section-only | v1 | v2 | 10.7 |
| Collaboration-ready comment schema | v1 | v2 | 10.7 |

(This table has more than 15 lines because the per-breakpoint-override and custom-component-insertion rows each produced two table lines above — one for the old undifferentiated row's disposition, one implied by the new split row's addition — counted once each in the "15" figure by feature, not by resulting row.)

**Open questions this revision could not close, left visible rather than papered over:**

1. **`layout.json` vs `pages/<id>.doc.json`** (§10.4's file-naming note). Renamed within this section; §4, §11, and §12.6/§12.10 still say `layout.json` as of this revision. Whether the command stack, op log, and editor lock are per-page or site-wide is undecided anywhere in the PRD — **requires a §12 update this section cannot make.**
2. **1440 has no live preview surface** (§10.1's breakpoint note). Checked at LOCK and at preflight, never previewable interactively in v1 or v2 as scoped here. **Requires user decision** on whether to add it as a fifth switcher option.
3. **Four rows kept on inference alone** (Breakpoint switcher, Type-aware resize, the section-level/general split on Drag-to-reorder-in-tree, Per-breakpoint visibility) — see the Method paragraph above. **No known mitigation beyond re-confirming against the next §18 revision.**
4. **Custom-component insertion (minimal) and the minimal chart-data field are deviations from §18's literal v1 cut, restoring a user-named Step-6 example (charts) to v1 usability. REQUIRES USER SIGN-OFF** before implementation — see the sign-off note at the top of §10.3. If the user declines, the honest fallback is to also move "Charts: build-time SVG only" out of v1 in §18, since a chart component nobody can populate with data is not a real v1 feature — that fallback would itself need to be written into §18, which is outside this section's authority.
