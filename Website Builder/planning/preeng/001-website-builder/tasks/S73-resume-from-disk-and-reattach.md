# S73-resume-from-disk-and-reattach — Resume from disk and re-attach rather than relaunch

| Field | Value |
|---|---|
| Epic / Story | E18 / ST-25 |
| Type · MoSCoW · Size | build · MUST · S `[I]` |
| Phase / Demo | Phase 6 / — |
| Depends on | S09-install-config-session-selftest, S37-eight-control-security-posture |
| Requirements | FR-240, FR-241 |
| Acceptance criteria | A13 · SL-S73-1 · SL-S73-2 |
| CQ / evidence | CQ6 |
| Note | **The frontier principle:** the pipeline phase is recomputed from **which directories are populated and which gates passed** — never from conversation memory. A resume that reads the transcript is not a resume |

## PM — slice definition

**Objective.** Reconstruct the pipeline phase **from on-disk state alone** and survive a context reset **without restarting a live server**.

**In scope.** `--resume` recomputing the frontier over the session tree — `00-interview/` … `07-lock/` population plus the passed-gate record — and mapping it onto the phase machine `init → warm-start → interview → prompt-emitted → awaiting-ingest → ingested → direction-tournament → direction-selected → editing → regenerating → locking → locked → published`; reading the **eight-field** `state.json` `{phase, step, awaiting, nextAction, port, pid, url, sessionId}` (NA-B03 — the carried four-field shape is a subset); **regenerate-if-stale** when `state.json` names a dead pid; and the post-`/clear` resume text that says **RE-ATTACH** to the fixed port `8820` via `state.json`, never relaunch — a `/clear` kills the `tail -f` inbox loop, and re-attaching restores it.

**Out of scope.** Launching a server (that is S01's rung and S08's boot path). Any branch that consults conversation memory, a chat summary or a handoff note for state. Cross-session orchestration outside this skill.

**Allowed files / contexts.**
- `scripts/lib/resume.ts`, `scripts/lib/frontier.ts`, `scripts/lib/reattach.ts`, the resume text in `SKILL.md`, `scripts/selftest.ts` (extend).
- Reads `state.json`, `session.json`, `events.jsonl` and the directory tree. **Writes nothing in the doc-owned zone** — Claude reaches documents only through `wb op`.

**Steps.**
1. Implement `frontier.ts` as a pure function of a directory listing plus the gate record — no arguments carrying narrative state, so the "no conversation memory" property is structural rather than a promise.
2. Map the frontier onto the phase machine; every transition must be evidenced by a file, and an ambiguous frontier resolves to the **earlier** phase and says why.
3. Read all eight `state.json` fields; a four-field file is treated as stale and regenerated.
4. Implement re-attach: probe `127.0.0.1:8820` through `state.json`; if it answers, **re-attach and restore the inbox `tail -f`**. If the pid is dead, say so and hand off to the launcher rung — but never relaunch as the first move.
5. Write the post-`/clear` resume text using the imperative "re-attach", and add a selftest assertion that the text contains no relaunch instruction.
6. Prove survival across a real turn boundary with a **second curl in a separate tool call** — a same-turn 200 is never proof of life.

**Definition of Done.**
- Artifacts: `resume.ts`, `frontier.ts`, `reattach.ts`, the resume text, selftest assertions for the no-memory and no-relaunch properties.
- Validation: a session tree copied to a fresh location resumes to the correct phase with an empty conversation; a killed server is detected as stale rather than silently re-attached; the post-boundary curl returns 200 in its own tool call.
- `slice.yaml` mapping — `acceptance_criteria: [A13, SL-S73-1, SL-S73-2]`, `verification_method: exit-code` (SL-S73-1/SL-S73-2: `grep-assert`).

## Dev — execution contract

Absolute paths everywhere — agent-thread cwd resets between shell calls. There is **no `timeout` binary**; it yields empty output, not an error, so probes poll instead. Evidence bundle: (1) summary naming the phase recomputed and from which evidence files; (2) traceability FR-240, FR-241 → file:line; (3) structural quality — `frontier.ts` is pure and takes no narrative argument; (4) functional testing — a cold resume transcript with an empty context plus the two-call survival proof; (5) security/compliance — re-attach re-presents the per-session bearer token from `.wb/editor.token` (mode 0600) and never logs it; (6) operational — what to do when the port is occupied by a foreign process; (7) self-assessment.

## QA — zero-trust verification

- **Resume in a fresh context yourself** with no prior conversation and confirm the phase is correct; a resume that works only in the session that wrote it is a rejection.
- **Read `frontier.ts` yourself** and confirm no parameter could carry conversation state; **grep** for any read of a transcript, summary or handoff file.
- **Grep the resume text** for relaunch/restart wording and require zero; the instruction must say re-attach.
- **Kill the server yourself**, resume, and confirm the stale pid is detected rather than reported as live.
- **Re-prove survival in your own separate tool call** — a same-turn 200 is not proof.
- **Reject** if `state.json` is read as four fields.

## Dev Learnings

_Not Done until filled. Required: which directory signal proved unreliable as a frontier marker, and what an ambiguous frontier resolved to in practice._

## QA Learnings

_Not Done until filled. Required: whether a cold resume genuinely needed nothing from the conversation, and where a relaunch instruction tried to survive._
