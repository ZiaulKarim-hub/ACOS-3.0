---
name: acos-dataroom-v2
description: |
  Autonomous, multi-model consensus, zero-defect outbound data room generation for OKOA
  Capital. Takes a source loan folder + deal type + one-line objective; outputs a
  buyer-ready organized dataroom (optionally with a 2-worksheet Excel guide). No
  human gates. Deal-type-driven categorical exclusion fast path, asymmetric-veto
  Phase 2 inclusion (any single EXCLUDE wins, no loop), dedicated privilege scanner,
  Wigum-loop QA on classification, intra-category dedup, and a marquee-prefix
  sub-phase that elevates canonical documents in each sub-folder. Designed to be
  boss-criticism-proof on first cold look. Successor to acos-dataroom v1.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch
argument-hint: "--source <folder> --deal-type <enum> --objective '<one-line brief>' [--with-excel-guide]"
---

# ACOS Data Room v2 — Autonomous Multi-Model Consensus

## 0. Authority

This SKILL.md is the orchestrator procedure executed by the main Claude session when
the user invokes `/acos-dataroom-v2`. The authoritative design specification is
`DESIGN.md` in this directory — read it first if anything in this procedure seems
unclear.

**Non-negotiables (DO NOT VIOLATE — see `DESIGN.md §1` for full list):**

