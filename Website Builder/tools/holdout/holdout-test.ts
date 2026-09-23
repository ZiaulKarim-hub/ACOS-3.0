#!/usr/bin/env bun
/**
 * holdout-test.ts — S79's own layer-1 verification.
 *
 * Expect 200/200. Raised from 194 on 2026-09-23 after the EIGHTH security review
 * returned REJECT with Z1-Z3: the planted-config foothold, neutralized for
 * reveal's calls (X2), still fired in the CUSTODIAN's own plain `git status` —
 * during the authoring window, harvesting the next pack's plaintext answers
 * (fix: command-valued local config is DETECTED — seal refuses, reveal refuses
 * pre-run, and a mid-run plant is sealed as tampering with the keys named);
 * signing a shrink as holdout-reveal@local bought SILENCE where a foreign
 * author left a branded brick — the incentive was inverted (fix: every shrink
 * bricks; the reveal-identity spelling is marked FORGED); and bricked_author
 * was attacker-chosen free text presented as attribution (fix: renamed to
 * bricked_commit_author_claim, with the unauthenticated-identity caveat in the
 * record itself).
 *
 * Previously 194/194. Raised from 186 on 2026-09-23 after the SEVENTH security review
 * returned REJECT with X1-X4: a forward MERGE commit whose tree carried the old
 * anchor (seal commit as second parent) was TREESAME-simplified out of
 * `git log -- path`, hiding every growth commit from the W1 walk and un-spending
 * a W2-sealed pack — one ordinary ref update, inside the stated boundary
 * (fix: --full-history, both walkers); a case planted core.fsmonitor in
 * .git/config and git executed it INSIDE reveal's own status/commit calls with
 * reveal's full environment, persistently (fix: GIT_SAFE prefix on EVERY git
 * call); the W1 refusal was PERMANENT, so one hostile anchor commit denied all
 * future verdicts deniably (fix: a terminal BRICKED run record is sealed once,
 * and verify-run-records confirms the brick is real before honoring it); and
 * bidi controls (U+202E) are fixed points of canonicalization that render
 * reversed while executing forwards (fix: byte-level refusal of bidi/zero-width
 * codepoints in case string fields, at seal and at reveal).
 *
 * Previously 186/186. Raised from 175 on 2026-09-23 after the SIXTH security review
 * returned REJECT with W1-W5: an ordinary FORWARD COMMIT of a truncated anchor
 * defeated the HEAD-prefix check (the committed copy WAS the truncation); a
 * spent pack was re-sat with two seds and an rm -rf, because revealed_at's
 * committed state is null; a ONE-LINE flow mapping bypassed the dash-anchored
 * flow refusal and executed a hidden second command; and a case that COMMITTED
 * its own edit read as a clean tree. Now: the anchor's whole commit history
 * must be append-only (every blob a prefix of the next); a sealed reveal
 * appends and commits a `revealed` spent marker to the chain (its committed
 * state is its ABSENCE, so reverting shows); the sealed cases.yaml must BE the
 * canonical serialization of its own parse (wb-cases-1 — kills the whole
 * YAML-spelling class, three passes of regex defeats); HEAD after the cases
 * must equal the commit reveal itself made; and reveal's git commits run with
 * hooks disabled (a planted pre-commit hook is pinned harmless).
 *
 * Previously 175/175. Raised from 169 on 2026-09-23 after the FIFTH security review
 * returned REJECT with V1-V3: SIGKILL bypassed the U1 exit-handler heal (a
 * signal is not an exit) and truncating both chain copies to the COMMITTED
 * genesis left git status empty — the forged state WAS the committed state;
 * a QUOTED key spelling ("run":) slipped past caseKeyProblems while Bun.YAML
 * treated it as the same key; and seal printed the answer key only AFTER
 * deleting the plaintext, leaving a crash window that strands an unopenable
 * pack. Now: reveal COMMITS every attempt line before any case runs (a kill
 * cannot un-commit; HEAD's copy must be a prefix of the working tree's),
 * quoted spellings count as the bare key, and the key prints before the
 * deletion. The burn is pinned live: truncate-both + kill -9, recovery, then
 * the refusal that reads the committed history.
 *
 * Previously 169/169. Raised from 161 later on 2026-09-23 after the FOURTH security
 * review returned REJECT with U1-U3: the T4 git filter had CANCELLED the T3
 * anchor (a case truncated the tracked chain during an ABORTED run — no
 * post-run check fires there — and the next seal affirmed attempt: 1); the
 * bundle directory was a write-anything blind zone (a planted second run log
 * passed the verifier); and cases inherited reveal's whole environment (a live
 * API key was ps-readable from inside a case). Now: the anchor leaves the
 * blind zone unless its bytes equal what reveal itself wrote, an exit handler
 * heals aborted-run truncation from memory and preserves the found bytes, the
 * bundle is censused before sealing, the verifier demands exactly one run log,
 * and cases get a minimal PATH/HOME/TMPDIR environment with a canary test.
 *
 * Previously 161/161. Raised from 138 on 2026-09-23 after the THIRD security review
 * returned REJECT with two EXECUTED forgeries: T1, a file descriptor opened
 * before the mode-000 lockdown read the plaintext answer key straight through
 * it (POSIX checks permission at open, not read); and T2, a multi-line case
 * `run` string injected footer fields into the hashed log, which the verifier's
 * first-match scan then trusted. The pack's answer key is now CIPHERTEXT on
 * disk (seal encrypts, reveal takes the key on stdin, plaintext exists only in
 * memory); the run record has delimited trust regions; the attempts chain is
 * anchored in a TRACKED file (T3); and post_run_tree_clean states its own
 * limits inside the record (T4). The new tests re-run the reviewer's own
 * attacks — the fd daemon now harvests ciphertext, the injection is refused at
 * both tools, the forged-bundle sed flip is caught by region parsing, and both
 * live branches of post_run_tree_clean are exercised in a real git fixture.
 *
 * Previously 138/138 (v3 lockdown + ctime tripwire + hardlink attack).
 * Before that, expect 71/71. Raised from 68 on 2026-09-22 after a review DEFEATED the
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
import { ENC_NAME, PLAIN_NAME, decryptExpected, encryptExpected, newKeyHex } from "./keybox.ts";
import { canonicalCasesText, caseKeyProblems } from "./json-keys.ts";
import { validate } from "./manifest.ts";
import { duplicateJsonKeys } from "./json-keys.ts";

// T1: every sealed pack's answer key is ciphertext; the suite plays custodian
// and keeps each pack's key here, handing it to reveal on stdin like the real
// flow does. seal() parses the key seal.ts prints; encryptPack() is the
// manual-seal equivalent.
const packKeys = new Map<string, string>();
const encryptPack = (id: string, dir: string): string => {
  const plain = join(dir, PLAIN_NAME);
  rmSync(join(dir, ENC_NAME), { force: true });   // a stale seal never survives a re-author
  const key = newKeyHex();
  writeFileSync(join(dir, ENC_NAME), encryptExpected(readFileSync(plain), key));
  rmSync(plain);
  packKeys.set(id, key);
  return key;
};
// T3: manual seals must also plant the TRACKED attempts anchor seal.ts creates.
const anchorPack = (root: string, id: string, digest: string) => {
  mkdirSync(join(root, "planning/holdouts/attempts"), { recursive: true });
  writeFileSync(join(root, "planning/holdouts/attempts", `${id}.log`),
    `sealed at=2026-01-01T00:00:00Z id=${id} pack_sha256=${digest} prev=GENESIS
`);
};

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

// T1 changed the sealed shape: the answer key on disk is expected.json.enc, and
// expectedResultsHash covers the CIPHERTEXT. The pack is encrypted here — after
// the plaintext-era hash tests above, before anything derives manifest hashes.
writeFileSync(join(packDir, "cases.yaml"), canonicalCasesText(readFileSync(join(packDir, "cases.yaml"), "utf8")));
const key99 = encryptPack("HLD-S99-v1", packDir);
const sealedPack99 = canonicalPackHash(packDir);
ok("a sealed pack lists the ciphertext, never the plaintext",
   sealedPack99.files.join(",") === "README.md,cases.yaml,expected.json.enc", sealedPack99.files.join(","));
const shasum = execFileSync("/bin/sh", ["-c", `shasum -a 256 "${join(packDir, ENC_NAME)}" | cut -d' ' -f1`], { encoding: "utf8" }).trim();
ok("expected_results_sha256 equals `shasum -a 256 expected.json.enc`", expectedResultsHash(packDir) === shasum, `${expectedResultsHash(packDir)} vs ${shasum}`);
ok("the ciphertext round-trips under its key",
   decryptExpected(readFileSync(join(packDir, ENC_NAME)), key99).toString().includes('"H002"'));

console.log("— manifest validation —");
const good = {
  artifact_type: "HoldoutManifest", id: "HLD-S99-v1", parent_story_id: "ST-99",
  dev_id: "S99-example", qa_id: "QA-S99", contract_version: "v1", created_at: "2026-09-22T00:00:00Z",
  custodian: "holdout-custodian-agent (not the implementation agent)", hash_method: HASH_METHOD,
  case_classes: ["nominal", "counterexample"], case_count: 2, covered_invariants: ["INV-1"],
  private_pack_sha256: sealedPack99.digest, expected_results_sha256: expectedResultsHash(packDir),
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
anchorPack(repoRoot, "HLD-S99-v1", sealedPack99.digest);
const TOOL = join(process.cwd(), "tools/holdout/reveal.ts");
// The fixture root is deliberately NOT a git repository, and reveal now REFUSES
// that state unless --allow-unverified-candidate is passed (security review F2).
// The helper passes the flag so every existing test exercises the override path;
// the F2 tests below call the tool directly to pin the refusal itself.
const run = (env: Record<string, string>, args: string[], cwd = repoRoot) => {
  // T1: the key rides stdin, exactly like the real flow. Unknown id -> empty
  // stdin, which only matters to tests that get past every earlier refusal.
  const id2 = args[args.indexOf("--id") + 1] ?? "";
  const key = packKeys.get(id2) ?? "";
  try {
    const out = execFileSync("bun", [TOOL, ...args, "--allow-unverified-candidate", "--key-stdin"],
      { cwd, encoding: "utf8", env: { ...process.env, ...env }, input: key + "\n", stdio: ["pipe", "pipe", "pipe"] });
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
  let r: { code: number; out: string };
  try { r = { code: 0, out: execFileSync("bun", [SEAL, ...args], { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }) }; }
  catch (e: any) { r = { code: e.status ?? 1, out: String(e.stdout ?? "") + String(e.stderr ?? "") }; }
  // T1: seal prints the answer key ONCE; the suite is the custodian and keeps it.
  // V3 moved the key print BEFORE the plaintext deletion (and so before the
  // final "sealed <id>" line) — the two are matched independently.
  const mId = /ANSWER KEY for (HLD-[A-Za-z0-9-]+)/.exec(r.out);
  const mKey = /WB_HOLDOUT_KEY=([0-9a-f]{64})/.exec(r.out);
  if (r.code === 0 && mId && mKey) packKeys.set(mId[1], mKey[1]);
  return r;
};

// manualSeal writes a manifest directly, BYPASSING seal.ts. seal now refuses
// ambiguous packs at authoring time (F9), but reveal's guards must hold even
// against a manifest a compliant seal would never have produced — a hand-written
// or older-tool manifest is exactly the adversarial input reveal exists to survive.
const manualSeal = (id2: string, dir2: string, caseCount = 1, opts?: { rawCases?: boolean }) => {
  const m = /^HLD-(S\d+)[A-Za-z0-9-]*-v(\d+)$/.exec(id2)!;
  // T1/T3: a hand-written manifest still describes the SEALED shape — encrypt
  // the answer key (registering the key) and plant the tracked anchor, exactly
  // as seal.ts would, THEN hash. The point of manualSeal is bypassing seal's
  // REFUSALS, not producing a pack shape reveal would never see.
  // W3: reveal requires canonical cases.yaml. manualSeal canonicalizes a
  // WELL-FORMED file just as seal.ts would — but leaves any file the scanner
  // flags untouched, because those packs exist to prove reveal refuses them.
  try {
    const ctRaw = readFileSync(join(dir2, "cases.yaml"));
    const ct = ctRaw.toString("utf8");
    // non-UTF-8 attack packs stay byte-exact: canonicalizing would LAUNDER them
    if (!(opts && opts.rawCases) && Buffer.from(ct, "utf8").equals(ctRaw) && caseKeyProblems(ct).length === 0) {
      writeFileSync(join(dir2, "cases.yaml"), canonicalCasesText(ct));
    }
  } catch { /* unparseable attack pack: leave as authored */ }
  if (existsSync(join(dir2, PLAIN_NAME))) encryptPack(id2, dir2);
  const packDigest = canonicalPackHash(dir2).digest;
  anchorPack(repoRoot, id2, packDigest);
  const g: Record<string, unknown> = { ...good, id: id2, parent_story_id: "ST-" + m[1].slice(1),
    dev_id: m[1] + "-x", qa_id: "QA-" + m[1], contract_version: "v" + m[2],
    case_classes: ["nominal"], case_count: caseCount, covered_invariants: ["INV-1"],
    private_pack_sha256: packDigest,
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
writeFileSync(join(rc, "key.txt"), packKeys.get(raceId)! + "\n");   // T1: each contender reads the key itself
const one = (cand: string, tag: string) =>
  "( WB_QA_CONTEXT=1 bun " + JSON.stringify(TOOL) + " --id " + raceId + " --candidate " + cand +
  " --allow-unverified-candidate --key-stdin < " + rc + "/key.txt > " + rc + "/" + tag + ".log 2>&1; echo $? > " + rc + "/" + tag + ".rc ) &";
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
// The reviewer's three-round-old gap, closed: post_run_tree_clean's live "true"
// branch. exit 0 above already implies it, but the field is the evidence — and
// it proves the T3/T4 filter: reveal's OWN writes (the anchor append; the
// bundle is gitignored in this fixture) do not condemn an honest run.
ok("GIT: an honest run in a real repository seals post_run_tree_clean: true",
   /post_run_tree_clean: true/.test(readFileSync(join(repo2, "planning/evidence/EVB-HLD-S90-v1/manifest.yaml"), "utf8")));

// ...and the live "false" branch: a case that dirties a TRACKED file is caught,
// recorded, and fails the exit code even though the case itself passed.
writeFileSync(join(repo2, "src.txt"), "original\n");
mkdirSync(join(repo2, "qa-private", "HLD-S90B-v1"), { recursive: true });
writeFileSync(join(repo2, "qa-private/HLD-S90B-v1/README.md"), "# dirty\n");
writeFileSync(join(repo2, "qa-private/HLD-S90B-v1/cases.yaml"),
  "cases:\n  - id: H1\n    class: hostile\n    run: \"echo tampered >> src.txt\"\n");
writeFileSync(join(repo2, "qa-private/HLD-S90B-v1/expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S90B", "--story", "ST-90", "--contract", "v1"], repo2);
git("add", "-A"); git("commit", "-q", "-m", "second pack");
const head2 = git("rev-parse", "HEAD").trim();
const dirtyRun = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S90B-v1", "--candidate", head2], repo2);
ok("GIT: a case that modifies a TRACKED file seals post_run_tree_clean: false and fails the exit",
   dirtyRun.code !== 0 && /TAMPERING RECORDED/.test(dirtyRun.out) &&
   /post_run_tree_clean: false/.test(readFileSync(join(repo2, "planning/evidence/EVB-HLD-S90B-v1/manifest.yaml"), "utf8")),
   dirtyRun.out.slice(-240));

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
// W3 made seal REWRITE cases.yaml — so seal must refuse bad bytes rather than
// launder them into clean UTF-8, and reveal's own refusal is reached via
// manualSeal, which keeps attack packs byte-exact.
const u8Seal = seal(["--slice", "S88", "--story", "ST-88", "--contract", "v1"]);
ok("seal refuses a cases.yaml that is not valid UTF-8 — the rewrite must never launder bytes",
   u8Seal.code !== 0 && /not valid UTF-8/.test(u8Seal.out), u8Seal.out.slice(-200));
manualSeal(u8Id, u8Dir);
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
  "cases:\n  - id: H1\n    class: hostile\n    run: \"cat qa-private/" + f1Id + "/" + ENC_NAME + "\"\n");
