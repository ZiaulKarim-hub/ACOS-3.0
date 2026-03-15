# Phase 4: Validation + Wigum Loop

You are the **Phase 4 Orchestrator** for the ACOS Loan Document Generator.
Your job: validate the document draft against benchmark criteria and manage the Wigum loop.

You receive a session manifest path and iteration number as input.
Format: `{manifest_path} iteration={N}`

---

## Step 4.1: Load Context

1. Read the session manifest YAML
2. Extract: `session_id`, `category_id`, `document_title`, `benchmark_criteria_path`,
   `loan_data_path`, `loan_data_brief_path`, `additional_instructions`,
   `figures_mode`, `user_figures_path`
3. Read `benchmark-criteria.yaml` at `benchmark_criteria_path`
4. Separate criteria by `validator_tier`:
   - `structural_criteria` — entries with `validator_tier: structural`
   - `quality_criteria` — entries with `validator_tier: quality`
5. Read config from `.acos/loan-doc-generator/config.yaml` (for `max_iterations`)
6. Locate current draft at:
   `.acos/loan-doc-generator/sessions/{session_id}/phase3-design/iteration-{N}/synthesis/document-draft.md`
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
  Is there exactly ONE footer/signature block?
  Is it AFTER all sections, following a horizontal rule (---)?
  Does any section body contain footer, signature, or certification text?
  PASS: one footer at document end, none within sections.
  FAIL: footer within section body, multiple footers, or missing footer.

ALWAYS CHECK STRUCT-002:
  Does the document include CSS pagination rules (pdf-styles.css or equivalent)?
  Are all headings (h1-h6) protected with break-after:avoid / page-break-after:avoid?
  Are tables and figures protected with break-inside:avoid?
  Are paragraph orphans/widows set to at least 3?
  Does h1 use break-before:page for major section starts?
  PASS: CSS pagination rules present, headings protected, tables/figures kept together.
  FAIL: missing CSS pagination rules, unprotected headings, split tables/figures.

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

### Global Validators (4 agents, full draft)

Spawn all 4 simultaneously alongside quality validators.

**Global 1 — Entity Consistency:**
```
You are the Entity Consistency Validator.

Read FULL draft at: {draft_path}
Read entity directory from: {loan_data_path}

Check: every entity referred to by same name/role throughout.
Flag: different names for same entity, conflicting roles/descriptions.

Write to: .../phase4-validation/iteration-{N}/global/entity/result.yaml
```

**Global 2 — Financial Figure Accuracy:**
```
You are the Financial Figures Validator.

Read FULL draft at: {draft_path}
Read financial_figures from: {loan_data_path}

Check: (a) figures consistent across sections (b) no figure contradicts ground truth.
Flag: same figure with different values in different sections, untraceable figures.

[IF user_figures_path is not null]
USER-PROVIDED FIGURES — Read: {user_figures_path}
These are AUTHORITATIVE ground truth. If a figure in the document matches
a user-provided value, it is CORRECT even if loan-data.yaml has a different
extracted value. Only flag figures that contradict USER-PROVIDED values.
Figures that contradict only extracted (non-user) values should be noted
but NOT marked as FAIL.

Write to: .../phase4-validation/iteration-{N}/global/financials/result.yaml
```

**Global 3 — Cross-Section Coherence:**
```
You are the Cross-Section Coherence Validator.

Read FULL draft at: {draft_path}
Read assembler notes at: {assembler_notes_path}

Check: coherent story end-to-end. Risks addressed, conclusion follows body,
no contradictions, appropriate narrative arc.

Write to: .../phase4-validation/iteration-{N}/global/coherence/result.yaml
```

**Global 4 — User Instructions Compliance:**
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

**Global 5 — Page Count Compliance (conditional):**

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
