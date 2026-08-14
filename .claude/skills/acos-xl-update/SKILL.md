---
name: acos-xl-update
description: Automates OKOA Capital's weekly "XL Ant" investor portfolio update. Duplicates the latest dated workbook, rolls the report date forward one week, pulls each loan's payoff / outstanding / per-diem from acos-hypercore-ask (provenance-bound, never guessed), drafts each loan's "Progress Made This Week" and "Key Issues / Blockers" bullets from acos-fireflies-ask (short, diplomatic, and RECENT — sourced only to meetings from the last two weeks, primary focus the last week; a loan with fewer than two updates in that window carries forward the prior week's points, with the neutral "No recent updates received" only as a fallback), and writes them into the new workbook WITHOUT altering its formatting. Non-destructive — originals are never modified; every number is Hypercore-verified or flagged, never fabricated. Also sweeps BOTH work mailboxes read-only (ziaul@okoacapital.com and, already-read messages only, jason@okoacapital.com) for weekly-update points, via one-shot subprocesses pinned to each mailbox's own claude.ai account — no write verb is ever handed over and no message body is ever recorded. Produces a SEPARATE machine-verified reference companion tracing every bullet to its exact Fireflies meeting line (title, date + time, speaker, in-meeting timestamp) or marking it a prior-week carry-forward — references never go in the workbook. Use when the user says "run the XL update", "do this week's XL report", "update the XL Ant portfolio update", or "prepare the XL investor update".
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
3. **Never fabricate an update; keep fresh points RECENT, and keep quiet loans STABLE.** Any *new*
   progress / blocker bullet is grounded in acos-fireflies-ask meetings from the **last two weeks** (no
   source older than 14 days before the report date), primary focus on the **last week** — no invented
   events. But a loan is never blanked for a quiet week: with **fewer than two updates this cycle it
   carries forward the prior week's points** (adding the one new update if there is exactly one); the
   neutral `"No recent updates received from the borrower."` is only a fallback when there is nothing to
   carry. (See Phase 3's CONTINUITY RULE, and the machine-enforced `--min-date` cutoff.)
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
7. **Email is READ-ONLY, and Jason's mailbox is read-only AND already-read-only.** (Zee, 2026-08-13.)
   The sweep reaches both mailboxes through `xl_mail_sweep.ts` and nothing else — the skill holds no
   Gmail tool of its own, so it has no write verb to misuse. Inside the sweep, every subprocess is
   handed a fail-CLOSED read-verb allow-list (`list`/`get`/`search`/`read`/`query`/`download`); any
   other leading verb aborts the run before a single search fires. **`jason@okoacapital.com` queries
   always carry `is:read`**, so an unread message can never enter the result set — "never open an
   unopened email" is enforced by the query, not by instruction. **Never** change, label, move, trash,
   draft, send, or mark anything in either mailbox. Body text is never requested and never recorded.
   The sweep exists for ONE purpose: finding weekly-update points. Nothing else.

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

| # | Worksheet | Hypercore loan (id) | XL participation | Payoff action |
|---|---|---|---|---|
| 0 | Loan Status Template | — | — | **leave entirely as-is** (do not put it in the spec) |
| 1 | Riverdale | Motel 6 | — | **no payoff write** — it's a formula; setting the date recalcs it |
| 2 | Utah Shoe | Utah Shoe (**88**) | **100%** | payoff = **Hypercore payoff** for loan 88 **as of the report date** (safe ONLY because participation is 100% — see the scope rule below) |
| 3 | Utah Shoe III | Utah Shoe III (131) | **60%** | **CARRY FORWARD** — copy B17 from the latest Dropbox workbook. **No Hypercore call, ever.** (Zee, 2026-08-13) |
| 4 | Argent | Argent | — | **no change** |
| 5 | Ascent Senior | Beehive Waldorff (**134**) | partial | payoff = **XL's outstanding IN loan 134** (the senior/Beehive loan) |
| 6 | Ascent Pref | Ascent Pref Equity (**149**) | partial | payoff = **XL's outstanding IN loan 149** |
| 7 | Lux II | Lux II LOC (**171**) | partial | payoff = **current balance + 7 × per-diem interest for XL in loan 171** (per-diem ≈ 1,029.24 — confirm live) |

Notes:
- **EVERY SHEET IS INVESTOR-SCOPED.** These sheets report XL's book, not the borrower's. Proof: cell
  B11 "Original Loan Amount" equals XL's `funding_commitment` to the dollar on each sheet (Utah Shoe
  1,025,000; Utah Shoe III 300,000). A loan-level payoff is the WRONG KIND OF NUMBER for these cells
  unless XL's participation is 100%.
