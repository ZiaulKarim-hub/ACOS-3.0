# Deal Types — acos-dataroom-v2 v2.1.0

This file is the source-of-truth for the `--deal-type` argument of `/acos-dataroom-v2`.

**Two roles this file plays:**

1. **Audience definition.** The Phase 1 objective-researcher and objective-synthesizer
   read this file to ground their "buyer profile" and "out-of-scope" sections in
   the actual recipient of the dataroom.

2. **Categorical hard-exclude fast path.** The Phase 2 inclusion-deliberator consults
   this file at the top of its decision workflow. If a file matches a hard-exclude
   category for the active deal type, the verdict is EXCLUDE with
   `reason: categorical_exclusion` — no per-file deliberation needed. This dramatically
   speeds up large runs AND prevents the deliberator from "leaning include" on docs
   that should never be in this audience's hands.

**Six deal types are supported:**

| Slug | One-line audience |
|---|---|
| `takeout-lender` | Third-party lender evaluating taking over our debt position or providing rescue capital |
| `property-sale` | Asset buyer evaluating purchase of the underlying real property |
| `loan-sale` | Buyer of the debt position (note buyer) |
| `loan-participation` | Co-lender joining the existing loan |
| `foreclosure-auction` | Public auction bidders / trustee-sale package |
| `lender-internal` | Internal OKOA review (no categorical exclusions; kitchen sink) |

---

## How to read each deal-type block

Each block has four sections:

- **Audience.** Plain-English description of who is reading the dataroom and what
  they're trying to decide. The obj-researcher uses this as its "buyer profile."

- **Relevant scope.** High-level categories that this audience NEEDS. The
  taxonomy-designer uses this to prioritize folder design.

- **Hard exclusions.** Categorical bright-line cuts. The inclusion-deliberator's
  fast path checks every file against this list. **Match = EXCLUDE, no deliberation.**
  Each rule has (a) a one-line category name, (b) why this audience doesn't need it,
  (c) **filename hint patterns** the deliberator uses for fast string-match detection,
  and (d) **content-signal patterns** for vision-summary detection when filename
  isn't dispositive.

- **Objective-string augmentation.** A paragraph the obj-synthesizer pastes into
  `SOLIDIFIED_OBJECTIVE.md` §3 (Buyer profile) and §5 (Out-of-scope). This carries
  the deal-type framing through every downstream Phase 2 deliberation prompt.

---

## takeout-lender

### Audience
A third-party lender (community bank, private credit fund, debt fund, hard-money
lender) evaluating whether to take out OKOA's existing loan position, provide rescue
capital to the sponsor, or otherwise step into the senior-secured slot on this asset.
The recipient is **NOT** OKOA, **NOT** the borrower, **NOT** our outside counsel.
They will assess the asset on its merits, the construction status, the title chain,
the priority of recorded encumbrances (especially C-PACE), the brand/franchise
posture, and the foreclosure clock. They will **NOT** want or need to see how OKOA
structured its loan, the borrower's internal entity organization, the sponsor's
personal financials, or any of OKOA's settlement strategy or workout deliberations.

### Relevant scope (what MUST be in the dataroom)
- Property identity, location, broker-led market view, recent presentations to capital
- Title commitment + policy + recorded encumbrances + environmental Phase I
- Architectural drawings (the asset as-designed)
- Engineering and MEP drawings (the asset as-built systems)
- Construction status reports (from GC, owner-rep, senior-construction-lender)
- Construction draws + lien waivers (the capital actually invested vs budget)
- C-PACE financing documents (recorded priority liens that survive a takeout)
- Brand/franchise agreement + hotel management agreement (operational obligations)
- Appraisals + as-completed values + unit sales/pricing analysis + project pro-forma
- Current foreclosure posture (notice of default, substitution of trustee, sale notice)

### Hard exclusions

