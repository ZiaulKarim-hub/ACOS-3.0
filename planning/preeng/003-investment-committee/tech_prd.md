# Technical PRD — ACOS Investment Committee (003-investment-committee)

**Command:** `/preeng.plan` output (technical PRD).
**Companion:** `plan.md`, `data-model.md`.
**Grounding:** `spec.md` §4.2/§4.3, `research.md`, `domain-lattice.json`,
`.acos/swarm/swarm-20260707-141351/synthesis/report.md` + agent-04 / agent-07 / agent-10.

This document specifies the **component architecture** and the **contracts** between the IC
skill (domain adapter) and the reused ACOS engines (epistemics). It defines expectations,
not implementation code.

---

## 1. Component architecture

### 1.1 SKILL.md router (`/acos-investment-committee`) — the moderator seat

- **Type:** top-level ACOS `SKILL.md`, `user-invocable: true`, runs in the **main
  conversation**. This is the ONLY component permitted to call `AskUserQuestion` /
  `ExitPlanMode` (hard platform constraint — subagents cannot; agent 04). All Mode B human
  pausing is owned here. [lattice: `pattern-main-convo-moderator`]
- **Invocation surface (`Assumption`):**
  `/acos-investment-committee --deal <dir> --mode A|B [--autopilot] [--seats lean|full]`.
- **Responsibilities:** parse args; **pre-flight ASSERT `.acos/state/autopilot-active` is
  absent (ABORT with a clear message if present — no autonomous-fallback branch)**; run
  intake (delegates to the shared extraction layer, §1.11, which produces the deal-brief +
  evidence-index every seat reads); resolve the session's active roster (exclude/include,
  §1.2 "Active roster"); dispatch the independence-first blind opening pass (each seat also
  spawning its private research swarm, §1.12); branch to Mode A (fan-out -> synthesize) or
  Mode B (moderated relay); own the round-boundary `AskUserQuestion` menu, the
  ESC-interject handler, the roster `exclude`/`include only` command (§1.2, §1.7), and the
  one-to-one/team-deliberation toggle; never narrate a verdict; render/print the final
  artifacts.
- **Model:** the router runs in the main conversation (advisory model per `/model`); seat
  spawns get per-seat model classes via `resolve-agent-model.sh`.

### 1.2 Seat expert agents (numbered 9-expert core [8 scrutiny seats + Deal Advocate #9] + Gap-Hunter (#10) + deal-triggered optionals (#11-15))

- **Type:** `Task()`-spawned agents (subscription-only; never `ANTHROPIC_API_KEY`).
- **Seat numbers are STABLE** — the chair, transcript, and turn schema
  (`addresses_prior_turn_ids`) all refer to seats by number; numbers are never reassigned
  mid-session.
