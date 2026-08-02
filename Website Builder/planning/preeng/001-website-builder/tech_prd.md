# Technical PRD — Website Builder (`001-website-builder`)

**Command:** `/preeng.plan` (companion to `plan.md` and `data-model.md`)
**Feature directory (absolute):** `/Users/zee/Documents/Vibe Coding/ACOS 3.0/Website Builder/planning/preeng/001-website-builder/`
**Sources:** `spec.md` (FR/NFR ids), `research.md` + `domain-lattice.json` + `evidence-ledger.json` (EL/CQ ids), and direct reads of the signed-off PRD at `Website Builder/prd/website-builder-prd.md` (§12.10–§12.17 and §19 were read **this pass**, by offset window; the PRD is never read whole).
**Marker discipline:** `[V]` verified against a read source · `[I]` inference · `[U]` unsourced. Never promoted. **Every effort, duration and volume figure is `[I]`.**
**Language law:** TypeScript executed by Bun (`#!/usr/bin/env bun`, `scripts/package.json` with `type: module`, no build step). No new Python except the sign-off-gated F4 launcher rung. No Rust.

---

## 1. System shape

```
┌── Claude session (the only engine) ──────────────────────────────┐
│  SKILL.md thin router (9 phases) → scripts/*.ts (Bun)            │
│  reads .wb/inbox.jsonl via a blocking `tail -f` (zero tokens)    │
└───────────────┬──────────────────────────────────────────────────┘
                │ typed ops via `wb op` → POST /internal/*
┌───────────────▼──────────────── wb-server (Bun.serve, :8820) ────┐
│  THE ONLY WRITER of the doc-owned set                            │
│  GET /doc · POST /ops · GET /events (SSE) · POST /variants       │
│  POST /lock · POST /internal/* · static · GET /health            │
└───────────────┬───────────────────────────────┬──────────────────┘
                │ SSE + typed ops               │ pure render
┌───────────────▼──────────────┐   ┌────────────▼──────────────────┐
│ Editor chrome (browser)      │   │ Preview (same-origin iframe)  │
│ 3 panes; overlay OUTSIDE the │   │ device-height pinned; zero    │
│ iframe; proposes ops only    │   │ editor chrome in any capture  │
└──────────────────────────────┘   └───────────────────────────────┘
```

**Non-shape (explicit).** No autonomous multi-agent generation loop, no VLM judge, no autonomous aesthetic iteration (NG1). No backend, no CMS, no database (NG3). No CRDT. No File System Access API as a persistence path `[V — §12.15: Safari ships only OPFS, Mozilla published a "harmful" position]`. No multi-user writer (NG2).

---

## 2. Process topology — open, with committed invariants

`§17-O4` is **unresolved**. Two candidates:

| | Candidate A — two origins | Candidate B — single origin |
|---|---|---|
| Shape | preview dev-server renders the site; `wb-server` serves editor chrome; site in an iframe; `postMessage` with an explicit `targetOrigin` | one Bun server proxies the preview |
| Precedent | the shape Onlook / Stackbit / Tina converged on `[I]` | fewer moving parts, one port, one Origin allowlist entry |
| Cost | two ports, two origins, two things to forget to shut down (R38) | proxy correctness, HMR passthrough |

**Build only the topology-independent invariants until the ADR lands (slice S04):**

| Id | Invariant | Enforced by |
|---|---|---|
| I1 | One writer: `wb-server` alone writes the doc-owned set | `editor.lock`, the write allowlist, the ownership guard |
| I2 | The route contract of §3 | route tests in `selftest.ts` |
| I3 | Semantic ops only; never a raw path, never a raw JSON Patch | op-schema validation + 400 on path/patch bodies |
| I4 | Preview isolation is a **requirement, not a mechanism** — a capture of the preview contains zero editor chrome | purity gate 4 (screenshot diff) |
| I5 | The editor survives a preview-process restart without losing unsaved state | pending-op queue is server-side, not preview-side |
| I6 | Nothing hard-depends on one substrate | no framework import outside `src/substrate/*` |

**Spike scoring (S04):** the same two-page vertical slice on both topologies, one working session each, scored on channel LOC, preview-only screenshot achievability, HMR round-trip latency for a move op, and behaviour after killing and restarting the preview process. The result is an **ADR that updates §16.6 and §17-O4 together**.

---

## 3. Server contract

### 3.1 Routes (invariant I2)

| Route | Method | Contract | Failure modes |
|---|---|---|---|
| `/health` | GET | Liveness for Gate 16-A's post-turn-boundary curl | — |
| `/doc` | GET | Composition document + **ETag**; supports 304 | 404 if no session |
| `/ops` | POST | **Typed semantic ops only.** Validate each op against its schema *and* against the component library; derive the RFC 6902 patch; apply atomically (write-temp → `fs.rename`); append `{op, patch, inverse}` to `history.jsonl`; push over SSE | **409** stale ETag · **400** raw patch / file path / disallowed pointer · **422** op fails library validation |
| `/events` | GET | SSE, ~15s keepalive; carries doc updates, gate results, tab claim | reconnect with `Last-Event-ID` |
| `/variants` | POST | Lazy generation for one family in the active direction | 422 unknown family |
| `/lock` | POST | Runs the LOCK pipeline; returns the structured gate report | never throws on a normal gate fail |
| `/internal/*` | POST | The Claude session's write-back channel — **same validation path as `/ops`** | identical codes |
| static | GET | Editor chrome and the preview | — |

**Every mutating route and the SSE upgrade enforce the bearer token *and* the Origin allowlist. Every request — including the bootstrap `GET /` — enforces `Host` validation.**

### 3.2 Wire format: typed semantic ops

The browser and the Claude session send the *same* op shapes; there is one validation path and one code path for both (`wb op '<json>'` → `POST /internal/ops`).

```jsonc
{ "op": "swap-variant", "node": "n_hero", "variant": "hero-split@3",
  "etag": "sha256:…", "txn": "01J…", "label": "swap hero variant" }
```

Op families (the catalogue is normative; `data-model.md` carries the field-level schemas):

| Family | Ops | Writes |
|---|---|---|
| Node/layout | `place-node`, `move-node`, `set-span`, `reorder-siblings`, `set-align`, `set-space`, `set-free-position`, `clear-free-position`, `set-order-override`, `reset-to-inherited`, `delete-node`, `restore-node`, `duplicate-node`, `paste-fragment` | `pages/*.doc.json` |
| Content | `set-text`, `set-richtext` (v2), `set-slot`, `park-orphan`, `restore-orphan` | `content.json` |
| Component | `swap-variant`, `regenerate-section`, `acknowledge-migration`, `freeze-node`, `unfreeze-node` | `pages/*.doc.json` |
| Site | `add-page`, `remove-page`, `rename-page`, `reorder-pages`, `set-page-meta`, `set-breakpoints`, `set-grid`, `set-doctor-thresholds` | `site.json` |
| Asset | `register-asset`, `set-asset-meta`, `set-alt-text`, `record-derivative` | `assets/manifest.json` |
| Provenance | `record-placement`, `record-variant-swap` | `provenance.json` |

**Hard rules.** (a) A raw JSON Patch over HTTP is rejected — `add`/`replace` on an arbitrary pointer could rewrite `systemLock` or inject an `override` path `[V — §12.13]`. (b) **`systemLock` is not writable by any op, ever**; the validator rejects any derived patch whose pointer starts `/systemLock` with 400, whichever op produced it (§12.17-A96). (c) A request naming any path outside the allowlist table — including via symlink or `..` — is rejected with 400 and logged.

### 3.3 Write allowlist (normative — supersedes A78's three-shape assertion; NA-B15)

