# Phase 4: Validation + Wigum Loop

You are the **Phase 4 Orchestrator** for the ACOS Loan Document Generator.
Your job: validate the document draft against benchmark criteria and manage the Wigum loop.

## HARD ITERATION CEILING

Regardless of `config.max_iterations`, if `current_iteration > 10`, ABORT
immediately with an error message:
"WIGUM LOOP EXCEEDED HARD CEILING (10 iterations). Returning last draft as-is."
This is a safety backstop — the configurable limit (default 5) should always
terminate before this ceiling. If this fires, something is wrong with convergence.

You receive a session manifest path as input.
Format: `{manifest_path}` (iteration is tracked in the session manifest's `current_iteration` field)

If current_iteration is 0 or null, treat as iteration 1 (first run).
In batch mode, read current_iteration from the batch_item corresponding to
the batch_index provided in the prompt, not from the top-level manifest.

When invoked by the `loan-doc-phase34` agent, the iteration parameter is managed internally by the phase34 agent. The first invocation starts at iteration=1. The phase34 agent reads both phase3-design.md and phase4-validate.md and handles the Wigum loop.

---

## PPTX Validation (conditional)

**If `catalog_entry.output_format == 'pptx'`**, run PPTX-specific validation:

### Gate A: Data & Code Validation
1. Execute: `python3 .claude/scripts/validate-pptx.py <pptx> <data> <spec> -o <report>`
2. Checks performed:
   - Text overflow: every shape's text fits within bounds
   - Boundary: no shape extends beyond slide edges
   - Data integrity: every number matches verified-data.yaml
   - Font compliance: correct font per content role (Courier New/Georgia/Calibri)
   - Color compliance: all RGB values in design spec palette
   - Anchor audit: all text_frames have vertical_anchor set
   - Margin audit: no default margins (all explicit)
3. Verdict: PASS if zero errors (warnings and info are advisory)
4. On FAIL: feed findings back to Phase 3 for the Wigum loop iteration

### Gate B: Layout Pre-Check
5. Execute: `python3 .claude/scripts/check-pptx-layout.py <pptx> -o <layout-report>`
6. Checks performed:
   - Shape boundary violations (extends beyond slide)
   - Shape-to-shape overlap detection
   - Text overflow estimation (character width × lines vs container height)
   - Footer collision detection
   - Margin compliance
   - Cross-slide consistency (header/footer/column positions)
   - Callout internal consistency (child shapes within parent)
7. On FAIL: feed coordinate-level fixes back to Phase 3

### Gate C: Visual Screenshot Verification
8. Execute: `python3 .claude/scripts/render-doc-audit.py <pptx> --output-dir <dir> --dpi 150`
   - **MANDATORY DPI ≤150.** Higher DPI produces PNGs >2000 px tall, which trips
     the Anthropic API many-image cap and locks the conversation in an
     unrecoverable image-error state. Follow up with `sips -Z 1800 <dir>/page-*.png`
     as a safety net for tabloid / A3 inputs.
9. Read EVERY rendered slide screenshot via the Read tool
   - **Batch the reads in groups of ~5–8 slides, then `/compact` between batches**
     for documents longer than 20 slides. The 2000 px cap is a per-conversation
     constraint — accumulated images can hit it even when each individual image
     is within limits. If you see `"image could not be processed and was removed"`
     even once, stop adding images and `/compact` before continuing.
10. Evaluate ALL visual criteria per Step 4.5.3 checklist (below):
    - Layout & overflow, typography, color & contrast, spacing & alignment,
      visual hierarchy, tables, cross-slide consistency
11. On any visual ERROR: feed screenshot + defect description back to Phase 3

**All three gates must PASS for PPTX validation to succeed.**
Gate A catches data errors. Gate B catches coordinate errors. Gate C catches
visual errors that neither A nor B can detect (color issues, density imbalance,
visual hierarchy problems, text wrapping artifacts).

**After all three gates complete, jump to Step 4.5 (Visual QA Gate) for the
formal screenshot review and reporting. Then proceed to Step 4.6 (Return to Caller).**

**For non-PPTX types**, continue with standard validation below (Steps 4.1–4.4),
then ALL formats go through Step 4.5 (Visual QA Gate).

## Step 4.1: Load Context

1. Read the session manifest YAML
2. Extract: `session_id`, `document_id`, `category_id`, `document_title`, `benchmark_criteria_path`,
   `loan_data_path`, `loan_data_brief_path`, `additional_instructions`,
   `figures_mode`, `user_figures_path`
3. Read `benchmark-criteria.yaml` at `benchmark_criteria_path`
4. Separate criteria by `validator_tier`:
   - `structural_criteria` — entries with `validator_tier: structural`
   - `quality_criteria` — entries with `validator_tier: quality`
5. Read config from `.acos/loan-doc-generator/config.yaml` (for `max_iterations`)
6. Locate current draft at:
   `.acos/loan-doc-generator/sessions/{session_id}/phase3-design/iteration-{N}/synthesis/document-draft.html`
7. Locate assembler notes at:
   `.acos/loan-doc-generator/sessions/{session_id}/phase3-design/iteration-{N}/synthesis/assembler-notes.yaml`

Read the validation-result template from:
`.claude/skills/acos-loan-doc-generator/templates/validation-result.yaml`

## Step 4.2: Launch Structural Validator (Haiku)

Spawn one structural validator covering all `structural_criteria`. Runs synchronously.

```
You are a Document Structure Validator.
Your job is CHECKLIST COMPLIANCE only — not qualitative judgment.

DOCUMENT DRAFT — Read the file at:
{draft_path}

STRUCTURAL CRITERIA (checklist):
{list all structural_criteria IDs and descriptions}

For each criterion:
- PASS: clearly met
- FAIL: clearly not met — quote exact evidence

ALWAYS CHECK STRUCT-001:
  Is there exactly ONE footer/signature block using <div class="footer-block">?
  Is it AFTER all sections, as the last major element before </body>?
  Does any section body contain footer, signature, or certification text?
  PASS: one <div class="footer-block"> at document end, none within sections.
  FAIL: footer within section body, multiple footers, missing footer, or non-HTML footer syntax.

ALWAYS CHECK STRUCT-002:
  Does the document include CSS pagination rules (pdf-styles.css or equivalent)?
  Are all headings (h1-h6) protected with break-after:avoid / page-break-after:avoid?
  Are tables and figures protected with break-inside:avoid?
  Are paragraph orphans/widows set to at least 3?
  Does h1 use break-before:page for major section starts?
  PASS: CSS pagination rules present, headings protected, tables/figures kept together.
  FAIL: missing CSS pagination rules, unprotected headings, split tables/figures.

ALWAYS CHECK STRUCT-003:
  HTML Well-Formedness
  Verify the document is valid HTML: all tags are properly closed, no unclosed
  <table>, <div>, or <section> tags. No raw markdown syntax (no `#`, `**`, `|---|`
  pipe tables). If any markdown syntax is detected in the document body, flag as
  FAIL — the document must be pure HTML.
  PASS: well-formed HTML, all tags closed, no markdown syntax in document body.
  FAIL: unclosed tags, raw markdown headings (#), bold (**), or pipe tables detected.

ALWAYS CHECK STRUCT-004:
  Visual Rendering Quality
  Check the HTML for rendering issues that would cause visual defects in PDF/DOCX:
  (a) No empty <section>, <div>, or <p> tags that create blank whitespace
  (b) No consecutive <br> tags (use margins/padding instead)
  (c) All tables have <thead> and <tbody> (required for header repeat on page break)
  (d) No inline styles that override the stylesheet (e.g., style="margin-top:50px")
      — except for chart SVGs and intentional color-coding classes
  (e) Every <h1> is inside a <section class="chapter"> wrapper
  (f) No text content outside of <section> tags (except document title area)
  (g) No adjacent identical content (duplicate paragraphs or tables)
  (h) All <img> tags have width/height or are inside a <figure> container
  PASS: clean HTML structure, no rendering hazards detected.
  FAIL: any of the above rendering hazards found — quote the specific HTML.

ALWAYS CHECK STRUCT-004b:
  Design Quality Rules (from STYLE-GUIDE-RESEARCH.yaml)
  Read the design quality rules at:
  .acos/loan-doc-generator/design-library/STYLE-GUIDE-RESEARCH.yaml
  Look under the `enforceable_quality_rules` key.

  Check ALL rules with severity: "required" (21 rules). Key checks include:
  - DESIGN-001: Max 2 font families in the document
  - DESIGN-002: Body font size 10-12pt
  - DESIGN-003: Heading sizes form a clear hierarchy (h1 > h2 > h3)
  - DESIGN-010: Page margins >= 0.75in on all sides
  - DESIGN-020: Table headers visually distinct (background color or bold + border)
  - DESIGN-021: Numeric columns right-aligned
  - DESIGN-022: Every table has <thead> and <tbody>
  - DESIGN-030: Max 5 distinct colors in the document
  - DESIGN-031: Text contrast ratio >= 4.5:1
  - DESIGN-040: Currency values use thousands separators ($X,XXX)
  - DESIGN-041: Negative values use parentheses, not minus signs
  - DESIGN-042: Percentages formatted consistently (X.X%)
  - DESIGN-043: Date formats consistent throughout
  - DESIGN-060: No skipped heading levels (h1→h2→h3, not h1→h3)
  - DESIGN-065: If section numbering used, single scheme throughout

  Also check "recommended" rules and report compliance percentage.
  DESIGN-099 composite gate: ALL required pass AND >= 80% recommended pass.

  PASS: DESIGN-099 composite gate passes.
  FAIL: Any required design rule fails — list each failure with rule ID and evidence.

ALWAYS CHECK STRUCT-005:
  HTML-to-PDF/DOCX Convertibility
  NOTE: Validation runs BEFORE PDF/DOCX conversion. Check the HTML structure
  for elements that would prevent clean conversion:
  (a) No JavaScript or interactive elements (they won't render in PDF/DOCX)
  (b) All images use file:// absolute paths or are embedded SVG
  (c) CSS is embedded in a <style> block (not external <link> stylesheet)
  (d) No external resource dependencies (all content self-contained in the HTML)
  (e) The HTML source is in phase3-design/iteration-N/synthesis/ (not output/)
  PASS: HTML is self-contained and will convert cleanly to PDF and DOCX.
  FAIL: HTML contains non-convertible elements — quote the specific issues.

Output matching schema:
{validation-result.yaml template contents}
Set validator_tier: structural

Write to:
.acos/loan-doc-generator/sessions/{session_id}/phase4-validation/iteration-{N}/structural/result.yaml
```

Use `model: haiku`.

**Wait for structural validator.** Read result.

If STRUCT-001 fails or any `severity: required` structural criterion fails:
1. Flag the issue
2. Spawn the assembler again (from Phase 3 Step 3.4 instructions) with explicit
   fix instruction for the structural issues
3. Re-run this structural validator on the corrected draft
4. Only proceed to quality validators after structural passes

Maximum 3 structural fix attempts. If STRUCT-001 still fails after 3 attempts:
- Record "structural-loop-exceeded" in the validation report
- Proceed to Step 4.3 quality validators (report structural failure to Wigum loop)

## Step 4.3: Launch Quality + Global Validators

Once structural passes, spawn ALL quality and global validators in a **SINGLE message**.

### Quality Validators (section-scoped)

Group `quality_criteria` by primary `applies_to` section. One validator per section with criteria.

```
You are an adversarial Quality Validator.
Your job is to find failures, not confirm success.

SCOPE: {section_name(s)}
DIMENSION: {benchmark dimension}

RELEVANT SECTIONS — Read the draft at:
{draft_path}
Extract ONLY the sections: {section_names}

QUALITY CRITERIA:
{quality_criteria mapped to these sections}

LOAN DATA BRIEF — Read section entries from:
{loan_data_brief_path}

GROUND TRUTH — For accuracy, read financial_figures and risk_factors from:
{loan_data_path}

ASSEMBLER NOTES — Read:
{assembler_notes_path}

Rules:
1. Check EVERY criterion — do not skip any
2. Be STRICT — if in doubt, mark FAIL
3. FAIL: quote specific evidence from the draft
4. FAIL: provide actionable fix instruction scoped to a section
5. Fabricated data not in loan data AND not in user-provided figures = automatic FAIL
6. If user_figures_path exists: figures matching user-provided values are CORRECT
   regardless of what loan-data.yaml says

Output matching schema:
{validation-result.yaml template contents}
Set validator_tier: quality

Write to:
.acos/loan-doc-generator/sessions/{session_id}/phase4-validation/iteration-{N}/quality/agent-{NN}/result.yaml
```

Use `run_in_background: true`, `model: sonnet`.

### Global Validators

Spawn alongside quality validators. Globals 1-3 are CONSOLIDATED into a single
Document Integrity Validator to avoid 3 redundant full-draft reads per iteration.

**Global 1 — Document Integrity (consolidated: entity + financial + coherence):**
```
You are the Document Integrity Validator.
You check THREE dimensions in a SINGLE pass over the document.

Read FULL draft at: {draft_path}
Read entity directory and financial_figures from: {loan_data_path}
Read assembler notes at: {assembler_notes_path}

[IF user_figures_path is not null]
USER-PROVIDED FIGURES — Read: {user_figures_path}
These are AUTHORITATIVE ground truth. Figures matching user-provided values
are CORRECT even if loan-data.yaml differs.

CHECK ALL THREE:

DIMENSION A — Entity Consistency:
  Every entity referred to by same name/role throughout.
  Flag: different names for same entity, conflicting roles/descriptions.

DIMENSION B — Financial Figure Accuracy:
  (a) Figures consistent across sections (b) no figure contradicts ground truth.
  Flag: same figure with different values in different sections, untraceable figures.
  If user_figures_path exists: only flag figures contradicting USER-PROVIDED values.

DIMENSION C — Cross-Section Coherence:
  Coherent story end-to-end. Risks addressed, conclusion follows body,
  no contradictions, appropriate narrative arc.

Output a SINGLE result file with all three dimensions:
Write to: .../phase4-validation/iteration-{N}/global/integrity/result.yaml
```

Use `run_in_background: true`, `model: sonnet`.

**Global 2 — User Instructions Compliance (lightweight — no full draft read needed if no instructions):**
```
You are the User Instructions Compliance Validator.

Read FULL draft at: {draft_path}

[IF additional_instructions is not null]
USER INSTRUCTIONS: {additional_instructions}
For each instruction: was it incorporated? Clear violation = FAIL.

[IF additional_instructions is null]
No user instructions. Output minimal result: verdict PASS, all N/A.

Write to: .../phase4-validation/iteration-{N}/global/instructions/result.yaml
```

**Global 3 — Chart & Ratio Accuracy (conditional):**

Only spawn this validator if `selected_charts` is not null/empty in the session manifest.

```
You are the Chart & Ratio Accuracy Validator.

Read FULL draft at: {draft_path}
Read financial_figures from: {loan_data_path}

Read the recommendation matrix config at:
.acos/loan-doc-generator/recommendation-matrix.yaml

TASK:
1. For each chart/SVG in the document, verify the data values match loan-data.yaml
2. For each ratio displayed (LTV, DSCR, Debt Yield, etc.), independently recalculate
   from the source values in loan-data.yaml and verify the document's value matches
3. For the recommendation matrix: read pillar_weights, categories, and override_rules
   from the config. Recalculate the composite score independently. Verify the
   document's score matches. Verify the color/category matches the config thresholds.
4. For credit memos: verify all charts listed in config `must_have_charts` are present

VERDICT:
- Ratio mismatch > 0.1% = FAIL (required)
- Missing must-have chart in credit memo = FAIL (required)
- Chart data not matching source = FAIL (required)
- Wrong recommendation color/category = FAIL (required)

Write to: .../phase4-validation/iteration-{N}/global/charts/result.yaml
```

**Global 4 — Page Count Compliance (conditional):**

Only spawn this validator if `target_pages` is not null in the session manifest.

```
You are the Page Count Compliance Validator.

Read FULL draft at: {draft_path}

TARGET: {target_pages} pages (~{target_pages * 300} words).
PER-SECTION BUDGETS: {page_budget dict from manifest}

TASK:
1. Count total words in the document (excluding HTML tags and CSS).
2. Estimate total pages (words / 300).
3. For each section, count words and estimate pages.
4. Compare to budgets.

VERDICT RULES (severity: recommended, NOT required):
- Total within ±30% of target: PASS
- Any section >2x its budget: NOTE (not FAIL)
- Total >2x target or <0.3x target: FAIL

This validator uses severity: recommended — failures here do NOT
block the Wigum loop. They appear as notes for user awareness.

Write to: .../phase4-validation/iteration-{N}/global/page-count/result.yaml
```

Use `run_in_background: true`, `model: sonnet` for all globals.

## Step 4.4: Aggregate Validation Results

Wait for ALL validators, then spawn aggregator (model: opus):

```
You are the Validation Aggregator.

TASK: Read all validation results and produce a unified report.

Read structural results:
.acos/loan-doc-generator/sessions/{session_id}/phase4-validation/iteration-{N}/structural/result.yaml

Read ALL quality results matching:
.../phase4-validation/iteration-{N}/quality/agent-*/result.yaml

Read ALL global results matching:
.../phase4-validation/iteration-{N}/global/*/result.yaml

Some global validators may not have been spawned (e.g., charts validator when
no charts selected, page count when target_pages is null). If a global result
file does not exist, treat that validator as N/A — no pass/fail contribution.

Produce validation-report.yaml with:

overall:
  iteration: N
  total_criteria: [count]
  passed: [count]
  failed: [count]
  pass_rate: "[percentage]"
  required_failures: [count of FAIL with severity=required]
  verdict: "PASS|FAIL"

by_validator_tier:
  structural: {passed, failed, verdict}
  quality: {passed, failed, verdict}
  global: {passed, failed, verdict}

failures:
  - criterion_id, criterion_name, severity, validator_tier,
    affected_sections, failure_detail, fix_instruction

feedback_by_section:
  "[section_name]":
    - criterion_id, instruction, severity

convergence:
  previous_failure_count: [or null]
  current_failure_count: N
  improving: true|false
  stuck: true|false

Write to:
.acos/loan-doc-generator/sessions/{session_id}/phase4-validation/iteration-{N}/synthesis/validation-report.yaml
```

## Step 4.5: Visual QA Gate (Screenshot-First Verification)

**This gate applies to ALL output formats (PPTX, PDF, DOCX).** The principle:
**for design, the screenshot IS the source of truth, not the code.** A document
that passes all code-level checks but looks wrong in a screenshot is a FAIL.

### Step 4.5.1: Render Screenshots

Determine the document path based on output format:
- **PPTX:** `{session_dir}/output/{document_slug}.pptx`
- **PDF:** `{session_dir}/output/{document_slug}.pdf`
- **DOCX:** `{session_dir}/output/{document_slug}.docx`

Run the universal renderer:
```bash
python3 .claude/scripts/render-doc-audit.py \
  {document_path} \
  --output-dir {session_dir}/visual-audit/iteration-{N}/ \
  --dpi 150
```

This produces:
- One PNG per page/slide: `page_01.png` / `slide_01.png`
- A defect summary: `audit-summary.yaml` (includes programmatic defects)

After rendering completes, read the audit summary:
`{session_dir}/visual-audit/iteration-{N}/audit-summary.yaml`

If the summary contains any defects with severity ERROR, these are immediate
Gate 2 failures — feed them back to Phase 3 without needing screenshot review.
This applies to ALL formats (PPTX, PDF, DOCX), not just PPTX.

### Step 4.5.2: Code-Level Pre-Check (PPTX and PDF only)

**For PPTX:** Run the fast layout checker first:
```bash
python3 .claude/scripts/check-pptx-layout.py \
  {document_path} \
  -o {session_dir}/visual-audit/iteration-{N}/layout-check.yaml
```

**For PDF:** Run the PDF layout checker:
```bash
python3 .claude/scripts/check-pdf-layout.py \
  {document_path} \
  -o {session_dir}/visual-audit/iteration-{N}/layout-check.yaml
```

If the code-level checker finds ERRORS: these are immediate FAIL items — feed
them back to Phase 3 without needing screenshot review (they're definitively broken).

If code-level passes or only has WARNINGS: proceed to visual review.

### Step 4.5.3: Visual Screenshot Review

**Screenshot dimension safety (MANDATORY).** All screenshots must be rendered
at ≤150 DPI (US Letter → 1275×1650 px) and post-processed with `sips -Z 1800`
to enforce a 1800 px ceiling. The Anthropic API rejects many-image requests
where any image exceeds 2000 px on either edge; tripping this cap locks the
conversation until manual `/compact` or `/clear`. The render command in Gate C
above already enforces this — if you are re-rendering or reading screenshots
generated elsewhere, verify dimensions with `sips -g pixelWidth -g pixelHeight`
before starting the Read loop.

**Read EVERY screenshot** using the Read tool — one page/slide at a time.
**For documents >20 pages, `/compact` between batches of ~5–8 reads** to keep
the cumulative image count from retroactively tripping the cap. The very first
`"image could not be processed and was removed"` warning means the buffer is
already degraded — stop and `/compact` before continuing.

For EACH screenshot, evaluate ALL of the following criteria:

**Layout & Overflow:**
- [ ] All text fits within its container — no clipping, no text-on-text
- [ ] No elements overlap or collide
- [ ] No shapes extend beyond page/slide boundaries
- [ ] Tables are fully visible — no rows cut off
- [ ] Images are properly placed — no placeholders visible

**Typography:**
- [ ] Font sizes are consistent within each role (headings, body, captions)
- [ ] Font families are consistent — no unexpected font changes
- [ ] Text is readable — no text too small or too light
- [ ] Bold/italic used consistently for emphasis

**Color & Contrast:**
- [ ] Text has sufficient contrast against its background
- [ ] Color palette is consistent across all pages/slides
- [ ] Header/footer colors are consistent
- [ ] Table header colors are consistent
- [ ] No jarring color combinations

**Spacing & Alignment:**
- [ ] Consistent margins on all pages/slides
- [ ] Consistent spacing between elements
- [ ] Left/right column alignment is consistent across pages/slides
- [ ] No orphaned headers (section title at bottom of page with body on next)
- [ ] No widow lines (single line stranded at top of page)

**Visual Hierarchy & Balance:**
- [ ] Titles visually dominate — clear reading order
- [ ] Key metrics/numbers stand out (larger, bolder)
- [ ] Content density is balanced — no half-empty pages next to packed pages
- [ ] Section headers clearly delineate sections

**Tables & Charts:**
- [ ] Table columns are properly aligned (numbers right-aligned)
- [ ] Table headers are visually distinct from body rows
- [ ] Table styling is consistent across all tables in the document
- [ ] Charts (if any) are legible and properly labeled

**Page Breaks (PDF/DOCX only):**
- [ ] Page breaks occur at sensible locations
- [ ] No tables split awkwardly across pages
- [ ] Headers are not stranded at bottom of pages

**Cross-Page/Slide Consistency:**
- [ ] Header bar position identical across all content pages/slides
- [ ] Footer position identical across all content pages/slides
- [ ] Column alignment consistent across pages/slides
- [ ] Font usage consistent across pages/slides
- [ ] Table styling consistent across pages/slides

### Step 4.5.4: Visual Defect Reporting

For each screenshot defect found, record:
```yaml
visual_defects:
  - page: 4
    category: "overlap"
    description: "Capital Stack text overflows into OUR ENTRY POINT header"
    severity: ERROR
    fix_instruction: "Increase text box height or move OUR ENTRY POINT down by 200000 EMU"
  - page: 2
    category: "color"
    description: "Footer text contrast too low against white background"
    severity: WARNING
    fix_instruction: "Darken footer text color from #C0C0C0 to #787F7C"
```

Write visual defect report to:
`{session_dir}/visual-audit/iteration-{N}/visual-defects.yaml`

### Step 4.5.5: Visual Gate Decision

**PASS criteria:** Zero visual defects with severity ERROR.
Warnings are noted but do not block.

**FAIL criteria:** Any visual defect with severity ERROR.
Feed ALL error-level visual defects back to Phase 3 with:
- The screenshot path (so Phase 3 can reference the visual)
- The specific defect description
- The fix instruction with coordinates where applicable

### Step 4.5.6: Cross-Page/Slide Consistency Check

After reviewing all individual pages/slides, do a consistency sweep:
1. Compare header positions across all content pages/slides
2. Compare footer positions
3. Compare margin usage
4. Compare font sizes for same-role elements (e.g., all section headers should be same size)
5. Compare table styling

Any inconsistency = WARNING (not ERROR) unless it's visually jarring.

Write consistency report to:
`{session_dir}/visual-audit/iteration-{N}/consistency-check.yaml`

---

## Step 4.6: Return to Caller

Read the validation report AND the visual defect report. Combine into final decision:

**Overall Verdict Logic:**
1. If structural/quality validation FAILED: verdict = FAIL (data/content issues)
2. If visual QA gate FAILED: verdict = FAIL (design issues)
3. If both passed: verdict = PASS

Return the combined decision data:

```
Phase 4 iteration {N} complete.
- Data/Content validation:
  - Total criteria: {count}
  - Passed: {count} ({pass_rate})
  - Failed: {count} (required: {required_failures})
- Visual QA gate:
  - Screenshots rendered: {count}
  - Visual defects (ERROR): {count}
  - Visual defects (WARNING): {count}
  - Consistency issues: {count}
- Combined verdict: {PASS|FAIL}
- Convergence: {improving|stuck|first_iteration}
- Sections needing rewrite: {list from feedback_by_section}
- Visual fixes needed: {list from visual_defects}
- Validation report: {report_path}
- Visual audit: {visual_audit_dir}
```

The caller (SKILL.md router) handles Wigum loop decisions based on this data.
The **visual gate is authoritative** — if data validation passes but visual QA
fails, the overall verdict is FAIL and the Wigum loop continues.
