# acos-hypercore-ask — developer README

Trust-first natural-language interface to the Hypercore loan-servicing platform.
This README is the engineering companion to `SKILL.md` (the user/agent-facing surface).

## Status

**FOUNDATION (slices 00–02 built).** Buildable and testable today entirely on fixtures.
No live Hypercore call is made by any part of this skill — live access is stubbed behind
an unchanged read-only adapter contract until credentials are provisioned (Doppler).

## Directory layout

```
.claude/skills/acos-hypercore-ask/
  SKILL.md          command surface + forward pipeline (user/agent-facing)
  README.md         this file
  config.yaml       consensus / freshness / confidence / adapter defaults (NO secrets)
  fixtures/         canned RawApiResponse JSON (PLACEHOLDER synthetic data)   [slice-02]
  schemas/          expected entity schemas (validated in slice-05)           [slice-02]

.claude/scripts/
  hca-route.py      intake & tier router (deterministic; no network)          [slice-01]
  hca-adapter.py    read-only adapter contract + FixtureBackend + LiveBackend [slice-02]
  tests/
    test_hca_adapter.py   stdlib unittest incl. read-only guard test          [slice-02]
```

Downstream scripts (`hca-cache.py`, `hca-normalize.py`, `hca-consensus.py`,
`hca-gates.py`, `hca-provenance.py`, `hca-deliver.py`) are forward references — see
`tech_prd.md` §1 — and are NOT built in this foundation.

## Ground rules (locked)

See `memory/decisions/2026-06-18-hca-build-ground-rules.md`. In short:

- Python 3 stdlib only; no third-party deps.
- Read-only adapter, structurally enforced (no mutating method exists; guard test asserts it).
- Stubbed-until-access: live calls live only in `LiveBackend` (`NotImplementedError` for now);
  `FixtureBackend` is active.
- Graceful degradation: `is_live() == false` → `NO_LIVE_DATA` / `NoLiveDataError`, never fabricate.
- Secrets via env / Doppler only (`HYPERCORE_CLIENT_SECRET`, `HYPERCORE_BASE_URL`; names configurable);
  none in repo.
- Subscription-only Claude: blind extraction via `Task()`; never `ANTHROPIC_API_KEY`.

## Running the foundation locally

```bash
# Tier router self-test (must exit 0)
python3 .claude/scripts/hca-route.py --selftest

# Classify one question
python3 .claude/scripts/hca-route.py "What is the total exposure across the portfolio?"

# Adapter test suite (read-only guard, fixture roundtrip, degradation, live stub)
python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py' -v
```

## Secrets (Doppler)

Credentials are NEVER stored in this repo. At runtime they come from environment
variables injected by Doppler:

```bash
doppler run --project acos-3-0 --config dev -- python3 .claude/scripts/hca-adapter.py ...
```

`config.yaml` declares only the env var NAMES (`adapter.credentials_env.api_key`,
`adapter.credentials_env.base_url`), not the values.

## Evidence

Foundation evidence bundle: `.acos/evidence/2026-06-18/SLICE-HCA-00-02/`.
