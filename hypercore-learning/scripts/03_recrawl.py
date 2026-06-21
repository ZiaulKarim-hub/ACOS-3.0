#!/usr/bin/env python3
"""
HyperCore — Phase 2.5: Smart re-crawl using URL probing + comprehensive loans.

The Phase 2 crawler missed the actual left-rail nav because HyperCore's sidebar
uses React click handlers (not <a href>). This script probes common URL paths
to discover the real navigation, then comprehensively crawls all loans.

URL probing: try a candidate path. If page loads with non-error content
(no 404, has substantive HTML), record it. Otherwise skip.

Comprehensive loan crawl:
- Load /loans (the actual list page)
- Extract every row → loans_full.yaml
- For every loan ID found: navigate to /loans/<id>, capture overview
- For each tab found on the loan page: click, capture
- Save per-loan YAML with structured data

READ-ONLY by construction. Same safety rails as 02_crawl.py.
"""
from __future__ import annotations

import json
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
NAV_DELAY = 1.0
LOAN_DETAIL_DELAY = 1.5

# Candidate top-level URL paths to probe.
CANDIDATE_PATHS = [
    "/dashboard",
    "/loans",
    "/clients",
    "/borrowers",
    "/customers",
    "/reports",
    "/analytics",
    "/settings",
    "/admin",
    "/team",
    "/users",
    "/notifications",
    "/help",
    "/tasks",
    "/transactions",
    "/payments",
    "/documents",
    "/files",
    "/funds",
    "/products",
    "/loan-products",
    "/integrations",
    "/api-keys",
    "/billing",
    "/audit",
    "/account",
    "/profile",
    "/search",
]

# Per-loan tabs we expect (based on what we saw)
KNOWN_LOAN_TABS = ["Info", "Terms", "Notes", "Files"]
# Per-loan inner table tabs (Schedule, Transactions, etc.)
KNOWN_INNER_TABS = ["Schedule", "Original", "Transactions", "Fees", "Deposits", "Aging"]


# ─────────────────────────────────────────────────────────────────────────────
# Modal handling (same as 02_crawl)
# ─────────────────────────────────────────────────────────────────────────────

def dismiss_any_modal(page) -> bool:
    try:
        page.keyboard.press("Escape")
        time.sleep(0.3)
    except Exception:
        pass
    for sel in [
        "[aria-label*='close' i]",
        "[aria-label*='dismiss' i]",
        "[role='dialog'] button:has-text('×')",
        "[role='dialog'] button:has-text('✕')",
    ]:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible(timeout=300):
                loc.click(timeout=2000)
                time.sleep(0.3)
                return True
        except Exception:
            continue
    return False


# ─────────────────────────────────────────────────────────────────────────────
# URL probing
# ─────────────────────────────────────────────────────────────────────────────

def probe_url(page, path: str) -> dict | None:
    """Visit a candidate URL. Return snapshot dict if it loaded a real page, None otherwise."""
    url = f"https://{ALLOWED_HOST}{path}"
    try:
        page.goto(url, wait_until="networkidle", timeout=15000)
    except PlaywrightTimeoutError:
        # Some pages may not reach networkidle but still loaded — try again with 'load'
        try:
            page.goto(url, wait_until="load", timeout=10000)
        except Exception:
            return None
    except Exception:
        return None

    # If the URL changed away from the requested path significantly, it might be a redirect
    current = page.url
    final_path = current.replace(f"https://{ALLOWED_HOST}", "").split("?")[0].rstrip("/")
    if final_path == "":
        final_path = "/"

    # Heuristic: did the page actually render content?
    title = page.title()
    body_text = page.inner_text("body")[:3000]
    body_len = len(body_text.strip())
    is_404 = bool(re.search(r"\b(404|not\s+found|page\s+not\s+found)\b", body_text, re.I))
    is_error = bool(re.search(r"\b(error|forbidden|unauthorized|access\s+denied)\b", body_text, re.I)) and body_len < 500

    if is_404 or body_len < 100:
        return None

    dismiss_any_modal(page)
    rec = snapshot(page, f"nav-{path.strip('/').replace('/', '-')}")
    rec["candidate_path"] = path
    rec["final_path"] = final_path
    rec["body_text_preview"] = body_text[:500]
    rec["body_length"] = body_len
    rec["is_error"] = is_error
    return rec


