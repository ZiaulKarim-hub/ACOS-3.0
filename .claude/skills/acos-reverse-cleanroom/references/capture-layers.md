# Phase 0 — the ADAPTIVE capture layer library (27 layers + always-on probe)

Capture is a layered protocol, not one read. Each layer produces evidence the intent
extractors cite. The library holds **27 layers**; the orchestrator runs an **adaptive
subset** chosen per app to reach `capture.coverage_benchmark` (default `0.99`) of the
app's features + intent — NOT a fixed count (illustratively 7–27, no hardcoded number).
The **server-invisible probe always runs**. The same app is a DIFFERENT app per auth role,
so every observational layer runs per role in the sweep.

Selection is estimate → verify → top-up (inner loop) wrapped in re-run-until-converged
(outer loop). See "Loops" below. 99% is a benchmark to chase, not a guarantee — some
behavior stays `UNKNOWN`, and probed facts stay `inferred`.

---

## Selection protocol (how the orchestrator picks the subset)

1. **Recon.** Run a cheap first pass — layer 1 (structure) + a light layer 2 (behavioral) —
   to build the `surface-census.json` denominator and detect app-shape SIGNALS (roles,
   real-time connections, forms, search, locales, service workers, external scripts, …).
2. **Seed the core.** Always select the `core` layers below, plus the always-on probe. Add
   `core (role-gated)` layers when >1 auth role exists.
