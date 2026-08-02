# Agent 2 — Feature-Gap Analysis (raw findings, received 2026-07-21)

Research complete. I surveyed 10 commercial tools, the open-source CLI/repo landscape, and the MCP ecosystem, and probed key-free feasibility for each gap dimension. Here is the full feature-gap analysis.

# acos-domain-finder — Feature-Gap Analysis
All sources accessed 2026-07-21. Confidence: **Verified** = directly confirmed from vendor/official page; **Probable** = from secondary/aggregator sources or partial confirmation; **Open** = inference, needs a spike.

## 1. Landscape snapshot

**Commercial:** Namelix (free, 4 naming styles, learns from saved names, instant Brandmark logo previews, domain check) — Verified. Atom.com ex-Squadhelp (AI generator + 100k-namer contests, audience testing, one-click US/EU trademark check, social-handle checks, domain marketplace) — Verified. Looka (name gen + domain/social checks, "hear how it sounds", Google-results conflict check, instant logo mockups on real-world objects) — Verified. Brandmark (logo side of Namelix) — Verified. BrandBucket (curated aftermarket marketplace, $1,200+ names, each with pro logo; curation criteria = pronounceable, no spelling variants) — Verified. Wordoid (invented phonotactic words, 5 languages, quality dial high/med/low, placement pattern, length filter) — Probable. Namecheap Beast Mode (bulk 5,000 keywords, 1,164 TLDs in categories, transforms: domain hacks, drop-last-vowel, pluralize, prefix/suffix, price-range filter, shareable searches) — Verified. Panabee (alive at generate.panabee.com; domain + Facebook/Instagram/Twitter + App Store checks, related terms) — Probable. Instant Domain Search (per-keystroke, premium/for-sale detection, **official remote MCP server** with 3 tools, free, no key) — Verified. Domainr (classic API **deprecated**; now Fastly Domain Research API — commercial, registry-privileged data, premium/aftermarket status, IDNA support) — Verified.

**Open-source:** `saidutt46/domain-check` (Rust; 1,200+ TLDs via IANA bootstrap, RDAP-first + WHOIS fallback, pattern expansion `\w \d ?`, prefix/suffix permutations, 100-concurrent streaming, JSON/CSV, 11 vertical presets, `--info` returns registrar/creation/expiry, **doubles as an MCP server**, MIT/Apache) — Verified. `pepa65/domaincheck`, `Gadiguibou/rdapcheck` (bulk RDAP) — Verified. Steven Tey's one-word-domains (1.2M curated available one-worders, synonym "more like this") — Probable. `namae.dev` (open source; checks a name across ~15 registries: domains, GitHub org, npm, PyPI, RubyGems, crates.io, Homebrew, Twitter, Slack, Heroku, S3 + shows similar GitHub/App Store projects) — Verified. Sherlock (400+ site username probes, key-free, documented false-positive problem) — Verified.

**MCP/Claude ecosystem (direct overlap with this skill):** InstantDomainSearch official remote MCP (search_domains / generate_domain_variations / check_domain_availability, premium flags, free) — Verified. `saidutt46/domain-check` MCP — Verified. `imprvhub/mcp-domain-availability` (50+ TLDs, DNS+WHOIS, uvx zero-clone) — Verified. Whodis, ajot/domain-checker-mcp, `dorukardahan/domain-search-mcp` (has a `check_socials` tool) — Probable. **NameIntel** (remote MCP in official registry; scores names on 5 axes: domain, USPTO trademark screening, 12+ social handles, SEO strength, **"AI findability"**; x402 micropayments $0.01–0.05/call, no signup) — Verified. Brandomica (brand availability + safety MCP), `jordanburke/trademark-mcp-server` — Probable. **No existing published Claude *skill* for brand naming found** (searches surfaced MCP servers only) — Open (absence of evidence). Implication: the generation+scoring pipeline is differentiated; the availability-check part is commoditized. Note the privacy conflict: every remote MCP (IDS, NameIntel) ships the candidate list off-box — our plan's local-only stance is a genuine differentiator worth stating in the skill's output.

## 2. Feature-gap table

