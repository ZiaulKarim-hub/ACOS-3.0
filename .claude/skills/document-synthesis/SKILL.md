---
name: document-synthesis
description: Structured guidance for compressing large documents into structured, LLM-friendly YAML summaries (synthdocs). Supports legal, financial, technical, and general documents with strict data integrity.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Glob, Grep, Bash
---

# Document Synthesis Skill

## Purpose

Transform large documents (50-200+ pages) into structured, LLM-friendly synthetic summaries ("synthdocs") for efficient downstream analysis. Works with any document type -- legal, financial, technical, academic, or general business.

## When to Use

Apply this skill when:
- Processing large documents for LLM analysis
- Creating structured summaries from dense source material
- Enabling multi-document correlation
- Building knowledge bases from document collections
- Preparing documents for knowledge graph extraction

## Skill Protocol

### Phase 1: Document Intake & Analysis

1. Read the source document (PDF, DOCX, XLSX, TXT, or other formats)
2. Identify document type from content (legal, financial, technical, academic, policy, operational, other)
3. Assess document complexity and scope
4. Note metadata: page count, date, author, file size
5. Perform safety checks for large or scanned PDFs:
   - Check text extractability
   - Classify size: **SAFE** (<10MB text), **LARGE TEXT** (>10MB text), **SCANNED/OCR** (no text layer)
   - For SCANNED/OCR documents, note that extraction quality may be degraded

### Phase 2: Content Extraction

1. Extract full text content preserving structure (headers, sections, tables)
2. For spreadsheets: extract data from all sheets including numerical values and formulas
3. For presentations: extract slide content and speaker notes
4. Preserve table structures and relationships
5. Note any embedded images or charts with descriptions

### Phase 3: Classification & Categorization

1. Identify the primary document category
2. Map to a domain-appropriate classification system (the project's own taxonomy, or general-purpose categories)
3. Document classification confidence (0.0-1.0)
4. Note secondary categories if the document spans multiple areas

### Phase 4: Synthetic Summary Generation

Generate a YAML synthdoc with the following structure. Adapt sections to the document type -- not every section applies to every document.

```yaml
synthdoc:
  metadata:
    source_document: "[Original filename]"
    document_type: "[classification]"
    date_created: "[YYYY-MM-DD]"
    page_count: 0
    synthesized_by: "Claude Code"
    classification_confidence: 0.0

  executive_summary: |
    Brief 2-3 sentence summary of document purpose and key content.

  key_entities:
    - name: "[Entity name]"
      type: "[person|organization|system|location|other]"
      role: "[Role in document context]"

  key_facts:
    - fact: "[Extracted fact]"
      value: "[Exact value -- DO NOT ROUND]"
      context: "[Context for this fact]"
      source_section: "[Section reference]"

  structure_summary:
    - section: "[Section name]"
      topic: "[What this section covers]"
      key_points:
        - "[Point 1]"
        - "[Point 2]"

  risk_factors:
    - risk: "[Description]"
      severity: "[High|Medium|Low]"
      mitigation: "[Stated mitigation if any]"

  action_items:
    - item: "[Required action or outstanding item]"
      priority: "[High|Medium|Low]"
      deadline: "[Date if stated]"

  cross_references:
    - document: "[Referenced document]"
      relationship: "[How it relates]"

  red_flags: []  # Items requiring immediate attention

  data_integrity_notes:
    estimation_instances: []
    data_quality_flags: []

  omissions:
    - item: "[What was omitted]"
      reason: "[Why -- materiality threshold or irrelevance]"
```

Also generate a markdown summary as secondary output containing the executive summary, key facts, risk factors, and action items in a human-readable format.

### Phase 5: Multi-Document Compilation (Optional)

When processing multiple documents for the same project or topic:

1. Process each document individually through Phases 1-4
2. Create a cross-reference map between documents
3. Identify discrepancies between documents (conflicting dates, numbers, or claims)
4. Generate a compiled summary with a metadata header listing all source documents
5. Flag items needing reconciliation across documents

### Phase 6: Quality Verification

Before delivering any synthdoc:

1. Cross-reference all numerical data with the source document -- 100% transcription accuracy required
2. Verify all proper names are transcribed exactly as they appear in the source
3. Confirm all dates are accurate and in the format used by the source
4. Ensure no information was fabricated -- use `NOT_FOUND` for missing data
5. Validate that the YAML output is parseable
6. Confirm classification confidence is reasonable given the document content

## Data Integrity Rules (Non-Negotiable)

These rules apply to every synthdoc produced. There are no exceptions.

- **NO FABRICATION** -- never create information not present in the source document
- **EXACT NUMERICAL PRESERVATION** -- all numbers must be copied exactly as they appear; no rounding, no unit conversion, no approximation
- **PRECISE DATE HANDLING** -- all dates must be transcribed exactly as written in the source
- **NAME ACCURACY** -- all proper names (people, organizations, places, products) must be transcribed exactly
- **INFORMATION GAPS** -- when data is not found, use `NOT_FOUND` or `Source document unclear on [specific point]`; never fill gaps with assumptions

## Output Naming Convention

```
{YYYY-MM-DD}_{DocumentType}_SYNTHDOC.yaml
{YYYY-MM-DD}_{DocumentType}_SUMMARY.md
```

Examples:
- `2026-02-10_Legal_SYNTHDOC.yaml`
- `2026-02-10_Financial_SUMMARY.md`
- `2026-02-10_Technical_SYNTHDOC.yaml`

## Domain-Specific Adaptations

The synthdoc schema adapts based on document type. Include domain-relevant sections and omit irrelevant ones.

| Document Type | Additional Sections to Emphasize |
|---|---|
| **Legal** | Key parties, terms, covenants, provisions, events of default, governing law |
| **Financial** | Metrics, projections, ratios, assumptions, audit opinions, material changes |
| **Technical** | Architecture, APIs, dependencies, specifications, compatibility requirements |
| **Academic/Research** | Methodology, findings, conclusions, citations, limitations, peer review status |
| **Policy/Operational** | Requirements, processes, timelines, responsibilities, compliance obligations |

## Quality Checklist

### Completeness
- [ ] All major sections of the source document are represented
- [ ] Key entities are captured with correct roles
- [ ] Numerical data is transcribed exactly
- [ ] Dates are accurate
- [ ] Cross-references to other documents are noted

### Accuracy
- [ ] No fabricated information
- [ ] All proper names match the source exactly
- [ ] Classification confidence is justified
- [ ] Information gaps are explicitly marked as NOT_FOUND

### Structure
- [ ] YAML is valid and parseable
- [ ] Sections are appropriate for the document type
- [ ] Executive summary is concise (2-3 sentences)
- [ ] Omissions section explains what was left out and why

### Usability
- [ ] Synthdoc can stand alone for downstream LLM analysis
- [ ] Markdown summary is readable by humans
- [ ] File naming convention is followed
- [ ] Evidence bundle includes source document metadata and verification notes

---

*Document Synthesis Skill -- Compress once, reason many times.*
