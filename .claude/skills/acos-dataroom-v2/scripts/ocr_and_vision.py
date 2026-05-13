"""Phase 4 — OCR + Vision fallback (bridge-file dispatch).

Runs Tesseract OCR on PDF pages and standalone images. When a page needs
vision augmentation, this script does NOT call the Anthropic API directly.
Instead, it writes a request file to a bridge directory and either polls for
a response (blocking mode) or returns immediately (batch mode).

The bridge is fulfilled by the orchestrating Claude Code session: it reads
pending requests, spawns a vision-capable Task() sub-agent for each, and
writes responses back. This routes vision through the user's Claude Code
subscription instead of a separately-billed Anthropic API key.

Bridge directory layout (under <run_dir>/intermediate/vision_bridge/):

    requests/   req_<file_id>_p<page>.json   — manifest written by this script
    images/     img_<file_id>_p<page>.png    — rendered page or source image
    responses/  res_<file_id>_p<page>.json   — filled in by orchestrator
    fulfilled/  res_<file_id>_p<page>.json   — archived after rehydrate

Two modes:

    --vision-mode batch     Write request + image, mark page pending, return.
                            Caller (orchestrator) fulfills requests in bulk.
                            (Default — keeps the script non-blocking.)

    --vision-mode blocking  Write request, then poll for response until
                            --vision-timeout-seconds elapses. Convenience for
                            single-file invocations where the orchestrator is
                            available to respond synchronously.

    --vision-mode skip      Do not call vision. Useful for OCR-only smoke runs.

A separate subcommand rehydrates extraction.json after responses land:

    python ocr_and_vision.py --rehydrate --run-dir <run>

Read references/vision_fallback.md for trigger logic and references/
vision_bridge_contract.md for the request/response schemas.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import importlib
import io
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
import utils  # noqa: E402


# ---------------------------------------------------------------------------
# Tesseract OCR
# ---------------------------------------------------------------------------

def ocr_image(image_bytes: bytes) -> dict[str, Any]:
    """OCR an image. Returns {text, confidence, library}.

    Confidence is the mean per-word Tesseract confidence (0.0–1.0). If
    Tesseract is unavailable, returns a no-op record.
    """
    try:
        pytesseract = importlib.import_module("pytesseract")
        Image = importlib.import_module("PIL.Image")
    except ImportError:
        return {
            "text": "",
            "confidence": 0.0,
            "library": None,
            "error": "pytesseract or Pillow not installed",
        }

    try:
        img = Image.open(io.BytesIO(image_bytes))
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        words = []
        confs = []
        for i, txt in enumerate(data.get("text", [])):
            if txt and txt.strip():
                words.append(txt)
                conf_raw = data["conf"][i]
                try:
                    conf_val = float(conf_raw)
                except (ValueError, TypeError):
                    conf_val = -1
                if conf_val >= 0:
                    confs.append(conf_val / 100.0)
        return {
            "text": " ".join(words),
            "confidence": sum(confs) / len(confs) if confs else 0.0,
            "library": "pytesseract",
        }
    except Exception as exc:  # noqa: BLE001
        return {"text": "", "confidence": 0.0, "library": "pytesseract", "error": str(exc)}


# ---------------------------------------------------------------------------
# PDF page rendering (for OCR + vision)
# ---------------------------------------------------------------------------

def render_pdf_page(pdf_path: Path, page_number_1based: int, dpi: int = 200) -> bytes | None:
    """Render a PDF page to PNG bytes. Returns None if no renderer available."""
    try:
        pdf2image = importlib.import_module("pdf2image")
        images = pdf2image.convert_from_path(
            str(pdf_path),
            first_page=page_number_1based,
            last_page=page_number_1based,
            dpi=dpi,
        )
        buf = io.BytesIO()
        images[0].save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        pass
    except Exception:  # noqa: BLE001
        pass

    try:
        fitz = importlib.import_module("fitz")  # PyMuPDF
        doc = fitz.open(str(pdf_path))
        page = doc[page_number_1based - 1]
        zoom = dpi / 72.0
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        return pix.tobytes("png")
    except ImportError:
        return None
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# Bridge-file dispatch
# ---------------------------------------------------------------------------

BRIDGE_SCHEMA_VERSION = "1.0"

VISION_PROMPT = """You are a document analysis assistant. The image below is a single page (or
standalone image) from a document being processed for an outbound diligence
data room. Your job is to recover content and structure that pure text
extraction may have missed.

