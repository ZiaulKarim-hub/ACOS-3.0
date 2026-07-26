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
| NG4 | Application-shell UI (dashboards, auth, settings, data tables at scale) | 62 inventory items are app-shell/commerce/exotic-chart; gated behind the site-type answer and deferred to v3 |
| NG5 | Raster image generation inside the pipeline | Structurally impossible on the claude.ai leg |
| NG6 | Rewriting existing Python ACOS tooling | Read-only reference; new code is TypeScript per the standing language rule |

### 2.3 Success criteria

| # | Criterion | Measurement |
|---|---|---|
| S1 | Interview completes in ≤30 minutes for the common case | Wall-clock, single-language single-surface marketing site, ~35–45 answered questions |
| S2 | Hand-carry completes in ≤3 pastes per chunk, ≤6 chunks total | Count of `pbpaste` ingests per generation cycle |
| S3 | Zero `data-wb-*` strings in `dist/published/**` | Grep assertion, build-failing |
| S4 | Editor-installed build and editor-uninstalled build are byte-identical | `diff -r` of two dist trees |
| S5 | Locked site passes all Tier-1 lock gates (§13.4) | Gate suite exit code |
| S6 | The human can name why they chose their direction | The concept document records it; qualitative |
| S7 | A content-only edit six months later requires no dev server | Content mode (§15.5) |

---

