"""
Summit County Treasurer — Property Tax Scraper
Scrapes tax data for Ascent Park City condo units from the Summit County
Treasurer EagleWeb portal using Playwright browser automation.

Usage:
    source /tmp/scraper-venv/bin/activate
    python3 scrape_summit_taxes.py
"""
import csv
import re
import sys
import time
from playwright.sync_api import sync_playwright

PARCELS = [
    "APC-101", "APC-102", "APC-103", "APC-104", "APC-105", "APC-106", "APC-107", "APC-108",
    "APC-109", "APC-110", "APC-111", "APC-112", "APC-113", "APC-114", "APC-116", "APC-118",
    "APC-120", "APC-122", "APC-124", "APC-126", "APC-139", "APC-141", "APC-143", "APC-144",
    "APC-145", "APC-146", "APC-147", "APC-148", "APC-149", "APC-150", "APC-151", "APC-152",
    "APC-153", "APC-154", "APC-155", "APC-156", "APC-201", "APC-202", "APC-203", "APC-204",
    "APC-205", "APC-206", "APC-207", "APC-208", "APC-209", "APC-210", "APC-211", "APC-212",
    "APC-213", "APC-214", "APC-216", "APC-218", "APC-220", "APC-222", "APC-224", "APC-226",
    "APC-228", "APC-230", "APC-232", "APC-234", "APC-235", "APC-237", "APC-239", "APC-241",
    "APC-243", "APC-244", "APC-245", "APC-246", "APC-247", "APC-248", "APC-249", "APC-250",
    "APC-251", "APC-252", "APC-253", "APC-254", "APC-255", "APC-256", "APC-301", "APC-302",
    "APC-303", "APC-304", "APC-305", "APC-306", "APC-307", "APC-308", "APC-309", "APC-310",
    "APC-311", "APC-312", "APC-313", "APC-314", "APC-316", "APC-318", "APC-320", "APC-322",
    "APC-326", "APC-328", "APC-330", "APC-332", "APC-334", "APC-335", "APC-337", "APC-339",
    "APC-341", "APC-343", "APC-344", "APC-345", "APC-346", "APC-347", "APC-348", "APC-349",
    "APC-350", "APC-351", "APC-352", "APC-353", "APC-354", "APC-356", "APC-324", "APC-355",
    "APC-D-1", "APC-H-1",
]

OUTPUT_CSV = "ascent_park_city_taxes.csv"
BASE_URL = "https://treasurer.summitcounty.org/treasurer"


def parse_currency(text):
    """Extract dollar amount from text like '$1,677.58' or 'Balance: 1677.58'."""
    match = re.search(r'\$?([\d,]+\.?\d*)', text.replace(',', ''))
    if match:
        return match.group(0).lstrip('$')
    return "0.00"


