# Data Model — ACOS Investment Committee (003-investment-committee)

**Command:** `/preeng.plan` output (data model).
**Entities source:** `command_inputs.plan.data_model_entities`.
**Engine contract:** axiom-synthesis `orchestrate.py::process_fact` +
`_ic_extension_severity` (spec §4.2; agent-07).
**Grounding:** `spec.md`, `tech_prd.md`, `domain-lattice.json`.

Types are illustrative (YAML/JSON on-disk shapes). The load-bearing design decision is that
**Objection is a thin domain wrapper over the axiom-synthesis `fact` record**, and the
severity axis is a **domain-owned extension** that never touches the six engine scripts.

---

## 0. Entity relationship map (textual)

```
SessionManifest 1───* Round 1───* Turn ──addresses──> Turn
      │                  │            └─ HumanInjection (stance=HUMAN_OVERSEER)
      │                  └─ Transcript (append-only render of all Turns)
      │
Deal 1───* Seat 1──has──1 ExpertProfile
Deal 1───* Objection ──maps_to──> axiom-synthesis `fact`  (+ SeverityGrade / Axis S)
Objection 1───* Mitigant (Mitigant = a NEW fact, depends_on the Objection)
Mitigant 1───* ConditionPrecedent (each CP tagged to the risk/Objection it retires)
Objection *───1 SeverityGrade (Axis S; orthogonal to Axis A/B truth-grading)
Objection *───* EvidenceCitation
Verdict 1───1 SessionManifest   (one deterministic verdict per run)
ICMemo   1───1 Verdict          (13-section render from the ledger)
ConflictsDisclosure 1───1 SessionManifest (per-run governance artifact)
```

---

## 1. Deal

The transaction under committee review.

| Field | Type | Notes |
|-------|------|-------|
| `deal_id` | string | slug derived from `--deal <dir>` |
| `deal_dir` | path | dataroom folder (Assumption: folder input, acos-dataroom style) |
| `name` | string | human deal name |
| `asset_type` | enum | CRE/bridge/construction/etc. — drives deal-triggered optional seats |
| `ask` | object | loan amount, rate, term, lien position, structure |
| `jurisdictions` | [string] | property + borrower states -> per-deal usury/licensing check |
| `fund_id` | string \| null | links to the loan tape read by the Portfolio seat |
| `documents` | [EvidenceCitation] | intake-catalogued source docs |

Relationships: 1─*Seat (roster instance), 1─*Objection, 1─1Verdict, 1─1ICMemo.

## 2. Seat

An instance of a discipline chair on THIS deal's committee.

| Field | Type | Notes |
|-------|------|-------|
| `seat_id` | enum | `CREDIT, VALUATION, LEGAL, ENVIRONMENTAL, INSURANCE, FRAUD, PORTFOLIO, CHAIR, ADVOCATE` + optionals |
| `role_label` | string | stable speaker label, e.g. `[CREDIT]` |
| `voting` | bool | `false` for ADVOCATE (FR-M2) and CHAIR-as-procedural |
| `scope` | enum | `deal` \| `fund` (PORTFOLIO is `fund` — reads loan tape, FR-M17) |
| `owned_risk_categories` | [int] | indices into the 16-risk coverage map |
| `expert_profile` | ExpertProfile | 1─1 |
| `optional_trigger` | string \| null | condition that promoted an optional seat |

Relationships: *─1Deal; 1─1ExpertProfile; 1─*Objection (raised_by).

## 3. ExpertProfile

The model + persona configuration that instantiates a Seat (diversity carrier).

| Field | Type | Notes |
|-------|------|-------|
| `model_class` | enum | `opus` \| `sonnet` (via `resolve-agent-model.sh`) |
| `provider` | string | `anthropic` default; `openai/google/...` if Hybrid-Review |
| `persona` | string | adversarial mandate text (e.g. "assume fabricated until corroborated") |
| `temperature` | float | diversity knob |
| `mandate` | string | seat charter + falsifiable-objection requirement + procedural-chair note |

Note: when every ExpertProfile shares one `provider`, the run sets `reduced_independence:
true` (FR-S4, `metric-independence-flag`).

## 4. Objection  ← the core adapter entity

A falsifiable expert concern. **Maps 1:1 onto an axiom-synthesis `fact` record.**

| Objection field | -> `fact` field | Type | Notes |
|-----------------|-----------------|------|-------|
| `objection_id` | `fact_id` | string | stable id |
| `statement` | `statement` | string | "the deal fails if/because ___" (falsifiable, FR-M4) |
| `claim_type` | `claim_type` | enum | axiom-synthesis claim taxonomy |
| `candidates` | `candidates` | [obj] | per-source value candidates for fusion |
| `grading` | `grading` | object | Axis A (reliability) + Axis B (certainty) — engine-graded |
| `flags` | `flags` | [string] | e.g. reduced-independence, single-source |
| `refuter` | `refuter` | object | different-discipline falsification-gate verdict |
| `conflict` | `conflict` | object | same-fact cross-discipline contradiction (-> resolve_conflict) |
| `depends_on` | `depends_on` | [id] | mitigant/parent linkage |
| `covers` | `covers` | [string] | coverage-gate tags |
| `raised_by` | (domain) | seat_id | which Seat raised it |
| `severity` | `_ic_extension_severity` | SeverityGrade | **Axis S — domain-owned, NEVER blended** |

