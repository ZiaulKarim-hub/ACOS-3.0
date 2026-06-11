#!/usr/bin/env python3
"""
html-emit.py — page-plan + tokens.css + templates → single-file HTML

Usage:
    html-emit.py <page-plan.yaml> <output.html>
                 --tokens <tokens.css>
                 --templates <page-templates-dir>
"""
from __future__ import annotations

import argparse
import html as html_escape
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: pyyaml required\n")
    sys.exit(1)


GOOGLE_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500;1,600&'
    'family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700&'
    'family=IBM+Plex+Mono:wght@400;500;600&display=swap">'
)


PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def esc(v) -> str:
    if v is None:
        return ""
    return html_escape.escape(str(v), quote=True)


def render_metrics_block(metrics: list) -> str:
    parts = []
    for m in metrics[:9]:
        parts.append(
            f'<div class="card" style="background-color: var(--white); padding: 20px; border-top: 3px solid var(--coral);">'
            f'<div class="mono-label" style="color: var(--coral); background-color: var(--white);">{esc(m.get("label",""))}</div>'
            f'<div class="display-data" style="color: var(--ink); background-color: var(--white); margin-top: 12px;">{esc(m.get("value",""))}</div>'
            f'<div class="body-card-sm" style="color: var(--ink-60); background-color: var(--white); margin-top: 8px;">{esc(m.get("description",""))}</div>'
            f"</div>"
        )
    return "\n".join(parts)


def render_steps_block(steps: list) -> str:
    parts = []
    for s in steps[:5]:
        parts.append(
            f'<div style="display: grid; grid-template-columns: 80px 140px 1fr; column-gap: 24px; align-items: baseline; border-top: 1px solid var(--ink-10); padding-top: 16px; background-color: inherit;">'
            f'<div class="display-data" style="color: var(--coral); background-color: inherit; font-size: 40px;">{esc(s.get("number",""))}</div>'
            f'<div class="mono-label" style="color: var(--ink-60); background-color: inherit;">{esc(s.get("day_range",""))}</div>'
            f'<div style="background-color: inherit;">'
            f'<div class="display-quote" style="color: var(--ink); background-color: inherit; font-style: italic;">{esc(s.get("subhead",""))}</div>'
            f'<div class="body-sm" style="color: var(--ink-80); background-color: inherit; margin-top: 4px;">{esc(s.get("body",""))}</div>'
            f"</div></div>"
        )
    return "\n".join(parts)


def render_product_names(items: list) -> str:
    return "\n".join(
        f'<div class="body-card-title" style="color: var(--ink); background-color: var(--white); padding: 12px 0; border-bottom: 1px solid var(--ink-10);">{esc(it.get("name",""))}</div>'
        for it in items
    )


def render_product_descs(items: list) -> str:
    return "\n".join(
        f'<div class="body-sm" style="color: var(--ink-80); background-color: var(--white); padding: 12px 0; border-bottom: 1px solid var(--ink-10);">{esc(it.get("description",""))}</div>'
        for it in items
    )


def render_portfolio_items(items: list) -> str:
    parts = []
    for i, it in enumerate(items[:4]):
        stats = it.get("stats", [])
        stats_html = "".join(
            f'<div style="background-color: var(--white);"><div class="mono-tag" style="color: var(--ink-60); background-color: var(--white);">{esc(st.get("label",""))}</div><div class="body-card-title" style="color: var(--ink); background-color: var(--white);">{esc(st.get("value",""))}</div></div>'
            for st in stats
        )
        tags = ",".join(it.get("tags", ["architectural", "property"]))
        parts.append(
            f'<div class="card" style="background-color: var(--white); overflow: hidden; display: grid; grid-template-rows: 1.6in auto;">'
            f'<div data-photo-slot="{esc(tags)}" data-slot-id="portfolio_{i}" style="background-size: cover; background-position: center; background-color: var(--ink-10);"></div>'
            f'<div style="padding: 14px 18px; background-color: var(--white);">'
            f'<div class="mono-label" style="color: var(--coral); background-color: var(--white);">{esc(it.get("eyebrow",""))}</div>'
            f'<div class="body-card-title" style="color: var(--ink); background-color: var(--white); margin-top: 4px;">{esc(it.get("title",""))}</div>'
            f'<div class="mono-tech" style="color: var(--ink-60); background-color: var(--white); margin-top: 2px;">{esc(it.get("location",""))}</div>'
            f'<div class="body-card-sm" style="color: var(--ink-80); background-color: var(--white); margin-top: 8px;">{esc(it.get("body",""))}</div>'
            f'<div style="display: grid; grid-template-columns: repeat({max(len(stats),1)}, 1fr); column-gap: 8px; margin-top: 10px; background-color: var(--white);">{stats_html}</div>'
            f"</div></div>"
        )
    return "\n".join(parts)


