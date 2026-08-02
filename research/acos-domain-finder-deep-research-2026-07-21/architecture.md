# acos-domain-finder — Architecture (v1)

**Date:** 2026-07-22
**Status:** Design, pre-build. Supersedes the .com-only shape in `.acos/swarm/swarm-20260718-022553/synthesis/report.md`.
**Evidence base:** `report.md` + appendices A–D in this folder.

---

## 0. Design thesis

Three layers, each doing only what it is actually good at:

| Layer | Owns | Why it owns it |
|---|---|---|
| **LLM (the skill body)** | Semantics: idea parsing, name generation, meaning/relevance/sound judgments, cross-language salience, tie-breaks | Only the model can judge "does this allude to the function" or "would a Swede laugh at this" |
| **Scripts (TypeScript, zero deps)** | Exact mechanics: character-level string ops, all network I/O, tri-state verdicts, rate-limit etiquette | LLMs are architecturally unreliable at character-level work (tokenization); network discipline must be deterministic and testable |
| **Data files (JSON, date-stamped)** | Facts that decay: TLD→endpoint overrides, industry→TLD congruence, parked-lander list | These change under you (three registry migrations appeared in one research pass). Dated data ≠ logic; it must be editable without touching code |

**Non-negotiable invariant:** no code path may produce `AVAILABLE` from an absence of information. Silence, timeouts, transport errors, NXDOMAIN, unknown TLDs → `UNKNOWN`, always.

---

## 1. Runtime decision (verified 2026-07-22 on this machine)

| Runtime | Version found | TypeScript direct? | Built-in `fetch`? | `node:net` port-43? |
|---|---|---|---|---|
| Node | v20.19.3 | **No** (type-strip landed 22.6+) | Yes | Yes |
| Bun | 1.3.9 | **Yes** | Yes | Yes (verified) |

**Decision: TypeScript, executed by Bun, with zero npm dependencies.** Smoke-tested end to end this session: a `.ts` file using `node:net` + global `fetch` returned `TAKEN` for `nic.com`, `AVAILABLE` for a gibberish `.com`, and a full 31-line WHOIS record from `whois.gg`.

This satisfies both constraints that were in tension: the language rule (TypeScript for I/O-bound tooling) and the original plan's zero-dependency/zero-key goal. Nothing is installed; both channels use runtime built-ins.

**Portability shim** — `scripts/run` picks a runtime and fails loudly rather than silently:
1. `bun` on PATH → `bun scripts/<x>.ts`
2. else Node ≥ 22.6 → `node --experimental-strip-types scripts/<x>.ts`
3. else → exit 2 with a one-line install hint. **Never** degrades to a partial check.

---

## 2. File layout

```
~/.claude/skills/acos-domain-finder/
├── SKILL.md                          # orchestration contract, ~120 lines
├── references/
│   ├── naming-craft.md               # generation buckets + full 0/1/2 anchors + evidence flags
│   ├── legal-posture.md              # disclaimer text, deep links, what we may never claim
│   └── data/
│       ├── tld-map.json              # overrides + industry congruence + premium-risk flags (dated)
│       └── parked-landers.json       # NS patterns for for-sale detection (dated)
└── scripts/
    ├── run                           # runtime shim (bun → node≥22.6 → hard fail)
    ├── check-domains.ts              # availability engine (the core)
    ├── screen-mechanics.ts           # offline string mechanics, no network
    └── enrich-finalists.ts           # history, dev-registry, parked, expiry
```

Frontmatter: third-person `description` front-loading trigger words (business name, brand, startup, domain); `argument-hint: [business idea in plain language]`; `allowed-tools` pre-granting the runner. Model-invocation stays on so "help me name my startup" triggers it without the slash command.

---

## 3. Pipeline

```
 [0] INTAKE ──► [1] GENERATE ──► [2] MECHANICAL SCREEN ──► [3] AVAILABILITY
                     ▲                (offline, free)          (network, tri-state)
                     │                                              │
                     │                                              ▼
                     │                                        [4] HARD GATES
                     │                                              │
                     │                                              ▼
              [7] LOOP CONTROL ◄──────────────────────────── [5] SCORING (0/1/2)
                (≤4 rounds)                                         │
                                                                    ▼
                                                          [6] FINALIST ENRICH
                                                                    │
                                                                    ▼
                                                             [8] OUTPUT
```

### Phase 0 — Intake (LLM)
**Input:** the business idea as a full paragraph (the single biggest competitive differentiator per the field survey — incumbents take keywords).

