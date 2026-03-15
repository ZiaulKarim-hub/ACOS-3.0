---
name: acos-loan-doc-finder
description: |
  Multi-agent loan document finder with adversarial QA. Scans source directories,
  classifies documents against a user-provided category schema using PRISM's 252-item
  DD framework, copies matches to an output folder, and runs adversarial review with
  a Wigum feedback loop (max 5 iterations) until QA passes or escalates to user.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "<source-dir-1> [source-dir-2] ... --output <output-folder> [--schema <schema-file>]"
---

# ACOS Loan Document Finder

## Purpose

Find, classify, copy, and verify loan documents from one or more source directories using a
3-tier multi-agent swarm pipeline:

1. **Coordinator** — Orchestrates all phases, manages the Wigum feedback loop
2. **Document Classifier Agents** (parallel) — Read and classify documents against topic headings
3. **Adversarial QA Agents** (parallel) — Verify classifications, flag mismatches

Leverages PRISM's 252-item Due Diligence framework (CCII codes) for institutional-grade
document classification when available in the project's knowledge graph.

```
Phase 0: Init           → Parse args, build category schema, inventory files
Phase 1: Classification → Parallel agents read & classify all documents
Phase 2: Copy           → Copy matched documents to output folder
Phase 3: QA Review      → Adversarial agents verify classifications
  ↕ Wigum Loop          → If QA flags issues, reclassify flagged docs (max 5 rounds)
Phase 4: Final Report   → Generate document inventory report
```

---

## Phase 0: Initialization

### Step 0.0: Model Selection (Token Savings)

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

### Step 0.1: Parse Arguments

Parse `$ARGUMENTS` for source directories, output folder, and optional schema:

| Argument | Required | Description |
|----------|----------|-------------|
| `<source-dir-1>` | Yes | First directory to scan |
| `[source-dir-2 ...]` | No | Additional directories to scan |
| `--output <path>` | Yes | Destination folder for copied documents |
| `--schema <path>` | No | YAML file with document categories (see schema format below) |

**Examples:**
```
/acos-loan-doc-finder /path/to/ascent /path/to/waldorf --output ~/Desktop/Waldorf Senior Loan files
/acos-loan-doc-finder /path/to/deal-folder --output ~/Desktop/Output --schema categories.yaml
```

If `--output` is missing, prompt the user:
> "Where should I copy the matched documents? Provide a destination folder path."

If no source directories are provided, prompt the user:
> "Which directories should I search? Provide one or more source directory paths."

### Step 0.2: Build Category Schema

If `--schema` is provided, read the YAML file. Expected format:

```yaml
categories:
  - group: "Ascent"
    documents:
      - name: "Third party inspector reports"
        ccii_hint: "06xx"
        keywords: ["inspector", "inspection", "third party", "site visit"]
      - name: "City sign-offs"
        ccii_hint: "07xx"
        keywords: ["city", "sign-off", "certificate of occupancy", "permit", "approval"]
      # ... more items
  - group: "Waldorf"
    documents:
      - name: "Phase I report on excess land"
        ccii_hint: "0603"
        keywords: ["phase I", "environmental", "ESA", "excess land"]
      # ... more items
```

If `--schema` is NOT provided, prompt the user interactively:
> "What document categories are you looking for? List them organized by group/property.
> Example: 'Ascent: inspector reports, city sign-offs, RFIs | Waldorf: Phase I, ALTA, budget'"

Parse the user's response into the internal category schema format. For each document name,
auto-generate keyword hints using domain knowledge.

### Step 0.3: Validate & Inventory Source Directories

For each source directory:

1. Verify the path exists and is readable
2. Recursively inventory all files: `**/*.{pdf,docx,doc,xlsx,xls,csv,txt,md,png,jpg,jpeg,tiff}`
3. Record: filename, full path, file size, file type, parent folder name
4. Skip hidden files/directories (`.DS_Store`, `.git`, `.acos`, `.claude`, etc.)
5. Count total documents per directory

Display inventory summary to user:
```
Source Directory Inventory
===========================
Directory 1: /path/to/ascent (47 files)
  PDF: 31 | DOCX: 8 | XLSX: 5 | Other: 3

Directory 2: /path/to/waldorf (23 files)
  PDF: 18 | DOCX: 3 | XLSX: 2 | Other: 0

Total: 70 documents to classify
Categories: 12 document types across 2 groups
```

### Step 0.4: Create Session & Resolve Models

