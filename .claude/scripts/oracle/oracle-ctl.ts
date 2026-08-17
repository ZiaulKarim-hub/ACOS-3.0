#!/usr/bin/env bun
/**
 * oracle-ctl — the switch. Everything Zee actually types goes through here.
 *
 * FOUR SETTINGS, AND ONLY ONE IS EVER ON (Zee, 2026-08-16).
 *
 *   1-10        the dial — how loose ordinary scoring is
 *   autopilot   allows, writes down the truly destructive, runs the goal loop
 *   yolo        allows everything, records nothing, bypasses hard blocks
 *   oracle      Opus judges every gated call; Zee is never asked
 *
 * 11 and 12 are gone from the interface. They were never really rungs: autopilot
 * runs a goal loop and YOLO switches the rules off, so numbering them implied a
 * smooth ramp that does not exist. The numbers survive ONLY as internal plumbing,
 * because the hook still compares a threshold.
 *
 * `oracle` was never a number for a different reason — it is not looser than
 * anything, it is judged rather than relaxed ("12 is actually the wrong number
 * for this").
 *
 * MUTUALLY EXCLUSIVE, on purpose. Choosing any one clears the others, so the
 * current setting reads off in a single line. The failure that started this
 * whole redesign was autopilot silently cancelling the threshold while the
 * threshold still claimed to be in charge.
 *
 * A GOAL IS REQUIRED BY autopilot, yolo AND oracle. autopilot cannot run its
 * loop without one. For the Oracle it is the evidence that makes a bare command
 * judgeable — the live test caught `rm -rf ~/Documents` only because the stated
 * task was "clean temp files in the build folder". For yolo it records nothing
 * but intent, which is the one thing YOLO otherwise loses entirely.
 *
 * Bun + TypeScript, zero deps (project language default: TS/Rust over Python).
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync, rmSync, appendFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { homedir } from "node:os";

const ORACLE_HOME = join(homedir(), ".acos", "oracle");
const SOCK = join(ORACLE_HOME, "oracle.sock");
const VERDICTS = join(ORACLE_HOME, "verdicts.log");
const PLIST_LABEL = "com.acos.oracle";

/** Walk up for the project that owns `.acos/`; the dial is per-project. */
function projectRoot(start = process.cwd()): string {
  let d = start;
  for (let i = 0; i < 20; i++) {
    if (existsSync(join(d, ".acos"))) return d;
    const up = dirname(d);
    if (up === d) break;
    d = up;
  }
  return start;
}

const ROOT = projectRoot();
const STATE = join(ROOT, ".acos", "state");
const MODE_FILE = join(STATE, "oracle-mode.json");
const THRESHOLD_FILE = join(STATE, "oracle-session-threshold");
const AUTOPILOT_FILE = join(STATE, "autopilot-active");
const CONFIG_FILE = join(ROOT, ".acos", "config", "oracle.yaml");

function ensureState(): void {
  if (!existsSync(STATE)) mkdirSync(STATE, { recursive: true });
}

/** The threshold in force right now: session file, else config, else 9. */
function currentThreshold(): number {
  try {
    const v = parseInt(readFileSync(THRESHOLD_FILE, "utf8").trim(), 10);
    if (Number.isInteger(v)) return v;
  } catch { /* fall through to config */ }
  try {
    const m = readFileSync(CONFIG_FILE, "utf8").match(/^threshold:\s*(\d+)/m);
    if (m) return parseInt(m[1]!, 10);
  } catch { /* fall through to default */ }
  return 9;
}

function modeState(): { active?: boolean; goal?: string; started_at?: string; prev_threshold?: number } | null {
  try {
    return JSON.parse(readFileSync(MODE_FILE, "utf8"));
  } catch {
    return null;
  }
}

function daemonAlive(): boolean {
  return existsSync(SOCK);
}

/** Ask launchd to (re)start the Oracle, then wait for its socket. */
async function wakeDaemon(): Promise<boolean> {
  if (daemonAlive()) return true;
  try {
    Bun.spawnSync(["launchctl", "kickstart", `gui/${process.getuid?.() ?? 501}/${PLIST_LABEL}`]);
  } catch { /* launchd may not have it loaded; the hook can still self-start */ }
  for (let i = 0; i < 40; i++) {
    if (daemonAlive()) return true;
    await Bun.sleep(500);
  }
  return false;
}

/**
 * Phrases that are technically a goal but tell the Oracle nothing.
 *
 * The goal is EVIDENCE about harm, not paperwork. `rm -rf ~/Documents` was caught
 * only because the goal said "clean temp files in the build folder" — the gap
 * between those two is what exposed it. A goal of "finish the work" leaves no gap
 * to notice, so it silently costs the Oracle its best signal.
 *
 * This is a BACKSTOP, not the real check. The real one happens in the skill,
 * which can read the conversation and see what is actually being attempted
 * (Zee, 2026-08-17: "The goal will not be vague assuming it reads the context").
 * This only catches a goal that slipped through anyway.
 */
