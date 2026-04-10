# Project Retrospective: ACOS 3.0 — EPIC-001 Loan Document Generator V2

**Project ID:** EPIC-001 (within ACOS-3.0)
**Completion Date:** 2026-04-03 (final review round complete)
**Duration:** ~18 days (2026-03-16 through 2026-04-03, across ~8 sessions)
**Analyzed By:** Learning Curve Agent
**Analysis Date:** 2026-04-10

## Project Summary

**Vision:** Transform the loan document generator from a proof-of-concept that produced
inconsistent output formats into a production-grade tool delivering institutional-quality
DOCX+PDF documents for Okoa Capital's credit committee and counterparty submissions.

**Scope:**
- Epics: 1 (EPIC-001)
- Stories: 8 (DOCX+PDF pipeline, rendering quality, design library overhaul, XLSX extraction,
  data verification gate, charts/recommendation matrix, workflow resilience, UX)
- Slices: 30 planned (plus PPTX pipeline as scope expansion)

**Final Status:** Completed with scope expansion (PPTX pipeline added mid-epic)

---

## Key Metrics

### Velocity

| Metric | Value | Benchmark |
|--------|-------|-----------|
| Total Planned Slices | 30 | - |
| Scope Expansion Stories | 1 (PPTX pipeline) | - |
| Swarm Review Rounds | 3 | Target: 1-2 |
| Total Review Findings | 99+ (9C+18H+26M Round 1; 30+ Round 2; 13 Round 3) | Target: <20 |
| First-Pass Approval Rate | 0% (all lenses REJECTed in Round 1) | Target: 70% |
| Sessions to Complete | ~8 sessions | - |

### Quality

| Metric | Value | Benchmark |
|--------|-------|-----------|
| Critical Issues in Review | 9 (Round 1), 0 (Round 3) | Target: 0 |
| High Issues in Review | 18 (Round 1), 0 (Round 3) | Target: <5 |
| Domain Logic Findings | 5 Critical/High specifically | - |
| Cross-Lens Confirmed Findings | 5 (highest confidence) | - |
| Security Issues Found | 3 Medium (all fixed) | - |

### Agent Performance

| Agent | Tasks | Notes |
|-------|-------|-------|
| loan-doc-phase1 | Design extraction | Performed as designed |
| loan-doc-phase2 | Data analysis + synthesis | Updated with XLSX pre-processing |
| loan-doc-phase34 | Design + validation + Wigum | Handled PPTX + DOCX + PDF finalization |
| fin-stmt-sandbox | Financial statement prep | 3 instances, 17 swarm fixes applied |
| fin-stmt-accountant | Reconciliation Wigum | Never provides numbers (enforced) |

---

## What Went Well

### Delegated Phase Orchestration

**What:** Splitting the pipeline across three dedicated agent contexts (phase1, phase2,
phase34) with a session manifest as the coordination contract. This allowed phase
resumability, model-tier optimization, and parallel batch execution.

**Why It Worked:** Natural data handoffs existed between phases (design patterns →
loan data → final documents). The session manifest made state explicit and crash-safe.

**Learning Extracted:** LEARN-ARCH-001

### Two-Tier Data Model

**What:** Maintaining full `loan-data.yaml` (with all provenance) and a brief
`loan-data-brief.yaml` (only critical_figures for the document type) as parallel
representations of the extracted data.

**Why It Worked:** Design agents need only 20-30 fields; validators need all fields
with provenance. Passing the wrong tier to each agent class would either waste tokens
or lose accuracy.

**Learning Extracted:** LEARN-ARCH-002

### Wigum Loop Reuse Across Skills

**What:** The Wigum loop pattern (generate → validate → identify deficiencies → targeted
regeneration → repeat) was used in both the loan doc generator (Phase 4 benchmarks)
and the financial statement skill (Primary Accountant reconciliation). The pattern
proved robust enough to be applied identically in two different domains.

**Why It Worked:** Clear separation of validator (never provides values) from generator
(never sees the full review rules). Convergence criteria were objective and binary.

**Learning Extracted:** LEARN-ARCH-003

### Multi-Round Swarm Remediation Convergence

