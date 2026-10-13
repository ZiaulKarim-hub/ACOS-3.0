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
import { RequestFramer } from "./framing";

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

function isJudgeRequest(v: unknown): v is JudgeRequest {
  if (v === null || typeof v !== "object") return false;
  const o = v as Record<string, unknown>;
  return typeof o.tool_name === "string" && typeof o.cwd === "string" &&
    o.tool_input !== null && typeof o.tool_input === "object" && !Array.isArray(o.tool_input);
}

interface Verdict {
  decision: "allow" | "deny";
  reason: string;
  elapsed_ms: number;
  model: string;
  /** D-14 (2026-10-08): when the first reply was unreadable, what class it was and what was tried. */
  cause?: FailureClass;
  recovery?: string[];
}

// ---------------------------------------------------------------------------
// Unreadable replies: classify, recover, and only then deny — NEVER allow.
//
// Zee, 2026-10-08: "make sure that the oracle finds the reason of a verdict being
// unreadable and finds a way to read this and then makes the decision, not just passes it
// to me." Before this change 990 verdicts were silently allowed as unreadable, 87 of 169
// Writes among them. The reasons were lost because stderr was discarded and the prompt sat
// on the command line (E2BIG for big Writes). Now: the prompt goes on STDIN, stderr is kept,
// the failure is classified, each class has a recovery plan, and a final failure is a DENY
// that names the class. (Mirrors acos-nemesis-protocol/scripts/lib/verdict.ts, reimplemented
// here so the Oracle never depends on a skill directory.)
// ---------------------------------------------------------------------------

export type FailureClass = "empty" | "usage_limit" | "too_long" | "prose" | "malformed" | "auth" | "crash";

function extractJsonObjects(text: string): string[] {
  const out: string[] = [];
  let depth = 0, start = -1, inStr = false, esc = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i]!;
    if (inStr) { if (esc) esc = false; else if (c === "\\") esc = true; else if (c === '"') inStr = false; continue; }
    if (c === '"') { inStr = true; continue; }
    if (c === "{") { if (depth === 0) start = i; depth++; }
    else if (c === "}") { depth--; if (depth === 0 && start >= 0) { out.push(text.slice(start, i + 1)); start = -1; } if (depth < 0) depth = 0; }
  }
  return out;
}

