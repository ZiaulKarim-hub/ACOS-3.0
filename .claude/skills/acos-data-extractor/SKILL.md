---
name: acos-data-extractor
description: "Data extraction from large document collections with optional PRISM industry intelligence. Schema-driven triage, parallel extraction with provenance, adversarial QA with Wigum loop. When PRISM DD framework is available, enriches agents with 252-item due diligence taxonomy for institutional-grade accuracy. Handles hundreds to thousands of files (PDF, DOCX, XLSX, TXT)."
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
context: fork
argument-hint: "<folder-path-1> [folder-path-2] ... --schema <schema.yaml> [--output <output-folder>]"
---

# ACOS Data Extractor

## Overview

Extracts specific data points from large document collections using a **schema-driven, multi-agent pipeline**. Given a set of folders and a schema describing what to find, the skill inventories all files, triages them for relevance, deeply extracts values with provenance, and validates everything through adversarial QA.

Designed for **high-accuracy extraction** where missing data is costly — financial documents, legal files, compliance records, due diligence packages. Works across any domain; the domain knowledge lives in the schema, not the skill.

When PRISM intelligence is available (at `$HOME/okoa-labs/okoa_ops/.claude/data/`), the skill automatically enriches all agents with the **252-item Due Diligence framework** (CCII codes), giving them institutional-grade awareness of document types, data structures, and authority hierarchies. This is optional — the skill degrades gracefully to keyword-only extraction without PRISM.

```
Phase 0: Init            -> Parse args, load schema, inventory files, resolve models
  |-- PRISM Integration  -> Auto-detect DD framework, build field-to-CCII mapping (optional)
  |-- Token Budget       -> Estimate file tokens, compute optimal agent counts per phase
Phase 1: Triage          -> Fast parallel scan — token-budgeted agent count (2-15)
  |-- QA Gate 1          -> Completeness check — did triage miss relevant files?
Phase 2: Deep Extraction -> Read triaged files — recalculated agent count from actual triage (2-7)
  |-- QA Gate 2          -> Adversarial verification (3 QA agents + Domain Expert if PRISM)
  ↕ Wigum Loop           -> Iterate on flagged items (max 5 rounds)
Phase 3: Final Report    -> Consolidated findings with full provenance chain + CCII tags
```

## Data Integrity Rules

**INJECT THESE RULES into every agent prompt in every phase.** Non-negotiable for extraction accuracy.

1. **NO FABRICATION** — Never create, infer, estimate, or guess values. If a value cannot be found in the source documents, use `NOT_FOUND`. No exceptions.
2. **EXACT NUMERICAL PRESERVATION** — Copy numbers character-by-character from the source. No rounding, no reformatting, no unit conversion. `$1,234,567.89` stays exactly `$1,234,567.89`.
3. **EXACT NAME PRESERVATION** — Preserve capitalization, spacing, suffixes (Jr., Sr., III, LLC, Inc., Corp.), and all punctuation exactly as written.
4. **EXACT DATE PRESERVATION** — Copy dates in their source format. No conversion between formats (e.g., do NOT convert `03/15/2024` to `March 15, 2024`).
5. **PROVENANCE REQUIRED** — Every extracted value MUST cite: source document filename, page number, section/area on the page, and a verbatim quote of the surrounding context.
6. **NOT_FOUND PROTOCOL** — When a value cannot be found: list ALL documents searched, confirm the data is genuinely absent (not just in an unexpected location), and mark as `NOT_FOUND`.
7. **CONFLICT PROTOCOL** — When multiple sources provide different values for the same field: flag the conflict, record ALL values with their sources, apply the resolution hierarchy (recency > authority > specificity), and document the rationale.
8. **CONFIDENCE HONESTY** — Rate confidence as a percentage (0–100%). Use the following anchors: 90–100% = exact match with clear, unambiguous source; 60–89% = requires interpretation, indirect reference, or context inference; below 60% = ambiguous source, partial match, or significant uncertainty. Never inflate confidence. Round to the nearest 5%.

---

## Protocol

### Phase 0: Initialization

**Step 0.1** — Parse `$ARGUMENTS` for required and optional parameters:

| Argument | Required | Description |
|----------|----------|-------------|
| `<folder-path-1>` | Yes | First directory to scan |
| `[folder-path-2 ...]` | No | Additional directories to scan |
| `--schema <path>` | Yes* | YAML file defining fields to extract |
| `--output <path>` | No | Output directory for results (default: `.acos/sessions/data-extractor/{session-id}/`) |

*If `--schema` is not provided, enter interactive schema builder (Step 0.1b).

If no folders are provided, prompt:
> "Which directories should I search? Provide one or more folder paths."

**Step 0.1b** — Interactive Schema Builder (when no `--schema` provided):

Prompt the user:
> "What specific data points are you looking for? Describe each item you need to find.
> Example: 'loan origination date, property address, payoff amount, monthly investor payments with dates'"

Parse the user's response into the internal schema format. For each field:
- Generate a unique `id` (snake_case from the field name)
- Infer `type` (date, currency, address, text, number, currency_with_date, etc.)
- Set `multi: true` if the field implies multiple entries (e.g., "monthly payments", "all investors")
- Generate `hints` — keyword variations an agent would look for in documents
- Write the generated schema to `{session-dir}/extraction-schema.yaml`
- Present the schema to the user for confirmation before proceeding

**Step 0.2** — Validate all folder paths exist. For each folder, recursively inventory all files:

- Count total documents
- Classify by format: PDF, DOCX/DOC, XLSX/XLS/CSV, TXT/MD, images, other
- Skip hidden files/directories (`.DS_Store`, `.git`, `.acos`, `.claude`, etc.)
- Flag any files larger than 50MB (may need special handling)
- Record: filename, full path, file size, file type, parent folder name
- Write inventory to `{session-dir}/file-inventory.yaml` using the template from `templates/file-inventory.yaml`

