# Old-Information Bias in Evidence-Weighted Synthesis
## Recency vs. Reliability — a cited design study for `acos-axiom-synthesis`

**Author:** deep-research agent (ACOS)
**Date:** 2026-08-02
**Scope:** Research questions 1–5 from the design brief, plus a concrete recommendation mapped onto the skill's existing hooks (`N5-NOT-STALE` / `freshness_ok`, `grade_claim` `stale` downgrade, the `resolve.py` `recency_correction` ladder rung, `--mode actual|synthesis`).
**Method:** WebSearch + WebFetch across library science, evidence-based medicine, information retrieval, ML, temporal databases, and LLM-temporal-alignment literatures. Every non-obvious claim is cited. Items I could not verify to a primary source are flagged **UNVERIFIED**.

---

## 1. Executive summary (≤200 words)

An evidence-weighted synthesizer that grades confidence by independent corroboration structurally favors **older** claims: they have had more time to accumulate citations and cross-references. In fast-moving domains (AI/ML, software, security, prices, "state-of-the-art") the well-corroborated old claim is often **obsolete**, and the correct answer is a recent claim with **thinner** evidence. This is a real, named problem across fields — the **half-life of facts** (Arbesman), **concept/data drift** (ML), **temporal validity** (IR/KGs), and **currency** in source-evaluation (CRAAP/RADAR). Mature fields already counter it: **living systematic reviews** (continuous surveillance), **bitemporal / "as-of" dating**, **time-decay ranking**, **query-deserves-freshness**, and **supersession** rules in standards.

The fix is not "trust the newest thing." It is to (1) **classify each claim's volatility** (durable vs. volatile), (2) keep **recency as a separate axis from reliability**, (3) **cap** the tier of stale *volatile* claims, (4) require **≥1 recent independent source** before a volatile claim reaches the top tier, and (5) let a **corroborated, equal-or-higher-tier newer source supersede** an older one — all **behind the existing de-circularization firewall and the ≥2-independent-family floor**, so recency reweights *which* well-evidenced claim wins without letting a single fresh source win.

---

## 2. The named concepts and how each frames the problem

The phenomenon has no single canonical name; it appears under a family of related concepts, each contributing a different lever.

