"""Analyze all existing captured HTML to extract maximum data."""
import re
from pathlib import Path
from collections import Counter, defaultdict
import yaml

HTML_DIR = Path("data/html")
EXTRACTED = Path("data/extracted")

# Step 1: Discover all unique loan IDs across every file
all_loan_ids = set()
files_per_loan = defaultdict(list)

for html_file in sorted(HTML_DIR.glob("*.html")):
    text = html_file.read_text()
    ids = set(re.findall(r"/loans/(\d+)", text))
    all_loan_ids |= ids
    for lid in ids:
        files_per_loan[lid].append(html_file.name)

print(f"=== Loan IDs discovered across all captures ===")
print(f"Total unique IDs: {len(all_loan_ids)}")
sorted_ids = sorted(all_loan_ids, key=lambda x: int(x))
print(f"IDs: {', '.join(sorted_ids)}")
print()

# Step 2: For each loan, what files have its data?
print(f"=== Coverage per loan ===")
print(f"{'loan_id':>8s}  {'#files':>7s}  example files")
for lid in sorted_ids:
    files = files_per_loan[lid]
    examples = [f for f in files if f"loan-{lid}-" in f or f"/loans/{lid}" in f or f"section-" in f][:3]
    print(f"{lid:>8s}  {len(files):>7d}  {examples[:2]}")
print()

# Step 3: Files that look like a single-loan-detail page (contain a unique loan path)
loan_detail_pages = []
for html_file in sorted(HTML_DIR.glob("*.html")):
    text = html_file.read_text()
    # Look for pages where one loan ID is heavily referenced
    counts = Counter(re.findall(r"/loans/(\d+)", text))
    if not counts:
        continue
    top, top_count = counts.most_common(1)[0]
    others = sum(c for i, c in counts.items() if i != top)
    if top_count > 10 and top_count > others:
        loan_detail_pages.append((html_file.name, top, top_count, others))

print(f"=== Files that are loan-detail pages ===")
print(f"{'file':<55s} {'main_loan':>10s} {'main_count':>10s} {'other_count':>11s}")
for fname, top, tc, oc in loan_detail_pages[:40]:
    print(f"{fname[:54]:<55s} {top:>10s} {tc:>10d} {oc:>11d}")

# Step 4: How many loan-detail pages do we have per loan?
detail_per_loan = defaultdict(list)
for fname, lid, _, _ in loan_detail_pages:
    detail_per_loan[lid].append(fname)
print(f"\n=== Detail pages per loan ===")
print(f"Loans with detail captures: {len(detail_per_loan)}")
for lid in sorted(detail_per_loan, key=lambda x: int(x)):
    print(f"  Loan {lid}: {len(detail_per_loan[lid])} files — {detail_per_loan[lid][:2]}")

# Save findings
findings = {
    "all_loan_ids_seen": sorted_ids,
    "total_unique_loans": len(all_loan_ids),
    "loans_with_detail_capture": list(detail_per_loan.keys()),
    "detail_files_per_loan": {k: v for k, v in detail_per_loan.items()},
}
EXTRACTED.mkdir(exist_ok=True)
(EXTRACTED / "coverage_analysis.yaml").write_text(
    yaml.safe_dump(findings, sort_keys=False, allow_unicode=True), encoding="utf-8"
)
print(f"\n✓ Saved coverage analysis → data/extracted/coverage_analysis.yaml")
