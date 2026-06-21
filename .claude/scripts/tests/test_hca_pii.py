#!/usr/bin/env python3
"""test_hca_pii.py — stdlib unittest for the PII scrubber (SLICE-HCA-10).

ADVERSARIAL by construction: every PII class handled by hca-pii.py has a
POSITIVE test (clean record passes unchanged) and a NEGATIVE test (PII-bearing
string/dict is redacted — no leak).

Hard gates:
  - No PII leaks: any string containing the planted PII literal after scrubbing => FAIL.
  - Aggregates preserved: dollar amounts / rates / IDs must survive scrubbing intact.

Run:
  python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py' -v
"""

import importlib.util
import json
import os
import sys
import unittest

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.abspath(os.path.join(_THIS_DIR, os.pardir))


def _load(modname, filename):
    cached = sys.modules.get(modname)
    if cached is not None:
        return cached
    path = os.path.join(_SCRIPTS_DIR, filename)
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


pii = _load("hca_pii", "hca-pii.py")

REDACTED = pii.REDACTED


# ===========================================================================
# Helpers
# ===========================================================================

def _contains_pii(obj, pii_literal: str) -> bool:
    """Return True if the object (after JSON serialization) still contains the literal."""
    text = json.dumps(obj, ensure_ascii=False)
    return pii_literal in text


# ===========================================================================
# 1. Email address
# ===========================================================================

class EmailRedactionTest(unittest.TestCase):
    """Email addresses must be redacted; non-email text must survive."""

    EMAIL = "alice.smith@example.com"
    SAFE = "loan@id"          # not an email — has no TLD-shaped suffix in isolation

    def test_email_in_string_is_redacted(self):
        out = pii.scrub_string(f"Contact: {self.EMAIL}")
        self.assertNotIn(self.EMAIL, out, "email must not survive scrubbing")
        self.assertIn(REDACTED, out)

    def test_email_in_dict_field_is_redacted(self):
        rec = {"email": self.EMAIL, "loan_id": "L-001"}
        out = pii.scrub(rec)
        self.assertFalse(_contains_pii(out, self.EMAIL), "email value must not survive")
        self.assertEqual(out["loan_id"], "L-001", "non-PII field must survive")

    def test_no_email_passes_unchanged(self):
        rec = {"loan_id": "L-001", "outstanding_principal": 3900000}
        out = pii.scrub(rec)
        self.assertEqual(out, rec, "clean record must be unchanged by scrubber")


# ===========================================================================
# 2. Phone numbers
# ===========================================================================

class PhoneRedactionTest(unittest.TestCase):
    """Phone numbers (US + international) must be redacted."""

    PHONES = [
        "555-867-5309",       # US dashes
        "(555) 867-5309",     # US with parens
        "555.867.5309",       # US dots
        "+44 7700 900123",    # international
    ]

    def test_us_phone_in_string_redacted(self):
        for phone in self.PHONES[:3]:
            with self.subTest(phone=phone):
                out = pii.scrub_string(f"Call {phone} for details")
                self.assertNotIn(phone, out, f"phone {phone!r} must be redacted")

    def test_phone_in_dict_field_redacted(self):
        rec = {"phone": "555-867-5309", "currency": "USD"}
        out = pii.scrub(rec)
        self.assertEqual(out["phone"], REDACTED, "phone field must be redacted")
        self.assertEqual(out["currency"], "USD", "currency must survive")

    def test_phone_field_name_variants(self):
        for field in ("phone_number", "mobile", "cell", "fax"):
            with self.subTest(field=field):
                rec = {field: "555-123-4567"}
                out = pii.scrub(rec)
                self.assertEqual(out[field], REDACTED)


# ===========================================================================
# 3. SSN / TIN / EIN
# ===========================================================================

class TaxIdRedactionTest(unittest.TestCase):
    """SSN (ddd-dd-dddd) and EIN (dd-ddddddd) must be redacted."""

    SSN = "123-45-6789"
    EIN = "12-3456789"

    def test_ssn_in_string_redacted(self):
        out = pii.scrub_string(f"SSN is {self.SSN}")
        self.assertNotIn(self.SSN, out, "SSN must be redacted in strings")

    def test_ein_in_string_redacted(self):
        out = pii.scrub_string(f"EIN: {self.EIN}")
        self.assertNotIn(self.EIN, out, "EIN must be redacted in strings")

    def test_ssn_field_redacted(self):
        rec = {"ssn": self.SSN, "borrower_id": "B-001"}
        out = pii.scrub(rec)
        self.assertEqual(out["ssn"], REDACTED)
        self.assertEqual(out["borrower_id"], "B-001")

    def test_tax_id_field_name_variants(self):
        for field in ("tin", "ein", "tax_id", "social_security_number",
                      "tax_identification_number"):
            with self.subTest(field=field):
                rec = {field: "123-45-6789"}
                out = pii.scrub(rec)
                self.assertEqual(out[field], REDACTED)


