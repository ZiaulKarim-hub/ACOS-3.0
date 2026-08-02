/**
 * Per-dimension coverage accounting and the dual stop rule (design invariant I8).
 *
 * The prior failure this exists to prevent: FALSE GLOBAL SATURATION — research
 * stopped because nothing new turned up in the lanes that were probed, while
 * whole dimensions were never probed at all. Therefore:
 *   - a dimension with probes === 0 can NEVER read as saturated;
 *   - saturation is K consecutive probes yielding zero novel claims, per
 *     dimension (a seat's own dry report is recorded as agent_saturated,
 *     never forged into the counted streak);
 *   - any novelty resets the dry streak to 0 and clears agent_saturated;
 *   - a fast-moving dimension (fast_moving !== false — the default) cannot
 *     saturate until at least one recency probe — a search restricted to the
 *     recent window (~90 days) — has run; "nothing new in the window" counts
 *     as that probe's result (CONTRACT-7 recency floor);
 *   - a hard budget cap bounds spend independently of saturation.
 */

import { readJson, writeJson } from "./util.ts";
import { loadManifest, paths, SATURATION_K, TIERS, type Tier } from "./session.ts";

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
  /** The seat reported its own question loop dry (I30) — an honest flag, never forged into dry_streak. */
  agent_saturated?: boolean;
  /** CONTRACT-7: absent means TRUE. Only an explicit false exempts a dimension from the recency floor. */
  fast_moving?: boolean;
  /** CONTRACT-7: count of probes flagged `recency` (window-restricted sweeps). Absent means 0. */
  recency_probes?: number;
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

/**
 * Second validation layer behind the CLI (M24): coverage payloads are
 * model-authored JSON, and a mis-keyed element (`dimension_id` for `id`) would
 * land in coverage.json as an id-less dimension that permanently blocks the
 * gate — probe and attest can never target it — while crashing every table
 * render. Throw naming the element instead of persisting it.
 */
function assertDimShape(d: unknown, label: string): void {
  if (!d || typeof d !== "object" || Array.isArray(d)) {
    throw new Error(`coverage dimension ${label}: expected an object {id, name, ...}`);
  }
  const rec = d as Record<string, unknown>;
  const bad: string[] = [];
  for (const f of ["id", "name"] as const) {
    const v = rec[f];
    if (typeof v !== "string" || !v.trim()) bad.push(f);
  }
  if (rec["why"] !== undefined && typeof rec["why"] !== "string") bad.push("why");
  if (rec["fast_moving"] !== undefined && typeof rec["fast_moving"] !== "boolean") {
    bad.push("fast_moving");
  }
  if (bad.length) {
    const named = typeof rec["id"] === "string" && rec["id"] ? ` ("${rec["id"]}")` : "";
    throw new Error(
      `coverage dimension ${label}${named}: missing or malformed field(s): ${bad.join(", ")} — ` +
        `id and name must be non-empty strings`,
    );
  }
}

export function initCoverage(
  sessionId: string,
  dims: Array<{ id: string; name: string; why?: string; fast_moving?: boolean }>,
  tier: Tier,
  force = false,
): Coverage {
  if (!Array.isArray(dims)) {
    throw new Error("coverage init payload must be a JSON array of dimensions");
  }
  dims.forEach((d, i) => assertDimShape(d, `#${i}`));
  // Re-running init would silently wipe every probe count, dry streak, and
  // attestation — the whole saturation record, unrecoverable. Refuse unless
  // forced OR nothing has been probed yet: bare declarations are exactly what
  // this call replaces, so there is nothing to protect (M25). Incremental
  // changes belong to `coverage add`.
  const existing = loadCoverage(sessionId);
  const probed = existing.dimensions.some((d) => d.probes > 0);
  if (existing.dimensions.length > 0 && probed && !force) {
    throw new Error(
      `coverage already declares ${existing.dimensions.length} dimension(s) with recorded probes — ` +
        `re-initializing would wipe all probe counts and attestations. ` +
        `Use \`riff coverage add\` for incremental changes, or --force to discard the record.`,
    );
  }
  const cap = TIERS[tier].searchesPerResearcher;
  const c: Coverage = {
    k: SATURATION_K,
    dimensions: dims.map((d) => ({
      id: d.id,
      name: d.name,
      why: d.why ?? "",
      probes: 0,
      novel_claims: 0,
      dry_streak: 0,
      cap,
      status: "unprobed" as DimensionStatus,
      notes: [],
      // CONTRACT-7: every declared dimension is fast-moving unless the scoper
      // explicitly said otherwise — the default forces the newest releases to
      // be LOOKED for, which no grading rule can substitute for.
      fast_moving: d.fast_moving !== false,
      recency_probes: 0,
    })),
  };
  saveCoverage(sessionId, c);
  return c;
}

export function recomputeStatus(d: Dimension, k: number): DimensionStatus {
  if (d.probes === 0) return "unprobed";
  if (d.attested_by) return "attested";
  // Saturation outranks the cap: a dimension that goes dry on the probe that
  // also reaches its budget is genuinely exhausted, not budget-truncated —
  // "capped" must mean only "stopped by budget without saturating".
  const dry = d.dry_streak >= k || d.agent_saturated === true;
  // CONTRACT-7 recency floor: a fast-moving dimension (the default) may not
  // saturate until at least one recency probe has swept the recent window —
  // dryness on established literature says nothing about last month's releases.
  const recencySwept = d.fast_moving === false || (d.recency_probes ?? 0) > 0;
  if (dry && recencySwept) return "saturated";
  if (d.probes >= d.cap) return "capped";
  return "thin";
}

