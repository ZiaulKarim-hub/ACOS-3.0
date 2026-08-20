timestamp: "2026-08-11T23:58:00Z"
status: "active"
type: "emergency-manual"
trigger: "acos-eternity-protocol (737,881 tokens vs 500,000 threshold)"
session_id: "d72f5b72-b88e-4c3c-be62-9fa7e54f0fbf"
estimated_tokens: 737881

authorship_note: |
  WRITTEN BY THE ORCHESTRATOR, NOT THE HANDOFF AGENT. The handoff-agent wrote a
  657-byte STUB and was cut off — the same stream-watchdog stall that killed six
  working agents in the same minute. The stub's own text said "enrichment in
  progress; if this text survives, the handoff agent was cut off". The eternity
  Step-1 freshness guard checks mtime ONLY, not content, so it would have passed
  a stub straight through to /clear. Caught and replaced by hand.

repo_scope:
  THE WORK IS NOT IN THIS REPO: "/Users/zee/Documents/Vibe Coding/R2P"
  r2p_is_local_only: "NEVER push. No remote. This is a standing, absolute rule."
  acos_3_0_role: "Only the shell this session runs in. Its ~98 dirty files are unrelated framework churn and are NOT this session's work."
  re_derive_from: "R2P's own `git log` and `git status`. Never ACOS 3.0's."

session_summary: |
  EPIC-001 of R2P: 24 DEV/QA pairs, each built by one agent and reviewed by a
  second that never sees the builder's reasoning, then measured once against a
  sealed holdout pack written before any code existed.

  This session took the epic from 15 sealed pairs to 15 sealed + 9 in active
  motion, landing 19 commits. Every one of the 24 builds now exists. Seven
  independent reviews ran. Two holdout packs were spent (9/9 and 7/9).

  The reviews found faults in five modules whose own test suites were all green.
  NOT ONE was a wrong calculation. Every single one was the same class: an input
  is missing, unreadable or out of range, and the code SILENTLY SUBSTITUTES a
  plausible-looking stand-in instead of refusing. Seven dead `?? RATIONAL_ZERO`
  defaults that would each have published a zero; two unreadable ids collapsing
  to "" and comparing equal; dropped residual explanations; merged duplicate
  position rows; an overflow returning 0; a negative age defaulting to same_day;
  non-object entries discarded beneath a positive completeness claim.

  A second theme emerged late: the CHECK is often the weak part, not the code.
  A guard structurally unreachable; a check set presented as enumerated and
  complete that was missing an eleventh member; a verifier covering 9 of 15
  fields; an audit that recomputes part of its answer but re-reads a stored field.

six_agents_died_simultaneously:
  cause: "Harness-level: 'Agent stalled: no progress for 600s (stream watchdog did not recover)'. NOT an agent fault. All six within the same minute."
  state: "PARTIAL WORK IS ON DISK AND UNCOMMITTED (~35 files in R2P's working tree). All are resumable by a fresh agent given the same brief."
  agents:
    - id: "QA-001-006-03 pass 1 (reviewer, pair 18)"
      last_reported: "Finishing the record now — findings, sweep verdicts, traps survived, attestation."
      banked: "Proved its category-(d) guard FIRES against its own out-of-repo mutant with the exact reported detail. Deep freeze holds at 16/16 exit 0."
      open_leads: "Publisher.publish returns 0 on overflow — fail-open unless EVERY caller checks failures(); one that does not is HIGH. classifyAgeBand defaults to same_day for any negative age."
    - id: "DEV-001-006-02 revision 2 (builder, pair 17, answering a BLOCK)"
      last_reported: "Now the property-test instrument: generator split, P1/P6 rework, P3 exactness, and the new P10 family."
    - id: "DEV-001-007-03 revision 2 (builder, pair 21, answering a BLOCK)"
      last_reported: "Instrument 1 is calibrated: it reproduces both QA shapes and found a third non-footing site. Now instrument 2 — the guard mutation census."
      NEW_INFORMATION_DO_NOT_LOSE: "It found a THIRD non-footing site beyond the two the reviewer named."
    - id: "QA-001-007-02 pass 2 (re-reviewer, pair 20)"
      last_reported: "The guard fired on command complexity. Let me split into simple steps."
    - id: "QA-001-008-03 pass 1 (reviewer, pair 24)"
      last_reported: "Now the gate-scope evidence — let me verify the two excerpts verbatim."
      banked: "verifyExportMatchesDisplay checks only 9 of the 15 meta keys it emits. Six are never compared."
    - id: "Holdout custodian HLD-001-008-02-v1 (pair 23)"
      last_reported: "Pre-execution correction: one unused import. Removing it cannot change any graded outcome."
      CRITICAL: |
        IT HAD NOT YET SPENT ITS ONE-SHOT RUN. The pack should still read
        revealed_at: null. VERIFY THIS FIRST. A fresh custodian must re-run the
        EIGHT pack-hash checks (4 pre + 4 post) itself and spend the run itself.
        Assume-it-ran costs the pair its only unbiased measurement; assume-it-did-not
        when it did spends the cases twice. Check, do not guess.

