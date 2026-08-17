#!/usr/bin/env bun
/**
 * The Oracle — a real AI sitting at the permission door.
 *
 * WHAT THIS REPLACES. The old Oracle scored a tool call 0-10 with regexes and
 * stopped to ask Zee whenever the score beat his threshold. Threshold 11 (YOLO)
 * skipped the asking entirely and allowed everything blind. This daemon is the
 * rung above: nothing is blind, and Zee is still never asked. Opus reads the
 * command IN CONTEXT and answers.
 *
 * THE BAR IS HARM, NOT NEED (Zee, 2026-08-15). "Just because an operation is
 * outside the work directory doesn't automatically mean it is harmful, it could
 * still be necessary, touching keys or credentials could be necessary too. If I
 * have to decide what is harmful then what is the point of having an intelligent
 * AI watching over?" So there is NO hardcoded deny-list here, on purpose. The
 * judgement is the product. A rule list would just be the old Oracle wearing a
 * new name.
 *
 * WHY A DAEMON AND NOT A ONE-SHOT. The hook must not pay process startup on every
 * call, the audit trail wants one owner, and Zee asked for a long-running program
 * rather than a tab to babysit. `--follow` gives him the tab view when he wants
 * to watch it think.
 *
 * SUBSCRIPTION, NEVER AN API KEY (standing rule). Judging runs through the
 * Claude Code CLI in headless mode, which uses the logged-in subscription.
 * ANTHROPIC_API_KEY is explicitly stripped from the child environment.
 *
 * Bun + TypeScript, zero deps (project language default: TS/Rust over Python).
 */

import { existsSync, mkdirSync, appendFileSync, writeFileSync, readFileSync, chmodSync, unlinkSync } from "node:fs";
import { join } from "node:path";
import { homedir } from "node:os";
import { randomBytes } from "node:crypto";

const ORACLE_HOME = join(homedir(), ".acos", "oracle");
const SOCK = join(ORACLE_HOME, "oracle.sock");
const TOKEN_FILE = join(ORACLE_HOME, "token");
const LOG = join(ORACLE_HOME, "verdicts.log");
const PID_FILE = join(ORACLE_HOME, "oracle.pid");

/**
 * The Claude Code binary, resolved to a REAL path.
 *
 * `claude` in an interactive shell is a zsh function wrapping `_acos_cli`, which
 * does not exist in a non-interactive shell — calling it there dies with
 * "command not found: _acos_cli". The daemon must therefore never rely on the
 * name alone.
 */
const CLAUDE_CANDIDATES = [
  "/opt/homebrew/bin/claude",
  join(homedir(), ".claude", "local", "claude"),
  "/usr/local/bin/claude",
];

function claudeBin(): string {
  for (const c of CLAUDE_CANDIDATES) if (existsSync(c)) return c;
  throw new Error(`no claude binary found; looked in: ${CLAUDE_CANDIDATES.join(", ")}`);
}

// ---------------------------------------------------------------------------
// The charter — what the Oracle is asked, every time
// ---------------------------------------------------------------------------

/**
 * Deliberately short. A long charter turns into a rule list, and a rule list is
 * the thing this design rejects. It states the bar, the default, and the output
 * shape, then gets out of the way.
 */
