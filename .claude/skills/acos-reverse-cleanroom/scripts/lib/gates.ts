// lib/gates.ts — the mechanical gates of /acos-reverse-cleanroom, pure + testable.
//
// These are the points where the pipeline BLOCKS mechanically instead of trusting an
// agent's prose. Each returns a structured verdict (never throws on a normal failure) so
// the CLI wrapper (gate.ts) can turn it into an exit code and the orchestrator can loop.
//
//   • completenessGate  — Phase 3.5 (PRD) & Phase 5 (fused plan): every kept intent/surface/
//                          rule/parity item maps to a requirement, or is explicitly waived.
//   • protectedSetGate  — Phase 3: BLOCK+HALT if a proposed cut hits a protected item
//                          (rule-ledger / behavior-critical / human-essential).
//   • buildabilityGate  — Phase 5: the fused plan must decompose leaves-first into an acyclic
//                          component graph with every component independently testable.
//   • traceabilityGate  — Phase 6: every intent_id / REQ maps to a component, or is waived.

// ─── Shared mapping gate (completeness + traceability share this core) ────────────────

export interface MappingGateResult {
  verdict: "PASS" | "FAIL";
  total: number;
  mapped: number;
  waived: number;
  unmapped: string[]; // the items that block — neither mapped nor waived
}

/**
 * Every id in `items` must be present in `coveredIds` (something maps to it) OR in `waivers`
 * (explicitly waived with a reason recorded elsewhere). Anything else is an unmapped blocker.
 * Ids are compared exactly (no normalization) — ids are machine tokens, not prose.
 */
export function mappingGate(items: string[], coveredIds: string[], waivers: string[] = []): MappingGateResult {
  const covered = new Set(coveredIds);
  const waived = new Set(waivers);
  const seen = new Set<string>();
  const unmapped: string[] = [];
  let mapped = 0;
  let waivedCount = 0;
  for (const raw of items) {
    const id = String(raw);
    if (seen.has(id)) continue; // dedupe the item list
    seen.add(id);
    if (covered.has(id)) mapped++;
    else if (waived.has(id)) waivedCount++;
    else unmapped.push(id);
  }
  return {
    verdict: unmapped.length === 0 ? "PASS" : "FAIL",
    total: seen.size,
    mapped,
    waived: waivedCount,
    unmapped: unmapped.sort(),
  };
}

// ─── Completeness gate (Phase 3.5 PRD, Phase 5 plan) ──────────────────────────────────

/** Kept items that MUST each be satisfied by the PRD/plan. */
export interface KeptItems {
  intents?: string[]; // kept intent_ids (Won't-list cuts are excluded upstream)
  surfaces?: string[]; // surface ids from surface-census.json
  rules?: string[]; // rule-ledger entry ids
  parity?: string[]; // parity case ids
}

/** A requirement (or plan component) and the item ids it satisfies. */
export interface Requirement {
  req_id: string;
  maps: string[]; // intent/surface/rule/parity ids this requirement covers
}

export interface CompletenessResult extends MappingGateResult {
  by_kind: Record<string, { total: number; unmapped: string[] }>;
}

export function completenessGate(kept: KeptItems, requirements: Requirement[], waivers: string[] = []): CompletenessResult {
  const covered = requirements.flatMap((r) => r.maps ?? []);
  const kinds: (keyof KeptItems)[] = ["intents", "surfaces", "rules", "parity"];
  const allItems: string[] = [];
  const by_kind: CompletenessResult["by_kind"] = {};
  const coveredSet = new Set(covered);
  const waivedSet = new Set(waivers);
  for (const kind of kinds) {
    const arr = kept[kind] ?? [];
    allItems.push(...arr);
    const un = [...new Set(arr.map(String))].filter((id) => !coveredSet.has(id) && !waivedSet.has(id)).sort();
    by_kind[kind] = { total: new Set(arr.map(String)).size, unmapped: un };
  }
  const base = mappingGate(allItems, covered, waivers);
  return { ...base, by_kind };
}

// ─── Protected-set hard gate (Phase 3) ────────────────────────────────────────────────

export interface ProtectedIndex {
  rule_ledger?: string[]; // ids linked to a verbatim rule-ledger entry
  behavior_critical?: string[]; // public API / export / integration surfaces (Hyrum's Law)
  human_essential?: string[]; // items a human marked essential at Gate B
}

