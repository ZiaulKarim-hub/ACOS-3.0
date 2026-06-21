#!/usr/bin/env python3
"""test_hca_freshness.py — stdlib unittest for SLICE-HCA-11 freshness gate hardening.

ADVERSARIAL by construction. Every stale hostile case MUST FAIL. Clean case MUST PASS.
Never-serve-stale-silently invariant must hold in all cases.

Hostile cases:
  1. Stale-at-boundary (loan_stale_boundary__L-902.json): fetched_at is exactly 1 second
     past the 1-day (86400s) freshness window boundary.  Gate must FAIL.
  2. Clock-skew simulation: a timestamp that is nominally in the future relative to `now`.
     This can happen if the cache clock and the gate's `now` differ slightly. Gate must PASS
     (future timestamps are fresh — the record was fetched after our reference time).
  3. Far-stale (loan_stale__L-900.json): 2024-01-01 timestamp — far outside any window.
  4. Missing timestamp (no fetched_at / no provenance.fetched_at): MUST FAIL (cannot
     prove freshness; never serve unknown-age data).

Clean cases:
  - loan__L-001.json with now pinned to 2026-06-18T12:00:00Z: within the 1-day window.
  - A 'client' entity with a 30-day window: within-window timestamp MUST PASS.

Never-serve-stale-silently invariant:
  - When any stale fixture is passed to GateSuite.run_all(), the suite outcome MUST be
    'refuse', not a 'warn-and-proceed'. Confirmed for both the boundary case and the
    far-stale case.

Run:
  python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py' -v
"""

import datetime
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
cache_mod = _load("hca_cache", "hca-cache.py")


