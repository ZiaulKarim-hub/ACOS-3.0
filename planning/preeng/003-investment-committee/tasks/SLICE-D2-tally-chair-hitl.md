# SLICE-D2-tally-chair-hitl — Deterministic tally + Gap-Hunter selection + chair menu + ESC interject + one-to-one

**Parent story:** STORY-D1 (tally) / STORY-D2 (chair HITL) · **Epic:** EPIC-D · **Effort:** M · **Demo:** Demo 3
**slice.yaml mapping:** Objective->`objective`; Allowed files->`files_allowed`;
DoD+evidence gates->`acceptance_criteria`; QA verification->`verification_method`.

## PM (Planner / LCE brief)

**Objective (single, narrow):** Add the deterministic tally (mechanical-only, plain Python,
NEVER an LLM), Gap-Hunter (#10, procedural/no-vote) per-round speaker selection, the Deal
Advocate's (#9) participation as deliberation defense (mitigant turns against scrutiny
objections, same falsification gate, no vote), the round-boundary chair pause+menu (chair
addresses seats BY NUMBER, incl. `exclude`/`include only` active-roster commands), an ESC
mid-turn interject path, and a one-to-one sidebar toggle — with the chair's authority
procedural, never evidentiary, in both team deliberation and 1:1.

**In-scope:**
- `tally.py` (plain Python, NOT an LLM): over the round's turn JSONs, answers only mechanical
  questions — did every selected seat respond? majority/veto signal? stagnation (2 rounds with
  no new claim)? Hides numeric confidence between agents. NEVER declares a verdict and NEVER
  terminates a round/session on "all agree."
- the Turn stance schema `{round, seat, stance ∈ SUPPORT|REBUT|ABSTAIN|CONDITIONAL|FLAG_RISK,
  argument, addresses_prior_turn_ids, would_change_mind_if}` with `⟲ UPDATED` reversals.
