#!/usr/bin/env python3
"""
emit-pptx-content.py — page-plan → PPTX content YAML.

Translates a page-plan (shared with HTML path) into a YAML conforming to
data-to-pptx.py's expected schema. Per-slide: layout_name + shape_content_dict
+ resolved image paths (from image-resolution.log).

Usage:
    emit-pptx-content.py --page-plan <path> --image-log <path> --output <path>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: pyyaml required\n")
    sys.exit(1)


LAYOUT_MAP = {
    "cover": "cover_layout",
    "two-column-narrative": "two_column_narrative_layout",
    "metric-grid": "metric_grid_layout",
    "timeline": "timeline_layout",
    "chapter-divider": "chapter_divider_layout",
    "product-detail": "product_detail_layout",
    "portfolio-grid": "portfolio_grid_layout",
    "photo-break": "photo_break_layout",
    "closing": "closing_layout",
}


def build_image_index(image_log_path: Path) -> dict:
    """Map page -> {slot_id -> image_path}."""
    if not image_log_path.exists():
        return {}
    data = yaml.safe_load(image_log_path.read_text()) or {}
    idx: dict = {}
    for r in data.get("resolutions") or []:
        page = str(r.get("page"))
        slot_id = r.get("slot_id")
        resolution = r.get("resolution") or {}
        local = resolution.get("local_path") or resolution.get("file_path")
        if local:
            idx.setdefault(page, {})[slot_id] = local
    return idx


def build_slide_spec(page: dict, page_num: int, images_for_page: dict) -> dict:
    template_id = page["template_id"]
    layout = LAYOUT_MAP.get(template_id, "two_column_narrative_layout")
    content = page.get("content") or {}

    shape = {
        "eyebrow": page.get("eyebrow", ""),
        "title_lead": page.get("title_lead", ""),
        "italic_accent_phrase": page.get("italic_accent_phrase", ""),
        "page_number_roman": page.get("page_number_roman", ""),
        "total_pages_roman": page.get("total_pages_roman", ""),
        "running_header_left": page.get("running_header_left", ""),
        "running_header_right": page.get("running_header_right", ""),
    }
    for k, v in content.items():
        shape[k] = v

    # Resolve image paths per slot. Pass through ALL images the fill-photo-slots
    # step actually placed on this page, not just those declared in the page-plan's
    # photo_slots list. The decomposer declares one nominal slot per page even for
    # portfolio-grid (which has 4 card slots at emit time), so filtering by the
    # page-plan photo_slots drops the card images.
    return {
        "slide_number": page_num,
        "layout_name": layout,
        "shape_content": shape,
        "images": dict(images_for_page),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--page-plan", required=True)
    ap.add_argument("--image-log", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    plan = yaml.safe_load(Path(args.page_plan).read_text()) or {}
    images = build_image_index(Path(args.image_log))

    slides = []
    for i, page in enumerate(plan.get("pages") or [], start=1):
        slides.append(build_slide_spec(page, i, images.get(str(i), {})))

    out = {
        "metadata": plan.get("metadata", {}),
        "slides": slides,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(yaml.safe_dump(out, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"Wrote {len(slides)} slide specs to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