1. Files keep original names — TWO documented exceptions: (a) `(2)`, `(3)` suffix on flat-folder name collisions per §4.6 of DESIGN; (b) `_A__` / `_B__` marquee prefix applied by Phase 5.7 per §9.7 of this file.
2. ALL file operations are COPY. Source folder is never modified.
3. Blind consensus in every swarm — agents within a swarm NEVER see each other's outputs.
4. Cognitive diversity via model mix — Opus + Sonnet + Opus, or Opus + Opus + Sonnet.
5. **Asymmetric consensus where stakes are asymmetric.** Phase 2 (inclusion), Phase 2.5 (privilege), and Phase 5.7 (marquee) all use single-veto-wins with NO re-dispatch loop. Phases 3, 4b, 5 use unanimous-or-loop (re-dispatch up to K=5). See per-phase rules. (Phase 5.5 dedup is a separate, unanimous-or-keep-all pass — see §9.5.)
6. **Default-EXCLUDE on every borderline.** v2.1 inclusion deliberators do NOT lean include on ambiguity — borderline = EXCLUDE. The Phase 3 fresh-eyes loop is the mechanism for catching over-aggressive cuts.
7. **Categorical exclusion fast path.** Phase 2 deliberators check the active deal type's `hard_exclusions` list (from `references/deal_types.md`) BEFORE any general deliberation. Filename / content match = EXCLUDE, no full deliberation. Carve-outs are explicit per category.
8. No human gates — skill runs to completion autonomously. Only HALT triggers are documented in §11 of this file.
9. No external Anthropic API calls. All Claude work via `Task()` sub-agents (user's Max subscription).
10. Checkpoint after every consensus decision. Multi-hour runs must survive crashes.

## 0.5 Agent Spawning Convention

All v2 agents are prefixed `dr2-` in `.claude/agents/`. The 15 agent roles:

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
| Marquee classifier | `dr2-marquee-classifier` | opus |
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
/acos-dataroom-v2 \
  --source "/path/to/loan/folder" \
  --deal-type <takeout-lender|property-sale|loan-sale|loan-participation|foreclosure-auction|lender-internal> \
  --objective "<one-line brief>" \
  [--with-excel-guide]
```

REQUIRED args: `--source`, `--deal-type`, `--objective`.
OPTIONAL args: `--with-excel-guide` (default OFF — see §10).

If any required arg is missing, FAIL with a clear error message listing which
required arg is missing and the valid values for `--deal-type`. Do NOT prompt
interactively, do NOT default — the failure modes that motivated v2.1.0 came
from too much skill autonomy on these inputs.

No other args. No subcommands. No interactive wizard.

## 2. Argument parsing

Parse `$ARGUMENTS` for `--source`, `--deal-type`, `--objective`, `--with-excel-guide`. Validate:

- `--source` is an existing directory readable by the user.
- `--deal-type` is one of the enum values listed in §1. Case-insensitive match;
  store as canonical lowercase-hyphenated form. Any other value → FAIL with
  the valid list.
- `--objective` is a non-empty string.
- `--with-excel-guide` is a presence flag — its presence sets
  `with_excel_guide=true`; absence sets `false`.

If any validation fails, print a clear error message identifying the failing arg
and exit non-zero. Do not run any phases.

## 3. Run-directory setup

Once args are validated:

```bash
SOURCE="$ARG_SOURCE"
DEAL_TYPE="$ARG_DEAL_TYPE"
OBJECTIVE="$ARG_OBJECTIVE"
WITH_EXCEL_GUIDE="${ARG_WITH_EXCEL_GUIDE:-false}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
HASH="$(echo "${SOURCE}::${DEAL_TYPE}" | shasum -a 256 | cut -c1-8)"
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

# One mkdir per agent-output dir actually written by the phases below.
# (phase3_5 removed — no phase writes it. Marquee lives under phase5_7,
# matching its Phase 5.7 number; dedup lives under phase5_5_dedup.)
mkdir -p "$RUN_DIR"/{phase1/proposals,phase2/votes,phase2_5/scans,phase3/qa,phase4/proposals,phase4/placement_votes,phase5/qa,phase5_5_dedup,phase5_7/marquee,phase6/drafts,phase6/descriptions,phase6/qa_descriptions,intermediate,extraction,evidence,logs,dataroom}
```

Write `$RUN_DIR/run_state.json` with initial state:
```json
{
  "run_id": "<RUN_ID>",
  "source": "<SOURCE>",
  "deal_type": "<DEAL_TYPE>",
  "objective_brief": "<OBJECTIVE>",
  "with_excel_guide": <WITH_EXCEL_GUIDE>,
  "started_at": "<ISO8601>",
  "phase": "0_setup",
  "last_completed_checkpoint": null,
  "skill_version": "v2.1.0"
}
```

Initialize `$RUN_DIR/logs/run_log.txt` for verbose logging.

## 4. Phase 1 — Objective Solidification

**Goal:** transform thin user objective into rich, internet-grounded, consensus-validated specification. The full procedure is in §4.1–§4.4 below.

### 4.1 Source-folder shape inventory

Call (shallow = Phase 1 quick scan, no hashing):
```bash
python3 scripts/scan_folder.py --source "$SOURCE" --run-dir "$RUN_DIR" --shallow
```

`scan_folder.py` writes the shape inventory to `$RUN_DIR/intermediate/file_manifest.json`
(the script has no `--output` flag — output path is fixed under `--run-dir`). Read the
shape inventory from `$RUN_DIR/intermediate/file_manifest.json`. It lists folder names +
file counts and per-file metadata across the source folder.

### 4.2 Spawn 3 research agents in parallel

Spawn via `Task()` with `subagent_type: dr2-obj-researcher` (3 parallel instances per §0.5 swarm convention)`. ALL THREE IN PARALLEL (single message, 3 tool calls).

Each agent's prompt includes:
- The user's `--objective` brief verbatim
- The user's `--deal-type` value verbatim
- Contents of `references/deal_types.md` (the full file — researchers must internalize
  the deal-type's audience definition and hard-exclusion categories so they don't
  later propose "Relevant scope" categories that contradict the categorical excludes)
- Contents of `$RUN_DIR/intermediate/file_manifest.json` (the shallow shape inventory)
- Instruction to output a structured Markdown to `$RUN_DIR/phase1/proposals/<agent_id>.md`
- Authorization to use WebSearch + WebFetch for grounding

WAIT for all 3 to complete before proceeding.

### 4.3 Synthesize

Spawn `Task()` with `subagent_type: dr2-obj-synthesizer`. Prompt includes:
- Paths to all 3 proposals
- The user's `--deal-type` value
- Contents of `references/deal_types.md`
- Instruction to read all three proposals AND to paste the deal-type's
  "Objective-string augmentation" verbatim into §3 (Buyer profile) and §5
  (Out-of-scope) of the synthesized output
- Output path: `$RUN_DIR/phase1/SOLIDIFIED_OBJECTIVE.md`

Read the synthesized result. If the synthesizer's metadata indicates substance convergence <60% or >2 open questions, dispatch ONE blind re-run of all 3 researchers (same prompts, no feedback) and re-synthesize. If still divergent → HALT per §11.

### 4.4 Checkpoint

Update `run_state.json`:
```json
{ "phase": "1_objective_solidified", "last_completed_checkpoint": "phase1_synthesis_complete" }
```

Log to `logs/run_log.txt` and proceed to Phase 2.

## 5. Phase 2 — Inclusion Deliberation (Asymmetric Veto, No Loop)

**Goal:** for every file, decide INCLUDE vs EXCLUDE via **asymmetric** 3-agent blind
consensus. **Any single EXCLUDE vote wins. No re-dispatch loop.** This is a v2.1
structural change from v2.0's unanimous-or-loop model — see DESIGN.md for rationale.

The intuition: v2.0's "give borderline files 5 chances to find unanimity" produced
a too-permissive dataroom that included every file at least one agent thought might
be relevant. v2.1's "any single expert excludes → file is out" produces the tight
"guilty until proven needed" posture the boss-criticism-proof contract requires.
The Phase 3 fresh-eyes QA loop is the recovery mechanism for over-aggressive cuts —
not a Phase 2 re-deliberation loop.

### 5.1 Pre-flight — full file manifest

```bash
python3 scripts/scan_folder.py --source "$SOURCE" --run-dir "$RUN_DIR"
```

Full recursive scan + per-file SHA-256 hashing is the DEFAULT (no `--shallow`); there
are no `--recursive`/`--hash`/`--output` flags. The script writes the full manifest to
`$RUN_DIR/intermediate/file_manifest.json` (overwriting the Phase 1 shallow shape file).
Produces deterministic `file_id` per file (SHA-256 prefix), detects encrypted/zero-byte/
unsupported files (these carry a non-`extracted` `inclusion_in_extraction` value and never
reach the deliberation swarm).

### 5.2 Extraction

`extract_text.py` and `ocr_and_vision.py` are PER-FILE scripts (one file per call,
keyed by `--source <path> --file-id <id> --run-dir`). There is no batch/manifest mode.
Read `$RUN_DIR/intermediate/file_manifest.json` into memory and loop over the entries
whose `inclusion_in_extraction == "extracted"`, using each entry's `source_path` and
`file_id`:

```bash
python3 - <<'PY'
import json, subprocess, pathlib
run_dir = "$RUN_DIR"
manifest = json.load(open(f"{run_dir}/intermediate/file_manifest.json"))
scripts = pathlib.Path("scripts")
for f in manifest["files"]:
    if f.get("inclusion_in_extraction") != "extracted":
        continue
    src, fid = f["source_path"], f["file_id"]
    # 1) native text extraction → extraction/<file_id>/extraction.json
    subprocess.run(["python3", str(scripts/"extract_text.py"),
                    "--source", src, "--file-id", fid, "--run-dir", run_dir], check=True)
    # 2) OCR + vision-bridge request emission (batch mode = non-blocking)
    subprocess.run(["python3", str(scripts/"ocr_and_vision.py"),
                    "--source", src, "--file-id", fid, "--run-dir", run_dir,
                    "--vision-mode", "batch"], check=True)
PY
```

Native text where possible. PDF pages with low OCR confidence or no extractable text are
OCR'd and, when still weak, emit a vision-bridge request under
`$RUN_DIR/intermediate/vision_bridge/requests/` (batch mode is non-blocking — it writes
the request and returns).

Then spawn vision-capable `Task()` sub-agents to fulfill the pending bridge requests per
the v1.1.0 vision-bridge protocol, writing responses to
`$RUN_DIR/intermediate/vision_bridge/responses/`. After responses are written, rehydrate
once for the whole run (rehydrate is run-level, not per-file):
```bash
python3 scripts/ocr_and_vision.py --rehydrate --run-dir "$RUN_DIR"
```

### 5.3 Per-file deliberation (batched, asymmetric, single-pass)

Read `file_manifest.json` into memory. For each evaluable file (skip already-logged in `phase2/inclusion_log.csv`):

**Batch processing:** process files in batches of B=5. Per batch:

Spawn 3 deliberation agents per file IN PARALLEL via `Task()` —
`subagent_type: dr2-inclusion-deliberator` x 3, with model overrides per §0.5
(opus, sonnet, opus). For B=5 files this is 15 parallel `Task()` calls in one
message.

Each agent's prompt includes:
- The file's full extracted text + vision summary from `$RUN_DIR/extraction/<file_id>/extraction.json`
- The file's filename + source path
- Contents of `$RUN_DIR/phase1/SOLIDIFIED_OBJECTIVE.md`
- The active `--deal-type` value
- Contents of `references/deal_types.md` (the FULL file — the deliberator runs
  the categorical-exclusion fast path against the active deal-type's
  `hard_exclusions` BEFORE any general deliberation; see agent definition)
- Output path: `$RUN_DIR/phase2/votes/<file_id>/<agent_id>.json`
- The blindness invariant (do not reference other agents)
- The asymmetric-consensus rule (any single EXCLUDE wins; no re-dispatch — agent's
  judgment is final and binds the consensus)
- The default-EXCLUDE-on-borderline rule (v2.1 deliberators do NOT lean include
  on ambiguity)
- Privilege checklist (flag for Phase 2.5, but Phase 2 decision is relevance-only)

WAIT for all batch votes to land on disk.

### 5.4 Asymmetric consensus check (per file in batch)

For each file, read all 3 votes and apply ASYMMETRIC consensus:

- **All 3 INCLUDE:** copy source file to `$RUN_DIR/dataroom/<filename>` (apply
  `(2)`, `(3)` suffix on collision). Append to `phase2/inclusion_log.csv` with
  the three votes' reasoning compiled.
- **ANY 1+ EXCLUDE:** file is **EXCLUDED**. Log to `phase2/exclusion_log.csv`
  with each excluding agent's reasoning AND the including agents' reasoning (so
  Phase 3 QA can later second-guess if needed). No re-vote. No second chance.

**There is no "split → re-dispatch" path in v2.1.** Any single dissent excludes
the file. The Phase 3 fresh-eyes loop catches over-aggressive cuts by surfacing
them via the inclusion-QA workflow.

### 5.5 Checkpoint

Update `run_state.json` after every batch:
```json
{ "phase": "2_inclusion", "last_completed_checkpoint": "phase2_batch_N_complete" }
```

Once manifest is exhausted, advance to Phase 2.5.

### 5.6 What v2.0's K=5 re-dispatch did vs what v2.1 does

| v2.0 behavior | v2.1 behavior |
|---|---|
| Split → blind re-dispatch up to 5 times | No re-dispatch; first split kills the file |
| K=5 re-runs at 3 agents each = up to 15 extra Opus calls per disputed file | 3 Opus calls per file, period |
| Conservative-include heuristic in deliberator prompt | Default-EXCLUDE-on-borderline in deliberator prompt |
| Disputed-after-5 files logged to `phase2/disputed/` | No `phase2/disputed/` directory exists in v2.1 |
| Avg run: ~3-4 hours, ~70-75% file retention rate | Avg run: ~1.5-2 hours, ~50-60% file retention rate |

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

**Goal:** catch Phase 2 errors with fresh-eyes review. The full procedure is in §7.1–§7.3 below.

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

Create the sub-folder skeleton in `$RUN_DIR/dataroom/`. Each taxonomy folder's
`full_label` already includes the `"NN <name>"` space-separated prefix — use it
VERBATIM (do NOT reconstruct an underscore form):
```bash
jq -r '.folders[].full_label' "$RUN_DIR/phase4/TAXONOMY.json" | while IFS= read -r label; do
  mkdir -p "$RUN_DIR/dataroom/$label"
done
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

## 9.5. Phase 5.5 — Intra-Folder Dedup Pass

**Goal:** within each sub-folder, collapse near-duplicates (multiple drafts /
redlines / dated versions of the same conceptual document) to the canonical
version. This is what cut v2.0's Title folder from 22 → 8 in the boss's edits.

### 9.5.1 Cluster identification

For each sub-folder, the orchestrator (main Claude session) groups files into
near-duplicate clusters using filename heuristics:

- Files sharing a normalized stem (case-folded, punctuation-stripped, trailing
  "FINAL"/"Executed"/"Signed"/redline markers stripped, dated suffixes stripped)
- Files differing only by date suffix (`*2024.11.08.xlsx` vs `*2025.03.01.xlsx`
  vs `*2025.03.24.xlsx` — all three are versions of the same model)
- Files differing only by version marker (`v1`, `v2`, `Rev.0`, `Rev.1`, `(2)`, `(3)`)

A cluster has ≥2 files. Singleton files (no near-duplicates) skip Phase 5.5
entirely — they remain in the folder unchanged.

Write cluster groupings to `phase5_5_dedup/clusters.json`.

### 9.5.2 Per-cluster canonical selection (batched)

For each cluster, spawn `dr2-inclusion-deliberator` x 3 in a SPECIAL MODE
("dedup-canonical" — same agent, different prompt content) per §0.5 model mix.

Each agent's prompt includes:
- The cluster's full file list with extraction summaries
- The folder context (which folder these files live in)
- The active `--deal-type`
- Output path: `$RUN_DIR/phase5_5_dedup/clusters/<cluster_id>/<agent_id>.json`
- Instruction: identify which ONE file in the cluster is the canonical version
  (most-recent dated, "FINAL"/"Executed"/"Signed", recorded if applicable) and
  which files should be excluded as redundant.

Output schema:
```json
{
  "agent_id": "<id>",
  "cluster_id": "<id>",
  "canonical_filename": "<filename>",
  "exclude_filenames": ["<filename>", ...],
  "reasoning": "<paragraph>",
  "confidence": 0.0-1.0
}
```

### 9.5.3 Consensus rule for dedup

Unanimous-or-keep-all (NOT asymmetric here — dedup is a "select winner" task,
asymmetric-veto applied to "select" produces "everyone disagrees, nobody wins"
which is the wrong default):

- **All 3 pick the SAME canonical:** keep the canonical, exclude all the
  redundant siblings. Excluded files move from `dataroom/<folder>/<filename>`
  to `phase5_5_dedup/excluded/<folder>/<filename>` and log to
  `phase5_5_dedup/dedup_log.csv`.
- **Disagreement on canonical (any spread):** KEEP ALL files in the cluster.
  Log to `phase5_5_dedup/kept_cluster.csv` with all three agents' reasoning.
  This is the safe default — when reviewers disagree about which version is
  canonical, ship all versions.

There is no re-dispatch loop.

### 9.5.4 Checkpoint

```json
{ "phase": "5_5_dedup", "last_completed_checkpoint": "phase5_5_complete" }
```

## 9.7. Phase 5.7 — Marquee Prefix

**Goal:** within each sub-folder, identify the canonical (`_A__`) and runner-up
(`_B__`) marquee documents and apply the prefix in the copy.

This convention works because underscores sort before letters and digits, so
prefixed files float to the top of Finder's alphabetical sort. Your boss applied
this convention by hand on the Ascent dataroom; v2.1 automates it.

### 9.7.1 Per-folder marquee selection (asymmetric, no loop)

For each sub-folder, spawn `dr2-marquee-classifier` x 3 in parallel per §0.5
(opus, sonnet, opus). Each gets:

- The sub-folder name
- The active `--deal-type` and the §3 Buyer profile from SOLIDIFIED_OBJECTIVE.md
- The full file list currently in that sub-folder (post-dedup), with the
  one-sentence content summary per file (from Phase 6 descriptions if already
  generated, else from extraction)
- Output path: `$RUN_DIR/phase5_7/marquee/<folder_slug>/<agent_id>.json`

Each agent independently picks `marquee_a` (or null) and `marquee_b` (or null)
per the schema in `dr2-marquee-classifier.md`.

### 9.7.2 Asymmetric consensus

For each sub-folder:

- **All 3 agents pick the SAME `_A__` file (none null):** rename the file in
  the dataroom by prefixing `_A__` to the original filename. Log to
  `phase5_7/marquee_log.csv`.
- **Any single agent declined OR picked a different filename:** NO `_A__`
  applied in this sub-folder. Folder remains unprefixed for that slot.

Same rule for `_B__`. If `_A__` is unset (no consensus), `_B__` is also unset
(cannot have a runner-up to nothing).

There is no re-dispatch loop. Single dissent kills the prefix.

### 9.7.3 Prefix application

Rename the elected file in the dataroom:
```
dataroom/<folder>/<original_filename>  →  dataroom/<folder>/_A__<original_filename>
```

This is a documented exception to non-negotiable #1 (files keep original names).
The source folder is still untouched — the rename is only on the COPY inside
the run dir's dataroom.

### 9.7.4 Checkpoint

```json
{ "phase": "5_7_marquee", "last_completed_checkpoint": "phase5_7_complete" }
```

## 10. Phase 6 — Excel Artifact + Manual Review Markdown

**v2.1 default:** the Excel guide is **OPT-IN**. If the user did NOT pass
`--with-excel-guide`, skip §10.1–§10.3 entirely. §10.4 (Manual Review markdown)
and §10.5 (Final-ship copy) still run.

If `--with-excel-guide` was passed, run §10.1–§10.3 normally.

The motivation: v2.0's Excel guide consumed ~30 minutes of Phase 6 Opus work
and the boss removed it from the final delivery on the Ascent run. For most
outbound datarooms, the folder structure + filenames are self-explanatory and
counterparties navigate Finder directly. Opt-in is the safer default.

### 10.1 Worksheet 1 — Data Room Guide

Spawn `dr2-guide-drafter` x 3 in parallel per §0.5. Each reads `SOLIDIFIED_OBJECTIVE.md` + `TAXONOMY.json` + dataroom file counts. Each writes a draft to `phase6/drafts/<agent_id>.md`.

Spawn one `dr2-guide-synthesizer` (default opus) — merges into `phase6/ws1_guide.md`.

Spawn one `dr2-guide-qa` (default opus) — reads the synthesized draft + SOLIDIFIED_OBJECTIVE + actual dataroom listing. Issues PASS or returns specific fix-list. Re-loop guide-synthesizer with fixes. Cap: 10 iterations → HALT.

### 10.2 Worksheet 2 — File Tree

For each file in the final classified dataroom, spawn `dr2-description-drafter` x 3 per §0.5 (opus, sonnet, opus). Each writes a 1-sentence description of what the file IS (not what it MEANS). Output: `phase6/descriptions/<file_id>/<agent_id>.json`.

Consensus rule: substance similarity ≥90% on ≥2/3. If satisfied → synthesis (text merging done in main Claude session, not a separate agent) produces final description. If not → blind re-dispatch K=3 times. Still divergent → fallback to "filename + extracted document type" with a flag in the description.

After all descriptions assembled, spawn `dr2-description-qa` in batches for a final accuracy pass against extracted content. Wigum loop on fixes.

Once the drafters + QA have converged for a `file_id`, the orchestrator (main Claude session) MUST write the post-consensus description for that file to `phase6/descriptions/<file_id>/consensus.json` as a JSON object with exactly these fields: `{"file_name": "<original filename>", "description": "<final 1-sentence description>"}`. This is the producer step that §10.2.1 below reads — without it, the aggregation step finds no `consensus.json` and silently drops every file. The field names `file_name` and `description` MUST match what the §10.2.1 aggregator and `build_dataroom_guide_excel.py` expect.

#### 10.2.1 Aggregate descriptions into the ONE canonical file

The per-file consensus descriptions live scattered under
`phase6/descriptions/<file_id>/...`. Before the Excel build, merge them into ONE
canonical, filename-keyed JSON that `build_dataroom_guide_excel.py` consumes:

```bash
python3 - <<'PY'
import json, pathlib
run_dir = pathlib.Path("$RUN_DIR")
manifest = json.load(open(run_dir/"intermediate"/"file_manifest.json"))
id_to_name = {f["file_id"]: f["file_name"] for f in manifest["files"]}
final = {}
for fid_dir in (run_dir/"phase6"/"descriptions").iterdir():
    if not fid_dir.is_dir():
        continue
    # the orchestrator writes the post-consensus description as consensus.json
    consensus = fid_dir/"consensus.json"
    if not consensus.exists():
        continue
    rec = json.load(open(consensus))
    name = id_to_name.get(fid_dir.name, rec.get("file_name"))
    if name:
        final[name] = rec.get("description", "")
out = run_dir/"phase6"/"descriptions_final.json"
json.dump(final, out.open("w"), indent=2)
print(f"Wrote {len(final)} descriptions to {out}")
PY
```

This writes `$RUN_DIR/phase6/descriptions_final.json` — the canonical filename used
consistently in §10.3, in the script docstring, and as the script's documented input.

### 10.3 Excel build

```bash
python3 scripts/build_dataroom_guide_excel.py \
  --guide-md "$RUN_DIR/phase6/ws1_guide.md" \
  --descriptions-json "$RUN_DIR/phase6/descriptions_final.json" \
  --taxonomy-json "$RUN_DIR/phase4/TAXONOMY.json" \
  --dataroom-dir "$RUN_DIR/dataroom" \
  --output "$RUN_DIR/dataroom/<DataRoomName>_Guide_<date>.xlsx"
```

`phase6/descriptions_final.json` is the ONE canonical aggregated descriptions file
produced by the §10.2.1 aggregation step above (§10.2.1) — it maps each final filename to its
consensus one-sentence description. The script reads it via `--descriptions-json` and
keys descriptions by filename.

Style: Carbon-style header row, visual sub-folder grouping with outline levels, no formulas/hyperlinks/dropdowns.

### 10.4 Manual Review markdown (conditional)

If any of the buckets the phases actually emit is non-empty —
unable-to-evaluate files (derived from `intermediate/file_manifest.json`
entries whose `inclusion_in_extraction != "extracted"`, i.e. Phase 2 pre-flight
non-extractable files),
`phase3/qa_failed_unconverged.csv` (Phase 3 §7.2 K-exhaustion), or
`dataroom/00_Pending_Classification/` (Phase 4b §8.2 split-after-K) —
then:

(Note: there is NO `phase2/disputed/` bucket in v2.1 — Phase 2 is asymmetric
single-pass with no re-dispatch, so it never produces disputed-after-K files;
see §5.6. Phase 5 placement-QA K-exhaustion is already surfaced via the
`00_Pending_Classification/` bucket it returns files to.)

```bash
python3 scripts/build_manual_review_md.py \
  --run-dir "$RUN_DIR" \
  --output "$RUN_DIR/dataroom/Manual_Review_Required_<date>.md"
```

If all empty, do NOT write this file.

### 10.5 Final-ship copy

Compute `<DataRoomName>` from `SOLIDIFIED_OBJECTIVE.md` asset_identity field
(kebab-case, ASCII-safe, then Title-Cased with spaces for the final folder name —
e.g., `ascent-park-city` slug → `Ascent Park City Dataroom`).

```bash
FINAL_DIR="${SOURCE_PARENT}/${DATAROOM_NAME_PRETTY}"
cp -R "$RUN_DIR/dataroom" "$FINAL_DIR"
```

When `--with-excel-guide` was passed, the Excel file is already inside
`$RUN_DIR/dataroom/` from §10.3, so the recursive copy picks it up. When NOT
passed, the final dir contains only sub-folders + files (no Excel artifact at
root).

This is the shippable output. The skill's job is done.

```json
{ "phase": "complete", "last_completed_checkpoint": "phase6_complete", "final_output": "<FINAL_DIR>" }
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
✅ acos-dataroom-v2 v2.1.0 complete for "<asset name>"

Deal type: <DEAL_TYPE>
Final dataroom: <FINAL_DIR>
File count: <N> across <M> sub-folders
Excluded by Phase 2 categorical fast path: <X1>
Excluded by Phase 2 asymmetric veto: <X2>
Removed by Phase 2.5 (privilege): <Y>
Collapsed by Phase 5.5 dedup: <D>
Marquee-prefixed (_A__): <M_A>, runner-up (_B__): <M_B>
Excel guide: <included | not generated>
Files in manual review bucket: <Z>

Open the dataroom: file://<FINAL_DIR>
```

---

## References

- `DESIGN.md` — authoritative specification (this skill's contract)
- `references/deal_types.md` — **NEW in v2.1.0** — 6 deal types + categorical
  hard-exclusion lists + objective-string augmentations. Source-of-truth for
  the Phase 2 categorical-exclusion fast path.
- `references/privilege_markers.md` — catalog of privilege patterns (Phase 2.5)

*acos-dataroom-v2 v2.1.0 — autonomous, multi-model consensus, zero-defect data
room generation. Deal-type-aware categorical exclusion + asymmetric Phase 2
veto + dedup + marquee. Run end-to-end with one invocation; no human gates;
boss-criticism-proof on first cold look.*
