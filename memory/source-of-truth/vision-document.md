# Vision Document — HTML-to-PDF Visual Composer

**Created:** 2026-05-23
**Based on:** vision-interview.md (4 rounds, Architect-satisfied exit)
**Status:** Active
**Vision ID:** VISION-HVC-01 (HTML-to-PDF Visual Composer)
**Supersedes:** vision-document.acos-ultimate-designer.md (snapshotted 2026-05-23, prior vision for already-shipped EPIC-002)

---

## Executive Summary

A single-user, browser-hosted visual editor that ingests HTML files, decomposes
them into a freeform "parts bin" of draggable containers (text, images, tables,
inline SVG charts, background images), and lets the user lay them out across
multi-page PDF canvases. A four-stage AI polish pipeline (snap-to-grid →
typography harmonization → sizing equalization → Opus 4.7 vision review)
auto-corrects approximate placements into a finished PDF that meets
institutional quality standards. Replaces the current hand-composed
HTML → Puppeteer-rendered PDF workflow at Okoa Capital.

---

## Target Users

### Primary User
**Zee, Associate at Okoa Capital (private real-estate-equity lender).** Single
user. Technical level: high (Claude Code power user, comfortable with Node,
Python, Vite, React). Domain: private credit, real-estate capital, investor-
grade document production. Hardware: macOS, Apple Silicon. Existing tooling
already in workflow: Brad design system (HTML + CSS), `html-to-pdf.js`
(Puppeteer), `acos-document-design-brad`, `acos-ultimate-designer`,
`acos-doc-design-qa`.

### Secondary Users
None at launch. Tool is explicitly scoped to single-user. **Not intended as
a commercial product.**

---

## Platform Requirements

- **Runtime:** Local web app (browser-hosted). Served by Vite dev server on
  `localhost`, opened in Chrome or Safari.
- **Operating system:** macOS (Apple Silicon primary). Cross-platform
  acceptable but not a priority.
- **No installer, no signing, no notarization.** `pnpm dev` is the launch
  command.
- **No multi-tenant, no auth, no billing.** All state local.
- **Offline-capable.** Internet only required for AI polish API calls
  (Anthropic Messages API for Opus 4.7).

---

## Features

### Must Have (MVP)

1. **HTML ingest with full DOM decomposition.** Parser walks the rendered DOM
   and produces a "parts bin" entry for every visible element — `<p>`, `<h1>`–`<h6>`,
   `<img>`, `<svg>`, `<table>`, `<div class="bg-image">`, etc. Maximum
   granularity.
2. **Parts-bin UI (right pane).** Hierarchical tree showing the source DOM
   structure, with section-level collapse, flat-search/filter input, and
   thumbnail previews of each container. Drag any item from bin onto canvas.
3. **Multi-page PDF canvas (left pane).** Default page size: US Letter
   (8.5 × 11 in), portrait, 0.75″ margins (matches Brad). Multiple pages
   stack vertically; navigation via scroll + page-thumbnail strip.
4. **Drag-and-drop placement.** Containers move from bin to canvas, and within
   the canvas, freely via standard pointer drag.
5. **Corner-resize gesture model:**
   - **Text containers** — drag corner reshapes the box; text **reflows** to
     fit; font size is unchanged.
   - **Image containers** — drag corner rescales the image with aspect-lock
     by default, free-scale with shift-modifier.
   - **Inline SVG (charts)** — drag corner rescales the vector lossless.
     Aspect-lock by default.
   - **Table containers** — drag corner scales the entire table uniformly;
     cells grow/shrink together; cell text reflows internally. Column-width
     handles available for per-column manual adjustment.
   - **Background image containers** — drag corner reshapes the box; image
     uses CSS-cover fit (no distortion); user can drag image *inside* the
     container to set focal point (Squarespace pattern).
6. **Font size control (numeric).** Each selected text container exposes a
   font-size field in the right sidebar; `+` / `-` keyboard shortcuts step the
   value while a container is selected. Initial value inherits from source HTML.
7. **Snap + magnetic alignment guides.** Background 8 px grid (toggleable);
   while dragging, snap to nearest gridline and show alignment guides when an
   edge or center aligns with another container or a page edge.
8. **Project file format (`.layoutproj`, JSON).** Saved alongside source HTML.
   Re-opening the file restores layout state, container positions/sizes,
   font-size overrides, polish-pipeline log, and brand-deviation flags.
   Includes source HTML path + SHA-256 hash for re-ingest detection.
