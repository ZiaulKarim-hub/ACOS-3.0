---
name: acos-underwriting-pipeline
description: |
  End-to-end underwriting pipeline for new loan deals. Runs 6 phases: deal setup,
  document inventory & triage, collateral & sponsor analysis, financial modeling,
  underwriting synthesis, and batch document generation via /acos-loan-doc-generator.
  Produces IC-ready outputs with best available design from the design library.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch, Task(general-purpose)
argument-hint: "<loan-folder-path>"
---

# ACOS Underwriting Pipeline

## Purpose

One-command underwriting for new loan deals. Takes a raw loan folder (Dropbox path
with PDFs, tax returns, financials, site plans, etc.) and runs the full underwriting
analysis pipeline, culminating in batch document generation via `/acos-loan-doc-generator`.

```
Phase 1: Deal Setup          → Create deal structure, inventory documents
Phase 2: Document Triage     → Read & classify every document, extract key data
Phase 3: Underwriting Math   → Calculate LTV, DSCR, IRR, debt yield, equity cushion
Phase 4: Risk & Sponsor      → Sponsor evaluation, risk assessment, market context
Phase 5: Synthesis           → Compile underwriting package (YAML + summary)
Phase 6: Document Generation → Batch-invoke /acos-loan-doc-generator for IC docs
```

---

## Phase 1: Deal Setup & Inventory

### Step 1.0: Parse Arguments

Parse `$ARGUMENTS` for the loan folder path. If not provided, prompt:
> "Provide the path to the loan folder (e.g., /Users/zee/Desktop/Deal Name/)"

Store as `LOAN_FOLDER`.

Verify the path exists:
```bash
ls "$LOAN_FOLDER"
```

If it doesn't exist, error and stop.

### Step 1.1: Extract Deal Name

Derive deal name from the folder name. Present to user for confirmation:

```
╔══════════════════════════════════════════════════════════════╗
║        ACOS Underwriting Pipeline                            ║
╚══════════════════════════════════════════════════════════════╝

  Loan Folder: {LOAN_FOLDER}
  Derived Name: {deal_name}

  Is this correct? [Y/n, or type a different name]:
```

Store as `DEAL_NAME`.

### Step 1.2: Create Workspace

Create the underwriting workspace **inside the loan folder itself**:

```bash
mkdir -p "$LOAN_FOLDER/underwriting-zee/"
```

Store this path as `UW_DIR` — all subsequent output files go here.

The `zee` suffix identifies the analyst. This prevents collisions if multiple
people underwrite the same deal (e.g., `underwriting-brad/`, `underwriting-ty/`).

### Step 1.3: Inventory Documents

Recursively list all files in `LOAN_FOLDER`:

```bash
find "$LOAN_FOLDER" -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.doc" -o -name "*.xlsx" -o -name "*.xls" -o -name "*.csv" -o -name "*.txt" -o -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) -not -name ".*" -not -path "*/underwriting-*/*"
```