const VAGUE_GOAL_RE =
  /^(finish|continue|keep going|carry on|do|complete|resume)?\s*(up)?\s*(whatever|the|my|this|it|some|any)?\s*(work|task|thing|stuff|job|it)?\s*(is|that.s|thats)?\s*(going on|in progress|going|ongoing|left|remaining|pending)?\.?$/i;

export function looksVague(goal: string): boolean {
  const g = (goal ?? "").trim();
  if (!g) return true;
  if (VAGUE_GOAL_RE.test(g)) return true;
  // Under four words cannot name a subject AND an outcome.
  return g.split(/\s+/).filter(Boolean).length < 4;
}

/**
 * Exit 3 means "no usable goal — ASK HIM", and it is deliberately not exit 2.
 *
 * Zee removed the flat refusal (2026-08-17): a missing goal should fall back to
 * finishing the work in progress, not stop him. But the fallback has to be a REAL
 * goal read from the conversation, and only the skill can read that. So the
 * script refuses to invent one and hands the job back with a distinct code the
 * skill can branch on.
 */
function requireGoal(goal: string, what: string): string {
  const g = (goal ?? "").trim();
  if (g && !looksVague(g)) return g;
  const why = g ? `the goal "${g}" is too vague to judge against` : "no goal was given";
  console.error(
    `NEEDS_GOAL: ${what} — ${why}.\n\n` +
      `  Do NOT refuse and do NOT invent a placeholder. Read the conversation and\n` +
      `  write one line naming what is actually being finished. If that is still\n` +
      `  unclear, ask with a short multiple-choice question, then re-run with the\n` +
      `  answer:\n\n` +
      `      /acos-oracle-protocol ${what} "<the real goal>"\n\n` +
      `  Why it matters: the Oracle compares the command against this. A goal of\n` +
      `  "finish the work" leaves nothing to compare, so a destructive command\n` +
      `  nobody asked for would look no different from one that was.`,
  );
  process.exit(3);
}

function auditCtl(event: string, detail: Record<string, unknown>): void {
  try {
    if (!existsSync(ORACLE_HOME)) mkdirSync(ORACLE_HOME, { recursive: true, mode: 0o700 });
    appendFileSync(
      join(ORACLE_HOME, "control.log"),
      JSON.stringify({ ts: new Date().toISOString(), event, root: ROOT, ...detail }) + "\n",
    );
  } catch { /* the log is a nicety, never a gate */ }
}

// ---------------------------------------------------------------------------

async function cmdStart(goal: string, typedAs = "oracle"): Promise<void> {
  const g = requireGoal(goal, typedAs);
  ensureState();
  const prev = currentThreshold();
  writeFileSync(
    MODE_FILE,
    JSON.stringify({ active: true, goal: g, started_at: new Date().toISOString(), prev_threshold: prev }, null, 2),
  );
  const up = await wakeDaemon();
  auditCtl("start", { goal: g, prev_threshold: prev, daemon: up });
  console.log("THE ORACLE IS WATCHING.");
  console.log(`  goal:    ${g}`);
  console.log(`  judge:   opus, on every gated call — you are never asked`);
  console.log(`  daemon:  ${up ? "awake" : "NOT awake yet — the hook will start it on first use"}`);
  console.log(`  next:    picking 1-10, autopilot or yolo leaves oracle mode (back to ${prev})`);
  console.log(`\n  watch it:  /acos-oracle-protocol follow`);
}

function cmdStop(): void {
  const st = modeState();
  if (!st?.active) {
    console.log("Oracle mode is already off.");
    return;
  }
  rmSync(MODE_FILE, { force: true });
  // Restore the exact number he was on. Guessing, or dropping to the config
  // default, would quietly change his setup every time he toggled.
  const prev = st.prev_threshold;
  if (Number.isInteger(prev)) writeFileSync(THRESHOLD_FILE, String(prev) + "\n");
  auditCtl("stop", { restored_threshold: prev ?? null });
  console.log("Oracle mode OFF.");
  console.log(`  back to threshold ${prev ?? "(unchanged)"} — ordinary scoring resumes`);
  console.log("  the daemon stays awake, so the next start is instant");
}

