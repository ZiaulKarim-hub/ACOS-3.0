# Vision

`isodate CLI` is a tiny, single-file Python 3 standard-library-only command-line tool
(`isodate.py`) that prints the current date. With no arguments it prints the local date in
ISO-8601 form (`YYYY-MM-DD`). The `--utc` flag prints the current UTC date instead; the
`--time` flag appends the current time as `HH:MM:SS`; the two flags compose freely. Unknown or
malformed flags cause the tool to exit with a non-zero status and emit a usage message on
stderr. All date/time logic is driven through an injectable clock so the behavior is fully
deterministic under test.

## Domain

Software — a command-line utility (CLI tool) implemented in Python 3 using only the standard
library (`argparse`, `datetime`). No third-party runtime dependencies.

## Success Criteria (testable)

- **SC-01** — `python3 build/isodate.py` (no flags) prints a single line matching `YYYY-MM-DD` (local date).
- **SC-02** — `python3 build/isodate.py --utc` prints the current UTC date as `YYYY-MM-DD`.
- **SC-03** — `python3 build/isodate.py --time` appends the current time as `HH:MM:SS` to the date output.
- **SC-04** — `python3 build/isodate.py --utc --time` composes both behaviors: UTC date + UTC time.
- **SC-05** — An unknown/bad flag causes exit status ≠ 0 with a usage message written to stderr.
- **SC-06** — The implementation imports only Python 3 standard-library modules and is testable via shell/`unittest`.
- **SC-07** — Date/time output is deterministic when a fixed clock is injected (same input clock → same output).

## Verifier Vocabulary

- **software-test** — the system runs a named shell/test command and asserts exit code 0 plus
  expected stdout/stderr; a human can run the identical command and read pass/fail. THIS is the
  verifier type used by every node in this product (all nodes are software).
- **manual-only** — present in the vocabulary for completeness but NOT used by any node in this
  product; every node here is machine-verifiable.

## Assumptions

- Assumption: Test runner is plain-shell + Python stdlib `unittest` (invoked via `python3 -m unittest`), because `pytest` is not guaranteed to be installed; this keeps every auto_check runnable with zero extra dependencies from repo root.
- Assumption: Determinism is achieved by an injectable clock — a `now()` provider that accepts an optional fixed datetime — rather than monkeypatching `datetime`.
- Assumption: "Local date" uses the system local timezone via `datetime.now()`; `--utc` uses `datetime.now(timezone.utc)`.
- Assumption: Bad-flag behavior follows `argparse` defaults (exit code 2, usage on stderr), which satisfies "exit non-zero with a usage message".
- Assumption: The component tree is kept to 4 components (root CLI + clock + formatter + arg parser) to honor the 3–5 target, with a single shared formatter and shared clock.
- Assumption: Build artifacts live under `build/` (`build/isodate.py`, `build/tests/test_isodate.py`); auto_check commands run from repo root referencing those paths.
