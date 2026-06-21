# Product Context — acos-hypercore-ask

- **feature_id:** `001-hypercore-ask`
- **product_name:** acos-hypercore-ask (ACOS skill)
- **deliverable type:** A new ACOS skill (`.claude/skills/acos-hypercore-ask/`) plus supporting
  scripts (`.claude/scripts/`) and optional `general-purpose`-based agents. The "product" being
  pre-engineered is this skill itself.

## 1. Product / Feature Name
`acos-hypercore-ask` — an ACOS skill that answers any natural-language question about, and mines
data from, the **Hypercore loan-management platform** (hypercore.ai), with a **zero-hallucination,
provenance-verified** data guarantee. Output is usable as a direct deliverable (reports, tables,
datasets) or as a **trusted, verified input feed** for other ACOS tasks/skills.

## 2. Business Objectives
- Give OKOA Capital staff a single, trustworthy natural-language interface to all loan-portfolio
  data held in Hypercore (loans, borrowers, facilities, drawdowns, payments, fees, interest,
  amortization, covenants, collateral, investor allocations).
- Produce **verified** data extracts — reports, tables, datasets — deliverable directly OR consumed
  as trusted inputs by other ACOS skills (prospectus live-numbers, data rooms, financial
  statements, legal diligence).
- Eliminate slow, technical, error-prone manual data pulls and the hallucination risk of ad-hoc
  AI querying. Every delivered number must be defensible to OKOA's boss on first cold look.

## 3. User Problems (ranked)
1. Staff need answers about Hypercore data, but querying the platform/API directly is slow,
   technical, and error-prone.
2. AI-generated data answers cannot currently be trusted — fabrication, **stale data**, **silent
   pagination cutoffs**, and **aggregation errors** make outputs unusable for IC-grade work.
3. Other ACOS skills need clean, verified loan data as input, but there is no canonical,
   provenance-backed source feed.
4. There is no standard way to turn a question into a verified report/table without bespoke
   scripting each time.

## 4. Success Metrics
- **0% hallucination/fabrication:** every delivered value traces to a specific cached raw API
  response (endpoint + request params + timestamp + JSON field path).
- **100% provenance coverage** on delivered values; values that cannot be provenance-bound are
  **refused, not guessed**.
- **Adversarial-consensus pass:** a value/answer is delivered only when ≥N independent extraction
  agents agree on substance.
- **Completeness:** pagination-complete (no silent truncation), freshness within stated window,
  schema-validated.
- Single-source figures flagged with **confidence ≤ 0.7** (per OKOA prior pattern).
- Time-to-verified-answer materially faster than a manual pull.

## 5. Constraints
- **Read-only** against Hypercore — the skill MUST NOT write/mutate Hypercore data via the API.
- **Subscription-only Claude (NO `ANTHROPIC_API_KEY`)** — all model work via main-thread Read or
  `Task()` sub-agents (standing OKOA rule; separate API billing is forbidden).
- **API access not yet provisioned** — design fully now; live API calls are **stubbed/TODO behind a
  clearly isolated client/adapter layer** until credentials arrive. The skill must degrade
  gracefully and explicitly say "no live data" rather than fabricate.
- Must run inside ACOS / Claude Code as a skill (+ supporting scripts; optional `general-purpose`
  agents — no new restricted `.claude/agents/` files without human approval).
- Hypercore API security posture: TLS 1.2+, AES-256 at rest, RBAC, SOC 2 Type II, GDPR, MFA/SSO —
  secrets handled securely (no credentials in repo; use env/secret store).
- Prefer Python 3 stdlib for scripts (consistency with existing ACOS scripts) — confirm at plan time.

## 6. Dependencies
- **Hypercore platform API** (hypercore.ai) — REST read endpoints + real-time webhook events;
  entities spanning origination → servicing → repayment. Platform integrations include Salesforce,
  NetSuite, document repositories. **API docs are partner-gated and not yet in hand.**
