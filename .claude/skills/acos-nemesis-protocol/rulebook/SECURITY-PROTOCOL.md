---
name: security-protocol
description: The ten-star security protocol — a mandatory, iterative security gate that runs before every task, around every feature, and before every line of code, until zero issues remain. General-purpose; drop into any project or skill. Written 2026-10-08 for the OKOA Investor Portal.
---

# The Ten-Star Security Protocol

> **Rule zero.** Security is the most important property of anything built under this protocol.
> There is no trade-off that buys a loophole. If a feature cannot be built securely in the time
> available, the feature waits; the loophole never ships.

This protocol is written so that a person, a Claude session, or another skill can follow it
mechanically. It has four parts: the **principles** (what we believe), the **loop** (what we do,
in order, every time), the **checklists** (what we look for, by domain), and the **records**
(what we write down so the next reader can verify we did it). An **integration** section at the
end explains how to wire it into other skills and hooks.

The protocol was written for the OKOA Investor Portal, where the data is other people's money
and tax ids. Nothing in it is specific to that portal; the portal's own threat model lives in its
PRD and only *applies* this document.

---

## Part 1 — Principles

1. **Deny by default.** Nothing is readable, writable or callable until a rule explicitly allows
   it for that person, that row, that action. Row-level security on every table; a table without a
   policy shows nothing. Every endpoint starts closed.
2. **Least privilege, everywhere.** People, services, database roles, API keys and build agents
   each get the smallest set of rights that lets them do their one job. Staff bypass is a named
   role, never the default connection.
3. **Defense in depth.** The application checks, the database checks again, the audit log records
   it, and a test proves it. One layer failing must not expose data.
4. **Never trust input.** Every value that crosses a boundary (browser, file, e-mail, API,
   another skill, an AI model) is validated against an allow-list and encoded on output.
5. **Data minimization.** Collect, store, show, log and send only what the feature needs. Mask by
   default (last-4). Encrypt sensitive values before they reach storage.
6. **Fail closed.** When unsure, refuse with a typed error and log it. Never guess, never fall back
   to "show everything", never swallow an error.
7. **Separation of duties.** The person who writes a thing is not the person who approves it:
   code review, report approval, campaign send, payment-like actions.
8. **Everything on record.** Every change, login, denial, export and impersonation is in an
   append-only audit trail that the actor cannot edit.
9. **No secrets in code, prompts, logs or tickets.** Secrets live in a secrets manager or
   environment injection; the repository, the transcript and the model never see them.
10. **Reproducible and reviewed.** Pinned dependencies, lockfiles, signed releases, branch
    protection, and an independent adversarial review before anything reaches people.
11. **No fabricated security.** A claim like "this is safe" without a test, a record and a
    reviewer is not a claim; it is a guess. Say "unverified" when it is unverified.
12. **Humans approve the irreversible.** Deletes of real data, sends to real people, and any
    money-like action need a second person and a confirmation step.

---

## Part 2 — The loop (do this, in order, every time)

The loop runs at three sizes: once per **task** (a feature, a slice, a ticket), once per **change**
(a commit or a pull request), and once per **line** (while writing). The steps are the same;
only the depth changes.

### S0. Pre-task security check — before anything else

Before the first file is opened, write the task's **threat sketch** (template in Part 4):

- What data does this touch? Classify it (Part 3.6): public / internal / confidential /
  sensitive (PII, financial, secrets).
- Who may see or change it? Name the roles and the row-level rule.
- What could go wrong? Walk STRIDE: **S**poofing (fake identity), **T**ampering (changed data),
  **R**epudiation (no record), **I**nformation disclosure (leak), **D**enial of service,
  **E**levation of privilege. One line each, "none" allowed only with a reason.
- Which checklists apply (Part 3)? Tick them.
- What is the **abuse case**? Write the attacker's story in two sentences.

**Gate:** no threat sketch → the task does not start.

### S1. Design review — before code

- Draw the data flow: where the data enters, where it is stored, where it leaves, and every
  trust boundary it crosses.
- Write the **authorization matrix** for the feature: rows = actions, columns = roles, cells =
  allowed / denied / own-rows-only. The row-level-security rule for each table is written here.
- Decide the typed errors the feature returns (`PERMISSION_DENIED`, `NOT_FOUND`,
  `VALIDATION_FAILED`, …) and that they never leak existence of other people's data.
- Decide what is logged and what must never be logged (secrets, full tax ids, full bank numbers,
  session tokens, raw request bodies with PII).
- If an AI model is involved: what exactly goes into the prompt, what must never go in, and who
  approves the output before anyone else sees it.

**Gate:** design review recorded (Part 4) → coding may start.

### S2. The line rule — while writing

