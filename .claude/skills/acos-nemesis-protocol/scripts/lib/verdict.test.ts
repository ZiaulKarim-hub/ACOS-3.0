/**
 * verdict.test.ts — the recovery plans, and the one route out of them that must stay shut.
 *
 * SEC-63. A judge that hit a usage limit or an auth error used to re-run its child with
 * `CLAUDE_CONFIG_DIR=$NEMESIS_ALT_CONFIG_DIR`: no arm record, no window, no meter reading.
 * An unattended daemon therefore reached for a second account at exactly the moment the
 * first was exhausted — the measured 2026-11-16 drain, a borrowed config dir inherited by
 * automation nobody was watching. BG-001's actor table is flat: daemons "may never touch
 * Jason at all, armed or not".
 *
 * The step was REMOVED rather than guarded, because a guard needs an allow-list and there is
 * nothing to allow: the accounts on this machine are `.claude`, `.claude-account`,
 * `.claude-jason` and `.claude-personal`, and the only one a judge would switch TO is the
 * borrowed one. The rows below are a tripwire on that removal — three executors honoured the
 * step (`judgeWithRecovery`, `requestGeneric`, `nemesis-daemon`), so deleting one and leaving
 * two was a live possibility and did in fact happen once during this repair.
 */
import { describe, expect, it } from "bun:test";
import * as fs from "node:fs";
import * as path from "node:path";
import { recoveryPlan, type FailureClass } from "./verdict.ts";

/** Every class `classifyFailure` can return, so no plan escapes the sweep below. */
const ALL_CLASSES: FailureClass[] = ["empty", "crash", "usage_limit", "too_long", "prose", "malformed", "auth"];

const SCRIPTS = path.dirname(import.meta.dir);

/** The actions that retry the SAME account. Anything else would change who is paying. */
const SAME_ACCOUNT_RETRIES = ["wait_then_retry", "retry_backoff", "retry_direct"];

/**
 * Phrases that could only be an OFFER of another account.
 *
 * Narrow on purpose. A first version forbade the words "another account", which matched the
 * auth plan's own denial note — "the caller denies rather than borrowing another account
 * (SEC-63)" — so the test failed against correct code. A tripwire that fires on the
 * explanation of the fix is worse than no tripwire: it gets deleted.
 */
const OFFERS_ANOTHER_ACCOUNT = /alternate[_ ]account|alternate Claude|switch (to )?(another|a second) account/i;

/**
 * Any WRITE of the config-dir key into something, in any syntax.
 *
 * The harm is handing a child a different account, not one particular spelling. A first
 * version matched only `CLAUDE_CONFIG_DIR:`, the shape the removed code happened to use, so
 * `env.CLAUDE_CONFIG_DIR = alt` and `env["CLAUDE_CONFIG_DIR"] = alt` would both have passed
 * as clean under a row whose name promised "never". Verified 2026-11-18 against eight
 * spellings: it catches the object key, the quoted key, the dotted assignment, the bracket
 * assignment and a spread-into-env, and it lets a `===` comparison, a bare string in a Set
 * and a log line through — which matters, because `selftest.ts` legitimately names the key
 * inside a Set.
 */
const WRITES_CONFIG_DIR = /CLAUDE_CONFIG_DIR["'`\]]*\s*(:|=(?!=))/;

/**
 * `src` with comments removed, strings and code intact.
 *
 * `Bun.Transpiler` rather than a regex, and the reason is a measured hole. Stripping block
 * comments with a lazy `/* … *\/` regex also fires inside an ordinary string: a glob of two
 * stars followed by `/*.ts` contains a comment terminator, so the regex eats everything from
 * the previous comment opener up to it and can blind the tripwire to real code that follows.
 * Verified 2026-11-18 that the transpiler drops a line comment and a block comment while
 * keeping `process.env.X`, an env-key write and that glob string exactly.
 *
 * A file that cannot be transpiled is returned RAW, which can only over-report. Over-
 * reporting is the safe direction: it asks a person to look.
 */
export function codeWithoutComments(src: string): string {
  try {
    return new Bun.Transpiler({ loader: "ts" }).transformSync(src);
  } catch {
    return src;
  }
}

/** Every .ts file under scripts/, so a re-add anywhere is caught, not just where it left. */
function sourceFiles(dir: string, out: string[] = []): string[] {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name === "node_modules" || e.name.startsWith(".")) continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) sourceFiles(p, out);
    else if (e.name.endsWith(".ts")) out.push(p);
  }
  return out;
}

/** This file names both forbidden tokens in order to forbid them, so it exempts itself. */
const swept = (): string[] => sourceFiles(SCRIPTS).filter((f) => path.basename(f) !== "verdict.test.ts");

describe("no recovery plan can switch Claude accounts (SEC-63)", () => {
  it("covers every failure class, so nothing slips through an unswept case", () => {
    // If `classifyFailure` gains a class, this row fails before the sweep can pass vacuously.
    for (const c of ALL_CLASSES) expect(recoveryPlan(c).length).toBeGreaterThan(0);
    expect(ALL_CLASSES.length).toBe(7);
  });

  it("emits no account-switching step for ANY failure class", () => {
    for (const c of ALL_CLASSES) {
      const steps = recoveryPlan(c);
      expect(steps.map((s) => s.action)).not.toContain("alternate_account");
      // And nothing renamed it: no step's action or note offers another config dir.
      for (const s of steps) expect(`${s.action} ${s.note}`).not.toMatch(OFFERS_ANOTHER_ACCOUNT);
    }
  });

  it("answers a usage limit with a bounded wait, which is the replacement", () => {
    const actions = recoveryPlan("usage_limit").map((s) => s.action);
    // It waits and retries. What it must NOT do is find more quota somewhere else.
    expect(actions).toContain("wait_then_retry");
    for (const a of actions) expect(SAME_ACCOUNT_RETRIES).toContain(a);
  });

  it("answers an auth error with a retry, not with a different login", () => {
    const actions = recoveryPlan("auth").map((s) => s.action);
    expect(actions.length).toBeGreaterThan(0);
    for (const a of actions) expect(SAME_ACCOUNT_RETRIES).toContain(a);
  });
});

