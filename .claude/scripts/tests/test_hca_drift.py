#!/usr/bin/env python3
"""test_hca_drift.py — stdlib unittest for SLICE-HCA-11 schema-drift gate hardening.

ADVERSARIAL by construction. Every drift hostile case MUST FAIL. The clean case MUST PASS.
Nothing is silently absorbed (R4).

Hostile cases:
  1. Renamed field (loan_drift_renamed__L-903.json): outstanding_principal -> current_balance.
     Gate must: detect current_balance as unexpected, detect outstanding_principal missing.
  2. Type-narrowed field (loan_drift_type_narrowed__L-904.json): commitment_amount is string
     where schema says number. Gate must detect type-changed.
  3. Added-required-field missing: a record that is simply missing a required field
     (no unexpected fields added). Gate must detect the missing required field.

Clean case:
  - loan__L-001.json — all fields match the expected schema, required fields present,
    no unexpected fields. Gate must PASS.

The gate-drift result shape checked:
  {gate, status: PASS|FAIL, reason, evidence: {added_fields, missing_fields, type_changed}}

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
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPTS_DIR, os.pardir, os.pardir))
_FIXTURES = os.path.join(_REPO_ROOT, ".claude", "skills", "acos-hypercore-ask", "fixtures")
_ADV = os.path.join(_FIXTURES, "adversarial")
_SCHEMAS = os.path.join(_REPO_ROOT, ".claude", "skills", "acos-hypercore-ask", "schemas")


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


gates = _load("hca_gates", "hca-gates.py")


def _fx(name):
    with open(os.path.join(_FIXTURES, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _adv(name):
    with open(os.path.join(_ADV, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _schema(name):
    with open(os.path.join(_SCHEMAS, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


# ===========================================================================
# Schema-drift gate — adversarial (SLICE-HCA-11 hardening)
# ===========================================================================

class SchemaDriftHardeningTest(unittest.TestCase):
    """Schema-drift gate under adversarial conditions. Nothing silently absorbed (R4)."""

    # --- CLEAN CASE: no drift -----------------------------------------------
    def test_PASS_clean_loan_no_drift(self):
        """Clean loan fixture with all expected fields, no extras, correct types — MUST PASS."""
        res = gates.gate_schema_drift(_fx("loan__L-001.json"), "loan")
        self.assertEqual(res["status"], gates.PASS,
                         "clean loan with matching schema must PASS drift gate")
        ev = res["evidence"]
        self.assertEqual(ev.get("added_fields", []), [],
                         "no added_fields in clean fixture")
        self.assertEqual(ev.get("missing_fields", []), [],
                         "no missing_fields in clean fixture")
        self.assertEqual(ev.get("type_changed", []), [],
                         "no type_changed in clean fixture")

    # --- HOSTILE CASE 1: renamed field --------------------------------------
    def test_FAIL_drift_renamed_field(self):
        """Renamed-field fixture: outstanding_principal -> current_balance.

        The gate must detect:
          - 'current_balance' as an added/unexpected field.
          - 'outstanding_principal' as missing (it is in required_fields).
        MUST FAIL. Nothing silently absorbed (R4: never absorb drift).
        """
        src = _adv("loan_drift_renamed__L-903.json")
        res = gates.gate_schema_drift(src, "loan")
        self.assertEqual(res["status"], gates.FAIL,
                         "renamed-field drift MUST FAIL schema-drift gate")
        ev = res["evidence"]
        added_names = {a["field"] for a in ev.get("added_fields", [])}
        missing_names = {m["field"] for m in ev.get("missing_fields", [])}
        self.assertIn("current_balance", added_names,
                      "renamed field 'current_balance' must appear in added_fields")
        self.assertIn("outstanding_principal", missing_names,
                      "missing required field 'outstanding_principal' must appear in missing_fields")

    # --- HOSTILE CASE 2: type narrowed --------------------------------------
    def test_FAIL_drift_type_narrowed(self):
        """Type-narrowed fixture: commitment_amount is a string instead of a number.

        The gate must detect the type change (observed: string, expected: number).
        MUST FAIL. Nothing silently absorbed (R4).
        """
        src = _adv("loan_drift_type_narrowed__L-904.json")
        res = gates.gate_schema_drift(src, "loan")
        self.assertEqual(res["status"], gates.FAIL,
                         "type-narrowed drift MUST FAIL schema-drift gate")
        ev = res["evidence"]
        type_changed = ev.get("type_changed", [])
        changed_fields = {(t["field"], t["expected"], t["observed"]) for t in type_changed}
        self.assertIn(("commitment_amount", "number", "string"), changed_fields,
                      "type change on commitment_amount (number->string) must be detected")

    # --- HOSTILE CASE 3: added required field missing (no extra fields) -----
    def test_FAIL_drift_added_required_field_missing(self):
        """A record missing a required field (loan_id) with no unexpected extras.

        The drift gate (not schema_validation) must detect the missing required
        field via the missing_fields path. MUST FAIL (R4).
        """
        rec = _fx("loan__L-001.json")
        # Remove the 'loan_id' required field.
        del rec["body"]["loan_id"]
        res = gates.gate_schema_drift(rec, "loan")
        self.assertEqual(res["status"], gates.FAIL,
                         "missing required field 'loan_id' must FAIL schema-drift gate")
        ev = res["evidence"]
        missing_names = {m["field"] for m in ev.get("missing_fields", [])}
        self.assertIn("loan_id", missing_names,
                      "missing required field 'loan_id' must appear in missing_fields evidence")

    # --- HOSTILE CASE 4: existing drifted fixture (slice-02 adversarial) ----
    def test_FAIL_loan_drifted_fixture_required(self):
        """The existing loan_drifted__L-901 fixture must FAIL (REQUIRED — R4 baseline).

        Covers: outstanding_principal->principal_outstanding (renamed), currency
        missing (required field dropped), legacy_balance (unexpected addition).
        """
        res = gates.gate_schema_drift(_fx("loan_drifted__L-901.json"), "loan")
        self.assertEqual(res["status"], gates.FAIL,
                         "loan_drifted__L-901 MUST FAIL schema-drift gate (R4 baseline)")
        ev = res["evidence"]
        added_names = {a["field"] for a in ev.get("added_fields", [])}
        missing_names = {m["field"] for m in ev.get("missing_fields", [])}
        self.assertIn("principal_outstanding", added_names,
                      "principal_outstanding (renamed field) must be in added_fields")
        self.assertIn("legacy_balance", added_names,
                      "legacy_balance (unexpected field) must be in added_fields")
        self.assertIn("currency", missing_names,
                      "currency (required, dropped) must be in missing_fields")

    # --- Drift result shape contract ----------------------------------------
    def test_drift_result_shape_on_fail(self):
        """FAIL result must carry all three evidence arrays (even if some are empty)."""
        src = _adv("loan_drift_renamed__L-903.json")
        res = gates.gate_schema_drift(src, "loan")
        self.assertEqual(res["gate"], gates.GATE_DRIFT,
                         "gate name must be schema_drift")
        self.assertIn("status", res)
        self.assertIn("reason", res)
        ev = res["evidence"]
        self.assertIn("added_fields", ev,
                      "evidence must contain 'added_fields' key on FAIL")
        self.assertIn("missing_fields", ev,
                      "evidence must contain 'missing_fields' key on FAIL")
        self.assertIn("type_changed", ev,
                      "evidence must contain 'type_changed' key on FAIL")

    def test_drift_result_shape_on_pass(self):
        """PASS result must carry the standard gate result shape."""
        res = gates.gate_schema_drift(_fx("loan__L-001.json"), "loan")
        self.assertEqual(res["gate"], gates.GATE_DRIFT)
        self.assertEqual(res["status"], gates.PASS)
        self.assertIn("reason", res)
        self.assertIn("evidence", res)

    # --- No drift silently absorbed — gate is a HARD gate -------------------
    def test_gate_drift_is_a_hard_gate(self):
        """GATE_DRIFT must be in HARD_GATES (drift FAIL forces suite to refuse)."""
        self.assertIn(gates.GATE_DRIFT, gates.HARD_GATES,
                      "schema_drift must be a hard gate (FAIL -> refuse)")

    # --- Suite-level: drift FAIL forces outcome == refuse --------------------
    def test_suite_refuses_on_drift(self):
        """GateSuite.run_all must refuse when schema_drift FAILs."""
        suite = gates.GateSuite()
        v = suite.run_all(_fx("loan_drifted__L-901.json"), entity_type="loan",
                          source_count=2)
        self.assertEqual(v["outcome"], gates.OUTCOME_REFUSE,
                         "suite must refuse on schema-drift failure")
        self.assertIn(gates.GATE_DRIFT, v["failures"],
                      "schema_drift must appear in suite failures[]")


if __name__ == "__main__":
    unittest.main(verbosity=2)
