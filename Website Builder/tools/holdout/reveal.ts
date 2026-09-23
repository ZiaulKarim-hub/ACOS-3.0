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

import { execFileSync, spawnSync } from "node:child_process";
import { appendFileSync, chmodSync, cpSync, existsSync, lstatSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, renameSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { caseKeyProblems, duplicateJsonKeys } from "./json-keys.ts";
import { canonicalPackHash, expectedResultsHash, sha256Hex } from "./canonical-hash.ts";
import { ID_SHAPE, SHA256_HEX, parse, validate, type HoldoutManifest } from "./manifest.ts";

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
// MEASURED (security review F7): the old `Number(env ?? 120_000)` accepted garbage.
// On bun 1.3.9, `timeout: NaN` makes spawn THROW ERR_OUT_OF_RANGE — per case, after
// earlier cases already ran — and `timeout: 0` silently disables the timer and the
// child ran to completion. Both are refused here, before anything is read or run.
const CASE_TIMEOUT_MS = (() => {
  const raw = process.env.WB_HOLDOUT_CASE_TIMEOUT_MS;
  if (raw === undefined) return 120_000;
  const n = Number(raw);
  if (!Number.isInteger(n) || n <= 0) {
    console.error(`reveal refused: WB_HOLDOUT_CASE_TIMEOUT_MS is ${JSON.stringify(raw)} — it must be a positive integer of milliseconds.\nA non-number here used to throw mid-run; 0 or a negative silently DISABLED the per-case timeout.`);
    process.exit(1);
  }
  return n;
})();
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
  // Security review F3: --id used to be interpolated raw into THREE path
  // expressions that normalize differently. MEASURED: with --id "./HLD-S41-v1",
  // join() collapses "./" in the manifest and pack paths but NOT in
  // "EVB-./HLD-S41-v1" — so the same pack resolved, while the write-once guard
  // and the lock both looked at a directory that never exists. "../.." escaped
  // qa-private/ entirely. The shape check kills the whole class: no dots, no
  // separators, nothing for normalize() to disagree about.
  if (!ID_SHAPE.test(id)) {
    die(`reveal refused: --id ${JSON.stringify(id)} is not a valid pack id (HLD-S<nn>...-v<n>).\nThe id becomes three filesystem paths; anything but the strict shape is refused unseen.`);
  }
  const candidate = arg("--candidate") ?? die("reveal refused: --candidate <commit-sha> is required.\nA pack is run against a NAMED FROZEN candidate, or the result cannot be attributed to anything.");
  // Security review F2 (secondary): the candidate is written into the lock file,
  // the run record and a YAML comment. It names a COMMIT, so it is hex or nothing —
  // which also makes newline/YAML injection through it impossible by construction.
  if (!/^[0-9a-fA-F]{7,40}$/.test(candidate.trim())) {
    die(`reveal refused: --candidate ${JSON.stringify(candidate)} is not a commit sha (7-40 hex characters).\nAttribution to anything other than a commit is not attribution.`);
  }
  const dryRun = has("--dry-run");
  const allowUnverified = has("--allow-unverified-candidate");

  // ---- the manifest -------------------------------------------------------
  const mPath = join(MANIFEST_DIR, `${id}.yaml`);
  if (!existsSync(mPath)) die(`reveal refused: no manifest at ${mPath}`);
  // Held in memory until the stamp at the very end. The stamp used to RE-READ the
  // file from disk after every case had run — so a case's own shell command could
  // rewrite the manifest mid-run and the rewrite is what got stamped and sealed
  // (security review F6). What gets stamped now is exactly what was validated.
  const preRunManifestText = readFileSync(mPath, "utf8");
  const parsed = parse(preRunManifestText);
  if (!parsed.ok) die(`reveal refused: ${mPath} does not parse — ${parsed.error}`);
  const problems = validate(parsed.value);
  if (problems.length) {
    die(`reveal refused: ${mPath} is invalid —\n` + problems.map((p) => `    ${p.field}: ${p.message}`).join("\n"));
  }
  const man = parsed.value as HoldoutManifest;
  if (man.id !== id) {
    die(`reveal refused: the manifest at ${mPath} says id ${JSON.stringify(man.id)}, not ${JSON.stringify(id)}.\nA manifest reachable under a name it does not claim is a moved or forged manifest.`);
  }

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

  // Security review F4: listPackFiles() lstat-refuses symlinks it WALKS TO, but the
  // walk starts with readdirSync on the root it was handed, which FOLLOWS a link.
  // So qa-private/ or the pack directory itself could be a symlink out of the
  // audited tree, and "a pack must be self-contained" was not true at the root.
  for (const p of [PACK_ROOT, packDir]) {
    if (lstatSync(p).isSymbolicLink()) {
      die(`reveal refused: ${p} is a symlink. A holdout pack must be self-contained;\nwhat a link points at can change without the pack changing.`);
    }
  }
  if (realpathSync(packDir) !== join(realpathSync(PACK_ROOT), id)) {
    die(`reveal refused: ${packDir} does not resolve to a plain directory under ${PACK_ROOT}/.`);
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
    // Security review F2: this used to be a console note and nothing else. The
    // sealed record then read "run exactly once against frozen candidate X" —
    // byte-indistinguishable from a verified run. Copy the manifest and pack to
    // any non-repo directory and ANY string sealed as the candidate. Now it is a
    // refusal, and the explicit override writes UNVERIFIED into everything.
    if (!allowUnverified) {
      die(
        `reveal refused: not a git repository, so the candidate cannot be verified as frozen.\n` +
        `Run from the repository the candidate commit lives in. If you truly need an\n` +
        `unattributed run, pass --allow-unverified-candidate — the run record and the\n` +
        `manifest stamp will then both carry candidate_verified: false, permanently.`,
      );
    }
    console.log("note: not a git repository — candidate is UNVERIFIED and the sealed record will say so.");
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
  // F9: Bun.YAML.parse keeps the LAST duplicate key in silence (MEASURED: a case
  // carrying run: twice executed the second command while a reader saw the first).
  {
    const yamlProblems = caseKeyProblems(casesText);
    if (yamlProblems.length) {
      die(`reveal refused (pack NOT spent): cases.yaml is ambiguous —\n  ` + yamlProblems.join("\n  "));
    }
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
      else {
        // Security review F10: optional fields were tested for TRUTHINESS at use,
        // so "" or null silently disabled that check for that case, and a
        // misspelled field name was silently ignored. All refused here instead.
        for (const k of Object.keys(w)) {
          if (k !== "exit" && k !== "stdout_sha256" && k !== "stdout_contains") {
            shapeProblems.push(`${c.id}: unknown expectation field ${JSON.stringify(k)} — a typo here would silently weaken the case`);
          }
        }
        if ("stdout_sha256" in w && (typeof w.stdout_sha256 !== "string" || !SHA256_HEX.test(w.stdout_sha256))) {
          shapeProblems.push(`${c.id}: "stdout_sha256" must be 64 lowercase hex characters`);
        }
        if ("stdout_contains" in w && (typeof w.stdout_contains !== "string" || w.stdout_contains.length === 0)) {
          shapeProblems.push(`${c.id}: "stdout_contains" must be a non-empty string — an empty one matches everything and checks nothing`);
        }
      }
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

  // F12 fixed by ORDER: everything above this line is read-only, and --dry-run
  // returns before the bundle directory or the lock ever exist.

  // F8 (security review): every abort path after this point used to exit with
  // NOTHING written, while the console printed each case's PASS/FAIL as it ran.
  // A reveal could be started, watched, and killed before the seal, arbitrarily
  // many times — "a pack that can be re-run until it passes is homework, not an
  // exam", and the abort paths were the re-run. Every attempt now lands in the
  // bundle BEFORE the first case runs, and the count is sealed into the record.
  const attemptsPath = join(bundleDirEarly, "attempts.log");
  appendFileSync(attemptsPath, `${new Date().toISOString()} pid=${process.pid} candidate=${candidate} starting\n`);
  const attemptCount = readFileSync(attemptsPath, "utf8").split("\n").filter((l) => l.endsWith(" starting") || l.includes(" starting")).length;
  if (attemptCount > 1) {
    console.log(`note: this is reveal ATTEMPT ${attemptCount} for ${id} — earlier attempts aborted before sealing, and the sealed record will say so.`);
  }

  // ---- run, once ----------------------------------------------------------
  // F1 (security review, CRITICAL): each case is the IMPLEMENTER'S code running
  // with this process's filesystem rights, and the pack — answer key included —
  // sat at a well-known path in the same tree. A case could read
  // qa-private/*/expected.json on its first invocation and satisfy every later
  // case from the answers. So for the duration of the run the pack lives at an
  // unguessable mkdtemp path outside the repository, mode 700.
  //
  // STATED LIMIT, not hidden: the cases run as the SAME USER as this process, so
  // a determined case can still hunt the temp root or attach a debugger. That
  // cannot be closed without OS-level sandboxing (PRD §22 assumes the candidate
  // is graded, not imprisoned). What this buys: the answer key is no longer at a
  // knowable path, and the POST-RUN re-verification below turns silent tampering
  // into a recorded, sealed fact.
  const hideBase = mkdtempSync(join(tmpdir(), "wb-reveal-"));
  chmodSync(hideBase, 0o700);
  const hiddenPack = join(hideBase, "pack");
  let packHidden = false;
  try {
    renameSync(packDir, hiddenPack);
    packHidden = true;
  } catch (e: any) {
    if (e?.code === "EXDEV") {   // tmp on another volume: copy, then remove
      cpSync(packDir, hiddenPack, { recursive: true });
      rmSync(packDir, { recursive: true, force: true });
      packHidden = true;
    } else { rmSync(hideBase, { recursive: true, force: true }); throw e; }
  }
  // The lock file names the hiding place, so a SIGKILLed reveal can be recovered
  // by hand — consistent with the lock's "deliberately not automatic" doctrine.
  appendFileSync(lockPath, `pack_hidden_at: ${hiddenPack}\n`);
  const restorePack = () => {
    if (!packHidden) return;
    try { renameSync(hiddenPack, packDir); }
    catch {
      try { cpSync(hiddenPack, packDir, { recursive: true }); } catch {}
    }
    packHidden = false;
    try { rmSync(hideBase, { recursive: true, force: true }); } catch {}
  };
  process.on("exit", restorePack);   // fires on die() too — die() is process.exit(1)

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
    let outBuf: Buffer = Buffer.alloc(0), errBuf: Buffer = Buffer.alloc(0), code = 0, signalName = "";
    // spawnSync, not execFileSync: execFileSync only surfaces stderr on the ERROR
    // object, so a SUCCEEDING case's stderr was silently discarded (security
    // review F11) and could never be part of the evidence. spawnSync returns
    // errors in-band, so the abort branches below read r.error instead of a catch.
    const r = spawnSync("/bin/sh", ["-c", c.run], {
      stdio: ["ignore", "pipe", "pipe"],
      maxBuffer: CASE_MAX_BUFFER, timeout: CASE_TIMEOUT_MS,
    });
    outBuf = Buffer.isBuffer(r.stdout) ? r.stdout : Buffer.from(String(r.stdout ?? ""));
    errBuf = Buffer.isBuffer(r.stderr) ? r.stderr : Buffer.from(String(r.stderr ?? ""));
    {
      const e: any = r.error;
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
      // both are checked. (Re-verified across the execFileSync->spawnSync move by
      // the suite's own timeout assertion.)
      if (e?.code === "ETIMEDOUT" || (r as any).killed === true) {
        die(`reveal aborted (pack NOT spent): case ${c.id} did not finish within ${CASE_TIMEOUT_MS} ms and was killed.\n` +
            `A timeout is a harness limit, not a failure. Fix the case or raise CASE_TIMEOUT_MS, then re-run.`);
      }
      if (typeof r.status === "number") {
        code = r.status;
      } else if (typeof r.signal === "string" && r.signal) {
        // Killed by a signal: a real failure, but it has no exit code. Record
        // the signal rather than inventing an exit status the case never had.
        code = -1;
        signalName = r.signal;
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
    log.push(`## ${c.id} [${c.class}] ${ok ? "PASS" : "FAIL"}`, `run: ${c.run}`, `exit: ${code}`, `stdout_sha256: ${outHash}`,
             `stderr_sha256: ${sha256Hex(errBuf)}`, `stderr_bytes: ${errBuf.length}`);
    if (!ok) log.push(`reasons: ${reasons.join("; ")}`);
    log.push("");
    console.log(`  ${ok ? "PASS" : "FAIL"}  ${c.id} [${c.class}]${ok ? "" : "  — " + reasons.join("; ")}`);
  }

  // ---- restore the pack, then RE-VERIFY everything the run could have bent ----
  restorePack();
  // F1's detection half: the pack hash and the working tree were verified BEFORE
  // the run and never re-checked, so anything a case modified stayed invisible to
  // the sealed record. Both are re-verified here and sealed into the record. A
  // failed re-check still seals — the pack IS spent; what must not happen is the
  // tampering staying off the record — and the process exits non-zero.
  let packIntactAfterRun = false;
  try {
    packIntactAfterRun =
      canonicalPackHash(packDir).digest === man.private_pack_sha256 &&
      expectedResultsHash(packDir) === man.expected_results_sha256;
  } catch { packIntactAfterRun = false; }
  let treeCleanAfterRun: "true" | "false" | "unverified" = "unverified";
  if (inRepo) {
    try { treeCleanAfterRun = execFileSync("git", ["status", "--porcelain"], { encoding: "utf8" }).trim() === "" ? "true" : "false"; }
    catch { treeCleanAfterRun = "false"; }
  }
  // F6: what gets stamped is the text validated BEFORE the run. If the file on
  // disk changed while cases were running, that is recorded as tampering.
  const manifestOnDiskNow = readFileSync(mPath, "utf8");
  const manifestRewrittenDuringRun = manifestOnDiskNow !== preRunManifestText;

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
     `candidate_verified: ${inRepo}`, `attempt: ${attemptCount}`,
     `started_at: "${startedAt}"`, `finished_at: "${finishedAt}"`, `case_count: ${cases.length}`,
     `pass: ${pass}`, `fail: ${fail}`, `raw_log: ${logName}`, `raw_log_sha256: "${logHash}"`,
     `post_run_pack_intact: ${packIntactAfterRun}`,
     `post_run_tree_clean: ${treeCleanAfterRun}`,
     `manifest_rewritten_during_run: ${manifestRewrittenDuringRun}`,
     `# Preserved AS PRODUCED. Failures are not re-run and are not edited (PRD §22, O43).`, ""].join("\n"));

  // Stamp the manifest last, so a crash mid-run never marks a pack spent that
  // produced no sealed record. Stamped from the PRE-RUN text held in memory (F6):
  // a case that rewrote the manifest mid-run used to have its rewrite stamped by
  // this very tool; now the rewrite is discarded and recorded as tampering.
  const src = preRunManifestText;
  // Written to a sibling temp file and RENAMED into place. A plain overwrite is
  // not atomic: a concurrent reader can observe a half-written manifest, and a
  // torn read of a seal.ts write was OBSERVED in review (1 run in 5). rename(2)
  // within one directory is atomic, so a reader sees the old file or the new one.
  // Function replacers, never replacement STRINGS: a "$&" in a replacement string
  // expands to the matched text, which has silently corrupted generated code here.
  const stamped = src
    .replace(/^revealed_at:.*$/m, () => `revealed_at: "${finishedAt}" # ${cases.length} case(s) run exactly once against ${inRepo ? "frozen candidate" : "UNVERIFIED candidate"} ${candidate}; ${pass} PASS / ${fail} FAIL, preserved as-produced`)
    .replace(/^run_evidence_bundle:.*$/m, () => `run_evidence_bundle: ${bundle}`);
  const mTmp = `${mPath}.tmp-${process.pid}`;
  writeFileSync(mTmp, stamped);
  renameSync(mTmp, mPath);

  console.log(`\n${pass} PASS / ${fail} FAIL of ${cases.length}. Sealed at ${join(bundleDir, logName)}`);
  const tampered = !packIntactAfterRun || treeCleanAfterRun === "false" || manifestRewrittenDuringRun;
  if (tampered) {
    console.log(`TAMPERING RECORDED: pack_intact=${packIntactAfterRun} tree_clean=${treeCleanAfterRun} manifest_rewritten=${manifestRewrittenDuringRun}.`);
    console.log(`The run is sealed AS PRODUCED, the pack is spent, and this verdict must not be trusted.`);
  }
  console.log(fail ? `FAIL is the result. It stands. A fix needs a new pack at the next version.` : tampered ? `Cases passed, but see the tampering record above.` : `All cases passed.`);
  // Exit non-zero on failure so a caller that checks the EXIT CODE and not the
  // tally sees it — a suite that throws mid-run still prints "N/N passed".
  return fail || tampered ? 1 : 0;
}

process.exit(main());
