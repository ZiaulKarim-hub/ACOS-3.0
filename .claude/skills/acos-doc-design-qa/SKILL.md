---
name: acos-doc-design-qa
description: |
  Screenshot-first deal document QA with per-page perfection loop.
  Scores every page 0-100 across 10 dimensions (60% substance, 40% execution).
  Uses independent reviewer agents that only see screenshots — never the fix list
  or source code. Loops per page until 100/100 before advancing. Designed for
  investment documents: prospectuses, credit memos, pitch decks, offering memoranda.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# ACOS Deal Document Design QA

## Purpose

Evaluate and perfect investment documents page-by-page using a **screenshot-first,
dual-rubric, independent-reviewer** methodology. The skill treats every page as a
deliverable that must score 100/100 before advancing to the next.

This is NOT a design linter. It evaluates whether the document works as a
**fundraising and decision-support tool** for institutional investors (LPs, IC members,
allocators) — not just whether it looks clean.

## Core Principles

### 1. Screenshot Authority
The screenshot is the single source of truth. If it looks wrong in the PNG,
it IS wrong — regardless of what the source code says. The reviewer agent reads
the rendered page image via the `Read` tool. It never reads the build script,
the fix list, or the data YAML.

### 2. Independence Wall
The **Fixer** and the **Reviewer** are separate agents with no shared context:
- **Fixer**: Reads the screenshot, reads the source code, implements fixes, rebuilds.
  The Fixer operates in the main conversation context.
- **Reviewer**: Spawned as a background `Task()` (with `run_in_background`). Receives ONLY the page PNG path,
  the page number, the page type, and the scoring rubric. Never sees what was
  "supposed to" be fixed. Cannot be primed to confirm a fix it didn't independently verify.

### 3. Convergence Requirement
Each Wigum iteration MUST reduce the total deduction count. If iteration N has
the same or more deductions than iteration N-1, the loop terminates with a
**STALL** verdict and escalates to the user. This prevents infinite fix-break cycles.

### 4. Page-Type Sensitivity
Different page types weight the 10 dimensions differently. A performance page
cares more about chart integrity and methodology transparency. A legal page
cares more about compliance and risk disclosure. The rubric adapts.

---

## Scoring Framework: 100 Points Per Page

### SUBSTANCE (60 points)

#### S1. Audience Fit (10 pts)
*Does this page show what an LP / IC member needs at this point in the document?*

| Criterion | What to evaluate |
|---|---|
| Information priority | Most decision-relevant info is most visually prominent |
| LP mental model | Answers what the LP is thinking at this document position |
| IC-ready data | Analyst could pull this page into an IC memo without modification |
| Jargon calibration | Institutional vocabulary — neither vague nor exclusionary |
| Non-redundancy | Page adds new information, doesn't repeat what was already said |

#### S2. Narrative Position (10 pts)
*Does this page fit logically in the story arc: Thesis > Evidence > Team > Structure > Risk > Action?*

| Criterion | What to evaluate |
|---|---|
| Sequencing logic | Page belongs where it is in the document order |
| Story momentum | Builds on the previous page, sets up the next |
| Thesis reinforcement | Connects back to the fund's core value proposition |
| Completeness | Covers its topic fully, no obvious gaps that undermine credibility |
| Transition clarity | Reader understands why they're now seeing this topic |

#### S3. Trust Signals (10 pts)
*Does this page build credibility through transparency, not just polish?*

| Criterion | What to evaluate |
|---|---|
| Source citations | Data claims cite a source (e.g., "Source: Cliffwater 2023") |
| Methodology disclosure | Performance numbers explain calculation method (per-loan vs fund-level, gross vs net) |
| Assumptions stated | Projections/illustrations identify what's assumed vs. actual |
| Date stamping | Data has an "as of" date; staleness is acknowledged |
| Limitation disclosure | Acknowledges what it doesn't show (e.g., subset of loans, specific exclusions) |
| Provenance | Track record sourced from audited financials vs. internal calcs — stated? |

