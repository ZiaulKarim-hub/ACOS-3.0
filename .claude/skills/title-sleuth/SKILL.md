---
name: title-sleuth
user-invocable: false
description: "Property title research and chain-of-title analysis. Identifies current and historical ownership, mortgages, liens, judgments, and tax status from public records. Produces confidence-rated reports with full provenance. Triggers on: title search, title report, chain of title, ownership history, lien search, encumbrance search, property ownership, title research, who owns this property."
version: 1.0.0
updated: 2026-02-13
---

# Title Sleuth Research Engine

Identify current and historical property ownership and associated liabilities (mortgages, deeds of trust, liens, judgments, taxes) across U.S. states and territories by consulting official sources, cross-verifying records, and producing a documented, confidence-rated report.

## When to Use

Use this skill when you need:
- Chain of title / ownership history for a property
- Active encumbrance search (mortgages, deeds of trust, liens, judgments)
- Tax status and delinquency checks
- UCC fixture filing searches
- Court/lis pendens/judgment searches against a property or owner
- Pre-DD title screening before underwriting
- Discrepancy investigation (assessor vs recorder disagreements)

## Usage

```bash
title-sleuth [address or APN]
title-sleuth "1234 Main St, Phoenix, AZ"
title-sleuth "APN 123-45-678, Maricopa County, AZ"
title-sleuth "owner: Smith Family Trust, Clark County NV"
```

**With options:**
```bash
title-sleuth "1234 Main St, Phoenix, AZ" --preset underwriting_depth
title-sleuth "1234 Main St, Phoenix, AZ" --lookback 30 --include-courts full
```

## Core Tenets

1. **Official sources first** — county recorder, assessor, tax collector, state SOS/UCC, court portals. Third-party aggregators are corroborative signals only.
2. **Normalize everything** — identifiers, dates (YYYY-MM-DD), legal descriptions, money formats before analysis.
3. **Show conflicts** — when sources disagree, present both claims with a preferred reading and rationale.
4. **Provenance is mandatory** — URL/portal path, document ID, recording #/book-page, and retrieval timestamp attached to every non-trivial claim.
5. **No legal conclusions** — this is research, not legal advice or title insurance.

## Confidence Labels

Every finding must be labeled:

| Label | Criteria |
|-------|----------|
| **Verified** | Score >= 0.92 OR corroborated across >= 2 authoritative sources |
| **Probable** | 0.80 <= Score < 0.92 OR partial corroboration |
| **Unconfirmed** | Score < 0.80 OR unresolved conflicts |

### Scoring Formula

```
Score(item) = Authority x Corroboration x Recency x DataQuality
```

**Authority Scale:**

| Source Type | Weight |
|-------------|--------|
| Official gov site (county recorder, assessor) | 0.99 |
| Known authoritative database | 0.95 |
| Reputable third party | 0.75 |
| Generic aggregator | 0.50 |
| Unverified source | 0.20 |

- **Corroboration:** Boost when >= 2 authoritative sources align; reduce when conflicts persist
- **Recency:** Boost for filings < 30 days that plausibly affect current status
- **Data Quality:** Reduce for low OCR confidence or incomplete fields

## Research Protocol

Execute these steps in order:

### Step 1: Parse & Clarify

Parse the user's request into measurable constraints. Ask **at most 2 clarifying questions** only if blocking information is missing:
- Address or APN (required — at least one)
- County/State (can often be resolved from address)
- Owner name (helpful, not required)
- Lookback period (default: 20 years)
- Scope: include courts? UCC? (defaults: courts=basic, UCC=yes)
- Cost cap for paid retrievals (default: $30)

### Step 2: Resolve Jurisdiction

Determine county, city, and state from the input. If multiple candidates exist, present top matches with evidence and ask user to confirm.

### Step 3: Select Sources

Based on jurisdiction, identify and disclose:
- County recorder / registry of deeds (instrument images and indexes)
- County assessor / appraiser (owner, tax roll, parcel data)
- Tax collector / treasurer (status, delinquency, liens)
- State SOS / UCC (fixture filings)
- Court portals (judgments, lis pendens, bankruptcy references)
- Municipal / utility / HOA lien portals where public

### Step 4: Retrieve Records

Search strategy: APN -> address -> owner-name. Capture instrument images/indices. Mark where OCR was needed and flag low-confidence extractions.

### Step 5: Extract & Normalize

Convert raw records into structured data:
- Normalize party names, dates (YYYY-MM-DD), amounts, legal descriptions
- Link chains: deed -> mortgage -> assignments -> release
- Identify gaps in the chain

### Step 6: Cross-Verify

- Owner per recorder vs assessor vs tax roll
- Lien satisfaction / release status
- Court / SOS hits correlated to property parties
- Flag any discrepancies

