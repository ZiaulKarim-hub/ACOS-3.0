# Decision: Page-as-Canvas Composition (not Flow Layout)

**Date:** 2026-04-23
**Decision Maker:** human (confirmed) + the-architect (proposed)
**Status:** accepted
**Supersedes:** N/A
**ADR ID:** ADR-001
**Related Epic:** EPIC-002 (acos-ultimate-designer)

## Context

`acos-ultimate-designer` produces PDF and PPTX output from arbitrary content,
targeting the coffee-table book aesthetic demonstrated by the v3 Private
Credit Capabilities reference at
`/Users/zee/Desktop/Private Credit Capabilities/v3/`.

Two existing skills are in scope:

- **`acos-document-design-brad`** — defines the OKOA design system (tokens,
  typography scale, grid). Skill is design-as-spec, not design-as-process.
- **`acos-loan-doc-generator-with-visual-verification`** — produces loan
  documents from sample-derived designs using a flow-layout CSS
  (`templates/pdf-styles.css`) and Puppeteer with default @page rules.

The new skill must choose how pages are composed in HTML before rendering
to PDF.

## Problem Statement

How should pages be laid out in the HTML emitter? The options split along one
axis: does content flow through pages naturally (like a Word document), or
does each page have its own explicit, art-directed canvas (like a magazine)?

## Options Considered

### Option 1: Flow layout with CSS page-breaks

**Description:** Content renders as a continuous HTML document. `@page`
rules define margins and print behavior. Page breaks occur via
`page-break-before`, `page-break-after`, `break-inside: avoid` on selected
elements. This is how loan-doc's `pdf-styles.css` works.

**Pros:**
- Simple content model: one long document, automatic pagination.
- Reuses proven infrastructure (loan-doc's flow layout + render scripts are
  battle-tested).
- Natural for text-heavy documents that don't need per-page art direction.
- Less template authoring up-front.

**Cons:**
- No per-page art direction: every page looks structurally similar.
- Full-bleed images don't compose cleanly — either you fight the page-break
  engine or you get awkward margins.
- Coffee-table rhythm (photo page between text pages, chapter dividers,
  oversized cover) is nearly impossible without `@page` hacks that break
  elsewhere.
- The v3 reference is **demonstrably** not flow-layout — it has a full-bleed
  cover, chapter dividers, mid-content photo bands. Reverse-engineering v3
  as flow-layout would not match its visual intent.

**Effort:** Low
**Risk:** High (aesthetic mismatch with stated goal)

### Option 2: Page-as-canvas (fixed-size explicit page divs)

**Description:** Each page is an explicit `<div class="page">` with fixed
`8.5in × 11in` dimensions, `page-break-after: always`, `overflow: hidden`.
`@page { size: Letter; margin: 0; }` ensures the renderer respects the page
div's edges. Each page uses one of several art-directed layout templates
(cover, metric-grid, photo-break, chapter-divider, etc.). No content flows
between pages.

**Pros:**
- 1:1 match to the v3 reference — this is how `tearsheet-v3.html` is
  structured, and it's the pattern that produces the v3 PDF's visual quality.
- Every page is deliberately composed. Coffee-table rhythm is explicit in
  the template set, not an emergent property of pagination heuristics.
- Full-bleed images are trivial: they fill the 8.5×11in canvas directly.
- Maps 1:1 to PPTX slide model (STORY-004): every HTML page → one slide with
  the corresponding layout. Clean parallel.
- The content decomposer (SLICE-001-04) becomes a page-plan builder — it
  decides which template each chunk of content goes into, rather than trying
  to force content through a single flowable template.

**Cons:**
- More template authoring up-front (9 templates vs. 1 flowable stylesheet).
- Content that overflows a page must either be split by the decomposer
  (multi-page narrative) or rejected with a clear error — no automatic
  overflow handling.
- Font size + line-height choices are per-template, not global — slight
  inconsistency risk between templates if not carefully managed (mitigated
  by tokens.css and typography classes).

