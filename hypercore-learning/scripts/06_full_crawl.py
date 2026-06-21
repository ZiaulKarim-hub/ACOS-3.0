#!/usr/bin/env python3
"""
HyperCore — Phase 2 v3: Streamlined comprehensive crawl.

Designed to complete within the ~10-minute session window:
  1. Warm up at /dashboard
  2. Discover left-rail nav by clicking each sidebar icon (Playwright bounding-box)
  3. For the Loans nav target: load it, wait 10s for SPA, extract every loan ID
  4. Visit each loan: capture overview (single page per loan, no tab clicks for speed)
  5. Save partial state every 5 loans so a session timeout doesn't lose progress
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
    utc_now_iso,
    EXTRACTED_DIR,
    HTML_DIR,
    PROJECT_ROOT,
    ALLOWED_HOST,
)

DASHBOARD_URL = f"https://{ALLOWED_HOST}/dashboard"
SPA_RENDER_WAIT = 6.0  # generous wait for React + lazy data fetch
LOAN_DELAY = 0.6  # short polite delay between loans


def is_session_dead(page) -> bool:
    return ("auth.hypercore.ai" in page.url
            or "/login" in page.url
            or "/oauth" in page.url)


def discover_sidebar_links(page) -> list[dict]:
    """Find clickable elements in the leftmost ~80px of the page (sidebar icons).

    Returns list of {label, url} after clicking each and observing where it goes.
    Restores the page to /dashboard between clicks.
    """
    nav_map: list[dict] = []

    # Get all clickable elements with bounding boxes
    candidates = page.locator("button, a, [role='button'], [role='link']").all()
    sidebar = []
    for c in candidates:
        try:
            box = c.bounding_box()
            if box is None:
                continue
            # Sidebar icons are in the leftmost ~80px and below the very top (skip logo)
            if box["x"] < 80 and 50 < box["y"] < 1200 and box["width"] < 80:
                aria = c.get_attribute("aria-label") or ""
                title = c.get_attribute("title") or ""
                sidebar.append({"locator": c, "aria": aria, "title": title,
                                "y": box["y"], "x": box["x"]})
        except Exception:
            pass

    # Sort by y-coordinate (top to bottom)
    sidebar.sort(key=lambda s: s["y"])
    print(f"  found {len(sidebar)} sidebar element(s)")

    seen_urls: set[str] = set()
    for i, item in enumerate(sidebar):
        label = item["aria"] or item["title"] or f"sidebar-{i}"
        if not safe_to_click(label):
            print(f"    skip (unsafe text): {label!r}")
            continue
        try:
            url_before = page.url
            item["locator"].click(timeout=2500)
            time.sleep(2)
            url_after = page.url
            if is_session_dead(page):
                print(f"    SESSION DIED while clicking {label!r}")
                return nav_map
            if url_after != url_before and url_after not in seen_urls:
                seen_urls.add(url_after)
                nav_map.append({"label": label, "url": url_after,
                                "y": item["y"]})
                print(f"    {label[:30]!r:32s} → {url_after}")
        except Exception as e:
            print(f"    click failed for {label!r}: {str(e)[:80]}")
        finally:
            # Return to dashboard to re-establish base for next click
            try:
                page.goto(DASHBOARD_URL, wait_until="domcontentloaded", timeout=10000)
                time.sleep(1)
            except Exception:
                pass

    return nav_map


def find_loans_url(nav_map: list[dict]) -> str | None:
    """Pick the nav target most likely to be the Loans list."""
    # Look for /loans, /loan, /portfolio in URLs (not /loans/{id})
    for item in nav_map:
        url = item["url"]
        path = url.replace(f"https://{ALLOWED_HOST}", "").split("?")[0].rstrip("/")
        if re.match(r"^/(loans?|portfolio)$", path):
            return url
    return None


def extract_loan_ids_from_page(page) -> list[str]:
    """Wait for SPA to render and extract /loans/{id} links."""
    time.sleep(SPA_RENDER_WAIT)
    html = page.content()
    ids = sorted(set(re.findall(r"/loans/(\d+)", html)), key=lambda x: int(x))
    return ids


def main() -> int:
    inv = {
        "captured_at": utc_now_iso(),
        "sidebar_nav": [],
        "section_pages": {},
        "loans_list_url": None,
        "loan_ids": [],
        "loan_captures": [],
    }

    with open_session(headless=True, log_navigation=False) as (browser, ctx, page):
        # ── Phase 1: Warmup
        print("→ Phase 1: warmup")
        page.goto(DASHBOARD_URL, wait_until="domcontentloaded", timeout=20000)
        time.sleep(SPA_RENDER_WAIT)
        if is_session_dead(page):
            print("✗ Session is dead — re-run 01_login.py")
            return 1
        print(f"  ✓ on {page.url}")

        # ── Phase 2: Sidebar discovery
        print("\n→ Phase 2: sidebar discovery (click-based)")
        sidebar_map = discover_sidebar_links(page)
        inv["sidebar_nav"] = sidebar_map

        # Save sidebar map immediately
        (EXTRACTED_DIR / "sidebar_nav.yaml").write_text(
            yaml.safe_dump({"sidebar": sidebar_map}, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

        # ── Phase 3: Capture each non-loan-detail nav target
        print("\n→ Phase 3: capturing each section page")
        for item in sidebar_map:
            url = item["url"]
            label = item["label"]
            # Skip individual loan detail pages
            if re.match(rf"^https://{ALLOWED_HOST}/loans/\d+", url):
                continue
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                time.sleep(SPA_RENDER_WAIT)
                if is_session_dead(page):
                    print(f"  SESSION DIED at {label}")
                    break
                rec = snapshot(page, f"section2-{label.replace('/', '-')}",
                               polite_delay=0.5)
                rec["sidebar_label"] = label
                inv["section_pages"][label] = rec
                print(f"  ✓ {label[:30]:30s} captured ({rec['url']})")
            except Exception as e:
                print(f"  ⚠ {label} failed: {str(e)[:80]}")

        # ── Phase 4: Find loans list, extract all IDs
        print("\n→ Phase 4: discover all loan IDs")
        loans_url = find_loans_url(sidebar_map)
        if loans_url:
            print(f"  loans list URL: {loans_url}")
            try:
                page.goto(loans_url, wait_until="domcontentloaded", timeout=20000)
                ids = extract_loan_ids_from_page(page)
                if not ids:
                    # Try one more time with even longer wait
                    time.sleep(5)
                    ids = extract_loan_ids_from_page(page)
                inv["loans_list_url"] = loans_url
                inv["loan_ids"] = ids
                print(f"  ✓ {len(ids)} unique loan IDs: {ids[:30]}{'…' if len(ids) > 30 else ''}")
                rec = snapshot(page, "loans-list-final", polite_delay=0)
                inv["loans_list_capture"] = rec
            except Exception as e:
                print(f"  ⚠ loans list failed: {e}")
                ids = []
        else:
            print("  no /loans-like URL found in sidebar; falling back to URL probing")
            ids = []

        # If sidebar didn't give us a Loans URL, try direct /loans
        if not ids and not is_session_dead(page):
            for fallback in ["/loans", "/loan", "/portfolio"]:
                try:
                    page.goto(f"https://{ALLOWED_HOST}{fallback}",
                              wait_until="domcontentloaded", timeout=15000)
                    time.sleep(SPA_RENDER_WAIT)
                    if is_session_dead(page):
                        break
                    candidate_ids = extract_loan_ids_from_page(page)
                    if len(candidate_ids) > 5:
                        ids = candidate_ids
                        inv["loans_list_url"] = page.url
                        inv["loan_ids"] = ids
                        print(f"  ✓ fallback {fallback}: {len(ids)} IDs")
                        break
                except Exception:
                    continue

        # ── Phase 5: Crawl every loan (overview only)
        if ids:
            print(f"\n→ Phase 5: crawl {len(ids)} loans (overview only)")
            for i, lid in enumerate(ids, start=1):
                if is_session_dead(page):
                    print(f"  SESSION DIED at loan {lid} (#{i})")
                    break
                try:
                    page.goto(f"https://{ALLOWED_HOST}/loans/{lid}",
                              wait_until="domcontentloaded", timeout=15000)
                    time.sleep(3)  # let loan detail render
                    if is_session_dead(page):
                        print(f"  SESSION DIED at loan {lid}")
                        break
                    rec = snapshot(page, f"v3-loan-{lid}-overview", polite_delay=LOAN_DELAY)
                    rec["loan_id"] = lid
                    inv["loan_captures"].append(rec)
                    print(f"  [{i:02d}/{len(ids)}] loan {lid:>4s}  ({rec['url'][-40:]})")
                except Exception as e:
                    print(f"  [{i:02d}/{len(ids)}] loan {lid:>4s}  ⚠ {str(e)[:60]}")

                # Save partial state every 5 loans
                if i % 5 == 0:
                    (EXTRACTED_DIR / "v3_partial.yaml").write_text(
                        yaml.safe_dump(inv, sort_keys=False, allow_unicode=True),
                        encoding="utf-8",
                    )

    # Final save
    (EXTRACTED_DIR / "v3_inventory.yaml").write_text(
        yaml.safe_dump(inv, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    print("\n=== Summary ===")
    print(f"  Sidebar nav targets:  {len(inv['sidebar_nav'])}")
    print(f"  Section pages:        {len(inv['section_pages'])}")
    print(f"  Loan IDs found:       {len(inv['loan_ids'])}")
    print(f"  Loans captured:       {len(inv['loan_captures'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
