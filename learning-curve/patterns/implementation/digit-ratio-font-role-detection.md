# Learning: Digit-Ratio Heuristic for Font Role Detection in PPTX

**ID:** LEARN-IMPL-003
**Extracted From:** EPIC-001 (Loan Document Generator V2), PPTX pipeline
**Date:** 2026-04-10
**Category:** pattern
**Subcategory:** implementation
**Domain:** general
**Confidence:** high
**Applications:** 1

## Context

When programmatically generating or validating PPTX files and needing to distinguish
"data/number" text runs from "label/header" text runs to apply different formatting
rules (e.g., monospace fonts for numbers, serif fonts for headers).

## The Learning

Classify text runs by the ratio of digit characters to total characters, not by a simple
`contains-digit` check. A text run is a "data run" if its digit ratio exceeds a threshold
(e.g., ≥0.5). This correctly handles mixed strings like "Q3 2025 Revenue" (label) vs
"$83,400,000" (data).

## Pattern Description

### Problem

The initial PPTX font role detection used `str.contains_digit()` logic: if any digit
appears in a text run, treat it as a data/number run. This caused widespread
misclassification:
- "Q3 2025 Revenue" → classified as data run (wrong: it's a label)
- "72% LTV (appraisal basis)" → classified as data run (partially wrong: it's a label with a metric)
- "$83,400,000" → correctly classified as data run

The naive heuristic applied monospace/data formatting to header and label text,
breaking the visual design of generated slides.

### Solution

Calculate `digit_ratio = count(digit chars) / len(text_run)`. Apply a threshold
(default: 0.5) to classify runs:
- `digit_ratio >= 0.5` → data run (apply data font, e.g., Calibri monospace-weight)
- `digit_ratio < 0.5` → label/header run (apply label font, e.g., Georgia)

Edge cases:
- Empty strings: treat as label
- Strings with only punctuation/symbols (`$`, `%`, `,`): treat as label unless accompanied by digits
- Currency strings: `$83,400,000` has `digit_ratio = 8/13 = 0.62` → correctly classified as data

### Benefits

- Eliminates misclassification of "Q3 2025" style labels as data runs
- Handles financial notation correctly ($, %, commas in numbers)
- Simple, deterministic, and debuggable
- No ML or NLP required — pure string math

### Trade-offs

- Threshold (0.5) may need tuning for specific document conventions
- Very short strings (1-3 chars) can be misclassified regardless of ratio
- Does not distinguish "42%" (metric) from "Revenue ($M)" (label with symbol)

## Evidence

### Project: EPIC-001 — Loan Document Generator V2

**Context:** `data-to-pptx.py` (1049 lines) generated PPTX slides from loan data.
The initial `contains-digit` check was misclassifying header text, causing Georgia
headers to be rendered in Calibri data-font style (incorrect per design system).

**Applied:** Commit `4b40471` rewrote the font role detection to use the digit-ratio
heuristic. The commit message explicitly states: "Rewrite PPTX font role detection —
digit-ratio heuristic, not contains-digit check." The 2026-03-30 handoff confirms
this was a targeted fix.

**Outcome:** Font role detection accuracy improved. The fix was part of the round-1
remediation that closed 7 PPTX-specific defects alongside the 56 swarm review findings.

## Application Guide

### When to Use

- Any PPTX/DOCX generation pipeline that needs to classify text runs by type
- When applying different fonts, sizes, or colors to "data" vs "label" text
- When building a validation script that checks formatting compliance

### When NOT to Use

- Text runs are explicitly tagged with roles in the data model (use tags instead)
- All text in the document type uses the same font (no classification needed)
- Very specialized formats where domain-specific classification rules are better

### Implementation Steps

```python
def classify_text_run(text: str, threshold: float = 0.5) -> str:
    if not text or not text.strip():
        return "label"
    digit_count = sum(1 for c in text if c.isdigit())
    ratio = digit_count / len(text)
    return "data" if ratio >= threshold else "label"
```

### Common Mistakes

- Using `any(c.isdigit() for c in text)` → misclassifies any label with a year
- Using `text.isnumeric()` → fails on currency strings with symbols
- Forgetting to handle empty strings (ZeroDivisionError)

## Related Learnings

- LEARN-ARCH-001 — Delegated Phase Orchestration
- LEARN-ANTI-003 — Naive Contains-Digit Check for Text Classification

## Success Rate

- Applied: 1 time
- Successful: 1 time
- Success Rate: 100%

## Update History

| Date | Update | By |
|------|--------|-----|
| 2026-04-10 | Initial creation | Learning Curve Agent |

---

*Extracted by ACOS Learning Curve Agent*