Before every line of code (or SQL, or config) is committed to the file, answer the twelve
questions silently; if any answer is "yes", write the line differently or stop and fix the cause:

1. Does this line read or write data without the caller's authorization being checked **on this
   row**?
2. Does it build a query, a command, HTML, a URL or an e-mail from input without
   parameterization or encoding?
3. Does it trust a client-supplied id, role, price, amount, profile or user id?
4. Does it log, print, return or store a secret, a full sensitive value, or more fields than needed?
5. Does it catch an error and continue as if nothing happened?
6. Does it widen a permission, a CORS rule, a role, a policy, or disable a check "for now"?
7. Does it use randomness, hashing or encryption from a hand-rolled or non-approved source?
8. Does it accept a file, a path, a redirect target, an HTML fragment or a template from input
   without an allow-list?
9. Does it send data to a third party, a model, a webhook or an e-mail that the design review
   did not list?
10. Does it depend on a package, version or script that is not pinned and reviewed?
11. Does it make an irreversible or money-like action without the second-person step?
12. Could this line behave differently under concurrency, retries or a replayed request
    (double payout, double send)?

**If the problem comes from somewhere else** (a missing policy, an upstream function that
returns too much, a library default), the line is not the place to patch it: open the real cause
as a security issue (Part 4) and fix it there, now, before continuing. Do not "write around" an
upstream hole.

### S3. Post-change scan — after every change

Run all of these; record the results:

- **Static checks:** type-check, lint with security rules, secret scanner over the diff and the
  repository, dependency audit (known vulnerabilities), license and provenance check for new
  packages.
- **Policy check:** every new table has row-level security enabled; every new view runs as the
  caller; every new endpoint has an authorization test; every new write path has a typed error
  path.
- **Tests:** the feature's positive tests **and** its negative tests: wrong user, wrong row,
  wrong role, missing field, oversized input, replay, concurrent duplicate. A feature with no
  negative test is not done.
- **Data tests:** no sensitive value appears in logs, error messages, exports or test fixtures
  that leave the machine.
- **Review the diff as an attacker:** read every changed line asking the twelve questions again.

### S4. The iterative fix loop — until zero

Every finding from S3 (or from a reviewer, a scanner, a holdout, or production) enters the
**issue list** with a severity (Part 2, "Severity"). Then:

```
repeat
  fix the highest-severity open issue at its root cause (not at the symptom)
  re-run S3 in full — a fix can introduce a new issue
  add any new finding to the list
until the list has zero open issues
then run S3 once more; it must be clean twice in a row
```

The loop has no step budget. Stopping with an open issue is a defect, whatever its severity.
A finding may be closed only by a fix plus a passing re-check, or by a written decision from
the owner that the finding is a false positive, with the reason.

### S5. The security check record — written evidence

Each task ends with a record (template in Part 4) that lists: the threat sketch, the design
review, the issues found and how each was closed, the scans run and their results, the tests
added, the reviewer, and the leftover risks with owners and dates. No record → not done.

### S6. Independent adversarial review

A second reviewer who did not write the code (a person, or a separate Claude agent with no
shared context) reads the change and the record with one goal: break it. The reviewer reports
findings in the same severity scale; the loop in S4 runs again on them.

### S7. Holdout proof

For every security-relevant behavior, a **holdout test** written before the code and hidden from
the builder (see `acos-holdout-test`) proves the behavior at reveal time: cross-user reads are
denied, soft-deleted rows never render, exports are logged, drafts are invisible, approvals need
a second person. A holdout that blocks is a security issue.

### S8. Release gate and watch

Before release: zero open security issues at any severity, S6 complete, holdouts passed, secrets
rotated if any were exposed during the work, backups and restore tested, monitoring and alerts
in place for failed logins, permission denials, rate limits and unusual exports. After release:
the alerts are read, and every incident re-enters the loop at S0.

### Severity

| Level | Meaning | Rule |
|---|---|---|
| Critical | Data of another person readable or changeable; secrets exposed; money-like action without control | Stop all other work. Fix now. |
| High | A control missing that one more mistake would turn into Critical (no RLS on a table, no negative test, no audit) | Fix before the change is merged. |
| Medium | Weakens a layer (verbose error, missing rate limit, loose validation) | Fix before the feature is called done. |
| Low | Hygiene (header missing, stale dependency without known exploit) | Fix in the same task; may not be deferred past release. |

"Zero open issues" means zero at every level. Low is not "ignore".

---

## Part 3 — Checklists by domain

Tick every line that applies; write "n/a + why" for the rest. A line you cannot tick is an issue.

### 3.1 Identity and login
- Login is delegated to a proven provider (e.g. Clerk) or a reviewed library; no home-made
  password storage.
