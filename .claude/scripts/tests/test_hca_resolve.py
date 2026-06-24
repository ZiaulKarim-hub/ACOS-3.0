#!/usr/bin/env python3
"""test_hca_resolve.py — stdlib unittest for fuzzy loan-name resolution (SLICE-HCA-12).

Proves the NON-NEGOTIABLE resolution policy on FIXTURES (no network, no creds), via a fake
GraphQL client that serves a synthetic loan list through the SAME `loans(filter:{searchString})`
RELIABLE query the live resolver uses:

  - EXACT match           -> resolves, echoes the resolution.
  - FUZZY single match    -> resolves a partial name ("beehive" -> "Beehive Waldorff") + echoes.
  - AMBIGUOUS             -> returns the candidate list, NEVER auto-picks (no `match`).
  - NO MATCH              -> empty candidates (clean miss; never invents a loan).
  - candidates always come from the fake API rows (never fabricated).

Run:
  python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py' -v
"""

import importlib.util
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


resolve_mod = _load("hca_resolve", "hca-resolve.py")


# Synthetic portfolio (NO real PII — loan NAMES are reference data; ids are placeholders).
_LOANS = [
    {"id": "134", "name": "Beehive Waldorff", "status": "ACTIVE"},
    {"id": "201", "name": "Sunset Plaza Bridge", "status": "ACTIVE"},
    {"id": "202", "name": "Granite Ridge Construction", "status": "CLOSED"},
    {"id": "303", "name": "Maple Grove Senior", "status": "ACTIVE"},
    {"id": "304", "name": "Maple Grove Junior", "status": "ACTIVE"},
]


class _FakeClient:
    """A fake LiveGraphQLClient: raw_query honors the searchString filter over _LOANS.

    Records the queries it received so we can assert the resolver used the reliable list
    query (and never tried `loan(id)` / a preview resolver).
    """

    def __init__(self, loans=None, fail_with=None):
        self.loans = loans if loans is not None else list(_LOANS)
        self.queries = []
        self.fail_with = fail_with  # an Exception to raise (transport-failure simulation)

    def raw_query(self, query, variables=None):
        self.queries.append((query, variables))
        if self.fail_with is not None:
            raise self.fail_with
        variables = variables or {}
        filt = variables.get("filter") or {}
        ss = (filt.get("searchString") or "").strip().lower()
        if ss:
            rows = [l for l in self.loans if ss in l["name"].lower()]
        else:
            rows = list(self.loans)
        return {"loans": {"totalFilteredRecords": len(rows), "pageItems": rows}}


class ScoringTest(unittest.TestCase):
    def test_exact_normalized_match_is_one(self):
        self.assertEqual(resolve_mod.score_name("Beehive Waldorff", "Beehive Waldorff"), 1.0)
        # case / punctuation insensitive
        self.assertEqual(resolve_mod.score_name("beehive  waldorff", "Beehive Waldorff"), 1.0)

    def test_clean_subset_partial_is_high_confidence(self):
        # a single distinctive token of a two-word name clears the high-confidence bar
        self.assertGreaterEqual(
            resolve_mod.score_name("beehive", "Beehive Waldorff"),
            resolve_mod.HIGH_CONFIDENCE)

    def test_unrelated_name_scores_low(self):
        self.assertLess(resolve_mod.score_name("beehive", "Granite Ridge Construction"),
                        resolve_mod.MIN_CANDIDATE_SCORE)


class ResolveExactTest(unittest.TestCase):
    def setUp(self):
        self.client = _FakeClient()
        self.r = resolve_mod.LoanResolver(client=self.client)

    def test_exact_match_resolves_and_echoes(self):
        res = self.r.resolve_loan("Beehive Waldorff")
        self.assertTrue(res["resolved"])
        self.assertIsNotNone(res["match"])
        self.assertEqual(res["match"]["id"], "134")
        self.assertEqual(res["match"]["name"], "Beehive Waldorff")
        # ECHO is recorded so the caller can surface it (policy: record the resolution)
        self.assertIsNotNone(res["echo"])
        self.assertIn("Beehive Waldorff", res["echo"])
        self.assertIn("134", res["echo"])

    def test_used_reliable_list_query_only(self):
        self.r.resolve_loan("Beehive Waldorff")
        # every query the resolver issued must be the loans LIST query (never loan(id))
        self.assertTrue(self.client.queries)
        for q, _v in self.client.queries:
            self.assertIn("loans(", q)
            self.assertNotIn("getLoanTransactionPreview", q)
            # not a single-entity loan(id:...) fetch
            self.assertNotIn("loan(id", q.replace(" ", ""))


