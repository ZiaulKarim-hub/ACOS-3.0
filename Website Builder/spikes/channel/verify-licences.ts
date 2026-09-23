#!/usr/bin/env bun
/**
 * verify-licences.ts — S06 step 4.
 *
 * "For each adopted dependency, open its ACTUAL LICENSE file and record the
 *  licence string, the commit/tag inspected and the date. Registry summaries are
 *  not evidence — one adopted candidate shows two different licences on two
 *  registries."
 *
 * The discrepancy class this hunts is recorded in PRD §20.3 U14: GrapesJS reports
 * NOASSERTION on the GitHub API and BSD-3-Clause on npm. A licence gate that reads
 * package.json is reading a CLAIM, not a licence.
 *
 * So this tool reads both and reports where they disagree:
 *   DECLARED — the `license` field in the package's own package.json (the claim)
 *   FILE     — the licence actually detected in its LICENSE/COPYING file (evidence)
 *
 * Usage: bun spikes/channel/verify-licences.ts <node_modules-dir>
 */

import { readdirSync, readFileSync, statSync, existsSync } from "node:fs";
import { join } from "node:path";

/**
 * ALL matches are returned, never just the first.
 *
 * WHY, and this was a real bug in this file's first version: a package's licence
 * file is often not ONE licence. `vite`'s LICENSE.md opens "Vite is released
 * under the MIT license" and then carries **84** further sections for vendored
 * dependencies. `@astrojs/compiler`'s LICENSE begins "MIT License" and contains a
 * BSD-3-Clause section for vendored Google code at line 39.
 *
 * A first-match scanner reported vite as ISC and @astrojs/compiler as
 * BSD-3-Clause. Both were WRONG about the package's own licence, and both were
 * pointing at something real. Returning one string per package cannot express
 * that, so it stops trying: PRIMARY is the licence the file leads with, and
 * ALSO_PRESENT is everything else found in it.
 */
const SIGNATURES: Array<[string, RegExp]> = [
  ["0BSD",         /Permission to use, copy, modify, and\/?or distribute this software for any\s+purpose with or without fee is hereby granted\. THE SOFTWARE IS PROVIDED/i],
  ["BSD-3-Clause", /Neither the name of .{0,80}nor the names of its contributors may be used to endorse/is],
  ["BSD-2-Clause", /Redistribution and use in source and binary forms.{0,400}THIS SOFTWARE IS PROVIDED/is],
  ["Apache-2.0",   /Apache License Version 2\.0/i],
  ["ISC",          /Permission to use, copy, modify, and\/?or distribute this software for any\s+purpose with or without fee is hereby granted, provided that the above copyright notice/i],
  ["MIT",          /Permission is hereby granted, free of charge, to any person obtaining a copy/i],
  ["MPL-2.0",      /Mozilla Public License Version 2\.0/i],
  ["Unlicense",    /This is free and unencumbered software released into the public domain/i],
  ["CC0-1.0",      /Creative Commons.{0,40}CC0/is],
  ["GPL-3.0",      /GNU GENERAL PUBLIC LICENSE Version 3/i],
  ["LGPL",         /GNU LESSER GENERAL PUBLIC LICENSE/i],
  ["AGPL",         /GNU AFFERO GENERAL PUBLIC LICENSE/i],
];

const LICENSE_NAMES = /^(LICENSE|LICENCE|COPYING|LICENSE\.md|LICENSE\.txt|LICENSE-MIT|LICENSE\.BSD)$/i;

/** Returns every licence found, ordered by where it first appears in the file.
 *  Position matters: the one the file LEADS with is the package's own. */