- **Core 8 (seat -> owned risk categories, from the 16-risk map):**
  1. **Credit & Valuation** — is collateral+cash-flow sufficient to secure & repay
     (LTV/DSCR/comps/cap-rate). Runs TWO explicit sub-passes: **collateral-value** (#2
     Collateral/Valuation, #3 Market/Macro sub-check, #7 Construction/Completion baseline)
     and **repayment-capacity** (#1 Credit/Borrower, #8 Cash-Flow/DSCR). Merges the former
     separate Credit and Valuation seats. [`seat-credit-valuation`, `metric-dscr`]
  2. **Finance** — are we paid enough & is structure/exit sound: spread, lender IRR,
     capital structure, refi/takeout. Core-owns #9 Interest-Rate/Refi/Exit (folded in from
     the former Credit sub-mandate — now a permanent core ownership, not an optional).
     [`seat-finance`]
  3. **Accounting** — are the numbers real & normalized (QoE/GAAP/add-backs). **OWNS the
     single normalized-NOI claim** that seat #1 (collateral-value + repayment-capacity) and
     seat #2 (spread/lender-IRR) both consume; disagreement between Accounting's NOI and
     #1/#2's NOI is a mandatory escalation — the ROCO fraud tripwire. Does not primarily own
     one of the 16 risk categories; cross-checks #1 Credit/Borrower, #2
     Collateral/Valuation, #8 Cash-Flow/DSCR, #14 Fraud. [`seat-accounting`,
     `term-noi-tripwire`]
  4. **Legal & Structural** — #4 Structural/Legal, #5 Title/Survey sub-pass, #15
     Regulatory/Compliance state sub-pass, #12 Tax fold-in, zoning/entitlement, PLUS an
     **environmental-legal sub-lens** on #6 Environmental — CERCLA §101(20) secured-lender
     shield, Phase I ASTM E1527-21 currency/staleness — scoped ONLY to what is legally/
     financially material to OKOA (not a full physical condition review). Delegates
     document diligence to `legal-analyst`. [`seat-legal`, `std-astm-e1527`, `std-cercla`]
  5. **Insurance & Climate** — #13 Insurance + #16 ESG/physical-climate merged; a
     non-renewal / premium-spike is a financial lens (stresses renewal cost into pro forma,
     DSCR transmission). [`seat-insurance`]
  6. **Sponsor & Fraud-Forensics** — #10 Sponsor/Track-Record, #14 Fraud/Misrepresentation;
     explicit adversarial statement-veracity mandate ("assume fabricated until externally
     corroborated"). [`seat-fraud`, `std-fincen-cre-fraud`]
  7. **Portfolio & Concentration (fund-scoped)** — #11 Concentration/Portfolio; reads the
     fund loan tape, NOT deal-scoped. [`seat-portfolio`, `loan-tape`]
  8. **Strategy** — thesis fit, opportunity cost, off-mandate distraction. Does not own one
     of the 16 deal-risk categories (a distinct strategic-fit lens); held to the SAME
     falsifiable-objection discipline as every other seat — MUST produce a falsifiable
     "fails strategically because ___" objection or abstain. **NOT an advocate** for the
     deal. [`seat-strategy`]
- **(9) Deal Advocate — ninth expert seat, structurally separate from scrutiny:** presents
  the deal's steelman/bull case; during deliberation, responds to objections raised by seats
  #1-8 with the strongest GOOD-FAITH mitigant the evidence supports. Does NOT hunt holes and
  casts NO scrutiny vote — structurally separate from the 8 scrutiny seats (independence
  principle; three-lines-of-defense analog, `std-three-lines`). Its mitigants are treated as
  CLAIMS and MUST pass through the SAME falsification gate as objections (§1.4 falsify
  stage): survive -> downgrades the targeted objection's Axis S severity; refuted ->
  discarded, not counted. Prompt invariant: must argue in good faith FROM EVIDENCE already
  in the deal materials, the shared deal-brief (§1.11), or its own private swarm findings
  (§1.12); fabrication is prohibited under the same anti-hallucination discipline as every
  other seat. Does not own a primary 16-risk-map category. [`seat-deal-advocate`,
  `proc-falsification-gate`]
- **(10) Gap-Hunter / Chair-agent meta-seat** — procedural, **NO vote**; each round selects
  which seat(s) have something material to add (including calling seat #9 to respond to a
  specific objection); hunts for risks nobody claimed; never silences dissent. Also owns the
  exclude/include roster-coverage log (below): when a seat is excluded from the active
  roster, Gap-Hunter records what coverage is left unowned for the session.
  [`seat-gap-hunter`]
- **Active roster / exclude-include (roster mechanism):** the chair sets the ACTIVE roster
  for a session via `exclude #n[, #n ...]` or `include only #n[, ...]`; usable at session
  start OR mid-session. Excluded seats are skipped by Gap-Hunter (#10) selection above and
  never opened for that session. The active roster is recorded in `manifest.yaml` as an
  `active_seats` list (§2). When a seat is excluded, Gap-Hunter (#10) MUST log what coverage
  is left unowned (e.g. "excluding #3 -> normalized-NOI veracity unowned this session") — a
  conscious, recorded choice, never a silent gap. Chair command syntax lives in the
  vocabulary list, §1.7. [`method-roster-exclude-include`, `anti-silent-roster-gap`]
- **Deal packaging (human, not a numbered seat):** the deal team / underwriting lead
  packages the ask and MUST NOT cast a scrutiny vote (three-lines-of-defense independence);
  this is a human deal-team role, not one of the 9 numbered committee seats. **Do not
  confuse this human packaging role with Seat #9 Deal Advocate above** — the human packages
  the deal outside the committee; Seat #9 is an AI committee seat inside the committee,
  structurally separate from the 8 scrutiny seats, and its good-faith mitigants are subject
  to the SAME falsification gate as every objection. [`std-three-lines`]
- **Deal-triggered optionals (#11-15), seated only on trigger:** (11) Construction/
  Completion (promoted from seat #1's collateral-value baseline), (12) Tax (promoted from
  seat #4's fold-in), (13) Market/Macro (promoted from seat #1's sub-check), (14) Compliance
  (promoted from seat #4's state sub-pass), (15) Environmental/Physical-Condition (fires
  only on a flagged REC or collateral type — the full physical/environmental review that
  seat #4's legal sub-lens does NOT cover).
- **Diversity:** each seat resolves a model class (Opus vs Sonnet) + persona/temperature via
  the Model Profile system (`resolve-agent-model.sh`). If all seats share one provider ->
  emit `reduced_independence: true`. [`method-model-diversity`, `metric-independence-flag`]
- **Prompt invariants (every scrutiny seat #1-8 plus the optionals #11-15):**
  independence-first (open blind); >=1 **falsifiable** objection ("the deal fails if/because
  ___; evidence present/absent/untested"); the chair's stated opinion carries **no automatic
  evidentiary weight** (including in a one-to-one side-channel); agreement without new
  evidence is forbidden; confidence is *derived*, never self-reported. **Seat #9 Deal
  Advocate is EXEMPT from the falsifiable-objection requirement** (its function is defense,
  not objection-hunting) but shares every other invariant: no automatic evidentiary weight
  for the chair's opinion, no fabrication, and derived (not self-reported) confidence for
  its mitigant claims.

### 1.3 IC fact-builder adapter (the Axis S owner)

- **Purpose:** the domain adapter that converts each expert **Objection** into an
  axiom-synthesis atomic `fact` record — the ONLY place the severity extension lives.
- **Engine contract (unchanged, vendored copy):** `scripts/synthesis/orchestrate.py::process_fact()`
  consumes `{fact_id, statement, claim_type, candidates, grading, flags, refuter, conflict,
  depends_on, covers}`.
- **Axis S extension (domain-owned, NOT an engine field):** attach
  `_ic_extension_severity {axis_s_materiality, raised_by_role, rationale}` where
  `axis_s_materiality ∈ {informational, limitation, material-risk, deal-breaker-candidate}`
  on a fixed ordinal ladder, scored by the raising seat, **stored alongside Axis A
  (reliability) and Axis B (certainty) and NEVER blended with them.** The engine grades
  TRUTH; Axis S grades "how bad if true." A stale-insurance-cert and a no-enforceable-lien
  objection must NOT grade identically. [`method-severity-axis-s`, `metric-severity-ladder`]
- **Mitigant handling:** a mitigant surfaced by a refuter — INCLUDING Seat #9 Deal
  Advocate's good-faith mitigant claims (§1.2) — is a NEW `fact` with `depends_on` the
  objection. Residual severity is a **rendering-time compute**, not a ledger state.
- **Same-fact conflicts:** route each same-underlying-fact cross-discipline contradiction
  through `resolve_conflict()` as `fact["conflict"]` — **never** an aggregator-LLM prose
  blend (MoA anti-pattern). Detecting "same atomic fact" (same collateral/entity ref +
  contradictory value) is an open design surface (entity-linking reuse candidate). The
  Accounting (#3) vs Credit & Valuation (#1) NOI disagreement is the canonical example of a
  same-fact conflict that MUST route through `resolve_conflict()`, never a silent override
  by either seat. [`anti-llm-aggregator-blend`]

### 1.4 Vendored axiom-synthesis engine (private copy, standalone)

- **Type:** a **private, vendored copy** of the `acos-axiom-synthesis` engine, copied into
  `.claude/skills/acos-investment-committee/scripts/synthesis/`:
  - **Substrate:** `axiom_ledger.py`, `ledger_writer.py`, `verify_ledger.py`,
    `next_claims.py`, `render.py`.
  - **Pipeline:** `decircularize.py`, `grade_fuse.py`, `falsify.py`,
    `oscillation_guard.py`, `resolve.py`, `lifecycle.py`, `coverage.py`, `mirror.py`,
    `orchestrate.py`.
  - **Tests:** `test_substrate.py`, `test_pipeline.py` (vendored alongside the scripts, run
    in-skill; fixture-tested, 54 assertions, Phases 0-7, at vend time).
  - **Provenance:** `scripts/synthesis/VENDORED_FROM.md` records the source skill path and
    the exact git commit vended from, so drift can be audited.
- **Standalone by design:** the IC skill has **NO runtime import of / dependency on** the
  `acos-axiom-synthesis` skill. This is a deliberate tradeoff — the IC skill must keep
  working even if `acos-axiom-synthesis` changes, is removed, or is unavailable; the cost is
  that upstream engine fixes are NOT automatically inherited (a human must periodically diff
  against `VENDORED_FROM.md` and re-vend).
- **Pipeline applied to objections (unchanged logic, vendored code):** ingest expert reports
  -> decompose to atomic objection-claims -> **de-circularize** (collapse same-doc/same-
  clause/same-role votes; flag reduced independence) -> **grade** Axis A + Axis B (+ Axis S
  carried alongside, IC-owned) -> **fuse** per claim (dual-track tally, single-source cap) ->
  **falsify** (independent DIFFERENT-discipline refuter cross-exam — INCLUDING Seat #9 Deal
  Advocate's good-faith mitigant claims, which enter this SAME stage as any other refuter
  counter-claim, §1.2, §1.3; ACH; nullification; oscillation guard) -> **resolve**
  (same-fact conflicts via precedence ladder) -> hash-chained append-only ledger. **No
  change to the vendored engine scripts' logic** vs the upstream `acos-axiom-synthesis`
  source at vend time. [`engine-axiom-synthesis-vendored`, `proc-falsification-gate`]
- **Guarantees inherited (from the vendored code):** single-writer ledger; single-source cap
  (a lone objection caps at `probable`); `UNRESOLVED` first-class; tamper-evident hash chain;
  demotion cascade over dependents (`lifecycle.py`).

### 1.5 Deterministic verdict computation

- **Mechanism:** `resolve.py` (vendored copy, `scripts/synthesis/resolve.py`) — the overall
  verdict is modeled as **one final `fact`** whose candidates are per-discipline roll-ups,
  resolved by `resolve_conflict()` with **asymmetric-veto polarity gated on
  deal-breaker-flagged claims** (false-accept is the catastrophic error), quorum/precedence-
  ladder for ordinary limitations; terminates in `UNRESOLVED`. **Zero new engine code beyond
  the vendored copy.** Seat #9 Deal Advocate does NOT contribute a discipline roll-up (it
  casts no scrutiny vote, §1.2); its influence on the verdict is indirect only, via
  downgrading or failing to downgrade the objections its mitigants target during falsify
  (§1.4). [`proc-deterministic-verdict`, `method-asymmetric-veto`]
- **Deal-breaker (derived deterministic domain rule, computed AFTER truth settles):**
  `deal_breaker = state ∈ {ESTABLISHED, CORROBORATED} AND axis_s ∈ {material-risk,
  deal-breaker-candidate} AND no depends_on mitigant reaches {CORROBORATED, ESTABLISHED}`.
  Keeps "is it true" (engine, mechanical) separate from "is it fatal" (domain). [`term-deal-breaker`]
- **Verdict states:** `PROCEED | PROCEED-WITH-CONDITIONS | DECLINE | UNRESOLVED`. Computation:
  any deal-breaker without a CORROBORATED+ mitigant -> **DECLINE** (asymmetric veto); truth
  CONTESTED with no deciding rung -> **UNRESOLVED**; deal-breakers all mitigated but material
  risk remains -> **PROCEED-WITH-CONDITIONS** (conditions = surviving mitigant claims);
  nothing material survives -> **PROCEED**. **Never a synthesizer LLM narrating the word.**
  [`anti-narrated-verdict`]

### 1.6 13-section IC memo renderer (Mode A)

- Renders `recommendation.md` **from the ledger, via the vendored `render.py`, never
  hand-edited.** Front-matter: deal, ic_session, contributors, `independence_note`
  (reduced-independence flag), ledger_head, confidence_tier_definitions. Sections (agent 08
  canon): BLUF Recommendation box -> Exec Summary -> Transaction/Loan Summary -> Sponsor &
  Guarantor -> Collateral & Valuation -> Market -> Financial Analysis -> Sensitivities/
  Downside -> **Risks & Mitigants (repeating Risk->Mitigant->Residual triplet table with CP
  cross-refs)** -> Structure & Covenants -> Conditions Precedent -> Legal/Title/
  Environmental -> Exit/Repayment -> Recommendation (full + Key Judgment Calls). Severity
  language: 4-tier plain-English (Monitor / Mitigated / Material-Conditioned /
  Disqualifying) mapped to FATAL/MATERIAL/MINOR and to OCC Pass/SM/Substandard/Doubtful/
  Loss. [`artifact-ic-memo`, `pattern-risk-mitigant-residual`]

### 1.7 Mode B moderator loop + append-only transcript + deterministic tally

- **Moderator loop (owned by the main conversation, §1.1):**
  - **Round 1 — blind parallel two-line openers.** Every seated seat runs the SAME
    independence-first blind pass as Mode A, but its opening turn is compressed to
    **two lines**: line 1 = number of gaps found + why the chair should care; line 2 =
    overall recommendation. Full detail is still written to the per-seat opening JSON on
    disk; only the two-line digest hits the transcript/terminal. Seat #9 Deal Advocate's
    two-line opener instead presents the deal's steelman/bull case (line 1 = strongest case
    for the deal; line 2 = overall recommendation), since it has no gaps to count.
  - **Round 2 onward — Gap-Hunter-directed.** The Gap-Hunter (#10) reviews the prior round
    and selects which seat(s) have something material to add — including calling Seat #9
    Deal Advocate to respond to a specific objection with a good-faith mitigant (§1.2).
    Selected seats speak **serially** (not blind), referencing prior turns **by seat number**
    (`addresses_prior_turn_ids`), under a **150-250 word cap**, with a **mandatory
    mitigant + residual-risk statement attached to every non-fatal gap** they raise or
    concede.
  - **Pause after EVERY round** — the chair menu (`AskUserQuestion`) fires after each round
    with no auto-continue; Mode B never advances a round silently.
  - **ESC interject (any time):** the chair can interrupt an in-flight turn. This aborts the
    in-flight `Task()` turn; the deliberation resumes with the chair-tagged seat if one was
    named, else the last speaker — that seat folds the chair's new fact into its position,
    re-comments, and then the Gap-Hunter (#10) re-selects who speaks next.
  - **One-to-one toggle:** `"one to one #n"` moves a named seat into a private channel with
    the chair; every other seat is paused; the raw exchange is persisted to
    `sidebars/<seat>-<n>.json` / `.md` (never mixed into the main transcript). `"team
    deliberation"` returns to the floor; on return, **every seat receives a sidebar
    summary** — new facts surfaced + that seat's position changes — while the raw one-to-one
    chat stays in the sidebar file. This is a private channel with a transparent OUTCOME
    (not a transparent transcript).
  - **Termination:** `/end`, a hard round cap (5-6), or a forced `/vote`. Mode B NEVER
    terminates because "everyone agrees." On termination, the FULL transcript (all rounds +
    sidebar summaries, not raw sidebar chat) is handed to the SAME vendored synthesis
    engine as Mode A (§1.4), the SAME deterministic verdict computation (§1.5,
    asymmetric-veto on deal-breakers) runs, and the SAME 13-section memo renderer (§1.6)
    produces the final artifact — dissent is preserved into the memo, never smoothed over.
- **Append-only transcript (source of truth, NFR-4):** each turn written to
  `rounds/round-NN/**` JSON + appended to human-readable `transcript.md` **before** the next
  `Task()`. Conversation memory is never authoritative. [`pattern-transcript-on-disk`,
  `artifact-transcript`]
- **Turn schema (FR-M11):** `{round, seat, stance ∈ SUPPORT|REBUT|ABSTAIN|CONDITIONAL|
  FLAG_RISK, argument (<=150-250 words from Round 2 on; 2 lines in Round 1),
  addresses_prior_turn_ids, would_change_mind_if}`; reversals prefixed `⟲ UPDATED`.
- **Deterministic tally (`consensus_check.py` style, dr2 pattern):** plain Python answers
  mechanical questions only — everyone responded? majority? veto? converged? LLM judgment is
  reserved for argument quality. **Never terminate a round on consensus.** Numeric confidence
  is hidden between agents mid-debate; a lopsided approve-leaning distribution triggers a
  mandatory 10th-man pass. [`method-devils-advocate`, `anti-consensus-as-correctness`]
- **Chair vocabulary:** `/call /ask /challenge /vote /premortem /table /board /recap
  /end|/synthesize`, plus `exclude #n[, #n ...]` / `include only #n[, ...]` (sets the
  session's active roster, §1.2; usable at session start OR mid-session; Gap-Hunter #10
  logs any resulting coverage gap), **ESC** (interject) and **one-to-one toggle**;
  plain-English fallback always accepted; freeform text -> a `[CHAIR — you]` turn.
  **Scoreboard** reprints at checkpoints (every ~3 rounds / `/board`); `/recap` prints
  Converged / Open / Tabled / Lean (terminal has no sidebar-panel).
- **Human injection (FR-M12):** a chair message is a first-class `HUMAN_OVERSEER` transcript
  turn; every implicated seat in the next round MUST address it (update-with-a-named-new-fact
  or hold-with-a-reason), never capitulate. Chair authority is **procedural, not evidentiary**
  (FR-M13) — including inside a one-to-one. [`method-justification-forcing`]
- **Resume (NFR-4):** `manifest.yaml` (`status: open|paused_for_human|closed` + round
  pointer) + `round-status.yaml` let the skill re-enter at the last-closed round after
  `/clear`, crash, or Eternity handoff. An in-flight one-to-one records its own status in
  `sidebars/<...>.status.yaml` so resume knows whether to re-enter the sidebar or the floor.

### 1.8 Legal-analyst reuse wrapper + compliance companion

- **Delegation (FR-M15).** Seat #4 (Legal & Structural) delegates document diligence to
  `legal-analyst` via `/acos-legal-analysis --mode lending` (produces `findings-manifest.yaml`,
  `red-flags.yaml`), then **re-projects** `red-flags.yaml` into IC voting format — it does NOT
  re-derive a parallel framework. [`proc-legal-delegation`, `engine-legal-analyst`]
- **Compliance companion (FR-M16):** covers legal-analyst's four gaps — lender-side
  usury/licensing (per-deal jurisdiction check; Utah Commercial Financing Registration),
  AML/KYC/OFAC/beneficial-ownership, structured foreclosure-mechanics fields
  (`foreclosure_type, timeline_days, deficiency_available`), and Phase I **ASTM E1527-21**
  currency/staleness gate (mandatory since 2024-02-13; feeds CERCLA §101(20) BFPP defense).
  This is seat #4's environmental-legal sub-lens; it stops at legal/financial materiality
  and does NOT extend to a full physical/environmental condition review (that is optional
  seat #15).
- **Deal-breaker vs curable (spec Appendix D):** enumerated legal deal-breakers (SPE above
  threshold if refused; entity authority for THIS loan; illegal non-conforming use w/o
  rebuild letter; unaddressed Phase I RECs w/o Phase II; usury; unlicensed lending where
  void/voidable; AML/OFAC sanctioned party; fraud indicators; IC's own undisclosed conflict)
  vs curable-by-CP (chain of title, lien priority, UCC, guaranty carve-outs, insurance,
  intercreditor, leases/estoppels/SNDAs) vs risk-input-only (foreclosure mechanics / LGD).

### 1.9 conflicts-disclosure.yaml emitter (governance)

- Per-run artifact (FR-M19); each seat discloses conflicts before voting; evidences the
  committee's own process was sound (SEC 2026 fiduciary focus). [`conflicts-disclosure`,
  `std-sec-2026`]

### 1.10 autopilot pre-flight assertion (not a detector-with-fallback)

- **At skill entry (BOTH Mode A and Mode B), before any dispatch:**
  `test -f .acos/state/autopilot-active`. If present, the skill **ABORTs immediately** with
  a clear message instructing the user to disable autopilot manually before invoking the
  Investment Committee. **There is no autonomous-fallback branch** — the design guarantee is
  that the USER keeps autopilot off manually; the skill only asserts and refuses, it never
  tries to work around an active autopilot session. [`proc-autopilot-preflight-assert`,
  `risk-autopilot-auto-answer`]

### 1.11 Shared extraction layer (single upfront read of the deal folder)

- **Purpose:** eliminate 9x redundant extraction and keep every seat working from
  consistent base facts. **Research depth is NOT tiered** — there is no quick/deep or
  swarm/no-swarm mode selector; every Mode A and Mode B run (§1.1) includes BOTH this shared
  extraction layer AND the per-expert private swarms (§1.12). The existing `--seats
  lean|full` flag (§1.1) selects ROSTER SIZE only, never research depth.
- **Mechanism:** ONE `Task()` pass reads the deal directory ONCE, at intake (before the
  independence-first blind opening pass, §1.2), and produces a structured, read-only shared
  **deal-brief + evidence-index** (raw facts + citations only — T-12/financials, rent roll,
  appraisal figures, org docs, entity list, insurance certs, etc. — NOT interpretations, NOT
  normalized figures) persisted to `deal-brief/` (§2). All 9 expert seats read this before
  or alongside forming their own independent judgment.
- **Relationship to the NOI fraud tripwire (unchanged mechanic):** the RAW financial data
  that feeds Seat #3 Accounting's normalized-NOI claim originates here (single source of
  raw facts) — Accounting still independently DERIVES the normalized-NOI claim from these
  raw numbers (ownership unchanged, §1.2 item 3); Credit & Valuation (#1) and Finance (#2)
  independently derive their OWN read of the same raw numbers. Disagreement between
  Accounting's derived claim and #1/#2's own derived read remains the mandatory-escalation
  ROCO fraud tripwire (§1.3) — the shared layer removes REDUNDANT re-extraction; it does NOT
  remove independent interpretation.
- **Guarantee:** prevents 9x redundant extraction and a stale/transcription-drifted version
  of the same source document circulating between seats. [`method-shared-extraction`,
  `pattern-single-source-raw-facts`]

### 1.12 Per-expert private research-swarm sub-component

- **Purpose:** discipline-specific deep/external research (governing law, comps, submarket
  data, sponsor litigation search, regulatory currency, etc.) that the shared extraction
  pass does not cover — it only reads the deal folder; swarms reach OUTWARD.
- **Mechanism:** after reading the shared deal-brief (§1.11), each of the 9 expert seats
  (#1-9) spawns its OWN private swarm of **2-4 `Task(general-purpose)` research bots**,
  SIZED TO NEED per deal (a seat with nothing external to check may run as few as 2; a seat
  facing an unusual jurisdiction/asset class may run 4).
- **Blind independence:** swarm bots report ONLY to their spawning seat — NO cross-seat
  visibility into another seat's swarm, the same blind-independence discipline as another
  seat's opening verdict (§1.2, `proc-independence-first`). Findings persist to
  `swarms/{seat}/` (§2).
- **Fold-in:** each seat folds the shared-layer facts + its own private swarm's CITED
  findings into its objection (or, for Seat #9, its good-faith mitigant, §1.2) before that
  objection/mitigant enters the IC fact-builder (§1.3) and the falsification gate's evidence
  grading (§1.4) — swarm-citation quality is one input to Axis A reliability.
- **Dispatch discipline:** subscription-only `Task()`, same as every other spawn (NFR-1);
  no `ANTHROPIC_API_KEY`. [`method-private-research-swarm`, `pattern-blind-swarm-reporting`]

---

## 2. On-disk state layout (from spec §4.2 / agent 04)

```
.acos/investment-committee/<session-id>/
  manifest.yaml         # deal context, roster, active_seats (exclude/include, §1.2), round
                         # config, status: open|paused_for_human|closed
  deal-brief/            # shared extraction layer (§1.11): deal-brief.json + evidence-index.json
                         # (read-only, all 9 seats)
  transcript.md         # human-readable append-only render (Mode B)
  rounds/round-NN/
    opening/{seat}.json # blind opening verdicts (both modes; Round 1 two-line digest in Mode B)
    turns/{turn-id}.json# Mode B per-turn records
    human-injection.json# HUMAN_OVERSEER turn(s)
    round-status.yaml   # tally result + resume pointer
  swarms/{seat}/         # per-expert private research-swarm findings (§1.12; blind, seat-scoped)
  sidebars/              # one-to-one side-channel transcripts + sidebar summaries (Mode B)
  conflicts-disclosure.yaml
  ledger/               # vendored axiom-synthesis hash-chained ledger + settled-objections.md
  recommendation.md     # Mode A memo / Mode B final synthesis
  verdict.md            # deterministic verdict + rationale (which rung/polarity decided)
```

Manifest status state machine: `open -> (dispatch round) -> paused_for_human -> (resume) ->
open -> ... -> closed`.

---

## 3. Non-functional requirements (from spec §4.3)

- **NFR-1 Subscription-only** — all agents via `Task()`; never `ANTHROPIC_API_KEY`.
- **NFR-2 Hook compliance** — Oracle PreToolUse, check-scope, Independence Wall, autopilot/
  Eternity continuation.
- **NFR-3 Determinism** — verdict reproducible from the ledger: same ledger -> same verdict.
- **NFR-4 Durability** — every turn hits disk immediately; survives `/clear`, crash, Eternity;
  resume at last-closed round.
- **NFR-5 Observability** — SubagentStop logs expert identity/round to
  `.acos/metrics/agent-completions.log`; per-turn JSON + transcript + hash-chained ledger =
  audit trail.
- **NFR-6 Cost/latency** — round cap 5-6; blind parallel openings; rolling-synthesis + last-K
  verbatim context window (constant per-call cost); Mode A cheaper default, Mode B opt-in;
  per-expert private research swarms sized 2-4 bots to need (§1.12), bounding swarm cost per
  seat.
- **NFR-7 Honesty** — moderated-relay framing (turn-based, not simulated real-time);
  UNRESOLVED + reduced-independence flags surfaced, never hidden.
- **NFR-8 Artifact quality** — memo boss-criticism-proof on a first cold look.

---

## 4. APA / PSA metrics scaffolding (§0.5 — formulas defined, not computed)

| Metric | Definition | Where recorded |
|--------|-----------|----------------|
| SPD | Story Points Delivered (qualitative approximation per slice) | `AGENT-METRICS.md` |
| QAP | `(Delivered_Value * Quality_Score) / (1 + Rejection_Count)` | `AGENT-METRICS.md` |
| TER | Token Efficiency Ratio: artifacts per 1K tokens | `AGENT-METRICS.md` |
| UAPS | `0.3*Quality + 0.4*Efficiency + 0.3*CostEffectiveness` | `AGENT-METRICS.md` |

**Instrumentation plan:** ACOS already logs agent identity to
`.acos/metrics/agent-completions.log` (agent_type / agent_id via SubagentStop) — the IC seat
spawns inherit this automatically. Per-slice production/efficiency roll-ups are aggregated
into a feature-level `AGENT-METRICS.md`. **Domain-quality analytics (IC-specific):**
risk-category coverage %, deal-breaker count/type, mitigant-attachment rate, independence
flag (single- vs multi-provider), stance-flip count per seat (flip auditing), UNRESOLVED
rate, round count vs cap, mitigant survival rate (Deal Advocate claims that survive vs are
refuted), excluded-seat coverage-gap log completeness. Metrics are *defined* here and
*computed* post-run — never during pre-engineering.

---

## 5. Component -> requirement traceability (selected)

| Component | Requirements | Lattice anchors |
|-----------|-------------|-----------------|
| SKILL.md router / moderator | FR-M9, FR-M20, FR-M21, NFR-2 | `pattern-main-convo-moderator`, `proc-mode-b` |
| Seat expert agents (numbered #1-9 experts [8 scrutiny + #9 Deal Advocate] + #10 Gap-Hunter + #11-15 optionals) | FR-M1, FR-M2, FR-M3, FR-M4, FR-M24, FR-S4 | `seat-*`, `seat-deal-advocate`, `proc-independence-first` |
| Roster exclude/include command | FR-M25 | `method-roster-exclude-include`, `anti-silent-roster-gap` |
| Shared extraction layer | FR-M26 | `method-shared-extraction`, `pattern-single-source-raw-facts` |
| Per-expert private research swarms | FR-M27, FR-M28 | `method-private-research-swarm`, `pattern-blind-swarm-reporting` |
| IC fact-builder / Axis S | FR-M5, FR-M24 | `method-severity-axis-s`, `metric-severity-ladder` |
| Vendored axiom-synthesis engine (standalone) | FR-M6, FR-M24 | `engine-axiom-synthesis-vendored`, `proc-falsification-gate` |
| Deterministic verdict | FR-M7, FR-W2, NFR-3 | `proc-deterministic-verdict`, `method-asymmetric-veto` |
| Memo renderer | FR-M8, NFR-8 | `artifact-ic-memo`, `pattern-risk-mitigant-residual` |
| Mode B loop / transcript / tally / ESC / one-to-one | FR-M10..14, FR-M22, FR-M23, NFR-4 | `pattern-transcript-on-disk`, `method-justification-forcing` |
| Legal reuse + compliance + conflicts | FR-M15, FR-M16, FR-M19 | `proc-legal-delegation`, `conflicts-disclosure` |
| Concentration / fraud ownership | FR-M17, FR-M18 | `seat-portfolio`, `seat-fraud`, `anti-silent-concentration-pass` |
| autopilot pre-flight assertion | FR-M20 | `proc-autopilot-preflight-assert`, `risk-autopilot-auto-answer` |