def substitute(template: str, data: dict) -> str:
    def repl(m: re.Match) -> str:
        key = m.group(1)
        return str(data.get(key, ""))
    return PLACEHOLDER_RE.sub(repl, template)


def render_page(template_dir: Path, page: dict) -> str:
    tmpl_id = page["template_id"]
    tmpl_path = template_dir / f"{tmpl_id}.html"
    if not tmpl_path.exists():
        sys.stderr.write(
            f"[html-emit] unknown template_id '{tmpl_id}'; "
            "falling back to 'two-column-narrative'\n")
        tmpl_path = template_dir / "two-column-narrative.html"
    tmpl = tmpl_path.read_text(encoding="utf-8")

    content = page.get("content", {}) or {}
    data = {
        "eyebrow": esc(page.get("eyebrow", "")),
        "title_lead": esc(page.get("title_lead", "")),
        "italic_accent_phrase": esc(page.get("italic_accent_phrase", "")),
        "page_number_roman": esc(page.get("page_number_roman", "")),
        "total_pages_roman": esc(page.get("total_pages_roman", "")),
        "running_header_left": esc(page.get("running_header_left", "")),
        "running_header_right": esc(page.get("running_header_right", "")),
        # content-derived
        "subtitle": esc(content.get("subtitle", "")),
        "metadata_label": esc(content.get("metadata_label", "")),
        "metadata_value": esc(content.get("metadata_value", "")),
        "pull_quote": esc(content.get("pull_quote", "")),
        "body_col_1": esc(content.get("body_col_1", content.get("body", ""))),
        "body_col_2": esc(content.get("body_col_2", "")),
        "caption_label": esc(content.get("caption_label", "")),
        "caption_location": esc(content.get("caption_location", "")),
        "part_number": esc(content.get("part_number", page.get("page_number", ""))),
        "summary_col_1": esc(content.get("summary_col_1", "")),
        "summary_col_2": esc(content.get("summary_col_2", "")),
        "panel_title": esc(content.get("panel_title", "")),
        "panel_body": esc(content.get("panel_body", "")),
        "footer_text": esc(content.get("footer_text", "okoacapital.com")),
        # derived HTML blocks
        "metrics_html": render_metrics_block(content.get("metrics", [])),
        "steps_html": render_steps_block(content.get("steps", [])),
        "names_html": render_product_names(content.get("items", [])),
        "descriptions_html": render_product_descs(content.get("items", [])),
        "items_html": render_portfolio_items(content.get("portfolio", content.get("items", []))),
    }
    return substitute(tmpl, data)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("page_plan")
    ap.add_argument("output")
    ap.add_argument("--tokens", required=True)
    ap.add_argument("--templates", required=True)
    args = ap.parse_args()

    plan = yaml.safe_load(Path(args.page_plan).read_text(encoding="utf-8"))
    pages = plan.get("pages", [])
    metadata = plan.get("metadata", {})
    tokens_css = Path(args.tokens).read_text(encoding="utf-8")
    tpl_dir = Path(args.templates)

    rendered_pages = []
    for p in pages:
        html_page = render_page(tpl_dir, p)
        # Inject data-page-number / data-total-pages on the first `data-template` element
        # of the rendered fragment so downstream consumers (fill-photo-slots,
        # emit-pptx-content) can resolve slot-to-page mapping. The template's
        # outermost .page div carries data-template but no page number; we inject
        # it here rather than making every template carry the attribute.
        total = len(pages)
        html_page = html_page.replace(
            'data-template=',
            f'data-page-number="{p.get("page_number","")}" data-total-pages="{total}" data-template=',
            1,
        )
        rendered_pages.append(html_page)

    html = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{esc(metadata.get('title', 'OKOA Document'))}</title>",
        GOOGLE_FONTS,
        "<style>",
        tokens_css,
        "</style>",
        "</head>",
        "<body>",
        "\n".join(rendered_pages),
        "</body>",
        "</html>",
    ]

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(html), encoding="utf-8")
    print(f"Wrote {len(pages)} pages to {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
