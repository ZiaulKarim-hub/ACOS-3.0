#!/usr/bin/env bun
/**
 * nemesis-daemon.ts — the Nemesis judge daemon (R-035, R-037, R-040).
 *
 *   bun nemesis-daemon.ts serve [--model opus]     run in the foreground (the CLI detaches it)
 *   bun nemesis-daemon.ts status | stop | install  LaunchAgent keep-alive
 *
 * Own socket, own token, own verdict log, own charter — never shared with the Oracle (D-19).
 * Each request spawns `claude -p --model opus` with READ-ONLY tools (Read, Grep, Glob): no
 * Bash, no Write, no Task. The prompt travels on STDIN. There is NO TIMEOUT on a verdict —
 * "think as long as needed" (D-33). An unreadable reply is classified and recovered, and a
 * final failure is a DENY that names the cause (D-14). The string "unparseable — allowed"
 * cannot occur here.
 */
import * as fs from "node:fs";
import * as path from "node:path";
import * as os from "node:os";
import { randomBytes } from "node:crypto";
import { spawnSync } from "node:child_process";
import * as net from "node:net";
import { NEMESIS_HOME, nowIso } from "./lib/state";
import { SOCK, TOKEN_FILE, PID_FILE, VERDICT_LOG, DAEMON_LOG, START_LOCK, JUDGE_TOOLS, claudeBin, spawnJudgeSync, judgeWithRecovery, type JudgeRequest, type JudgeReply, retryWaits, logContract, DEFAULT_RETRY_WAITS_MS } from "./lib/judge";
import { extractJsonObjects, repairJson, classifyFailure, recoveryPlan } from "./lib/verdict";

export const allowedTools = [...JUDGE_TOOLS];
const PLIST = path.join(os.homedir(), "Library", "LaunchAgents", "com.acos.nemesis.plist");

function log(line: string): void {
  const s = `[${nowIso()}] ${line}\n`;
  process.stdout.write(s);
  try { fs.appendFileSync(DAEMON_LOG, s); } catch { /* best effort */ }
}

function ensureHome(): void { fs.mkdirSync(NEMESIS_HOME, { recursive: true, mode: 0o700 }); }
function ensureToken(): string {
  try { const t = fs.readFileSync(TOKEN_FILE, "utf8").trim(); if (t) return t; } catch { /* create */ }
  const token = randomBytes(32).toString("hex");
  fs.writeFileSync(TOKEN_FILE, token + "\n", { mode: 0o600 });
  return token;
}

