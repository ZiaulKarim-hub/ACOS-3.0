# Builder — 001-isodate-cli

## Role
Produce exactly ONE component's output artifact, only within that component's allowed scope.
You build leaves first (C-001, C-002, C-003), then the integrator composes them into C-000.

## Inputs
- `component-tree.json` (your component's node: purpose, single_responsibility, output_artifact, contract, acceptance_criteria).
- `components/<id>.md` (human spec).
- Target file: `build/isodate.py` (your component is one function within it: now / format_line / parse_args / main).

## Workflow
1. Read your node + its `components/<id>.md`.
2. Implement ONLY your function(s) in `build/isodate.py`. Do not modify other components' functions beyond their declared contract.
3. Use Python 3 stdlib only (argparse, datetime). No third-party imports.
4. Run your component's auto_check: `PYTHONPATH=planning/preeng-unix/001-isodate-cli/build/tests python3 -m unittest test_isodate.<YourTestClass>`.
5. Hand off to the Verifier.

## Definition of Done
- Your function satisfies every acceptance criterion in your node.
- Your component's auto_check command exits 0.
- Output lands at `build/isodate.py` (location_hint).

## Prohibited
- No third-party dependencies.
- No editing the verifier/tests to make them pass.
- No work outside your component's single responsibility.

## Evidence
Record the auto_check command output (OK + test count) for the verifier's zero-trust review.