9. **Four-stage polish pipeline.** Triggered by "Finalize" button:
   1. **Snap-to-grid / edge alignment** (deterministic, instant). Nudges
      each container so edges share gridlines and gutters are equal.
   2. **Typography harmonization** (heuristic, fast). Normalizes font sizes
      and line-heights across same-class containers within a page (e.g., body
      paragraphs at 11.7 / 12 / 12.3 pt → all 12 pt).
   3. **Sizing equalization** (heuristic, fast). Same-class image containers
      (e.g., side-by-side photos) snap to identical widths/heights.
   4. **Opus 4.7 vision review loop.** Same engine as `acos-doc-design-qa` —
      screenshot each page, score 10 dimensions, loop until 100/100 per page.
      No cost ceiling.
10. **Brand-aware polish with deviation sidebar.** Polish prefers Brad's
    typographic scale, palette, and 8 px spacing grid. When a deviation gives
    a better visual score, deviation is allowed but logged to a "Brand drift"
    sidebar showing each deviation, its delta, and rationale. User can
    approve or snap-back per deviation.
11. **PDF export.** Final layout is rendered to PDF via Node sidecar (reuses
    existing `html-to-pdf.js` Puppeteer pipeline). Output saved alongside
    project file.

### Should Have (Phase 2)

1. **Threaded text containers.** Like InDesign — link two text containers
   so overflow from container A flows into container B automatically across
   pages. (MVP uses manual continuation containers; Phase 2 automates.)
2. **Custom page geometry.** A4, landscape, custom dimensions, variable margins.
3. **Polish-pipeline toggles.** User selects which polish stages to run
   ("Quick polish" = stages 1–3 only; "Full polish" = all 4). Currently the
   "Finalize" button always runs all four.
4. **Brand-deviation snap-back batch action.** Single click to revert ALL
   deviations in the sidebar to brand-spec values.
5. **Undo / redo with full history visualization.**
6. **Export to alternative formats.** DOCX, EPUB, web (HTML+CSS) round-trip.

### Could Have (Future)

1. **Multi-document templates.** Save a layout structure and reapply to
   different HTML inputs of the same type (e.g., monthly investor letter
   template).
2. **Multi-user comments / review mode.** A read-only viewer where
   stakeholders can annotate the canvas without editing.
3. **Live HTML-source sync.** Edits to the underlying HTML propagate back
   into the parts bin without forcing re-ingest.
4. **AI auto-layout suggestions.** Given an HTML input, suggest 3 candidate
   layouts and let the user pick one as a starting point.

### Won't Have (Excluded)

1. **Web hosting / SaaS deployment.** Tool is local only.
2. **Multi-tenant / auth / billing.** Single user.
3. **Real-time collaboration.** Single user.
4. **Mobile / responsive output.** Desktop browser only; PDF output only.
5. **Editor for the source HTML itself.** The tool *consumes* HTML; it does
   not produce it. Brad design system + hand-composed HTML remains the
   source.
6. **Cross-platform installer / native app packaging.** Browser-hosted Vite
   dev server is the delivery model.

---

## Technical Requirements

### Scale

- Expected Users: 1 (Zee).
- Concurrent Users: 1.
- Typical Input: 1 HTML file per project, ~100 KB–1 MB raw HTML.
- Typical Output: 5–20 page PDF, US Letter portrait.
- Typical Container Count: 100–300 per project.

### Performance

- Initial HTML ingest → parts-bin populated: **≤ 3 seconds** for a 30 KB Brad document.
- Drag latency (container reposition or corner resize): **< 16 ms** (60 fps).
- Deterministic polish stages (1–3) on a 10-page document: **≤ 2 seconds total**.
- Vision polish (stage 4): bounded only by Opus API latency. Typical: 30–90 seconds per page; 5–15 minutes for a 10-page document. Acceptable because it runs only on "Finalize."
- PDF export from finalized layout: **≤ 10 seconds** for a 10-page document.

### Security

- All project files stored locally on user's macOS file system.
- HTML parsing must sanitize / sandbox — no script execution from ingested HTML (use Cheerio or JSDOM with scripts disabled).
- Anthropic API key stored in `.env.local` (gitignored). No key in source.

### Compliance

- None applicable (single-user, no PII handled, no external distribution).

---

## Integrations

