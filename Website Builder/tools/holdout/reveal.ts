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
 *   printf '%s\n' "$WB_HOLDOUT_KEY" | \
 *     WB_QA_CONTEXT=1 bun tools/holdout/reveal.ts --id HLD-S41-v1 --candidate <sha> --key-stdin
 *   [--dry-run]   verify hashes and print the plan; run nothing, seal nothing.
 *   The answer key travels on STDIN only (T1): argv and env are visible to any
 *   same-user process via ps; stdin is not.
 */

import { execFileSync, spawnSync } from "node:child_process";
import { appendFileSync, chmodSync, existsSync, lstatSync, mkdirSync, readdirSync, readFileSync, realpathSync, renameSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { canonicalCasesText, caseKeyProblems, duplicateJsonKeys } from "./json-keys.ts";
import { canonicalPackHash, expectedResultsHash, sha256Hex } from "./canonical-hash.ts";
import { ENC_NAME, KEY_HEX, PLAIN_NAME, decryptExpected } from "./keybox.ts";
import { ID_SHAPE, SHA256_HEX, parse, validate, type HoldoutManifest } from "./manifest.ts";
import { CASES_DELIM, FOOTER_DELIM } from "./record-format.ts";

const MANIFEST_DIR = "planning/holdouts/manifests";
const ATTEMPTS_DIR = "planning/holdouts/attempts";   // TRACKED attempts anchors (T3)
const PACK_ROOT = "qa-private";
const EVIDENCE_ROOT = "planning/evidence";

// T4, recorded IN the record rather than only in a comment: what the tree
// snapshot can and cannot see. Cross-checked verbatim between the hashed log
// and the readable manifest by verify-run-records.ts, like every other field.
const TREE_CLEAN_SEMANTICS = "end-of-run snapshot; blind to a modify-then-restore during the run and to gitignored paths; reveal's own run artifacts (this pack's evidence bundle and attempts anchor) are excluded";

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

/**
 * `git status --porcelain -uall`, minus the paths reveal itself legitimately
 * writes during a run: this pack's evidence bundle (untracked until someone
 * commits it) and this pack's attempts anchor (a TRACKED file each attempt
 * appends to — that append is the T3 fix, not tampering). Without the filter,
 * reveal's own bookkeeping makes every git-repo run read "dirty": an aborted
 * attempt's bundle blocked the next attempt pre-run, and the post-run snapshot
 * condemned every run for the bundle it had just sealed. -uall, because
 * porcelain otherwise collapses an untracked directory to one line and the
 * individual paths cannot be filtered. Rename lines are never filtered.
 * Quoted paths (spaces, escapes) are never filtered either — ours contain none.
 */
const gitDirtyFiltered = (id: string, anchorClean: boolean): string => {
  const raw = execFileSync("git", ["status", "--porcelain", "-uall"], { encoding: "utf8" });
  const bundlePrefix = `${EVIDENCE_ROOT}/EVB-${id}/`;
  const anchorFile = `${ATTEMPTS_DIR}/${id}.log`;
  return raw.split("\n").filter(Boolean).filter((line) => {
    if (line.includes(" -> ")) return true;            // renames always count
    const path = line.slice(3);
    if (path.startsWith('"')) return true;             // quoted: not ours, keep
    // U1 (fourth review, EXECUTED): a blanket path exclusion here CANCELLED the
    // T3 anchor — a case truncated the tracked anchor and the tree still read
    // clean, because the one file whose changes mattered was the one file the
    // check skipped. The anchor is excluded ONLY while its content is exactly
    // what this process itself wrote (anchorClean); pre-run that is the text
    // just chain-verified, post-run it is pre-run text + this run's own line,
    // checked byte-for-byte by the caller. Anything else is dirt.
    if (path === anchorFile) return !anchorClean;
    return !path.startsWith(bundlePrefix);             // bundle content is checked separately (U2)
  }).join("\n");
};

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
  // A pack at mode 000 is the footprint of an INTERRUPTED reveal (the v3 lockdown
  // below survives any kill). The pack is intact; the refusal says how to recover.
  if ((lstatSync(packDir).mode & 0o777) === 0) {
    die(
      `reveal refused: ${packDir} is at mode 000 — an interrupted reveal left it locked down.\n` +
      `The pack is INTACT, merely unreadable. Recover it with:\n` +
      `    chmod u+rwX ${packDir} && chmod -R u+rwX ${packDir}\n` +
      `then read attempts.log in ${join(EVIDENCE_ROOT, "EVB-" + id)} before revealing again —\n` +
      `the interrupted attempt is already on that record.`,
    );
  }
  for (const p of [PACK_ROOT, packDir]) {
    if (lstatSync(p).isSymbolicLink()) {
      die(`reveal refused: ${p} is a symlink. A holdout pack must be self-contained;\nwhat a link points at can change without the pack changing.`);
    }
  }
  if (realpathSync(packDir) !== join(realpathSync(PACK_ROOT), id)) {
    die(`reveal refused: ${packDir} does not resolve to a plain directory under ${PACK_ROOT}/.`);
  }

  // T1: a sealed pack carries the answer key as CIPHERTEXT only. Plaintext on
  // disk is exactly what the pre-opened-descriptor attack read through the
  // mode-000 lockdown, so its presence is refused outright — there is no
  // downgrade path back to the defeated design.
  if (existsSync(join(packDir, PLAIN_NAME))) {
    die(`reveal refused: ${join(packDir, PLAIN_NAME)} is PLAINTEXT.\n` +
        `A sealed pack holds ${ENC_NAME}; plaintext on disk is readable by any same-user\n` +
        `process that opened it early (security review T1). Re-seal through seal.ts.`);
  }
  if (!existsSync(join(packDir, ENC_NAME))) {
    die(`reveal refused: ${join(packDir, ENC_NAME)} is missing — this pack was not sealed by seal.ts.`);
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
    dirty = gitDirtyFiltered(id, true).trim();   // anchor content was chain-verified moments ago
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

  // T2 (EXECUTED): a double-quoted YAML scalar with \n escapes is a multi-line
  // run string the block-scalar refusals never see, and it used to be written
  // verbatim into the hashed log — where the verifier's first-match field scan
  // read the INJECTED footer field instead of the real one. seal.ts refuses
  // these at authoring; this is the same refusal against a hand-written pack.
  {
    const multiline = cases.flatMap((c) =>
      (["id", "class", "description", "run"] as const)
        .filter((k) => typeof (c as any)[k] === "string" && /[\r\n]/.test((c as any)[k]))
        .map((k) => `${JSON.stringify(c.id)}: field "${k}" contains a newline`));
    if (multiline.length) {
      die(`reveal refused (pack NOT spent): case string fields must be single-line —\n  ` + multiline.join("\n  ") +
          `\nAn embedded newline in a case field is a run-record injection vector (security review T2).`);
    }
  }

  // W3 (sixth security review, EXECUTED): three passes in a row, a YAML
  // spelling nobody enumerated smuggled a duplicate key past a line regex —
  // last time a ONE-LINE flow mapping sealed and executed a hidden second
  // command. Structural fix: a sealed cases.yaml must BE the canonical
  // serialization of its own parse. Whatever Bun.YAML read is regenerated
  // here; one byte of difference means the bytes on disk are not their own
  // parse, and that is exactly the reader/harness divergence PRD §22 forbids.
  {
    let canon = "";
    try { canon = canonicalCasesText(casesText); }
    catch (e: any) { die(`reveal refused (pack NOT spent): cases.yaml did not canonicalize — ${String(e?.message ?? e)}`); }
    if (canon !== casesText) {
      die(`reveal refused (pack NOT spent): cases.yaml is not in canonical form wb-cases-1.\n` +
          `seal.ts writes the canonical serialization; a sealed pack that deviates from the\n` +
          `canonical form of its OWN parse can show a reader one thing and run another.\n` +
          `Re-seal the pack at the next version.`);
    }
  }

  // ---- the answer key: ciphertext on disk, key on stdin, plaintext in memory (T1)
  if (!has("--key-stdin")) {
    die(`reveal refused (pack NOT spent): the answer key is encrypted and no --key-stdin was given.\n` +
        `Pipe the key the custodian recorded at seal time:\n` +
        `    printf '%s\\n' "$WB_HOLDOUT_KEY" | WB_QA_CONTEXT=1 bun tools/holdout/reveal.ts ... --key-stdin\n` +
        `Stdin, not argv or env: ps shows both of those to any same-user process.`);
  }
  let keyLine = "";
  try { keyLine = readFileSync(0, "utf8").split("\n")[0].trim(); } catch { keyLine = ""; }
  if (!KEY_HEX.test(keyLine)) {
    die(`reveal refused (pack NOT spent): stdin did not carry a 64-hex answer key.`);
  }
  let expectedText = "";
  try {
    expectedText = decryptExpected(readFileSync(join(packDir, ENC_NAME)), keyLine).toString("utf8");
  } catch (e: any) {
    die(`reveal refused (pack NOT spent): ${ENC_NAME} did not decrypt — wrong key, or the\n` +
        `ciphertext was modified (GCM authenticates every byte). ${String(e?.message ?? e)}`);
  }
  const expected = JSON.parse(expectedText) as Record<string, Expected>;

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
    const rawExpected = expectedText;   // the DECRYPTED bytes — the only copy that exists (T1)
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
  const bundlePreExisted = existsSync(bundleDirEarly);

  // ---- the attempt chain: verify READ-ONLY, before anything is created ------
  // Order matters (found by this suite's own T3 test): these checks used to sit
  // after the bundle directory and the lock existed, so a refusal here left an
  // EMPTY pre-existing bundle behind, and the next attempt was refused for the
  // wrong reason ("no attempts.log"). Everything below is a read; the appends
  // happen only after the lock is held.
  // A held lock outranks every other refusal about this bundle: if another
  // reveal is mid-run, its bundle legitimately exists and half-written state
  // must not be diagnosed as tampering. Read-only peek here; the atomic "wx"
  // acquisition below remains the authoritative gate.
  const lockPath = join(bundleDirEarly, ".reveal.lock");
  if (existsSync(lockPath)) {
    die(
      `reveal refused: ${lockPath} exists, so another reveal of ${id} holds the lock.\n` +
      `Two concurrent reveals would spend one pack and disagree about which candidate ran it.\n` +
      `If no reveal is running, a previous one died mid-run: read the lock file, work out what\n` +
      `actually happened to the pack, and remove it by hand. This is deliberately not automatic.`,
    );
  }
  const attemptsPath = join(bundleDirEarly, "attempts.log");
  if (bundlePreExisted && !existsSync(attemptsPath)) {
    die(`reveal refused: ${bundleDirEarly} already existed but holds no attempts.log.\n` +
        `Every reveal writes its attempt line BEFORE running anything, so a pre-existing\n` +
        `bundle without the log has had it deleted. The attempt history is evidence;\n` +
        `remove the whole directory by hand if a reset is truly intended — THAT act is\n` +
        `the stated limit of this record, and it is at least an act, not an edit.`);
  }
  const verifyChain = (lines: string[], what: string): string => {
    let prevHash = "GENESIS";
    for (const [i, line] of lines.entries()) {
      if (!line.includes(`prev=${prevHash}`)) {
        die(`reveal refused: ${what} line ${i + 1} does not chain to the line before it.\n` +
            `The log has been edited or truncated. The attempt history is evidence; repair is manual.`);
      }
      prevHash = sha256Hex(line);
    }
    return prevHash;
  };
  const bundleChainText = existsSync(attemptsPath) ? readFileSync(attemptsPath, "utf8") : null;
  if (bundleChainText !== null) verifyChain(bundleChainText.split("\n").filter(Boolean), "attempts.log");
  const anchorPath = join(ATTEMPTS_DIR, `${id}.log`);
  if (!existsSync(anchorPath)) {
    die(`reveal refused: no attempts anchor at ${anchorPath}.\n` +
        `seal.ts creates it and it is committed with the manifest, so its absence means\n` +
        `it was deleted — \`git status\` will show a tracked file missing. Restore it\n` +
        `(git checkout -- ${anchorPath}) and read it before revealing again.`);
  }
  const anchorText = readFileSync(anchorPath, "utf8");
  const anchorLines = anchorText.split("\n").filter(Boolean);
  if (!anchorLines.length || !anchorLines[0].startsWith("sealed ")) {
    die(`reveal refused: ${anchorPath} does not begin with its sealed genesis line — it was edited or rebuilt.`);
  }
  // W2 (sixth security review, EXECUTED): revealed_at lives in the pack
  // manifest, whose COMMITTED state is `revealed_at: null` by design — so two
  // seds and an rm -rf re-armed a genuinely spent pack with `git status`
  // clean, and the re-sit sealed as an innocent-looking attempt 2. "A pack
  // that can be re-run until it passes is homework, not an exam" (PRD §22
  // O43). Spentness is therefore ALSO written into the attempts chain: a
  // successful seal appends (and in a repo, commits) a `revealed ...` line,
  // which is NOT the committed-at-seal state — reverting it shows.
  if (anchorLines.some((l) => l.startsWith("revealed "))) {
    die(`reveal refused: the attempts chain for ${id} carries a "revealed" line — this pack\n` +
        `was revealed and its result sealed. Resetting revealed_at in the pack manifest\n` +
        `cannot un-spend it: the spent marker lives in the chain${inRepo ? " and in git history" : ""}.\n` +
        `A failed exam takes a NEW pack at the next version (PRD §22, O43).`);
  }
  // V1 (fifth security review, EXECUTED): the exit-handler heal is bypassed by
  // SIGKILL — a signal is not an exit — and truncating BOTH chain copies back
  // to the COMMITTED genesis line left `git status` empty, because the forged
  // state WAS the committed state. So the count is now bound to something a
  // SIGKILLed run cannot rewind: every attempt line is COMMITTED the moment it
  // is appended (below), and here the committed copy must be a PREFIX of the
  // working-tree copy. A truncated-to-genesis anchor is then SHORTER than
  // HEAD's copy, and refuses loudly. Rewriting git history remains the stated
  // universal boundary; a crash cannot un-commit.
  // `HEAD:./path` — the ./ makes the path cwd-relative for git show.
  if (inRepo) {
    let committedAnchor = "";
    try {
      committedAnchor = execFileSync("git", ["show", `HEAD:./${anchorPath}`], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
    } catch {
      die(`reveal refused: ${anchorPath} is not committed (git show HEAD:./${anchorPath} failed).\n` +
          `seal.ts creates the anchor and instructs the custodian to COMMIT it with the\n` +
          `manifest before any reveal. An uncommitted anchor cannot bind the attempt count.`);
    }
    if (!anchorText.startsWith(committedAnchor)) {
      die(`reveal refused: the attempts anchor on disk is SHORTER than (or diverged from) its\n` +
          `committed copy — HEAD:./${anchorPath} holds ${committedAnchor.split("\n").filter(Boolean).length} chained line(s),\n` +
          `the working tree holds ${anchorLines.length}. A crash cannot un-commit an attempt line, so\n` +
          `this is truncation of the attempt history (security review V1). Restore it with\n` +
          `    git checkout -- ${anchorPath}\n` +
          `then make the bundle copy agree, and read the history before revealing again.`);
    }
    // W1 (sixth security review, EXECUTED): comparing only HEAD's copy was
    // defeated by an ordinary FORWARD commit — a case committed its own
    // truncation, so HEAD's copy WAS the truncated one and the prefix held.
    // The anchor's whole commit history is the oracle: walked oldest-first,
    // every successive committed blob must be a prefix of the next. A
    // truncation commit breaks monotonic growth immediately. What remains is
    // history REWRITE (reset/rebase/filter), the stated universal boundary,
    // which reflog records.
    let commits: string[] = [];
    try {
      commits = execFileSync("git", ["log", "--format=%H", "--", anchorPath], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] })
        .trim().split("\n").filter(Boolean).reverse();
    } catch {
      die(`reveal refused: git log on ${anchorPath} failed — the anchor's history cannot be verified.`);
    }
    let prevBlob = "";
    for (const h of commits) {
      let blob = "";
      try { blob = execFileSync("git", ["show", `${h}:./${anchorPath}`], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }); }
      catch { continue; }   // the commit touched the path by deletion/rename; the prefix chain over what exists still binds
      if (!blob.startsWith(prevBlob)) {
        die(`reveal refused: the attempts anchor's COMMIT HISTORY is not append-only —\n` +
            `commit ${h.slice(0, 12)} shrank or rewrote ${anchorPath}.\n` +
            `Attempt lines only ever grow (security review W1); a commit that shortens the\n` +
            `chain is a forged reset. Read \`git log -p -- ${anchorPath}\` before touching this pack.`);
      }
      prevBlob = blob;
    }
  }
  const anchorTail = verifyChain(anchorLines, anchorPath);
  if (bundleChainText !== null && bundleChainText !== anchorText) {
    die(`reveal refused: the two copies of the attempt chain disagree.\n` +
        `  tracked anchor: ${anchorPath} (${anchorLines.length} line(s))\n` +
        `  bundle copy:    ${attemptsPath}\n` +
        `One of them was edited or reset. The attempt history is evidence; repair is manual.`);
  }
  const attemptCount = anchorLines.length;   // genesis + N-1 prior attempts -> this is attempt N

  mkdirSync(bundleDirEarly, { recursive: true });
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
  // S4 (security re-review, EXECUTED): one `rm attempts.log` reset the counter to 1
  // and the sealed record then AFFIRMED the wrong number. Two changes close what
  // can be closed: a bundle directory that exists WITHOUT its attempts log is
  // refused outright, and each line carries the sha256 of the line before it, so
  // an edited or truncated log breaks the chain and is refused too.
  //
  // T3 (third review, EXECUTED): the chain used to live ONLY in the bundle — an
  // UNTRACKED directory this tool itself creates, invisible to `git status`
  // throughout the retry loop — so one `rm -rf` reset the sealed counter to 1
  // and the record AFFIRMED it. The chain's ANCHOR now lives in a TRACKED file
  // (planning/holdouts/attempts/<id>.log), created and committed at seal time;
  // the bundle keeps a byte-identical copy. Deleting the anchor is the deletion
  // of a tracked file; resetting it to its committed genesis while the bundle
  // copy remembers is a visible disagreement, refused above.
  //
  // NARROWED LIMIT, stated: an insider who BOTH git-restores the anchor AND
  // rm -rf's the bundle still erases pre-seal history. Erasure now takes a git
  // operation on tracked content plus a deletion — not one rm — and surviving
  // history can no longer be silently renumbered. Full erasure resistance is
  // git-history territory, the boundary every file in this repository shares.

  const attemptLine = `attempt=${attemptCount} at=${new Date().toISOString()} pid=${process.pid} candidate=${candidate} prev=${anchorTail}`;
  const anchorExpectedAfter = anchorText + attemptLine + "\n";
  appendFileSync(anchorPath, attemptLine + "\n");
  // V1: committed BEFORE any case runs, so no kill at any later moment can make
  // this attempt not have happened. The commit touches ONLY the anchor (pathspec
  // commit); the tree was verified clean of everything else above. A failed
  // commit refuses — the appended line stays on disk, and the prefix check
  // still holds for the retry. HEAD moves by one anchor-only commit per
  // attempt; the candidate was verified against HEAD before this point, and
  // the next pack's candidate is simply the then-current HEAD.
  // core.hooksPath points at an empty directory (reviewer's reasoned finding,
  // sixth pass): a case from an EARLIER run could plant .git/hooks/pre-commit —
  // .git/ is invisible to every tree check — and either sabotage all future
  // anchor commits or run code inside reveal's process tree. Hooks get no say.
  const GIT_ID = ["-c", "user.email=holdout-reveal@local", "-c", "user.name=holdout-reveal", "-c", "core.hooksPath=/var/empty"];
  let ownCommitSha = "";
  if (inRepo) {
    try {
      execFileSync("git", [...GIT_ID,
        "commit", "-q", "-m", `holdout: ${id} attempt ${attemptCount}`, "--", anchorPath],
        { stdio: ["ignore", "pipe", "pipe"] });
      ownCommitSha = execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
    } catch (e: any) {
      die(`reveal refused: could not commit the attempt line to ${anchorPath} — ${String(e?.stderr ?? e?.message ?? e).trim()}\n` +
          `The attempt count is bound to git history (V1); an uncommittable anchor cannot bind it.`);
    }
  }
  // The bundle copy is the WHOLE chain, byte-identical to the anchor — one
  // hash (attempts_log_sha256, sealed in the footer) then covers both.
  writeFileSync(attemptsPath, anchorExpectedAfter);
  // U1 (fourth review, EXECUTED): a hostile case truncated BOTH copies during
  // an ABORTED run — where no post-run check ever fires — and the next reveal
  // sealed `attempt: 1` off the shortened chain, verifier's blessing included.
  // Every abort path is a die(), and die() is process.exit(), so an exit
  // handler CAN act there (unlike signals during spawnSync, measured): if the
  // chain on disk is not exactly what this process wrote, the tampered bytes
  // are preserved as evidence and the true chain is put back from memory.
  // SIGKILL still skips this — and SIGKILL already leaves a locked pack and a
  // stale lock, so that abort is loud and manual by design, never silent.
  let chainHealTarget = anchorExpectedAfter;   // grows by the spent marker after a seal (W2)
  const restoreAttempts = () => {
    for (const [path2, label] of [[anchorPath, "attempts-anchor"], [attemptsPath, "attempts-log"]] as const) {
      try {
        const now = readFileSync(path2, "utf8");
        if (now !== chainHealTarget) {
          try { writeFileSync(join(bundleDirEarly, `${label}-as-found-after-run.log`), now); } catch {}
          writeFileSync(path2, chainHealTarget);
        }
      } catch {
        try { writeFileSync(path2, chainHealTarget); } catch {}
      }
    }
  };
  process.on("exit", restoreAttempts);
  if (attemptCount > 1) {
    console.log(`note: this is reveal ATTEMPT ${attemptCount} for ${id} — earlier attempts aborted before sealing, and the sealed record will say so.`);
  }

  // ---- run, once ----------------------------------------------------------
  // F1 (security review, CRITICAL): each case is the IMPLEMENTER'S code running
  // with this process's filesystem rights, and the pack — answer key included —
  // sat at a well-known path in the same tree.
  //
  // THREE designs, two of them defeated, all on the record:
  //   v1: pack at its normal path. DEFEATED on paper (review F1): one cat.
  //   v2: pack relocated to an unguessable mkdtemp dir. DEFEATED, executed
  //       (re-review S1): the lock file published `pack_hidden_at:` at a path
  //       derived from --id, and $TMPDIR held stale hide dirs findable by glob.
  //       Its crash story was WORSE than the disease (S3, executed): a SIGTERM
  //       mid-run stranded the repo's only copy of an unrevealed pack in
  //       /var/folders — and a signal handler cannot save it, MEASURED: bun's
  //       loop is blocked inside spawnSync, so handlers never ran and the
  //       process died with the pack still outside the tree.
  //   v3, this one: the pack NEVER LEAVES ITS PLACE. Every pack file and the
  //       pack directory drop to mode 000 for the duration of the run, and
  //       their ctimes are recorded first. To read anything a case must chmod
  //       something — through the path or through a pre-made hardlink, mode
  //       lives on the inode — and chmod moves ctime, WHICH THE KERNEL OWNS.
  //       No same-user process can set ctime back. So reading is no longer
  //       silent: the post-run comparison seals `post_run_pack_untouched`.
  //
  // Crash story of v3: any kill, including SIGKILL, leaves the pack INTACT at
  // its own path, merely unreadable. Recovery is one command, printed in the
  // lock's own doctrine: chmod -R u+rwX qa-private/<id>. Nothing is ever
  // outside the repository, so nothing can be stranded.
  //
  // STATED LIMIT, unchanged: a same-user debugger can read this process's
  // memory, where the parsed expectations live. That is OS-sandbox territory;
  // PRD §22 grades the candidate, it does not imprison it.
  // ctime is recorded AFTER each chmod — the chmod itself moves ctime, so the
  // baseline must be the post-lockdown value or every comparison fails vacuously.
  const packCtimes = new Map<string, number>();
  const packModes = new Map<string, number>();
  for (const rel of files) {
    const p = join(packDir, rel);
    packModes.set(rel, lstatSync(p).mode & 0o777);
    chmodSync(p, 0o000);
    packCtimes.set(rel, lstatSync(p).ctimeMs);
  }
  const dirCtimeBefore = (() => { chmodSync(packDir, 0o000); return lstatSync(packDir).ctimeMs; })();
  let accessRestored = false;
  const restoreAccess = () => {
    if (accessRestored) return;
    accessRestored = true;
    try { chmodSync(packDir, 0o700); } catch {}
    for (const [rel, mode] of packModes) { try { chmodSync(join(packDir, rel), mode); } catch {} }
  };
  process.on("exit", restoreAccess);   // fires on die() too — die() is process.exit(1)

  const startedAt = new Date().toISOString().replace(/\.\d+Z$/, "Z");
  // S2 (security re-review, EXECUTED): every detection field used to live ONLY in
  // the bundle manifest — outside the one hash — and flipping candidate_verified
  // with sed left raw_log_sha256 identical. Every integrity fact is now written
  // into the LOG, which is what gets hashed; the bundle manifest repeats them for
  // readability and tools/holdout/verify-run-records.ts cross-checks the two.
  // T2: the log has three regions — header (trusted), cases (candidate-
  // controlled, NEVER parsed for fields), footer (trusted). The delimiters are
  // defined once in record-format.ts and verify-run-records.ts bounds every
  // field read by them: header fields before the FIRST cases delimiter, footer
  // fields after the LAST footer delimiter. A case that echoes either string
  // lands between the two and moves neither boundary.
  const log: string[] = [
    `# Holdout run record — ${id}`, `candidate: ${candidate}`, `candidate_verified: ${inRepo}`,
    `attempt: ${attemptCount}`, `started_at: ${startedAt}`,
    `hash_method: ${man.hash_method}`, `pack_sha256: ${digest}`, `expected_results_sha256: ${expDigest}`, "",
    CASES_DELIM, "",
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
    // U3 (fourth review, EXECUTED): cases used to inherit reveal's WHOLE
    // environment, and `ps -E` from inside a case dumped it — the reviewer's
    // probe printed a live third-party API key its shell happened to export.
    // Cases get a minimal environment: enough to run a shell command, nothing
    // that belongs to the QA agent.
    const r = spawnSync("/bin/sh", ["-c", c.run], {
      stdio: ["ignore", "pipe", "pipe"],
      env: {
        PATH: process.env.PATH ?? "/usr/bin:/bin",
        HOME: process.env.HOME ?? "",
        TMPDIR: process.env.TMPDIR ?? "/tmp",
      },
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
    // JSON-escaped, so the one candidate-authored string in this file cannot
    // even CONTAIN a raw newline here (T2 belt-and-braces; the refusal above
    // already guarantees it).
    log.push(`## ${c.id} [${c.class}] ${ok ? "PASS" : "FAIL"}`, `run: ${JSON.stringify(c.run)}`, `exit: ${code}`, `stdout_sha256: ${outHash}`,
             `stderr_sha256: ${sha256Hex(errBuf)}`, `stderr_bytes: ${errBuf.length}`);
    if (!ok) log.push(`reasons: ${reasons.join("; ")}`);
    log.push("");
    console.log(`  ${ok ? "PASS" : "FAIL"}  ${c.id} [${c.class}]${ok ? "" : "  — " + reasons.join("; ")}`);
  }

  // ---- verify the tripwire, restore access, then RE-VERIFY content ----------
  // Order matters: the dir ctime is sampled BEFORE restoreAccess touches modes,
  // because restoring modes moves ctime again. A changed ctime here means some
  // process chmod-ed, renamed, relinked or otherwise reached for the pack while
  // the cases were running — the kernel wrote that fact and nobody can unwrite it.
  let packUntouched = true;
  try {
    if (lstatSync(packDir).ctimeMs !== dirCtimeBefore) packUntouched = false;
  } catch { packUntouched = false; }   // the DIRECTORY itself is gone or moved
  if (packUntouched) {
    // Search permission only — enough to lstat the children, not to read them.
    // This moves the DIR's ctime, which was already compared above.
    try { chmodSync(packDir, 0o100); } catch { packUntouched = false; }
    for (const [rel, ct] of packCtimes) {
      try { if (lstatSync(join(packDir, rel)).ctimeMs !== ct) { packUntouched = false; break; } }
      catch { packUntouched = false; break; }
    }
  }
  restoreAccess();
  // F1's detection half: the pack hash and the working tree were verified BEFORE
  // the run and never re-checked, so anything a case modified stayed invisible to
  // the sealed record. Both are re-verified here and sealed into the record. A
  // failed re-check still seals — the pack IS spent; what must not happen is the
  // tampering staying off the record — and the process exits non-zero.
  // STATED LIMITS on the three checks below (re-review S5, S8 — reasoned there,
  // recorded here): they are END-OF-RUN SNAPSHOTS. A case that modifies a file
  // and restores it before the last case exits leaves them clean, and
  // `git status --porcelain` honours .gitignore, so ignored paths are invisible
  // to the tree check. And candidate_verified: true asserts only that a CLEAN
  // git checkout in this cwd has the named commit as HEAD — it does not bind
  // that repository to this project's history. Snapshots narrow the window and
  // record what they saw; they are not a movie of the run.
  let packIntactAfterRun = false;
  try {
    packIntactAfterRun =
      canonicalPackHash(packDir).digest === man.private_pack_sha256 &&
      expectedResultsHash(packDir) === man.expected_results_sha256;
  } catch { packIntactAfterRun = false; }
  // U1: the chain on disk must be EXACTLY what this process wrote — pre-run
  // text plus its own appended line, both copies. A mismatch is sealed as
  // tampering, the found bytes are preserved, and the true chain is restored
  // (the same restore the exit handler performs on abort paths).
  let attemptsIntactAfterRun = true;
  for (const p2 of [anchorPath, attemptsPath]) {
    try { if (readFileSync(p2, "utf8") !== anchorExpectedAfter) attemptsIntactAfterRun = false; }
    catch { attemptsIntactAfterRun = false; }
  }
  if (!attemptsIntactAfterRun) restoreAttempts();
  // W4 (sixth security review, EXECUTED): a case that COMMITTED its own edit
  // of a tracked file read as a clean tree — modify-then-commit is easier than
  // modify-then-restore, and V1's per-attempt anchor commits made mid-run HEAD
  // movement look routine. HEAD after the cases must be exactly the commit
  // reveal itself made before them.
  let headUnchangedDuringRun: "true" | "false" | "unverified" = "unverified";
  if (inRepo) {
    try {
      headUnchangedDuringRun = execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim() === ownCommitSha ? "true" : "false";
    } catch { headUnchangedDuringRun = "false"; }
  }
  let treeCleanAfterRun: "true" | "false" | "unverified" = "unverified";
  if (inRepo) {
    // Filtered exactly like the pre-run check — except the anchor, which is
    // only excluded while its content matches what reveal itself wrote (U1).
    try { treeCleanAfterRun = gitDirtyFiltered(id, attemptsIntactAfterRun).trim() === "" ? "true" : "false"; }
    catch { treeCleanAfterRun = "false"; }
  }
  // F6: what gets stamped is the text validated BEFORE the run. If the file on
  // disk changed while cases were running, that is recorded as tampering.
  const manifestOnDiskNow = readFileSync(mPath, "utf8");
  const manifestRewrittenDuringRun = manifestOnDiskNow !== preRunManifestText;
  if (manifestRewrittenDuringRun) {
    // The rewrite is about to be DISCARDED by the stamp below, so preserve what
    // was found — the attacker's own text is the best evidence of the attack.
    writeFileSync(join(EVIDENCE_ROOT, `EVB-${id}`, "manifest-as-found-after-run.yaml"), manifestOnDiskNow);
  }

  // U2 (fourth review, EXECUTED): the bundle directory was a write-anything
  // blind zone — a case planted a SECOND holdout-run-*.log in a sealed bundle
  // and the verifier said nothing, because it only inspected leftovers when
  // the manifest was MISSING. The bundle's contents are censused here, before
  // the log and manifest are written: everything reveal itself created is
  // expected; anything else is a planted file, sealed as tampering.
  const bundleExpectedFiles = new Set(["attempts.log", ".reveal.lock"]);
  if (manifestRewrittenDuringRun) bundleExpectedFiles.add("manifest-as-found-after-run.yaml");
  if (!attemptsIntactAfterRun) {
    bundleExpectedFiles.add("attempts-anchor-as-found-after-run.log");
    bundleExpectedFiles.add("attempts-log-as-found-after-run.log");
  }
  let bundleExtraFiles: string[] = [];
  try { bundleExtraFiles = readdirSync(join(EVIDENCE_ROOT, `EVB-${id}`)).filter((f) => !bundleExpectedFiles.has(f)).sort(); }
  catch { bundleExtraFiles = ["(bundle directory unreadable)"]; }
  const bundleCleanAfterRun = bundleExtraFiles.length === 0;

  // ---- seal, as produced --------------------------------------------------
  const finishedAt = new Date().toISOString().replace(/\.\d+Z$/, "Z");
  const bundle = `EVB-${id}`;
  const bundleDir = join(EVIDENCE_ROOT, bundle);
  mkdirSync(bundleDir, { recursive: true });
  // finishedAt is second-precision for readability; the FILENAME carries
  // milliseconds, because two runs in the same second previously produced the
  // same name and one raw log was silently overwritten.
  const logName = `holdout-run-${new Date().toISOString().replace(/[-:.]/g, "")}.log`;
  // Hash the chain reveal ITSELF wrote (held in memory), never a re-read: a
  // case that rewrote the file mid-run must not choose what gets sealed (U1).
  const attemptsTail = sha256Hex(anchorExpectedAfter);
  const logText = log.concat([
    FOOTER_DELIM,
    `post_run_pack_intact: ${packIntactAfterRun}`,
    `post_run_tree_clean: ${treeCleanAfterRun}`,
    `post_run_tree_clean_semantics: ${TREE_CLEAN_SEMANTICS}`,
    `head_unchanged_during_run: ${headUnchangedDuringRun}`,
    `manifest_rewritten_during_run: ${manifestRewrittenDuringRun}`,
    `post_run_pack_untouched: ${packUntouched}`,
    `post_run_attempts_intact: ${attemptsIntactAfterRun}`,
    `attempts_anchor_committed: ${inRepo}`,
    `post_run_bundle_clean: ${bundleCleanAfterRun}`,
    // JSON-escaped: a planted FILENAME may contain newlines, and this line
    // lives in the trusted footer (T2) — it must stay one line.
    `bundle_extra_files: ${JSON.stringify(bundleExtraFiles)}`,
    `attempts_log_sha256: ${attemptsTail}`,
    `finished_at: ${finishedAt}`, `result: ${pass} PASS / ${fail} FAIL of ${cases.length}`,
  ]).join("\n") + "\n";
  writeFileSync(join(bundleDir, logName), logText);
  const logHash = sha256Hex(logText);
  writeFileSync(join(bundleDir, "manifest.yaml"),
    [`artifact_type: HoldoutRunRecord`, `id: ${bundle}`, `holdout_id: ${id}`, `candidate: ${candidate}`,
     `candidate_verified: ${inRepo}`, `attempt: ${attemptCount}`,
     `started_at: "${startedAt}"`, `finished_at: "${finishedAt}"`, `case_count: ${cases.length}`,
     `pass: ${pass}`, `fail: ${fail}`, `raw_log: ${logName}`, `raw_log_sha256: "${logHash}"`,
     `post_run_pack_intact: ${packIntactAfterRun}`,
     `post_run_tree_clean: ${treeCleanAfterRun}`,
     `post_run_tree_clean_semantics: ${TREE_CLEAN_SEMANTICS}`,
     `head_unchanged_during_run: ${headUnchangedDuringRun}`,
     `manifest_rewritten_during_run: ${manifestRewrittenDuringRun}`,
     `post_run_pack_untouched: ${packUntouched}`,
     `post_run_attempts_intact: ${attemptsIntactAfterRun}`,
     `attempts_anchor_committed: ${inRepo}`,
     `post_run_bundle_clean: ${bundleCleanAfterRun}`,
     `attempts_log_sha256: "${attemptsTail}"`,
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

  // W2: the SPENT marker, in the chain itself. `revealed_at:` lives in a file
  // whose committed state is null, so reverting it is invisible to git; this
  // line is appended only when a seal actually happened, so its removal is a
  // shrink of committed history (W1 walk) or a visible working-tree edit.
  const revealedLine = `revealed at=${finishedAt} raw_log_sha256=${logHash} prev=${sha256Hex(attemptLine)}`;
  const chainFinal = anchorExpectedAfter + revealedLine + "\n";
  appendFileSync(anchorPath, revealedLine + "\n");
  writeFileSync(attemptsPath, chainFinal);
  chainHealTarget = chainFinal;   // the exit-handler heal must not erase the spent marker
  let spentCommitFailed = false;
  if (inRepo) {
    try {
      execFileSync("git", [...GIT_ID, "commit", "-q", "-m", `holdout: ${id} revealed`, "--", anchorPath], { stdio: ["ignore", "pipe", "pipe"] });
    } catch {
      spentCommitFailed = true;
      console.log(`WARNING: the spent marker could not be COMMITTED — it exists only in the working tree. Commit ${anchorPath} by hand.`);
    }
  }

  console.log(`\n${pass} PASS / ${fail} FAIL of ${cases.length}. Sealed at ${join(bundleDir, logName)}`);
  const tampered = !packIntactAfterRun || treeCleanAfterRun === "false" || manifestRewrittenDuringRun || !packUntouched
    || !attemptsIntactAfterRun || !bundleCleanAfterRun || headUnchangedDuringRun === "false";
  if (tampered) {
    console.log(`TAMPERING RECORDED: pack_intact=${packIntactAfterRun} pack_untouched=${packUntouched} tree_clean=${treeCleanAfterRun} manifest_rewritten=${manifestRewrittenDuringRun} attempts_intact=${attemptsIntactAfterRun} bundle_clean=${bundleCleanAfterRun} head_unchanged=${headUnchangedDuringRun}.`);
    console.log(`The run is sealed AS PRODUCED, the pack is spent, and this verdict must not be trusted.`);
  }
  console.log(fail ? `FAIL is the result. It stands. A fix needs a new pack at the next version.` : tampered ? `Cases passed, but see the tampering record above.` : `All cases passed.`);
  // Exit non-zero on failure so a caller that checks the EXIT CODE and not the
  // tally sees it — a suite that throws mid-run still prints "N/N passed".
  return fail || tampered || spentCommitFailed ? 1 : 0;
}

process.exit(main());
