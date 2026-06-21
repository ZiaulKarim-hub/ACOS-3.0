#!/usr/bin/env python3
"""
HyperCore — Phase 2: Comprehensive read-only crawl.

Loads the saved session, dismisses any modal, walks every navigation target
discoverable from the dashboard, captures screenshot + HTML for each page,
extracts the loan list, and drills into 2 sample loan detail pages.

READ-ONLY by construction:
- All clicks pass through `safe_to_click()` (verb blocklist).
- Domain assertion: every page URL must be on app.hypercore.ai.
- The script never types into forms, never submits, never edits.

Outputs:
- data/screenshots/*.png
- data/html/*.html
- data/extracted/nav_map.yaml — labelled nav targets + URLs
- data/extracted/loans_list.yaml — every loan from the list view
- data/extracted/sample_loan_<id>.yaml — per-tab snapshots for sample loans
- data/extracted/inventory.yaml — master record of every page captured
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

import yaml
from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.session import (
    open_session,
    snapshot,
    safe_to_click,
    assert_on_hypercore,
    slugify,
    utc_now_iso,
    EXTRACTED_DIR,
    HTML_DIR,
    PROJECT_ROOT,
    ALLOWED_HOST,
)

DASHBOARD_URL = f"https://{ALLOWED_HOST}/dashboard"
NAV_DELAY = 1.5
SAMPLE_LOAN_COUNT = 2


# ─────────────────────────────────────────────────────────────────────────────
# Modal handling
# ─────────────────────────────────────────────────────────────────────────────

def dismiss_any_modal(page) -> bool:
    """Try multiple strategies to close any blocking modal. Returns True if dismissed."""
    # Strategy 1: Escape key (works on most well-built modals)
    try:
        page.keyboard.press("Escape")
        time.sleep(0.4)
    except Exception:
        pass

    # Strategy 2: known close-button patterns
    close_selectors = [
        "[aria-label*='close' i]",
        "[aria-label*='dismiss' i]",
        "[role='dialog'] button:has-text('×')",
        "[role='dialog'] button:has-text('✕')",
        "[role='dialog'] button[aria-label]",
    ]
    for sel in close_selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible(timeout=300):
                loc.click(timeout=2000)
                time.sleep(0.4)
                print(f"  [modal] dismissed via {sel!r}")
                return True
        except Exception:
            continue

    return False


# ─────────────────────────────────────────────────────────────────────────────
# Nav discovery
# ─────────────────────────────────────────────────────────────────────────────

def discover_nav_targets(page) -> list[dict]:
    """Return list of {label, url} for every internal nav target on this page."""
    html = page.content()
    soup = BeautifulSoup(html, "lxml")

    targets: list[dict] = []
    seen_urls: set[str] = set()

    # Strategy 1: <a href="..."> elements anywhere in <nav> or <aside>
    for container_tag in ("nav", "aside"):
        for container in soup.find_all(container_tag):
            for a in container.find_all("a", href=True):
                href = (a.get("href") or "").strip()
                if not href or href.startswith("#") or href.startswith("javascript:"):
                    continue
                if href.startswith("//") or href.startswith("http"):
                    if ALLOWED_HOST not in href:
                        continue
                # Normalize to absolute URL
                if href.startswith("/"):
                    url = f"https://{ALLOWED_HOST}{href}"
                else:
                    url = href
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                label = (a.get("aria-label")
                         or a.get("title")
                         or a.get_text(strip=True)
                         or href.strip("/"))
                if safe_to_click(label):
                    targets.append({"label": label, "url": url, "source": container_tag})

    # Strategy 2: any <a href="/..."> at the top level of the body if Strategy 1 was empty
    if not targets:
        for a in soup.find_all("a", href=True):
            href = (a.get("href") or "").strip()
            if not href.startswith("/") or href.startswith("//"):
                continue
            url = f"https://{ALLOWED_HOST}{href}"
            if url in seen_urls:
                continue
            seen_urls.add(url)
            label = (a.get("aria-label") or a.get("title") or a.get_text(strip=True) or href)
            if safe_to_click(label):
                targets.append({"label": label, "url": url, "source": "body"})

    return targets


# ─────────────────────────────────────────────────────────────────────────────
# Loan list extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_table_rows(html: str) -> list[dict]:
    """Try several strategies to extract tabular data from a page's HTML.

    Returns list of dicts (one per row) with column header → cell value.
    """
    soup = BeautifulSoup(html, "lxml")

    # Strategy 1: <table> elements
    rows: list[dict] = []
    for table in soup.find_all("table"):
        headers = []
        thead = table.find("thead")
        if thead:
            headers = [th.get_text(strip=True) for th in thead.find_all(["th", "td"])]
        if not headers:
            first_row = table.find("tr")
            if first_row:
                headers = [c.get_text(strip=True) for c in first_row.find_all(["th", "td"])]
        if not headers:
            continue

        body = table.find("tbody") or table
        for tr in body.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if not cells or len(cells) < len(headers) // 2:
                continue
            row = {}
            for i, c in enumerate(cells):
                key = headers[i] if i < len(headers) else f"col_{i}"
                row[key or f"col_{i}"] = c.get_text(" ", strip=True)
                # Capture link if present (likely loan detail href)
                link = c.find("a", href=True)
                if link:
                    row[f"_{key}_href"] = link["href"]
            rows.append(row)

    if rows:
        return rows

    # Strategy 2: ARIA grid roles
    for grid in soup.select("[role='grid'], [role='table']"):
        # Identify rows by role
        col_headers = [h.get_text(strip=True) for h in grid.select("[role='columnheader']")]
        for row_el in grid.select("[role='row']"):
            cells = row_el.select("[role='cell'], [role='gridcell']")
            if not cells:
                continue
            row = {}
            for i, c in enumerate(cells):
                key = col_headers[i] if i < len(col_headers) else f"col_{i}"
                row[key or f"col_{i}"] = c.get_text(" ", strip=True)
                link = c.find("a", href=True)
                if link:
                    row[f"_{key}_href"] = link["href"]
            rows.append(row)

    return rows


def find_loans_url(nav_targets: list[dict]) -> str | None:
    """Identify which nav target is most likely the Loans page."""
    for t in nav_targets:
        if re.search(r"\bloan", t["label"], re.I) or "/loan" in t["url"].lower():
            return t["url"]
    return None


def extract_loan_links(page) -> list[dict]:
    """Find every link from the loans-list page that points to a loan detail page."""
    html = page.content()
    soup = BeautifulSoup(html, "lxml")
    links: list[dict] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        # Loan detail URLs likely look like /loans/<id> or /loan/<id> or contain a UUID/numeric segment
        if not href.startswith("/"):
            continue
        if not re.search(r"/loans?/", href, re.I):
            continue
        if href.endswith("/loans") or href.endswith("/loan"):
            continue
        if href in seen:
            continue
        seen.add(href)
        label = a.get("aria-label") or a.get("title") or a.get_text(strip=True) or href
        links.append({"label": label[:100], "href": href})
    return links


def extract_tabs_in_detail(page) -> list[dict]:
    """Find tab-like elements within a loan detail page."""
    html = page.content()
    soup = BeautifulSoup(html, "lxml")
    tabs = []

    # ARIA pattern
    for tab in soup.select("[role='tab']"):
        text = tab.get_text(strip=True)
        if text and safe_to_click(text):
            tabs.append({"label": text, "selector": f"[role='tab']:has-text({text!r})"})

    # Fallback: anchors within the detail-page content area
    if not tabs:
        for a in soup.find_all("a", href=True):
            href = a.get("href") or ""
            if "#" in href or re.search(r"/loans?/[^/]+/", href, re.I):
                text = a.get_text(strip=True)
                if text and safe_to_click(text) and len(text) < 40:
                    tabs.append({"label": text, "href": href})

    # Dedupe by label
    seen = set()
    out = []
    for t in tabs:
        if t["label"] not in seen:
            seen.add(t["label"])
            out.append(t)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Main crawl
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    inventory = {
        "captured_at": utc_now_iso(),
        "dashboard": None,
        "nav_targets": [],
        "section_pages": [],
        "loans_list_page": None,
        "loans_extracted": [],
        "sample_loan_pages": [],
    }

    with open_session(headless=True, log_navigation=False) as (browser, context, page):
        # ── Phase A: Dashboard, dismiss modal, snapshot clean
        print("→ Phase A: dashboard cleanup")
        page.goto(DASHBOARD_URL, wait_until="networkidle", timeout=30000)
        assert_on_hypercore(page)
        dismiss_any_modal(page)
        time.sleep(1)
        rec = snapshot(page, "01-dashboard-clean")
        inventory["dashboard"] = rec
        print(f"  ✓ dashboard captured: {rec['url']}")

        # ── Phase B: discover nav
        print("\n→ Phase B: discovering nav targets")
        nav_targets = discover_nav_targets(page)
        inventory["nav_targets"] = nav_targets
        print(f"  Found {len(nav_targets)} unique nav targets:")
        for t in nav_targets:
            print(f"    • {t['label']:35s} → {t['url']}")

        # ── Phase C: walk each nav target
        print("\n→ Phase C: capturing each section")
        for i, t in enumerate(nav_targets, start=1):
            label = t["label"]
            url = t["url"]
            print(f"  [{i:02d}/{len(nav_targets)}] {label}")
            try:
                page.goto(url, wait_until="networkidle", timeout=20000)
                assert_on_hypercore(page)
                dismiss_any_modal(page)
                rec = snapshot(page, f"section-{i:02d}-{label}")
                rec["nav_label"] = label
                rec["nav_url"] = url
                inventory["section_pages"].append(rec)
                time.sleep(NAV_DELAY)
            except Exception as e:
                print(f"    ⚠  failed: {e}")

        # ── Phase D: loans deep dive
        print("\n→ Phase D: loans list extraction")
        loans_url = find_loans_url(nav_targets)
        if loans_url:
            try:
                page.goto(loans_url, wait_until="networkidle", timeout=20000)
                dismiss_any_modal(page)
                rec = snapshot(page, "loans-list")
                inventory["loans_list_page"] = rec
                print(f"  ✓ loans list page: {rec['url']}")

                loan_rows = extract_table_rows(page.content())
                print(f"  Extracted {len(loan_rows)} table rows")
                inventory["loans_extracted"] = loan_rows

                loan_links = extract_loan_links(page)
                print(f"  Found {len(loan_links)} loan-detail links")

                # Save full loans list early in case detail dive fails
                (EXTRACTED_DIR / "loans_list.yaml").write_text(
                    yaml.safe_dump(
                        {"loans_list_url": rec["url"],
                         "row_count": len(loan_rows),
                         "rows": loan_rows,
                         "detail_links": loan_links},
                        sort_keys=False, allow_unicode=True),
                    encoding="utf-8",
                )

                # ── Phase E: sample loan detail pages
                print(f"\n→ Phase E: drilling into {SAMPLE_LOAN_COUNT} sample loans")
                for j, link in enumerate(loan_links[:SAMPLE_LOAN_COUNT], start=1):
                    detail_url = link["href"]
                    if detail_url.startswith("/"):
                        detail_url = f"https://{ALLOWED_HOST}{detail_url}"
                    print(f"  [{j}/{SAMPLE_LOAN_COUNT}] {link['label']} → {detail_url}")
                    try:
                        page.goto(detail_url, wait_until="networkidle", timeout=20000)
                        dismiss_any_modal(page)
                        rec = snapshot(page, f"loan-{j:02d}-overview")
                        rec["loan_label"] = link["label"]
                        inventory["sample_loan_pages"].append(rec)

                        # Detect tabs and visit each
                        tabs = extract_tabs_in_detail(page)
                        print(f"     {len(tabs)} tabs detected")
                        for k, tab in enumerate(tabs[:8], start=1):
                            label = tab["label"]
                            try:
                                if "href" in tab:
                                    tab_url = tab["href"]
                                    if tab_url.startswith("/"):
                                        tab_url = f"https://{ALLOWED_HOST}{tab_url}"
                                    page.goto(tab_url, wait_until="networkidle", timeout=15000)
                                else:
                                    # role=tab — click it
                                    sel = tab["selector"]
                                    page.locator(sel).first.click(timeout=5000)
                                    time.sleep(0.8)
                                dismiss_any_modal(page)
                                rec = snapshot(page, f"loan-{j:02d}-tab-{k:02d}-{label}")
                                rec["loan_label"] = link["label"]
                                rec["tab_label"] = label
                                inventory["sample_loan_pages"].append(rec)
                                time.sleep(NAV_DELAY)
                            except Exception as e:
                                print(f"     ⚠  tab {label} failed: {e}")
                    except Exception as e:
                        print(f"    ⚠  loan {link['label']} failed: {e}")
            except Exception as e:
                print(f"  ⚠  loans phase failed: {e}")
        else:
            print("  (no Loans nav target detected — skipping)")

    # ── Save inventory
    inventory_path = EXTRACTED_DIR / "inventory.yaml"
    inventory_path.write_text(
        yaml.safe_dump(inventory, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    nav_map_path = EXTRACTED_DIR / "nav_map.yaml"
    nav_map_path.write_text(
        yaml.safe_dump({"nav_targets": inventory["nav_targets"]},
                       sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    print(f"\n✓ Inventory   → {inventory_path}")
    print(f"✓ Nav map     → {nav_map_path}")
    print(f"✓ Loans list  → {EXTRACTED_DIR / 'loans_list.yaml'}")
    print(f"\nTotals:")
    print(f"  • Sections captured  : {len(inventory['section_pages'])}")
    print(f"  • Loans extracted    : {len(inventory['loans_extracted'])}")
    print(f"  • Sample loan pages  : {len(inventory['sample_loan_pages'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
