# SLICE-B3-expert-research-swarms — Per-expert private research swarms

**Parent story:** STORY-B2 · **Epic:** EPIC-B · **Effort:** M · **Demo:** Demo 1 (3-seat) -> Demo 2 (full)
**slice.yaml mapping:** Objective->`objective`; Allowed files->`files_allowed`;
DoD+evidence gates->`acceptance_criteria`; QA verification->`verification_method`.

## PM (Planner / LCE brief)

**Objective (single, narrow):** Build the mechanism that lets each of the **9 expert seats**
(the 8 voting seats #1-8 plus the Deal Advocate #9 — NOT the procedural Gap-Hunter #10) spawn
its **own private swarm of 2-4 `Task(general-purpose)` research bots**, sized to what its
discipline actually needs for the deal, during its isolated blind-opening pass (SLICE-B2).
Each swarm does discipline-specific deep/external research on top of the shared deal-brief +
evidence-index (SLICE-B1) and reports **ONLY to the spawning expert** — never to another
seat, never to the chair. Every citation a swarm surfaces is captured into the evidence
ledger. **ONE mode only** — there is no quick/deep tiering; every expert gets the same
swarm mechanism, sized 2-4 bots per its own judgment of need.

**In-scope:** `expert_swarm.py` — the per-seat swarm-spawn helper each expert's own `Task()`
context invokes (per the instruction wired into its template in SLICE-A2): (1) accepts a
seat_id + discipline research query + a requested bot count; (2) clips/rejects any request
outside the **2-4 bound**; (3) spawns that many `Task(general-purpose)` bots, each given
ONLY the shared deal-brief + evidence-index (SLICE-B1) plus the seat's discipline-specific
query — never another seat's swarm output, objection, or mitigant; (4) enforces **private
reporting isolation** — every bot's findings return to the spawning seat's own scratch space
only (e.g. `rounds/round-00/opening/{seat}/swarm/`), unreadable by any other seat's process in
the same run; (5) **citation capture** — every citation a swarm bot returns is appended,
tagged by `seat_id` + bot index, to the session's evidence ledger so fact-builder/synthesis
(C1) and QA can trace every mitigant/objection to a real source.

**Out-of-scope:** the shared upfront extraction pass itself (SLICE-B1, already built); the
top-level per-seat `Task()` fan-out/dispatch (SLICE-B2 — B3 is what a seat's OWN Task()
invokes internally, not the outer orchestration); fact-builder/synthesis consumption of swarm
citations (SLICE-C1); any quick/deep tiering (explicitly rejected — one mode only).

**Allowed files/contexts:** `.claude/skills/acos-investment-committee/scripts/expert_swarm.py`;
READ-ONLY: `seats/*.md` (SLICE-A2, for the swarm-spawn instruction contract each template
carries), `deal-brief.yaml` + `evidence-index.yaml` (SLICE-B1), domain-lattice
`proc-independence-first` + `method-model-diversity` nodes.

**Step-by-step:**
1. Define the swarm-spawn contract: `seat_id` + discipline query + requested `bot_count` ->
   N `Task(general-purpose)` bots, each context-limited to the seat's discipline query plus
   the shared deal-brief/evidence-index — never another seat's swarm, objection, or mitigant.
2. Enforce the **2-4 bound**: clip or reject any out-of-range request; log
   requested-vs-granted count for audit (sized-to-need, not a fixed count).
3. Enforce **private-reporting isolation**: each bot's findings are written ONLY into the
   spawning seat's own scratch path; no shared/global location any other seat's process can
   read during the same run.
4. **Citation capture**: append every citation a swarm bot returns — tagged by `seat_id` +
   bot index — to the evidence ledger built on SLICE-B1's scaffold, so nothing a swarm found
   is lost or untraceable.
5. Confirm single-mode: no quick/deep tiering flag, config key, or code path exists anywhere
   in this script.
6. Confirm the Gap-Hunter (#10) never triggers a spawn — only the 9 expert seats (#1-9) do,
   per the capability wired into their templates in SLICE-A2.

**Definition of Done:**
- Artifacts: `scripts/expert_swarm.py`; a fixture run showing at least 2 different expert
  seats each spawning between 2 and 4 bots.
- Validation: bot count per seat always within [2,4]; each seat's swarm output is isolated
  (unreadable by any other seat's process in the same run — the load-bearing independence
  check, same rigor as SLICE-B2's zero-sibling-output check); every swarm citation lands in
  the evidence ledger tagged by seat_id; no quick/deep mode flag present anywhere; Gap-Hunter
  (#10) never spawns.
- Evidence bundle: swarm-spawn transcript for >=2 expert seats + the resulting evidence-ledger
  citations (tagged by seat_id) + an isolation attestation.

## Dev (Executor)

**Execution notes:** subscription-only via `Task()`. Whether a `Task(general-purpose)`
sub-agent can itself call `Task()` to spawn further sub-agents (true nesting) vs a
script-mediated flat fan-out coordinated from within the seat's own context is a build-time
architecture decision this slice must resolve empirically — either satisfies "each expert
spawns its own swarm" as long as **reporting isolation** and **citation capture** hold;
document the actual mechanism chosen in Dev Learnings. Respect the Independence Wall / Oracle
hooks. Write-to-disk for citations is immediate (durability), matching B1/B2's pattern.

**Evidence Bundle:** 1) Summary; 2) Traceability (swarm-spawn contract -> fields; citation ->
ledger mapping); 3) Quality (bot-count-bound lint; isolation-path lint); 4) Testing
(>=2-seat spawn transcript, bound enforcement, isolation check); 5) Compliance (no
cross-seat swarm visibility; single-mode only; Gap-Hunter never spawns); 6) Operational
(immediate citation persistence); 7) Self-assessment.

## QA (Zero-Trust Verifier)

Verify: (a) run the swarm mechanism for >=2 different expert seats and recount that each
spawned between 2 and 4 bots (do not trust the summary); (b) inspect for isolation — confirm
each seat's swarm findings are NOT readable from any other seat's process/output during the
same run, mirroring SLICE-B2's zero-sibling-output check; (c) recount every citation the
swarm bots surfaced against what actually landed in the evidence ledger, confirming correct
`seat_id` tagging and zero dropped citations; (d) grep the script/config for any quick/deep
tiering flag or code path — reject if one exists (single mode only, per DELTA 3); (e) confirm
the Gap-Hunter (#10) never triggers a swarm spawn — only seats #1-9 do. Reject if any seat's
swarm output leaks to another seat, if any bot count falls outside 2-4, or if any citation is
dropped.

**Evidence gates:** bot count in [2,4] per seat, recomputed; zero cross-seat swarm-output
visibility; citation-to-ledger completeness with correct seat tagging; single-mode confirmed
(no tiering); Gap-Hunter (#10) never spawns.

## Dev Learnings
_(fill: which nesting mechanism was actually used — true nested Task() vs script-mediated
flat fan-out — and why; how the 2-4 sizing-to-need heuristic was implemented per discipline.)_

## QA Learnings
_(fill: any subtle swarm-output leak between seats; citation-tagging mismatches found;
confirmation that no tiering crept in.)_