# ─────────────────────────────────────────────────────────────────────────────
# Loan list extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_loan_list(page) -> tuple[list[dict], list[str]]:
    """From /loans page, extract loan rows and unique loan IDs.

    Returns (rows, ids).
    """
    html = page.content()
    soup = BeautifulSoup(html, "lxml")

    # Find every link matching /loans/<id>
    ids: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        m = re.match(r"^/loans/(\d+)/?$", href)
        if m:
            ids.add(m.group(1))

    # Try to extract table rows
    rows: list[dict] = []
    for table in soup.find_all("table"):
        headers = []
        thead = table.find("thead")
        if thead:
            headers = [th.get_text(strip=True) for th in thead.find_all(["th", "td"])]
        if not headers:
            tr = table.find("tr")
            if tr:
                headers = [c.get_text(strip=True) for c in tr.find_all(["th", "td"])]
        if not headers:
            continue

        body = table.find("tbody") or table
        for tr in body.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if not cells:
                continue
            row = {}
            row_id = None
            for i, c in enumerate(cells):
                key = headers[i] if i < len(headers) else f"col_{i}"
                key = key or f"col_{i}"
                row[key] = c.get_text(" ", strip=True)
                link = c.find("a", href=True)
                if link:
                    href = link["href"]
                    row[f"_{key}_href"] = href
                    m = re.match(r"^/loans/(\d+)/?$", href)
                    if m:
                        row_id = m.group(1)
            if row_id:
                row["_loan_id"] = row_id
                rows.append(row)

    # Also try ARIA grid/role-based tables for SPAs that don't use <table>
    if not rows:
        for grid in soup.select("[role='grid'], [role='table']"):
            col_headers = [h.get_text(strip=True) for h in grid.select("[role='columnheader']")]
            for row_el in grid.select("[role='row']"):
                cells = row_el.select("[role='cell'], [role='gridcell']")
                if not cells:
                    continue
                row = {}
                row_id = None
                for i, c in enumerate(cells):
                    key = col_headers[i] if i < len(col_headers) else f"col_{i}"
                    row[key or f"col_{i}"] = c.get_text(" ", strip=True)
                    link = c.find("a", href=True)
                    if link:
                        m = re.match(r"^/loans/(\d+)/?$", link["href"])
                        if m:
                            row_id = m.group(1)
                if row_id:
                    row["_loan_id"] = row_id
                    rows.append(row)

    return rows, sorted(ids, key=int)


# ─────────────────────────────────────────────────────────────────────────────
# Per-loan crawl
# ─────────────────────────────────────────────────────────────────────────────

