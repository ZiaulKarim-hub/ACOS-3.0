---
name: acos-financial-statement
description: |
  Triple-redundancy adversarial financial statement preparation system.
  Three independent sandbox orchestrators each prepare complete GAAP financial
  statements from loan folder data. A Primary Accountant compares outputs,
  identifies deficiencies (never provides numbers), and iterates via Wigum loop
  until substance convergence (actuals) or optimal synthesis (projections).

  Supports: Income Statement, Balance Sheet, Statement of Owner's Equity,
  Statement of Cash Flows. Modes: Actual (historical) and Projection (pro forma
  with multi-period support). Property-type-aware with CRE-specific COA.

  Output: institutional-grade XLSX with live formulas, FAST Standard formatting,
  IB color conventions, cross-statement linkages, and automated validation checks.
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task(fin-stmt-accountant)
---

# ACOS Financial Statement Preparation

## Architecture

```
                         ┌───────────────────────────┐
                         │      SKILL.MD (Phase 0)   │
                         │   Interview Wizard + Setup │
                         └─────────┬─────────────────┘
                                   │ Task(fin-stmt-accountant)
                                   ▼
                    ┌──────────────────────────────┐
                    │     PRIMARY ACCOUNTANT        │
                    │  (Never gives numbers)        │
                    │  Owns Wigum loop + synthesis  │
                    │  Spawns reviewers as needed   │
                    └───┬─────────┬─────────┬──────┘
                        │         │         │
          Task(sandbox) │         │         │ Task(sandbox)
                        ▼         ▼         ▼
                 ┌──────────┐ ┌──────────┐ ┌──────────┐
                 │SANDBOX A │ │SANDBOX B │ │SANDBOX C │
                 │          │ │          │ │          │
                 │Extractors│ │Extractors│ │Extractors│
                 │Calculator│ │Calculator│ │Calculator│
                 │Compilers │ │Compilers │ │Compilers │
                 │Reviewers │ │Reviewers │ │Reviewers │
                 └────┬─────┘ └────┬─────┘ └────┬─────┘
                      │            │            │
                      ▼            ▼            ▼
                   FS Set A    FS Set B     FS Set C
                      │            │            │
                      └────────┬───┘────────────┘
                               ▼
                    ┌──────────────────────┐
                    │  SUBSTANCE MATCH?    │
                    │  (Actual: converge)  │
                    │  (Proj: synthesize)  │
                    └──────────┬───────────┘
                         NO → Wigum Loop
                        YES → Generate XLSX
```

### Key Principles

1. **Independence Wall** — Sandboxes never see each other's work. The Primary
   Accountant never provides numbers, calculations, or correct values to any
   sandbox. Each sandbox must independently arrive at the truth.

2. **Canonical COA** — All sandboxes work against the same IREM-based Chart of
   Accounts (`templates/chart-of-accounts.yaml`). This enables mechanical
   substance comparison by account code rather than fuzzy text matching.

3. **Dual Mode** — Actual mode requires convergence (same numbers within
   materiality). Projection mode expects divergence and synthesizes the best
   features from all three sandboxes into one final projection.

4. **Validation Engine** — Each sandbox runs 20+ automated checks before
   submission (`templates/validation-checks.yaml`). The Primary Accountant
   also validates the reconciled output. All checks are embedded as live
   formulas in the final XLSX.

5. **XLSX Output** — Professional formatting following FAST Standard column
   layout and investment banking color conventions. Live formulas (not static
   values) enable users to modify assumptions and see recalculated results.

---

## Phase 0: Interview Wizard

The interview runs in the primary conversation context (no agent spawning).
Ask questions sequentially by presenting them to the user and waiting for their response.

### Step 0.1: Mode Selection

Ask the user:

```
═══════════════════════════════════════════════════════════
  ACOS Financial Statement Preparation
═══════════════════════════════════════════════════════════

What would you like to prepare?

  [A]  Actual Financial Statement (historical, from real data)
  [P]  Financial Statement Projection (pro forma, forward-looking)
```

