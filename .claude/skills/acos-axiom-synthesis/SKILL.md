---
name: acos-axiom-synthesis
description: Synthesize outputs from multiple AI agents and/or different LLMs into ONE
  coherent, authoritative, defeasible source-of-truth file — or an explicit refusal —
  never a fabricated consensus. Decomposes inputs into atomic claims, de-circularizes
  correlated sources, grades each claim on two axes, fuses claim-by-claim, runs an
  independent different-family falsification gate, preserves conflicts, and writes a
  hash-chained append-only claim ledger rendered to Markdown. Use to reconcile multiple
  analyses / model outputs / agent reports into a trusted single document.
user-invocable: true
argument-hint: "[question or path-to-inputs] [--mode actual|synthesis] [--models N]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task, WebSearch, WebFetch
---

# ACOS Axiom Synthesis

Fuse many AI-agent / multi-model outputs into one authoritative, defeasible
source-of-truth file. **A refutation-and-grading engine, not a merger** — its value is
the discipline it imposes between "many opinions" and "one trusted answer."

Full design rationale: `planning/acos-axiom-synthesis/PLAN.md`.
Formal claim-state contract: `STATE-MACHINE.md` (authoritative).

## Build status (all phases built; deterministic core fixture-tested)

**BUILT & fixture-tested (Phases 0–7 + confidence checklist + live-run conductor + recency discipline, deterministic, no model calls — 159 assertions):**
- Substrate (Phases 0–1): `axiom_ledger.py` (single-writer hash-chained ledger,
  §15.1 invariants, §15.2 state machine, §15.3 resumable frontier, renderer),
  `ledger_writer.py` / `verify_ledger.py` / `next_claims.py` / `render.py`.
- `decircularize.py` (Phase 2) — the citogenesis firewall: collapse non-independent
  sources to one vote BEFORE any corroboration counting.
- `grade_fuse.py` (Phase 3) — two-axis grading + claim-level fusion (median/majority/
  linear-pool) + dual-track tally + single-source cap.
- `checklist.py` (**Point-1 confidence gate**, 2026-07) — the auditable YES/NO
  checklist that decides the confidence tier: 4 **veto** questions (any single NO
  nullifies the claim) + 10 **normal** questions scored to a percentage, graded into
  `verified` / `probable` / `unverified` with the single-source cap preserved. Knobs
  (threshold, questions, per-topic add-on packs) live in `config/checklist.yaml`;
  `DEFAULT_CHECKLIST` is an identical embedded fallback so a missing/edited file never
  breaks the run. Engaged when a fact carries blind-judge semantic answers; the legacy
  grade tier remains for facts without them (backward-compatible).
- `falsify.py` + `oscillation_guard.py` (Phase 4) — nullification checklist +
  falsification-gate disposition + the settled-objections oscillation guard.
- `resolve.py` (Phase 5) — the precedence-ladder conflict resolver + consensus polarity,
  terminating in UNRESOLVED (never a fabricated winner). For a **non-durable** conflict it
  consults a **guarded supersession** rung (below directness/originality/reliability,
  above independent_sources): a newer claim retires an older one only if it is
  equal-or-higher tier AND independently corroborated — otherwise the guard fails and the
  classic ladder decides (a lone fresh source can never win).
- `volatility.py` + `config/volatility.yaml` (**recency discipline**, 2026-08 —
  RESEARCH-recency-bias-2026-08-02.md) — corrects the structural bias by which an OLD
  well-corroborated claim out-scores a fresher, better one, WITHOUT "newest wins."
  Each claim is classified `durable` / `slow` / `fast` / `volatile` (deterministic
  lexical + domain prior, optional blind-judge label reconciled; **advisory** — it may
  cap or flag, never nullify). `compute_freshness` decides staleness from the dates of
  the **independent** sources vs. per-class windows (durable = ∞, slow = 1095d, fast =
  183d, volatile = 14d; editable). A confidently-volatile **stale** claim earns a
  `("stale", severity)` downgrade and its top tier requires ≥1 **recent** independent
  source (else caps at `probable`); durable claims are **exempt** (age is not a defect);
  an unclassifiable claim is flagged but NOT capped (low classifier confidence). The
  renderer surfaces a "⚠ possibly stale as of <date>" banner. Wired opt-in through
  `grade_fuse.grade_claim`, `resolve.resolve_conflict`, `checklist` (`N5-NOT-STALE`'s
  `freshness_ok` is now **computed**, not hand-set), and `orchestrate.process_fact`;
  inert on pre-recency fixtures. **Two deliberate deviations from the design doc,
  verified against the code:** (1) `N5-NOT-STALE` stays a **normal** question (a stale
  claim loses a point → tier capped), NOT a veto — consistent with "cap, never nullify";
  (2) freshness keys on each source's `as_of` (content date), not `observed_at` (ingest),
  because ingest ≈ run-date carries no staleness signal within a single run (`observed_at`
  is still recorded on every claim for bitemporal audit).
