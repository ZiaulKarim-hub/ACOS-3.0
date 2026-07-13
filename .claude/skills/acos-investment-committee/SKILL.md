---
name: acos-investment-committee
description: Adversarial multi-seat investment-committee review of a real-estate lending deal — a fixed panel of complementary-discipline expert seats produces independence-first objections, fused deterministically via a vendored axiom-synthesis engine, into a 13-section IC memo with a computed (never narrated) PROCEED/PROCEED-WITH-CONDITIONS/DECLINE/UNRESOLVED verdict.
user-invocable: true
argument-hint: "[deal-folder] [--mode A|B] [--seats lean|full]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task
---

# ACOS Investment Committee

**Mode A is wired and runnable.** This SKILL.md establishes the pre-flight guarantees,
the on-disk session layout, the vendored synthesis engine, and the full **Mode A**
dispatch loop (blind opening pass → fact-builder → fuse → deterministic verdict → 13-section
memo). **Mode B** (live browser-chaired meeting) is now BUILT — see "Mode B — chaired meeting engine" below and `scripts/committee-room/ic-server.py`. The **Deal Advocate seat is retired**; each seat proposes its own `suggested_mitigants` inline, and every objection now leads with a `question` (Question → context → suggested mitigant). See
`diagnostics.md` for the diagnosed problem (D1–D6) this skill exists to solve, and
`planning/preeng/003-investment-committee/{spec.md,tech_prd.md}` for the full design.

## Overview

The Investment Committee skill runs a fixed panel of complementary-discipline expert
seats over a deal dataroom, each producing an independence-first, falsifiable
objection. Objections are fused through a **vendored, standalone copy** of the
`acos-axiom-synthesis` engine (`scripts/synthesis/` — see `scripts/synthesis/VENDORED_FROM.md`
for provenance) into a hash-chained claim ledger. The overall verdict is **computed**
deterministically from that ledger (never narrated by an LLM) and rendered into a
13-section IC memo.

Two modes:
- **Mode A — synthesized memo.** Seats run blind in parallel; the vendored engine
  fuses; a memo + deterministic verdict are rendered. Fast, cheap, default.
- **Mode B — live deliberation.** Blind openings, then bounded adversarial rebuttal
  rounds with a human chair, ending in the same synthesis + verdict pipeline as
  Mode A. Opt-in, higher cost.

## Pre-flight

Before any dispatch, in either mode:

1. **Autopilot assertion (F1 stub, hardened later).** `test -f
   .acos/state/autopilot-active` → if present, **ABORT immediately** with a clear
   message instructing the user to disable autopilot manually before invoking the
   Investment Committee. **No fallback branch.** Implemented today as
   `scripts/session_scaffold.py --autopilot-check` (and as the unconditional
   pre-check inside every `session_scaffold.py` invocation).
2. **Session scaffold.** `python3 scripts/session_scaffold.py --session-id
   <session-id> [--deal <path>]` deterministically creates
   `.acos/investment-committee/<session-id>/` with the full canonical subtree
   (`manifest.yaml`, `transcript.md`, `rounds/`, `sidebars/`, `ledger/`,
   `evidence/`). Idempotent — re-running the same session-id is a no-op diff.
3. **Vendored-engine smoke check.** The synthesis engine vendored at
   `scripts/synthesis/` must be intact before any seat is dispatched. Verify via:
   ```bash
   S=.claude/skills/acos-investment-committee/scripts/synthesis
   PYTHONPATH="$S" python3 "$S/tests/test_substrate.py"   # 19 assertions
   PYTHONPATH="$S" python3 "$S/tests/test_pipeline.py"    # 35 assertions
   ```
   Both must exit 0. See `WAVE0-smoke-report.md` for the recorded Wave-0 run.

## Modes

### Mode A — synthesized memo (wired)

Mode A is the default. The main conversation acts as the **moderator**: it runs the
deterministic front-end scripts, dispatches the expert seats blind and in parallel via
`Task()`, then drives the deterministic synthesis → verdict → memo chain. The moderator
never grades a claim or narrates the verdict — those are computed by the vendored engine
and `verdict.py`.