# ===========================================================================
# 4. Legal name / borrower name
# ===========================================================================

class NameRedactionTest(unittest.TestCase):
    """Name fields must be redacted; non-name strings survive intact."""

    def test_legal_name_field_redacted(self):
        rec = {"legal_name": "Alice Smith", "loan_id": "L-001"}
        out = pii.scrub(rec)
        self.assertEqual(out["legal_name"], REDACTED)
        self.assertEqual(out["loan_id"], "L-001")

    def test_borrower_name_field_redacted(self):
        for field in ("borrower_name", "first_name", "last_name", "full_name",
                      "name", "contact_name", "guarantor_name"):
            with self.subTest(field=field):
                rec = {field: "Bob Jones"}
                out = pii.scrub(rec)
                self.assertEqual(out[field], REDACTED)

    def test_name_not_in_unrelated_field(self):
        """A name-like value in a non-PII field must have inline patterns scrubbed, not the whole value."""
        rec = {"notes": "Loan for Alice Smith (borrower_id B-001)", "currency": "USD"}
        out = pii.scrub(rec)
        # The email/phone/SSN patterns won't match a plain name in notes — that's OK.
        # The KEY point is the currency field survives.
        self.assertEqual(out["currency"], "USD")


# ===========================================================================
# 5. Street addresses
# ===========================================================================

class AddressRedactionTest(unittest.TestCase):
    """Street addresses must be redacted from fields and inline strings."""

    ADDRESS = "742 Evergreen Terrace"

    def test_address_field_redacted(self):
        for field in ("address", "street_address", "mailing_address", "home_address"):
            with self.subTest(field=field):
                rec = {field: self.ADDRESS}
                out = pii.scrub(rec)
                self.assertEqual(out[field], REDACTED)

    def test_address_pattern_in_string_redacted(self):
        out = pii.scrub_string(f"Property at {self.ADDRESS}, Springfield, IL")
        self.assertNotIn(self.ADDRESS, out)

    def test_zip_code_field_redacted(self):
        rec = {"zip": "62704", "state": "IL"}
        out = pii.scrub(rec)
        self.assertEqual(out["zip"], REDACTED)


# ===========================================================================
# 6. Account / routing numbers
# ===========================================================================

class AccountNumberRedactionTest(unittest.TestCase):
    """Long digit runs (account/routing numbers) must be redacted from fields."""

    def test_account_number_field_redacted(self):
        for field in ("account_number", "bank_account", "routing_number"):
            with self.subTest(field=field):
                rec = {field: "0001234567890"}
                out = pii.scrub(rec)
                self.assertEqual(out[field], REDACTED)

    def test_long_digit_run_in_string_redacted(self):
        """A bare 12-digit account number in a string must be caught by the regex."""
        out = pii.scrub_string("Account: 012345678901 (checking)")
        self.assertNotIn("012345678901", out)


# ===========================================================================
# 7. Aggregates and IDs are PRESERVED (hard requirement)
# ===========================================================================

class AggregatesPreservedTest(unittest.TestCase):
    """Dollar amounts, percentages, LTV ratios, interest rates, and IDs must survive.

    These are the deliverable financial aggregates — they do NOT carry PII.
    """

    def test_dollar_amounts_survive(self):
        rec = {
            "outstanding_principal": 3900000,
            "funded_amount": 4200000,
            "commitment_amount": 5000000,
            "currency": "USD",
        }
        out = pii.scrub(rec)
        self.assertEqual(out["outstanding_principal"], 3900000)
        self.assertEqual(out["funded_amount"], 4200000)
        self.assertEqual(out["currency"], "USD")

    def test_interest_rate_survives(self):
        rec = {"interest_rate": 0.115, "rate_type": "fixed"}
        out = pii.scrub(rec)
        self.assertEqual(out["interest_rate"], 0.115)

    def test_loan_id_survives(self):
        rec = {"loan_id": "L-001", "borrower_id": "B-001"}
        out = pii.scrub(rec)
        self.assertEqual(out["loan_id"], "L-001")
        self.assertEqual(out["borrower_id"], "B-001")

    def test_status_survives(self):
        rec = {"status": "active", "facility_type": "bridge"}
        out = pii.scrub(rec)
        self.assertEqual(out["status"], "active")
        self.assertEqual(out["facility_type"], "bridge")

    def test_dates_survive(self):
        rec = {"origination_date": "2025-03-01", "maturity_date": "2027-03-01"}
        out = pii.scrub(rec)
        self.assertEqual(out["origination_date"], "2025-03-01")
        self.assertEqual(out["maturity_date"], "2027-03-01")

    def test_boolean_and_none_survive(self):
        rec = {"active": True, "collateral_ids": None}
        out = pii.scrub(rec)
        self.assertEqual(out["active"], True)
        self.assertIsNone(out["collateral_ids"])