/**
 * Record one probe against a dimension. `novel` = count of NEW claims it produced.
 *
 * `agentSaturated` means the researcher reported that its OWN internal question
 * loop went dry on this dimension. Without it, a dimension can only clear the
 * gate after three orchestrator-level probes — one productive, then two dry —
 * which triples the cost of every session and ignores the searching the agent
 * already did. The seat's report is evidence and is credited as such (recorded
 * as its own `agent_saturated` flag, never forged into the counted dry streak —
 * I30); what it cannot do is make an unprobed dimension count, because it only
 * applies to a probe that actually happened.
 *
 * `recency` marks a CONTRACT-7 recency probe — a search restricted to the
 * recent window (~90 days). It is what licenses a fast-moving dimension to
 * saturate, and "nothing new in the window" counts as its result, so a
 * zero-novel recency probe still records the sweep.
 */
export function recordProbe(
  sessionId: string,
  dimId: string,
  novel: number,
  note?: string,
  agentSaturated = false,
  recency = false,
): Dimension {
  // Second layer behind the CLI's flag validation: a NaN or negative count
  // would poison novel_claims while counting as a dry probe — an input error
  // must never push a dimension toward saturation (I8).
  if (!Number.isInteger(novel) || novel < 0) {
    throw new Error(`novel claim count must be a non-negative integer, got: ${novel}`);
  }
  const c = loadCoverage(sessionId);
  const d = c.dimensions.find((x) => x.id === dimId);
  if (!d) throw new Error(`unknown coverage dimension: ${dimId}`);
  d.probes += 1;
  d.novel_claims += novel;
  // The dry streak only ever counts real dry probes (I30). Novelty refutes a
  // prior agent-saturation report as surely as it resets the streak (I8).
  d.dry_streak = novel > 0 ? 0 : d.dry_streak + 1;
  if (agentSaturated) d.agent_saturated = true;
  else if (novel > 0) delete d.agent_saturated;
  if (recency) d.recency_probes = (d.recency_probes ?? 0) + 1;
  if (note) {
    const tags = [
      ...(agentSaturated ? ["[agent reports saturation]"] : []),
      ...(recency ? ["[recency probe]"] : []),
    ];
    d.notes.push(tags.length ? `${note} ${tags.join(" ")}` : note);
  }
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
  dim: { id: string; name: string; why?: string; cap?: number; fast_moving?: boolean },
): Dimension {
  assertDimShape(dim, "(coverage add)");
  const c = loadCoverage(sessionId);
  if (c.dimensions.some((d) => d.id === dim.id)) {
    throw new Error(`coverage dimension already exists: ${dim.id}`);
  }
  // Last-resort cap comes from the session's own tier budget, not a hardcoded
  // literal that would silently diverge if TIERS were retuned.
  const cap =
    dim.cap ?? c.dimensions[0]?.cap ?? TIERS[loadManifest(sessionId).tier].searchesPerResearcher;
  const d: Dimension = {
    id: dim.id,
    name: dim.name,
    why: dim.why ?? "",
    probes: 0,
    novel_claims: 0,
    dry_streak: 0,
    cap,
    status: "unprobed",
    notes: [],
    fast_moving: dim.fast_moving !== false,
    recency_probes: 0,
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
 * The coverage gate, computed PURELY (CONTRACT-5). Passes only when EVERY
 * declared dimension has either saturated (K dry probes, plus the recency
 * sweep for fast-moving dimensions) or hit its budget cap. Unprobed or thin
 * dimensions block — this is the structural cure for the missed-tools failure.
 *
 * Recomputes each dimension's status on the in-memory Coverage but touches
 * NOTHING on disk, so the room's read path (room.ts) and query commands can
 * evaluate the gate with zero side effects. evaluateGate is this plus persist.
 */
export function computeGate(c: Coverage): GateResult {
  for (const d of c.dimensions) d.status = recomputeStatus(d, c.k);
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
        : `${blocking.length} dimension(s) still open: ${blocking
            .map((d) =>
              // A blocking dimension that is already dry can only be waiting
              // on the CONTRACT-7 recency sweep — say so, not just the id.
              d.dry_streak >= c.k || d.agent_saturated === true
                ? `${d.id} (awaiting recency probe)`
                : d.id,
            )
            .join(", ")}`,
  };
}

/** The coverage gate with persistence: computeGate, then the recomputed
 *  statuses are written back to coverage.json. Mutating CLI paths (`riff gate`)
 *  call this; pure readers (status/resume/room) call computeGate directly. */
export function evaluateGate(sessionId: string): GateResult {
  const c = loadCoverage(sessionId);
  const res = computeGate(c);
  saveCoverage(sessionId, c);
  return res;
}

export function renderTable(c: Coverage): string {
  const rows = c.dimensions.map((d) => {
    const bar = `${d.probes}/${d.cap}`;
    const attest = d.attested_by ? `  attested by ${d.attested_by}` : "";
    // Surface the CONTRACT-7 debt honestly: a fast-moving dimension that has
    // never been recency-swept cannot saturate, however dry its streak reads.
    const recency =
      d.fast_moving !== false && (d.recency_probes ?? 0) === 0 ? "  [needs recency probe]" : "";
    return `  ${d.status.padEnd(10)} ${d.id.padEnd(24)} probes ${bar.padEnd(8)} dry ${String(
      d.dry_streak,
    ).padEnd(3)} novel ${String(d.novel_claims).padEnd(4)}${attest}${recency}`;
  });
  return rows.join("\n");
}
