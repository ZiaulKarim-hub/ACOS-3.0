// PRD §22 — high-volume concurrency stress for the holdout manifest.
//
// WHY THIS EXISTS. Two small-N concurrency results were reported honestly and
// neither is proof: 5 same-id seal/reveal races and 3 different-id races. A QA
// review asked for a higher-volume run before either could be counted as cleared
// rather than reasoned about. This is that run. It is NOT part of holdout-test.ts
// because it takes minutes; it is run on demand and its output is filed as evidence.
//
// WHAT IT CHECKS, and the distinction the review drew:
//   - a TORN read is unparseable — the reader caught bytes mid-write
//   - a PARSEABLE-BUT-WRONG read parses fine but holds stale or mixed content
// The second is the dangerous one and the one nobody had tested. Every distinct
// byte-state a reader observes is recorded, parsed and validated, so a
// parseable-but-wrong state would show up as a SECOND distinct valid hash.
//
// Usage: bun tools/holdout/stress-concurrency.ts [rounds]

import { execFileSync, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createHash } from "node:crypto";
import { parse, validate } from "./manifest.ts";

const ROUNDS = Number(process.argv[2] ?? 120);
const SEAL = join(process.cwd(), "tools/holdout/seal.ts");
const REVEAL = join(process.cwd(), "tools/holdout/reveal.ts");

const repo = mkdtempSync(join(tmpdir(), "wb-stress-"));
const packId = "HLD-S60-v1";
const packDir = join(repo, "qa-private", packId);
mkdirSync(packDir, { recursive: true });
writeFileSync(join(packDir, "README.md"), "# stress\n");
writeFileSync(join(packDir, "cases.yaml"), 'cases:\n  - id: H1\n    class: nominal\n    run: "echo hi"\n');
writeFileSync(join(packDir, "expected.json"), JSON.stringify({ H1: { exit: 0 } }) + "\n");
const manifestPath = join(repo, "planning/holdouts/manifests", `${packId}.yaml`);
const readerLog = join(repo, "reads.txt");
const rcLog = join(repo, "rc.txt");

const sha = (b: Buffer) => createHash("sha256").update(b).digest("hex");

// Every distinct byte-state any reader ever saw, across every round.
const states = new Map<string, { text: string; count: number; rounds: Set<number> }>();
let multiWinnerRounds = 0, zeroWinnerRounds = 0, roundsWithReads = 0, totalReads = 0;

console.log(`stress: ${ROUNDS} rounds, repo ${repo}`);
const started = Date.now();

for (let round = 0; round < ROUNDS; round++) {
  rmSync(manifestPath, { force: true });
  // Two seals of the SAME id, launched together, with a reader hashing the name
  // as fast as it can for the whole window. Exactly one seal may win.
  const doneFlag = join(repo, "round.done");
  rmSync(doneFlag, { force: true });
  // The reader spins until the seals signal they are finished. An earlier version
  // ran a fixed 40 iterations and recorded ZERO reads — it finished before bun
  // had even started, and would have "passed" while proving nothing. That is why
  // a landed-read count is asserted at the end.
  execFileSync("sh", ["-c",
    `: > "${readerLog}"; : > "${rcLog}";\n` +
    `( while [ ! -f "${doneFlag}" ]; do\n` +
    `    if [ -f "${manifestPath}" ]; then shasum -a 256 "${manifestPath}" | cut -d" " -f1 >> "${readerLog}"; fi\n` +
    `  done ) & reader=$!\n` +
    `for i in 1 2; do ( bun "${SEAL}" --slice S60 --story ST-60 --contract v1 >/dev/null 2>&1; echo $? >> "${rcLog}" ) & seals="$seals $!"; done\n` +
    `wait $seals; : > "${doneFlag}"; wait $reader\n`,
  ], { cwd: repo, stdio: ["ignore", "pipe", "pipe"] });

  const rcs = readFileSync(rcLog, "utf8").trim().split("\n").filter(Boolean);
  const winners = rcs.filter((r) => r === "0").length;
  if (winners > 1) multiWinnerRounds++;
  if (winners < 1) zeroWinnerRounds++;

  const hashes = readFileSync(readerLog, "utf8").trim().split("\n").filter(Boolean);
  totalReads += hashes.length;
  if (hashes.length) roundsWithReads++;
  if (existsSync(manifestPath)) {
    const finalText = readFileSync(manifestPath, "utf8");
    const finalHash = sha(Buffer.from(finalText, "utf8"));
    for (const h of new Set(hashes)) {
      const rec = states.get(h) ?? { text: h === finalHash ? finalText : "(not the final state — captured only as a hash)", count: 0, rounds: new Set<number>() };
      rec.count++; rec.rounds.add(round);
      states.set(h, rec);
    }
    // The final state must itself be a valid manifest every single round.
    const p = parse(finalText);
    if (!p.ok || validate(p.value).length) {
      console.log(`ROUND ${round}: FINAL MANIFEST INVALID — ${p.ok ? validate(p.value).map((x) => x.field).join(",") : p.error}`);
    }
    states.set("FINAL:" + finalHash, { text: finalText, count: 1, rounds: new Set([round]) });
  }
}