**IMPORTANT:** The `-not -path "*/underwriting-*/*"` excludes any existing underwriting
output folders (yours or other analysts') from the inventory.

Display summary:
```
Document Inventory
==================
Total files: {count}
  PDF:  {n}
  DOCX: {n}
  XLSX: {n}
  Other: {n}
```

Write the inventory to `{LOAN_FOLDER}/underwriting-zee/inventory.yaml`.

### Step 1.4: Create DEAL_INFO Skeleton

Write `{LOAN_FOLDER}/underwriting-zee/DEAL_INFO.yaml` with the standard template:

```yaml
deal_info:
  name: "{DEAL_NAME}"
  created_date: "{today YYYY-MM-DD}"
  status: "underwriting"
  loan_folder: "{LOAN_FOLDER}"

  property:
    address: ""
    city: ""
    state: ""
    property_type: ""
    subtype: ""

  loan_request:
    amount: 0
    loan_type: ""
    purpose: ""
    term_months: 0
    requested_rate: ""

  values:
    purchase_price: 0
    as_is_value: 0
    as_stabilized_value: 0
    as_completed_value: 0
    cost_to_complete: 0

  sponsor:
    name: ""
    entity_name: ""
    experience_years: 0
    net_worth: 0
    liquidity: 0

  source:
    referral_source: ""
    date_received: "{today}"

  timeline:
    target_close: ""
    maturity_date: ""
```

---

## Phase 2: Document Triage & Data Extraction

### Step 2.0: Launch Parallel Triage Agents

Spawn 3-5 parallel agents (based on document count) to read and classify every
document. Each agent gets a partition of the file inventory.

**CRITICAL: ALL triage agents MUST be spawned in a SINGLE message.**

Each agent receives this prompt:

```
You are a Loan Document Triage Agent for OKOA Capital's underwriting pipeline.

YOUR TASK: Read each assigned document and extract:
1. DOCUMENT TYPE — What kind of document is this? (tax return, appraisal, lease,
   entity doc, financial statement, proforma, site plan, title report, insurance,
   construction budget, loan application, personal financial statement, etc.)
2. KEY DATA POINTS — Extract ALL numbers, dates, names, addresses, and financial
   figures you find. Be exhaustive. Include:
   - Dollar amounts (with context: "loan amount", "appraised value", "annual rent")
   - Dates (maturity, execution, effective dates)
   - Names (borrower, guarantor, entity names, property name/address)
   - Rates (interest rate, cap rate, tax rate)
   - Percentages (LTV, occupancy, vacancy)
   - Areas (square feet, acreage, lot size)
3. RELEVANCE — Rate each document: CRITICAL / IMPORTANT / SUPPORTING / IRRELEVANT

YOUR FILE ASSIGNMENTS:
{list of file paths}

OUTPUT FORMAT (YAML):
Write to: {LOAN_FOLDER}/underwriting-zee/triage/agent-{NN}.yaml

documents:
  - file: "{path}"
    filename: "{name}"
    document_type: "{type}"
    relevance: "CRITICAL"
    extracted_data:
      - field: "loan_amount"
        value: "5000000"
        context: "Page 1, Section 2.1"
      - field: "borrower_name"
        value: "Hazel St LLC"
        context: "Page 1, header"
    summary: "2-3 sentence description"
```

### Step 2.1: Aggregate Triage Results

After ALL agents complete, read all `triage/agent-*.yaml` files.

Merge into `{LOAN_FOLDER}/underwriting-zee/triage-master.yaml`:
- Deduplicate documents
- Resolve any conflicts
- Sort by relevance (CRITICAL first)

### Step 2.2: Populate DEAL_INFO

Using the extracted data from triage, auto-populate `DEAL_INFO.yaml`:
- Property address, city, state from documents
- Loan amount from proforma, application, or term sheet
- Sponsor name from entity docs, PFS, or tax returns
- Entity name from formation docs
- Property type from appraisal, site plans, or proforma
- Values from appraisal or BPO

Display the populated DEAL_INFO to the user for confirmation/correction:

```
Deal Information (auto-populated from documents)
=================================================
Property: {address}, {city}, {state}
Loan Type: {type}
Loan Amount: ${amount}
Sponsor: {name} / {entity}
Property Type: {type}
Values:
  As-Is: ${as_is}
  As-Completed: ${as_completed}
  Purchase Price: ${purchase}

[Review above. Type corrections or press Enter to confirm]:
```

Apply any user corrections to DEAL_INFO.yaml.

---

## Phase 3: Underwriting Math

### Step 3.0: Calculate Core Metrics

Using data from Phase 2, calculate and write to `{LOAN_FOLDER}/underwriting-zee/underwriting-metrics.yaml`:

```yaml
underwriting_metrics:
  # Leverage Ratios
  ltv_as_is: 0            # Loan Amount / As-Is Value
  ltv_as_completed: 0     # Loan Amount / As-Completed Value
  ltv_as_stabilized: 0    # Loan Amount / As-Stabilized Value
  ltac: 0                 # Loan-to-After-Completion (Loan / (As-Is + Cost-to-Complete))

  # Coverage Ratios (if income-producing)
  dscr: 0                 # NOI / Annual Debt Service
  debt_yield: 0           # NOI / Loan Amount
  noi: 0                  # Revenue - Operating Expenses

  # Return Metrics
  gross_yield: 0          # Annual Interest / Loan Amount
  origination_fee_pct: 0
  exit_fee_pct: 0
  estimated_irr: 0        # Approximated from rate + fees + term
  estimated_moic: 0       # Total Proceeds / Investment

  # Safety Metrics
  equity_cushion_pct: 0   # (Value - Loan) / Value
  interest_reserve_months: 0
  cost_to_complete: 0

  # Sources and Uses
  sources:
    loan_amount: 0
    borrower_equity: 0
    other: 0
    total: 0
  uses:
    acquisition: 0
    construction: 0
    soft_costs: 0
    reserves: 0
    closing_costs: 0
    total: 0

  # Stress Tests
  stress_tests:
    value_decline_10pct:
      ltv: 0
      equity_cushion: 0
    value_decline_20pct:
      ltv: 0
      equity_cushion: 0
    value_decline_30pct:
      ltv: 0
      equity_cushion: 0
    rate_increase_200bps:
      dscr: 0
      annual_debt_service: 0

  # Red Flags
  red_flags: []
  warnings: []
```

### Step 3.1: Display Metrics Dashboard

```
Underwriting Metrics Dashboard
================================
LTV (As-Is):       {x}%     {✓ if <70% | ⚠ if 70-80% | ✗ if >80%}
LTV (Completed):   {x}%     {✓/⚠/✗}
DSCR:              {x}x     {✓ if >1.25 | ⚠ if 1.0-1.25 | ✗ if <1.0}
Debt Yield:        {x}%     {✓ if >10% | ⚠ if 8-10% | ✗ if <8%}
Equity Cushion:    {x}%     {✓ if >25% | ⚠ if 15-25% | ✗ if <15%}
Est. IRR:          {x}%
Est. MOIC:         {x}x

Stress Test (20% value decline):
  LTV:             {x}%
  Equity Cushion:  {x}%

Red Flags: {count}
Warnings:  {count}
```

---

## Phase 4: Risk & Sponsor Assessment

### Step 4.0: Sponsor Evaluation

From the triage data, extract and evaluate:

```yaml
sponsor_evaluation:
  name: ""
  experience:
    years: 0
    similar_projects: 0
    description: ""
  financial_strength:
    net_worth: 0
    liquidity: 0
    annual_income: 0
    debt_obligations: 0
  credit_indicators:
    tax_returns_reviewed: false
    pfs_reviewed: false
    background_check: false
  assessment: ""        # strong, adequate, weak, insufficient
  guaranty_strength: "" # strong, moderate, limited
```

### Step 4.1: Risk Assessment

```yaml
risk_assessment:
  market_risk: ""       # low, moderate, elevated, high
  execution_risk: ""    # low, moderate, elevated, high
  sponsor_risk: ""      # low, moderate, elevated, high
  exit_risk: ""         # low, moderate, elevated, high
  legal_risk: ""        # low, moderate, elevated, high
  collateral_risk: ""   # low, moderate, elevated, high
  overall_risk: ""      # low, moderate, elevated, high

  risk_mitigants:
    - risk: ""
      mitigant: ""

  deal_strengths:
    - ""

  deal_weaknesses:
    - ""

  recommendation: ""    # proceed, proceed_with_conditions, decline, need_more_info
  conditions: []        # if proceed_with_conditions
```

### Step 4.2: Market Context (Optional — Web Research)

If the user has internet access, run a quick market research query:

```
Searching for: "{property_type} market conditions in {city}, {state}"
```

Use WebSearch to gather:
- Local market cap rates
- Comparable rents / lease rates
- Vacancy rates
- Recent comparable sales
- Construction cost indices (if construction deal)

Append findings to `{LOAN_FOLDER}/underwriting-zee/market-context.yaml`.

If no internet access, skip and note "Market context: NOT AVAILABLE (offline)".

---

## Phase 5: Underwriting Synthesis

### Step 5.0: Compile Underwriting Package

Write the master underwriting file to `{LOAN_FOLDER}/underwriting-zee/UNDERWRITING_PACKAGE.yaml`:

```yaml
underwriting_package:
  deal_name: "{DEAL_NAME}"
  date: "{today}"
  analyst: "ACOS Underwriting Pipeline"

  deal_info: !include DEAL_INFO.yaml
  metrics: !include underwriting-metrics.yaml
  sponsor: !include sponsor-evaluation (from Phase 4)
  risk: !include risk-assessment (from Phase 4)
  market: !include market-context.yaml (if available)

  documents_reviewed:
    critical: [{list}]
    important: [{list}]
    supporting: [{list}]

  executive_summary: |
    {3-5 sentence summary of the deal: what it is, key metrics,
     recommendation, and top risk/mitigant}

  recommendation: "{proceed / proceed_with_conditions / decline / need_more_info}"
  conditions: [{list if applicable}]
```

### Step 5.1: Write Human-Readable Summary

Write `{LOAN_FOLDER}/underwriting-zee/UNDERWRITING_SUMMARY.md`:

```markdown
# Underwriting Summary: {DEAL_NAME}

**Date:** {today}
**Recommendation:** {PROCEED / PROCEED WITH CONDITIONS / DECLINE / NEED MORE INFO}

## Deal Overview
| Metric | Value |
|--------|-------|
| Property | {address} |
| Loan Amount | ${amount} |
| Loan Type | {type} |
| LTV | {x}% |
| DSCR | {x}x |
| Term | {months} months |
| Sponsor | {name} |

## Executive Summary
{summary}

## Key Metrics
{metrics dashboard}

## Risk Assessment
{risk table}

## Sponsor Assessment
{sponsor summary}

## Conditions (if applicable)
{conditions list}

## Documents Reviewed
{document inventory with relevance ratings}
```

### Step 5.2: Present to User

Display the summary to the user and ask:

```
Underwriting analysis complete.

  Recommendation: {recommendation}
  Report: {LOAN_FOLDER}/underwriting-zee/UNDERWRITING_SUMMARY.md

  Proceed to document generation? [Y/n]:
```

If user declines, stop here. If user confirms, proceed to Phase 6.

---

## Phase 6: Batch Document Generation

### Step 6.0: Determine Documents to Generate

For underwriting-level output, the standard batch is:

| # | Document | Design Style |
|---|----------|-------------|
| 1 | Internal Credit Memo | wall-street |
| 2 | Term Sheet | modern-institutional |
| 3 | Deal Memo | wall-street |
| 4 | Executive Summary | modern-institutional |

Present to user:
```
Document Generation Plan
=========================
The following documents will be generated using /acos-loan-doc-generator:

  [1] ✓  Internal Credit Memo      (wall-street design)
  [2] ✓  Term Sheet                (modern-institutional design)
  [3] ✓  Deal Memo                 (wall-street design)
  [4] ✓  Executive Summary         (modern-institutional design)

  Loan Folder: {LOAN_FOLDER}
  Underwriting Data: {LOAN_FOLDER}/underwriting-zee/

  Modify selection? [Enter to confirm, or type numbers to toggle, e.g., "-2 +5"]:
```

If user adds/removes docs, update the list. Available additions:
- Scoping Letter
- External Credit Memo

### Step 6.1: Invoke /acos-loan-doc-generator in Batch Mode

**CRITICAL:** Do NOT re-implement the loan-doc-generator. Invoke it via the Skill tool.

The generator needs to be invoked with `batch` mode. Since the Skill tool invokes
it as a slash command, prepare the context by writing the batch manifest:

Write `{LOAN_FOLDER}/underwriting-zee/generation-manifest.yaml`:

```yaml
generation_manifest:
  mode: "batch"
  loan_folder: "{LOAN_FOLDER}"
  underwriting_data: "{LOAN_FOLDER}/underwriting-zee/"
  documents:
    - document_id: "credit-underwriting/internal-credit-memo"
      design_style: "wall-street"
    - document_id: "credit-underwriting/term-sheet"
      design_style: "modern-institutional"
    - document_id: "credit-underwriting/deal-memo"
      design_style: "wall-street"
    - document_id: "credit-underwriting/executive-summary"
      design_style: "modern-institutional"
```

Then tell the user:

```
Generation manifest created. Now invoking /acos-loan-doc-generator.

The generator will run in batch mode and produce all {N} documents.
Each document will use data from:
  1. Raw loan folder:     {LOAN_FOLDER}
  2. Underwriting package: {LOAN_FOLDER}/underwriting-zee/UNDERWRITING_PACKAGE.yaml

The generator's interview wizard will appear next. For each question:
  - Mode: Select [3] Batch
  - Documents: Pre-selected from manifest (confirm each)
  - Design: Use design library (wall-street or modern-institutional as indicated)
  - Loan folder: {LOAN_FOLDER}
  - Critical figures: Pull from UNDERWRITING_PACKAGE.yaml
  - Instructions: "Use underwriting data from {LOAN_FOLDER}/underwriting-zee/ for all figures and analysis."
```

Then invoke the Skill:

```
Skill(skill: "acos-loan-doc-generator")
```

### Step 6.2: Post-Generation Summary

After the loan-doc-generator completes, display:

```
╔══════════════════════════════════════════════════════════════╗
║        Underwriting Pipeline — Complete                      ║
╚══════════════════════════════════════════════════════════════╝

Deal: {DEAL_NAME}
Recommendation: {recommendation}

Underwriting Outputs:
  {LOAN_FOLDER}/underwriting-zee/DEAL_INFO.yaml
  {LOAN_FOLDER}/underwriting-zee/UNDERWRITING_PACKAGE.yaml
  {LOAN_FOLDER}/underwriting-zee/UNDERWRITING_SUMMARY.md
  {LOAN_FOLDER}/underwriting-zee/underwriting-metrics.yaml
  {LOAN_FOLDER}/underwriting-zee/triage-master.yaml

Generated Documents:
  {list of generated document paths from loan-doc-generator output}

Next Steps:
  1. Review UNDERWRITING_SUMMARY.md for accuracy
  2. Review generated documents for completeness
  3. If proceeding: present to IC / principals for approval
  4. After approval: hand off to counsel for legal documentation
```

---

## Configuration Reference

| Setting | Default | Description |
|---------|---------|-------------|
| Max triage agents | 5 | Upper bound on parallel document readers |
| Min triage agents | 3 | Lower bound on parallel document readers |
| Default design (credit memo) | wall-street | Design library style for credit memos |
| Default design (term sheet) | modern-institutional | Design library style for term sheets |
| Default design (deal memo) | wall-street | Design library style for deal memos |
| Default design (exec summary) | modern-institutional | Design library style for summaries |
| Market research | optional | Requires internet access |
| Stress test increments | 10%, 20%, 30% | Property value decline scenarios |

---

## Integration Points

- **Input:** Raw loan folder (Dropbox or local path)
- **Analysis:** Self-contained underwriting engine (Phases 1-5)
- **Generation:** Delegates to `/acos-loan-doc-generator` (Phase 6)
- **Design Library:** Uses existing designs at `.acos/loan-doc-generator/design-library/`
- **okoa-ops compatibility:** Output YAML format matches okoa-ops `DEAL_INFO.yaml` schema

---

*ACOS Underwriting Pipeline — From raw documents to IC-ready package in one command.*
