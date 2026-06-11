---
name: acos-loan-doc-mapper
description: "High-accuracy loan document mapping. Extracts fields from target form, maps answers from loan folder with provenance, produces completed document. Three-phase pipeline with adversarial QA gates."
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
context: fork
agent: architect
---

# Loan Document Mapper

## Overview

Maps information from a **loan folder** (containing source documents like appraisals, tax returns, bank statements, credit reports, etc.) to a **target loan form/document** that needs to be filled. Designed for financial document pipelines where **100% accuracy is legally required** — no fabricated data, no rounding, no guessing.

Three-phase pipeline with adversarial QA gates at every phase boundary. Multiple agents work in parallel for extraction. A QA reviewer with binary YES/NO checklists validates each phase before proceeding. Failed QA triggers a retry loop (max 3 iterations) before escalating to the user.

```
Phase 0: Init            -> Validate inputs, inventory loan folder
Phase 1: Field Discovery -> Extract ALL fields from target form + inventory sources
  |-- QA Gate 1          -> Binary checklist (12 criteria), retry loop
Phase 2: Answer Extraction -> Find answers from loan folder for every field
  |-- QA Gate 2          -> Binary checklist (12 criteria), retry loop
Phase 3: Document Population -> Fill the form + final verification
  |-- QA Gate 3          -> Binary checklist (10 criteria), retry loop
```

### Pre-flight: Auto-Bootstrap

Before proceeding, ensure ACOS is initialized in this project:

```bash
bash .claude/scripts/acos-preflight.sh
```

This is idempotent — it exits immediately if ACOS is already initialized. If not, it runs the full bootstrap (symlinks, directories, config, gitignore).

## Data Integrity Rules

**INJECT THESE RULES into every agent prompt in every phase.** These are non-negotiable for financial document accuracy.

1. **NO FABRICATION** — Never create, infer, estimate, or guess values. If a value cannot be found in the source documents, use `NOT_FOUND`. No exceptions.
2. **EXACT NUMERICAL PRESERVATION** — Copy numbers character-by-character from the source. No rounding, no reformatting, no unit conversion. `$1,234,567.89` stays exactly `$1,234,567.89`.
3. **EXACT NAME PRESERVATION** — Preserve capitalization, spacing, suffixes (Jr., Sr., III, LLC, Inc., Corp.), and all punctuation exactly as written.
4. **EXACT DATE PRESERVATION** — Copy dates in their source format. No conversion between formats (e.g., do NOT convert `03/15/2024` to `March 15, 2024`).
5. **PROVENANCE REQUIRED** — Every extracted value MUST cite: source document filename, page number, section/area on the page, and a verbatim quote of the surrounding context.
6. **NOT_FOUND PROTOCOL** — When a value cannot be found: list ALL documents searched, confirm the data is genuinely absent (not just in an unexpected location), and mark as `NOT_FOUND`.
7. **CONFLICT PROTOCOL** — When multiple sources provide different values for the same field: flag the conflict, record ALL values with their sources, apply the resolution hierarchy (recency > authority > specificity), and document the rationale.
8. **CONFIDENCE HONESTY** — Rate confidence as `high` (exact match, clear source), `medium` (requires interpretation or context), or `low` (ambiguous source, partial match). Never inflate confidence.

## Protocol

### Phase 0: Initialization

**Step 0.0: Model Selection (Token Savings)**

Before parsing arguments, present this choice to the user:

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

**Step 0.1** — Parse `$ARGUMENTS` for two required paths:
- `target_form_path` — the loan form/document to be filled
- `loan_folder_path` — directory containing source documents

If either is missing, prompt the user:
> "Please provide the path to the target form and the loan folder. Usage: `/acos-loan-doc-mapper <target-form-path> <loan-folder-path>`"

**Step 0.2** — Validate both paths exist. For `loan_folder_path`, inventory all files:
- Count total documents
- Classify by format (PDF, DOCX, XLSX, TXT, images, other)
- Flag any unsupported or empty files

**Step 0.3** — Generate session ID: `LDM-[YYYY-MM-DD]-[HH-MM]`