Display inventory summary to user:
```
Source Directory Inventory
===========================
Directory 1: /path/to/folder (247 files)
  PDF: 183 | DOCX: 31 | XLSX: 22 | TXT: 8 | Other: 3

Directory 2: /path/to/folder2 (89 files)
  PDF: 61 | DOCX: 15 | XLSX: 9 | Other: 4

Total: 336 documents to scan
Schema: 12 fields to extract
```

**Step 0.3** — Generate session ID: `DDE-[YYYYMMDD]-[HHMMSS]`

**Step 0.4** — Create session directory and evidence structure:

```
{output-dir}/
├── session-manifest.yaml
├── extraction-schema.yaml        # copy of input schema or generated schema
├── prism-context.yaml            # PRISM DD framework context (if available)
├── token-budget.yaml             # agent scaling plan with per-file token estimates
├── file-inventory.yaml          # full file inventory (from template)
├── phase1/
│   └── triage-manifest.yaml
├── phase2/
│   ├── extraction-map.yaml
│   ├── provenance-record.yaml
│   └── conflict-resolutions.yaml
├── qa-gates/
│   ├── triage-qa-iteration-1.yaml
│   ├── extraction-qa-value-iteration-1.yaml
│   ├── extraction-qa-completeness-iteration-1.yaml
│   ├── extraction-qa-provenance-iteration-1.yaml
│   ├── extraction-qa-domain-iteration-1.yaml  # Domain Expert QA (if PRISM)
│   ├── extraction-qa-synthesis-iteration-1.yaml
│   └── ...
├── extraction-results.yaml      # machine-readable final output (from template)
└── EXTRACTION_REPORT.md
```

Write `session-manifest.yaml` using the template from `templates/session-manifest.yaml`.

**Step 0.6** — PRISM Knowledge Integration (Optional Enhancement)

Check if PRISM intelligence is available:

```bash
PRISM_DATA=""
if [ -d "$HOME/okoa-labs/okoa_ops/.claude/data" ]; then
  PRISM_DATA="$HOME/okoa-labs/okoa_ops/.claude/data"
fi
```

If PRISM data directory is found:

1. **Load DD Framework Taxonomy** — Read `$PRISM_DATA/dd-framework-taxonomy.yaml` (31 categories, 252 items with CCII codes, asset types, deal structures, responsible parties). This gives agents a complete taxonomy of document types in private credit.

2. **Load Master DD Framework** — Read `$PRISM_DATA/master-dd-framework.txt` (detailed descriptions, instructions, and internal evaluation criteria for each of the 252 DD items). This tells agents what to look for inside documents and how to evaluate data quality.

3. **Load KG Schema** — Read `$PRISM_DATA/kg-schema.yaml` (16 node types: DEAL, PARTY, PROPERTY, FINANCIAL_INSTRUMENT, COVENANT, RISK, etc.; 22 edge types). This gives agents structural awareness of how financial entities relate to each other.

4. **Map Schema Fields to DD Categories** — For each extraction schema field, identify which DD categories (by CCII code range) are most likely to contain answers. Build a `field_to_ccii_map`:

```yaml
field_to_ccii_map:
  loan_origination_date:
    likely_categories: ["29 - Transaction Documentation", "30 - Closing & Post-Closing"]
    likely_ccii_codes: ["2901", "2902", "3001"]
    dd_context: "Found in loan agreements (2901), term sheets (2902), or closing checklists (3001)"
  property_address:
    likely_categories: ["06 - Real Estate Property Analysis"]
    likely_ccii_codes: ["0601", "0604"]
    dd_context: "Found in appraisals (0601) or title reports (0604)"
  payoff_amount:
    likely_categories: ["03 - Financial Analysis", "29 - Transaction Documentation"]
    likely_ccii_codes: ["0301", "0302", "2903"]
    dd_context: "Found in financial statements (0301), payoff letters (0302), or security docs (2903)"
```

5. **Build PRISM Context Block** — Assemble a reusable context block for injection into agent prompts:

```
PRISM INDUSTRY CONTEXT (252-Item Due Diligence Framework):
[inject relevant DD categories with item names, descriptions, and evaluation criteria]

DOCUMENT TYPE AWARENESS:
[inject DD taxonomy — what document types exist, what they typically contain]

FIELD-TO-CATEGORY MAPPING:
[inject field_to_ccii_map — which DD categories likely contain each schema field]

ENTITY STRUCTURE AWARENESS:
[inject KG node types — agents should recognize deals, parties, properties, instruments, covenants, risks]
```

6. **Write PRISM context** to `{session-dir}/prism-context.yaml` for reuse across phases.

If PRISM data is NOT available:
- Log: `"PRISM intelligence not found at $HOME/okoa-labs/okoa_ops/.claude/data — proceeding with keyword-only extraction"`
- Proceed with the existing keyword-based pipeline (no degradation)

Record in session manifest: `prism_integration: true|false`

**Step 0.7** — Token Budget Planning

Before spawning any agents, compute the optimal agent counts for Phase 1 and Phase 2.
This prevents token waste from over-parallelism (too much duplicated overhead) and
quality degradation from under-parallelism (agents overloaded with too many files).

**Step 0.7a** — Estimate per-file token costs from the file inventory:

```
For each file in inventory:
  if file_type == "PDF":
    # Estimate pages from file size (~50KB per page for typical PDFs)
    estimated_pages = max(1, file_size_bytes / 50000)
    triage_tokens = min(estimated_pages, 3) * 500    # triage reads first 3 pages
    extraction_tokens = estimated_pages * 500          # extraction reads ALL pages
  elif file_type in ["DOCX", "DOC"]:
    estimated_pages = max(1, file_size_bytes / 25000)
    triage_tokens = min(estimated_pages, 5) * 400
    extraction_tokens = estimated_pages * 400
  elif file_type in ["XLSX", "XLS", "CSV"]:
    # Spreadsheets are token-dense: headers + rows
    triage_tokens = min(2000, file_size_bytes / 10)   # triage reads headers + 20 rows
    extraction_tokens = min(25000, file_size_bytes / 5) # extraction reads ALL sheets
  elif file_type in ["TXT", "MD"]:
    triage_tokens = min(1000, file_size_bytes / 4)     # triage reads first 200 lines
    extraction_tokens = file_size_bytes / 4             # extraction reads all
  else:
    triage_tokens = 1000                                # conservative default
    extraction_tokens = 5000
```

**Step 0.7b** — Calculate per-agent overhead (tokens duplicated in every agent prompt):

```
# These are injected into EVERY agent, so they multiply by agent count
overhead_system_prompt    = 300      # base instructions
overhead_schema           = num_schema_fields * 80   # ~80 tokens per field definition
overhead_integrity_rules  = 500      # 8 data integrity rules
overhead_prism_context    = 0        # default if PRISM not available

if prism_integration:
  # PRISM context includes DD taxonomy, field-to-CCII map, entity guide
  overhead_prism_context = 2000 + (num_schema_fields * 120)  # base + per-field CCII mapping

overhead_per_agent = overhead_system_prompt + overhead_schema + overhead_integrity_rules + overhead_prism_context
```

**Step 0.7c** — Compute optimal agent counts:

```
MAX_PAYLOAD_PER_AGENT = 80000    # tokens — safe working budget per agent context
MIN_AGENTS = 2                    # never go below 2 (parallelism baseline)
MAX_TRIAGE_AGENTS = 15            # hard cap
MAX_EXTRACTION_AGENTS = 7         # hard cap

# ── Phase 1: Triage ──
total_triage_payload = sum(triage_tokens for all files)

# Minimum agents so no agent exceeds context budget
min_triage = max(MIN_AGENTS, ceil(total_triage_payload / MAX_PAYLOAD_PER_AGENT))

# Cost function: total_tokens = (N * overhead_per_agent) + total_triage_payload
# Payload is constant regardless of N, but overhead scales linearly.
# Constraint: per_agent_payload = total_triage_payload / N <= MAX_PAYLOAD_PER_AGENT
# Optimal N = smallest N satisfying the constraint (minimizes overhead)
optimal_triage_agents = clamp(min_triage, MIN_AGENTS, MAX_TRIAGE_AGENTS)

# ── Phase 2: Extraction (estimated — refined after triage) ──
# Use conservative estimate: assume 60% of files pass triage (RELEVANT + MAYBE)
estimated_triaged_files = total_files * 0.6
total_extraction_payload = sum(extraction_tokens for estimated triaged files)

min_extraction = max(MIN_AGENTS, ceil(total_extraction_payload / MAX_PAYLOAD_PER_AGENT))
optimal_extraction_agents = clamp(min_extraction, MIN_AGENTS, MAX_EXTRACTION_AGENTS)
```

**Step 0.7d** — Display token budget plan to user:

```
Token Budget Plan
==================
Per-agent overhead: ~{overhead_per_agent} tokens
  System prompt:    {overhead_system_prompt} tokens
  Schema ({N} fields): {overhead_schema} tokens
  Integrity rules:  {overhead_integrity_rules} tokens
  PRISM context:    {overhead_prism_context} tokens {or "N/A" if not available}

Phase 1 — Triage:
  Total payload:    ~{total_triage_payload} tokens ({total_files} files, first 3 pages each)
  Agents:           {optimal_triage_agents}
  Per-agent payload: ~{total_triage_payload / optimal_triage_agents} tokens
  Total overhead:   ~{optimal_triage_agents * overhead_per_agent} tokens
  Efficiency:       {payload / (payload + overhead) * 100}%

Phase 2 — Extraction (estimated, refined after triage):
  Total payload:    ~{total_extraction_payload} tokens (est. {estimated_triaged_files} files, full read)
  Agents:           {optimal_extraction_agents}
  Per-agent payload: ~{total_extraction_payload / optimal_extraction_agents} tokens
  Total overhead:   ~{optimal_extraction_agents * overhead_per_agent} tokens
  Efficiency:       {payload / (payload + overhead) * 100}%
```

**Step 0.7e** — Save budget plan to `{session-dir}/token-budget.yaml`:

```yaml
token_budget:
  overhead_per_agent: 0
  overhead_breakdown:
    system_prompt: 300
    schema: 0
    integrity_rules: 500
    prism_context: 0

  phase1_triage:
    total_payload_tokens: 0
    optimal_agents: 0
    per_agent_payload: 0
    total_overhead: 0
    efficiency_pct: 0

  phase2_extraction:
    total_payload_tokens: 0
    optimal_agents: 0
    per_agent_payload: 0
    total_overhead: 0
    efficiency_pct: 0
    note: "Estimated — recalculated after triage with actual RELEVANT+MAYBE counts"

  file_estimates:
    - file: "example.pdf"
      size_bytes: 0
      triage_tokens: 0
      extraction_tokens: 0
```

Record `optimal_triage_agents` and `optimal_extraction_agents` in session manifest.

---

### Phase 1: Triage (Fast Scan)

**Goal:** Quickly identify which files are likely to contain answers for schema fields. This avoids deep-reading thousands of irrelevant files.

