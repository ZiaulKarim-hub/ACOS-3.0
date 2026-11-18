/**
 * checks.test.ts — the rows that keep the repo's three checks from going quiet again.
 *
 * These exist because of FUN-3, FUN-4, FUN-5 and FUN-6: the S3 scan reported `typecheck`
 * and `lint` as SKIPPED and `test` as FAILED, and a skip is not a pass. The scan resolves
 * each check by looking in package.json FIRST (lib/scan.ts), so the scripts named here are
 * the whole mechanism — delete one and the scan silently goes back to reporting a skip
 * rather than an error. That is what these rows catch.
 *
 * WHY THESE ROWS BELONG TO THE JASON BREAK-GLASS TASK, which was asked and is worth
 * answering here rather than in a ledger entry (FUN-115). R-014 is the requirement that
 * the 50% stop cannot be raised, and the only MECHANICAL proof of it is ceiling.test.ts,
 * which sweeps the live decision from 0.000 to 1.000 and asserts where it turns over. That
 * proof is worth exactly as much as the gate that runs it. If the `test` check can be
 * pointed at a stub bun, handed a preloaded module, or narrowed by one extra argument, then
 * the sweep still exists and nothing runs it, and R-014 has no proof at all — while every
 * scan reports green. So the rows about the toolchain are not a second project; they are
 * the part of R-014 that lives outside the skill's own folder, and each one names the
 * finding it came from (SEC-28 through SEC-36).
 */
import { describe, expect, it } from "bun:test";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, readdirSync, realpathSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { isUnder, walkRepo } from "./discover.ts";
import { GATE_ENV_ALLOW, gateEnv } from "./gate-env.ts";
import { accountFor } from "./tests.ts";

const ROOT = resolve(fileURLToPath(new URL(".", import.meta.url)), "..", "..");
const pkg = JSON.parse(readFileSync(join(ROOT, "package.json"), "utf8")) as { scripts?: Record<string, string> };

