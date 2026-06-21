#!/usr/bin/env python3
"""test_hca_adapter.py — stdlib unittest for the Hypercore read-only adapter (SLICE-HCA-02).

Covers:
  1. READ-ONLY GUARD (hard gate): no mutating verb is callable on the contract / backends
     / public adapter surface.
  2. FixtureBackend returns well-formed RawApiResponse-shaped dicts (backend="fixture").
  3. is_live() is false with no creds; require_live raises NoLiveDataError (no fabrication).
  4. LiveBackend is import-safe but raises the documented NotImplementedError when invoked.
  5. Config/env-driven backend selection (default fixture; "live" -> LiveBackend stub).
  6. Adversarial fixtures (paginated / truncated / stale / drifted) are present and labeled.
  7. No network import is present in the adapter module.

Run:
  python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py' -v
"""

import importlib.util
import inspect
import json
import os
import unittest

# --- load the adapter module by path (filename has a hyphen) -----------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.abspath(os.path.join(_THIS_DIR, os.pardir))           # .claude/scripts
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPTS_DIR, os.pardir, os.pardir))
_ADAPTER_PATH = os.path.join(_SCRIPTS_DIR, "hca-adapter.py")
_FIXTURES_DIR = os.path.join(_REPO_ROOT, ".claude", "skills", "acos-hypercore-ask", "fixtures")


_LIVE_PATH = os.path.join(_SCRIPTS_DIR, "hca-live.py")
_INTROSPECTION_PATH = os.path.join(
    _REPO_ROOT, "planning", "preeng", "001-hypercore-ask", "_introspection.json"
)


