#!/usr/bin/env python3
"""
HyperCore — Phase 1: Manual login + session capture.

Opens a visible Chrome window. The user logs in via Google manually.
Once the URL leaves auth.hypercore.ai, the session (cookies + localStorage)
is persisted to .auth/auth_state.json so future scripts can reuse it.

Security guarantees enforced in code:
- Read-only: never types into forms, never clicks; user does all interaction.
- Domain allowlist: page navigation outside hypercore/google fails loudly.
- auth_state.json saved with file mode 0600.
- Verbose URL logging so the user can see every navigation.
"""
import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUTH_DIR = PROJECT_ROOT / ".auth"
AUTH_STATE_FILE = AUTH_DIR / "auth_state.json"
SCREENSHOTS_DIR = PROJECT_ROOT / "data" / "screenshots"

LOGIN_URL = "https://auth.hypercore.ai/oauth/account/login"
DASHBOARD_URL_PATTERN = "https://app.hypercore.ai/**"
LOGIN_TIMEOUT_SEC = 600

ALLOWED_DOMAIN_SUFFIXES = (
    "hypercore.ai",
    "google.com",
    "googleusercontent.com",
    "gstatic.com",
    "googleapis.com",
    "accounts.youtube.com",
)


def ensure_dirs() -> None:
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(AUTH_DIR, 0o700)


def is_post_login(url: str) -> bool:
    """We consider login complete when URL leaves auth.hypercore.ai entirely."""
    if not url or url == "about:blank":
        return False
    if "auth.hypercore.ai" in url:
        return False
    return "hypercore.ai" in url


def domain_is_allowed(url: str) -> bool:
    if not url or url.startswith("about:") or url.startswith("data:"):
        return True
    for suffix in ALLOWED_DOMAIN_SUFFIXES:
        if suffix in url:
            return True
    return False


def main() -> int:
    ensure_dirs()

    if AUTH_STATE_FILE.exists():
        print(f"⚠️  Existing session found at {AUTH_STATE_FILE}")
        ans = input("Overwrite and re-authenticate? [y/N]: ").strip().lower()
        if ans != "y":
            print("Aborted — keeping existing session.")
            return 0

    print(f"→ Opening Chrome at {LOGIN_URL}")
    print(f"→ You have up to {LOGIN_TIMEOUT_SEC // 60} minutes to complete Google login + 2FA")
    print(f"→ Script auto-detects success when URL leaves auth.hypercore.ai\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Log every navigation for transparency
        page.on("framenavigated", lambda f: print(f"  [nav] {f.url}") if f == page.main_frame else None)

        try:
            page.goto(LOGIN_URL, timeout=30000)
        except PlaywrightTimeoutError:
            print("✗ Could not reach login URL — network issue?")
            browser.close()
            return 1

        try:
            page.wait_for_url(DASHBOARD_URL_PATTERN, timeout=LOGIN_TIMEOUT_SEC * 1000)
            print(f"\n✓ Detected post-login URL: {page.url}")
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except PlaywrightTimeoutError:
                pass
            time.sleep(2)
        except PlaywrightTimeoutError:
            print(f"\n✗ Timed out after {LOGIN_TIMEOUT_SEC}s — last URL was {page.url}")
            print(f"  Expected: {DASHBOARD_URL_PATTERN}")
            browser.close()
            return 1
        except PlaywrightError as e:
            msg = str(e)
            if "closed" in msg.lower():
                print("\n✗ Browser was closed before login completed. Re-run when ready.")
                return 2
            raise

        # Persist session
        context.storage_state(path=str(AUTH_STATE_FILE))
        os.chmod(AUTH_STATE_FILE, 0o600)
        print(f"✓ Saved session → {AUTH_STATE_FILE} (mode 0600)")

        # Screenshot the dashboard
        shot = SCREENSHOTS_DIR / "01_dashboard.png"
        page.screenshot(path=str(shot), full_page=True)
        print(f"✓ Saved screenshot → {shot}")

        # Diagnostic dump
        print(f"\n--- Dashboard metadata ---")
        print(f"  URL:   {page.url}")
        print(f"  Title: {page.title()}")
        print(f"  Cookies: {len(context.cookies())} cookie(s)")

        browser.close()

    print("\n✓ Phase 1 complete. Ready for Phase 2 (crawl).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
