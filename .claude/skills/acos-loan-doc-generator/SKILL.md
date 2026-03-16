---
name: acos-loan-doc-generator
description: |
  Multi-phase swarm-based private equity loan document generator. Interactive
  wizard selects document type, design source, and loan folder. Delegates heavy
  work to phase orchestrator agents — each phase runs in its own context window.
  Includes persistent design library, Phase 2 cache, and quality-safe token
  optimizations. Primary context stays thin (~25K tokens vs ~300K+ previously).
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task(loan-doc-phase1), Task(loan-doc-phase2), Task(loan-doc-phase34)
---

# ACOS Loan Document Generator

## Purpose

Generate institutional-quality private equity loan documents from loan folders
using a 5-step pipeline with **delegated phase orchestration**:

1. **Interview** — Quick/Detailed wizard: type, design, folder, figures, page count, images (runs here)
2. **Extract** — Learn design patterns and benchmarks (delegated to `loan-doc-phase1` agent)
3. **Analyze** — Deep-read loan folder, extract data (delegated to `loan-doc-phase2` agent)
4. **Design + Validate** — Write document with CSS pagination, validate, Wigum loop (delegated to `loan-doc-phase34` agent)
5. **Report** — Data provenance table, results display (runs here)

**Architecture**: The primary context window handles ONLY the interactive interview
(Phase 0) and phase dispatching. All heavy reading, agent spawning, and iteration
happens inside phase orchestrator agents — each in their own context window.

---

## Phase 0: Interview Wizard

All user interaction happens here. No CLI argument parsing except `status`.

If `$ARGUMENTS` contains `status`, skip to the **Status Command** section.

### Step 0.0: Mode Selection

Display the mode selection first:

```
╔══════════════════════════════════════════════════════════════╗
║        ACOS Loan Document Generator                         ║
╚══════════════════════════════════════════════════════════════╝

  [1] Quick      — 3 questions, smart defaults, fast generation
  [2] Detailed   — Full wizard with all customization options
  [3] Batch      — Multiple documents, same loan folder

Enter selection [1-3]:
```

Store as `interview_mode`: `quick`, `detailed`, or `batch`.

- **Quick mode** asks only: Document type → Design source → Loan folder → Confirm
- **Detailed mode** adds: Critical figures → Page count → Images → Instructions
- **Batch mode** asks: Multiple document types → Design sources per type → Loan folder → Confirm

### Step 0.1: Document Category Selection

Display the category menu:

```
Step {1 of 4 if quick | 1 of 8 if detailed}: Select a document category

  [A]  Credit Memo & Underwriting
  [B]  Closing & Administration
  [C]  Portfolio Management
  [D]  Loan Modifications & Workout
  [E]  Investor & Participation
  [F]  Other

Enter selection [A-F]:
```

Map selection to `category_id`:

| # | category_id |
|---|-------------|
| A | `credit-underwriting` |
| B | `closing-admin` |
| C | `portfolio-management` |
| D | `loan-modifications` |
| E | `investor-participation` |
| F | `other` |

Store as `category_id`.

### Step 0.2: Document Type Selection

**If category is F (Other):**

```
  You selected: Other

  What document do you need?

  Document name: _
```

Store the entered value as `document_title`. Set `document_id = "other/custom"`.
Load the `other` fallback entry from `templates/doc-type-catalog.yaml`.

**For categories A–E**, display the documents within the selected category:

**Category A — Credit Memo & Underwriting:**
```
  [1]  Internal Credit Memo        (risk-focused, credit committee)
  [2]  External Credit Memo        (marketing document, broker-facing)
  [3]  Term Sheet                   (proposed deal terms)
  [4]  Deal Memo                    (deal summary, committee presentation)
  [5]  Scoping Letter               (preliminary interest, high-level terms)
  [6]  Executive Summary            (deal overview, one-pager)

Enter selection [1-6]:
```

**Category B — Closing & Administration:**
```
  [1]  Closing Summary / Checklist  (closing items, conditions, status)
  [2]  Settlement Statement         (final transaction amounts, disbursements)
  [3]  Escrow Instructions          (escrow agent directives, conditions)
  [4]  Wire Instructions            (wire transfer details, routing)
  [5]  Transaction Checklist        (pre/post-close task tracking)

Enter selection [1-5]:
```

**Category C — Portfolio Management:**
```
  [1]  Payoff Statement / Letter    (outstanding balance, per-diem, payoff terms)
  [2]  Redemption Statement         (investor redemption amounts, timing)

Enter selection [1-2]:
```

**Category D — Loan Modifications & Workout:**
```
  [1]  Extension Request Questionnaire  (borrower extension request form)
  [2]  Loan Extension Agreement         (extension terms, modified conditions)
  [3]  Forbearance Agreement            (temporary relief, modified payment terms)
  [4]  Pre-Foreclosure Notice           (default notice, cure period)
  [5]  Demand Letter                    (payment demand, legal notice)

Enter selection [1-5]:
```