### 2.1 Citogenesis / circular reporting / citation cascades — *why old evidence over-counts*
"Circular reporting" (a.k.a. **citogenesis**, coined by Randall Munroe in xkcd #978, 2011) is a source-criticism failure in which information "appears to come from multiple independent sources, but in reality comes from only one source." ([Circular reporting, Wikipedia](https://en.wikipedia.org/wiki/Circular_reporting); [explain xkcd 978](https://www.explainxkcd.com/wiki/index.php/978:_Citogenesis)). Crucially for *this* problem, the Wikipedia community notes it is "hard to catch because of the speed of revisions of modern webpages, and the lack of 'as of' timestamps in citations and 'last updated' timestamps on pages" ([Slate, 2019](https://slate.com/technology/2019/03/wikipedia-citogenesis-circular-reporting-problem.html)). **Framing:** an old claim's high corroboration count may be citation *echo*, not independent support — so time both *accumulates* corroboration and *hides* its non-independence. This is exactly why de-circularization must run before any recency logic.

### 2.2 Information cascades / rational herding — *why corroboration count ≠ truth*
Bikhchandani, Hirshleifer & Welch (1992) show that fully rational agents who imitate predecessors can converge — collectively and confidently — on the **wrong** answer, because each optimally ignores private information ([BHW cascades survey, Caltech PDF](https://www.tamuz.caltech.edu/papers/cascades_survey.pdf); [Palgrave entry PDF](https://bpb-us-e2.wpmucdn.com/sites.uci.edu/dist/c/362/files/2017/01/Palgrave-information-cascades-Online-version.pdf)). **Framing:** volume of agreement is not proportional to correctness; both a stale majority and a fresh bandwagon can be cascades.

### 2.3 Half-life of facts / knowledge decay — *the temporal axis of truth*
Arbesman's *The Half-Life of Facts* (2012) applies radioactive-decay intuition to knowledge: the truth-value of a body of facts "tends to fall along a decaying exponential function." A cited study of hepatology found the half-life of clinical knowledge about cirrhosis/hepatitis to be **~45 years** ([fs.blog summary](https://fs.blog/the-half-life-of-facts/); [SciTechDaily](https://scitechdaily.com/samuel-arbesman-explains-the-half-life-of-facts/)). **Framing:** decay rate is *domain-specific* — 45 years for liver disease implies days-to-months for prices or "SOTA." This is the origin of the per-domain half-life idea. (The 45-year figure is Arbesman's reporting of a hospital study; the underlying paper is cited secondarily and I did not read it — **the specific number is UNVERIFIED to primary source**.)

### 2.4 Concept drift & data drift (ML) — *the operational analog*
**Concept drift** = the joint distribution linking inputs to outputs "evolves over time," so historical data mismatches the current target; **data drift / covariate shift** = the input distribution alone shifts. Drift comes in gradual, recurring/cyclical, and sudden/abrupt forms ([Lu et al., *Learning under Concept Drift: A Review*, arXiv:2004.05785](https://arxiv.org/pdf/2004.05785); [Frontiers in AI 2024 survey](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2024.1330257/full); [Dataversity](https://www.dataversity.net/articles/data-drift-vs-concept-drift-what-is-the-difference/)). **Framing:** ML already treats "the world moved, my well-fit old model is now wrong" as a first-class, detectable, *adaptable* problem — the direct engineering analog of stale-but-well-supported claims.

### 2.5 Temporal validity / temporal information retrieval — *facts have valid-time windows*
Kanhabua, Blanco & Nørvåg's survey *Temporal Information Retrieval* (2015) formalizes how relevance varies with time; related work stresses that "truth can vary over time, so fact-checking decisions ... should take into account temporal information of both the claim and supporting or refuting evidence" ([survey PDF](https://www.dc.fi.udc.es/~roi/publications/fntir-temporalweb_ebook.2015.pdf); [ACM Computing Surveys 2014, 10.1145/2619088](https://dl.acm.org/doi/10.1145/2619088)). **Framing:** a claim is not simply true/false but true *within a valid-time interval*; evidence must be time-matched to the claim.

### 2.6 Knowledge cutoff & temporal misalignment (LLMs) — *the freshest instance of the problem*
"Temporal misalignment" = model degradation caused by the gap between training-time and test-time periods, from language change or fact updates ([*Set the Clock*, arXiv:2402.16797](https://arxiv.org/pdf/2402.16797); benchmarks **TempLAMA** and **RealTimeQA**, [survey context arXiv:2306.08952](https://arxiv.org/html/2306.08952); [TemporalWiki, arXiv:2204.14211](https://arxiv.org/pdf/2204.14211)). The **FreshQA/FreshLLMs** work (Vu et al., Google, arXiv:2310.03214, Oct 2023; ACL Findings 2024) is the most directly useful: it partitions questions into **never-changing / slow-changing / fast-changing / false-premise**, and finds that "all models (regardless of model size) struggle on questions that involve fast-changing knowledge and false premises" ([arXiv:2310.03214](https://arxiv.org/abs/2310.03214)). **Framing:** the never/slow/fast taxonomy is a ready-made, empirically-motivated volatility scheme; the false-premise category maps to the synthesizer's refutation gate.

### 2.7 "Currency" in source-evaluation frameworks — *the library-science lever*
**CRAAP** (Currency, Relevance, Authority, Accuracy, Purpose; Blakeslee, CSU Chico) makes **Currency** — "the timeliness of a source ... up-to-date" — a first-class evaluation axis, *separate* from Authority ([CRAAP test, Wikipedia](https://en.wikipedia.org/wiki/CRAAP_test)). **RADAR** (Relevance, Authority, **Date**, Appearance, Reason) likewise isolates **Date** ([BCU LibGuide](https://libguides.bcu.ac.uk/critical-evaluation/checklist-approach)). **Framing:** decades of source-literacy practice already separate "how current" from "how authoritative" — direct precedent for keeping recency a *separate axis* from reliability.

### 2.8 GRADE — *and a genuine gap*
GRADE rates certainty (Very Low→High) via five downgrade domains — risk of bias, inconsistency, **indirectness**, imprecision, publication bias — plus three upgrade factors ([GRADEpro: Indirectness](https://book.gradepro.org/guideline/indirectness); [CDC ACIP GRADE Handbook ch.8](https://www.cdc.gov/acip-grade-handbook/hcp/chapter-8-domains-decreasing-certainty-in-the-evidence/index.html)). **Notable disagreement / gap:** GRADE has **no formal "currency" downgrade domain**; age of evidence is handled only *indirectly* (temporal indirectness) or via the separate *decision to update a review* — not as a first-class certainty domain (my reading of the domain list; consistent with the search result noting currency "doesn't appear to be formally recognized as a separate downgrade domain"). Evidence-based medicine's actual answer to currency is organizational, not per-claim: **living systematic reviews** (§3.1).

### 2.9 Supersession (standards & law) — *the discrete override rule*
Standards bodies formalize lifecycle states: a **superseded** document "has been replaced by a more recent document"; a **withdrawn** one "is no longer relevant." Notably, "both superseded and withdrawn standards **remain available** ... and can still be used if organizations choose to do so" ([Standards NZ](https://www.standards.govt.nz/news-and-updates/current-cited-superseded-or-withdrawn-which-standard-should-you-use); [BSI](https://knowledge.bsigroup.com/articles/standards-terminology-when-is-a-standard-no-longer-a-standard); [FASB superseded standards](https://fasb.org/archive/superseded-standards)). **Framing:** supersession is a *discrete, authority-gated* override — a newer, sufficiently-authoritative document retires an older one — but the old text is preserved as history, not deleted. This is the model for a supersession rung that keeps the old claim in the ledger as `SUPERSEDED`.

### 2.10 Recency vs. authority in ranking; temporal knowledge graphs — *the weighting & data-model levers*
Web ranking has an explicit recency lever: **Query Deserves Freshness (QDF)** (Amit Singhal, Google, 2007) temporarily promotes new content "above older, more authoritative content" when news/blog/search volume spikes; Google's Nov-2011 "Freshness Update" reportedly touched ~35% of searches ([Search Engine Land QDF guide](https://searchengineland.com/guide/query-deserves-freshness-qdf); [SISTRIX](https://www.sistrix.com/ask-sistrix/google-updates-and-algorithm-changes/google-freshness-update/what-does-query-deserves-freshness-qdf-mean)) (the 35% figure is Google's, relayed by SEO secondary sources — **treat as approximate**). **Temporal knowledge graphs** (TKGs) attach valid-time to every fact — quadruples `(head, relation, tail, timestamp)` — modeling "when it became true, when it stopped being true, and where it came from," with bi-temporal tracking of valid time vs. ingestion/provenance time ([TKG survey, arXiv:2403.04782](https://arxiv.org/html/2403.04782v1); ["When Facts Expire," CIKM 2025, 10.1145/3746252.3761648](https://dl.acm.org/doi/10.1145/3746252.3761648)). **Framing:** QDF = *situational* recency weighting; TKG = the *data model* that makes valid-time a queryable property of each claim.

---

## 3. How mature fields already handle it

### 3.1 Living systematic reviews / continuous evidence surveillance (evidence-based medicine)
The field's answer to currency is **process, not a per-claim knob**. A **Living Systematic Review (LSR)** is "continually updated, incorporating new relevant evidence as it becomes available," underpinned by "continual evidence surveillance," often with **monthly** searches and predefined rules for how often evidence is sought and integrated ([Cochrane LSR news](https://ec.cochrane.org/news/living-systematic-reviews-lsrs-new-approach-conducting-systematic-reviews-using-cochrane); [Cochrane LSR guidance PDF, 2019](https://resources.cochrane.org/sites/resources.cochrane.org/files/uploads/inline-files/Transform/201912_LSR_Revised_Guidance.pdf); [scoping review, PMC10722674](https://pmc.ncbi.nlm.nih.gov/articles/PMC10722674/)). **Transfer to us:** the synthesizer's ledger is already append-only and resumable; an LSR-style "surveillance" pass (re-run search for a claim, compare, supersede) is the natural continuous-mode extension.

### 3.2 Bitemporal / "as-of" dating (databases)
Snodgrass's model (in SQL:2011) separates **valid time** ("when a fact was true in the reality modeled") from **transaction time** ("when a fact was stored") ([Fowler, *Bitemporal history*](https://martinfowler.com/articles/bitemporal-history.html); [Jensen & Snodgrass, TSQL2 ch.12](https://people.cs.aau.dk/~csj/Thesis/pdf/chapter12.pdf)). Fowler reframes these as **actual time** ("what history should be") and **record time** ("how our knowledge of history changes"), and shows **as-of** queries: `salaryAt('2021-02-25','2021-03-25')` = "salary on Feb 25 *according to our knowledge on Mar 25*." **Transfer to us:** every claim should carry two dates — the claim's **valid-as-of** date and the **observed/ingested** date — and the rendered source-of-truth should be answerable "as of" a date. (Note the terminology coincidence with the skill's `--mode actual`: Fowler's "actual time" is *valid time*, which is **not** the same as the skill's `actual` mode meaning; do not conflate them.)

### 3.3 Time-decay / recency weighting (forecasting, ranking, recommenders)
Exponential smoothing weights observations so "more weight [is] given to recent data," with **half-life = ln(2)/λ** — "the number of lags at which the weight falls to half" ([R-bloggers exponential decay](https://www.r-bloggers.com/2012/05/exponential-decay-models/); [half-life decaying recommender, CEUR-2038](https://ceur-ws.org/Vol-2038/paper1.pdf)). Hacker News ranks by `Score = (P−1)/(T+2)^G` with gravity `G≈1.8`: votes raised to a power <1, time to a power >1, so **time dominates** and old items decay even with many votes ([righto.com, 2009](http://www.righto.com/2009/06/how-does-newsyc-ranking-work.html)). **Transfer to us:** a decay factor on the *corroboration count* of volatile claims is the direct analog — but decay is tuned to a *domain half-life*, and (unlike a feed) truth is not monotone in recency, so decay must **cap** not **invert**.

### 3.4 Freshness/currency gates (search & source-literacy)
QDF (§2.10) is a *conditional* gate: freshness is boosted **only when the query is time-sensitive**, otherwise authority wins ([Search Engine Land](https://searchengineland.com/guide/query-deserves-freshness-qdf)). CRAAP/RADAR gate at the human-judgment level via a Currency/Date criterion (§2.7). **Transfer to us:** freshness should be *conditional on volatility*, never global.

### 3.5 Domain-specific fact volatility (LLM QA)
FreshQA's **never/slow/fast** partition (§2.6) is the field operationalizing "fact volatility" directly, and its remedy (**FreshPrompt** / retrieval augmentation) is: *for volatile questions, fetch a fresh source at answer time* ([arXiv:2310.03214](https://arxiv.org/abs/2310.03214)). A patent line ("Applying level of permanence to statements to influence confidence ranking," US 10,331,673 / US 10,360,219) proposes scoring answers "utilizing associated permanence metadata" and "tracking how permanence data for a particular term evolves over time" — i.e., a per-statement volatility classifier feeding confidence ([USPTO 10331673](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10331673)). **(Only the abstract framing was read; specific claim scope is UNVERIFIED.)** **Transfer to us:** volatility can be a *learned/annotated property of the claim*, not just the domain.

**Cross-field synthesis:** every mature field separates *currency* from *authority* and makes freshness *conditional on volatility* — none does "newest always wins." The common architecture is: **(model valid-time per fact) → (classify volatility) → (apply recency only where volatility warrants) → (supersede via an authority gate, preserving history) → (keep surveilling).**

---

## 4. Volatility classification — signals and method

The core design lever is a per-claim classifier of **how fast the claim's truth decays**. Best practice fuses three signal layers.

### 4.1 Domain / topic priors (coarse, high-recall)
Assign a base half-life by subject, echoing Arbesman (§2.3) and FreshQA (§2.6):

| Volatility class | Illustrative half-life | Example claims |
|---|---|---|
| **Durable / never-changing** | effectively ∞ | mathematical facts, historical events, physical constants, closed-form definitions |
| **Slow-changing** | years | demographics, org structures, mature-API behavior, established clinical guidance |
| **Fast-changing** | weeks–months | SOTA benchmarks, model/library versions, "current best," active-research frontier |
| **Volatile / ephemeral** | hours–days | prices, rates, CVE/exploit status, "as of today," live standings |

Half-lives are **UNVERIFIED / calibration targets** — the *structure* (domain-keyed decay) is well-supported; the *numbers* must be tuned empirically (see Open Questions).

### 4.2 Lexical / surface signals in the claim text (fine, high-precision)
Signals that a specific claim is volatile even inside a durable domain:
- **Recency deixis:** "current," "currently," "latest," "now," "today," "as of," "recently," "upcoming."
- **Superlatives / SOTA language:** "fastest," "best," "state-of-the-art," "leading," "record," "first to," "only."
- **Version / release tokens:** semantic versions (`v3.2`, `4.7`), release names, "new in," "deprecated," "since."
- **Dated benchmarks / metrics:** leaderboard scores, "achieves X on Y," percentages tied to an evaluation date.
- **Prices / rates / quantities-in-flux:** currency amounts, interest/exchange rates, counts that change ("N users").
- **Frontier markers:** "preprint," "just released," "emerging," "in beta," named after a moving target.
These map cleanly onto FreshQA's fast/false-premise categories and the temporal-validity literature's emphasis on time-scoping the claim (§2.5).

### 4.3 Evidence-temporal signals (from the corroboration set itself)
- **Age of newest independent source** relative to the domain half-life (stale if newest support > k·half-life old).
- **Dispersion of source dates:** all support clustered in an old window ⇒ likely superseded; a fresh outlier ⇒ candidate supersession.
- **Provenance freshness after de-circularization:** if the *only* recent "sources" collapse to one origin, treat as citogenesis, not freshness (§2.1).

### 4.4 Method (recommended)
A **hybrid classifier**: (1) cheap deterministic lexical/domain pass yields a prior + a `volatile?` flag with a confidence; (2) the blind judge already producing semantic answers also emits a `volatility ∈ {durable, slow, fast, volatile}` label and an `as_of` date estimate; (3) the two are reconciled — **disagreement widens uncertainty rather than forcing a class**. Keep the classifier **advisory**: it should only ever *cap* or *flag*, never *nullify*, a claim (asymmetric error handling — misclassifying a durable fact as volatile must not delete it).

### 4.5 How volatility should change the confidence rule
- **Durable claims:** unchanged — accumulated corroboration is legitimately strong; age is not a defect.
- **Volatile claims:** (a) age of newest support becomes a **downgrade** input; (b) the top tier requires **recent** independent corroboration, not merely *much* corroboration; (c) a corroborated newer higher/equal-tier source can **supersede**; (d) staleness is **surfaced** to the reader regardless.

---

## 5. Ranked, implementable mechanisms — tradeoffs & failure modes

Ranked by (impact × safety × fit to the existing engine). The cross-cutting principle **(h) recency as a separate axis** governs all of them and is treated first, not ranked.

**(h) — cross-cutting principle: keep recency SEPARATE from reliability (don't blend).**
Precedent: CRAAP/RADAR separate Currency/Date from Authority (§2.7); the engine already keeps Axis A (source reliability) and Axis B (claim certainty) separate. **Do:** add recency as a claim-level attribute (`as_of` date + `volatility` + `freshness_ok`), feeding Axis B and the checklist — **never** modify Axis A. **Failure mode if violated:** blending makes an old authoritative source look unreliable (wrong) or a fresh weak source look authoritative (dangerous). Cost: near-zero; it's an organizing decision.

**Rank 1 — (a) Volatility classification of each claim.** *Foundational; everything else keys off it.*
- **Tradeoff:** adds a classification step and a small config table of domain half-lives.
- **Failure modes:** false-volatile (durable fact flagged volatile → needless downgrade) and false-durable (volatile fact missed → stays stale). Mitigate with asymmetric handling (§4.4: cap/flag, never nullify) and by requiring *high* classifier confidence before the freshness gate bites.

**Rank 2 — (g) "As-of" stamping + surfacing staleness to the reader.** *Cheapest high-value move; pure transparency, zero truth-risk.*
- Attach `valid_as_of` and `observed_at` to every claim (bitemporal, §3.2); render a visible "⚠ possibly stale as of <date>" banner on volatile claims whose newest support is old. Directly answers the citogenesis complaint about missing "as of" timestamps (§2.1).
- **Tradeoff:** need reliable dates per source (often hard on the open web).
- **Failure mode:** none that harms correctness — worst case is an over-cautious banner. **This should ship first.**

**Rank 3 — (e) Freshness gate that CAPS the tier of stale volatile claims.** *Safe strong lever; already half-built.*
- If `volatile ∧ newest_independent_support older than domain window` ⇒ cap confidence at `probable` (or `unverified`), mirroring the existing single-source cap. This is the `freshness_ok=False` / `N5-NOT-STALE` path.
- **Tradeoff:** needs a per-domain freshness window (a coarser cousin of the half-life).
- **Failure mode:** a still-true durable fact mislabeled volatile gets under-graded — bounded because it only *caps*, never flips the answer, and the reader sees the reason.

**Rank 4 — (f) Require ≥1 RECENT independent source before a volatile claim reaches the top tier.** *Anti-stale AND anti-single-fresh in one rule.*
- Extend the existing "≥2 independent cross-family sources for `verified`" floor with: *for volatile claims, at least one of those independent sources must be within the domain freshness window.*
- **Tradeoff:** volatile claims will more often land at `probable` when no fresh corroboration exists — which is correct behavior (honest abstention over stale confidence).
- **Failure mode:** if "recent" is set too loose it under-protects; too tight and legitimately-stable facts get penalized. This rule is strong precisely because it **cannot** be satisfied by a lone fresh source (still needs ≥2 independent). **High recommend.**

**Rank 5 — (c) Supersession: a newer, equal-or-higher-tier, corroborated source overrides an older well-corroborated claim (volatile domains only).** *The direct fix to "old out-scores new"; maps to the ladder.*
- Model on standards supersession (§2.9): the newer claim wins the conflict and the older is retained as `SUPERSEDED` (not deleted). **Guarded:** fires only if the superseding claim is (i) volatility-relevant, (ii) **equal-or-higher reliability tier**, and (iii) **itself independently corroborated (≥2 families)** *or* an authoritative/primary source. Otherwise the newer source only **downgrades** the old claim to *contested*, it is **not** promoted to winner.
- **Tradeoff / failure mode:** the whole danger of "newest wins" lives here — an *ungated* supersession lets a single fresh wrong source retire a correct old one. The three-part gate is what prevents that. Also risks thrash/oscillation between an old and new claim — reuse the existing oscillation guard.

**Rank 6 — (b) Time-decay applied to the corroboration COUNT for volatile claims.** *Refinement; useful but parameter-hungry.*
- Multiply each corroborating source's weight by `exp(−λ·age)` with `λ = ln(2)/half_life` (§3.3), so a volatile claim's *effective* corroboration reflects **fresh** agreement, blunting the old-claim accumulation advantage.
- **Tradeoff:** requires a defensible per-domain half-life; wrong half-lives silently mis-grade.
- **Failure modes:** (i) decay must **cap** the tier, never **invert** the winner (truth isn't monotone in recency); (ii) applying decay to a durable claim is a bug; (iii) decay + supersession can double-count age — apply decay to *grading*, supersession to *conflict resolution*, not both to the same decision. Lower rank because (e)+(f) capture most of the benefit with fewer magic numbers.

**Rank 7 — (d) Per-run "recency-priority mode" flag.** *Situational; must be strictly guarded.*
- A `--recency` (or `--mode current`) switch that: shortens freshness windows, shrinks decay half-lives, raises the supersession rung's priority, and turns the freshness gate from advisory to hard-capping — for questions the user knows are time-sensitive (the QDF idea made explicit, §2.10).
- **Hard constraint:** recency mode must **NOT** lower the ≥2-independent-cross-family floor or bypass de-circularization. It changes *how aggressively* recency reweights, never *whether a single source can be "verified."*
- **Failure mode if unconstrained:** exactly the single-fresh-source and fresh-cascade problems (§2.1–2.2). Keep it a *reweighting* knob, not a *floor-lowering* knob.

---

## 6. Recommendation for `acos-axiom-synthesis`

The engine already has the right skeleton: two separated axes, a single-source cap, a de-circularization firewall, an append-only ledger with supersession history, a `freshness_ok`/`N5-NOT-STALE` gate, a `stale` nullification reason, a `recency_correction` ladder rung, and per-run modes. The recommendation is to **wire these latent hooks into a coherent, volatility-conditional recency discipline** — adopting mechanisms **(h)+(a)+(g)+(e)+(f)+(c)** as the core, **(b)** as a tunable refinement, and **(d)** as a guarded mode.

### 6.1 Adopt (in order)
1. **(h) Recency as a separate attribute (not a reliability change).** Add `as_of` (valid-time), `observed_at` (ingest-time), and `volatility ∈ {durable, slow, fast, volatile}` to the claim schema. Feed volatility + freshness into Axis B and the checklist; leave Axis A untouched.
2. **(a) Volatility classifier** (§4): deterministic lexical/domain prior + blind-judge label, reconciled, advisory (cap/flag only).
3. **(g) As-of stamping + staleness banner** in `render.py` — ship first; pure transparency.
4. **(e) Freshness gate** — make `freshness_ok` *computed*: `freshness_ok = (not volatile) OR (∃ independent source with observed_at within domain_window)`. A `False` caps the tier (already the `N5-NOT-STALE` veto semantics).
5. **(f) Recent-corroboration requirement for the top tier** on volatile claims — extend the `verified` gate in `grade_claim`.
6. **(c) Guarded supersession** — promote/insert a supersession step in `resolve.py` for volatile claims, gated as in Rank 5, retaining the old claim as `SUPERSEDED`.

### 6.2 Exact mapping onto existing hooks

- **`config/checklist.yaml` → `N5-NOT-STALE` (`expr: not superseded and grading.freshness_ok`).** Keep the expression; change what feeds it. `superseded` is now set by the guarded supersession step; `freshness_ok` is now the computed volatility-conditional predicate above. N5 stays a **veto** for volatile claims and is auto-`True` for durable claims (age is not a defect) — so durable well-corroborated claims are *never* penalized, which is the whole point of not over-correcting.

- **`scripts/grade_fuse.py` → `grade_claim(...)` `downgrades`/`stale` + top-tier gate.**
  - Emit a **`("stale", severity)`** downgrade when `volatile ∧ newest_independent_support > k·half_life` (severity 1 for slow-changing, 2 for fast/volatile). This is the "grade_claim stale downgrade" already anticipated by `falsify.py`'s `stale` reason.
  - Amend the `verified` condition: currently `independent_sources ≥ 2 ∧ distinct_families ≥ 2 ∧ axis_b ∈ {High, Moderate}`. Add: *if `volatile`, also require ≥1 of those independent sources within `domain_window`* — mechanism (f). If unmet, fall to `probable` with reason `"volatile-claim: no recent independent corroboration → capped"`.
  - **Preserve** the single-source cap and cross-family floor unchanged — recency never lowers them.

- **`scripts/resolve.py` → the `recency_correction` rung (currently rung 8, boolean, below reliability/authority/independent_sources).** Two changes:
  - Make the ladder **volatility-aware.** For **durable** conflicts, keep the current order (old accumulated evidence legitimately wins). For **volatile** conflicts, insert a **guarded `supersession` rung ABOVE `independent_sources`** so a *corroborated, equal-or-higher-tier, newer* claim beats an older claim that merely has *more accumulated* corroboration — directly countering the structural old-information advantage. Keep it **below** `directness`, `originality`, and `reliability`, so a lone fresh low-tier source can never win.
  - The rung must read a real supersession predicate (newer `as_of` **and** tier ≥ incumbent **and** independently corroborated), not just a boolean flag; if the predicate fails, fall through to the existing ladder (no fabricated winner; `UNRESOLVED` preserved).

- **`--mode actual|synthesis` → add recency behavior, plus an optional `--recency` overlay.**
  - In **`actual` mode** (facts expected to converge), staleness of a *volatile* claim is strong evidence of a problem → freshness gate is **hard** (cap + prominent banner), supersession enabled.
  - In **`synthesis` mode** (optimally combining projections/opinions), recency is a **weight/decay** input, not a hard gate — a stale view is *discounted*, not *nullified*.
  - **`--recency` (new overlay, mechanism d):** shortens `domain_window`, shrinks half-lives, and raises the supersession rung — **without** touching the ≥2-independent-cross-family floor or de-circularization. Document it as a *reweighting* knob only.

### 6.3 What a "recency mode" adds (net-new)
A per-run switch that makes the engine behave like QDF-on: (1) tighter freshness windows / shorter half-lives; (2) supersession rung elevated; (3) freshness gate promoted from advisory to hard-capping; (4) staleness banners forced on. It **adds no new trust** — it only changes *how aggressively existing, already-safe recency levers apply*. The floors it must never relax: the corroboration/independence gate and the citogenesis firewall.

### 6.4 Guardrails that keep this from becoming "newest wins" (research question 5)
1. **De-circularization runs first, always.** A burst of fresh sources that collapse to one origin is citogenesis, not corroboration (§2.1–2.2). Recency *amplifies* cascade risk because fresh cascades propagate fast — so the firewall is *more* important in recency mode, not less.
2. **Recency never lowers the independence floor.** `verified` still needs ≥2 independent cross-family sources. A single fresh source maxes out at `probable`, exactly like a single old source.
3. **Supersession is authority-gated + corroboration-gated.** A newer source can *demote* an old claim to *contested* on its own, but can only *win* if it is equal-or-higher tier **and** independently corroborated. This blocks the single-fresh-wrong-source failure.
4. **Volatility classifier is advisory and asymmetric.** It may cap or flag, never nullify; durable facts are exempt from the freshness gate so genuine evidence is never defeated by mere age.
5. **Decay caps, never inverts.** Time-decay reduces a stale volatile claim's tier; it does not by itself select a winner (that's supersession's job, with its stronger gate).
6. **Preserve, don't delete.** Superseded claims stay in the ledger as history (standards-model, §2.9), so an over-eager supersession is auditable and reversible — and the oscillation guard prevents thrash.
7. **Abstain over both failure modes.** When neither a fresh nor a stale claim clears its gate, emit `UNRESOLVED` with the staleness surfaced — the engine's existing refusal discipline is the ultimate guardrail.

---

## 7. Open questions

1. **Per-domain half-lives / freshness windows — where do the numbers come from?** The *structure* (domain-keyed decay) is well-supported; the *values* are not. Needs an empirical calibration table (math=∞; mature APIs=years; SOTA/versions=months; prices/CVEs=days) and a policy for unknown domains (default conservative = treat as slow-changing, flag). **UNVERIFIED numbers.**
2. **Reliable dating of sources.** As-of stamping and decay both need trustworthy `observed_at`/`valid_as_of` dates, but many web sources lack them — the very citogenesis complaint (§2.1). What is the fallback when a source has no reliable date (treat as unknown-age → cannot satisfy the "recent" requirement)?
3. **Volatility-classifier error costs.** False-volatile vs. false-durable have asymmetric costs; what confidence threshold should gate the freshness cap, and should the two error types have different thresholds?
4. **Interaction of decay with de-circularization.** After collapsing a fresh cascade to one vote, does the remaining single fresh source still count toward the "recent corroboration" requirement (it should **not**, alone)?
5. **Recency as a third rendered axis?** Should the output surface a distinct `currency` grade (like CRAAP's Currency) beside reliability and certainty, or keep recency folded into `freshness_ok` + banners? (Leaning: fold in, but expose `as_of` prominently.)
6. **Continuous "living" mode.** Should the skill offer an LSR-style surveillance loop (§3.1) that periodically re-searches volatile claims and auto-proposes supersession, given the ledger is already append-only and resumable? Scope/cost unknown.
7. **GRADE-currency gap.** Since GRADE itself lacks a currency domain (§2.8), is there defensible published methodology for a per-claim currency downgrade, or is the honest position that we are formalizing something the source frameworks handle only organizationally (LSRs) — and should that be disclosed in the output's methodology note? **Genuine open gap.**

---

## Sources (primary preferred; access date 2026-08-02)

**Citogenesis / cascades**
- Circular reporting — Wikipedia. https://en.wikipedia.org/wiki/Circular_reporting
- xkcd #978 "Citogenesis" (Munroe, 2011) — explain xkcd. https://www.explainxkcd.com/wiki/index.php/978:_Citogenesis
- "Citogenesis: the serious circular reporting problem," Slate, 2019-03. https://slate.com/technology/2019/03/wikipedia-citogenesis-circular-reporting-problem.html
- Bikhchandani, Hirshleifer & Welch — *Information Cascades and Social Learning* (survey PDF). https://www.tamuz.caltech.edu/papers/cascades_survey.pdf ; Palgrave entry PDF. https://bpb-us-e2.wpmucdn.com/sites.uci.edu/dist/c/362/files/2017/01/Palgrave-information-cascades-Online-version.pdf

**Half-life of facts / drift**
- Arbesman, *The Half-Life of Facts* (2012) — fs.blog summary. https://fs.blog/the-half-life-of-facts/ ; SciTechDaily. https://scitechdaily.com/samuel-arbesman-explains-the-half-life-of-facts/
- Lu et al., *Learning under Concept Drift: A Review*, arXiv:2004.05785. https://arxiv.org/pdf/2004.05785 ; Frontiers in AI 2024 concept-drift survey. https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2024.1330257/full ; Dataversity data-vs-concept drift. https://www.dataversity.net/articles/data-drift-vs-concept-drift-what-is-the-difference/

**Temporal IR / KG / LLM temporal alignment**
- Kanhabua, Blanco & Nørvåg, *Temporal Information Retrieval* (2015). https://www.dc.fi.udc.es/~roi/publications/fntir-temporalweb_ebook.2015.pdf ; ACM Computing Surveys 2014 (10.1145/2619088). https://dl.acm.org/doi/10.1145/2619088
- TKG survey, arXiv:2403.04782. https://arxiv.org/html/2403.04782v1 ; "When Facts Expire," CIKM 2025 (10.1145/3746252.3761648). https://dl.acm.org/doi/10.1145/3746252.3761648
- Vu et al., *FreshLLMs / FreshQA*, arXiv:2310.03214 (Oct 2023; ACL Findings 2024). https://arxiv.org/abs/2310.03214
- *Set the Clock: Temporal Alignment of Pretrained LMs*, arXiv:2402.16797. https://arxiv.org/pdf/2402.16797 ; TemporalWiki, arXiv:2204.14211. https://arxiv.org/pdf/2204.14211 ; temporal-reasoning benchmark context, arXiv:2306.08952. https://arxiv.org/html/2306.08952

**Source-evaluation / evidence**
- CRAAP test — Wikipedia. https://en.wikipedia.org/wiki/CRAAP_test ; BCU checklist (CRAAP + RADAR). https://libguides.bcu.ac.uk/critical-evaluation/checklist-approach
- GRADE Indirectness — GRADEpro. https://book.gradepro.org/guideline/indirectness ; CDC ACIP GRADE Handbook ch.8. https://www.cdc.gov/acip-grade-handbook/hcp/chapter-8-domains-decreasing-certainty-in-the-evidence/index.html
- Cochrane Living Systematic Reviews — news. https://ec.cochrane.org/news/living-systematic-reviews-lsrs-new-approach-conducting-systematic-reviews-using-cochrane ; LSR guidance PDF (2019). https://resources.cochrane.org/sites/resources.cochrane.org/files/uploads/inline-files/Transform/201912_LSR_Revised_Guidance.pdf ; scoping review, PMC10722674. https://pmc.ncbi.nlm.nih.gov/articles/PMC10722674/

**Temporal data model / ranking / supersession**
- Fowler, *Bitemporal History* (valid/actual vs transaction/record time; as-of queries). https://martinfowler.com/articles/bitemporal-history.html ; Jensen & Snodgrass, TSQL2 ch.12. https://people.cs.aau.dk/~csj/Thesis/pdf/chapter12.pdf
- Exponential decay / half-life = ln(2)/λ — R-bloggers. https://www.r-bloggers.com/2012/05/exponential-decay-models/ ; half-life decaying recommender, CEUR-2038. https://ceur-ws.org/Vol-2038/paper1.pdf
- Hacker News ranking formula — righto.com (2009). http://www.righto.com/2009/06/how-does-newsyc-ranking-work.html
- Query Deserves Freshness (Singhal 2007; Google 2011 freshness update) — Search Engine Land. https://searchengineland.com/guide/query-deserves-freshness-qdf ; SISTRIX. https://www.sistrix.com/ask-sistrix/google-updates-and-algorithm-changes/google-freshness-update/what-does-query-deserves-freshness-qdf-mean
- Superseded vs withdrawn standards — Standards NZ. https://www.standards.govt.nz/news-and-updates/current-cited-superseded-or-withdrawn-which-standard-should-you-use ; BSI. https://knowledge.bsigroup.com/articles/standards-terminology-when-is-a-standard-no-longer-a-standard ; FASB superseded standards. https://fasb.org/archive/superseded-standards
- "Applying level of permanence to statements to influence confidence ranking," USPTO 10,331,673 (abstract framing only; claim scope **UNVERIFIED**). https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10331673

**UNVERIFIED flags:** Arbesman's ~45-year hepatology half-life (secondary reporting of an underlying study I did not read); Google's "~35% of searches" freshness figure (Google's number relayed via SEO secondary sources); the "level of permanence" patents' specific claims (abstract only); all per-domain half-life *values* in §4.1 (structure supported, numbers require empirical calibration).
