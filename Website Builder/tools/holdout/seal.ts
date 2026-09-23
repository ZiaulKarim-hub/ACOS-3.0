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
import { caseKeyProblems, duplicateJsonKeys } from "./json-keys.ts";
import { CASE_CLASSES, validate, type CaseClass } from "./manifest.ts";

const MANIFEST_DIR = "planning/holdouts/manifests";
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

  // ---- the pack the custodian wrote --------------------------------------
  const packDir = join(PACK_ROOT, id);
  if (!existsSync(packDir)) {
    die(
      `seal refused: no pack at ${packDir}.\n` +
      `Write the three files first: ${PACK_FILES.join(", ")}.\n` +
      `  cases.yaml     — { cases: [ { id, class, description?, run } ] }\n` +
      `  expected.json  — { "<case id>": { exit, stdout_sha256? , stdout_contains? } }\n` +
      `  README.md      — what this pack covers, and why these cases.`,
    );
  }
  for (const f of PACK_FILES) {
    if (!existsSync(join(packDir, f))) die(`seal refused: ${packDir}/${f} is missing.`);
  }

  const casesText = readFileSync(join(packDir, "cases.yaml"), "utf8");
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
  const cases = ((globalThis as any).Bun.YAML.parse(casesText) as { cases: Array<{ id: string; class: string; run: string }> }).cases;
  if (!Array.isArray(cases) || cases.length === 0) die("seal refused: cases.yaml holds no cases.");
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
  if (problems.length) die(`seal refused: the manifest this would write is invalid —\n` + problems.map((p) => `    ${p.field}: ${p.message}`).join("\n"));

  mkdirSync(MANIFEST_DIR, { recursive: true });
  const outPath = join(MANIFEST_DIR, `${id}.yaml`);
  if (existsSync(outPath)) {
    die(`seal refused: ${outPath} already exists. A pack version is written once; a changed pack takes the next version.`);
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
  console.log(`\nCommit the manifest now, before implementation starts. Do NOT commit ${PACK_ROOT}/ —`);
  console.log(`.gitignore holds it out of the implementation worktree on purpose.`);
  return 0;
}

process.exit(main());
