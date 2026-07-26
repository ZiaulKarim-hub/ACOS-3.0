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

