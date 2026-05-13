"""Generate a synthetic 10-file source folder for acos-dataroom-v2 smoke testing.

Creates an isolated folder with files designed to exercise the pipeline's main
decision paths:
  - 3 clearly-relevant files (should pass Phase 2 INCLUDE consensus)
  - 3 clearly-irrelevant files (other-property docs; should pass Phase 2 EXCLUDE
    consensus)
  - 1 privileged document (sample attorney memo; should be removed by Phase 2.5)
  - 1 encrypted PDF (placeholder — flagged for manual review)
  - 1 zero-byte file (flagged for manual review)
  - 1 ambiguous-relevance file (intended to trigger split deliberation → re-dispatch)

CLI usage:
  python3 generate_synthetic_source.py --output /tmp/acos_dr2_smoke_src
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


# Synthetic file definitions: (relative_path, content_lines)
SYNTHETIC_FILES: list[tuple[str, list[str]]] = [
    # --- 3 clearly-relevant: Ascent Hotel docs ---
    (
        "Property/Ascent_Hotel_Overview.txt",
        [
            "ASCENT PARK CITY HOTEL — PROPERTY OVERVIEW",
            "",
            "Asset: 75-key luxury hotel, Waldorf-Astoria flagged",
            "Location: Park City, Utah",
            "Owner: LKCap Okoa Ascent LLC (Delaware LLC)",
            "Stories: 5, plus rooftop amenity deck",
            "Year built: 2019",
            "Total enclosed area: 95,000 sq ft",
            "",
            "This document summarizes the physical and operational characteristics of the",
            "Ascent Park City hotel asset, intended for diligence by prospective buyers.",
        ],
    ),
    (
        "Title/Ascent_Title_Commitment.txt",
        [
            "FIRST AMERICAN TITLE INSURANCE COMPANY",
            "Title Commitment for Title Insurance — Form 2021",
            "",
            "Commitment date: March 12, 2024",
            "Property: Lot 14 Block 2 of Park City Heights subdivision",
            "County: Summit County, Utah",
            "Vested in: LKCap Okoa Ascent LLC",
            "",
            "Schedule A — Effective Date: March 12, 2024",
            "Schedule B-I — Requirements: Pay all taxes through Q4 2023.",
            "Schedule B-II — Exceptions: Easement of record for utility line (Doc 875202).",
        ],
    ),
    (
        "Operating/Ascent_T12_PL_2023.txt",
        [
            "ASCENT PARK CITY HOTEL — T-12 OPERATING P&L",
            "Reporting period: January 2023 — December 2023",
            "",
            "Total Revenue:        $14,200,000",
            "  Room Revenue:        9,800,000",
            "  F&B Revenue:         3,200,000",
            "  Other Revenue:       1,200,000",
            "",
            "Total Operating Expenses:  $9,500,000",
            "  Labor:                4,200,000",
            "  Cost of Goods:        1,100,000",
            "  Fixed Costs:          2,800,000",
            "  Marketing:              900,000",
            "  Other:                  500,000",
            "",
            "GOP (Gross Operating Profit):    $4,700,000",
            "GOP Margin: 33.1%",
        ],
    ),

    # --- 3 clearly-irrelevant: other property docs ---
    (
        "Other_Properties/Magnolia_Ridge_Apartments_Rent_Roll.txt",
        [
            "MAGNOLIA RIDGE APARTMENTS — RENT ROLL",
            "Property: Magnolia Ridge Apartments, Phoenix AZ",
            "Reporting period: April 1, 2024 as-of",
            "",
            "Unit  | Tenant            | Rent     | Lease End",
            "101   | A. Smith          | $1,850   | 2024-12-31",
            "102   | B. Johnson        | $1,890   | 2025-03-31",
            "103   | C. Lee            | $1,825   | 2024-09-30",
            "",
            "NOTE: This document concerns the Magnolia Ridge multifamily asset in",
            "Phoenix, Arizona — completely separate from the Ascent Park City hotel.",
        ],
    ),
    (
        "Other_Properties/Bay_Vista_Land_Survey.txt",
        [
            "BAY VISTA — ALTA/NSPS LAND TITLE SURVEY",
            "Property: Bay Vista raw-land parcel, Half Moon Bay, California",
            "Surveyor: PaceLine Surveying Inc., CA License 12345",
            "",
            "Acreage: 47.3 acres",
            "Zoning: A-1 Agricultural",
            "",
            "NOTE: This survey is for the Bay Vista property in California — a separate",
            "OKOA loan unrelated to the Ascent hotel sale.",
        ],
    ),
    (
        "Other_Properties/Sunset_Industrial_Phase_I_ESA.txt",
        [
            "PHASE I ENVIRONMENTAL SITE ASSESSMENT",
            "Property: Sunset Industrial Park, Bldg C, Fontana CA",
            "Assessor: GeoEnviron Consultants",
            "Date of report: November 14, 2023",
            "",
            "Findings: No recognized environmental conditions (RECs) identified.",
            "Historical use: warehousing since 1987.",
            "",
            "NOTE: This Phase I ESA is for the Sunset Industrial property — separate",
            "OKOA loan, unrelated to the Ascent hotel.",
        ],
    ),

    # --- 1 privileged: sample attorney memo ---
    (
        "Legal/PRIVILEGED_Attorney_Memo_re_Foreclosure.txt",
        [
            "PRIVILEGED & CONFIDENTIAL",
            "ATTORNEY-CLIENT PRIVILEGED COMMUNICATION",
            "",
            "MEMORANDUM",
            "",
            "To:   OKOA Capital Principals",
            "From: Holland & Knight LLP (Counsel)",
            "Date: November 2, 2024",
            "Re:   Wolfgramm / Ascent Park City — Foreclosure Strategy Analysis",
            "",
            "PRIVILEGED ANALYSIS:",
            "",
            "The following constitutes legal advice regarding our foreclosure",
            "strategy. Counsel analyzed the borrower's likely defenses, our",
            "exposure on the Notice of Default timing, and recommended cure-period",
            "tactics. This memo should NOT be disclosed to any third party, including",
            "any prospective buyer of the property.",
            "",
            "[Privileged content omitted from synthetic test]",
            "",
            "/s/ Jane Doe, Partner, Holland & Knight LLP",
        ],
    ),

    # --- 1 zero-byte file ---
    ("Misc/empty_placeholder.txt", []),

    # --- 1 ambiguous-relevance: a document mentioning multiple properties ---
    (
        "Mixed/2024_Q3_Portfolio_Update_Letter.txt",
        [
            "OKOA CAPITAL — PORTFOLIO UPDATE",
            "Quarter: Q3 2024",
            "",
            "This letter summarizes performance across OKOA's portfolio. The Ascent",
            "Park City hotel continues to outperform original underwriting, with",
            "T-12 GOP at $4.7M (vs. $4.2M projected). Concurrently, the Magnolia",
            "Ridge multifamily and Bay Vista land assets remain on hold pending",
            "market conditions.",
            "",
            "While the bulk of this letter references multiple properties, the",
            "Ascent-related performance commentary may be of interest to a hotel",
            "buyer. Discretion on whether to include this in an Ascent-focused",
            "dataroom is recommended.",
        ],
    ),
]


# Placeholder for encrypted PDF — we'll just create a stub file with .pdf extension
# and zero bytes (the skill's pre-flight will categorize as "unable_to_evaluate").
ENCRYPTED_PDF_PATH = "Misc/encrypted_placeholder.pdf"


def generate(output: Path) -> None:
    """Generate the synthetic source folder."""
    output = Path(output)
    if output.exists():
        print(f"WARNING: {output} already exists — overwriting files in place")
    output.mkdir(parents=True, exist_ok=True)

    for rel_path, lines in SYNTHETIC_FILES:
        fp = output / rel_path
        fp.parent.mkdir(parents=True, exist_ok=True)
        if not lines:
            # Zero-byte file — touch only
            fp.touch()
        else:
            fp.write_text("\n".join(lines), encoding="utf-8")
        print(f"  wrote: {rel_path} ({fp.stat().st_size} bytes)")

    # Encrypted-PDF placeholder (zero-byte .pdf)
    enc = output / ENCRYPTED_PDF_PATH
    enc.parent.mkdir(parents=True, exist_ok=True)
    enc.touch()
    print(f"  wrote: {ENCRYPTED_PDF_PATH} ({enc.stat().st_size} bytes — encrypted-stub)")

    total = sum(1 for _ in output.rglob("*") if _.is_file())
    print(f"\nGenerated {total} files in {output}")


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic source folder for acos-dataroom-v2 smoke test.")
    parser.add_argument("--output", required=True, type=Path, help="Output directory")
    args = parser.parse_args(argv)
    generate(args.output)
    return 0


if __name__ == "__main__":
    sys.exit(cli_main())
