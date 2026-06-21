#!/usr/bin/env python3
"""hca-live.py — REAL Hypercore GraphQL transport + token lifecycle for LiveBackend.

This is the ONLY module in acos-hypercore-ask that imports a network library. It is
imported LAZILY by hca-adapter.LiveBackend (inside its methods), so the adapter module
itself stays network-import-free and the FixtureBackend path can never reach a socket.

What lives here:
  - `TokenManager`     : 3-step JWT lifecycle (fetch / cache-with-expiry / auto-refresh).
  - `GraphQLTransport` : stdlib urllib over HTTPS with TLS >= 1.2 enforced; POST
                         {query, variables}; parse {data, errors}; surface GraphQL errors.
  - `assert_query_only`: hard operation-level READ-ONLY guard — refuses any operation
                         text that is a `mutation` or `subscription`.
  - `LiveGraphQLClient`: composes the two; exposes query(), single-entity, and a
                         offset-pagination walker that fetches to COMPLETION.
  - `SchemaIndex`      : in-memory index over the introspected schema for field/entity
                         validation BEFORE a query is sent (unknown field -> refuse).

Security invariants (memory/decisions/2026-06-18-hca-build-ground-rules.md):
  - Python 3 stdlib ONLY. No third-party deps.
  - NEVER log/print the client secret or any JWT (access or refresh token).
  - TLS 1.2+ enforced on every request (ssl.SSLContext minimum_version = TLSv1_2).
  - READ-ONLY: only GraphQL `query` operations are ever sent; mutations/subscriptions
    are refused at the operation level in addition to the contract having no mutating
    methods.
  - Degradation: missing creds / auth failure / network error -> structured error or
    the NO_LIVE_DATA envelope; NEVER fabricated data.

Pagination model (verified live 2026-06-18): OFFSET-based. List queries take
`skip: Int` + `limit: Int` and return `Paginated*` = { totalFilteredRecords, pageItems }.
Completeness = walk skip += limit until len(accumulated) >= totalFilteredRecords.
"""

from __future__ import annotations

import json
import re
import ssl
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Optional


# ---------------------------------------------------------------------------
# Errors (structured; never carry a secret/token)
# ---------------------------------------------------------------------------

class LiveAuthError(RuntimeError):
    """Token exchange / refresh failed (HTTP, network, or missing accessToken)."""


class LiveTransportError(RuntimeError):
    """Network / HTTP / TLS error talking to the GraphQL endpoint."""


class GraphQLError(RuntimeError):
    """The GraphQL response carried `errors` (surfaced structurally, never fabricated)."""

    def __init__(self, message: str, errors: Optional[list] = None):
        super().__init__(message)
        self.errors = errors or []


class LiveServerError(LiveTransportError):
    """An HTTP 5xx (e.g. the intermittent 500 the resolver returns). Carries the status code
    so the shared retry helper can decide whether to retry vs surface. After the retry budget
    is exhausted this is what the caller sees (and turns into a structured 500 refusal)."""

    def __init__(self, message: str, status: int):
        super().__init__(message)
        self.status = status


class ReadOnlyViolation(RuntimeError):
    """An operation that is not a `query` (i.e. a mutation/subscription) was attempted."""


class SchemaValidationError(RuntimeError):
    """A requested entity / field is not present in the introspected schema."""


# ---------------------------------------------------------------------------
# Operation-level READ-ONLY guard
# ---------------------------------------------------------------------------

# Match a leading operation keyword. Anonymous `{ ... }` shorthand is a query by spec.
_OP_KEYWORD_RE = re.compile(r"\b(query|mutation|subscription)\b", re.IGNORECASE)


def _strip_graphql_noise(text: str) -> str:
    """Remove string literals, block strings, and # comments so keyword scanning of the
    operation text cannot be fooled by a field/alias literally named e.g. 'mutation'."""
    # block strings \"\"\" ... \"\"\"
    text = re.sub(r'"""(?:.|\n)*?"""', " ", text)
    # ordinary string literals "..."
    text = re.sub(r'"(?:\\.|[^"\\])*"', " ", text)
    # line comments
    text = re.sub(r"#[^\n]*", " ", text)
    return text


