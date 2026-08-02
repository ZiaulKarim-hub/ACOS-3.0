# S09-install-config-session-selftest — Symlink installer, project config, session tree, nested git repo, selftest harness

| Field | Value |
|---|---|
| Epic / Story | E1 / ST-02 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 1 / — |
| Depends on | S07-skill-router-and-confirmation-gate |
| Requirements | FR-013, FR-014, FR-015, FR-016 |
| Acceptance criteria | A88 · A83 · A85 · SL-S09-1 |
| CQ / evidence | — |

## PM — slice definition

**Objective.** Make installation drift-proof and every session resumable, versioned and self-testable from the first run.

**In scope.** `install.sh` (shell, two lines — it must run before Bun tooling is assumed present) creating a **symlink**, never a copy; `.acos/config/website-builder.yaml` with a snapshot to `audit/config-snapshot.yaml` at init; the full session tree; `git init` **inside the site tree as its own repo**, with the sessions path added to the framework's ignore file (NA-B11); `bun selftest.ts`.

**Out of scope.** Copying the skill anywhere. Committing session artifacts to the framework repo. Any product feature.

**Allowed files / contexts.**
- `install.sh`, `scripts/selftest.ts`, `scripts/lib/session.ts`, `.acos/config/website-builder.yaml` (template), the framework `.gitignore`.

**Steps.**
1. `install.sh`: create the symlink into the global skills directory; refuse to run if a **copy** already exists there, naming the drift risk.
2. Session tree: create the numbered step directories, `.wb/`, `evidence/`, `audit/`, `state.json`, `events.jsonl` and the `ACTIVE` marker exactly as specified; remove `ACTIVE` at close.
3. Config: write the per-project config (version, port, breakpoints, direction count, variants per component, artwork count, gate thresholds, licence policy tier, publish target) and snapshot it hash-stamped into `audit/`.
4. Git: initialise the site tree as its own repository; add the sessions path to the framework ignore file; assert both.
5. `selftest.ts`: an assertion harness that fails the process on the first failed assertion and prints a count.

**Definition of Done.**
- Artifacts: installer, session bootstrap, config template plus snapshot, selftest harness.
- Validation: `ls -la` of the global skills directory shows an arrow; the site tree reports itself as a git repository; the sessions path is ignored by the framework repo; `bun selftest.ts` exits 0 with 100% of assertions passing.
- `slice.yaml` mapping — `acceptance_criteria: [A88, A83, A85, SL-S09-1]`, `verification_method: exit-code` (A88: `grep-assert`).

## Dev — execution contract

Never `rm -rf` anything (destructive commands score high with the permission layer); create-then-swap where a replacement is needed. Evidence bundle: (1) summary; (2) traceability FR-013…FR-016 → file:line; (3) structural quality — the installer has no Bun dependency; (4) functional testing — `ls -la` output, `git rev-parse` output, ignore-file grep, selftest exit code; (5) security/compliance — config contains no credential; (6) operational — how to uninstall without touching a session; (7) self-assessment.

## QA — zero-trust verification

- **Run your own** `ls -la ~/.claude/skills/ | grep acos-website-builder` and require a `->`; a copy is an outright rejection.
- **Run your own** `git -C <site tree> rev-parse --is-inside-work-tree` and require `true`.
- **Grep** the framework ignore file yourself for the sessions path.
- **Run** `bun selftest.ts` yourself; a reported pass without your own exit code is a rejection.
- **Reject** if the config snapshot is not hash-stamped — an unstamped snapshot cannot prove what the session was judged under.

## Dev Learnings

_Not Done until filled. Required: whether the two-copy drift pattern in the estate was actually broken, and what would let it recur._

## QA Learnings

_Not Done until filled. Required: what the selftest harness does not yet assert that it should._
