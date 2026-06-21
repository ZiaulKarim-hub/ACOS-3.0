"""Quick path-probe to find the real loans list URL."""
import sys, time, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.session import open_session, ALLOWED_HOST

PATHS_TO_CHECK = [
    "/loans", "/loan", "/portfolio", "/clients", "/client", "/customers",
    "/reports", "/settings", "/team", "/products", "/loan-types",
    "/payments", "/documents", "/investors", "/main", "/app/loans",
]

with open_session(headless=True, log_navigation=False) as (browser, ctx, page):
    for p in PATHS_TO_CHECK:
        url = f"https://{ALLOWED_HOST}{p}"
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
        except Exception as e:
            print(f"{p:20s}  GOTO ERR: {e}")
            continue
        time.sleep(4)  # wait for SPA to render lazy data
        final = page.url
        final_path = final.replace(f"https://{ALLOWED_HOST}", "")
        body = page.inner_text("body")
        html = page.content()
        loan_links = len(re.findall(r"/loans/\d+", html))
        body_preview = body[:200].replace("\n", " | ")
        print(f"{p:18s} -> {final_path:30s}  body={len(body):5d}  loanlinks={loan_links:3d}  preview: {body_preview[:120]}")