**1. Lender-internal loan documents.** Documents OKOA's outside counsel drafted as
part of originating, modifying, or extending our debt. The takeout lender will
draft their OWN loan documents, so ours have zero diligence value to them.

- Filename hints: `*Promissory Note*`, `*Deed of Trust*` (when it's our DOT, not a
  recorded prior DOT in the title chain), `*Loan Agreement*`, `*Construction Loan
  Agreement*`, `*Loan Modification*`, `*Payment Guaranty*`, `*Performance Guaranty*`,
  `*Environmental Indemnity*`, `*Collateral Assignment*` (when OKOA is assignee),
  `*Forbearance*`, `*Bridge Loan Modification*`, `*Loan Extension*`,
  `*Borrower Signed Docs*`, `*Closing Binder*`, `*Approval Letter*`
- Content signals: document drafted by OKOA's outside counsel (BTJD, Brad Pak, etc.);
  signature block names OKOA as a party; "BTJD redline" or "FINAL for Execution"
  pattern indicating internal draft progression
- **Carve-out (KEEP):** Documents that affect the recorded title chain regardless
  of who drafted them — recorded DOTs, recorded intercreditor agreements, recorded
  assignments — even if OKOA is a party. The takeout lender needs to know what's
  on title.

**2. Borrower and SPE organizational documents.** Internal entity formation and
governance documents. A takeout lender will independently verify entity authority
through fresh good-standing certificates and an opinion-of-counsel deliverable —
they don't review historical org docs.

- Filename hints: `*Operating Agreement*`, `*Certificate of Organization*`,
  `*Certificate of Good Standing*`, `*COGS*`, `*Subscription Agreement*`,
  `*Org Chart*`, `*Beneficial Ownership*`, `*BOI*`, `*EIN*`, `*IRS Letter*`,
  `*Certified - <LLC Name>*`, `*Initial Filing*`, `*A&R LLC Agreement*`,
  `*Amendment to * LLC Agreement*`
- Content signals: document signed by the borrower's members or managers
  internally; lists ownership percentages; recites capital contributions

**3. Sponsor and guarantor personal financials.** Personal Financial Statements,
guarantor tax returns, demand letters to guarantors. **PII risk** — never to be
in an outbound dataroom unless the audience is explicitly evaluating recourse
posture (loan-participation might want this; takeout-lender does not).

- Filename hints: `*PFS*`, `*Personal Financial Statement*`, `*Pwolfgramm PFS*`,
  `*Handy PFS*`, `*Koloa Wolfgramm*`, `*Demand Letter*` (when addressed to a
  guarantor as natural person), `* PFS *`
- Content signals: net-worth tables for a natural person; SSN-adjacent
  identifiers; named-individual tax-return data

**4. Cross-collateral on unrelated properties.** Deeds of trust, mortgages, or
recorded instruments tying THIS loan to OTHER assets owned by the sponsor or
sponsor affiliates. A takeout lender pays off our loan and the cross-collateral
releases — the documents on the other assets aren't theirs to review.

- Filename hints: `*Lone Star*`, `*Texas DOT*`, `*Louisiana Mortgage*`,
  `*Wilderness Trails*`, `*Galveston*`, `*Harris_Preserve*`, `*Harris_The Reserve*`,
  `*Beehive Hospitality*` DOT outside of UT, `*Bayou Hospitality*`, `*Armada Prime*`
- Content signals: deed of trust or mortgage citing a state or property address
  unrelated to the dataroom's primary asset; CCRs for an unrelated subdivision
  (e.g., Frostwood, Dakota Mountain Lodge when the asset is Ascent Park City)

**5. Settlement strategy and workout deliberations.** Settlement agreements, workout
proposals, takeover scenarios, internal negotiation drafts. The takeout lender
wants the foreclosure POSTURE (where in the clock we are), not the SETTLEMENT
STRATEGY (what we offered the sponsor to avoid foreclosure).

