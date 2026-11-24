/**
 * WHICH ACCOUNT THE ORACLE'S JUDGE SPENDS.
 *
 * The Oracle judges by running Claude Code, and two of its four reach-layers run
 * inside the window that made the tool call: the DIRECT judge, and the AUTO-START
 * that launches the daemon. Both used to inherit that window's environment whole
 * and strip only `ANTHROPIC_API_KEY`. In a borrowed-account window that
 * environment carries the account-selecting variables and the live OAuth
 * credential the account door exports, so the judge spent the BORROWED allowance
 * — with no arm record, no window key, no ceiling and no audit line. The
 * auto-start case is the worse of the two, because the daemon it leaves behind is
 * detached and outlives the window.
 *
 * These rows are the guard. There are two implementations because there are two
 * layers (TypeScript in the daemon, Python in the hook) and neither trusts the
 * other, so both are checked here side by side — a fix to one that misses the
 * other is the exact failure this file exists to catch.
 */
import { describe, expect, it } from "bun:test";
import { spawnSync } from "node:child_process";
import { join } from "node:path";
import { ACCOUNT_SELECTING_ENV, CREDENTIAL_ENV, altConfigDir, judgingEnv } from "./oracle-daemon.ts";

const HOOK_DIR = join(import.meta.dir, "..");

/** What a borrowed-account window really exports, read out of the account door. */
const BORROWED_WINDOW = {
  CLAUDE_CONFIG_DIR: "/Users/zee/.claude-jason",
  CLAUDE_ACCOUNT: "jason",
  CLAUDE_ACCOUNT_NO_PROMPT: "1",
  // Deliberately NOT shaped like a real credential: this repo is public, and a
  // realistic prefix in a test fixture reads as a leak to every scanner and human
  // who meets it. The rows only check that the KEY is gone, never its value.
  CLAUDE_CODE_OAUTH_TOKEN: "placeholder-never-a-real-token",
};

/** Things a judge child legitimately needs, which the strip must leave alone. */
const KEEP = {
  HOME: "/Users/zee",
  PATH: "/usr/bin:/bin",
  ORACLE_CLAUDE_BIN: "/opt/homebrew/bin/claude",
  CLAUDE_CODE_MESSAGING_TOKEN: "an internal the CLI needs; a blanket /TOKEN/ would eat it",
};

describe("judgingEnv — the daemon's side", () => {
  it("strips every account-selecting and credential variable a borrowed window carries", () => {
    const env = judgingEnv({ ...KEEP, ...BORROWED_WINDOW });
    for (const k of Object.keys(BORROWED_WINDOW)) expect(env[k]).toBeUndefined();
  });

  it("keeps the binary pin, HOME, PATH and the CLI's own messaging token", () => {
    const env = judgingEnv({ ...KEEP, ...BORROWED_WINDOW });
    for (const [k, v] of Object.entries(KEEP)) expect(env[k]).toBe(v);
  });

  it("strips what it INHERITED but still honours a deliberate pin passed by a caller", () => {
    // A recovery step that reports success while silently doing nothing is worse
    // than no recovery step, so `extraEnv` is applied after the strip.
    const env = judgingEnv({ ...BORROWED_WINDOW }, { CLAUDE_CONFIG_DIR: "/Users/zee/.claude-personal" });
    expect(env.CLAUDE_CONFIG_DIR).toBe("/Users/zee/.claude-personal");
    expect(env.CLAUDE_CODE_OAUTH_TOKEN).toBeUndefined();
    expect(env.CLAUDE_ACCOUNT).toBeUndefined();
  });

  it("matches by shape, so a sibling nobody has invented yet is covered too", () => {
    for (const k of ["CLAUDE_SOMETHING_ACCOUNT", "CLAUDE_NEW_CONFIG_DIR_2", "CLAUDE_JASON_WHATEVER"]) {
      expect(ACCOUNT_SELECTING_ENV.test(k)).toBe(true);
    }
    for (const k of ["CLAUDE_OAUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"]) {
      expect(CREDENTIAL_ENV.test(k)).toBe(true);
    }
    expect(ACCOUNT_SELECTING_ENV.test("ORACLE_CLAUDE_BIN")).toBe(false);
    expect(CREDENTIAL_ENV.test("CLAUDE_CODE_MESSAGING_TOKEN")).toBe(false);
  });
});

