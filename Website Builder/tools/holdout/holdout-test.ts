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
import { mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, symlinkSync, utimesSync, writeFileSync, existsSync } from "node:fs";
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
const run = (env: Record<string, string>, args: string[], cwd = repoRoot) => {
  try {
    const out = execFileSync("bun", [TOOL, ...args], { cwd, encoding: "utf8", env: { ...process.env, ...env }, stdio: ["ignore", "pipe", "pipe"] });
    return { code: 0, out };
  } catch (e: any) { return { code: e.status ?? 1, out: String(e.stdout ?? "") + String(e.stderr ?? "") }; }
};
const gated = run({}, ["--id", "HLD-S99-v1", "--candidate", "abc123"]);
ok("refuses without WB_QA_CONTEXT=1", gated.code !== 0 && /only in the QA review context/.test(gated.out));
const dry = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S99-v1", "--candidate", "abc123", "--dry-run"]);
ok("--dry-run verifies both hashes and runs nothing", dry.code === 0 && /MATCH/.test(dry.out) && /NOT run/.test(dry.out), dry.out.slice(-200));
ok("--dry-run leaves revealed_at untouched", /revealed_at: null/.test(readFileSync(join(repoRoot, "planning/holdouts/manifests/HLD-S99-v1.yaml"), "utf8")));

write("README.md", before + "tampered");
const mism = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S99-v1", "--candidate", "abc123"]);
ok("a tampered pack refuses and runs NOTHING", mism.code !== 0 && /MISMATCH/.test(mism.out) && /NOTHING WAS RUN/.test(mism.out));
write("README.md", before);

const real = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S99-v1", "--candidate", "abc123"]);
ok("a real reveal runs every case and seals a run record", real.code === 0 && /2 PASS \/ 0 FAIL/.test(real.out) && existsSync(join(repoRoot, "planning/evidence/EVB-HLD-S99-v1/manifest.yaml")), real.out.slice(-300));
const spent = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S99-v1", "--candidate", "abc123"]);
ok("a revealed pack is SPENT and refuses a second run", spent.code !== 0 && /already revealed/.test(spent.out));

console.log("— seal, the custodian side —");
const SEAL = join(process.cwd(), "tools/holdout/seal.ts");
const seal = (args: string[], cwd = repoRoot) => {
  try { return { code: 0, out: execFileSync("bun", [SEAL, ...args], { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }) }; }
  catch (e: any) { return { code: e.status ?? 1, out: String(e.stdout ?? "") + String(e.stderr ?? "") }; }
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
const rt = run({ WB_QA_CONTEXT: "1" }, ["--id", rtId, "--candidate", "cafe01"]);
ok("a sealed pack reveals cleanly — seal and reveal agree on the hash", rt.code === 0 && /2 PASS \/ 0 FAIL/.test(rt.out), rt.out.slice(-300));

// a FAILING pack must exit non-zero and keep its result
const failDir = join(repoRoot, "qa-private", "HLD-S95-v1");
mkdirSync(failDir, { recursive: true });
writeFileSync(join(failDir, "README.md"), "#\n");
writeFileSync(join(failDir, "cases.yaml"), "cases:\n  - id: H001\n    class: nominal\n    run: \"exit 1\"\n");
writeFileSync(join(failDir, "expected.json"), JSON.stringify({ H001: { exit: 0 } }) + "\n");
seal(["--slice", "S95", "--story", "ST-95", "--contract", "v1"]);
const bad = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S95-v1", "--candidate", "cafe02"]);
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
const big = run({ WB_QA_CONTEXT: "1" }, ["--id", bigId, "--candidate", "cafe03"]);
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
                 ["--id", hangId, "--candidate", "cafe04"]);
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
const bytes = run({ WB_QA_CONTEXT: "1" }, ["--id", byteId, "--candidate", "cafe05"]);
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
const second = run({ WB_QA_CONTEXT: "1" }, ["--id", rtId, "--candidate", "cafe06"]);
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
  " > " + rc + "/" + tag + ".log 2>&1; echo $? > " + rc + "/" + tag + ".rc ) &";
