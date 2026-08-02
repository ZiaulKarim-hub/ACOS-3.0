/**
 * Session layout + manifest for acos-research-riffs.
 *
 * All durable state lives on disk (design invariant I6) so the conversation
 * holds references, not content, and a cleared session resumes from the
 * directory alone.
 */

import { existsSync, readdirSync, readFileSync, renameSync } from "node:fs";
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
  // A non-Latin or all-punctuation topic slugifies to "", and the degenerate
  // id "<date>-" would collide across UNRELATED topics the same day. Fall back
  // to a short stable hash of the topic: the same topic still resolves to the
  // same id (so init's collision detection keeps working), different topics
  // don't. The substituted slug is visible in the returned session id.
  if (!slug) {
    let h = 5381;
    for (let i = 0; i < topic.length; i++) h = ((h * 33) ^ topic.charCodeAt(i)) >>> 0;
    slug = `topic-${h.toString(36)}`;
  }
  return `${today()}-${slug}`;
}

export function loadManifest(sessionId: string): Manifest {
  const p = paths(sessionId);
  if (!existsSync(p.manifest)) {
    throw new Error(`no session at ${p.root} (run: riff init --topic "...")`);
  }
  // writeJson is a plain non-atomic write and sessions here get hard-killed at
  // token limits, so an empty or truncated manifest is a real crash mode. Fail
  // with a recovery hint rather than letting a null or a SyntaxError surface
  // as a confusing deep TypeError later.
  let m: Manifest | null;
  try {
    m = readJson<Manifest>(p.manifest, null as unknown as Manifest);
  } catch {
    m = null;
  }
  if (!m || !m.session_id) {
    throw new Error(
      `manifest at ${p.manifest} is empty or corrupt — restore it from git or re-init with --force`,
    );
  }
  // A directory shelved by `init --force` still holds a manifest naming the
  // LIVE session. Operating on it would read one directory but WRITE another —
  // saveManifest routes by session_id — clobbering the live manifest with
  // stale phase/gate/ledger-counter state. Refuse the mismatch loudly.
  if (m.session_id !== sessionId) {
    throw new Error(
      `directory ${p.root} holds the manifest of "${m.session_id}" — a superseded or copied ` +
        `session; riff commands cannot operate on archives`,
    );
  }
  return m;
}

export function saveManifest(m: Manifest): void {
  m.updated = nowIso();
  // Routing the write by session_id is safe: loadManifest refuses any
  // directory whose manifest names a different session, so a loaded
  // manifest's id IS the directory it was loaded from.
  writeJson(paths(m.session_id).manifest, m);
}

/**
 * True when `pid` is a live process whose command line contains `marker`
 * (same judgement riff-live makes when arbitrating its lock). EPERM still
 * means alive; an unreadable command line is assumed live — this feeds a
 * refusal gate, which must fail closed.
 */
function pidIsLive(pid: number, marker: string): boolean {
  try {
    process.kill(pid, 0);
  } catch (e) {
    return (e as { code?: string }).code === "EPERM";
  }
  try {
    const cmd = Bun.spawnSync(["ps", "-p", String(pid), "-o", "command="]).stdout.toString("utf8");
    return cmd.includes(marker);
  } catch {
    return true; // cannot verify — assume live
  }
}

/**
 * Pids of daemons still operating out of a session directory: the live
 * responder named by room-live.lock, and any riff-server listening on the
 * port recorded in room.port. Renaming the directory out from under either
 * would strip the single-responder lock and orphan the server.
 */
function liveOwnerPids(root: string): number[] {
  const pids: number[] = [];
  const lock = join(root, "room-live.lock");
  if (existsSync(lock)) {
    try {
      const pid = Number(JSON.parse(readFileSync(lock, "utf8")).pid);
      if (Number.isInteger(pid) && pid > 0 && pidIsLive(pid, "riff-live")) pids.push(pid);
    } catch {
      /* unreadable/empty lock — stale, not an owner */
    }
  }
  const portFile = join(root, "room.port");
  if (existsSync(portFile)) {
    const port = Number(readFileSync(portFile, "utf8").trim());
    if (Number.isInteger(port) && port > 0) {
      try {
        const listeners = Bun.spawnSync(["lsof", "-ti", `tcp:${port}`, "-sTCP:LISTEN"])
          .stdout.toString("utf8");
        for (const line of listeners.split("\n")) {
          const pid = Number(line.trim());
          // Ports get recycled — only count a listener verifiably running
          // riff-server, so a stale room.port never blocks a legitimate force.
          if (Number.isInteger(pid) && pid > 0 && pidIsLive(pid, "riff-server")) pids.push(pid);
        }
      } catch {
        /* lsof unavailable — the lock check above still guards the responder */
      }
    }
  }
  return pids;
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
  // --force must mean a genuinely fresh start: next_ledger_id resets to 1, so
  // the old directory (ledger, claims, coverage, panel, dossiers) cannot be
  // allowed to survive in place — that would append duplicate ledger ids and
  // carry a stale corpus into the "fresh" session. Rename it aside instead of
  // deleting: history stays on disk for forensics, but allSessions() never
  // rediscovers it (loadManifest refuses the id/directory mismatch).
  if (force && existsSync(p.root)) {
    // Never yank the directory out from under running daemons: the rename
    // takes room-live.lock with it, the recreated same-name path is lock-free,
    // and the next `riff room` spawns a SECOND responder while the old one
    // keeps tailing the recreated inbox — double-answering every chair click.
    const owners = liveOwnerPids(p.root);
    if (owners.length > 0) {
      throw new Error(
        `session ${sessionId} is still owned by running daemon(s): pid ${owners.join(", pid ")}. ` +
          `Close the room and stop the live responder (kill those pids), then re-run init --force.`,
      );
    }
    const stamp = nowIso().replace(/:/g, "-");
    let dest = `${p.root}.superseded-${stamp}`;
    for (let n = 2; existsSync(dest); n++) dest = `${p.root}.superseded-${stamp}-${n}`;
    renameSync(p.root, dest);
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
      // loadManifest refuses directories whose manifest names another session
      // (`init --force` shelves), so anything it returns here is live.
      out.push(loadManifest(entry.name));
    } catch {
      /* skip malformed or superseded */
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
 * Resolve a session id: explicit flag, else the most recently updated session —
 * preferring an incomplete one only when it is also the newest overall, so a
 * stale abandoned session never shadows the session just finished.
 *
 * Reaching completed sessions matters. Marking a session `complete` must not
 * make it unreachable — `eval`, `status` and `resume` are exactly the commands
 * you want on a finished session, to review what it concluded and how well it
 * ran.
 */
export function resolveSession(explicit?: string): Manifest {
  if (explicit) return loadManifest(explicit);
  const r = findResumable();
  const l = findLatest();
  const m = r && (!l || r.updated >= l.updated) ? r : l;
  if (!m) throw new Error('no riff session found (run: riff init --topic "...")');
  return m;
}

export function autopilotActive(): boolean {
  return existsSync(join(projectRoot(), ".acos", "state", "autopilot-active"));
}