describe("altConfigDir — the fallback account", () => {
  it("is unusable when unset, and says the absence is deliberate", () => {
    const a = altConfigDir({});
    expect(a.usable).toBe(false);
    expect(a.why).toContain("2026-11-16");
  });

  it("REFUSES the borrowed folder by shape rather than merely being unset", () => {
    for (const dir of ["/Users/zee/.claude-jason", "/Users/zee/.CLAUDE-Jason", "/tmp/jason-config"]) {
      const a = altConfigDir({ ORACLE_ALT_CONFIG_DIR: dir });
      expect(a.usable).toBe(false);
      expect(a.why).toContain("breakglass");
    }
  });

  it("accepts a folder that is not the borrowed one", () => {
    const a = altConfigDir({ ORACLE_ALT_CONFIG_DIR: "/Users/zee/.claude-personal" });
    expect(a.usable).toBe(true);
    expect(a.dir).toBe("/Users/zee/.claude-personal");
  });
});

/** Run one expression against the hook module and return its printed result. */
function py(expr: string): string {
  const r = spawnSync("python3", ["-c", `import sys; sys.path.insert(0, ${JSON.stringify(HOOK_DIR)})\nimport _oracle_judge as j\nprint(${expr})`], {
    encoding: "utf8",
    env: { PATH: process.env.PATH ?? "/usr/bin:/bin", HOME: process.env.HOME ?? "/Users/zee" },
  });
  if (r.status !== 0) throw new Error(`python3 exited ${r.status}: ${r.stderr}`);
  return r.stdout.trim();
}

describe("judging_env — the hook's side, which is the one inside the window", () => {
  const base = JSON.stringify({ ...KEEP, ...BORROWED_WINDOW });

  it("strips every account-selecting and credential variable", () => {
    const out = py(`sorted(k for k in j.judging_env(__import__("json").loads(${JSON.stringify(base)})) if k.startswith(("CLAUDE_","ANTHROPIC_")))`);
    expect(out).toBe("['CLAUDE_CODE_MESSAGING_TOKEN']");
  });

  it("keeps the binary pin, HOME and PATH", () => {
    expect(py(`[j.judging_env(__import__("json").loads(${JSON.stringify(base)})).get(k) for k in ("HOME","PATH","ORACLE_CLAUDE_BIN")]`))
      .toBe(`['/Users/zee', '/usr/bin:/bin', '/opt/homebrew/bin/claude']`);
  });

  it("strips the alternate-account switch, so a hook-started daemon cannot be handed it", () => {
    expect(py(`"ORACLE_ALT_CONFIG_DIR" in j.judging_env({"ORACLE_ALT_CONFIG_DIR": "/Users/zee/.claude-jason"})`)).toBe("False");
  });

  it("reads the live environment when given no argument", () => {
    // The default argument is the whole point: `_ask_direct` and `_start_daemon`
    // call it with nothing, inside the window.
    expect(py(`("HOME" in j.judging_env(), "CLAUDE_CONFIG_DIR" in j.judging_env())`)).toBe("(True, False)");
  });
});

describe("both reach-layers actually USE the strip", () => {
  const src = Bun.file(join(HOOK_DIR, "_oracle_judge.py"));

  it("the direct judge builds its environment with judging_env, not a bare copy", async () => {
    const text = await src.text();
    const direct = text.slice(text.indexOf("def _ask_direct"), text.indexOf("def parse_verdict"));
    expect(direct).toContain("judging_env()");
    expect(direct).not.toContain("dict(os.environ)");
  });

  it("the auto-started daemon is given a stripped environment, not an inherited one", async () => {
    const text = await src.text();
    const start = text.slice(text.indexOf("def _start_daemon"), text.indexOf("def classify_failure"));
    expect(start).toContain("env=judging_env()");
  });
});