export function repairJson(s: string): string {
  return s.replace(/```(?:json)?/g, "").replace(/[\u201c\u201d]/g, '"').replace(/[\u2018\u2019]/g, "'")
    .replace(/,\s*([}\]])/g, "$1").replace(/'([^'\\]*)'\s*:/g, '"$1":').replace(/:\s*'([^'\\]*)'/g, ': "$1"')
    .replace(/\bTrue\b/g, "true").replace(/\bFalse\b/g, "false").replace(/\bNone\b/g, "null");
}

export function classifyFailure(stdout: string, stderr: string, exitCode: number | null): FailureClass {
  const all = `${stdout}\n${stderr}`;
  if (/E2BIG|argument list too long|prompt is too long|too many tokens|exceeds the (maximum|context)|context window/i.test(all)) return "too_long";
  if (/usage limit|rate limit|rate_limit|quota|429|overloaded|too many requests|limit reached|You've reached/i.test(all)) return "usage_limit";
  if (/not logged in|unauthori[sz]ed|invalid api key|authentication|please run \/login|OAuth/i.test(all)) return "auth";
  if (!stdout.trim()) return exitCode === 0 ? "empty" : "crash";
  if (extractJsonObjects(stdout).some((x) => /"decision"/.test(x))) return "malformed";
  return "prose";
}

export type RecoveryAction = "retry_direct" | "retry_backoff" | "shrink_to_file" | "json_only_reask" | "extract_from_prose" | "repair_json" | "alternate_account" | "wait_then_retry";

export function recoveryPlan(cls: FailureClass): RecoveryAction[] {
  switch (cls) {
    case "empty": case "crash": return ["retry_direct", "retry_backoff", "shrink_to_file"];
    case "usage_limit": return ["wait_then_retry", "alternate_account"];
    case "too_long": return ["shrink_to_file", "retry_direct"];
    case "prose": return ["extract_from_prose", "json_only_reask"];
    case "malformed": return ["repair_json", "json_only_reask"];
    case "auth": return ["alternate_account", "retry_backoff"];
  }
}

function extractionPrompt(prose: string): string {
  return `A permission judge answered in prose instead of JSON. Convert it FAITHFULLY into the required JSON and output ONLY the JSON. If the prose says the action is acceptable/ordinary/safe, the decision is "allow". If it says the action would do real, lasting damage and should not run, the decision is "deny". Do not add judgement of your own.\n\nRequired shape: {"decision":"allow"|"deny","reason":"<short>"}\n\n--- THE PROSE ---\n${prose.slice(0, 20000)}\n--- END ---`;
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
    cause: v.cause, recovery: v.recovery,
  });
  appendFileSync(LOG, line + "\n", { encoding: "utf8" });
}

/** Pull the verdict JSON out of the model's reply, wherever it sits. */
export function parseVerdict(raw: string): { decision: "allow" | "deny"; reason: string } | null {
  const text = (raw ?? "").trim();
  if (!text) return null;
  // Last JSON object carrying a decision wins: a thinking-aloud reply ends with its answer.
  const cands = extractJsonObjects(text).filter((x) => /"decision"\s*:/.test(x));
  for (let i = cands.length - 1; i >= 0; i--) {
    for (const attempt of [cands[i]!, repairJson(cands[i]!)]) {
      try {
        const o = JSON.parse(attempt) as { decision: string; reason?: string };
        if (o.decision === "allow" || o.decision === "deny") return { decision: o.decision, reason: String(o.reason ?? "").slice(0, 500) };
      } catch { /* next */ }
    }
  }
  return null;
}

function spawnJudge(prompt: string, token: string, model: string, extraEnv: Record<string, string> = {}): { stdout: string; stderr: string; status: number | null } {
  const env: Record<string, string | undefined> = { ...process.env, ACOS_ORACLE_JUDGE: token, ...extraEnv };
  delete env.ANTHROPIC_API_KEY; // standing rule: subscription only, never an API key
  // The prompt travels on STDIN: no argument-length cliff (a big Write used to hit E2BIG and
  // come back unreadable), no shell quoting.
  const proc = Bun.spawnSync([claudeBin(), "-p", "--model", model], { stdin: Buffer.from(prompt), stdout: "pipe", stderr: "pipe", env: env as Record<string, string> });
  return { stdout: proc.stdout.toString(), stderr: proc.stderr.toString(), status: proc.exitCode };
}

async function judge(req: JudgeRequest, token: string, model: string): Promise<Verdict> {
  const started = Date.now();
  // NO TIMEOUT — Zee, 2026-08-15: "Think as long as needed." A slow verdict is
  // a stuck tool call, which he accepted; a rushed verdict is a wrong one.
  const tried: string[] = [];
  let prompt = buildPrompt(req);
  let r: { stdout: string; stderr: string; status: number | null };
  try { r = spawnJudge(prompt, token, model); } catch (e) { r = { stdout: "", stderr: String(e), status: null }; }
  let parsed = parseVerdict(r.stdout);
  if (parsed) return { ...parsed, elapsed_ms: Date.now() - started, model };
  let cls = classifyFailure(r.stdout, r.stderr, r.status);
  let lastErr = (r.stderr || r.stdout).slice(0, 300) || `exit ${r.status}`;
  console.log(`[${new Date().toISOString()}] unreadable reply: class=${cls} status=${r.status} stderr=${r.stderr.slice(0, 200).replace(/\n/g, " ")}`);
  for (const action of recoveryPlan(cls)) {
    tried.push(action);
    console.log(`[${new Date().toISOString()}] recovery: ${action}`);
    try {
      switch (action) {
        case "retry_direct": r = spawnJudge(prompt, token, model); break;
        case "retry_backoff": await Bun.sleep(3000); r = spawnJudge(prompt, token, model); if (!parseVerdict(r.stdout)) { await Bun.sleep(10000); r = spawnJudge(prompt, token, model); } break;
        case "wait_then_retry": { let got = false; for (const w of [30000, 120000, 300000]) { await Bun.sleep(w); r = spawnJudge(prompt, token, model); if (parseVerdict(r.stdout)) { got = true; break; } } if (!got) continue; break; }
        case "alternate_account": if (!process.env.ORACLE_ALT_CONFIG_DIR) continue; r = spawnJudge(prompt, token, model, { CLAUDE_CONFIG_DIR: process.env.ORACLE_ALT_CONFIG_DIR }); break;
        case "shrink_to_file": {
          const dir = join(ORACLE_HOME, "tmp"); mkdirSync(dir, { recursive: true });
          const f = join(dir, `prompt-${Date.now()}.txt`); writeFileSync(f, prompt, { mode: 0o600 });
          prompt = `Your full instructions and the request to judge are in the file ${f}. Read it with the Read tool, then answer exactly as its final section says: ONE line of JSON and nothing else.`;
          r = spawnJudge(prompt, token, model); break;
        }
        case "repair_json": { const rv = parseVerdict(repairJson(r.stdout)); if (rv) return { ...rv, elapsed_ms: Date.now() - started, model, cause: cls, recovery: tried }; continue; }
        case "extract_from_prose": r = spawnJudge(extractionPrompt(r.stdout), token, model); break;
        case "json_only_reask": r = spawnJudge(prompt + "\n\nREMINDER: output ONLY the single-line JSON object. No prose, no code fences.", token, model); break;
      }
    } catch (e) { r = { stdout: "", stderr: String(e), status: null }; }
    parsed = parseVerdict(r.stdout) ?? parseVerdict(repairJson(r.stdout));
    if (parsed) return { ...parsed, elapsed_ms: Date.now() - started, model, cause: cls, recovery: tried };
    const c2 = classifyFailure(r.stdout, r.stderr, r.status);
    lastErr = (r.stderr || r.stdout).slice(0, 300) || `exit ${r.status}`;
    if (c2 !== cls) { console.log(`[${new Date().toISOString()}] class changed ${cls} → ${c2}`); cls = c2; }
  }
  // Every recovery failed. This is a DENY that names the cause — never an allow (D-14).
  return {
    decision: "deny",
    reason: `The Oracle could not obtain a readable verdict. Cause class: ${cls}. Last error: ${lastErr}. Recovery tried: ${tried.join(" → ") || "(none)"}. Oracle mode allows nothing it has not judged; fix the cause (see ~/.acos/oracle/daemon-out.log) and retry.`,
    elapsed_ms: Date.now() - started, model, cause: cls, recovery: tried,
  };
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

  // One request per connection, but the bytes arrive in CHUNKS (about 8 KB each).
  // Until 2026-10-12 every chunk was parsed as a whole document, so any request
  // over ~8 KB — a Write of a real file, a big heredoc — was "bad request" and,
  // once that stopped being fail-open, denied. RequestFramer collects the chunks
  // and says "complete" only when the whole object has arrived (see framing.ts).
  Bun.listen<{ framer: RequestFramer; settled: boolean }>({
    unix: SOCK,
    socket: {
      open: (socket) => {
        socket.data = { framer: new RequestFramer(), settled: false };
      },
      data: async (socket, chunk) => {
        const st = socket.data;
        if (st.settled) return;
        const r = st.framer.feed(chunk);
        if (r.kind === "incomplete") return;
        st.settled = true;
        if (r.kind !== "complete" || !isJudgeRequest(r.value)) {
          const why =
            r.kind === "overflow" ? `request too large (${r.bytes} bytes)` :
            r.kind === "malformed" ? r.why :
            "request is missing tool_name, tool_input or cwd";
          socket.write(JSON.stringify({ decision: "deny", reason: `bad request to the Oracle daemon (${why}) — nothing was judged, so nothing is allowed` }) + "\n");
          socket.end();
          return;
        }
        const req = r.value;
        const v = await judge(req, token, model);
        logVerdict(req, v);
        const mark = v.decision === "deny" ? "DENY " : "allow";
        console.log(
          `[${new Date().toISOString()}] ${mark} ${req.tool_name} (${v.elapsed_ms}ms)` +
            `${v.cause ? ` [recovered from ${v.cause}: ${(v.recovery ?? []).join("→")}]` : ""}\n    ${v.reason}`,
        );
        socket.write(JSON.stringify(v) + "\n");
        socket.end();
      },
      close: (socket) => {
        // The hook hung up before its request was complete (it crashed or timed
        // out). Nothing was judged and there is nobody left to answer.
        const st = socket.data;
        if (st && !st.settled && st.framer.bytes > 0) {
          console.log(`[${new Date().toISOString()}] dropped: client closed after ${st.framer.bytes} bytes of an incomplete request`);
        }
      },
      error: (_socket, err) => {
        console.log(`[${new Date().toISOString()}] socket error: ${String(err)}`);
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
