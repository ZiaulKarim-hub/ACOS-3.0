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
import { loadCoverage } from "./coverage.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
export const TEMPLATE_DIR = join(HERE, "..", "..", "templates");

/**
 * Where one charter template is read from.
 *
 * `RIFF_TEMPLATE_DIR` is an OVERLAY, not a replacement. A launcher that drives
 * this engine at a different corpus — /investigate reads files where /research
 * reads the web — needs to reword the probe charter without forking the other
 * four. So the override dir is consulted per FILE and falls through to the
 * engine's own templates/ when it does not carry that name. A whole-dir swap
 * would instead force every overlay to vendor all five templates, and adding a
 * sixth template here later would silently break every overlay that predates
 * it (the same "N copies drift" failure the depth dial is data to avoid).
 *
 * Unset env → byte-identical behaviour to before this existed.
 */
export function resolveTemplate(fileName: string): string {
  const override = process.env["RIFF_TEMPLATE_DIR"];
  if (override) {
    const candidate = join(override, fileName);
    if (existsSync(candidate)) return candidate;
  }
  return join(TEMPLATE_DIR, fileName);
}

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
  // The payload arrives as model-authored JSON cast straight to Seat[] — guard
  // the two shapes that would crash HERE before validatePanel's per-seat
  // reporting gets a chance to name the offender (I24): a non-array payload
  // throws named, and null / non-object elements pass through untouched so
  // validatePanel can report them by index.
  if (!Array.isArray(seats)) {
    throw new Error(
      `panel set expects a JSON array of seats, got ${seats === null ? "null" : typeof seats}`,
    );
  }
  const p = loadPanel(sessionId);
  p.seats = seats.map((s) =>
    s && typeof s === "object" ? { ...s, status: s.status ?? "proposed" } : (s as Seat),
  );
  p.approved = false;
  // A re-set replaces the whole roster (dropping approval); leave the same
  // audit trace the other mutating verbs leave, so the panel history the
  // report reads as "how the research direction moved" has no gap (I29).
  p.history.push({
    ts: new Date().toISOString(),
    action: "set",
    slug: "*",
    rationale: `roster replaced: ${p.seats.length} seat(s)`,
  });
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