execFileSync("/bin/sh", ["-c",
  "cd " + JSON.stringify(repoRoot) + " && " + one("race-aaa", "a") + " " + one("race-bbb", "b") + " wait",
], { encoding: "utf8" });
const rcA = readFileSync(join(rc, "a.rc"), "utf8").trim();
const rcB = readFileSync(join(rc, "b.rc"), "utf8").trim();
ok("two concurrent reveals of one id: EXACTLY ONE succeeds",
   [rcA, rcB].filter((x) => x === "0").length === 1, "exit codes " + rcA + " and " + rcB);
const raceMan = readFileSync(join(repoRoot, "planning/holdouts/manifests", raceId + ".yaml"), "utf8");
const raceEvb = readFileSync(join(repoRoot, "planning/evidence", "EVB-" + raceId, "manifest.yaml"), "utf8");
const manCand = (/frozen candidate (\S+);/.exec(raceMan) ?? [])[1] ?? "";
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
const held = run({ WB_QA_CONTEXT: "1" }, ["--id", heldId, "--candidate", "cafe09"]);
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
const wrongSha = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S90-v1", "--candidate", "totally-fabricated-not-a-sha"], repo2);
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
const malformed = run({ WB_QA_CONTEXT: "1" }, ["--id", badId, "--candidate", "cafe07"]);
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
const u8 = run({ WB_QA_CONTEXT: "1" }, ["--id", u8Id, "--candidate", "cafe08"]);
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
const zcRun = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S86-v1", "--candidate", "totally-made-up-not-a-commit"], zc);
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
const ct = run({ WB_QA_CONTEXT: "1" }, ["--id", ctId, "--candidate", "cafe10"]);
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
const dupRun = run({ WB_QA_CONTEXT: "1" }, ["--id", dupId, "--candidate", "cafe11"]);
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
seal(["--slice", "S82", "--story", "ST-82", "--contract", "v1"]);
const dkRun = run({ WB_QA_CONTEXT: "1" }, ["--id", dkId, "--candidate", "cafe12"]);
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
const bigRun = run({ WB_QA_CONTEXT: "1" }, ["--id", bigCountId, "--candidate", "cafe13"]);
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
seal(["--slice", "S76", "--story", "ST-76", "--contract", "v1"]);
const meta = run({ WB_QA_CONTEXT: "1" }, ["--id", metaId, "--candidate", "cafe14"]);
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
const okMeta = run({ WB_QA_CONTEXT: "1" }, ["--id", okMetaId, "--candidate", "cafe15"]);
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
seal(["--slice", "S74", "--story", "ST-74", "--contract", "v1"]);
const esc = run({ WB_QA_CONTEXT: "1" }, ["--id", escId, "--candidate", "cafe16"]);
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
seal(["--slice", "S73", "--story", "ST-73", "--contract", "v1"]);
const ws = run({ WB_QA_CONTEXT: "1" }, ["--id", wsId, "--candidate", "cafe17"]);
ok("a duplicate key separated from its colon by newlines and tabs is REFUSED", ws.code !== 0 && /repeats key/.test(ws.out), ws.out.slice(-260));