**Step 0.4** — Resolve model assignments for all agents that will be spawned:

```bash
FORM_ANALYST_MODEL=$(bash .claude/scripts/resolve-agent-model.sh developer)
INVENTORY_MODEL=$(bash .claude/scripts/resolve-agent-model.sh developer)
QA_MODEL=$(bash .claude/scripts/resolve-agent-model.sh qa-reviewer)
EXTRACTOR_MODEL=$(bash .claude/scripts/resolve-agent-model.sh developer)
WRITER_MODEL=$(bash .claude/scripts/resolve-agent-model.sh developer)
```

Use these resolved models for all subsequent Task() or external agent dispatches.

**Step 0.5** — Create evidence bundle directory:

```
.acos/evidence/[DATE]/loan-doc-mapper-[SESSION-ID]/
├── phase1/
├── phase2/
├── phase3/
└── qa-gates/
```

**Step 0.6** — Write `mapping-session.yaml` to the evidence bundle root using the template from `templates/mapping-session.yaml`. Set Phase 0 status to `complete`.

---

### Phase 1: Field Discovery

**Goal:** Extract every field from the target form and inventory all source documents in the loan folder.

**Step 1.1** — Spawn **2 agents in parallel** (`run_in_background: true`):

**Agent A — Form Analyst** (developer model):
- Read the target form page-by-page
- Extract EVERY field: text inputs, numbers, currency amounts, dates, booleans/checkboxes, tables/repeating rows, signature blocks
- For each field record: `field_id`, `name` (exact label on form), `type`, `section`, `page`, `format_hint`, `context` (surrounding text for disambiguation)
- Signature fields: identify but mark `extraction: false` (signatures are not data-extractable)
- Output as YAML following `templates/field-registry.yaml`
- **INJECT: All 8 Data Integrity Rules above**

**Agent B — Source Inventory** (developer model):
- Read every document in the loan folder
- Classify each document (appraisal, tax return, bank statement, credit report, pay stub, W-2, 1099, deed, title, insurance, etc.)
- Summarize available data in each document (key figures, dates, names, amounts)
- Note document quality (clear/legible, partial, damaged)
- Output as YAML inline (no separate template needed) following this schema:

```yaml
source_inventory:
  total_documents: <int>
  documents:
    - filename: "appraisal_2024.pdf"      # exact file name
      path: "<absolute path>"             # full path within loan folder
      doc_type: "appraisal"               # appraisal | tax_return | bank_statement | credit_report | pay_stub | W-2 | 1099 | deed | title | insurance | other
      format: "PDF"                        # PDF | DOCX | XLSX | TXT | image | other
      page_count: <int>                    # null if unknown
      quality: "clear"                     # clear | partial | damaged | unreadable
      available_data: "Key figures, dates, names, amounts summarized here"
      notes: ""                            # optional: anomalies, unsupported/empty flags
  unsupported_or_empty:
    - filename: "<name>"
      reason: "<why skipped>"
```

**Step 1.2** — Collect results from both agents. Merge Form Analyst output into `phase1/field-registry.yaml` and Source Inventory output into `phase1/source-inventory.yaml`. Save raw agent outputs as `phase1/form-analysis-raw.yaml`.

**Step 1.3** — **QA Gate 1**: Spawn `qa-reviewer` agent (blocking, NOT background). Provide:
- The target form (original document)
- The field registry (`phase1/field-registry.yaml`)
- The QA checklist from `templates/qa-checklist-phase1.yaml` (12 binary criteria)

