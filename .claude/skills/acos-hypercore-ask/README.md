# acos-hypercore-ask — developer README

Trust-first natural-language interface to the Hypercore loan-servicing platform.
This README is the engineering companion to `SKILL.md` (the user/agent-facing surface).

## Status

**FULL — live-verified 2026-06-19.** All pipeline stages are built and the skill answers
live against the Hypercore GraphQL API under Doppler (`hypercore-ask/dev_personal`):
read-only adapter, two-tier provenance cache, deterministic gates, adversarial consensus,
deliver/report/feed envelopes, fuzzy loan-name resolution, a figures registry (native +
derived), KG-joined leverage ratios, and a portfolio analysis layer. Every delivered value
is provenance-bound or the skill REFUSES. Still fully fixture-testable offline (stdlib
`unittest`, no network). See `SKILL.md` for the user/agent-facing surface.

## Directory layout

```
.claude/skills/acos-hypercore-ask/
  SKILL.md          command surface + pipeline (user/agent-facing)
  README.md         this file
  config.yaml       consensus / freshness / confidence / adapter defaults (NO secrets)
  fixtures/         canned RawApiResponse JSON (synthetic, for offline tests)
  schemas/          expected entity schemas (live-introspection-derived; drift-checked)
  prompts/          blind-extractor prompt for the consensus agents
  demos/            end-to-end walkthroughs (thin path / consensus / report / feed)

.claude/scripts/
  hca-route.py      intake & tier router (deterministic; no network)
  hca-adapter.py    read-only adapter contract + FixtureBackend + LiveBackend
  hca-secrets.py    Doppler/env credential + JWT token handling (no values in repo)
  hca-live.py       live GraphQL transport (read-only; TLS; pagination to completion)
  hca-cache.py      two-tier cache (Tier-1 RawApiResponse + Tier-2 NormalizedAnswerRecord)
  hca-normalize.py  Tier-2 normalization
  hca-provenance.py provenance binder (bind value -> cited Tier-1 source; else REFUSE)
  hca-gates.py      deterministic gate suite (schema/pagination/freshness/reconcile/...)
  hca-consensus.py  adversarial N-agent substance consensus + bounded blind re-dispatch
  hca-deliver.py    delivery spine + ReportBuilder (multi-figure report orchestration)
  hca-feed.py       JSON/CSV/feed renderer + schema-valid provenance manifest
  hca-resolve.py    fuzzy loan-name resolver (real loans via searchString list query)
  hca-figures.py    Figure/FigureRegistry: native + derived figures, payoff/early-redemption
  hca-ontology.py   PRISM-seeded private-credit concept map
  hca-kg.py         OKOA knowledge-graph join for leverage ratios (dual provenance)
  hca-analyze.py    portfolio analysis layer (rankings, roll-ups, concentration, covenant)
  tests/            stdlib unittest suites (read-only guard, fixtures only, no network)
```

All of the above are BUILT and live-verified. The planning record for this skill lives at
`planning/preeng/001-hypercore-ask/`.

## Ground rules (locked)

See `memory/decisions/2026-06-18-hca-build-ground-rules.md`. In short:

- Python 3 stdlib only; no third-party deps.
- Read-only adapter, structurally enforced (no mutating method exists; guard test asserts it).
- Stubbed-until-access: live calls live only in `LiveBackend` (`NotImplementedError` for now);
  `FixtureBackend` is active.
- Graceful degradation: `is_live() == false` → `NO_LIVE_DATA` / `NoLiveDataError`, never fabricate.
- Secrets via env / Doppler only (`CLIENT_ID` + `HYPERCORE_CLIENT_SECRET`; names configurable;
  `HYPERCORE_BASE_URL` is an optional URL override, not a credential); none in repo.
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
doppler run --project hypercore-ask --config dev_personal -- python3 .claude/scripts/hca-adapter.py ...
```

`config.yaml` declares only the credential env var NAMES under
`adapter.credentials_env` — `client_id` (=`CLIENT_ID`) and `client_secret`
(=`HYPERCORE_CLIENT_SECRET`) — never the values. The GraphQL URL defaults to the public
endpoint in `config.yaml` and can be overridden by the optional `HYPERCORE_BASE_URL` env
var (an override, not a credential).

## Evidence

Foundation evidence bundle: `.acos/evidence/2026-06-18/SLICE-HCA-00-02/`.