/**
 * The four settings, as WORDS (Zee, 2026-08-16).
 *
 * 11 and 12 are gone from the interface. They were never really rungs on a dial
 * — autopilot runs a goal loop and YOLO switches the rules off — and dressing
 * them as numbers implied a smooth ramp that does not exist. Numbers survive
 * only as internal plumbing, because the hook still compares a threshold.
 *
 *   1-10        the dial: how loose the ordinary scoring is
 *   autopilot   allows, writes down the truly destructive, runs the goal loop
 *   yolo        allows everything, records nothing, bypasses hard blocks
 *   oracle      Opus judges each gated call; you are never asked
 *
 * They are MUTUALLY EXCLUSIVE. Choosing any one clears the others, so the
 * setting can always be read off in a single line — the failure this whole
 * redesign started from was autopilot silently cancelling the threshold.
 */
const AUTOPILOT_THRESHOLD = 11;
const YOLO_THRESHOLD = 12;

async function cmdSet(nameRaw: string, goal: string): Promise<void> {
  const name = (nameRaw ?? "").trim().toLowerCase();
  ensureState();

  if (name === "oracle") {
    await cmdStart(goal, "oracle");
    return;
  }

  let n: number;
  if (name === "autopilot") n = AUTOPILOT_THRESHOLD;
  else if (name === "yolo") n = YOLO_THRESHOLD;
  else {
    n = parseInt(name, 10);
    if (!Number.isInteger(n) || n < 0 || n > 10) {
      // 11 and 12 refused BY NAME, pointing at the word. Silently accepting them
      // would keep two vocabularies alive for the same thing.
      const hint =
        n === 11 ? `\n  11 is now:  autopilot`
        : n === 12 ? `\n  12 is now:  yolo`
        : `\n  words:      autopilot | yolo | oracle`;
      console.error(`setting must be 0-10, or a word (got "${nameRaw}")${hint}`);
      process.exit(2);
    }
  }

  // autopilot and yolo both need a goal. autopilot because its loop genuinely
  // cannot start without one; yolo because a stated intent is the only thing it
  // can still record about itself.
  let g = "";
  if (n === AUTOPILOT_THRESHOLD || n === YOLO_THRESHOLD) g = requireGoal(goal, name);

  // Choosing a dial setting or autopilot/yolo LEAVES Oracle mode. One selector,
  // one answer — no combination can leave two of them believing they are on.
  const wasOracle = modeState();
  if (wasOracle?.active) {
    rmSync(MODE_FILE, { force: true });
    console.log("  oracle mode off");
  }

  // ORDER MATTERS. The threshold is written only AFTER the loop actually starts.
  // Writing it first left a half-applied state on failure: the number said
  // autopilot while no loop was running, which is precisely the "the setting
  // lies about itself" bug this redesign exists to remove.
  if (n === AUTOPILOT_THRESHOLD) {
    // DELEGATE — never hand-write the sentinel.
    //
    // autopilot-activate.py does considerably more than drop a file: it runs a
    // preflight, scopes the sentinel to THIS session id, writes a paired
    // loop-state file, audits, and warns when the goal names paths outside the
    // project. An earlier draft of this function wrote the JSON itself and got
    // all of that wrong — most seriously the session scoping, which would have
    // switched autopilot on for every window in the project instead of one.
    // Absorbing the old command means routing to it, not reimplementing it.
    const r = Bun.spawnSync(
      ["python3", join(ROOT, ".claude", "scripts", "autopilot-activate.py"), "on", g],
      { cwd: ROOT, stdout: "inherit", stderr: "inherit" },
    );
    if (r.exitCode !== 0) {
      console.error(
        `\nautopilot-activate.py exited ${r.exitCode} — the loop did NOT start, ` +
        `so the setting was left unchanged.`,
      );
      process.exit(r.exitCode ?? 1);
    }
    writeFileSync(THRESHOLD_FILE, String(n) + "\n");
  } else {
    // Leaving any other rung must also leave the loop, or autopilot keeps
    // running invisibly under a threshold that says otherwise.
    //
    // Called UNCONDITIONALLY, and that is the fix for a real bug: this used to
    // be guarded by existsSync(".acos/state/autopilot-active"), but the sentinel
    // is SESSION-SCOPED — the actual name is `autopilot-active-<session-id>`.
    // The guard therefore never matched, the teardown never ran, and a live test
    // left autopilot switched on after dropping back to threshold 10. The script
    // is idempotent and reports its own no-op, so asking it every time is both
    // cheaper and safer than trying to guess the filename.
    const off = Bun.spawnSync(
      ["python3", join(ROOT, ".claude", "scripts", "autopilot-activate.py"), "off"],
      { cwd: ROOT, stdout: "pipe", stderr: "pipe" },
    );
    const said = new TextDecoder().decode(off.stdout);
    if (said.includes("DEACTIVATED")) console.log("  autopilot loop stopped");
    writeFileSync(THRESHOLD_FILE, String(n) + "\n");
  }

  auditCtl("threshold", { threshold: n, goal: g || null });
  const label =
    n === YOLO_THRESHOLD ? "allows everything, records nothing, bypasses hard blocks"
    : n === AUTOPILOT_THRESHOLD ? "allows, logs the truly destructive, runs the goal loop"
    : `ordinary scoring (auto-approve at or below ${n})`;
  const shown = n === YOLO_THRESHOLD ? "yolo" : n === AUTOPILOT_THRESHOLD ? "autopilot" : String(n);
  console.log(`${shown} — ${label}`);
  if (g) console.log(`  goal: ${g}`);
  if (n === AUTOPILOT_THRESHOLD) console.log(`  loop: stops on the goal marker, 150 iterations, or 5 idle turns`);
  if (n === YOLO_THRESHOLD) console.log(`  NOTE: nothing is judged under yolo. For autonomy WITH judgement: /acos-oracle-protocol oracle "<goal>"`);
}

