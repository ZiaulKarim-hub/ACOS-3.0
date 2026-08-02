# Overview

**Product:** ACOS Investment Committee (IC) — feature `003-investment-committee`
**Project:** ACOS 3.0
**Command:** `/preeng.specify` output (canonical PRD)
**Grounding:** `.acos/swarm/swarm-20260707-141351/synthesis/report.md` + agents 01-10 findings.

The ACOS Investment Committee is a **thin orchestrator + domain adapter** that convenes a
panel of discipline-expert AI agents to read a private-credit / real-estate deal and find
holes from each discipline's point of view. It produces the best-possible deal
recommendation: per-discipline limitations, named mitigants with explicit residual risk,
and separately-flagged deal-breakers — terminating in a **deterministically computed**
verdict (`PROCEED | PROCEED-WITH-CONDITIONS | DECLINE | UNRESOLVED`) that is never narrated
or fabricated by an LLM.

It offers two user-selectable output modes:

- **Mode A — Synthesized IC Memo (default, cheaper):** fan-out to isolated expert seats,
  then fuse via a **vendored private copy of the axiom-synthesis engine**
  (`.claude/skills/acos-investment-committee/scripts/synthesis/` — refutation-and-grading;
  preserves conflict; terminates in UNRESOLVED, never fabricated consensus). The skill is
  **standalone**: it has NO runtime dependency on the `acos-axiom-synthesis` skill. Renders
  a 13-section IC memo with the Risk -> Mitigant -> Residual-risk -> Conditions-Precedent
  pattern.
- **Mode B — Live, Interruptible, Human-Chaired Deliberation (opt-in):** a moderated
  relay run by the top-level SKILL.md (main conversation), append-only transcript on disk
  as source of truth, two-line blind openers in Round 1, Gap-Hunter-directed serial rounds
  thereafter, per-turn stance badges, a human chair with procedural (not evidentiary)
  authority, an ESC-interject channel, a one-to-one/team-deliberation toggle, and a
  deterministic tally for mechanical checks.

**Core design thesis (from research):** the best AI IC is NOT built by making agents
"argue their way to the right answer." Multi-agent debate does not reliably beat simple
voting on accuracy for a no-ground-truth judgment like approve/decline, and consensus is
not evidence of correctness. Accuracy comes from **structural guardrails** —
independence-first, model/persona diversity, mandatory falsification, evidence-only
confidence, deterministic verdict — not from more talking. Debate's value is **legibility,
adversarial hole-finding, and genuine human participation.**

**Reuse over rebuild:** Mode A synthesis = a **vendored private copy** of the
`acos-axiom-synthesis` engine (substrate + pipeline scripts copied into
`scripts/synthesis/` with a `VENDORED_FROM.md` provenance record; no runtime import of the
`acos-axiom-synthesis` skill — the IC skill is standalone); legal seat = `legal-analyst` via
`/acos-legal-analysis --mode lending`; orchestration = Wigum loop + `consensus_check.py`-
style deterministic tally + blind dispatch; human-pause idiom = `fin-stmt-accountant`
bounce-up-persist-redispatch.

---

## Diagnostics

**Purpose (§0.3 Diagnostic Protocol — problem before solution).** Before locking solution
requirements, this section captures the symptoms of the current problem so requirements can
be traced to a diagnosed cause. There is a dedicated **diagnostic slice (SLICE-DIAG-01)**
in the backlog; where a diagnosis is incomplete the derived requirement is marked
`Assumption` and carries a validation story.

### Symptoms ("what is going wrong")