export interface Cut {
  id: string; // the intent/feature id being cut
  reason?: string;
}

export interface ProtectedSetResult {
  verdict: "OK" | "BLOCK";
  violations: { id: string; protected_by: string[] }[];
  checked: number;
}

/**
 * BLOCK + HALT if ANY proposed cut references an id that sits in a protected set. A false cut
 * of a rule-ledger / behavior-critical / human-essential item is catastrophic and expensive
 * to reverse late, so this gate is mechanical and absolute — a single violation blocks.
 */
export function protectedSetGate(cuts: Cut[], protectedIndex: ProtectedIndex): ProtectedSetResult {
  const buckets: [string, Set<string>][] = [
    ["rule_ledger", new Set((protectedIndex.rule_ledger ?? []).map(String))],
    ["behavior_critical", new Set((protectedIndex.behavior_critical ?? []).map(String))],
    ["human_essential", new Set((protectedIndex.human_essential ?? []).map(String))],
  ];
  const violations: ProtectedSetResult["violations"] = [];
  for (const cut of cuts) {
    const id = String(cut.id);
    const hitBy = buckets.filter(([, set]) => set.has(id)).map(([name]) => name);
    if (hitBy.length > 0) violations.push({ id, protected_by: hitBy });
  }
  return { verdict: violations.length === 0 ? "OK" : "BLOCK", violations, checked: cuts.length };
}

// ─── Buildability dry-run (Phase 5) ───────────────────────────────────────────────────

export interface Component {
  id: string;
  deps?: string[]; // ids this component depends on (its children)
  testable?: boolean; // does it carry a verifier / independent auto-check?
}

export interface BuildabilityResult {
  verdict: "PASS" | "FAIL";
  acyclic: boolean;
  order: string[]; // a leaves-first topological order (empty if cyclic)
  cycle: string[]; // one detected dependency cycle (empty if acyclic)
  untestable: string[]; // components with no independent verifier
  unknown_deps: string[]; // deps referencing ids not present in the tree
}

/**
 * A fused plan is buildable only if it decomposes leaves-first: the dependency graph must be
 * acyclic (so there is a bottom to start from) AND every component must be independently
 * testable (so each part can be verified before it is composed upward). Either failure FAILs.
 */
export function buildabilityGate(components: Component[]): BuildabilityResult {
  const ids = new Set(components.map((c) => c.id));
  const deps = new Map<string, string[]>();
  const unknownDeps = new Set<string>();
  for (const c of components) {
    const ds = (c.deps ?? []).map(String);
    deps.set(c.id, ds);
    for (const d of ds) if (!ids.has(d)) unknownDeps.add(d);
  }

  // Kahn's algorithm — leaves (no deps) first. If it can't drain, there's a cycle.
  const order: string[] = [];
  const remaining = new Map<string, Set<string>>();
  for (const c of components) remaining.set(c.id, new Set((deps.get(c.id) ?? []).filter((d) => ids.has(d))));
  let progress = true;
  while (order.length < components.length && progress) {
    progress = false;
    for (const [id, need] of remaining) {
      if (order.includes(id)) continue;
      if (need.size === 0) {
        order.push(id);
        for (const [, n2] of remaining) n2.delete(id);
        progress = true;
      }
    }
  }
  const acyclic = order.length === components.length;

  // Report one cycle: the components that never drained.
  const cycle = acyclic ? [] : components.map((c) => c.id).filter((id) => !order.includes(id)).sort();
  const untestable = components.filter((c) => c.testable === false).map((c) => c.id).sort();

  const verdict = acyclic && untestable.length === 0 ? "PASS" : "FAIL";
  return { verdict, acyclic, order: acyclic ? order : [], cycle, untestable, unknown_deps: [...unknownDeps].sort() };
}

// ─── Traceability gate (Phase 6) ──────────────────────────────────────────────────────

export interface TraceabilityResult extends MappingGateResult {}

/**
 * Every intent_id / REQ id must map to a built component (in `mappedIds`) or be explicitly
 * waived. This is the Phase-6 hard gate that blocks completion — the last check that nothing
 * the pipeline promised silently vanished between spec and build.
 */
export function traceabilityGate(itemIds: string[], mappedIds: string[], waivers: string[] = []): TraceabilityResult {
  return mappingGate(itemIds, mappedIds, waivers);
}
