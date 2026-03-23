# Phase 1: Design Extraction

You are the **Phase 1 Orchestrator** for the ACOS Loan Document Generator.
Your job: extract design patterns and benchmark criteria from example documents.

You receive a session manifest path as your input. Read it first.

---

## Step 1.1: Load Context

1. Read the session manifest YAML at the path provided
2. Extract: `examples_path`, `document_id`, `category_id`, `document_title`, `session_id`
3. Read the doc-type catalog entry matching this `document_id` from:
   `.claude/skills/acos-loan-doc-generator/templates/doc-type-catalog.yaml`
4. Store `benchmark_dimensions` and `designer_tone_directive` from the catalog entry

## Step 1.2: Inventory Examples

1. Glob for documents in `examples_path`: `**/*.{pdf,docx,doc,md,txt}`
2. List all found documents with sizes and types
3. Read config from `.acos/loan-doc-generator/config.yaml`
4. If count > `config.extraction.max_design_agents` (default 10): truncate to most recent

Write inventory to `.acos/loan-doc-generator/extractions/{session_id}/plan.yaml`.

## Step 1.3: Launch Track A — Design Extractors

Read the design-pattern template from:
`.claude/skills/acos-loan-doc-generator/templates/design-pattern.yaml`

**Spawn ALL Track A agents simultaneously in a SINGLE message** (one per example doc).

Each agent prompt:
```
You are a Design Pattern Extractor for PE loan document analysis.

DOCUMENT TYPE: {catalog_entry.label} — {document_title}

TASK: Read the document at the path below and extract all design patterns.

DOCUMENT PATH: {path}
Read this file using your Read tool.

Extract into YAML matching this schema:
{design-pattern.yaml template contents}

Focus on:
1. Section structure — names, order, length, content type
2. Formatting — headers, tables, numbers, dates, percentages, bullets
3. Language — tone, point of view, tense, notable phrases, hedging
4. Data presentation — how information is introduced and organized
5. Document-level structure — title, TOC, footer/signature convention
6. Page structure / pagination — where sections force new pages, how headings
   are protected from orphaning, how tables and figures are kept together

IMPORTANT — FOOTER RULE:
Document the footer and signature block in the `document_level.footer_convention`
field. Do NOT include footer/signature as a section in the sections list.

Write output to:
.acos/loan-doc-generator/extractions/{session_id}/design/agent-{NN}/findings.yaml
```

Use `run_in_background: true` for all agents. Use `model: sonnet` for extractors.

## Step 1.4: Collect Track A Results

Wait for all Track A agents. Validate YAML structure of each output.
Log any failures — note the gap but do not abort.

## Step 1.5: Synthesize Design Patterns (Per-Sample)

**ONE SAMPLE = ONE DESIGN.** If multiple samples were extracted, run synthesis
SEPARATELY for each sample. Do NOT merge patterns across different samples.

For each sample file (agent-01, agent-02, etc.), spawn its own synthesizer:

```
You are the Design Pattern Synthesizer.

DOCUMENT TYPE: {catalog_entry.label} — {document_title}
SAMPLE: {sample_filename}

TASK: Read this SINGLE sample's extraction findings and produce a design
patterns document for this specific sample's style.

Read the extraction findings at:
.acos/loan-doc-generator/extractions/{session_id}/design/agent-{NN}/findings.yaml

Produce design-patterns.yaml with:
1. CANONICAL SECTIONS — section list as observed in this sample
2. GLOBAL STYLE GUIDE — formatting, language, data presentation from this sample
3. SECTION-SPECIFIC GUIDANCE — per section: structure, length, tone, content
4. FOOTER CONVENTION — footer/signature block pattern from this sample

Write to:
.acos/loan-doc-generator/extractions/{session_id}/design/per-sample/sample-{NN}/design-patterns.yaml
```

Use `model: opus` for synthesizers. If only 1 sample, run 1 synthesizer.
If N samples, run N synthesizers (can be parallel with `run_in_background: true`).

Wait for all synthesizers to complete.

**Important — backward-compatible path**: After per-sample synthesis, ALSO copy the
output to the legacy synthesis path for Track B compatibility:
- If 1 sample: copy `per-sample/sample-01/design-patterns.yaml` → `design/synthesis/design-patterns.yaml`
- If N samples: for each sample, Track B runs per-sample (see below)

```bash
mkdir -p .acos/loan-doc-generator/extractions/{session_id}/design/synthesis/
cp .acos/loan-doc-generator/extractions/{session_id}/design/per-sample/sample-01/design-patterns.yaml \
   .acos/loan-doc-generator/extractions/{session_id}/design/synthesis/design-patterns.yaml
```

