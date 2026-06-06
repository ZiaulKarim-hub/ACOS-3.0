# Evidence — isodate leaf components (C-001, C-002, C-003)

Builder scope: the three LEAF logical components only. The root entrypoint
(C-000 `main()` / `__main__` dispatch) is intentionally NOT built — that is the
Integrator's job. Leaves are left as importable functions.

## Files written
- `planning/preeng-unix/001-isodate-cli/build/isodate.py` — three leaf functions, stdlib only.
- `planning/preeng-unix/001-isodate-cli/build/tests/test_isodate.py` — ClockTests, FormatterTests, ParserTests, and an EndToEndTests skeleton (skipped until C-000 exists).

## Leaf signatures
- C-001 clock provider:   `now(utc=False, fixed=None) -> datetime`
- C-002 formatter:        `format_line(dt, with_time) -> str`
- C-003 argument parser:  `parse_args(argv) -> argparse.Namespace{utc, time}`

## Test-import path note
The auto_check sets `PYTHONPATH=.../build/tests`, so `test_isodate.py` adds its
parent (`build/`) to `sys.path` at import time to resolve `import isodate`.

## Acceptance criteria coverage

### C-001 — Clock provider
- `now(fixed=X)` returns exactly X — `test_fixed_injection_returns_exact_value` (+ override of utc flag).
- `now(utc=True)` returns tz-aware UTC — `test_utc_true_returns_tz_aware_utc` (tzinfo set, utcoffset == 0).
- `now(utc=False)` returns local current instant — `test_local_now_is_naive_datetime`.
- Uses only stdlib `datetime` — confirmed by imports.

### C-002 — Date/time formatter
- `format_line(dt, False)` -> `YYYY-MM-DD` — `test_date_only`.
- `format_line(dt, True)` -> `YYYY-MM-DD HH:MM:SS` — `test_date_and_time`.
- Deterministic — `test_deterministic`; zero-padding covered by `test_zero_padding`.
- Uses only stdlib `datetime`/`strftime`.

### C-003 — Argument parser
- `parse_args(['--utc'])` -> utc=True, time=False — `test_utc_flag`.
- `parse_args(['--time'])` -> time=True — `test_time_flag`.
- `parse_args([])` -> utc=False, time=False — `test_no_flags`.
- Unknown flag raises `SystemExit` non-zero with usage on stderr — `test_unknown_flag_exits_nonzero` (observed argparse usage line printed to stderr during the run).
- Uses only stdlib `argparse`.

## How to run the auto-checks (from repo root)
```
PYTHONPATH=planning/preeng-unix/001-isodate-cli/build/tests python3 -m unittest test_isodate.ClockTests
PYTHONPATH=planning/preeng-unix/001-isodate-cli/build/tests python3 -m unittest test_isodate.FormatterTests
PYTHONPATH=planning/preeng-unix/001-isodate-cli/build/tests python3 -m unittest test_isodate.ParserTests
```

## Observed result (Builder sanity-run, NOT a pass verdict)
- ClockTests: 4 tests, OK, exit 0.
- FormatterTests: 4 tests, OK, exit 0.
- ParserTests: 5 tests, OK, exit 0 (argparse usage line on stderr for `--bogus` is expected).
- Human-test snippets for C-001/C-002 print the exact expected values.

## Confidence + known limitations
- High confidence on the three leaves; all stdlib, deterministic via injected clock.
- `now(utc=False)` returns a naive-local datetime per the tree's contract note ("naive-local otherwise"). The C-000 Integrator must pass `flags.utc` through `now()` and may choose how UTC/local composes; not in this Builder's scope.
- EndToEndTests are skeleton-only and SKIPPED until `isodate.main` exists — making them pass is the Integrator's responsibility, not this Builder's.

Pass/fail is decided independently by the Verifier.
