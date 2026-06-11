#!/usr/bin/env python3
"""
record-image-feedback.py — persist user image rejection to the brand manifest.

Usage:
    record-image-feedback.py --session-id <id> --page <N> [--reason <text>]
    record-image-feedback.py --list [--manifest <path>]
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: pyyaml required\n")
    sys.exit(1)


def find_session(session_id: str) -> Path:
    base = Path(".acos/ultimate-designer/sessions") / session_id
    if not base.exists():
        raise SystemExit(f"ERROR: session not found: {base}")
    return base


def find_manifest_from_session(session_dir: Path) -> Path | None:
    manifest_yaml = session_dir / "manifest.yaml"
    if not manifest_yaml.exists():
        return None
    m = yaml.safe_load(manifest_yaml.read_text()) or {}
    asset_dir = m.get("inputs", {}).get("asset_dir")
    if not asset_dir:
        return None
    return Path(asset_dir) / ".acos-ultimate-designer-manifest.yaml"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--session-id")
    ap.add_argument("--page", type=int)
    ap.add_argument("--reason", default="user rejection, no reason given")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--manifest")
    args = ap.parse_args()

    if args.list:
        mf_path = Path(args.manifest) if args.manifest else None
        if not mf_path or not mf_path.exists():
            sys.stderr.write("ERROR: --manifest required and must exist for --list\n")
            return 1
        mf = yaml.safe_load(mf_path.read_text()) or {}
        for h, e in (mf.get("entries") or {}).items():
            rejects = e.get("user_rejected_for") or []
            if rejects:
                print(f"{e.get('filename')} ({h[:12]}):")
                for r in rejects:
                    print(f"  - {r.get('context')} | {r.get('reason')} | {r.get('timestamp')}")
        return 0

    if not args.session_id or not args.page:
        sys.stderr.write("ERROR: --session-id and --page required\n")
        return 1

    session_dir = find_session(args.session_id)
    res_log = session_dir / "image-resolution.log"
    if not res_log.exists():
        sys.stderr.write(f"ERROR: no image-resolution.log in session {args.session_id}\n")
        return 1
    resolutions = (yaml.safe_load(res_log.read_text()) or {}).get("resolutions", [])
    row = next((r for r in resolutions if str(r.get("page")) == str(args.page)), None)
    if not row:
        sys.stderr.write(f"ERROR: no resolution found for page {args.page}\n")
        return 1

    resolution = row.get("resolution") or {}
    file_hash = resolution.get("file_hash")
    if not file_hash:
        sys.stderr.write("ERROR: page image came from fallback (not brand manifest); no entry to mark\n")
        return 1

    mf_path = find_manifest_from_session(session_dir)
    if not mf_path or not mf_path.exists():
        sys.stderr.write("ERROR: brand manifest not found\n")
        return 1
    mf = yaml.safe_load(mf_path.read_text()) or {"version": 1, "entries": {}}
    entry = mf["entries"].get(file_hash)
    if not entry:
        sys.stderr.write(f"ERROR: hash {file_hash[:12]} not in manifest\n")
        return 1

    doc_type = (yaml.safe_load((session_dir / "manifest.yaml").read_text()) or {}).get("inputs", {}).get("doc_type") or "document"
    context = f"page {args.page} of {doc_type}"

    entry.setdefault("user_rejected_for", []).append({
        "context": context,
        "reason": args.reason,
        "timestamp": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session_id": args.session_id,
    })

    tmp = mf_path.with_suffix(mf_path.suffix + ".tmp")
    tmp.write_text(yaml.safe_dump(mf, sort_keys=False, allow_unicode=True), encoding="utf-8")
    tmp.replace(mf_path)

    print(f"Recorded feedback: {entry.get('filename')} will not be used for contexts similar to '{context}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