#### S4. Risk & Balance (10 pts)
*Does this page present risks credibly, or is it pure upside polish?*

| Criterion | What to evaluate |
|---|---|
| Risk acknowledgment | Risks mentioned proportional to claims made |
| Downside scenarios | Return pages show loss scenarios, not only upside |
| Survivorship bias | Track record exclusions disclosed |
| Forward-looking language | Projections flagged with appropriate caveats |
| Balanced framing | Claims are defensible under LP scrutiny; not overselling |
| Regulatory accuracy | Reg D, accredited investor, and other legal terms used correctly |

#### S5. Chart & Data Integrity (10 pts)
*Are the numbers honest, well-presented, and decision-enabling?*

| Criterion | What to evaluate |
|---|---|
| Scale honesty | Axes start at zero or justify truncation; no misleading visual compression |
| Denominator clarity | Percentages state what they're a % of |
| Time period consistency | Compared numbers use the same time window |
| Apples-to-apples | Comparisons compare comparable things (gross vs gross, not gross vs net) |
| Source attribution | Charts cite their data source |
| Date anchoring | Every data point has an "as of" date |

#### S6. Compliance & Legal (10 pts)
*Would legal counsel approve this page for distribution?*

| Criterion | What to evaluate |
|---|---|
| Required disclaimers | Performance pages carry past-performance disclaimer |
| Forward-looking flagged | Projections clearly marked as forward-looking |
| Reg D compliance | 506(b) restrictions respected (no general solicitation) |
| Eligible investor language | Correct accredited/qualified client definitions |
| Confidentiality notice | Present where required |
| Definition precision | Legal terms (carried interest, preferred return, waterfall) used correctly |

---

### EXECUTION (40 points)

#### E1. Readability (10 pts)
*Can every element be read without squinting?*

| Criterion | What to evaluate |
|---|---|
| Text contrast | Every text element clearly readable against its background |
| Font sizing | Body >= 16px effective, headers proportionally larger |
| Word spacing | No words running together, no truncation |
| Photo/chart clarity | Images sharp, charts readable, labels visible |
| Text over photos | Background chip, shadow, or sufficient overlay opacity |
| Chart labels | Every label readable against chart background |

#### E2. Layout & Alignment (10 pts)
*Is the page geometrically clean?*

| Criterion | What to evaluate |
|---|---|
| Element overlap | Nothing colliding with anything else |
| Grid consistency | Columns, rows, margins aligned |
| Connector integrity | Lines and arrows connect properly |
| Whitespace purpose | Empty space is intentional breathing room, not missing content |
| Vertical balance | Content fills 70-90% of vertical space |
| Card/box alignment | Same-level elements share baselines |

#### E3. Brand & Visual System (10 pts)
*Does this page belong in this specific deck?*

| Criterion | What to evaluate |
|---|---|
| Color palette | Brand colors used correctly, no off-palette elements |
| Logo rendering | Clean wordmark, correct variant for background color |
| Design consistency | Same page type = same visual treatment |
| Eyebrow / footer | Present and consistent with other pages |
| No artifacts | No stray rectangles, debug marks, rendering glitches |

#### E4. Professional Polish (10 pts)
*Would this page hold up next to a BCRED, Apollo, or Ares prospectus?*

| Criterion | What to evaluate |
|---|---|
| Institutional tone | Visual confidence without overselling |
| Completeness feel | Page looks finished — no "coming soon" energy |
| Image quality | Photos crisp, no smudging, pixelation, or upscaling artifacts |
| Decision usefulness | LP can act on this page's information |
| Print readiness | Would look good printed at A4/Letter |
| Peer comparison | Competitive with top-tier PE fund marketing materials |

---

## Page-Type Weight Modifiers

Not every dimension matters equally on every page. The reviewer applies these
emphasis shifts (heavier dimensions get +2 severity on defects; lighter get -1):

