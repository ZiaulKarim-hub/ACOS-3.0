---
name: acos-dataroom
description: |
  Outbound diligence data room preparation for OKOA Capital. Transforms a messy
  single-loan folder into an investor-ready data room through an AI-assisted,
  human-reviewed pipeline. Five deal types: loan_sale, loan_participation,
  property_sale, foreclosure_auction, lender_package. Mandatory OCR+vision on
  image-only PDFs. Adaptive checklist (skill-internal base + per-deal tailoring).
  Evidence-bundle-backed no-hallucination guarantee. Two human pause gates
  (deal-type confirmation, Excel guide review). Defaults to no-upload,
  no-rename, no-share.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "<subcommand> [flags] — subcommands: create-guide | validate-guide | create-room"
---

# ACOS Data Room

## Overview

OKOA's existing DD checklists are *origination-side* (inbound — what OKOA
collects when underwriting). This skill is **outbound** — what OKOA must
produce when selling, participating-out, foreclosing, or pitching an existing
position. Different orientation, different artifacts.

The skill operates in three callable subcommands and an 11-phase internal
pipeline:

| Subcommand | Phases | Output |
|---|---|---|
| `create-guide` | 1–9 | `<name>_Internal_Working_<date>.xlsx` (4-worksheet boss-review workbook) + `<name>_QA_Report_<date>.md` (standalone diagnostic) |
| `validate-guide` | 10 | Validation report + diff log |
| `create-room` | 11 | Final renamed/organized data room folder + `<name>_Index_<date>.xlsx` (sanitized 2-worksheet buyer-facing index) |

Two human pause gates: **deal-type confirmation** (Phase 1) and **Excel guide
review** (after Phase 9). No proceeding without explicit confirmation.

**Two distinct workbooks, by design.** The internal workbook is the boss's
working tool — full reasoning, confidence scores, exclusions, missing-document
recommendations. The buyer-facing workbook is a stripped-down 5-column index
generated only after the boss finalizes the internal one. The buyer never
sees reasoning, confidence, exclusions, or QA findings — by construction,
because the buyer workbook is derived from the boss-finalized "Files
Included" worksheet, which contains nothing internal-only.

## Skill Contract — Non-Negotiables

1. **Never modify, move, delete, rename, or share source files.** Copies only.
2. **Never auto-upload anywhere.** v1 writes to local paths (Dropbox folders are local for our purposes).
3. **Never auto-redact.** Flag for redaction; require user-provided redacted file or explicit override.
4. **Human decision is final.** Diff logging is audit-only — never blocks a human override.
5. **Every claim must be traceable** to source file, page, extraction method, and evidence-bundle snippet.
6. **Vision is mandatory** for image-only PDFs and low-OCR-confidence pages.
7. **Pause gates are real.** Deal-type confirmation and guide review both require explicit confirmation.
8. **Defaults to no-upload, no-rename, no-share.** Destructive or external actions require explicit `--confirmed true`.

## Architecture (Progressive Disclosure)

This SKILL.md is the orchestrator. Detailed logic lives in `references/`:

- **Deal types** → `references/deal_types.md`
- **Per-deal-type base checklists** → `references/checklist_<type>.md` (5 files)
- **Per-deal-type taxonomies** (folder structure of the data room) → `references/taxonomy_<type>.md` (5 files)
- **Excel workbook schema** → `references/excel_schema.md`
- **Evidence bundle format & no-hallucination rules** → `references/evidence_bundle_spec.md`
- **Extraction recipes per file type** → `references/extraction_recipes.md`
- **Vision fallback triggers and prompts** → `references/vision_fallback.md`
- **Vision bridge request/response contract** → `references/vision_bridge_contract.md`
- **Risk dashboards (per deal type)** → `references/risk_dashboards.md`
- **The 7 QA passes + adversarial pass** → `references/qa_checklists.md`
- **Naming convention + collision handling** → `references/naming_convention.md`
- **Local + Dropbox-as-synced-folder platform notes** → `references/platform_local_dropbox.md`

Load only what's relevant to the current phase. Do not pre-load all 5 checklists
when only one deal type is in play.

## Subcommand: `create-guide`

```
acos-dataroom create-guide \
  --source "/path/to/loan/folder" \
  --objective "Prepare data room for loan sale" \
  [--deal-type <enum>] \
  [--output "/path/to/output"] \
  [--data-room-name "AscentParkCity_LoanSale"] \
  [--buyer-stage NDA_signed]
```

