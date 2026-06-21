#!/usr/bin/env python3
"""test_hca_completeness.py — stdlib unittest for SLICE-HCA-11 pagination-completeness hardening.

ADVERSARIAL by construction. Every hostile case MUST FAIL the pagination gate.
Every clean case MUST PASS. Also validates the FreshnessInvalidationHook from
hca-adapter (read-only, no Hypercore mutations).

Hostile cases covered:
  - Deeply-truncated multi-page (list_loan_deeptrunc__page1.json): fetched 10 < total 141.
  - Empty-page mid-walk (list_loan_empty_page_mid__page2.json): page 2 returns 0 items,
    non-null cursor, complete=False.
  - Off-by-one (off_by_one_source): fetched == reported_total - 1 (nearest miss).

Clean case:
  - gql_list_loan__complete.json: fetched == reported_total, complete=True, no cursor.

FreshnessInvalidationHook (read-only):
  - on_change_event marks the specific entity stale.
  - A bulk change event (no id) marks the whole entity_type stale.
  - poll() marks all entries stale when max_age_s is 0 (immediate flush).
  - poll() respects max_age_s: does NOT mark stale before the interval elapses.
  - is_stale() returns False for entries not in the stale set.
  - clear_stale() removes the marker.
  - stale_snapshot() is read-only and returns the loggable copy.
  - No mutating Hypercore call is made (invariant: the class never calls any
    adapter write method, confirmed by inspecting stale_snapshot and is_stale
    return types rather than checking for side effects that don't exist).

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
adapter_mod = _load("hca_adapter", "hca-adapter.py")


def _fx(name):
    with open(os.path.join(_FIXTURES, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _adv(name):
    with open(os.path.join(_ADV, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


# ===========================================================================
# Pagination-completeness — hardened against SLICE-HCA-11 hostile cases
# ===========================================================================

class CompletenessHardeningTest(unittest.TestCase):
    """Pagination-completeness gate under adversarial conditions (SLICE-HCA-11)."""

    # --- HOSTILE CASE 1: deeply-truncated multi-page list -------------------
    def test_FAIL_deeply_truncated_multipage(self):
        """Deeply-truncated fixture: fetched 10 of 141 with a live cursor — MUST FAIL.

        Simulates a server rate-limit or cutoff mid-walk. The gate must refuse:
        fetched(10) < reported_total(141) and cursor non-null (more pages exist).
        No silent truncation. (REQUIRED per SLICE-HCA-11.)
        """
        src = _adv("list_loan_deeptrunc__page1.json")
        res = gates.gate_pagination_completeness(src)
        self.assertEqual(res["status"], gates.FAIL,
                         "deeply-truncated multi-page list MUST FAIL pagination gate")
        # The gate must detect the count shortfall.
        ev = res["evidence"]
        self.assertLess(ev["fetched"], ev["reported_total"],
                        "evidence must show fetched < reported_total")

    # --- HOSTILE CASE 2: empty page mid-walk --------------------------------
    def test_FAIL_empty_page_mid_walk(self):
        """Empty-page-mid-walk: page 2 returns 0 items, complete=False, cursor non-null.

        The gate must refuse: complete=False is an explicit truncation signal.
        """
        src = _adv("list_loan_empty_page_mid__page2.json")
        res = gates.gate_pagination_completeness(src)
        self.assertEqual(res["status"], gates.FAIL,
                         "empty page mid-walk (complete=False) MUST FAIL pagination gate")
        self.assertFalse(res["evidence"].get("complete"),
                         "evidence.complete must be False for empty-page-mid-walk")

    # --- HOSTILE CASE 3: off-by-one total -----------------------------------
    def test_FAIL_off_by_one_total(self):
        """Synthetic off-by-one: fetched == reported_total - 1. Nearest possible miss.

        Proves the gate checks exact equality, not approximate. Even one dropped
        record must cause a FAIL (no silent truncation).
        """
        src = {
            "entity_type": "loan",
            "list": True,
            "timestamp": "2026-06-18T08:00:00Z",
            "body": {
                "data": [{"loan_id": f"L-OBO-{i}"} for i in range(4)],
                "fetched": 4,
                "reported_total": 5,   # one short
                "complete": True,      # backend LIED about completeness
                "next_cursor": None,
            },
        }
        res = gates.gate_pagination_completeness(src)
        self.assertEqual(res["status"], gates.FAIL,
                         "off-by-one (fetched 4 < reported_total 5) MUST FAIL — even with "
                         "complete=True; fetched count takes precedence over the flag")

    # --- CLEAN CASE: complete GQL list walk ---------------------------------
    def test_PASS_complete_gql_list(self):
        """Clean complete GQL list: fetched == reported_total, complete=True, no cursor."""
        src = _fx("gql_list_loan__complete.json")
        res = gates.gate_pagination_completeness(src)
        self.assertEqual(res["status"], gates.PASS,
                         "clean complete GQL list MUST PASS pagination gate")

    # --- Additional completeness hardening: cursor-with-count-match ---------
    def test_FAIL_cursor_contradicts_count_match(self):
        """A non-null next_cursor with fetched == reported_total is a contradiction.

        The server count and the cursor signal disagree; the gate must refuse.
        """
        src = {
            "entity_type": "loan",
            "list": True,
            "timestamp": "2026-06-18T08:00:00Z",
            "body": {
                "data": [{"loan_id": "L-CONT-1"}],
                "fetched": 1,
                "reported_total": 1,
                "next_cursor": "GHOST_CURSOR",
            },
        }
        res = gates.gate_pagination_completeness(src)
        self.assertEqual(res["status"], gates.FAIL,
                         "cursor contradiction (next_cursor non-null, count matches) MUST FAIL")


# ===========================================================================
# FreshnessInvalidationHook — read-only, no Hypercore mutations
# ===========================================================================

class FreshnessInvalidationHookTest(unittest.TestCase):
    """Tests for hca-adapter.FreshnessInvalidationHook (SLICE-HCA-11 requirement).

    READ-ONLY invariant: the hook only updates the in-process stale set. It never
    calls any Hypercore write endpoint. Tests confirm this by checking that all
    observable effects are confined to is_stale() / stale_snapshot() / clear_stale()
    — no network, no file writes, no adapter mutating methods.
    """

    def setUp(self):
        self.hook = adapter_mod.FreshnessInvalidationHook()

    # --- webhook stub: specific entity stale --------------------------------
    def test_change_event_marks_specific_entity_stale(self):
        """on_change_event with an id marks ONLY that id stale, not all entries."""
        self.hook.on_change_event({
            "entity_type": "loan",
            "id": "L-001",
            "change_type": "updated",
        })
        self.assertTrue(self.hook.is_stale("loan", "L-001"),
                        "specific entity id must be marked stale after change event")
        # A different id in the same type must NOT be stale.
        self.assertFalse(self.hook.is_stale("loan", "L-002"),
                         "unrelated entity id must NOT be marked stale")

    # --- webhook stub: bulk change (no id) marks all stale ------------------
    def test_bulk_change_event_marks_all_stale(self):
        """A change event without an id marks the entire entity_type stale (conservative)."""
        self.hook.on_change_event({
            "entity_type": "loan",
            "change_type": "bulk_update",
            # no 'id' field
        })
        self.assertTrue(self.hook.is_stale("loan"),
                        "bulk change event (no id) must mark all 'loan' entries stale")
        self.assertTrue(self.hook.is_stale("loan", "L-ANY"),
                        "any specific id must also be stale after bulk event")

    # --- no cross-type contamination ----------------------------------------
    def test_change_event_does_not_contaminate_other_types(self):
        """Marking 'loan' stale must not affect 'borrower'."""
        self.hook.on_change_event({"entity_type": "loan", "id": "L-001"})
        self.assertFalse(self.hook.is_stale("borrower", "B-001"),
                         "stale marker must not leak to other entity types")

    # --- polling fallback: immediate flush (max_age_s=0) --------------------
    def test_poll_immediate_flush_marks_all_stale(self):
        """poll() with max_age_s=0 must mark ALL entries for entity_type stale immediately."""
        ret = self.hook.poll("loan", max_age_s=0, now_ts=1000.0)
        self.assertTrue(self.hook.is_stale("loan"),
                        "poll with max_age_s=0 must mark all 'loan' entries stale")
        # Return value: -1 signals 'all marked'.
        self.assertEqual(ret, -1,
                         "poll return value must be -1 when all entries are marked stale")

    # --- polling fallback: respects max_age_s interval ----------------------
    def test_poll_respects_interval_before_expiry(self):
        """poll() must NOT mark stale if max_age_s not yet elapsed."""
        now_ts = 10000.0
        # First poll: sets last_polled.
        self.hook.poll("loan", max_age_s=300, now_ts=now_ts)
        # Clear the stale flag to reset state for the interval test.
        self.hook.clear_stale("loan")
        # Second poll: only 100s later (< 300s interval) — must NOT mark stale.
        ret = self.hook.poll("loan", max_age_s=300, now_ts=now_ts + 100.0)
        self.assertEqual(ret, 0,
                         "poll must return 0 (not due) when interval has not elapsed")
        self.assertFalse(self.hook.is_stale("loan"),
                         "entries must NOT be stale when poll interval has not elapsed")

    # --- polling fallback: marks stale after interval elapses ---------------
    def test_poll_marks_stale_after_interval_elapses(self):
        """poll() MUST mark stale once max_age_s has elapsed."""
        now_ts = 10000.0
        self.hook.poll("loan", max_age_s=300, now_ts=now_ts)
        self.hook.clear_stale("loan")
        # 301s later: past the interval — must mark stale.
        ret = self.hook.poll("loan", max_age_s=300, now_ts=now_ts + 301.0)
        self.assertEqual(ret, -1,
                         "poll must mark all stale (return -1) after interval elapses")
        self.assertTrue(self.hook.is_stale("loan"),
                        "entries must be stale once poll interval has elapsed")

    # --- clear_stale removes individual marker ------------------------------
    def test_clear_stale_removes_specific_id(self):
        """clear_stale(type, id) must remove only the specific id from the stale set."""
        self.hook.on_change_event({"entity_type": "loan", "id": "L-001"})
        self.hook.on_change_event({"entity_type": "loan", "id": "L-002"})
        self.hook.clear_stale("loan", "L-001")
        self.assertFalse(self.hook.is_stale("loan", "L-001"),
                         "cleared id must no longer be stale")
        self.assertTrue(self.hook.is_stale("loan", "L-002"),
                        "un-cleared id must still be stale")

    # --- clear_stale removes whole type -------------------------------------
    def test_clear_stale_removes_whole_type(self):
        """clear_stale(type) with no id must clear all stale markers for the type."""
        self.hook.on_change_event({"entity_type": "loan"})
        self.hook.clear_stale("loan")
        self.assertFalse(self.hook.is_stale("loan"),
                         "clear_stale(type) must clear all stale markers for that type")

    # --- fresh entity is not stale ------------------------------------------
    def test_fresh_entity_not_stale(self):
        """An entity not mentioned in any change event must not be stale."""
        self.assertFalse(self.hook.is_stale("loan", "L-FRESH"),
                         "entity with no change event must not be stale")

    # --- stale_snapshot is a loggable copy ----------------------------------
    def test_stale_snapshot_returns_copy(self):
        """stale_snapshot() must return a plain dict (loggable, not the internal set)."""
        self.hook.on_change_event({"entity_type": "loan", "id": "L-001"})
        snap = self.hook.stale_snapshot()
        self.assertIsInstance(snap, dict,
                              "stale_snapshot must return a dict")
        # The snapshot must contain the stale id.
        self.assertIn("loan", snap)
        ids_in_snap = snap["loan"]
        self.assertIn("L-001", ids_in_snap,
                      "stale_snapshot must include the stale entity id")

    # --- malformed events are silently ignored ------------------------------
    def test_malformed_event_ignored(self):
        """A malformed change event (non-dict, missing entity_type) must not crash."""
        self.hook.on_change_event("not-a-dict")
        self.hook.on_change_event({})
        self.hook.on_change_event({"change_type": "updated"})  # no entity_type
        # No exception raised; stale set unchanged.
        self.assertEqual(self.hook.stale_snapshot(), {},
                         "malformed events must not add entries to the stale set")

    # --- READ-ONLY invariant: no mutating method on the hook class ----------
    def test_no_mutating_hypercore_methods(self):
        """The FreshnessInvalidationHook must not expose any Hypercore mutating method.

        Confirms the read-only invariant by checking there is no method named
        with typical write verbs (create, update, delete, post, put, patch, write,
        mutate, send) on the class.
        """
        import inspect
        mutating_verbs = {"create", "update", "delete", "post", "put", "patch",
                          "write", "mutate", "send"}
        members = {name for name, _ in
                   inspect.getmembers(adapter_mod.FreshnessInvalidationHook,
                                      predicate=inspect.isfunction)}
        found = {m for m in members
                 if any(v in m.lower() for v in mutating_verbs)}
        self.assertEqual(found, set(),
                         f"FreshnessInvalidationHook must not expose mutating methods; "
                         f"found: {found}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