Record selection as `mode: "actual"` or `mode: "projection"`.

### Step 0.2: Statement Selection

**If mode = actual:**
```
Which financial statement(s) would you like to prepare?

  [1]  Income Statement (P&L)
  [2]  Balance Sheet
  [3]  Statement of Owner's Equity
  [4]  Statement of Cash Flows
  [5]  All of the above

Select one or more (e.g., "1,2" or "5"):
```

**If mode = projection:**
```
Which financial statement projection(s) would you like to prepare?

  [1]  Income Statement Projection
  [2]  Balance Sheet Projection
  [3]  Statement of Owner's Equity Projection
  [4]  Statement of Cash Flows Projection

Select one or more (e.g., "1,2"):
```

Note: If the user selects Cash Flow Statement, the Income Statement and Balance
Sheet are automatically included as dependencies (cash flow is derived from them
via the indirect method). Inform the user of this dependency.

Record selections in `statements_requested`.

### Step 0.3: Property Type

```
What type of property is this?

  [1]  Multifamily
  [2]  Office
  [3]  Retail
  [4]  Industrial / Warehouse
  [5]  Hospitality / Hotel
  [6]  Mixed-Use
  [7]  Other (please specify)
```

Property type determines which COA accounts are active. For example:
- Multifamily includes pet fees, laundry income, storage income
- Retail includes percentage rent, CAM recoveries
- Hospitality includes departmental revenue/expense structure
- Industrial has low operating expense ratios

Record as `property_type`.

### Step 0.4: Time Period Configuration

**If mode = actual:**
```
For which time period should the financial statements be prepared?

  From: [date, e.g., January 1, 2024]
  To:   [date, e.g., December 31, 2024]
```

Accept flexible date formats. Convert to ISO 8601 (YYYY-MM-DD) internally.
Record in `time_period.from` and `time_period.to`.

**If mode = projection:**

Step 0.4a — Period Shape:
```
What is the reporting period for each projection?

  From: [month and day, e.g., October 1]
  To:   [month and day, e.g., September 30]

This defines one "period." It can be any duration:
  - 12 months (annual): Jan 1 – Dec 31, or Oct 1 – Sep 30, etc.
  - 6 months (semi-annual)
  - 3 months (quarterly)
```

Step 0.4b — Starting Year:
```
Starting from which year?
  [e.g., 2024]
```

Step 0.4c — Number of Periods:
```
How many periods do you want the projection for?
  [e.g., 5]
```

Validate that `num_periods >= 1`. If the user enters 0 or a negative number, re-prompt
with: "The number of periods must be at least 1. Please enter a valid number."

After collecting all three inputs, generate the period list and confirm:
```
Projection will cover these periods:

  Period 1:  Oct 2024 – Sep 2025
  Period 2:  Oct 2025 – Sep 2026
  Period 3:  Oct 2026 – Sep 2027
  Period 4:  Oct 2027 – Sep 2028
  Period 5:  Oct 2028 – Sep 2029

Is this correct? [Y/n]
```

Record in `projection.period_from_month`, `projection.period_from_day`,
`projection.period_to_month`, `projection.period_to_day`,
`projection.start_year`, `projection.num_periods`, and auto-generate
`projection.periods` array with `{from, to, label}` for each period.

### Step 0.5: Loan Folder Path

```
Please provide the path to the loan folder:
  [absolute or relative path]
```

**Path validation (MANDATORY):**
1. Resolve the path to absolute using realpath
2. Verify it exists and is a directory (not a file)
3. **REJECT** paths containing `..` traversal sequences
4. **REJECT** paths pointing to system directories (`/etc/`, `/usr/`, `/var/`, `~/.ssh/`)
5. **REJECT** symlinks whose target resolves outside the user's home directory
6. Verify the folder contains at least 1 file