def assert_query_only(operation_text: str) -> None:
    """HARD read-only guard. Refuse anything that is not a pure `query`.

    Rules:
      - Anonymous `{ ... }` shorthand (no leading keyword) -> allowed (it's a query).
      - First operation keyword MUST be `query`.
      - The presence of ANY `mutation`/`subscription` operation keyword -> refuse.
    """
    cleaned = _strip_graphql_noise(operation_text)
    keywords = [m.group(1).lower() for m in _OP_KEYWORD_RE.finditer(cleaned)]
    for kw in keywords:
        if kw in ("mutation", "subscription"):
            raise ReadOnlyViolation(
                f"refused: operation contains a {kw!r} operation; this client is "
                f"READ-ONLY and sends GraphQL queries only"
            )
    # If a leading keyword exists it must be `query`; bare `{...}` (no keyword) is fine.
    stripped = cleaned.lstrip()
    if stripped[:1] not in ("{", ""):  # has a leading word
        first = _OP_KEYWORD_RE.match(stripped)
        if first and first.group(1).lower() != "query":  # pragma: no cover (caught above)
            raise ReadOnlyViolation(
                "refused: leading operation is not a `query`; client is READ-ONLY"
            )
        if not first:
            # a leading word that isn't query/mutation/subscription and isn't `{` —
            # not a valid operation we will send.
            raise ReadOnlyViolation(
                "refused: operation does not begin with `query` or `{`; client is READ-ONLY"
            )


# ---------------------------------------------------------------------------
# Shared retry policy for intermittent HTTP 5xx
# ---------------------------------------------------------------------------
# The Hypercore API returns sporadic HTTP 500s on several read paths (loan(id), the
# transaction-preview / payoff resolvers, and — observed under load — even bulk loans pages).
# EVERY live read funnels through GraphQLTransport.execute, so retry lives THERE: that single
# choke point covers single-record reads, the offset-pagination walker, raw_query (used by
# hca-figures + hca-analyze bulk fetch + hca-kg joins). After the budget is exhausted the
# transport raises LiveServerError, which each caller renders as a structured 500 REFUSAL —
# never a fabricated value.

RETRY_ATTEMPTS = 3          # total attempts (1 initial + up to 2 retries)
RETRY_BACKOFF_S = 0.5       # linear backoff base: sleep backoff_s * attempt_index
RETRYABLE_STATUSES = frozenset({500, 502, 503, 504})


# ---------------------------------------------------------------------------
# TLS-enforced HTTP POST helper
# ---------------------------------------------------------------------------

def _tls12_context() -> "ssl.SSLContext":
    ctx = ssl.create_default_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx


def _http_post_json(url: str, payload: dict, headers: Optional[dict] = None,
                    *, timeout: int = 60,
                    opener: Optional[Callable] = None) -> tuple[int, dict]:
    """POST JSON over HTTPS (TLS>=1.2). Returns (status, parsed_json).

    `opener` (test seam): a callable(url, data, headers, method, timeout) -> (status, body_str)
    used by unit tests to mock the network. When None, the real urllib path runs.
    """
    body = json.dumps(payload).encode()
    h = {"accept": "application/json", "content-type": "application/json"}
    if headers:
        h.update(headers)
    if opener is not None:
        status, text = opener(url=url, data=body, headers=h, method="POST", timeout=timeout)
        # Normalize a 5xx returned by the test seam into the SAME signal the real urllib path
        # produces (urlopen raises HTTPError on 5xx) so retry behavior is identical in tests.
        if isinstance(status, int) and status in RETRYABLE_STATUSES:
            raise LiveServerError(f"HTTP {status} from {url}", status=status)
        return status, json.loads(text)
    req = urllib.request.Request(url, data=body, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=_tls12_context()) as r:
        return r.status, json.loads(r.read().decode())


