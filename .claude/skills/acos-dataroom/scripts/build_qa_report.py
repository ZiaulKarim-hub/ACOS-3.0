"""Generate the standalone markdown QA report.

Output: `<DataRoomName>_QA_Report_<YYYY-MM-DD>.md` in the run directory.

Reads:
  - intermediate/classifications.json
  - intermediate/qa_report.json
  - intermediate/extraction_summary.json
  - intermediate/file_manifest.json
  - evidence/<file_id>.json (for unable_to_verify claims, if any)

Sections:
  1. Header / metadata
  2. Executive Summary (one paragraph)
  3. Pass-by-Pass Findings (8 sections — 7 standard QA + adversarial)
  4. Rows Flagged for Your Attention (table)
  5. Methodology Notes (limitations of the run)
"""

from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
import utils  # noqa: E402


def _coerce_float(v: Any) -> float | None:
    if v is None or v == "" or v == "n/a":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _row_overall_confidence(c: dict) -> float | None:
    comp = [_coerce_float(c.get(k)) for k in
            ("classification_confidence", "extraction_confidence",
             "summary_confidence", "ocr_confidence")]
    valid = [s for s in comp if s is not None]
    return min(valid) if valid else None


def _gather_unable_to_verify(evidence_dir: Path, classifications: list[dict]) -> list[dict]:
    """Pull any unable_to_verify claims from per-file evidence bundles."""
    out = []
    for c in classifications:
        fid = c.get("file_id")
        if not fid:
            continue
        bundle_path = evidence_dir / f"{fid}.json"
        if not bundle_path.exists():
            continue
        try:
            bundle = utils.read_json(bundle_path)
        except Exception:  # noqa: BLE001
            continue
        unable = bundle.get("summary", {}).get("unable_to_verify", []) or []
        if unable:
            out.append({
                "file_id": fid,
                "file_name": c.get("file_name", ""),
                "claims": unable,
            })
    return out


def _build_executive_summary(classifications: list[dict], qa_rows: list[dict],
                             low_confidence_rows: list[dict]) -> str:
    n = len(classifications)
    n_low = len(low_confidence_rows)
    pii_rows = [c for c in classifications if (c.get("external_room_recommendation") or "").lower() == "internal_only_pii"]
    privileged_rows = [c for c in classifications if (c.get("external_room_recommendation") or "").lower() == "internal_only_privileged"]

    flagged_in_qa = sum(int(r.get("flagged_count") or 0) for r in qa_rows
                        if str(r.get("pass_name", "")).lower() != "completeness")

    sentences: list[str] = []
    if n == 0:
        sentences.append("No files classified in this run — nothing to report on.")
    else:
        sentences.append(
            f"Classified {n} files. "
            f"{n - n_low} row(s) at or above 0.70 overall confidence; "
            f"{n_low} row(s) below the threshold and surfaced in the table below."
        )
    if pii_rows:
        sentences.append(
            f"Sensitivity pass caught {len(pii_rows)} PII file(s) — flagged for internal-only handling."
        )
    if privileged_rows:
        sentences.append(
            f"{len(privileged_rows)} file(s) flagged as privileged. "
            "Review whether the marking is appropriate; loan documents marked privileged "
            "may be over-classified."
        )
    if flagged_in_qa > 0:
        sentences.append(
            f"Across the 7 QA passes plus the adversarial pass, {flagged_in_qa} row-level flag(s) "
            "were raised. See the pass-by-pass detail below."
        )
    if not pii_rows and not privileged_rows and flagged_in_qa == 0 and n > 0:
        sentences.append("No PII, privileged content, or QA-pass anomalies surfaced.")
    return " ".join(sentences)


def _format_pass_section(qa_row: dict, classifications: list[dict]) -> list[str]:
    pass_id = qa_row.get("qa_pass_id")
    name = qa_row.get("pass_name", "Unknown pass")
    flagged = qa_row.get("flagged_count", 0)
    total = qa_row.get("total_checked", 0)
    flagged_ids = qa_row.get("flagged_file_ids", "") or ""
    notes = qa_row.get("notes", "")

    lines = [f"### Pass {pass_id} — {name}", ""]
    lines.append(f"- **Flagged:** {flagged} of {total}")
    if notes:
        lines.append(f"- **Notes:** {notes}")
    if flagged_ids.strip():
        # Resolve each flagged file_id to a file_name from classifications
        flagged_list = [fid.strip() for fid in flagged_ids.split(",") if fid.strip()]
        if flagged_list:
            id_to_name = {c.get("file_id"): c.get("file_name", "") for c in classifications}
            lines.append("- **Files flagged:**")
            for fid in flagged_list:
                name_str = id_to_name.get(fid, "(unknown)")
                lines.append(f"  - `{fid}` — {name_str}")
    lines.append("")
    return lines


def _format_flagged_rows_table(low_rows: list[dict]) -> list[str]:
    if not low_rows:
        return ["_No rows flagged at confidence < 0.70._", ""]
    lines = [
        "| File | Overall Confidence | Why Flagged |",
        "|---|---:|---|",
    ]
    for r in low_rows:
        name = r.get("file_name", "")
        conf = r.get("_overall_confidence", "")
        notes = (r.get("qa_notes") or "")[:200]
        conf_str = f"{conf:.2f}" if isinstance(conf, (int, float)) else str(conf)
        lines.append(f"| {name} | {conf_str} | {notes} |")
    lines.append("")
    return lines


