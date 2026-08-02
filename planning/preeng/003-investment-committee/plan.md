# Implementation Plan — ACOS Investment Committee (003-investment-committee)

**Command:** `/preeng.plan` output.
**Preconditions checked:** `spec.md` exists; `research.md` exists;
`research_qa_report.json.qa_status == "APPROVED"` (not REJECTED) -> proceed.
**Grounding:** `spec.md`, `research.md`, `domain-lattice.json` (78 nodes / 119 edges /
100% CQ coverage), `.acos/swarm/swarm-20260707-141351/synthesis/report.md`.
**Architecture constraints source:** `command_inputs.plan.architecture_constraints`.

---

## 0. Plan thesis (the load-bearing research decisions this plan is built around)

This is a **thin-orchestrator** build. Nine tenths of the epistemics already exist in ACOS;
the IC skill supplies the *domain* (expert seats, objection semantics, IC verdict
vocabulary) and the engines supply the *epistemics* (grading, falsification, conflict
preservation, refusal-over-fabrication). The plan is organized around six load-bearing
research decisions, each of which becomes a non-negotiable design invariant:

1. **The main conversation IS the Mode B moderator.** Subagents physically cannot call
   `AskUserQuestion`/`ExitPlanMode` (a hard Claude Code platform constraint, agent 04).
   Therefore the top-level `SKILL.md` running in the main conversation owns the
   human-pausing loop; no nested/spawned agent may own it. Every Mode B design choice
   flows from this. [lattice: `pattern-main-convo-moderator`, `proc-mode-b`]
2. **Reuse `acos-axiom-synthesis` (Mode A) and `legal-analyst` (legal seat).** Mode A
   synthesis = the built, fixture-tested (54 assertions, Phases 0-7) refutation-and-grading
   engine. The legal seat delegates to `legal-analyst` via `/acos-legal-analysis --mode
   lending`. Zero engine forks. [lattice: `pattern-reuse-over-rebuild`,
   `engine-axiom-synthesis`, `engine-legal-analyst`]
3. **Independence-first blind opening pass** is the single highest-leverage anti-groupthink
   lever, mechanically enforced in BOTH modes: every seat's opening verdict comes from an
   isolated `Task()` reading the deal alone, in parallel, zero cross-visibility; cross-talk
   only begins Round 2+. [lattice: `proc-independence-first`, `method-blind-first-pass`]
4. **The verdict is computed deterministically, never narrated.** One `resolve.py`
   `resolve_conflict()` over per-discipline roll-ups with **asymmetric-veto polarity on
   deal-breaker-flagged claims**; quorum/precedence-ladder otherwise; terminates in
   `UNRESOLVED`. No synthesizer LLM ever writes the verdict word. [lattice:
   `proc-deterministic-verdict`, `method-asymmetric-veto`, `anti-narrated-verdict`]
5. **Consensus is not correctness.** Never terminate a round because "all agents agree";
   hide numeric confidence between agents mid-debate; a lopsided approve-leaning
   distribution triggers a mandatory 10th-man pass; dissent is preserved in the memo.
   [lattice: `anti-consensus-as-correctness`, `method-devils-advocate`]
6. **Per-seat model-class diversity + reduced-independence honesty.** Assign Opus/Sonnet +
   persona/temperature per seat via the Model Profile system; when all seats share one
   provider, emit a **reduced-independence flag** (label, never block). [lattice:
   `method-model-diversity`, `metric-independence-flag`]

Everything below is a scaffold for delivering these six invariants as demo-able vertical
slices under ACOS's own orchestration (skills + agents + hooks), executed by
`/acos-execute-slice`.

---

## 1. Development philosophy — vertical slices + named demos (§0.8)

Each slice produces an **observable artifact** (a memo, a transcript, a verdict file), not
an internal refactor. Early slices deliver a walking skeleton that touches the whole reuse
spine; later slices harden and scale. The three named demo checkpoints (mirrored from
`spec.md` Rollout Plan) are the acceptance gates for the slice waves:

- **Demo 1 — Walking skeleton (3-seat Mode A -> memo).** A minimal Mode A with 3 seats
  (Credit, Valuation, Legal) fans out blind, fuses through `acos-axiom-synthesis`, and
  renders a short `recommendation.md` with a deterministic verdict. Proves the reuse spine
  end-to-end on the smallest surface. **Slices:** DIAG-01, A1, A2 (3-seat subset), B1, B2,
  C1, C2, C3, C4.
