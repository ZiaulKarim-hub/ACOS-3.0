/**
 * S05 — two-build byte-reproducibility spike. Answers §12-O33:
 *   "Is an Astro/Vite production build byte-reproducible across two installs
 *    of the same lockfile on the same machine?"
 *
 * The question is decomposed, because "it differed" is not actionable on its own:
 *
 *   TEST 1  same node_modules, build twice      -> is the BUNDLER deterministic?
 *   TEST 2  two independent `npm ci`, build once each -> is INSTALL + BUILD deterministic?
 *
 * Test 1 failing means the bundler itself is nondeterministic. Test 1 passing and
 * test 2 failing means the install is what moves. O33 as written is test 2.
 *
 * This slice REPORTS. It does not adopt §12-O33's normalised-comparison fallback:
 * that weakens D3's proof and is DECISIONS.md item 5, which is Zee's to settle.
 */
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { cpSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { join, relative, sep } from "node:path";

const SRC = process.env.WB_S05_SRC ?? "/Users/zee/Documents/Vibe Coding/ACOS 3.0/Website Builder/spikes/substrate/a-framework";
const FIXTURE = process.env.WB_S05_FIXTURE ?? "light";
const WORK = process.env.WB_S05_WORK ?? "/private/tmp/claude-501/-Users-zee-Documents-Vibe-Coding-ACOS-3-0-Website-Builder/bac449f9-ed36-4ef3-87ed-17ba26eb97f2/scratchpad/s05";

const sha = (b: Buffer | string) => createHash("sha256").update(b).digest("hex");

/** Every file under dir, path-relative and sorted, with its own digest. */
function hashTree(dir: string): Record<string, string> {
  const out: Record<string, string> = {};
  const walk = (d: string) => {
    for (const name of readdirSync(d).sort()) {
      const full = join(d, name);
      const st = statSync(full);
      if (st.isDirectory()) walk(full);
      else if (st.isFile()) out[relative(dir, full).split(sep).join("/")] = sha(readFileSync(full));
    }
  };
  walk(dir);
  return out;
}

function run(cmd: string, args: string[], cwd: string, label: string, env: Record<string, string> = {}) {
  const t0 = Date.now();
  try {
    execFileSync(cmd, args, { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"],
      maxBuffer: 64 * 1024 * 1024, env: { ...process.env, ...env } });
  } catch (e: any) {
    console.error(`FAILED ${label}: ${cmd} ${args.join(" ")}\n${String(e.stdout ?? "")}\n${String(e.stderr ?? "")}`);
    process.exit(1);
  }
  console.log(`  ${label}: ${((Date.now() - t0) / 1000).toFixed(1)}s`);
}

/**
 * index.astro imports "../../../shared/tokens.json", which resolves THREE levels
 * above src/pages/ — i.e. a sibling of the project directory, not inside it.
 * The seeded layout must reproduce that or the build cannot resolve its inputs:
 *
 *   <root>/shared/{tokens,content}.json
 *   <root>/proj/{package.json, src/pages/index.astro}
 *
 * Returns the project directory; the caller never needs the root.
 */
function seed(root: string): string {
  rmSync(root, { recursive: true, force: true });
  mkdirSync(root, { recursive: true });
  // The light fixture imports "../../../shared/*.json"; the heavy one is
  // self-contained. Copy the sibling only when the fixture actually has one.
  if (existsSync(join(SRC, "..", "shared"))) cpSync(join(SRC, "..", "shared"), join(root, "shared"), { recursive: true });
  const proj = join(root, "proj");
  mkdirSync(proj, { recursive: true });
  for (const f of ["package.json", "package-lock.json"]) cpSync(join(SRC, f), join(proj, f));
  cpSync(join(SRC, "src"), join(proj, "src"), { recursive: true });
  return proj;
}

/** Compare two trees; returns the differing paths and the two one-sided sets. */
function compare(a: Record<string, string>, b: Record<string, string>) {
  const ka = Object.keys(a), kb = Object.keys(b);
  const onlyA = ka.filter((k) => !(k in b));
  const onlyB = kb.filter((k) => !(k in a));
  const differing = ka.filter((k) => k in b && a[k] !== b[k]);
  return { fileCountA: ka.length, fileCountB: kb.length, onlyA, onlyB, differing,
           identical: onlyA.length === 0 && onlyB.length === 0 && differing.length === 0 };
}

mkdirSync(WORK, { recursive: true });
const report: any = { question: "§12-O33", fixture: FIXTURE, src: SRC, node: process.version, started: new Date().toISOString() };

// ---- TEST 1: one install, two builds -> is the BUNDLER deterministic? -------
console.log("TEST 1 — same node_modules, two builds (bundler determinism)");
const t1 = seed(join(WORK, "t1"));
run("npm", ["ci", "--no-audit", "--no-fund"], t1, "install");
run("npx", ["astro", "build"], t1, "build 1");
const t1a = hashTree(join(t1, "dist"));
rmSync(join(t1, "dist"), { recursive: true, force: true });
rmSync(join(t1, ".astro"), { recursive: true, force: true });
run("npx", ["astro", "build"], t1, "build 2");
const t1b = hashTree(join(t1, "dist"));
report.test1 = { name: "same install, two builds", ...compare(t1a, t1b) };
console.log(`  -> ${report.test1.identical ? "BYTE-IDENTICAL" : "DIFFERS"} (${report.test1.fileCountA} files)`);

// ---- TEST 2: two independent installs -> O33 as written --------------------
console.log("TEST 2 — two independent `npm ci`, one build each (O33 as written)");
const t2a = seed(join(WORK, "t2a")), t2b = seed(join(WORK, "t2b"));
// Separate npm caches, so install B cannot simply replay install A's downloads.
// A shared warm cache would make the two installs agree for a reason that has
// nothing to do with the lockfile being reproducible.
run("npm", ["ci", "--no-audit", "--no-fund"], t2a, "install A", { npm_config_cache: join(WORK, "cache-a") });
run("npm", ["ci", "--no-audit", "--no-fund"], t2b, "install B", { npm_config_cache: join(WORK, "cache-b") });
run("npx", ["astro", "build"], t2a, "build A");
run("npx", ["astro", "build"], t2b, "build B");
const h2a = hashTree(join(t2a, "dist")), h2b = hashTree(join(t2b, "dist"));
report.test2 = { name: "two installs, one build each", ...compare(h2a, h2b) };
console.log(`  -> ${report.test2.identical ? "BYTE-IDENTICAL" : "DIFFERS"} (${report.test2.fileCountA} files)`);

// ---- supporting: are the two installs themselves identical? ----------------
const n2a = hashTree(join(t2a, "node_modules")), n2b = hashTree(join(t2b, "node_modules"));
report.installs = { name: "node_modules trees", ...compare(n2a, n2b) };
report.installs.onlyA = report.installs.onlyA.slice(0, 25);
report.installs.onlyB = report.installs.onlyB.slice(0, 25);
report.installs.differing = report.installs.differing.slice(0, 25);
console.log(`  node_modules identical: ${report.installs.identical} (${report.installs.fileCountA} vs ${report.installs.fileCountB} files)`);

report.output = {
  files: Object.keys(h2a).sort(),
  jsBundles: Object.keys(h2a).filter((f) => f.endsWith(".js")).length,
  totalBytes: Object.keys(h2a).length,
};
report.finished = new Date().toISOString();
writeFileSync(join(WORK, "report.json"), JSON.stringify(report, null, 2));
console.log(`\nreport: ${join(WORK, "report.json")}`);
console.log(`VERDICT test1 bundler=${report.test1.identical ? "REPRODUCIBLE" : "NOT REPRODUCIBLE"}  test2 O33=${report.test2.identical ? "REPRODUCIBLE" : "NOT REPRODUCIBLE"}`);