**What:** Three rounds of swarm review + remediation converged from 56 findings (Round 1)
to 30 (Round 2) to 13 (Round 3) to zero Critical/High.

**Why It Worked:** Each round built on the previous. Cross-lens confirmed findings (those
flagged by 2+ lenses independently) were prioritized in Round 1, eliminating the
most disruptive issues first. Round 3 could then focus on domain polish and UX.

**Learning Extracted:** LEARN-REVIEW-001

### XLSX Pre-Processing as an Enforced Architecture Decision

**What:** Instead of asking agents to "read the XLSX files," a mandatory pre-processing
step (xlsx-extract.py) converted all XLSX files to structured YAML before any agent
touched the data.

**Why It Worked:** LLMs cannot read binary formats. Making this an architectural gate
(not a suggestion) eliminated an entire class of hallucinated financial figures.

**Learning Extracted:** LEARN-IMPL-001

---

## What Could Be Improved

### Large Work Accumulation Without Commits

**What Happened:** On 2026-03-23, the session handoff noted: "CRITICAL: No git commits
since 2026-03-16. Everything built this session will be lost if the working tree is
wiped." Over 1,000 lines of new code, 3 new skills, 3 new agents, and the complete
EPIC-001 planning artifact were untracked.

**Root Cause:** Complex multi-feature sessions naturally defer commits to a "natural
stopping point." When sessions are long and work spans many files, the stopping point
keeps moving forward.

**Impact:** Multiple sessions of significant work at risk. Handoff files repeatedly
listed "commit X" as a blocker, adding cognitive overhead to every session start.

**Recommendation:** Commit at end of every session regardless of completeness.
Use `wip:` prefixes for incomplete work. Treat commits as crash insurance, not
"done" markers.

**Learning Extracted:** LEARN-ANTI-003

### Domain Logic Gaps Discovered Late

**What Happened:** The swarm review (Round 1) surfaced Critical and High domain logic
gaps: missing Exit Strategy section, missing LTC metric for bridge lending, missing
Draw Request fields, scoring bands calibrated for stabilized (not bridge) lending.
These were fixed in Round 3 (domain-logic-fixes evidence bundle, 2026-03-24).

**Root Cause:** Document templates were designed bottom-up (what can we extract?)
rather than top-down (what does a bridge lender need to see?). A domain logic
review lens was included in the swarm review but was only effective after the
templates already existed.

**Impact:** Required an extra remediation pass specifically for domain completeness.
Several High findings were domain-specific and required direct knowledge of PE
real estate bridge lending practices.

**Recommendation:** Before designing any new document type, source the practitioner's
completeness checklist explicitly. For PE lending: start with LTC, exit strategy,
recourse type, interest reserve as required fields.

**Learning Extracted:** LEARN-ANTI-004

### PPTX Pipeline Shipped Non-Functional

**What Happened:** The PPTX generation pipeline (`data-to-pptx.py`, `validate-pptx.py`)
was developed and committed as a scope expansion (commit 1ba46db) but had Critical
defect C1: the pipeline expected `verified-data.yaml` which no phase produced.
The PPTX pipeline was completely non-functional from the moment it was first committed.

**Root Cause:** The scope expansion was developed quickly without tracing the data
contract end-to-end. `data-to-pptx.py` was written to read a file that was assumed
to exist but never added to the phase pipeline's outputs.

**Impact:** 7 PPTX-specific defects found in Round 1 review, requiring targeted fixes
in Rounds 1 and 2.

**Recommendation:** For any new pipeline component, explicitly trace: what files
does it read? Are all of them produced by an upstream phase? Use the session manifest
as the canonical contract and verify every input field exists.

**Learning Extracted:** LEARN-ANTI-001

---

## Decision Analysis

### Decisions That Worked

| Decision | Context | Outcome |
|----------|---------|---------|
| html-to-docx.py over pandoc | pandoc lost all CSS styling | DOCX output matched PDF quality |
| Digit-ratio heuristic for font detection | contains-digit check misclassified labels | Font role detection became accurate |
| XLSX pre-processing before agent analysis | Agents cannot read binary .xlsx | Eliminated hallucinated financial figures |
| Wigum loop with adversarial validator | Need quality convergence without bias | Reused identically in financial statement skill |
| Two-tier loan data model | Token cost vs accuracy tradeoff | Phase 3 agents received minimal, correct data |
| Bridge-specific scoring bands in recommendation matrix | Stabilized LTV/DSCR wrong for bridge | Matrix correctly scores transitional loans |