1. Generate session ID: `LDF-YYYYMMDD-HHMMSS`
2. Create session directory: `.acos/sessions/loan-doc-finder/{session-id}/`
3. Write session manifest from `templates/session-manifest.yaml`
4. Resolve agent models:

```bash
CLASSIFIER_MODEL=$(bash .claude/scripts/resolve-agent-model.sh developer)
QA_MODEL=$(bash .claude/scripts/resolve-agent-model.sh qa-reviewer)
COORDINATOR_MODEL=$(bash .claude/scripts/resolve-agent-model.sh architect)
```

### Step 0.5: PRISM Knowledge Integration (Optional Enhancement)

Check if PRISM knowledge graph exists at the project level:

```bash
# Check for PRISM knowledge in okoa-labs or current project
PRISM_KG=""
if [ -d "$HOME/okoa-labs/okoa_ops/knowledge-graph/vault" ]; then
  PRISM_KG="$HOME/okoa-labs/okoa_ops/knowledge-graph/vault"
fi
```

If PRISM knowledge graph is available:
1. Read relevant entity files for the deal/property names in the category schema
2. Extract CCII code mappings for each document category
3. Build an enriched classification context with PRISM's DD framework codes
4. Inject this context into classifier agent prompts for higher accuracy

If not available, proceed with keyword-based classification only.

---

## Phase 1: Document Classification Swarm

### Step 1.1: Partition Files Across Agents

Divide the file inventory across N classifier agents (5-10, based on total file count):

```
if total_files <= 20:   agents = 5
elif total_files <= 50:  agents = 7
elif total_files <= 100: agents = 8
else:                    agents = 10
```

Each agent gets a roughly equal partition of files. Files are assigned round-robin by
directory order to ensure each agent sees files from all source directories.

### Step 1.2: Launch Classifier Agents

**CRITICAL: ALL classifier agents MUST be spawned in a SINGLE message as parallel Task() calls.**

For each classifier agent, resolve the model and dispatch:

```
# If CLASSIFIER_MODEL is a bare Claude name (no colon):
Task(general-purpose)
  - run_in_background: true
  - model: $CLASSIFIER_MODEL
  - prompt: |
      You are a Loan Document Classifier for the ACOS Loan Doc Finder pipeline.

      YOUR TASK: Read each assigned document and classify it against the category schema.
      For each document, determine which category (if any) it belongs to.

      CATEGORY SCHEMA:
      [inject full category schema with groups, document names, CCII hints, keywords]

      PRISM CONTEXT (if available):
      [inject PRISM CCII code mappings and DD framework descriptions]

      YOUR FILE ASSIGNMENTS:
      [list of file paths assigned to this agent]

      CLASSIFICATION RULES:
      1. READ the actual content of each document — do NOT classify by filename alone
      2. For PDFs: read the first 10 pages minimum, scan for key terms and structure
      3. For spreadsheets: examine sheet names, headers, and data patterns
      4. Match against category keywords AND document structure/purpose
      5. Assign confidence: high (exact match), medium (likely match), low (possible match)
      6. If a document matches NO category, classify as "UNMATCHED"
      7. If a document could match MULTIPLE categories, list all with confidence levels
      8. Record the classification rationale — what specific content led to the match

      OUTPUT FORMAT (YAML):
      Write to: .acos/sessions/loan-doc-finder/{session-id}/phase1/agent-{NN}/classifications.yaml

      Use the template structure from templates/classification-manifest.yaml

# If CLASSIFIER_MODEL contains ":" (external provider):
Bash(run_in_background: true):
  python3 .claude/scripts/run-external-agent.py \
    --agent developer \
    --model "$CLASSIFIER_MODEL" \
    --task "[full prompt above]" \
    --context [file paths]
```

### Step 1.3: Aggregate Classifications

Wait for ALL classifier agents to complete. Then aggregate:

1. Read all `phase1/agent-*/classifications.yaml` files
2. Merge into a unified classification manifest
3. Resolve conflicts (same document classified differently by overlapping agents — shouldn't
   happen with partitioning, but handle edge cases)
4. Build the master classification map:

