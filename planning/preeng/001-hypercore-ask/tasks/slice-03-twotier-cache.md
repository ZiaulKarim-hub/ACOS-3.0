# slice-03-twotier-cache — Two-tier data model + raw-response cache

- **Parent story:** STORY-HCA-03 · **Parent epic:** EPIC-HCA-03 · **Demo:** -
- **Effort:** L · **Dependency order:** 4 · **Depends on:** slice-02-adapter
- **Lattice refs:** meth-twotier, proc-cache, ent-rawresp, ent-normrec, meth-normalize, cq-14, cq-03

## PM Section (Planner / Specifier — LCE)

### Objective
Implement the two-tier data model: **Tier-1 `RawApiResponse` cache** = immutable source of truth keyed for provenance lookup, and the **Tier-2 `NormalizedAnswerRecord`** derived view where every normalized field carries a back-pointer (`raw_response_id` + `json_field_path`) to its Tier-1 source. This is what makes provenance structurally guaranteed (LEARN-ARCH-002).

### Scope
**In scope:** `hca-cache.py` (persist/lookup Tier-1 records keyed by `raw_response_id`; immutable once written); `hca-normalize.py` (build Tier-2 records from Tier-1, typed projection, with per-field bindings — unit/currency normalization wiring stubbed here, fully implemented in slice-05); the cache store on disk (AES-256-at-rest noted as posture TODO).
**Out of scope:** provenance refusal logic (slice-04), the gate suite math (slice-05), consensus.

### Guardrails / Allowed files
- `.claude/scripts/hca-cache.py` (Tier-1 store; stdlib only)
- `.claude/scripts/hca-normalize.py` (Tier-2 derivation + field bindings)
- cache dir under `.acos/state/hca-cache/` (git-ignored; PII-minimized)
- tests: `.claude/scripts/tests/test_hca_cache.py`, `test_hca_normalize.py`
- this task file + `.acos/evidence/[DATE]/slice-03-twotier-cache/`
- Prohibited: mutating Tier-1 records after write; storing PII beyond need; persisting secrets.

### Definition of Done
- [ ] Tier-1 cache writes immutable `RawApiResponse` records (re-write of same key is rejected or no-op) and looks them up by `raw_response_id` — pass-condition: immutability + lookup tests pass.
- [ ] Tier-2 `NormalizedAnswerRecord` built from Tier-1 with `field_bindings` mapping each field -> `{raw_response_id, json_field_path}` and `derived_from[]` — pass-condition: every normalized field resolves back to a Tier-1 record (binding-resolution test).
- [ ] Each agent can be handed a **minimal Tier-1 slice** (scoping helper) rather than the full cache — artifact: scoping helper + test (PII/token minimization).
- [ ] Cache is durable/resumable (re-run finds prior Tier-1 without re-fetch) — pass-condition: resume test.
- [ ] `## Dev Learnings` / `## QA Learnings` updated.

## Dev Section (Executor)

### Approach
1. `hca-cache.py`: write-once JSON store keyed by `raw_response_id`; reject silent overwrite; provide `get(raw_response_id)` and `put(raw_api_response)`.
2. `hca-normalize.py`: walk a Tier-1 body, project typed fields, record `json_field_path` for each (e.g. `$.data[3].outstanding_principal`), set `derived_from`.
3. Scoping helper: extract the minimal Tier-1 slice for a given value/question.
4. Tests: immutability, lookup, binding resolution, scoping, resume.

### Dev Evidence Bundle (7 parts — required)
Summary; Traceability (M8 two-tier, NFR-Resilience durable, cq-14/03); Code Quality (stdlib, immutability); Functional (5 tests); Security (PII-minimized cache, no secrets); Operational (resume); Self-assessment.