Engine truth-state (from axiom-synthesis STATE-MACHINE): `CONJECTURE / PROBABLE / CORROBORATED
/ ESTABLISHED / CONTESTED / UNRESOLVED / RETRACTED`. Objection state is engine-owned; the IC
skill only reads it for the deal-breaker derivation.

## 5. Mitigant

A structural/documentary control that caps (not erases) an Objection.

| Field | Type | Notes |
|-------|------|-------|
| `mitigant_id` | string | its own `fact_id` (a NEW fact, agent-07) |
| `depends_on` | objection_id | linkage to the risk it caps |
| `mitigant_type` | enum | reserve, guaranty, covenant, insurance, holdback, CP |
| `statement` | string | the control |
| `truth_state` | enum | engine-graded; a mitigant only "counts" at CORROBORATED+ |
| `residual_risk` | string | **mandatory** — what remains after the mitigant (FR-M8) |

Rule: a Mitigant is aspirational-forbidden — must be structural/documentary
(`term-mitigant`). Residual severity is a **rendering-time compute**, not a ledger state.

## 6. SeverityGrade  (Axis S)

The domain-owned materiality axis — the ONLY engine extension.

| Field | Type | Notes |
|-------|------|-------|
| `axis_s_materiality` | ordinal enum | `informational < limitation < material-risk < deal-breaker-candidate` |
| `raised_by_role` | seat_id | scoring seat |
| `rationale` | string | why this materiality |

Stored on the fact as `_ic_extension_severity`. **Orthogonal to Axis A/B — never averaged
or blended into the truth grade** (a stale insurance cert and a no-enforceable-lien objection
grade identically on truth but differ on Axis S). Measured by `metric-severity-ladder`.

## 7. Round

A deliberation cycle (both modes: opening = round 0; rebuttal rounds 1..N, cap 5-6).

| Field | Type | Notes |
|-------|------|-------|
| `round_id` | int | 0 = blind openings |
| `kind` | enum | `opening \| rebuttal \| premortem \| devils-advocate \| tenth-man \| synthesis` |
| `dispatched_seats` | [seat_id] | who spoke |
| `status` | enum | `open \| paused_for_human \| closed` |
| `tally` | object | deterministic tally result (responded/majority/veto/converged) |

Relationships: *─1SessionManifest; 1─*Turn.

## 8. Turn  (Mode B)

One seat's contribution in a round. Persisted to disk BEFORE the next dispatch.

| Field | Type | Notes |
|-------|------|-------|
| `turn_id` | string | `rNN-<seat>-<seq>` |
| `round` | int | |
| `seat` | seat_id | speaker label |
| `stance` | enum | `SUPPORT \| REBUT \| ABSTAIN \| CONDITIONAL \| FLAG_RISK` (FR-M11) |
| `argument` | string | <=150-250 words (UX cap) |
| `addresses_prior_turn_ids` | [turn_id] | what it answers |
| `would_change_mind_if` | string | justification-forcing hook |
| `updated` | bool | reversal -> rendered `⟲ UPDATED` |

## 9. HumanInjection

A chair message as a first-class transcript turn (FR-M12).

| Field | Type | Notes |
|-------|------|-------|
| `turn_id` | string | recorded like a Turn |
| `seat` | const | `HUMAN_OVERSEER` |
| `stance` | const | `HUMAN_OVERSEER` |
| `message` | string | chair text / command |
| `implicated_seats` | [seat_id] | who must address it next round |

Rule: the next round's implicated seats MUST update-with-a-named-new-fact or
hold-with-a-reason — never capitulate. Chair authority is procedural, not evidentiary
(FR-M13). Persisted as `rounds/round-NN/human-injection.json`.

## 10. Transcript

The append-only source-of-truth record (NFR-4).

| Field | Type | Notes |
|-------|------|-------|
| `transcript_md` | path | human-readable append-only render |
| `turn_records` | [path] | `rounds/round-NN/turns/*.json` |
| `head` | string | last-appended turn_id (resume pointer) |

Rule: conversation memory is never authoritative; every turn hits disk immediately
(`pattern-transcript-on-disk`). Survives `/clear`, crash, Eternity resume.

## 11. Verdict

The deterministically-computed committee decision (never narrated).

