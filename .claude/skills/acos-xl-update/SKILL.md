---
name: acos-xl-update
description: Automates OKOA Capital's weekly "XL Ant" investor portfolio update. Duplicates the latest dated workbook, rolls the report date forward one week, pulls each loan's payoff / outstanding / per-diem from acos-hypercore-ask (provenance-bound, never guessed), drafts each loan's "Progress Made This Week" and "Key Issues / Blockers" bullets from acos-fireflies-ask (short, diplomatic, carry-forward-aware), and writes them into the new workbook WITHOUT altering its formatting. Non-destructive — originals are never modified; every number is Hypercore-verified or flagged, never fabricated. Produces a SEPARATE machine-verified reference companion tracing every bullet to its exact Fireflies meeting line (title, date + time, speaker, in-meeting timestamp) or marking it a prior-week carry-forward — references never go in the workbook. Use when the user says "run the XL update", "do this week's XL report", "update the XL Ant portfolio update", or "prepare the XL investor update".
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "[--date YYYYMMDD] | dry-run | prepare-only"
---

# acos-xl-update

## Purpose

Prepares OKOA's **weekly XL Ant portfolio update** (an investor-facing Excel workbook, one
worksheet per loan) end-to-end: roll the file forward a week, refresh each loan's payoff from
**acos-hypercore-ask**, and refresh each loan's narrative from **acos-fireflies-ask** — producing
a review-ready `.xlsx` that is indistinguishable in look from the prior weeks.

**Source folder (READ — the published report series):**
`/Users/zee/Library/CloudStorage/Dropbox-OkoaCapital/Investor Relations/Investor Updates/XL/XL Weekly Update`
Files are named `XL Ant Portfolio Update YYYYMMDD.xlsx`. Each week = prior week + 7 days. This folder is
read-only to the skill — it is never written to.

**Output folder (WRITE — the draft staging area):**
`/Users/zee/Documents/OKOA/XL Ant Weekly Update Draft`
The skill ALWAYS writes the new workbook here, never back into the Dropbox series. This is the engine
default (`DEFAULT_OUT_FOLDER`); override per-run with `prepare --out-folder DIR`. Publishing an approved
draft into the Dropbox series is a separate, user-driven step.

## Non-negotiable guardrails

1. **Non-destructive.** Only ever write the NEW duplicated file, and only into the **draft output
   folder** (`/Users/zee/Documents/OKOA/XL Ant Weekly Update Draft`). Never modify a prior week's file
   and never write into the Dropbox source series.
2. **Never fabricate a number.** Every payoff comes from acos-hypercore-ask (provenance-bound and
   reconciled) or the cell is left unchanged / flagged for the user. No estimated or remembered
   figures. If Hypercore refuses or is unavailable for a loan, REPORT it — do not guess.
3. **Never fabricate an update.** Progress / blocker bullets are grounded in acos-fireflies-ask
   findings and/or the prior week's still-relevant bullets. No invented events.
4. **Appearance-safe.** The engine writes values/text and sets `fullCalcOnLoad` — it does NOT
   change formulas or formatting. Do not run destructive reformatting. Riverdale's payoff is a
   date-driven FORMULA — never overwrite it; it recalculates from the report date.
5. **Review before send.** This skill produces a DRAFT for the user to review. It does not email
   or share anything. Always end by reporting every number's provenance and every bullet's source.
6. **Every update is referenced — in a SEPARATE companion.** No narrative bullet ships without a
   reference. Each bullet is either quoted to the exact Fireflies meeting line (meeting title, date +
   time in Mountain Time, speaker, in-meeting timestamp) or explicitly marked as carried forward from a
   named prior week. These references live ONLY in the standalone `… — Sources & Provenance.md`
   companion in the draft folder — NEVER inside the investor workbook (no investor-visible internal
   quotes). Quotes are machine-verified verbatim against the cached transcripts; a quote that cannot be
   located is flagged, not shipped.

## The engine