| Page Type | Examples | Heavier Weight (+2 on defects) | Lighter Weight (-1 on defects) |
|---|---|---|---|
| **Cover** | Title page | Audience Fit, Brand, Polish | Data Integrity, Compliance |
| **Offering Summary** | Key terms at a glance | Audience Fit, Data Integrity, Decision Use | Narrative, Risk |
| **Market Thesis** | Why now, macro context | Trust Signals (citations!), Chart Integrity | Brand, Layout |
| **Performance** | Track record, returns | Chart Integrity, Trust Signals, Risk Balance | Brand, Layout |
| **Comparatives** | Asset class charts | Chart Integrity, Source Attribution | Compliance, Polish |
| **Sponsor / Team** | About us, bios | Audience Fit, Image Quality, Credibility | Data Integrity |
| **Strategy / Process** | How we lend | Narrative Position, Completeness | Chart Integrity |
| **Portfolio / Pipeline** | Current exposure | Data Integrity, Risk Balance (forward-looking) | Polish |
| **Case Studies** | Deal examples | Trust Signals (real outcomes), Image Quality | Compliance |
| **Structure / Terms** | Fund structure, economics | Decision Usefulness, Compliance, Readability | Image Quality |
| **Subscription** | How to invest | Audience Fit (CTA), Compliance | Chart Integrity |
| **Legal / Disclaimers** | Risk factors, legal | Compliance, Risk Balance, Legal Completeness | Layout, Brand |
| **Waterfall** | Distribution example | Chart Integrity, Trust Signals (math transparency) | Brand |

---

## Protocol

### Step 0: Initialization

1. **Identify the document type**: Prospectus, credit memo, pitch deck, offering memo, etc.
2. **Locate the page images**: Find all rendered page PNGs (e.g., `page-01.png` through `page-XX.png`)
   - **Verify dimensions before starting**: `sips -g pixelWidth -g pixelHeight page-01.png`.
     Every PNG must be ≤2000 px on both edges or the per-page Read loop will lock the
     conversation in an unrecoverable Anthropic API image-cap error. If any PNG exceeds
     the cap, re-render with `pdftoppm -r 150 -png` (US Letter → 1275×1650 px) or
     downscale in place with `sips -Z 1800 page-*.png` before proceeding.
3. **Locate the build system**: Identify the build script, data YAML, and rebuild command
4. **Identify the data source of truth**: The YAML or data file that feeds the document
5. **Map page types**: Assign each page a type from the Page-Type Weight Modifiers table
6. **Set iteration limits**: Default max 5 iterations per page. Configurable.

**Long-document Read discipline (mandatory for >20-page docs):** the per-page
loop reads ONE PNG per iteration, but rebuild + re-read cycles accumulate images
in the conversation buffer over time. After every ~8 page iterations, `/compact`
to flush old screenshots. The first `"image could not be processed and was removed"`
warning means the buffer is already degraded — stop and `/compact` before continuing.

Display initialization summary:
```
Document: {document_name}
Pages: {total_pages}
Build command: {build_command}
Data source: {data_yaml_path}
Max iterations per page: {max_iter}

Page map:
  P01: Cover
  P02: Navigation
  P03: Offering Summary
  ...
```

Ask user to confirm the page-type mapping before proceeding.

### Step 1: Per-Page Perfection Loop

Process pages sequentially: Page 1, then Page 2, ..., through Page N.

For each page:

#### 1a. Screenshot Read (Fixer Context)

The Fixer (main conversation) reads the current page PNG:
```
Read page-{NN}.png
```

Perform an initial assessment. Note obvious defects. Do NOT score yet —
scoring is the Reviewer's job.

#### 1b. Independent Reviewer Spawn

Spawn a **background `Task()`** (with `run_in_background`) as the Reviewer. The Reviewer receives:

- The page PNG path (reads it via `Read` tool)
- The page number and page type
- The full scoring rubric (copy of the 10 dimensions above)
- The page-type weight modifiers for this specific page type
- The data source YAML path (for content accuracy checks only — NOT the build script)

