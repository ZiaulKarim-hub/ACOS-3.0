# SLICE-D3-resume-durability — Resume from manifest + round-status (survives /clear + Eternity)

**Parent story:** STORY-D2 · **Epic:** EPIC-D · **Effort:** M · **Demo:** Demo 3
**slice.yaml mapping:** Objective->`objective`; Allowed files->`files_allowed`;
DoD+evidence gates->`acceptance_criteria`; QA verification->`verification_method`.

## PM (Planner / LCE brief)

**Objective (single, narrow):** Make a Mode B deliberation resumable — re-read `manifest.yaml`
+ `round-status.yaml` and re-enter at the last-closed round after `/clear`, crash, or Eternity
Protocol handoff, with the transcript-on-disk as the sole source of truth.

**In-scope:** `resume.py` — detect an existing session; read `manifest.status` +
`current_round` + `round-status.yaml`; reconstruct the last-K verbatim + rolling-synthesis
context from disk; re-enter the moderator loop at the correct round; never trust conversation
memory.

**Out-of-scope:** autopilot detection (F1); new deliberation logic (D1/D2).

**Allowed files/contexts:** `scripts/resume.py`; SKILL.md resume entry; READ-ONLY:
`manifest.yaml`, `round-status.yaml`, `transcript.md`, turn JSONs, domain-lattice
`pattern-transcript-on-disk`; CLAUDE.md Eternity/handoff notes.

**Step-by-step:**
1. On invocation with an existing `--session`/deal, load manifest + round-status.
2. If `status: paused_for_human` or an incomplete round, rebuild context from disk (last-K
   turns verbatim + rolling synthesis) and re-enter at `current_round`.
3. Continue the loop; verify no turn is duplicated or lost across the resume boundary.

**Definition of Done:**
- Artifacts: `scripts/resume.py`; SKILL.md resume entry; a resume-across-/clear fixture proof.
- Validation: kill a session mid-round, run resume, and confirm it re-enters at the last-closed
  round with the full prior transcript, zero duplicated/lost turns; conversation memory is
  never consulted (disk-only).
- Evidence bundle: a before/after transcript pair across a simulated /clear + a
  no-duplicate-turn proof.

## Dev (Executor)

**Execution notes:** disk is authoritative; if a resume ever reads state from conversation
memory it is a defect. Cross-check git/handoff state on resume (per Eternity stale-handoff
lesson). subscription-only.

**Evidence Bundle:** 1) Summary; 2) Traceability (FR-M10, NFR-4); 3) Quality (idempotent
re-entry); 4) Testing (kill+resume transcript, no dup/lost turns); 5) Compliance (disk-only,
never conversation memory); 6) Operational (Eternity/`/clear` survival); 7) Self-assessment.

## QA (Zero-Trust Verifier)

Verify: (a) kill a fixture session mid-round yourself, run `resume.py`, and confirm re-entry at
the last-closed round (recompute the expected round from `round-status.yaml`); (b) diff the
turn set before/after resume — zero duplicates, zero losses; (c) confirm the resume path reads
ONLY disk (grep for any reliance on prior conversation context); (d) confirm a stale-handoff
git-state cross-check is performed. Reject on wrong re-entry, dup/lost turns, or memory
reliance.

**Evidence gates:** correct re-entry round; no dup/lost turns; disk-only; git-state cross-check.

## Dev Learnings
_(fill: resume pointer reconstruction; Eternity handoff interplay.)_

## QA Learnings
_(fill: any turn duplication/loss; memory-reliance sniff test.)_