- `lifecycle.py` (Phase 6) — the demotion cascade (truth-maintenance over dependents).
- `coverage.py` + `mirror.py` (Phase 7) — the final coverage gate + ACOS evidence/metrics mirror.
- `orchestrate.py` — the end-to-end driver (stages 2→7 over the ledger; runs the
  confidence checklist at stage 4.5 when judge answers are present).
- `conductor.py` (**the live-run driver**, 2026-08) — turns collected raw model
  replies into engine `fact` records and runs the pipeline: tolerant JSON extraction
  (fences/prose), per-family reply parsers, N-grader majority consensus (fail-closed),
  refuter→`V4` derivation, cross-family claim clustering, and `run_from_collected`
  (parse→cluster→assemble→`orchestrate.run`). The live model calls it depends on
  (Task/external/browser) are driven by the orchestrator per `RUNBOOK.md`.
- Tests: `tests/test_substrate.py` (19) + `tests/test_pipeline.py` (35, incl. the
  end-to-end adversarial cases) + `tests/test_checklist.py` (21, the confidence gate)
  + `tests/test_conductor.py` (36, the live-run driver incl. the F4 volatility-vote
  wiring) + `tests/test_recency.py` (48, the volatility/freshness/supersession
  discipline incl. the 2026-08-02 review-fix cases) = **159 offline assertions**.

**What still requires live models (the ONLY non-deterministic part):** producing the
atomic claims (elicitation), the ACH pass, the independent different-family refuter
verdict, and the **semantic checklist answers** (the blind judge's YES/NO on the
non-deterministic questions — e.g. "does the cited source actually support the claim?").
These are performed by `Task()`-spawned agents (Claude) and `run-external-agent.py`
(external families) that fill the `fact` structure `orchestrate.run()` consumes. In tests
they are supplied as fixtures, so the whole pipeline is provable offline. The agent
prompts live in `prompts/` and the thin wizard that spawns them is the remaining glue
(see PLAN.md §7, §10.2).

## The pipeline (target — PLAN.md §3)

```
[1] decompose & elicit (blind, cross-family)  →  [2] de-circularize  →
[3] grade on two axes  →  [4] fuse per claim (+dual-track tally)  →
[5] falsify (independent different-family refuter + oscillation guard)  →
[6] resolve or abstain (precedence ladder / UNRESOLVED)  →
[7] write the hash-chained ledger + render source-of-truth.md
```

Confidence is **derived from independent cross-family agreement + provenance** — never
model self-report, never a fake decimal. Every claim carries an ordinal tier
(`verified` / `probable` / `unverified`), a citation to origin, the rejected
alternatives, and a supersession history.

A **recency discipline** runs alongside [3]–[6]: each claim's volatility is classified,
staleness of the independent sources caps the tier of a confidently-volatile stale claim
(never a durable one), and a guarded supersession rung lets a newer, corroborated,
equal-or-higher-tier claim retire an older one — all **behind** the de-circularization
firewall and the ≥2-independent-cross-family floor, so recency reweights *which*
well-evidenced claim wins without ever letting a single fresh source win.

## Model strategy — the four-family fan-out (cross-family diversity)

Cross-family diversity breaks correlated errors: models from different makers don't share
the same blind spots, so their agreement is real corroboration. The configured families:

| Family | Transport | Key / access |
|--------|-----------|--------------|
| **Claude** (Opus/Sonnet) | `Task()` blind sub-agents | subscription — never `ANTHROPIC_API_KEY` |
| **Gemini** | `run-external-agent.py --model google:gemini-flash-latest` | `GOOGLE_API_KEY` — **free key from Google AI Studio** (`ai.google.dev`); the consumer Gemini app subscription does NOT include it. Use the `-latest` aliases; dated models like `gemini-2.5-flash` retire (404). |
| **z.ai / GLM** | `run-external-agent.py --model zai:glm-4.7` | `ZAI_API_KEY` — your Z.ai Coding Plan key (Doppler `ai-model-api/dev_personal` → `ZAI_CODING_PLAN_API_KEY`) |
| **ChatGPT** (Plus) | Claude-in-Chrome browser voice (below) | your Plus web login — Plus has **no** API |