def _post_json_with_retry(url: str, payload: dict, headers: Optional[dict] = None, *,
                          timeout: int = 60, opener: Optional[Callable] = None,
                          attempts: int = RETRY_ATTEMPTS,
                          backoff_s: float = RETRY_BACKOFF_S,
                          sleep: Optional[Callable[[float], None]] = None
                          ) -> tuple[int, dict]:
    """POST JSON with bounded retry on intermittent HTTP 5xx.

    Retries up to `attempts` total on a retryable 5xx (raised HTTPError OR a 5xx returned by
    the opener seam, both normalized to LiveServerError), with linear backoff. Non-5xx HTTP
    errors and transport/network errors are NOT retried — they surface immediately (we never
    burn the budget on a deterministic failure). After the budget is exhausted, the LAST 5xx
    LiveServerError propagates so the caller can REFUSE while stating the 500.
    """
    _sleep = sleep or time.sleep
    last_exc: Optional[Exception] = None
    n = max(1, int(attempts))
    for i in range(1, n + 1):
        try:
            return _http_post_json(url, payload, headers=headers, timeout=timeout,
                                   opener=opener)
        except urllib.error.HTTPError as e:
            if e.code in RETRYABLE_STATUSES:
                last_exc = LiveServerError(f"GraphQL HTTP {e.code} {e.reason}", status=e.code)
                if i < n:
                    _sleep(backoff_s * i)
                    continue
                raise last_exc from None
            # non-retryable HTTP error -> surface immediately (e.g. 401 handled by caller, 4xx)
            raise
        except LiveServerError as e:
            last_exc = e
            if i < n:
                _sleep(backoff_s * i)
                continue
            raise
    # Unreachable, but keep the type-checker happy.
    if last_exc:
        raise last_exc
    raise LiveTransportError("retry loop exited without a result")  # pragma: no cover


# ---------------------------------------------------------------------------
# Token lifecycle
# ---------------------------------------------------------------------------

class TokenManager:
    """3-step JWT lifecycle with in-memory caching + auto-refresh.

    - fetch: POST {clientId, secret} -> {accessToken, expiresIn, refreshToken}
    - cache: keep accessToken + computed expiry (from response expiresIn; trust_response_expiry)
    - refresh: ~`refresh_skew_seconds` before expiry, POST {refreshToken} with
               Authorization: Bearer <accessToken> to the refresh URL. On failure, full re-auth.

    NEVER logs/prints the secret, accessToken, or refreshToken.
    """

    def __init__(self, *, token_url: str, refresh_url: str,
                 client_id: str, client_secret: str,
                 refresh_skew_seconds: int = 60,
                 timeout: int = 45,
                 opener: Optional[Callable] = None,
                 now: Optional[Callable[[], float]] = None):
        if not client_id or not client_secret:
            raise LiveAuthError("missing CLIENT_ID / client secret in environment")
        self._token_url = token_url
        self._refresh_url = refresh_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._skew = max(0, int(refresh_skew_seconds))
        self._timeout = timeout
        self._opener = opener
        self._now = now or time.time
        # cached state
        self._access: Optional[str] = None
        self._refresh: Optional[str] = None
        self._expires_at: float = 0.0

    # --- public ------------------------------------------------------------
    def access_token(self) -> str:
        """Return a valid access token, fetching/refreshing as needed. Never logs it."""
        if self._access is None:
            self._full_auth()
        elif self._now() >= (self._expires_at - self._skew):
            self._refresh_or_reauth()
        return self._access  # type: ignore[return-value]

    def invalidate(self) -> None:
        """Drop cached tokens (e.g. after a 401) to force a fresh full auth next call."""
        self._access = None
        self._refresh = None
        self._expires_at = 0.0

    # --- internals ---------------------------------------------------------
    def _apply_token_response(self, tok: dict) -> None:
        access = tok.get("accessToken")
        if not access:
            raise LiveAuthError(
                f"token response missing accessToken (keys present: {sorted(tok.keys())})"
            )
        self._access = access
        self._refresh = tok.get("refreshToken")
        # trust_response_expiry: derive TTL from response; default conservatively if absent.
        try:
            expires_in = int(tok.get("expiresIn") or 0)
        except (TypeError, ValueError):
            expires_in = 0
        if expires_in <= 0:
            expires_in = 300  # conservative fallback; we still re-auth on 401
        self._expires_at = self._now() + expires_in

    def _full_auth(self) -> None:
        try:
            status, tok = _http_post_json(
                self._token_url,
                {"clientId": self._client_id, "secret": self._client_secret},
                timeout=self._timeout, opener=self._opener,
            )
        except LiveServerError as e:
            # A 5xx during token exchange is an auth failure (we cannot get a token);
            # never echo the secret/token — only the status code.
            raise LiveAuthError(f"token exchange HTTP {e.status}") from None
        except urllib.error.HTTPError as e:
            raise LiveAuthError(f"token exchange HTTP {e.code} {e.reason}") from None
        except (urllib.error.URLError, OSError, ssl.SSLError, ValueError) as e:
            raise LiveAuthError(f"token exchange failed: {type(e).__name__}") from None
        self._apply_token_response(tok)

    def _refresh_or_reauth(self) -> None:
        if not self._refresh or not self._access:
            self._full_auth()
            return
        try:
            status, tok = _http_post_json(
                self._refresh_url,
                {"refreshToken": self._refresh},
                headers={"Authorization": f"Bearer {self._access}"},
                timeout=self._timeout, opener=self._opener,
            )
            self._apply_token_response(tok)
        except Exception:
            # Any refresh failure -> fall back to a full re-auth (never fabricate a token).
            self.invalidate()
            self._full_auth()