**Step 1.1** — Read `optimal_triage_agents` from the token budget (Step 0.7).

This value was computed from actual file sizes and per-agent overhead — not a static lookup table.
Bounds: minimum 2, maximum 15 agents.

Partition files across agents using round-robin across directories (each agent sees files from all source directories).

**Step 1.2** — Spawn ALL triage agents in a SINGLE message (`run_in_background: true`).

Each triage agent receives:
- Its assigned file batch
- The full extraction schema (all fields with hints)
- All 8 Data Integrity Rules

Each triage agent MUST, for each assigned file:
- Read the first 3 pages of PDFs, first sheet + headers of spreadsheets, first 200 lines of text files
- Check content against ALL schema field hints
- Score the file:
  - `RELEVANT` — contains likely answers for one or more fields. List which fields.
  - `MAYBE` — ambiguous but could contain answers. List suspected fields.
  - `SKIP` — clearly irrelevant to all schema fields.
- **CONSERVATIVE BIAS**: when in doubt, mark `MAYBE`. False positives are cheap; false negatives lose data.
- Record: filename, relevance score, suspected fields, brief content summary (1-2 sentences)

Triage agent prompt template:
```
You are a Document Triage Agent for the ACOS Data Extractor pipeline.

YOUR TASK: Quickly scan each assigned document and determine if it MIGHT contain
answers for any of the extraction schema fields. You are a FIRST PASS — speed
matters, but NEVER skip a potentially relevant document.

EXTRACTION SCHEMA:
[inject full schema with field IDs, names, types, and hint keywords]

YOUR FILE ASSIGNMENTS:
[list of file paths]

PRISM INDUSTRY CONTEXT (if available):
[inject from {session-dir}/prism-context.yaml — includes:]
- DOCUMENT TYPE AWARENESS: DD taxonomy describing what each document type contains
  (e.g., "CCII 0601 = Appraisal: contains property value, comparables, market analysis")
- FIELD-TO-CATEGORY MAPPING: Which DD categories likely contain each schema field
  (e.g., "loan_origination_date → look in Transaction Docs (29xx) and Closing (30xx)")
- Use this context to improve semantic matching beyond keyword hints. A document
  classified as CCII 0301 (Financial Statements) likely contains currency amounts,
  dates, and entity names even if the schema keywords don't appear verbatim.
[If PRISM not available, omit this section entirely]

TRIAGE RULES:
1. READ actual content — do NOT classify by filename alone
2. For PDFs: read the first 3 pages minimum
3. For DOCX/DOC: read the first 5 pages minimum
4. For spreadsheets: examine ALL sheet names, column headers, and first 20 data rows
5. For text files: read the first 200 lines
6. Match against schema field hints AND semantic meaning (a "closing statement" might
   contain a "payoff amount" even if the word "payoff" doesn't appear)
7. When in doubt, mark MAYBE — we will deep-read it in Phase 2
8. SKIP only when you are CERTAIN the document cannot contain ANY schema field
9. If PRISM context is available: also note the likely CCII code for each file
   (e.g., "This appears to be a CCII 0604 Title Report") — this helps downstream agents

DATA INTEGRITY RULES:
[inject all 8 rules]

OUTPUT: Write YAML to {session-dir}/phase1/triage-agent-{NN}.yaml
using the triage-manifest template structure.
For each file, include: filename, relevance, suspected_fields, content_summary,
and (if PRISM available) estimated_ccii_code.
```

**Step 1.3** — Collect and merge all triage agent outputs into `phase1/triage-manifest.yaml`:

- Combine results across all agents
- Deduplicate (same file should only appear once)
- Build three lists: `RELEVANT`, `MAYBE`, `SKIP`
- For files marked `RELEVANT` or `MAYBE`, aggregate which schema fields they might answer
- Calculate triage statistics: total scanned, relevant count, maybe count, skip count

Display triage summary:
```
Triage Results
===============
Total scanned: 336 files
Relevant: 47 files (likely contain answers)
Maybe: 23 files (ambiguous, will deep-read)
Skip: 266 files (irrelevant)

Deep extraction target: 70 files (21% of corpus)

Field coverage estimate:
  loan_origination_date: 8 candidate files
  property_address: 12 candidate files
  payoff_amount: 5 candidate files
  investor_payments: 3 candidate files
  ...
```

**Step 1.4** — **QA Gate 1 (Triage Completeness)**: Spawn `qa-reviewer` agent (blocking).

The triage QA agent receives:
- The full triage manifest (including SKIP list)
- The extraction schema
- A random sample of 15% of SKIP files (the agent must actually read these)

QA reviewer MUST:
- Read the sampled SKIP files to verify they are genuinely irrelevant
- Check if any schema fields have ZERO candidate files — if so, re-examine SKIP files with those field hints
- Verify that RELEVANT/MAYBE rationale is reasonable

Verdicts:
- **PASS**: SKIP sample verified, all fields have candidates (or genuinely absent)
- **FAIL**: Found relevant files in the SKIP pile, or fields with no candidates that should have candidates

Write verdict to `qa-gates/triage-qa-iteration-1.yaml`.

**Step 1.5** — If FAIL and iteration < 3:
- Re-triage ONLY the files flagged by QA (plus all SKIP files for any zero-candidate fields)
- Merge corrections into triage manifest
- Return to Step 1.4

If FAIL and iteration >= 3: ESCALATE to user with QA findings.

If PASS: proceed to Phase 2.

---

### Phase 2: Deep Extraction

**Goal:** Read every RELEVANT and MAYBE file deeply. Extract exact values for every schema field with full provenance.

**Step 2.1** — Recalculate extraction agent count from actual triage results.

