#!/usr/bin/env python3
"""
HyperCore — Phase 2 v2: Fixed comprehensive crawl.

Fixes from 03_recrawl.py:
  1. Detect auth-redirect: if page.url ends up on auth.hypercore.ai, abort.
  2. Use domcontentloaded + sleep instead of networkidle (HyperCore has
     long-polling connections that prevent networkidle from firing).
  3. Larger candidate path list.
  4. Comprehensive 33-loan crawl with all tabs and inner tabs.

Run this IMMEDIATELY after 01_login.py to keep the session fresh.
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
PROBE_DELAY = 0.5  # short, since we need to beat the session clock
LOAN_DELAY = 1.0
RENDER_WAIT = 2.5  # seconds to let React render after page load

# Candidate paths to probe.
CANDIDATE_PATHS = [
    "/dashboard",
    "/loans", "/loan", "/loans/list", "/portfolio",
    "/clients", "/client", "/borrowers", "/customers", "/contacts",
    "/reports", "/report", "/analytics",
    "/settings", "/admin", "/configuration", "/preferences",
    "/team", "/users", "/members",
    "/notifications", "/notification", "/alerts",
    "/help", "/support", "/docs",
    "/tasks", "/todos", "/workflow",
    "/transactions", "/payments", "/cashflow",
    "/documents", "/files", "/library",
    "/funds", "/investors", "/sources",
    "/products", "/loan-products", "/loan-types",
    "/integrations", "/api-keys", "/webhooks",
    "/billing", "/audit", "/logs",
    "/account", "/profile", "/me",
    "/search",
    # Frontegg-related (auth platform)
    "/account/settings", "/account/users", "/account/api-keys",
    # Common SPA patterns
    "/app", "/app/loans", "/app/clients",
    "/main", "/home",
]

KNOWN_LOAN_TABS = ["Info", "Terms", "Notes", "Files"]
KNOWN_INNER_TABS = ["Schedule", "Original", "Transactions", "Fees", "Deposits", "Aging"]


def is_session_redirect(url: str) -> bool:
    """True if the URL is the auth/login page — meaning our session died."""
    return ("auth.hypercore.ai" in url
            or "/login" in url
            or "/oauth" in url)


def safe_goto(page, url: str, timeout: int = 10000) -> str | None:
    """Navigate to URL with domcontentloaded wait. Return final URL or None on failure."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        time.sleep(RENDER_WAIT)
        final = page.url
        if is_session_redirect(final):
            return None  # signal: session dead
        return final
    except PlaywrightTimeoutError:
        return None
    except Exception:
        return None


def dismiss_any_modal(page) -> bool:
    try:
        page.keyboard.press("Escape")
        time.sleep(0.2)
    except Exception:
        pass
    for sel in ["[aria-label*='close' i]", "[role='dialog'] button"]:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible(timeout=200):
                txt = loc.inner_text()[:30] if loc.count() else ""
                if safe_to_click(txt):
                    loc.click(timeout=1500)
                    time.sleep(0.2)
                    return True
        except Exception:
            continue
    return False


def probe_url(page, path: str) -> dict | None:
    url = f"https://{ALLOWED_HOST}{path}"
    final = safe_goto(page, url, timeout=8000)
    if final is None:
        return None
    if is_session_redirect(final):
        return {"_session_dead": True}

    title = page.title()
    body_text = page.inner_text("body")[:2000]
    body_len = len(body_text.strip())
    if body_len < 80:
        return None

    final_path = final.replace(f"https://{ALLOWED_HOST}", "").split("?")[0].rstrip("/") or "/"
    rec = snapshot(page, f"nav-{path.strip('/').replace('/', '-') or 'root'}",
                   polite_delay=0)
    rec["candidate_path"] = path
    rec["final_path"] = final_path
    rec["body_length"] = body_len
    rec["body_preview"] = body_text[:300]
    return rec


def extract_loan_list(page) -> tuple[list[dict], list[str]]:
    html = page.content()
    soup = BeautifulSoup(html, "lxml")

    ids: set[str] = set()
    for a in soup.find_all("a", href=True):
        m = re.match(r"^/loans/(\d+)/?$", a.get("href", "").strip())
        if m:
            ids.add(m.group(1))

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
                    row[f"_{key}_href"] = link["href"]
                    m = re.match(r"^/loans/(\d+)/?$", link["href"])
                    if m:
                        row_id = m.group(1)
            if row_id:
                row["_loan_id"] = row_id
                rows.append(row)

    return rows, sorted(ids, key=lambda x: int(x))


