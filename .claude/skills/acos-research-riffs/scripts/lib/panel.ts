/**
 * The panel: generated seats, their charters, and mid-session mutation.
 *
 * Seats are GENERATED per question rather than chosen from a fixed roster, but
 * two seats are structural and always present:
 *   generalist — covers the fundamentals that specialists collectively skip;
 *   skeptic    — tasked to refute the emerging consensus and find what the
 *                others will miss. This is the seat that exists because the
 *                previous research missed tools a reader later named.
 *
 * Charters are rendered from templates/ and handed to a subagent at dispatch.
 * No agent definition file is created per run — .claude/agents/ is restricted
 * infrastructure.
 */

import { existsSync, readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { readJson, writeFileEnsured, writeJson } from "./util.ts";
import { paths, TIERS, type Tier } from "./session.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
export const TEMPLATE_DIR = join(HERE, "..", "..", "templates");

export type SeatRole = "researcher" | "generalist" | "skeptic" | "auditor" | "probe";
export type SeatStatus = "proposed" | "active" | "done" | "retired";

export interface Seat {
  slug: string;
  role: SeatRole;
  title: string;
  objective: string;
  lane: string;
  not_lane: string;
  dimensions: string[];
  status: SeatStatus;
  added_at?: string;
  rationale?: string;
}

export interface Panel {
  seats: Seat[];
  approved: boolean;
  history: Array<{ ts: string; action: string; slug: string; rationale?: string }>;
}

export function loadPanel(sessionId: string): Panel {
  return readJson<Panel>(paths(sessionId).panel, { seats: [], approved: false, history: [] });
}

export function savePanel(sessionId: string, p: Panel): void {
  writeJson(paths(sessionId).panel, p);
}

export function setPanel(sessionId: string, seats: Seat[]): Panel {
  const p = loadPanel(sessionId);
  p.seats = seats.map((s) => ({ ...s, status: s.status ?? "proposed" }));
  p.approved = false;
  savePanel(sessionId, p);
  return p;
}

export function approvePanel(sessionId: string): Panel {
  const p = loadPanel(sessionId);
  for (const s of p.seats) if (s.status === "proposed") s.status = "active";
  p.approved = true;
  p.history.push({ ts: new Date().toISOString(), action: "approved", slug: "*" });
  savePanel(sessionId, p);
  return p;
}

export function addSeat(sessionId: string, seat: Seat): Panel {
  const p = loadPanel(sessionId);
  if (p.seats.some((s) => s.slug === seat.slug)) {
    throw new Error(`seat already exists: ${seat.slug}`);
  }
  p.seats.push({ ...seat, status: "active", added_at: new Date().toISOString() });
  p.history.push({
    ts: new Date().toISOString(),
    action: "added",
    slug: seat.slug,
    rationale: seat.rationale,
  });
  savePanel(sessionId, p);
  return p;
}

export function retireSeat(sessionId: string, slug: string, rationale: string): Panel {
  const p = loadPanel(sessionId);
  const s = p.seats.find((x) => x.slug === slug);
  if (!s) throw new Error(`unknown seat: ${slug}`);
  s.status = "retired";
  p.history.push({ ts: new Date().toISOString(), action: "retired", slug, rationale });
  savePanel(sessionId, p);
  return p;
}

export function validatePanel(p: Panel): string[] {
  const problems: string[] = [];
  const live = p.seats.filter((s) => s.status !== "retired");
  if (!live.some((s) => s.role === "generalist")) {
    problems.push("no generalist seat — specialists will collectively skip fundamentals");
  }
  if (!live.some((s) => s.role === "skeptic")) {
    problems.push("no skeptic seat — nothing is tasked with refuting the consensus");
  }
  const lanes = live.map((s) => s.lane.toLowerCase().trim());
  const dupes = lanes.filter((l, i) => lanes.indexOf(l) !== i);
  if (dupes.length) problems.push(`overlapping lanes: ${[...new Set(dupes)].join("; ")}`);
  return problems;
}

export interface CharterContext {
  sessionId: string;
  seat: Seat;
  brief: string;
  tier: Tier;
  dimensions: Array<{ id: string; name: string; why: string }>;
}

/** Render a seat's delegation contract from templates/ and write it to charters/. */
export function emitCharter(ctx: CharterContext): string {
  const { sessionId, seat, brief, tier } = ctx;
  const tmplName =
    seat.role === "auditor"
      ? "auditor-charter.md"
      : seat.role === "probe"
        ? "probe-charter.md"
        : "researcher-charter.md";
  const tmplPath = join(TEMPLATE_DIR, tmplName);
  if (!existsSync(tmplPath)) throw new Error(`missing template: ${tmplPath}`);
  const spec = TIERS[tier];
  const p = paths(sessionId);
  const dims = ctx.dimensions
    .filter((d) => seat.dimensions.length === 0 || seat.dimensions.includes(d.id))
    .map((d) => `- \`${d.id}\` — ${d.name}: ${d.why}`)
    .join("\n");

  const filled = readFileSync(tmplPath, "utf8")
    .replaceAll("{{SESSION_ID}}", sessionId)
    .replaceAll("{{SLUG}}", seat.slug)
    .replaceAll("{{ROLE}}", seat.role)
    .replaceAll("{{TITLE}}", seat.title)
    .replaceAll("{{OBJECTIVE}}", seat.objective)
    .replaceAll("{{LANE}}", seat.lane)
    .replaceAll("{{NOT_LANE}}", seat.not_lane)
    .replaceAll("{{DIMENSIONS}}", dims || "- (all declared dimensions)")
    .replaceAll("{{DIMENSION_IDS}}", seat.dimensions.join(", ") || "(all)")
    .replaceAll("{{MAX_SEARCHES}}", String(spec.searchesPerResearcher))
    .replaceAll("{{TIER}}", tier)
    .replaceAll("{{BRIEF}}", brief.trim())
    .replaceAll("{{DOSSIER_PATH}}", join(p.dossiers, `${seat.slug}.md`))
    .replaceAll("{{CLAIMS_PATH}}", join(p.dossiers, `${seat.slug}.claims.jsonl`))
    .replaceAll("{{SESSION_ROOT}}", p.root);

  const out = join(p.charters, `${seat.slug}.md`);
  writeFileEnsured(out, filled);
  return out;
}

/**
 * Render a charter that has no panel seat behind it.
 *
 * Live probes, the coverage auditor, the report compiler and the citation
 * verifier are all one-shot roles — they answer to the session, not to a lane,
 * so putting them in the panel would clutter the panel-change history that the
 * report reads as "how the research direction moved".
 */
export function emitRoleCharter(
  sessionId: string,
  template: "probe" | "auditor" | "compiler" | "citer" | "eval",
  opts: { slug?: string; objective?: string; dimension?: string; brief: string; tier: Tier },
): { path: string; slug: string } {
  const tmplPath = join(
    TEMPLATE_DIR,
    template === "eval" ? "eval-rubric.md" : `${template}-charter.md`,
  );
  if (!existsSync(tmplPath)) throw new Error(`missing template: ${tmplPath}`);
  const p = paths(sessionId);
  const slug = opts.slug ?? template;
  const spec = TIERS[opts.tier];
  const filled = readFileSync(tmplPath, "utf8")
    .replaceAll("{{SESSION_ID}}", sessionId)
    .replaceAll("{{SESSION_ROOT}}", p.root)
    .replaceAll("{{SLUG}}", slug)
    .replaceAll("{{ROLE}}", template)
    .replaceAll("{{TITLE}}", template)
    .replaceAll("{{OBJECTIVE}}", opts.objective ?? "(see the brief)")
    .replaceAll("{{DIMENSION_IDS}}", opts.dimension ?? "")
    .replaceAll("{{MAX_SEARCHES}}", String(spec.searchesPerResearcher))
    .replaceAll("{{TIER}}", opts.tier)
    .replaceAll("{{BRIEF}}", opts.brief.trim())
    .replaceAll("{{DOSSIER_PATH}}", join(p.dossiers, `${slug}.md`))
    .replaceAll("{{CLAIMS_PATH}}", join(p.dossiers, `${slug}.claims.jsonl`));
  const out = join(p.charters, `${slug}.md`);
  writeFileEnsured(out, filled);
  return { path: out, slug };
}

export function renderPanel(p: Panel): string {
  if (p.seats.length === 0) return "(no panel yet)";
  return p.seats
    .map(
      (s) =>
        `  [${s.status.padEnd(8)}] ${s.slug.padEnd(20)} ${s.role.padEnd(10)} ${s.title}\n` +
        `${" ".repeat(13)}lane: ${s.lane}\n` +
        `${" ".repeat(13)}not:  ${s.not_lane}`,
    )
    .join("\n");
}