- **Demo 2 — Full roster + severity + deterministic verdict.** Full 7-core roster +
  Chair/Gap-Hunter, the **Axis S** severity extension wired through the fact-builder, the
  Risk->Mitigant->Residual triplet + CP tagging, and the deterministic asymmetric-veto
  verdict rendered into the 13-section memo canon. Proves zero-uncovered-risk coverage and
  the deal-breaker rule. **Slices:** A2 (full), A3, C1 (Axis S complete), C3, C4 (13-section).
- **Demo 3 — Mode B live deliberation.** The main-conversation moderator loop: blind
  openings, bounded rebuttal rounds, transcript-on-disk, scoreboard, chair command
  vocabulary, human injection as a first-class turn, deterministic tally, autopilot
  detection, resume. Proves HITL + resumability. **Slices:** D1, D2, D3.
- **Post-demo hardening.** legal-analyst reuse + compliance companion +
  conflicts-disclosure (E1); the full guardrail suite — independence enforcement, kill
  criteria, anti-sycophancy schema, reduced-independence flag, autopilot detection (F1);
  instrumentation; a real-deal pilot to tune round/turn/checkpoint constants.

Sequencing rule: **no slice merges until its DoD artifact is demo-able in isolation.** The
walking skeleton (through C4 at 3 seats) must render a real memo from a real ledger before
any Mode B work starts.

---

## 2. Orchestration & edge constraints (§0.9) — framed against ACOS

**Target orchestration stack = ACOS's own primitives.** There is no external workflow
engine. The IC skill is an ACOS `SKILL.md` router that spawns seat expert agents via
`Task()` and runs deterministic Python (axiom-synthesis scripts + a small IC tally/adapter)
under the ACOS hook chain. The eventual executor of every slice in this plan is
`/acos-execute-slice`, which turns each `tasks/*.md` file into a real `planning/slices/`
`slice.yaml` executed by architect/developer/reviewer agents under hook enforcement.

**PM/Dev/QA -> orchestration node mapping (§0.1).** PM≈architect (plans the slice, writes
the LCE brief), Dev≈developer (implements within `files_allowed` scope), QA≈qa-reviewer /
security-reviewer / integration-reviewer behind the Independence Wall. Author every slice
DoD so it maps cleanly onto `slice.yaml`: Objective->`objective`/`description`, allowed
files->`files_allowed`, DoD + evidence gates->`acceptance_criteria`, QA verification
->`verification_method`.

**Durable execution / resume (NFR-4).** The moderated relay is turn-based and interruptible.
Durability is achieved by **transcript-as-source-of-truth**: every turn hits disk
immediately (`rounds/round-NN/**` JSON + append-only `transcript.md`) before the next
`Task()` is dispatched. `manifest.yaml` carries `status: open|paused_for_human|closed` and
the current round pointer. Resume re-reads `manifest.yaml` + `round-status.yaml` and
re-enters at the last-closed round — surviving `/clear`, crash, and Eternity Protocol
handoff. Conversation memory is never authoritative. [lattice: `pattern-transcript-on-disk`]

**Human-in-the-loop pause nodes.** Mode B pauses at round boundaries via a zero-typing
`AskUserQuestion` menu owned by the main conversation. The human-input idiom is
`fin-stmt-accountant`'s "bounce a structured request up the call stack, persist to disk,
re-dispatch": the moderator writes `human-injection.json` as a first-class `HUMAN_OVERSEER`
turn, then re-dispatches the next round with every implicated seat required to address it
(update-with-a-named-new-fact or hold-with-a-reason, never capitulate). **Hazard node:**
when `.acos/state/autopilot-active` exists the pause `AskUserQuestion` is *silently
auto-answered*; the skill must detect this state file at Mode B entry and either refuse
deep-pause or fall back to a documented autonomous batch mode, with the "(Recommended)"
option engineered to be safe under auto-pick ("continue, no injection"). [lattice:
`proc-autopilot-detection`, `risk-autopilot-auto-answer`]

**Observability (NFR-5).** Expert identity + round is logged to
`.acos/metrics/agent-completions.log` via the existing SubagentStop hook (agent_type /
agent_id already captured). Per-turn JSON + the append-only transcript + the hash-chained
axiom-synthesis ledger form the complete audit trail. A per-run `conflicts-disclosure.yaml`
evidences that the committee's own process was sound (SEC 2026 fiduciary focus).

