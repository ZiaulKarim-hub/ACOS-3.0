"""Verify session by hitting /dashboard with longer waits."""
import sys, time, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.session import open_session, ALLOWED_HOST

with open_session(headless=True, log_navigation=True) as (browser, ctx, page):
    print("→ Going to /dashboard")
    page.goto(f"https://{ALLOWED_HOST}/dashboard", wait_until="domcontentloaded", timeout=20000)
    print(f"  immediate URL: {page.url}")

    # Sample at multiple delays
    for delay in [1, 2, 3, 5, 8]:
        time.sleep(1 if delay == 1 else delay - {1: 0, 2: 1, 3: 2, 5: 3, 8: 5}[delay])
        body = page.inner_text("body")
        html = page.content()
        loan_links = len(re.findall(r"/loans/\d+", html))
        print(f"  [t={delay}s] url={page.url[:60]:60s}  body={len(body):6d}  /loans/N={loan_links}")

    body_preview = page.inner_text("body")[:500].replace("\n", " | ")
    print(f"\nFinal body preview: {body_preview}")

    # Save dashboard HTML for inspection
    Path("data/html/dashboard_v2_debug.html").write_text(page.content(), encoding="utf-8")
    print(f"\nSaved → data/html/dashboard_v2_debug.html")
