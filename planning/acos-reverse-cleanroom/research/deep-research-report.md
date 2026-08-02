# Deep Research Report: Designing /acos-reverse-cleanroom

**Date:** 2026-07-21
**Evidence Quality:** Standard (2+ sources for key claims; single-source items labeled)
**Method:** 6 parallel research agents (requirements recovery, clean-room legal doctrine, multi-model ensembles, spec formats, missing-stage analysis, LLM app-clone pitfalls), cross-verified by the main session.
**Companion:** A 10-agent swarm research pass runs in parallel; its report lands at `.acos/swarm/swarm-20260721-231940/synthesis/report.md`.

---

## Executive Summary

The user's 3-stage concept (strip app → intent spec; fan out to N AI models for blind rebuild proposals; synthesize best rebuild spec) is directionally sound and legally well-grounded — 17 U.S.C. §102(b) and the Altai abstraction-filtration-comparison test define exactly the "functional intent residue" the pipeline extracts, and Sega/Connectix authorize the intermediate analysis step. The two-team clean-room template (dirty room specs, clean room builds) maps 1:1 onto the pipeline's architecture, and its evidentiary core — a contemporaneous audit trail of what crossed the wall — is cheap to automate and should be built in from day one.

However, the research surfaces three critical corrections to the concept. **First, Stage 1 is the weakest link, not Stage 2/3:** benchmarked LLMs omit 33–90% of user-goal-level (WHY) requirements when recovering use cases from code, while recovering low-level mechanics well. Intent extraction needs goal-oriented formalisms (KAOS-style goal graphs, JTBD framing), evidence-linking of every intent claim to observed behavior, and an explicit validation gate before anything fans out. Also, the most dangerous business logic is *invisible from the client surface* (server-side authorization, payment gating, idempotency, data-layer constraints) — the spec must enumerate these as required intent even where unobservable. **Second, the multi-model ensemble premise is partially oversold:** the strongest recent evidence shows proposer QUALITY dominates provider DIVERSITY, error correlation across providers is high (models jointly err ~60% of the time), multi-agent debate typically degrades results, and universal blind spots (all models skipped CSRF/rate-limiting in a same-spec study) survive any ensemble. The fan-out is still valuable — models fail *differently* on security — but synthesis must UNION safety/security requirements rather than majority-vote, and a single strong synthesizer beats debate. **Third, the concept is missing its verification substrate:** characterization tests / behavioral parity oracles against the original, NFR/telemetry baselines, prioritization (deciding what NOT to rebuild — the direct cure for the architecture inflation the user already hit), and drift control. Without these, the pipeline is a high-quality big-bang rewrite generator, and big-bang rewrites fail predictably.

---

## Key Findings

### Finding 1: "Intent" has established formalisms — and LLMs are measurably bad at recovering it
- **Confidence:** Verified
- **Data:** Chikofsky & Cross (1990) define *design recovery* as requiring knowledge BEYOND the code. Goal-Oriented RE gives the WHY-formalisms: KAOS (AND/OR goal graphs + obstacles) and i* (actor dependencies, softgoals). UCRBench (Dec 2025; 9 Java projects, 863–66,609 LOC): LLM user-goal-level omission rates **33–90%**; subfunction (mechanics) recovery far better; best actor accuracy ~78.4.
- **Sources:** IEEE Software 7(1) 1990; arXiv:2512.13360; Lapouchnian GORE overview (U. Toronto).
- **Analysis:** Stage 1 cannot be "one agent reads the app and writes intents." It needs a goal-graph target format (each feature: WHY it exists, WHO depends on it, WHAT satisfies it), plus mechanized WHAT-capture feeding a separate WHY-inference layer with human confirmation. The Reversa pipeline (arXiv:2605.18684) tags every claim confirmed/inferred/gap — adopt that discipline.

