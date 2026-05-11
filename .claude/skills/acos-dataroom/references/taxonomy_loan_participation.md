# Taxonomy — Loan Participation Data Room

Folder structure for the final loan-participation data room. Inherits from
`taxonomy_loan_sale.md` and adds participation-specific sections.

Categories are numbered `NN` and align with
`references/checklist_loan_participation.md`.

## Top-Level Folders

```
[DataRoomName]/
├── 01_Loan_Documents/
├── 02_Collateral_Perfection/
├── 03_Title_and_Survey/
├── 04_Borrower_and_Sponsor/
├── 05_Guarantor/
├── 06_Property_and_Asset/
├── 07_Third_Party_Reports/
├── 08_Insurance/
├── 09_Servicing_and_Payment_History/
├── 10_Default_Workout_Modifications/
├── 11_Financial_Statements/
├── 12_Tax_and_Regulatory/
├── 13_Participation_Agreement_and_Governance/  # <-- participation-specific
├── 14_Lead_Lender_Conduct_and_Disclosures/    # <-- participation-specific
├── 15_Pro_Rata_Mechanics_and_Waterfalls/      # <-- participation-specific
├── 16_Participant_Rights_and_Remedies/        # <-- participation-specific
├── 17_Existing_Participations/                # <-- participation-specific
├── 18_Litigation_and_Disclosures/
├── 19_Participation_Sale_Transaction/
├── 99_Index_and_QA/
```

## Participation-Specific Subcategories

### 13_Participation_Agreement_and_Governance
- `13.01_Participation_Agreement_Original/`
- `13.02_Participation_Amendments/`
- `13.03_Voting_and_Consent_Matrix/`
- `13.04_Decision_Authority_Schedule/`

### 14_Lead_Lender_Conduct_and_Disclosures
- `14.01_Lead_Action_Log/` — material decisions made by lead since origination
- `14.02_Modifications_Approved/`
- `14.03_Forbearance_Approved/`
- `14.04_Workout_Approvals/`
- `14.05_Standard_of_Care_Disclosures/`

### 15_Pro_Rata_Mechanics_and_Waterfalls
- `15.01_Waterfall_Worksheet/` — current as-of pro-rata calculation
- `15.02_Principal_and_Interest_Allocation/`
- `15.03_Default_Proceeds_Allocation/`
- `15.04_Fee_Splits/` — origination, servicing, modification, default, exit
- `15.05_Expense_Allocation/` — protective advances, legal, third-party reports

### 16_Participant_Rights_and_Remedies
- `16.01_Information_Rights/`
- `16.02_Buyout_Put_Rights/`
- `16.03_Successor_Lead_Mechanics/`
- `16.04_Default_Cure_Rights/`

### 17_Existing_Participations
- `17.01_Existing_Participants_List/`
- `17.02_Prior_Participation_Agreements/`
- `17.03_Cross_Participation_Conflicts/`

### 19_Participation_Sale_Transaction
- `19.01_Participation_Purchase_Agreement/`
- `19.02_Bid_Letter/`
- `19.03_Disclosure_Schedules/`
- `19.04_Assignment_of_Participation_Interest/`
- `19.05_Closing_Documents/`

## Inherited Subcategories

01–12 and 18 follow the same subcategory layout as `taxonomy_loan_sale.md`.
99_Index_and_QA same as loan sale.
