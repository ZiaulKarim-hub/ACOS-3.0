---
name: acos-credit-memo-generator
description: |
  Multi-phase swarm-based credit memo generation. Extracts design patterns
  and benchmarks from example memos, analyzes loan folders, generates credit
  memos via parallel designer agents, and validates against benchmarks with
  iterative feedback loops.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# ACOS Credit Memo Generator

## Purpose

Generate institutional-quality credit memos from loan folders using a 4-phase swarm pipeline:
1. **Extract** — Learn design patterns and benchmarks from example credit memos
2. **Analyze** — Deep-read the loan folder and extract all relevant data
3. **Design** — Write the credit memo section-by-section following learned patterns
4. **Validate** — Check against benchmarks, iterate until passing (Wigum loop)

## Phase 0: Argument Parsing & Configuration

### Step 0.0: Model Selection (Token Savings)

Before parsing arguments (unless `$ARGUMENTS` is `status`), present this choice:

```
╔══════════════════════════════════════════════════════════════╗
║  Model Selection — This skill uses many tokens              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] Claude (current profile) — Higher quality               ║
║  [2] GLM-5 via OpenRouter    — Saves Claude tokens           ║
║  [3] GLM-5 Heavy             — Maximum Claude token savings  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

Based on user choice:
- **Choice 1**: No change. Continue with current model profile.
- **Choice 2**: Run `bash .claude/scripts/set-skill-model.sh glm-review`
- **Choice 3**: Run `bash .claude/scripts/set-skill-model.sh glm-heavy`

Then continue to Step 0.1.

### Step 0.1: Parse Arguments

Parse `$ARGUMENTS` to determine the execution mode:

| Command | Mode | Phases Run |
|---------|------|------------|
| `/acos-credit-memo-generator extract [examples-path]` | Extract only | Phase 1 |
| `/acos-credit-memo-generator generate [loan-folder-path]` | Generate only | Phases 2-4 (requires cached extraction) |
| `/acos-credit-memo-generator [loan-folder-path]` | Full run | Phase 1 (if no cache) → 2 → 3 → 4 |
| `/acos-credit-memo-generator status` | Status | Show cached extractions and sessions |

If no arguments provided, prompt the user for the loan folder path.

### Step 0.2: Bootstrap Configuration

Check for `.acos/seos/config.yaml`. If it does not exist:

1. Create the `.acos/seos/` directory structure:
   ```
   .acos/seos/
   ├── config.yaml
   ├── extractions/
   └── sessions/
   ```

2. Copy the template: `!cat templates/seos-config.yaml` → `.acos/seos/config.yaml`

3. Prompt the user to configure:
   - `examples_path` — directory containing example credit memos
   - `loan_folder_base` — base path for loan folders
   - Review `memo_sections` — confirm or customize the section list

4. Write updated config to `.acos/seos/config.yaml`

If config exists, read it and validate paths exist.

### Step 0.3: Route to Phase

Based on the parsed mode:

- **`status`** → Display status report and exit (see Status section below)
- **`extract`** → Jump to Phase 1
- **`generate`** → Verify extraction cache exists at `.acos/seos/extractions/`, then jump to Phase 2
- **Full run** → Check extraction cache. If exists and user confirms reuse, skip to Phase 2. Otherwise start at Phase 1.

Generate a session ID: `YYYYMMDD-HHMMSS` (e.g., `20260302-143022`)

---

## Phase 1: Extraction (Two Parallel Swarm Tracks)

Phase 1 extracts design patterns and benchmark criteria from example credit memos. Results are cached and reusable across loan folders.

### Step 1.1: Inventory Examples

1. Read the `examples_path` from config
2. Glob for documents: `**/*.{pdf,docx,doc,md,txt}` in the examples path
3. List all found documents with file sizes and types
4. If more than `max_design_agents` (default 10), ask the user which to include or truncate to the most recent

Store the inventory for reference:
```yaml
# .acos/seos/extractions/{session-id}/plan.md
extraction_id: "{session-id}"
date: "YYYY-MM-DD"
examples_path: "[path]"
documents:
  - filename: ""
    path: ""
    size: ""
    type: ""
```

### Step 1.2: Launch Dual-Track Extraction Swarms

**CRITICAL: Both tracks MUST be launched simultaneously in a SINGLE message.** This means all design extractor agents AND all benchmark extractor agents are spawned in one batch of parallel `Task()` / `Bash()` calls.

**Before spawning any agent, resolve its model:**
```bash
RESOLVED=$(bash .claude/scripts/resolve-agent-model.sh developer)
```

For synthesizer agents:
```bash
SYNTH_MODEL=$(bash .claude/scripts/resolve-agent-model.sh architect)
```

For each agent, check whether `$RESOLVED` contains `:` to determine dispatch path.

---

#### Track A — Design Extractors (1 agent per example document)

For each example document, spawn one agent:

**Claude dispatch** (no `:` in resolved model):
```
Task(general-purpose)
  - run_in_background: true
  - model: $RESOLVED
  - prompt: |
      You are a Design Pattern Extractor for credit memo analysis.

      TASK: Analyze this example credit memo and extract design patterns.

      DOCUMENT: [read and include full document content]
      DOCUMENT PATH: [path]

      Extract the following into YAML format matching this schema:
      [include contents of templates/design-pattern.yaml]

      Focus on:
      1. Section structure — names, order, typical length, content type
      2. Formatting — headers, tables, numbers, dates, percentages, bullets
      3. Language — tone, point of view, tense, notable phrases, hedging
      4. Data presentation — how financials are introduced, comparisons, risk, recommendations

      Be EXHAUSTIVE. Every pattern you identify helps downstream designers produce
      accurate credit memos.

      Write your output to: .acos/seos/extractions/{session-id}/design/agent-{NN}/findings.yaml
```

**External dispatch** (`:` in resolved model):
```
Bash(run_in_background: true):
  python3 .claude/scripts/run-external-agent.py \
    --agent developer \
    --model "$RESOLVED" \
    --task "[full prompt as above, with document content pre-read and embedded]" \
    --context [document path]
```
For external agents, pre-read the document content and include it in `--task`. Write the output file yourself after receiving the response.

---

#### Track B — Benchmark Extractors (1 agent per dimension)

Read `benchmark_dimensions` from config (default 7 dimensions). For each dimension, spawn one agent that analyzes ALL example documents:

**Claude dispatch:**
```
Task(general-purpose)
  - run_in_background: true
  - model: $RESOLVED
  - prompt: |
      You are a Benchmark Criterion Extractor for credit memo quality assurance.

      TASK: Analyze ALL provided example credit memos and extract testable
      benchmark criteria for the dimension: [DIMENSION NAME]

      EXAMPLE DOCUMENTS:
      [read and include content of ALL example documents]

      Extract criteria into YAML format matching this schema:
      [include contents of templates/benchmark-criterion.yaml]

      Rules:
      1. Every criterion MUST be objectively testable (no subjective judgments)
      2. Each criterion needs: clear pass condition, clear fail condition, test method
      3. Classify severity: required (must pass), recommended (should pass), nice-to-have
      4. Include specific examples from the source documents
      5. Criteria must be ACTIONABLE — a writer should know exactly what to do

      Dimension focus: [DIMENSION NAME]
      [Add dimension-specific guidance based on the dimension name]

      Write your output to: .acos/seos/extractions/{session-id}/benchmarks/agent-{NN}/findings.yaml
```

**External dispatch:** Same pattern as Track A — pre-read all documents, embed in `--task`.

---

### Step 1.3: Collect Track Results

Wait for ALL agents to complete. For each agent:
- If it completed successfully, read its output file and validate YAML structure
- If it crashed or returned no output, log the failure and note the gap

**Do NOT proceed until all agents have reported.** Missing results mean incomplete patterns/benchmarks.

### Step 1.4: Synthesize — Design Patterns

Resolve the synthesizer model:
```bash
SYNTH_MODEL=$(bash .claude/scripts/resolve-agent-model.sh architect)
```

Spawn the design synthesizer:

```
Task(general-purpose)
  - model: $SYNTH_MODEL
  - prompt: |
      You are the Design Pattern Synthesizer for credit memo generation.

      TASK: Merge all design extraction findings into a single canonical
      design patterns document.

      INDIVIDUAL FINDINGS:
      [read and include ALL files from .acos/seos/extractions/{session-id}/design/agent-*/findings.yaml]

      Produce a unified design-patterns.yaml with:
      1. CANONICAL SECTIONS — merged section list with consensus ordering,
         resolving conflicts by majority vote across examples
      2. GLOBAL STYLE GUIDE — unified formatting, language, and data presentation
         conventions. Where examples disagree, note the predominant pattern
         and flag variants.
      3. SECTION-SPECIFIC GUIDANCE — for each canonical section, specific
         instructions on structure, length, tone, and content expectations

      Write output to: .acos/seos/extractions/{session-id}/design/synthesis/design-patterns.yaml