**Category E — Investor & Participation:**
```
  [1]  Investor Participation Agreement  (participation terms, pro-rata shares)
  [2]  Investor Update / Report          (portfolio performance, deal updates)

Enter selection [1-2]:
```

Map selection to `document_id` (format: `{category_id}/{document_slug}`):

| Category | # | document_id | document_title |
|----------|---|-------------|----------------|
| A | 1 | `credit-underwriting/internal-credit-memo` | Internal Credit Memo |
| A | 2 | `credit-underwriting/external-credit-memo` | External Credit Memo |
| A | 3 | `credit-underwriting/term-sheet` | Term Sheet |
| A | 4 | `credit-underwriting/deal-memo` | Deal Memo |
| A | 5 | `credit-underwriting/scoping-letter` | Scoping Letter |
| A | 6 | `credit-underwriting/executive-summary` | Executive Summary / Deal Overview |
| B | 1 | `closing-admin/closing-summary` | Closing Summary / Checklist |
| B | 2 | `closing-admin/settlement-statement` | Settlement Statement |
| B | 3 | `closing-admin/escrow-instructions` | Escrow Instructions |
| B | 4 | `closing-admin/wire-instructions` | Wire Instructions |
| B | 5 | `closing-admin/transaction-checklist` | Transaction Checklist |
| C | 1 | `portfolio-management/payoff-statement` | Payoff Statement / Letter |
| C | 2 | `portfolio-management/redemption-statement` | Redemption Statement |
| D | 1 | `loan-modifications/extension-request` | Extension Request Questionnaire |
| D | 2 | `loan-modifications/extension-agreement` | Loan Extension Agreement |
| D | 3 | `loan-modifications/forbearance-agreement` | Forbearance Agreement |
| D | 4 | `loan-modifications/pre-foreclosure-notice` | Pre-Foreclosure Notice |
| D | 5 | `loan-modifications/demand-letter` | Demand Letter |
| E | 1 | `investor-participation/participation-agreement` | Investor Participation Agreement |
| E | 2 | `investor-participation/investor-report` | Investor Update / Report |
| F | — | `other/custom` | (user-specified) |

Load the matching entry from `templates/doc-type-catalog.yaml` using `document_id`.
Store as `catalog_entry`. Set `document_title` from the table above (or user input for F).

**Batch mode:** Both steps are combined. After category selection, the document
menu changes to support multi-select within that category:

```
Enter selections (comma-separated, e.g., 1,3,5): _
```

Then ask if the user wants to add documents from another category:

```
  Selected so far:
    A1  Internal Credit Memo
    A3  Term Sheet

  Add documents from another category? [Y/n]:
```

If Y, show the category menu again (excluding already-visited categories).
Repeat until the user declines or all categories are visited.

Parse all selections into a `batch_entries` list. Each entry gets its own
`batch_item` dict with `document_id`, `document_title`, `category_id`, and
per-document pipeline state (design source, skip flags, page count, etc.).

For any batch items from category F, prompt for each document name individually.

### Step 0.3: Design Library Check

Read `.acos/loan-doc-generator/design-library/index.yaml` if it exists.
Filter entries where `entry.document_id == document_id`.

**Case A — Library has 1+ designs:**

```
Step 2 of 5: Design style

  Design Library has {N} design(s) for "{catalog_entry.label}":
  ─────────────────────────────────────────────────────────────
  [1]  {label}  │  {example_count} samples  │  Added {date_added}
       Samples:
         file://{sample_files[0]}
         file://{sample_files[1]}

  [2]  {label}  │  {example_count} samples  │  Added {date_added}
       Samples:
         file://{sample_files[0]}
  ...
  ─────────────────────────────────────────────────────────────
  [N+1]  Use New Design (provide new examples)

Enter selection [1-{N+1}]:
```

Sample `file://` links are clickable — users can open them to preview what the
design looks like before choosing. The links open in the system's default viewer.

If user selects **a numbered design [1-N]**, store as `selected_library_entry`.
Set `skip_phase_1 = true`. Load `design_patterns_path` and `benchmark_criteria_path`
from the selected entry.

If user selects **[N+1] Use New Design**, prompt for example path (see Case B below).

**Case B — No designs in library for this document type:**

```
Step 2 of 5: Design style

  No designs in library for "{catalog_entry.label}". Using new design.

  Enter path to example document(s):
  (File path, directory, or glob pattern)

  Path: _
```

Validate the path exists. Store as `examples_path`. Set `skip_phase_1 = false`.

**Novelty check (Case B and "Use New Design" in Case A):**

Compute fingerprint: `document_id + ":" + realpath(examples_path)`.
Check against all entries in `design-library/index.yaml`.

- **Match found:** Prompt: `"This source was previously extracted as '{label}' (added {date_added}). Re-use cached extraction? [Y/n]: "`. If Y: `skip_phase_1 = true`, load from that library entry. If N: proceed to Phase 1.
- **No match:** `skip_phase_1 = false`. Will extract and auto-add to library after Phase 1.

