---
name: deep-research
description: Structured deep research methodology with multi-source verification, cross-reference analysis, conflict identification, and executive summary generation. For complex research tasks requiring forensic-level rigor.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, WebSearch, WebFetch
---

# Deep Research Skill

## Purpose

Conduct rigorous, multi-source research on complex topics. Goes beyond surface-level search by applying a structured verification framework: triangulate claims across sources, assign confidence levels, identify conflicts between sources, and produce decision-ready analysis with complete audit trails.

## When to Use

- Research requiring forensic-level verification (not just "find an answer")
- Complex topics where multiple sources may conflict
- Decision-support research (evaluating options with evidence)
- Market research, competitive analysis, regulatory research
- Any research where confidence levels and source quality matter
- Pre-decision analysis where stakeholders need verified data

**Use `/technology-research` instead for:** library/framework comparison, tooling evaluation, simple tech stack decisions.

## Skill Protocol

### Phase 1: Define Research Scope

1. Clarify the research question (restate it precisely)
2. Identify what "answer" looks like (metrics, comparisons, recommendations, risk assessment)
3. Determine required evidence quality:
   - **Maximum**: 3+ independent sources for all material claims (regulatory, financial, high-stakes)
   - **Standard**: 2+ sources for key claims, single source acceptable for supporting details
   - **Exploratory**: Single sources acceptable, focus on breadth over depth
4. Set scope boundaries (what's in, what's explicitly out)
5. Identify source tiers:
   - **Tier 1 -- Authoritative**: Official documentation, regulatory filings, academic papers, primary sources
   - **Tier 2 -- Expert**: Industry reports, analyst research, expert commentary, technical specifications
   - **Tier 3 -- Empirical**: Benchmarks, case studies, real-world implementations, user reports
   - **Tier 4 -- Community**: Forums, blog posts, social media, anecdotal evidence

### Phase 2: Information Gathering

1. **Internal research** -- Search the project's own files, documentation, and codebase using Read, Glob, Grep
2. **External research** -- Use WebSearch and WebFetch to find authoritative sources
3. For each source found:
   - Record full citation (title, author, URL, access date)
   - Classify into source tier
   - Extract relevant data points with exact values
   - Note any caveats or limitations of the source
4. Document all sources in a structured bibliography

### Phase 3: Cross-Verification & Conflict Analysis

For each material claim:

1. **Triangulate** -- find the same fact in 2-3 independent sources
2. **Label confidence**:
   - **Verified**: 3+ independent sources, full consistency -- state as fact
   - **Probable**: 2 sources, material consistency -- state with "likely" qualifier
   - **Open**: Single source or inference -- state with "preliminary" qualifier
3. **Identify conflicts** -- where sources disagree:
   ```
   | Data Point | Source A | Source B | Source C | Assessment |
   |------------|----------|----------|----------|------------|
   | [Metric]   | [Value]  | [Value]  | [Value]  | [Reasoning]|
   ```
4. **DO NOT harmonize conflicts** -- preserve disagreements, they are valuable information
5. For each conflict, assess: different data? different methodology? different timeframe? outdated source?

### Phase 4: Analysis & Pattern Recognition

1. Identify patterns across findings (trends, correlations, anomalies)
2. Perform quantitative analysis where data permits (statistics, trend lines, comparisons)
3. Risk assessment:
   ```
   | Risk | Likelihood | Impact | Severity | Mitigation |
   |------|------------|--------|----------|------------|
   | [Risk] | [H/M/L] | [H/M/L] | [Score] | [Strategy] |
   ```
   Severity = Likelihood score (1-5) x Impact score (1-5), rated: High (16-25), Medium (6-15), Low (1-5)
4. Scenario analysis for key variables where applicable

### Phase 5: Synthesis & Recommendations

Generate a comprehensive research report:

```markdown
# Deep Research Report: [Topic]

**Date:** [YYYY-MM-DD]
**Evidence Quality:** [Maximum|Standard|Exploratory]

---

## Executive Summary
[2-3 paragraphs: key findings, critical risks, recommendations]

---

## Key Findings

### Finding 1: [Title]
- **Confidence Level:** [Verified|Probable|Open]
- **Data:** [Precise value with units]
- **Sources:**
  1. [Tier 1 citation]
  2. [Tier 2 citation]
- **Analysis:** [Interpretation]

### Finding 2: [Title]
[Same structure]

---

## Cross-Reference Analysis

### Source Conflicts
| Data Point | Source A | Source B | Assessment |
|------------|----------|----------|------------|
| [Metric]   | [Value]  | [Value]  | [Resolution] |

### Data Quality Assessment
- **High Quality:** [Sources with complete, verifiable data]
- **Medium Quality:** [Sources with partial data]
- **Low Quality:** [Sources requiring additional validation]

---

## Risk Assessment
[Risk matrix table]

---

## Recommendations

### Tier 1: High Confidence (Multi-Source Agreement)
1. [Recommendation -- supported by 3+ sources]

### Tier 2: Medium Confidence (Some Conflict)
1. [Recommendation -- with noted caveats]

### Tier 3: Requires Further Investigation
1. [Area where data is insufficient]

---

## Methodology & Limitations
[Research approach, tools used, scope limitations, assumptions]

---

## Sources
### Tier 1 -- Authoritative
1. [Full citation with URL]

### Tier 2 -- Expert
1. [Full citation]

### Tier 3 -- Empirical
1. [Full citation]

---

## Audit Trail
**Research Conducted:** [Timestamp]
**Verification Standard:** [Maximum|Standard|Exploratory]
```

## Key Principles

### Verification Over Speed
- Never rely on a single source for material claims
- Always label confidence levels explicitly
- Quantify where possible -- convert qualitative to quantitative

### Conflict Preservation
- Disagreements between sources are informative, not errors
- Present all perspectives in conflicts
- Let the reader/decision-maker weigh the evidence

### Complete Audit Trail
- Every claim traceable to a source
- Every source categorized by tier
- Every limitation documented

### Data Integrity
- 100% accuracy for numerical transcription
- No fabrication -- use "Data not available" for gaps
- Exact citations with access dates for all web sources

---

*Deep Research Skill -- Verify, cross-reference, decide with confidence.*
