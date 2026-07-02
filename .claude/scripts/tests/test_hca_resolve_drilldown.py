#!/usr/bin/env python3
"""test_hca_resolve_drilldown.py — progressive-disclosure resolution (learned alias + partial
signal + native tranche drill-down). All fakes; no live creds, no network.

Motivating case: "409 Hodson" shares NO distinctive token with "North Carolina II - 409 High
Point", so pure fuzzy resolution missed it. Three additive layers fix that WITHOUT weakening the
never-silently-pick / never-fabricate guarantees:

  LAYER 3  learned alias (hca-learned.entity_for_query)   — a CONFIRMED "409 hodson" -> loan 144
           resolves directly next time (exact OR all-tokens-present inside a longer query). Routing
           only: the id is re-fetched live downstream, never a stored value.
  LAYER 1  partial-signal surfacing (LoanResolver)        — when no full-name match clears the bar,
           surface loans sharing a discriminator token (a street number / distinctive word) as
           LOW-confidence candidates to drill into. Capped < high-confidence: always disambiguate.
  LAYER 2  native tranche drill-down (LoanResolver.group_tree) — walk the RELIABLE parentLoan edge
           (child->parent) to enumerate a multi-tranche facility's tranches (the reverse
           groupSubLoans edge is not populated by the backend).
"""

import importlib.util
import os
import sys
import tempfile
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


resolve_mod = _load("hca_resolve", "hca-resolve.py")
learned_mod = _load("hca_learned", "hca-learned.py")


# A North-Carolina-II-shaped facility with the REAL parentLoan edges (child -> parent 141) and one
# unrelated standalone loan. groupSubLoans deliberately omitted (backend returns it empty).
_PARENT = {"id": "141", "name": "North Carolina II - Multi Tranche"}


def _tranche(lid, name):
    return {"id": lid, "name": name, "status": "Active",
            "parentLoan": {"id": "141", "name": _PARENT["name"]}}


_NC_LOANS = [
    {"id": "141", "name": "North Carolina II - Multi Tranche", "status": "Active", "parentLoan": None},
    _tranche("142", "North Carolina II - 202 High Point"),
    _tranche("143", "North Carolina II - 206 High Point"),
    _tranche("144", "North Carolina II - 409 High Point"),
    _tranche("145", "North Carolina II - 1203 High Point"),
    _tranche("146", "North Carolina II - 1609 High Point"),
    {"id": "999", "name": "Standalone Bridge Loan", "status": "Active", "parentLoan": None},
]


class _FakeClient:
    """Honors the searchString substring filter over a loan fixture; returns full row dicts
    (so parentLoan rides along for the tree tests)."""

    def __init__(self, loans=None):
        self.loans = loans if loans is not None else list(_NC_LOANS)
        self.queries = []

    def raw_query(self, query, variables=None):
        self.queries.append((query, variables))
        filt = (variables or {}).get("filter") or {}
        ss = (filt.get("searchString") or "").strip().lower()
        rows = [l for l in self.loans if ss in l["name"].lower()] if ss else list(self.loans)
        return {"loans": {"totalFilteredRecords": len(rows), "pageItems": rows}}


class _FakeLearned:
    """Minimal learned-store stand-in exposing only entity_for_query (what resolve consults)."""

    def __init__(self, result=None):
        self._result = result
        self.calls = []

    def entity_for_query(self, q):
        self.calls.append(q)
        return self._result


# ---------------------------------------------------------------------------
# LAYER 3 — learned-alias resolution inside resolve_loan
# ---------------------------------------------------------------------------

