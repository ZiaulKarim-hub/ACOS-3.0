# S39-ownership-guard-wb-op-and-inbox — Ownership guard with stated limits, the sanctioned agent write path, and the inbox

| Field | Value |
|---|---|
| Epic / Story | E16 / ST-12 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 2 / — |
| Depends on | S38-reconciliation-409-lock-and-tab-claim |
| Requirements | FR-221, FR-223, FR-224, FR-228 |
| Acceptance criteria | A78 (amended) · A79 · A81 · A89 · §12.17-A96 · SL-S39-1 · SL-S39-2 |
| CQ / evidence | CQ7 · CQ8 |
| Note | **NA-B15** — the write-allowlist **table** supersedes A78's three-shape assertion; A78 is amended, not satisfied as written. The table also adds `/systemLock`-pointer rejection and symlink rejection |

## PM — slice definition

**Objective.** Give the agent a legal write path so the ownership rule is followed rather than routed around, and keep one validation path for both writers.

**In scope.** **One writer** — `wb-server` is the only process that writes the doc-owned set; the browser proposes typed semantic ops and never performs raw file writes. Enforcement of the write-allowlist table by path shape (`pages/*.doc.json`, `content.json`, `site.json`, `assets/manifest.json`, `provenance.json`, `history.jsonl`, `.wb/**` with `.wb/locks/**` read-only to the server), resolved by `realpath` → `startsWith(sessionRoot)` assertion → symlink rejected → `..` rejected, **re-checked after resolution, not before**. Rejection of a raw JSON Patch body and of any file path in a request body. Rejection with **400** of any derived patch whose pointer starts `/systemLock`, whichever op produced it. A **fail-open** PreToolUse ownership guard blocking `Write`/`Edit` on doc-owned paths and scanning Bash command text, registered dynamically and removed at close, **with its limits written into the skill instructions**. `wb op '<typed op JSON>'` posting the same typed op the browser posts, through the same server, inheriting validation, the op log, optimistic concurrency and the SSE push — and starting a **headless** server when none is running. `.wb/inbox.jsonl` as append-only `{id, ts, actor, intent, payload, status}`, watched by a blocking `tail -f` in the Claude session; **agent ops go through the inbox always**, even when the editor is not running. **The server NEVER calls `Task()`; the Claude session is the only engine.**

**Out of scope.** Reconciliation, 409 and the lock (S38) — this slice consumes them and must not re-implement them. `chmod 0444` and `.gitattributes` / pre-commit advisories, which are recorded as advisory only.

**Allowed files / contexts.**
- `scripts/lib/write-allowlist.ts`, `scripts/lib/ownership-guard.ts`, `scripts/wb.ts` (the `op` subcommand), `scripts/lib/inbox.ts`, the op validator from S31, the skill instruction file.
- Runtime-only: `.wb/inbox.jsonl`.

**Assumption (recorded).** The requirement names the inbox `commands.jsonl` while the data model names it `.wb/inbox.jsonl` "(a.k.a. `commands.jsonl`)"; this slice treats `.wb/inbox.jsonl` as canonical and the other as an alias `[I]`.

**Steps.**
1. Implement the allowlist as a table of path shapes with permitted ops, not as a list of prefixes; everything not in the table is rejected.
2. Resolve then check: `realpath` first, prefix assertion second; add a fixture that symlinks an allowed name to an outside file and require rejection.
3. Add the `/systemLock` pointer rejection in the patch-derivation step, so it holds for every op present and future.
4. Build `wb op` over the same HTTP route the browser uses; on no server, start one headless, apply, exit.
5. Route agent ops through the inbox unconditionally; truncate-after-apply and record `status`.
6. Implement the guard fail-open; write its limits into the skill instructions in the imperative — it is a heuristic, defeatable by indirection, and **reconciliation is the authoritative mechanism**.

**Definition of Done.**
- Artifacts: allowlist module, guard, `wb op`, inbox reader/writer, the amended skill-instruction text.
- Validation: symlinked path rejected; raw JSON Patch rejected; file path in body rejected; `/systemLock` patch rejected 400 from two different ops; `wb op` applies with no browser open; an inbox entry applies and is marked; a forced guard error still allows the tool call.
- `slice.yaml` mapping — `acceptance_criteria: [A78, A79, A81, A89, "§12.17-A96", SL-S39-1, SL-S39-2]`, `verification_method: exit-code` (A89 and SL-S39-2: `grep-assert`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-221, FR-223, FR-224, FR-228 → file:line; (3) structural quality — one validator serving browser, `wb op` and inbox alike, proven by call graph; (4) functional testing — the six rejection fixtures plus the headless-apply transcript; (5) security/compliance — the guard's limits stated plainly, and the ranking that puts reconciliation above it; (6) operational — how the `tail -f` watcher is started and stopped, and its zero-token-cost property; (7) self-assessment.

## QA — zero-trust verification

- **Build your own symlink fixture** inside the session pointing outside it and require a rejection; a prefix check performed before resolution is a rejection of the slice.
- **POST a raw JSON Patch yourself** and require refusal; then POST two different ops whose derived patch touches `/systemLock` and require 400 from both.
- **Run `wb op` with no browser open** and confirm the doc changed, the op landed in `history.jsonl`, and the journal was updated.
- **`grep` the skill instructions** for the stated guard limit and for the "server never calls `Task()`" rule; absence is a rejection.
- **Reject** if the guard is presented anywhere as the anti-clobber mechanism.

## Dev Learnings

_Not Done until filled. Required: which indirection defeated the guard in testing, and how the inbox path behaved when the editor was closed._

## QA Learnings

_Not Done until filled. Required: whether any write path reached disk without passing the single validator._
