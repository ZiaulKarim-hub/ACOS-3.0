# Appendix A — RDAP Multi-TLD Domain Availability Research (Agent 1 raw dossier)

**Research date:** 2026-07-21 (all live probes executed 2026-07-22 ~04:55–05:30 UTC from a US vantage point). All empirical HTTP results below were obtained via direct `curl` against production endpoints during this session (Tier 3 evidence, reproducible).

**Confidence scale:** Verified = 3+ independent sources/evidence classes · Probable = 2 · Open = 1.

---

## Q1 — IANA RDAP Bootstrap Registry (`dns.json`)

**Purpose (Verified):** `https://data.iana.org/rdap/dns.json` is the IANA "bootstrap" registry mapping TLDs → authoritative RDAP base URLs. It is the mechanism defined in **RFC 9224** ("Finding the Authoritative Registration Data Access Protocol (RDAP) Service", **Internet Standard STD 95**, published 2022, **obsoletes RFC 7484**) [RFC-Editor info page, accessed 2026-07-21; Tier 1]. Verisign's own RDAP help page lists RFC 9224 among the RFCs it implements [verisign.com/news-insights/registration-data-access-protocol/help/, accessed 2026-07-21; Tier 1]. rdap.org describes itself as an aggregator of exactly this registry [about.rdap.org, accessed 2026-07-21; Tier 2].

**Client resolution algorithm (per RFC 9224, confirmed working empirically — Verified):**
1. Fetch `https://data.iana.org/rdap/dns.json` (plain HTTPS GET — **no key, no auth, free**; confirmed by direct fetch this session).
2. Structure: `{"description": ..., "publication": "<ISO timestamp>", "services": [ [ [tld, tld...], [baseURL, ...] ], ... ] }`. Observed publication: `2026-07-14T22:00:03Z`.
3. Find the service entry whose TLD array contains the target label (case-insensitive; use the A-label/punycode form for IDN TLDs — e.g., the file contains `xn--kpry57d`).
4. Take a base URL from that entry (prefer the `https://` one), then append the RDAP path per RFC 9082: `<base>domain/<fqdn>` (base URLs in the file end with `/`).
5. If the TLD is absent from the file → no IANA-registered RDAP service exists (this does NOT prove no RDAP exists at all — see Q3: .io/.sh/.me/.us/.de/.so/.co all have working RDAP outside the bootstrap).

**Update cadence (Probable):** No fixed schedule; IANA republishes when registrations change. Observed HTTP headers: `last-modified: Tue, 14 Jul 2026 22:00:03Z`, `cache-control: max-age=86400`, `etag` present — i.e., IANA itself signals 24-hour caching. Practical rule for the skill: cache `dns.json` locally, revalidate with `If-None-Match`/`If-Modified-Since` no more than daily. RFC 9224 instructs clients to cache and periodically refresh.

---

## Q2 — WHOIS (port 43) Sunset

**Status (Verified, primary source obtained directly):** ICANN announcement "ICANN Update: Launching RDAP; Sunsetting WHOIS," dated 27 January 2025, states verbatim: *"As of 28 January 2025, the Registration Data Access Protocol (RDAP) will be the definitive source for delivering generic top-level domain name (gTLD) registration information in place of sunsetted WHOIS services."* [icann.org announcement, full text retrieved via curl this session; Tier 1].

Key nuances (Verified across ICANN + Tier 2 coverage):
- The sunset **removed the contractual requirement** for gTLD registries/registrars to operate WHOIS port 43; it did **not order a shutdown**. Operators may keep WHOIS voluntarily [WhoisXML API blog; seo.domains; dynadot.com; cctld.ru — all accessed 2026-07-21; Tier 2].
- Scope is **gTLDs only**. ccTLDs are not subject to ICANN contracts and may run WHOIS indefinitely (see Q4).
- WHOIS decay is real and ongoing: one Tier 2 count says 374 gTLDs had already shut port 43 (Open — single source). **Verified concrete example:** Identity Digital deprecated WHOIS port 43 and web WHOIS for its entire portfolio on **2025-08-04**, going RDAP-only [identity.digital Help Center WHOIS FAQ, accessed 2026-07-21; Tier 1].

