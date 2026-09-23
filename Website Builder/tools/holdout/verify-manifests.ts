#!/usr/bin/env bun
/**
 * verify-manifests.ts — parse and shape-check every holdout manifest.
 *
 * Runs in ANY context, including the implementation one: it reads only the
 * PUBLIC manifests, never `qa-private/`. That is deliberate — the manifest is
 * public by design, so the implementer may confirm a pack EXISTS and is
 * well-formed without learning anything about its contents.
 *
 * Usage: bun tools/holdout/verify-manifests.ts [--expect N]
 * Exit:  0 = every check passed. 1 = at least one failed (details on stdout).
 *
 * `--expect N` is the census. R2P's equivalent literal has been hand-edited at
 * least four times as pairs were added, each with a written reason, and its
 * author recorded that the gate "went RED ... before this line moved, and that is
 * the census working rather than failing". A census that moves on its own is not
 * a census: a manifest that VANISHED would then be a smaller clean run instead of
 * a failure. So N is passed in and is expected to be argued for, not inferred.
 */

import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { parse, validate } from "./manifest.ts";

const MANIFEST_DIR = "planning/holdouts/manifests";

function main(argv: string[]): number {
  const i = argv.indexOf("--expect");
  const expect = i >= 0 ? Number(argv[i + 1]) : null;

  if (!existsSync(MANIFEST_DIR)) {
    // Diagnostic, not a failure: before the first pack is authored there is
    // genuinely nothing to verify, and a red gate there would be noise that
    // teaches people to ignore this tool.
    console.log(`verify-manifests: ${MANIFEST_DIR} does not exist — 0 manifests, nothing to check.`);
    return expect && expect > 0 ? (console.log(`FAIL: --expect ${expect} but the directory is absent.`), 1) : 0;
  }

  // A DIRECTORY named "*.yaml" previously crashed readFileSync with an uncaught
  // EISDIR, which fails the census for a reason that has nothing to do with any
  // manifest. Only regular files are manifests; anything else is reported and counted
  // bad, never silently skipped.
  const entries = readdirSync(MANIFEST_DIR, { withFileTypes: true })
    .filter((e) => e.name.endsWith(".yaml")).sort((a, b) => a.name.localeCompare(b.name));
  const notFiles = entries.filter((e) => !e.isFile()).map((e) => e.name);
  const files = entries.filter((e) => e.isFile()).map((e) => e.name);
  let bad = notFiles.length;
  for (const n of notFiles) console.log(`FAIL ${n}: not a regular file, so it cannot be a manifest`);
  let revealed = 0;

  for (const f of files) {
    const text = readFileSync(join(MANIFEST_DIR, f), "utf8");
    const r = parse(text);
    if (!r.ok) { console.log(`FAIL ${f}: does not parse — ${r.error}`); bad++; continue; }
    const problems = validate(r.value);
    if (problems.length) {
      console.log(`FAIL ${f}:`);
      for (const p of problems) console.log(`    ${p.field}: ${p.message}`);
      bad++;
      continue;
    }
    if ((r.value as any).revealed_at !== null) revealed++;
    console.log(`ok   ${f}${(r.value as any).revealed_at !== null ? "  (revealed — spent)" : ""}`);
  }

  console.log(`\n${files.length} manifest(s): ${files.length - bad} ok, ${bad} failed, ${revealed} already revealed.`);
  if (expect !== null && files.length !== expect) {
    console.log(`FAIL: expected ${expect} manifest(s), found ${files.length}. If a pack was added, move the census by hand and say why.`);
    return 1;
  }
  // Restated rather than assumed: a well-formed `revealed_at` for a reveal that
  // never happened passes every check above. Truth about a reveal lives in the
  // evidence bundle, not in this parser.
  return bad ? 1 : 0;
}

process.exit(main(process.argv.slice(2)));