**The Reviewer NEVER receives:**
- The build script path or contents
- The list of fixes applied in previous iterations
- The Fixer's assessment or notes
- Any information about what "should have" been fixed

**Reviewer prompt template:**
```
You are an INDEPENDENT document quality reviewer. You have never seen this
document before. You have no knowledge of any fixes, changes, or prior
iterations. You are evaluating a FRESH page.

Read the page image at: {png_path}
Read the data source at: {data_yaml_path} (for content accuracy checks only)

Page: {page_number} of {total_pages}
Page type: {page_type}
Document type: {document_type}

Score this page using the rubric below. For EACH of the 10 dimensions,
provide:
  1. Score (0-10)
  2. Every specific deduction with:
     - Location on the page (top-left, center, bottom-right, etc.)
     - What is wrong (specific, not vague)
     - Severity: minor (-1), moderate (-3), major (-5)
     - Suggested fix (what it should look like)

Apply page-type weight modifiers for "{page_type}":
  Heavier (defect severity +2): {heavier_dimensions}
  Lighter (defect severity -1): {lighter_dimensions}

Be ruthlessly critical. Your job is to find EVERY flaw. If you say PASS
and there is a visible defect, you have failed at your job. It is better
to flag a false positive than to miss a real defect.

Do NOT hallucinate defects — only report what you can actually see in the
screenshot. If you cannot read text due to resolution, say "unreadable at
this resolution" rather than guessing what it says.

Output format:
PAGE {NN} — {page_type}
Total: {score}/100

S1. Audience Fit: {score}/10
  [deductions or CLEAN]
S2. Narrative Position: {score}/10
  [deductions or CLEAN]
...
E4. Professional Polish: {score}/10
  [deductions or CLEAN]

VERDICT: {PASS (100/100) | FAIL ({score}/100)}
DEDUCTION COUNT: {N}
```

#### 1c. Process Reviewer Results

When the Reviewer agent completes:

1. Read its verdict and deduction list
2. If **PASS (100/100)**: Lock page, display result, advance to next page
3. If **FAIL**: Proceed to fix cycle

#### 1d. Fix Cycle (Fixer Context)

For each deduction reported by the Reviewer:

1. **Diagnose**: Read the relevant section of the build script
2. **Fix**: Edit the build script or data YAML
3. **Track**: Log each fix with the deduction it addresses

After all fixes:

