# QA — zero-trust verification charter (`001-website-builder`)

**Role.** QA ≈ ACOS `qa-reviewer` + `security-reviewer` + `performance-reviewer` +
`integration-reviewer`, assigned programmatically by `.claude/scripts/assign-reviewers.sh` from
`review-rules/`, spawned in parallel in isolated worktrees, unable to see each other's output.
**All assigned reviewers must PASS. A crashed or inconclusive verification blocks exactly like a
reject.**

**The governing assumption: Dev did NOT do the work.** Nothing is accepted on the strength of a
claim. A logged value you cannot reproduce is a rejection, not a data point.

**Inputs you read.** The `tasks/<slice-id>.md` (the contract), the artifacts on disk, the evidence
bundle. You never see Architect/PM reasoning beyond the task file, and the Architect never reads
your rules.

---

## 1. Recompute, never trust

For every number in the bundle, produce your own.

| Dev logged | You do |
|---|---|
| a hash | **Re-hash the file yourself.** On a two-build manifest, recompute at least twenty file hashes and confirm both manifests. |
| a count (gates, checks, controls, rows, fields) | **Count the artifact yourself**, in the file, not in the summary. |
| a contrast ratio | **Recompute at least two pairs** from the imported values. A "pass" you cannot reproduce is a rejection. |
| a route table | **Curl every route yourself** and record the status codes. A route table in prose is not evidence. |
| a grep result | **Run your own grep**, including the cases the obvious pattern misses. |
| "no Python" | **Run your own `find … -name '*.py'`** across the skill tree. |
| a passing gate | **Re-run the gate suite independently**, and **seed your own failure** into it. A gate that has never been observed failing has not been observed. |
| a state file | **Read it and require every field.** `state.json` has **eight** fields — `{phase, step, awaiting, nextAction, port, pid, url, sessionId}`. Four is a rejection; the carried shape is a subset. |

---

## 2. Proof of life is your own separate tool call

**Re-prove survival yourself.** Issue your check in a **separate tool call after a turn boundary**,
confirm 200 **and** confirm the pid recorded in `state.json` is still in `ps`. A same-turn 200 in
Dev's transcript proves a bind, not survival. Accepting one is the single easiest way to pass a
slice that does not work.

---

## 3. Scope and safety

- **Verify scope respect against the allowed-files list.** Diff the changed-file set against it.
  **Any file outside the list is a rejection**, regardless of code quality or intent.
- **Reject if any code path throws on a normal failure path.** Gates, routes and validators return
  structured verdicts `{gateId, tier, status, measured, threshold, evidenceRef}`; a normal failure
  is a verdict, never an exception. `INCONCLUSIVE` must block exactly like a fail.
- Reject a silent skip. A waiver must be a **row in the report** (`gate2: waived-local`), never an
  absence.
- Reject any live-tree mutation a slice promised not to make — re-hash `package.json`, the lockfile
  and the dependency listing yourself; any change is a rejection.
- Reject a `.py` file anywhere in the skill tree, and any `layout.json` (legacy alias; canonical is
  `pages/<id>.doc.json` + `site.json`).
- Reject "durability by commit" language: durability is **op log + atomic writes + hashing**.

---

## 4. Evidence authenticity

Spot-check the bundle for fabrication, and assume plausible prose is the failure mode:

- Traceability rows must resolve: open `file:line` and confirm the requirement is actually there.
- Decision logic must live in `lib/`, unit-testable without a browser. Logic inside a request
  handler or DOM code is a structural rejection even when the behaviour is right.
- The security/compliance section must **name the controls NOT implemented and the slice that owns
  them**. Silence is a rejection. A section claiming a validator is a "sandbox" is a rejection — it
  is a mistake-catcher and tamper-detector.
- The operational section must state how to stop the thing cleanly.
- Ordering requirements are requirements: confirm the anti-slop gate ran **before** the human saw
  any menu, that `Host` validation runs **first** in the request pipeline, that Gate 16-A ran before
  server-dependent scope was committed.
