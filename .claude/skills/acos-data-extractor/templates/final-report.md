# Data Extraction Report

**Session:** {session-id}
**Date:** YYYY-MM-DD HH:MM
**Source Directories:** [list of folder paths]
**Schema:** [field count] fields ([multi count] multi-value)
**QA Iterations:** N (triage: X, extraction: Y)
**Final Verdict:** PASS | PASS WITH WARNINGS | ESCALATED

---

## Executive Summary

- **Files Scanned:** [total] across [N] directories
- **Files Triaged for Deep Read:** [count] ([percentage]% of corpus)
- **Files Contributing Data:** [count]
- **Fields Found:** [X]/[Y] ([percentage]%)
- **Fields Not Found:** [count]
- **Conflicts Resolved:** [count]
- **Unresolved Conflicts:** [count]

---

## Results at a Glance

<!-- One row per schema field. Sort: FOUND first, then CONFLICT, then NOT_FOUND. -->
<!-- For multi-value fields, show entry count in Value column instead of raw value. -->
<!-- Confidence: percentage 0–100%. NOT_FOUND fields show — -->
<!-- Source File = the document name. Location = page/sheet/section where the value was found. -->

| Field | Value | Confidence | Status | Source File | Location |
|-------|-------|------------|--------|-------------|----------|
| [Field Name] | [extracted value] | 95% | FOUND | [filename] | Page [N], "[section]" |
| [Field Name] | [extracted value] | 75% | FOUND | [filename] | Page [N], "[section]" |
| [Field Name] | [N entries → see below] | 90% | FOUND | [filename] | [sheet/rows summary] |
| [Field Name] | [value] | 70% | CONFLICT ⚠ | [filename] (resolved) | Page [N], "[section]" |
| [Field Name] | — | — | NOT FOUND | — | ([N] files searched) |

**Confidence:** 90–100% = exact match, unambiguous source · 60–89% = requires interpretation · below 60% = ambiguous or partial

---

## Extracted Data

<!-- Repeat this section for each single-value field -->

### [Field Name] — [STATUS: FOUND | NOT_FOUND | CONFLICT]

**Field ID:** [field_id]
**Type:** [field_type]
**Value:** [exact extracted value]
**Confidence:** [0–100%]
**Source File:** [filename], page [N], section "[section name]"
**Quote:** "[verbatim quote from source document]"

<!-- For corroborated values -->
**Corroboration:** Also found in [filename2] (page [N]) — values match.

---

<!-- For multi-value fields -->

### [Field Name] — [STATUS: FOUND | PARTIAL | NOT_FOUND]

**Field ID:** [field_id]
**Type:** [field_type]
**Entries Found:** [count]

| # | Value | Date | Source File | Location | Confidence (%) |
|---|-------|------|-------------|----------|----------------|
| 1 | [value] | [date] | [filename] | Page [N], "[section]" or Sheet/Row | [0–100%] |
| 2 | [value] | [date] | [filename] | Page [N], "[section]" or Sheet/Row | [0–100%] |
| ... | ... | ... | ... | ... | ... |

<!-- If PARTIAL -->
**Completeness Note:** [what appears to be missing]

---

<!-- For NOT_FOUND fields -->

### [Field Name] — NOT_FOUND

**Field ID:** [field_id]
**Type:** [field_type]
**Status:** Not found in any source document
**Documents Searched:** [count] files deeply read, [total] files triaged
**Search Notes:** [what was searched, why it wasn't found]
**Recommendation:** [where this data might typically be found]

---

<!-- For UNRESOLVED_CONFLICT fields -->

### [Field Name] — UNRESOLVED CONFLICT

**Field ID:** [field_id]
**Type:** [field_type]
**Conflicting Values:**

| Value | Source File | Location | Date of Document |
|-------|-------------|----------|-----------------|
| [value1] | [filename1] | Page [N], "[section]" | [doc date] |
| [value2] | [filename2] | Page [N], "[section]" | [doc date] |

**Resolution Attempted:** [recency | authority | specificity]
**Why Unresolved:** [explanation]
**Recommendation:** [which value to use and why, or request for user decision]

---

## QA Review Summary

### Triage QA (Phase 1)
- Iterations: [N]/3
- SKIP files sampled: [count]
- Misclassified files found: [count]
- Final verdict: PASS | FAIL

### Extraction QA (Phase 2)
- Wigum iterations: [N]/5
- Value verification: [verified]/[total] checked
- Completeness audit: [N] NOT_FOUND fields verified
- Provenance audit: [N]% of citations spot-checked
- Final verdict: PASS | FAIL

### Remaining Flags
<!-- If any flags remain after max iterations -->

| Field | Issue | QA Agent | Recommendation |
|-------|-------|----------|----------------|
| [field] | [issue] | [agent] | [recommendation] |

---

## Corpus Analysis

### Source Directory Breakdown

| Directory | Files | PDF | DOCX | XLSX | TXT | Other |
|-----------|-------|-----|------|------|-----|-------|
| [path1] | [N] | [n] | [n] | [n] | [n] | [n] |
| [path2] | [N] | [n] | [n] | [n] | [n] | [n] |
| **Total** | **[N]** | **[n]** | **[n]** | **[n]** | **[n]** | **[n]** |

### Triage Distribution

| Classification | Count | Percentage |
|---------------|-------|------------|
| RELEVANT | [N] | [%] |
| MAYBE | [N] | [%] |
| SKIP | [N] | [%] |

---

## Appendix: Full File Inventory

<!-- Table of ALL files with their triage classification and contribution status -->

| File | Directory | Type | Triage | Fields Contributed |
|------|-----------|------|--------|--------------------|
| [filename] | [dir] | PDF | RELEVANT | origination_date, property_address |
| [filename] | [dir] | XLSX | RELEVANT | investor_payments |
| [filename] | [dir] | PDF | SKIP | — |
| ... | ... | ... | ... | ... |

---

*Generated by ACOS Data Extractor — Schema-driven extraction with adversarial QA.*