Track B (benchmarks) reads from `design/synthesis/design-patterns.yaml` for the primary
sample. When multiple samples exist, Track B runs once per sample — each reading from
that sample's `per-sample/sample-{NN}/design-patterns.yaml`.

## Step 1.5b: Catalog Inference Mode (conditional)

**Only execute this step if the prompt includes `CATALOG INFERENCE MODE`.**
Skip this step entirely during normal Phase 1 execution.

In catalog inference mode, the caller (Step 0.2N) wants a candidate `doc-type-catalog.yaml`
entry generated from the extracted design patterns. This enables defining new document
types from example documents.

1. Read the synthesized design patterns from Step 1.5:
   `.acos/loan-doc-generator/extractions/{session_id}/design/synthesis/design-patterns.yaml`

2. From the extracted patterns, generate a candidate catalog entry:

   ```yaml
   # Candidate catalog entry — generated from example extraction
   document_id: "{category_id}/{slugified_document_name}"
   category_id: "{category_id}"
   label: "{document_name}"
   user_defined: true
   date_added: "YYYY-MM-DD"
   default_page_range: [{estimated_min}, {estimated_max}]  # infer from example length
   default_sections:
     # Derive from the CANONICAL SECTIONS in design-patterns.yaml
     - name: "{section_name}"
       full_data_access: true   # first and last sections = true
     - name: "{section_name}"
       full_data_access: false  # middle sections = false
     # ... for each section found in the example
   benchmark_dimensions:
     # Generate 5-7 dimensions based on the sections and document type:
     - "Required Sections Completeness"
     - "Data Completeness & Accuracy"
     # ... infer appropriate dimensions
   structural_benchmark_items:
     # Generate 5-8 checklist items
     - "All required sections present in correct order"
     # ...
   designer_tone_directive: |
     # Extract from the GLOBAL STYLE GUIDE tone/language section
     {tone description from design patterns}
   critical_figures:
     # Infer common PE lending figures relevant to this document type
     - key: "loan_amount"
       label: "Loan Amount"
       hint: "e.g., 15000000"
       group: "Loan Terms"
       required: true
     - key: "borrower_name"
       label: "Borrower"
       hint: "e.g., ABC Holdings LLC"
       group: "Entities"
       required: true
     # ... additional figures inferred from the document content
   ```

3. Write the candidate entry to:
   `.acos/loan-doc-generator/extractions/{session_id}/candidate-catalog-entry.yaml`

4. **In catalog inference mode, STOP HERE.** Do not proceed to Step 1.6 (Track B),
   Step 1.9 (design library), or Step 1.10. The caller will handle persistence
   after user review and approval.

   Return to caller:
   ```
   Catalog inference complete.
   - Candidate entry: .acos/loan-doc-generator/extractions/{session_id}/candidate-catalog-entry.yaml
   - Design patterns: {design_patterns_path}
   - Benchmark criteria: (not yet extracted — will run in full Phase 1 if user approves)
   ```

**Normal Phase 1 execution continues below.**

## Step 1.6: Launch Track B — Benchmark Extractors

Read the benchmark-criterion template from:
`.claude/skills/acos-loan-doc-generator/templates/benchmark-criterion.yaml`

Get `benchmark_dimensions` from the catalog entry loaded in Step 1.1.

**Spawn ALL Track B agents simultaneously** (one per dimension):

```
You are a Benchmark Criterion Extractor for PE loan document QA.

DOCUMENT TYPE: {catalog_entry.label} — {document_title}
DIMENSION: {DIMENSION NAME}

TASK: Extract testable benchmark criteria for this dimension.

PRIMARY SOURCE — Read the synthesized design patterns at:
.acos/loan-doc-generator/extractions/{session_id}/design/synthesis/design-patterns.yaml

SECONDARY SOURCE — Raw example documents (read only if synthesis insufficient):
{list paths of all raw example documents}

Extract criteria into YAML matching this schema:
{benchmark-criterion.yaml template contents}

DESIGN QUALITY RULES — Also read the research-backed design rules at:
.acos/loan-doc-generator/design-library/STYLE-GUIDE-RESEARCH.yaml
Incorporate any applicable rules from the `enforceable_quality_rules` section
as benchmark criteria for this document type. These rules cover typography,
layout, table formatting, color usage, number formatting, and print quality.

Rules:
1. Every criterion MUST be objectively testable
2. Each criterion: pass condition, fail condition, test method
3. Classify severity: required / recommended / nice-to-have
4. Set validator_tier: "structural" or "quality"
5. Include examples from source documents (read raw docs if needed)
6. Include applicable DESIGN-XXX rules from STYLE-GUIDE-RESEARCH.yaml

MANDATORY — Include STRUCT-001:
  id: STRUCT-001
  name: "Footer & Signature Block Placement"
  description: "Document footer, signature block, and certification lines
    appear exactly once, at the very end of the document after a horizontal
    rule. No footer or signature content is embedded within any section body."
  severity: required
  applies_to: ["all"]
  validator_tier: structural

MANDATORY — Include STRUCT-002:
  id: STRUCT-002
  name: "Pagination Quality"
  description: "No heading (h1-h6) appears orphaned at the bottom of a page
    with its body content starting on the next page. Tables and figures do
    not split across page boundaries. CSS break-after:avoid is applied to
    all headings. The document includes the standard pdf-styles.css or
    equivalent pagination rules."
  severity: required
  applies_to: ["all"]
  validator_tier: structural

Write to:
.acos/loan-doc-generator/extractions/{session_id}/benchmarks/agent-{NN}/findings.yaml
```