- **Utah Shoe III is carry-forward, permanently.** Zee ruled 2026-08-13: "Starting next week the utah
  shoe III number stays whatever we have there" — i.e. whatever sits in the LATEST Dropbox workbook.
  Read it, copy it, write nothing sourced. Context: OKOA reclassified all 2026 payments from Utah
  Shoe 1 (loan 88) to Utah Shoe 3 (loan 131) and credited them ALL to XL, though XL is only 60% of
  that capital stack (OKOA Partners is 40%). That makes every Hypercore figure on loan 131
  unreliable for investor reporting. The rule attaches to the SHEET, not to any value — if Zee
  hand-edits it, the next run carries the new figure. Name the carried figure in the provenance file
  every week so it stays visible.
- **Loan 88 carries the same reclassification.** Payments were moved OFF it, so its Hypercore payoff
  is overstated (XL `funding_outstanding` 1,047,958.33 exceeds the 1,025,000 commitment). Zee let
  the 20260816 figure stand. Keep sourcing it per the table, but **flag the reclassification in the
  provenance file every week** until Zee says to stop.
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
- Riverdale, Utah Shoe III, Argent → **no Hypercore call** (formula / carry-forward / no-change).
- If a figure REFUSES or resolves to an unexpected loan, leave that payoff cell unchanged and flag
  it in the Phase 5 report — never write an unverified number.

#### Phase 2b — INVESTOR-SUM CHECK (MANDATORY, blocks the write)

Added 2026-08-13 after a live failure: the 20260816 run wrote **273,816.67** into `Utah Shoe III`.
That was loan 131's LOAN-LEVEL payoff. XL's own line was 48,460.00 and OKOA Partners' was
225,356.67 — and **48,460.00 + 225,356.67 = 273,816.67 exactly**. The report handed XL the whole
pot and the 40% co-investor nothing. Every number was faithfully sourced from Hypercore, and the
sheet was still wrong, because the FIGURE'S SCOPE was never checked. Verifying the source is not
the same as verifying the scope.

**For every sheet you are about to write a Hypercore-sourced payoff into, run this before writing:**

```
# 1. XL's participation on the loan. If it is not 100, a loan-level payoff is FORBIDDEN.
doppler run --project hypercore-ask --config dev_personal -- \
  python3 .claude/scripts/hca-funding.py --figure funding_participation \
    --loan-id <LOAN_ID> --funding-entity-id 3

# 2. Every investor's outstanding on that loan. Sweep entity ids 1,2,3 (at minimum) —
#    1 = OKOA Partners, 2 = OKOA Management, 3 = XL. Sum them.
doppler run --project hypercore-ask --config dev_personal -- \
  python3 .claude/scripts/hca-funding.py --figure funding_outstanding \
    --loan-id <LOAN_ID> --funding-entity-id <E>
```

Then apply all three gates. **Any gate failing = do not write. Leave the cell unchanged and flag it
in the Phase 5 report.**

| Gate | Test | Why it fires |
|---|---|---|
| **G1 — scope** | Value about to be written **≠** the sum of all investors' `funding_outstanding` | If it EQUALS the sum, you are writing the whole loan into one investor's sheet |
| **G2 — participation** | Using a loan-level `payoff_as_of` **requires** `funding_participation` == 100 | At 60% the loan payoff is not XL's number, and 60% of it is not either — participation and outstanding are different fields, never derive one from the other |
| **G3 — commitment** | Sheet cell **B11** should equal XL's `funding_commitment` | Confirms the sheet is investor-scoped, and catches a wrong loan id |

Record the participation percentage and the investor sum in the provenance companion for every
sourced sheet, so a future reader can re-run the check without re-querying.

**This check does NOT override a "no change" or "carry forward" row in the workbook table.** Those
sheets are never sourced, so there is nothing to gate. Argent proves the point: a surprising
Hypercore figure gets written only where the table says to source from Hypercore.

### Phase 3 — Narrative (acos-fireflies-ask — RECENT: ≤2 weeks, last week primary)
For each loan worksheet, build the **Progress Made This Week** bullets (≤5) and any **Key Issues /
Blockers** bullets. **This is a WEEKLY update — recency is a hard rule, not a preference.**