# ---------------------------------------------------------------------------
# Schema index (field/entity validation BEFORE sending)
# ---------------------------------------------------------------------------

class SchemaIndex:
    """Index over a stored introspection result for pre-send field/entity validation."""

    def __init__(self, introspection: dict):
        schema = (introspection.get("data") or {}).get("__schema") or {}
        self._types = {t["name"]: t for t in schema.get("types", []) if t.get("name")}
        self.query_type = (schema.get("queryType") or {}).get("name")
        self.mutation_type = (schema.get("mutationType") or {}).get("name")
        qt = self._types.get(self.query_type or "", {})
        self._query_fields = {f["name"]: f for f in (qt.get("fields") or [])}

    # --- type ref helpers --------------------------------------------------
    @staticmethod
    def _named(type_ref: dict) -> Optional[str]:
        cur = type_ref
        while cur:
            if cur.get("kind") not in ("NON_NULL", "LIST"):
                return cur.get("name")
            cur = cur.get("ofType")
        return None

    def has_query_field(self, name: str) -> bool:
        return name in self._query_fields

    def query_field_return_type(self, name: str) -> Optional[str]:
        f = self._query_fields.get(name)
        return self._named(f["type"]) if f else None

    def object_field_names(self, type_name: str) -> set:
        t = self._types.get(type_name) or {}
        return {f["name"] for f in (t.get("fields") or [])}

    def item_type_of_paginated(self, paginated_type: str) -> Optional[str]:
        """For a Paginated* type, return the element type behind `pageItems`."""
        t = self._types.get(paginated_type) or {}
        for f in (t.get("fields") or []):
            if f["name"] == "pageItems":
                return self._named(f["type"])
        return None

    def validate_fields(self, type_name: str, fields: list) -> None:
        """Refuse if any requested field is absent from the type (do NOT send)."""
        known = self.object_field_names(type_name)
        if not known:
            raise SchemaValidationError(
                f"type {type_name!r} not found in introspected schema (cannot validate fields)"
            )
        unknown = [f for f in fields if f not in known]
        if unknown:
            raise SchemaValidationError(
                f"unknown field(s) {unknown} on type {type_name!r} — refusing to send "
                f"(known fields include: {sorted(known)[:8]}...)"
            )

    def type_descriptor(self, type_name: str) -> dict:
        """Return the introspected type entry (for get_schema)."""
        t = self._types.get(type_name)
        if t is None:
            raise SchemaValidationError(f"type {type_name!r} not in introspected schema")
        return t


# ---------------------------------------------------------------------------
# GraphQL transport (read-only)
# ---------------------------------------------------------------------------