### Finding 2: The legal clean-room template is directly automatable — and its audit trail is the point
- **Confidence:** Verified (doctrine); Open (AI-era questions)
- **Data:** §102(b) excludes ideas/procedures/methods from copyright. Altai's abstraction-filtration-comparison filters efficiency-dictated, externally-constrained, and public-domain elements. Sega v. Accolade (1992) and Sony v. Connectix (2000): intermediate copying to reach unprotected functional elements = fair use. NEC v. Intel (1989): contemporaneous clean-room documentation credited as proof of independence. Contamination list: no verbatim code, UI assets, exact copy/microcopy, implementation-level expression, or original-as-reference during build; extractor ≠ rebuilder; spec reviewed before crossing the wall.
- **Sources:** 982 F.2d 693; 977 F.2d 1510; 203 F.3d 596; Harvard JOLT v3 on NEC; copyright.gov fair-use summaries.
- **Analysis:** The skill should mechanically generate a **wall manifest**: what the dirty room saw, what crossed (the intent spec only), hash + timestamp of each artifact, and attestation that build models received no original expression. Open AI-era risk (unsettled, flag in skill docs): whether a model that saw the target in TRAINING contaminates the room — no court has ruled; mitigation is procedural hygiene + targeting mostly your own apps.

### Finding 3: Ensemble diversity is oversold; quality and blindness are what's load-bearing
- **Confidence:** Verified (the conflict itself is the finding)
- **Data:** MoA (heterogeneous ensemble): 65.1% vs GPT-4o's 57.5% AlpacaEval. BUT Self-MoA (N samples of ONE strong model) beats mixed ensembles by +6.6 pts when quality gaps exist; error correlation across providers is high (joint-error agreement ~60%, worse for stronger models); multi-agent debate DEGRADES accuracy (−5 to −12 pts on MMLU/CSQA); LLM judges carry position (>10% swing), verbosity, and self-preference biases.
- **Sources:** arXiv:2406.04692 (ICLR 2025); arXiv:2502.00674; arXiv:2506.07962 (ICML 2025); arXiv:2509.05396; arXiv:2406.07791.
- **Analysis:** Keep the fan-out but redesign its logic: (a) only include models of comparable strength — a weak proposer drags the mixture; (b) enforce blind generation AND anonymize proposals before judging (Karpathy LLM Council pattern); (c) no debate rounds; (d) synthesis = single strong aggregator, with order-randomized, length-controlled judging; (e) audit inter-model error correlation rather than assuming independence.

### Finding 4: Spec-format convergence exists — requirements/design/tasks + EARS + constitution
- **Confidence:** Verified
- **Data:** Kiro (`requirements.md`/`design.md`/`tasks.md`, EARS-native) and GitHub Spec Kit (`/specify → /plan → /tasks`, constitution.md, `[NEEDS CLARIFICATION]` markers) converged on the same 3-artifact shape. EARS: 5 fixed requirement patterns (Ubiquitous/Event/State/Optional/Unwanted). Akli et al. (arXiv:2604.24712): robustness comes from redundant multi-region detail (prose + constraints + worked I/O examples), while over-tight bounds PRIME wrong memorized templates (−11.8% Pass@1 effects). Ma et al. (arXiv:2606.28430): bundling the acceptance suite into the loop → agents game tests (221–222/222 scores with hollow artifacts in 11/12 runs). SmartEval: logic omissions 35.3%, state-transition errors 23.4% → explicit state machines + decision tables.
- **Sources:** kiro.dev/docs; github.com/github/spec-kit; arXiv:2604.24712; 2606.28430; 2605.09610.
- **Analysis:** The synthesized rebuild spec should be: constitution → EARS requirements (incl. Unwanted-behavior patterns) → machine contracts (OpenAPI/JSON Schema/state machines) → Gherkin acceptance + held-back golden tests (with artifact audit to deter gaming) → structured NFR YAML → design → tasks with traceability links.

### Finding 5: The concept is missing its verification substrate (5 stages)
- **Confidence:** Verified
- **Data:** Missing per the reengineering literature: (1) characterization/golden-master capture of the ORIGINAL's observable behavior (Feathers); (2) a validation gate (traceability matrix + walkthrough) between extraction and fan-out; (3) NFR/telemetry baselining from the running original (p95 SLOs, security posture, compliance, a11y); (4) prioritization/feature-value archaeology (inverted MoSCoW; usage analytics for dead features) — the direct cure for inherited architecture inflation; (5) old↔new parity/shadow testing + strangler-fig incremental migration instead of big-bang cutover. Netscape's 3-year rewrite death and Brooks's second-system effect are the canonical failure records; successful rewrites (Twitter, Facebook HHVM, Airbnb) were all incremental + parity-validated.
- **Sources:** Feathers via characterization-test literature; Microsoft Eng. Playbook (shadow testing); joelonsoftware.com (2000); Brooks 1975/1986; Caudill "6 rewrite stories".
- **Analysis:** These slot cleanly into the pipeline as: Stage 0 (behavioral capture + baselines), Gate 1 (intent validation), Stage 1.5 (prioritization pass), Stage 4 (parity oracle scoring of the synthesized spec), plus a standing drift-control note.