If validation fails, explain why and re-prompt. If the folder contains 0 files,
inform the user: "The specified folder is empty. Please provide a path to a
folder containing loan documents." and re-prompt.

```
Found N files in the loan folder:
  - document1.pdf
  - document2.xlsx
  - ...

Is this the correct folder? [Y/n]
```

Record as `loan_folder_path`.

### Step 0.5.5: Prior Period Sample (Optional)

```
Do you have a sample financial statement from a prior period?

This is NOT used as a data source — no numbers will be carried forward.
It serves as a structural reference that shows the agents:
  - What line items typically appear for this business
  - How items are categorized and labeled
  - What accounts are relevant vs. irrelevant
  - What the relative proportions look like

  [Y]  Yes — I have a sample I can provide
  [N]  No — proceed without a sample
```

If the user provides a sample:
1. Accept the file path (PDF, XLSX, DOCX, or image)
2. Copy or reference the file in the session directory, preserving the real
   file extension (the literal `.*` does NOT expand — derive the extension):
   ```bash
   ext="${sample_path##*.}"
   cp "{sample_path}" ".acos/financial-statement/sessions/{session_id}/prior-sample.${ext}"
   ```
3. Record the EXACT copied path (with the derived extension) in the manifest:
   ```yaml
   prior_sample:
     provided: true
     path: ".acos/financial-statement/sessions/{session_id}/prior-sample.${ext}"  # actual extension (pdf/xlsx/docx/png/...)
     usage: "structural_reference_only"  # NEVER "data_source"
   ```

**How sandboxes use the sample:**
- As a "what to look for" guide — if the sample shows a line item for "Snow Removal"
  but the sandbox finds no snow removal expense in the loan folder, that's a signal
  to search harder or confirm the item is genuinely absent for the current period
- As a structural template for how to organize the output (grouping, ordering, subtotals)
- As a proportionality benchmark — if property taxes were ~25% of operating expenses
  in the sample, a current period where they're 5% should trigger investigation
- NEVER as a source of actual numbers, beginning balances, or default values

### Step 0.6: Configuration (Optional)

```
Would you like to customize any settings? (Press Enter to skip)

  [M]  Materiality threshold (default: 1% of total assets / 5% of revenue)
  [I]  Max iterations (default: 5 for actual, 4 for projection)
  [S]  Skip — use defaults
```

If user selects M, ask for custom percentages.
If user selects I, ask for custom max iterations.

### Step 0.7: Confirmation

Display all selections:
```
═══════════════════════════════════════════════════════════
  Session Summary
═══════════════════════════════════════════════════════════

  Mode:          Actual Financial Statement
  Statements:    Income Statement, Balance Sheet
  Property Type: Multifamily
  Time Period:   January 1, 2024 – December 31, 2024
  Loan Folder:   /path/to/folder (N files)
  Materiality:   1% total assets / 5% total revenue
  Max Iterations: 5
  Sandboxes:     3 (A, B, C)

  [C]  Confirm and begin
  [E]  Edit a selection
```

### Step 0.8: Session Setup

After confirmation, execute these setup steps:

**0. Verify .gitignore protection (MANDATORY):**
Check that `.acos/financial-statement/sessions/` is in `.gitignore`. Session directories
contain extracted financial data (dollar amounts, loan balances, property valuations) from
client loan folders. If not gitignored, add it immediately:
```
.acos/financial-statement/sessions/
```
This prevents accidental commit of confidential client financial data via `git add .`.

**1. Generate session ID:**
```
session_id = "FS-{YYYYMMDD}-{HHMMSS}"
```

**2. Create session directories:**
```bash
mkdir -p .acos/financial-statement/sessions/{session_id}/sandbox-A
mkdir -p .acos/financial-statement/sessions/{session_id}/sandbox-B
mkdir -p .acos/financial-statement/sessions/{session_id}/sandbox-C
mkdir -p .acos/financial-statement/sessions/{session_id}/reconciliation
mkdir -p .acos/financial-statement/sessions/{session_id}/output
```

