# SLICE-A2-expert-agent-defs — Expert seat agent definitions

**Parent story:** STORY-A2 · **Epic:** EPIC-A · **Effort:** M · **Demo:** Demo 1 (3-seat) -> Demo 2 (full)
**slice.yaml mapping:** Objective->`objective`; Allowed files->`files_allowed`;
DoD+evidence gates->`acceptance_criteria`; QA verification->`verification_method`.

## PM (Planner / LCE brief)

**Objective (single, narrow):** Author the seat expert-agent prompt templates that
instantiate each numbered Seat as an isolated `Task()` agent with an independence-first,
falsifiable-objection mandate and per-seat diversity config. Deliver the **3-seat subset for
Demo 1 — #1 Credit & Valuation, #3 Accounting, #4 Legal & Structural** (this trio also
demonstrates the Accounting-owns-NOI fraud tripwire: #1 and #3 must independently arrive at
consistent NOI or escalate), then the **full numbered roster for Demo 2 — add #2 Finance,
#5 Insurance & Climate, #6 Sponsor & Fraud-Forensics, #7 Portfolio & Concentration, #8
Strategy, #9 Deal Advocate (NEW), #10 Gap-Hunter/Chair-agent** (10 templates total).

**In-scope:** one prompt template per seat encoding: seat charter + owned risk categories
(per `roster.yaml` / `coverage-map.yaml` from SLICE-A1); open-blind (independence-first);
mandatory >=1 **falsifiable** objection ("the deal fails if/because ___; evidence
present/absent/untested"); the chair's opinion carries **no evidentiary weight**;
agreement-without-new-evidence forbidden; confidence is *derived* not self-reported;
seat-specific distinctive mandates:
- **#1 Credit & Valuation:** runs and clearly labels its TWO sub-passes (collateral-value,
  repayment-capacity); reconciles its own NOI figure against #3 Accounting's and flags a
  disagreement rather than silently picking one.
- **#3 Accounting:** OWNS the single normalized-NOI claim; explicit instruction that #1 and
  #2 consume this number and a disagreement is a mandatory escalation, not a quiet override.
