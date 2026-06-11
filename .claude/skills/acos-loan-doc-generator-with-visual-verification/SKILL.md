---
name: acos-loan-doc-generator-with-visual-verification
description: |
  Multi-phase swarm-based private equity loan document generator with screenshot-first
  visual verification. All output formats (PPTX, PDF, DOCX) are rendered to screenshots
  and visually inspected before delivery. Three validation gates: data/code, layout,
  and visual screenshot review. The visual gate is authoritative — if it looks wrong
  in a screenshot, it's a fail regardless of what the code-level checks say.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task(loan-doc-phase1), Task(loan-doc-phase2), Task(loan-doc-phase34)
---

# ACOS Loan Document Generator (with Visual Verification)

## Purpose

Generate institutional-quality private equity loan documents from loan folders
using a 6-step pipeline with **delegated phase orchestration** and **screenshot-first
visual verification**:

1. **Interview** — Quick/Detailed wizard: type, design, folder, figures, page count, images (runs here)
2. **Extract** — Learn design patterns and benchmarks (delegated to `loan-doc-phase1` agent)
3. **Analyze** — Deep-read loan folder, extract data (delegated to `loan-doc-phase2` agent)
4. **Design + Validate** — Write document, validate data/structure, Wigum loop (delegated to `loan-doc-phase34` agent)
5. **Visual QA** — Render screenshots, review every page/slide visually, fix defects in Wigum loop (integrated into Phase 4)
6. **Report** — Data provenance table, results display (runs here)

**Key Difference from base skill:** Step 5 (Visual QA) renders every output document
to PNG screenshots and the agent visually inspects each one for design defects.
This catches issues that code-level validation misses: text wrapping artifacts,
color contrast problems, spacing imbalance, visual hierarchy issues, and
cross-page/slide style drift.

**Architecture**: The primary context window handles ONLY the interactive interview
(Phase 0) and phase dispatching. All heavy reading, agent spawning, and iteration
happens inside phase orchestrator agents — each in their own context window.

## Visual Verification Pipeline

```
Phase 3: Build Document (PPTX / HTML→PDF+DOCX)
    │
    ├── Build-time guard rails (auto-size containers, pre-check overlaps)
    │
    ▼
Gate 1: Data & Code Check (format-specific)
    │   PPTX: validate-pptx.py (data, fonts, colors, anchors)
    │   PDF:  structural + quality validators (content accuracy)
    │   → If FAIL: Wigum loop back to Phase 3
    │
    ▼
Gate 2: Layout Pre-Check (format-specific)
    │   PPTX: check-pptx-layout.py (bounds, overlaps, text overflow estimation)
    │   PDF:  check-pdf-layout.py (margins, orphans, table splits)
    │   → If FAIL: Wigum loop back to Phase 3 with coordinate fixes
    │
    ▼
Gate 3: Visual Screenshot Review (ALL formats)
    │   render-doc-audit.py → PNG per page/slide at 150 DPI (≤2000px safety cap)
    │   → Agent reads each screenshot via Read tool
    │   → Evaluates ALL visual criteria:
    │       • Text overflow, clipping, orphans
    │       • Color contrast & palette compliance
    │       • Table styling & alignment
    │       • Typography consistency
    │       • Spacing, crowding, dead space
    │       • Visual hierarchy & reading flow
    │       • Image placement & quality
    │       • Page break quality (PDF/DOCX)
    │       • Cross-page/slide consistency
    │   → If ANY error-level visual defect: Wigum loop back to Phase 3
    │
    ▼
PASS → Output final document
```

**The visual gate is authoritative.** If code checks pass but screenshots show
a problem, it's a fail. The screenshot is what the recipient will see.

### Visual QA Scripts

| Script | Purpose | Formats |
|--------|---------|---------|
| `render-doc-audit.py` | Render any document to PNG screenshots at 150 DPI (≤2000px safety cap) | PPTX, PDF, DOCX |
| `check-pptx-layout.py` | Fast coordinate-level PPTX layout check | PPTX only |
| `check-pdf-layout.py` | Fast text-position PDF layout check | PDF only |

### Wigum Loop Iteration Limits

| Format | Default max_iterations | Reason |
|--------|----------------------|--------|
| PDF/DOCX | 5 (up from 3) | Visual fixes often reveal secondary issues |
| PPTX | 5 (up from 3) | Same — coordinate fixes can cascade |

---

## Phase 0: Interview Wizard

All user interaction happens here. No CLI argument parsing except `status` and `resume`.

### UX Principles (apply throughout all steps)

- **Be concise.** Show only what the user needs to decide. No verbose explanations.
- **Smart defaults.** Pre-fill obvious choices. Quick mode = minimal questions.
- **No noise.** Sample file:// links are hidden by default. Agent internals stay in logs.
- **Progress clarity.** Show step N of M. Show phase progress during dispatch.
- **Fail gracefully.** One clear error message with what went wrong and what to do next.
- **Output format.** ALWAYS produce DOCX + PDF. Never .html, .md, or any other format.
- **Navigation.** Every step (except Step 0.0) shows `[<] Back` to return to the
  previous step. At the confirmation step (0.8), numbered fields allow jumping to
  any specific step. When revisiting a step after back-navigation, show the
  previously-entered value as a default — pressing Enter with no input keeps it.

### Back-Navigation Rules (apply to ALL steps)

When the user enters `<` or `back` at any step prompt:

1. Re-display the **previous step's** prompt
2. Show the current stored value: `(current: {value})`
3. Offer to keep it: `"Enter selection or press Enter to keep [{current}]"`
4. If the user enters a new value, overwrite the stored variable
5. If the user presses Enter with no input, keep the existing value and advance forward
6. After the step completes, proceed forward from that step as normal

**State invalidation on change:**
- If `interview_mode` changes (Step 0.0): clear all mode-specific fields (figures,
  images, charts, instructions, page count) to their defaults
- If `document_id` changes (Step 0.2): set `selected_library_entry = null`,
  re-run the design library lookup when reaching Step 0.3
- If `category_id` changes (Step 0.1): clear `document_id` and cascade above

**Batch mode back-navigation:**
- During the category loop: `<` returns to the previous category's document selection,
  removing documents added from the current (cancelled) category
