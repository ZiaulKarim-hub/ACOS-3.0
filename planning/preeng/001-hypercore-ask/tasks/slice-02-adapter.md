# slice-02-adapter — Hypercore client/adapter contract + fixture/mock backend (stubbed-until-access)

- **Parent story:** STORY-HCA-02 · **Parent epic:** EPIC-HCA-02 · **Demo:** -
- **Effort:** L · **Dependency order:** 3 · **Depends on:** slice-01-scaffold
- **Lattice refs:** meth-adapter, std-readonly, pat-fixturefirst, meth-degrade, term-nolivedata, risk-apiunknown, std-tls, std-secretstore, cq-01, cq-10, cq-11

## PM Section (Planner / Specifier — LCE)

### Objective
Define the **only** module that talks to Hypercore: a stable, **read-only** adapter contract with a `FixtureBackend` (active now) and a stubbed `LiveBackend` (TODO). Absence of credentials must degrade to an explicit `NO_LIVE_DATA` state — never fabricate. This is the pillar that makes the whole skill buildable before API access.

### Scope
**In scope:** the adapter contract surface (`is_live`, `get_entity`, `list_entities`, `get_schema`, `subscribe_events`) per tech_prd §2; `FixtureBackend` serving canned `RawApiResponse` JSON from `fixtures/`; `LiveBackend` raising `NotImplementedError("Hypercore live backend TODO — access not yet provisioned")`; `NoLiveDataError`; backend selection from `config.yaml`/env; a read-only **guard test** asserting no mutating verb is callable; the initial fixture set.
**Out of scope:** real endpoints/auth (TBD until access — stub behind contract); cache persistence (slice-03); gates/consensus.

### Guardrails / Allowed files
- `.claude/scripts/hca-adapter.py` (contract + FixtureBackend + stubbed LiveBackend + NoLiveDataError; stdlib only)
- `.claude/skills/acos-hypercore-ask/fixtures/*.json` (canned RawApiResponse records for every modeled entity A1–A11; include one paginated-list fixture, one deliberately-truncated, one stale, one drifted — to be exercised by later slices)
- `.claude/skills/acos-hypercore-ask/schemas/*.json` (expected entity schemas — created here, validated in slice-05)
- tests: `.claude/scripts/tests/test_hca_adapter.py` (stdlib `unittest`, incl. the read-only guard test)
- this task file + `.acos/evidence/[DATE]/slice-02-adapter/`
- Prohibited: ANY `create_*`/`update_*`/`delete_*`/`post_*`/`put_*`/`patch_*` method on the contract; any real network call; any credential in repo.

### Definition of Done
- [ ] Adapter exposes exactly the read-only contract surface; **no mutating method exists** — pass-condition: read-only guard test asserts no mutating verb is callable (REQUIRED gate; M5/NFR-Read-only).
- [ ] `FixtureBackend` returns well-formed `RawApiResponse`-shaped dicts (`endpoint`, `request_params`, `timestamp`, `http_status`, `cursor`, `reported_total`, `body`, `backend: "fixture"`) for each modeled entity — artifact: `fixtures/` + passing adapter test.
- [ ] `is_live()` returns false absent creds; requesting live data while not live raises/returns `NoLiveDataError` cleanly (M6/M7) — pass-condition: degradation test passes.
- [ ] `LiveBackend` is import-safe but raises the documented `NotImplementedError` if invoked (stubbed-until-access) — pass-condition: stub test passes.
- [ ] Backend is selectable via config/env; default `fixture` — pass-condition: config-driven selection test.
- [ ] Adversarial fixtures present (truncated, stale, drifted) for downstream gate slices — artifact check.
- [ ] `## Dev Learnings` / `## QA Learnings` updated.

## Dev Section (Executor)

### Approach
1. Implement the contract as a small class/protocol with read-only methods only; backends implement it.
2. `FixtureBackend` loads JSON from `fixtures/`, wraps each into the RawApiResponse shape with `backend: "fixture"`, supports cursor-based paging from fixture pages.
3. `LiveBackend` stubbed (`NotImplementedError`), gated behind `is_live()` which checks env/secret presence (none now -> false).
4. `NoLiveDataError` raised when live requested and not live.
5. Author expected schemas (slice-05 validates against them) and the adversarial fixtures.
6. Write `unittest` tests incl. the read-only guard (introspect the contract for forbidden verbs).

### Dev Evidence Bundle (7 parts — required)
Summary; Traceability (M5,M6,M7,R1; cq-01/10/11); Code Quality (stdlib, typed shape); Functional (adapter+degradation+guard tests pass); Security (no creds, no network, read-only by omission+guard, TLS-on-live noted as TODO); Operational (backend selection); Self-assessment.