- **#4 Legal & Structural:** the environmental-legal sub-lens (CERCLA secured-lender shield,
  Phase I ASTM E1527-21 currency) is scoped ONLY to legal/financial materiality — the
  template must NOT ask this seat to perform a full physical/environmental condition review
  (that is optional seat #15).
- **#6 Sponsor & Fraud-Forensics:** the "assume fabricated until externally corroborated"
  mandate.
- **#7 Portfolio & Concentration:** the fund/loan-tape scope (NOT deal-scoped).
- **#8 Strategy:** held to the SAME falsifiable-objection discipline as every other seat —
  must produce a falsifiable "the deal fails strategically because ___" objection or
  abstain; the template must explicitly state this seat is **NOT an advocate** for the deal
  (no cheerleading mandate, no packaging role).
- **#9 Deal Advocate (NEW):** structurally separate from Gap-Hunter (#10) and from every
  scrutiny seat; steelmans the deal and answers objections with the **best good-faith
  mitigant the evidence supports** — no hole-hunting, no scrutiny vote (`voting: false`,
  `owned_risk_categories: []`); its mitigants are held to the SAME falsification gate as
  objections (fact-builder/axiom-synthesis grades a mitigant claim exactly like an objection
  claim — cited or discounted, never taken on faith); the template must explicitly forbid
  fabricating a mitigant not supported by the evidence — argue in good faith, concede when
  the evidence does not support a mitigant.
- **#10 Gap-Hunter/Chair-agent (renumbered from the former #9):** procedural, **non-voting**;
  its distinctive mandate is selecting (each round) which seat(s) have something material to
  add and hunting for risks nobody claimed — it does not itself cast a scrutiny vote and does
  NOT steelman the deal (that is the Advocate #9's role; the two are never collapsed).
Diversity resolution via `resolve-agent-model.sh`.

**Per-expert private research swarms (new capability — feeds SLICE-B3):** every seat template
for the 9 "expert" seats (#1-9 — the 8 voting seats plus the Deal Advocate) MUST grant
`Task(general-purpose)` tool access and carry a standard instruction block: *"After reading
the shared deal-brief and evidence-index, spawn your OWN private swarm of 2-4
`Task(general-purpose)` research bots, sized to what your discipline actually needs for this
deal. Each bot reports ONLY to you — never to another seat, never to the chair. Fold your
swarm's cited findings into your objection (or, for the Advocate, your mitigant). Capture
every citation your swarm returns so it can feed the evidence ledger."* The Gap-Hunter (#10)
is procedural only and does **NOT** spawn a swarm (it has no discipline-specific research
need — its job is selecting speakers and hunting for unclaimed risks, not deep research). The
actual swarm-spawn mechanics (bounds enforcement, isolation, citation capture) are built in
SLICE-B3; this slice only wires the capability + instruction into the 9 expert templates.

**Out-of-scope:** the fan-out orchestration (SLICE-B2); the per-expert swarm-spawn mechanism
itself (SLICE-B3); the fact-builder (C1); Mode B turns.

**Allowed files/contexts:** `.claude/skills/acos-investment-committee/seats/{seat}.md`
templates; `scripts/resolve_seat_model.sh` wrapper over `resolve-agent-model.sh`; READ-ONLY:
`roster.yaml`, spec §UX + §4.1, domain-lattice `seat-*` + `method-model-diversity`.

**Step-by-step:**
1. Write #1 Credit & Valuation, #3 Accounting, #4 Legal & Structural templates (Demo 1).
   Each ends with a required opening-verdict JSON schema stub (verdict + >=1 falsifiable
   objection + Axis S self-score); #1 and #3 templates cross-reference the shared-NOI
   reconciliation rule (without violating independence-first — reconciliation happens at
   fact-builder/synthesis time, NOT by one seat reading the other's output).
2. Add #2 Finance, #5 Insurance & Climate, #6 Sponsor & Fraud-Forensics, #7 Portfolio &
   Concentration, #8 Strategy, **#9 Deal Advocate (NEW)**, #10 Gap-Hunter/Chair-agent
   (Demo 2 — 10 templates total). Fraud + Portfolio carry their distinctive mandates
   (adversarial veracity / fund-scope); Strategy carries the NOT-an-advocate
   falsifiable-objection mandate; the Deal Advocate carries the steelman/good-faith-mitigant
   mandate under the same falsification gate as objections; Gap-Hunter carries the
   non-voting selection/hunting mandate and is kept structurally distinct from the Advocate.
3. Grant `Task(general-purpose)` access + the standard "spawn your 2-4 research bots"
   instruction block to the 9 expert templates (#1-9); confirm the Gap-Hunter (#10) template
   deliberately omits it.
4. Wire `resolve_seat_model.sh` to assign a model class + persona/temperature per seat; emit
   `reduced_independence: true` when all seats resolve to one provider.

**Definition of Done:**
- Artifacts: `seats/*.md` (3 for Demo 1, 10 for Demo 2), `scripts/resolve_seat_model.sh`.
- Validation: every voting-seat template contains the falsifiable-objection requirement, the
  procedural-not-evidentiary chair note, and the no-agreement-without-evidence clause; the
  Deal Advocate (#9) template contains its steelman/good-faith-mitigant clause and the
  no-scrutiny-vote / no-fabrication constraints instead of a falsifiable-objection
  requirement; the Gap-Hunter (#10) template contains its non-voting selection mandate
  instead of a scrutiny-vote clause; every expert template (#1-9) grants
  `Task(general-purpose)` + the swarm-spawn instruction, and the Gap-Hunter (#10) template
  does not; diversity resolver returns a model class per seat and the flag when
  single-provider.
- Evidence bundle: a dry-run resolver transcript listing each seat (by number) -> model/
  persona + flag; a template-lint listing confirming which seats carry the swarm-spawn
  instruction (#1-9) and which does not (#10).

## Dev (Executor)

**Execution notes:** subscription-only; seats spawned by later slices via `Task()`. Do NOT
let any template reference another seat's output (independence-first is a template
invariant) — this includes #1 not reading #3's NOI and vice versa, and the Advocate (#9) not
reading any scrutiny seat's objection before forming its mitigant; NOI reconciliation and
objection/mitigant reconciliation are both fact-builder/synthesis-time concerns, not
cross-seat reads.

**Evidence Bundle:** 1) Summary; 2) Traceability (FR-M3, FR-M4, FR-M13, FR-M18, FR-S4); 3)
Quality (template lint: every voting seat has the 3 required clauses; the Advocate has its
steelman/no-fabrication clauses; Gap-Hunter has its non-voting clause; swarm-spawn
instruction present on #1-9 and absent on #10); 4) Testing (resolver dry-run, flag
behavior); 5) Compliance (no cross-seat references; subscription-only); 6) Operational; 7)
Self-assessment.

## QA (Zero-Trust Verifier)

Verify by reading EACH template (do not trust a summary claim): (a) grep every voting seat
for the falsifiable-objection clause, the "no evidentiary weight" chair note, and the
no-agreement-without-evidence clause — all must be present; (b) confirm Fraud (#6) has the
"assume fabricated" mandate and Portfolio (#7) has fund/loan-tape scope; (c) confirm
Accounting (#3) explicitly states it owns the normalized-NOI claim and Credit & Valuation
(#1) explicitly reconciles against it; (d) confirm Legal & Structural (#4) scopes its
environmental sub-lens to legal/financial materiality only (no full condition-review
language); (e) confirm Strategy (#8) has the falsifiable "fails strategically because ___"
clause AND an explicit "NOT an advocate" statement; (f) confirm the Deal Advocate (#9) is
`voting: false`, carries the steelman/good-faith-mitigant mandate, the same-falsification-gate
clause for mitigants, and an explicit no-fabrication constraint — and does NOT carry the
scrutiny falsifiable-objection requirement; (g) confirm Gap-Hunter (#10) is explicitly
non-voting AND distinct from the Advocate (#9) — reject if the two roles were merged into one
template or one seat_id; (h) confirm every expert template (#1-9) grants
`Task(general-purpose)` + the swarm-spawn instruction and the Gap-Hunter (#10) template does
NOT; (i) confirm NO template references another seat's findings; (j) run the resolver and
confirm the reduced-independence flag fires when forced single-provider. Reject if any seat
is missing a required clause.

**Evidence gates:** all voting-seat templates carry the 3 invariant clauses; fraud/portfolio
mandates present; Accounting/NOI and Legal/environmental-scoping clauses present; Strategy's
not-an-advocate clause present; Deal Advocate's steelman/no-fabrication clauses present and
distinct from Gap-Hunter's non-voting clause; swarm-spawn instruction present on #1-9 only;
zero cross-seat references; flag fires single-provider.

## Dev Learnings
_(fill: persona wording that changed vs did not change objection quality; diversity mapping;
how the Advocate's "good-faith mitigant" instruction was worded to avoid slipping into
cheerleading.)_

## QA Learnings
_(fill: which clause omissions slipped through; independence-leak checks; any case where the
Advocate template drifted toward objection-hunting or the Gap-Hunter drifted toward
advocacy.)_