// Collapse: how many DISTINCT byte-states did readers ever observe, ignoring the
// bookkeeping "FINAL:" entries? More than one means a reader saw something other
// than the published file — torn if it fails to parse, parseable-but-wrong if it
// parses. Either is a finding.
const observed = [...states.keys()].filter((k) => !k.startsWith("FINAL:"));
const finals = [...states.keys()].filter((k) => k.startsWith("FINAL:")).map((k) => k.slice(6));
const unexpected = observed.filter((h) => !finals.includes(h));

const secs = ((Date.now() - started) / 1000).toFixed(1);
console.log(`\nrounds                     ${ROUNDS}`);
console.log(`rounds where a read landed ${roundsWithReads}`);
console.log(`total reads                ${totalReads}`);
console.log(`rounds with >1 winner      ${multiWinnerRounds}`);
console.log(`rounds with 0 winners      ${zeroWinnerRounds}`);
console.log(`distinct states observed   ${observed.length}`);
console.log(`distinct FINAL states      ${finals.length}`);
console.log(`states that were NOT a published final file  ${unexpected.length}`);
console.log(`elapsed                    ${secs}s`);

let bad = 0;
if (multiWinnerRounds) { console.log(`\nFAIL: ${multiWinnerRounds} round(s) had more than one winning seal.`); bad++; }
if (zeroWinnerRounds) { console.log(`\nFAIL: ${zeroWinnerRounds} round(s) had no winning seal.`); bad++; }
if (unexpected.length) { console.log(`\nFAIL: readers observed ${unexpected.length} state(s) that were never a published final file.`); bad++; }
if (!roundsWithReads) { console.log(`\nFAIL: no read ever landed — the test proved nothing.`); bad++; }

// Second phase: seal racing a reveal of the SAME id, at volume. A reveal must
// either refuse cleanly (no manifest yet) or run against a fully valid manifest.
// It must NEVER refuse because the manifest failed to parse or validate.
let parseRefusals = 0, cleanRefusals = 0, reveals = 0, otherOutcomes = 0;
const RACE_ROUNDS = Math.max(20, Math.floor(ROUNDS / 3));
for (let round = 0; round < RACE_ROUNDS; round++) {
  rmSync(manifestPath, { force: true });
  rmSync(join(repo, "planning/evidence"), { recursive: true, force: true });
  // A randomized sub-second delay before the reveal, so the rounds SAMPLE across
  // the seal's whole execution window instead of all landing in the same instant.
  const delay = (round % 12) * 0.004;
  const out = spawnSync("sh", ["-c",
    `( bun "${SEAL}" --slice S60 --story ST-60 --contract v1 >/dev/null 2>&1 ) &\n` +
    `sleep ${delay.toFixed(3)}\n` +
    `bun "${REVEAL}" --id ${packId} --candidate cafe6000 --allow-unverified-candidate 2>&1\n` +
    `wait\n`,
  ], { cwd: repo, encoding: "utf8", env: { ...process.env, WB_QA_CONTEXT: "1" } });
  const text = (out.stdout ?? "") + (out.stderr ?? "");
  if (/does not parse|is invalid/.test(text)) parseRefusals++;
  else if (/no manifest at/.test(text)) cleanRefusals++;
  else if (/PASS \/ .* FAIL of/.test(text)) reveals++;
  else otherOutcomes++;
}
console.log(`\nseal-vs-reveal, same id, ${RACE_ROUNDS} rounds`);
console.log(`  clean "no manifest yet" refusals   ${cleanRefusals}`);
console.log(`  full reveals against a valid file  ${reveals}`);
console.log(`  other outcomes                     ${otherOutcomes}`);
console.log(`  PARSE/VALIDATE refusals (the bug)  ${parseRefusals}`);
if (parseRefusals) { console.log(`\nFAIL: ${parseRefusals} reveal(s) read a manifest that did not parse or validate.`); bad++; }

rmSync(repo, { recursive: true, force: true });
console.log(bad ? `\nSTRESS FAILED (${bad} check(s))` : `\nSTRESS PASSED — every check held.`);
process.exit(bad ? 1 : 0);
