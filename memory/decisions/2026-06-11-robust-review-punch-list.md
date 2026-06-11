# ACOS Robust Review — Punch-List (Design/Efficiency — NOT auto-applied)

These are NOT bugs. They are design, efficiency, robustness, or contract-uncertainty
items collected during the robust-review loop. Per the agreed fix policy, they require
your approval before any change. Outright bugs were auto-fixed in the loop.

Session: 20260611-032000

---

## Subsystem 1 — hooks + .claude/scripts

### S1-P1 — Independence-wall guard over-broad substring match (HIGH-value, recommend approve)
`block-review-rules-read.sh` matches the literal substring `review-rules` anywhere in a
Bash command line, so benign commands (an `ls`/`find`/syntax-sweep over the repo that merely
*mentions* the path, e.g. this very review's verification loop) are blocked even when not
reading the protected directory. Verified live: my own `bash -n` sweep was blocked because the
command contained the script's own filename.
- Proposed: narrow the Bash matcher to resolve the actual referenced path and check it is under
  `review-rules/`, rather than substring-matching the whole command line. Keep fail-closed semantics.
- Risk if changed: low; must preserve the wall's fail-closed guarantee.

### S1-P2 — AskUserQuestion updatedInput schema unverified (contract-uncertainty)
`autopilot-askuserquestion-handler.py:117` builds `updatedInput = {"questions": questions,
"answers": {<question_text>: <label-without-(Recommended)>}}`. The exact Claude Code
AskUserQuestion `updatedInput` contract (key by question text vs header vs index; whether the
option label must retain its exact original text) is NOT documented in the repo. If the schema
is wrong the auto-pick silently fails and the harness falls back to prompting (fail-open, no harm),
but unattended autopilot would stall on questions.
- Proposed: verify the live updatedInput schema against the installed Claude Code version, then
  align keys/labels. NOT blind-fixed because a wrong change could break a currently-working path.

### S1-P3 — token-gate.sh / context-monitor / claude-loop handoff format coverage (partially addressed)
The `.md` handoff coverage was fixed in context-monitor.sh, claude-loop.sh, fallback-to-opencode.sh,
archive-project.sh. token-gate.sh still globs only `*.yaml`/`*.yml` for its session-handoff freshness
detection (lines ~257, ~408). Not a crash — a staleness false-negative that could re-press the user
after they created a markdown handoff.
- Proposed: add `*.md` to token-gate.sh handoff globs and parse session_id from md front-matter.
- Deferred (not a hard bug; consistency improvement) — recommend approve for coherence.

### S1-P4 — CLAUDE.md vs settings.local.json hook-registration drift (docs/integration coherence)
CLAUDE.md documents token-gate.sh (PreToolUse, 130k ceiling), context-monitor.sh (Stop), and
context-watchdog.sh (PreCompact) as ACTIVE hooks, and describes ordering as "Oracle -> check-scope
-> execute". In `settings.local.json`: there is NO token-gate.sh entry, NO PreCompact entry, the
Stop hook runs `autopilot-stop-handler.py` (not context-monitor.sh), and the PreToolUse array has
five hooks (Oracle, check-scope, autopilot-askuserquestion, block-review-rules-read, autopilot-allow-extra-tools)
not the documented three-stage description. Either the docs are stale or the handoff hooks live in
a different settings file (e.g. user-global `~/.claude/settings.json`).
- Proposed: reconcile CLAUDE.md with the actual registered hooks, OR register the missing hooks if
  they are intended to be active. This is a coherence decision for you — it affects whether the
  documented handoff/token-gate behavior actually fires from this project.

### S1-P5 — Over-fetch / dedup tuning in RAG querier (addressed; note for awareness)
The double over-fetch (querier 2x + db.search 2x = 4x) was consolidated into a single layer sized
for `max_per_file`. No further action needed unless you want to tune `MAX_PER_FILE` (currently 3)
or the over-fetch margin.
- Note: the cosine-metric fix assumes the vector DB is (re-)indexed under the cosine metric. Current
  code uses brute-force search (no ANN index), so it applies cleanly; if an ANN index is added later
  it must be built with `metric="cosine"`.

### S1-P6 — Minor robustness / cosmetic (low priority, batch-approve candidates)
- `validate-evidence.sh:57` — `find ... -name $SLICE_ID | head -1` returns an arbitrary (first-by-
  traversal, not newest) match when a SLICE-ID exists under multiple dates; sort by date desc.
- `validate-evidence.sh:144` — completeness checks rely on literal placeholder-token greps
  (`grep -q TODO`, `grep -q YES` matches anywhere); could pass with blank-but-non-placeholder content.
- `post-write-evidence.sh:5` — logs to fixed `.acos/evidence/current/modifications.log` which is never
  promoted into the slice bundle's `after/modified-files.txt`; PostToolUse trail is disconnected from
  the validated bundle. Wire a promotion step or parameterize.
- `create-evidence-bundle.sh:136` — next-steps text references `./capture-evidence.sh` (stale; the
  validator is `validate-evidence.sh`).
- `data-to-pptx.py auto_fit_font` (~line 384) — per-run vs whole-shape font reduction produces
  non-uniform font sizes within one box; intentionally left untouched this pass (compute a single
  whole-shape scale factor instead).
- `data-to-pptx.py:1057` — unknown slide types warn-and-skip but exit 0; a calling pipeline can't
  detect an all-typo spec producing an empty deck.
- `check-scope-bash.sh:68` — redirection regex misses the `>|` clobber operator (self-declared
  "NOT airtight / defense-in-depth").
- `validate-pptx.py` / `data-to-pptx.py` — `detect_font_role` is duplicated with a "must match exactly"
  comment but no parity test; extract to a shared module or add a parity test.
- `render-doc-audit.py` overflow line-height multiplier (1.2) disagrees with check-pptx-layout.py (1.4);
  align so the two tools don't contradict on the same deck.
- `check-pptx-layout.py:145` — overlap severity uses `max(x_overlap, y_overlap)`; minimum-translation
  separation is the `min` axis — grazing slivers over-graded as ERROR with nonsensical fix suggestions.
- `rag-index.sh` uses `set -euo pipefail` (with -e) while `rag-query.sh` uses `set -uo pipefail`
  (without -e) — standardize per the documented convention.
- `grader-cohort-curve.py:840` — per-student XLSX reuses col 4 for both the wide Reasoning column and
  a narrow audit column; openpyxl keeps the last-set width, narrowing Reasoning.

### S1-P7 — RAG cosine score baseline shift (needs your call — added Round 2)
The Round-1 fix switched the RAG similarity to a cosine metric. With cosine, an unrelated/orthogonal
chunk scores ~0.5 (not ~0), because `score = (1 + cos_sim)/2`. A caller-supplied `min_score` tuned
against an intuitive 0=irrelevant scale will behave more permissively than expected (0.5 = orthogonal
baseline). Not a crash — a semantics question.
- Proposed: either expose `score = cos_sim` (range ~[0,1], 0=orthogonal) so min_score is intuitive, OR
  document the 0.5=orthogonal baseline so callers set min_score accordingly. Your preference on the
  threshold convention drives the choice.

### S1-P8 — Out-of-repo daemon parallel bug (flagged, not fixed — added Round 2)
`~/Library/Application Support/acos-token-monitor/bin/register-session-pid.sh` carries the SAME
`*"/claude"*` PID-walk pattern that was just fixed in `eternity-resume-prepend.sh` (it would match
`claude-loop.sh` and resolve to the wrapper PID instead of the real claude PID). That file is in the
user-global daemon directory, OUTSIDE this repo, so it was not touched by this review.
- Proposed: apply the same `*claude-loop*) ;;` exclusion + end-anchored `*/claude` match there.
  Requires editing outside the repo — separate approval.

### S1-P9 — Additional low-priority items (added Round 2, batch-approve candidates)
- `validate-evidence.sh` — completeness `grep -q TODO` over whole Summary.md false-triggers on a
  legitimate prose mention of "TODO"; match the template placeholder more specifically.
- `run-quality-gates.sh` — a required stage-less gate now runs once per stage filter (the fix made it
  fall through); for N stages it executes N times. Acceptable, but scope to a single canonical stage
  or document it.
- `check-pptx-layout.py` — unused module constant `MARGIN_RIGHT_LIMIT` and unused imports
  (`math`, `collections.defaultdict`); remove.
- `render-doc-audit.py` — overflow line-height multiplier (1.2) disagrees with check-pptx-layout (1.4);
  coarse heuristic, but the two tools can disagree on the same deck.
- `autopilot-askuserquestion-handler.py` — `from datetime import ...` inside `main()` (style; move to top).
- `autopilot-stop-handler.py` — `read_transcript_tail` 400-line cap is a best-effort boundary on
  idle-detection during very heavy-tool turns (fail-open, low impact); a per-turn sentinel marker would
  be more robust than transcript reconstruction.
- `data-to-pptx.py:97` — malformed slide_width/height silently swallowed (bare except pass); warn to
  stderr like the colors path does, for diagnosability.

## Subsystem 2 — core/framework agents (.claude/agents/*.md, 10 core agents)

Round 1 swarm: 3 reviewers (1 qa + 2 integration) over the 10 core agents. Outright instruction
bugs were auto-fixed in the loop (see commit). The items below are design decisions left for your call.

### S2-P1 — general-purpose agent lacks `Edit` (design decision)
`general-purpose.md` grants `tools: Read, Write, Glob, Grep, Bash` but its description says it does
"data extraction, compilation, and review tasks within orchestrated pipelines." It has no `Edit`. If any
orchestrator (data-extractor, dataroom-v2, grader families) ever instructs a general-purpose worker to
modify a file IN PLACE, the Edit call is unavailable and the worker would fail or fall back to a
full-rewrite Write (clobbering). Currently every pipeline that needs in-place edits spawns a more
specific agent, so this may be intentional (GP = create/overwrite only).
- Proposed (only if a pipeline needs it): add `Edit` to general-purpose's tools list.
- Risk: low; broadens GP's mutation surface. Recommend verifying against actual pipeline prompts before changing.

### S2-P2 — architect's per-agent block-review guard is redundant with the global hook (design/coherence)
The architect declares a per-agent PreToolUse hook for the independence-wall guard script. The global
`settings.local.json` already registers that same script for ALL agents (matcher `Read|Bash|Grep|Glob`).
The per-agent block is therefore redundant — the script runs twice on Read/Bash calls for the architect.
Round 1 auto-fix ALIGNED the per-agent matcher to `Read|Bash|Grep|Glob` (it was the narrower `Read|Bash`,
which misrepresented the enforced surface), so there is no longer a coverage-impression gap. The remaining
question is purely whether to KEEP the (now-aligned but redundant) per-agent declaration as documentation,
or REMOVE it to avoid the double-run and single-source the guard in settings.local.json.
- Proposed: remove the per-agent hook block from architect.md frontmatter (global registration already
  covers all agents), OR keep it as intentional belt-and-suspenders. Your call — both are correct at runtime.

## Subsystem 3 — orchestration / lifecycle / methodology skills (.claude/skills/*)

Round 1 swarm: 9 reviewers (R1-A…R1-I) over the Subsystem-3 skill families. Outright bugs were
auto-fixed in the loop (see commit). The items below are design / contract-uncertainty decisions
left for your call.

### S3-P1 — Handoff EMIT-format unification (.yaml vs .md) — design decision, NOT drift
Following the Subsystem-2 precedent (emitters writing `.yaml` are NOT drift because readers now glob
both), this pass fixed only the `.yaml`-only READER skills (acos-complete Steps 2/4/5, acos-resume-prompt
Step 1) to glob `*.md`+`*.yaml` and exclude `*.resume.md`. Two handoff EMITTERS still write `.yaml`:
- `acos-complete` Step 3 creates the completion handoff as `…-completion-handoff.yaml` (R1-B LOW).
- `acos-handoff-protocol` Step 3 writes `…-session-handoff.yaml` (R1-D MEDIUM) while the global
  `acos-handoff` skill delegates to handoff-agent and emits `.md`. The two handoff skills have diverged.
- **Proposed (your call):** pick ONE canonical emit format (`.md`, matching handoff-agent) and one emitter,
  OR explicitly bless `.yaml` as a legacy format the both-format globs still accept. Not blind-fixed because
  changing emit format is a contract decision, and both formats are currently read correctly.

### S3-P2 — `acos-handoff` vs `acos-handoff-protocol` skill-name reference (portability) — R1-D LOW
The eternity skills (cmux Step 1 ~line 173; warp Step 1 ~line 112) invoke the **global** `acos-handoff`
skill via the `Skill` tool. No in-repo skill is named `acos-handoff` (the in-repo one is
`acos-handoff-protocol`). Functionally correct in this user's environment (global skill exists, emits `.md`),
but a project that embeds ACOS skills WITHOUT the global `acos-handoff` installed would fail to resolve it.
- **Proposed:** document `acos-handoff` (global) as an explicit dependency of the eternity protocol, OR
  point the eternity skills at the in-repo `acos-handoff-protocol` (after reconciling its emit format per S3-P1).

### S3-P3 — `acos-resume-prompt` "auto-injection" framing is cmux-only (warp-stale) — R1-D LOW
The description + Step 3 body say the resume prompt is "auto-injected after /clear". True for the cmux variant
(daemon RPC), but Warp auto-injection was disabled 2026-06-04 (manual-only; AXTitle race). The file is shared
across both variants.
- **Proposed:** qualify the wording — auto-injection applies to cmux; for Warp the prompt is delivered by the
  manually-invoked `/acos-eternity-protocol-resume`. Doc-only; deferred to keep this pass to outright bugs.

### S3-P4 — `acos-add-skills` lists `acos-create-skill` as addable, but it is global-only — R1-E LOW
`acos-add-skills` Step 2 "Meta" category lists `acos-create-skill` as addable via `add-skills.sh`, but that
script enumerates from the in-repo `.claude/skills/`, where `acos-create-skill` does NOT exist (it is a global
standalone). The Step-1 loop never surfaces it and `add-skills.sh acos-create-skill` would find no source dir.
- **Proposed:** remove it from the addable catalog or annotate "already global — not addable here". Doc-only.

### S3-P5 — `Agent`-in-allowed-tools propagated to 4 out-of-subsystem skills — R1-E MEDIUM (evidence)
The bad skill-maker guidance (now fixed) had already propagated `Agent` into the `allowed-tools` frontmatter of
four skills NOT in this subsystem's reviewer scope: `acos-data-extractor`, `acos-legal-analysis`,
`acos-pdf-xlsx-converter`, `acos-electronics-repair`. `Agent` is not a valid `allowed-tools` value (no-op;
misleads readers). Left untouched to respect subsystem boundaries — clean batch-approve cleanup.
- **Proposed:** remove `Agent` from those four frontmatters (Task() comes from the invoking agent's context).

### S3-P6 — `acos-oracle-protocol` Quick Preset Details table omits `default` row — R1-E TRIVIAL
Cosmetic: the preset table (lines ~192-198) omits the `default | 9` row present in the Phase-2 list and
threshold reference. All six presets are correct elsewhere. Optional cosmetic add.

### S3-P7 — Portable-skill teaching snippets fail strict TS (illustrative) — R1-G TRIVIAL
`backend-coding` (validateRequest double-wrap example; untyped errorHandler params) and `frontend-coding`
(untyped tsx handlers) snippets are illustrative pseudo-code that would not compile under strict TS. Harmless
as teaching material. Optional: add minimal types or mark snippets as illustrative.

## S1-P31 — check-scope-bash.sh: shlex-aware write-target tokenization (late-arriving reviewer finding)
- **Source:** G1 reviewer (completed after Subsystem 1 convergence pass)
- **Issue:** Target-token regexes split on whitespace, so quoted write targets with spaces — including ANY path under this repo root ("ACOS 3.0" contains a space) — truncate at the first space, get classified outside-repo, and the out-of-scope write is silently allowed.
- **Interim mitigation applied:** limitation documented in the script header (commit pending).
- **Proposed fix:** tokenize the command with shlex (honoring quotes/escapes) before write-target extraction, falling back to the current regexes on shlex failure. Design change to guard behavior → needs approval.

## S3-P8 — Should /acos-complete actively invalidate outstanding eternity resume pointers?
- **Source:** S3 Round-3 contract sweep (R3-B, MEDIUM).
- **Context:** /acos-complete (clean break) and the eternity resume path (continuation) encode opposing intents. Interim BUG FIX applied: archiving now rewrites the preserved .resume.md sibling's embedded handoff path to the archive/ location, so a later resume still works.
- **Open design call:** should completing a milestone instead CONSUME the per-PID pointer + sibling (option a — a completed milestone can never be half-resumed), or is resume-after-complete legitimate (current behavior, option b)? Conflicts with the standing "never delete pending-resume files" rule if option a is chosen.

---

## Subsystem 4 — domain skill families + their agents

Round 1 swarm: 10 reviewers (R1-A…R1-J) over the 14 in-repo S4 skills + 30 agents. 134 findings.
Outright bugs were auto-fixed in the loop (see commits). The items below are design / contract
decisions left for your call.

### S4-P1 — dataroom-v2 dedup "special mode" needs a real agent contract (R1-B HIGH, design)
SKILL.md §9.5.2 spawns `dr2-inclusion-deliberator` x3 in a "dedup-canonical mode" requiring output
`{canonical_filename, exclude_filenames, reasoning, confidence}`, but the agent implements only the
per-file INCLUDE/EXCLUDE relevance schema — it has no dedup mode, and `consensus_check.py` has no dedup
helper. The loop-side bug (consensus_check inclusion rule) was auto-fixed; this is the deeper design gap.
- **Proposed:** add an explicit "Dedup-canonical mode" section + alternate output schema to
  dr2-inclusion-deliberator.md (gated on a prompt flag), OR create a dedicated dr2-dedup-classifier agent;
  then add a dedup branch to consensus_check.py. Design because it changes an agent's contract surface.

### S4-P2 — dr2 reviewer/deliberator agents carry unused `Bash` tool (R1-B LOW, design)
dr2-inclusion-qa, dr2-inclusion-deliberator, dr2-placement-qa, dr2-description-qa, dr2-guide-qa declare
`Bash` but their procedures only Read inputs and Write one JSON verdict — no bash step. Over-broad tool
grant. Left unfixed (tightening agent tool surfaces is a deliberate least-privilege decision, not an
outright bug).
- **Proposed:** drop `Bash` from these read/write-only agents (keep Read, Write, +Glob where dir-listing
  is needed). Verify against any future bash step first.

### S4-P3 — dataroom-v2 final-report split counts have no defined source (R1-B LOW, design)
§14 prints "Excluded by Phase 2 categorical fast path" vs "Excluded by Phase 2 asymmetric veto" as
separate counts, but the skill never specifies partitioning exclusion_log.csv by reason_code to derive
them. Either specify the partition (on reason_code categorical_exclusion:* vs relevance/borderline) or
collapse to a single "Excluded by Phase 2" count.

### S4-P4 — loan-doc-phase34 PPTX output carve-out (R1-D LOW, design)
phase34 agent + phase3 Step 3.5b say "Generate BOTH PDF and DOCX, place ONLY .pdf and .docx in output/",
with no carve-out for PPTX document types (which produce a .pptx and no PDF/DOCX). Add a PPTX carve-out to
the phase34 finalization rule. Design because it changes the agent's output contract.

### S4-P5 — loan-doc-finder/mapper design items (R1-E, design)
- finder: orphan `templates/final-report.md` + `templates/qa-review.yaml` diverge from the inlined
  DOCUMENT_REPORT.md / qa-synthesis schemas — wire them in or delete them.
- finder: documented "Confidence threshold: medium" gate is never enforced in Phase 2 (low-confidence
  matches still copied) — implement the filter or remove the config row.
- mapper: `disable-model-invocation: false` lets Claude auto-trigger a high-stakes zero-fabrication
  pipeline; finder correctly uses `true`. Consider setting mapper to `true`.
- mapper: documented "model resolution fails → hardcoded defaults" fallback is not wired
  (`MODEL=${MODEL:-sonnet}` guard absent).
- cross-skill session-status enum drift (in-progress vs in_progress; PASS_WITH_WARNINGS vs spaces).

### S4-P6 — fin-stmt reconciliation design items (R1-F, design)
- stuck-loop branch (phase2 Step 7) adds feedback but has no independent terminating effect; should
  explicitly fall through to "proceed with best available" on max_iterations (the control-flow BUG —
  Step 6 skipping the Step 7 gate — was auto-fixed; this is the residual wording).
- 2-sandbox degraded mode lacks an explicit finalization rule (2/3 majority is undefined with 2 sandboxes).
- optional investigative-reviewer (4.3) is a soft number-leak vector with no mechanical barrier; add an
  explicit "feedback must not encode the reviewer's computed value" rule.
- accountant agent's Projection Mode bullet doesn't mention the "reserve 1 iteration for synthesis" rule.
- `generate-xlsx-financial.py` missing; inline xlsxwriter fallback exists but is a vague stub — ship the
  script or make the inline path a concrete runnable skeleton.

### S4-P7 — data-extractor / pdf-xlsx design items (R1-G, design)
- data-extractor token-budget comment/formula mismatch (narrative describes a cost-function/optimal-N
  derivation; code takes smallest-feasible-N); redundant inner MIN_AGENTS in clamp.
- data-extractor default session path not aligned with framework `.acos/evidence` convention (standalone
  skill, may be intentional).
- pdf-xlsx-converter: hard `openpyxl` pip dependency with no graceful-degradation hint; temp generation
  script path never specified (Phase 3 writes, Phase 6 cleans an undefined path).

### S4-P8 — legal-analysis / electronics design items (R1-H, design)
- legal: Phase 5 renders via `/tmp/render-ic-memo.js` (volatile, never shipped); reuse html-to-pdf.js or
  ship a committed render helper.
- electronics: orphan `reference/svg-template.svg` (unused + contradicts the SKILL's light-background
  spec); asymmetric template coverage (block-diagram.yaml / visual-inspection.yaml have no scaffold);
  stray `references/` (plural) dir holding an unrelated TI app-note PDF next to the cited `reference/`
  (singular) dir — confusing near-duplicate naming.

### S4-P9 — type-forge legacy per-tool servers (R1-I, design)
serve.sh/serve.py (port 8787) + spacing.sh/spacing_serve.py (port 8790) are superseded by the unified
typeforge.sh (:8800) and diverge from its contract (different endpoints; `spacingfont.woff2` vs
`font.woff2`). Remove them or clearly mark deprecated. (The stale SKILL.md gotcha pointing at serve.sh,
and proof.sh referencing a nonexistent proof.html, were auto-fixed as bugs.)

### S4-P11 — acos-preflight.sh still requires removed `context-monitor.sh` hook (R1-E MEDIUM, cross-subsystem)
- **Source:** R1-E (loan-doc-mapper reviewer), but the defect lives in the SHARED `.claude/scripts/acos-preflight.sh:24`, an already-converged Subsystem-1 file.
- **Issue:** the HOOKS_OK completeness check greps for `context-monitor.sh` as a required hook. Per current reality the Stop hook is `autopilot-stop-handler.py`. On projects migrated to the new Stop handler, preflight's fast-exit fails and it re-runs full `bootstrap --force` on EVERY skill invocation instead of the intended <1ms idempotent exit. Every S4 skill that calls preflight is affected (mapper is the named in-scope caller).
- **Why deferred, not auto-fixed:** editing acos-preflight.sh re-opens a Subsystem-1-converged file mid-Subsystem-4; same handling class as S1-P31 (late-arriving reviewer finding against a converged S1 file). Recommend folding into a short S1 re-touch.
- **Proposed fix:** change the required-hook loop to accept `autopilot-stop-handler.py` OR `context-monitor.sh` (the project may register either as its Stop hook), so the idempotent fast-exit works on migrated projects.

### S4-P10 — ultimate-designer style/robustness items (R1-J, design)
- bootstrap-manifest.py computes file_hash twice per file (build_entry + main overwrite) — pass the
  precomputed hash in.
- `dt.datetime.utcnow()` deprecated (bootstrap-manifest.py + wigum-loop.py) — use timezone-aware now().
- (The real api-key/contract/snippet bugs in this skill were auto-fixed.)

---

## Subsystem 5 — .acos/ config + cross-cutting closure (CONVERGED Round 5, zero findings)

**Target:** `.acos/config/*` (project.yaml, oracle.yaml, model-profile.yaml, providers.yaml,
quality-gates.yaml, eternity-protocol.yaml, known-design-choices.md) audited against their real
consumers, PLUS the factual resolution of the S1-P4 hook-registration drift and closure of S4-P11.
**Rounds:** 5 (converged — Round 5 both reviewers PASS, zero findings at any severity).
**Fix policy:** ALL Subsystem-5 findings were outright bugs / factual doc-drift and were auto-fixed
in the loop. **No design items were deferred — the S5 punch-list is empty.**

### CLOSED by Subsystem 5 (previously deferred):

- **S1-P4 — RESOLVED (was: CLAUDE.md vs settings hook-registration drift).** Determined factually:
  the legacy handoff trio (`context-monitor.sh`/`context-watchdog.sh`/`token-gate.sh`) was
  superseded by the autopilot architecture and was registered in NO project/global-`settings.json`
  layer — but a stale pre-autopilot `hooks` block in the user-global `~/.claude/settings.local.json`
  (2026-04-25, using the removed `git rev-parse` pattern) still registered all three, causing
  duplicate Stop + PreToolUse firing. Fixed the wrong side: removed that stale hooks block; rewrote
  CLAUDE.md "Handoff & Continuation System" + Oracle hook-ordering to autopilot reality; added
  LEGACY/UNREGISTERED banners to the three orphan scripts; corrected the now-false anti-oscillation
  note in `known-design-choices.md`.
- **S4-P11 — RESOLVED (was: acos-preflight.sh requires removed context-monitor.sh hook).** The
  hook-completeness check forced a non-converging `bootstrap --force` on every skill invocation
  because it grepped for the unregistered `token-gate.sh`+`context-monitor.sh`. Rewired to check the
  real autopilot hook set (oracle-evaluate.py, check-scope.sh, block-review-rules-read.sh,
  autopilot-stop-handler.py) across all three settings files; fixed the wrong global-settings path
  (`settings.local.json` → also `settings.json`). Verified: preflight now exits 0 cleanly.

### S5 design items: NONE.
All eleven Round-1 findings (1 CRITICAL, 4 HIGH, 3 MEDIUM, 3 LOW) plus the Round-2 settings-trio
regression, two Round-3 trivials, and one Round-4 coherence finding were factual bugs/doc-drift,
auto-fixed and re-verified to zero. Nothing in Subsystem 5 requires user approval.
