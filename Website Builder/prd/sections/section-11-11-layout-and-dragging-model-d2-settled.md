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

