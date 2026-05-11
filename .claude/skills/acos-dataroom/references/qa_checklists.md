# QA Checklists — The 7 Passes + Adversarial Pass

All 7 QA passes run in **Phase 8**, before the Excel guide is written. The
adversarial pass runs last. Each pass writes its findings to the `QA_Report`
tab.

A QA pass NEVER blocks the workflow. It produces flags and severity. The boss
decides what to do with flags during the review pause.

---

## Pass #1 — Completeness

**Question:** Does every file in the source manifest appear somewhere in the
output?

Checks:
- For each `file_id` in `intermediate/file_manifest.json`, confirm the file appears either in `Proposed_Data_Room_Index` (extracted), `Source_File_Manifest` with non-extracted status (system_excluded, encrypted, corrupt, zero_byte, unsupported, out_of_scope), or in the Internal_Only tab.
- A file_id missing from all of those is a critical flag.

Severity: critical (any miss).

---

## Pass #2 — Classification

**Question:** Are classifications confident and consistent?

Checks:
- Flag any `classification_confidence < 0.70` (review_required).
- Flag any case where the second-best alternative's confidence is > 0.75 of the chosen — i.e., the model wasn't sure between two categories.
- Flag any cluster of files in the same source folder where classifications diverge significantly more than expected (e.g., one folder named `loan_docs/` containing files classified into 5 different categories).

Severity: medium (low confidence) → high (folder cluster divergence).

---

## Pass #3 — Summary (No-Hallucination)

**Question:** Does every claim in every summary trace back to a snippet in
the evidence bundle?

**Implementation:** `scripts/verify_no_hallucination.py` (run via
`--update-qa-report` so this pass's row in `qa_report.json` reflects real
numbers).

The verifier uses **layered matching** rather than pure substring. Each
claim's snippet (and the claim text itself for paraphrase detection) is
checked against the corresponding file's extraction text:

1. **Verbatim** — `snippet.text` is a verbatim substring of the source. Pass at confidence 1.00.
2. **Whitespace-normalized** — matches after collapsing whitespace. Pass at 0.97.
3. **Format-normalized** — matches after stripping currency symbols, commas, decorative punctuation, casing. Handles `$11,500,000` ↔ `11500000`. Pass at 0.92.
4. **Paraphrase-likely** — ≥80% of *claim* tokens appear in source AND every number in the claim appears in the source. Pass at 0.70–0.90 depending on overlap ratio.
5. **Fail (number_mismatch)** — claim contains a number not present in source. **Strong hallucination signal.** Confidence 0.00.
6. **Fail (low_token_overlap)** — <80% of claim tokens in source. Confidence 0.00.

Failed claims are moved to `summary.unable_to_verify[]` in the evidence
bundle, the per-pass row in `qa_report.json` records the by-layer breakdown,
and a full per-claim audit is written to
`<run_dir>/intermediate/hallucination_check.json`.

**A summary with any number_mismatch failure** triggers `qa_status =
review_required` for that file, regardless of other QA results. Number
mismatches are the strongest hallucination signal and should always be
human-reviewed.

**A summary with > 30% low_token_overlap failures** also flags the file for
re-review — sustained loose paraphrasing means the agent isn't grounding
in the source closely enough.

Severity: critical (any number_mismatch); high (>30% low_token_overlap).

This is the **most important pass.** It enforces the no-hallucination rule.

---

## Pass #4 — OCR / Vision

**Question:** Did low-confidence pages get vision treatment?

Checks:
- For every page where `ocr_confidence < 0.70`, confirm `vision_supplement` exists in the page's extraction record.
- For every image-only PDF (no native text on any page), confirm vision was used on at least one page.
- For every standalone image file, confirm vision was used.

Severity: high (any miss — means a page is invisible to the skill).

---

## Pass #5 — Sensitivity

**Question:** Are PII / wire / privileged content adequately flagged?

Re-scan extracted text for sensitivity patterns:
- SSN: `\b\d{3}-\d{2}-\d{4}\b`
- EIN: `\b\d{2}-\d{7}\b`
- Bank account / routing patterns
- Wire instruction indicators ("wire to", "ABA", "SWIFT", "beneficiary")
- Privileged markings ("Attorney-Client Privileged", "Work Product", "Confidential — Counsel Eyes Only", "Subject to Common Interest Privilege")
- Settlement / litigation strategy keywords
- Compensation / employee data

For each detection, confirm the file's bundle has the corresponding entry in
`sensitivity.reasons` and `sensitivity.redaction_targets`. Missing entries
trigger flags.

