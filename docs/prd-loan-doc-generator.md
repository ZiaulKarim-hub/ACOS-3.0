# PRD: ACOS Loan Document Generator
**Skill:** `/acos-loan-doc-generator`
**Status:** Draft
**Date:** 2026-03-09
**Replaces:** `/acos-credit-memo-generator`

---

## 1. Overview

The ACOS Loan Document Generator is a multi-agent swarm skill that generates institutional-quality private equity loan documents. It learns document design patterns from user-provided examples, analyzes a loan folder for relevant data, and produces a complete document through parallel AI agents with iterative quality validation.

The skill is general-purpose: it can generate any loan-related document by extracting style from examples rather than relying on hardcoded templates. A curated document type menu guides the user to the right benchmark standards, while free-text entry and an additional instructions field accommodate any specific document within each category.

---

## 2. Problem Statement

Producing loan documents in private equity is time-consuming, inconsistent, and highly dependent on institutional knowledge. Each firm has its own style conventions, section structure, and language standards embedded in past documents. New team members, high deal volume, and document variety create bottlenecks.

Existing tools either generate generic templates (ignoring firm-specific style) or require manual assembly. There is no tool that learns from a firm's own examples and generates documents that match their institutional voice at scale.

---

## 3. Goals

- **Learn style from examples** — Extract design patterns and quality benchmarks from a firm's own example documents. Never hardcode style.
- **Generate any PE loan document** — Support the full range of private equity loan documents through category selection and free-text specificity.
- **Maintain a reusable design library** — Cache extracted design patterns so future generations for the same doc category reuse prior extraction work.
- **Enforce quality through adversarial validation** — Validate every generated document against extracted benchmarks. Iterate until passing (Wigum loop).
- **Accept user guidance** — Allow freeform additional instructions that override or extend defaults at any step.

## 4. Non-Goals

- **Not a template filler** — The skill does not fill pre-built templates. It generates document content from scratch, guided by learned patterns.
- **Not a legal review tool** — Generated documents are drafts for human review. No legal advice is implied.
- **Not a document editor** — The skill produces output; editing is done externally.
- **Not a global design library** — The design library is per-project. Cross-project sharing is out of scope.
- **Not a data room tool** — The skill reads loan folders but does not organize, classify, or manage them.

---

## 5. User Journey

### 5.1 Entry Point

```
/acos-loan-doc-generator [optional: status]
```

If `status` is passed, display current config, design library, and active sessions. Otherwise, begin the Interview Wizard.

---

### 5.2 Interview Wizard (Phase 0)

The skill opens an interactive interview. All input is numbered-menu or free-text. No CLI argument parsing.

#### Step 1 — Document Type Selection

The user selects from 10 options organized into a menu:

```
╔══════════════════════════════════════════════════════════════╗
║        ACOS Loan Document Generator                         ║
╚══════════════════════════════════════════════════════════════╝

Step 1 of 4: What would you like to generate?

  [1]  Credit Memo — Internal    (risk-focused, credit committee)
  [2]  Credit Memo — External    (marketing document, broker-facing)
  ─────────────────────────────────────────────────────────────
  [3]  Loan Agreement
  [4]  Guarantee Document
  [5]  Deal Document
  [6]  Foreclosure Document
  [7]  Legal & Litigation Document
  [8]  Closing & Administration Document
  [9]  Investor Reporting Document
  [10] Other

Enter selection [1-10]:
```

**Credit Memo (1 & 2):** Both are explicit top-level options because their purpose, structure, and benchmark standards are fundamentally different from each other and from all other categories.

**Categories (3–10):** Broad enough to encompass any document within the domain. The user specifies the exact document in the next step.

#### Step 2 — Specific Document Name (non-Credit-Memo only)

For selections 3–10, ask:

```
  You selected: Loan Agreement

  What specific document do you need?
  (e.g., "Bridge Loan Agreement", "Construction Loan Agreement",
   "Mezzanine Loan and Security Agreement")

  Document name: _
```

- The entered name becomes the `document_title` used in all agent prompts and the output filename.
- For Credit Memo selections (1 or 2), this step is skipped.

#### Step 3 — Design Style Selection

