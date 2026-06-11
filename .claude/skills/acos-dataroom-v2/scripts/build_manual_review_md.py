"""Generate Manual_Review_Required_<date>.md from acos-dataroom-v2 run state.

Aggregates the manual-review buckets the v2.1 phases actually emit and emits a
single operator-facing markdown listing files that need follow-up:
  - Unable to evaluate — non-extractable files (encrypted / zero-byte / unsupported /
    out-of-scope), derived from intermediate/file_manifest.json
    (inclusion_in_extraction != "extracted")
  - Phase 3 QA-failed unconverged (phase3/qa_failed_unconverged.csv — §7.2 K-exhaustion)
  - Phase 4b pending classification — split-after-K files that land in
    dataroom/00_Pending_Classification/ (directory listing, per §8.2/§10.4)
  - Phase 2.5 privilege-removed (informational — these are CORRECTLY removed)

Buckets the v2.1 phases never emit are intentionally NOT read:
  - phase2/disputed/ — Phase 2 is asymmetric single-pass, no re-dispatch (§5.6)
  - phase5/qa_failed_unconverged.csv — Phase 5 K-exhaustion surfaces via
    00_Pending_Classification/ instead

Only writes the file if at least one bucket is non-empty. If all empty, prints
"NO_MANUAL_REVIEW_NEEDED" to stdout and writes nothing.

CLI usage:
  python3 build_manual_review_md.py --run-dir <RUN_DIR> --output <PATH>
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any


def _read_csv_safe(p: Path) -> list[dict[str, str]]:
    if not p.exists():
        return []
    rows = []
    try:
        with p.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)
    except Exception:
        pass
    return rows


def _list_dir_files(d: Path) -> list[dict[str, str]]:
    """List regular files directly under a directory as bucket records.

    Used for dataroom/00_Pending_Classification/, where Phase 4b split-after-K
    placement files actually land (per §8.2/§10.4). Returns [] if absent.
    """
    if not d.exists() or not d.is_dir():
        return []
    out: list[dict[str, str]] = []
    for fp in sorted(d.iterdir()):
        if fp.is_file():
            out.append({
                "filename": fp.name,
                "reason": "Placement unanimity failed after K=5 — needs manual sub-folder assignment",
                "source_path": str(fp),
            })
    return out


def _unable_to_evaluate_from_manifest(run_dir: Path) -> list[dict[str, str]]:
    """Derive the non-extractable / non-evaluable set from the file manifest.

    No phase writes intermediate/unable_to_evaluate.csv; non-extractable files are
    tracked in intermediate/file_manifest.json via the per-file
    `inclusion_in_extraction` field (written by scan_folder.py). Any value other
    than "extracted" (e.g. encrypted, zero_byte, unsupported_extension,
    out_of_scope_*, system_excluded, user_excluded, inaccessible) means the file
    could not be evaluated by the deliberation swarm. Returns [] if absent.
    """
    manifest_path = run_dir / "intermediate" / "file_manifest.json"
    if not manifest_path.exists():
        return []
    try:
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception:
        return []
    out: list[dict[str, str]] = []
    for rec in manifest.get("files", []):
        if not isinstance(rec, dict):
            continue
        status = rec.get("inclusion_in_extraction", "")
        if status and status != "extracted":
            out.append({
                "filename": rec.get("file_name", "?"),
                "reason": rec.get("notes") or status,
                "source_path": rec.get("source_path", ""),
            })
    return out


def gather_buckets(run_dir: Path) -> dict[str, list[Any]]:
    return {
        # Non-extractable files derived from the manifest (no CSV is ever written).
        "unable_to_evaluate": _unable_to_evaluate_from_manifest(run_dir),
        "phase2_5_privileged_removed": _read_csv_safe(run_dir / "phase2_5" / "privileged_removed.csv"),
        "phase3_unconverged": _read_csv_safe(run_dir / "phase3" / "qa_failed_unconverged.csv"),
        # Split-after-K placement files land here as actual files (§8.2/§10.4).
        "phase4_pending": _list_dir_files(run_dir / "dataroom" / "00_Pending_Classification"),
    }


def build_markdown(run_dir: Path, output: Path) -> Path | None:
    buckets = gather_buckets(run_dir)
    total = sum(len(v) for v in buckets.values())
    # Exclude privilege-removed from "needs review" total since those are correctly removed
    actionable = total - len(buckets["phase2_5_privileged_removed"])

    if actionable == 0 and len(buckets["phase2_5_privileged_removed"]) == 0:
        return None

    lines = []
    today = _dt.date.today().isoformat()
    lines.append(f"# Manual Review Required — {today}")
    lines.append("")
    lines.append(f"**Run directory:** `{run_dir}`")
    lines.append("")
    lines.append(
        "This file is generated by acos-dataroom-v2 when one or more buckets need "
        "operator (Zee) follow-up. **Not a buyer-facing artifact** — do not include "
        "in the data room shipped to the counterparty."
    )
    lines.append("")
    lines.append(f"**Total files needing action:** {actionable}")
    lines.append(f"**Files correctly removed (privilege):** {len(buckets['phase2_5_privileged_removed'])} (informational only)")
    lines.append("")

    sections = [
        ("unable_to_evaluate", "Files that could not be evaluated (encrypted / zero-byte / unsupported / out-of-scope)",
         "These files were pre-bucketed by scan_folder.py before reaching the deliberation "
         "swarm and are tracked in intermediate/file_manifest.json "
         "(inclusion_in_extraction != \"extracted\"). Encrypted PDFs need a password to "
         "extract; zero-byte files are empty; unsupported extensions have no extraction "
         "recipe; out-of-scope archives/emails are skipped in v1. Action: open each "
         "manually, decide whether it belongs in the dataroom, and either redact + re-add "
         "or exclude."),
        ("phase3_unconverged", "Files that failed Phase 3 QA after K=5 iterations",
         "The QA Wigum loop could not stabilize on these files. They were excluded from the "
         "final dataroom. Action: review each manually to decide inclusion."),
        ("phase4_pending", "Files placed in 00_Pending_Classification/ (Phase 4b unanimity failed)",
         "The 3 placement agents disagreed on sub-folder after 5 re-dispatches. Files are "
         "in dataroom/00_Pending_Classification/. Action: manually move each into the "
         "appropriate numbered sub-folder."),
        ("phase2_5_privileged_removed", "Files removed by Phase 2.5 privilege scanner (informational)",
         "These files were FLAGGED for privilege by at least one scanner and removed under "
         "the asymmetric-consensus rule. They are NOT in the dataroom. Action (optional): "
         "review each scanner's reasoning if you disagree with the removal."),
    ]

    for key, heading, description in sections:
        items = buckets[key]
        if not items:
            continue
        lines.append(f"## {heading}")
        lines.append("")
        lines.append(description)
        lines.append("")
        lines.append("| Filename | Reason / Notes | Source path |")
        lines.append("|---|---|---|")
        for item in items:
            if isinstance(item, dict):
                fn = item.get("filename") or item.get("file") or item.get("file_id", "?")
                reason = item.get("reason") or item.get("notes") or item.get("triggered_markers") or ""
                src = item.get("source_path") or item.get("path", "")
                if isinstance(reason, list):
                    reason = "; ".join(str(x) for x in reason)
                lines.append(f"| `{fn}` | {reason} | `{src}` |")
            else:
                lines.append(f"| (unparseable record) | — | — |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*acos-dataroom-v2 Manual Review Required — operator follow-up only. Not for buyer.*")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build acos-dataroom-v2 manual-review markdown.")
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)

    if not args.run_dir.is_dir():
        print(f"ERROR: run-dir not found: {args.run_dir}", file=sys.stderr)
        return 2

    out = build_markdown(args.run_dir, args.output)
    if out is None:
        print("NO_MANUAL_REVIEW_NEEDED")
    else:
        print(str(out))
    return 0


if __name__ == "__main__":
    sys.exit(cli_main())