| # | Feature | Incumbents that have it | In our plan? | Key-free feasible? | Priority |
|---|---------|------------------------|--------------|--------------------|----------|
| 1 | Multi-TLD / user-preferred extensions | Beast Mode (1,164), IDS, Fastly, domain-check (1,200+), all MCPs | No (.com only) | Yes — IANA RDAP bootstrap + same DoH prefilter | **High** |
| 2 | TLD suggestion by industry (.ai/.io/.dev norms) | IDS suggestions; registrar UIs; domaindetails guides | No | Yes — static heuristic table, zero network | Med |
| 3 | Social handle availability | Atom, Looka, Panabee, Wordoid, NameIntel, namae, domain-search-mcp | No | Partial — Sherlock-style probes work for GitHub; X/Instagram unreliable unauthenticated | Med |
| 4 | Dev-registry collisions (npm/PyPI/crates/GitHub org) | namae.dev, NameIntel ("package registries") | No | **Yes, fully** — all four registries have key-free JSON endpoints | **High** (conditional on tech-business input) |
| 5 | App-store collision | Panabee, namae | No | Yes — iTunes Search API is key-free; Google Play scrape-only | Med |
| 6 | Premium/aftermarket "for-sale" detection | Fastly, IDS (premium flags), BrandBucket | No | Partial — .com has no registry-premium tier, so gap = aftermarket only; detect via parked-NS heuristic (sedoparking/afternic/dan/bodis) on TAKEN names | Med (.com-only) → High if #1 adopted (.ai/.io registry premiums are real) |
| 7 | Domain **history** of AVAILABLE names (prior spam/parking) | None of the generators; domainer tooling (DomCop, guides) | No | Yes — Wayback CDX API (no key); Spamhaus DBL via DNS query (caveat: fails through public resolvers); Google Safe Browsing needs free key | **High** |
| 8 | RDAP metadata surfaced for TAKEN names (expiry date, registrar) | domain-check `--info` | No (data already fetched, discarded) | Yes — zero extra requests | Med |
| 9 | Search-results collision score (how many companies share the name) | Looka (Google-conflict check), NameIntel (SEO strength) | Partial (common-law pass exists but scores legal risk, not uniqueness) | Yes — reuse the same WebSearch pass, emit a distinct 0/1/2 dimension | Med |
| 10 | LLM-knowledge collision / "AI findability" | NameIntel only | No | **Yes, uniquely cheap for us** — ask the local model what it associates with each finalist | Med |
| 11 | Tokenization/voice-assistant survival | NameIntel (partially); nobody else | Partial (radio test ≈ voice) | Yes — `gpt-tokenizer` npm offline for token count; radio test already covers ASR | Low |
| 12 | Pronunciation audio | Looka ("hear how it sounds") | Partial (text pronunciation only) | Yes — macOS `say` locally | Low-Med |
| 13 | Logo / type-treatment preview | Namelix, Looka, Brandmark, BrandBucket | No | Partial — HTML wordmark specimens (font pairings) local; real logo gen out of scope | Low |
| 14 | Company-register collision (SoS / Companies House) | None of the generators (adjacent: TailorBrands entity search) | No | Mostly no — OpenCorporates/Companies House need (free) keys; 50 states are portal-scattered | Low-Med (links-only, same pattern as trademark) |
| 15 | Trademark knockout via free API (vs links-only) | Atom one-click US/EU; trademark-mcp-server; NameIntel | Links only | No strictly — USPTO APIs are free but key-registered (60 req/min); web-search pass is the true key-free proxy | Med (document upgrade path) |
| 16 | Cross-language screening | WordSafety (19 langs, phonetic matching); naming agencies | **Yes** (LLM-based) | Yes | — (covered; add WordSafety deep link) |
| 17 | Name-style buckets / meaning tiers | Namelix styles, Wordoid quality dial | **Yes** (5 technique buckets) | — | — (covered; label the tier in output) |
| 18 | Iterative learning from user picks | Namelix (learns from saves) | Partial (avoid-list only, no positive signal) | Yes — prompt-side: "more like the ones user starred" | Med |
| 19 | Mechanical transforms (drop-vowel, pluralize, domain hacks) | Beast Mode, domain-check patterns | Partial (misspelling bucket; hacks are non-.com) | Yes | Low |
| 20 | Shareable shortlist | Beast Mode share, Atom | No | Yes — Artifact publish (private by default) | Low |
| 21 | Availability-first generation (only propose names whose .com is free) | one-word-domains, BrandBucket (inventory model) | No (generate → filter) | Different architecture; not worth it for coined names (coinages are usually free) | Low |