**Implication for a `whois`-fallback design (Verified):** `whois` is now a *decaying, per-registry-optional* channel for gTLDs — it can disappear per-TLD at any time without notice, and output formats were never standardized. RDAP must be the primary path for all gTLDs; port-43 WHOIS should be reserved strictly for TLDs with no RDAP at all (in our list: only .gg), and treated as best-effort. Note also an empirical warning: `whois.registry.co` answered "DOMAIN NOT FOUND" for **t.co**, a registered domain (probable post-migration breakage or non-standard query format) — WHOIS fallbacks can silently lie after registry transitions.

---

## Q3 — Per-TLD RDAP Coverage (25 TLDs)

Every "HTTP" cell below is an empirical result from this session (Tier 3). "Bootstrap" = present in `dns.json` publication 2026-07-14 (Tier 1). "IANA page" = RDAP server field on `iana.org/domains/root/db/<tld>.html` (Tier 1).

| TLD | Type | RDAP exists? | In IANA bootstrap? | RDAP base URL | Empirical evidence (this session) | No-RDAP fallback | Confidence |
|---|---|---|---|---|---|---|---|
| .com | gTLD (Verisign) | Yes | Yes | `https://rdap.verisign.com/com/v1/` | 200 example.com | n/a | **Verified** |
| .net | gTLD (Verisign) | Yes | Yes | `https://rdap.verisign.com/net/v1/` | bootstrap + Verisign help page | n/a | **Verified** |
| .org | gTLD (PIR) | Yes | Yes | `https://rdap.publicinterestregistry.org/rdap/` | 200 wikipedia.org | n/a | **Verified** |
| .io | ccTLD (Chagos/BIOT) | **Yes — but NOT bootstrapped** | **No** | `https://rdap.identitydigital.services/rdap/` | 200 nic.io; 404 gibberish.io | (whois.nic.io listed at IANA, but Identity Digital killed port 43 Aug 2025) | **Verified** (empirical + ID Digital WHOIS-deprecation notice + backend lineage ICB→Afilias→Identity Digital) |
| .ai | ccTLD (Anguilla) | **Yes** | **Yes** | `https://rdap.identitydigital.services/rdap/` | 200 nic.ai; 404 gibberish.ai | n/a | **Verified** |
| .co | ccTLD (Colombia) | Yes — NOT bootstrapped | No | `https://rdap.registry.co/co/` (zone-scoped path — `/domain/x.co` without `/co/` 404s for everything) | 200 t.co, registry.co; 404 gibberish.co; ICANN-profile `rdapConformance` strings | whois.registry.co exists but returned DOMAIN NOT FOUND for t.co (unreliable) | **Probable** (empirical + CentralNic zone-path convention; no official doc found) |
| .app | gTLD (Google Registry) | Yes | Yes | `https://pubapi.registry.google/rdap/` | 200 get.app | n/a | **Verified** |
| .dev | gTLD (Google Registry) | Yes | Yes | `https://pubapi.registry.google/rdap/` | 200 web.dev | n/a | **Verified** |
| .xyz | gTLD (XYZ/CentralNic backend) | Yes | Yes | `https://rdap.centralnic.com/xyz/` | 200 nic.xyz | n/a | **Verified** |
| .tech | gTLD (Radix) | Yes | Yes | `https://rdap.radix.host/rdap/` | 200 nic.tech | n/a | **Verified** |
| .me | ccTLD (Montenegro) | Yes — NOT bootstrapped | No (IANA page: no RDAP, record 2020) | `https://rdap.identitydigital.services/rdap/` | 200 domain.me (valid domain object); 404 gibberish.me; `whois.nic.me` CNAMEs to `whois.identitydigital.services` | whois.nic.me port 43 (verified working via `whois` command) | **Probable** (empirical + DNS CNAME backend proof; no official doc) |
| .us | ccTLD (US; Registry Services LLC / GoDaddy Registry) | Yes — NOT bootstrapped | No (IANA page: no RDAP) | `https://rdap.nic.us/` | 200 nic.us with `icann_rdap_response_profile_1` conformance; 404 gibberish.us | whois.nic.us port 43 | **Probable** (empirical + IANA operator record; no formal endpoint doc found) |
| .uk | ccTLD (Nominet) | **Yes** | **Yes** | `https://rdap.nominet.uk/uk/` | 200 nic.uk; 404 gibberish.co.uk (covers .co.uk tree) | Nominet DAS exists but is registrar/tag-gated — not the no-key path | **Verified** |
| .de | ccTLD (DENIC) | Yes — NOT bootstrapped, officially "test operation" | No (IANA page: no RDAP) | `https://rdap.denic.de/` | 200 denic.de (`denic_version_0` conformance); 404 gibberish.de | whois.denic.de port 43 (status-only output) | **Verified** (empirical + DENIC official RDAP service page + docs.denic.de) — flag DENIC's no-SLA "pilot" language |
| .ca | ccTLD (CIRA) | Yes | Yes | `https://rdap.ca.fury.ca/rdap/` | 200 cira.ca | n/a | **Verified** |
| .in | ccTLD (NIXI) | Yes | Yes | `https://rdap.nixiregistry.in/rdap/` | 200 nixi.in | n/a | **Verified** |
| .sh | ccTLD (St Helena) | Yes — NOT bootstrapped | No (IANA page: no RDAP, record 2023) | `https://rdap.identitydigital.services/rdap/` | 200 nic.sh; 404 gibberish.sh | whois.nic.sh (same Identity Digital deprecation risk) | **Verified** (same evidence class as .io) |
| .gg | ccTLD (Guernsey, Island Networks) | **NO RDAP** | No | — (rdap.nic.gg has no DNS record; rdap.org → 404; IANA page: no RDAP, record updated 2025-07-07) | port-43 probe of whois.gg returned full record for nic.gg | **whois.gg port 43** (verified working); else DNS inference only | **Verified** (no-RDAP) |
| .so | ccTLD (Somalia) | Yes — NOT bootstrapped | No (IANA page: no RDAP) | `https://rdap.nic.so/` | 200 nic.so with ICANN-profile conformance; 404 gibberish.so | whois.nic.so port 43 | **Probable** (empirical + IANA whois-host naming; no doc found) |
| .id | ccTLD (Indonesia, PANDI) | Yes — official | **Yes** (also listed on IANA root page) | `https://rdap.pandi.id/rdap/` | **UNREACHABLE from US vantage: 3/3 connection timeouts incl. 45 s** | whois.id port 43 (IANA-listed) | **Verified** existence (bootstrap + IANA page); **reliability from US: poor (empirical)** |
| .site | gTLD (Radix) | Yes | Yes | `https://rdap.radix.host/rdap/` | same host as .tech (probed 200) | n/a | **Verified** |
| .online | gTLD (Radix) | Yes | Yes | `https://rdap.radix.host/rdap/` | same host | n/a | **Verified** |
| .store | gTLD (Radix) | Yes | Yes | `https://rdap.radix.host/rdap/` | same host | n/a | **Verified** |
| .cloud | gTLD (Aruba PEC) | Yes | Yes | `https://rdap.registry.cloud/rdap/` | 200 nic.cloud | n/a | **Verified** |
| .fun | gTLD (Radix) | Yes | Yes | `https://rdap.radix.host/rdap/` | same host | n/a | **Verified** |

