"""Smoke tests for acos-dataroom.

Exercise the core pipeline without requiring vision API access. Includes
end-to-end coverage of the vision-bridge protocol (request write → mock
fulfill → rehydrate merge) introduced in v1.1.0.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Tests live at .claude/skills/acos-dataroom/tests/
SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL_DIR / "scripts"
FIXTURE = SKILL_DIR / "tests" / "fixtures" / "synthetic_loan"


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def test_fixture_present() -> None:
    """The synthetic loan fixture must exist with full file-type coverage."""
    assert FIXTURE.exists(), f"Missing fixture: {FIXTURE}"
    files = list(FIXTURE.rglob("*"))
    real_files = [f for f in files if f.is_file()]
    assert len(real_files) >= 8, f"Fixture has too few files: {len(real_files)}"

    # Confirm the file-type coverage added in v1.2.0 — PDF/DOCX/image paths
    # must be exercised by the smoke tests, not just text/CSV/Markdown.
    exts = {f.suffix.lower() for f in real_files}
    for required in (".pdf", ".docx", ".png"):
        assert required in exts, f"Fixture missing {required} coverage"


def test_scan_folder_smoke() -> None:
    """scan_folder.py produces a manifest covering the fixture."""
    with tempfile.TemporaryDirectory() as tmp:
        # Copy fixture into a temp location so we don't pollute the source
        src = Path(tmp) / "loan"
        shutil.copytree(FIXTURE, src)

        run_dir = src / "_acos_dataroom_output" / "smoketest_run"
        run_dir.mkdir(parents=True, exist_ok=True)

        _run([
            sys.executable,
            str(SCRIPTS / "scan_folder.py"),
            "--source", str(src),
            "--run-dir", str(run_dir),
        ])

        manifest_path = run_dir / "intermediate" / "file_manifest.json"
        assert manifest_path.exists(), "Expected file_manifest.json"

        manifest = json.loads(manifest_path.read_text())
        assert manifest["file_count"] >= 5, f"Expected >=5 files, got {manifest['file_count']}"
        # System files (.DS_Store) absent because we copied; just confirm structure
        ext_count = manifest["extracted_count"]
        assert ext_count >= 5, f"Expected >=5 extractable files, got {ext_count}"

        # Every file_id should be deterministic (12 hex chars after f_)
        for f in manifest["files"]:
            if f["inclusion_in_extraction"] == "extracted":
                fid = f["file_id"]
                assert fid.startswith("f_"), f"Bad file_id: {fid}"
                assert len(fid) == 14, f"Bad file_id length: {fid}"


def test_extract_text_smoke() -> None:
    """extract_text.py succeeds on a representative subset, including PDF/DOCX."""
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "loan"
        shutil.copytree(FIXTURE, src)
        run_dir = src / "_acos_dataroom_output" / "smoketest_run"
        run_dir.mkdir(parents=True, exist_ok=True)

        _run([
            sys.executable,
            str(SCRIPTS / "scan_folder.py"),
            "--source", str(src),
            "--run-dir", str(run_dir),
        ])

        manifest = json.loads(
            (run_dir / "intermediate" / "file_manifest.json").read_text()
        )

        # Track which file types we actually exercised so we can assert later
        ext_records_by_ext: dict[str, dict] = {}

        for f in manifest["files"]:
            if f["inclusion_in_extraction"] != "extracted":
                continue
            _run([
                sys.executable,
                str(SCRIPTS / "extract_text.py"),
                "--source", f["source_path"],
                "--file-id", f["file_id"],
                "--run-dir", str(run_dir),
            ])
            ext_json = run_dir / "extraction" / f["file_id"] / "extraction.json"
            assert ext_json.exists(), f"Missing extraction.json for {f['file_id']}"
            record = json.loads(ext_json.read_text())
            ext_records_by_ext.setdefault(f["extension"], record)

        # PDF: must have at least one page with native text containing $1,500,000
        pdf_rec = ext_records_by_ext.get(".pdf")
        assert pdf_rec is not None, "PDF fixture was not extracted"
        pdf_text = "\n".join(p.get("text", "") for p in pdf_rec.get("pages", []))
        assert "1,500,000" in pdf_text or "1500000" in pdf_text, \
            f"Expected $1,500,000 in PDF text, got: {pdf_text[:200]}"
        assert pdf_rec.get("library") in ("pdfplumber", "pypdf"), \
            f"Expected pdfplumber/pypdf library, got {pdf_rec.get('library')}"

        # DOCX: must extract Borrower / Lender / Principal
        docx_rec = ext_records_by_ext.get(".docx")
        assert docx_rec is not None, "DOCX fixture was not extracted"
        docx_text = "\n".join(p.get("text", "") for p in docx_rec.get("pages", []))
        assert "Borrower" in docx_text and "OKOA Capital" in docx_text, \
            f"DOCX text missing expected entities: {docx_text[:200]}"

        # PNG: extract_text leaves it empty (pages == []); ocr_and_vision handles it
        png_rec = ext_records_by_ext.get(".png")
        assert png_rec is not None, "PNG fixture was not extracted"
        assert png_rec.get("metadata", {}).get("is_image_only") is True, \
            f"PNG should be flagged image-only: {png_rec}"


def test_run_directory_layout() -> None:
    """ensure_run_dirs creates all expected subfolders."""
    sys.path.insert(0, str(SCRIPTS))
    import utils  # type: ignore  # noqa: E402

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp)
        layout = utils.run_dir_layout(src, "test_run_id")
        utils.ensure_run_dirs(layout)
        for key, path in layout.items():
            assert path.exists(), f"Missing {key}: {path}"


# ---------------------------------------------------------------------------
# Vision bridge — end-to-end contract test (v1.1.0+)
# ---------------------------------------------------------------------------

def _make_test_png(target: Path) -> None:
    """Write a 4x4 black PNG using PIL (already a project dependency)."""
    from PIL import Image
    img = Image.new("RGB", (4, 4), color=(0, 0, 0))
    img.save(str(target), format="PNG")


def test_vision_bridge_skip_mode() -> None:
    """--vision-mode skip writes no requests and marks pages skipped."""
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "loan"
        src.mkdir()
        img_path = src / "scan.png"
        _make_test_png(img_path)

        run_dir = src / "_acos_dataroom_output" / "skip_test"
        run_dir.mkdir(parents=True, exist_ok=True)
        file_id = "f_skip0000test"
        ext_dir = run_dir / "extraction" / file_id
        ext_dir.mkdir(parents=True)
        # Seed an extraction record (extract_text.py would do this in real flow)
        (ext_dir / "extraction.json").write_text(json.dumps({
            "schema_version": "1.0",
            "file_id": file_id,
            "extension": ".png",
            "library": None,
            "pages": [],
            "metadata": {"is_image_only": True},
        }))

        _run([
            sys.executable, str(SCRIPTS / "ocr_and_vision.py"),
            "--source", str(img_path),
            "--file-id", file_id,
            "--run-dir", str(run_dir),
            "--vision-mode", "skip",
        ])

        bridge_reqs = run_dir / "intermediate" / "vision_bridge" / "requests"
        if bridge_reqs.exists():
            assert not list(bridge_reqs.glob("*.json")), \
                "skip mode must not write requests"

        record = json.loads((ext_dir / "extraction.json").read_text())
        assert record["pages"], "page record missing"
        vs = record["pages"][0].get("vision_supplement", {})
        assert vs.get("status") == "skipped", f"expected skipped, got {vs}"


def test_vision_bridge_batch_and_rehydrate() -> None:
    """Full bridge round-trip: batch write → fake response → rehydrate."""
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "loan"
        src.mkdir()
        img_path = src / "scan.png"
        _make_test_png(img_path)

        run_dir = src / "_acos_dataroom_output" / "bridge_test"
        run_dir.mkdir(parents=True, exist_ok=True)
        file_id = "f_brdg0000test"
        ext_dir = run_dir / "extraction" / file_id
        ext_dir.mkdir(parents=True)
        (ext_dir / "extraction.json").write_text(json.dumps({
            "schema_version": "1.0",
            "file_id": file_id,
            "extension": ".png",
            "library": None,
            "pages": [],
            "metadata": {"is_image_only": True},
        }))

        # 1. Batch mode writes a request and marks page pending.
        _run([
            sys.executable, str(SCRIPTS / "ocr_and_vision.py"),
            "--source", str(img_path),
            "--file-id", file_id,
            "--run-dir", str(run_dir),
            "--vision-mode", "batch",
        ])

        bridge_root = run_dir / "intermediate" / "vision_bridge"
        reqs = list((bridge_root / "requests").glob("*.json"))
        assert len(reqs) == 1, f"expected 1 request, got {len(reqs)}"
        request = json.loads(reqs[0].read_text())
        assert request["status"] == "pending"
        assert request["file_id"] == file_id
        assert request["page_number"] == 1
        assert Path(request["image_path"]).exists(), "image not persisted"

        record = json.loads((ext_dir / "extraction.json").read_text())
        vs = record["pages"][0]["vision_supplement"]
        assert vs["status"] == "pending"
        assert vs["request_id"] == request["request_id"]

        # 2. Orchestrator simulator writes a fake response.
        resp_dir = bridge_root / "responses"
        resp_dir.mkdir(parents=True, exist_ok=True)
        response = {
            "request_id": request["request_id"],
            "fulfilled_at": "2026-05-11T13:00:00Z",
            "fulfilled_by": "test-harness",
            "model": "claude-opus-4-7",
            "document_type": "synthetic-test-doc",
            "extracted_text": "test transcription",
            "visual_elements": ["signature"],
            "critical_fields": {"dates": ["2026-05-11"]},
            "privacy_flags": [],
            "confidence_self_assessment": 0.92,
            "notes": "",
        }
        res_name = request["request_id"].replace("req_", "res_", 1) + ".json"
        (resp_dir / res_name).write_text(json.dumps(response))

        # 3. Rehydrate merges the response back into extraction.json.
        _run([
            sys.executable, str(SCRIPTS / "ocr_and_vision.py"),
            "--rehydrate", "--run-dir", str(run_dir),
        ])

        record = json.loads((ext_dir / "extraction.json").read_text())
        vs = record["pages"][0]["vision_supplement"]
        assert vs["status"] == "fulfilled", f"expected fulfilled, got {vs}"
        assert vs["document_type"] == "synthetic-test-doc"
        assert vs["extracted_text"] == "test transcription"
        assert vs["confidence_self_assessment"] == 0.92

        # 4. Response was archived; rehydrate is now a no-op.
        archived = bridge_root / "fulfilled" / res_name
        assert archived.exists(), "response should be archived"
        assert not (resp_dir / res_name).exists(), \
            "archived response should leave responses/ dir empty"


if __name__ == "__main__":
    test_fixture_present()
    print("✓ test_fixture_present")
    test_scan_folder_smoke()
    print("✓ test_scan_folder_smoke")
    test_extract_text_smoke()
    print("✓ test_extract_text_smoke")
    test_run_directory_layout()
    print("✓ test_run_directory_layout")
    test_vision_bridge_skip_mode()
    print("✓ test_vision_bridge_skip_mode")
    test_vision_bridge_batch_and_rehydrate()
    print("✓ test_vision_bridge_batch_and_rehydrate")
    print("\nAll smoke tests passed.")
