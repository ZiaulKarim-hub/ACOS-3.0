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
 * T2 (third review, EXECUTED): the first version of THIS tool was itself
 * defeated. It read fields with a first-match line scan over the whole log, and
 * case sections precede the footer — so a case `run` string carrying escaped
 * newlines injected `post_run_pack_untouched: true` ABOVE the real `false`,
 * the log hash still verified (nothing was edited after sealing; the sealer
 * wrote the forgery itself), and this tool blessed the lie. Fields are now read
 * ONLY from the log's trusted regions (record-format.ts): header fields before
 * the FIRST cases delimiter, footer fields after the LAST footer delimiter.
 * The region between them is candidate-controlled and is never parsed.
 *
 * Checks, per EVB-* bundle under planning/evidence/:
 *   1. manifest.yaml parses and names a raw log that exists.
 *   2. sha256(raw log bytes) === raw_log_sha256.
 *   3. The log carries both trust delimiters.
 *   4. Every duplicated field says the SAME thing in the hashed log's trusted
 *      region and the readable manifest.
 *   5. attempts.log (bundle copy) and the TRACKED anchor at
 *      planning/holdouts/attempts/<id>.log are byte-identical, begin with the
 *      sealed genesis line, chain unbroken, match the sha256 anchor sealed
 *      inside the hashed log, and agree with the sealed attempt number (T3).
 *
 * STATED LIMIT (narrowed by T3, not gone): an insider who deletes an ENTIRE
 * unsealed bundle AND git-restores the tracked anchor to its committed genesis
 * erases pre-seal attempt history. That now takes a git operation on a tracked
 * file plus a deletion; a bare rm no longer does it. Nothing inside a
 * same-user repository can survive deliberate git history surgery.
 *
 * Exit: 0 all records verify (or none exist); 1 any record fails.
 */

import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { sha256Hex } from "./canonical-hash.ts";
import { trustedRegions } from "./record-format.ts";

const EVIDENCE_ROOT = "planning/evidence";
const ATTEMPTS_DIR = "planning/holdouts/attempts";

// X2 (seventh security review): .git/config can carry command-executing keys
// (core.fsmonitor, hooks, askpass) that a hostile case planted — config is out
// of tree and invisible to every check. This tool's own git calls must never
// execute them.
const GIT_SAFE = [
  "-c", "core.hooksPath=/var/empty",
  "-c", "core.fsmonitor=false",
  "-c", "core.askPass=",
  "-c", "credential.helper=",
];

