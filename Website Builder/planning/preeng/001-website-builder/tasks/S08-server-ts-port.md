# S08-server-ts-port — Port the in-estate Python server to `server.ts` (the TypeScript spine)

| Field | Value |
|---|---|
| Epic / Story | E1 / ST-02 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 1 / — |
| Depends on | S01-gate-16a-and-launcher-rung |
| Requirements | FR-012, FR-227 |
| Acceptance criteria | A84 · A80 · SL-S08-1 |
| CQ / evidence | CQ6 |
| Note | **This is the first product code written** — it exists to establish the TypeScript spine against Python-gravity (R12) |

## PM — slice definition

**Objective.** Port the 105-line in-estate Python server contract to `server.ts` on Bun, serving the route contract on the fixed loopback port with a complete `state.json` at boot.

**In scope.** `scripts/server.ts` (Bun.serve); the route skeleton `GET /health`, `GET /doc`, `POST /ops`, `GET /events`, `POST /variants`, `POST /lock`, `POST /internal/*`, static; fixed port 8820 on `127.0.0.1`; `state.json` written at boot; regenerate-if-stale on startup; launch through the rung that passed in S01.

**Out of scope.** Op validation and the document model (S24, S31). The security controls (S37) — this slice binds loopback only and leaves the other seven controls to S37, and must say so in its own README note. Any editor UI.

**Allowed files / contexts.**
- `scripts/server.ts`, `scripts/lib/routes.ts`, `scripts/package.json`, the S01 launcher.
- **No `.py` file may be created anywhere in the skill tree.**

**Steps.**
1. Create `scripts/package.json` with `type: module`; shebang `#!/usr/bin/env bun`; no build step.
2. Implement the route skeleton with typed handlers returning structured responses; every handler is a stub that returns a documented status until its owning slice lands.
3. Bind `127.0.0.1:8820` explicitly; never a random port; write `{phase, step, awaiting, nextAction, port, pid, url, sessionId}` to `state.json` at boot.
4. Implement regenerate-if-stale: on startup, if `state.json` names a dead pid, rewrite it rather than refusing to start.
5. Launch via the S01 rung; confirm bind with retrying curl; **prove survival with a second curl in a separate tool call**.
6. Assert `find scripts app -name '*.py' | wc -l` is 0.

**Definition of Done.**
- Artifacts: `server.ts`, `routes.ts`, `package.json`, the boot `state.json` sample, the survival transcript.
- Validation: the eight-field `state.json`; the zero-Python assertion; a post-boundary 200.
- `slice.yaml` mapping — `acceptance_criteria: [A84, A80, SL-S08-1]`, `verification_method: exit-code` (A80: `probe`).

## Dev — execution contract

Every stub route must return a documented status rather than throwing. Evidence bundle: (1) summary; (2) traceability FR-012, FR-227 → file:line per route; (3) structural quality — decision logic is in `lib/` so it is unit-testable without a browser; (4) functional testing — a curl transcript per route plus the post-boundary check; (5) security/compliance — state explicitly which controls are **not** yet implemented and that S37 owns them; (6) operational — how to stop the server cleanly, and the idle-shutdown hook point; (7) self-assessment.

## QA — zero-trust verification

- **Curl every route yourself** and record status codes; a route table in prose is not evidence.
- **Read `state.json`** and require all eight fields; four fields is a rejection (the carried shape is a subset).
- **Run your own** `find` for `.py` files under the skill tree.
- **Re-prove survival** in your own separate tool call — a same-turn 200 is not proof of life.
- **Reject** if any route throws on a normal failure path.

## Dev Learnings

_Not Done until filled. Required: what the Python original did implicitly that the port had to make explicit._

## QA Learnings

_Not Done until filled. Required: which route stub was easiest to mistake for implemented._
