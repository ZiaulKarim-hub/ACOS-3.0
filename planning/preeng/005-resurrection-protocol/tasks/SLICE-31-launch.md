# SLICE-31-launch — launch-project.sh: focus-or-launch + SPINE 1 acceptance + verified argv delivery
**Epic EPIC-3 / Story STORY-3.1 — Demo: Demo 3 (focus-never-launch)**
_Vertical value:_ Focus-never-launch kills the duplicate pile-up at its source (worth more than every other feature in the window).

## PM (Planner / Specifier) — Lean Context Engineering
**Single objective:** launch-project.sh: focus-or-launch + SPINE 1 acceptance + verified argv delivery

**In scope:**
- (a) same-root -> newest .reentry.md re-resolved AT OPEN TIME, loaded inline
- (b) open elsewhere -> cmux rpc workspace.select focus, NEVER a second workspace
- (c) not open -> new-workspace with argv reentry delivery, read-screen delivery verification + one retry, trust-gate detection ('Quick safety check'), [ -d "$CWD" ] precheck
- Write --name/--description from the registry (<next_action> [key:<uuid>]) via list-form subprocess

**Out of scope (guardrails):**
- cmux send / surface.send_text for the prompt (shred at \n)
- Any registry-derived string entering --command (only the reentry file PATH)
- Recency as a selector (exact identity match first)

**Allowed files / contexts:** .claude/scripts/resurrection/launch-project.sh; cmux rpc workspace.select / new-workspace / read-screen (absolute binary).

**Definition of Done:** all acceptance criteria below pass; required artifacts written under the repo path; the evidence bundle at `.acos/evidence/[DATE]/SLICE-31-launch/` is populated; `## Dev Learnings` and `## QA Learnings` are updated (a slice is not Done until they are — §0.7).

## Dev (Executor) — steps + 7-part Evidence Bundle
**Steps (execute EXACTLY; no scope expansion, only allowed files):**
- Implement the three-way routing.
- Implement argv delivery + read-screen marker verification + one retry + trust-gate detection.
- Run the SPINE 1 acceptance test.

**Evidence Bundle to produce:** 1) Implementation Summary; 2) Requirements Traceability (to spec FR-* / tech_prd TR-*); 3) Structural Quality Evidence; 4) Functional/structural checks (the verification method below); 5) Security/Compliance notes; 6) Operational/Runtime considerations; 7) Self-assessment (confidence + known limitations).

## QA (Zero-Trust Verifier)
Assume the Dev did **not** do the work correctly. Verify scope respect, evidence authenticity (no fabricated logs — spot-check and recompute), and that every acceptance criterion + evidence gate is satisfied. QA may **REJECT** and require rework until the gates pass (a reject blocks the slice like an INCONCLUSIVE reviewer).

**QA checks:**
- Independently confirm the workspace count is constant on an open pick (cmux does no dedup - a bug here creates a 5th ACOS 3.0 workspace)
- Confirm delivery is verified via read-screen + retry, not assumed
- Confirm the reentry PATH, not its contents, is what enters --command

## Definition of Done (maps to ACOS `slice.yaml`)
**acceptance_criteria:**
- Picking ACOS 3.0 while open changes focus and the workspace count stays CONSTANT (SPINE 1)
- Launch on a throwaway delivers the multi-line reentry as ONE message (read-screen marker found)
- Untrusted-dir launch is detected and reported, not silently assumed delivered
- No registry-derived string enters --command; names/next_action go via --name/--description list-form

**verification_method:** Workspace count before/after an open pick archived; read-screen marker shown for a throwaway launch; trust-gate detection shown; --command inspected.

**evidence bundle:** `.acos/evidence/[DATE]/SLICE-31-launch/`

## Dev Learnings
_2026-07-18 (build session, cmux 0.64.19):_
- **Quote-split the marker in the echoed command.** `echo 'RESURRECTION-DELIVERY-''BEGIN-<nonce>'` means the contiguous marker string exists ONLY in output, never in the typed command line that read-screen also captures — this killed the marker-matches-its-own-command false positive before it happened. Reuse this for any screen-grep verification.
- **`workspace <sub>` is the canonical noun on 0.64.19** ("Legacy verbs (new-workspace, ...) keep working and print a one-time deprecation hint"). Used `workspace create/select/close` list-form throughout; behavior identical to the legacy verbs the design doc quotes.
- **End the default --command with `exec /bin/zsh -i`.** A command that exits can leave the surface dead before the 2s-delayed read-screen; keeping a shell alive makes verification deterministic and close-workspace still kills it silently.
- **Join back to the created workspace by the `[key:<uuid>]` description tag, not by parsing create's stdout** — durable, and the same join the book uses. workspace.list can lag creation ~1s; retry up to 5x1s.
- **`read-screen --scrollback` is mandatory for delivery verification** — a 15-line reentry already pushes BEGIN toward the top; a 40-line one scrolls it off the visible screen entirely.
- Creation genuinely does NOT steal focus (selected workspace unchanged across `workspace create`) — no restore needed on the create path, only after a select test.
- Surprise: `rpc workspace.list` payload is per-window (single `window_id` at top level). Fine today (one window), but a multi-window setup could hide a match and break SPINE 1 — flagged in the evidence bundle for DR-1/SLICE-30.

## QA Learnings
_2026-07-18 (zero-trust pass on own build):_
- **The decoy-reentry test caught the class that matters:** an older 2026-07-01 `.reentry.md` planted next to the newest one — the mtime scan reported "newest of 2 candidates" and picked 2026-07-18. Without the decoy, a `sorted()[0]`-style bug would have passed silently. Always plant a stale sibling when testing "newest wins".
- **Count-constant must be read independently before AND after** via `rpc workspace.list`, not trusted from the script's own print — archived 5→5 on the focus pick; the script's stdout agreed but was not the source of truth.
- **The NOT-VERIFIED path was proven by construction** (override printing the trust-gate text): rc=3, two read-screen attempts logged, trust gate reported, and the row still activated (the workspace exists) — verified that loud-fail and mutate-on-launch are correctly independent.
- Nearly slipped through: the "only the reentry PATH was substituted" message printed even for overrides with no `{REENTRY}` placeholder — a misleading claim in the receipt. Caught reading the T6 transcript; fixed to state "used verbatim (no {REENTRY} placeholder)". Receipts must never claim substitutions that did not happen.
- Hardening left open (honest): registry-fallback reentry branch and 2+-duplicate ordering are structural-only; multi-window enumeration untested. Listed in the bundle §7, not hidden.