```yaml
# .acos/sessions/loan-doc-finder/{session-id}/phase1/classification-master.yaml
classifications:
  - file: "/path/to/document.pdf"
    filename: "document.pdf"
    source_dir: "/path/to/source"
    assigned_category:
      group: "Ascent"
      document_type: "Third party inspector reports"
      ccii_code: "0612"  # if PRISM context available
    confidence: "high"
    rationale: "Contains site inspection findings dated 2025-11-15..."
    classified_by: "agent-03"

  - file: "/path/to/other.xlsx"
    filename: "other.xlsx"
    source_dir: "/path/to/source"
    assigned_category: null  # UNMATCHED
    confidence: null
    rationale: "General ledger entries, does not match any target category"
    classified_by: "agent-01"

unmatched_count: 15
matched_count: 12
categories_found: 9
categories_missing: 3
missing_categories:
  - group: "Ascent"
    document_type: "Deposit Log"
  - group: "Waldorf"
    document_type: "2026 operating budget"
  - group: "Waldorf"
    document_type: "Excess land plans"
```

Display classification summary to user:
```
Classification Results (Iteration 1)
=====================================
Matched: 12/70 documents → 9/12 categories found
Missing: 3 categories (Deposit Log, 2026 operating budget, Excess land plans)
Unmatched: 58 documents (not relevant to any category)
```

---

## Phase 2: Copy Matched Documents

### Step 2.1: Create Output Directory Structure

```bash
mkdir -p "$OUTPUT_FOLDER"
mkdir -p "$OUTPUT_FOLDER/Ascent"
mkdir -p "$OUTPUT_FOLDER/Waldorf"
# Create a subdirectory per group from the category schema
```

### Step 2.2: Copy Files (Read-Only on Source)

For each classified document with a match:

```bash
# Copy, preserving original filename. If duplicates, append counter.
cp -n "$SOURCE_PATH" "$OUTPUT_FOLDER/$GROUP/$FILENAME"
```

**CRITICAL: Use `cp` only. Never `mv`. Never modify source directories.**

### Step 2.3: Generate Copy Manifest

Write `$OUTPUT_FOLDER/_copy-manifest.yaml` documenting every copy operation:

```yaml
copies:
  - source: "/original/path/to/doc.pdf"
    destination: "$OUTPUT_FOLDER/Ascent/doc.pdf"
    category: "Third party inspector reports"
    confidence: "high"
    copy_status: "success"
    file_hash: "sha256:abc123..."  # verify integrity
```

Verify each copy by comparing file sizes (and optionally sha256 hashes).

---

## Phase 3: Adversarial QA Review

### Step 3.1: Launch QA Agents

Spawn 3 adversarial QA agents in a SINGLE message, each with a different review lens:

**QA Agent 1 — Content Verifier:**
```
Task(general-purpose)
  - run_in_background: true
  - model: $QA_MODEL
  - isolation: worktree
  - prompt: |
      You are an ADVERSARIAL Content Verifier. Your job is to DISPROVE document
      classifications. Assume every classification is WRONG until you verify it.

      CLASSIFICATION MANIFEST:
      [inject phase1/classification-master.yaml]

      COPY MANIFEST:
      [inject $OUTPUT_FOLDER/_copy-manifest.yaml]

      FOR EACH CLASSIFIED DOCUMENT:
      1. Read the ACTUAL document content (at least first 10 pages for PDFs)
      2. Compare the content against the assigned category description
      3. Check: Does this document REALLY contain what the category requires?
      4. Check: Could this document be a DIFFERENT category instead?
      5. Check: Is the confidence rating justified?

      VERDICT per document: CONFIRMED | MISMATCH | QUESTIONABLE
      - CONFIRMED: Content clearly matches the assigned category
      - MISMATCH: Content does NOT match — provide the correct category or "NONE"
      - QUESTIONABLE: Content is ambiguous — explain why

      Write to: .acos/sessions/loan-doc-finder/{session-id}/phase3/iteration-{N}/qa-content/review.yaml
```

**QA Agent 2 — Completeness Auditor:**
```
Task(general-purpose)
  - run_in_background: true
  - model: $QA_MODEL
  - isolation: worktree
  - prompt: |
      You are an ADVERSARIAL Completeness Auditor. Your job is to find MISSING
      documents that the classifiers overlooked.

      CATEGORY SCHEMA:
      [inject full schema]

      CLASSIFICATION MANIFEST:
      [inject classification-master.yaml — including unmatched files]

      FULL FILE INVENTORY:
      [inject complete file list from Phase 0]

      FOR EACH MISSING CATEGORY:
      1. Re-examine ALL unmatched files — could any of them actually be this document?
      2. Check filenames, folder structures, and file metadata for clues
      3. Read promising candidates (files with suggestive names or locations)
      4. Could a matched document actually serve double duty for a missing category?

      FOR EACH MATCHED CATEGORY:
      1. Are there ADDITIONAL documents that should also be included?
      2. Are there newer versions of the same document that were missed?

      Write to: .acos/sessions/loan-doc-finder/{session-id}/phase3/iteration-{N}/qa-completeness/review.yaml
```

