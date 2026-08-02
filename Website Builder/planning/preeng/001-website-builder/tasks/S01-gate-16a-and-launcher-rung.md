# S01-gate-16a-and-launcher-rung — Gate 16-A turn-boundary probe and launcher-rung decision

| Field | Value |
|---|---|
| Epic / Story | E0 — Phase-0 spikes and blocking gates / ST-01 |
| Type · MoSCoW · Size | diagnostic · MUST · S `[I — ordinal size class, explicitly non-temporal]` |
| Phase / Demo | Phase 0 / — |
| Depends on | none — **this is the first slice of the plan** |
| Requirements | FR-001, FR-002 |
| Acceptance criteria | A80 · SL-S01-1 · SL-S01-2 |
| CQ / evidence | CQ6 (confidence 0.45 — one of the three weakest answers in the domain) |
| Blocking | **YES.** Nothing server-dependent may be treated as committed until this passes |

## PM — slice definition (Lean Context Engineering)

**Objective.** Determine, with recorded evidence, whether a long-running local server survives this harness's turn boundary, and at which rung of the F1→F5 ladder.

**In scope.** A throwaway probe server bound to `127.0.0.1:8820`; the launcher rung ladder F1 (TS detached spawn + `unref`) → F2 (TS double-fork; **`setsid` does not exist on this Mac**) → F3 (~15-line POSIX `sh` launcher); writing `state.json` with the pid; the multi-turn curl protocol; ADR-01.

**Out of scope.** The real `server.ts` route contract (S08). Any editor code. Any product feature. Rungs F4 (Python shim) and F5 (manual terminal) **may not be implemented in this slice** — reaching them halts the slice pending the user's signature.

**Allowed files / contexts.**
- `scripts/probes/probe-turn-boundary.ts` (new)
- `scripts/probes/launch-f1.ts`, `launch-f2.ts`, `launch-f3.sh` (new)
- `docs/adr/ADR-01-launcher-rung.md` (new)
- Read-only: `references/gotchas.md` if it exists.
- **Nothing under `src/`, `app/`, `.claude/agents/`, or any product path.**

**Steps.**
1. Implement the probe server: bind `127.0.0.1:8820` explicitly, expose `GET /health`, write `{phase, step, awaiting, nextAction, port, pid, url, sessionId}` to `state.json` at boot.
2. Launch at rung F1. Confirm bind with `curl --retry 20 --retry-connrefused` for HTTP 200 **in the same turn**.
3. **End the turn.**
4. In a **separate later tool call**, curl `/health` again and confirm the pid recorded in `state.json` is still present in `ps`.
5. Repeat step 3–4 across at least **two further** turn boundaries, and once across an eternity `/clear`.
6. On any failure, drop to the next rung and restart from step 2. Record every attempt, including failures.
7. Write ADR-01 naming the passing rung, the exact launch invocation, and the evidence paths.

**Definition of Done.**
- Artifacts: the probe script, the launcher for the passing rung, ADR-01, and a raw evidence log of every curl (command, exit code, HTTP status, timestamp, pid check).
- Validation: at least three post-boundary checks plus one post-`/clear` check, all 200, original pid alive at each.
- Evidence bundle: all seven Dev sections, with the raw curl transcript attached, not summarised.
- `slice.yaml` mapping — `acceptance_criteria: [A80, SL-S01-1, SL-S01-2]`, `verification_method: probe`.

## Dev — execution contract

Execute exactly this slice; do not expand scope; touch only the allowed files. **Never use `timeout`/`gtimeout`** — no such binary exists here and it yields *empty output*, not an error; guard long runs with background execution plus polling. Use absolute paths in every command (cwd resets between calls).

Evidence bundle, seven sections: (1) implementation summary naming the rung reached; (2) requirements traceability FR-001, FR-002 → file:line; (3) structural quality — the probe has no product dependencies; (4) functional testing — the full multi-turn transcript; (5) security/compliance — bound to loopback only, no external listener; (6) operational — how to re-run, and what to do if the rung regresses; (7) self-assessment — confidence, and explicitly whether the pass was observed across a `/clear` or only across ordinary turn boundaries.

## QA — zero-trust verification

Assume Dev did not do the work. **Do not trust any logged status line.**
- **Re-run** the post-boundary curl yourself in a separate tool call and record your own exit code.
- **Recompute** the pid check: read `state.json`, then `ps -p <pid>`; a "still running" claim without your own `ps` output is a rejection.
- **Reject** if any post-boundary check was performed in the same turn as the launch (a same-turn 200 is never proof of life).
- **Reject** if F4 or F5 was implemented without a recorded user signature.
- **Reject** if only one boundary was crossed, or if the `/clear` crossing is missing.
- **Reject** if ADR-01 does not name the exact launch invocation that passed.
- Verdict `inconclusive` (e.g. the probe could not be launched at all) **blocks exactly like a fail**.

## Dev Learnings

_Not Done until filled. Required: which rung passed, what failed at each earlier rung, and the exact failure signature (exit 143 vs missing pid vs connection refused). This is a first-party harness fact worth more than any documentation — it must also land in `references/gotchas.md` (S75) and in the estate's memory._

## QA Learnings

_Not Done until filled. Required: what the verification would have missed had it trusted the Dev log, and whether the multi-turn protocol needs tightening for future probes._
