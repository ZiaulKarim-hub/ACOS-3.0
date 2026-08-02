# Deep Research Report: Architecture for /acos-research-riffs

**Date:** 2026-07-21
**Evidence Quality:** Standard (2+ sources for key claims; single-source claims labeled)
**Research question:** What is the best architecture for `/acos-research-riffs` — an upfront multi-agent deep-research phase that pre-briefs a dynamically generated panel of perspective agents (dossiers), followed by a live Q&A conversation that answers from those dossiers and dispatches on-demand research agents for unexpected/deeper questions, with a decision ledger and a compiled formal report — and what prior art, patterns, and pitfalls exist?

---

## Executive Summary

The proposed architecture is not speculative — every component has validated prior art, and the closest system (Stanford/Yale **Co-STORM**, EMNLP 2024) implements almost exactly the "agents pre-research, user converses, report compiles" loop, with human-eval preference rates of 70% over Google Search and 78% over a RAG chatbot. The design task is therefore assembly, not invention: combine Co-STORM's discourse machinery (mind-map ledger, mixed-initiative turns, moderator seat), STORM's panel-generation recipe, the CRAG corpus-first routing pattern, Anthropic's delegation-contract and effort-scaling rules, and LangChain's compression-boundary + one-shot-report discipline — on top of ACOS's existing substrate (swarm isolation, IC research-bot contract, render-from-ledger discipline, resume-from-disk).

The failure literature directly explains the previous "sloppy" research session. The MAST taxonomy (UC Berkeley, 1,600+ traces) attributes 41.77% of multi-agent failures to specification issues and 21.30% to verification/termination issues — the prior session's coverage gap (missed tools) and missing decision tracking are textbook instances of these two dominant classes. The countermeasures are structural: a frozen research brief with a coverage checklist, self-contained agent charters, an independent coverage gate before Q&A opens, per-dimension saturation-based stop rules, and an append-only supersession ledger.

