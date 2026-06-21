# Vision Interview — HTML-to-PDF Visual Composer

**Date:** 2026-05-23
**Interviewer:** The Architect (Claude Opus 4.7, /acos-interview skill)
**Interviewee:** Zee (Okoa Capital)

## Initial Vision Statement

> "I need to build a design software that will allow me to convert HTML files to PDF in the perfect way. The software window will show HTML file on the right hand side with each component of the file (text, image, charts, tables and anything else) in using freeform containers. I can drag and drop those containers in the PDF layout with pages. I should be able to drag to reshape the containers and the texts should auto adjust within the containers. I should be able to make the images bigger or smaller by dragging the corners of the images. I should also be able to drag and drop the background images from the html to the pdf layout and drag corners to fit page or however I see appropriate. Same should be for the tables. Also, if i drag the corners of a text container, the font size can be made bigger or smaller. Once I place the contents in appropriate places (approximately), the AI should be able to fix the slight errors in consistancy, sizing and shapes and convert it into a perfect pdf file. Is this something that can be created? Do deep research on this and ask me questions."

### Architect's restated understanding (before research)

> A desktop or web app with two synchronized panes — right pane shows the HTML
> decomposed into a "parts bin" of freeform draggable containers (text, image,
> chart, table, background image), left pane shows multi-page PDF canvas. User
> drags containers from bin to canvas; corner-dragging resizes containers (with
> text reflowing, fonts/images scaling, etc.). After approximate placement, an
> AI polish pass corrects alignment, sizing, consistency before exporting
> final PDF. Closest analog: "InDesign-style freeform composition, but the
> input is your existing HTML, and the final cleanup is automated."

The user confirmed this implicitly by proceeding to deep research.

---

## Deep Research Pre-Round (web search synthesis)

Four parallel WebSearch queries were executed before Round 1 to ground the
feasibility assessment in current-market reality.

### Market gap

- **HTML→PDF converters** (Puppeteer, pdfcrowd, iLovePDF, Sejda) — render-and-dump, no editing.
- **PDF template designers** (CraftMyPDF, APITemplate.io, PDF-API.io) — drag-and-drop UI, but design from scratch (no HTML ingest).
- **HTML→Design importers** (html.to.design, Builder.io Figma plugin) — ingest HTML into Figma; manual cleanup; no PDF output focus.
- **The user's idea sits in the gap** — ingest HTML → layout on PDF pages → AI polish → export. No current product covers this.

### Available building blocks (all open-source)

- `react-rnd` — draggable + resizable React components.
- `Konva` / `react-konva` — canvas transforms; canonical "resize text" pattern.
- `react-scale-text` — fits text to container via font scaling.
- `interact.js` — gesture / corner-drag layer.
- `Cheerio` / `JSDOM` / native `DOMParser` — HTML decomposition.
- `Puppeteer` or `pdf-lib` — final PDF export.

### Adjacent AI-polish tooling

- Adobe InDesign now has an AI Assistant (Beta) that auto-aligns objects.
- Venngage offers DesignAI auto-layout.
- Silicon Publishing sells AI plugins for InDesign.
- **Closest internal analog: the user's own `acos-doc-design-qa` skill** —
  screenshot → 10-dimension vision review → per-page perfection loop.

### Feasibility verdict

**Buildable. ~8–16 weeks of single-developer effort for an MVP.** Hardest
component is text-behavior model on corner drag (reflow vs scale conflict),
resolved in Round 1.

---

## Round 1 — Scope, behavior model, audience, integration

### Questions Asked

1. What HTML files does this tool need to handle?
2. When you drag a text container's corner, what should happen to the text?
3. Who is this tool for, ultimately?
4. How does this fit your existing OKOA design pipeline?

### User Responses

1. **OKOA HTML plus generic web pages.** Optimization case is Brad-system HTML; tool must also tolerate arbitrary web pages.
2. **Drag = reflow; font stays the same size.** Corner gesture is a *box-reshape*, not a *type-scale*. Font size lives elsewhere in the UI.
3. **Just me (Zee at OKOA).** Single-user dogfood. No multi-tenant, no auth, no billing.
4. **Replacement for hand-composed HTML → PDF flow.** Today Zee hand-composes HTML against Brad's design system and runs `html-to-pdf.js` (Puppeteer). This tool replaces the manual PDF-positioning work. Brad stays the source of style.