/** Generic JSON answer (review / release / holdout-author) with the same recovery discipline. */
async function judgeGeneric(prompt: string, model: string, waits: number[] = DEFAULT_RETRY_WAITS_MS, root?: string): Promise<{ result: Record<string, unknown> | null; raw: string; recovery: string[]; cause?: string; error?: string; elapsed_ms: number }> {
  const t0 = Date.now();
  const tried: string[] = [];
  const parse = (s: string): Record<string, unknown> | null => {
    for (const cand of extractJsonObjects(s).reverse()) { try { return JSON.parse(cand) as Record<string, unknown>; } catch { try { return JSON.parse(repairJson(cand)) as Record<string, unknown>; } catch { /* next */ } } }
    return null;
  };
  let r = spawnJudgeSync(prompt, model, {}, root);
  let obj = parse(r.stdout);
  if (obj) return { result: obj, raw: r.stdout, recovery: tried, elapsed_ms: Date.now() - t0 };
  let cls = classifyFailure(r.stdout, r.stderr, r.status);
  log(`generic reply unreadable: class=${cls} stderr=${r.stderr.slice(0, 200).replace(/\n/g, " ")}`);
  let cur = prompt;
  for (const step of recoveryPlan(cls)) {
    tried.push(step.action);
    log(`recovery: ${step.action}`);
    if (step.action === "shrink_to_file") {
      const tmp = path.join(NEMESIS_HOME, "tmp"); fs.mkdirSync(tmp, { recursive: true });
      const f = path.join(tmp, `prompt-${Date.now()}.txt`); fs.writeFileSync(f, cur, { mode: 0o600 });
      cur = `Your full instructions are in the file ${f}. Read it entirely with the Read tool, then answer exactly as its final section says: ONE JSON object and nothing else.`;
      r = spawnJudgeSync(cur, model, {}, root);
    } else if (step.action === "retry_backoff") { await new Promise((x) => setTimeout(x, 3000)); r = spawnJudgeSync(cur, model, {}, root); }
    else if (step.action === "wait_then_retry") { for (const w of waits) { await new Promise((x) => setTimeout(x, w)); r = spawnJudgeSync(cur, model, {}, root); if (parse(r.stdout)) break; } }
    else if (step.action === "alternate_account") { if (!process.env.NEMESIS_ALT_CONFIG_DIR) continue; r = spawnJudgeSync(cur, model, { CLAUDE_CONFIG_DIR: process.env.NEMESIS_ALT_CONFIG_DIR }, root); }
    else if (step.action === "extract_from_prose" || step.action === "json_only_reask") r = spawnJudgeSync(cur + "\n\nREMINDER: output ONLY one JSON object, no prose, no fences.", model, {}, root);
    else if (step.action === "repair_json") { obj = parse(repairJson(r.stdout)); if (obj) return { result: obj, raw: r.stdout, recovery: tried, cause: cls, elapsed_ms: Date.now() - t0 }; continue; }
    else r = spawnJudgeSync(cur, model, {}, root);
    obj = parse(r.stdout);
    if (obj) return { result: obj, raw: r.stdout, recovery: tried, cause: cls, elapsed_ms: Date.now() - t0 };
    const c2 = classifyFailure(r.stdout, r.stderr, r.status); if (c2 !== cls) cls = c2;
  }
  return { result: null, raw: r.stdout, recovery: tried, cause: cls, error: (r.stderr || r.stdout).slice(0, 300), elapsed_ms: Date.now() - t0 };
}

async function handle(req: JudgeRequest, model: string): Promise<Record<string, unknown>> {
  const started = Date.now();
  try { fs.appendFileSync(path.join(NEMESIS_HOME, "requests.log"), JSON.stringify({ at: nowIso(), id: req.id, kind: req.kind, project: req.project, meta: req.meta, contract: logContract(req), prompt_sha256: Bun.hash(req.prompt).toString(16), prompt_chars: req.prompt.length }) + "\n"); } catch { /* best effort */ }
  if (req.kind === "verdict") {
    // NO TIMEOUT: the judge may take as long as it needs.
    const reply: JudgeReply = await judgeWithRecovery(req.prompt, (p, env) => spawnJudgeSync(p, model, env, req.project), { model, log, altConfigDir: process.env.NEMESIS_ALT_CONFIG_DIR, waits: retryWaits(null, req.meta) });
    const out = { ...reply, model, layer: reply.layer.replace(/^direct/, "socket") };
    try { fs.appendFileSync(VERDICT_LOG, JSON.stringify({ ts: nowIso(), id: req.id, project: req.project, path: req.meta.path, decision: reply.verdict.decision, findings: reply.verdict.findings.length, stuck: reply.verdict.history_assessment.stuck, rung: reply.verdict.history_assessment.recommended_rung, elapsed_ms: reply.elapsed_ms, layer: out.layer, cause: reply.cause, recovery: reply.recovery, reason: reply.verdict.reason }) + "\n"); } catch { /* best effort */ }
    log(`${reply.verdict.decision.toUpperCase()} ${String(req.meta.path ?? "")} (${reply.elapsed_ms}ms, ${out.layer}) findings=${reply.verdict.findings.length}${reply.cause ? ` cause=${reply.cause}` : ""}`);
    return out as unknown as Record<string, unknown>;
  }
  const g = await judgeGeneric(req.prompt, model, retryWaits(null, req.meta), req.project);
  log(`${req.kind} ${req.id} ${g.result ? "ok" : "FAILED"} (${g.elapsed_ms}ms)${g.cause ? ` cause=${g.cause}` : ""}`);
  return { kind: req.kind, id: req.id, result: g.result, raw: g.raw.slice(0, 20000), recovery: g.recovery, cause: g.cause, error: g.error, elapsed_ms: Date.now() - started, model };
}