The Phase 0 estimate assumed 60% of files would pass triage. Now we have real numbers,
so recalculate using the actual RELEVANT + MAYBE file list:

```
# Recalculate with actual triaged files (not the 60% estimate from Phase 0)
actual_triaged_files = len(RELEVANT) + len(MAYBE)
actual_extraction_payload = sum(extraction_tokens for file in triaged_files)

# Phase 2 overhead is higher than Phase 1: includes triage manifest context
phase2_overhead = overhead_per_agent + (actual_triaged_files * 30)  # ~30 tokens per triage entry

recalc_min = max(2, ceil(actual_extraction_payload / MAX_PAYLOAD_PER_AGENT))
optimal_extraction_agents = clamp(recalc_min, 2, 7)
```

Update `token-budget.yaml` with the recalculated values.
Log: `"Extraction budget recalculated: {actual_triaged_files} files, {optimal_extraction_agents} agents (was {estimated} from Phase 0)"`

Partition triaged files across agents. Include the triage manifest so each extractor knows which fields each file might contain.

**Step 2.2** — Spawn ALL extractor agents in a SINGLE message (`run_in_background: true`).

Each extractor agent receives:
- Its assigned files (full paths)
- The triage manifest entries for those files (which fields to look for)
- The full extraction schema
- All 8 Data Integrity Rules
- Output format from `templates/extraction-map.yaml`

Each extractor agent MUST, for EVERY schema field:
- Search its assigned documents thoroughly (ALL pages, not just first 3)
- For `multi: true` fields, collect ALL instances (every payment, every date, every entry)
- Record the value EXACTLY as found (no reformatting)
- Record full provenance: source document, page number, section, verbatim quote
- Rate confidence as a percentage (0–100%, rounded to nearest 5%)
- If not found in assigned docs: mark `NOT_IN_ASSIGNED_DOCS`

Extractor agent prompt template:
```
You are a Deep Extraction Agent for the ACOS Data Extractor pipeline.

YOUR TASK: Thoroughly read each assigned document and extract EXACT values for
every schema field. You are the ACCURACY phase — read every page, check every table,
leave no stone unturned.

EXTRACTION SCHEMA:
[inject full schema]

TRIAGE CONTEXT:
[inject triage manifest entries for this agent's files — which fields each file might answer]
[if PRISM available, include estimated CCII codes from triage]

YOUR FILE ASSIGNMENTS:
[list of file paths with triage notes]

PRISM INDUSTRY CONTEXT (if available):
[inject from {session-dir}/prism-context.yaml — includes:]
- DOCUMENT STRUCTURE AWARENESS: For each CCII code identified during triage, inject
  the master DD framework's detailed description and evaluation criteria. This tells
  you what data each document type conventionally contains and where to find it.
  Example: "CCII 0301 (Financial Statements) — look for balance sheets, P&L,
  cash flow statements. Key values typically on first pages with summaries."
- ENTITY RECOGNITION GUIDE: KG node types to watch for — when you encounter
  party names, property addresses, financial instruments, covenants, or risk
  descriptions, note them as structured entities in your output.
- FIELD-TO-CATEGORY MAPPING: Which DD categories are expected to contain each
  schema field. Prioritize searching these document types first.
- EVALUATION CRITERIA: What makes data authoritative in this domain — official
  legal documents over informal correspondence, signed originals over drafts,
  most recent version over older versions.
[If PRISM not available, omit this section entirely]

EXTRACTION RULES:
1. Read the ENTIRE document, not just the first few pages
2. For spreadsheets: check ALL sheets, ALL columns, ALL rows
3. For PDFs with tables: parse table structure carefully, match headers to values
4. For multi-value fields (multi: true): collect EVERY instance with its date/context
5. Copy values CHARACTER-BY-CHARACTER — no rounding, reformatting, or inference
6. Every value MUST have provenance: filename, full absolute path, page, section, verbatim quote
7. If a value requires interpretation (e.g., calculating a total), assign confidence below 60%
   and note the interpretation in the provenance
8. If NOT found in your docs, mark NOT_IN_ASSIGNED_DOCS (another agent may have it)
9. ALWAYS include the full absolute file path for every source document — this enables
   clickable links in the final report
10. If PRISM context is available: tag each extraction with its CCII code source
   (e.g., ccii_source: "0301") and note document authority level

DATA INTEGRITY RULES:
[inject all 8 rules]

OUTPUT: Write YAML to {session-dir}/phase2/extractor-{NN}.yaml
```

**Step 2.3** — Collect and merge all extractor outputs into `phase2/extraction-map.yaml`:

- Combine results across extractors
- For each schema field:
  - If found by one extractor: use that value
  - If found by multiple extractors with SAME value: keep with highest confidence, note corroboration
  - If found by multiple extractors with DIFFERENT values: flag as `CONFLICT`
  - If not found by any extractor: mark `NOT_FOUND` with full search record
- For `multi: true` fields: merge all instances across extractors, deduplicate by value+date
- Preserve original extractor outputs as `phase2/extractor-{NN}.yaml`

**Step 2.4** — Conflict resolution for multi-source fields:

- If values match: keep with highest confidence, note corroboration
- If values conflict, apply resolution hierarchy:
  1. **Recency** — more recent document wins
  2. **Authority** — official/legal documents over informal
  3. **Specificity** — document specific to the field over general document
- If hierarchy cannot resolve: flag as `UNRESOLVED_CONFLICT`
- Write all resolutions to `phase2/conflict-resolutions.yaml`

**Step 2.5** — Generate provenance record (`phase2/provenance-record.yaml`) using `templates/provenance-record.yaml`.

