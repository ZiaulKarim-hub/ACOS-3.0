# Hypercore Live API — Discovery Findings (2026-06-18)

Source: `docs.hypercore.ai` (Docusaurus, client-rendered SPA), its `sitemap.xml`, and the
docs `main.*.js` bundle. The rendered page bodies are NOT scrapeable (every path returns
the same ~7.6KB SPA shell); these findings come from the sitemap structure + JS bundle +
web search.

## CONFIRMED
- **API style: GraphQL** (NOT REST). Evidence: schema-doc layout uses
  `queries/ mutations/ objects/ inputs/ enums/ directives/`; the docs JS bundle contains the
  literal endpoint path `/graphql`.
- **Auth: OAuth 2.0 client-credentials grant.** Credentials in Doppler (project `acos-3-0`,
  config `dev`):
  - `CLIENT_ID`  = OAuth client id
  - `HYPERCORE_API_KEY` = OAuth **client secret** (misnamed; recommend rename to
    `HYPERCORE_CLIENT_SECRET` for clarity — adapter will map either name via config).
- **Schema modules (entity catalog)** from sitemap `/docs/api/<module>/`:
  `authentication, change-requests, changelog, clients, common, data-tables, deal-onboarding,
  documents, equities, funding-sources, import, loans, notifications, statements`.
  - Read-relevant for this skill: `loans, clients` (borrowers), `statements, documents,
    equities, funding-sources, data-tables, deal-onboarding, notifications, change-requests`.
- **Docs:** overview `https://docs.hypercore.ai/docs/api` · auth `https://docs.hypercore.ai/docs/api/authentication`.

## IMPLICATIONS FOR THE BUILD (changes vs the REST assumption in the plan)
- **LiveBackend = GraphQL client:** one endpoint, HTTP POST `{query, variables}`. Use ONLY
  `query` operations — NEVER `mutation`. Read-only is now enforceable at the *operation* level
  (assert no mutation is ever sent) in addition to the contract having no mutating methods.
- **Provenance model update:** each delivered value cites
  `{operation_name, query_hash, variables, response_json_path, timestamp}` instead of REST
  `endpoint+params`. Same guarantee, GraphQL-shaped.
- **Pagination:** GraphQL connection/`Paginated*` objects (e.g. `PaginatedChangeRequests`) →
  cursor-based via `pageInfo`/`endCursor`. Completeness gate follows cursors until `hasNextPage=false`.
- **get_schema():** use GraphQL **introspection** as the authoritative schema source (better than docs).
- **Fixtures/schemas:** the foundation's placeholder REST fixtures + `*.schema.json` will be
  REPLACED with real introspected types + captured query responses. The adapter CONTRACT and its
  31 tests are unaffected (backend-agnostic) — only the stubbed LiveBackend internals + fixtures change.

## STILL NEEDED (from user's browser OR via one live introspection call)
1. **GraphQL endpoint host** — path is `/graphql`; host unknown (likely `api.hypercore.ai` or
   `app.hypercore.ai`). → value for `HYPERCORE_BASE_URL`.
2. **OAuth token endpoint URL** — where `CLIENT_ID` + secret are exchanged for an access token.
3. **Token exchange details** — body params vs HTTP Basic; any `scope`/`audience`; token TTL;
   the request header format for API calls (expected `Authorization: Bearer <token>`).
4. Once (1)+(2) known and creds in Doppler: run a **GraphQL introspection query** (read-only) to
   pull the full authoritative schema, then capture 2-3 de-identified sample responses per entity
   to replace placeholder fixtures.
