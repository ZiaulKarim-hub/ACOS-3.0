# Research Dossier — ACOS Investment Committee (003-investment-committee)

**Command:** `/preeng.research` — Phase 4 emission (narrative synthesis).
**Precondition:** `spec.md` exists.
**Companion artifacts:** `domain-brief.md`, `domain-cqs.md`, `domain-lattice.json`
(78 nodes / 119 edges / 100% CQ coverage), `evidence-ledger.json` (36 tiered entries),
`research_qa_report.json`.
**Primary evidence base:** the swarm synthesis
(`.acos/swarm/swarm-20260707-141351/synthesis/report.md`) + 10 blind, isolated agent
findings, tiered T1 (authoritative) -> T5 (internal ACOS).

---

## 1. Executive synthesis

The research converges on a counter-intuitive thesis: **the best-possible AI Investment
Committee is NOT built by making agents argue their way to the right answer.** Three
independent technical agents found that multi-agent LLM debate does not reliably beat simple
voting on accuracy, that **consensus is not evidence of correctness** (confident-wrong agents
drag the group down and grow *more* overconfident as they argue), and that an approve/decline
call has no ground truth — so it behaves more like the troubling social-persuasion literature
than the reassuring math-benchmark literature. Accuracy therefore comes from **structural
guardrails**, not from more talking. Debate's value is **legibility, adversarial hole-finding,
and genuine human participation.**

Three load-bearing architectural findings follow:

1. **Independence-first** — every seat forms its opening verdict in an isolated context with
   zero cross-visibility before any cross-talk — is the single highest-leverage anti-
   groupthink lever, and it is already a proven ACOS pattern (grader blind re-dispatch, dr2
   blind deliberators, axiom-synthesis blind cross-family elicitation). [ev-08]
2. **Reuse over rebuild** — the IC skill is a thin orchestrator + domain adapter over engines
   ACOS already has: `acos-axiom-synthesis` for Mode A synthesis, `legal-analyst` for the
   legal seat, Wigum-loop + `consensus_check.py` + blind-dispatch for orchestration. [ev-19,
   ev-30]
3. **The main conversation must be the Mode-B moderator** — subagents physically cannot call
   `AskUserQuestion`, so only the top-level SKILL.md can pause for a live human; an append-
   only transcript on disk is the source of truth. [ev-24]

---

## 2. The five sub-domains

### 2.1 IC governance (agents 01, 02)
Institutional ICs run ~5-9 voting seats and structurally separate the deal team from
credit/risk (the independence principle / three-lines-of-defense). A minimum-complete
lending IC needs 7 core seats + a Chair/Gap-Hunter, because gap zones — by definition — do
not surface in any single expert's output. Two risks are **nobody's job by default**: fund-
level concentration (no single-deal file holds fund exposure -> silent PASS unless the
Portfolio seat is fund-scoped with loan-tape access) and financial-statement veracity (Credit
trusts the T-12, Valuation trusts Credit's NOI, Accounting checks format, Legal never opens
the spreadsheet -> needs an explicit adversarial Fraud-Forensics mandate). [ev-01..05]

### 2.2 Multi-agent debate (agents 03, 06)
Debate improves accuracy only *conditionally* (checkable structure, capable models, bounded
rounds, genuine diversity) and can backfire otherwise. Same-model ensembles share correlated
errors (0.679 vs 0.396 cross-family); 10 same-model agents behave like ~1.4 independent
forecasters. Sycophancy is large and RLHF-native (~58%; 63.7% agreement with an asserted
incorrect belief). The design implications: never terminate on consensus, hide mid-debate
confidence, derive confidence (never self-report), default to model-class/persona diversity,
and emit a reduced-independence flag when single-provider. [ev-08..12]

### 2.3 Hole-finding methodology (agent 05)
A ranked, mechanically-enforceable protocol stack: independent-first sequencing; a mandatory
falsifiable objection per seat; decomposed per-dimension scoring before any holistic verdict
(MAP); reference-class/base-rate checks; a standing hole-category checklist explicitly
cleared; assigned rotating devil's advocate + consensus-triggered 10th-man; pre-committed,
mechanically-applied kill criteria run FIRST; and a mitigant + explicit residual-risk required
for every non-fatal finding. The largest caveat: because framing alone may not change LLM
reasoning, treat **mechanical enforcement** (isolation, required schema fields, sequencing) as
load-bearing, not persona-prompting. [ev-13..18]

### 2.4 Synthesis -> verdict (agent 07)
`acos-axiom-synthesis` is a near-exact structural fit (fixture-tested, 54 assertions, Phases
0-7): blind decompose -> de-circularization firewall -> two-axis grading -> claim-level fusion
-> falsification gate -> precedence-ladder resolver terminating in UNRESOLVED -> hash-chained
ledger. The one required extension is a domain-owned **Axis S (severity/materiality)** — the
engine grades TRUTH, not "how bad if true"; a stale insurance cert and a no-enforceable-lien
objection grade identically today. The overall verdict is one `resolve_conflict()` over
per-discipline roll-ups with asymmetric-veto polarity on deal-breakers, computed
deterministically and never narrated. The naive MoA aggregator-LLM blend is the exact anti-
pattern the engine avoids. [ev-19..23]

