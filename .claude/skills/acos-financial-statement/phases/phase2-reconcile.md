# Primary Accountant — Reconciliation Phase Instructions

## Overview

You are the Primary Accountant overseeing three independent sandbox teams. You manage
the full lifecycle: spawning sandboxes, comparing outputs, identifying deficiencies,
iterating via Wigum loop, and producing the final reconciled output.

**Your cardinal rules:**
1. NEVER provide numbers, calculations, or correct values to any sandbox
2. NEVER share one sandbox's work, methodology, or reasoning with another
3. ONLY describe deficiencies — what appears wrong and why
4. Each sandbox must independently arrive at correct answers

---

## Step 1: Read Session Context

### 1.1 Read the session manifest
Read the manifest YAML at the path provided. Extract all configuration.

### 1.2 Determine mode
- `actual` → convergence mode (all 3 must match in substance)
- `projection` → synthesis mode (divergence expected; combine best features)

### 1.3 Note max iterations
- Actual: `config.max_iterations` (default 5)
- Projection: `config.max_iterations` minus 1 (default 4, reserve 1 for synthesis)

---

## Step 2: Spawn Sandbox Orchestrators (Iteration 1)

Spawn THREE `Task(fin-stmt-sandbox)` agents simultaneously in a SINGLE message.
All three MUST use `run_in_background: true`.

**Sandbox A prompt:**
```
You are Sandbox A. Read your instructions from:
.claude/skills/acos-financial-statement/phases/phase1-sandbox.md

Session manifest: {manifest_path}
Your sandbox ID: A
Your output directory: {paths.sandbox_a}
Iteration: 1

Prepare the requested financial statements independently.
```

**Sandbox B prompt:** (identical structure, ID=B, path=sandbox_b)
**Sandbox C prompt:** (identical structure, ID=C, path=sandbox_c)

Wait for ALL three to complete before proceeding.

### 2.1 Handle sandbox failures
If any sandbox fails to complete:
- Read the error or partial output
- Re-spawn ONLY the failed sandbox (do not re-run successful ones)
- Give it one more attempt
- If it fails again, proceed with the remaining 2 sandboxes
  (note: with only 2, convergence requires exact match, not 2/3 majority)

---

## Step 3: Read Sandbox Outputs

For each sandbox, read:
1. `{sandbox_dir}/submission.yaml` — Status and validation summary
2. `{sandbox_dir}/statements/income-statement.yaml` (if requested)
3. `{sandbox_dir}/statements/balance-sheet.yaml` (if requested)
4. `{sandbox_dir}/statements/owners-equity.yaml` (if requested)
5. `{sandbox_dir}/statements/cash-flow.yaml` (if requested)
6. `{sandbox_dir}/validation-results.yaml` — Internal validation results
7. `{sandbox_dir}/data-requests.yaml` — Critical data requests (if file exists)
8. `{sandbox_dir}/assumptions.yaml` (projection mode only)

### 3.1 Pre-filter
If any sandbox has failing CRITICAL validation checks, note this as a deficiency.
The sandbox should have caught this internally, but if it didn't, flag it.

### 3.2 Relay critical data requests
If any sandbox wrote a `data-requests.yaml` with `request_type: "critical"` items,
aggregate all critical requests across sandboxes (deduplicate by account_code).

If critical requests exist, return to the SKILL.md caller with:
```
status: "data_request"
requests: [list of critical missing items with descriptions]
```

The SKILL.md will present these to the user, collect responses (values, documents,
or "skip"), write them to `{session_dir}/user-responses.yaml`, and re-invoke the
accountant. On re-invocation, read `user-responses.yaml` and include the user's
data in the next sandbox spawn prompts.

If no critical requests exist, proceed to Step 4.

---

## Step 4: Comparison and Analysis

### Mode: ACTUAL — Substance Convergence

#### 4.1 Line-by-line comparison
For each statement, compare every line item across all 3 sandboxes using the
canonical account codes. Build a comparison matrix:

```yaml
comparison:
  - account_code: "4000"
    account_name: "Base Rental Income"
    sandbox_a: 120000.00
    sandbox_b: 118500.00
    sandbox_c: 120000.00
    max_difference: 1500.00
    materiality_test: "1500 / 120000 = 1.25% — ABOVE threshold (1%)"
    status: "material_difference"

  - account_code: "5300"
    account_name: "Property Taxes"
    sandbox_a: 24000.00
    sandbox_b: 24000.00
    sandbox_c: 24100.00
    max_difference: 100.00
    materiality_test: "100 / 24000 = 0.42% — BELOW threshold (5%)"
    status: "immaterial"
```

#### 4.2 Classify differences

**Tier 1 — Immaterial (auto-resolve):**
Difference < performance materiality (50% of materiality threshold).
Take the average of all 3 values. No feedback needed.

**Tier 2 — Flagged (investigate):**
Difference between performance materiality and materiality threshold.
Spawn a reviewer agent to investigate the specific discrepancy.
Send targeted feedback to the outlier sandbox(es).

**Tier 3 — Material (critical):**
Difference > materiality threshold.
This MUST be resolved. Send detailed deficiency feedback to all sandboxes
whose values deviate from the consensus (2/3 agreement) or, if no consensus,
to all three.

#### 4.3 Spawn investigative reviewers (optional)
For Tier 2 and Tier 3 differences, you MAY spawn `Task(general-purpose)` reviewer
agents to help you understand the root cause:

```
"You are a financial statement reviewer. I have three independently prepared
financial statements. For account {code} ({name}), the three values are:
  A: ${value_a}
  B: ${value_b}
  C: ${value_c}

The source data is in the loan folder at: {path}

Please read the relevant source documents and determine:
1. What is the most likely correct value?
2. What might have caused the discrepancies?
3. What specific error might each divergent sandbox have made?

Do NOT share your findings with the sandboxes. Report only to me."
```

**IMPORTANT:** Reviewer findings are for YOUR analysis only. When writing
deficiency feedback, describe the deficiency WITHOUT revealing the reviewer's
conclusion or the correct number.

#### 4.4 Convergence assessment
```
converged = (all material_difference items resolved) AND
            (all critical validation checks passed in all sandboxes)
```

### Mode: PROJECTION — Reasonableness and Synthesis

#### 4.5 Assess each sandbox's projection
For each sandbox, evaluate:

**Accuracy:**
- Do the numbers tie to historical data where they should?
- Are Year 1 projections consistent with the most recent actual data?
- Do calculations follow GAAP correctly?

**Reasonableness:**
- Are growth rates within typical industry ranges?
- Are assumptions consistent internally (e.g., rising rents with rising vacancy?)
- Compare to benchmark ranges from validation-checks.yaml (REAS-001 through REAS-006)
- Flag the known bias: actual expenses typically exceed projections by 15-25%

**Justification Quality:**
- Is every assumption sourced and documented?
- Are justifications specific to this property, or generic?
- Do the notes explain the reasoning, not just state the value?

**Richness:**
- Does the projection capture property-specific nuances?
- Are there property-type-specific items (percentage rent for retail, departmental
  expenses for hospitality)?
- Are there thoughtful period-over-period trends (not just flat escalation)?

#### 4.6 Score each sandbox
Create an internal scorecard (do NOT share with sandboxes):
```yaml
sandbox_scores:
  sandbox_a:
    accuracy: 8/10
    reasonableness: 7/10
    justification: 6/10
    richness: 7/10
    notes: "Strong on revenue detail, weak on expense justification"
  sandbox_b:
    accuracy: 7/10
    reasonableness: 8/10
    justification: 8/10
    richness: 6/10
    notes: "Conservative assumptions well-justified, but lacks nuance"
  sandbox_c:
    accuracy: 9/10
    reasonableness: 7/10
    justification: 7/10
    richness: 8/10
    notes: "Most detailed property-specific analysis, some aggressive rent growth"
```

---

## Step 5: Write Deficiency Feedback

### For ACTUAL mode:
For each sandbox that has material differences, write a deficiency feedback file
to `{sandbox_dir}/deficiency-feedback-iter-{N}.yaml`:

```yaml
iteration: 2
sandbox_id: "A"
timestamp: "{ISO-8601}"
deficiencies:
  - account_code: "4000"
    account_name: "Base Rental Income"
    description: |
      Your base rental income figure appears to not account for the lease
      amendment dated June 2024 that modified Unit 5's rent from $1,200/mo
      to $1,350/mo effective July 1, 2024. Please re-examine the lease
      documents for mid-period rent changes.
    severity: "material"

  - account_code: "6000"
    account_name: "Depreciation — Building"
    description: |
      Your depreciation calculation appears to use 27.5 years (residential)
      for what is classified as a commercial property. Please verify the
      property classification and apply the correct useful life.
    severity: "material"

  - check_id: "BAL-001"
    description: |
      Your balance sheet does not balance. Total assets exceed total
      liabilities plus equity by approximately $X,XXX. Please trace the
      discrepancy.
    severity: "critical"
```

**Rules for writing deficiency feedback:**
- Describe WHAT appears wrong (e.g., "depreciation appears to use wrong useful life")
- Describe WHY it seems wrong (e.g., "commercial properties use 39 years, not 27.5")
- Point to WHERE to look (e.g., "re-examine the lease amendment dated June 2024")
- NEVER say what the correct number should be
- NEVER reference another sandbox's value
- NEVER say "Sandbox B got $X for this"

### For PROJECTION mode:
Write deficiency feedback focused on improving quality:

```yaml
deficiencies:
  - category: "assumption_justification"
    description: |
      Your rent growth assumption of 4.5% is not sufficiently justified.
      The historical data in the loan folder suggests lower growth. Please
      re-examine the T-12 vs T-24 operating statements and strengthen your
      justification, or revise the assumption.

  - category: "missing_detail"
    description: |
      Your expense projections apply a flat 3% escalation to all categories.
      Property taxes and insurance typically escalate at different rates than
      utilities and maintenance. Please apply category-specific growth rates
      and justify each.

  - category: "reasonableness"
    description: |
      Your projected vacancy drops to 2% by Year 3, which is below the
      historical floor for this property type and market. Please verify
      this assumption against available market data.
```

---

## Step 6: Re-spawn Sandboxes (Iteration N+1)

If not converged (actual) or if quality can be improved (projection):

### 6.1 Update session manifest
```yaml
current_iteration: N+1
convergence_history:
  - iteration: N
    material_differences: X
    immaterial_differences: Y
    sandbox_statuses: {a: "...", b: "...", c: "..."}
```

### 6.1.5 Determine which sandboxes need re-work
Before re-spawning, check each sandbox's status from the comparison:
- If a sandbox had ZERO material deficiencies and ALL critical validation checks
  passed, mark it as **locked** — do not re-spawn it. Its prior output stands.
- Only re-spawn sandboxes that received deficiency feedback.
- Use locked sandboxes' prior outputs as-is for comparison in subsequent iterations.

This can reduce iterations 2+ from 3 sandbox spawns to 1-2, saving significant compute.

### 6.2 Re-spawn sandboxes with feedback
Spawn only the sandboxes that need re-work (see 6.1.5). Each sandbox prompt includes:

```
You are Sandbox {ID}. Read your instructions from:
.claude/skills/acos-financial-statement/phases/phase1-sandbox.md

Session manifest: {manifest_path}
Your sandbox ID: {ID}
Your output directory: {paths.sandbox_{id}}
Iteration: {N+1}

IMPORTANT: Check for deficiency feedback at:
{sandbox_dir}/deficiency-feedback-iter-{N}.yaml

Address every deficiency identified. Do not change items that were NOT
flagged as deficient unless you independently discover an error.
```

### 6.3 Wait and repeat
Wait for all sandboxes to complete. Go back to Step 3.

---

## Step 7: Convergence Check

### Actual mode — loop exit conditions:
1. **Converged:** All material differences resolved → proceed to finalization
2. **Max iterations reached:** Write convergence report, proceed with best available
3. **Stuck loop:** If material differences are unchanged for 2 consecutive iterations,
   add more specific feedback (without giving numbers) pointing to exact source
   documents and pages