const fieldFrom = (text: string, key: string): string | null => {
  // Function-free line scan; the first match wins, quoted values unquoted.
  // SAFE ONLY on trusted text: a whole manifest (no candidate-controlled
  // content) or a trusted region of the log — never the full log (T2).
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

// Header fields are written before any case runs; footer fields after the last.
const HEADER_FIELDS = ["candidate", "candidate_verified", "attempt"] as const;
const FOOTER_FIELDS = ["post_run_pack_intact", "post_run_tree_clean",
                       "post_run_tree_clean_semantics", "head_unchanged_during_run",
                       "manifest_rewritten_during_run", "post_run_pack_untouched",
                       "post_run_attempts_intact", "attempts_anchor_committed",
                       "post_run_bundle_clean",
                       "attempts_log_sha256"] as const;

/** GENESIS-rooted hash chain; returns problems, never throws. */
function chainProblems(lines: string[], what: string): string[] {
  if (!lines.length || !lines[0].startsWith("sealed ")) {
    return [`${what} does not begin with its sealed genesis line — edited or rebuilt`];
  }
  let prev = "GENESIS";
  for (const [i, line] of lines.entries()) {
    if (!line.includes(`prev=${prev}`)) return [`${what} line ${i + 1} breaks the hash chain — the log was edited`];
    prev = sha256Hex(line);
  }
  return [];
}

function verifyBundle(dir: string): { bad: string[]; note?: string } {
  const bad: string[] = [];
  const manPath = join(dir, "manifest.yaml");
  if (!existsSync(manPath)) {
    // No manifest means no seal. That is LEGITIMATE when the bundle holds only
    // aborted-attempt bookkeeping (attempts.log, maybe a stale lock): reveal
    // writes the attempt line before running and seals only at the end. It is
    // corrupt only if run artifacts exist without their seal.
    const leftovers = readdirSync(dir).filter((f) => f.startsWith("holdout-run-"));
    if (leftovers.length) return { bad: [`run log(s) ${leftovers.join(", ")} exist but the bundle was never sealed — a crashed or truncated seal`] };
    return { bad: [] };   // unsealed attempts-only bundle: nothing to verify yet
  }
  const man = readFileSync(manPath, "utf8");

  const logName = fieldFrom(man, "raw_log");
  if (!logName) return { bad: [`manifest.yaml names no raw_log`] };
  // U2 (fourth review, EXECUTED): a case planted a SECOND holdout-run-*.log in
  // a sealed bundle and this tool said nothing — it only inspected leftovers
  // when the manifest was MISSING. A sealed bundle records exactly one run.
  const runLogs = readdirSync(dir).filter((f) => f.startsWith("holdout-run-")).sort();
  if (runLogs.length !== 1) {
    bad.push(`${runLogs.length} holdout-run-* file(s) exist (${runLogs.join(", ")}) — a sealed bundle records exactly ONE run; extras are planted`);
  } else if (runLogs[0] !== logName) {
    bad.push(`the one run log on disk (${runLogs[0]}) is not the one the manifest names (${logName})`);
  }
  const logPath = join(dir, logName);
  if (!existsSync(logPath)) return { bad: [`raw log ${logName} is MISSING`] };
  const logBytes = readFileSync(logPath);
  const logText = logBytes.toString("utf8");

  const sealedHash = fieldFrom(man, "raw_log_sha256");
  const actualHash = sha256Hex(logBytes);
  if (sealedHash !== actualHash) {
    bad.push(`raw_log_sha256 mismatch — sealed ${sealedHash}, actual ${actualHash}: the log was edited`);
  }

  // T2: fields are read ONLY from the trusted regions. A log without both
  // delimiters is not this format and cannot be verified.
  const regions = trustedRegions(logText);
  if (!regions) {
    bad.push(`the raw log lacks its trust delimiters — pre-T2 format, or a forged log`);
    return { bad };
  }

  // X3 (seventh review): a BRICKED record is the terminal verdict reveal seals
  // when the anchor's commit history shrank under a foreign author. It has no
  // cases, no chain tail and no footer battery — its truth condition is
  // different: both halves must agree it is bricked, and the brick must be
  // REAL: the append-only walk over the live anchor history must fail at the
  // named commit. A "bricked" claim over a healthy history is a forgery.
  if (fieldFrom(man, "bricked") === "true") {
    if (fieldFrom(regions.footer, "bricked") !== "true") {
      bad.push(`manifest says bricked: true but the hashed log's footer does not`);
    }
    for (const key of ["bricked_commit", "bricked_author", ...HEADER_FIELDS] as const) {
      const region = key.startsWith("bricked") ? regions.footer : regions.header;
      const inMan = fieldFrom(man, key);
      const inLog = fieldFrom(region, key);
      if (inMan === null || inLog === null) {
        bad.push(`field ${key} missing from ${inMan === null ? "manifest.yaml" : "the raw log's trusted region"}`);
      } else if (inMan !== inLog) {
        bad.push(`field ${key} DISAGREES — manifest says ${JSON.stringify(inMan)}, hashed log says ${JSON.stringify(inLog)}`);
      }
    }
    const bHoldout = fieldFrom(man, "holdout_id");
    const namedCommit = fieldFrom(man, "bricked_commit") ?? "";
    if (!bHoldout) {
      bad.push(`manifest.yaml names no holdout_id, so the brick cannot be confirmed against the anchor`);
    } else {
      const bAnchor = join(ATTEMPTS_DIR, `${bHoldout}.log`);
      try {
        const commits = execFileSync("git", [...GIT_SAFE, "log", "--full-history", "--format=%H", "--", bAnchor], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] })
          .trim().split("\n").filter(Boolean).reverse();
        let prevBlob = "", shrankAt = "";
        for (const h of commits) {
          let blob = "";
          try { blob = execFileSync("git", [...GIT_SAFE, "show", `${h}:./${bAnchor}`], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }); }
          catch { continue; }
          if (!blob.startsWith(prevBlob)) { shrankAt = h; break; }
          prevBlob = blob;
        }
        if (!shrankAt) bad.push(`record claims BRICKED but the anchor's history walks append-only CLEAN — a forged brick`);
        else if (namedCommit && shrankAt !== namedCommit) bad.push(`record names bricked_commit ${namedCommit.slice(0, 12)} but the walk shrinks at ${shrankAt.slice(0, 12)}`);
      } catch { /* not a repo: a bricked record moved out of its repository is the stated whole-cloth limit */ }
    }
    return { bad, note: "BRICKED BY TAMPERING — terminal verdict, no case ran" };
  }

  // Both halves must tell the same story, field by field.
  for (const [keys, region] of [[HEADER_FIELDS, regions.header], [FOOTER_FIELDS, regions.footer]] as const) {
    for (const key of keys) {
      const inMan = fieldFrom(man, key);
      const inLog = fieldFrom(region, key);
      if (inMan === null || inLog === null) {
        bad.push(`field ${key} missing from ${inMan === null ? "manifest.yaml" : "the raw log's trusted region"}`);
      } else if (inMan !== inLog) {
        bad.push(`field ${key} DISAGREES — manifest says ${JSON.stringify(inMan)}, hashed log says ${JSON.stringify(inLog)}`);
      }
    }
  }
  const manPass = fieldFrom(man, "pass"), manFail = fieldFrom(man, "fail");
  const result = fieldFrom(regions.footer, "result");
  if (result && (manPass === null || manFail === null || !result.startsWith(`${manPass} PASS / ${manFail} FAIL`))) {
    bad.push(`pass/fail counts DISAGREE — manifest ${manPass}/${manFail}, hashed log "${result}"`);
  }

  // The attempts chain: bundle copy, tracked anchor, and the sealed hash (T3).
  const holdoutId = fieldFrom(man, "holdout_id");
  const attemptsPath = join(dir, "attempts.log");
  if (!existsSync(attemptsPath)) {
    bad.push(`attempts.log is MISSING — every reveal writes it before running anything`);
  } else {
    const attemptsRaw = readFileSync(attemptsPath, "utf8");
    const lines = attemptsRaw.split("\n").filter(Boolean);
    bad.push(...chainProblems(lines, "attempts.log"));
    // W2: a SEALED bundle's chain must END with the spent marker, and that
    // marker must name this very record's raw_log_sha256. attempts_log_sha256
    // was sealed inside the log BEFORE the marker existed, so it covers the
    // chain WITHOUT its trailing revealed line.
    const last = lines[lines.length - 1] ?? "";
    if (!last.startsWith("revealed ")) {
      bad.push(`the attempts chain does not end with a "revealed" spent marker — a sealed record without one means the marker was stripped (W2)`);
    } else {
      const sealedLogHash = fieldFrom(man, "raw_log_sha256");
      if (sealedLogHash && !last.includes(`raw_log_sha256=${sealedLogHash}`)) {
        bad.push(`the chain's revealed line names a different raw_log_sha256 than this record — it belongs to another run`);
      }
    }
    const preMarker = lines.filter((l) => !l.startsWith("revealed ")).join("\n") + "\n";
    const sealedAttempts = fieldFrom(regions.footer, "attempts_log_sha256");
    if (sealedAttempts && sealedAttempts !== sha256Hex(preMarker)) {
      bad.push(`attempts.log no longer matches the anchor sealed in the hashed log — lines were added or removed AFTER sealing`);
    }
    const attempt = fieldFrom(regions.header, "attempt");
    const attemptLines = lines.filter((l) => l.startsWith("attempt=")).length;
    if (attempt && Number(attempt) !== attemptLines) {
      bad.push(`sealed attempt number ${attempt} != ${attemptLines} chained attempt line(s)`);
    }
    if (!holdoutId) {
      bad.push(`manifest.yaml names no holdout_id, so the tracked attempts anchor cannot be located`);
    } else {
      const anchorPath = join(ATTEMPTS_DIR, `${holdoutId}.log`);
      if (!existsSync(anchorPath)) {
        bad.push(`the TRACKED attempts anchor ${anchorPath} is MISSING — seal.ts created it; its deletion is the removal of a tracked file`);
      } else if (readFileSync(anchorPath, "utf8") !== attemptsRaw) {
        bad.push(`the tracked anchor ${anchorPath} and the bundle's attempts.log DISAGREE — one was edited or reset`);
      } else {
        // V1: reveal commits every attempt line, so HEAD's copy of the anchor
        // must be a prefix of (or equal to) the working-tree copy. Best effort:
        // silently skipped outside a git repository (fixtures), where the
        // record itself says attempts_anchor_committed: false.
        try {
          const committed = execFileSync("git", [...GIT_SAFE, "show", `HEAD:./${anchorPath}`], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
          if (!readFileSync(anchorPath, "utf8").startsWith(committed)) {
            bad.push(`the anchor on disk is SHORTER than or diverged from HEAD's copy — attempt history was truncated after its commit`);
          }
          // W1: HEAD alone was defeated by a forward commit OF a truncation —
          // the whole history must be append-only, each blob a prefix of the next.
          // X1: --full-history, or TREESAME simplification follows a merge's
          // matching parent and HIDES the growth commits (seventh review, EXECUTED).
          const commits = execFileSync("git", [...GIT_SAFE, "log", "--full-history", "--format=%H", "--", anchorPath], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] })
            .trim().split("\n").filter(Boolean).reverse();
          let prevBlob = "";
          for (const h of commits) {
            let blob = "";
            try { blob = execFileSync("git", [...GIT_SAFE, "show", `${h}:./${anchorPath}`], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }); }
            catch { continue; }
            if (!blob.startsWith(prevBlob)) { bad.push(`anchor commit ${h.slice(0, 12)} SHRANK or rewrote the chain — attempt history is not append-only (W1)`); break; }
            prevBlob = blob;
          }
        } catch { /* not a repo, or anchor never committed: the record's attempts_anchor_committed field carries that fact */ }
      }
    }
  }
  return { bad };
}

function main(): number {
  if (!existsSync(EVIDENCE_ROOT)) { console.log(`verify-run-records: ${EVIDENCE_ROOT} does not exist — 0 records, nothing to check.`); return 0; }
  const bundles = readdirSync(EVIDENCE_ROOT, { withFileTypes: true })
    .filter((e) => e.isDirectory() && e.name.startsWith("EVB-"))
    .map((e) => e.name).sort();
  if (!bundles.length) { console.log("verify-run-records: no EVB-* bundles — nothing to check."); return 0; }
  let badCount = 0;
  for (const b of bundles) {
    const { bad: problems, note } = verifyBundle(join(EVIDENCE_ROOT, b));
    if (problems.length) {
      badCount++;
      console.log(`FAIL  ${b}`);
      for (const p of problems) console.log(`      ${p}`);
    } else {
      console.log(`ok    ${b}${note ? `  [${note}]` : ""}`);
    }
  }
  console.log(`\n${bundles.length - badCount} ok / ${badCount} bad of ${bundles.length} run record(s).`);
  return badCount ? 1 : 0;
}

process.exit(main());
