# Anti-Pattern: Using Pandoc as Primary Pipeline for Styled DOCX Output

**ID:** LEARN-ANTI-002
**Extracted From:** EPIC-001 (Loan Document Generator V2), Story 1
**Date:** 2026-04-10
**Category:** anti-pattern
**Subcategory:** failed-approaches
**Domain:** general
**Confidence:** high
**Occurrences:** 1

## Context

When building a document generation pipeline that needs to produce institutional-quality
Word (.docx) output from HTML source. Pandoc is the most commonly suggested tool
for HTML→DOCX conversion.

## The Anti-Pattern

Using the `pandoc` CLI as the primary HTML→DOCX converter for documents that have
custom CSS styling (colors, fonts, table borders, section backgrounds, page layout).

## Why It's Wrong

Pandoc performs structural conversion: it converts HTML heading tags to Word heading
styles, paragraphs to Word paragraphs, tables to Word tables. But it does not convert
CSS styling. Custom colors, font-family definitions, border widths, background colors,
and padding from CSS are all silently dropped. The output is structurally correct
but visually blank.

### Consequences

- Generated DOCX looks like a plain text document despite the PDF looking perfect
- CSS color conventions (#455D52 sage green, institutional navy, etc.) are lost
- Custom fonts fall back to Times New Roman or document default
- Table formatting (colored header rows, alternating row shading) is stripped
- For institutional loan documents sent to counterparties, this is a credibility failure

### Root Causes

- Pandoc is well-known and frequently recommended as "the tool for format conversion"
- It works well for simple documents (plain text, basic tables, headers)
- Developers test with simple inputs that happen to work, miss the styling failures
- CSS styling is a fundamentally different layer from HTML structure — pandoc does structure, not style

## Evidence

### Incident: EPIC-001 Story 1 (SLICE-S1-002)

**What Happened:**
The initial DOCX pipeline used pandoc with a reference-doc.docx template. The
reference doc was supposed to carry the institutional styling. In practice, pandoc
did not consistently apply the reference doc styles — it produced output that
looked like stripped plain text.

**Impact:**
DOCX output was visually unacceptable for institutional use. The user's persistent
feedback (recorded in MEMORY.md as feedback_docx_quality.md) explicitly states:
"DOCX must match PDF styling; never use plain pandoc for DOCX."

**How Discovered:**
Direct user feedback after reviewing the generated DOCX vs PDF for the same document.
The difference was immediately visible.

**Fix Applied:**
Replaced pandoc with `html-to-docx.py` built on python-docx. Pandoc demoted to
emergency fallback only. See LEARN-IMPL-002 for the correct approach.

## The Correct Approach

### Do This Instead

Build a custom `html-to-docx.py` using the python-docx library that explicitly maps
CSS style attributes to python-docx formatting API calls. This preserves:
- Custom colors (CSS hex → python-docx ARGB)
- Font families (CSS font-family → python-docx font.name)
- Table formatting (CSS border, background-color → python-docx table cell formatting)
- Section backgrounds and heading styles

### Why It Works

python-docx provides programmatic access to all DOCX formatting attributes. Unlike
pandoc (which maps HTML structure to DOCX structure), python-docx lets you set
individual formatting properties explicitly, giving the same control as CSS but in
the DOCX domain.

### Example

**Wrong:**
```bash
# pandoc drops all CSS styling silently
pandoc output.html -o output.docx --reference-doc=reference.docx
```

**Right:**
```python
# python-docx applies styling explicitly
from docx import Document
from docx.shared import RGBColor

doc = Document()
heading = doc.add_heading("Section Title", level=1)
heading.runs[0].font.color.rgb = RGBColor(0x45, 0x5D, 0x52)  # #455D52 sage green
heading.runs[0].font.name = "Georgia"
```

## Prevention Guide

### Warning Signs

- A document generation pipeline uses pandoc for anything that has CSS styling
- DOCX output is described as "looks different from the PDF"
- Generated DOCX has Times New Roman where custom fonts were specified

### Prevention Checklist

- [ ] If the document has custom CSS: use python-docx, not pandoc
- [ ] Test DOCX output visually against PDF before declaring "done"
- [ ] Document python-docx as a required dependency in requirements.txt
- [ ] If using pandoc as fallback, log a WARNING when fallback is triggered

### Review Focus

For reviewers — look for:
- Any `pandoc` call in a pipeline that generates institutional documents
- DOCX generation that doesn't use python-docx or equivalent
- Missing visual validation step for DOCX output

## Related Anti-Patterns

- LEARN-ANTI-001 — Missing Data Contract Between Pipeline Stages

## Related Correct Patterns

- LEARN-IMPL-002 — HTML-to-DOCX via python-docx (not pandoc)

## Occurrence History

| Date | Project | Caught By | Severity |
|------|---------|-----------|----------|
| 2026-03-16 | EPIC-001 Story 1 | User feedback (direct) | HIGH |

---

*Documented to prevent recurrence - ACOS Learning Curve Agent*