**QA Agent 3 — Domain Expert (PRISM-informed):**
```
Task(general-purpose)
  - run_in_background: true
  - model: $QA_MODEL
  - isolation: worktree
  - prompt: |
      You are a Domain Expert QA reviewer with deep knowledge of real estate
      lending and due diligence. You understand PRISM's 252-item DD framework.

      PRISM CCII REFERENCE:
      [inject CCII code descriptions for all relevant categories]

      CLASSIFICATION MANIFEST:
      [inject classification-master.yaml]

      YOUR REVIEW FOCUS:
      1. Do the classified documents meet institutional DD standards for their category?
      2. Are there industry-standard documents that SHOULD exist but are missing?
      3. For each document, does the CCII code assignment make sense?
      4. Flag any documents that a senior loan officer would question
      5. Note if any documents appear outdated, incomplete, or insufficient

      DOMAIN-SPECIFIC CHECKS:
      - ALTA surveys: Must be recent (within 12 months), show easements and exceptions
      - Phase I ESA: Must comply with ASTM E1527, signed by qualified professional
      - Operating budgets: Must cover the relevant fiscal year, show line-item detail
      - Inspector reports: Must be from licensed third-party, not self-inspection
      - City sign-offs: Must be official municipal documents with stamps/signatures
      - RFIs: Must show request-response pairs with dates
      - Schedule of Values: Must align with construction loan draw schedule
      - Liens: Must show current status (filed, released, subordinated)

      Write to: .acos/sessions/loan-doc-finder/{session-id}/phase3/iteration-{N}/qa-domain/review.yaml
```

### Step 3.2: Aggregate QA Results

Wait for ALL 3 QA agents. Then aggregate:

1. Read all three review files
2. Merge findings into a unified QA report:

```yaml
# .acos/sessions/loan-doc-finder/{session-id}/phase3/iteration-{N}/qa-synthesis.yaml
iteration: N
overall_verdict: "PASS | FAIL"

document_verdicts:
  - file: "document.pdf"
    category: "Third party inspector reports"
    content_verdict: "CONFIRMED"
    domain_verdict: "CONFIRMED"
    flags: []

  - file: "wrong-doc.pdf"
    category: "City sign-offs"
    content_verdict: "MISMATCH"
    domain_verdict: "MISMATCH"
    flags:
      - type: "misclassification"
        detail: "This is actually a construction permit application, not a city sign-off"
        suggested_category: "NONE"
        source_agent: "qa-content"

newly_found:
  - file: "overlooked-doc.pdf"
    suggested_category: "Deposit Log"
    rationale: "Contains deposit tracking entries with dates and amounts"
    source_agent: "qa-completeness"

missing_confirmed:
  - category: "2026 operating budget"
    group: "Waldorf"
    search_exhaustive: true
    notes: "No document in any source directory contains 2026 budget information"

convergence:
  previous_flag_count: null  # or N from previous iteration
  current_flag_count: 4
  improving: null  # or true/false
  stuck: false
```

### Step 3.3: Decision Gate (Wigum Loop)

Read the QA synthesis. Apply decision logic:

**Case 1: ALL PASS** (zero flags, zero new finds, only confirmed missing)
```
→ Proceed to Phase 4 (Final Report)
→ Log: "QA passed on iteration {N} — all classifications verified"
```

**Case 2: FLAGS EXIST + iterations remaining** (iteration < 5)
```
→ Check convergence: if stuck (flag count not decreasing for 2+ iterations), warn user
→ Extract actionable feedback:
    - Misclassified documents → remove from output, reclassify
    - Newly found documents → add to classification queue
    - Questionable documents → re-examine with more context
→ Log: "Wigum loop iteration {N}/5: {flag_count} flags, reclassifying {reclass_count} documents"
→ Loop back to Phase 1 Step 1.2 with ONLY the flagged/new documents
    - Do NOT re-examine already-confirmed documents
    - Include QA feedback in the classifier prompt for context
→ After reclassification, re-run Phase 2 (copy updates) and Phase 3 (QA) for affected files only
```