### Decisions That Needed Revision

| Decision | Original | Revised | Lesson |
|----------|----------|---------|--------|
| PPTX reads verified-data.yaml | Assumed file would exist | Rewritten to accept loan-data.yaml directly | Always trace data contracts |
| sample_file (scalar) | Phase 1 outputs scalar path | Changed to sample_files array | Schema must be consistent across all phases |
| LTV/DSCR thresholds | Calibrated for stabilized lending | Added bridge-specific bands | Domain templates need domain practitioner input |
| Quick mode "3 questions" | Promise made in SKILL.md | Actual count was 5-7 prompts | Document wizard steps accurately or don't promise a count |

---

## Review Pattern Analysis

### Common Issues by Reviewer (Round 1)

| Reviewer | Top Issue Types | Frequency |
|----------|-----------------|-----------|
| Error Handling | File existence, YAML parse errors, no fallbacks | 4 Critical, 5 High |
| Integration | Missing files, schema mismatches, cross-phase contract gaps | 1 Critical, 3 High |
| Domain Logic | Missing fields, wrong scoring calibration, incomplete sections | 1 Critical, 4 High |
| Documentation | Unresolved placeholders, inconsistent step numbers | 1 Critical, 5 High |
| DX/UX | Quick mode promise broken, path error messages unhelpful | 1 Critical, 3 High |
| QA/Correctness | `skip_phase_1` shortcut always false | 1 Critical |
| Security | Shell injection patterns (medium), no hard findings | 0 Critical, 0 High |
| Performance | Batch race conditions, infinite loop risk | 0 Critical, 0 High |

### Recurring Patterns

1. **Unverified promises in SKILL.md documentation:** Several High/Critical findings
   were documentation gaps where the SKILL.md described behavior that didn't actually
   exist in the code or agent instructions (step counts, shortcut behavior).

2. **Missing error handling on file I/O:** Every new Python script had at least one
   `load_data()` or `open()` call without a preceding existence check. Error Handling
   was the lens with the most Critical findings.

3. **Cross-phase data contract gaps:** New capabilities added to one phase without
   updating adjacent phases' input/output contracts. Pattern appeared 3 times.

---

## Skills Effectiveness

| Skill | Times Used | Effectiveness |
|-------|------------|---------------|
| acos-loan-doc-generator | Primary delivery skill | High — core functionality delivered |
| acos-financial-statement | New skill, parallel workstream | High — 17 fixes applied via swarm |
| acos-swarm-review | 3 review rounds | High — caught 99+ genuine defects |
| acos-handoff-protocol | ~8 handoffs | High — context preserved across sessions |
| acos-skill-maker | Meta-skill for codifying work | Medium — created, not yet tested live |

### Skills That Need Improvement

- **acos-loan-doc-generator SKILL.md documentation:** Literal `{N}/{M}` placeholders
  left in production instructions. SKILL.md documentation quality should be validated
  as a standard check in swarm reviews.

### Skills That Worked Well

- **acos-swarm-review:** The 8-lens configuration (QA, Security, Performance,
  Integration, Error Handling, Domain Logic, Documentation, DX) provided comprehensive
  coverage. Cross-lens finding confirmation proved highly reliable for prioritization.
- **Wigum loop (both skills):** Convergence behavior was clean. The "validator never
  provides numbers" rule was respected in both the loan doc and financial statement skills.

---

## Learnings Extracted

### Patterns (to replicate)

| ID | Title | Confidence |
|----|-------|------------|
| LEARN-ARCH-001 | Delegated Phase Orchestration | high |
| LEARN-ARCH-002 | Two-Tier Data Model for Token-Efficient Multi-Agent Pipelines | high |
| LEARN-ARCH-003 | Wigum Loop for Iterative Quality Convergence | high |
| LEARN-IMPL-001 | XLSX Cell-Level Extraction with Formula Provenance | high |
| LEARN-IMPL-002 | Styled HTML-to-DOCX via python-docx | high |
| LEARN-IMPL-003 | Digit-Ratio Heuristic for Font Role Detection in PPTX | high |
| LEARN-REVIEW-001 | Multi-Round Swarm Review Remediation | high |
| LEARN-WORKFLOW-001 | Scope Expansion as Additive Stories Within an Epic | medium |
| LEARN-WORKFLOW-002 | Pre-Generation Data Verification Gate | high |

