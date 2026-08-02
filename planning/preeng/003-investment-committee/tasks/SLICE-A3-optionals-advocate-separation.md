# SLICE-A3-optionals-advocate-separation — Deal-triggered optionals + advocate separation

**Parent story:** STORY-A1 · **Epic:** EPIC-A · **Effort:** S · **Demo:** Demo 2
**slice.yaml mapping:** Objective->`objective`; Allowed files->`files_allowed`;
DoD+evidence gates->`acceptance_criteria`; QA verification->`verification_method`.

## PM (Planner / LCE brief)

**Objective (single, narrow):** Implement deal-triggered optional-seat promotion
(#11 Construction/Completion, #12 Tax, #13 Market/Macro, #14 Compliance/Regulatory,
#15 Environmental/Physical-Condition), compose the roster resolver with the chair's
`exclude/include` command, and mechanically enforce that the Deal Advocate (#9) NEVER
casts a scrutiny vote.

**In-scope:** `optional_triggers.yaml` (asset_type/attribute -> optional seat); a
`resolve_roster.py` that takes a Deal + `--seats lean|full` + an optional exclude/include set
and returns the active roster (writing `active_seats` to the session manifest); a hard
assertion that `ADVOCATE(#9).voting == false` and that #9 never appears in a scrutiny tally.

**Out-of-scope:** the optional seats' full prompt authoring beyond a charter stub; synthesis;
the chair-command PARSING itself (that lives in SLICE-D2 — this slice exposes the resolver
D2 calls).

**Allowed files/contexts:** `.claude/skills/acos-investment-committee/optional_triggers.yaml`,
`scripts/resolve_roster.py`; READ-ONLY: `roster.yaml`, `coverage-map.yaml` (SLICE-A1), spec
Appendix A, domain-lattice `seat-advocate` + `std-three-lines`.

**The roster (stable numbers):** scrutiny seats #1–#8; Deal Advocate #9 (always present,
defense role, NON-voting); Gap-Hunter/Chair-agent #10 (procedural, non-voting, speaker-picker);
deal-triggered optionals #11–#15. NOTE: Exit/Refinance is NOT an optional — it folded into
Finance (#2). Every one of the 16 mapped risk categories still has an owner.

**Step-by-step:**
1. Encode triggers (e.g. `asset_type: construction -> #11 Construction/Completion`;
   `borrower_entity: SPE-stack -> #12 Tax`; `collateral_flag: REC -> #15 Environmental/Physical`).
2. `resolve_roster.py`: `lean` = #1–#8 + #9 Advocate + #10 Chair; `full` = + all triggered
   optionals (#11–#15). Accept an `--exclude`/`--include-only` set (as the D2 chair command
   supplies) and apply it AFTER promotion; write the resulting `active_seats` to
   `.acos/investment-committee/<session>/manifest.yaml`. When a seat is excluded, emit a
   Gap-Hunter (#10) uncovered-risk log line (e.g. "excluding #3 -> normalized-NOI veracity
   unowned this session").
3. Assert-and-fail if any code path would let #9 vote or appear in a scrutiny tally.

**Definition of Done:**
- Artifacts: `optional_triggers.yaml`, `scripts/resolve_roster.py`.
- Validation: a fixture deal with a construction attribute promotes #11; an `exclude #3`
  produces an active_seats set without #3 plus the uncovered-risk log; #9 excluded from the
  voting set in lean and full.
- Evidence bundle: resolve_roster transcripts for lean, full, and an exclude-command run.

## Dev (Executor)

**Execution notes:** three-lines-of-defense is load-bearing — the Advocate-non-voting rule is
an assertion, not a comment. `active_seats` in the manifest is the single source of truth the
moderator (D1/D2) reads. stdlib-only.

**Evidence Bundle:** 1) Summary; 2) Traceability (FR-M1 optionals, FR-M2 advocate #9,
exclude/include FR); 3) Quality; 4) Testing (lean + full + trigger + exclude transcripts);
5) Compliance (advocate never in voting set); 6) Operational (active_seats written to manifest);
7) Self-assessment.

## QA (Zero-Trust Verifier)

Verify: (a) run `resolve_roster.py` on a construction fixture and confirm #11 appears;
(b) run with `--exclude 3` and confirm active_seats omits #3 AND an uncovered-risk line is
logged; (c) enumerate the returned voting set in BOTH lean and full and confirm #9 ADVOCATE is
absent (recompute — do not trust the flag); (d) attempt to construct a scrutiny tally including
#9 and confirm the assertion blocks it. Reject if #9 can ever vote.

**Evidence gates:** correct optional promotion; exclude applied + uncovered-risk logged; #9
absent from voting set in both modes; assertion enforced; active_seats persisted to manifest.

## Dev Learnings
_(fill: trigger-condition edge cases; where the non-voting assertion had to live; exclude/include compose order.)_

## QA Learnings
_(fill: any path that leaked #9 into a count; any exclude that dropped a seat without logging the gap.)_