Check the design library for existing entries matching the selected category.

**If 1+ designs exist in library:**

```
Step 2 of 4: Design style

  Design Library has 2 design(s) for "Loan Agreement":
  ─────────────────────────────────────────────────────────────
  [1]  Choose Design from Library
  [2]  Use New Design

Enter selection [1-2]:
```

If "Choose Design from Library" is selected, show available entries:

```
  Available designs for "Loan Agreement":
  ─────────────────────────────────────────────────────────────
  [1]  bank-style-2024      │ 4 examples │ Added 2026-02-15
  [2]  pe-fund-format-v2    │ 2 examples │ Added 2026-03-01

Enter selection [1-2]:
```

If "Use New Design" is selected, prompt for example path (see below).

**If no designs exist in library for this category:**

```
  No designs in library for "Loan Agreement". Using new design.

  Enter path to example document(s):
  (File path, directory, or glob pattern)

  Path: _
```

**Novelty check:** Before Phase 1 extraction, compute a fingerprint from `(category, source_path)` and check against the library index. If the source is already indexed, offer to reuse the cached extraction or force re-extraction. If new, extract and auto-add to library after Phase 1 completes.

#### Step 4 — Loan Folder

```
Step 3 of 4: Loan folder

  Enter path to the loan folder for this transaction:
  Path: _
```

#### Step 5 — Additional Instructions (Optional)

Shown for all document types:

```
Step 4 of 4: Additional instructions  (optional — press Enter to skip)

  Add any specific requirements, custom clauses, emphasis areas,
  or context that should guide the document generation:

  Examples:
    "Include a 3-year financial summary table in the Financial Analysis"
    "Borrower is a repeat client — tone should be relationship-oriented"
    "Use California law conventions for the governing law section"
    "Flag any covenant breaches prominently"

  Instructions: _
```

#### Step 6 — Confirmation

Display a summary before proceeding:

```
╔══════════════════════════════════════════════════════════════╗
║ Ready to Generate                                           ║
╠══════════════════════════════════════════════════════════════╣
║  Category      : Loan Agreement                             ║
║  Document      : Bridge Loan and Security Agreement         ║
║  Design Source : bank-style-2024 (from library)             ║
║  Loan Folder   : /path/to/loan-folder/                      ║
║  Instructions  : "Flag any covenant concerns prominently"   ║
║  Session ID    : 20260309-143022                            ║
╚══════════════════════════════════════════════════════════════╝

  Phases to run:
    ✓ Phase 1: Extraction     (skipped — using library design)
    ☐ Phase 2: Loan Analysis
    ☐ Phase 3: Document Design
    ☐ Phase 4: Validation + Wigum Loop

Proceed? [Y/n]:
```

---

## 6. Document Type Catalog

Each category defines: default sections, benchmark dimensions, and a designer tone directive. The category drives benchmark standards; the `document_title` free text drives content specificity.

### 6.1 Credit Memo — Internal

**Purpose:** Internal credit committee document. Analytical, risk-first.

**Default Sections:**
1. Executive Summary
2. Borrower & Sponsor Overview
3. Transaction Summary
4. Financial Analysis
5. Collateral Analysis
6. Risk Assessment
7. Stress Testing
8. Mitigants & Strengths
9. Conditions & Covenants
10. Recommendation

**Benchmark Dimensions:**
- Required Sections Completeness
- Data Completeness & Accuracy
- Risk Coverage (all material risks named and quantified)
- Financial Analysis Standards (ratios, trends, peer comparison)
- Stress Testing Rigor
- Recommendation Clarity (unambiguous, with conditions)
- Language & Tone (formal-analytical)
- Formatting Consistency

**Designer Tone Directive:**
> This is an internal credit memo for the credit committee. Be direct and analytical. Lead with risks, not strengths. Every material risk must be named, quantified where possible, and accompanied by a specific mitigant. Stress test scenarios must be conservative and specific. The recommendation must be unambiguous. Tone: formal institutional analysis.

---

### 6.2 Credit Memo — External

**Purpose:** Marketing and advertising document for brokers and capital partners. Opportunity-first.

