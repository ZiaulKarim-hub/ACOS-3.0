# Domain Brief — acos-property-search

> Phase 1 of the Constitutional Domain Compilation Pipeline (Protocol 0.2 / DLG). Offline structuring of
> the **already-completed research in PLAN.md** (treated as authoritative). Per-portal source availability
> and per-state statutes are tagged by tier in `evidence-ledger.json`; lattice in `domain-lattice.json`;
> CQs in `domain-cqs.md`. Where PLAN.md leaves a numeric/operational detail open, it is carried as
> `Assumption`/`TBD`.

## Domain framing

The domain has two coupled halves:

1. **The subject domain — US real-property ownership discovery for skip-tracing / collections.** Ownership
   and *control* of real property surfaces across ~3,100 counties under 48+ recording statutes, frequently
   **concealed** behind LLCs, land trusts, nominees, series LLCs, contract-for-deed, life estates, and TIC.
   There is **no free nationwide owner-name search**; "widest net" therefore means maximizing independent
   **discovery channels** and **entity-graph pivots** and taking the union.
2. **The method domain — defensible, free-sources-only asset discovery.** A multi-channel graph engine with
   temporal/provenance edges, a **hub-guard** (stop-list + dynamic detection + hop limit + inverse-frequency
   weighting), a **blind isolated swarm** with a between-rounds synthesizer (corroboration + conflict
   preservation + pruning), a scoring rubric with confidence tiers, an estimated-equity rollup from free
   data, a **blocking compliance gate**, hedged language, and a full audit trail. This is the skill's
   distinguishing discipline.

The product is an ACOS **project skill** (explicit-invocation-only) that, given a person or entity name
(+ optional anchors), returns ranked, deduplicated, provenance-tagged likely holdings in confidence tiers,
with an estimated equity picture, a compliance record, and an audit trail — using **free / open-web sources
only**.

## Entities

**Subject-domain (graph) entities** — PLAN.md §4 node set:
- Name · Person · Entity (LLC/corp/trust) · Address · Agent (registered agent) · Phone · Email · Parcel ·
  Loan · Lien · Deed · Court-case · UCC filing.

**Skill-internal (method) entities:**
- GraphNode / GraphEdge (temporal + provenance: `{source, source_url, confidence, date_first_seen,
  date_last_verified, effective_date, expiration_date, raw_evidence}`).
