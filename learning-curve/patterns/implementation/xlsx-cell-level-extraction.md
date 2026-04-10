# Learning: XLSX Cell-Level Extraction with Formula Provenance

**ID:** LEARN-IMPL-001
**Extracted From:** EPIC-001 (Loan Document Generator V2), Story 4
**Date:** 2026-04-10
**Category:** pattern
**Subcategory:** implementation
**Domain:** general
**Confidence:** high
**Applications:** 1

## Context

When AI agents need to extract precise numerical data from Excel spreadsheets for use
in financial documents. The default approach — asking agents to Read the .xlsx binary
file — is unreliable. Agents cannot read binary formats directly and frequently
hallucinate or misread cell values.

## The Learning

Pre-process all .xlsx files through a dedicated Python parser (xlsx-extract.py) before
any agent touches the data. The parser outputs structured YAML with cell addresses,
values, formulas, and named ranges. Agents receive clean YAML, not binary files.
This is an architecturally-enforced accuracy guarantee, not a best-effort suggestion.

## Pattern Description

### Problem

Phase 2 analyzer agents were being told to "read the XLSX files" in the loan folder.
Claude cannot read .xlsx binary format. Agents either: (a) failed silently and invented
plausible-looking numbers, (b) read only the first few visible bytes and misinterpreted
them, or (c) skipped the file entirely. For a PE real estate lender, fabricated financial
figures are a credibility-destroying failure mode.

### Solution

Add an XLSX pre-processing step (Step 2.1b) before analyzer agents are spawned.
`xlsx-extract.py` runs on every .xlsx/.xlsm file found in the loan folder and outputs:
- Cell addresses with values (numbers, strings, booleans)
- Formula strings where formulas exist
- Named range definitions
- Structured table boundaries
- Sheet names and visible/hidden status

Agents receive `{filename}-extracted.yaml` instead of the raw .xlsx.

### Benefits

- Eliminates hallucinated financial figures (the most severe failure mode)
- Enables formula provenance: calculated values show their input cells
- Supports cross-validation: same figure appearing in multiple XLSX files
  can be compared programmatically
- Cell-level addresses become clickable provenance links in verification tables

### Trade-offs

- Adds ~2-5 seconds per XLSX file for extraction
- xlsx-extract.py requires openpyxl or similar dependency
- Merged cells require special handling (value attributed to top-left cell only)
- Very large spreadsheets (10k+ rows) may produce large YAML files

## Evidence

### Project: EPIC-001 — Loan Document Generator V2

**Context:** Initial loan doc generator (pre-EPIC-001) had agents "reading" XLSX files
for financial data. The 2026-03-16 session identified this as a reliability gap.
Story 4 (SLICE-S4-001 through S4-003) formalized the fix.

**Applied:** `.claude/scripts/xlsx-extract.py` (14.7KB) created as a new script.
Phase 2 agent definition updated to detect .xlsx files and pre-process them before
assigning to analyzer agents. Output includes cell-level YAML with formula strings.
Cross-validation layer added: figures from a single source are flagged as
`confidence: ≤0.7` in loan-data.yaml.

**Outcome:** Committed as part of the EPIC-001 work (commit cbb21a8 +). The
2026-03-23 swarm review confirmed this fix was correctly implemented and no hallucination
risk remained for XLSX data.

## Application Guide

### When to Use

- Any pipeline that needs to extract numbers from .xlsx files
- Financial documents where accuracy is critical (not just "approximately right")
- When provenance (which cell, which sheet) matters for audit trails

### When NOT to Use

- Data is in CSV format (agents can read these directly)
- Only need column headers and structure, not cell values
- XLSX files are used only as templates, not data sources

### Implementation Steps

1. Create `xlsx-extract.py` using `openpyxl` (Python stdlib)
2. Output schema: `{sheet_name: {cell_address: {value, formula, type}}}`
3. Add named_ranges and structured_tables as top-level sections
4. In Phase 2, detect .xlsx files before spawning analyzer agents
5. Run extractor: `python3 xlsx-extract.py <input.xlsx> <output.yaml>`
6. Pass `<output.yaml>` path (not .xlsx path) to analyzer agents
7. In loan-data.yaml, add `source_cell` field alongside each extracted value

### Common Mistakes

- Passing .xlsx path to agents without pre-processing (they cannot read it)
- Extracting only visible cells (miss hidden sheets with key data)
- Not handling merged cells (value appears in top-left, rest show None)
- Ignoring formula strings (lose the calculation provenance)

## Related Learnings

- LEARN-ARCH-002 — Two-Tier Data Model
- LEARN-IMPL-003 — HTML-to-DOCX via python-docx (not pandoc)

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
