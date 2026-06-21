"""
Thurston Lux 2 — Multi-County Property Tax Scraper

Reads parcels.csv, dispatches per jurisdiction, writes timestamped status CSV
plus a PNG screenshot per parcel for audit.

Jurisdictions:
  - Wasatch County, UT     (automatable — EmpRep portal)
  - Utah County, UT        (automatable — treasurer + land records)
  - Kauai County, HI       (automatable — kauairpt.ehawaii.gov)
  - Miami-Dade County, FL  (automatable — TaxSys)
  - CRIM (PR)              (manual only — catastro + SSN required)

Usage:
    source /tmp/scraper-venv/bin/activate   # same venv as scrape_summit_taxes.py
    python3 scrape_lux2_taxes.py                              # run all
    python3 scrape_lux2_taxes.py --parcel LUX2-02             # one parcel
    python3 scrape_lux2_taxes.py --county "Kauai County"      # one jurisdiction
    python3 scrape_lux2_taxes.py --headful                    # show browser
    python3 scrape_lux2_taxes.py --debug                      # pause before each nav

Selectors were written against portal layouts as of April 2026. Portals change.
If a county returns ``parse_failed``, run with ``--headful --debug`` to inspect.
"""
import argparse
import csv
import datetime as dt
import re
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from playwright.sync_api import Page, TimeoutError as PWTimeout, sync_playwright

ROOT = Path(__file__).parent
PARCELS_CSV = ROOT / "parcels.csv"
TODAY = dt.date.today().isoformat()
STATUS_CSV = ROOT / f"lux2_tax_status_{TODAY}.csv"
SCREENSHOT_DIR = ROOT / "screenshots" / TODAY

STATUS_COLUMNS = [
    "property_id", "property_name", "address", "jurisdiction", "parcel_id",
    "current_year_taxes", "prior_year_delinquent", "total_due",
    "last_payment_date", "next_due_date", "status", "source_url",
    "checked_at", "notes",
]


@dataclass
class Parcel:
    property_id: str
    property_name: str
    address: str
    city: str
    state: str
    jurisdiction: str
    entity_owner: str
    parcel_id: str
    parcel_id_format: str
    title_file_ref: str
    portal_url: str
    notes: str

    @property
    def needs_parcel(self) -> bool:
        return self.parcel_id.strip().upper() == "TODO"


@dataclass
class Result:
    property_id: str
    property_name: str
    address: str
    jurisdiction: str
    parcel_id: str
    current_year_taxes: str = ""
    prior_year_delinquent: str = ""
    total_due: str = ""
    last_payment_date: str = ""
    next_due_date: str = ""
    status: str = "pending"
    source_url: str = ""
    checked_at: str = field(default_factory=lambda: dt.datetime.now().isoformat(timespec="seconds"))
    notes: str = ""

    def to_row(self) -> dict:
        return {k: getattr(self, k) for k in STATUS_COLUMNS}


def read_parcels() -> list[Parcel]:
    with PARCELS_CSV.open(newline="") as f:
        return [
            Parcel(
                property_id=row["property_id"],
                property_name=row["property_name"],
                address=row["address"],
                city=row["city"],
                state=row["state"],
                jurisdiction=row["county_or_jurisdiction"],
                entity_owner=row["entity_owner"],
                parcel_id=row["parcel_id"],
                parcel_id_format=row["parcel_id_format"],
                title_file_ref=row["title_file_ref"],
                portal_url=row["portal_url"],
                notes=row["notes"],
            )
            for row in csv.DictReader(f)
        ]


def parse_currency(text: str) -> str:
    if not text:
        return ""
    m = re.search(r"\$?\s*([\d,]+\.\d{2}|\d{1,3}(?:,\d{3})+|\d+)", text)
    return m.group(1).replace(",", "") if m else ""


def screenshot(page: Page, parcel: Parcel, tag: str = "result") -> str:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SCREENSHOT_DIR / f"{parcel.property_id}_{tag}.png"
    try:
        page.screenshot(path=str(path), full_page=True)
    except Exception:
        pass
    return str(path)