**Default Sections:**
1. Opportunity Headline
2. Deal at a Glance *(scannable summary box)*
3. Why This Deal *(3–5 thesis points, bullet format)*
4. The Asset *(collateral story)*
5. The Borrower *(track record and credibility)*
6. The Numbers *(thesis-supporting metrics only)*
7. Market Context *(why this market, why now)*
8. Structure & Protections *(objection handling)*
9. Call to Action *(next steps, contact, deadline)*

**Benchmark Dimensions:**
- Headline & Hook Strength (does the opening create immediate interest?)
- Scannability (key thesis readable in under 60 seconds)
- Thesis Coherence (3–5 reasons are specific, evidenced, and compelling)
- Asset Presentation (collateral described to create confidence and desire)
- Numbers Selection (only thesis-supporting metrics shown — no data dumps)
- Objection Handling (risks acknowledged but led by mitigants)
- Call to Action Clarity (specific, easy to follow, action-oriented)
- Professional Marketing Tone (confident, investment-grade, not aggressive)

**Designer Tone Directive:**
> This is an external credit memo — it is a marketing and advertising document. You are writing to attract capital partners and brokers, not to interrogate the deal. Advertising principles apply: lead with opportunity and return, not structure or risk. Make the reader want to participate. Use vivid, confident, specific language — not hedged financial prose. Risks appear only as managed risks with strong mitigants leading. Select numbers that support the thesis; do not dump all data. Headlines and subheadings should be compelling, not generic. The document must be visually scannable (short paragraphs, bullets, callout boxes). End with urgency and a specific call to action. Tone: professional investment marketing.

---

### 6.3 Loan Agreement

**Purpose:** Legal agreement governing a loan between lender and borrower.

**Benchmark Dimensions:**
- Definitions Completeness & Precision
- Covenant Enforceability (affirmative, negative, financial)
- Default & Remedies Coverage
- Representations & Warranties Scope
- Cross-Reference Integrity
- Legal Language Standards

**Designer Tone Directive:**
> This is a legal loan agreement. Every term must be precise and unambiguous. Definitions must be complete and cross-referenced correctly throughout. Covenants must be specific, measurable, and enforceable. Follow design pattern legal language conventions exactly.

---

### 6.4 Guarantee Document

**Purpose:** Legal instrument by which a guarantor assumes obligations of a borrower.

**Benchmark Dimensions:**
- Guarantor Scope Clarity (who, what obligations)
- Carve-Outs & Limitations Coverage
- Enforcement Provisions
- Signatory & Execution Requirements
- Legal Language Standards

**Designer Tone Directive:**
> This is a legal guarantee document. Scope of the guaranty must be unambiguous. Carve-outs must be exhaustive and precisely worded. Enforcement rights must be clearly stated. Follow design pattern conventions for legal guarantee language exactly.

---

### 6.5 Deal Document

**Purpose:** Pre-deal documents including term sheets, commitment letters, LOIs, and deal teasers.

**Benchmark Dimensions:**
- Key Terms Completeness
- Conditions & Contingencies Clarity
- Binding vs. Non-Binding Distinctions
- Expiry & Timeline Clarity
- Tone Appropriateness (varies: teaser = marketing; term sheet = precise)

**Designer Tone Directive:**
> Tone depends on the specific document. Term sheets and commitment letters must be precise and unambiguous about binding terms. Deal teasers and LOIs may be persuasive and opportunity-focused. Follow the design patterns and the document_title to calibrate tone correctly.

---

### 6.6 Foreclosure Document

**Purpose:** Legal documents related to foreclosure proceedings on defaulted loans.

**Benchmark Dimensions:**
- Statutory Compliance (jurisdiction-specific requirements)
- Notice Requirements (proper parties, timing, method)
- Timeline & Procedural Accuracy
- Rights Preservation (borrower and lender)
- Jurisdiction-Specific Legal Standards

**Designer Tone Directive:**
> This is a legal foreclosure document. Jurisdiction-specific statutory requirements take precedence over style. Every procedural step must be explicitly stated. Notice requirements must be complete. Follow design pattern conventions for the applicable jurisdiction.

---

### 6.7 Legal & Litigation Document

**Purpose:** Demand letters, notices of default, legal opinions, litigation support memos, and related documents.

