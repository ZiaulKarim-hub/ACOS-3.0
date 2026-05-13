# acos-dataroom-v2 — Design Specification

**Status:** DRAFT, awaiting user (Zee) review before any implementation begins.
**Author:** Claude (Opus 4.7).
**Date:** 2026-05-13.
**Companion docs:** `memory/project_acos_dataroom_v2.md` (project memory),
`memory/feedback_boss_no_intermediate_review.md` (the design constraint that
triggered this rewrite).

---

## 0. Why this document exists

v1 of `acos-dataroom` shipped output that required boss review of an Internal
Working Workbook to be acceptable. The boss refused to review the workbook
("I don't have time") and judged the unreviewed result harshly ("AI is a
piece of shit"). v1's quality model — "AI proposes, boss disposes via Excel"
— is structurally incompatible with the boss's actual behavior.

v2 inverts the trust model: **the skill itself is the quality enforcer.** No
human gates. No intermediate-review artifacts. The boss only ever sees the
final dataroom + a 2-worksheet Excel guide, and that final must be
criticism-proof on first cold look. The mechanism is multi-stage adversarial
consensus, modeled on `/acos-grader`.

---

## 1. Non-negotiables (invariants)

These are the load-bearing rules. Implementation MUST NOT violate any of them.
Each is traceable to the user's 2026-05-13 vision statement.

| # | Invariant | Rationale |
|---|---|---|
| 1 | **Files keep original names.** No renaming at any phase. | User explicit. |
| 2 | **All file operations are COPY.** Source folder is never modified. | User explicit (and v1 carries the same rule). |
| 3 | **Blind consensus in every swarm.** Agents within a swarm never see each other's outputs before voting. | User explicit. Prevents anchoring + cascade errors. |
| 4 | **Cognitive diversity via model mix.** No single-model swarm. Realistic mix on Claude: Opus + Sonnet + Opus, or Opus + Opus + Sonnet. | User explicit. Avoids correlated systematic blind spots. |
| 5 | **Default-EXCLUDE on irreducible disagreement.** If a swarm cannot reach unanimous concurrence after K iterations, the safe outcome is exclusion. | User explicit. Inclusion mistakes are catastrophic; exclusion mistakes are recoverable (file stays in source). |
| 6 | **No human gates.** Skill runs to completion autonomously. The only allowed escape hatch is the convergence failure HALT in §6. | User explicit. |
| 7 | **No intermediate artifacts the boss might be expected to review.** | User explicit. |
| 8 | **Boss-criticism-proof on first cold look.** | User explicit. The architectural target. |
| 9 | **Domain expertise baked into every deliberation agent.** Finance + private credit + private equity + real-estate lending. Not generic. | User explicit. |
| 10 | **Emergent taxonomy.** Sub-folder structure is designed per-dataroom by the classifier swarm, not loaded from a pre-baked per-deal-type template. | User explicit. v1's pre-baked taxonomies are abandoned. |
| 11 | **No external Anthropic API calls.** All Claude work routes through `Task()` sub-agents under the user's Max subscription. | Memory: `feedback_subscription_not_api`. Same constraint as v1.1.0+. |
| 12 | **Checkpoint after every consensus decision.** Multi-hour runs must survive crashes / interruptions. | User confirmed "run as long as needed" — implies resumability matters. |
| 13 | **No coarse pre-filter.** Every source file gets the 3-agent deliberation, regardless of folder. | User confirmed. |

---

## 2. Pipeline overview

```
┌────────────────────────────────────────────────────────────────────────┐
│ INPUT                                                                  │
│   --source <folder>                                                    │
│   --objective "<one-line brief, e.g., 'Sell the Ascent hotel'>"        │
│                                                                        │
│ (no other args. no wizard. no pause gates.)                            │
└────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 1 — OBJECTIVE SOLIDIFICATION (§3)                                │
│   3 research agents, blind consensus, internet-grounded.               │
│   Output: SOLIDIFIED_OBJECTIVE.md (the spec everything measures against)│
└────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 2 — INCLUSION DELIBERATION (§4)                                  │
│   3 finance-domain agents, blind, per-file INCLUDE/EXCLUDE vote.       │
│   Unanimous INCLUDE → file COPIED to flat dataroom folder.             │
│   K iterations of blind re-dispatch on disagreement.                   │
│   Output: dataroom/ (flat, original names)                             │
└────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 2.5 — PRIVILEGED-CONTENT SCANNER (§5)                            │
│   3 paranoid agents, ONLY look for privilege markers.                  │
│   Unanimous PASS to stay. Any single FLAG → file removed, logged.      │
└────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 3 — INCLUSION QA (§6)                                            │
│   3 QA agents review every survivor against deliberation transcripts.  │
│   Any FAIL → file returns to Phase 2 for re-deliberation.              │
│   Wigum loop until all agents PASS every file. Cap = 5 iterations.     │
└────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 4 — SUB-FOLDER CLASSIFICATION (§7)                               │
│   4a Taxonomy design: 3 agents propose emergent taxonomy → consensus.  │
│   4b Per-file placement: 3 agents pick sub-folder → blind consensus.   │
│   Output: dataroom/01_<name>/, dataroom/02_<name>/ … (no gaps)         │
└────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 5 — CLASSIFICATION QA (§8)                                       │
│   3 QA agents verify placement. Any FAIL → back to Phase 4.            │
│   Wigum loop until clean.                                              │
└────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 6 — EXCEL ARTIFACT (§9)                                          │
│   WS1: Data Room Guide (plain-English navigation guide)                │
│   WS2: File Tree (folder → sub-folder → file → description)            │
│   Multi-agent deliberation on descriptions + final QA pass.            │
└────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                  FINAL OUTPUTS (ship as-is to buyer)
                  • <SourceParent>/<DataRoomName>/                        (folder tree)
                  • <SourceParent>/<DataRoomName>/Dataroom_Guide_<date>.xlsx
```

---

## 3. Phase 1 — Objective Solidification

### 3.1 Goal

Transform a thin one-line user objective ("Sell the Ascent hotel") into a
**rich, internet-grounded, consensus-validated specification** of what the
dataroom is for and what an institutional buyer needs to evaluate the deal.
This is the ground truth that downstream phases measure relevance against.

### 3.2 Inputs

- `--objective` (one-line user brief)
- Source folder shape (top-level folder names, file counts per folder, sample
  filenames — NOT file contents at this phase)
- A 5-file high-signal sample: files whose names match patterns suggesting
  "deal-defining" docs (term sheet, purchase agreement, notice of sale, loan
  agreement, offering memo).

### 3.3 Agents

Three research agents, deployed via `Task()`:

| Agent | Model | Role |
|---|---|---|
| `obj-researcher-1` | Opus 4.7 | Senior PE research analyst lens |
| `obj-researcher-2` | Sonnet 4.6 | Institutional buyer / diligence-lead lens |
| `obj-researcher-3` | Opus 4.7 | Real-estate lending / restructuring specialist lens |

Each agent has tools: `Read, Glob, Grep, Bash, WebSearch, WebFetch`. They run
**in parallel, blind to each other**.

### 3.4 What each agent produces

Each writes a structured Markdown file to
`<run_dir>/phase1/proposals/<agent_id>.md` with these sections:

1. **Asset identity** — what is the specific asset / loan being transacted?
2. **Transaction nature** — what type of deal is this, in institutional
   terminology? (sale / participation / foreclosure auction / lender package
   / note sale / etc.)
3. **Buyer profile** — who is the likely buyer? What lens will they use?
4. **Relevant scope** — which physical / financial / legal artifacts MUST be
   in the dataroom for a buyer to underwrite?
5. **Out-of-scope** — what's in the source folder that's IRRELEVANT to this
   objective (e.g., docs for other collateral properties, internal-only
   strategy notes)?
6. **Web-sourced grounding** — what they learned from internet research,
   with URLs cited.
7. **Confidence note** — what's still uncertain and would change the
   solidified objective.

### 3.5 Consensus mechanism

A 4th agent, `obj-synthesizer` (Opus), reads all three proposals and produces
a final `SOLIDIFIED_OBJECTIVE.md`. Synthesis rules:

- **Substance convergence:** any claim asserted by ≥2 researchers is kept.
- **Singleton claims** with strong grounding (cited URL + plausibility) are
  flagged as "supplementary" and kept with the flag.
- **Singleton claims without grounding** are dropped.
- **Direct contradictions** are surfaced as `OPEN_QUESTIONS` in the
  solidified objective; the most conservative interpretation is adopted as
  the working assumption.

If after synthesis there are >2 open questions or substance convergence is
<60%, the synthesizer triggers ONE blind re-dispatch of all 3 researchers,
prompted only with the open questions. If still divergent after re-dispatch,
the run HALTS with a structured "objective could not be solidified" report
(this is the only non-convergence escape hatch in the skill).

### 3.6 Output

`<run_dir>/phase1/SOLIDIFIED_OBJECTIVE.md` — the canonical spec read by every
agent in Phases 2–6.

> **★ Design insight:** Phase 1 is the highest-leverage component in the
> entire skill. A weak solidified objective means every downstream
> classification decision is misaimed. We spend ~5-10 minutes here to save
> hours of downstream re-deliberation.

---

## 4. Phase 2 — Inclusion Deliberation

### 4.1 Goal

For every source file, decide INCLUDE (copy to flat dataroom folder) or
EXCLUDE (leave in source, log reason) via unanimous 3-agent consensus.

### 4.2 Pre-flight

Run `scripts/scan_folder.py` (port from v1, adapted):

- Recursive walk
- SHA-256 hashes → deterministic `file_id`
- Detect dupes, encrypted, password-protected, zero-byte, unsupported.
- Write `<run_dir>/intermediate/file_manifest.json`.

Unreadable files (encrypted / zero-byte / unsupported format) are placed
in an "unable-to-evaluate" bucket up front — they never reach the
deliberation swarm and are flagged in the final Excel under a separate
section "Files Requiring Manual Review."

### 4.3 Extraction

Run `scripts/extract_text.py` + `scripts/ocr_and_vision.py` (port from v1.1.0,
keep the bridge-file dispatch).

- Native text extraction for PDF / DOCX / XLSX / PPTX / TXT / MD / RTF.
- Image-only PDF pages and standalone images → bridge-file vision dispatch
  via `Task()` (no API key needed).
- Each file → `<run_dir>/extraction/<file_id>/extraction.json`.

### 4.4 Agents

Three deliberation agents per file:

| Agent | Model | Role profile |
|---|---|---|
| `inclusion-deliberator-1` | Opus 4.7 | Senior PE underwriter (institutional buyer mindset) |
| `inclusion-deliberator-2` | Sonnet 4.6 | Real-estate lending workout specialist |
| `inclusion-deliberator-3` | Opus 4.7 | Private credit / structured finance domain expert |

Each agent sees:
- `SOLIDIFIED_OBJECTIVE.md`
- The file's full extracted text + vision summary (from `extraction.json`)
- The file's filename and source path within the source folder
- An **explicit privilege checklist** ("if you see these markers, flag —
  but final privilege decision is Phase 2.5, your job here is relevance.")

Each agent produces a structured JSON vote at
`<run_dir>/phase2/votes/<file_id>/<agent_id>.json`:

```json
{
  "verdict": "INCLUDE" | "EXCLUDE",
  "confidence": 0.0-1.0,
  "reasoning": "<paragraph with snippet-anchored claims>",
  "relevant_to_objective": true|false,
  "evidence_snippets": ["<verbatim snippet 1>", "<verbatim snippet 2>"],
  "privilege_flag_for_phase_2_5": true|false,
  "open_questions": ["<question 1>"]
}
```

### 4.5 Consensus rule

For each file, after all 3 agents vote:

- **Unanimous INCLUDE:** file is COPIED to `<run_dir>/dataroom/`. Logged in
  `phase2/inclusion_log.csv`.
- **Unanimous EXCLUDE:** file stays in source. Logged with reasoning.
- **Split decision (2-1 either way):** blind re-dispatch. The 3 agents
  re-vote with NO information about the prior split — same prompt, same
  inputs. Up to K=5 iterations.
- **Still split after K iterations:** **default-EXCLUDE.** Logged with full
  iteration trail under `phase2/disputed/<file_id>.json`. Surfaced in the
  final Excel under "Files Requiring Manual Review."

### 4.6 Filename collision in flat dataroom

If two files from different source paths share an identical name, the
second-arriving file gets a numeric suffix BEFORE the extension:
`report.pdf` → `report.pdf` (first) and `report (2).pdf` (second). This is
the ONLY deviation from invariant #1 and is documented in the Data Room
Guide. The collision-resolved name carries through to Phase 4 placement.

### 4.7 Checkpointing

After every file's verdict is finalized, write to
`<run_dir>/run_state.json`:
```json
{ "phase": 2, "last_completed_file_id": "f_...", "files_remaining": N }
```
Resuming after crash skips files already in `inclusion_log.csv`.

---

## 5. Phase 2.5 — Privileged-Content Scanner

### 5.1 Goal

Catastrophic-failure-mode firewall. A privileged document leaking to a
buyer can waive attorney-client privilege, expose OKOA to malpractice
claims, and contaminate diligence with discoverable material. Zero
tolerance.

### 5.2 Scope

Runs ONLY on files in `<run_dir>/dataroom/` (Phase 2 survivors). Phase 2
agents may have flagged some files via `privilege_flag_for_phase_2_5: true`
— those get priority, but ALL files are scanned regardless.

### 5.3 Agents

| Agent | Model | Role |
|---|---|---|
| `privilege-scanner-1` | Opus 4.7 | Real-estate-PE in-house counsel lens |
| `privilege-scanner-2` | Sonnet 4.6 | Litigation discovery specialist lens |
| `privilege-scanner-3` | Opus 4.7 | Outside-counsel review lens |

Each agent gets one job and one job only: **read this file and decide if it
contains privileged content that must NOT ship to a buyer.**

Checklist they apply (loaded from `references/privilege_markers.md` —
authored as part of implementation):

- "Privileged & Confidential" / "Attorney-Client Privileged" headers/footers
- "Attorney Work Product" markings
- Communications to/from attorneys discussing legal strategy
- Internal legal memos analyzing litigation positions
- Settlement negotiation correspondence (pre-execution)
- Internal post-mortem of legal disputes
- Discovery production lists
- Outside-counsel invoices with substantive descriptions

### 5.4 Consensus rule

**ANY single agent flagging privilege → file is REMOVED from dataroom.** No
re-dispatch. No second chance. The asymmetric cost of a privilege leak vs.
a missing-file gap makes "false positive bias" the correct posture.

Removed files are logged to `<run_dir>/phase2_5/privileged_removed.csv` with
reasoning from each flagging agent. Surfaced in Excel under "Files Withheld
for Privilege Review."

### 5.5 Checkpointing

After each file's scan, append to `phase2_5/scan_log.csv`. Resumable.

> **★ Design insight:** Phase 2.5 deliberately violates the consensus
> symmetry of every other phase. Elsewhere we require unanimous concurrence
> to act; here we require unanimous concurrence to KEEP, and any single
> dissent removes. This asymmetry is the correct response to asymmetric
> harm: missing a privileged doc = catastrophic legal exposure; falsely
> removing a non-privileged doc = recoverable gap.

---

## 6. Phase 3 — Inclusion QA (Wigum Loop)

### 6.1 Goal

Catch errors from Phase 2 by replaying the inclusion decisions through a
fresh lens. Same architecture as `/acos-grader`'s QA loop.

### 6.2 Agents

| Agent | Model | Role |
|---|---|---|
| `inclusion-qa-1` | Opus 4.7 | Adversarial reviewer ("what's the strongest case this is wrong?") |
| `inclusion-qa-2` | Sonnet 4.6 | Completeness reviewer ("does this file actually serve the objective?") |
| `inclusion-qa-3` | Opus 4.7 | Coherence reviewer ("does the dataroom hang together as a complete package?") |

### 6.3 Per-file QA

For each file in `<run_dir>/dataroom/`, each QA agent reads:
- `SOLIDIFIED_OBJECTIVE.md`
- The file's extracted content
- The 3 Phase 2 deliberation votes + reasoning
- (For QA agent 3 only) the FULL current `dataroom/` listing for context

Each QA agent issues PASS or FAIL per file with reasoning.

### 6.4 Wigum loop

- All 3 PASS → file stays.
- ANY FAIL → file is returned to Phase 2 for **fresh blind re-deliberation**
  by 3 new deliberation agent instances (same models, no memory of prior
  votes). The QA failure reasoning is NOT shared with the deliberators —
  this is the "blind re-dispatch" pattern.
- After re-deliberation, the file's verdict is whatever the new swarm
  decides (could be EXCLUDE this time, in which case the file is moved out
  of `dataroom/`).
- Re-deliberated files go back through Phase 2.5 (privilege scan) if they
  re-enter `dataroom/`.

Loop cap: K=5 iterations per file. If still failing after 5 → file goes to
"Files Requiring Manual Review" bucket and is excluded from the dataroom.

### 6.5 Convergence rule

Phase 3 is "done" when ALL files in `dataroom/` PASS all 3 QA agents AND
no files are still in re-deliberation. Logged at `phase3/qa_pass_log.csv`.

---

## 7. Phase 4 — Sub-folder Classification

### 7.1 Goal

Design and execute a per-dataroom sub-folder taxonomy. No pre-baked
templates. The taxonomy emerges from what's actually in the dataroom.

### 7.2 Step 4a — Taxonomy design

Three classifier agents look at the FULL list of `dataroom/` files
(filenames + brief content summaries from Phase 2 extraction) and each
proposes a taxonomy:

```json
{
  "folders": [
    {"num": 1, "name": "Property Overview", "description": "..."},
    {"num": 2, "name": "Title & Recorded Documents", "description": "..."},
    ...
  ]
}
```

Taxonomy constraints (enforced in agent prompt + validated post-hoc):

- **Sequentially numbered 1..N, no gaps.**
- **No semantic duplicates** — "Property docs" + "Property-related" is
  illegal; the agent must merge them.
- **All-encompassing** — every file in `dataroom/` must fit at least one
  proposed folder.
- **Minimal count** — prefer fewer folders if all files still fit cleanly.
  Heuristic: ≤15 folders for any realistic dataroom; flag if >15.

A 4th agent, `taxonomy-synthesizer` (Opus), reads all three proposals and
produces a final taxonomy. Synthesis rules:

- **Concept convergence:** folder concepts appearing in ≥2 proposals are
  kept (renamed to the clearest of the three proposed names via short
  deliberation).
- **Singleton folders** are kept only if ≥1 file in `dataroom/` requires
  them.
- **Conflicting numbering** resolved by topic ordering (property→title→
  financial→legal→transaction, roughly).

Output: `<run_dir>/phase4/TAXONOMY.json`.

### 7.3 Step 4b — Per-file placement

For each file in `dataroom/`, 3 classifier agents independently pick a
sub-folder number from `TAXONOMY.json`. Unanimous concurrence → file is
MOVED (within `dataroom/`) to that sub-folder. Split → blind re-dispatch
K=5 times. Still split → file lands in a "pending" sub-folder at the top
level (`dataroom/00_Pending_Classification/`), surfaced in Excel under
"Files With Disputed Categorization."

### 7.4 Filename collisions within sub-folders

Same rule as §4.6 — suffix `(2)`, `(3)` on duplicate filenames.

---

## 8. Phase 5 — Classification QA

### 8.1 Goal

Wigum loop on placement. Identical pattern to Phase 3 but for sub-folder
placement instead of inclusion.

### 8.2 Agents

Three QA agents (Opus + Sonnet + Opus) each issue PASS/FAIL per file based
on the question "**is this file in the right sub-folder?**" Inputs: the
file's content, the file's current sub-folder, the full `TAXONOMY.json`.

### 8.3 Wigum loop

Same as Phase 3: any FAIL → back to Phase 4 for fresh blind placement
re-deliberation. Loop until clean. K=5 iteration cap.

Edge case: if the QA loop reveals the taxonomy itself is wrong (e.g., too
many files keep failing because no sub-folder fits them), the orchestration
script triggers a "taxonomy revision" — re-runs Step 4a with the
failing-file context, then re-places everything.

---

## 9. Phase 6 — Excel Artifact

### 9.1 Goal

Produce one Excel file that ships alongside the dataroom folder. Two
worksheets. Boss-criticism-proof.

### 9.2 Worksheet 1 — Data Room Guide

Plain English, accessible to a non-expert reader. Sections:

1. **Title** — "<Asset Name> Data Room Guide"
2. **About this data room** — one paragraph from `SOLIDIFIED_OBJECTIVE.md`,
   rewritten for an external reader.
3. **What's in this data room** — bulleted list of the sub-folders with one
   sentence each describing what's in each.
4. **How to navigate** — step-by-step "start here, then here, then here."
5. **File totals** — count of files in each sub-folder.
6. **A note on file naming** — disclosure that filenames are preserved as
   they were received (no renaming), and that collision-suffixed names
   `(2), (3)` indicate same-named source files from different folders.

Drafting process:
- 3 drafter agents (Opus + Sonnet + Opus) each produce a draft.
- A 4th synthesizer agent merges into one polished version.
- A 5th QA agent reads the synthesized draft AND `SOLIDIFIED_OBJECTIVE.md`
  AND the actual `dataroom/` listing, and either PASSES or returns a
  bullet list of specific fixes. Loop until PASS.

### 9.3 Worksheet 2 — File Tree

Hierarchical listing:

| Sub-folder | File | Brief description |
|---|---|---|

- Sub-folder column uses visual grouping (blank on repeated rows, like v1).
- Files listed within sub-folder are sorted alphabetically.
- "Brief description" is one sentence describing what the file is — not
  what it MEANS, just what it IS. ("First American title commitment dated
  Mar 12, 2024.") No commentary, no risk flags, no inferences.

Brief description generation:
- 3 description agents (Opus + Sonnet + Opus) each produce a description
  per file, BLIND to each other.
- Consensus: ≥2/3 substance convergence (LLM-judge similarity ≥90%) AND
  no factual conflicts → synthesizer produces final description.
- Disagreement → blind re-dispatch K=3 times. Still disagreeing → the
  description defaults to filename + extracted document-type, with a flag.

A final QA pass reads every description against the actual file content and
either PASSES or returns fixes. Wigum loop to clean.

### 9.4 Excel output

Filename: `<DataRoomName>_Guide_<YYYY-MM-DD>.xlsx`

Location: inside `<DataRoomName>/` at the top level (same folder as
sub-folders 01, 02, …).

Companion artifact (conditional): if ANY file ended up in the manual-review
bucket (encrypted, zero-byte, over-size, unsupported, K-iteration-exhausted
inclusion or placement disputes), the skill ALSO writes
`<DataRoomName>/Manual_Review_Required_<YYYY-MM-DD>.md` — a plain markdown
file listing those files with filename / source path / reason / recommended
action. NOT a buyer-facing artifact. Operator-only audit trail. If the
bucket is empty, this file is not written.

Styling: clean, professional. Carbon-style header row (dark grey
background, white bold text), visual sub-folder grouping with outline
levels (collapse/expand). No formulas. No hyperlinks. No dropdowns.

---

## 10. Agent specifications summary

| Agent name | Model | Used in | Tools |
|---|---|---|---|
| `obj-researcher-1/2/3` | Opus/Sonnet/Opus | Phase 1 | Read, Glob, Grep, Bash, WebSearch, WebFetch |
| `obj-synthesizer` | Opus | Phase 1 | Read, Write |
| `inclusion-deliberator-1/2/3` | Opus/Sonnet/Opus | Phase 2 | Read, Bash |
| `privilege-scanner-1/2/3` | Opus/Sonnet/Opus | Phase 2.5 | Read, Bash |
| `inclusion-qa-1/2/3` | Opus/Sonnet/Opus | Phase 3 | Read, Bash |
| `taxonomy-designer-1/2/3` | Opus/Sonnet/Opus | Phase 4a | Read, Write |
| `taxonomy-synthesizer` | Opus | Phase 4a | Read, Write |
| `placement-classifier-1/2/3` | Opus/Sonnet/Opus | Phase 4b | Read, Bash |
| `placement-qa-1/2/3` | Opus/Sonnet/Opus | Phase 5 | Read, Bash |
| `guide-drafter-1/2/3` | Opus/Sonnet/Opus | Phase 6 WS1 | Read, Write |
| `guide-synthesizer` | Opus | Phase 6 WS1 | Read, Write |
| `guide-qa` | Opus | Phase 6 WS1 | Read |
| `description-drafter-1/2/3` | Opus/Sonnet/Opus | Phase 6 WS2 | Read, Bash |
| `description-qa` | Opus | Phase 6 WS2 | Read |

Total distinct agent role definitions: 14.

> **★ Design insight:** Agent role definitions are stored as `.claude/agents/
> *.md` files (one per role) so the model assignments and prompts live in
> first-class native Claude Code primitives. The orchestration script
> spawns instances via `Task()` and can vary the model at spawn time if
> the model profile system overrides defaults.

---

## 11. Consensus & Wigum-loop mechanics (consolidated)

### 11.1 "Blind" defined

When a swarm of N agents votes, no agent in the swarm receives:
- Any other agent's vote
- Any prior iteration's vote (in re-dispatch)
- Any QA feedback explaining why a prior round failed

What they DO see: the same prompt, the same inputs, every time. The
re-dispatch is structurally identical to the first dispatch — only the
random seed in model decoding changes.

### 11.2 Consensus rule (universal across phases)

| Phase decision type | Rule |
|---|---|
| Inclusion (Phase 2) | Unanimous (3/3) for INCLUDE; otherwise EXCLUDE |
| Privilege (Phase 2.5) | Unanimous (3/3) PASS to keep; any FLAG removes |
| QA pass (Phase 3, 5) | Unanimous (3/3) PASS; any FAIL triggers re-deliberation |
| Taxonomy design (Phase 4a) | Synthesis-by-majority from 3 proposals |
| Placement (Phase 4b) | Unanimous (3/3) on sub-folder; otherwise re-dispatch |
| Description (Phase 6 WS2) | LLM-judge ≥90% substance similarity ≥2/3 |
| Guide QA (Phase 6 WS1) | Single QA agent PASS |

### 11.3 Re-dispatch cap K

K=5 across the skill, except K=3 for description re-dispatch (descriptions
are lower-stakes — defaulting to "filename + doc type" is acceptable).

### 11.4 Convergence failure HALT

The only path that surfaces work to the user (Zee) outside the planned
end-state. Triggered when:
- Phase 1: synthesizer cannot converge after 1 re-dispatch.
- Phases 2, 3, 4b, 5: K=5 iterations exhausted (these are LOGGED but do
  NOT halt the run — the failing files go to "manual review" buckets).
- Phase 6: QA loop runs >10 iterations (sanity cap).

On HALT, the skill writes `<run_dir>/HALT_REPORT.md` with the specific
unconverged decision and exits with a non-zero code.

---

## 12. State, resumability, checkpoints

### 12.1 Run directory layout

**Location:** the audit trail is created in the directory the user invokes
`/acos-dataroom-v2` FROM (`$(pwd)`), NOT next to the source folder. This
keeps internal deliberation / evidence material out of Dropbox-synced source
locations and consolidates all run audit trails under the operator's
local workspace.

```
<invocation_pwd>/_acos_dataroom_v2_output/run_<YYYYMMDD_HHMMSS>_<short_hash>/
├── run_state.json                # current phase + checkpoint
├── phase1/
│   ├── proposals/                # 3 researcher outputs
│   ├── SOLIDIFIED_OBJECTIVE.md
│   └── synthesis_log.md
├── intermediate/
│   ├── file_manifest.json
│   └── extraction/<file_id>/extraction.json
├── phase2/
│   ├── votes/<file_id>/<agent>.json
│   ├── inclusion_log.csv
│   └── disputed/<file_id>.json
├── phase2_5/
│   ├── scan_log.csv
│   └── privileged_removed.csv
├── phase3/
│   └── qa_pass_log.csv
├── phase4/
│   ├── TAXONOMY.json
│   ├── proposals/<agent>.json
│   └── placement_log.csv
├── phase5/
│   └── qa_pass_log.csv
├── phase6/
│   ├── ws1_guide.md
│   ├── ws2_descriptions.json
│   └── final.xlsx                # also copied to dataroom root
├── logs/run_log.txt
└── HALT_REPORT.md                # only if convergence failed
```

### 12.2 Final shippable output

`<source_parent>/<DataRoomName>/` (NEXT TO the source folder, NOT under the
audit-trail tree). Contains:
- Numbered sub-folder tree
- `<DataRoomName>_Guide_<date>.xlsx` at top level
- (Optional) `Manual_Review_Required_<date>.md` if any files ended up in the
  manual-review bucket
- Nothing else.

The split is deliberate: the **buyer artifact** lives near the source for
convenient sharing/copying; the **audit trail** lives under the invocation
workspace for separation of operational data from shippable product.

### 12.3 Resume on crash

Every consensus decision writes its log entry IMMEDIATELY. Resume logic:

1. Read `run_state.json` → current phase.
2. Within phase, read the phase's main log (`inclusion_log.csv`,
   `qa_pass_log.csv`, etc.).
3. Skip any decision already logged.
4. Continue from the next pending decision.

Phase 1 is non-resumable mid-phase (whole-phase atomic) — too fast to
matter. Everything else is per-decision resumable.

---

## 13. Edge cases

| Case | Handling |
|---|---|
| Encrypted PDF (password-protected) | Goes to "unable-to-evaluate" bucket pre-Phase 2. Surfaced in Excel under "Files Requiring Manual Review." |
| Zero-byte file | Same — pre-Phase 2 bucket. |
| Unsupported extension (.eml, .msg, .zip) | Same — pre-Phase 2 bucket. v2 inherits v1's out-of-scope list. |
| File >50 MB | Same — pre-Phase 2 bucket (token cost prohibitive). |
| Filename collision in flat dataroom | `(2)`, `(3)` suffix per §4.6 — only deviation from "no rename" rule. |
| Single file gets 5 conflicting verdicts across re-dispatches (true ambiguity) | Default-EXCLUDE per §4.5. Logged with full trail. |
| Phase 2 produces empty dataroom (every file excluded) | HALT with a "no files passed consensus" report. Probably indicates a wrong objective; user should review and re-run. |
| Phase 4a taxonomy synthesizer produces >15 sub-folders | Synthesizer is re-prompted with "consolidate to ≤15." Up to 2 re-prompts. If still >15 → ship as proposed but flag. |
| WebSearch / WebFetch quota exhausted in Phase 1 | Researcher agents degrade gracefully — produce proposal based on source-folder context only, with explicit "no web grounding available" flag. |

---

## 14. Open questions — RESOLVED (2026-05-13)

User reviewed and approved all 5 open questions on 2026-05-13.

1. **Output folder naming.** RESOLVED: auto-naming default from solidified
   objective. Format `<source_parent>/<asset_name>_Dataroom/`. The asset
   name comes from `SOLIDIFIED_OBJECTIVE.md` Phase 1 output. No
   `--data-room-name` CLI flag in v2.
2. **HALT_REPORT escape hatch triggers.** RESOLVED: current balance retained.
   Halts only on (a) Phase 1 non-convergence after 1 re-dispatch, (b) Phase 6
   QA loop >10 iterations, (c) empty dataroom (every file excluded by
   Phase 2). Phases 2/3/4b/5 send failing files to the "manual review" bucket
   without halting the run.
3. **"Files Requiring Manual Review" bucket.** RESOLVED: separate markdown
   file `Manual_Review_Required_<YYYY-MM-DD>.md` at the dataroom top level,
   alongside the Excel. Excel stays minimal (2 worksheets only). The markdown
   lists: encrypted/password-protected, zero-byte, unsupported-extension,
   over-size, and K-iteration-exhausted disputed files. Each entry: filename,
   source path, reason, recommended action for Zee. Not a buyer-facing
   artifact — operator-only. If zero files end up in this bucket, the file is
   not written.
4. **Boss email auto-compose.** RESOLVED: SKIPPED entirely. No email
   artifact. The dataroom folder + Excel guide are the only outputs.
   Rationale: minimum-surface-area discipline — every additional artifact is
   another surface for the boss to criticize.
5. **First real test.** RESOLVED: re-run on the Ascent Park City source
   folder for head-to-head v1-vs-v2 comparison. Same source data → directly
   comparable outputs. Rebuilds credibility with boss after v1 failure.

---

## 15. Implementation plan (proposed task breakdown)

Once this design is approved, I'll set up tasks via TaskCreate covering:

1. Create `.claude/skills/acos-dataroom-v2/` skeleton (SKILL.md, scripts/, references/, tests/)
2. Port + adapt v1 scripts: `scan_folder.py`, `extract_text.py`, `ocr_and_vision.py`, `utils.py`
3. Author 14 agent definitions in `.claude/agents/`
4. Author `references/privilege_markers.md`
5. Build orchestration script `scripts/orchestrator.py` (or a Bash wrapper that invokes Claude main thread)
6. Build per-phase logic — Phase 1 first (proves the research-swarm pattern), then Phase 2 (proves the deliberation pattern), then 2.5/3/4/5 (variations on the same pattern), then Phase 6 (Excel)
7. Build checkpoint/resume logic
8. Build halt-handling
9. Write `tests/test_smoke.py` (10-file synthetic source folder)
10. Run on Ascent for v1-vs-v2 comparison (chosen as first dogfood deal — same source `/Users/zee/Library/CloudStorage/Dropbox-OkoaCapital/Okoa Loans - 2. Active/1. In HyperCore/Wolfgramm_Ascent_Beehive - Waldorf (30M)`)

Each task gets its own slice with its own evidence bundle.

---

*acos-dataroom-v2 — autonomous, multi-model consensus, zero-defect dataroom generation. Companion to project memory `project_acos_dataroom_v2.md` and feedback memory `feedback_boss_no_intermediate_review.md`.*
