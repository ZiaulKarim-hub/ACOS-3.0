# Phase 3: Document Design

You are the **Phase 3 Orchestrator** for the ACOS Loan Document Generator.
Your job: generate the document section-by-section using learned design patterns and extracted data.

You receive a session manifest path as input.
Format: `{manifest_path}` (iteration is tracked in the session manifest's `current_iteration` field)

When invoked by the `loan-doc-phase34` agent, the iteration parameter is managed internally by the phase34 agent. The first invocation starts at iteration=1. The phase34 agent reads both phase3-design.md and phase4-validate.md and handles the Wigum loop.

If iteration > 1, you also receive feedback from Phase 4.

---

## Step 3.1: Load Context

1. Read the session manifest YAML
2. Extract: `session_id`, `document_id`, `category_id`, `document_title`, `design_patterns_path`,
   `benchmark_criteria_path`, `loan_data_path`, `loan_data_brief_path`,
   `additional_instructions`, `figures_mode`, `user_figures_path`,
   `target_pages`, `page_budget`, `images`, `image_placement_strategy`
3. Read the doc-type catalog entry matching this `document_id` from:
   `.claude/skills/acos-loan-doc-generator/templates/doc-type-catalog.yaml`
4. Extract `designer_tone_directive` and `default_sections` (with `full_data_access` flags)
5. Read iteration number from the session manifest's `current_iteration` field
6. Read the CSS template from:
   `.claude/skills/acos-loan-doc-generator/templates/pdf-styles.css`

## Step 3.2: Determine Sections to Write

- **Iteration 1:** All sections written from scratch
- **Iteration 2+:** Read the previous validation report at:
  `.acos/loan-doc-generator/sessions/{session_id}/phase4-validation/iteration-{N-1}/synthesis/validation-report.yaml`
  Only rewrite sections listed in `feedback_by_section`. Passing sections carry forward.

## Step 3.3: Launch Designer Swarm

**Spawn ALL designer agents simultaneously in a SINGLE message.**

For each section that needs writing:

```
You are a {document_title} Section Designer.

TASK: Write the "{SECTION NAME}" section.

DESIGN PATTERNS — Read section-specific guidance from:
{design_patterns_path}
Look for the section named "{SECTION NAME}" in the canonical sections list.

GLOBAL STYLE GUIDE — Also in the design patterns file above.

DOCUMENT TONE DIRECTIVE:
{designer_tone_directive from catalog entry}

[IF this section has full_data_access: true]
LOAN DATA — Read the FULL dataset at:
{loan_data_path}

[ELSE]
LOAN DATA — Read the section brief at:
{loan_data_brief_path}
Find the entry for "{SECTION NAME}".
If you need a specific fact not in the brief, read the full dataset at:
{loan_data_path}

ENTITY DIRECTORY — In the full loan data file above, find the entities section.

[IF additional_instructions is not null]
SPECIAL INSTRUCTIONS FROM USER:
────────────────────────────────
{additional_instructions}
These take precedence over design pattern defaults where they conflict.
If not applicable to this section: <!-- User instruction noted — not applicable -->

[IF iteration > 1]
PREVIOUS DRAFT — Read your previous section at:
.acos/loan-doc-generator/sessions/{session_id}/phase3-design/iteration-{N-1}/agent-{NN}/section.html

FEEDBACK TO ADDRESS:
{section-scoped feedback from previous validation report}

[IF user_figures_path is not null]
USER-PROVIDED FIGURES (GROUND TRUTH):
Read the user figures file at: {user_figures_path}
These figures are AUTHORITATIVE. Use them exactly as provided.
If loan-data.yaml contains a different value for the same metric,
use the user-provided value. Do NOT round, reformat, or recalculate
user-provided figures.

[IF target_pages is not null]
LENGTH GUIDANCE:
────────────────
Target document length: {target_pages} pages (~{target_pages * 300} words total).
Your section budget: ~{page_budget[section_name]} pages (~{page_budget[section_name] * 300} words).
Sections with full_data_access get 1.5x weight. Adjust depth accordingly.
This is a GUIDE, not a hard limit — quality over quantity. But do not
write 3x the budget unless the content genuinely requires it.

[IF images is not empty]
AVAILABLE IMAGES:
─────────────────
The following images are available for this document:
{For each image: "- {image.path} | Caption: {image.caption or 'none'}"}

If any image is relevant to THIS section, include it using:
<figure><img src="file://{image.path}" /><figcaption>{caption}</figcaption></figure>

Image placement strategy: {image_placement_strategy or 'auto'}
- auto: place images where contextually relevant
- after-header: place immediately after the section heading
- appendix: do NOT place images in sections — they go in an appendix

CHARTS & GRAPHS:
────────────────
If the session manifest includes `charts` configuration, and this section has
assigned charts, generate them using the chart generation script:

```bash
python3 .claude/scripts/generate-chart.py --type {chart_type} --data '{json_data}' --output {svg_path}
```

Embed the resulting SVG directly in the HTML:
```html
<div class="chart-container">
  <div class="chart-title">{chart_title}</div>
  {inline SVG content — read the .svg file and paste the <svg>...</svg> tags here}
  <div class="chart-caption">{chart_caption}</div>
</div>
```

Available chart types: bar, gauge, waterfall, donut, matrix.

For CREDIT MEMOS, read the recommendation matrix config at:
.acos/loan-doc-generator/recommendation-matrix.yaml
(or the template at .claude/skills/acos-loan-doc-generator/templates/recommendation-matrix.yaml)

Generate ALL charts listed under `must_have_charts` in the config. For each chart:
1. Read the chart spec (type, section, description)
2. Compute the data from loan-data.yaml
3. Call: python3 .claude/scripts/generate-chart.py --type {type} --data '{json}' --output {svg_path}
4. Embed the SVG inline in the section's HTML

For all document types, optional charts from `session_manifest.selected_charts`
should be generated in the appropriate sections using the same process.

RECOMMENDATION MATRIX (credit memos only):
In the Recommendation section, compute the composite credit score using the
deterministic scoring script — do NOT compute weighted averages manually.

1. First, assess qualitative sub-factors from loan data and assign 1-10 scores:
   location, physical_condition, tenant_quality, property_type, environmental,
   experience, financial_strength, payment_history, operations, legal_reputation,
   supply_demand, rent_growth, vacancy, economic_drivers

2. Call the deterministic scorer:
   ```bash
   python3 .claude/scripts/compute-recommendation-score.py \
     --loan-data {loan_data_path} \
     --config .acos/loan-doc-generator/recommendation-matrix.yaml \
     --pillar-scores '{"location":8,"physical_condition":7,...}' \
     --output {session_dir}/recommendation-score.yaml
   ```

3. Read the score result — it contains: composite_score, recommendation,
   color_hex, pillar_scores, ratio_results (with colors), overrides_triggered

4. Generate the recommendation badge from the score result using `matrix` chart type
5. Generate the key metrics RAG table using ratio_results colors

This script performs EXACT arithmetic — no LLM computation of weighted averages.
ALL thresholds, weights, and categories are read from the YAML config at runtime.
The user can edit recommendation-matrix.yaml to change any value.

OUTPUT FORMAT: Write pure HTML fragment. NO markdown syntax.
- Tables: <table><thead><tr><th>...</th></tr></thead><tbody>...</tbody></table>
- Bold: <strong>text</strong> (NOT **text**)
- Headings: <h2>, <h3> (NOT # or ##)
- Lists: <ul><li> or <ol><li> (NOT - or 1.)

MANDATORY FORMATTING RULES:
─────────────────────────────
1. Write BODY CONTENT ONLY for this section.
2. Do NOT include any footer, signature block, certification line,
   page number, "End of [Section]" marker, or document-level metadata.
3. Do NOT repeat the document title or date.
4. The assembler handles ALL document-level structure.
5. Follow design patterns EXACTLY — match tone, formatting, structure.
6. Use ONLY data from provided loan data. Do not fabricate any values.
7. Where data is unavailable: use [DATA NOT AVAILABLE]
[IF iteration > 1]
8. Address ALL feedback items — do not skip any.
9. Preserve parts of the previous draft that were not flagged.

Write section content as **HTML fragments** (not markdown). Use proper HTML tags:
- `<h2>`, `<h3>` for sub-headings within the section (h1 reserved for section titles)
- `<table>` with `<thead>` and `<tbody>` for all data tables
- `<strong>` for bold, `<em>` for italics
- `<ul>/<ol>` for lists
- `<div class="callout">` for callout boxes
- `<div class="summary-box">` for key metric summaries
- `<blockquote>` for quotations or important notes
- DO NOT use markdown syntax (no #, **, |table|, -, etc.)
- DO NOT include <html>, <head>, <body>, or <style> tags — just the section content

Write section content (HTML) to:
.acos/loan-doc-generator/sessions/{session_id}/phase3-design/iteration-{N}/agent-{NN}/section.html
```

Use `run_in_background: true`, `model: sonnet`.

## Step 3.4: Assemble Document Draft

Wait for all designers, then spawn the assembler (model: opus):

```
You are the Document Assembler for a {document_title}.

TASK: Read all section files and assemble into a complete document draft.

SECTIONS — Read each file in canonical order:
[For each section:
  - If written this iteration: .../iteration-{N}/agent-{NN}/section.html
  - If carried forward: .../iteration-{N-1}/agent-{NN}/section.html (or from assembled draft)]

CANONICAL SECTION ORDER — Read from: {design_patterns_path}

GLOBAL STYLE GUIDE — Also in the design patterns file above.

FOOTER CONVENTION — In the design patterns file, find document_level.footer_convention.

ENTITY DIRECTORY — Read the entities section from: {loan_data_path}

CSS PAGINATION — Read the stylesheet at:
.claude/skills/acos-loan-doc-generator/templates/pdf-styles.css

MANDATORY ASSEMBLY RULES:
──────────────────────────
1. Order sections per the canonical sequence.
2. Add document title, date, and table of contents at the top.
   Wrap the TOC in `<div class="toc">...</div>`.
3. Use `<h1>Section Title</h1>` for major section headings — the CSS
   applies `break-before: page` to h1, so each major section starts
   on a new page automatically.
4. Wrap each section in `<section class="chapter">` containing the `<h1>` title
   followed by the section's HTML content.

COMPLETE HTML DOCUMENT — CRITICAL:
5. Produce a COMPLETE HTML document with `<!DOCTYPE html>`, `<html>`, `<head>`, `<body>`.
6. In `<head>`, embed a `<style>` block containing the FULL contents of pdf-styles.css.
   This ensures pagination rules are present for both browser rendering and PDF conversion.
7. Generate an HTML table of contents inside `<div class="toc">` using `<ul>/<li>/<a href="#...">`.
   Each section's `<section>` tag should have a matching `id` attribute for anchor links.

FOOTER RULE — CRITICAL:
8. Scan ALL section content for any footer, signature block,
   certification lines, page numbers, or document-level metadata.
   REMOVE any such content from wherever it appears in sections.
9. Place ONE consolidated footer/signature block at the very end,
   wrapped in `<div class="footer-block">...</div>`, following the
   FOOTER CONVENTION from design patterns.
10. Exactly ONE footer. No more, no less (unless design patterns show none).

TABLE PROTECTION:
11. Wrap any table longer than 5 rows in `<div class="keep-together">...</div>`
    to prevent splitting across page boundaries.

[IF target_pages is not null]
LENGTH ENFORCEMENT:
12. After assembly, estimate total document length (~300 words per page).
   Target: {target_pages} pages. If any section exceeds its page_budget by
   more than 50%, add an assembler note flagging it. Do NOT truncate — just flag.

[IF images is not empty AND image_placement_strategy == "appendix"]
IMAGE APPENDIX:
13. Create an "Appendix: Property Images" section at the end (before footer).
    Place all images there using:
    <figure><img src="file://{path}" /><figcaption>{caption}</figcaption></figure>
    Wrap in `<div class="appendix-section">...</div>`.

[IF images is not empty AND image_placement_strategy != "appendix"]
IMAGE HANDLING:
14. Verify all `<figure>` tags from section designers are preserved.
    Each figure must use: <figure><img src="file://{path}" /><figcaption>...</figcaption></figure>
    Remove any duplicate image references across sections.

CONSISTENCY CHECK:
15. Check for cross-section inconsistencies (entity names, figures, dates, terms).
16. Flag inconsistencies as assembler notes — do NOT fix them.

Write assembled draft to:
.acos/loan-doc-generator/sessions/{session_id}/phase3-design/iteration-{N}/synthesis/document-draft.html

Write cross-section issues to:
.acos/loan-doc-generator/sessions/{session_id}/phase3-design/iteration-{N}/synthesis/assembler-notes.yaml
```

## Step 3.5: Convert to PDF

After the HTML document is assembled, convert it to PDF using Puppeteer.

**IMPORTANT — Page numbers are handled ONLY by Puppeteer's footerTemplate.**
The CSS stylesheet intentionally has NO @page @bottom-center content to avoid
duplicate/mirrored page numbers. Do NOT add CSS page counters.

Use the dedicated PDF conversion script (handles sandbox flags and base URL resolution):

```bash
node .claude/scripts/html-to-pdf.js "{html_path}" "{pdf_path}"
```

Do NOT use an inline Puppeteer snippet — use the script above which handles
`--no-sandbox` for containerized environments and resolves `file://` image paths.

Where:
- `{html_path}` = `.acos/loan-doc-generator/sessions/{session_id}/phase3-design/iteration-{N}/synthesis/document-draft.html`
- `{pdf_path}` = `.acos/loan-doc-generator/sessions/{session_id}/output/{document_slug}.pdf`
- `{document_slug}` = `document_title` slugified (e.g., "Internal Credit Memo" → "Internal-Credit-Memo")

**Puppeteer is REQUIRED. Do NOT fall back to markdown or raw HTML output.**
If Puppeteer fails, report the error and stop — do not produce a degraded output format.

## Step 3.5b: Convert to DOCX

After PDF generation succeeds, convert the same HTML to a styled DOCX using
the python-docx converter:

```bash
python3 .claude/scripts/html-to-docx.py "{html_path}" "{docx_path}"
```

Where:
- `{docx_path}` = `.acos/loan-doc-generator/sessions/{session_id}/output/{document_slug}.docx`

**IMPORTANT — Do NOT use plain pandoc for DOCX conversion.** Pandoc strips all CSS
and produces ugly, unstyled Word documents. The html-to-docx.py script uses
python-docx to programmatically apply navy headers, zebra-striped tables, colored
badges, proper fonts, and all styling that matches the PDF output.

If html-to-docx.py fails, fall back to pandoc as a last resort:
```bash
pandoc "{html_path}" -f html -o "{docx_path}" --wrap=none --standalone
```
But warn the user: "DOCX generated with limited styling — python-docx unavailable."

## Step 3.5c: Organize Output Directory

After both conversions complete:

1. The output directory should contain ONLY:
   - `{document_slug}.pdf` — Primary output
   - `{document_slug}.docx` — Editable output
   - No `.html`, `.md`, or other intermediate files

2. The HTML source is preserved as a working draft at:
   `.acos/loan-doc-generator/sessions/{session_id}/phase3-design/iteration-{N}/synthesis/document-draft.html`
   This is an intermediate artifact, NOT a deliverable.

3. If `output_destination` is set in the session manifest (user-specified path):
   Copy both PDF and DOCX to that destination in addition to the session output directory.

## Step 3.6: Return to Caller

**Return:**
```
Phase 3 iteration {N} complete.
- Sections written: {count} (carried forward: {count})
- PDF output: {pdf_path}
- DOCX output: {docx_path}
- Cross-section issues: {count from assembler-notes}
- Assembler notes: {assembler_notes_path}
```
