# Deep Research Report: acos-domain-finder skill — gaps, multi-TLD feasibility, and the four name-quality requirements

**Date:** 2026-07-21
**Evidence Quality:** Standard (2+ sources for key claims), with Maximum-grade verification (3+ independent evidence classes, including two independent live-probe sets) on the load-bearing multi-TLD architecture claims.

**Research question (as posed):** (1) What is the planned acos-domain-finder skill missing versus the field? (2) Is it possible to do the domain search "this way" (key-free registry RDAP) — including for a **user-specified preferred domain extension** (R4)? (3) How do we guarantee: R1 business relevance, R2 meaningful-or-cleverly-alluding names, R3 names that sound strong and nice to hear?

**Companion documents (this folder):**
- `appendix-a-rdap-landscape.md` — full per-TLD RDAP/WHOIS landscape dossier (Agent 1)
- `appendix-b-feature-gaps.md` — 21-row feature-gap analysis vs 10 commercial tools, 6 OSS projects, 8 MCP servers (Agent 2)
- `appendix-c-sound-meaning.md` — linguistics + trademark-spectrum evidence base, 19 Tier-1 sources (Agent 3)
- `appendix-d-empirical-probes.md` — main-session probe transcripts (independent verification set)

---

## Executive Summary

**Yes — the domain search works this way, for any of the popular extensions, with zero API keys.** The mechanism is the IANA RDAP bootstrap registry (`data.iana.org/rdap/dns.json`, RFC 9224/STD 95): a free, daily-cacheable file mapping 1,199 TLDs to their official RDAP endpoints. The 200=TAKEN / 404=appears-available / 429=back-off semantics of the existing .com-only plan generalize unchanged: this research verified them empirically on **15 TLDs across 10 different registry operators, in two independent probe sets** (Agent 1's and the main session's — every probe agreed). The one architectural surprise: seven popular extensions (.io, .co, .me, .us, .de, .sh, .so) run **working RDAP servers that are absent from the IANA bootstrap** ("shadow RDAP") — the skill needs a small hardcoded override table for them, or it would wrongly conclude they are uncheckable. Only .gg has no RDAP at all (port-43 WHOIS works); .id's official endpoint is IANA-canonical but timed out consistently from a US vantage.

**What the plan is missing:** the field survey found the .com-only stance is the plan's single most visible deficiency (every incumbent and every MCP competitor is multi-TLD — and the user's R4 requires it anyway). Beyond that, three high-value, key-free gaps: (a) a **domain-history check** on "available" finalists (Wayback CDX; an available domain may carry spam baggage — no incumbent generator does this); (b) **dev-registry collision checks** (npm/PyPI/crates.io/GitHub) for tech-flavored ideas; (c) surfacing the **RDAP metadata already fetched** (expiry dates for taken names) plus **parked/for-sale detection** on taken names. A novel free differentiator: an **LLM-knowledge "AI findability" probe** (a competitor charges $0.01–0.05/call for this; it is a free prompt for a skill running inside Claude). The plan is already at-or-above market on: technique buckets, cross-language screening, radio test, tri-state honesty, rejected-with-reasons output, and its local-only privacy stance (every competitor MCP ships the candidate list off-box).

**The four requirements are all implementable, and R2 contains a happy inversion:** trademark doctrine (*Abercrombie & Fitch Co. v. Hunting World*, 537 F.2d 4 (2d Cir. 1976)) makes the "cleverly alludes" fallback the legally STRONGER outcome — suggestive names (Netflix, Pinterest) are inherently distinctive, while plainly descriptive real words are the weakest protectable class and generic names get no protection ever (absolute veto). R3 ("strong and nice to hear") converts to evidence-based scoring: plosive spine + sonorant flesh, vowel choice congruent with the business's dominant attribute (≈2:1 preference effect), processing fluency as a liking bonus — with explicit single-study/failed-replication flags baked into the rubric so it does not overclaim.

