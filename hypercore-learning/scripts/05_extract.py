"""Extract structured loan data from captured HTML files."""
import re
import json
from pathlib import Path
from collections import defaultdict
import yaml
from bs4 import BeautifulSoup

HTML_DIR = Path("data/html")
EXTRACTED = Path("data/extracted")
EXTRACTED.mkdir(exist_ok=True)


def map_file_to_loan_id(filename: str) -> str | None:
    """Determine which loan ID a captured file represents."""
    # 1. Sample loans were re-numbered as loan-01 (=57) and loan-02 (=167)
    if re.match(r"^loan-01-", filename):
        return "57"
    if re.match(r"^loan-02-", filename):
        return "167"
    # 2. Section files have notification text in filename containing the loan number
    m = re.search(r"loan-(\d+)", filename)
    if m:
        return m.group(1)
    # 3. New nav-* files don't represent specific loans
    return None


def file_role(filename: str) -> str:
    """What part of a loan does this file capture?"""
    if "tab-01-info" in filename:
        return "tab_info"
    if "tab-02-terms" in filename:
        return "tab_terms"
    if "tab-03-notes" in filename:
        return "tab_notes"
    if "tab-04-docs" in filename:
        return "tab_files"
    if "overview" in filename:
        return "overview"
    if "section-" in filename:
        return "section_default"
    if filename.startswith("nav-"):
        return "nav_page"
    if filename.startswith("01-dashboard") or "dashboard" in filename:
        return "dashboard"
    if "loans-list" in filename:
        return "loans_list_visit"
    return "other"


def extract_label_value_pairs(html: str) -> dict[str, str]:
    """Extract field/value pairs from a loan detail page.

    HyperCore uses a Material/Tailwind layout where labels and values are
    paired as adjacent <div>s or <span>s. Heuristic: look for short text nodes
    followed by longer text nodes.
    """
    soup = BeautifulSoup(html, "lxml")
    pairs: dict[str, str] = {}

    # Strategy: find dl/dt/dd patterns
    for dl in soup.find_all("dl"):
        for dt in dl.find_all("dt"):
            dd = dt.find_next_sibling("dd")
            if dd:
                pairs[dt.get_text(strip=True)] = dd.get_text(" ", strip=True)

    # Strategy: find label/value divs paired side by side
    # HyperCore uses: <div class="label">Name</div><div class="value">Val</div>
    for label in soup.find_all(class_=re.compile(r"label", re.I)):
        nxt = label.find_next_sibling()
        if nxt:
            k = label.get_text(strip=True)
            v = nxt.get_text(" ", strip=True)
            if k and v and len(k) < 60 and k not in pairs:
                pairs[k] = v

    return pairs


def extract_loan_summary(html: str) -> dict:
    """Best-effort extraction of loan-detail-page summary data."""
    soup = BeautifulSoup(html, "lxml")
    summary = {}

    # Page heading typically: "Loan #57 - Murdock - Oberland"
    h_text = ""
    for h in soup.find_all(["h1", "h2"]):
        t = h.get_text(strip=True)
        if "Loan #" in t:
            h_text = t
            break
    if h_text:
        summary["heading"] = h_text
        m = re.match(r"Loan\s*#?(\d+)\s*[-–]\s*(.+)", h_text)
        if m:
            summary["loan_id_from_heading"] = m.group(1)
            summary["client_or_name"] = m.group(2).strip()

    # Look for status indicators
    for span in soup.find_all(["span", "div", "p"]):
        t = span.get_text(strip=True)
        if t in {"Closed", "Active", "Pending", "Funded", "Disbursed",
                 "Matured", "Default", "Performing", "Non-Performing"}:
            summary["status_observed"] = t
            break

    # Extract every text node that contains a $ amount
    text = soup.get_text(" ", strip=True)
    money_amounts = re.findall(r"\$[\d,]+(?:\.\d{2})?[KMB]?", text)
    if money_amounts:
        summary["money_amounts_found"] = list(set(money_amounts))[:30]

    # Extract percentages
    pcts = re.findall(r"\d+(?:\.\d+)?%", text)
    if pcts:
        summary["percentages_found"] = list(set(pcts))[:20]

    # Extract dates (DD MMM YYYY or MM/DD/YYYY)
    date_pat1 = r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}"
    date_pat2 = r"\d{1,2}/\d{1,2}/\d{4}"
    dates = list(set(re.findall(date_pat1, text) + re.findall(date_pat2, text)))[:20]
    if dates:
        summary["dates_found"] = dates

    # Label-value pairs
    pairs = extract_label_value_pairs(html)
    if pairs:
        summary["fields"] = pairs

    summary["html_length"] = len(html)
    summary["body_text_length"] = len(text)

    return summary


def main():
    files = sorted(HTML_DIR.glob("*.html"))
    print(f"Total HTML files: {len(files)}")

    by_loan = defaultdict(lambda: {"loan_id": None, "files": [], "summary": {}})

    for f in files:
        loan_id = map_file_to_loan_id(f.name)
        role = file_role(f.name)
        if loan_id is None:
            continue

        html = f.read_text()
        info = {"filename": f.name, "role": role, "size": len(html)}

        # Extract summary only for the "main" page (overview or section_default)
        if role in {"overview", "section_default"} and not by_loan[loan_id]["summary"]:
            by_loan[loan_id]["summary"] = extract_loan_summary(html)

        by_loan[loan_id]["loan_id"] = loan_id
        by_loan[loan_id]["files"].append(info)

    # Save per-loan YAMLs
    LOAN_DIR = Path("data/loans")
    LOAN_DIR.mkdir(exist_ok=True)
    for lid, data in by_loan.items():
        (LOAN_DIR / f"loan_{lid}.yaml").write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    # Master summary
    master = {
        "loans_analyzed": sorted(by_loan.keys(), key=lambda x: int(x)),
        "loans_with_summary": sorted(
            [k for k, v in by_loan.items() if v["summary"]],
            key=lambda x: int(x)
        ),
        "loans_count": len(by_loan),
    }
    (EXTRACTED / "loans_master.yaml").write_text(
        yaml.safe_dump(master, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    print(f"\n=== Extracted ===")
    print(f"Loans with any data:      {len(by_loan)}")
    print(f"Loans with summary data:  {len(master['loans_with_summary'])}")
    print(f"Per-loan YAMLs written to data/loans/")
    print(f"\nLoans found: {', '.join(master['loans_analyzed'])}")

    # Show sample summary for loan 57
    if "57" in by_loan:
        print(f"\n=== Sample: Loan 57 ===")
        s = by_loan["57"]["summary"]
        for k, v in s.items():
            if isinstance(v, list):
                print(f"  {k}: {v[:5]}{'…' if len(v) > 5 else ''}")
            elif isinstance(v, dict):
                print(f"  {k}: {len(v)} entries")
            else:
                print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