describe("the source-level tripwire can actually see (SEC-63)", () => {
  /**
   * The detector is tested BEFORE it is trusted. A sweep that silently matches nothing
   * reports a clean codebase, which is the same output as a clean codebase — so the only way
   * to tell them apart is to plant something and watch it get caught.
   */
  it("ignores a mention that lives in a comment", () => {
    const code = codeWithoutComments('// NEMESIS_ALT_CONFIG_DIR\n/* CLAUDE_CONFIG_DIR: x */\nconst a = 1;\n');
    expect(/NEMESIS_ALT_CONFIG_DIR/.test(code)).toBe(false);
    expect(WRITES_CONFIG_DIR.test(code)).toBe(false);
  });

  it("catches an env-var read that lives in code", () => {
    expect(/NEMESIS_ALT_CONFIG_DIR/.test(codeWithoutComments("const x = process.env.NEMESIS_ALT_CONFIG_DIR;\n"))).toBe(true);
  });

  it("catches EVERY syntax that writes the config dir, not just the one that was removed", () => {
    const writes = [
      'const y = { CLAUDE_CONFIG_DIR: "/tmp" };',            // the object key the old code used
      "env.CLAUDE_CONFIG_DIR = alt;",                          // a dotted assignment
      'env["CLAUDE_CONFIG_DIR"] = alt;',                       // a bracket assignment
      'const o = { "CLAUDE_CONFIG_DIR": alt };',               // a quoted key
      "spawn(c, { env: { ...process.env, CLAUDE_CONFIG_DIR: d } });", // spread into a child env
    ];
    for (const w of writes) expect(WRITES_CONFIG_DIR.test(codeWithoutComments(`${w}\n`))).toBe(true);
  });

  it("does NOT fire on merely naming the key, or the sweep becomes noise", () => {
    // selftest.ts legitimately lists the key in a Set of allowed env names. A tripwire that
    // fires on that gets a blanket exemption added, and then it protects nothing.
    const harmless = [
      'if (e === "CLAUDE_CONFIG_DIR") skip();',
      'const allowed = new Set(["HOME", "CLAUDE_CONFIG_DIR"]);',
      'log("CLAUDE_CONFIG_DIR");',
    ];
    for (const h of harmless) expect(WRITES_CONFIG_DIR.test(codeWithoutComments(`${h}\n`))).toBe(false);
  });

  it("is NOT blinded by a glob string containing a comment terminator", () => {
    // The measured hole in the regex version: a two-star glob followed by `/*.ts` holds a
    // comment terminator. If this row ever fails, the sweep below is reporting "clean"
    // because it cannot see, not because the codebase is clean.
    const planted = 'const glob = "**/*.ts";\nconst x = process.env.NEMESIS_ALT_CONFIG_DIR;\nconst y = { CLAUDE_CONFIG_DIR: "/tmp" };\n';
    const code = codeWithoutComments(planted);
    expect(/NEMESIS_ALT_CONFIG_DIR/.test(code)).toBe(true);
    expect(WRITES_CONFIG_DIR.test(code)).toBe(true);
  });

  it("sweeps a real number of files, so an empty sweep cannot pass as a clean one", () => {
    expect(swept().length).toBeGreaterThan(20);
  });
});

describe("no source file can reach another account (SEC-63)", () => {
  /**
   * A SOURCE-LEVEL assertion, deliberately, and the reason is measured. The first attempt at
   * this repair deleted ONE of the three executors; typecheck passed, every behavioural test
   * passed, and the account switch was still live in the other two. A plan-level test cannot
   * see that. Reading the files can.
   */
  it("reads NEMESIS_ALT_CONFIG_DIR nowhere in code", () => {
    const offenders = swept().filter((f) => /NEMESIS_ALT_CONFIG_DIR/.test(codeWithoutComments(fs.readFileSync(f, "utf8"))));
    expect(offenders.map((f) => path.relative(SCRIPTS, f))).toEqual([]);
  });

  it("never hands a judge child a CLAUDE_CONFIG_DIR of its own", () => {
    const offenders = swept().filter((f) => WRITES_CONFIG_DIR.test(codeWithoutComments(fs.readFileSync(f, "utf8"))));
    expect(offenders.map((f) => path.relative(SCRIPTS, f))).toEqual([]);
  });

  it("still names the borrowed account somewhere, so the rule is written down", () => {
    // Belt and braces against a tidy-up that deletes the explanation along with the code: if
    // nothing records WHY there is no fallback account, the next reader adds one back.
    const verdict = fs.readFileSync(path.join(SCRIPTS, "lib", "verdict.ts"), "utf8");
    expect(verdict).toContain("SEC-63");
    expect(verdict).toMatch(/DELIBERATELY ABSENT|never touch Jason/);
  });
});