0. **RECENCY RULE (mandatory).** Compute the cutoff = **report date − 14 days** (e.g. a 07/05 report →
   `2026-06-21`). Build the **eligible meeting allow-list** = every cached Fireflies meeting dated on or
   after the cutoff (`fireflies_search.py list --from <cutoff>`; refresh the cache first). A bullet may
   cite ONLY an eligible meeting — **never anything older**. The **primary focus is the LAST WEEK**
   (report date − 7 days .. report date): lead with those meetings; the earlier half of the window is
   secondary context only. This recency is also machine-enforced downstream by
   `xl_provenance.py --min-date <cutoff>` (any older source is flagged `OLDER THAN CUTOFF` and the
   `stale_sources` count must be 0).
1. **Pull each loan's recent activity from Fireflies** (eligible meetings only):
   ```
   /acos-fireflies-ask "What happened on the <loan/property> loan since <cutoff>?"
   ```
   Use the loan's real-world name/property/borrower for the query (e.g. Motel 6 / Warburton for
   Riverdale, Beehive / Wolfgramm for Ascent Senior, the property city/name for the others).
   Portfolio-wide meetings (the weekly *Credit Committee / Portfolio* and *Pipeline Meeting*) are the
   best place to find updates on quieter loans — check them before concluding a loan has none.
2. **COUNT this cycle's updates per loan, then decide (CONTINUITY RULE — this governs quiet loans).**
   An **update** = one distinct, substantive new development about the loan this cycle, drawn from
   an **eligible-window** (≤2-week) Fireflies meeting line, **or** from a Phase 3b **email finding**
   inside the same window, **or** from a document / user-provided input supplied for this run (e.g. a
   borrower letter, a buyer count). Count them per loan, then:
   - **≥ 2 updates → compose fresh** from those updates (strict-recency path). The prior week's bullets
     (`progress_current`) tell you which storylines to look for, but a storyline with **no update this
     cycle is DROPPED, not carried**. Keep the **top 5** most material points (payoff-relevant,
     legal/foreclosure, refinance/extension, buyer/sale progress).
   - **exactly 1 update → carry forward last week's bullets for that loan, then ADD the one new update**
     as an extra bullet. Do not otherwise rewrite the carried bullets.
   - **0 updates → carry forward last week's bullets VERBATIM** (the `progress_current` /
     `blocker_current` from the manifest). Do NOT blank the loan, and do NOT invent activity.
   - When you carry forward AND add a new update, **drop any carried `"No recent updates received…"`
     line** — it must never coexist with a real bullet. Respect the slot caps (**≤5 progress, ≤3
     blockers**); if carry-forward + new exceeds them, keep the new update plus the most material carried
     points and note the drop. Carried bullets are marked `[carried]` in the companion (see item 6), so
     the repeat is explicit and honest — never a stale point *dressed as current*.
3. **Neutral placeholder is a FALLBACK, not the default for quiet loans.** Use
   `"No recent updates received from the borrower."` as a loan's only bullet **only when there is nothing
   to carry forward** — a brand-new loan, or a prior week that itself had no substantive bullet.
   Otherwise a quiet loan (0–1 updates) keeps last week's points per the continuity rule above.
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

### Phase 3b — Email sweep (BOTH mailboxes, read-only) — Zee, 2026-08-13

Run AFTER Phase 3's Fireflies pass, so email adds to the picture rather than driving it.

```
bun .claude/skills/acos-xl-update/scripts/xl_mail_sweep.ts \
  --since <cutoff YYYY-MM-DD>  --out mail_sweep.json
```

`--since` is the SAME cutoff as Phase 3 (report date − 14 days). Add `--dry-run` to print each
mailbox's auth mode and exact query without contacting anything. `--mailbox ziaul|jason` narrows it.

**How it reaches two accounts from one window.** Each mailbox belongs to a different claude.ai
account, and the claude.ai connectors follow the logged-in account. The sweep spawns a one-shot
`claude -p` per mailbox, pinned to the right account. It works identically whichever window you
started the skill in:

| Mailbox | Account that owns its Gmail connector | How the subprocess is pinned |
|---|---|---|
| `ziaul@okoacapital.com` | Zee's own personal Claude account | `CLAUDE_CONFIG_DIR` + `CLAUDE_SECURESTORAGE_CONFIG_DIR` = `/Users/zee/.claude-personal` |
| `jason@okoacapital.com` | the boss's account (the default config dir) | **both vars REMOVED from the environment** |

**Never retype the default config dir into those vars** — proven to fail 2026-08-13 with
`Not logged in`, because the default settings file lives at `~/.claude.json` (not inside
`~/.claude/`) and the default Keychain drawer keeps its legacy unsuffixed name. To restore default
behaviour you REMOVE the variables. The script already does this; do not "fix" it by setting them.