`scripts/xl_update.py` (openpyxl, stdlib) owns all mechanical Excel work:
- `prepare --folder DIR [--weeks 1] [--date YYYYMMDD] [--out-folder DIR]` — duplicate the latest file
  (found in the source `--folder`) into the **draft output folder** → +1 week, set `Riverdale!B3` (the
  single date input; every other sheet's `B3` = `=Riverdale!B3`), set `fullCalcOnLoad`, and print a
  **manifest** (per-sheet payoff cell + whether it's a formula + current value + the current
  Progress/Blocker bullets — the carry-forward source, plus `output_folder`). `--out-folder` defaults to
  `/Users/zee/Documents/OKOA/XL Ant Weekly Update Draft`; pass it only to override.
- `manifest --file XLSX` — inspect a file (same shape) without changing anything.
- `apply --file XLSX --spec SPEC.json` — write payoffs + bullets from a spec (below).
- `verify --file XLSX` — post-write sanity checks.

Cells are located by ROW LABEL per sheet (offsets differ between tabs) — never hardcode rows.

`scripts/xl_provenance.py` (openpyxl-free, stdlib + zoneinfo) renders the SEPARATE reference companion:
- `--spec SPEC.json --out FILE.md` — from a provenance spec (one entry per bullet: `kind`
  = carried/refreshed/new, `prior_week_basis`, and `sources[]` of `{meeting_id, meeting_title, quote}`,
  plus an optional `payoffs[]` block for the Hypercore figure trail), it loads each cited Fireflies
  transcript from `~/.fireflies-cache`, resolves the meeting's Mountain-Time datetime, locates each
  quote VERBATIM (attaching speaker + in-meeting mm:ss), and writes a Markdown audit into the draft
  folder. It prints `{unverified_quotes, sourceless_new_bullets}` — both MUST be 0 before delivery.

## The workbook (8 worksheets)

| # | Worksheet | Hypercore loan (id) | Payoff action |
|---|---|---|---|
| 0 | Loan Status Template | — | **leave entirely as-is** (do not put it in the spec) |
| 1 | Riverdale | Motel 6 | **no payoff write** — it's a formula; setting the date recalcs it |
| 2 | Utah Shoe | Utah Shoe (**88**) | payoff = **Hypercore payoff** for loan 88 **as of the report date** |
| 3 | Utah Shoe III | Utah Shoe III (131) | **no change** |
| 4 | Argent | Argent | **no change** |
| 5 | Ascent Senior | Beehive Waldorff (**134**) | payoff = **XL's outstanding IN loan 134** (the senior/Beehive loan) |
| 6 | Ascent Pref | Ascent Pref Equity (**149**) | payoff = **XL's outstanding IN loan 149** |
| 7 | Lux II | Lux II LOC (**171**) | payoff = **current balance + 7 × per-diem interest for XL in loan 171** (per-diem ≈ 1,029.24 — confirm live) |

Notes:
- "XL's outstanding IN <loan>" is the **per-loan** funding figure for the XL Ant investor (funding
  entity id **3**) — NOT XL's portfolio total (XL is invested in several loans).
- The **loan ids are pinned** (verified live 2026-07-02) so figures are deterministic. They are
  stable in Hypercore, but each run STILL verifies the resolved loan name matches the expected one
  and flags any mismatch (a defensive guard, per the anti-confabulation rule).
- The template has **5** progress bullet slots and **3** blocker slots per sheet (the workbook
  currently exposes 5 progress slots, not 6 — fill the top 5).

## Protocol

### Phase 0 — Arguments & setup
- `--date YYYYMMDD` overrides the default (latest + 7 days). `dry-run` = do everything but write
  to a temp copy and report (never touch the Dropbox folder). `prepare-only` = stop after Phase 1.
- Report date in the sheets renders `MM/DD/YYYY` automatically from the date you set.

### Phase 1 — Roll the file forward
Run (quote the path):
```
python3 .claude/skills/acos-xl-update/scripts/xl_update.py prepare \
  --folder "/Users/zee/Library/CloudStorage/Dropbox-OkoaCapital/Investor Relations/Investor Updates/XL/XL Weekly Update"
```
The new workbook is created in the draft output folder (`/Users/zee/Documents/OKOA/XL Ant Weekly Update
Draft`) — the Dropbox source is only read. Capture the manifest: the new file path (`file` +
`output_folder`), the report date (`YYYY-MM-DD` and `MM/DD/YYYY`), and each sheet's `payoff_current` +
`progress_current` + `blocker_current` (the **carry-forward source** for Phase 3). Confirm the new
filename ends with the expected +7-day date.

### Phase 2 — Payoff figures (acos-hypercore-ask — verified, never guessed)
For each loan below, fetch the figure LIVE under Doppler. Prefer Hypercore's own native value; the
skill reconciles + provenance-binds or REFUSES. Record each value **with its provenance** for the
final report. If a figure REFUSES/errors, leave that cell unchanged and flag it.

```
# Utah Shoe (loan 88) — PAYOFF as of the report date. Use the payoff figure DIRECTLY by loan id.
# (Do NOT use hca-ask for payoff — smart_ask does not route the payoff intent, and the bare name
#  "Utah Shoe" is ambiguous with "Utah Shoe II/III". The direct figure is the proven path.)
doppler run --project hypercore-ask --config dev_personal -- \
  python3 .claude/scripts/hca-figures.py --loan-id 88 --date <REPORT_DATE>

# Ascent Senior — XL's outstanding on loan 134 (funding figure; verify it resolves to loan 134):
doppler run --project hypercore-ask --config dev_personal -- \
  python3 .claude/scripts/hca-ask.py --ask "what is XL's outstanding on the Beehive senior loan?"

# Ascent Pref — XL's outstanding on loan 149 (verify it resolves to loan 149):
doppler run --project hypercore-ask --config dev_personal -- \
  python3 .claude/scripts/hca-ask.py --ask "what is XL's outstanding on the Ascent Pref loan?"

# Lux II — per-diem interest for XL on loan 171 (verify it resolves to loan 171), then compute:
doppler run --project hypercore-ask --config dev_personal -- \
  python3 .claude/scripts/hca-ask.py --ask "what is the per diem interest for XL on the Lux II loan?"
```
- **Payoff (Utah Shoe):** take `values[0].value` from the DELIVERED figure; it reconciles component
  parts to the cent or REFUSES.
- **Funding (Ascent Senior / Ascent Pref):** the DELIVERED envelope's `answer`/`values[0].value` is
  XL's outstanding; confirm `meta.resolution.loan.id` == the expected id (134 / 149) and
  `investor.id` == 3 — if not, STOP and flag (don't write a mismatched loan's number).
- **Lux II new balance = `payoff_current` (from the manifest) + 7 × per_diem.** Confirm the per-diem
  against the ≈1,029.24 expectation; if it deviates materially, surface it before writing. Verify
  the figure resolved to loan 171.
- Riverdale, Utah Shoe III, Argent → **no Hypercore call** (formula / no-change).
- If a figure REFUSES or resolves to an unexpected loan, leave that payoff cell unchanged and flag
  it in the Phase 5 report — never write an unverified number.

### Phase 3 — Narrative (acos-fireflies-ask — diplomatic, carry-forward-aware)
For each loan worksheet, build the **Progress Made This Week** bullets (≤5) and any **Key Issues /
Blockers** bullets:

1. **Start from continuity.** Read the prior week's bullets (`progress_current` / `blocker_current`
   from the manifest). Many updates remain relevant week-to-week — keep the still-true ones
   (verbatim or lightly refreshed).
