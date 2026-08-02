# S75-gotchas-provenance-and-banners — Gotchas reference, provenance and do-not-hand-edit banners

| Field | Value |
|---|---|
| Epic / Story | E18 / ST-25 |
| Type · MoSCoW · Size | build · MUST · S `[I]` |
| Phase / Demo | Phase 6 / — |
| Depends on | S09-install-config-session-selftest |
| Requirements | FR-243, FR-244, FR-245 |
| Acceptance criteria | SL-S75-1 · SL-S75-2 · SL-S75-3 |
| CQ / evidence | CQ6 |
| Note | **R44 restated:** the generation **RESULT** is the artifact of record; the prompt is provenance only. A system that plans to be re-derived from a stored prompt is a system that cannot be reproduced |

## PM — slice definition

**Objective.** Write down the harness facts that cost time, and make generated files say **what to edit instead**.

**In scope.** `references/gotchas.md` carrying every harness fact — **cwd resets between shell calls** so every path is absolute; there is **no `timeout`/`gtimeout` binary** on this machine and it yields **empty output rather than an error** (a silent, misleading failure); previews are opened with an **explicit browser invocation**, not the default handler; **APFS is case-insensitive**, so sibling direction directory names must not differ only by case; **destructive commands score high with the permission layer** and `rm -rf` never appears in the export path; a same-turn HTTP 200 is never proof of life; subagents are policy-blocked from `Write`, so agent-produced code returns as text and the main thread writes it; `Task` availability mid-skill is unverified (`§16.5.1-O31`) and nothing depends on it. Plus `provenance.json` recording the RESULT with the prompt stored **for provenance only**; generated-file **do-not-hand-edit banners** that name the file to edit instead; and durable artifacts kept under `.acos/website-builder/` and the project's own tree, outside the framework state directory that session cleanup touches.

**Out of scope.** Enforcing the gotchas in code — this slice records them and adds the two mechanical assertions below; hooks and guards belong to their owning slices. Re-deriving anything from a stored prompt, ever.

**Allowed files / contexts.**
- `references/gotchas.md` (new), `scripts/lib/banner.ts`, `scripts/lib/provenance.ts`, `04-site/provenance.json` (write via the editor process), `scripts/selftest.ts` (extend).

**Steps.**
1. Write `gotchas.md` with one row per fact: the fact, how it manifests, and the countermeasure. A fact with no observed manifestation is marked as inherited, not as first-party.
2. Add the **passing launcher rung** from Gate 16-A the moment S01 lands — it is a first-party harness fact worth more than any documentation, and it is one of the three named learning obligations.
3. Implement `banner.ts`: every generated file gets a banner naming (a) that it is generated, (b) the generator, and (c) **the file to edit instead** — a banner that only forbids is ignored.
4. Implement `provenance.ts`: persist the generation RESULT as the artifact of record; store the prompt under `01-prompt/` for provenance only.
5. Add a selftest assertion that **no code path re-derives a system from a stored prompt** — a grep over the source for a read of `01-prompt/**` feeding a generator input.
6. Assert durable artifact paths live under `.acos/website-builder/` and the project tree, never under the framework state directory that session cleanup removes.

**Definition of Done.**
- Artifacts: `references/gotchas.md`, `banner.ts`, `provenance.ts`, selftest assertions for the no-re-derivation and durable-path rules.
- Validation: every named harness fact present by grep; every generated file carries a banner naming an alternative file; the re-derivation grep returns zero; no durable artifact path resolves inside the session-cleanup scope.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S75-1, SL-S75-2, SL-S75-3]`, `verification_method: grep-assert` (SL-S75-3: `exit-code`).

## Dev — execution contract

Write the gotchas for someone six months from now who has forgotten all of it, including yourself. Evidence bundle: (1) summary listing the facts recorded and which are first-party; (2) traceability FR-243, FR-244, FR-245 → file:line; (3) structural quality — the banner text is generated from one template, so it cannot drift file to file; (4) functional testing — the grep transcript per fact, a sample banner from three different generated file kinds, the re-derivation assertion; (5) security/compliance — the prompt store contains no credential and no session path; (6) operational — how to add a gotcha without renumbering anything; (7) self-assessment.

## QA — zero-trust verification

- **Grep `gotchas.md` yourself** for each named fact; a fact described in a paragraph but not findable by its keyword is a rejection, because this file is read under pressure.
- **Verify the `timeout` fact yourself** by running a command that would use it and observing the empty output — this is the gotcha most likely to be recorded wrongly as "errors out".
- **Open a generated file** and confirm the banner names a specific alternative file, not just "do not edit".
- **Run your own** grep for any code path reading a stored prompt into a generator input; one hit is a rejection.
- **Check every durable artifact path** against the session-cleanup scope; an artifact inside it is a rejection.
- **Reject** if a gotcha is stated as first-party when it was inherited and never observed here.

## Dev Learnings

_Not Done until filled. Required: which harness fact cost the most time on this build, and which inherited one turned out to be wrong._

## QA Learnings

_Not Done until filled. Required: whether the banners changed anyone's behaviour, and which gotcha was hardest to state in one falsifiable sentence._