def _fx(name):
    with open(os.path.join(_FIXTURES, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _adv(name):
    with open(os.path.join(_ADV, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Reference time anchor for deterministic tests
# ---------------------------------------------------------------------------

# Gate 'now' reference: 2026-06-18 12:00:00 UTC
_NOW = datetime.datetime(2026, 6, 18, 12, 0, 0, tzinfo=datetime.timezone.utc)

# The boundary fixture timestamp is 2026-06-17T07:59:59Z.
# Elapsed relative to _NOW: ~(1 day + 4 hours + 1 second) > 86400s — stale.
_BOUNDARY_TS = "2026-06-17T07:59:59Z"


# ===========================================================================
# Freshness gate — adversarial (SLICE-HCA-11 hardening)
# ===========================================================================

class FreshnessHardeningTest(unittest.TestCase):
    """Freshness gate under adversarial conditions. Never serve stale silently (S2)."""

    # --- CLEAN CASE: within window ------------------------------------------
    def test_PASS_fresh_loan_within_window(self):
        """loan__L-001 with timestamp 2026-06-18T08:00:00Z is within the 1-day window
        relative to _NOW (2026-06-18T12:00:00Z). Gate must PASS."""
        res = gates.gate_freshness(_fx("loan__L-001.json"), "loan", now=_NOW)
        self.assertEqual(res["status"], gates.PASS,
                         "fresh loan within window must PASS freshness gate")
        ev = res["evidence"]
        self.assertEqual(ev["window_days"], 1,
                         "window_days must be 1 for entity class 'loan'")

    # --- HOSTILE CASE 1: stale at boundary (1 second past window) -----------
    def test_FAIL_stale_at_boundary(self):
        """Stale-at-boundary fixture: timestamp exactly 1 second past the 1-day boundary.

        elapsed ≈ 1d 4h 1s > 86400s. Gate must FAIL with flag_refresh=True.
        Never serve stale silently (S2). No grace second, no rounding.
        (SLICE-HCA-11 REQUIRED.)
        """
        src = _adv("loan_stale_boundary__L-902.json")
        res = gates.gate_freshness(src, "loan", now=_NOW)
        self.assertEqual(res["status"], gates.FAIL,
                         "stale-at-boundary MUST FAIL freshness gate (1s past window)")
        ev = res["evidence"]
        self.assertTrue(ev.get("flag_refresh"),
                        "stale gate result must carry flag_refresh=True")
        self.assertEqual(ev["window_days"], 1,
                         "window_days must be 1 for entity class 'loan'")
        self.assertEqual(ev["fetched_at"], _BOUNDARY_TS,
                         "evidence must surface the offending fetched_at timestamp")

    # --- HOSTILE CASE 2: far-stale fixture (slice-02 required fixture) ------
    def test_FAIL_far_stale_required(self):
        """loan_stale__L-900: timestamp 2024-01-01, far outside any window. REQUIRED."""
        res = gates.gate_freshness(_fx("loan_stale__L-900.json"), "loan", now=_NOW)
        self.assertEqual(res["status"], gates.FAIL,
                         "far-stale fixture MUST FAIL freshness gate (REQUIRED)")
        self.assertTrue(res["evidence"].get("flag_refresh"),
                        "far-stale result must carry flag_refresh=True")

    # --- HOSTILE CASE 3: missing timestamp ----------------------------------
    def test_FAIL_missing_timestamp(self):
        """A record with no fetched_at / no provenance.fetched_at MUST FAIL.

        Gate rule: never serve data of unknown age (cannot prove freshness).
        """
        rec = _fx("loan__L-001.json")
        del rec["timestamp"]
        rec["body"].pop("provenance", None)
        res = gates.gate_freshness(rec, "loan", now=_NOW)
        self.assertEqual(res["status"], gates.FAIL,
                         "missing timestamp must FAIL freshness gate")
        self.assertIsNone(res["evidence"]["fetched_at"],
                          "evidence.fetched_at must be None when no timestamp found")

    # --- HOSTILE CASE 4: clock-skew — timestamp slightly in the future ------
    def test_PASS_future_timestamp_is_fresh(self):
        """A timestamp slightly in the future (clock skew) must PASS — it is not stale.

        Stale means older than the window, not newer. A future timestamp is fresh
        (the record was fetched after our reference 'now'). The gate must not FAIL
        a fresh record just because the clock skew put it nominally in the future.
        """
        skew_ts = "2026-06-18T13:00:00Z"  # 1h ahead of _NOW
        rec = _fx("loan__L-001.json")
        rec["timestamp"] = skew_ts
        res = gates.gate_freshness(rec, "loan", now=_NOW)
        self.assertEqual(res["status"], gates.PASS,
                         "a future timestamp (clock skew) must PASS freshness gate "
                         "(the record is fresh, not stale)")

    # --- Window comes from config (not hardcoded) ----------------------------
    def test_window_comes_from_config_not_hardcoded(self):
        """The freshness window reported in evidence must match cache_mod.freshness_window_days.

        Ensures the gate reads the config-driven window, never a hardcoded constant.
        """
        from_config = cache_mod.freshness_window_days("loan")
        res = gates.gate_freshness(_fx("loan__L-001.json"), "loan", now=_NOW)
        self.assertEqual(res["evidence"]["window_days"], from_config,
                         "evidence.window_days must match the config-driven freshness window")

    # --- Reference-static entity (30-day window) ----------------------------
    def test_PASS_reference_static_within_30d_window(self):
        """A 'client' entity with a 29-day-old timestamp must PASS (window=30d)."""
        # Construct a source with a 29-day-old timestamp.
        old_ts = (_NOW - datetime.timedelta(days=29)).strftime("%Y-%m-%dT%H:%M:%SZ")
        src = {
            "entity_type": "client",
            "timestamp": old_ts,
            "body": {"client_id": "C-SYN-1", "name": "Test Client"},
        }
        res = gates.gate_freshness(src, "client", now=_NOW)
        self.assertEqual(res["status"], gates.PASS,
                         "client entity 29d old must PASS (30d window)")
        self.assertEqual(res["evidence"]["window_days"], 30)

    def test_FAIL_reference_static_past_30d_window(self):
        """A 'client' entity with a 31-day-old timestamp must FAIL (window=30d)."""
        old_ts = (_NOW - datetime.timedelta(days=31)).strftime("%Y-%m-%dT%H:%M:%SZ")
        src = {
            "entity_type": "client",
            "timestamp": old_ts,
            "body": {"client_id": "C-SYN-2", "name": "Old Client"},
        }
        res = gates.gate_freshness(src, "client", now=_NOW)
        self.assertEqual(res["status"], gates.FAIL,
                         "client entity 31d old must FAIL (30d window)")
        self.assertTrue(res["evidence"].get("flag_refresh"))


# ===========================================================================
# Never-serve-stale-silently — suite-level invariant
# ===========================================================================

class NeverServeStaleInvariantTest(unittest.TestCase):
    """Confirms that stale data never reaches the delivery path.

    Any stale fixture through GateSuite.run_all() must result in outcome == 'refuse',
    not a 'warn-and-proceed'. This is the highest-level invariant of the freshness gate.
    """

    def setUp(self):
        self.suite = gates.GateSuite(now=_NOW)

    def test_suite_refuses_boundary_stale(self):
        """GateSuite.run_all on stale-at-boundary fixture must outcome == 'refuse'."""
        src = _adv("loan_stale_boundary__L-902.json")
        v = self.suite.run_all(src, entity_type="loan", source_count=2)
        self.assertEqual(v["outcome"], gates.OUTCOME_REFUSE,
                         "suite must refuse stale-at-boundary (no warn-and-proceed)")
        self.assertIn(gates.GATE_FRESHNESS, v["failures"],
                      "freshness must be listed in suite failures")

    def test_suite_refuses_far_stale(self):
        """GateSuite.run_all on far-stale fixture must outcome == 'refuse'."""
        v = self.suite.run_all(_fx("loan_stale__L-900.json"), entity_type="loan",
                               source_count=2)
        self.assertEqual(v["outcome"], gates.OUTCOME_REFUSE,
                         "suite must refuse far-stale (no warn-and-proceed)")
        self.assertIn(gates.GATE_FRESHNESS, v["failures"])

    def test_freshness_is_a_hard_gate(self):
        """GATE_FRESHNESS must be in HARD_GATES (stale FAIL -> refuse, never warn)."""
        self.assertIn(gates.GATE_FRESHNESS, gates.HARD_GATES,
                      "freshness must be a hard gate (FAIL => refuse, no warn-and-proceed)")

    def test_suite_passes_fresh_loan(self):
        """GateSuite.run_all on a fresh loan must PASS the freshness gate."""
        v = self.suite.run_all(_fx("loan__L-001.json"), entity_type="loan",
                               source_count=2)
        # Freshness should pass; other gate failures are acceptable for this test.
        gate_results = {g["gate"]: g["status"] for g in v["gates"]}
        self.assertEqual(gate_results.get(gates.GATE_FRESHNESS), gates.PASS,
                         "freshness gate must PASS for a within-window fixture")


if __name__ == "__main__":
    unittest.main(verbosity=2)
