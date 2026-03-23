---
name: acos-pdf-xlsx-converter
description: Converts PDF financial/accounting documents to production-grade XLSX spreadsheets with 0% error tolerance. Triple adversarial review (Value Verifier, Structure Auditor, Formula Validator) ensures every number, heading, and formula is correct. Use when the user wants to convert a PDF to spreadsheet, extract tables from PDF, or create Excel from PDF.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

# ACOS PDF to XLSX Converter

## Purpose

Extracts structured data from PDF financial/accounting documents and generates
production-grade XLSX spreadsheets with professional formatting, live formulas,
and triple adversarial review for 0% error tolerance. Designed for accounting
documents where a single wrong digit is unacceptable.

## When to Use

Apply this skill when:
- The user wants to convert a PDF to an Excel spreadsheet
- The user needs to extract tables/numbers from a PDF into XLSX
- The user has an accounting document (income statement, balance sheet, trial balance, rent roll, etc.) in PDF form
- The user says "create a spreadsheet from this PDF" or "turn this PDF into Excel"
- The user needs a financial document digitized with zero errors

## Arguments

`$ARGUMENTS` accepts:
- `<pdf-path>` — Path to the source PDF file (required)
- `--output <path>` — Output directory for the XLSX (default: `~/Desktop/`)
- `--skip-review` — Skip the triple review (NOT recommended for accounting docs)
- `--format <type>` — Document type hint: `income-statement`, `balance-sheet`, `rent-roll`, `trial-balance`, `general` (default: auto-detect)

Examples:
```
/acos-pdf-xlsx-converter /path/to/income-statement.pdf
/acos-pdf-xlsx-converter /path/to/doc.pdf --output /path/to/folder/
/acos-pdf-xlsx-converter /path/to/doc.pdf --format balance-sheet
```

## Skill Protocol

### Phase 1: Source Analysis

1. **Read the PDF** using the Read tool (supports PDF natively, max 20 pages per read)
   - For PDFs > 20 pages, read in batches using the `pages` parameter
2. **Identify document type** (if not specified via `--format`):
   - Income Statement: has Revenue, Expenses, Net Income
   - Balance Sheet: has Assets, Liabilities, Equity
   - Rent Roll: has tenant names, lease terms, rent amounts
   - Trial Balance: has Debit/Credit columns
   - General: tabular data with headers and values
3. **Map the document structure**:
   - Column headers (months, categories, periods)
   - Row hierarchy (sections, sub-sections, line items, subtotals, totals)
   - Account codes (if present)
   - Number format (decimals, negatives, currency)
   - Metadata (property name, period, entity, notes)
4. **Count the scope**: total rows, columns, estimated cell count
5. **Report to user**: "{document_type} detected: {rows} rows x {cols} columns = ~{cells} values to extract"

### Phase 2: Structured Extraction

1. **Define the data structure** — each row needs:
   - `code`: Account code or row identifier (if present)
   - `name`: Account name or row label
   - `indent`: Visual hierarchy level (0 = top, higher = deeper)
   - `style`: `h` (header, no values), `l` (line item), `t` (subtotal, bold), `T` (major total, bold + border)
   - `values`: List of numeric values for each column, or `None` for header-only rows

2. **Extract ALL data** — Go through the PDF page by page, row by row:
   - Every number must be extracted to 2 decimal places (or whatever precision the source uses)
   - Negative numbers: preserve the sign (watch for parenthetical negatives)
   - Zero values: explicitly include as `0.00`
   - Headers with no values: mark as style `h` with `None` values
   - Subtotal rows: mark as style `t` or `T`

3. **Organize into Python data structure** — Create a `DATA` list of tuples:
   ```python
   DATA = [
       (code, name, indent, style, [val1, val2, ..., valN]),
       ...
   ]
   ```

4. **Sanity check**: Count extracted rows vs. PDF rows. They must match.

### Phase 3: XLSX Generation

Generate the spreadsheet using Python + openpyxl. The script must include:

**Header Section:**
- Document title (merged across columns, large bold font)
- Metadata lines (entity, period, currency, book type — whatever the source has)
- Column headers with professional styling (dark fill, white bold text)

