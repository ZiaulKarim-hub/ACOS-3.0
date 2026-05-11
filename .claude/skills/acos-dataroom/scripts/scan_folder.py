"""Phase 3 — File inventory.

Recursively scan a source folder. Capture metadata, hash every file, detect
duplicates, flag inaccessible / encrypted / corrupt / zero-byte / unsupported
files, and write file_manifest.json + file_manifest.csv.

Never modifies originals.

Usage:
    python scan_folder.py --source /path/to/folder --run-dir /path/to/_acos_dataroom_output/run_xxx
    python scan_folder.py --source /path/to/folder --shallow  # Phase 1 quick mode
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import fnmatch
import json
import sys
from pathlib import Path
from typing import Any

# Allow running as a script from any CWD
sys.path.insert(0, str(Path(__file__).parent))
import utils  # noqa: E402

SUPPORTED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".xlsm", ".csv",
    ".ppt", ".pptx", ".txt", ".md", ".rtf",
    ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".heic", ".webp",
}

OUT_OF_SCOPE_EMAIL = {".eml", ".msg", ".mbox"}
OUT_OF_SCOPE_ARCHIVE = {".zip", ".tar", ".gz", ".7z", ".rar"}


def classify_inclusion(
    path: Path,
    cfg: dict[str, Any],
    excluded_folders: list[str],
) -> tuple[str, str]:
    """Return (inclusion_status, notes)."""
    name = path.name
    ext = path.suffix.lower()

    if utils.is_system_file(name, cfg.get("system_files_excluded", [])):
        return "system_excluded", f"Matched system-files-excluded pattern"

    for ef in excluded_folders:
        if any(fnmatch.fnmatch(part, ef) for part in path.parts):
            return "user_excluded", f"User-excluded folder: {ef}"

    try:
        size = path.stat().st_size
    except OSError as exc:
        return "inaccessible", f"stat failed: {exc}"

    if size == 0:
        return "zero_byte", "Empty file"

    if ext in OUT_OF_SCOPE_EMAIL:
        return "out_of_scope_email", "Email files not processed in v1"

    if ext in OUT_OF_SCOPE_ARCHIVE:
        return "out_of_scope_archive", "Archives not processed in v1 — extract contents and re-run"

    if ext not in SUPPORTED_EXTENSIONS:
        return "unsupported_extension", f"No extraction recipe for {ext}"

    # PDF encrypted check
    if ext == ".pdf":
        try:
            with utils.safe_open(path, "rb") as fh:
                head = fh.read(4096)
            if b"/Encrypt" in head:
                return "encrypted", "PDF contains /Encrypt — likely password-protected"
        except Exception:  # noqa: BLE001
            pass

    return "extracted", ""


def scan(
    source: Path,
    run_dir: Path,
    excluded_folders: list[str] | None = None,
    *,
    shallow: bool = False,
) -> dict[str, Any]:
    cfg = utils.load_config()
    excluded_folders = excluded_folders or []
    layout = {
        "base": run_dir,
        "extraction": run_dir / "extraction",
        "evidence": run_dir / "evidence",
        "intermediate": run_dir / "intermediate",
        "logs": run_dir / "logs",
    }
    utils.ensure_run_dirs(layout)
    logger = utils.make_logger(layout)

    files: list[dict[str, Any]] = []
    seen_hashes: dict[str, str] = {}  # hash -> first file_id
    duplicate_groups: dict[str, list[str]] = {}

    for path in source.rglob("*"):
        if path.is_dir():
            continue
        # Don't include the output subfolder in the scan
        if cfg.get("output_subfolder") in path.parts:
            continue

        try:
            stat = path.stat()
            size_bytes = stat.st_size
            modified_iso = _dt.datetime.fromtimestamp(stat.st_mtime).isoformat()
        except OSError as exc:
            logger.warning("stat failed for %s: %s", path, exc)
            continue

        inclusion, notes = classify_inclusion(path, cfg, excluded_folders)

        # Hashing — skip in shallow mode for speed
        sha256 = ""
        file_id = ""
        if not shallow and inclusion == "extracted":
            try:
                sha256 = utils.sha256_file(path)
                file_id = utils.file_id_from_hash(sha256)
                if sha256 in seen_hashes:
                    primary = seen_hashes[sha256]
                    duplicate_groups.setdefault(primary, [primary]).append(file_id)
                else:
                    seen_hashes[sha256] = file_id
            except Exception as exc:  # noqa: BLE001
                logger.warning("hash failed for %s: %s", path, exc)
                inclusion = "inaccessible"
                notes = f"Hash failed: {exc}"

        record = {
            "file_id": file_id,
            "file_name": path.name,
            "extension": path.suffix.lower(),
            "size_bytes": size_bytes,
            "modified_date": modified_iso,
            "source_path": str(path),
            "relative_path": utils.relative_to(path, source),
            "sha256_hash": sha256,
            "parent_folder": str(path.parent.relative_to(source)) if path.parent != source else "",
            "inclusion_in_extraction": inclusion,
            "notes": notes,
        }
        files.append(record)
        if not shallow:
            logger.debug("scanned | %s | inclusion=%s", path, inclusion)

    manifest = {
        "schema_version": utils.SCHEMA_VERSION,
        "scanned_at": _dt.datetime.utcnow().isoformat() + "Z",
        "source": str(source),
        "shallow": shallow,
        "file_count": len(files),
        "extracted_count": sum(1 for f in files if f["inclusion_in_extraction"] == "extracted"),
        "duplicate_groups": duplicate_groups,
        "files": files,
    }

    # Write outputs
    out_dir = layout["intermediate"]
    out_dir.mkdir(parents=True, exist_ok=True)
    utils.write_json(out_dir / "file_manifest.json", manifest)

    csv_path = out_dir / "file_manifest.csv"
    if files:
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(files[0].keys()))
            writer.writeheader()
            writer.writerows(files)

    logger.info(
        "Scan complete: %d files (%d extractable, %d excluded, %d duplicate groups).",
        len(files),
        manifest["extracted_count"],
        len(files) - manifest["extracted_count"],
        len(duplicate_groups),
    )

    if not shallow:
        utils.mark_phase_complete(layout, "phase_3_inventory", extra={
            "file_count": len(files),
            "extracted_count": manifest["extracted_count"],
        })

    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan a source folder for acos-dataroom.")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--run-dir", type=Path, help="Run directory; if omitted, derive from --source.")
    parser.add_argument("--excluded-folder", action="append", default=[])
    parser.add_argument("--shallow", action="store_true", help="Phase 1 quick scan (no hashing).")
    args = parser.parse_args(argv)

    if not args.source.exists():
        parser.error(f"Source does not exist: {args.source}")

    run_dir = args.run_dir
    if run_dir is None:
        run_id = utils.make_run_id(args.source)
        layout = utils.run_dir_layout(args.source, run_id)
        run_dir = layout["base"]
        utils.ensure_run_dirs(layout)

    scan(args.source, run_dir, args.excluded_folder, shallow=args.shallow)
    print(f"Manifest written to: {run_dir}/intermediate/file_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
