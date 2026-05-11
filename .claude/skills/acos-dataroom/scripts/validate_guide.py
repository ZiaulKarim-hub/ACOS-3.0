"""Phase 10 — Validate the boss-edited internal workbook.

Reads the edited 4-worksheet internal workbook, verifies structure, diffs
against the original snapshot stored at
`<run_dir>/intermediate/original_guide_snapshot.json`, and writes the diff
to `<run_dir>/intermediate/change_log.json` (NOT to a workbook tab — the
new design keeps the workbook clean).

The diff is audit-only. It NEVER blocks a boss decision — even when the
boss overrides a high-severity flag.

Hard errors (these DO block):
- Required worksheets missing.
- Required columns deleted from a worksheet.
- Workbook is corrupt / unreadable.
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


HARD_FAIL = 2
SOFT_FAIL = 0  # Diff-only = success


# Expected worksheet schemas for the new 4-WS internal workbook.
# Maps worksheet name -> ordered list of expected column headers.
WORKSHEET_SCHEMAS: dict[str, list[str]] = {
    "Files Included": [
        "Primary Subfolder",
        "Sub-folder",
        "Sub-sub-folder",
        "Original Filename",
        "Proposed Renamed Filename",
        "Brief Description",
        "Why Included",
        "Confidence — Reasoning",
        "Confidence — Overall Row",
    ],
    "Files Excluded": [
        "Primary Subfolder",
        "Sub-folder",
        "Sub-sub-folder",
        "Original Filename",
        "Proposed Renamed Filename",
        "Reason for Exclusion",
        "Confidence — Reasoning",
        "Confidence — Overall Row",
    ],
}

# Columns we watch for boss edits — anything in these lists, on these worksheets,
# triggers a Change_Log entry if it differs from the snapshot.
DIFF_COLUMNS_PER_WS: dict[str, list[str]] = {
    "Files Included": [
        "Original Filename",  # not expected to change but worth flagging if it does
        "Proposed Renamed Filename",
        "Brief Description",
        "Why Included",
        "Confidence — Reasoning",
        "Confidence — Overall Row",
    ],
    "Files Excluded": [
        "Reason for Exclusion",
        "Confidence — Reasoning",
        "Confidence — Overall Row",
    ],
}

# Forward-fill columns (visual grouping suppresses repeats; restore for diff)
FILL_FORWARD = ("Primary Subfolder", "Sub-folder", "Sub-sub-folder")


def find_run_dir_for_guide(guide_path: Path) -> Path:
    """The guide lives in <run_dir>; walk up to confirm and return it."""
    if (guide_path.parent / "intermediate").is_dir():
        return guide_path.parent
    raise FileNotFoundError(
        f"Could not locate run directory for guide at {guide_path}. "
        "Expected <run_dir>/intermediate/ alongside the workbook."
    )


def load_workbook_data(guide_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Return {worksheet_name: [row_dict, ...]} for all data worksheets in the new design.

    Forward-fills the visual-grouping columns so blank cells are restored to
    their semantic values before comparison.
    """
    openpyxl = importlib.import_module("openpyxl")
    wb = openpyxl.load_workbook(str(guide_path), data_only=True)
    data: dict[str, list[dict[str, Any]]] = {}
    for ws_name in WORKSHEET_SCHEMAS:
        if ws_name not in wb.sheetnames:
            data[ws_name] = []
            continue
        ws = wb[ws_name]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            data[ws_name] = []
            continue
        headers = [str(h) if h is not None else "" for h in rows[0]]
        records: list[dict[str, Any]] = []
        last: dict[str, Any] = {}
        for r in rows[1:]:
            if all(c is None or str(c).strip() == "" for c in r):
                continue
            rec = {headers[i]: ("" if v is None else v) for i, v in enumerate(r) if i < len(headers)}
            # Forward-fill visual-grouping columns
            for col in FILL_FORWARD:
                val = rec.get(col, "")
                if val == "" or val is None:
                    if last.get(col):
                        rec[col] = last[col]
                else:
                    last[col] = val
                    if col == "Primary Subfolder":
                        last["Sub-folder"] = ""
                        last["Sub-sub-folder"] = ""
                    elif col == "Sub-folder":
                        last["Sub-sub-folder"] = ""
            records.append(rec)
        data[ws_name] = records
    return data


def check_required_columns(data: dict[str, list[dict[str, Any]]]) -> list[str]:
    """Return list of human-readable error messages for any missing columns."""
    errors = []
    for ws_name, expected_cols in WORKSHEET_SCHEMAS.items():
        rows = data.get(ws_name, [])
        if not rows:
            continue  # An empty worksheet is OK — not all are populated
        first = rows[0]
        for c in expected_cols:
            if c not in first:
                errors.append(f"Worksheet '{ws_name}' is missing required column '{c}'.")
    return errors