| Path shape | Ops permitted | Constraints |
|---|---|---|
| `pages/*.doc.json` | all node/layout/text/slot/variant ops | canonical serialisation; one file per op batch |
| `content.json` | `set-text`, `set-richtext`, content-mode ops | never touched by layout ops |
| `site.json` | page ops, `set-page-meta`, `set-breakpoints`, `set-grid`, `set-doctor-thresholds` | **`/systemLock` never writable by any op** |
| `assets/manifest.json` | `register-asset`, `set-asset-meta`, `set-alt-text`, `record-derivative` | append-or-update; delete requires no live doc reference |
| `provenance.json` | `record-placement`, `record-variant-swap` | append-only in practice |
| `history.jsonl` | written by the server itself for every applied op | append-only, never rewritten |
| `.wb/**` | `editor.lock`, `session-ui.json`, `doc-hashes.json`, `inbox.jsonl` (read + truncate-after-apply), `conflicts/**` | **`.wb/locks/**` is read-only to the server**; only `wb lock` writes it |

Everything not in the table is rejected. Path resolution: `realpath` → `startsWith(sessionRoot)` assertion → symlinks rejected → `..` segments rejected → **re-check after resolution, not before**.

### 3.4 Server lifecycle

`not-started → launching (rung F1..F5) → bound (same-turn 200) → survived-boundary (second curl, separate tool call) → serving → idle → shut-down`.

- Fixed port **8820** on `127.0.0.1`. **Never a random port.**
- `state.json` = `{phase, step, awaiting, nextAction, port, pid, url, sessionId}` at boot `[V — §12.11; NA-B03]`.
- Bind confirmation: `curl --retry 20 --retry-connrefused`.
- **Survival proof: a SECOND curl in a SEPARATE tool call.** A same-turn 200 is never proof of life (a `run_in_background` server binds, curls 200, then takes SIGTERM/exit 143 at the turn boundary).
- Regenerate-if-stale on startup; heartbeat from the editor page; **idle shutdown after N minutes** — a forgotten dev server left running for days is the realistic exposure, not a targeted attack `[V — §12.12 control 6]`.

### 3.5 Gate 16-A and the launcher ladder (blocking)

**Procedure.** Launch via the candidate detached-spawn mechanism → `curl --retry 20 --retry-connrefused` for 200 in the same turn → **end the turn** → in a separate later tool call curl again and confirm the pid in `state.json` is still in `ps` → repeat across at least two further turn boundaries and once across an eternity `/clear`. **Pass = 200 at every post-boundary check with the original pid alive** (A80).

| Rung | Mechanism | Sign-off |
|---|---|---|
| F1 | TypeScript detached spawn + `unref` | none |
| F2 | TypeScript double-fork (**`setsid` does not exist on this Mac**) | none |
| F3 | ~15-line POSIX `sh` launcher — **preferred fallback**, keeps 100% of the server in TypeScript | none |
| F4 | ~20-line Python double-fork launcher | **required** (standing-language-rule deviation) |
| F5 | User starts the server in their own terminal | **required** (UX regression) |

**If F1–F3 fail and both F4 and F5 are refused there is no known mitigation and the browser-editor premise must be rescoped.** Nothing server-dependent is committed until this gate passes (CQ6, confidence 0.45).

---

## 4. Security architecture

### 4.1 Eight controls (NA-B02 — the carried "six-control posture" is understated)

| # | Control | What it defeats |
|---|---|---|
| 1 | Bind `127.0.0.1` explicitly, **never** `0.0.0.0` | network exposure |
| 2 | Validate `Origin` on **every non-GET and on the SSE/WS upgrade** against a two-entry allowlist | cross-origin state-changing requests |
| 3 | `Access-Control-Allow-Origin` = the exact editor origin, **never `*`** | CORS-granted response reads |
| 4 | Per-session bearer token — 32 random bytes, `.wb/editor.token` mode `0600`, injected into the editor page at render, sent as `Authorization` on every non-navigation request | **drive-by CSRF** from an origin that has never seen the token |
| 5 | Pin the substrate's allowed-hosts setting to the explicit host and pin the substrate version above the fixed advisory | known dev-server CVE classes |
| 6 | Heartbeat + idle shutdown | the forgotten server, which is the realistic exposure |
| 7 | **`Host`-header validation on EVERY request, including the plain `GET /` that bootstraps the editor page** — reject unless `Host` is exactly `127.0.0.1:<port>` or `localhost:<port>` | **DNS rebinding** |
| 8 | `Cross-Origin-Resource-Policy: same-origin`, `X-Content-Type-Options: nosniff`, `Cache-Control: no-store` on the bootstrap, a strict CSP on the editor page, and **never reflect a request header into a response** | sniffing, caching and reflection classes |

**Why control 7 and not control 4 is the rebinding answer** `[V — §12.12, argument written to be auditable; the reasoning itself is marked `[I]` by the source]`: a cross-origin attacker can *send* to `127.0.0.1:<port>` but cannot *read* the response, so the token is not exposed and control 4 stops CSRF. DNS rebinding removes the same-origin argument by construction — the browser now believes `evil.example:<port>` is same-origin, so the attacker reads the bootstrap HTML **including the token**, and an `Origin` check does not help because the attacker's origin is `evil.example` on both sides. The header that does not lie is `Host`: a rebound request still arrives as `Host: evil.example:<port>`. Rejecting it refuses the request **before a response body exists to be read**. Cost: one header comparison.

**Reference anti-pattern in-estate, not to be copied:** an existing local server binds `127.0.0.1` correctly but performs **no Origin check on POST** and no `Host` check anywhere `[V — grep-verified in the source]`.

### 4.2 The Step-3 importer is an unauthenticated code-import channel

Pasted component code lands in the source tree, is evaluated by the preview process, and is bundled into the published site. Treat it as untrusted input.

| Layer | Mechanism |
|---|---|
| **Parse** | Split component files into frontmatter/template/style with the substrate's own compiler; parse JS/TS with a real ESTree-producing parser; parse CSS with a real CSS parser. **A parse failure is a quarantine, never a pass-through** |
| **Resolve** | Walk the AST **with scope tracking**. Flag `CallExpression`/`NewExpression` whose callee **resolves** to a denied binding (`eval`, `Function`, `fetch`, `XMLHttpRequest`, `WebSocket`, non-local dynamic `import()`, `require`, `process`, `child_process`, `fs`, `Worker`, `importScripts`, `navigator.sendBeacon`) — **resolution, not spelling** |
| **Fail closed on the undecidable** | Any computed member access on a global (`window[x]`), any dynamic import specifier, any `constructor` chain, any assembled-then-called string, any `with`, any non-literal `srcset`/`href`/`url()` → **quarantine.** Static analysis of adversarial JS is undecidable in general; the honest posture is "anything I cannot resolve, a human looks at" |
| **Template & CSS** | Remote `<script src>`, remote `<link>`, remote `@import`, remote `url()`, inline event-handler attributes, `javascript:` URLs, `<iframe>`, `<object>`, `<embed>`, `srcdoc` → quarantine. **Every remote origin is simultaneously a determinism violation and a licence-evidence violation**, so this rule earns its keep twice |
| **Tokens** | Validate `tokens.json` as DTCG; reject unknown token types; reject non-literal values |
| **Containment** | Quarantined and newly-accepted items render first in a **sandboxed iframe** (`sandbox` without `allow-same-origin`) under a strict CSP with **no `connect-src`**, so a first render cannot exfiltrate |
| **Human gate** | The quarantine list is a rendered diff with the offending node highlighted; nothing leaves quarantine without an explicit **per-item accept** recorded in `inbound/import-report.json` |

**Honest limit, stated not implied** `[V — §12.14]`: the paste's author is the user's own generation session, so the realistic threat is a *mistake* (a copied snippet with a CDN font, a component that calls an analytics endpoint) or a *prompt-injection-induced* insertion — not a determined attacker with full input control. This validator is a **mistake-catcher and supply-chain-tamper detector with a fail-closed quarantine, not a sandbox-escape-proof boundary.** If the threat model changes, the answer is process isolation, not a longer denylist.

**Functional (not only security) consequence:** partial or malformed paste-backs will happen on most runs, so per-item accept/reject with a "retry just these three" prompt is a **functional requirement**; a hard-failing importer stalls the pipeline at paste #1.

### 4.3 Ingest integrity (truncation, which is not a security problem but fails identically)