- Multi-factor is available and required for staff.
- Sessions expire; logout invalidates server-side; tokens are not in localStorage; cookies are
  `HttpOnly`, `Secure`, `SameSite`.
- Invitations are single-use, expire, and bind to the invited e-mail.
- Sign-up or activation that needs staff approval stays in a `pending` state that can read nothing.
- Failed logins and lockouts are logged and rate-limited.

### 3.2 Authorization
- Every table has row-level security enabled; staff bypass is a named role.
- Every view runs as the caller (`security_invoker`).
- Every endpoint checks authorization **on the object**, not only on the role (no IDOR).
- Investors (or end users) can write only their own rows in a short, listed set of tables.
- Impersonation ("view as") is a logged, time-boxed, read-only mode.
- Permission denials return the same shape as "not found" where existence must not leak.

### 3.3 Input, output and injection
- Parameterized queries only; no string-built SQL, shell, LDAP or template code.
- HTML from users or AI is sanitized with an allow-list; rendered content never executes scripts.
- Output is encoded for its context (HTML, attribute, URL, JSON, CSV formula injection).
- File uploads: allow-listed types, size limit, content sniffed, stored outside the web root
  under a generated name, served through signed, expiring URLs, scanned where possible.
- Redirects and links only to allow-listed destinations.
- Numbers for money are decimal, never float; parsing rejects anything but digits, sign and point.

### 3.4 Secrets and configuration
- Secrets come from the environment or a secrets manager; `.env` files are ignored by git.
- A secret scanner runs on every commit; a found secret is rotated, not just removed.
- Production, staging and development have separate secrets and separate data.
- Debug modes, verbose errors and sample accounts are off in production.

### 3.5 Cryptography
- TLS everywhere; HSTS on.
- Sensitive fields are encrypted by the application with a managed key before storage; only a
  last-4 is kept in clear.
- Keys are rotated on a schedule and on any suspicion; old keys can still decrypt.
- Only well-known libraries; no custom algorithms; strong randomness for ids, tokens, invites.

### 3.6 Data classification and privacy
- Public / internal / confidential / sensitive, decided in S0 and written on the schema
  (`sensitive` flag) and the API.
- Sensitive data is masked in every list and export unless the viewer has an explicit right.
- Exports (PDF, CSV, Excel, images) are logged with who, what, filters and size.
- Retention: what is kept how long, and how it is deleted (soft delete first, purge on schedule).
- The person's own rights: view, correct, export, erase where the law applies.

### 3.7 Logging and audit
- Append-only audit table for inserts, updates, deletes, logins, failed logins, denials, rate
  limits, exports, downloads, impersonation, invites.
- Logs never contain secrets, full sensitive values, session tokens or full request bodies.
- Audit rows record the acting user **and** any "acting as" identity.
- Logs are time-synchronized, retained, and alert on patterns (many denials, mass export).

### 3.8 E-mail and messaging
- Sending domain has SPF, DKIM and DMARC; the sender is a fixed list.
- Templates are allow-listed merge fields; no raw HTML from input.
- Links are to our domain, expire where they grant access, and never carry secrets in the URL.
- Bulk sends need a second-person approval and a test send first.
- Unsubscribe and bounce handling exist and are honored.

### 3.9 AI and language models
- The model sees the minimum: one person's data for one output; never secrets; never other
  people's rows.
- Prompts are templates with validated slots; user text is marked as data, never as instruction
  (prompt injection defense); tool access is allow-listed.
- Model output is treated as untrusted input: sanitized, validated, and approved by a person
  before anyone else sees it.
- Every generation is recorded (model, instruction hash, input hash), without storing the raw
  prompt that contained personal data.
- No external model endpoint receives confidential data unless the contract and the data-flow
  review allow it; subscription-bound agents preferred where available.

