/**
 * Shared utilities for the acos-research-riffs CLI.
 * Runtime: bun (TypeScript, no build step). Zero external dependencies.
 */

import {
  mkdirSync,
  readFileSync,
  writeFileSync,
  appendFileSync,
  existsSync,
  renameSync,
} from "node:fs";
import { dirname } from "node:path";

export function nowIso(): string {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

export function today(): string {
  return new Date().toISOString().slice(0, 10);
}

export function slugify(s: string): string {
  return s
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60);
}

export function ensureDir(path: string): void {
  mkdirSync(path, { recursive: true });
}

export function writeFileEnsured(path: string, content: string): void {
  ensureDir(dirname(path));
  writeFileSync(path, content, "utf8");
}

export function appendLine(path: string, line: string): void {
  ensureDir(dirname(path));
  appendFileSync(path, line.replace(/\n/g, " ") + "\n", "utf8");
}

export function readJson<T>(path: string, fallback: T): T {
  if (!existsSync(path)) return fallback;
  const raw = readFileSync(path, "utf8").trim();
  if (!raw) return fallback;
  return JSON.parse(raw) as T;
}

export function writeJson(path: string, value: unknown): void {
  // Atomic: write a tmp sibling, then rename over the target. Sessions get
  // hard-killed at token limits and the room server re-reads these files every
  // tick — a torn manifest/coverage/panel/tree file must never be observable.
  ensureDir(dirname(path));
  const tmp = `${path}.tmp-${process.pid}`;
  writeFileSync(tmp, JSON.stringify(value, null, 2) + "\n", "utf8");
  renameSync(tmp, path);
}

export function readJsonl<T>(path: string): T[] {
  return readJsonlStrict<T>(path).rows;
}

export interface JsonlRead<T> {
  rows: T[];
  /** 1-based line numbers of malformed lines that were skipped (trailing torn line excluded). */
  dropped: number[];
}

/**
 * JSONL read that REPORTS malformed lines instead of hiding them. A partial
 * trailing line with no newline after it (a write torn mid-append) is tolerated
 * silently; any other unparseable line lands in `dropped` so callers guarding
 * an evidence trail (the ledger) can surface the loss instead of losing it
 * quietly.
 */
export function readJsonlStrict<T>(path: string): JsonlRead<T> {
  if (!existsSync(path)) return { rows: [], dropped: [] };
  const raw = readFileSync(path, "utf8");
  const torn = !raw.endsWith("\n"); // last line may be a mid-append fragment
  const lines = raw.split("\n");
  const rows: T[] = [];
  const dropped: number[] = [];
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i]!.trim();
    if (!l) continue;
    try {
      rows.push(JSON.parse(l) as T);
    } catch {
      if (!(torn && i === lines.length - 1)) dropped.push(i + 1);
    }
  }
  return { rows, dropped };
}

export function appendJsonl(path: string, value: unknown): void {
  appendLine(path, JSON.stringify(value));
}

/** Read a JSON payload from --json <file>, --stdin, or an inline --data '<json>'. */
export function readPayload(args: Args): unknown {
  if (args.flags["json"]) {
    return JSON.parse(readFileSync(args.flags["json"], "utf8"));
  }
  if (args.flags["data"]) {
    return JSON.parse(args.flags["data"]);
  }
  if (args.bools.has("stdin")) {
    return JSON.parse(readFileSync(0, "utf8"));
  }
  throw new Error("no payload: pass --json <file>, --data '<json>', or --stdin");
}

// ---------------------------------------------------------------------------
// Lexical scoring (dependency-free retrieval; optional LanceDB upgrade later)
// ---------------------------------------------------------------------------

const STOP = new Set(
  ("a an and are as at be but by for from has have how i if in into is it its of on or that the " +
    "their there these they this to was were what when where which who why will with you your do does " +
    "can could should would about over under between across we our us not no yes than then them " +
    "so up my me he")
    .split(" "),
);
// Deliberately NOT stopped: "go" (the language — often the discriminating
// token on exactly the tech topics this skill researches) and "am" (keeps
// am/pm symmetric in time-of-day claims).

export function tokenize(text: string): string[] {
  // length > 1 keeps two-char domain terms (AI, EU, 5G, ML) — often the most
  // discriminating tokens on the topics this skill researches; the two-letter
  // function words are handled by STOP instead. Trailing '.', '-', '_' are
  // stripped so sentence-final "latency." matches "latency" — internal ones
  // survive for node.js / api.z.ai, and trailing '+' is kept for C++.
  return (text.toLowerCase().match(/[a-z0-9][a-z0-9+._-]*/g) ?? [])
    .map((t) => t.replace(/[._-]+$/, ""))
    .filter((t) => t.length > 1 && !STOP.has(t));
}

export function termFreq(text: string): Map<string, number> {
  const tf = new Map<string, number>();
  for (const t of tokenize(text)) tf.set(t, (tf.get(t) ?? 0) + 1);
  return tf;
}

/** Cosine similarity over raw term-frequency vectors. Range 0..1. */
export function cosine(a: Map<string, number>, b: Map<string, number>): number {
  let dot = 0;
  let na = 0;
  let nb = 0;
  for (const [, v] of a) na += v * v;
  for (const [k, v] of b) {
    nb += v * v;
    const av = a.get(k);
    if (av) dot += av * v;
  }
  if (na === 0 || nb === 0) return 0;
  return dot / (Math.sqrt(na) * Math.sqrt(nb));
}

export function similarity(a: string, b: string): number {
  return cosine(termFreq(a), termFreq(b));
}

// ---------------------------------------------------------------------------
// Arg parsing
// ---------------------------------------------------------------------------

export interface Args {
  positional: string[];
  flags: Record<string, string>;
  bools: Set<string>;
}

export function parseArgs(argv: string[]): Args {
  const positional: string[] = [];
  const flags: Record<string, string> = {};
  const bools = new Set<string>();
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]!;
    if (a.startsWith("--")) {
      const name = a.slice(2);
      // Support --flag=value alongside --flag value.
      const eq = name.indexOf("=");
      if (eq > 0) {
        flags[name.slice(0, eq)] = name.slice(eq + 1);
        continue;
      }
      const next = argv[i + 1];
      if (next !== undefined && !next.startsWith("--")) {
        flags[name] = next;
        i++;
      } else {
        bools.add(name);
      }
    } else {
      positional.push(a);
    }
  }
  return { positional, flags, bools };
}

export function fail(msg: string): never {
  console.error(`riff: ${msg}`);
  process.exit(1);
}

export function requireFlag(args: Args, name: string): string {
  const v = args.flags[name];
  if (!v) fail(`missing required --${name}`);
  return v;
}
