#!/usr/bin/env python3
"""test_hca_entities.py — stdlib unittest for GENERALIZED entity-name resolution.

Proves the SAME NON-NEGOTIABLE resolution policy hca-resolve enforces, now for ANY
searchable entity (funding entities, clients, equities, loans), on FIXTURES (no network,
no creds) via a fake GraphQL client that serves MULTIPLE entity types through each one's
`<entity>(filter:{searchString})` RELIABLE list query:

  - EXACT match (fundingEntity "XL")  -> resolves, echoes the resolution.
  - AMBIGUOUS                          -> returns the candidate list, NEVER auto-picks.
  - NO MATCH                           -> empty candidates (clean miss; never invents a row).
  - CLIENT name field                  -> resolution reads `displayName` (not `name`).
  - candidates always come from the fake API rows (never fabricated).

The fake client routes on WHICH list_query the GraphQL string contains (loans /
fundingEntities / clients / equities) and honors the searchString substring filter — the
same way the real per-entity list queries behave.

Run:
  python3 .claude/scripts/tests/test_hca_entities.py
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


entities_mod = _load("hca_entities", "hca-entities.py")


# Synthetic portfolios per entity type (NO real PII — NAMES are reference data; ids are
# placeholders, except the verified-live fundingEntity "XL" -> id 3 from the brief).
_FUNDING_ENTITIES = [
    {"id": "3", "name": "XL"},
    {"id": "11", "name": "XL Capital Partners"},
    {"id": "20", "name": "Beehive Investors"},
    {"id": "21", "name": "Granite Capital"},
]

_CLIENTS = [
    {"id": "C-1", "displayName": "Acme Holdings LLC"},
    {"id": "C-2", "displayName": "Beehive Development Group"},
    {"id": "C-3", "displayName": "Sunset Partners"},
]

_EQUITIES = [
    {"id": "E-1", "name": "Maple Grove Equity"},
    {"id": "E-2", "name": "Granite Ridge Equity"},
]

_LOANS = [
    {"id": "134", "name": "Beehive Waldorff", "status": "ACTIVE"},
    {"id": "303", "name": "Maple Grove Senior", "status": "ACTIVE"},
    {"id": "304", "name": "Maple Grove Junior", "status": "ACTIVE"},
]


class _FakeClient:
    """A fake LiveGraphQLClient serving MULTIPLE entity types.

    raw_query routes on which list_query the GraphQL string contains and honors the
    searchString substring filter over the matching synthetic portfolio. Records the
    queries it received so we can assert which list query was used (never a single-entity
    `fundingEntity(id:...)` fetch).
    """

    # list_query name (as it appears in the GraphQL string) -> (portfolio, name field)
    _ROUTES = {
        "fundingEntities": (_FUNDING_ENTITIES, "name"),
        "clients": (_CLIENTS, "displayName"),
        "equities": (_EQUITIES, "name"),
        "loans": (_LOANS, "name"),
    }

    def __init__(self, overrides=None, fail_with=None):
        # overrides: {list_query_name: [rows]} to swap in a custom portfolio for a test.
        self._overrides = overrides or {}
        self.queries = []
        self.fail_with = fail_with  # an Exception to raise (transport-failure simulation)

    def _route(self, query: str):
        # Pick the route whose list_query field name appears as `<name>(` in the query.
        # Check longer names first so "loanFundings" can't shadow "loans" (not used here,
        # but keeps the router robust).
        for qname in sorted(self._ROUTES, key=len, reverse=True):
            if f"{qname}(" in query:
                rows, name_field = self._ROUTES[qname]
                rows = self._overrides.get(qname, rows)
                return qname, rows, name_field
        raise AssertionError(f"fake client got an unrouted query: {query!r}")

    def raw_query(self, query, variables=None):
        self.queries.append((query, variables))
        if self.fail_with is not None:
            raise self.fail_with
        qname, rows, name_field = self._route(query)
        variables = variables or {}
        filt = variables.get("filter") or {}
        ss = (filt.get("searchString") or "").strip().lower()
        if ss:
            matched = [r for r in rows if ss in str(r.get(name_field, "")).lower()]
        else:
            matched = list(rows)
        return {qname: {"totalFilteredRecords": len(matched), "pageItems": matched}}


class FundingEntityExactTest(unittest.TestCase):
    def setUp(self):
        self.client = _FakeClient()
        self.r = entities_mod.EntityResolver(client=self.client)

    def test_exact_funding_entity_resolves_and_echoes(self):
        # "XL" exactly matches the funding entity id 3 (verified live). "XL Capital Partners"
        # is a clean superset (query is a strict token-subset of it) but the EXACT match wins
        # the high-confidence single-match (score 1.0) with a clear gap -> resolves, no pick-ambiguity.
        res = self.r.resolve_entity("XL", "fundingEntity")
        self.assertTrue(res["resolved"], res.get("reason"))
        self.assertIsNotNone(res["match"])
        self.assertEqual(res["match"]["id"], "3")
        self.assertEqual(res["match"]["name"], "XL")
        self.assertIsNotNone(res["echo"])
        self.assertIn("XL", res["echo"])
        self.assertIn("3", res["echo"])

    def test_used_reliable_list_query_only(self):
        self.r.resolve_entity("XL", "fundingEntity")
        self.assertTrue(self.client.queries)
        for q, _v in self.client.queries:
            self.assertIn("fundingEntities(", q)
            # never a single-entity fundingEntity(id:...) fetch
            self.assertNotIn("fundingEntity(id", q.replace(" ", ""))

    def test_funding_entity_candidates_have_no_status_field(self):
        # status only exists on loans; other entity candidates must omit it.
        res = self.r.resolve_entity("XL", "fundingEntity")
        for c in res["candidates"]:
            self.assertNotIn("status", c)


class FundingEntityAmbiguousTest(unittest.TestCase):
    def test_ambiguous_returns_candidates_no_silent_pick(self):
        # Two funding entities share the distinctive "vector cove" name root with only a
        # trailing qualifier differing -> they tie at the top, so the resolver must NOT pick.
        client = _FakeClient(overrides={"fundingEntities": [
            {"id": "30", "name": "Vector Cove North"},
            {"id": "31", "name": "Vector Cove South"},
            {"id": "32", "name": "Granite Holdings"},
        ]})
        r = entities_mod.EntityResolver(client=client)
        res = r.resolve_entity("vector cove", "fundingEntity")
        self.assertFalse(res["resolved"])
        self.assertIsNone(res["match"])          # NEVER silently picks
        self.assertTrue(res["ambiguous"])
        # The two tied Vector Cove entities are the ambiguous top pair; the unrelated
        # "Granite Holdings" scores below the candidate floor and is excluded.
        ids = {c["id"] for c in res["candidates"]}
        self.assertEqual(ids, {"30", "31"})
        # top two within the ambiguity gap -> too close to call
        cands = res["candidates"]
        self.assertGreaterEqual(len(cands), 2)
        self.assertLess(cands[0]["score"] - cands[1]["score"], entities_mod.AMBIGUITY_GAP)
        # every candidate is a REAL fixture row (never fabricated)
        for c in cands:
            self.assertIn(c["id"], {"30", "31", "32"})


class NoMatchTest(unittest.TestCase):
    def test_no_match_returns_empty_candidates(self):
        client = _FakeClient()
        r = entities_mod.EntityResolver(client=client)
        res = r.resolve_entity("nonexistent zzz entity", "fundingEntity")
        self.assertFalse(res["resolved"])
        self.assertEqual(res["candidates"], [])
        self.assertIsNone(res["match"])
        self.assertFalse(res["ambiguous"])

    def test_empty_query_is_clean_miss(self):
        r = entities_mod.EntityResolver(client=_FakeClient())
        res = r.resolve_entity("   ", "fundingEntity")
        self.assertFalse(res["resolved"])
        self.assertEqual(res["candidates"], [])


class ClientDisplayNameTest(unittest.TestCase):
    """Clients name on `displayName`, not `name` — resolution must read the right field."""

    def setUp(self):
        self.client = _FakeClient()
        self.r = entities_mod.EntityResolver(client=self.client)

    def test_client_resolves_via_display_name(self):
        res = self.r.resolve_entity("Acme Holdings LLC", "client")
        self.assertTrue(res["resolved"], res.get("reason"))
        self.assertEqual(res["match"]["id"], "C-1")
        # The candidate's `name` is populated FROM displayName.
        self.assertEqual(res["match"]["name"], "Acme Holdings LLC")

    def test_client_query_uses_displayName_field(self):
        self.r.resolve_entity("Acme Holdings LLC", "client")
        self.assertTrue(self.client.queries)
        for q, _v in self.client.queries:
            self.assertIn("clients(", q)
            self.assertIn("displayName", q)   # selection reads displayName, not name

    def test_client_partial_resolves(self):
        res = self.r.resolve_entity("acme", "client")
        self.assertTrue(res["resolved"], res.get("reason"))
        self.assertEqual(res["match"]["id"], "C-1")


class EquityAndLoanTest(unittest.TestCase):
    def test_equity_resolves_via_name(self):
        r = entities_mod.EntityResolver(client=_FakeClient())
        res = r.resolve_entity("Granite Ridge Equity", "equity")
        self.assertTrue(res["resolved"], res.get("reason"))
        self.assertEqual(res["match"]["id"], "E-2")

    def test_loan_candidates_carry_status(self):
        # loans still resolve through this generalized resolver AND keep the status field.
        r = entities_mod.EntityResolver(client=_FakeClient())
        res = r.resolve_entity("Beehive Waldorff", "loan")
        self.assertTrue(res["resolved"], res.get("reason"))
        self.assertEqual(res["match"]["id"], "134")
        self.assertIn("status", res["match"])
        self.assertEqual(res["match"]["status"], "ACTIVE")


class CandidatesFromRealRowsTest(unittest.TestCase):
    def test_candidates_come_from_real_rows(self):
        r = entities_mod.EntityResolver(client=_FakeClient())
        res = r.resolve_entity("XL", "fundingEntity")
        real_ids = {e["id"] for e in _FUNDING_ENTITIES}
        real_names = {e["name"] for e in _FUNDING_ENTITIES}
        self.assertTrue(res["candidates"])
        for c in res["candidates"]:
            self.assertIn(c["id"], real_ids)
            self.assertIn(c["name"], real_names)


class FailureTest(unittest.TestCase):
    def test_live_failure_raises_resolve_error_never_fabricates(self):
        # Every retry attempt fails -> ResolveError (never invents rows).
        client = _FakeClient(fail_with=RuntimeError("GraphQL HTTP 500 Internal Server Error"))
        r = entities_mod.EntityResolver(client=client, retry_tries=4)
        with self.assertRaises(entities_mod.ResolveError):
            r.resolve_entity("XL", "fundingEntity")

    def test_retry_recovers_from_transient_500(self):
        # First two attempts 500, then succeed -> resolves without fabricating.
        client = _FlakyClient(fail_n=2)
        r = entities_mod.EntityResolver(client=client, retry_tries=5)
        res = r.resolve_entity("XL", "fundingEntity")
        self.assertTrue(res["resolved"], res.get("reason"))
        self.assertEqual(res["match"]["id"], "3")


class _FlakyClient(_FakeClient):
    """Fails the first `fail_n` raw_query calls with a 500, then behaves normally."""

    def __init__(self, fail_n=2, **kw):
        super().__init__(**kw)
        self._fail_n = fail_n
        self._calls = 0

    def raw_query(self, query, variables=None):
        self._calls += 1
        if self._calls <= self._fail_n:
            # record the attempt so query history is realistic, then fail
            self.queries.append((query, variables))
            raise RuntimeError("GraphQL HTTP 500 Internal Server Error")
        return super().raw_query(query, variables)


class NonResolvableTypeTest(unittest.TestCase):
    def test_loan_funding_is_rejected(self):
        # loanFunding has no human name -> not resolvable; raises ValueError (never guesses).
        r = entities_mod.EntityResolver(client=_FakeClient())
        with self.assertRaises(ValueError):
            r.resolve_entity("anything", "loanFunding")

    def test_unknown_type_is_rejected(self):
        r = entities_mod.EntityResolver(client=_FakeClient())
        with self.assertRaises(ValueError):
            r.resolve_entity("anything", "borrower")


class ModuleConvenienceTest(unittest.TestCase):
    def test_module_level_resolve_entity(self):
        res = entities_mod.resolve_entity("XL", "fundingEntity", client=_FakeClient())
        self.assertTrue(res["resolved"], res.get("reason"))
        self.assertEqual(res["match"]["id"], "3")


if __name__ == "__main__":
    unittest.main(verbosity=2)
