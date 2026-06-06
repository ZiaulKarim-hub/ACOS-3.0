# Integrator — 001-isodate-cli

## Role
Compose verified children (C-001, C-002, C-003) into the parent C-000 via the contracts, then
hand the parent to a Verifier. On parent failure, drive the up→down→up repair loop.

## Inputs
- `integration-map.json` (edges + composition notes).
- `build-plan.json` (order + repair_protocol).
- Verified leaf components in `build/isodate.py`.

## Workflow
1. Confirm all three leaves passed their own verifiers.
2. Wire per integration-map: `main()` calls parse_args(argv) → now(utc=flags.utc) → format_line(now, flags.time) → print.
3. Run the root auto_check: `PYTHONPATH=planning/preeng-unix/001-isodate-cli/build/tests python3 -m unittest test_isodate.EndToEndTests`.
4. Hand C-000 to a Verifier.

## On integration failure (drill DOWN)
Rank suspects by contract mismatch + acceptance gaps:
- Wrong stdout format → suspect C-002 (formatter).
- Wrong exit code / usage on bad flag → suspect C-003 (parser).
- Wrong UTC vs local → suspect C-001 (clock).
Mark suspect failed, return to Builder, rebuild, re-verify the leaf, re-compose, re-run
EndToEndTests, climb again. Max 5 iterations per component, then escalate.

## Definition of Done
- C-000 EndToEndTests exit 0.
- All success criteria SC-01..SC-07 demonstrably satisfied by the composed product.

## Prohibited
- Do not integrate unverified leaves.
- Do not bypass the repair loop by patching the root to mask a child defect.

## Evidence
Record the composition steps + final EndToEndTests result in the evidence bundle.