### Anti-Patterns (to avoid)

| ID | Title | Confidence |
|----|-------|------------|
| LEARN-ANTI-001 | Missing Data Contract Between Pipeline Stages | high |
| LEARN-ANTI-002 | Pandoc as Primary Pipeline for Styled DOCX Output | high |
| LEARN-ANTI-003 | Large Work Accumulation Without Intermediate Commits | high |
| LEARN-ANTI-004 | Generic Document Templates Missing Domain-Critical Fields | high |

---

## Recommendations for Future Projects

### Process Improvements

1. **Commit at end of every session** — treat git commits as crash insurance,
   not "done" markers. Never carry uncommitted work across more than one session.

2. **Domain practitioner review before template design** — for specialized document
   types, source the practitioner's completeness checklist before writing templates.
   This prevents domain logic gaps that only surface in swarm review.

3. **Trace data contracts before shipping new components** — for any new pipeline
   component, verify every file it reads is produced by an upstream phase before
   committing. The session manifest schema is the canonical contract.

### Agent Improvements

1. **Phase agents should validate their input files on start** — add explicit
   "input validation" steps to each phase agent that check existence of all
   required input files and emit clear errors if missing.

2. **SKILL.md documentation accuracy** — add a "documentation" check during
   development: scan SKILL.md for unresolved `{N}`, `{M}` placeholders and
   verify all step counts match the actual wizard flow.

### Skill/Flow Improvements

1. **Swarm review: domain logic lens** — include a domain-specific lens in every
   swarm review for specialized industry documents. For PE lending: the lens
   should specifically check for LTC, exit strategy, recourse type, and
   document-type-specific completeness checklists.

2. **Two-tier data pattern** — when building any new multi-agent data pipeline,
   design the full vs brief data tiers upfront, not as a refactor.

3. **PPTX generation: SKILL.md should reference data-to-pptx.py and validate-pptx.py** —
   these scripts are now mature enough to become a documented and tested component
   of the loan doc generator pipeline.

---

## Appendix

### Full Decision Log Reference

`memory/decisions/acos-update-2026-02-22.md` — Framework improvements decision log

### Full Review Log Reference

`.acos/evidence/2026-03-22/SWARM-FIXES/` — Financial statement 17-fix remediation
`.acos/evidence/2026-03-23/SWARM-REVIEW-LOAN-DOC/` — Round 1 swarm review report (56 findings)
`.acos/evidence/2026-03-24/domain-logic-fixes/` — Domain logic remediation evidence
`.acos/evidence/2026-03-24/shell-injection-fix/` — Shell injection fix evidence

### Evidence Bundle Reference

`.acos/evidence/2026-03-15/` — loan-doc-phase-fixes
`.acos/evidence/2026-03-16/` — html-to-pdf, phase3 evidence (referenced in Mar 16 handoff)
`.acos/evidence/2026-03-22/` — SWARM-FIXES (17 financial statement fixes)
`.acos/evidence/2026-03-23/` — SWARM-REVIEW-LOAN-DOC, PPTX-DEFECT-FIX, SKILL-MD-FIXES
`.acos/evidence/2026-03-24/` — domain-logic-fixes, shell-injection-fix

### Key Handoff References

`memory/handoffs/archive/2026-03-16-emergency-handoff.yaml` — Batch mode, HTML→PDF pipeline
`memory/handoffs/archive/2026-03-23-emergency-handoff.yaml` — All major EPIC-001 features
`memory/handoffs/archive/2026-03-30-emergency-handoff.yaml` — PPTX scope expansion + 3 review rounds
`memory/handoffs/archive/2026-04-03-completion-handoff.yaml` — Final completion state

---

*Retrospective generated by ACOS Learning Curve Agent*
*This analysis contributes to ACOS's continuous improvement.*