**Critical risk to word correctly in output (R4 consequence):** on many non-.com TLDs (notably .ai and .io), registries hold premium tiers — a name can return RDAP 404 ("appears available") yet cost hundreds or thousands at checkout, or be reserved. The tri-state contract's "appeared available as of <time> — confirm at your registrar's checkout" wording is not boilerplate; it is load-bearing, and MUST accompany every non-.com verdict.

---

## Key Findings

### Finding 1: Multi-TLD availability checking is feasible key-free — verified end-to-end
- **Confidence Level:** Verified (Tier 1 docs + two independent Tier 3 probe sets)
- **Data:** IANA bootstrap (publication `2026-07-14T22:00:03Z`) covers 1,199 TLDs. Empirical 200/404 semantics confirmed on: .com, .org, .ai, .app, .dev, .xyz, .tech, .uk (bootstrap-listed; 8/8 correct) and .io, .me, .sh, .co, .us, .so, .de (override endpoints; 14/14 probes correct in the main-session re-verification, matching Agent 1's independent probes).
- **Sources:** RFC 9224 (STD 95, obsoletes RFC 7484); `data.iana.org/rdap/dns.json` direct fetch; live probes (appendix D); Verisign RDAP help page.
- **Analysis:** Resolution order for the skill: (1) hardcoded override table → (2) cached IANA bootstrap (24 h, `If-None-Match`) → (3) port-43 WHOIS if IANA lists a server → (4) DNS inference (TAKEN/UNKNOWN only) → (5) UNKNOWN. The user's preferred-extension input (R4) plugs into this chain unchanged.

### Finding 2: Seven popular TLDs need hardcoded "shadow RDAP" overrides
- **Confidence Level:** Verified for .io/.sh/.de (empirical ×2 + operator documentation); Probable for .co/.me/.us/.so (empirical ×2, no official endpoint docs found)
- **Data:** `.io .sh .me` → `https://rdap.identitydigital.services/rdap/` ; `.co` → `https://rdap.registry.co/co/` (the `/co/` zone segment is mandatory) ; `.us` → `https://rdap.nic.us/` ; `.so` → `https://rdap.nic.so/` ; `.de` → `https://rdap.denic.de/` (official "test operation" — no SLA).
- **Sources:** appendix A Q3 table; appendix D §D4 (14/14 re-verification); IANA root-db pages; identity.digital WHOIS FAQ.
- **Analysis:** A bootstrap-only client (including the rdap.org redirector) believes these TLDs have no RDAP. ccTLDs do get added to the bootstrap over time (.ai was added around its 2025-02-11 registry migration), so the override table should be re-checked against the bootstrap periodically.

### Finding 3: WHOIS is a decaying fallback, and it can silently lie
- **Confidence Level:** Verified (ICANN primary text + operator notice + empirical false negative)
- **Data:** ICANN sunset effective 2025-01-28 (RDAP is "the definitive source" for gTLD registration data; WHOIS no longer contractually required). Identity Digital retired port 43 portfolio-wide on 2025-08-04. Empirical: `whois.registry.co` returned "DOMAIN NOT FOUND" for **t.co — a registered domain** (Agent 1's probe), while answering correctly for nic.co (main session) — a preserved conflict; assessment in appendix D §D5.
- **Sources:** icann.org announcement 27-01-2025 (full text); identity.digital WHOIS FAQ; probe transcripts.
- **Analysis:** WHOIS is acceptable only where no RDAP exists (.gg in our set) and must never override an RDAP verdict. A WHOIS "not found" from a post-migration registry is not proof of availability.

### Finding 4: RDAP 404 ≠ buyable — reserved and premium names also 404
- **Confidence Level:** Verified (protocol semantics + registry premium-tier documentation; consistent with the prior swarm's finding)
- **Data:** 404 means "no object in the registry database." Reserved, registry-blocked, and premium-held names can 404 while being unregistrable or expensive. Registry premium tiers are real on new gTLDs and ccTLDs (.ai, .io among them); .com has uniform Verisign pricing (no registry-premium tier), so the risk concentrates exactly where R4 takes the skill.
- **Sources:** OpenSRS/Dynadot premium-tier docs; RFC 7480 semantics; appendix A Q3 caution; appendix B gap 6.
- **Analysis:** Every AVAILABLE verdict must be worded "appeared available as of <timestamp> — confirm price and registrability at your registrar's checkout," and the winner must be re-checked at decision time. This was already in the plan for .com; multi-TLD makes it mandatory, not stylistic.

### Finding 5: Rate limits are mostly unpublished; the etiquette envelope is easy to stay inside
- **Confidence Level:** Verified for Nominet and rdap.org; Open/Probable elsewhere
- **Data:** Nominet (.uk): 1,000 queries per rolling 60 s (recalculated every 5 s). rdap.org: 10 requests/10 s (and empirically flaky — 5 consecutive timeouts observed). Verisign, Google Registry, PIR, Radix, Team Internet, GoDaddy Registry: no published numbers; RFC 7480 prescribes 429 + Retry-After behavior. Identity Digital: "queries to the RDDS are throttled," numbers unpublished.
- **Sources:** registrars.nominet.uk RDAP ToS; about.rdap.org; RFC 7480; operator pages (appendix A Q5).
- **Analysis:** For 100–200 lookups/run: query registries directly (skip rdap.org entirely), concurrency 2–4, 100–250 ms spacing, honor Retry-After on 429 else exponential backoff with jitter, descriptive User-Agent, cache bootstrap 24 h. This supersedes the prior plan's concurrency 4–8 for the multi-TLD case (per-registry volume drops further when names spread across extensions).

### Finding 6: The feature-gap field survey — 4 high-priority gaps, 5 confirmed non-gaps
- **Confidence Level:** Verified per-tool (vendor pages fetched); priorities are analyst judgment
- **Data:** 21 feature dimensions scored (appendix B). High priority: multi-TLD (gap 1 — now R4), domain history on AVAILABLE finalists (gap 7 — Wayback CDX, key-free), dev-registry collisions for tech ideas (gap 4 — npm/PyPI/crates.io/GitHub, all key-free JSON), aftermarket/parked detection on TAKEN names (gap 6, rises to High with multi-TLD). Medium: TLD-by-industry advice line, RDAP expiry surfacing (zero extra requests), uniqueness score from the existing web-search pass, LLM "AI findability" self-probe (NameIntel charges $0.01–0.05/call for the equivalent), two-tier social-handle honesty (GitHub = fact; X/Instagram = deep links only), positive preference learning ("more like the starred ones").
- **Sources:** appendix B (Tier 1 vendor/repo pages, accessed 2026-07-21).
- **Analysis:** Non-gaps — already at/above market: technique buckets, LLM cross-language screen, radio test, famous-mark veto, tri-state honesty, rejected-with-reasons, local-only privacy (a genuine differentiator worth stating in the output header; every remote competitor ships candidate lists off-box). One correction the survey forces: BrandBucket's curation criteria imply the misspelling bucket will systematically score poorly — cap its share per batch.

### Finding 7 (R2): "Cleverly alludes" is the legally optimal class, not the consolation prize
- **Confidence Level:** Verified (primary legal authority + convergent industry frameworks)
- **Data:** *Abercrombie & Fitch Co. v. Hunting World, Inc.*, 537 F.2d 4 (2d Cir. 1976) spectrum: generic (no protection ever) → descriptive (protection only after acquired secondary meaning) → suggestive (inherently distinctive, protectable immediately) → arbitrary → fanciful (strongest). Suggestive = "requires imagination, thought and perception to reach a conclusion as to the nature of goods" — precisely R2's "cleverly alludes to the function" class (Netflix, Pinterest, Coppertone).
- **Sources:** WIPO case record; BitLaw; INTA fact sheet; Igor Naming Guide taxonomy (independently converges: "literal = weak, evocative = strong").
- **Analysis:** The judge rubric scores: generic = absolute veto (no averaging rescues it); flatly descriptive = 0; arbitrary real word or opaque coinage = 1 (legally strong, semantically mute for R1); suggestive real word or transparent coinage = 2. A suggestive name is the only class that can score 2/2 on both relevance (R1) and meaning (R2).

### Finding 8 (R3): "Sounds strong and nice" converts to scoreable, evidence-flagged rules
- **Confidence Level:** Mixed by rule — each rule carries its own flag (appendix C evidence table)
- **Data:** Well-evidenced: front/back vowel symbolism with category congruence (≈2:1 preference margins, Lowrey & Shrum 2007); bouba/kiki basis for plosive=hard/sonorant=soft (72% congruent across 25 languages, 95% CrI 56–82%, at/below chance in Romanian/Mandarin/Turkish); fluency→liking direction (with Bahník & Vranka 2017 failed-generalization limit). Probable: voiced consonants = potency. Single-study/do-not-hard-code: Pogacar phoneme table (English-market, correlational; word-initial plosive pattern reverses for non-English-origin names). Not supported: vowel-ending likability (only gender-congruence effects: -a feminine, -o masculine). Contested, keep out: stops-vs-fricatives gender direction. Weak: the two-syllable rule (2026 J. Brand Management study: recognition rises with length; attitude is inverted-U in phonemes; top-100 mean = 6.4 characters, 2.1 syllables as descriptive norm only).
- **Sources:** 19 Tier-1 sources (appendix C).
- **Analysis:** The "strong AND nice" recipe = plosive spine (≥1 plosive, ideally word-initial, voiced for potency) + sonorant/vowel flesh (l, m, n, s) + vowel congruent with the business's dominant attribute (back o/a for big-heavy-strong, front i/e for fast-light-precise) + unambiguous spelling→pronunciation. The judge must infer the business's dominant attribute from the idea paragraph BEFORE scoring vowels (prevents naive "back vowels always = strong").

### Finding 9 (R1 + R4 wiring): both are parameter/rubric changes, not architecture changes
- **Confidence Level:** Verified (follows directly from Findings 1–2, 7–8)
- **Data:** R1 = the existing idea-paragraph input + a dedicated 0/1/2 RELEVANCE dimension (anchors in appendix C Q3: 2 = function/benefit evident on first hearing to a stranger; 1 = needs one sentence; 0 = private-backstory only). R4 = a preferred-extensions parameter (default `.com`, accept a list, e.g. `--tlds com,ai,io`), fed through the Finding-1 resolution chain; optionally suggest 2 industry-congruent TLDs from a static table.
- **Sources:** appendices B (gap 1, 2) and C (Q3 rubric).
- **Analysis:** The generation loop, tri-state contract, and Wigum re-generation logic all survive unchanged; multi-TLD only changes the checker script and verdict table (one column per requested extension).

---

## Cross-Reference Analysis

### Source Conflicts (preserved, not harmonized)

| Data Point | Source A | Source B | Assessment |
|---|---|---|---|
| .co WHOIS reliability | Main session: `whois.registry.co` correct for nic.co and gibberish | Agent 1: same server returned "DOMAIN NOT FOUND" for registered t.co | Post-migration WHOIS unreliable (Team Internet took .co 2025-10-03); .co RDAP answered correctly in both sets → RDAP-only for .co |
| Stops vs fricatives → gender | Klink 2000: initial stops rated more feminine | Guèvremont & Grohmann 2015: stops enhance masculinity | Genuinely contested — excluded from scoring; use voicing (replicated potency cue) instead |
| Name length | Textbook 2-syllable rule; top-100 mean 2.1 syllables | 2026 J. Brand Mgmt: recognition rises with length; attitude inverted-U in phonemes; Pathak 2019: length enhances luxury | Score fluency/phoneme-shape, not syllable count; 2–3 syllables = soft default only |
| Fluency → risk/liking | Song & Schwarz 2009 (effect with original stimuli) | Bahník & Vranka 2017 (zero effect on 50 new stimuli) | Direction (liking) retained as bonus; fine-grained risk prediction rejected |
| .io/.co/.me RDAP existence | IANA bootstrap + IANA root-db pages: absent | Live endpoints: fully functional (two probe sets) | Registration lag/holdout, not absence — hence the override table; recheck bootstrap periodically |

### Data Quality Assessment
- **High:** IANA bootstrap + RFC 9224; ICANN sunset text (primary, fetched verbatim); all 22 live-probe results (two independent evidence classes, 100% agreement); Abercrombie doctrine; Nominet's published limits.
- **Medium:** Operator rate-limit postures other than Nominet (mostly unpublished → etiquette derived, not guaranteed); .co/.me/.us/.so endpoint permanence (no official docs); TLD market-share stats (.com 57%, .ai ~28% of Q1-2025 startups — secondary sources); Pogacar phoneme table (single corpus study).
- **Low / flagged Open:** "374 gTLDs already shut port 43" (single source); "no published Claude skill for brand naming" (absence of evidence); LLM cross-language screening parity with human native-speaker panels (no benchmark exists); .id endpoint behavior outside a US vantage.

---

## Risk Assessment

| Risk | Likelihood | Impact | Severity (L×I) | Mitigation |
|---|---|---|---|---|
| 404 read as "buyable" on premium/reserved names (esp. .ai/.io) | H (4) | M (3) | 12 Medium | Mandatory checkout-confirmation wording on every AVAILABLE; re-verify winner at decision time; parked/premium flag where detectable |
| Shadow-RDAP endpoint moves/breaks after a registry migration | M (3) | M (3) | 9 Medium | Override table small + dated; on override failure fall through to bootstrap → WHOIS → UNKNOWN (never silently AVAILABLE); periodic bootstrap recheck |
| 429 throttling mid-run (Identity Digital explicitly throttles) | M (3) | L (2) | 6 Medium | Concurrency 2–4, 100–250 ms spacing, Retry-After honor, jittered backoff; per-registry budgets |
| WHOIS false negatives (t.co case) polluting verdicts | M (3) | H (4) | 12 Medium | WHOIS only where no RDAP exists; WHOIS can confirm TAKEN but never upgrade to AVAILABLE against RDAP silence |
| LLM cross-language screen misses what a native panel catches | M (3) | M (3) | 9 Medium | Flag as heuristic; surface flags for human confirmation; wordsafety.com deep link; phonetic (not letter-string) matching per the Nova lesson |
| Rubric overclaims from single-study rules | M (3) | L (2) | 6 Medium | Evidence-strength flags shipped inside the rubric; single-study rules scored as bonuses, never gates |
| .id (or similar) endpoint unreachable from user's region | M (3) | L (2) | 6 Medium | Timeout → WHOIS → DNS → UNKNOWN chain; never hang the run |
| Misspelling-bucket names systematically scoring poorly | H (4) | L (2) | 8 Medium | Cap bucket share per batch; keep the ~14% preference-penalty flag from the prior swarm |

---

## Recommendations

### Tier 1: High Confidence (multi-source agreement) — fold into the build plan
1. **Adopt multi-TLD (R4) via: override table → cached IANA bootstrap → WHOIS (only if IANA-listed) → DNS (TAKEN/UNKNOWN only) → UNKNOWN.** Ship the seven-entry override table from Finding 2 with a "verified 2026-07-21" date stamp. User parameter: preferred extension list, default `.com`.
2. **Keep the tri-state contract verbatim and strengthen the AVAILABLE wording for non-.com TLDs** (premium/reserved caveat is load-bearing — Finding 4).
3. **Score the four requirements with the three-dimension 0/1/2 rubric** (appendix C Q3): RELEVANCE (R1), MEANING on the Abercrombie spectrum with absolute generic veto (R2 — suggestive = 2), SOUND (R3 — plosive spine + sonorant flesh + attribute-congruent vowels), each with anchored brand examples and evidence-strength flags.
4. **Add the domain-history check on finalists** (Wayback CDX, key-free): zero snapshots = likely virgin; snapshots = "previously used — review history" + deep link.
5. **Surface RDAP metadata already in hand** for TAKEN survivors (expiry date, registrar) — zero extra requests.
6. **Demote WHOIS to last-resort and never let it produce AVAILABLE against RDAP silence** (Finding 3, t.co case).
7. **Skip rdap.org and all aggregators** — same coverage as DIY bootstrap, plus a 10/10s cap and observed flakiness.
8. **Cap the misspelling bucket's share per batch** (BrandBucket criteria + prior swarm's ~14% penalty).

### Tier 2: Medium Confidence (some conflict or single-source) — include, flagged
1. **Dev-registry collision checks** (npm/PyPI/crates.io/GitHub org) on ≤10 finalists, only for software-flavored ideas; soft flags, not vetoes. GitHub unauthenticated = 60 req/h — finalists only.
2. **LLM "AI findability" self-probe** on finalists (free; catches famous-mark misses from a second angle). Value Probable, feasibility certain.
3. **Uniqueness score** as its own 0/1/2 dimension reusing the existing common-law web-search pass.
4. **TLD-by-industry advice line** from a static table (.ai carries premium pricing — say so).
5. **Parked/for-sale detection** on TAKEN finalists via NS-against-parked-lander-list heuristic.
6. **Two-tier social handles:** GitHub probe as fact; X/Instagram as deep links only (Sherlock false-positive lesson).
7. **Positive preference learning:** star favorites between rounds → "more like these" in the next generation prompt.
8. **Pronunciation via macOS `say`** on finalists (matches Looka's "hear it," zero cost).

### Tier 3: Requires Further Investigation
1. Empirically probe Verisign RDAP throttling at 100–200/min bursts (still unpublished; prior live tests passed ~7.5 QPS without establishing a ceiling).
2. Verify `${CLAUDE_SKILL_DIR}` glob behavior inside `allowed-tools` before shipping frontmatter (unchanged open question from the prior swarm).
3. Benchmark the LLM cross-language screen against a small human panel before trusting it beyond flag-for-review.
4. Track Fastly Domain Research API for a free tier (would add premium/aftermarket truth in one call).
5. Re-check the IANA bootstrap monthly for .io/.co/.me/.us/.de/.sh/.so additions (retire overrides as they land).

---

## Methodology & Limitations

Three parallel research agents (RDAP landscape; competitive feature gaps; linguistics/trademark evidence) ran WebSearch/WebFetch sweeps with per-claim confidence labels and tiered citations, while the main session independently fetched the IANA bootstrap and live-probed RDAP endpoints (curl) and WHOIS servers (raw port-43 sockets). The load-bearing multi-TLD claims were then **re-verified by the main session against Agent 1's endpoints (14/14 agreement)** — two independent evidence classes for every override endpoint. Conflicts were preserved per protocol (five documented above). Limitations: probes ran from one US vantage point at one point in time (~2026-07-22 04:45–05:30 UTC); registry endpoints and policies migrate (three registry transitions documented in this research alone); market-share statistics are secondary-source; the linguistics rubric anchors are analyst-constructed from the cited evidence, not themselves validated instruments; no test of actual registrar checkout behavior for premium-tier names was performed.

## Sources

Consolidated per-appendix: appendix A (31 sources, Tiers 1–4), appendix B (Tiers 1–4, all accessed 2026-07-21), appendix C (33 sources, 19 Tier-1). Headline Tier-1: RFC 9224/STD 95; RFC 7480; `data.iana.org/rdap/dns.json`; ICANN sunset announcement 2025-01-27 (verbatim text); IANA root-db pages (.ai/.io/.co/.me/.us/.gg/.sh/.so/.de/.id); identity.digital WHOIS FAQ + RDDS Access Policy; registrars.nominet.uk RDAP ToS; denic.de RDAP service page; *Abercrombie & Fitch Co. v. Hunting World, Inc.*, 537 F.2d 4 (2d Cir. 1976); Klink 2000; Yorkston & Menon 2004; Lowrey & Shrum 2007; Pogacar 2015/2018; Ćwiek 2022; Alter & Oppenheimer 2006; Bahník & Vranka 2017.

## Audit Trail
**Research conducted:** 2026-07-21 (probes ~2026-07-22 04:45–05:30 UTC)
**Verification standard:** Standard, with Maximum-grade (two independent probe sets + Tier 1 docs) on multi-TLD architecture claims
**Raw agent dossiers:** appendices A–C verbatim; probe transcripts: appendix D