| # | Symptom | Affected role | Current behavior | Desired behavior |
|---|---------|---------------|------------------|------------------|
| D1 | Single-analyst review structurally misses discipline-specific holes (legal, valuation, environmental, concentration, fraud) | OKOA associate/analyst (IC chair) | One person reads the whole deal; blind spots go unchecked | A fixed panel of complementary disciplines each interrogates its own risk category; a gap-hunter chases risks nobody claimed |
| D2 | LLM/analyst reviews are sycophantic and drift toward rubber-stamping the deal framing | Deal team, decision-makers | Reviewer agrees with the packaged narrative (~58% sycophancy baseline; 63.7% agreement with an asserted incorrect belief) | Independence-first blind opening pass; mandatory falsifiable objection per seat; evidence-only (derived, not self-reported) confidence |
| D3 | No structured way to separate deal-breakers from mitigable risks, each with a mitigant + residual-risk statement | IC chair, decision-makers | Findings are a bare list; "mitigated" with no residual; deal-breakers buried among minor items | Every non-fatal finding carries a named mitigant + explicit residual risk + CP cross-ref; deal-breakers derived by a deterministic rule and surfaced first |
| D4 | No way to run an adversarial, human-participated deliberation like a real IC | IC chair | Reviews are static documents; no live challenge / interjection | Mode B moderated relay with chair command vocabulary, stance-tagged turns, human injection as a first-class turn |
| D5 | Two risks are nobody's job by default: fund-level concentration and financial-statement fraud | Portfolio manager, decision-makers | Each reviewer reads only the deal folder -> concentration gets a silent PASS; T-12 veracity is unowned (Credit trusts it, Valuation trusts Credit's NOI, Accounting checks format, Legal never opens the spreadsheet) | A fund-scoped Portfolio & Concentration seat (#7) with loan-tape access; an explicit adversarial Sponsor & Fraud-Forensics mandate (#6, "assume fabricated until externally corroborated"); Accounting (#3) owns the single normalized-NOI claim that Credit & Valuation (#1) and Finance (#2) consume — disagreement over NOI is a mandatory escalation (ROCO fraud tripwire) |
| D6 | Verdicts are narrated by an LLM and can be fabricated (a confident PROCEED / DECLINE with no auditable basis) | Decision-makers | The recommendation is prose an LLM wrote; consensus is treated as correctness | Verdict computed deterministically from the ledger via `resolve.py` polarity (asymmetric-veto on deal-breakers); UNRESOLVED is a first-class output |

### Hypotheses & unknowns

- **H1:** Independence-first (isolated opening verdict, zero cross-visibility) is the single
  highest-leverage anti-groupthink lever. *Confidence: Verified (agents 03/05/06/09).*
- **H2:** Mechanical enforcement (context isolation, required schema fields, sequencing,
  deterministic tally) changes outcomes more than persona-prompting alone. *Confidence:
  Verified caveat (agent 06); treat mechanism as load-bearing.*
- **H3:** A 9-numbered-expert roster — 8 scrutiny seats (#1-8) plus a structurally-separate
  Deal Advocate (#9, presents the steelman/bull case, no scrutiny vote) — plus a procedural
  Gap-Hunter (#10, no vote) plus deal-triggered optionals (#11-15) achieves zero uncovered
  risk category across the 16-risk coverage map, with Environmental demoted from a core seat
  to a deal-triggered optional (#15) and its legally-material sub-lens (CERCLA secured-lender
  shield, Phase I currency) folded into Legal & Structural (#4). *Confidence: Verified
  (agents 01/02) for the 8-scrutiny-seat core; the demotion plus the Accounting/Finance/
  Strategy additions, the Deal Advocate (#9), and the roster-renumbering are later design
  refinements layered on top of agents 01/02's original 7-core finding, not independently
  re-verified against their raw data.*
- **Unknown U1 (`Assumption`):** OKOA's SEC adviser-registration status is unknown ->
  defaulted to best-practice fiduciary discipline + `conflicts-disclosure.yaml`; flag before
  hardcoding Advisers Act requirements.
- **Unknown U2 (`Assumption`):** no codified OKOA SPE/bankruptcy-remoteness size threshold
  exists -> surface as a governance gap, do not assume a number.
- **Unknown U3 (`Assumption`):** full active-state lending footprint beyond UT/HI/ID/PR is
  unknown -> per-deal jurisdiction check for usury/licensing.

---

## Users & Use Cases

### Primary users

1. **OKOA associate/analyst acting as IC chair (Zee)** — invokes the skill, selects Mode A
   or B, chairs the deliberation, injects questions, forces votes, consumes the memo.
2. **OKOA deal / underwriting team preparing a credit decision** — supplies the deal
   dataroom; consumes limitations and conditions precedent.
3. **OKOA investment decision-makers who consume the IC memo** — read the BLUF verdict,
   deal-breakers, and conditions; must be able to trust the artifact on a first cold look
   (OKOA final-artifact standard: boss-criticism-proof).

### Use cases

- **UC1 — Fast synthesized review (Mode A).** Chair points the skill at a deal dataroom,
  selects Mode A. Seats run blind in parallel; axiom-synthesis fuses; a 13-section memo +
  deterministic verdict are rendered. *Primary, cheapest, default.*
- **UC2 — Live adversarial deliberation (Mode B).** Chair selects Mode B; blind openings,
  then bounded rebuttal rounds with a scoreboard, chair commands, and human injection; ends
  in a synthesized verdict via the same engine. *Opt-in, higher cost.*
- **UC3 — Legal/compliance deep dive.** The legal seat delegates to `legal-analyst`
  (A1-A8) and runs a compliance companion (usury/licensing, AML/KYC/OFAC, foreclosure
  mechanics, Phase I currency) + emits `conflicts-disclosure.yaml`.
- **UC4 — Autopilot must be off (pre-flight assertion).** The skill runs a pre-flight
  assertion: if `.acos/state/autopilot-active` exists, it ABORTs immediately with a clear
  message instructing the user to disable autopilot before invoking the Investment
  Committee. There is no autonomous-fallback batch mode — the user guarantees autopilot is
  off manually; the skill only checks and refuses.
- **UC5 — Resume after interruption.** A session interrupted by `/clear`, crash, or
  Eternity handoff resumes from `manifest.yaml` + `round-status.yaml` (transcript-on-disk is
  the source of truth).

---

## Requirements

### 4.1 Functional Requirements (MoSCoW)

**MUST**

- **FR-M1 (Seat roster).** Provide a **numbered, stable 9-expert roster** — eight scrutiny
  seats, (1) Credit & Valuation (collateral+cash-flow sufficient to secure & repay;
  LTV/DSCR/comps/cap-rate; runs TWO sub-passes: collateral-value + repayment-capacity), (2)
  Finance (are we paid enough & is structure/exit sound — spread, lender IRR, capital
  structure, refi/takeout folded in), (3) Accounting (are the numbers real & normalized —
  QoE/GAAP/add-backs; OWNS the single normalized-NOI claim that #1 and #2 consume), (4)
  Legal & Structural (title/lien/SPE/guaranty plus an environmental-legal sub-lens — CERCLA
  secured-lender shield, Phase I ASTM-E1527-21 currency — scoped to what affects the lender
  legally/financially), (5) Insurance & Climate (non-renewal / premium-spike that breaks
  DSCR), (6) Sponsor & Fraud-Forensics (track record, litigation, cross-doc fabrication —
  "assume fabricated until externally corroborated"), (7) Portfolio & Concentration
  (fund-scoped, loan-tape access), (8) Strategy (thesis fit, opportunity cost, off-mandate
  distraction — held to the SAME falsifiable-objection discipline as every other seat; must
  produce a falsifiable "fails strategically because ___" objection or abstain; NOT an
  advocate) — plus a ninth, structurally-separate expert seat, **(9) Deal Advocate**
  (presents the deal's steelman/bull case; during deliberation, answers objections raised by
  seats #1-8 with the strongest GOOD-FAITH mitigant the evidence supports; does NOT hunt
  holes and casts NO scrutiny vote — independence principle; its mitigants are CLAIMS that
  pass through the SAME falsification gate as objections, FR-M24: survive -> downgrade the
  targeted objection's severity, refuted -> discarded; must argue in good faith from
  evidence, never fabricate) — plus a **(10) Gap-Hunter / Chair-agent** meta-seat
  (procedural, NO vote; each round selects who has something material to add; hunts for
  risks nobody claimed; also owns the exclude/include roster-coverage log, FR-M25) — plus
  **deal-triggered optionals seated only on trigger**: (11) Construction/Completion, (12)
  Tax, (13) Market/Macro, (14) Compliance, (15) Environmental/Physical-Condition (fires only
  on a flagged REC or collateral type). Seat numbers are STABLE — the chair and transcript
  refer to seats by number. Environmental is DEMOTED from a core seat to optional #15; its
  legally-material checks live permanently in seat #4. Every one of the 16 mapped risk
  categories still has a default owner (core seat or core-seat sub-mandate) even when the
  corresponding optional seat is not triggered.
- **FR-M2 (Deal packaging ≠ scrutineer; Strategy is adversarial, not the Advocate; Deal
  Advocate #9 is structurally separate from scrutiny).** The human deal team's packaging /
  underwriting-lead function MUST remain structurally separate from every scrutiny seat and
  MUST NOT cast a scrutiny vote (three-lines-of-defense independence principle); it is not
  one of the 9 numbered committee seats. Seat #8 Strategy is NOT a cheerleading advocate for
  the deal — it is held to the same mandatory-falsifiable-objection discipline as every
  other seat (FR-M4). Seat #9 Deal Advocate (FR-M1, FR-M24) is a DISTINCT, AI-run committee
  seat — not the human deal-packaging function above and not Strategy — that presents the
  deal's good-faith bull case; it casts NO scrutiny vote and is structurally separate from
  the 8 scrutiny seats; its mitigants pass through the same falsification gate as every
  objection (FR-M24), never a free pass.
- **FR-M3 (Independence-first).** Every seat's opening verdict MUST come from an isolated
  `Task()` reading the deal materials alone, in parallel, with zero cross-visibility. Cross-
  talk begins only in Round 2+. Applies in BOTH modes. A shared upfront extraction pass
  (FR-M26) supplies common RAW FACTS to every seat before this independence-first pass runs
  — sharing facts, not judgments, does not violate independence.
- **FR-M4 (Mandatory falsifiable objection).** Each seat MUST emit at least one falsifiable
  objection of the form "the deal fails if/because ___; evidence present / absent / untested."
- **FR-M5 (Objection -> atomic claim + severity).** Each expert objection MUST map onto an
  atomic `fact` record in the skill's vendored axiom-synthesis engine
  (`scripts/synthesis/`), extended with a domain-owned **Axis S (severity/materiality)** on
  a fixed ordinal ladder (`informational < limitation < material-risk <
  deal-breaker-candidate`), scored by the raising seat, stored alongside Axis A
  (reliability) and Axis B (certainty), and NEVER blended with them.
- **FR-M6 (Mode A synthesis).** Mode A MUST fuse objections through the skill's **vendored
  private copy** of the axiom-synthesis engine (`scripts/synthesis/`: decircularize ->
  grade -> fuse -> falsify -> resolve -> ledger; no runtime dependency on the
  `acos-axiom-synthesis` skill), preserving dissent, and render a 13-section IC memo from
  the ledger (never hand-edited).
- **FR-M7 (Deterministic verdict).** The overall verdict MUST be computed by `resolve.py`
  over per-discipline roll-ups — **asymmetric-veto polarity on deal-breaker-flagged claims**
  (false-accept is catastrophic), quorum/precedence-ladder otherwise — terminating in
  `UNRESOLVED` when no rung decides. The verdict is NEVER narrated or fabricated by an LLM.
  Deal-breaker is a derived rule: `state ∈ {ESTABLISHED, CORROBORATED} AND axis_s ∈
  {material-risk, deal-breaker-candidate} AND no depends_on mitigant reaches
  {CORROBORATED, ESTABLISHED}`.
- **FR-M8 (Risk triplet).** Every non-fatal finding MUST carry a named mitigant (structural/
  documentary, not aspirational), an explicit residual-risk statement, and a Conditions-
  Precedent cross-reference. "Mitigated" with no residual is disallowed.
- **FR-M9 (Mode B moderator = main conversation).** The Mode B moderator MUST be the top-
  level SKILL.md running in the main conversation (only it can call `AskUserQuestion`). No
  nested/spawned agent may own the human-pausing loop, the ESC-interject handling, or the
  one-to-one/team-deliberation toggle.
- **FR-M10 (Transcript on disk).** Mode B MUST persist every turn to an append-only
  transcript + per-round JSON immediately; the transcript, not conversation memory, is the
  source of truth. State survives `/clear`, crash, and Eternity resume.
- **FR-M11 (Round structure & turn schema).** **Round 1** MUST be a blind parallel
  **two-line opener** per seat: line 1 = number of gaps found + why the chair should care;
  line 2 = overall recommendation — except **seat #9 Deal Advocate**, whose two-line opener
  presents the deal's steelman/bull case (line 1 = strongest case for the deal; line 2 =
  overall recommendation) rather than a gap count. **Round 2 onward**, the Gap-Hunter (#10)
  selects which seat(s) have something material to add — including calling seat #9 to answer
  a specific objection with a good-faith mitigant (FR-M24); selected seats speak
  **serially**, referencing prior turns **by seat number**, under a **150-250 word cap**,
  with a **mandatory mitigant + residual-risk statement on every non-fatal gap**. Each turn
  MUST record `{round, seat, stance ∈ SUPPORT|REBUT|ABSTAIN|CONDITIONAL|FLAG_RISK, argument,
  addresses_prior_turn_ids, would_change_mind_if}`; reversals are prefixed `⟲ UPDATED`;
  numeric confidence is hidden between agents mid-debate.
- **FR-M12 (Human injection first-class; ESC interject).** A human chair message MUST be
  recorded as a first-class `HUMAN_OVERSEER` transcript turn; every implicated seat in the
  next round MUST address it (update-with-a-named-new-fact or hold-with-a-reason), never
  capitulate. The chair MAY interject with ESC **at any time**, which aborts the in-flight
  turn; the deliberation resumes with the chair-tagged seat (else the last speaker), which
  folds in the new fact and re-comments, after which the Gap-Hunter (#10) re-selects who
  speaks next.
- **FR-M13 (Chair authority procedural, not evidentiary — including in one-to-one).** Each
  seat's system prompt MUST state that the chair's stated opinion carries no automatic
  evidentiary weight; the chair's power is procedural (call/ask/challenge/vote/table/end/
  one-to-one). This holds in team deliberation AND inside a one-to-one side-channel — agents
  update on new FACTS, never capitulate to OPINION.
- **FR-M14 (Deterministic tally; pause after every round; bounded termination).** A plain-
  Python tally (`consensus_check.py` style) MUST answer mechanical questions (everyone
  responded? majority? veto? converged?) — LLM judgment reserved only for argument quality.
  The chair menu pauses after EVERY round (no auto-continue). Mode B terminates on `/end`,
  a hard round cap (5-6), or a forced `/vote` — never on consensus; dissent is preserved
  into the transcript and the memo.
- **FR-M15 (Legal seat reuse).** The legal seat MUST delegate document diligence to
  `legal-analyst` via `/acos-legal-analysis --mode lending` and re-project `red-flags.yaml`
  into voting format — not re-derive a parallel framework.
- **FR-M16 (Compliance companion).** A companion pass MUST cover legal-analyst's four gaps:
  lender-side usury/licensing (per-deal jurisdiction check), AML/KYC/OFAC/beneficial-
  ownership, structured foreclosure-mechanics fields (foreclosure_type, timeline_days,
  deficiency_available), and Phase I ASTM E1527-21 currency/staleness gate.
- **FR-M17 (Concentration ownership).** The Portfolio & Concentration seat MUST be fund-
  scoped with read access to the fund loan tape (NOT deal-scoped), so concentration cannot
  get a silent PASS.
- **FR-M18 (Fraud ownership).** The Sponsor & Fraud-Forensics seat MUST carry an explicit
  adversarial financial-statement-veracity mandate ("assume numbers fabricated until
  externally corroborated: bank statements, tax returns, estoppels, county records").
- **FR-M19 (Conflicts disclosure).** Each run MUST emit a `conflicts-disclosure.yaml`
  governance artifact (SEC 2026 fiduciary focus) evidencing the committee's own process was
  sound.
- **FR-M20 (Autopilot pre-flight assertion, not detection-and-fallback).** The skill MUST
  assert, before any run (Mode A or B), that `.acos/state/autopilot-active` does NOT exist;
  if it exists, the skill MUST ABORT with a clear message instructing the user to disable
  autopilot manually before invoking the Investment Committee. There is no autonomous-
  fallback branch — autopilot is guaranteed off by the user, not worked around by the skill.
- **FR-M21 (Never terminate on consensus).** The skill MUST NOT terminate a round because
  "all agents agree"; numeric confidence MUST be hidden between agents mid-debate; a
  lopsided approve-leaning distribution MUST trigger a mandatory 10th-man contrarian pass.
- **FR-M22 (One-to-one toggle & sidebars).** The chair MUST be able to toggle a seat into a
  private one-to-one channel ("one to one #n") and back to team deliberation ("team
  deliberation"); while active, all other seats are paused and the raw exchange is persisted
  to `sidebars/` (private channel). On return to team deliberation, EVERY seat MUST receive a
  **sidebar summary** (new facts surfaced + that seat's position changes) while the raw
  one-to-one chat remains in the sidebar file — a transparent outcome, not a transparent
  transcript.
- **FR-M23 (Mode B termination -> deterministic pipeline).** On `/end`, hard round-cap (5-6),
  or forced `/vote`, Mode B MUST hand the full transcript to the SAME vendored synthesis
  engine used by Mode A (FR-M6), compute the deterministic verdict via the SAME
  asymmetric-veto rule (FR-M7), and render the SAME 13-section IC memo (FR-M8) — Mode B never
  ends on consensus and dissent is preserved into the memo.
- **FR-M24 (Deal Advocate — good-faith defense, falsification-gated mitigants).** Seat #9
  Deal Advocate MUST present the deal's steelman/bull case and, during deliberation, answer
  objections raised by seats #1-8 with the strongest GOOD-FAITH mitigant the evidence
  supports. It MUST NOT hunt holes and MUST NOT cast a scrutiny vote — it is structurally
  separate from the 8 scrutiny seats (independence principle, FR-M2). Its mitigants are
  CLAIMS that MUST pass through the SAME falsification gate as objections (FR-M6): a
  mitigant that survives falsification downgrades the targeted objection's Axis S severity;
  a refuted mitigant is discarded, never counted as a mitigant. Seat #9 MUST argue in good
  faith from evidence already in the deal materials, the shared deal-brief (FR-M26), or its
  own private swarm findings (FR-M27/FR-M28); fabrication is prohibited under the same
  anti-hallucination discipline as every other seat.
- **FR-M25 (Roster exclude/include command).** The chair MUST be able to set the ACTIVE
  roster for a session via `exclude #n[, #n ...]` or `include only #n[, ...]`, usable at
  session start OR mid-session. Excluded seats MUST be skipped by Gap-Hunter (#10) selection
  and MUST NOT be opened for that session. The active roster MUST be recorded in
  `manifest.yaml` as an `active_seats` list. When a seat is excluded, Gap-Hunter (#10) MUST
  log what coverage is left unowned for the session (e.g. "excluding #3 -> normalized-NOI
  veracity unowned this session") — a conscious, recorded choice, never a silent gap.
- **FR-M26 (Shared extraction layer).** Before any seat's independence-first opening pass
  (FR-M3), the skill MUST run ONE upfront extraction pass that reads the deal folder ONCE
  and produces a structured, read-only shared deal-brief + evidence-index that ALL 9 expert
  seats read. This is a single source of RAW facts and citations (not interpretations); it
  is where the raw financial data feeding seat #3 Accounting's normalized-NOI claim
  originates, preventing 9x redundant extraction and keeping every seat working from
  consistent base facts. There is NO quick/deep tiering of research depth — every Mode A and
  Mode B run includes the shared extraction pass; `--seats lean|full` (§4.2) controls roster
  SIZE, never research depth.
- **FR-M27 (Per-expert private research swarms — dispatch).** After reading the shared
  deal-brief (FR-M26), each of the 9 expert seats MUST spawn its OWN private swarm of **2-4
  `Task(general-purpose)` research bots, sized to need per deal**, to perform
  discipline-specific deep/external research (governing law, comps, submarket, sponsor
  litigation, regulatory currency, etc.) that the shared extraction pass does not cover.
- **FR-M28 (Per-expert private research swarms — blind reporting).** Swarm bots MUST report
  ONLY to their spawning seat — NO cross-seat visibility into another seat's swarm (same
  blind-independence discipline as FR-M3). Each seat MUST fold the shared-layer facts and
  its own swarm's CITED findings into its objection (or, for seat #9, its mitigant) before
  it enters the IC fact-builder and the falsification gate's evidence grading (Axis A
  reliability).

**SHOULD**

- **FR-S1 (Pre-mortem round).** Run a mandatory pre-mortem/inversion round ("assume total
  loss — what happened?") before any holistic verdict.
- **FR-S2 (MAP decomposition).** Decompose per-dimension scoring (sponsor, market,
  collateral, structure/leverage, legal/title, exit/refi, downside recovery) before the
  deal-level verdict; lock the verdict field until all dimensions are populated.
- **FR-S3 (Rotating devil's advocate).** Assign a rotating devil's-advocate seat each round
  producing a quantified downside case.
- **FR-S4 (Model/persona diversity).** Assign per-seat model-class diversity (Opus vs Sonnet
  + persona/temperature) via the Model Profile system; emit a **reduced-independence flag**
  when single-provider.
- **FR-S5 (Reference-class / base-rate check).** Require each seat to reconcile sponsor
  projections against an empirical reference class (default rate, LGD, time-to-resolution) or
  explicitly flag the base-rate as a data gap.
- **FR-S6 (Scoreboard & checkpoints).** Reprint a compact stance scoreboard at checkpoints
  (every ~3 rounds or `/board`), plus a `/recap` summary box (Converged/Open/Tabled/Lean).
- **FR-S7 (Chair command vocabulary).** Support `/call /ask /challenge /vote /premortem
  /table /board /recap /end|/synthesize`, plus **ESC** (interject, any time) and **"one to
  one #n" / "team deliberation"** (toggle); plain-English fallback always accepted.
- **FR-S8 (Kill criteria).** Support pre-committed, mechanically-applied kill criteria run
  FIRST (before narrative mitigant reasoning); override = separately-logged policy exception.
- **FR-S9 (Standing hole-checklist).** Explicitly clear a standing hole-category checklist
  (concentration, leverage exceptions, statement veracity, tenant concentration,
  refi/maturity) — "no findings" on any is suspicious unless checked.

**COULD**

- **FR-C1** Single mega-prompt "quick take" preview (labeled lower-fidelity, no true
  independence) as an optional cheap pre-screen.
- **FR-C2** `/step` turn-by-turn pacing during heated exchanges (default pause is per-round).
- **FR-C3** Multi-provider Hybrid-Review preset for genuine cross-family diversity.
- **FR-C4** Flip-auditing report ("did Legal fold under pressure or find a new fact?").

**WON'T (this version)**

- **FR-W1** Real-time streaming "talk-over" between agents (platform is turn-based; simulate
  via append-only transcript).
- **FR-W2** A single narrated LLM verdict (explicitly prohibited — verdict is deterministic).
- **FR-W3** Champion/single-partner-veto voting template (wrong for a formal RE private-
  credit lender; use majority-or-consensus with domain kill-conditions).
- **FR-W4** Hardcoded jurisdiction legal rules before OKOA governance unknowns are confirmed.

### 4.2 APIs, Data & States

**Invocation surface (Assumption — thin skill router):**
`/acos-investment-committee --deal <dir> --mode A|B [--autopilot] [--seats lean|full]`

**Deal input (`Assumption`):** a folder/dataroom of deal documents (consistent with
`acos-dataroom` / `acos-data-extractor` inputs). Intake reads a deal directory.

**On-disk state layout (Mode B; from agent 04):**

```
.acos/investment-committee/<session-id>/
  manifest.yaml         # deal context, roster, active_seats (exclude/include, FR-M25), round
                         # config, status: open|paused_for_human|closed
  deal-brief/            # shared extraction layer (FR-M26): deal-brief.json + evidence-index.json
                         # (read-only, all 9 seats)
  transcript.md         # human-readable append-only render
  rounds/round-NN/opening/{seat}.json ; human-injection.json ; round-status.yaml
  swarms/{seat}/         # per-expert private research-swarm findings (FR-M27/28; blind, seat-scoped)
  sidebars/              # one-to-one side-channel transcripts + sidebar summaries (Mode B)
  conflicts-disclosure.yaml
  ledger/               # vendored axiom-synthesis hash-chained ledger + settled-objections.md
  recommendation.md     # Mode A memo / Mode B final synthesis
  verdict.md
```

**Key data entities** (detailed in `data-model.md` at plan stage): Deal, Seat,
ExpertProfile, Objection (-> atomic claim), Mitigant, SeverityGrade (Axis S), Round, Turn,
HumanInjection, Transcript, Verdict, ConditionPrecedent, ConflictsDisclosure, ICMemo,
EvidenceCitation, SessionManifest, SidebarSummary, DealBrief, EvidenceIndex,
ActiveSeatSelection, SwarmFinding.

**Manifest status state machine:** `open -> (dispatch round) -> paused_for_human ->
(resume) -> open -> ... -> closed`. Verdict states:
`PROCEED | PROCEED-WITH-CONDITIONS | DECLINE | UNRESOLVED`.

**Engine contract (vendored axiom-synthesis `scripts/synthesis/orchestrate.py::process_fact`):**
consumes `{fact_id, statement, claim_type, candidates, grading, flags, refuter, conflict,
depends_on, covers}` plus a domain-owned `_ic_extension_severity {axis_s_materiality,
raised_by_role, rationale}`. No change to the vendored engine scripts; the vendored copy is
NOT imported from the `acos-axiom-synthesis` skill at runtime.

### 4.3 Non-Functional Requirements (NFRs)

- **NFR-1 (Subscription-only).** Never use `ANTHROPIC_API_KEY`; spawn all agents via
  `Task()` under the $200/mo Max subscription.
- **NFR-2 (Hook compliance).** Run correctly under ACOS hooks (Oracle PreToolUse,
  check-scope, Independence Wall) and the autopilot/Eternity continuation system.
- **NFR-3 (Determinism).** The verdict MUST be reproducible from the ledger by re-running the
  deterministic scripts — same ledger -> same verdict.
- **NFR-4 (Durability / resumability).** Every turn hits disk immediately; state survives
  `/clear`, crash, and Eternity handoff; resume re-enters at last-closed round.
- **NFR-5 (Observability).** Log expert identity/round to `.acos/metrics/agent-completions.log`
  via SubagentStop; per-turn JSON + transcript form the audit trail.
- **NFR-6 (Cost/latency bound).** Bound rounds (5-6 cap); blind parallel openings; rolling
  synthesis + last-K verbatim context window (constant per-call cost). Mode A is the cheaper
  default; Mode B is opt-in; per-expert private research swarms are sized 2-4 bots to need
  (FR-M27), bounding swarm cost per seat.
- **NFR-7 (Honesty).** Deliberation is presented honestly as a moderated relay (turn-based),
  not simulated real-time. UNRESOLVED and reduced-independence flags are surfaced, never
  hidden.
- **NFR-8 (Artifact quality).** Final memo must be boss-criticism-proof on a first cold look
  (OKOA final-artifact standard).

---

## Prioritization & Scope Cut

**In-scope (v1):** Mode A synthesized memo end-to-end; the numbered 9-expert core roster
(#1-8 scrutiny + #9 Deal Advocate) + Gap-Hunter (#10) + deal-triggered optionals (#11-15);
the shared extraction layer (FR-M26) + per-expert private research swarms (FR-M27/FR-M28,
2-4 bots each, ONE research mode — no quick/deep tiering); the roster `exclude`/`include
only` command (FR-M25); the skill's vendored axiom-synthesis engine (no runtime dependency
on `acos-axiom-synthesis`); Axis S severity extension; the Deal Advocate's
falsification-gated mitigants (FR-M24); deterministic verdict; Mode B moderated relay with
HITL, two-line Round-1 openers, Gap-Hunter-directed later rounds, ESC interject,
one-to-one/sidebars toggle, chair vocabulary, transcript-on-disk; legal-analyst reuse +
compliance companion + conflicts-disclosure; core guardrails (independence, kill criteria,
autopilot pre-flight assertion, anti-sycophancy schema).

**Deferred / out-of-scope (v1):** multi-provider Hybrid-Review as default (optional preset
only); flip-auditing report; `/step` turn-by-turn pacing; tuned round/turn/checkpoint
constants (ship reasoned defaults, instrument, tune later); ESG/capital-markets seats
(OKOA is a balance-sheet secured lender, not originate-to-distribute).

**Scope-cut rationale:** research shows accuracy comes from structural guardrails, not from
maximizing debate; so v1 prioritizes independence + deterministic verdict + reuse over rich
argument features. Mode A (cheap, structural) is the walking skeleton; Mode B is layered on.

**Cut candidates if over budget:** single mega-prompt quick-take (FR-C1); multi-provider
diversity (FR-C3); dedicated Market/Macro as an always-on core seat (it stays a
deal-triggered optional, #13, folded into Credit & Valuation's #1 sub-check by default —
Exit/Refi is no longer a cut candidate; it is core-owned permanently by Finance, #2).

---

## Metrics & Analytics

**Success metrics (from `command_inputs.specify.success_metrics`):**

- CQ coverage of the domain lattice >= 95%.
- Zero uncovered risk category across the seat roster (validated against the 16-risk
  coverage map).
- Every finding carries severity + mitigant + residual-risk; deal-breakers explicitly
  flagged.
- Verdict is deterministic and reproducible from the ledger (never narrated).
- Human chair can observe and inject; agents update-with-new-fact or hold-with-reason (no
  capitulation).
- Boss-criticism-proof on first cold look.

**Agent performance metrics (§0.5 — formulas defined, not computed here):**

- **SPD** — Story Points Delivered (qualitative approximation).
- **QAP** = `(Delivered_Value * Quality_Score) / (1 + Rejection_Count)`.
- **TER** — Token Efficiency Ratio: artifacts per 1K tokens.
- **UAPS** = `0.3*Quality + 0.4*Efficiency + 0.3*CostEffectiveness`.
- **Instrumentation:** recorded to `.acos/metrics/agent-completions.log` (agent_type/
  agent_id already logged by SubagentStop) and a feature-level `AGENT-METRICS.md`.

**Domain-quality analytics (IC-specific):** risk-category coverage %, deal-breaker
count/type, mitigant-attachment rate, independence flag (single- vs multi-provider),
stance-flip count per seat (flip auditing), UNRESOLVED rate, round count vs cap, mitigant
survival rate (Deal Advocate claims that survive vs are refuted by the falsification gate),
excluded-seat coverage-gap log completeness.

---

## UX & Content

- **Speaker labels** are numbered seat names — `[1-CREDIT-VALUATION]`, `[2-FINANCE]`,
  `[3-ACCOUNTING]`, `[4-LEGAL]`, `[5-INSURANCE]`, `[6-FRAUD]`, `[7-PORTFOLIO]`,
  `[8-STRATEGY]`, `[9-ADVOCATE]`, `[10-GAP-HUNTER]`, plus any seated optional
  (`[11-CONSTRUCTION]` etc.) — stable every round; seat numbers never get reassigned
  mid-session.
- **Round 1 format:** a blind parallel **two-line opener** per seat — line 1: number of
  gaps found + why the chair should care; line 2: overall recommendation; seat #9 Deal
  Advocate's line 1 is the strongest case for the deal instead of a gap count (FR-M11).
- **Stance badges** per turn: `SUPPORTS / OPPOSES / CONDITIONAL / ABSTAINS`; reversals
  prefixed `⟲ UPDATED`.
- **Turn length cap** ~150-250 words from Round 2 onward (forces distillation; detail ->
  evidence bundle on disk); turns reference prior turns **by seat number**.
- **Pacing:** default pause after EVERY round (no auto-continue); `/step` optional for
  turn-by-turn.
- **ESC interject:** the chair can interject at any time; it aborts the in-flight turn and
  resumes with the chair-tagged seat (else the last speaker), which folds in the new fact
  and re-comments, then the Gap-Hunter (#10) re-selects.
- **One-to-one toggle:** `"one to one #n"` pulls a seat into a private channel (persisted to
  `sidebars/`), pausing the rest; `"team deliberation"` returns to the floor and every seat
  receives a **sidebar summary** (new facts + that seat's position changes) — the raw
  exchange stays in the sidebar file (private channel, transparent outcome).
- **Scoreboard:** reprint a compact stance table at checkpoints (every ~3 rounds / `/board`)
  because the terminal has no sidebar-panel; `/recap` prints Converged / Still open / Tabled
  / Current lean.
- **Chair vocabulary:** `/call /ask /challenge /vote /premortem /table /board /recap
  /end|/synthesize`, plus `exclude #n[, #n ...]` / `include only #n[, ...]` (sets the
  session's active roster, FR-M25; may be issued at session start or mid-session; Gap-Hunter
  #10 logs any resulting coverage gap), ESC, and the one-to-one toggle; plain-English
  fallback always accepted; freeform text becomes a `[CHAIR — you]` turn.
- **Round-boundary menu:** a zero-typing `AskUserQuestion` menu (Continue (Recommended) /
  Call expert / Ask floor / Vote / Pre-mortem / End & synthesize) — safe by construction
  since autopilot is asserted off before the run ever starts (no autopilot-safe-default
  logic needed at the menu level).
- **Memo content (Mode A):** 13-section IC canon (agent 08) — BLUF Recommendation box ->
  Exec Summary -> Transaction/Loan Summary -> Sponsor & Guarantor -> Collateral & Valuation
  -> Market -> Financial Analysis -> Sensitivities/Downside -> Risks & Mitigants (repeating
  triplet table) -> Structure & Covenants -> Conditions Precedent -> Legal/Title/
  Environmental -> Exit/Repayment -> Recommendation (full + Key Judgment Calls).
- **Severity language:** plain-English 4-tier — Monitor / Mitigated / Material-Conditioned /
  Disqualifying — mapped to the FATAL / MATERIAL / MINOR rubric and to OCC Pass/SM/
  Substandard/Doubtful/Loss.

---

## Rollout Plan

Vertical-slice, demo-able increments (§0.8). Each slice yields an observable artifact (a
memo, a transcript, a verdict file).

- **Demo 1 — Walking skeleton (3-seat Mode A -> memo).** A minimal Mode A with 3 seats
  (#1 Credit & Valuation, #3 Accounting, #4 Legal & Structural), after a shared extraction
  pass (FR-M26) produces the deal-brief they all read, fans out blind, fuses through the
  vendored axiom-synthesis engine, and renders a short recommendation with a deterministic
  verdict. Proves the reuse spine end-to-end AND the Accounting-owns-NOI tripwire (#1 vs #3
  disagreement on NOI escalates).
- **Demo 2 — Full roster + severity + deterministic verdict.** Full numbered 9-expert core
  roster (#1-8 scrutiny + #9 Deal Advocate) + Gap-Hunter (#10), each expert running its own
  private research swarm (FR-M27/FR-M28), Axis S severity extension, Risk->Mitigant->Residual
  triplet, Deal Advocate mitigants passing through the falsification gate (FR-M24), and the
  deterministic asymmetric-veto verdict rendered into the 13-section memo. Proves
  zero-uncovered-risk coverage (16-risk map) and the deal-breaker rule.
- **Demo 3 — Mode B live deliberation.** The main-conversation moderator loop: two-line
  blind Round-1 openers, Gap-Hunter-directed bounded rebuttal rounds, transcript-on-disk,
  ESC interject, one-to-one/sidebars toggle, scoreboard, chair command vocabulary (including
  roster `exclude`/`include only`, FR-M25), human injection as a first-class turn,
  deterministic tally, autopilot pre-flight assertion. Proves HITL + resumability.
- **Post-demo hardening:** legal-analyst reuse + compliance companion + conflicts-disclosure;
  full guardrail suite (independence enforcement, kill criteria, anti-sycophancy schema,
  reduced-independence flag), instrumentation, and a real-deal pilot to tune round/turn/
  checkpoint constants.

---

## Risks & Mitigations

| Risk | Severity | Mitigant | Residual risk |
|------|----------|----------|---------------|
| Consensus is not evidence of correctness; debate can amplify confident-wrong agents | Material | Independence-first; never terminate on consensus; hide mid-debate confidence; 10th-man on lopsided distribution; verdict deterministic not debated | Debate legibility ≠ accuracy on no-ground-truth judgments; instrument a pilot |
| Sycophancy (~58%) and correlated same-model error (0.396 vs 0.679) undermine independence | Material | Model-class + persona/temperature diversity; forbid agreement-without-new-evidence; derived (not self-reported) confidence; reduced-independence flag when single-provider | Subscription-Claude limits cross-family diversity; residual correlated error labeled, not eliminated |
| `autopilot-active` silently auto-answers the human-pause `AskUserQuestion`, defeating HITL | Material | Pre-flight ASSERTION: detect the state file and ABORT with a clear message before any run starts; no autonomous-fallback branch exists to silently work around HITL | User must manually guarantee autopilot is off before invoking the skill; the assertion is a hard guard, not a workaround; smoke-test once skill exists |
| Fund concentration and financial-statement fraud get a silent PASS | Material | Fund-scoped Portfolio seat with loan-tape access; explicit adversarial Fraud-Forensics mandate; standing hole-checklist | Concentration needs an accurate loan tape; fraud detection bounded by externally-corroboratable evidence |
| Cost/latency of 9 expert seats, each optionally running a 2-4-bot private research swarm, x N rounds x two modes | Monitor | Mode A cheaper default; Mode B opt-in; blind parallel openings; bounded rounds; rolling-synthesis context window; swarm bot count sized to need (FR-M27) | High-touch Mode B + full swarms remains expensive; budget per session |
| Greenfield UX (no validated precedent for terminal human-chaired multi-agent financial debate) | Material-Conditioned | Ship reasoned defaults; honest moderated-relay framing; pilot-and-instrument | Round/turn/checkpoint constants unvalidated until real sessions |
| Axis S severity does not exist in the vendored engine; "same underlying fact" detection undefined | Material | Axis S is domain-owned in the IC fact-builder, layered on the skill's OWN vendored copy of the engine (no engine-script change); route same-fact conflicts through `resolve_conflict()` | Entity-linking for cross-discipline same-fact detection is a new design surface; the vendored copy must be kept in sync with upstream fixes via `VENDORED_FROM.md` provenance, manually |
| Vendored axiom-synthesis copy can drift from the canonical `acos-axiom-synthesis` skill (bug fixes not backported) | Monitor | `VENDORED_FROM.md` records source path + git commit at vend time; standalone-by-design tradeoff (independence of the two skills over automatic sync) | No automatic sync; a human must periodically diff and re-vend |
| OKOA governance unknowns (SEC registration, SPE threshold, state footprint) | Material-Conditioned | Best-practice defaults + conflicts-disclosure; per-deal jurisdiction check; surface gaps not assumptions | `Assumption` markers must be confirmed by user before hardcoding legal rules |
| Deal Advocate (#9) becomes a smuggled-in sycophancy vector, reintroducing the rubber-stamping bias the roster was built to remove | Material | Structural separation from the 8 scrutiny seats (no vote); mitigants graded as CLAIMS through the SAME falsification gate as objections — refuted mitigants are discarded, not counted; good-faith-from-evidence prompt constraint, never fabricate (FR-M24) | Depends on the falsification gate actually catching a bad-faith mitigant; monitor via mitigant-survival-rate metric |
| Shared extraction layer (FR-M26) becomes a single point of factual error — one bad extraction now feeds all 9 seats instead of just one | Material | Extraction produces RAW facts + citations only, never interpretations or normalized figures; each seat still independently derives its own judgment (and, for Accounting, the normalized-NOI claim) from the shared raw facts — the fraud tripwire (D5) is unaffected because the CLAIM stays seat-owned even though the underlying raw numbers are shared | Entity-linking / extraction-quality assurance for the shared pass is a new failure surface; instrument extraction-error rate against a pilot |
| Chair excludes a seat via `exclude`/`include only` (FR-M25), silently losing that seat's risk coverage for the session | Material-Conditioned | Gap-Hunter (#10) MUST log exactly what coverage is left unowned whenever a seat is excluded — a recorded, conscious choice, never a silent gap | Requires the chair to read the log; still a deliberate scope-in/scope-out tradeoff the chair owns |

---

## Dependencies & Stakeholders

**Engine / asset dependencies:**

- A **vendored private copy** of the `acos-axiom-synthesis` engine (substrate +
  decircularize/grade_fuse/falsify/oscillation_guard/resolve/lifecycle/coverage/mirror/
  orchestrate, plus tests) at `scripts/synthesis/`, with `VENDORED_FROM.md` recording source
  path + git commit — the epistemics engine. **No runtime import of the
  `acos-axiom-synthesis` skill** (the IC skill is standalone).
- `legal-analyst` agent + `/acos-legal-analysis --mode lending` (legal seat;
  `findings-manifest.yaml`, `red-flags.yaml`).
- Model Profile system (`resolve-agent-model.sh`) for per-seat model-class diversity.
- `Task()` + SubagentStart/Stop hooks; deterministic consensus tally (dr2
  `consensus_check.py`).
- `fin-stmt-accountant` "bounce request up + persist + re-dispatch" idiom for human input.
- autopilot-active pre-flight assertion (abort, no fallback); Eternity Protocol resume
  (transcript-on-disk survives `/clear`).

**Stakeholders:** Zee (IC chair / builder / primary user); OKOA deal & underwriting team
(deal input, condition owners); OKOA decision-makers (memo consumers). PM≈architect,
Dev≈developer, QA≈qa-reviewer/security-reviewer under ACOS hook enforcement.

---

## Open Questions

1. **`Assumption`** — OKOA's SEC adviser-registration status is unknown -> defaulted to
   best-practice fiduciary discipline + `conflicts-disclosure.yaml`; confirm before
   hardcoding Advisers Act requirements.
2. **`Assumption`** — no codified OKOA SPE/bankruptcy-remoteness size threshold -> surface as
   a governance gap rather than assume a number.
3. **`Assumption`** — full active-state lending footprint beyond UT/HI/ID/PR unknown ->
   per-deal jurisdiction check for usury/licensing.
4. **`Assumption`** — default model diversity = Opus/Sonnet class + persona/temperature
   (subscription-only); multi-provider Hybrid-Review optional -> emit reduced-independence
   flag when single-provider.
5. **`Assumption`** — Mode A is the cheaper default; Mode B is opt-in -> user selects mode at
   invocation.
6. **`Assumption`** — deal input is a folder/dataroom of deal documents -> intake reads a
   deal directory.
7. **Resolved** — default seat roster size and composition are finalized: numbered
   9-expert core (#1-8 scrutiny + #9 Deal Advocate) + Gap-Hunter (#10, no vote) +
   deal-triggered optionals (#11-15), seated only on trigger; no longer an open
   lean-7-vs-full-9-12 question.
8. **Open (engine)** — define "same underlying fact" cross-discipline conflict detection and
   the Axis S ladder against real objection data (entity-linking / knowledge-graph reuse
   candidate).
9. **Open (UX)** — tune Mode B round cap (5-6), turn cap (150-250w), checkpoint interval
   (every 3) against a real OKOA deal pilot; no empirical baseline exists.
10. **Open (engine)** — TaskStop semantics for interrupting an in-flight background expert
    (discard vs count) need live testing.
11. **Open (engine)** — calibrate per-expert private-swarm bot count (2-4, "sized to need")
    against real deal complexity; no empirical baseline exists yet (mirrors Q9's
    round/turn/checkpoint tuning gap).

---

## Appendix

**A. Seat -> risk coverage (numbered 9-expert core [8 scrutiny + Deal Advocate] +
Gap-Hunter + optionals, superseding the original 7-core agent-02 draft):**

1. **Credit & Valuation** — #1 credit/borrower, #2 collateral/valuation, #3 market/macro
   (sub-check), #7 construction/completion (baseline), #8 cash-flow/DSCR; TWO sub-passes
   (collateral-value, repayment-capacity); merges the former separate Credit and Valuation
   seats.
2. **Finance** — #9 interest-rate/refi/exit (core-owned, no longer a Credit fold-in);
   spread/lender-IRR/capital-structure analysis beyond the 16-category taxonomy.
3. **Accounting** — no primary 16-category ownership; cross-checks #1 credit/borrower, #2
   collateral/valuation, #8 cash-flow/DSCR, #14 fraud; OWNS the single normalized-NOI claim
   consumed by seats #1 and #2 (ROCO fraud tripwire).
4. **Legal & Structural** — #4 structural, #5 title/survey sub-pass, #6 environmental
   **legal-materiality sub-lens only** (CERCLA/Phase I currency — NOT a full physical
   review), #12 tax fold-in, #15 regulatory/state sub-pass, zoning/entitlement.
5. **Insurance & Climate** — #13 insurance + #16 ESG/physical-climate merged.
6. **Sponsor & Fraud-Forensics** — #10 sponsor, #14 fraud, cross-doc veracity, guarantor
   PFS.
7. **Portfolio & Concentration** — #11, fund-scoped.
8. **Strategy** — no primary 16-category ownership; a distinct strategic-fit
   falsifiable-objection lens (thesis fit, opportunity cost, off-mandate distraction); NOT
   an advocate.
9. **Deal Advocate** — no primary 16-category ownership; presents the steelman/bull case for
   the deal and answers objections raised by seats #1-8 with the strongest good-faith
   mitigant the evidence supports; structurally separate from the 8 scrutiny seats (no
   scrutiny vote); mitigants pass through the SAME falsification gate as objections (survive
   -> downgrade severity; refuted -> discarded).
10. **Gap-Hunter / Chair-agent** — procedural, no vote; hunts risks nobody claimed; also
    logs coverage lost to any chair-issued `exclude` command.
11-15. **Deal-triggered optionals** — Construction/Completion (#7, promoted from seat #1's
   baseline), Tax (#12, promoted from seat #4's fold-in), Market/Macro (#3, promoted from
   seat #1's sub-check), Compliance (#15, promoted from seat #4's state sub-pass),
   Environmental/Physical-Condition (#6 full review, fires only on a flagged REC or
   collateral type — seat #4 covers only the legal-materiality slice by default).

Environmental is DEMOTED from a core seat (agent-02's original 7-core draft) to a
deal-triggered optional (#15); its legally-material checks are permanently owned by seat #4
regardless of trigger, so risk category #6 is never fully uncovered.

**B. Vendored axiom-synthesis pipeline applied to objections** (the skill's own private
copy at `scripts/synthesis/`, no runtime dependency on the `acos-axiom-synthesis` skill):
ingest expert reports -> decompose to atomic objection-claims -> de-circularize (collapse
same-doc/same-clause/same-role votes; flag reduced independence) -> grade Axis A
(reliability) + Axis B (certainty) + Axis S (severity, IC extension) -> fuse per claim
(dual-track tally) -> falsify (different-discipline refuter cross-exam, INCLUDING seat #9
Deal Advocate's good-faith mitigant claims, FR-M24; ACH; nullification; oscillation guard)
-> resolve (same-fact conflicts via ladder; verdict = one `resolve_conflict()` over
discipline roll-ups; asymmetric-veto on deal-breakers) -> hash-chained ledger -> render
`recommendation.md`.

**C. Deal-breaker derived rule:** `deal_breaker = state ∈ {ESTABLISHED, CORROBORATED} AND
axis_s ∈ {material-risk, deal-breaker-candidate} AND no depends_on mitigant reaches
{CORROBORATED, ESTABLISHED}`. Keeps "is it true" (engine, mechanical) separate from "is it
fatal" (domain, computed after truth settles).

**D. Legal deal-breaker vs curable (agent 10):** Deal-breakers — SPE above threshold if
borrower refuses; entity authority for THIS loan; illegal non-conforming use w/o rebuild
letter; Phase I unaddressed RECs w/o Phase II; usury cannot qualify at proposed rate; OKOA
unlicensed where lending is void/voidable; AML/KYC sanctioned party; fraud indicators; IC's
own undisclosed conflict. Curable-by-CP — chain of title; lien priority; UCC searches;
guaranty carve-outs; insurance adequacy; intercreditor; leases/estoppels/SNDAs; ESG
disclosure. Risk-input-only (price it) — foreclosure mechanics/LGD.

**E. Standards referenced:** OCC Comptroller's Handbook (CRE Lending); FDIC RMS §3.2; FinCEN
CRE Financing Fraud advisory; ASTM E1527-21 (Phase I ESA, mandatory since 2024-02-13);
CERCLA §101(20) secured-lender exemption / BFPP; SEC 2026 exam priorities (private-credit
fiduciary + conflicts); ALTA/NSPS survey; Utah Commercial Financing Registration (2023).

**F. Evidence provenance:** primary evidence base is the swarm synthesis
(`.acos/swarm/swarm-20260707-141351/synthesis/report.md`) + agents 01-10 findings;
tiered T1 (regulator/standard) -> T5 (internal ACOS) in `evidence-ledger.json`.

---

## PRD Summary (One-Page Digest)

**What:** ACOS Investment Committee — a thin orchestrator that convenes a numbered
9-expert discipline roster (#1-8 scrutiny + #9 Deal Advocate) + a Gap-Hunter/Chair-agent
(#10, no vote) + deal-triggered optionals (#11-15) to find holes in a private-credit / RE
deal and produce the best-possible recommendation (limitations, mitigants, residual risk,
deal-breakers) with a **deterministically computed** verdict.

**Why:** single-analyst review misses discipline-specific holes; LLM reviews are
sycophantic; there is no deal-breaker/mitigable separation; concentration and financial-
statement fraud are nobody's job by default.

**How:** reuse a **vendored private copy** of `acos-axiom-synthesis` (Mode A synthesis,
preserves dissent, UNRESOLVED never fabricated, no runtime skill dependency) and
`legal-analyst` (legal seat); a shared upfront extraction layer feeding every seat
consistent raw facts, then per-expert private research swarms (2-4 bots each);
independence-first blind opening pass; mandatory falsifiable objections; a good-faith Deal
Advocate (#9) whose mitigants pass the SAME falsification gate as objections; Axis S
severity extension; deterministic asymmetric-veto verdict via `resolve.py`. Mode A =
synthesized memo (default); Mode B = live human-chaired moderated relay run by the
top-level SKILL.md with two-line Round-1 openers, Gap-Hunter-directed later rounds, ESC
interject, one-to-one/sidebars toggle, roster `exclude`/`include only` control, and
transcript-on-disk.

**Two output modes:** (A) synthesized 13-section IC memo; (B) live interruptible
deliberation with a human chair (procedural, not evidentiary authority).

**Non-negotiables:** independence-first; never terminate on consensus; verdict deterministic
never narrated; every finding carries mitigant + residual + CP; concentration and fraud
explicitly owned; autopilot MUST be off (pre-flight assertion aborts otherwise, no
fallback); roster exclusions are logged by Gap-Hunter, never silent; Deal Advocate mitigants
must survive the same falsification gate as objections.

**Verdict states:** PROCEED | PROCEED-WITH-CONDITIONS | DECLINE | UNRESOLVED.

**Demos:** D1 3-seat (#1, #3, #4) Mode A memo -> D2 full 9-expert + Gap-Hunter (#10)
roster + severity + deterministic verdict -> D3 Mode B live deliberation.

**Top risks:** consensus≠correctness; sycophancy/correlated error; autopilot auto-answer;
unowned concentration/fraud; greenfield UX; Axis S unvalidated; OKOA governance unknowns
(marked `Assumption`); Deal Advocate as a sycophancy vector; shared-extraction single point
of failure.