**Parameters:**
| Parameter | Default | Purpose |
|---|---|---|
| `--tlds com` | `com` | Ordered preference list, e.g. `com,ai,io`. First entry = **primary** (see §4) |
| `--positioning` | inferred | luxury / rugged / precise / playful — conditions rubric weights |
| `--markets` | EN + top-5 roster | Languages for the cross-language salience screen |
| `--count` | 10 | Finalists to deliver |

**Derived before any name exists** (this ordering matters — the vowel rule is meaningless without it):
- **Dominant attribute** → big/heavy/strong vs fast/light/precise. Drives vowel congruence in Phase 5. (Evidence: ≈2:1 preference for congruent vowels, Lowrey & Shrum 2007.)
- **Semantic field map** → roots, metaphor sources, adjacent domains, the words a stranger already associates with this business.
- **Tech-flavored?** → gates the dev-registry collision check in Phase 6.

### Phase 1 — Generation (LLM, bucket-forced)
Batches of ~20–25 across five buckets, so the model cannot collapse into one style:

| Bucket | Target class | Cap |
|---|---|---|
| Evocative metaphor (real word, allusive) | suggestive / arbitrary | — |
| Compound / portmanteau | suggestive | — |
| Latin / Greek root fusion | suggestive → fanciful | — |
| Invented phonotactically-regular coinage | fanciful | — |
| Misspelling variant | fanciful (weak) | **≤10% of batch** |

The misspelling cap is a research-driven correction: a curated marketplace's own criteria exclude spelling variants, and the prior swarm measured a ~14% preference penalty for misspelling-based names. They stay available as a fallback, but may not flood a batch.

Anti-collapse technique stack: Verbalized-Sampling phrasing, persona rotation per batch, and a running avoid-list of every name seen in the session.

**Generation target = the suggestive class.** Phase 5 makes this explicit, so the generator aims at the only class that can score 2/2 on both relevance and meaning.

### Phase 2 — Mechanical screen (`screen-mechanics.ts`, offline, free)
Deterministic character work, no network, no model:
- LDH syntax filter (letters/digits/hyphens; 1–63 chars).
- **Re-segmentation scan both ways**: enumerate every plausible tokenization of the lowercase concatenation, emit *candidate* embarrassments. Output is a candidate list, never a veto — the model judges salience in Phase 4, because the naive version flags innocent names (the Scunthorpe problem) while missing real ones.
- Syllable count, phoneme-shape estimate, initial-stress guess.
- Consonant inventory: plosive positions (word-initial flagged), voiced vs voiceless, sonorant balance.
- Spelling-ambiguity heuristics (double letters, silent clusters, homophone endings).

Emits one JSON record per name. Phase 5's SOUND judge reads these facts rather than re-deriving them — the model must not count letters itself.

### Phase 3 — Availability (`check-domains.ts`, the core)

**Per-TLD resolution chain** — first hit wins, and a miss falls through rather than concluding anything:

```
1. Local override table (references/data/tld-map.json, date-stamped)
2. Cached IANA bootstrap  (data.iana.org/rdap/dns.json, 24h cache, If-None-Match)
3. Port-43 WHOIS          — only if IANA root-db lists a server for that TLD
4. DNS inference          — may produce TAKEN only, never AVAILABLE
5. UNKNOWN("no channel for .<tld>")
```

**Override table shipped v1** (working RDAP absent from the IANA bootstrap; verified twice, 2026-07-21):

| TLD | Endpoint | Note |
|---|---|---|
| `.io` `.sh` `.me` | `https://rdap.identitydigital.services/rdap/` | |
| `.co` | `https://rdap.registry.co/co/` | `/co/` zone segment is mandatory |
| `.us` | `https://rdap.nic.us/` | |
| `.so` | `https://rdap.nic.so/` | |
| `.de` | `https://rdap.denic.de/` | registry calls it test operation, no service-level guarantee |
| `.gg` | *(none — WHOIS `whois.gg`)* | only true no-RDAP TLD in the surveyed set |
| `.id` | `https://rdap.pandi.id/rdap/` | IANA-canonical but timed out 3/3 from a US vantage → expect the WHOIS/DNS fallback |

Each entry carries `verified_at` and a `source` note. A monthly re-check against the bootstrap retires entries as IANA adds them (`.ai` was added around its 2025-02-11 migration).

