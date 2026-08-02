# S77-selftest-and-evidence-bundles — Selftest at full assertion pass and per-slice evidence bundles

| Field | Value |
|---|---|
| Epic / Story | E19 / ST-26 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 6 / — |
| Depends on | S09-install-config-session-selftest, S76-acceptance-criteria-sweep |
| Requirements | FR-251 |
| Acceptance criteria | A85 · A84 · A86 · A87 · A88 · A89 · SL-S77-1 |
| CQ / evidence | — |
| Note | **A85 is 100% of assertions, not a percentage bar.** The in-estate precedent is 67/67; the bar here is every assertion the harness contains, and a skipped assertion is a failed one |

## PM — slice definition

**Objective.** Make the release claim **testable**, and make every slice's evidence **reproducible from disk**.

**In scope.** `bun selftest.ts` extended to cover the whole skill and required to pass **100% of assertions before any release claim** (A85); the packaging assertions run inside it — **zero `.py` files** under the skill's `scripts/`/`app/` trees (A84, NG6, the only contemplated exception being the sign-off-gated F4 launcher rung), **zero files added to `.claude/agents/`** (A86), `Task` **absent** from the skill frontmatter's `allowed-tools` (A87), the install being a **symlink** verified by an `ls -la` showing the arrow (A88), and the rule that subagents are policy-blocked from `Write` so agent-produced code returns as text and the main thread writes it (A89); plus per-slice evidence bundles under `.acos/evidence/[DATE]/[SLICE-ID]/` with **all seven sections** present for every slice in this feature.

**Out of scope.** Writing the individual slices' evidence — each slice owns its own bundle; this slice **audits** their presence and shape. Loosening A85 to a percentage. Adding a Python file anywhere for any reason.

**Allowed files / contexts.**
- `scripts/selftest.ts`, `scripts/lib/packaging-assertions.ts`, `scripts/evidence-audit.ts`, `.acos/evidence/[DATE]/[SLICE-ID]/` (read + index write).
- **This slice may not edit another slice's evidence bundle** — it reports a missing section, it does not fill one in.

**Steps.**
1. Consolidate every module's assertions into one harness that fails the process on the first failure and prints `passed/total`; **skipped counts as failed**.
2. Implement the packaging assertions: `find scripts app -name '*.py' | wc -l` is 0; `.claude/agents/` gained zero files; the frontmatter `allowed-tools` line omits `Task`; `ls -la ~/.claude/skills/ | grep acos-website-builder` shows `->`; the no-subagent-Write rule is asserted as a documented constraint with an inline main-session path for every named feature (`§16.5.1-O31`).
3. Implement `evidence-audit.ts`: for every slice id in `stories.json`, require a bundle directory and **all seven sections** — summary, traceability, structural quality, functional testing, security/compliance, operational, self-assessment.
4. Make the audit's failure mode specific: name the slice **and** the missing section, never a count.
5. Wire the selftest into the resume path and into LOCK so a release claim cannot be made from a stale green.
6. Record the assertion total as a first-party number; it is the figure any release claim is measured against.

**Definition of Done.**
- Artifacts: the consolidated `selftest.ts`, packaging assertions, `evidence-audit.ts`, the audit report, the recorded `passed/total`.
- Validation: `bun selftest.ts` exits 0 with `passed == total`; a seeded `.py` file fails it; a seeded missing evidence section is named by slice and section; the symlink assertion fails against a copied install.
- `slice.yaml` mapping — `acceptance_criteria: [A85, A84, A86, A87, A88, A89, SL-S77-1]`, `verification_method: exit-code` (A84/A86/A87/A88/A89: `grep-assert`).

## Dev — execution contract

All new code is **TypeScript run by Bun**; there is no circumstance in which this slice adds Python, and the assertion that proves it is part of the deliverable. Evidence bundle: (1) summary with `passed/total` and the audit's slice coverage; (2) traceability FR-251 → file:line per assertion group; (3) structural quality — assertions are registered, not scattered, so the total is countable; (4) functional testing — the selftest transcript plus one seeded failure per packaging assertion; (5) security/compliance — the selftest reads no credential and opens no socket beyond the loopback probe; (6) operational — how to run one assertion group in isolation; (7) self-assessment naming what the harness still does not assert.

## QA — zero-trust verification

- **Run `bun selftest.ts` yourself** and read the exit code; a reported pass without your own exit code is a rejection.
- **Confirm `passed == total`** and that **no assertion is skipped**; a harness reporting 100% while skipping is the defect this criterion exists to prevent.
- **Run your own** `find` for `.py` files under the skill tree, your own `ls -la | grep` for the symlink arrow, and your own grep of the frontmatter for `Task`.
- **Seed a missing evidence section** in a scratch copy and confirm the audit names the slice and the section.
- **Count the bundles yourself** against the slice list in `stories.json`.
- **Reject** if this slice wrote into another slice's bundle.
- **Reject** if the selftest can be satisfied without the packaging assertions running.

## Dev Learnings

_Not Done until filled. Required: the final assertion total, and which packaging assertion was closest to failing._

## QA Learnings

_Not Done until filled. Required: whether any assertion was silently skipped, and which evidence section was most often thin across slices._
