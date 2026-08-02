// lib/layers.ts — the 27-layer capture library + the ADAPTIVE selection protocol.
//
// Phase 0 of /acos-reverse-cleanroom does NOT run a fixed number of capture layers.
// The orchestrator runs a cheap recon pass, detects the app's SHAPE (which signals
// are present), then selects the subset of the 27-layer library predicted to reach
// `coverage_benchmark` (default 0.99) of THIS app's feature+intent surface. The count
// varies per app (illustratively 7–27, no hardcoded number).
//
// This module is PURE (no I/O, no Playwright): the browser-driving lives in capture.ts.
// The decision logic — which layers, in what order, when the benchmark is met — is here
// so it can be unit-tested without a live target. See references/capture-layers.md.

export type LayerTier =
  | "core" // nearly always run
  | "core-role" // core when >1 auth role exists (per-role differentiation)
  | "conditional" // run ONLY if its trigger signal was detected in recon
  | "ext"; // added while chasing the coverage benchmark (value-ranked top-up)

export interface Layer {
  n: number; // library index (1–27), stable
  id: string; // kebab-case id used on the CLI / in audit records
  name: string;
  tier: LayerTier;
  /** For conditional layers: the recon signal name that must be detected to include it. */
  signal?: string;
  /** Relative marginal coverage contribution. Higher = covers more of the surface. */
  weight: number;
  catches: string; // what this layer uniquely observes
}

/** The always-on probe — runs on EVERY app regardless of the adaptive selection. */
export const ALWAYS_ON_PROBE = {
  id: "server-invisible-probe",
  name: "Server-invisible behavior probe",
  catches: "rate limits / webhooks / emails / scheduled jobs (the back-end iceberg)",
} as const;

