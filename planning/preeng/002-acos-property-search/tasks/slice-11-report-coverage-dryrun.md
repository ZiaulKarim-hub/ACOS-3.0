# slice-11-report-coverage-dryrun — Report + coverage/limits footer + dry-run hardening (Demo 3)

- **Parent story:** STORY-APS-11 · **Parent epic:** EPIC-APS-11 · **Demo:** Demo 3
- **Effort:** M · **Dependency order:** 12 · **Depends on:** slice-10-equity-rollup
- **Lattice refs:** cq-15, cq-16, cq-18, ent-reportv1, meth-hedged, std-hedged, metric-fpr, metric-channelcov, metric-prunect, risk-licensing, proc-audit

## PM Section (Planner / Specifier — LCE)

### Objective
Render the full **Markdown dossier** and harden the pipeline with a **real-name dry run**. The dossier:
**compliance header → High-confidence tier → Candidate tier → per-parcel** `{APN, county/state, situs,
owner-of-record, mailing, matched-through evidence chain, confidence score + signals, per-record freshness,
source URLs}` **→ estimated portfolio value / debt / equity → "Coverage & limits" footer** (counties
searched, hops reached, hubs pruned, stated limitations incl. licensing-out-of-scope) **→ manual-review
flags**, with **hedged language** throughout. The dry run probes **real portal availability** and the
**false-positive rate at the 75/50 cutoffs**, validates the audit trail, and re-validates H1/H2/H3.

### Scope
**In scope:** the report renderer in `SKILL.md` (assembling slice-09 scores + slice-10 equity + flags +
coverage stats); the coverage/limits footer; a documented dry-run procedure + its findings; tuning notes
for the cutoffs.
**Out of scope:** the v2 loan-doc visual render; `/schedule` monitoring; channels 5-9.

### Guardrails / Allowed files
- `.claude/skills/acos-property-search/SKILL.md` (report-render + coverage-footer section)
- `.claude/skills/acos-property-search/scripts/tests/test_report.py`
- this task file + `.acos/evidence/[DATE]/slice-11-report-coverage-dryrun/`
- Prohibited: un-hedged language; omitting the coverage/limits footer; presenting estimates as AVMs;
  claiming nationwide licensing coverage (it is out of scope and must be stated).

### Definition of Done
- [ ] The dossier renders all required sections (compliance header → tiers → per-parcel chain → estimated portfolio → coverage/limits footer → review flags) — pass-condition: structure test.
- [ ] Hedged language is used throughout; "owns" only with direct title support — pass-condition: **hedged-language test (REQUIRED)**.
- [ ] The coverage/limits footer reports counties searched, hops reached, hubs pruned, and stated limitations (incl. licensing-out-of-scope) — pass-condition: **coverage-footer test (REQUIRED)**.
- [ ] Per-record freshness + source URLs appear on every parcel — pass-condition: provenance/freshness test.
- [ ] A documented real-name dry run records portal availability + the false-positive rate at 75/50 and re-validates H1/H2/H3 — pass-condition: dry-run findings recorded.
- [ ] `## Dev Learnings` / `## QA Learnings` updated.

## Dev Section (Executor)

### Approach
1. Implement the renderer assembling scores (slice-09) + equity (slice-10) + flags + coverage stats into
   the Markdown dossier; enforce hedged language.
2. Build the coverage/limits footer from the synthesizer's prune log + counties/hops + the stated
   limitations (PLAN.md §17).
3. Run the documented dry run on a sample real name; record portal availability + false-positive rate;
   note any cutoff tuning; re-validate H1/H2/H3.
4. Tests: structure, hedged language, coverage footer, provenance/freshness.

### Dev Evidence Bundle (7 parts — required)
Summary; Traceability (ent-reportv1, meth-hedged, EV-020/023, metric-channelcov/prunect/fpr, risk-licensing);
Quality (stdlib render); Functional (the DoD tests + dry-run findings); Security/Compliance (hedged,
estimates-labeled, limitations stated); Operational (audit trail verified); Self-assessment.

### Dev Learnings
- (fill at execution) Dry-run portal availability surprises; false-positive rate observed; cutoff tuning.

## QA Section (Zero-Trust Verifier)

### Verification steps
1. Scan the rendered dossier for un-hedged claims — any "definitely owns" / bare "owns" without title = REJECT.
2. Confirm the coverage/limits footer reports counties/hops/hubs-pruned AND the stated limitations
   (no-free-national-search, name-blocked states, big-county gating, estimates-not-AVMs, licensing out of scope).
3. Independently confirm every parcel row carries source URLs + freshness.
4. Review the dry-run findings: are portal availability + false-positive rate actually recorded, and are
   H1/H2/H3 re-validated?

### Evidence gates (all must pass)
- [ ] **Hedged language throughout** (hard; fail = REJECT).
- [ ] **Coverage/limits footer complete (counts + stated limitations)** (hard; fail = REJECT).
- [ ] Provenance + freshness on every parcel.
- [ ] Dry-run findings recorded; H1/H2/H3 re-validated.
- [ ] Learnings updated.

### QA Learnings
- (fill at execution) Any missing limitation or un-hedged phrasing in the final dossier.