**Effort:** Medium–High (SLICE-001-03 is an L-sized slice)
**Risk:** Low (proven pattern from v3)

### Option 3: Hybrid — flow for body pages, canvas for cover/dividers/photo-breaks

**Description:** Mix the two: body content flows through pages 2–N using
flow-layout CSS; cover, chapter dividers, and photo-break pages are inserted
as fixed-size canvas divs with their own overrides.

**Pros:**
- Gets full-bleed cover + photo-break without template-authoring every body
  page type.
- Easier for text-heavy documents where most pages are just body.

**Cons:**
- Two layout systems in one document = sharp edges at the boundaries
  (photo-break page breaks the flow, next flow page's top margin is off by a
  few pixels, running footer numbering goes wrong).
- PPTX parallel breaks — flow-layout pages don't map cleanly to slides.
- Coffee-table rhythm (the whole point) becomes harder, not easier: the skill
  would have to interleave two kinds of pages and ensure continuous numbering,
  consistent footers, and correct page-break behavior at every boundary.

**Effort:** High (most complex option)
**Risk:** High (interaction bugs between the two layout systems)

## Decision

**Chosen Option:** Option 2 — Page-as-canvas composition.

## Rationale

The v3 reference is the design target, and v3 is page-as-canvas. Attempting
to match it via flow layout would require forcing an inappropriate layout
system to produce an output it's not designed for. Option 3 compounds the
friction by running both systems simultaneously.

Option 2 also aligns naturally with the PPTX output path: each HTML page
becomes one slide. This 1:1 mapping is what makes STORY-004 tractable —
otherwise, PPTX would require a separate content model and the two paths
would diverge.

The up-front cost of authoring 9 page templates is real but bounded
(SLICE-001-03, effort=L). That cost is paid once and amortizes across every
future document the skill generates.

This decision is what makes the skill architecturally DIFFERENT from both
Brad (a design spec, not a composition engine) and loan-doc (flow layout
for loan documents). The new skill is the composition engine Brad's spec
implies but doesn't supply.

## Implications

### Immediate

- SLICE-001-03 must build 9 distinct page templates, each a self-contained
  canvas div. Template variable syntax becomes a shared contract between
  SLICE-001-04 (decomposer writes to it) and SLICE-001-05 (emitter reads
  from it).
- `@page { size: Letter; margin: 0; }` is required; zero margin because all
  margin work happens inside the `.page` div.
- Puppeteer render (SLICE-003-01) must use `preferCSSPageSize: true` and
  `printBackground: true` — defaults drop background fills and may override
  the explicit page size.

### Long-term

- The template library is a living asset. Additions require design review.
  A chart layout, a testimonial layout, and a multi-photo mood-board layout
  are likely first extensions.
- PPTX slide masters (SLICE-004-02) must parallel the HTML templates exactly.
  If HTML gets a new template, PPTX needs the corresponding slide master or
  the format falls out of sync.
- Content that doesn't fit a page needs the decomposer to split it into
  multiple pages of the same or similar template. The decomposer owns
  overflow handling, not CSS.

### Dependencies

- Depends on: `acos-document-design-brad` SKILL.md (source of tokens for
  templates).
- Depends on: v3 reference HTML (gold-standard composition to reverse-engineer
  template shapes from).
- Enables: STORY-004 PPTX pipeline (1:1 slide mapping).
- Enables: STORY-005 visual checklist (per-template aesthetic rules).

## Related Decisions

- ADR-002 — Brand-first image sourcing with vision-bootstrapped manifest
- (future) ADR-003 — Visual reviewer model hard-pinned to opus
- (future) ADR-004 — Zero loan-doc design-library content loads

## Review Notes

User approved this decision as part of EPIC-002 planning on 2026-04-23 at
08:15Z. Rationale was discussed during the evaluation/planning session
captured in `memory/handoffs/2026-04-23-073005-session-handoff.yaml` and
`memory/handoffs/2026-04-23-081259-plan-approved-pending.yaml`.

---

*Recorded by The Architect*
