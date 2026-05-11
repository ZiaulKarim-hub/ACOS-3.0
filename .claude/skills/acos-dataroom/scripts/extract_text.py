"""Phase 4 — Extraction.

Per-file dispatch by extension. Native extraction for PDFs (pdfplumber),
Word (python-docx), Excel (openpyxl), PowerPoint (python-pptx), text files.
Hands off to ocr_and_vision.py when text extraction is insufficient.

Each call writes a per-file extraction record to:
    <run_dir>/extraction/<file_id>/extraction.json

The extraction record is one of the inputs the evidence-bundle builder uses
to construct the per-file evidence bundle.

Optional dependencies handled gracefully (clear error if unavailable rather
than crashing the run).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import importlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
import utils  # noqa: E402

LIB_VERSIONS: dict[str, str] = {}


def _try_import(module_name: str):
    """Import a module if available; return None and log otherwise."""
    try:
        mod = importlib.import_module(module_name)
        version = getattr(mod, "__version__", "unknown")
        LIB_VERSIONS[module_name] = version
        return mod
    except ImportError:
        return None


def extract_pdf(path: Path) -> dict[str, Any]:
    """Native PDF extraction with pdfplumber, fallback to pypdf."""
    pdfplumber = _try_import("pdfplumber")
    pypdf = _try_import("pypdf")

    pages: list[dict[str, Any]] = []

    if pdfplumber is not None:
        try:
            with pdfplumber.open(str(path)) as pdf:
                for i, page in enumerate(pdf.pages, 1):
                    text = page.extract_text() or ""
                    pages.append({
                        "page_number": i,
                        "method": "native_pdf",
                        "text": text,
                        "char_count": len(text),
                        "confidence": 1.0 if text.strip() else 0.0,
                        "needs_fallback": len(text.strip()) < 50,
                    })
            return {"pages": pages, "library": "pdfplumber"}
        except Exception as exc:  # noqa: BLE001
            return {"pages": [], "error": f"pdfplumber failed: {exc}", "library": "pdfplumber"}

    if pypdf is not None:
        try:
            reader = pypdf.PdfReader(str(path))
            for i, page in enumerate(reader.pages, 1):
                text = page.extract_text() or ""
                pages.append({
                    "page_number": i,
                    "method": "native_pdf",
                    "text": text,
                    "char_count": len(text),
                    "confidence": 1.0 if text.strip() else 0.0,
                    "needs_fallback": len(text.strip()) < 50,
                })
            return {"pages": pages, "library": "pypdf"}
        except Exception as exc:  # noqa: BLE001
            return {"pages": [], "error": f"pypdf failed: {exc}", "library": "pypdf"}

    return {
        "pages": [],
        "error": "No PDF library available — install pdfplumber or pypdf",
        "library": None,
    }


def extract_docx(path: Path) -> dict[str, Any]:
    docx_mod = _try_import("docx")  # python-docx
    if docx_mod is None:
        return {"error": "python-docx not installed", "library": None}
    try:
        doc = docx_mod.Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        tables = []
        for tbl in doc.tables:
            rows = []
            for row in tbl.rows:
                rows.append([cell.text for cell in row.cells])
            tables.append(rows)
        text = "\n\n".join(paragraphs)
        return {
            "library": "python-docx",
            "pages": [{
                "page_number": 1,
                "method": "native_docx",
                "text": text,
                "char_count": len(text),
                "confidence": 1.0,
            }],
            "metadata": {
                "paragraph_count": len(paragraphs),
                "table_count": len(tables),
                "tables": tables,
            },
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": f"docx extraction failed: {exc}", "library": "python-docx"}


def extract_xlsx(path: Path) -> dict[str, Any]:
    openpyxl = _try_import("openpyxl")
    if openpyxl is None:
        return {"error": "openpyxl not installed", "library": None}
    try:
        max_rows = int(utils.load_config().get("xlsx_max_rows_per_sheet", 1000))
        wb = openpyxl.load_workbook(str(path), data_only=False, read_only=True)
        sheets = []
        truncated_sheets: list[str] = []
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            visible = ws.sheet_state == "visible"
            rows: list[list[Any]] = []
            truncated = False
            for row in ws.iter_rows(values_only=True):
                rows.append([("" if v is None else str(v)) for v in row])
                if len(rows) >= max_rows:
                    # Probe whether more rows existed after the cap
                    try:
                        next(ws.iter_rows(values_only=True, min_row=max_rows + 1, max_row=max_rows + 1))
                        truncated = True
                    except StopIteration:
                        pass
                    break
            if truncated:
                truncated_sheets.append(sheet_name)
            sheets.append({
                "sheet_name": sheet_name,
                "visible": visible,
                "row_count_sampled": len(rows),
                "truncated_at_row_cap": truncated,
                "rows": rows,
            })
        text_blob = "\n\n".join(
            f"## Sheet: {s['sheet_name']}{' (HIDDEN)' if not s['visible'] else ''}"
            f"{' (TRUNCATED)' if s.get('truncated_at_row_cap') else ''}\n" +
            "\n".join("\t".join(r) for r in s["rows"])
            for s in sheets
        )
        page_notes = (
            [f"truncated_at_{max_rows}_rows:{','.join(truncated_sheets)}"]
            if truncated_sheets else []
        )
        return {
            "library": "openpyxl",
            "pages": [{
                "page_number": 1,
                "method": "native_xlsx",
                "text": text_blob,
                "char_count": len(text_blob),
                "confidence": 1.0,
                **({"notes": page_notes} if page_notes else {}),
            }],
            "metadata": {
                "sheet_count": len(sheets),
                "hidden_sheet_count": sum(1 for s in sheets if not s["visible"]),
                "row_cap_per_sheet": max_rows,
                "truncated_sheets": truncated_sheets,
                "sheets": sheets,
            },
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": f"openpyxl extraction failed: {exc}", "library": "openpyxl"}


def extract_csv(path: Path) -> dict[str, Any]:
    import csv
    try:
        with open(path, "r", encoding="utf-8", errors="replace", newline="") as fh:
            sample = fh.read(8192)
            fh.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample) if sample else csv.excel
            except csv.Error:
                dialect = csv.excel
            reader = csv.reader(fh, dialect)
            rows = list(reader)[:200]
        text = "\n".join("\t".join(r) for r in rows)
        return {
            "library": "stdlib-csv",
            "pages": [{
                "page_number": 1,
                "method": "native_csv",
                "text": text,
                "char_count": len(text),
                "confidence": 1.0,
            }],
            "metadata": {"row_count_sampled": len(rows)},
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": f"csv extraction failed: {exc}", "library": "stdlib-csv"}


def extract_pptx(path: Path) -> dict[str, Any]:
    pptx_mod = _try_import("pptx")
    if pptx_mod is None:
        return {"error": "python-pptx not installed", "library": None}
    try:
        prs = pptx_mod.Presentation(str(path))
        slides = []
        for i, slide in enumerate(prs.slides, 1):
            slide_text = []
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        for run in paragraph.runs:
                            if run.text.strip():
                                slide_text.append(run.text)
            notes_text = ""
            if slide.has_notes_slide:
                notes_text = slide.notes_slide.notes_text_frame.text or ""
            slides.append({
                "slide_number": i,
                "text": "\n".join(slide_text),
                "speaker_notes": notes_text,
            })
        text_blob = "\n\n".join(
            f"## Slide {s['slide_number']}\n{s['text']}\n[notes] {s['speaker_notes']}"
            for s in slides
        )
        return {
            "library": "python-pptx",
            "pages": [{
                "page_number": 1,
                "method": "native_pptx",
                "text": text_blob,
                "char_count": len(text_blob),
                "confidence": 1.0,
            }],
            "metadata": {"slide_count": len(slides), "slides": slides},
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": f"pptx extraction failed: {exc}", "library": "python-pptx"}


def extract_text_file(path: Path) -> dict[str, Any]:
    encodings = ["utf-8", "latin-1"]
    text = ""
    for enc in encodings:
        try:
            text = path.read_text(encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    return {
        "library": "stdlib-text",
        "pages": [{
            "page_number": 1,
            "method": "native_text",
            "text": text,
            "char_count": len(text),
            "confidence": 1.0,
        }],
    }


DISPATCH = {
    ".pdf": extract_pdf,
    ".docx": extract_docx,
    ".xlsx": extract_xlsx,
    ".xlsm": extract_xlsx,
    ".xls": extract_xlsx,
    ".csv": extract_csv,
    ".pptx": extract_pptx,
    ".ppt": extract_pptx,
    ".txt": extract_text_file,
    ".md": extract_text_file,
    ".rtf": extract_text_file,
}


def extract_one(path: Path, file_id: str, run_dir: Path, logger) -> dict[str, Any]:
    """Run extraction on a single file and write extraction.json."""
    ext = path.suffix.lower()
    out_dir = run_dir / "extraction" / file_id
    out_dir.mkdir(parents=True, exist_ok=True)

    if ext in {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".heic", ".webp"}:
        # Pure image — leave native extraction empty; ocr_and_vision.py handles it.
        result = {"library": None, "pages": [], "metadata": {"is_image_only": True}}
    elif ext in DISPATCH:
        result = DISPATCH[ext](path)
    else:
        result = {"error": f"No extractor for extension {ext}", "library": None, "pages": []}

    record = {
        "schema_version": utils.SCHEMA_VERSION,
        "file_id": file_id,
        "extension": ext,
        "extracted_at": _dt.datetime.utcnow().isoformat() + "Z",
        "library_versions": dict(LIB_VERSIONS),
        **result,
    }
    utils.write_json(out_dir / "extraction.json", record)

    if "error" in result:
        logger.warning("Extraction error for %s: %s", file_id, result["error"])
    else:
        logger.debug("Extracted %s | pages=%d", file_id, len(result.get("pages", [])))

    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract text from a single file.")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--file-id", required=True)
    parser.add_argument("--run-dir", required=True, type=Path)
    args = parser.parse_args(argv)

    layout = {"base": args.run_dir, "logs": args.run_dir / "logs",
              "extraction": args.run_dir / "extraction",
              "evidence": args.run_dir / "evidence",
              "intermediate": args.run_dir / "intermediate"}
    utils.ensure_run_dirs(layout)
    logger = utils.make_logger(layout)
    extract_one(args.source, args.file_id, args.run_dir, logger)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
