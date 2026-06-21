# slice-02-cache-fetch-posture — Cache + fetch + scraping posture

- **Parent story:** STORY-APS-02 · **Parent epic:** EPIC-APS-02 · **Demo:** -
- **Effort:** M · **Dependency order:** 3 · **Depends on:** slice-01-scaffold-compliance-gate
- **Lattice refs:** cq-18, meth-cache, ent-cacheentry, std-scraping, metric-freshttl, risk-block

## PM Section (Planner / Specifier — LCE)

### Objective
Implement `cache.py`: a JSON cache with **freshness TTLs** that wraps **every** external lookup, keyed by
person / entity / address / parcel / query. It must survive 403s and rate limits, make re-runs cheap and
resumable, and surface **per-record freshness stamps**. Enforce the scraping posture (public no-login pages
only; respect robots / rate limits; per-datum provenance).

### Scope
**In scope:** `scripts/cache.py` (`get_or_fetch(key, fetch_fn, ttl_days)`; freshness/staleness derivation;
403/rate-limit handling; per-record `fetched_at` + `source_url` stamps); posture helper (gate to public
no-login pages; honor a robots/rate-limit policy).
**Out of scope:** any specific channel/source (slice-05); the graph (slice-04).

### Guardrails / Allowed files
- `.claude/skills/acos-property-search/scripts/cache.py` (stdlib only)
- `.claude/skills/acos-property-search/scripts/tests/test_cache.py`
- this task file + `.acos/evidence/[DATE]/slice-02-cache-fetch-posture/`
- Prohibited: any paid-API call; bypassing the compliance gate; logging unnecessary PII into cache payloads.

### Definition of Done
- [ ] A second identical lookup within TTL is served from cache (no re-fetch) — pass-condition: cache-hit test (fetch_fn called once).
- [ ] A lookup past its TTL is marked stale and re-fetched — pass-condition: staleness test.
- [ ] A 403 / rate-limit is captured as a cache `status` without crashing the run — pass-condition: block-resilience test (re-author a 403 fixture).
- [ ] Every cache entry carries `fetched_at` + `source_url` (freshness stamp surfaces later) — pass-condition: stamp test.
- [ ] No external lookup proceeds while `COMPLIANCE_BLOCKED` — pass-condition: gate-respect test.
- [ ] `## Dev Learnings` / `## QA Learnings` updated.

## Dev Section (Executor)

### Approach
1. Implement a deterministic JSON cache keyed by a canonical lookup key; store `payload`, `fetched_at`,
   `ttl_days`, `status`, `source_url`.
2. `get_or_fetch`: on hit-within-TTL return cached; else call `fetch_fn`, record status (ok/403/
   rate-limited), stamp, persist.
3. Posture helper rejects login-gated/paid endpoints; honors a rate-limit policy.
4. Tests: hit-within-TTL, stale-refetch, 403 resilience, stamp presence, gate respect.

### Dev Evidence Bundle (7 parts — required)
Summary; Traceability (meth-cache, std-scraping, EV-019, NFR-Resilience); Quality (stdlib); Functional (the
five DoD tests); Security/Compliance (no PII beyond need; gate respected); Operational (resumability);
Self-assessment.

### Dev Learnings
- (fill at execution) Cache-key canonicalization gotchas; how staleness is computed deterministically.

## QA Section (Zero-Trust Verifier)

### Verification steps
1. Re-author a 403 fixture; confirm the run records the status and continues (no crash, no fabricated data).
2. Independently verify a hit-within-TTL does not call `fetch_fn` a second time.
3. Confirm freshness stamps exist on every entry.
4. Confirm a lookup is refused while `COMPLIANCE_BLOCKED`.

### Evidence gates (all must pass)
- [ ] 403 / rate-limit resilience proven (re-authored fixture).
- [ ] Cache-hit suppresses re-fetch; stale triggers re-fetch.
- [ ] Freshness stamps present.
- [ ] Compliance-gate respected by the cache layer.
- [ ] Learnings updated.

### QA Learnings
- (fill at execution) Any way to get a lookup past the gate via the cache.