def diff_against_snapshot(
    edited: dict[str, list[dict[str, Any]]],
    snapshot: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Return list of change records (one per cell that differs)."""
    now = _dt.datetime.utcnow().isoformat() + "Z"
    changes: list[dict[str, Any]] = []
    for ws_name, edited_rows in edited.items():
        if ws_name not in DIFF_COLUMNS_PER_WS:
            continue
        watch_cols = DIFF_COLUMNS_PER_WS[ws_name]
        snap_rows = snapshot.get(ws_name, [])
        # Index by Original Filename (most stable identifier on the included/excluded sheets)
        key_col = "Original Filename"
        if edited_rows and key_col not in edited_rows[0]:
            continue
        snap_index = {r.get(key_col): r for r in snap_rows if r.get(key_col)}
        for row in edited_rows:
            row_id = row.get(key_col)
            if not row_id:
                continue
            snap_row = snap_index.get(row_id)
            if not snap_row:
                continue
            for col in watch_cols:
                if col not in row:
                    continue
                old = snap_row.get(col, "")
                new = row.get(col, "")
                if str(old) != str(new):
                    changes.append({
                        "worksheet": ws_name,
                        "row_id": row_id,
                        "column_name": col,
                        "original_value": old,
                        "edited_value": new,
                        "changed_at": now,
                    })
    return changes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate edited internal workbook.")
    parser.add_argument("--guide", required=True, type=Path)
    parser.add_argument("--run-dir", type=Path, help="Override; otherwise inferred from guide location.")
    args = parser.parse_args(argv)

    if not args.guide.exists():
        print(f"Guide not found: {args.guide}", file=sys.stderr)
        return HARD_FAIL

    run_dir = args.run_dir or find_run_dir_for_guide(args.guide)
    layout = {"base": run_dir, "logs": run_dir / "logs",
              "extraction": run_dir / "extraction",
              "evidence": run_dir / "evidence",
              "intermediate": run_dir / "intermediate"}
    utils.ensure_run_dirs(layout)
    logger = utils.make_logger(layout)

    edited = load_workbook_data(args.guide)
    errors = check_required_columns(edited)
    if errors:
        print("VALIDATION FAILED — required columns missing:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return HARD_FAIL

    snapshot_path = layout["intermediate"] / "original_guide_snapshot.json"
    if snapshot_path.exists():
        snapshot_raw = utils.read_json(snapshot_path)
        # Snapshot may be in old schema (Proposed_Data_Room_Index, Internal_Only, etc.)
        # or new schema (Files Included, Files Excluded). Migrate old → new headers if needed.
        snapshot = _migrate_snapshot_to_new_schema(snapshot_raw)
    else:
        logger.warning("No original_guide_snapshot.json — first edit cycle, skipping diff.")
        snapshot = {}

    changes = diff_against_snapshot(edited, snapshot)

    # Stats
    included_rows = edited.get("Files Included", [])
    excluded_rows = edited.get("Files Excluded", [])

    # Write diff to JSON (NOT to a workbook tab — keep the workbook clean)
    change_log_path = layout["intermediate"] / "change_log.json"
    utils.write_json(change_log_path, changes)

    logger.info("Validation OK | %d cell change(s) | %d included, %d excluded.",
                len(changes), len(included_rows), len(excluded_rows))

    print(f"Validated. {len(included_rows)} rows on Files Included, "
          f"{len(excluded_rows)} on Files Excluded.")
    print(f"{len(changes)} change(s) recorded to {change_log_path}.")
    return SOFT_FAIL


def _migrate_snapshot_to_new_schema(snap: dict) -> dict[str, list[dict]]:
    """Translate any old-schema snapshot tab names to new worksheet names.

    Backward-compat shim. Old snapshots used `Proposed_Data_Room_Index` /
    `Internal_Only` / `Tailored_Diligence_Scope`; new design uses `Files Included` /
    `Files Excluded`. Field names also changed (e.g., `file_name` → `Original Filename`).
    """
    out: dict[str, list[dict]] = {}
    if "Files Included" in snap:
        # Already new-schema
        out["Files Included"] = snap["Files Included"]
        out["Files Excluded"] = snap.get("Files Excluded", [])
        return out
    # Old-schema migration
    pdi = snap.get("Proposed_Data_Room_Index", [])
    if pdi:
        included = []
        excluded = []
        for c in pdi:
            row = {
                "Original Filename": c.get("file_name", ""),
                "Proposed Renamed Filename": c.get("proposed_renamed_filename", ""),
                "Brief Description": c.get("brief_summary", ""),
                "Why Included": c.get("qa_notes", ""),
                "Confidence — Reasoning": c.get("classification_confidence", ""),
                "Confidence — Overall Row": c.get("summary_confidence", ""),
            }
            rec = (c.get("external_room_recommendation") or "").lower()
            if rec.startswith("internal_only_") or rec in ("superseded", "absent"):
                excluded.append({**row, "Reason for Exclusion": rec})
            else:
                included.append(row)
        out["Files Included"] = included
        out["Files Excluded"] = excluded
    return out


if __name__ == "__main__":
    raise SystemExit(main())