**Benchmark Dimensions:**
- Legal Basis Clarity (what right or obligation is being invoked)
- Factual Accuracy (all stated facts must trace to loan data)
- Demand/Relief Specificity (what exactly is being requested)
- Tone Calibration (firm but professional)
- Legal Language Standards

**Designer Tone Directive:**
> This is a legal or litigation document. Tone must be firm, precise, and professionally assertive — not aggressive. Every factual claim must be supportable. Legal basis for any demand or position must be explicitly stated. Follow design pattern conventions for legal correspondence.

---

### 6.8 Closing & Administration Document

**Purpose:** Checklists, disbursement agreements, and administrative documents for loan closing.

**Benchmark Dimensions:**
- Checklist Completeness (all standard closing items present)
- Conditions Precedent Coverage
- Disbursement Accuracy
- Party Identification & Roles
- Procedural Clarity

**Designer Tone Directive:**
> This is a closing or administrative document. Completeness and procedural clarity take priority over narrative. Every item must be specific, actionable, and assigned to a responsible party. Follow design pattern conventions for closing checklists and administrative forms.

---

### 6.9 Investor Reporting Document

**Purpose:** LP-facing communications including quarterly reports, capital call notices, distribution notices, investor letters, and NAV statements.

**Benchmark Dimensions:**
- Required Disclosures Completeness
- Financial Accuracy (figures match source data)
- Narrative Clarity (performance explained, not just reported)
- Portfolio Coverage (all relevant positions addressed)
- Tone Appropriateness (transparent, professional, investor-friendly)

**Designer Tone Directive:**
> This is an investor reporting document for limited partners. Be transparent, professional, and clear. Report performance honestly — explain variances, not just results. Financial figures must be precise and match source data exactly. Narrative should give LPs confidence in management without overselling. Follow design pattern conventions for investor communications.

---

### 6.10 Other

**Purpose:** Catch-all for any document not covered by the above categories.

**Benchmark Dimensions (generic):**
- Document Completeness (all expected sections present)
- Structural Coherence (logical flow and organization)
- Language Clarity
- Data Accuracy (all stated facts traceable to loan folder)
- Formatting Consistency

**Designer Tone Directive:**
> Generate the requested document following the design patterns exactly. Use the document_title and any additional instructions to calibrate content, tone, and structure. Where design patterns are silent, default to formal professional standards.

---

## 7. Design Library

### 7.1 Purpose

The design library is a persistent cache of extracted design patterns, indexed by document category. It avoids re-running Phase 1 extraction when the same design has been extracted previously.

### 7.2 Storage Location

```
.acos/loan-doc-generator/design-library/
├── index.yaml                    ← Master library index
└── {design-id}/
    └── manifest.yaml             ← Metadata + paths to extraction files
```

### 7.3 Index Schema

```yaml
version: "1.0"
entries:
  - design_id: "loan-agreement-bank-style-2024"
    category: "loan-agreement"
    label: "Bank Style 2024"
    source_path: "/path/to/examples/"
    source_fingerprint: "sha256-of-category+source_path"
    date_added: "2026-02-15"
    example_count: 4
    extraction_session_id: "20260215-091500"
    design_patterns_path: ".acos/loan-doc-generator/extractions/20260215-091500/design/synthesis/design-patterns.yaml"
    benchmark_criteria_path: ".acos/loan-doc-generator/extractions/20260215-091500/benchmarks/synthesis/benchmark-criteria.yaml"
```

### 7.4 Novelty Check

Before Phase 1 extraction, compute `fingerprint = sha256(category + source_path)` and check against existing index entries.

- **Match found:** Offer to reuse cached extraction or force re-extraction.
- **No match:** Proceed with Phase 1. After Step 1.6, auto-add to library.

### 7.5 Adding to Library

After a successful Phase 1 extraction from a new source:

1. Generate `design_id`: `{category-slug}-{YYYYMMDD}`
2. Prompt user for an optional custom label: `Name this design [{auto-id}]: _`
3. Append entry to `design-library/index.yaml`
4. Confirm: `Design added to library: "{label}" — reusable for future {Category} generation.`

---

