# Domain Brief — 005-resurrection-protocol
*(Constitutional Domain Compilation, Phase 1: Domain List Generation — §0.2. Source corpus:
`_preseed/` product-context, design, build-plan, vision-deltas, decision-points, digests; swarm report
`swarm-20260714-084532`. RAG unavailable — internal priors are Assumptions from the swarm report + memory.)*

## Domain statement
The problem domain is **durable, verifiable, single-operator project continuity** on one macOS machine
running many concurrent Claude Code + cmux sessions. The core artifact is a **derived-not-stored** per-project
registry ("the book") whose payload is a **generated** `next_action` headline — the one thing no vendor ships.
The design tension is that closing a workspace must FEEL safe (verified zero-loss) while the actual failure
mode is a *force-quit* in which the close ritual never runs. The domain is dominated by one empirical fact:
on this machine, **silent failure is the base rate** — so every claim is delivered as a verified read-back,
never a verdict, and never a green badge.

## Entities
- **The book** — one unified view rendered FRESH per invocation over the sharded store (no persisted master).
- **Project registry row** — `~/.acos/registry.d/<project_uuid>.json`; every field derived/generated.
- **Audit event** — append-only `~/.acos/registry-audit.jsonl`, one `os.write` per line.
- **project-id file** — `<root>/.acos/project-id` (git-ignored); the uuid4 minted once at enrollment.
- **Close handoff** — `memory/handoffs/closed/<slug>/handoff.yaml` (`type: close-project`, `status: parked`).
- **Reentry doc** — `memory/handoffs/closed/<slug>/<slug>.reentry.md` (never `.resume.md`).
- **cmux description tag** — `<next_action> [key:<uuid>]` (tag at END, ~45-char overhead) — the workspace-row join.
- **Daemon stop marker** — `state/stop-<SESSION_ID>`, the ONLY permitted daemon-state write.
- **Evidence bundle** — `.acos/evidence/[DATE]/[SLICE-ID]/` (probe outputs, tamper transcripts, DR-1 recording).

## Processes
- **Enrollment** — SessionStart marker-gated -> derived row; O(1), fail-open; `realpath(cwd)==root` assertion.
- **Safe close** — `/acos-safe-close` thin router over `close-project.sh` steps 0-10; enrich -> verify -> close last.
- **Resurrect menu** — `/acos-resurrect` renders the fresh book; pick focuses/launches; finish verb -> completed.
- **Launch-or-focus** — same-root inline / open-elsewhere focus / not-open launch with verified argv delivery.
- **DR-1 gate** — full cycle on a real project; recording/receipts archived; ship only after it exists.
- **Phase-0 verification** — probe battery + DP2 + prerequisite fixes; the mandatory diagnostic slice.

## Methods (mechanisms)
- Atomic write (`mkstemp`->`fsync(tmp)`->`os.replace`->`fsync(dir)`, one writer per file); per-project sharded JSON.
- uuid4 identity minted once; `realpath.casefold` lookup index; `(st_dev,st_ino)` re-link.
- Marker-gated enrollment; rebuild-from-disk (`rebuild-registry.py`, 16/16 baseline).
- Close steps 0-10; validated `workspace.close` (fail closed); blind round-trip verifier (Wigum cap 5 -> DEGRADE).
- Generated `next_action` headline; verified read-back receipt; facts-not-verdicts rendering.
- Focus-never-launch; live liveness joins (`lsof`/`ps`/`cmux tree`); `[key:<uuid>]` description-tag join.
- Argv reentry delivery + read-screen verification; absolute binary paths; version-control-where-it-executes.
- Co-located `closed/<slug>/` namespace; tombstone-never-delete; append-only audit; Phase-0 probe battery.

## Standards / regulations / best practices
- **POSIX/LWN/SQLite** fsync-before-rename crash durability (T1). **APFS** case-insensitivity -> casefold (T1).
- **JSON fails loudly** (vs YAML silent truncation) (T3). **DP2 sacrificial-test discipline** (T4).
- **SPINE 1-7** (binding internal rules): focus-not-launch; derived/generated only; verified reads;
  code-not-prose; cmux-is-UI; no-recency-selector; daemon-dir-off-limits.
- **Three-agent LCE pattern** (PM/Dev/QA, zero-trust). **T1-T5 evidence-tier model.**
- **Policy constraints:** subscription-only Claude (never `ANTHROPIC_API_KEY`); never modify agent definitions
  or the human-editable reviewer trigger-rules directory; never write top-level `memory/handoffs/*.{md,yaml}`
  or the daemon state dir (except `state/stop-<sid>`); never delete/move `pending-resume-*.txt` /
  `RESCUED-resume-*.txt`.

## Metrics
- Torn/errored write count (6x60->0); unlocked-write silent-survival (3/25); reproduced row count (16/16);
  `listed N of M` (== `git status --porcelain | wc -l`); workspace-count-constant; dangling-pointer rate (->0);
  adoption at day 60 (~30% baseline); `next_action` <=90 chars; Wigum cap (5); DR-1 round-trip achieved;
  silent-failure base rate; daemon-dir write count (==1); CQ coverage (>=95%); delivery-marker verification;
  Phase-0 probe pass count; PATH-shadow count (2).
- Governance formulas (§0.5): `QAP=(Delivered_Value*Quality_Score)/(1+Rejection_Count)`; TER=artifacts/1K tokens;
  `UAPS=0.3*Quality+0.4*Efficiency+0.3*CostEffectiveness`. Instrumentation -> `.acos/metrics/agent-completions.log`
  + `~/.acos/registry-audit.jsonl`.

## Risks
- Adoption decay (~30% day-60); `next_action` generation quality (highest-risk dependency); cmux 0.64.x
  behavior UNVERIFIED; Eternity cross-contamination; in-pane hook regression (#5427); silent-failure base rate;
  trust death (one silent loss); duplicate launch -> cross-pane contamination (residual #10); auto-naming
  confidentiality (OKOA content).

## Anti-patterns (explicitly killed, with the evidence)
- Shared mutable master file (3/25 valid-but-wrong); YAML silent truncation (19/30); SQLite opaque to git;
  rows created by closing (empty at force-quit, DR-8); naive filesystem-scan membership; green badge (false
  green = trust death); recency-as-selector; `identify --surface` fail-open; `cmux send`/`surface.send_text`
  newline shred; `sanitize(cwd)` identity (non-injective); auto-stash at close; notifier/nagger.

## Key terms
- **`project_uuid`** — uuid4 minted once at enrollment; the canonical identity.
- **`next_action`** — the generated <=90-char imperative resume headline.
- **force-quit** — killing cmux/Warp without a clean close (files survive; uncaptured reasoning dies).
- **Wigum loop** — bounded adversarial retry (cap 5) then DEGRADE.
- **SPINE** — the seven binding design rules. **LCE** — Lean Context Engineering (single narrow objective + DoD).
- **pane-durable vs pane-independent** — Eternity (same-pane) vs Resurrection (cross-window). Opposite invariants.