def crawl_loan(page, loan_id: str) -> dict:
    base_url = f"https://{ALLOWED_HOST}/loans/{loan_id}"
    record = {"loan_id": loan_id, "url": base_url, "tabs": [], "inner_tabs": []}

    final = safe_goto(page, base_url, timeout=12000)
    if final is None or is_session_redirect(final or ""):
        record["error"] = "navigation failed or session dead"
        return record
    dismiss_any_modal(page)
    rec = snapshot(page, f"loan-{loan_id}-overview", polite_delay=LOAN_DELAY)
    record["overview"] = rec
    record["title"] = page.title()

    for tab_name in KNOWN_LOAN_TABS:
        try:
            sel = f"[role='tab']:has-text('{tab_name}'), button:has-text('{tab_name}')"
            tab = page.locator(sel).first
            if tab.count() == 0:
                continue
            if not tab.is_visible(timeout=200):
                continue
            tab.click(timeout=2500)
            time.sleep(0.5)
            tab_rec = snapshot(page, f"loan-{loan_id}-tab-{tab_name.lower()}",
                               polite_delay=LOAN_DELAY)
            tab_rec["tab"] = tab_name
            record["tabs"].append(tab_rec)
        except Exception as e:
            record.setdefault("tab_errors", {})[tab_name] = str(e)[:100]

    for tab_name in KNOWN_INNER_TABS:
        try:
            sel = f"button:has-text('{tab_name}')"
            tab = page.locator(sel).first
            if tab.count() == 0 or not tab.is_visible(timeout=200):
                continue
            tab.click(timeout=2500)
            time.sleep(0.5)
            inner = snapshot(page, f"loan-{loan_id}-inner-{tab_name.lower()}",
                             polite_delay=LOAN_DELAY)
            inner["inner_tab"] = tab_name
            record["inner_tabs"].append(inner)
        except Exception as e:
            record.setdefault("inner_tab_errors", {})[tab_name] = str(e)[:100]

    return record


def main() -> int:
    inv = {
        "captured_at": utc_now_iso(),
        "nav_probes": {},
        "loan_ids": [],
        "loans_full": [],
        "loans_list_rows": [],
    }

    with open_session(headless=True, log_navigation=False) as (browser, ctx, page):
        # Warmup: ensure we're authenticated
        print("→ Warmup: dashboard")
        final = safe_goto(page, DASHBOARD_URL, timeout=15000)
        if final is None or is_session_redirect(final or ""):
            print("✗ Session is already dead. Re-run 01_login.py first.")
            return 1
        dismiss_any_modal(page)
        print(f"  ✓ authenticated, on {final}")

        # Phase 1: probe URLs
        print(f"\n→ Phase 1: probing {len(CANDIDATE_PATHS)} candidate paths")
        for path in CANDIDATE_PATHS:
            rec = probe_url(page, path)
            if rec is None:
                print(f"  ✗ {path}")
                continue
            if rec.get("_session_dead"):
                print(f"  ⚠  SESSION DIED while probing — saving partial and aborting")
                break
            final = rec["final_path"]
            marker = "✓" if final == path else f"→ {final}"
            print(f"  {marker:>20s} {path}  ({rec['title'][:40]!r})")
            inv["nav_probes"][path] = rec
            time.sleep(PROBE_DELAY)

        # Phase 2: loans list
        print("\n→ Phase 2: /loans list extraction")
        if "/loans" in inv["nav_probes"]:
            final = safe_goto(page, f"https://{ALLOWED_HOST}/loans", timeout=15000)
            if final and not is_session_redirect(final):
                dismiss_any_modal(page)
                time.sleep(2)  # let list render
                rec = snapshot(page, "loans-list-real")
                rows, ids = extract_loan_list(page)
                inv["loans_list"] = rec
                inv["loans_list_rows"] = rows
                inv["loan_ids"] = ids
                print(f"  ✓ {len(rows)} rows, {len(ids)} unique IDs: {ids[:30]}")

                (EXTRACTED_DIR / "loans_list.yaml").write_text(
                    yaml.safe_dump(
                        {"url": rec["url"], "rows": rows, "loan_ids": ids},
                        sort_keys=False, allow_unicode=True),
                    encoding="utf-8",
                )

        # Phase 3: per-loan crawl
        if inv["loan_ids"]:
            print(f"\n→ Phase 3: crawling {len(inv['loan_ids'])} loans")
            for i, lid in enumerate(inv["loan_ids"], start=1):
                print(f"  [{i:02d}/{len(inv['loan_ids'])}] loan {lid}", end=" ", flush=True)
                rec = crawl_loan(page, lid)
                if rec.get("error"):
                    print(f"⚠ {rec['error']}")
                    if "session dead" in rec["error"]:
                        print("  ⚠ session expired — saving partial")
                        break
                else:
                    print(f"— {len(rec['tabs'])} tabs, {len(rec['inner_tabs'])} inner")
                inv["loans_full"].append(rec)
                # checkpoint every 5
                if i % 5 == 0:
                    (EXTRACTED_DIR / "loans_full_partial.yaml").write_text(
                        yaml.safe_dump({"loans": inv["loans_full"]},
                                       sort_keys=False, allow_unicode=True),
                        encoding="utf-8",
                    )

    # Save
    (EXTRACTED_DIR / "nav_probes.yaml").write_text(
        yaml.safe_dump({"probes": inv["nav_probes"]}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    (EXTRACTED_DIR / "loans_full.yaml").write_text(
        yaml.safe_dump({"loans": inv["loans_full"]}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    (EXTRACTED_DIR / "inventory_v2.yaml").write_text(
        yaml.safe_dump(inv, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    print("\n=== Summary ===")
    print(f"  Nav targets discovered: {len(inv['nav_probes'])}")
    print(f"  Loan IDs in /loans:     {len(inv['loan_ids'])}")
    print(f"  Loan detail captures:   {len(inv['loans_full'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