- During per-item design resolution: `<` returns to the previous item's design prompt
- At batch confirmation: numbered jump can target category re-selection or a specific
  item's design source

If `$ARGUMENTS` contains `status`, skip to the **Status Command** section.
If `$ARGUMENTS` contains `resume`, skip to the **Resume Mode** section in Phase Dispatch.

### Step 0.0: Mode Selection

Display the mode selection first:

```
╔══════════════════════════════════════════════════════════════╗
║        ACOS Loan Document Generator                         ║
╚══════════════════════════════════════════════════════════════╝

  [1] Quick      — minimal prompts, smart defaults, fast generation
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
Step {1 of 4 if quick | 1 of 8 if detailed | 1 of 4 if batch}: Select a document category
{if revisiting: "(current: {letter} — {category_name})"}

  [A]  Credit Memo & Underwriting
  [B]  Closing & Administration
  [C]  Portfolio Management
  [D]  Loan Modifications & Workout
  [E]  Investor & Participation
  [F]  Other

Enter selection [A-F]{if revisiting: " or Enter to keep [{current}]"}:           [<] Back
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

Store as `category_id`. Also store the human-readable label as `category_name` (e.g., "Credit Memo & Underwriting" for category A).

### Step 0.2: Document Type Selection

**If category is F (Other):**

Display existing named types in this category from `doc-type-catalog.yaml`,
plus special options:

```
  Category F — Other:
  [1]  Borrower Resolution          (corporate authorization, entity resolution)
  [2]  FIRPTA Certificate           (foreign investment tax certificate)
  [3]  Title Requirements Letter    (title company/closing agent directives)
  ─────────────────────────────────────────────────────
  [C]  Quick custom (name only, generic template)
  [N]  Define a new document type

Enter selection [1-3, C, N]:           [<] Back
```

**If user selects [1-3]:** Load the matching catalog entry by `document_id`.
Store `document_id`, `document_title`, `catalog_entry` as normal.

**If user selects [C]:** Prompt for document name:

```
  Document name: _
```

Store the entered value as `document_title`. Generate `document_id` by slugifying
the title: `"other/" + document_title.lower().replace(/[^a-z0-9]+/g, "-").strip("-")`
(e.g., "Promissory Note" → `other/promissory-note`).
Load the `other/custom` fallback entry from `templates/doc-type-catalog.yaml`.

**If user selects [N]:** Jump to **Step 0.2N: New Document Type Definition** below.

**For categories A–E**, display the documents within the selected category:

**Category A — Credit Memo & Underwriting:**
```
  [1]  Internal Credit Memo        (risk-focused, credit committee)
  [2]  External Credit Memo        (marketing document, broker-facing)
  [3]  Term Sheet                   (proposed deal terms)
  [4]  Deal Memo                    (deal summary, committee presentation)
  [5]  Scoping Letter               (preliminary interest, high-level terms)
  [6]  Executive Summary            (deal overview, one-pager)
  ─────────────────────────────────────────────────────
  [N]  Define a new document type in this category

Enter selection [1-6, N]:           [<] Back
```

**Category B — Closing & Administration:**
```
  [1]  Closing Summary / Checklist  (closing items, conditions, status)
  [2]  Settlement Statement         (final transaction amounts, disbursements)
  [3]  Escrow Instructions          (escrow agent directives, conditions)
  [4]  Wire Instructions            (wire transfer details, routing)
  [5]  Transaction Checklist        (pre/post-close task tracking)
  [6]  Loan Agreement              (bridge, construction, mezzanine)
  [7]  Guarantee Document          (personal, carve-out, completion)
  ─────────────────────────────────────────────────────
  [N]  Define a new document type in this category

Enter selection [1-7, N]:           [<] Back
```

**Category C — Portfolio Management:**
```
  [1]  Payoff Statement / Letter    (outstanding balance, per-diem, payoff terms)
  [2]  Redemption Statement         (investor redemption amounts, timing)
  [3]  Draw Request                  (construction/renovation disbursement)
  ─────────────────────────────────────────────────────
  [N]  Define a new document type in this category

Enter selection [1-3, N]:           [<] Back
```

**Category D — Loan Modifications & Workout:**
```
  [1]  Extension Request Questionnaire  (borrower extension request form)
  [2]  Loan Extension Agreement         (extension terms, modified conditions)
  [3]  Forbearance Agreement            (temporary relief, modified payment terms)
  [4]  Pre-Foreclosure Notice           (default notice, cure period)
  [5]  Demand Letter                    (payment demand, legal notice)
  [6]  Foreclosure Complaint       (judicial foreclosure filing)
  ─────────────────────────────────────────────────────
  [N]  Define a new document type in this category

Enter selection [1-6, N]:           [<] Back
```

**Category E — Investor & Participation:**
```
  [1]  Investor Participation Agreement  (participation terms, pro-rata shares)
  [2]  Investor Update / Report          (portfolio performance, deal updates)
  [3]  Participation Interest Offering  (presentation, investor marketing)
  ─────────────────────────────────────────────────────
  [N]  Define a new document type in this category

Enter selection [1-3, N]:           [<] Back
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
| B | 6 | `closing-admin/loan-agreement` | Loan Agreement |
| B | 7 | `closing-admin/guarantee-document` | Guarantee Document |
| C | 1 | `portfolio-management/payoff-statement` | Payoff Statement / Letter |
| C | 2 | `portfolio-management/redemption-statement` | Redemption Statement |
| C | 3 | `portfolio-management/draw-request` | Construction / Renovation Draw Request |
| D | 1 | `loan-modifications/extension-request` | Extension Request Questionnaire |
| D | 2 | `loan-modifications/extension-agreement` | Loan Extension Agreement |
| D | 3 | `loan-modifications/forbearance-agreement` | Forbearance Agreement |
| D | 4 | `loan-modifications/pre-foreclosure-notice` | Pre-Foreclosure Notice |
| D | 5 | `loan-modifications/demand-letter` | Demand Letter |
| D | 6 | `loan-modifications/foreclosure-complaint` | Foreclosure Complaint |
| E | 1 | `investor-participation/participation-agreement` | Investor Participation Agreement |
| E | 2 | `investor-participation/investor-report` | Investor Update / Report |
| E | 3 | `investor-participation/participation-offering` | Participation Interest Offering |
| F | 1 | `other/borrower-resolution` | Borrower Resolution |
| F | 2 | `other/firpta-certificate` | FIRPTA Certificate |
| F | 3 | `other/title-requirements-letter` | Title Requirements Letter |
| F | C | `other/custom` | (user-specified, quick custom) |
| F | N | — | (new document type definition) |