Return your analysis as STRICT JSON matching this schema (no preamble, no
prose outside the JSON):

{
  "document_type": "<your guess>",
  "extracted_text": "<full transcription including [handwritten:...], [stamped:...], [signature:...], [illegible] markers>",
  "visual_elements": ["<element 1>", "<element 2>"],
  "critical_fields": {
    "dates": [],
    "parties": [],
    "monetary_amounts": [],
    "addresses": [],
    "signatures": [{"who": "...", "location": "...", "present": true}],
    "instrument_numbers": []
  },
  "privacy_flags": [],
  "confidence_self_assessment": 0.0,
  "notes": ""
}
"""

EXPECTED_RESPONSE_SCHEMA = {
    "document_type": "string",
    "extracted_text": "string",
    "visual_elements": "list[string]",
    "critical_fields": "object",
    "privacy_flags": "list[string]",
    "confidence_self_assessment": "number",
    "notes": "string",
}


def bridge_layout(run_dir: Path) -> dict[str, Path]:
    """Return the bridge subdirectory paths under <run_dir>/intermediate/vision_bridge/."""
    root = run_dir / "intermediate" / "vision_bridge"
    return {
        "root": root,
        "requests": root / "requests",
        "images": root / "images",
        "responses": root / "responses",
        "fulfilled": root / "fulfilled",
    }


def _safe_id_segment(s: str) -> str:
    """Make a string safe for use in a filename segment."""
    return re.sub(r"[^A-Za-z0-9_\-]", "_", s)


def _request_id(file_id: str, page_number: int) -> str:
    return f"req_{_safe_id_segment(file_id)}_p{page_number}"


def write_vision_request(
    run_dir: Path,
    *,
    file_id: str,
    page_number: int,
    image_bytes: bytes,
    trigger_reason: str,
    ocr_confidence: float | None = None,
    ocr_text: str = "",
    char_count_native: int = 0,
    model_hint: str = "claude-opus-4-7",
) -> dict[str, Any]:
    """Write a vision request to the bridge. Returns a pending vision_supplement."""
    layout = bridge_layout(run_dir)
    for p in layout.values():
        p.mkdir(parents=True, exist_ok=True)

    req_id = _request_id(file_id, page_number)
    image_path = layout["images"] / f"img_{_safe_id_segment(file_id)}_p{page_number}.png"
    image_path.write_bytes(image_bytes)

    manifest = {
        "schema_version": BRIDGE_SCHEMA_VERSION,
        "request_id": req_id,
        "file_id": file_id,
        "page_number": page_number,
        "image_path": str(image_path),
        "trigger_reason": trigger_reason,
        "ocr_confidence": ocr_confidence,
        "ocr_text": ocr_text,
        "char_count_native": char_count_native,
        "prompt": VISION_PROMPT,
        "expected_schema": EXPECTED_RESPONSE_SCHEMA,
        "model_hint": model_hint,
        "created_at": _dt.datetime.utcnow().isoformat() + "Z",
        "status": "pending",
    }
    utils.write_json(layout["requests"] / f"{req_id}.json", manifest)

    return {
        "method": "claude_vision_via_bridge",
        "model": model_hint,
        "status": "pending",
        "request_id": req_id,
        "request_path": str(layout["requests"] / f"{req_id}.json"),
        "response_path": str(layout["responses"] / f"res_{req_id[4:]}.json"),
        "trigger_reason": trigger_reason,
        "rendered_at": _dt.datetime.utcnow().isoformat() + "Z",
    }


def _response_path_for(run_dir: Path, file_id: str, page_number: int) -> Path:
    layout = bridge_layout(run_dir)
    return layout["responses"] / f"res_{_safe_id_segment(file_id)}_p{page_number}.json"


def poll_for_response(
    run_dir: Path,
    file_id: str,
    page_number: int,
    *,
    timeout_seconds: float,
    poll_interval_seconds: float = 2.0,
) -> dict[str, Any] | None:
    """Block until the response file lands or timeout. Returns the parsed
    response dict or None on timeout.
    """
    response_path = _response_path_for(run_dir, file_id, page_number)
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if response_path.exists():
            try:
                return utils.read_json(response_path)
            except Exception:  # noqa: BLE001
                # File still being written; wait one more cycle.
                pass
        time.sleep(poll_interval_seconds)
    return None


def merge_response_into_supplement(
    supplement: dict[str, Any],
    response: dict[str, Any],
) -> dict[str, Any]:
    """Merge a fulfilled response into a previously-pending vision_supplement."""
    supplement = dict(supplement)
    supplement["status"] = "fulfilled"
    supplement["fulfilled_at"] = response.get(
        "fulfilled_at", _dt.datetime.utcnow().isoformat() + "Z"
    )
    supplement["fulfilled_by"] = response.get("fulfilled_by", "main-thread-task")
    supplement["model"] = response.get("model", supplement.get("model", "unknown"))
    for k in (
        "document_type",
        "extracted_text",
        "visual_elements",
        "critical_fields",
        "privacy_flags",
        "confidence_self_assessment",
        "notes",
    ):
        if k in response:
            supplement[k] = response[k]
    if "error" in response:
        supplement["error"] = response["error"]
        supplement["status"] = "error"
    return supplement


# ---------------------------------------------------------------------------
# Per-file augmentation
# ---------------------------------------------------------------------------

def augment_extraction(
    extraction_record: dict[str, Any],
    source_path: Path,
    run_dir: Path,
    *,
    ocr_threshold: float,
    max_vision_calls: int,
    vision_mode: str,
    vision_timeout_seconds: float,
    logger,
) -> dict[str, Any]:
    ext = extraction_record.get("extension", "").lower()
    pages = extraction_record.get("pages", [])
    vision_calls_used = 0

    def _dispatch_vision(
        file_id: str,
        page_num: int,
        image_bytes: bytes,
        trigger_reason: str,
        ocr_conf: float | None = None,
        ocr_text: str = "",
        char_count_native: int = 0,
    ) -> dict[str, Any]:
        if vision_mode == "skip":
            return {
                "method": "claude_vision_via_bridge",
                "status": "skipped",
                "trigger_reason": trigger_reason,
                "rendered_at": _dt.datetime.utcnow().isoformat() + "Z",
            }
        supplement = write_vision_request(
            run_dir,
            file_id=file_id,
            page_number=page_num,
            image_bytes=image_bytes,
            trigger_reason=trigger_reason,
            ocr_confidence=ocr_conf,
            ocr_text=ocr_text,
            char_count_native=char_count_native,
        )
        if vision_mode == "blocking":
            response = poll_for_response(
                run_dir, file_id, page_num,
                timeout_seconds=vision_timeout_seconds,
            )
            if response is None:
                supplement["status"] = "timeout"
                supplement["error"] = (
                    f"No response within {vision_timeout_seconds:.0f}s. "
                    "Run `--rehydrate` after the orchestrator fulfills the request."
                )
                logger.warning(
                    "Vision bridge timeout for %s p%d after %.0fs",
                    file_id, page_num, vision_timeout_seconds,
                )
            else:
                supplement = merge_response_into_supplement(supplement, response)
                logger.info("Vision bridge fulfilled for %s p%d", file_id, page_num)
        else:
            logger.debug(
                "Vision request written for %s p%d (mode=batch, fulfill via orchestrator)",
                file_id, page_num,
            )
        return supplement

    file_id = extraction_record.get("file_id", "unknown")

    # Standalone images: always OCR + vision
    if ext in {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".heic", ".webp"}:
        try:
            data = source_path.read_bytes()
        except Exception as exc:  # noqa: BLE001
            logger.error("Could not read image %s: %s", source_path, exc)
            return extraction_record

        ocr_result = ocr_image(data)
        vision_supplement: dict[str, Any]
        if vision_calls_used < max_vision_calls:
            vision_supplement = _dispatch_vision(
                file_id, 1, data,
                trigger_reason="standalone_image",
                ocr_conf=ocr_result.get("confidence", 0.0),
                ocr_text=ocr_result.get("text", ""),
                char_count_native=0,
            )
            vision_calls_used += 1
        else:
            vision_supplement = {
                "method": "claude_vision_via_bridge",
                "status": "skipped_quota_exceeded",
                "trigger_reason": "standalone_image",
            }

        pages = [{
            "page_number": 1,
            "method": "ocr",
            "text": ocr_result.get("text", ""),
            "char_count": len(ocr_result.get("text", "")),
            "confidence": ocr_result.get("confidence", 0.0),
            "vision_supplement": vision_supplement,
        }]
        extraction_record["pages"] = pages
        extraction_record.setdefault("methods_used", []).extend(
            ["ocr", "claude_vision_via_bridge"]
        )
        return extraction_record

    # PDF pages: OCR low-confidence/empty pages, then vision-augment if still weak
    if ext == ".pdf":
        for page_record in pages:
            text = page_record.get("text", "")
            char_count = page_record.get("char_count", 0)
            needs_fallback = char_count < 50

            page_num = page_record["page_number"]
            page_image: bytes | None = None

            if needs_fallback:
                page_image = render_pdf_page(source_path, page_num)
                if page_image is None:
                    page_record.setdefault("notes", []).append(
                        "needs_fallback_but_no_renderer_available"
                    )
                    continue
                ocr_result = ocr_image(page_image)
                page_record["method"] = "ocr"
                page_record["text"] = ocr_result.get("text", text)
                page_record["confidence"] = ocr_result.get("confidence", 0.0)
                page_record["char_count"] = len(page_record["text"])

            ocr_conf = (
                page_record.get("confidence", 1.0)
                if page_record.get("method") == "ocr"
                else 1.0
            )
            trigger = None
            if ocr_conf < ocr_threshold and page_record.get("method") == "ocr":
                trigger = "ocr_confidence_below_threshold"
            elif needs_fallback and not page_record.get("text", "").strip():
                trigger = "native_extraction_empty"

            if trigger and vision_calls_used < max_vision_calls:
                if page_image is None:
                    page_image = render_pdf_page(source_path, page_num)
                if page_image is not None:
                    vision_supplement = _dispatch_vision(
                        file_id, page_num, page_image,
                        trigger_reason=trigger,
                        ocr_conf=ocr_conf,
                        ocr_text=page_record.get("text", ""),
                        char_count_native=char_count,
                    )
                    page_record["vision_supplement"] = vision_supplement
                    extraction_record.setdefault("methods_used", []).append(
                        f"vision_page_{page_num}"
                    )
                    vision_calls_used += 1

        extraction_record["pages"] = pages
        return extraction_record

    # Other types: no OCR/vision needed
    return extraction_record


# ---------------------------------------------------------------------------
# Rehydration: merge fulfilled responses into extraction.json
# ---------------------------------------------------------------------------

def rehydrate_run(run_dir: Path, logger) -> dict[str, int]:
    """Walk vision_bridge/responses/, merge each into the corresponding
    extraction.json, and archive the response into vision_bridge/fulfilled/.

    Returns a summary {processed, no_extraction, no_pending, archived}.
    """
    layout = bridge_layout(run_dir)
    for p in layout.values():
        p.mkdir(parents=True, exist_ok=True)

    summary = {"processed": 0, "no_extraction": 0, "no_pending": 0, "archived": 0}

    for res_path in sorted(layout["responses"].glob("*.json")):
        try:
            response = utils.read_json(res_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skipping unreadable response %s: %s", res_path, exc)
            continue

        request_id = response.get("request_id", res_path.stem)
        m = re.match(r"^(?:req_|res_)?(.+)_p(\d+)$", request_id)
        if not m:
            logger.warning("Cannot parse request_id '%s' — skipping", request_id)
            continue
        file_id = m.group(1)
        page_number = int(m.group(2))

        ext_path = run_dir / "extraction" / file_id / "extraction.json"
        if not ext_path.exists():
            logger.warning(
                "No extraction.json for %s — orphan response %s",
                file_id, res_path.name,
            )
            summary["no_extraction"] += 1
            continue

        record = utils.read_json(ext_path)
        merged_any = False
        for page_record in record.get("pages", []):
            if page_record.get("page_number") != page_number:
                continue
            vs = page_record.get("vision_supplement") or {}
            if not isinstance(vs, dict):
                continue
            if vs.get("status") not in ("pending", "timeout"):
                summary["no_pending"] += 1
                continue
            page_record["vision_supplement"] = merge_response_into_supplement(
                vs, response,
            )
            merged_any = True

        if merged_any:
            utils.write_json(ext_path, record)
            summary["processed"] += 1
            # Archive the response so we don't re-process on the next rehydrate
            archived = layout["fulfilled"] / res_path.name
            try:
                res_path.replace(archived)
                summary["archived"] += 1
            except OSError as exc:
                logger.warning("Could not archive response %s: %s", res_path, exc)

    logger.info(
        "Rehydrate complete | processed=%d archived=%d no_extraction=%d no_pending=%d",
        summary["processed"], summary["archived"],
        summary["no_extraction"], summary["no_pending"],
    )
    return summary


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Augment extraction.json with OCR + vision-bridge requests, "
                    "or rehydrate fulfilled vision responses."
    )
    parser.add_argument(
        "--rehydrate", action="store_true",
        help="Merge fulfilled vision responses into extraction.json. "
             "When set, all other flags except --run-dir are ignored.",
    )
    parser.add_argument("--source", type=Path,
                        help="Source file path (augment mode).")
    parser.add_argument("--file-id",
                        help="Deterministic file_id (augment mode).")
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--max-vision-calls", type=int, default=200)
    parser.add_argument(
        "--vision-mode",
        choices=("batch", "blocking", "skip"),
        default="batch",
        help="Dispatch mode for vision requests. "
             "batch (default): write request, return immediately. "
             "blocking: wait for response up to --vision-timeout-seconds. "
             "skip: do not call vision at all.",
    )
    parser.add_argument(
        "--vision-timeout-seconds", type=float, default=300.0,
        help="Per-page timeout when --vision-mode=blocking (default: 300s).",
    )
    args = parser.parse_args(argv)

    layout = {"base": args.run_dir, "logs": args.run_dir / "logs",
              "extraction": args.run_dir / "extraction",
              "evidence": args.run_dir / "evidence",
              "intermediate": args.run_dir / "intermediate"}
    utils.ensure_run_dirs(layout)
    logger = utils.make_logger(layout)

    if args.rehydrate:
        summary = rehydrate_run(args.run_dir, logger)
        print(f"Rehydrated: processed={summary['processed']} "
              f"archived={summary['archived']} "
              f"no_extraction={summary['no_extraction']} "
              f"no_pending={summary['no_pending']}")
        return 0

    if not args.source or not args.file_id:
        parser.error("--source and --file-id are required in augment mode "
                     "(omit only when using --rehydrate).")

    cfg = utils.load_config()
    threshold = cfg.get("ocr_confidence_threshold", 0.70)

    extraction_path = args.run_dir / "extraction" / args.file_id / "extraction.json"
    if not extraction_path.exists():
        logger.error("No extraction.json at %s — run extract_text.py first",
                     extraction_path)
        return 2

    record = utils.read_json(extraction_path)
    # Ensure file_id flows into augment_extraction (used as bridge request key)
    record.setdefault("file_id", args.file_id)
    record = augment_extraction(
        record, args.source, args.run_dir,
        ocr_threshold=threshold,
        max_vision_calls=args.max_vision_calls,
        vision_mode=args.vision_mode,
        vision_timeout_seconds=args.vision_timeout_seconds,
        logger=logger,
    )
    utils.write_json(extraction_path, record)
    logger.info("Augmented extraction for %s (vision_mode=%s)",
                args.file_id, args.vision_mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
