#!/usr/bin/env bun
/**
 * cleanroom egress guard — PreToolUse hook (fail-CLOSED within a cleanroom session).
 *
 * Purpose: mechanically enforce the clean-room wall. When a reverse-cleanroom
 * session is ACTIVE, no dirty-room content (the original app's code, names,
 * secrets, or extracted text) may leave the machine via an external model call,
 * WebFetch, or a network Bash command. Only the post-wall clean spec may egress.
 *
 * Contract (Claude Code PreToolUse hook):
 *   stdin  : JSON { tool_name, tool_input, cwd, ... }
 *   stdout : "allow" | "deny: <reason>"   (also sets exit code)
 *   exit 0 : allow    exit 2 : deny (block the tool call)
 *
 * Activation: only fires when .acos/cleanroom/<current>/ACTIVE exists AND that
 * session's egress.enforce is true. Outside a cleanroom session it ALLOWS
 * everything (this hook is a no-op for all other ACOS work).
 *
 * Fail posture: INSIDE an active session it fails CLOSED — if the fingerprint
 * is unreadable or the payload can't be parsed, it DENIES. This is the opposite
 * of the Oracle (which is fail-open), and is intentional: a leak is worse than
 * a blocked call the user can re-run after clearing the wall.
 *
 * Run via bun (no build step). Registered as a PreToolUse hook only while a
 * cleanroom session is active — see references/egress-and-cleanroom.md.
 */

import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import {
  type DirtyFingerprint,
  sha256,
  sharedShingleCount,
  sharedChunkCount,
  forbiddenHits,
} from "./lib/fingerprint.ts";

const EXTERNAL_TOOLS = /^(WebFetch|WebSearch|mcp__)/;
// Bash commands that move bytes off-box. Conservative allowlist-by-denylist.
const NET_BASH = /\b(curl|wget|nc|ncat|scp|rsync|ssh|http|https|run-external-agent|openai|gemini|glm|kimi|deepseek|openrouter)\b/i;

/** Recursively collect every string leaf value from a tool_input object (paragraph-preserving). */
function collectStrings(v: unknown, out: string[] = []): string[] {
  if (typeof v === "string") out.push(v);
  else if (Array.isArray(v)) for (const x of v) collectStrings(x, out);
  else if (v && typeof v === "object") for (const x of Object.values(v)) collectStrings(x, out);
  return out;
}

function out(decision: "allow" | "deny", reason = ""): never {
  if (decision === "allow") {
    process.stdout.write("allow");
    process.exit(0);
  }
  process.stdout.write(`deny: ${reason}`);
  process.exit(2);
}

function readStdin(): string {
  try {
    return readFileSync(0, "utf8");
  } catch {
    return "";
  }
}

function findActiveSession(cwd: string): string | null {
  // Look for .acos/cleanroom/*/ACTIVE nearest to cwd.
  const base = join(cwd, ".acos", "cleanroom");
  if (!existsSync(base)) return null;
  try {
    const { readdirSync } = require("node:fs");
    for (const sid of readdirSync(base)) {
      if (existsSync(join(base, sid, "ACTIVE"))) return join(base, sid);
    }
  } catch {
    /* fall through */
  }
  return null;
}

function main(): void {
  const raw = readStdin();
  let evt: any = {};
  try {
    evt = JSON.parse(raw || "{}");
  } catch {
    // Can't parse the event. Outside a session we allow; but we don't yet know
    // the session. Resolve cwd defensively from env, then decide.
    evt = {};
  }

  const cwd: string = evt.cwd || process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const sessionDir = findActiveSession(cwd);

  // Not in a cleanroom session → this hook is a no-op.
  if (!sessionDir) out("allow");

  // From here we are INSIDE an active session → fail CLOSED on any doubt.
  const toolName: string = evt.tool_name || "";
  const toolInput = evt.tool_input ?? {};
  const payload = JSON.stringify(toolInput);

  // Is this an egress-capable tool call?
  const isExternalTool = EXTERNAL_TOOLS.test(toolName);
  const isNetBash =
    toolName === "Bash" && NET_BASH.test(String(toolInput.command || ""));
  if (!isExternalTool && !isNetBash) out("allow"); // local tool → fine

  // Load the dirty-room fingerprint. Missing/broken → fail closed.
  const fpPath = join(sessionDir!, "audit", "dirty-fingerprint.json");
  if (!existsSync(fpPath)) {
    out("deny", `cleanroom active but no dirty-fingerprint.json — egress blocked (fail-closed). Session: ${sessionDir}`);
  }
  let fp: DirtyFingerprint;
  try {
    fp = JSON.parse(readFileSync(fpPath, "utf8")) as DirtyFingerprint;
  } catch (e) {
    out("deny", `dirty-fingerprint.json unreadable — egress blocked (fail-closed): ${String(e)}`);
  }

  // If the payload is exactly (a reference to) the cleared clean-spec, allow.
  // The clean spec's own hash is in allow_hashes; sending its content is fine.
  const payloadHash = sha256(payload);
  if (fp!.allow_hashes?.includes(payloadHash)) out("allow");

  // 1) Verbatim forbidden-token check (secrets, identifiers, tech nouns, entities).
  const hits = forbiddenHits(payload, fp!);
  if (hits.length > 0) {
    out(
      "deny",
      `dirty-room forbidden token(s) in outgoing payload: ${hits.slice(0, 5).join(", ")}${hits.length > 5 ? " …" : ""}. Route through the spec-wall (Phase 2) first.`,
    );
  }

  // 2) Shingle-overlap check (bulk dirty-room text leaking into the payload).
  const shared = sharedShingleCount(payload, fp!);
  const max = (fp as any).max_shared_shingles ?? 3;
  if (shared > max) {
    out(
      "deny",
      `outgoing payload overlaps dirty-room text (${shared} shared 8-word shingles > ${max}). Only 02-wall/spec-clean.md may egress.`,
    );
  }

  // 3) Chunk-overlap check (ONLY if the fingerprint carries multi-granularity chunk
  // hashes). Runs against the raw string FIELD VALUES (paragraph boundaries preserved),
  // not the JSON-encoded payload — so a single pasted dirty PARAGRAPH in any field is
  // caught even when it is too short to trip the 8-word shingle overlap. Absent
  // chunk_shingles → sharedChunkCount returns 0 → this check is a no-op (back-compat).
  const rawFieldText = collectStrings(toolInput).join("\n\n");
  const chunkHits = sharedChunkCount(rawFieldText, fp!);
  if (chunkHits > 0) {
    out(
      "deny",
      `outgoing payload contains ${chunkHits} verbatim dirty-room paragraph(s). Route through the spec-wall (Phase 2) first.`,
    );
  }

  out("allow");
}

main();