**404/200 semantics verified empirically on:** Verisign (.com), Identity Digital (.ai/.io/.sh/.me), Nominet (.uk), DENIC (.de), Team Internet (.co), rdap.nic.us, rdap.nic.so — all returned **404 for gibberish names, 200 for registered names**. Caution: 404 = "no object" = *appears available*; reserved/premium/blocked names can also 404 — final truth is only at a registrar checkout.

### Special attention: .ai (Anguilla)
- Historically WHOIS-only (`whois.nic.ai`, Vince Cate–era custom registry). **The Identity Digital backend migration brought RDAP:** the IANA root-db page for .ai now lists **RDAP Server: `https://rdap.identitydigital.services/rdap/`**, record last updated **2025-02-11** — matching the early-2025 migration window [iana.org/domains/root/db/ai.html, accessed 2026-07-21; Tier 1]. .ai is also **in the IANA bootstrap** (rare for a ccTLD) — Verified (IANA page + bootstrap + empirical 200/404).

### Special attention: .io
- Backend lineage: Internet Computer Bureau (1997) → sold to Afilias 2017 → Donuts acquired Afilias 2020 → 2022 merger formed Identity Digital, which operates .io's backend via its ICB subsidiary [Wikipedia .io/Identity Digital; domainincite.com; accessed 2026-07-21; Tier 2].
- **Empirically served today by `rdap.identitydigital.services`** (200/404 semantics correct), but — unlike .ai — .io is **NOT in the IANA bootstrap and NOT on its IANA root-db page** (record last updated 2023-01-18). So bootstrap-only clients and rdap.org think .io has no RDAP. The skill must **hardcode** the Identity Digital base for .io/.sh/.me, and re-check the bootstrap periodically (ccTLDs do get added — .ai was).

