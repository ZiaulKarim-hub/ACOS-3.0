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

## Build status (incremental build — substrate first)

**BUILT & fixture-tested (Phases 0–1, deterministic, no model calls):**
- `scripts/axiom_ledger.py` — the single library: canonical hashing, the append-only
  hash-chained ledger, the **single-writer invariants** (§15.1), the **legal state
  machine** (§15.2), the **pure-function resumable frontier** (§15.3), and the renderer.
- `scripts/ledger_writer.py` — the ONLY writer of claim state; refuses illegal writes
  with a non-zero exit (2 schema · 3 invariant · 4 illegal transition).
- `scripts/verify_ledger.py` — tamper-evidence check over the hash-chain.
- `scripts/next_claims.py` — the resumable work frontier (pure function of on-disk state).
- `scripts/render.py` — generates `source-of-truth.md` (UNRESOLVED CONFLICTS / OPEN
  QUESTIONS / SUPERSESSION LOG surfaced).
- `tests/test_substrate.py` — 19 offline assertions covering all of the above.

**NOT yet built (Phases 2–7 — the model-dependent pipeline):** decompose + de-circularize,
two-axis grading + fusion, the falsification gate + oscillation guard, conflict
resolution + abstention, living re-synthesis, coverage gate + review. See PLAN.md §11.

Until those land, invoke the substrate directly (below); the full wizard is a stub.

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