3. **Fire conditionals.** For each `conditional` layer, include it only if its trigger signal
   was detected in recon (a layer that can't apply is skipped, not forced).
4. **Top-up to benchmark (INNER LOOP).** Estimate coverage vs the census. While predicted
   coverage < `coverage_benchmark` and the library is not exhausted, add the next-highest-value
   `extended` layer and re-measure.
5. **Converge (OUTER LOOP).** After a full pass, re-run per "Loops" until a fresh pass adds
   nothing material or `capture.max_reruns` is hit.
6. **Record.** Write the selected-layer list + why each was included/skipped into `audit/`.

---

## The 27-layer library

`Sel` = default selection tier: **core** (nearly always), **core*** (core when >1 role),
**cond:<signal>** (only if the signal is detected), **ext** (added while chasing the benchmark).

| # | Layer | How | Catches (uniquely) | Sel |
|---|---|---|---|---|
| 1 | Structure discovery | crawl seeds + mine JS for endpoints/routes | full map + `surface-census.json` — the completeness DENOMINATOR | core |
| 2 | Behavioral capture | Playwright + CDP; record HAR + interaction traces | what the app DOES when driven (provoke states, don't just crawl) | core |
| 3 | Contract inference | `har-to-openapi.ts` (merged: the old standalone 0.2 lives here) | the back-end call contract `contracts.openapi.json` — INFERENCE, exercised endpoints only | core |
| 4 | Source-map extraction | unpack sourcemaps if served | collapses black-box → readable source | cond:sourcemaps-served |
| 5 | Vision capture | screenshot + multimodal describe | the rendered look/layout — ~83–87% element-fidelity ceiling | core |
| 6 | Accessibility tree | `page.accessibility.snapshot` | roles/names/states screenshots can't show | core |
| 7 | Auth-role sweep | anon/user/admin/paid (human-provided storage-state) | that the app differs per role — NEVER automate a login-wall bypass | core* |
| 8 | Client storage & state | read cookies, localStorage/sessionStorage, IndexedDB | what the app persists on-device: tokens, settings, flags | ext |
| 9 | Console & client-error | capture console logs, JS errors, stack traces | hidden error paths + warnings the UI never shows | ext |
| 10 | Third-party dependency | enumerate external scripts/SDKs/CDNs/trackers | outside services a rebuild must replace or re-integrate | cond:external-scripts |
| 11 | Security-surface | read headers (CSP/CORS/auth), cookie flags, rate-limit headers | the defenses a rebuild must reproduce | ext |
| 12 | Real-time transport | detect WebSockets / SSE / long-poll / push | live/streaming features a request log misses | cond:realtime-detected |
| 13 | Data-model / schema | sample real records across list + detail surfaces | the shape of the domain data (what a record contains) | core |
| 14 | Authorization matrix | per role, probe allowed vs denied actions (403s) | the real "who can do what" access rules | core* |
| 15 | Business-rules / validation | probe form limits + calculations (min/max, cross-field, math) | the exact validation + computation logic, VERBATIM to the rule ledger | cond:forms-or-calc |
| 16 | Navigation / state-machine | map journeys + allowed transitions (wizards, guards) | the ORDER + gating of multi-step flows | cond:multistep-flows |
| 17 | Search & query-behavior | exercise search/filter/sort/paginate with varied inputs | ranking, fuzzy match, empty-result handling | cond:search-present |
| 18 | Notification-content | trigger + capture actual emails/SMS/push | WHAT outbound messages say (probe only sees THAT they fire) | cond:outbound-messaging |
| 19 | Internationalization (i18n) | switch language/currency/timezone/RTL | which strings are translated; date/money/format/RTL behavior | cond:multi-locale |
| 20 | Device / responsive matrix | many viewports, touch, dark mode, print, reduced-motion | how the app reshapes per device + user preference | ext |
| 21 | Time-dependent behavior | longitudinal watch for expiries/reminders/scheduled jobs | background/scheduled behavior | cond:time-dependent |
| 22 | Offline / resilience | test service workers, offline mode, retry, network-loss | behavior when the network fails | cond:service-worker |
| 23 | Content-vs-code (CMS) | distinguish editor-managed content from hard-coded UI | what is data (admin-editable) vs code | cond:editable-content |
| 24 | Legal / compliance-surface | consent banners, privacy/cookie flows, data export/delete | compliance features a rebuild legally must keep | cond:consent-privacy |
| 25 | SEO / metadata | titles, meta, sitemap, robots, structured data, Open Graph | search-engine + social-preview behavior | cond:public-pages |
| 26 | Analytics / event taxonomy | capture events the app tracks (clicks, funnels) | the product's own success metrics + event names | ext |
| 27 | Deep performance profiling | runtime CPU/memory/long-tasks/frame-rate under real use | WHERE + WHY it's slow (deeper than the layer-5/baseline snapshot) | ext |

**Always-on probe (not numbered — runs on EVERY app):** `server-invisible-probe` — the
"back-end iceberg" (rate limits, webhooks, emails). See "Server-invisible behavior" below.

---

## Loops

**Inner (top-up) loop.** After the selected layers run, measure coverage against the
`surface-census.json` denominator. While predicted coverage < `coverage_benchmark` and the
library is not exhausted, add the next-best layer and re-measure. This is estimate → verify → top-up.

**Outer (re-run) loop.** After a full pass, re-run the WHOLE capture until a fresh pass adds
nothing MATERIAL, capped by `capture.max_reruns` (default `2` → 3 passes max). Compare on
NORMALIZED features/intent (against the census + intent ledger), never raw bytes (raw diffs
drown in timestamps/tokens/ordering). VARY conditions each pass (data/timing/inputs) so a
re-run probes NEW ground, not just re-confirms — identical re-runs share the same blind spots.
"No new material findings" is the convergence proxy for the benchmark: evidence, not proof.

---

## Interaction-state provocation (part of layer 2)

A static crawl misses state-dependent UX. For each interactive element:
- hover / focus / active / disabled
- submit empty, invalid, and boundary form input
- trigger empty states (fresh account / no data)
- watch loading states on a throttled network
- resize across breakpoints

States that cannot be provoked (payment failure, permission-denied, degraded modes) are
marked `UNKNOWN` in the spec — a blind rebuilder treats silence as "doesn't exist."

## Server-invisible behavior (probe, never assert) — ALWAYS ON

Cron jobs, outbound emails, webhooks, and rate limits are unobservable from the client. PROBE
them into `probes.json` with an explicit confidence band:
- rate limits: escalate request rate until 429; record the threshold + window
- emails/webhooks: point at disposable catch-all sinks; record the actual payloads that fired
- scheduled jobs: infer from time-correlated state changes (low confidence)

**Robustness:** require two independent signals before marking a probe "likely." Every probed
fact is `inferred`, never `confirmed`. These are exactly the items a UI-only clone silently
drops (the "backend iceberg").

## Baselines (the acceptance oracle inputs)

- `golden/parity-manifest.json` — observed input→output cases (see `parity.ts`), confidence-banded.
  **Robustness:** multiple samples per case + stable-vs-volatile field tagging.
- `baselines/budgets.json` — Lighthouse, p50/p95 latency, a11y score from the ORIGINAL.
  **Robustness:** repeat the baseline a few times; keep the spread, not a single number.
- `capture-manifest.json` — observation epoch + pinned `source_ref` (staleness control).
  **Robustness:** content-hash + build/version stamp; auto-diff new vs old on re-run (feeds the outer loop).

## Source-available mode

If the user supplies a repo instead of (or with) a live URL, layers 1–4 also read source
directly — but LLM source→requirements recovery is reliable only up to ~200 lines of code per
pass, so chunk it and treat recovered intent as `inferred` until cross-checked against observed
behavior. Reading source does NOT relax the wall: the extracted intent still passes the
spec-wall before any egress.