**Hook compliance (NFR-2).** All seat spawns are `Task()` under the $200/mo Max
subscription — never `ANTHROPIC_API_KEY`. The skill runs correctly under the Oracle
PreToolUse temperature scoring, `check-scope`, the Independence Wall, and the
autopilot/Eternity continuation system.

---

## 3. Architecture overview (component-level)

```
/acos-investment-committee  (SKILL.md router — main conversation; the ONLY moderator)
  --deal <dir> --mode A|B [--autopilot] [--seats lean|full]
        |
        |-- intake            : read deal dir -> Deal + SessionManifest; scaffold session dir
        |-- autopilot gate     : detect .acos/state/autopilot-active -> refuse deep-pause / batch
        |
   ┌────┴─ Mode A (default, cheaper) ──────────────────────────────────────────┐
   │  blind fan-out: 7 core seat agents via Task() (isolated, zero cross-view)   │
   │        -> per-seat report + >=1 falsifiable objection                        │
   │  IC fact-builder (adapter): objection -> axiom-synthesis `fact` + Axis S     │
   │  axiom-synthesis orchestrate.py: decircularize->grade->fuse->falsify->resolve │
   │  deterministic verdict: resolve.py verdict-as-fact over discipline roll-ups   │
   │        (asymmetric-veto on deal-breakers) -> verdict.md                       │
   │  memo renderer: 13-section IC canon from ledger -> recommendation.md          │
   └──────────────────────────────────────────────────────────────────────────┘
   ┌────── Mode B (opt-in) ─────────────────────────────────────────────────────┐
   │  blind openings (same independence-first pass) -> transcript.md              │
   │  moderator loop (main convo): bounded rounds; per-turn stance schema on disk  │
   │  deterministic tally (consensus_check.py style): responded? majority? veto?   │
   │  chair vocab + round-boundary menu; HUMAN_OVERSEER injection as first turn     │
   │  resume from manifest.yaml + round-status.yaml; then SAME synthesis+verdict    │
   └──────────────────────────────────────────────────────────────────────────┘
   ┌────── Legal seat (both modes) ─────────────────────────────────────────────┐
   │  delegate -> legal-analyst /acos-legal-analysis --mode lending               │
   │        (findings-manifest.yaml, red-flags.yaml) -> re-project into voting     │
   │  compliance companion: usury/licensing, AML/KYC/OFAC, foreclosure, Phase I    │
   │  conflicts-disclosure.yaml (per run)                                          │
   └──────────────────────────────────────────────────────────────────────────┘
```

**Component list** (detailed in `tech_prd.md`): SKILL.md router; 7 core seat expert agents
+ Chair/Gap-Hunter + Deal Advocate (non-voting); deal-triggered optional seats; IC
fact-builder adapter (Axis S owner); axiom-synthesis engine (unforked); deterministic
verdict computation; 13-section memo renderer; Mode B moderator loop + append-only
transcript + deterministic tally; legal-analyst reuse wrapper + compliance companion;
conflicts-disclosure emitter; autopilot-active detector; resume reader; observability
mirror to `.acos/metrics/agent-completions.log`.

---

## 4. Data model summary

Full definitions in `data-model.md`. Entities: **Deal, Seat, ExpertProfile, Objection,
Mitigant, SeverityGrade, Round, Turn, HumanInjection, Transcript, Verdict,
ConditionPrecedent, ConflictsDisclosure, ICMemo, EvidenceCitation, SessionManifest.** The
load-bearing mapping: **Objection -> axiom-synthesis `fact`** (`orchestrate.py::process_fact`
consumes `{fact_id, statement, claim_type, candidates, grading, flags, refuter, conflict,
depends_on, covers}`) **plus a domain-owned `_ic_extension_severity {axis_s_materiality,
raised_by_role, rationale}`** (the SeverityGrade / Axis S). Mitigant = a NEW fact
(`depends_on` the objection). Deal-breaker is a *derived* rule, never an engine field.

---

## 5. Build phases (slice waves) & sequencing

