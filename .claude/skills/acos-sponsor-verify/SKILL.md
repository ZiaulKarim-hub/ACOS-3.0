---
name: acos-sponsor-verify
user-invocable: false
description: "Sponsor background verification, track-record corroboration, and cross-document fraud-forensics research. Treats every sponsor-supplied claim (track record, litigation history, entity status, credentials) as a CLAIM, not a fact, until a named public third party corroborates it — and treats a contradiction between the deal file's own documents as a hard fabrication tripwire. Produces a claim-by-claim Corroboration Ledger with confidence scoring and full provenance. Triggers on: sponsor verification, track record verification, fraud forensics, background check, entity search, business entity lookup, litigation search, judgment search, license verification, OFAC check, sanctions screening, cross-document contradiction, fabrication check, sponsor due diligence, guarantor background."
version: 1.0.0
updated: 2026-07-13
---

# Sponsor-Verify Fraud-Forensics Engine

Corroborate — or falsify — every material claim a sponsor, borrower, guarantor, or deal
memo makes about track record, credentials, litigation history, and entity standing, using
public records and the deal file's own internal consistency. Produce a claim-by-claim,
confidence-scored, provenance-logged Corroboration Ledger, with explicit fabrication
tripwires that escalate hard when a claim contradicts a named third-party source or
contradicts another document in the same deal package.

## Ethos (read this first)

**A claim is a CLAIM until a named third party corroborates it.** Sponsor bios, track-record
summaries, litigation disclosures, and credential claims are treated as **assume-fabricated-
until-corroborated** — not out of malice toward any sponsor, but because self-reported figures
in a lending package are exactly the artifact fraud hides inside. "Unverified" is not the same
as "false" — an unverified claim may simply be true and hard to check. But unverified is also
not the same as "cleared," and it cannot by itself close out a deal-breaker-candidate objection.
Only a named, checkable, public source — or the sponsor's own contradicting document —
moves a claim off "unverified."

## When to Use

Use this skill when you need to:
- Verify a sponsor's, borrower's, guarantor's, or key principal's track-record claims
  (deal count, years of experience, completed rehabs, prior exits, stated returns)
- Check entity existence, good standing, formation date, and officers/managers for any
  LLC/LP/corp named in the deal (sponsor entity, borrower SPE, guarantor entity)
- Screen for undisclosed litigation, judgments, liens, bankruptcies, or foreclosures
  against a sponsor, principal, or entity
- Verify a claimed contractor, broker, appraiser, or lender license is active and free of
  discipline
- Screen sponsors/guarantors/lender-counterparties against OFAC sanctions and adverse media
- Cross-check every material figure and date across ALL documents in a deal file for
  internal contradiction (the fabrication tripwire)
- Pre-IC screening before Seat #6 (Sponsor & Fraud-Forensics) forms its opening objections

## Usage

```
acos-sponsor-verify "[Sponsor Name / Entity]" --deal <session>/deal-brief/
acos-sponsor-verify "Smith Capital LLC, John Q. Smith (manager)" --preset fraud_deep_dive
acos-sponsor-verify "Alex Marqueda" --lookback 10 --states UT,NV
```

**With options:**
```
acos-sponsor-verify "[Sponsor Name]" --cost-limit 30 --court-depth full
acos-sponsor-verify "[Sponsor Name]" --states-auto  # infer from deal brief + entity filings
```

## Core Tenets

1. **Assume fabricated until corroborated.** Every sponsor-supplied figure or claim starts
   at status `unverified` by default. It moves to `verified` only when a named,
   independently-checkable public source (or a second deal-file document reporting the same
   fact from an independent chain) confirms it.
2. **A contradiction is louder than an absence.** Finding nothing (no public record either
   way) is a normal, non-alarming `unverified`. Finding a source or a sibling document that
   affirmatively conflicts with the claim is a `contradicted` HARD FLAG — always escalate it,
   regardless of how minor it looks.
3. **Independence first.** Build the full inventory of material claims from the shared deal
   brief ALONE, before running a single public lookup. This skill corroborates the seat's
   independently-formed suspicions — it does not manufacture them from what the lookups
   happen to find.