### Key Insights

- Reflow-on-drag is the *easier* engineering choice — solving reflow + font-scale together on the same gesture would require real-time typographic harmony, which is genuinely hard. Reflow-only on the handle gives a clean, deterministic property model that the polish step can later harmonize cheaply.
- "Just me" + "replacement for hand-composed flow" is the cheapest possible scope for this product category. Multi-tenant, web hosting, marketing, telemetry, notarization — all dropped.
- "OKOA + generic" forces robust element-extraction, but the OKOA case can ship first with high accuracy and the generic case can be allowed to be imperfect at launch (polish covers the slack).

---

## Round 2 — AI polish definition, font UX, gesture model for non-text, tech stack

### Questions Asked

1. What should AI polish actually fix when you click "finalize"? (multi-select)
2. How do you want to control font size since corner drag is now reflow?
3. How should corner-drag work on tables and background images?
4. Tech stack preference for the desktop app?

### User Responses

1. **All four polish modes:** snap to grid / align edges, harmonize typography across page, fix sizing inconsistencies for similar containers, AND vision review like `acos-doc-design-qa`.
2. **Per-container number input + +/- buttons.** Explicit numeric font size in sidebar field; no gesture overloading.
3. **Trust the Architect's recommendation.** Architect committed: tables scale uniformly (cells grow/shrink together); backgrounds use cover-fit with focal-point drag-inside-container (Squarespace pattern).
4. **Local web app (Vite + React, runs in browser).** No installer, no signing, no notarization. Node sidecar (existing `html-to-pdf.js`) handles export.

### Key Insights

- Picking all four polish modes implies a **staged pipeline**: deterministic snap → heuristic typography → heuristic sizing → AI vision review loop. Ordering matters because vision review on an un-snapped page produces noisy feedback. The pipeline is toggleable (Quick / Full polish escape hatch).
- Numeric font input + keyboard shortcuts (`+` / `-` while selected) gives speed without conflict.
- Vite + React + browser + Node sidecar is the lowest-cost delivery for a single-user dev workflow. The trade-off (browser File System Access API instead of native dialogs) is acceptable given single-user scope.

---

## Round 3 — Element granularity, charts, project file, brand enforcement

### Questions Asked

1. How should the tool choose what becomes a "container" in the parts bin?
2. How do charts appear in Brad HTML, and how should they be handled?
3. How do you expect to save and resume work?
4. Should the polish step respect Brad's design tokens as hard constraints?

### User Responses

1. **Every visible element — max granularity.** Each `<p>`, `<h1>`, `<img>`, `<svg>`, `<table>` becomes its own draggable container.
2. **Inline SVG — treat as scalable image container.** Lossless vector-to-vector PDF preservation; corner-drag scales without quality loss. (Architect noted canvas/PNG fallback for generic case.)
3. **Project file (.json or .layoutproj) + PDF export.** Layout state in JSON, reopenable; PDF export is a separate render step. Multi-session workflows supported.
4. **Soft hints — polish prefers Brad, can deviate.** Tries Brad values first; if a closer non-Brad value gives a better visual score, deviation is allowed but flagged in a "review me" sidebar.

### Key Insights

- Max granularity = 100–200+ containers per Brad document. Parts bin needs hierarchical tree + flat search/filter + collapse-section affordance to stay usable.
- SVG-first chart handling means lossless polish-time resize and clean PDF output. Canvas/PNG fallback covers third-party HTML.
- JSON project file is diffable in git, scriptable, survives schema migrations. Schema must include HTML source path + hash (for re-ingest detection), per-container layout, font-size overrides, polish pipeline log, and brand-deviation flags.
- Soft-hints-with-deviation-sidebar converts brand discipline from a tax into a feedback loop — a meaningful UX innovation for this product.

---

## Round 4 — Page geometry, snapping, polish model, success criteria

### Questions Asked