```

### Step 1.5: Synthesize — Benchmark Criteria

Spawn the benchmark synthesizer (can run in parallel with Step 1.4):

```
Task(general-purpose)
  - model: $SYNTH_MODEL
  - prompt: |
      You are the Benchmark Criteria Synthesizer for credit memo validation.

      TASK: Merge all benchmark extraction findings into a single unified
      benchmark criteria document.

      INDIVIDUAL FINDINGS:
      [read and include ALL files from .acos/seos/extractions/{session-id}/benchmarks/agent-*/findings.yaml]

      Produce a unified benchmark-criteria.yaml with:
      1. UNIQUE CRITERION IDs — format: DIM-NNN (e.g., SEC-001 for Required Sections)
      2. DEDUPLICATED CRITERIA — merge overlapping criteria across dimensions
      3. SEVERITY CLASSIFICATION — required / recommended / nice-to-have
      4. SECTION MAPPING — which memo section(s) each criterion applies to
      5. CROSS-CUTTING CRITERIA — criteria that span multiple sections (e.g., consistency)

      Every criterion must have: id, name, description, severity, applies_to,
      test_method, pass_condition, fail_condition.

      Write output to: .acos/seos/extractions/{session-id}/benchmarks/synthesis/benchmark-criteria.yaml
```

### Step 1.6: Write Extraction Manifest

After both synthesizers complete, write the manifest:

```yaml
# .acos/seos/extractions/{session-id}/manifest.yaml
extraction_id: "{session-id}"
date: "YYYY-MM-DD HH:MM:SS"
examples_path: "[path]"
document_count: N
documents:
  - filename: ""
    path: ""