- Filename hints: `*Settlement Agreement*`, `*Workout*`, `*Takeover Scenario*`,
  `*War Room*` (often used for internal workout strategy), `*Negotiation*`,
  `*Pre-Negotiation Agreement*`
- Content signals: terms describing a release in exchange for forbearance or partial
  payment; identifies disputed claims; internal strategic memoranda

**6. Payoff and discharge documents.** Payoff statements, releases of lien, full
reconveyances, borrower payoff calculations. A takeout lender pays us off and a
new payoff is calculated at closing — historical payoff drafts have no value.

- Filename hints: `*Payoff Statement*`, `*Payoff*` (when it's a payoff dollar
  schedule, not a recorded conveyance), `*Release of Lien*`, `*Full Reconveyance*`,
  `*Borrower Statement*` (payoff context), `*Interest Catch-Up*`
- Content signals: per-diem interest accrual tables; payoff dollar amount at a
  forward date; release-and-discharge language

**7. Lender-internal financial models and trackers.** Loan models, cash-flow
projections OKOA built for internal IC, sources-and-uses internal worksheets,
internal portfolio schedules. The takeout lender will build their own.

- Filename hints: `*Loan Model*`, `*Loan Statement*` (lender's), `*Interest
  Catch-Up*`, `*Take-Out Loan S&U*`, `*RE Schedule*` (when it's OKOA's portfolio
  schedule), `*Funding Analysis*` (when it's OKOA's internal funding analysis,
  NOT the borrower's project pro-forma)
- **Carve-out (KEEP):** Project pro-formas authored by the BORROWER or by Nuveen
  (the C-PACE lender), or appraisal models. Anything that describes the asset's
  expected economics. Cut only the OKOA-internal loan-economics models.

**8. Internal intercreditor and participation drafts.** Working drafts of
intercreditor agreements, participation agreements with our affiliates, internal
participation interest calculations. Only the recorded versions of intercreditor
agreements (which affect the title chain) survive.

- Filename hints: `*Intercreditor Agreement*` with `(BTJD*` or `redline` or
  `*draft*` markers, `*Participation Agreement*` redlines/drafts,
  `*Nichols_Participation*`, `*Team Pond Participation*`
- Content signals: `.docx` extension on a finalized-on-paper document type;
  redline markup; party signatures missing or proposed
- **Carve-out (KEEP):** Recorded intercreditor agreements (e.g.,
  `Beehive 30 Inter-Creditor Agreement.pdf` when it shows up in the title chain).
  These are public and dispositive of lien priority.

**9. Property and casualty insurance policies.** Builder's risk, general liability,
property insurance binders. Operational, not asset-diligence. A takeout lender's
own insurance counsel will require fresh certificates at closing.

- Filename hints: `*Insurance Policy*` (when NOT title insurance), `*Insurance
  Binder*`, `*Insurance Certificate*`, `*Builder's Risk*`, `*GL Policy*`
- **Carve-out (KEEP):** **Title insurance policies** — these document the insured
  state of the title chain and ARE asset-diligence. Cut only operational/casualty.

### Objective-string augmentation

The Phase 1 synthesizer pastes the following into `SOLIDIFIED_OBJECTIVE.md` §3
(Buyer profile) and §5 (Out-of-scope) for this deal type:

> **§3 Buyer profile (takeout-lender):** The reader is a third-party lender or
> private credit principal evaluating whether to take out OKOA's existing senior
> debt position on this asset or to provide rescue/bridge capital to the sponsor
> in advance of OKOA's foreclosure. They underwrite the ASSET (construction
> status, title posture, priority of recorded encumbrances, brand/franchise
> obligations, appraised value, foreclosure clock) — NOT OKOA's loan structure or
> the borrower's internal organization. They will draft their own loan documents
> if they proceed, so ours have zero diligence value to them.
>
> **§5 Out-of-scope (takeout-lender — categorical):** Lender-internal loan
> documents OKOA's counsel drafted (promissory notes, deeds of trust, loan
> agreements, payment guaranties, environmental indemnities, collateral
> assignments, forbearance agreements, loan modifications, closing binders);
> borrower and SPE organizational documents (operating agreements, certificates
> of organization, subscription agreements, beneficial ownership, EIN letters,
> org charts); sponsor and guarantor personal financials (PFS, demand letters
> to guarantors); cross-collateral instruments on unrelated properties; settlement
> strategy and workout deliberations; payoff statements and releases of lien;
> lender-internal financial models and trackers; intercreditor and participation
> agreement drafts/redlines (only RECORDED versions survive); property and casualty
> insurance policies (title insurance survives).

