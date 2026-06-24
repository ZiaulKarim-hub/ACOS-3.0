#!/usr/bin/env python3
"""hca-pii.py — PII scrubber for logs and evidence bundles (SLICE-HCA-10).

Redacts borrower PII from any string or dict before it is written to logs,
evidence bundles, or any output that leaves the git-ignored cache.

PII CLASSES HANDLED:
  - borrower / legal names — FIELD-NAME-based only (full-value redaction of known
    identity and free-text fields such as legal_name, contact, notes, description).
    There is NO arbitrary-free-text name regex: a personal name buried in genuinely
    unstructured prose under a non-PII key is NOT detected. We redact the WHOLE value
    of fields whose name signals identity or free-text that commonly carries names.
  - email addresses
  - phone numbers (US + international)
  - street addresses (numeric street prefix)
  - SSN / TIN / EIN and other tax/ID numbers (US + non-US) — FIELD-NAME-based for
    arbitrary-shaped IDs (e.g. taxId "AB123456C", identificationNumber "X4815162"),
    regex-based for canonically-shaped US SSN/EIN in free text.
  - account numbers (long digit runs)
  - credit card numbers (16-digit Luhn-shaped)
  - zip codes (US 5+4)
  - IP addresses (v4 / v6)

DESIGN PRINCIPLES:
  - Redact anything that looks like PII in free-text; keep numeric aggregates intact.
  - Field-name-driven redaction for structured dicts: named PII fields (identity,
    contact, tax/ID, free-text) are fully replaced with a redaction token; other
    fields are recursively scrubbed for inline PII patterns.
  - Field-name matching is CASE-INSENSITIVE and camelCase-AWARE: identifiers are split
    into tokens (mobileNumber -> {mobile, number}) before the substring/token check, so
    the LIVE Hypercore camelCase names are caught alongside snake_case variants.
  - The PII field-name vocabulary has a SINGLE source of truth: the live camelCase
    names live in hca-normalize.DEFAULT_PII_FIELDS and are imported here (see
    _canonical_pii_fields); hca-pii adds only snake_case/aliasing breadth on top.
  - The scrubber is conservative: when in doubt, redact.
  - stdlib only (Python 3); no network; no model calls; no secrets.

WHAT IS NOT REDACTED (aggregates):
  - Dollar amounts, percentages, LTV ratios, interest rates — these are the
    deliverable financial data. They do NOT carry PII by themselves.
  - Loan IDs, entity IDs (opaque system identifiers, not personal data).
  - Dates (origination_date, maturity_date) without an accompanying name.
  - CAVEAT (fail-safe over-redaction): a bare, unformatted 10-20 digit run embedded
    in a free-text STRING is treated as a possible account number and IS redacted,
    even if it was actually a numeric aggregate written without separators (e.g.
    "Portfolio total 1234567890"). Numeric aggregates passed as JSON numbers (int /
    float) are always preserved; only string-embedded long digit runs are affected.
    We accept this over-redaction because under-redacting an account number is worse.

GROUND RULES (memory/decisions/2026-06-18-hca-build-ground-rules.md):
  - Python 3 stdlib only.
  - This module is read-only: it returns scrubbed copies; it never mutates in place.
  - It is never called on git-tracked files — only on runtime log/evidence strings.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import re
import sys
from typing import Any, Optional, Union


# ---------------------------------------------------------------------------
# Redaction token
# ---------------------------------------------------------------------------

REDACTED = "[REDACTED]"

# ---------------------------------------------------------------------------
# Single source of truth: the LIVE Hypercore camelCase PII field names
# ---------------------------------------------------------------------------
# The canonical PII field-name vocabulary lives ONCE, in hca-normalize.py
# (DEFAULT_PII_FIELDS — the live Hypercore camelCase names). hca-pii imports it
# here rather than maintaining its own divergent copy. Both files share the same
# lexicon, so they cannot drift again.
#
# hca-normalize uses a hyphenated filename, so it is loaded via the same
# importlib seam pattern hca-normalize itself uses for hca-cache. The load is
# lazy + memoized and degrades safely (empty set) if the sibling is missing, so
# the scrubber can never be locked out — it simply falls back to its own
# snake_case lexicon below.

_CANONICAL_PII_FIELDS_CACHE: Optional[frozenset] = None


def _canonical_pii_fields() -> frozenset:
    """Import hca-normalize.DEFAULT_PII_FIELDS (the live camelCase names) lazily.

    Memoized. No circular import: hca-normalize imports hca-cache (not hca-pii),
    so loading hca-normalize from here introduces no cycle. Fails safe to an empty
    frozenset so a missing/broken sibling never disables redaction.
    """
    global _CANONICAL_PII_FIELDS_CACHE
    if _CANONICAL_PII_FIELDS_CACHE is not None:
        return _CANONICAL_PII_FIELDS_CACHE
    try:
        mod = sys.modules.get("hca_normalize")
        if mod is None:
            here = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(here, "hca-normalize.py")
            spec = importlib.util.spec_from_file_location("hca_normalize", path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["hca_normalize"] = mod
            spec.loader.exec_module(mod)
        fields = frozenset(getattr(mod, "DEFAULT_PII_FIELDS", ()))
    except Exception:
        fields = frozenset()  # fail safe: rely on the snake_case lexicon below
    _CANONICAL_PII_FIELDS_CACHE = fields
    return fields


# ---------------------------------------------------------------------------
# Field-name driven PII classification
# ---------------------------------------------------------------------------

# snake_case / aliasing breadth ADDED ON TOP of the canonical camelCase set.
# Matched case-insensitively against the camelCase-split tokens of the field name.
_PII_FIELD_NAMES: frozenset = frozenset({
    # names
    "legal_name", "borrower_name", "first_name", "last_name", "full_name",
    "name", "contact_name", "guarantor_name", "entity_name",
    # contact
    "email", "email_address", "phone", "phone_number", "mobile", "cell",
    "fax", "address", "street_address", "mailing_address", "home_address",
    "city", "state", "zip", "zip_code", "postal_code", "country",
    # tax / financial IDs (US + non-US)
    "ssn", "tin", "ein", "tax_id", "taxid", "social_security_number",
    "tax_identification_number", "employer_identification_number",
    "identification_number", "identificationnumber", "id_number",
    "passport", "national_id",
    "account_number", "bank_account", "routing_number",
    # auth-adjacent
    "password", "secret", "token", "api_key", "access_token", "refresh_token",
    "client_secret",
    # IP / device
    "ip_address", "ip", "mac_address",
    # demographics
    "date_of_birth", "dob", "birth_date", "gender", "race", "nationality",
})

# Field-name substrings that signal PII even if not an exact match above.
# Checked against the camelCase-normalized (split-then-rejoined) field name.
_PII_FIELD_SUBSTRINGS: tuple = (
    "name", "email", "phone", "mobile", "contact", "address", "ssn", "tin", "ein",
    "tax_id", "taxid", "identification", "id_number", "passport", "national_id",
    "account", "routing", "secret", "token", "password",
    "dob", "birth", "ip_addr",
)

# Free-text fields whose ENTIRE value is redacted because such prose commonly
# carries borrower names and other PII that no field-name or regex rule can catch
# inside arbitrary text. Case-insensitive, camelCase-aware (matched as tokens).
_FREE_TEXT_PII_FIELDS: frozenset = frozenset({
    "contact", "notes", "note", "description", "comment", "comments",
    "memo", "remarks",
})


def _split_camel(key: str) -> str:
    """Lower-case a field name and insert '_' at camelCase / digit boundaries.

    mobileNumber -> 'mobile_number'; taxId -> 'tax_id'; identificationNumber ->
    'identification_number'; SSNValue -> 'ssn_value'. This lets a single set of
    tokens match snake_case, camelCase, PascalCase, and UPPER variants uniformly.
    """
    # boundary between a lowercase/digit and an uppercase letter
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", key)
    # boundary inside acronym runs, e.g. 'SSNValue' -> 'SSN_Value'
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "_", s)
    # collapse existing separators (hyphen / space / dot) to underscore
    s = re.sub(r"[\s\-.]+", "_", s)
    return s.lower().strip("_")


def _is_pii_field(key: str) -> bool:
    """Return True if the field name indicates a PII value.

    Case-insensitive and camelCase-aware: the key is normalized to snake_case
    tokens first, so mobileNumber / taxId / identificationNumber / contact are all
    caught regardless of casing. Matches against (1) the canonical live camelCase
    set imported from hca-normalize, (2) the snake_case/alias set, and (3) the
    free-text set, then falls back to a token-aware substring scan.
    """
    raw_lo = key.lower().strip()
    norm = _split_camel(key)                 # e.g. 'mobile_number', 'tax_id'
    tokens = set(norm.split("_")) if norm else set()

    # 1) canonical camelCase names from hca-normalize — match on the camelCase
    #    form (lower) OR on any normalized token (e.g. 'mobileNumber' -> 'mobile').
    canon_lo = {c.lower() for c in _canonical_pii_fields()}
    if raw_lo in canon_lo or norm in canon_lo:
        return True
    for c in canon_lo:
        c_tokens = set(_split_camel(c).split("_"))
        if c_tokens and c_tokens.issubset(tokens):
            return True

    # 2) exact snake_case / alias names (compare both the raw and normalized forms)
    if raw_lo in _PII_FIELD_NAMES or norm in _PII_FIELD_NAMES:
        return True

    # 3) free-text fields (full-value redaction) — token-level match
    if raw_lo in _FREE_TEXT_PII_FIELDS or norm in _FREE_TEXT_PII_FIELDS:
        return True
    if tokens & _FREE_TEXT_PII_FIELDS:
        return True

    # 4) substring fallback against the normalized name
    return any(substr in norm for substr in _PII_FIELD_SUBSTRINGS)


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
    # International phone: +CC followed by the WHOLE grouped number.
    # Ordered BEFORE the US-phone pattern so it wins on "+1-202-555-0147" forms —
    # otherwise the US pattern would consume the local part and leave "+1-" exposed.
    # Greedily consumes every digit group (with (), space, dash, or dot separators).
    re.compile(r"\+\d{1,3}(?:[\s.\-]?\(?\d{1,4}\)?){1,6}"),
    # US phone: (ddd) ddd-dddd  or  ddd-ddd-dddd  or  ddd.ddd.dddd
    re.compile(r"\(?\d{3}\)?[\s.\-]\d{3}[\s.\-]\d{4}"),
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