**Stages per run:**
- **Stage 0 — DoH prefilter (optional, cheap):** DNS-over-HTTPS `NS` query. A positive answer proves TAKEN and kills the candidate before any registry sees it. NXDOMAIN advances the name and proves nothing.
- **Stage 1 — RDAP:** `GET <base>domain/<name>.<tld>`. Concurrency 2–4 **per registry**, 100–250 ms spacing, `--max-time 10`, one retry. Mapping: `200 → TAKEN` · `404 → available-pending` · `429 → honor Retry-After, else jittered exponential backoff` · anything else/timeout → `UNKNOWN(reason)`.
- **Stage 2 — WHOIS cross-check:** only for TLDs with no RDAP, or as confirmation on survivors. It may confirm TAKEN; it may **never** upgrade anything to AVAILABLE. (A registry WHOIS server returned "DOMAIN NOT FOUND" for a *registered* domain during this research — the failure mode is real.)

**Output contract**, one line per name×TLD:
```
<name>.<tld>  AVAILABLE|TAKEN|UNKNOWN(<reason>)  <ISO-timestamp>  via <channel>
```

**Rate-limit budget:** only one published ceiling exists in the whole surveyed field (1,000 queries per rolling 60 s at one ccTLD registry); everywhere else is unpublished, so the design stays ~100× under the one known number and treats `429` as the real signal. Names spread across several TLDs *reduce* per-registry load.

### Phase 4 — Hard gates (veto before scoring)

| Gate | Judge | Rule |
|---|---|---|
| Generic for the category | LLM | **Absolute veto.** Generic marks get no trademark protection ever — no score can rescue them |
| Salient embarrassment (own or cross-language) | LLM on script candidates | Veto if a native speaker would plausibly hear it; borderline = demote, not delete |
| Famous-mark proximity | script + LLM | Edit distance ≤2 from, or substring of, a famous mark |
| Radio-test failure | LLM + Phase-2 facts | Heard once, a listener cannot spell it |
| Hyphens / digits | script | Veto |
| No AVAILABLE in the **primary** TLD | script | Demote out of the ranked list (kept in the appendix with its verdict matrix) |

Cross-language screening judges **sound**, not letter strings: the industry's most-repeated cautionary tale is a myth built on eyeballed spelling, while the two real disasters were genuine homophones. Flags surface for human confirmation; the model is not treated as equal to a native-speaker panel, because no benchmark exists showing it is.

### Phase 5 — Scoring (LLM judge, 0/1/2 anchored)

**Core three — your stated requirements:**

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| **RELEVANCE** (R1) | No connection without the founder's backstory | Oblique; needs one sentence to land | Function/benefit evident on first hearing to a stranger |
| **MEANING** (R2) | Generic (**veto**) or flatly descriptive | Arbitrary real word, or opaque coinage — legally strong, semantically mute | **Suggestive**: real word or transparent coinage that alludes without describing |
| **SOUND** (R3) | Disfluent; ambiguous pronunciation; no stress point | Pronounceable but flat (all-soft or all-hard, or drags) | Plosive spine + sonorant flesh; attribute-congruent vowels; one obvious pronunciation |

Each anchor ships with 2–3 real brand examples baked into `naming-craft.md`, because coarse scales with anchors beat 1–10 "vibe" scores on judge agreement.

**Supporting four:** spelling certainty · memorability/distinctiveness · extensibility · uniqueness (how many existing companies already use the exact string — scored from the same web-search pass that serves the legal screen, so it costs nothing extra).

**Ranking:** minimum-then-mean — consistently good beats spiky. Pairwise comparison only to break ties inside the top cluster.

**Evidence flags travel with the rubric.** The sound rules are not equally solid, and the rubric says so in-line: vowel congruence is well-replicated; the sound-shape mapping holds at 72% across 25 languages and fails in a few; the phoneme-frequency table is one English-market correlational study whose word-initial pattern *reverses* for non-English-origin names, so it is a bonus signal, never a gate; the two-syllable rule is a soft default only; consonant-gender claims are contested and excluded entirely.

### Phase 6 — Finalist enrichment (≤10 names, all key-free)

| Check | Method | Emits |
|---|---|---|
| **Domain history** | Internet Archive CDX index | zero snapshots = likely fresh; snapshots = "previously used — review history" + deep link |
| **Dev-registry collisions** (tech ideas only) | npm / PyPI / crates.io / GitHub org JSON endpoints | soft flags, never vetoes |
| **Parked / for-sale** on TAKEN | NS records vs `parked-landers.json` | "taken but appears parked — may be purchasable on the aftermarket" |
| **Expiry + registrar** on TAKEN | parse events from the RDAP response **already fetched** | zero extra requests |
| **AI findability** | ask the model what it associates with the exact string | 0/1/2 association strength; second angle on famous-mark proximity |
| **Pronunciation** | local text-to-speech | optional audio + phonetic spelling |

The history check is the one no incumbent name generator performs, and it changes a buy decision: a domain that is free today may carry a prior owner's spam reputation.

