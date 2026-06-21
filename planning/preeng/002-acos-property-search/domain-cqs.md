# Competency Questions — acos-property-search

> Phase 1 (DLG) output. A practitioner building/operating this skill must be able to answer each.
> Each CQ has a stable id (`CQ-01`…`CQ-18`), maps to a `cq`-type node in `domain-lattice.json`, and is
> connected to method/metric/standard/risk nodes there (≥95% coverage target). Operational numerics
> PLAN.md left tunable are answered with `Assumption`/`TBD`.

| ID | Competency Question |
|---|---|
| **CQ-01** | Why is there no free nationwide owner-name property search, and what does "widest defensible net" actually mean operationally? |
| **CQ-02** | What are the 9 independent discovery channels, and what does each catch that a direct owner-name assessor search misses? |
| **CQ-03** | Which jurisdictions support statewide owner search vs. owner-friendly county-by-county vs. name-blocked, and how does that drive routing? |
| **CQ-04** | How is the recorder grantor-grantee name index used as the highest-yield free channel and the workaround for name-blocked states (CA/NJ/Cook)? |
| **CQ-05** | How does the mailing-address pivot (ArcGIS REST `MAIL_ADDR LIKE` / bulk-roll group-by) surface portfolios held under many entity names billed to one back office? |
| **CQ-06** | How does the entity graph expand from a seed (person→officer/agent→entities→siblings→parcels), and what does each node/edge represent? |
| **CQ-07** | What temporal + provenance fields must every edge store, and why is ownership time-variant ("as of")? |
| **CQ-08** | What is the edge-strength ordering, and how does inverse-frequency weighting separate signal from noise? |
| **CQ-09** | How does the hub-guard (registered-agent stop-list + dynamic detection threshold + hop limit + log-every-prune) prevent combinatorial blow-up while keeping coverage honest? |
| **CQ-10** | Why must swarm agents be **isolated/blind**, and how does that make "Verified = 2+ independent sources" genuine rather than circular? |
| **CQ-11** | What does the between-rounds synthesizer do (cross-reference → confidence, preserve conflicts, hub-prune + hop-limit, emit next seeds), and when does the loop stop? |
| **CQ-12** | How is Stage-1 identity resolution performed (aliases/spouse/relatives/associates as leads-only), and why are ≥2 anchors required for common names? |
| **CQ-13** | How are concealed holdings pierced (land trusts, nominees, series LLCs, trusts, contract-for-deed, life estate, TIC), and which recorded instruments expose control? |
| **CQ-14** | Why is FinCEN BOI unusable and why are paid APIs / data brokers excluded — and how does that constrain the design? |
| **CQ-15** | What is the merged scoring rubric, what are the confidence-tier cutoffs (75/50), and what is the manual-review flag taxonomy? |
| **CQ-16** | How is an estimated equity / value / debt picture computed from FREE data, and how is every figure labeled to avoid AVM misinterpretation? |
| **CQ-17** | What does the BLOCKING compliance gate require (DPPA/FCRA/FDCPA permissible purpose, debt classification, GLBA anti-pretexting hard block, scraping posture), and what per-run record is captured? |
| **CQ-18** | How do caching + freshness TTLs + per-record freshness stamps + the audit trail make runs cheap, resilient (403/rate-limit), and auditable — and what does monitoring (v2) add? |

## Answer sketches (offline; full reasoning lives in research.md / PLAN.md)

- **CQ-01** — Ownership lives across ~3,100 counties under 48+ recording statutes with no unified free
  index. Widest net = maximize **independent discovery channels + entity-graph pivots**, then take the
  **union** (not one magic search).
- **CQ-02** — The 9 channels (assessor / recorder index / mailing pivot / entity graph / lien+UCC /
  bankruptcy / court / people-search / piercing); each catches a distinct miss (LLC transfers, mailing
  back-office portfolios, controlled entities, lien-tied parcels, sworn schedules, contested property,
  aliases, concealed title). Recorder index is highest-yield.
