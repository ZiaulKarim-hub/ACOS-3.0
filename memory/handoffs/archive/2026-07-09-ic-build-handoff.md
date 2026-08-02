---
title: acos-investment-committee — mid-build handoff (Waves 0–2 done, harmonization fix pending)
date: 2026-07-09
status: "completed"
project: acos-investment-committee skill build
---

# HANDOFF — Building the `acos-investment-committee` skill

## What this is
Building a brand-new ACOS skill: an adversarial multi-seat AI Investment Committee that
reviews a real-estate lending deal for OKOA. Planned via `/acos-preeng-classic` (plan at
`planning/preeng/003-investment-committee/`), researched via a 10-agent `/acos-swarm-research`
swarm (`.acos/swarm/swarm-20260707-141351/synthesis/report.md`). User wants it built fast with
agents and to EXPERIENCE using it. Build is being driven in dependency WAVES from the main
conversation, verifying each wave (recompute gates — DO NOT trust agent self-reports/logs).

## Final design (locked with user across the session)
- **Two modes:** A = synthesized IC memo (deterministic); B = live human-chaired deliberation.
- **Roster (STABLE numbers):** #1 Credit&Valuation, #2 Finance, #3 Accounting (OWNS the single
  normalized-NOI claim = fraud tripwire), #4 Legal&Structural (+env-legal sub-lens), #5
  Insurance&Climate, #6 Sponsor&Fraud-Forensics, #7 Portfolio&Concentration (FUND-scoped),
  #8 Strategy, **#9 Deal Advocate (defense role, NON-voting, mitigants pass same falsification
  gate)**, **#10 Gap-Hunter/Chair-agent (procedural, non-voting, picks speakers each round)**,
  #11–15 deal-triggered optionals (Construction, Tax, Market/Macro, Compliance, Environmental/
  Physical). Exit/Refi folded into Finance (#2), NOT an optional.
- **Standalone:** VENDORS a private copy of acos-axiom-synthesis (no runtime dependency).
- **Axis S (severity):** domain-owned side-channel (informational<limitation<material-risk<
  deal-breaker-candidate), ORTHOGONAL to the engine's truth-grading — never blended.
- **Deterministic verdict:** asymmetric-veto on deal-breakers → PROCEED / PROCEED-WITH-
  CONDITIONS / DECLINE / UNRESOLVED. Never LLM-narrated.
- **Mode B specifics:** main conversation is the moderator (subagents can't AskUserQuestion);
  Round 1 = blind parallel TWO-LINE openers; Rounds 2+ = Gap-Hunter picks speakers; pause after
  EVERY round; ESC interject anytime (abort turn, resume with tagged-or-last seat, fold in fact);
  one-to-one #n ⇄ team toggle (private channel `sidebars/`, transparent SIDEBAR SUMMARY on
  resume); chair authority procedural-NOT-evidentiary; exclude/include roster command; autopilot
  must be OFF (pre-flight ABORT if `.acos/state/autopilot-active` exists — user guarantees off).
- **Shared extraction layer** (one pass, all seats read it) + **per-expert private swarms**
  (2–4 `Task(ic-research-bot)` bots each, sized to need, report only to their seat). ONE mode
  (always swarms, no quick/deep tiering).

## BUILD STATUS
### ✅ Wave 0 (VERIFIED by me): `.claude/skills/acos-investment-committee/`
- Vendored engine at `scripts/synthesis/{scripts,tests}/` — mirrors source layout EXACTLY so
  bare-name imports resolve. **Passes 54/54** (19 substrate + 35 pipeline) with standard
  invocation `python3 scripts/synthesis/tests/test_pipeline.py`. `VENDORED_FROM.md` records
  provenance. (I fixed a layout bug the build agent introduced — engine was nested wrong,
  tests threw ModuleNotFoundError; now correct.)
- `scripts/session_scaffold.py` — idempotent session dir + `--autopilot-check` (aborts if marker).
- `SKILL.md` skeleton (frontmatter valid, later-wave sections marked), `diagnostics.md`.

### ✅ Wave 1 (VERIFIED, incl. cross-script interop): 
- `roster.yaml` + `coverage-map.yaml` (A1) — 10 seats + optionals, 16 risk categories all owned.
- 11 agents in `.claude/agents/`: `ic-01-credit-valuation` … `ic-10-gap-hunter` + `ic-research-bot`
  (A2) — REGISTERED & spawnable. #1–9 have `Task(ic-research-bot)`; #10 no swarm; research-bot
  has web tools. #9 advocate = no-scrutiny-vote framing; #3 owns normalized-NOI.
- `scripts/resolve_roster.py` + `optional_triggers.yaml` (A3) — lean/full, exclude/include→
  `active_seats` in manifest + gap-log, HARD ASSERTION that #9/#10 never in voting_set. Tested.
- `scripts/extract_deal.py` + `fixtures/sample-deal/` (B1) — shared extraction → `deal-brief.yaml`
  (+ reserved `normalized_noi` slot owner:#3, value:null) + `evidence-index.yaml`. Idempotent.
- **INTEROP VERIFIED:** scaffold→extract→resolve pipeline runs end-to-end; A3 parses B1's REAL
  deal-brief.yaml (two hand-rolled stdlib YAML handlers interoperate).

### ✅ Wave 2 BUILT (self-tested 23/23) — but has ONE OPEN DEFECT (see NEXT STEP):
- `scripts/build_facts.py` (C1) — objection→axiom `fact` + `severity-map.json` (Axis S side-
  channel) + `mitigant-map.json`. Its header docstring (~lines 33–71) documents the EXACT
  per-seat JSON it consumes (wrapper `{seat,seat_name,role_family,objections[],mitigants[]}`,
  evidence as LIST of dicts).
- `scripts/run_synthesis.py` (C2) — puts `synthesis/scripts/` on sys.path, drives vendored
  `orchestrate.run()` → `ledger/claims.jsonl`. SEAM: `refuter`/`flags` are model-produced
  (filled upstream by Task-spawned different-discipline refuter in the live skill); stubbed
  None/{} for smoke.
- `scripts/verdict.py` (C3) — deterministic deal-breaker predicate + asymmetric-veto verdict.
  Smoke: unmitigated deal-breaker→DECLINE; add surviving mitigant→PROCEED-WITH-CONDITIONS.
- `scripts/render_memo.py` (C4) — 13-section IC memo, Risk→Mitigant→Residual triplet + CPs.
- `verify_ledger.py` passes (hash chain intact).

## ⚠️ IMMEDIATE NEXT STEP (do this FIRST): harmonization fix
**A contract mismatch exists** and its fix-agent DIED on an API error writing NOTHING (files
clean, verified). The seat agent defs (`ic-01..08` + `ic-09`) currently tell seats to emit a
LOOSE objection format (statement/falsifiable_form/axis_s/evidence:string/mitigant_hypothesis),
but `build_facts.py` (C1) requires the PRECISE JSON in its docstring (wrapper + evidence as list
of dicts). A real seat run would produce output C1 can't parse → Mode A breaks at first run.
**FIX (two-sided):**
1. Pin PRODUCERS: rewrite the "## Objection schema" + "## Output" sections of `ic-01..08` +
   `ic-09-deal-advocate` to emit EXACTLY the JSON `build_facts.py` parses, WITH a concrete worked
   example. Wrapper `{"seat":N,"seat_name":..,"role_family":..,"objections":[..],"mitigants":[..]}`
   → `<session>/rounds/round-01/seat-NN.json`. Each objection: statement, falsifiable_form,
   axis_s, axis_s_rationale, covers[], falsifiable, evidence:[{citation,locator,text}], optional
   mitigant_hypothesis. **#9 advocate:** `objections:[]` + `mitigants:[{retires_objection_id,
   statement,mitigant_type,residual_risk,falsifiable,evidence[]}]`. **#10 gap-hunter:** no
   objections (speaker-selection + gap-log only) — leave as is.
2. Make CONSUMER forgiving: add minimal input-coercion to `build_facts.py` (string evidence→
   [{citation}]; missing wrapper→derive seat from filename; list→objections; normalize axis_s
   casing). Keep engine-fact output + Axis-S separation UNCHANGED.
VERIFY: author a realistic seat-04.json + seat-09.json, run build_facts.py, confirm facts.json/
severity-map.json/mitigant-map.json produced, advocate mitigant→depends_on fact, axis_s ONLY in
severity-map.

## THEN (the "experience it" milestone — Mode A):
3. Wire `SKILL.md` Mode-A router + the blind-opening-pass step (spawn active seats via Task on
   the shared brief → collect round-01 objections → build_facts → run_synthesis → verdict →
   render_memo). 
4. Do a REAL run on `.claude/skills/acos-investment-committee/fixtures/sample-deal/` → produce a
   real `ic-memo.md`. SHOW IT TO THE USER (this is what they asked to experience).

## THEN Waves 4–5:
- Wave 4 Mode B: D1 moderator loop + transcript, D2 tally/chair-vocab/ESC/one-to-one/exclude,
  D3 resume/durability.
- Wave 5: E1 (reuse legal-analyst via /acos-legal-analysis + compliance companion + conflicts-
  disclosure.yaml), F1 (guardrails: independence-first, kill-criteria, autopilot pre-flight
  ABORT assertion, per-run conflicts-disclosure).

## Key gotchas / discipline
- **Vendored engine invocation:** any script calling the engine must
  `sys.path.insert(0, <skilldir>/scripts/synthesis/scripts)` — modules import by bare name.
- **VERIFY, DON'T TRUST LOGS:** recompute every gate. Two agent self-reports this session hid
  real bugs (engine layout; the C1↔seat contract). Run scripts TOGETHER (interop), not just solo.
- **Subagent Write:** works for real files (the swarm "findings.md" block was harness-specific);
  see memory `reference_subagent_write_blocked`.
- Plan artifacts: `planning/preeng/003-investment-committee/` (spec.md, tech_prd.md, 16 slices,
  all reconciled to the final roster). Slice skeletons: `planning/slices/SLICE-IC-*.yaml`.
- Build via parallel dependency waves from main conversation ("fast mode"); user is hands-off,
  interrupt only for genuine design forks / destructive / broken-dependency-changing-design.