### Phase 7 — Loop control
If fewer than ~`--count` names survive with an available primary domain, regenerate — informed by *which patterns died*, not blindly. Cap 3–4 rounds. Between rounds the user may star favorites, and the next batch is told to generate more sharing their phonetic and semantic DNA (positive signal, added to the existing avoid-list negative signal).

### Phase 8 — Output

```
BUSINESS NAME FINDER — <n> candidates · checked <ISO timestamp>
Checked locally. Your candidate list was never sent to any registrar, marketplace, or third-party service.

RANKED
 #  NAME        .com    .ai     .io    REL MEAN SOUND  MIN  FLAGS
 1  <name>      AVAIL   AVAIL   TAKEN   2    2     2     2  —
 2  <name>      AVAIL   UNKNOWN AVAIL   2    2     1     1  spelling: two plausible spellings
...

PER-NAME CARDS
  <name>  /prəˈnʌns/  · meaning tier: suggestive · reads as: "<gloss>"
    why it scores: <one line per dimension>
    soft flags:    <spelled out in full, e.g. "lowercased this can read as…">
    history:       <fresh | previously used + link>

▸ REJECTED AND WHY (collapsed)   ← so you can overrule a false positive

AVAILABILITY HONESTY
  <k> names returned UNKNOWN: <reason breakdown>. UNKNOWN is not available.
  Every AVAILABLE above means: appeared available as of <timestamp> — confirm price and
  registrability at your registrar's checkout. Reserved and premium-tier names also return
  "not found", especially outside .com.

LEGAL
  Domain availability is not trademark clearance and this is not legal advice.
  Pre-screen only. <deep links: USPTO search, TMview, WIPO Global Brand Database (links only —
  automated querying of WIPO GBD is prohibited by its terms), your state business register>
  Attorney knockout search ≈ $150–$500; full US clearance ≈ $1k–$3k.

NEXT: re-verify your chosen name at checkout before you buy.
```

---

## 4. Multi-TLD semantics (the R4 design)

The user's TLD list is **ordered**, and the first entry is the **primary**:
- **Primary** gates ranking. A name with no available primary domain drops out of the ranked list (it stays in the appendix with its full verdict matrix, so nothing is hidden).
- **Secondary TLDs** are shown as extra columns and used only as tie-breakers and fallback suggestions.
- **Premium-risk flag:** TLDs known to run registry premium tiers (notably `.ai`, `.io`) carry a persistent marker in the output, because a 404 there can still mean an expensive or reserved name. `.com` has uniform registry pricing, so the risk concentrates exactly where multi-TLD support takes the skill.
- If a requested TLD has no channel, the column reads `UNKNOWN(no channel)` for every name. The skill says so once, plainly, rather than quietly dropping the column.

---

## 5. What this deliberately does NOT do (and why)

| Excluded | Reason |
|---|---|
| Aggregator/redirector services | Same coverage as doing the routing ourselves, plus a 10-requests-per-10-seconds cap, an extra hop, and observed flakiness. Worse, its "not found" replies for TLDs it doesn't know would read as available |
| Registrar / commercial availability APIs | Money gates, time gates, or IP-whitelisting; add no availability truth beyond the registry |
| Zone files, bloom filters, bulk DNS | Approval chores and ~23 GB daily for a tool that checks 20–200 names |
| Automated trademark register queries | Free official APIs exist but require a registered key; one major database prohibits automated querying outright. Links-only is the honest ceiling for v1 |
| Sending candidates to any remote service | Every competing plug-in ships your list off-box. Staying local is free here and is a genuine differentiator |
| Logo generation | Out of scope; a local wordmark specimen is a possible v1.1 |

---

## 6. Failure posture

| Failure | Behavior |
|---|---|
| Bootstrap file unreachable | Use last cached copy; if none, override table only; unlisted TLDs → `UNKNOWN` |
| Override endpoint 5xx / moved | Fall through the chain; never silently AVAILABLE |
| `429` from a registry | Honor `Retry-After`, else jittered exponential backoff; if the budget is exhausted → `UNKNOWN(rate-limited)` |
| Regional endpoint unreachable (the `.id` case) | Timeout → WHOIS → DNS → `UNKNOWN`; never hang the run |
| Runtime missing | Shim exits 2 with an install hint; no partial or fabricated results |
| Every candidate vetoed | Report the veto histogram and regenerate against it — do not lower the gates |

---

## 7. Build order (each step independently testable)