**Batch mode design resolution:** Iterate through each `batch_item` and resolve
its design source independently. Display a summary table:

```
  Design sources for batch:
  ─────────────────────────────────────────────────────────────
  #  DOCUMENT                     DESIGN SOURCE           PHASE 1
  1  Credit Memo — Internal       Library: pe-format-2024  Skip
  2  Credit Memo — External       New: /path/to/examples   Run
  3  Deal Document                Library: deal-v2          Skip

  Documents needing Phase 1 extraction: 1 of 3
```

For each item needing a new design, prompt for the examples path (one prompt per
item). Run novelty checks as in single-document mode.

### Step 0.4: Loan Folder Path

```
Step 3 of 5: Loan folder

  Enter path to the loan folder for this transaction:
  Path: _
```

Validate the path exists. Store as `loan_folder_path`.

### Step 0.5: Critical Numbers

**Quick mode / Batch mode:** Skip this step entirely. Set `figures_mode = "auto"`, `user_figures_path = null`.

**Detailed mode:** Continue below.

The figures shown to the user are **category-specific** — read from
`catalog_entry.critical_figures` (loaded in Step 0.1).

```
Step 4 of 8: Financial figures

  How should critical numbers be handled?

  [1] I'll provide key numbers   — highest accuracy, fewer tokens
  [2] Extract from documents     — fully automated
  [3] Hybrid                     — I'll provide some, extract the rest

Enter selection [1-3]:
```

Store as `figures_mode`: `user`, `auto`, or `hybrid`.

**If user selects [1] or [3]:**

1. Read `catalog_entry.critical_figures` for the selected category
2. Generate a category-specific YAML template at:
   `.acos/loan-doc-generator/sessions/{session_id}/user-figures.yaml`

   The generated file has this structure:
   ```yaml
   # Financial Figures — {catalog_entry.label}
   # Fill in figures you know. Leave blank or delete lines you don't have.
   # These become GROUND TRUTH — the document uses them exactly as entered.
   #
   # Fallback for blank fields:
   #   1. Extract from loan folder documents (Phase 2)
   #   2. If not found: [DATA NOT AVAILABLE] in the document

   # ── {Group Name} ──
   {key}:           # {hint}  {★ if required}
   {key}:           # {hint}
   ...

   # ── Custom Figures ──
   # Add any deal-specific figures not listed above:
   # custom_field_name: value
   ```

   Only include figures from `catalog_entry.critical_figures` — NOT a generic
   template. Example for Guarantee Document:
   ```yaml
   # ── Guarantee ──
   guarantee_amount:          # e.g., 15000000 or Unlimited  ★
   guarantor_name:            # e.g., John Smith  ★
   guarantor_liability_cap:   # e.g., 25% of loan amount or 3750000
   # ── Underlying Loan ──
   loan_amount:               # e.g., 15000000  ★
   borrower_name:             # e.g., ABC Holdings LLC  ★
   lender_name:               # e.g., XYZ Capital Partners  ★
   ...
   ```

3. Display the required fields inline for quick entry:
   ```
     Key figures for {catalog_entry.label}:
     ─────────────────────────────────────────────────────────────
     ★ = important for accuracy

     {Group 1}:
       ★ {Label}:  {hint}
         {Label}:  {hint}
     {Group 2}:
       ★ {Label}:  {hint}
       ...

     A template has been created at:
     .acos/loan-doc-generator/sessions/{session_id}/user-figures.yaml

     Fill in what you know — blank fields will be extracted from documents.

     [Press Enter when done editing]
   ```
4. Wait for user to confirm
5. Read the file back. Parse all non-empty, non-comment fields into `user_figures` dict.
6. Display summary grouped by category:
   ```
     Figures provided: {count} of {total_fields}
     ─────────────────────────────────────────────────────────────
     {Group}:
       {Label}       : {value}               ✓
       {Label}       : —                     (will extract)
     ...

     These figures are authoritative ground truth.
     Confirm? [Y/n]:
   ```
7. Store `user_figures_path` = path to the edited file

**If user selects [2]:**
Set `user_figures_path = null`. All figures extracted from documents.

### Fallback Cascade for Financial Figures

Every figure in the final document resolves through this priority chain:

```
Priority 1: User-provided figure  → source: "user_input",  confidence: 1.0
Priority 2: Extracted from docs   → source: "{filename}",  confidence: 0.x
Priority 3: [DATA NOT AVAILABLE]  → explicit gap marker in the document
```

- **Priority 1** applies when `figures_mode` is `user` or `hybrid` and the user
  filled in the field. These are never overridden by extraction.
- **Priority 2** applies for all blank fields (hybrid/auto mode). Phase 2
  analyzers extract from loan folder documents. Conflicts between multiple
  source documents are flagged in cross-reference issues.