---

## property-sale

### Audience
A buyer of the underlying real property — typically a hospitality acquirer, a
hotel operator, a real estate private equity fund, or a strategic. They are
buying the asset, not the debt. They want to evaluate the physical asset, its
operational obligations, its construction status, and its clear-title posture
post-closing. They will pay off OKOA's debt at closing as part of consideration.

### Relevant scope (what MUST be in the dataroom)
- Property identity, broker materials, marketing presentations
- Title commitment + policy + recorded encumbrances + environmental Phase I
- Architectural drawings + engineering/MEP drawings
- Construction status, schedule, change orders, RFI log
- Construction draws + lien waivers (to understand work paid for vs. owing)
- C-PACE financing + assessment posture (survives sale; buyer assumes)
- Brand/franchise + hotel management agreement (buyer must accept assignment or terminate)
- Appraisals + project pro-formas + unit sales/pricing
- Foreclosure posture (relevant if asset is being sold THROUGH foreclosure or as a
  pre-foreclosure deed-in-lieu)

### Hard exclusions
Same as `takeout-lender` plus:

**10. Existing debt-position economics.** Cap-stack worksheets, sources-and-uses
that focus on debt vs. equity composition. A property buyer is paying cash (or
their own financing); our debt economics are irrelevant.

- Filename hints: `*Sources and Uses*` (when it shows debt tranches), `*Capital
  Stack*`, `*Cap Stack*`, `*Funding Analysis*`

### Objective-string augmentation

> **§3 Buyer profile (property-sale):** The reader is an asset acquirer
> evaluating the purchase of the underlying real property. They pay cash or
> bring their own financing; OKOA's debt is paid off at closing. They underwrite
> the PHYSICAL ASSET and its OPERATIONAL OBLIGATIONS — construction status,
> title posture, brand/franchise terms, recorded encumbrances surviving the
> sale, appraised value. They do NOT underwrite our loan position or our
> internal financing structure.
>
> **§5 Out-of-scope (property-sale — categorical):** Same categorical exclusions
> as takeout-lender, plus cap-stack/sources-and-uses worksheets focused on debt
> structure.

---

## loan-sale

### Audience
A buyer of the debt position itself — a note buyer, debt fund, or distressed-debt
shop. They are buying OKOA's loan as a financial instrument. They WILL want to
see our loan documents (they're buying them). They will NOT want internal
strategic deliberations or sponsor personal financials.

### Relevant scope
- Property identity (collateral)
- Title commitment + policy + recorded encumbrances
- Construction status (collateral condition)
- Construction draws + lien waivers (work paid; balance to finish)
- C-PACE + intercreditor (priority of our lien)
- Brand/franchise + management (operational continuity affects collateral value)
- Appraisals + as-completed values
- **OKOA's loan documents — INCLUDED for this deal type only** (note, DOT, loan agreement,
  guaranties, environmental indemnity, modifications/forbearances)
- Foreclosure posture
- Recorded intercreditor (full)

### Hard exclusions
Reduced list (loan documents ARE in scope here):

- Borrower and SPE org docs **DROP** (loan buyer relies on covenants and reps in
  the loan docs, not on entity formation history; minor exception: operating
  agreement IS often included for loan sales because the loan docs reference it.
  Defer to deliberator for OA specifically — flag as borderline rather than
  categorical exclusion).