**Step 1 — front-end (deterministic scripts, in this order):**
```bash
SK=.claude/skills/acos-investment-committee        # run from project root
SID=<session-id>                                    # e.g. the deal name, slugified
SESS="$SK/.acos/investment-committee/$SID"
python3 "$SK/scripts/session_scaffold.py" --session-id "$SID" --deal <deal-folder>   # aborts if autopilot-active
python3 "$SK/scripts/extract_deal.py"     --deal <deal-folder> --session "$SESS"     # -> deal-brief/deal-brief.yaml (+ evidence-index)
python3 "$SK/scripts/resolve_roster.py"   --session "$SESS" --seats lean             # -> manifest active_seats [+ --exclude/--include]
mkdir -p "$SESS/rounds/round-01"
```
Read `active_seats` and the voting set from `$SESS/manifest.yaml`. The **scrutiny seats**
are the voting members (#1–#8 plus any triggered scrutiny optionals #11–#15); the
**Deal Advocate (#9)** is non-voting defense; the **Gap-Hunter (#10)** is procedural and
raises no objections in Mode A.

**Step 2 — blind opening pass (parallel `Task()` dispatch):**
Spawn every active **scrutiny** seat SIMULTANEOUSLY (one message, N `Task()` calls) so no
seat sees another's work — independence-first is mechanical here. Give each seat the path
to `deal-brief/deal-brief.yaml` (and the evidence dir) and the exact output path
`rounds/round-01/seat-NN.json`. Each seat emits the pinned wrapper JSON
(`{seat, seat_name, role_family, objections[], mitigants:[]}`) its agent def specifies.
Because seat agents may not have Write in every harness, the robust pattern is: each seat
**returns** its `seat-NN.json` content as its final message and the moderator writes the
file (this also lets the moderator validate each before proceeding).

**Step 3 — advocate pass (after objections exist):**
Once all scrutiny `seat-NN.json` files are written, dispatch **#9 Deal Advocate** with the
brief AND the collected objection IDs + statements. It returns `seat-09.json` with
`objections: []` and a `mitigants[]` list, each entry `retires_objection_id`-linked to a
real objection. (The two-pass `build_facts.py` needs every objection present before it reads
mitigants, so the advocate runs second.)

**Step 3.5 — falsification refuter pass (the different-discipline gate):**
Before synthesis, challenge every mitigant that attaches to a **material-or-worse** objection:
spawn a `Task()` refuter of a DIFFERENT discipline than the mitigant's author, asking *"does
this mitigant actually cure the objection NOW, or is it a deferral / promise / conjecture?"*.
Collect the verdicts and write them to `rounds/round-01/refuters.json`:
```json
{ "<mitigant_fact_id>": {"objection": "<why the cure fails / is deferred>",
                          "credible": true, "rebutted": false} }
```
`build_facts.py` applies this map onto the matching fact's `refuter` field. The vendored
falsify gate downgrades a `credible && !rebutted` mitigant one tier — a single-source
CORROBORATED "we'll obtain the document later" CP drops to **CONJECTURE**, so it can no longer
clear a deal-breaker it does not actually cure. A genuinely-curative condition (e.g. a title
policy that really does establish first-lien priority) is left un-refuted and correctly becomes
a Condition Precedent. Refuters may also challenge objections themselves — same map, keyed by
`objection_id`. This is the safeguard against an aspirational mitigant mechanically retiring a
structural risk.

**Step 4 — synthesis → verdict → memo (deterministic chain):**
```bash
python3 "$SK/scripts/build_facts.py"    --session "$SESS"   # objections+mitigants (+refuters.json) -> synthesis/facts.json, severity-map.json, mitigant-map.json
python3 "$SK/scripts/run_synthesis.py"  --session "$SESS"   # fuse via vendored engine -> ledger/claims.jsonl (hash-chained)
python3 "$SK/scripts/verdict.py"        --session "$SESS"   # deterministic asymmetric-veto verdict -> verdict.json
python3 "$SK/scripts/render_memo.py"    --session "$SESS"   # -> ic-memo.md (13 sections, Risk->Mitigant->Residual + CPs)
```
`build_facts.py` writes Axis-S severity to a **side-channel** (`severity-map.json`) that
never enters the engine's truth-grading. `verdict.py` reads the settled ledger + the
side-channel and computes PROCEED / PROCEED-WITH-CONDITIONS / DECLINE / UNRESOLVED by rule.
Present `ic-memo.md` and the verdict to the user.

> **SEAM (model-produced fields) — wired.** The per-fact `refuter` verdict is produced by the
> Step-3.5 refuter pass (moderator-spawned different-discipline `Task()` agents) and applied via
> `rounds/round-01/refuters.json`. `run_synthesis.py` rebuilds the ledger **fresh** on every
> invocation (it clears any prior `claims.jsonl` + `settled-objections.jsonl` first), so
> re-running is deterministic and the oscillation guard never mistakes this run's refuters for
> already-settled ones. The Stage-5 `flags` (hard/soft trigger detections) remain optional
> per-fact inputs defaulting to `{}` — populate them the same way when a hard trigger
> (fabrication, internal contradiction) is detected upstream.

### Mode B — live deliberation (wired)

Mode B keeps a **human chair** (the OKOA associate) in the loop across bounded adversarial
rounds. The **main conversation is the moderator** — because subagents cannot call
`AskUserQuestion`, the moderator is the only actor that talks to the chair; seats are dispatched
via `Task()` and never address the chair directly. Same pre-flight and same terminal
synthesis→verdict→memo pipeline as Mode A; only the middle (how objections are gathered) differs.

**Pre-flight:** identical to Mode A Step 1 (autopilot abort → scaffold → extract → resolve).
Set `mode: deliberation` in the manifest.

**Round 1 — blind parallel two-line openers.** Dispatch every active scrutiny seat + the Deal
Advocate SIMULTANEOUSLY (independence-first), each returning a **two-line opener** — its single
sharpest objection/mitigant — written to `rounds/round-01/seat-NN.json` (same wrapper schema;
one or two objections is fine for an opener). Then **PAUSE**: show the chair all openers and wait.

**Rounds 2+ — Gap-Hunter-directed.** Spawn **#10 Gap-Hunter** with the transcript-so-far; it
returns an ordered speaker list + rationale (who has an unanswered objection, what risk is
uncovered). The moderator dispatches those seats (each now sees the transcript and uses the
stance vocabulary SUPPORT | REBUT | ABSTAIN | CONDITIONAL | FLAG_RISK, naming the turns it
addresses), writing `rounds/round-NN/seat-MM.json`. **PAUSE after EVERY round.**

**Chair controls** (what the chair may type at any pause):
- `next` — proceed; Gap-Hunter picks the next speakers.
- `speak #n` — call seat #n next specifically.
- `exclude #n` / `include #n` — adjust the roster (`resolve_roster.py --exclude/--include`); the
  drop is logged to the gap-log so what it leaves uncovered is on the record.
- `sidebar #n` — enter a private one-to-one with seat #n (dispatched with a `sidebars/` scratch
  channel the other seats never see); on return the moderator posts a transparent **SIDEBAR
  SUMMARY** into the transcript so the record stays complete.
- `fact: <text>` — inject a fact. It is weighed as a **CLAIM, not accepted as truth**: it is
  folded into the next dispatch for a seat to adopt *with evidence*, and graded like any other.
- `tally` — interim verdict: run `build_facts.py --round all` → `run_synthesis.py` →
  `verdict.py` and show the CURRENT computed verdict. Does **not** end the session.
- `verdict` / `close` — terminate (below).
- **ESC** — interject mid-turn: abort the in-flight seat turn, fold in the chair's input, resume
  with the tagged (or last) seat.

**Chair-input doctrine — the seats bring the evidence, not the chair (FR-M13, revised 2026-07-13).**
The chair directs *who speaks* and *the roster*, and the deterministic verdict is never overridden by the
chair — but the burden of proof for contesting a chair input sits on the **seats**, not the chair.
Diligence is the panel's job. When the chair states a number or input, a seat may NOT demand the chair
prove it. Instead: **(a)** if the seat's documents or research bots give it evidence that *contradicts*
the input, it challenges — citing that evidence and asking the refinement question ("my comp/appraisal
shows Y against your X — is X documented, or your own verification?"); **(b)** absent contradicting
evidence, the seat *accepts the input as a working assumption*, updates, and logs it as a condition "to
be confirmed by [document]" — not a veto (unverified ≠ disqualifying); **(c)** a hopeful *projection* and
a firm *input* are both accepted-unless-contradicted, with genuine uncertainty surfaced as a CP rather
than a reflexive push-back. A chair **personal assurance** ("I verified X myself / I hold a verbal
commitment") is the strongest form — evidence on the record — converting a live objection to a
`CP-verified-by-chair` (testimonial; reopens if a document later contradicts it; never clears a
Fraud/Misrepresentation kill on its own). Seats absorb every prior chair input as known context and
never make the chair repeat themselves. (The deterministic verdict still grades the settled ledger by
evidence; an uncontested chair input enters as a working assumption / CP, not as fiat truth.)

**Termination → same deterministic pipeline as Mode A.** On `verdict`/`close`: run the
**Step-3.5 refuter pass** over every mitigant attaching to a material-or-worse objection across
all rounds, then:
```bash
python3 "$SK/scripts/build_facts.py"   --session "$SESS" --round all   # each seat's LATEST turn wins; refuters merged across rounds
python3 "$SK/scripts/run_synthesis.py" --session "$SESS"               # fresh rebuild -> hash-chained ledger
python3 "$SK/scripts/verdict.py"       --session "$SESS"               # same asymmetric-veto verdict
python3 "$SK/scripts/render_memo.py"   --session "$SESS"               # -> ic-memo.md
```
`transcript.md` accumulates every round, chair action, and sidebar summary as the append-only
human-readable record alongside the machine ledger.

## Roster

The canonical roster is data in `roster.yaml` (+ `coverage-map.yaml` for the 16 risk
categories, `optional_triggers.yaml` for deal-triggered seats). Each seat is a registered
agent in `.claude/agents/ic-NN-*.md`. Stable numbering — never renumber beyond `roster.yaml`.

**Scrutiny seats (voting, hole-hunters):**
- **#1 Credit & Valuation** — LTV, DSCR, comps, cap-rate; collateral-value + repayment-capacity sub-passes.
- **#2 Finance** — spread, lender-IRR, capital structure; core-owns Interest-Rate/Refi/Exit.
- **#3 Accounting** — QoE / GAAP / add-backs; **OWNS the single normalized-NOI claim** (the fraud tripwire consumed by #1 and #2).
- **#4 Legal & Structural** — title, lien, SPE, guaranty; + a scoped environmental-legal sub-lens (CERCLA/Phase I currency).
- **#5 Insurance & Climate** — non-renewal / premium-spike risk that breaks DSCR; merged physical-climate lens.
- **#6 Sponsor & Fraud-Forensics** — track-record, litigation, cross-document fabrication; assume fabricated until corroborated.
- **#7 Portfolio & Concentration** — **FUND-scoped** (reads the fund loan tape): sponsor / geo / type / maturity concentration.
- **#8 Strategy** — thesis-fit, opportunity-cost, off-mandate; must produce a falsifiable objection or abstain (not an advocate).

**Non-voting seats:**
- **#9 Deal Advocate** — defense role; steelmans the deal and answers objections with the best
  good-faith mitigant the evidence supports. Mitigants pass the SAME falsification gate as
  objections. Mechanically asserted never to appear in a scrutiny tally (`resolve_roster.py`).
- **#10 Gap-Hunter / Chair-agent** — procedural; picks speakers in Mode B rounds 2+, logs what
  roster exclusions leave uncovered. Raises no objections in Mode A.

**Deal-triggered optionals (#11–#15):** Construction/Completion, Tax, Market/Macro,
Compliance/Regulatory, Environmental/Physical-Condition — promoted from a core seat's fold-in
when `optional_triggers.yaml` fires. `lean` roster = #1–#10; `full` = + all triggered optionals.

**Chair (human)** — the OKOA associate/analyst; procedural authority (FR-M13). Chair input is
*accepted as a working assumption unless a seat has evidence that contradicts it* — the burden of proof
sits on the seats (diligence is their job), not on the chair; a seat challenges only with contradicting
evidence, else it logs the input as a "to-be-confirmed" condition. A genuine personal **assurance**
(vouching/attesting from own verification) is evidence on the record → `CP-verified-by-chair`
(testimonial, still falsifiable; never clears a fraud kill). See the full chair-input doctrine above.

## Guardrails (F1) & Legal reuse (E1)

**Independence-first (mechanical, not policy).** Scrutiny seats form their openings in a single
parallel `Task()` dispatch, so no seat can see another's work before committing — the wall is
enforced by dispatch structure, not instructions.

**Autopilot pre-flight ABORT.** `session_scaffold.py` refuses to scaffold if
`.acos/state/autopilot-active` exists (and `--autopilot-check` runs the assertion alone). There
is no autonomous-fallback branch — a live committee requires a present human chair.

**Kill-criteria (un-mitigable veto).** `verdict.py` treats a CORROBORATED objection whose `covers`
intersects `_KILL_CATEGORIES` (default `Fraud/Misrepresentation`) as un-mitigable: it vetoes even
if a mitigant reached CORROBORATED. Documentation gaps are curable by conditions precedent;
fabrication is not. Surfaced as `kill_findings` in `verdict.json` and the DECLINE rationale.

**Per-run conflicts / independence disclosure.** `emit_disclosure.py --session <SESS>` stamps
`<session>/conflicts-disclosure.yaml` — AI-financial-interest attestation, the voting vs.
non-voting roster, excluded seats, and the kill-categories in force — for the chair to countersign.
Run it once per committee session (any time after `resolve_roster.py`).

**Deep legal diligence (E1).** The Legal & Structural seat (#4) runs a scoped review and flags
promotions. For a full legal-risk memo (title/lien/SPE/guaranty/foreclosure mechanics, or IP), the
moderator can invoke the existing **`/acos-legal-analysis`** skill (the `legal-analyst` agent) on
the same deal folder and fold its cited findings back in as seat-#4 (or optional #12/#14) evidence
— reuse, not a re-implementation. Diligence support only; **not** legal or investment advice.

## Diagnostics

See `diagnostics.md` for the full D1–D6 symptom → requirement trace this skill is
built to address.

## Mode B — chaired meeting engine (BUILT 2026-07-10)

A real browser-chaired committee meeting. The **main conversation is the moderator/engine** (only
it can dispatch `Task()` seats); the **browser is the chair's cockpit**, bridged by
`scripts/committee-room/ic-server.py` (stdlib SSE + `chair-inbox.jsonl` + blocking-tail — a port of
acos-guided-reader's gr-server). No Deal Advocate; each seat proposes its own `suggested_mitigants`.

**Pre-flight:** identical to Mode A (autopilot abort → scaffold → extract → resolve). `mode: deliberation`.

**1. Blind openings.** Dispatch every active scrutiny seat SIMULTANEOUSLY (independence-first). Each
returns `seat-NN.json` in the **Question → Context → suggested_mitigants** schema.

**2. Committee Briefing + launch the engine (decoupled from the main conversation).** Synthesize every
seat's sharpest question + top mitigant into one briefing doc (shown in the room sidebar), then start the
whole live engine via **`ic-launch.sh`** — the warm **`claude -p` pool** (`ic-pool.py --safe-mode`, no API
key — removes the moderator from the live loop, ~5-7s turns) + the **`ic-live.py`** consumer (routes each
chair `speak` → pool with a grounded, in-voice, doctrine-following prompt) + **`ic-server.py`** (serves +
SSE-broadcasts the room, opens Chrome). All three are independent daemons, so **chatting in the main
conversation never stops the committee** — that decoupling is what the pool buys you, tab or no tab:
```bash
CR=.claude/skills/acos-investment-committee/scripts/committee-room
CRABS="$(cd "$CR" && pwd)"; SESSABS="$(cd "$SESS" && pwd)"
python3 "$CR/build_meeting.py" --session "$SESS" --out "$CR/meeting.html"        # briefing + arc + state
bash "$CR/ic-launch.sh" "$SESSABS" 8930 &                                        # engine as background daemons (proven)
```
**To run it in its OWN cmux tab (visible, self-contained):** the `cmux new-workspace` CLI only works from a
FOCUSED cmux surface. Run from the Claude session's own subprocess it fails with `TabManager not available`
(`identify` shows `caller:null`), and raw `cmux rpc workspace.create` makes a *disconnected* workspace with
no terminal — so the moderator CANNOT reliably open the tab itself. Instead hand the chair this one line to
paste into THEIR terminal (e.g. via the `!` prefix), where their shell IS the focused surface:
```
cmux new-workspace --name "IC — <deal>" --cwd "<CRABS>" --command "bash ./ic-launch.sh '<SESSABS>' 8930"
```
`ic-launch.sh`'s EXIT trap tears the engine down when that tab closes. (The old inline `ic-server.py &` +
moderator-generates-each-turn path still works but is slower and pins the main session — prefer the pool.)

**3. Chaired rounds — the chair controls the floor.** Loop until the chair closes:
- **Wait for the chair** at zero token cost: `EVENT=$(tail -n 0 -f "$SESS/chair-inbox.jsonl" | head -1)`
  (re-arm past the Bash 600s cap). Or drain queued commands: `python3 "$CR/meeting_state.py" inbox --session "$SESS"`.
- Parse the command: `speak #n` | `next` | `message` | `tally` | `close`.
- **Fresh per-turn generation:** dispatch the called seat via `Task(ic-0N)` WITH the transcript-so-far
  (+ any chair message); it returns a fresh spoken turn reacting to the latest discussion. Push it live:
  ```bash
  python3 "$CR/meeting_state.py" add-turn --session "$SESS" --seat N --name "…" --short "…" --text "…"
  python3 scripts/transcript_append.py    --session "$SESS" --who "…" --text "…"
  ```
- **Reactions + hands:** compute each other seat's evolving, non-face reaction emoji (👍👎❤️💩🤔🔥💯)
  and which seats raise a hand, then push — `ic-server.py`'s watcher broadcasts each change over SSE:
  ```bash
  python3 "$CR/meeting_state.py" reactions --session "$SESS" --json '{"1":"👍","5":"🤔"}'
  python3 "$CR/meeting_state.py" hands     --session "$SESS" --seats 3,6
  ```
- `tally` → `python3 scripts/tally.py --session "$SESS"` (interim verdict; does not end the meeting).

**3b. Autonomous meeting engine (`ic-meeting-runner.py`) — the "real meeting" feel.** The root cause
of the old slowness: in live mode nothing advanced the meeting except the moderator LLM pushing a turn
inside a response, so every turn waited minutes on a human-in-the-render-loop (the mechanical pipeline
is <100ms; generation-coupled-to-the-moderator was the bottleneck). The fix DECOUPLES playback from
generation: build the deliberation UP FRONT, then a runner plays it at natural cadence while the chair
steers. Live generation is needed only for genuinely-novel chair arguments.
- **Pre-build the script (one batch, not turn-by-turn).** After the blind openings, the moderator
  composes the whole arc in-voice from the seat objections — openings → cross-talk → chair challenge →
  rebuttals → close — as `<SESS>/meeting-script.json`: `{pace:{per_word_ms,react_ms,gap_ms}, beats:[{seat,
  name,short,text,reactions,hands}], closing:{…}}`. Chair beats use `seat:0`.
- **Run it:** `python3 "$CR/ic-meeting-runner.py" --session "$SESS" [--speed 1.0] &` (sole consumer of
  `chair-inbox.jsonl`; subsumes `ic-turn-daemon.py`). It auto-advances one beat at a time, pacing each
  by `words·per_word_ms + react_ms + gap_ms` (matched to the client's ~135ms/word typewriter so the next
  turn never interrupts the current one; ≈370 wpm reading pace, ~4-min meeting). Reactions **trickle in**
  during each turn and hands raise a beat in (client-side stagger in `playEvent`) — the room feels alive.
- **Chair steering (live, no waiting):** `pause`/`hold` freezes on the current speaker; `play`/`resume`/
  `next` resumes; `speak #n` (bare) jumps to seat n's next scripted beat NOW (or serves its `ic_turns`
  cache); `close`/`verdict` plays the closing beat and stops.
- **Novel chair argument (the only path that needs the model):** `speak #n` WITH a new argument can't be
  pre-answered — the runner sets the `thinking` state (seat types instantly) and drops
  `turn-cache/PENDING.json`; the moderator generates that one fresh turn, pushes it, and the meeting
  resumes. `ic_turns.py`/`ic-turn-daemon.py` remain for the pure chair-steered (non-autoplay) style.

**4. Close → verdict (same deterministic chain as Mode A).** On `close`:
`build_facts.py --round all → run_synthesis.py → verdict.py → render_memo.py`. Mitigants are gathered
from each objection's inline `suggested_mitigants` (Advocate retired). `transcript.md` is the append-only
human record; `resume.py` rebuilds `meeting-state.json` from disk to resume after a `/clear`.