| Field | Type | Notes |
|-------|------|-------|
| `verdict` | enum | `PROCEED \| PROCEED-WITH-CONDITIONS \| DECLINE \| UNRESOLVED` |
| `deciding_rung` | string | which precedence rung / polarity decided (audit) |
| `polarity` | enum | `asymmetric_veto` (deal-breaker claims) \| `quorum` (ordinary) |
| `deal_breakers` | [objection_id] | derived: state∈{ESTABLISHED,CORROBORATED} AND axis_s>=material-risk AND no CORROBORATED+ mitigant |
| `surviving_conditions` | [mitigant_id] | become Conditions Precedent on PROCEED-WITH-CONDITIONS |
| `unresolved_conflicts` | [conflict] | both sides preserved, no fabricated winner |
| `ledger_head` | string | reproducibility anchor (NFR-3) |

Computed by `resolve.py` over per-discipline roll-ups. NOT an LLM narration
(`anti-narrated-verdict`).

## 12. ConditionPrecedent (CP)

A binding pre-funding gate that converts a risk into an approvable deal.

| Field | Type | Notes |
|-------|------|-------|
| `cp_id` | string | |
| `retires_objection` | objection_id | each CP tagged to the risk it retires (FR-M8) |
| `source_mitigant` | mitigant_id | the surviving mitigant it operationalizes |
| `text` | string | the condition |
| `owner` | string | deal-team owner |

## 13. ConflictsDisclosure

Per-run governance artifact (FR-M19; SEC 2026 fiduciary focus).

| Field | Type | Notes |
|-------|------|-------|
| `session_id` | string | |
| `seat_disclosures` | [{seat_id, disclosed_conflicts}] | each seat discloses before voting |
| `process_attestations` | [string] | independence-first honored, verdict deterministic, etc. |
| `reduced_independence` | bool | single-provider flag surfaced |

On disk: `conflicts-disclosure.yaml` (`conflicts-disclosure`, `std-sec-2026`).

## 14. ICMemo

The rendered 13-section recommendation (Mode A / Mode B final).

| Field | Type | Notes |
|-------|------|-------|
| `path` | path | `recommendation.md` |
| `sections` | [13] | agent-08 canon (BLUF -> ... -> Recommendation + Key Judgment Calls) |
| `bluf` | object | verdict box (mirrors Verdict) |
| `risk_triplet_table` | [{risk, mitigant, residual, cp_refs}] | repeating triplet (FR-M8) |
| `independence_note` | string | reduced-independence flag surfaced |
| `rendered_from_ledger` | bool | must be `true` — never hand-edited |

## 15. EvidenceCitation

A source reference attached to an Objection/Mitigant.

| Field | Type | Notes |
|-------|------|-------|
| `citation_id` | string | |
| `source_ref` | string | doc path + locator (clause/page) |
| `tier` | enum | T1..T5 (evidence-ledger convention) |
| `entity_ref` | string | collateral/entity id — basis for same-fact detection (open surface) |

## 16. SessionManifest

The run's control record and resume anchor.

| Field | Type | Notes |
|-------|------|-------|
| `session_id` | string | `.acos/investment-committee/<session-id>/` |
| `deal` | Deal | context |
| `mode` | enum | `A \| B` |
| `roster` | [Seat] | resolved seats + ExpertProfiles |
| `round_config` | object | cap (5-6), turn cap (150-250w), checkpoint interval (3) |
| `status` | enum | `open \| paused_for_human \| closed` |
| `current_round` | int | resume pointer |
| `autopilot_detected` | bool | `.acos/state/autopilot-active` present at entry |
| `reduced_independence` | bool | single-provider flag |
| `ledger_head` | string | axiom-synthesis ledger head |

On disk: `manifest.yaml`. State machine: `open -> paused_for_human -> open -> ... -> closed`.

---

## 17. On-disk layout mapping (entities -> files)

```
.acos/investment-committee/<session-id>/
  manifest.yaml                       # SessionManifest, Deal, roster(Seat+ExpertProfile)
  transcript.md                       # Transcript (append-only render)
  rounds/round-NN/
    opening/{seat}.json               # blind opening Objections (both modes)
    turns/{turn-id}.json              # Turn records (Mode B)
    human-injection.json              # HumanInjection
    round-status.yaml                 # Round.status + tally + resume pointer
  conflicts-disclosure.yaml           # ConflictsDisclosure
  ledger/                             # axiom-synthesis hash-chained facts (Objection/Mitigant)
    settled-objections.md             # falsification-gate audit (EvidenceCitation trail)
  recommendation.md                   # ICMemo (13-section)
  verdict.md                          # Verdict (deterministic + deciding_rung)
```

## 18. Engine-contract fidelity note

The IC skill adds **exactly one** thing to axiom-synthesis: the `_ic_extension_severity`
blob on each `fact` (Objection). Everything else — Objection, Mitigant, conflict resolution,
truth states, ledger, verdict-as-fact — uses the engine's existing shapes unchanged. The
deal-breaker predicate and residual-severity are **derived at render time from ledger state +
Axis S**, not stored as engine fields. This is what keeps "is it true" (engine, mechanical)
separate from "is it fatal" (domain, computed after truth settles). `covers`/coverage-gate
tags carry the 16-risk-map coverage assertion used by `metric-risk-coverage`.