class LearnedAliasResolveTest(unittest.TestCase):
    def test_learned_loan_resolves_directly(self):
        learned = _FakeLearned({"entity_type": "loan", "id": "144",
                                "name": "STALE STORED LABEL"})   # deliberately stale label
        r = resolve_mod.LoanResolver(client=_FakeClient(), learned=learned)
        out = r.resolve_loan("409 Hodson")
        self.assertTrue(out["resolved"])
        self.assertEqual(out["via"], "learned")
        self.assertEqual(out["match"]["id"], "144")
        # the learned path RE-VERIFIES live: the match name is the current row name, NOT the
        # (stale) stored label — no stale value is ever replayed.
        self.assertEqual(out["match"]["name"], "North Carolina II - 409 High Point")
        self.assertNotEqual(out["match"]["name"], "STALE STORED LABEL")
        self.assertIn("[verified live]", out["echo"])

    def test_dangling_learned_alias_falls_through(self):
        # learned points at an id that no longer resolves to any live loan -> the alias is NOT
        # trusted; resolution falls through (here to partial-signal on '409').
        learned = _FakeLearned({"entity_type": "loan", "id": "77777", "name": "Ghost Loan"})
        r = resolve_mod.LoanResolver(client=_FakeClient(), learned=learned)
        out = r.resolve_loan("409 Hodson")
        self.assertNotEqual(out.get("via"), "learned")   # dangling id not returned
        self.assertFalse(out["resolved"])
        self.assertTrue(out.get("partial"))              # fell through to partial-signal

    def test_learned_miss_falls_through_to_fuzzy(self):
        # learned returns None -> normal fuzzy resolution still works (Multi Tranche parent).
        learned = _FakeLearned(None)
        r = resolve_mod.LoanResolver(client=_FakeClient(), learned=learned)
        out = r.resolve_loan("North Carolina II - Multi Tranche")
        self.assertTrue(out["resolved"])
        self.assertEqual(out.get("via"), None)     # fuzzy path, not learned
        self.assertEqual(out["match"]["id"], "141")
        # the learned store WAS consulted (then missed) — proves the wiring, not just the outcome.
        self.assertIn("North Carolina II - Multi Tranche", learned.calls)

    def test_no_learned_store_is_pure_fuzzy(self):
        r = resolve_mod.LoanResolver(client=_FakeClient())  # learned omitted
        out = r.resolve_loan("409 Hodson")
        # pure fuzzy still can't match "409 Hodson" by NAME -> partial-signal surfaces 144 instead
        self.assertFalse(out["resolved"])
        self.assertTrue(out.get("partial"))

    def test_learned_non_loan_entity_is_ignored(self):
        learned = _FakeLearned({"entity_type": "fundingEntity", "id": "3", "name": "XL"})
        r = resolve_mod.LoanResolver(client=_FakeClient(), learned=learned)
        out = r.resolve_loan("North Carolina II - Multi Tranche")
        self.assertEqual(out.get("via"), None)     # not routed via the non-loan learned entry
        self.assertEqual(out["match"]["id"], "141")

    def test_learned_empty_id_is_ignored(self):
        learned = _FakeLearned({"entity_type": "loan", "id": "", "name": "bad"})
        r = resolve_mod.LoanResolver(client=_FakeClient(), learned=learned)
        out = r.resolve_loan("North Carolina II - Multi Tranche")
        self.assertEqual(out.get("via"), None)
        self.assertTrue(out["resolved"])


# ---------------------------------------------------------------------------
# LAYER 3 (store) — entity_for_query exact + token-subset matching
# ---------------------------------------------------------------------------