class GraphQLTransport:
    """POST GraphQL queries to the endpoint with a Bearer token; parse {data, errors}."""

    def __init__(self, *, gql_url: str, token_manager: TokenManager,
                 timeout: int = 60, opener: Optional[Callable] = None,
                 retry_attempts: int = RETRY_ATTEMPTS,
                 retry_backoff_s: float = RETRY_BACKOFF_S,
                 sleep: Optional[Callable[[float], None]] = None):
        self._gql_url = gql_url
        self._tokens = token_manager
        self._timeout = timeout
        self._opener = opener
        self._retry_attempts = int(retry_attempts)
        self._retry_backoff_s = float(retry_backoff_s)
        self._sleep = sleep

    def _post(self, payload: dict, headers: dict) -> tuple:
        return _post_json_with_retry(
            self._gql_url, payload, headers=headers, timeout=self._timeout,
            opener=self._opener, attempts=self._retry_attempts,
            backoff_s=self._retry_backoff_s, sleep=self._sleep)

    def execute(self, query: str, variables: Optional[dict] = None) -> dict:
        """Run a READ-ONLY query. Returns the `data` object. Raises on errors.

        Read-only is enforced at the operation level here, BEFORE any network call. Every
        request is wrapped in the shared 5xx-retry helper (the API returns intermittent HTTP
        500s); a 401 still triggers exactly one cached-token drop + re-auth. After the 5xx
        retry budget is exhausted a LiveServerError propagates (caller renders a 500 refusal).
        """
        assert_query_only(query)  # hard guard: refuse mutation/subscription text
        payload = {"query": query, "variables": variables or {}}
        token = self._tokens.access_token()
        headers = {"Authorization": f"Bearer {token}"}
        try:
            status, res = self._post(payload, headers)
        except urllib.error.HTTPError as e:
            # On 401, drop cached token once and retry a single time with a fresh auth.
            if e.code == 401:
                self._tokens.invalidate()
                token = self._tokens.access_token()
                headers = {"Authorization": f"Bearer {token}"}
                try:
                    status, res = self._post(payload, headers)
                except Exception as e2:
                    raise LiveTransportError(
                        f"GraphQL request failed after re-auth: {type(e2).__name__}"
                    ) from None
            else:
                raise LiveTransportError(f"GraphQL HTTP {e.code} {e.reason}") from None
        except LiveServerError:
            # 5xx survived the retry budget — surface it so the caller refuses, stating the 500.
            raise
        except (urllib.error.URLError, OSError, ssl.SSLError, ValueError) as e:
            raise LiveTransportError(f"GraphQL transport error: {type(e).__name__}") from None

        if res.get("errors"):
            # Surface GraphQL errors structurally; never fabricate a fallback result.
            msgs = "; ".join(str(e.get("message")) for e in res["errors"])[:400]
            raise GraphQLError(f"GraphQL errors: {msgs}", errors=res["errors"])
        if "data" not in res:
            raise GraphQLError("GraphQL response missing `data`", errors=[])
        return res["data"]


# ---------------------------------------------------------------------------
# High-level client: single-entity read + offset-pagination walker
# ---------------------------------------------------------------------------

