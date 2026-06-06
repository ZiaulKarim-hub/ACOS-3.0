# Coverage Report — 001-isodate-cli

## Success-criteria → component coverage matrix

| Criterion | Statement (abbrev) | Covered by | Covered? |
|---|---|---|---|
| SC-01 | No-flag run prints valid local `YYYY-MM-DD` | C-003, C-001, C-002, C-000 | Yes |
| SC-02 | `--utc` prints UTC date | C-003, C-001, C-002, C-000 | Yes |
| SC-03 | `--time` appends `HH:MM:SS` | C-002, C-001, C-000 | Yes |
| SC-04 | `--utc --time` composes both | C-003, C-001, C-002, C-000 | Yes |
| SC-05 | Bad flag → non-zero exit + usage on stderr | C-003, C-000 | Yes |
| SC-06 | Stdlib-only + testable via shell/unittest | C-000, C-001, C-002, C-003 | Yes |
| SC-07 | Deterministic under injected fixed clock | C-001, C-002 | Yes |

**Coverage: 7 / 7 success criteria covered (100%).**

## Gate results

1. **Coverage gate — PASS.** Every criterion has at least one covering component path; no orphan criteria.
2. **Testability gate — PASS.** All 4 nodes carry a non-empty `verifier.human_test.procedure` and non-empty `acceptance_criteria`. Every node uses `software-test` with `auto_check.runnable=true`; all four auto_check commands were executed live and returned `OK` (13 tests total).
3. **Composability gate — PASS.** Root C-000's required inputs (`parsed_flags`, `now`, `rendered_line`) are each produced by a child output (C-003, C-001, C-002 respectively) per `integration-map.json`. The only external input is `argv` (OS shell), documented as an Assumption.

**QA status: APPROVED** (see `coverage_qa_report.json`).

## Reuse summary

- **C-001 Clock provider** — reusable (tags: clock, time-source, injectable, determinism); consumed by C-002 and C-000.
- **C-002 Date/time formatter** — reusable (tags: formatter, iso8601, datetime, rendering); consumed by C-000.
- **C-003 Argument parser** — reusable (tags: argparse, cli-flags, usage, exit-code); consumed by C-000.
- **C-000** — the product entry point; not reusable.

## Self-verification evidence
All component auto_check commands run from repo root:
- `...ClockTests` → OK (3 tests)
- `...FormatterTests` → OK (2 tests)
- `...ParserTests` → OK (4 tests)
- `...EndToEndTests` → OK (4 tests)
Total: 13 tests, all passing, zero human input.
