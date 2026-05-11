# Deal Types — Reference

The acos-dataroom skill recognizes 5 deal types in v1. Each represents an
**outbound** transaction OKOA may need to support with a data room (the inverse
of origination diligence, where OKOA is the *recipient* of documents).

## When to Use Each

### `loan_sale`

**Definition:** OKOA is selling a whole loan (or a pool of loans) to another
investor.

**Counterparty:** Loan buyer (debt fund, bank, family office).

**Critical artifacts:**
- Full enforceability chain (note, allonges, assignments, recordation)
- Collateral perfection (UCC filings, deed of trust, recorded mortgage)
- Payment history at full granularity (servicing report, ledger)
- Default / forbearance / modification history
- Payoff calculations / current UPB

**Inference signals (filenames, content):**
- `*purchase*sale*agreement*`, `*loan*sale*`, `*PSA*`, `*assignment*and*assumption*`
- "Loan Sale Agreement", "Bid Letter", "Indicative Bid"

---

### `loan_participation`

**Definition:** OKOA is selling a participation interest (typically pro-rata)
in an existing loan, retaining the lead lender role.

**Counterparty:** Participating lender or investor.

**Critical artifacts:**
- Everything in `loan_sale`, **plus**
- Participation agreement (with voting/consent mechanics)
- Pro-rata waterfalls and fee splits
- Lead lender disclosures
- Participant rights and remedies

**Inference signals:**
- `*participation*agreement*`, `*PA*`, `*intercreditor*`
- "Participation Interest", "Pro Rata Share"

---

### `property_sale`

**Definition:** OKOA is selling underlying real estate, typically post-
foreclosure (lender becomes seller after taking title).

**Counterparty:** Property buyer (operator, developer, opportunistic investor).

**Critical artifacts:**
- Title commitment + final policy
- Environmental Phase I (and Phase II/III if relevant)
- ALTA survey
- Zoning verification + entitlements
- Leases, rent roll, operating statements (income property)
- CapEx history + budget
- Property condition assessment
- Tenant estoppels + SNDAs (if leased)
- Broker materials, comparables
- Code compliance, permits, insurance, tax bills

**Inference signals:**
- `*REO*`, `*property*sale*`, `*OM*`, `*offering*memo*`
- "Real Estate Owned", "REO Sale", "Bid Date"

---

### `foreclosure_auction`

**Definition:** OKOA is preparing for a foreclosure / trustee sale auction —
the data room supports OKOA's own conduct of the sale and supports bidders.

**Counterparty:** Foreclosure bidders, trustee, court (where judicial).

**Critical artifacts:**
- Sale notice procedural compliance (publication, posting, mailing)
- Redemption rights analysis
- Junior lienholder notices and standing
- Bidder qualification materials
- "As-is" disclosures
- Auction terms and procedures
- Post-sale transfer mechanics
- Occupancy / eviction status
- Title condition at sale
- Payoff demand history

**Inference signals:**
- `*notice*sale*`, `*trustee*sale*`, `*foreclosure*`, `*NOD*`, `*notice*default*`
- "Notice of Sale", "Notice of Default", "Trustee's Sale"

---

### `lender_package`

**Definition:** OKOA is pitching an existing loan to a takeout / refinance
lender — i.e., showing a new lender why they should take out OKOA's existing
position. **Confirmed by user.**

**Counterparty:** Prospective takeout lender.

**Critical artifacts:**
- Loan performance history
- Current borrower financial state
- Current collateral coverage
- Refinance thesis (why now, why this borrower, why this property)
- Takeout source identification
- Bridge-to-permanent narrative
- Sponsor track record
- Market support
- Current cap stack
- Proposed terms

**Inference signals:**
- `*takeout*`, `*refi*pitch*`, `*lender*package*`, `*pitch*deck*`
- "Refinance Package", "Takeout Memo"

---

## Inference Logic (Phase 1)

When `--deal-type` is not provided, the skill:

1. Inventories filenames in the source folder.
2. Pulls first page from up to 5 likely-key files.
3. Scores each deal type by signal match.
4. Surfaces the highest-scoring type with a confidence and the matching signals.
5. **Always pauses for user confirmation** — never proceeds on inference alone.

If no deal type scores above a confidence threshold (0.55), the skill defaults
to recommending `lender_package` (broadest scaffold) and tells the user to
override if needed.

---

## Edge Cases

- **Mixed deals** (e.g., a loan sale that includes a property pledge requiring property-sale-style materials): use the dominant deal type and rely on Phase 7a tailoring to *add* property-side items.
- **Pre-default / performing loan being sold:** still `loan_sale`; the absence of default history is a legitimate finding, not a gap.
- **Two-step process** (foreclosure now → property sale later): run as `foreclosure_auction` first; rerun later as `property_sale` against the updated folder.