### 3.10 API, web and rate limits
- CSRF protection on state-changing requests; CORS allow-list; security headers
  (`Content-Security-Policy`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`,
  `frame-ancestors`).
- Rate limits per user and per IP on login, requests, exports, searches; limits are logged.
- Pagination caps; no unbounded list endpoints.
- Idempotency keys on anything that could be replayed (sends, postings, approvals).

### 3.11 Dependencies, build and supply chain
- Lockfile committed; versions pinned; new packages reviewed (purpose, maintainer, size,
  install scripts).
- Automated vulnerability audit in CI; a known exploitable vulnerability blocks.
- Builds are reproducible from a clean checkout; no network fetches at runtime from unpinned
  sources; CDN scripts pinned to exact versions and allow-listed by CSP.
- Branch protection: review required, CI green required, no force-push to main.

### 3.12 Database
- RLS on every table; policies tested with a negative test per table.
- Soft delete and audit on business tables; immutable (append-only) tables for ledgers and events.
- Constraints carry the invariants (checks, uniques, foreign keys) so bad data cannot be stored.
- Migrations are reviewed with the twelve questions; destructive migrations need a backup first.
- Backups encrypted, tested by an actual restore, and access-logged.

### 3.13 Infrastructure and operations
- Private network for the database; least-privilege roles; no shared admin accounts.
- Encryption at rest; key management by the provider or a KMS.
- Monitoring and alerts; an incident runbook; a contact for security reports.
- Access to production data is logged and needs a reason.

### 3.14 Front end
- No sensitive data in localStorage or in URLs; only per-viewer conveniences.
- Strict CSP; no inline event handlers; dependencies pinned; subresource integrity where used.
- Clickjacking protection; forms with CSRF tokens; file downloads via signed URLs.
- Accessibility of security flows (every action possible without a mouse).

---

## Part 4 — Records and templates

### 4.1 Threat sketch (S0) — one per task

```yaml
task: <id / title>
data_touched: [<table or object>: <public|internal|confidential|sensitive>, ...]
actors: [<role>: <what they may do>, ...]
stride:
  spoofing: <one line or "none because ...">
  tampering: <...>
  repudiation: <...>
  information_disclosure: <...>
  denial_of_service: <...>
  elevation_of_privilege: <...>
abuse_case: <two sentences from the attacker's view>
checklists: [3.1, 3.2, 3.3, ...]
```

### 4.2 Design review (S1)

```yaml
data_flow: <entry -> storage -> exit; trust boundaries named>
authorization_matrix:
  - action: <...>; staff: allow; investor: own_rows; anonymous: deny
rls_rules: [<table>: <policy in words>, ...]
typed_errors: [PERMISSION_DENIED, NOT_FOUND, VALIDATION_FAILED, ...]
logging: {log: [...], never_log: [...]}
ai_use: {inputs: [...], never_inputs: [...], approver: <role>}  # or "none"
reviewer: <who>
```

### 4.3 Security issue

```yaml
id: SEC-<n>
severity: critical|high|medium|low
found_by: scan|test|review|holdout|production
where: <file:line or table/policy or endpoint>
what: <one sentence>
root_cause: <one sentence — the real cause, not the symptom>
fix: <what changed>
re_check: <scan/test run after the fix, and its result>
closed_at: <date>   # only after a clean re-check
```

### 4.4 Security check record (S5) — one per task

```yaml
task: <id>
threat_sketch: <link or inline>
design_review: <link or inline>
issues: [SEC-1, SEC-2, ...]      # all closed, or the task is not done
scans: {typecheck: pass, lint_security: pass, secrets: clean, deps_audit: clean}
tests_added: {positive: <n>, negative: <n>}
loop_passes: <n>                  # S3 runs; the last two must be clean
independent_review: {by: <who>, findings: [...], closed: true}
holdout: {pack: <manifest>, verdict: PASS}
residual_risks: [{risk: ..., owner: ..., due: ...}]   # empty is the goal
```

---

## Part 5 — Integration with other skills and hooks

- **As a skill:** copy this file to `~/.claude/skills/security-protocol/SKILL.md`. Any skill that
  builds software should say in its own instructions: "Run the security-protocol loop: S0 before
  starting, S2 while writing, S3–S4 after every change, S5 before reporting done."
- **With `acos-holdout-test`:** every security behavior gets a holdout case authored before the
  build (S7). Security packs always carry a `deciding` case: the cross-user read denial.
- **With the ACOS reviewers:** the `security-reviewer` agent is the S6 reviewer; it receives the
  threat sketch, the design review and the diff, and reports in the Part 4.3 format.
- **With the Confirmation Gate / restate step:** the restatement of any build task names the data
  classes it touches and the checklists that apply (S0 in one line).
- **As a hook:** a `PreToolUse` hook can refuse an edit to files under `db/`, `auth/`, `policies/`
  or `*.sql` when no security check record exists for the current task, and a `PostToolUse` hook
  can run the secret scanner on every written file. Keep hooks in TypeScript, run by bun.
- **In a PRD:** every feature section carries a "Security" block (threats, controls, negative
  tests, holdout cases) and the build order makes S0–S8 explicit per phase.

---

## Part 6 — The short version (print this)

1. Nothing starts without a threat sketch.
2. Deny by default; every table has row-level security; every view runs as the caller.
3. Ask the twelve questions before every line; fix causes, not symptoms.
4. Scan, test (negative tests too), and re-scan after every fix, until clean twice.
5. Write the record; get the adversarial review; pass the holdout.
6. Zero open issues at release — at every severity. No loophole, ever.