**Step 2.6** — **QA Gate 2 (Adversarial Extraction QA)**: Spawn QA agents in a SINGLE message (`run_in_background: true`). Spawn 3 agents always + 1 Domain Expert if `prism_integration: true` (4 total when PRISM is available):

**QA Agent 1 — Value Verifier** (qa-reviewer model):
```
You are an ADVERSARIAL Value Verifier. Your job is to DISPROVE extracted values.
Assume every extraction is WRONG until you verify it against the source document.

EXTRACTION MAP:
[inject phase2/extraction-map.yaml]

SOURCE DOCUMENTS:
[paths to all triaged files]

FOR EACH EXTRACTED VALUE:
1. Go to the cited source document and page
2. Find the cited verbatim quote — does it exist on that page?
3. Does the extracted value EXACTLY match what's in the document? Character-by-character.
4. For currency: check every digit, decimal, comma
5. For names: check every letter, space, suffix
6. For dates: check format matches source exactly
7. For multi-value fields: verify the COUNT of instances matches reality

VERDICT per field: VERIFIED | INCORRECT | UNVERIFIABLE
Write to: {session-dir}/qa-gates/extraction-qa-value-iteration-{N}.yaml
```

**QA Agent 2 — Completeness Auditor** (qa-reviewer model):
```
You are an ADVERSARIAL Completeness Auditor. Your job is to find MISSED data that
the extractors overlooked.

EXTRACTION MAP:
[inject extraction-map.yaml — including NOT_FOUND fields]

TRIAGE MANIFEST:
[inject triage-manifest.yaml — including SKIP files]

FULL FILE INVENTORY:
[inject complete file list]

YOUR TASKS:
1. For each NOT_FOUND field: pick 5 random SKIP files and actually read them.
   Could any contain the missing data?
2. For each FOUND field: are there ADDITIONAL sources that corroborate or contradict?
3. For multi-value fields: did extractors capture ALL instances, or miss some?
4. Check if any MAYBE files were skipped by extractors

Write to: {session-dir}/qa-gates/extraction-qa-completeness-iteration-{N}.yaml
```

**QA Agent 3 — Provenance Auditor** (qa-reviewer model):
```
You are an ADVERSARIAL Provenance Auditor. Your job is to verify the citation chain.
Every value must trace back to a real location in a real document.

PROVENANCE RECORD:
[inject phase2/provenance-record.yaml]

SOURCE DOCUMENTS:
[paths to cited source documents]

FOR EACH PROVENANCE CHAIN:
1. Open the cited document
2. Go to the cited page number — does that page exist?
3. Find the cited section — does it exist on that page?
4. Read the verbatim quote — is it actually verbatim, or paraphrased/truncated?
5. Does the quote contain the extracted value?
6. Spot-check at least 50% of all citations

VERDICT per citation: VALID | INVALID_PAGE | INVALID_SECTION | MISQUOTED | FABRICATED
Write to: {session-dir}/qa-gates/extraction-qa-provenance-iteration-{N}.yaml
```

**QA Agent 4 — Domain Expert (PRISM-informed)** — Only spawned if `prism_integration: true` in session manifest. Uses qa-reviewer model:
```
You are a Domain Expert QA reviewer with deep knowledge of institutional
due diligence standards. You understand the 252-item DD framework (CCII codes)
and how financial, legal, and real estate documents are structured.

PRISM DD FRAMEWORK REFERENCE:
[inject relevant DD categories with item descriptions and evaluation criteria
from {session-dir}/prism-context.yaml]

EXTRACTION MAP:
[inject phase2/extraction-map.yaml]

FIELD-TO-CCII MAPPING:
[inject field_to_ccii_map from prism-context.yaml]

YOUR REVIEW FOCUS:
1. SOURCE AUTHORITY: For each extracted value, does it come from the
   institutionally correct document type? A loan amount from a term sheet
   (CCII 2902) is more authoritative than from a marketing summary.
2. DD COMPLETENESS: Are there standard DD documents (per the 252-item framework)
   that SHOULD exist in the corpus but were not found? Flag missing documents
   that a senior analyst would expect.
3. CCII CODE ACCURACY: If extractors assigned CCII codes, verify they are correct.
   A "rent roll" is CCII 0701, not 0301. Misclassification could cause downstream
   errors.
4. DOMAIN-SPECIFIC VALIDATION:
   - Financial metrics: Do DSCR, LTV, cap rate values fall within plausible ranges?
   - Dates: Are dates internally consistent (origination before maturity)?
   - Currency: Are amounts in the right order of magnitude for the deal size?
   - Entities: Do party names match across documents (same entity, different references)?
5. INSTITUTIONAL STANDARDS: Would a senior loan officer, underwriter, or IC member
   accept these extractions as sufficient? Flag anything that needs corroboration
   from additional sources.
6. CONFLICT AWARENESS: When multiple sources provide different values, does the
   resolution follow the correct authority hierarchy? (Legal docs > financial
   statements > correspondence > marketing materials)

VERDICT per field: INSTITUTIONAL_PASS | AUTHORITY_CONCERN | DOMAIN_FLAG | COMPLETENESS_GAP
Write to: {session-dir}/qa-gates/extraction-qa-domain-iteration-{N}.yaml
```

**Step 2.7** — Aggregate QA results into `qa-gates/extraction-qa-synthesis-iteration-{N}.yaml` using the template from `templates/qa-synthesis.yaml`:

Collect results from all QA agents (3 standard + 1 domain expert if PRISM enabled).

