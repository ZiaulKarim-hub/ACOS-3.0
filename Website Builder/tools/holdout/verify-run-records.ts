#!/usr/bin/env bun
/**
 * verify-run-records.ts — re-check every sealed holdout RUN RECORD.
 *
 * WHY (security re-review S2, EXECUTED): the run record's integrity fields used
 * to live only in the bundle's manifest.yaml — outside the one hash — and
 * flipping `candidate_verified: false` to `true` with sed left `raw_log_sha256`
 * identical, because nothing ever verified a run record after it was written.
 * reveal.ts now writes every integrity fact into the RAW LOG (which is hashed)
 * as well; this tool is the other half: it re-derives everything derivable and
 * refuses records whose two halves disagree.
 *
 * Checks, per EVB-* bundle under planning/evidence/:
 *   1. manifest.yaml parses and names a raw log that exists.
 *   2. sha256(raw log bytes) === raw_log_sha256.
 *   3. Every duplicated field (candidate, candidate_verified, attempt, pass/fail
 *      counts, post_run_*, manifest_rewritten_during_run, attempts_log_sha256)
 *      says the SAME thing in the hashed log and the readable manifest.
 *   4. attempts.log exists, its hash chain is unbroken, and its sha256 matches
 *      the anchor sealed inside the hashed log.
 *
 * STATED LIMIT (same boundary as the lock file's): an insider who deletes an
 * ENTIRE bundle directory before sealing leaves nothing for this tool to check.
 * Tamper-evidence covers what survives; nothing inside the repository can prove
 * a directory never existed.
 *
 * Exit: 0 all records verify (or none exist); 1 any record fails.
 */

import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { sha256Hex } from "./canonical-hash.ts";

const EVIDENCE_ROOT = "planning/evidence";

const fieldFrom = (text: string, key: string): string | null => {
  // Function-free line scan; the first match wins, quoted values unquoted.
  for (const line of text.split("\n")) {
    if (line.startsWith(`${key}:`)) {
      let v = line.slice(key.length + 1).trim();
      const hash = v.indexOf(" #");
      if (hash >= 0) v = v.slice(0, hash).trim();
      if (v.startsWith('"') && v.endsWith('"')) v = v.slice(1, -1);
      return v;
    }
  }
  return null;
};

function verifyBundle(dir: string): string[] {
  const bad: string[] = [];
  const manPath = join(dir, "manifest.yaml");
  if (!existsSync(manPath)) {
    // No manifest means no seal. That is LEGITIMATE when the bundle holds only
    // aborted-attempt bookkeeping (attempts.log, maybe a stale lock): reveal
    // writes the attempt line before running and seals only at the end. It is
    // corrupt only if run artifacts exist without their seal.
    const leftovers = readdirSync(dir).filter((f) => f.startsWith("holdout-run-"));
    if (leftovers.length) return [`run log(s) ${leftovers.join(", ")} exist but the bundle was never sealed — a crashed or truncated seal`];
    return [];   // unsealed attempts-only bundle: nothing to verify yet
  }
  const man = readFileSync(manPath, "utf8");

  const logName = fieldFrom(man, "raw_log");
  if (!logName) return [`manifest.yaml names no raw_log`];
  const logPath = join(dir, logName);
  if (!existsSync(logPath)) return [`raw log ${logName} is MISSING`];
  const logBytes = readFileSync(logPath);
  const logText = logBytes.toString("utf8");

  const sealedHash = fieldFrom(man, "raw_log_sha256");
  const actualHash = sha256Hex(logBytes);
  if (sealedHash !== actualHash) {
    bad.push(`raw_log_sha256 mismatch — sealed ${sealedHash}, actual ${actualHash}: the log was edited`);
  }

  // Both halves must tell the same story, field by field.
  for (const key of ["candidate", "candidate_verified", "attempt",
                     "post_run_pack_intact", "post_run_tree_clean",
                     "manifest_rewritten_during_run", "post_run_pack_untouched",
                     "attempts_log_sha256"]) {
    const inMan = fieldFrom(man, key);
    const inLog = fieldFrom(logText, key);
    if (inMan === null || inLog === null) {
      bad.push(`field ${key} missing from ${inMan === null ? "manifest.yaml" : "the raw log"}`);
    } else if (inMan !== inLog) {
      bad.push(`field ${key} DISAGREES — manifest says ${JSON.stringify(inMan)}, hashed log says ${JSON.stringify(inLog)}`);
    }
  }
  const manPass = fieldFrom(man, "pass"), manFail = fieldFrom(man, "fail");
  const result = fieldFrom(logText, "result");
  if (result && (manPass === null || manFail === null || !result.startsWith(`${manPass} PASS / ${manFail} FAIL`))) {
    bad.push(`pass/fail counts DISAGREE — manifest ${manPass}/${manFail}, hashed log "${result}"`);
  }

  // The attempts chain, and its anchor inside the hashed log.
  const attemptsPath = join(dir, "attempts.log");
  if (!existsSync(attemptsPath)) {
    bad.push(`attempts.log is MISSING — every reveal writes it before running anything`);
  } else {
    const attemptsRaw = readFileSync(attemptsPath, "utf8");
    const lines = attemptsRaw.split("\n").filter(Boolean);
    let prev = "GENESIS";
    for (const [i, line] of lines.entries()) {
      if (!line.includes(`prev=${prev}`)) { bad.push(`attempts.log line ${i + 1} breaks the hash chain — the log was edited`); break; }
      prev = sha256Hex(line);
    }
    const sealedAttempts = fieldFrom(logText, "attempts_log_sha256");
    if (sealedAttempts && sealedAttempts !== sha256Hex(attemptsRaw)) {
      bad.push(`attempts.log no longer matches the anchor sealed in the hashed log — lines were added or removed AFTER sealing`);
    }
    const attempt = fieldFrom(logText, "attempt");
    if (attempt && Number(attempt) !== lines.length) {
      bad.push(`sealed attempt number ${attempt} != ${lines.length} chained line(s)`);
    }
  }
  return bad;
}

function main(): number {
  if (!existsSync(EVIDENCE_ROOT)) { console.log(`verify-run-records: ${EVIDENCE_ROOT} does not exist — 0 records, nothing to check.`); return 0; }
  const bundles = readdirSync(EVIDENCE_ROOT, { withFileTypes: true })
    .filter((e) => e.isDirectory() && e.name.startsWith("EVB-"))
    .map((e) => e.name).sort();
  if (!bundles.length) { console.log("verify-run-records: no EVB-* bundles — nothing to check."); return 0; }
  let badCount = 0;
  for (const b of bundles) {
    const problems = verifyBundle(join(EVIDENCE_ROOT, b));
    if (problems.length) {
      badCount++;
      console.log(`FAIL  ${b}`);
      for (const p of problems) console.log(`      ${p}`);
    } else {
      console.log(`ok    ${b}`);
    }
  }
  console.log(`\n${bundles.length - badCount} ok / ${badCount} bad of ${bundles.length} run record(s).`);
  return badCount ? 1 : 0;
}

process.exit(main());
