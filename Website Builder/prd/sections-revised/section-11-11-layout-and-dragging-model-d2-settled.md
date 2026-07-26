## 11. Layout and dragging model (D2, settled)

### 11.1 The four-level layout contract (normative)

1. **Page** = a vertical list of sections. Reorder-only.
2. **Section** = a real CSS Grid — 12/6/4 tracks with `fr` units.
3. **Block** = integer `grid-column` / `grid-row` placement, per breakpoint.
4. **Inside a block** = flow only (hug / fill / fixed). Never coordinates.

This is Figma's model expressed in CSS, and it gives the best freedom-to-safety ratio of anything surveyed. Figma is explicit that its two positioning systems do not mix: constraints (Left / Right / Left-and-Right / Center / Scale) apply **only** to children of plain frames — *"It's not possible to apply constraints to layers … in an auto layout frame."* Inside auto layout you get direction, wrap, gap, padding, alignment, and per-child Hug/Fill/Fixed with min/max. The escape hatch is a single per-child toggle, **"Ignore auto layout,"** which removes that one child from flow, keeps it inside the parent, and hands it back the constraint system. **[V — help.figma.com, both articles fetched, quote verbatim]** Framer copied the same shape.

**Corollary that §11.3.1 depends on:** level 3's placement is *coordinates*, not *sequence* — moving a block visually never requires moving it in the document's child order. Level 1's "reorder-only" and level 4's "never coordinates" are the same idea applied one level up and one level down. Keep this in mind for the whole section: everywhere a "drag" writes data, ask which of the four levels is actually being edited, because levels 1 and 3 use different mechanisms for what looks like the same gesture.

### 11.2 The grid overlay must BE the grid

Draw the overlay by reading `getComputedStyle(section).gridTemplateColumns` — the browser resolves `fr` → px for you — and render those exact tracks. **Never a hand-authored decorative grid.**

Drag then becomes integer rounding:

```
col = clamp(1, round((x − gridLeft) / (colWidth + gap)) + 1, cols + 1)
```

and the persisted value is `grid-column: 3 / span 6`, which is **inherently fluid** (6-of-12 is 50% at every width). This single choice makes Step-4 dragging and Step-7 export the same data.

Wix Studio validates the approach: it ships a real advanced CSS grid with arbitrary row/column counts, units `fr` / `%` / `px` / `vw-vh` / `auto` / `minmax()` / `calc()`, placement by clicking a cell or typing column+row numbers, and explicit multi-cell spanning **[V — support.wix.com, fetched]**. Squarespace Fluid Engine is a 24-col desktop / 8-col mobile CSS grid **[V]**.

