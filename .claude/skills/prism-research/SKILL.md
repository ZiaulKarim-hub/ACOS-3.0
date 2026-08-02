---
name: prism-research
description: Institutional-grade financial and strategic research using PRISM Intelligence methodology. Produces forensic-level analysis with executive dashboards, risk matrices, and IC-ready outputs. Finance and private equity domain only.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, WebSearch, WebFetch
---

# PRISM Research Skill

## Purpose

Conduct institutional-grade financial and strategic research using the PRISM (Pattern Recognition Intelligence & Strategic Mastery) methodology. Produces decision-ready analyses for investment committees, regulatory filings, and strategic planning with forensic verification standards and complete audit trails.

**This is a domain-specific skill for finance and private equity research. For general research, use `/acos-deep-research` instead.**

## When to Use

Apply this skill when:
- Institutional-grade financial analysis (market research, comps, valuations)
- Investment committee preparation (IC memos, deal analysis)
- Private equity / private credit research
- Real estate market analysis and deal evaluation
- Regulatory compliance research for financial products
- Capital markets research (debt, equity, structured products)
- Risk assessment for investment decisions

**Do NOT use for:** general software research, technology evaluation, non-financial research topics. Use `/acos-deep-research` or `/technology-research` instead.

## PRISM Operational Standards

- **Verification Intensity:** Maximum -- minimum 3 independent sources for material claims
- **Analytical Depth:** Forensic
- **Calculation Tolerance:** 0.000001 (6 decimal precision)
- **Source Minimum:** 3 independent sources
- **Tone:** Formal, institutional-grade
- **Zero fabrication tolerance** -- only report verified information

## Confidence Levels

- **Verified:** 3+ independent sources with full consistency -- state as established fact
- **Probable:** 2 sources with material consistency -- state with "likely" qualifier
- **Open:** Single source or inference -- state as preliminary, flag for further verification

## Skill Protocol

### Phase 1: Research Scoping

1. Parse `$ARGUMENTS` for the research topic
2. Identify the financial domain: private credit, private equity, real estate, capital markets, structured products, etc.
3. Determine output requirements: executive dashboard, full report, risk matrix, or combination
4. Identify target audience: IC presentation, LP reporting, regulatory filing, internal strategy

### Phase 2: Information Gathering

**Internal research:**
- Search project files for relevant deal data, synthdocs, financial models
- Review knowledge graph (if exists) for related entities and historical data
- Check for existing analysis or reports on the topic

**External research:**
- Web search for authoritative financial sources:
  - Regulatory filings (SEC EDGAR, state filings)
  - Industry reports (CBRE, JLL, CoStar for real estate; PitchBook, Preqin for PE)
  - Market data (FRED, BLS, Census for macro; specific exchanges for securities)
  - Academic and trade publications
- For each source: record full citation, classify tier, extract exact figures

### Phase 3: Cross-Verification

Apply maximum verification intensity:

1. Triangulate all material financial claims using 3+ sources
2. Normalize units: currencies to USD at spot rates, dates to ISO 8601, percentages to decimal form
3. Handle conflicts: present both perspectives with preferred interpretation and supporting rationale
4. Flag data freshness -- mark any data >30 days old for fast-moving markets

### Phase 4: Analysis

**Quantitative Analysis:**
- Statistical summary (mean, median, standard deviation, range, trend)
- Time series analysis for trends
- Comparative analysis (benchmarking against relevant comps)
- Sensitivity analysis on key variables

**Risk Assessment:**
```
Severity = Likelihood (1-5) x Impact (1-5)
High: 16-25 | Medium: 6-15 | Low: 1-5
```

**Financial Metrics:**
- All calculations to 6 decimal precision
- IRR/NPV using XNPV/XIRR for uneven cash flows
- Standard growth: (New/Old)^(1/n)-1
- No hard-coded assumptions -- all inputs documented

### Phase 5: Output Generation

#### Executive Dashboard (YAML)

```yaml
executive_summary:
  topic: "[Research topic]"
  date: "[YYYY-MM-DD]"
  analyst: "PRISM Intelligence"

  key_findings:
    - finding: "[Finding]"
      confidence: "[Verified|Probable|Open]"
      evidence: "[Citations]"

  critical_metrics:
    - metric: "[Name]"
      value: "[Precise value]"
      unit: "[Unit]"
      source: "[Citation]"

  risk_assessment:
    high_risks:
      - risk: "[Description]"
        likelihood: "[H/M/L]"
        impact: "[Quantified]"
        mitigation: "[Strategy]"
```

#### Detailed Research Report (Markdown)

```markdown
# PRISM Intelligence Research Report
## [Topic]

**Date:** [YYYY-MM-DD]
**Classification:** Institutional Research
**Verification Standard:** Maximum (3+ sources, 6-decimal precision)

---

## Executive Summary
[Key findings, risks, recommendations]

## Research Findings
### Section 1: [Area]
#### Finding 1.1
- **Confidence:** [Verified|Probable|Open]
- **Data:** [Precise value with units]
- **Sources:** [Tier 1/2/3 citations]
- **Analysis:** [Interpretation]

## Cross-Reference Analysis
### Conflicts Identified
| Data Point | Source A | Source B | PRISM Assessment |
|------------|----------|----------|------------------|

## Risk Assessment Matrix
| Risk | Likelihood | Impact | Severity | Mitigation |
|------|------------|--------|----------|------------|

## Quantitative Analysis
[Statistical summaries, trend analysis, comparisons]

## Recommendations
### Immediate Actions
### Strategic Considerations
### Further Research Required

## Sources
### Tier 1 -- Authoritative
### Tier 2 -- Expert
### Tier 3 -- Empirical

## Audit Trail
```

## Common Use Cases

**Market Research:**
```
/prism-research "Multifamily cap rates in western US markets Q1 2026"
```

**Competitive Analysis:**
```
/prism-research "Private credit lenders in bridge loan space"
```

**Investment Thesis:**
```
/prism-research "Student housing demand drivers near major universities"
```

**Risk Assessment:**
```
/prism-research "Construction cost inflation impact on development feasibility"
```

## Integration with Other Skills

- Use with `/acos-deep-research` for non-financial aspects of the same topic
- Use with `/document-synthesis` to process source documents first
- Use with `/knowledge-graph` to build entity relationships from findings

---

*PRISM Research Skill -- Institutional-grade intelligence for alternative investments.*