class ResolveFuzzySingleTest(unittest.TestCase):
    def setUp(self):
        self.client = _FakeClient()
        self.r = resolve_mod.LoanResolver(client=self.client)

    def test_partial_name_resolves_with_echo(self):
        res = self.r.resolve_loan("beehive")
        self.assertTrue(res["resolved"], res.get("reason"))
        self.assertEqual(res["match"]["id"], "134")
        self.assertIn("matched", res["echo"])
        self.assertIn("'beehive'", res["echo"])
        self.assertIn("Beehive Waldorff", res["echo"])

    def test_fuzzy_full_name_with_noise_resolves(self):
        # full loan name with case + spacing noise resolves to the exact loan (fuzzy, single).
        res = self.r.resolve_loan("  BEEHIVE   waldorff ")
        self.assertTrue(res["resolved"], res.get("reason"))
        self.assertEqual(res["match"]["id"], "134")
        self.assertIn("Beehive Waldorff", res["echo"])

    def test_query_superset_of_short_name_resolves(self):
        # candidate name is a clean subset of the query (user adds a qualifier the name lacks),
        # and no other loan competes for the distinctive token -> single confident match.
        client = _FakeClient(loans=[
            {"id": "500", "name": "Beehive", "status": "ACTIVE"},
            {"id": "201", "name": "Sunset Plaza Bridge", "status": "ACTIVE"},
        ])
        r = resolve_mod.LoanResolver(client=client)
        res = r.resolve_loan("beehive senior")
        self.assertTrue(res["resolved"], res.get("reason"))
        self.assertEqual(res["match"]["id"], "500")

    def test_candidates_come_from_real_rows(self):
        res = self.r.resolve_loan("beehive")
        for c in res["candidates"]:
            self.assertIn(c["id"], {l["id"] for l in _LOANS})
            self.assertIn(c["name"], {l["name"] for l in _LOANS})


class ResolveAmbiguousTest(unittest.TestCase):
    def setUp(self):
        self.client = _FakeClient()
        self.r = resolve_mod.LoanResolver(client=self.client)

    def test_ambiguous_returns_candidates_no_silent_pick(self):
        # "maple grove" matches BOTH "Maple Grove Senior" and "Maple Grove Junior" — tied.
        res = self.r.resolve_loan("maple grove")
        self.assertFalse(res["resolved"])
        self.assertIsNone(res["match"])           # NEVER silently picks
        self.assertTrue(res["ambiguous"])
        ids = {c["id"] for c in res["candidates"]}
        self.assertEqual(ids, {"303", "304"})

    def test_ambiguous_top_two_within_gap(self):
        res = self.r.resolve_loan("maple grove")
        cands = res["candidates"]
        self.assertGreaterEqual(len(cands), 2)
        self.assertLess(cands[0]["score"] - cands[1]["score"], resolve_mod.AMBIGUITY_GAP)


class ResolveNoMatchTest(unittest.TestCase):
    def setUp(self):
        self.client = _FakeClient()
        self.r = resolve_mod.LoanResolver(client=self.client)

    def test_no_match_returns_empty_candidates(self):
        res = self.r.resolve_loan("nonexistent zzz loan")
        self.assertFalse(res["resolved"])
        self.assertEqual(res["candidates"], [])
        self.assertIsNone(res["match"])
        self.assertFalse(res["ambiguous"])

    def test_empty_query_is_clean_miss(self):
        res = self.r.resolve_loan("   ")
        self.assertFalse(res["resolved"])
        self.assertEqual(res["candidates"], [])


class ResolveFailureTest(unittest.TestCase):
    def test_live_failure_raises_resolve_error_never_fabricates(self):
        client = _FakeClient(fail_with=RuntimeError("GraphQL HTTP 500 Internal Server Error"))
        r = resolve_mod.LoanResolver(client=client)
        with self.assertRaises(resolve_mod.ResolveError):
            r.resolve_loan("beehive")


class SearchTokenBroadeningTest(unittest.TestCase):
    """Substance-preserving resolution retry: progressively broader searchStrings, all built ONLY
    from the user's own words (never invented), so a real loan is surfaced even when a strict
    server-side filter returns nothing."""

    def test_search_tokens_include_full_pair_singles_and_unfiltered(self):
        r = resolve_mod.LoanResolver(client=_FakeClient())
        variants = r._search_tokens("Beehive Waldorff Senior")
        self.assertEqual(variants[0], "beehive waldorff senior")   # full query first (specific)
        self.assertIsNone(variants[-1])                            # unfiltered fallback last
        self.assertIn("waldorff beehive", variants)                # two most-distinctive tokens
        for tok in ("waldorff", "beehive", "senior"):              # each token individually
            self.assertIn(tok, variants)
        # de-duped (None keyed as a sentinel)
        keys = [v if v is not None else "__ALL__" for v in variants]
        self.assertEqual(len(keys), len(set(keys)))

    def test_broadening_surfaces_candidate_a_strict_filter_would_miss(self):
        # Reversed word order: the full searchString "waldorff beehive" is NOT a substring of the
        # real name, so a single strict-filter fetch returns zero rows; token broadening + the
        # order-insensitive token-set score still surface (and resolve) the real loan.
        client = _FakeClient(loans=[{"id": "134", "name": "Beehive Waldorff", "status": "Active"}])
        r = resolve_mod.LoanResolver(client=client)
        res = r.resolve_loan("Waldorff Beehive")
        self.assertIn("134", [c["id"] for c in res["candidates"]])


if __name__ == "__main__":
    unittest.main(verbosity=2)