**3. Write session manifest:**
Read the template from `templates/session-manifest.yaml`, fill in all user
selections, and write to:
`.acos/financial-statement/sessions/{session_id}/session-manifest.yaml`

**4. Resolve agent model:**
```bash
ACCOUNTANT_MODEL=$(bash .claude/scripts/resolve-agent-model.sh fin-stmt-accountant 2>/dev/null || echo "opus")
```
Pass `ACCOUNTANT_MODEL` into the Task(fin-stmt-accountant) dispatch in Phase 1+2
(via the spawn's `model` override) so model-profile overrides actually take
effect. If `ACCOUNTANT_MODEL` is a bare Claude model name (`opus`/`sonnet`/`haiku`),
use it as the Task model override; if it resolves to an external `provider:model`
spec, ignore it and let the agent's own `model: opus` default stand (the
architect/developer-style safety gate — the accountant requires Claude tool access).

**5. Copy COA template:**
Copy the chart-of-accounts.yaml to the session directory so all sandboxes
reference the same version:
```bash
cp .claude/skills/acos-financial-statement/templates/chart-of-accounts.yaml \
   .acos/financial-statement/sessions/{session_id}/chart-of-accounts.yaml
```

---

## Phase 1+2: Dispatch Primary Accountant

After session setup, spawn the Primary Accountant agent. The accountant handles
the entire process from here: sandbox spawning, comparison, Wigum loop, and
finalization.

**Dispatch:**

Spawn `Task(fin-stmt-accountant)` with the `model` override set to the
`ACCOUNTANT_MODEL` resolved in Step 0.8 #4 (when it is a bare Claude model name;
otherwise omit the override and let the agent's `model: opus` default stand).

```
Spawn Task(fin-stmt-accountant) [model: {ACCOUNTANT_MODEL}] with prompt:

"You are the Primary Accountant for financial statement session {session_id}.

Read your instructions from:
.claude/skills/acos-financial-statement/phases/phase2-reconcile.md

Session manifest path:
.acos/financial-statement/sessions/{session_id}/session-manifest.yaml

Begin by reading the manifest and spawning the three sandbox orchestrators."
```

Use `run_in_background: false` — wait for the accountant to complete before
proceeding.

---

## Phase 3: Present Results

After the accountant returns:

**1. Read the final output path from the session manifest:**
```yaml
final_output_path: ".acos/financial-statement/sessions/{session_id}/output/financial-statements.xlsx"
```

**2. Read the convergence history to summarize the process:**
```yaml
convergence_history:
  - iteration: 1 ...
  - iteration: 2 ...
```

**3. Present results to the user:**
```
═══════════════════════════════════════════════════════════
  Financial Statement Preparation — Complete
═══════════════════════════════════════════════════════════

  Mode:           Actual Financial Statement
  Statements:     Income Statement, Balance Sheet
  Time Period:    Jan 1, 2024 – Dec 31, 2024
  Iterations:     3 (converged on iteration 3)

  Output:
    XLSX: file://{absolute_path}/financial-statements.xlsx

  Validation:
    Balance Sheet Equation:      PASS
    Retained Earnings Continuity: PASS
    Cash Reconciliation:          PASS
    All Footing Checks:           PASS (12/12)
    GAAP Compliance:              PASS (7/7)

  Supplemental Metrics:
    NOI:          $X,XXX,XXX
    FFO:          $X,XXX,XXX
    DSCR:         X.XXx
    Debt Yield:   XX.X%
```

If the session failed (max iterations without convergence):
```
  Status: INCOMPLETE — sandboxes did not converge after {max} iterations

  Remaining Differences:
    - Account 4000 (Base Rental Income): Sandbox A=$X vs B=$Y vs C=$Z
    - Account 5300 (Property Taxes): Sandbox A=$X vs B=$Y vs C=$Z

  Partial output saved to: file://{path}/financial-statements-draft.xlsx

  Options:
    [R] Resume with more iterations
    [M] Accept best sandbox's output as-is
```

