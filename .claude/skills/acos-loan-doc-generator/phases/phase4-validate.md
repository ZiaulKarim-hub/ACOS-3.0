# Phase 4: Validation + Wigum Loop

You are the **Phase 4 Orchestrator** for the ACOS Loan Document Generator.
Your job: validate the document draft against benchmark criteria and manage the Wigum loop.

You receive a session manifest path as input.
Format: `{manifest_path}` (iteration is tracked in the session manifest's `current_iteration` field)

When invoked by the `loan-doc-phase34` agent, the iteration parameter is managed internally by the phase34 agent. The first invocation starts at iteration=1. The phase34 agent reads both phase3-design.md and phase4-validate.md and handles the Wigum loop.

---

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

## Step 4.5: Return to Caller

Read the validation report. Return the decision data:

```
Phase 4 iteration {N} complete.
- Total criteria: {count}
- Passed: {count} ({pass_rate})
- Failed: {count} (required: {required_failures})
- Verdict: {PASS|FAIL}
- Convergence: {improving|stuck|first_iteration}
- Sections needing rewrite: {list from feedback_by_section}
- Validation report: {report_path}
```

The caller (SKILL.md router) handles Wigum loop decisions based on this data.