1. `scripts/run` shim + `check-domains.ts` skeleton with the resolution chain and tri-state contract.
2. `tld-map.json` seeded with the seven verified overrides + `verified_at` stamps.
3. Availability engine end-to-end against a fixture list of known-taken and known-free names across `.com`, `.ai`, `.io`, `.de`, `.gg` (the five distinct channel shapes).
4. `screen-mechanics.ts` (offline; unit-testable with no network).
5. `SKILL.md` orchestration + `naming-craft.md` anchors and evidence flags.
6. `enrich-finalists.ts`.
7. Full dry run on a real business idea; inspect the rejected-and-why section for false positives.

---

## 7a. AS-BUILT — deltas from this design (recorded 2026-07-22)

The skill shipped. This section records where reality differs from the design above, so the
document stays trustworthy rather than aspirational.

**Name.** Shipped as **`acos-domain-finder`** (user decision, 2026-07-22), not
`business-name-finder`. The research folder was renamed to match. The skill's own name
appears in the user-agent string, the cache directory, and the shim's error messages — all
updated; a self-test check now fails if any stale reference reappears.

**Files added that this design did not list:**

| File | Why |
|---|---|
| `package.json` | `{"type":"module"}` — required for the Node ≥22.6 fallback path to treat `.ts` as an ES module. Bun does not need it |
| `scripts/selftest` | 70 checks across structure, runtime, live accuracy, honesty rules, mechanics, enrichment, and maintenance. Makes "it works" reproducible instead of anecdotal |
| `scripts/verify-overrides.ts` | Turns open item #4 ("re-verify monthly") from a note into a command. Reports `OK` / `ADOPTED` / `BROKEN` / `DEGRADED` per override and changes nothing on disk |
| `references/data/segmentation-wordlist.json` | The re-segmentation scan needs a wordlist; the design implied it without naming the file |

**Two modes, not one.** The rename exposed a gap: "domain finder" implies the user may bring
their own names. `SKILL.md` now documents **Mode A** (full naming pipeline) and **Mode B**
(check names the user already has — Phases 2, 3, 6 only, no generation).

**WHOIS asymmetry clarified.** This design said WHOIS "may never upgrade anything to
AVAILABLE". Taken literally that made `.gg` — which has no RDAP at all — permanently
unanswerable. The shipped rule is two-mode and precise: as **primary** channel (no RDAP
exists for that TLD) the registry is the authority, so a recognised not-found marker yields
AVAILABLE; as **fallback or cross-check** it may only confirm TAKEN, never upgrade. The
`t.co` false-negative case is handled separately, by marking that specific WHOIS server
`role: disabled` in the data file.

**Two bugs found and fixed during the build:**

1. *Segmentation visibility was boolean and wrong on its most important case.* The first
   implementation checked only whether a match aligned with a component edge, so
   `expertsexchange` → "sex" — where the reading exists **only** because two components run
   together — was labelled `buried`, the lowest concern. Now three-tier:
   `crosses-boundary` > `at-edge` > `buried`. Verified: `ExpertsExchange` and `PenIsland`
   rate crossing, `TherapistFinder` rates at-edge, `Scunthorpe` rates buried (and must not
   auto-veto), `BlackBerry` is clean.
2. *Domain history timed out into a false UNKNOWN.* Two causes: the `collapse=timestamp:N`
   query parameter reliably pushed the request past 25 s, and the default 12 s budget was
   too short regardless. Fixed by dropping the parameter, giving history its own 30 s budget,
   and adding one retry — the index is erratic, not down (identical queries measured at
   0.5 s, 10.8 s and 20.0 s within a minute). Four consecutive runs now answer.

**Market finding from the dry run (relevant to expectations, not to code):** across 23
pronounceable candidates for a sample business, **0 `.com` domains were available** —
verified independently against the registry, with several registered in 2026. A `.com`-only
build would have returned nothing. Multi-extension support is load-bearing, and the loop
phase is not optional decoration.

**Open items 1–3 resolved by design, not by investigation:** concurrency stays at 3 per
registry, so the unpublished-throttle question never arises (item 1); the coarse
`allowed-tools` fallback was taken rather than relying on the unverified path variable
(item 2); the cross-language screen ships explicitly labelled as flag-for-review, never
clearance (item 3). Item 4 now has `verify-overrides` behind it.

## 8. Open items carried forward

1. Registry throttling ceilings are unpublished almost everywhere — the etiquette envelope is inferred from one published limit plus protocol behavior, not measured. Probe before raising concurrency.
2. Whether the skill-directory variable glob-matches inside `allowed-tools` is unverified on the current version — fall back to coarser permissions if not.
3. The model's cross-language screen has no published benchmark against human native-speaker panels; it flags for review, it does not clear.
4. `.co`, `.me`, `.us`, `.so` endpoints work empirically but have no official endpoint documentation — treat as Probable and re-verify monthly.
