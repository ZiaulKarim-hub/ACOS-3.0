# Competency Questions — ACOS Investment Committee (003-investment-committee)

**Command:** `/preeng.research` — Phase 1 CQ set + Phase 2 lattice-answerability check.
Each CQ is answerable from `domain-lattice.json` (verified: 100% of the 12 required CQ
nodes reach a method/process AND a metric/standard within 2 hops — see
`research_qa_report.json`). Required CQs come from `command_inputs.research.required_cqs`;
derived CQs (CQ-13..CQ-15) extend coverage.

Legend: **Lattice node** = the `cq` node id; **Answered via** = the primary lattice path.

---

## Required competency questions (12)

**CQ-01 — What disciplines constitute a complete IC panel with zero uncovered risk category?**
- Lattice node: `cq-01`
- Answer: 7 core seats (Credit & Cash-Flow, Collateral Valuation, Legal & Structural,
  Environmental & Physical, Insurance & Climate, Sponsor & Fraud-Forensics, Portfolio &
  Concentration) + a Chair/Gap-Hunter that hunts for risks nobody claimed. Validated against
  the 16-risk coverage map.
- Answered via: `seat-chair`, `method-map`, `metric-risk-coverage`, `std-occ-cre`. [ev-01..03]

**CQ-02 — How is the deal advocate kept structurally independent of the adversarial credit seat?**
- Lattice node: `cq-02`
- Answer: the Deal Advocate/Underwriting Lead packages the ask and MUST NOT cast a scrutiny
  vote; the adversarial Credit seat is a separate voice (three-lines-of-defense / independence
  principle; OCC independent loan review).
- Answered via: `proc-independence-first`, `std-three-lines`, `seat-advocate`. [ev-01]

**CQ-03 — How do we elicit genuine dissent and avoid sycophancy / correlated same-model error?**
- Lattice node: `cq-03`
- Answer: independence-first blind opening pass; model-class/persona diversity; forbid
  agreement-without-new-evidence; assigned rotating devil's advocate + 10th-man; derived (not
  self-reported) confidence; reduced-independence flag when single-provider.
- Answered via: `method-blind-first-pass`, `method-devils-advocate`, `metric-independence-flag`.
  [ev-08..10]

**CQ-04 — How is a live, interruptible, human-chaired deliberation realized on Claude Code primitives?**
- Lattice node: `cq-04`
- Answer: subagents cannot call AskUserQuestion, so the Mode B moderator is the top-level
  SKILL.md (main conversation); an append-only transcript on disk is the source of truth;
  presented honestly as a moderated relay, not real-time.
- Answered via: `proc-mode-b`, `pattern-main-convo-moderator`, `method-justification-forcing`.
  [ev-24, ev-28]

**CQ-05 — How does an expert objection map onto an axiom-synthesis atomic claim + a severity axis?**
- Lattice node: `cq-05`
- Answer: each objection becomes an atomic `fact` consumed by `orchestrate.py`, extended with
  a domain-owned Axis S (severity/materiality) on a fixed ordinal ladder, stored alongside
  Axis A (reliability) and Axis B (certainty), never blended.
- Answered via: `engine-axiom-synthesis`, `method-severity-axis-s`, `metric-severity-ladder`.
  [ev-19, ev-20]

**CQ-06 — How is the overall PROCEED/DECLINE verdict computed deterministically without fabricating consensus?**
- Lattice node: `cq-06`
- Answer: one `resolve_conflict()` over per-discipline roll-ups; asymmetric-veto polarity on
  deal-breaker-flagged claims (false-accept is catastrophic); quorum/ladder otherwise;
  terminates in UNRESOLVED; never narrated by an LLM.
- Answered via: `proc-deterministic-verdict`, `method-asymmetric-veto`,
  `metric-severity-ladder`, `term-unresolved`. [ev-11, ev-21, ev-22]

**CQ-07 — What is the canonical IC-memo structure and the Risk -> Mitigant -> Residual -> CP pattern?**
- Lattice node: `cq-07`
- Answer: a 13-section canon built on the 5 C's; risks written as a bound triplet (Risk ->
  Mitigant -> Residual) with each Condition Precedent tagged to the risk it retires; BLUF
  recommendation box.
