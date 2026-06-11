#!/usr/bin/env python3
"""
fill-photo-slots.py — substitute every data-photo-slot placeholder in HTML.

Iterates every element with `data-photo-slot`, calls match-image.py (if a
brand manifest exists) then fetch-image-fallback.py, writes updated HTML +
image-resolution.log + ATTRIBUTION.md.

Usage:
    fill-photo-slots.py --html <input.html>
                         --session-dir <dir>
                         --output <output.html>
                         [--manifest <brand-manifest.yaml>]
                         [--threshold 0.6]
                         [--verbose]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.stderr.write("ERROR: beautifulsoup4 required\n")
    sys.exit(1)


SKILL_ROOT = Path(__file__).resolve().parent.parent


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_image", SKILL_ROOT / "scripts" / "validate-image.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.is_valid_image


is_valid_image = _load_validator()


def path_to_file_uri(p: Path) -> str:
    return "file://" + quote(str(p.resolve()), safe="/:")


def call_matcher(slot: dict, manifest_path: Path, threshold: float, verbose: bool) -> dict:
    cmd = ["python3", str(SKILL_ROOT / "scripts" / "match-image.py"),
           "--slot", json.dumps(slot),
           "--manifest", str(manifest_path),
           "--threshold", str(threshold)]
    if verbose:
        cmd.append("--verbose")
    out = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if out.returncode != 0 or not out.stdout.strip():
        return {"action": "fallback", "query": " ".join(slot.get("semantic_tags", []))}
    try:
        result = json.loads(out.stdout.strip().splitlines()[-1])
    except json.JSONDecodeError:
        return {"action": "fallback", "query": " ".join(slot.get("semantic_tags", []))}
    # match-image returns brand hits keyed as "file_path"; the downstream slot-
    # filling code and the fetcher fallback both use "local_path". Normalize so
    # brand and fetcher results flow through the same path-handling branch.
    if result.get("source") == "brand" and result.get("file_path") and not result.get("local_path"):
        result["local_path"] = result["file_path"]
    return result


def call_fetcher(query: str, cache_dir: Path, verbose: bool) -> dict:
    cmd = ["python3", str(SKILL_ROOT / "scripts" / "fetch-image-fallback.py"),
           "--query", query, "--cache-dir", str(cache_dir)]
    if verbose:
        cmd.append("--verbose")
    out = subprocess.run(cmd, capture_output=True, text=True, check=False)
    try:
        return json.loads(out.stdout.strip().splitlines()[-1]) if out.stdout.strip() else {"action": "empty_slot"}
    except json.JSONDecodeError:
        return {"action": "empty_slot"}


def apply_image_to_element(el, image_url: str) -> None:
    """Set background-image on element. Preserves existing styles."""
    existing = el.get("style", "") or ""
    bg_rule = f"background-image: url({image_url});"
    # Replace existing background-image if present
    if "background-image" in existing:
        import re as _re
        existing = _re.sub(r"background-image\s*:\s*[^;]+;?", "", existing)
    sep = "" if existing.rstrip().endswith(";") or not existing.strip() else ";"
    el["style"] = existing + sep + " " + bg_rule
    # Ensure background sizing set
    if "background-size" not in el["style"]:
        el["style"] += " background-size: cover; background-position: center;"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--html", required=True)
    ap.add_argument("--session-dir", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--manifest")
    ap.add_argument("--threshold", type=float, default=0.6)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    html_path = Path(args.html)
    session_dir = Path(args.session_dir)
    out_path = Path(args.output)
    cache_dir = session_dir / "images"
    cache_dir.mkdir(parents=True, exist_ok=True)

    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")

    slots = soup.find_all(attrs={"data-photo-slot": True})
    print(f"Found {len(slots)} photo slots", file=sys.stderr)

    resolution_log: list[dict] = []
    attributions: list[dict] = []

    manifest_path = Path(args.manifest) if args.manifest else None

    for idx, el in enumerate(slots, 1):
        tags = [t.strip() for t in (el.get("data-photo-slot") or "").split(",") if t.strip()]
        slot_id = el.get("data-slot-id") or f"slot_{idx}"
        page_el = el.find_parent(attrs={"data-template": True})
        # Defensive default: if the page wrapper lacks data-page-number, fall
        # back to the slot's structural index rather than None. None breaks
        # emit-pptx-content.build_image_index which keys on page.
        page_n = (page_el.get("data-page-number") if page_el else None) or idx
        tmpl = page_el.get("data-template") if page_el else "unknown"

        slot = {
            "slot_id": slot_id,
            "semantic_tags": tags,
            "content_context": f"page {page_n} ({tmpl})",
            "page_number": page_n,
        }

        resolved = None
        if manifest_path and manifest_path.exists():
            resolved = call_matcher(slot, manifest_path, args.threshold, args.verbose)

        if not resolved or resolved.get("action") == "fallback":
            query = (resolved or {}).get("query") or " ".join(tags) or "architecture"
            resolved = call_fetcher(query, cache_dir, args.verbose)

        if resolved and resolved.get("local_path"):
            resolved_path = Path(resolved["local_path"])
            valid, reason, _kind = is_valid_image(resolved_path)
            if not valid and resolved_path.suffix.lower() != ".heic":
                print(f"  [warn] slot {slot_id} resolved to non-image {resolved_path}: {reason} — treating as empty slot",
                      file=sys.stderr)
                resolved = {"action": "empty_slot", "reason": f"validate-image rejected: {reason}"}

        if resolved and resolved.get("local_path"):
            uri = path_to_file_uri(Path(resolved["local_path"]))
            apply_image_to_element(el, uri)
            attributions.append({
                "slot_id": slot_id, "page": page_n,
                "source": resolved.get("source", "brand"),
                "photographer": resolved.get("photographer", "OKOA Capital"),
                "photographer_url": resolved.get("photographer_url", ""),
                "filename": Path(resolved["local_path"]).name,
                "attribution_string": resolved.get("attribution_string") or ("OKOA Capital brand asset"),
            })
        else:
            # Empty slot placeholder
            el["class"] = (el.get("class") or []) + ["photo-slot-empty"]
            attributions.append({"slot_id": slot_id, "page": page_n, "source": "empty", "attribution_string": "IMAGE MISSING"})

        resolution_log.append({
            "slot_id": slot_id, "page": page_n, "template": tmpl,
            "tags": tags,
            "resolution": resolved or {"action": "empty_slot"},
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(str(soup), encoding="utf-8")

    import yaml
    (session_dir / "image-resolution.log").write_text(
        yaml.safe_dump({"resolutions": resolution_log}, sort_keys=False), encoding="utf-8")

    attr_md = ["# Attribution\n",
               "| Asset | Source | Photographer | Used On |",
               "|---|---|---|---|"]
    for a in attributions:
        attr_md.append(f"| {a.get('filename', a['slot_id'])} | {a['source']} | {a.get('photographer','')} | page {a['page']} ({a['slot_id']}) |")
    attr_md.append("\n## Credits\n")
    for a in attributions:
        if a["source"] != "empty":
            attr_md.append(f"- {a['attribution_string']}")
    (session_dir / "ATTRIBUTION.md").write_text("\n".join(attr_md) + "\n", encoding="utf-8")

    print(f"Wrote filled HTML to {out_path}; {len([a for a in attributions if a['source'] != 'empty'])}/{len(slots)} slots resolved", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
