# Analysis Report — 001-isodate-cli

## Reuse map

| Component | Reusable | Tags | Known consumers |
|---|---|---|---|
| C-001 Clock provider | Yes | clock, time-source, injectable, determinism | C-002, C-000 |
| C-002 Date/time formatter | Yes | formatter, iso8601, datetime, rendering | C-000 |
| C-003 Argument parser | Yes | argparse, cli-flags, usage, exit-code | C-000 |
| C-000 isodate CLI | No | cli, entrypoint, isodate | — |

## Canonical-candidate components (exemplary, reusable)

- **C-001 Clock provider** — strong canonical candidate. The "isolate the non-deterministic
  time source behind a tiny injectable provider" pattern (CAGE node N-05) is broadly reusable
  across any CLI/service that must be deterministic under test. Recommend promoting to a shared
  library if a second feature needs injectable time.
- **C-002 Date/time formatter** — pure function (datetime + bool → str), no side effects;
  trivially reusable wherever ISO-8601 date/time rendering is needed.

## Bloat annotations (annotate only — nothing deleted)

| Component | Classification | Rationale |
|---|---|---|
| C-000 | Active | Required product entry point; thin composition layer, no redundancy. |
| C-001 | Active | Atomic, single-responsibility, carries the determinism guarantee. |
| C-002 | Active | Single shared formatter — already deduplicated across all flag combinations. |
| C-003 | Active | Atomic argparse wrapper; owns the usage/exit-code contract. |

No components fall into **Review** or **Burn-Pile**. The tree is minimal (4 nodes for a 3–5
target) with no duplicated capability: the shared-formatter and shared-clock decisions
(CAGE N-06, N-02) pre-empted the most likely duplication.

## Notes
- Assumption surfaced: stdlib `unittest` selected over `pytest` (not installed) so every
  verifier is runnable with zero third-party dependencies — consistent with stdlib-only.
- Assumption surfaced: `argv` is an external input to the root; not modeled as an internal
  component because the OS shell supplies it.
