# Independent PRD audit — acos-nemesis-protocol

Phase 5.6 of `/acos-skill-maker` (R-048). Auditor: `Task(qa-reviewer)`, read-only, isolated, given only
`prd/PRD.md` and the skill directory (plus the two Oracle files and the skill-maker named by R-038/R-049).
The builder never saw `holdout/pack/`; the auditor never opened it either. Four rounds, 2026-10-08.

## Round 1 — 12 findings (all fixed)

| # | Finding (auditor's words, abridged) | Fix |
|---|---|---|
| 1 | R-002 PARTIAL — enroll never wrote `source_globs`/`exclude_globs` into config.json | `cmdEnroll` writes both; `canonical()` added in `scope.ts` for symlinked parents |
| 2 | R-007 PARTIAL — the daemon's request log lacked the contract fields | `RequestContract` on every verdict request; logged by the daemon (`requests.log`) and per project (`records/requests.jsonl`) |
| 3 | R-013 DIVERGES — Bash pre-snapshot re-hashed every file, no cache | `indexTree` reuses hashes on unchanged mtime+size; `refreshTreeIndex` persists the cache |
| 4 | R-014 PARTIAL — data scan lacked TIN/EIN, bank shapes, error-message lines | patterns added; `ERROR_LINE` routes error messages to checklist 3.3.6 |
| 5 | R-015 PARTIAL — "gitleaks if installed" missing | `detectToolchain` adds a `gitleaks` check when the binary exists |
| 6 | R-022 PARTIAL — `nemesis scan` clean S3 wrote no green snapshot | `cmdScan` diffs the tree index and snapshots changed files |
| 7 | R-024 DIVERGES — rung 8 unreachable; `issue decide` needed `--force` | `release-gate` moves open issues to rung 8 and writes the product report; `--force` removed |
| 8 | R-027 PARTIAL — no-block path untested | selftest `green path: task closes, release gate opens and goal-complete is accepted` |
| 9 | R-032 DIVERGES — S6/S7/S8 never used the daemon; close path untested | `requestGeneric` goes socket → autostart → direct (`askSocketSync`, `sock-ask.ts`); green-path selftest |
| 10 | R-034 PARTIAL — "record is written" untested | green-path selftest |
| 11 | R-035 PARTIAL — daemon status and socket round trip untested | selftest `daemon serves a request over its socket and status shows it` |
| 12 | R-037 PARTIAL — retry waits hardcoded, not 10 minutes | `retryWaits()` from config `judge_retry_waits_ms`, default `[60000, 180000, 360000]` |

## Round 2 — 12 verified FIXED; 3 new findings (all fixed)

```
R-017: PARTIAL — status `fixing` declared but never assigned.
R-033: DIVERGES — pack authored at `task start`, before S1 exists; never re-derived from S1.
R-034: PARTIAL — rotation demanded only of critical 3.4.x issues.
```

Fixes: a judged-clean edit on an issue's file sets `fixing` (`pre-tool.ts`, event `fix-landed`); the pack is
authored at `task design` and re-sealed as a new version on `task redesign`; the release gate demands a
rotation entry for any issue under checklist 3.4.x or whose finding names a secret, at any severity.

## Round 3 — 3 verified FIXED; 1 new finding (fixed)

```
R-046: DIVERGES — SKILL.md:84 and PRD §5 still said S7 is authored at `task start`.
```

Fix: both S7 rows now read "`task design` authors+seals (daemon; new version on `task redesign`); `task end` reveals".

## Round 4 — final

Auditor's closing words: "No new findings. All 54 requirements are now implemented as specified and each is
proven by a selftest, an intent step, or a sealed §6 holdout case."

## Gate outputs observed by the auditor (round 4) and by the builder after the last edit

```
selftest: all guarantees hold (51 ok, 7260ms)
```

```
rulebook fresh: source_sha256 matches
```

```
  decisions: 40 active, 1 superseded
  requirements: 54 in trace, 54 declared in PRD

TRACE: clean (phase design, 40 active decisions all covered)
```

```
[1] rulebook generated from source (never hand-edited)
[2] no python under nemesis scripts
[3] skill md names enforcement
[4] trace gate clean (design phase)
[5] selftest (all guarantees)
[6] oracle: unreadable verdicts never allowed
all nemesis intents hold
```

`bunx tsc --noEmit -p scripts/tsconfig.json` — no output, exit 0.

Build-phase trace before this file was written: `TRACE: 1 hole(s)` — only `R-048: symbol "Audit verdict:
zero findings" not found in prd/AUDIT.md`, which this file closes. The holdout reveal (R-047) is recorded in
the section below once the QA context has run it.

## Notes the auditor recorded without counting them as findings

1. R-011 names an `edit_id` field; the S2 artifact carries `verdict_id` (the edit identity) instead. Acceptance met.
2. R-005's "well under 100 ms" is asserted in the selftest only as `< 5000 ms`; the auditor measured 10–20 ms independently.
3. `verdict.ts` converts an `allow` carrying findings into a `deny` and clamps a recommended rung to 1–6.

Audit verdict: zero findings

## Holdout reveal (R-047) — run once by a separate QA context, 2026-10-08

```
summary: 19/19 passed, 0 failed, 0 inconclusive
deciding case rule-breaking-edit-refused-until-fixed: passed
evidence bundle: holdout/evidence/EVB-HLD-acos-nemesis-protocol-0001-2026-10-08T23-06-45-521Z/bundle.json
revealed_at: 2026-10-08T23:06:45.521Z (pack is now SPENT — it will refuse to run again)
```

`holdout.ts status`: state SPENT, verdict PASS, pack-vs-manifest OK, bundle exists, raw.log integrity OK.
The QA context also found that `trace.ts check --reveal` looked for the bundle relative to the manifest
instead of the candidate root; fixed in `acos-skill-maker/scripts/trace.ts` (accepts both), its selftest passes.
