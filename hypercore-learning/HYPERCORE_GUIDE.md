# HyperCore — Operational Guide for Okoa Capital

**Author:** Generated for Zee from automated Playwright crawl + manual review
**Status:** Draft v1 — based on 25 of 33 active loans captured
**Last updated:** 2026-05-12

This guide is a personal-learning reference for HyperCore (`https://app.hypercore.ai`) — the loan-servicing software Okoa Capital uses to manage its private-credit real estate book. It was produced by logging into HyperCore via a Playwright script, capturing screenshots and HTML for every page reachable from the dashboard, and parsing the captures into structured data.

It is **not** an official HyperCore manual. It is reverse-engineered from observed behavior.

---

## Table of Contents

- [Chapter A — The Portfolio at a Glance](#chapter-a--the-portfolio-at-a-glance)
- [Chapter B — Anatomy of a Loan](#chapter-b--anatomy-of-a-loan)
- [Chapter C — Lifecycle & UI Map](#chapter-c--lifecycle--ui-map)
- [Appendix — What We Don't Know Yet](#appendix--what-we-dont-know-yet)
- [Appendix — Data Locations](#appendix--data-locations)

---

# Chapter A — The Portfolio at a Glance

## The Dashboard Is Okoa's Servicing Cockpit

When you land on `https://app.hypercore.ai/dashboard`, HyperCore shows five KPI tiles, two charts, and a notification panel. Together they answer the question "*how is Okoa's book doing right now?*"

### The Five KPIs (as of 2026-05-01)

| KPI | Value | What it actually means |
|---|---|---|
| **# Active Loans** | 33 | Loans currently being serviced through HyperCore. Doesn't include paid-off or written-off. |
| **Total Loan Approved** | $172.1M | Cumulative *committed* principal — what Okoa promised to lend across all 33 loans. |
| **Total Disbursement** | $169.2M | Cumulative *funded* principal — what's actually been drawn. The $2.9M gap to "Approved" is undrawn commitments (construction loans where Okoa hasn't released all stages yet). |
| **Total Repaid** | $36.8M | All cashflow received back across the book — principal + interest + fees combined. |
| **Total Outstanding Principal** | $164.7M | Principal still owed to Okoa today. Math: $169.2M disbursed - $4.5M principal repaid = $164.7M. |

### The Math Tells a Story

**$172.1M approved → $169.2M disbursed.** That's a **98.3% draw rate** — almost every dollar Okoa committed has been pulled. This is a "fully deployed" portfolio. The remaining $2.9M is undrawn commitment risk: Okoa is on the hook to fund it if construction continues per schedule.

**$169.2M disbursed → $164.7M outstanding.** Only **$4.5M of principal has been paid down** out of $169.2M. That's a 2.7% principal-paydown rate, which is exactly what you'd expect for a portfolio of short-term (12-24 month) interest-only construction and bridge loans — borrowers pay interest monthly, return principal only at maturity or exit.

**$36.8M repaid - $4.5M principal = ~$32.3M interest and fees collected** to date. On a ~$169M average book over (roughly) two years, that's a blended yield of ~10% — consistent with private-credit RE lending norms.

### The Revenue Chart Has Two Big Spikes

The "Revenue (Interest + Fees)" chart shows monthly cashflow into Okoa:

| Month | Revenue | What it likely is |
|---|---|---|
| Sep 2025 | $0.13M | Normal interest-only month |
| Oct 2025 | $0.24M | Normal |
| Nov 2025 | $0.11M | Normal |
| **Dec 2025** | **$1.97M** | **Spike** — likely a large loan payoff (principal + accrued interest + exit fee) |
| Jan 2026 | $0.76M | Elevated — maybe one mid-sized payoff |
| Feb 2026 | $0.20M | Normal |
| **Mar 2026** | **$2.62M** | **Spike** — biggest month, almost certainly a major payoff |
| Apr 2026 | $0.04M | Surprisingly low |

The pattern is consistent with a portfolio where **revenue is dominated by exit events** (payoffs at maturity), with steady-state monthly interest in the $100–250K range. If you want to understand a month's revenue, look at which loans matured or paid off that month.

### The Outstanding Principal Chart Is Boring (And That's the Point)

The "Outstanding Principal Over Time" chart shows the book staying right around $164M for the entire window. That's intentional — every loan that pays off is replaced by a new origination. A stable outstanding-principal line means **Okoa is running a level book, not growing it**. Growth would show as a rising line; runoff (winding down) would show as a falling line.

### The Notification System

In the top-right of every page, there's a bell icon with a number (95 as of last capture). Clicking it opens a panel listing recent events. We observed four event types in the wild:

- **Missed Payment** — `Payment for Loan #X on DATE hasn't been entered yet.` HyperCore is asking *you* to record a payment it expected. This means HyperCore drives a payment schedule and watches for posted payments against it.
- **Upcoming Payment** — `Loan #X has a scheduled payment of $X in 7 days.` 7-day lookahead.
- **Loan Maturing Soon** — `Loan #X is maturing in 30 days.` 30-day maturity warning.
- **Upcoming Payments** *(plural)* — `5 upcoming payments in 7 days.` Daily roll-up of the above.

**Why this matters operationally**: HyperCore is *not* automatically receiving payments from your bank — it's a record-keeping system. Someone at Okoa has to manually enter payments as they arrive, and HyperCore tracks deviation from the scheduled cashflow.

---

# Chapter B — Anatomy of a Loan

## Loan 57 — "Murdock - Oberland" (Case Study)

We captured every tab of Loan 57's detail page. This section walks through what each region of the page represents. Same structure applies to every loan in the portfolio.

The URL format is `https://app.hypercore.ai/loans/<integer-id>`. IDs are sequential integers issued at origination (Loan 2 is older than Loan 171). The currently-active book ranges from Loan 2 to Loan 171, with many gaps from paid-off legacy loans.

### Page Layout (3-Column Composition)

```
┌──────────────────────────────────────────────────────────────────┐
│ [Back]  Loan #57 - Murdock - Oberland             [Actions ▼]    │
├──────────────────────────────────────────────────────────────────┤
│ ┌─ LEFT (60% width) ────────────────┐  ┌─ RIGHT (40%) ────────┐  │
│ │ Current Summary  │  KPIs  │  Perf │  │ Top tabs:            │  │
│ │ (cards)          │ (gauges)│ chart│  │ Info | Terms |       │  │
│ │                                   │  │ Notes | Files        │  │
│ │ ──────────────────────────────── │  │ ──────────────────── │  │
│ │ Bottom tabs:                      │  │ Reference ID         │  │
│ │ Schedule | Original | Transactions│  │ Description          │  │
│ │  | Fees | Deposits | Aging        │  │ Type                 │  │
│ │ (data table)                      │  │ Owner                │  │
│ │                                   │  │ Funding Sources      │  │
│ │                                   │  │ ...                  │  │
│ └───────────────────────────────────┘  └──────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### Region 1 — Header Bar

- **`Back`** button: returns you to wherever you came from (notifications panel, loans list, etc.)
- **Title format**: `Loan #<id> - <client-or-property-name>` — the client name comes from the borrowing entity's `Client.name` field
- **`Actions ▼` button**: dropdown of mutating operations (record payment, edit, etc.). **You should never click this when reading data**; the safety logic in the crawler explicitly blocks it.

### Region 2 — Status Badge

Just below the title, a single-word status. Observed values across the 25 captured loans:
- **Disbursed** — all 25 of our captured loans (i.e., funded and currently servicing)

We didn't observe any loans in **Closed**, **Pending**, **Approved**, **Default**, or other states in this sample. Those exist as states in HyperCore's data model but no captured loans are currently in them.

### Region 3 — Current Summary (Left Column, Top)

Shows the *real-time* financial state of the loan as a set of paired metrics:

| Metric | Sub-fields |
|---|---|
| **Total** | Disbursed / Repaid / Outstanding / Overdue |
| **Principal** | Disbursed / Repaid / Outstanding / Overdue |

The dual-row layout lets you see both gross (Total = principal + interest + fees) and net-of-charges (Principal only). "Overdue" is the amount that should have been received per the schedule but hasn't been recorded yet.

**Loan 57 example**: Total Disbursed: $3,000,000 (matches Principal Disbursed because nothing else has been disbursed beyond principal — i.e., no fees rolled into the loan).

### Region 4 — KPIs (Left Column, Middle)

Three gauge-style metrics. For Loan 57:
- **17.19%** — almost certainly the **realized yield** to date on the loan (annualized IRR of cashflows received). High for traditional fixed-income, normal for private RE credit.
- **1.3x** — likely **MOIC** (multiple on invested capital) or **DSCR** (debt service coverage). Without a label we can't be sure; both are common loan-level KPIs.
- **1.3x** — second 1.3x ratio. If first is MOIC, this is probably DSCR (or vice versa).

We also observed these percentages in Loan 57's HTML: 23.33%, 27.5%, 46.67%, 67.2%. Likely: LTV (loan-to-value), LTC (loan-to-cost), and time-elapsed-on-term ratios.

### Region 5 — Performance Chart (Left Column, Top-Right)

A small chart visualizing loan-level cashflow vs. schedule over time. Not enough resolution in our screenshot to interpret precisely.

### Region 6 — Bottom Tabbed Table (Left Column, Bottom)

This is the **most operationally important** region. Six tabs that show different cashflow views:

| Tab | What it shows |
|---|---|
| **Schedule** | Current expected cashflow schedule (what's due, when) — *the live amortization schedule, including any modifications* |
| **Original** | The original schedule at funding — provides a baseline to compare modifications against |
| **Transactions** | Actual cashflows that occurred (payments recorded) |
| **Fees** | Fee schedule and accruals |
| **Deposits** | Money held by Okoa on the borrower's behalf (interest reserves, tax reserves, etc.) |
| **Aging** | Past-due amounts categorized by how long they've been overdue |

Columns we observed in the Schedule table: **Date, Disbursement, Principal Repayment, Interest Repayment** (and likely Fees, Total Cashflow extending off-screen).

This is where a servicer spends most of their time — entering payments into Transactions and checking Aging.

### Region 7 — Right-Side Metadata (Tabs: Info / Terms / Notes / Files)

The right pane shows loan metadata. Four tabs:

#### Info tab (default)
Captured fields from Loan 57:
- **Reference ID** — internal Okoa cross-reference (e.g., to a deal CRM)
- **Description** — free-text description of the deal
- **Type** — loan type (e.g., "Term Loan", "Bridge", "Construction")
- **Owner** — Okoa team member responsible (e.g., "Brad Heitmann" on Loan 57)
- **Funding Sources** (mini cap-stack table inside Info):
  - Cash external: row in cap stack
  - Maximum Loan Amount: $1,750,000.00 @ 7.30%
  - CRGM Partners: $625,000.00 @ 8.00%
  - (and likely more rows off-screen)

The Funding Sources table represents the **capital stack** — multiple sources funding this single loan. Each row has Amount + Rate. This is critical for participated loans where Okoa is not the sole lender or where Okoa uses external warehouse financing.

#### Terms tab
Captured fields (partial — full extraction pending):
- Loan Amount
- Approval Date
- Funding Date (we saw values like "03/27/2026")
- Maturity Date
- Term (12 months observed for Loan 57)
- Origination Fee
- Purpose (e.g., "Construction")
- Asset Type (e.g., "Real Estate")
- Contract Closing Date
- Date Modified (last edit timestamp)

#### Notes tab
Free-text comments from Okoa team members. Captured for sample loans but content not parsed.

#### Files tab
Attached loan documents (PDFs, etc.). HyperCore stores these — they're not just links. Note: any URL in the tab name "docs3" we saw suggests there's a counter or document-3-of-N pagination.

### What This Tells Us About HyperCore's Data Model

Inferred schema (one loan-detail page implies these tables):

```
Loan
  ├─ id, status, client_name, reference_id, description
  ├─ type, purpose, asset_type
  ├─ approval_date, funding_date, maturity_date, term_months
  ├─ origination_fee
  ├─ owner (FK → User)
  ├─ FundingSources[]  (cap stack — 1:N)
  │    └─ source_name, amount, rate
  ├─ Schedule[]        (1:N expected cashflows)
  │    └─ date, disbursement, principal, interest, fees
  ├─ OriginalSchedule[]   (immutable baseline)
  ├─ Transactions[]    (actual cashflows recorded)
  ├─ Fees[]
  ├─ Deposits[]        (reserves held)
  └─ Aging[]           (computed views)

Client
  └─ name (e.g., "Murdock - Oberland")
```

---

# Chapter C — Lifecycle & UI Map

## What Kind of Software Is HyperCore?

Technical signals we observed:

- **Tech stack**: React single-page application (no server-rendered HTML; all routes render the same shell with `<frontegg-app>` and `<noscript>` fallback). Tailwind / Material Design components. Likely Vite or Next.js underneath.
- **Auth**: Frontegg — a B2B-SaaS identity-as-a-service platform. The login flow uses OAuth (Google in our case, but Frontegg supports many providers).
- **URL pattern**: `/dashboard`, `/loans/<id>`, `/notifications`. Singular resource-detail routes with integer IDs.
- **Session**: Cookies expire on the order of minutes (not hours) — HyperCore is aggressive about inactive-session invalidation. Likely a security feature given the financial data.

The vibe: **HyperCore is a focused SaaS product for private credit loan servicing**, not a general accounting system. It does loan administration well; it probably does not do GL accounting or wire transfers itself.

## The Left-Rail Navigation (10 Icons)

From top to bottom on the blue sidebar (icons only, no text labels — we identified by visual inspection of the dashboard screenshot):

| # | Icon (visual) | Best guess at section | URL (confirmed?) |
|---|---|---|---|
| 1 | Hypercore atom logo | Home | redirects to `/dashboard` |
| 2 | Magnifying glass | Search | unknown |
| 3 | Grid (selected) | **Dashboard** | `/dashboard` ✓ |
| 4 | Book | **Loans portfolio list** | unknown (probably `/loans` but didn't render content for our automated crawler) |
| 5 | People | **Clients / Borrowers** | unknown |
| 6 | Pie chart | **Reports / Analytics** | unknown |
| 7 | Clipboard | **Tasks / Workflows** | unknown |
| 8 | Grid-w/-layout | **Funds / Capital sources** | unknown |
| 9 | Sheet | (unclear — possibly Documents library or Transactions) | unknown |
| 10 | Gear | **Settings** | unknown |
| 11 | Question mark | **Help / Docs** | unknown |

Plus the bottom of the rail:
- **OKOA workspace badge** — confirms tenant
- **Z avatar** — user menu (account, logout)

**This is the biggest gap in the guide.** We were never able to discover the actual URLs for icons 4–10. To fill the gap, you would need to manually open HyperCore, click each icon, and tell me what URL the address bar shows.

## The 25-Loan Portfolio Snapshot

The portfolio captured (25 of 33 currently active loans, sorted by loan ID — all currently "Disbursed"):

| Loan ID | Client / Project |
|---|---|
| 2 | Williams - River Haven |
| 4 | Cofi - Mappleton |
| 5 | Peterson Camille |
| 7 | One O Clock Hill Development |
| 23 | Fardown |
| 30 | Broadbent - Springville |
| 57 | Murdock - Oberland |
| 58 | Kohan - Golden East |
| 88 | Utah Shoe |
| 90 | Nash |
| 92 | Israelsen - Alpine |
| 110 | 25th Ave |
| 111 | Sidhu - Post Rd |
| 112 | NYC 233rd |
| 117 | 925 S Layton |
| 120 | Mossy Bark |
| 123 | Coslin Ave |
| 124 | Lilikoi |
| 131 | Utah Shoe III |
| 134 | Beehive Waldorff |
| 147 | Free Legation |
| 166 | Larkin - Red Ledges |
| 167 | Fletcher II |
| 169 | Haystack |
| 171 | Lux II LOC |

Notice the naming patterns: most are `<borrower-name> - <property/project>` (e.g., "Murdock - Oberland"). Some are just project names ("25th Ave", "NYC 233rd", "Coslin Ave"). "Utah Shoe" and "Utah Shoe III" suggests sequential loans to the same borrower. "Lux II LOC" implies this is the second tranche of a Lux line-of-credit.

The 8 loans we couldn't see are presumably the "quiet" ones — no missed payments, no upcoming maturities within 30 days, no upcoming payments within 7 days. They're paying exactly to schedule.

## Inferred Loan Lifecycle in HyperCore

Based on the fields we observed and the status states the data model supports, the workflow is:

```
1. Pre-Approval
     ↓ (Approval Date field gets set)
2. Approved
     ↓ (loan is created in HyperCore — status: Pending or similar)
3. Funded / Disbursed  ← all our captured loans are here
     ↓ (Funding Date set; disbursement transaction recorded;
        schedule generated from Term + rate + amount)
4. Servicing
     ↓ (monthly: borrower wires interest; Okoa manually records
        in Transactions tab; HyperCore reconciles against Schedule;
        Aging tab populates if late)
5. Maturity (term ends)
     ↓ (HyperCore sends "Loan Maturing Soon" notification at -30 days)
6. Payoff
     ↓ (Principal + accrued interest + exit fee paid in lump sum)
7. Closed (no longer in Active Loan count)
```

Refinances or extensions probably show as Schedule modifications (Original tab preserves the baseline, Schedule tab gets updated).

---

# Appendix — What We Don't Know Yet

This guide is incomplete in known ways. To upgrade it, the following are still needed:

| Gap | Why it matters | How to fill |
|---|---|---|
| **Real `/loans` portfolio URL** | Without it, we can only see loans with active notifications (25 of 33) | Manually navigate HyperCore, watch the URL bar when you click the book icon |
| **Other 8 active loans** | Could be brand-new originations or performing-perfectly loans worth knowing about | Find above; or visit each `/loans/<id>` until we find them by brute force (slow/noisy) |
| **`/clients` page structure** | Who are Okoa's repeat borrowers? Risk concentration? | Click the people icon, share URL |
| **`/reports` capabilities** | Crucial — this is where pre-built portfolio analytics live | Click the pie-chart icon |
| **`/settings` page** | Permissions, integrations, what other Okoa team members can do | Click the gear icon |
| **Actions ▼ dropdown contents on loan detail** | What state transitions can a servicer trigger? | Click it once in your browser (NOT in the script) and screenshot |
| **Inner table tab data (Schedule, Transactions, etc.)** | We screenshotted them but didn't parse the structured data | Run an extraction pass against the existing HTML files |
| **The 5 "ghost" loan IDs in our gap-filled crawl** | We saw IDs go up to 171 with massive gaps. These are probably paid-off loans that exist as inactive records | Try visiting `/loans/100`, `/loans/150`, etc. — those that return content are accessible historical loans |

---

# Appendix — Data Locations

Everything from this exploration lives under `hypercore-learning/`:

| What | Path | Description |
|---|---|---|
| **This guide** | [HYPERCORE_GUIDE.md](file:///Users/zee/Documents/Vibe%20Coding/ACOS%203.0/hypercore-learning/HYPERCORE_GUIDE.md) | The file you're reading |
| **Screenshots** | [data/screenshots/](file:///Users/zee/Documents/Vibe%20Coding/ACOS%203.0/hypercore-learning/data/screenshots/) | ~90 PNG files: dashboard, each loan overview, sample loan tabs, section pages |
| **Raw HTML** | [data/html/](file:///Users/zee/Documents/Vibe%20Coding/ACOS%203.0/hypercore-learning/data/html/) | ~90 HTML files — same set as screenshots. Useful for re-extracting data later without re-crawling |
| **Per-loan extracted data** | [data/loans/](file:///Users/zee/Documents/Vibe%20Coding/ACOS%203.0/hypercore-learning/data/loans/) | 25 YAML files named `loan_<id>.yaml`, one per captured loan |
| **Coverage / inventory** | [data/extracted/coverage_analysis.yaml](file:///Users/zee/Documents/Vibe%20Coding/ACOS%203.0/hypercore-learning/data/extracted/coverage_analysis.yaml) | Which loans have which captures |
| **Sidebar nav map** | [data/extracted/sidebar_nav.yaml](file:///Users/zee/Documents/Vibe%20Coding/ACOS%203.0/hypercore-learning/data/extracted/sidebar_nav.yaml) | (Currently empty — sidebar discovery failed) |
| **Loan list extraction** | [data/extracted/loans_list.yaml](file:///Users/zee/Documents/Vibe%20Coding/ACOS%203.0/hypercore-learning/data/extracted/loans_list.yaml) | First-run loan list — actually a loan-detail page extraction |
| **Master inventory v2** | [data/extracted/inventory_v2.yaml](file:///Users/zee/Documents/Vibe%20Coding/ACOS%203.0/hypercore-learning/data/extracted/inventory_v2.yaml) | URL probe results + section captures |
| **Master inventory v3** | [data/extracted/v3_inventory.yaml](file:///Users/zee/Documents/Vibe%20Coding/ACOS%203.0/hypercore-learning/data/extracted/v3_inventory.yaml) | Final crawl results — 25-loan capture manifest |
| **Crawl logs** | `data/*.log` | Timestamped logs of each crawl run |
| **Scripts** | [scripts/](file:///Users/zee/Documents/Vibe%20Coding/ACOS%203.0/hypercore-learning/scripts/) | The Python crawlers themselves |
| **Auth state (gitignored)** | `.auth/auth_state.json` | Saved session cookies. Lives only on this Mac. Mode 0600. Delete to "log out" the script. |

## Script Reference

| Script | What it does |
|---|---|
| [scripts/01_login.py](file:///Users/zee/Documents/Vibe%20Coding/ACOS%203.0/hypercore-learning/scripts/01_login.py) | Manual-login script. Opens visible Chrome, waits for you to log in via Google, saves cookies. **Re-run whenever the session dies.** |
| [scripts/02_crawl.py](file:///Users/zee/Documents/Vibe%20Coding/ACOS%203.0/hypercore-learning/scripts/02_crawl.py) | First-pass crawler. Found notification links, captured sample loans. |
| [scripts/03_recrawl.py](file:///Users/zee/Documents/Vibe%20Coding/ACOS%203.0/hypercore-learning/scripts/03_recrawl.py) | URL-probing recrawler. Failed due to overly-aggressive probe rejection. |
| [scripts/04_recrawl_v2.py](file:///Users/zee/Documents/Vibe%20Coding/ACOS%203.0/hypercore-learning/scripts/04_recrawl_v2.py) | Fixed probe logic. Captured many shell pages. |
| [scripts/05_extract.py](file:///Users/zee/Documents/Vibe%20Coding/ACOS%203.0/hypercore-learning/scripts/05_extract.py) | Parses captured HTML into per-loan YAML extracts. |
| [scripts/06_full_crawl.py](file:///Users/zee/Documents/Vibe%20Coding/ACOS%203.0/hypercore-learning/scripts/06_full_crawl.py) | Streamlined comprehensive crawl. Captured all 25 reachable loans. |
| [scripts/lib/session.py](file:///Users/zee/Documents/Vibe%20Coding/ACOS%203.0/hypercore-learning/scripts/lib/session.py) | Shared helpers: load session, snapshot a page, safety rails. |

## Re-Running

When the session cookies expire (~1 hour), to refresh data:

```bash
cd "/Users/zee/Documents/Vibe Coding/ACOS 3.0/hypercore-learning"
.venv/bin/python scripts/01_login.py    # log in via Google
.venv/bin/python scripts/06_full_crawl.py    # immediately crawl
.venv/bin/python scripts/05_extract.py    # rebuild per-loan YAMLs
```

## Safety Guarantees in the Code

Every script imports `lib/session.py` which enforces:

- **Domain allowlist**: every page URL must be on `app.hypercore.ai`. Any redirect to `auth.hypercore.ai` or elsewhere triggers an immediate abort.
- **Verb blocklist on clicks**: the `safe_to_click()` function refuses to click anything whose text matches `submit | save | delete | pay | fund | disburse | approve | reject | release | edit | update | create | new loan | add | invite | transfer | etc.` (full list in `FORBIDDEN_VERBS`).
- **No form interaction**: no `page.fill()`, no `page.type()`, no form submission anywhere in any script.
- **File mode 0600 on auth_state.json**: only your Mac user can read it.
- **Read-only by HTTP semantics**: every navigation is a GET request.

If you ever want to add write capabilities (e.g., to automate payment entry), you would do that in a *separate* script with its own approval flow — not by modifying the read-only crawlers.
