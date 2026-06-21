#!/usr/bin/env python3
"""hca-pii.py — PII scrubber for logs and evidence bundles (SLICE-HCA-10).

Redacts borrower PII from any string or dict before it is written to logs,
evidence bundles, or any output that leaves the git-ignored cache.

PII CLASSES HANDLED:
  - legal_name / borrower names
  - email addresses
  - phone numbers (US + international)
  - street addresses (numeric street prefix)
  - SSN / TIN / EIN (tax IDs)
  - account numbers (long digit runs)
  - credit card numbers (16-digit Luhn-shaped)
  - zip codes (US 5+4)
  - IP addresses (v4 / v6)

DESIGN PRINCIPLES:
  - Redact anything that looks like PII in free-text; keep aggregates intact.
  - Field-name-driven redaction for structured dicts: named PII fields are fully
    replaced with a redaction token; non-PII fields are recursively scrubbed for
    inline PII patterns.
  - The scrubber is conservative: when in doubt, redact.
  - stdlib only (Python 3); no network; no model calls; no secrets.

WHAT IS NOT REDACTED (aggregates):
  - Dollar amounts, percentages, LTV ratios, interest rates — these are the
    deliverable financial data. They do NOT carry PII by themselves.
  - Loan IDs, entity IDs (opaque system identifiers, not personal data).
  - Dates (origination_date, maturity_date) without an accompanying name.

GROUND RULES (memory/decisions/2026-06-18-hca-build-ground-rules.md):
  - Python 3 stdlib only.
  - This module is read-only: it returns scrubbed copies; it never mutates in place.
  - It is never called on git-tracked files — only on runtime log/evidence strings.
"""

from __future__ import annotations

import copy
import json
import re
from typing import Any, Optional, Union


# ---------------------------------------------------------------------------
# Redaction token
# ---------------------------------------------------------------------------

REDACTED = "[REDACTED]"

# ---------------------------------------------------------------------------
# Field-name driven PII classification
# ---------------------------------------------------------------------------

# Fields whose VALUE must be fully redacted regardless of content.
# The match is case-insensitive on the field name.
_PII_FIELD_NAMES: frozenset = frozenset({
    # names
    "legal_name", "borrower_name", "first_name", "last_name", "full_name",
    "name", "contact_name", "guarantor_name", "entity_name",
    # contact
    "email", "email_address", "phone", "phone_number", "mobile", "cell",
    "fax", "address", "street_address", "mailing_address", "home_address",
    "city", "state", "zip", "zip_code", "postal_code", "country",
    # tax / financial IDs
    "ssn", "tin", "ein", "tax_id", "social_security_number",
    "tax_identification_number", "employer_identification_number",
    "account_number", "bank_account", "routing_number",
    # auth-adjacent
    "password", "secret", "token", "api_key", "access_token", "refresh_token",
    "client_secret",
    # IP / device
    "ip_address", "ip", "mac_address",
    # demographics
    "date_of_birth", "dob", "birth_date", "gender", "race", "nationality",
})

# Field-name substrings that signal PII even if not in the exact set above.
# Checked with `any(substr in lower_key ...)`.
_PII_FIELD_SUBSTRINGS: tuple = (
    "name", "email", "phone", "address", "ssn", "tin", "ein",
    "tax_id", "account", "routing", "secret", "token", "password",
    "dob", "birth", "ip_addr",
)


def _is_pii_field(key: str) -> bool:
    """Return True if the field name indicates a PII value."""
    lo = key.lower().strip()
    if lo in _PII_FIELD_NAMES:
        return True
    return any(substr in lo for substr in _PII_FIELD_SUBSTRINGS)


# ---------------------------------------------------------------------------
# Regex-based inline PII patterns (applied to free-text strings)
# ---------------------------------------------------------------------------

# Street address suffix list (USPS standard + common variants).
# Must match the FINAL word of the address string — the regex anchors the
# suffix to a word boundary, so "141 loans" or "$434,989,118" are NOT matched
# (no numeric-only token can carry a street suffix word after it).
_STREET_SUFFIXES = (
    r"Street|St"
    r"|Avenue|Ave"
    r"|Boulevard|Blvd"
    r"|Road|Rd"
    r"|Drive|Dr"
    r"|Lane|Ln"
    r"|Court|Ct"
    r"|Way"
    r"|Place|Pl"
    r"|Circle|Cir"
    r"|Trail|Trl"
    r"|Terrace|Terr|Ter"
    r"|Parkway|Pkwy"
    r"|Highway|Hwy"
    r"|Square|Sq"
    r"|Loop"
    r"|Run"
    r"|Pass"
    r"|Pike"
    r"|Row"
    r"|Path"
)

