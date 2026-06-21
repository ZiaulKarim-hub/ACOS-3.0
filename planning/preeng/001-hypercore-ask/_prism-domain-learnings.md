# PRISM Domain Learnings — acos-hypercore-ask Ontology
<!-- synthesized 2026-06-19 from ~/okoa-labs/okoa_ops PRISM files (read-only) -->

## Files consulted

| File | Purpose |
|------|---------|
| `.claude/skills/prism-financial-modeler/SKILL.md` | Capability overview, template list, KG-extraction fields |
| `.claude/skills/prism-financial-modeler/prism-agent-config.yaml` | Full agent spec (568 L): domain competencies, modeling specs, wall-street conventions |
| `.claude/skills/prism-financial-modeler/templates/bridge-loan.yaml` | Concrete field-level bridge-loan model — formulas, covenants, returns sheet |
| `.claude/skills/prism-financial-modeler/scripts/institutional_model.py` | Excel builder: number-format constants, color conventions |
| `.claude/skills/prism-financial-modeler/scripts/model_validator.py` | 9-check validation, cell-type taxonomy |
| `.claude/skills/prism-research/SKILL.md` | Research protocol, risk-severity matrix, confidence tiers |
| `.claude/prompts/prism-intelligence-v2-0.md` | Deployed system prompt: executive-dashboard schema, cross-doc analysis |
| `.system/canonical-examples/CANONICAL_PRISM_INTELLIGENCE_SYSTEM_v2.0.0_COMPLETE.yaml` | 540-L partial canonical (note: self-describes as partial; full spec ~1500 L lives at session init) |
| `.system/canonical-examples/CANONICAL_DD_FRAMEWORK_v3.0_COMPLETE.yaml` | 3211-L, 231-item DD framework with category codes (CCII) |
| `docs/prism-setup.md` | Setup + 9-point validation checklist |

---

## 1. Private-Credit Metrics — Definitions, Formulas, and Inputs

All definitions below are extracted from or consistent with PRISM's bridge-loan template
(`templates/bridge-loan.yaml`) and `prism-agent-config.yaml` unless noted otherwise.
Where PRISM gives an explicit formula, it is quoted verbatim. Where PRISM implies the
formula from field definitions, it is reconstructed and marked *(derived)*.

### 1.1 Loan Balance Metrics

#### Outstanding / Principal Balance
- **PRISM field:** `beginning_balance` (Cash Flow sheet, monthly time-series column)
- **Definition:** Unpaid principal as of a period-start date before any payments.
- **Formula (bridge-loan template):** `ending_balance[t-1]` → rolled forward each month.
- **Ending balance:** `=beginning_balance + draws - principal_paid` *(derived; interest-only loans → principal_paid = 0 until payoff)*
- **Hypercore map:** `outstanding` (loan-level field), `totalDue` is a superset (see below).

#### Total Due / Payoff
- **PRISM field:** `loan_payoff` (Exit Analysis sheet)
- **Formula:** `=ending_balance + exit_fee`
  - `exit_fee = loan_amount × exit_fee_pct` (default 1%)
- **Also includes:** accrued/unpaid interest at payoff date *(derived; not split out in template but implied by cash-flow schedule)*
- **Hypercore map:** `totalDue`; `penalties` would add default interest/late charges on top.

#### Interest Reserve
- **PRISM field:** `interest_reserve` (Sources & Uses sheet)
- **Formula:** `=loan_amount × interest_rate × reserve_months / 12`
- **Inputs:** loan_amount, interest_rate (annual), reserve_months (default 12)
- **Note:** Interest is drawn monthly from reserve (`reserve_draw`); reserve depletes over time.