- Gap-Hunter (#10, procedural, no vote): each round, selects which seat(s) have something
  material to add; unselected seats stay silent that round; selection additionally respects the
  session's active roster (see exclude/include below) — excluded seats are never selected.
- Deal Advocate (#9, participates, no vote): after scrutiny seats raise objections in a round,
  the Advocate MAY respond with the strongest good-faith mitigant when Gap-Hunter (#10) calls on
  it (like any seat); the Advocate's mitigants are CLAIMS that pass the SAME falsification gate
  as objections — survive -> downgrade the objection's severity; refuted -> discarded. The
  Advocate does NOT hunt holes and casts NO scrutiny vote; it is never counted in the tally.
- Pause after EVERY round -> chair menu: `Continue · /call <n> · /challenge <n> <claim> ·
  /ask <n[,n]> <q> · /vote · /premortem · one to one #n · exclude #n[, #n ...] · include only
  #n[, ...] · /end` (+ plain-English fallback). The chair refers to seats BY NUMBER (the stable
  1-14 roster).
- `exclude #n[, #n ...]` / `include only #n[, ...]`: sets the ACTIVE roster for the session,
  recorded in `manifest.yaml` `active_seats`; excluded seats are skipped by Gap-Hunter selection
  and never open; works at session start OR mid-session. When a seat is excluded, Gap-Hunter
  (#10) LOGS what it leaves uncovered (e.g. "excluding #3 -> normalized-NOI veracity unowned
  this session").
- ESC interject (anytime, mid-turn): aborts the in-flight turn (discarded, not saved); chair
  injects a fact; the tagged seat (if named) or else the last seat that spoke resumes, marks
  `⟲ UPDATED <- CHAIR`, folds in the new fact, and re-comments; Gap-Hunter THEN re-selects any
  other seat the new fact now affects; already-spoken seats are re-called only if Gap-Hunter
  deems the fact material to them. ESC during the parallel Round 1 opening -> openers are
  re-issued, then the loop proceeds to Round 2.
- One-to-one toggle: `one to one #n` -> `manifest.mode: one_to_one:n`, all other seats paused,
  the exchange saved to `sidebars/chair-with-<n>.md`; `team deliberation` -> resume, and a
  SIDEBAR SUMMARY (new facts + seat #n's position changes) is injected into `transcript.md` as
  a first-class entry visible to all seats — the raw 1:1 chat stays in the sidebar file only.
- Chair authority is procedural, NEVER evidentiary, in team deliberation AND in 1:1: seats
  update their position only on new FACTS, never capitulate to chair OPINION (e.g. "I like this
  deal" moves nothing). Confidence stays hidden between agents mid-debate; the loop never
  terminates on consensus; dissent is preserved through to the memo, not smoothed over.

**Out-of-scope:** resume/autopilot (D3); the moderator loop mechanics + Round 1 opener
persistence (D1, which now also reflects the Advocate's (#9) round-flow turn — this slice owns
the tally/Gap-Hunter/menu/ESC/1:1/exclude-include logic that D1's dispatch loop hooks into).

**Allowed files/contexts:** `scripts/tally.py`; SKILL.md Mode B chair-handling block;
READ-ONLY: `transcript.md`, turn JSONs, spec §UX + FR-M11..14 + FR-S6/S7, dr2
`consensus_check.py`, domain-lattice `method-justification-forcing`.

**Step-by-step:**
1. `tally.py`: pure Python; answers only mechanical questions (responded? majority/veto?
   stagnation?); NEVER declares a verdict and NEVER terminates a round on "all agree"; hides
   numeric confidence between agents.
2. Enforce the Turn stance schema; render `⟲ UPDATED` on reversals; require
   `would_change_mind_if`; implement Gap-Hunter's (#10) per-round speaker selection, respecting
   the session's active roster (exclude/include); implement the Deal Advocate's (#9)
   mitigant-turn handling against the same falsification gate as objections.
3. Implement the round-boundary pause + chair menu (`Continue · /call <n> · /challenge <n>
   <claim> · /ask <n[,n]> <q> · /vote · /premortem · one to one #n · exclude #n[, #n ...] ·
   include only #n[, ...] · /end`) with by-number seat addressing and a plain-English fallback.
4. Implement `exclude #n[, #n ...]` / `include only #n[, ...]`: update `manifest.yaml`
   `active_seats` (session start OR mid-session); Gap-Hunter (#10) skips excluded seats and
   never opens them; on exclusion, Gap-Hunter logs what coverage is left unowned that session.
5. Implement ESC mid-turn interject (abort in-flight turn, chair fact injection, tagged/last
   seat resumes with `⟲ UPDATED <- CHAIR`, Gap-Hunter re-selection of affected seats, Round-1
   re-issue-then-Round-2 special case).
6. Implement the one-to-one toggle (sidebar file, paused main seats, sidebar-summary
   re-injection into `transcript.md` on return to team deliberation).

**Definition of Done:**
- Artifacts: `scripts/tally.py`; SKILL.md chair block; a fixture round showing Gap-Hunter
  seat selection, a Deal Advocate (#9) mitigant-turn example, a chair menu interaction, an
  exclude/include active-roster example (incl. Gap-Hunter's uncovered-risk log line), an ESC
  interject with `⟲ UPDATED <- CHAIR`, and a one-to-one sidebar round-trip with sidebar-summary
  injection.
- Validation: tally never emits a verdict and never terminates on consensus (or stagnation);
  every turn conforms to the stance schema; Gap-Hunter silences seats with nothing material and
  never selects an excluded seat; excluding a seat logs what coverage is left unowned that
  session; the Deal Advocate's (#9) mitigants clear the same falsification gate as objections
  (survive -> downgrade severity, refuted -> discarded) and the Advocate is never counted in the
  tally; the chair menu matches the canonical vocabulary (incl. exclude/include); ESC discards
  the in-flight turn and resumes correctly; chair opinion carries no evidentiary weight in team
  OR 1:1 mode (seat prompts unchanged by chair stance); the 1:1 sidebar stays private but its
  outcome (sidebar summary) is transparent to all seats on return.
- Evidence bundle: tally transcript + Gap-Hunter selection example + a Deal Advocate mitigant
  example + an exclude/include roster example + an ESC-interject `⟲ UPDATED <- CHAIR` example +
  a one-to-one sidebar round-trip example.

## Dev (Executor)

**Execution notes:** the tally is mechanical ONLY; argument-quality judgment stays with the
LLM but the tally never decides. The round-boundary menu and ESC interject are both called by
the main conversation (never a subagent). subscription-only.

**Evidence Bundle:** 1) Summary; 2) Traceability (FR-M11, FR-M12, FR-M13, FR-M14, FR-M21); 3)
Quality (stance-schema conformance; menu-vocabulary conformance; active-roster
exclude/include conformance); 4) Testing (tally + Gap-Hunter + Advocate mitigant +
exclude/include + ESC-interject + one-to-one transcripts); 5) Compliance (no
consensus-termination; procedural-only chair, incl. in 1:1; Advocate non-voting enforced); 6)
Operational; 7) Self-assessment.

## QA (Zero-Trust Verifier)

Verify: (a) grep `tally.py` to confirm it NEVER outputs a verdict and NEVER short-circuits on
unanimity or stagnation (recompute the tally by hand on a fixture); (b) confirm every turn
matches the stance schema and reversals show `⟲ UPDATED`; (c) confirm Gap-Hunter silences seats
with nothing material and re-selects correctly after an ESC interject; (d) trigger an ESC
interject mid-turn and confirm the in-flight turn is discarded (not saved), the correct seat
resumes and marks `⟲ UPDATED <- CHAIR`, and a Round-1 ESC re-issues openers before Round 2; (e)
confirm the round-boundary menu matches the canonical vocabulary and seats are addressable by
number; (f) toggle one-to-one and confirm other seats pause, the raw chat lands only in
`sidebars/chair-with-<n>.md`, and a sidebar summary (not the raw chat) is injected into
`transcript.md` on return; (g) confirm a chair "I like this deal" (team OR 1:1) does not raise
any claim's grade; (h) confirm `exclude #n[, #n ...]` / `include only #n[, ...]` correctly set
`manifest.yaml` `active_seats` at session start AND mid-session, that Gap-Hunter never selects
an excluded seat and the excluded seat never opens, and that Gap-Hunter logs what coverage is
left unowned when a seat is excluded; (i) confirm the Deal Advocate's (#9) mitigant turns are
graded through the SAME falsification gate as objections (recompute — a surviving mitigant
downgrades the objection's severity, a refuted one is discarded) and that the Advocate casts no
scrutiny vote and never appears in the tally. Reject on consensus-termination, schema violation,
capitulation-to-chair, a lost/duplicated ESC turn, sidebar-privacy leakage (raw 1:1 chat
appearing in the main transcript), an excluded seat being selected or opened, a missing
Gap-Hunter uncovered-risk log line on exclusion, an Advocate mitigant bypassing the
falsification gate, or the Advocate appearing in any vote count.

**Evidence gates:** mechanical-only tally; stance-schema conformance; Gap-Hunter selection
correctness; ESC interject discard+resume+re-selection; chair-menu conformance; no
capitulation; chair non-evidentiary (team + 1:1); sidebar privacy with transparent outcome;
active-roster exclude/include correctness with uncovered-risk logging; Advocate mitigant
falsification-gate parity; Advocate non-voting enforcement.

## Dev Learnings
_(fill: consensus_check reuse; justification-forcing enforcement; ESC interject state-machine
edge cases; sidebar round-trip gotchas; Advocate mitigant-vs-objection grading parity;
exclude/include roster edge cases — e.g. mid-session exclusion of an already-open seat,
uncovered-risk logging.)_

## QA Learnings
_(fill: capitulation-to-chair caught; any consensus short-circuit; ESC race conditions; sidebar
leakage checks; Advocate falsification-gate bypass attempts caught; excluded-seat
selection/opening attempts caught.)_