// The full library. Tiers + signals mirror references/capture-layers.md exactly.
export const LAYER_LIBRARY: Layer[] = [
  { n: 1, id: "structure-discovery", name: "Structure discovery", tier: "core", weight: 10, catches: "full map + surface-census.json (the completeness denominator)" },
  { n: 2, id: "behavioral-capture", name: "Behavioral capture", tier: "core", weight: 10, catches: "what the app DOES when driven (provoke states, not just crawl)" },
  { n: 3, id: "contract-inference", name: "Contract inference", tier: "core", weight: 10, catches: "the back-end call contract (INFERENCE — exercised endpoints only)" },
  { n: 4, id: "source-map-extraction", name: "Source-map extraction", tier: "conditional", signal: "sourcemaps-served", weight: 5, catches: "collapses black-box → readable source when sourcemaps are served" },
  { n: 5, id: "vision-capture", name: "Vision capture", tier: "core", weight: 10, catches: "the rendered look/layout (~83–87% element-fidelity ceiling)" },
  { n: 6, id: "accessibility-tree", name: "Accessibility tree", tier: "core", weight: 10, catches: "roles/names/states screenshots can't show" },
  { n: 7, id: "auth-role-sweep", name: "Auth-role sweep", tier: "core-role", weight: 6, catches: "that the app differs per role (never automates a login-wall bypass)" },
  { n: 8, id: "client-storage-state", name: "Client storage & state", tier: "ext", weight: 2, catches: "what the app persists on-device: tokens, settings, flags" },
  { n: 9, id: "console-client-error", name: "Console & client-error", tier: "ext", weight: 2, catches: "hidden error paths + warnings the UI never shows" },
  { n: 10, id: "third-party-dependency", name: "Third-party dependency", tier: "conditional", signal: "external-scripts", weight: 5, catches: "outside services a rebuild must replace or re-integrate" },
  { n: 11, id: "security-surface", name: "Security-surface", tier: "ext", weight: 2, catches: "the defenses (CSP/CORS/auth/rate-limit headers) a rebuild must reproduce" },
  { n: 12, id: "realtime-transport", name: "Real-time transport", tier: "conditional", signal: "realtime-detected", weight: 5, catches: "WebSocket/SSE/long-poll live features a request log misses" },
  { n: 13, id: "data-model-schema", name: "Data-model / schema", tier: "core", weight: 10, catches: "the shape of the domain data (what a record contains)" },
  { n: 14, id: "authorization-matrix", name: "Authorization matrix", tier: "core-role", weight: 6, catches: "the real who-can-do-what access rules (allowed vs 403)" },
  { n: 15, id: "business-rules-validation", name: "Business-rules / validation", tier: "conditional", signal: "forms-or-calc", weight: 5, catches: "exact validation + computation logic, VERBATIM to the rule ledger" },
  { n: 16, id: "navigation-state-machine", name: "Navigation / state-machine", tier: "conditional", signal: "multistep-flows", weight: 5, catches: "the ORDER + gating of multi-step flows" },
  { n: 17, id: "search-query-behavior", name: "Search & query-behavior", tier: "conditional", signal: "search-present", weight: 5, catches: "ranking, fuzzy match, empty-result handling" },
  { n: 18, id: "notification-content", name: "Notification-content", tier: "conditional", signal: "outbound-messaging", weight: 5, catches: "WHAT outbound messages say (the probe only sees THAT they fire)" },
  { n: 19, id: "internationalization", name: "Internationalization (i18n)", tier: "conditional", signal: "multi-locale", weight: 5, catches: "which strings are translated; date/money/format/RTL behavior" },
  { n: 20, id: "device-responsive-matrix", name: "Device / responsive matrix", tier: "ext", weight: 2, catches: "how the app reshapes per device + user preference" },
  { n: 21, id: "time-dependent-behavior", name: "Time-dependent behavior", tier: "conditional", signal: "time-dependent", weight: 5, catches: "background/scheduled behavior (expiries/reminders)" },
  { n: 22, id: "offline-resilience", name: "Offline / resilience", tier: "conditional", signal: "service-worker", weight: 5, catches: "behavior when the network fails (service workers, retry)" },
  { n: 23, id: "content-vs-code", name: "Content-vs-code (CMS)", tier: "conditional", signal: "editable-content", weight: 5, catches: "what is data (admin-editable) vs hard-coded UI" },
  { n: 24, id: "legal-compliance-surface", name: "Legal / compliance-surface", tier: "conditional", signal: "consent-privacy", weight: 5, catches: "consent/privacy/export/delete features a rebuild legally must keep" },
  { n: 25, id: "seo-metadata", name: "SEO / metadata", tier: "conditional", signal: "public-pages", weight: 5, catches: "titles/meta/sitemap/robots/structured-data/Open Graph" },
  { n: 26, id: "analytics-event-taxonomy", name: "Analytics / event taxonomy", tier: "ext", weight: 2, catches: "the product's own success metrics + event names" },
  { n: 27, id: "deep-performance-profiling", name: "Deep performance profiling", tier: "ext", weight: 2, catches: "WHERE + WHY it's slow (deeper than the layer-5/baseline snapshot)" },
];

/** The set of every signal name a conditional layer can be triggered by. */
export const KNOWN_SIGNALS: string[] = LAYER_LIBRARY
  .filter((l) => l.tier === "conditional" && l.signal)
  .map((l) => l.signal!);

/** Recon output: how many auth roles exist + which app-shape signals were detected. */
export interface ReconSignals {
  roles: number; // count of distinct auth roles (anon counts as 1)
  detected: string[]; // subset of KNOWN_SIGNALS observed in the recon pass
}

const byId = new Map(LAYER_LIBRARY.map((l) => [l.id, l]));
export const layerById = (id: string): Layer | undefined => byId.get(id);

/**
 * A layer is APPLICABLE to an app when it CAN meaningfully run:
 *  - core: always
 *  - core-role: only when more than one auth role exists
 *  - conditional: only when its trigger signal was detected
 *  - ext: always (adds value on any app; selected via top-up, not auto)
 * The applicable set is the coverage DENOMINATOR — you cannot cover behavior an app
 * does not have, so a conditional whose signal is absent is neither covered nor missing.
 */
export function isApplicable(layer: Layer, s: ReconSignals): boolean {
  switch (layer.tier) {
    case "core":
      return true;
    case "core-role":
      return s.roles > 1;
    case "conditional":
      return !!layer.signal && s.detected.includes(layer.signal);
    case "ext":
      return true;
  }
}

export function applicableLayers(s: ReconSignals): Layer[] {
  return LAYER_LIBRARY.filter((l) => isApplicable(l, s));
}