- **Priority 3** applies when neither user nor extraction produced a value.
  The designer writes `[DATA NOT AVAILABLE]` and the validator flags it as
  a data gap (severity: recommended, not required — so it won't block the
  Wigum loop unless the benchmark marks that field as required).

Phase 4 validators check figures against this cascade:
- User-provided figures are GROUND TRUTH — matching them = PASS
- Extracted figures are BEST EFFORT — contradicting them = NOTE (not FAIL)
- `[DATA NOT AVAILABLE]` is an explicit gap — flagged for user awareness

### Step 0.5b: Target Page Count

**Quick mode / Batch mode:** Set `target_pages` to the midpoint of `catalog_entry.default_page_range`
(e.g., if `default_page_range: [5, 10]`, set `target_pages = 8`). Skip the prompt.
For batch mode, compute this per `batch_item` using each item's `catalog_entry`.

**Detailed mode:** Continue below.

```
Step 5 of 8: Document length

  Recommended for {catalog_entry.label}: {default_page_range[0]}-{default_page_range[1]} pages

  [1] Short     ({default_page_range[0]} pages)
  [2] Standard  ({midpoint} pages)
  [3] Extended  ({default_page_range[1]} pages)
  [4] Custom    (enter your own target)
  [5] No limit  (let the content determine length)

Enter selection [1-5]:
```

If [4], prompt: `Target pages: _`. Store the entered number.
If [5], set `target_pages = null` (no constraint).
Otherwise, map to the appropriate value.

**Calculate per-section page budgets:**

For each section in `catalog_entry.default_sections`:
- Base weight: 1.0
- If `full_data_access: true`: weight = 1.5
- Section budget = `target_pages * (section_weight / total_weight)`

Store `target_pages` and `page_budget` dict (section_name → pages) in the manifest.

### Step 0.5c: Images / Photos

**Quick mode / Batch mode:** Set `images = []`, `image_placement_strategy = null`. Skip the prompt.

**Detailed mode:** Continue below.

```
Step 6 of 8: Images & photos  (optional — press Enter to skip)

  Include property photos, site plans, maps, or other images?

  Enter image paths (one per line, optional caption after |):
    /path/to/photo.jpg | Aerial view of property
    /path/to/site-plan.png | Site plan showing Phase I and Phase II
    /path/to/map.png

  (Press Enter twice when done, or Enter once to skip)

  Images: _
```

If images provided, prompt for placement strategy:

```
  Image placement:
  [1] Auto         — place where contextually relevant
  [2] After header — place immediately after section headings
  [3] Appendix     — group all images in an appendix at the end

Enter selection [1-3]:
```

Parse each line: split on `|`, first part = path (trimmed), second = caption (trimmed, optional).
Validate each path exists.

Store `images` list (each entry: `{path, caption, placement}`) and `image_placement_strategy`
(`auto`, `after-header`, or `appendix`).

### Step 0.6: Additional Instructions

**Quick mode / Batch mode:** Set `additional_instructions = null`. Skip the prompt.

**Detailed mode:** Continue below.

```
Step 7 of 8: Additional instructions  (optional — press Enter to skip)

  Add any specific requirements, custom clauses, emphasis areas,
  or context that should guide the document generation:

  Examples:
    "Include a 3-year financial summary table in the Financial Analysis"
    "Borrower is a repeat client — tone should be relationship-oriented"
    "Use California law conventions for the governing law section"
    "Flag any covenant breaches prominently"

  Instructions: _
```

Store as `additional_instructions`. If the user presses Enter with no input, set to `null`.

### Step 0.7: Phase 2 Cache Check

Compute `loan_folder_fingerprint`:
1. List all files in `loan_folder_path` recursively with their sizes
2. Sort the list, concatenate filenames+sizes, compute sha256

Check for `.acos/loan-doc-generator/cache/{loan_folder_fingerprint}/phase2-cache-manifest.yaml`.

If found, read the manifest and compare:
- `manifest.file_count` vs. current file count
- `manifest.folder_mtime` vs. current latest file mtime

- **Unchanged:** Prompt: `"Loan folder analysis found in cache (analyzed {date_analyzed}). Reuse? [Y/n]: "`. If Y: `skip_phase_2 = true`, load `loan_data_path` and `loan_data_brief_path` from manifest.
- **Changed:** Display: `"Loan folder has changed since last analysis. Re-running Phase 2."`. Set `skip_phase_2 = false`.
- **Not found:** `skip_phase_2 = false`.

### Step 0.8: Confirmation & Bootstrap

Generate `session_id`: `YYYYMMDD-HHMMSS`.

Display confirmation:

**Single document mode (quick/detailed):**