Load the matching entry from `templates/doc-type-catalog.yaml` using `document_id`.
Store as `catalog_entry`. Set `document_title` from the table above (or user input for F).

**When the user selects [N] at any category (A–F):** Jump to Step 0.2N below.

### Step 0.2N: New Document Type Definition

This sub-flow is triggered when the user selects `[N]` in any category. It creates
a fully-defined document type entry and persists it to `doc-type-catalog.yaml`.

Show a sub-step counter: "New type -- step X of Y" where Y depends on the path:
Path 1 (example): Y=4, Path 2 (manual): Y=5, Path 3 (AI-generated): Y=2.

```
  Define a new document type
  ─────────────────────────────────────────────────────

  Category: {current category_name} (from Step 0.1)

  How would you like to define this document type?

  [1]  From example  — provide a sample doc, I'll learn the structure
  [2]  Manual        — describe the sections, I'll build the definition
  [3]  AI-generated  — I'll generate a definition from the name alone

Enter selection [1-3]:           [<] Back
```

#### Path 1: From Example (recommended)

1. Prompt for document name:
   ```
     Document name: _
   ```

2. Prompt for example document path:
   ```
     Enter path to example document(s):
     Path: _
   ```
   Validate the path exists.

3. Run Phase 1 in **catalog inference mode** — dispatch to `loan-doc-phase1` with
   a special flag:
   ```
   Task(loan-doc-phase1)
     - prompt: |
         CATALOG INFERENCE MODE — do NOT write to design library yet.
         Example path: {examples_path}
         Document name: {document_name}
         Category: {category_id}
         Execute Phase 1 extraction, then run Step 1.5b to generate a
         candidate catalog entry.
         phase_instructions_path: .claude/skills/acos-loan-doc-generator-with-visual-verification/phases/
         Read phase1-extract.md from that directory.
   ```

4. Read the candidate catalog entry from Phase 1 output. Display for review:
   ```
     Inferred definition for "{document_name}":
     ──────────────────────────────────────────────────────
     ID:         {category_id}/{slugified_name}
     Pages:      {min}-{max}
     Sections:
       1. {section_name}    ({full_data_access ? "full data" : "section brief"})
       2. {section_name}    (...)
       ...
     Benchmarks: {benchmark_1}, {benchmark_2}, ...
     Critical figures: {figure_1}, {figure_2}, ...

     [A]  Approve & save
     [E]  Edit (modify sections, benchmarks, or figures)
     [R]  Reject & try again

   Enter selection [A/E/R]:
   ```

5. **If [E] Edit:** Show the candidate as YAML in a temp file, let the user edit,
   then re-read and re-display for approval.

6. **If [A] Approve:**
   - Generate `document_id`: `{category_id}/{slugified_name}`. If this ID already
     exists in the catalog, append `-v2`, `-v3`, etc.
   - Read `templates/doc-type-catalog.yaml`, parse YAML, append the new entry to
     the `documents` list with `user_defined: true`, write back the file.
   - Store `catalog_entry` with the new entry.
   - Store `document_id` and `document_title`.
   - **Shortcut:** The example used here becomes the design source. Set
     `examples_path = {path from step 2}`, `skip_phase_1 = false` (Phase 1 already
     ran in inference mode — the extraction outputs are reusable). When dispatching
     the normal Phase 1 later, check if catalog inference already produced
     `design_patterns_path`. If so, set `skip_phase_1 = true` and reuse the
     design patterns. Note: benchmark criteria were NOT extracted during catalog
     inference — Phase 1 will still need to run Track B (benchmarks). Set a flag
     `phase_1_track_b_only = true` so Phase 1 skips Track A (design extraction)
     and only runs Track B (benchmark extraction) using the already-extracted
     design patterns.
   - Continue to **Step 0.3** (design library check).

7. **If [R] Reject:** Loop back to the path selection prompt at the top of Step 0.2N.

#### Path 2: Manual Definition (4 prompts)

1. ```
     Document name: _
   ```

2. ```
     List the sections for this document (one per line, or comma-separated):
     Sections: _
   ```
   Parse into a list of section names.

3. ```
     Typical page range?
     [1] Short    (1-3 pages)
     [2] Medium   (3-8 pages)
     [3] Long     (8-15 pages)
     [4] Custom: _

   Enter selection [1-4]:
   ```

4. ```
     Document purpose/tone (one sentence):
     (e.g., "Formal legal document establishing lending commitment terms")
     Tone: _
   ```

After collecting these 4 inputs, Claude generates a full catalog entry:
- `document_id`: `{category_id}/{slugified_name}`
- `default_sections`: from user's section list, with `full_data_access` inferred
  (first and last sections = true, middle sections = false)
