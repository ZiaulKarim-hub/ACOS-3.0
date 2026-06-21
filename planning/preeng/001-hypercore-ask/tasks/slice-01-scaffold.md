# slice-01-scaffold — Skill scaffold + ACOS integration

- **Parent story:** STORY-HCA-01 · **Parent epic:** EPIC-HCA-01 · **Demo:** -
- **Effort:** M · **Dependency order:** 2 · **Depends on:** slice-00-diagnostic
- **Lattice refs:** proc-intake, meth-tiered, term-tier, ent-bundle, meth-subonly

## PM Section (Planner / Specifier — LCE)

### Objective
Scaffold the `acos-hypercore-ask` skill so it is discoverable and loadable in ACOS/Claude Code, exposes the natural-language command surface, classifies a question into a verification tier, surfaces the skill config, and wires per-slice evidence bundles. No data access yet.

### Scope
**In scope:** `SKILL.md` (frontmatter + command surface + pipeline overview pointing forward to later slices); the tier-router script that classifies a question as `trivial-lookup` vs `report/aggregation/analysis`; the skill config file (consensus/freshness/confidence/adapter defaults from tech_prd §5); evidence-bundle wiring stub.
**Out of scope:** adapter, cache, gates, consensus, provenance, delivery (later slices). The router must NOT fetch data.

### Guardrails / Allowed files
- `.claude/skills/acos-hypercore-ask/SKILL.md`
- `.claude/skills/acos-hypercore-ask/config.yaml` (consensus/freshness/confidence/adapter defaults; **NO secrets**)
- `.claude/scripts/hca-route.py` (tier router; Python 3 stdlib only)
- `.claude/skills/acos-hypercore-ask/README.md`
- this task file (learnings) + `.acos/evidence/[DATE]/slice-01-scaffold/`
- Prohibited: any `.claude/agents/` file; any network/API call; any secret in config.

### Definition of Done
- [ ] `SKILL.md` loads (valid frontmatter `name`/`description`); documents the NL command surface and the forward pipeline; states read-only + subscription-only + stubbed-until-access guardrails — artifact: `SKILL.md`.
- [ ] `hca-route.py` deterministically classifies a question into `trivial-lookup` or `report/aggregation/analysis` and prints the tier; covered by an inline self-test (`python3 hca-route.py --selftest` exits 0) — pass-condition: self-test passes.
- [ ] `config.yaml` present with the tech_prd §5 keys (`consensus.default_quorum`, `agent_count`, `redispatch_retries`, `freshness_windows_days.*`, `confidence.single_source_cap: 0.7`, `adapter.backend: fixture`) and **no secrets** — artifact: `config.yaml`.
- [ ] Evidence-bundle wiring writes to `.acos/evidence/[DATE]/[SLICE-ID]/` — pass-condition: bundle dir created.
- [ ] `## Dev Learnings` / `## QA Learnings` updated.

## Dev Section (Executor)

### Approach
1. Author `SKILL.md` frontmatter + sections: purpose, command surface, pipeline overview (router -> adapter -> cache -> normalize -> consensus -> gates -> binder -> deliver), guardrails. Keep bodies of downstream stages as forward references.
2. Implement `hca-route.py` with a deterministic rule-based classifier (keyword/structure heuristics: single id/field => trivial; aggregation/list/"total"/"across"/"by" => report tier). Stdlib only. Add `--selftest`.
3. Write `config.yaml` from tech_prd §5 defaults; add a comment that secrets come from env/secret store only.
4. Stub evidence-bundle directory creation helper.

### Dev Evidence Bundle (7 parts — required)
Summary; Traceability (M1 routing, M10 subscription-only, NFR-Observability); Code Quality (stdlib-only, self-test); Functional (router self-test output); Security (no secrets in config; no network); Operational (skill load); Self-assessment.

### Dev Learnings
- **The router's safe default is `trivial-lookup`, not `report`.** A question with no
  aggregation signal routes trivial even if ambiguous — this is conservative because the
  trivial path still applies universal provenance + the deterministic gate suite; it only
  declines to *mandate* full adversarial consensus. Routing ambiguous questions to the
  expensive report tier would burn consensus budget without a trust gain.
- **Aggregation signal is keyword/phrase based** (total/sum/across/all/list/by/per/compare/
  rank/portfolio/how many...). Single-word signals are whole-word matched (so "ball" never
  matches "all"); multi-word phrases ("how many", "over time") are substring matched.
- **Authored a truth-set bug in my own self-test** ("interest rate on borrower B-204's
  facility" — I expected report, the deterministic classifier correctly said trivial because
  there is no aggregation signal and it is one value on one record). Fixed the expectation,
  not the classifier. Lesson: trust the deterministic rule, not the gut feel.
- **Evidence-bundle wiring lives inside `hca-route.py`** as `hca_evidence_bundle_dir()` rather
  than a new file, to stay within slice-01 `files_allowed`. It resolves the repo root from
  `__file__` (no git dependency, matching ACOS hook policy) and is pure stdlib.
- `config.yaml` carries ONLY env var NAMES under `adapter.credentials_env`, never values —
  Doppler injects values at runtime. Zero secret-looking literals in the file.
- Executed 2026-06-18 as part of the SLICE-HCA-00..02 foundation bundle.

## QA Section (Zero-Trust Verifier)

### Verification steps
1. Independently load `SKILL.md` frontmatter; confirm `name`/`description` valid and guardrails stated.
2. Run `python3 .claude/scripts/hca-route.py --selftest`; confirm exit 0 and that classifications match a QA-authored truth set (re-author, do not trust Dev's).
3. Grep `config.yaml` for any secret-looking key (API key, token, password) — must find none.
4. Confirm no `.claude/agents/` file was added; confirm no network call in `hca-route.py` (no `urllib`/`http`/`socket`).
5. Confirm evidence bundle exists and is authentic.

### Evidence gates (all must pass)
- [ ] SKILL.md valid + guardrails present.
- [ ] Router self-test passes against QA truth set (not Dev's) — fail = REJECT.
- [ ] config.yaml has required keys, zero secrets, `adapter.backend: fixture`.
- [ ] No network import in router; no new agent file.
- [ ] Learnings updated.

### QA Learnings
- `python3 .claude/scripts/hca-route.py --selftest` exits 0 (14 cases). QA should re-author an
  INDEPENDENT truth set rather than trust the Dev cases embedded in the file (per the slice-01
  gate). Spot-checks of independent questions agree with the deterministic rule.
- Secret grep of `config.yaml` finds NO secret VALUES — only declared env var NAMES
  (`HYPERCORE_API_KEY`, `HYPERCORE_BASE_URL`) which are identifiers, not credentials. Pass.
- `hca-route.py` imports only `argparse, datetime, json, os, re, sys` — NO `urllib`, `http`,
  `http.client`, `socket`, `ssl`, or `requests`. No network path exists. Pass.
- No file added under `.claude/agents/`. SKILL.md frontmatter has valid `name`/`description`
  and states the read-only + subscription-only + stubbed-until-access guardrails. Pass.