4. **Provenance is mandatory.** Every ledger row carries source, portal/citation, locator
   (case #, entity #, doc ID, book/page, URL), and an as-of retrieval date. A claim with no
   provenance line is not a finding — it is an unsupported assertion and must stay
   CONJECTURE.
5. **Official/public sources first; aggregators are corroborative signals only.**
   Secretary of State portals, licensing boards, court portals, county recorders, and OFAC
   are authoritative. Bizapedia, generic people-search sites, and news aggregation are
   signals to chase down, never citations to rest a `verified` status on alone.
6. **No legal, insurance, or investment conclusions.** This is diligence-support research.
   It does not determine creditworthiness, adjudicate fraud, or replace counsel, background-
   check vendors, or underwriting judgment.

## Confidence-Scoring Rubric

Every individual **check** (one source consulted for one claim) gets a confidence score
before it feeds the ledger's claim-level `status`.

```
Score(check) = Authority x Corroboration x Recency x DataQuality
```

**Authority Scale:**

| Source Type | Weight |
|-------------|--------|
| Official gov portal (SOS, license board, court docket, county recorder, OFAC) | 0.99 |
| Federal court record via PACER/CourtListener (official docket) | 0.97 |
| Licensing-board disciplinary record | 0.95 |
| Reputable named news outlet / adverse media (bylined, dated, checkable) | 0.75 |
| Aggregator (OpenCorporates, Bizapedia, generic people-search) | 0.50 |
| Sponsor-supplied document alone, no independent chain | 0.20 |
| Anonymous / unverifiable source | 0.10 |

- **Corroboration:** boost when >=2 independent authoritative sources agree; a single
  sponsor-supplied document is never, by itself, corroboration.
- **Recency:** boost when a license/entity/litigation status was checked as of the report
  date (public registries are point-in-time — always re-state the as-of date; don't reuse a
  stale check silently).
- **Data Quality:** reduce for partial name matches, common-name ambiguity, redacted
  records, or low-confidence OCR on scanned exhibits.

**Confidence Labels** (identical thresholds to Title-Sleuth, for cross-seat consistency):

| Label | Criteria |
|-------|----------|
| **Verified** | Score >= 0.92 OR corroborated across >= 2 authoritative sources |
| **Probable** | 0.80 <= Score < 0.92 OR partial corroboration |
| **Unconfirmed** | Score < 0.80 OR unresolved conflict |

### Ledger Status (derived from confidence label + contradiction check)

The Corroboration Ledger's per-claim `status` is a 3-value enum, derived — never
self-reported:

| Status | Derivation |
|--------|-----------|
| **verified** | Label is Verified or Probable, from >= 1 independent public/third-party source, AND no contradiction found anywhere. |
| **unverified** | Label is Unconfirmed — no independent corroborating source found (or only the sponsor's own document exists). Absence of evidence, not evidence of absence. |
| **contradicted** | ANY corroborating check — a public source OR a sibling deal-file document — affirmatively conflicts with the claim. Overrides a prior "verified" reading until reconciled. HARD FLAG (see Fabrication Tripwires). |

## SOURCES / Authority Catalog

### 1. Secretary of State — Business-Entity Search
Existence, good standing, formation date, registered agent, officers/managers/members.
Resolve the correct state(s) dynamically from the sponsor's stated state(s) of formation
and operation (and from any entity number already in the deal file); do not assume Delaware
or the property's state without checking.

| State (illustrative — resolve per-deal) | Portal |
|---|---|
| Delaware | Division of Corporations — icis.corp.delaware.gov |
| California | Bizfile Online — bizfileonline.sos.ca.gov |
| Nevada | SilverFlume / NV SOS — nvsilverflume.gov, nvsos.gov |
| Utah | Division of Corporations (OneStop) — corporations.utah.gov |
| Texas | SOSDirect / Comptroller Taxable Entity Search — comptroller.texas.gov |
| Florida | Division of Corporations — sunbiz.org |
| New York | Dept of State Division of Corporations — apps.dos.ny.gov/publicInquiry |
| Arizona | Corporation Commission — ecorp.azcc.gov |
| Cross-jurisdiction aggregator (corroborative signal only, NEVER authoritative alone) | OpenCorporates — opencorporates.com |

### 2. State Contractor & Professional License Boards
License status, expiry, disciplinary actions/complaints for any claimed contractor,
broker, appraiser, engineer, or architect credential.

| Board type (illustrative) | Portal |
|---|---|
| CA contractors | CSLB License Check — cslb.ca.gov |
| NV contractors | Nevada State Contractors Board — nvcontractorsboard.com |
| AZ contractors | Registrar of Contractors — roc.az.gov |
| UT professional licensing | DOPL — dopl.utah.gov |
| FL professional licensing | DBPR — myfloridalicense.com |
| TX professional licensing | TDLR — tdlr.texas.gov |
| Appraisers (national registry) | ASC National Registry — asc.gov |
| Mortgage loan originators / lenders | NMLS Consumer Access — nmlsconsumeraccess.org |

### 3. Court Records
| Layer | Portal / Notes |
|---|---|
| Federal civil/bankruptcy — free-first | CourtListener/RECAP — courtlistener.com (search before paying PACER) |
| Federal civil/bankruptcy — paid | PACER — pacer.uscourts.gov ($0.10/pg, capped $3/doc; **chair approval required**, see Constraints) |
| State civil / judgment | Varies by state — e.g. Utah Courts XChange (secure.utcourts.gov/xchange), Clark County NV Odyssey (Eighth Judicial District), Maricopa County AZ Superior Court eAccess |
| Bankruptcy | PACER (national index) + CourtListener free archive |
| County recorder (liens/UCC/lis pendens) | Same catalog Title-Sleuth uses for chain-of-title — if Seat #4/Title-Sleuth has already run on this deal, READ its sidebar (`<session>/sidebars/seat-04-title-report.md`) rather than re-searching; cross-cite instead of duplicating |

### 4. Sanctions & Adverse Media
| Source | Portal |
|---|---|
| OFAC SDN List | sanctionslist.ofac.treas.gov (Sanctions List Search) |
| Adverse media / news | WebSearch: sponsor/principal name + "lawsuit", "fraud", "indicted", "SEC", "foreclosure", "bankruptcy", "complaint" |
| Lender/broker counterparty screening | NMLS Consumer Access — nmlsconsumeraccess.org |

**OFAC/SDN hit on any named sponsor, principal, or guarantor is an automatic HARD FLAG** —
see Fabrication Tripwires. Screen every named natural person and every named entity, not
just the primary sponsor.

### 5. Track-Record Corroboration
Verify a claimed project list against public records, not against the sponsor's own summary.

| Check | Portal |
|---|---|
| Deed of record (did this sponsor/entity actually own/transact the claimed asset?) | County recorder grantor/grantee index, by claimed project's county |
| Building permits (was rehab/construction work actually pulled/completed under this name?) | City/county building-permit portal, by address |
| Sale / refinance record (did the claimed exit actually close, at the claimed price/date?) | County recorder + assessor transfer history |

### 6. Cross-Document Contradiction Detection (the fabrication tripwire)
Not a public portal — an internal protocol step against the deal file's own corpus.

| Source | Method |
|---|---|
| Internal — Deal File Corpus | `Glob` every document in the deal brief/session folder; `Grep` for every instance of each material figure/date/claim (years of experience, deal count, dollar amounts, entity names, dates); diff instances across documents for drift or outright contradiction |

## PROTOCOL

Execute these phases in order. Each phase names the tool(s) it runs with — this skill is
grounded to Read, Write, Glob, Grep, Bash, WebSearch, WebFetch only; there is no Task/agent
spawn inside this protocol (that lives one layer up, in the seat that carries this skill).

### Phase 0 — Independence: Build the Claim Inventory (Read, Glob, Grep)

Before any public lookup, extract the FULL inventory of material claims from the shared deal
brief alone:
- `Glob` the deal-brief/session folder for every document (memo, sponsor bio, PPM, loan
  request/application, appraisal, org chart, financials).
- `Read` each one. Extract every claim bearing on: sponsor/principal identity, entity names
  and formation states, track record (deal count, years of experience, completed
  projects/exits, claimed returns), credentials/licenses, and any litigation/bankruptcy
  disclosure (or notable absence of one).
- For each claim, record: `claim_text`, `source_document`, and whether it is `material`
  (touches Sponsor/Track-Record or Fraud/Misrepresentation).
- Do NOT run any WebSearch/WebFetch yet. This phase is blind-independent by design.

### Phase 1 — Cross-Document Contradiction Sweep (Grep, Read)

For every material claim, `Grep` across ALL deal-file documents for other mentions of the
same fact (same figure, same date, same project, same entity, same years-of-experience
statement). Build a same-claim cluster per fact. Any cluster where documents disagree
(a number, a date, a project count, a "completed" vs "in progress" status) is logged now,
before any public lookup — this is often the sharpest fabrication signal available and
costs nothing to find. Flag the canonical example pattern: a summary memo claiming "15
years / 10 completed rehabs" against the borrower's own loan request/application stating
"this is my first project" — log this class of finding as `contradicted` immediately.

### Phase 2 — Entity & Licensing Verification (WebSearch, WebFetch)

For every named entity and every claimed professional credential:
- `WebSearch` to locate the correct state SOS portal (or license board) for the entity's/
  principal's stated state.
- `WebFetch` the entity-search result page or license-lookup result page. Capture: status
  (active/dissolved/revoked/not found), formation/issue date, registered agent, officers/
  managers, expiry, disciplinary history.
- If a claimed entity or license does NOT appear in the relevant registry, or an entity
  number cited in the deal file does not resolve, log it now — a non-existent or unfindable
  entity/license is a Phase-5 escalation candidate, not a silent gap.

### Phase 3 — Litigation, Bankruptcy & Sanctions Screening (WebSearch, WebFetch)

- Free-first: `WebSearch`/`WebFetch` CourtListener/RECAP for the sponsor's and each named
  principal's/entity's name, before considering PACER.
- If federal dockets require PACER and the projected cost exceeds a nominal, trivial lookup,
  STOP and request chair approval (default cost cap $30 — see Constraints) before proceeding.
- `WebFetch` relevant state civil-court portals for the sponsor's stated state(s) of
  residence/operation and the property's state.
- `WebFetch` or `WebSearch` the OFAC Sanctions List Search for every named natural person
  and entity. An OFAC/SDN hit is an immediate HARD FLAG — surface to the chair before
  continuing further research on that party (see Constraints).
- `WebSearch` for adverse media using the sponsor/principal name plus fraud/litigation/
  regulatory keywords. Log bylined, dated, checkable results only — discard unattributable
  forum chatter.

### Phase 4 — Track-Record Corroboration (WebSearch, WebFetch, Bash+pdftotext where needed)

For each claimed prior project/exit in the sponsor's track record:
- `WebSearch`/`WebFetch` the relevant county recorder's grantor/grantee index for the
  claimed sponsor name/entity and the claimed project's county, to find a deed showing
  actual ownership/transaction.
- `WebFetch` the relevant building-permit portal for the claimed address to check whether
  claimed rehab/construction work was actually permitted/completed under this sponsor's
  name.
- `WebFetch` the county assessor/recorder sale-transfer history to confirm a claimed exit's
  sale price and date.
- Watch specifically for the **double-counted-asset tripwire**: two "different" track-record
  entries that resolve to the same parcel, the same recording instrument, or an overlapping
  date/workout event — this is a HARD FLAG, not a data-quality note.
- If a claimed project cannot be traced to any public deed/permit/sale record under the
  sponsor's claimed name or entity, log it as `unverified` (untraceable) — and if a public
  record instead shows a DIFFERENT owner/entity entirely for that asset, upgrade it to
  `contradicted`.

### Phase 5 — Score, Classify & Fire Tripwires

For every check gathered above, apply the Confidence-Scoring Rubric to get a per-check
score and label. Roll each claim up to one ledger `status` (`verified` / `unverified` /
`contradicted`) per the derivation rule above. Then run every claim through the Fabrication
Tripwires list (below) and mark `tripwire_fired` where applicable.

### Phase 6 — Chair Escalation Gate

Before any of the following, STOP and request explicit chair approval (do not proceed
silently):
- Any paid retrieval (PACER, licensed background-check API, etc.) — state the projected
  cost against the $30 default cap.
- Any search expanding beyond the sponsor's stated state(s) + the property's state (a
  broad/multi-jurisdiction sweep).
- Any HARD FLAG tripwire (OFAC hit, cross-document contradiction on a material claim,
  double-counted track-record asset) — surface immediately, don't bundle into the final
  report only.

### Phase 7 — Produce the Corroboration Ledger & Side Report (Write)

Assemble the full Corroboration Ledger (Data Model below) and write the side report to
`<session>/sidebars/seat-06-sponsor-report.md` via `Write` (or `Bash` heredoc if `Write` is
unavailable). Fold material `contradicted` and material `unverified` findings back into the
seat's JSON objections, citing the ledger row (`claim_id` + citation + locator) as the
objection's `evidence`.

## Fabrication Tripwires (explicit hard-flag rules)

These escalate regardless of how the rest of the ledger reads. A tripwire firing on a
`material` claim should be treated by the calling seat as at minimum `material-risk`, and
as `deal-breaker-candidate` when it goes to the deal's core Sponsor/Track-Record or Fraud/
Misrepresentation kill-criteria:

1. **Cross-document contradiction** — a material claim in the memo/summary conflicts with
   the borrower's/sponsor's OWN document (e.g., "15 years / 10 completed rehabs" in a
   sponsor summary vs. "this is my first project" in the borrower's own loan request). This
   is the defining tripwire of this skill — always a HARD FLAG.
2. **OFAC/SDN hit** on any named sponsor, principal, guarantor, or entity — immediate HARD
   FLAG, escalate to the chair before continuing.
3. **Entity or license not found, expired, or under active discipline** at the relevant SOS/
   licensing-board portal, where the deal file represents it as active/current.
4. **Undisclosed judgment, lien, bankruptcy, or foreclosure** against a sponsor/principal/
   entity that is NOT mentioned anywhere in the deal file.
5. **Untraceable track-record project** — no public deed/permit/sale record under the
   sponsor's claimed name/entity for a claimed prior project (log `unverified`; if a public
   record shows a different owner entirely, upgrade to `contradicted`).
6. **Double-counted track-record asset** — the same underlying parcel/instrument/workout
   event appearing twice under different project names or entities in the claimed track
   record.
7. **Material numeric or date drift** across documents beyond plausible rounding (dollar
   amounts, unit counts, dates, years-of-experience, deal counts).

## Data Model

### Claim
```yaml
claim:
  claim_id: string
  claim_text: string          # verbatim or close paraphrase of the sponsor/deal-file claim
  source_document: string     # which deal-file doc it came from
  material: true|false        # bears on Sponsor/Track-Record or Fraud/Misrepresentation
  checks: [check]             # see below
  confidence_score: number    # 0.0-1.0, rolled up per the scoring formula
  confidence_label: Verified|Probable|Unconfirmed
  status: verified|unverified|contradicted
  tripwire_fired: string|null
  notes: string|null
```

### Check
```yaml
check:
  source_type: sos|license_board|court_pacer|court_courtlistener|state_court|county_recorder|ofac|adverse_media|nmls|permit_portal|assessor|internal_cross_document
  portal: string
  query: string
  result_summary: string
  citation: string            # portal/case name/doc name
  locator: string             # case #, entity #, doc ID, book/page, URL fragment
  as_of: YYYY-MM-DD
  authority_weight: number
```

## OUTPUT

### Deliverables (all required unless noted)

**1. Executive Summary** (<= 300 words)
- Overall fabrication-risk read (how many material claims land `contradicted`,
  `unverified`, or trigger a tripwire)
- Any OFAC/sanctions hits or HARD FLAGS, stated first and plainly
- Entity/licensing status snapshot
- One-line characterization of track-record corroboration (how much of the claimed record
  is independently traceable)

**2. Corroboration Ledger** (the core deliverable — every material claim)

| Claim ID | Claim | Source Doc | Checks (source + citation + as-of) | Confidence (score/label) | Status | Tripwire |
|---|---|---|---|---|---|---|

**3. Fabrication Tripwires Fired**

| Claim ID | Rule # | Evidence | Escalation |
|---|---|---|---|

**4. Entity & Licensing Summary**

| Entity/Principal | Portal | Status | Formation/Issue Date | Officers/Managers | As-of | Confidence |
|---|---|---|---|---|---|---|

**5. Litigation & Adverse Findings**

| Party | Source | Case/Reference | Type | Status | As-of | Confidence |
|---|---|---|---|---|---|---|

**6. Track-Record Verification Table**

| Claimed Project | Claimed Role/Outcome | Public Record Match | Status | Notes |
|---|---|---|---|---|

**7. Cross-Document Contradiction Log**

| Fact | Document A says | Document B says | Resolution/Status |
|---|---|---|---|

**8. Open Questions / Chair-Approval Items** (paid retrievals not yet run, multi-jurisdiction
expansion requests, ambiguous name matches needing chair disambiguation)

**9. Sources & Retrieval Log**

| Item | Source Type | Portal | URL/Doc ID | Retrieved |
|---|---|---|---|---|

### Path
Write the full report to: `<session>/sidebars/seat-06-sponsor-report.md`

## Research Tools

- **Read** — read every document in the deal-brief/session folder; the source of the claim
  inventory in Phase 0.
- **Glob** — enumerate all deal-file documents needing the cross-document sweep.
- **Grep** — the fabrication-tripwire mechanism: find every instance of a material figure,
  date, or claim across the corpus and cluster them for contradiction-checking.
- **WebSearch** — locate the correct SOS/license-board/court/OFAC portal for a given
  jurisdiction; run adverse-media queries.
- **WebFetch** — retrieve specific entity-search results, license-lookup results, court
  docket pages, recorder/assessor pages, OFAC search results.
- **Bash + pdftotext/curl** — extract text from scanned deal-file exhibits; script
  API-style lookups (e.g., OFAC list search) where the portal permits it.
- **Write** — produce the Corroboration Ledger side report.

## Configurable Parameters

| Parameter | Options | Default |
|-----------|---------|---------|
| `states` | explicit list / auto-infer from deal brief | auto-infer (sponsor's stated state + property state only) |
| `lookback_years` | 1-30 | 10 |
| `court_depth` | skip / basic / full | basic |
| `paywall_tolerance` | none / capped / approved | capped |
| `cost_limit_usd` | 0-999 | 30 |
| `search_breadth` | narrow / standard / wide | standard |

## Verification Depth Presets

| Preset | When to Use |
|--------|-------------|
| `quick_screen` | Fast initial read — entity + OFAC + cross-document sweep only |
| `standard_verification` | Default — entity, licensing, litigation, track-record, cross-document, all at standard depth |
| `fraud_deep_dive` | Chair-directed escalation after a tripwire fires — full court depth, wider jurisdiction, deeper track-record tracing |

## Constraints

- **Never fabricate** a record, a citation, or a number. Mark **"unverified"** when unknown
  — never round an absence of evidence up to a finding.
- **Log provenance for every value** — source, citation, locator, and as-of date. A ledger
  row with no provenance is not a finding.
- **Respect portal terms and CAPTCHAs.** Never attempt to circumvent either; if blocked, log
  it as a data gap, not a workaround.
- **Chair approval required** before any paid retrieval (default cost cap **$30**) or any
  broad/multi-jurisdiction search beyond the sponsor's stated state(s) plus the property's
  state.
- **Public records + brief-supplied data only.** Never request or search for SSNs or other
  non-public identifiers. Use only what is independently public or already in the deal file.
- **Diligence support ONLY.** This is explicitly **NOT** insurance advice, **NOT** legal
  advice, and **NOT** investment advice. Findings inform the seat's objections; they do not
  themselves constitute a fraud determination or a lending decision.
- **"Unverified" is not "false."** Never let a claim's status drift from `unverified` to an
  implied negative finding without a genuine `contradicted` basis.
- **Independence first.** Build the claim inventory from the shared deal brief ALONE before
  any public lookup — this skill corroborates the seat's own objections; it does not
  originate them from whatever the lookups happen to surface.
- **Timeboxed passes.** Quick read -> validated -> final ledger. Don't perfectionist-stall
  chasing one more source past the deadline — a report with honest `unverified` rows on
  time beats a "complete" one that's late.

## Integration with the Investment Committee

- **Seat #6 (Sponsor & Fraud-Forensics)** carries this skill to corroborate (or falsify)
  the objections it forms independently from the deal brief.
- **Cross-reference, don't duplicate:** if Seat #4 (Legal & Structural) has already run
  Title-Sleuth on this deal, read its sidebar (`<session>/sidebars/seat-04-title-report.md`)
  for chain-of-title/lien findings rather than re-searching county recorder records from
  scratch.
- Material `contradicted` or material `unverified` ledger rows become the `evidence` behind
  the seat's JSON objections (citation = ledger row's citation, locator = ledger row's
  locator).

## Disclaimer

> This sponsor/fraud-forensics research is for informational and due-diligence purposes
> only. It does not constitute a background-check-vendor report, a legal opinion, insurance
> underwriting, or investment advice. An "unverified" status means no independent
> corroboration was found — it does not mean the claim is false. Consult qualified counsel,
> licensed background-check providers, and independent underwriting judgment before relying
> on these findings for any transaction decision.
