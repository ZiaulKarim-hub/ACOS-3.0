/**
 * Per-dimension coverage accounting and the dual stop rule (design invariant I8).
 *
 * The prior failure this exists to prevent: FALSE GLOBAL SATURATION — research
 * stopped because nothing new turned up in the lanes that were probed, while
 * whole dimensions were never probed at all. Therefore:
 *   - a dimension with probes === 0 can NEVER read as saturated;
 *   - saturation is K consecutive probes yielding zero novel claims, per dimension;
 *   - any novelty resets the dry streak to 0;
 *   - a hard budget cap bounds spend independently of saturation.
 */

import { readJson, writeJson } from "./util.ts";
import { paths, SATURATION_K, TIERS, type Tier } from "./session.ts";

export type DimensionStatus = "unprobed" | "thin" | "saturated" | "capped" | "attested";

export interface Dimension {
  id: string;
  name: string;
  why: string;
  probes: number;
  novel_claims: number;
  dry_streak: number;
  cap: number;
  status: DimensionStatus;
  notes: string[];
  attested_by?: string;
  attested_note?: string;
}

export interface Coverage {
  k: number;
  dimensions: Dimension[];
}

export function loadCoverage(sessionId: string): Coverage {
  return readJson<Coverage>(paths(sessionId).coverage, { k: SATURATION_K, dimensions: [] });
}

export function saveCoverage(sessionId: string, c: Coverage): void {
  writeJson(paths(sessionId).coverage, c);
}

export function initCoverage(
  sessionId: string,
  dims: Array<{ id: string; name: string; why: string }>,
  tier: Tier,
): Coverage {
  const cap = TIERS[tier].searchesPerResearcher;
  const c: Coverage = {
    k: SATURATION_K,
    dimensions: dims.map((d) => ({
      id: d.id,
      name: d.name,
      why: d.why,
      probes: 0,
      novel_claims: 0,
      dry_streak: 0,
      cap,
      status: "unprobed" as DimensionStatus,
      notes: [],
    })),
  };
  saveCoverage(sessionId, c);
  return c;
}

export function recomputeStatus(d: Dimension, k: number): DimensionStatus {
  if (d.probes === 0) return "unprobed";
  if (d.attested_by) return "attested";
  if (d.probes >= d.cap) return "capped";
  if (d.dry_streak >= k) return "saturated";
  return "thin";
}

/**
 * Record one probe against a dimension. `novel` = count of NEW claims it produced.
 *
 * `agentSaturated` means the researcher reported that its OWN internal question
 * loop went dry on this dimension. Without it, a dimension can only clear the
 * gate after three orchestrator-level probes — one productive, then two dry —
 * which triples the cost of every session and ignores the searching the agent
 * already did. The seat's report is evidence and is credited as such; what it
 * cannot do is make an unprobed dimension count, because it only applies to a
 * probe that actually happened.
 */
export function recordProbe(
  sessionId: string,
  dimId: string,
  novel: number,
  note?: string,
  agentSaturated = false,
): Dimension {
  const c = loadCoverage(sessionId);
  const d = c.dimensions.find((x) => x.id === dimId);
  if (!d) throw new Error(`unknown coverage dimension: ${dimId}`);
  d.probes += 1;
  d.novel_claims += novel;
  d.dry_streak = agentSaturated ? c.k : novel > 0 ? 0 : d.dry_streak + 1;
  if (note) d.notes.push(agentSaturated ? `${note} [agent reports saturation]` : note);
  d.status = recomputeStatus(d, c.k);
  saveCoverage(sessionId, c);
  return d;
}

/**
 * The auditor's judgment call on a dimension the counter cannot settle.
 *
 * A dimension can be genuinely well covered by one thorough seat, in which case
 * demanding two more dry probes buys nothing. The auditor — which has read the
 * corpus and has not seen the researchers' reasoning — may attest to that.
 *
 * It may NOT attest a dimension with zero probes. That is the whole failure this
 * system exists to prevent, and no amount of confident judgment substitutes for
 * having looked.
 */
export function attest(
  sessionId: string,
  dimId: string,
  by: string,
  note: string,
): Dimension {
  const c = loadCoverage(sessionId);
  const d = c.dimensions.find((x) => x.id === dimId);
  if (!d) throw new Error(`unknown coverage dimension: ${dimId}`);
  if (d.probes === 0) {
    throw new Error(
      `cannot attest ${dimId}: it has never been probed. ` +
        `An unprobed dimension is exactly the gap this gate exists to catch — research it instead.`,
    );
  }
  d.attested_by = by;
  d.attested_note = note;
  d.status = recomputeStatus(d, c.k);
  saveCoverage(sessionId, c);
  return d;
}

export function addDimension(
  sessionId: string,
  dim: { id: string; name: string; why: string; cap?: number },
): Dimension {
  const c = loadCoverage(sessionId);
  if (c.dimensions.some((d) => d.id === dim.id)) {
    throw new Error(`coverage dimension already exists: ${dim.id}`);
  }
  const cap = dim.cap ?? c.dimensions[0]?.cap ?? 15;
  const d: Dimension = {
    id: dim.id,
    name: dim.name,
    why: dim.why,
    probes: 0,
    novel_claims: 0,
    dry_streak: 0,
    cap,
    status: "unprobed",
    notes: [],
  };
  c.dimensions.push(d);
  saveCoverage(sessionId, c);
  return d;
}

export interface GateResult {
  passed: boolean;
  blocking: Dimension[];
  ready: Dimension[];
  reason: string;
}

/**
 * The coverage gate. Passes only when EVERY declared dimension has either
 * saturated (K dry probes) or hit its budget cap. Unprobed or thin dimensions
 * block — this is the structural cure for the missed-tools failure.
 */
export function evaluateGate(sessionId: string): GateResult {
  const c = loadCoverage(sessionId);
  for (const d of c.dimensions) d.status = recomputeStatus(d, c.k);
  saveCoverage(sessionId, c);
  const blocking = c.dimensions.filter(
    (d) => d.status === "unprobed" || d.status === "thin",
  );
  const ready = c.dimensions.filter(
    (d) => d.status === "saturated" || d.status === "capped" || d.status === "attested",
  );
  if (c.dimensions.length === 0) {
    return { passed: false, blocking, ready, reason: "no coverage dimensions declared" };
  }
  return {
    passed: blocking.length === 0,
    blocking,
    ready,
    reason:
      blocking.length === 0
        ? `all ${c.dimensions.length} dimensions saturated or capped`
        : `${blocking.length} dimension(s) still open: ${blocking.map((d) => d.id).join(", ")}`,
  };
}

export function renderTable(c: Coverage): string {
  const rows = c.dimensions.map((d) => {
    const bar = `${d.probes}/${d.cap}`;
    const attest = d.attested_by ? `  attested by ${d.attested_by}` : "";
    return `  ${d.status.padEnd(10)} ${d.id.padEnd(24)} probes ${bar.padEnd(8)} dry ${String(
      d.dry_streak,
    ).padEnd(3)} novel ${String(d.novel_claims).padEnd(4)}${attest}`;
  });
  return rows.join("\n");
}
