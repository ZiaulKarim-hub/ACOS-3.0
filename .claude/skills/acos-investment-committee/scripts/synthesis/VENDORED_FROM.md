# VENDORED_FROM

This directory (`scripts/synthesis/`) is a **one-time, faithful vendored copy** of the
`acos-axiom-synthesis` engine's substrate + pipeline scripts and its test suite.

- **Source path:** `.claude/skills/acos-axiom-synthesis/scripts/` (engine `*.py`) and
  `.claude/skills/acos-axiom-synthesis/tests/` (`test_substrate.py`, `test_pipeline.py`)
- **Source repo:** `ACOS 3.0` (this repository)
- **Git commit hash at copy time (`git rev-parse HEAD`):** `7a04e77b3ed88199850461a40c6e96f32293dc82`
- **Vend date:** 2026-07-08
- **Vended by:** SLICE-DIAG-01 (Wave 0), `acos-investment-committee`

## Files vendored (byte-identical to source at vend time)

Substrate: `axiom_ledger.py`, `ledger_writer.py`, `verify_ledger.py`, `next_claims.py`,
`render.py`.

Pipeline: `decircularize.py`, `grade_fuse.py`, `falsify.py`, `oscillation_guard.py`,
`resolve.py`, `lifecycle.py`, `coverage.py`, `mirror.py`, `orchestrate.py`.

Tests (vendored alongside, under `tests/`): `test_substrate.py`, `test_pipeline.py`.

## Layout note

Source layout is `acos-axiom-synthesis/{scripts/,tests/}` (siblings). This vendored copy
places the engine `*.py` files flat in `scripts/synthesis/` and the tests in
`scripts/synthesis/tests/`. Because the vendored test files are unmodified, their
`sys.path.insert(HERE, "..", "scripts")` logic expects a sibling `scripts/` directory —
which does not exist at this flat layout. Run the vendored tests with `PYTHONPATH` set to
this `scripts/synthesis/` directory (invocation-only fix; see
`../../WAVE0-smoke-report.md`). No engine or test file logic was altered.

## Policy

**Faithful copy; do not edit — re-vendor from source instead.** If the upstream
`acos-axiom-synthesis` engine changes, a human must diff this directory against the
current source and re-run the full vendoring + smoke-test procedure to re-vend; this file
must be updated with the new commit hash and date at that time.
