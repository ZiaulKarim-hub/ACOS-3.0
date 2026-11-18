/**
 * judge.test.ts — the environment a judge child is allowed to inherit.
 *
 * SEC-70/SEC-71. `spawnJudgeSync` built the child env as `{ ...process.env, ... }` and
 * stripped only `ANTHROPIC_API_KEY` and `NEMESIS_JUDGE_STUB`. A PreToolUse hook runs inside
 * the user's own window, so a window armed on the borrowed account handed the judge child
 * `CLAUDE_CONFIG_DIR=~/.claude-jason` AND `CLAUDE_CODE_OAUTH_TOKEN` — Jason's live
 * credential — with no arm record, no window binding and no meter reading. Same harm as
 * SEC-63, arriving by inheritance rather than by an explicit switch, and BG-001 forbids
 * both: daemons "may never touch Jason at all, armed or not".
 *
 * The variable names below were READ OUT OF THE DOOR, not guessed:
 * `~/.claude-account/bin/launch-jason` exports `CLAUDE_CONFIG_DIR`, `CLAUDE_ACCOUNT=jason`
 * and `CLAUDE_CODE_OAUTH_TOKEN`. Counting the account-selection names used across this
 * machine's tooling on 2026-11-18 also found `CLAUDE_ACCOUNT_NO_PROMPT` and
 * `CLAUDE_SECURESTORAGE_CONFIG_DIR`, the latter selecting the KEYCHAIN ENTRY — so stripping
 * the config dir alone would have left a second door to the same credentials.
 */
import { describe, expect, it } from "bun:test";
import { ACCOUNT_SELECTING_ENV, CREDENTIAL_ENV, judgeChildEnv } from "./judge.ts";

/** Every account or credential variable measured on this machine, plus one invented sibling. */
const MUST_NOT_SURVIVE = [
  "CLAUDE_CONFIG_DIR",
  "CLAUDE_ACCOUNT",
  "CLAUDE_ACCOUNT_NO_PROMPT",
  "CLAUDE_SECURESTORAGE_CONFIG_DIR",
  "CLAUDE_CODE_OAUTH_TOKEN",
  "CLAUDE_OAUTH_TOKEN",
  "CLAUDE_JASON_CFG",
  "ANTHROPIC_API_KEY",
  "ANTHROPIC_AUTH_TOKEN",
  "NEMESIS_JUDGE_STUB",
  // A name nobody has created yet. The scrub is a shape for exactly this reason: a fixed
  // list of four names is how the OAuth token stayed in the environment the first time.
  "CLAUDE_FUTURE_ACCOUNT_SELECTOR",
];

/** What the child genuinely needs. Stripping these would stop the judge starting at all. */
const MUST_SURVIVE = ["PATH", "HOME", "TMPDIR", "LANG", "CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_MESSAGING_TOKEN"];

const base = (): NodeJS.ProcessEnv => {
  const e: NodeJS.ProcessEnv = {};
  for (const k of MUST_SURVIVE) e[k] = `keep-${k}`;
  for (const k of MUST_NOT_SURVIVE) e[k] = `drop-${k}`;
  return e;
};

describe("a judge child never inherits an account or a credential (SEC-70)", () => {
  it("drops every account and credential variable that arrives from the PARENT", () => {
    const env = judgeChildEnv(base(), {}, "tok");
    for (const k of MUST_NOT_SURVIVE) expect(env[k]).toBeUndefined();
  });

  it("drops them even when a CALLER supplies them through extraEnv", () => {
    // The merge order is the point: extraEnv is spread BEFORE the strip, so a caller cannot
    // smuggle an account back in. The choke point enforces the rule; callers are not trusted.
    const extra: Record<string, string> = {};
    for (const k of MUST_NOT_SURVIVE) extra[k] = `smuggled-${k}`;
    const env = judgeChildEnv({}, extra, "tok");
    for (const k of MUST_NOT_SURVIVE) expect(env[k]).toBeUndefined();
  });

  it("keeps what the child needs to start, so the gate does not stop running", () => {
    const env = judgeChildEnv(base(), {}, "tok");
    for (const k of MUST_SURVIVE) expect(env[k]).toBe(`keep-${k}`);
  });

  it("still passes the judge token, which the child is identified by", () => {
    expect(judgeChildEnv(base(), {}, "tok-123").ACOS_NEMESIS_JUDGE).toBe("tok-123");
    // And a caller cannot overwrite it through extraEnv, or the child loses its identity.
    expect(judgeChildEnv({}, { ACOS_NEMESIS_JUDGE: "forged" }, "tok-123").ACOS_NEMESIS_JUDGE).toBe("tok-123");
  });

  it("does NOT strip the messaging token, which a blanket /TOKEN/ match would have", () => {
    // Measured on the running daemon (pid 11065): CLAUDE_CODE_MESSAGING_TOKEN is a live
    // Claude Code internal. The wider net was considered and refused for this reason, so the
    // refusal is pinned here rather than left as a comment someone later "tidies".
    expect(CREDENTIAL_ENV.test("CLAUDE_CODE_MESSAGING_TOKEN")).toBe(false);
    expect(ACCOUNT_SELECTING_ENV.test("CLAUDE_CODE_MESSAGING_TOKEN")).toBe(false);
    expect(judgeChildEnv({ CLAUDE_CODE_MESSAGING_TOKEN: "m" }, {}, "t").CLAUDE_CODE_MESSAGING_TOKEN).toBe("m");
  });

  it("recognises the credential the Jason door actually exports", () => {
    // Read from ~/.claude-account/bin/launch-jason, which exports exactly these three.
    expect(CREDENTIAL_ENV.test("CLAUDE_CODE_OAUTH_TOKEN")).toBe(true);
    expect(ACCOUNT_SELECTING_ENV.test("CLAUDE_CONFIG_DIR")).toBe(true);
    expect(ACCOUNT_SELECTING_ENV.test("CLAUDE_ACCOUNT")).toBe(true);
  });
});
