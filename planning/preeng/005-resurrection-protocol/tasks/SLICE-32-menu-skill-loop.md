# SLICE-32-menu-skill-loop — acos-resurrect/SKILL.md menu + finish verb + loop mechanics
**Epic EPIC-3 / Story STORY-3.1 — Demo: Demo 3 (the loop)**
_Vertical value:_ The loop, with inverted economics: resume flips parked->active; finish sets completed; /acos-complete untouched.

## PM (Planner / Specifier) — Lean Context Engineering
**Single objective:** acos-resurrect/SKILL.md menu + finish verb + loop mechanics

**In scope:**
- The menu (terminal-first per DP1) over resurrect-view.py + launch-project.sh
- Finish verb -> status: completed (hidden in ARCHIVED, never deleted)
- Loop: resume flips parked->active; last_verified_at refreshes on render contact
- /acos-complete left untouched

**Out of scope (guardrails):**
- Any nagger/notifier
- Deleting a finished row
- Auto-close at a token threshold

**Allowed files / contexts:** .claude/skills/acos-resurrect/SKILL.md (surface per DP1, terminal-first). Status transitions via registry_lib.

**Definition of Done:** all acceptance criteria below pass; required artifacts written under the repo path; the evidence bundle at `.acos/evidence/[DATE]/SLICE-32-menu-skill-loop/` is populated; `## Dev Learnings` and `## QA Learnings` are updated (a slice is not Done until they are — §0.7).

## Dev (Executor) — steps + 7-part Evidence Bundle
**Steps (execute EXACTLY; no scope expansion, only allowed files):**
- Author the SKILL.md menu router over the two scripts.
- Implement the finish verb and status transitions.
- Verify the loop transitions in the row file and audit log.

**Evidence Bundle to produce:** 1) Implementation Summary; 2) Requirements Traceability (to spec FR-* / tech_prd TR-*); 3) Structural Quality Evidence; 4) Functional/structural checks (the verification method below); 5) Security/Compliance notes; 6) Operational/Runtime considerations; 7) Self-assessment (confidence + known limitations).

## QA (Zero-Trust Verifier)
Assume the Dev did **not** do the work correctly. Verify scope respect, evidence authenticity (no fabricated logs — spot-check and recompute), and that every acceptance criterion + evidence gate is satisfied. QA may **REJECT** and require rework until the gates pass (a reject blocks the slice like an INCONCLUSIVE reviewer).

**QA checks:**
- Confirm a finished row is hidden, not deleted
- Confirm no nagger exists
- Confirm /acos-complete was not modified

## Definition of Done (maps to ACOS `slice.yaml`)
**acceptance_criteria:**
- Resume flips parked->active; finish sets completed (row hidden in ARCHIVED, never deleted)
- Status transitions visible in the row file and the audit log
- /acos-complete is unchanged

**verification_method:** Row-file + audit-log deltas archived for each transition; /acos-complete shown untouched (diff).

**evidence bundle:** `.acos/evidence/[DATE]/SLICE-32-menu-skill-loop/`

## Dev Learnings

**2026-07-18 (SLICE build):**
- What worked: testing the skill's transition blocks EXACTLY as written by extracting
  the python bodies from the SKILL.md fences programmatically and executing those
  files — zero drift between what the skill says and what was verified. Reuse this
  extract-and-run pattern for every future skill that embeds runnable blocks.
- What worked: passing `RES_UUID`/`RES_DIR` as environment variables into the
  python heredocs instead of shell interpolation — the repo path contains a space
  ("ACOS 3.0") and env-var passing makes the blocks quoting-proof. All blocks honor
  `ACOS_REGISTRY_HOME`, so QA can re-run them in a sandbox forever.
- What surprised: the harness surfaced `acos-resurrect` in the live skill listing
  seconds after the file write — "appears in a fresh skill listing" was directly
  observable mid-session, no restart needed.
- Design reconciliation to reuse: the yaml phrase "last_verified_at refreshes on
  render contact" collides with SLICE-30's read-only-book hard rule; it was mapped
  to refresh-on-RESUME-contact (every registry_lib upsert during launch or the
  same-root flip refreshes it; the render mutates nothing). Documented in the skill
  and the evidence bundle §1 for explicit QA sign-off.
- Audit vocabulary: upsert_row appends its own `upsert` event, so the verbs add the
  FR-S1 semantic events (`resume`, `finish`) as a second explicit line; `tombstone`
  needs no extra line (tombstone_row appends its own). Idempotence falls out free:
  the blocks skip upsert+audit entirely when the status already matches (0 audit
  lines on a repeated finish).

## QA Learnings

**2026-07-18 (build-time self-QA; zero-trust reviewer still to run):**
- What nearly slipped through: an early draft had the finish one-liner as a
  `python3 -c` shell string — the space in "ACOS 3.0" plus nested quotes made it
  fragile; the switch to env-var heredocs was caught by dry-running the block
  against the sandbox before committing the skill text. Harden: any embedded
  command in a skill must be executed at least once from the file itself.
- Which check caught what: the refusal test (T5) proved the resume block cannot
  resurrect a tombstoned row (AssertionError, exit 1) — guarding the launcher's
  refusal is not enough because same-root picks bypass the launcher.
- Verified hidden-not-deleted with BOTH halves: sandbox book shows completed +
  tombstoned rows ONLY under ARCHIVED (`listed 3 of 3`, nothing dropped) AND the
  row files remain on disk. `/acos-complete` diff is 0 bytes; nagger grep hits only
  the skill's own prohibition lines (44-48). Real registry proven read-only by
  row-file mtime comparison across the launcher dry-run.
- Harden next: the AskUserQuestion (<=4 projects) branch and curation walk are
  prose-verified only — first interactive use should confirm option descriptions
  really carry next_action verbatim and that curation tombstones only on per-row
  answers.