def scrape_wasatch(page: Page, parcel: Parcel) -> Result:
    # Wasatch County EmpRep portal. Supports owner-name or parcel search.
    # Landing page has a serial/parcel number field.
    r = Result(
        property_id=parcel.property_id, property_name=parcel.property_name,
        address=parcel.address, jurisdiction=parcel.jurisdiction,
        parcel_id=parcel.parcel_id, source_url=parcel.portal_url,
    )
    page.goto(parcel.portal_url, wait_until="domcontentloaded", timeout=60_000)
    # Try parcel first; if TODO, fall back to owner entity
    search_text = parcel.parcel_id if not parcel.needs_parcel else parcel.entity_owner
    try:
        # EmpRep forms historically expose an input named like "CriteriaText" or similar
        box = page.locator("input[type='text']").first
        box.fill(search_text)
        page.locator("input[type='submit'], button[type='submit']").first.click()
        page.wait_for_load_state("domcontentloaded", timeout=30_000)
        body = page.inner_text("body")
        r.current_year_taxes = parse_currency(_after(body, "Current Tax"))
        r.total_due = parse_currency(_after(body, "Total Due")) or parse_currency(_after(body, "Balance"))
        r.status = "parsed" if r.total_due or r.current_year_taxes else "parse_failed"
        r.notes = "Wasatch portal — verify result matches address; back-tax payoff via taxpayoff@wasatch.utah.gov"
    except PWTimeout:
        r.status = "timeout"
    screenshot(page, parcel)
    return r


def scrape_utah_county(page: Page, parcel: Parcel) -> Result:
    # Utah County: resolve address -> serial via Land Records, then Treasurer for balance.
    r = Result(
        property_id=parcel.property_id, property_name=parcel.property_name,
        address=parcel.address, jurisdiction=parcel.jurisdiction,
        parcel_id=parcel.parcel_id, source_url=parcel.portal_url,
    )
    serial = parcel.parcel_id if not parcel.needs_parcel else ""
    if not serial:
        page.goto("https://www.utahcounty.gov/landrecords/AddressSearchForm.asp",
                  wait_until="domcontentloaded", timeout=60_000)
        try:
            # Address search form — exact field names vary; try common labels
            page.fill("input[name*='address' i], input[name='House'], input[name*='Street' i]",
                      parcel.address)
            page.locator("input[type='submit'], button[type='submit']").first.click()
            page.wait_for_load_state("domcontentloaded", timeout=30_000)
            body = page.inner_text("body")
            m = re.search(r"\b\d{2}:\d{3}:\d{4}\b", body)
            if m:
                serial = m.group(0)
                r.parcel_id = serial
                r.notes = f"resolved serial from address: {serial}"
        except PWTimeout:
            r.status = "address_resolve_timeout"
            screenshot(page, parcel, tag="landrecords")
            return r

    if serial:
        page.goto(f"https://treasurer.utahcounty.gov/?serial={serial}",
                  wait_until="domcontentloaded", timeout=60_000)
        body = page.inner_text("body")
        r.current_year_taxes = parse_currency(_after(body, "Current Tax"))
        r.total_due = parse_currency(_after(body, "Total Due")) or parse_currency(_after(body, "Balance Due"))
        r.status = "parsed" if r.total_due or r.current_year_taxes else "parse_failed"
    else:
        r.status = "no_serial"
    screenshot(page, parcel)
    return r