**Case 3: FLAGS EXIST + max iterations reached** (iteration = 5)
```
→ Proceed to Phase 4 with current state
→ Include all remaining flags in the final report
→ Escalate to user:
    "Document classification completed 5 QA iterations but {flag_count} items remain flagged.

     Remaining flags:
     [list each flag with document, issue, and QA agent recommendation]

     Options:
     1. Accept current classifications as-is
     2. Manually review flagged documents
     3. Provide additional source directories to search"
→ AWAIT USER DECISION before finalizing
```

### Convergence Safety

If the Wigum loop detects it is stuck (flag count not decreasing for 2+ consecutive iterations):

1. Log warning: "Wigum loop may be stuck — flags not decreasing"
2. Check if the same documents are being flagged repeatedly with the same issues
3. If genuinely ambiguous documents, escalate those specific items to the user mid-loop
4. Do not waste iterations on documents that QA and classifiers fundamentally disagree on

---

## Phase 4: Final Report Generation

### Step 4.1: Generate Document Report

Create `$OUTPUT_FOLDER/DOCUMENT_REPORT.md` with the following structure:

```markdown
# Loan Document Finder Report
**Generated:** YYYY-MM-DD HH:MM
**Session:** LDF-YYYYMMDD-HHMMSS
**Source Directories:** [list]
**Output Folder:** [path]
**QA Iterations:** N/5
**Final Verdict:** PASS | PASS WITH WARNINGS | ESCALATED

---

## Summary
- Documents Scanned: [total]
- Documents Matched: [count]
- Documents Copied: [count]
- Categories Found: [X/Y]
- Categories Missing: [list]

---

## [Group Name] Documents

### [Category Name] — [STATUS: FOUND | NOT FOUND]
**File:** [filename] (copied to [relative path])
**Source:** [original path]
**Classification Confidence:** [high/medium/low]
**QA Verdict:** [CONFIRMED / QUESTIONABLE]
**CCII Code:** [code if available]

**Summary:** [2-3 sentence description of the document's content, key dates,
parties involved, and relevance to the category]

---

### [Category Name] — NOT FOUND
**Status:** Not available in source directories
**Search Notes:** [What was searched, why it wasn't found]
**Recommendation:** [Where this document might typically be obtained]

---

## QA Review Summary
- Total QA Iterations: N
- Documents Confirmed: X
- Documents Reclassified: Y (across all iterations)
- Remaining Flags: Z

## Appendix: Full Classification Log
[Table of ALL documents scanned, their classification, and final status]
```

### Step 4.2: Display Summary to User

Print a concise summary of the completed operation:

```
Loan Document Finder — Complete
=================================
Output: ~/Desktop/Waldorf Senior Loan files/
Report: ~/Desktop/Waldorf Senior Loan files/DOCUMENT_REPORT.md

Found 9/12 categories:
  ✓ Ascent: Inspector reports, City sign-offs, RFIs, Schedule of Values, Liens, GC schedule
  ✓ Waldorf: Phase I report, ALTA
  ✗ Missing: Deposit Log, Change order log, 2026 operating budget, Excess land plans

QA: PASSED after 2 iterations (3 reclassifications)
```

---

## Data Flow Reference

```
Phase 0 ── file inventory + category schema ──→ Phase 1 (what to find, where to look)

Phase 1 ── classification-master.yaml ──→ Phase 2 (which files to copy)
                                       ──→ Phase 3 (what to verify)

Phase 2 ── copy-manifest.yaml ──→ Phase 3 (verify copies match classifications)

Phase 3 ── qa-synthesis.yaml ──→ Phase 1 (reclassify flagged, if Wigum loop)
        or ──→ Phase 4 (final report, if PASS or max iterations)

PRISM KG ── CCII codes + DD framework ──→ Phase 1 (enriched classification context)
                                        ──→ Phase 3 (domain expert QA context)
```

---

## Configuration Reference

| Setting | Default | Description |
|---------|---------|-------------|
| Max classifier agents | 10 | Upper bound on parallel classifiers |
| Min classifier agents | 5 | Lower bound on parallel classifiers |
| QA agents | 3 | Content verifier + completeness auditor + domain expert |
| Max Wigum iterations | 5 | Maximum QA feedback loops before escalation |
| Confidence threshold | medium | Minimum confidence to include in copy |
| File types scanned | pdf,docx,xlsx,csv,txt,md | Supported document formats |
| PRISM integration | auto | auto (detect), on (require), off (skip) |

---

*ACOS Loan Document Finder — Multi-agent classification with adversarial QA and iterative refinement.*