function buildPrompt(req: JudgeRequest): string {
  const input = JSON.stringify(req.tool_input ?? {}, null, 1).slice(0, 4000);
  // THE GOAL IS EVIDENCE, NOT A GATE. Zee asked for a stated goal on Oracle mode
  // (2026-08-16). It sharpens the judgement — the live test caught `rm -rf
  // ~/Documents` only because the stated task was "clean temp files in the build
  // folder", and the mismatch is what exposed the harm. But it must never become
  // an "is this on-task?" test, which is the bar he explicitly rejected. Kept
  // word-for-word in step with _oracle_judge.build_charter: if the two drifted,
  // the verdict would depend on which layer happened to serve the request.
  const goalBlock = req.goal
    ? `\n--- THE SESSION'S STATED GOAL ---\n${req.goal.slice(0, 1500)}\n` +
      `Use this as EVIDENCE, not as a test. A command that is off-topic but harmless is ` +
      `still ALLOW — wandering is not damage. What the goal buys you is the mismatch case: ` +
      `when a command would destroy something and the stated work does not explain why ` +
      `anyone would want that destroyed, the gap itself is the warning.\n`
    : "";
  return `You are THE ORACLE. You hold the permission door for Zee's machine, and he is not going to be asked. Your answer is final and it executes.

Zee's standing instruction, verbatim:
"give permission to everything unless it is truly going to cause harm to my system"
"just because an operation is outside the work directory doesn't automatically mean it is harmful, it could still be necessary, touching keys or credentials could be necessary too"

SO YOUR DEFAULT IS ALLOW. Deleting files, force pushes, editing config, writing outside the project, reading credentials, installing packages — these are ordinary work. None of them is a reason to deny on its own. He has run everything wide open for a long time and it has never hurt him.

DENY only when the command would do REAL, LASTING damage to his computer or his data, and the surrounding work does not explain why that damage would be wanted. Ask yourself the honest question: if this runs and it was a mistake, can it be undone? If yes, allow.

You may investigate before answering. Read files, inspect the repo, check what a path actually is. Take as long as you need — Zee explicitly chose correctness over speed. But do not act on the world: read only, change nothing.

Two failure modes, and they are NOT equal.
- Denying something ordinary makes the system useless and breaks the promise it is built on. This is the common failure and the one to fear.
- Allowing genuine destruction is rarer but unrecoverable.
Weigh accordingly: lean hard toward allow, and reserve deny for the case you could defend to him afterwards in one sentence.

${goalBlock}
--- THE REQUEST ---
tool: ${req.tool_name}
cwd: ${req.cwd}
input: ${input}

--- RECENT CONVERSATION (what this is for) ---
${req.context?.slice(0, 6000) || "(none supplied)"}

--- YOUR ANSWER ---
Reply with ONE line of JSON and nothing else:
{"decision":"allow","reason":"<short>"}
or
{"decision":"deny","reason":"<the one sentence you would defend to Zee>"}`;
}

// ---------------------------------------------------------------------------

interface JudgeRequest {
  tool_name: string;
  tool_input: Record<string, unknown>;
  cwd: string;
  context?: string;
  /** The session's stated goal — evidence about harm, never an on-task test. */
  goal?: string;
}

interface Verdict {
  decision: "allow" | "deny";
  reason: string;
  elapsed_ms: number;
  model: string;
  /** True when the judge could not be reached and the fallback allowed it. */
  fallback?: boolean;
}

function ensureHome(): void {
  if (!existsSync(ORACLE_HOME)) mkdirSync(ORACLE_HOME, { recursive: true, mode: 0o700 });
}

/**
 * The recursion token.
 *
 * The Oracle judges by running Claude Code, and that child session loads the same
 * PreToolUse hook. Without a guard the child's first Read would ask the Oracle,
 * which would spawn another child, forever. The child therefore carries a secret
 * the hook recognises.
 *
 * A bare env-var flag would be weaker than what it replaces: anything able to set
 * an env var could then wave every check through. Requiring the value to MATCH a
 * 0600 file the daemon owns keeps the escape hatch closed to everyone else — the
 * same reasoning that removed the old ORACLE_THRESHOLD env var (security: H3).
 */
function ensureToken(): string {
  ensureHome();
  try {
    const existing = readFileSync(TOKEN_FILE, "utf8").trim();
    if (existing) return existing;
  } catch {
    /* absent or unreadable — mint a fresh one below */
  }
  const token = randomBytes(32).toString("hex");
  writeFileSync(TOKEN_FILE, token + "\n", { mode: 0o600 });
  chmodSync(TOKEN_FILE, 0o600);
  return token;
}

function logVerdict(req: JudgeRequest, v: Verdict): void {
  ensureHome();
  const line = JSON.stringify({
    ts: new Date().toISOString(),
    tool: req.tool_name,
    cwd: req.cwd,
    detail: String((req.tool_input as { command?: string })?.command ?? "").slice(0, 300)
      || String((req.tool_input as { file_path?: string })?.file_path ?? "").slice(0, 300),
    decision: v.decision,
    reason: v.reason,
    elapsed_ms: v.elapsed_ms,
    fallback: v.fallback ?? false,
  });
  appendFileSync(LOG, line + "\n", { encoding: "utf8" });
}