// A duplicate NESTED inside one entry is just as dangerous: a repeated "exit"
// silently changes that case's expectation. Scope is the whole document.
const nestId = "HLD-S71-v1";
const nestDir = join(repoRoot, "qa-private", nestId);
mkdirSync(nestDir, { recursive: true });
writeFileSync(join(nestDir, "README.md"), "# nested duplicate\n");
writeFileSync(join(nestDir, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"echo hi\"\n");
writeFileSync(join(nestDir, "expected.json"), '{\n  "H1": { "exit": 0, "exit": 9 }\n}\n');
seal(["--slice", "S71", "--story", "ST-71", "--contract", "v1"]);
const nest = run({ WB_QA_CONTEXT: "1" }, ["--id", nestId, "--candidate", "cafe18"]);
ok("a duplicate key nested INSIDE one expectation is REFUSED", nest.code !== 0 && /repeats key/.test(nest.out), nest.out.slice(-260));

// The other half, and the reason the scanner decodes keys rather than hunting for
// text: a string that merely LOOKS like a key, sitting in value position, must NOT
// refuse. The previous indexOf scan would have counted this as a duplicate.
const valId = "HLD-S72-v1";
const valDir = join(repoRoot, "qa-private", valId);
mkdirSync(valDir, { recursive: true });
writeFileSync(join(valDir, "README.md"), "# lookalike in a value\n");
writeFileSync(join(valDir, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"echo hi\"\n");
writeFileSync(join(valDir, "expected.json"),
  '{\n  "H1": { "exit": 0, "note": "\\"H1\\" : this is a VALUE, not a key" }\n}\n');
seal(["--slice", "S72", "--story", "ST-72", "--contract", "v1"]);
const val = run({ WB_QA_CONTEXT: "1" }, ["--id", valId, "--candidate", "cafe19"]);
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
writeFileSync(join(deepDir, "expected.json"), '{\n  "H1": { "exit": 0, "meta": { "H1": 1 } }\n}\n');
seal(["--slice", "S69", "--story", "ST-69", "--contract", "v1"]);
const deep = run({ WB_QA_CONTEXT: "1" }, ["--id", deepId, "--candidate", "cafe20"]);
ok("the same id as a key in a DIFFERENT nested object is not a duplicate",
   deep.code === 0 && /1 PASS \/ 0 FAIL/.test(deep.out), deep.out.slice(-260));

// The sharpest false-refusal case: a string VALUE whose text is identical to a
// key in the SAME object. Here "exit" is both a key and, separately, the note's
// value. Only the key position may be recorded, or the guard starts rejecting
// ordinary packs — and a guard that refuses valid work is not a safer guard.
const sameId = "HLD-S68-v1";
const sameDir = join(repoRoot, "qa-private", sameId);
mkdirSync(sameDir, { recursive: true });
writeFileSync(join(sameDir, "README.md"), "# value equals a sibling key\n");
writeFileSync(join(sameDir, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"echo hi\"\n");
writeFileSync(join(sameDir, "expected.json"), '{\n  "H1": { "exit": 0, "note": "exit" }\n}\n');
seal(["--slice", "S68", "--story", "ST-68", "--contract", "v1"]);
const same = run({ WB_QA_CONTEXT: "1" }, ["--id", sameId, "--candidate", "cafe21"]);
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
  return { sealed, reveal: () => run({ WB_QA_CONTEXT: "1" }, ["--id", id, "--candidate", "cafe" + slice.slice(1)]) };
};

// 1. A SURROGATE PAIR. "H😀" and a literal H followed by U+1F600 are the
// same key to JSON.parse. The two spellings share almost no bytes, which is the
// same shape of attack that defeated the previous scan with "1".
const astral = "H\u{1F600}";
const fz1 = fuzzPack("HLD-S66-v1", JSON.stringify(astral),
  '{\n  "' + astral + '": { "exit": 0 },\n  "H' + '\\uD83D\\uDE00": { "exit": 9 }\n}\n', "S66");
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
const r3 = fz3.reveal();
ok("a key holding a literal backslash, spelled two ways, is REFUSED",
   r3.code !== 0 && /repeats key/.test(r3.out), r3.out.slice(-240));

// 4. An ESCAPED QUOTE inside the key, spelled two ways. If the scanner mistook the
// escaped quote for the end of the string, every frame after it would desync.
const quoteId = 'a"b';
const fz4 = fuzzPack("HLD-S63-v1", JSON.stringify(quoteId),
  '{\n  "a\\"b": { "exit": 0 },\n  "a' + '\\u0022b": { "exit": 9 }\n}\n', "S63");
const r4 = fz4.reveal();
ok("a key holding an escaped quote, spelled two ways, is REFUSED",
   r4.code !== 0 && /repeats key/.test(r4.out), r4.out.slice(-240));

// 5. A string VALUE stuffed with the characters that drive the frame stack. If any
// of these were read outside the string, the tokenizer would push or pop a frame
// that JSON.parse never saw, and every later key would land in the wrong object.
const fz5 = fuzzPack("HLD-S62-v1", "H1",
  '{\n  "H1": { "exit": 0, "note": "}}} {{{ [[[ ]]] ,,, ::: \\" \\\\ " }\n}\n', "S62");
const r5 = fz5.reveal();
ok("braces, brackets, commas, colons, a quote and a backslash inside a VALUE do not desync the scan",
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

rmSync(tmp, { recursive: true, force: true });
console.log(`\n${pass}/${pass + fail} passed.`);
if (fail) { console.log("FAILURES PRESENT — exit 1"); process.exit(1); }
process.exit(0);