/**
 * D-63 / R-081: IS SOMETHING ALREADY LISTENING AT THE SOCKET PATH?
 *
 * A unix socket path has exactly ONE bound inode. `serve` used to unlink whatever it found and bind
 * its own, which does not stop the previous daemon - it only takes away its name. That daemon keeps
 * running, accepting nothing, forever. Connecting is the whole test: a connect that succeeds proves
 * a listener, and nothing is sent, so no request is judged and no log is touched.
 */
async function someoneIsServing(): Promise<boolean> {
  if (!fs.existsSync(SOCK)) return false;
  return await new Promise<boolean>((resolve) => {
    let settled = false;
    const finish = (v: boolean): void => { if (settled) return; settled = true; clearTimeout(timer); try { c.destroy(); } catch { /* already gone */ } resolve(v); };
    const c = net.createConnection(SOCK);
    // cleared on settle, so a daemon that finds the path taken exits at once rather than holding
    // the event loop open for the whole timeout
    const timer = setTimeout(() => finish(false), 2000);
    c.on("connect", () => finish(true));
    c.on("error", () => finish(false));                 // ECONNREFUSED on a stale socket file
  });
}

/** Every daemon process this user is running, so `stop` can reap a fleet rather than one of it. */
function daemonPids(): number[] {
  try {
    const r = spawnSync("/bin/ps", ["-eo", "pid=,command="], { encoding: "utf8" });
    return r.stdout.split("\n")
      .filter((l) => l.includes("nemesis-daemon.ts") && /\bserve\b/.test(l) && !l.includes("grep"))
      .map((l) => Number(l.trim().split(/\s+/)[0]))
      .filter((n) => Number.isFinite(n) && n > 0 && n !== process.pid);
  } catch { return []; }
}

export async function serve(model: string): Promise<void> {
  ensureHome();
  const token = ensureToken();
  if (!claudeBin()) log("WARNING: no claude binary found — verdicts will fail closed (deny) until it is installed");
  // R-081: a live socket is never unlinked. Exiting 0 here is the point — the daemon that is
  // already answering keeps answering, and this process does not become an unreachable orphan.
  if (await someoneIsServing()) {
    log(`a daemon is already serving at ${SOCK}; this one is exiting instead of unlinking a live socket (R-081). Run \`nemesis daemon stop\` first to replace it.`);
    try { fs.unlinkSync(START_LOCK); } catch { /* best effort */ }
    return;
  }
  try { fs.unlinkSync(SOCK); } catch { /* none */ }     // only a STALE socket file reaches here
  fs.writeFileSync(PID_FILE, String(process.pid) + "\n", { mode: 0o600 });
  Bun.listen({
    unix: SOCK,
    socket: {
      open(socket) { (socket as unknown as { buf: string }).buf = ""; },
      async data(socket, data) {
        const s = socket as unknown as { buf: string };
        s.buf += new TextDecoder().decode(data);
        if (!s.buf.includes("\n")) return; // newline-framed: wait for the whole request
        const line = s.buf.slice(0, s.buf.indexOf("\n"));
        s.buf = "";
        let req: JudgeRequest;
        try { req = JSON.parse(line) as JudgeRequest; } catch {
          socket.write(JSON.stringify({ verdict: { decision: "deny", findings: [], history_assessment: { stuck: false, recommended_rung: 1, why: "" }, reason: "bad request to the Nemesis daemon — nothing was judged" }, layer: "bad-request", elapsed_ms: 0 }) + "\n");
          socket.end(); return;
        }
        const out = await handle(req, model);
        socket.write(JSON.stringify(out) + "\n");
        socket.end();
      },
    },
  });
  fs.chmodSync(SOCK, 0o600);
  try { fs.unlinkSync(START_LOCK); } catch { /* best effort */ }   // bound: the next caller may start one if this dies
  log(`Nemesis is awake. model=${model} socket=${SOCK} tools=${allowedTools.join(",")} pid=${process.pid} token=${token.slice(0, 6)}…`);
  log(`Default is DENY on any finding. An unreadable verdict is classified and recovered; never allowed by default.`);
}

