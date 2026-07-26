#!/usr/bin/env bun
/**
 * riff-live — the live responder for the research room.
 *
 * Removes the moderator from the loop: when the chair clicks "Call" (or types to
 * a seat) in the room, that lands as a `speak` line in chair-inbox.jsonl. This
 * daemon tails that inbox, builds the called seat's GROUNDED prompt from its own
 * dossier claims, and dispatches it to a warm pool of `claude -p` workers, which
 * generate the turn in ~5-7s and append it to room-turns.jsonl (which the room
 * server broadcasts over SSE). The main Claude session never touches it.
 *
 * Faithful port of acos-investment-committee's ic-pool.py + ic-live.py protocol.
 * LOAD-BEARING (kept verbatim from that engine, do not "simplify"):
 *   - workers run `claude -p --safe-mode --input-format stream-json
 *     --output-format stream-json --verbose --model <m>` — subscription OAuth,
 *     NEVER an API key (a set key would silently bill per-token; we refuse it).
 *   - every user message is a CONTENT-BLOCK ARRAY, never a bare string, or the
 *     `result` event can defer to stdin-EOF and stall multi-turn.
 *   - the per-turn `result` event IS end-of-turn.
 *   - --safe-mode disables this project's hooks/CLAUDE.md/skills, so a seat is
 *     NOT reshaped by the session's Eden reading-level filter and warmup skips
 *     the slow SessionStart hooks; the reading level is set in the prompt instead.
 *
 * The one thing that is riff-specific and MUST NOT be softened: a seat speaks
 * ONLY from its own findings and cites their ids; if the chair's question is not
 * in its corpus it says so and does not guess (invariants I2 + I9).
 *
 * Run:  bun riff-live.ts --session <id> [--models sonnet,haiku] [--root <dir>]
 */
