#!/usr/bin/env bun
/**
 * seal.ts — the CUSTODIAN's side. Author a pack, hash it, publish the manifest.
 *
 * `reveal.ts` opens a sealed pack. This creates one. They are deliberately two
 * commands run by two different agents in two different contexts, because the
 * single property that makes a holdout worth anything is that the agent who
 * writes the code did not write — and cannot read — the cases.
 *
 * PRE-CODE, ALWAYS. The manifest is committed BEFORE implementation starts,
 * against the slice's stated contract, not against the code (PRD §22.1). A
 * holdout written afterwards tests what was built, which is the thing it exists
 * to avoid. This tool therefore REFUSES to seal a pack for a slice already
 * marked complete.
 *
 * Usage:
 *   bun tools/holdout/seal.ts --slice S41-gridline-overlay --story ST-12 \
 *       --contract "v1 (S41 acceptance_criteria)" [--version 1] [--require-counterexample]
 *
 * Reads the pack the custodian has already written at qa-private/HLD-<slice>-v<n>/,
 * and writes planning/holdouts/manifests/HLD-<slice>-v<n>.yaml.
 */

import { existsSync, linkSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { canonicalPackHash, expectedResultsHash, HASH_METHOD, PACK_FILES } from "./canonical-hash.ts";
import { ENC_NAME, PLAIN_NAME, encryptExpected, newKeyHex } from "./keybox.ts";
import { canonicalCasesText, caseKeyProblems, duplicateJsonKeys, caseIdCollisions, INVISIBLE_CODEPOINTS, invisibleName } from "./json-keys.ts";
import { commandValuedConfigKeys, hookCensus } from "./git-guard.ts";
import { CASE_CLASSES, validate, type CaseClass } from "./manifest.ts";

const MANIFEST_DIR = "planning/holdouts/manifests";
// T3 (security review, executed): the attempts chain used to live ONLY in the
// untracked evidence bundle, so `rm -rf` of that directory reset the sealed
// attempt counter to 1 and the record AFFIRMED it. The chain's anchor now lives
// under a TRACKED directory, created at seal time and committed with the
// manifest — deleting it shows in `git status` as the deletion of a tracked file.
const ATTEMPTS_DIR = "planning/holdouts/attempts";
const PACK_ROOT = "qa-private";
const SLICE_DIR = "planning/slices";

const arg = (n: string): string | null => {
  const i = process.argv.indexOf(n);
  return i >= 0 ? process.argv[i + 1] ?? null : null;
};
const die = (m: string): never => { console.error(m); process.exit(1); };

function main(): number {
  const slice = arg("--slice") ?? die("seal refused: --slice <slice-id> is required.");
  const story = arg("--story") ?? die("seal refused: --story <story-id> is required.");
  const contract = arg("--contract") ?? die("seal refused: --contract <text> is required.\nThe pack is written against a NAMED contract version; without one, a later reader\ncannot tell which statement of the requirements the cases were derived from.");
  const version = arg("--version") ?? "1";
  const requireCounterexample = process.argv.includes("--require-counterexample");
  const id = `HLD-${slice}-v${version}`;

  // ---- pre-code check -----------------------------------------------------
  const slicePath = join(SLICE_DIR, `${slice}.yaml`);
  if (existsSync(slicePath)) {
    const st = /^status:\s*"?([a-z]+)"?/m.exec(readFileSync(slicePath, "utf8"));
    if (st && st[1] === "complete") {
      die(
        `seal refused: ${slice} is already marked complete.\n` +
        `A holdout is authored PRE-CODE, against the contract, not against the finished work.\n` +
        `A pack written now would test what was built — which is the failure it exists to catch.`,
      );
    }
  } else {
    console.log(`note: no slice file at ${slicePath} — the pre-code status check is recorded as UNVERIFIED.`);
  }

  // ---- Z1 (eighth security review, EXECUTED) ------------------------------
  // seal runs in the AUTHORING WINDOW — the one moment the answer key is
  // plaintext on disk. A hostile case from an earlier reveal planted
  // core.fsmonitor in .git/config, and the custodian's next plain `git status`
  // executed it and harvested the next pack's answers. GIT_SAFE immunizes only
  // OUR git calls; the custodian's own are unprotectable — so the foothold is
  // DETECTED and sealing refuses until the repository is clean.
  {
    const badKeys = commandValuedConfigKeys();
    if (badKeys.length) {
      die(`seal refused: .git/config carries command-valued key(s) git will EXECUTE:\n` +
          badKeys.map((k) => `  ${k}`).join("\n") +
          `\nA hostile case can plant these, and they fire inside ANY git command — including\n` +
          `yours, right now, while the answer key is plaintext (security review Z1).\n` +
          `Inspect the value(s), then remove each with\n` +
          `    git config --local --unset <key>\nand seal again.`);
    }
  }

  // AA1: a hook already in the repo is a WARNING, not a refusal — a legitimate
  // repository may carry its own (this one has a post-commit). seal cannot vouch
  // for hook CONTENTS, and it runs while the answer key is plaintext, so it says
  // so loudly; reveal's before/after snapshot is the hard guarantee against a
  // hook PLANTED during a run (door 3).
  {
    const hooks = hookCensus();
    if (hooks.length) {
      console.log(`WARNING: the repository's hooks directory carries executable hook(s): ${hooks.join(", ")}.`);
      console.log(`These run on your own git commands while ${PLAIN_NAME} is still plaintext. Confirm none are`);
      console.log(`hostile before sealing — a planted hook can read the answer key on your next commit (AA1).`);
    }
  }

  // ---- write-once refusals FIRST -------------------------------------------
  // Before touching the pack at all: a re-seal of an existing version must say
  // "already exists", not stumble over the transformed pack shape the first
  // seal left behind (the plaintext is deleted in the act of sealing).
  const outPath = join(MANIFEST_DIR, `${id}.yaml`);
  const anchorPath = join(ATTEMPTS_DIR, `${id}.log`);
  if (existsSync(outPath)) {
    die(`seal refused: ${outPath} already exists. A pack version is written once; a changed pack takes the next version.`);
  }
  if (existsSync(anchorPath)) {
    die(`seal refused: ${anchorPath} already exists — an attempts anchor for ${id} was already sealed.\n` +
        `A pack version is written once; a changed pack takes the next version.`);
  }

  // ---- the pack the custodian wrote --------------------------------------
  const packDir = join(PACK_ROOT, id);
  if (!existsSync(packDir)) {
    die(
      `seal refused: no pack at ${packDir}.\n` +
      `Write the three files first: cases.yaml, ${PLAIN_NAME}, README.md.\n` +
      `  cases.yaml     — { cases: [ { id, class, description?, run } ] }\n` +
      `  ${PLAIN_NAME}  — { "<case id>": { exit, stdout_sha256? , stdout_contains? } }\n` +
      `  README.md      — what this pack covers, and why these cases.\n` +
      `Sealing ENCRYPTS ${PLAIN_NAME} into ${ENC_NAME} and deletes the plaintext (T1);\n` +
      `the sealed pack then holds ${PACK_FILES.join(", ")}.`,
    );
  }
  // The AUTHORING shape: plaintext answer key in, ciphertext out. A pack that
  // already carries ${ENC_NAME} was sealed once (or half-sealed); this tool
  // cannot validate ciphertext it has no key for, so it refuses rather than
  // double-encrypt or trust it.
  for (const f of ["cases.yaml", PLAIN_NAME, "README.md"]) {
    if (!existsSync(join(packDir, f))) die(`seal refused: ${packDir}/${f} is missing.`);
  }
  if (existsSync(join(packDir, ENC_NAME))) {
    die(`seal refused: ${packDir}/${ENC_NAME} already exists alongside the plaintext.\n` +
        `A pack is sealed once. If a previous seal crashed half-way, its key was already\n` +
        `printed (the key prints BEFORE the plaintext is deleted); discard that key,\n` +
        `delete the stale ciphertext by hand, check the plaintext is the version you\n` +
        `mean to seal, and re-run.`);
  }

  // Raw-bytes round trip BEFORE any parse: an invalid byte decodes to U+FFFD,
  // and the canonical rewrite below would then LAUNDER the attack bytes into
  // clean UTF-8 — sealing a command the author never wrote. Refused instead,
  // for the same reason reveal refuses it (the hash pins bytes, not decodes).
  const casesRawBytes = readFileSync(join(packDir, "cases.yaml"));
  const casesText = casesRawBytes.toString("utf8");
  if (!Buffer.from(casesText, "utf8").equals(casesRawBytes)) {
    die(`seal refused: cases.yaml is not valid UTF-8 — decoding would silently replace bytes,\nand the sealed pack would not hold the bytes the author wrote.`);
  }
  // The same two ambiguity refusals reveal.ts applies, HERE, where fixing them is
  // free — at reveal time the same defect costs a spent pack (security review F9).
  {
    const yamlProblems = caseKeyProblems(casesText);
    if (yamlProblems.length) die(`seal refused: cases.yaml is ambiguous —\n  ` + yamlProblems.join("\n  "));
  }
  const rawExpected = readFileSync(join(packDir, "expected.json"), "utf8");
  {
    const dupKeys = duplicateJsonKeys(rawExpected);
    if (dupKeys.length) die(`seal refused: expected.json repeats key(s) ${dupKeys.join(", ")} — JSON keeps only the LAST one, and a pack sealed over that ambiguity is a wrong verdict waiting to happen.`);
  }
  const cases = ((globalThis as any).Bun.YAML.parse(casesText) as { cases: Array<{ id: string; class: string; run: string; description?: string }> }).cases;
  if (!Array.isArray(cases) || cases.length === 0) die("seal refused: cases.yaml holds no cases.");
  // T2 (security review, EXECUTED): a double-quoted YAML scalar with \n escapes
  // is a MULTI-LINE run string that the block-scalar refusals never see, and
  // reveal used to write it verbatim into the hashed log — where a first-match
  // field scan then read the injected line instead of the real footer. A case
  // command has no business spanning lines; refuse at authoring, where it is free.
  {
    const multiline = cases.flatMap((c) =>
      (["id", "class", "description", "run"] as const)
        .filter((k) => typeof c[k] === "string" && /[\r\n]/.test(c[k] as string))
        .map((k) => `${JSON.stringify(c.id)}: field "${k}" contains a newline`));
    if (multiline.length) {
      die(`seal refused: case string fields must be single-line —\n  ` + multiline.join("\n  ") +
          `\nAn embedded newline in a case field is a run-record injection vector (security review T2).`);
    }
    // X4 (seventh review, EXECUTED): a run string carrying U+202E sealed
    // cleanly and read REVERSED in every render of the record — a fixed point
    // of canonicalization, invisible to the structural check. Byte-level rule.
    const invisibles = cases.flatMap((c) =>
      (["id", "class", "description", "run"] as const)
        .filter((k) => typeof c[k] === "string" && INVISIBLE_CODEPOINTS.test(c[k] as string))
        .map((k) => `${JSON.stringify(c.id)}: field "${k}" carries ${invisibleName(c[k] as string)}, a bidi/invisible control codepoint`));
    if (invisibles.length) {
      die(`seal refused: case string fields may not carry bidi or zero-width codepoints —\n  ` + invisibles.join("\n  ") +
          `\nText that renders differently than it executes is a Trojan Source vector (security review X4).`);
    }
    // AA1: case ids that normalize to the same text render identically.
    const idCollisions = caseIdCollisions(cases.map((c) => String(c.id)));
    if (idCollisions.length) {
      die(`seal refused: case ids must be distinct to a reader —\n  ` + idCollisions.join("\n  ") +
          `\nUnicode-confusable ids produce run-record sections nobody can tell apart (security review AA1).`);
    }
    // W3: the canonical rewrite below keeps exactly the four known keys, so
    // anything else would be silently dropped — refused instead, and every
    // kept field must be a string (a non-string run would reach sh -c).
    const fieldProblems = cases.flatMap((c) => {
      const out: string[] = [];
      for (const k of Object.keys(c as object)) {
        if (!["id", "class", "description", "run"].includes(k)) out.push(`${JSON.stringify(c.id)}: unknown case field ${JSON.stringify(k)}`);
      }
      for (const k of ["id", "class", "run"] as const) {
        if (typeof (c as any)[k] !== "string") out.push(`${JSON.stringify(c.id)}: field "${k}" is ${typeof (c as any)[k]}, expected a string`);
      }
      if ("description" in c && typeof (c as any).description !== "string") out.push(`${JSON.stringify(c.id)}: "description" must be a string`);
      return out;
    });
    if (fieldProblems.length) die(`seal refused: cases.yaml holds fields the canonical form cannot carry —\n  ` + fieldProblems.join("\n  "));
  }
  const expected = JSON.parse(rawExpected) as Record<string, unknown>;

  const missing = cases.filter((c) => !(c.id in expected)).map((c) => c.id);
  if (missing.length) die(`seal refused: no expected result for ${missing.join(", ")}.`);
  const orphan = Object.keys(expected).filter((k) => !cases.some((c) => c.id === k));
  if (orphan.length) die(`seal refused: expected.json holds results for cases that do not exist: ${orphan.join(", ")}.`);

  const classes = [...new Set(cases.map((c) => c.class))] as CaseClass[];
  const unknown = classes.filter((c) => !CASE_CLASSES.includes(c));
  if (unknown.length) die(`seal refused: unknown case class(es) ${unknown.join(", ")}. Known: ${CASE_CLASSES.join(", ")}.`);

  if (requireCounterexample && !classes.includes("counterexample")) {
    die(
      `seal refused: this pack needs a \`counterexample\` case — one the slice must FAIL, and fail correctly.\n` +
      `A suite made only of cases that should pass cannot distinguish a working gate from a gate that\n` +
      `approves everything (PRD §22.2).`,
    );
  }

  // ---- seal the answer key: plaintext in memory, ciphertext on disk (T1) --
  // From here to the end, any failure RESTORES the plaintext so the custodian
  // is never left with a half-sealed pack and no key.
  // W3: the sealed cases.yaml IS the canonical serialization of its parse —
  // reveal refuses any deviation, so no YAML spelling can make a reader and
  // the harness disagree inside a sealed pack. The authored bytes are kept in
  // memory and restored if anything below refuses.
  const casesOriginalBytes = readFileSync(join(packDir, "cases.yaml"));
  const casesCanonical = canonicalCasesText(casesText);
  if (casesCanonical !== casesText) {
    writeFileSync(join(packDir, "cases.yaml"), casesCanonical);
    console.log(`note: cases.yaml was rewritten into canonical form (comments dropped, values JSON-quoted).`);
    console.log(`      REVIEW the sealed file — it is what auditors and the harness will both read.`);
  }
  const plainBytes = readFileSync(join(packDir, PLAIN_NAME));
  const keyHex = newKeyHex();
  writeFileSync(join(packDir, ENC_NAME), encryptExpected(plainBytes, keyHex));
  // V3 (fifth security review): the key used to print at the very END, after
  // the plaintext was deleted — so a kill landing between the two left a pack
  // whose ciphertext no one could ever open. The key prints BEFORE the
  // deletion: a crash after this line loses nothing (the plaintext, the
  // ciphertext and the printed key all still exist), and a refusal below
  // restores the plaintext, after which this key should simply be discarded.
  console.log(`ANSWER KEY for ${id} — shown ONCE, stored NOWHERE by this tool:`);
  console.log(`  WB_HOLDOUT_KEY=${keyHex}`);
  console.log(`(printed before the plaintext is deleted, so no crash can strand an unopenable pack;`);
  console.log(` if this seal REFUSES below, the plaintext is restored and this key is void)`);
  rmSync(join(packDir, PLAIN_NAME));
  const restorePlain = () => {
    try { writeFileSync(join(packDir, PLAIN_NAME), plainBytes); } catch {}
    try { rmSync(join(packDir, ENC_NAME), { force: true }); } catch {}
    try { writeFileSync(join(packDir, "cases.yaml"), casesOriginalBytes); } catch {}
  };

  // ---- hash and publish ---------------------------------------------------
  const { digest, files } = canonicalPackHash(packDir);
  const expDigest = expectedResultsHash(packDir);
  const now = new Date().toISOString().replace(/\.\d+Z$/, "Z");

  const man = {
    artifact_type: "HoldoutManifest" as const, id, parent_story_id: story,
    dev_id: slice, qa_id: `QA-${slice}`, contract_version: contract, created_at: now,
    custodian: "holdout-custodian-agent (not the implementation agent)",
    hash_method: HASH_METHOD, case_classes: classes, case_count: cases.length,
    covered_invariants: (arg("--invariants") ?? "").split(",").map((s) => s.trim()).filter(Boolean),
    private_pack_sha256: digest, expected_results_sha256: expDigest,
    revealed_at: null, run_evidence_bundle: null,
  };

  const problems = validate(man, { requireCounterexample });
  if (problems.length) {
    restorePlain();
    die(`seal refused: the manifest this would write is invalid —\n` + problems.map((p) => `    ${p.field}: ${p.message}`).join("\n"));
  }

  mkdirSync(MANIFEST_DIR, { recursive: true });
  mkdirSync(ATTEMPTS_DIR, { recursive: true });

  // ---- the tracked attempts anchor (T3), published write-once -------------
  // Same temp-then-link(2) publish as the manifest below, for the same two
  // measured reasons: atomicity and EEXIST-as-write-once in one syscall.
  const genesis = `sealed at=${now} id=${id} pack_sha256=${digest} prev=GENESIS\n`;
  const anchorTmp = join(ATTEMPTS_DIR, `.${id}.log.tmp-${process.pid}`);
  writeFileSync(anchorTmp, genesis);
  try {
    linkSync(anchorTmp, anchorPath);
  } catch (e: any) {
    rmSync(anchorTmp, { force: true });
    restorePlain();
    if (e?.code === "EEXIST") {
      die(`seal refused: ${anchorPath} already exists — an attempts anchor for ${id} was already sealed.`);
    }
    throw e;
  } finally {
    rmSync(anchorTmp, { force: true });
  }

  // Built in a sibling temp file, then PUBLISHED with link(2). Two reasons, both
  // MEASURED in review: a plain writeFileSync to outPath is not atomic, and a
  // concurrent reveal.ts read the file mid-write and refused with "(root): not a
  // mapping" (1 run in 5); and the existsSync check above is a TOCTOU race that
  // cannot be closed by checking harder. link(2) fails with EEXIST if the name is
  // already taken, so write-once and atomic-publish are the SAME operation here.
  const tmpPath = join(MANIFEST_DIR, `.${id}.yaml.tmp-${process.pid}`);
  writeFileSync(tmpPath, [
    `# PRD §22 — Holdout manifest (PUBLIC; committed BEFORE coding).`,
    `# The cases and answers are NOT here. Only their shape and their seal.`,
    `artifact_type: HoldoutManifest`,
    `id: ${man.id}`,
    `parent_story_id: ${man.parent_story_id}`,
    `dev_id: ${man.dev_id}`,
    `qa_id: ${man.qa_id}`,
    `contract_version: ${JSON.stringify(man.contract_version)}`,
    `created_at: ${JSON.stringify(man.created_at)}`,
    `custodian: ${JSON.stringify(man.custodian)}`,
    `hash_method: ${man.hash_method}   # the ONE derivation method; see tools/holdout/canonical-hash.ts`,
    `case_classes: [${man.case_classes.join(", ")}]`,
    `case_count: ${man.case_count}`,
    `covered_invariants: [${man.covered_invariants.join(", ")}]`,
    `private_pack_sha256: ${JSON.stringify(man.private_pack_sha256)}`,
    `expected_results_sha256: ${JSON.stringify(man.expected_results_sha256)}`,
    `revealed_at: null`,
    `run_evidence_bundle: null`,
    "",
  ].join("\n"));
  try {
    linkSync(tmpPath, outPath);
  } catch (e: any) {
    rmSync(tmpPath, { force: true });
    rmSync(anchorPath, { force: true });   // created THIS run; a lost race unpublishes it
    restorePlain();
    if (e?.code === "EEXIST") {
      die(`seal refused: ${outPath} already exists. A pack version is written once; a changed pack takes the next version.`);
    }
    throw e;
  } finally {
    rmSync(tmpPath, { force: true });
  }

  console.log(`sealed ${id}`);
  console.log(`  pack     ${packDir}  (${files.length} file(s): ${files.join(", ")})`);
  console.log(`  cases    ${cases.length}  [${classes.join(", ")}]`);
  console.log(`  method   ${HASH_METHOD}`);
  console.log(`  manifest ${outPath}`);
  console.log(`  attempts ${anchorPath}  (tracked; every reveal attempt chains onto it)`);
  console.log(`\nThe ANSWER KEY was printed above, before the plaintext was deleted (V3).`);
  console.log(`Store it OUTSIDE this repository (T1: anything on disk here, a same-user`);
  console.log(`process can read). reveal.ts will ask for it on stdin (--key-stdin).`);
  console.log(`Anyone holding this key AND the pack can read the answers; losing it means`);
  console.log(`the pack can never be revealed and must be re-sealed at the next version.`);
  console.log(`\nCommit the manifest AND the attempts anchor now, before implementation starts.`);
  console.log(`Do NOT commit ${PACK_ROOT}/ — .gitignore holds it out of the implementation`);
  console.log(`worktree on purpose.`);
  return 0;
}

process.exit(main());