## 8. Additional Instructions

### 8.1 Collection

Collected in Step 5 of the Interview Wizard. Optional for all document types. Stored as `additional_instructions` in the session manifest.

### 8.2 Injection into Phase 3 (Designer Agents)

Every section designer agent receives:

```
SPECIAL INSTRUCTIONS FROM USER:
────────────────────────────────
{additional_instructions}

These instructions take precedence over design pattern defaults where
they conflict. Incorporate them into your section. If an instruction
is not applicable to your specific section, acknowledge it as noted
but not applicable here.
```

### 8.3 Injection into Phase 4 (Validator Agents)

Every validator agent receives an additional criterion:

```
USER INSTRUCTIONS COMPLIANCE CHECK:
──────────────────────────────────────
{additional_instructions}

Verify that the assembled document honors these instructions.
Any clear, specific violation is a FAIL with fix instruction.
```

---

## 9. Technical Architecture

### 9.1 Delegated Phase Orchestration (v2 — Mar 2026)

The pipeline uses **delegated phase orchestration** to keep the primary context
window thin. Each phase runs in its own agent context window:

| Component | Context | Token Budget | Role |
|-----------|---------|-------------|------|
| SKILL.md (thin router) | Primary | ~8K | Interview wizard + phase dispatch |
| `loan-doc-phase1` agent | Own window | Up to 200K | Design extraction orchestration |
| `loan-doc-phase2` agent | Own window | Up to 200K | Loan folder analysis orchestration |
| `loan-doc-phase34` agent | Own window | Up to 200K | Design + validation + Wigum loop |

**Primary context usage**: ~25-30K tokens total (vs ~300K+ in v1 monolithic design).

**Key design principles**:
- **Agent-reads-from-disk**: Sub-agents are told WHERE to read files, not given
  embedded content. Eliminates double-counting in the orchestrator's context.
- **Phase files on demand**: Phase instructions live in separate `.md` files,
  read only by the agent that needs them.
- **Self-contained Wigum loop**: The Phase 3+4 agent handles all iterations
  internally — no iteration state accumulates in the primary context.

| Phase | Description | Orchestrator Agent |
|-------|-------------|-------------------|
| Phase 0 | Interview Wizard | Primary context (SKILL.md) |
| Phase 1 | Extraction | `loan-doc-phase1` |
| Phase 2 | Loan Folder Analysis | `loan-doc-phase2` |
| Phase 3+4 | Design + Validation + Wigum | `loan-doc-phase34` |

### 9.2 Skill File Layout

```
.claude/skills/acos-loan-doc-generator/
├── SKILL.md                         ← Thin router (~8KB)
├── phases/
│   ├── phase1-extract.md            ← Phase 1 orchestrator instructions
│   ├── phase2-analyze.md            ← Phase 2 orchestrator instructions
│   ├── phase3-design.md             ← Phase 3 orchestrator instructions
│   └── phase4-validate.md           ← Phase 4 orchestrator instructions
└── templates/                       ← (unchanged)

.claude/agents/
├── loan-doc-phase1.md               ← Phase 1 orchestrator agent
├── loan-doc-phase2.md               ← Phase 2 orchestrator agent
└── loan-doc-phase34.md              ← Phase 3+4 orchestrator agent
```

### 9.3 Workspace Layout

```
.acos/loan-doc-generator/
├── config.yaml
├── design-library/
│   ├── index.yaml
│   └── {design-id}/manifest.yaml
├── extractions/
│   └── {session-id}/
│       ├── plan.yaml
│       ├── manifest.yaml
│       ├── design/
│       │   ├── agent-{NN}/findings.yaml
│       │   └── synthesis/design-patterns.yaml
│       └── benchmarks/
│           ├── agent-{NN}/findings.yaml
│           └── synthesis/benchmark-criteria.yaml
├── cache/
│   └── {fingerprint}/phase2-cache-manifest.yaml
└── sessions/
    └── {session-id}/
        ├── session-manifest.yaml
        ├── phase2-analysis/
        │   ├── agent-{NN}/extract.yaml
        │   └── synthesis/
        │       ├── loan-data.yaml
        │       └── loan-data-brief.yaml
        ├── phase3-design/
        │   └── iteration-{N}/
        │       ├── agent-{NN}/section.md
        │       └── synthesis/
        │           ├── document-draft.md
        │           └── assembler-notes.yaml
        ├── phase4-validation/
        │   └── iteration-{N}/
        │       ├── structural/result.yaml
        │       ├── quality/agent-{NN}/result.yaml
        │       ├── global/{dimension}/result.yaml
        │       └── synthesis/validation-report.yaml
        └── output/
            ├── {document-title}-final.md
            └── validation-report.yaml
```