import { existsSync, readFileSync, writeFileSync, appendFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { parseArgs, readJsonl } from "./lib/util.ts";
import { paths, resolveSession } from "./lib/session.ts";
import { loadPanel } from "./lib/panel.ts";
import { allClaims } from "./lib/claims.ts";

const CLAUDE_BIN = process.env.ACOS_CLAUDE_BIN || join(process.env.HOME || "", ".claude/local/claude");
const RESET_AFTER_TURNS = 20;

const args = parseArgs(process.argv.slice(2));
if (args.flags["root"]) process.env.RIFF_ROOT = args.flags["root"];

if (process.env.ANTHROPIC_API_KEY) {
  console.error(JSON.stringify({ event: "live_failed", error: "ANTHROPIC_API_KEY is set — refusing (Max-subscription only; a set key bills per-token)" }));
  process.exit(2);
}

let sessionId: string;
try {
  sessionId = resolveSession(args.flags["session"]).session_id;
} catch (e) {
  console.error(`riff-live: ${e instanceof Error ? e.message : String(e)}`);
  process.exit(1);
}

const P = paths(sessionId);
const INBOX = join(P.root, "chair-inbox.jsonl");
const TURNS = join(P.root, "room-turns.jsonl");
const THINKING = join(P.root, "room-thinking.json");
const LEVELFILE = join(P.root, "room-level.json");
const LOCK = join(P.root, "room-live.lock");

// Single consumer only — a second daemon would double-answer every click.
if (existsSync(LOCK)) {
  try {
    const prev = JSON.parse(readFileSync(LOCK, "utf8"));
    try {
      process.kill(prev.pid, 0); // throws if the pid is gone
      console.error(JSON.stringify({ event: "live_failed", error: "another live responder owns this session", pid: prev.pid }));
      process.exit(3);
    } catch {
      /* stale lock; take it */
    }
  } catch {
    /* unreadable lock; take it */
  }
}
writeFileSync(LOCK, JSON.stringify({ pid: process.pid, ts: new Date().toISOString() }));
function releaseLock() {
  try {
    if (existsSync(LOCK) && JSON.parse(readFileSync(LOCK, "utf8")).pid === process.pid) writeFileSync(LOCK, "");
  } catch {
    /* ignore */
  }
}

// ---- reading-level dial (the pool runs --safe-mode, so the prompt is the ONLY
//      thing that sets a seat's register) --------------------------------------
const LEVELS: Record<number, string> = {
  0: "READING LEVEL 0 (EXPERT — default): speak to sophisticated peers; use technical terms freely with no definitions.",
  1: "READING LEVEL 1 (ADVANCED): precise professional language; briefly gloss an unusual term the first time.",
  2: "READING LEVEL 2 (PLAIN PROFESSIONAL): plain business English; define each technical term in a few words on first use.",
  3: "READING LEVEL 3 (GENERAL): short sentences, everyday words; define EVERY technical term simply the first time and give one quick example.",
  4: "READING LEVEL 4 (SIMPLE): very plain, very short sentences; explain as if to someone new to the topic.",
  5: "READING LEVEL 5 (VERY SIMPLE): the simplest possible language, tiny words, one idea per sentence.",
};
const LEVEL_FIDELITY = " Keep EVERY number, name, source id and your actual conclusion exactly the same — change only HOW plainly you say it, never what is true, and never drop a caveat.";

function readLevel(): number {
  try {
    return Math.max(0, Math.min(5, Number(JSON.parse(readFileSync(LEVELFILE, "utf8")).level) || 0));
  } catch {
    return 0;
  }
}

interface Turn { seat: number; slug: string; name: string; short: string; text: string; ts: string; chair?: string }

function recentTurns(n = 10): Turn[] {
  return readJsonl<Turn>(TURNS).slice(-n);
}
function setThinking(seat: number) {
  writeFileSync(THINKING, JSON.stringify({ seat, ts: new Date().toISOString() }));
}
function clearThinking() {
  writeFileSync(THINKING, JSON.stringify({}));
}
function appendTurn(t: Turn) {
  appendFileSync(TURNS, JSON.stringify(t) + "\n");
  clearThinking();
}

const panel = loadPanel(sessionId).seats;
function seatOf(n: number) {
  return panel[n - 1]; // buildIcState numbers seats by panel order, 1-based
}

/** The grounded prompt: a seat may state ONLY its own findings and must cite ids. */
function buildPrompt(seatN: number, chair: string, topic: string): { name: string; short: string; prompt: string; model: string } {
  const seat = seatOf(seatN);
  const slug = seat?.slug ?? `seat-${seatN}`;
  const name = seat?.title || slug;
  const short = (seat?.title || slug).slice(0, 22);
  const mine = allClaims(sessionId)
    .filter((c) => c.slug === slug)
    .sort((a, b) => (a.tier ?? 9) - (b.tier ?? 9))
    .slice(0, 24);
  const findings = mine.length
    ? mine.map((c) => `- [${c.id}] (tier ${c.tier ?? "?"}, ${c.sources.length} src, as of ${c.as_of}) ${c.claim}`).join("\n")
    : "(you have no recorded findings on this yet — say so plainly and do not invent any)";
  const tl = recentTurns(10);
  const transcript = tl.length
    ? tl.map((t) => `${t.short}: ${t.text}`).join("\n\n")
    : "(the discussion has just opened — no turns yet)";
  const level = readLevel();
  const spokeBefore = tl.some((t) => t.seat === seatN);

  const parts = [
    `You are the "${name}" seat on a research panel investigating: ${topic}`,
    `You personally did the research on your lane. Speak in the first person, like a panelist in a live meeting — short, human, varied sentences; never a memo.`,
    `YOUR FINDINGS — the ONLY facts you may state. Each has an id; cite the id(s) in square brackets behind every claim:\n${findings}`,
    `THE DISCUSSION SO FAR:\n${transcript}`,
    LEVELS[level] + LEVEL_FIDELITY,
    `RULES (binding): Speak ONLY from YOUR FINDINGS above. If the question is not covered by them, say "that's not in what I found" and name what you'd need to check — do NOT guess or fill the gap. Cite finding ids like [named-frontier-017]. Keep every number, name and source exact.`,
  ];
  if (chair) {
    parts.push(`THE CHAIR JUST ASKED YOU:\n"${chair}"`);
    parts.push(`TASK: Answer the chair directly, in character, using only your findings. If nothing you found bears on it, say so and stop. ~90-150 words. Return ONLY your spoken turn — no preamble, no name label.`);
  } else {
    const verb = spokeBefore ? "add your next most important finding given the discussion above" : "deliver your single most important finding on your lane";
    parts.push(`TASK: ${verb}, in character, grounded in and citing your findings. ~90-150 words. Return ONLY your spoken turn — no preamble, no name label.`);
  }
  // haiku for a plain first opening, sonnet for real answers/arguments
  const model = !chair && !spokeBefore ? "haiku" : "sonnet";
  return { name, short, prompt: parts.join("\n\n"), model };
}

// ---- warm pool of claude -p workers (protocol ported from ic-pool.py) --------
type Job = { seatN: number; name: string; short: string; slug: string; prompt: string; chair: string };

class Worker {
  proc: ReturnType<typeof Bun.spawn> | null = null;
  ready = false;
  private inWarmup = false;
  private acc = "";
  private current: Job | null = null;
  private q: Job[] = [];
  private turns = 0;
  constructor(public model: string) { this.start(); }

  start() {
    this.ready = false;
    this.proc = Bun.spawn(
      [CLAUDE_BIN, "-p", "--safe-mode", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose", "--model", this.model],
      { stdin: "pipe", stdout: "pipe", stderr: "ignore" },
    );
    this.readLoop();
    this.inWarmup = true;
    this.write(userMsg("Reply with only the word: ok"));
  }

  private write(msg: unknown): boolean {
    try {
      const sink = this.proc!.stdin as { write(s: string): unknown; flush(): unknown };
      sink.write(JSON.stringify(msg) + "\n");
      sink.flush();
      return true;
    } catch {
      return false;
    }
  }

  private async readLoop() {
    const dec = new TextDecoder();
    let buf = "";
    try {
      for await (const chunk of this.proc!.stdout as unknown as AsyncIterable<Uint8Array>) {
        buf += dec.decode(chunk);
        let nl: number;
        while ((nl = buf.indexOf("\n")) >= 0) {
          const line = buf.slice(0, nl).trim();
          buf = buf.slice(nl + 1);
          if (line) this.onEvent(line);
        }
      }
    } catch {
      /* worker died; a resubmit will restart it */
    }
  }

  private onEvent(line: string) {
    let evt: Record<string, unknown>;
    try {
      evt = JSON.parse(line);
    } catch {
      return;
    }
    const t = evt.type;
    if (t === "result" && this.inWarmup) {
      this.inWarmup = false;
      this.ready = true;
      this.drain();
      return;
    }
    if (this.inWarmup) return;
    if (!this.current) return;
    if (t === "assistant") {
      const content = (evt.message as { content?: Array<{ type: string; text?: string }> })?.content ?? [];
      for (const b of content) if (b.type === "text") this.acc += b.text ?? "";
    } else if (t === "result") {
      const text = this.acc.trim() || "(the seat returned no response)";
      const cur = this.current;
      this.current = null;
      this.acc = "";
      appendTurn({ seat: cur.seatN, slug: cur.slug, name: cur.name, short: cur.short, text, ts: new Date().toISOString(), ...(cur.chair ? { chair: cur.chair } : {}) });
      console.log(JSON.stringify({ event: "turn", seat: cur.seatN, model: this.model, chars: text.length }));
      this.maybeReset();
      this.drain();
    }
  }

  submit(job: Job) {
    this.q.push(job);
    if (!this.current) this.drain();
  }

  private drain() {
    if (this.current) return;
    const job = this.q.shift();
    if (!job) return;
    this.current = job;
    this.acc = "";
    this.turns++;
    if (!this.write(userMsg(job.prompt))) {
      this.current = null;
      this.start();
      this.q.unshift(job);
    }
  }

  private maybeReset() {
    if (this.turns >= RESET_AFTER_TURNS) {
      try {
        this.proc?.kill();
      } catch {
        /* ignore */
      }
      this.turns = 0;
      this.start();
    }
  }

  kill() {
    try {
      this.proc?.kill();
    } catch {
      /* ignore */
    }
  }
}

function userMsg(text: string) {
  // CONTENT-BLOCK ARRAY framing (load-bearing) — never a bare string.
  return { type: "user", message: { role: "user", content: [{ type: "text", text }] } };
}

const modelNames = (args.flags["models"] || "sonnet,haiku").split(",").map((s) => s.trim()).filter(Boolean);
const workers = new Map<string, Worker>();
for (const m of modelNames) workers.set(m, new Worker(m));

function pickWorker(model: string): Worker {
  return workers.get(model) || workers.get("sonnet") || [...workers.values()][0]!;
}

async function waitReady(timeoutMs = 120_000): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if ([...workers.values()].every((w) => w.ready)) return true;
    await Bun.sleep(150);
  }
  return false;
}

