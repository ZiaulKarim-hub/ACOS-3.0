# Decision: acos-property-search Skill Design — Decision Lock D1–D8, Ground Rules, Hypothesis Verdicts

**Date:** 2026-06-19
**Decision Maker:** human (confirmed) + the-architect (proposed)
**Status:** accepted
**Supersedes:** N/A
**ADR ID:** ADR-003
**Related Epic:** EPIC-APS-00 (acos-property-search) — PROPOSED via VISION-APS-01
**Related Slice:** slice-00-diagnostic (problem-before-solution lock)

## Context

`acos-property-search` is a project skill (planned at
`.claude/skills/acos-property-search/`) that, given a person or business/entity
name plus optional anchors, casts the widest defensible net to find all US real
property the party owns or controls — nationwide, for skip-tracing / collections —
and returns ranked, deduplicated, provenance-tagged holdings in confidence tiers
with an equity picture, a compliance record, and an audit trail.

The full design lives in
`.claude/skills/acos-property-search/PLAN.md` (plan-only; nothing built). The
governing reality the plan is built around: **there is no free nationwide
owner-name property search** — ownership lives across ~3,100 counties under 48+
recording statutes. "Widest net" therefore means maximizing the number of
independent discovery channels and pivots, then taking the union — not finding one
magic search.

This ADR is produced by slice-00-diagnostic to lock the problem before any build:
it records the eight design decisions from PLAN §16 (D1–D8), the locked ground
rules from PLAN §1 / §7 / §10, and a written verdict on each of the three
diagnostic hypotheses (H1/H2/H3). No solution code, SKILL.md, reference files, or
network calls are produced by this slice.

## Problem Statement

Eight design choices must be fixed before the v1 build begins, the non-negotiable
ground rules must be recorded so the build cannot silently drift off them, and the
three hypotheses that justify the architecture must each receive an explicit
written verdict grounded in what the plan/build shows. Empirical unknowns that
cannot be settled on paper must be routed to a later validation slice rather than
guessed at now.

## Options Considered

This ADR records eight separate decisions. Each is presented with its chosen
default, at least one alternative considered, and a one-line rationale. The
detailed Pros/Cons/Effort/Risk treatment is reserved for the two highest-leverage,
most-contested decisions (D1 swarm wiring, D3 compliance gate); the remaining
decisions are recorded in compact form.

### D1 — Swarm wiring: **(A) embed an adapted, hub-guarded swarm**

**Description:** Embed a swarm execution layer adapted from the
`acos-swarm-research` pattern directly into the skill, rather than composing the
generic swarm skill as a black box. Isolated parallel agents (5–20) fan out per
round, each writing its own `findings.md`; a between-rounds synthesizer holds the
control point (cross-reference → confidence, conflict preservation, hub-prune +
hop limit, next-round seeds).

**Pros:**
- The decomposition axis the problem actually needs is **channel × jurisdiction ×
  entity**, not generic research lenses — only an adapted swarm can express it.
- The skill can own the loop: it runs **per round**, because the graph
  rediscovers its own work-list, which one-shot generic swarm cannot do.
- The between-rounds synthesizer can hold the **hub stop-list + hop counter** —
  the precision control that prevents combinatorial blow-up (see H3).

**Cons:**
- More build surface than wiring up the existing skill as-is.
- Some duplication of swarm scaffolding logic that `acos-swarm-research` already
  solves.

**Effort:** Medium **Risk:** Low

**Alternative considered:** (B) compose `acos-swarm-research` directly.
**Rationale (one line):** Compose was rejected because the generic skill is
one-shot and lens-axis; this domain needs a looped, channel×jurisdiction×entity
swarm whose synthesizer owns the hub-guard — so we embed an adapted version.

### D2 — Report renderer: **Markdown for v1; doc-skill render for v2**

**Chosen default:** A single Markdown report in v1 (compliance header → tiers →
per-parcel evidence chain → equity rollup → coverage/limits footer → review
flags), deferring the screenshot-verified institutional deliverable to v2 via
`acos-loan-doc-generator-with-visual-verification`.
**Alternative considered:** Render the loan-doc visual-verification deliverable in
v1.
**Rationale (one line):** Markdown ships the methodology and audit trail first
without coupling v1 to the heavier render/verify pipeline; the institutional memo
is a v2 presentation layer over the same structured findings.

### D3 — Compliance gate: **Hard gate (BLOCKING), runs first, every time**

**Description:** A compliance gate runs before any discovery and **refuses to
proceed** until the permissible purpose (mapped to statute), debt classification
(consumer vs. commercial), the GLBA anti-pretexting hard block, and the scraping
posture are recorded for the run.

**Pros:**
- Skip-tracing carries real legal weight (DPPA, FCRA, FDCPA, GLBA); a blocking
  gate makes the permissible-purpose record a precondition, not an afterthought.