---

## Q4 — ccTLD Caveat

**Confirmed (Verified):** ccTLDs have no ICANN contractual obligation to deploy RDAP; adoption is voluntary, per-registry, driven by local policy. Roughly **60% of ccTLDs had deployed RDAP as of early 2026** (+12% since January 2025) [IETF blog "The current state of RDAP" / APNIC Blog mirror 2026-02-10; ICANN OCTO-024 RDAP primer; cctld.ru news; all accessed 2026-07-21; Tiers 1–2].

Within our list:
- **True holdout (no RDAP at all): .gg** (Island Networks; port-43 `whois.gg` only).
- **"Shadow RDAP" group (working RDAP, but not IANA-bootstrapped, so invisible to spec-compliant clients): .io, .sh, .me, .us, .so, .de, .co.** These require hardcoded overrides in the skill.
- **Bootstrapped ccTLDs (behave like gTLDs for resolution): .ai, .uk, .ca, .in, .id** (.id with a US-reachability caveat).

---

## Q5 — Rate Limits / Anti-Abuse per Operator

General protocol rule (Verified): RFC 7480 defines RDAP-over-HTTP; a rate-limited server answers **429 Too Many Requests** and clients SHOULD slow down and honor **Retry-After** [RFC 7480 via datatracker; rdapapi.io; accessed 2026-07-21; Tiers 1–2].

| Operator (TLDs here) | Published limits | Notes |
|---|---|---|
| **Verisign** (.com/.net) | **None published** (Verified absence: help page silent; Tier 2 sources confirm no public thresholds) | Returns 429 under load; community reports say casual use never hits it. No `X-RateLimit`/`Retry-After` headers observed on a normal 200. |
| **Identity Digital** (.ai/.io/.sh/.me + hundreds of gTLDs) | **"Queries to the RDDS are throttled"** — RDDS Access Policy restricts high-volume automated queries without authorization; no numbers published | WHOIS fully retired 2025-08-04, RDAP-only [identity.digital RDDS Access Policy + WHOIS FAQ; Tier 1]. **Probable** |
| **Nominet** (.uk) | **Yes — explicit:** 1,000 queries per rolling 60 s (recalculated every 5 s); daily cap formula (registrar-tag-based: 5× domains-on-tag + 200× peak monthly new regs, capped at 3M/day; >480k daily → rate raised to 3× daily/1440); limits applied equally to all IPs/subnets | [registrars.nominet.uk RDAP + ToS pages; Tier 1]. **Verified.** DAS is a separate registrar-only channel. |
| **Google Registry** (.app/.dev) | Nothing published found | Assume 429 semantics per RFC 7480. **Open** |
| **Public Interest Registry** (.org) | Nothing published found | **Open** |
| **Radix** (.tech/.site/.online/.store/.fun) | No numeric limits published; `rdap.radix.host` landing page documents domain/nameserver/entity + wildcard search; AUP is registrant-focused | **Probable** |
| **Team Internet / CentralNic** (.co since 2025-10-03, .xyz) | Nothing published found | **Open** |
| **GoDaddy Registry / Registry Services LLC** (.us) | Nothing published found | **Open** |
| **DENIC** (.de) | RDAP offered as pilot/"test operation", **no service-level guarantee** | [denic.de RDAP Service page; Tier 1]. **Verified** |
| **rdap.org** (aggregator) | **10 requests / 10 seconds** (Cloudflare-enforced), 429 beyond | [about.rdap.org; Tier 2]. **Verified** (also observed timeouts empirically) |

