# Domain Brief — ACOS Investment Committee (003-investment-committee)

**Command:** `/preeng.research` — Phase 1 (Domain List Generation).
**Precondition met:** `spec.md` exists.
**Evidence base:** `.acos/swarm/swarm-20260707-141351/synthesis/report.md` + agents 01-10 findings
(tiered in `evidence-ledger.json`).

## Domain framing

The Investment Committee (IC) domain sits at the intersection of five sub-domains that the
swarm research independently converged on:

1. **Institutional IC / credit-committee governance** for PE real-estate & private credit
   (roster design, independence principle, voting mechanics, conditions precedent).
2. **Multi-agent LLM debate/deliberation** (when it helps vs hurts; consensus ≠ correctness;
   independence-first; correlated error).
3. **Structured hole-finding methodology** (pre-mortem, MAP, dialectical inquiry, ACH,
   reference-class forecasting, kill criteria).
4. **Refutation-and-grading synthesis** via `acos-axiom-synthesis` (objection -> atomic
   claim, severity axis, deterministic verdict, UNRESOLVED-not-fabricated).
5. **RE-PE legal / regulatory / fiduciary diligence** and reuse of `legal-analyst`.

The unifying thesis: the best AI IC gets its accuracy from **structural guardrails**
(independence, diversity, falsification, evidence-only confidence, deterministic verdict),
not from making agents argue their way to an answer. The skill is a **thin orchestrator +
domain adapter** over engines ACOS already has.

---

## Domain List (structured)

### Entities

- **Seats (7 core + chair + advocate):** Credit & Cash-Flow; Collateral Valuation; Legal &
  Structural; Environmental & Physical; Insurance & Climate; Sponsor & Fraud-Forensics;
  Portfolio & Concentration (fund-scoped); Chair / Gap-Hunter (meta); Deal Advocate /
  Underwriting Lead (packages the ask, non-voting). Deal-triggered optionals:
  Construction/Completion, Tax, Exit & Capital Markets, Market/Macro, Compliance/Regulatory.
- **Engines / assets reused:** `acos-axiom-synthesis` (Mode A synthesis); `legal-analyst` +
  `/acos-legal-analysis` (legal seat); Model Profile system (`resolve-agent-model.sh`); dr2
  `consensus_check.py` (deterministic tally); `fin-stmt-accountant` bounce-up idiom.
- **Artifacts:** IC memo (`recommendation.md`); append-only transcript; hash-chained ledger
  + `settled-objections.md`; `conflicts-disclosure.yaml`; `manifest.yaml` / `round-status.yaml`.
- **Inputs:** deal dataroom (folder of deal documents); fund loan tape / portfolio register.

### Processes

- Independence-first blind opening pass (isolated `Task()`, zero cross-visibility).
- Mode A (fan-out -> axiom-synthesis fusion -> memo).
- Mode B (main-conversation moderated relay: blind openings, bounded rebuttal rounds, HITL).
- Deterministic verdict computation (`resolve.py` polarity over discipline roll-ups).
- Falsification / cross-examination gate (different-discipline refuter; ACH; nullification).
- Legal delegation + compliance companion (usury/licensing, AML/KYC/OFAC, foreclosure, Phase I).
- Autopilot-active detection + safe fallback.
- Resume from transcript-on-disk (survives `/clear` + Eternity).

### Methods

- Pre-mortem / inversion (Klein); Mediating Assessments Protocol (Kahneman, MAP);
  Analysis of Competing Hypotheses (Heuer/CIA); reference-class forecasting (Flyvbjerg);
  pre-committed kill criteria; blind independent first pass; asymmetric-veto resolution;
  assigned rotating devil's advocate + consensus-triggered 10th-man; justification-forcing
  (update-or-hold); model-class/persona diversity; Axis S (severity/materiality) extension.

### Standards / Regulations

- **T1 authoritative:** OCC Comptroller's Handbook (CRE Lending); FDIC RMS Manual §3.2;
  FinCEN CRE Financing Fraud advisory; ASTM E1527-21 (Phase I ESA, mandatory 2024-02-13);
  CERCLA §101(20) secured-lender exemption / BFPP; SEC 2026 exam priorities (private-credit
  fiduciary + conflicts); Utah Commercial Financing Registration (2023).
- **T2 expert best-practice:** Three Lines of Defense / independence principle; ALTA/NSPS
  survey + title commitment; the 13-section IC-memo canon; 5 C's credit taxonomy.

### Metrics

- CQ coverage % (>=95% target); risk-category coverage (zero uncovered); DSCR / debt yield;
  Axis S severity ladder; reduced-independence flag; agent-performance (SPD, QAP, TER, UAPS).

### Risks

- Domain: fund-level concentration; financial-statement / valuation fraud; refinance / exit /
  maturity; insurance-cost / physical-climate; title/lien; environmental (RECs).
- Epistemic / operational: sycophancy; consensus-as-correctness; correlated same-model error;
  narrated (non-deterministic) verdict; `autopilot-active` silent auto-answer of the pause.

### Key terms

- **Deal-breaker** (derived rule): `state ∈ {ESTABLISHED, CORROBORATED} AND axis_s ≥
  material-risk AND no surviving mitigant`.
- **Mitigant** (structural/documentary control that caps, not erases, a risk).
- **Residual risk** (what remains after the mitigant; mandatory even on approved deals).
- **Conditions Precedent (CP)** (binding pre-funding gate; each tagged to the risk it retires).
- **UNRESOLVED** (first-class terminal verdict; never a fabricated PROCEED/DECLINE).
- **5 C's** (Character, Capacity, Capital, Collateral, Conditions).
- **Reduced-independence flag** (single-provider ensemble -> labeled, not blocked).

---

## Assumptions carried from spec (`Assumption`)

- Deal input is a folder/dataroom of documents; intake reads a deal directory.
- Default diversity = Opus/Sonnet class + persona/temperature; multi-provider optional.
- Mode A is the cheaper default; Mode B is opt-in.
- OKOA SEC adviser-registration status, SPE size threshold, and full state footprint are
  unknown -> best-practice defaults + `conflicts-disclosure.yaml` + per-deal jurisdiction
  check; surfaced as governance gaps, not assumed values.

See `domain-cqs.md` for the competency questions, `domain-lattice.json` for the knowledge
graph, and `evidence-ledger.json` for tiered evidence.
