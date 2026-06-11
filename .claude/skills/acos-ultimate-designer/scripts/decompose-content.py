#!/usr/bin/env python3
"""
decompose-content.py — content → page plan

Takes user-supplied content (YAML or markdown with YAML front-matter) and produces
a page-plan: ordered list of page specs with {template_id, content, photo_slots,
italic_accent_phrase}. Applies coffee-table composition heuristics.

Usage:
    decompose-content.py <input.yaml|input.md> <output-plan.yaml>
                         [--fix-context <fix-instructions.yaml>]
                         [--dry-run] [--verbose]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: pyyaml required. pip install pyyaml\n")
    sys.exit(1)


def roman(n: int) -> str:
    vals = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    out = ""
    for v, s in zip(vals, syms):
        while n >= v:
            out += s
            n -= v
    return out


def extract_italic_accent(title: str) -> tuple[str, str]:
    """Split title into (lead_words, italic_accent_phrase). Picks the last 1-2 meaningful
    words that carry noun weight. Examples:
      "Flexible Capital" → ("Flexible", "Capital")
      "Our Debt Solutions" → ("Our Debt", "Solutions")
      "First dollar" → ("", "First dollar")  (short titles: italicize whole)
    """
    words = title.strip().rstrip(".").split()
    if not words:
        return ("", "")
    if len(words) <= 2:
        return ("", " ".join(words))
    return (" ".join(words[:-1]), words[-1])


def load_content(path: Path) -> dict:
    """Load YAML or markdown-with-frontmatter. Returns dict."""
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        return yaml.safe_load(text) or {}

    # Markdown with front-matter
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        data = yaml.safe_load(fm) or {}
        data["_body_markdown"] = body.strip()
        return data
    return {"title": path.stem, "_body_markdown": text.strip()}


def classify_section(section: dict) -> str:
    """Heuristic: {metrics} → metric-grid; {steps: [...]} → timeline;
    {items: [{name, description}]} → product-detail; {portfolio: [...]} → portfolio-grid;
    default → two-column-narrative."""
    if isinstance(section, dict):
        if "metrics" in section and isinstance(section["metrics"], list):
            return "metric-grid"
        if "steps" in section and isinstance(section["steps"], list):
            return "timeline"
        if "portfolio" in section and isinstance(section["portfolio"], list):
            return "portfolio-grid"
        if "items" in section and isinstance(section["items"], list):
            if any(isinstance(it, dict) and "name" in it and "description" in it for it in section["items"]):
                return "product-detail"
    return "two-column-narrative"


def build_page_spec(template_id: str, section: dict, section_name: str, page_n: int) -> dict:
    title = section.get("title", section_name) if isinstance(section, dict) else section_name
    lead, accent = extract_italic_accent(title)
    eyebrow = f"{page_n:02d} {section_name.upper()}"
    spec = {
        "template_id": template_id,
        "eyebrow": eyebrow,
        "title_lead": lead,
        "italic_accent_phrase": accent,
        "content": section if isinstance(section, dict) else {"body": str(section)},
        "photo_slots": [],
    }
    if template_id in ("cover", "chapter-divider", "photo-break", "portfolio-grid"):
        spec["photo_slots"] = [{"slot_id": "image_1", "semantic_tags": ["architectural", "landscape"]}]
    return spec


def build_plan(content: dict, fix_context: dict | None = None) -> list[dict]:
    pages: list[dict] = []

    # 1. Cover
    title = content.get("title", "Untitled")
    lead, accent = extract_italic_accent(title)
    pages.append({
        "template_id": "cover",
        "eyebrow": (content.get("eyebrow") or "OKOA CAPITAL").upper(),
        "title_lead": lead, "italic_accent_phrase": accent,
        "content": {
            "subtitle": content.get("subtitle", ""),
            "metadata_label": content.get("metadata_label", "DOCUMENT"),
            "metadata_value": content.get("metadata_value", ""),
        },
        "photo_slots": [{"slot_id": "cover_image", "semantic_tags": ["hero", "architectural", "landscape"]}],
    })

    # 2. Parts/sections
    parts = content.get("parts") or [{"sections": content.get("sections", [])}]
    content_pages_since_photo = 0
    last_section_for_caption: dict | None = None
    for part_idx, part in enumerate(parts):
        if len(parts) > 1:
            ptitle = part.get("title", f"Part {part_idx + 1}")
            plead, paccent = extract_italic_accent(ptitle)
            pages.append({
                "template_id": "chapter-divider",
                "eyebrow": f"PART {roman(part_idx + 1)}",
                "title_lead": plead, "italic_accent_phrase": paccent,
                "content": {"subtitle": part.get("subtitle", "")},
                "photo_slots": [{"slot_id": "divider_image", "semantic_tags": ["atmospheric", "architectural"]}],
            })

        for section in part.get("sections", []):
            tmpl = classify_section(section)
            section_name = section.get("name", section.get("title", "Section")) if isinstance(section, dict) else "Section"
            pages.append(build_page_spec(tmpl, section, section_name, len(pages) + 1))
            if isinstance(section, dict):
                last_section_for_caption = section
            content_pages_since_photo += 1
            if content_pages_since_photo >= 3:
                pages.append({
                    "template_id": "photo-break",
                    "eyebrow": "",
                    "title_lead": "", "italic_accent_phrase": "",
                    "content": {
                        "caption_label": section.get("photo_caption_label", "PORTFOLIO") if isinstance(section, dict) else "PORTFOLIO",
                        "caption_location": section.get("photo_caption_location", "") if isinstance(section, dict) else "",
                    },
                    "photo_slots": [{"slot_id": "band_image", "semantic_tags": ["atmospheric", "landscape", "full-bleed"]}],
                })
                content_pages_since_photo = 0

    # 2b. Terminal flush: if the pipeline ended with 1-2 content pages since the last
    # photo-break, emit a final photo-break so the ct-01 rhythm rule (ceil(n/3)) is
    # always satisfied and the closing page is preceded by the coffee-table photo
    # transition, not a text page.
    if content_pages_since_photo > 0:
        cap = last_section_for_caption or {}
        pages.append({
            "template_id": "photo-break",
            "eyebrow": "",
            "title_lead": "", "italic_accent_phrase": "",
            "content": {
                "caption_label": cap.get("photo_caption_label", "PORTFOLIO"),
                "caption_location": cap.get("photo_caption_location", ""),
            },
            "photo_slots": [{"slot_id": "band_image", "semantic_tags": ["atmospheric", "landscape", "full-bleed"]}],
        })

    # 3. Closing
    closing = content.get("closing", {})
    ctitle = closing.get("title", "Ready When You Are")
    clead, caccent = extract_italic_accent(ctitle)
    pages.append({
        "template_id": "closing",
        "eyebrow": f"{len(pages) + 1:02d} CLOSING",
        "title_lead": clead, "italic_accent_phrase": caccent,
        "content": {
            "summary_col_1": closing.get("summary_col_1", ""),
            "summary_col_2": closing.get("summary_col_2", ""),
            "panel_title": closing.get("panel_title", ""),
            "panel_body": closing.get("panel_body", ""),
            "footer_text": closing.get("footer_text", "okoacapital.com"),
        },
        "photo_slots": [],
    })

    # 4. Populate page numbers + running header/footer
    total = len(pages)
    for i, p in enumerate(pages, start=1):
        p["page_number"] = i
        p["page_number_roman"] = roman(i)
        p["total_pages_roman"] = roman(total)
        p["running_header_left"] = content.get("running_header_left", title.upper())
        p["running_header_right"] = content.get("running_header_right", "OKOA CAPITAL")

    # 5. Apply fix-context if present (Wigum re-entry)
    if fix_context:
        for fix in fix_context.get("fixes", []):
            target_page = fix.get("page")
            if target_page and 1 <= target_page <= len(pages):
                page = pages[target_page - 1]
                if fix.get("action") == "insert_photo_break_after":
                    pages.insert(target_page, {
                        "template_id": "photo-break",
                        "eyebrow": "", "title_lead": "", "italic_accent_phrase": "",
                        "content": {"caption_label": "INSERTED", "caption_location": ""},
                        "photo_slots": [{"slot_id": f"band_image_fix_{target_page}", "semantic_tags": ["landscape", "atmospheric"]}],
                    })
                elif fix.get("action") == "set_italic_accent":
                    page["italic_accent_phrase"] = fix.get("value", page["italic_accent_phrase"])
                elif fix.get("action") == "set_template":
                    page["template_id"] = fix.get("value", page["template_id"])

    return pages


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--fix-context")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        sys.stderr.write(f"ERROR: input not found: {in_path}\n")
        return 1

    content = load_content(in_path)
    fix_context = yaml.safe_load(Path(args.fix_context).read_text()) if args.fix_context and Path(args.fix_context).exists() else None

    plan = build_plan(content, fix_context)
    metadata = {
        "title": content.get("title", "Untitled"),
        "source_content": str(in_path),
        "page_count": len(plan),
    }
    output = {"metadata": metadata, "pages": plan}

    if args.verbose:
        for i, p in enumerate(plan, 1):
            sys.stderr.write(f"  page {i:>2}: {p['template_id']:<22} | {p.get('eyebrow','')[:40]}\n")

    if args.dry_run:
        print(yaml.safe_dump(output, sort_keys=False, allow_unicode=True))
        return 0

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml.safe_dump(output, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"Wrote {len(plan)} pages to {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