function detectAll(raw: string): string[] {
  // Collapse ALL whitespace before matching. WHY, and this was the second real
  // bug here: licence files hard-wrap their prose, so the MIT grant arrives as
  // "...to any person obtaining\na copy...". A pattern written with a literal
  // space misses it. The first version of this file returned UNDETERMINED for
  // **101 of 273** packages, 91 of which plainly declare MIT and plainly carry
  // the MIT text — the detector was measuring line-wrapping, not licences.
  const text = raw.replace(/\s+/g, " ");
  const hits: Array<[number, string]> = [];
  for (const [name, re] of SIGNATURES) {
    const m = re.exec(text);
    if (m) hits.push([m.index, name]);
  }
  hits.sort((a, b) => a[0] - b[0]);
  return [...new Set(hits.map((h) => h[1]))];
}

function packages(root: string): string[] {
  const out: string[] = [];
  for (const name of readdirSync(root).sort()) {
    if (name === ".bin" || name === ".package-lock.json") continue;
    const p = join(root, name);
    if (!statSync(p).isDirectory()) continue;
    if (name.startsWith("@")) {
      for (const sub of readdirSync(p).sort()) out.push(join(p, sub));
    } else out.push(p);
  }
  return out;
}

const root = process.argv[2];
if (!root || !existsSync(root)) { console.error("usage: bun verify-licences.ts <node_modules-dir>"); process.exit(1); }

interface Row { pkg: string; version: string; declared: string; file: string; detected: string; alsoPresent: string[] }
const rows: Row[] = [];

for (const dir of packages(root)) {
  const pjPath = join(dir, "package.json");
  if (!existsSync(pjPath)) continue;
  let pj: any; try { pj = JSON.parse(readFileSync(pjPath, "utf8")); } catch { continue; }
  const declared = typeof pj.license === "string" ? pj.license
    : Array.isArray(pj.licenses) ? pj.licenses.map((l: any) => l.type).join(" OR ")
    : pj.license?.type ?? "(none declared)";

  let file = "(no licence file)"; let detected = "NO FILE"; let alsoPresent: string[] = [];
  for (const f of readdirSync(dir)) {
    if (LICENSE_NAMES.test(f)) {
      file = f;
      const all = detectAll(readFileSync(join(dir, f), "utf8"));
      detected = all[0] ?? "UNDETERMINED";
      alsoPresent = all.slice(1);
      break;
    }
  }
  rows.push({ pkg: pj.name ?? dir, version: pj.version ?? "?", declared, file, detected, alsoPresent });
}

const norm = (s: string) => s.replace(/^\(|\)$/g, "").trim().toUpperCase();
const agrees = (r: Row) => norm(r.declared).includes(norm(r.detected)) || norm(r.detected).includes(norm(r.declared).split(" OR ")[0]);

const noFile = rows.filter((r) => r.detected === "NO FILE");
const undet = rows.filter((r) => r.detected === "UNDETERMINED");
const mismatch = rows.filter((r) => r.detected !== "NO FILE" && r.detected !== "UNDETERMINED" && !agrees(r));

console.log(JSON.stringify({
  scanned: rows.length,
  agree: rows.length - noFile.length - undet.length - mismatch.length,
  no_licence_file: noFile.length,
  undetermined: undet.length,
  declared_vs_file_mismatch: mismatch.length,
  mismatches: mismatch.map((r) => ({ pkg: r.pkg, version: r.version, declared: r.declared, file: r.file, detected: r.detected, alsoPresent: r.alsoPresent })),
  multi_licence_files: rows.filter((r) => r.alsoPresent.length).map((r) => ({ pkg: r.pkg, primary: r.detected, also: r.alsoPresent })),
  copyleft: rows.filter((r) => /GPL|AGPL|LGPL|MPL/i.test(r.declared + " " + r.detected + " " + r.alsoPresent.join(" "))).map((r) => ({ pkg: r.pkg, version: r.version, declared: r.declared, file: r.file, detected: r.detected, also: r.alsoPresent })),
  missing_file: noFile.map((r) => ({ pkg: r.pkg, version: r.version, declared: r.declared })),
  undetermined_list: undet.map((r) => ({ pkg: r.pkg, version: r.version, declared: r.declared, file: r.file })),
  rows,
}, null, 2));
