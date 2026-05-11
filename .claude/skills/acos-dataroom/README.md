# acos-dataroom

Transform a messy single-loan folder into an investor-ready data room through an
AI-assisted, human-reviewed workflow. **Outbound diligence orientation** — this
skill prepares documents for *external* parties (loan buyers, participation
partners, property buyers, foreclosure bidders, takeout lenders), not for OKOA's
own underwriting process.

## Quick Start

```bash
# Phase 1–9: scan, extract, classify, build review workbook
acos-dataroom create-guide \
  --source "/Users/zee/Dropbox/Loans/AscentParkCity/source" \
  --objective "Prepare data room for loan sale" \
  --deal-type loan_sale \
  --data-room-name "AscentParkCity_LoanSale"

# (You edit the Excel guide that pops out — Include / Sensitivity / Decision columns)

# Phase 10: validate the edited guide
acos-dataroom validate-guide \
  --guide "/path/to/edited/AscentParkCity_LoanSale_Data_Room_Guide_2026-05-06.xlsx"

# Phase 11: create the final data room
acos-dataroom create-room \
  --guide "/path/to/edited/...xlsx" \
  --target "/Users/zee/Dropbox/DataRooms/AscentParkCity" \
  --confirmed true
```

## Deal Types (v1)

| Deal Type | Use Case |
|---|---|
| `loan_sale` | Sell an existing loan to another investor |
| `loan_participation` | Sell a participation interest in an existing loan |
| `property_sale` | Sell underlying real estate (typically post-foreclosure) |
| `foreclosure_auction` | Prepare for a foreclosure / trustee sale auction |
| `lender_package` | Pitch a loan to a takeout / refinance lender |

Don't see your deal type? Run with `--deal-type lender_package` for the
broadest scaffold and tailor in the Excel review.

## What's in the Skill

- `SKILL.md` — orchestrator (read this first)
- `config.json` — paths, defaults, enums
- `references/` — checklists, taxonomies, schemas, recipes
- `scripts/` — Python implementation (pdf/word/excel extraction, OCR, vision, Excel guide build, validation, final folder creation)
- `tests/` — synthetic fixture for regression testing

## Non-Negotiables

1. **Never modify, move, delete, rename, or share source files.** Copies only, after explicit confirmation.
2. **Never auto-upload.** v1 writes to local paths (which may live inside synced Dropbox folders).
3. **Never auto-redact.** Flag for redaction; require user-provided redacted file or explicit override.
4. **Human decision is final.** Diff logging is audit-only.
5. **Every claim must be traceable** to source file, page, extraction method, and evidence-bundle snippet.
6. **Vision is mandatory, not optional** for image-only PDFs and low-OCR-confidence pages.
7. **Pause gates are real.** Deal-type confirmation (Phase 1) and guide review (Phase 9) require explicit user confirmation.

## Why "Outbound" Diligence Matters

OKOA's existing DD checklists at `/Users/zee/okoa-labs/okoa_ops/...` are
*origination-side* — they describe what OKOA collects when underwriting a
borrower's loan. This skill produces the inverse: what OKOA must hand over
when monetizing or transferring an existing position. Different artifacts,
different orientations. The OKOA master reference is loaded only as a
*category vocabulary supplement* so terminology stays consistent across
OKOA's internal artifacts.

See `references/deal_types.md` for full deal-type definitions.