- Credentials / secret management (to be provisioned).
- ACOS framework: skill loader, `Task()` sub-agents (`general-purpose`), evidence bundles
  (`.acos/evidence/`), memory / RAG.
- Optional downstream consumer skills: `acos-dataroom-v2`, `acos-financial-statement`, the
  prospectus pipeline, `legal-analyst`.

## 7. Known Risks
- **API surface unknown until access granted** → plan MUST isolate the Hypercore client behind a
  contract/adapter so the rest of the skill is built and tested against fixtures/mocks now.
- **Stale data:** "updates using hypercore api" → must define a freshness policy (live fetch vs
  cached, webhook-driven invalidation) and never serve stale data silently.
- **Silent pagination / rate-limit truncation** → a completeness gate is required.
- **Schema drift** on Hypercore's side → schema validation + drift detection.
- **Aggregation / units / currency errors** in reports (the real hallucination-adjacent failure
  mode) → reconciliation checks + adversarial recomputation.
- **Privilege / PII:** loan data is sensitive (borrower PII, financials) → access controls, no
  leakage into logs/evidence beyond need, GDPR-aware.
- **Over-trust:** users may treat answers as gospel → mandatory provenance display + confidence +
  refusal-on-uncertainty.

## 8. Pre-seeded research (T-tagged)

### External — Hypercore platform (T3: vendor/public site hypercore.ai; API specifics partner-gated, UNVERIFIED until access)
- Hypercore is loan-management software for private credit / direct lending; manages origination,
  underwriting, servicing, amendments, restructurings, repayment.
- Supports term loans, revolvers, mezzanine, **bridge**, **construction**, syndicated, hybrid facilities
  (OKOA does bridge + construction lending).
- **API:** connects to CRMs, GLs, banking portals, third-party data; exposes **read/write endpoints +
  real-time webhook events**. Common integrations: Salesforce, NetSuite, document repositories.
- Automates fee/interest calc, amortization schedules, funding/drawdowns, compliance checks;
  real-time reporting; audit-ready controls.
- Security: TLS 1.2+ (transit), AES-256 (rest), RBAC, SOC 2 Type II, GDPR, MFA + SSO.
- **Likely core read entities to model:** loans/facilities, borrowers/entities, drawdowns/fundings,
  payments/repayments, fees, interest accruals, amortization schedules, covenants/compliance,
  collateral, investor allocations, documents.

### Internal — ACOS priors (T2: validated learnings/retrospectives in this repo)
- **`pre-generation-verification-gate`** (LEARN): mandatory, non-bypassable gate between extraction
  and delivery; show every data point with source + provenance + confidence; cap single-source
  figures at confidence ≤ 0.7.
- **`two-tier-data-model`** (LEARN-ARCH-002): full canonical record w/ full provenance (source of
  truth) + brief derived view (token-efficient); give each agent only the tier it needs. → raw
  cached API responses = truth; normalized answer layer = derived.
- **Provenance discipline** (real OKOA loan extractions): no fabrication; exact numeric/name/date
  preservation; provenance required on every field.
- **Adversarial-consensus pattern** (`acos-dataroom-v2` / `acos-financial-statement` / `acos-grader`):
  N blind independent agents + asymmetric/quorum consensus gating before a result is accepted. Reuse
  this for answer/extract verification.

## Verification architecture (REQUIRED — distinguishing feature; DO NOT strip or weaken)
**Provenance-binding + adversarial multi-model consensus:**
- Every delivered value MUST cite the exact raw cached API response (endpoint + request params +
  timestamp + JSON field path) it derives from. **No citation → no delivery (refuse).**
- Multiple independent extraction/answer agents run **blind**; a result is delivered only on substance
  consensus. Disagreement → re-dispatch / escalate, never a silent pick.
- Deterministic gates layered underneath: schema validation, pagination-completeness, freshness
  window, cross-field reconciliation, unit/currency normalization, single-source confidence cap ≤ 0.7.
- Tiered application is acceptable (deterministic for trivial lookups; full consensus for
  reports/aggregations/analysis that feed other tasks) — but **provenance-binding is universal**.
