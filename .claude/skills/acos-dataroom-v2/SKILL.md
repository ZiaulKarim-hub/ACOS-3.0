---
name: acos-dataroom-v2
description: |
  Autonomous, multi-model consensus, zero-defect outbound data room generation for OKOA
  Capital. Takes a source loan folder + one-line objective, outputs a buyer-ready
  organized dataroom + 2-worksheet Excel guide. No human gates. Multi-stage adversarial
  consensus (3-agent blind voting, Wigum loop QA, dedicated privilege scanner) enforces
  quality. Designed to be boss-criticism-proof on first cold look. Successor to
  acos-dataroom v1.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch
argument-hint: "--source <folder> --objective '<one-line brief>'"
---

# ACOS Data Room v2 — Autonomous Multi-Model Consensus

## 0. Authority

This SKILL.md is the orchestrator procedure executed by the main Claude session when
the user invokes `/acos-dataroom-v2`. The authoritative design specification is
`DESIGN.md` in this directory — read it first if anything in this procedure seems
unclear.

**Non-negotiables (DO NOT VIOLATE — see `DESIGN.md §1` for full list):**

1. Files keep original names (one exception: `(2)`, `(3)` suffix on flat-folder collisions per §4.6 of DESIGN).
2. ALL file operations are COPY. Source folder is never modified.
3. Blind consensus in every swarm — agents within a swarm NEVER see each other's outputs.
4. Cognitive diversity via model mix — Opus + Sonnet + Opus, or Opus + Opus + Sonnet.
5. Default-EXCLUDE on irreducible disagreement.
6. No human gates — skill runs to completion autonomously. Only HALT triggers are documented in §11 of this file.
7. No external Anthropic API calls. All Claude work via `Task()` sub-agents (user's Max subscription).
8. Checkpoint after every consensus decision. Multi-hour runs must survive crashes.

## 0.5 Agent Spawning Convention

All v2 agents are prefixed `dr2-` in `.claude/agents/`. The 14 agent roles:

| Role (this skill) | Agent file | Default model |
|---|---|---|
| Objective researcher | `dr2-obj-researcher` | opus |
| Objective synthesizer | `dr2-obj-synthesizer` | opus |
| Inclusion deliberator | `dr2-inclusion-deliberator` | opus |
| Privilege scanner | `dr2-privilege-scanner` | opus |
| Inclusion QA | `dr2-inclusion-qa` | opus |
| Taxonomy designer | `dr2-taxonomy-designer` | opus |
| Taxonomy synthesizer | `dr2-taxonomy-synthesizer` | opus |
| Placement classifier | `dr2-placement-classifier` | opus |
| Placement QA | `dr2-placement-qa` | opus |
| Guide drafter | `dr2-guide-drafter` | opus |
| Guide synthesizer | `dr2-guide-synthesizer` | opus |
| Guide QA | `dr2-guide-qa` | opus |
| Description drafter | `dr2-description-drafter` | opus |
| Description QA | `dr2-description-qa` | opus |

**Swarm spawn pattern (for 3-agent blind swarms):** spawn 3 PARALLEL `Task()` calls in
one message, ALL with the same `subagent_type`, with model overrides for cognitive
diversity. Standard mix:
- Instance 1: `model: opus` (default)
- Instance 2: `model: sonnet` (cognitive-diversity instance)
- Instance 3: `model: opus` (default)

The agent's prompt is the same for all 3 instances. Each writes its output to a path
keyed by an `agent_id` you assign in the prompt (e.g., `instance_1`, `instance_2`,
`instance_3`). This gives the blind-consensus + model-mix architecture the design
requires.

**Synthesizer + single-agent spawns:** one `Task()` call with default model (opus).

## 1. Invocation

User invocation:
```
/acos-dataroom-v2 --source "/path/to/loan/folder" --objective "<one-line brief>"
```

Both `--source` and `--objective` are REQUIRED. If either is missing, ask the user
once for the missing arg and then proceed. No other args. No subcommands. No
interactive wizard beyond the one-arg-missing fallback.

## 2. Argument parsing

Parse `$ARGUMENTS` for `--source` and `--objective`. Validate:
- `--source` is an existing directory readable by the user.
- `--objective` is a non-empty string.

If either is missing or invalid, print one clarifying prompt and wait for response.

## 3. Run-directory setup

Once args are validated:

```bash
SOURCE="$ARG_SOURCE"
OBJECTIVE="$ARG_OBJECTIVE"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
HASH="$(echo "$SOURCE" | shasum -a 256 | cut -c1-8)"
RUN_ID="run_${TIMESTAMP}_${HASH}"

# Audit trail (votes, evidence, deliberation logs, run_state.json) lands in
# the directory the skill is invoked from — NOT next to the source folder.
# This keeps the messy audit material out of Dropbox-synced source folders
# and consolidates all runs under a single workspace location.
INVOCATION_DIR="$(pwd)"
RUN_DIR="${INVOCATION_DIR}/_acos_dataroom_v2_output/${RUN_ID}"

# The FINAL shippable dataroom still lands next to the source folder so it
# can be conveniently shared/copied without leaving the source location.
SOURCE_PARENT="$(dirname "$SOURCE")"

mkdir -p "$RUN_DIR"/{phase1/proposals,phase2/votes,phase2/disputed,phase2_5,phase3,phase4/proposals,phase5,phase6,intermediate,extraction,evidence,logs,dataroom}
```

Write `$RUN_DIR/run_state.json` with initial state:
```json
{
  "run_id": "<RUN_ID>",
  "source": "<SOURCE>",
  "objective_brief": "<OBJECTIVE>",
  "started_at": "<ISO8601>",
  "phase": "0_setup",
  "last_completed_checkpoint": null,
  "skill_version": "v2.0.0"
}
```

Initialize `$RUN_DIR/logs/run_log.txt` for verbose logging.

## 4. Phase 1 — Objective Solidification

**Goal:** transform thin user objective into rich, internet-grounded, consensus-validated specification. See `references/phase_1.md` for full procedure detail.

### 4.1 Source-folder shape inventory

Call:
```bash
python3 scripts/scan_folder.py --source "$SOURCE" --shallow --output "$RUN_DIR/phase1/source_shape.json"
```

This walks the top 2 levels of the source folder, lists folder names + file counts, samples up to 5 "high-signal" filenames (matching `*term*sheet*`, `*purchase*agreement*`, `*notice*sale*`, `*loan*agreement*`, `*offering*memo*`, `*PSA*`, `*ASA*`).

### 4.2 Spawn 3 research agents in parallel

Spawn via `Task()` with `subagent_type: dr2-obj-researcher` (3 parallel instances per §0.5 swarm convention)`. ALL THREE IN PARALLEL (single message, 3 tool calls).

Each agent's prompt includes:
- The user's `--objective` brief verbatim
- Contents of `$RUN_DIR/phase1/source_shape.json`
- Instruction to output a structured Markdown to `$RUN_DIR/phase1/proposals/<agent_id>.md` per the schema in `references/phase_1.md §3.4`
- Authorization to use WebSearch + WebFetch for grounding

WAIT for all 3 to complete before proceeding.

### 4.3 Synthesize

Spawn `Task()` with `subagent_type: dr2-obj-synthesizer`. Prompt includes:
- Paths to all 3 proposals
- Instruction to read all three and produce `$RUN_DIR/phase1/SOLIDIFIED_OBJECTIVE.md` per the schema in `references/phase_1.md §3.5`

Read the synthesized result. If the synthesizer's metadata indicates substance convergence <60% or >2 open questions, dispatch ONE blind re-run of all 3 researchers (same prompts, no feedback) and re-synthesize. If still divergent → HALT per §11.

### 4.4 Checkpoint

Update `run_state.json`:
```json
{ "phase": "1_objective_solidified", "last_completed_checkpoint": "phase1_synthesis_complete" }
```

Log to `logs/run_log.txt` and proceed to Phase 2.

## 5. Phase 2 — Inclusion Deliberation

**Goal:** for every file, decide INCLUDE vs EXCLUDE via unanimous 3-agent blind consensus. See `references/phase_2.md` for full procedure.

### 5.1 Pre-flight — full file manifest

```bash
python3 scripts/scan_folder.py --source "$SOURCE" --recursive --hash --output "$RUN_DIR/intermediate/file_manifest.json"
```

Produces deterministic `file_id` per file (SHA-256 prefix), detects encrypted/zero-byte/oversized/unsupported files. These pre-bucket into `intermediate/unable_to_evaluate.csv` and never reach the deliberation swarm.

### 5.2 Extraction

For each evaluable file, call:
```bash
python3 scripts/extract_text.py --manifest "$RUN_DIR/intermediate/file_manifest.json" --output-dir "$RUN_DIR/extraction/"
```

Native text where possible. PDF pages with low OCR confidence or no extractable text get marked for vision-bridge dispatch.

For pages marked for vision:
```bash
python3 scripts/ocr_and_vision.py --manifest "$RUN_DIR/intermediate/file_manifest.json" --output-dir "$RUN_DIR/extraction/" --emit-bridge-requests
```

Then spawn vision-capable `Task()` sub-agents to fulfill bridge requests per the v1.1.0 vision-bridge protocol. After responses are written:
```bash
python3 scripts/ocr_and_vision.py --rehydrate --extraction-dir "$RUN_DIR/extraction/"
```

### 5.3 Per-file deliberation (batched)

Read `file_manifest.json` into memory. For each evaluable file (skip already-logged in `phase2/inclusion_log.csv`):

**Batch processing:** process files in batches of B=5 to balance parallelism with main-thread coordination overhead. Per batch:

Spawn 3 deliberation agents per file IN PARALLEL via `Task()` — `subagent_type: dr2-inclusion-deliberator` x 3, with model overrides per §0.5 (opus, sonnet, opus). For B=5 files this is 15 parallel `Task()` calls in one message.

Each agent's prompt includes:
- The file's full extracted text + vision summary from `$RUN_DIR/extraction/<file_id>/extraction.json`
- The file's filename + source path
- Contents of `$RUN_DIR/phase1/SOLIDIFIED_OBJECTIVE.md`
- Output path: `$RUN_DIR/phase2/votes/<file_id>/<agent_id>.json`
- Schema spec from `references/phase_2.md §4.4`
- The blindness invariant (do not reference other agents)
- Privilege checklist (flag for Phase 2.5, but Phase 2 decision is relevance-only)

WAIT for all batch votes to land on disk.

### 5.4 Consensus check (per file in batch)

For each file, read all 3 votes:

- **Unanimous INCLUDE:** copy source file to `$RUN_DIR/dataroom/<filename>` (apply `(2)`, `(3)` suffix on collision). Append to `phase2/inclusion_log.csv`.
- **Unanimous EXCLUDE:** log to `phase2/exclusion_log.csv` with reasoning.
- **Split (2-1):** queue for blind re-dispatch.

### 5.5 Blind re-dispatch

For each split-decision file, re-spawn the same 3 agents with the same prompts (no feedback about prior split). Up to K=5 iterations. After 5 still-split → default-EXCLUDE and log to `phase2/disputed/<file_id>.json` with full iteration trail.

Disputed files are surfaced in the final Excel's Manual Review markdown.

### 5.6 Checkpoint

Update `run_state.json` after every batch:
```json
{ "phase": "2_inclusion", "last_completed_checkpoint": "phase2_batch_N_complete" }
```

Once manifest is exhausted, advance to Phase 2.5.

## 6. Phase 2.5 — Privileged-Content Scanner

**Goal:** asymmetric-consensus catastrophic-failure firewall. Any single agent flag → file removed.

### 6.1 Scope

Iterate every file in `$RUN_DIR/dataroom/` (Phase 2 survivors).

### 6.2 Per-file scan (batched)

Same batch size B=5. Per batch, spawn `dr2-privilege-scanner` x 3 in parallel per file per §0.5 (opus, sonnet, opus model mix).

Each agent's prompt includes:
- The file's full extracted text + vision summary
- Contents of `references/privilege_markers.md`
- ONE JOB: detect privileged content. Issue KEEP or FLAG with reasoning.
- Output path: `$RUN_DIR/phase2_5/scans/<file_id>/<agent_id>.json`

### 6.3 Asymmetric consensus

For each file:
- **All 3 KEEP:** file stays in dataroom. Log to `phase2_5/scan_log.csv`.
- **ANY 1+ FLAG:** file is REMOVED from `$RUN_DIR/dataroom/`. Logged to `phase2_5/privileged_removed.csv` with each flagging agent's reasoning.

No re-dispatch. No second chance. This is the asymmetric-harm response per DESIGN §5.4.

### 6.4 Checkpoint

```json
{ "phase": "2_5_privilege", "last_completed_checkpoint": "phase2_5_batch_N_complete" }
```

Advance to Phase 3.

## 7. Phase 3 — Inclusion QA Wigum Loop

**Goal:** catch Phase 2 errors with fresh-eyes review. See `references/phase_3.md`.

### 7.1 Per-file QA (batched)

For every file in `$RUN_DIR/dataroom/` post-2.5, spawn `dr2-inclusion-qa` x 3 per file per §0.5. Distinguish instances in the prompt:
- Instance 1 — adversarial lens ("strongest case this is wrong")
- Instance 2 — completeness lens ("does this serve the objective")
- Instance 3 — coherence lens ("does this fit the dataroom as a whole"; gets full dataroom listing as additional context)

Each issues PASS or FAIL with reasoning. Output: `$RUN_DIR/phase3/qa/<file_id>/<agent_id>.json`.

### 7.2 Wigum loop

For each file:
- **All 3 PASS:** file confirmed. Log to `phase3/qa_pass_log.csv`.
- **ANY 1+ FAIL:** file returns to Phase 2 deliberation queue with FRESH 3-agent instances (no memory of prior votes, NO QA feedback shared — preserves blindness). The re-deliberated verdict may be EXCLUDE this time (file gets removed from dataroom) or INCLUDE (continues to next Phase 3 iteration through Phase 2.5 again).

Cap: K=5 iterations per file. After 5 still failing → file goes to manual-review bucket; logged to `phase3/qa_failed_unconverged.csv`.

### 7.3 Convergence

Phase 3 done when ALL `$RUN_DIR/dataroom/` files PASS all 3 QA agents.

Update `run_state.json`:
```json
{ "phase": "3_inclusion_qa_clean", "last_completed_checkpoint": "phase3_converged" }
```

## 8. Phase 4 — Sub-folder Classification

### 8.1 Step 4a — Taxonomy design

Read all filenames + brief content summaries from `$RUN_DIR/extraction/` for every file in `$RUN_DIR/dataroom/`. Compile into a single context document `phase4/dataroom_inventory.json`.

Spawn `dr2-taxonomy-designer` x 3 in parallel per §0.5. Each gets `phase4/dataroom_inventory.json` + DESIGN.md §7.2 constraints. Each writes a proposed taxonomy JSON to `phase4/proposals/<agent_id>.json`.

Then spawn one `dr2-taxonomy-synthesizer` (default opus). Reads all 3 proposals, produces `phase4/TAXONOMY.json`.

Validate: sequential numbering 1..N no gaps, no semantic duplicates, ≤15 folders, all-encompassing (every dataroom file fits ≥1 proposed folder). If validation fails, re-prompt synthesizer with explicit fix-list (up to 2 re-prompts).

### 8.2 Step 4b — Per-file placement (batched)

Create the sub-folder skeleton in `$RUN_DIR/dataroom/`:
```bash
for folder in TAXONOMY.json.folders:
  mkdir -p "$RUN_DIR/dataroom/$(printf '%02d' $num)_${name}"
```

For each file currently in the dataroom flat root, spawn `dr2-placement-classifier` x 3 per file per §0.5 (opus, sonnet, opus).

Each gets the file content + filename + `TAXONOMY.json`. Each picks a folder number.

- **Unanimous:** move file (within dataroom) to that folder.
- **Split:** blind re-dispatch K=5.
- **Still split:** land in `$RUN_DIR/dataroom/00_Pending_Classification/` and log.

Apply `(2)`, `(3)` suffix on intra-folder collisions.

### 8.3 Checkpoint

```json
{ "phase": "4_classification", "last_completed_checkpoint": "phase4_placement_complete" }
```

## 9. Phase 5 — Classification QA Wigum Loop

For each file in its sub-folder, spawn `dr2-placement-qa` x 3 per §0.5 (opus, sonnet, opus).

Each gets file content + current sub-folder + full TAXONOMY.json. PASS or FAIL.

- **All PASS:** confirmed.
- **ANY FAIL:** file returns to Phase 4 step 4b with fresh 3-agent placement re-deliberation. K=5.

Edge case: if >20% of files keep failing, trigger taxonomy revision (re-run 4a with failing-file context, then re-place ALL files).

```json
{ "phase": "5_classification_qa_clean", "last_completed_checkpoint": "phase5_converged" }
```

## 10. Phase 6 — Excel Artifact + Manual Review Markdown

### 10.1 Worksheet 1 — Data Room Guide

Spawn `dr2-guide-drafter` x 3 in parallel per §0.5. Each reads `SOLIDIFIED_OBJECTIVE.md` + `TAXONOMY.json` + dataroom file counts. Each writes a draft to `phase6/drafts/<agent_id>.md`.

Spawn one `dr2-guide-synthesizer` (default opus) — merges into `phase6/ws1_guide.md`.

Spawn one `dr2-guide-qa` (default opus) — reads the synthesized draft + SOLIDIFIED_OBJECTIVE + actual dataroom listing. Issues PASS or returns specific fix-list. Re-loop guide-synthesizer with fixes. Cap: 10 iterations → HALT.

### 10.2 Worksheet 2 — File Tree

For each file in the final classified dataroom, spawn `dr2-description-drafter` x 3 per §0.5 (opus, sonnet, opus). Each writes a 1-sentence description of what the file IS (not what it MEANS). Output: `phase6/descriptions/<file_id>/<agent_id>.json`.

Consensus rule: substance similarity ≥90% on ≥2/3. If satisfied → synthesis (text merging done in main Claude session, not a separate agent) produces final description. If not → blind re-dispatch K=3 times. Still divergent → fallback to "filename + extracted document type" with a flag in the description.

After all descriptions assembled, spawn `dr2-description-qa` in batches for a final accuracy pass against extracted content. Wigum loop on fixes.

### 10.3 Excel build

```bash
python3 scripts/build_dataroom_guide_excel.py \
  --guide "$RUN_DIR/phase6/ws1_guide.md" \
  --descriptions "$RUN_DIR/phase6/descriptions.json" \
  --taxonomy "$RUN_DIR/phase4/TAXONOMY.json" \
  --dataroom "$RUN_DIR/dataroom" \
  --output "$RUN_DIR/dataroom/<DataRoomName>_Guide_<date>.xlsx"
```

Style: Carbon-style header row, visual sub-folder grouping with outline levels, no formulas/hyperlinks/dropdowns.

### 10.4 Manual Review markdown (conditional)

If any of `intermediate/unable_to_evaluate.csv`, `phase2/disputed/`, `phase3/qa_failed_unconverged.csv`, `phase5/qa_failed_unconverged.csv`, or `dataroom/00_Pending_Classification/` is non-empty:

```bash
python3 scripts/build_manual_review_md.py \
  --run-dir "$RUN_DIR" \
  --output "$RUN_DIR/dataroom/Manual_Review_Required_<date>.md"
```

If all empty, do NOT write this file.

### 10.5 Final-ship copy

Compute `<DataRoomName>` from `SOLIDIFIED_OBJECTIVE.md` asset_identity field (kebab-case, ASCII-safe).

```bash
FINAL_DIR="${SOURCE_PARENT}/${DATAROOM_NAME}_Dataroom"
cp -R "$RUN_DIR/dataroom" "$FINAL_DIR"
```

This is the shippable output. The skill's job is done.

```json
{ "phase": "complete", "last_completed_checkpoint": "phase6_excel_written", "final_output": "<FINAL_DIR>" }
```

## 11. HALT Handling

Triggers (per DESIGN.md §11.4):
1. Phase 1: objective synthesizer cannot converge after 1 re-dispatch.
2. Phase 6: guide QA loop runs >10 iterations.
3. Phase 2 produces empty dataroom (every file excluded).

On HALT, write `$RUN_DIR/HALT_REPORT.md` with:
- Trigger condition
- What was attempted
- All reasoning logs from the unconverged decision
- Recommended operator action

Update `run_state.json` with `"phase": "halted"`. Exit with non-zero code.

**Note:** Phases 2/3/4b/5 do NOT halt the run. Files that exhaust K iterations land in the manual-review bucket. The run continues.

## 12. Resumption Logic

If the user re-invokes `/acos-dataroom-v2 --source <same> --objective <same>` **from the same working directory**:

1. Compute `RUN_ID` deterministically from source path hash + objective hash → look for existing run dir under `$(pwd)/_acos_dataroom_v2_output/`.
2. If found, read its `run_state.json` → find current phase.
3. Within phase, read main log (e.g., `phase2/inclusion_log.csv`) → skip files already logged.
4. Continue from the next pending decision.

Phase 1 is non-resumable mid-phase (whole-phase atomic — too fast to matter).
Phase 6 is non-resumable mid-Wigum-loop (rewriting Excel is cheap).
All other phases are per-decision resumable.

**Important:** because the audit trail lives in `$(pwd)/_acos_dataroom_v2_output/`,
resuming requires invoking from the SAME working directory as the original run.
If you invoke from a different `pwd`, the skill will not find the prior run dir
and will start fresh. To find a prior run, look under
`<original_pwd>/_acos_dataroom_v2_output/run_<TIMESTAMP>_<HASH>/`.

## 13. Logging

Every consensus decision, every Task() spawn, every checkpoint update, every error gets a line in `$RUN_DIR/logs/run_log.txt`. Format:
```
[ISO8601 timestamp] [PHASE] [DECISION_TYPE] file_id=<id> verdict=<...> agents=<...>
```

## 14. Final report

After Phase 6 completes, print to user:

```
✅ acos-dataroom-v2 complete for "<asset name>"

Final dataroom: <FINAL_DIR>
File count: <N> across <M> sub-folders
Excluded by Phase 2 (relevance): <X>
Removed by Phase 2.5 (privilege): <Y>
Files in manual review bucket: <Z>

Open the dataroom: file://<FINAL_DIR>
Open the Excel guide: file://<FINAL_DIR>/<DataRoomName>_Guide_<date>.xlsx
```

---

## References

- `DESIGN.md` — authoritative specification (this skill's contract)
- `references/phase_1.md` — Objective Solidification details + prompts
- `references/phase_2.md` — Inclusion Deliberation details + prompts
- `references/phase_2_5.md` — Privileged-Content Scanner details + prompts
- `references/phase_3.md` — Inclusion QA Wigum details + prompts
- `references/phase_4.md` — Sub-folder Classification details + prompts
- `references/phase_5.md` — Classification QA Wigum details + prompts
- `references/phase_6.md` — Excel + Manual Review details + prompts
- `references/privilege_markers.md` — catalog of privilege patterns
- `references/consensus_mechanics.md` — universal consensus + Wigum loop spec

*acos-dataroom-v2 — autonomous, multi-model consensus, zero-defect data room generation. Run end-to-end with one invocation; no human gates; boss-criticism-proof.*
