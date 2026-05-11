# Tests — acos-dataroom

Synthetic regression fixture and smoke tests for the skill. Designed so the
end-to-end pipeline can be exercised without exposing real loan data.

## Layout

```
tests/
├── README.md                       — this file
├── test_smoke.py                   — smoke test: scan + extract + write workbook
└── fixtures/
    └── synthetic_loan/              — fake loan folder (no real data)
        ├── 01_loan_documents/
        │   ├── promissory_note.txt
        │   └── loan_agreement_summary.md
        ├── 02_collateral/
        │   └── recorded_documents.txt
        ├── 03_servicing/
        │   ├── rent_roll.csv
        │   └── payment_history.csv
        ├── 04_property/
        │   └── property_overview.md
        ├── 05_third_party/
        │   └── appraisal_summary.txt
        ├── .DS_Store                 — system file (skill auto-excludes)
        └── README.txt                — describes the fixture itself
```

## Running smoke tests

```bash
cd /Users/zee/Documents/Vibe\ Coding/ACOS\ 3.0/.claude/skills/acos-dataroom
python -m pytest tests/test_smoke.py -v
# or
python tests/test_smoke.py
```

## Adding binary fixtures

The shipped fixture uses text files only because creating real PDF/DOCX/image
fixtures requires extra tooling (LaTeX, LibreOffice, etc.). To exercise the
PDF/Word/Excel/image paths:

1. Drop a small real PDF into `fixtures/synthetic_loan/` (a one-pager works).
2. Drop a `.docx` (e.g., a simple Word doc with a few paragraphs).
3. Drop a `.xlsx` (a workbook with 1–2 sheets, headers and a few rows).
4. Drop a `.png` or `.jpg` (any image — vision will describe it).

The smoke test will pick them up automatically; no test changes needed.

## What the fixture does NOT contain

- Real borrower / property names or financial data.
- Any PII (no SSNs, no actual addresses, no real signatures).
- Encrypted PDFs (would require generating one with a known password — not
  needed for smoke testing the happy path).
- Email files (out of scope for v1).
- Zip archives (out of scope for v1).

## What `test_smoke.py` validates

1. The fixture directory is scannable.
2. `scan_folder.py` produces a `file_manifest.json` and `file_manifest.csv`.
3. Every file in the fixture appears in the manifest with a deterministic
   `file_id` derived from its SHA-256 hash.
4. System files (`.DS_Store`) are excluded.
5. `extract_text.py` runs without error on each fixture file (whether or not
   text extraction returns content depends on the file type).
6. The expected output directories (`extraction/`, `evidence/`, `intermediate/`,
   `logs/`) are created.

The smoke test does NOT exercise:
- Vision fallback (requires `ANTHROPIC_API_KEY`).
- Excel guide generation (requires `openpyxl` and is exercised separately).
- Final data room creation (requires a confirmed boss-edited guide).

For a full end-to-end test, run the real subcommands against the fixture
manually after the smoke test passes:

```bash
acos-dataroom create-guide \
  --source tests/fixtures/synthetic_loan \
  --objective "Smoke test — please ignore" \
  --deal-type loan_sale \
  --data-room-name "Synthetic_Test_Room"
```