- Sponsor/guarantor PFS — **CATEGORICAL EXCLUDE** (still PII; loan buyer can
  request fresh PFS post-purchase if they want recourse evaluation)
- Cross-collateral on unrelated properties **DROP**
- Settlement strategy deliberations **CATEGORICAL EXCLUDE**
- Lender-internal financial models / loan models — **CATEGORICAL EXCLUDE** (loan
  buyer builds their own)
- P&C insurance policies **CATEGORICAL EXCLUDE** (loan buyer requires fresh certs)

### Objective-string augmentation

> **§3 Buyer profile (loan-sale):** The reader is a note buyer or distressed-debt
> fund evaluating the purchase of OKOA's senior secured debt position as a
> financial instrument. They WILL want to see our loan documents (they're buying
> them — covenants, defaults, remedies, security). They will NOT want our
> strategic deliberations about how to enforce, the sponsor's personal financial
> statements, or our internal loan economics models.
>
> **§5 Out-of-scope (loan-sale — categorical):** Sponsor/guarantor personal
> financial statements; cross-collateral instruments on unrelated properties;
> settlement strategy and workout deliberations; OKOA's internal loan-economics
> models; property and casualty insurance policies.

---

## loan-participation

### Audience
A co-lender joining the existing loan as a participant — typically another bank
or private credit fund taking a piece of OKOA's loan. They want everything a
loan-sale buyer wants PLUS the participation-agreement terms and a deeper view of
the borrower's recourse posture.

### Relevant scope
Same as `loan-sale` plus:
- Sponsor/guarantor personal financials (recourse evaluation — **IN scope here**)
- Participation agreements with other participants (to understand pari-passu
  terms with co-lenders)

### Hard exclusions
Reduced list:
- Cross-collateral on unrelated properties **CATEGORICAL EXCLUDE** (unless the
  participation is portfolio-wide, in which case all collateral is in scope —
  flag in objective; non-categorical)
- Settlement strategy and workout deliberations **CATEGORICAL EXCLUDE**
- Lender-internal financial models specific to OKOA's IC **CATEGORICAL EXCLUDE**
- P&C insurance policies **CATEGORICAL EXCLUDE**

### Objective-string augmentation

> **§3 Buyer profile (loan-participation):** The reader is a co-lender joining
> the existing loan as a participant. They will want everything a debt buyer
> wants plus the participation-agreement terms, the sponsor's personal financials
> (for recourse evaluation), and the borrower's organizational documents (for
> entity diligence on the obligor). They will NOT want internal settlement
> strategy deliberations or OKOA's IC-specific models.
>
> **§5 Out-of-scope (loan-participation — categorical):** Cross-collateral on
> unrelated properties; settlement strategy and workout deliberations; OKOA's
> internal IC-specific financial models; property and casualty insurance
> policies.

---

## foreclosure-auction

### Audience
Public auction bidders or trustee-sale participants. The package is what's
required to be made available to bidders per the foreclosure notice and per
practical convention for non-judicial trustee sales in the relevant state.
Auction bidders want: what they're bidding on, what survives the sale, what
they're paying off, and what the property looks like.

### Relevant scope
- Property identity, address, legal description
- Title commitment / policy + recorded encumbrances (what survives the sale)
- Architectural + engineering drawings (one-page asset summary level; not the
  full 200+ drawing set unless competition is high)
- Construction status one-pager
- Appraisal (most recent; one comp set)
- C-PACE + recorded intercreditors (what survives foreclosure)
- Foreclosure documents: notice of default, notice of sale, substitution of
  trustee, trustee's sale package
- Brand/franchise: whether the franchise survives a foreclosure transfer

