# S37-eight-control-security-posture — The eight-control local-server security posture

| Field | Value |
|---|---|
| Epic / Story | E16 / ST-12 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 2 / — |
| Depends on | S08-server-ts-port · S29-editor-shell-and-overlay |
| Requirements | FR-220, FR-229 |
| Acceptance criteria | A76 · A77 · §12.17-A100 · SL-S37-1 · SL-S37-2 · SL-S37-3 |
| CQ / evidence | CQ8 |
| Note | **NA-B02** — the carried requirement states a **six**-control posture. The source specifies **eight**: exact-origin CORS, `Host`-header validation and the security-header/CSP row are additional, and **`Host` validation — not the bearer token — is the anti-DNS-rebinding control** |

## PM — slice definition

**Objective.** Treat localhost as a hostile boundary: bind, origin, exact CORS, bearer token, pinned host settings, idle shutdown, `Host` validation and security headers.

**In scope.** All eight controls on `server.ts`: (1) explicit `127.0.0.1` bind, never `0.0.0.0`; (2) `Origin` validation on **every non-GET and on the SSE upgrade** against a two-entry allowlist; (3) `Access-Control-Allow-Origin` = the exact editor origin, **never `*`**; (4) a per-session bearer token — 32 random bytes at `.wb/editor.token` mode `0600`, injected into the editor page at render, sent as `Authorization` on every non-navigation request; (5) the substrate's allowed-hosts setting pinned to the explicit host and the substrate version pinned above the fixed advisory; (6) heartbeat plus idle shutdown, recorded in the event log; (7) **`Host` validation on EVERY request including the bootstrap `GET /`** — reject unless `Host` is exactly `127.0.0.1:8820` or `localhost:8820`, **before a response body exists to be read**; (8) `Cross-Origin-Resource-Policy: same-origin`, `X-Content-Type-Options: nosniff`, `Cache-Control: no-store` on the bootstrap, a strict CSP on the editor page, and **never reflect a request header into a response**. Plus: any hook this skill registers is cheap, **fail-open**, registered dynamically and removed at close.

**Out of scope.** Hash-journal reconciliation, 409 concurrency, the lock and the tab claim (S38). The ownership guard, `wb op` and the inbox (S39). The importer's AST validation (S19) — a different, unauthenticated channel with its own posture.

**Allowed files / contexts.**
- `scripts/lib/security.ts`, `scripts/lib/token.ts`, `scripts/lib/hooks.ts`, the `server.ts` middleware wiring from S08, the substrate config file.
- Runtime-only: `.wb/editor.token`.
- **No `.py` file may be created anywhere in the skill tree.**

**Steps.**
1. Implement each control as a named, individually testable middleware; the request pipeline names them in order so a missing control is visible by reading the chain.
2. Order `Host` validation **first**, ahead of routing and ahead of any body production.
3. Generate the token with a CSPRNG; write at `0600`; inject at render only; never log it, never echo it in an error.
4. Wire the idle timer to the editor heartbeat; on fire, append a shutdown record to the event log and exit cleanly.
5. Register hooks dynamically at open and remove them at close; wrap each in a fail-open guard so a hook error still allows the tool call.
6. Record in the README which control defeats which class, including why control 7 and not control 4 answers DNS rebinding.

**Assumption (recorded).** The idle window is stated in the source only as "N minutes"; this slice reads it from the project config and records the value used rather than inventing a constant `[I]`.

**Definition of Done.**
- Artifacts: `security.ts` with eight named middlewares, `token.ts`, the hook register/remove pair, the control→threat README table, a transcript per control.
- Validation: foreign-`Host` GET rejected and loopback-`Host` GET accepted; non-allowlisted `Origin` POST rejected; SSE upgrade rejected without a valid origin and token; `stat` shows `0600`; idle shutdown observed in the event log; a forced hook error still allows the tool call.
- `slice.yaml` mapping — `acceptance_criteria: [A76, A77, "§12.17-A100", SL-S37-1, SL-S37-2, SL-S37-3]`, `verification_method: exit-code` (SL-S37-1: `grep-assert`).

## Dev — execution contract

Evidence bundle: (1) summary naming all eight controls; (2) traceability FR-220, FR-229 → file:line per control; (3) structural quality — one middleware per control, no control implemented twice; (4) functional testing — a curl transcript per control including the negative case; (5) security/compliance — state which classes remain **out** of the model (a local user with the same uid, and the importer channel), and that the in-estate reference server binds loopback but performs no `Origin` check on POST and no `Host` check anywhere, so it must not be copied; (6) operational — how to rotate the token and how idle shutdown interacts with `--resume`; (7) self-assessment.

## QA — zero-trust verification

- **Send your own** `GET /` with `Host: evil.example:8820` and require rejection **with no body**; repeat with a loopback `Host` and require 200.
- **Send your own** cross-origin POST and your own SSE upgrade from a non-allowlisted origin; both must be rejected.
- **`stat` the token file yourself** and read the mode; then `grep -r` the session tree, the event log and git for the token value — one hit is a rejection.
- **Assert `Access-Control-Allow-Origin` is never `*`** by reading response headers yourself.
- **Force a hook error** and confirm the tool call still proceeds; a hook that can block is a rejection.
- **Reject** if any response reflects a request header, or if any control is asserted in prose without a transcript.

## Dev Learnings

_Not Done until filled. Required: which control was easiest to implement in a way that looks present but is not enforced on every path, and where the pipeline order mattered._

## QA Learnings

_Not Done until filled. Required: which of the eight controls the request transcript would have let pass unverified._
