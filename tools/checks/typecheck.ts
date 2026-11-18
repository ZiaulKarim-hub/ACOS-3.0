#!/usr/bin/env bun
/**
 * typecheck.ts — the repo's `typecheck` check (FUN-3).
 *
 * WHY IT EXISTS. The Nemesis S3 scan refuses to call a repo clean while a check is
 * SKIPPED — "a skip is not a pass" — and it looks for a `typecheck` script, then a root
 * tsconfig.json, then Cargo.toml. This workspace had none of the three, so every scan
 * reported a skip and no finding could be closed.
 *
 * WHY NOT JUST ADD A ROOT tsconfig.json. There is no single program here. This workspace
 * holds several independent projects with incompatible compiler settings — a React app
 * with JSX and DOM libs, bun scripts with bun-types, skills with their own strictness —
 * and one root config would have to be loose enough for all of them, which would weaken
 * the checking that each project's own config already does well. So this runs each real
 * tsconfig on its own terms.
 *
 * HOW IT STAYS HONEST. A list of paths is exactly the kind of thing that keeps passing
 * while new code appears beside it. So the run DISCOVERS every tsconfig in the workspace
 * and must account for each one: it is checked, or it is named in NOT_CHECKED with the
 * reason. An unaccounted config FAILS the check rather than being ignored, and a listed
 * config that no longer exists fails too, so the list cannot rot in either direction.
 */

import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { isUnder, walkRepo } from "./discover.ts";
import { runGate } from "./gate-env.ts";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");

/** Measured 2026-11-18: each of these reports 0 errors. */
const CHECKED = [
  ".claude/skills/acos-jason-breakglass/tsconfig.json",
  ".claude/skills/acos-nemesis-protocol/scripts/tsconfig.json",
  ".claude/skills/acos-research-riffs/tsconfig.json",
  ".claude/skills/investigate/tsconfig.json",
  ".claude/skills/research/tsconfig.json",
];

/**
 * Not checked here, each with the measurement behind it. These are reasons, not excuses:
 * the point of writing them down is that the next reader can re-measure the claim.
 */
const NOT_CHECKED: { prefix: string; why: string }[] = [
  {
    prefix: "apps/visual-composer/",
    why: "a separate Vite project whose dependencies are NOT installed in this checkout — "
      + "it has no node_modules of its own, and `tsc -p` there fails with exactly two errors, "
      + "TS2688 for 'vite/client' and TS2688 for 'vitest/globals', both missing type PACKAGES "
      + "rather than anything wrong with its code. It carries its own `typecheck` script "
      + "(`tsc --noEmit`) and must be checked from inside itself after `bun install`.",
  },
];

function accountFor(configs: string[]): string[] {
  return configs.filter((c) =>
    !CHECKED.includes(c) && !NOT_CHECKED.some((n) => isUnder(c, n.prefix.replace(/\/$/, ""))));
}

function main(): number {
  const discovered = walkRepo(ROOT).filter((f) => /(^|\/)tsconfig[^/]*\.json$/.test(f));

  const unaccounted = accountFor(discovered);
  const missing = CHECKED.filter((c) => !existsSync(resolve(ROOT, c)));

  if (unaccounted.length > 0 || missing.length > 0) {
    console.error("typecheck: the list of tsconfigs no longer matches the repo.\n");
    for (const c of unaccounted) {
      console.error(`  UNACCOUNTED  ${c}`);
      console.error("               add it to CHECKED, or to NOT_CHECKED with the reason.");
    }
    for (const c of missing) {
      console.error(`  MISSING      ${c}`);
      console.error("               listed in CHECKED but not on disk; remove it or restore it.");
    }
    return 1;
  }

  /**
   * THE INSTALLED COMPILER, OR NOTHING (SEC-32).
   *
   * This used to run `bunx tsc`, and bunx only uses the typescript version pinned in the
   * root package.json when the root node_modules is present. In a fresh checkout it is not: bunx would then DOWNLOAD
   * and run the unpinned npm package literally named `tsc`, which is a different,
   * unreviewed project and not TypeScript at all. So the gate that decides whether this
   * repository typechecks could end up running third-party code and reporting on a
   * compiler nobody chose -- and reporting a pass is the dangerous direction.
   *
   * The binary is therefore resolved on disk, under this repository, and a missing install
   * is a FAILURE rather than a trip to the registry. The message says what to run, because
   * "FAIL" with no route forward is how a gate gets switched off.
   */
  const TSC = `${ROOT}/node_modules/typescript/bin/tsc`;
  if (!existsSync(TSC)) {
    // stderr and `return 1`, like every other failure in this function, so
    // `process.exit(main())` stays the only place this program decides its own status.
    console.error(`FAIL  the pinned TypeScript is not installed at ${TSC}`);
    console.error("typecheck: cannot run — install the pinned compiler first: bun install");
    return 1;
  }

  let failed = 0;
  for (const cfg of CHECKED) {
    const run = runGate(process.execPath, [TSC, "--noEmit", "-p", cfg], { cwd: ROOT });

    const output = `${run.stdout}${run.stderr}`.trim();
    // A spawn that never ran is a FAILURE, not a pass: `status` is null when the process
    // could not start or was killed by a signal, and `null !== 0` would read as "fine"
    // under a loose check while nothing had been verified at all.
    const ok = run.error === undefined && run.signal === null && run.status === 0;
    console.log(`${ok ? "pass" : "FAIL"}  ${cfg}`);
    if (!ok) {
      failed += 1;
      if (run.error !== undefined) console.error(`      could not run tsc: ${run.error.message}`);
      if (run.signal !== null) console.error(`      tsc was killed by ${run.signal}`);
      if (output !== "") console.error(output.split("\n").map((l) => `      ${l}`).join("\n"));
    }
  }

  for (const n of NOT_CHECKED) console.log(`skip  ${n.prefix} — ${n.why}`);

  console.log(`\ntypecheck: ${CHECKED.length - failed}/${CHECKED.length} configs clean`);
  return failed === 0 ? 0 : 1;
}

process.exit(main());