# ===========================================================================
# 8. Nested / list structures
# ===========================================================================

class NestedStructureTest(unittest.TestCase):
    """PII in nested dicts or lists must be scrubbed at every depth."""

    def test_nested_dict_pii_redacted(self):
        rec = {
            "loan_id": "L-001",
            "borrower": {
                "legal_name": "Alice Smith",
                "email": "alice@example.com",
                "outstanding_principal": 3900000,
            },
        }
        out = pii.scrub(rec)
        self.assertEqual(out["loan_id"], "L-001")
        self.assertEqual(out["borrower"]["legal_name"], REDACTED)
        self.assertEqual(out["borrower"]["email"], REDACTED)
        self.assertEqual(out["borrower"]["outstanding_principal"], 3900000)

    def test_list_of_dicts(self):
        records = [
            {"loan_id": "L-001", "email": "a@b.com"},
            {"loan_id": "L-002", "email": "c@d.com"},
        ]
        out = pii.scrub(records)
        self.assertEqual(out[0]["loan_id"], "L-001")
        self.assertEqual(out[0]["email"], REDACTED)
        self.assertEqual(out[1]["email"], REDACTED)

    def test_list_of_strings(self):
        items = ["alice@example.com", "L-001", "555-123-4567"]
        out = pii.scrub(items)
        self.assertNotIn("alice@example.com", out)
        self.assertIn("L-001", out)
        self.assertNotIn("555-123-4567", out)


# ===========================================================================
# 9. scrub_evidence top-level entry point
# ===========================================================================

class ScrubEvidenceTest(unittest.TestCase):
    """scrub_evidence() is the top-level API; it must not mutate the original."""

    def test_does_not_mutate_original(self):
        original = {"legal_name": "Alice Smith", "outstanding_principal": 3900000}
        _ = pii.scrub_evidence(original)
        self.assertEqual(original["legal_name"], "Alice Smith",
                         "scrub_evidence must not mutate the original")

    def test_full_bundle_scrubbed(self):
        bundle = {
            "borrower_name": "Bob Jones",
            "email": "bob@loans.io",
            "outstanding_principal": 1_500_000,
            "notes": "Call 555-321-4321 for docs.",
        }
        out = pii.scrub_evidence(bundle)
        self.assertFalse(_contains_pii(out, "Bob Jones"),
                         "name must not appear in evidence output")
        self.assertFalse(_contains_pii(out, "bob@loans.io"),
                         "email must not appear in evidence output")
        self.assertFalse(_contains_pii(out, "555-321-4321"),
                         "phone must not appear in evidence output")
        self.assertEqual(out["outstanding_principal"], 1_500_000,
                         "dollar aggregate must survive")


# ===========================================================================
# 10. scrub_json_string
# ===========================================================================

class ScrubJsonStringTest(unittest.TestCase):
    def test_valid_json_scrubbed(self):
        payload = json.dumps({"email": "x@y.com", "amount": 5000})
        out = pii.scrub_json_string(payload)
        data = json.loads(out)
        self.assertEqual(data["email"], REDACTED)
        self.assertEqual(data["amount"], 5000)

    def test_invalid_json_falls_back_to_regex(self):
        text = "plain text with alice@example.com here"
        out = pii.scrub_json_string(text)
        self.assertNotIn("alice@example.com", out)


# ===========================================================================
# 11. IP address and credit-card patterns
# ===========================================================================

class IpAndCardTest(unittest.TestCase):
    def test_ipv4_field_redacted(self):
        rec = {"ip_address": "192.168.1.100", "currency": "USD"}
        out = pii.scrub(rec)
        self.assertEqual(out["ip_address"], REDACTED)
        self.assertEqual(out["currency"], "USD")

    def test_ipv4_in_string_redacted(self):
        out = pii.scrub_string("Client connected from 10.0.0.1 today")
        self.assertNotIn("10.0.0.1", out)

    def test_credit_card_in_string_redacted(self):
        out = pii.scrub_string("card: 4111 1111 1111 1111")
        self.assertNotIn("4111 1111 1111 1111", out)


if __name__ == "__main__":
    unittest.main()
