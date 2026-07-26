## 2. Goals, non-goals, and success criteria

### 2.1 Goals

| # | Goal | Why |
|---|---|---|
| G1 | A single human, in one working session, goes from "I need a site" to a locked, publishable site that looks deliberately designed | The whole product |
| G2 | Every visual decision traces to an interview answer or an explicit human pick | Makes the design defensible and re-derivable; operationalises the prior report's concept-gate traceability rule |
| G3 | The design system is coherent by construction — derived values are computed, never picked (D1) | Prevents the clash that ~80 independently-chosen items produces |
| G4 | The site works at 320px and 1440px without the human doing responsive work (D2) | Constraint dragging exists for this reason |
| G5 | LOCK produces a static site with provably zero editor runtime, reversibly (D3) | The export contract |
| G6 | Run N+1 starts warm from run N's reusable assets without inheriting run N's identity | Warm start that doesn't homogenise the user's portfolio |
| G7 | Every font and asset in the shipped site has a recorded licence class | Legal exposure is concentrated here |
| G8 | The tool is used more than twice | The manual hand-carry is the biggest threat to this |

### 2.2 Non-goals

| # | Non-goal | Reason |
|---|---|---|
| NG1 | AI aesthetic judging of any kind | Replaced by the human, per the product brief |
| NG2 | Multi-user real-time collaboration | Single-user product; comment schema is collaboration-ready but no second writer in v1–v3 |
| NG3 | A CMS or backend | Static output; forms use a third-party endpoint or a mailto fallback |
| NG4 | Application-shell UI (dashboards, auth, settings, data tables at scale) | 62 inventory items are app-shell/commerce/exotic-chart [I: figure carried over from the §7/§8 component inventory tally; not independently recounted in this revision pass — treat as approximate until a §7/§8 audit re-confirms the exact count]; gated behind the site-type answer and deferred to v3 |
| NG5 | Raster image generation inside the pipeline | Structurally impossible on the claude.ai leg |
| NG6 | Rewriting existing Python ACOS tooling | Read-only reference; new code is TypeScript per the standing language rule |

### 2.3 Success criteria

Split below into the **v1 ship bar** (every criterion here must pass before v1 is considered done)
and criteria that are legitimately **out of the v1 bar** because the capability they measure is
scoped to a later version elsewhere in this PRD. A criterion never counts as "unmeasured because
it's hard" — it only leaves the v1 bar when another section has already, explicitly, deferred the
underlying feature.

**v1 ship bar**

| # | Criterion | Measurement |
|---|---|---|
| S1 | Interview completes in ≤30 minutes for the common case | Wall-clock, single-language single-surface marketing site, ~35–45 answered questions |
| S2 | Hand-carry completes in ≤3 pastes per chunk, ≤6 chunks total | Count of `pbpaste` ingests per generation cycle. Terminology note: §4 Step 3 names this mechanism the "one-paste protocol," which promises exactly one paste per chunk; this criterion's ≤3 tolerance is the *budget for retries*, not a redefinition of success. A 2nd or 3rd paste within one chunk means a retry happened (e.g. a failed parse or an incomplete clipboard capture) and each such retry should be logged as a near-miss against S2 even though it still counts as a pass at ≤3. Hitting the ≤3 ceiling on a majority of chunks is itself a signal the "one-paste" mechanism in §4 is not working as designed and should be raised as a defect against §4, not just tracked here. §4 should be reconciled to either rename the mechanism (e.g. "bounded-paste protocol") or state this retry semantics explicitly — open as of this revision. |
| S3 | Zero `data-wb-*` strings in `dist/published/**` | Grep assertion, build-failing |
| S4 | Editor-installed build and editor-uninstalled build are byte-identical | `diff -r` of two dist trees |
| S5 | Locked site passes all Tier-1 lock gates (§13.4) | Gate suite exit code |
| S6 | The human can name why they chose their direction | The concept document records it; qualitative |
| S8 | Zero shipped assets or fonts without a recorded licence class | Grep/lint assertion against the evidence bundle (§ evidence-bundle content list — every font-family and asset filename referenced in `dist/published/**` has a matching licence-class entry), build-failing. Closes G7, which previously had no operationalised criterion despite being flagged in its own "Why" column as where legal exposure concentrates. |
| S9 | Repeat use: the same ACOS project shows more than one completed run (warm-start or fresh) within a tracked window | Count of completed LOCK events attributed to the same project identifier. **Open question, no known mitigation yet**: this PRD does not currently specify a telemetry/analytics mechanism, a "project identifier" persistence scheme, or a tracked-window length (the gap suggestion proposed 90 days as an example, not a decision). Until product decides whether any usage telemetry is acceptable for a tool that otherwise has no backend (NG3) and no multi-user tracking (NG2), S9 cannot be measured automatically — it degrades to a qualitative/self-reported proxy (e.g. asking the user in a later session whether this is a repeat run against a warm-started project). Requires user decision on: (a) whether local-only usage logging is in scope at all, (b) the window length, (c) whether this is measured per-machine or per-user. Closes the "G8 has no success criterion" gap by giving it a criterion; does not close the measurement-mechanism gap, which is inherited from the fact that G8 itself was never given an implementation plan elsewhere in the PRD. |

**Deferred to v2 (not part of the v1 ship bar)**

| # | Criterion | Measurement | Deferred because |
|---|---|---|---|
| S7 | A content-only edit six months later requires no dev server | Content mode (§15.5) | §3.3's usage-model table tags Content mode as "(v2)." S7 measures a capability that does not exist in v1, so it cannot be part of the v1 acceptance bar. It remains a real, tracked success criterion for whenever Content mode ships — it is not deleted — but a v1 sign-off checklist that includes S7 unqualified is invalid and should be corrected to check S1–S6 + S8–S9 only. If Content mode is pulled forward into v1 scope (a scope change, not something this section can decide unilaterally), S7 moves back into the v1 ship bar and this row is removed. |

---
