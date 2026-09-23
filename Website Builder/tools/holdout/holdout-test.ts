#!/usr/bin/env bun
/**
 * holdout-test.ts — S79's own layer-1 verification.
 *
 * Expect 71/71. Raised from 68 on 2026-09-22 after a review DEFEATED the
 * duplicate-key guard: it was built from a regex whose escape a patch tool had
 * corrupted, so any case id holding a regex metacharacter slipped past. EVERY id in
 * this suite was alphanumeric, which is why nothing here could see it. Three cases
 * now use metacharacter ids on both sides of the guard.
 *
 * Previously raised from 62 to 68: the third review PASSED but named
 * items it never reached. Probing them found two more defects — a repeated case id
 * ran twice and sealed, and a repeated expected.json key graded silently against
 * the LAST one. Six cases cover those, seal-side orphan expectations, and scale.
 *
 * Previously raised from 54 to 62 after a THIRD QA review returned
 * REJECT: eight cases cover attribution in a zero-commit repo and a detached HEAD,
 * and a byte-exact stdout_contains.
 *
 * Previously raised from 51 to 54: mutation testing showed the
 * two-process race check passes even with the lock REMOVED, because the two
 * processes did not overlap inside this suite. Three deterministic cases hold the
 * lock directly instead. The race check is kept as an integration signal.
 *
 * Previously raised from 42 to 51 after a SECOND QA review returned
 * REJECT: nine cases cover a concurrency race, unverified candidate attribution,
 * malformed expectations that ran side effects, a non-UTF-8 cases.yaml, and a
 * census that crashed on a directory.
 *
 * Previously raised from 39 to 42 after the first QA review returned REJECT:
 * three cases cover the raw-byte digest and the write-once run record.
 *
 * Previously raised from 34 to 39 the same day: five cases were added to cover
 * the three confirmed defects fixed that day — the 1 MiB stdout limit, the
 * missing per-case timeout, and symlinks inside a pack.
 *
 * An expected total is what makes a SHRINKING suite a failure
 * rather than a faster green run. If you add a case, move this number by hand
 * and say why — a total that follows the suite is not a total.
 *
 * ALWAYS CHECK THE EXIT CODE, NOT THE TALLY: a suite that throws mid-run still
 * prints "N/N passed". This file exits non-zero on any failure and on any throw.
 *
 * Usage: bun tools/holdout/holdout-test.ts
 */

