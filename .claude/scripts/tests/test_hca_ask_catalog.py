#!/usr/bin/env python3
"""test_hca_ask_catalog.py — the CATALOG-GUIDED explorer wiring (OPTIONAL-1).

Two halves, all with INJECTED fakes (no live creds, no network):

  PART A — smart_ask wiring (hca-ask.py)
    The catalog-guided pass is tried FIRST in the explorer fallback and, when it yields a live
    value, wins with tier="catalog"; otherwise the blind keyword explorer runs unchanged. Proves:
      * a catalog hit beats the blind explorer (tier=catalog, meta.catalog_backed, blind NOT called);
      * an empty catalog lookup falls through to the blind explorer (tier=explorer);
      * catalog hits that fetch NOTHING live fall through to the blind explorer;
      * catalog_lookup=None preserves the exact base behavior (catalog never consulted);
      * the entity_type -> catalog-domain seam maps correctly (loan/fundingEntity/client).

  PART B — explore_paths (hca-explorer.py), the new additive fetch
    Proves the trust invariants of fetching a CURATED exact path:
      * returns the LIVE fetched value (NEVER the catalog's illustrative example), graded HIGH,
        with the gotcha + source=catalog + catalog_path attached;
      * figure-owned descriptors are NOT raw-fetched (the per-diem trap);
      * unsafe paths (depth>2 / list-index) are skipped;
      * a depth-1 nested path fetches via a nested selection;
      * a fuzzy entity caps every field at LOW;
      * an absent field is skipped (no fabrication); record None -> NO_MATCH;
      * an unknown entity_type / missing id REFUSES;
      * a flaky single-record 500 falls back to the list query and still fetches.
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


ask_mod = _load("hca_ask", "hca-ask.py")
explorer = _load("hca_explorer", "hca-explorer.py")


# ---------------------------------------------------------------------------
# Shared resolver-shaped helpers (mirror test_hca_ask.py)
# ---------------------------------------------------------------------------

def _resolved(eid, name, score=1.0):
    m = {"id": eid, "name": name, "score": score}
    return {"query": name, "match": m, "resolved": True, "ambiguous": False,
            "candidates": [m], "echo": f"matched -> {name} ({eid})", "reason": "single match"}


def _no_match(name):
    return {"query": name, "match": None, "resolved": False, "ambiguous": False,
            "candidates": [], "echo": None, "reason": "no match"}


def _refuse(q):
    return {"state": "REFUSED", "refusals": [{"reason_code": "UNMAPPABLE"}]}


def _fake_catalog(hits_by_domain):
    """A catalog `lookup(query, domain=..., top=...)` fake. Returns the canned hits for the asked
    domain and records the last call so a test can assert the entity->domain mapping."""
    captured = {}

    def lookup(query, *, domain=None, top=8):
        captured.update(query=query, domain=domain, top=top)
        return list(hits_by_domain.get(domain, []))

    return lookup, captured


class _FakeExplorer:
    """Fake explorer exposing BOTH methods. Records calls so a test can assert which path ran."""

    def __init__(self, *, paths_result=None, question_result=None):
        self._paths = paths_result
        self._question = question_result
        self.calls = []

    def explore_paths(self, entity_type, entity_id, fields, *,
                      name_hint=None, entity_fuzzy=False, fetched_at=None):
        self.calls.append(("paths", entity_type, entity_id, list(fields), name_hint))
        return self._paths or {"state": "NO_MATCH", "entity_type": entity_type,
                               "entity_id": entity_id, "graphql_type": None,
                               "keywords": [], "results": [], "notes": []}

    def explore_question(self, question, resolved_entity):
        self.calls.append(("question", question, resolved_entity))
        return self._question or {"state": "NO_MATCH", "entity_type": resolved_entity["entity_type"],
                                  "entity_id": resolved_entity["id"], "graphql_type": None,
                                  "keywords": [], "results": [], "notes": []}

    def ran(self, kind):
        return any(c[0] == kind for c in self.calls)


def _explored_paths_envelope(value="USD", gotcha=None):
    return {"state": "EXPLORED", "entity_type": "fundingEntity", "entity_id": "3",
            "graphql_type": "FundingEntity", "keywords": ["base currency"],
            "results": [{"field": "base currency", "value": value, "confidence": 0.85,
                         "confidence_label": "high", "source": "catalog",
                         "catalog_path": "baseCurrency", "gotcha": gotcha,
                         "provenance": {"operation": "fundingEntity",
                                        "json_field_path": "$.fundingEntity.baseCurrency"}}],
            "notes": ["best-effort (not a verified figure)"]}


def _blind_question_envelope():
    return {"state": "EXPLORED", "entity_type": "fundingEntity", "entity_id": "3",
            "graphql_type": "FundingEntity", "keywords": ["irr"],
            "results": [{"field": "currentAverageInterestRate", "value": 0.11, "confidence": 0.6,
                         "confidence_label": "medium",
                         "provenance": {"operation": "fundingEntity", "json_field_path": "$.x"}}],
            "notes": ["best-effort (not a verified figure)"]}


# A figure-LESS catalog hit (the kind explore_paths is allowed to raw-fetch).
_HIT_BASE_CURRENCY = {"domain": "funding_entity", "path": "baseCurrency", "kind": "str",
                      "name": "base currency", "synonyms": ["currency"], "example": "EUR",
                      "example_status": "ok", "figure": None, "gotchas": None}


# ---------------------------------------------------------------------------
# PART A — smart_ask wiring
# ---------------------------------------------------------------------------

class SmartAskCatalogWiringTest(unittest.TestCase):
    def _resolve_xl_as_fe(self, name, etype):
        return _resolved("3", "XL") if etype == "fundingEntity" and "xl" in name.lower() \
            else _no_match(name)

    def test_catalog_pass_wins_over_blind_explorer(self):
        lookup, _cap = _fake_catalog({"funding_entity": [_HIT_BASE_CURRENCY]})
        fake = _FakeExplorer(paths_result=_explored_paths_envelope(value="USD"),
                             question_result=_blind_question_envelope())
        out = ask_mod.smart_ask(
            "what is the base currency for XL?",
            deliver_ask=_refuse, resolve_loan=lambda n: _no_match(n),
            resolve_entity=self._resolve_xl_as_fe, run_funding=lambda *a, **k: None,
            explorer=fake, catalog_lookup=lookup)
        self.assertEqual(out["state"], "EXPLORED")
        self.assertEqual(out["tier"], "catalog")
        self.assertTrue(out["meta"]["catalog_backed"])
        self.assertTrue(out["meta"]["best_effort"])
        self.assertEqual(out["results"][0]["value"], "USD")
        # the catalog won outright -> the blind keyword explorer must NOT have been consulted.
        self.assertTrue(fake.ran("paths"))
        self.assertFalse(fake.ran("question"))

    def test_empty_catalog_falls_through_to_blind_explorer(self):
        lookup, _cap = _fake_catalog({})  # no hits for any domain
        fake = _FakeExplorer(question_result=_blind_question_envelope())
        out = ask_mod.smart_ask(
            "what is the irr for XL?",
            deliver_ask=_refuse, resolve_loan=lambda n: _no_match(n),
            resolve_entity=self._resolve_xl_as_fe, run_funding=lambda *a, **k: None,
            explorer=fake, catalog_lookup=lookup)
        self.assertEqual(out["state"], "EXPLORED")
        self.assertEqual(out["tier"], "explorer")     # blind path, not catalog
        self.assertFalse(fake.ran("paths"))           # empty hits -> explore_paths never reached
        self.assertTrue(fake.ran("question"))

    def test_catalog_hits_but_no_live_result_falls_through(self):
        # The catalog matches a phrase, but explore_paths fetches nothing (e.g. all figure-owned /
        # absent) -> NO_MATCH -> we must fall through to the blind explorer, not dead-end.
        lookup, _cap = _fake_catalog({"funding_entity": [_HIT_BASE_CURRENCY]})
        fake = _FakeExplorer(
            paths_result={"state": "NO_MATCH", "results": [], "notes": [], "keywords": []},
            question_result=_blind_question_envelope())
        out = ask_mod.smart_ask(
            "what is the base currency for XL?",
            deliver_ask=_refuse, resolve_loan=lambda n: _no_match(n),
            resolve_entity=self._resolve_xl_as_fe, run_funding=lambda *a, **k: None,
            explorer=fake, catalog_lookup=lookup)
        self.assertEqual(out["tier"], "explorer")
        self.assertTrue(fake.ran("paths"))
        self.assertTrue(fake.ran("question"))

    def test_catalog_lookup_none_preserves_base_behavior(self):
        # Default OFF: with no catalog_lookup the catalog is NEVER consulted (explore_paths unused).
        fake = _FakeExplorer(paths_result=_explored_paths_envelope(),
                             question_result=_blind_question_envelope())
        out = ask_mod.smart_ask(
            "what is the irr for XL?",
            deliver_ask=_refuse, resolve_loan=lambda n: _no_match(n),
            resolve_entity=self._resolve_xl_as_fe, run_funding=lambda *a, **k: None,
            explorer=fake)  # catalog_lookup omitted
        self.assertEqual(out["tier"], "explorer")
        self.assertFalse(fake.ran("paths"))
        self.assertTrue(fake.ran("question"))

    def test_domain_seam_fundingentity(self):
        lookup, cap = _fake_catalog({"funding_entity": [_HIT_BASE_CURRENCY]})
        fake = _FakeExplorer(paths_result=_explored_paths_envelope())
        ask_mod.smart_ask(
            "base currency for XL", deliver_ask=_refuse, resolve_loan=lambda n: _no_match(n),
            resolve_entity=self._resolve_xl_as_fe, run_funding=lambda *a, **k: None,
            explorer=fake, catalog_lookup=lookup)
        self.assertEqual(cap["domain"], "funding_entity")
        # the FULL lookup interface is exercised: the question text + the default top are passed.
        self.assertEqual(cap["query"], "base currency for XL")
        self.assertEqual(cap["top"], 6)

    def test_catalog_explore_propagates_fuzzy_flag(self):
        # The fuzzy signal on the resolved entity must flow through _catalog_explore into
        # explore_paths(entity_fuzzy=...), so a fuzzily-resolved entity caps results at LOW.
        # (smart_ask doesn't currently mark entities fuzzy — this LOCKS the wiring contract so a
        # future entity that IS fuzzy can never silently fetch at HIGH confidence.)
        captured = {}

        class _Recorder:
            def explore_paths(self, et, eid, fields, *, name_hint=None,
                              entity_fuzzy=False, fetched_at=None):
                captured["fuzzy"] = entity_fuzzy
                return {"state": "EXPLORED", "keywords": [],
                        "results": [{"field": "x", "value": 1, "confidence": 0.35,
                                     "confidence_label": "low", "provenance": {}}],
                        "notes": []}

        lookup, _cap = _fake_catalog({"funding_entity": [_HIT_BASE_CURRENCY]})
        entity = {"entity_type": "fundingEntity", "id": "3", "name": "XL", "fuzzy": True}
        env = ask_mod._catalog_explore("base currency for XL", entity,
                                       catalog_lookup=lookup, explorer=_Recorder())
        self.assertTrue(captured["fuzzy"])
        self.assertEqual(env["tier"], "catalog")

    def test_domain_seam_loan(self):
        lookup, cap = _fake_catalog({"loan": [{"path": "annualInterestRate", "name": "rate",
                                               "figure": None, "example": 9, "gotchas": "x"}]})
        fake = _FakeExplorer(paths_result={"state": "EXPLORED", "entity_type": "loan",
                                           "entity_id": "134", "graphql_type": "Loan",
                                           "keywords": ["rate"],
                                           "results": [{"field": "rate", "value": 15,
                                                        "confidence": 0.85,
                                                        "confidence_label": "high",
                                                        "provenance": {}}],
                                           "notes": []})
        out = ask_mod.smart_ask(
            "interest rate for Beehive",
            deliver_ask=_refuse,
            resolve_loan=lambda n: _resolved("134", "Beehive") if "beehive" in n.lower()
            else _no_match(n),
            resolve_entity=lambda n, t: _no_match(n), run_funding=lambda *a, **k: None,
            explorer=fake, catalog_lookup=lookup)
        self.assertEqual(cap["domain"], "loan")
        self.assertEqual(out["tier"], "catalog")

    def test_domain_seam_client_maps_to_borrower(self):
        lookup, cap = _fake_catalog({"borrower": [{"path": "companyName", "name": "company name",
                                                   "figure": None, "example": "Acme",
                                                   "gotchas": None}]})
        fake = _FakeExplorer(paths_result={"state": "EXPLORED", "entity_type": "client",
                                           "entity_id": "C-1", "graphql_type": "Client",
                                           "keywords": ["company name"],
                                           "results": [{"field": "company name", "value": "Beehive LLC",
                                                        "confidence": 0.85,
                                                        "confidence_label": "high",
                                                        "provenance": {}}],
                                           "notes": []})
        ask_mod.smart_ask(
            "company name for Beehive borrower",
            deliver_ask=_refuse, resolve_loan=lambda n: _no_match(n),
            resolve_entity=lambda n, t: _resolved("C-1", "Beehive Borrower")
            if t == "client" else _no_match(n),
            run_funding=lambda *a, **k: None, explorer=fake, catalog_lookup=lookup)
        self.assertEqual(cap["domain"], "borrower")

    def test_corrupt_catalog_index_degrades_to_blind(self):
        # A lookup that raises (missing/corrupt index) must NOT crash smart_ask — it degrades.
        def boom(query, *, domain=None, top=8):
            raise FileNotFoundError("catalog-index.json missing")

        fake = _FakeExplorer(question_result=_blind_question_envelope())
        out = ask_mod.smart_ask(
            "what is the irr for XL?", deliver_ask=_refuse, resolve_loan=lambda n: _no_match(n),
            resolve_entity=self._resolve_xl_as_fe, run_funding=lambda *a, **k: None,
            explorer=fake, catalog_lookup=boom)
        self.assertEqual(out["tier"], "explorer")
        self.assertTrue(fake.ran("question"))


# ---------------------------------------------------------------------------
# PART B — explore_paths (real EntityExplorer + fake fetch client)
# ---------------------------------------------------------------------------

class _Http500(RuntimeError):
    """Carries '500' so hca-figures._is_http_500 classifies it retryable (-> list fallback)."""
    def __init__(self):
        super().__init__("GraphQL HTTP 500 Internal Server Error")


_UNSET = object()


class _FakeFetchClient:
    """Answers the single-record-by-id fetch (and the list-query fallback) for one entity family.

    explore_paths does NOT introspect, so no `__type` query is expected. `record` may be nested
    (for depth-1 path tests). Pass record=None to simulate "no such row". `single_fail_always`
    forces the single query to 500 so the list fallback is exercised.
    """

    def __init__(self, *, single_query, list_query, record=_UNSET, single_fail_always=False):
        self._sq = single_query
        self._lq = list_query
        self._record = {"id": "L-1"} if record is _UNSET else record
        self._fail = single_fail_always
        self.calls = []

    def raw_query(self, query, variables=None):
        self.calls.append((query, variables))
        flat = query.replace(" ", "")
        if f"{self._sq}(id:" in flat:
            if self._fail:
                raise _Http500()
            return {self._sq: (dict(self._record) if self._record is not None else None)}
        if f"{self._lq}(" in flat:
            items = [dict(self._record)] if self._record is not None else []
            return {self._lq: {"totalFilteredRecords": len(items), "pageItems": items}}
        return {}


def _no_sleep(_):
    return None


def _loan_explorer(record=_UNSET, single_fail_always=False):
    client = _FakeFetchClient(single_query="loan", list_query="loans",
                              record=record, single_fail_always=single_fail_always)
    return explorer.EntityExplorer(client=client, sleep=_no_sleep), client


_RATE_DESC = {"path": "annualInterestRate", "kind": "float", "name": "annual interest rate",
              "synonyms": ["interest rate"], "example": 99.0, "example_status": "ok",
              "figure": None, "gotchas": "PERCENT not fraction (example 15 = 15%)"}


class ExplorePathsTest(unittest.TestCase):
    def test_returns_live_value_not_example_high_conf_with_gotcha(self):
        ex, client = _loan_explorer(record={"id": "L-1", "annualInterestRate": 15})
        res = ex.explore_paths("loan", "L-1", [_RATE_DESC], name_hint="Beehive")
        self.assertEqual(res["state"], "EXPLORED")
        self.assertEqual(len(res["results"]), 1)
        r = res["results"][0]
        self.assertEqual(r["value"], 15)            # the LIVE value
        self.assertNotEqual(r["value"], 99.0)       # NOT the catalog example
        self.assertEqual(r["confidence_label"], "high")
        self.assertEqual(r["source"], "catalog")
        self.assertEqual(r["catalog_path"], "annualInterestRate")
        self.assertIn("PERCENT", r["gotcha"])
        self.assertEqual(r["provenance"]["operation"], "loan")

    def test_figure_owned_field_is_not_raw_fetched(self):
        owned = dict(_RATE_DESC); owned["figure"] = "per_diem_interest"
        ex, client = _loan_explorer(record={"id": "L-1", "annualInterestRate": 15})
        res = ex.explore_paths("loan", "L-1", [owned], name_hint="Beehive")
        self.assertEqual(res["state"], "NO_MATCH")
        self.assertEqual(res["results"], [])
        self.assertTrue(any("verified figure" in n for n in res["notes"]))
        # nothing was fetched (we skipped before issuing a query).
        self.assertEqual(client.calls, [])

    def test_unsafe_path_is_skipped(self):
        deep = {"path": "repaymentSchedule.scheduleTable.due", "name": "per diem",
                "figure": None, "example": 1, "gotchas": None}          # depth 3 -> unsafe
        ex, client = _loan_explorer(record={"id": "L-1"})
        res = ex.explore_paths("loan", "L-1", [deep])
        self.assertEqual(res["state"], "NO_MATCH")
        self.assertTrue(any("not safely fetchable" in n for n in res["notes"]))
        self.assertEqual(client.calls, [])

    def test_depth1_nested_path_fetched(self):
        nested = {"path": "totalOutstanding.principal", "name": "outstanding principal",
                  "figure": None, "example": 0.0, "gotchas": "use .principal for interest basis"}
        ex, client = _loan_explorer(
            record={"id": "L-1", "totalOutstanding": {"principal": 6922294.60}})
        res = ex.explore_paths("loan", "L-1", [nested], name_hint="Beehive")
        self.assertEqual(res["state"], "EXPLORED")
        self.assertEqual(res["results"][0]["value"], 6922294.60)
        self.assertEqual(res["results"][0]["catalog_path"], "totalOutstanding.principal")
        # the nested selection path is pinned into the provenance citation pointer
        self.assertEqual(res["results"][0]["provenance"]["json_field_path"],
                         "$.loan.totalOutstanding.principal")

    def test_fuzzy_entity_caps_low(self):
        ex, client = _loan_explorer(record={"id": "L-1", "annualInterestRate": 15})
        res = ex.explore_paths("loan", "L-1", [_RATE_DESC], entity_fuzzy=True)
        self.assertEqual(res["results"][0]["confidence_label"], "low")

    def test_absent_field_skipped_no_fabrication(self):
        # The field is requested but the record doesn't carry it -> skipped, never invented.
        ex, client = _loan_explorer(record={"id": "L-1"})  # no annualInterestRate key
        res = ex.explore_paths("loan", "L-1", [_RATE_DESC])
        self.assertEqual(res["state"], "NO_MATCH")
        self.assertEqual(res["results"], [])

    def test_partial_fields_present_some_absent_returns_subset(self):
        # A realistic lookup returns several candidate paths; the record carries SOME but not all.
        # explore_paths must return exactly the present subset (never all-or-nothing, never a null
        # row for the absent one).
        descs = [
            {"path": "annualInterestRate", "name": "rate", "figure": None, "example": 0, "gotchas": None},
            {"path": "baseCurrency", "name": "currency", "figure": None, "example": "x", "gotchas": None},
            {"path": "notOnRecord", "name": "ghost", "figure": None, "example": 0, "gotchas": None},
        ]
        ex, client = _loan_explorer(record={"id": "L-1", "annualInterestRate": 15, "baseCurrency": "USD"})
        res = ex.explore_paths("loan", "L-1", descs, name_hint="Beehive")
        self.assertEqual(res["state"], "EXPLORED")
        self.assertEqual({r["field"] for r in res["results"]}, {"rate", "currency"})
        self.assertEqual(len(res["results"]), 2)   # the absent path is skipped, not a null row

    def test_null_field_reported_as_is(self):
        ex, client = _loan_explorer(record={"id": "L-1", "annualInterestRate": None})
        res = ex.explore_paths("loan", "L-1", [_RATE_DESC])
        self.assertEqual(res["state"], "EXPLORED")
        self.assertIsNone(res["results"][0]["value"])
        self.assertIn("null", res["results"][0]["note"])

    def test_unknown_entity_type_refused(self):
        ex, client = _loan_explorer()
        res = ex.explore_paths("unicorn", "X-1", [_RATE_DESC])
        self.assertEqual(res["state"], "REFUSED")

    def test_missing_entity_id_refused(self):
        ex, client = _loan_explorer()
        res = ex.explore_paths("loan", "", [_RATE_DESC])
        self.assertEqual(res["state"], "REFUSED")

    def test_no_record_returns_no_match(self):
        ex, client = _loan_explorer(record=None)  # single null + empty list page
        res = ex.explore_paths("loan", "L-1", [_RATE_DESC], name_hint="Nope")
        self.assertEqual(res["state"], "NO_MATCH")
        self.assertEqual(res["results"], [])

    def test_single_500_falls_back_to_list_query(self):
        ex, client = _loan_explorer(record={"id": "L-1", "annualInterestRate": 15},
                                    single_fail_always=True)
        res = ex.explore_paths("loan", "L-1", [_RATE_DESC], name_hint="Beehive")
        self.assertEqual(res["state"], "EXPLORED")
        self.assertEqual(res["results"][0]["value"], 15)
        self.assertEqual(res["results"][0]["provenance"]["operation"], "loans")  # list fallback
        # the list-fallback prefix ($.<list>.pageItems) is pinned, distinct from the single path
        self.assertEqual(res["results"][0]["provenance"]["json_field_path"],
                         "$.loans.pageItems.annualInterestRate")
        self.assertTrue(any("list query" in n for n in res["notes"]))

    def test_empty_fields_list_no_match(self):
        ex, client = _loan_explorer(record={"id": "L-1", "annualInterestRate": 15})
        res = ex.explore_paths("loan", "L-1", [])
        self.assertEqual(res["state"], "NO_MATCH")
        self.assertEqual(client.calls, [])

    # --- regression pins from the OPTIONAL-1 adversarial verification (ship_with_fixes) ----------

    def test_provenance_json_path_and_fetched_at_roundtrip(self):
        # The cache-citation pointer (json_field_path) and the staleness stamp (fetched_at) are the
        # load-bearing provenance fields for OKOA financial data, yet only provenance.operation was
        # pinned before — a regression in json_path_prefix or the selection-path join would have
        # passed every other test. Pin the exact single-query pointer + the fetched_at round-trip.
        ex, client = _loan_explorer(record={"id": "L-1", "annualInterestRate": 15})
        res = ex.explore_paths("loan", "L-1", [_RATE_DESC], name_hint="Beehive",
                               fetched_at="2026-06-26T12:00:00Z")
        prov = res["results"][0]["provenance"]
        self.assertEqual(prov["operation"], "loan")
        self.assertEqual(prov["json_field_path"], "$.loan.annualInterestRate")
        self.assertEqual(prov["fetched_at"], "2026-06-26T12:00:00Z")

    def test_list_index_and_non_identifier_paths_skipped(self):
        # These paths are depth<=2 (so they PASS the depth gate) but carry a non-identifier segment,
        # so the _IDENT_RE guard must reject them. test_unsafe_path_is_skipped uses a depth-3 path,
        # rejected by the depth gate BEFORE _IDENT_RE runs — so without this the identifier guard is
        # never exercised, leaving a future _IDENT_RE refactor unguarded.
        for bad in ("items[0]", "totalOutstanding.0"):
            ex, client = _loan_explorer(
                record={"id": "L-1", "items": [1], "totalOutstanding": {"0": 9}})
            res = ex.explore_paths("loan", "L-1", [{"path": bad, "name": "bad", "figure": None,
                                                    "example": 0, "gotchas": None}])
            self.assertEqual(res["state"], "NO_MATCH", bad)
            self.assertEqual(client.calls, [], bad)            # rejected before any query is issued
            self.assertTrue(any("not safely fetchable" in n for n in res["notes"]), bad)

    def test_safe_selection_path_unit(self):
        # Direct unit pin of the path-safety gate (depth <= 2 AND every segment a plain identifier).
        sp = explorer._safe_selection_path
        self.assertEqual(sp("annualInterestRate"), ["annualInterestRate"])
        self.assertEqual(sp("totalOutstanding.principal"), ["totalOutstanding", "principal"])
        self.assertIsNone(sp("a.b.c"))               # depth-3 -> rejected by the depth gate
        self.assertIsNone(sp("items[0]"))            # list-index -> rejected by the identifier check
        self.assertIsNone(sp("totalOutstanding.0"))  # numeric segment -> rejected
        self.assertIsNone(sp(""))                    # empty
        self.assertIsNone(sp(None))                  # None


if __name__ == "__main__":
    unittest.main(verbosity=2)