**Etiquette for a 100–200-lookup run (synthesis, grounded in RFC 7480 + Nominet's published numbers):** query registries directly (skip rdap.org); serialize or cap concurrency at ~2–4; space requests ~100–250 ms (≤10 rps/registry stays 100× under Nominet's only published ceiling); on 429 honor Retry-After else exponential backoff with jitter; cache `dns.json` 24 h and per-domain results per run; send a descriptive User-Agent. At 100–200 lookups spread across many TLD registries, per-registry volume is trivially low.

---

## Q6 — Aggregators

**rdap.org (Verified):**
- Community-run redirector by Gavin Brown (personal project, though he is an ICANN employee). Query `https://rdap.org/domain/<name>` → **HTTP 302** with `Location:` pointing to the authoritative registry RDAP server. Confirmed empirically: `example.com` → 302 → `https://rdap.verisign.com/com/v1/domain/example.com`.
- **Coverage = IANA bootstrap only.** Per about.rdap.org it "only knows about RDAP servers registered with IANA"; empirically it returned **404 for t.co, nic.me, nic.io, nic.gg** — all four of which either have working non-bootstrapped RDAP (.co/.me/.io) or exist (.gg). **Therefore a 404 from rdap.org is NOT an availability signal and it adds no ccTLD coverage beyond doing the bootstrap yourself.**
- Rate-limited (10 req/10 s via Cloudflare) and **empirically flaky**: during this session it timed out on 5 consecutive requests (~20–30 s each), then worked minutes later.
- **Verdict for the skill:** materially *worse* than following the IANA bootstrap directly — same coverage, plus a rate cap, an extra round trip, and a single point of failure. Use the bootstrap + hardcoded ccTLD overrides.

**Other key-free options (with catches):**
- **lookup.icann.org** — ICANN's official RDAP web lookup (Tier 1, cited in the sunset announcement). Web UI aimed at humans; its backing API is undocumented/unversioned; gTLD-focused. Not suitable as a programmatic dependency.
- **ICANN's open-source RDAP CLI client and other clients** (linked from the ICANN announcement; e.g., OpenRDAP) — these implement RFC 9224 bootstrap resolution locally; useful as reference implementations, not as services.
- **rdap.cloudflare.com and other registrar RDAP servers** — answer only for domains sponsored by that registrar; useless for availability. (Registrar RDAP ≠ registry RDAP.)
- **DNS-over-HTTPS (dns.google, cloudflare-dns.com)** — key-free, effectively unlimited; only usable for the *taken* half of the DNS-inference rule (Q7).
- Anything from WhoisXML/similar commercial APIs requires keys — out of scope by design constraint.

---

## Q7 — DNS-Inference Correctness Rule (for .gg and any RDAP/WHOIS-dead zone)

Restated rule (design doctrine; supporting mechanics Verified):

1. **A positive DNS answer proves TAKEN.** If a query for `NS` (or `SOA`) on the exact domain returns records, the domain is delegated in the registry zone → it is registered. Safe to report TAKEN.
2. **NXDOMAIN proves NOTHING.** A domain can be registered yet absent from the zone: registered-but-no-nameservers, or held out of zone by EPP statuses such as `serverHold`/`clientHold` (registered domains removed from the zone — a documented registry mechanism [regway.com KB on serverHold, accessed 2026-07-21; Tier 4]; the status codes themselves are ICANN/EPP standard, icann.org/epp). Reserved, premium-held, and registry-blocked names also resolve to NXDOMAIN while being unregistrable.
3. **Therefore: never report AVAILABLE from DNS alone.** The only honest outputs from a DNS-only check are TAKEN (positive answer) or **UNKNOWN — "no delegation found; availability cannot be confirmed, verify at a registrar"**.
4. Implementation notes: query the authoritative chain or a hard-validating resolver (DoH with `AD`/status field), ask for `NS` on the apex name exactly, and treat SERVFAIL/timeouts as UNKNOWN, never as available.