4. **Rebuild**: Run the build command
5. **Verify**: Read the updated page PNG (Fixer's own check)
6. **Re-spawn Reviewer**: New independent `Task()` with NO knowledge of previous iteration

#### 1e. Convergence Check

After each iteration, compare deduction counts:

Evaluate rows top-to-bottom; the first matching row fires. The 100/100 PASS check MUST come first so a page that simultaneously reaches 100/100 and reduces its deduction count locks immediately instead of wasting an extra loop:

| Condition | Action |
|---|---|
| Score is 100/100 | PASS — lock page, advance |
| Deduction count decreased | Continue loop |
| Deduction count same or increased | **STALL** — escalate to user |
| Max iterations reached | **MAX_ITER** — escalate to user |

**STALL escalation message:**
```
PAGE {NN} — STALL after {N} iterations
Deductions: {dedupe_count} (was {prev_dedupe_count})   |   Score: {score}/100 (was {prev_score}/100)
Remaining deductions:
  {list each deduction}

The fix cycle is not converging. Options:
  [1] Accept at current score and move on
  [2] Give me specific guidance on the remaining defects
  [3] Skip this page entirely
```

### Step 2: Cross-Page Consistency Check

After ALL pages pass individually, run a final cross-page sweep:

Spawn a **Cross-Page Reviewer** via `Task()` that reads ALL page PNGs (or a
representative subset) and checks:

| Check | What it evaluates |
|---|---|
| Style drift | Do all pages of the same type look consistent? |
| Number consistency | Same metrics shown on multiple pages agree |
| Narrative arc | Does the document build logically from thesis to action? |
| Tone consistency | No jarring shifts between pages |
| Footer/header consistency | Same position, same format across all pages |

If cross-page defects are found, return to the affected pages for targeted fixes.

### Step 3: Final Report

Display the final scorecard:

```
DOCUMENT QA COMPLETE
====================
Document: {document_name}
Pages: {total_pages}
Total iterations: {sum_iterations}

Per-Page Results:
  P01 (Cover):            100/100  [1 iteration]
  P02 (Navigation):       100/100  [1 iteration]
  P03 (Offering Summary): 100/100  [3 iterations]
  ...
  P20 (Legal):            100/100  [2 iterations]

Cross-Page Check: PASS

Outputs:
  PDF:  file://{pdf_path}
  PPTX: file://{pptx_path}

Total defects found and fixed: {total_defects}
Categories: {breakdown by dimension}
```

---

## Reviewer Agent Independence Safeguards

These rules are NON-NEGOTIABLE. Violating them compromises the entire QA system.

1. **No fix-list forwarding**: The Reviewer prompt NEVER includes what was changed
2. **No code access**: The Reviewer NEVER reads the build script, only the screenshot
3. **No iteration memory**: Each Reviewer spawn is a fresh agent with no prior context
4. **No leading language**: The prompt never says "verify that X was fixed" — it says
   "evaluate this page"
5. **Data YAML access is read-only**: The Reviewer reads the data YAML only to verify
   content accuracy (e.g., "does the page show the correct fund size?"). It does not
   read the YAML to understand what was "supposed to" be rendered.
6. **Hallucination guard**: The Reviewer must quote or describe specific visual evidence
   for every deduction. "The text appears faded" must be accompanied by "the text at
   [location] reading '[specific words]' on a [color] background." If the Reviewer
   cannot read the text, it must say so rather than guessing.

---

## Deduction Severity Scale

| Severity | Points | Definition | Example |
|---|---|---|---|
| Minor | -1 | Cosmetic imperfection a careful reader might notice | Slightly uneven margin, minor whitespace imbalance |
| Moderate | -3 | Clearly visible flaw that affects readability or credibility | Text contrast issue, missing source citation, chart without date |
| Major | -5 | Defect that would cause an LP to question document quality | Logo rendering as rectangle, numbers disagreeing between pages, missing disclaimer on performance page |

Page-type weight modifiers adjust these:
- **Heavier** dimensions: severity +2 (minor becomes -3, moderate becomes -5, major becomes -7 capped at -10)
- **Lighter** dimensions: severity -1 (minor becomes 0/ignored, moderate becomes -2, major becomes -4)

---

## Usage

Invoke with:
```
/acos-doc-design-qa
```

The skill will prompt for:
1. Document location (folder containing page PNGs)
2. Build command (how to rebuild after fixes)
3. Data source YAML path
4. Document type (prospectus, credit memo, pitch deck, etc.)

Or provide arguments:
```
/acos-doc-design-qa --pages /path/to/pages --build "python3 build.py" --data /path/to/inputs.yaml --type prospectus
```

---

## Integration with Other Skills

- **After `/acos-loan-doc-generator-with-visual-verification`**: Run this skill on the
  generated output for substance-level QA (the generator skill focuses on visual
  rendering; this skill adds audience fit, narrative flow, trust signals, and compliance).
- **After manual document builds**: Any PIL/reportlab/python-pptx document can be QA'd
  by rendering to PNGs and pointing this skill at the output folder.
- **Standalone review**: Point at any folder of document page images to get a quality
  assessment without a rebuild loop (read-only mode).

---

*ACOS Deal Document Design QA — Screenshot-first, independent-reviewer, per-page
perfection loop with dual rubric (60% substance / 40% execution). Designed for
institutional investment documents. The reviewer never sees the fix list.*
