/**
 * Session layout + manifest for acos-research-riffs.
 *
 * All durable state lives on disk (design invariant I6) so the conversation
 * holds references, not content, and a cleared session resumes from the
 * directory alone.
 */

import { existsSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { ensureDir, nowIso, readJson, today, writeJson } from "./util.ts";

export type Phase =
  | "scope"
  | "panel-research"
  | "coverage-gate"
  | "riff"
  | "report"
  | "complete";

export type Tier = "lite" | "standard" | "deep";

export interface TierSpec {
  researchers: number;
  searchesPerResearcher: number;
  probeAgents: number;
  gapRounds: number;
}

export const TIERS: Record<Tier, TierSpec> = {
  lite: { researchers: 1, searchesPerResearcher: 8, probeAgents: 1, gapRounds: 1 },
  standard: { researchers: 3, searchesPerResearcher: 15, probeAgents: 1, gapRounds: 2 },
  deep: { researchers: 5, searchesPerResearcher: 25, probeAgents: 3, gapRounds: 3 },
};

/** Moderator fires after this many consecutive plain answer turns (Co-STORM L=2). */
export const MODERATOR_L = 2;
/** Consecutive dry probes required for a dimension to count as saturated. */
export const SATURATION_K = 2;
/** A concept tree node reorganizes above this many claims (Co-STORM K=10). */
export const TREE_K = 10;

export interface Manifest {
  session_id: string;
  topic: string;
  created: string;
  updated: string;
  phase: Phase;
  tier: Tier;
  mode: "standard" | "direct";
  moderator_streak: number;
  models: Record<string, string>;
  panel_approved: boolean;
  gate_passed: boolean;
  next_ledger_id: number;
}

export function projectRoot(): string {
  return process.env.RIFF_ROOT ?? process.cwd();
}

export function riffsRoot(): string {
  return join(projectRoot(), ".acos", "riffs");
}

export function sessionDir(sessionId: string): string {
  return join(riffsRoot(), sessionId);
}

export interface Paths {
  root: string;
  manifest: string;
  brief: string;
  coverage: string;
  panel: string;
  charters: string;
  dossiers: string;
  ledger: string;
  tree: string;
  surfaced: string;
  transcript: string;
  report: string;
  questions: string;
}

export function paths(sessionId: string): Paths {
  const root = sessionDir(sessionId);
  return {
    root,
    manifest: join(root, "manifest.json"),
    brief: join(root, "brief.md"),
    coverage: join(root, "coverage.json"),
    panel: join(root, "panel.json"),
    charters: join(root, "charters"),
    dossiers: join(root, "dossiers"),
    ledger: join(root, "ledger.jsonl"),
    tree: join(root, "tree.json"),
    surfaced: join(root, "surfaced.jsonl"),
    transcript: join(root, "transcript.md"),
    report: join(root, "report"),
    questions: join(root, "questions.jsonl"),
  };
}

export function newSessionId(topic: string, slug: string): string {
  return `${today()}-${slug}`;
}

export function loadManifest(sessionId: string): Manifest {
  const p = paths(sessionId);
  if (!existsSync(p.manifest)) {
    throw new Error(`no session at ${p.root} (run: riff init --topic "...")`);
  }
  return readJson<Manifest>(p.manifest, null as unknown as Manifest);
}

export function saveManifest(m: Manifest): void {
  m.updated = nowIso();
  writeJson(paths(m.session_id).manifest, m);
}

export function initSession(topic: string, slug: string, tier: Tier, force = false): Manifest {
  const sessionId = newSessionId(topic, slug);
  const p = paths(sessionId);
  // Session ids are date + slug, so the same question on the same day collides.
  // Silently re-initialising would reset the ledger counter and start emitting
  // ids that already exist in ledger.jsonl — corrupting an append-only file.
  if (existsSync(p.manifest) && !force) {
    throw new Error(
      `session ${sessionId} already exists (phase: ${loadManifest(sessionId).phase}). ` +
        `Continue it with \`riff resume\`, or pass --force to start over.`,
    );
  }
  ensureDir(p.root);
  ensureDir(p.charters);
  ensureDir(p.dossiers);
  ensureDir(p.report);
  const m: Manifest = {
    session_id: sessionId,
    topic,
    created: nowIso(),
    updated: nowIso(),
    phase: "scope",
    tier,
    mode: "standard",
    moderator_streak: 0,
    models: {},
    panel_approved: false,
    gate_passed: false,
    next_ledger_id: 1,
  };
  saveManifest(m);
  return m;
}

function allSessions(): Manifest[] {
  const root = riffsRoot();
  if (!existsSync(root)) return [];
  const out: Manifest[] = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    try {
      const m = loadManifest(entry.name);
      if (m) out.push(m);
    } catch {
      /* skip malformed */
    }
  }
  return out.sort((a, b) => (a.updated < b.updated ? 1 : -1));
}

/** Most recently updated INCOMPLETE session — what "offer to resume" should use. */
export function findResumable(): Manifest | null {
  return allSessions().find((m) => m.phase !== "complete") ?? null;
}

/** Most recently updated session of ANY phase, including completed ones. */
export function findLatest(): Manifest | null {
  return allSessions()[0] ?? null;
}

/**
 * Resolve a session id: explicit flag, else the newest incomplete session, else
 * the newest session of any phase.
 *
 * The last fallback matters. Marking a session `complete` must not make it
 * unreachable — `eval`, `status` and `resume` are exactly the commands you want
 * on a finished session, to review what it concluded and how well it ran.
 */
export function resolveSession(explicit?: string): Manifest {
  if (explicit) return loadManifest(explicit);
  const m = findResumable() ?? findLatest();
  if (!m) throw new Error('no riff session found (run: riff init --topic "...")');
  return m;
}

export function autopilotActive(): boolean {
  return existsSync(join(projectRoot(), ".acos", "state", "autopilot-active"));
}