The formula above only ever derives a **column**. That is not an oversight to gloss over — the row axis, the occupied-cell policy, and the cross-section case are the actual hard part of this mechanic (this is Step 4b, the product's headline gesture), and they are specified in full below rather than left to be inferred at implementation time.

#### 11.2.1 Row derivation, span preservation, occupancy, and cross-section drops (normative drop algorithm)

**Row axis.** Section grids get an explicit row axis for placement purposes, sized from the direction's spacing scale (the same derived-value mechanism D1 uses for spacing/radius/shadow, applied to a `--wb-row-unit`) via `grid-auto-rows: var(--wb-row-unit)`. This gives rows discrete, droppable lines exactly the way `colWidth + gap` gives columns discrete lines:

```
row = clamp(1, round((y − gridTop) / (rowUnit + rowGap)) + 1, sanityRowCap)
```

`sanityRowCap` (recommend 200) exists only to reject runaway drags (branch AC8 below); it is not a layout constraint — CSS grid's `grid-auto-rows` already grows the track list as needed, so ordinary drops never hit it.

**Span preservation.** A dragged block keeps its existing `colSpan`/`rowSpan` when moved, with one exception: if the drop target's section has fewer columns than `col + colSpan − 1` requires (e.g. an 8-span block dropped into a 6-col section), `colSpan` clamps to `min(colSpan, targetCols)` anchored at the drop column, and the clamp is shown in the same pre-commit chip §11.3 already specifies for breakpoint-scoped edits, before the drop commits. `rowSpan` is never clamped (rows auto-grow).

**Occupied-cell policy.** When the computed target rectangle `{col, colSpan, row, rowSpan}` overlaps an existing sibling's rectangle:

- **Default: displace-down.** The overlapped sibling(s) shift down by the dragged block's `rowSpan + rowGap`, cascading to any sibling the shift in turn overlaps. A live ghost preview shows every block that will move *before* the pointer is released — this is not a silent side effect.
- **Exception: art/decoration containers may stack instead of displacing**, consistent with D4 (motion/art live in draggable containers, and §11.8 failure #4 already gives every section an integer z paint list). When either the dragged block or the occupied block carries `role: "art"` in its node data, overlap is resolved by z-order rather than displacement.
- **Opt-in stacking for non-art blocks:** a per-drop toggle, "Allow overlap here," lets the user deliberately stack two ordinary blocks (writes an explicit `z`) instead of displacing. This is an intentional escape hatch, not a default, and it is capped and counted by **the same lint family** as free-positioning (§11.4 rule 5) — a visible "N overlapping pairs" counter — precisely so it cannot quietly regrow the Squarespace mess §11.3's table documents.

**Cross-section drops.** Two cases:
- **Drop hovers over a different section than the block's current parent:** this is a re-parent, not a placement edit. The node is removed from the source section's children array and inserted into the target section's children array at the computed `{col, row}`. The vacated cell in the source section is left empty — no auto-compaction runs, because compaction would silently move *other* blocks the user did not touch, which is the same "changed order and position" failure §11.3's table quotes Squarespace for.
- **Drop lands in the boundary zone between two sections** (within one row-unit of a section edge): resolved as an append to the nearer section at that section's near edge row (row 1, or `maxRow + 1`), never as a merge of the two sections' grids.

**Rejected drops (visual: block snaps back with a brief outline flash).** A drop is rejected outright — not resolved by displacement — only when the target is illegal by construction:
- The pointer is over another block's **internal** region (level 4 of §11.1: flow-only, never coordinates). Blocks are never drop targets for other top-level blocks.
- The displacement cascade would have to reflow a step inside a pinned/scrubbed sequence container that forbids child reflow (§9.4).
- `row` would exceed `sanityRowCap`.

**Acceptance criteria — one per branch:**

| AC | Branch | Expected result |
|---|---|---|
| AC1 | Same-section move, no overlap | `col`/`row` update; `colSpan`/`rowSpan` unchanged; no sibling affected |
| AC2 | Same-section move, overlaps a non-art sibling | Sibling(s) displace down by dragged block's `rowSpan + rowGap`; ghost preview shown before release |
| AC3 | Same-section move, overlaps a sibling where either block has `role: "art"` | No displacement; overlap resolved via `z`; no lint counter change (art exception is unconditional) |
| AC4 | Same-section move, "Allow overlap here" used on two ordinary blocks | Overlap kept, explicit `z` written, overlap-lint counter increments and is shown |
| AC5 | Move into a narrower section | `colSpan` clamps to `min(colSpan, targetCols)`; pre-commit chip shows the clamp before commit |
| AC6 | Cross-section move | Node re-parented in the doc; source cell left empty; no auto-compaction anywhere in the doc |
| AC7 | Drop on another block's internal (flow-only) region | Drop rejected; block snaps back with outline flash |
| AC8 | Drop would force reflow inside a reflow-forbidding pinned sequence container (§9.4) | Drop rejected; block snaps back |
| AC9 | Computed `row` exceeds `sanityRowCap` | Drop rejected with an inline message, not a silent clamp |

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

Blocks with **no** small-breakpoint override compile to `grid-column: 1 / -1` in source order. That default alone prevents the *overlap* half of Squarespace's signature failure. The Squarespace quote above names a second, distinct failure — "blocks mix-up or change order and position" — which the overlap default does nothing for. §11.3.1 is that missing half.

#### 11.3.1 Reading order vs. visual order (mobile stacking, focus order, screen readers)

**Invariant (normative): DOM order is always the intended reading order.** Desktop and tablet visual order is achieved *only* by grid placement — explicit `grid-column`/`grid-row` integers, or named areas per §11.6 — never by reordering nodes in the document tree. This is why §11.2.1's drop algorithm never touches the sibling array for an ordinary drag: a same-breakpoint move only ever writes `col`/`row`/`colSpan`/`rowSpan`, so DOM order — and therefore mobile stack order, tab order, and screen-reader order — stays fixed by construction unless a user deliberately overrides it (below).

**The one legitimate exception:** an author sometimes genuinely wants the sequence a phone or a screen reader encounters to differ from where a sighted desktop reader's eye lands first — e.g. a pull-quote placed visually first on desktop but intended to be read last. For that case only, the layout node exposes a **per-breakpoint `order` override**, independent of `grid-column`/`grid-row`:

```
order: { bp: "sm" | "md" | "lg", value: N }
```

Using it has real, named costs, which the editor surfaces rather than hides:

- It desynchronises visual order from reading/tab/screen-reader order at that breakpoint, by definition. The moment `order` is set to a non-default value, the editor shows a **persistent warning chip**: "Reading order will differ from what's shown here."
- It is **blocked by a hard lint on any focusable node** (link, button, form field). CSS `order` moving a focusable control breaks WCAG 2.2 **SC 2.4.3 Focus Order (Level A)** without a `tabindex` remediation strategy this PRD does not take on — the lint refuses the edit outright for those node types rather than merely warning.
- For non-focusable content nodes (text, art, decorative containers) the lint is a warning, not a block — **SC 1.3.2 Meaningful Sequence (Level A)** still applies, but reordering non-interactive content is a judgment call the author is entitled to make deliberately, with the warning as the record that it was deliberate.

**Small-breakpoint stack-order preview.** Before any commit that changes mobile stacking — a small-breakpoint layout override, a new `order` value, or a block moving to/from the `1 / -1` default — the editor renders a numbered list preview of the resulting top-to-bottom mobile sequence, at the same breakpoints §10.1's preflight report already renders (320/390/768/1280/1440), so the user sees the actual read order, not just the visual box layout, before committing. This is the mobile-stacking counterpart to the pre-commit chip already specified above for breakpoint-scoped style edits.

**§10.1's responsive preflight report gains a check as a direct result:** it already can flag a breakpoint where DOM order and computed visual (row-major) order diverge past a heuristic threshold; per the gap this subsection closes, that flag now has a remediation path attached (the `order` override and its lint, above) instead of being a dead-end warning with no fix a user can take.

### 11.4 The free-position escape hatch

Practitioner documentation is blunt about the cost. Framer University: *"Your element won't adjust when the screen resizes. What looked perfect on desktop suddenly overlaps or disappears on mobile"*; Framer *"stops treating that element as part of the stack"*; *"Spacing gets weird. Alignments break. Responsiveness? Gone"*; and animations desync because *"elements no longer share the same reference points"* — which matters directly under D4. GrapesJS is equally explicit that its absolute mode is *"ideal for fixed-layout designs like documents for print, business cards, certificates, or static prototypes where responsiveness isn't required."* **[V — framer.university, app.grapesjs.com, quotes verbatim]**

The mechanics of naive absolute positioning: (1) the element leaves flow, so an auto-height parent collapses and the next section slides up under it; (2) `left: 812px` was measured in a 1512px editor viewport, so at 390px it sits 422px off-screen, creating body `overflow-x` or invisible clipping; (3) at 2560px it floats in dead space. Then the user does it fourteen more times and the site is a 1512px fixed canvas wearing a responsive costume.

**Design rules:**

1. **Not raw absolute.** Implement as **anchored-offset**: the element keeps a declared anchor and the free drag writes a **percentage / `clamp()` offset from that anchor**, so it scales. **v1 restricts the anchor target to `parent` or a grid line/cell** — `anchor: { to: "parent" | { col, row }, edge: ... }`. Anchoring to an arbitrary sibling node is **deferred, not implemented**: CSS anchor positioning is the only zero-JavaScript way to express an offset relative to a non-parent sibling, and §11.5 (below) rules anchor positioning out for load-bearing layout — it is still a carryover Interop 2026 item — while runtime positioning JavaScript is separately forbidden in the locked export by the no-editor-runtime contract (§12.5). Neither implementation path is legal as written, so sibling anchoring cannot ship in v1.
   **This narrows the hatch from what was originally stated ("parent edge, sibling, or grid cell") and is a deviation from the user's Step-4b expectation — it requires explicit user sign-off**, since D2 grants the free-position escape hatch without qualifying which anchors it covers. Two paths forward, neither yet validated:
   *(a)* accept the v1 restriction (parent or grid-cell anchors only) as the shipped scope; or
   *(b)* if sibling anchoring is genuinely required, the only known compile strategy is to promote the anchored pair into a shared CSS subgrid wrapper at generate time — subgrid is universally supported (§11.5) — turning the offset into a track-relative value instead of a JS-measured one. **This has not been prototyped. Open question, no known mitigation beyond the subgrid idea stated here** — do not treat it as a committed design.
   **Coordination requirement:** §12.3's persisted schema currently reads `anchor: { to: "parent" | nodeId, edge: ... }`; whichever path (a)/(b) is chosen, that schema must be updated to match — `nodeId` should be narrowed to the grid-cell form under path (a), or explicitly retained only once path (b)'s compile strategy is proven under path (b). Flagging for §12's owner; this section does not have authority to edit §12.3's text.
2. The parent gets a reserved `min-block-size` at drop time so it cannot collapse.
3. Per-block **and** per-breakpoint.
4. **Auto-demotes to normal flow at ≤390px** — moved down from the originally stated 479px, which is not a breakpoint the editor, the preview iframe, or the lock gate can ever render: §10.1's live breakpoint switcher offers 390/768/1280/full, this section's own Hard LOCK gate (rule 6, below) renders 390/768/1440, and §11.7 pins device heights at 390×844/768×1024/1280×800/1440×900. None of those include 479. 390 is the smallest width any of them actually shows, so it is the only small-screen demotion boundary a user can preview *before* it fires.
   The demotion is **authored into the document, not computed implicitly at render.** Dropping — or later editing — a free-positioned block writes a sibling object on the same node:
   ```
   flowFallback: { col, colSpan, row, order }
   ```
   defaulted at drop time from the element's current visual position (nearest column line; row per §11.2.1; DOM order unchanged unless the user separately sets §11.3.1's `order`), and independently editable afterward in the Navigator — never a value the user has to reverse-engineer from behavior. At ≤390px the compiled CSS switches that node from its anchored-offset rule to ordinary `grid-column`/`grid-row` sourced from `flowFallback`; nothing about where the element lands at that breakpoint is inferred at render time or hidden from the editor.
   The z-stacking a free element had under §11.8 failure #4 is dropped at the same breakpoint by default — an element that overlapped others by design in free-position mode has nothing left to overlap once it's back in flow — unless `flowFallback` also carries an explicit `z`, which the user may set the same way any stacked block's z is set (§11.2.1).
5. **Lint caps free-positioned blocks per section** (~2), with a visible counter ("4 elements are free-positioned"). This is the same lint family §11.2.1 extends to opt-in overlap pairs.
6. **Hard LOCK gate**: render at 390/768/1440 and refuse to lock if any free-positioned element produces document `overflow-x` or leaves its parent's box.
7. Disabled by default for pinned/scrubbed sequence containers (§9.4).

**Honest caveat:** anchored-offset still fails for art whose composition depends on absolute relationships across the whole viewport (a scattered constellation of sprites). For that case the only answer is to treat the whole composition as **one component with its own internal responsive rules** — which means the user cannot drag its parts individually, which is exactly what they asked for. There is no better answer.

### 11.5 Container queries, not viewport media queries, inside components

Step 4(d) lets the user swap a component for a variant, and 4(b) lets them move it between slots of different widths. If component internals key off `@media`, a card that looks right in a 6-col slot breaks the moment it is dragged into a 3-col slot — an unbounded matrix of manual fixes.

**Put `container-type: inline-size` on every block wrapper and write component internals with `@container`.** A component then adapts to *the space it was dropped into*, which is the only sane contract for drag-and-swap.

Platform status as of 2026: container queries, `:has()`, `@property`, cascade layers, nesting, and logical properties are all **Baseline Widely Available**. Subgrid is universally supported (Chrome 117+, Firefox 71+, Safari 16+) and is the right tool for aligning a nested component's internals to the parent section's tracks — and, per §11.4 rule 1 path (b), the only currently-known way sibling-relative free-position offsets could ever be made to work without runtime JS. **Anchor positioning is still a carryover Interop 2026 item — use it only for editor chrome and progressive-enhancement decoration, never load-bearing layout.** This is the platform fact §11.4 rule 1 is reconciled against: it is why sibling anchors are deferred rather than shipped in v1. **[V — web.dev/blog/interop-2026, webkit.org]**

### 11.6 grid-template-areas and integer placement, together

Named areas are the most readable and most mobile-safe form — the entire mobile layout of a section is one property rewrite. Their hard limit is that every area must be a **contiguous rectangle**, so they cannot express arbitrary drag results (an L-shape, or two blocks in one cell).

**Resolution:** the design system ships ~12 section archetypes as `grid-template-areas` per direction. The moment a user drags a block off its area, **that block only** is promoted to explicit `grid-column`/`grid-row` integers on the same grid — the same integers §11.2.1's drop algorithm computes. Both compile to identical CSS Grid, so export is unaffected and the archetype stays readable for every untouched block.

### 11.7 Preview must be a same-origin iframe

A scaled `<div>` cannot evaluate media queries against the simulated width; an iframe can, because the iframe's own viewport is what `@media` sees.

Puck ships exactly this: viewports as `{width, height: 'auto'|number, label, icon}`, defaults Small 360 / Medium 768 / Large 1280 / Full-width, *"rendered in a same-origin iframe that can be resized to simulate different viewports"* **[V — puckeditor.com/docs/integrating-puck/viewports, fetched]**.

**The trap:** all four Puck defaults use `height: 'auto'`, so any hero using `100vh`/`svh`/`dvh` measures the iframe's expanded height, not a phone's. Hero framing looks right in the editor and wrong on device. **Fix: pin device heights (390×844, 768×1024, 1280×800, 1440×900) whenever the page contains a viewport-height rule.** Also note that when Puck's compositional `<Puck.Preview />` is used directly, the viewports API has no effect at all.

### 11.8 Failure-mode catalogue — all fourteen mechanically detectable

| # | Failure | Detector |
|---|---|---|
| 1 | Small-screen overlap (Squarespace's signature failure) | Per-breakpoint rectangle-intersection over resolved grid areas; default any block with no sm override to `1 / -1`. Same-breakpoint overlaps are additionally *prevented at drop time*, not just caught after the fact, by §11.2.1's occupancy rule |
| 2 | Horizontal overflow | Assert `documentElement.scrollWidth <= clientWidth` at 320/390/768/1280/1440 |
| 3 | Text reflow blowout | Fuzz every text block with a 40-char unbroken token at 320px; require `overflow-wrap: anywhere`; forbid fixed heights on text blocks |
| 4 | Z-order confusion | Z-order is an integer paint list per section in `layout.json`, compiled to `z-index` only where needed, with each section establishing a stacking context (`isolation: isolate`) so nothing leaks across sections. §11.2.1's art-stacking and opt-in-overlap branches are the only paths that intentionally write to this list |
| 5 | Nested scroll containers | Forbid `overflow: auto` inside blocks except one explicit "scroller" component |
| 6 | Absolute drift | Cap free-positioned blocks per section; auto-demote to `flowFallback` at ≤390px (§11.4 rule 4) |
| 7 | Unclickable / ghost elements | The Navigator tree is the guaranteed selection path |
| 8 | Zoom-broken snapping | Tolerance ÷ zoom |
| 9 | 100vh lying in the editor | Pin iframe device heights |
| 10 | Font-load measurement drift | `await document.fonts.ready` before **any** `getBoundingClientRect` in editor or capture |
| 11 | Split undo stacks | A single command stack over `layout.json` patches |
| 12 | Drag pointer leaving the iframe | `setPointerCapture` on the overlay; translate coordinates by the iframe rect rather than listening inside |
| 13 | Occupied-cell drop producing silent displacement, or overlap outside the declared art/opt-in exceptions | §11.2.1's drop algorithm resolves overlap *at* drop time (displace-down by default; z-stack only under the `role:"art"` exception or an explicit "Allow overlap here" opt-in, both lint-counted); illegal targets are rejected outright per its AC6–AC9 rather than left ambiguous |
| 14 | Reading order silently diverging from visual order (mobile stack order, tab order, screen-reader order) | §11.3.1's DOM-order-is-reading-order invariant, the hard lint blocking `order` overrides on focusable nodes (WCAG SC 2.4.3), the warning lint on non-focusable nodes (WCAG SC 1.3.2), and the preflight divergence check with an attached remediation path |

### 11.9 Zero DOM injection (architectural constraint, not a note)

The natural implementation of drag is to wrap each component in a `<div data-wb-id>` for hit-testing. **Do not.** Those wrappers get removed at LOCK, and the site uses `.grid > *` for auto-placement, `:first-child` for the hero's top margin, and flex `gap` between direct children. With wrappers the direct children were the wrappers; without them they are the components. Every one of those selectors now matches different elements. The locked site's spacing differs from the design surface by 8px here and a whole grid column there, **and there is no way to explain it to the user because "nothing changed."**

**Constraint:** hit-testing uses `data-wb-node` attributes on elements that **already exist**, plus a **single sibling overlay `<div>` outside the page's layout root**, positioned with `getBoundingClientRect()` + `ResizeObserver`. Handles, selection rings, snap guides and gridlines all live in that overlay. LOCK then removes exactly one element and one `<script>`, and **provably cannot move anything**.

**Corollary for Step 7's "gridlines removed":** the gridlines must visualise a **real CSS Grid** on the page (with named lines). If the grid is only an overlay and snapped positions are baked as margins, removing it is fine — but then "components snap to gridlines" (D2) is decoration, and changing the grid later reflows nothing. **Pick real-grid, and make removal a no-op by construction.**

---