### Dev Learnings
- **Read-only is enforced two ways.** (1) By OMISSION: the abstract `HypercoreBackend`
  declares only `is_live/get_entity/list_entities/get_schema/subscribe_events`; no mutating
  verb exists. (2) By a GUARD TEST that introspects every public method of the base,
  FixtureBackend, LiveBackend, and the public `HypercoreAdapter` against a forbidden-verb
  list, PLUS a `test_contract_surface_is_exactly_the_read_allowlist` that fails if the base
  surface ever drifts from `READ_ONLY_CONTRACT_METHODS`. Negative-tested: adding a hypothetical
  `update_entity` to a subclass makes the guard fire.
- **Avoid `set`/`edit`/`add` as method-name verbs.** The forbidden-verb list includes them, so
  no contract/helper method may be named `set_*`/`add_*`/`edit_*` etc. — would self-trip the
  guard. Kept all surface methods read-named.
- **No network import exists in the module at all.** Rather than guard live HTTP behind a flag,
  there is simply NO `urllib`/`http`/`socket`/`ssl`/`requests` import; LiveBackend's read methods
  raise `NotImplementedError("live wiring pending API discovery")`. So no network call is even
  reachable today. `test_adapter_module_has_no_network_import` checks the import block (not prose).
- **`is_live()` reads BOTH env vars** (`HYPERCORE_API_KEY` + `HYPERCORE_BASE_URL`, names
  configurable). Partial creds -> False. Doppler injects values at runtime; none in repo.
- **Degradation is explicit and structured.** `is_live()==False` + `require_live=True` ->
  `NoLiveDataError` carrying the `NO_LIVE_DATA` envelope with `data: null` — never fabricated.
  Without `require_live`, fixture reads succeed and are stamped `backend: "fixture"`.
- **Config read is stdlib-only.** `_read_config_backend()` scans the `adapter:`/`backend:` line
  by hand (no YAML lib) to stay within the no-third-party-dep rule for one scalar.
- **Cursor paging** keys off each fixture's inbound `request_params.cursor`: null -> page1,
  matching cursor -> next page. The complete pair (page1+page2) reconciles fetched(3)=reported(3);
  the `_truncated` variant deliberately does NOT, for the slice-05 completeness gate.
- 31 tests pass (`Ran 31 tests in 0.001s OK`). Executed 2026-06-18 as part of SLICE-HCA-00..02.

### Dev Learnings — LiveBackend upgrade (2026-06-18, access verified)
- **LiveBackend is now REAL** (GraphQL client), behind the UNCHANGED read-only contract.
  Network code lives in a sibling module `hca-live.py`, imported LAZILY inside LiveBackend
  methods — so `hca-adapter.py` keeps ZERO top-level network imports and the FixtureBackend
  path still cannot reach a socket. `test_adapter_module_has_no_network_import` still passes.
- **Pagination is OFFSET-based, NOT cursor-based** (the big surprise). List queries take
  `skip: Int` + `limit: Int`; `Paginated*` returns `{ totalFilteredRecords, pageItems }`.
  The walker increments `skip += limit` until `len(accumulated) >= totalFilteredRecords`
  and surfaces an explicit `complete: true/false` flag (a short page with a known larger
  total -> `complete: false`, never a silent partial). Live proof: limit=2 walked 71 pages
  to fetch all 141 loans (complete=True); clients walked 62 pages for 124 records.
- **3-step JWT auth verified live.** `expiresIn=1800s`, refreshToken present. TokenManager
  caches in-memory, auto-refreshes ~60s before expiry via the refresh URL (Bearer header +
  `{refreshToken}` body), and falls back to a full re-auth on any refresh failure. NEVER
  logs/prints the secret or any token.
- **Operation-level read-only guard** (`assert_query_only`) refuses any `mutation`/
  `subscription` text BEFORE a network call, ignoring keywords inside string literals/
  comments. Proven live: a real query executed, a mutation was refused with zero HTTP calls.
- **TLS 1.2+** enforced via `ssl.SSLContext.minimum_version = TLSv1_2` on every request.
- **Schema validation before send:** requested fields are checked against the introspected
  type; an unknown field is refused and never sent. `get_schema()` returns the introspected
  GraphQL type for an entity.
- **GraphQL provenance shape:** each record/list carries
  `{operation_name, query, variables(_template), response_json_path, fetched_at}` so Tier-1
  RawApiResponse binds provenance GraphQL-style (endpoint = the /graphql URL; request_params
  = operation + variables; cursor is always null because pagination is offset-based).