def crawl_loan(page, loan_id: str) -> dict:
    """Visit a loan detail page and capture overview + each tab. Return aggregated record."""
    base_url = f"https://{ALLOWED_HOST}/loans/{loan_id}"
    record: dict = {"loan_id": loan_id, "url": base_url, "tabs": []}

    try:
        page.goto(base_url, wait_until="networkidle", timeout=20000)
    except PlaywrightTimeoutError:
        try:
            page.goto(base_url, wait_until="load", timeout=10000)
        except Exception as e:
            record["error"] = f"navigation: {e}"
            return record

    dismiss_any_modal(page)
    rec = snapshot(page, f"loan-{loan_id}-overview", polite_delay=LOAN_DETAIL_DELAY)
    record["overview"] = rec
    record["title"] = page.title()

    # Try clicking each known top-level loan tab
    for tab_name in KNOWN_LOAN_TABS:
        try:
            sel = f"[role='tab']:has-text('{tab_name}'), button:has-text('{tab_name}')"
            tab = page.locator(sel).first
            if tab.count() == 0 or not tab.is_visible(timeout=300):
                continue
            tab.click(timeout=3000)
            time.sleep(0.7)
            dismiss_any_modal(page)
            tab_rec = snapshot(page, f"loan-{loan_id}-tab-{tab_name.lower()}",
                               polite_delay=LOAN_DETAIL_DELAY)
            tab_rec["tab"] = tab_name
            record["tabs"].append(tab_rec)
        except Exception as e:
            record.setdefault("tab_errors", {})[tab_name] = str(e)

    # Also try the inner table tabs (Schedule, Transactions, etc.)
    inner_records = []
    for tab_name in KNOWN_INNER_TABS:
        try:
            sel = f"button:has-text('{tab_name}'), [role='tab']:has-text('{tab_name}')"
            tab = page.locator(sel).first
            if tab.count() == 0 or not tab.is_visible(timeout=300):
                continue
            tab.click(timeout=3000)
            time.sleep(0.7)
            inner_rec = snapshot(page, f"loan-{loan_id}-inner-{tab_name.lower()}",
                                 polite_delay=LOAN_DETAIL_DELAY)
            inner_rec["inner_tab"] = tab_name
            inner_records.append(inner_rec)
        except Exception as e:
            record.setdefault("inner_tab_errors", {})[tab_name] = str(e)
    if inner_records:
        record["inner_tabs"] = inner_records

    return record


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    inventory = {
        "captured_at": utc_now_iso(),
        "nav_probes": {},
        "loans_list": None,
        "loans_full": [],
    }

    with open_session(headless=True, log_navigation=False) as (browser, context, page):
        # Phase 1: Probe URLs
        print("→ Phase 1: probing candidate URLs")
        for path in CANDIDATE_PATHS:
            print(f"  probing {path:25s}", end=" ", flush=True)
            rec = probe_url(page, path)
            if rec:
                final = rec["final_path"]
                marker = "✓" if final == path else f"→ {final}"
                err_marker = " [error-suspicious]" if rec.get("is_error") else ""
                print(f"{marker} ({rec['title'][:40]!r}, {rec['body_length']:,}b){err_marker}")
                inventory["nav_probes"][path] = rec
            else:
                print("✗ (404 / empty / error)")
            time.sleep(NAV_DELAY)

        # Phase 2: Loans list
        print("\n→ Phase 2: extract loans list from /loans")
        if "/loans" in inventory["nav_probes"]:
            try:
                page.goto(f"https://{ALLOWED_HOST}/loans", wait_until="networkidle", timeout=20000)
                dismiss_any_modal(page)
                # Allow extra time for the list to render (lazy loading)
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except PlaywrightTimeoutError:
                    pass
                time.sleep(2)
                rec = snapshot(page, "loans-list-real")
                inventory["loans_list"] = rec
                rows, loan_ids = extract_loan_list(page)
                inventory["loans_list_rows"] = rows
                inventory["loan_ids_discovered"] = loan_ids
                print(f"  ✓ extracted {len(rows)} rows, {len(loan_ids)} unique loan IDs")
                if loan_ids:
                    print(f"    IDs: {', '.join(loan_ids[:30])}{'…' if len(loan_ids) > 30 else ''}")

                # Persist immediately in case loan crawl fails partway
                (EXTRACTED_DIR / "loans_list.yaml").write_text(
                    yaml.safe_dump(
                        {"url": rec["url"], "rows": rows, "loan_ids": loan_ids},
                        sort_keys=False, allow_unicode=True),
                    encoding="utf-8",
                )
            except Exception as e:
                print(f"  ⚠  loans list failed: {e}")
                loan_ids = []
        else:
            print("  ⚠  /loans probe failed earlier — skipping list extraction")
            loan_ids = []

        # Phase 3: Per-loan crawl (every loan)
        if loan_ids:
            print(f"\n→ Phase 3: crawling all {len(loan_ids)} loans")
            for i, lid in enumerate(loan_ids, start=1):
                print(f"  [{i:02d}/{len(loan_ids)}] loan {lid}", end=" ", flush=True)
                try:
                    rec = crawl_loan(page, lid)
                    inventory["loans_full"].append(rec)
                    n_tabs = len(rec.get("tabs", []))
                    n_inner = len(rec.get("inner_tabs", []))
                    err = " ⚠" if rec.get("error") else ""
                    print(f"— {n_tabs} top tabs, {n_inner} inner tabs{err}")
                except Exception as e:
                    print(f"  ⚠  failed: {e}")
                # Persist incrementally — every 5 loans
                if i % 5 == 0:
                    (EXTRACTED_DIR / "loans_full_partial.yaml").write_text(
                        yaml.safe_dump({"loans": inventory["loans_full"]},
                                       sort_keys=False, allow_unicode=True),
                        encoding="utf-8",
                    )

    # Final write
    (EXTRACTED_DIR / "nav_probes.yaml").write_text(
        yaml.safe_dump({"probes": inventory["nav_probes"]}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    (EXTRACTED_DIR / "loans_full.yaml").write_text(
        yaml.safe_dump({"loans": inventory["loans_full"]}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    (EXTRACTED_DIR / "inventory_v2.yaml").write_text(
        yaml.safe_dump(inventory, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    print(f"\n✓ Nav probes  → data/extracted/nav_probes.yaml")
    print(f"✓ Loans list  → data/extracted/loans_list.yaml")
    print(f"✓ Loans full  → data/extracted/loans_full.yaml")
    print(f"✓ Inventory   → data/extracted/inventory_v2.yaml")
    print(f"\nSummary:")
    print(f"  • Real nav targets discovered: {len(inventory['nav_probes'])}")
    print(f"  • Loan IDs discovered:         {len(loan_ids) if loan_ids else 0}")
    print(f"  • Loan detail pages captured:  {len(inventory['loans_full'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
