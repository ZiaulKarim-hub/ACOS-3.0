# slice-10-security-pii — Security / PII / GDPR + secret handling + read-only enforcement hardening

- **Parent story:** STORY-HCA-09A · **Parent epic:** EPIC-HCA-09 · **Demo:** -
- **Effort:** M · **Dependency order:** 12 · **Depends on:** slice-08-orchestration
- **Lattice refs:** meth-piiscrub, std-readonly, std-secretstore, std-rbac, std-tls, std-aes, std-gdpr, risk-pii, cq-12

## PM Section (Planner / Specifier — LCE)

### Objective
Harden the safety posture so the skill is safe to point at live data once provisioned: PII-scrubbed logs/evidence, credentials loaded **only** from env/secret store, and a **structural read-only guard** that makes Hypercore mutation impossible. Honor TLS 1.2+, AES-256 at rest, RBAC, GDPR.

### Scope
**In scope:** a PII-scrubber applied to all logs + evidence-bundle writes; env/secret-store credential loader (no creds in repo); the read-only guard test elevated to a CI/quality-gate; AES-256-at-rest note + least-privilege on the Tier-1 cache; RBAC scope pass-through hook on the adapter (TBD specifics behind contract).
**Out of scope:** live auth scheme (TBD until access); feed formats (slice-09); consensus.

### Guardrails / Allowed files
- `.claude/scripts/hca-pii.py` (PII scrubber for logs/evidence; stdlib only)
- `.claude/scripts/hca-secrets.py` (env/secret-store loader; raises clear error if absent; **never logs the secret**)
- `.claude/scripts/hca-adapter.py` (add RBAC-scope pass-through hook + reinforce read-only guard — minimal, no contract change)
- tests: `.claude/scripts/tests/test_hca_pii.py`, `test_hca_secrets.py`, `test_hca_readonly_guard.py`
- `.acos/config/quality-gates.yaml` (register the read-only guard + PII-scan as gates — if project convention allows)
- this task file + `.acos/evidence/[DATE]/slice-10-security-pii/`
- Prohibited: any credential committed to repo; logging a secret or unredacted PII; adding a mutating adapter method.

### Definition of Done
- [ ] PII scrubber redacts borrower PII / financials in logs + evidence bundles to need-to-know — pass-condition: PII-scrub test on a sample containing planted PII (REQUIRED; nothing leaks).
- [ ] Credentials read only from env/secret store; absence yields a clear error and the NO_LIVE_DATA path, never a crash that leaks or a fabricated answer — pass-condition: secrets-loader test; **grep proves no credential string in repo** (REQUIRED).
- [ ] Read-only guard test elevated so adding any mutating verb to the adapter fails the gate — pass-condition: guard test fails on a planted mutating method.
- [ ] AES-256-at-rest + least-privilege documented for the Tier-1 cache; RBAC scope pass-through hook present (TBD behind contract) — artifact: security notes + hook.
- [ ] Subscription-only re-confirmed: no `ANTHROPIC_API_KEY` anywhere — pass-condition: repo grep gate.
- [ ] `## Dev Learnings` / `## QA Learnings` updated.

## Dev Section (Executor)

### Approach
1. `hca-pii.py`: redact known PII fields (legal_name, contact, financial detail) before any log/evidence write; default-deny unknown fields flagged sensitive.
2. `hca-secrets.py`: read `HYPERCORE_API_*` from env/secret store; never print; clear error on absence.
3. Reinforce the read-only guard (slice-02) into a standing gate; add RBAC pass-through hook.
4. Document AES-256/least-privilege/TLS posture.
5. Tests: PII-scrub, secrets-loader (present + absent), guard, repo-grep for secrets + API key.

### Dev Evidence Bundle (7 parts — required)
Summary; Traceability (Sh4 PII, NFR-Security/Privacy/Read-only, std-*, risk-pii, cq-12); Code Quality; Functional (tests); Security (the whole point — grep proofs); Operational; Self-assessment.

### Dev Learnings
- _(to fill at execution)_

## QA Section (Zero-Trust Verifier)

### Verification steps
1. Plant PII in a log + evidence write; confirm the scrubber redacts it everywhere it lands (logs, evidence, consensus/gate ledgers). Any leak = REJECT.
2. Grep the entire repo for credential-looking strings and `ANTHROPIC_API_KEY`; must find none.
3. Add a mutating method to the adapter in a scratch copy; confirm the elevated guard gate fails.
4. Run secrets loader with vars absent; confirm clear error + NO_LIVE_DATA, no crash/leak/fabrication.

### Evidence gates (all must pass)
- [ ] **No PII leaks into logs/evidence** — fail = REJECT (hard).
- [ ] **No credential / ANTHROPIC_API_KEY in repo** — fail = REJECT (hard).
- [ ] Read-only guard gate fails on planted mutation.
- [ ] Secrets-absent path degrades cleanly to NO_LIVE_DATA.
- [ ] Learnings updated.

### QA Learnings
- _(to fill at execution)_