- Forces a per-run audit artifact — the dossier is flagged "asset location / debt
  recovery — NOT for eligibility," keeping it off the FCRA consumer-report side.
- A hard block on GLBA anti-pretexting prevents the worst-case misuse by
  construction.

**Cons:**
- Adds a mandatory step before the user sees any value.
- A misconfigured gate could block legitimate runs (mitigated: the gate records,
  it does not adjudicate; counsel sign-off is noted out-of-scope).

**Effort:** Low **Risk:** Low (and high risk if omitted)

**Alternative considered:** prompt-and-log non-blocking, or a minimal note.
**Rationale (one line):** Non-blocking was rejected because compliance for
skip-tracing must be a precondition of execution, not advisory text the run can
skip past.

### D4 — Scope depth v1: **Channels 1–4 + full recorder index; channels 5–9 phased**

**Chosen default:** v1 covers assessor owner-search, the recorder grantor-grantee
index (full), the mailing-address pivot, and the entity graph (channels 1–4);
liens/judgments, bankruptcy, courts, people-search-at-depth, and concealment
piercing (5–9) are phased into v2/v3.
**Alternative considered:** all nine channels in v1.
**Rationale (one line):** Channels 1–4 plus the high-yield recorder index deliver
the widest-net core; loading all nine into v1 inflates scope without proving the
core pipeline first.

### D5 — Scripts in v1: **full stdlib-only set, not core-3-only**

**Chosen default:** ship `normalize, score, dedup, arcgis_query, graph,
swarm_dispatch, synthesize_round, rollup, cache` in v1.
**Alternative considered:** core three only (normalize, score, dedup).
**Rationale (one line):** The graph, swarm-dispatch, synthesizer, ArcGIS pivot,
rollup, and cache are what make the widest-net + corroboration + hub-guard design
real; core-3 would ship a scorer without the engine it scores.

### D6 — Confidence tiers: **75 / 50 cutoffs**

**Chosen default:** ≥75 high-confidence (actionable) · 50–74 candidate (review) ·
<50 weak (logged only).
**Alternative considered:** 70 / 40 cutoffs (the earlier v1 proposal).
**Rationale (one line):** The higher 75/50 cutoffs bias toward precision for an
actionable collections tier; the exact false-positive cost of this choice is an
empirical unknown routed to slice-11 (see Implications).

### D7 — Hub frequency threshold: **25 entities**

**Chosen default:** any registered agent / address appearing on >25 entities is
treated as a dynamic hub and pruned (in addition to the static `hub_agents.txt`
stop-list).
**Alternative considered:** tune the threshold per-state.
**Rationale (one line):** A single tunable default of 25 is simple and honest
(every prune is logged); per-state tuning is a later refinement once real
frequency distributions are observed.

### D8 — Hop limit: **2 degrees from the seed**

**Chosen default:** bound graph expansion at 2 degrees from the seed by default.
**Alternative considered:** 3 degrees for deep dives.
**Rationale (one line):** 2 hops captures the controlled-entity neighborhood while
containing blow-up; 3-hop deep dives are opt-in, not the default, because each
extra hop multiplies false-link risk.

## Locked Ground Rules (non-negotiable)

These are recorded so the build cannot silently drift off them:

1. **Free / open-web sources only.** No paid APIs — no ATTOM, CoreLogic,
   BatchData, RealEstateAPI, Middesk, TLO/IDI, or equivalents. (PLAN §1.)
2. **Stdlib-only Python helpers.** Methodology (`SKILL.md`) + small stdlib-only
   Python scripts + reference files. No external infrastructure — no Neo4j /
   Elasticsearch / Postgres / billing. (PLAN §1.)
3. **BLOCKING compliance gate.** The compliance gate runs first, every time, and
   refuses to proceed until the permissible-purpose record, debt classification,
   GLBA anti-pretexting hard block, and scraping posture are captured. (PLAN §10;
   D3 above.)
4. **Mandated hedged language.** Output says "likely controlled by" and "possible
   ownership connection via mailing address." The word **"owns" is reserved only
   where a title record directly supports it** — never a bare "owns" without title
   support, and never "definitely owns" otherwise. (PLAN §7.)

## Hypothesis Verdicts (written, grounded in what the build/plan shows)

**H1 — Widest net = union of independent channels/pivots, not one magic search.**
**VERDICT: CONFIRMED.** The plan is built on the fact that no free nationwide
owner-name search exists (ownership is fragmented across ~3,100 counties under 48+
statutes), so PLAN §2 hits all nine independent discovery channels and unions their
results because each catches what the others miss — confirming that the widest net
is the union of channels and pivots, not any single search.

**H2 — Blind agent isolation makes "Verified = 2+ sources" genuine corroboration,
not circular.** **VERDICT: CONFIRMED.** Because each channel-agent fans out
**blind to the others** and writes its own `findings.md` (PLAN §3), two agents
independently landing on the same parcel is genuine corroboration rather than one
source echoing another — which is precisely what makes the "Verified = 2+
independent isolated agents" confidence tier meaningful instead of circular.