### 2.5 HITL deliberation UX + legal (agents 04, 09, 10)
Mode B is a **moderated relay / structured written deposition with a chair**, not a fake
real-time room: discipline-named speaker labels, per-turn stance badges, a ~150-250 word turn
cap, pause-after-each-round default, and scoreboard/checkpoint reprints (the terminal has no
sidebar). The chair has full *procedural* authority but their stated opinion carries **no
automatic evidentiary weight** — an IC exists precisely to catch a human railroading a deal
under closing pressure. The legal seat delegates document diligence to `legal-analyst` and
adds a compliance companion (usury/licensing, AML/KYC/OFAC, foreclosure mechanics, Phase I
ASTM E1527-21 currency) plus a per-run `conflicts-disclosure.yaml` (SEC 2026 fiduciary focus).
[ev-24..35]

---

## 3. Evidence quality & tiers

The evidence ledger holds 36 entries. Tier distribution: **T1 authoritative** (7 — OCC,
FDIC, FinCEN, ASTM E1527-21, CERCLA §101(20), SEC 2026, Utah Commercial Financing
Registration); **T2 expert** (8 — three-lines-of-defense, IC-memo canon, valuation
triangulation, insurance-as-underwriting); **T3 empirical/academic** (12 — SycEval,
correlated-error study, Du et al. MAD, Kahneman MAP/Noise, Klein pre-mortem, Flyvbjerg RCF,
Heuer ACH, KKR/Audax devil's-advocate); **T5 internal ACOS** (9 — axiom-synthesis,
legal-analyst, dr2 consensus_check, fin-stmt bounce-up idiom, autopilot handler,
transcript-on-disk). No T4 community-tool sources were load-bearing.

**Confidence posture:** every architecture claim is grounded in an existing ACOS asset where
one exists (per `evidence_requirements`). The two lattice nodes not directly cited by a ledger
entry (`metric-cq-coverage`, a process-governance meta-metric defined in `domain-brief.md`;
and `risk-refi-exit`, supported transitively by ev-06 and ev-15) carry evidence via adjacent
entries or governance definitions, not a structural gap.

---

## 4. Data gaps (open, honestly reported)

1. **No public precedent** for terminal-CLI, human-chaired, multi-agent financial debate, or
   for MAD on a no-ground-truth IC judgment — greenfield; pilot and instrument, do not assume
   (round cap 5-6, turn cap 150-250w, checkpoint every 3 are reasoned defaults). [ev-36]
2. **Axis S does not exist in the built engine** and "same underlying fact" cross-discipline
   detection is undefined — a new domain-owned field + an entity-linking design surface. [ev-20,
   ev-23]
3. **OKOA governance unknowns** — SEC adviser-registration status, any codified SPE/bankruptcy-
   remoteness size threshold, and the full active-state lending footprint — marked `Assumption`
   in spec Open Questions; confirm before hardcoding legal rules. [ev-31, ev-33]
4. **autopilot-active x interactive IC** behavior is inferred from the hook script, not
   observed — smoke-test once the skill exists. [ev-27]
5. **No live ground-truth IC case** has been run through the pipeline yet.

---

## 5. Recommendations (carried into `plan.md`)

- Build the IC skill as a thin orchestrator over existing engines. [High]
- Independence-first blind opening pass in BOTH modes, mechanically enforced. [High]
- Main conversation is the Mode-B moderator; transcript-on-disk; detect autopilot-active. [High]
- Never terminate on consensus; preserve dissent; hide mid-debate confidence; verdict computed
  deterministically with asymmetric-veto on deal-breakers -> PROCEED / PROCEED-WITH-CONDITIONS
  / DECLINE / UNRESOLVED. [High]
- Core 7 seats + Chair/Gap-Hunter; advocate structurally separate from adversarial credit;
  Portfolio seat fund-scoped. [High]
- Mandatory hole-finding protocol enforced mechanically, not by persona alone. [High]
- Mode A memo follows the 13-section canon with the Risk->Mitigant->Residual triplet + CP
  tagging; add Axis S orthogonal to truth-grading. [High]
- Legal seat = delegate to legal-analyst + compliance companion + conflicts-disclosure. [High]
- Model-class/persona diversity; reduced-independence flag when single-provider. [Medium]
- Pilot Mode B on a real OKOA deal to tune round/turn/checkpoint constants. [Investigate]

---

## 6. Audit trail

- Swarm plan: `.acos/swarm/swarm-20260707-141351/plan.md`
- Findings: `.acos/swarm/swarm-20260707-141351/agent-{01..10}/findings.md`
- Synthesis: `.acos/swarm/swarm-20260707-141351/synthesis/report.md`
- Lattice/ledger generated deterministically and schema-validated (see
  `research_qa_report.json`).