export function addSeat(sessionId: string, seat: Seat): Panel & { problems: string[] } {
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
  // Mid-session adds bypass the approval gate, and gap rounds are exactly when
  // a hastily added seat duplicates an existing lane — re-validate here so the
  // problems at least surface in the command output instead of passing silently.
  // (Attached after save: warnings are for the caller, not the panel file.)
  return Object.assign(p, { problems: validatePanel(p) });
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

/** Slugs become charter/dossier file names and the claim-id namespace — keep
 *  them path-safe (I25). Shared with emitRoleCharter's --slug. */
const SLUG_RE = /^[a-z0-9][a-z0-9._-]*$/;

export function validatePanel(p: Panel): string[] {
  const problems: string[] = [];
  // `panel set` casts a model-authored payload straight to Seat[] with no shape
  // check, so verify each seat's shape here — a per-seat problem string beats a
  // TypeError that names no seat. Malformed seats are excluded from the checks
  // below (their absence then surfaces naturally, e.g. as a missing role).
  const shaped: Seat[] = [];
  p.seats.forEach((s, i) => {
    const raw = s as Partial<Seat> | null | undefined;
    const missing: string[] = [];
    for (const f of ["slug", "role", "title", "objective", "lane", "not_lane"] as const) {
      if (typeof raw?.[f] !== "string") missing.push(f);
    }
    if (!Array.isArray(raw?.dimensions)) missing.push("dimensions");
    if (missing.length) {
      const label = typeof raw?.slug === "string" ? raw.slug : `#${i}`;
      problems.push(`seat ${label}: missing or malformed field(s): ${missing.join(", ")}`);
      return;
    }
    // A '/', '..', or empty slug scatters charters and dossiers outside the
    // session layout where claims.ts's non-recursive readdir never finds them.
    if (!SLUG_RE.test((raw as Seat).slug)) {
      problems.push(
        `seat ${(raw as Seat).slug || `#${i}`}: slug must match ${SLUG_RE} — ` +
          `it becomes file names and the claim-id namespace`,
      );
    }
    shaped.push(s);
  });
  // Slug uniqueness is the invariant everything downstream keys on — charters,
  // dossier files, claim-id namespaces, retire/charter lookups. addSeat throws
  // on a duplicate, but the bulk `panel set` path lands here instead (M18).
  // Checked across ALL seats: a retired seat still owns its artifacts.
  const slugs = p.seats
    .map((s) => (s as Partial<Seat> | null | undefined)?.slug)
    .filter((x): x is string => typeof x === "string");
  const dupSlugs = slugs.filter((x, i) => slugs.indexOf(x) !== i);
  if (dupSlugs.length) {
    problems.push(`duplicate seat slug(s): ${[...new Set(dupSlugs)].join(", ")}`);
  }
  const live = shaped.filter((s) => s.status !== "retired");
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

/**
 * Literal template substitution, in a SINGLE pass over the template (I26): a
 * placeholder-shaped token inside a VALUE (a brief quoting {{MUSTACHE}} syntax
 * — reachable for a research skill covering template engines) is never
 * re-expanded by a later key, and $-patterns in values ($$, $&, $`, $') stay
 * literal because the replacement comes from a function, not a replacement
 * string. Unknown placeholders survive verbatim for the render tests to catch.
 */
function fill(tmpl: string, vars: Record<string, string>): string {
  return tmpl.replace(/\{\{([A-Z_]+)\}\}/g, (match, key: string) =>
    Object.hasOwn(vars, key) ? vars[key]! : match,
  );
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
  const tmplPath = resolveTemplate(tmplName);
  if (!existsSync(tmplPath)) throw new Error(`missing template: ${tmplPath}`);
  // The brief is the question of record every guardrail is measured against —
  // a charter frozen with an empty scope block spends the seat's whole budget
  // off-target and nothing catches it until the dossier comes back (I27).
  if (!brief.trim()) {
    throw new Error(
      `no brief for session ${sessionId} — run \`riff brief\` before rendering charters`,
    );
  }
  const spec = TIERS[tier];
  const p = paths(sessionId);
  const seatDims = seat.dimensions ?? [];
  // A typo'd dimension id would otherwise be dropped silently below (or, if none
  // survive, replaced by "(all declared dimensions)") — the seat would spend its
  // whole budget tagging claims `coverage probe` rejects while the real dimension
  // sits unprobed and blocks the gate. Fail at render time instead.
  const declared = new Set(ctx.dimensions.map((d) => d.id));
  const unknown = seatDims.filter((id) => !declared.has(id));
  if (unknown.length) {
    throw new Error(
      `seat ${seat.slug} references undeclared coverage dimension(s): ${unknown.join(", ")} — ` +
        `declare them with \`riff coverage add\` or fix the seat's dimensions list`,
    );
  }
  const dims = ctx.dimensions
    .filter((d) => seatDims.length === 0 || seatDims.includes(d.id))
    .map((d) => `- \`${d.id}\` — ${d.name}: ${d.why}`)
    .join("\n");

  const filled = fill(readFileSync(tmplPath, "utf8"), {
    SESSION_ID: sessionId,
    SLUG: seat.slug,
    ROLE: seat.role,
    TITLE: seat.title,
    OBJECTIVE: seat.objective,
    LANE: seat.lane,
    NOT_LANE: seat.not_lane,
    DIMENSIONS: dims || "- (all declared dimensions)",
    DIMENSION_IDS: seatDims.join(", ") || "(all)",
    MAX_SEARCHES: String(spec.searchesPerResearcher),
    TIER: tier,
    BRIEF: brief.trim(),
    DOSSIER_PATH: join(p.dossiers, `${seat.slug}.md`),
    CLAIMS_PATH: join(p.dossiers, `${seat.slug}.claims.jsonl`),
    SESSION_ROOT: p.root,
  });

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
  const tmplPath = resolveTemplate(
    template === "eval" ? "eval-rubric.md" : `${template}-charter.md`,
  );
  if (!existsSync(tmplPath)) throw new Error(`missing template: ${tmplPath}`);
  const p = paths(sessionId);
  const slug = opts.slug ?? template;
  // Same path-safety bar as panel slugs (I25): this value becomes charter and
  // dossier file names, so a '/' or '..' from --slug scatters the record.
  if (!SLUG_RE.test(slug)) {
    throw new Error(`invalid slug "${slug}" — must match ${SLUG_RE} (it becomes file names)`);
  }
  // Mirror emitCharter's undeclared-dimension guard (I28): a typo'd --dimension
  // would otherwise surface only after the probe's budget is spent, as claims
  // tagged with an id the per-dimension accounting never credits.
  if (opts.dimension) {
    const declared = new Set(loadCoverage(sessionId).dimensions.map((d) => d.id));
    const unknown = opts.dimension
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean)
      .filter((x) => !declared.has(x));
    if (unknown.length) {
      throw new Error(
        `charter for ${slug} references undeclared coverage dimension(s): ${unknown.join(", ")} — ` +
          `declare them with \`riff coverage add\` or fix --dimension`,
      );
    }
  }
  const spec = TIERS[opts.tier];
  const filled = fill(readFileSync(tmplPath, "utf8"), {
    SESSION_ID: sessionId,
    SESSION_ROOT: p.root,
    SLUG: slug,
    ROLE: template,
    TITLE: template,
    OBJECTIVE: opts.objective ?? "(see the brief)",
    DIMENSION_IDS: opts.dimension ?? "",
    MAX_SEARCHES: String(spec.searchesPerResearcher),
    TIER: opts.tier,
    BRIEF: opts.brief.trim(),
    DOSSIER_PATH: join(p.dossiers, `${slug}.md`),
    CLAIMS_PATH: join(p.dossiers, `${slug}.claims.jsonl`),
  });
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