2. **Pull new updates from Fireflies** for that loan/property:
   ```
   /acos-fireflies-ask "What are the latest updates, decisions, or next steps on the <loan/property> loan?"
   ```
   Use the loan's real-world name/property for the query (e.g. Motel 6 for Riverdale, Beehive for
   Ascent Senior, the property city/name for the others).
3. **Merge & prioritize** carry-forward + new into a single list; drop the stale/resolved; if more
   than 5, keep the **top 5** most material (payoff-relevant, legal/foreclosure, refinance/extension,
   buyer/sale progress). Fewer than 5 (or none) is fine — "No recent updates received from the
   borrower" is an acceptable neutral bullet, matching prior weeks.
4. **Negative items / blockers → the Key Issues / Blockers section** (≤3), not Progress.
5. **Tone (learned from prior files):** short, factual, active voice; name the actor (OKOA,
   borrower, legal, foreclosure team); forward-looking; **diplomatic and business-formal** — never
   casual, disparaging, or speculative. Match the register of existing bullets, e.g.:
   - "OKOA continues buyout discussions with multiple institutional parties ahead of the auction."
   - "Final extension draft has been reviewed by legal and returned to the borrower for execution."
   - "No recent updates received from the borrower."
6. **Capture provenance for EVERY bullet (mandatory — feeds the reference companion).** As you
   finalize each bullet, record its reference:
   - NEW / REFRESHED bullet → the source meeting(s): `meeting_id` (the cached transcript id),
     `meeting_title`, and the VERBATIM supporting line(s) copied **exactly** from the transcript
     `sentences[].text` (must be findable as an exact substring — no paraphrase, no stitched
     fragments). A bullet may cite more than one meeting.
   - CARRIED / REFRESHED bullet → the exact prior-week text it rehashes (`prior_week_basis`).
   - A NEW bullet with NO source is not allowed — cut it or find the source. Prefer tight 1–2
     sentence quotes. Best pulled with a parallel per-loan pass (search the loan terms, read the
     top `~/.fireflies-cache/transcripts/<id>.json` + `extracts/<id>.yaml`, quote verbatim).