def scrape_kauai(page: Page, parcel: Parcel) -> Result:
    # Kauai eHawaii Real Property Tax Payment portal. Search by TMK.
    r = Result(
        property_id=parcel.property_id, property_name=parcel.property_name,
        address=parcel.address, jurisdiction=parcel.jurisdiction,
        parcel_id=parcel.parcel_id, source_url=parcel.portal_url,
    )
    if parcel.needs_parcel:
        r.status = "no_parcel"
        return r
    page.goto("https://kauairpt.ehawaii.gov/propertytax/", wait_until="domcontentloaded", timeout=60_000)
    try:
        tmk = parcel.parcel_id.replace("-", "")  # 13-digit TMK (no owner sequence) is accepted
        # Portal layout confirmed from screenshot: label "TMK" above the input, T&C checkbox
        # gates the Search button. get_by_label / get_by_role selectors are more robust than
        # input[type=...] for this JS-rendered form.
        page.get_by_label("TMK", exact=False).fill(tmk)
        page.get_by_label("I have read, understand", exact=False).check()
        page.get_by_role("button", name="Search").click()
        # Tyler Technologies flow: (1) button shows "Searching..." then (2) a "Loading Invoice..."
        # modal overlays the page then (3) modal disappears + invoice content renders.
        # Wait for loading modal to appear, then for it to disappear, then for $ sign in body.
        try:
            page.wait_for_selector("text=Loading Invoice", state="visible", timeout=15_000)
            page.wait_for_selector("text=Loading Invoice", state="detached", timeout=60_000)
        except PWTimeout:
            pass
        try:
            page.wait_for_function(
                "() => document.body.innerText.includes('$')",
                timeout=15_000,
            )
        except PWTimeout:
            pass
        body = page.inner_text("body")
        # Kauai portal labels are specific — parse them directly
        r.current_year_taxes = parse_currency(_after(body, "Tax Amount"))
        r.prior_year_delinquent = parse_currency(_after(body, "Penalty Amount"))
        r.total_due = parse_currency(_after(body, "Amount Due Now")) or parse_currency(_after(body, "Total Due"))
        nd = re.search(r"Due Date\s*(\d{4}-\d{2}-\d{2})", body)
        if nd:
            r.next_due_date = nd.group(1)
        st = re.search(r"Status\s*(Past Due|Current|Delinquent|Paid)", body, re.I)
        interest = parse_currency(_after(body, "Interest Amount"))
        period = re.search(r"Period\s*([\d-]+)", body)
        r.notes = (
            f"HI semiannual Aug 20 + Feb 20. "
            f"status={st.group(1) if st else 'unknown'}, "
            f"period={period.group(1) if period else '?'}, "
            f"interest={interest}, "
            f"penalty={r.prior_year_delinquent}"
        )
        r.status = "parsed" if r.total_due else "parse_failed"
        screenshot(page, parcel)
        return r
        body = page.inner_text("body")
        r.current_year_taxes = parse_currency(_after(body, "Current"))
        r.prior_year_delinquent = parse_currency(_after(body, "Delinquent")) or parse_currency(_after(body, "Prior"))
        r.total_due = parse_currency(_after(body, "Total Due")) or parse_currency(_after(body, "Balance"))
        r.status = "parsed" if r.total_due or r.current_year_taxes else "parse_failed"
        r.notes = "HI semiannual: Aug 20 + Feb 20 installments"
    except PWTimeout:
        r.status = "timeout"
    screenshot(page, parcel)
    return r


def scrape_miami_dade(page: Page, parcel: Parcel) -> Result:
    # Miami-Dade TaxSys. Search by address; TaxSys accepts partial address queries.
    r = Result(
        property_id=parcel.property_id, property_name=parcel.property_name,
        address=parcel.address, jurisdiction=parcel.jurisdiction,
        parcel_id=parcel.parcel_id, source_url=parcel.portal_url,
    )
    page.goto("https://miamidade.county-taxes.com/public/search/property_tax",
              wait_until="domcontentloaded", timeout=60_000)
    try:
        query = parcel.parcel_id if not parcel.needs_parcel else parcel.address
        page.fill("input[type='search'], input[type='text']", query)
        page.keyboard.press("Enter")
        page.wait_for_load_state("domcontentloaded", timeout=30_000)
        # Click first result
        first = page.locator("a.result, a[href*='/public/real_estate/']").first
        if first.count():
            first.click()
            page.wait_for_load_state("domcontentloaded", timeout=30_000)
        body = page.inner_text("body")
        r.current_year_taxes = parse_currency(_after(body, "Current Tax Bill"))
        r.total_due = parse_currency(_after(body, "Total Due")) or parse_currency(_after(body, "Amount Due"))
        r.status = "parsed" if r.total_due or r.current_year_taxes else "parse_failed"
        m = re.search(r"\b\d{2}-\d{4}-\d{3}-\d{4}\b", body)
        if m:
            r.parcel_id = m.group(0)
        r.notes = "FL: delinquent Apr 1; tax certificate auction Jun 1"
    except PWTimeout:
        r.status = "timeout"
    screenshot(page, parcel)
    return r


