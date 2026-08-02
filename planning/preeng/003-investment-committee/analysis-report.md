# Cross-Artifact Analysis Report — ACOS Investment Committee (003-investment-committee)

**Command:** `/preeng.analyze` output.
**Date:** 2026-07-07 · **Session:** preeng-003-investment-committee.
**Grounding:** all on-disk artifacts under `planning/preeng/003-investment-committee/` +
`.acos/swarm/swarm-20260707-141351/synthesis/report.md`.

---

## 1. Artifact presence

| Artifact | Present | Notes |
|----------|:------:|-------|
| `spec.md` | yes | canonical PRD, 13 sections + One-Page Digest |
| `research.md` | yes | Phase-4 narrative synthesis |
| `domain-brief.md` | yes | Phase-1 domain brief |
| `domain-cqs.md` | yes | 12 required + 3 derived CQs, all lattice-answerable |
| `domain-lattice.json` | yes | 78 nodes / 119 edges / 100% CQ coverage |
| `evidence-ledger.json` | yes | 36 tiered entries |
| `research_qa_report.json` | yes | qa_status = APPROVED |
| `plan.md` | yes | 6 load-bearing decisions; Demo 1/2/3; orchestration vs ACOS |
| `tech_prd.md` | yes | component architecture + engine contracts + APA/PSA |
| `data-model.md` | yes | 16 entities; Objection->fact + Axis S mapping |
| `planning_qa_report.json` | yes | qa_status = APPROVED |
| `stories.json` | yes | 11 stories across 6 epics |
| `tasks/*.md` | yes | 15 vertical-slice files (PM/Dev/QA + Learnings) |
| `tasks_qa_report.json` | yes | qa_status = APPROVED |
| `analysis-report.md` | yes | this file |
| `cage_preeng_nodes.csv` | yes | 36 nodes |
| `cage_preeng_edges.csv` | yes | full BLOCKER->...->PATTERN chain present |
| `agent_instructions/{pm,dev,qa}.md` | yes | emitted by `/preeng.instructions` |

**Verdict:** the full pre-engineering artifact set is present and internally cross-referenced.
No missing prerequisites; no ERROR gates tripped (research + planning + tasks QA all APPROVED,
none REJECTED).

---

## 2. QA status roll-up

| Stage | Report | qa_status |
|-------|--------|-----------|
| research | `research_qa_report.json` | **APPROVED** (coverage >=95%, no critical structural violations) |
| planning | `planning_qa_report.json` | **APPROVED** (all constraints/entities covered; open items non-blocking) |
| tasks | `tasks_qa_report.json` | **APPROVED** (15 slices; PM/Dev/QA + Learnings; walking skeleton first) |

All open issues are NON-BLOCKING and honestly tracked (greenfield UX constants; Axis S / same-
fact detection design surface; OKOA governance unknowns; autopilot smoke-test).

---

## 3. CQ coverage + evidence quality

- **CQ coverage:** 12/12 required CQs answerable from the lattice within 2 hops = **100%**
  (>=95% target). 3 derived CQs (CQ-13..15) extend coverage.
- **Evidence ledger:** 36 entries. Tier distribution T1=7 (regulator/standard), T2=8 (expert),
  T3=12 (empirical/academic), T5=9 (internal ACOS). No T4 (no community-tool source was
  load-bearing) — an intentional, disclosed posture.
- **Grounding discipline:** every architecture claim is anchored to an existing ACOS asset
  where one exists (axiom-synthesis, legal-analyst, dr2 consensus_check, fin-stmt bounce-up
  idiom, autopilot handler, transcript-on-disk). Two lattice nodes (`metric-cq-coverage`,
  `risk-refi-exit`) are supported transitively/by governance definition, not a coverage gap.
