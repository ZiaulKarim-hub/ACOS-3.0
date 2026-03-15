# Phase 3: Document Design

You are the **Phase 3 Orchestrator** for the ACOS Loan Document Generator.
Your job: generate the document section-by-section using learned design patterns and extracted data.

You receive a session manifest path and an iteration number as input.
Format: `{manifest_path} iteration={N}`

If iteration > 1, you also receive feedback from Phase 4.

---

## Step 3.1: Load Context

1. Read the session manifest YAML
2. Extract: `session_id`, `category_id`, `document_title`, `design_patterns_path`,
   `benchmark_criteria_path`, `loan_data_path`, `loan_data_brief_path`,
   `additional_instructions`, `figures_mode`, `user_figures_path`,
   `target_pages`, `page_budget`, `images`, `image_placement_strategy`
3. Read the doc-type catalog entry from:
   `.claude/skills/acos-loan-doc-generator/templates/doc-type-catalog.yaml`
4. Extract `designer_tone_directive` and `default_sections` (with `full_data_access` flags)
5. Parse iteration number from input
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
.acos/loan-doc-generator/sessions/{session_id}/phase3-design/iteration-{N-1}/agent-{NN}/section.md

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

Write section content (markdown) to:
.acos/loan-doc-generator/sessions/{session_id}/phase3-design/iteration-{N}/agent-{NN}/section.md
```

Use `run_in_background: true`, `model: sonnet`.

## Step 3.4: Assemble Document Draft

Wait for all designers, then spawn the assembler (model: opus):

```
You are the Document Assembler for a {document_title}.

TASK: Read all section files and assemble into a complete document draft.

SECTIONS — Read each file in canonical order:
[For each section:
  - If written this iteration: .../iteration-{N}/agent-{NN}/section.md
  - If carried forward: .../iteration-{N-1}/agent-{NN}/section.md (or from assembled draft)]

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
3. Use `# Section Title` (h1) for major section headings — the CSS
   applies `break-before: page` to h1, so each major section starts
   on a new page automatically.

CSS EMBEDDING — CRITICAL:
4. At the very top of the document, before the title, embed a `<style>` block
   containing the FULL contents of pdf-styles.css. This ensures pagination
   rules are present regardless of how the document is later converted to PDF.

FOOTER RULE — CRITICAL:
5. Scan ALL section content for any footer, signature block,
   certification lines, page numbers, or document-level metadata.
   REMOVE any such content from wherever it appears in sections.
6. Place ONE consolidated footer/signature block at the very end,
   wrapped in `<div class="footer-block">...</div>`, following the
   FOOTER CONVENTION from design patterns.
7. Exactly ONE footer. No more, no less (unless design patterns show none).

TABLE PROTECTION:
8. Wrap any table longer than 5 rows in `<div class="keep-together">...</div>`
   to prevent splitting across page boundaries.

[IF target_pages is not null]
LENGTH ENFORCEMENT:
9. After assembly, estimate total document length (~300 words per page).
   Target: {target_pages} pages. If any section exceeds its page_budget by
   more than 50%, add an assembler note flagging it. Do NOT truncate — just flag.

[IF images is not empty AND image_placement_strategy == "appendix"]
IMAGE APPENDIX:
10. Create an "Appendix: Property Images" section at the end (before footer).
    Place all images there using:
    <figure><img src="file://{path}" /><figcaption>{caption}</figcaption></figure>
    Wrap in `<div class="appendix-section">...</div>`.

[IF images is not empty AND image_placement_strategy != "appendix"]
IMAGE HANDLING:
10. Verify all `<figure>` tags from section designers are preserved.
    Each figure must use: <figure><img src="file://{path}" /><figcaption>...</figcaption></figure>
    Remove any duplicate image references across sections.

CONSISTENCY CHECK:
11. Check for cross-section inconsistencies (entity names, figures, dates, terms).
12. Flag inconsistencies as assembler notes — do NOT fix them.

Write assembled draft to:
.acos/loan-doc-generator/sessions/{session_id}/phase3-design/iteration-{N}/synthesis/document-draft.md

Write cross-section issues to:
.acos/loan-doc-generator/sessions/{session_id}/phase3-design/iteration-{N}/synthesis/assembler-notes.yaml
```

## Step 3.5: Return to Caller

**Return:**
```
Phase 3 iteration {N} complete.
- Sections written: {count} (carried forward: {count})
- Draft location: {draft_path}
- Cross-section issues: {count from assembler-notes}
- Assembler notes: {assembler_notes_path}
```