- **Step 0 (schema depth):** added `hca-introspect-full.py` (standard full IntrospectionQuery
  with `args`/`inputFields`/`enumValues`, type-ref chain depth 7) and extended
  `hca-schema-digest.py` to emit query args + the pagination/filter/sort INPUT_OBJECT shapes
  (incl. nested `PeriodInput`). `_introspection.json` overwritten; `_schema-digest.md`
  regenerated. Live: 84 query fields, 71 with args, 226 input objects, 130 enums.
- **New GraphQL-shaped fixtures** (camelCase + GraphQL provenance) added alongside (not
  replacing) the pre-access REST fixtures, so the existing green tests stay green:
  `gql_loan__L-GQL-1`, `gql_list_loan__complete`, `gql_list_loan_truncated__short`,
  `gql_client__C-GQL-1`. All marked `_placeholder: true`; client PII fully de-identified
  (synthetic names/email/phone). New live-introspection-derived schema descriptors:
  `loan.gql.schema.json`, `client.gql.schema.json`.
- **59 tests pass** (`Ran 59 tests OK`, up from 31). Executed 2026-06-18.

### QA Learnings — LiveBackend upgrade (2026-06-18)
- Read-only is now enforced THREE ways: contract omission, query-only construction, and
  the operation-level `assert_query_only` guard. Independently verified live that a mutation
  string is refused with zero HTTP calls (`mock.calls == []` in unit test; live test shows
  refusal after a real query succeeded).
- Pagination-completeness: a short page against a known larger total yields `complete: false`
  (surfaced, never silent). The offset walker reconciles fetched vs `totalFilteredRecords`.
- No secret/JWT leak: scanned scripts + evidence + planning for the literal CLIENT_ID value,
  the secret value, and any `eyJ...` JWT pattern — NONE present. The full introspection JSON
  carries schema only (no token). The introspect script prints `list(tok.keys())`, never values.
- TLS >= 1.2 asserted on the transport SSL context (`minimum_version == TLSv1_2`).
- Unit tests mock the HTTP layer (`opener` seam) — NO real network in `unittest`. The live
  proof is isolated to the `--selftest-live` Doppler run captured in the evidence bundle.

## QA Section (Zero-Trust Verifier)

### Verification steps
1. **Independently** introspect `hca-adapter.py` for any method name matching a mutating verb (create/update/delete/post/put/patch/write/mutate); ANY match = REJECT.
2. Grep the module for network imports (`urllib`, `http.client`, `requests`, `socket`); for `FixtureBackend` path there must be no live network call; LiveBackend network code may exist but must be unreachable while `is_live()` is false.
3. Run the test suite; re-author at least the read-only guard test yourself and confirm it fails loudly if a mutating method is added.
4. Confirm `is_live()` is false with no creds, and `NoLiveDataError`/NO_LIVE_DATA path triggers — never a fabricated record.
5. Confirm adversarial fixtures (truncated/stale/drifted) exist and are labeled.

### Evidence gates (all must pass)
- [ ] **Read-only guard test present and passing; no mutating verb callable** — fail = REJECT (hard).
- [ ] FixtureBackend returns RawApiResponse-shaped records with `backend: "fixture"`.
- [ ] No-live-data degradation verified (no fabrication).
- [ ] LiveBackend stub raises documented NotImplementedError.
- [ ] Adversarial fixtures present.
- [ ] Learnings updated.

### QA Learnings
- Independent introspection of `hca-adapter.py` finds NO method name matching
  create/update/delete/post/put/patch/write/mutate (and the broader insert/remove/drop/save/
  upsert/modify/add/set set) on the contract or any backend. Read-only hard gate: PASS.
- Re-authored the read-only guard with an independent forbidden-verb list and confirmed it
  fails loudly when a mutating method is grafted onto a subclass (negative test PASS).
- `grep -E '^\s*(import|from)\s+(urllib|http|socket|requests|ssl)'` over the module: NONE.
  FixtureBackend path has no network call; LiveBackend has no network code at all (only
  `NotImplementedError`) — unreachable-by-construction while is_live() is false. PASS.
- With no creds, `is_live()` is false and `require_live=True` raises `NoLiveDataError` with a
  `NO_LIVE_DATA` envelope (`data: null`) — no fabricated record. PASS.
- `LiveBackend` is import-safe and raises the documented `NotImplementedError` on every read
  method when invoked. PASS.
- Adversarial fixtures present and labeled via `_adversarial`: paginated (`list_loan__page1/2`),
  truncated (`list_loan_truncated__page1`, fetched<reported & cursor null), stale
  (`loan_stale__L-900`, 2024 timestamp), drifted (`loan_drifted__L-901`, renamed/missing/extra
  fields). All fixtures carry the `PLACEHOLDER` marker (synthetic, no PII). PASS.
