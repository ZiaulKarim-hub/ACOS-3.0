#!/usr/bin/env bun
/**
 * fingerprint-build.ts — build audit/dirty-fingerprint.json for a cleanroom session.
 *
 * The egress guard reads this file to decide whether an outgoing payload leaks
 * dirty-room content. Run it at the END of Phase 0 (capture) and again after
 * Phase 1 (intent) so the fingerprint covers every dirty artifact. Re-run after
 * the spec-wall writes 02-wall/spec-clean.md so its hash lands in allow_hashes.
 *
 * Usage:  bun fingerprint-build.ts <session-dir> [--shingle 8] [--max 3]
 *
 * It scans 00-capture/ and 01-intent/ for text, builds word-shingles, folds in
 * the wall's forbidden-token list (02-wall/forbidden-tokens.txt if present), and
 * records the sha256 of 02-wall/spec-clean.md as the sole egress-allowed hash.
 */

import { readFileSync, writeFileSync, existsSync, readdirSync, statSync, mkdirSync } from "node:fs";
import { join, extname } from "node:path";
import { shingles, sha256, type DirtyFingerprint } from "./lib/fingerprint.ts";
import { scanSecretsPII, chunkShingles, type Finding } from "./lib/scan.ts";

const TEXT_EXT = new Set([".md", ".txt", ".json", ".yaml", ".yml", ".html", ".htm", ".js", ".ts", ".css", ".har", ".csv", ".xml"]);

function walk(dir: string, out: string[] = []): string[] {
  if (!existsSync(dir)) return out;
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    const s = statSync(p);
    if (s.isDirectory()) walk(p, out);
    else if (TEXT_EXT.has(extname(p).toLowerCase()) && s.size < 5_000_000) out.push(p);
  }
  return out;
}

function main() {
  const args = process.argv.slice(2);
  const sessionDir = args[0];
  if (!sessionDir) {
    console.error("usage: bun fingerprint-build.ts <session-dir> [--shingle 8] [--max 3]");
    process.exit(1);
  }
  const k = Number(args[args.indexOf("--shingle") + 1]) || 8;
  const max = Number(args[args.indexOf("--max") + 1]) || 3;
  // Robustness gates (references/capture-layers.md 0.5): a second secret/PII scan and
  // multi-granularity (chunk-level) fingerprints to catch partial leaks.
  const secretScan = args.includes("--secret-scan");
  const multiGranularity = args.includes("--multigranularity");

  const sessionId = sessionDir.replace(/\/+$/, "").split("/").pop() || "unknown";
  const dirtyDirs = [join(sessionDir, "00-capture"), join(sessionDir, "01-intent")];

  const shingleSet = new Set<string>();
  const chunkSet = new Set<string>();
  const secretFindings: (Finding & { file: string })[] = [];
  for (const d of dirtyDirs) {
    for (const f of walk(d)) {
      try {
        const txt = readFileSync(f, "utf8");
        for (const sh of shingles(txt, k)) shingleSet.add(sh);
        if (multiGranularity) for (const c of chunkShingles(txt)) chunkSet.add(c);
        if (secretScan) for (const hit of scanSecretsPII(txt)) secretFindings.push({ ...hit, file: f });
      } catch { /* skip unreadable */ }
    }
  }

  // Forbidden tokens: one per line, written by the spec-wall (rc-spec-wall).
  const forbidden: string[] = [];
  const forbiddenPath = join(sessionDir, "02-wall", "forbidden-tokens.txt");
  if (existsSync(forbiddenPath)) {
    for (const line of readFileSync(forbiddenPath, "utf8").split("\n")) {
      const t = line.trim();
      if (t && !t.startsWith("#")) forbidden.push(t);
    }
  }
  // --secret-scan: every scanned secret/PII token is ALSO armed as a forbidden token, so a
  // leaked key/email is denied even if the wall's token list missed it. De-duplicate.
  if (secretScan) {
    const already = new Set(forbidden);
    for (const hit of secretFindings) {
      if (hit.token.length >= 3 && !already.has(hit.token)) {
        forbidden.push(hit.token);
        already.add(hit.token);
      }
    }
  }

  // The ONLY content cleared to leave: the post-wall clean spec.
  const allow_hashes: string[] = [];
  const cleanSpec = join(sessionDir, "02-wall", "spec-clean.md");
  if (existsSync(cleanSpec)) {
    const content = readFileSync(cleanSpec, "utf8");
    // Store the hash of both the raw content and a JSON-wrapped form, since the
    // guard hashes JSON.stringify(tool_input) — the orchestrator passes the
    // clean spec as a tool_input string.
    allow_hashes.push(sha256(content));
    allow_hashes.push(sha256(JSON.stringify({ content })));
  }

  const fp: DirtyFingerprint & { max_shared_shingles: number; built_at_note: string } = {
    version: "1.0.0",
    session_id: sessionId,
    shingle_words: k,
    shingles: [...shingleSet],
    forbidden_tokens: forbidden,
    allow_hashes,
    max_shared_shingles: max,
    ...(multiGranularity ? { chunk_shingles: [...chunkSet] } : {}),
    built_at_note: "timestamp intentionally omitted — set by orchestrator, not this script",
  };

  const auditDir = join(sessionDir, "audit");
  if (!existsSync(auditDir)) mkdirSync(auditDir, { recursive: true });
  const outPath = join(auditDir, "dirty-fingerprint.json");
  writeFileSync(outPath, JSON.stringify(fp, null, 2));

  // --secret-scan: emit the masked audit report (raw tokens live only in the fingerprint's
  // forbidden list, which never egresses; the report is safe to keep in audit/).
  if (secretScan) {
    const byType: Record<string, number> = {};
    for (const h of secretFindings) byType[h.type] = (byType[h.type] ?? 0) + 1;
    const report = {
      session_id: sessionId,
      total: secretFindings.length,
      by_type: byType,
      findings: secretFindings.map((h) => ({ type: h.type, masked: h.masked, file: h.file, index: h.index })),
    };
    writeFileSync(join(auditDir, "secret-pii-scan.json"), JSON.stringify(report, null, 2));
  }

  console.log(
    `dirty-fingerprint.json written: ${shingleSet.size} shingles` +
      (multiGranularity ? `, ${chunkSet.size} chunk-shingles` : "") +
      `, ${forbidden.length} forbidden tokens` +
      (secretScan ? ` (incl. ${secretFindings.length} scanned secret/PII)` : "") +
      `, ${allow_hashes.length} allow-hashes → ${outPath}`,
  );
}

main();