```
╔══════════════════════════════════════════════════════════════╗
║ Ready to Generate                                           ║
╠══════════════════════════════════════════════════════════════╣
║  Mode          : {interview_mode}                           ║
║  Document      : {document_title}                           ║
║  Design Source : {label or path}                            ║
║  Loan Folder   : {loan_folder_path}                         ║
║  Figures Mode  : {figures_mode}                              ║
║  Target Pages  : {target_pages or "no limit"}               ║
║  Images        : {len(images) or "none"}                    ║
║  Instructions  : {additional_instructions or "none"}        ║
║  Session ID    : {session_id}                               ║
╚══════════════════════════════════════════════════════════════╝

  Phases to run:
    {✓ skipped / ☐ pending} Phase 1: Design Extraction
    {✓ skipped / ☐ pending} Phase 2: Loan Folder Analysis
    ☐ Phase 3: Document Design
    ☐ Phase 4: Validation + Wigum Loop

Proceed? [Y/n]:
```

**Batch mode:**

```
╔══════════════════════════════════════════════════════════════╗
║ Ready to Generate — Batch Mode ({N} documents)              ║
╠══════════════════════════════════════════════════════════════╣
║  Loan Folder   : {loan_folder_path}                         ║
║  Session ID    : {session_id}                               ║
╠──────────────────────────────────────────────────────────────╣
║  #  DOCUMENT                     DESIGN         PAGES  PH1  ║
║  1  Credit Memo — Internal       Library: ...   8      Skip ║
║  2  Credit Memo — External       New: /path     8      Run  ║
║  3  Deal Document                Library: ...   6      Skip ║
╠──────────────────────────────────────────────────────────────╣
║  Shared Phase 2: {✓ cached / ☐ pending}                     ║
║  Phase 1 runs:   {count needing extraction} of {N}          ║
║  Phase 3+4 runs: {N} (parallel)                             ║
╚══════════════════════════════════════════════════════════════╝

Proceed? [Y/n]:
```

On confirmation:

1. Bootstrap config if `.acos/loan-doc-generator/config.yaml` does not exist:
   Copy `templates/loan-doc-config.yaml` → `.acos/loan-doc-generator/config.yaml`

2. Bootstrap design library index if not present:
   Create `.acos/loan-doc-generator/design-library/` directory.
   Copy `templates/design-library-index.yaml` → `.acos/loan-doc-generator/design-library/index.yaml`

3. Create session workspace:
   ```
   .acos/loan-doc-generator/sessions/{session_id}/
   ├── session-manifest.yaml
   ├── phase2-analysis/
   ├── phase3-design/
   ├── phase4-validation/
   └── output/
   ```

4. Write `session-manifest.yaml`:

   **Single document mode (quick/detailed):**
   ```yaml
   session_id: "{session_id}"
   date: "YYYY-MM-DD HH:MM:SS"
   interview_mode: "quick"           # quick|detailed
   batch_mode: false
   category_id: ""                   # e.g., credit-underwriting
   document_id: ""                   # e.g., credit-underwriting/internal-credit-memo
   document_title: ""
   design_source: "library|new"
   design_label: ""
   design_patterns_path: ""
   benchmark_criteria_path: ""
   examples_path: ""
   loan_folder_path: ""
   loan_data_path: ""
   loan_data_brief_path: ""
   figures_mode: "auto"
   user_figures_path: null
   additional_instructions: null
   target_pages: null                # null = no constraint
   page_budget: {}                   # per-section budgets (section_name → pages)
   images: []                        # [{path, caption, placement}]
   image_placement_strategy: null    # null|auto|after-header|appendix
   skip_phase_1: false
   skip_phase_2: false
   status: "in-progress"
   current_phase: 1
   current_iteration: 0
   ```

   **Batch mode:**
   ```yaml
   session_id: "{session_id}"
   date: "YYYY-MM-DD HH:MM:SS"
   interview_mode: "batch"
   batch_mode: true
   loan_folder_path: ""
   loan_data_path: ""               # shared — populated after Phase 2
   loan_data_brief_path: ""         # shared — populated after Phase 2
   skip_phase_2: false
   figures_mode: "auto"             # batch always uses auto
   status: "in-progress"
   current_phase: 1
   batch_items:
     - batch_index: 1
       category_id: ""
       document_id: ""
       document_title: ""
       design_source: "library|new"
       design_label: ""
       design_patterns_path: ""
       benchmark_criteria_path: ""
       examples_path: ""
       target_pages: null
       page_budget: {}
       skip_phase_1: false
       status: "pending"            # pending|phase1|phase34|complete|failed
       output_path: ""
     - batch_index: 2
       # ... same structure
   ```

   For batch mode, also create per-item subdirectories:
   ```
   .acos/loan-doc-generator/sessions/{session_id}/
   ├── session-manifest.yaml
   ├── phase2-analysis/              ← shared
   ├── batch-1/                      ← per-document
   │   ├── phase3-design/
   │   ├── phase4-validation/
   │   └── output/
   ├── batch-2/
   │   ├── phase3-design/
   │   ├── phase4-validation/
   │   └── output/
   └── output/
       └── batch-report.md           ← combined provenance + results
   ```

---

## Phase Dispatch