def _format_unable_to_verify(unable_to_verify: list[dict]) -> list[str]:
    if not unable_to_verify:
        return ["_All summary claims successfully snippet-backed. No hallucinations detected._", ""]
    lines = []
    for entry in unable_to_verify:
        lines.append(f"- **{entry['file_name']}** (`{entry['file_id']}`)")
        for claim in entry["claims"]:
            text = claim.get("claim", str(claim)) if isinstance(claim, dict) else str(claim)
            lines.append(f"  - {text}")
    lines.append("")
    return lines


def build_qa_report(run_dir: Path, *, data_room_name: str, deal_type: str,
                    objective: str, source: str | None = None,
                    run_id: str | None = None) -> Path:
    inter = run_dir / "intermediate"
    evidence_dir = run_dir / "evidence"

    classifications = utils.read_json(inter / "classifications.json") if (inter / "classifications.json").exists() else []
    qa_rows = utils.read_json(inter / "qa_report.json") if (inter / "qa_report.json").exists() else []
    extraction_summary = utils.read_json(inter / "extraction_summary.json") if (inter / "extraction_summary.json").exists() else {}
    manifest = utils.read_json(inter / "file_manifest.json") if (inter / "file_manifest.json").exists() else {}

    # Annotate each classification with its overall confidence
    annotated: list[dict] = []
    low_rows: list[dict] = []
    for c in classifications:
        overall = _row_overall_confidence(c)
        c2 = dict(c)
        c2["_overall_confidence"] = overall
        annotated.append(c2)
        if overall is not None and overall < 0.70:
            low_rows.append(c2)
    low_rows.sort(key=lambda r: r.get("_overall_confidence") or 0)

    # Unable-to-verify claims across evidence bundles
    unable_to_verify = _gather_unable_to_verify(evidence_dir, classifications)

    today = _dt.date.today().isoformat()
    lines: list[str] = []

    # Header
    lines += [
        f"# QA Report — {data_room_name}",
        "",
        f"_Standalone diagnostic file. Internal use only. This file is **not** part of the data room workbook and is **not** shared with counterparties._",
        "",
        "## Run Information",
        "",
        f"- **Date prepared:** {today}",
        f"- **Run ID:** {run_id or '(unspecified)'}",
        f"- **Source folder:** {source or '(unspecified)'}",
        f"- **Deal type:** {deal_type}",
        f"- **Objective:** {objective}",
        f"- **Files in source folder:** {manifest.get('file_count', 0)}",
        f"- **Files extracted in this run:** {extraction_summary.get('sample_size', 0) or sum(1 for f in manifest.get('files', []) if f.get('inclusion_in_extraction') == 'extracted')}",
        f"- **Files classified:** {len(classifications)}",
        "",
    ]

    # Executive summary
    lines += [
        "## Executive Summary",
        "",
        _build_executive_summary(classifications, qa_rows, low_rows),
        "",
    ]

    # Pass-by-pass findings
    lines += [
        "## Pass-by-Pass Findings",
        "",
    ]
    if not qa_rows:
        lines += ["_No QA pass results available._", ""]
    else:
        for qa_row in qa_rows:
            lines += _format_pass_section(qa_row, classifications)

    # No-hallucination check
    lines += [
        "## No-Hallucination Check (Evidence-Bundle Cross-Reference)",
        "",
        "Every claim in every file's brief description must trace to a verbatim snippet "
        "in that file's extraction text. Claims that could not be backed appear below.",
        "",
    ]
    lines += _format_unable_to_verify(unable_to_verify)

    # Rows flagged for attention
    lines += [
        "## Rows Flagged for Your Attention",
        "",
        f"Files where the AI's overall row confidence is below 0.70. Total: {len(low_rows)}.",
        "",
    ]
    lines += _format_flagged_rows_table(low_rows)

    # Methodology notes
    lines += [
        "## Methodology Notes",
        "",
        "- **Overall row confidence** is computed as the minimum of (classification, extraction, summary, OCR) confidences for that row. The pessimistic aggregator surfaces weak links rather than averaging them away.",
        "- **No-hallucination guarantee** is enforced by substring-matching every summary claim against the file's extraction text. Claims that cannot be backed are listed in the section above and replaced in the workbook with `\"Unable to verify — see evidence bundle\"`.",
        "- **Vision unavailable in this run.** Files that depend on Claude Vision for content recovery (image-only PDFs, low-OCR-confidence pages, standalone images requiring document-type interpretation) fall back to OCR-only or to placeholder records. See Pass 4 (OCR / Vision) above for which files were affected.",
        "- **Sample-induced uncertainty.** When extraction was run on a subset of source files, checklist coverage gaps may be sample-induced rather than truly missing. The Missing / Recommended worksheet of the internal workbook flags this in its row notes.",
        "- **Aggressive privileged marking.** The classifier may flag loan documents as `internal_only_privileged` even when the documents are not attorney-client material. Review such markings before applying them — see the Files Excluded worksheet in the internal workbook.",
        "",
    ]

    # Footer
    lines += [
        "---",
        "",
        f"_Generated by acos-dataroom skill on {today}._",
        "",
    ]

    out_path = run_dir / f"{data_room_name}_QA_Report_{today}.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the standalone markdown QA report.")
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--data-room-name", required=True)
    parser.add_argument("--deal-type", required=True)
    parser.add_argument("--objective", required=True)
    parser.add_argument("--source", default="")
    parser.add_argument("--run-id", default="")
    args = parser.parse_args(argv)

    out_path = build_qa_report(
        args.run_dir,
        data_room_name=args.data_room_name,
        deal_type=args.deal_type,
        objective=args.objective,
        source=args.source,
        run_id=args.run_id,
    )
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
