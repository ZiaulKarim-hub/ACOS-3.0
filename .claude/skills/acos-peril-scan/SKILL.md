---
name: acos-peril-scan
user-invocable: false
description: "Insurance and physical-climate/catastrophe peril research for real-estate collateral. Geolocates a parcel, scores seismic/flood/wildfire/wind/freeze exposure from public federal and state sources, maps deal-type to required coverages, estimates a premium band and its DSCR impact, and flags non-renewal/insurability risk. Produces confidence-rated findings with full provenance and falsifiable Conditions Precedent. Triggers on: insurance review, non-renewal risk, premium spike, DSCR insurance impact, flood zone, seismic hazard, wildfire hazard, hurricane/wind zone, builder's risk, vacant dwelling coverage, mortgagee clause, FAIR plan, insurability, catastrophe peril, climate risk screening."
version: 1.0.0
updated: 2026-07-13
---

# Peril Scan Research Engine

Identify the physical-climate and catastrophe-peril profile of a loan's real property
collateral, translate that profile into the coverages a lender should require, estimate what
those coverages will cost, and test whether the underwritten DSCR survives a realistic premium
or non-renewal shock — all from public federal/state hazard sources plus the shared deal brief,
with full provenance and falsifiable findings.

## When to Use

Use this skill when you need to:
- Screen a property's exposure to seismic, flood, wildfire, wind/named-storm, hail/tornado, or
  freeze/burst-pipe peril
- Determine what insurance coverages a deal type (ground-up construction, gut renovation,
  vacant/transitional, stabilized rental, hospitality) actually requires
- Estimate a premium band and check whether it fits inside the underwritten NOI/DSCR
- Assess non-renewal risk, admitted-vs-surplus-lines placement, or FAIR-plan dependency in a
  hardening regional market