// ---- inbox consumer ----------------------------------------------------------
let topic = "this research question";
try {
  topic = JSON.parse(readFileSync(P.manifest, "utf8")).topic || topic;
} catch {
  /* keep default */
}

function handle(cmd: Record<string, unknown>) {
  const typ = String(cmd.type || "").toLowerCase();
  if (typ === "level" || typ === "reading_level") {
    const lvl = Math.max(0, Math.min(5, Number(cmd.value ?? cmd.level ?? 0) || 0));
    writeFileSync(LEVELFILE, JSON.stringify({ level: lvl }));
    console.log(JSON.stringify({ event: "level", level: lvl }));
    return;
  }
  // "speak" (a seat is called) or a bare "message"/"speak" -> route to a seat.
  let seatN = cmd.seat != null ? Number(cmd.seat) : null;
  const chair = String(cmd.chair ?? cmd.text ?? "").trim();
  if (seatN == null) {
    if (!chair) return;
    seatN = routeToSeat(chair); // a bare chair message goes to the best-matching seat
  }
  if (!seatN || seatN < 1 || seatN > panel.length) return;
  setThinking(seatN);
  const { name, short, prompt, model } = buildPrompt(seatN, chair, topic);
  pickWorker(model).submit({ seatN, name, short, slug: seatOf(seatN)?.slug ?? `seat-${seatN}`, prompt, chair });
  console.log(JSON.stringify({ event: "dispatch", seat: seatN, model, chair: Boolean(chair) }));
}

