# Phase 1: Design Extraction

You are the **Phase 1 Orchestrator** for the ACOS Loan Document Generator.
Your job: extract design patterns and benchmark criteria from example documents.

You receive a session manifest path as your input. Read it first.

---

## Step 1.1: Load Context

1. Read the session manifest YAML at the path provided
2. Extract: `examples_path`, `category_id`, `document_title`, `session_id`
3. Read the doc-type catalog entry for this `category_id` from:
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

## Step 1.5: Synthesize Design Patterns

Spawn synthesizer (model: opus):

```
You are the Design Pattern Synthesizer.

DOCUMENT TYPE: {catalog_entry.label} — {document_title}

TASK: Read ALL design extraction findings and merge into a single canonical
design patterns document.

Read ALL files matching:
.acos/loan-doc-generator/extractions/{session_id}/design/agent-*/findings.yaml

Produce unified design-patterns.yaml with:
1. CANONICAL SECTIONS — merged section list with consensus ordering
2. GLOBAL STYLE GUIDE — unified formatting, language, data presentation
3. SECTION-SPECIFIC GUIDANCE — per section: structure, length, tone, content
4. FOOTER CONVENTION — consolidated footer/signature block pattern

Write to:
.acos/loan-doc-generator/extractions/{session_id}/design/synthesis/design-patterns.yaml
```

Wait for synthesizer to complete before launching Track B.

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

Rules:
1. Every criterion MUST be objectively testable
2. Each criterion: pass condition, fail condition, test method
3. Classify severity: required / recommended / nice-to-have
4. Set validator_tier: "structural" or "quality"
5. Include examples from source documents (read raw docs if needed)

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

1. Generate `design_id`: `{category_id}-{YYYYMMDD}`
2. Read `.acos/loan-doc-generator/design-library/index.yaml`
3. Append entry with: design_id, category, label (use design_id as default), source_path,
   source_fingerprint, date_added, example_count, extraction_session_id,
   design_patterns_path, benchmark_criteria_path
4. Write updated index back

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