| Wave | Demo | Epics | Slices | Delivers |
|------|------|-------|--------|----------|
| W0 diagnostic | pre-Demo-1 | B/F | DIAG-01 | problem validated; session-dir scaffold; axiom-synthesis reachability smoke test |
| W1 skeleton | Demo 1 | A,B,C | A1, A2(3-seat), B1, B2, C1, C2, C3, C4 | 3-seat Mode A memo + deterministic verdict end-to-end |
| W2 full roster | Demo 2 | A,C | A2(full), A3, C1(Axis S), C3, C4(13-sec) | 7-core roster, severity, triplet, deal-breaker rule, 13-section memo |
| W3 Mode B | Demo 3 | D | D1, D2, D3 | moderator loop, transcript, tally, chair HITL, resume |
| W4 harden | post-demo | E,F | E1, F1 | legal reuse + compliance + conflicts; guardrail suite; autopilot detection |

Dependency spine: DIAG-01 -> B1 -> B2 -> C1 -> C2 -> C3 -> C4 (Demo 1). A1/A2 gate B2.
D1 depends on B2 + C1 (reuses the independence-first pass and fact schema). E1/F1 harden
across all modes and can proceed once Demo 2 is green.

---

## 6. Risks carried into the build (from spec §Risks)

- **Consensus != correctness** -> load accuracy onto structural guardrails (F1), not debate;
  verdict deterministic (C3); never terminate on consensus (F1).
- **Sycophancy / correlated same-model error** -> model-class + persona diversity (A2/F1);
  derived (not self-reported) confidence; reduced-independence flag when single-provider.
- **autopilot-active silently auto-answers the pause** -> detect the state file (F1/D3);
  "(Recommended)" option safe under auto-pick; smoke-test once skill exists.
- **Concentration + fraud silent PASS** -> fund-scoped Portfolio seat with loan-tape access
  (A2); explicit adversarial Fraud-Forensics mandate (A2); standing hole-checklist (F1).
- **Axis S does not exist in the engine** -> domain-owned in the IC fact-builder (C1); no
  engine change; "same underlying fact" detection is an open design surface (C2 note).
- **Greenfield UX; unvalidated constants** -> ship reasoned defaults (round cap 5-6, turn
  cap 150-250w, checkpoint every 3); instrument and pilot (post-demo).
- **OKOA governance unknowns** (SEC registration, SPE threshold, state footprint) -> marked
  `Assumption`; best-practice defaults + conflicts-disclosure; confirm before hardcoding
  legal rules (E1).

---

## 7. Metrics & governance scaffolding (§0.5)

Formulas defined here, computed later (see `tech_prd.md` §APA/PSA and `AGENT-METRICS.md`):
SPD (Story Points Delivered, qualitative); QAP = `(Delivered_Value * Quality_Score) /
(1 + Rejection_Count)`; TER = artifacts per 1K tokens; UAPS =
`0.3*Quality + 0.4*Efficiency + 0.3*CostEffectiveness`. Instrumentation points at
`.acos/metrics/agent-completions.log` (SubagentStop already logs agent_type/agent_id) plus
a feature-level `AGENT-METRICS.md`. Domain-quality analytics: risk-category coverage %,
deal-breaker count/type, mitigant-attachment rate, independence flag, stance-flip count per
seat, UNRESOLVED rate, round count vs cap.

---

## 8. Assumptions & open items (carried from spec Open Questions)

- `Assumption` — OKOA SEC adviser-registration status unknown -> best-practice fiduciary
  discipline + `conflicts-disclosure.yaml`; confirm before hardcoding Advisers Act rules.
- `Assumption` — no codified SPE/bankruptcy-remoteness threshold -> surface as governance gap.
- `Assumption` — active-state footprint beyond UT/HI/ID/PR unknown -> per-deal jurisdiction
  check for usury/licensing.
- `Assumption` — default diversity = Opus/Sonnet class + persona/temperature; multi-provider
  Hybrid-Review optional -> reduced-independence flag when single-provider.
- `Assumption` — Mode A cheaper default, Mode B opt-in; user selects mode at invocation.
- `Assumption` — deal input is a folder/dataroom (consistent with acos-dataroom /
  acos-data-extractor); intake reads a deal directory.
- Open (engine) — "same underlying fact" cross-discipline detection + Axis S ladder need
  validation against real objection data (entity-linking reuse candidate).
- Open (UX) — Mode B round cap / turn cap / checkpoint interval unvalidated; pilot to tune.
- Open (engine) — TaskStop semantics for interrupting an in-flight background expert
  (discard vs count) need live testing.
