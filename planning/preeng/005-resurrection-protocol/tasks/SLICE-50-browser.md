# SLICE-50-browser — (DP1-conditional) resurrection-server.py: the 8820 browser window
**Epic EPIC-5 / Story STORY-5.1 — Demo: Optional (only if DP1 selects it)**
_Vertical value:_ An always-glanceable dashboard that does not occupy a Claude session (adopted only if the menu earns it).

## PM (Planner / Specifier) — Lean Context Engineering
**Single objective:** (DP1-conditional) resurrection-server.py: the 8820 browser window

**In scope:**
- stdlib ThreadingHTTPServer at 127.0.0.1:8820 FIXED; skill-started, never launchd; NO idle reaper (comment in code)
- Singleton via GET /api/whoami on EADDRINUSE, never port-hop; POST /api/launch opaque-ID only
- Validate Origin+Host+Content-Type; no ACAO:*; textContent never innerHTML; open -a 'Google Chrome'; 5s visible-only polling

**Out of scope (guardrails):**
- launchd hosting
- idle reaper / port-hopping
- ACAO:* / innerHTML
- Accepting a path (not an ID) at /api/launch

**Allowed files / contexts:** .claude/scripts/resurrection/resurrection-server.py; the same engine (resurrect-view.py, launch-project.sh).

**Definition of Done:** all acceptance criteria below pass; required artifacts written under the repo path; the evidence bundle at `.acos/evidence/[DATE]/SLICE-50-browser/` is populated; `## Dev Learnings` and `## QA Learnings` are updated (a slice is not Done until they are — §0.7).

## Dev (Executor) — steps + 7-part Evidence Bundle
**Steps (execute EXACTLY; no scope expansion, only allowed files):**
- Implement the loopback server + singleton + opaque-ID launch.
- Implement header validation and textContent rendering.
- Run the security tests.

**Evidence Bundle to produce:** 1) Implementation Summary; 2) Requirements Traceability (to spec FR-* / tech_prd TR-*); 3) Structural Quality Evidence; 4) Functional/structural checks (the verification method below); 5) Security/Compliance notes; 6) Operational/Runtime considerations; 7) Self-assessment (confidence + known limitations).

## QA (Zero-Trust Verifier)
Assume the Dev did **not** do the work correctly. Verify scope respect, evidence authenticity (no fabricated logs — spot-check and recompute), and that every acceptance criterion + evidence gate is satisfied. QA may **REJECT** and require rework until the gates pass (a reject blocks the slice like an INCONCLUSIVE reviewer).

**QA checks:**
- Confirm no idle reaper and no launchd hosting
- Confirm no ACAO:* and no innerHTML anywhere
- Confirm /api/launch rejects a path and only accepts an opaque ID

## Definition of Done (maps to ACOS `slice.yaml`)
**acceptance_criteria:**
- EADDRINUSE reuse works (singleton via /api/whoami), never port-hops
- A hostile project name renders inert (textContent)
- Cross-origin POST rejected; /api/launch with a path instead of an ID -> 400

**verification_method:** Singleton reuse shown; hostile-name render inspected; cross-origin + path-not-ID rejections archived.

**evidence bundle:** `.acos/evidence/[DATE]/SLICE-50-browser/`

## Dev Learnings
_(fill at execution — the slice is NOT Done until this is updated: what worked, what surprised, what to reuse.)_

## QA Learnings
_(fill at execution — the slice is NOT Done until this is updated: what nearly slipped through, which check caught it, what to harden.)_
