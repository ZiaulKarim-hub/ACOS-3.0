# Phase 2: Loan Folder Analysis

You are the **Phase 2 Orchestrator** for the ACOS Loan Document Generator.
Your job: analyze the loan folder and extract all relevant data for document generation.

You receive a session manifest path as your input. Read it first.

---

## Step 2.1: Load Context

1. Read the session manifest YAML at the path provided
2. Extract: `loan_folder_path`, `document_id`, `category_id`, `document_title`, `session_id`,
   `design_patterns_path`, `figures_mode`, `user_figures_path`
3. Read the `catalog_entry` directly from the session manifest (embedded by Phase 0).
   If missing, fall back to reading from: `.claude/skills/acos-loan-doc-generator/templates/doc-type-catalog.yaml`
4. Read the design patterns file at `design_patterns_path`
5. Extract: canonical sections list + section-specific data expectations

**Batch mode:** If `batch_mode: true`, iterate over `batch_items[]` and read each
item's `design_patterns_path`. Build a union of all canonical sections and their
data expectations. Extract data to satisfy ALL document types in the batch.

6. Read config from `.acos/loan-doc-generator/config.yaml`
7. **If `user_figures_path` is not null:** Read the user-figures YAML file.
   Parse all non-empty fields into `user_figures` dict. These are GROUND TRUTH.

**Batch mode handling:** If the manifest contains `batch_mode: true`, there is no
top-level `document_id`, `category_id`, or `document_title`. Instead:
- Use the first batch item's `document_id` to load a representative catalog entry
  for section structure reference, OR
- Read design patterns from ALL batch items' `design_patterns_path` entries to
  build a union of expected sections and data fields
- The loan folder analysis should extract ALL data comprehensively — batch mode
  requires data for multiple document types from the same folder

## Step 2.2: Inventory Loan Folder

1. Glob: `**/*.{pdf,docx,doc,xlsx,xls,csv,txt,md,jpg,png,tif}` in `loan_folder_path`
2. Classify each document by type:
   - `financial-statement` — P&L, balance sheet, cash flow
   - `appraisal` — property valuations, assessments
   - `tax-return` — federal/state tax filings
   - `legal-doc` — agreements, guarantees, UCC, title
   - `insurance` — policies, certificates, binders
   - `environmental` — Phase I/II, environmental assessments
   - `borrower-application` — applications, personal financials
   - `third-party-report` — market studies, engineering, inspections
   - `other` — anything else
3. Log inventory summary (count by type)

### Step 2.2b: Pre-Process XLSX Files

**For every .xlsx or .xlsm file found in the inventory**, run the XLSX extraction
utility BEFORE assigning files to analyzer agents:

```bash
python3 .claude/scripts/xlsx-extract.py "{xlsx_path}" \
  --output ".acos/loan-doc-generator/sessions/{session_id}/phase2-analysis/xlsx-extracts/{filename}.yaml"
```

This produces structured YAML with:
- Cell-level values with addresses (e.g., `Sheet1!B7`)
- Formula detection (both the formula string and computed value)
- Currency/percentage/date type classification
- Merged cell handling
- Named range resolution

The extracted YAML replaces the raw .xlsx file in the agent assignment. Analyzer
agents receive the YAML extraction instead of trying to Read the .xlsx directly
(which produces unreliable results). The YAML includes full provenance (file,
sheet, cell address) for every data point.

Log: `"Pre-processed {N} XLSX files → structured YAML with cell-level provenance"`

## Step 2.3: Determine Analyzer Strategy

Read `config.generation.analyzer_strategy`:
- `per-doc` — 1 agent per document
- `by-type` — 1 agent per document type group
- `auto` (default) — if doc count > `config.generation.auto_strategy_threshold` (10), use `by-type`

Calculate agent count: clamp between `config.generation.min_analyzers` (3)
and `config.generation.max_analyzers` (15).

## Step 2.4: Launch Analyzer Swarm

Read the loan-data-extract template from:
`.claude/skills/acos-loan-doc-generator/templates/loan-data-extract.yaml`

**Spawn ALL analyzer agents simultaneously in a SINGLE message:**