class EntityForQueryTest(unittest.TestCase):
    def _store(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self._tmp.close()
        return learned_mod.LearnedStore(self._tmp.name, now="2026-07-01T00:00:00Z")

    def tearDown(self):
        try:
            os.unlink(self._tmp.name)
        except (OSError, AttributeError):
            pass

    def test_exact_match(self):
        s = self._store()
        s.record_entity_resolution("409 hodson", "loan", "144", "409 High Point")
        self.assertEqual(s.entity_for_query("409 Hodson")["id"], "144")

    def test_token_subset_fires_inside_longer_query(self):
        s = self._store()
        s.record_entity_resolution("409 hodson", "loan", "144", "409 High Point")
        got = s.entity_for_query("what is the payoff for 409 hodson in north carolina loan")
        self.assertIsNotNone(got)
        self.assertEqual(got["id"], "144")

    def test_incidental_single_token_does_not_fire(self):
        # alias {409, hodson}; query has "409" but NOT "hodson" -> must NOT match (avoids a lone
        # shared number triggering an unrelated alias).
        s = self._store()
        s.record_entity_resolution("409 hodson", "loan", "144", "409 High Point")
        self.assertIsNone(s.entity_for_query("409 high point something else"))

    def test_longest_alias_wins(self):
        s = self._store()
        s.record_entity_resolution("hodson", "loan", "100", "generic")
        s.record_entity_resolution("409 hodson", "loan", "144", "specific")
        got = s.entity_for_query("409 hodson north carolina")
        self.assertEqual(got["id"], "144")   # the 2-token alias beats the 1-token alias

    def test_no_alias_returns_none(self):
        s = self._store()
        self.assertIsNone(s.entity_for_query("beehive"))


# ---------------------------------------------------------------------------
# LAYER 1 — partial-signal surfacing
# ---------------------------------------------------------------------------

class PartialSignalTest(unittest.TestCase):
    def setUp(self):
        self.r = resolve_mod.LoanResolver(client=_FakeClient())

    def test_off_name_query_surfaces_number_match(self):
        out = self.r.resolve_loan("409 Hodson")
        self.assertFalse(out["resolved"])
        self.assertTrue(out["ambiguous"])
        self.assertTrue(out["partial"])
        ids = [c["id"] for c in out["candidates"]]
        self.assertIn("144", ids)
        top = out["candidates"][0]
        self.assertIn("409", top["matched_tokens"])

    def test_partial_never_auto_resolves(self):
        out = self.r.resolve_loan("409 Hodson")
        for c in out["candidates"]:
            self.assertLess(c["score"], resolve_mod.HIGH_CONFIDENCE)  # capped below auto-resolve

    def test_partial_score_is_hard_capped_at_ceiling(self):
        # Directly exercise the capping FORMULA: a query whose discriminators ALL match (frac=1.0)
        # plus the numeric bonus would compute 0.40 + 0.39 + 0.10 = 0.89 uncapped; the hard cap
        # must clamp it to 0.79 (< HIGH_CONFIDENCE 0.82) so a partial can never auto-resolve.
        rows = [{"id": "144", "name": "409 500", "status": "Active"}]
        out = self.r._partial_signal_candidates("409 500", rows)
        self.assertTrue(out)
        self.assertEqual(out[0]["score"], 0.79)
        self.assertLess(out[0]["score"], resolve_mod.HIGH_CONFIDENCE)

    def test_no_discriminator_overlap_is_clean_miss(self):
        out = self.r.resolve_loan("zzz qqq wwww")   # 3+ char tokens, but match no loan name
        self.assertFalse(out["resolved"])
        self.assertFalse(out["ambiguous"])
        self.assertEqual(out["candidates"], [])
        self.assertNotIn("partial", out)

    def test_full_name_match_still_wins_over_partial(self):
        # a real full-name query must resolve normally (partial only fires when nothing clears).
        out = self.r.resolve_loan("North Carolina II - 409 High Point")
        self.assertTrue(out["resolved"])
        self.assertEqual(out["match"]["id"], "144")


# ---------------------------------------------------------------------------
# LAYER 2 — native tranche drill-down (group_tree via parentLoan)
# ---------------------------------------------------------------------------

class GroupTreeTest(unittest.TestCase):
    def setUp(self):
        self.r = resolve_mod.LoanResolver(client=_FakeClient())

    def test_facility_name_returns_root_and_all_tranches(self):
        t = self.r.group_tree("North Carolina II")
        self.assertEqual(t["state"], "OK")
        self.assertTrue(t["is_multi_tranche"])
        self.assertEqual(t["root"]["id"], "141")
        self.assertEqual(t["via"], "parentLoan")
        ids = [x["id"] for x in t["tranches"]]
        for expect in ("141", "142", "143", "144", "145", "146"):
            self.assertIn(expect, ids)
        self.assertNotIn("999", ids)              # the unrelated standalone loan is excluded
        self.assertTrue(t["tranches"][0]["is_root"])   # root sorts first

    def test_seed_on_a_tranche_resolves_root_from_parentLoan(self):
        t = self.r.group_tree("409 High Point")
        self.assertEqual(t["root"]["id"], "141")   # climbed child -> parent
        self.assertIn("144", [x["id"] for x in t["tranches"]])

    def test_standalone_loan_is_single(self):
        t = self.r.group_tree("Standalone Bridge Loan")
        self.assertEqual(t["state"], "SINGLE")
        self.assertFalse(t["is_multi_tranche"])
        self.assertEqual(t["root"]["id"], "999")
        self.assertEqual(len(t["tranches"]), 1)

    def test_no_match_is_no_match(self):
        t = self.r.group_tree("nonexistent zzz facility")
        self.assertEqual(t["state"], "NO_MATCH")
        self.assertEqual(t["tranches"], [])
        self.assertIsNone(t["root"])

    def test_tranches_are_real_rows_only(self):
        # every tranche id must come from the fixture (never invented).
        t = self.r.group_tree("North Carolina II")
        known = {l["id"] for l in _NC_LOANS}
        for x in t["tranches"]:
            self.assertIn(x["id"], known)


if __name__ == "__main__":
    unittest.main(verbosity=2)