/** Pick the seat whose corpus best matches a bare chair message (lexical overlap). */
function routeToSeat(text: string): number {
  const words = new Set(text.toLowerCase().match(/[a-z0-9]{3,}/g) ?? []);
  let best = 1;
  let bestScore = -1;
  panel.forEach((p, i) => {
    const claims = allClaims(sessionId).filter((c) => c.slug === p.slug);
    let score = 0;
    for (const c of claims) {
      const cw = c.claim.toLowerCase();
      for (const w of words) if (cw.includes(w)) score++;
    }
    // a generalist is the sensible fallback for an off-lane question
    if (p.role === "generalist") score += 0.5;
    if (score > bestScore) {
      bestScore = score;
      best = i + 1;
    }
  });
  return best;
}

function shutdown() {
  for (const w of workers.values()) w.kill();
  releaseLock();
  process.exit(0);
}
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
process.on("exit", releaseLock);

(async () => {
  const ok = await waitReady();
  if (!ok) {
    console.error(JSON.stringify({ event: "live_failed", error: "pool warmup timeout" }));
    shutdown();
    return;
  }
  if (!existsSync(THINKING)) clearThinking();
  let off = existsSync(INBOX) ? statSync(INBOX).size : 0;
  console.log(JSON.stringify({ event: "live_ready", session_id: sessionId, models: modelNames, start_offset: off }));
  const poll = Number(args.flags["poll"] ?? "0.15") * 1000;
  // eslint-disable-next-line no-constant-condition
  while (true) {
    try {
      if (existsSync(INBOX)) {
        const sz = statSync(INBOX).size;
        if (sz < off) off = sz; // file truncated/rotated
        if (sz > off) {
          const fd = readFileSync(INBOX, "utf8");
          const chunk = fd.slice(off);
          off = Buffer.byteLength(fd, "utf8");
          for (const ln of chunk.split("\n")) {
            const s = ln.trim();
            if (!s) continue;
            try {
              handle(JSON.parse(s));
            } catch (e) {
              console.error(JSON.stringify({ event: "cmd_err", error: e instanceof Error ? e.message : String(e) }));
            }
          }
        }
      }
    } catch (e) {
      console.error(JSON.stringify({ event: "loop_err", error: e instanceof Error ? e.message : String(e) }));
    }
    await Bun.sleep(poll);
  }
})();