def _load_adapter_module():
    spec = importlib.util.spec_from_file_location("hca_adapter", _ADAPTER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_live_module():
    # Share ONE module instance with the adapter's lazy loader (sys.modules cache),
    # so exception classes are identical across both (isinstance/except match).
    import sys
    cached = sys.modules.get("hca_live")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location("hca_live", _LIVE_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["hca_live"] = mod
    spec.loader.exec_module(mod)
    return mod


hca = _load_adapter_module()
live = _load_live_module()


# Independent forbidden-verb list (QA re-authors this; do NOT import the module's).
MUTATING_VERBS = (
    "create", "update", "delete", "post", "put", "patch", "write", "mutate",
    "insert", "remove", "drop", "save", "upsert", "modify", "add",
)


def _public_methods(obj_or_cls):
    names = []
    for name, _ in inspect.getmembers(obj_or_cls, predicate=callable):
        if name.startswith("_"):
            continue
        names.append(name)
    return names


class ReadOnlyGuardTest(unittest.TestCase):
    """HARD GATE: no mutating verb may be callable on the contract or any backend."""

    def _assert_no_mutating_methods(self, cls):
        for name in _public_methods(cls):
            lowered = name.lower()
            for verb in MUTATING_VERBS:
                self.assertFalse(
                    lowered == verb or lowered.startswith(verb + "_")
                    or ("_" + verb) in lowered or lowered.endswith("_" + verb),
                    msg=(f"FORBIDDEN mutating method {name!r} found on {cls.__name__} "
                         f"(verb={verb!r}) — read-only contract violated"),
                )

    def test_contract_base_is_read_only(self):
        self._assert_no_mutating_methods(hca.HypercoreBackend)

    def test_fixture_backend_is_read_only(self):
        self._assert_no_mutating_methods(hca.FixtureBackend)

    def test_live_backend_is_read_only(self):
        self._assert_no_mutating_methods(hca.LiveBackend)

    def test_public_adapter_is_read_only(self):
        self._assert_no_mutating_methods(hca.HypercoreAdapter)

    def test_contract_surface_is_exactly_the_read_allowlist(self):
        # Every public method declared on the abstract base must be in the read-only
        # allow-list. This fails loudly if a mutating method is ever added.
        declared = {n for n in vars(hca.HypercoreBackend) if not n.startswith("_")
                    and callable(getattr(hca.HypercoreBackend, n))}
        self.assertEqual(
            declared, set(hca.READ_ONLY_CONTRACT_METHODS),
            msg=f"contract surface drifted from read-only allow-list: {declared}",
        )


class FixtureBackendTest(unittest.TestCase):
    def setUp(self):
        self.backend = hca.FixtureBackend()

    def test_get_entity_returns_raw_api_response_shape(self):
        resp = self.backend.get_entity("loan", "L-001")
        for field in ("raw_response_id", "endpoint", "request_params", "timestamp",
                      "http_status", "cursor", "reported_total", "body", "backend"):
            self.assertIn(field, resp, msg=f"RawApiResponse missing field {field!r}")
        self.assertEqual(resp["backend"], "fixture")
        self.assertEqual(resp["http_status"], 200)
        self.assertEqual(resp["body"]["loan_id"], "L-001")

    def test_get_entity_borrower(self):
        resp = self.backend.get_entity("borrower", "B-001")
        self.assertEqual(resp["backend"], "fixture")
        self.assertEqual(resp["body"]["borrower_id"], "B-001")

    def test_get_entity_missing_fixture_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.backend.get_entity("loan", "DOES-NOT-EXIST")

    def test_list_entities_paginates_to_exhaustion(self):
        page1 = self.backend.list_entities("loan")
        self.assertEqual(page1["backend"], "fixture")
        self.assertEqual(page1["reported_total"], 3)
        self.assertEqual(len(page1["body"]["data"]), 2)
        self.assertEqual(page1["cursor"], "CURSOR_PAGE2")
        page2 = self.backend.list_entities("loan", cursor=page1["cursor"])
        self.assertIsNone(page2["cursor"])
        self.assertEqual(len(page2["body"]["data"]), 1)
        fetched = len(page1["body"]["data"]) + len(page2["body"]["data"])
        self.assertEqual(fetched, page2["reported_total"])  # complete, no truncation

    def test_get_schema_loads_descriptor(self):
        desc = self.backend.get_schema("loan")
        self.assertIsInstance(desc, hca.SchemaDescriptor)
        self.assertEqual(desc.entity_type, "loan")
        self.assertIn("outstanding_principal", desc.expected_fields)

    def test_fixtures_contain_placeholder_marker(self):
        # All fixtures must be clearly marked PLACEHOLDER synthetic data.
        names = [n for n in os.listdir(_FIXTURES_DIR) if n.endswith(".json")]
        self.assertTrue(names)
        for name in names:
            with open(os.path.join(_FIXTURES_DIR, name), "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            self.assertIn("PLACEHOLDER", json.dumps(raw),
                          msg=f"fixture {name} is not marked PLACEHOLDER")


class DegradationTest(unittest.TestCase):
    def test_fixture_adapter_is_not_live(self):
        adapter = hca.HypercoreAdapter(backend=hca.FixtureBackend())
        self.assertFalse(adapter.is_live())

    def test_require_live_raises_no_live_data_error_with_envelope(self):
        adapter = hca.HypercoreAdapter(backend=hca.FixtureBackend())
        with self.assertRaises(hca.NoLiveDataError) as ctx:
            adapter.get_entity("loan", "L-001", require_live=True)
        env = ctx.exception.envelope
        self.assertEqual(env["state"], hca.NO_LIVE_DATA)
        self.assertFalse(env["live"])
        self.assertIsNone(env["data"])  # never fabricated
        self.assertEqual(env["entity_type"], "loan")

    def test_no_live_data_envelope_shape(self):
        env = hca.no_live_data_envelope(entity_type="loan", request={"id": "L-1"})
        self.assertEqual(env["state"], "NO_LIVE_DATA")
        self.assertIsNone(env["data"])
        self.assertIn("no live data", env["message"])

    def test_fixture_read_without_require_live_succeeds(self):
        # Graceful: without require_live, fixture reads work and are labeled.
        adapter = hca.HypercoreAdapter(backend=hca.FixtureBackend())
        resp = adapter.get_entity("loan", "L-001")
        self.assertEqual(resp["backend"], "fixture")


class LiveBackendCredentialTest(unittest.TestCase):
    """Import-safety + credential presence (is_live keys on CLIENT_ID + client secret)."""

    def test_live_backend_imports_safely(self):
        lb = hca.LiveBackend(env={})  # construction must not raise (no network at ctor)
        self.assertIsInstance(lb, hca.HypercoreBackend)

    def test_is_live_false_without_creds(self):
        lb = hca.LiveBackend(env={})
        self.assertFalse(lb.is_live())

    def test_is_live_true_with_both_creds(self):
        lb = hca.LiveBackend(env={
            "CLIENT_ID": "doppler-injected-id",
            "HYPERCORE_CLIENT_SECRET": "doppler-injected-secret",
        })
        self.assertTrue(lb.is_live())

    def test_is_live_false_with_partial_creds(self):
        lb = hca.LiveBackend(env={"HYPERCORE_CLIENT_SECRET": "only-secret"})
        self.assertFalse(lb.is_live())
        lb2 = hca.LiveBackend(env={"CLIENT_ID": "only-id"})
        self.assertFalse(lb2.is_live())

    def test_live_backend_reads_configurable_env_names(self):
        lb = hca.LiveBackend(client_id_env="CUSTOM_ID", api_key_env="CUSTOM_SECRET",
                             env={"CUSTOM_ID": "i", "CUSTOM_SECRET": "s"})
        self.assertTrue(lb.is_live())

    def test_invoking_live_method_without_creds_raises_no_live_data(self):
        lb = hca.LiveBackend(env={})  # no creds
        with self.assertRaises(hca.NoLiveDataError):
            lb.get_entity("loan", "L-001")

    def test_subscribe_events_is_todo(self):
        lb = hca.LiveBackend(env={"CLIENT_ID": "i", "HYPERCORE_CLIENT_SECRET": "s"})
        with self.assertRaises(NotImplementedError):
            lb.subscribe_events("loan")


class BackendSelectionTest(unittest.TestCase):
    def test_explicit_fixture_default_resolves_fixture(self):
        # With an explicit fixture default and clean env, fixture is selected.
        backend = hca.select_backend(backend="fixture", env={})
        self.assertIsInstance(backend, hca.FixtureBackend)

    def test_env_override_to_fixture(self):
        backend = hca.select_backend(env={"HCA_ADAPTER_BACKEND": "fixture"})
        self.assertIsInstance(backend, hca.FixtureBackend)

    def test_env_override_to_live(self):
        backend = hca.select_backend(env={"HCA_ADAPTER_BACKEND": "live"})
        self.assertIsInstance(backend, hca.LiveBackend)

    def test_explicit_arg_wins(self):
        backend = hca.select_backend(backend="live", env={})
        self.assertIsInstance(backend, hca.LiveBackend)

    def test_config_backend_is_live_now_access_verified(self):
        # config.yaml ships adapter.backend: "live" since access was verified 2026-06-18.
        self.assertEqual(hca._read_config_backend(), "live")


class AdversarialFixturesTest(unittest.TestCase):
    def _load(self, name):
        with open(os.path.join(_FIXTURES_DIR, name), "r", encoding="utf-8") as fh:
            return json.load(fh)

    def test_paginated_fixture_present(self):
        self.assertTrue(os.path.isfile(os.path.join(_FIXTURES_DIR, "list_loan__page1.json")))
        fx = self._load("list_loan__page1.json")
        self.assertEqual(fx["_adversarial"], "paginated")
        self.assertEqual(fx["reported_total"], 3)

    def test_truncated_fixture_present_and_inconsistent(self):
        fx = self._load("list_loan_truncated__page1.json")
        self.assertEqual(fx["_adversarial"], "truncated")
        # deliberately inconsistent: cursor null (claims done) but fetched < reported_total
        self.assertIsNone(fx["cursor"])
        self.assertLess(len(fx["body"]["data"]), fx["reported_total"])

    def test_stale_fixture_present(self):
        fx = self._load("loan_stale__L-900.json")
        self.assertEqual(fx["_adversarial"], "stale")
        self.assertTrue(fx["timestamp"].startswith("2024"))

    def test_drifted_fixture_present(self):
        fx = self._load("loan_drifted__L-901.json")
        self.assertEqual(fx["_adversarial"], "drifted")
        body = fx["body"]
        # drift: renamed field + missing currency + unexpected legacy field
        self.assertNotIn("outstanding_principal", body)
        self.assertIn("principal_outstanding", body)
        self.assertNotIn("currency", body)
        self.assertIn("legacy_balance", body)


class NoNetworkImportTest(unittest.TestCase):
    def test_adapter_module_has_no_network_import(self):
        with open(_ADAPTER_PATH, "r", encoding="utf-8") as fh:
            src = fh.read()
        # Check actual import statements (ignore prose/comments mentioning the words).
        import_lines = [ln.strip() for ln in src.splitlines()
                        if ln.strip().startswith("import ") or ln.strip().startswith("from ")]
        joined = "\n".join(import_lines)
        for forbidden in ("urllib", "http.client", "http ", "socket", "requests", "ssl"):
            self.assertNotIn(forbidden, joined,
                             msg=f"network import {forbidden!r} found in adapter import block")

    def test_fixture_backend_path_uses_no_network(self):
        # A full FixtureBackend round-trip must not need hca-live (no socket reachable).
        backend = hca.FixtureBackend()
        self.assertFalse(backend.is_live())
        resp = backend.get_entity("loan", "L-001")
        self.assertEqual(resp["backend"], "fixture")


# ===========================================================================
# LiveBackend internals (mocked HTTP — NO real network in unit tests)
# ===========================================================================

_FAKE_ACCESS = "FAKE.JWT.ACCESS"
_FAKE_REFRESH = "FAKE.REFRESH.TOKEN"


class _MockHttp:
    """Records calls and returns scripted (status, body_str) tuples by URL substring.

    Used as the `opener` test seam on TokenManager / GraphQLTransport / LiveBackend, so
    NO real socket is ever opened. Also asserts no secret is logged by us (we never print).
    """

    def __init__(self):
        self.calls = []                 # list of dicts: {url, body(dict), headers}
        self.token_response = {"accessToken": _FAKE_ACCESS, "expiresIn": 1800,
                               "refreshToken": _FAKE_REFRESH}
        self.refresh_response = {"accessToken": "FAKE.JWT.ACCESS2", "expiresIn": 1800,
                                 "refreshToken": "FAKE.REFRESH2"}
        self.gql_pages = []             # FIFO of dicts to return as GraphQL `data` payloads
        self.gql_raw = None             # if set, return this raw {data/errors} envelope
        self.fail_token = False

    def __call__(self, *, url, data, headers, method, timeout):
        import json as _json
        body = _json.loads(data.decode())
        self.calls.append({"url": url, "body": body, "headers": dict(headers)})
        if "token/refresh" in url:
            return 200, _json.dumps(self.refresh_response)
        if "api-token" in url:
            if self.fail_token:
                return 500, _json.dumps({"error": "boom"})
            return 200, _json.dumps(self.token_response)
        # GraphQL endpoint
        if self.gql_raw is not None:
            return 200, _json.dumps(self.gql_raw)
        page = self.gql_pages.pop(0) if self.gql_pages else {}
        return 200, _json.dumps({"data": page})


def _live_backend_with_mock(mock, **kw):
    return hca.LiveBackend(
        env={"CLIENT_ID": "fake-id", "HYPERCORE_CLIENT_SECRET": "fake-secret"},
        introspection_path=_INTROSPECTION_PATH,
        opener=mock, **kw,
    )


class ReadOnlyOperationGuardTest(unittest.TestCase):
    """Operation-level read-only enforcement: a mutation/subscription string is refused."""

    def test_query_allowed(self):
        live.assert_query_only("query Q { loans { totalFilteredRecords } }")
        live.assert_query_only("{ loans { totalFilteredRecords } }")  # anon = query

    def test_mutation_refused(self):
        with self.assertRaises(live.ReadOnlyViolation):
            live.assert_query_only("mutation M { deleteLoan(id: 1) { id } }")

    def test_subscription_refused(self):
        with self.assertRaises(live.ReadOnlyViolation):
            live.assert_query_only("subscription S { loanUpdated { id } }")

    def test_mutation_hidden_after_query_refused(self):
        # A document carrying both a query and a mutation must be refused.
        doc = "query A { loan(id:1){id} }\nmutation B { updateLoan(id:1){id} }"
        with self.assertRaises(live.ReadOnlyViolation):
            live.assert_query_only(doc)

    def test_word_mutation_in_string_literal_is_not_a_false_positive(self):
        # 'mutation' appearing only inside a string literal is NOT an operation keyword.
        live.assert_query_only('query Q { search(term: "mutation") { id } }')

    def test_transport_refuses_mutation_before_network(self):
        mock = _MockHttp()
        tm = live.TokenManager(token_url="https://auth/api-token",
                               refresh_url="https://auth/api-token/token/refresh",
                               client_id="i", client_secret="s", opener=mock)
        tx = live.GraphQLTransport(gql_url="https://api/graphql", token_manager=tm,
                                   opener=mock)
        with self.assertRaises(live.ReadOnlyViolation):
            tx.execute("mutation M { deleteLoan(id: 1) { id } }")
        # Guard fires BEFORE any HTTP call (no token fetch, no gql call).
        self.assertEqual(mock.calls, [])


class TokenLifecycleTest(unittest.TestCase):
    def _tm(self, mock, now_box):
        return live.TokenManager(
            token_url="https://auth/api-token",
            refresh_url="https://auth/api-token/token/refresh",
            client_id="i", client_secret="s", refresh_skew_seconds=60,
            opener=mock, now=lambda: now_box[0],
        )

    def test_fetch_caches_and_reuses(self):
        mock = _MockHttp()
        now = [1000.0]
        tm = self._tm(mock, now)
        t1 = tm.access_token()
        t2 = tm.access_token()  # still valid -> no second auth call
        self.assertEqual(t1, _FAKE_ACCESS)
        self.assertEqual(t2, _FAKE_ACCESS)
        auth_calls = [c for c in mock.calls if c["url"].endswith("api-token")]
        self.assertEqual(len(auth_calls), 1)

    def test_auto_refresh_near_expiry(self):
        mock = _MockHttp()
        now = [1000.0]
        tm = self._tm(mock, now)
        tm.access_token()                       # fetch (expiresIn=1800 -> expires_at=2800)
        now[0] = 2800 - 30                       # within 60s skew of expiry
        t2 = tm.access_token()                   # should refresh
        self.assertEqual(t2, "FAKE.JWT.ACCESS2")
        refresh_calls = [c for c in mock.calls if "token/refresh" in c["url"]]
        self.assertEqual(len(refresh_calls), 1)
        # refresh request carried the refreshToken and a Bearer header
        self.assertEqual(refresh_calls[0]["body"].get("refreshToken"), _FAKE_REFRESH)
        self.assertIn("Authorization", refresh_calls[0]["headers"])

    def test_refresh_failure_falls_back_to_full_reauth(self):
        mock = _MockHttp()
        now = [1000.0]
        tm = self._tm(mock, now)
        tm.access_token()
        # make refresh raise, full re-auth must recover
        def boom(*a, **k):
            if "token/refresh" in k["url"]:
                raise OSError("refresh down")
            import json as _json
            return 200, _json.dumps(mock.token_response)
        mock_calls_before = len(mock.calls)
        tm._opener = boom  # type: ignore[attr-defined]
        now[0] = 2800 - 30
        t = tm.access_token()
        self.assertEqual(t, _FAKE_ACCESS)  # recovered via full re-auth

    def test_missing_creds_raises_auth_error(self):
        with self.assertRaises(live.LiveAuthError):
            live.TokenManager(token_url="u", refresh_url="r",
                              client_id="", client_secret="")

    def test_secret_and_token_never_in_error_messages(self):
        mock = _MockHttp()
        mock.fail_token = True
        now = [1000.0]
        tm = self._tm(mock, now)
        # fail_token returns 500 -> urllib path would raise HTTPError, but our mock
        # returns (500, body); _apply_token_response will see no accessToken -> LiveAuthError.
        with self.assertRaises(live.LiveAuthError) as ctx:
            tm.access_token()
        msg = str(ctx.exception)
        self.assertNotIn("fake-secret", msg)
        self.assertNotIn(_FAKE_ACCESS, msg)


class LivePaginationCompletenessTest(unittest.TestCase):
    def test_walks_offset_pages_to_completion(self):
        mock = _MockHttp()
        # reported_total = 3, page_limit will be 2 -> two pages (2 + 1)
        mock.gql_pages = [
            {"loans": {"totalFilteredRecords": 3,
                       "pageItems": [{"id": "1"}, {"id": "2"}]}},
            {"loans": {"totalFilteredRecords": 3,
                       "pageItems": [{"id": "3"}]}},
        ]
        lb = _live_backend_with_mock(mock, page_limit=2)
        resp = lb.list_entities("loan", filters={"limit": 2, "fields": ["id"]})
        body = resp["body"]
        self.assertEqual(body["reported_total"], 3)
        self.assertEqual(body["fetched"], 3)
        self.assertTrue(body["complete"])
        self.assertEqual(body["pages"], 2)
        self.assertEqual(len(body["data"]), 3)
        self.assertIsNone(resp["cursor"])  # offset pagination, no cursor

    def test_short_page_with_known_total_flags_incomplete(self):
        mock = _MockHttp()
        # server claims 5 but returns a short page of 2 and no more -> NOT complete
        mock.gql_pages = [
            {"loans": {"totalFilteredRecords": 5,
                       "pageItems": [{"id": "1"}, {"id": "2"}]}},
        ]
        lb = _live_backend_with_mock(mock, page_limit=10)
        resp = lb.list_entities("loan", filters={"limit": 10, "fields": ["id"]})
        body = resp["body"]
        self.assertEqual(body["reported_total"], 5)
        self.assertEqual(body["fetched"], 2)
        self.assertFalse(body["complete"])  # surfaced, never silently truncated

    def test_provenance_shape_on_list(self):
        mock = _MockHttp()
        mock.gql_pages = [
            {"loans": {"totalFilteredRecords": 1, "pageItems": [{"id": "1"}]}},
        ]
        lb = _live_backend_with_mock(mock, page_limit=50)
        resp = lb.list_entities("loan", filters={"fields": ["id"]})
        prov = resp["body"]["provenance"]
        for k in ("operation_name", "query", "variables_template",
                  "response_json_path", "fetched_at"):
            self.assertIn(k, prov)


class LiveSchemaValidationTest(unittest.TestCase):
    def test_unknown_field_is_refused_before_send(self):
        mock = _MockHttp()
        lb = _live_backend_with_mock(mock)
        with self.assertRaises(live.SchemaValidationError):
            lb.get_entity("loan", "L-1", params={"fields": ["id", "definitely_not_a_field"]})
        # refused before any GraphQL call (only the token fetch may have happened, but
        # since validation occurs before transport.execute, no gql page was consumed)
        gql_calls = [c for c in mock.calls if c["url"].endswith("graphql")]
        self.assertEqual(gql_calls, [])

    def test_known_field_passes_validation_and_sends(self):
        mock = _MockHttp()
        mock.gql_pages = [{"loan": {"id": "L-1", "name": "n"}}]
        lb = _live_backend_with_mock(mock)
        resp = lb.get_entity("loan", "L-1", params={"fields": ["id", "name"]})
        self.assertEqual(resp["backend"], "live")
        self.assertEqual(resp["body"]["record"]["id"], "L-1")
        for k in ("operation_name", "query", "variables", "response_json_path",
                  "fetched_at"):
            self.assertIn(k, resp["body"]["provenance"])

    def test_unknown_entity_type_refused(self):
        mock = _MockHttp()
        lb = _live_backend_with_mock(mock)
        with self.assertRaises(live.SchemaValidationError):
            lb.get_entity("not_an_entity", "X-1")

    def test_get_schema_returns_introspected_descriptor(self):
        mock = _MockHttp()
        lb = _live_backend_with_mock(mock)
        desc = lb.get_schema("loan")
        self.assertIsInstance(desc, hca.SchemaDescriptor)
        self.assertIn("id", desc.expected_fields)
        self.assertTrue(desc.version.startswith("live-introspection:"))


class LiveGraphQLErrorTest(unittest.TestCase):
    def test_graphql_errors_surface_structurally(self):
        mock = _MockHttp()
        mock.gql_raw = {"data": None, "errors": [{"message": "not authorized"}]}
        lb = _live_backend_with_mock(mock)
        with self.assertRaises(live.GraphQLError) as ctx:
            lb.get_entity("loan", "L-1", params={"fields": ["id"]})
        self.assertTrue(ctx.exception.errors)  # never fabricated; errors preserved

    def test_tls_min_version_is_1_2(self):
        # The transport's SSL context enforces TLS >= 1.2.
        ctx = live._tls12_context()
        import ssl as _ssl
        self.assertEqual(ctx.minimum_version, _ssl.TLSVersion.TLSv1_2)


class LiveDegradationTest(unittest.TestCase):
    def test_no_creds_via_public_adapter_raises_no_live_data(self):
        lb = hca.LiveBackend(env={})  # not live
        adapter = hca.HypercoreAdapter(backend=lb)
        self.assertFalse(adapter.is_live())
        with self.assertRaises(hca.NoLiveDataError) as ctx:
            adapter.get_entity("loan", "L-1", require_live=True)
        env = ctx.exception.envelope
        self.assertEqual(env["state"], hca.NO_LIVE_DATA)
        self.assertIsNone(env["data"])  # never fabricated


class GraphQLShapedFixturesTest(unittest.TestCase):
    """New fixtures SHAPED from the real GraphQL schema (camelCase + GraphQL provenance).

    These exercise the live-shaped path for downstream slices without breaking the
    pre-access REST fixtures. Every one must be marked `_placeholder: true` and carry
    NO real PII.
    """

    GQL_FIXTURES = [
        "gql_loan__L-GQL-1.json",
        "gql_list_loan__complete.json",
        "gql_list_loan_truncated__short.json",
        "gql_client__C-GQL-1.json",
    ]
    # Synthetic-placeholder markers that MUST appear in any PII-bearing value.
    PII_OK_MARKERS = ("PLACEHOLDER", "example.invalid", "+10000000000")

    def _load(self, name):
        with open(os.path.join(_FIXTURES_DIR, name), "r", encoding="utf-8") as fh:
            return json.load(fh)

    def test_gql_fixtures_present_and_marked_placeholder(self):
        for name in self.GQL_FIXTURES:
            path = os.path.join(_FIXTURES_DIR, name)
            self.assertTrue(os.path.isfile(path), msg=f"missing GraphQL fixture {name}")
            fx = self._load(name)
            self.assertIs(fx.get("_placeholder"), True,
                          msg=f"{name} not marked _placeholder: true")

    def test_gql_single_loan_uses_camelcase_and_provenance(self):
        fx = self._load("gql_loan__L-GQL-1.json")
        rec = fx["body"]["record"]
        # camelCase GraphQL field names (NOT the REST loan_id/outstanding_principal shape)
        self.assertIn("id", rec)
        self.assertIn("commitment", rec)
        self.assertNotIn("loan_id", rec)
        prov = fx["body"]["provenance"]
        for k in ("operation_name", "query", "variables", "response_json_path",
                  "fetched_at"):
            self.assertIn(k, prov)

    def test_gql_paginated_complete_reconciles(self):
        fx = self._load("gql_list_loan__complete.json")
        body = fx["body"]
        self.assertEqual(body["fetched"], body["reported_total"])
        self.assertTrue(body["complete"])

    def test_gql_truncated_is_incomplete(self):
        fx = self._load("gql_list_loan_truncated__short.json")
        body = fx["body"]
        self.assertLess(body["fetched"], body["reported_total"])
        self.assertFalse(body["complete"])  # surfaced, not silent

    def test_gql_client_pii_is_deidentified(self):
        fx = self._load("gql_client__C-GQL-1.json")
        rec = fx["body"]["record"]
        for field in ("companyName", "displayName", "email", "mobileNumber",
                      "identificationNumber"):
            val = rec.get(field)
            if val is None:
                continue
            self.assertTrue(
                any(m in str(val) for m in self.PII_OK_MARKERS),
                msg=f"client fixture field {field!r}={val!r} is not a synthetic placeholder",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