### Hard exclusions
Tightest list (auction packages are public; conservative):
- ALL lender-internal documents **CATEGORICAL EXCLUDE**
- ALL borrower/SPE org documents **CATEGORICAL EXCLUDE**
- ALL sponsor/guarantor PFS **CATEGORICAL EXCLUDE**
- ALL settlement strategy **CATEGORICAL EXCLUDE**
- ALL internal models **CATEGORICAL EXCLUDE**
- ALL cross-collateral **CATEGORICAL EXCLUDE**
- Detailed construction sub-drawings (keep general-arrangement only)
- Detailed draw-by-draw lien waiver detail (keep current balance-to-finish summary only)

### Objective-string augmentation

> **§3 Buyer profile (foreclosure-auction):** The reader is a bidder at a
> public trustee's sale or judicial foreclosure auction. The package is governed
> by the foreclosure notice and the practical conventions of the relevant
> state's non-judicial or judicial sale. Auction bidders want: what they're
> bidding on, what survives the sale, what they're paying off, and what the
> property physically looks like — at a one-pager level of detail.
>
> **§5 Out-of-scope (foreclosure-auction — categorical):** All lender-internal,
> all borrower/SPE, all sponsor PFS, all settlement strategy, all internal
> models, all cross-collateral, detailed construction sub-drawings, detailed
> draw-by-draw lien-waiver granularity (summary only).

---

## lender-internal

### Audience
OKOA's own underwriting team, IC, asset management, or workout team. This is
NOT an outbound dataroom — it's an internal organized view of everything we
have on the loan.

### Relevant scope
Everything.

### Hard exclusions
**None.** This deal type has zero categorical exclusions. Every file in the
source folder is evaluated by Phase 2 on relevance to OKOA's internal use,
which is "anything that isn't trash or a duplicate." The inclusion-deliberator
falls back to its general relevance-and-quality lens here. Dedup pass still
applies (we don't need 5 redlines of the same construction loan agreement —
the most recent / FINAL / Executed version wins).

### Objective-string augmentation

> **§3 Buyer profile (lender-internal):** The reader is OKOA's own underwriting,
> IC, asset management, or workout team. This is an internal organized view of
> the loan — everything is in scope, the question is only "is this the canonical
> version" not "is this audience-appropriate."
>
> **§5 Out-of-scope (lender-internal — none categorical):** No categorical
> exclusions. The Phase 2 deliberator evaluates relevance and dedup only.

---

## Implementation contract — for the inclusion-deliberator's fast path

Pseudocode the deliberator runs BEFORE its full deliberation workflow:

```
read SOLIDIFIED_OBJECTIVE.md
extract deal_type
load deal_types.md entry for deal_type
for each hard_exclusion in entry.hard_exclusions:
    if filename matches any filename_hint pattern:
        if no carve-out applies:
            return EXCLUDE with reason: "categorical_exclusion: <hard_exclusion.name>"
    if vision/content summary matches any content_signal:
        if no carve-out applies:
            return EXCLUDE with reason: "categorical_exclusion: <hard_exclusion.name>"
# else: fall through to normal relevance deliberation
```

Filename matching is **case-insensitive substring match** on the original filename
(not the path). Content-signal matching is the deliberator's existing vision-summary
read — just augmented to look specifically for the listed signals.

**Carve-outs are explicit.** Each hard-exclusion category lists carve-outs in
plain prose. The deliberator must check filename + content against the carve-out
before invoking the categorical exclude. When in doubt about a carve-out, the
deliberator falls through to normal deliberation (the carve-out is the
"this might be the exception" escape hatch).

## Implementation contract — for the obj-synthesizer

The obj-synthesizer reads the user's `--deal-type` from `SOLIDIFIED_OBJECTIVE.md`
metadata and pastes the deal-type's "Objective-string augmentation" verbatim into
the §3 Buyer profile and §5 Out-of-scope sections of the SOLIDIFIED_OBJECTIVE.md.
This guarantees every downstream Phase 2 deliberator sees the categorical
exclusion language in their primary context, not just the deal-type slug.

---

*acos-dataroom-v2 v2.1.0 — deal-types reference. Source-of-truth for categorical
exclusion fast path and buyer-profile grounding.*