# Entity registry: maps adapter entity_type -> GraphQL query field names + return types
# + the field set the LiveBackend selects + variable type declarations for list queries.
# Verified against the live full introspection (2026-06-18).
ENTITY_REGISTRY: dict = {
    "loan": {
        "single_query": "loan",
        "single_return": "Loan",
        "list_query": "loans",
        "paginated_return": "PaginatedLoans",
        "item_type": "Loan",
        "default_fields": ["id", "refId", "name", "status", "commitment",
                           "startDate", "endDate"],
        # GraphQL variable declarations for the list query (offset pagination).
        "list_var_decls": "$skip: Int, $limit: Int, $filter: LoansFilterInput, "
                          "$sortBy: LoansSortByInput",
        "list_arg_passing": "skip: $skip, limit: $limit, filter: $filter, sortBy: $sortBy",
    },
    "client": {
        "single_query": "client",
        "single_return": "Client",
        "list_query": "clients",
        "paginated_return": "PaginatedClients",
        "item_type": "ClientExtended",
        "default_fields": ["id", "type", "displayName", "isActive", "createdAt",
                           "numOfActiveLoans"],
        "list_var_decls": "$skip: Int, $limit: Int, $filter: ClientsFilterInput, "
                          "$sortBy: ClientsSortByInput",
        "list_arg_passing": "skip: $skip, limit: $limit, filter: $filter, sortBy: $sortBy",
    },
    "equity": {
        "single_query": "equity",
        "single_return": "Equity",
        "list_query": "equities",
        "paginated_return": "PaginatedEquity",
        "item_type": "Equity",
        "default_fields": ["id", "refId", "type", "status", "name", "createdAt"],
        "list_var_decls": "$skip: Int, $limit: Int, $filter: EquitiesFilterInput",
        "list_arg_passing": "skip: $skip, limit: $limit, filter: $filter",
    },
    "fundingEntity": {
        "single_query": "fundingEntity",
        "single_return": "FundingEntity",
        "list_query": "fundingEntities",
        "paginated_return": "PaginatedFundingEntities",
        "item_type": "FundingEntity",
        "default_fields": ["id", "name", "totalCommitment", "totalDisbursement",
                           "activeLoansCount"],
        "list_var_decls": "$skip: Int, $limit: Int, $filter: FundingEntitiesFilterInput, "
                          "$sortBy: FundingEntitiesSortByInput",
        "list_arg_passing": "skip: $skip, limit: $limit, filter: $filter, sortBy: $sortBy",
    },
    "loanFunding": {
        "single_query": "loanFunding",
        "single_return": "LoanFunding",
        "list_query": "loanFundings",
        "paginated_return": "PaginatedLoanFundings",
        "item_type": "LoanFunding",
        "default_fields": ["id", "name", "description", "commitmentAmount",
                           "participationPercentage"],
        "list_var_decls": "$skip: Int, $limit: Int, $filter: LoanFundingsFilterInput",
        "list_arg_passing": "skip: $skip, limit: $limit, filter: $filter",
    },
    "loanTransaction": {
        "single_query": "loanTransaction",
        "single_return": "LoanTransaction",
        "list_query": None,    # no top-level paginated list for transactions
        "paginated_return": None,
        "item_type": "LoanTransaction",
        "default_fields": ["id", "date", "type", "outstandingLoanBalance", "note"],
        "list_var_decls": None,
        "list_arg_passing": None,
    },
}

_DEFAULT_PAGE_LIMIT = 50
_MAX_PAGES = 10_000  # safety bound against a server that never reports completion


def _selection_block(fields: list) -> str:
    return " ".join(fields)