---

## XLSX Output Specification

The final XLSX workbook must follow these standards:

### Workbook Structure (tab order)

| Tab | Name | Color | Content |
|-----|------|-------|---------|
| 1 | Cover | Blue | Model metadata, TOC with hyperlinks, version |
| 2 | Assumptions | Yellow | All inputs in blue font on light yellow background |
| 3 | Income Statement | White | Full P&L with NOI subtotal |
| 4 | Balance Sheet | White | Assets, Liabilities, Equity |
| 5 | Owner's Equity | White | Changes in equity (if requested) |
| 6 | Cash Flow | White | Indirect method (if requested) |
| 7 | Supplemental | Green | NOI, FFO, AFFO, DSCR, Debt Yield, LTV |
| 8 | Checks | Red | All validation checks with PASS/FAIL |
| 9 | Notes | White | Assumption documentation, source citations |
| 10 | Attestation | White | Data attestation report — sources used, gaps found, resolutions, opinion tier |

Only include tabs for requested statements. Checks and Cover are always included.

### Formatting Standards (FAST + IB Conventions)

**Font:** Arial 10pt throughout. Headers 11pt bold.

**Color Conventions:**
- Blue font (`#0000FF`): Hard-coded inputs, assumptions, user-provided data
- Black font (`#000000`): Formulas and same-sheet references
- Green font (`#008000`): Cross-sheet references
- Navy header bg (`#002060`): Section headers with white bold text
- Light yellow bg (`#FFFFCC`): Input cells

**Border Conventions:**
- Thin bottom border: Separates line items from subtotals
- Medium bottom border: Subtotal rows
- Double bottom border: Grand totals / final totals
- No vertical borders between data columns

**Number Formats:**
- Currency: `#,##0` (no decimals) with parentheses for negatives: `#,##0_);(#,##0)`
- Percentages: `0.0%`
- Ratios: `0.00x`
- Dates: `mmm-yy` for period headers
- Zero values: Dash (`"-"`) instead of 0

**Column Layout (FAST Standard):**
- Columns A-B: Line item labels (30-45 chars wide)
- Column C: Account code (8 chars)
- Column D: Units label ($, %, x)
- Column E: Totals column (SUM of period columns)
- Columns F+: Time series data (12-15 chars each, one per period)

**Formulas:**
- ALL calculations must be live Excel formulas, not static values
- Cross-statement links as actual cell references (e.g., `='Income Statement'!F45`)
- Named ranges for key cross-statement values (Net_Income, Ending_Cash, etc.)
- Subtotals use `=SUM(range)`, grand totals reference subtotals

**Print Setup:**
- Landscape orientation
- Narrow margins (0.25" sides, 0.5" top/bottom)
- Repeat rows 1-3 on every page (header + column labels)
- Repeat column A on every page (line item labels)
- Left header: Entity name | Center header: Statement title | Right header: Date
- Center footer: Page &P of &N

**Checks Sheet:**
- One row per validation check
- Columns: Check ID, Check Name, Formula, Result (PASS/FAIL), per-period results
- Conditional formatting: green fill = PASS, red fill = FAIL
- Master cell at top: `ALL CHECKS PASS` or `N CHECKS FAILING`

### Projection-Specific Additions

For projection mode, the XLSX also includes:

| Tab | Name | Color | Content |
|-----|------|-------|---------|
| 2a | Assumptions | Yellow | All projection assumptions with sources and reasonableness scores |
| 10 | Sensitivity | White | Two-way tables (exit cap vs rent growth, vacancy vs expenses) |
| 11 | Scenarios | White | Base / Upside / Downside scenarios side by side |

**Assumption Documentation (Notes tab):**
For each projected value, include:
- Value used
- Source (document, page/cell, or benchmark)
- Benchmark comparison (market data, historical, industry average)
- Reasonableness score (green/yellow/red)
- Calculation method (if derived)

