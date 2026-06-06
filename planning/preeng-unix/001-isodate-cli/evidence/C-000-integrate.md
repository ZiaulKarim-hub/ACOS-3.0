# Evidence Note — C-000 integration (root product: isodate CLI)

Role: Integrator (acos-execute-component). This note records the composition
of the root C-000 from its already-verified children. It does NOT mark C-000
passed — an independent Verifier makes the final call.

## Pre-flight: children verified
All three children are `status: passed` in `component-tree.json`:
- C-001 clock provider — passed (evidence/C-001-agent.md)
- C-002 date/time formatter — passed (evidence/C-002-agent.md)
- C-003 argument parser — passed (evidence/C-003-agent.md)

A parent may only be assembled from verified parts — satisfied.

## What was wired (entrypoint added)
Added a pure-composition root entrypoint to `build/isodate.py`:

- `main(argv) -> int` — wires the three leaves with NO behavior of its own
  beyond composition, in the order required by the contract and integration map:
  1. `flags = parse_args(argv)`  — **C-003**; on bad flags argparse raises
     `SystemExit(2)` with usage on stderr **before** any other component runs.
     `main()` deliberately does not catch it (that is C-003's contracted
     `usage_error` output, not parent logic).
  2. `dt = now(utc=flags.utc)`   — **C-001**; clock mode selected by `--utc`.
  3. `line = format_line(dt, flags.time)` — **C-002**; appends `HH:MM:SS` iff `--time`.
  4. `print(line)` → product stdout; `return 0` on success.
- `if __name__ == "__main__": sys.exit(main(sys.argv[1:]))` — makes the file a
  real CLI (valid flags print the line + exit 0; bad flag → argparse usage on
  stderr + non-zero exit, propagated by `sys.exit`).
- Added `import sys` (stdlib). Leaf functions were NOT modified — only wired.

## Child → parent connections (per integration-map.json)
| Edge | Child output | Feeds parent input | Wiring in main() |
|------|--------------|--------------------|------------------|
| C-003 → C-000 | `flags` Namespace{utc,time} | branch logic (clock mode + append-time) | `parse_args(argv)` called first |
| C-001 → C-000 | `now` datetime | the instant to format | `now(utc=flags.utc)` |
| C-002 → C-000 | `line` str | the exact stdout text | `format_line(dt, flags.time)` then `print(line)` |

External input `argv` (sys.argv[1:]) is an Assumption supplied by the OS shell,
not an internal component — matches `composability_check` (satisfied: true).

## EndToEndTests realized (build/tests/test_isodate.py)
Replaced the skeleton (which was skip-guarded and missing cases) with 9 live
tests exercising the assembled CLI both in-process (`main()`) and as a real
subprocess:
- `test_default_run_prints_date` — no flags → exactly one `YYYY-MM-DD` line, exit 0.
- `test_time_flag_appends_hms` — `--time` → `YYYY-MM-DD HH:MM:SS`, exit 0.
- `test_utc_path_prints_date` — `--utc` clock branch → date line, exit 0.
- `test_utc_time_composition_prints_datetime` — `--utc --time` composition → UTC datetime, exit 0.
- `test_bad_flag_exits_nonzero` — `main(["--bogus"])` raises SystemExit non-zero.
- `test_subprocess_default_prints_date_exit0` — real CLI, default.
- `test_subprocess_utc_time_prints_datetime_exit0` — real CLI, `--utc --time`.
- `test_subprocess_bad_flag_usage_on_stderr_nonzero` — real CLI bad flag: rc!=0,
  empty stdout, `usage` text on stderr.
- `test_subprocess_utc_time_value_deterministic_via_fixed_clock` — injects a
  fixed clock in a child interpreter to assert the exact line `2020-01-02 03:04:05`,
  proving the wiring carries the clock value verbatim through formatter to stdout.

## Results when run
- C-000 auto_check (contract method): `PYTHONPATH=.../build/tests python3 -m unittest test_isodate.EndToEndTests`
  → **Ran 9 tests, OK, exit 0**.
- Full suite (`test_isodate`): **Ran 22 tests, OK** — all leaf classes
  (ClockTests/FormatterTests/ParserTests) still green; no regression introduced.
- Human smoke (repo root):
  - `isodate.py` → `2026-06-05`, rc=0
  - `isodate.py --utc --time` → `2026-06-05 16:59:21`, rc=0
  - `isodate.py --bogus` → usage on stderr, rc=2
- stdlib-only check (AST): imports = {argparse, datetime, sys}; all stdlib → true.

## Acceptance criteria trace (C-000)
- [x] No-flag run prints exactly one YYYY-MM-DD line, exit 0.
- [x] `--utc --time` prints a UTC `YYYY-MM-DD HH:MM:SS` line, exit 0.
- [x] Bad flag exits non-zero, usage to stderr.
- [x] isodate.py imports only stdlib modules.

## Integration notes / drill-down
No child defects observed; no hidden behavior was patched into the parent. The
root is pure composition. Result handed off for independent verification.

Status reported by Integrator: **INTEGRATED** (Verifier makes the final call).