function status(): void {
  const pid = (() => { try { return Number(fs.readFileSync(PID_FILE, "utf8").trim()); } catch { return 0; } })();
  const alive = pid > 0 && (() => { try { process.kill(pid, 0); return true; } catch { return false; } })();
  console.log(`socket: ${fs.existsSync(SOCK) ? SOCK : "(absent)"}`);
  console.log(`pid: ${pid || "(none)"} ${alive ? "alive" : "not running"}`);
  console.log(`claude: ${claudeBin() ?? "(not found)"}`);
  console.log(`verdict log: ${VERDICT_LOG}`);
  if (fs.existsSync(VERDICT_LOG)) {
    const lines = fs.readFileSync(VERDICT_LOG, "utf8").trim().split("\n").filter(Boolean);
    const today = lines.filter((l) => l.includes(`"ts":"${nowIso().slice(0, 10)}`));
    console.log(`verdicts: ${lines.length} total, ${today.length} today`);
  }
}

/** R-081: stops the DAEMON, not one process of it. This read only `PID_FILE`, which names the
    newest daemon only, so on 2026-11-10 it would have stopped 1 of 44 and reported success. */
function stop(): void {
  const pids = new Set<number>(daemonPids());
  try { const p = Number(fs.readFileSync(PID_FILE, "utf8").trim()); if (p > 0) pids.add(p); } catch { /* no pid file */ }
  const killed: number[] = [];
  for (const p of pids) { try { process.kill(p, "SIGTERM"); killed.push(p); } catch { /* already gone */ } }
  console.log(killed.length ? `stopped ${killed.length} daemon process(es): ${killed.join(", ")}` : "daemon not running");
  try { fs.unlinkSync(SOCK); } catch { /* none */ }
  try { fs.unlinkSync(START_LOCK); } catch { /* none */ }
}

function install(): void {
  const bun = process.execPath;
  const here = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/%20/g, " ")), "nemesis-daemon.ts");
  const plist = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.acos.nemesis</string>
  <key>ProgramArguments</key><array><string>${bun}</string><string>${here}</string><string>serve</string></array>
  <key>RunAtLoad</key><true/>
  <!-- R-081: restart on a CRASH, never on a clean exit. serve exits 0 when another daemon is
       already answering, and an unconditional KeepAlive would respawn it every few seconds. -->
  <key>KeepAlive</key><dict><key>SuccessfulExit</key><false/></dict>
  <key>StandardOutPath</key><string>${path.join(NEMESIS_HOME, "launchd-out.log")}</string>
  <key>StandardErrorPath</key><string>${path.join(NEMESIS_HOME, "launchd-err.log")}</string>
  <key>EnvironmentVariables</key><dict><key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:${path.dirname(bun)}</string></dict>
</dict></plist>
`;
  fs.mkdirSync(path.dirname(PLIST), { recursive: true });
  fs.writeFileSync(PLIST, plist);
  const r = spawnSync("launchctl", ["load", "-w", PLIST], { encoding: "utf8" });
  console.log(`LaunchAgent written: ${PLIST}\nlaunchctl load: ${r.status === 0 ? "ok" : r.stderr.trim()}`);
}

if (import.meta.main) {
  const [cmd, ...rest] = process.argv.slice(2);
  const mi = rest.indexOf("--model");
  const model = mi >= 0 && rest[mi + 1] ? rest[mi + 1]! : "opus";
  if (cmd === "serve") await serve(model);
  else if (cmd === "status") status();
  else if (cmd === "stop") stop();
  else if (cmd === "install") install();
  else { console.log("usage: nemesis-daemon.ts serve [--model opus] | status | stop | install"); process.exit(2); }
}