#### Accrued Interest (monthly)
- **PRISM field:** `interest_accrued` (Cash Flow sheet)
- **Formula:** `=beginning_balance × interest_rate / 12`
- **Inputs:** beginning_balance, interest_rate (annual)
- **Note:** For interest-only (I/O) loans (OKOA's default), `interest_paid = interest_accrued`; no principal amortization until balloon.

#### Default / Penalty Interest
- **PRISM mentions:** "default interest" as a risk in bridge-lending competencies; not modeled as a separate formula in the bridge-loan template (penalty rate = note rate + spread, applied only post-default).
- **Reconstructed formula:** `default_interest_accrued = outstanding × default_rate / 12`
  - `default_rate` is typically `note_rate + 3–5%` (OKOA-specific; not hardcoded in PRISM template).
- **Hypercore map:** `penalties` field in Hypercore InstallmentComponents breakdown.

### 1.2 Loan Sizing / Commitment

#### Loan Amount / Commitment
- **PRISM field:** `loan_amount` / `senior_loan` (Sources & Uses sheet)
- **Definition:** The face amount committed by the lender; the ceiling on total draws.
- **Hypercore map:** `commitment` field.

#### Utilization (for revolving/construction facilities)
- **PRISM mentions:** "revolving credit facilities with commitment fees" and "delayed draw term loans with ticking fees" as modeling capabilities.
- **Formula (derived):** `utilization = outstanding / commitment`
- **Note:** PRISM tracks `unused_line_fee` (% of undrawn commitment) as a cost item in the Assumptions sheet.
- **Hypercore map:** `outstanding / commitment` → can be computed on-the-fly from Hypercore fields.

#### Capex Holdback
- **PRISM field:** `capex_holdback_pct` (Assumptions → Reserves section, default 10%)
- **Definition:** Portion of renovation budget withheld and released as draws upon verified completion milestones.
- **Formula:** `holdback = renovation_budget × capex_holdback_pct`
- **Hypercore map:** Maps to `fundings` (draws released from holdback) vs. `commitment`.

### 1.3 Leverage Ratios

#### LTV — Loan-to-Value
- **PRISM field:** `ltv` (Cover sheet)
- **Formula:** `=loan_amount / purchase_price` (as-is basis)
- **PRISM covenant:** `max_ltv` default **75%**; validation fires error if exceeded.
- **Variants PRISM tracks:**
  - As-Is LTV: `loan_amount / as_is_value`
  - As-Stabilized LTV: `loan_amount / as_stabilized_value`
  - Post-renovation LTV uses `exit_value` in the Exit Analysis sheet.
- **Source:** `bridge-loan.yaml`, Assumptions → Covenants; Cover → Key Metrics.
- **Hypercore map:** Computable from `outstanding` (or `commitment`) ÷ collateral value (not in Hypercore itself — needs appraisal feed).

#### LTC — Loan-to-Cost
- **PRISM mentions:** "construction loan modeling with funding ratios" — LTC is the construction-loan analog of LTV.
- **Formula (derived):** `ltc = loan_amount / total_project_cost`
  - `total_project_cost = purchase_price + renovation_budget + closing_costs + carrying_costs`
- **Not in bridge-loan template** (construction template referenced but not present in read files).
- **Hypercore map:** Not a native field; requires manual cost-basis input from deal docs.

#### DSCR — Debt Service Coverage Ratio
- **PRISM field:** `min_dscr` (Assumptions → Covenants, default **1.25x**)
- **Formula:** `=noi / (loan_amount × interest_rate)` *(I/O bridge; denominator is annual interest only)*
  - For amortizing: `=noi / annual_debt_service` where `annual_debt_service = P+I payments × 12`
- **Validation:** Warning if below covenant floor.
- **Source:** `bridge-loan.yaml`, validations section: `"=noi / (loan_amount * interest_rate) >= min_dscr"`
- **Note:** PRISM treats DSCR as an underwriting/covenant metric, not a portfolio roll-up metric.
- **Hypercore map:** Requires NOI (property income) + `outstanding` + `interest` from Hypercore; NOI not in Hypercore directly.

#### Debt Yield
- **PRISM field:** `min_debt_yield` (Assumptions → Covenants, default **8%**)
- **Formula (derived):** `debt_yield = noi / loan_amount`
- **Definition:** The unleveraged return the lender would earn if it took title — independent of cap-rate assumptions, making it a preferred stress metric vs. LTV.
- **Source:** `bridge-loan.yaml`, Assumptions → Covenants section.
- **Hypercore map:** Same note as DSCR — needs NOI from outside Hypercore.

### 1.4 Rate Metrics

#### Coupon / Note Rate
- **PRISM field:** `interest_rate` (Assumptions → Loan Terms)
- **Validation range:** 8%–20% (`{ min: 0.08, max: 0.20 }`)
- **Payment types modeled:** Interest-Only (OKOA default), P+I, Partial P+I.

#### Floating Rate Decomposition
- **PRISM fields:**
  - `index_rate` — benchmark (e.g., SOFR, Prime)
  - `spread = interest_rate - index_rate`
- **Hypercore map:** `interest` field in InstallmentComponents; rate decomposition not explicit.

#### All-In / Effective Yield (Lender)
- **PRISM field:** `effective_yield` (Returns sheet, labeled "All-in Yield incl fees")
- **Definition:** Lender's yield including origination fee, exit fee, and any extension fees amortized over hold period.
- **Formula (derived):** `effective_yield = XIRR(lender_cash_flows, lender_dates)` inclusive of fee cash flows.
- **Also tracked:** `spread_over_index = effective_yield - index_rate`.
- **Source:** `bridge-loan.yaml`, Returns → Lender Returns section.

#### Blended / Weighted-Average Rate (Portfolio)
- **PRISM mentions:** "blended rate" implicitly in portfolio modeling competencies; not formula-defined in bridge-loan template.
- **Standard formula (derived):** `wa_rate = Σ(outstanding_i × rate_i) / Σ(outstanding_i)`
- **Hypercore map:** Computable from Hypercore `outstanding` + `interest` per loan.

### 1.5 Duration / Maturity

#### Term / Maturity
- **PRISM fields:**
  - `term_months` (default 24) — initial loan term
  - `extension_options` (default 2) + `extension_months_each` (default 6)
  - `maturity_date = closing_date + term_months / 12`
  - Max possible term = `term_months + (extension_options × extension_months_each)` months
- **Source:** `bridge-loan.yaml`, Assumptions → Loan Terms + Cover → Key Metrics.
- **Hypercore map:** `scheduleEndDate` / `maturity`.

#### WAM — Weighted-Average Maturity (Portfolio)
- **PRISM mentions:** "duration and interest rate sensitivity" and "vintage year diversification" in portfolio management.
- **Standard formula (derived):** `WAM = Σ(outstanding_i × months_to_maturity_i) / Σ(outstanding_i)`
- **Hypercore map:** Computable from `outstanding` + `scheduleEndDate` per loan.

#### WAL — Weighted-Average Life
- **PRISM mentions:** implicitly in CLO/CDO waterfall modeling and portfolio analytics.
- **Standard formula (derived):** `WAL = Σ(t × principal_payment_t) / total_principal` — more meaningful for amortizing loans; for I/O bridge loans WAL ≈ maturity.

### 1.6 Return Metrics

#### IRR — Internal Rate of Return
- **PRISM field:** `lender_irr` / `equity_irr` (Returns sheet)
- **Formula:** `=XIRR(cash_flows, dates)` — uses Excel's XIRR for uneven cash flows (non-negotiable Wall Street convention).
- **Lender cash flows:** `[-loan_amount, monthly_interest_paid..., loan_payoff + exit_fee]`
- **Equity cash flows:** `[-equity_invested, annual_distributions..., equity_proceeds_at_exit]`
- **Source:** `bridge-loan.yaml`, Returns sheet.

#### Lender Multiple (MOIC)
- **PRISM field:** `lender_multiple` (Returns → Lender Returns)
- **Formula:** `=total_lender_proceeds / loan_amount`
  - `total_lender_proceeds = SUM(interest_paid) + origination_fee + exit_fee + loan_amount`
- **Equity multiple:** `=equity_proceeds / equity_invested`
- **Note:** PRISM also uses MOIC/TVPI/DPI in the context of fund-level PE modeling (not bridge loans):
  - `TVPI (Total Value to Paid-In) = (NAV + Distributions) / Paid-In Capital`
  - `DPI (Distributed to Paid-In) = Distributions / Paid-In Capital`
  - `RVPI (Residual Value to Paid-In) = NAV / Paid-In Capital`

#### Cash-on-Cash
- **PRISM field:** `cash_on_cash` (Returns → Borrower Economics)
- **Formula:** `=annual_cash_flow / equity_invested`

### 1.7 Fee Metrics

#### Origination Fee
- **PRISM field:** `origination_fee_pct` (default **2%**), `origination_fee = loan_amount × origination_fee_pct`
- **Note:** Included in Uses of Funds; reduces net proceeds to borrower.

#### Exit Fee
- **PRISM field:** `exit_fee_pct` (default **1%**), `exit_fee = exit_value × exit_fee_pct` (or `loan_amount × exit_fee_pct`)
- **Included in:** `loan_payoff = ending_balance + exit_fee`

#### Extension Fee
- **PRISM field:** `extension_fee_pct` (default **0.5% per extension**)

#### Unused Line / Ticking Fee
- **PRISM field:** `unused_line_fee` (default 0%; applies to revolving/construction facilities)
- **Formula (derived):** `fee = (commitment - outstanding) × unused_line_pct / 12` per month

#### OID — Original Issue Discount
- **PRISM mentions:** OID implicitly through origination fee mechanics (fee taken at close reduces net proceeds; IRR calculation captures the effective OID impact).
- **Not explicitly labeled "OID" in template** — the origination fee IS the OID for tax purposes on private credit.

---

## 2. Ratios, Risk Methodology, and Analysis Framework

### 2.1 Credit Risk Assessment Framework

PRISM structures credit risk across four stages (source: `prism-agent-config.yaml`, research_methodology):

| Phase | Activities |
|-------|-----------|
| **Discovery** | Map capital structure, identify all entities, catalog regulatory requirements, assess data quality, establish assumptions |
| **Analysis** | Build financial models, perform multi-method valuations, test base/upside/downside/stress scenarios, Monte Carlo (10,000 iterations minimum) |
| **Verification** | Cross-check calculations independently, triangulate 3+ sources, test edge cases |
| **Synthesis** | Integrate findings, resolve conflicts, recommend, establish monitoring |

### 2.2 Covenant Testing

PRISM tracks three covenants for bridge loans (source: `bridge-loan.yaml`, Assumptions → Covenants):

| Covenant | Default Threshold | Formula | Error/Warning |
|----------|------------------|---------|---------------|
| Max LTV | 75% | `loan_amount / purchase_price ≤ 0.75` | **error** |
| Min DSCR | 1.25x | `noi / (loan_amount × interest_rate) ≥ 1.25` | warning |
| Min Debt Yield | 8% | `noi / loan_amount ≥ 0.08` | *(derived)* |

PRISM also models: recourse type (Full/Non-Recourse/Partial), guarantor coverage, and amendment fees for covenant waivers (mentioned in `prism-agent-config.yaml`).

### 2.3 Concentration Risk

Source: `CANONICAL_DD_FRAMEWORK_v3.0_COMPLETE.yaml`, dd_code 0408 (Credit & Risk Analysis):

> "Assessment of concentration risks including geographic, sector, tenant, customer, and counterparty concentration analysis."

PRISM's portfolio risk module explicitly tracks:
- Geographic concentration
- Sector/asset-type concentration
- Vintage year diversification
- Counterparty exposure limits
- Liquidity analysis and investor concentration (source: `prism-agent-config.yaml`, portfolio_management_risk)

### 2.4 "At-Risk" Signals (PRISM's risk escalation triggers)

Derived from DD Framework (dd_codes 0401–0410) and `prism-agent-config.yaml`:

- LTV breach (above covenant maximum)
- DSCR below minimum (1.25x for bridge)
- Debt yield below minimum (8%)
- Guarantor net worth insufficient
- Construction completion delay or cost overrun
- Missed payment / reserve depletion
- Counterparty credit deterioration
- Concentration limits exceeded
- Covenant non-compliance (tracked via "Covenant Structure & Testing" dd_code 0404)
- Negative portfolio correlation impact

### 2.5 Portfolio Roll-Up Methodology

Source: `prism-agent-config.yaml`, portfolio_analytics:
- PME calculations (various methodologies)
- Time-weighted vs. money-weighted returns
- Vintage year J-curve tracking
- Contribution and distribution modeling
- Commitment coverage ratios
- Sector and geographic exposure (roll-up from loan level)

### 2.6 Risk Severity Matrix

Source: `prism-research/SKILL.md`, Output Format Standards:

```
Severity = Likelihood Score × Impact Score
Likelihood: 1–5 scale
Impact:     1–5 scale
Severity:   1–25 scale

High:   16–25
Medium:  6–15
Low:     1–5
```

### 2.7 Valuation and Exit Scenarios

Source: `bridge-loan.yaml`, Exit Analysis sheet:

| Scenario | Formula |
|----------|---------|
| Exit value | `noi / exit_cap_rate` |
| Net exit proceeds | `exit_value - exit_costs - loan_payoff` |
| Refinance feasibility | `refi_loan_amount (= exit_value × refi_ltv) >= loan_payoff` |
| Cash-out on refi | `refi_loan_amount - loan_payoff` |

Sensitivity analysis is a 2-variable data table over `exit_cap_rate` and `hold_period` (output: `lender_irr`).

---

## 3. Terminology and Synonyms

The following synonyms were surfaced across PRISM files. Useful for intent-matching in acos-hypercore-ask:

| PRISM term | Synonyms / user phrasings |
|-----------|--------------------------|
| `loan_amount` / `senior_loan` | commitment, face amount, principal, loan size, facility amount |
| `outstanding` / `beginning_balance` | current balance, unpaid principal, UPB, principal outstanding |
| `interest_accrued` | accrued interest, PIK interest (if not paid), running interest |
| `loan_payoff` | payoff amount, total payoff, loan payoff balance |
| `totalDue` (Hypercore) | amount due, total outstanding, total owed |
| `exit_fee` | prepayment fee, exit charge, back-end fee |
| `origination_fee` | points, loan fee, front-end fee, origination points |
| `interest_reserve` | IR, interest holdback, reserve |
| `capex_holdback` | rehab holdback, renovation holdback, construction holdback |
| `ltv` | loan-to-value, LTV ratio, leverage ratio |
| `ltc` | loan-to-cost, LTC ratio |
| `dscr` | debt service coverage, DSC, debt coverage ratio, DCR |
| `debt_yield` | debt yield %, DY |
| `lender_irr` | yield, return, lender return, IRR, yield to maturity, all-in yield |
| `lender_multiple` | MOIC, money-on-money, multiple, cash-on-cash multiple |
| `equity_irr` | sponsor IRR, borrower return, equity return |
| `noi` | net operating income, net income, income (informal) |
| `cap_rate` | capitalization rate |
| `term_months` | loan term, term, duration, maturity |
| `maturity_date` | due date, balloon date, loan end date, scheduleEndDate |
| `closing_date` | origination date, funding date |
| `extension_options` | extension, extension option, loan extension |
| `as_is_value` | current value, appraised value, as-is appraisal |
| `as_stabilized_value` | stabilized value, ARV, after-repair value |
| `recourse` | personal guarantee, full recourse, non-recourse |
| `guarantor` | personal guarantor, carve-out guarantor |
| `interest_rate` | coupon, note rate, interest rate, rate, yield |
| `spread` | spread over index, margin |
| `index_rate` | base rate, benchmark, SOFR, Prime |
| `covenant` | test, financial covenant, maintenance covenant |
| `fundings` (Hypercore) | draw, advance, construction draw, disbursement |
| `equities` (Hypercore) | equity, preferred equity, mezz |
| `penalties` (Hypercore) | default interest, late charge, penalty interest, PIK default |

---

## 4. DD / Risk Taxonomy

Source: `CANONICAL_DD_FRAMEWORK_v3.0_COMPLETE.yaml` (231 items, version 3.0, updated 2025-08-15).

The PRISM skill references "252-item DD framework" in SKILL.md, but the canonical YAML on disk
counts **231 items** (the difference is likely an older reference or items removed during a refactor).

### 4.1 Category Index (31 categories, codes 00–30)

| Code | Category | Relevant to Hypercore-ask? |
|------|----------|--------------------------|
| 00 | OKOA Process Control | Partial (deal tracker, credit memo) |
| 01 | Entity & Organizational | Yes (borrower, guarantor, UBO) |
| 02 | Investment Strategy & Business Plan | Yes (thesis, exit) |
| **03** | **Financial Analysis & Documentation** | **High — statements, cash flows, debt schedule, financial model** |
| **04** | **Credit & Risk Analysis** | **High — DSCR, LTV, covenant testing, recovery, concentration** |
| 05 | Legal & Regulatory Compliance | Yes (title, UCC, environmental) |
| **06** | **Real Estate Property Analysis** | **High — appraisal, as-is/stabilized value, cap rate** |
| 07 | Real Estate Leasing & Tenants | Yes (rent roll, occupancy, NOI) |
| 08 | Real Estate Operations & Management | Moderate |
| **09** | **Real Estate Construction & Development** | **High — budget, draws, GC, completion guaranty** |
| 10–14 | Property Types (MF/Office/Retail/Industrial/Hospitality) | Property-type filters |
| 15 | Property Types — Specialized | Niche |
| 16 | Equipment & Machinery Assets | Non-RE only |
| 17 | Transportation Assets | Non-RE only |
| 18 | Intellectual Property Assets | Non-RE only |
| 19 | Art & Collectibles | Non-RE only |
| 20 | Revenue & Cash Flow Assets | Non-RE |
| 21 | Inventory & Supply Chain | Non-RE |
| 22 | Financial Assets & Securities | Non-RE |
| 23 | Company Stock & Equity Investments | Non-RE |
| **24** | **Specialized Deal Structures** | **High — mezzanine, pref equity, inter-creditor, C-PACE** |
| 25 | Insurance & Risk Management | Yes (GL, builder's risk, title) |
| **26** | **Valuation & Market Analysis** | **High — comp analysis, market absorption, cap rates** |
| 27 | ESG & Sustainability | Low for Hypercore-ask |
| 28 | Technology & Cybersecurity | Low |
| 29 | Transaction Documentation | Yes (loan docs, DOT, note) |
| 30 | Closing & Post-Closing | Yes (funding, post-close conditions) |

### 4.2 Deal Structure Taxonomy (PRISM/DD framework)

These deal structures are explicitly listed across all 231 DD items as applicability filters:

```
1st Lien | Other Senior/UCC | Subordinated | Mezzanine | Preferred Equity
Note Purchase | Construction Loan | LOC/Revolver | Revenue Loan | Royalties
Lease | Trade Finance | Common Equity | Options/Warrants | NAV Loan
Amortizing | C-PACE
```

### 4.3 Property/Asset Type Taxonomy (PRISM/DD framework)

```
Land | Residential | Multifamily | Single Family for Rent | Hospitality
Office | Retail | Healthcare/Medical Office | Storage | Data Center
Infrastructure | Power | Agriculture | Mixed Use | Equipment
Financial Assets | Art | Boats | Aircraft | Vehicles | IP
Receivables | Inventory | Company Stock | Revenue | Cash Flow
```

### 4.4 Key Sub-Dimensions within Credit & Risk Analysis (dd_codes 0401–0410)

| DD Code | Item | Hypercore relevance |
|---------|------|-------------------|
| 0401 | Credit History & Reports | Borrower/guarantor credit profile |
| **0402** | **Debt Service Coverage Analysis** | **DSCR — computable from Hypercore + NOI** |
| **0403** | **Loan-to-Value Assessment** | **LTV — computable from Hypercore + appraisal** |
| **0404** | **Covenant Structure & Testing** | **Covenant compliance monitoring** |
| 0405 | Security Interest Analysis | Lien priority, UCC, DOT |
| 0406 | Guarantee Analysis | Guarantor net worth |
| 0407 | Recovery Analysis & Scenarios | Liquidation value, workout |
| **0408** | **Concentration Risk Assessment** | **Geographic / sector concentration — portfolio roll-up** |
| 0409 | Portfolio Correlation Analysis | Multi-loan factor exposure |
| 0410 | Counterparty Risk Assessment | Lender / servicer exposure |

---

## 5. Directly Reusable Artifacts

### 5.1 Bridge-Loan Template — LIFT DIRECTLY
**Path:** `~/okoa-labs/okoa_ops/.claude/skills/prism-financial-modeler/templates/bridge-loan.yaml`

This is the highest-value artifact. It defines:
- All field names with types, formulas, defaults, and validation rules
- Named-range registry (Excel cell references for all key metrics)
- KG extraction targets (parties, properties, loans, covenants, claims)
- Covenant defaults that should become Hypercore-ask ontology defaults (LTV 75%, DSCR 1.25x, Debt Yield 8%)

**Recommendation:** Import the `sheets[*].sections[*].fields` structure and `covenants` block directly as the canonical field definitions for acos-hypercore-ask's metric ontology.

### 5.2 KG Extraction Schema — LIFT DIRECTLY
**Path:** `bridge-loan.yaml` → `kg_extraction` block

```yaml
kg_extraction:
  parties: [borrower, guarantor, lender]
  properties: [address, city, state, zip, apn, property_type]
  loans: [loan_amount, interest_rate, term_months, payment_type]
  covenants: [max_ltv, min_dscr, min_debt_yield]
  claims: [purchase_price, loan_amount, appraised_value, noi, lender_irr]
```

This maps precisely onto Hypercore entities and can be used as the extraction schema for financial figures the skill should know how to source.

### 5.3 Number Format Constants — LIFT AS REFERENCE
**Path:** `~/.../scripts/institutional_model.py`, class `InstitutionalModel`

```python
CURRENCY          = '$#,##0;($#,##0);"-"'
PERCENT           = '0.0%;(0.0%);"-"'
PERCENT_PRECISE   = '0.00%;(0.00%);"-"'
MULTIPLE          = '0.0"x";(0.0"x");"-"'
BASIS_POINTS      = '0 "bps";(0 "bps");"-"'
```

Useful for display-formatting rules in Hypercore-ask answer templates.

### 5.4 DD Category Codes (CCII system) — REFERENCE FOR DOCUMENT ROUTING
**Path:** `~/.../CANONICAL_DD_FRAMEWORK_v3.0_COMPLETE.yaml`

The CCII code system (Category Code + Item Code, e.g., "0402" = Credit & Risk Analysis, item 02 = DSCR Analysis) can serve as a document-type taxonomy for acos-hypercore-ask when routing questions that require underlying documents (e.g., "what's the DSCR?" → needs NOI from category 06/07 + loan terms from category 29).

### 5.5 Risk Severity Matrix — LIFT AS ANALYSIS RULE
**Path:** `prism-research/SKILL.md`, Output Format Standards

```
Severity = Likelihood × Impact  (both 1–5 scales)
High: 16–25 | Medium: 6–15 | Low: 1–5
```

Pair with covenant-breach flags for the analysis layer.

### 5.6 Confidence Tier System — LIFT AS EVIDENCE LABELING
**Path:** `prism-research/SKILL.md` + `prism-intelligence-v2-0.md`

| Tier | Rule |
|------|------|
| Verified | 3+ independent sources, full consistency |
| Probable | 2 sources, material consistency |
| Open | Single source or inference |

Map this onto Hypercore-ask answer confidence when figures come from single vs. multiple data sources (e.g., `outstanding` from Hypercore API = Verified; inferred payoff = Open).

### 5.7 Wall Street Formatting Conventions — ADOPT
**Path:** `prism-agent-config.yaml`, `wall_street_conventions`; `institutional_model.py`

- Blue = input, Black = formula, Red = negative, Green = cross-sheet link
- XNPV/XIRR for uneven cash flows (not NPV/IRR)
- 6 decimal places for calculations
- No hard-coded numbers in formulas

These should be the presentation/calculation conventions for any Hypercore-ask output that surfaces modeled figures.

---

## OKOA-Proprietary vs. Generic Finance

| Item | Status |
|------|--------|
| LTV 75% max covenant | **OKOA default** (generic market range is 65–80%) |
| DSCR 1.25x minimum | Generic market standard (same as OKOA) |
| Debt Yield 8% minimum | OKOA default (market range 7–10%) |
| Origination fee 2% | OKOA default |
| Exit fee 1% | OKOA default |
| Extension fee 0.5%/option | OKOA default |
| Interest rate 8–20% validation range | OKOA/private credit range (generic) |
| Interest reserve 12 months default | OKOA default (market 6–18 months) |
| Payment type "Interest-Only" as default | OKOA product preference |
| 252 vs. 231 DD items | OKOA proprietary (231 in current YAML) |
| CCII code system | OKOA proprietary document taxonomy |
| "Wolfgramm format" for master synthdoc | OKOA-internal document format |
| Evidence tiers (Verified/Probable/Open) | PRISM convention, generic finance adapts 3-source rule |

## Hypercore Field Mapping Summary

| Hypercore field | PRISM equivalent | Notes |
|----------------|-----------------|-------|
| `outstanding` | `beginning_balance` / `ending_balance` | Current UPB |
| `totalDue` | `loan_payoff` (approx) | Includes exit fee; may also include accrued interest |
| `penalties` | Default/penalty interest accrual | PRISM models separately post-default |
| `commitment` | `loan_amount` / `senior_loan` | Face amount |
| `interest` | `interest_accrued` | Monthly: `outstanding × rate / 12` |
| `maturity` / `scheduleEndDate` | `maturity_date` | `closing_date + term_months/12` |
| `fundings` | Draw schedule / `renovation_budget` draws | Construction/holdback releases |
| `equities` | `mezzanine` / preferred equity layers | Subordinated capital |
| `clients` | `borrower` + `guarantor` (KG: PARTY node) | Entity roster |
| *(not in Hypercore)* | `noi` | Must be sourced externally for DSCR/DY |
| *(not in Hypercore)* | `appraised_value` / `as_is_value` | Must come from appraisal docs for LTV |
| *(not in Hypercore)* | `exit_cap_rate` | Market / underwriting assumption |

**Key insight:** Hypercore holds the liability side (balance, payments, maturity, fees) but NOT the property/income side (NOI, value). Any analysis metric that requires property data (LTV, DSCR, Debt Yield, cap rate) needs a second data source — appraisals from the DD document pipeline or the KG.
