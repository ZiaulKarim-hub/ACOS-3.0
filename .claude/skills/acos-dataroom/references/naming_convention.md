# Naming Convention — Final Data Room Files

When the skill creates the final data room (Phase 11), it copies and renames
files according to a consistent convention so the room is navigable and the
filenames carry meaning.

## Format

```
[Cat#].[Sub#]_[DocType]_[Borrower|Property]_[Date]_[Status].[ext]
```

### Components

- **`Cat#`** — two-digit category number from the deal-type taxonomy (e.g., `01`, `02`).
- **`Sub#`** — two-digit subcategory number within the category (e.g., `03`).
- **`DocType`** — short document type label (no spaces; underscores for separators). Examples: `Note`, `Loan_Agreement`, `Deed_of_Trust`, `Title_Commitment`, `Phase_I`, `Estoppel`.
- **`Borrower|Property`** — short identifier for the loan/property. Use whichever is more recognizable for this deal. Sanitize: lowercase, hyphens for spaces, no special chars. Examples: `ascent-park-city`, `borrowerco-llc`.
- **`Date`** — document date in `YYYYMMDD`. Use `00000000` if no date is recoverable.
- **`Status`** — one of: `executed`, `draft`, `redlined`, `recorded`, `expired`, `superseded`, `unknown`.
- **`ext`** — original extension, lowercase.

### Examples

```
01.02_Note_borrowerco-llc_20240815_executed.pdf
02.01_Deed_of_Trust_ascent-park-city_20240816_recorded.pdf
03.04_Phase_I_ascent-park-city_20240701_unknown.pdf
04.03_Estoppel_TenantA_20250120_executed.pdf
05.01_Servicing_History_borrowerco-llc_20260301_unknown.xlsx
```

## Length Limits

- Maximum filename length: **180 characters** (under macOS / Windows / Dropbox limits with margin).
- If a generated name exceeds the limit, truncate `Borrower|Property` first (preserve `Cat#`, `Sub#`, `DocType`, `Date`, `Status`).

## Sanitization Rules

Applied to every component before joining:
- Replace spaces with underscores in `DocType`.
- Replace spaces with hyphens in `Borrower|Property`.
- Lowercase `Borrower|Property`.
- Strip all chars except `[A-Za-z0-9._-]`.
- Collapse runs of underscores to a single underscore.

## Collision Handling

If the generated name already exists in the target folder:

1. Append `_v2` before the extension: `01.02_Note_borrowerco-llc_20240815_executed_v2.pdf`.
2. If `_v2` also exists, increment to `_v3`, `_v4`, etc.
3. Cap at `_v99`. If exceeded, error out with "Too many collisions for this name — investigate manually."

The collision log is written to `creation_log.csv` so the boss can see why
names were versioned.

## What Stays in the Original Name

If the source filename has unusual but meaningful info (e.g., a specific recording number, a county, a tax year), the skill preserves that in the **`DocType`** component, not in the `Borrower|Property` component. Example:

```
Source:    "Title Commitment - Salt Lake County - 2024.pdf"
Renamed:   01.05_Title_Commitment_SLC_ascent-park-city_20240715_unknown.pdf
                                  ^^^ moved into DocType for context
```

## Override

The Excel guide's `proposed_renamed_filename` column is editable. The boss
can override the auto-generated name by editing this column before running
`create-room`. The validation step (`validate-guide`) re-applies the
sanitization rules to any boss-edited names.

## Original Filename Preservation

The original filename is always preserved in:
- `Source_File_Manifest.file_name` (Excel)
- `evidence/<file_id>.json → source.name`
- `creation_log.csv → source_file_name` column

So even after rename, the original is recoverable. **Source files themselves
are never modified, never moved, never renamed** — only copies in the target
data room.