epic_001_position:
  verify_every_line_against_disk: true
  sealed: "15 pairs — 001-001-01 through 001-005-03."
  pair_16_006_01: "QA pass 4 PASS (blocking_findings []). Holdout run 1 SPENT, 9/9, 59/59 graded assertions, 8/8 pack digests. Three findings from ungraded probes, none score-affecting. NEXT: mutation gate, then seal."
  pair_17_006_02: "QA pass 1 BLOCK on QA-F4 (duplicate instrumentId accepted; account holds 12, sleeves 7, reconciliation ACCEPTED) and QA-D1 (a defect ALL NINE property families and all 89 unit cases miss). Revision 2 in flight when it died."
  pair_18_006_03: "Built. QA pass 1 in flight when it died."
  pair_19_007_01: "QA pass 3 PASS. Pre-registered refutation of the builder's strict-superset argument HELD. NEXT: holdout."
  pair_20_007_02: "QA pass 1 BLOCK (narrow) on F-01/F-06/F-03. Revision 2 COMMITTED — it DEMONSTRATED the CAR-path underflow the reviewer could only call structurally exposed, by deriving the boundary m > 200*(1-h11) and measuring both sides. QA pass 2 in flight when it died."
  pair_21_007_03: "Built and COMMITTED. QA pass 1 BLOCK (narrow) on QA-F-01 (published column does not foot: 666666666 vs 666666667) and QA-F-02 (a named (b) guard that never fires). Revision 2 in flight when it died."
  pair_22_008_01: "Holdout run 1 SPENT 7/9. Revision 3 COMMITTED. QA pass 3 was dispatched but NEVER RAN — re-dispatch it."
  pair_23_008_02: "QA pass 1 PASS with six findings, two medium. Holdout custodian died BEFORE spending the run."
  pair_24_008_03: "Built and COMMITTED. QA pass 1 in flight when it died."

orchestrator_obligations_all_open:
  - "#14 whole-project regression — owed to three agents that named it undemonstrated because siblings were live."
  - "#15 land three deferred barrel exports. BLOCKED by OBS-09: the two performance-package siblings collide on THREE exported names (Availability, DeclaredPolicyRecord, IRRATIONAL_DERIVATION), verified by compiling to TS2308. Renaming is a public-contract change — Ben's call."
  - "#16 assemble the EPIC-001 ratification packet. tools/close-packet.ts is COMMITTED and its --control mode PASSES on all five sealed story bundles."
  - "#17 mutation gate. MUST run only when NO agents are live: stryker.config.mjs sets inPlace: true and rewrites source files. The PRD §16.7 70% bar for this epic is UNESTABLISHED — two agents said so explicitly, and one added that catching six hand-chosen defects is not a mutation score."

standing_rules_carry_forward_verbatim:
  - "R2P is LOCAL-ONLY. NEVER push."
  - "AP-06: never weaken a test, an invariant or a tolerance."
  - "AP-07: no agent approves, seals, closes or ratifies anything. Every finding stays pending_human_review, owner Ben. Never treat silence as approval."
  - "TypeScript only, ZERO python3 in R2P. An accidental invocation is 'one accidental, disclosed', never claimed as zero."
  - "qa-private/ is custodian-only. Builders, reviewers and the orchestrator must never open it, the holdout harness, or any run log."
  - "Reviewers run in isolated worktrees — they MUST write to the MAIN checkout at /Users/zee/Documents/Vibe Coding/R2P by ABSOLUTE path, or the work never reaches the repo."
  - "Every reviewer's blind-derivation file needs artifact_type or validate-planning-yaml fails. This tripped four reviewers today."
  - "Whole-project tsc is CLEAN at zero errors. An earlier orchestrator claim of ~50 errors is STALE and was caught by an agent."
  - "macOS: no timeout/gtimeout. zsh aborts on unmatched globs — use find. vitest -t is a REGEX and matching nothing exits 0."
  - "Agents stop at narration boundaries. Check DISK first, then resume with an exact numbered remainder checklist. Never re-dispatch."

three_orchestrator_errors_caught_by_agents:
  - "22 type errors in tools/close-packet.ts, committed after verifying only that it RAN. tsx strips types without checking them. Found by DEV-001-006-03's builder, which correctly refused to touch the file. Fixed; now zero."
  - "A false premise about a broken file at the wrong pair's path. QA-001-008-02's reviewer measured, found no such file, and reported the premise false rather than acting on it."
  - "A merged restatement of two separate results. QA-001-006-02's reviewer refused it outright and pointed at the exact lines of its own record."

next_actions:
  - "Re-derive position from R2P's git log and git status. Do not trust the numbers above without checking."
  - "FIRST: verify whether HLD-001-008-02-v1 was revealed. If revealed_at is null, re-dispatch a fresh custodian with the full eight-check gate."
  - "Re-dispatch the six dead agents with their original briefs plus an exact numbered remainder built from their banked work above."
  - "Re-dispatch QA-001-008-01 pass 3, which was dispatched but never ran."
  - "Commit the ~35 uncommitted files ONLY as each agent reports — one commit per pair, never a bulk save."

blockers: "None technical. Seven-plus items await Ben's ruling; all twelve ADRs remain status: proposed."