This rule applies in our list only to **.gg** (if its port-43 WHOIS is unavailable or rate-limits) and as a cheap TAKEN-prefilter before RDAP for any TLD.

---

## Key Design Deliverables (synthesis for the skill)

1. **Resolution order per TLD:** (a) local override table (below) → (b) cached IANA bootstrap → (c) if neither: WHOIS port 43 if a server is IANA-listed → (d) DNS inference (TAKEN/UNKNOWN only).
2. **Required override table (not in bootstrap as of 2026-07-14):**
   - `.io`, `.sh`, `.me` → `https://rdap.identitydigital.services/rdap/`
   - `.co` → `https://rdap.registry.co/co/` (note the mandatory `/co/` zone segment)
   - `.us` → `https://rdap.nic.us/`
   - `.so` → `https://rdap.nic.so/`
   - `.de` → `https://rdap.denic.de/` (pilot status; keep whois.denic.de as backup)
   - `.gg` → **no RDAP**: whois.gg port 43, else DNS-inference
3. **.id caveat:** official endpoint `https://rdap.pandi.id/rdap/` is IANA-canonical but timed out consistently from a US vantage (possible geo-restriction/instability) — the skill needs a timeout→WHOIS(whois.id)→DNS fallback chain here.
4. **Semantics everywhere:** 200 = taken; 404 = *appears* available (reserved/premium caveat); 429 = back off with Retry-After; anything else/timeout = UNKNOWN.

---

## Source List