writeFileSync(join(f1Dir, "expected.json"), JSON.stringify({ H1: { exit: 1 } }) + "\n");
seal(["--slice", "S57", "--story", "ST-57", "--contract", "v1"]);
const f1run = run({ WB_QA_CONTEXT: "1" }, ["--id", f1Id, "--candidate", "abc1230"]);
ok("F1: a case that reads its own pack's answer key mid-run finds NOTHING",
   f1run.code === 0 && /1 PASS \/ 0 FAIL/.test(f1run.out), f1run.out.slice(-240));
ok("F1: the pack is restored after the run, byte-identical",
   existsSync(join(f1Dir, ENC_NAME)) &&
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
// Back to the AUTHORING shape: seal consumes plaintext, and the manualSeal above
// left a manifest + anchor that would trip the write-once refusal before the
// flow-style scan this test exists to reach.
writeFileSync(join(f9Dir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
rmSync(join(f9Dir, ENC_NAME), { force: true });
rmSync(join(repoRoot, "planning/holdouts/manifests", "HLD-S53-v1.yaml"), { force: true });
rmSync(join(repoRoot, "planning/holdouts/attempts", "HLD-S53-v1.log"), { force: true });
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
const s3KeyFile = join(tmp, "s3key.txt");
writeFileSync(s3KeyFile, packKeys.get(s3Id)! + "\n");
execFileSync("/bin/sh", ["-c",
  `WB_QA_CONTEXT=1 bun ${JSON.stringify(TOOL)} --id ${s3Id} --candidate abc1230 --allow-unverified-candidate --key-stdin < ${JSON.stringify(s3KeyFile)} > /dev/null 2>&1 & pid=$!; sleep 1.2; kill -TERM $pid 2>/dev/null; wait $pid 2>/dev/null; exit 0`,
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
   // attempt: 2, not 1 — the s4 block above rm -rf'd the whole bundle, and the
   // TRACKED anchor still remembers the SIGTERM attempt (T3: rm resets nothing).
   /candidate_verified: false/.test(s2Log) && /attempt: 2/.test(s2Log) &&
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
const s2LogOriginal = readFileSync(s2LogPath, "utf8");
writeFileSync(s2LogPath, s2LogOriginal.replace("post_run_pack_intact: true", "post_run_pack_intact: banana"));
const vrr3 = vrr(repoRoot);
ok("S2: an edited raw log is CAUGHT by its own hash", vrr3.code !== 0 && /raw_log_sha256 mismatch/.test(vrr3.out), vrr3.out.slice(-300));
writeFileSync(s2LogPath, s2LogOriginal);   // restore: later verifier passes must see honest records

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
linkSync(join(hlDir, ENC_NAME), hlLink);   // the attacker's pre-made second name
const hlRun = run({ WB_QA_CONTEXT: "1" }, ["--id", hlId, "--candidate", "abc1230"]);
ok("HARDLINK: a pre-made hardlink to the answer key reads NOTHING during the run",
   hlRun.code === 0 && /1 PASS \/ 0 FAIL/.test(hlRun.out), hlRun.out.slice(-240));
rmSync(hlLink, { force: true });

console.log("— third security review: T1/T2/T3/T4, each executed defeat pinned —");

// A direct-key runner for the refusal tests: exact control of what stdin carries.
const runKey = (id2: string, keyLine: string | null, cwd = repoRoot) => {
  const args = [TOOL, "--id", id2, "--candidate", "abc1230", "--allow-unverified-candidate"];
  if (keyLine !== null) args.push("--key-stdin");
  try {
    const out = execFileSync("bun", args, { cwd, encoding: "utf8",
      env: { ...process.env, WB_QA_CONTEXT: "1" },
      ...(keyLine !== null ? { input: keyLine + "\n", stdio: ["pipe", "pipe", "pipe"] as const }
                           : { stdio: ["ignore", "pipe", "pipe"] as const }) });
    return { code: 0, out };
  } catch (e: any) { return { code: e.status ?? 1, out: String(e.stdout ?? "") + String(e.stderr ?? "") }; }
};

// T1 — the reviewer's pre-opened-descriptor daemon, re-run against the sealed
// shape. POSIX checks permission at open(2), not read(2): the fd DOES read
// straight through mode 000, the tripwire records nothing — and it no longer
// matters, because what it reads is ciphertext.
const t1Id = "HLD-S40-v1";
const t1Dir = join(repoRoot, "qa-private", t1Id);
mkdirSync(t1Dir, { recursive: true });
const t1Flag = join(tmp, "t1-flag"), t1Dump = join(tmp, "t1-dump.bin"), t1Ready = join(tmp, "t1-ready");
writeFileSync(join(t1Dir, "README.md"), "# t1\n");
writeFileSync(join(t1Dir, "cases.yaml"),
  "cases:\n  - id: H1\n    class: hostile\n    run: \"touch " + t1Flag + "; sleep 0.6\"\n");
writeFileSync(join(t1Dir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S40", "--story", "ST-40", "--contract", "v1"]);
ok("T1: after sealing, NO plaintext answer key exists on disk",
   !existsSync(join(t1Dir, PLAIN_NAME)) && existsSync(join(t1Dir, ENC_NAME)));
const t1Cipher = readFileSync(join(t1Dir, ENC_NAME));
// The daemon: open the key file BEFORE the reveal, signal readiness, then dump
// THROUGH the held descriptor while the case (which raised the flag) still runs
// and the file sits at mode 000.
execFileSync("/bin/sh", ["-c",
  `( exec 3< ${JSON.stringify(join(t1Dir, ENC_NAME))}; : > ${JSON.stringify(t1Ready)}; ` +
  `while [ ! -e ${JSON.stringify(t1Flag)} ]; do sleep 0.05; done; cat <&3 > ${JSON.stringify(t1Dump)} ) &`], { cwd: repoRoot });
execFileSync("/bin/sh", ["-c", `for i in $(seq 40); do [ -e ${JSON.stringify(t1Ready)} ] && exit 0; sleep 0.05; done; exit 1`]);
const t1Run = run({ WB_QA_CONTEXT: "1" }, ["--id", t1Id, "--candidate", "abc1230"]);
execFileSync("/bin/sh", ["-c", `for i in $(seq 20); do [ -s ${JSON.stringify(t1Dump)} ] && exit 0; sleep 0.1; done; exit 0`]);
const t1Got = existsSync(t1Dump) ? readFileSync(t1Dump) : Buffer.alloc(0);
ok("T1: the pre-opened fd reads THROUGH mode 000 — and harvests ONLY ciphertext",
   t1Got.length > 0 && t1Got.equals(t1Cipher) && !t1Got.includes(Buffer.from('"exit"')),
   `dumped ${t1Got.length} byte(s)`);
ok("T1: the run it spied on is unforged, and the tripwire honestly saw nothing (fd reads move no ctime)",
   t1Run.code === 0 && /1 PASS \/ 0 FAIL/.test(t1Run.out) &&
   /post_run_pack_untouched: true/.test(readFileSync(join(repoRoot, "planning/evidence", "EVB-" + t1Id, "manifest.yaml"), "utf8")),
   t1Run.out.slice(-200));

// T1, the key-handling refusals — all on an UNSPENT pack, none spend it.
const t1xId = "HLD-S39-v1";
const t1xDir = join(repoRoot, "qa-private", t1xId);
mkdirSync(t1xDir, { recursive: true });
writeFileSync(join(t1xDir, "README.md"), "# t1x\n");
writeFileSync(join(t1xDir, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"echo ok\"\n");
writeFileSync(join(t1xDir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S39", "--story", "ST-39", "--contract", "v1"]);
const t1NoFlag = runKey(t1xId, null);
ok("T1: without --key-stdin the reveal refuses, naming the stdin channel",
   t1NoFlag.code !== 0 && /--key-stdin/.test(t1NoFlag.out), t1NoFlag.out.slice(-200));
const t1Wrong = runKey(t1xId, "f".repeat(64));
ok("T1: a WRONG key refuses — GCM authenticates every byte, nothing decrypts to garbage",
   t1Wrong.code !== 0 && /did not decrypt/.test(t1Wrong.out), t1Wrong.out.slice(-200));
writeFileSync(join(t1xDir, PLAIN_NAME), JSON.stringify({ H1: { exit: 0 } }) + "\n");
const t1Plain = runKey(t1xId, packKeys.get(t1xId)!);
ok("T1: PLAINTEXT alongside the ciphertext is refused outright — no downgrade path",
   t1Plain.code !== 0 && /is PLAINTEXT/.test(t1Plain.out), t1Plain.out.slice(-200));
rmSync(join(t1xDir, PLAIN_NAME), { force: true });
ok("T1: none of those refusals spent the pack",
   /revealed_at: null/.test(readFileSync(join(repoRoot, "planning/holdouts/manifests", t1xId + ".yaml"), "utf8")));

// T2 — the reviewer's log-injection run string: a double-quoted YAML scalar
// with \n escapes, invisible to the block-scalar refusals. Refused at BOTH
// tools now, and the pack survives the reveal-side refusal.
const t2Id = "HLD-S37-v1";
const t2Dir = join(repoRoot, "qa-private", t2Id);
mkdirSync(t2Dir, { recursive: true });
writeFileSync(join(t2Dir, "README.md"), "# t2\n");
writeFileSync(join(t2Dir, "cases.yaml"),
  'cases:\n  - id: H1\n    class: hostile\n    run: "echo hi\\npost_run_pack_untouched: true\\nresult: 1 PASS / 0 FAIL of 1"\n');
writeFileSync(join(t2Dir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
const t2Seal = seal(["--slice", "S37", "--story", "ST-37", "--contract", "v1"]);
ok("T2: seal refuses a multi-line run string — the injection vector dies at authoring",
   t2Seal.code !== 0 && /must be single-line/.test(t2Seal.out), t2Seal.out.slice(-200));
manualSeal(t2Id, t2Dir);
const t2Rev = run({ WB_QA_CONTEXT: "1" }, ["--id", t2Id, "--candidate", "abc1230"]);
ok("T2: reveal refuses the same pack sealed around the tool, pack NOT spent",
   t2Rev.code !== 0 && /must be single-line/.test(t2Rev.out) &&
   /revealed_at: null/.test(readFileSync(join(repoRoot, "planning/holdouts/manifests", t2Id + ".yaml"), "utf8")),
   t2Rev.out.slice(-200));

// T2 — a case whose run string CONTAINS the footer delimiter text, single-line.
// It lands in the cases region as `run: "..."`; the LAST-line-match boundary
// never moves, the record verifies clean.
const t2cId = "HLD-S36-v1";
const t2cDir = join(repoRoot, "qa-private", t2cId);
mkdirSync(t2cDir, { recursive: true });
writeFileSync(join(t2cDir, "README.md"), "# t2c\n");
writeFileSync(join(t2cDir, "cases.yaml"),
  'cases:\n  - id: H1\n    class: hostile\n    run: "true # === wb-run-record footer v2: authoritative fields run from the LAST occurrence of this line to end-of-file ==="\n');
writeFileSync(join(t2cDir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S36", "--story", "ST-36", "--contract", "v1"]);
const t2cRun = run({ WB_QA_CONTEXT: "1" }, ["--id", t2cId, "--candidate", "abc1230"]);
ok("T2: a run string carrying the delimiter TEXT cannot move the trusted boundary",
   t2cRun.code === 0 && /1 PASS \/ 0 FAIL/.test(t2cRun.out), t2cRun.out.slice(-200));

// T2 — the verifier itself, attacked the reviewer's way: a bundle whose log
// carries an injected `post_run_pack_untouched: true` line in the CASES region,
// a real `false` in the footer, and a manifest sed-flipped to `true`. The old
// first-match scan blessed exactly this; region parsing must refuse it.
const fgId = "HLD-S38-v1";
const fgBundle = join(repoRoot, "planning/evidence", "EVB-" + fgId);
mkdirSync(fgBundle, { recursive: true });
const fgGenesis = `sealed at=2026-01-01T00:00:00Z id=${fgId} pack_sha256=${"0".repeat(64)} prev=GENESIS`;
const fgAttempt = `attempt=1 at=2026-01-01T00:00:01Z pid=1 candidate=abc1230 prev=${sha256Hex(fgGenesis)}`;
const fgChain = fgGenesis + "\n" + fgAttempt + "\n";   // the chain as sealed INSIDE the log (pre-marker)
mkdirSync(join(repoRoot, "planning/holdouts/attempts"), { recursive: true });
// full on-disk chain = sealed chain + the W2 spent marker naming this log's hash
let fgChainFull = "";   // finished below, once fgLog's hash exists
const FOOTER = "=== wb-run-record footer v2: authoritative fields run from the LAST occurrence of this line to end-of-file ===";
const CASESD = "=== cases: candidate-controlled region — no field below this line is trusted until the footer delimiter ===";
const fgLog = [
  `# Holdout run record — ${fgId}`, `candidate: abc1230`, `candidate_verified: false`,
  `attempt: 1`, `started_at: 2026-01-01T00:00:02Z`, `hash_method: wb-canon-2`,
  `pack_sha256: ${"0".repeat(64)}`, `expected_results_sha256: ${"1".repeat(64)}`, "",
  CASESD, "",
  `## H1 [hostile] PASS`, `post_run_pack_untouched: true`, `exit: 0`, "",
  FOOTER,
  `post_run_pack_intact: true`, `post_run_tree_clean: unverified`,
  `post_run_tree_clean_semantics: test-semantics`, `head_unchanged_during_run: unverified`,
  `manifest_rewritten_during_run: false`, `post_run_pack_untouched: false`,
  `post_run_attempts_intact: true`, `attempts_anchor_committed: false`, `post_run_bundle_clean: true`,
  `config_planted_during_run: false`, `git_config_command_keys: []`,
  `attempts_log_sha256: ${sha256Hex(fgChain)}`,
  `finished_at: 2026-01-01T00:00:03Z`, `result: 1 PASS / 0 FAIL of 1`,
].join("\n") + "\n";
fgChainFull = fgChain + `revealed at=2026-01-01T00:00:03Z raw_log_sha256=${sha256Hex(fgLog)} prev=${sha256Hex(fgAttempt)}` + "\n";
mkdirSync(join(repoRoot, "planning/holdouts/attempts"), { recursive: true });
writeFileSync(join(repoRoot, "planning/holdouts/attempts", fgId + ".log"), fgChainFull);
writeFileSync(join(fgBundle, "attempts.log"), fgChainFull);
writeFileSync(join(fgBundle, "holdout-run-forged.log"), fgLog);
const fgManifest = (untouched: string) => [
  `artifact_type: HoldoutRunRecord`, `id: EVB-${fgId}`, `holdout_id: ${fgId}`,
  `candidate: abc1230`, `candidate_verified: false`, `attempt: 1`,
  `case_count: 1`, `pass: 1`, `fail: 0`, `raw_log: holdout-run-forged.log`,
  `raw_log_sha256: "${sha256Hex(fgLog)}"`,
  `post_run_pack_intact: true`, `post_run_tree_clean: unverified`,
  `post_run_tree_clean_semantics: test-semantics`, `head_unchanged_during_run: unverified`,
  `manifest_rewritten_during_run: false`, `post_run_pack_untouched: ${untouched}`,
  `post_run_attempts_intact: true`, `attempts_anchor_committed: false`, `post_run_bundle_clean: true`,
  `config_planted_during_run: false`, `git_config_command_keys: []`,
  `attempts_log_sha256: "${sha256Hex(fgChain)}"`, "",
].join("\n");
writeFileSync(join(fgBundle, "manifest.yaml"), fgManifest("true"));   // the sed lie
const VRR = join(process.cwd(), "tools/holdout/verify-run-records.ts");
const vrrRun = (cwd: string) => {
  try { return { code: 0, out: execFileSync("bun", [VRR], { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }) }; }
  catch (e: any) { return { code: e.status ?? 1, out: String(e.stdout ?? "") + String(e.stderr ?? "") }; }
};
const fgV1 = vrrRun(repoRoot);
ok("T2: the verifier reads the FOOTER, not the injected line — the sed flip is caught",
   fgV1.code !== 0 && /post_run_pack_untouched DISAGREES/.test(fgV1.out), fgV1.out.slice(-300));
// A fully CONSISTENT forged bundle passes: this tool proves consistency and
// post-seal integrity, not provenance. Whole-cloth fabrication remains the
// stated same-user limit (reviewer round 3, item withheld by design).
writeFileSync(join(fgBundle, "manifest.yaml"), fgManifest("false"));
const fgV2 = vrrRun(repoRoot);
ok("T2: with the lie corrected, every bundle verifies again", fgV2.code === 0, fgV2.out.slice(-300));

// T3 — the tracked anchor. Deleting it refuses; resetting it to genesis while
// the bundle copy remembers refuses. (The rm -rf amnesia itself is already
// pinned above: the S2 record now says `attempt: 2` BECAUSE the anchor
// survived the s4 block's whole-bundle rm.)
const t3Id = "HLD-S35-v1";
const t3Dir = join(repoRoot, "qa-private", t3Id);
mkdirSync(t3Dir, { recursive: true });
writeFileSync(join(t3Dir, "README.md"), "# t3\n");
writeFileSync(join(t3Dir, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"sleep 2\"\n");
writeFileSync(join(t3Dir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S35", "--story", "ST-35", "--contract", "v1"]);
const t3Anchor = join(repoRoot, "planning/holdouts/attempts", t3Id + ".log");
const t3AnchorGenesis = readFileSync(t3Anchor, "utf8");
rmSync(t3Anchor);
const t3NoAnchor = run({ WB_QA_CONTEXT: "1" }, ["--id", t3Id, "--candidate", "abc1230"]);
ok("T3: a deleted attempts anchor refuses — its absence is the removal of a TRACKED file",
   t3NoAnchor.code !== 0 && /no attempts anchor/.test(t3NoAnchor.out), t3NoAnchor.out.slice(-200));
writeFileSync(t3Anchor, t3AnchorGenesis);
// One aborted attempt (per-case timeout), so both copies carry attempt=1...
const t3Abort = run({ WB_QA_CONTEXT: "1", WB_HOLDOUT_CASE_TIMEOUT_MS: "200" }, ["--id", t3Id, "--candidate", "abc1230"]);
ok("T3: the timeout abort landed attempt=1 on BOTH copies of the chain",
   t3Abort.code !== 0 && /attempt=1 /.test(readFileSync(t3Anchor, "utf8")) &&
   /attempt=1 /.test(readFileSync(join(repoRoot, "planning/evidence", "EVB-" + t3Id, "attempts.log"), "utf8")),
   t3Abort.out.slice(-160));
// ...then the insider "git checkout"s the anchor back to its committed genesis.
writeFileSync(t3Anchor, t3AnchorGenesis);
rmSync(join(repoRoot, "planning/evidence", "EVB-" + t3Id, ".reveal.lock"), { force: true });
const t3Reset = run({ WB_QA_CONTEXT: "1" }, ["--id", t3Id, "--candidate", "abc1230"]);
ok("T3: an anchor reset to genesis DISAGREES with the bundle copy and refuses",
   t3Reset.code !== 0 && /disagree/.test(t3Reset.out), t3Reset.out.slice(-240));

// T3/T4 on the verifier: a sealed record whose anchor disappears afterwards.
const t2cBundle = join(repoRoot, "planning/evidence", "EVB-" + t2cId);
const t2cAnchor = join(repoRoot, "planning/holdouts/attempts", t2cId + ".log");
const t2cAnchorText = readFileSync(t2cAnchor, "utf8");
rmSync(t2cAnchor);
const t3V1 = vrrRun(repoRoot);
ok("T3: verify-run-records catches a MISSING tracked anchor behind a sealed record",
   t3V1.code !== 0 && /attempts anchor .* is MISSING/.test(t3V1.out), t3V1.out.slice(-300));
writeFileSync(t2cAnchor, t2cAnchorText);
// T4: the semantics caveat is IN the record, in both halves, and cross-checked.
const t2cMan = join(t2cBundle, "manifest.yaml");
ok("T4: the record itself states what post_run_tree_clean cannot see",
   /post_run_tree_clean_semantics: end-of-run snapshot; blind to a modify-then-restore/.test(readFileSync(t2cMan, "utf8")));
writeFileSync(t2cMan, readFileSync(t2cMan, "utf8").replace("blind to a modify-then-restore", "sees a modify-then-restore"));
const t4V = vrrRun(repoRoot);
ok("T4: editing the manifest's semantics line DISAGREES with the hashed log",
   t4V.code !== 0 && /post_run_tree_clean_semantics DISAGREES/.test(t4V.out), t4V.out.slice(-300));
writeFileSync(t2cMan, readFileSync(t2cMan, "utf8").replace("sees a modify-then-restore", "blind to a modify-then-restore"));
const t4V2 = vrrRun(repoRoot);
ok("T4: restored, every record verifies again", t4V2.code === 0, t4V2.out.slice(-200));

console.log("— fourth security review: U1/U2/U3, each executed defeat pinned —");

// U1 — the reviewer's anchor truncation, sealing-run variant: a case shortens
// BOTH copies of the chain to their genesis line mid-run. The blanket path
// exclusion used to hide this from the tree check; the content check seals it.
const u1Id = "HLD-S34-v1";
const u1Dir = join(repoRoot, "qa-private", u1Id);
mkdirSync(u1Dir, { recursive: true });
const u1Anchor = "planning/holdouts/attempts/" + u1Id + ".log";
const u1Copy = "planning/evidence/EVB-" + u1Id + "/attempts.log";
const truncBoth = "head -n1 " + u1Anchor + " > .u1t && mv .u1t " + u1Anchor + "; head -n1 " + u1Copy + " > .u1u && mv .u1u " + u1Copy;
writeFileSync(join(u1Dir, "README.md"), "# u1\n");
writeFileSync(join(u1Dir, "cases.yaml"),
  "cases:\n  - id: H1\n    class: hostile\n    run: \"" + truncBoth + "; true\"\n");
writeFileSync(join(u1Dir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S34", "--story", "ST-34", "--contract", "v1"]);
const u1Run = run({ WB_QA_CONTEXT: "1" }, ["--id", u1Id, "--candidate", "abc1230"]);
const u1Rec = readFileSync(join(repoRoot, "planning/evidence", "EVB-" + u1Id, "manifest.yaml"), "utf8");
ok("U1: a case that truncates BOTH chain copies mid-run is sealed as tampering",
   u1Run.code !== 0 && /TAMPERING RECORDED/.test(u1Run.out) &&
   /post_run_attempts_intact: false/.test(u1Rec), u1Run.out.slice(-240));
ok("U1: the found bytes are preserved and the true chain is restored from memory",
   existsSync(join(repoRoot, "planning/evidence", "EVB-" + u1Id, "attempts-anchor-as-found-after-run.log")) &&
   /attempt=1 /.test(readFileSync(join(repoRoot, u1Anchor), "utf8")));

// U1 — the reviewer's EXECUTED variant: truncation during an ABORTED run,
// where no post-run check ever fires. The exit handler heals it, so the next
// reveal counts attempt 2, not the forged 1.
const u1bId = "HLD-S33-v1";
const u1bDir = join(repoRoot, "qa-private", u1bId);
mkdirSync(u1bDir, { recursive: true });
const u1bAnchor = "planning/holdouts/attempts/" + u1bId + ".log";
const u1bCopy = "planning/evidence/EVB-" + u1bId + "/attempts.log";
const truncB = "head -n1 " + u1bAnchor + " > .u1v && mv .u1v " + u1bAnchor + "; head -n1 " + u1bCopy + " > .u1w && mv .u1w " + u1bCopy;
writeFileSync(join(u1bDir, "README.md"), "# u1b\n");
writeFileSync(join(u1bDir, "cases.yaml"),
  "cases:\n  - id: H1\n    class: hostile\n    run: \"" + truncB + "; sleep 2\"\n");
writeFileSync(join(u1bDir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S33", "--story", "ST-33", "--contract", "v1"]);
const u1bAbort = run({ WB_QA_CONTEXT: "1", WB_HOLDOUT_CASE_TIMEOUT_MS: "300" }, ["--id", u1bId, "--candidate", "abc1230"]);
const u1bAnchorNow = readFileSync(join(repoRoot, u1bAnchor), "utf8");
ok("U1: truncation during an ABORTED run is healed by the exit handler — attempt 1 survives",
   u1bAbort.code !== 0 && /attempt=1 /.test(u1bAnchorNow) && u1bAnchorNow.split("\n").filter(Boolean).length === 2,
   `anchor lines=${u1bAnchorNow.split("\n").filter(Boolean).length}`);
rmSync(join(repoRoot, "planning/evidence", "EVB-" + u1bId, ".reveal.lock"), { force: true });
const u1bSecond = run({ WB_QA_CONTEXT: "1" }, ["--id", u1bId, "--candidate", "abc1230"]);
const u1bRec = readFileSync(join(repoRoot, "planning/evidence", "EVB-" + u1bId, "manifest.yaml"), "utf8");
// The sealing run exits 1 too: the hostile case truncates again and is caught
// live this time. Both halves of the reviewer's attack now fail separately —
// the aborted-run theft of history (healed) and the count itself (attempt: 2).
ok("U1: the sealing run records attempt: 2 — the reviewer's forged '1' is dead",
   u1bSecond.code !== 0 && /attempt: 2/.test(u1bRec) && /post_run_attempts_intact: false/.test(u1bRec),
   u1bRec.slice(0, 300));

// U2 — a case plants a decoy run log inside its own bundle.
const u2Id = "HLD-S32-v1";
const u2Dir = join(repoRoot, "qa-private", u2Id);
mkdirSync(u2Dir, { recursive: true });
writeFileSync(join(u2Dir, "README.md"), "# u2\n");
writeFileSync(join(u2Dir, "cases.yaml"),
  "cases:\n  - id: H1\n    class: hostile\n    run: \"echo decoy > planning/evidence/EVB-" + u2Id + "/holdout-run-00000000T000000000Z.log\"\n");
writeFileSync(join(u2Dir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S32", "--story", "ST-32", "--contract", "v1"]);
const u2Run = run({ WB_QA_CONTEXT: "1" }, ["--id", u2Id, "--candidate", "abc1230"]);
const u2Rec = readFileSync(join(repoRoot, "planning/evidence", "EVB-" + u2Id, "manifest.yaml"), "utf8");
ok("U2: a planted file in the bundle is sealed as tampering, named in the hashed log",
   u2Run.code !== 0 && /post_run_bundle_clean: false/.test(u2Rec) &&
   /holdout-run-00000000T000000000Z\.log/.test(readFileSync(join(repoRoot, "planning/evidence", "EVB-" + u2Id,
     readdirSync(join(repoRoot, "planning/evidence", "EVB-" + u2Id)).filter((f) => f.startsWith("holdout-run-2"))[0]), "utf8")),
   u2Run.out.slice(-240));
const u2V1 = vrrRun(repoRoot);
ok("U2: the verifier refuses a sealed bundle holding two run logs",
   u2V1.code !== 0 && /exactly ONE run/.test(u2V1.out), u2V1.out.slice(-300));
rmSync(join(repoRoot, "planning/evidence", "EVB-" + u2Id, "holdout-run-00000000T000000000Z.log"), { force: true });
const u2V2 = vrrRun(repoRoot);
ok("U2: with the decoy removed every record verifies again (the sealed 'false' stays consistent)",
   u2V2.code === 0, u2V2.out.slice(-300));

// U3 — cases run with a MINIMAL environment. The reviewer's ps -E probe read a
// live API key out of reveal's inherited env; a canary now proves nothing but
// PATH/HOME/TMPDIR crosses the boundary.
const u3Id = "HLD-S31-v1";
const u3Dir = join(repoRoot, "qa-private", u3Id);
mkdirSync(u3Dir, { recursive: true });
writeFileSync(join(u3Dir, "README.md"), "# u3\n");
writeFileSync(join(u3Dir, "cases.yaml"),
  'cases:\n  - id: H1\n    class: hostile\n    run: "test -z \\"$WB_CANARY_SECRET\\" && test -n \\"$HOME\\""\n');
writeFileSync(join(u3Dir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S31", "--story", "ST-31", "--contract", "v1"]);
const u3Run = run({ WB_QA_CONTEXT: "1", WB_CANARY_SECRET: "leak-me" }, ["--id", u3Id, "--candidate", "abc1230"]);
ok("U3: a secret in reveal's environment is INVISIBLE to the case; HOME still present",
   u3Run.code === 0 && /1 PASS \/ 0 FAIL/.test(u3Run.out), u3Run.out.slice(-200));

console.log("— fifth security review: V1/V2, each executed defeat pinned —");

// V2 — a QUOTED key spelling is the same key. `run:` plus `"run":` sealed and
// executed the second command while a reader saw the first (executed, fifth
// pass). One regex character class closes it, both tools, same scanner.
const v2Id = "HLD-S30-v1";
const v2Dir = join(repoRoot, "qa-private", v2Id);
mkdirSync(v2Dir, { recursive: true });
writeFileSync(join(v2Dir, "README.md"), "# v2\n");
writeFileSync(join(v2Dir, "cases.yaml"),
  'cases:\n  - id: H1\n    class: nominal\n    run: "echo SAFE"\n    "run": "echo PWNED"\n');
writeFileSync(join(v2Dir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
const v2Seal = seal(["--slice", "S30", "--story", "ST-30", "--contract", "v1"]);
ok("V2: seal refuses a double-quoted duplicate of run:",
   v2Seal.code !== 0 && /"run:" 2 times/.test(v2Seal.out), v2Seal.out.slice(-200));
manualSeal(v2Id, v2Dir);
const v2Rev = run({ WB_QA_CONTEXT: "1" }, ["--id", v2Id, "--candidate", "abc1230"]);
ok("V2: reveal refuses the same pack sealed around the tool, pack NOT spent",
   v2Rev.code !== 0 && /"run:" 2 times/.test(v2Rev.out) &&
   /revealed_at: null/.test(readFileSync(join(repoRoot, "planning/holdouts/manifests", v2Id + ".yaml"), "utf8")),
   v2Rev.out.slice(-200));
// ...and a SINGLE quoted spelling used once is not a false refusal.
const v2b = join(repoRoot, "qa-private", "HLD-S29-v1");
mkdirSync(v2b, { recursive: true });
writeFileSync(join(v2b, "README.md"), "# v2b\n");
writeFileSync(join(v2b, "cases.yaml"), 'cases:\n  - id: H1\n    class: nominal\n    \'run\': "echo ok"\n');
writeFileSync(join(v2b, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
const v2bSeal = seal(["--slice", "S29", "--story", "ST-29", "--contract", "v1"]);
ok("V2: one quoted key, used once, still seals — no false refusal", v2bSeal.code === 0, v2bSeal.out.slice(-160));

// V1 — the SIGKILL burn. A case truncates BOTH chain copies to the committed
// genesis and kill -9's reveal: the exit handler never runs (a signal is not
// an exit) and git status is EMPTY, because the forged state IS the committed
// state. The counter that survives: reveal COMMITS each attempt line before
// any case runs, and a kill cannot un-commit.
const v1Id = "HLD-S90C-v1";
const v1Pack = join(repo2, "qa-private", v1Id);
const v1AnchorRel = "planning/holdouts/attempts/" + v1Id + ".log";
const v1CopyRel = "planning/evidence/EVB-" + v1Id + "/attempts.log";
// Arm flag and key file live OUTSIDE repo2 — an untracked file inside it
// would (correctly) fail reveal's dirty-tree check before the burn even runs.
const v1Arm = join(tmp, "v1-burnarm");
const v1Key = join(tmp, "v1-key");
mkdirSync(v1Pack, { recursive: true });
writeFileSync(join(v1Pack, "README.md"), "# v1\n");
writeFileSync(join(v1Pack, "cases.yaml"),
  "cases:\n  - id: H1\n    class: hostile\n    run: \"if [ -f " + v1Arm + " ]; then head -n1 " + v1AnchorRel + " > " + join(tmp, "b1") + " && mv " + join(tmp, "b1") + " " + v1AnchorRel + "; head -n1 " + v1CopyRel + " > " + join(tmp, "b2") + " && mv " + join(tmp, "b2") + " " + v1CopyRel + "; kill -9 $PPID; fi; true\"\n");
writeFileSync(join(v1Pack, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S90C", "--story", "ST-90", "--contract", "v1"], repo2);
git("add", "-A"); git("commit", "-q", "-m", "v1 pack");
writeFileSync(v1Key, packKeys.get(v1Id)! + "\n");
writeFileSync(v1Arm, "armed\n");
execFileSync("/bin/sh", ["-c",
  `WB_QA_CONTEXT=1 bun ${JSON.stringify(TOOL)} --id ${v1Id} --candidate ${git("rev-parse", "HEAD").trim()} --key-stdin < ${JSON.stringify(v1Key)} > /dev/null 2>&1; exit 0`,
], { cwd: repo2 });
rmSync(v1Arm, { force: true });
const v1DiskLines = readFileSync(join(repo2, v1AnchorRel), "utf8").split("\n").filter(Boolean).length;
const v1HeadLines = git("show", "HEAD:./" + v1AnchorRel).split("\n").filter(Boolean).length;
ok("V1: the attempt line was COMMITTED before cases ran — SIGKILL could not rewind it",
   v1DiskLines === 1 && v1HeadLines === 2, `disk=${v1DiskLines} HEAD=${v1HeadLines}`);
// The documented crash recovery (chmod + remove the stale lock)...
execFileSync("/bin/sh", ["-c", `chmod u+rwX qa-private/${v1Id} && chmod -R u+rwX qa-private/${v1Id}`], { cwd: repo2 });
rmSync(join(repo2, "planning/evidence", "EVB-" + v1Id, ".reveal.lock"), { force: true });
// ...and the next reveal REFUSES: the working tree chain is shorter than HEAD's.
const v1Second = run({ WB_QA_CONTEXT: "1" }, ["--id", v1Id, "--candidate", git("rev-parse", "HEAD").trim()], repo2);
ok("V1: after recovery, the truncated anchor is refused against its committed copy",
   v1Second.code !== 0 && /SHORTER than/.test(v1Second.out) &&
   /revealed_at: null/.test(readFileSync(join(repo2, "planning/holdouts/manifests", v1Id + ".yaml"), "utf8")),
   v1Second.out.slice(-260));
// Repair exactly as the refusal instructs, disarm the burn, and the seal is honest.
git("checkout", "--", v1AnchorRel);
execFileSync("cp", [join(repo2, v1AnchorRel), join(repo2, v1CopyRel)]);
const v1Third = run({ WB_QA_CONTEXT: "1" }, ["--id", v1Id, "--candidate", git("rev-parse", "HEAD").trim()], repo2);
const v1Rec = readFileSync(join(repo2, "planning/evidence", "EVB-" + v1Id, "manifest.yaml"), "utf8");
ok("V1: the repaired chain seals attempt: 2, anchor committed, exit 0",
   v1Third.code === 0 && /attempt: 2/.test(v1Rec) && /attempts_anchor_committed: true/.test(v1Rec),
   v1Rec.slice(0, 340) + " ||" + v1Third.out.slice(-160));

console.log("— sixth security review: W1/W2/W3/W4, each executed defeat pinned —");

// W3 — the reviewer's ONE-LINE flow pack: `cases: [{... run: a, run: b}]`
// bypassed every dash-anchored regex and executed the hidden second command.
const w3Id = "HLD-S27-v1";
const w3Dir = join(repoRoot, "qa-private", w3Id);
mkdirSync(w3Dir, { recursive: true });
writeFileSync(join(w3Dir, "README.md"), "# w3\n");
writeFileSync(join(w3Dir, "cases.yaml"), "cases: [{id: H001, class: nominal, run: echo SAFE, run: echo PWNED}]\n");
writeFileSync(join(w3Dir, "expected.json"), JSON.stringify({ H001: { exit: 0 } }) + "\n");
const w3Seal = seal(["--slice", "S27", "--story", "ST-27", "--contract", "v1"]);
ok("W3: a one-line flow mapping is refused at seal — structure, not a dash spelling",
   w3Seal.code !== 0 && /flow-style collections/.test(w3Seal.out), w3Seal.out.slice(-200));
manualSeal(w3Id, w3Dir, 1, { rawCases: true });
const w3Rev = run({ WB_QA_CONTEXT: "1" }, ["--id", w3Id, "--candidate", "abc1230"]);
ok("W3: reveal refuses the same pack sealed around the tool — the file must BE its own parse",
   w3Rev.code !== 0 && /flow-style collections|canonical form/.test(w3Rev.out), w3Rev.out.slice(-220));
// ...and braces INSIDE a quoted run string are still fine — no false refusal.
const w3b = join(repoRoot, "qa-private", "HLD-S26-v1");
mkdirSync(w3b, { recursive: true });
writeFileSync(join(w3b, "README.md"), "# w3b\n");
writeFileSync(join(w3b, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"echo '{ok}'\"\n");
writeFileSync(join(w3b, "expected.json"), JSON.stringify({ H1: { exit: 0, stdout_contains: "{ok}" } }) + "\n");
seal(["--slice", "S26", "--story", "ST-26", "--contract", "v1"]);
const w3bRun = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S26-v1", "--candidate", "abc1230"]);
ok("W3: braces inside a quoted run string seal and reveal cleanly",
   w3bRun.code === 0 && /1 PASS \/ 0 FAIL/.test(w3bRun.out), w3bRun.out.slice(-200));

// W2 — the re-sit. revealed_at's committed state is null, so two seds and an
// rm -rf re-armed a spent pack with git status clean. The spent marker now
// lives in the chain, where the committed state is its ABSENCE.
const w2Id = "HLD-S28-v1";
const w2Dir = join(repoRoot, "qa-private", w2Id);
mkdirSync(w2Dir, { recursive: true });
writeFileSync(join(w2Dir, "README.md"), "# w2\n");
writeFileSync(join(w2Dir, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"echo done\"\n");
writeFileSync(join(w2Dir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S28", "--story", "ST-28", "--contract", "v1"]);
const w2First = run({ WB_QA_CONTEXT: "1" }, ["--id", w2Id, "--candidate", "abc1230"]);
const w2Anchor = readFileSync(join(repoRoot, "planning/holdouts/attempts", w2Id + ".log"), "utf8").trim().split("\n");
ok("W2: a sealed reveal appends the spent marker to the chain",
   w2First.code === 0 && w2Anchor[w2Anchor.length - 1].startsWith("revealed "), w2Anchor.slice(-1)[0]);
// The reviewer's exact re-arm: two seds + rm -rf, tree byte-identical to committed.
const w2Man = join(repoRoot, "planning/holdouts/manifests", w2Id + ".yaml");
writeFileSync(w2Man, readFileSync(w2Man, "utf8")
  .replace(/^revealed_at:.*$/m, "revealed_at: null")
  .replace(/^run_evidence_bundle:.*$/m, "run_evidence_bundle: null"));
rmSync(join(repoRoot, "planning/evidence", "EVB-" + w2Id), { recursive: true, force: true });
const w2Resit = run({ WB_QA_CONTEXT: "1" }, ["--id", w2Id, "--candidate", "abc1230"]);
ok("W2: the re-sit is REFUSED off the chain's revealed line — homework is dead again",
   w2Resit.code !== 0 && /"revealed" line/.test(w2Resit.out) && /O43/.test(w2Resit.out), w2Resit.out.slice(-240));

// W1 — the forward-commit burn. The case commits its own truncation, so
// HEAD's copy IS the truncated one; only the HISTORY walk sees the shrink.
const w1Id = "HLD-S90D-v1";
const w1Pack = join(repo2, "qa-private", w1Id);
const w1AnchorRel = "planning/holdouts/attempts/" + w1Id + ".log";
const w1CopyRel = "planning/evidence/EVB-" + w1Id + "/attempts.log";
mkdirSync(w1Pack, { recursive: true });
writeFileSync(join(w1Pack, "README.md"), "# w1\n");
writeFileSync(join(w1Pack, "cases.yaml"),
  "cases:\n  - id: H1\n    class: hostile\n    run: \"head -n1 " + w1AnchorRel + " > " + join(tmp, "w1a") + " && mv " + join(tmp, "w1a") + " " + w1AnchorRel + "; head -n1 " + w1CopyRel + " > " + join(tmp, "w1b") + " && mv " + join(tmp, "w1b") + " " + w1CopyRel + "; git -c user.email=x@x -c user.name=x commit -q -m tidy -- " + w1AnchorRel + "; kill -9 $PPID; true\"\n");
writeFileSync(join(w1Pack, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S90D", "--story", "ST-90", "--contract", "v1"], repo2);
git("add", "-A"); git("commit", "-q", "-m", "w1 pack");
writeFileSync(join(tmp, "w1key"), packKeys.get(w1Id)! + "\n");
execFileSync("/bin/sh", ["-c",
  `WB_QA_CONTEXT=1 bun ${JSON.stringify(TOOL)} --id ${w1Id} --candidate ${git("rev-parse", "HEAD").trim()} --key-stdin < ${JSON.stringify(join(tmp, "w1key"))} > /dev/null 2>&1; exit 0`,
], { cwd: repo2 });
execFileSync("/bin/sh", ["-c", `chmod u+rwX qa-private/${w1Id} && chmod -R u+rwX qa-private/${w1Id}`], { cwd: repo2 });
rmSync(join(repo2, "planning/evidence", "EVB-" + w1Id, ".reveal.lock"), { force: true });
const w1Resit = run({ WB_QA_CONTEXT: "1" }, ["--id", w1Id, "--candidate", git("rev-parse", "HEAD").trim()], repo2);
// X3 (seventh review): the walk still catches the shrink — but the permanent
// refusal was itself a weapon (one hostile anchor commit denied every future
// verdict, deniably). A foreign-author shrink now seals a TERMINAL record.
ok("W1/X3: a COMMITTED truncation is caught by the history walk and sealed as a terminal BRICKED verdict",
   w1Resit.code !== 0 && /BRICKED BY TAMPERING/.test(w1Resit.out), w1Resit.out.slice(-260));
const w1BunDir = join(repo2, "planning/evidence", "EVB-" + w1Id);
const w1BrickMan = existsSync(join(w1BunDir, "manifest.yaml")) ? readFileSync(join(w1BunDir, "manifest.yaml"), "utf8") : "(no bricked record was sealed)";
ok("X3/Z3: the bricked record names the shrinking commit, and the author as an unauthenticated CLAIM",
   /bricked: true/.test(w1BrickMan) && /bricked_commit: [0-9a-f]{40}/.test(w1BrickMan) &&
   /bricked_commit_author_claim: x@x/.test(w1BrickMan) && /UNAUTHENTICATED free text/.test(w1BrickMan),
   w1BrickMan.slice(0, 500));
const w1Again = run({ WB_QA_CONTEXT: "1" }, ["--id", w1Id, "--candidate", git("rev-parse", "HEAD").trim()], repo2);
ok("X3: a bricked pack refuses forever WITHOUT sealing a second record",
   w1Again.code !== 0 && /is BRICKED/.test(w1Again.out) &&
   readdirSync(w1BunDir).filter((f) => f.startsWith("holdout-run-")).length === 1,
   w1Again.out.slice(-220));

// W4 — modify-then-COMMIT mid-run: the tree reads clean, but HEAD is no longer
// the commit reveal itself made, and that is now a sealed, tampering fact.
const w4Id = "HLD-S90E-v1";
const w4Pack = join(repo2, "qa-private", w4Id);
mkdirSync(w4Pack, { recursive: true });
writeFileSync(join(w4Pack, "README.md"), "# w4\n");
writeFileSync(join(w4Pack, "cases.yaml"),
  'cases:\n  - id: H1\n    class: hostile\n    run: "echo w4 >> src.txt; git -c user.email=x@x -c user.name=x commit -qam w4-cover"\n');
writeFileSync(join(w4Pack, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S90E", "--story", "ST-90", "--contract", "v1"], repo2);
git("add", "-A"); git("commit", "-q", "-m", "w4 pack");
const w4Run = run({ WB_QA_CONTEXT: "1" }, ["--id", w4Id, "--candidate", git("rev-parse", "HEAD").trim()], repo2);
const w4Rec = readFileSync(join(repo2, "planning/evidence", "EVB-" + w4Id, "manifest.yaml"), "utf8");
ok("W4: a case that COMMITS its own edit is sealed as tampering even though the tree is clean",
   w4Run.code !== 0 && /TAMPERING RECORDED/.test(w4Run.out) &&
   /head_unchanged_during_run: false/.test(w4Rec) && /post_run_tree_clean: true/.test(w4Rec),
   w4Run.out.slice(-240));

// The reviewer's reasoned (untested) item: a planted .git/hooks/pre-commit.
// reveal's own commits run with core.hooksPath pointing at an empty directory,
// so a hostile hook can neither sabotage the anchor commits nor run code.
const whId = "HLD-S90F-v1";
const whPack = join(repo2, "qa-private", whId);
mkdirSync(whPack, { recursive: true });
writeFileSync(join(whPack, "README.md"), "# wh\n");
writeFileSync(join(whPack, "cases.yaml"), 'cases:\n  - id: H1\n    class: nominal\n    run: "echo hi"\n');
writeFileSync(join(whPack, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S90F", "--story", "ST-90", "--contract", "v1"], repo2);
git("add", "-A"); git("commit", "-q", "-m", "wh pack");
mkdirSync(join(repo2, ".git/hooks"), { recursive: true });
writeFileSync(join(repo2, ".git/hooks/pre-commit"), "#!/bin/sh\nexit 1\n");
chmodSync(join(repo2, ".git/hooks/pre-commit"), 0o755);
const whRun = run({ WB_QA_CONTEXT: "1" }, ["--id", whId, "--candidate", git("rev-parse", "HEAD").trim()], repo2);
rmSync(join(repo2, ".git/hooks/pre-commit"), { force: true });
ok("HOOKS: a planted pre-commit hook cannot block or ride reveal's anchor commits",
   whRun.code === 0 && /1 PASS \/ 0 FAIL/.test(whRun.out), whRun.out.slice(-220));

console.log("— seventh security review: X1/X2/X4, each executed defeat pinned —");

// X1 — the reviewer's merge burn. A merge commit whose TREE carries the old
// anchor, with the seal commit as second parent, is TREESAME to that parent —
// and a default `git log -- path` follows ONLY the TREESAME parent, hiding
// every growth commit from the walk. No history rewrite: an ordinary forward
// ref update. --full-history lists the merge; the prefix walk then refuses,
// and the X3 brick path seals the terminal verdict.
const x1Id = "HLD-S90G-v1";
const x1Pack = join(repo2, "qa-private", x1Id);
const x1AnchorRel = "planning/holdouts/attempts/" + x1Id + ".log";
mkdirSync(x1Pack, { recursive: true });
writeFileSync(join(x1Pack, "README.md"), "# x1\n");
writeFileSync(join(x1Pack, "cases.yaml"), 'cases:\n  - id: H1\n    class: hostile\n    run: "kill -9 $PPID; true"\n');
writeFileSync(join(x1Pack, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S90G", "--story", "ST-90", "--contract", "v1"], repo2);
git("add", "-A"); git("commit", "-q", "-m", "x1 pack");
const x1Seal = git("rev-parse", "HEAD").trim();
writeFileSync(join(tmp, "x1key"), packKeys.get(x1Id)! + "\n");
for (let i = 0; i < 2; i++) {   // two aborted attempts -> two committed growth commits
  execFileSync("/bin/sh", ["-c",
    `WB_QA_CONTEXT=1 bun ${JSON.stringify(TOOL)} --id ${x1Id} --candidate $(git rev-parse HEAD) --allow-unverified-candidate --key-stdin < ${JSON.stringify(join(tmp, "x1key"))} > /dev/null 2>&1; exit 0`,
  ], { cwd: repo2 });
  execFileSync("/bin/sh", ["-c", `chmod u+rwX qa-private/${x1Id} && chmod -R u+rwX qa-private/${x1Id}`], { cwd: repo2 });
  rmSync(join(repo2, "planning/evidence", "EVB-" + x1Id, ".reveal.lock"), { force: true });
}
git("checkout", x1Seal, "--", x1AnchorRel);          // stage the 1-line genesis blob
const x1Tree = git("write-tree").trim();
const x1Merge = git("commit-tree", x1Tree, "-p", "HEAD", "-p", x1Seal, "-m", "merge: housekeeping").trim();
git("reset", "--hard", x1Merge);                     // forward ref move: ordinary reflog entry, no rewrite
writeFileSync(join(repo2, "planning/evidence", "EVB-" + x1Id, "attempts.log"),
  readFileSync(join(repo2, x1AnchorRel), "utf8"));   // bundle copy agrees with the shrunk anchor
const x1Resit = run({ WB_QA_CONTEXT: "1" }, ["--id", x1Id, "--candidate", x1Merge], repo2);
ok("X1: a TREESAME merge cannot hide the growth commits — --full-history walks them, and the pack bricks",
   x1Resit.code !== 0 && /BRICKED BY TAMPERING/.test(x1Resit.out) && !/1 PASS/.test(x1Resit.out),
   x1Resit.out.slice(-260));
const x1V = vrrRun(repo2);
ok("X1/X3: verify-run-records CONFIRMS each brick against the live history and reports it terminal",
   /ok\s+EVB-HLD-S90G-v1\s+\[BRICKED BY TAMPERING/.test(x1V.out) && /ok\s+EVB-HLD-S90D-v1\s+\[BRICKED BY TAMPERING/.test(x1V.out),
   x1V.out.slice(-500));

// X2 — the fsmonitor foothold. .git/config is out of tree; a case CAN plant
// core.fsmonitor there. What it can no longer do is get reveal to EXECUTE it:
// every git call reveal makes carries -c core.fsmonitor=false (GIT_SAFE).
const x2Id = "HLD-S90H-v1";
const x2Pack = join(repo2, "qa-private", x2Id);
const x2Flag = join(tmp, "fsmon-fired");
const x2Script = join(tmp, "fsmon.sh");
writeFileSync(x2Script, `#!/bin/sh\ntouch ${x2Flag}\nexit 1\n`);
chmodSync(x2Script, 0o755);
mkdirSync(x2Pack, { recursive: true });
writeFileSync(join(x2Pack, "README.md"), "# x2\n");
writeFileSync(join(x2Pack, "cases.yaml"), `cases:\n  - id: H1\n    class: hostile\n    run: "git config core.fsmonitor ${x2Script}; echo planted"\n`);
writeFileSync(join(x2Pack, "expected.json"), JSON.stringify({ H1: { exit: 0, stdout_contains: "planted" } }) + "\n");
seal(["--slice", "S90H", "--story", "ST-90", "--contract", "v1"], repo2);
git("add", "-A"); git("commit", "-q", "-m", "x2 pack");
const x2Run = run({ WB_QA_CONTEXT: "1" }, ["--id", x2Id, "--candidate", git("rev-parse", "HEAD").trim()], repo2);
const x2ConfigSet = git("config", "--get", "core.fsmonitor").trim();
const x2Fired = existsSync(x2Flag);
git("config", "--unset", "core.fsmonitor");
ok("X2: a case CAN plant core.fsmonitor — but reveal's own git calls never execute it",
   x2ConfigSet === x2Script && !x2Fired,
   `set=${JSON.stringify(x2ConfigSet)} fired=${x2Fired}`);
// Z1 (eighth review): neutralizing OUR calls was not the property that mattered
// — the custodian's next plain `git status` still ran the payload, in the
// window where the NEXT pack's answers are plaintext. A mid-run plant cannot
// be refused away, so it is SEALED as tampering and the unset command printed.
const x2Man = readFileSync(join(repo2, "planning/evidence", "EVB-" + x2Id, "manifest.yaml"), "utf8");
ok("Z1: the mid-run plant is SEALED as tampering — keys named, unset command printed, exit 1",
   x2Run.code !== 0 && /TAMPERING RECORDED/.test(x2Run.out) && /config_planted=true/.test(x2Run.out) &&
   /git config --local --unset core\.fsmonitor/.test(x2Run.out) &&
   /config_planted_during_run: true/.test(x2Man) && /core\.fsmonitor/.test(x2Man),
   x2Run.out.slice(-300));

// Z1 — the OTHER two doors. seal runs in the authoring window itself (the one
// moment the answer key is plaintext), so it refuses outright; reveal refuses
// PRE-run — one unset later the pack reveals cleanly. Recovery, not a brick.
const z1Id = "HLD-S90J-v1";
const z1Pack = join(repo2, "qa-private", z1Id);
mkdirSync(z1Pack, { recursive: true });
writeFileSync(join(z1Pack, "README.md"), "# z1\n");
writeFileSync(join(z1Pack, "cases.yaml"), 'cases:\n  - id: H1\n    class: nominal\n    run: "echo ok"\n');
writeFileSync(join(z1Pack, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
git("config", "alias.pwn", "!echo pwned");
const z1Seal1 = seal(["--slice", "S90J", "--story", "ST-90", "--contract", "v1"], repo2);
ok("Z1: seal REFUSES while .git/config carries a command-valued key — the authoring window stays clean",
   z1Seal1.code !== 0 && /alias\.pwn/.test(z1Seal1.out) && /command-valued/.test(z1Seal1.out),
   z1Seal1.out.slice(-240));
git("config", "--unset", "alias.pwn");
seal(["--slice", "S90J", "--story", "ST-90", "--contract", "v1"], repo2);
git("add", "-A"); git("commit", "-q", "-m", "z1 pack");
git("config", "core.sshCommand", "ssh -o ProxyCommand=evil");
const z1Rev1 = run({ WB_QA_CONTEXT: "1" }, ["--id", z1Id, "--candidate", git("rev-parse", "HEAD").trim()], repo2);
ok("Z1: reveal REFUSES pre-run on a planted key — recoverable, pack NOT spent",
   z1Rev1.code !== 0 && /core\.sshcommand/.test(z1Rev1.out) && /pack NOT spent/.test(z1Rev1.out),
   z1Rev1.out.slice(-260));
git("config", "--unset", "core.sshCommand");
const z1Rev2 = run({ WB_QA_CONTEXT: "1" }, ["--id", z1Id, "--candidate", git("rev-parse", "HEAD").trim()], repo2);
ok("Z1: one unset later the same pack reveals cleanly — the refusal is recovery, not a brick",
   z1Rev2.code === 0 && /1 PASS \/ 0 FAIL/.test(z1Rev2.out), z1Rev2.out.slice(-200));

// Z2 — the silence branch. The identical shrink, committed AS
// holdout-reveal@local, used to take the hard-refusal path: no record, ever —
// strictly better for the attacker than the branded brick the foreign author
// earned. Every shrink now bricks; this spelling is additionally marked FORGED.
const z2Id = "HLD-S90I-v1";
const z2Pack = join(repo2, "qa-private", z2Id);
const z2AnchorRel = "planning/holdouts/attempts/" + z2Id + ".log";
const z2CopyRel = "planning/evidence/EVB-" + z2Id + "/attempts.log";
mkdirSync(z2Pack, { recursive: true });
writeFileSync(join(z2Pack, "README.md"), "# z2\n");
writeFileSync(join(z2Pack, "cases.yaml"),
  "cases:\n  - id: H1\n    class: hostile\n    run: \"head -n1 " + z2AnchorRel + " > " + join(tmp, "z2a") + " && mv " + join(tmp, "z2a") + " " + z2AnchorRel + "; head -n1 " + z2CopyRel + " > " + join(tmp, "z2b") + " && mv " + join(tmp, "z2b") + " " + z2CopyRel + "; git -c user.email=holdout-reveal@local -c user.name=holdout-reveal commit -q -m tidy -- " + z2AnchorRel + "; kill -9 $PPID; true\"\n");
writeFileSync(join(z2Pack, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
seal(["--slice", "S90I", "--story", "ST-90", "--contract", "v1"], repo2);
git("add", "-A"); git("commit", "-q", "-m", "z2 pack");
writeFileSync(join(tmp, "z2key"), packKeys.get(z2Id)! + "\n");
execFileSync("/bin/sh", ["-c",
  `WB_QA_CONTEXT=1 bun ${JSON.stringify(TOOL)} --id ${z2Id} --candidate $(git rev-parse HEAD) --allow-unverified-candidate --key-stdin < ${JSON.stringify(join(tmp, "z2key"))} > /dev/null 2>&1; exit 0`,
], { cwd: repo2 });
execFileSync("/bin/sh", ["-c", `chmod u+rwX qa-private/${z2Id} && chmod -R u+rwX qa-private/${z2Id}`], { cwd: repo2 });
rmSync(join(repo2, "planning/evidence", "EVB-" + z2Id, ".reveal.lock"), { force: true });
const z2Resit = run({ WB_QA_CONTEXT: "1" }, ["--id", z2Id, "--candidate", git("rev-parse", "HEAD").trim()], repo2);
ok("Z2: forging reveal's identity no longer buys silence — the shrink bricks like any other",
   z2Resit.code !== 0 && /BRICKED BY TAMPERING/.test(z2Resit.out), z2Resit.out.slice(-260));
const z2Man = readFileSync(join(repo2, "planning/evidence", "EVB-" + z2Id, "manifest.yaml"), "utf8");
const z2V = vrrRun(repo2);
ok("Z2/Z3: the record marks the identity FORGED, and the verifier confirms the brick",
   /bricked_commit_author_claim: holdout-reveal@local \(FORGED/.test(z2Man) &&
   /ok\s+EVB-HLD-S90I-v1\s+\[BRICKED BY TAMPERING/.test(z2V.out),
   z2Man.slice(0, 500));

// W3, the mutant-killer: a pack every SCANNER passes (plain block style, no
// dups, no flow) that is simply not canonical. Only the file-IS-its-own-parse
// requirement refuses it — remove that check and this test alone catches it.
const w3c = join(repoRoot, "qa-private", "HLD-S25-v1");
mkdirSync(w3c, { recursive: true });
writeFileSync(join(w3c, "README.md"), "# w3c\n");
writeFileSync(join(w3c, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"echo ok\"\n");
writeFileSync(join(w3c, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
manualSeal("HLD-S25-v1", w3c, 1, { rawCases: true });
const w3cRev = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S25-v1", "--candidate", "abc1230"]);
ok("W3: a scanner-clean but non-canonical pack is refused — the canonical check carries weight of its own",
   w3cRev.code !== 0 && /canonical form/.test(w3cRev.out) &&
   /revealed_at: null/.test(readFileSync(join(repoRoot, "planning/holdouts/manifests", "HLD-S25-v1.yaml"), "utf8")),
   w3cRev.out.slice(-200));

// X4 — Trojan Source. U+202E (RIGHT-TO-LEFT OVERRIDE) in a run string is a
// FIXED POINT of canonicalization: canonical(parse(x)) == x, so the W3 check
// passes while the text renders REVERSED to every human reader. The refusal
// is byte-level, beside the structural one, at seal AND at reveal.
const x4Dir = join(repoRoot, "qa-private", "HLD-S24-v1");
mkdirSync(x4Dir, { recursive: true });
writeFileSync(join(x4Dir, "README.md"), "# x4\n");
writeFileSync(join(x4Dir, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"echo \u202Egnp.liame\u202C ok\"\n");
writeFileSync(join(x4Dir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
const x4Seal = seal(["--slice", "S24", "--story", "ST-24", "--contract", "v1"]);
ok("X4: a bidi override in a run string is refused at seal, named by codepoint",
   x4Seal.code !== 0 && /U\+202E/.test(x4Seal.out) && /Trojan Source/.test(x4Seal.out), x4Seal.out.slice(-240));
// No rawCases here: manualSeal CANONICALIZES, and the bidi char survives it —
// this is the exact fixed point where the W3 byte-compare passes and ONLY the
// byte-level rule stands between the reader and the reversed text.
manualSeal("HLD-S24-v1", x4Dir, 1);
const x4Rev = run({ WB_QA_CONTEXT: "1" }, ["--id", "HLD-S24-v1", "--candidate", "abc1230"]);
ok("X4: the pack in CANONICAL form with the bidi char is refused at reveal, pack not spent",
   x4Rev.code !== 0 && /U\+202E/.test(x4Rev.out) && /pack NOT spent/.test(x4Rev.out), x4Rev.out.slice(-240));
const x4b = join(repoRoot, "qa-private", "HLD-S23-v1");
mkdirSync(x4b, { recursive: true });
writeFileSync(join(x4b, "README.md"), "# x4b\n");
writeFileSync(join(x4b, "cases.yaml"), "cases:\n  - id: H1\n    class: nominal\n    run: \"echo a\u200Bb\"\n");
writeFileSync(join(x4b, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
const x4bSeal = seal(["--slice", "S23", "--story", "ST-23", "--contract", "v1"]);
ok("X4: a ZERO-WIDTH SPACE is refused the same way — the whole invisible class, not one codepoint",
   x4bSeal.code !== 0 && /U\+200B/.test(x4bSeal.out), x4bSeal.out.slice(-200));

// The landscape this suite built — honest seals, tampered seals, forged-but-
// consistent bundles, healed chains — must verify as one coherent whole.
const wFinal = vrrRun(repoRoot);
ok("FINAL: verify-run-records passes the whole fixture landscape", wFinal.code === 0, wFinal.out.slice(-300));

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