Cost reality: multi-agent research runs at roughly 15x chat-level token usage (Anthropic, vendor-reported), which is precisely why the dossier-first shape is right — research once in the background, answer many times cheaply from disk, and dispatch fresh agents only on retrieval miss. The main open risks are echo-chamber panels (mitigated by a mandatory generalist + skeptic seat), false saturation (mitigated by per-dimension coverage accounting), and ledger drift (Co-STORM's mind map tracked its own discourse correctly only 71% of the time — a correction affordance is mandatory).

---

## Key Findings

### Finding 1: The previous session's failures match the two dominant documented failure classes
- **Confidence Level:** Verified
- **Data:** MAST ("Why Do Multi-Agent LLM Systems Fail?", arXiv:2503.13657, UC Berkeley): Specification/System Design failures 41.77%, Inter-Agent Misalignment 36.94%, Task Verification & Termination 21.30% (1,600+ annotated traces, 7 frameworks, annotation kappa = 0.88). Notable single modes: step repetition 15.7%, reasoning-action mismatch 13.2%, unaware-of-termination 12.4%, disobey task spec 11.8%, incorrect verification 9.10%, no/incomplete verification 8.20%.
- **Sources:** (1) arXiv:2503.13657 + v3 HTML [Tier 1, acc. 2026-07-21]; (2) FutureAGI commentary incl. PwC/CrewAI 7x accuracy case (10% → 70% after adding independent judge-agent validation loops) [Tier 2/3, acc. 2026-07-21].
- **Analysis:** The coverage gap ("missed several great tools") is a specification failure — the research scope never enumerated what full coverage meant, so nothing could detect the gap. The absent decision trail is a verification failure. ~63% of observed multi-agent failures (FC1 + FC3) live exactly where the new skill's guardrails must go. MAST's own targeted fixes bought only +9.4% and +15.6% — structure must be right from the start, not patched.

### Finding 2: Multi-agent research pays off only on parallelizable breadth, at ~15x token cost
- **Confidence Level:** Verified (with boundary conditions; headline number is vendor-reported)
- **Data:** Anthropic: multi-agent (Opus 4 lead + Sonnet 4 subagents) outperformed single-agent Opus 4 by 90.2% on an internal research eval; agents ≈ 4x chat tokens, multi-agent ≈ 15x; token usage alone explains 80% of performance variance; parallel tool calls cut research time by up to 90%. Counter-evidence: at equal thinking-token budgets, single-agent beats multi-agent on multi-hop reasoning (arXiv:2604.02460); Cognition's position piece argues context fragmentation compounds errors (p^N: ten 95%-reliable steps ≈ 60% end-to-end).
- **Sources:** (1) anthropic.com/engineering/built-multi-agent-research-system [Tier 1 for architecture, vendor-reported for benchmarks, acc. 2026-07-21]; (2) arXiv:2604.02460 [Tier 3]; (3) cognition.com/blog/dont-build-multi-agents [Tier 2].
- **Analysis:** Not a contradiction — a boundary condition. Fan out only for independent breadth (the upfront dossier phase); never chain-serialize dependent reasoning; keep the live Q&A a single fast loop. The 15x figure is the economic argument for dossier-first: research once, answer many.

### Finding 3: The delegation contract is the single load-bearing prompt element
- **Confidence Level:** Verified
- **Data:** Anthropic: every subagent needs "an objective, an output format, guidance on the tools and sources to use, and clear task boundaries," plus effort-scaling rules (simple fact-find = 1 agent / 3–10 tool calls; comparisons = 2–4 agents / 10–15 calls; complex = 10+ agents). GPT Researcher independently converges: a planner materializes an explicit research-question set before any searching; 20+ sources per run as an objectivity quota.
- **Sources:** (1) Anthropic engineering blog [Tier 1, acc. 2026-07-21]; (2) github.com/assafelovic/gpt-researcher README [Tier 1/3, acc. 2026-07-21]; corroborated by MAST FC1 frequencies [Tier 1].
- **Analysis:** Both the upfront panel dispatcher and the live-phase dispatcher should emit charters from a fixed template: objective, dossier schema, tool/source guidance, boundaries, effort tier, stop rule. This attacks the largest failure class (specification) at its root.

### Finding 4: The live Q&A loop has a named, validated shape — corpus-first with fallback (CRAG), categorical confidence, abstention as a first-class answer
- **Confidence Level:** Verified
- **Data:** CRAG (arXiv:2401.15884): a retrieval evaluator scores retrieved evidence; below-threshold confidence triggers reformulation or fresh retrieval. Adaptive-RAG: retrieval effort tiered by query complexity. Gemini Deep Research production-validates the pattern: follow-up Q&A runs RAG over everything gathered in-session ("smarter the longer you interact with it") on a 1M-token context. ACL Findings 2025: numeric RAG confidence scores are axiomatically unreliable — categorical labels tied to evidence state are safer. SURE-RAG and Microsoft's Confidence-Aware RAG: verify evidence sufficiency; abstain when weak.
- **Sources:** (1) RAG survey arXiv:2506.00054 (CRAG/Adaptive-RAG/Self-RAG mechanics) [Tier 1, acc. 2026-07-21]; (2) gemini.google/overview/deep-research/ [Tier 1]; (3) aclanthology.org/2025.findings-acl.852 [Tier 1]; (4) SURE-RAG arXiv:2605.03534, Microsoft Confidence-Aware RAG [Tier 1/2].
- **Analysis:** Per user question: (1) attempt answer from dossiers; (2) sufficiency check; (3) label **verified** (multi-source) / **provisional** (single-source or inferred) / **not-in-corpus**; (4) not-in-corpus abstains AND auto-dispatches a fast research agent, and the new material writes back into the corpus with a timestamp. "Not in corpus" as an honest first-class answer is the direct guardrail against coverage gaps resurfacing as confident wrong answers. Freshness literature adds: timestamp every dossier claim at write time (embeddings are time-blind); answers carry an as-of date.

### Finding 5: Co-STORM is the closest prior art and contributes three evaluated mechanisms
- **Confidence Level:** Probable (single system, but Tier 1 peer-reviewed with human eval)
- **Data:** Co-STORM (arXiv:2408.15232, EMNLP 2024): (a) **dynamic mind map** — a concept tree where every finding is stored with the question that produced it; insert/reorganize operations (reorganize triggers at K=10 items per concept); the same tree becomes the final report outline; tracked its own discourse correctly 71% of the time. (b) **Mixed-initiative turn policy** — the user may interject any time and wins the turn; the interjection is used verbatim as a retrieval query and regenerates the expert roster; after L=2 consecutive answering turns a moderator is forced to intervene. (c) **Moderator seat** — mines information retrieved but never yet cited, reranked by cos(i,t)^α · (1−cos(i,q))^(1−α) with α=0.5 (topic-relevant but question-dissimilar), to ask "you didn't ask, but…" questions. Ablation: removing the moderator hurts more than removing experts; "one expert and one moderator can already provide most of the benefits." Human eval: 70% preferred vs Google Search, 78% vs RAG chatbot; Serendipity 3.90 vs 2.70 (p=0.009); 80% agreed it took less effort.
- **Sources:** (1) arXiv:2408.15232 PDF pp. 1–10 [Tier 1, acc. 2026-07-21]; (2) stanford-oval/storm repo (DiscourseManager) [Tier 1/3].
- **Analysis:** The moderator is the anti-"missed tools" mechanism at conversation time: dossier material the user never asked about gets proactively surfaced instead of dying on disk. The 71% mind-map accuracy mandates a user-visible correction affordance on the ledger. Known limitation: users with a clear target found the discursive mode verbose — the skill must degrade gracefully into direct Q&A.

### Finding 6: Panel generation has one published recipe (STORM); everything in-house is selection, not generation
- **Confidence Level:** Verified
- **Data:** STORM (arXiv:2402.14207): derive N=5 perspectives from the structure of adjacent/analogous topics, always adding a mandatory generalist "basic fact writer" (p0); each agent researches via a perspective-conditioned multi-turn (M=5) question → filtered-search → cited-answer loop; 84.83% of output sentences supported by citations under an entailment check. In-house survey: IC roster (roster.yaml), swarm-research (12-lens pool), swarm-review (17-lens table) all *select from fixed pools*; the sanctioned mechanism for dynamic panels is Task(general-purpose) with generated prompts (precedent: acos-software-swarm-review, acos-synthesis-protocol, document-synthesis, acos-grader), because `.claude/agents/` is restricted infrastructure (CLAUDE.md).
- **Sources:** (1) arXiv:2402.14207 [Tier 1, acc. 2026-07-21]; (2) internal survey of ACOS repo, paths cited in Cross-Reference section [Tier 1 internal, direct file evidence].
- **Analysis:** Generate the panel from the frozen research brief (not the raw request): enumerate adjacent domains/analogous problems, derive 3–5 non-overlapping perspective charters, and always seat (a) the generalist and (b) a skeptic/verifier. STORM's named failure modes — source-bias transfer and over-association of unrelated facts — justify the skeptic seat and a citation-entailment QA gate.

### Finding 7: The report must compile one-shot from ledger + dossiers; parallel section-writing is a documented anti-pattern
- **Confidence Level:** Verified
- **Data:** LangChain Open Deep Research: earlier versions had sub-agents write report sections in parallel — "the reports were disjoint"; the fix was multi-agent for research only, one-shot writing from brief + compressed findings. Anthropic: subagent outputs bypass the coordinator to external storage with lightweight references (anti-"game of telephone"), and a dedicated CitationAgent attributes claims at compile time. OpenAI's system card and launch materials concede citation mistakes persist even in the flagship product. In-house: IC's render_memo.py projects the memo deterministically from the ledger — nothing free-written.
- **Sources:** (1) langchain.com/blog/open-deep-research [Tier 1, acc. 2026-07-21]; (2) Anthropic engineering blog [Tier 1]; (3) OpenAI Deep Research system card, cdn.openai.com/deep-research-system-card.pdf [Tier 1]; (4) `.claude/skills/acos-investment-committee/scripts/render_memo.py` [Tier 1 internal].
- **Analysis:** Three independent traditions converge on the same discipline: files are the artery, the conversation is only the nervous system; compression at every boundary; one writer; separate citation verification.

### Finding 8: Stop rules — budget cap AND evidenced saturation, accounted per coverage dimension
- **Confidence Level:** Verified
- **Data:** Grounded-theory saturation (Glaser & Strauss 1967): stop when additional sampling yields nothing new; operationalized as K-consecutive-dry-probes with novelty resetting the counter. Tight 2024 (Qualitative Inquiry): saturation is routinely asserted without evidence — credible use requires documenting what stopped appearing. MAST: unaware-of-termination = 12.4% of failures, premature termination = 6.20% — both under- and over-stopping are measured failure modes. Anthropic: effort scaled per query complexity; token budget dominates performance.
- **Sources:** (1) saturation methodology literature (Simply Psychology summary of Glaser & Strauss; Tight 2024, journals.sagepub.com/doi/full/10.1177/10778004231183948) [Tier 1/2, acc. 2026-07-21]; (2) MAST arXiv:2503.13657 [Tier 1]; (3) Anthropic blog [Tier 1].
- **Analysis:** The prior session's coverage gap was *false global saturation* — it stopped before the "relevant tools" category was saturated because nothing measured coverage per dimension. Fix: the brief generates a coverage checklist; saturation is tracked per checklist dimension (a dimension with zero probes can never read as saturated); the stop decision itself is a ledger entry recording the last K dry probes. Suggested K = 2–3.

### Finding 9: The ledger form is solved — Nygard-minimal records, supersession semantics, ALCOA+ attribution
- **Confidence Level:** Verified
- **Data:** Nygard ADR (Cognitect, 2011): Status / Context / Decision / Consequences (all consequences, not just positive); reversals recorded by superseding entries with cross-links, never deletion; the minimal form is the one teams actually maintain. AI-lab audit-trail practice: automatic timestamps + agent AND model attribution + evidence link (attributing changes to "system" without model/input/approver fails the ALCOA+ attributability standard). In-house: IC's hash-chained append-only claims ledger and /acos-decide's ADRs in memory/decisions/ provide the local idiom.
- **Sources:** (1) cognitect.com/blog/2011/11/15/documenting-architecture-decisions [Tier 1, acc. 2026-07-21]; (2) adr.github.io/adr-templates [Tier 1]; (3) labmanager.com audit-trail requirements article [Tier 2]; (4) IC ledger machinery, `.claude/skills/acos-investment-committee/scripts/` [Tier 1 internal].
- **Analysis:** Ledger entry schema: id, timestamp, type (finding | decision | assumption | correction | stop-decision), status (active | superseded-by:N), context (1–3 sentences), body ("We found… / We will…"), consequences, provenance (source + access date), author (agent + model). Assumptions are entries too, so the report can separate verified findings from assumption-dependent ones.

### Finding 10: ACOS already provides the substrate; five components are genuinely new
- **Confidence Level:** Verified (internal, direct file evidence)
- **Data:** Reusable: ic-research-bot's private, cite-or-it-didn't-happen contract (`.claude/agents/ic-research-bot.md`); mechanical independence via single-message parallel dispatch (IC Mode A); isolation-by-information-hiding + optional enforcement hook (`~/.claude/skills/acos-swarm-research/`, `.acos/swarm/<session>/agent-NN/`); announce-panel-before-spawning UX (swarm-review); compute-don't-narrate ledger→render discipline (render_memo.py); resume-from-disk (IC scripts/resume.py); autopilot pre-flight guard (session_scaffold.py --autopilot-check — live Q&A requires a present human); model resolution via resolve-agent-model.sh (name-keyed — dynamic agents need a representative name or a pinned model); RAG infrastructure (`.claude/scripts/rag/`, LanceDB in `.acos/vectordb/`). Genuinely new: (1) true panel *generation*; (2) durable per-perspective dossiers consulted during later Q&A; (3) a decision/finding/reversal ledger for research; (4) answer-from-dossiers-else-dispatch behavior; (5) a ledger→formal-report compile step for research.
- **Sources:** Internal survey with per-claim file paths [Tier 1 internal, acc. 2026-07-21]; constraint: CLAUDE.md "Restricted Files" (`.claude/agents/` requires human approval).
- **Analysis:** Precedent (acos-synthesis-protocol's prompts/builder.md pattern) shows the clean implementation: the skill ships charter *templates* as prompt files; the dispatcher instantiates them per run onto general-purpose agents. Also relevant: the prior session's own handoff records the user preference "research done in conversational style, not a formal report" — the riffs design satisfies both sides by keeping the conversation conversational and compiling the formal artifact from the ledger at the end.

---

## Cross-Reference Analysis

### Source Conflicts

| Data Point | Source A | Source B | Assessment |
|------------|----------|----------|------------|
| Multi-agent vs single-agent | Anthropic: +90.2% multi-agent (breadth research) | arXiv:2604.02460: single-agent wins multi-hop at equal budgets; Cognition: "don't build multi-agents" | Boundary condition, not contradiction: fan out for independent breadth with scaled budget; single fast loop for dependent reasoning and live Q&A. |
| Anthropic blog source tier | Lanes 2/3 rated Tier 1 | Lane 1 rated Tier 2 (vendor commentary) | Tier 1 for its own architecture; benchmark numbers (90.2%, 15x, 80%) are vendor-reported and unreplicated — treat as directional. |
| Discursive vs direct answering | Co-STORM: discourse preferred (70%/78%) | Co-STORM's own user study: clear-target users found it verbose | Both true for different user states — the skill needs a discourse mode and a direct-QA mode, switchable per question. |
| Formal report vs conversational preference | User's recorded preference: "conversational style, NOT a formal report" (2026-07-21 handoff intent_core) | This project's premise: formal final report required | Resolved by the architecture itself: conversation stays conversational; the formal artifact is compiled from the ledger afterward, not delivered as the interaction style. |
| Panel size | STORM N=5 perspectives; Anthropic 3–5 parallel subagents | Co-STORM ablation: 1 expert + 1 moderator retains most benefit | Read as floor vs default: lite mode = 1+1 (+generalist); default = 3–5; scale by question complexity. |

### Data Quality Assessment
- **High Quality:** MAST failure frequencies (peer-reviewed, kappa 0.88); STORM/Co-STORM evaluations (peer-reviewed incl. IRB human study); OpenAI system card injection measurements; internal ACOS survey (direct file reads with paths).
- **Medium Quality:** Anthropic benchmark figures (primary source, vendor-reported); GPT Researcher cost figure (~$0.4/run, self-reported README); Perplexity claims (marketing-weighted, launch page 403'd, quotes recovered via relay).
- **Low Quality:** p^N reliability formalization (Tier 4 blog, used only as an illustration); PwC 7x case study (reported second-hand via Tier 2 commentary).

---

## Risk Assessment

| Risk | Likelihood | Impact | Severity | Mitigation |
|------|------------|--------|----------|------------|
| Echo-chamber panel (correlated perspectives miss what a boss's letter catches) | M (3) | H (5) | 15 Medium | Charter generator assigns non-overlapping lanes; mandatory generalist p0 + skeptic seat; blind single-message dispatch (IC pattern) |
| False saturation → coverage gap recurs | M (3) | H (5) | 15 Medium | Brief-derived coverage checklist; per-dimension saturation accounting; independent coverage gate before Q&A opens; moderator mines unused material |
| Ledger drifts from conversation (Co-STORM map: 71% accurate) | M (3) | M (3) | 9 Medium | Per-turn append; user-visible ledger status; explicit correction affordance; corrections are supersession entries |
| Token blowout (~15x chat) | H (4) | M (3) | 12 Medium | Dossier-first answering; effort-scaling tiers; per-agent budget caps; lite mode (1 expert + 1 moderator) |
| Stale dossiers answered as current | M (3) | M (3) | 9 Medium | Timestamps at write time; as-of date on answers; re-verify tags on volatile facts (pricing etc.) |
| Prompt injection via fetched pages into background agents | L (2) | H (5) | 10 Medium | Treat web content as untrusted data; agents report findings, never execute page instructions; provenance required for every claim |
| Disjoint final report | M (3) | M (3) | 9 Medium | One-shot compile from brief + ledger + dossiers; never parallel section-writing; separate citation-verification pass |
| Context truncation / session death mid-research | M (3) | H (5) | 15 Medium | All state on disk (brief, charters, dossiers, ledger); Eternity-compatible resume; conversation holds references, not content |

---

## Recommendations

### Tier 1: High Confidence (Multi-Source Agreement)
1. **Adopt the five-phase blueprint:** Scope (interview → frozen brief + coverage checklist → user-editable panel plan) → Panel research (parallel charters, background) → Coverage gate (independent audit vs checklist) → Live Q&A (CRAG router + moderator) → Report (one-shot compile + citation pass).
2. **Template the delegation contract** into every dispatch: objective, dossier schema, tool/source guidance, boundaries, effort tier, stop rule.
3. **Dossier-first economics:** answer from disk; dispatch only on retrieval miss; fast single-loop agents for live dispatches; heavy fan-out reserved for the upfront phase.
4. **Ledger as Nygard-minimal append-only records** with supersession, agent+model attribution, provenance + access date, assumptions and stop-decisions as first-class entries.
5. **One-shot report compilation from ledger + dossiers** with a separate citation-verification pass; ledger tree doubles as the outline.
6. **Categorical confidence labels** (verified / provisional / not-in-corpus) — never numeric scores; abstention auto-dispatches research.
7. **Dual stop rule:** per-perspective budget cap + K=2–3 dry-probe saturation, evidenced in the ledger, per coverage dimension.

### Tier 2: Medium Confidence (Strong but Single-System Evidence)
1. **Co-STORM moderator seat:** mine unsurfaced dossier material for proactive "you didn't ask, but…" turns (topic-relevant-but-question-dissimilar ranking). Highest-leverage single component per ablation; implementable with the in-repo RAG/LanceDB stack or LLM-judged novelty.
2. **Mixed-initiative turn policy:** user interjections always win and can regenerate the panel; anti-rut rule after L=2 consecutive answer turns; degrade to direct-QA mode for clear-target questions.
3. **STORM panel-generation recipe:** derive perspectives from adjacent-topic structures; N=3–5 default, 1+1(+generalist) lite mode.
4. **Citation-entailment QA gate** on the final report (STORM measured 84.83% support even with filtering — verification is not optional).

### Tier 3: Requires Further Investigation
1. **Transport for the live phase:** plain conversation vs IC Mode B's committee-room SSE machinery (ic-server.py). Start with plain conversation; the SSE room is a v2 option.
2. **Sufficiency-check calibration:** what counts as "answerable from dossiers" needs tuning against real sessions; start rule-based (source count + tier + freshness), evaluate with ~20 realistic queries and an LLM-judge rubric (Anthropic's eval recipe).
3. **Automated saturation detection** (Q-Sat-style) vs simple dry-probe counting; start with counting.
4. **Model assignment for dynamic agents:** resolve-agent-model.sh is name-keyed; decide between a representative registered name per role class or pinning models in charters.

---

## Methodology & Limitations

Four parallel research lanes (academic/OSS prior art; commercial systems; failure modes & patterns; internal ACOS survey), executed by independent agents with citation requirements, then cross-verified in a synthesis pass. 30+ external sources across Tiers 1–4; internal claims verified by direct file reads with paths. Limitations: Anthropic/OpenAI/Perplexity benchmark figures are vendor-reported and unreplicated; two launch pages returned 403 and were recovered via secondary relays (marked); Co-STORM contributes several mechanisms as the only system of its kind (labeled Probable); no hands-on evaluation of any system was performed; fast-moving product facts (pricing, limits) should be re-verified before any build decision that depends on them.

---

## Sources

### Tier 1 — Authoritative
1. Cemri et al., "Why Do Multi-Agent LLM Systems Fail?" (MAST), arXiv:2503.13657 (+v3 HTML; OpenReview fAjbYBmonr). Accessed 2026-07-21.
2. Shao et al., "Assisting in Writing Wikipedia-like Articles From Scratch with Large Language Models" (STORM), NAACL 2024, arXiv:2402.14207. Accessed 2026-07-21.
3. Jiang et al., "Into the Unknown Unknowns: Engaged Human Learning through Participation in Language Model Agent Conversations" (Co-STORM), EMNLP 2024, arXiv:2408.15232. Accessed 2026-07-21.
4. Anthropic Engineering, "How we built our multi-agent research system," anthropic.com/engineering/built-multi-agent-research-system. Accessed 2026-07-21. (Benchmarks vendor-reported.)
5. OpenAI, "Deep Research System Card," cdn.openai.com/deep-research-system-card.pdf (2025-02-25). Accessed 2026-07-21.
6. OpenAI API guide "Deep research" + Cookbook introduction, developers.openai.com. Accessed 2026-07-21.
7. Google, "Gemini Deep Research — your personal research assistant," gemini.google/overview/deep-research/; ai.google.dev/gemini-api/docs/deep-research. Accessed 2026-07-21.
8. RAG survey, arXiv:2506.00054 (incl. CRAG arXiv:2401.15884, Adaptive-RAG, Self-RAG mechanics). Accessed 2026-07-21.
9. ACL Findings 2025, "Why Uncertainty Estimation Methods Fall Short in RAG," aclanthology.org/2025.findings-acl.852. Accessed 2026-07-21.
10. SURE-RAG, arXiv:2605.03534; temporal RAG, arXiv:2509.19376; equal-budget comparison, arXiv:2604.02460; Q-Sat AI, arXiv:2511.01935. Accessed 2026-07-21.
11. Nygard, "Documenting Architecture Decisions," cognitect.com (2011-11-15); adr.github.io/adr-templates; Nygard template via joelparkerhenderson/architecture-decision-record. Accessed 2026-07-21.
12. Tight, "Saturation: An Overworked and Misunderstood Concept?", Qualitative Inquiry 2024, doi 10.1177/10778004231183948. Accessed 2026-07-21.
13. langchain.com/blog/open-deep-research (+ github.com/langchain-ai/open_deep_research). Accessed 2026-07-21.
14. github.com/assafelovic/gpt-researcher README (v3.6.0, 28.5k stars). Accessed 2026-07-21.
15. Roucher et al., "Open-source DeepResearch," huggingface.co/blog/open-deep-research. Accessed 2026-07-21.
16. github.com/stanford-oval/storm README (30.2k stars; DiscourseManager). Accessed 2026-07-21.
17. Perplexity, "Introducing Perplexity Deep Research," perplexity.ai/hub/blog (403'd; quotes via search relay + official Threads post). Accessed 2026-07-21.
18. Internal (direct file evidence): CLAUDE.md Restricted Files; `.claude/skills/acos-investment-committee/` (SKILL.md, roster.yaml, scripts/resolve_roster.py, scripts/render_memo.py, scripts/committee-room/, scripts/resume.py); `.claude/agents/ic-research-bot.md`, `.claude/agents/ic-01-credit-valuation.md`; `~/.claude/skills/acos-swarm-research/SKILL.md`; `~/.claude/skills/acos-swarm-review/SKILL.md`; `.claude/skills/technology-research/SKILL.md`; `.claude/skills/prism-research/SKILL.md`; `.claude/skills/acos-deep-research/SKILL.md`; `.claude/scripts/resolve-agent-model.sh`; `memory/handoffs/closed/2026-07-21-Website-Research-close/handoff.yaml`; `.claude/scripts/rag/`; `.acos/` output conventions.

### Tier 2 — Expert
1. FutureAGI, "Why do multi agent LLM systems fail (and how to fix)," futureagi.substack.com. Accessed 2026-07-21.
2. Cognition, "Don't Build Multi-Agents" + "Multi-Agents: What's Actually Working," cognition.com/blog. Accessed 2026-07-21.
3. promptingguide.ai, "OpenAI Deep Research Guide." Accessed 2026-07-21.
4. Microsoft Community Hub, "Confidence-Aware RAG." Accessed 2026-07-21.
5. Zimmermann, "The MADR Template Explained and Distilled," ozimmer.ch. Accessed 2026-07-21.
6. Lab Manager, "Audit Trail Requirements for AI-Assisted Laboratory Systems." Accessed 2026-07-21.
7. MindStudio, "Google Gemini Deep Research API." Accessed 2026-07-21.
8. Saturation summaries: simplypsychology.org, dovetail.com, heymarvin.com. Accessed 2026-07-21.
9. Anthropic-system summaries: theaiengineer.substack.com, blog.bytebytego.com. Accessed 2026-07-21.

### Tier 3/4 — Empirical / Community
1. Benchmark figures as self-reported: GAIA 55.15% (HuggingFace), HLE 26.6% (OpenAI) / 21.1% (Perplexity), SimpleQA 93.9% (Perplexity), ~$0.4/run (GPT Researcher).
2. TianPan.co, "The RAG Freshness Problem" [Tier 4]. Curry, "The Coordination Threshold" (p^N illustration) [Tier 4]. Sapio Sciences ELN/AILN [Tier 2 vendor]. Accessed 2026-07-21.

---

## Audit Trail
**Research Conducted:** 2026-07-21 (four parallel lanes + synthesis, same day)
**Verification Standard:** Standard (2+ sources for key claims; single-source items labeled Probable/Open; conflicts preserved, not harmonized)
**Working notes:** session scratchpad, lane files 1–4 (lane1-academic-oss-prior-art.md, lane2-commercial-systems.md, lane3-patterns-failure-modes.md, lane4-internal-prior-art.md)
