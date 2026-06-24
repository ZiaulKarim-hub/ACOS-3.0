#!/usr/bin/env python3
"""test_hca_retry.py — centralized retry-on-500 coverage for every live Hypercore call.

The Hypercore API returns sporadic HTTP 500s on several read paths (loan(id), the
transaction-preview / payoff resolvers, and bulk loans pages under load). Retry is
CENTRALIZED in GraphQLTransport.execute (hca-live.py): every live read — single record,
the offset-pagination walker, raw_query (used by hca-figures + the hca-analyze bulk fetch +
hca-kg joins) — funnels through it. This suite proves:

  1. Transport RETRIES an intermittent 500 (up to 3x, linear backoff) then SUCCEEDS.
  2. Transport REFUSES (raises LiveServerError) after the budget is exhausted, stating 500.
  3. Transport does NOT retry a non-5xx error (e.g. a deterministic 400) — surfaces at once.
  4. A 502/503/504 is retried the same as a 500.
  5. The pagination walker (list_entities) inherits the retry on a flaky page.
  6. The analyze BULK FETCH retries a flaky page, then refuses after exhaustion.
  7. NO sleeping happens in tests (a sleep seam is injected and counted, not real time).

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
_INTROSPECTION_PATH = os.path.join(
    _REPO_ROOT, "planning", "preeng", "001-hypercore-ask", "_introspection.json")


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


live = _load("hca_live", "hca-live.py")
analyze = _load("hca_analyze", "hca-analyze.py")
figures = _load("hca_figures", "hca-figures.py")


# ---------------------------------------------------------------------------
# A scriptable HTTP opener seam: returns a FIFO of (status, body) tuples per URL class.
# A 5xx status is turned into a LiveServerError by _http_post_json (mirrors real urllib).
# ---------------------------------------------------------------------------

_FAKE_ACCESS = "FAKE.JWT.ACCESS"


class _ScriptedHttp:
    def __init__(self, gql_script):
        # gql_script: list of (status, data_dict_or_None). 5xx -> body ignored.
        self._gql = list(gql_script)
        self.gql_call_count = 0
        self.token_call_count = 0

    def __call__(self, *, url, data, headers, method, timeout):
        if "api-token" in url and "token/refresh" not in url:
            self.token_call_count += 1
            return 200, json.dumps({"accessToken": _FAKE_ACCESS, "expiresIn": 1800,
                                    "refreshToken": "R"})
        if "token/refresh" in url:
            return 200, json.dumps({"accessToken": _FAKE_ACCESS, "expiresIn": 1800,
                                    "refreshToken": "R"})
        # GraphQL endpoint
        self.gql_call_count += 1
        if not self._gql:
            return 200, json.dumps({"data": {}})
        status, payload = self._gql.pop(0)
        if isinstance(status, int) and status >= 500:
            return status, json.dumps({"error": "boom"})
        if isinstance(status, Exception):  # allow scripting a raised transport error
            raise status
        return status, json.dumps({"data": payload})


def _transport(mock, *, attempts=3, backoff_s=0.0, sleep=None):
    tm = live.TokenManager(token_url="https://auth/api-token",
                           refresh_url="https://auth/api-token/token/refresh",
                           client_id="i", client_secret="s", opener=mock)
    return live.GraphQLTransport(gql_url="https://api/graphql", token_manager=tm,
                                 opener=mock, retry_attempts=attempts,
                                 retry_backoff_s=backoff_s, sleep=sleep)


class _SleepSpy:
    def __init__(self):
        self.calls = []

    def __call__(self, secs):
        self.calls.append(secs)


# ===========================================================================
# Transport-level retry (the centralized choke point)
# ===========================================================================

class TransportRetryTest(unittest.TestCase):
    def test_retries_intermittent_500_then_succeeds(self):
        # 500, 500, then 200 -> succeeds on the 3rd attempt (within the 3-attempt budget).
        spy = _SleepSpy()
        mock = _ScriptedHttp([(500, None), (500, None),
                              (200, {"loans": {"totalFilteredRecords": 0, "pageItems": []}})])
        tx = _transport(mock, attempts=3, sleep=spy)
        data = tx.execute("query Q { loans { totalFilteredRecords pageItems { id } } }")
        self.assertEqual(data["loans"]["totalFilteredRecords"], 0)
        self.assertEqual(mock.gql_call_count, 3)        # exactly 3 underlying attempts
        self.assertEqual(len(spy.calls), 2)             # slept between the 2 retries only

    def test_refuses_after_budget_exhausted_stating_500(self):
        # Persistent 500: after the budget, a LiveServerError(500) propagates (caller refuses).
        spy = _SleepSpy()
        mock = _ScriptedHttp([(500, None), (500, None), (500, None), (500, None)])
        tx = _transport(mock, attempts=3, sleep=spy)
        with self.assertRaises(live.LiveServerError) as ctx:
            tx.execute("query Q { loans { totalFilteredRecords } }")
        self.assertEqual(ctx.exception.status, 500)
        self.assertIn("500", str(ctx.exception))
        self.assertEqual(mock.gql_call_count, 3)        # tried exactly the budget, no more

    def test_does_not_retry_non_5xx(self):
        # A deterministic 400 is NOT retried (don't burn the budget on a real error).
        import io
        import urllib.error

        class _Http400:
            def __init__(self):
                self.gql_call_count = 0

            def __call__(self, *, url, data, headers, method, timeout):
                if "api-token" in url:
                    return 200, json.dumps({"accessToken": _FAKE_ACCESS, "expiresIn": 1800})
                self.gql_call_count += 1
                # fp=BytesIO so the HTTPError owns a closeable stream (no ResourceWarning).
                raise urllib.error.HTTPError(url, 400, "Bad Request", {}, io.BytesIO(b""))

        import warnings
        mock = _Http400()
        tx = _transport(mock, attempts=3, sleep=_SleepSpy())
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)  # synthetic HTTPError fp cleanup
            with self.assertRaises(live.LiveTransportError):
                tx.execute("query Q { loans { totalFilteredRecords } }")
        self.assertEqual(mock.gql_call_count, 1)        # exactly one attempt — no retry

    def test_502_503_504_are_retried_like_500(self):
        for code in (502, 503, 504):
            mock = _ScriptedHttp([(code, None),
                                  (200, {"loans": {"totalFilteredRecords": 1,
                                                   "pageItems": [{"id": "L-1"}]}})])
            tx = _transport(mock, attempts=3, sleep=_SleepSpy())
            data = tx.execute("query Q { loans { totalFilteredRecords pageItems { id } } }")
            self.assertEqual(data["loans"]["pageItems"][0]["id"], "L-1", f"code={code}")
            self.assertEqual(mock.gql_call_count, 2, f"code={code} should retry once")

    def test_pagination_walker_inherits_retry(self):
        # list_entities walks pages via the same transport.execute -> retry covers each page.
        with open(_INTROSPECTION_PATH, "r", encoding="utf-8") as fh:
            intro = json.load(fh)
        schema_index = live.SchemaIndex(intro)
        # page-1 flakes once (500) then returns 2 of 3; page-2 returns the last 1.
        mock = _ScriptedHttp([
            (500, None),
            (200, {"loans": {"totalFilteredRecords": 3,
                             "pageItems": [{"id": "1"}, {"id": "2"}]}}),
            (200, {"loans": {"totalFilteredRecords": 3, "pageItems": [{"id": "3"}]}}),
        ])
        tx = _transport(mock, attempts=3, sleep=_SleepSpy())
        client = live.LiveGraphQLClient(transport=tx, schema_index=schema_index)
        out = client.list_entities("loan", fields=["id"], page_limit=2)
        self.assertEqual(out["fetched"], 3)
        self.assertTrue(out["complete"])
        self.assertEqual(out["reported_total"], 3)


# ===========================================================================
# Analyze bulk-fetch retry (the analysis bulk fetch path explicitly called out)
# ===========================================================================

class _FlakyBulkClient:
    """A raw_query client that fails the first `fail_first` calls with a 500-like error,
    then serves the scripted bulk pages."""

    def __init__(self, pages, *, fail_first=0):
        self._pages = list(pages)
        self._fail_first = int(fail_first)
        self.calls = 0

    def raw_query(self, query, variables):
        self.calls += 1
        if self._fail_first > 0:
            self._fail_first -= 1
            raise live.LiveServerError("GraphQL HTTP 500 Internal Server Error", status=500)
        if not self._pages:
            return {"loans": {"totalFilteredRecords": 0, "pageItems": []}}
        return {"loans": self._pages.pop(0)}


class _Sleep:
    def __init__(self):
        self.calls = 0

    def __call__(self, _secs):
        self.calls += 1


class AnalyzeBulkRetryTest(unittest.TestCase):
    def _fetcher(self, client, **kw):
        # Use an isolated in-memory cache to avoid touching the on-disk cache.
        cachelib = analyze._cache()
        cache = cachelib.TwoTierCache()
        return analyze.PortfolioFetcher(client=client, cache=cache, page_limit=100, **kw)

    def test_bulk_fetch_retries_flaky_page_then_succeeds(self):
        client = _FlakyBulkClient(
            [{"totalFilteredRecords": 2, "pageItems": [{"id": "L-1"}, {"id": "L-2"}]}],
            fail_first=2)  # two 500s then the good page
        sleep = _Sleep()
        out = self._fetcher(client, sleep=sleep).fetch()
        self.assertTrue(out["ok"], out)
        self.assertEqual(out["fetched"] if "fetched" in out else len(out["rows"]), 2)
        self.assertTrue(out["complete"])
        self.assertEqual(client.calls, 3)              # 2 failed + 1 success
        self.assertEqual(sleep.calls, 2)               # slept between the 2 retries

    def test_bulk_fetch_refuses_after_exhaustion(self):
        client = _FlakyBulkClient([], fail_first=99)   # never recovers
        out = self._fetcher(client, sleep=_Sleep()).fetch()
        self.assertFalse(out["ok"])
        self.assertEqual(out["state"], analyze.STATE_REFUSED)
        # The refusal text states the failure (a 500), never fabricates a value.
        self.assertIn("500", out["reason"])
        self.assertEqual(client.calls, figures.RETRY_ATTEMPTS)   # exactly the budget


# ===========================================================================
# figures._call_with_retry recognizes the live LiveServerError as the flaky 500
# ===========================================================================

class FiguresRetryRecognizesLiveServerErrorTest(unittest.TestCase):
    def test_call_with_retry_treats_live_server_error_as_retryable(self):
        class _C:
            def __init__(self):
                self.calls = 0

            def raw_query(self, q, v):
                self.calls += 1
                if self.calls < 2:
                    raise live.LiveServerError("HTTP 500", status=500)
                return {"ok": True}

        c = _C()
        data, attempts, errs = figures._call_with_retry(
            c, "query Q { x }", {}, attempts=3, backoff_s=0.0, sleep=lambda _s: None)
        self.assertEqual(data, {"ok": True})
        self.assertEqual(c.calls, 2)
        self.assertEqual(len(errs), 1)


# ===========================================================================
# figures._call_with_retry re-fetches a TRANSIENT EMPTY payload (substance-preserving retry):
# same input re-issued; a missing value is recovered, never a wrong one (re-gated downstream).
# ===========================================================================

class FiguresRetryOnEmptyPayloadTest(unittest.TestCase):
    @staticmethod
    def _empty(d):
        return not isinstance((d or {}).get("getLoanRepaymentDistribution"), dict)

    def test_refetches_transient_empty_then_succeeds(self):
        good = {"getLoanRepaymentDistribution": {"total": 100.0}}

        class _C:
            def __init__(self):
                self.calls = 0

            def raw_query(self, q, v):
                self.calls += 1
                return {} if self.calls < 3 else good  # empty twice (same input), then good

        c = _C()
        data, attempts, errs = figures._call_with_retry(
            c, "query Q { x }", {}, attempts=3, backoff_s=0.0, sleep=lambda _s: None,
            is_empty=self._empty)
        self.assertEqual(data, good)
        self.assertEqual(c.calls, 3)
        self.assertTrue(any("empty" in e for e in errs))

    def test_returns_last_empty_after_budget_so_caller_refuses(self):
        class _C:
            def __init__(self):
                self.calls = 0

            def raw_query(self, q, v):
                self.calls += 1
                return {}  # always empty

        c = _C()
        data, attempts, errs = figures._call_with_retry(
            c, "query Q { x }", {}, attempts=3, backoff_s=0.0, sleep=lambda _s: None,
            is_empty=self._empty)
        self.assertEqual(c.calls, 3)            # spent the full budget re-fetching the same input
        self.assertTrue(self._empty(data))      # hands the still-empty payload back -> caller refuses

    def test_non_empty_first_response_is_not_refetched(self):
        good = {"getLoanRepaymentDistribution": {"total": 5.0}}

        class _C:
            def __init__(self):
                self.calls = 0

            def raw_query(self, q, v):
                self.calls += 1
                return good

        c = _C()
        data, attempts, errs = figures._call_with_retry(
            c, "query Q { x }", {}, attempts=3, backoff_s=0.0, sleep=lambda _s: None,
            is_empty=self._empty)
        self.assertEqual(c.calls, 1)
        self.assertEqual(data, good)


if __name__ == "__main__":
    unittest.main(verbosity=2)