**What comes back.** Per mailbox, a JSON list of findings, each `{date, subject, loan, point,
confidence}`. Subject line, date, loan, and a one-sentence summary — **never body text, senders,
recipients, quotes, links, or attachments.**

**What to do with a finding:**
- It **counts as an update** for the Phase 3 CONTINUITY RULE, exactly like a Fireflies line.
- Only findings dated **on or after the cutoff** may be used. Older ones are dropped like any other
  stale source.
- **A number seen in an email is NEVER written to the workbook.** Payoffs come from Hypercore
  (Phase 2) and Utah Shoe III comes from the Dropbox carry-forward — email cannot override either.
  If an email disagrees with a figure, surface it as a FLAG in Phase 5 and change nothing.
- `confidence: low` findings are leads for Zee, not bullets. Report them; do not compose from them.

**A mailbox that cannot be reached is a NOTE, not a failure.** The script prints
`NOTE — <mailbox> unreachable: <reason>` and returns `ok: false` with empty findings. Record it in
the companion and carry on — an email outage never blocks the report.

**Read `findings: []` honestly.** Empty means "nothing matched the query", not "nothing happened".
For `jason@` it means specifically: nothing matched **among already-read messages**. Say it that way.

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
  --spec prov_spec.json  --min-date <cutoff YYYY-MM-DD> \
  --out "/Users/zee/Documents/OKOA/XL Ant Weekly Update Draft/XL Ant Portfolio Update <YYYYMMDD> — Sources & Provenance.md"
```
Confirm the audit prints `unverified_quotes: 0`, `sourceless_new_bullets: 0`, AND `stale_sources: 0`.
`--min-date` = the Phase 3 cutoff (report date − 14 days); any source older than it is flagged
`OLDER THAN CUTOFF` and counts as stale. If any count is non-zero, fix it (copy the quote verbatim,
or drop an out-of-window source) and re-render — an unverifiable or stale reference must not ship.

**Then APPEND the email section** to that same companion — after `xl_provenance.py` has rendered and
audited it, so the audited counts are never disturbed. One `## Email sweep` heading, then per mailbox:
the query run, and one line per finding — **mailbox · date · subject line** only, plus which bullet it
fed (or `lead only — not used`). **Never the body text.** A mailbox that was unreachable gets a line
saying so. `findings: []` is written as "nothing matched the query" — and for `jason@`, as "nothing
matched among already-read messages".

```
## Email sweep (read-only)

### ziaul@okoacapital.com
query: after:2026/07/31 (XL OR "Utah Shoe" OR …)
- 2026-08-13 · "Re: Appraisal: 4080 Cooper Lane, Park City, UT 84098" → Ascent Senior, progress bullet 2
- 2026-08-13 · "Re: Dropbox Access FW: Okoa v. Wolfgramm"             → lead only — not used

### jason@okoacapital.com  (read-only; is:read enforced)
query: … is:read
- nothing matched among already-read messages
```

### Phase 5 — Report for review (do NOT send)
Give the user clickable links to **both** the workbook AND the reference companion, plus a concise
change report:
- **Payoffs:** each loan → old value → new value → **Hypercore provenance** (or "unchanged" /
  "flagged: <reason>"). Show the Lux II arithmetic (current + 7 × per-diem).
- **Narrative:** per loan, the final bullets, marked `[carried forward]` vs `[new — Fireflies: <meeting/date>]`
  vs `[new — email: <mailbox> <date>]`.
- **Email sweep:** which mailboxes were reached, how many findings each returned, and every
  `confidence: low` finding listed as a LEAD for Zee (not written into the workbook). Any email that
  DISAGREES with a Hypercore figure or the Utah Shoe III carry-forward is flagged here, loudly, with
  the number left unchanged. State an unreachable mailbox plainly; never let it pass as "nothing found".
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
- **Email sweep:** `bun` + `scripts/xl_mail_sweep.ts` + `/opt/homebrew/bin/claude`. No API key and no
  Gmail tool is held by this skill — each mailbox is read by a one-shot `claude -p` subprocess pinned
  to the account that owns that mailbox's claude.ai connector. The two logins live in separate macOS
  Keychain drawers (`Claude Code-credentials` for the boss, `Claude Code-credentials-ad7ff1c5` for
  Zee's own personal account), so neither can sign the other out. See
  `reference_claude_code_config_dir_isolates_keychain` for the tested details.
- Python 3 + openpyxl (system python3 has it); `xl_provenance.py` needs only stdlib + `zoneinfo`
  (Python 3.9+). LibreOffice optional (only to bake cached values / render a PDF preview; not required
  — Excel recalculates on open via `fullCalcOnLoad`).
