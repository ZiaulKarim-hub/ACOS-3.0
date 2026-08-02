# Research Dossier — 005-resurrection-protocol
*(`/preeng.research`. Precondition satisfied: `spec.md` exists. Constitutional Domain Compilation, §0.2,
all four phases. RAG index unavailable (venv missing) — internal priors are drawn from swarm report
`swarm-20260714-084532` + project memory and are tiered T5 with an Assumption note.)*

## Domain focus (research scope)
1. Durable project-registry / index design (per-project sharded JSON, derived-not-stored).
2. Atomic file persistence on APFS (`mkstemp`/`fsync`/`os.replace`; case-insensitivity; inode re-link).
3. cmux 0.64.19 CLI/RPC workspace lifecycle (list/select/close, description tag, read-screen, tree).
4. Claude Code native session persistence (`--resume`/`--session-id`; `~/.claude.json` `projects{}`).
5. Eternity Protocol continuation coexistence (pane-durable vs pane-independent; namespace disjointness).
6. Handoff / reentry semantics (intent core vs disk enrichment; graveyard forensics).
7. Adoption behavior economics (immediate vs deferred payoff; ritual survival).
8. Silent-failure defensive engineering (verified reads; facts-not-verdicts; no green badge).

## Phase 1 — Domain List Generation (DLG)
Output: `domain-brief.md` (entities, processes, methods, standards, metrics, risks, anti-patterns, terms) +
`domain-cqs.md` (18 Competency Questions, CQ1–CQ18). The brief encodes the one-operator/one-machine domain
whose dominant fact is that **silent failure is the base rate**, which forces every design choice toward
verified read-backs and away from verdicts.

## Phase 2 — Lattice Expansion Loop
Output: `domain-lattice.json` (canonical schema §2.3). For each CQ a bounded subgraph (≤2 hops) expresses
Problem→Method→Metric→Standard and Risk→Control→Evidence. Node types are from the controlled vocabulary
(entity, process, method, metric, standard, risk, pattern, anti_pattern, term, cq); edges carry explicit
types (uses, measured_by, constrained_by, mitigates, depends_on, part_of, implements, contradicts). The
lattice deliberately encodes the *killed* alternatives as `anti_pattern` nodes joined to the winning method by
a `contradicts` edge (e.g., `M-sharded-store contradicts ANTI-shared-master / ANTI-yaml-truncation /
ANTI-sqlite-opaque`), so the design's negative space is machine-checkable, not just prose.

## Phase 3 — Evidence Ledger
Output: `evidence-ledger.json` (schema §2.4), 24 entries, each tiering a major claim:
- **T1 (authoritative):** POSIX/LWN/SQLite fsync-before-rename durability; APFS case-insensitivity.
- **T3 (empirical, this machine, 2026-07-14/16):** concurrency (3/25 unlocked survive as valid JSON; mkstemp
  0/360 torn); 16/16 registry rebuild; graveyard forensics (17/17 dangling, ~10/17 never read); duplicate
  census (21 sessions ≈ 7 projects, 13/21 ACOS 3.0); live inventory (cmux 0.64.19, Claude 2.1.212, 643
  transcripts/1.2 GB, 963 daemon entries, 18 handoff dirs, ~230 RPC methods); silent-failure base rate
  (ALL-GREEN doctor over 2,000+ failures; `head -40` hiding 34/74, confirmed live); `sanitize(cwd)`
  non-injectivity; YAML silent truncation (19/30); `identify --surface` fail-open; argv-vs-send delivery.
- **T4 (vendor doc, UNVERIFIED until Phase-0):** cmux 0.64.x RPC behavior (`workspace.select/close`,
  `surface.resume.*`), Agent Hibernation, `customDescription` restart survival, `automation.autoNamingAgent`.
- **T5 (internal priors):** SPINE 1–7; Eternity incident history (2026-06-26 cross-pane contamination,
  f639310 project-scoping fix, self-expiring dead-surface marker); adoption economics (147 hand-run
  `/acos-complete`); DR-1 ship-gate discipline; blind round-trip / Wigum-cap pattern. **Assumption:** T5
  priors substitute for the unavailable RAG index.

## Phase 4 — Agent Emission (Pre-Eng Outputs)
The domain brief, CQ list, lattice, and ledger feed the PM/Dev/QA agent instructions (`/preeng.instructions`)
and the plan/tech-PRD/data-model (`/preeng.plan`); the diagnostic slice (Phase-0 probe battery) is the
mandatory problem-before-solution gate (§0.3). Metric/governance scaffolding is defined in `spec.md §Metrics`
and `plan.md` (instrumented at `.acos/metrics/agent-completions.log` + `~/.acos/registry-audit.jsonl`).

## VALIDATION NOTE (mechanical)
Computed by `build_research.py` over `domain-lattice.json` (BFS ≤2 hops per CQ, requiring the reachable set
to contain ≥1 `method` + ≥1 `metric` + ≥1 (`standard` OR `pattern`)):

- **Nodes: 121** (method 24, metric 16, standard 13, pattern 8, anti_pattern 12, risk 9, entity 9, process 6,
  term 6, cq 18). **Edges: 182.**
- **CQ nodes: 18. Covered: 18. CQ coverage = 100.0%** (target ≥95% — PASS).
- **Structural checks:** 0 orphan nodes; every edge endpoint resolves to a defined node; all node types are in
  the controlled vocabulary; all edge relations are in the controlled relation set. **No critical violations.**
- **Evidence ledger: 24 entries**, every lattice claim tiered T1/T3/T4/T5; `lattice_node_ids` back-reference
  from each entry, and each node's `source_ids` are the inverse mapping (consistent by construction).
- **Evidence quality:** load-bearing atomicity/identity/graveyard/silent-failure claims are T3
  (measured-on-machine, freshness ≤3 days); durability foundations are T1; every cmux 0.64.x *behavior* claim
  is T4 and explicitly UNVERIFIED, gated behind the Phase-0 probe battery before the close skill may ship.

## Open verification items carried into planning (UNVERIFIED)
cmux `workspace.close` against a live Claude session; last-workspace-in-window close; `customDescription`
restart survival; `workspace.select`/`surface.resume.*`/`session.restore_previous` behavior; the 1-in-6 silent
prompt drop; `--command` shell-parse-vs-exec; fsync-before-rename durability (docs-based). All routed to the
Phase-0 diagnostic slice; solution requirements resting on them are marked `Assumption` in `spec.md` and
`plan.md`.