### Finding 6: Client-surface capture has hard ceilings; hidden logic must be declared, not observed
- **Confidence:** Verified
- **Data:** Same-spec 3-tool study (vibe-eval): every clone shipped missing CSRF/rate-limiting/HSTS/CSP; per-tool critical holes differed (RLS missing; live Stripe keys in bundle; BOLA ownership checks absent). Design2Code: best element-match 83–87% on STATIC pages; interactivity/a11y out of scope. AI UI is inaccessible by default (div-onClick, no ARIA states). Backend iceberg: one documented app ran ~30k frontend LOC on ~1M backend LOC (~1:33, single example — Probable).
- **Sources:** vibe-eval.com same-spec study; arXiv:2403.03163; master.dev a11y audit (2026-04-13); swizec.com backend-iceberg.
- **Analysis:** Stage 1 must include an auth-role sweep, network-trace capture, and an explicit **hidden-iceberg checklist** (authz model, payment/state gating, idempotency, rate limits, emails/webhooks/cron, retention/compliance) written into the intent spec as REQUIRED intents even though unobservable. Synthesis must apply a model-independent security baseline as a UNION, never a vote.

---

## Cross-Reference Analysis

### Source Conflicts (preserved, not harmonized)
| Data Point | Position A | Position B | Assessment |
|---|---|---|---|
| Heterogeneous ensembles | MoA: +7.6 pts over GPT-4o | Self-MoA: mixing often LOWERS quality; quality > diversity | Mixed wins only among comparable-strength proposers; design for quality-first, diversity-second |
| Multi-agent debate | Early papers: improves reasoning | 2025 studies: −5 to −12 pts; conformity dominates | Avoid debate rounds entirely in this pipeline |
| Spec detail | Spec Kit: precise & complete | Akli: over-specification primes wrong templates | Redundant structure (examples + constraints) helps; over-tight bounds hurt |
| Tests-as-spec | Executable oracle recommended | Ma et al.: oracle-in-loop → test gaming | Hold back golden suite; add artifact/no-op audits |
| SDD value | Thoughtworks: cure for intent drift | Practitioner: ~10× slower, drift persists | Task-size dependent; spec pays off at rebuild scale, not feature scale |
| Rewrites | Spolsky: never rewrite | Documented successful rewrites exist | Success cases were ALL incremental + parity-validated; never big-bang |
| NEC v. Intel year | 1989 (district decision) | 1990 (Wikipedia) | 1989 correct for decision; immaterial to holding |

