# SLICE-D1-moderator-loop-transcript — Mode B moderator loop + append-only transcript

**Parent story:** STORY-D1 · **Epic:** EPIC-D · **Effort:** L · **Demo:** Demo 3
**slice.yaml mapping:** Objective->`objective`; Allowed files->`files_allowed`;
DoD+evidence gates->`acceptance_criteria`; QA verification->`verification_method`.

## PM (Planner / LCE brief)

**Objective (single, narrow):** Implement the Mode B moderated-relay loop **in the top-level
SKILL.md (main conversation)** — the main conversation IS the moderator; subagents cannot pause
or call `AskUserQuestion`, so no dispatched seat may own the loop — blind openings, then bounded
Gap-Hunter-directed (#10) rebuttal rounds (cap 5-6) — including the Deal Advocate's (#9) defense
turns when called — with every turn persisted to an append-only transcript on disk IMMEDIATELY
(survives `/clear` + resume) BEFORE the next dispatch.

**In-scope:** the SKILL.md Mode B branch that dispatches implicated seats per round via
`Task()` — for Rounds 2+, "implicated" means Gap-Hunter's (#10) per-round selection (owned by
D2), including calling on the Deal Advocate (#9) to respond when scrutiny seats raise an
objection — persists each `Turn` to disk, appends the human-readable render to `transcript.md`,
updates `manifest.status`/`manifest.current_round`, and enforces the round cap +
rolling-synthesis + last-K verbatim context window — against the canonical on-disk session
layout `.acos/investment-committee/<session>/`:
- `manifest.yaml` — `mode: deliberation|one_to_one:<n>`, `status: open|paused|closed`,
  `current_round`.
- `transcript.md` — append-only, human-readable.
- `rounds/round-NN/*.json` — one file per seat turn for that round.
- `sidebars/`, `ledger/`, `evidence/`.

Round numbering: **Round 1** = the blind parallel TWO-LINE opener pass per seat (line 1: number
of gaps found + why the chair should care; line 2: overall recommendation), rendered
one-line-per-seat in `transcript.md`. **Rounds 2+** = serial rebuttal turns among the seats
Gap-Hunter (#10) selects that round — including the Deal Advocate (#9) when called to defend
against an objection just raised — each conforming to the per-turn JSON schema `{round, seat,
stance: SUPPORT|REBUT|ABSTAIN|CONDITIONAL|FLAG_RISK, argument (≤250w), addresses_prior_turn_ids,
would_change_mind_if}`. The Advocate's turns use the same schema and pipeline as any other seat
— no vote, no separate persistence path — but content-wise carry a mitigant claim that must
clear the same falsification gate as an objection (owned by D2's tally/grading, not this
slice).

**Out-of-scope:** the two-line opener prompt/dispatch mechanics themselves (owned by B2 — this
slice consumes Round 1's output and persists/renders it); the tally + chair vocab, Gap-Hunter's
(#10) selection logic, the Advocate's (#9) falsification-gate grading, and the exclude/include
active-roster commands (all D2); resume (D3); the verdict (reuses C3).

**Allowed files/contexts:** `.claude/skills/acos-investment-committee/SKILL.md` (Mode B
branch); `scripts/transcript_append.py`; READ-ONLY: `manifest.yaml`, `seats/*.md`,
`blind_openings.py`, tech_prd §1.7 + §2, domain-lattice `proc-mode-b` +
`pattern-main-convo-moderator` + `pattern-transcript-on-disk`.

**Step-by-step:**
1. In SKILL.md, render Round 1's blind two-line openers (one line per seat) into
   `transcript.md`, then enter the round loop (main conversation owns it — NO nested moderator
   agent; dispatched seats cannot call `AskUserQuestion` or otherwise pause the loop).
2. Per round 2+: dispatch the seats Gap-Hunter (#10) selects via `Task()` — including the Deal
   Advocate (#9) when called to respond to an objection raised that round — write each returned
   Turn to `rounds/round-NN/*.json` (one file per seat turn) immediately; append to
   `transcript.md`; bump `manifest.current_round`.
3. Enforce round cap; use rolling synthesis + last-K verbatim to bound per-call cost.

**Definition of Done:**
- Artifacts: SKILL.md Mode B branch; `scripts/transcript_append.py`; a fixture `transcript.md`
  + `rounds/round-NN/*.json` including at least one Deal Advocate (#9) defense turn.
- Validation: the moderator loop lives in the main conversation (no spawned agent calls the
  loop, and no subagent invokes `AskUserQuestion`); every turn is on disk before the next
  dispatch (durability); round cap enforced; the transcript render matches the per-turn JSON
  records, including the Round 1 one-line-per-seat opener render; the seats dispatched each
  round match Gap-Hunter's (#10) selection, including Advocate (#9) turns when called.
- Evidence bundle: a multi-round fixture run transcript (incl. an Advocate turn) + a durability
  proof (kill after a turn -> turn already on disk).

## Dev (Executor)

**Execution notes:** ONLY the main conversation moderates (subagents can't pause or call
`AskUserQuestion`). Disk-first is load-bearing for resume. subscription-only. Respect
Oracle/check-scope hooks. The per-round seat list (including whether the Advocate is called) is
an EXTERNAL input to this slice's dispatch loop, not computed here — do not hardcode which
seats speak.

**Evidence Bundle:** 1) Summary; 2) Traceability (FR-M9, FR-M10, NFR-6); 3) Quality (transcript
== JSON consistency); 4) Testing (multi-round transcript + mid-turn kill durability); 5)
Compliance (no nested moderator; subscription-only); 6) Operational (round cap, context
window); 7) Self-assessment.

## QA (Zero-Trust Verifier)

Verify: (a) confirm the loop is in SKILL.md and NO spawned agent owns the round loop
(architecture check — grep for a moderator Task()); (b) after each turn, confirm the JSON
exists on disk BEFORE the next dispatch (interrupt mid-round and confirm the last turn
survived); (c) confirm `transcript.md` render is faithful to the JSON records (recompute),
including the Round 1 two-line opener render; (d) confirm the round cap halts the loop; (e)
confirm a Deal Advocate (#9) turn, when Gap-Hunter (#10) calls on it, persists and renders
through the IDENTICAL Turn schema/pipeline as any scrutiny seat's turn (no bespoke
advocate-only code path) and that the dispatch loop never treats the Advocate as an
"implicated" scrutiny seat on its own. Reject if the moderator is nested, a turn is lost on
interrupt, a subagent is found calling `AskUserQuestion`, or an Advocate turn is handled via a
special-cased path.

**Evidence gates:** main-convo moderator; disk-first durability; transcript==JSON; round cap
enforced; no subagent AskUserQuestion calls; Advocate turns share the standard Turn
persistence/render pipeline.

## Dev Learnings
_(fill: main-convo loop structure; rolling-synthesis context tuning; wiring an externally
supplied per-round seat list, incl. Advocate calls, without hardcoding.)_

## QA Learnings
_(fill: durability interrupt test; any transcript/JSON drift; any Advocate-turn special-casing
found.)_
