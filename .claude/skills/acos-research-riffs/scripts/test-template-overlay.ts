#!/usr/bin/env bun
/**
 * Focused test for the RIFF_TEMPLATE_DIR charter overlay (lib/panel.ts).
 *
 * The overlay exists so a launcher can drive this engine at a different corpus
 * without forking every charter: /investigate reads files where /research reads
 * the web, so it reasons over the SAME claims/tiers/gates but needs its own
 * probe-charter.md. The contract under test is that the override is per-FILE
 * with fallback — NOT a whole-directory swap, which would force every overlay
 * to vendor all five templates and would break silently whenever a sixth
 * template is added here.
 *
 * Kept separate from test-riff.ts (an end-to-end CLI smoke test) so a unit-level
 * contract does not require standing up a session.
 *
 * Run:  bun .claude/skills/acos-research-riffs/scripts/test-template-overlay.ts
 */

import { mkdtempSync, rmSync, writeFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { resolveTemplate, TEMPLATE_DIR } from "./lib/panel.ts";

let passed = 0;
let failed = 0;

function check(name: string, cond: boolean): void {
  if (cond) passed++;
  else {
    failed++;
    console.error(`FAIL: ${name}`);
  }
}
function eq(name: string, got: unknown, want: unknown): void {
  check(
    `${name} (got ${JSON.stringify(got)}, want ${JSON.stringify(want)})`,
    JSON.stringify(got) === JSON.stringify(want),
  );
}

const ORIGINAL = process.env["RIFF_TEMPLATE_DIR"];
function setEnv(v: string | undefined): void {
  if (v === undefined) delete process.env["RIFF_TEMPLATE_DIR"];
  else process.env["RIFF_TEMPLATE_DIR"] = v;
}

const tmp = mkdtempSync(join(tmpdir(), "riff-overlay-"));
try {
  // The overlay dir carries ONE charter; the other four must still resolve to
  // the engine's own templates/.
  const overlaid = join(tmp, "probe-charter.md");
  writeFileSync(overlaid, "# overlaid probe charter\n");

  // ── unset env → byte-identical to pre-overlay behaviour ────────────────────
  {
    setEnv(undefined);
    eq(
      "unset env → engine probe charter",
      resolveTemplate("probe-charter.md"),
      join(TEMPLATE_DIR, "probe-charter.md"),
    );
    eq(
      "unset env → engine auditor charter",
      resolveTemplate("auditor-charter.md"),
      join(TEMPLATE_DIR, "auditor-charter.md"),
    );
  }

  // ── env set, file PRESENT in overlay → overlay wins ────────────────────────
  {
    setEnv(tmp);
    eq("overlay has the file → overlay wins", resolveTemplate("probe-charter.md"), overlaid);
  }

  // ── env set, file ABSENT from overlay → falls through to the engine ────────
  // This is the whole reason the override is per-file. A whole-dir swap would
  // return a non-existent path here and throw "missing template" at render time.
  {
    setEnv(tmp);
    for (const name of [
      "auditor-charter.md",
      "compiler-charter.md",
      "citer-charter.md",
      "researcher-charter.md",
      "eval-rubric.md",
    ]) {
      eq(`overlay lacks ${name} → falls back`, resolveTemplate(name), join(TEMPLATE_DIR, name));
      check(`${name} fallback actually exists on disk`, existsSync(resolveTemplate(name)));
    }
  }

  // ── env pointing at a directory that does not exist → falls back ───────────
  {
    setEnv(join(tmp, "no-such-dir"));
    eq(
      "nonexistent overlay dir → falls back",
      resolveTemplate("probe-charter.md"),
      join(TEMPLATE_DIR, "probe-charter.md"),
    );
  }

  // ── env set to empty string → treated as unset, never join("", name) ───────
  {
    setEnv("");
    eq(
      "empty env → falls back (not a bare relative path)",
      resolveTemplate("probe-charter.md"),
      join(TEMPLATE_DIR, "probe-charter.md"),
    );
  }

  // ── the real /investigate overlay, if installed, resolves its probe ────────
  // Not a hard requirement of the engine, so absence is skipped, not failed.
  {
    const real = join(
      process.env["HOME"] ?? "",
      ".claude",
      "skills",
      "investigate",
      "templates",
    );
    if (existsSync(join(real, "probe-charter.md"))) {
      setEnv(real);
      eq(
        "/investigate overlay resolves its own probe charter",
        resolveTemplate("probe-charter.md"),
        join(real, "probe-charter.md"),
      );
      eq(
        "/investigate overlay still inherits the citer charter",
        resolveTemplate("citer-charter.md"),
        join(TEMPLATE_DIR, "citer-charter.md"),
      );
    } else {
      console.log("note: /investigate overlay not installed — skipped 2 checks");
    }
  }
} finally {
  setEnv(ORIGINAL);
  rmSync(tmp, { recursive: true, force: true });
}

if (failed > 0) {
  console.error(`\n${failed} FAILED, ${passed} passed`);
  process.exit(1);
}
console.log(`All ${passed} checks passed`);
