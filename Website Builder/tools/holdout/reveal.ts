#!/usr/bin/env bun
/**
 * reveal.ts — open a sealed holdout pack, run it ONCE, seal the result.
 *
 * This is the command R2P calls `qa:holdout`. There, it is 41 lines of
 * scaffolding whose own output reads "no holdout run-record verification is
 * implemented yet in this scaffolding slice — nothing sealed." This is that
 * command actually built (PRD §22, slice S79).
 *
 * CONTEXT GATE. Refuses unless WB_QA_CONTEXT=1. The value of a holdout is
 * destroyed the moment the implementing context can read the cases, and an
 * environment check is the cheapest available fence around that. It is a fence,
 * not a wall: it stops the accident, not a determined reader.
 *
 * A REVEALED PACK IS SPENT (PRD §22, O43). Revealing sets `revealed_at`, and a
 * manifest that already carries one is refused. If the code then needs fixing,
 * that needs a NEW pack at v<n+1>, authored by the custodian, and the failed run
 * stays in the record. A pack that can be re-run until it passes is homework,
 * not an exam.
 *
 * Usage:
 *   WB_QA_CONTEXT=1 bun tools/holdout/reveal.ts --id HLD-S41-v1 --candidate <sha>
 *   [--dry-run]   verify hashes and print the plan; run nothing, seal nothing.
 */

import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, renameSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { duplicateJsonKeys } from "./json-keys.ts";
import { canonicalPackHash, expectedResultsHash, sha256Hex } from "./canonical-hash.ts";
import { parse, validate, type HoldoutManifest } from "./manifest.ts";

const MANIFEST_DIR = "planning/holdouts/manifests";
const PACK_ROOT = "qa-private";
const EVIDENCE_ROOT = "planning/evidence";

interface Case { id: string; class: string; description?: string; run: string }

/**
 * Per-case harness limits.
 *
 * These are NOT pass/fail criteria — they bound the harness so it cannot
 * misreport. A case that trips either one aborts the whole reveal WITHOUT
 * sealing, because a holdout pack is a one-shot exam: recording a harness
 * limit as a case failure would burn the pack on a bug in this file.
 */
const CASE_MAX_BUFFER = 64 * 1024 * 1024;   // 64 MiB, vs the 1 MiB default
const CASE_TIMEOUT_MS = Number(process.env.WB_HOLDOUT_CASE_TIMEOUT_MS ?? 120_000);
interface Expected { exit: number; stdout_sha256?: string; stdout_contains?: string }

const arg = (n: string): string | null => {
  const i = process.argv.indexOf(n);
  return i >= 0 ? process.argv[i + 1] ?? null : null;
};
const has = (n: string) => process.argv.includes(n);
const die = (msg: string): never => { console.error(msg); process.exit(1); };