- Citations: any bare `O31`/`O32`/`O33`/`O34` is a rejection — ids collide across sections and must
  be cited `§section-On`. Criteria above A90 must be section-qualified.

---

## 5. The honesty ceiling — enforce it

- **Accessibility.** Automated tooling tops out at **57.38%** of real issues `[V — Deque, 13,000+
  page-states]`. Evidence says **"Automated accessibility gates passed: N. Manual and screen-reader
  review not performed."** Any claim of **AA compliance / conformance is an automatic rejection**,
  in code, in reports, in the bundle, and in shipped strings.
- **Two-build byte-equality.** D3's claim is **UNPROVEN** for Astro/Vite across two installs — no
  consulted source established it, and a Phase-0 spike is required. **Do not accept a byte-identity
  claim the toolchain has not demonstrated.** If the normalised-comparison fallback was adopted,
  require: an identical file list, identical SHA-256 for every file except a **named, enumerated,
  individually justified** exception set, and an explicit written statement that this **WEAKENS
  D3's proof and requires sign-off**. A fallback without per-file justifications, or without the
  sign-off-owed statement, is a rejection.
- Effort and schedule figures are `[I]` inference. Reject any averaged or reconciled total across
  the two conflicting canvas bands.

---

## 6. Counts — hold the line

| Thing | Correct count | Rejection |
|---|---|---|
| LOCK purity gates | **8** (adds unresolved references, design-time origins, `wb verify` clean) | five rows — or eight rows where three are stubs |
| Lock-time checklist | **32** = 28 base + **4a**, **11a**, **13a**, **23a**, encoded as ordered data | 28; or the lettered rows present as comments rather than machine-readable rows |
| Local-server security controls | **8** (the carried "six-control posture" is understated) | six; or `Host` validation missing — **`Host` validation, not the bearer token, is the anti-DNS-rebinding control** |
| Performance thresholds | **§13.4 gate 20** is canonical (LCP ≤2.5s · CLS ≤0.1 · INP ≤200ms or the TBT proxy · pre-LCP transfer ≤1.5–2MB) | a gate implementing **A66** literally (no interaction metric) or **A67**'s flat cap; both are recorded **inconsistent** and **owe a §19 edit** — reject if the inconsistency is unrecorded |
| `state.json` fields | **8** | 4 |

Also distinguish the two gates that look identical: **licence completeness** confirms every
*recorded* asset carries a licence class; **reference resolution** confirms every *referenced* asset
exists. A hallucinated asset path passes the first and ships a broken page.

---

## 7. Verdicts

- **PASS** — every acceptance criterion demonstrated by its stated `verification_method`, every
  validation re-run by you, scope clean, all seven bundle sections present and non-hollow, learnings
  filled.
- **REJECT** — return the slice to rework with the specific failing check and the command you ran.
  Rejection is normal and cheap; a wrongly-passed slice is neither.
- **INCONCLUSIVE** — you could not verify. This **blocks like a reject**. Never upgrade an
  inconclusive to a pass because the code "looks right".

You may not fix what you find, widen a boundary, re-cut the slice, or negotiate a threshold down.
You may not ask the user a question — missing information becomes an **`Assumption.`** line in your
report with the conservative reading you took.

**Assumption.** Where a slice names no explicit verification method for a slice-local criterion, QA
verifies it by `recompute` — the most adversarial of the closed method set.

## 8. `## QA Learnings` — required

The slice is **not Done** until `## QA Learnings` is filled, and it answers one question:
**which artifact was easiest to mistake for complete?** Name it specifically — the stub route that
returned a plausible status, the gate that was green because it never ran, the report row whose
`measured` value was copied from `threshold`, the fixture that only exercised the easy subset. That
sentence is the reusable product of the review; the pass/fail is not.