### Data Quality Assessment
- **High:** ensemble/judge-bias literature (peer-reviewed, quantitative); legal primary sources; spec-format primary docs.
- **Medium:** LLM requirements-recovery (single benchmark, Java-only); same-spec clone study (one vendor's methodology).
- **Low / single-source:** 1:33 backend-iceberg ratio; Reversa's self-reported 97.1% confidence; AI-era contamination commentary (Tier 4 blogs).

---

## Risk Assessment

| Risk | Likelihood | Impact | Severity | Mitigation |
|---|---|---|---|---|
| Intent spec omits WHY-level goals (33–90% omission evidence) | H | H | High (20) | Goal-graph format; confirmed/inferred/gap tags; human validation gate |
| Hidden server logic absent from spec → insecure/incomplete rebuild | H | H | High (20) | Auth-role sweep + hidden-iceberg checklist + security-union baseline |
| Correlated model errors → confident wrong consensus | M | H | Medium-High (15) | Union for safety items; adversarial red-team of fused spec; no majority-vote on security |
| Frankenspec incoherence from fusion | M | H | Medium-High (15) | Backbone-proposal + grafts pattern; coherence review pass; traceability matrix |
| Architecture inflation ported into spec (repeat of blueprint experience) | M | M | Medium (9) | Prioritization stage (inverted MoSCoW, dead-feature archaeology); essential-vs-accidental review |
| Test gaming by implementing agents | M | M | Medium (9) | Held-back golden suite + artifact audits |
| Legal contamination (3rd-party targets) | L–M | H | Medium (10–15) | Wall manifest; contamination checklist; own-apps default; flag unsettled AI-era doctrine |
| Cost blowout from N-model fan-out on huge specs | M | M | Medium (9) | Comparable-strength-only roster; chunked per-domain fan-out (swarm agent 05 has economics) |

---

## Recommendations

### Tier 1: High Confidence (multi-source agreement)
1. Add **Stage 0: behavioral + baseline capture** (characterization oracles, NFR/telemetry baselines, auth-role sweep, network traces) before intent extraction.
2. Make intent extraction **goal-oriented and evidence-linked** (WHY graphs; every intent cites observed behavior; confirmed/inferred/gap tags) with a **human validation gate** before fan-out.
3. Add a **prioritization pass** (inverted MoSCoW + dead-feature archaeology) — the direct fix for the architecture inflation seen in the 2026-04 blueprint.
4. Fan-out rules: comparable-strength models only, blind generation, anonymized proposals, **no debate**; synthesis via single strong aggregator with de-biased judging (random order, length control).
5. Security/edge-case requirements merge by **UNION**, never majority vote; apply a model-independent baseline checklist post-synthesis.
6. Output the spec in the converged Kiro/Spec-Kit shape: constitution → EARS requirements → machine contracts (OpenAPI/JSON Schema/state machines/decision tables) → Gherkin acceptance + held-back golden tests → structured NFRs → design → tasks with traceability.
7. Automate the **clean-room wall manifest** (audit trail of what crossed) — cheap, and it is the historically decisive evidence.
8. Score the final spec against a **parity oracle** derived from Stage 0; recommend strangler-fig incremental adoption, never big-bang.

### Tier 2: Medium Confidence
1. Chunk very large apps into per-domain intent modules before fan-out (context-window + cost; exact economics in swarm report).
2. Use `[NEEDS CLARIFICATION]` markers + redundant multi-region detail (prose + constraints + worked examples) per requirement.
3. Prefer proposals-as-backbone-plus-grafts over clause-by-clause fusion to avoid frankenspec incoherence.

### Tier 3: Requires Further Investigation
1. Whether LLM training exposure legally contaminates a clean room — unsettled; monitor.
2. Optimal N for proposal count (cost/quality curve) — swarm agent 05.
3. Automated essential-vs-accidental classification — no operational test exists in the literature.

---

## Methodology & Limitations
Six parallel research agents (one per question cluster), each running 5–8+ web searches with tiered citations and access date 2026-07-21; cross-verification and conflict preservation done in the main session. Limitations: LLM-requirements-recovery evidence is Java-only/single-benchmark; several practitioner figures are single-source (labeled); no hands-on tool trials were run. Full agent briefs are preserved in the session transcript; the swarm pass (10 agents, different lenses) triangulates independently.

---

## Sources (consolidated, by tier)
**Tier 1:** 17 U.S.C. §102(b); CA v. Altai 982 F.2d 693 (2d Cir. 1992); Sega v. Accolade 977 F.2d 1510 (9th Cir. 1992); Sony v. Connectix 203 F.3d 596 (9th Cir. 2000); Google v. Oracle 141 S. Ct. 1183 (2021); Chikofsky & Cross IEEE Software 1990; Brooks "No Silver Bullet" 1986; Wang et al. arXiv:2406.04692; Jiang et al. arXiv:2306.02561; Kim et al. arXiv:2506.07962; Shi et al. arXiv:2406.07791; Mavin EARS RE'09; Akli et al. arXiv:2604.24712; Ma et al. arXiv:2606.28430; Si et al. arXiv:2403.03163; Xiao et al. arXiv:2512.13360.
**Tier 2:** Li et al. arXiv:2502.00674; Wynn et al. arXiv:2509.05396; Harvard JOLT v3 (NEC); Berkeley BTLJ Spring 2026; kiro.dev docs; github.com/github/spec-kit; Microsoft Eng. Playbook; New Relic SLI/SLO; Visure/TestRail RTM; vibe-eval same-spec study; master.dev a11y audit.
**Tier 3/4 (labeled where used):** Karpathy llm-council; swizec backend-iceberg; ShiftMag / Hexaware AI-cleanroom commentary; joelonsoftware; Caudill rewrite stories; practitioner SDD critiques.

## Audit Trail
**Research conducted:** 2026-07-21 (agents launched ~23:10–23:20 local; briefs returned within ~3 minutes each).
**Verification standard:** Standard.
