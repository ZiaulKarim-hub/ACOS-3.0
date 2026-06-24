#!/usr/bin/env python3
"""test_hca_explorer.py — stdlib unittest for the CONFIDENCE-GRADED EXPLORER FALLBACK
(hca-explorer.py).

Proves on FIXTURES (no network, no creds) — via a FAKE GraphQL client that answers (a) the
`__type` introspection for a small fake FundingEntity type with a few scalar fields, and (b)
the single_query field-fetch returning real values — that the explorer:

  HAPPY PATH
    - keyword "commitment" matches the scalar field `totalCommitment` at HIGH confidence and
      returns its ACTUAL fetched value with provenance (operation + json_field_path + the
      caller-supplied fetched_at).
    - camelCase is tokenized so "loans" matches `activeLoansCount` at HIGH.
    - difflib fuzzy: the typo "disbursment" matches `totalDisbursement` at MEDIUM (>= 0.6),
      not HIGH (not a substring).

  NEVER-FABRICATE (REQUIRED — fail = REJECT)
    - a keyword matching NOTHING -> EMPTY results, state NO_MATCH (no invented field/value).
    - nested OBJECT fields are NOT auto-traversed (only scalars are explored/fetched).
    - a matched field that comes back null is reported value=None (reported as-is, not faked).

  CONFIDENCE POLICY
    - HIGH = exact/substring field-name match on a firmly resolved entity.
    - MEDIUM = fuzzy field-name match.
    - LOW = the entity itself was only fuzzily resolved (entity_fuzzy=True caps all fields).

  FALLBACK
    - when the single_query 500s, the explorer falls back to the list_query (name_hint filter)
      and picks the row matching the id; provenance reflects the list path.

  HIGHER-LEVEL HELPER
    - explore_question() extracts keywords from a free-text question (stopwords dropped) and
      routes to explore() with the resolved entity.

Run:
  python3 .claude/scripts/tests/test_hca_explorer.py
  (or)  python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py' -v
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


explorer = _load("hca_explorer", "hca-explorer.py")


# ---------------------------------------------------------------------------
# A fake FundingEntity type's introspection result (scalar fields + one nested object).
# Mirrors the shape Hypercore's `__type(name:"FundingEntity"){ fields{...} }` returns.
# ---------------------------------------------------------------------------

def _scalar(name):
    return {"name": name, "kind": "SCALAR", "ofType": None}


# FundingEntity: three scalar fields the explorer should keep + one nested OBJECT it must skip
# + one LIST scalar it must skip (bounded-query discipline).
_FAKE_FUNDING_ENTITY_FIELDS = [
    {"name": "id", "type": {"name": "ID", "kind": "SCALAR", "ofType": None}},
    {"name": "name", "type": {"name": "String", "kind": "SCALAR", "ofType": None}},
    {"name": "totalCommitment", "type": {"name": "Float", "kind": "SCALAR", "ofType": None}},
    {"name": "totalDisbursement", "type": {"name": "Float", "kind": "SCALAR", "ofType": None}},
    {"name": "activeLoansCount", "type": {"name": "Int", "kind": "SCALAR", "ofType": None}},
    # nested OBJECT field — MUST be excluded (no auto-traversal of nested graphs):
    {"name": "summary", "type": {"name": "FundingSummary", "kind": "OBJECT", "ofType": None}},
    # LIST-of-scalar field — MUST be excluded (bounded-query discipline):
    {"name": "tags", "type": {"name": None, "kind": "LIST",
                              "ofType": {"name": "String", "kind": "SCALAR", "ofType": None}}},
]

# The actual values the single_query returns for funding entity "FE-1".
_FAKE_FE_RECORD = {
    "id": "FE-1",
    "name": "Beehive Fund I",
    "totalCommitment": 125000000.0,
    "totalDisbursement": 98000000.0,
    "activeLoansCount": 17,
}


class _Http500(RuntimeError):
    """Looks like the flaky 5xx (message carries '500') so _is_http_500 classifies it retryable."""
    def __init__(self):
        super().__init__("GraphQL HTTP 500 Internal Server Error")


_UNSET = object()  # sentinel: "record arg not passed" vs an explicit record=None (no row)


class _FakeClient:
    """Fake LiveGraphQLClient: answers the __type introspection + the single/list field fetch.

    Records every (query, variables) call so tests can assert what was sent. Can simulate the
    single_query failing N times with HTTP 500 (to exercise the list-query fallback / retry).
    `record` overrides the returned single-record; pass record=None explicitly to simulate
    "no such row" (the single query returns null AND the list page is empty).
    """

    def __init__(self, *, fields=None, record=_UNSET,
                 single_fail_times=0, single_fail_always=False):
        self._fields = fields if fields is not None else _FAKE_FUNDING_ENTITY_FIELDS
        self._record = dict(_FAKE_FE_RECORD) if record is _UNSET else record
        self._single_fail_times = single_fail_times
        self._single_fail_always = single_fail_always
        self._single_attempts = 0
        self.calls = []

    def raw_query(self, query, variables=None):
        self.calls.append((query, variables))
        if "__type" in query:
            return {"__type": {"fields": list(self._fields)}}
        # Single-record query: `fundingEntity(id: $id){ ... }`
        if "fundingEntity(id:" in query.replace(" ", ""):
            self._single_attempts += 1
            if self._single_fail_always or self._single_attempts <= self._single_fail_times:
                raise _Http500()
            return {"fundingEntity": (dict(self._record) if self._record is not None else None)}
        # List-query fallback: `fundingEntities(filter:...){ totalFilteredRecords pageItems{...} }`
        if "fundingEntities(" in query.replace(" ", ""):
            items = [dict(self._record)] if self._record is not None else []
            return {"fundingEntities": {"totalFilteredRecords": len(items), "pageItems": items}}
        return {}


def _no_sleep(_):
    return None


def _make_explorer(client):
    return explorer.EntityExplorer(client=client, sleep=_no_sleep)


# ---------------------------------------------------------------------------
# Tokenizer / keyword unit tests
# ---------------------------------------------------------------------------

class TokenizeTest(unittest.TestCase):
    def test_camelcase_split(self):
        self.assertEqual(explorer.tokenize_identifier("totalCommitment"),
                         ["total", "commitment"])
        self.assertEqual(explorer.tokenize_identifier("activeLoansCount"),
                         ["active", "loans", "count"])

    def test_acronym_and_snake(self):
        self.assertEqual(explorer.tokenize_identifier("refId"), ["ref", "id"])
        self.assertEqual(explorer.tokenize_identifier("annual_interest_rate"),
                         ["annual", "interest", "rate"])

    def test_extract_keywords_drops_stopwords(self):
        kws = explorer.extract_keywords("What is the total commitment for this fund?")
        # stopwords (what/is/the/for/this) + the soft-stopword 'total' are dropped; 'commitment'
        # and 'fund' survive.
        self.assertIn("commitment", kws)
        self.assertIn("fund", kws)
        self.assertNotIn("the", kws)
        self.assertNotIn("is", kws)


# ---------------------------------------------------------------------------
# score_field policy unit tests
# ---------------------------------------------------------------------------

class ScoreFieldTest(unittest.TestCase):
    def test_exact_token_is_high(self):
        label, conf, mk = explorer.score_field("totalCommitment", ["commitment"])
        self.assertEqual(label, explorer.LABEL_HIGH)
        self.assertEqual(conf, explorer.CONFIDENCE_HIGH)
        self.assertEqual(mk, "commitment")

    def test_camelcase_token_match_is_high(self):
        # "loans" matches the middle token of activeLoansCount only because we tokenize camelCase.
        label, conf, _ = explorer.score_field("activeLoansCount", ["loans"])
        self.assertEqual(label, explorer.LABEL_HIGH)

    def test_fuzzy_typo_is_medium(self):
        # "disbursment" (typo) is NOT a substring of totalDisbursement, but difflib ratio ~0.96.
        label, conf, mk = explorer.score_field("totalDisbursement", ["disbursment"])
        self.assertEqual(label, explorer.LABEL_MEDIUM)
        self.assertEqual(conf, explorer.CONFIDENCE_MEDIUM)
        self.assertEqual(mk, "disbursment")

    def test_no_match_returns_none(self):
        label, conf, mk = explorer.score_field("totalCommitment", ["zebra"])
        self.assertIsNone(label)
        self.assertEqual(conf, 0.0)
        self.assertIsNone(mk)


# ---------------------------------------------------------------------------
# Scalar-only introspection filtering
# ---------------------------------------------------------------------------

class IntrospectScalarFilterTest(unittest.TestCase):
    def test_only_scalars_kept_no_nested_traversal(self):
        client = _FakeClient()
        ex = _make_explorer(client)
        scalars = ex.introspect_type("FundingEntity")
        names = {s["name"] for s in scalars}
        # scalars kept:
        self.assertIn("totalCommitment", names)
        self.assertIn("totalDisbursement", names)
        self.assertIn("activeLoansCount", names)
        self.assertIn("id", names)
        self.assertIn("name", names)
        # nested OBJECT + LIST excluded (no auto-traversal of nested graphs):
        self.assertNotIn("summary", names)
        self.assertNotIn("tags", names)

    def test_introspection_cached_in_process(self):
        client = _FakeClient()
        ex = _make_explorer(client)
        ex.introspect_type("FundingEntity")
        first_call_count = sum(1 for q, _ in client.calls if "__type" in q)
        ex.introspect_type("FundingEntity")  # second call should hit the cache
        second_call_count = sum(1 for q, _ in client.calls if "__type" in q)
        self.assertEqual(first_call_count, 1)
        self.assertEqual(second_call_count, 1)  # unchanged -> cache hit


# ---------------------------------------------------------------------------
# explore() — the core behavior
# ---------------------------------------------------------------------------

class ExploreHappyPathTest(unittest.TestCase):
    def test_commitment_keyword_high_with_value_and_provenance(self):
        client = _FakeClient()
        ex = _make_explorer(client)
        res = ex.explore("fundingEntity", "FE-1", ["commitment"],
                         fetched_at="2026-06-24T00:00:00Z")
        self.assertEqual(res["state"], explorer.STATE_EXPLORED)
        self.assertEqual(res["graphql_type"], "FundingEntity")
        # exactly one field matched: totalCommitment
        fields = [r["field"] for r in res["results"]]
        self.assertIn("totalCommitment", fields)
        top = next(r for r in res["results"] if r["field"] == "totalCommitment")
        # HIGH confidence
        self.assertEqual(top["confidence_label"], explorer.LABEL_HIGH)
        self.assertEqual(top["confidence"], explorer.CONFIDENCE_HIGH)
        # ACTUAL fetched value returned (not fabricated, not a guess)
        self.assertEqual(top["value"], 125000000.0)
        self.assertEqual(top["graphql_type"], "Float")
        # provenance: operation + json_field_path + fetched_at
        prov = top["provenance"]
        self.assertEqual(prov["operation"], "fundingEntity")
        self.assertEqual(prov["json_field_path"], "$.fundingEntity.totalCommitment")
        self.assertEqual(prov["fetched_at"], "2026-06-24T00:00:00Z")
        # best-effort banner present
        self.assertIn(explorer.BEST_EFFORT_NOTE, res["notes"])

    def test_camelcase_loans_keyword_matches_active_loans_count(self):
        client = _FakeClient()
        ex = _make_explorer(client)
        res = ex.explore("fundingEntity", "FE-1", ["loans"])
        self.assertEqual(res["state"], explorer.STATE_EXPLORED)
        fields = {r["field"]: r for r in res["results"]}
        self.assertIn("activeLoansCount", fields)
        self.assertEqual(fields["activeLoansCount"]["confidence_label"], explorer.LABEL_HIGH)
        self.assertEqual(fields["activeLoansCount"]["value"], 17)

    def test_fuzzy_keyword_medium(self):
        client = _FakeClient()
        ex = _make_explorer(client)
        res = ex.explore("fundingEntity", "FE-1", ["disbursment"])  # typo
        self.assertEqual(res["state"], explorer.STATE_EXPLORED)
        fields = {r["field"]: r for r in res["results"]}
        self.assertIn("totalDisbursement", fields)
        self.assertEqual(fields["totalDisbursement"]["confidence_label"], explorer.LABEL_MEDIUM)
        self.assertEqual(fields["totalDisbursement"]["value"], 98000000.0)

    def test_results_sorted_by_confidence_desc(self):
        client = _FakeClient()
        ex = _make_explorer(client)
        # "commitment" -> HIGH (totalCommitment); "disbursment" -> MEDIUM (totalDisbursement)
        res = ex.explore("fundingEntity", "FE-1", ["commitment", "disbursment"])
        labels = [r["confidence_label"] for r in res["results"]]
        confs = [r["confidence"] for r in res["results"]]
        self.assertEqual(confs, sorted(confs, reverse=True))
        self.assertEqual(labels[0], explorer.LABEL_HIGH)


class ExploreNoFabricationTest(unittest.TestCase):
    def test_no_keyword_match_returns_empty(self):
        client = _FakeClient()
        ex = _make_explorer(client)
        res = ex.explore("fundingEntity", "FE-1", ["zebra", "spaceship"])
        self.assertEqual(res["state"], explorer.STATE_NO_MATCH)
        self.assertEqual(res["results"], [])  # NOTHING invented

    def test_empty_keywords_returns_empty(self):
        client = _FakeClient()
        ex = _make_explorer(client)
        res = ex.explore("fundingEntity", "FE-1", [])
        self.assertEqual(res["state"], explorer.STATE_NO_MATCH)
        self.assertEqual(res["results"], [])

    def test_null_field_reported_as_is_not_fabricated(self):
        # totalCommitment present but null on the record -> value=None, not a guessed number.
        rec = dict(_FAKE_FE_RECORD)
        rec["totalCommitment"] = None
        client = _FakeClient(record=rec)
        ex = _make_explorer(client)
        res = ex.explore("fundingEntity", "FE-1", ["commitment"])
        self.assertEqual(res["state"], explorer.STATE_EXPLORED)
        top = next(r for r in res["results"] if r["field"] == "totalCommitment")
        self.assertIsNone(top["value"])
        self.assertIn("note", top)  # explicit "matched but null" note

    def test_unknown_entity_type_refuses(self):
        client = _FakeClient()
        ex = _make_explorer(client)
        res = ex.explore("unicorn", "X-1", ["commitment"])
        self.assertEqual(res["state"], explorer.STATE_REFUSED)
        self.assertEqual(res["results"], [])

    def test_no_record_returns_empty_no_invention(self):
        client = _FakeClient(record=None)  # single + list both yield no row
        ex = _make_explorer(client)
        res = ex.explore("fundingEntity", "FE-NONEXISTENT", ["commitment"])
        self.assertEqual(res["state"], explorer.STATE_NO_MATCH)
        self.assertEqual(res["results"], [])


class ExploreConfidenceCapTest(unittest.TestCase):
    def test_fuzzy_entity_caps_every_field_at_low(self):
        client = _FakeClient()
        ex = _make_explorer(client)
        # "commitment" would be HIGH, but the entity was only fuzzily resolved -> capped to LOW.
        res = ex.explore("fundingEntity", "FE-1", ["commitment"], entity_fuzzy=True)
        self.assertEqual(res["state"], explorer.STATE_EXPLORED)
        top = next(r for r in res["results"] if r["field"] == "totalCommitment")
        self.assertEqual(top["confidence_label"], explorer.LABEL_LOW)
        self.assertEqual(top["confidence"], explorer.CONFIDENCE_LOW)


class ExploreFallbackTest(unittest.TestCase):
    def test_single_query_500_falls_back_to_list_query(self):
        # single_query 500s on every attempt -> fall back to fundingEntities list, match by id.
        client = _FakeClient(single_fail_always=True)
        ex = _make_explorer(client)
        res = ex.explore("fundingEntity", "FE-1", ["commitment"], name_hint="Beehive")
        self.assertEqual(res["state"], explorer.STATE_EXPLORED)
        top = next(r for r in res["results"] if r["field"] == "totalCommitment")
        self.assertEqual(top["value"], 125000000.0)
        # provenance reflects the LIST path
        self.assertEqual(top["provenance"]["operation"], "fundingEntities")
        self.assertEqual(top["provenance"]["json_field_path"],
                         "$.fundingEntities.pageItems.totalCommitment")
        # a list-query call was actually issued
        self.assertTrue(any("fundingEntities(" in q.replace(" ", "") for q, _ in client.calls))


class ExploreQuestionTest(unittest.TestCase):
    def test_explore_question_extracts_keywords_and_routes(self):
        client = _FakeClient()
        ex = _make_explorer(client)
        resolved = {"entity_type": "fundingEntity", "id": "FE-1", "name": "Beehive Fund I"}
        res = ex.explore_question("What is the total commitment for this funding entity?",
                                  resolved, fetched_at="2026-06-24T00:00:00Z")
        self.assertEqual(res["state"], explorer.STATE_EXPLORED)
        self.assertIn("commitment", res["keywords"])
        top = next(r for r in res["results"] if r["field"] == "totalCommitment")
        self.assertEqual(top["value"], 125000000.0)
        self.assertEqual(top["confidence_label"], explorer.LABEL_HIGH)

    def test_explore_question_fuzzy_entity_caps_low(self):
        client = _FakeClient()
        ex = _make_explorer(client)
        resolved = {"entity_type": "fundingEntity", "id": "FE-1",
                    "name": "Beehive Fund I", "fuzzy": True}
        res = ex.explore_question("how much commitment?", resolved)
        top = next(r for r in res["results"] if r["field"] == "totalCommitment")
        self.assertEqual(top["confidence_label"], explorer.LABEL_LOW)


if __name__ == "__main__":
    unittest.main(verbosity=2)
