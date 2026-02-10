---
name: document-processing
description: Structured guidance for ingesting, extracting, and preparing documents for downstream analysis. Handles PDF, DOCX, XLSX, and other formats. Use when processing raw documents before synthesis or knowledge graph construction.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Glob, Grep, Bash
---

# Document Processing Skill

## Purpose

Process raw documents into clean, structured text suitable for downstream analysis. This skill handles the intake and extraction pipeline — the step *before* `/document-synthesis` or `/knowledge-graph`.

## When to Use

Apply this skill when:
- Ingesting batches of raw documents for analysis
- Extracting text from PDFs (including scanned/OCR documents)
- Converting between document formats while preserving structure
- Preparing documents for `/document-synthesis` or `/knowledge-graph`
- Building document processing pipelines for a project

**Use `/document-synthesis` instead for:** Creating structured YAML summaries from already-readable documents.

## Skill Protocol

### Phase 1: Document Inventory

1. Scan the target directory for all document files
2. Classify each by format:
   - **Text-native:** `.md`, `.txt`, `.csv`, `.json`, `.yaml`, `.xml`, `.html`
   - **Office formats:** `.docx`, `.xlsx`, `.pptx`, `.odt`, `.ods`
   - **PDF:** `.pdf` (text-layer vs scanned)
   - **Image:** `.png`, `.jpg`, `.tiff` (require OCR)
3. Generate an inventory:
   ```yaml
   document_inventory:
     scan_date: "[YYYY-MM-DD]"
     source_directory: "[path]"
     total_files: 0
     by_format:
       pdf: 0
       docx: 0
       xlsx: 0
       other: 0
     processing_notes: []
   ```

### Phase 2: Extraction Strategy

For each document, determine approach based on available tooling:

| Format | Strategy | Fallback |
|--------|----------|----------|
| **Text-native** | Direct `Read` | — |
| **PDF (text)** | `Read` (Claude reads PDFs natively) | `pdftotext` via project toolchain |
| **PDF (scanned)** | Note OCR requirement | Recommend `tesseract` or project's OCR tool |
| **DOCX/PPTX** | `pandoc` if available | Note limitation |
| **XLSX** | Sheet-by-sheet extraction | `csvkit` or project's preferred tool |

Check available tooling — do NOT hardcode tool preferences. Defer to the project's `CLAUDE.md` for toolchain conventions.

### Phase 3: Text Extraction

For each document, extract content preserving structure:

1. **Headings:** Preserve hierarchy (H1 > H2 > H3)
2. **Tables:** Convert to markdown tables or CSV
3. **Lists:** Preserve numbered and bulleted structure
4. **Metadata:** Extract title, author, date, page count
5. **Page boundaries:** Mark for source referencing

Produce per-document output:
```yaml
extracted_document:
  metadata:
    source_file: "[original filename]"
    format: "[pdf|docx|xlsx|etc]"
    extraction_date: "[YYYY-MM-DD]"
    page_count: 0
    word_count: 0
    extraction_method: "[direct|pandoc|ocr]"
    extraction_quality: "[high|medium|low]"

  content:
    full_text: |
      [Extracted text with structure markers]
    sections:
      - heading: "[Section title]"
        level: 1
        content: "[Section content]"
    tables:
      - table_id: 1
        caption: "[Table caption if any]"
        data: "[Markdown table or CSV]"
```

### Phase 4: Batch Processing

When processing multiple documents:
1. Process independent files in parallel where possible
2. Track status per document:
   ```yaml
   batch_status:
     total: 0
     completed: 0
     failed: 0
     documents:
       - file: "[name]"
         status: "[completed|failed|skipped]"
         quality: "[high|medium|low]"
         notes: "[any issues]"
   ```
3. Handle failures gracefully — log and continue with remaining documents
4. Generate batch summary when complete

### Phase 5: Output & Handoff

1. Write extracted content to the project's conventions (or default to `extracted/` directory)
2. Prepare manifest for downstream skills:
   - **For `/document-synthesis`:** List of clean, structured text files ready for synthdoc creation
   - **For `/knowledge-graph`:** Flag entities and relationships found during extraction
   - **For `/deep-research`:** Note key claims and data points for verification

## Quality Checklist

- [ ] All documents in inventory have been processed or noted as failed
- [ ] Text extraction preserves original structure (headings, tables, lists)
- [ ] Numerical data is transcribed exactly — no rounding or unit conversion
- [ ] Extraction quality is rated per document (high/medium/low)
- [ ] Batch report generated with processing results
- [ ] Output follows project's file conventions

## Data Integrity Rules

- **No content modification** — extract text exactly as it appears
- **Preserve numerical precision** — never round or convert during extraction
- **Mark quality issues** — if extraction is lossy, document what was lost
- **Source traceability** — every section references its source page/location

---

*Document Processing Skill — Clean extraction is the foundation of good analysis.*
