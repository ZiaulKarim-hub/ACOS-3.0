---
name: okoa-deal-analyzer
user-invocable: false
description: "Analyze prospective real estate credit deals against OKOA investment criteria. Use when evaluating new deal opportunities, assessing risk/return profiles, or preparing deal summaries for investment committee. Triggers on: analyze deal, deal analysis, evaluate opportunity, new deal, prospective deal, deal summary, investment criteria."
---

# OKOA Deal Analyzer Skill

Comprehensive deal analysis system for OKOA's private credit real estate investments.

## Investment Criteria

### Target Profile
- **Transaction Size:** $1-20M
- **Geography:** Western U.S. primary, with assessments throughout U.S. and Canada
- **Deal Types:** Bridge loans, construction financing, preferred equity, note purchases
- **Property Types:** Residential, commercial, land development, special situations

### Risk Parameters
- **LTV Maximum:** 70% (80% with strong sponsor)
- **Debt Service Coverage:** Minimum 1.20x
- **Interest Rate Floor:** Market + spread based on risk
- **Term:** Typically 12-36 months

## Analysis Framework

### 1. Deal Summary
```yaml
deal_summary:
  property_name: ""
  property_address: ""
  property_type: ""  # residential, commercial, land, mixed-use
  deal_type: ""      # bridge, construction, pref equity, note purchase
  loan_amount: 0
  ltv_percent: 0
  interest_rate: ""
  term_months: 0
  sponsor_name: ""
  source: ""         # broker, direct, referral
```

### 2. Property Analysis
```yaml
property_analysis:
  current_value: 0
  as_is_value: 0
  as_stabilized_value: 0
  recent_appraisal_date: ""
  property_condition: ""  # excellent, good, fair, needs_work
  occupancy_percent: 0
  market_rent_psf: 0
  comparable_sales: []
```

### 3. Sponsor Evaluation
```yaml
sponsor_evaluation:
  experience_years: 0
  similar_projects_completed: 0
  net_worth: 0
  liquidity: 0
  credit_score: 0
  guaranty_type: ""  # full, limited, springing
  track_record_notes: ""
```

### 4. Risk Assessment
```yaml
risk_assessment:
  market_risk: ""     # low, moderate, elevated, high
  execution_risk: ""
  sponsor_risk: ""
  exit_risk: ""
  legal_risk: ""
  overall_risk: ""
  risk_mitigants: []
  deal_breakers: []
```

### 5. Return Analysis
```yaml
return_analysis:
  gross_yield: 0
  net_yield: 0
  origination_fee: 0
  exit_fee: 0
  total_return: 0
  irr_base_case: 0
  irr_downside: 0
```

## Analysis Workflow

1. **Gather Information**
   - Read deal documents from `deals/01_prospective/{deal-folder}/`
   - Extract key terms from term sheet
   - Review property information

2. **Run Quantitative Analysis**
   - Calculate LTV and coverage ratios
   - Model cash flows and returns
   - Run sensitivity analysis on key variables

3. **Perform Qualitative Assessment**
   - Evaluate sponsor strength
   - Assess market conditions
   - Identify execution risks

4. **Generate Output**
   - Create deal summary YAML
   - Generate investment memo outline
   - Flag items requiring further diligence

## Output Format

### Deal Analysis Report
```markdown
# Deal Analysis: {Property Name}

## Executive Summary
- **Recommendation:** [Proceed to DD / Decline / Need More Info]
- **Key Strength:**
- **Key Risk:**
- **Quick Take:**

## Deal Overview
| Metric | Value |
|--------|-------|
| Loan Amount | ${amount} |
| LTV | {pct}% |
| Rate | {rate}% |
| Term | {months} months |

## Property Summary
{property_description}

## Sponsor Summary
{sponsor_assessment}

## Risk Assessment
| Risk Category | Level | Notes |
|---------------|-------|-------|
| Market | {level} | {notes} |
| Execution | {level} | {notes} |
| Sponsor | {level} | {notes} |
| Exit | {level} | {notes} |

## Return Analysis
| Metric | Base Case | Downside |
|--------|-----------|----------|
| Gross Yield | {pct}% | {pct}% |
| Total Return | {pct}% | {pct}% |
| IRR | {pct}% | {pct}% |

## Due Diligence Items
1. [ ] {item}
2. [ ] {item}
3. [ ] {item}

## Recommendation
{detailed_recommendation}
```

## Integration Points

- **Hypercore LMS:** Pull comparable loan data
- **PRISM Modeler:** Generate detailed financial model
- **Document Synthesizer:** Process supporting documents

## Usage

This hidden skill is normally reached through `/okoa`.

```text
/okoa Analyze deals/01_prospective/smith-property-bridge/ against OKOA criteria and save the analysis in my workspace.
```

This will:
1. Read all documents in the deal folder
2. Run the analysis framework
3. Generate a deal analysis report
4. Create a due diligence checklist
5. Save outputs to the personal workspace first for review