Each agent prompt:
```
You are a Loan Document Analyzer.

DOCUMENT BEING GENERATED: {document_title}
CATEGORY: {catalog_entry.label}

TASK: Read the assigned documents and extract all data relevant to
generating a {document_title}.

ASSIGNED DOCUMENTS (read each using your Read tool):
{list of file paths assigned to this agent}

NOTE ON XLSX FILES: Any .xlsx files have been pre-processed into structured
YAML with cell-level provenance. You will receive the YAML extraction path
instead of the raw .xlsx path. The YAML contains exact cell values, formulas,
addresses, and type classifications. Use these extractions as your primary
source for spreadsheet data — they are more reliable than reading .xlsx directly.

CANONICAL SECTIONS TO MAP DATA TO:
{section names from design-patterns.yaml}

SECTION-SPECIFIC DATA EXPECTATIONS:
{section-specific guidance from design-patterns.yaml}

Extract into YAML matching the schema at:
.claude/skills/acos-loan-doc-generator/templates/loan-data-extract.yaml
Read this template file using your Read tool — do NOT expect it embedded in this prompt.

Rules:
1. Extract EXACT values — never round, estimate, or interpret
2. Record source document, page (or cell address for XLSX), and file path for every data point
3. Map every fact to one or more document sections
4. Flag contradictions across documents
5. Note missing data — what SHOULD be here but isn't
6. Extract ALL entities, financial figures, risk factors, conditions
7. For XLSX-sourced data: preserve the cell reference (e.g., "Sheet1!B7") as provenance
8. For calculated values from XLSX: note the formula and input cells

[IF figures_mode is "user" or "hybrid"]
NOTE: The user has provided authoritative financial figures separately.
Focus your extraction on: entities, narrative context, risk factors,
conditions/covenants, property details, borrower background, and
qualitative data. You do NOT need to deep-extract loan amounts, rates,
ratios, or financial metrics — those are provided by the user.
Still extract any figures you encounter for cross-reference verification,
but prioritize qualitative and contextual data.

Write to:
.acos/loan-doc-generator/sessions/{session_id}/phase2-analysis/agent-{NN}/extract.yaml
```

Use `run_in_background: true`, `model: sonnet`.

## Step 2.5: Synthesize — Full + Brief

Wait for all analyzers. Read the loan-data-brief template from:
`.claude/skills/acos-loan-doc-generator/templates/loan-data-brief.yaml`

Spawn synthesizer (model: opus):

```
You are the Loan Data Synthesizer.

TASK: Read ALL analyzer findings and produce TWO output files.

Read ALL files matching:
.acos/loan-doc-generator/sessions/{session_id}/phase2-analysis/agent-*/extract.yaml

── OUTPUT 1: Full loan-data.yaml ──
Complete unified dataset:
1. MERGED DATA BY SECTION — all facts organized by section, deduplicated
2. ENTITY DIRECTORY — all entities with roles and relationships
3. FINANCIAL FIGURES — all financials in a sortable table, each with:
   - value, display_value, source_document, source_page_or_cell, file_path
   - confidence (0.0-1.0), source_count (how many docs confirm this value)
   - is_calculated (bool), calculation_formula (if derived)
   - cross_validated (bool) — true if 2+ independent sources agree
4. RISK FACTORS — consolidated risk register
5. CONDITIONS — all conditions/covenants in one list
6. CROSS-REFERENCE ISSUES — contradictions across documents
7. DATA COMPLETENESS — per-section assessment (present vs. expected)
8. CROSS-VALIDATION SUMMARY — for every financial figure:
   - How many independent sources confirm the value
   - List of confirming sources with page/cell references
   - Flag "single-source" figures with confidence < 0.8
   - Flag contradictions with all conflicting values and sources

CROSS-VALIDATION RULES:
- A figure confirmed by 2+ independent documents: confidence >= 0.9, cross_validated: true
- A figure from only 1 document: confidence <= 0.7, cross_validated: false, flagged as "single-source"
- A figure contradicted by another document: both values kept, flagged in CROSS-REFERENCE ISSUES
- XLSX formula-derived values: trace input cells to their sources for transitive validation
- User-provided figures are ALWAYS confidence: 1.0 and cross_validated: true (ground truth)

When multiple agents extracted the same fact, keep higher confidence.

[IF user_figures_path is not null]
USER-PROVIDED FIGURES (GROUND TRUTH):
Read the user figures file at: {user_figures_path}
For every field the user provided:
- Insert it into the merged data with `source: "user_input"` and `confidence: 1.0`
- If an agent extracted a DIFFERENT value for the same field, keep BOTH but mark
  the user value as authoritative: `authoritative: true`
- Log the conflict in CROSS-REFERENCE ISSUES with a note:
  "User-provided value ({user_value}) differs from extracted value ({agent_value})
   from {source_doc}. User value used as authoritative."

If figures_mode is "user" (not "hybrid"), analyzers may have been instructed to
skip deep financial extraction. Ensure user figures fill any resulting gaps.

Write to:
.acos/loan-doc-generator/sessions/{session_id}/phase2-analysis/synthesis/loan-data.yaml

── OUTPUT 2: Compact loan-data-brief.yaml ──
Per-section brief matching this schema:
{loan-data-brief.yaml template contents}

For each section in the canonical section list:
- Include ONLY 3–8 most section-relevant key facts
- Include only essential entities and financials for that section
- Every fact must have source citation
- Distill — do NOT truncate. Select the most important facts.

EXCLUDE these sections from the brief (they use full data directly):
{sections where full_data_access: true from catalog entry}

Write to:
.acos/loan-doc-generator/sessions/{session_id}/phase2-analysis/synthesis/loan-data-brief.yaml
```

