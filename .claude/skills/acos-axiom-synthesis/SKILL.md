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

**BUILT & fixture-tested (Phases 0–7, deterministic, no model calls — 54 assertions):**
- Substrate (Phases 0–1): `axiom_ledger.py` (single-writer hash-chained ledger,
  §15.1 invariants, §15.2 state machine, §15.3 resumable frontier, renderer),
  `ledger_writer.py` / `verify_ledger.py` / `next_claims.py` / `render.py`.
- `decircularize.py` (Phase 2) — the citogenesis firewall: collapse non-independent
  sources to one vote BEFORE any corroboration counting.
- `grade_fuse.py` (Phase 3) — two-axis grading + claim-level fusion (median/majority/
  linear-pool) + dual-track tally + single-source cap.
- `falsify.py` + `oscillation_guard.py` (Phase 4) — nullification checklist +
  falsification-gate disposition + the settled-objections oscillation guard.
- `resolve.py` (Phase 5) — the precedence-ladder conflict resolver + consensus polarity,
  terminating in UNRESOLVED (never a fabricated winner).
- `lifecycle.py` (Phase 6) — the demotion cascade (truth-maintenance over dependents).
- `coverage.py` + `mirror.py` (Phase 7) — the final coverage gate + ACOS evidence/metrics mirror.
- `orchestrate.py` — the end-to-end driver (stages 2→7 over the ledger).
- Tests: `tests/test_substrate.py` (19) + `tests/test_pipeline.py` (35, incl. the
  end-to-end adversarial cases).

**What still requires live models (the ONLY non-deterministic part):** producing the
atomic claims (elicitation), the ACH pass, and the independent different-family refuter
verdict. These are performed by `Task()`-spawned agents that fill the `fact` structure
`orchestrate.run()` consumes. In tests they are supplied as fixtures / a mock runner, so
the whole pipeline is provable offline. The agent prompts live in `prompts/` (drafts) and
the thin wizard that spawns them is the remaining glue (see PLAN.md §7, §10.2).

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

## Model strategy (subscription-only Claude)

Cross-family diversity is the ideal (breaks correlated errors). When only Claude is
available, achieve partial diversity via model **classes** (Opus/Sonnet) + prompt /
temperature variation, and **flag in the output that cross-family independence is
reduced** (open decision PLAN.md §12.4). External families plug in later via the model-
profile system / `run-external-agent.py`. Spawn via `Task()` — never `ANTHROPIC_API_KEY`.

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
python3 .claude/skills/acos-axiom-synthesis/tests/test_substrate.py   # 19 assertions, offline
```