- Seed (worklist item: name / address / entity / person).
- ChannelAgentRun (one isolated agent's `findings.md`).
- RoundSynthesis (cross-reference result: confidence, conflicts, pruned nodes, next seeds).
- ParcelRecord (APN-keyed dedup unit).
- ConfidenceRecord (score + signals + tier).
- ReviewFlag (manual-review taxonomy entry).
- EquityRollup (assessed value − estimated encumbrances; all "estimated").
- ComplianceRecord (per-run permissible-purpose record).
- CacheEntry (JSON, freshness TTL).
- AuditArtifact (`workspace/<session-id>/round-NN/agent-NN/findings.md` + `synthesis/`).

## Processes
- **Compliance gate (BLOCKING, first):** map permissible purpose to statute; classify debt; GLBA hard
  block; set scraping posture; record → only then proceed.
- Normalize / classify input (person vs. entity; alias/variant expansion; fuzzy match).
- **Stage 1 identity resolution:** aliases, prior addresses, spouse/relatives/associates (people-search =
  leads only, corroborate); ≥2 anchors for common names.
- **Entity discovery:** SoS + OpenCorporates person→officer/agent→entities→siblings; harvest
  officers/agents/addresses/phones.
- **Graph-expansion loop (loop-until-dry, hop-limited):** per-round fan-out of isolated channel×jurisdiction×
  entity agents → `findings.md` → between-rounds synthesizer → next worklist → stop when no new
  high-confidence nodes.
- **Discovery channels (1–9):** assessor owner-name; recorder grantor-grantee index; mailing-address pivot
  (ArcGIS REST); entity graph; lien/judgment (+UCC fixtures); bankruptcy A/B+SOFA; court records;
  people-search; concealment piercing.
- **Synthesizer:** cross-reference → confidence (Verified = 2+ independent isolated agents); **preserve
  conflicts** as manual-review flags; **hub-prune + enforce hop limit**; emit next-round seeds.
- Dedup on APN + per-owner aggregation.
- Scoring + tiers + review flags.
- Equity / value / debt rollup (estimated, from free data).
- Report rendering (Markdown v1; loan-doc render v2) with hedged language.
- Caching (JSON + freshness TTLs) wrapping every external lookup; per-record freshness stamps in the report.
- (v2) Monitoring / refresh alerts off cache freshness deltas.

## Methods / patterns
- **Multi-channel union** ("widest net" = maximize independent channels + pivots, then union).
- **Entity graph with temporal/provenance edges** ("shares attribute X"); edge-strength ordering
  (shared officer/member > shared mailing/principal address > shared phone > shared email/domain >
  shared filing batch > shared registered agent if non-commercial).
- **Hub-guard** (registered-agent stop-list + dynamic detection ≥25 + hop limit 2 + inverse-frequency
  weighting + **log every prune**); inverse signal kept (a *non-commercial* agent on a few related entities
  is a *strong* control link).
- **Blind isolated swarm** (adapted from `acos-swarm-research`): decomposition axis = channel × jurisdiction
  × entity; runs **per round in a loop**; between-rounds synthesizer holds the hub stop-list + hop counter.
- **Corroboration-via-isolation** (Verified = 2+ independent isolated agents → non-circular).
- **Conflict preservation** (never silently harmonize; flag for manual review).
- **Concealment-piercing playbook** (channel 9): land trusts (CABI + guaranty + IL disclosure register),
  nominees/series LLCs (recorded mortgage/deed-of-trust signatories + guaranty + UCC debtor + tax-bill
  mailing triangulation), trusts (search person *as trustee* + trust name), contract-for-deed/life estate/
  TIC (read the vesting clause), DBA/assumed-name (works *for* us).
- **Estimated-equity rollup from free data** (assessed value + original recorded mortgage − amortization
  assumption → estimated equity; everything labeled "estimated").
- **Confidence scoring + tiers + review-flag taxonomy.**
- **Caching with freshness TTLs**; per-record freshness stamps.
- **Hedged language discipline** ("likely controlled by"; reserve "owns" for direct title support).

## Anti-patterns (to avoid)
- Searching "who owns this property" instead of "what assets are likely controlled by this actor."
- Single-channel owner-name search (misses LLC/trust/name-blocked holdings).
- Expanding "siblings" through a **hub** registered agent / shared address (N² false links).
- Unbounded graph expansion (no hop limit → combinatorial blow-up).
- **Silently harmonizing conflicting owner names** instead of flagging them.
- Scoring **people-search leads** as facts without corroboration.
- Treating a single source as "Verified."
- Saying "definitely owns" without a title record; un-hedged language.
- **Fabricating equity / payoff figures** (presenting estimates as AVMs).
- Proceeding **without the compliance gate**; GLBA pretexting; ignoring robots/rate limits.
- Depending on **FinCEN BOI** (non-public; ~all domestic entities exempted) or **paid APIs**.

## Standards / regulations / posture
- **DPPA** §2721(b)(3) (debt recovery) / (b)(4) (judgment enforcement) — DMV-derived data.
- **FCRA** §1681b(a)(3)(A) (any credit pull); the assembled dossier flagged "asset location / debt
  recovery — NOT for eligibility" (FTC skip-tracer interpretation; both content + purpose prongs).
- **FDCPA** — consumer debt only; third-party contacts location-only, once, no debt disclosure.
- **GLBA anti-pretexting** — hard block: no obtaining financial info by misrepresentation (no general
  debt-collection exception).
- **State suppression statutes** — CA Gov. Code §7928.205; Cook County IL; NJ Daniel's Law (drives routing
  to the recorder index).
- **Land-trust statutes** — IL 765 ILCS 405; FL §689.071 (FL more opaque, no analog register).
- **Scraping posture** — official bulk feeds / record APIs preferred; public no-login pages only; respect
  rate limits / robots; per-datum provenance. (Counsel sign-off out of scope; not legal advice.)
- **OKOA / ACOS conventions (Assumption):** subscription-only Claude (no API key); IC-grade deliverables;
  provenance + hedged language on every figure; skills + Python 3 stdlib + general-purpose agents;
  `/acos-execute-slice` orchestration.

## Metrics
- Channel-coverage (counties/channels hit vs. attempted); corroboration rate (% parcels with ≥2 independent
  sources); hub-prune count (precision health); false-positive rate at the 75/50 cutoffs (dry-run review);
  freshness-within-TTL %; compliance-record completeness (100% target); hedged-language conformance;
  time-to-dossier.

## Risks
- No free national owner search; county fragmentation; name-blocked states; hub blow-up; concealment;
  common-name false positives; portal 403/rate-limit blocks; people-search noise; silent conflict
  harmonization; equity-figure misinterpretation; compliance/legal exposure (DPPA/FCRA/FDCPA/GLBA);
  FinCEN BOI unusable; nationwide licensing analysis out of scope.

## Key terms
- Widest-net / discovery channel; recorder grantor-grantee index; mailing-address pivot; ArcGIS REST parcel
  layer; owner-search-by-state matrix (statewide / friendly / name-blocked); entity graph; temporal/
  provenance edge; edge strength; hub agent / hub-guard / hub stop-list; dynamic hub detection; hop limit;
  inverse-frequency weighting; blind isolated swarm; between-rounds synthesizer; corroboration-via-isolation;
  conflict preservation; confidence tier (high/candidate/weak); manual-review flag; concealment piercing
  (land trust / nominee / series LLC / CABI / guaranty / vesting clause); estimated equity; freshness TTL;
  hedged language; permissible-purpose record; compliance gate.

## Coverage note
This brief, the CQ list (`domain-cqs.md`), the lattice (`domain-lattice.json`), and the evidence ledger
(`evidence-ledger.json`) jointly satisfy the 4-phase pipeline. CQ coverage is computed in `research.md` and
the QA report; target ≥ 95% with no critical structural violations.
