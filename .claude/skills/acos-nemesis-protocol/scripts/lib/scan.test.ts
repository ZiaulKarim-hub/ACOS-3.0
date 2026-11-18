/**
 * scan.test.ts — the S3 scan's own behaviour, where getting it wrong is silent.
 *
 * SEC-38 is the reason this file exists. `bun audit` asks a remote service, so it can exit
 * non-zero either because it FOUND vulnerable packages or because it COULD NOT ASK. Both
 * arrived at the ledger as a bare `fail`, and a failed check blocks the protocol, so one
 * dropped packet was indistinguishable from a security hole. It happened once in 203 scans
 * with the text `Timeout: audit request failed`.
 *
 * These rows drive the real `runCommand` with a stand-in command, because the defect is in
 * how a non-zero exit is CLASSIFIED, not in bun. Each row counts the attempts on disk, so
 * "it retried" is measured rather than assumed.
 */
import { describe, expect, it } from "bun:test";
import { mkdtempSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { ADVISORY_PRESENT, DEPS_ATTEMPTS, detectToolchain, isRegistryOutage, parseAuditJson, renderAuditJson, runCommand, timeoutFor, wasKilledAtTimeout } from "./scan.ts";

/**
 * A command that records each run and then fails, writing `text` to the chosen stream.
 *
 * THE STREAM IS THE WHOLE POINT, so it is a required argument rather than a default.
 * Measured on bun 1.3.9: an audit that RAN prints its answer to stdout — `{}` when clean
 * under `--json`, a package-keyed object when not, "No vulnerabilities found" in prose mode
 * — while an audit that could not reach the registry prints nothing at all to stdout and
 * puts its message on stderr. The classifier reads that structural difference, so a fixture
 * that put everything on one stream would be testing a world the tool does not live in.
 */
function failing(dir: string, text: string, stream: "stdout" | "stderr"): { cmd: string; args: string[]; countFile: string } {
  const tag = Math.random().toString(36).slice(2);
  const countFile = join(dir, `runs-${tag}.txt`);
  // The payload goes through a FILE, never through the shell command string. Interpolating
  // it meant the fixture could not carry a double quote, which rules out the one output
  // shape that matters most here — a `--json` audit, which is nothing but double quotes.
  const payload = join(dir, `out-${tag}.txt`);
  writeFileSync(countFile, "");
  writeFileSync(payload, text);
  const redirect = stream === "stderr" ? " >&2" : "";
  return {
    cmd: "/bin/sh",
    args: ["-c", `printf 'x' >> "${countFile}"; cat "${payload}"${redirect}; exit 1`],
    countFile,
  };
}

const attempts = (f: string): number => (existsSync(f) ? readFileSync(f, "utf8").length : 0);

// The exact line the live ledger recorded for SEC-38.
const SEC38_TEXT = "Timeout: audit request failed";

// A real advisory, taken verbatim from the same project's earlier scan records.
const REAL_ADVISORY = "extract-zip <=2.0.1 high: extract-zip unvalidated symlink path traversal";

describe("the dependency audit separates an unreachable registry from a real finding (SEC-38)", () => {
  it("retries a transport failure, and still reports it as a failure, never a pass", () => {
    const dir = mkdtempSync(join(tmpdir(), "scan-deps-"));
    const f = failing(dir, SEC38_TEXT, "stderr");
    const r = runCommand(dir, { id: "deps", kind: "deps", cmd: f.cmd, args: f.args });

    // It must NOT pass. An audit that could not run is never clean.
    expect(r.status).toBe("fail");
    // It must say WHICH kind of failure this was, so the ledger is readable without a re-run.
    expect(r.output).toContain("REGISTRY UNREACHABLE");
    expect(r.output).toContain("NOT a vulnerability report");
    // And it must actually have retried, measured on disk rather than inferred.
    //
    // A LITERAL 3, deliberately, NOT the imported DEPS_ATTEMPTS. Comparing the observed
    // count against the same constant the code uses compares the code with itself: the
    // mutation that sets DEPS_ATTEMPTS to 1 deletes the retry entirely, and this row stayed
    // GREEN through it until the expected value stopped moving with the source. Measured
    // 2026-11-18, which is the only reason this comment is here rather than a tidier line.
    expect(attempts(f.countFile)).toBe(3);
    // Stated separately so the intent survives a future change to the number: whatever the
    // constant says, it has to mean "more than one go".
    expect(DEPS_ATTEMPTS).toBeGreaterThan(1);
  }, 30_000);

  it("does NOT retry or excuse a real advisory, which must fail on the first run", () => {
    const dir = mkdtempSync(join(tmpdir(), "scan-deps-"));
    const f = failing(dir, REAL_ADVISORY, "stdout");
    const r = runCommand(dir, { id: "deps", kind: "deps", cmd: f.cmd, args: f.args });

    expect(r.status).toBe("fail");
    expect(r.output).not.toContain("REGISTRY UNREACHABLE");
    expect(r.output).toContain("extract-zip");
    expect(attempts(f.countFile)).toBe(1);
  }, 30_000);

  it("retries nothing but the dependency audit, so a flaky test stays visible", () => {
    const dir = mkdtempSync(join(tmpdir(), "scan-test-"));
    const f = failing(dir, SEC38_TEXT, "stderr");
    // Same transport-shaped output, but this is the TEST check, not the deps check.
    const r = runCommand(dir, { id: "test", kind: "test", cmd: f.cmd, args: f.args });

    expect(r.status).toBe("fail");
    expect(r.output).not.toContain("REGISTRY UNREACHABLE");
    expect(attempts(f.countFile)).toBe(1);
  }, 30_000);
});

/**
 * SEC-43 and SEC-46, and why there is no transport word list left to test.
 *
 * The first fix for SEC-38 decided "was this an outage?" by searching the audit's whole
 * output for transport vocabulary — `timed out`, `ECONNRESET`, `socket hang up`, `request
 * failed`. SEC-43 showed that advisory TITLES use exactly those words, so a real finding
 * could be retried and stamped NOT a vulnerability report. SEC-46 showed the companion
 * guard was incomplete too: it knew `GHSA-` and `CVE-` but not `RUSTSEC-` or `PYSEC-`, so
 * a cargo or pip advisory titled "timeout" fell through it and was mislabelled anyway.
 *
 * The strings below are the adversarial cases that drove both findings, and every one of
 * them is now answered by a single structural fact: the tool PRINTED something to stdout,
 * so it reached the registry and answered, whatever its answer happens to say.
 */
describe("a real advisory is never excused as an outage, however it is worded (SEC-43)", () => {
  const ADVISORY_WITH_TRANSPORT_WORDS = [
    "basic-ftp <=5.3.0 high: basic-ftp vulnerable to denial of service via unbounded memory consumption in Client.list() - https://github.com/advisories/GHSA-rp42-5vxx-qpwr",
    "ws >=8.0.0 <8.20.1 moderate: ws: Uninitialized memory disclosure — connection reset by peer during handshake",
    "some-pkg <=1.2.3 high: request failed to time out, allowing a socket to be held open indefinitely - CVE-2026-12345",
    "1 vulnerabilities (1 high, 0 moderate) — the audit request failed to bound its timeout",
  ];

  it("refuses to call any of them an outage, because the audit ANSWERED on stdout", () => {
    for (const s of ADVISORY_WITH_TRANSPORT_WORDS) {
      expect(isRegistryOutage({ stdout: s, stderr: "" })).toBe(false);
    }
  });

  it("refuses even with stdout EMPTY, if the advisory landed on the wrong stream", () => {
    // The one case the stdout test cannot see, and the only reason ADVISORY_PRESENT
    // survives at all: a tool that reports its findings on stderr and prints nothing.
    for (const s of ADVISORY_WITH_TRANSPORT_WORDS) {
      expect(ADVISORY_PRESENT.test(s)).toBe(true);
      expect(isRegistryOutage({ stdout: "", stderr: s })).toBe(false);
    }
  });

  it("never calls a CLEAN run an outage, which is the costliest possible mix-up", () => {
    // Measured: a clean tree exits 0 with "No vulnerabilities found" in prose mode and
    // `{}` under --json. If either were read as an outage the scan would retry and then
    // fail a healthy project.
    expect(isRegistryOutage({ stdout: "No vulnerabilities found", stderr: "" })).toBe(false);
    expect(isRegistryOutage({ stdout: "{}", stderr: "" })).toBe(false);
  });

  it("does NOT excuse a report it simply does not recognise", () => {
    // The failure mode a loose fallback invites: anything unfamiliar becoming "oh, a blip".
    // An unrecognised report fails as what it is, so nobody is told the audit never ran.
    expect(isRegistryOutage({ stdout: "audit: unexpected manifest shape in bun.lock", stderr: "" })).toBe(false);
    expect(isRegistryOutage({ stdout: "panic: this should never happen", stderr: "" })).toBe(false);
  });

  it("does not excuse a report even when the report ITSELF talks about timeouts", () => {
    // The purest form of the SEC-43 defect: output that is nothing but transport words,
    // on stdout, from an audit that ran. Under the old word list this was retried three
    // times and relabelled. There is now no word list to consult.
    expect(isRegistryOutage({ stdout: "pkg: request timed out upstream; ECONNRESET; socket hang up", stderr: "" })).toBe(false);
  });

  it("still calls a bare transport failure an outage, so the SEC-38 repair survives", () => {
    // Measured on bun 1.3.9 — nothing on stdout, the message on stderr, non-zero exit.
    expect(isRegistryOutage({ stdout: "", stderr: "Timeout: audit request failed" })).toBe(true);
    expect(isRegistryOutage({ stdout: "   ", stderr: "ENOTFOUND registry.npmjs.org" })).toBe(true);
    expect(isRegistryOutage({ stdout: "", stderr: "ConnectionRefused: audit request failed" })).toBe(true);
  });

  it("does not retry or relabel an advisory that mentions a timeout, measured end to end", () => {
    // INDEX 2 IS DELIBERATE, and index 0 was wrong. The end-to-end row has to use a string
    // that would have tripped the OLD word list, or it proves nothing: index 0 says
    // "denial of service", which that list did not match, so this row stayed GREEN with
    // the advisory guard deleted outright. Index 2 says "request failed to time out" AND
    // carries a CVE. Measured 2026-11-18. This is SEC-43's registered reproduction.
    const dir = mkdtempSync(join(tmpdir(), "scan-sec43-"));
    const f = failing(dir, ADVISORY_WITH_TRANSPORT_WORDS[2] as string, "stdout");
    const r = runCommand(dir, { id: "deps", kind: "deps", cmd: f.cmd, args: f.args });

    expect(r.status).toBe("fail");
    expect(r.output).not.toContain("REGISTRY UNREACHABLE");
    expect(r.output).toContain("CVE-2026-12345");
    expect(attempts(f.countFile)).toBe(1);
  }, 30_000);
});

/**
 * SEC-46 — the ecosystems this machine cannot run.
 *
 * `cargo audit -q` and `pip-audit -q` are discovered by `detectToolchain`, but neither
 * `cargo-audit` nor `pip-audit` is installed here (checked 2026-11-18: `cargo audit` → "no
 * such command", `pip-audit` → not on PATH), so their exact output could not be measured.
 * Which is the whole point of the rows below: the verdict must not DEPEND on their wording.
 *
 * Each string is an INVENTED shape in the right general style, deliberately using
 * identifiers and phrasing the npm-flavoured marker list does not know, and every one of
 * them is correctly treated as an answer — because it was printed to stdout.
 */
describe("a prose audit from any ecosystem is an answer, whatever its vocabulary (SEC-46)", () => {
  const PROSE_ADVISORIES_WITH_TRANSPORT_WORDS = [
    "ID: RUSTSEC-2026-0041\nCrate: hyper\nTitle: request timed out handling can deadlock a worker\nSolution: No fixed upgrade is available!",
    "Found 2 known vulnerabilities in 1 package\nName Version ID Fix Versions\nurllib3 1.26.5 PYSEC-2026-77 1.26.19  (socket hang up on redirect)",
    "audit report: 1 issue — connection reset by peer is reachable from untrusted input",
  ];

  it("treats every one of them as an answer, so none is retried or relabelled", () => {
    for (const s of PROSE_ADVISORIES_WITH_TRANSPORT_WORDS) {
      expect(isRegistryOutage({ stdout: s, stderr: "" })).toBe(false);
    }
  });

  it("does so WITHOUT depending on the marker list, which is the SEC-46 lesson", () => {
    // The third string carries no identifier the marker list knows, no severity label and
    // no version range — it is recognised purely because the tool printed it. If the
    // verdict needed the marker list, this row would fail.
    const unrecognised = PROSE_ADVISORIES_WITH_TRANSPORT_WORDS[2] as string;
    expect(ADVISORY_PRESENT.test(unrecognised)).toBe(false);
    expect(isRegistryOutage({ stdout: unrecognised, stderr: "" })).toBe(false);
  });

  it("recognises RUSTSEC and PYSEC ids on stderr too, narrowing the residual", () => {
    // Belt and braces for the stderr-only case. Based on the published ID FORMAT, which is
    // stable and public — NOT on any claim about these tools' prose, which is unmeasured.
    expect(ADVISORY_PRESENT.test("RUSTSEC-2026-0041")).toBe(true);
    expect(ADVISORY_PRESENT.test("PYSEC-2026-77")).toBe(true);
    expect(ADVISORY_PRESENT.test("Found 2 known vulnerabilities")).toBe(true);
    expect(ADVISORY_PRESENT.test("Severity: 7.5 (high)")).toBe(true);
    // And it must still refuse the transport messages, or a real outage stops being retried.
    for (const s of ["Timeout: audit request failed", "ConnectionRefused: audit request failed", "ENOTFOUND registry.npmjs.org"])
      expect(ADVISORY_PRESENT.test(s)).toBe(false);
  });

  it("end to end: a RUSTSEC-style report fails once and keeps its own words", () => {
    const dir = mkdtempSync(join(tmpdir(), "scan-sec46-"));
    const f = failing(dir, PROSE_ADVISORIES_WITH_TRANSPORT_WORDS[0] as string, "stdout");
    const r = runCommand(dir, { id: "deps", kind: "deps", cmd: f.cmd, args: f.args });

    expect(r.status).toBe("fail");
    expect(r.output).not.toContain("REGISTRY UNREACHABLE");
    expect(r.output).toContain("RUSTSEC-2026-0041");
    expect(attempts(f.countFile)).toBe(1);
  }, 30_000);
});

/**
 * `--json` and what it is actually for.
 *
 * Every string below was MEASURED from `bun audit --json` on bun 1.3.9 on 2026-11-18, in a
 * throwaway project pinned to `extract-zip@1.6.6`:
 *
 *   clean ............. exit 0, stdout `{}`                      (3 bytes)
 *   advisories found .. exit 1, stdout an object keyed by package (1157 bytes)
 *   unreachable ....... exit 1, stdout ZERO bytes, `ConnectionRefused: audit request
 *                       failed` on stderr
 *
 * The unreachable line was produced by pointing `BUN_CONFIG_REGISTRY` at a closed port AND
 * at a non-resolving host; bun reports BOTH as `ConnectionRefused`, so that one string is
 * the real text for two different transport failures.
 *
 * HONEST SCOPE. `--json` does NOT decide anything — the stdout test already separates all
 * three states, and a parse in front of it was provably dead code. What `--json` earns its
 * place for is the RECORD: `renderAuditJson` turns the machine shape into lines naming the
 * package, the affected range, the severity, the title and the advisory URL, which is more
 * than the prose table carried and is what a person reads when deciding what to fix.
 */
const AUDIT_JSON_CLEAN = "{}";

const AUDIT_JSON_FINDINGS =
  '{"extract-zip":[{"id":1139346,"url":"https://github.com/advisories/GHSA-jmr9-qjv8-65gv","title":"extract-zip unvalidated symlink path traversal","severity":"high","vulnerable_versions":"<=2.0.1","cwe":["CWE-22"],"cvss":{"score":8.1,"vectorString":"CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:N"}}],"minimist":[{"id":1097677,"url":"https://github.com/advisories/GHSA-xvch-5gv4-984h","title":"Prototype Pollution in minimist","severity":"critical","vulnerable_versions":"<0.2.4","cwe":["CWE-1321"],"cvss":{"score":9.8,"vectorString":"CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"}}]}';

const AUDIT_UNREACHABLE_STDERR = "ConnectionRefused: audit request failed";

describe("the measured --json shapes are classified correctly (SEC-43)", () => {
  it("reads the measured CLEAN result as an answer, so it is never an outage", () => {
    expect(parseAuditJson(AUDIT_JSON_CLEAN)).toEqual({});
    expect(isRegistryOutage({ stdout: AUDIT_JSON_CLEAN, stderr: "" })).toBe(false);
  });

  it("reads the measured FINDINGS result as an answer", () => {
    const parsed = parseAuditJson(AUDIT_JSON_FINDINGS);
    expect(parsed).not.toBeNull();
    expect(Object.keys(parsed as object).sort()).toEqual(["extract-zip", "minimist"]);
    expect(isRegistryOutage({ stdout: AUDIT_JSON_FINDINGS, stderr: "" })).toBe(false);
  });

  it("reads the measured UNREACHABLE shape as no answer at all", () => {
    expect(parseAuditJson("")).toBeNull();
    expect(isRegistryOutage({ stdout: "", stderr: AUDIT_UNREACHABLE_STDERR })).toBe(true);
  });

  /**
   * The parse feeds the RECORD, so a wrong parse writes a wrong record. `null`, `0` and
   * `""` are all VALID JSON, and a tool that printed any of them has not reported an
   * audit. An array is refused for the same reason: no audit on record emits one, and
   * quietly accepting shapes nobody emits is how a strict check becomes a loose one.
   */
  it("counts only a JSON OBJECT as an answer, never every valid JSON document", () => {
    for (const s of ["null", "0", '""', "[]", "[1,2]", "true", "not json at all", "{", '{"a":'])
      expect(parseAuditJson(s)).toBeNull();
    expect(parseAuditJson('{"pkg":[]}')).toEqual({ pkg: [] });
  });

  it("records the findings READABLY, so adding --json did not degrade the ledger", () => {
    const rendered = renderAuditJson(AUDIT_JSON_FINDINGS) as string;
    expect(rendered).toContain("2 advisory/advisories in 2 package(s)");
    // Each line has to carry what a reader needs to act: package, range, severity, title, URL.
    expect(rendered).toContain("extract-zip <=2.0.1 high: extract-zip unvalidated symlink path traversal");
    expect(rendered).toContain("https://github.com/advisories/GHSA-xvch-5gv4-984h");
    expect(rendered).toContain("minimist <0.2.4 critical:");
    // A clean audit says so in words rather than printing "{}" into the record.
    expect(renderAuditJson(AUDIT_JSON_CLEAN)).toBe("no advisories");
    // Anything that is not an audit's JSON is left alone, so the raw text survives.
    expect(renderAuditJson("Timeout: audit request failed")).toBeNull();
    expect(renderAuditJson('{"pkg":"not-an-array"}')).toBeNull();
  });

  it("end to end: a --json findings report fails ONCE and is recorded in prose", () => {
    const dir = mkdtempSync(join(tmpdir(), "scan-json-"));
    const f = failing(dir, AUDIT_JSON_FINDINGS, "stdout");
    const r = runCommand(dir, { id: "deps", kind: "deps", cmd: f.cmd, args: f.args });

    expect(r.status).toBe("fail");
    expect(r.output).not.toContain("REGISTRY UNREACHABLE");
    expect(r.output).toContain("extract-zip <=2.0.1 high:");
    expect(r.output).toContain("GHSA-xvch-5gv4-984h");
    // The record is the readable form, not the machine one.
    expect(r.output).not.toContain('"vectorString"');
    expect(attempts(f.countFile)).toBe(1);
  }, 30_000);

  it("end to end: the measured unreachable shape retries and is named as unreachable", () => {
    const dir = mkdtempSync(join(tmpdir(), "scan-json-"));
    // Exactly what bun 1.3.9 does: nothing on stdout, its own message on stderr.
    const f = failing(dir, AUDIT_UNREACHABLE_STDERR, "stderr");
    const r = runCommand(dir, { id: "deps", kind: "deps", cmd: f.cmd, args: f.args });

    expect(r.status).toBe("fail");
    expect(r.output).toContain("REGISTRY UNREACHABLE");
    expect(r.output).toContain("NOT a vulnerability report");
    expect(attempts(f.countFile)).toBe(3);
  }, 30_000);
});
/**
 * The repair has to be visible where the audit is BUILT, not only where its output is read.
 *
 * Measured 2026-11-18: removing `--json` from the discovered command — reverting SEC-43's
 * repair at its source — passed every other row in this file, because nothing asserted how
 * the deps check is assembled. A classifier that can read a structured result is no repair
 * at all if the command never asks for one.
 */
describe("the discovered dependency audit asks for a structured result (SEC-43)", () => {
  const project = (files: Record<string, string>): string => {
    const dir = mkdtempSync(join(tmpdir(), "scan-detect-"));
    for (const [name, body] of Object.entries(files)) writeFileSync(join(dir, name), body);
    return dir;
  };
  const deps = (dir: string) => detectToolchain(dir).find((c) => c.id === "deps");

  it("passes --json on the bun path, which is the path this repo is on", () => {
    const dir = project({ "package.json": '{"name":"p","private":true}', "bun.lock": "{}" });
    const c = deps(dir);
    expect(c?.cmd).toBe("bun");
    expect(c?.args).toEqual(["audit", "--json"]);
  });

  it("leaves the npm path exactly as it was, because its shape is UNMEASURED", () => {
    // Not an oversight. bun 1.3.9's three-way behaviour was measured here; npm's was not,
    // and the classifier's prose fallback already covers it. Guessing would be the defect.
    const dir = project({ "package.json": '{"name":"p","private":true}' });
    const c = deps(dir);
    expect(c?.cmd).toBe("npm");
    expect(c?.args).toEqual(["audit", "--audit-level=high"]);
  });

  it("still lets a project name its own audit, which the repair must not hijack", () => {
    const dir = project({ "package.json": '{"name":"p","private":true,"scripts":{"audit":"my-audit"}}', "bun.lock": "{}" });
    const c = deps(dir);
    expect(c?.cmd).toBe("bun");
    expect(c?.args).toEqual(["run", "audit"]);
  });
});

/**
 * FUN-135 — the timeout path, which the SEC-38 retry inherited and nobody had tested.
 *
 * MEASURED 2026-11-18, because the finding's own account was partly wrong and acting on it
 * unchecked would have produced a fix for a bug that was not there. `spawnSync` killed at
 * its timeout returns `status: null`, `signal: "SIGTERM"`, `error.code: "ETIMEDOUT"` and
 * EMPTY streams. `null !== 0`, and empty stdout is an outage, so the retry loop DID already
 * cover it — the finding's claim that it "is not retried" does not hold.
 *
 * What did hold, and was worse than reported:
 *   - the record said "timed out after Ns" rather than naming the audit as unperformed, so
 *     the one case SEC-38 exists for read like an ordinary slow check;
 *   - the ceiling was `CHECK_TIMEOUT_MS`, TWENTY MINUTES, sized for a test suite. Three
 *     attempts was a worst case of one hour on a single check, not the "3×timeout" of the
 *     finding, with nothing bounding it;
 *   - and the quoted figure came from the global constant, so once the audit got its own
 *     ceiling the ledger would have printed a number ten times too large.
 *
 * These rows drive the real `runCommand` with tiny ceilings through its `limits` argument,
 * which is why they take milliseconds rather than minutes.
 */
describe("a dependency audit that never finishes is named, and bounded (FUN-135)", () => {
  const hangs = (dir: string): { cmd: string; args: string[]; countFile: string } => {
    const countFile = join(dir, `runs-${Math.random().toString(36).slice(2)}.txt`);
    writeFileSync(countFile, "");
    return { cmd: "/bin/sh", args: ["-c", `printf 'x' >> "${countFile}"; sleep 30`], countFile };
  };

  it("gives an audit a far shorter ceiling than a test suite", () => {
    expect(timeoutFor("deps")).toBe(2 * 60 * 1000);
    expect(timeoutFor("test")).toBe(20 * 60 * 1000);
    expect(timeoutFor("typecheck")).toBe(20 * 60 * 1000);
    // The relationship, stated separately so it survives a change to either number: an
    // audit is one request and must never inherit the ceiling meant for a compile.
    expect(timeoutFor("deps")).toBeLessThan(timeoutFor("test"));
  });

  it("records a timed-out audit as unperformed, not as an ordinary slow check", () => {
    const dir = mkdtempSync(join(tmpdir(), "scan-timeout-"));
    const f = hangs(dir);
    const r = runCommand(dir, { id: "deps", kind: "deps", cmd: f.cmd, args: f.args }, { timeoutMs: 250, budgetMs: 1 });

    expect(r.status).toBe("fail");
    expect(r.output).toContain("REGISTRY UNREACHABLE");
    expect(r.output).toContain("did not finish within 0.25s");
    expect(r.output).toContain("NOT a vulnerability report");
  }, 30_000);

  it("quotes the ceiling that ACTUALLY applied, not the global one", () => {
    const dir = mkdtempSync(join(tmpdir(), "scan-timeout-"));
    const f = hangs(dir);
    const r = runCommand(dir, { id: "deps", kind: "deps", cmd: f.cmd, args: f.args }, { timeoutMs: 250, budgetMs: 1 });
    // 1200s is CHECK_TIMEOUT_MS. If it appears here the ledger is lying about the wait.
    expect(r.output).not.toContain("1200s");
  }, 30_000);

  it("still says plainly 'timed out' for a check that is NOT an audit", () => {
    const dir = mkdtempSync(join(tmpdir(), "scan-timeout-"));
    const f = hangs(dir);
    const r = runCommand(dir, { id: "test", kind: "test", cmd: f.cmd, args: f.args }, { timeoutMs: 250 });

    expect(r.status).toBe("fail");
    expect(r.output).toContain("timed out after 0.25s");
    // A slow test suite is not a registry problem and must never be dressed as one.
    expect(r.output).not.toContain("REGISTRY UNREACHABLE");
    // And it is never retried: a flaky test is a defect worth seeing.
    expect(attempts(f.countFile)).toBe(1);
  }, 30_000);

  it("starts NO further attempt once the retry budget is spent", () => {
    const dir = mkdtempSync(join(tmpdir(), "scan-timeout-"));
    const f = hangs(dir);
    // One 250 ms attempt already overruns a 1 ms budget, so there must be exactly one.
    const r = runCommand(dir, { id: "deps", kind: "deps", cmd: f.cmd, args: f.args }, { timeoutMs: 250, budgetMs: 1 });

    expect(r.status).toBe("fail");
    expect(attempts(f.countFile)).toBe(1);
    expect(r.output).toContain("after 1 attempt(s)");
  }, 30_000);

  it("does retry up to the cap when the budget allows it, so the bound is not a block", () => {
    const dir = mkdtempSync(join(tmpdir(), "scan-timeout-"));
    const f = hangs(dir);
    const r = runCommand(dir, { id: "deps", kind: "deps", cmd: f.cmd, args: f.args }, { timeoutMs: 250, budgetMs: 60_000 });

    expect(r.status).toBe("fail");
    expect(attempts(f.countFile)).toBe(DEPS_ATTEMPTS);
    expect(r.output).toContain(`after ${DEPS_ATTEMPTS} attempt(s)`);
  }, 30_000);

  it("leaves the real ceilings in force when nothing is passed", () => {
    // The seam must not become the behaviour. A caller that passes no limits gets the
    // production numbers, which is what the scan itself does.
    const dir = mkdtempSync(join(tmpdir(), "scan-timeout-"));
    const f = failing(dir, "{}", "stdout");
    const r = runCommand(dir, { id: "deps", kind: "deps", cmd: f.cmd, args: f.args });
    // `{}` on stdout is an answer, so this returns at once and proves no ceiling was needed.
    expect(r.status).toBe("fail");
    expect(attempts(f.countFile)).toBe(1);
  }, 30_000);
});

/**
 * FUN-142 — the retry and the record have to agree about what happened.
 *
 * `isRegistryOutage` reads the OUTPUT. A child killed at its ceiling after printing a
 * banner, or half a JSON chunk, looks by output alone like a tool that answered, so it was
 * not retried — while the very next line of the record correctly called it unreachable. One
 * event, two verdicts, because only the label could see the kill.
 */
describe("a killed audit is retried whatever it printed first (FUN-142)", () => {
  const hangsAfterPrinting = (dir: string, text: string): { cmd: string; args: string[]; countFile: string } => {
    const countFile = join(dir, `runs-${Math.random().toString(36).slice(2)}.txt`);
    writeFileSync(countFile, "");
    const payload = join(dir, `out-${Math.random().toString(36).slice(2)}.txt`);
    writeFileSync(payload, text);
    return { cmd: "/bin/sh", args: ["-c", `printf 'x' >> "${countFile}"; cat "${payload}"; sleep 30`], countFile };
  };

  it("sees the kill in error.code, not in the text it managed to print", () => {
    expect(wasKilledAtTimeout({ error: { code: "ETIMEDOUT" } })).toBe(true);
    expect(wasKilledAtTimeout({ error: { code: "ENOENT" } })).toBe(false);
    expect(wasKilledAtTimeout({})).toBe(false);
    expect(wasKilledAtTimeout({ error: undefined })).toBe(false);
  });

  it("retries an audit killed after printing a BANNER, which output alone calls an answer", () => {
    const dir = mkdtempSync(join(tmpdir(), "scan-fun142-"));
    // A banner is not an answer, but it is non-empty stdout, so isRegistryOutage says
    // "answered". Only the kill tells the truth.
    const f = hangsAfterPrinting(dir, "bun audit v1.3.9 (cf6cdbbb)");
    expect(isRegistryOutage({ stdout: "bun audit v1.3.9 (cf6cdbbb)", stderr: "" })).toBe(false);

    const r = runCommand(dir, { id: "deps", kind: "deps", cmd: f.cmd, args: f.args }, { timeoutMs: 250, budgetMs: 60_000 });
    expect(r.status).toBe("fail");
    expect(attempts(f.countFile)).toBe(DEPS_ATTEMPTS);
    expect(r.output).toContain("REGISTRY UNREACHABLE");
  }, 30_000);

  it("retries an audit killed mid-JSON, where the partial chunk even parses as nothing", () => {
    const dir = mkdtempSync(join(tmpdir(), "scan-fun142-"));
    const partial = '{"extract-zip":[{"id":1139346,"url":"https://github.com/advisor';
    const f = hangsAfterPrinting(dir, partial);
    // The chunk is non-empty and unparseable: an answer by the output test, nothing by the parse.
    expect(parseAuditJson(partial)).toBeNull();
    expect(isRegistryOutage({ stdout: partial, stderr: "" })).toBe(false);

    const r = runCommand(dir, { id: "deps", kind: "deps", cmd: f.cmd, args: f.args }, { timeoutMs: 250, budgetMs: 60_000 });
    expect(r.status).toBe("fail");
    expect(attempts(f.countFile)).toBe(DEPS_ATTEMPTS);
  }, 30_000);

  it("does NOT retry a non-audit check that was killed, however much it printed", () => {
    const dir = mkdtempSync(join(tmpdir(), "scan-fun142-"));
    const f = hangsAfterPrinting(dir, "running 412 tests");
    const r = runCommand(dir, { id: "test", kind: "test", cmd: f.cmd, args: f.args }, { timeoutMs: 250, budgetMs: 60_000 });

    expect(r.status).toBe("fail");
    expect(r.output).toContain("timed out after 0.25s");
    expect(attempts(f.countFile)).toBe(1);
  }, 30_000);

  it("does not retry an audit that exited 0, so a clean pass is never spent three times", () => {
    // EXIT 0 WITH EMPTY STDOUT, deliberately. An earlier version of this row printed `{}`,
    // which the output test already calls an answer, so it never reached the exit-code guard
    // at all: removing `r.status !== 0` from the loop condition left it GREEN. Measured
    // 2026-11-18. Empty stdout is the one shape where only the exit code can speak.
    const dir = mkdtempSync(join(tmpdir(), "scan-fun142-"));
    const countFile = join(dir, "runs.txt");
    writeFileSync(countFile, "");
    const r = runCommand(dir, {
      id: "deps", kind: "deps", cmd: "/bin/sh",
      args: ["-c", `printf 'x' >> "${countFile}"; exit 0`],
    });
    // The tool said it succeeded. That is the end of it — no retry, and a pass.
    expect(r.status).toBe("pass");
    expect(attempts(countFile)).toBe(1);
  }, 30_000);
});