After Phase 0 completes, dispatch to phase orchestrator agents.
The `manifest_path` is `.acos/loan-doc-generator/sessions/{session_id}/session-manifest.yaml`.

### Single Document Dispatch (quick/detailed)

#### Dispatch Phase 1 (if needed)

If `skip_phase_1 = false`:

```
Task(loan-doc-phase1)
  - prompt: |
      Session manifest: {manifest_path}
      Execute Phase 1: Design Extraction.
      Read your instructions from:
      .claude/skills/acos-loan-doc-generator/phases/phase1-extract.md
```

Wait for completion. Report Phase 1 results to user.

If `skip_phase_1 = true`:
Report: `"Phase 1 skipped — using cached design from library: {design_label}"`

#### Dispatch Phase 2 (if needed)

If `skip_phase_2 = false`:

```
Task(loan-doc-phase2)
  - prompt: |
      Session manifest: {manifest_path}
      Execute Phase 2: Loan Folder Analysis.
      Read your instructions from:
      .claude/skills/acos-loan-doc-generator/phases/phase2-analyze.md
```

Wait for completion. Report Phase 2 results to user.

If `skip_phase_2 = true`:
Report: `"Phase 2 skipped — using cached loan analysis from {date_analyzed}"`

#### Dispatch Phase 3+4

```
Task(loan-doc-phase34)
  - prompt: |
      Session manifest: {manifest_path}
      Execute Phase 3 (Document Design) + Phase 4 (Validation + Wigum Loop).
      Read your instructions from:
      .claude/skills/acos-loan-doc-generator/phases/phase3-design.md
      .claude/skills/acos-loan-doc-generator/phases/phase4-validate.md
      Handle all Wigum loop iterations internally.
```

Wait for completion.

### Batch Dispatch

When `batch_mode = true`, orchestrate phases with shared loan analysis and parallel
document generation.

#### Batch Step 1: Parallel Phase 1 Extractions

Collect all `batch_items` where `skip_phase_1 = false`. If any exist, dispatch
**all of them simultaneously** in a single message using `run_in_background: true`:

```
For each batch_item where skip_phase_1 = false:

Task(loan-doc-phase1)
  - run_in_background: true
  - prompt: |
      Session manifest: {manifest_path}
      Batch item index: {batch_index}
      Execute Phase 1: Design Extraction for "{document_title}" ({category_id}).
      Read your instructions from:
      .claude/skills/acos-loan-doc-generator/phases/phase1-extract.md
      Write outputs to: batch-{batch_index}/ subdirectory within the session.
```

Wait for all Phase 1 agents to complete. Report results:

```
Phase 1 — Design Extraction:
  ✓ Credit Memo — Internal     Skipped (cached: pe-format-2024)
  ✓ Credit Memo — External     Extracted (5 patterns, 12 benchmarks)
  ✓ Deal Document              Skipped (cached: deal-v2)
```

Update each `batch_item.status` to `"phase1-complete"` and populate
`design_patterns_path` and `benchmark_criteria_path` in the manifest.

#### Batch Step 2: Shared Phase 2

Phase 2 runs once — it analyzes the loan folder that all documents share.

If `skip_phase_2 = false`:

```
Task(loan-doc-phase2)
  - prompt: |
      Session manifest: {manifest_path}
      Execute Phase 2: Loan Folder Analysis (shared across batch).
      Read your instructions from:
      .claude/skills/acos-loan-doc-generator/phases/phase2-analyze.md
```

Wait for completion. Update `loan_data_path` and `loan_data_brief_path` in the
manifest (these are shared by all batch items).

If `skip_phase_2 = true`:
Report: `"Phase 2 skipped — using cached loan analysis from {date_analyzed}"`

#### Batch Step 3: Parallel Phase 3+4

Dispatch **all batch items simultaneously** for document design and validation.
Each document type gets its own `Task(loan-doc-phase34)` agent in its own context
window, running in parallel via `run_in_background: true`:

```
For each batch_item:

Task(loan-doc-phase34)
  - run_in_background: true
  - prompt: |
      Session manifest: {manifest_path}
      Batch item index: {batch_index}
      Document: "{document_title}" ({category_id})
      Execute Phase 3 (Document Design) + Phase 4 (Validation + Wigum Loop).
      Read your instructions from:
      .claude/skills/acos-loan-doc-generator/phases/phase3-design.md
      .claude/skills/acos-loan-doc-generator/phases/phase4-validate.md
      Handle all Wigum loop iterations internally.
      Write outputs to: batch-{batch_index}/ subdirectory within the session.
      Use shared loan data from: {loan_data_path}
      Use design patterns from: {batch_item.design_patterns_path}
      Use benchmarks from: {batch_item.benchmark_criteria_path}
```

Wait for **all** Phase 3+4 agents to complete. Display progress as each finishes:

```
Phase 3+4 — Document Generation:
  ✓ Credit Memo — Internal     PASS  (2 iterations, 95% pass rate)
  ✓ Credit Memo — External     PASS  (1 iteration, 100% pass rate)
  ⏳ Deal Document              Running... (iteration 3)
```

