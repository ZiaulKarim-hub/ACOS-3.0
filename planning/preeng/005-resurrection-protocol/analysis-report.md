# Cross-Artifact Analysis Report — 005-resurrection-protocol
*(`/preeng.analyze`. Facts, not verdicts — presence/bytes computed at write time; QA statuses read from the JSON reports. No green badge is implied; a MISSING or REJECTED line is the only signal that matters.)*

## 1. Artifact presence & byte counts
| artifact | status | bytes |
|---|---|---|
| `spec.md` | PRESENT | 22529 |
| `research.md` | PRESENT | 5921 |
| `research_qa_report.json` | PRESENT | 774 |
| `domain-brief.md` | PRESENT | 6618 |
| `domain-cqs.md` | PRESENT | 6566 |
| `domain-lattice.json` | PRESENT | 60951 |
| `evidence-ledger.json` | PRESENT | 15716 |
| `plan.md` | PRESENT | 7872 |
| `tech_prd.md` | PRESENT | 6830 |
| `data-model.md` | PRESENT | 4498 |
| `planning_qa_report.json` | PRESENT | 878 |
| `stories.json` | PRESENT | 17767 |
| `tasks_qa_report.json` | PRESENT | 723 |
| `analysis-report.md` | MISSING | 0 |
| `cage_preeng_nodes.csv` | PRESENT | 8159 |
| `cage_preeng_edges.csv` | PRESENT | 2205 |

(Plus `tasks/` = 14 slice files; `_preseed/` and `_worker_prompt.md`/`_runner_config.json` are inputs, not outputs.)

## 2. QA gate status (each command's mechanical QA)
- `/preeng.research` -> `research_qa_report.json` = **APPROVED**
- `/preeng.plan` -> `planning_qa_report.json` = **APPROVED**
- `/preeng.tasks` -> `tasks_qa_report.json` = **APPROVED**
- No ERROR precondition gate tripped in any command (spec.md present before research; research not REJECTED before plan; planning not REJECTED before tasks).

## 3. Domain coverage & evidence quality
- **Lattice:** 121 nodes, 182 edges; **18 CQ nodes; CQ coverage = 100.0%** (target >=95%, mechanically computed by <=2-hop BFS requiring method+metric+standard/pattern per CQ). 0 orphan nodes; controlled vocabulary clean; no critical structural violations.
- **Evidence ledger:** 24 entries, tiered T1=2, T3=14, T4=2, T5=6. Load-bearing atomicity/identity/graveyard/silent-failure claims are T3 (measured-on-machine, freshness <=3 days); durability foundations T1; every cmux 0.64.x *behavior* claim is T4 UNVERIFIED and Phase-0-gated; T5 internal priors substitute for the unavailable RAG index (Assumption).
- **Backlog:** 6 epics, 14 vertical slices, 14 task files; each slice carries PM/Dev/QA + `## Dev Learnings` / `## QA Learnings` + a DoD mapping to `slice.yaml` acceptance_criteria + verification_method. EPIC-0 is the mandatory diagnostic slice; Demo 1/2/3 present; SLICE-40 (DR-1) is the ship gate.

## 4. CAGE pre-eng session trace
- `cage_preeng_nodes.csv` (39 nodes) + `cage_preeng_edges.csv` (36 edges) encode the pre-eng session (BLOCKER/TOOL/FINDING/DECISION/ARTIFACT/OUTCOME/PATTERN/ANTI_PATTERN).
- **Required full chain present & consecutively linked:** `CB-CONC (BLOCKER) -> CT-CRASHTEST (TOOL) -> CF-CONC (FINDING) -> CD-SHARDED (DECISION) -> CA-DATAMODEL (ARTIFACT) -> CO-DURABLE (OUTCOME) -> CP-ONEWRITER (PATTERN)`.

## 5. Bloat management & canonicalization (§0.6 — annotate only, delete nothing)
- **Active (recent + needed):** the six `resurrection/` scripts + the two skills + the three Phase-0 fixes; all six pre-eng artifact families in this directory.
- **Review (canonical-candidate — exemplary, reusable framework-wide):** `registry_lib.py` atomic-write helper (mkstemp->fsync->os.replace->fsync(dir)); the **verified read-back receipt** pattern (`P-RECEIPT`); the **derived-index-cannot-dangle** rebuild pattern (`P-DERIVED`); `build_research.py`'s mechanical CQ-coverage computation. These are strong candidates for promotion to shared ACOS references.
- **Burn Pile (safe to archive later, not now):** throwaway `RESURRECTION-PROBE-*` workspaces and their transcripts once outputs are archived; the scratch crash-test dir. Nothing is deleted here — annotated only.

## 6. Residual risks carried forward
- All cmux 0.64.x behavior claims remain UNVERIFIED until the Phase-0 probe battery (SLICE-00) passes; the close skill (EPIC-2) must not ship before it.
- The single highest-risk dependency (`next_action` generation quality) and adoption decay are both answered only at Demo 3 (DR-1). Until the recorded round-trip exists, the skill is not shipped.
