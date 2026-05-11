# Extraction Recipes — Per File Type

Every file gets a recipe based on its extension. Recipes prescribe: which
library to use, what to extract, when to fall back to OCR, when to fall back
to vision. Native extraction is always tried first; OCR and vision are
fallbacks, not replacements.

The skill writes the **methods used** array into each evidence bundle so the
boss can see exactly how each page's content was recovered.

---

## PDFs (`.pdf`)

1. **Native extraction** with `pdfplumber` (preferred) or `pypdf` (fallback). Capture text per page with character ranges.
2. **Quality check per page:**
   - If extracted character count < 50 AND rendered page area > 1000 × 1000 px → page is image-only.
   - If extracted text exists but contains > 20% gibberish (high ratio of non-alphanumeric chars to alphanumeric) → encoding problem.
3. **OCR fallback** with `pytesseract` on any page failing the quality check. Capture per-page OCR confidence (mean per-word confidence from Tesseract).
4. **Vision fallback** triggers (any of):
   - OCR confidence < `0.70`
   - Native extraction returned zero text
   - Page contains visible signatures/stamps/handwriting (heuristic: detect via image analysis)
   - File has any `vision_required: true` flag set in `references/vision_fallback.md`
5. **Vision call:** render page to PNG at 200 DPI; submit to Claude vision; record description + recovered text + visual elements in evidence bundle.

**Both OCR text and vision description are kept** — they are not redundant. Vision describes structure (signatures, seals, layout); OCR captures plain text.

**Encrypted/password-protected PDFs:** flag in manifest with status `encrypted`. Do not attempt to crack. Surface in `Source_File_Manifest` with note "Password-protected — cannot extract."

---

## Word (`.doc`, `.docx`)

- `.docx`: `python-docx` for native extraction. Capture paragraphs, headings, tables, comments, and tracked changes (where present).
- `.doc` (legacy binary): `antiword` or `textract` if available; otherwise convert via LibreOffice headless mode → `.docx` → `python-docx`.
- **Embedded images in Word docs:** extract via `python-docx` image relationships; submit each through vision if the file shows signs of containing scanned content (presence of images > 500 KB, OR images on > 50% of pages).
- **Tracked changes / comments:** capture in evidence bundle under `extraction.metadata.tracked_changes` and `extraction.metadata.comments`. Do not silently accept changes — record both before and after.

---

## Excel (`.xls`, `.xlsx`, `.xlsm`, `.csv`)

- **Workbook metadata:** sheet names, sheet visibility, hidden sheet flag, named ranges, defined names.
- **Per sheet:** headers (first row), used range, formulas, cell values, merged cells.
- **Hidden sheets** are flagged loudly — they are a common hiding place for sensitive data and should never be silently ignored.
- **Formulas** captured both as the formula string and the evaluated value (where pre-evaluated by Excel).
- `.csv`: standard CSV parsing with sniffer for delimiter; capture headers and first 100 rows for snippet evidence.
- **Vision fallback** is generally NOT needed for spreadsheets — but if a sheet contains an embedded image (e.g., a screenshot pasted into Excel), extract that image and run vision on it.

Library: `openpyxl` (.xlsx/.xlsm), `xlrd` (legacy .xls), Python `csv` module.

---

## PowerPoint (`.ppt`, `.pptx`)

- `python-pptx` for `.pptx` (preferred). Capture slide text, layout name, speaker notes, embedded images.
- `.ppt` (legacy): convert via LibreOffice headless mode → `.pptx`.
- **Every embedded image** goes through vision. Pitch decks often communicate via charts, photos, and infographics that are pure images — text-only extraction misses the substance.
- Speaker notes go into evidence bundle under `extraction.metadata.speaker_notes` per slide.

---

## Plain Text (`.txt`, `.md`, `.rtf`)

- Direct read with UTF-8 default; fall back to latin-1 if UTF-8 fails.
- `.rtf`: `pyth.plugins.rtf15.reader` or strip RTF markup with regex.
- `.md`: read raw; do not render. Headings used as section anchors for snippet citation.

No OCR or vision fallback (text is text).

---

## Images (`.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, `.heic`, `.webp`)

- **Always run BOTH OCR and vision.** No exceptions.
- OCR with `pytesseract` (capture confidence).
- Vision with Claude Opus (capture description, recovered text, visual elements).
- `.heic`: convert to `.png` via `Pillow` (with `pillow-heif` plugin) before OCR/vision.
- `.tif/.tiff`: multi-page TIFFs decompose into per-page processing.

---

## Archive (`.zip`, `.tar`, `.gz`, `.7z`, `.rar`)

**Out of scope for v1.** Flag in manifest with status `out_of_scope_archive`. Note in `Source_File_Manifest`: "Archive — extract contents to a separate folder and re-run."

Do NOT auto-extract. Auto-extraction creates files in the source tree, which violates the "never modify originals" rule.

---

## Email (`.eml`, `.msg`, `.mbox`)

**Out of scope for v1.** Flag in manifest with status `out_of_scope_email`. Note: "Emails not processed in v1 — export attachments and add to source folder if needed."

---

## Other / Unknown Extensions

Unsupported extensions get flagged in manifest with status `unsupported_extension`. The skill records the file in `Source_File_Manifest` but does not attempt extraction.

Examples: `.psd`, `.ai`, `.dwg`, `.cad`, `.sketch`.

---

## Resource Limits

- **Per-file extraction timeout:** 300 seconds. Files exceeding this are flagged `extraction_timeout`.
- **Page limit:** PDFs > 500 pages are processed but flagged for "consider splitting before re-running" (review_required).
- **Image size limit for vision:** images > 10 MB are downsampled to 4096 px on the longest side before submission.

---

## Library Versioning

The evidence bundle records `library_versions` for every library used in
extraction. This makes regression-testing on a different machine reproducible.