- Identify coverage gaps (missing lender's-interest/mortgagee clause, no builder's-risk during
  rehab, no loss-of-rents, no flood/earthquake rider where the peril data says it's needed)
- Produce Conditions Precedent that gate funding on a bound, correctly-endorsed policy

This is the operating engine that IC Seat #5 (Insurance & Climate) carries into its blind
opening-round review, the same way the Legal & Structural seat carries `title-sleuth`.

## Independence Rule (MANDATORY — read before doing anything else)

The seat's OBJECTIONS must be formed from the shared deal brief (`<session>/deal-brief/`)
**alone** — property address/APN, asset type, renovation/vacancy status, stated coverages,
NOI, and any insurance documents already in the brief. This skill does not supply opinions or
objections; it supplies **corroboration**. Use it to verify or falsify what the brief claims
("sponsor states flood zone X" → check NFHL; "sponsor states insured value $Y" → check whether
that's plausible against a peril-adjusted premium band) and to fill gaps the brief left open
(no seismic disclosure at all, for instance, is itself a finding). Never let a public-source
finding talk you out of an objection the brief evidence already supports, and never manufacture
an objection the deal brief gives no basis for — corroborate, don't invent.

## SOURCES (authority catalog)

Public, official-first. Every value pulled from these must carry the source name, the specific
tool/report/portal path, and an as-of / retrieval date. Third-party aggregators or catastrophe
model estimates a chair supplies are corroborative signals only — never treated as equal to the
primary source below.

| Peril | Primary Source | What it Yields | Access Notes |
|-------|---------------|-----------------|--------------|
| **Seismic** | USGS National Seismic Hazard Model (NSHM); USGS Design Ground Motions / U.S. Seismic Design Maps tool | PGA, Ss/S1, Site Class default, Seismic Design Category (SDC) for a lat/long or address | Free API/web tool (`earthquake.usgs.gov/ws/designmaps`); no login |
| **Flood** | FEMA National Flood Hazard Layer (NFHL); FEMA Map Service Center (MSC); NFIP | Flood zone (X/A/AE/AO/VE etc.), Base Flood Elevation where mapped, effective FIRM panel/date, NFIP mandatory-purchase trigger | Free (`msc.fema.gov`, NFHL viewer/API); some panels are Preliminary vs Effective — note which |
| **Wildfire** | USFS/USDA Wildfire Risk to Communities — Wildfire Hazard Potential (WHP); WUI (Wildland-Urban Interface) classification layers | WHP class (Very Low → Very High) for the parcel/area, WUI status (interoperability of structures and wildland vegetation) | Free (`wildfirerisk.org`, USFS RDS-2020-0016 data); state agencies (e.g., CAL FIRE FHSZ) supplement where finer-grained |
| **Wind / named storm** | NOAA (National Hurricane Center historical tracks, wind-speed design maps referenced in ASCE 7); NOAA Storm Prediction Center (SPC) hail/tornado climatology | Design wind speed zone / named-storm exposure tier, historical hurricane landfall frequency for the region, hail/tornado climatological frequency | Free (`nhc.noaa.gov`, `spc.noaa.gov`); ASCE 7 wind maps corroborate design-basis wind speed |
| **Cold-climate / freeze** | NOAA NWS climate normals (heating degree days, extreme-minimum temperature); no single federal "freeze hazard" portal — infer from NWS climate data + deal-brief facts (vacancy status, heating-system condition) | Freeze/burst-pipe exposure signal; whether continuous heat is a real requirement during vacancy or a mechanical (boiler/HVAC) swap | Free; combine with brief-supplied facts (vacant/transitional status, scope of rehab) |
| **Market / non-renewal** | State Department of Insurance (DOI) market-conduct/withdrawal bulletins, admitted-carrier filings, FAIR-plan (residual market) enrollment and rate filings | Insurer market-withdrawal announcements, admitted vs. surplus-lines placement norms for the region, FAIR-plan dependency as a red flag, filed rate-increase trends | Free, state-by-state (each state DOI has its own portal — verify by name, e.g. California DOI, Florida OIR, Louisiana DOI) |
| **Fire-protection class** | ISO Public Protection Classification (PPC) — usually surfaced via the local fire department, county GIS, or the carrier/broker quote rather than a free ISO public lookup | PPC 1–10 class for the parcel's fire district — drives base property premium and insurability | ISO's own lookup is not freely public; corroborate via county/fire-district website or ask the broker/sponsor for the quote sheet's stated class; mark "unverified — no free public ISO lookup" if unobtainable |

### Source tiers
- **Primary (prefer, cite by name):** USGS NSHM/Design Ground Motions, FEMA NFHL/MSC/NFIP, USFS/USDA WHP, NOAA NHC/SPC/NWS, State DOI portals.
- **Corroborative only, never authoritative alone:** commercial catastrophe-model summaries, real-estate listing sites' "flood factor"/"fire factor" scores, sponsor-supplied broker quotes (useful for pricing signal, not for hazard classification).
- **Brief-supplied:** existing insurance certificates, binders, non-renewal notices, or broker quotes already in the deal brief — treat as primary evidence for the DSCR-impact estimate once you corroborate the underlying hazard classification independently.

## PROTOCOL

Execute in order. Timebox each pass — see Timeboxing under Constraints.

### Phase 1 — Geolocate the Parcel

1. Pull the situs address / APN / lat-long from the deal brief. If only a city/submarket is
   given, note the reduced precision as a limitation on every downstream score.
2. Resolve to a lat/long via `WebSearch`/`WebFetch` against a public geocoder or the county
   GIS/assessor if the brief doesn't already supply coordinates. Log the resolution method and
   the coordinates used — every peril tool below is coordinate- or address-sensitive, and a
   sloppy geocode invalidates every downstream score.
3. If the parcel straddles a flood-zone or hazard-class boundary, note both possible readings
   rather than silently picking one.

### Phase 2 — Score Each Peril for the Parcel

For each peril, run the lookup, extract the parameter, and assign a Confidence label (see
CONFIDENCE-SCORING below). Do not skip a peril because it seems obviously immaterial for the
region — a one-line "Wildfire: Very Low, WUI: No — coastal urban infill" is still a required
line, not an omission.

- **Seismic:** query USGS Design Ground Motions for the coordinates (risk category per asset
  use, Site Class — default to Site Class D if no geotechnical data exists in the brief, and
  say so); record PGA, Ss, S1, and resulting SDC.
- **Flood:** query FEMA NFHL/MSC for the parcel; record flood zone, whether it's Special Flood
  Hazard Area (SFHA) triggering NFIP mandatory purchase, effective vs. preliminary panel status,
  and BFE if mapped.
- **Wildfire:** query USFS Wildfire Risk to Communities for WHP class at the parcel/area level
  and WUI status; supplement with state agency layer (e.g., CAL FIRE Fire Hazard Severity Zone)
  when the state is known to publish one.
- **Wind/storm:** determine the region's named-storm exposure tier (Gulf/Atlantic coast vs.
  interior) via NOAA NHC historical landfall data; pull SPC hail/tornado climatology for
  interior/Plains/Midwest exposures; note the ASCE 7 design wind speed if the brief or a public
  building-code reference states it.
- **Cold-climate/freeze:** pull NWS climate normals (extreme minimum temp, heating degree days)
  for the region; cross-reference against brief facts — is the property vacant or under
  renovation with the heating system offline or being swapped? That combination is the actual
  risk driver, not the climate data alone.
- **Market/non-renewal:** search the state DOI portal for market-withdrawal bulletins, FAIR-plan
  enrollment data, and admitted-carrier availability for the property's line of business
  (habitational, hospitality, builder's risk) in that state/region.
- **Fire-protection class:** attempt to find the PPC via county/fire-district public sources; if
  unobtainable, mark "unverified — no free public ISO lookup" and note it as an open item for
  the broker/sponsor to supply.

### Phase 3 — Map Deal Type to Required Coverages

Using the brief's stated asset type / deal stage, determine the coverage set that SHOULD be in
place, then compare against what the brief says IS in place:

| Deal Type / Stage | Required Coverages |
|---|---|
| Ground-up construction | Builder's-risk (completed-value, all-risk), general liability (incl. completed-operations), lender's-interest/mortgagee clause naming the lender as mortgagee/loss-payee, flood (NFIP or private) if SFHA, earthquake if SDC warrants, wind/named-storm if regionally exposed |
| Gut renovation / major PIP | Vacant-dwelling or renovation-specific property policy (standard occupied-dwelling forms typically EXCLUDE vacancy >30-60 days), builder's-risk for the scope under construction, GL, lender's-interest clause, interim continuous-heat plan if a boiler/HVAC swap during a cold-climate season |
| Vacant / transitional | Vacant-property policy (not a standard occupied form), GL, lender's-interest clause, freeze-plan/watch-service if heat is off, loss-of-rents typically N/A until stabilized |
| Stabilized rental / multifamily | Property (all-risk or named-perils matching regional exposure), GL, flood (NFIP/private) if SFHA, earthquake if SDC warrants, wind/named-storm if regionally exposed, loss-of-rents/business-interruption, lender's-interest/mortgagee clause |
| Hospitality (hotel/motel) | Property (all-risk), GL (incl. liquor liability if applicable), business-interruption (often more critical than habitational — total revenue loss, not just rent), flood/earthquake/wind riders per peril scores, lender's-interest clause |

Flag every required-but-missing or ambiguously-worded coverage as a GAP (Phase 5).

### Phase 4 — Estimate Premium Band and DSCR Impact

1. Establish a premium band using whatever pricing signal is available and legitimate: a
   broker quote or expiring-premium figure already in the brief, a stated non-renewal
   replacement quote, or — absent any brief figure — a labeled ROUGH ORDER OF MAGNITUDE band
   reasoned from the peril scores (e.g., "SFHA + Tier-1 wind zone typically prices materially
   above a non-coastal, non-flood comparable; treat any premium figure below X% of insured
   value as suspect pending a quote"). Never present a fabricated dollar figure as if it were a
   quote — label estimates as ESTIMATE, not VERIFIED.
2. Compute premium as a percentage of underwritten NOI, and recompute DSCR at (a) the
   underwritten/expiring premium and (b) the estimated replacement/renewal premium (or the
   worst peril-consistent band if no quote exists).
3. State the DSCR delta in absolute terms ("DSCR moves from 1.28x to 1.11x if the premium
   triples on non-renewal") — this is the single number the chair most needs.

### Phase 5 — Assess Insurability / Non-Renewal Risk and Flag Coverage Gaps

- Weigh the state DOI market signal (withdrawals, FAIR-plan dependency, filed rate trend)
  against the peril scores to judge whether non-renewal at the next term is a live risk or a
  remote one.
- List every coverage GAP found in Phase 3 explicitly — a missing lender's-interest/mortgagee
  clause is treated as material regardless of how low the peril scores are, since it is a
  structural lender-protection defect, not a peril question.
- Note any FAIR-plan or surplus-lines placement as a standalone flag (higher cost, thinner
  coverage, and often a leading indicator of admitted-market withdrawal already underway).

### Phase 6 — Emit Falsifiable Conditions Precedent

For every material-risk or deal-breaker-candidate finding, propose 1-3 concrete, checkable CPs,
for example:
- "A bound policy naming [Lender] as mortgagee/loss-payee, evidencing [coverage], delivered
  before funding."
- "An interim continuous-heat plan (temporary boiler, freeze-watch service, or executed HVAC
  swap timeline) in place before any winter-season vacancy period begins."
- "A written flood-zone determination (Standard Flood Hazard Determination or equivalent) and,
  if SFHA, evidence of bound NFIP or private flood coverage before funding."
- "A seismic/geotechnical determination confirming Site Class and SDC before funding, if none
  exists in the brief and the parcel sits in a region of elevated USGS-mapped PGA."
- "Evidence of admitted-market (non-FAIR-plan) placement, or a documented non-renewal
  contingency plan, before the next policy term."

Each CP must be falsifiable — a reviewer must be able to check, at a later date, whether it was
satisfied or not. Do not propose vague CPs like "adequate insurance in place."

## CONFIDENCE-SCORING

Label every peril score and every coverage/premium finding:

| Label | Criteria |
|-------|----------|
| **Verified** | Direct read from the named primary source (USGS/FEMA/USFS/NOAA/State DOI) with a specific tool output, panel/report ID, and retrieval date; OR corroborated by >= 2 primary sources that agree |
| **Probable** | Read from a primary source but with reduced geocode precision, a Preliminary (not yet Effective) FEMA panel, an inferred Site Class/default assumption, or a single-source read with no corroboration |
| **Unconfirmed** | No public source obtainable (e.g., ISO PPC with no free lookup), conflicting sources, or a pricing figure that is a labeled ESTIMATE rather than a quote |

### Scoring formula (mirrors title-sleuth's structure, adapted to hazard data)

```
Score(item) = Authority x Corroboration x Recency x DataQuality
```

| Source Type | Weight |
|-------------|--------|
| Official federal hazard source (USGS/FEMA/USFS/NOAA) direct tool output | 0.99 |
| State DOI official bulletin/filing | 0.95 |
| Broker quote / carrier document already in the deal brief | 0.85 |
| Reputable third-party hazard aggregator (corroborative only) | 0.60 |
| Reasoned estimate / rough order of magnitude (no direct source) | 0.30 |

- **Corroboration:** boost when >= 2 primary sources agree (e.g., FEMA NFHL zone matches a
  brief-supplied flood certificate); reduce and flag when they conflict.
- **Recency:** boost for current/Effective panels and recent DOI bulletins; reduce for stale or
  Preliminary data — always state the as-of date.
- **Data Quality:** reduce for reduced geocode precision, assumed defaults (e.g., default Site
  Class), or incomplete address resolution.

## OUTPUT

### Where it goes
Write the full peril report as a side artifact (does NOT go in the seat's JSON objection
file): **`<session>/sidebars/seat-05-peril-report.md`**. Write it via `Write` (or `Bash`
heredoc if `Write` is unavailable) so the full research is preserved for the chair without
polluting the machine-read JSON. Feed only the material findings — with their evidence and
Confidence label — into the seat's actual objections/CPs.

### Side-report schema

**1. Executive Summary** (<= 300 words) — parcel location and geocode method, headline peril
exposures, single most important DSCR-impact number, and the top 1-3 CPs.

**2. Parcel & Geolocation** — address/APN as given, resolved lat/long, resolution method,
precision caveats.

**3. Peril Exposure Table**

| Peril | Parameter(s) | Value | Confidence | Source | As-of Date |
|-------|-------------|-------|------------|--------|-----------|

(One row minimum per peril: Seismic, Flood, Wildfire, Wind/Storm, Cold-climate/Freeze,
Fire-protection class.)

**4. Required vs. Actual Coverage Table**

| Coverage | Required? (deal-type driven) | In Place per Brief? | Gap? | Notes |
|----------|-------------------------------|----------------------|------|-------|

**5. Premium Band & DSCR Impact**
- Premium band (labeled VERIFIED quote / ESTIMATE) and its basis
- Premium as % of underwritten NOI
- DSCR at underwritten premium vs. at renewal/replacement/worst-case premium
- Explicit DSCR delta statement

**6. Insurability & Non-Renewal Risk Assessment** — state DOI market signal, FAIR-plan/
surplus-lines flags, and a plain-language read on non-renewal likelihood at next term.

**7. Coverage Gaps** — bulleted list, each tagged material-risk / deal-breaker-candidate /
informational.

**8. Falsifiable Conditions Precedent** — numbered list per Phase 6, each independently
checkable.

**9. Open Questions / Unverified Items** — anything marked Unconfirmed, with what would resolve
it (e.g., "broker quote sheet would confirm ISO PPC").

**10. Sources & Retrieval Log**

| Item | Source | Tool/Portal | Query/Params | Retrieved |
|------|--------|-------------|--------------|-----------|

## CONSTRAINTS

- **Never fabricate** a hazard reading, a citation, a premium figure, or any number. Mark
  "unverified" when a value cannot be obtained from a real source, and never present a
  reasoned ESTIMATE as if it were a VERIFIED quote.
- **Provenance is mandatory** — every value in the Peril Exposure Table, Premium Band, and Gaps
  sections carries a source name/tool and an as-of/retrieval date.
- **Respect portal terms and CAPTCHAs.** Do not attempt to circumvent access controls. Request
  chair approval before any paid retrieval (default cost cap $30) or any broad multi-jurisdiction
  search beyond the single parcel/region at hand.
- **Public data + brief-supplied data only.** Never request SSNs, non-public identifiers, or
  attempt to access anything beyond public government hazard/insurance-market sources and what
  the deal brief already supplies.
- **Diligence support ONLY.** This skill and its output are explicitly NOT insurance advice,
  NOT legal advice, and NOT investment advice. It does not bind, place, or recommend a specific
  carrier or policy — it identifies exposure, required coverage categories, and gaps for the
  committee's own judgment.
- **Independence discipline.** Corroborate the brief's claims and fill brief-identified gaps;
  never invent an objection the brief gives no basis for, and never let a public-source read
  override brief evidence without stating the conflict explicitly.
- **Timeboxed passes, no perfectionist stall.** Quick read (peril scores + obvious gaps) ->
  validated (premium band + DSCR impact + CPs) -> final (full side-report with provenance log).
  Move to the next phase once a pass is "good enough to be falsifiable," don't loop chasing an
  unobtainable data point (e.g., ISO PPC with no free lookup — mark unverified and move on).

## Disclaimer

> This peril and insurance screening is for informational and due-diligence purposes only. It
> does not constitute insurance advice, a coverage recommendation, a legal opinion, or
> investment advice. Consult a licensed insurance broker/underwriter and qualified counsel
> before making coverage, binding, or lending decisions.