Severity: critical (privileged content not flagged) → high (PII not flagged).

---

## Pass #6 — Diligence Coverage

**Question:** Does the tailored scope cover what the deal type requires?

Checks:
- For each base checklist item NOT marked `not_applicable`, confirm `document_status` is set (`present` / `present_but_excluded` / `absent`) — no items left in limbo.
- For each `skill_added` item, confirm `modification_reasoning` is non-empty.
- For each `not_applicable` item, confirm `modification_reasoning` is non-empty.
- For each `absent` item, confirm `severity_if_absent` is set.

Severity: medium (limbo items) → high (skill_added without reasoning).

---

## Pass #7 — Workbook Structure

**Question:** Is the internal workbook structurally sound?

Checks:
- All 4 worksheets present (Cover, Files Included, Files Excluded, Missing or Recommended).
- All required columns per worksheet (per `references/excel_schema.md`).
- Confidence cells use the `0.00` numeric format with traffic-light fill colors applied (green ≥ 0.85, amber ≥ 0.70, red < 0.70).
- Frozen header row + autofilter on every data worksheet.
- Folder-hierarchy sort applied to Files Included, Files Excluded, and Missing or Recommended.
- Risk callout on the Cover worksheet uses severity-keyed fill colors.

Severity: high (any broken structure prevents `validate-guide` from succeeding later).

---

## Adversarial Pass — "What's the Strongest Case This Is Wrong?"

For every classification with `confidence >= 0.90`, the skill prompts itself:

> "I classified `<file_name>` as `<category>/<subcategory>` with confidence
> `<conf>`. Reasoning: `<reasoning>`. Snippets: `<snippets>`. What is the
> strongest case this classification is WRONG? List 1–3 alternative
> classifications and the strongest evidence for each. If any alternative is
> > 0.30 confidence on its own merits, flag this file for re-review."

This catches the **confident-but-wrong** error mode that flat confidence
scoring misses (a model can be confidently wrong because it pattern-matched on
a misleading surface signal).

Outputs go into the file's `qa_flags` array and into the `QA_Report` Excel tab
with a one-line note explaining the strongest counter-case.

Severity: medium (any file where the alternative analysis surfaced a >0.30
counter-case).

---

## QA Report Output — Standalone Markdown File

Each pass contributes one section to the standalone markdown QA report —
**not** to a worksheet tab. The report is at:

`<run_dir>/<DataRoomName>_QA_Report_<YYYY-MM-DD>.md`

Generated by `scripts/build_qa_report.py`. Internal use only — never shared
with counterparties. The report's structure is described in
`references/excel_schema.md` under "Standalone QA Report (Markdown)".

The intermediate `qa_report.json` (used to build both the markdown report and
the AI Confidence Summary line on the workbook Cover) preserves the per-pass
record:

```jsonc
[
  {"qa_pass_id": 1, "pass_name": "Completeness",
   "flagged_count": 0, "total_checked": 47, "flagged_file_ids": "",
   "notes": "All accounted for"},
  {"qa_pass_id": 2, "pass_name": "Classification",
   "flagged_count": 3, "total_checked": 47, "flagged_file_ids": "f_..., f_..., f_...",
   "notes": "Low confidence on 2; folder cluster divergence on 1"},
  {"qa_pass_id": 3, "pass_name": "Summary",
   "flagged_count": 0, "total_checked": 47, "flagged_file_ids": "",
   "notes": "No unverified claims"},
  {"qa_pass_id": 4, "pass_name": "OCR / Vision",
   "flagged_count": 1, "total_checked": 47, "flagged_file_ids": "f_...",
   "notes": "Image-only PDF without vision treatment — re-extract"},
  {"qa_pass_id": 5, "pass_name": "Sensitivity",
   "flagged_count": 2, "total_checked": 47, "flagged_file_ids": "f_..., f_...",
   "notes": "Wire instructions detected; redaction recommended"},
  {"qa_pass_id": 6, "pass_name": "Diligence Coverage",
   "flagged_count": 5, "total_checked": 73, "flagged_file_ids": "",
   "notes": "5 items in limbo"},
  {"qa_pass_id": 7, "pass_name": "Workbook Structure",
   "flagged_count": 0, "total_checked": 0, "flagged_file_ids": "",
   "notes": "OK"},
  {"qa_pass_id": "ADV", "pass_name": "Adversarial",
   "flagged_count": 1, "total_checked": 12, "flagged_file_ids": "f_...",
   "notes": "Strong counter-case for category=loan_documents/note vs. category=loan_documents/loan_agreement"}
]
```