Update each `batch_item.status` to `"complete"` or `"failed"` based on results.

### Report Final Results

#### Single Document Report

**Step R.1: Data Provenance Table**

After Phase 3+4 completes (regardless of PASS/FAIL), generate a data provenance table:

1. Read `loan-data.yaml` at `loan_data_path` — each data point has `source_document` and `source_page` fields
2. Read the final document draft to identify which data points were actually used
3. Cross-reference: for each key figure appearing in the document, find its source in loan-data.yaml
4. Display the provenance table in the context window:

```
╔══════════════════════════════════════════════════════════════╗
║ Data Provenance                                              ║
╠══════════════════════════════════════════════════════════════╣

DATA / VALUE              │ SOURCE DOCUMENT         │ PAGE │ LINK
──────────────────────────┼─────────────────────────┼──────┼──────────
Loan Amount: $2,100,000   │ Loan Agreement.pdf      │ 2    │ file://...
Borrower: Cook Group LLC  │ Application.pdf         │ 1    │ file://...
Interest Rate: 7.25%      │ Term Sheet.pdf          │ 1    │ file://...
Property Value: $3,200,000│ Appraisal.pdf           │ 5    │ file://...
...

{count} data points traced  │  {gap_count} gaps (DATA NOT AVAILABLE)
╚══════════════════════════════════════════════════════════════╝
```

5. Write the provenance table to:
   `.acos/loan-doc-generator/sessions/{session_id}/output/provenance-table.md`

   Format as a markdown table with columns: Data Point, Value, Source Document, Page, File Link.
   Include a `file://` link to the source document for each entry.
   Flag any `[DATA NOT AVAILABLE]` entries at the bottom.

**Step R.2: Results Display**

Based on Phase 3+4 return:

**If PASS:**
```
╔══════════════════════════════════════════════════════════════╗
║ Document Generated Successfully                             ║
╠══════════════════════════════════════════════════════════════╣
║  Document      : {document_title}                           ║
║  Iterations    : {count}                                    ║
║  Pass Rate     : {rate}                                     ║
║  Output        : {output_path}                              ║
║  Provenance    : {provenance_table_path}                    ║
║  Validation    : {validation_report_path}                   ║
╚══════════════════════════════════════════════════════════════╝
```

**If FAIL (max iterations):**
```
╔══════════════════════════════════════════════════════════════╗
║ Document Generated — Validation Incomplete                  ║
╠══════════════════════════════════════════════════════════════╣
║  Document      : {document_title}                           ║
║  Iterations    : {count}/{max}                              ║
║  Pass Rate     : {rate}                                     ║
║  Remaining     : {failure_count} required failures          ║
║  Output        : {output_path}                              ║
║  Validation    : {validation_report_path}                   ║
╚══════════════════════════════════════════════════════════════╝

Remaining failures:
{list each with criterion, section, fix instruction}

Options:
1. Accept the current draft as-is
2. Manually edit the draft and re-run validation
3. Increase max_iterations in config and re-run
```

#### Batch Report

When `batch_mode = true`, generate a combined report after all Phase 3+4 agents
complete.

**Step R.1b: Combined Data Provenance**

Generate a single provenance table that covers all documents in the batch. Since
all documents share the same loan folder analysis (Phase 2), many data points will
be reused across documents. The combined table deduplicates shared data:

1. Read `loan-data.yaml` (shared Phase 2 output)
2. For each batch item, read its final document draft from `batch-{N}/output/`
3. Cross-reference all documents against the shared loan data
4. Display the combined provenance:

```
╔══════════════════════════════════════════════════════════════╗
║ Batch Provenance — {N} Documents                             ║
╠══════════════════════════════════════════════════════════════╣

DATA / VALUE              │ SOURCE DOCUMENT      │ PAGE │ USED IN
──────────────────────────┼──────────────────────┼──────┼───────────────
Loan Amount: $2,100,000   │ Loan Agreement.pdf   │ 2    │ All 3 docs
Borrower: Cook Group LLC  │ Application.pdf      │ 1    │ All 3 docs
Interest Rate: 7.25%      │ Term Sheet.pdf       │ 1    │ CM-Int, CM-Ext
Property Value: $3,200,000│ Appraisal.pdf        │ 5    │ CM-Int, Deal
LTV Ratio: 65.6%          │ (calculated)         │ —    │ CM-Int
...

{count} data points  │  {shared} shared across docs  │  {gap_count} gaps
╚══════════════════════════════════════════════════════════════╝
```

5. Write to `.acos/loan-doc-generator/sessions/{session_id}/output/batch-report.md`

**Step R.2b: Batch Results Summary**

