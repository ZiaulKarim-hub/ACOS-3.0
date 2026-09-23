# ADR-05 — Two-build byte-reproducibility (§12-O33)

**Status: MEASURED — the answer is YES, with stated limits. §12-O33's fallback is
NOT adopted and is NOT needed on this evidence. `DECISIONS.md` item 5 stays OPEN.**

**Date:** 2026-09-22 · **Slice:** `S05` (Two-build byte-reproducibility spike) ·
**Answers:** §12-O33 · **Does NOT answer:** §12.5 purity gate 2 (that is `S67`) ·
**Verification:** `hash-compare`

§12-O33 asks, verbatim: *"Is an Astro/Vite production build byte-reproducible
across two installs of the same lockfile on the same machine?"* and records that
**no source consulted for the PRD establishes it**. This ADR replaces that absence
with a measurement.

## Why the question was split in two

"It differed" is not an actionable answer, so the spike separates the two places
nondeterminism could live:

| Test | Setup | What a failure would mean |
|---|---|---|
| **1** | one `npm ci`, build **twice** | the **bundler** itself is nondeterministic |
| **2** | **two** independent `npm ci`, build once each | the **install** is what moves (O33 as written) |

Test 2 is O33. Test 1 isolates its cause if it ever fails.

## Fixtures — because a build that emits nothing proves nothing

The first run passed while emitting **one** file and **zero** JavaScript bundles.
That is the easiest possible case, and O33's real risk — chunk content hashing,
module ordering across packages, minifier state — lives in bundled JavaScript.
Two harder fixtures were added rather than reporting the easy pass:

| Fixture | `dist` files | JS bundles | What it adds |
|---|---|---|---|
| `light` | 1 | **0** | the S03 page: static HTML, no client JS at all |
| `heavy` | 3 | 2 | three first-party modules + a **dynamic `import()`**, forcing a content-hashed split chunk |
| `heavy-vendor` | 4 | 3 | adds `nanoid@5.0.9`, a **third-party runtime dependency**, forcing cross-package chunk layout |

## Results — all three fixtures, both tests

| Fixture | Test 1 (bundler) | Test 2 (O33) |
|---|---|---|
| `light` | **BYTE-IDENTICAL** | **BYTE-IDENTICAL** |
| `heavy` | **BYTE-IDENTICAL** | **BYTE-IDENTICAL** |
| `heavy-vendor` | **BYTE-IDENTICAL** | **BYTE-IDENTICAL** |

The content hashes Vite writes into the filenames are themselves stable across
two independent installs — that is the strongest single signal here, because the
hash is computed from the emitted chunk:

```
_astro/c.B2dlit7F.js                                           A=b5eb03459b3a8ecb B=b5eb03459b3a8ecb SAME
_astro/d.DRD-UfDk.js                                           A=367e3688ac49886e B=367e3688ac49886e SAME
_astro/index.astro_astro_type_script_index_0_lang.wXwh5Z8j.js  A=b4e294fbef1ab067 B=b4e294fbef1ab067 SAME
index.html                                                     A=b5ebf0e81be86759 B=b5ebf0e81be86759 SAME
```

### The installs were genuinely independent

Each `npm ci` was given its **own npm cache** (`npm_config_cache`), so install B
could not replay install A's downloads. A shared warm cache would have made the
two agree for a reason unrelated to lockfile reproducibility. Both caches
materialised at **33M / 566 files** each, confirming two real installs.

### The two `node_modules` trees are not identical — and it does not matter

| Measure | Value |
|---|---|
| Files in each tree | **9727 vs 9727** |
| Present in only one tree | **0** |
| Differing content | **1** — `.vite/deps/_metadata.json` |

That single file is **Vite's dependency pre-bundling cache**, written during the
build, not installed by npm. It lives inside `node_modules` but it is a build
artefact. No installed package content differed.

### Clock and locale do not leak into the output

Two builds seconds apart would not catch a build that embeds a date. The
`heavy-vendor` tree was therefore rebuilt under `TZ="Pacific/Kiritimati"` (UTC+14,
a **different calendar day** from the host's `MDT`) with `LANG`/`LC_ALL` set to
`de_DE.UTF-8`, and compared against the untouched second install:

**4 files same, 0 differ.**

## Environment

| Component | Version |
|---|---|
| Astro | `5.14.1` |
| node | `v20.19.3` |
| npm | `10.8.2` |
| Platform | darwin 24.5.0 |

## What this does NOT establish

Stated in full, because the result is favourable and a favourable result is
exactly when limits get dropped.

1. **It does not answer §12.5 purity gate 2.** Gate 2 requires *"build the same
   doc twice — once with the editor integration installed, once with it removed
   from `package.json` entirely"*. That compares **two different dependency
   trees**; this spike compares two installs of the **same** tree. Gate 2 is a
   strictly harder test and it belongs to `S67`. **Passing O33 is a precondition
   for gate 2, not evidence that gate 2 passes.**
2. **Two samples per comparison.** Reproducibility that fails one run in fifty
   would very likely have gone unseen.
3. **Same machine, same versions.** O33's own wording scopes it to one machine,
   so this is in scope — but nothing here speaks to a different machine, a
   different architecture, or an Astro/node upgrade.
4. **Narrow feature surface.** No CSS bundling, no image or asset pipeline, no
   content collections, no SSR adapter, and no UI-framework integration
   (React/Vue/Svelte). Each of those adds its own emit path.
5. **`nanoid@5.0.9` is a small pure-ESM package** with no postinstall script and
   no native binary. A dependency with either could behave differently.
6. **The real project does not exist yet.** These are spike fixtures. The
   substrate itself is still open (`ADR-03`, invariant I6), so this measures a
   candidate, not an adopted toolchain.

## Decision

**None taken, by design.** The charter is explicit: *"`S05` can run the spike and
report the result. It may NOT adopt the fallback. Running the measurement is the
slice's job; choosing what to do about a failure is item 5, and item 5 is Zee's."*

The spike did not fail, so the fallback is not reached. Whether that settles
`DECISIONS.md` item 5 — *"Build byte-reproducibility: is D3's proof achievable?"* —
is Zee's call, and the six limits above are the reason it is worth his reading
rather than an automatic yes.

## Reproduction

```
cd "Website Builder/spikes/reproducibility"

# light fixture (the S03 page)
bun run two-build.ts

# heavy fixture: code-split chunk + third-party vendor chunk
WB_S05_SRC="$PWD/heavy" WB_S05_FIXTURE=heavy-vendor \
WB_S05_WORK=/tmp/s05-vendor bun run two-build.ts

# clock/locale independence
cd /tmp/s05-vendor/t2a/proj && rm -rf dist .astro
TZ="Pacific/Kiritimati" LANG=de_DE.UTF-8 LC_ALL=de_DE.UTF-8 npx astro build
```

Each run writes `report.json` into its work directory with the full file lists,
per-file digests, and the `node_modules` comparison.