function main(): number {
  if (process.env.WB_QA_CONTEXT !== "1") {
    die(
      "reveal refused: this command is available only in the QA review context (PRD §22.1).\n" +
      "Set WB_QA_CONTEXT=1 and run it from a separate QA worktree or session — never from the\n" +
      "implementation agent's own context, whose whole purpose is not to have seen these cases.",
    );
  }

  const id = arg("--id") ?? die("reveal refused: --id <HLD-...> is required.");
  const candidate = arg("--candidate") ?? die("reveal refused: --candidate <commit-sha> is required.\nA pack is run against a NAMED FROZEN candidate, or the result cannot be attributed to anything.");
  const dryRun = has("--dry-run");

  // ---- the manifest -------------------------------------------------------
  const mPath = join(MANIFEST_DIR, `${id}.yaml`);
  if (!existsSync(mPath)) die(`reveal refused: no manifest at ${mPath}`);
  const parsed = parse(readFileSync(mPath, "utf8"));
  if (!parsed.ok) die(`reveal refused: ${mPath} does not parse — ${parsed.error}`);
  const problems = validate(parsed.value);
  if (problems.length) {
    die(`reveal refused: ${mPath} is invalid —\n` + problems.map((p) => `    ${p.field}: ${p.message}`).join("\n"));
  }
  const man = parsed.value as HoldoutManifest;

  if (man.revealed_at !== null) {
    die(
      `reveal refused: ${id} was already revealed at ${man.revealed_at}.\n` +
      `A revealed pack is SPENT. Fixing the code needs a NEW pack at the next version,\n` +
      `authored by the custodian; the earlier run stays in the record exactly as produced.`,
    );
  }

  // ---- the pack, and its seal --------------------------------------------
  const packDir = join(PACK_ROOT, id);
  if (!existsSync(packDir)) {
    die(
      `reveal refused: no pack at ${packDir}.\n` +
      `The pack is withheld from the implementation worktree by design — run this from the\n` +
      `QA worktree or the withheld archive where ${PACK_ROOT}/ actually exists (PRD §22.5).`,
    );
  }

  const { digest, files } = canonicalPackHash(packDir);
  const expDigest = expectedResultsHash(packDir);
  const packOk = digest === man.private_pack_sha256;
  const expOk = expDigest === man.expected_results_sha256;

  console.log(`pack     ${packDir}  (${files.length} file(s): ${files.join(", ")})`);
  console.log(`method   ${man.hash_method}`);
  console.log(`pack     ${packOk ? "MATCH" : "MISMATCH"}  computed ${digest}\n                    manifest ${man.private_pack_sha256}`);
  console.log(`expected ${expOk ? "MATCH" : "MISMATCH"}  computed ${expDigest}\n                    manifest ${man.expected_results_sha256}`);

  if (!packOk || !expOk) {
    die(
      `\nreveal refused: hash mismatch. NOTHING WAS RUN.\n` +
      `Both hashes were published before the code existed, so a mismatch means the sealed\n` +
      `content moved. This tool computes them one way only (${man.hash_method}), so a mismatch\n` +
      `here is not the "which recipe did the custodian use?" problem that made R2P's HASHING.md\n` +
      `922 lines long — it is a real difference in the pack.`,
    );
  }

  // ---- the candidate must genuinely be frozen -----------------------------
  // "Not a git repository" and "a git repository whose HEAD does not resolve" are
  // DIFFERENT states, and lumping them together was exploitable. MEASURED: `git init`
  // with no commit and a `.git/info/exclude` of "*" gives a tree that is CLEAN
  // (`git status --porcelain` empty) while HEAD cannot resolve. The old single catch
  // then printed "not a git repository", skipped the attribution check, and SEALED
  // the pack against the candidate "totally-made-up-not-a-commit" — the exact failure
  // the check exists to prevent, surviving in one untested state.
  let dirty = "", headSha = "", inRepo = false;
  try {
    execFileSync("git", ["rev-parse", "--git-dir"], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
    inRepo = true;
  } catch { /* genuinely outside a repository */ }

  if (!inRepo) {
    console.log("note: not a git repository — the frozen-candidate check is recorded as UNVERIFIED.");
  } else {
    dirty = execFileSync("git", ["status", "--porcelain"], { encoding: "utf8" }).trim();
    try {
      headSha = execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
    } catch {
      die(
        `reveal refused: this IS a git repository, but HEAD does not resolve to a commit.\n` +
        `That happens before the first commit, or on an unborn branch. There is nothing to\n` +
        `attribute the result to, and falling back to UNVERIFIED here would let any string\n` +
        `be sealed as the candidate. Commit the frozen candidate first, then reveal.`,
      );
    }
  }

  // A clean tree only proves nothing is UNCOMMITTED. It says nothing about WHICH
  // commit is checked out, so --candidate was previously an unverified label: any
  // string was accepted and written into the evidence as the thing that ran. The
  // whole purpose of naming a candidate is attribution, so the name must match.
  if (headSha) {
    const c = candidate.trim().toLowerCase(), h = headSha.toLowerCase();
    if (c.length < 7 || !h.startsWith(c)) {
      die(
        `reveal refused: --candidate "${candidate}" does not name the commit that is checked out.\n` +
        `HEAD is ${headSha}. Give that sha, or at least its first 7+ characters.\n` +
        `A result attributed to a commit that did not run it is worse than no result.`,
      );
    }
  }
  if (dirty) {
    die(
      `reveal refused: the working tree is dirty, so "${candidate}" is not a frozen candidate.\n` +
      `A holdout result is only attributable to a commit if that commit is what ran.`,
    );
  }

  // ---- the run record must never be overwritten -----------------------------
  // seal.ts refuses to overwrite an existing manifest; reveal.ts did not, so a
  // second reveal of the same id silently replaced the first run's record while
  // that record's own comment claimed it was "Preserved AS PRODUCED". The
  // revealed_at stamp is the primary guard, but it lives in an editable file —
  // this is the defence in depth for a cleared, restored or double-invoked run.
  // Checked BEFORE any case runs, so a refusal costs nothing.
  const bundleDirEarly = join(EVIDENCE_ROOT, `EVB-${id}`);
  if (existsSync(join(bundleDirEarly, "manifest.yaml"))) {
    die(
      `reveal refused: a run record already exists at ${join(bundleDirEarly, "manifest.yaml")}.\n` +
      `A holdout pack is revealed exactly once, and the first run's record is evidence.\n` +
      `Overwriting it would destroy the only account of what actually ran.`,
    );
  }

  // An existsSync check followed by a later write is NOT atomic. MEASURED: two
  // reveal.ts processes launched together against the same unrevealed id BOTH
  // passed the check above, both ran, and the last writer won — leaving the
  // manifest stamped "candidate: race-A" while the evidence bundle recorded
  // "candidate: race-B", on a pack that is now genuinely spent. One raw log was
  // overwritten outright, because both runs derived the same filename from a
  // whole-second timestamp.
  //
  // The lock closes it: "wx" fails if the path exists, and that test-and-create
  // is a single atomic syscall, so exactly one process can hold it.
  mkdirSync(bundleDirEarly, { recursive: true });
  const lockPath = join(bundleDirEarly, ".reveal.lock");
  try {
    writeFileSync(lockPath, `pid: ${process.pid}\ncandidate: ${candidate}\nlocked_at: ${new Date().toISOString()}\n`, { flag: "wx" });
  } catch (e: any) {
    if (e?.code === "EEXIST") {
      die(
        `reveal refused: ${lockPath} exists, so another reveal of ${id} holds the lock.\n` +
        `Two concurrent reveals would spend one pack and disagree about which candidate ran it.\n` +
        `If no reveal is running, a previous one died mid-run: read the lock file, work out what\n` +
        `actually happened to the pack, and remove it by hand. This is deliberately not automatic.`,
      );
    }
    throw e;
  }
  // Release the lock however this process ends, but ONLY if we still own it.
  process.on("exit", () => { try { if (readFileSync(lockPath, "utf8").includes(`pid: ${process.pid}\n`)) rmSync(lockPath, { force: true }); } catch {} });

  // ---- load the cases (FIRST read of withheld content in this process) ----
  // The pack hash is over cases.yaml's RAW BYTES, but the file is parsed as UTF-8.
  // An invalid byte is silently replaced with U+FFFD before the command is built,
  // so the hash could MATCH while the command actually executed differed from the
  // bytes the hash pinned. Refuse rather than run something the hash does not cover.
  const casesRaw = readFileSync(join(packDir, "cases.yaml"));
  const casesText = casesRaw.toString("utf8");
  if (!Buffer.from(casesText, "utf8").equals(casesRaw)) {
    die(
      `reveal refused (pack NOT spent): cases.yaml is not valid UTF-8.\n` +
      `The pack hash covers its raw bytes, but parsing would silently replace the invalid\n` +
      `ones, so the command that ran would not be the command the hash pinned.`,
    );
  }
  const cases = ((globalThis as any).Bun.YAML.parse(casesText) as { cases: Case[] }).cases;
  const expected = JSON.parse(readFileSync(join(packDir, "expected.json"), "utf8")) as Record<string, Expected>;

  // MEASURED: a cases.yaml carrying the SAME id twice ran BOTH commands and sealed
  // "2 PASS / 0 FAIL of 2". Two different commands were then graded against one
  // shared expectation, and the run record held two "## H001" sections that no
  // reader can tell apart. An id that does not identify one case cannot anchor a
  // verdict, so duplicates are refused.
  {
    const seen = new Set<string>(), dupes = new Set<string>();
    for (const c of cases) { if (seen.has(c.id)) dupes.add(c.id); seen.add(c.id); }
    if (dupes.size) {
      die(`reveal refused (pack NOT spent): cases.yaml repeats case id(s) ${[...dupes].join(", ")}.\n` +
          `Each id must name exactly one case, or the run record cannot attribute a result to it.`);
    }
  }

  // MEASURED: expected.json with the SAME key twice parses last-key-wins in silence.
  // A file reading {"H001":{"exit":0},"H001":{"exit":5}} graded the case against
  // exit 5 and PASSED, while a custodian reading top-down would believe the
  // expectation was exit 0. JSON.parse cannot report this, so the raw text is
  // scanned. The pack hash pins these bytes, but pinning the wrong expectation is
  // not the same as catching it.
  {
    const rawExpected = readFileSync(join(packDir, "expected.json"), "utf8");
    // The scanner lives in ./json-keys.ts so it can be property-tested directly.
    // Two earlier attempts at this guard were BOTH defeated, and both failed the
    // same way — they searched the raw text for ONE literal spelling of the key:
    //   1. a regex built from the id. A corrupted escape disabled it for any id
    //      holding a regex metacharacter; `H(1)` sealed a wrong verdict, MEASURED.
    //   2. an indexOf scan for JSON.stringify(id). Defeated by ESCAPE EQUIVALENCE:
    //      {"H1":{"exit":0},"H\u0031":{"exit":9}} is one repeated key to JSON.parse
    //      (\u0031 IS "1"), but the two spellings share no bytes, so the scan saw
    //      one occurrence and let a wrong verdict seal. MEASURED by review.
    // So the id is never spelled out at all. The raw text is tokenized, every
    // object KEY is decoded through JSON.parse, and decoded keys are compared.
    // Any two spellings of the same key now collide by construction.
    // Scope is the WHOLE document, not just the ids in cases.yaml: a repeated
    // "exit" inside one entry silently changes that expectation too. A string
    // that merely LOOKS like a key while sitting in value position is correctly
    // ignored, because only keys are ever recorded.
    const dupKeys = duplicateJsonKeys(rawExpected);
    if (dupKeys.length) {
      die(`reveal refused (pack NOT spent): expected.json repeats key(s) ${dupKeys.join(", ")}.\n` +
          `JSON keeps only the LAST one, so the expectation actually used is not the one a\n` +
          `reader would see first. Two different spellings of one key (for example "H1" and\n` +
          `"H\\u0031") count as a repeat, because JSON.parse treats them as the same key.\n` +
          `Remove the duplicate and re-seal at the next version.`);
    }
  }

  // Every expectation is shape-checked BEFORE a single case runs. A malformed or
  // null entry previously threw mid-loop at `want.exit` — after earlier cases had
  // already executed their shell commands and left side effects behind.
  {
    const shapeProblems: string[] = [];
    for (const c of cases) {
      const w = (expected as any)[c.id];
      if (w === undefined) shapeProblems.push(`${c.id}: no entry in expected.json`);
      else if (w === null || typeof w !== "object" || Array.isArray(w)) shapeProblems.push(`${c.id}: entry is ${w === null ? "null" : Array.isArray(w) ? "an array" : typeof w}, expected an object`);
      else if (typeof w.exit !== "number") shapeProblems.push(`${c.id}: "exit" is ${typeof w.exit}, expected a number`);
    }
    if (shapeProblems.length) {
      die(`reveal refused (pack NOT spent): expected.json is malformed and NOTHING WAS RUN.\n  ` + shapeProblems.join("\n  "));
    }
  }

  if (cases.length !== man.case_count) {
    die(`reveal refused: manifest says case_count ${man.case_count}, pack holds ${cases.length}. The count was published before the code existed; a disagreement means the pack moved.`);
  }
  const missing = cases.filter((c) => !(c.id in expected)).map((c) => c.id);
  if (missing.length) die(`reveal refused: no expected result for ${missing.join(", ")}.`);

  if (dryRun) { console.log(`\n--dry-run: ${cases.length} case(s) verified and NOT run. revealed_at untouched.`); return 0; }

  // ---- run, once ----------------------------------------------------------
  const startedAt = new Date().toISOString().replace(/\.\d+Z$/, "Z");
  const log: string[] = [
    `# Holdout run record — ${id}`, `candidate: ${candidate}`, `started_at: ${startedAt}`,
    `hash_method: ${man.hash_method}`, `pack_sha256: ${digest}`, `expected_results_sha256: ${expDigest}`, "",
  ];
  let pass = 0, fail = 0;

  for (const c of cases) {
    const want = expected[c.id];
    // Capture stdout as RAW BYTES. With encoding "utf8" the child's bytes go
    // through a lossy UTF-8 decoder first, so any invalid byte becomes U+FFFD
    // before hashing. MEASURED: bytes 0xFF 0x41 hash to
    // 1b6d8a78363cf390895eba876b9fefb99d73506bb40fe31c4efeb2b58f7fe1fc once
    // decoded, but to be611a063fe2322ed4671804fd2e68027756b32e14ec8d64f2e790344eb93261
    // raw — and `shasum -a 256`, which is how a custodian writes the
    // expectation, produces the RAW one. A byte-exact correct answer was
    // therefore recorded FAIL and the pack spent on it. Worse, 0xFF 0x41 and
    // 0xFE 0x41 are different byte streams that decode to the SAME string, so
    // two distinct answers collided into a single verdict.
    let outBuf: Buffer = Buffer.alloc(0), code = 0, signalName = "";
    try {
      outBuf = execFileSync("/bin/sh", ["-c", c.run], {
        stdio: ["ignore", "pipe", "pipe"],
        maxBuffer: CASE_MAX_BUFFER, timeout: CASE_TIMEOUT_MS,
      });
    } catch (e: any) {
      // A harness limit is not a verdict. Abort before sealing so the pack
      // survives to be revealed again once the harness is fixed.
      if (e?.code === "ENOBUFS") {
        die(`reveal aborted (pack NOT spent): case ${c.id} wrote more than ${CASE_MAX_BUFFER} bytes to stdout.\n` +
            `That is a harness limit, not a failure, and this exam is one-shot. Raise CASE_MAX_BUFFER and re-run.`);
      }
      // MEASURED on bun 1.3.9: a timeout sets code "ETIMEDOUT", signal "SIGTERM",
      // status null, and leaves `killed` UNDEFINED. Testing `killed` alone never
      // matched, so the hang fell through to the signal branch and was sealed as a
      // real FAIL — spending the pack on a harness limit. Node sets `killed`, so
      // both are checked.
      if (e?.code === "ETIMEDOUT" || e?.killed === true) {
        die(`reveal aborted (pack NOT spent): case ${c.id} did not finish within ${CASE_TIMEOUT_MS} ms and was killed.\n` +
            `A timeout is a harness limit, not a failure. Fix the case or raise CASE_TIMEOUT_MS, then re-run.`);
      }
      outBuf = Buffer.isBuffer(e.stdout) ? e.stdout : Buffer.from(String(e.stdout ?? ""));
      if (typeof e.status === "number") {
        code = e.status;
      } else if (typeof e.signal === "string" && e.signal) {
        // Killed by a signal: a real failure, but it has no exit code. Record
        // the signal rather than inventing an exit status the case never had.
        code = -1;
        signalName = e.signal;
      } else {
        die(`reveal aborted (pack NOT spent): case ${c.id} failed with no exit status and no signal — ` +
            `${String(e?.code ?? e?.message ?? e)}. That is a harness fault, not a verdict.`);
      }
    }

    // The digest AND the substring check are both over the raw bytes. The decoded
    // string is now only ever used for human-readable logging.
    const outHash = sha256Hex(outBuf);
    const reasons: string[] = [];
    if (signalName) reasons.push(`killed by signal ${signalName} (expected exit ${want.exit})`);
    else if (code !== want.exit) reasons.push(`exit ${code} != ${want.exit}`);
    if (want.stdout_sha256 && outHash !== want.stdout_sha256) reasons.push(`stdout sha256 ${outHash} != ${want.stdout_sha256}`);
    // Matched against the RAW BYTES, for the same reason the digest is. Matching the
    // decoded string would carry the identical lossy-decode exposure that
    // stdout_sha256 had: every invalid byte collapses to U+FFFD, so distinct outputs
    // become indistinguishable to the matcher.
    if (want.stdout_contains && !outBuf.includes(Buffer.from(want.stdout_contains, "utf8"))) reasons.push(`stdout missing ${JSON.stringify(want.stdout_contains)}`);

    const ok = reasons.length === 0;
    ok ? pass++ : fail++;
    log.push(`## ${c.id} [${c.class}] ${ok ? "PASS" : "FAIL"}`, `run: ${c.run}`, `exit: ${code}`, `stdout_sha256: ${outHash}`);
    if (!ok) log.push(`reasons: ${reasons.join("; ")}`);
    log.push("");
    console.log(`  ${ok ? "PASS" : "FAIL"}  ${c.id} [${c.class}]${ok ? "" : "  — " + reasons.join("; ")}`);
  }

  // ---- seal, as produced --------------------------------------------------
  const finishedAt = new Date().toISOString().replace(/\.\d+Z$/, "Z");
  const bundle = `EVB-${id}`;
  const bundleDir = join(EVIDENCE_ROOT, bundle);
  mkdirSync(bundleDir, { recursive: true });
  // finishedAt is second-precision for readability; the FILENAME carries
  // milliseconds, because two runs in the same second previously produced the
  // same name and one raw log was silently overwritten.
  const logName = `holdout-run-${new Date().toISOString().replace(/[-:.]/g, "")}.log`;
  const logText = log.concat([`finished_at: ${finishedAt}`, `result: ${pass} PASS / ${fail} FAIL of ${cases.length}`]).join("\n") + "\n";
  writeFileSync(join(bundleDir, logName), logText);
  const logHash = sha256Hex(logText);
  writeFileSync(join(bundleDir, "manifest.yaml"),
    [`artifact_type: HoldoutRunRecord`, `id: ${bundle}`, `holdout_id: ${id}`, `candidate: ${candidate}`,
     `started_at: "${startedAt}"`, `finished_at: "${finishedAt}"`, `case_count: ${cases.length}`,
     `pass: ${pass}`, `fail: ${fail}`, `raw_log: ${logName}`, `raw_log_sha256: "${logHash}"`,
     `# Preserved AS PRODUCED. Failures are not re-run and are not edited (PRD §22, O43).`, ""].join("\n"));

  // Stamp the manifest last, so a crash mid-run never marks a pack spent that
  // produced no sealed record.
  const src = readFileSync(mPath, "utf8");
  // Written to a sibling temp file and RENAMED into place. A plain overwrite is
  // not atomic: a concurrent reader can observe a half-written manifest, and a
  // torn read of a seal.ts write was OBSERVED in review (1 run in 5). rename(2)
  // within one directory is atomic, so a reader sees the old file or the new one.
  // Function replacers, never replacement STRINGS: a "$&" in a replacement string
  // expands to the matched text, which has silently corrupted generated code here.
  const stamped = src
    .replace(/^revealed_at:.*$/m, () => `revealed_at: "${finishedAt}" # ${cases.length} case(s) run exactly once against frozen candidate ${candidate}; ${pass} PASS / ${fail} FAIL, preserved as-produced`)
    .replace(/^run_evidence_bundle:.*$/m, () => `run_evidence_bundle: ${bundle}`);
  const mTmp = `${mPath}.tmp-${process.pid}`;
  writeFileSync(mTmp, stamped);
  renameSync(mTmp, mPath);

  console.log(`\n${pass} PASS / ${fail} FAIL of ${cases.length}. Sealed at ${join(bundleDir, logName)}`);
  console.log(fail ? `FAIL is the result. It stands. A fix needs a new pack at the next version.` : `All cases passed.`);
  // Exit non-zero on failure so a caller that checks the EXIT CODE and not the
  // tally sees it — a suite that throws mid-run still prints "N/N passed".
  return fail ? 1 : 0;
}

process.exit(main());
