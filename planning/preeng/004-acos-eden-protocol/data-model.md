# Data Model — acos-eden-protocol

## E1 — EdenLevel state (`.acos/state/eden-level`)
| Field | Value |
|---|---|
| Format | plain text, a single character |
| Domain | `1` \| `2` \| `3` \| `4` \| `5` |
| Absence | **file does not exist ⇒ off** (no separate "0"/"off" token stored) |
| Lifecycle | survives `/clear`; excluded from `session-cleanup.sh` purge (persists across sessions) |
| Written by | the skill front door (toggle) |
| Read by | `eden-level-injector.py` every turn |

## E2 — Level-spec table (embedded in SKILL.md + directive) — school-band dial (updated 2026-07-13)
| Level | Reader | Age | FK grade | FRE | Max sentence (words) | Vocabulary rule |
|---|---|---|---|---|---|---|
| 1 | College | ~18–22 | 13–16+ | 10–40 | 25–35 | full academic vocab; jargon allowed undefined |
| 2 | High school | ~14–18 | 9–12 | 45–60 | 18–22 | assume no subject background; **define every domain term on first use** |
| 3 | Middle school | ~11–13 | 6–8 | 60–70 | 12–15 | assume no subject background; **define every term**; short plain sentences |
| 4 | Elementary | ~8–10 | 3–5 | 80–90 | 8–12 | common everyday words; define harder words in-sentence; concrete analogies |
| 5 | Kindergarten | ~5 | 0–1 | 95–100 | 5–7 (one idea) | simplest words ≤2 syllables; physical examples only |
| off | Normal | — | — | — | — | no rewrite pass |

_History: the original 5-audience spec (university / HS-senior-no-knowledge / HS-junior / 5th / 1st)
was relabeled to a clean school-band ladder on 2026-07-13 at user request; the "assume no subject
background → define every term" behavior was retained on BOTH High school (2) and Middle school (3)._

## E3 — Exempt-content classifier (detector spec)
Detects spans passed through **byte-for-byte** at every level:
| Class | Heuristic |
|---|---|
| Code (fenced / inline) | ```` ``` ```` fences; `` `...` `` inline spans |
| Shell commands / CLI | lines starting with a known verb or `$`, flag tokens `--x` |
| File paths | `/`- or `~/`-rooted tokens; `*.ext` |
| API / function / config names | dotted identifiers, `key: value`, camelCase/snake_case idents |
| URLs / citations | `https?://…`; `[n]` / footnote / doc-ref markers |
| Exact quotes | text inside quotation marks attributed to a source |
| Formulas | math/financial expressions (XIRR, waterfall tiers, `=`-expressions) |
| Numbers-with-units | currency, `%`, dates, ratios (LTV/DSCR), counts, IDs |
| Defined entities | Capitalized contract-defined terms ("Borrower", "Event of Default") |
| Warnings / regulatory | disclosure / safety / "subject to" language |

## E4 — Per-turn directive (payload)
Fields: `active_level`, `reader_label`, `scope_statement`, `level_spec_row`, `fidelity_floor_compact`,
`precision_appendix_rule`. Rendered as `additionalContext` text (see tech_prd §2.2).

## E5 — Fidelity Floor (invariant set)
Ordered list of 8 invariants (research.md §3). Referenced by the directive and by `qa.md`. Immutable
across levels.

## E6 — Precision appendix (block)
| Field | Value |
|---|---|
| Trigger | reply contains ≥1 exempt span |
| Default | ON (globally); session toggle may hide for casual use |
| Source | the ORIGINAL composed answer (never re-derived from simplified text) |
| Render | collapsible "Exact figures & terms" footer listing every exempt span verbatim |

## E7 — Command grammar (parser states)
| Input | Action | State change |
|---|---|---|
| (bare) | default to level 3 (middle school) + banner | write `3` |
| `status` | report active level + (first use) grammar table | none |
| `off` | clear filter | delete file |
| `1`..`5` / `level N` | set level N | write `N` |
| invalid (`7`,`banana`,`on`) | error naming valid range | none |

_Updated 2026-07-13: (1) bare invocation now defaults to level 3 (was: show status); `status` is the
explicit way to check the current level. (2) `on` was dropped entirely — it is no longer a command and
now errors like any unrecognized token. Bare is a defined default that always announces the level it
set, so it is not a silent guess; only genuinely unrecognized tokens error._

## E8 — Per-message override (ephemeral)
`raw:` (⇒ off for this reply) or `L{n}:` (⇒ level n for this reply) prefix. Applies to ONE reply.
**Never** writes E1. Parsed from the user message, not the state file.