- **CQ-03** — Statewide = MD/MA/MT; friendly = FL/TX/AZ/NV; name-blocked = CA (§7928.205)/Cook/NJ
  (Daniel's Law); else county-by-county. Routing matrix in `references/owner-search-by-state.md`.
- **CQ-04** — Grantor-grantee index catches LLC/trust transfers + roll lag + name-blocked states; it is the
  workaround where owner names are suppressed.
- **CQ-05** — `MAIL_ADDR LIKE` / bulk-roll group-by on the tax-bill mailing address links many entity names
  to one back office (portfolio discovery).
- **CQ-06** — From each seed, resolve entities → harvest officers/agents/addresses/phones → discover sibling
  entities & people → search parcels → push **new** nodes onto the worklist → repeat to closure.
- **CQ-07** — Every edge stores `{source, source_url, confidence, date_first_seen, date_last_verified,
  effective_date, expiration_date, raw_evidence}` because ownership is time-variant and needs an "as of."
- **CQ-08** — Strength order: shared officer/member > shared mailing/principal address > shared phone >
  shared email/domain > shared filing batch > shared registered agent (only if non-commercial).
  Inverse-frequency: a value shared by 2 nodes is strong; by thousands is noise.
- **CQ-09** — Hub stop-list (`hub_agents.txt`) + dynamic detection (default **25**, `Assumption`-tunable) +
  hop limit (default **2 degrees**) + inverse-frequency weighting; **log every prune** so coverage stays
  honest. Inverse signal kept: a non-commercial agent on a few entities is a strong control link.
- **CQ-10** — Agents work **blind** to each other; two independently landing on the same parcel is genuine
  corroboration, making the "Verified = 2+ sources" tier non-circular.
- **CQ-11** — Synthesizer cross-references → confidence, **preserves** conflicts (never harmonizes),
  hub-prunes + enforces the hop limit, emits next seeds; stop when a round yields **no new high-confidence
  nodes**.
- **CQ-12** — Resolve the real person first (aliases / maiden / Jr-Sr / prior addresses / spouse /
  relatives / associates) — people-search = **leads only**, corroborate against a primary record before
  scoring; ≥2 anchors for common names.
- **CQ-13** — Pierce via recorded instruments: land trust (CABI + personal guaranty + IL disclosure
  register; FL more opaque), nominee/series LLC (mortgage/deed-of-trust signatories + guaranty + UCC debtor
  + tax-bill mailing triangulation), trust (search person *as trustee* + trust name), contract-for-deed/
  life estate/TIC (read the vesting clause). DBA/assumed-name works *for* us.
- **CQ-14** — FinCEN BOI is non-public and the March 2025 interim final rule exempted ~all US domestic
  entities, so the data often doesn't exist — flag only, build nothing on it. Paid APIs excluded by the
  free-only constraint (cost + FCRA/data-broker exposure).
- **CQ-15** — Merged rubric (PLAN.md §7): +40/+25/+25/+20/+10/+10-per-corroboration(cap+20) /
  −40/−30/−20/−10/−10 / cap ≤40 through a hub. Tiers ≥75 high / 50–74 candidate / <50 weak
  (`Assumption`-tunable, default 75/50). Review-flag taxonomy in `references/review-flags.md`.
- **CQ-16** — Per confirmed parcel: assessed value (flag "assessed, not market") + last sale + original
  recorded mortgage − stated amortization assumption → **estimated equity**; "no mortgage data found" flag;
  true AVM/payoff stated as a limitation, never fabricated.
- **CQ-17** — Gate (blocking) records permissible purpose mapped to statute (DPPA (b)(3)/(b)(4); FCRA
  §1681b; "asset location — NOT for eligibility"), debt classification (consumer vs. commercial → FDCPA),
  GLBA anti-pretexting **hard block**, scraping posture. Per-run schema in `references/compliance.md`.
- **CQ-18** — JSON cache wraps every lookup with freshness TTLs (corporate ~30 d, property ~30–60 d,
  deed/transfer faster — `Assumption` defaults), handles rate-limits/403, makes re-runs cheap + auditable;
  per-record freshness stamps surface in the report; audit trail under `workspace/<session-id>/`.
  v2 monitoring (`/schedule`) alerts on new acquisitions/transfers off freshness deltas.