- **Traceability:** spec FR-* -> lattice nodes -> tech_prd components -> slices is intact
  (see tech_prd §5 and each slice's Traceability evidence line).

---

## 4. Canonical-candidate annotations (§0.6 Bloat Management)

Artifacts are annotated, not deleted. Categories: **Active** (recent + needed), **Review**
(canonical-example candidates worth promoting as templates), **Burn Pile** (safe to archive
later).

**Active (recent + needed for the build):** all 15 `tasks/*.md`; `plan.md`; `tech_prd.md`;
`data-model.md`; `stories.json`; the three QA reports; `domain-lattice.json`;
`evidence-ledger.json`; both CAGE CSVs; `agent_instructions/*`.

**Review — canonical-example candidates (exemplary; promote as reusable templates):**
- `spec.md` — an unusually complete PRD with an explicit Diagnostics section tying D1-D6 to
  requirements and a One-Page Digest; **canonical PRD template candidate.**
- `data-model.md` §4 + §18 — the Objection->axiom-synthesis-`fact` + Axis S mapping is a clean
  worked example of "domain adapter over an existing engine without forking it"; **canonical
  reuse-adapter pattern candidate.**
- `tasks/SLICE-C3-deterministic-verdict.md` — the zero-trust QA gate "grep the entire verdict
  path for any LLM call that writes the verdict word" is an exemplary determinism check;
  **canonical anti-narration QA-gate candidate.**
- `tasks/SLICE-B2-blind-opening-pass.md` — the "zero cross-visibility" independence attestation
  is a reusable anti-groupthink slice template; **canonical independence-first slice candidate.**
- `domain-lattice.json` — fully connects all 16 risk categories to methods+metrics+standards;
  **canonical lattice-density example.**

**Burn Pile (safe to archive later, once the build stabilizes):** none yet — this is a fresh
pre-engineering pass; nothing is stale. Re-evaluate after Demo 2 (older fixture scaffolds from
DIAG-01 may become archivable once real intake exists).

---

## 5. CAGE session trace summary

- `cage_preeng_nodes.csv`: **36 nodes** (BLOCKER x5, TOOL x5, FINDING x3, DECISION x6,
  ARTIFACT x6, OUTCOME x3, PATTERN x4, ANTI_PATTERN x4).
- `cage_preeng_edges.csv`: **>=1 full chain present** —
  `BLK-01 (LLM-narrated verdict hazard) -> TOOL-01 (axiom-synthesis resolve.py) -> FIND-01
  (consensus != correctness) -> DEC-01 (deterministic asymmetric-veto verdict) -> ART-01
  (verdict.md / compute_verdict.py) -> OUT-01 (reproducible verdict; UNRESOLVED first-class) ->
  PAT-01 (structural-guardrails-over-debate)`. Two additional full chains encode the
  main-conversation-moderator discovery (BLK-02->PAT-02) and the concentration/fraud coverage
  discovery (BLK-03->PAT-03). Anti-patterns are wired via `contradicts` from the decisions
  that avoid them.

---

## 6. Cross-artifact consistency notes

- The deterministic deal-breaker rule and verdict states are stated identically in `spec.md`
  (FR-M7 / Appendix C), `tech_prd.md` (§1.5), `data-model.md` (§11 Verdict), and
  `tasks/SLICE-C3`. Consistent.
- The Axis S ladder (`informational < limitation < material-risk < deal-breaker-candidate`) is
  identical across spec §4.1, tech_prd §1.3, data-model §6, and SLICE-C1. Consistent.
- The on-disk session layout is identical in spec §4.2, tech_prd §2, and data-model §17.
  Consistent.
- The 6 epics map 1:1 onto stories.json epics and onto the 15 slices; the demo waves in
  `plan.md` §5 match the `spec.md` Rollout Plan. Consistent.
- **Open surfaces (carried, not resolved):** "same underlying fact" cross-discipline detection
  (entity-linking); Axis S calibration against real objection data; OKOA governance unknowns;
  autopilot x interactive smoke-test; Mode B constant tuning. All are `Assumption`/Open-marked
  in spec Open Questions and echoed in the QA reports — no silent gaps.