/** Pull the verdict JSON out of the model's reply, wherever it sits. */
export function parseVerdict(raw: string): { decision: "allow" | "deny"; reason: string } | null {
  const text = (raw ?? "").trim();
  if (!text) return null;
  // Last JSON object wins: a thinking-aloud reply ends with its answer.
  const matches = [...text.matchAll(/\{[^{}]*"decision"\s*:\s*"(allow|deny)"[^{}]*\}/g)];
  const chosen = matches.length ? matches[matches.length - 1]![0] : null;
  if (chosen) {
    try {
      const o = JSON.parse(chosen) as { decision: string; reason?: string };
      if (o.decision === "allow" || o.decision === "deny") {
        return { decision: o.decision, reason: String(o.reason ?? "").slice(0, 500) };
      }
    } catch {
      /* fall through */
    }
  }
  return null;
}

async function judge(req: JudgeRequest, token: string, model: string): Promise<Verdict> {
  const started = Date.now();
  // NO TIMEOUT — Zee, 2026-08-15: "Think as long as needed." A slow verdict is
  // a stuck tool call, which he accepted; a rushed verdict is a wrong one.
  try {
    const proc = Bun.spawn([claudeBin(), "-p", buildPrompt(req), "--model", model], {
      stdout: "pipe",
      stderr: "pipe",
      env: {
        ...process.env,
        // The child IS the Oracle. Without this it would ask itself, forever.
        ACOS_ORACLE_JUDGE: token,
        // Standing rule: subscription only, never an API key.
        ANTHROPIC_API_KEY: undefined as unknown as string,
      },
    });
    const out = await new Response(proc.stdout).text();
    await proc.exited;
    const parsed = parseVerdict(out);
    if (!parsed) {
      // Unreadable answer is NOT a denial. Falling back to deny would make every
      // parser hiccup look like the Oracle refusing ordinary work, which is the
      // failure mode Zee cares most about avoiding.
      return {
        decision: "allow",
        reason: "oracle reply unparseable — allowed (fallback is YOLO, which is where this started)",
        elapsed_ms: Date.now() - started,
        model,
        fallback: true,
      };
    }
    return { ...parsed, elapsed_ms: Date.now() - started, model };
  } catch (e) {
    return {
      decision: "allow",
      reason: `oracle unreachable (${String(e).slice(0, 120)}) — allowed`,
      elapsed_ms: Date.now() - started,
      model,
      fallback: true,
    };
  }
}

// ---------------------------------------------------------------------------
// Server
// ---------------------------------------------------------------------------

async function serve(model: string): Promise<void> {
  ensureHome();
  const token = ensureToken();
  if (existsSync(SOCK)) {
    try {
      unlinkSync(SOCK);
    } catch {
      /* a stale socket file is not fatal */
    }
  }
  writeFileSync(PID_FILE, String(process.pid) + "\n", { mode: 0o600 });

  Bun.listen({
    unix: SOCK,
    socket: {
      data: async (socket, data) => {
        let req: JudgeRequest;
        try {
          req = JSON.parse(new TextDecoder().decode(data)) as JudgeRequest;
        } catch {
          socket.write(JSON.stringify({ decision: "allow", reason: "bad request — allowed" }) + "\n");
          socket.end();
          return;
        }
        const v = await judge(req, token, model);
        logVerdict(req, v);
        const mark = v.decision === "deny" ? "DENY " : "allow";
        console.log(
          `[${new Date().toISOString()}] ${mark} ${req.tool_name} (${v.elapsed_ms}ms)` +
            `${v.fallback ? " [fallback]" : ""}\n    ${v.reason}`,
        );
        socket.write(JSON.stringify(v) + "\n");
        socket.end();
      },
    },
  });

  chmodSync(SOCK, 0o600);
  console.log(`The Oracle is awake.`);
  console.log(`  model:  ${model}`);
  console.log(`  socket: ${SOCK}`);
  console.log(`  log:    ${LOG}`);
  console.log(`  pid:    ${process.pid}`);
  console.log(`Default is ALLOW. Deny is reserved for real, lasting harm.`);
}

if (import.meta.main) {
  const args = process.argv.slice(2);
  const mIdx = args.indexOf("--model");
  const model = mIdx >= 0 && args[mIdx + 1] ? args[mIdx + 1]! : "opus";

  if (args.includes("--token")) {
    console.log(ensureToken());
  } else if (args.includes("--print-prompt")) {
    console.log(
      buildPrompt({ tool_name: "Bash", tool_input: { command: "rm -rf build/" }, cwd: "/tmp", context: "(demo)" }),
    );
  } else {
    await serve(model);
  }
}