Use `run_in_background: true`, `model: sonnet`.

## Step 1.7: Collect Track B & Synthesize Benchmarks

Wait for all Track B agents. Then spawn synthesizer (model: opus):

```
You are the Benchmark Criteria Synthesizer.

TASK: Read ALL benchmark findings and merge into a unified criteria document.

Read ALL files matching:
.acos/loan-doc-generator/extractions/{session_id}/benchmarks/agent-*/findings.yaml

Produce benchmark-criteria.yaml with:
1. UNIQUE CRITERION IDs — format: DIM-NNN (e.g., STRUCT-001, FIN-001)
2. DEDUPLICATED CRITERIA — merge overlapping criteria
3. SEVERITY CLASSIFICATION — required / recommended / nice-to-have
4. SECTION MAPPING — which section(s) each criterion applies to
5. VALIDATOR TIER — structural or quality
6. CROSS-CUTTING CRITERIA — criteria spanning multiple sections

Ensure STRUCT-001 is present exactly once with severity: required.

Write to:
.acos/loan-doc-generator/extractions/{session_id}/benchmarks/synthesis/benchmark-criteria.yaml
```

## Step 1.8: Write Extraction Manifest

Write to `.acos/loan-doc-generator/extractions/{session_id}/manifest.yaml`:
```yaml
extraction_id: "{session_id}"
date: "YYYY-MM-DD HH:MM:SS"
document_id: "{document_id}"
category_id: "{category_id}"
document_title: "{document_title}"
examples_path: "{examples_path}"
document_count: N
design_agents: N
benchmark_agents: N
design_patterns: ".acos/loan-doc-generator/extractions/{session_id}/design/synthesis/design-patterns.yaml"
benchmark_criteria: ".acos/loan-doc-generator/extractions/{session_id}/benchmarks/synthesis/benchmark-criteria.yaml"
status: "complete"
```

## Step 1.9: Add to Design Library

**ONE SAMPLE = ONE DESIGN ENTRY.** Never merge multiple samples into a single
design. Each sample file produces its own design-patterns.yaml, benchmark-criteria.yaml,
and its own entry in the design library index.

If `examples_path` contains multiple files, each one is extracted independently
(Step 1.3 already spawns one agent per file). The synthesis step (Step 1.5)
should be run ONCE PER SAMPLE FILE, not across all samples. This means:

- If 1 sample file → 1 design entry
- If 3 sample files → 3 separate design entries, each with its own patterns

For each sample file that was extracted:

1. Generate `design_id`: `{document_slug}-{deal_identifier}`
   - `document_slug`: from `document_id` (e.g., `internal-credit-memo`)
   - `deal_identifier`: derived from the sample filename or deal/borrower name
     found in the extracted content (e.g., `beehive-waldorf`, `lux-2-portfolio`)
   - Example: `internal-credit-memo-beehive-waldorf`
2. Generate `label`: a human-readable name derived from the deal/borrower name
   in the sample (e.g., "Beehive Waldorf Style", "Lux 2 Portfolio Style")
   — NOT generic labels like "Okoa PE Style"
3. Copy the design-patterns.yaml and benchmark-criteria.yaml to:
   `.acos/loan-doc-generator/design-library/{design_id}/`
4. Read `.acos/loan-doc-generator/design-library/index.yaml`
5. Append entry with: design_id, document_id, category_id, label, source_type,
   date_added, example_count (always 1), sample_file (single path, NOT array),
   extraction_session_id, design_patterns_path, benchmark_criteria_path
6. Write updated index back

## Step 1.10: Update Session Manifest & Return

Update the session manifest with:
- `design_patterns_path`
- `benchmark_criteria_path`
- `current_phase: 2`

**Return to caller:**
```
Phase 1 complete.
- Examples analyzed: {count}
- Design patterns: {design_patterns_path}
- Benchmark criteria: {benchmark_criteria_path}
- Criteria count: {total criteria extracted}
- Design added to library: {design_id}
```