import { execFileSync } from "node:child_process";
import { chmodSync, linkSync, lstatSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, symlinkSync, utimesSync, writeFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { canonicalPackHash, expectedResultsHash, sha256Hex, HASH_METHOD } from "./canonical-hash.ts";
import { validate } from "./manifest.ts";
import { duplicateJsonKeys } from "./json-keys.ts";

let pass = 0, fail = 0;
const ok = (name: string, cond: boolean, detail = "") => {
  cond ? pass++ : fail++;
  console.log(`  ${cond ? "PASS" : "FAIL"}  ${name}${cond || !detail ? "" : "  — " + detail}`);
};

const tmp = mkdtempSync(join(tmpdir(), "wb-holdout-"));
const packDir = join(tmp, "qa-private", "HLD-S99-v1");
mkdirSync(packDir, { recursive: true });
const write = (n: string, s: string) => writeFileSync(join(packDir, n), s);
write("README.md", "# test pack\n");
write("cases.yaml", "cases:\n  - id: H001\n    class: nominal\n    run: \"echo hello\"\n  - id: H002\n    class: counterexample\n    run: \"exit 3\"\n");
write("expected.json", JSON.stringify({ H001: { exit: 0, stdout_contains: "hello" }, H002: { exit: 3 } }, null, 2) + "\n");

console.log("— canonical hash —");
const a = canonicalPackHash(packDir);
const b = canonicalPackHash(packDir);
ok("deterministic across two runs", a.digest === b.digest);
ok("lists all three pack files, sorted", a.files.join(",") === "README.md,cases.yaml,expected.json", a.files.join(","));

// THE property. R2P's tar-based hash embeds mtime, which is why its packs need a
// normalised mtime (`touch -t 202608060000`) for the hash to be stable at all.
const old = new Date(2020, 0, 1);
for (const f of a.files) utimesSync(join(packDir, f), old, old);
ok("mtime change does NOT move the digest", canonicalPackHash(packDir).digest === a.digest);

const before = readFileSync(join(packDir, "README.md"), "utf8");
write("README.md", before + "x");
ok("a content change DOES move the digest", canonicalPackHash(packDir).digest !== a.digest);
write("README.md", before);
ok("restoring the content restores the digest", canonicalPackHash(packDir).digest === a.digest);

const shasum = execFileSync("/bin/sh", ["-c", `shasum -a 256 "${join(packDir, "expected.json")}" | cut -d' ' -f1`], { encoding: "utf8" }).trim();
ok("expected_results_sha256 equals `shasum -a 256 expected.json`", expectedResultsHash(packDir) === shasum, `${expectedResultsHash(packDir)} vs ${shasum}`);

console.log("— manifest validation —");
const good = {
  artifact_type: "HoldoutManifest", id: "HLD-S99-v1", parent_story_id: "ST-99",
  dev_id: "S99-example", qa_id: "QA-S99", contract_version: "v1", created_at: "2026-09-22T00:00:00Z",
  custodian: "holdout-custodian-agent (not the implementation agent)", hash_method: HASH_METHOD,
  case_classes: ["nominal", "counterexample"], case_count: 2, covered_invariants: ["INV-1"],
  private_pack_sha256: a.digest, expected_results_sha256: expectedResultsHash(packDir),
  revealed_at: null, run_evidence_bundle: null,
};
ok("a well-formed manifest validates clean", validate(good).length === 0, JSON.stringify(validate(good)));
const withField = (k: string, v: unknown) => validate({ ...good, [k]: v });
ok("refuses an unknown hash_method", withField("hash_method", "tar-v2").some((p) => p.field === "hash_method"));
ok("refuses a local-offset timestamp", withField("created_at", "2026-09-22T00:00:00+02:00").some((p) => p.field === "created_at"));
ok("accepts fractional seconds on revealed_at", withField("revealed_at", "2026-09-22T00:00:00.123Z").filter((p) => p.field === "revealed_at").length === 0);
ok("refuses revealed_at that is neither null nor a timestamp", withField("revealed_at", "yes").some((p) => p.field === "revealed_at"));
ok("refuses a revealed manifest with no evidence bundle", validate({ ...good, revealed_at: "2026-09-22T00:00:00Z" }).some((p) => p.field === "run_evidence_bundle"));
ok("refuses an id whose slice disagrees with dev_id", withField("dev_id", "S41-gridline").some((p) => p.field === "id"));
ok("refuses a custodian that names the implementer", withField("custodian", "the implementation agent").some((p) => p.field === "custodian"));
ok("requires a counterexample case when asked", validate({ ...good, case_classes: ["nominal"] }, { requireCounterexample: true }).some((p) => p.field === "case_classes"));
ok("refuses a malformed sha256", withField("private_pack_sha256", "abc").some((p) => p.field === "private_pack_sha256"));

console.log("— reveal, end to end —");
const repoRoot = tmp;
mkdirSync(join(repoRoot, "planning/holdouts/manifests"), { recursive: true });
const yaml = Object.entries(good).map(([k, v]) =>
  `${k}: ${v === null ? "null" : Array.isArray(v) ? `[${v.join(", ")}]` : typeof v === "number" ? v : JSON.stringify(v)}`).join("\n") + "\n";
writeFileSync(join(repoRoot, "planning/holdouts/manifests/HLD-S99-v1.yaml"), yaml);
const TOOL = join(process.cwd(), "tools/holdout/reveal.ts");
// The fixture root is deliberately NOT a git repository, and reveal now REFUSES
// that state unless --allow-unverified-candidate is passed (security review F2).
// The helper passes the flag so every existing test exercises the override path;
// the F2 tests below call the tool directly to pin the refusal itself.
const run = (env: Record<string, string>, args: string[], cwd = repoRoot) => {
  try {
    const out = execFileSync("bun", [TOOL, ...args, "--allow-unverified-candidate"], { cwd, encoding: "utf8", env: { ...process.env, ...env }, stdio: ["ignore", "pipe", "pipe"] });
    return { code: 0, out };
  } catch (e: any) { return { code: e.status ?? 1, out: String(e.stdout ?? "") + String(e.stderr ?? "") }; }
};
const gated = run({}, ["--id", "HLD-S99-v1", "--candidate", "abc1230"]);
ok("refuses without WB_QA_CONTEXT=1", gated.code !== 0 && /only in the QA review context/.test(gated.out));
const dry = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S99-v1", "--candidate", "abc1230", "--dry-run"]);
ok("--dry-run verifies both hashes and runs nothing", dry.code === 0 && /MATCH/.test(dry.out) && /NOT run/.test(dry.out), dry.out.slice(-200));
ok("--dry-run leaves revealed_at untouched", /revealed_at: null/.test(readFileSync(join(repoRoot, "planning/holdouts/manifests/HLD-S99-v1.yaml"), "utf8")));

write("README.md", before + "tampered");
const mism = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S99-v1", "--candidate", "abc1230"]);
ok("a tampered pack refuses and runs NOTHING", mism.code !== 0 && /MISMATCH/.test(mism.out) && /NOTHING WAS RUN/.test(mism.out));
write("README.md", before);

const real = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S99-v1", "--candidate", "abc1230"]);
ok("a real reveal runs every case and seals a run record", real.code === 0 && /2 PASS \/ 0 FAIL/.test(real.out) && existsSync(join(repoRoot, "planning/evidence/EVB-HLD-S99-v1/manifest.yaml")), real.out.slice(-300));
const spent = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S99-v1", "--candidate", "abc1230"]);
ok("a revealed pack is SPENT and refuses a second run", spent.code !== 0 && /already revealed/.test(spent.out));

console.log("— seal, the custodian side —");
const SEAL = join(process.cwd(), "tools/holdout/seal.ts");
const seal = (args: string[], cwd = repoRoot) => {
  try { return { code: 0, out: execFileSync("bun", [SEAL, ...args], { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }) }; }
  catch (e: any) { return { code: e.status ?? 1, out: String(e.stdout ?? "") + String(e.stderr ?? "") }; }
};

// manualSeal writes a manifest directly, BYPASSING seal.ts. seal now refuses
// ambiguous packs at authoring time (F9), but reveal's guards must hold even
// against a manifest a compliant seal would never have produced — a hand-written
// or older-tool manifest is exactly the adversarial input reveal exists to survive.
const manualSeal = (id2: string, dir2: string, caseCount = 1) => {
  const m = /^HLD-(S\d+)[A-Za-z0-9-]*-v(\d+)$/.exec(id2)!;
  const g: Record<string, unknown> = { ...good, id: id2, parent_story_id: "ST-" + m[1].slice(1),
    dev_id: m[1] + "-x", qa_id: "QA-" + m[1], contract_version: "v" + m[2],
    case_classes: ["nominal"], case_count: caseCount, covered_invariants: ["INV-1"],
    private_pack_sha256: canonicalPackHash(dir2).digest,
    expected_results_sha256: expectedResultsHash(dir2),
    revealed_at: null, run_evidence_bundle: null };
  const y = Object.entries(g).map(([k, v]) =>
    `${k}: ${v === null ? "null" : Array.isArray(v) ? `[${v.join(", ")}]` : typeof v === "number" ? v : JSON.stringify(v)}`).join("\n") + "\n";
  writeFileSync(join(repoRoot, "planning/holdouts/manifests", id2 + ".yaml"), y);
};

// A fresh pack for the round trip — the first one is spent by the reveal above.
const rtId = "HLD-S98-v1";
const rtDir = join(repoRoot, "qa-private", rtId);
mkdirSync(rtDir, { recursive: true });
writeFileSync(join(rtDir, "README.md"), "# round trip\n");
writeFileSync(join(rtDir, "cases.yaml"), "cases:\n  - id: H001\n    class: nominal\n    run: \"echo ok\"\n  - id: H002\n    class: counterexample\n    run: \"exit 7\"\n");
writeFileSync(join(rtDir, "expected.json"), JSON.stringify({ H001: { exit: 0, stdout_contains: "ok" }, H002: { exit: 7 } }, null, 2) + "\n");

const s1 = seal(["--slice", "S98", "--story", "ST-98", "--contract", "v1 (S98)", "--require-counterexample"]);
ok("seal writes a manifest with revealed_at null", s1.code === 0 && /revealed_at: null/.test(readFileSync(join(repoRoot, "planning/holdouts/manifests", rtId + ".yaml"), "utf8")), s1.out.slice(-200));
const s2 = seal(["--slice", "S98", "--story", "ST-98", "--contract", "v1 (S98)"]);
ok("seal refuses to overwrite an existing manifest version", s2.code !== 0 && /already exists/.test(s2.out));

// counterexample enforcement, on a pack that deliberately lacks one
const noCex = join(repoRoot, "qa-private", "HLD-S97-v1");
mkdirSync(noCex, { recursive: true });
writeFileSync(join(noCex, "README.md"), "#\n");
writeFileSync(join(noCex, "cases.yaml"), "cases:\n  - id: H001\n    class: nominal\n    run: \"true\"\n");
writeFileSync(join(noCex, "expected.json"), JSON.stringify({ H001: { exit: 0 } }) + "\n");
const s3 = seal(["--slice", "S97", "--story", "ST-97", "--contract", "v1", "--require-counterexample"]);
ok("seal refuses a pack with no counterexample when one is required", s3.code !== 0 && /counterexample/.test(s3.out));
const s4 = seal(["--slice", "S97", "--story", "ST-97", "--contract", "v1"]);
ok("...and allows it when one is not required", s4.code === 0, s4.out.slice(-160));

// pre-code guard
mkdirSync(join(repoRoot, "planning/slices"), { recursive: true });
writeFileSync(join(repoRoot, "planning/slices/S96.yaml"), 'slice_id: "S96"\nstatus: "complete"\n');
const s5 = seal(["--slice", "S96", "--story", "ST-96", "--contract", "v1"]);
ok("seal refuses a slice already marked complete", s5.code !== 0 && /already marked complete/.test(s5.out));

// the round trip that matters: sealed by one tool, opened by the other
const rt = run({ WB_QA_CONTEXT: "1" }, ["--id", rtId, "--candidate", "cafe011"]);
ok("a sealed pack reveals cleanly — seal and reveal agree on the hash", rt.code === 0 && /2 PASS \/ 0 FAIL/.test(rt.out), rt.out.slice(-300));

// a FAILING pack must exit non-zero and keep its result
const failDir = join(repoRoot, "qa-private", "HLD-S95-v1");
mkdirSync(failDir, { recursive: true });
writeFileSync(join(failDir, "README.md"), "#\n");
writeFileSync(join(failDir, "cases.yaml"), "cases:\n  - id: H001\n    class: nominal\n    run: \"exit 1\"\n");
writeFileSync(join(failDir, "expected.json"), JSON.stringify({ H001: { exit: 0 } }) + "\n");
seal(["--slice", "S95", "--story", "ST-95", "--contract", "v1"]);
const bad = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S95-v1", "--candidate", "cafe022"]);
ok("a failing pack exits NON-ZERO", bad.code !== 0, `exit ${bad.code}`);
// "Sealed, not discarded" is TWO claims: the count is recorded machine-readably,
// AND the reason survives verbatim. A record that says `fail: 1` without saying
// WHY is a tally, and a tally is the thing this whole suite distrusts.
const evbDir = join(repoRoot, "planning/evidence/EVB-HLD-S95-v1");
const evb = readFileSync(join(evbDir, "manifest.yaml"), "utf8");
ok("...the failure count is sealed machine-readably", /^fail: 1$/m.test(evb) && /^pass: 0$/m.test(evb), evb.slice(0, 160));
const rawName = (/^raw_log: (.+)$/m.exec(evb) ?? [])[1] ?? "";
const raw = rawName ? readFileSync(join(evbDir, rawName), "utf8") : "";
ok("...the raw log is named, present, and keeps the REASON verbatim", /exit 1 != 0/.test(raw) && /0 PASS \/ 1 FAIL of 1/.test(raw), rawName || "(no raw_log field)");
const rawHash = (/^raw_log_sha256: "([0-9a-f]{64})"$/m.exec(evb) ?? [])[1] ?? "";
ok("...and the raw log's own hash is recorded and correct", rawHash === sha256Hex(raw), `${rawHash.slice(0, 16)}… vs ${sha256Hex(raw).slice(0, 16)}…`);

// the census
const vOut = (() => { try { return execFileSync("bun", [join(process.cwd(), "tools/holdout/verify-manifests.ts"), "--expect", "4"], { cwd: repoRoot, encoding: "utf8" }); } catch (e: any) { return String(e.stdout ?? ""); } })();
ok("verify-manifests accepts the true census and reports the revealed ones", /4 manifest\(s\): 4 ok, 0 failed/.test(vOut), vOut.slice(-200));
const vBad = (() => { try { execFileSync("bun", [join(process.cwd(), "tools/holdout/verify-manifests.ts"), "--expect", "99"], { cwd: repoRoot, encoding: "utf8" }); return "exit0"; } catch (e: any) { return String(e.stdout ?? ""); } })();
ok("verify-manifests FAILS on a census that disagrees", /expected 99 manifest/.test(vBad));


console.log("— harness limits must never become verdicts —");

// MEASURED, 12/12 deterministic on bun 1.3.9: with node's DEFAULT 1 MiB
// maxBuffer, a case writing 2 MiB has its stdout TRUNCATED and its exit status
// replaced by 1. A passing case is then recorded as FAIL on an exam that is
// spent the moment it is revealed. At exactly 1,048,577 bytes execFileSync
// throws too, but stdout survives intact and status is 0 — harmless. 2 MiB is
// the smallest size tested at which the verdict is actually corrupted.
const bigId = "HLD-S94-v1";
const bigDir = join(repoRoot, "qa-private", bigId);
mkdirSync(bigDir, { recursive: true });
writeFileSync(join(bigDir, "README.md"), "# big stdout\n");
writeFileSync(join(bigDir, "cases.yaml"),
  "cases:\n  - id: H001\n    class: nominal\n    run: \"printf '%*s' 2097152 ''\"\n");
writeFileSync(join(bigDir, "expected.json"), JSON.stringify({ H001: { exit: 0 } }) + "\n");
seal(["--slice", "S94", "--story", "ST-94", "--contract", "v1"]);
const big = run({ WB_QA_CONTEXT: "1" }, ["--id", bigId, "--candidate", "cafe033"]);
ok("a case writing 2 MiB to stdout still PASSES (the 1 MiB default would false-FAIL it)",
   big.code === 0 && /1 PASS \/ 0 FAIL/.test(big.out), big.out.slice(-220));

// A hanging case must ABORT the reveal and leave the pack UNSPENT, because a
// timeout is a property of the harness, not an answer about the code.
const hangId = "HLD-S93-v1";
const hangDir = join(repoRoot, "qa-private", hangId);
mkdirSync(hangDir, { recursive: true });
writeFileSync(join(hangDir, "README.md"), "# hang\n");
writeFileSync(join(hangDir, "cases.yaml"), "cases:\n  - id: H001\n    class: nominal\n    run: \"sleep 30\"\n");
writeFileSync(join(hangDir, "expected.json"), JSON.stringify({ H001: { exit: 0 } }) + "\n");
seal(["--slice", "S93", "--story", "ST-93", "--contract", "v1"]);
const hang = run({ WB_QA_CONTEXT: "1", WB_HOLDOUT_CASE_TIMEOUT_MS: "1500" },
                 ["--id", hangId, "--candidate", "cafe044"]);
ok("a hanging case ABORTS the reveal rather than recording a verdict",
   hang.code !== 0 && /did not finish within/.test(hang.out), hang.out.slice(-220));
ok("...and the pack is NOT spent — revealed_at stays null",
   /revealed_at: null/.test(readFileSync(join(repoRoot, "planning/holdouts/manifests", hangId + ".yaml"), "utf8")));

// A pack must be self-contained. Skipping symlinks is NOT enough: reveal.ts
// reads cases.yaml with readFileSync, which FOLLOWS links, so a skipped
// symlinked cases file would still RUN while contributing nothing to the hash.
const linkDir = join(tmp, "linkpack");
mkdirSync(linkDir, { recursive: true });
writeFileSync(join(linkDir, "README.md"), "# link\n");
writeFileSync(join(linkDir, "expected.json"), "{}\n");
writeFileSync(join(tmp, "outside-cases.yaml"), "cases: []\n");
symlinkSync(join(tmp, "outside-cases.yaml"), join(linkDir, "cases.yaml"));
let linkErr = "";
try { canonicalPackHash(linkDir); } catch (e: any) { linkErr = String(e?.message ?? e); }
ok("a pack containing a symlink is REFUSED, not silently skipped", /symlink/.test(linkErr), linkErr.slice(0, 160));
ok("...and the refusal names the offending file", /cases\.yaml/.test(linkErr), linkErr.slice(0, 160));


console.log("— the digest must be over raw bytes, and a run record is write-once —");

// QA finding 1 (CRITICAL). reveal.ts ran cases with encoding "utf8", so stdout
// was lossily decoded BEFORE hashing: any invalid byte became U+FFFD. A
// custodian writes the expectation with `shasum -a 256`, which hashes the RAW
// bytes, so a byte-exact correct answer was recorded FAIL and the pack spent on
// it. This test writes the expectation exactly as a custodian would.
const byteId = "HLD-S92-v1";
const byteDir = join(repoRoot, "qa-private", byteId);
mkdirSync(byteDir, { recursive: true });
const RUN_NON_UTF8 = "printf \"\\377\\101\"";   // emits bytes 0xFF 0x41 — 0xFF is not valid UTF-8
const custodianHash = execFileSync("/bin/sh", ["-c", RUN_NON_UTF8 + " | shasum -a 256 | cut -d' ' -f1"], { encoding: "utf8" }).trim();
writeFileSync(join(byteDir, "README.md"), "# non-utf8 stdout\n");
writeFileSync(join(byteDir, "cases.yaml"), "cases:\n  - id: H001\n    class: nominal\n    run: '" + RUN_NON_UTF8 + "'\n");
writeFileSync(join(byteDir, "expected.json"), JSON.stringify({ H001: { exit: 0, stdout_sha256: custodianHash } }) + "\n");
seal(["--slice", "S92", "--story", "ST-92", "--contract", "v1"]);
const bytes = run({ WB_QA_CONTEXT: "1" }, ["--id", byteId, "--candidate", "cafe055"]);
ok("a correct answer containing non-UTF-8 bytes PASSES against a shasum-derived expectation",
   bytes.code === 0 && /1 PASS \/ 0 FAIL/.test(bytes.out), bytes.out.slice(-260));

// The same defect made two DIFFERENT byte streams collide into one verdict,
// because both decode to the same replacement character.
ok("...and two different byte streams do NOT share a digest",
   sha256Hex(Buffer.from([0xFF, 0x41])) !== sha256Hex(Buffer.from([0xFE, 0x41])));

// QA finding 2 (HIGH). seal.ts refuses to overwrite an existing manifest;
// reveal.ts did not, so a second reveal silently replaced the first run's record
// while that record's own comment claimed it was "Preserved AS PRODUCED".
// revealed_at is the primary guard, but it lives in an editable file — clearing
// it (tampering, a bad restore, a double invocation) used to let the overwrite
// through. Simulate exactly that.
const rtManifest = join(repoRoot, "planning/holdouts/manifests", rtId + ".yaml");
writeFileSync(rtManifest, readFileSync(rtManifest, "utf8")
  .replace(/^revealed_at:.*$/m, "revealed_at: null")
  .replace(/^run_evidence_bundle:.*$/m, "run_evidence_bundle: null"));
const second = run({ WB_QA_CONTEXT: "1" }, ["--id", rtId, "--candidate", "cafe066"]);
ok("a second reveal REFUSES rather than overwriting the first run record",
   second.code !== 0 && /run record already exists/.test(second.out), second.out.slice(-260));


console.log("— concurrency, attribution, and malformed packs —");

// QA finding A (CRITICAL). existsSync-then-write is not atomic. MEASURED: two
// reveals launched together both passed the guard, both ran, and the last writer
// won — the manifest recorded candidate race-A while the evidence bundle recorded
// race-B, on a pack that was genuinely spent. One raw log was overwritten because
// both derived the same filename from a whole-second timestamp.
const raceId = "HLD-S91-v1";
const raceDir = join(repoRoot, "qa-private", raceId);
mkdirSync(raceDir, { recursive: true });
writeFileSync(join(raceDir, "README.md"), "# race\n");
writeFileSync(join(raceDir, "cases.yaml"), "cases:\n  - id: H001\n    class: nominal\n    run: \"sleep 3; echo ok\"\n");
writeFileSync(join(raceDir, "expected.json"), JSON.stringify({ H001: { exit: 0, stdout_contains: "ok" } }) + "\n");
seal(["--slice", "S91", "--story", "ST-91", "--contract", "v1"]);
const rc = join(tmp, "race");
mkdirSync(rc, { recursive: true });
const one = (cand: string, tag: string) =>
  "( WB_QA_CONTEXT=1 bun " + JSON.stringify(TOOL) + " --id " + raceId + " --candidate " + cand +
  " --allow-unverified-candidate > " + rc + "/" + tag + ".log 2>&1; echo $? > " + rc + "/" + tag + ".rc ) &";
execFileSync("/bin/sh", ["-c",
  "cd " + JSON.stringify(repoRoot) + " && " + one("aaaaaa1", "a") + " " + one("bbbbbb2", "b") + " wait",
], { encoding: "utf8" });
const rcA = readFileSync(join(rc, "a.rc"), "utf8").trim();
const rcB = readFileSync(join(rc, "b.rc"), "utf8").trim();
ok("two concurrent reveals of one id: EXACTLY ONE succeeds",
   [rcA, rcB].filter((x) => x === "0").length === 1, "exit codes " + rcA + " and " + rcB);
const raceMan = readFileSync(join(repoRoot, "planning/holdouts/manifests", raceId + ".yaml"), "utf8");
const raceEvb = readFileSync(join(repoRoot, "planning/evidence", "EVB-" + raceId, "manifest.yaml"), "utf8");
const manCand = (/(?:frozen|UNVERIFIED) candidate (\S+);/.exec(raceMan) ?? [])[1] ?? "";
const evbCand = (/^candidate: (.+)$/m.exec(raceEvb) ?? [])[1] ?? "";
ok("...and the two records name the SAME candidate",
   manCand !== "" && manCand === evbCand, "manifest " + manCand + " vs bundle " + evbCand);

// The two-process race above is an INTEGRATION check and it is timing-dependent:
// MEASURED, with the lock removed, the second process still exited 1 inside this
// suite because it simply started after the first had finished, while the same
// scenario in an idle sandbox had BOTH exit 0. A test that can pass for a
// scheduling reason cannot evidence the guard, so the guard is also tested
// directly and deterministically: hold the lock, then try to reveal.
const heldId = "HLD-S87-v1";
const heldDir = join(repoRoot, "qa-private", heldId);
mkdirSync(heldDir, { recursive: true });
writeFileSync(join(heldDir, "README.md"), "# lock held\n");
writeFileSync(join(heldDir, "cases.yaml"), "cases:\n  - id: H001\n    class: nominal\n    run: \"echo ok\"\n");
writeFileSync(join(heldDir, "expected.json"), JSON.stringify({ H001: { exit: 0 } }) + "\n");
seal(["--slice", "S87", "--story", "ST-87", "--contract", "v1"]);
const heldBundle = join(repoRoot, "planning/evidence", "EVB-" + heldId);
mkdirSync(heldBundle, { recursive: true });
writeFileSync(join(heldBundle, ".reveal.lock"), "pid: 999999\ncandidate: someone-else\n");
const held = run({ WB_QA_CONTEXT: "1" }, ["--id", heldId, "--candidate", "cafe099"]);
ok("a reveal REFUSES while another holds the lock",
   held.code !== 0 && /holds the lock/.test(held.out), held.out.slice(-220));
ok("...and that refusal does NOT spend the pack",
   /revealed_at: null/.test(readFileSync(join(repoRoot, "planning/holdouts/manifests", heldId + ".yaml"), "utf8")));
ok("...and it did NOT steal a lock it does not own",
   readFileSync(join(heldBundle, ".reveal.lock"), "utf8").includes("pid: 999999"));


// QA pass 2 left this unresolved: is --candidate ever checked against HEAD? It was
// not. A clean tree only proves nothing is uncommitted; it says nothing about WHICH
// commit is checked out, so any string was accepted and written into the evidence.
const repo2 = join(tmp, "repo2");
mkdirSync(join(repo2, "planning/holdouts/manifests"), { recursive: true });
mkdirSync(join(repo2, "qa-private", "HLD-S90-v1"), { recursive: true });
writeFileSync(join(repo2, ".gitignore"), "qa-private/\nplanning/evidence/\n");
writeFileSync(join(repo2, "qa-private/HLD-S90-v1/README.md"), "# attribution\n");
writeFileSync(join(repo2, "qa-private/HLD-S90-v1/cases.yaml"), "cases:\n  - id: H001\n    class: nominal\n    run: \"echo ok\"\n");
writeFileSync(join(repo2, "qa-private/HLD-S90-v1/expected.json"), JSON.stringify({ H001: { exit: 0, stdout_contains: "ok" } }) + "\n");
seal(["--slice", "S90", "--story", "ST-90", "--contract", "v1"], repo2);
const git = (...a: string[]) =>
  execFileSync("git", ["-c", "user.email=t@t", "-c", "user.name=t", ...a],
               { cwd: repo2, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
git("init", "-q"); git("add", "-A"); git("commit", "-q", "-m", "seal");
const head = git("rev-parse", "HEAD").trim();
const wrongSha = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S90-v1", "--candidate", "deadbeefdeadbee"], repo2);
ok("a --candidate that does not name HEAD is REFUSED",
   wrongSha.code !== 0 && /does not name the commit/.test(wrongSha.out), wrongSha.out.slice(-200));
ok("...and the pack is NOT spent by the refusal",
   /revealed_at: null/.test(readFileSync(join(repo2, "planning/holdouts/manifests/HLD-S90-v1.yaml"), "utf8")));
const rightSha = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S90-v1", "--candidate", head], repo2);
ok("...and the real HEAD sha is accepted",
   rightSha.code === 0 && /1 PASS \/ 0 FAIL/.test(rightSha.out), rightSha.out.slice(-200));

// A malformed expectation used to throw mid-loop at want.exit — AFTER earlier cases
// had already run their shell commands and left side effects behind.
const badId = "HLD-S89-v1";
const badDir = join(repoRoot, "qa-private", badId);
mkdirSync(badDir, { recursive: true });
const marker = join(tmp, "side-effect-marker");
writeFileSync(join(badDir, "README.md"), "# malformed\n");
writeFileSync(join(badDir, "cases.yaml"),
  "cases:\n  - id: H001\n    class: nominal\n    run: \"touch " + marker + "\"\n" +
  "  - id: H002\n    class: nominal\n    run: \"echo two\"\n");
writeFileSync(join(badDir, "expected.json"), JSON.stringify({ H001: { exit: 0 }, H002: null }) + "\n");
seal(["--slice", "S89", "--story", "ST-89", "--contract", "v1"]);
const malformed = run({ WB_QA_CONTEXT: "1" }, ["--id", badId, "--candidate", "cafe077"]);
ok("a malformed expected.json is refused, naming the offending case",
   malformed.code !== 0 && /expected\.json is malformed/.test(malformed.out) && /H002/.test(malformed.out),
   malformed.out.slice(-220));
ok("...and NOTHING ran — the first case left no side effect", !existsSync(marker));

// The pack hash covers cases.yaml's RAW bytes, but it is parsed as UTF-8, so an
// invalid byte would become U+FFFD and the command that ran would not be the
// command the hash pinned.
const u8Id = "HLD-S88-v1";
const u8Dir = join(repoRoot, "qa-private", u8Id);
mkdirSync(u8Dir, { recursive: true });
writeFileSync(join(u8Dir, "README.md"), "# bad bytes\n");
writeFileSync(join(u8Dir, "cases.yaml"), Buffer.concat([
  Buffer.from("cases:\n  - id: H001\n    class: nominal\n    run: \"echo "),
  Buffer.from([0xFF]),
  Buffer.from("\"\n")]));
writeFileSync(join(u8Dir, "expected.json"), JSON.stringify({ H001: { exit: 0 } }) + "\n");
seal(["--slice", "S88", "--story", "ST-88", "--contract", "v1"]);
const u8 = run({ WB_QA_CONTEXT: "1" }, ["--id", u8Id, "--candidate", "cafe088"]);
ok("a cases.yaml that is not valid UTF-8 is REFUSED before anything runs",
   u8.code !== 0 && /not valid UTF-8/.test(u8.out), u8.out.slice(-220));

// verify-manifests crashed with an uncaught EISDIR on a DIRECTORY named *.yaml,
// failing the census for a reason unrelated to any manifest.
mkdirSync(join(repoRoot, "planning/holdouts/manifests", "HLD-weird-v1.yaml"), { recursive: true });
const vDir = (() => {
  try { return execFileSync("bun", [join(process.cwd(), "tools/holdout/verify-manifests.ts")],
                            { cwd: repoRoot, encoding: "utf8" }); }
  catch (e: any) { return String(e.stdout ?? "") + String(e.stderr ?? ""); }
})();
ok("verify-manifests survives a DIRECTORY named *.yaml and reports it",
   /not a regular file/.test(vDir) && !/EISDIR/.test(vDir), vDir.slice(-220));


console.log("— attribution in odd git states, and a byte-exact contains —");

// A git repo with NO commits and a .git/info/exclude of "*" has a CLEAN tree while
// HEAD cannot resolve. The old code lumped that in with "not a git repository",
// skipped the attribution check, and SEALED the pack against a fabricated candidate.
// Reproduced before fixing: revealed_at was stamped against
// "totally-made-up-not-a-commit".
const zc = join(tmp, "zerocommit");
mkdirSync(join(zc, "planning/holdouts/manifests"), { recursive: true });
mkdirSync(join(zc, "qa-private", "HLD-S86-v1"), { recursive: true });
execFileSync("git", ["init", "-q", "."], { cwd: zc, stdio: ["ignore", "ignore", "ignore"] });
writeFileSync(join(zc, ".git/info/exclude"), "*\n");
writeFileSync(join(zc, "qa-private/HLD-S86-v1/README.md"), "# zero commit\n");
writeFileSync(join(zc, "qa-private/HLD-S86-v1/cases.yaml"), "cases:\n  - id: H001\n    class: nominal\n    run: \"echo ok\"\n");
writeFileSync(join(zc, "qa-private/HLD-S86-v1/expected.json"), JSON.stringify({ H001: { exit: 0, stdout_contains: "ok" } }) + "\n");
seal(["--slice", "S86", "--story", "ST-86", "--contract", "v1"], zc);
const zcClean = execFileSync("git", ["status", "--porcelain"], { cwd: zc, encoding: "utf8" }).trim();
ok("a zero-commit repo with an exclude-all IS clean (the precondition for the bypass)", zcClean === "", "status [" + zcClean + "]");
const zcRun = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S86-v1", "--candidate", "deadbeefdeadbee"], zc);
ok("a repo whose HEAD does not resolve is REFUSED, not treated as 'not a git repository'",
   zcRun.code !== 0 && /HEAD does not resolve/.test(zcRun.out), zcRun.out.slice(-220));
ok("...and the pack is NOT spent by that refusal",
   /revealed_at: null/.test(readFileSync(join(zc, "planning/holdouts/manifests/HLD-S86-v1.yaml"), "utf8")));
ok("...and no evidence bundle was created", !existsSync(join(zc, "planning/evidence/EVB-HLD-S86-v1")));

// Control: once a real commit exists, the real sha is accepted in the same repo.
const zcGit = (...a: string[]) => execFileSync("git", ["-c", "user.email=t@t", "-c", "user.name=t", ...a],
  { cwd: zc, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
zcGit("add", "-A", "-f"); zcGit("commit", "-q", "-m", "first");
const zcHead = zcGit("rev-parse", "HEAD").trim();
ok("...and after a real commit the true sha is accepted",
   run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S86-v1", "--candidate", zcHead], zc).code === 0);

// Detached HEAD — the reviewer ran out of budget before reaching it. HEAD still
// resolves when detached, so attribution must keep working rather than fall back.
const det = join(tmp, "detached");
mkdirSync(join(det, "planning/holdouts/manifests"), { recursive: true });
mkdirSync(join(det, "qa-private", "HLD-S85-v1"), { recursive: true });
execFileSync("git", ["init", "-q", "."], { cwd: det, stdio: ["ignore", "ignore", "ignore"] });
writeFileSync(join(det, ".git/info/exclude"), "qa-private/\nplanning/evidence/\n");
writeFileSync(join(det, "qa-private/HLD-S85-v1/README.md"), "# detached\n");
writeFileSync(join(det, "qa-private/HLD-S85-v1/cases.yaml"), "cases:\n  - id: H001\n    class: nominal\n    run: \"echo ok\"\n");
writeFileSync(join(det, "qa-private/HLD-S85-v1/expected.json"), JSON.stringify({ H001: { exit: 0, stdout_contains: "ok" } }) + "\n");
seal(["--slice", "S85", "--story", "ST-85", "--contract", "v1"], det);
const detGit = (...a: string[]) => execFileSync("git", ["-c", "user.email=t@t", "-c", "user.name=t", ...a],
  { cwd: det, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
detGit("add", "-A"); detGit("commit", "-q", "-m", "seal");
const detHead = detGit("rev-parse", "HEAD").trim();
detGit("checkout", "-q", "--detach", detHead);
ok("a DETACHED HEAD still resolves, so attribution keeps working",
   run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S85-v1", "--candidate", detHead], det).code === 0);
ok("...and a wrong candidate is still refused while detached",
   run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S85-v1", "--candidate", "0000000deadbeef"], det).code !== 0);

// stdout_contains carried the SAME lossy-decode exposure stdout_sha256 had: every
// invalid byte collapses to U+FFFD, so a matcher looking for "�A" would match
// output that never contained a replacement character at all. Matching raw bytes
// removes the false match.
const ctId = "HLD-S84-v1";
const ctDir = join(repoRoot, "qa-private", ctId);
mkdirSync(ctDir, { recursive: true });
writeFileSync(join(ctDir, "README.md"), "# contains\n");
writeFileSync(join(ctDir, "cases.yaml"), "cases:\n  - id: H001\n    class: nominal\n    run: 'printf \"\\376\\101\"'\n");
writeFileSync(join(ctDir, "expected.json"), JSON.stringify({ H001: { exit: 0, stdout_contains: "�A" } }) + "\n");
seal(["--slice", "S84", "--story", "ST-84", "--contract", "v1"]);
const ct = run({ WB_QA_CONTEXT: "1" }, ["--id", ctId, "--candidate", "cafe100"]);
ok("stdout_contains does NOT falsely match a replacement character the output never held",
   ct.code !== 0 && /stdout missing/.test(ct.out), ct.out.slice(-220));


console.log("— pack self-consistency, and scale —");

// MEASURED before the fix: a cases.yaml repeating one id ran BOTH commands and
// sealed "2 PASS / 0 FAIL of 2". Two different commands were graded against one
// shared expectation, and the record held two indistinguishable "## H001" sections.
const dupId = "HLD-S83-v1";
const dupDir = join(repoRoot, "qa-private", dupId);
mkdirSync(dupDir, { recursive: true });
writeFileSync(join(dupDir, "README.md"), "# dup ids\n");
writeFileSync(join(dupDir, "cases.yaml"),
  "cases:\n  - id: H001\n    class: nominal\n    run: \"echo first\"\n" +
  "  - id: H001\n    class: nominal\n    run: \"echo second\"\n");
writeFileSync(join(dupDir, "expected.json"), JSON.stringify({ H001: { exit: 0 } }) + "\n");
seal(["--slice", "S83", "--story", "ST-83", "--contract", "v1"]);
const dupRun = run({ WB_QA_CONTEXT: "1" }, ["--id", dupId, "--candidate", "cafe111"]);
ok("cases.yaml repeating a case id is REFUSED",
   dupRun.code !== 0 && /repeats case id/.test(dupRun.out), dupRun.out.slice(-200));
ok("...and that refusal does not spend the pack",
   /revealed_at: null/.test(readFileSync(join(repoRoot, "planning/holdouts/manifests", dupId + ".yaml"), "utf8")));

// MEASURED before the fix: expected.json with one key twice parses last-key-wins in
// silence. {"H001":{"exit":0},"H001":{"exit":5}} graded the case against exit 5 and
// PASSED, while a custodian reading top-down would believe the expectation was 0.
const dkId = "HLD-S82-v1";
const dkDir = join(repoRoot, "qa-private", dkId);
mkdirSync(dkDir, { recursive: true });
writeFileSync(join(dkDir, "README.md"), "# dup keys\n");
writeFileSync(join(dkDir, "cases.yaml"), "cases:\n  - id: H001\n    class: nominal\n    run: \"exit 5\"\n");
writeFileSync(join(dkDir, "expected.json"), "{\"H001\":{\"exit\":0},\"H001\":{\"exit\":5}}\n");
const dkSeal = seal(["--slice", "S82", "--story", "ST-82", "--contract", "v1"]);
ok("seal refuses an expected.json with a repeated key, at authoring time",
   dkSeal.code !== 0 && /repeats key/.test(dkSeal.out), dkSeal.out.slice(-160));
manualSeal(dkId, dkDir);
const dkRun = run({ WB_QA_CONTEXT: "1" }, ["--id", dkId, "--candidate", "cafe122"]);
ok("expected.json repeating a key is REFUSED, not silently last-key-wins",
   dkRun.code !== 0 && /repeats key/.test(dkRun.out), dkRun.out.slice(-200));
ok("...and that refusal does not spend the pack either",
   /revealed_at: null/.test(readFileSync(join(repoRoot, "planning/holdouts/manifests", dkId + ".yaml"), "utf8")));

// Confirms existing seal-side behaviour rather than a new fix: an expectation for a
// case that does not exist is caught by the CUSTODIAN tool, before a manifest exists.
const orphanDir = join(repoRoot, "qa-private", "HLD-S78-v1");
mkdirSync(orphanDir, { recursive: true });
writeFileSync(join(orphanDir, "README.md"), "# orphan\n");
writeFileSync(join(orphanDir, "cases.yaml"), "cases:\n  - id: H001\n    class: nominal\n    run: \"echo x\"\n");
writeFileSync(join(orphanDir, "expected.json"), JSON.stringify({ H001: { exit: 0 }, H999: { exit: 0 } }) + "\n");
const orphan = seal(["--slice", "S78", "--story", "ST-78", "--contract", "v1"]);
ok("seal refuses an expected.json holding results for cases that do not exist",
   orphan.code !== 0 && /cases that/.test(orphan.out), orphan.out.slice(-200));

// Scale: nothing truncates or silently drops at a large case count. MEASURED at
// 2000 cases in about 4.3 seconds.
const bigN = 2000;
const bigCountId = "HLD-S77-v1";
const bigCountDir = join(repoRoot, "qa-private", bigCountId);
mkdirSync(bigCountDir, { recursive: true });
writeFileSync(join(bigCountDir, "README.md"), "# scale\n");
let bigCases = "cases:\n"; const bigExp: Record<string, any> = {};
for (let i = 0; i < bigN; i++) {
  const cid = "H" + String(i).padStart(4, "0");
  bigCases += "  - id: " + cid + "\n    class: nominal\n    run: \"echo " + i + "\"\n";
  bigExp[cid] = { exit: 0, stdout_contains: String(i) };
}
writeFileSync(join(bigCountDir, "cases.yaml"), bigCases);
writeFileSync(join(bigCountDir, "expected.json"), JSON.stringify(bigExp) + "\n");
seal(["--slice", "S77", "--story", "ST-77", "--contract", "v1"]);
const bigRun = run({ WB_QA_CONTEXT: "1" }, ["--id", bigCountId, "--candidate", "cafe133"]);
ok("a " + bigN + "-case pack runs every case with nothing dropped",
   bigRun.code === 0 && new RegExp(bigN + " PASS \\/ 0 FAIL of " + bigN).test(bigRun.out), bigRun.out.slice(-200));


console.log("— case ids that are regex metacharacters —");

// A QA review DEFEATED the duplicate-key guard here. The guard built a regex from
// the case id, and the escape in it had been corrupted by a patch tool into a
// literal comment string. For an id holding a regex metacharacter the wrong regex
// was built, the guard silently did nothing, and a pack with id "H(1)" and a
// duplicated key SEALED a wrong verdict. Every id in this suite was alphanumeric,
// so the escape never had anything to replace and the corruption was invisible.
// The guard no longer builds a regex at all; these cases keep it that way.
const metaId = "HLD-S76-v1";
const metaDir = join(repoRoot, "qa-private", metaId);
mkdirSync(metaDir, { recursive: true });
writeFileSync(join(metaDir, "README.md"), "# metachar\n");
writeFileSync(join(metaDir, "cases.yaml"), "cases:\n  - id: \"H(1)\"\n    class: nominal\n    run: \"echo hi\"\n");
writeFileSync(join(metaDir, "expected.json"), "{\n  \"H(1)\": { \"exit\": 0 },\n  \"H(1)\": { \"exit\": 9 }\n}\n");
manualSeal(metaId, metaDir);
const meta = run({ WB_QA_CONTEXT: "1" }, ["--id", metaId, "--candidate", "cafe144"]);
ok("a duplicate key is caught even when the case id holds a regex metacharacter",
   meta.code !== 0 && /repeats key/.test(meta.out), meta.out.slice(-220));
ok("...and that pack is NOT spent",
   /revealed_at: null/.test(readFileSync(join(repoRoot, "planning/holdouts/manifests", metaId + ".yaml"), "utf8")));

// The other half, and the reason it matters: a metacharacter id with NO duplicate
// must still run normally. Otherwise the "fix" is just refusing everything awkward.
const okMetaId = "HLD-S75-v1";
const okMetaDir = join(repoRoot, "qa-private", okMetaId);
mkdirSync(okMetaDir, { recursive: true });
writeFileSync(join(okMetaDir, "README.md"), "# metachar ok\n");
writeFileSync(join(okMetaDir, "cases.yaml"),
  "cases:\n  - id: \"H(1)\"\n    class: nominal\n    run: \"echo hi\"\n" +
  "  - id: \"H.2\"\n    class: counterexample\n    run: \"exit 4\"\n");
writeFileSync(join(okMetaDir, "expected.json"),
  JSON.stringify({ "H(1)": { exit: 0, stdout_contains: "hi" }, "H.2": { exit: 4 } }) + "\n");
seal(["--slice", "S75", "--story", "ST-75", "--contract", "v1", "--require-counterexample"]);
const okMeta = run({ WB_QA_CONTEXT: "1" }, ["--id", okMetaId, "--candidate", "cafe155"]);
ok("a metacharacter id with NO duplicate still runs and passes normally",
   okMeta.code === 0 && /2 PASS \/ 0 FAIL/.test(okMeta.out), okMeta.out.slice(-220));

console.log("— duplicate keys the LITERAL scans could not see —");

// A QA review DEFEATED the duplicate-key guard a SECOND time, and this defeat was
// not a typo — it was inherent to matching one literal spelling of the key.
// {"H1":...,"H\u0031":...} is ONE repeated key to JSON.parse, because \u0031 IS
// the character "1". The two spellings share no bytes, so an indexOf scan for
// JSON.stringify(id) saw a single occurrence, no refusal fired, and a pack sealed
// a wrong verdict. The guard now decodes every key it finds, so spellings collide.
const ESC_MANIFESTS = join(repoRoot, "planning/holdouts/manifests");
const escId = "HLD-S74-v1";
const escDir = join(repoRoot, "qa-private", escId);
mkdirSync(escDir, { recursive: true });
writeFileSync(join(escDir, "README.md"), "# escape equivalence\n");
writeFileSync(join(escDir, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"echo hi\"\n");
writeFileSync(join(escDir, "expected.json"),
  '{\n  "H1"   :   { "exit": 0 },\n  "H' + '\\u0031": { "exit": 9 }\n}\n');
manualSeal(escId, escDir);
const esc = run({ WB_QA_CONTEXT: "1" }, ["--id", escId, "--candidate", "cafe166"]);
ok("a duplicate key spelled two different ways is REFUSED", esc.code !== 0 && /repeats key/.test(esc.out), esc.out.slice(-260));
ok("...and that pack is NOT spent", /revealed_at: null/.test(readFileSync(join(ESC_MANIFESTS, escId + ".yaml"), "utf8")));

// Whitespace and newlines between a key and its colon are now structurally
// irrelevant — the scanner records a key by POSITION, never by the bytes after it.
const wsId = "HLD-S73-v1";
const wsDir = join(repoRoot, "qa-private", wsId);
mkdirSync(wsDir, { recursive: true });
writeFileSync(join(wsDir, "README.md"), "# whitespace\n");
writeFileSync(join(wsDir, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"echo hi\"\n");
writeFileSync(join(wsDir, "expected.json"), '{\n  "H1"\n  :\n  { "exit": 0 },\n  "H1"\t:\t{ "exit": 9 }\n}\n');
manualSeal(wsId, wsDir);
const ws = run({ WB_QA_CONTEXT: "1" }, ["--id", wsId, "--candidate", "cafe177"]);
ok("a duplicate key separated from its colon by newlines and tabs is REFUSED", ws.code !== 0 && /repeats key/.test(ws.out), ws.out.slice(-260));

// A duplicate NESTED inside one entry is just as dangerous: a repeated "exit"
// silently changes that case's expectation. Scope is the whole document.
const nestId = "HLD-S71-v1";
const nestDir = join(repoRoot, "qa-private", nestId);
mkdirSync(nestDir, { recursive: true });
writeFileSync(join(nestDir, "README.md"), "# nested duplicate\n");
writeFileSync(join(nestDir, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"echo hi\"\n");
writeFileSync(join(nestDir, "expected.json"), '{\n  "H1": { "exit": 0, "exit": 9 }\n}\n');
manualSeal(nestId, nestDir);
const nest = run({ WB_QA_CONTEXT: "1" }, ["--id", nestId, "--candidate", "cafe188"]);
ok("a duplicate key nested INSIDE one expectation is REFUSED", nest.code !== 0 && /repeats key/.test(nest.out), nest.out.slice(-260));

// The other half, and the reason the scanner decodes keys rather than hunting for
// text: a string that merely LOOKS like a key, sitting in value position, must NOT
// refuse. The previous indexOf scan would have counted this as a duplicate.
const valId = "HLD-S72-v1";
const valDir = join(repoRoot, "qa-private", valId);
mkdirSync(valDir, { recursive: true });
writeFileSync(join(valDir, "README.md"), "# lookalike in a value\n");
writeFileSync(join(valDir, "cases.yaml"),
  "cases:\n  - id: H1\n    class: nominal\n    run: \"echo '\\\"H1\\\" : this is a VALUE, not a key'\"\n");
writeFileSync(join(valDir, "expected.json"),
  '{\n  "H1": { "exit": 0, "stdout_contains": "\\"H1\\" : this is a VALUE, not a key" }\n}\n');
seal(["--slice", "S72", "--story", "ST-72", "--contract", "v1"]);
const val = run({ WB_QA_CONTEXT: "1" }, ["--id", valId, "--candidate", "cafe199"]);
ok("a key-lookalike inside a string VALUE does NOT falsely refuse",
   val.code === 0 && /1 PASS \/ 0 FAIL/.test(val.out), val.out.slice(-260));

// The same id used as a key in a DIFFERENT, nested object is not a duplicate —
// each object carries its own key set. The defeated indexOf scan counted every
// occurrence in the whole file and would have refused this pack outright, which
// is the false-refusal half of the same bug. Refusing valid packs is not a fix.
const deepId = "HLD-S69-v1";
const deepDir = join(repoRoot, "qa-private", deepId);
mkdirSync(deepDir, { recursive: true });
writeFileSync(join(deepDir, "README.md"), "# nested elsewhere\n");
writeFileSync(join(deepDir, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"echo hi\"\n");
// F10 now refuses the unknown "meta" field a full pack needed to express this, so
// the scanner property is pinned as direct unit tests instead — same property,
// plus the quote/backslash frame-desync values S62 can no longer legally carry.
ok("scanner: the same id as a key in a DIFFERENT nested object is not a duplicate",
   duplicateJsonKeys('{ "H1": { "exit": 0, "meta": { "H1": 1 } } }').length === 0);
ok("scanner: a genuine duplicate nested two levels down IS caught",
   duplicateJsonKeys('{ "a": { "b": { "k": 1, "k": 2 } } }').join(",") === "k");
ok("scanner: a value holding quotes, backslashes and braces does not desync the frames",
   duplicateJsonKeys('{ "H1": { "exit": 0, "s": "}}} {{{ \\" \\\\ ,,, ::: " }, "H2": { "exit": 1 } }').length === 0);
rmSync(deepDir, { recursive: true, force: true });

// The sharpest false-refusal case: a string VALUE whose text is identical to a
// key in the SAME object. Here "exit" is both a key and, separately, the note's
// value. Only the key position may be recorded, or the guard starts rejecting
// ordinary packs — and a guard that refuses valid work is not a safer guard.
const sameId = "HLD-S68-v1";
const sameDir = join(repoRoot, "qa-private", sameId);
mkdirSync(sameDir, { recursive: true });
writeFileSync(join(sameDir, "README.md"), "# value equals a sibling key\n");
writeFileSync(join(sameDir, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"echo exit-ok\"\n");
writeFileSync(join(sameDir, "expected.json"), '{\n  "H1": { "exit": 0, "stdout_contains": "exit" }\n}\n');
seal(["--slice", "S68", "--story", "ST-68", "--contract", "v1"]);
const same = run({ WB_QA_CONTEXT: "1" }, ["--id", sameId, "--candidate", "cafe211"]);
ok("a string value identical to a sibling KEY does not falsely refuse",
   same.code === 0 && /1 PASS \/ 0 FAIL/.test(same.out), same.out.slice(-260));

console.log("— the key tokenizer, fuzzed —");

// A review declined to clear the new tokenizer without live tests and said so
// plainly: its read of the algorithm found no hole, but "analysis is not what
// this review process is supposed to rest on." These are those tests.
const fuzzPack = (id: string, yamlId: string, rawExpected: string, slice: string) => {
  const dir = join(repoRoot, "qa-private", id);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, "README.md"), `# fuzz ${slice}\n`);
  writeFileSync(join(dir, "cases.yaml"), `cases:\n  - id: ${yamlId}\n    class: nominal\n    run: "echo hi"\n`);
  writeFileSync(join(dir, "expected.json"), rawExpected);
  const sealed = seal(["--slice", slice, "--story", `ST-${slice.slice(1)}`, "--contract", "v1"]);
  if (sealed.code !== 0) console.log(`    (seal ${slice} refused: ${sealed.out.trim().split("\n")[0]})`);
  return { sealed, reveal: () => run({ WB_QA_CONTEXT: "1" }, ["--id", id, "--candidate", "cafe000" + slice.slice(1)]) };
};

// 1. A SURROGATE PAIR. "H😀" and a literal H followed by U+1F600 are the
// same key to JSON.parse. The two spellings share almost no bytes, which is the
// same shape of attack that defeated the previous scan with "1".
const astral = "H\u{1F600}";
const fz1 = fuzzPack("HLD-S66-v1", JSON.stringify(astral),
  '{\n  "' + astral + '": { "exit": 0 },\n  "H' + '\\uD83D\\uDE00": { "exit": 9 }\n}\n', "S66");
manualSeal("HLD-S66-v1", join(repoRoot, "qa-private", "HLD-S66-v1"));
const r1 = fz1.reveal();
ok("a duplicate key spelled as a literal astral character and as a surrogate pair is REFUSED",
   r1.code !== 0 && /repeats key/.test(r1.out), r1.out.slice(-240));

// 2. The other half — an astral key with NO duplicate must still run normally.
const fz2 = fuzzPack("HLD-S65-v1", JSON.stringify(astral),
  '{\n  "H' + '\\uD83D\\uDE00": { "exit": 0 }\n}\n', "S65");
const r2 = fz2.reveal();
ok("an astral-character key with no duplicate still runs and passes",
   r2.code === 0 && /1 PASS \/ 0 FAIL/.test(r2.out), r2.out.slice(-240));

// 3. A LITERAL BACKSLASH inside the key, spelled two ways: "H\\1" and "H\1".
// \ IS the backslash, so these are one key. This also exercises the scanner's
// escape skip directly — the character after a backslash must never be read as a
// string terminator.
const backslashId = "H\\1";
const fz3 = fuzzPack("HLD-S64-v1", JSON.stringify(backslashId),
  '{\n  "H\\\\1": { "exit": 0 },\n  "H' + '\\u005C1": { "exit": 9 }\n}\n', "S64");
manualSeal("HLD-S64-v1", join(repoRoot, "qa-private", "HLD-S64-v1"));
const r3 = fz3.reveal();
ok("a key holding a literal backslash, spelled two ways, is REFUSED",
   r3.code !== 0 && /repeats key/.test(r3.out), r3.out.slice(-240));

// 4. An ESCAPED QUOTE inside the key, spelled two ways. If the scanner mistook the
// escaped quote for the end of the string, every frame after it would desync.
const quoteId = 'a"b';
const fz4 = fuzzPack("HLD-S63-v1", JSON.stringify(quoteId),
  '{\n  "a\\"b": { "exit": 0 },\n  "a' + '\\u0022b": { "exit": 9 }\n}\n', "S63");
manualSeal("HLD-S63-v1", join(repoRoot, "qa-private", "HLD-S63-v1"));
const r4 = fz4.reveal();
ok("a key holding an escaped quote, spelled two ways, is REFUSED",
   r4.code !== 0 && /repeats key/.test(r4.out), r4.out.slice(-240));

// 5. A string VALUE stuffed with the characters that drive the frame stack. If any
// of these were read outside the string, the tokenizer would push or pop a frame
// that JSON.parse never saw, and every later key would land in the wrong object.
// (the quote/backslash-in-value variants are unit-tested on the scanner directly,
// because F10 now refuses the unknown carrier field a full pack needed for them)
const fz5Dir = join(repoRoot, "qa-private", "HLD-S62-v1");
mkdirSync(fz5Dir, { recursive: true });
writeFileSync(join(fz5Dir, "README.md"), "# hostile value\n");
writeFileSync(join(fz5Dir, "cases.yaml"),
  "cases:\n  - id: H1\n    class: nominal\n    run: \"printf '%s' '}}} {{{ [[[ ]]] ,,, ::: '\"\n");
writeFileSync(join(fz5Dir, "expected.json"),
  '{\n  "H1": { "exit": 0, "stdout_contains": "}}} {{{ [[[ ]]] ,,, ::: " }\n}\n');
seal(["--slice", "S62", "--story", "ST-62", "--contract", "v1"]);
const r5 = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S62-v1", "--candidate", "cafe5555"]);
ok("braces, brackets, commas, colons inside a VALUE do not desync the scan",
   r5.code === 0 && /1 PASS \/ 0 FAIL/.test(r5.out), r5.out.slice(-240));

// 6. A BOM (byte order mark, U+FEFF) in front of the JSON. JSON.parse rejects it,
// so this must be a clean refusal with NOTHING RUN — recorded as whatever it
// actually does, not as whatever would be convenient.
const fz6 = fuzzPack("HLD-S61-v1", "H1",
  "﻿" + '{\n  "H1": { "exit": 0 }\n}\n', "S61");
// MEASURED: the BOM never reaches the tokenizer at all. seal.ts parses
// expected.json itself, JSON.parse rejects a leading U+FEFF, and the pack is
// refused before a manifest exists. So the pack cannot be created, let alone spent.
ok("a byte-order mark in front of expected.json is refused at SEAL time, so no pack exists",
   fz6.sealed.code !== 0 && !existsSync(join(repoRoot, "planning/holdouts/manifests", "HLD-S61-v1.yaml")),
   fz6.sealed.out.slice(-240));

console.log("— the key scanner, property-tested against ground truth —");

// A QA review asked the sharpest question about this scanner: can its verdict
// DISAGREE with what JSON.parse actually does, in a case where it does NOT
// refuse? Six hand-built fuzz cases cannot answer that. This generates 2000
// documents whose answer is known BY CONSTRUCTION — the generator decides
// whether to plant a duplicate before it writes a single character — and
// compares the scanner's verdict to that ground truth in BOTH directions:
// a missed duplicate and a false refusal are each a failure.
{
  let seed = 20260923;                      // fixed seed: any failure is reproducible
  const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; };
  const pick = <T>(xs: T[]): T => xs[Math.floor(rnd() * xs.length)];

  // An alphabet chosen to be hostile: a quote, a backslash, every character that
  // drives the frame stack, a control character, and an astral character (which
  // JSON may spell as a surrogate PAIR — two escapes for one character).
  const ALPHABET = ["a", "Z", "0", "_", "\"", "\\", ":", ",", "{", "}", "[", "]", " ", "\n", "", "é", "\u{1F600}"];
  const makeKey = () => Array.from({ length: 1 + Math.floor(rnd() * 4) }, () => pick(ALPHABET)).join("");

  // Spell one key three legal ways. All three decode to the same string, so a
  // scanner comparing RAW BYTES sees three different keys and is defeated.
  const spell = (k: string): string => {
    const mode = Math.floor(rnd() * 3);
    if (mode === 0) return JSON.stringify(k);
    const out: string[] = ["\""];
    for (const ch of k) {
      const cp = ch.codePointAt(0)!;
      if (mode === 1 || cp > 0xffff || ch === "\"" || ch === "\\" || cp < 0x20) {
        for (let u = 0; u < ch.length; u++) out.push("\\u" + ch.charCodeAt(u).toString(16).padStart(4, "0"));
      } else out.push(ch);
    }
    out.push("\"");
    return out.join("");
  };
  const ws = () => pick(["", " ", "\n", "\t", "  \n  "]);

  // Values include strings that LOOK like keys, plus nested containers — so a
  // scan that counted occurrences anywhere in the file would false-refuse here.
  const makeValue = (depth: number): { text: string; dup: boolean } => {
    const r = Math.floor(rnd() * (depth > 2 ? 3 : 5));
    if (r === 0) return { text: String(Math.floor(rnd() * 1000)), dup: false };
    if (r === 1) return { text: spell(makeKey()), dup: false };
    if (r === 2) return { text: pick(["true", "false", "null"]), dup: false };
    if (r === 3) {
      const a = makeValue(depth + 1), b = makeValue(depth + 1);
      return { text: "[" + ws() + a.text + "," + ws() + b.text + ws() + "]", dup: a.dup || b.dup };
    }
    return makeObject(depth + 1);
  };

  const makeObject = (depth: number): { text: string; dup: boolean } => {
    const n = 1 + Math.floor(rnd() * 3);
    const keys: string[] = [];
    while (keys.length < n) { const k = makeKey(); if (!keys.includes(k)) keys.push(k); }
    let dup = false;
    const entries: string[] = [];
    for (const k of keys) {
      const v = makeValue(depth);
      dup = dup || v.dup;
      entries.push(spell(k) + ws() + ":" + ws() + v.text);
    }
    // Plant a duplicate in roughly half the objects, spelled DIFFERENTLY on purpose.
    if (rnd() < 0.5 && depth < 3) {
      const v = makeValue(depth);
      dup = true;
      entries.push(spell(keys[0]) + ws() + ":" + ws() + v.text);
    }
    return { text: "{" + ws() + entries.join("," + ws()) + ws() + "}", dup };
  };

  let checked = 0, missed = 0, falseRefusals = 0, withDup = 0, withoutDup = 0, unparseable = 0;
  const firstBad: string[] = [];
  for (let t = 0; t < 2000; t++) {
    const doc = makeObject(0);
    try { JSON.parse(doc.text); } catch { unparseable++; continue; }   // reveal only ever sees parseable text
    const verdict = duplicateJsonKeys(doc.text).length > 0;
    checked++;
    if (doc.dup) withDup++; else withoutDup++;
    if (doc.dup && !verdict) { missed++; if (firstBad.length < 1) firstBad.push("MISSED: " + doc.text.slice(0, 180)); }
    if (!doc.dup && verdict) { falseRefusals++; if (firstBad.length < 1) firstBad.push("FALSE REFUSAL: " + doc.text.slice(0, 180)); }
  }
  console.log(`    (property run: checked=${checked} planted=${withDup} clean=${withoutDup} unparseable=${unparseable} missed=${missed} falseRefusals=${falseRefusals})`);
  ok("the scanner agrees with ground truth on every generated document",
     missed === 0 && falseRefusals === 0 && checked > 1000 && withDup > 100 && withoutDup > 100,
     `checked=${checked} (planted=${withDup}, clean=${withoutDup}, unparseable=${unparseable}) missed=${missed} falseRefusals=${falseRefusals} ${firstBad[0] ?? ""}`);
}

console.log("— the manifest is published atomically —");

// A concurrent reveal.ts read a manifest WHILE seal.ts was writing it and refused
// with "(root): not a mapping" — MEASURED by review, 1 run in 5. seal now builds
// the file under a temp name and publishes it with link(2), which is atomic and
// fails with EEXIST if the name is taken, so write-once needs no separate check.
const atomId = "HLD-S70-v1";
const atomDir = join(repoRoot, "qa-private", atomId);
mkdirSync(atomDir, { recursive: true });
writeFileSync(join(atomDir, "README.md"), "# atomic publish\n");
writeFileSync(join(atomDir, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"echo hi\"\n");
writeFileSync(join(atomDir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
const atom1 = seal(["--slice", "S70", "--story", "ST-70", "--contract", "v1"]);
const strays1 = readdirSync(ESC_MANIFESTS).filter((f) => f.includes(".tmp-"));
ok("a successful seal leaves no temp file behind", atom1.code === 0 && strays1.length === 0, strays1.join(", "));
const atom2 = seal(["--slice", "S70", "--story", "ST-70", "--contract", "v1"]);
const strays2 = readdirSync(ESC_MANIFESTS).filter((f) => f.includes(".tmp-"));
ok("a refused second seal still leaves no temp file behind",
   atom2.code !== 0 && /already exists/.test(atom2.out) && strays2.length === 0, atom2.out.slice(-200) + " | " + strays2.join(", "));

// Six seals of the SAME id, launched together, while a reader hashes the manifest
// path as fast as it can. Two invariants: exactly one seal may win the name, and
// every successful read must return the SAME bytes — one distinct hash, never an
// intermediate state. A non-atomic write exposes intermediate states to readers;
// a review OBSERVED exactly that, 1 run in 5, as a torn read of a fresh seal.
//
// STATED LIMIT, MEASURED: this asserts invariants, it does not PROVE atomicity.
// Reverting seal to the pre-fix straight write was caught in only 1 of 3 runs
// (exit codes 0,0,1,1,1,1 — two winners, the TOCTOU race made visible); the
// torn-read half never fired in those 3 runs. So the detector is probabilistic.
// The atomicity argument rests on link(2) and rename(2) semantics — a name either
// exists or it does not — NOT on this test. On the fixed code the test is stable:
// 4 consecutive clean runs. It is here to catch an outright regression, and its
// weakness is recorded rather than hidden.
const sealRaceId = "HLD-S67-v1";
const sealRaceDir = join(repoRoot, "qa-private", sealRaceId);
mkdirSync(sealRaceDir, { recursive: true });
writeFileSync(join(sealRaceDir, "README.md"), "# concurrent seal\n");
writeFileSync(join(sealRaceDir, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"echo hi\"\n");
writeFileSync(join(sealRaceDir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
const sealRacePath = join(repoRoot, "planning/holdouts/manifests", sealRaceId + ".yaml");
const sealRaceLog = join(tmp, "race-hashes.txt");
const sealRaceRc = join(tmp, "race-rc.txt");
execFileSync("sh", ["-c",
  `: > "${sealRaceLog}"; : > "${sealRaceRc}";\n` +
  `( end=$(( $(date +%s) + 6 )); while [ "$(date +%s)" -lt "$end" ]; do\n` +
  `    if [ -f "${sealRacePath}" ]; then shasum -a 256 "${sealRacePath}" | cut -d" " -f1 >> "${sealRaceLog}"; fi\n` +
  `  done ) & reader=$!\n` +
  `for i in 1 2 3 4 5 6; do ( bun "${SEAL}" --slice S67 --story ST-67 --contract v1 >/dev/null 2>&1; echo $? >> "${sealRaceRc}" ) & done\n` +
  `wait $(jobs -p | grep -v "^$reader$") 2>/dev/null; wait\n`,
], { cwd: repoRoot, stdio: ["ignore", "pipe", "pipe"] });
const rcs = readFileSync(sealRaceRc, "utf8").trim().split("\n").filter(Boolean);
const winners = rcs.filter((r) => r === "0").length;
ok("exactly one of six concurrent seals wins the manifest name",
   winners === 1 && rcs.length === 6, `exit codes: ${rcs.join(",")}`);
const seenHashes = [...new Set(readFileSync(sealRaceLog, "utf8").trim().split("\n").filter(Boolean))];
ok("every concurrent read of the manifest returned the SAME bytes",
   seenHashes.length === 1 && seenHashes[0] === sha256Hex(readFileSync(sealRacePath)),
   `${seenHashes.length} distinct hash(es) across the reads`);

console.log("— security review F1-F12, each finding pinned by its own attack —");

// F3 — --id was interpolated raw into three path expressions that normalize
// differently; "./" defeated the write-once guard and "../.." escaped qa-private.
const f3a = run({ WB_QA_CONTEXT: "1" }, ["--id", "./HLD-S99-v1", "--candidate", "abc1230"]);
ok("F3: --id with a ./ prefix is refused unseen", f3a.code !== 0 && /not a valid pack id/.test(f3a.out), f3a.out.slice(-160));
const f3b = run({ WB_QA_CONTEXT: "1" }, ["--id", "../../etc", "--candidate", "abc1230"]);
ok("F3: --id with path traversal is refused unseen", f3b.code !== 0 && /not a valid pack id/.test(f3b.out), f3b.out.slice(-160));
// ...and a manifest reachable under a name it does not claim is refused.
const wrongName = join(repoRoot, "planning/holdouts/manifests", "HLD-S59-v1.yaml");
writeFileSync(wrongName, readFileSync(join(repoRoot, "planning/holdouts/manifests", "HLD-S99-v1.yaml"), "utf8"));
mkdirSync(join(repoRoot, "qa-private", "HLD-S59-v1"), { recursive: true });
const f3c = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S59-v1", "--candidate", "abc1230"]);
ok("F3: a manifest that claims a different id than its filename is refused",
   f3c.code !== 0 && /does not claim|says id/.test(f3c.out), f3c.out.slice(-200));
rmSync(wrongName, { force: true });

// F2 — outside a git repository used to be a console note; the sealed record was
// byte-indistinguishable from a verified run. Now: refusal without the override,
// and candidate_verified: false in the record with it.
const f2Id = "HLD-S58-v1";
const f2Dir = join(repoRoot, "qa-private", f2Id);
mkdirSync(f2Dir, { recursive: true });
writeFileSync(join(f2Dir, "README.md"), "# f2\n");
writeFileSync(join(f2Dir, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"echo hi\"\n");
writeFileSync(join(f2Dir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S58", "--story", "ST-58", "--contract", "v1"]);
const f2bare = (() => {   // deliberately WITHOUT the helper's override flag
  try {
    const out = execFileSync("bun", [TOOL, "--id", f2Id, "--candidate", "abc1230"],
      { cwd: repoRoot, encoding: "utf8", env: { ...process.env, WB_QA_CONTEXT: "1" }, stdio: ["ignore", "pipe", "pipe"] });
    return { code: 0, out };
  } catch (e: any) { return { code: e.status ?? 1, out: String(e.stdout ?? "") + String(e.stderr ?? "") }; }
})();
ok("F2: outside a git repository, reveal REFUSES without the explicit override",
   f2bare.code !== 0 && /not a git repository/.test(f2bare.out) &&
   /revealed_at: null/.test(readFileSync(join(repoRoot, "planning/holdouts/manifests", f2Id + ".yaml"), "utf8")),
   f2bare.out.slice(-200));
const f2run = run({ WB_QA_CONTEXT: "1" }, ["--id", f2Id, "--candidate", "abc1230"]);
const f2rec = readFileSync(join(repoRoot, "planning/evidence", "EVB-" + f2Id, "manifest.yaml"), "utf8");
ok("F2: with the override, the sealed record says candidate_verified: false",
   f2run.code === 0 && /candidate_verified: false/.test(f2rec), f2rec.slice(0, 300));
ok("F2: the manifest stamp says UNVERIFIED, not 'frozen'",
   /UNVERIFIED candidate/.test(readFileSync(join(repoRoot, "planning/holdouts/manifests", f2Id + ".yaml"), "utf8")));
const f2inj = run({ WB_QA_CONTEXT: "1" }, ["--id", f2Id, "--candidate", "abc1230\npid: 99999"]);
ok("F2: a candidate carrying a newline is refused by shape — YAML injection is dead",
   f2inj.code !== 0 && /not a commit sha/.test(f2inj.out), f2inj.out.slice(-160));

// F7 — a garbage timeout refuses up front. It used to throw MID-RUN (NaN) or
// silently disable the timer (0), both measured.
const f7a = run({ WB_QA_CONTEXT: "1", WB_HOLDOUT_CASE_TIMEOUT_MS: "not-a-number" }, ["--id", f2Id, "--candidate", "abc1230"]);
ok("F7: a non-numeric timeout env is refused before anything runs",
   f7a.code !== 0 && /WB_HOLDOUT_CASE_TIMEOUT_MS/.test(f7a.out), f7a.out.slice(-160));
const f7b = run({ WB_QA_CONTEXT: "1", WB_HOLDOUT_CASE_TIMEOUT_MS: "0" }, ["--id", f2Id, "--candidate", "abc1230"]);
ok("F7: a zero timeout is refused — it silently DISABLED the timer",
   f7b.code !== 0 && /WB_HOLDOUT_CASE_TIMEOUT_MS/.test(f7b.out), f7b.out.slice(-160));

// F1 — the answer key is not readable from inside a case. The case below IS the
// attack: it tries to read its own pack's expected.json mid-run. The custodian
// seals the expectation that the attempt FAILS (cat exits 1), so a pass here is
// a live demonstration that the pack was gone during execution.
const f1Id = "HLD-S57-v1";
const f1Dir = join(repoRoot, "qa-private", f1Id);
mkdirSync(f1Dir, { recursive: true });
writeFileSync(join(f1Dir, "README.md"), "# f1\n");
writeFileSync(join(f1Dir, "cases.yaml"),
  "cases:\n  - id: H1\n    class: hostile\n    run: \"cat qa-private/" + f1Id + "/expected.json\"\n");
writeFileSync(join(f1Dir, "expected.json"), JSON.stringify({ H1: { exit: 1 } }) + "\n");
seal(["--slice", "S57", "--story", "ST-57", "--contract", "v1"]);
const f1run = run({ WB_QA_CONTEXT: "1" }, ["--id", f1Id, "--candidate", "abc1230"]);
ok("F1: a case that reads its own pack's answer key mid-run finds NOTHING",
   f1run.code === 0 && /1 PASS \/ 0 FAIL/.test(f1run.out), f1run.out.slice(-240));
ok("F1: the pack is restored after the run, byte-identical",
   existsSync(join(f1Dir, "expected.json")) &&
   /post_run_pack_intact: true/.test(readFileSync(join(repoRoot, "planning/evidence", "EVB-" + f1Id, "manifest.yaml"), "utf8")));

// F6 — a case that rewrites the MANIFEST mid-run. The rewrite used to be what got
// stamped by this very tool. Now: the pre-run text is stamped, the rewrite is
// discarded, the record says manifest_rewritten_during_run: true, and the exit
// code is non-zero even though every case passed.
const f6Id = "HLD-S56-v1";
const f6Dir = join(repoRoot, "qa-private", f6Id);
mkdirSync(f6Dir, { recursive: true });
writeFileSync(join(f6Dir, "README.md"), "# f6\n");
writeFileSync(join(f6Dir, "cases.yaml"),
  "cases:\n  - id: H1\n    class: hostile\n    run: \"printf 'attacker-was-here' > planning/holdouts/manifests/" + f6Id + ".yaml\"\n");
writeFileSync(join(f6Dir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S56", "--story", "ST-56", "--contract", "v1"]);
const f6run = run({ WB_QA_CONTEXT: "1" }, ["--id", f6Id, "--candidate", "abc1230"]);
const f6man = readFileSync(join(repoRoot, "planning/holdouts/manifests", f6Id + ".yaml"), "utf8");
const f6rec = readFileSync(join(repoRoot, "planning/evidence", "EVB-" + f6Id, "manifest.yaml"), "utf8");
ok("F6: the attacker's rewrite of the manifest is DISCARDED — the validated text is stamped",
   !/attacker-was-here/.test(f6man) && /revealed_at: "/.test(f6man), f6man.slice(0, 200));
ok("F6: the record says manifest_rewritten_during_run: true",
   /manifest_rewritten_during_run: true/.test(f6rec));
ok("F6: tampering exits non-zero even though every case passed",
   f6run.code !== 0 && /1 PASS \/ 0 FAIL/.test(f6run.out) && /TAMPERING RECORDED/.test(f6run.out), f6run.out.slice(-300));

// F8 — attempts are on the record. Attempt 1 aborts on a per-case timeout (a
// harness limit, pack NOT spent); attempt 2 seals, and the record says attempt: 2.
const f8Id = "HLD-S55-v1";
const f8Dir = join(repoRoot, "qa-private", f8Id);
mkdirSync(f8Dir, { recursive: true });
writeFileSync(join(f8Dir, "README.md"), "# f8\n");
writeFileSync(join(f8Dir, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"sleep 1; echo hi\"\n");
writeFileSync(join(f8Dir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S55", "--story", "ST-55", "--contract", "v1"]);
const f8abort = run({ WB_QA_CONTEXT: "1", WB_HOLDOUT_CASE_TIMEOUT_MS: "80" }, ["--id", f8Id, "--candidate", "abc1230"]);
ok("F8: the timeout abort still refuses without spending the pack (spawnSync path re-verified)",
   f8abort.code !== 0 && /did not finish within 80 ms/.test(f8abort.out) &&
   /revealed_at: null/.test(readFileSync(join(repoRoot, "planning/holdouts/manifests", f8Id + ".yaml"), "utf8")),
   f8abort.out.slice(-200));
const f8run = run({ WB_QA_CONTEXT: "1" }, ["--id", f8Id, "--candidate", "abc1230"]);
const f8rec = readFileSync(join(repoRoot, "planning/evidence", "EVB-" + f8Id, "manifest.yaml"), "utf8");
ok("F8: the sealed record counts BOTH attempts — the abort is no longer invisible",
   f8run.code === 0 && /attempt: 2/.test(f8rec), f8rec.slice(0, 300));

// F11 — stderr of a SUCCEEDING case is hashed into the raw log.
const f11Id = "HLD-S54-v1";
const f11Dir = join(repoRoot, "qa-private", f11Id);
mkdirSync(f11Dir, { recursive: true });
writeFileSync(join(f11Dir, "README.md"), "# f11\n");
writeFileSync(join(f11Dir, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"echo visible; echo hidden-error 1>&2\"\n");
writeFileSync(join(f11Dir, "expected.json"), JSON.stringify({ H1: { exit: 0, stdout_contains: "visible" } }) + "\n");
seal(["--slice", "S54", "--story", "ST-54", "--contract", "v1"]);
const f11run = run({ WB_QA_CONTEXT: "1" }, ["--id", f11Id, "--candidate", "abc1230"]);
const f11bundle = join(repoRoot, "planning/evidence", "EVB-" + f11Id);
const f11log = readdirSync(f11bundle).filter((f) => f.endsWith(".log")).map((f) => readFileSync(join(f11bundle, f), "utf8")).join("");
ok("F11: a succeeding case's stderr is hashed into the raw log",
   f11run.code === 0 && new RegExp("stderr_sha256: " + sha256Hex("hidden-error\n")).test(f11log) && /stderr_bytes: 13/.test(f11log),
   f11log.slice(-300));

// F9 — cases.yaml ambiguity. Bun.YAML.parse keeps the LAST duplicate key in
// silence (MEASURED: run: twice parsed to the second command).
const f9Dir = join(repoRoot, "qa-private", "HLD-S53-v1");
mkdirSync(f9Dir, { recursive: true });
writeFileSync(join(f9Dir, "README.md"), "# f9\n");
writeFileSync(join(f9Dir, "cases.yaml"),
  "cases:\n  - id: H1\n    class: nominal\n    run: \"echo real\"\n    run: \"echo evil\"\n");
writeFileSync(join(f9Dir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
const f9seal = seal(["--slice", "S53", "--story", "ST-53", "--contract", "v1"]);
ok("F9: seal refuses a case carrying run: twice — a reader and the harness would disagree",
   f9seal.code !== 0 && /"run:" 2 times/.test(f9seal.out), f9seal.out.slice(-200));
manualSeal("HLD-S53-v1", f9Dir);
const f9rev = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S53-v1", "--candidate", "abc1230"]);
ok("F9: reveal refuses the same pack even when the manifest was written around seal",
   f9rev.code !== 0 && /"run:" 2 times/.test(f9rev.out) &&
   /revealed_at: null/.test(readFileSync(join(repoRoot, "planning/holdouts/manifests", "HLD-S53-v1.yaml"), "utf8")),
   f9rev.out.slice(-200));
writeFileSync(join(f9Dir, "cases.yaml"), 'cases:\n  - { id: H1, class: nominal, run: "echo a", run: "echo b" }\n');
const f9flow = seal(["--slice", "S53", "--story", "ST-53", "--contract", "v1"]);
ok("F9: flow-style case mappings are refused outright rather than scanned",
   f9flow.code !== 0 && /flow-style/.test(f9flow.out), f9flow.out.slice(-160));

// F4 — the pack ROOT itself as a symlink. The walk refused symlinks it found,
// but followed one it was handed.
const f4Real = join(tmp, "outside-pack");
mkdirSync(f4Real, { recursive: true });
writeFileSync(join(f4Real, "README.md"), "# f4\n");
writeFileSync(join(f4Real, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"echo hi\"\n");
writeFileSync(join(f4Real, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
const f4Link = join(repoRoot, "qa-private", "HLD-S52-v1");
symlinkSync(f4Real, f4Link);
manualSeal("HLD-S52-v1", f4Real);
const f4run = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S52-v1", "--candidate", "abc1230"]);
ok("F4: a pack whose ROOT is a symlink out of the tree is refused",
   f4run.code !== 0 && /is a symlink/.test(f4run.out), f4run.out.slice(-200));
rmSync(f4Link, { force: true });

// F5 — the executable bit now moves the digest (wb-canon-2).
const f5Dir = join(tmp, "f5-pack");
mkdirSync(f5Dir, { recursive: true });
writeFileSync(join(f5Dir, "README.md"), "# f5\n");
writeFileSync(join(f5Dir, "cases.yaml"), "cases: []\n");
writeFileSync(join(f5Dir, "expected.json"), "{}\n");
const f5Before = canonicalPackHash(f5Dir).digest;
chmodSync(join(f5Dir, "cases.yaml"), 0o755);
ok("F5: flipping the executable bit MOVES the pack digest",
   canonicalPackHash(f5Dir).digest !== f5Before);
chmodSync(join(f5Dir, "cases.yaml"), 0o644);
ok("F5: restoring the bit restores the digest", canonicalPackHash(f5Dir).digest === f5Before);
mkdirSync(join(f5Dir, "empty-dir"));
let f5Threw = "";
try { canonicalPackHash(f5Dir); } catch (e: any) { f5Threw = String(e?.message ?? e); }
ok("F5: an empty directory in a pack is refused", /empty directory/.test(f5Threw), f5Threw.slice(0, 120));

// F10 — the expectation shape check covers every field.
const f10Dir = join(repoRoot, "qa-private", "HLD-S51-v1");
mkdirSync(f10Dir, { recursive: true });
writeFileSync(join(f10Dir, "README.md"), "# f10\n");
writeFileSync(join(f10Dir, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"echo hi\"\n");
const f10try = (expectedBody: string, label: string, want: RegExp) => {
  writeFileSync(join(f10Dir, "expected.json"), expectedBody);
  rmSync(join(repoRoot, "planning/holdouts/manifests", "HLD-S51-v1.yaml"), { force: true });
  rmSync(join(repoRoot, "planning/evidence", "EVB-HLD-S51-v1"), { recursive: true, force: true });
  manualSeal("HLD-S51-v1", f10Dir);
  const r = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S51-v1", "--candidate", "abc1230"]);
  ok(label, r.code !== 0 && want.test(r.out), r.out.slice(-220));
};
f10try('{"H1": {"exit": 0, "stdout_sha265": "x"}}',
       "F10: a MISSPELLED expectation field is refused, not silently ignored", /unknown expectation field/);
f10try('{"H1": {"exit": 0, "stdout_contains": ""}}',
       "F10: an empty stdout_contains is refused — it matches everything and checks nothing", /non-empty string/);
f10try('{"H1": {"exit": 0, "stdout_sha256": "ABC"}}',
       "F10: a malformed stdout_sha256 is refused", /64 lowercase hex/);

console.log("— security re-review S1-S9, each defeat pinned —");

// S1 — the first F1 fix was DEFEATED, executed, two ways: the lock file published
// pack_hidden_at at a path derived from --id, and $TMPDIR held stale wb-reveal-*
// hide dirs findable with one glob. The pack now lives in reveal's MEMORY: no
// pointer to leak because there is no location to point at.
const s1Id = "HLD-S48-v1";
const s1Dir = join(repoRoot, "qa-private", s1Id);
mkdirSync(s1Dir, { recursive: true });
writeFileSync(join(s1Dir, "README.md"), "# s1\n");
// The case IS the reviewer's attack: read the lock hunting for the pointer.
writeFileSync(join(s1Dir, "cases.yaml"),
  "cases:\n  - id: H1\n    class: hostile\n    run: \"! grep -q pack_hidden_at planning/evidence/EVB-" + s1Id + "/.reveal.lock\"\n");
writeFileSync(join(s1Dir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S48", "--story", "ST-48", "--contract", "v1"]);
const tmpRootS1 = process.env.TMPDIR ?? "/tmp";
const hideDirsBefore = readdirSync(tmpRootS1).filter((d) => d.startsWith("wb-reveal-")).length;
const s1run = run({ WB_QA_CONTEXT: "1" }, ["--id", s1Id, "--candidate", "abc1230"]);
const hideDirsAfter = readdirSync(tmpRootS1).filter((d) => d.startsWith("wb-reveal-")).length;
ok("S1: the lock carries NO pointer to the pack during the run — the case looked",
   s1run.code === 0 && /1 PASS \/ 0 FAIL/.test(s1run.out), s1run.out.slice(-240));
ok("S1/S9: a reveal creates NO hide directory in $TMPDIR — nothing for a glob to find",
   hideDirsAfter === hideDirsBefore, `before=${hideDirsBefore} after=${hideDirsAfter}`);

// S3 — SIGTERM two seconds into a run used to leave the repository's only copy of
// an unrevealed pack stranded in /var/folders. Executed by the reviewer. The
// restore now runs from memory on SIGINT/SIGTERM/SIGHUP.
const s3Id = "HLD-S47-v1";
const s3Dir = join(repoRoot, "qa-private", s3Id);
mkdirSync(s3Dir, { recursive: true });
writeFileSync(join(s3Dir, "README.md"), "# s3\n");
writeFileSync(join(s3Dir, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"sleep 5; echo hi\"\n");
writeFileSync(join(s3Dir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S47", "--story", "ST-47", "--contract", "v1"]);
const s3HashBefore = canonicalPackHash(s3Dir).digest;
// The kill must hit BUN, not a wrapper shell. An earlier version wrote
// `cd X && bun ... &`, which backgrounds the WHOLE `cd && bun` compound — $! was
// the subshell, the kill orphaned the reveal instead of ending it, and the
// orphan finished, sealed, and raced the next test's reveal over one bundle.
// (reveal.ts caught that interference and flagged it, which is how the launcher
// bug was found.) cwd comes from execFileSync, so nothing wraps bun.
execFileSync("/bin/sh", ["-c",
  `WB_QA_CONTEXT=1 bun ${JSON.stringify(TOOL)} --id ${s3Id} --candidate abc1230 --allow-unverified-candidate > /dev/null 2>&1 & pid=$!; sleep 1.2; kill -TERM $pid 2>/dev/null; wait $pid 2>/dev/null; exit 0`,
], { cwd: repoRoot });
// v3 contract, measured: a signal handler CANNOT run while bun is blocked inside
// spawnSync, so nothing restores on SIGTERM — and nothing needs to. The pack
// never left its path; the kill leaves it at mode 000, intact.
ok("S3: after a SIGTERM mid-run the pack is still ON DISK at its own path, locked",
   existsSync(s3Dir) && (lstatSync(s3Dir).mode & 0o777) === 0, `mode=${(lstatSync(s3Dir).mode & 0o777).toString(8)}`);
ok("S3: ...and the interrupted pack is NOT spent",
   /revealed_at: null/.test(readFileSync(join(repoRoot, "planning/holdouts/manifests", s3Id + ".yaml"), "utf8")));
const s3Locked = run({ WB_QA_CONTEXT: "1" }, ["--id", s3Id, "--candidate", "abc1230"]);
ok("S3: revealing a locked-down pack refuses WITH the recovery command",
   s3Locked.code !== 0 && /interrupted reveal/.test(s3Locked.out) && /chmod u\+rwX/.test(s3Locked.out), s3Locked.out.slice(-260));
execFileSync("/bin/sh", ["-c", `chmod u+rwX ${JSON.stringify(s3Dir)} && chmod -R u+rwX ${JSON.stringify(s3Dir)}`]);
ok("S3: one chmod recovers it byte-identical — nothing was ever outside the repository",
   canonicalPackHash(s3Dir).digest === s3HashBefore);

// S4 — one `rm attempts.log` reset the sealed attempt counter to 1 (executed by
// the reviewer). Now: a bundle with content but no attempts log refuses, and an
// edited line breaks the hash chain and refuses.
const s4Bundle = join(repoRoot, "planning/evidence", "EVB-" + s3Id);
// The SIGTERM above also stranded the lock — by design ("deliberately not
// automatic"). The documented manual recovery removes it before going on.
rmSync(join(s4Bundle, ".reveal.lock"), { force: true });
ok("S4: the aborted attempt above IS on the chained record",
   existsSync(join(s4Bundle, "attempts.log")) && /attempt=1 /.test(readFileSync(join(s4Bundle, "attempts.log"), "utf8")));
rmSync(join(s4Bundle, "attempts.log"), { force: true });
const s4NoLog = run({ WB_QA_CONTEXT: "1" }, ["--id", s3Id, "--candidate", "abc1230"]);
ok("S4: a bundle with content but NO attempts.log is refused — the rm is no longer silent",
   s4NoLog.code !== 0 && /no attempts.log/.test(s4NoLog.out), s4NoLog.out.slice(-200));
writeFileSync(join(s4Bundle, "attempts.log"), `attempt=1 at=2026-01-01T00:00:00Z pid=1 candidate=abc1230 prev=GENESIS\nattempt=2 at=2026-01-01T00:00:01Z pid=2 candidate=abc1230 prev=WRONGHASH\n`);
const s4BadChain = run({ WB_QA_CONTEXT: "1" }, ["--id", s3Id, "--candidate", "abc1230"]);
ok("S4: an attempts.log whose lines do not chain is refused as edited",
   s4BadChain.code !== 0 && /does not chain/.test(s4BadChain.out), s4BadChain.out.slice(-200));
rmSync(s4Bundle, { recursive: true, force: true });   // stated limit: whole-dir deletion is the boundary

// S2 — the detection fields used to live outside the only hash; flipping one with
// sed left raw_log_sha256 identical (executed by the reviewer). They are now IN
// the hashed log, and verify-run-records.ts cross-checks the two halves.
const s2run = run({ WB_QA_CONTEXT: "1" }, ["--id", s3Id, "--candidate", "abc1230"]);
const s2Bundle = join(repoRoot, "planning/evidence", "EVB-" + s3Id);
const s2Logs = readdirSync(s2Bundle).filter((f) => f.endsWith(".log") && f.startsWith("holdout-run-"));
ok("S2: exactly ONE run log exists — no concurrent reveal sealed this bundle", s2Logs.length === 1, s2Logs.join(", "));
const s2LogName = s2Logs[0];
const s2Log = readFileSync(join(s2Bundle, s2LogName), "utf8");
ok("S2: every integrity field is inside the HASHED log",
   s2run.code === 0 &&
   /candidate_verified: false/.test(s2Log) && /attempt: 1/.test(s2Log) &&
   /post_run_pack_intact: true/.test(s2Log) && /manifest_rewritten_during_run: false/.test(s2Log) &&
   /attempts_log_sha256: [0-9a-f]{64}/.test(s2Log),
   s2Log.slice(-400) + " ||EXIT=" + s2run.code + "|| " + s2run.out.slice(-200));
const VERIFY_RECORDS = join(process.cwd(), "tools/holdout/verify-run-records.ts");
const vrr = (cwd: string) => {
  try { return { code: 0, out: execFileSync("bun", [VERIFY_RECORDS], { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }) }; }
  catch (e: any) { return { code: e.status ?? 1, out: String(e.stdout ?? "") + String(e.stderr ?? "") }; }
};
const vrr1 = vrr(repoRoot);
ok("S2: verify-run-records PASSES every honestly sealed bundle", vrr1.code === 0, vrr1.out.slice(-300));
const s2Man = join(s2Bundle, "manifest.yaml");
writeFileSync(s2Man, readFileSync(s2Man, "utf8").replace("candidate_verified: false", "candidate_verified: true"));
const vrr2 = vrr(repoRoot);
ok("S2: the reviewer's sed flip of candidate_verified is now CAUGHT",
   vrr2.code !== 0 && /candidate_verified DISAGREES/.test(vrr2.out), vrr2.out.slice(-300));
writeFileSync(s2Man, readFileSync(s2Man, "utf8").replace("candidate_verified: true", "candidate_verified: false"));
const s2LogPath = join(s2Bundle, s2LogName);
writeFileSync(s2LogPath, readFileSync(s2LogPath, "utf8").replace("post_run_pack_intact: true", "post_run_pack_intact: banana"));
const vrr3 = vrr(repoRoot);
ok("S2: an edited raw log is CAUGHT by its own hash", vrr3.code !== 0 && /raw_log_sha256 mismatch/.test(vrr3.out), vrr3.out.slice(-300));

// The ctime tripwire, attacked. A case that chmods the pack directory to reach
// inside it moves the dir's ctime — a timestamp only the kernel writes and no
// same-user process can rewind. The reach itself becomes a sealed fact, even
// when the case puts the mode back afterwards.
const twId = "HLD-S42-v1";
const twDir = join(repoRoot, "qa-private", twId);
mkdirSync(twDir, { recursive: true });
writeFileSync(join(twDir, "README.md"), "# ctime tripwire\n");
writeFileSync(join(twDir, "cases.yaml"),
  "cases:\n  - id: H1\n    class: hostile\n    run: \"chmod 700 qa-private/" + twId + "; chmod 000 qa-private/" + twId + "; true\"\n");
writeFileSync(join(twDir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S42", "--story", "ST-42", "--contract", "v1"]);
const twRun = run({ WB_QA_CONTEXT: "1" }, ["--id", twId, "--candidate", "abc1230"]);
const twRec = readFileSync(join(repoRoot, "planning/evidence", "EVB-" + twId, "manifest.yaml"), "utf8");
ok("TRIPWIRE: a case that chmods the pack dir and puts it back is still RECORDED",
   /post_run_pack_untouched: false/.test(twRec), twRec.slice(0, 400));
ok("TRIPWIRE: ...and the reach fails the exit code even though the case passed",
   twRun.code !== 0 && /1 PASS \/ 0 FAIL/.test(twRun.out) && /TAMPERING RECORDED/.test(twRun.out), twRun.out.slice(-260));

// ...and the other direction: an honest run records post_run_pack_untouched: true.
ok("TRIPWIRE: an honest run seals post_run_pack_untouched: true",
   /post_run_pack_untouched: true/.test(f2rec) || /post_run_pack_untouched: true/.test(readFileSync(join(repoRoot, "planning/evidence", "EVB-" + f1Id, "manifest.yaml"), "utf8")));

// The HARDLINK route, attacked. A hardlink is a second name for the same file;
// directory permissions do not apply to it, because mode lives on the inode.
// An implementer who hardlinks expected.json BEFORE the reveal can read straight
// through it — UNLESS the files themselves drop to mode 000. This is the one
// attack the per-file lockdown exists for, and the mutant that skipped that
// lockdown survived the suite until this test.
const hlId = "HLD-S41A-v1";
const hlDir = join(repoRoot, "qa-private", hlId);
const hlLink = join(tmp, "smuggled-answer-key");
mkdirSync(hlDir, { recursive: true });
writeFileSync(join(hlDir, "README.md"), "# hardlink\n");
writeFileSync(join(hlDir, "cases.yaml"),
  "cases:\n  - id: H1\n    class: hostile\n    run: \"cat " + hlLink + "\"\n");
writeFileSync(join(hlDir, "expected.json"), JSON.stringify({ H1: { exit: 1 } }) + "\n");
seal(["--slice", "S41A", "--story", "ST-41", "--contract", "v1"]);
linkSync(join(hlDir, "expected.json"), hlLink);   // the attacker's pre-made second name
const hlRun = run({ WB_QA_CONTEXT: "1" }, ["--id", hlId, "--candidate", "abc1230"]);
ok("HARDLINK: a pre-made hardlink to the answer key reads NOTHING during the run",
   hlRun.code === 0 && /1 PASS \/ 0 FAIL/.test(hlRun.out), hlRun.out.slice(-240));
rmSync(hlLink, { force: true });

// S6 — a FIFO left the digest byte-identical (executed by the reviewer).
const s6Dir = join(tmp, "s6-pack");
mkdirSync(s6Dir, { recursive: true });
writeFileSync(join(s6Dir, "README.md"), "# s6\n");
writeFileSync(join(s6Dir, "cases.yaml"), "cases: []\n");
writeFileSync(join(s6Dir, "expected.json"), "{}\n");
execFileSync("mkfifo", [join(s6Dir, "helper")]);
let s6Threw = "";
try { canonicalPackHash(s6Dir); } catch (e: any) { s6Threw = String(e?.message ?? e); }
ok("S6: a FIFO in a pack is refused, as symlinks and empty dirs already are",
   /not a regular file/.test(s6Threw), s6Threw.slice(0, 120));

rmSync(tmp, { recursive: true, force: true });
console.log(`\n${pass}/${pass + fail} passed.`);
if (fail) { console.log("FAILURES PRESENT — exit 1"); process.exit(1); }
process.exit(0);