- **Brad design system** (`acos-document-design-brad`) — source of typographic scale, palette, spacing grid. Polish pipeline reads Brad's design tokens as hints.
- **`acos-doc-design-qa` skill** — engine for stage-4 vision polish loop. Same screenshot → 10-dimension score → iterate pattern.
- **`html-to-pdf.js` Puppeteer pipeline** — Node sidecar for final PDF export step. Reused as-is.
- **Anthropic Messages API** — Opus 4.7 for vision review. Subscription billing (Claude Code Max plan); explicitly NOT a separate ANTHROPIC_API_KEY (per user's standing preference, memory key `feedback_subscription_not_api`).

---

## Design Requirements

- **Visual style** — Tool's UI: clean, dark-mode-default, monospace-accent (matches user's existing power-tool aesthetic). Output PDFs: Brad design system (Swiss/International modernism, warm earth tones, coral accents).
- **Brand Guidelines** — Brad design tokens as soft hints in polish pipeline, with deviation sidebar for transparency.
- **Accessibility** — Tool itself: keyboard navigable for power-user shortcuts. Output PDFs: tagged PDF / accessibility tree is *not* required for v1 (internal distribution).

---

## Technology Stack

- **Frontend:** Vite + React + TypeScript.
- **State management:** Zustand or Redux Toolkit (TBD in planning).
- **Canvas / interaction:** `react-rnd` for the box + corner-handle layer; `Konva` / `react-konva` as fallback if richer canvas needs surface; `interact.js` if multi-touch becomes relevant.
- **HTML parsing:** Native browser `DOMParser` for initial decomposition; JSDOM in Node sidecar if heavier server-side work is needed.
- **Charts:** Inline SVG preserved as-is; canvas fallback for third-party HTML rasterizes via `html2canvas` at 2x DPI.
- **PDF export:** Existing `html-to-pdf.js` (Puppeteer) reused as Node sidecar invoked via child process. Final layout serialized to a print-stylesheet HTML and rendered.
- **AI vision polish:** Anthropic Messages API (Claude Opus 4.7) via subscription auth — reuses the `acos-doc-design-qa` engine.
- **Project file:** JSON, schema-versioned, gitignored or git-trackable per user choice.
- **Backend:** None for app proper. Node sidecar (one file) only for PDF export.
- **Database:** None. Local file system only.
- **Hosting:** None. Browser at `localhost:5173`.

---

## Success Criteria

1. **Primary acceptance gate (must hit):** *Zee can lay out a Brad-style 10-page report in 15 minutes and it ships to OKOA stakeholders without further edits.* Measured against a real OKOA document workflow, repeatable across at least one shipped deliverable.
2. **Polish-quality gate:** Output PDF scores ≥ 95/100 on the `acos-doc-design-qa` 10-dimension rubric, averaged across all pages, for the v1 acceptance document.
3. **Workflow-replacement gate:** v1 ships the next OKOA document Zee would otherwise have hand-composed in HTML. Once that deliverable is out the door, MVP is closed.

---

## Constraints & Assumptions

### Constraints

- **Single-developer build budget.** Implementation runs through ACOS slice workflow with Architect + Developer + Reviewers. ~8–16 weeks of single-developer effort estimated.
- **Quality bar is institutional.** Output PDFs go to credit committees, investors, counterparties. Any rendering defect or font-size inconsistency is a v1 failure.
- **Reuse over rebuild.** Existing `html-to-pdf.js`, Brad design system, `acos-doc-design-qa` engine are reused as-is. New code is the editor UI + the parts-bin extractor + the polish pipeline orchestration.
- **No new model costs beyond existing subscription.** All Opus 4.7 vision calls go through the Claude Code Max subscription, not a separate API key.

### Assumptions

- Brad design system HTML output is stable enough that an extractor optimized for it will not need frequent rework.
- Browser File System Access API is sufficient for opening/saving project files without native dialogs.
- Puppeteer (already in user's toolchain) can render the finalized layout at fidelity equivalent to current `html-to-pdf.js` output.
- Opus 4.7 vision-review cost per document (~$5–$30 per 10-page render) is acceptable given the institutional output value.
- The four-stage polish pipeline ordering (deterministic → heuristic → vision) is correct; vision review on un-snapped pages would produce noisy feedback, so deterministic stages must run first.
- Manual overflow continuation is acceptable for MVP; threaded text containers (InDesign-style) deferred to Phase 2.

---

*This document is the source of truth for the project. All planning and implementation decisions must align with these requirements.*