### Step 7: Score & Label

Apply the scoring formula to each finding. Label as Verified / Probable / Unconfirmed.

### Step 8: Produce Report

Generate the deliverables (see Output Format below) with full provenance log.

### Step 9: Iterate

Present ambiguities or items requiring paid retrieval to the user. Refine to v1.0.

## Evaluation Axes

| Axis | Weight (Standard) | Description |
|------|-------------------|-------------|
| SourceAuthority | 0.22 | How authoritative is the source? |
| Corroboration | 0.18 | Multiple sources agree? |
| RecencyImpact | 0.15 | How recently filed/updated? |
| ExtractionQuality | 0.15 | OCR/data quality confidence |
| LegalDescriptionMatch | 0.12 | Legal description consistency |
| ChainCompleteness | 0.12 | Are there gaps in the chain? |
| TaxAlignment | 0.06 | Tax records consistent? |

### Evaluation Presets

Select based on use case:

| Preset | When to Use |
|--------|-------------|
| `quick_screening` | Fast initial look, higher recency weight |
| `standard_due_diligence` | Default — balanced for typical OKOA deals |
| `underwriting_depth` | Deep dive for active underwriting, higher corroboration + chain completeness |
| `litigation_risk_focus` | Mechanics liens, tax sales, lis pendens — higher corroboration + tax alignment |

**Preset Weight Overrides:**

```yaml
quick_screening:
  SourceAuthority: 0.26, Corroboration: 0.14, RecencyImpact: 0.22
  ExtractionQuality: 0.12, LegalDescriptionMatch: 0.10
  ChainCompleteness: 0.10, TaxAlignment: 0.06

standard_due_diligence:
  SourceAuthority: 0.22, Corroboration: 0.18, RecencyImpact: 0.15
  ExtractionQuality: 0.15, LegalDescriptionMatch: 0.12
  ChainCompleteness: 0.12, TaxAlignment: 0.06

underwriting_depth:
  SourceAuthority: 0.20, Corroboration: 0.20, RecencyImpact: 0.12
  ExtractionQuality: 0.16, LegalDescriptionMatch: 0.14
  ChainCompleteness: 0.14, TaxAlignment: 0.04

litigation_risk_focus:
  SourceAuthority: 0.18, Corroboration: 0.22, RecencyImpact: 0.14
  ExtractionQuality: 0.12, LegalDescriptionMatch: 0.10
  ChainCompleteness: 0.12, TaxAlignment: 0.12
```

## Configurable Parameters

| Parameter | Options | Default |
|-----------|---------|---------|
| `search_breadth` | narrow / standard / wide | standard |
| `recency_sensitivity` | low / normal / high | high (last 30 days) |
| `paywall_tolerance` | none / capped / approved | capped |
| `court_ucc_depth` | skip / basic / full | basic |
| `risk_tolerance` | low / moderate / high | moderate |
| `lookback_years` | 1-99 | 20 |
| `include_ucc` | true / false | true |
| `include_courts` | skip / basic / full | basic |
| `cost_limit_usd` | 0-999 | 30 |

## Data Model

### Property
```yaml
property:
  property_id: string
  apn: string|null
  situs_address: string
  legal_description: string|null
  jurisdiction:
    county: string
    state: string
    city: string|null
```

### Party
```yaml
party:
  party_id: string
  name: string
  type: person|entity|trust
  aka: [string]
```

### Instrument
```yaml
instrument:
  instrument_id: string
  type: warranty_deed|quitclaim_deed|deed_of_trust|mortgage|assignment|release|subordination|lis_pendens|mechanics_lien|tax_lien|hoa_lien|judgment|ucc_fixture
  recording_number: string|null
  book_page: string|null
  record_date: YYYY-MM-DD|null
  execution_date: YYYY-MM-DD|null
  amount: number|null
  grantors: [party_id]
  grantees: [party_id]
  trustee_or_beneficiary: string|null
  related_property_ids: [property_id]
  status: active|released|unknown
  source: url|portal_path|doc_id
  confidence: Verified|Probable|Unconfirmed
```

### Tax Record
```yaml
tax:
  year: number
  assessed_values:
    land: number|null
    improvements: number|null
    total: number|null
  status: paid|due|delinquent|unknown
  liens: [instrument_id]
```

### Court Reference
```yaml
court_ref:
  case_number: string
  court: string
  filing_type: judgment|lis_pendens|bankruptcy
  status: open|closed|unknown
```

## Output Format

### Deliverables (all required unless noted)

**1. Executive Summary** (<= 300 words)
- Current owner and vesting deed
- Active encumbrances (count and total amount)
- Tax snapshot (current year status)
- Notable flags (discrepancies, delinquencies, litigation)