### 9.4 Model Resolution

Phase orchestrator agents assign models to sub-agents:
- Extractor/analyzer/designer agents: `model: sonnet`
- Synthesizer/assembler agents: `model: opus`
- Structural validators: `model: haiku`
- Quality + global validators: `model: sonnet`
- Validation aggregator: `model: opus`

### 9.5 Parallel Execution

All agents within each phase are spawned simultaneously in a single message with `run_in_background: true`. No phase begins until all agents from the prior phase have reported.

### 9.6 Wigum Loop

Maximum iterations configurable in `config.yaml` (default: 3). Loop terminates on: all benchmarks passing, max iterations reached, or convergence failure (failure count not decreasing for 2+ consecutive iterations). On max iterations reached, escalate to user with remaining failures, fix instructions, and options. The entire loop runs inside the `loan-doc-phase34` agent.

---

## 10. Configuration

Template: `.claude/skills/acos-loan-doc-generator/templates/loan-doc-config.yaml`
Runtime: `.acos/loan-doc-generator/config.yaml`

```yaml
# Paths
examples_path: ""
loan_folder_base: ""

# Design Library
design_library:
  path: ".acos/loan-doc-generator/design-library"
  auto_add_new_designs: true
  prompt_for_label: true

# Extraction
extraction:
  max_design_agents: 10

# Generation
generation:
  max_iterations: 3
  min_analyzers: 3
  max_analyzers: 15
  analyzer_strategy: "auto"
  auto_strategy_threshold: 10

# Output
output:
  format: "markdown"
  include_validation_report: true
  include_data_gaps: true
```

---

## 11. Status Command

```
/acos-loan-doc-generator status
```

Displays:

```
ACOS Loan Document Generator — Status
=======================================

Configuration: .acos/loan-doc-generator/config.yaml

Design Library:
  [category]    [design-id]        [examples]  [date-added]
  loan-agreement  bank-style-2024  4 examples  2026-02-15
  credit-memo-int pe-format-v2     3 examples  2026-03-01

Cached Extractions:
  [session-id]     [date]      [docs]  [status]
  20260215-091500  2026-02-15  4       complete
  20260301-091500  2026-03-01  3       complete

Active Sessions:
  [session-id]     [category]        [document]            [phase]  [iter]  [status]
  20260309-143022  loan-agreement    Bridge Loan Agreement  3        1       in-progress
```

---

## 12. File Layout (Skill)

```
.claude/skills/acos-loan-doc-generator/
├── SKILL.md
└── templates/
    ├── loan-doc-config.yaml
    ├── doc-type-catalog.yaml
    ├── design-library-index.yaml
    ├── design-library-entry.yaml
    ├── design-pattern.yaml
    ├── benchmark-criterion.yaml
    ├── loan-data-extract.yaml
    └── validation-result.yaml
```

---

## 13. Success Criteria

- [ ] Interview wizard guides user to a complete configuration in under 2 minutes
- [ ] Design library correctly identifies existing designs for a category and offers them
- [ ] New designs are extracted and added to the library automatically
- [ ] Phase 1 extraction produces valid `design-patterns.yaml` and `benchmark-criteria.yaml`
- [ ] Phase 3 produces a document that matches the tone directive for the selected category
- [ ] Additional instructions appear in at least one section of the generated document
- [ ] External Credit Memo reads as a marketing document, not a financial report
- [ ] Wigum loop iterates correctly until pass or max iterations
- [ ] Status command shows accurate library, extraction, and session state
- [ ] "Other" category produces a coherent document for any reasonable document name

---

*ACOS Loan Document Generator — PRD v1.0*