| # | Source | Tier | Accessed | Used for |
|---|---|---|---|---|
| 1 | https://data.iana.org/rdap/dns.json (direct fetch, publication 2026-07-14T22:00:03Z) | 1 | 2026-07-21 | Q1, Q3 bootstrap presence/URLs |
| 2 | https://www.rfc-editor.org/info/rfc9224 | 1 | 2026-07-21 | Q1 (STD 95, obsoletes RFC 7484) |
| 3 | RFC 7480 — https://datatracker.ietf.org/doc/rfc7480/ | 1 | 2026-07-21 | Q5/Q7 (429/Retry-After) |
| 4 | https://www.icann.org/en/announcements/details/icann-update-launching-rdap-sunsetting-whois-27-01-2025-en (full text via curl) | 1 | 2026-07-21 | Q2 |
| 5 | https://www.iana.org/domains/root/db/ai.html | 1 | 2026-07-21 | Q3 .ai (RDAP listed, record 2025-02-11) |
| 6 | https://www.iana.org/domains/root/db/io.html | 1 | 2026-07-21 | Q3 .io (no RDAP listed) |
| 7 | https://www.iana.org/domains/root/db/co.html | 1 | 2026-07-21 | Q3 .co (MinTIC, record 2026-02-17) |
| 8 | https://www.iana.org/domains/root/db/me.html | 1 | 2026-07-21 | Q3 .me |
| 9 | https://www.iana.org/domains/root/db/us.html | 1 | 2026-07-21 | Q3 .us |
| 10 | https://www.iana.org/domains/root/db/gg.html | 1 | 2026-07-21 | Q3 .gg |
| 11 | https://www.iana.org/domains/root/db/sh.html | 1 | 2026-07-21 | Q3 .sh |
| 12 | https://www.iana.org/domains/root/db/so.html | 1 | 2026-07-21 | Q3 .so |
| 13 | https://www.iana.org/domains/root/db/de.html | 1 | 2026-07-21 | Q3 .de |
| 14 | https://www.iana.org/domains/root/db/id.html | 1 | 2026-07-21 | Q3 .id (RDAP listed) |
| 15 | https://www.verisign.com/news-insights/registration-data-access-protocol/help/ | 1 | 2026-07-21 | Q1/Q3/Q5 (.com/.net base URLs, RFC list, no published limits) |
| 16 | https://www.denic.de/en/service/whois-service/rdap-service (+ docs.denic.de Domain Query) | 1 | 2026-07-21 | Q3/Q5 .de RDAP pilot |
| 17 | https://www.identity.digital/help-articles/whois-faq | 1 | 2026-07-21 | Q2/Q3 (WHOIS retired 2025-08-04, RDAP-only) |
| 18 | https://www.identity.digital/policies/rdds-access-policy | 1 | 2026-07-21 | Q5 (throttling policy) |
| 19 | https://registrars.nominet.uk/rdap/ (+ /rdap/tos/, how-to-use-rdap) | 1 | 2026-07-21 | Q3/Q5 .uk limits |
| 20 | https://www.icann.org/en/system/files/files/octo-024-14dec22-en.pdf (RDAP primer) | 1 | 2026-07-21 | Q4 |
| 21 | https://www.ietf.org/blog/current-state-of-rdap/ + https://blog.apnic.net/2026/02/10/the-current-state-of-rdap/ | 2 | 2026-07-21 | Q4 (~60% ccTLD adoption) |
| 22 | https://about.rdap.org/ | 2 | 2026-07-21 | Q6 (redirector mechanics, 10/10s limit, IANA-only coverage) |
| 23 | https://main.whoisxmlapi.com/blog/icanns-whois-port-43-shutdown-what-it-means-for-you | 2 | 2026-07-21 | Q2 (374 gTLDs count — Open) |
| 24 | https://seo.domains/seo-resources/whois-rdap/rdap-successor-to-whois/ ; https://www.dynadot.com/hub/domain-management/whois-vs-rdap ; https://cctld.ru/en/media/news/industry/37446/ | 2 | 2026-07-21 | Q2/Q4 corroboration |
| 25 | https://domainincite.com/31134-godaddy-loses-co-to-team-internet ; https://teaminternet.com/team-internets-centralnic-registry-successfully-migrates-co-domain-names/ ; https://webhosting.today/2025/06/16/team-internet-wins-control-of-colombias-co-domain-godaddy-out/ ; https://domainnamewire.com/2025/06/12/big-new-godaddy-loses-co-contract-to-tig-partnership/ | 2 | 2026-07-21 | Q3 .co transition (Equipo PuntoCo, migration 2025-10-03) |
| 26 | https://en.wikipedia.org/wiki/.io ; https://en.wikipedia.org/wiki/Identity_Digital ; https://domainincite.com/30850-is-io-safe-now-identity-digital-now-running-mauritian-cctld ; https://en.wikipedia.org/wiki/.me ; https://en.wikipedia.org/wiki/.us | 2 | 2026-07-21 | Q3 backend lineage |
| 27 | https://rdapapi.io/blog/verisign-rdap-endpoint ; https://rdapapi.io/blog/whois-rate-limits ; https://domaindetails.com/kb/technical-guides/whois-vs-rdap-comparison | 2 | 2026-07-21 | Q5 (Verisign 429 behavior, unpublished thresholds) |
| 28 | https://rdap.radix.host/ (landing/docs) ; https://radix.website/policies | 1–2 | 2026-07-21 | Q3/Q5 Radix |
| 29 | Empirical curl probes of 20+ endpoints (all HTTP codes in Q3 table; 404-semantics tests on 9 registries; rdap.org 302/404/timeout behavior; whois.gg + whois.nic.me port-43 tests; whois.registry.co false-negative; rdap.pandi.id 3× timeout; whois.nic.me CNAME → whois.identitydigital.services) | 3 | 2026-07-21/22 UTC | Q3, Q5, Q6 |
| 30 | https://support.regway.com/knowledgebase.php?article=48 (serverHold explainer) | 4 | 2026-07-21 | Q7 (registered-but-not-in-zone mechanism) |
| 31 | https://www.acorndomains.co.uk/threads/nominet-uk-rdap.173119/ | 4 | 2026-07-21 | Q5 .uk corroboration |