- `default_page_range`: from page range selection
- `benchmark_dimensions`: generate 5-7 reasonable dimensions based on document
  name and sections (e.g., "Sections Completeness", "Data Accuracy", "Legal
  Language Standards", "Formatting Consistency", "Structural Coherence")
- `structural_benchmark_items`: generate 5-8 checklist items
- `designer_tone_directive`: from the tone input
- `critical_figures`: infer common PE lending figures relevant to this document
  type (loan_amount, borrower_name, etc.)

Display the same `[A]/[E]/[R]` review gate as Path 1. On approve, persist to
`doc-type-catalog.yaml` with `user_defined: true`. Continue to **Step 0.3**.

#### Path 3: AI-Generated (1 prompt)

1. ```
     Document name: _
   ```

Claude generates the entire catalog entry using its knowledge of PE loan
documentation. This includes sections, benchmarks, page range, tone, and
critical figures — all inferred from the document name and category.

Display the same `[A]/[E]/[R]` review gate. On approve, persist to
`doc-type-catalog.yaml` with `user_defined: true`. Continue to **Step 0.3**.

#### Persistence Format

New entries appended to `templates/doc-type-catalog.yaml` follow the existing
schema exactly, with one addition:

```yaml
  - document_id: "{category_id}/{slug}"
    category_id: "{category_id}"
    label: "{document_name}"
    user_defined: true                    # ← distinguishes from built-in types
    date_added: "YYYY-MM-DD"
    default_page_range: [min, max]
    default_sections:
      - name: "Section Name"
        full_data_access: true
      # ...
    benchmark_dimensions:
      - "Dimension 1"
      # ...
    structural_benchmark_items:
      - "Item 1"
      # ...
    designer_tone_directive: |
      Tone description...
    critical_figures:
      - key: "figure_key"
        label: "Display Label"
        hint: "e.g., 15000000"
        group: "Group Name"
        required: true
      # ...
```

**Collision handling:** If `document_id` already exists in the catalog, append
a version suffix (`-v2`, `-v3`, etc.) and inform the user of the adjusted ID.

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

**Single-document batch warning:** If the final `batch_entries` list has only 1 item,
suggest switching to Quick mode: `"You selected only 1 document. Batch mode adds
overhead — switch to Quick mode? [Y/n]: "`. If Y, switch `interview_mode = "quick"`
and continue with single-document flow.

For any batch items from category F, prompt for each document name individually.

### Step 0.3: Design Library Check

Read `.acos/loan-doc-generator/design-library/index.yaml` if it exists.
Filter entries where `entry.document_id == document_id`.

**Case A — Library has 1+ designs:**

```
Step {2 of 4 if quick | 2 of 8 if detailed | 2 of 4 if batch}: Design style

  {N} design(s) available for "{catalog_entry.label}":
  ─────────────────────────────────────────────────────
  [1]  {label}                    │  Added {date_added}
  [2]  {label} (T)                │  Added {date_added}
  ...
  ─────────────────────────────────────────────────────
  (T) = template-based design (no real sample document)
  [V]  View sample for a design
  [{N+1}]  Use New Design

Enter selection [1-{N+1}] or [V]:           [<] Back
```

**Sample links are NOT shown by default** — this keeps the UI clean. If user
picks [V], prompt: `"Which design? [1-{N}]: "`, then display:
`"Sample: file://{sample_files[0]}"`. The `file://` link is clickable.

If user selects **a numbered design [1-N]**, store as `selected_library_entry`.
Set `skip_phase_1 = true`. Load `design_patterns_path` and `benchmark_criteria_path`
from the selected entry.

If user selects **[N+1] Use New Design**, prompt for example path (see Case B below).

**Case B — No designs in library for this document type:**

```
Step {2 of 4 if quick | 2 of 8 if detailed | 2 of 4 if batch}: Design style

  No designs in library for "{catalog_entry.label}". Using new design.

  Enter path to example document(s):
  (File path, directory, or glob pattern)

  Path: _                                             [<] Back
```

Validate the path exists. Store as `examples_path`. Set `skip_phase_1 = false`.

**Novelty check (Case B and "Use New Design" in Case A):**

Compute fingerprint: `document_id + ":" + realpath(examples_path)`.
Check against all entries in `design-library/index.yaml`.

- **Match found:** Prompt: `"This source was previously extracted as '{label}' (added {date_added}). Re-use cached extraction? [Y/n]: "`. If Y: `skip_phase_1 = true`, load from that library entry. If N: proceed to Phase 1.
- **No match:** `skip_phase_1 = false`. Will extract and auto-add to library after Phase 1.

**Batch mode design resolution:** Iterate through each `batch_item` and resolve
its design source independently. Display a clean summary table (no sample links):

```
  Batch design sources:
  ──────────────────────────────────────────────────────
  #  DOCUMENT                 DESIGN              PH1
  1  Credit Memo — Internal   pe-format-2024       Skip
  2  Credit Memo — External   New design           Run
  3  Deal Document            deal-v2              Skip
  ──────────────────────────────────────────────────────
  Phase 1 extractions needed: 1 of 3
```

If the user enters `<` at the design summary, return to the last batch item's design prompt.

For each item needing a new design, prompt for the examples path (one prompt per
item). Run novelty checks as in single-document mode.

### Step 0.4: Loan Folder Path

```
Step {3 of 4 if quick | 3 of 8 if detailed | 3 of 4 if batch}: Loan folder
{if revisiting: "(current: {loan_folder_path})"}

  Enter path to the loan folder for this transaction:
  Path{if revisiting: " (Enter to keep current)"}: _           [<] Back
```

Validate the path exists (check with `ls` or `stat`). If invalid, display error
and re-prompt:
```
Path not found: {path}
  Tip: Use absolute paths (e.g., /Users/zee/deals/cook-group/)
       ~ expansion is supported. Relative paths resolve from CWD.
Try again: _
```
Store as `loan_folder_path`.

### Step 0.5: Critical Numbers

**Quick mode / Batch mode:** Skip this step entirely. Set `figures_mode = "auto"`, `user_figures_path = null`.

**Detailed mode:** Continue below.

The figures shown to the user are **document-specific** — read from
`catalog_entry.critical_figures` (loaded in Step 0.2).

```
Step 4 of 8: Financial figures  (detailed mode only)

  How should critical numbers be handled?

  [1] I'll provide key numbers   — highest accuracy, fewer tokens
  [2] Extract from documents     — fully automated
  [3] Hybrid                     — I'll provide some, extract the rest

Enter selection [1-3]:           [<] Back
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

For PPTX document types (where `catalog_entry.output_format == 'pptx'`), use
`default_slide_count` instead of `default_page_range`. Store as `target_slides`
instead of `target_pages`.

**Detailed mode:** Continue below.

```
Step 5 of 8: Document length

  Recommended for {catalog_entry.label}: {default_page_range[0]}-{default_page_range[1]} pages

  [1] Short     ({default_page_range[0]} pages)
  [2] Standard  ({midpoint} pages)
  [3] Extended  ({default_page_range[1]} pages)
  [4] Custom    (enter your own target)
  [5] No limit  (let the content determine length)

Enter selection [1-5]:           [<] Back
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

  Images: _                                          [<] Back
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

### Step 0.5d: Charts & Graphs

**Quick mode:** For credit memos, auto-include must-have charts (LTV waterfall,
DSCR gauge, recommendation matrix). For other document types, no charts by default.
Set `selected_charts = "auto"`. Skip the prompt.

**Batch mode:** Same as quick mode per batch item. Skip the prompt.

**Detailed mode:** Continue below.

```
Step 6 of 8: Charts & graphs  (detailed mode only)

  ── Must-Have (credit memos only, auto-included) ──────────
  {For each chart in catalog_entry.must_have_charts:}
  ✓ {chart.description}          ({chart.section})

  ── Optional Charts ───────────────────────────────────────
  [1] Debt Structure Bar Chart    (Transaction Summary)
  [2] Cash Flow Trend             (Financial Analysis)
  [3] Cap Rate Comparison         (Collateral Analysis)
  [4] Risk Factor Donut           (Risk Assessment)
  [5] Amortization Schedule       (Financial Analysis)

  Select optional charts (comma-separated, or Enter to skip): _    [<] Back
```

For non-credit-memo document types, show only the optional charts menu (no
must-have section). The chart list is derived from `catalog_entry.available_charts`
in the doc-type catalog.

Store as `selected_charts`: list of chart IDs. For credit memos, always include
the 3 must-have charts plus any user-selected optional charts.

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

  Instructions: _                                    [<] Back
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

- **Unchanged:** Verify the cached files are valid: check that `loan_data_path`
  and `loan_data_brief_path` from the cached manifest (a) exist on disk, (b) are
  non-empty (file size > 0), and (c) parse as valid YAML mappings (not null, not a
  list root). If any check fails, treat as cache miss. If files exist, prompt: `"Loan folder analysis found in cache
  (analyzed {date_analyzed}). Reuse? [Y/n]: "`. If Y: `skip_phase_2 = true`, load paths.
- **Changed:** Display: `"Loan folder has changed since last analysis. Re-running Phase 2."`. Set `skip_phase_2 = false`.
- **Not found:** `skip_phase_2 = false`.

**Config override:** If `.acos/loan-doc-generator/config.yaml` has `cache.enable_phase2_cache: false`,
skip the cache check entirely and set `skip_phase_2 = false`.

### Step 0.7b: Output Destination

**Quick mode / Batch mode:** Set `output_destination = null`. Skip the prompt.

```
Step 8 of 8: Output destination  (optional — press Enter for default)

  Where should the final documents be saved?

  Default: .acos/loan-doc-generator/sessions/{session_id}/output/

  Custom path: _                                     [<] Back
```

If the user enters a custom path, validate it exists (or can be created). Store as
`output_destination`. If Enter with no input, set `output_destination = null` (use default).

### Step 0.8: Confirmation & Bootstrap

Generate `session_id`: `YYYYMMDD-HHMMSS`.

Display confirmation:

**Single document mode (quick/detailed):**

```
╔══════════════════════════════════════════════════════════════╗
║ Ready to Generate                                           ║
╠══════════════════════════════════════════════════════════════╣
║  [1] Mode          : {interview_mode}                       ║
║  [2] Category      : {category_name}                        ║
║  [3] Document      : {document_title}                       ║
║  [4] Design Source : {label or path}                        ║
║  [5] Loan Folder   : {loan_folder_path}                     ║
{if detailed:}
║  [6] Figures Mode  : {figures_mode}                          ║
║  [7] Target Pages  : {target_pages or "no limit"}           ║
║  [8] Images        : {len(images) or "none"}                ║
║  [9] Charts        : {chart_count or "auto"}                ║
║ [10] Instructions  : {truncated or "none"}                  ║
║ [11] Output To     : {output_destination or "session default"} ║
{end if}
{if quick:}
║  [6] Output To     : {output_destination or "session default"} ║
{end if}
║      Output Format : {if catalog_entry.output_format == 'pptx': "PPTX" else: "PDF + DOCX"} ║
║      Session ID    : {session_id}                           ║
╚══════════════════════════════════════════════════════════════╝

  Phases to run:
    {✓ skipped / ☐ pending} Phase 1: Design Extraction
    {✓ skipped / ☐ pending} Phase 2: Loan Folder Analysis
    ☐ Phase 3: Document Design
    ☐ Phase 4: Validation + Wigum Loop

  [Y] Proceed   [<] Back   [1-{N}] Edit specific step
```

If the user enters a number (e.g., `3`), jump directly to that step's prompt
with the current value shown. After the user updates (or keeps) the value,
return to this confirmation screen with the updated summary. Apply state
invalidation rules from the Back-Navigation Rules section (e.g., changing
document type clears design source).


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

1b. Bootstrap recommendation matrix config if not present:
   Copy `templates/recommendation-matrix.yaml` → `.acos/loan-doc-generator/recommendation-matrix.yaml`

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
   catalog_entry: {}                 # FULL catalog entry from doc-type-catalog.yaml
                                     # Embedded here so phase agents read ~1KB from manifest
                                     # instead of parsing the full 107KB catalog file.
                                     # Contains: default_sections, benchmark_dimensions,
                                     # structural_benchmark_items, designer_tone_directive,
                                     # critical_figures, default_page_range, etc.
   phase_1_track_b_only: false       # true when catalog inference already extracted design patterns;
                                     # Phase 1 should skip Track A (Steps 1.2-1.5) and only run Track B
   design_source: "library|new"
   design_label: ""
   design_patterns_path: ""
   benchmark_criteria_path: ""
   template_pptx_path: ""           # PPTX only: path to extracted template.pptx
   design_spec_path: ""             # PPTX only: path to extracted design-spec.yaml
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
   output_destination: null          # null = session default, or user-specified path
   selected_charts: "auto"          # "auto" for credit memos, or list of chart IDs
   verification_table_path: ""      # populated after Phase 2 Step 2.5b
   skip_phase_1: false
   skip_phase_2: false
   status: "in-progress"
   current_phase: 1
   current_iteration: 0
   checkpoint:                      # populated after each phase completes
     last_successful_phase: null
     completed_phases: []
     phase_outputs: {}
     timestamp: null
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
   output_destination: null
   verification_table_path: ""
   status: "in-progress"
   current_phase: 1
   checkpoint:
     last_successful_phase: null
     completed_phases: []
     phase_outputs: {}
     timestamp: null
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
       selected_charts: "auto"
       skip_phase_1: false
       current_iteration: 0
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
       └── batch-report.md           ← combined provenance + results (PDFs in batch-N/output/)
   ```

---

## Phase Dispatch

After Phase 0 completes, dispatch to phase orchestrator agents.
The `manifest_path` is `.acos/loan-doc-generator/sessions/{session_id}/session-manifest.yaml`.

### Session Checkpointing

After each phase completes successfully, update the session manifest with a checkpoint:

```yaml
# Added after each phase completes:
checkpoint:
  last_successful_phase: 2       # 0, 1, 2, or 34
  completed_phases: [0, 1, 2]
  phase_outputs:
    phase_1:
      design_patterns_path: "..."
      benchmark_criteria_path: "..."
    phase_2:
      loan_data_path: "..."
      loan_data_brief_path: "..."
  timestamp: "YYYY-MM-DD HH:MM:SS"
```

This enables resume from any checkpoint if the session is interrupted.

### Resume Mode

If `$ARGUMENTS` contains `resume` or `resume {session_id}`:

1. If no session_id given, list all sessions with status `"in-progress"`:
   ```
   Incomplete sessions:
     SESSION ID          DOCUMENT                    LAST PHASE   STATUS
     20260316-143022     Internal Credit Memo        Phase 2      in-progress
     20260315-091500     Term Sheet (batch 3)        Phase 1      in-progress

   Resume which session? [session_id]:
   ```

2. Read the session manifest and checkpoint
3. Before skipping any phase, verify that all phase output files referenced in
   `checkpoint.phase_outputs` (a) exist on disk, (b) are non-empty (size > 0), and
   (c) parse as valid YAML mappings (not null, not a list root). For YAML files
   (design-patterns.yaml, benchmark-criteria.yaml, loan-data.yaml), verify the
   file contains at least one expected top-level key (e.g., `canonical_sections`
   for design patterns, `criteria` for benchmarks). If any check fails, downgrade
   `last_successful_phase` to the phase before the missing/corrupt output and report:
   `"Phase {N} outputs invalid or missing — will re-run from Phase {N}."`
4. Report: `"Resuming session {session_id} from Phase {N+1}"`
5. Skip to the appropriate dispatch step below based on `last_successful_phase`

### Single Document Dispatch (quick/detailed)

#### Dispatch Phase 1 (if needed)

If `skip_phase_1 = false`:

```
Task(loan-doc-phase1)
  - prompt: |
      Session manifest: {manifest_path}
      Execute Phase 1: Design Extraction.
      phase_instructions_path: .claude/skills/acos-loan-doc-generator-with-visual-verification/phases/
      Read phase1-extract.md from that directory.
```

Wait for completion. **Checkpoint: update manifest with Phase 1 outputs.**
Report Phase 1 results to user.

If `skip_phase_1 = true`:
Report: `"Phase 1 skipped — using cached design from library: {design_label}"`

#### Dispatch Phase 2 (if needed)

If `skip_phase_2 = false`:

```
Task(loan-doc-phase2)
  - prompt: |
      Session manifest: {manifest_path}
      Execute Phase 2: Loan Folder Analysis.
      phase_instructions_path: .claude/skills/acos-loan-doc-generator-with-visual-verification/phases/
      Read phase2-analyze.md from that directory.
```

Wait for completion. **Checkpoint: update manifest with Phase 2 outputs.**
Report Phase 2 results to user.

If `skip_phase_2 = true`:
Report: `"Phase 2 skipped — using cached loan analysis from {date_analyzed}"`

**When Phase 2 is cached**: The verification table may not exist for this session.
Re-run ONLY Step 2.5b (verification table generation) using the cached loan-data.yaml:

```
Task(loan-doc-phase2)
  - prompt: |
      Session manifest: {manifest_path}
      CACHE HIT MODE: Phase 2 data is already at {loan_data_path}.
      Run ONLY Step 2.5b from phase2-analyze.md — generate the verification table.
      Do NOT re-analyze the loan folder.
```

Wait for completion. Update `verification_table_path` in the manifest.

#### Data Verification Gate (between Phase 2 and Phase 3)

**This gate is MANDATORY. Do NOT skip it.**

After Phase 2 completes (or cache is loaded), read the verification table at
`verification_table_path` from the session manifest. Display it to the user:

```
╔══════════════════════════════════════════════════════════════════════════╗
║ Data Verification — Review Before Document Generation                    ║
╠══════════════════════════════════════════════════════════════════════════╣

  {total_figures} data points extracted  │  {cross_validated_count} cross-validated
  {single_source_count} single-source    │  {calculated_count} calculated

  ── Key Financial Figures ────────────────────────────────────────────────
  DATA POINT              VALUE              SOURCE              CONFIDENCE
  ─────────────────────── ────────────────── ─────────────────── ──────────
  Loan Amount             $2,100,000         Loan Agreement p2   ✓ 0.95
  Interest Rate           7.25%              Term Sheet p1       ✓ 0.92
  Property Value          $3,200,000         Appraisal p5        ✓ 0.90
  📊 LTV Ratio            65.6%              (calculated)        ✓ 0.90
  ⚠ Maturity Date         2027-03-15         Note p3             ⚠ 0.65

  ── Entities ─────────────────────────────────────────────────────────────
  Borrower                Cook Group LLC     Application p1      ✓ 0.98
  Guarantor               James Cook         Guarantee p1        ✓ 0.95
  Property                123 Main St, SLC   Appraisal p1        ✓ 0.93

  ── Calculated Values ────────────────────────────────────────────────────
  📊 LTV: $2,100,000 / $3,200,000 = 65.6%
     └─ Loan Amount from: Loan Agreement.pdf p2
     └─ Property Value from: Appraisal.pdf p5
  📊 DSCR: $285,000 / $168,000 = 1.70x
     └─ NOI from: Operating Statement.xlsx Sheet1!D15
     └─ Debt Service from: Term Sheet.pdf p2 (calculated from rate + amort)

  Click any source link to verify: file:// paths open the source document.

╚══════════════════════════════════════════════════════════════════════════╝

  [A]  Approve all data — proceed to document generation
  [F]  Flag specific values for correction
  [O]  Override a value manually (becomes ground truth)

Enter selection [A/F/O]:
```

**If [A] Approve:** Proceed to Phase 3+4 dispatch.

**If [F] Flag:** Prompt for which data points to re-examine. Offer to re-run
specific analyzer agents on specific source documents. Update loan-data.yaml
with corrected values. Regenerate verification table and re-display.

**If [O] Override:** Prompt for the data point name and new value.
```
  Data point to override: _
  New value: _
  Reason (optional): _
```
Update loan-data.yaml with the override: set `source: "user_override"`,
`confidence: 1.0`, `authoritative: true`. Also update user-figures.yaml if it
exists (or create it). Regenerate verification table and re-display.

Loop back to the verification display until the user selects [A] Approve.

#### Dispatch Phase 3+4

```
Task(loan-doc-phase34)
  - prompt: |
      Session manifest: {manifest_path}
      Execute Phase 3 (Document Design) + Phase 4 (Validation + Wigum Loop).
      phase_instructions_path: .claude/skills/acos-loan-doc-generator-with-visual-verification/phases/
      Read phase3-design.md and phase4-validate.md from that directory.
      Handle all Wigum loop iterations internally.
```

Wait for completion. **Checkpoint: update manifest with Phase 3+4 outputs.**

#### Human-in-the-Loop Approval Gate

After Phase 3+4 completes (regardless of PASS/FAIL), do NOT finalize immediately.
Present the user with a review gate:

```
╔══════════════════════════════════════════════════════════════╗
║ Document Draft Ready for Review                              ║
╠══════════════════════════════════════════════════════════════╣
║  Validation  : {PASS|FAIL} ({pass_rate}%)                   ║
║  Iterations  : {count}                                       ║
║  PDF Preview : file://{pdf_path}                             ║
║  DOCX Preview: file://{docx_path}                            ║
╚══════════════════════════════════════════════════════════════╝

  Please review the draft. Options:
  [A]  Approve and finalize
  [E]  Edit specific sections (provide instructions)
  [R]  Reject and start over

Enter selection [A/E/R]:
```

**If [A] Approve:** Proceed to the Report step. Copy final outputs to
`output_destination` if set.

**If [E] Edit:** Show the section list from `catalog_entry.default_sections` as a numbered pick-list:
```
  Which section(s) to edit?
  [1] {section_1_name}
  [2] {section_2_name}
  ...
  Enter numbers (comma-separated): _
  Instructions for changes: _
```
Store as iteration feedback and re-dispatch Phase 3+4 for only those sections.
Return to this approval gate after the edit cycle completes.

**If [R] Reject:** Mark session as `"rejected"` in the manifest. Offer to
start a new session with the same configuration.

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
      phase_instructions_path: .claude/skills/acos-loan-doc-generator-with-visual-verification/phases/
      Read phase1-extract.md from that directory.
      Use batch_index {batch_index} to differentiate extraction outputs.
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
      phase_instructions_path: .claude/skills/acos-loan-doc-generator-with-visual-verification/phases/
      Read phase2-analyze.md from that directory.
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
      phase_instructions_path: .claude/skills/acos-loan-doc-generator-with-visual-verification/phases/
      Read phase3-design.md and phase4-validate.md from that directory.
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
**Checkpoint: update manifest with all batch item statuses and outputs.**

#### Batch Step 4: Partial Retry (if any items failed)

If any `batch_item.status == "failed"`:

```
  {fail_count} of {total} documents failed validation.

  Failed items:
    #{batch_index}  {document_title}   {failure_reason}

  [R]  Retry failed items only
  [P]  Proceed with all (include failed drafts)
  [S]  Skip — proceed to report with mixed results

Enter selection [R/P/S]:
```

**If [R] Retry:** Re-dispatch ONLY the failed batch items through Phase 3+4
using the same shared Phase 2 data. Update `batch_item.status` on completion.
Return to this step if any still fail (max 2 retry cycles).

**If [P] Proceed:** Mark all as `"complete"` (even those with validation failures).

**If [S] Skip:** Proceed to report. Failed items are flagged in the batch report.

#### Batch Human-in-the-Loop Gate

Same as single-document mode — present the batch results for review before
finalizing. User can approve all, edit specific documents, or reject.

### Report Final Results

#### Single Document Report

**Step R.1: Data Provenance Table**

After Phase 3+4 completes (regardless of PASS/FAIL), generate a data provenance table:

1. Read `loan-data.yaml` at `loan_data_path` — each data point has `source_document` and `source_page` fields
2. Read the final PDF (or HTML fallback) to identify which data points were actually used
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
║  PDF Output    : file://{pdf_path}                          ║
║  DOCX Output   : file://{docx_path}                         ║
║  Provenance    : {provenance_table_path}                    ║
║  Validation    : {validation_report_path}                   ║
╚══════════════════════════════════════════════════════════════╝
```

If `output_destination` was specified, also show:
```
║  Copied to     : {output_destination}                       ║
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
║  PDF Output    : file://{pdf_path}                          ║
║  DOCX Output   : file://{docx_path}                         ║
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
2. For each batch item, read its final PDF (or HTML fallback) from `batch-{N}/output/`
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
╔════════════════════════════════════════════════════════════════════════════╗
║ Batch Generation Complete — {pass_count}/{N} passed                       ║
╠════════════════════════════════════════════════════════════════════════════╣
║  #  DOCUMENT                  RESULT  ITER  RATE   PDF             DOCX  ║
║  1  Credit Memo — Internal    PASS    2     95%    file://...pdf   ...docx║
║  2  Credit Memo — External    PASS    1     100%   file://...pdf   ...docx║
║  3  Deal Document             FAIL    5/5   72%    file://...pdf   ...docx║
╠════════════════════════════════════════════════════════════════════════════╣
║  Shared loan analysis   : {loan_data_path}                                ║
║  Combined provenance    : {batch_report_path}                             ║
║  Session workspace      : {session_path}                                  ║
╚════════════════════════════════════════════════════════════════════════════╝
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
  DOCUMENT ID                                  LABEL                  ADDED
  credit-underwriting/internal-credit-memo     Okoa PE Style          2026-03-15
  credit-underwriting/term-sheet               Okoa PE Style          2026-03-15
  closing-admin/settlement-statement           Okoa PE Style          2026-03-15

Cached Phase 2 Analyses:
  FINGERPRINT         LOAN FOLDER                        ANALYZED        FILES EXIST
  sha256-abc123...    /path/to/loan-folder/              2026-03-01      Yes

Active Sessions:
  SESSION ID          DOCUMENT                           PHASE  ITER  STATUS
  20260309-143022     Bridge Loan Agreement              3      1     in-progress
```

---

## Data Flow Reference

**Single document mode:**
```
Phase 0 (this context) ──→ session-manifest.yaml ──→ all phases read this

Phase 1 Agent ─┬─ design-patterns.yaml (per-sample, not merged) ──→ Phase 3 + 4
               └─ benchmark-criteria.yaml + DESIGN rules ──→ Phase 4

Phase 2 Agent ─┬─ xlsx-extract.py (pre-process .xlsx) ──→ structured YAML
               ├─ loan-data.yaml (with cross-validation) ──→ Phase 3 + 4
               ├─ loan-data-brief.yaml ──→ Phase 3 + 4
               └─ verification-table.yaml ──→ Phase 0 (user approval gate)

  ── DATA VERIFICATION GATE (mandatory) ──
  Phase 0 displays verification table → user approves / flags / overrides

Phase 3+4 Agent ─┬─ document-draft.html ──→ Puppeteer ──→ PDF
                  ├─ html-to-docx.py ──→ DOCX
                  ├─ generate-chart.py ──→ SVG charts (embedded in HTML)
                  ├─ validators (structural + design + quality + global + charts)
                  └─ VISUAL-QA GATE (3 gates, per Wigum iteration):
                     • Gate 1 — validate-pptx.py (data/font/color/anchor)
                     • Gate 2 — check-pptx-layout.py / check-pdf-layout.py (layout)
                     • Gate 3 — render-doc-audit.py ──→ PNG @150 DPI (≤2000px)
                                ──→ agent Reads each screenshot ──→ visual verdict
                                ──→ visual-audit/iteration-{N}/
                     ──→ Wigum loop ──→ output/ (PDF + DOCX only)

  ── HUMAN-IN-THE-LOOP GATE ──
  Phase 0 displays draft for review → user approves / edits / rejects

Phase 0 (post) ─── loan-data.yaml ──→ provenance-table.md (cross-ref with PDF)

Design Library ──→ Phase 0 (skip Phase 1 if cached)
Phase 2 Cache  ──→ Phase 0 (skip Phase 2 if unchanged)
Checkpoints    ──→ Phase 0 resume (skip to last successful phase)
```

**Batch mode:**
```
Phase 0 ──→ session-manifest.yaml (with batch_items array)
         │
         ├─→ Phase 1 Agent [doc-1] ─┬─ design-patterns.yaml ──→ batch-1/
         ├─→ Phase 1 Agent [doc-2] ─┤  (parallel, per-sample, not merged)
         │   ...                    └─ benchmark-criteria.yaml
         │
         ├─→ Phase 2 Agent (shared) ─┬─ xlsx pre-processing
         │                           ├─ loan-data.yaml ──→ all batch items
         │                           ├─ loan-data-brief.yaml
         │                           └─ verification-table.yaml ──→ user gate
         │
         ├─→ DATA VERIFICATION GATE (shared, one approval for all items)
         │
         ├─→ Phase 3+4 Agent [doc-1] ──→ batch-1/output/ (PDF+DOCX) ─┐
         ├─→ Phase 3+4 Agent [doc-2] ──→ batch-2/output/ (PDF+DOCX) ─┤ parallel
         ├─→ Phase 3+4 Agent [doc-3] ──→ batch-3/output/ (PDF+DOCX) ─┘
         │
         ├─→ BATCH PARTIAL RETRY (if any failed) ──→ re-dispatch failed only
         │
         ├─→ HUMAN-IN-THE-LOOP GATE (review all before finalizing)
         │
         └─→ Phase 0 (post) ──→ batch-report.md (combined provenance)
```

---

## File Layout

```
.claude/skills/acos-loan-doc-generator-with-visual-verification/
├── SKILL.md                         ← This file (thin router)
├── phases/
│   ├── phase1-extract.md            ← Phase 1 orchestrator instructions
│   ├── phase2-analyze.md            ← Phase 2 orchestrator instructions
│   ├── phase3-design.md             ← Phase 3 orchestrator instructions
│   └── phase4-validate.md           ← Phase 4 orchestrator instructions (visual-QA gate)
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

.claude/scripts/
├── xlsx-extract.py                  ← XLSX cell-level extraction (openpyxl)
├── generate-chart.py                ← SVG chart generation (bar, gauge, waterfall, donut, matrix)
├── html-to-docx.py                  ← Styled DOCX conversion (pandoc + python-docx)
├── html-to-pdf.js                   ← PDF conversion via Puppeteer
├── render-doc-audit.py              ← Render document to PNG screenshots at 150 DPI (visual QA)
├── check-pptx-layout.py             ← Fast coordinate-level PPTX layout check
├── check-pdf-layout.py              ← Fast text-position PDF layout check
└── validate-pptx.py                 ← PPTX data/font/color/anchor validation

.acos/loan-doc-generator/
├── config.yaml                      ← Runtime configuration
├── design-library/
│   ├── index.yaml                   ← Master design index (one entry per sample)
│   ├── STYLE-GUIDE.yaml             ← Okoa-specific style guide
│   ├── STYLE-GUIDE-RESEARCH.yaml    ← Research-backed design quality rules (30 rules)
│   └── {design_id}/                 ← Per-design extraction outputs
├── research/
│   └── pe-lending-ratios-research.yaml  ← PE ratios, scoring matrix, chart specs
├── cache/                           ← Phase 2 cache by loan folder fingerprint
└── sessions/{session_id}/           ← Per-session workspace
```

---

*ACOS Loan Document Generator — Quick/Detailed/Batch interview modes, DOCX+PDF dual
output (no other formats), CSS pagination, page count control, image support, data
provenance, delegated phase orchestration with design library, Phase 2 caching,
XLSX cell-level extraction, parallel batch generation, section-scoped validation,
benchmark-driven Wigum loop, session checkpointing with resume, batch partial retry,
human-in-the-loop approval gate, post-generation editing, and configurable output
destination.*
