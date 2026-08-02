# SLICE-A1-roster-coverage-map — Seat roster schema + 16-risk coverage map

**Parent story:** STORY-A1 · **Epic:** EPIC-A · **Effort:** S · **Demo:** Demo 1/2
**slice.yaml mapping:** Objective->`objective`; Allowed files->`files_allowed`;
DoD+evidence gates->`acceptance_criteria`; QA verification->`verification_method`.

## PM (Planner / LCE brief)

**Objective (single, narrow):** Define the `Seat` + `ExpertProfile` schema for the
**numbered, stable roster** — 8 core voting seats (#1-8), the non-voting **Deal Advocate**
(#9), the non-voting Gap-Hunter/Chair-agent (#10), and 5 deal-triggered optionals (#11-15) —
and a machine-checkable **16-risk coverage map** asserting every risk category has a named
default owner (zero uncovered), with the Portfolio seat (#7) marked `scope: fund`.

**In-scope:** `roster.yaml` (numbered seats #1-10 + optional-seat triggers #11-15);
`coverage-map.yaml` (16 risk categories -> owning seat_id, per spec Appendix A, reflecting
the Credit+Valuation merge into #1, the Environmental demotion to optional #15 with its
legal-materiality sub-lens folded into #4, and Finance's #2 core ownership of Exit/Refi);
a `check_coverage.py` that fails if any risk category is unowned.

**Out-of-scope:** the seat *prompt* content (SLICE-A2); intake; synthesis.

**Allowed files/contexts:** `.claude/skills/acos-investment-committee/roster.yaml`,
`coverage-map.yaml`, `scripts/check_coverage.py`; READ-ONLY: spec Appendix A, domain-lattice
`seat-*` + `metric-risk-coverage` nodes.

**Numbered roster (stable — the chair and transcript refer to seats by number):**

| # | Seat | Voting | Scope | Notes |
|---|------|--------|-------|-------|
| 1 | Credit & Valuation | yes | deal | merges former Credit + Valuation seats; TWO sub-passes: collateral-value + repayment-capacity |
| 2 | Finance | yes | deal | spread/lender IRR/capital structure; core-owns Exit/Refi (risk category #9), no longer a fold-in |
| 3 | Accounting | yes | deal | QoE/GAAP/add-backs; OWNS the single normalized-NOI claim consumed by #1 and #2 (ROCO fraud tripwire) |
| 4 | Legal & Structural | yes | deal | title/lien/SPE/guaranty + environmental-LEGAL sub-lens (CERCLA/Phase I currency) scoped to legal/financial materiality only |
| 5 | Insurance & Climate | yes | deal | non-renewal/premium-spike that breaks DSCR |
| 6 | Sponsor & Fraud-Forensics | yes | deal | "assume fabricated until externally corroborated" |
| 7 | Portfolio & Concentration | yes | **fund** | reads the fund loan tape, NOT deal-scoped |
| 8 | Strategy | yes | deal | thesis fit / opportunity cost / off-mandate distraction; same falsifiable-objection discipline; NOT an advocate |
| 9 | Deal Advocate (**NEW**) | **no** | deal | structurally separate defense role: steelmans the deal and answers objections with the best good-faith mitigant the evidence supports; NO hole-hunting, NO scrutiny vote; its mitigants pass the SAME falsification gate as objections (argue in good faith, never fabricate) |
| 10 | Gap-Hunter / Chair-agent (was #9) | **no** | deal | procedural meta-seat; each round selects who has something material to add; structurally distinct from the Advocate (#9) — one is defense, one is process |
| 11 | Construction/Completion | optional | deal | seated only on trigger (ground-up / major renovation) |
| 12 | Tax | optional | deal | seated only on trigger (complex multi-entity / reassessment risk) |
| 13 | Market/Macro | optional | deal | seated only on trigger (new-supply / forward-stress deal types) |
| 14 | Compliance | optional | deal | seated only on trigger (multi-state / regulatory complexity) |
| 15 | Environmental/Physical-Condition | optional | deal | fires ONLY on a flagged REC or collateral type; full physical/environmental review (seat #4 covers only the legal-materiality sub-lens by default) |

**16-risk coverage map (default owner when the corresponding optional is NOT triggered):**

| # | Risk category | Default owner | Notes |
|---|---------------|----------------|-------|
| 1 | Credit/Borrower | Seat 1 (repayment-capacity sub-pass) | |
| 2 | Collateral/Valuation | Seat 1 (collateral-value sub-pass) | |
| 3 | Market/Macro | Seat 1 (collateral-value sub-pass, sub-check) | promotable to optional #13 |
| 4 | Structural/Legal | Seat 4 | |
| 5 | Title/Survey | Seat 4 (sub-pass) | |
| 6 | Environmental | Seat 4 (legal-materiality sub-lens ONLY — CERCLA/Phase I currency) | full condition review promotable to optional #15 (fires on flagged REC/collateral type) |
| 7 | Construction/Completion | Seat 1 (collateral-value sub-pass, baseline) | promotable to optional #11 |
| 8 | Cash-Flow/DSCR/Debt Yield | Seat 1 (repayment-capacity sub-pass) | cross-checked by Seat 3 (NOI) and Seat 5 (DSCR transmission) |
| 9 | Interest-Rate/Refi/Exit | Seat 2 | core-owned (no longer a Credit fold-in) |
| 10 | Sponsor/Track Record | Seat 6 | |
| 11 | Concentration/Portfolio | Seat 7 (fund-scoped) | |
| 12 | Tax | Seat 4 (fold-in) | promotable to optional #12 |
| 13 | Insurance | Seat 5 | |
| 14 | Fraud/Misrepresentation | Seat 6 | |
| 15 | Regulatory/Compliance | Seat 4 (state sub-pass) | promotable to optional #14 |
| 16 | ESG/Physical Climate | Seat 5 (merged) | |

Seat 3 (Accounting), Seat 8 (Strategy), and **Seat 9 (Deal Advocate)** do NOT primarily own
one of the 16 risk categories — Accounting cross-checks #1/#2/#8/#14 and owns the shared
normalized-NOI claim (a cross-cutting artifact, not a category); Strategy contributes a
distinct strategic-fit falsifiable-objection lens outside the 16-category deal-risk taxonomy;
the Deal Advocate (#9) owns NO risk category by design — it is the structurally separate
defense/steelman role, not a risk-owning scrutiny seat, and is exempted the same way as
Accounting and Strategy. `roster.yaml` MUST encode this explicitly (e.g.
`owned_risk_categories: []` + a `cross_checks` / `owns_shared_artifact` / `is_defense_role`
field) so `check_coverage.py` does not misreport any of the three as gaps.

**Step-by-step:**
1. Encode the 10 numbered seats (8 voting + non-voting Deal Advocate #9 + non-voting
   Gap-Hunter/Chair-agent #10) with `seat_id` (stable integer), `scope`,
   `owned_risk_categories`, `voting`, and optional-seat trigger conditions for #11-15.
2. Encode the 16-risk -> seat map exactly per the table above (Exit/Refi core-owned by
   Finance #2; Tax folds into Legal #4, promotable to #12; Environmental demoted to a
   legal-materiality sub-lens under Legal #4 by default, full review promotable to
   optional #15).
3. `check_coverage.py`: assert 0 unowned categories; assert Portfolio (#7) `scope: fund`;
   assert Gap-Hunter (#10) `voting: false`; assert Deal Advocate (#9) `voting: false` and
   `owned_risk_categories == []`; assert Accounting (#3), Strategy (#8), and Deal Advocate
   (#9) are explicitly exempted from the "must own >=1 category" check via their documented
   cross-check / shared-artifact / defense-role fields (not silently missing).

**Definition of Done:**
- Artifacts: `roster.yaml`, `coverage-map.yaml`, `scripts/check_coverage.py`.
- Validation: `check_coverage.py` exits 0 (zero unowned); Portfolio fund-scoped; Deal
  Advocate (#9) and Gap-Hunter (#10) both non-voting; Accounting/Strategy/Advocate
  explicitly exempted, not silently unowned.
- Evidence bundle: coverage-check transcript showing all 16 categories mapped and the
  seat-number stability (no seat renumbered from THIS table onward — #9 Deal Advocate and
  #10 Gap-Hunter are the new stable numbering; the map supersedes any prior #9-Gap-Hunter
  draft).

## Dev (Executor)

**Execution notes:** stdlib-only Python; YAML fixtures. Mirror the numbered roster and
coverage table above verbatim; do not invent risk categories; do not renumber seats. Note
for anyone touching earlier drafts: Gap-Hunter moved from #9 to #10 and the Deal Advocate is
a brand-new #9 — this is a deliberate, one-time renumbering, not an oversight.

**Evidence Bundle:** 1) Summary; 2) Traceability (FR-M1, FR-M2, FR-M17 -> fields); 3) Quality
(schema lint); 4) Testing (check_coverage transcript, all 16 mapped, exit 0); 5) Compliance
(matches Appendix A / this table); 6) Operational; 7) Self-assessment.

## QA (Zero-Trust Verifier)

Verify: (a) count risk categories = 16 and each maps to a real seat_id (recompute from the
map, do not trust the summary); (b) Portfolio (#7) `scope: fund`, Deal Advocate (#9)
`voting: false`, and Gap-Hunter (#10) `voting: false` all present; (c) run `check_coverage.py`
yourself and confirm exit 0; (d) confirm no seat claims a category outside the table above;
(e) confirm Accounting (#3), Strategy (#8), and Deal Advocate (#9) are explicitly exempted
(not silently unowned) and Environmental's default is Seat 4's legal-materiality sub-lens,
not a full condition review; (f) confirm the Deal Advocate (#9) and Gap-Hunter (#10) are
distinct seat_ids with distinct roles (defense vs procedural) — reject if they were collapsed
into one seat. Reject on any unowned/mislabeled category or any seat renumbering beyond this
table's numbering.

**Evidence gates:** 16/16 covered; fund-scoped Portfolio (#7); non-voting Deal Advocate (#9);
non-voting Gap-Hunter (#10); map == the coverage table above; seat numbers stable 1-15.

## Dev Learnings
_(fill: any ambiguity in the fold-in categories; schema decisions; how the Advocate/#9 vs
Gap-Hunter/#10 split was encoded without collapsing the two roles.)_

## QA Learnings
_(fill: coverage-count recomputation; any silent-PASS category risk found; any place the
Advocate could have been mistaken for a risk-owning seat.)_