function cmdStatus(): void {
  const st = modeState();
  const thr = currentThreshold();
  const ap = existsSync(AUTOPILOT_FILE);
  let today = 0, denies = 0;
  try {
    const stamp = new Date().toISOString().slice(0, 10);
    for (const line of readFileSync(VERDICTS, "utf8").split("\n")) {
      if (!line.trim()) continue;
      try {
        const v = JSON.parse(line);
        if (String(v.ts ?? "").startsWith(stamp)) {
          today++;
          if (v.decision === "deny") denies++;
        }
      } catch { /* skip a malformed line rather than lose the count */ }
    }
  } catch { /* no log yet */ }

  console.log(`project:   ${ROOT}`);
  console.log(`ORACLE:    ${st?.active ? "WATCHING" : "off"}`);
  if (st?.active) {
    console.log(`  goal:    ${st.goal}`);
    console.log(`  since:   ${st.started_at}`);
    console.log(`  on stop: threshold ${st.prev_threshold}`);
  }
  console.log(`threshold: ${thr}${thr === 12 ? " (YOLO)" : thr === 11 ? " (AUTOPILOT)" : ""}`);
  console.log(`autopilot: ${ap ? "loop running" : "off"}`);
  console.log(`daemon:    ${daemonAlive() ? "awake" : "asleep (starts on first gated call)"}`);
  console.log(`verdicts:  ${today} today, ${denies} denied`);
}

async function cmdFollow(): Promise<void> {
  console.log(`watching ${VERDICTS} — ctrl-c to stop\n`);
  let size = 0;
  try {
    size = readFileSync(VERDICTS, "utf8").length;
  } catch { /* file appears on the first verdict */ }
  for (;;) {
    try {
      const text = readFileSync(VERDICTS, "utf8");
      if (text.length > size) {
        for (const line of text.slice(size).split("\n")) {
          if (!line.trim()) continue;
          try {
            const v = JSON.parse(line);
            const mark = v.decision === "deny" ? "DENY " : "allow";
            console.log(`${v.ts}  ${mark}  ${v.tool}  ${String(v.detail ?? "").slice(0, 70)}`);
            console.log(`    ${v.reason}`);
          } catch {
            console.log(line);
          }
        }
        size = text.length;
      }
    } catch { /* log not there yet */ }
    await Bun.sleep(1000);
  }
}

// ---------------------------------------------------------------------------

// Guarded so the module can be IMPORTED (tests, other tools) without the act
// of importing it running a command — an unguarded dispatch made looksVague()
// untestable, because loading the file printed the help text and exited.
if (import.meta.main) {
  const [cmd, ...rest] = process.argv.slice(2);
  const arg = rest.join(" ").trim();

  switch (cmd) {
    case "oracle":
    case "start": await cmdStart(arg, "oracle"); break;
    case "stop": cmdStop(); break;
    case "status": cmdStatus(); break;
    case "follow": await cmdFollow(); break;
    case "autopilot": await cmdSet("autopilot", arg); break;
    case "yolo": await cmdSet("yolo", arg); break;
    case "threshold": {
      const [n, ...g] = rest;
      await cmdSet(n ?? "", g.join(" "));
      break;
    }
    default:
      if (cmd && /^\d+$/.test(cmd)) { await cmdSet(cmd, arg); break; }
      console.log(`oracle-ctl — the permission switch

    <1-10>                the dial: how loose ordinary scoring is
    autopilot "<goal>"    allows, logs the truly destructive, runs the goal loop
    yolo "<goal>"         allows everything, records nothing, bypasses hard blocks
    oracle "<goal>"       Opus judges every gated call; you are never asked

    stop                  leave oracle mode, back to the number you were on
    status                what is on right now, and today's verdict count
    follow                watch decisions as they happen

  Oracle mode is a switch, not a rung. The 1-12 dial measures how loose the rules
  are; the Oracle is a different axis, so it has no number.`);
  }
}