**Data Section:**
- Account codes in column A (if present)
- Account names in column B with indentation matching hierarchy
- Numeric values in columns C onward
- **SUM formulas** in the Total column (not hardcoded values)
- Number format: `#,##0.00` (comma-separated with 2 decimals)

**Formatting:**
- Section headers: bold, colored font (navy)
- Subtotals: bold with thin bottom border
- Major totals: bold with top+bottom borders, light gray fill on grand totals
- Frozen panes (headers + label columns stay visible when scrolling)
- Column widths sized for content
- Print-ready layout (landscape, fit-to-width)

**Script execution:**
```bash
python3 /path/to/generate_script.py
```

Verify the XLSX was created successfully before proceeding.

### Phase 4: Triple Adversarial Review

Launch **3 independent reviewer agents in parallel** using `run_in_background: true`. Each reviewer operates in isolation (cannot see the others' work). **All 3 must PASS** for the extraction to be accepted.

#### Reviewer 1: Value Verifier
- Reads the source PDF and the generation script
- Checks EVERY individual value cell-by-cell against the PDF
- Looks for: transposed digits, wrong signs, missing decimals, values in wrong columns
- Reports: total values checked, errors found, error details
- Verdict: PASS (0 errors) or FAIL

#### Reviewer 2: Structure Auditor
- Verifies ALL rows from the PDF exist in the extraction (completeness)
- Checks account codes, names, spelling, capitalization
- Verifies no missing or phantom rows
- Checks hierarchy and indent levels
- Verifies metadata (property, period, entity)
- Verdict: PASS or FAIL

#### Reviewer 3: Formula Validator
- **Horizontal check**: For every row, sum the period values and compare to the PDF's stated Total
- **Vertical check**: For every subtotal/total row, verify it equals the sum of its children
- **Cross-foot check**: Verify grand total chains (e.g., Revenue - Expenses = NOI)
- Reports: checks passed, checks failed, discrepancy details
- Verdict: PASS or FAIL

### Phase 5: Error Resolution (if needed)

If ANY reviewer reports FAIL:
1. Read the error details from the failed reviewer(s)
2. Fix the errors in the generation script
3. Re-generate the XLSX
4. Re-run ONLY the failed reviewer(s)
5. Repeat until all 3 pass

### Phase 6: Delivery

1. **Clean up** — Remove the temporary generation script
2. **Report** to the user:
   - File location
   - Document summary (type, rows, columns, total values)
   - Review results table (all 3 reviewers with verdicts)
   - Any notes about the source document (e.g., math errors in the PDF itself)

## Quality Checklist

- [ ] Every number in the XLSX matches the source PDF exactly
- [ ] All account codes and names are present and correctly spelled
- [ ] No rows are missing or duplicated
- [ ] Total column uses SUM formulas (not hardcoded values)
- [ ] Subtotal/total hierarchy is correct
- [ ] Professional formatting applied (fonts, borders, number formats, frozen panes)
- [ ] All 3 reviewers returned PASS
- [ ] Temporary generation script cleaned up
- [ ] Output file is in the requested location

## Document Type Patterns

### Income Statement
- Columns: periods (months, quarters, years) + Total
- Rows: Revenue categories → Expense categories → NOI → Non-Op → Net Income
- Account codes: typically 4-digit with sub-codes (e.g., 4100-120)
- Key formulas: Revenue totals, Expense totals, NOI = Revenue - Expenses

### Balance Sheet
- Columns: periods or Current vs. Prior
- Rows: Assets → Liabilities → Equity
- Key formula: Assets = Liabilities + Equity

### Rent Roll
- Columns: Tenant, Suite, SF, Lease Start, Lease End, Base Rent, Recoveries, Total
- Rows: one per tenant/unit
- Key formulas: column totals, PSF calculations

### Trial Balance
- Columns: Account, Debit, Credit
- Rows: all GL accounts
- Key formula: Total Debits = Total Credits

## Dependencies

- **Python 3** with `openpyxl` library (`pip install openpyxl`)
- PDF must be text-based (not scanned images — OCR not supported)

## Output

- `{Document Name}.xlsx` — The production-grade spreadsheet
- Review results reported inline (not saved to file)

---
*ACOS PDF to XLSX Converter — Zero-error financial document digitization.*