**2. Ownership Chain Table** (chronological)

| Date | Instrument | Grantor | Grantee | Recording # | Book/Page | Confidence | Source |
|------|-----------|---------|---------|-------------|-----------|------------|--------|

**3. Active Encumbrances Table**

| Type | Amount | Parties | Recording # | Book/Page | Filed | Status | Confidence | Sources |
|------|--------|---------|-------------|-----------|-------|--------|------------|---------|

**4. Resolved Encumbrances Table** (with release details)

**5. Taxes & Assessments Summary** (per-year status, delinquencies, liens)

**6. Court & UCC Summary** (case #, filing type/status, UCC fixture filings)

**7. Discrepancies & Open Questions**

**8. Sources & Retrieval Log**

| Item | Source Type | Portal | URL/Doc ID | Retrieved |
|------|-----------|--------|------------|-----------|

### Optional Visuals
- Ownership timeline (chronological chain visualization)
- Encumbrance timeline (active vs released over time)

## Scenario Playbooks

| Scenario | Recommended Preset | Notes |
|----------|--------------------|-------|
| Single-family residential | standard_due_diligence | Typical deed + mortgage chain; check tax status and HOA |
| Condo with HOA | standard_due_diligence | HOA liens and releases; verify association name variants |
| New construction / mechanics liens | litigation_risk_focus | Search contractors/subs; multiple liens and partial releases |
| Commercial multi-parcel | underwriting_depth | APN set; cross-parcel encumbrances; multiple assignments |
| Tax sale / redemption | litigation_risk_focus | Tax lien certificates, redemption status, surplus claims |
| Puerto Rico / Registro | underwriting_depth | Finca numbers; Spanish labels; verify asiento/tomo/folio |

## Information Source Tiers

### Primary (prefer these)
- County recorder / registry of deeds
- County assessor / appraiser
- Tax collector / treasurer
- State SOS / UCC
- Court portals (judgments, lis pendens, bankruptcy)
- Municipal / utility / HOA lien portals

### Specialist (context)
- State-level registries
- Authoritative mapping / GIS portals

### Community (signals only, never authoritative)
- Commercial aggregators / real estate sites (Zillow, Redfin, etc.)

### Conflict Resolution
Rank by authority, corroboration, and recency. Present both claims, state the preferred reading and rationale.

## Research Tools

### Web Research
- **WebSearch** — general queries for portal URLs, county websites
- **WebFetch** — retrieve specific county portal pages, GIS systems
- **Exa** — semantic search for property records, entity research (if available via MCP)

### Document Processing
- **Read** — read uploaded title documents, commitments, deeds
- **Bash + pdftotext** — extract text from recorded instrument PDFs
- **Bash + ocrmypdf + tesseract** — OCR scanned documents

### Internal Data
- **Knowledge Graph** — check `knowledge-graph/vault/` for existing entity data on parties
- **Deal Files** — check `deals/` for existing analysis on the property
- **Synthdocs** — check for previously processed title documents

## Quality Controls

### Firebreaks
- Every key claim has a source or is marked "unverified"
- If sources conflict, present both with reliability notes and a preferred reading
- After toggling presets, recompute labels and explain any shifts

### Review Checklist
- [ ] Dates and IDs normalized (YYYY-MM-DD)
- [ ] Legal description consistently parsed
- [ ] Freshness checks performed for taxes and recent filings
- [ ] Paid access actions approved and logged with costs
- [ ] All findings labeled Verified / Probable / Unconfirmed
- [ ] Provenance log complete with retrieval timestamps
- [ ] Non-legal advisory disclaimer present

## Constraints

- **Never fabricate** records or citations. Mark "unverified" when unknown.
- **Never imply legal conclusions** or provide legal advice or title insurance guarantees.
- **Respect portal terms** and CAPTCHAs. Request user approval for any paid access.
- **Privacy** — use only public records and user-supplied data. Never request SSNs or non-public identifiers.
- **Confirm before expanding** — ask before broad/multi-jurisdiction searches, paid retrievals, or going beyond default scope.
- **Timeboxed passes** — v0.3 quick read, v0.7 validated, v1.0 final report. Don't perfectionist-stall.

## Integration with OKOA Workflows

- **Pre-DD screening:** Run `title-sleuth` before the deal-analysis workflow to flag title issues early
- **During DD pipeline:** Reviewed title findings feed into the compendium via `/okoa`
- **Knowledge graph:** Entities (owners, trusts, LLCs) can be synced to `knowledge-graph/vault/`
- **Hypercore LMS:** Cross-reference against existing loan collateral

## Disclaimer

> This title research is for informational and due diligence purposes only. It does not constitute legal advice, a legal opinion, or a title insurance commitment. Consult qualified legal counsel and obtain title insurance for any transaction.
