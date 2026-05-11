SYNTHETIC LOAN FOLDER — TEST FIXTURE

This folder contains fake documents for regression-testing the acos-dataroom
skill. None of the data is real. Borrower names, property names, addresses,
and dollar amounts are invented.

Structure mirrors a typical loan file:
  01_loan_documents/      — note, loan agreement
  02_collateral/          — recorded documents
  03_servicing/           — rent roll, payment history
  04_property/            — property overview
  05_third_party/         — appraisal summary

Use this fixture for smoke testing the skill end-to-end without exposing
real loan data.