## 3. Per-gap notes (what, who, feasibility, sketch)

**Gap 1 — Multi-TLD (High).** Every single incumbent and every MCP server is multi-TLD; .com-only is the plan's most visible deficiency vs. the entire field, and 2025 data shows real drift (.com share 57% and falling; ~28% of startups picking .ai in Q1-2025; .io the B2B default). Sketch: keep .com as the primary verdict column, add a user-preferred-extensions parameter (default `.com` + suggest 2 by industry); RDAP endpoints for other TLDs resolve via the IANA bootstrap file (`data.iana.org/rdap/dns.json`, key-free, cacheable) — same tri-state logic. Caveat: ~189 ccTLDs lack RDAP (per domain-check's docs) → those return UNKNOWN honestly. Confidence: Verified (bootstrap mechanism; incumbents' coverage).

**Gap 4 — Dev-registry collisions (High, conditional).** namae.dev proves the pattern. For any tech-flavored business idea, `registry.npmjs.org/<name>`, `pypi.org/pypi/<name>/json`, `crates.io/api/v1/crates/<name>`, `api.github.com/orgs/<name>` are all key-free JSON GETs (GitHub unauthenticated = 60 req/h — enough for finalists only). Sketch: run only on the ≤10 finalists, only when the idea paragraph classifies as software/dev-tool; emit as soft flags, not vetoes. Confidence: Verified (namae's coverage list; endpoint key-freeness is Probable-to-Verified from long-standing public API behavior).

**Gap 7 — Domain history of "fresh" AVAILABLE names (High).** No name generator does this; domain-buying guides (Spaceship, DomCop, GoDaddy, Dynadot) all insist on it. An AVAILABLE .com may be a dropped domain with spam/PBN baggage — this materially changes whether the user should buy it, and the plan currently implies AVAILABLE = clean. Sketch: for finalists only, one GET to Wayback CDX (`web.archive.org/cdx/search/cdx?url=<name>.com&output=json&limit=5&fl=timestamp`) — zero snapshots = likely virgin name; snapshots present = flag "previously used, review history" with a deep link to `web.archive.org/web/*/<name>.com`. Optionally query Spamhaus DBL (`<name>.com.dbl.spamhaus.org` A-record via system resolver; note Spamhaus returns errors through Google/Cloudflare public resolvers, and DoH would be the wrong transport here — treat any failure as UNKNOWN). Confidence: Wayback CDX key-free Verified; DBL free-tier resolver caveat Probable.

**Gap 6 — Aftermarket detection (Med for .com).** Registry-premium pricing does not exist for .com (uniform Verisign pricing; premium tiers are a new-gTLD/ccTLD phenomenon per OpenSRS/Dynadot docs) — so the plan's "confirm at checkout" is mostly safe today. The real .com gap is the reverse: a TAKEN name that is actually buyable (parked/for-sale). Sketch: on TAKEN finalists, check NS records (already in DNS pass) against a small parked-lander list (sedoparking.com, afternic.com, dan.com, bodis.com, parkingcrew) → flag "taken but appears parked/for-sale — may be purchasable on aftermarket". Becomes High-priority if Gap 1 lands, because .ai/.io premium tiers WILL contradict an "AVAILABLE" verdict at checkout. Confidence: Probable.

**Gap 8 — Surface RDAP metadata for TAKEN names (Med).** The RDAP response the plan already fetches contains registration/expiration events. "Taken, but expires 2026-09-12 and no website resolves" is actionable intelligence every domainer tool surfaces and costs zero extra requests. Sketch: parse `events[]` from the RDAP JSON already in hand; add an expiry column for TAKEN survivors. Confidence: Verified (RDAP event structure is standard; domain-check `--info` demonstrates it).

**Gap 9 — Uniqueness/collision score as its own dimension (Med).** Looka explicitly checks "Google results for the name don't conflict"; the plan's common-law pass sees the same SERPs but only reports legal risk. Sketch: from the same web-search pass, count distinct existing businesses using the exact string; anchor 2 = zero collisions, 1 = collisions in unrelated industries, 0 = active same-space use (which likely also triggers the legal flag). Free — it's a scoring change, not a new fetch. Confidence: Verified (Looka behavior; implementation trivially true).

**Gap 10 — LLM-knowledge collision probe / AI findability (Med, novel).** NameIntel charges $0.05/call for this; we get it free because the skill runs inside a frontier model. If the model already strongly associates "Lumon" with a TV show or "Vercel" with an existing company, the name fails AI-era uniqueness — and LLMs are now a primary brand-discovery surface (GEO/AEO literature). Sketch: for each finalist, a self-probe prompt — "What existing companies, products, or works do you associate with the exact string X?" — score 0/1/2 on association strength; also catches famous-mark proximity misses from a second angle. Confidence: Probable (value); Verified (feasibility — it's a prompt).

**Gap 3 — Social handles (Med).** Atom/Looka/Panabee/Wordoid all advertise it, so users will expect it. But key-free checking is unreliable exactly where it matters: Sherlock's own docs concede false positives and excluded sites; X and Instagram block unauthenticated probes. Sketch: two-tier honesty — reliable probes (GitHub `api.github.com/users/<name>` 404 = free) reported as facts; unreliable platforms reported as deep links (`x.com/<name>`, `instagram.com/<name>`) for manual click, mirroring the plan's trademark links-only philosophy. Do NOT report tri-state for hostile platforms. Confidence: Verified (Sherlock false-positive docs).

**Gap 2 — TLD advice (Med).** Even while staying .com-first, one output line — "for your industry, .ai (28% of 2025 startups) or .io are credible fallbacks when the .com is taken; .ai carries premium pricing" — costs a static table and matches what every 2025 TLD guide covers. Confidence: Verified (guides exist); stats Probable.

**Gap 15 — Trademark upgrade path (Med).** Links-only is defensible and matches the disclaimer posture, but note in the skill docs: USPTO's TSDR/Open Data Portal APIs are free with a registered key (60 req/min status; bulk register downloads at developer.uspto.gov) — a future opt-in knockout search is possible without paid services; third-party free tiers (Goalie IP) and trademark-mcp-server exist. Not key-free strictly, so correctly out of v1 scope. Confidence: Verified (key requirement, rate limits).

**Gap 18 — Positive preference learning (Med).** Namelix's signature feature is learning from saved names. The plan only has a negative signal (avoid-list). Sketch: between rounds, ask the user to star favorites; inject "generate more names sharing the phonetic/semantic DNA of ⟨starred⟩" into the next round's prompt. Pure prompt engineering, zero cost. Confidence: Verified (Namelix behavior).

**Gaps 5, 12, 13, 14, 19, 20 (Low / Low-Med), one-liners.** App-store: iTunes Search API `itunes.apple.com/search?term=<name>&entity=software` is key-free — run on finalists for app ideas (Probable). Pronunciation audio: `say -v Samantha "<name>"` + optionally export AIFF — local, free, matches Looka's "hear it" (Verified feasibility). Logo preview: out of scope, but a zero-cost HTML wordmark specimen (3 Google-Fonts pairings per finalist) approximates Namelix's hook (Open — value unproven). Company registers: no generator does it; keep links-only (user's state SoS + Companies House search + OpenCorporates) next to the trademark links; full API integration needs keys and per-state chaos (Verified — OpenCorporates' own blog documents US fragmentation). Mechanical transforms: Beast-Mode-style drop-vowel/pluralize are already subsumed by the misspelling bucket; skip. Shareable shortlist: Artifact publish is available in-harness if the user asks; skip from core.

**Non-gaps (plan already at or above market):** technique-bucket forcing (≥ Namelix's 4 styles); cross-language check (LLM beats WordSafety's 3,000-word list; add wordsafety.com as a validation deep link); radio test + famous-mark veto (no generator has an explicit radio test); tri-state timestamped availability honesty (stronger than most incumbents' binary claims); rejected-with-reasons section (nobody does this); privacy stance (unique vs. all remote tools — state it as a feature in the output header).

**Two risks the plan should absorb from this survey:** (a) Wordoid's "quality level" dial and BrandBucket's curation criteria (easily pronounced, no spelling variants) validate the plan's scoring dimensions — but BrandBucket's criteria imply the *misspelling bucket* will systematically score poorly; consider capping its share per batch. (b) domain-check's docs note ~189 ccTLDs lack RDAP — relevant only if Gap 1 lands.

## 4. Sources (all accessed 2026-07-21)

**Tier 1 (official/vendor docs):**
- https://namelix.com/ (via search synthesis) — styles, free, learning
- https://www.namecheap.com/blog/beast-mode-the-game-changing-bulk-search-tool/ and https://www.namecheap.com/domains/bulk-domain-search/ — Beast Mode transforms, 1,164 TLDs, 5,000-keyword bulk
- https://domainr.com/docs/api — API deprecated notice
- https://www.fastly.com/documentation/reference/api/domain-management/domain-research/ and https://www.fastly.com/products/domain-research-api — premium/aftermarket status, IDNA
- https://instantdomainsearch.com/mcp — official MCP server, 3 tools, free, premium designations
- https://looka.com/business-name-generator/ — domain/social/reputation/Google-conflict checks, "hear how it sounds"
- https://www.brandbucket.com/academy/brandbucket-domain-criteria and /academy/brandbucket-advantage, /help/faq/sellers — curation criteria, pricing, logos
- https://github.com/saidutt46/domain-check — full feature list (fetched directly)
- https://github.com/pepa65/domaincheck ; https://github.com/Gadiguibou/rdapcheck
- https://github.com/imprvhub/mcp-domain-availability ; https://github.com/jordanburke/trademark-mcp-server
- https://github.com/sherlock-project/sherlock — false-positive documentation
- https://namae.dev/ (+ https://uechi.io/blog/give-your-app-slick-name/) — 15-registry checks
- https://nameintel.io/ — 5-dimension scoring, x402 pricing
- https://tsdr.uspto.gov/ , https://developer.uspto.gov/node/165462 , https://www.uspto.gov/trademarks/apply/check-status-view-documents/trademark-bulk-data — TSDR API key requirement, rate limits, bulk data
- http://wordsafety.com/ — 19 languages, phonetic matching
- https://generate.panabee.com/ — Panabee live URL
- https://support.opensrs.com/support/solutions/articles/201000063243-registry-premium-domains-guide ; https://www.dynadot.com/help/question/what-are-registry-premium-domains — registry premium tiers
- https://api.opencorporates.com/documentation/API-Reference ; https://blog.opencorporates.com/2025/05/28/why-is-it-so-hard-to-find-us-company-data/ — US registry fragmentation

**Tier 2 (expert/industry):**
- https://www.einpresswire.com/article/704184252/... — Squadhelp→Atom rebrand, ecosystem scope
- https://domaindetails.com/kb/best-tlds-for-startups ; https://www.eurodns.com/blog/the-10-tlds-that-defined-2025-and-why-they-matter ; https://register.domains/en/blog/io-domain-guide-2025 — TLD-by-industry stats (.ai 28% Q1-2025, .com 57%)
- https://www.spaceship.com/blog/domain-history-check/ ; https://www.domcop.com/blog/check-domain-history/ ; https://www.godaddy.com/resources/skills/check-domain-history ; https://www.dynadot.com/hub/domain-tools/domain-history-ways-to-check — Wayback + Spamhaus DBL history-check practice
- https://thecuberesearch.com/ai-engine-optimization/ ; https://www.yotpo.com/blog/llm-optimization/ — GEO/AEO brand-discovery shift
- https://domainnamewire.com/2022/07/26/can-registries-change-the-pricing-tiers-of-your-premium-domains/ — premium tier mechanics
- https://www.prnewswire.com/news-releases/looka-launches-business-name-generator-to-re-imagine-brand-naming-301298294.html

**Tier 3 (empirical/directory):**
- https://terminaltrove.com/domain-check/ ; https://mcp.so/tags/domain (13 domain MCP servers) ; https://mcpservers.org/servers/imprvhub/mcp-domain-availability ; https://www.pulsemcp.com/servers/vinsidious-whodis ; https://glama.ai/mcp/servers/@dorukardahan/domain-search-mcp/tools/check_socials
- https://aitoolindex.io/tools/namelix ; https://siteefy.com/tools/namelix ; https://manytools.com/review/domainr/

**Tier 4 (community):**
- https://news.ycombinator.com/item?id=10117297 (WordSafety) ; https://www.namepros.com/blog/meet-steven-tey-the-young-developer-of-one-word-domains.1219481/ ; https://steventey.medium.com/whats-new-in-one-word-domains-2-0-38fe9a97ff4a ; https://www.producthunt.com/products/squadhelp ; https://dev.to/uetchy/give-your-app-slick-name-with-namae-dev-5c4h ; https://wbcomdesigns.com/best-startup-naming-tools/ ; https://www.guru99.com/blog-name-generators.html