Only **≥2 distinct families** are needed for the top `verified` tier, so Claude + Gemini +
z.ai/GLM already clears the bar; ChatGPT is an additive 4th voice. If only Claude is
available, fall back to model **classes** (Opus vs Sonnet) + prompt/temperature variation,
and **flag in the output that cross-family independence is reduced** (PLAN.md §12.4).

### The ChatGPT browser voice (optional 4th family)

ChatGPT Plus is web-only, so it can't be reached by `run-external-agent.py`. When enabled,
the main Claude session drives it through the Claude-in-Chrome tools:

1. Open a tab to `chatgpt.com` (user must already be logged in — Claude never signs in).
2. Paste the **same** self-contained prompt (`elicitor.md` / `grader.md` / `refuter.md`)
   used for the API families — the prompt is family-neutral by design.
3. Read the reply back and parse its STRICT-JSON block into the `fact` structure, tagging
   `family: "openai-web"`.

**Honest limits (do not hide these):** automating the ChatGPT web UI generally runs against
OpenAI's terms of service; it is slow (human-speed), breaks on UI changes/login walls, and
is *not blind* in the same way (the orchestrator sees it), which slightly weakens
independence. Keep it a flagged, optional voice — never a load-bearing seat. For scale or
reliability, prefer a paid OpenAI API key (`openai:gpt-4o`) instead.

## Wake-up checklist (the human-gated last mile)

The engine, checklist, prompts, and API wiring are built. Two steps need YOU (they touch
your accounts) before a **live** four-family run:

1. **Gemini key (free):** create an API key at `https://ai.google.dev` (Google AI Studio),
   store it in Doppler as `GOOGLE_API_KEY`. Test:
   `doppler run --project ai-model-api --config dev_personal --silent -- python3 .claude/scripts/run-external-agent.py --agent qa-reviewer --model google:gemini-flash-latest --task "reply OK"`.
   ✅ DONE 2026-07-22 — key stored in Doppler, `gemini-flash-latest` confirmed working.
2. **z.ai/GLM key:** `export ZAI_API_KEY="$(doppler secrets get ZAI_CODING_PLAN_API_KEY --project ai-model-api --config dev_personal --plain)"` (or your `glm` Doppler wrapper). Test with `--model zai:glm-4.7`.
3. **ChatGPT (optional):** log into `chatgpt.com` in Chrome first, then ask this session to
   run the browser voice.

Everything deterministic is already proven offline (75 assertions). These three unlock the
live model calls.

## Substrate usage (available now)

```bash
S=.claude/skills/acos-axiom-synthesis/scripts
L=.acos/axiom/<session>/claims.jsonl          # append-only ledger

# write a claim (THE single writer; refuses illegal writes by exit code)
echo '{"id":"CLM-1","statement":"...","state":"CONJECTURE","confidence":"unverified"}' \
  | python3 "$S/ledger_writer.py" "$L" --claim - --now "$(date -u +%FT%TZ)"

python3 "$S/verify_ledger.py" "$L"            # tamper check (exit 1 if broken)
python3 "$S/next_claims.py"  "$L"             # resumable work frontier
python3 "$S/render.py"       "$L" --out .acos/axiom/<session>/source-of-truth.md --question "..."
```

**The single-writer rule is load-bearing:** nothing except `ledger_writer.py` may
change a claim's state. That is what turns the plan's caps (single-source cap,
corroboration gate, falsification gate, dependency integrity) from written policy into
mechanical invariants that cannot be forgotten under load.

## Workspace layout

```
.acos/axiom/<session-id>/
  claims.jsonl          # canonical, append-only, hash-chained
  evidence/sha256-<hex> # content-addressed raw agent outputs (Phase 2+)
  source-of-truth.md    # generated human view
  settled-objections.md # oscillation-guard log (Phase 4)
  run_state.json        # cache/optimization; NOT the source of truth
```

## Tests

```bash
S=.claude/skills/acos-axiom-synthesis
python3 $S/tests/test_substrate.py    # 19 assertions, offline (substrate)
python3 $S/tests/test_pipeline.py     # 35 assertions, offline (Phases 2–7 end-to-end)
python3 $S/tests/test_checklist.py    # 21 assertions, offline (the confidence checklist)
python3 $S/tests/test_conductor.py    # 36 assertions, offline (the live-run driver)
python3 $S/tests/test_recency.py      # 48 assertions, offline (recency discipline)
# 159 offline assertions total, all passing.
```