**H3 — Without a hub-guard, expanding siblings through a mass registered agent
causes N^2 false-link blow-up.** **VERDICT: CONFIRMED.** A single mass registered
agent (e.g., CT Corporation, CSC) sits on thousands of unrelated entities, so
expanding "siblings" through it links them all to each other — one hub ≈ N² false
links (PLAN §3/§4). The design confirms the hypothesis by guarding against it: the
between-rounds synthesizer holds the static hub stop-list plus a dynamic
frequency threshold (D7=25) and a bounded hop limit (D8=2), and logs every prune so
coverage stays honest.

## Decision

**Chosen:** Lock D1–D8 at the defaults above (D1=embed adapted hub-guarded swarm;
D2=Markdown v1 / doc-skill render v2; D3=hard blocking compliance gate; D4=channels
1–4 + full recorder, 5–9 phased; D5=full v1 script set; D6=75/50 tiers; D7=25-entity
hub threshold; D8=2-degree hop limit). Lock the four ground rules (free-only,
stdlib-only, blocking compliance, hedged language). Record H1/H2/H3 as all
CONFIRMED. Route the empirical unknowns to slice-11.

## Rationale

The decisions cohere around one principle adopted verbatim in the plan: *don't
search for "who owns this property" — search for "what assets are likely controlled
by this economic actor."* The widest-net architecture (D1, D4, D5) is what
implements that principle; the precision controls (D6, D7, D8) are what keep the
net from collapsing into noise; and the ground rules (free-only, stdlib-only,
blocking compliance, hedged language) are what keep it cheap, portable, lawful, and
honest. Each hypothesis is the load-bearing justification for one part of that
structure — H1 for the union of channels, H2 for the corroboration tier, H3 for the
hub-guard — and the plan demonstrates each, so all three are confirmed at lock time.

Two questions cannot be settled on paper and are explicitly deferred rather than
guessed: whether the free portals are actually reachable in practice, and what the
false-positive rate is at the chosen 75/50 confidence cutoffs.

## Implications

### Immediate

- The v1 build proceeds against the locked defaults: PLAN §18 build steps may begin
  on explicit "go" (reconcile `SKILL.md` + `normalize.py` stubs, author reference
  files, implement the full stdlib script set, add tests, configure the allowlist,
  dry-run).
- The four ground rules are binding constraints on every subsequent slice — any
  paid source, non-stdlib dependency, non-blocking compliance path, or bare "owns"
  without title support is an automatic scope/quality failure.
- This slice produces no scripts, no SKILL.md, no reference files, and makes no
  network call (scope respect per the slice's acceptance criteria).

### Long-term

- **Open unknown — real portal availability** is routed to **slice-11's dry run**:
  many county/state portals 403-block bots and gate the richest owner+mailing data
  behind purchase, so actual reachability must be measured against real portals, not
  assumed. (Carried as a stated limitation in PLAN §17 until slice-11 settles it.)
- **Open unknown — false-positive rate at the 75/50 cutoffs (D6)** is routed to
  **slice-11's dry run**: the 75/50 thresholds and the D7=25 hub threshold are
  tunable, and their real precision/recall trade-off can only be observed by running
  the pipeline on sample subjects and inspecting the resulting tiers.
- D7 (per-state hub tuning) and D8 (3-hop deep-dive mode) are pre-identified
  refinement levers once slice-11 produces real frequency and false-link data.

### Dependencies

- Depends on: `.claude/skills/acos-property-search/PLAN.md` (the design this ADR
  locks) and `planning/slices/slice-00-diagnostic.yaml` (the acceptance criteria).
- Depends on: `acos-decide` ADR template + ADR-001/ADR-002 house style.
- Enables: the v1 build (PLAN §18) under fixed defaults.
- Routes to: **slice-11 dry run** for the two empirical unknowns (portal
  availability; false-positive rate at 75/50).

## Related Decisions

- ADR-001 — Page-as-Canvas Composition (house-style precedent).
- ADR-002 — Brand-First Image Sourcing (house-style precedent).
- (future) the v2 renderer decision, if `acos-loan-doc-generator-with-visual-verification`
  integration surfaces new trade-offs (D2 phase-2).

## Review Notes

Produced by slice-00-diagnostic (problem-before-solution lock) for the
`acos-property-search` skill. Decisions D1–D8 are transcribed from PLAN.md §16
"Decisions log"; ground rules from §1 / §7 / §10; hypothesis verdicts validated
against §2 (H1), §3 (H2), and §3/§4 (H3). VISION-APS-01 / EPIC-APS-00 are PROPOSED
and not yet formally planned via `/acos-plan`; if a later `/acos-plan` conflicts,
it is authoritative over this ADR's epic/vision references.

---

*Recorded by The Architect*