Envelope manifest per generation: declared file list · per-file line counts · sha256 prefixes · smallest-first ordering · **per-run random terminator**. A truncated chunk fails with a message naming the missing files and **writes no partial system** (A8). Silent truncation otherwise produces syntactically valid, semantically wrong CSS with no error anywhere (R3) — tokens cut at 40 of 62 properties render fine.

---

## 5. Persistence, concurrency and history

### 5.1 Two-tier truth

**Composition** (`pages/<id>.doc.json` + `content.json` + `site.json`) is the only thing the editor mutates. Implementation files are versioned on disk. The rendered site is produced by a pure function `render(doc, systemLock, library) → files` and is **never parsed back into JSON**. The DOM is never the source of truth; there is **zero DOM serialisation and zero DOM injection for hit-testing** (R4).

> **NA-07 naming.** Canonical scene graph = `pages/<id>.doc.json` + `site.json` `[V — §12.2 file set, §12.13 write allowlist]`. `layout.json` is a **legacy alias**; the rename must complete before implementation.

### 5.2 Canonical serialisation (purity gate 8's precondition)

UTF-8, LF, trailing newline, no BOM · fixed key sequence per node type then unknown keys sorted lexicographically · 2-space indent, one array element per line · shortest round-trip numbers, no `-0`, no exponents · booleans and `null` explicit · **absent optional keys omitted entirely rather than written `null`** (so §12.3's key-presence test for "overridden here" stays valid) · non-ASCII written literally, never `\u`-escaped.

`wb verify` re-serialises every doc-owned JSON file and requires a **zero diff**. This is what stops a hand-edit, a different formatter or a future library upgrade from silently reformatting a file and producing a 4,000-line diff that hides the one real change (§12.17-A98).

### 5.3 Concurrency: reconciliation is the authoritative mechanism (research F12)

Ranked, each with its stated limit:

| Rank | Mechanism | Limit |
|---|---|---|
| **1** | **Out-of-band-write reconciliation** — `.wb/doc-hashes.json` + a watch on the doc-owned set. Any doc-owned file whose on-disk hash diverges from the journal without a server-issued write raises a conflict **before the next save is accepted**, and the divergent version is copied to `.wb/conflicts/<iso>/` first | **Holds against Bash heredocs, `sed -i`, a second editor, anything.** If the watch API is unreliable, fall back to a hash re-check immediately before every save and on window focus — **and say so in the status bar. A silently-degraded conflict detector is the failure this exists to prevent** |
| 2 | **Optimistic concurrency** — every save carries the mtime/hash it loaded; a stale write is rejected **409** and the editor offers reload / force / open the conflict copy | needs a live client |
| 3 | **`editor.lock`** (pid + mtime heartbeat) + an **SSE tab claim** (second tab read-only) | covers processes and tabs, not out-of-band writes |
| 4 | **PreToolUse ownership guard** — blocks `Write`/`Edit` on doc-owned paths and scans Bash command text | **a heuristic, defeatable by indirection.** Demonstrably cannot catch what rank 1 catches |
| 5 | `chmod 0444` while the lock is held | **a speed bump** — same uid can chmod back (`§12.7-O34`, no in-scope mitigation) |
| 6 | `.gitattributes` marking generated output, a pre-commit hook, the generated banner | advisory |

**The agent gets a legal write path** (research F13): `wb op '<typed op JSON>'` posts the same typed op the browser posts, through the same server, inheriting validation, the op log, optimistic concurrency and the SSE push. When no editor process is running, `wb op` starts a headless one, applies, and exits — **so the agent path is never blocked on a browser being open.** The skill's instructions state this in the imperative, because an instruction the agent follows is cheaper and more reliable than a guard it can accidentally evade.

### 5.4 History, undo and durability

`history.jsonl` = append-only `{seq, ts, actor, op, target, patch, inverse, label}`. Undo/redo is a **single command stack over the doc**, covering canvas drags, inspector edits and text edits alike, mirroring the server-authoritative op log; a continuous drag coalesces into one entry. **Transactional grouping is mandatory and tested**: a component swap or a section regeneration is **ONE** undo step (A31, A32) — a naive per-mutation stack leaves a broken hybrid after one Cmd+Z (R22).

**Durability is the op log + atomic writes + hash reconciliation, not a commit per save** (NA-B07 `[V — §12.10, amending R6's carried mitigation line]`). Git commits happen at milestones; `wb autosave --git` is opt-in. `site/` is **its own git repo**, and `.acos/website-builder/sessions/*/site/` is in the ACOS `.gitignore`, otherwise every milestone commit pollutes ACOS history and every `wb-lock/<n>` tag collides (A83, NA-B11).

Delete uses a **recovery bin independent of the undo stack**, with restore-in-place. `trash[]` entries are retained unbounded within a project and **stripped at LOCK**.

---

## 6. Determinism contract

Generation is a **pure function of `(doc, system.lock.json, generator version)`**. Every generated file carries `@generated`, `doc-sha256`, `system-lock-sha256`, `generator-version` and **no timestamp**.

The six hazards, designed out rather than tested for:

| # | Hazard | Design |
|---|---|---|
| 1 | Key/iteration order | one fixed key comparator, applied everywhere |
| 2 | Absolute paths leaking into output | relative paths only |
| 3 | Locale-dependent sorting | fixed collator / `LC_ALL=C` |
| 4 | Regenerated ids | node ids are ULID-derived and **never regenerated** |
| 5 | Binary re-encoding | pinned asset encoder recorded per asset as `{encoder, encoderVersion, settingsHash, outputSha256}`; **hash comparison, never re-encoding** — encoders are not bit-stable and re-encoding manufactures false positives (research F14) |
| 6 | Ambient inputs | no clock, no network, no `Math.random`, no `process.env`, no outside-filesystem reads at generate time; frozen `SOURCE_DATE_EPOCH` |

**Why this is load-bearing:** `verify` is the drift guarantee. A verify that produces false positives teaches the user to ignore it, after which the guarantee is gone **while still appearing to exist** (R15, NFR-12). Acceptance: `verify` produces an empty diff on a freshly generated project **and** after ten drag operations (A53).

---

## 7. Renderer, resolution and migration

### 7.1 The renderer

`render(doc, systemLock, library) → files` is **pure and total**, and the *same* renderer serves the design surface and LOCK, switched by `editor: false` (D3). Zero editor artifacts are emitted when the flag is false — not stripped afterwards, **never emitted**.

### 7.2 Resolution policy (normative — applied at editor open, at generate, and at lock gate 6) `[V — §12.16]`

| Case | Policy |
|---|---|
| Unknown **component** id | **Hard fail.** The editor opens read-only in a "migration required" state listing every affected node and page; generate and LOCK both refuse. *A missing component has no honest substitute — a placeholder here is a hole that ships* |
| Known component, unknown **variant** id | Fall back to the direction's **canonical variant**; write `node.variantMigrated = {from, to, reason, at, auto:true}`; per-node badge + review queue; **gate 6 blocks LOCK until every flag is acknowledged** (per node, or bulk with one confirmation naming the count) |
| Variant resolves, **slot contract changed** | Slot content moves to `node.orphaned.<slotName>`, is surfaced in the editor, and is **never deleted by a migration.** A migration may relocate content; it may not destroy it |
| Prop removed/renamed | Apply the imported system's migration map if present; else reset to the variant default and flag per node |
| Unknown **motion** preset | Fall back to `motion.none`, flag, acknowledge before LOCK — **the same code path as a variant fallback**, because per D4 motion is a prop on an art container, not a parallel subsystem |
| Unknown **token** name | **Hard fail at generate time**, naming the token — a missing custom property otherwise degrades to an invalid CSS value and a silently wrong colour |
| Asset id absent from `assets/manifest.json` | **Hard fail** — the manifest is the allowlist |
| Doc `formatVersion` **newer** than the tool | Refuse to open, name both versions. **Never best-effort-parse a future format** |
| Doc `formatVersion` **older** | `wb migrate --format` applies ordered migrations after snapshotting to `.wb/locks/pre-migrate-<iso>/` |

### 7.3 `wb migrate [--to <systemLockSha>] [--format]`

1. Snapshot current docs to `.wb/locks/pre-migrate-<iso>/` **before touching anything**.
2. Diff old vs new `system.lock.json`: components added/removed/renamed, variants added/removed/renamed, slot and prop schema changes, token additions/removals.
3. Produce a **plan** and show it before applying — counts per rule, full node list on request.
4. Apply as **typed ops through the same server path**, so every change lands in `history.jsonl` with `actor:'agent'` and is individually undoable. **A migration is not a special bypass.**
5. Write `migration-report.json`; update `systemLock` in `site.json` — **the one write no HTTP op may perform.**
6. Leave the acknowledgement flags in place. **Migration proposes; the human accepts.**

> **§12.16-O35 (new open question, NA-B04):** whether `wb migrate` should attempt **semantic** cross-direction variant matching (slot-signature) instead of canonical fallback. Semantic matching preserves intent and is what makes the v2 cross-direction swap pleasant; it is also a heuristic that can confidently produce a wrong answer. **v1 = canonical fallback only, always reviewed.** No known mitigation removes the risk.

---

## 8. Design-system pipeline

### 8.1 Step 2 — prompt generation

- **`font-catalog.json`** is a skill-owned, cross-project resource at `.acos/website-builder/library/font-catalog.json`: `{familyId, classification, foundry, oflSourceUrl, fileHash, glyphCoverage, preSubsettedCuts:{latin, latinExtended}}`. Base64 cuts are computed **once, locally, ahead of time — never by the web model.** A hash-pinned copy is snapshotted to `01-prompt/font-catalog.snapshot.json` at Step-2 start, so a mid-run library refresh cannot change what a session is judging. 24–32 OFL families (OQ-09), a starting number.
- **`token-manifest.json`** is generated **mechanically** from the §7 item list — names only, no values — before any prompt is emitted, and re-pasted verbatim into every chunk.
- **Stage A** requests direction capsules (a 26-slot vector + a 40–80 word manifesto each) plus a gallery artifact previewing all directions as hero cards at **both** a desktop frame and a **390px-wide portrait frame**. Capsules are **over-generated**, machine pre-filtered on the self-audit fields (hue-anchor collisions, anti-slop deny-list hits), then cut by the user down to the ~10 D1 floor; any relaxation is recorded in `session.json` as a signed-off D1 deviation.
- **Stage B** reuses prompt sections 0, 2, 4, 5 verbatim and replaces section 3 with the full DTCG expansion plus identity-carrying component instances for one direction.
- Every emitted design directive **cites the interview question id that produced it** (A4).
- Greppable Stage-A contents (A6): the DTCG worked example, the OKLCH hue warning verbatim (*"hue 0deg = magenta, not red; red is ~41deg"*), the pinned font shortlist with base64 display cuts, the frozen token manifest + prior-identity negative constraints, the CSP constraint, the 390px preview requirement, the self-audit instruction.
- **Chunking is computed from measured artifact sizes at runtime**, never from a published ceiling (`§17-O2`/CQ18 is unknown and its published figures are unreliable — one referenced model name appears fabricated). The usage-tier cost is surfaced up front (R46).

### 8.2 Step 3 — ingest

Tolerant parser splitting on fenced `FILE:` blocks → envelope validation → AST validator (§4.2) → deterministic re-verification of **every claimed contrast pair** (auto-nudge failures, log to the substitution log) → font substitution to the nearest OFL match in the same classification, logged → `templateVersion` range check with a defined upgrade path → quarantine of everything undecidable → repair-prompt emission for "retry just these three".

**Local Regeneration Mode** runs the identical prompt through a Claude Code path and produces a bundle that passes the **identical validator with zero pastes** (A12). This is what makes the web hop a UX preference rather than a technical dependency (R7).

**The anti-slop lint is a hard gate upstream**, on the generated design-system JSON, *before* the human sees the menu of choices — and a Tier-2 advisory with permanent per-element dismiss at the human-edit layer.

### 8.3 Token compiler (E6)

One importer emits **both** DTCG token JSON **and** the design-system-forge `design-system-spec.yaml` (both consumers exist and the second is cheap). Compile to CSS custom properties + a Tailwind `@theme`. Pin the compiler version; commit the lockfile.

- **~600–900 resolved tokens per complete direction** `[V — counted programmatically from three published systems]`; the user's "~80 items" is an *item* count, each expanding to 1–40 tokens.
- Compile the full custom-property set to a **flat variable layer once per direction change**, never re-resolved per drag (R30, NFR-11).
- Every token carries `com.acos.llm`, `com.acos.pick`, `com.acos.direction` (A14). The editor renders **no control** for `pickable:false` (A15). A token whose `com.acos.direction.vectorHash` differs from the active direction is **rejected by the builder** (A16).
- **Derived families with no editor control** (A24): spacing, type steps, radius scale, shadow scale, semantic colour roles — **and font fallback metrics** (`size-adjust`, `ascent-override`, `descent-override`, `line-gap-override`), which are computed from the real selected font binary and therefore **cannot be produced by the generation channel at all** (research F17). This family is not yet named in the token taxonomy; naming it is a build prerequisite.
- `in-direction-repickable` rows ship a per-direction **validity list** in `token.capability-manifest`; options absent from the active direction's list are **hidden from the UI**, not merely warned about. A row that cannot supply a validity list is demoted to `direction-slot`.
- `tokens.css` is **machine-owned**; `extract-override.ts` is the sanctioned hand-tune path (`§17-O25`).
- Light and dark schemes are **independently solved**, and the contrast proof table covers both (A19).

### 8.4 The coherence-lint set — versioned, not counted (NA-05)

Required members, by name: **elevation-model lint** (a direction with `elevation.model: border-only` referencing any shadow token fails — A17) · **logical-properties-only lint** (`margin-inline-start`, `padding-block-end`, `inset-inline`, `border-inline-start`; never `left`/`right`/`top`/`bottom`/`margin-left`/`text-align: left`), run **at ingest and at LOCK** · **§7's lints 7–10**, validating direction-bound authored artefacts against the identity vector. The set carries a version number; gates cite the version, never a count.

---

## 9. Layout and canvas — technical specification

### 9.1 Breakpoint vocabulary (normative, shared by switcher, cascade, free-position rules, save format and gates)

| Key | Media query | Tracks | Previewed at |
|---|---|---|---|
| `base` | none | 12 | 1280 and full |
| `md` | `max-width: 991px` | 6 | 768 |
| `sm` | `max-width: 479px` | 4 | 390 |

Emission order `base → md → sm`, so the narrower rule wins by source order **with no `!important`**. The authored default is the desktop layout; **there is no key above `base` in v1** (`§12.3-O32`: an `xl` tier would introduce the only upward override in an otherwise desktop-down cascade). A doc containing an upward key is **rejected by the schema validator** with a message naming the desktop-down rule (§12.17-A92). 1440 is a **preview-only** fifth switcher option carrying no overrides (OQ-08).

`base` is mandatory on every node; `md`/`sm` are written **only where the user actually overrides**, so "overridden here" is a *key-presence* test. **A node with no `sm` entry compiles to `grid-column: 1 / -1`** inside the `sm` media query (A41, §12.17-A91).

> **NA-06 (carried):** the free-position **auto-demote trigger is ≤390px** while the `sm` **media-query boundary is ≤479px**. They are *not* identical, and 479 is a width no switcher, preview frame or gate ever renders — a user could never watch the demotion fire. Both call sites are recorded as a required cross-section fix (`§12.3-O31`).

### 9.2 Gridline overlay

Drawn by reading `getComputedStyle(section).gridTemplateColumns` and painting **those exact resolved tracks** — never a hand-authored decorative grid, because the overlay *is* the snap target (A39). It lives in the **out-of-iframe overlay**, so it disappears at LOCK **by construction** rather than by scrubbing.

### 9.3 Placement mathematics

```
col = clamp(1, round((x − gridLeft) / (colWidth + gap)) + 1, cols + 1)
row = clamp(1, round((y − gridTop)  / (rowUnit + rowGap)) + 1, sanityRowCap)
```

- Persisted value is `grid-column: <start> / span <n>` — **integers, inherently fluid**. A block spanning 6 of 12 occupies 50% at both 768 and 1440 (A40).
- The row axis is **explicit**, sized from the direction's spacing scale via `grid-auto-rows: var(--wb-row-unit)`. `sanityRowCap ≈ 200` is a **runaway-drag reject, not a layout constraint**.
- **Span preservation:** a dragged block keeps `colSpan`/`rowSpan`; `colSpan` clamps to `min(colSpan, targetCols)` anchored at the drop column when the target section is narrower, and the clamp is shown in the pre-commit chip **before** commit. `rowSpan` is never clamped.

### 9.4 Occupancy and the drop algorithm (AC1–AC9, normative — NA-17)

- **Displace-down by default:** overlapped siblings shift by the dragged block's `rowSpan + rowGap`, cascading, with a **live ghost preview of every block that will move before pointer release**.
- `role: "art"` blocks resolve by **z-order** instead.
- A per-drop **"Allow overlap here"** opt-in writes an explicit `z` and increments a **visible overlap counter**.
- **Cross-section drops re-parent** the node with **no auto-compaction anywhere in the document**; boundary-zone drops append to the nearer section's near edge and **never merge grids**.
- **Reject (snap back with an outline flash) only structurally illegal drops:** onto another block's internal flow-only region; where the displacement cascade would reflow a step inside a reflow-forbidding pinned/scrubbed container; or where `row` would exceed `sanityRowCap` — **an inline message, never a silent clamp**.

### 9.5 Snap engine

Two **1-D interval indexes per section** over four prioritised target classes:

1. grid lines → 2. sibling edges/centres → 3. section padding and content rails → 4. spacing-scale increments.

Tolerance **6–8 CSS px divided by zoom**, which keeps snapping usable at 25% and 200% (A47). Smart alignment guides carry **live distance labels in the accent colour**, plus equal-spacing indicators when 3+ siblings match. Span resize is by whole cells with a live **"6 of 12 · 50%"** readout, so the user learns the fluid consequence rather than memorising a number. Padding/gap drag handles snap to **discrete spacing-scale steps only** and display the **token name** (`space-6`), never a raw pixel value (A28) — *this is the mechanic that stops direct manipulation destroying the token system*.

### 9.6 The three verbs, and keyboard parity

The anchor/pin control exposes **exactly three verbs**: *align to* (left/centre/right/stretch), *space above/below* (a stepper over the scale), *order* (up/down among siblings). This is R8's core mitigation — "move the hero headline 12px up" is otherwise a four-way CSS puzzle.

**Keyboard nudge and grid stepping are not a convenience**: Arrow = one cell, Shift+Arrow = span ±1, Tab walks siblings — and this **is the WCAG 2.5.7 single-pointer alternative for every drag** (A26). Editor chrome must independently satisfy **2.5.8** (≥24×24 CSS px, four documented exceptions), checked by a **live bounding-rect check on render**, not only at lock (A27). Thin drag handles, tiny corner grips and dense icon rows violate this by default (research F5).

### 9.7 Override cascade

Desktop-down only; sparse overrides; a **structurally prominent** persistent breakpoint indicator (not a forgettable dropdown); a **pre-commit chip** naming exactly which sizes an edit affects with one-click *"apply to all sizes instead"* (A42); an **"overridden here" dot** per overridden property; one-click **reset-to-inherited**. Override accumulation escalates at **≥5 per page (amber), ≥15 (red finding — LOCK proceeds but the count is recorded), ≥40 per site, ≥25% of a page's nodes** `[I — stated starting numbers, tunable in `site.json`; NA-14]`.

### 9.8 Reading order (NA-18, normative)

**DOM order *is* the reading order.** Visual order is achieved only by grid placement, **never** by reordering the document tree. The single exception is a per-breakpoint `order: {bp, value}` override that:

(a) raises a persistent *"Reading order will differ from what's shown here"* chip; (b) is **hard-blocked on any focusable node** (WCAG 2.4.3); (c) warns on non-focusable nodes (WCAG 1.3.2).

Before **any** commit that changes mobile stacking, the editor renders a **numbered list preview** of the resulting top-to-bottom mobile sequence.

### 9.9 Free position (the escape hatch, deliberately narrow)

**Anchored offset, not raw absolute.** The element keeps a declared anchor and the drag writes a percentage/`clamp()` offset. **v1 restricts the anchor target to `parent` or a grid line/cell**; sibling anchoring is deferred behind an **unprototyped** subgrid-promotion strategy (OQ-05 / DECISIONS item 6) and CSS anchor positioning is ruled out for load-bearing layout. **Runtime positioning JS is forbidden in the locked export.**

Also mandatory: reserve `min-block-size` on the parent at drop time (A45); per-block **and** per-breakpoint; **auto-demote at the small breakpoint** using an **authored** `flowFallback: {col, colSpan, row, order}` written at drop time and independently editable in the Navigator; drop z-stacking at that breakpoint unless `flowFallback` carries an explicit `z`; cap ~2 per section with a **visible counter**; **disabled by default on pinned/scrubbed containers** (forcing requires explicit confirmation — A48); and **fails LOCK** if it produces document `overflow-x` or leaves its parent's box at any checked width (A44).

> **R9 residual, stated not solved:** for art whose composition depends on absolute relationships across the viewport, the only answer is to treat the composition as **one component with internal responsive rules** — which means the user cannot drag its parts individually, which is exactly what they asked for. **No better answer exists.**

### 9.10 Component internals

Component internals use `@container` with `container-type: inline-size` on **every block wrapper**, never `@media`, so moving a card from a 6-col to a 3-col slot needs no manual fix (A46). ~12 section archetypes ship as `grid-template-areas` per direction; the moment a user drags a block off its area, **that block only** is promoted to explicit integer placement on the same grid.

### 9.11 Preview frame

The preview is a **same-origin iframe** — a scaled `<div>` cannot evaluate media queries. Device heights are **pinned** (390×844, 768×1024, 1280×800, 1440×900) whenever the page contains any `vh`/`svh`/`dvh` rule, and the **measured** iframe height is asserted rather than assumed (gotcha 12: an auto-height iframe makes `100vh` resolve to the iframe height, so a hero is approved at a height no device has).

---

## 10. Components, variants and slots

**A variant is a structurally distinct composition of the same component within one direction.** Size, theme, density, state, icon-slot and semantic colour are **computed axes** and never count against the variant budget — this line is what keeps the budget finite (research F18; without it the same product category yields "5 buttons" in one library and "940 variants" in another).

- **Distinctness is machine-checkable:** every component declares a **variant axis vector**; two variants are distinct if their vectors differ in ≥1 axis. The axis schema is **hand-authored in the skill** for determinism (OQ-11), with its own effort line.
- `variants.ts` is a **deterministic generator** over the direction's tokens — **no model call, no subagent writes** (subagents are policy-blocked from `Write`; verified twice, first-party `[V]`).
- **Lazy:** generated on first open of a family's swap panel, cached per direction, **never pre-generated for unused families** (R29 — eager generation stalls Step 4 at ~120 variants per direction).
- "More variants" appends the next N using the skill-supplied current highest index (**append-only, collision-free**); "more like this" appends **5 deterministic neighbours** of an approved variant.
- **No two variants offered in the same bar may be indistinguishable at 200×120px** (A34) — the safeguard is distinguishability, not count (research F19).
- **Typed slot contracts** `{name, type, cardinality, required}`. The bar offers **only** variants whose contract is a superset or exact match, and states before the swap: *"this variant adds N slots"* / *"this variant has no place for: [x]"*.
- **Content orphanage:** anything the target cannot hold moves to a **visible parked panel**, is **never deleted**, and is auto-restored if a later swap re-introduces the slot (A29).
- **New empty slots render as visibly flagged placeholders that BLOCK LOCK** until filled or deleted (A30) — *this is what prevents fake statistics shipping.*
- A swap replaces the node **in place**; tab order before and after is identical for equivalent content (A38). A swap is **one** undo step (A31).
- **Global/shared component with instance overrides is a prerequisite for safe variant swapping** — build the data model before the component-bar UI.
- **Cross-direction swaps are out of v1** (only one direction is generated in full). The v2 design is already fixed: both renderings side by side ("Fitted to your direction" / "Kept as designed (adds N off-system values)"), transplants recorded in a visible **coherence-debt ledger**, a whole-site direction switch offered at a soft cap of ~3, and it **never blocks**.

**v1 volume of record:** 216 rows / 1,228 variants is the inventory `[V — §8.2/§8.3; NA-02]`; the **v1 build target is 88 rows / 675 variants** (87/674 from DECISIONS item 2 plus the skip-link row gate 11a requires — NA-B08). Radio group and Toggle switch are **non-demotable**. The v1 cut list must be regenerated **mechanically from the priority column**, never asserted.

---

## 11. Motion and art containers (D4)

**One container contract covers art and motion**, carrying: `boxSizing, aspectPolicy, anchor, overflow, mask, schemeAware, motionCapable, reducedMotionPoster, reducedMotionVariantRef, focalPoint, altText|decorative, licenseRef, trigger, viewportThreshold, source{kind, ref, poster}, playback{autoplay, muted, loop, iterationCount}, costClass, tokenRefs[]` — **plus `pauseAffordanceRef`**, which §13.4 gate 13a requires so an unpausable marquee/ticker/ambient layer is **structurally unbuildable** rather than caught late at LOCK.

Seven rules, each enforced at validation time:

1. Explicit `aspect-ratio` (or `min-block-size` from the ratio scale) is **mandatory**, so the grid row is reserved before the asset initialises.
2. Animation inside a container may only touch `transform`, `opacity`, `filter` — and may **never** change the container's grid placement, width or height.
3. `trigger` is a closed enum: `page-load`, `viewport-enter`, `viewport-scrub`, `pointerenter`, `click`, `always`; `viewportThreshold ∈ [0,1]` (default 0.2) is meaningful only for `viewport-enter`.
4. `reducedMotionVariantRef` is **mandatory whenever `motionCapable: true`** — validation fails without it. The reduced-motion render diff must **differ** where motion exists, and still look designed (A22).
5. `source.ref` **must** resolve against `assets/manifest.json`; a container with no asset of its own sets `source.kind: 'none'`.
6. `muted` **must** be true whenever `source.kind: 'video'` and `autoplay: true` — a field-level constraint.
7. `costClass ∈ {free, cheap, heavy, gpu}` is assigned per container **kind**, not per instance, and is what the concurrency caps are computed against.

**Concurrency caps** (per page): max 1 GPU-class scene, max 1 particle/ambient layer, max 2 autoplay video loops, max 2–3 pinned/scrubbed sequences, enforced **structurally with per-container attribution**, and surfaced live as a **running counter** so the human watches the count accumulate turn-by-turn rather than discovering it at LOCK `[I — carried over, not benchmarked against this render stack; a starting default, not a validated ceiling; NA-15/OQ-10]`.

The component bar presents **Style and Motion as two tabbed pickers** for dual-axis kinds — never a flattened cross-product list.

> **R14, no known mitigation.** Motion is **disabled in edit mode** because the editor runtime fights the site runtime (a smooth-scroll library lerps `scrollTop`; transform-based animation poisons `getBoundingClientRect`). Motion feel is judged in **preview mode**. Human-in-the-loop does not solve this; it relocates it. Automated visual scoring is forbidden — VLM recall of aesthetic animation measured **0.16** `[U — prior report, flagged unvalidated end-to-end]`, so acceptance rests on the human plus deterministic motion lint (CQ12, confidence 0.35).

Artwork lanes: **A** code-drawn/token-parameterised (≥60% of a 20-artwork set token-referencing via `currentColor`/`var(--*)`, re-skinning on hue-anchor change **with no regeneration** — A20, A21); **B** asset-library ingestion into `assets/manifest.json` with direction-affinity tags and a licence class; **C out of v1** — a runbook at `docs/lane-c-raster-runbook.md` whose output ingests through Lane B's manifest. The asset pane ships **direction-affinity filter chips** — *the chips are what makes presenting 20 artworks legal* (R34). Warn at **interview time** when a project has no asset library (R1/OQ-12): there is **no known mitigation that preserves the paste-only path**.

---

## 12. Quality gates and capture

### 12.1 Live vs lock-time

The dividing line is **scoped arithmetic/DOM-read vs whole-document render pass** — not "a11y vs performance". Live checks: **sub-100ms**, fire on **drop/mouseup only** (never mid-drag, never per-frame), scoped to the touched subtree. Lock-time checks: whole-document, batch.

**Live set:** contrast recompute (WCAG 2 ratio **and** APCA Lc on every touched pair) · target size via `getBoundingClientRect()` flagging <24×24 unless an exception applies · scoped accessibility-engine run on the touched subtree · overflow/clipping via `ResizeObserver` + `scrollWidth > clientWidth` · focus-not-obscured intersection · reading-order-vs-visual-order walk · reduced-motion sibling presence · **alt/decorative gate that blocks the placement** · image auto-optimisation on drop · budget HUD · **motion-concurrency running counter**.

**Severity tiers.** Tier 0 blocks the individual placement/edit inline. Tier 1 blocks **LOCK only** and never interrupts live editing. Tier 2 is advisory, dismissible, batched into the Design Health pill — **never a toast stream** (A37). Tier 3 is silent end-of-session record. Debounce to drop/mouseup; collapse repeated violations into one counted badge.

`gates.ts` returns **structured verdicts** `{gateId, tier, status: pass|fail|inconclusive, measured, threshold, evidenceRef}` and **never throws on a normal fail**. **INCONCLUSIVE blocks exactly like a fail.**

### 12.2 The 32-check lock-time checklist (NA-04)

28 base gates plus lettered insertions **4a** (motion-concurrency caps), **11a** (skip-link presence and first-tab-order — a Level A gap), **13a** (pause/stop/hide affordance — Level A), **23a** (asset-reference resolution). Ordered **cheapest-and-most-foundational first**. Three of these carry unfinished cross-section build prerequisites (research F6): the skip-link **component** does not exist in the inventory (NA-B08), the container contract needs `pauseAffordanceRef`, and the token taxonomy must name the font-fallback-metrics family.

Canonical thresholds (NFR-04, gate 20 — **A66 omits INP and A67 states a flat ≤2MB; both are subordinate and recorded as inconsistent**, NA-16): **LCP ≤2.5s · CLS ≤0.1** (internal stretch 0.05) **· INP ≤200ms** (or TBT ≤600ms floor / 300ms aspirational as proxy) **· pre-LCP transfer ≤1.5–2MB** (not total page weight), median-of-3, mobile, simulated Slow-4G + 4× CPU.

Reflow (NFR-07): no two-dimensional scroll at 320 CSS px except exempted content (A60) · a 40-char unbroken token produces no overflow (A61) · **+35% pseudolocalisation** produces no overflow or truncation (A62) · 200% zoom produces no horizontal scroll and no content loss (A63).

Accessibility floor: **WCAG 2.2 AA is the contractual floor, WCAG 2 is the pass/fail gate, APCA is advisory** (Lc75 body / Lc60 large-bold / Lc45 large-non-text `[U — inherited, not re-verified]`). Selected AAA items (2.4.13 Focus Appearance, 2.3.3 Animation from Interactions) are **aspiration, not gates**. **Never claim conformance:** automated tooling catches **57.38%** of real issues `[V — 13,000+ page-states, ~300,000 issues]`, so the only honest claim is *"Automated accessibility gates passed: N. Manual and screen-reader review not performed."* (A72, A73.)

SEO/structured data (NFR-18): unique title per page · 50–160-char description · canonical URL · OG + Twitter with image · `<html lang>` matching the interview language · **single `<h1>`, no skipped levels** · 100% alt coverage · `robots.txt` + `sitemap.xml` generated from the page tree · JSON-LD matched **1:1** to the site-type answer and validating against schema.org (A69, A70). **No-JS** (A71): content visible, nav usable, forms submittable with JavaScript disabled — also the crawler's view.

Fonts (NFR-20): `font-display: swap` on every `@font-face` · exactly the committed families preloaded · **a fourth family introduced by a late swap fails the gate** · every `@font-face` ships a **metric-matched local fallback computed from the real font binary**, with font-swap-attributable CLS ~0 (A68).

### 12.3 Capture

Plain Chrome CLI headless, **zero npm dependencies**: `--headless=new --disable-gpu --no-sandbox --hide-scrollbars --virtual-time-budget=4000 --screenshot=<out> <url>`, asserting `[ -s "$out" ]`. The inherited wait recipe is re-expressed in TypeScript: **navigate rather than set content**; network-idle with a load fallback; **strip `loading="lazy"`**; `document.fonts.ready` **plus** per-image `decode()`; a 500ms deferred-CSS settle. **`await document.fonts.ready` before ANY `getBoundingClientRect`**, in editor and capture alike.

Any capture used to judge a viewport-height layout **pins the window *and* the preview iframe to a real device size and asserts the measured iframe height**. Full-page tall captures are valid for **content review only** — never as hero-framing evidence. If scripted interaction capture is later needed: `bun add playwright` **inside the skill**, never via an evictable npx cache.

---

## 13. LOCK pipeline (D3)

**`build → scrub → assert → snapshot`. A re-render with `editor:false`, never a copy-and-strip** (`§17-O6`, described as the single most consequential architectural decision in the eight steps; A49–A59 are all written assuming re-render).

### 13.1 Five layered editor-absence mechanisms

1. **Two configs / two commands / two out-dirs** — the editor is not in the publish build graph at all.
2. Dev-only injection **gated on the build command**.
3. Dev-toolbar-class chrome that **physically cannot leak**.
4. `import.meta.env.WB_DESIGN` guards **explicitly defined as `false` in the publish config** — an *undefined* variable may not be tree-shaken (filed bug).
5. A post-build hook that **scrubs every emitted HTML file and then asserts**.

### 13.2 The eight purity gates (NA-03 — not five)

| # | Gate | Method |
|---|---|---|
| 1 | Zero editor strings in the published tree | `grep -r 'data-wb-'` and the dev-runtime patterns → any hit **fails the build** (A49, A50) |
| 2 | **Two-build equality** | sorted-path + SHA-256 manifest comparison, built in a **clean `git worktree`** against a committed editor-free dependency set, with `SOURCE_DATE_EPOCH` / `TZ=UTC` / `LC_ALL=C` / pinned runtime for both builds (A51) |
| 3 | Published JS byte-size assertion | threshold in `gate-report.json` |
| 4 | **Screenshot diff** | editor preview at 1280 (chrome hidden) vs the built page at 1280 → **zero pixels** (A52) |
| 5 | Interaction-manifest check | every declared motion/interaction behaviour exists in shipped code (A57) |
| 6 | **Zero unresolved references and zero unacknowledged `variantMigrated`/`orphaned` flags** | fails with the **node list, not a count** |
| 7 | **Zero design-time origins** | grep `localhost`, `127.0.0.1`, `0.0.0.0`, `file://`, the session port and the session root path across `srcset`, `<meta>`, inline `style`, CSS `url()`/`@import`, JSON-LD and sourcemap comments (§12.17-A93) |
| 8 | **`wb verify` clean at lock time** | regenerate to temp, `diff -r` the text files, hash-compare binaries **separately**, and re-serialise every doc into canonical form requiring a zero diff (§12.17-A98) |

**Gate 2 isolation (non-negotiable):** it **never** edits the live `package.json`, the live lockfile or the live dependency tree, so a design server running in another terminal is unaffected (§12.17-A94). Budget **≤3 minutes**; above **5 minutes** it demotes to CI-only with an explicit `gate2: waived-local` entry in `gate-report.json` — **a recorded waiver, never a silent skip**.

> **NA-B11 caveat (toolchain):** §12.5's gate-2 procedure is written against an `npm ci` + publish-manifest pair while the skill's own code is Bun TypeScript. The **site build toolchain is whatever the substrate spike selects**; gate 2's installer invocation and publish-manifest filenames must be **re-derived from that outcome**, not copied verbatim (NA-11).

> **NFR-13 / `§12.5-O33`:** **no consulted source establishes bundler-level byte reproducibility across two installs.** If the spike fails, the fallback is **normalised comparison** — identical file list, identical SHA-256 for every file except a **named, enumerated, individually justified** exception set recorded in `gate-report.json` — and adopting it **weakens D3's proof and requires explicit sign-off** (research F15: a gate that fails spuriously gets disabled by whoever is trying to ship).

### 13.3 Non-mutating, reversible

LOCK writes **only** `dist/published/` and `.wb/locks/<iso>/`, then tags `wb-lock/<n>`. `pages/*.doc.json` mtimes are unchanged (A54). **UNLOCK is restarting the design server** (A55). Export is **write-to-new-dir-then-swap**; **no `rm -rf` anywhere in the export path** (A59 — the Oracle scores destructive commands +5).

LOCK **strips** the recovery bin, `node.locked` freeze flags, per-section notes and asset-library pane state from published output; `assets/manifest.json` stays in the project and in the evidence bundle.

**Snapshot contents** (`§17-O26`): every doc, `site.json`, `content.json`, `system.lock.json`, `assets/manifest.json`, the dist hash manifest, the scrub output, `lock-manifest.json` and `gate-report.json`. **`dist/` is excluded — it is reproducible.** `.wb/locks/**` is **committed** (it is the durability story); `.wb/tmp/**` and `.wb/conflicts/**` are git-ignored.

**The one uncovered case, named explicitly:** hand-edits inside the exported tree. Mitigation = a generated-do-not-hand-edit banner, a per-file SHA-256 manifest diffed at both unlock and the next LOCK as a **blocking prompt** (A58), and a best-effort, **explicitly fallible** `extract-override --from-dist` re-homing path **that refuses rather than guessing**.

Restoring an older lock restores **documents and the system lock together**; if library files no longer hash-match the restored `system.lock.json`, the restore **stops and prints the migrate command** rather than opening a half-resolved project (A56, amended to include `system.lock.json` and `content.json`).

---

## 14. Publish and evidence

**Committed v1 behaviour is automated publish** (NA-09 `[V — §15.4]`, overriding the normalization's runbook-first default): after a one-time credential setup performed by the user, every subsequent lock-and-publish runs the static deploy non-interactively. If no valid credential is configured, or the deploy call fails auth, **fall back to emitting a runbook and record that the site is locked but NOT published** — the fallback **does not satisfy** the "locked, published" exit criterion. This commitment carries a sign-off row.

**Evidence bundle contents** (all of them, or the bundle is incomplete): per-font `{family, foundry, licenceClass, fileHash, sourceUrl, attributionRequired}` · per-asset `{generator, model, planTier, licenceClass, prompt, alt, source}` · third-party marks with usage rules and confirmation they were **used as supplied** (A75 — no `[3P]` mark may be redrawn; generating a platform badge is a trademark violation) · the gate report with thresholds **and measured values** · the contrast proof table (WCAG ratio **and** APCA Lc per pairing) · screenshots across the breakpoint matrix × light/dark × full/reduced motion, **including pinned-device-height captures** · the **direction tour** rendered from `direction-tour-log.json` including every heat's pick and stated reason · reference triangulation (the **≥3-reference rule**: each direction abstracts ≥3 references from different eras/genres/cultures; >70% overlap with any single reference forces regeneration) · the substitution log · the publish record (stating plainly whether the site is live or only locked) · and the **fixed disclosure line**.

**Commercial-foundry faces emit a pre-launch blocker rather than being embedded** (A74). A one-line verdict mirrors into `.acos/evidence/<date>/website-<session>/`.

---

## 15. Skill packaging and CLI surface

**Frontmatter (exact):** `disable-model-invocation: true` · `user-invocable: true` · `argument-hint: "[--project <path>] [--resume] [--system <name>] [--port 8820] [--content] [--local-gen]"` · `allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion`. **`Task` is NOT listed** (A87) and **zero files are added to `.claude/agents/`** (A86). Every named feature has an **inline main-session execution path**, so nothing depends on unverified mid-skill subagent availability (`§16.5.1-O31`; NA-10 resolves §14.5's agent-authored path the same way).

**Phase 0 is a mandatory Confirmation Gate**: restate the understood brief and wait for an explicit confirmation **before any file write or server launch** (A90) — both `CLAUDE.md` files mandate it.

**Install:** `install.sh` (shell, two lines — it must run before Bun tooling is assumed present) creates a **symlink** into `~/.claude/skills/`, never a copy, verified by `ls -la … | grep acos-website-builder` showing `->` (A88). This breaks the copy-drift pattern (an existing skill lives as two byte-identical copies).

**CLI surface (all TypeScript on Bun):** `wb serve` · `wb op '<typed op json>'` · `wb lock` · `wb publish` · `wb verify` · `wb doctor` · `wb migrate [--to <sha>] [--format]` · `wb extract-override [--from-dist]` · `wb selftest` · `wb probe turn-boundary`.

**Config:** `.acos/config/website-builder.yaml` (version, default port, breakpoints, direction count 10, variants-per-component 10, artwork count 20, gate thresholds, licence policy tier, publish target), snapshotted to `audit/config-snapshot.yaml` at init.

**Session tree** `[V — §12.11; NA-B12]`: `.acos/website-builder/sessions/WB-<ts>-<slug>/{00-interview, 01-prompt, 02-system, 03-selection, 04-site, 05-variants, 06-custom, 07-lock, evidence, audit, .wb, state.json, events.jsonl, ACTIVE}`; the cross-project library at `.acos/website-builder/systems/<name>/` and `.acos/website-builder/library/`. **The phase frontier is recomputed from which directories are populated and which gates passed — never from conversation memory.**

---

## 16. Testing strategy

| Layer | Mechanism | Bar |
|---|---|---|
| Unit | `lib/*.ts` split so ~90% of decision logic is unit-testable without a browser | assertions in `selftest.ts` |
| Selftest | `bun selftest.ts` | **100% of assertions** (A85); the in-estate precedent bar is 67/67 |
| Determinism | `verify.ts` — regenerate to temp, `diff -r` text, hash-compare binaries | empty diff fresh **and** after ten drags (A53) |
| Diagnostics | `doctor.ts` — hash mismatches, orphaned overrides, stale locks, override accumulation thresholds | structured report |
| Probes | `scripts/probes/probe-turn-boundary.ts` (Gate 16-A) and the Phase-0 battery | pass/fail with recorded evidence |
| Gate suite | `gates.ts` structured verdicts, live + lock-time | exit code drives LOCK |
| Visual | screenshot diff (purity gate 4) + the capture matrix | zero-pixel diff at 1280 |

**"No LOCK without gates passing" lives in a script exit code, not a hook.** Any hook the skill registers is **cheap and fail-open** (`|| printf '{"hookSpecificOutput"…allow'`), registered dynamically and removed at close.

---

## 17. NFR summary (thresholds are contractual; sources in `spec.md` §4.3)

| Id | Threshold |
|---|---|
| NFR-01 | Live checks sub-100ms, drop/mouseup only, scoped |
| NFR-02 | LOCK wall-clock **p50 ≤90s / p95 ≤180s** for a representative 5-page site `[I — sized against the 32-gate list; not measured; validate before treating as an SLA]` |
| NFR-03 | Gate 2 ≤3 min target; >5 min ⇒ CI-only with a recorded waiver |
| NFR-04 | LCP ≤2.5s · CLS ≤0.1 · INP ≤200ms · pre-LCP transfer ≤1.5–2MB (canonical; A66/A67 subordinate and inconsistent) |
| NFR-05 + NFR-06 | WCAG 2.2 AA floor, WCAG 2 gate, APCA advisory; **57.38% automated ceiling** ⇒ no conformance claim, ever |
| NFR-07 | 320px reflow · 40-char token · +35% pseudolocalisation · 200% zoom |
| NFR-08 + NFR-09 | Motion caps 1 GPU / 1 ambient / 2 autoplay video / 2–3 pinned per page `[I — provisional]`; motion verification ceiling VLM recall 0.16 `[U]` — human plus deterministic lint only, never an automated visual score |
| NFR-10 + NFR-11 | ~600–900 tokens per direction `[V]`; flat variable layer compiled once per direction change |
| NFR-12 + NFR-13 | Verify empty-diff determinism; two-build byte equality **contingent**, normalised fallback needs sign-off |
| NFR-14 | Zero editor strings, zero design-time origins, zero unresolved references — **asserted, not claimed** |
| NFR-15 | Eight-control posture; localhost is **not** a trust boundary |
| NFR-16 | No silent overwrite in either direction, ever; conflicts retain both versions |
| NFR-17 | Zero shipped assets/fonts without a licence class; every referenced `url()`, `font-family`, SVG id and asset path resolves to a manifest entry **and** a file on disk, with zero remote-host references |
| NFR-18 + NFR-19 + NFR-20 | SEO/structured data; no-JS usability; font loading and metric-matched fallbacks |
| NFR-21 | Harness rules: absolute paths · no `timeout` binary · no `rm -rf` in export · never trust a same-turn 200 · never assume `Task` |
| NFR-22 + NFR-23 | TypeScript on Bun (**zero `.py` under the skill's `scripts/`/`app/`** — A84); symlink install (A88) |
| NFR-24 + NFR-25 | Override thresholds 5/15/40/25% `[I]`; interview 25–35 min fast, 45–70 open-ended `[I]` |
| NFR-26 + NFR-27 | Structured verdicts with measured values; **no slice Done without Dev and QA learnings** |

---

## 18. ADR register (to be filled by Phase 0, not by this document)

| ADR | Question | Owner slice | Status |
|---|---|---|---|
| ADR-01 | Launcher rung (F1–F5) | S01 | **open — blocking** |
| ADR-02 | Font policy on the generation surface | S02 | open (assume blocked; mandate base64) |
| ADR-03 | Build substrate (framework vs plain generated HTML) | S03 | open (I6 until it lands) |
| ADR-04 | Process topology (single-origin vs two-origin) | S04 | open (I1–I6 until it lands) |
| ADR-05 | Byte reproducibility, or the normalised fallback | S05 | open — **sign-off contingent** |
| ADR-06 | Mid-skill subagent availability | S06 | open — not a v1 blocker |
| ADR-07 | Multi-page: Branch A+ vs Branch B | S36 | **defaulted to A+ (NA-B01), sign-off row** |
| ADR-08 | `wb migrate` semantic matching (`§12.16-O35`) | v2 | **defaulted to canonical fallback (NA-B04)** |

---

## 19. Technical open items carried, not closed

`§17-O4` topology · `§17-O5`/Gate 16-A survival · `§17-O1` font policy · `§17-O8` substrate · `§12.5-O33` byte reproducibility · `§16.5.1-O31` subagent availability · `§12.3-O31` breakpoint-boundary-vs-preview-width reconciliation · `§12.3-O32` wide/xl tier · `§12.7-O34` same-uid enforcement (**no in-scope mitigation**) · `§12.16-O35` semantic variant matching (**new, NA-B04**) · `§17-O2` generation-channel ceiling (**unknown, published figures unreliable**) · R9 free-position degradation (**partial**) · R14 motion judgement (**none**) · sibling-anchored free positioning (**unprototyped**).

**Every one of these is cited section-qualified.** Bare `O31`/`O32`/`O33`/`O34` are ambiguous four ways (NA-08), and acceptance ids above A90 are ambiguous two ways (NA-B05).

---

**End of `tech_prd.md`.** Field-level schemas, file formats and state machines: `data-model.md`. Slice contracts: `stories.json` + `tasks/*.md`.