```
╔══════════════════════════════════════════════════════════════════════╗
║ Batch Generation Complete — {pass_count}/{N} passed                 ║
╠══════════════════════════════════════════════════════════════════════╣
║  #  DOCUMENT                     RESULT  ITER  PASS RATE  OUTPUT    ║
║  1  Credit Memo — Internal       PASS    2     95%        file://.. ║
║  2  Credit Memo — External       PASS    1     100%       file://.. ║
║  3  Deal Document                FAIL    5/5   72%        file://.. ║
╠──────────────────────────────────────────────────────────────────────╣
║  Shared loan analysis   : {loan_data_path}                          ║
║  Combined provenance    : {batch_report_path}                       ║
║  Session workspace      : {session_path}                            ║
╚══════════════════════════════════════════════════════════════════════╝
```

If any documents failed validation, list their remaining failures grouped by
document. Offer the same options as single-document mode (accept/edit/retry)
but applied per-document.

---

## Status Command

When `$ARGUMENTS` contains `status`:

```
ACOS Loan Document Generator — Status
=======================================

Configuration: .acos/loan-doc-generator/config.yaml
  [path or "not configured"]

Design Library:  (.acos/loan-doc-generator/design-library/index.yaml)
  CATEGORY                      DESIGN ID                    EXAMPLES  ADDED
  credit-memo-internal          pe-format-2024               5         2026-02-15
  loan-agreement                bank-style-2024              4         2026-03-01

Cached Extractions:
  SESSION ID          DATE        CATEGORY               DOCS  STATUS
  20260215-091500     2026-02-15  credit-memo-internal   5     complete

Phase 2 Cache:
  FINGERPRINT         LOAN FOLDER                        ANALYZED
  sha256-abc123...    /path/to/loan-folder/              2026-03-01

Active Sessions:
  SESSION ID          DOCUMENT                           PHASE  ITER  STATUS
  20260309-143022     Bridge Loan Agreement              3      1     in-progress
```

---

## Data Flow Reference

**Single document mode:**
```
Phase 0 (this context) ──→ session-manifest.yaml ──→ all phases read this

Phase 1 Agent ─┬─ design-patterns.yaml ──→ Phase 2 + 3 + 4
               └─ benchmark-criteria.yaml ──→ Phase 4

Phase 2 Agent ─┬─ loan-data.yaml ──→ Phase 3 + 4
               └─ loan-data-brief.yaml ──→ Phase 3 + 4

Phase 3+4 Agent ─── document-draft.md ──→ validators ──→ Wigum loop ──→ output

Phase 0 (post) ─── loan-data.yaml ──→ provenance-table.md (cross-ref with draft)

Design Library ──→ Phase 0 (skip Phase 1 if cached)
Phase 2 Cache  ──→ Phase 0 (skip Phase 2 if unchanged)
```

**Batch mode:**
```
Phase 0 ──→ session-manifest.yaml (with batch_items array)
         │
         ├─→ Phase 1 Agent [doc-1] ─┬─ design-patterns.yaml ──→ batch-1/
         ├─→ Phase 1 Agent [doc-2] ─┤  (parallel, only for uncached)
         │   ...                    └─ benchmark-criteria.yaml
         │
         ├─→ Phase 2 Agent (shared) ─┬─ loan-data.yaml ──→ all batch items
         │                           └─ loan-data-brief.yaml
         │
         ├─→ Phase 3+4 Agent [doc-1] ──→ batch-1/output/ ─┐
         ├─→ Phase 3+4 Agent [doc-2] ──→ batch-2/output/ ─┤ (parallel)
         ├─→ Phase 3+4 Agent [doc-3] ──→ batch-3/output/ ─┘
         │
         └─→ Phase 0 (post) ──→ batch-report.md (combined provenance)
```

---

## File Layout

```
.claude/skills/acos-loan-doc-generator/
├── SKILL.md                         ← This file (thin router)
├── phases/
│   ├── phase1-extract.md            ← Phase 1 orchestrator instructions
│   ├── phase2-analyze.md            ← Phase 2 orchestrator instructions
│   ├── phase3-design.md             ← Phase 3 orchestrator instructions
│   └── phase4-validate.md           ← Phase 4 orchestrator instructions
└── templates/
    ├── loan-doc-config.yaml
    ├── doc-type-catalog.yaml
    ├── design-library-index.yaml
    ├── design-pattern.yaml
    ├── benchmark-criterion.yaml
    ├── loan-data-extract.yaml
    ├── loan-data-brief.yaml
    ├── validation-result.yaml
    └── pdf-styles.css              ← CSS pagination + typography rules

.claude/agents/
├── loan-doc-phase1.md               ← Phase 1 orchestrator agent
├── loan-doc-phase2.md               ← Phase 2 orchestrator agent
└── loan-doc-phase34.md              ← Phase 3+4 orchestrator agent
```

---

*ACOS Loan Document Generator — Quick/Detailed/Batch interview modes, CSS pagination,
page count control, image support, data provenance, delegated phase orchestration
with design library, Phase 2 caching, parallel batch generation, section-scoped
validation, and benchmark-driven Wigum loop.*
