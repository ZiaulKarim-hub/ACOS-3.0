# S70-publish-automated-with-runbook-fallback — Automated publish with an honest runbook fallback

| Field | Value |
|---|---|
| Epic / Story | E15 / ST-24 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 5 / Demo 4 (feeds) |
| Depends on | S69-lock-snapshots-manifest-and-unlock |
| Requirements | FR-210, FR-211 |
| Acceptance criteria | SL-S70-1 · SL-S70-2 · SL-S70-3 |
| CQ / evidence | EL-059 |
| Note | **NA-09 — §15.4 commits AUTOMATED publish as v1 behaviour**, overriding the normalization's runbook-first default. Sign-off row 7 ("Automated publish as the v1 commitment") is **Unsigned**; this slice records that fact rather than assuming approval |

## PM — slice definition

**Objective.** Commit automated deploy as the **v1 behaviour**, and record plainly when the fallback means the site is **locked but not published**.

**In scope.** A one-time credential setup performed by the user; every subsequent `wb lock && wb publish` running the static deploy **non-interactively**; the publish target read from `.acos/config/website-builder.yaml`; `publishRecord: {method: "automated"|"runbook", live: boolean, url?}` written into the evidence bundle and stated plainly in the run summary; the fallback path — **no valid credential, or the deploy call fails auth** ⇒ emit a runbook **and record that the site is locked but NOT published**; the recorded, quoted statement that the fallback **does not satisfy the "locked, published" exit criterion**; the unsigned sign-off row carried as a visible row in the publish record.

**Out of scope.** Choosing or provisioning a hosting provider on the user's behalf. Storing a credential anywhere in the session tree or the repository. Treating a successfully emitted runbook as a successful publish. Any backend, CMS or telemetry (NG3).

**Allowed files / contexts.**
- `scripts/publish.ts`, `scripts/lib/publish-target.ts`, `scripts/lib/runbook.ts`, `evidence/publish-record.json` (write), `07-lock/runbook.md` (write).
- **No credential is ever written into the session tree, the evidence bundle or the git repository** — the credential lives wherever the deploy tool already keeps it, and this slice only detects presence and validity.

**Steps.**
1. Detect credential presence and validity **before** building anything, so a doomed publish fails cheap.
2. On a valid credential: run the static deploy non-interactively against `07-lock/dist/`, capture the tool's exit code and the resulting URL, and write `publishRecord.method = "automated"`, `live = true`, `url`.
3. On no valid credential, or an auth failure: emit `runbook.md` with the exact commands the user must run, and write `publishRecord.method = "runbook"`, `live = false`. The run summary must say, in words, **"locked, NOT published"**.
4. Make the exit criterion mechanical: the "locked, published" bar is satisfied **only** by `method: "automated"` with `live: true`. A runbook run returns a distinct, non-zero-meaning status that Demo 4 can test.
5. Carry sign-off row 7 into the publish record as `signOff: {row: 7, statement: "Automated publish as the v1 commitment", status: "unsigned"}` — the slice records the row; only the human may sign it.
6. Redact anything credential-shaped from every log line and from the runbook before writing.

**Definition of Done.**
- Artifacts: `publish.ts`, the runbook template, `publish-record.json` from both paths, two recorded transcripts (automated and fallback).
- Validation: with a valid credential the deploy runs with no interactive prompt and records the URL; with the credential removed the run emits a runbook and records `live: false`; a grep of the bundle and logs for credential material returns zero.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S70-1, SL-S70-2, SL-S70-3]`, `verification_method: exit-code` (SL-S70-2: `grep-assert`; SL-S70-3: `manual-observation`).

**Assumption.** `[I]` The concrete deploy provider and its CLI are **not fixed by any read artifact** — the publish target is a configuration value (`publish target` in `.acos/config/website-builder.yaml`). This slice implements a provider-agnostic invocation contract (credential probe → non-interactive deploy of a static directory → URL capture) and names no provider. Choosing one is a user decision recorded at config time.

## Dev — execution contract

Evidence bundle: (1) summary stating in one sentence whether the site is live or only locked; (2) traceability FR-210, FR-211 → file:line; (3) structural quality — credential detection, deploy invocation and record writing are three separable functions so the fallback path is unit-testable without a network; (4) functional testing — both transcripts, with the fallback transcript showing the literal "locked, NOT published" string; (5) security/compliance — no credential in the tree, the bundle, the runbook or any log; the redaction test; (6) operational — the one-time credential setup, written for someone who has never done it; (7) self-assessment, stating that sign-off row 7 is **unsigned** and that this commitment is an interpretation.

## QA — zero-trust verification

- **Remove the credential yourself** and re-run; confirm a runbook is emitted **and** that `publishRecord.live` is `false`.
- **Grep the entire session tree, the bundle and the runbook** for credential-shaped strings; one hit is a rejection.
- **Confirm the exit criterion is mechanical** — force the runbook path and confirm the "locked, published" check *fails*. A runbook path that satisfies the exit criterion is the single most serious defect this slice can ship.
- **Read the run summary as a user would** and reject if a reader could come away believing a runbook run published the site.
- **Confirm the unsigned sign-off row is present and marked unsigned**; a slice that quietly assumes approval is a rejection.

## Dev Learnings

_Not Done until filled. Required: whether the deploy ran genuinely non-interactively on the first attempt, and what the credential probe could not detect in advance._

## QA Learnings

_Not Done until filled. Required: whether the fallback wording is unmistakable to a reader skimming the summary, and where "published" language leaked into the runbook path._