---

## Data Fallback Hierarchy

When data for a line item cannot be found in the loan folder, sandboxes follow
this tiered resolution strategy. Each tier is progressively less certain — the
system never silently produces a statement with missing critical data.

### Tier 1: EXTRACT (highest confidence)
Find the value directly in the loan folder documents.
- Confidence: 90-100%
- Tag: `source: extracted`
- Action: Use with full provenance citation

### Tier 2: DERIVE (high confidence)
Calculate the value from other available data in the loan folder.
- Example: No explicit depreciation schedule, but closing statement shows
  purchase price of $2M for building → derive depreciation at $2M / 39 years
- Example: No beginning cash balance, but bank statement ending balance for
  the month before the reporting period exists → use that
- Confidence: 70-89%
- Tag: `source: derived, method: "{calculation description}"`
- Action: Use with derivation methodology documented

### Tier 3: STRUCTURAL INFERENCE (medium confidence)
If a prior period sample was provided, use it as a guide for what SHOULD exist.
- The sample tells the sandbox "this business typically has snow removal expense"
- The sandbox searches harder for that item in the loan folder
- If still not found after targeted search, the item may be legitimately absent
  for the current period (e.g., new property, different season)
- Confidence: 50-69%
- Tag: `source: structural_inference, sample_showed: true, current_period: not_found`
- Action: Document as "expected but not found" — do NOT fabricate a value

### Tier 4: ESCALATE (requires user input)
When a line item is **critical** to the statement and cannot be extracted, derived,
or inferred, PAUSE and generate a request for the user.

**Critical items** (always escalate if missing):
- Total revenue / rental income (for Income Statement)
- Total assets or total liabilities (for Balance Sheet)
- Loan balance and terms (for interest expense, DSCR)
- Property cost basis (for depreciation)
- Current period operating expenses (for NOI)

**Escalation format:**
```
DATA REQUEST — Cannot proceed without this information:

  Missing Item:    Building Cost Basis
  Needed For:      Depreciation calculation (accounts 6000-6030)
  Searched In:     closing-statement.pdf, appraisal.pdf, tax-return-2023.pdf
  Impact:          Cannot calculate depreciation; Balance Sheet and Income
                   Statement will be incomplete

  Please provide:
    [V]  The value (e.g., $2,400,000)
    [D]  A document I should look at
    [S]  Skip this item (will be excluded with disclosure note)
```

### Tier 5: EXCLUDE WITH DISCLOSURE (lowest confidence)
When the user explicitly says "skip it" OR the item is non-critical:
- Exclude the line item from the statement
- Add a disclosure note: "Note: [Line item] excluded due to insufficient data
  in the provided documents. Financial statements may not be complete."
- Confidence: 0%
- Tag: `source: excluded, reason: "insufficient_data"`

### Confidence Scoring

Every line item in the output carries a confidence tag:

| Score | Color | Meaning | Source |
|-------|-------|---------|--------|
| 90-100% | GREEN | Directly extracted, cross-validated | Tier 1 |
| 70-89% | GREEN | Derived from available data | Tier 2 |
| 50-69% | YELLOW | Structural inference or partial data | Tier 3 |
| 1-49% | RED | User-provided override or estimate | Tier 4 (user value) |
| 0% | GRAY | Excluded with disclosure | Tier 5 |

### Data Quality Assessment (Opinion Tier)

The final output includes a system-generated quality assessment modeled on
audit opinion standards:

| Assessment | Criteria |
|------------|----------|
| **Complete** | All line items populated from Tier 1-2 sources; all validation checks pass |
| **Qualified** | Specific line items estimated or excluded, with exceptions listed; core statements are reliable |
| **Limited** | Significant data gaps exist; statement should be used with caution; key metrics may be unreliable |
| **Insufficient** | Too many gaps to produce a reliable statement; system refuses to finalize |