- Answered via: `pattern-risk-mitigant-residual`, `artifact-ic-memo`, `std-occ-cre`. [ev-34, ev-35]

**CQ-08 — Which legal/compliance checks are deal-breakers vs curable-by-condition, and what does legal-analyst already cover?**
- Lattice node: `cq-08`
- Answer: delegate A1-A8 document diligence to `legal-analyst`; a compliance companion covers
  its four gaps (usury/licensing, AML/KYC/OFAC, foreclosure mechanics, Phase I currency).
  Deal-breakers vs curable enumerated in spec Appendix D.
- Answered via: `proc-legal-delegation`, `engine-legal-analyst`, `std-astm-e1527`,
  `term-deal-breaker`. [ev-30..32]

**CQ-09 — How does the human chair observe and inject, and how do agents value human input without capitulating?**
- Lattice node: `cq-09`
- Answer: human text is a first-class `HUMAN_OVERSEER` turn; the next round MUST address it
  (update-with-a-named-new-fact or hold-with-a-reason); the chair's authority is procedural,
  not evidentiary.
- Answered via: `method-justification-forcing`, `proc-mode-b`, `metric-independence-flag`.
  [ev-25, ev-29]

**CQ-10 — How is concentration risk (fund-scoped) and financial-statement fraud explicitly owned?**
- Lattice node: `cq-10`
- Answer: a fund-scoped Portfolio & Concentration seat with loan-tape access (not deal-scoped);
  an explicit adversarial Fraud-Forensics mandate ("assume fabricated until externally
  corroborated"). Both are the default silent-PASS gaps.
- Answered via: `seat-portfolio`, `seat-fraud`, `metric-risk-coverage`, `std-fincen-cre-fraud`.
  [ev-04, ev-05]

**CQ-11 — What guardrail handles autopilot-active silently auto-answering the human pause?**
- Lattice node: `cq-11`
- Answer: detect `.acos/state/autopilot-active`; refuse deep-pause Mode B or fall back to a
  documented autonomous batch mode; make the "(Recommended)" pause option safe under auto-pick.
- Answered via: `proc-autopilot-detection`, `risk-autopilot-auto-answer`,
  `metric-independence-flag`. [ev-27]

**CQ-12 — How is the deliberation state persisted so it survives /clear and Eternity resume?**
- Lattice node: `cq-12`
- Answer: transcript-as-source-of-truth — every turn hits disk immediately; resume reads
  `manifest.yaml` + `round-status.yaml` to re-enter at the last-closed round.
- Answered via: `pattern-transcript-on-disk`, `artifact-transcript`, `proc-mode-b`. [ev-26]

---

## Derived competency questions (extend coverage)

**CQ-13 — When does multi-agent debate help vs hurt, and how is that reflected in the design?**
- Answer: debate does not reliably beat voting on a no-ground-truth judgment and can amplify
  confident-wrong agents; therefore debate is used for legibility + hole-finding + human
  participation, and accuracy is loaded onto structural guardrails. Answered via
  `anti-consensus-as-correctness`, `proc-falsification-gate`, `proc-deterministic-verdict`.
  [ev-11, ev-12, ev-36]

**CQ-14 — How is model/persona diversity used and reduced-independence surfaced under subscription-Claude?**
- Answer: per-seat Opus/Sonnet + persona/temperature diversity via the Model Profile system;
  emit a reduced-independence flag when all seats share one provider. Answered via
  `method-model-diversity`, `metric-independence-flag`, `anti-correlated-same-model`. [ev-10]

**CQ-15 — How is a same-underlying-fact cross-discipline conflict detected and resolved without prose-blending?**
- Answer: route each same-fact conflict through `resolve_conflict()` as `fact["conflict"]`,
  never an aggregator-LLM blend; entity-linking to detect "same atomic fact" is an open design
  surface. Answered via `anti-llm-aggregator-blend`, `engine-axiom-synthesis`, `term-unresolved`.
  [ev-23] (Open item — see spec Open Questions #8.)

---

## Answerability summary

- Required CQs: 12/12 answerable from the lattice (100%); each reaches >=1 method/process and
  >=1 metric/standard within 2 hops (mechanical check in `research_qa_report.json`).
- Derived CQs: 3 additional, each grounded in existing lattice nodes + ledger entries.
- Coverage target (>=95%) met.