class LiveGraphQLClient:
    """Composes TokenManager + GraphQLTransport + SchemaIndex into the read operations
    the LiveBackend needs. All operations are GraphQL `query` only."""

    def __init__(self, *, transport: GraphQLTransport, schema_index: SchemaIndex):
        self._t = transport
        self._schema = schema_index

    # --- single record -----------------------------------------------------
    def get_entity(self, entity_type: str, entity_id: str, *,
                   fields: Optional[list] = None) -> dict:
        reg = ENTITY_REGISTRY.get(entity_type)
        if not reg:
            raise SchemaValidationError(
                f"unknown entity_type {entity_type!r} (known: {sorted(ENTITY_REGISTRY)})"
            )
        qname = reg["single_query"]
        if not self._schema.has_query_field(qname):
            raise SchemaValidationError(
                f"query field {qname!r} absent from introspected schema"
            )
        return_type = reg["single_return"]
        sel = list(fields) if fields else list(reg["default_fields"])
        # Validate fields against the schema BEFORE sending (unknown -> refuse).
        self._schema.validate_fields(return_type, sel)
        op_name = f"HCAGet{return_type}"
        query = (
            f"query {op_name}($id: ID!) {{ "
            f"{qname}(id: $id) {{ {_selection_block(sel)} }} "
            f"}}"
        )
        variables = {"id": entity_id}
        data = self._t.execute(query, variables)
        record = data.get(qname)
        return {
            "record": record,
            "operation_name": op_name,
            "query": query,
            "variables": variables,
            "response_json_path": f"$.data.{qname}",
        }

    # --- paginated list (offset, walked to completion) ---------------------
    def list_entities(self, entity_type: str, *, fields: Optional[list] = None,
                      filter_input: Optional[dict] = None,
                      sort_by: Optional[dict] = None,
                      page_limit: int = _DEFAULT_PAGE_LIMIT) -> dict:
        reg = ENTITY_REGISTRY.get(entity_type)
        if not reg:
            raise SchemaValidationError(
                f"unknown entity_type {entity_type!r} (known: {sorted(ENTITY_REGISTRY)})"
            )
        qname = reg["list_query"]
        if not qname:
            raise SchemaValidationError(
                f"entity_type {entity_type!r} has no top-level paginated list query"
            )
        if not self._schema.has_query_field(qname):
            raise SchemaValidationError(
                f"list query field {qname!r} absent from introspected schema"
            )
        item_type = reg["item_type"]
        sel = list(fields) if fields else list(reg["default_fields"])
        self._schema.validate_fields(item_type, sel)

        op_name = f"HCAList{reg['paginated_return']}"
        var_decls = reg["list_var_decls"]
        arg_passing = reg["list_arg_passing"]
        query = (
            f"query {op_name}({var_decls}) {{ "
            f"{qname}({arg_passing}) {{ "
            f"totalFilteredRecords pageItems {{ {_selection_block(sel)} }} "
            f"}} }}"
        )

        accumulated: list = []
        reported_total: Optional[int] = None
        skip = 0
        pages = 0
        complete = False
        while True:
            pages += 1
            if pages > _MAX_PAGES:
                break
            variables = {"skip": skip, "limit": page_limit,
                         "filter": filter_input, "sortBy": sort_by}
            # drop keys the query doesn't declare (e.g. sortBy when not in var_decls)
            variables = {k: v for k, v in variables.items()
                         if ("$" + k) in (var_decls or "")}
            data = self._t.execute(query, variables)
            page = data.get(qname) or {}
            reported_total = page.get("totalFilteredRecords")
            items = page.get("pageItems") or []
            accumulated.extend(items)
            # Completion: server reports a total and we've reached it, OR the page
            # returned fewer than the requested limit (no more rows server-side).
            if reported_total is not None and len(accumulated) >= reported_total:
                complete = True
                break
            if len(items) < page_limit:
                # short page: if total is unknown we treat exhaustion as complete;
                # if total IS known but we got a short page early, that's a truncation
                # signal -> complete stays False (caller's completeness gate must catch).
                complete = (reported_total is None) or (len(accumulated) >= (reported_total or 0))
                break
            skip += page_limit

        return {
            "items": accumulated,
            "reported_total": reported_total,
            "fetched": len(accumulated),
            "complete": complete,
            "pages": pages,
            "operation_name": op_name,
            "query": query,
            "variables_template": {"limit": page_limit, "filter": filter_input,
                                   "sortBy": sort_by},
            "response_json_path": f"$.data.{qname}.pageItems",
        }

    # --- schema (introspected type for an entity) --------------------------
    def get_schema(self, entity_type: str) -> dict:
        reg = ENTITY_REGISTRY.get(entity_type)
        if not reg:
            raise SchemaValidationError(
                f"unknown entity_type {entity_type!r} (known: {sorted(ENTITY_REGISTRY)})"
            )
        return self._schema.type_descriptor(reg["single_return"])

    # --- generic read query (thin pass-through to the transport) -----------
    def raw_query(self, query: str, variables: Optional[dict] = None) -> dict:
        """Run an ARBITRARY read-only GraphQL `query` and return its `data` object.

        This is the thin generic seam the higher-level figure/resolver modules
        (hca-figures.py, hca-resolve.py) reuse instead of re-implementing auth +
        transport. It funnels through the SAME GraphQLTransport.execute path, so:
          - `assert_query_only` refuses any mutation/subscription text BEFORE the wire,
          - the 3-step JWT auth + single 401 re-auth retry apply,
          - GraphQL `errors` are surfaced structurally (GraphQLError), never fabricated.

        No schema pre-validation is done here (the caller owns the operation text); the
        operation-level READ-ONLY guard still applies inside the transport. Returns the
        raw `data` dict from the response.
        """
        return self._t.execute(query, variables or {})