design_agents: N
benchmark_agents: N
design_patterns: ".acos/seos/extractions/{session-id}/design/synthesis/design-patterns.yaml"
benchmark_criteria: ".acos/seos/extractions/{session-id}/benchmarks/synthesis/benchmark-criteria.yaml"
status: "complete"
```

Report to user:
- Number of design patterns extracted
- Number of benchmark criteria by severity
- Any gaps or warnings from failed agents

If mode is `extract`, **stop here**. Otherwise continue to Phase 2.

---

## Phase 2: Loan Folder Analysis (Swarm)

### Step 2.1: Inventory Loan Folder

1. Read the loan folder path from arguments (or config `loan_folder_base` + subfolder)
2. Glob for all documents: `**/*.{pdf,docx,doc,xlsx,xls,csv,txt,md,jpg,png,tif}`
3. Classify each document by type based on filename patterns and content sampling:
   - `financial-statement` — P&L, balance sheet, cash flow
   - `appraisal` — property valuations, assessments
   - `tax-return` — federal/state tax filings
   - `legal-doc` — loan agreements, guarantees, UCC filings, title
   - `insurance` — policies, certificates, binders
   - `environmental` — Phase I/II reports, environmental assessments
   - `borrower-application` — applications, personal financial statements
   - `third-party-report` — market studies, engineering reports, inspections
   - `other` — anything that doesn't fit the above

4. Create the session workspace:
   ```
   .acos/seos/sessions/{session-id}/
   ├── phase2-analysis/
   ├── phase3-design/
   ├── phase4-validation/
   └── output/
   ```

5. Display the inventory to the user and confirm before proceeding.

### Step 2.2: Determine Analyzer Strategy

Read `analyzer_strategy` from config:
- `per-doc` — 1 agent per document (use for small folders)
- `by-type` — group documents by classification type (use for large folders)
- `auto` (default) — if document count > `auto_strategy_threshold` (default 10), use `by-type`; otherwise `per-doc`

Calculate agent count: clamp between `min_analyzers` (3) and `max_analyzers` (15).

### Step 2.3: Load Extraction Context

Read the cached extraction results:
- `.acos/seos/extractions/{extraction-id}/design/synthesis/design-patterns.yaml` — tells analyzers WHAT data to look for
- The canonical sections list from design patterns — tells analyzers HOW to organize findings

If using a different extraction session than the current one, read the latest `manifest.yaml` from `.acos/seos/extractions/` (sort by date, pick newest with `status: complete`).

### Step 2.4: Launch Analyzer Swarm

Resolve the model:
```bash
RESOLVED=$(bash .claude/scripts/resolve-agent-model.sh developer)
```

**Spawn ALL analyzer agents simultaneously in a SINGLE message:**

For each agent (per-doc or per-type-group):

**Claude dispatch:**
```
Task(general-purpose)
  - run_in_background: true
  - model: $RESOLVED
  - prompt: |
      You are a Loan Document Analyzer for credit memo generation.

      TASK: Extract all data relevant to credit memo generation from the
      assigned document(s).

      ASSIGNED DOCUMENTS:
      [read and include document content]

      DESIGN PATTERNS (what data to look for):
      [include design-patterns.yaml — specifically the canonical sections
       and section-specific data expectations]

      MEMO SECTIONS TO MAP DATA TO:
      [list sections from config]

      Extract into YAML format matching this schema:
      [include contents of templates/loan-data-extract.yaml]

      Rules:
      1. Extract EXACT values — never round, estimate, or interpret
      2. Record the source document and page for every data point
      3. Map every fact to one or more memo sections
      4. Flag any contradictions or inconsistencies across documents
      5. Note missing data — what SHOULD be here based on the design patterns but isn't
      6. Extract ALL entities (people, organizations, properties, loans)
      7. Extract ALL financial figures with exact values and units
      8. Extract ALL risk factors and conditions

      Write output to: .acos/seos/sessions/{session-id}/phase2-analysis/agent-{NN}/extract.yaml
```

**External dispatch:** Pre-read documents and embed in `--task`.

### Step 2.5: Collect and Synthesize Loan Data

Wait for all analyzers to complete, then spawn the synthesizer:

```
Task(general-purpose)
  - model: $SYNTH_MODEL
  - prompt: |
      You are the Loan Data Synthesizer for credit memo generation.

      TASK: Merge all analyzer findings into a single unified loan data document.

      INDIVIDUAL EXTRACTIONS:
      [read and include ALL files from .acos/seos/sessions/{session-id}/phase2-analysis/agent-*/extract.yaml]

      Produce a unified loan-data.yaml with:
      1. MERGED DATA BY SECTION — all facts organized by memo section, deduplicated
      2. ENTITY DIRECTORY — all entities with roles and relationships
      3. FINANCIAL FIGURES — all financials in a single sortable table
      4. RISK FACTORS — consolidated risk register
      5. CONDITIONS — all conditions/covenants in one list
      6. CROSS-REFERENCE ISSUES — contradictions across documents
      7. DATA COMPLETENESS — per-section assessment of what's available vs. expected

      When multiple agents extracted the same fact, keep the one with higher
      confidence. Flag any conflicting values for the same data point.

      Write output to: .acos/seos/sessions/{session-id}/phase2-analysis/synthesis/loan-data.yaml
