---
name: acos-legal-analysis
description: Dual-mode legal analysis skill. Mode A runs real estate private equity lending diligence (loan docs, title, liens, SPE/entity, guarantors, franchise/management contracts, foreclosure mechanics). Mode B runs copyright and IP infringement analysis (ownership, substantial similarity, fair use, DMCA, damages, claim+defense maps). Spawns the legal-analyst agent. Produces a detailed legal-risk memo with citations AND, for OKOA-context deliverables, an IC-grade negotiation-strategy memo rendered via the OKOA Document Design (Brad) skill. Outputs are diligence support, NOT legal advice.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
---

# ACOS Legal Analysis

## Overview

A structured legal diligence skill that analyzes a folder of documents and produces **two complementary deliverables**:

1. **Detailed legal-risk memo** (`lending-report.md` / `ip-infringement-report.md`) — every assertion cited, every quote verbatim, every claim labeled fact/inference/argument. The defensible audit-trail document.
2. **IC-grade strategy memo** (`IC-memo.pdf`) — institutional-design negotiation-strategy document rendered via the `/acos-document-design-brad` design system. Offensive frame: what the deal team should DO with the legal conclusions. The deliverable for the OKOA Investment Committee.

Two analysis tracks:

- **Lending Mode** — real estate PE loan diligence (Okoa's primary use-case)
- **IP-Infringement Mode** — copyright / rights infringement analysis with balanced claim + defense mapping

The skill orchestrates; the heavy analysis runs inside the [legal-analyst](../../agents/legal-analyst.md) agent.

**IMPORTANT — disclaimer on every output:** Outputs are diligence support only, not legal advice, and do not form an attorney–client relationship.

---

## Why this skill produces a strategy memo, not just a risk memo

A diligence-only memo answers *"what can go wrong?"* but leaves the deal team to translate findings into action. The cost of that translation gap was observed empirically on the Ascent Park City run (2026-05-20): the depth memo was citation-perfect, but the user had to manually rebuild the negotiation strategy from the legal facts. The IC memo deliverable closes that gap by default.

The IC memo uses an **offensive frame** by default for OKOA-context lending diligence: the lender enters any post-foreclosure conversation as a new counterparty with leverage, not as an exposed party hoping the contract survives. The depth memo provides the legal grounding; the IC memo translates it into the deal team's playbook.

---

## Arguments

`$ARGUMENTS` may contain:

| Pattern | Effect |
|---------|--------|
| `<folder>` | Run auto-mode detection against `<folder>` |
| `<folder> --mode lending` | Force Mode A |
| `<folder> --mode ip-infringement` | Force Mode B |
| `<folder> --mode ip-infringement --party plaintiff` | Frame Mode B from plaintiff side (still produces balanced maps) |
| `<folder> --mode ip-infringement --party defendant` | Frame Mode B from defendant side (default for Okoa-adjacent use) |
| `<folder> --question "<focused question>"` | Scope analysis to a specific legal question (e.g., "does foreclosure wipe out the franchise agreement?") |
| `<folder> --counterparty-asserts "<assertion>"` | Tells the agent what the other side is claiming so it can build a Claim-vs-Reality rebuttal |
| `<folder> --no-ic-memo` | Skip Phase 5 (IC strategy memo). Default behaviour for OKOA-context runs is to produce it. |
| `<folder> --output-dir <path>` | Override default session output to a specific directory (e.g., `~/Documents/OKOA/<deal>_Analysis_<date>/`) |
| `resume <session-id>` | Resume / re-open a prior session |
| `status` | List all legal-analysis sessions |

---

## Protocol

### Phase 0 — Parse Arguments & Session Init

**0.1 Handle `status`:** List all sessions under `.acos/sessions/legal-analysis/`. For each, show `session-id | mode | folder | status | date`. Then STOP.

**0.2 Handle `resume <session-id>`:** Read `session-manifest.yaml` under `.acos/sessions/legal-analysis/<session-id>/`. Print current state and offer to re-run a specific phase. Skip to the requested phase.

**0.3 Handle new run:** Validate `<folder>` exists and is readable. If not, STOP and ask the user for a valid path.

Generate session id: `la-{YYYYMMDD}-{HHMMSS}`. Default session dir is `.acos/sessions/legal-analysis/{session_id}/` unless `--output-dir` was given. Create the directory with:

- `session-manifest.yaml` (from template)
- `inventory.yaml` (empty, Phase 1 fills it)
- `findings-manifest.yaml` (empty, Phase 3 fills it)
- `extracted-text/` (for pre-extracted PDF text)
- `qa/` (for citation-QA artifacts)

**0.4 Mode detection (if `--mode` not given):** Glob the folder and apply these heuristics:

| Signal | Implies |
|--------|---------|
| Files matching `note`, `mortgage`, `deed_of_trust`, `loan_agreement`, `guaranty`, `title_commitment`, `operating_agreement`, `franchise_agreement`, `management_agreement`, `notice_of_default`, `foreclosure_report` | Mode A (lending) |
| Files matching `cease_and_desist`, `dmca`, `infringement`, `copyright`, `registration_cert`, two media / code works side-by-side | Mode B (IP) |
| Both | Run Mode A first, then Mode B |
| Neither | STOP and ask user to specify mode or confirm folder contents |

Record the detected mode in `session-manifest.yaml`.

**0.5 Party framing (Mode B only, if not given):** Use AskUserQuestion to determine plaintiff / defendant / neutral framing.

**0.6 — NEW — Memory context read** (Mode A, OKOA-context only):

Before dispatching the legal-analyst, the orchestrator reads project memory to absorb audience and tone calibration:

- `~/.claude/projects/-Users-zee-Documents-Vibe-Coding-ACOS-3-0/memory/feedback_boss_no_intermediate_review.md` — Final deliverable must be boss-criticism-proof on first cold look
- `~/.claude/projects/-Users-zee-Documents-Vibe-Coding-ACOS-3-0/memory/feedback_internal_email_no_legal_explainers.md` — Don't condescend with legal-procedure explainers
- `~/.claude/projects/-Users-zee-Documents-Vibe-Coding-ACOS-3-0/memory/feedback_legal_analyst_metadata_confabulation.md` — Anti-confabulation discipline (added 2026-05-20)
- `~/.claude/projects/-Users-zee-Documents-Vibe-Coding-ACOS-3-0/memory/feedback_clickable_links.md` — Always provide clickable file links
- `~/.claude/projects/-Users-zee-Documents-Vibe-Coding-ACOS-3-0/memory/user_role.md` — Audience: PE-RE associate at Okoa

The orchestrator passes the substantive contents of these memories to the legal-analyst in the dispatch brief.

**0.7 — NEW — Pre-extract source PDFs** (Mode A):

Before dispatching the agent, the orchestrator pre-extracts text from key PDFs in the main thread using `pdftotext -layout`. For image-only PDFs (zero text extracted), it runs `tesseract` via `pdftoppm`. This avoids the Opus-subagent-PDF-timeout failure mode documented in [feedback_opus_subagent_timeouts.md]. Extracted text lands in `<session_dir>/extracted-text/`. The agent reads text files for fast scanning and opens the original PDFs only for citation verification of specific quotes.

---

### Phase 1 — Inventory, Gap Analysis & Anti-Confabulation Gate

Spawn the legal-analyst agent to:

1. Glob the target folder recursively
2. Classify every file into the taxonomy for the selected mode
3. Compare inventory against the mode's document checklist
4. Flag missing documents (severity HIGH if checklist-required, MEDIUM if standard-but-optional)
5. **NEW — Anti-confabulation gate:** identify candidate brand / party / asset / status identifications and ground each ONLY in source-document language. Cross-check against an authoritative current-state document (most recent appraisal, operating report, or status correspondence). Treat folder names and file names as marketing/loan-administration labels, NOT as legal facts. If the folder name says one thing but documents say another, REPORT what the documents say with a footnote about the discrepancy.
6. Write `inventory.yaml` and `missing-docs.yaml`

Before spawning, resolve the agent's model via `.claude/scripts/resolve-agent-model.sh legal-analyst`. Default model is **opus**.

Pass to the agent (in YAML envelope):

```yaml
mode: lending | ip-infringement
folder_path: <absolute path>
session_dir: <absolute path>
phase: inventory
question: <focused question if provided>
counterparty_asserts: <counterparty assertion if provided>
audience_calibration: <substantive content of memory files from Phase 0.6>
anti_confab_directive: |
  Brand/party/asset/status identifications come ONLY from source-document
  language. Folder and file names are NOT authoritative. Cross-check any
  current-state identification against an authoritative current-state
  document (most recent appraisal, operating report, or status memo).
  If documents in the folder say X and folder/file names suggest Y, report X
  with a footnote about the Y/X discrepancy. Do NOT assume Y based on
  naming convention.
```

Wait for return. Read `inventory.yaml`. Report counts to the user, including the brand/party/asset identifications the agent reached AND the source-document evidence for each.

---

### Phase 2 — Deep Read

Re-invoke the legal-analyst agent with `phase: deep-read`. The agent will:

1. Read every categorized document (PDFs in page ranges for files >10 pages, using the pre-extracted text where possible)
2. Build internal cross-references between documents (e.g. note amount ↔ mortgage amount ↔ title insurance amount)
3. Note discrepancies and ambiguities
4. Populate a per-document notes file in the session dir

Large folders: batch documents into groups of ~10 and spawn multiple parallel legal-analyst agents, each with a subset. Each writes to a subdirectory; Phase 3 merges.

---

### Phase 3 — Findings & Detailed Memo

Spawn legal-analyst with `phase: findings`. The agent:

1. Runs the full mode-specific framework (see agent definition):
   - Mode A: A1–A8 (chain of title, liens, entity, loan docs, leases, intercreditor, regulatory, missing-docs) PLUS A9 (franchise/management contracts) PLUS A10 (foreclosure mechanics) where applicable
   - Mode B: B1–B9
2. Populates `findings-manifest.yaml` — every finding with severity, category, citation (clickable file:// path, body-page number, section number), fact/inference/argument label, and counter_argument
3. Writes the detailed narrative:
   - Mode A: `lending-report.md`
   - Mode B: `ip-infringement-report.md`
4. Writes mode-specific supplemental files:
   - Mode A: `red-flags.yaml`
   - Mode B: `claim-map.yaml`, `defense-map.yaml`, `similarity-table.md`
5. Runs the **adversarial pass** — for every CRITICAL and HIGH finding, writes the counter-argument
6. **NEW — Counterparty Anticipation:** if `--counterparty-asserts` was given OR the agent identifies a likely counterparty negotiating posture, records the assertion, its components, and the rebuttal grounded in source documents **inline within `findings-manifest.yaml`** (under a `counterparty_rebuttal` block) — no separate artifact file. Phase 5 reads this block to assemble the IC-memo "Claim vs Reality" section.

Every markdown file must start with the **LEGAL DISCLAIMER** block.

---

### Phase 4 — Citation QA

Spawn a separate QA agent (`general-purpose`, Sonnet model for cost) with explicit instructions to:

1. Open each cited document and verify each quote against source
2. Verify page numbers via pdfinfo / form-feed-split extraction
3. Verify file paths resolve
4. Mark PASS / PASS_WITH_NOTE / FAIL_QUOTE_NOT_FOUND / FAIL_WRONG_PAGE / FAIL_MISALIGNED / FAIL_FILE_MISSING / INCONCLUSIVE per finding
5. **Verify negative claims** by exhaustive grep ("no Hilton/franchise/Tapestry references on title") — citation-QA against absence is mandatory because the legal-analyst agent cannot self-verify negatives
6. Output `qa/citations-qa-report.md` and `qa/findings-manifest-verified.yaml`

If FAIL count > 0, return failed findings to the legal-analyst for re-grounding (Wigum loop, cap at 3 iterations). Surface unresolved failures in the final SUMMARY.md.

---

### Phase 5 — IC Strategy Memo (NEW)

**Default behaviour for OKOA-context Mode A runs. Skipped if `--no-ic-memo` is set.**

The orchestrator (NOT the legal-analyst — this is a distinct deliverable) builds an IC-grade negotiation-strategy memo by **generating the HTML inline** from the `/acos-document-design-brad` design system tokens (no template file is read). When a counterparty assertion exists, the orchestrator assembles the assertion + rebuttal structure inline (verbatim assertion, what the counterparty is actually doing, and the response) — there is no separate YAML artifact for it. The IC memo's information architecture:

1. **Cover** — Property name (display-xl Cormorant), one-sentence subtitle naming the legal question + strategic deliverable ("survivability review with negotiation strategy"), property/brand/lender/date metadata grid, **Bottom Line callout** with offensive framing
2. **Deal Overview** — 3-cell metric grid ($Senior / $C-PACE-or-Junior / Key-Money-Target), parties table (party / role / entity / date)
3. **Survivability Matrix** — 4-column table: Document / Survives Foreclosure? / Authority / Exposure. ALL contracts under analysis (franchise, management, comfort letters) get a row.
4. **Side-by-side Findings** — two cards, lead with the WIN (Finding 01 = clean termination / lender protection / favorable provision with green pill), then the EXPOSURE (Finding 02 = does-not-survive / unfavorable / gap with coral pill)
5. **Claim vs Reality** — IF a counterparty assertion was given OR is implied by the deal context, dedicated section with the verbatim assertion, then 2-4 dot-bullets explaining what the counterparty is actually doing (referring to a comfort letter / asserting a negotiating posture / conflating different agreements / etc.) and how to respond
6. **OKOA's Core Position** — verbatim talking script the deal team can speak in the counterparty conversation. Quoted, italic, Cormorant Garamond.
7. **Leverage list** — 4-6 named leverage points, with the primary commercial lever highlighted (coral text). For hospitality: brand-upgrade-within-portfolio thesis if applicable. For real estate: completed-asset-value / market-positioning / capital-stack-status.
8. **Key Money & Fee Targets** — 3-column table (Term / Standard / OKOA Target). Standard rows for franchise/management deals: Key Money, Royalty Fee, Program Fee, Management Fee Base, Management Term, Incentive Fee, Owner Termination.
9. **Action Plan** — 5-7 numbered tactical steps with imperative verbs. Each step has a one-line title and a 2-3-sentence specific instruction.
10. **Supporting Source Documents** — dot-list of every cited document with clickable file:// link + section numbers referenced

**Rendering pipeline:**

1. Orchestrator generates the IC-memo HTML **inline** — there is no template file to read. Pull the `/acos-document-design-brad` design tokens (typography scale, color pills, Cormorant/Google-Fonts stack, @page rules) and assemble a single self-contained HTML document section-by-section per the information architecture above. Populate it with content extracted from `findings-manifest.yaml`, the inline counterparty-rebuttal structure (see Phase 5 below), and the substantive contract texts. The survivability matrix (IA section 3) is emitted inline as part of this HTML — it is an IC-memo section, not a separate artifact.
2. Orchestrator renders via Puppeteer to PDF using `/tmp/render-ic-memo.js` (preferCSSPageSize: true, margins from @page rule, printBackground: true)
3. Verify clickable links survived (grep raw PDF bytes for `/URI` entries — count and sample)

**Output:**
- `IC-memo.html` (single-file HTML, Google Fonts only)
- `IC-memo.pdf` (rendered, 7-12 pages typical)

---

### Phase 6 — Executive Summary & Handoff

The skill (not the agent) reads `findings-manifest.yaml` and produces a top-level `SUMMARY.md` with:

- Session metadata (mode, folder, date, session-id)
- **Bottom-line one-sentence answer** to the legal question (if `--question` was given)
- Counts by severity (CRITICAL / HIGH / MEDIUM / LOW / INFO) and QA verdicts
- Top 5 CRITICAL + HIGH findings with one-line descriptions and clickable citations
- Missing-doc summary (highest-priority chases)
- Recommended next steps (diligence, NOT legal advice)
- Standard disclaimer

Present clickable paths to the user for **both deliverables**:
- `IC-memo.pdf` — the primary IC-grade deliverable
- `lending-report.md` / `ip-infringement-report.md` — the detailed legal memo (appendix-level depth)
- `SUMMARY.md` — narrative summary
- `findings-manifest.yaml` / `red-flags.yaml` / `qa/citations-qa-report.md` — structured artifacts

Update `session-manifest.yaml` → `status: complete`.

---

## Session Directory Structure (Updated)

```
<session_dir>/                        # default .acos/sessions/legal-analysis/{session-id}/
                                      # OR --output-dir target (e.g., ~/Documents/OKOA/<deal>_Analysis_<date>/)
├── session-manifest.yaml             # metadata
├── inventory.yaml                    # file classification + brand/party/asset identifications with source evidence
├── missing-docs.yaml                 # gap analysis
├── findings-manifest.yaml            # structured findings
├── SUMMARY.md                        # exec summary (narrative entry point)
├── IC-memo.html                      # NEW — IC-grade strategy memo source (generated inline)
├── IC-memo.pdf                       # NEW — IC-grade strategy memo (PRIMARY deliverable for OKOA runs)
├── lending-report.md                 # detailed legal memo (Mode A — the detailed-memo deliverable)
├── ip-infringement-report.md         # Mode B — the detailed-memo deliverable
├── doc-notes/                        # per-document reading notes
├── extracted-text/                   # NEW — pre-extracted text from source PDFs
├── qa/
│   ├── citations-qa-report.md        # independent QA audit
│   └── findings-manifest-verified.yaml # findings with qa_verdict appended
├── red-flags.yaml                    # Mode A — CRITICAL + HIGH only
├── claim-map.yaml                    # Mode B
├── defense-map.yaml                  # Mode B
└── similarity-table.md               # Mode B
```

---

## Integration With Other Skills

- Programmatically invocable by loan-doc generator, credit-memo generator, data-extractor for legal-risk appendix
- The IC memo phase invokes `/acos-document-design-brad` design tokens directly and generates the IC-memo HTML inline (no template file)
- The citation-QA phase uses the same methodology as the `acos-grader` skill's dual-axis consensus

---

## Model & Performance

- Legal-analyst default model: **opus** (legal reasoning is the defining use case for the premium tier)
- Citation-QA agent: **sonnet** (mechanical verification, cost-optimized)
- IC memo rendering: main-thread Puppeteer (no agent dispatch)
- Recommended profile: `premium` or `auto`
- Expected runtime: 20–40 minutes for a full loan folder (200–500 pages), longer if Wigum loop fires in Phase 4

---

## Safety & Scope Limits

- Every output includes the **LEGAL DISCLAIMER** block (including the IC memo)
- The skill does not draft legal documents, demand letters, or pleadings (but the IC memo CAN include a verbatim talking script — that's negotiation-prep language, not pleading language)
- The skill does NOT opine on jurisdictional case law unless provided
- For Mode A: complements but does not replace counsel's opinion letter
- For Mode B: complements but does not replace litigation counsel's infringement / non-infringement opinion
- The IC memo's strategic recommendations are *commercial diligence positioning*, not legal advice — phrase action items in operational language ("anchor key money demand at $10M+") and reserve legal-action recommendations ("file suit", "counter-sue") for counsel

---

## Failure Modes & Discipline

| Failure mode | Prevention |
|---|---|
| Brand / party / asset misidentification from folder names | Phase 1 anti-confabulation gate (cross-check against current-state document) |
| Opus subagent PDF timeout | Phase 0.7 pre-extraction in main thread |
| Hedged, citation-heavy memo where the user wanted decisive strategy | Phase 5 IC memo deliverable + memory-read in Phase 0.6 |
| QA passes individual quotes but misses higher-order misattribution | Phase 4 Wigum loop with negative-claim grep + Phase 1 anti-confab gate |
| Generic-looking output that doesn't match OKOA design language | Phase 5 renders via Brad design system tokens |
| Defensive frame ("can the franchise survive?") instead of offensive ("how should OKOA use the answer?") | Default Phase 5 IC memo IA leads with Bottom Line offensive callout + Survivability Matrix + Leverage list + talking script |

---

## Templates

| File | Purpose |
|---|---|
| `templates/session-manifest.yaml` | Session metadata |
| `templates/findings-manifest.yaml` | Findings structure |
| `templates/lending-report.md` | Mode A detailed memo |
| `templates/ip-infringement-report.md` | Mode B detailed memo |

The IC strategy memo HTML, the counterparty assertion+rebuttal structure, and the survivability matrix are **generated inline** by Phase 5 from the `/acos-document-design-brad` design tokens — they have no template files.

---

*ACOS Legal Analysis — Structured diligence, adversarial rigor, always cited, never advice. Now with IC-grade strategy memo by default.*