describe("the three checks the S3 scan looks for actually exist", () => {
  it("declares a typecheck, a lint and a test script in the root package.json", () => {
    for (const name of ["typecheck", "lint", "test"]) {
      expect(pkg.scripts?.[name], `package.json has no "${name}" script, so S3 reports it SKIPPED`).toBeTruthy();
    }
  });

  /**
   * THE EXACT STRING THE SCAN IGNORES. `lib/scan.ts` credits scripts.test only when it
   * does NOT match /no test specified/ — so `npm init`'s placeholder, which this repo
   * carried, left the scan falling through to a bare `bun test`. That is how another
   * project's vitest suites became this repo's test result.
   */
  it("does not leave the npm placeholder as the test script", () => {
    expect(/no test specified/.test(pkg.scripts?.test ?? "")).toBe(false);
  });

  it("keeps a linter config on disk, which is the scan's second way of finding one", () => {
    expect(existsSync(join(ROOT, "biome.jsonc")) || existsSync(join(ROOT, "biome.json"))).toBe(true);
    const cfg = readFileSync(join(ROOT, "biome.jsonc"), "utf8");
    expect(cfg).toContain('"linter"');
    // The formatter stays off: enabling it would reformat files this goal never touched.
    expect(/"formatter"\s*:\s*\{\s*"enabled"\s*:\s*false/.test(cfg)).toBe(true);
  });
});

describe("the walk cannot adopt another project's suites (FUN-5)", () => {
  it("skips node_modules at ANY depth, not just the top level", () => {
    const base = join(tmpdir(), `bg-walk-${process.pid}-${Date.now()}`);
    try {
      mkdirSync(join(base, "pkg", "node_modules", "zod", "tests"), { recursive: true });
      writeFileSync(join(base, "pkg", "node_modules", "zod", "tests", "deep.test.ts"), "// vendored");
      mkdirSync(join(base, "pkg", "src"), { recursive: true });
      writeFileSync(join(base, "pkg", "src", "mine.test.ts"), "// ours");
      const found = walkRepo(base);
      // The positive half matters as much as the negative: a walk that returned NOTHING
      // would also pass a bare "does not contain zod" assertion.
      expect(found).toContain("pkg/src/mine.test.ts");
      expect(found.some((f) => f.includes("node_modules"))).toBe(false);
    } finally {
      rmSync(base, { recursive: true, force: true });
    }
  });

  it("skips a nested .nemesis, where the protocol keeps frozen copies of judged files", () => {
    const base = join(tmpdir(), `bg-walk2-${process.pid}-${Date.now()}`);
    try {
      mkdirSync(join(base, ".nemesis", "snapshots", "1", "files"), { recursive: true });
      writeFileSync(join(base, ".nemesis", "snapshots", "1", "files", "copy.test.ts"), "// frozen");
      writeFileSync(join(base, "real.test.ts"), "// current");
      const found = walkRepo(base);
      expect(found).toContain("real.test.ts");
      expect(found.some((f) => f.includes(".nemesis"))).toBe(false);
    } finally {
      rmSync(base, { recursive: true, force: true });
    }
  });

  it("compares containment on whole path segments, so tools does not match toolsmith", () => {
    expect(isUnder("tools/checks/tests.ts", "tools")).toBe(true);
    expect(isUnder("toolsmith/evil.test.ts", "tools")).toBe(false);
    expect(isUnder("anything", ".")).toBe(true);
  });
});

/**
 * A GATE MUST RUN THE THING THIS REPOSITORY CHOSE, NOT WHATEVER ARRIVES (SEC-29/30/32).
 *
 * Three gates decide whether this workspace is healthy, and each of them was reaching
 * outside the repository for the program that would answer:
 *
 *   SEC-30  the test gate spawned the bare name `bun`, looked up through the caller's
 *           PATH. A stub earlier on PATH printing "Ran 1 tests" and exiting 0 would have
 *           turned every suite group green. Same class as the `ps` and `doppler` fixes.
 *   SEC-32  the typecheck gate ran `bunx tsc`, and bunx only uses the pinned typescript
 *           when the root node_modules is installed. In a fresh checkout it would have
 *           DOWNLOADED the unrelated npm package literally named `tsc` and reported on it.
 *   SEC-29  the lint gate asked for `@biomejs/biome@2`, so the registry chose the release.
 *           This machine's cache already holds 2.3.15, 2.4.4, 2.6.4 and 2.6.8 — the
 *           version had drifted four times without one line changing in this repository.
 *
 * THESE ROWS READ SOURCE, AND SAY SO. Proving the fail-closed branches behaviourally
 * means removing the installed compiler, or putting a fake bun on PATH for a nested gate
 * run, and a test that moves the toolchain out from under a live repository can leave it
 * broken if it dies halfway. What a regression would actually do is reintroduce one of
 * these three spellings, and that is what these rows refuse.
 */
describe("every gate runs the program this repository pinned (SEC-29, SEC-30, SEC-32)", () => {
  const source = (rel: string): string => {
    const text = readFileSync(join(ROOT, rel), "utf8");
    // Comments stripped, because the paragraphs above quote the very spellings being
    // banned — a check that cannot tell code from prose about code would force the
    // explanation to be deleted to stay green.
    return text.split("\n").filter((l) => !/^(\/\/|\/\*|\*)/.test(l.trim())).join("\n");
  };

  it("runs the suites with this bun, not a name resolved through PATH (SEC-30)", () => {
    const code = source("tools/checks/tests.ts");
    // Both forms, because the gate now starts programs through the runGate wrapper (SEC-35)
    // and the thing that matters is that the BINARY is the interpreter already running,
    // never the name `bun` resolved through whatever PATH the caller carried.
    // Not the TEXT "bun" -- it is a legitimate runner name in this file's own types -- but
    // "bun" as the PROGRAM a call starts, in any call, which is the SEC-30 defect itself.
    expect(/\(\s*"bun"\s*[,)]/.test(code), "no program may be started by the name bun").toBe(false);
    expect(code).toContain("const BUN = process.execPath;");
    expect(code).toContain("runGate(BUN,");
  });

  it("runs the compiler installed here, and fails closed when it is absent (SEC-32)", () => {
    const code = source("tools/checks/typecheck.ts");
    expect(code).not.toContain('spawnSync("bunx"');
    expect(code).toContain("node_modules/typescript/bin/tsc");
    // The fail-closed half: a missing install must be a FAILURE, never a registry fetch.
    expect(code).toContain("if (!existsSync(TSC))");
    expect(code).toContain("return 1;");
    // And the compiler really is where the gate looks, in this checkout.
    expect(existsSync(join(ROOT, "node_modules/typescript/bin/tsc"))).toBe(true);
  });

  it("pins the linter to one exact release, not a range (SEC-29)", () => {
    const lint = pkg.scripts?.lint ?? "";
    const named = /@biomejs\/biome@(\S+)/.exec(lint)?.[1] ?? "";
    expect(named, `the lint script must name a biome version: ${lint}`).not.toBe("");
    // An exact pin is a bare semver. `2`, `^2.6.8` and `2.x` all let the registry choose.
    expect(named, `the lint version must be exact, not a range: ${named}`).toMatch(/^\d+\.\d+\.\d+$/);

    // AND THE CONFIG IS VALIDATED AGAINST THE SAME RELEASE (FUN-116). biome.jsonc names a
    // version too, in its $schema, and if the two drift then the rules the gate runs are
    // not the rules this config was written against — a config can declare a rule the
    // running release does not have, or miss one it added. A comment in biome.jsonc tells
    // the reader this is checked, so it is checked here rather than left as a claim.
    const schema = /biomejs\.dev\/schemas\/(\d+\.\d+\.\d+)\/schema\.json/
      .exec(readFileSync(join(ROOT, "biome.jsonc"), "utf8"))?.[1] ?? "";
    expect(schema, "biome.jsonc must name a schema version").not.toBe("");
    expect(schema, "biome.jsonc's schema and the lint script must name one release").toBe(named);
  });
});

/**
 * THE GATE DEFINITIONS ARE SOURCE TOO (SEC-28, SEC-31).
 *
 * Two of the checks that run on every scan are not code in this repository at all -- they
 * are entries in `.nemesis/config.json`. That file was outside `source_globs`, the list of
 * paths the judge reads, so an edit to it was never judged and raised no finding. Someone
 * could narrow the `--cwd`, add a filter that matches nothing, or delete an entry outright,
 * and every scan would go on reporting a clean run while checking less and less.
 *
 * Widening `source_globs` fixes the judging half. These rows are the other half: a quiet
 * loosening now turns a test red, which does not depend on anyone reading a diff.
 *
 * STILL TRUE AND NOT CLOSED BY THIS: `.nemesis/config.json` is not committed to git, so
 * these rows guard its CONTENT, not its history. Committing it is the user's call, not
 * something to slip in here.
 */
describe("the checks defined outside the code cannot be quietly loosened (SEC-28, SEC-31)", () => {
  interface Check { id: string; cmd: string; args: string[] }
  const cfg = JSON.parse(readFileSync(join(ROOT, ".nemesis/config.json"), "utf8")) as {
    source_globs?: string[];
    extra_checks?: Check[];
  };
  const byId = (id: string): Check | undefined => (cfg.extra_checks ?? []).find((c) => c.id === id);

  it("still declares both extra checks", () => {
    expect((cfg.extra_checks ?? []).map((c) => c.id).sort()).toEqual(["test-breakglass", "typecheck-breakglass"]);
  });

  /**
   * EVERY EXTRA CHECK NOW GOES THROUGH THE CLEAN-ENVIRONMENT LAUNCHER (SEC-40), so its
   * command is `/bin/sh clean-env.sh <interpreter> <arguments>`. The launcher is a shell
   * script rather than a flag because a preload module runs BEFORE a bun entry file and can
   * replace what that file imports — measured — so the cleaning has to happen in a process
   * that is not bun. The interpreter stays pinned by absolute path inside the arguments,
   * which is what SEC-30 asked for, and the launcher deliberately knows nothing about bun.
   */
  const parts = (id: string): { launcher: string; interpreter: string; rest: string[] } => {
    const c = byId(id);
    expect(c, `${id} must still be declared`).toBeDefined();
    expect(c?.cmd, `${id} must run through a shell, not bun directly`).toBe("/bin/sh");
    const args = c?.args ?? [];
    return { launcher: args[0] ?? "", interpreter: args[1] ?? "", rest: args.slice(2) };
  };

  it("runs the breakglass suite over the WHOLE skill, with no narrowing filter", () => {
    // The exact arguments, because every part of them is load-bearing: a changed --cwd
    // points the suite somewhere else, and ANY extra argument is a filter that can quietly
    // reduce what runs to nothing while the check still reports a pass.
    expect(parts("test-breakglass").rest).toEqual(["test", "--cwd", ".claude/skills/acos-jason-breakglass"]);
  });

  it("typechecks the breakglass tsconfig with the compiler installed here", () => {
    // THE WHOLE ARGUMENT LIST, not a `toContain` sweep (SEC-36). Containment accepts
    // anything EXTRA, and an extra argument to tsc is a narrowing: a second `-p` naming an
    // emptier config, or a `--project` override, leaves this check green over nothing. The
    // compiler is named by its path inside node_modules rather than as `tsc`, because
    // `bunx tsc` fetches an unrelated package of that name when node_modules is missing.
    expect(parts("typecheck-breakglass").rest).toEqual([
      join(ROOT, "node_modules/typescript/bin/tsc"),
      "--noEmit", "-p", ".claude/skills/acos-jason-breakglass/tsconfig.json",
    ]);
  });

  /**
   * SEC-36. "Absolute, and it exists" was not enough. /usr/bin/true is absolute, exists,
   * accepts any arguments and exits 0, so pointing either check at it satisfied every row
   * here while running nothing at all — and the scan would have reported both green. The
   * interpreter must be the SAME FILE as the one running this suite, compared through
   * realpath so that a symlinked bun install still matches.
   */
  it("runs each one with this very bun, through the clean launcher (SEC-30, SEC-36, SEC-40)", () => {
    for (const id of ["test-breakglass", "typecheck-breakglass"]) {
      const { launcher, interpreter } = parts(id);
      expect(launcher, `${id} must go through the launcher`).toBe(join(ROOT, "tools/checks/clean-env.sh"));
      expect(existsSync(launcher), `${id}'s launcher must exist`).toBe(true);
      expect(interpreter.startsWith("/"), `${id} must name an absolute interpreter, not ${interpreter}`).toBe(true);
      expect(existsSync(interpreter), `${id}'s interpreter must exist: ${interpreter}`).toBe(true);
      expect(basename(interpreter), `${id} must run bun, not ${interpreter}`).toBe("bun");
      expect(realpathSync(interpreter), `${id} must run the bun this suite is running on`)
        .toBe(realpathSync(process.execPath));
    }
  });


  it("keeps the files that DEFINE the gates inside the judged paths", () => {
    const globs = cfg.source_globs ?? [];
    for (const needed of ["package.json", "tools/checks/**", ".nemesis/config.json"]) {
      expect(globs, `${needed} must be judged`).toContain(needed);
    }
  });
});

/**
 * SEC-35. The gates spawn bun to run the suites and the compiler, and they used to hand it
 * this process's whole environment. One variable is enough to change what bun LOADS, so
 * the rows here prove three things in order: that the lever is real on the bun installed
 * now, that a leaking gate IS caught by the way this is measured, and that the real gates
 * pass nothing poisonous to anything they start.
 *
 * The primary lock is BEHAVIOURAL. Three text versions of the last row were each defeated
 * by something ordinary — single quotes, a renamed import, two imports on one line, and
 * then `Bun` being a global so that a gate needs no import at all to start a program. A
 * text row whose stated guarantee is false is worse than no row, so the gate is RUN.
 */
describe("the gates do not let the environment decide what runs (SEC-35)", () => {
  const TAG = `${process.pid}-${Date.now()}`;
  const pre = join(tmpdir(), `gate-env-preload-${TAG}.ts`);
  const trace = join(tmpdir(), `gate-env-trace-${TAG}.log`);
  const leaky = join(tmpdir(), `gate-env-leaky-${TAG}.ts`);
  const MARKER = "PRELOAD-RAN-INSTEAD";

  /**
   * A preload that leaves a trace THE GATE CANNOT SWALLOW: it appends its own process id
   * to a file. The first version printed a marker to stdout, which typecheck.ts captures
   * per child and prints only when tsc FAILS — so a leaked preload would have been
   * invisible in exactly the case that matters, and the row could not have failed.
   */
  const writePreload = (): void => {
    writeFileSync(pre, `require("node:fs").appendFileSync(${JSON.stringify(trace)}, process.pid + "\\n");\n`);
  };
  const traced = (): string[] => {
    try { return readFileSync(trace, "utf8").split("\n").filter((l) => l.trim() !== ""); } catch { return []; }
  };
  const poison = (): Record<string, string> => ({
    PATH: process.env.PATH ?? "", HOME: process.env.HOME ?? "",
    TMPDIR: process.env.TMPDIR ?? "", BUN_OPTIONS: `--preload ${pre}`,
  });
  const cleanUp = (): void => {
    for (const f of [pre, trace, leaky]) rmSync(f, { force: true });
  };

  it("keeps only the names on the list, whatever else is set", () => {
    // A CREDENTIAL NAME IS DELIBERATELY NOT USED AS A FIXTURE HERE (SEC-21, SEC-39). The
    // first version listed one, and the secret scan rightly called it a hard-coded
    // credential: a scanner cannot tell a convincing fake from a real one, and a file that
    // trains its readers to ignore that alarm is worse than the fake itself. It proved
    // nothing extra either — the list is name-blind, so RANDOM_THING covers the same case.
    const given = {
      PATH: "/usr/bin", HOME: "/tmp/home", TMPDIR: "/tmp/", USER: "someone",
      BUN_OPTIONS: "--preload /tmp/evil.ts", NODE_OPTIONS: "--require /tmp/evil.js",
      BUN_INSPECT: "1", RANDOM_THING: "x",
    };
    expect(gateEnv(given)).toEqual({
      PATH: "/usr/bin", HOME: "/tmp/home", TMPDIR: "/tmp/", USER: "someone",
    });
    // An allowed name that is NOT set stays absent rather than arriving empty: an empty
    // PATH and no PATH are different things to a child process.
    expect("LANG" in gateEnv({ PATH: "/usr/bin" })).toBe(false);
    expect(GATE_ENV_ALLOW).not.toContain("BUN_OPTIONS");
  });

  /**
   * THE LEVER, MEASURED RATHER THAN ASSUMED. If a future bun stopped honouring
   * BUN_OPTIONS this row would fail, and that is the right outcome: it would mean the rows
   * below had become tests of nothing, and the file should say so out loud instead of
   * quietly passing.
   */
  it("would otherwise let one variable preload code into every suite", () => {
    writeFileSync(pre, `console.log(${JSON.stringify(MARKER)});\n`);
    try {
      const withPoison = spawnSync(process.execPath, ["-e", "console.log('main ran')"], {
        encoding: "utf8",
        env: { PATH: process.env.PATH ?? "", HOME: process.env.HOME ?? "", BUN_OPTIONS: `--preload ${pre}` },
      });
      expect(withPoison.stdout ?? "").toContain(MARKER);
      expect(withPoison.stdout ?? "").toContain("main ran");

      const cleaned = spawnSync(process.execPath, ["-e", "console.log('main ran')"], {
        encoding: "utf8",
        env: gateEnv({ PATH: process.env.PATH ?? "", HOME: process.env.HOME ?? "", BUN_OPTIONS: `--preload ${pre}` }),
      });
      expect(cleaned.stdout ?? "").not.toContain(MARKER);
      expect(cleaned.stdout ?? "").toContain("main ran");
    } finally {
      cleanUp();
    }
  });

  /**
   * THE POSITIVE CONTROL ON THE MEASUREMENT ITSELF. Without it, "the trace holds one line"
   * could mean the gate is clean OR that the preload never ran at all, and those are
   * opposite conclusions. A deliberately leaking gate is written here and run the same
   * way; its child must appear in the trace.
   */
  it("catches a gate that does leak its environment", () => {
    writePreload();
    writeFileSync(leaky, `
      const { spawnSync } = require("node:child_process");
      spawnSync(process.execPath, ["-e", "0"], { stdio: "ignore" });
      console.log("leaky gate ran");
    `);
    try {
      const r = spawnSync(process.execPath, [leaky], { cwd: ROOT, encoding: "utf8", env: poison() });
      expect(`${r.stdout ?? ""}${r.stderr ?? ""}`, "the leaky gate did not run").toContain("leaky gate ran");
      // Its own process AND its child: two lines is the shape of a leak.
      expect(traced(), `the measurement cannot see a leak: ${traced().join(",")}`).toHaveLength(2);
    } finally {
      cleanUp();
    }
  }, 30_000);

  /**
   * AND THE REAL GATE. Its OWN process is preloaded, because it inherits the environment
   * that started it and nothing can change that, so the trace is COUNTED: exactly one line
   * is the gate itself, and a second line would be a child that inherited the poison.
   *
   * typecheck.ts is the gate used here because it spawns one child per config — five in
   * this repository — and the whole run costs 462 ms, measured. tests.ts could NOT be
   * used: it runs this very suite, so the row would recurse into itself.
   */
  it("passes nothing poisonous to any child it starts, measured by running it", () => {
    writePreload();
    try {
      const r = spawnSync(process.execPath, [join(ROOT, "tools/checks/typecheck.ts")], {
        cwd: ROOT, encoding: "utf8", env: poison(),
      });
      const out = `${r.stdout ?? ""}${r.stderr ?? ""}`;
      // THE GATE MUST HAVE ACTUALLY RUN ITS CHILDREN. "configs clean" alone was not
      // enough: typecheck.ts prints `0/5 configs clean` when every tsc spawn FAILS, so a
      // run in which no child ever started would leave one trace line and read as a pass.
      // The tally has to be N of N with N above zero, and the gate has to exit 0.
      expect(r.status, `the typecheck gate did not finish cleanly: ${out}`).toBe(0);
      const tally = /(\d+)\/(\d+) configs clean/.exec(out);
      expect(tally, `the typecheck gate printed no tally: ${out}`).not.toBeNull();
      expect(Number(tally?.[2] ?? "0"), "the gate must have had configs to check").toBeGreaterThan(0);
      expect(tally?.[1], `not every config was checked: ${out}`).toBe(tally?.[2]);
      const lines = traced();
      expect(lines, `the preload reached ${lines.length - 1} child process(es)`).toHaveLength(1);
      expect(lines[0], "the one trace line should be the gate's own process").toBe(String(r.pid));
    } finally {
      cleanUp();
    }
  }, 30_000);

  /**
   * AND THE GATE'S OWN PROCESS, which the fix above never reached (SEC-40). `runGate` cleans
   * what the gate STARTS; it cannot clean the gate, because a preload module runs before the
   * entry file and can replace what that file imports. Measured on bun 1.3.9: a preload that
   * swapped spawnSync made a gate's own `/bin/echo hello` return "faked" with /bin/echo never
   * running. So each script now goes through /bin/sh and `env -i` — a process that is not bun
   * — and the trace must come back EMPTY, because nothing in that chain is a bun that could
   * honour the variable.
   *
   * THE COMMAND IS READ FROM package.json, not written out here, so this row cannot keep
   * passing while the script quietly stops using the launcher.
   *
   * WHY IT DOES NOT DRIVE `bun run typecheck`, which is how the scan invokes it: measured,
   * `bun run <script>` with BUN_OPTIONS set prints its script list and exits 0 WITHOUT
   * running the script at all. That is a separate and larger hole — a check that reports a
   * pass having done nothing — and it lives in how the scan judges a check, not in this
   * repository's scripts. It is recorded in .nemesis/tasks/BG-001/gate-env-preload-measurement.md
   * rather than papered over here.
   */
  it("starts the gate itself with a clean environment, through the launcher the script names", () => {
    const script = (JSON.parse(readFileSync(join(ROOT, "package.json"), "utf8")) as
      { scripts?: Record<string, string> }).scripts?.typecheck ?? "";
    expect(script, "the typecheck script must go through the launcher").toContain("clean-env.sh");
    // Split on spaces, which is only safe because the line carries no quoting -- asserted,
    // so a future script with a quoted argument fails here instead of being mis-split.
    expect(script, "the script line must stay free of quoting for this row to split it").not.toMatch(/["']/);
    const argv = script.split(" ").filter((part) => part !== "");

    writePreload();
    try {
      const r = spawnSync(argv[0] ?? "", argv.slice(1), { cwd: ROOT, encoding: "utf8", env: poison() });
      const out = `${r.stdout ?? ""}${r.stderr ?? ""}`;
      expect(r.status, `the gate did not finish cleanly: ${out}`).toBe(0);
      const tally = /(\d+)\/(\d+) configs clean/.exec(out);
      expect(tally, `the gate printed no tally: ${out}`).not.toBeNull();
      expect(Number(tally?.[2] ?? "0"), "the gate must have had configs to check").toBeGreaterThan(0);
      expect(tally?.[1], `not every config was checked: ${out}`).toBe(tally?.[2]);

      const lines = traced();
      expect(lines, `the preload reached ${lines.length} process(es): ${lines.join(",")}`).toHaveLength(0);
    } finally {
      cleanUp();
    }
  }, 60_000);

  /**
   * THE SECONDARY LOCK, and labelled as such. It reads the source, so it cannot see
   * through `Bun` being a global; the row above is what covers that. What this adds is a
   * reason WHY, named at the line a future edit would change: the gates may import only
   * from a short list, and they start programs through one wrapper.
   */
  it("starts every program through the one wrapper that cleans the environment", () => {
    const stripped = (text: string): string =>
      text.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^[ \t]*\/\/.*$/gm, "");
    const ALLOWED_IMPORTS = ["node:fs", "node:path", "node:url", "./discover.ts", "./gate-env.ts"];
    const FORBIDDEN: [string, RegExp][] = [
      ["spawnSync", /(?<![.\w])spawnSync\s*\(/],
      ["spawn", /(?<![.\w])spawn\s*\(/],
      ["exec", /(?<![.\w])exec\s*\(/],
      ["execSync", /(?<![.\w])execSync\s*\(/],
      ["execFile", /(?<![.\w])execFile(Sync)?\s*\(/],
      ["fork", /(?<![.\w])fork\s*\(/],
      ["Bun.spawn", /Bun\s*\.\s*spawn/],
      ["Bun.$", /Bun\s*\.\s*\$/],
    ];

    for (const file of ["tests.ts", "typecheck.ts"]) {
      const src = readFileSync(join(ROOT, "tools/checks", file), "utf8");
      const code = stripped(src);
      expect(code, `${file} must run programs through runGate`).toContain("runGate(");
      for (const [name, pattern] of FORBIDDEN) {
        expect(pattern.test(code), `${file} must not start a program with ${name}`).toBe(false);
      }
      // IMPORTS READ BY A PARSER, NOT BY REGEX. Measured on every shape that defeated the
      // earlier text versions — single quotes, a renamed import, `import * as`, two
      // imports on one line, a multi-line import, a re-export, a require call and a
      // dynamic import written with a backtick — scanImports returns each with its
      // specifier. A specifier computed at run time is beyond any static check, which is
      // the reason the wrapper exists rather than only this row. The shebang is stripped
      // because scanImports refuses a file that starts with one.
      const found = new Bun.Transpiler({ loader: "ts" }).scanImports(src.replace(/^#![^\n]*\n/, ""));
      expect(found.length, `${file} should still import something`).toBeGreaterThan(0);
      for (const imported of found) {
        expect(ALLOWED_IMPORTS, `${file} may not import ${imported.path} (${imported.kind})`)
          .toContain(imported.path);
      }
    }

    // And the wrapper itself: ONE spawn, with the cleaned environment on it.
    const wrapper = stripped(readFileSync(join(ROOT, "tools/checks/gate-env.ts"), "utf8"));
    const calls = wrapper.split("spawnSync(").slice(1);
    expect(calls, "the wrapper must hold exactly one spawn").toHaveLength(1);
    expect(calls[0]?.slice(0, 400), "the wrapper's spawn must pass the cleaned environment").toContain("env: gateEnv()");
  });
});

/**
 * SEC-39, and it was found the hard way: a row in THIS file used a credential-shaped
 * literal as a fixture, and the repository-wide secret scan flagged it within seconds of
 * the edit landing. That scan is the real guard and it works. This row is a NARROWER copy
 * of the same rule, aimed only at the five files that define the quality gates, and it
 * exists for one reason — those files are the ones that decide whether the other checks
 * run at all, so a credential sitting in them would be read by whoever is debugging the
 * gate rather than by whoever is auditing the repository.
 *
 * It is deliberately short. A second full copy of the scanner's shape list would drift
 * from the original, which this project has already been bitten by; what is kept here is
 * the shape that actually occurred, plus a control that proves the check can still fire.
 */
describe("the files that define the gates carry no credential (SEC-39)", () => {
  // Assembled at run time, so no credential-shaped literal exists in this source either
  // (SEC-21): a scanner cannot tell a convincing fake from a real one, and a file that
  // trains its readers to ignore that alarm is worse than the fake itself.
  const SHAPES: { what: string; re: RegExp }[] = [
    // NOT `\b` AROUND THE NAME. In ANTHROPIC_API_KEY the character before API is an
    // underscore, which is a word character, so there is no word boundary there and the
    // pattern missed the very line SEC-39 was about. The control row below is what caught
    // that; a lookaround on letters and digits treats the underscore as the separator it is.
    { what: "a credential-shaped assignment", re: /(?<![A-Za-z0-9])(?:api[_-]?key|token|secret|password|credential)(?![A-Za-z0-9])\s*[:=]\s*["'`][^"'`\s]{8,}/i },
    { what: "an Anthropic key prefix", re: new RegExp(["sk", "ant"].join("-")) },
    { what: "a Doppler service token prefix", re: new RegExp(["dp", "st", ""].join("\\.")) },
  ];

  const gateFiles = (): string[] =>
    readdirSync(join(ROOT, "tools/checks")).filter((f) => f.endsWith(".ts")).map((f) => join(ROOT, "tools/checks", f));

  it("fires on the shape that actually occurred, so the row is not looking at nothing", () => {
    const fixture = `      BUN_INSPECT: "1", ${["ANTHROPIC", "API", "KEY"].join("_")}: "${"must-not-travel"}",`;
    expect(SHAPES.some((s) => s.re.test(fixture)), "the detector must catch the SEC-39 line").toBe(true);
    expect(SHAPES.some((s) => s.re.test('      BUN_INSPECT: "1", RANDOM_THING: "x",'))).toBe(false);
  });

  it("finds none in any of them", () => {
    const files = gateFiles();
    // A POSITIVE CONTROL ON THE FILE LIST: an empty sweep passes silently, which is how a
    // source-scanning guard usually dies.
    expect(files.length, "the gate folder should hold several files").toBeGreaterThan(3);
    expect(files.some((p) => p.endsWith("gate-env.ts"))).toBe(true);

    const offenders: string[] = [];
    for (const file of files) {
      for (const line of readFileSync(file, "utf8").split("\n")) {
        // A line that announces itself as an illustration is a comment ABOUT the shape.
        // Judged on the line's purpose, never on the match -- and the same deliberate hole
        // FUN-82 records for the skill's own sweep: a real credential on a line that also
        // says "example" passes. It is kept consistent with that sweep rather than quietly
        // different, and the repository-wide scan is what covers it.
        if (/example|placeholder|dummy|xxxx|a pattern like|assembled/i.test(line)) continue;
        for (const { what, re } of SHAPES) {
          if (re.test(line)) offenders.push(`${file.slice(ROOT.length + 1)}: ${what}`);
        }
      }
    }
    expect(offenders).toEqual([]);
  });
});

/**
 * FUN-86. The inventory used to skip every file under a NOT_OURS project by PATH, before
 * asking what runner the file was written for. Those entries exist because vitest suites
 * needing happy-dom, and vendored third-party library suites, cannot run in this checkout
 * — not because the directory is out of bounds. So a bun:test suite or a standalone script
 * added under one of those projects later would have been run by no gate and reported by
 * nobody, which is the one thing this inventory exists to prevent.
 *
 * The rows drive `accountFor` directly, which is why that policy was lifted out of the
 * loop: a row that ran the whole inventory would need real files in the tree, and this one
 * needs none. The runner is supplied rather than read, so each row says exactly which
 * combination it is about.
 */
describe("a suite under another project is skipped for its RUNNER, not its path (FUN-86)", () => {
  const VITEST_FILE = "apps/visual-composer/tests/parser/text.test.ts";
  const NEW_FILE = "apps/visual-composer/tests/parser/brand-new.test.ts";

  it("skips the vitest suites that genuinely cannot run here", () => {
    expect(accountFor(VITEST_FILE, "other")).toBeNull();
    expect(accountFor("Website Builder/spikes/substrate/x.spec.ts", "other")).toBeNull();
  });

  it("refuses to skip a bun:test or standalone suite added in the same place", () => {
    expect(accountFor(NEW_FILE, "bun"), "a bun:test suite there must be accounted for").toContain("UNACCOUNTED");
    expect(accountFor(NEW_FILE, "script"), "a standalone suite there must be accounted for").toContain("UNACCOUNTED");
  });

  /**
   * THE CONTROLS, so the rows above cannot pass by `accountFor` simply complaining about
   * everything: the suites this repository really does run must answer null.
   */
  it("accounts for the suites this repository runs, and flags one in a new place", () => {
    expect(accountFor(".claude/skills/acos-jason-breakglass/scripts/arm.test.ts", "bun")).toBeNull();
    expect(accountFor("tools/checks/checks.test.ts", "bun")).toBeNull();
    expect(accountFor("deps-audit.test.ts", "bun")).toBeNull();
    expect(accountFor(".claude/scripts/git-manager/stable-ids.test.ts", "script")).toBeNull();
    expect(accountFor("some/new/place/thing.test.ts", "bun")).toContain("UNACCOUNTED");
    expect(accountFor("some/new/place/thing.test.ts", "other")).toContain("UNACCOUNTED");
  });
});