The assessment is displayed to the user in Phase 3 output and included on the
Cover sheet of the XLSX workbook.

**Precedence rule:** Qualitative criteria override quantitative. If ANY qualitative
constraint fails, the opinion drops to the next tier regardless of average confidence:
- If average confidence is 90% but a critical item is Tier 3 → Qualified (not Complete)
- If average confidence is 75% but a critical item is excluded → Limited (not Qualified)

**Boundary rule:** Use inclusive lower bounds:
- Complete: average confidence >= 85%
- Qualified: average confidence >= 70% and < 85%
- Limited: average confidence >= 50% and < 70%
- Insufficient: average confidence < 50%

---

## Data Integrity Rules

These rules are injected into every sandbox agent's prompt. They are non-negotiable.

1. **NO FABRICATION** — Never invent, estimate, or infer financial values. If data
   is not found in the loan folder, use `NOT_FOUND` and document which files were
   searched. Never fill gaps with "reasonable estimates."

2. **EXACT NUMERICAL PRESERVATION** — Copy numbers exactly as they appear in source
   documents. No rounding, no unit conversion, no reformatting. $1,234,567.89 stays
   exactly as $1,234,567.89.

3. **PROVENANCE REQUIRED** — Every extracted value must cite: source document name,
   page number or cell reference, section/table where found, and verbatim context.

4. **PERIOD SENSITIVITY** — Revenue and expenses must be properly allocated to the
   reporting period. A 12-month expense for a period that only overlaps 4 months
   must be prorated to 4/12. Accruals must be calculated for the exact period.

5. **GAAP COMPLIANCE** — All statements follow US GAAP. Revenue recognition per
   ASC 606 (contracts) and ASC 842 (leases). Straight-line rent for all operating
   leases with escalations. Depreciation per GAAP useful lives.

6. **CANONICAL COA** — Use ONLY the account codes from the session's
   `chart-of-accounts.yaml`. Do not create ad-hoc categories. If a transaction
   doesn't map to an existing code, use the closest match and document why.

7. **CONFLICT PROTOCOL** — When two source documents show different values for the
   same item, flag the conflict. Record both values with their sources. Apply the
   resolution hierarchy: (1) audited financials, (2) tax returns, (3) bank statements,
   (4) operating statements, (5) rent rolls, (6) other documents.

8. **CROSS-STATEMENT CONSISTENCY** — Net Income on the Income Statement must equal
   Net Income on the Cash Flow Statement starting line and the Owner's Equity
   statement addition. Ending Cash on CFS must equal Cash on Balance Sheet.
   These are not suggestions — they are mathematical identities.

---

## Accounting Principles Reference

This section is provided to all sandbox agents as domain knowledge.

### Revenue Recognition (CRE Context)

**Base Rent (ASC 842):**
- Operating leases: straight-line income recognition over lease term
- Total scheduled rent payments / total months = monthly straight-line rent
- If SL rent > cash rent collected → Straight-Line Rent Receivable (asset 1400)
- If SL rent < cash rent collected → Deferred Rent Liability (liability 2400)

**Tenant Recoveries (CAM/Tax/Insurance):**
- Recognized as revenue when earned (typically monthly based on lease terms)
- Annual reconciliation may create true-up adjustments

**Percentage Rent:**
- Recognized only when tenant's sales exceed the natural breakpoint
- Natural breakpoint = base rent / percentage rate
- Contingent revenue — do not accrue until breakpoint is exceeded

**Vacancy & Credit Loss:**
- Contra-revenue deduction from Gross Potential Rent
- Based on actual vacancy (actuals) or projected vacancy rate (projections)

### Expense Recognition (Matching Principle)

- Expenses recognized when incurred, not when paid
- Property taxes: accrue monthly (annual bill / 12)
- Insurance: amortize prepaid premium over coverage period
- Management fees: % of EGI, recognized monthly
- Repairs: expense when incurred (unless capitalize if >$X and extends useful life)