/** Estimated coverage = selected applicable weight / total applicable weight (0..1). */
export function coverageOf(selected: Set<string>, s: ReconSignals): number {
  const applicable = applicableLayers(s);
  const total = applicable.reduce((a, l) => a + l.weight, 0);
  if (total === 0) return 1; // nothing to cover → fully covered by definition
  const got = applicable
    .filter((l) => selected.has(l.id))
    .reduce((a, l) => a + l.weight, 0);
  return got / total;
}

/** ext layers not yet selected, ranked by descending value (weight, then id for stability). */
export function remainingExtByValue(selected: Set<string>, s: ReconSignals): Layer[] {
  return applicableLayers(s)
    .filter((l) => l.tier === "ext" && !selected.has(l.id))
    .sort((a, b) => b.weight - a.weight || a.id.localeCompare(b.id));
}

export interface SelectionResult {
  selected: { id: string; n: number; tier: LayerTier; reason: string }[];
  skipped: { id: string; n: number; tier: LayerTier; reason: string }[];
  always_on: string[]; // ALWAYS_ON_PROBE.id
  coverage: number; // estimated coverage of the final selection
  benchmark: number;
  benchmark_met: boolean;
  denominator_layers: number; // count of applicable layers (the coverage denominator)
  roles: number;
}

/**
 * The selection protocol (estimate side of the inner loop):
 *   1. seed core (+ core-role when >1 role) + the always-on probe
 *   2. fire each conditional whose signal was detected
 *   3. top-up: add the next-best ext layer until coverage ≥ benchmark or ext is exhausted
 *
 * The runtime inner loop re-runs step 3 with MEASURED coverage via remainingExtByValue().
 */
export function selectLayers(s: ReconSignals, opts: { benchmark?: number } = {}): SelectionResult {
  const benchmark = clampBenchmark(opts.benchmark ?? 0.99);
  const selected = new Set<string>();
  const reasons = new Map<string, string>();

  // 1 + 2 — seed core / core-role / triggered conditionals
  for (const l of LAYER_LIBRARY) {
    if (l.tier === "core") {
      selected.add(l.id);
      reasons.set(l.id, "core (always run)");
    } else if (l.tier === "core-role" && s.roles > 1) {
      selected.add(l.id);
      reasons.set(l.id, `core-role (${s.roles} auth roles)`);
    } else if (l.tier === "conditional" && isApplicable(l, s)) {
      selected.add(l.id);
      reasons.set(l.id, `conditional signal '${l.signal}' detected`);
    }
  }

  // 3 — top-up ext by value until benchmark met or ext exhausted.
  // Guard the loop against an unreachable benchmark (>1.0) so it always terminates.
  let guard = LAYER_LIBRARY.length + 1;
  while (coverageOf(selected, s) < benchmark && guard-- > 0) {
    const next = remainingExtByValue(selected, s)[0];
    if (!next) break; // library exhausted
    selected.add(next.id);
    reasons.set(next.id, `ext top-up → benchmark ${benchmark}`);
  }

  const coverage = coverageOf(selected, s);
  const selectedOut: SelectionResult["selected"] = [];
  const skippedOut: SelectionResult["skipped"] = [];
  for (const l of LAYER_LIBRARY) {
    if (selected.has(l.id)) {
      selectedOut.push({ id: l.id, n: l.n, tier: l.tier, reason: reasons.get(l.id)! });
    } else {
      let reason: string;
      if (l.tier === "core-role") reason = `skipped — only ${s.roles} role (needs >1)`;
      else if (l.tier === "conditional") reason = `skipped — signal '${l.signal}' not detected`;
      else reason = "skipped — benchmark met without this ext layer";
      skippedOut.push({ id: l.id, n: l.n, tier: l.tier, reason });
    }
  }

  return {
    selected: selectedOut,
    skipped: skippedOut,
    always_on: [ALWAYS_ON_PROBE.id],
    coverage,
    benchmark,
    benchmark_met: coverage >= benchmark,
    denominator_layers: applicableLayers(s).length,
    roles: s.roles,
  };
}

/** Benchmarks above 1.0 are unreachable; clamp defensively but keep <1.0 as given. */
function clampBenchmark(b: number): number {
  if (!Number.isFinite(b) || b <= 0) return 0.99;
  return b;
}