_PATTERNS: list = [
    # Email addresses (before generic runs)
    re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", re.IGNORECASE),
    # SSN:  ddd-dd-dddd or ddd dd dddd
    re.compile(r"\b\d{3}[- ]\d{2}[- ]\d{4}\b"),
    # EIN: dd-ddddddd
    re.compile(r"\b\d{2}-\d{7}\b"),
    # US phone: (ddd) ddd-dddd  or  ddd-ddd-dddd  or  ddd.ddd.dddd
    re.compile(r"\(?\d{3}\)?[\s.\-]\d{3}[\s.\-]\d{4}"),
    # International phone: +1-... or +44-...
    re.compile(r"\+\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,9}"),
    # Credit card: 16 digits (blocks of 4)
    re.compile(r"\b(\d{4}[\s\-]){3}\d{4}\b"),
    # Long digit runs that look like account numbers (10–20 digits, no decimals around them)
    re.compile(r"(?<!\d)(?<!\.)(\d{10,20})(?!\d)(?!\.)"),
    # US zip+4
    re.compile(r"\b\d{5}(?:-\d{4})?\b"),
    # IPv4
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    # IPv6 (simplified — catches full and compressed)
    re.compile(r"\b[0-9a-fA-F]{1,4}(?::[0-9a-fA-F]{0,4}){2,7}\b"),
    # Street address heuristic: <1-5 digits> <words> <street-suffix>
    # The mandatory street-suffix anchor prevents matching plain aggregates like
    # "141 loans", "3 items", or dollar amounts — none end with a street keyword.
    re.compile(
        r"\b\d{1,5}\s+[A-Za-z][A-Za-z0-9\s]*\b(" + _STREET_SUFFIXES + r")\b",
        re.IGNORECASE,
    ),
]


def scrub_string(text: str) -> str:
    """Redact all inline PII patterns from a plain string.

    Returns the scrubbed copy. Non-string inputs are returned unchanged.
    Order matters: email is matched before digit runs (email has digits too).
    """
    if not isinstance(text, str):
        return text
    out = text
    for pat in _PATTERNS:
        out = pat.sub(REDACTED, out)
    return out


# ---------------------------------------------------------------------------
# Structured-dict scrubber (recursive)
# ---------------------------------------------------------------------------

def scrub(obj: Any, *, _depth: int = 0) -> Any:
    """Recursively scrub PII from a dict, list, or string.

    - dict: PII-named keys get their value replaced with REDACTED.
            Non-PII keys have their value recursively scrubbed.
    - list: each element is recursively scrubbed.
    - str:  inline regex patterns are applied.
    - Other scalars (int, float, bool, None): returned as-is (aggregates intact).

    Returns a deep-scrubbed copy; does NOT mutate the original.
    Capped at depth 50 to guard against pathological nesting.
    """
    if _depth > 50:
        return REDACTED  # conservative: deep nesting in a log is unusual; redact

    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if _is_pii_field(str(k)):
                out[k] = REDACTED
            else:
                out[k] = scrub(v, _depth=_depth + 1)
        return out

    if isinstance(obj, list):
        return [scrub(item, _depth=_depth + 1) for item in obj]

    if isinstance(obj, str):
        return scrub_string(obj)

    # int, float, bool, None — numeric aggregates are preserved
    return obj


def scrub_json_string(json_text: str) -> str:
    """Parse a JSON string, scrub it, and re-serialize. Returns the scrubbed JSON string.

    If the text is not valid JSON, falls back to scrub_string (regex-only pass).
    """
    try:
        obj = json.loads(json_text)
    except (ValueError, TypeError):
        return scrub_string(json_text)
    return json.dumps(scrub(obj), separators=(",", ":"), ensure_ascii=True)


def scrub_log_record(record: dict) -> dict:
    """Scrub a log record dict in place (COPIES first — does not mutate original).

    Convenience wrapper: deep-copies then calls scrub(). Safe to call on any
    logging.LogRecord extra dict or a structlog event dict.
    """
    return scrub(copy.deepcopy(record))


# ---------------------------------------------------------------------------
# Evidence-bundle scrubber (top-level entry point for slice writes)
# ---------------------------------------------------------------------------

def scrub_evidence(bundle: Any) -> Any:
    """Top-level entry point: scrub an evidence bundle before writing outside the cache.

    Accepts any JSON-serializable structure (dict, list, str, scalar). Returns a
    scrubbed deep copy. Call this on every dict/string written to:
      - .acos/evidence/
      - console logs / stderr output
      - any file outside the git-ignored .acos/state/hca-cache/

    Numeric aggregates (amounts, rates, LTV ratios) are preserved; borrower
    PII fields and inline PII patterns are redacted.
    """
    return scrub(bundle)


# ---------------------------------------------------------------------------
# Module-level smoke self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sample = {
        "borrower_name": "Alice Smith",
        "email": "alice.smith@example.com",
        "phone": "555-867-5309",
        "ssn": "123-45-6789",
        "address": "742 Evergreen Terrace, Springfield, IL 62704",
        "loan_id": "L-001",
        "outstanding_principal": 3900000,
        "currency": "USD",
        "notes": "Called borrower at 555-867-5309 re: loan L-001 balance of $3,900,000.",
    }
    result = scrub_evidence(sample)
    print(json.dumps(result, indent=2))