1. Page geometry and multi-page text behavior?
2. What snapping and alignment feedback should the canvas provide?
3. What model should drive the AI vision polish loop, and at what cost ceiling?
4. What's your v1 "done" criterion?

### User Responses

1. **US Letter, portrait, OKOA-standard margins; text overflows = manual split.** Default 8.5×11, 0.75″ margins. Overflow shown as red indicator; user manually drags a continuation container to next page.
2. **Snap to grid + magnetic guides to other containers.** Industry-standard pattern (Figma, Sketch, InDesign, Webflow).
3. **Opus 4.7 per page, no cost ceiling — quality wins.** Polish loop uses Opus for vision review on every page until 100/100. ~$0.50–$2 per page depending on iterations. Same engine as `acos-doc-design-qa`.
4. **"I can lay out a Brad-style 10-page report in 15 minutes and it ships to OKOA stakeholders without further edits."** Single tangible benchmark drives every other decision.

### Key Insights

- Letter portrait + OKOA margins matches Brad defaults — no friction porting existing documents.
- Manual overflow (vs threaded text frames) is the right MVP scope; threaded frames can be Phase 2 if the user finds manual overflow tedious.
- Opus-everywhere on polish reflects the user's existing pattern in `acos-doc-design-qa` and `acos-grader` — cost ceiling explicitly waived. This is institutional-grade tooling where output quality > inference cost.
- The "15-minute Brad-style 10-page report shipped without edits" success criterion is the cleanest possible MVP gate: observable, repeatable, real-world.

---

## Coverage Summary

| Category | Covered | Notes |
|----------|---------|-------|
| Users & Audience | ✅ | Single user (Zee at Okoa Capital). High technical level. Private credit / RE capital domain. |
| Platforms & Devices | ✅ | Local web app in browser (Mac, Apple Silicon). Vite + React. Node sidecar for PDF export. |
| Features & Scope | ✅ | Two-pane editor (parts bin + page canvas), reflow on drag, numeric font size, snap+guides, 4-stage polish pipeline, JSON project file, US Letter portrait + manual overflow. |
| Scale & Performance | ✅ | ~10-page Brad documents, ~100–200 containers per doc, single-user concurrency, no networked persistence. |
| Integrations | ✅ | Replaces hand-composed HTML→PDF Puppeteer pipeline. Uses Brad design system as style source. Reuses `acos-doc-design-qa` engine for vision polish stage. |
| Security & Compliance | ✅ | Single-user local. No PII, no auth, no compliance requirements. |
| Design & UX | ✅ | Hierarchical parts bin w/ search + collapse, deviation sidebar for brand drift, snap + magnetic guides, numeric font input + keyboard shortcuts. |
| Technology Preferences | ✅ | Vite + React + TypeScript. Browser-hosted. Node sidecar for PDF rendering (Puppeteer). HTML parsing via JSDOM/Cheerio. Possibly Konva for canvas transforms. |
| Success Criteria | ✅ | 10-page Brad-style report laid out in ≤15 minutes, exported, shipped to OKOA stakeholders without further edits. |

## Interview Summary

**Total Rounds:** 4
**Exit Reason:** Architect satisfied — all nine categories covered with sufficient depth to write a structured vision document and proceed to planning.

**Key insights gained:**
1. **Market gap is real.** No existing product ingests HTML, allows visual freeform PDF layout, and runs an AI polish pass — this is a genuine whitespace.
2. **All building blocks exist.** This is an *integration project* not an *invention project* — react-rnd, Konva, JSDOM, Puppeteer, and the user's own `acos-doc-design-qa` skill cover ~90% of the technical surface area.
3. **Scope is aggressively minimal.** Single user + known input + browser-hosted = no installer, no notarization, no auth, no billing. Cheapest possible delivery in this product category.
4. **The polish pipeline is the product's magic moment.** Four-stage pipeline (snap → typography → sizing → vision) gives both speed and quality, with Opus-everywhere reflecting the user's quality-over-cost institutional posture.
5. **Brand-aware polish with a deviation sidebar** is a genuinely novel UX pattern that turns Brad's design-system tax into a feedback loop.

---

*Vision Interview — Complete understanding before building.*