### Phase 4 — Write, verify & reference
Assemble a spec and apply it (omit no-change sheets and the template; omit `payoff` where the cell
is a formula or unchanged):
```json
{"sheets": {
  "Utah Shoe":     {"payoff": <n>, "progress": ["…"], "blockers": ["…"]},
  "Ascent Senior": {"payoff": <n>, "progress": ["…"]},
  "Ascent Pref":   {"payoff": <n>, "progress": ["…"]},
  "Lux II":        {"payoff": <n>, "progress": ["…"], "blockers": ["…"]},
  "Riverdale":     {"progress": ["…"]},
  "Utah Shoe III": {"progress": ["…"]},
  "Argent":        {"progress": ["…"]}
}}
```
```
python3 .claude/skills/acos-xl-update/scripts/xl_update.py apply  --file "<new file>" --spec spec.json
python3 .claude/skills/acos-xl-update/scripts/xl_update.py verify --file "<new file>"
```
Heed `apply` warnings (e.g. a formula-cell payoff is refused; too many bullets for the slots).

**Then render the reference companion** (mandatory — same draft folder, NEVER inside the workbook).
Assemble a provenance spec from your Phase 2 payoff provenances (`payoffs[]`) + your Phase 3 per-bullet
references (`sheets[].bullets[]` with `kind` / `prior_week_basis` / `sources[]`), then:
```
python3 .claude/skills/acos-xl-update/scripts/xl_provenance.py \
  --spec prov_spec.json \
  --out "/Users/zee/Documents/OKOA/XL Ant Weekly Update Draft/XL Ant Portfolio Update <YYYYMMDD> — Sources & Provenance.md"
```
Confirm the audit prints `unverified_quotes: 0` and `sourceless_new_bullets: 0`. If a quote is flagged
NOT LOCATED, fix it (copy it verbatim from the transcript) and re-render — an unverifiable reference
must not ship.

### Phase 5 — Report for review (do NOT send)
Give the user clickable links to **both** the workbook AND the reference companion, plus a concise
change report:
- **Payoffs:** each loan → old value → new value → **Hypercore provenance** (or "unchanged" /
  "flagged: <reason>"). Show the Lux II arithmetic (current + 7 × per-diem).
- **Narrative:** per loan, the final bullets, marked `[carried forward]` vs `[new — Fireflies: <meeting/date>]`.
- **Reference companion:** link the standalone `… — Sources & Provenance.md` and state the audit result
  (`unverified_quotes: 0`, `sourceless_new_bullets: 0`). Every bullet is quoted to its exact meeting
  line (date + time) or marked carried-forward. The workbook itself carries no references.
- **Verify** result + any warnings.
- Remind the user to review before sending to XL; offer to open the workbook (Excel — it recalculates
  the Riverdale formula on open) and the companion.

## Trust & failure posture
- A payoff that can't be Hypercore-verified is **left unchanged and flagged** — never estimated.
- Fireflies text is grounded + cited; if Fireflies has nothing for a loan, carry forward or use the
  neutral placeholder — never invent progress.
- On any hard error, stop and report; the prior weeks and the (partial) new file are safe to
  re-run — `prepare` refuses to overwrite an existing target unless `--overwrite` is passed.

## Dependencies
- acos-hypercore-ask (this repo; `.claude/scripts/hca-*.py`; Doppler `hypercore-ask/dev_personal`).
- acos-fireflies-ask (global skill; Doppler `acos-fireflies-ask/dev_personal`). Refresh its cache
  (`fireflies_client.py refresh` + `fireflies_extract.py`) before Phase 3 so the newest meetings are
  available; the reference companion reads verbatim quotes + datetimes straight from
  `~/.fireflies-cache/transcripts/<id>.json`.
- Python 3 + openpyxl (system python3 has it); `xl_provenance.py` needs only stdlib + `zoneinfo`
  (Python 3.9+). LibreOffice optional (only to bake cached values / render a PDF preview; not required
  — Excel recalculates on open via `fullCalcOnLoad`).