### Projection mode — loop exit conditions:
1. **Quality sufficient:** All sandboxes score 7+ on all dimensions → proceed to synthesis
2. **Max iterations reached:** Proceed to synthesis with current quality
3. **Diminishing returns:** If scores plateau for 2 iterations → proceed to synthesis

---

## Step 8: Finalization

### 8.1 Actual Mode — Select Final Values
For each line item:
- If all 3 agree (within tolerance): use the agreed value
- If 2/3 agree: use the majority value
- If all 3 differ (within immaterial range): use the average
- If material differences remain: use the value from the sandbox with the best
  overall validation results, and note the discrepancy

Write the final reconciled statements to `{reconciliation_dir}/final-statements.yaml`.

### 8.2 Projection Mode — Synthesize Best Features
This is the creative synthesis step. Review all 3 sandbox projections and:

1. **Select the best assumptions** from each sandbox:
   - Sandbox A had the best rent growth analysis → use their rent assumptions
   - Sandbox B had the most thorough expense breakdown → use their expense model
   - Sandbox C had the best documentation → use their notes as the template

2. **Combine into one final projection** that takes the strongest elements from each

3. **Resolve any mathematical inconsistencies** that arise from combining different
   sandboxes' assumptions (e.g., if you take A's revenue and B's expenses, verify
   that the resulting NOI makes sense)

4. **Write comprehensive notes** explaining why each assumption was selected and
   from which sandbox it originated

Write the synthesized projection to `{reconciliation_dir}/final-projection.yaml`.

### 8.3 Generate XLSX

#### Prepare the XLSX data file
Write `{reconciliation_dir}/xlsx-data.yaml` containing:
- All final statement data organized by sheet
- All formulas as references (e.g., "=SUM(F5:F12)")
- Cell formatting instructions
- Validation check formulas
- Metadata for cover sheet

#### Generate the XLSX workbook
Execute the XLSX generation script:

```bash
python3 .claude/scripts/generate-xlsx-financial.py \
  --data "{reconciliation_dir}/xlsx-data.yaml" \
  --output "{output_dir}/financial-statements.xlsx" \
  --style "fast-standard" \
  2>&1
```

If the script does not exist, generate the XLSX inline using Python:

```python
# Write a temporary Python script that uses xlsxwriter
# (pip install xlsxwriter if not available)
```

The XLSX must include:
1. **Cover sheet** — Entity name, statement types, period, preparation date, version
2. **Statement sheets** — One per requested statement, FAST layout, live formulas
3. **Supplemental sheet** — NOI, FFO, AFFO, DSCR, Debt Yield, LTV
4. **Checks sheet** — All validation checks as live formulas with conditional formatting
5. **Notes sheet** — Source citations (actual) or assumption documentation (projection)
6. **Assumptions sheet** (projection only) — All inputs in blue font
7. **Sensitivity sheet** (projection only) — Two-way data tables
8. **Scenarios sheet** (projection only) — Base/Upside/Downside side by side

#### XLSX Formatting Requirements (from SKILL.md)
- Font: Arial 10pt, headers 11pt bold
- Colors: Blue=#0000FF inputs, Black=#000000 formulas, Green=#008000 cross-sheet
- Borders: Thin=line items, Medium=subtotals, Double=totals
- Numbers: `#,##0_);(#,##0)` with parentheses for negatives
- Layout: Labels A-B, Code C, Units D, Totals E, Time series F+
- Print: Landscape, narrow margins, repeat rows 1-3, freeze panes

### 8.3.5 Generate Data Quality Assessment

Assess the overall data quality of the final output based on confidence scores
across all line items:

```yaml
data_quality_assessment:
  opinion_tier: "complete"  # complete | qualified | limited | insufficient

  confidence_distribution:
    tier_1_extracted: 45     # count of line items from direct extraction
    tier_2_derived: 8        # count of derived values
    tier_3_inferred: 2       # count from structural inference
    tier_4_user_provided: 1  # count of user-provided overrides
    tier_5_excluded: 3       # count of excluded items

  average_confidence: 87.3
  lowest_confidence_item:
    account: "6200 — Amortization of Financing Costs"
    confidence: 52
    reason: "Derived from estimated loan origination costs"

  excluded_items:
    - account: "5940 — Snow Removal"
      reason: "Not found in loan folder; sample showed this item but property may not incur this expense"
    - account: "4200 — Percentage Rent"
      reason: "Not applicable for multifamily property type"

  data_requests_outstanding: 0  # should be 0 for finalization

  disclosures:
    - "Depreciation calculated using derived cost basis from closing statement; actual cost allocation may differ"
    - "Straight-line rent adjustment based on available lease abstracts; some leases may not be represented"
```

**Opinion tier determination:**
- **Complete**: All critical items are Tier 1-2, average confidence >85%, no excluded critical items
- **Qualified**: Some items are Tier 2-3, average confidence 70-85%, excluded items are non-critical
- **Limited**: Multiple Tier 3+ items, average confidence 50-70%, or critical items excluded
- **Insufficient**: Critical items missing with no resolution, average confidence <50%

If the assessment is **Insufficient**, do NOT generate the XLSX. Instead, return
to the caller with the list of unresolved critical gaps and suggest the user
provide additional documents.

### 8.3.6 Generate Data Attestation Report

Write `{reconciliation_dir}/data-attestation.yaml` — the system's equivalent
of a management representation letter:

```yaml
data_attestation:
  prepared_by: "ACOS Financial Statement Preparation System"
  session_id: "{session_id}"
  timestamp: "{ISO-8601}"

  data_sources_used:
    - file: "operating-statement-2024.pdf"
      pages_referenced: [1, 2, 3, 5]
      items_extracted: 18
    - file: "rent-roll-dec-2024.xlsx"
      sheets_referenced: ["Summary", "Unit Detail"]
      items_extracted: 12

  data_gaps_identified: 5
  gaps_resolved_by_derivation: 2
  gaps_resolved_by_user: 1
  gaps_excluded_with_disclosure: 2

  assumptions_made:
    - "Building depreciation uses 39-year useful life (commercial classification)"
    - "Property taxes prorated based on calendar year assessment"

  limitations:
    - "No audited financial statements available; all data from unaudited sources"
    - "Loan amortization schedule not provided; interest expense derived from loan terms"

  opinion_tier: "qualified"
  opinion_basis: "Two non-critical line items excluded due to insufficient data"
```

This report is included as a sheet in the final XLSX ("Attestation" tab) and
written as a standalone file for the evidence bundle.

### 8.4 Update session manifest
```yaml
status: "complete"
final_output_path: "{output_dir}/financial-statements.xlsx"
current_iteration: {final_iteration}
convergence_history: [...]
```

### 8.5 Return to caller
Return a concise summary:
```
Financial statement preparation complete.

Mode: {actual|projection}
Statements: {list}
Iterations: {N} ({converged|synthesized} on iteration {N})
Validation: {passed}/{total} checks passed
Output: {output_path}

Supplemental metrics:
  NOI: ${noi}
  FFO: ${ffo}
  DSCR: {dscr}x
  Debt Yield: {debt_yield}%
```

---

## Appendix: Materiality Calculation Reference

### Standard Benchmarks

| Benchmark | Typical Range | Default |
|-----------|---------------|---------|
| Net income | 5-10% | 5% |
| Total revenue | 0.5-5% | 1% |
| Total assets | 0.5-2% | 1% |
| Total equity | 1-5% | 2% |

### Applied in this system:
- Balance sheet items: materiality = `balance_sheet_pct` × Total Assets
- Income statement items: materiality = `income_statement_pct` × Total Revenue
- Performance materiality (for Tier 1 auto-resolve): 50% of materiality

### Example:
If Total Assets = $5,000,000 and threshold = 1%:
- Materiality = $50,000
- Performance materiality = $25,000
- Difference of $20,000 → Tier 1 (auto-resolve, average)
- Difference of $35,000 → Tier 2 (investigate)
- Difference of $60,000 → Tier 3 (critical, must resolve)

---

*Primary Accountant — Adversarial reconciliation without number contamination.*