def scrape_crim_manual(page: Page, parcel: Parcel) -> Result:
    return Result(
        property_id=parcel.property_id, property_name=parcel.property_name,
        address=parcel.address, jurisdiction=parcel.jurisdiction,
        parcel_id=parcel.parcel_id, source_url="https://www.crimpr.net/",
        status="manual_required",
        notes=("CRIM requires catastro + SSN (or authorized agent). "
               "Order a Debt Certificate (Certificación de Deuda) via PR title "
               "company (First American — see Title/ALTA files) or PR counsel."),
    )


DISPATCH: dict[str, Callable[[Page, Parcel], Result]] = {
    "Wasatch County": scrape_wasatch,
    "Utah County": scrape_utah_county,
    "Kauai County": scrape_kauai,
    "Miami-Dade County": scrape_miami_dade,
    "CRIM (Municipio de Dorado)": scrape_crim_manual,
}


def _after(haystack: str, label: str) -> str:
    m = re.search(rf"{re.escape(label)}[^\$\d]*\$?\s*([\d,]+\.\d{{2}})", haystack, re.I)
    return m.group(0) if m else ""


def run(parcels: list[Parcel], headful: bool, debug: bool) -> list[Result]:
    results: list[Result] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headful)
        context = browser.new_context()
        page = context.new_page()
        for parcel in parcels:
            scraper = DISPATCH.get(parcel.jurisdiction)
            print(f"[{parcel.property_id}] {parcel.property_name} — {parcel.jurisdiction}")
            if scraper is None:
                results.append(Result(
                    property_id=parcel.property_id, property_name=parcel.property_name,
                    address=parcel.address, jurisdiction=parcel.jurisdiction,
                    parcel_id=parcel.parcel_id, status="no_dispatcher",
                ))
                continue
            if debug:
                input(f"  press enter to run {scraper.__name__}... ")
            try:
                results.append(scraper(page, parcel))
            except Exception as exc:
                traceback.print_exc()
                results.append(Result(
                    property_id=parcel.property_id, property_name=parcel.property_name,
                    address=parcel.address, jurisdiction=parcel.jurisdiction,
                    parcel_id=parcel.parcel_id, status=f"error: {type(exc).__name__}",
                    notes=str(exc)[:200],
                ))
        browser.close()
    return results


def write_status(results: list[Result]) -> None:
    with STATUS_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=STATUS_COLUMNS)
        writer.writeheader()
        for r in results:
            writer.writerow(r.to_row())
    print(f"\nwrote {STATUS_CSV}")
    print(f"screenshots: {SCREENSHOT_DIR}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parcel", help="run only this property_id (e.g. LUX2-02)")
    ap.add_argument("--county", help="run only this jurisdiction (exact match)")
    ap.add_argument("--headful", action="store_true", help="show browser window")
    ap.add_argument("--debug", action="store_true", help="pause before each scrape")
    args = ap.parse_args()

    parcels = read_parcels()
    if args.parcel:
        parcels = [p for p in parcels if p.property_id == args.parcel]
    if args.county:
        parcels = [p for p in parcels if p.jurisdiction == args.county]
    if not parcels:
        print("no parcels matched filter", file=sys.stderr)
        return 2

    print(f"running {len(parcels)} parcel(s), today={TODAY}")
    results = run(parcels, headful=args.headful, debug=args.debug)
    write_status(results)

    by_status: dict[str, int] = {}
    for r in results:
        by_status[r.status] = by_status.get(r.status, 0) + 1
    print("\nsummary:")
    for status, count in sorted(by_status.items()):
        print(f"  {status:20s} {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