## Step 2.5b: Generate Data Verification Table

After synthesis completes, generate a comprehensive verification table from loan-data.yaml.
This table will be presented to the user for accuracy review BEFORE document generation.

Spawn verification table generator (model: sonnet):

```
You are the Data Verification Table Generator.

TASK: Read the synthesized loan data and produce a verification table that lists
EVERY data point that will appear in the generated document, with full provenance.

Read the full loan data at:
.acos/loan-doc-generator/sessions/{session_id}/phase2-analysis/synthesis/loan-data.yaml

For EVERY data point (financial figures, entity names, addresses, dates, rates,
ratios, conditions, property details), produce a table entry with:

  data_point: "Loan Amount"
  value: "$2,100,000"
  type: "extracted"          # extracted | calculated | user-provided
  source_document: "Loan Agreement.pdf"
  source_location: "Page 2, Paragraph 1"  # or "Sheet1!B7" for XLSX
  file_link: "file:///path/to/Loan Agreement.pdf"
  confidence: 0.95
  cross_validated: true
  confirming_sources: 3      # number of independent sources
  section_used_in: ["Executive Summary", "Transaction Summary"]

For CALCULATED values, also include:
  calculation:
    formula: "LTV = Loan Amount / Property Value"
    inputs:
      - name: "Loan Amount"
        value: "$2,100,000"
        source: "Loan Agreement.pdf, Page 2"
      - name: "Property Value"
        value: "$3,200,000"
        source: "Appraisal.pdf, Page 5"
    result: "65.6%"

Group entries by document section. Flag any entries where:
- confidence < 0.8 (mark as "⚠ LOW CONFIDENCE")
- cross_validated is false (mark as "⚠ SINGLE SOURCE")
- type is "calculated" (mark as "📊 CALCULATED")

Write to:
.acos/loan-doc-generator/sessions/{session_id}/phase2-analysis/synthesis/verification-table.yaml
```

Update the session manifest with `verification_table_path`.

## Step 2.6: Write Phase 2 Cache Manifest

1. Compute `loan_folder_fingerprint`:
   - List all files in `loan_folder_path` recursively with sizes
   - Sort, concatenate filenames+sizes, compute sha256
   - If any file cannot be stat'd (permission denied, broken symlink), skip it with
     a warning log and exclude it from the fingerprint. Include the count of skipped
     files in the cache manifest for transparency.
2. Create `.acos/loan-doc-generator/cache/{loan_folder_fingerprint}/` directory
3. Write `phase2-cache-manifest.yaml`:
```yaml
loan_folder_path: "{loan_folder_path}"
loan_folder_fingerprint: "{fingerprint}"
file_count: N
folder_mtime: "YYYY-MM-DD HH:MM:SS"
date_analyzed: "YYYY-MM-DD HH:MM:SS"
loan_data_path: ".acos/loan-doc-generator/sessions/{session_id}/phase2-analysis/synthesis/loan-data.yaml"
loan_data_brief_path: ".acos/loan-doc-generator/sessions/{session_id}/phase2-analysis/synthesis/loan-data-brief.yaml"
session_id: "{session_id}"
```

## Step 2.7: Update Session Manifest & Return

Update the session manifest with:
- `loan_data_path`
- `loan_data_brief_path`
- `current_phase: 3`

**Return to caller:**
```
Phase 2 complete.
- Documents analyzed: {count}
- Analyzer agents: {count}
- Data completeness: {per-section summary}
- Cross-reference issues: {count}
- Entities found: {count}
- Financial figures: {count}
- Loan data: {loan_data_path}
- Loan data brief: {loan_data_brief_path}
- Cache written: {fingerprint}
```