QA reviewer MUST:
- Independently read the target form (do NOT trust the Form Analyst's output alone)
- Evaluate each of the 12 criteria as YES or NO
- ALL 12 must be YES for PASS
- Any NO = REJECT with specific findings per failed criterion

Write QA verdict to `qa-gates/phase1-iteration-1.yaml`.

**Step 1.4** — Retry loop:
- If PASS: proceed to Phase 2
- If REJECT and iteration < 3: re-spawn Form Analyst with QA feedback (the specific failed criteria and findings). Increment iteration counter. Return to Step 1.3.
- If REJECT and iteration >= 3: **ESCALATE** — present the user with:
  - All 3 QA verdicts
  - The remaining failed criteria
  - The current field registry
  - Ask user to manually resolve or override

---

### Phase 2: Answer Extraction

**Goal:** Find the answer to every field in the validated field registry from the loan folder source documents.

**Step 2.1** — Determine agent count based on source document count:
- 1-4 documents: 1 extractor agent
- 5-8 documents: 2 extractor agents
- 9-12 documents: 3 extractor agents
- 13+ documents: 4 extractor agents

Partition source documents across agents (roughly equal distribution). Each agent receives:
- The full validated field registry from Phase 1
- Its assigned source documents
- The source inventory from Phase 1 (for classification context)
- All 8 Data Integrity Rules
- Output format from `templates/answer-map.yaml`

Spawn all extractor agents in parallel (`run_in_background: true`).

Each extractor agent MUST, for every field in the registry:
- Search its assigned documents for the answer
- Record the value EXACTLY as found (no reformatting)
- Record full provenance: source document filename, page number, section, verbatim quote
- Rate confidence: `high`, `medium`, or `low`
- If not found in assigned docs, mark as `NOT_IN_ASSIGNED_DOCS` (not `NOT_FOUND` — other extractors may have it)

**Step 2.2** — Collect and merge all extractor outputs into `phase2/answer-map.yaml`:
- Combine results across extractors
- Fields found by no extractor: mark as `NOT_FOUND` with full search record
- Fields found by multiple extractors: flag as `multi_source` for conflict check
- Save raw extractor outputs as `phase2/extractor-[N]-raw.yaml`

**Step 2.3** — Conflict resolution for multi-source fields:
- If values match across sources: keep with highest confidence, note corroboration
- If values conflict: apply resolution hierarchy:
  1. **Recency** — more recent document wins (e.g., 2024 tax return over 2023)
  2. **Authority** — official/legal documents over informal (e.g., appraisal over estimate)
  3. **Specificity** — document specific to the field over general document
- If hierarchy cannot resolve: flag as `UNRESOLVED_CONFLICT` for user attention
- Write all conflict resolutions to `phase2/conflict-resolutions.yaml`

**Step 2.4** — Generate provenance record (`phase2/provenance-record.yaml`) using `templates/provenance-record.yaml` — full chain from field -> answer -> source document for every mapping.

**Step 2.5** — **QA Gate 2**: Spawn `qa-reviewer` agent (blocking). Provide:
- The source documents (originals from loan folder)
- The answer map (`phase2/answer-map.yaml`)
- The provenance record (`phase2/provenance-record.yaml`)
- The QA checklist from `templates/qa-checklist-phase2.yaml` (12 binary criteria)

QA reviewer MUST:
- Independently read source documents (do NOT trust extractor output alone)
- Spot-check 100% of currency/percentage values for exact match
- Spot-check 100% of names for letter-perfect match
- Spot-check 30% of page number citations for accuracy
- Spot-check 50% of NOT_FOUND entries to confirm genuine absence
- Evaluate each of the 12 criteria as YES or NO
- ALL 12 must be YES for PASS

Write QA verdict to `qa-gates/phase2-iteration-1.yaml`.

**Step 2.6** — Retry loop:
- If PASS: proceed to Phase 3
- If REJECT and iteration < 3: re-spawn extractors ONLY for the specific fields/documents flagged by QA. Merge corrections into the answer map. Return to Step 2.5.
- If REJECT and iteration >= 3: **ESCALATE** — present the user with all QA verdicts, remaining issues, and the current answer map for manual resolution.

---

### Phase 3: Document Population

**Goal:** Fill the target form with the validated answers and produce the final output with full audit trail.

**Step 3.1** — Spawn **Document Writer** agent (developer model, blocking). Provide:
- The target form (original)
- The finalized answer map from Phase 2
- All 8 Data Integrity Rules

The Document Writer MUST:
- Read the target form structure
- For each field in the answer map:
  - If status is `FOUND`: populate with the exact value from the answer map
  - If status is `NOT_FOUND`: annotate the field with `[NOT_FOUND — see summary report]`
  - If status is `UNRESOLVED_CONFLICT`: annotate with `[CONFLICT — see summary report]`
- Preserve the form's structure and layout
- Produce a population log (field-by-field record of what was written where)
- Output: completed document + population log

Write completed document to `phase3/completed-document.*` (matching source format where possible).
Write population log to `phase3/population-log.yaml`.

**Step 3.2** — Generate summary report (`phase3/summary-report.md`):

```markdown
# Loan Document Mapping — Summary Report

**Session:** [SESSION-ID]
**Date:** [DATE]
**Target Form:** [filename]
**Source Documents:** [count] files from [loan_folder_path]

## Statistics
- Total fields identified: [N]
- Successfully populated: [N] ([%])
- NOT_FOUND: [N] ([%])
- Conflicts resolved: [N]
- Unresolved conflicts: [N]

## NOT_FOUND Fields (Require Manual Attention)
| Field ID | Field Name | Section | Documents Searched |
|----------|------------|---------|-------------------|
| ...      | ...        | ...     | ...               |

## Unresolved Conflicts (Require Manual Decision)
| Field ID | Field Name | Values Found | Sources |
|----------|------------|-------------|---------|
| ...      | ...        | ...         | ...     |

## Provenance Summary
All populated values trace to source documents. Full provenance record available at:
`[path to provenance-record.yaml]`
```

**Step 3.3** — **QA Gate 3**: Spawn `qa-reviewer` agent (blocking). Provide:
- The completed document (`phase3/completed-document.*`)
- The answer map (`phase2/answer-map.yaml`)
- The source documents (originals from loan folder)
- The population log (`phase3/population-log.yaml`)
- The QA checklist from `templates/qa-checklist-phase3.yaml` (10 binary criteria)

QA reviewer MUST:
- Verify end-to-end: output document value -> answer map value -> source document value (must all match)
- Spot-check 100% of numerical values for exact character-by-character match
- Verify NO data was introduced outside the answer map
- Verify all NOT_FOUND fields are properly annotated (not incorrectly populated)
- Evaluate each of the 10 criteria as YES or NO
- ALL 10 must be YES for PASS

Write QA verdict to `qa-gates/phase3-iteration-1.yaml`.

**Step 3.4** — Retry loop:
- If PASS: proceed to Step 3.5
- If REJECT and iteration < 3: re-spawn Document Writer with QA feedback for specific fields. Return to Step 3.3.
- If REJECT and iteration >= 3: **ESCALATE** — present the user with all QA verdicts and remaining issues.

**Step 3.5** — Present results to user:

> **Loan Document Mapping Complete**
>
> - Completed document: `[path]`
> - Summary report: `[path]`
> - Evidence bundle: `[path]`
>
> **Stats:** [N] of [M] fields populated ([%]), [X] NOT_FOUND, [Y] conflicts
>
> **Action required:** [N] fields marked NOT_FOUND need manual attention. See summary report.

Update `mapping-session.yaml` with final status `complete` for all phases.

---

## Error Handling

| Stage | Error | Response |
|-------|-------|----------|
| Phase 0 | Target form not found | Report error, prompt for correct path |
| Phase 0 | Loan folder empty | Report error, prompt for correct path |
| Phase 0 | Unsupported file format | Log warning, skip file, continue with supported files |
| Phase 1 | Form Analyst agent fails | Retry once, then escalate to user |
| Phase 1 | Target form unreadable | Report to user, suggest alternative format |
| Phase 2 | Extractor agent fails | Retry once with same docs, then escalate |
| Phase 2 | Source document unreadable | Log as `UNREADABLE`, exclude from extraction, note in report |
| Phase 3 | Document Writer fails | Retry once, then escalate |
| Any QA Gate | QA reviewer crashes | Mark as INCONCLUSIVE (blocks like REJECT), retry gate |
| Any Phase | Max iterations (3) reached | Escalate to user with full context |
| Any Phase | Model resolution fails | Fall back to hardcoded defaults |

---

*Loan Document Mapper — Zero-fabrication financial document pipeline.*
