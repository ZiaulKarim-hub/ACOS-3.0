# S32-inline-plaintext-editing — Inline plaintext-only text editing

| Field | Value |
|---|---|
| Epic / Story | E8 / ST-10 |
| Type · MoSCoW · Size | build · MUST · S `[I]` |
| Phase / Demo | Phase 2 / — |
| Depends on | S31-typed-ops-autosave-history-undo |
| Requirements | FR-083 |
| Acceptance criteria | SL-S32-1 · SL-S32-2 |
| CQ / evidence | — (no CQ binds this slice) |
| Risk | **R36** — pasted source-app markup survives LOCK. `contenteditable="plaintext-only"` is the mitigation, and the stored value is the only place the mitigation can be proven |

## PM — slice definition

**Objective.** Let the human edit copy in place without source-app markup surviving into the type system.

**In scope.** `contenteditable="plaintext-only"` on the named text node classes — headings, eyebrows, buttons, nav items, labels, stat numbers (~90% of text nodes); each committed edit becoming a `set-text` typed op writing `content.json` through the single writer; the server rejecting a **non-plaintext payload on a `plaintext-only` node with 400**; content addressed by `node.text[key] → contentRef`, never by DOM position; `{value, kind: "plaintext"}` as the stored shape.

**Out of scope.** Rich text — `kind: "richtext"` is v2 and no code path may anticipate it. The content orphanage and parked content (S51). Copy rules and tone (the interview and concept slices). Any text node not in the named classes stays read-only in this slice and is listed.

**Assumption.** `contenteditable="plaintext-only"` is not uniformly supported across browsers; this slice pins the supported browser, tests the attribute's actual behaviour there, and ships a `paste`/`beforeinput` sanitiser as a **belt** rather than assuming the attribute holds `[I]`, low confidence.

**Allowed files / contexts.**
- `app/editor/inline-text.ts`, `scripts/lib/ops/set-text.ts`, `04-site/content.json` (written only through the op path).

**Steps.**
1. Mark the named classes editable with `plaintext-only`; every other text node stays inert and is enumerated in the evidence bundle.
2. Sanitise on `paste` and `beforeinput` as well, and record which one actually fired in the pinned browser.
3. Commit on blur and on the commit key as a `set-text` op carrying `{contentKey, value}` — never a DOM read of the whole subtree.
4. Reject a payload containing markup at the server with 400; the client-side strip is a convenience, the server rejection is the contract.
5. Prove the round trip by **inspecting the stored value in `content.json`**, not the rendered text.
6. Confirm each edit is one undo entry on the shared stack from S31.

**Definition of Done.**
- Artifacts: the inline editor module, the `set-text` op, the sanitiser, the enumerated editable-class list.
- Validation: a rich-text paste from a word processor into each named class stores plain text only, proven by reading `content.json`; a markup payload posted directly is rejected with 400; each edit is exactly one undo entry.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S32-1, SL-S32-2]`, `verification_method: grep-assert` (SL-S32-2: `exit-code`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-083 → file:line per editable class; (3) structural quality — one commit path; a grep proving no code writes `content.json` outside the op; (4) functional testing — the paste matrix (word processor, browser-copied HTML, plain text) × the six named classes, with the stored value recorded for each; (5) security/compliance — the stored value is text, so no markup reaches the renderer; state it and show the rejection; (6) operational — what happens to an in-progress edit when the SSE connection drops; (7) self-assessment.

## QA — zero-trust verification

- **Paste from a real word processor yourself** into each named class, then **read `content.json`** — a clean rendering with dirty stored bytes is a rejection.
- **Post a `set-text` op containing markup directly to the server** and require 400; a client-only strip is not the contract.
- **Grep the stored content values** for angle brackets, `&nbsp;` and style attributes; any hit is a rejection.
- **Count undo entries yourself** after a single field edit.
- **Confirm the non-editable text nodes are actually inert** — try to type into one.
- **Reject** if any code path anticipates `kind: "richtext"`.

## Dev Learnings

_Not Done until filled. Required: what `plaintext-only` actually stripped in the pinned browser versus what the sanitiser had to catch._

## QA Learnings

_Not Done until filled. Required: the paste source that came closest to landing markup in the stored value._
