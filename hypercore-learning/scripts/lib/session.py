"""
Shared session helpers for HyperCore exploration scripts.

Use:
    from lib.session import open_session, snapshot, safe_to_click

    with open_session(headless=True) as (browser, context, page):
        page.goto("https://app.hypercore.ai/dashboard")
        snapshot(page, "dashboard", out_dir=...)
"""
from __future__ import annotations

import os
import re
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUTH_STATE_FILE = PROJECT_ROOT / ".auth" / "auth_state.json"
DATA_ROOT = PROJECT_ROOT / "data"
SCREENSHOTS_DIR = DATA_ROOT / "screenshots"
HTML_DIR = DATA_ROOT / "html"
EXTRACTED_DIR = DATA_ROOT / "extracted"

# Domain allowlist
ALLOWED_HOST = "app.hypercore.ai"

# READ-ONLY safety regex — refuse to click anything matching these.
# These are state-mutating verbs in any reasonable English UI.
FORBIDDEN_VERBS = [
    r"\bsubmit\b", r"\bsave\b", r"\bdelete\b", r"\bdestroy\b", r"\bremove\b",
    r"\bpay\b", r"\bfund\b", r"\bdisburse\b", r"\bapprove\b", r"\bdeny\b",
    r"\breject\b", r"\brelease\b", r"\bcreate\b", r"\bnew\s+loan\b",
    r"\bedit\b", r"\bupdate\b", r"\barchive\b", r"\binvite\b",
    r"\badd\b", r"\bcancel\s+loan\b", r"\bconfirm\b", r"\bsign\b",
    r"\bsend\b", r"\binitiate\b", r"\bgenerate\b", r"\brevert\b",
    r"\bvoid\b", r"\boverride\b", r"\btransfer\b", r"\bwithdraw\b",
    r"\bdeposit\b", r"\bcharge\b", r"\bwaive\b", r"\bforgive\b",
]
FORBIDDEN_RE = re.compile("|".join(FORBIDDEN_VERBS), re.I)


def slugify(text: str, max_len: int = 80) -> str:
    """Filesystem-safe slug for labels."""
    if not text:
        return "page"
    s = re.sub(r"[^\w\s-]", "", text).strip()
    s = re.sub(r"[\s_-]+", "-", s)
    return (s[:max_len].lower() or "page")


def safe_to_click(text: Optional[str]) -> bool:
    """True if a button/link with this text is safe to click (read-only)."""
    if not text:
        return False
    return FORBIDDEN_RE.search(text) is None


def assert_on_hypercore(page: Page) -> None:
    """Hard assert that we're on app.hypercore.ai. Fails loud if not."""
    if ALLOWED_HOST not in page.url:
        raise RuntimeError(
            f"SAFETY: page URL {page.url!r} is not on {ALLOWED_HOST}. Aborting."
        )


def ensure_dirs() -> None:
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@contextmanager
def open_session(
    headless: bool = True,
    viewport: tuple[int, int] = (1440, 900),
    log_navigation: bool = True,
) -> Iterator[tuple[Browser, BrowserContext, Page]]:
    """Context manager that yields (browser, context, page) with the saved session."""
    if not AUTH_STATE_FILE.exists():
        raise FileNotFoundError(
            f"Auth state not found at {AUTH_STATE_FILE}. "
            f"Run scripts/01_login.py first."
        )

    ensure_dirs()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            storage_state=str(AUTH_STATE_FILE),
            viewport={"width": viewport[0], "height": viewport[1]},
        )
        page = context.new_page()

        if log_navigation:
            page.on(
                "framenavigated",
                lambda f: print(f"  [nav] {f.url}") if f == page.main_frame else None,
            )

        try:
            yield browser, context, page
        finally:
            try:
                browser.close()
            except Exception:
                pass


def snapshot(page: Page, label: str, *, polite_delay: float = 1.5) -> dict:
    """Capture a snapshot of the current page: URL, title, screenshot, HTML.

    Returns a dict with metadata. Asserts the page is on app.hypercore.ai.
    """
    assert_on_hypercore(page)

    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except PlaywrightTimeoutError:
        pass

    slug = slugify(label)
    screenshot_path = SCREENSHOTS_DIR / f"{slug}.png"
    html_path = HTML_DIR / f"{slug}.html"

    try:
        page.screenshot(path=str(screenshot_path), full_page=True)
    except Exception as e:
        print(f"  ⚠  screenshot failed for {label}: {e}")

    try:
        html_path.write_text(page.content(), encoding="utf-8")
    except Exception as e:
        print(f"  ⚠  html save failed for {label}: {e}")

    record = {
        "label": label,
        "slug": slug,
        "url": page.url,
        "title": page.title(),
        "screenshot": str(screenshot_path.relative_to(PROJECT_ROOT)),
        "html": str(html_path.relative_to(PROJECT_ROOT)),
        "captured_at": utc_now_iso(),
    }

    if polite_delay > 0:
        time.sleep(polite_delay)

    return record
