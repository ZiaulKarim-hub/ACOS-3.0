import { spawnSync } from "node:child_process";
/**
 * gate-env.ts — the environment the quality gates give to the programs they run (SEC-35).
 *
 * THE DEFECT, AND IT WAS MEASURED RATHER THAN REASONED ABOUT. These gates spawn bun to run
 * the suites and the compiler, and they used to hand it this process's whole environment.
 * On the bun installed here, 1.3.9:
 *
 *     BUN_OPTIONS="--preload ./pre.ts" bun -e 'console.log("main ran")'
 *     → PRELOADED
 *     → main ran
 *
 * So anything that can set one variable in the gate's environment can make bun load a file
 * of its choosing first, and that file can stub `bun:test`, replace the reporter or exit 0
 * before a single assertion runs. The gate would report every suite green while running
 * nothing. The same class as the PATH lookups already fixed for `ps` (SEC-14), `doppler`
 * (SEC-26), `bun audit` (FUN-73) and the gates' own interpreter (SEC-30, SEC-32): the
 * caller's environment decides what the gate actually executes. (`NODE_OPTIONS=--require`
 * was measured on the same bun and is NOT honoured — which is exactly why a list of known
 * dangerous names would be the wrong fix: it would have to be revised for every runtime
 * release, and a gate must not depend on that revision happening.)
 *
 * SO IT IS AN ALLOWLIST. Only names the suites genuinely need survive, and anything new a
 * runtime invents arrives excluded. Each one is here for a stated reason:
 *
 *   PATH    the suites spawn absolute binaries, but `bun audit` resolves its own network
 *           tooling, and a child with no PATH at all behaves differently from a real run.
 *   HOME    several rows read `os.homedir()` — the account door's own path is under it.
 *   TMPDIR  `os.tmpdir()` reads it; without it macOS tests fall back to /tmp, which is a
 *           different directory with different permissions from the per-user one.
 *   LANG, LC_ALL, TERM  text output and the pty row's terminal handling.
 *   USER    read by one shell script under test.
 *
 * WHAT IT DOES NOT CLAIM. A process that can set the gate's environment can usually also
 * edit the gate's own files, and nothing here stops that; the PostToolUse scan and the
 * judge do. This closes the cheapest route — one variable, no file touched, no trace in
 * the diff — not the whole class.
 */
export const GATE_ENV_ALLOW = ["PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "TERM", "USER"] as const;

/** The allowed names that are actually set, and nothing else. */
export function gateEnv(from: Record<string, string | undefined> = process.env): Record<string, string> {
  const out: Record<string, string> = {};
  for (const name of GATE_ENV_ALLOW) {
    const value = from[name];
    if (typeof value === "string") out[name] = value;
  }
  return out;
}

/**
 * THE ONE PLACE A GATE STARTS A PROGRAM, so the cleaned environment cannot be forgotten.
 *
 * The first fix passed `env: gateEnv()` at each call site and a test row checked that it
 * was there. The judge was right to refuse it: the row read the text `spawnSync(`, so a
 * later `execFileSync`, `Bun.spawn` or an aliased import would have inherited the whole
 * environment again and the row would have stayed green — the same silent regression the
 * row existed to catch. A single wrapper removes the possibility instead of policing it,
 * and the rows can then say something much simpler and stronger: the gates import no
 * process-starting API at all.
 */
export interface GateRun {
  stdout: string;
  stderr: string;
  status: number | null;
  signal: string | null;
  error?: Error;
}

export function runGate(cmd: string, args: string[], opts: { cwd: string }): GateRun {
  const r = spawnSync(cmd, args, {
    cwd: opts.cwd, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"], env: gateEnv(),
  });
  return {
    stdout: r.stdout ?? "",
    stderr: r.stderr ?? "",
    status: r.status,
    signal: r.signal,
    ...(r.error === undefined || r.error === null ? {} : { error: r.error }),
  };
}
