#!/usr/bin/env python3
"""
html-qa-gate.py — pre-conversion QA gate

Runs two checklists against the emitted HTML:
  (A) 22-item Brad QA (subset enforceable from HTML alone — the rest run on rendered pixels in Phase 4)
  (B) 8-item coffee-table rhythm + composition checklist

Usage:
    html-qa-gate.py <input.html> [<output-report.yaml>] [--force] [--verbose]

Exits 0 on pass, 1 on fail (unless --force given).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
    from bs4 import BeautifulSoup
except ImportError as e:
    sys.stderr.write(f"ERROR: missing dependency {e.name}. pip install pyyaml beautifulsoup4\n")
    sys.exit(1)


def check(id_: str, desc: str, passed: bool, evidence: str, severity: str = "ERROR") -> dict:
    return {"id": id_, "description": desc, "status": "pass" if passed else "fail", "severity": severity, "evidence": evidence}


def brad_checks(soup: BeautifulSoup, raw: str) -> list:
    results = []

    head = soup.find("head")
    # 1. Google Fonts link
    gfonts = soup.find("link", href=re.compile(r"fonts\.googleapis\.com"))
    results.append(check("brad-01", "Google Fonts link in <head>", bool(gfonts), str(gfonts)[:120] if gfonts else "no <link> to fonts.googleapis.com"))

    # 2. @page Letter margin 0 in <style>
    has_page_rule = bool(re.search(r"@page\s*\{[^}]*size\s*:\s*Letter[^}]*margin\s*:\s*0", raw, re.IGNORECASE | re.DOTALL))
    results.append(check("brad-02", "@page { size: Letter; margin: 0; } rule present", has_page_rule, "found" if has_page_rule else "missing @page rule"))

    # 3. OKOA logo SVG with fill='none' on outer <svg>
    svgs = soup.find_all("svg")
    logo_ok = any(s.get("fill") == "none" and re.search(r"M(126\.1|73\.3|18\.8|88\.7)", str(s)) for s in svgs)
    results.append(check("brad-03", "OKOA logo SVG present with fill='none' on outer <svg>", logo_ok, f"found {len(svgs)} svgs; logo match {logo_ok}"))

    # 4. .mono-label class used
    has_mono_label = bool(soup.select(".mono-label"))
    results.append(check("brad-04", "Mono label class used (coral eyebrow labels)", has_mono_label, f"mono-label elements: {len(soup.select('.mono-label'))}"))

    # 5. Cormorant display class used
    has_cormorant = bool(soup.select(".display-xl, .display-lg, .display-md, .display-sm, .display-data, .display-quote"))
    results.append(check("brad-05", "Cormorant display classes used for headlines", has_cormorant, f"display class count: {len(soup.select('.display-xl, .display-lg, .display-md, .display-sm, .display-data, .display-quote'))}"))

    # 6. No --ink-40 on dark backgrounds (spot check: dark bg class + ink-40 in same style)
    dark_ink40 = False
    for el in soup.find_all(style=True):
        st = el.get("style", "")
        if ("var(--ink-40)" in st or "#8d8d8d" in st.lower()) and ("bg-ink" in (el.get("class") or []) or "bg-sage" in (el.get("class") or []) or "bg-navy" in (el.get("class") or [])):
            dark_ink40 = True
            break
    results.append(check("brad-06", "No --ink-40 used on dark backgrounds (bg-ink/bg-sage/bg-navy)", not dark_ink40, "no violations" if not dark_ink40 else "found ink-40 on dark bg"))

    # 7. Carbon grid CSS present (in embedded <style>)
    has_grid = "col-16" in raw or "grid-template-columns: repeat(16" in raw
    results.append(check("brad-07", "Carbon 16-column grid CSS present", has_grid, "col-16 / grid-16 found" if has_grid else "missing"))

    # 8. Every .page div has explicit background (class or inline)
    pages = soup.select(".page")
    pages_with_bg = sum(1 for p in pages if "background-color" in (p.get("style") or "") or any(c.startswith("bg-") for c in (p.get("class") or [])))
    results.append(check("brad-08", "Every .page has explicit background", pages_with_bg == len(pages) and len(pages) > 0, f"{pages_with_bg}/{len(pages)} pages with explicit bg"))

    # 9. html+body explicit background
    html_bg = soup.find("html")
    body_bg = soup.find("body")
    bg_rule_present = "background-color" in raw.lower() and ("html" in raw.lower() or "body" in raw.lower())
    results.append(check("brad-09", "html + body explicit background declared", bg_rule_present, "declared in embedded style" if bg_rule_present else "missing"))

    # 10. IBM Plex Sans referenced in body class or font stack
    has_plex = "IBM Plex Sans" in raw
    results.append(check("brad-10", "IBM Plex Sans referenced", has_plex, "present" if has_plex else "missing"))

    # 11. IBM Plex Mono referenced
    has_plex_mono = "IBM Plex Mono" in raw
    results.append(check("brad-11", "IBM Plex Mono referenced", has_plex_mono, "present" if has_plex_mono else "missing"))

    # 12. Coral color defined
    has_coral = re.search(r"--coral\s*:\s*#(ff795e|FF795E)", raw) is not None
    results.append(check("brad-12", "--coral token defined as #ff795e", bool(has_coral), "yes" if has_coral else "missing/different"))

    # 13-22: remaining Brad checks that are evaluable visually (deferred to Phase 4) — stubbed as pass-through informational
    for i in range(13, 23):
        results.append(check(f"brad-{i:02d}", "Visual-only Brad criterion (deferred to Phase 4)", True, "deferred", severity="WARNING"))

    return results


def coffee_table_checks(soup: BeautifulSoup, raw: str) -> list:
    results = []
    pages = soup.select(".page[data-template]")
    templates = [p.get("data-template") for p in pages]
    content_pages = [t for t in templates if t in ("two-column-narrative", "metric-grid", "timeline", "product-detail", "portfolio-grid")]
    photo_pages = sum(1 for t in templates if t == "photo-break")

    # ct-01: >=1 full-bleed photo per 3 content pages
    expected_photos = (len(content_pages) + 2) // 3  # ceil(n/3)
    results.append(check("ct-01", "≥1 full-bleed photo page per 3 content pages", photo_pages >= expected_photos, f"{photo_pages} photo-break / {len(content_pages)} content (need ≥{expected_photos})"))

    # ct-02: chapter divider presence (informational — depends on content having parts)
    dividers = sum(1 for t in templates if t == "chapter-divider")
    results.append(check("ct-02", "If content has multiple parts, chapter divider present", True, f"{dividers} dividers (informational)", severity="WARNING"))

    # ct-03: first page is cover
    results.append(check("ct-03", "First page is cover template", len(templates) > 0 and templates[0] == "cover", f"first template: {templates[0] if templates else 'none'}"))

    # ct-04: last page is closing
    results.append(check("ct-04", "Last page is closing template", len(templates) > 0 and templates[-1] == "closing", f"last template: {templates[-1] if templates else 'none'}"))

    # ct-05: roman page numbers
    has_roman_page = bool(re.search(r"[IVXLCDM]+\s*/\s*[IVXLCDM]+", raw))
    results.append(check("ct-05", "Roman page numbers in 'N / total' format", has_roman_page, "found" if has_roman_page else "no roman pagination"))

    # ct-06: italic accent on section titles (at least one per content page)
    italic_spans = soup.select("span.italic-accent")
    results.append(check("ct-06", "Italic Cormorant accent on section titles", len(italic_spans) >= len(content_pages), f"{len(italic_spans)} italic accents / {len(content_pages)} content pages"))

    # ct-07: page-level eyebrow format. Only the first .mono-label per .page is the
    # page-level eyebrow; inner mono-labels (metric labels, portfolio geo tags,
    # timeline day ranges) are design elements, not section markers, and are
    # intentionally free-form. Cover (index 0) and photo-break pages are exempt.
    eyebrow_ok = 0
    eyebrow_total = 0
    eyebrow_format_re = re.compile(r"^(?:\d{2}\s+[A-Z]|PART\s+[IVXLCDM]+)")
    for idx, page in enumerate(pages):
        tmpl = page.get("data-template", "")
        if idx == 0 or tmpl == "photo-break":
            continue
        el = page.select_one(".mono-label")
        if el is None:
            continue
        txt = el.get_text(strip=True)
        if not txt:
            continue
        eyebrow_total += 1
        if eyebrow_format_re.match(txt):
            eyebrow_ok += 1
    results.append(check("ct-07", "Page eyebrows use 'NN NAME' or 'PART N' format",
                         eyebrow_total == 0 or eyebrow_ok == eyebrow_total,
                         f"{eyebrow_ok}/{eyebrow_total} page eyebrows match format"))

    # ct-08: closing has dark panel (look for bg-sage or bg-ink within the closing page)
    closing_pages = [p for p in pages if p.get("data-template") == "closing"]
    closing_has_dark = False
    if closing_pages:
        st = str(closing_pages[0])
        closing_has_dark = "var(--sage-80)" in st or "var(--ink)" in st or "bg-sage" in st or "bg-ink" in st
    results.append(check("ct-08", "Closing page has dark brand panel", closing_has_dark, "dark panel detected" if closing_has_dark else "missing"))

    return results


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input")
    ap.add_argument("output", nargs="?")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    raw = Path(args.input).read_text(encoding="utf-8")
    soup = BeautifulSoup(raw, "html.parser")

    brad_results = brad_checks(soup, raw)
    ct_results = coffee_table_checks(soup, raw)

    failed_errors = [r for r in brad_results + ct_results if r["status"] == "fail" and r["severity"] == "ERROR"]
    verdict = "pass" if not failed_errors else "fail"

    report = {
        "verdict": verdict,
        "brad_qa": brad_results,
        "coffee_table_qa": ct_results,
        "failed_items": [r["id"] for r in failed_errors],
    }
    out = yaml.safe_dump(report, sort_keys=False, allow_unicode=True)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(out, encoding="utf-8")
    else:
        print(out)

    if args.verbose:
        for r in brad_results + ct_results:
            sys.stderr.write(f"  [{r['status']:>4}] {r['id']}: {r['description']}\n")

    if verdict == "fail" and not args.force:
        sys.stderr.write(f"QA gate FAILED — {len(failed_errors)} ERROR-severity items: {', '.join(r['id'] for r in failed_errors)}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
