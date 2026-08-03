# Live-run RUNBOOK — acos-axiom-synthesis conductor

How a live four-family synthesis actually runs. The split:

- **The orchestrator (main Claude, at run time)** does what a subprocess cannot:
  spawns Claude `Task()` agents, calls `run-external-agent.py` for Gemini/GLM,
  drives the ChatGPT browser voice, and WRITES each raw reply into the collection
  layout below.
- **`conductor.py` (deterministic, tested)** reads that layout, parses every reply,
  clusters claims, assembles engine `fact` records, and runs `orchestrate.run()`.

The handoff between them is the **collection directory** — plain files on disk, so
the run is inspectable and resumable.

## Collection layout

```
.acos/axiom/<session-id>/
  collected/
    elicitor/<family>[-<n>].json        # raw elicitor reply, one per elicitor agent
    grader/<claim-id>__<family>.json     # raw grader reply, one per (claim, grader)
    refuter/<claim-id>.json              # raw refuter reply, one per claim
  claims.jsonl                           # written by the engine
  source-of-truth.md                     # written by the engine
```

Files hold the model's **raw text reply** (JSON, possibly fenced or prose-wrapped —
`conductor.extract_json` tolerates all three). `<claim-id>` is `C1`, `C2`, … in the
order `conductor.cluster_claims` produces (cluster index).

## Step-by-step (the orchestrator drives this)

### 1. Elicit (blind, cross-family)
For each family — Claude, Gemini, z.ai/GLM, ChatGPT — send the **same** family-neutral
`prompts/elicitor.md` with the question + sub-questions. Blind: no agent sees another's
output.
- **Claude**: `Task()` sub-agent (subscription).
- **Gemini**: `run-external-agent.py --model google:gemini-flash-latest`
- **GLM**: `ZAI_API_KEY="$ZAI_CODING_PLAN_API_KEY" run-external-agent.py --model zai:glm-4.7`
- **ChatGPT**: browser voice — open a **fresh** `chatgpt.com` chat (fresh = blind),
  paste the prompt, read the reply back.

Write each raw reply to `collected/elicitor/<family>.json`.

### 2. Cluster (peek)
Run `conductor.cluster_claims` (via a short `load_collected` + `build_facts` dry call,
or just reason over the parsed claims) to learn the claim ids `C1…Cn` and which
sub-question each covers. Clustering groups the same atomic claim across families.

> v1 clustering is a deterministic normalized-text match. For paraphrased duplicates
> (different wording, same claim) do a **semantic-match** pass as orchestrator — the
> same judgement step de-circularization uses — and merge before grading. Note any
> merge you make so it is auditable.

### 3. Grade (blind judges, never the author)
For each claim `Ck`, dispatch ≥2 blind graders from families **other than** the claim's
author, each with `prompts/grader.md` + the claim + its evidence. Write each to
`collected/grader/Ck__<family>.json`. `conductor.combine_graders` takes the per-question
majority (fail-closed on ties). Each grader also emits a blind `volatility` label
(durable/slow/fast/volatile); the unique-max vote becomes the recency classifier's
judge input (`volatility_judge`) — a tie means no judge signal.

### 4. Refute (independent, different family)
For each claim `Ck`, dispatch one refuter from a **different family** than the author,
with `prompts/refuter.md` + the claim + the injected `settled-objections` list. Write to
`collected/refuter/Ck.json`. The conductor derives `V4-SURVIVES-REFUTER` from the verdict
(survives unless fatal AND credible AND not rebutted).

### 5. Run the engine
```python
import sys; sys.path.insert(0, ".claude/skills/acos-axiom-synthesis/scripts")
import conductor
out = conductor.run_from_collected(
    session_dir=".acos/axiom/<session-id>",
    question="<the scoped question>",
    sub_questions=["SQ1", "SQ2", ...],
    now="<UTC ISO timestamp>",           # pass in; do not call Date.now in-engine
    repo_root=".", date_str="<YYYY-MM-DD>",   # REAL run date — freshness measures against it
    session="<session-id>",
    domain="<optional subject tag>")     # e.g. 'rates'/'ai'/'geography' — volatility prior
print(out["summary"], out["parse_errors"], out["assembly_notes"])
```
This parses, clusters, assembles facts, runs stages 2–7, writes `claims.jsonl` +
`source-of-truth.md`, runs the coverage gate, and mirrors the run.

### 6. Report
Surface `out["summary"]` (states, coverage, chain-intact), any `parse_errors` /
`assembly_notes` (never hide a dropped reply), and the clickable `source-of-truth.md`.
Invite the user to spot-check 2–3 `verified` claims against provenance.

## What is proven vs. driven

- **Proven offline (tests/test_conductor.py, 36 assertions):** JSON extraction,
  parsers, grader consensus (incl. the volatility vote), fact assembly, clustering,
  and the full `run_from_collected` path on fixture files — including the F4 e2e case
  (judge-volatile + undated sources → capped at CORROBORATED).
- **Driven live by the orchestrator (not unit-testable without models):** the actual
  Task()/external/browser calls in steps 1, 3, 4, and the semantic-merge in step 2.
  These are proven by a real end-to-end run, per the "run it live before done" rule.

## Known v1 limitations (honest)

- Cluster matching is exact-normalized-text; paraphrase merging is a manual orchestrator
  step until a semantic-match helper lands.
- Grader consensus is simple majority; no re-dispatch (Wigum) loop on grader disagreement
  yet.
- Recency / old-information handling is **BUILT** (2026-08-02, per RESEARCH-recency-bias-
  2026-08-02.md §6.1): `scripts/volatility.py` + `config/volatility.yaml` classify each
  claim's volatility and cap/flag a stale, confidently-volatile claim; `freshness_ok` is
  now COMPUTED (not hand-set) and `N5-NOT-STALE` reads it; guarded supersession runs for
  non-durable conflicts. **Operationally: pass the REAL run date as `date_str`** — recency
  keys the freshness windows off each source's `as_of` date vs. `date_str`, so the
  `1970-01-01` default makes every source look fresh (a safe no-op, but recency does
  nothing). F4 (2026-08-02) wired the live path: graders emit a blind `volatility`
  label (voted → `volatility_judge`), `run_from_collected` takes an optional `domain`
  tag, and the checklist path applies the same recent-corroboration cap for `verified`
  (losing N5 alone leaves 9/10 = 90%, which still meets `verified_min` — the cap closes
  that). Deferred: (b) time-decay math and (d) a `--recency` mode overlay.