```

Report to user:
- Documents analyzed
- Data completeness per section
- Any cross-reference issues found
- Entity count and financial figure count

---

## Phase 3: Design (Section-Based Swarm)

### Step 3.1: Prepare Design Context

Read:
- Design patterns: `.acos/seos/extractions/{extraction-id}/design/synthesis/design-patterns.yaml`
- Loan data: `.acos/seos/sessions/{session-id}/phase2-analysis/synthesis/loan-data.yaml`
- Memo sections from config
- Current iteration number (1 for first pass)
- Previous-iteration feedback (if iteration > 1, from Phase 4)

### Step 3.2: Determine Sections to Write

- **Iteration 1:** All sections are written from scratch
- **Iteration 2+:** Only sections with FAIL feedback are rewritten. Passing sections are carried forward unchanged from the previous iteration.

Read the sections list. For iteration > 1, read the validation report from the previous iteration to identify which sections need rewriting.

### Step 3.3: Launch Designer Swarm

Resolve the model:
```bash
RESOLVED=$(bash .claude/scripts/resolve-agent-model.sh developer)
```

**Spawn ALL designer agents simultaneously in a SINGLE message:**

For each section that needs writing:

**Claude dispatch:**
```
Task(general-purpose)
  - run_in_background: true
  - model: $RESOLVED
  - prompt: |
      You are a Credit Memo Section Designer.

      TASK: Write the "[SECTION NAME]" section of a credit memo.

      SECTION ASSIGNMENT: [SECTION NAME]

      DESIGN PATTERNS FOR THIS SECTION:
      [include section-specific guidance from design-patterns.yaml]

      GLOBAL STYLE GUIDE:
      [include formatting, language, and data presentation conventions]

      LOAN DATA FOR THIS SECTION:
      [include ONLY the data mapped to this section from loan-data.yaml]

      ENTITY DIRECTORY:
      [include entity directory for reference]

      [IF ITERATION > 1:]
      PREVIOUS DRAFT OF THIS SECTION:
      [include the previous iteration's version of this section]

      FEEDBACK TO ADDRESS:
      [include section-scoped feedback from Phase 4 validation]

      INSTRUCTIONS:
      1. Follow the design patterns EXACTLY — match the tone, formatting,
         structure, and conventions from the examples
      2. Use ONLY data from the provided loan data — do not fabricate
      3. Where data is unavailable, use the marker: [DATA NOT AVAILABLE]
      4. Maintain consistency with entity names and financial figures
      5. Write in the established voice and tense from the style guide
      [IF ITERATION > 1:]
      6. Address ALL feedback items. Do not ignore any.
      7. Preserve parts of the previous draft that were not flagged

      Write the section content (markdown) to:
      .acos/seos/sessions/{session-id}/phase3-design/iteration-{N}/agent-{NN}/section.md
```

**External dispatch:** Pre-read all context, embed in `--task`.

### Step 3.4: Assemble Credit Memo Draft

Wait for all designers to complete, then spawn the assembler:

```
Task(general-purpose)
  - model: $SYNTH_MODEL
  - prompt: |
      You are the Credit Memo Assembler.

      TASK: Assemble individual sections into a complete credit memo draft.

      SECTIONS (ordered by canonical section list):
      [For each section in the canonical order:
        - If written this iteration: read from phase3-design/iteration-{N}/agent-{NN}/section.md
        - If carried forward: read from the previous iteration's assembled draft]

      DESIGN PATTERNS:
      [include the canonical section ordering and global style guide]

      ENTITY DIRECTORY:
      [include for cross-referencing]

      Assemble the credit memo:
      1. Order sections according to the canonical sequence
      2. Add a title header and table of contents
      3. Check for cross-section inconsistencies:
         - Entity names used consistently?
         - Financial figures match across sections?
         - Dates and terms consistent?
         - No contradictory statements?
      4. Flag any inconsistencies as assembler notes (do NOT fix them —
         that's for the designers in the next iteration)
      5. Add page breaks between major sections

      Write the assembled draft to:
      .acos/seos/sessions/{session-id}/phase3-design/iteration-{N}/synthesis/credit-memo-draft.md

      Write any cross-section issues to:
      .acos/seos/sessions/{session-id}/phase3-design/iteration-{N}/synthesis/assembler-notes.yaml
```

Report to user:
- Sections written vs. carried forward
- Any cross-section inconsistencies found
- Draft location

---

## Phase 4: Validation + Wigum Loop

### Step 4.1: Load Validation Context

Read:
- Credit memo draft: `.acos/seos/sessions/{session-id}/phase3-design/iteration-{N}/synthesis/credit-memo-draft.md`
- Benchmark criteria: `.acos/seos/extractions/{extraction-id}/benchmarks/synthesis/benchmark-criteria.yaml`
- Loan data (ground truth): `.acos/seos/sessions/{session-id}/phase2-analysis/synthesis/loan-data.yaml`
- Assembler notes (if any): `.acos/seos/sessions/{session-id}/phase3-design/iteration-{N}/synthesis/assembler-notes.yaml`
- Current iteration number
- Previous iteration's failure count (for convergence tracking)

### Step 4.2: Launch Validator Swarm

Resolve the model (validators use qa-reviewer role — adversarial):
```bash
RESOLVED=$(bash .claude/scripts/resolve-agent-model.sh qa-reviewer)
```

Group benchmark criteria by dimension. **Spawn ALL validator agents simultaneously in a SINGLE message:**

For each benchmark dimension:

**Claude dispatch:**
```
Task(general-purpose)
  - run_in_background: true
  - model: $RESOLVED
  - prompt: |
      You are a Credit Memo Benchmark Validator.
      You are ADVERSARIAL — your job is to find failures, not confirm success.

      TASK: Validate the credit memo draft against benchmark criteria for
      the dimension: [DIMENSION NAME]

      FULL CREDIT MEMO DRAFT:
      [include the complete draft — validators check EVERYTHING]

      BENCHMARK CRITERIA FOR THIS DIMENSION:
      [include only criteria for this dimension from benchmark-criteria.yaml]

      GROUND TRUTH (loan data):
      [include loan-data.yaml for accuracy verification]

      ASSEMBLER NOTES:
      [include if present — known cross-section issues]

      For each criterion, produce a result matching this schema:
      [include contents of templates/validation-result.yaml]

      Rules:
      1. Check EVERY criterion — do not skip any
      2. Be STRICT — if in doubt, mark FAIL
      3. For FAIL results, provide SPECIFIC evidence (quote the draft)
      4. For FAIL results, provide ACTIONABLE fix instructions
      5. Scope fix instructions to specific sections
      6. Check accuracy against ground truth — any fabricated data is an automatic FAIL
      7. [DATA NOT AVAILABLE] markers are acceptable if the data truly isn't in the loan folder
      8. Cross-cutting criteria (consistency, formatting) require checking ALL sections

      Write output to:
      .acos/seos/sessions/{session-id}/phase4-validation/iteration-{N}/agent-{NN}/result.yaml
```

**External dispatch:** Pre-read all context, embed in `--task`.

### Step 4.3: Aggregate Validation Results

Wait for all validators, then aggregate:

```
Task(general-purpose)
  - model: $SYNTH_MODEL
  - prompt: |
      You are the Validation Aggregator for credit memo quality assurance.

      TASK: Aggregate all validation results into a unified report.

      INDIVIDUAL RESULTS:
      [read and include ALL files from phase4-validation/iteration-{N}/agent-*/result.yaml]

      Produce a validation-report.yaml with:

      overall:
        iteration: N
        total_criteria: [count]
        passed: [count]
        failed: [count]
        pass_rate: "[percentage]"
        required_failures: [count of FAIL with severity=required]
        verdict: "PASS|FAIL"

      by_dimension:
        [dimension_name]:
          passed: N
          failed: N
          verdict: "PASS|FAIL"

      failures:
        - criterion_id: ""
          criterion_name: ""
          severity: ""
          dimension: ""
          affected_sections: []
          failure_detail: ""
          fix_instruction: ""

      feedback_by_section:
        [section_name]:
          - criterion_id: ""
            instruction: ""
            severity: ""

      convergence:
        previous_failure_count: [from previous iteration, or null]
        current_failure_count: [this iteration]
        improving: true|false
        stuck: true|false  # true if failure count increased or didn't change

      Write to: .acos/seos/sessions/{session-id}/phase4-validation/iteration-{N}/synthesis/validation-report.yaml
```

### Step 4.4: Decision Gate (Wigum Loop)

Read the validation report. Apply the following decision logic:

**Case 1: ALL PASS** (zero required failures)
```
→ Copy the draft to: .acos/seos/sessions/{session-id}/output/credit-memo-final.md
→ If config.output.include_validation_report: copy validation report alongside
→ Report SUCCESS to user with final memo location
→ DONE
```

**Case 2: FAIL + iterations remaining** (iteration < max_iterations from config)
```
→ Check convergence: if stuck (failure count not decreasing), warn user
→ Extract feedback_by_section from validation report
→ Identify which sections need rewriting (only those with feedback)
→ Log: "Wigum loop iteration {N}/{max}: {failure_count} failures, rewriting {section_count} sections"
→ Loop back to Phase 3, Step 3.1 with:
    - iteration = iteration + 1
    - sections_to_rewrite = [sections with feedback]
    - feedback = feedback_by_section from validation report
```

**Case 3: FAIL + max iterations reached**
```
→ Copy current draft to: .acos/seos/sessions/{session-id}/output/credit-memo-final.md
→ Copy validation report alongside
→ Escalate to user:
    "Credit memo completed {max_iterations} validation iterations but still has
     {failure_count} required benchmark failures.

     Current draft: [path]
     Validation report: [path]

     Remaining failures:
     [list each required failure with section and fix instruction]

     Options:
     1. Accept the current draft as-is
     2. Manually edit the draft and re-run validation
     3. Increase max_iterations in config and re-run"
→ DONE (await user decision)
```

### Convergence Safety

If the Wigum loop detects it is stuck (failure count not decreasing for 2+ consecutive iterations):

1. Log a warning: "Wigum loop may be stuck — failures not decreasing"
2. Check if the same criteria are failing repeatedly with the same feedback
3. If stuck criteria are cross-cutting (consistency, formatting), try giving the assembler stronger merge instructions on the next iteration
4. If truly stuck after max iterations, include a "stuck criteria" section in the escalation to help the user understand which benchmarks may need manual resolution

---

## Status Command

When mode is `status`, display:

```
SEOS Credit Memo Status
========================

Configuration: .acos/seos/config.yaml
  Examples path: [path or "not configured"]
  Loan folder base: [path or "not configured"]
  Max iterations: [N]
  Memo sections: [count]

Cached Extractions:
  [For each extraction in .acos/seos/extractions/*/manifest.yaml:]
  - {id} | {date} | {document_count} docs | {status}
    Design patterns: {design_agents} agents → [synthesized/pending]
    Benchmarks: {benchmark_agents} agents → [synthesized/pending]

Generation Sessions:
  [For each session in .acos/seos/sessions/*/:]
  - {id} | Phase {current_phase} | Iteration {N}/{max}
    Loan folder: [path]
    Status: [in-progress/complete/escalated]
    Output: [path if complete]
```

---

## Data Flow Reference

```
Phase 1 ─┬─ design-patterns.yaml ──→ Phase 2 (tells analyzers WHAT to look for)
          │                       ──→ Phase 3 (style guide for designers)
          └─ benchmark-criteria.yaml ──→ Phase 4 (testable checks for validators)

Phase 2 ─── loan-data.yaml ──→ Phase 3 (raw material for designers)
                             ──→ Phase 4 (ground truth for accuracy checks)

Phase 3 ─── credit-memo-draft.md ──→ Phase 4 (what to validate)

Phase 4 ─── feedback_by_section ──→ Phase 3 (next iteration, if FAIL)
         or ─── DONE (if PASS or max iterations)
```

---

*ACOS Credit Memo Generator — Swarm-based generation with benchmark-driven quality assurance.*