### Dev Learnings
- Built `hca-cache.py` (Tier-1 immutable store + `TwoTierCache` facade) and `hca-normalize.py` (Tier-2 derivation). Tier-1 records are content-addressed by a STABLE id (`compute_raw_response_id(operation_name, variables)`) — NOT by the live `raw_response_id`, which embeds `fetched_at` and changes every fetch. The stable id is what makes durability/resume work: a re-fetch of the same query maps to the same key.
- Immutability is enforced as: re-`put` of an existing key with DIFFERENT content -> `ImmutableCacheError`; IDENTICAL content -> idempotent no-op (so resume never errors). Atomic tmp+rename write so a crash never leaves a half record. The store class has NO update/delete/mutate verb (append-only by omission), guarded by a test.
- Tier-1 body comes in THREE shapes that all needed handling: GraphQL list (`body.data[i]`), GraphQL single (`body.record`), and legacy REST (`body` IS the record). The normalizer + the json-path base differ per shape; `_items_and_base()` centralises this.
- Freshness window is per entity-CLASS (`balances_servicing`/`payments_drawdowns`/`reference_static`), read from `config.yaml` with a stdlib scan (no YAML lib). Unknown entity types fall back to the SHORTEST window so we always err toward refetch, never toward serving stale.
- `read_fresh()` never serves stale silently: stale -> refetch via a caller-supplied `refetcher` closure (or a live adapter); if no refetch is possible it RAISES `StaleRefusedError` with an envelope whose `data` is always `None`. A bare adapter cannot self-refetch (it has no entity id), so we force a refusal rather than guess.
- PII minimization lives in the DERIVED view only: contact-PII fields (email/mobile/identificationNumber/...) are dropped from Tier-2 `fields` (recorded in `_pii_minimized`); the raw value still lives in Tier-1 for need-to-know drill-down. The minimal-slice helper returns ONLY requested fields from at most N records (never a full-cache dump) and carries per-field json paths so an agent can still cite provenance.
- Cache dir `.acos/state/hca-cache/` is git-ignored two ways: the repo `.gitignore` (and the user global `~/.config/git/ignore`) ignore `.acos/`, AND the store drops a defensive `*` `.gitignore` into the cache dir on first write. Verified via `git check-ignore` on a real cached file. The optional live capture cached a REAL 141-loan response there and `git status` shows zero visible paths under the cache dir.

## QA Section (Zero-Trust Verifier)

### Verification steps
1. Attempt to mutate a written Tier-1 record via the API; confirm it is rejected (immutability).
2. For a sample Tier-2 record, independently resolve every `field_bindings` entry back to a real Tier-1 record + verify the `json_field_path` actually points at the value — any unresolvable binding = REJECT.
3. Confirm the scoping helper returns only the minimal slice (no full-cache dump, no extra PII).
4. Confirm resume finds cached Tier-1 without re-fetch (durability).

### Evidence gates (all must pass)
- [ ] Tier-1 immutability enforced.
- [ ] **100% of Tier-2 field bindings resolve to a real Tier-1 source + correct path** — fail = REJECT.
- [ ] Minimal-slice scoping verified (PII/token minimization).
- [ ] Resume/durability verified.
- [ ] Learnings updated.

### QA Learnings
- Immutability re-authored as a test: write a Tier-1 record, then attempt to `put` the same key with a mutated `commitment` -> must raise `ImmutableCacheError` AND the original value must be unchanged on read-back. Identical re-put must be a silent no-op (count stays 1). Both pass.
- Binding-resolution hard gate verified independently of the normalizer: `verify_bindings_against_tier1()` walks EVERY `field_bindings` entry, resolves it in the real Tier-1 record, and compares the value — any unresolvable path OR value mismatch fails the whole record (`ok=False`). Tested on a 2-record list (>=6 bindings checked) and on a deliberately corrupted path (must fail).
- Scoping helper verified to be minimal: requesting `["id","numOfActiveLoans"]` returns ONLY those keys (email/identificationNumber absent), and a slice over `hca:s1` does not leak `hca:s2` anywhere in its JSON. `max_records` caps a 5-item list to 2.
- Freshness refusal verified: a loan (1-day window) stamped `2024-01-01` with no refetcher raises `StaleRefusedError` and the envelope `data` is `None` (stale value NEVER returned, `refetch_attempted=False`). An absent record -> `NO_LIVE_DATA`. A not-live adapter -> still refuses. A stale record WITH a refetcher gets the fresh record (and it lands in cache).
- Durability verified by constructing a SECOND `TwoTierCache` over the same dir (simulating a new process) and finding the prior Tier-1 without re-fetch; a fresh record + a counting refetcher proves zero refetch calls when fresh.
- Git-ignore gate verified mechanically with `subprocess` + `git check-ignore` on a probe path inside the default cache dir (rc 0 = ignored = pass). Independently re-checked the REAL cached live-capture file: ignored, zero git-visible paths under the cache dir.