def extract_tax_data(page, parcel_id):
    """Search for a parcel and extract tax data from the account page."""
    # Navigate to search page
    page.goto(f"{BASE_URL}/treasurerweb/search.jsp", timeout=30000)
    page.wait_for_selector("#TaxAcctParcelID", timeout=10000)

    # Clear and fill parcel number
    page.fill("#TaxAcctParcelID", "")
    page.fill("#TaxAcctParcelID", parcel_id)
    time.sleep(0.3)

    # Submit search
    page.click("input[value='Search for Accounts']")
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(1)

    # Check for results
    text = page.inner_text("body")

    if "No items found" in text or "0 items found" in text:
        return {
            "parcel_number": parcel_id,
            "account_id": "",
            "owner": "",
            "situs_address": "",
            "taxes_due": "",
            "interest_due": "",
            "penalty_due": "",
            "total_due": "",
            "assessed_value": "",
            "tax_rate": "",
            "status": "NOT FOUND",
        }

    # Extract account ID from the search results link
    account_link = page.query_selector("a[href*='account.jsp?account=']")
    if not account_link:
        return {
            "parcel_number": parcel_id,
            "account_id": "",
            "owner": "",
            "situs_address": "",
            "taxes_due": "",
            "interest_due": "",
            "penalty_due": "",
            "total_due": "",
            "assessed_value": "",
            "tax_rate": "",
            "status": "NO LINK FOUND",
        }

    href = account_link.get_attribute("href")
    account_match = re.search(r'account=(\d+)', href)
    account_id = account_match.group(1) if account_match else ""

    # Navigate to account detail page
    page.goto(f"{BASE_URL}/treasurerweb/account.jsp?account={account_id}", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(1)

    body = page.inner_text("body")
    # Normalize non-breaking spaces (\xa0) to regular spaces for regex matching
    body = body.replace('\xa0', ' ')

    # Extract fields using regex
    def extract_field(pattern, text):
        m = re.search(pattern, text)
        return m.group(1).strip() if m else ""

    owner = extract_field(r'Owners\s+(.+?)(?:\n|Address)', body)
    situs = extract_field(r'Situs Address\t(.+?)(?:\n|Legal)', body)
    taxes_due = extract_field(r'Taxes Due\t\$([\d,]+\.?\d*)', body)
    interest_due = extract_field(r'Interest Due\t\$([\d,]+\.?\d*)', body)
    penalty_due = extract_field(r'Penalty Due\t\$([\d,]+\.?\d*)', body)
    total_due = extract_field(r'Total Due\t\$([\d,]+\.?\d*)', body)
    tax_rate = extract_field(r'(0\.00\d+)', body)
    assessed = extract_field(r'Assessed\n.+?\t([\d,]+)\t[\d,]+\nTaxes', body)

    return {
        "parcel_number": parcel_id,
        "account_id": account_id,
        "owner": owner,
        "situs_address": situs,
        "taxes_due": taxes_due,
        "interest_due": interest_due,
        "penalty_due": penalty_due,
        "total_due": total_due,
        "assessed_value": assessed,
        "tax_rate": tax_rate,
        "status": "OK",
    }


def main():
    results = []
    errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Guest login first
        print("Logging in as guest...")
        page.goto(f"{BASE_URL}/web/login.jsp", timeout=30000)
        time.sleep(1)
        page.click("input[name='submit']", timeout=5000)
        time.sleep(2)
        print(f"Logged in. Starting scrape of {len(PARCELS)} parcels...\n")

        for i, parcel in enumerate(PARCELS, 1):
            try:
                data = extract_tax_data(page, parcel)
                results.append(data)
                status = data["status"]
                total = data.get("total_due", "N/A")
                print(f"[{i:3d}/{len(PARCELS)}] {parcel:10s} | Total Due: ${total:>12s} | {status}")
            except Exception as e:
                error_msg = str(e)[:80]
                print(f"[{i:3d}/{len(PARCELS)}] {parcel:10s} | ERROR: {error_msg}")
                errors.append(parcel)
                results.append({
                    "parcel_number": parcel,
                    "account_id": "",
                    "owner": "",
                    "situs_address": "",
                    "taxes_due": "",
                    "interest_due": "",
                    "penalty_due": "",
                    "total_due": "",
                    "assessed_value": "",
                    "tax_rate": "",
                    "status": f"ERROR: {error_msg}",
                })
                # Re-login if session broke
                try:
                    page.goto(f"{BASE_URL}/web/login.jsp", timeout=15000)
                    time.sleep(1)
                    page.click("input[name='submit']", timeout=5000)
                    time.sleep(2)
                except:
                    pass

        browser.close()

    # Write CSV
    fieldnames = [
        "parcel_number", "account_id", "owner", "situs_address",
        "taxes_due", "interest_due", "penalty_due", "total_due",
        "assessed_value", "tax_rate", "status",
    ]
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n{'='*60}")
    print(f"Done! {len(results)} parcels written to {OUTPUT_CSV}")
    if errors:
        print(f"Errors on {len(errors)} parcels: {', '.join(errors)}")
    print(f"{'='*60}")

    # Print summary
    ok_results = [r for r in results if r["status"] == "OK" and r["total_due"]]
    if ok_results:
        total_taxes = sum(float(r["taxes_due"].replace(",", "") or 0) for r in ok_results)
        total_interest = sum(float(r["interest_due"].replace(",", "") or 0) for r in ok_results)
        total_penalty = sum(float(r["penalty_due"].replace(",", "") or 0) for r in ok_results)
        grand_total = sum(float(r["total_due"].replace(",", "") or 0) for r in ok_results)
        print(f"\nSummary ({len(ok_results)} parcels with data):")
        print(f"  Total Taxes Assessed:  ${total_taxes:>12,.2f}")
        print(f"  Total Interest Due:    ${total_interest:>12,.2f}")
        print(f"  Total Penalty Due:     ${total_penalty:>12,.2f}")
        print(f"  Grand Total Due:       ${grand_total:>12,.2f}")


if __name__ == "__main__":
    main()
