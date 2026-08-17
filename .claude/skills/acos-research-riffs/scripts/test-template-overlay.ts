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
 * ONE EXCEPTION, added 2026-08-17: probe-charter.md and researcher-charter.md
 * must agree on which corpus they point at. An overlay carrying the first but
 * not the second used to fall through silently, so every PANEL SEAT rendered
 * the engine's web charter while the one-shot probe read files — hit live in a
 * depth-5 /investigate run. resolveTemplate now throws on that pair, and only
 * that pair.
 *
 * Kept separate from test-riff.ts (an end-to-end CLI smoke test) so a unit-level
 * contract does not require standing up a session.
 *
 * Run:  bun .claude/skills/acos-research-riffs/scripts/test-template-overlay.ts
 */

import { mkdtempSync, rmSync, writeFileSync, existsSync, readFileSync } from "node:fs";
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
    // researcher-charter.md is deliberately NOT in this list — see the paired
    // block below. Every other charter still falls through silently.
    for (const name of [
      "auditor-charter.md",
      "compiler-charter.md",
      "citer-charter.md",
      "eval-rubric.md",
    ]) {
      eq(`overlay lacks ${name} → falls back`, resolveTemplate(name), join(TEMPLATE_DIR, name));
      check(`${name} fallback actually exists on disk`, existsSync(resolveTemplate(name)));
    }
  }

  // ── the probe/researcher PAIR must agree on its corpus ─────────────────────
  // An overlay that rewords probe-charter.md has declared a different corpus.
  // Letting researcher-charter.md fall through then aims every panel seat at
  // the web. That half-installed state is an error, not a fallback.
  {
    setEnv(tmp); // tmp carries probe-charter.md only
    let threw = false;
    let msg = "";
    try {
      resolveTemplate("researcher-charter.md");
    } catch (e) {
      threw = true;
      msg = e instanceof Error ? e.message : String(e);
    }
    check("overlay has probe but not researcher → THROWS", threw);
    check("the error names the missing file", msg.includes("researcher-charter.md"));
    check("the error names the overlay dir", msg.includes(tmp));
    check("the error explains the web-charter consequence", msg.includes("WEB"));
  }

  // ── both halves present → both resolve to the overlay ──────────────────────
  {
    const both = mkdtempSync(join(tmpdir(), "riff-overlay-both-"));
    try {
      writeFileSync(join(both, "probe-charter.md"), "# probe\n");
      writeFileSync(join(both, "researcher-charter.md"), "# researcher\n");
      setEnv(both);
      eq(
        "complete overlay → probe from overlay",
        resolveTemplate("probe-charter.md"),
        join(both, "probe-charter.md"),
      );
      eq(
        "complete overlay → researcher from overlay",
        resolveTemplate("researcher-charter.md"),
        join(both, "researcher-charter.md"),
      );
      eq(
        "complete overlay → citer still inherited",
        resolveTemplate("citer-charter.md"),
        join(TEMPLATE_DIR, "citer-charter.md"),
      );
    } finally {
      rmSync(both, { recursive: true, force: true });
    }
  }

  // ── the guard is ONE-DIRECTIONAL and narrow ────────────────────────────────
  // An overlay with neither half is an ordinary overlay: nothing has declared a
  // different corpus, so researcher falls through exactly as before. And an
  // overlay carrying only researcher does not force a probe — the pair is
  // checked in one direction, so this stays a fallback and not a new demand.
  {
    const neither = mkdtempSync(join(tmpdir(), "riff-overlay-none-"));
    const onlyResearcher = mkdtempSync(join(tmpdir(), "riff-overlay-res-"));
    try {
      writeFileSync(join(neither, "citer-charter.md"), "# citer\n");
      setEnv(neither);
      eq(
        "overlay declares no probe → researcher still falls back",
        resolveTemplate("researcher-charter.md"),
        join(TEMPLATE_DIR, "researcher-charter.md"),
      );

      writeFileSync(join(onlyResearcher, "researcher-charter.md"), "# researcher\n");
      setEnv(onlyResearcher);
      eq(
        "overlay with only researcher → probe still falls back",
        resolveTemplate("probe-charter.md"),
        join(TEMPLATE_DIR, "probe-charter.md"),
      );
      eq(
        "overlay with only researcher → researcher from overlay",
        resolveTemplate("researcher-charter.md"),
        join(onlyResearcher, "researcher-charter.md"),
      );
    } finally {
      rmSync(neither, { recursive: true, force: true });
      rmSync(onlyResearcher, { recursive: true, force: true });
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
      // The defect this guard exists for: seats must NOT get the web charter.
      eq(
        "/investigate overlay resolves its own SEAT charter",
        resolveTemplate("researcher-charter.md"),
        join(real, "researcher-charter.md"),
      );
      const seatText = readFileSync(resolveTemplate("researcher-charter.md"), "utf8");
      check("seat charter does not tell readers to search WIDE", !seatText.includes("search WIDE"));
      check(
        "seat charter does not carry the web tier ladder",
        !seatText.includes("Tier 1 authoritative"),
      );
      check(
        "seat charter names the artifact itself as Tier 1",
        seatText.includes("Tier 1 — the artifact itself"),
      );
    } else {
      console.log("note: /investigate overlay not installed — skipped 6 checks");
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
