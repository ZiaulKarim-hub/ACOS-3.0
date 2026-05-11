# Risk Dashboards — Per Deal Type

Each deal type has a tailored risk dashboard. The dashboard is the **first tab
the boss should look at** in the Excel guide. It's deal-specific because what
constitutes a "risk" depends on what's being sold or pitched.

For each dashboard below: each risk dimension produces zero, one, or many rows
in the `Risk_Dashboard` Excel tab. A dimension with no relevant evidence still
produces a row with severity = "low" and evidence = "No issues detected" — so
the boss can confirm the skill checked.

---

## `loan_sale` — Risk Dimensions

1. **Enforceability Chain** — Is there an unbroken chain of note → allonges → assignments? Severity escalates if any link is missing or unrecorded.
2. **Collateral Perfection** — UCC filings current and unlapsed? Deed of trust recorded? Mortgage assignments recorded?
3. **Payment History Integrity** — Servicing records complete? Late payments / defaults disclosed?
4. **Default / Forbearance Status** — Any active default, modification, or forbearance? Disclosed in offering materials?
5. **Payoff / UPB Calculation** — Current UPB calculation present? Reconciles to servicing records?
6. **Insurance Status** — Force-placed insurance? Lapses? Lender named as loss payee?
7. **Tax Status** — Property taxes current? Any tax sale risk?
8. **Title Status** — Title policy in place? Any clouds since origination?
9. **Litigation** — Any active litigation involving borrower, guarantor, or property?

---

## `loan_participation` — Risk Dimensions

All `loan_sale` dimensions, plus:

10. **Participation Agreement Clarity** — Voting/consent mechanics unambiguous? Pro-rata waterfalls clearly defined?
11. **Lead Lender Disclosures** — Does the participation agreement disclose all material lead-lender actions to date?
12. **Fee Splits** — Servicing fees, default fees, modification fees clearly allocated?
13. **Participant Rights** — Information rights, kick-out rights, buyout rights documented?

---

## `property_sale` — Risk Dimensions

1. **Title** — Commitment + final policy clean? Schedule B exceptions reviewed?
2. **Environmental** — Phase I current (within 6 months)? Any RECs / Phase II findings?
3. **Tenants** — Rent roll vs. leases reconcile? Estoppels obtained where required? SNDAs in place?
4. **Property Condition** — PCR identifies any material deferred maintenance or capital needs?
5. **Zoning / Entitlements** — Zoning matches as-built? Entitlements transferable?
6. **Liens** — All liens identified? Plan for clearance at closing?
7. **Code Violations / Permits** — Any open violations? All permits in place / closed out?
8. **Survey** — ALTA survey current? Encroachments / easements identified?
9. **Insurance** — Insurance binder available for buyer's review?
10. **Tax Bills** — Property taxes current? Any reassessment risk on transfer?
11. **Operating Statements** — 2 years of operating statements? Reconcile to bank?
12. **CapEx Budget** — Forward CapEx plan? Any capital reserves?

---

## `foreclosure_auction` — Risk Dimensions

1. **Notice Compliance** — Were all notices (Notice of Default, Notice of Sale) given per statute? Publication, posting, mailing all completed? Affidavits available?
2. **Redemption Rights** — Statutory redemption period analysis? Any equitable redemption claims?
3. **Junior Lienholders** — All junior liens identified? Notice given to all junior lienholders? Standing of any to object?
4. **Bidder Qualification** — Auction terms clear on bidder qualification (cash, cashier's check, escrow)?
5. **As-Is Disclosure** — Auction terms disclose property "as-is" with no warranties?
6. **Auction Procedures** — Procedures (date, time, location, online vs. in-person) clearly documented?
7. **Post-Sale Transfer** — Trustee's deed / sheriff's deed mechanics clear?
8. **Occupancy / Eviction** — Property occupied? By whom (borrower, tenant, squatter)? Eviction posture?
9. **Title at Sale** — Title condition at sale clear to buyer? Any wraparound liens senior to OKOA?
10. **Payoff Demand History** — Borrower / guarantor demand history? Any forbearance promises that could be cited?

---

## `lender_package` — Risk Dimensions

1. **Loan Performance** — Current and historical payment performance? Any covenant defaults?
2. **Borrower Financial Strength** — Current financials vs. underwriting financials? Material adverse change?
3. **Collateral Coverage** — Current LTV / DSCR / debt yield vs. underwriting? Updated valuation?
4. **Refinance Thesis** — Why is takeout justified? What's the source of repayment?
5. **Takeout Source** — Is there an identified takeout lender / sale? Soft circle? Hard commitment?
6. **Bridge-to-Permanent Path** — Clear narrative on how borrower gets to permanent financing?
7. **Sponsor Track Record** — Sponsor's prior deals? Any known issues?
8. **Market Support** — Comp rents / sales support the value? Market trajectory?
9. **Cap Stack** — Current cap stack clearly documented? Any other lenders / equity?
10. **Proposed Terms** — Terms reasonable for takeout lender? Pricing within market?

---

## How the Skill Builds the Dashboard

For each dimension above, the skill:

1. Searches the classified extraction set for evidence of the dimension's status.
2. Where evidence supports a clean status, severity = low + evidence_summary = "Confirmed [statement]".
3. Where evidence raises concern, severity = appropriate level + evidence_summary describes the concern + linked_file_ids cite the documents.
4. Where evidence is *absent*, severity = medium minimum (often high) + evidence_summary = "Not found in source folder — request from servicer/borrower/counsel" + recommended_action.

A `lender_package` row that the skill couldn't evidence at all (e.g., "no
takeout source identified") is **never silently low-severity**. The default
when nothing is found is medium, escalated to high if the absence is critical
to the deal type.