```yaml
iteration: N
overall_verdict: "PASS | FAIL"
prism_enabled: true|false

value_verification:
  total_checked: 0
  verified: 0
  incorrect: 0
  unverifiable: 0
  flagged_fields: []

completeness_audit:
  not_found_verified: 0
  missed_data_found: 0
  additional_sources: 0
  flagged_fields: []

provenance_audit:
  total_checked: 0
  valid: 0
  invalid: 0
  flagged_citations: []

# Only present when prism_enabled: true
domain_expert_audit:
  total_checked: 0
  institutional_pass: 0
  authority_concerns: 0
  domain_flags: 0
  completeness_gaps: 0
  flagged_fields: []
  missing_dd_documents: []  # DD items that should exist but weren't found

actionable_flags:
  - field_id: ""
    issue: ""
    source_agent: ""  # "value-verifier | completeness-auditor | provenance-auditor | domain-expert"
    action: "re-extract | add-source | fix-provenance | authority-upgrade | user-review"
```

**Step 2.8** — Wigum Loop decision:

**PASS** (zero actionable flags): proceed to Phase 3.

**FAIL + iterations remaining** (iteration < 5):
- Check convergence: if flag count not decreasing for 2+ iterations, warn user
- Re-extract ONLY flagged fields from ONLY the relevant documents
- Include QA feedback in the re-extraction prompt
- Merge corrections into the extraction map
- Re-run QA Gate 2 for affected fields only
- Log: `"Wigum iteration {N}/5: {flag_count} flags, re-extracting {reextract_count} fields"`

**FAIL + max iterations** (iteration = 5):
- Proceed to Phase 3 with current state
- Include all remaining flags in the final report
- Escalate to user:
  > "Extraction completed 5 QA iterations but {flag_count} items remain flagged.
  >
  > Remaining flags:
  > [list each flag with field, issue, and QA recommendation]
  >
  > Options:
  > 1. Accept current extractions as-is
  > 2. Manually review flagged fields
  > 3. Provide additional source directories"
- AWAIT user decision before finalizing

**Convergence Safety:**
If the Wigum loop detects it is stuck (flag count not decreasing for 2+ iterations):
1. Log warning: "Wigum loop may be stuck — flags not decreasing"
2. Identify which specific fields are cycling
3. Escalate those fields to the user mid-loop rather than wasting iterations
4. Continue the loop for non-stuck fields

---

### Phase 3: Final Report

**Step 3.1** — Generate `EXTRACTION_REPORT.md` in the output directory using the structure from `templates/final-report.md`.

The report MUST include:
- Session metadata (ID, date, source folders, schema)
- Executive summary (fields found, not found, conflicts)
- Per-field findings with provenance — **every source document reference MUST be a clickable markdown link** using `[filename](file:///absolute/path/to/file)` format (percent-encode spaces as `%20`)
- Multi-value field tables (for `multi: true` fields) — each entry links to its source
- NOT_FOUND fields with search exhaustion notes
- Conflict resolutions with rationale — link to each conflicting source
- QA summary (iterations, flags resolved, remaining issues)
- Appendix: full file inventory with triage classification — **every filename in the inventory MUST be a clickable link to the actual file**

**Step 3.2** — Generate machine-readable output (`extraction-results.yaml`) using the template from `templates/extraction-results.yaml`:

```yaml
session_id: "DDE-XXXXXXXX-XXXXXX"
extraction_date: "YYYY-MM-DD"
schema_version: "1.0"
prism_enabled: true  # false if PRISM not available
results:
  - field_id: "origination_date"
    field_name: "Loan Origination Date"
    status: "FOUND"
    value: "03/15/2024"
    confidence: 95            # percentage, 0-100, rounded to nearest 5%
    source_file: "closing-disclosure-final.pdf"
    source_path: "/path/to/closing-disclosure-final.pdf"
    source_link: "file:///path/to/closing-disclosure-final.pdf"  # clickable file:// URI
    page: 1
    section: "Date Issued"     # section or area on the page where the value was found
    quote: "Date Issued: 03/15/2024"
    ccii_source: "3001"  # only when prism_enabled: true
    authority_level: "legal_document"  # only when prism_enabled: true

  - field_id: "investor_payments"
    field_name: "Payments to Investors"
    status: "FOUND"
    multi: true
    entries:
      - value: "$127,500.00"
        date: "01/15/2025"
        confidence: 95
        source_file: "distribution-ledger.xlsx"
        source_path: "/path/to/distribution-ledger.xlsx"
        source_link: "file:///path/to/distribution-ledger.xlsx"
        page: "Sheet '2025'"
        section: "Row 14"
        quote: "01/15/2025 | Distribution | $127,500.00"
        ccii_source: "0301"
      - value: "$127,500.00"
        date: "02/15/2025"
        confidence: 95
        source_file: "distribution-ledger.xlsx"
        source_path: "/path/to/distribution-ledger.xlsx"
        source_link: "file:///path/to/distribution-ledger.xlsx"
        page: "Sheet '2025'"
        section: "Row 15"
        quote: "02/15/2025 | Distribution | $127,500.00"
        ccii_source: "0301"

  - field_id: "tax_parcel_id"
    field_name: "Property Tax Parcel ID"
    status: "NOT_FOUND"
    source_file: null
    source_link: null
    documents_searched: 70
    notes: "No tax parcel number found in any source document"
    expected_ccii: "0604"  # only when prism_enabled — where it SHOULD be
    dd_gap: "Title Report (CCII 0604) not found in corpus"
```

**Step 3.3** — Present results to user:

First, print the results table — one row per schema field, sorted by status (FOUND first, then CONFLICT, then NOT_FOUND). **CRITICAL: Every source file MUST be a clickable markdown link** using the format `[filename](file:///absolute/path/to/file)`:

```
Data Extraction Results
========================

| Field                   | Value                        | Confidence | Status      | Source Document                                                              | Location                        |
|-------------------------|------------------------------|------------|-------------|------------------------------------------------------------------------------|---------------------------------|
| Loan Origination Date   | 03/15/2024                   | 95%        | FOUND       | [closing-disclosure-final.pdf](file:///path/to/closing-disclosure-final.pdf) | Page 1, "Date Issued"           |
| Property Address        | 123 Main St, New York, NY    | 90%        | FOUND       | [appraisal-report.pdf](file:///path/to/appraisal-report.pdf)                | Page 3, "Subject Property"      |
| Monthly Investor Pmts   | 12 entries → see report      | 95%        | FOUND       | [distribution-ledger.xlsx](file:///path/to/distribution-ledger.xlsx)         | Sheet '2025', Rows 2-13         |
| Borrower Name           | John A. Smith Jr.            | 75%        | FOUND       | [loan-agreement-signed.pdf](file:///path/to/loan-agreement-signed.pdf)       | Page 1, "Borrower"              |
| Payoff Amount           | $1,450,000.00                | 70%        | CONFLICT    | [payoff-letter.pdf](file:///path/to/payoff-letter.pdf) (resolved)            | Page 1, "Total Due"             |
| Tax Parcel ID           | —                            | —          | NOT FOUND   | —                                                                            | (70 files searched)             |
```

**Clickable link format rules:**
- Use markdown links: `[display-name](file:///absolute/path)`
- The display name MUST be the filename (not the full path) for readability
- The link target MUST be the full absolute `file://` URI so it opens in the user's default app
- Spaces in paths must be percent-encoded: space → `%20`
- Example: `[Settlement Statement.pdf](file:///Users/zee/Dropbox/Loans/Settlement%20Statement.pdf)`
- For multi-source fields (corroborated by multiple documents), list all sources as separate links

Confidence: 90–100% = exact match, unambiguous source · 60–89% = requires interpretation · below 60% = ambiguous or partial

Then print the session summary:

```
Data Extraction Complete
=========================
Session: DDE-XXXXXXXX-XXXXXX
Output:  {output-dir}/
Report:  {output-dir}/EXTRACTION_REPORT.md
Data:    {output-dir}/extraction-results.yaml

Results: 10/12 fields found (83%)
  Found:     10 fields (8 high confidence, 2 medium)
  Not Found:  1 field (tax_parcel_id)
  Conflicts:  1 field resolved (payoff_amount — recency rule applied)

Corpus: 336 files scanned → 70 triaged → 47 contributed data
QA: PASSED after 2 Wigum iterations

Action required: 1 field NOT_FOUND — see report for details.
```

Update `session-manifest.yaml` with final status.

---

## Error Handling

| Stage | Error | Response |
|-------|-------|----------|
| Phase 0 | Folder not found | Report error, prompt for correct path |
| Phase 0 | No supported files in folder | Report error, list found file types |
| Phase 0 | Schema parse error | Show specific parse error, prompt to fix |
| Phase 1 | Triage agent fails | Retry once with same batch, then redistribute to other agents |
| Phase 1 | All files marked SKIP | Warn user — schema may not match document contents. Ask to refine schema. |
| Phase 2 | Extractor agent fails | Retry once, then redistribute files |
| Phase 2 | Document unreadable | Log as `UNREADABLE`, exclude from extraction, note in report |
| Phase 2 | Spreadsheet too large | Process sheet-by-sheet rather than whole file |
| QA Gate | QA reviewer crashes | Mark as INCONCLUSIVE (blocks like FAIL), retry gate once |
| Wigum | Max iterations reached | Escalate to user with full context |
| Wigum | Convergence stuck | Escalate stuck fields to user, continue loop for others |
| Any | Model resolution fails | Fall back to hardcoded defaults |
| Phase 0 | PRISM data directory not found | Log info, set `prism_integration: false`, proceed with keyword-only mode |
| Phase 0 | PRISM files partially missing | Load what's available, skip missing components, log warnings |
| QA Gate 2 | Domain Expert agent crashes | Mark as INCONCLUSIVE but do NOT block — standard 3 QA agents still govern pass/fail |

---

## Schema Field Types Reference

| Type | Description | Example Value |
|------|-------------|---------------|
| `text` | Free-form text | "John Smith Jr." |
| `date` | Any date format | "03/15/2024" |
| `currency` | Monetary amount | "$1,234,567.89" |
| `number` | Numeric value | "4.75" |
| `percentage` | Percentage | "4.75%" |
| `address` | Physical address | "123 Main St, Suite 400, New York, NY 10001" |
| `phone` | Phone number | "(555) 123-4567" |
| `email` | Email address | "john@example.com" |
| `boolean` | Yes/No value | "Yes" |
| `currency_with_date` | Amount + associated date | "$127,500.00 on 01/15/2025" |
| `text_list` | Multiple text values | ["Item 1", "Item 2"] |

For any type, set `multi: true` to collect all instances rather than just the first match.

---

## Data Flow Reference

```
PRISM Data ── DD taxonomy + master framework + KG schema ──→ Phase 0 (build prism-context.yaml)
                                                            ↓
Phase 0 ── file inventory + schema + PRISM context ──→ Phase 1 (what to find, where to look, what docs mean)

Phase 1 ── triage-manifest.yaml (with CCII codes) ──→ Phase 2 (which files to read, what to extract)

Phase 2 ── extraction-map.yaml (with CCII sources) ──→ QA Gate 2 (verify values, completeness, provenance, domain)

QA Gate 2 ── qa-synthesis.yaml ──→ Phase 2 (re-extract flagged, if Wigum loop)
          or ──→ Phase 3 (final report, if PASS or max iterations)
```

*ACOS Data Extractor — Schema-driven, multi-agent extraction with PRISM industry intelligence, adversarial QA, and iterative refinement.*
