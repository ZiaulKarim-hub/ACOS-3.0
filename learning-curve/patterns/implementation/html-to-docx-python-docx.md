# Learning: Styled HTML-to-DOCX via python-docx (Not Pandoc)

**ID:** LEARN-IMPL-002
**Extracted From:** EPIC-001 (Loan Document Generator V2), Story 1
**Date:** 2026-04-10
**Category:** pattern
**Subcategory:** implementation
**Domain:** general
**Confidence:** high
**Applications:** 1

## Context

When generating institutional-quality Word documents (.docx) from HTML source.
The naive approach (pandoc CLI) produces structurally correct but visually plain
output that loses CSS styling, custom fonts, table formatting, and color conventions.
For documents going to credit committees and counterparties, plain pandoc output is
not acceptable.

## The Learning

Use a custom `html-to-docx.py` script built on python-docx to convert HTML to DOCX
with full styling preservation. Pandoc should only be used as an emergency fallback.
The canonical document source is HTML+CSS; both PDF (via Puppeteer) and DOCX (via
python-docx) are derived from this same canonical source.

## Pattern Description

### Problem

The initial DOCX output pipeline used pandoc for HTML→DOCX conversion. The output
documents:
- Lost all CSS-defined colors and backgrounds
- Dropped custom font definitions (fell back to Times New Roman)
- Lost table border styles and cell shading
- Broke page break rules defined in CSS
- Produced inconsistent heading styles

The PDF output (via Puppeteer) looked correct. The DOCX looked like a plain text
document. For institutional loan documents, this inconsistency was unacceptable.

### Solution

Build `html-to-docx.py` (6.7KB) using python-docx library. The script:
1. Parses HTML with BeautifulSoup
2. Maps CSS selectors to python-docx style attributes
3. Applies institutional color conventions (#455D52 sage green, etc.) as ARGB values
4. Preserves table structure with cell-level formatting
5. Sets consistent heading styles to match the PDF design
6. Generates both DOCX and (via Puppeteer) PDF from the same HTML source

pandoc remains as a documented fallback only — never the primary pipeline.

### Structure

```
Phase 3 Assembler
    │
    ▼
canonical-output.html  (same file for both outputs)
    │
    ├─► Puppeteer html-to-pdf.js ──────────────────► output.pdf
    │
    └─► python-docx html-to-docx.py ──────────────► output.docx
                      (maps CSS → docx styles)
```

### Benefits

- Single canonical HTML source for both output formats (no drift)
- Full styling fidelity in DOCX (fonts, colors, tables preserved)
- python-docx gives programmatic control not available in pandoc CLI
- Custom ARGB color values can be mapped directly from CSS hex values

### Trade-offs

- python-docx requires pip install (dependency management needed)
- Mapping CSS to python-docx styles requires maintenance when CSS changes
- Complex CSS features (flexbox, grid) have no DOCX equivalent — must simplify layout
- CSS @media print rules don't transfer (DOCX has no print-media concept)

## Evidence

### Project: EPIC-001 — Loan Document Generator V2

**Context:** Story 1 (DOCX + PDF Output Pipeline) required institutional-quality DOCX
output. Initial pandoc implementation failed quality review. MEMORY.md explicitly
records: "DOCX must match PDF styling; never use plain pandoc for DOCX
(use python-docx html-to-docx.py)" as a persistent feedback item.

**Applied:** `html-to-docx.py` created at `.claude/scripts/html-to-docx.py` (6.7KB).
Phase 3 assembler and Phase 4 validator both updated to use python-docx pipeline.
Pandoc flagged as fallback-only in SKILL.md.

**Outcome:** DOCX output quality matched PDF quality. The requirement entered MEMORY.md
as a persistent rule (feedback_docx_quality.md) to prevent regression in future sessions.

## Application Guide

### When to Use

- Any pipeline that generates DOCX from HTML source
- Institutional documents where visual formatting matters (not just content)
- When DOCX and PDF must look identical (same canonical source approach)

### When NOT to Use

- DOCX quality doesn't matter (internal notes, drafts)
- Target is plain text DOCX with no special formatting
- Environment cannot install python-docx (e.g., locked-down CI)

### Implementation Steps

1. Define the CSS-to-style mapping table for your design system
2. Create `html-to-docx.py` that parses HTML and applies mapped styles
3. Ensure both html-to-pdf.js and html-to-docx.py read the same HTML file
4. Add python-docx to requirements.txt or document the dependency
5. Add STRUCT-check in Phase 4 to validate DOCX output (not just PDF)
6. Never expose intermediate .html in output/ directory to users

### Common Mistakes

- Using pandoc for styled output (loses CSS → always falls back to defaults)
- Generating HTML differently for PDF vs DOCX (causes format drift)
- Not documenting python-docx dependency (breaks silently in new environments)
- Exposing intermediate .html files in the user-facing output directory

## Related Learnings

- LEARN-ANTI-002 — Pandoc as Primary DOCX Pipeline
- LEARN-IMPL-001 — XLSX Cell-Level Extraction with Formula Provenance

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
