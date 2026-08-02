# S24-doc-schema-and-canonical-serialisation — Document schema and canonical serialisation

| Field | Value |
|---|---|
| Epic / Story | E7 / ST-08 |
| Type · MoSCoW · Size | build · MUST · M `[I]` |
| Phase / Demo | Phase 1 / — |
| Depends on | S03-o8-substrate-spike · S21-token-compiler-dtcg-and-forge |
| Requirements | FR-070, FR-074 |
| Acceptance criteria | §12.17-A98 · §12.17-A92 · SL-S24-1 · SL-S24-2 |
| CQ / evidence | CQ3 · EL-071 |
| Note | **NA-07** — `layout.json` is a **legacy alias**. The canonical scene graph is `pages/<id>.doc.json` + `site.json`; the rename completes **here** |

## PM — slice definition

**Objective.** Define the scene graph as per-page documents plus a project record, serialised canonically so a re-serialise is always a zero diff.

**In scope.** `Doc {formatVersion, pageId, root, sectionOrder}`, `Node`, `LayoutEntry` (flow and free) and `Site` as TypeScript types plus a runtime schema validator; the canonical serialiser — UTF-8, LF, trailing newline, no BOM, fixed key sequence per node type then unknown keys sorted lexicographically, 2-space indent, one array element per line, shortest round-trip numbers with no `-0` and no exponents, explicit booleans and `null`, non-ASCII written literally; **absent optional keys omitted entirely rather than written `null`**; rejection of any breakpoint key above `base`; one seeded real page (`04-site/pages/home.doc.json`) plus `04-site/site.json`; the re-serialise-zero-diff check wired into `wb verify` and the pre-commit hook.

**Out of scope.** Rendering (S25) and the cascade compiler (S26) — this slice ships a document a human can read and a check that runs, not a page. Purity gate 8 itself (S67); this is its precondition only.

**Assumption.** The per-node-type key sequence is not published as a list anywhere; it is pinned from the `data-model.md` §3.10 / §3.11 field order and committed as a fixture so a later reorder is a diff, not a silent reformat `[I]`, low confidence.

**Allowed files / contexts.**
- `scripts/lib/doc-schema.ts`, `scripts/lib/canonical-json.ts`, `scripts/lib/verify-serialisation.ts`, `04-site/site.json`, `04-site/pages/*.doc.json` (seed only), the pre-commit hook.

**Steps.**
1. Declare the entity types; every optional key is optional in the type, never nullable.
2. Implement the serialiser against the eleven canonical rules; the key comparator is **one function**, exported, used by every writer.
3. Implement the validator: unknown keys allowed and sorted; an upward breakpoint key is **rejected with a message naming the desktop-down rule**; a key written as `null` where the schema says optional is rejected.
4. Seed a real `home.doc.json` and a real `site.json` (breakpoints, preview devices, grid, `pages[]` of length 1, `freePositionPolicy`) — not a fixture, the file the rest of the build reads.
5. Wire `wb verify` to re-serialise every doc-owned JSON file and require a zero diff; wire the same check into the pre-commit hook.
6. Grep the whole skill tree for `layout.json`; the only permitted hit is the note recording it as a legacy alias.

**Definition of Done.**
- Artifacts: types, serialiser, validator, seeded `site.json` + `home.doc.json`, the `verify` subcommand, the hook, the zero-diff transcript.
- Validation: re-serialise produces a zero diff; a hand-collapsed array fails the hook; an upward-key fixture is rejected naming the rule; `grep -rn 'layout\.json'` returns only the alias note; a `"md": null` fixture is rejected.
- `slice.yaml` mapping — `acceptance_criteria: ["§12.17-A98", "§12.17-A92", SL-S24-1, SL-S24-2]`, `verification_method: hash-compare` (§12.17-A92: `exit-code`; SL-S24-1/2: `grep-assert`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-070, FR-074 → file:line per canonical rule; (3) structural quality — one comparator, one serialiser, no second JSON writer anywhere; (4) functional testing — the collapsed-array, reordered-key, upward-key and explicit-`null` fixtures with recorded exit codes; (5) security/compliance — path resolution for doc-owned writes is `realpath` then a `startsWith(sessionRoot)` assertion, re-checked **after** resolution; (6) operational — what a contributor does when the hook fires; (7) self-assessment.

## QA — zero-trust verification

- **Re-serialise every doc-owned file yourself** and run your own `diff`; a logged "zero diff" you cannot reproduce is a rejection.
- **Hand-edit a seeded file** — collapse one array onto a single line — and confirm the hook and `wb verify` both fail.
- **Write your own upward-key doc** (an `xl` entry) and require rejection with the desktop-down message.
- **Grep for `layout.json` yourself** across the tree, and grep for `: null` inside the seeded documents.
- **Reject** if any module serialises JSON without going through the shared comparator.

## Dev Learnings

_Not Done until filled. Required: which canonical rule was violated first by ordinary tooling, and whether the fixed per-node-type key sequence survived contact with the real seeded document._

## QA Learnings

_Not Done until filled. Required: the reformatting path most likely to slip past the hook, and whether the zero-diff check is fast enough to run on every commit._