Required: `--source`, `--objective`. All others optional.

### Phase 1 — Intake & Deal Type Confirmation

1. Validate `--source` exists and is readable.
2. Generate run ID: `run_YYYYMMDD_HHMMSS_<short_hash_of_source_path>`.
3. Create working directory: `<source>/_acos_dataroom_output/<run_id>/`.
4. Initialize `processing_manifest.json` with timestamp, source path, objective, run_id, optional flags.
5. **Deal type:**
   - If user provided `--deal-type`, validate against enum; confirm with user; proceed.
   - If not, run `scripts/scan_folder.py --shallow` to inventory filenames + folder shape, plus extract first page from up to 5 likely-key files (anything matching `*term*sheet*`, `*purchase*agreement*`, `*notice*sale*`, `*loan*agreement*`, `*offering*memo*`).
   - Read `references/deal_types.md` and propose the most likely deal type from the enum, with a confidence score and the signal that drove the inference.
   - **Pause gate #1:** Print the proposal and ask the user to confirm or override. Do NOT proceed to Phase 2 until the user confirms.
6. Record confirmed deal type into `processing_manifest.json`.

### Phase 2 — Checklist Load

1. Load `references/checklist_<deal_type>.md` (skill-internal base — authoritative for this skill).
2. Load `/Users/zee/okoa-labs/okoa_ops/.claude/data/dd-checklist-template.md` if present (category vocabulary supplement only — used to harmonize classification labels with OKOA terminology, NOT as a checklist).
3. If the master reference is missing, fall back to `/Users/zee/okoa-labs/okoa_ops` directory search; if still missing, log a warning and proceed without vocabulary harmonization. The skill-internal base checklist is sufficient on its own.
4. Load `references/taxonomy_<deal_type>.md` for the data room folder structure.

### Phase 3 — File Inventory

Delegate to `scripts/scan_folder.py`:

- Recursive walk; capture name, ext, size, modified date, source path, relative path, parent folder.
- Compute SHA-256 hash of every file → deterministic file_id (e.g., `f_<first_12_hex>`).
- Detect duplicates (same hash), inaccessible files, encrypted/password-protected files, zero-byte files, unsupported formats.
- Apply `system_files_excluded` from config (always exclude — never appear as real files).
- Apply user-supplied `--excluded-folders` if any.
- Apply `default_excluded_extensions` (eml, msg, mbox, zip, etc. — out of scope for v1; flag, don't process).
- Output: `intermediate/file_manifest.json` and `intermediate/file_manifest.csv`.

### Phase 4 — Extraction (with Mandatory Vision Fallback via Bridge)

Delegate per-file to `scripts/extract_text.py` and `scripts/ocr_and_vision.py`.
Read `references/extraction_recipes.md` for per-extension logic,
`references/vision_fallback.md` for vision triggers, and
`references/vision_bridge_contract.md` for the bridge request/response
schemas.

Key invariants:

- **PDFs:** native text → if a page yields < threshold characters relative to rendered area, OR OCR confidence < 0.70, OR no extractable text at all → render that page to PNG and request vision analysis. Both OCR text and vision description go in the evidence bundle, labeled by source method.
- **Images:** OCR + vision *always* (vision describes document type, visible text, signatures/seals, dates, parties).
- **Word/Excel/PowerPoint:** native extraction; embedded images in PowerPoint go through vision.
- **Text/Markdown/RTF:** direct read.
- **Out of scope (v1):** emails (eml/msg/mbox), zip archives. Flag in manifest, do not extract.

All extracted content lives in `<run_dir>/extraction/<file_id>/`. Never copied
to the final data room.

**Vision dispatch (v1.1.0+):** vision calls go through a bridge directory,
NOT a direct Anthropic SDK call. `ocr_and_vision.py` writes a request
manifest + rendered PNG to `<run_dir>/intermediate/vision_bridge/requests/`
and marks the page `vision_supplement.status = "pending"`. The orchestrating
Claude Code session reads pending requests, spawns a vision-capable `Task()`
sub-agent for each (inheriting the user's Max subscription — no
`ANTHROPIC_API_KEY` required), and writes structured JSON responses to
`vision_bridge/responses/`. A subsequent `ocr_and_vision.py --rehydrate`
call merges the responses back into each `extraction.json`. See
`references/vision_bridge_contract.md` for the full schema and orchestrator
fulfillment recipe.

### Phase 5 — Classification & Summarization

For each file, produce a structured record:

- `category` and `subcategory` (per deal-type taxonomy)
- `brief_summary` (1–3 sentences)
- `detailed_summary` (1 paragraph where appropriate)
- `key_entities`, `key_dates`, `monetary_amounts`, `document_status`, `document_date`
- Confidence scores: `classification_confidence`, `extraction_confidence`, `ocr_confidence`, `summary_confidence` (all 0.0–1.0)
- `sensitivity_level` (low/medium/high/critical), `redaction_recommended` (bool)
- `external_room_recommendation` from the include status enum:
  - `include`
  - `include_after_redaction`
  - `internal_only_pii`
  - `internal_only_privileged`
  - `internal_only_strategic`
  - `superseded`
  - `absent`
  - `review`

**Privileged content gets paranoid handling.** Anything with "Privileged &
Confidential" headers, attorney-client communications, internal legal memos,
litigation strategy, or work-product markings defaults to
`internal_only_privileged` regardless of category, with a critical-severity
flag.

**Strategic exclusion is judgment, not pattern matching.** The skill never
auto-assigns `internal_only_strategic`. It surfaces candidates ("this internal
valuation memo shows a number below asking price; consider whether to include")
in the Excel `Internal_Only` tab with reasoning, but the boss decides.

### Phase 6 — Evidence Bundle Generation

For every file, write `<run_dir>/evidence/<file_id>.json` containing:

- Source path, hash, all extraction methods used (`["native_pdf", "ocr_page_3", "vision_page_3"]`)
- Raw extracted text with page anchors
- OCR confidence per page; vision analysis output if used
- Classification reasoning, including alternatives considered and why rejected
- Summary reasoning with **direct source-text snippets backing every claim**

**Snippet authoring rule (for the classification agent):**

When backing a factual claim, **prefer verbatim source snippets**. The claim
text itself may paraphrase, but the `snippet.text` field must be the
as-extracted source text. **Never reformat numbers** in the snippet
(`11500000` stays `11500000`; the claim can read "$11,500,000" but the
snippet must not). **Never expand abbreviations** in the snippet (`Orig Fee`
stays `Orig Fee`). This keeps the audit trail at maximum confidence
(verbatim layer, 1.00) and avoids spurious mismatches in verification.

**No-hallucination rule, enforced:**

`scripts/verify_no_hallucination.py` validates every claim using **layered
matching** — verbatim → whitespace-normalized → format-normalized →
paraphrase-likely (with token overlap and number-presence checks).

Critical detail: **a claim citing a number not present in the source is
flagged as a hallucination at confidence 0.00, regardless of other token
matches.** Numbers must match precisely — case numbers, dollar amounts,
dates, account numbers. There is no soft path for invented numerics.

Failed claims either go into `summary.unable_to_verify[]` (with the failure
layer + missing tokens or numbers) or are removed from the summary before
finalization. The corresponding workbook cell reads `"Unable to verify —
see evidence bundle"` if a claim could not be backed.

A full per-claim audit is written to
`<run_dir>/intermediate/hallucination_check.json` for diagnostic review.

See `references/evidence_bundle_spec.md` for the full schema and the layered
matching specification. The verifier should be invoked with
`--update-qa-report` so QA Pass #3 reflects real-run numbers.

### Phase 7a — Tailored Diligence Scope

This is the **adaptive checklist** layer.

1. Load `references/checklist_<deal_type>.md`.
2. Read deal objective and the classified extraction set.
3. Produce `intermediate/tailored_scope.json`:

For each base item:
- `add` — triggered into scope by deal-specific evidence (e.g., property has shared-well documents → add "shared well agreement"; deal involves EB-5 capital → add "EB-5 source-of-funds documentation"). Reasoning required.
- `mark_not_applicable` — base item that doesn't apply (e.g., "tenant estoppels" for vacant property). Reasoning required.
- `leave_in_scope` — default; no reasoning needed.

Every modification is logged. The boss reviews these in the
`Tailored_Diligence_Scope` Excel tab.

### Phase 7b — Three-State Item Status

For each tailored-scope item:

- `present` — document found in source folder, recommended for inclusion in data room.
- `present_but_excluded` — document found but recommended to withhold. Surfaces in `Internal_Only` tab. **The skill never auto-assigns `internal_only_strategic`** — only `pii`, `privileged`, `superseded`, and `internal_only_by_default`.
- `absent` — document not found in source folder; flagged as a gap with severity (low/medium/high/critical).

### Phase 7c — Risk Dashboard + Data Tape Check

Read `references/risk_dashboards.md` for deal-type-specific risk dimensions.
Each row in the dashboard ties back to one or more file_ids and a severity.

**Data tape check:** search for a loan/servicing tape (column-headers like
`UPB`, `interest_rate`, `next_payment_due`, `servicing_history`). If absent,
high-severity gap.

### Phase 8 — QA Passes

Read `references/qa_checklists.md`. Run all 7 + adversarial pass:

1. Completeness — every source file appears in the guide.
2. Classification — re-check assignments; flag ambiguous (where second-best > 0.75 of best).
3. Summary — verify each claim against evidence bundle snippets (catches hallucinations).
4. OCR/Vision — confirm low-confidence pages got vision treatment.
5. Sensitivity — re-scan for PII, wire instructions, privileged content.
6. Diligence — checklist coverage vs. tailored scope.
7. Excel — workbook structure, formulas, dropdowns, hyperlinks.

**Adversarial pass:** for each high-confidence classification (>= 0.90), the
skill prompts itself with "what's the strongest case this is wrong?" Catches
confident-but-wrong errors.

### Phase 9 — Internal Workbook + QA Report

Two artifacts in this phase:

**Artifact 1 — Internal Working Workbook**

Delegate to `scripts/build_excel_guide.py`. Read `references/excel_schema.md`
for full column lists.

Filename: `<DataRoomName>_Internal_Working_<YYYY-MM-DD>.xlsx`

**4 worksheets:**

1. **Cover** — narrative landing page. Title, run information (date / run id /
   source / deal type / objective), Cover Information block (counts), and a
   detailed "How to Navigate This Data Room" section that includes a
   **per-primary-folder summary list** for every primary folder actually used
   in Worksheet 2. Each entry: humanized folder name + one-sentence
   description of what's in that folder for this deal type. Cover does NOT
   contain Key Risks (those live on Worksheet 4) and does NOT contain an AI
   Confidence Summary (that lives only in the standalone QA markdown).
2. **Files Included** — 9 columns: 3 folder hierarchy columns + Original
   Filename + Proposed Renamed Filename + Brief Description + Why Included +
   Confidence-Reasoning + Confidence-Overall-Row. Sorted by primary subfolder
   then sub-folder. Traffic-light fill on the overall-confidence column.
3. **Files Excluded** — 8 columns: 3 folder columns (where it would have
   gone) + Original + Renamed + Reason for Exclusion + 2 confidence columns.
   Absorbs the sensitivity log — every sensitivity-driven exclusion appears
   here with reasoning.
4. **Risks & Missing Documents** — combined worksheet. **Top section: Key
   Risks** — 5 columns (Severity / Risk Category / Risk Description / Evidence
   Summary / Recommended Action), sorted by severity, with severity fill
   colors. **Bottom section: Missing or Recommended Documents** — 8 columns,
   primary/sub folder names looked up from `taxonomy_<deal_type>.md` so cells
   contain real folder names rather than just numbers.

**Visual grouping (applies to data worksheets 2, 3, and the lower section of 4):**

- Primary subfolder and sub-folder values appear only on the *first row* of
  each group; subsequent rows leave those cells blank.
- Detail rows are assigned Excel `outline_level = 1` so a +/− gutter button
  collapses each primary subfolder to a single visible header row.
- The Sub-sub-folder column is **dynamically hidden** if no row populates it.
- See `references/excel_schema.md` ("Visual-Grouping Pattern") for the full
  spec.

No dropdowns, no formulas, no hyperlinks to evidence bundles. The workbook
is a **visual representation of the data room** with the AI's reasoning and
confidence attached. Evidence bundles live as separate JSON in the run
directory — referenced by the standalone QA report, not by the workbook.

**Artifact 2 — Standalone QA Report (Markdown)**

Delegate to `scripts/build_qa_report.py`.

Filename: `<DataRoomName>_QA_Report_<YYYY-MM-DD>.md`

Plain markdown file. Same directory as the internal workbook. Sections:
header / metadata, executive summary, pass-by-pass findings (8 sections),
no-hallucination check, rows flagged for attention, methodology notes,
footer. **Internal use only — never shared with counterparties.**

**Pause gate #2:** After writing both artifacts, print:

> "The internal working workbook is at <path-to-xlsx>. The standalone QA
> report is at <path-to-md>. Please review the workbook and edit any rows
> where you disagree with the skill's recommendation. Read the QA report for
> diagnostics on which rows need extra attention. When done, run
> `acos-dataroom create-room --guide <path-to-xlsx> --confirmed true`. I will
> not upload, move, rename, or copy any file until you confirm."

Stop. Do not proceed to `create-room` until user explicitly invokes it.

## Subcommand: `validate-guide` (Phase 10)

```
acos-dataroom validate-guide --guide "/path/to/edited.xlsx"
```

Delegate to `scripts/validate_guide.py`:

1. Read edited guide.
2. Validate required columns and structure (no required columns deleted, dropdowns intact, row count matches manifest within tolerance).
3. **Diff against original guide** — log every changed Include/Sensitivity/Decision cell to the `Change_Log` tab. The diff is audit-only; the human decision is final, even when it overrides a flag.
4. Confirm only rows marked `include` or `include_after_redaction` will be processed.
5. Stop with a clear error if the edited guide references missing source files.
6. Print summary: "Validated. N files marked include, M marked include_after_redaction, K marked internal_only_*, etc."

## Subcommand: `create-room` (Phase 11)

```
acos-dataroom create-room \
  --guide "/path/to/edited.xlsx" \
  --target "/Users/zee/Dropbox/DataRooms/AscentParkCity" \
  --confirmed true
```

`--confirmed true` is mandatory. Without it, the script prints a confirmation
checklist and exits.

Phase 11 produces two outputs: the physical data room folder and the
buyer-facing index workbook.

**Step 11a — Physical data room.** Delegate to `scripts/create_dataroom.py`:

1. Re-validate the guide (re-runs `validate_guide`).
2. Create folder hierarchy at `--target` per `references/taxonomy_<deal_type>.md`.
3. Copy files from source to target (never move, never modify originals).
4. Rename copies per `references/naming_convention.md`:
   `[Cat#].[Sub#]_[DocType]_[Borrower|Property]_[Date]_[Status].[ext]`
5. Handle filename collisions by appending `_v2`, `_v3`.
6. For rows in the "Files Included" worksheet that the boss has marked for
   redaction: require a redacted file path or explicit per-file
   `--allow-unredacted-override <file_id>` argument. **Never auto-redact.**
7. Generate `creation_log.csv` and a permissions checklist (`PERMISSIONS_CHECKLIST.md`).

**Step 11b — Buyer-facing index workbook.** Delegate to
`scripts/build_buyer_index.py`:

1. Read the boss-finalized internal workbook's `Files Included` worksheet.
2. Produce `<DataRoomName>_Index_<YYYY-MM-DD>.xlsx` in the target folder.
   2 worksheets:
   - **Cover** — sanitized: deal info, dataroom guide, counterparty notes. No risks, no QA, no exclusions.
   - **Data Room Index** — 5 columns: 3 folder hierarchy + File (renamed only, no original name) + Brief Description.
3. By construction, the buyer-facing workbook can never contain
   reasoning, confidence scores, exclusion data, or QA findings — those
   columns simply aren't read from the internal workbook.

## Logging

Verbose logging is **always on** in v1 (config: `verbose_logging: true`). Every
run writes to `<run_dir>/logs/run_log.txt`:

- Every file processed
- Every classification decision with reasoning
- Every QA flag raised
- Every confidence score below `0.85`
- Every checklist modification (add / mark_not_applicable) with reasoning
- Every Internal_Only candidate surfaced with reasoning

Permanent forensic trail. Retained alongside evidence bundles.

## Resumability

Each phase writes `<run_dir>/run_state.json` with last-completed phase and a
checkpoint. A re-run with the same `--source` and the same content (hashes
match) resumes from the last checkpoint instead of restarting.

## What's Out of Scope for v1

- Email files (`.eml`, `.msg`, `.mbox`)
- Zip archives
- Auto-upload to any external system
- Auto-redaction
- Buyer Q&A tracker
- Filename-only mode (text inside files is always read when accessible)
- Separate review-queue handoff to another reviewer

## Glossary

- **Outbound diligence** — documents prepared for an external counterparty (buyer, participant, takeout lender, foreclosure bidder). Inverse of *origination diligence* (what OKOA collects from a borrower).
- **Tailored scope** — the deal-specific checklist after Phase 7a modifications.
- **Pause gate** — a workflow stop where the skill blocks until explicit user input.
- **Evidence bundle** — per-file JSON containing all extraction provenance and snippet-backed reasoning.
- **Vision fallback** — when OCR is insufficient, render to image and use Claude vision for content recovery.

---

*acos-dataroom — outbound diligence, AI-assisted, human-reviewed.*