### Depreciation (GAAP Straight-Line)

| Asset | Useful Life | Method |
|-------|-------------|--------|
| Building (commercial) | 39 years | Straight-line |
| Building (residential) | 27.5 years | Straight-line |
| Building improvements | 5-15 years | Straight-line |
| Tenant improvements | Shorter of useful life or remaining lease term | Straight-line |
| FF&E | 5-7 years | Straight-line |
| Land | N/A | Never depreciated |

### Cash Flow Statement (Indirect Method)

```
OPERATING ACTIVITIES:
  Net Income
  Adjustments for non-cash items:
    + Depreciation & Amortization
    + Impairment charges
    +/- Straight-line rent adjustments
    - Gains on sale / + Losses on sale
  Changes in working capital:
    +/- Change in Accounts Receivable
    +/- Change in Prepaid Expenses
    +/- Change in Accounts Payable
    +/- Change in Accrued Liabilities
    +/- Change in Security Deposits Held
    +/- Change in Deferred Revenue
  = Net Cash from Operating Activities

INVESTING ACTIVITIES:
  - Property acquisitions
  - Capital improvements
  - Tenant improvements
  + Proceeds from property sales
  - Escrow deposits
  = Net Cash from Investing Activities

FINANCING ACTIVITIES:
  + Mortgage proceeds
  - Mortgage principal payments
  + Owner contributions
  - Owner distributions
  + Line of credit draws
  - Line of credit repayments
  = Net Cash from Financing Activities

Net Change in Cash = Operating + Investing + Financing
Ending Cash = Beginning Cash + Net Change in Cash
```

### Projection-Specific: Waterfall Structure

For projections, each period follows the CRE pro forma waterfall:

```
GROSS POTENTIAL RENTAL REVENUE
  Base Rent (per lease terms or market rent assumptions)
  + Straight-Line Rent Adjustment
= GROSS RENTAL REVENUE
- VACANCY & CREDIT LOSS (% of GPR)
- CONCESSIONS / FREE RENT
= EFFECTIVE RENTAL REVENUE
+ OTHER REVENUE
  CAM / OPEX Recoveries
  Tax / Insurance Recoveries
  Percentage Rent (if applicable)
  Parking, Storage, Other Income
= TOTAL REVENUE / EFFECTIVE GROSS INCOME (EGI)

OPERATING EXPENSES (escalated per period)
  Property Management Fees (% of EGI)
  Repairs & Maintenance
  Utilities
  Property Taxes
  Insurance
  Janitorial, Landscaping, Security
  Administrative, Professional Fees
  Marketing, Leasing Commissions
= TOTAL OPERATING EXPENSES

NET OPERATING INCOME (NOI) = EGI - OpEx   [key metric]

NON-OPERATING:
  - Depreciation & Amortization
  - Interest Expense
  - Amortization of Financing Costs
= NET INCOME

SUPPLEMENTAL:
  DSCR = NOI / Debt Service
  Debt Yield = NOI / Loan Amount
  FFO = Net Income + Depreciation - Gains + Losses
```

Each sandbox must document every assumption (rent growth rate, vacancy rate,
expense escalation, etc.) with source and justification.

---

## Error Recovery

### If a sandbox agent fails or crashes:
- The Primary Accountant detects the missing output file
- Re-spawns only the failed sandbox with the same parameters
- Does not re-spawn sandboxes that completed successfully

### If the Primary Accountant fails:
- The SKILL.md detects the Task failure
- Reads the session manifest to determine progress
- If sandboxes completed, re-spawns the accountant starting from comparison
- If sandboxes did not complete, re-spawns everything

### If max iterations exceeded (actual mode):
- The accountant writes a `convergence-report.yaml` detailing remaining differences
- Generates a draft XLSX using the sandbox output with the fewest material differences
- Presents the user with options: resume, accept best, or abandon

---

*ACOS Financial Statement — Triple-redundancy adversarial preparation with Wigum loop convergence.*
