#!/usr/bin/env bun
/**
 * capture.ts — Phase 0 dirty-room capture driver (runs ON-MACHINE ONLY).
 *
 * Records the observable truth of a LIVE app across the auth-role sweep:
 * structure (routes/screens), behavior (HAR network log), screenshots, and the
 * accessibility (AX) tree per role. Output feeds the intent extractors and the
 * dirty-fingerprint. Server-invisible behavior (cron/emails/webhooks/rate-limits)
 * is NOT guessed here — it is probed separately and confidence-flagged.
 *
 * Requires Playwright:  cd .claude/skills/acos-reverse-cleanroom/scripts && bun add playwright && bunx playwright install chromium
 *
 * Usage:
 *   bun capture.ts --base https://app.example.com --out <session-dir>/00-capture \
 *       --roles anon,user,admin --seed /,/dashboard,/settings
 *
 * Auth: for a role other than `anon`, provide a storage-state JSON captured by a
 * human login (Playwright `storageState`) at --state-<role> <path>. The skill
 * NEVER automates a login-wall bypass (CFAA/DMCA-1201 exposure) — a human logs in
 * once and exports the session state.
 */

import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

type Args = Record<string, string>;
function parseArgs(argv: string[]): Args {
  const a: Args = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith("--")) a[argv[i].slice(2)] = argv[i + 1] ?? "true";
  }
  return a;
}

/**
 * Build a layer-gate from --layers <comma list>. When --layers is ABSENT, everything is
 * wanted (back-compat: capture runs its default core observational set). When present, only
 * the named layer ids run (the adaptive subset select-layers.ts chose). Core observational
 * capture (structure/screens/ax/interactive) always runs regardless.
 */
function makeWant(layersArg?: string): (id: string) => boolean {
  if (!layersArg || layersArg === "true") return () => true;
  const set = new Set(layersArg.split(",").map((s) => s.trim()).filter(Boolean));
  return (id: string) => set.has(id);
}

async function loadPlaywright() {
  try {
    // dynamic import so the file parses even before playwright is installed
    return await import("playwright");
  } catch {
    console.error(
      "Playwright not installed. Run:\n  cd .claude/skills/acos-reverse-cleanroom/scripts && bun add playwright && bunx playwright install chromium",
    );
    process.exit(1);
  }
}

async function captureRole(
  pw: any,
  base: string,
  role: string,
  seeds: string[],
  outDir: string,
  statePath: string | undefined,
  want: (id: string) => boolean,
) {
  const roleDir = join(outDir, "roles", role);
  mkdirSync(join(roleDir, "screens"), { recursive: true });
  const harPath = join(roleDir, "network.har");

  const browser = await pw.chromium.launch({ headless: true });
  const context = await browser.newContext({
    recordHar: { path: harPath, content: "embed" },
    ...(statePath && existsSync(statePath) ? { storageState: statePath } : {}),
  });
  const page = await context.newPage();

  // Layer 9 (console & client-error) — gated. Attach BEFORE navigation so nothing is missed.
  const consoleLog: any[] = [];
  if (want("console-client-error")) {
    page.on("console", (msg: any) => consoleLog.push({ type: msg.type(), text: msg.text() }));
    page.on("pageerror", (err: any) => consoleLog.push({ type: "pageerror", text: String(err) }));
  }
  // Layer 11 (security-surface) — gated. Record main-document response headers per route.
  const securityHeaders: any[] = [];

  const structure: any[] = [];
  for (const route of seeds) {
    const url = new URL(route, base).toString();
    try {
      const resp = await page.goto(url, { waitUntil: "networkidle", timeout: 30_000 });
      const title = await page.title();
      if (want("security-surface") && resp) {
        try {
          securityHeaders.push({ route, status: resp.status(), headers: await resp.allHeaders() });
        } catch { /* header read best-effort */ }
      }
      // AX tree = the accessibility snapshot (roles/names/states) — the layer
      // screenshots can never show and rebuilds most reliably destroy.
      const ax = await page.accessibility.snapshot({ interestingOnly: false });
      const safe = route.replace(/[^a-z0-9]+/gi, "_").replace(/^_|_$/g, "") || "root";
      await page.screenshot({ path: join(roleDir, "screens", `${safe}.png`), fullPage: true });
      writeFileSync(join(roleDir, `ax-${safe}.json`), JSON.stringify(ax, null, 2));
      // interaction-state provocation: hover/focus every interactive element,
      // then re-snapshot. (Kept shallow in v1; deepen per references/capture-layers.md.)
      const interactive = await page.$$eval(
        "a,button,input,select,textarea,[role=button],[tabindex]",
        (els: any[]) => els.length,
      );
      structure.push({ route, url, title, interactive_elements: interactive });
    } catch (e) {
      structure.push({ route, url, error: String(e) });
    }
  }

  writeFileSync(join(roleDir, "structure.json"), JSON.stringify(structure, null, 2));

  // Layer 8 (client storage & state) — gated. Read on-device persistence from the last page.
  if (want("client-storage-state")) {
    try {
      const storage = await page.evaluate(() => {
        const dump = (s: Storage) => Object.fromEntries(Object.keys(s).map((k) => [k, s.getItem(k)]));
        return { localStorage: dump(localStorage), sessionStorage: dump(sessionStorage) };
      });
      const cookies = await context.cookies();
      writeFileSync(join(roleDir, "storage.json"), JSON.stringify({ ...storage, cookies }, null, 2));
    } catch (e) {
      writeFileSync(join(roleDir, "storage.json"), JSON.stringify({ error: String(e) }, null, 2));
    }
  }
  if (want("console-client-error")) {
    writeFileSync(join(roleDir, "console.json"), JSON.stringify(consoleLog, null, 2));
  }
  if (want("security-surface")) {
    writeFileSync(join(roleDir, "security-headers.json"), JSON.stringify(securityHeaders, null, 2));
  }

  await context.close(); // flushes HAR
  await browser.close();
  return { role, routes: structure.length, har: harPath };
}

/**
 * Recon pass (capture.ts --recon): a cheap anon crawl of the seeds that detects the app's
 * SHAPE — which app-shape signals are present — so select-layers.ts can pick the adaptive
 * layer subset. Emits recon/signals.json + surface-census.json (the completeness denominator).
 * Every detection is a HEURISTIC and best-effort: a false negative just means a layer is skipped,
 * so first runs are calibration. All detection is wrapped so a failure never aborts the recon.
 */
async function recon(pw: any, base: string, roles: string[], seeds: string[], outDir: string) {
  const detected = new Set<string>();
  const routes = new Set<string>();
  const externalOrigins = new Set<string>();
  let formsTotal = 0;
  let interactiveTotal = 0;

  const browser = await pw.chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  const baseOrigin = new URL(base).origin;

  for (const route of seeds) {
    const url = new URL(route, base).toString();
    try {
      const resp = await page.goto(url, { waitUntil: "networkidle", timeout: 30_000 });
      routes.add(route);
      if (resp && resp.status() < 400) detected.add("public-pages");
      const sig: any = await page.evaluate((originArg: string) => {
        const q = (sel: string) => document.querySelectorAll(sel).length;
        const scriptSrcs = Array.from(document.querySelectorAll("script[src]")).map((s: any) => s.src as string);
        const ext = scriptSrcs
          .map((s) => { try { return new URL(s).origin; } catch { return ""; } })
          .filter((o) => o && o !== originArg);
        const scriptText = Array.from(document.querySelectorAll("script")).map((s: any) => s.textContent || "").join(" ");
        const body = (document.body && document.body.innerText ? document.body.innerText : "").slice(0, 8000);
        return {
          ext,
          realtime: /websocket|socket\.io|eventsource|wss?:\/\//i.test(scriptText + " " + scriptSrcs.join(" ")),
          forms: q("form, input, textarea, select"),
          search: !!document.querySelector('input[type=search], [role=search], input[name*=search i], input[placeholder*=search i]'),
          locale: q("link[hreflang]") > 0 || (!!document.documentElement.lang && q("[lang]") > 1) || q('select[name*=lang i], [class*=lang-switch i]') > 0,
          consent: /cookie|consent|gdpr|privacy/i.test(body) && !!document.querySelector('[class*=cookie i],[id*=consent i],[class*=consent i]'),
          serviceWorker: !!(navigator as any).serviceWorker,
          stepper: !!document.querySelector('[class*=step i],[class*=wizard i],[role=tablist],[aria-current=step]'),
          editable: !!document.querySelector('[contenteditable=true]'),
          sourcemapHint: /sourceMappingURL/.test(scriptText),
          interactive: q('a,button,input,select,textarea,[role=button],[tabindex]'),
        };
      }, baseOrigin);

      for (const o of sig.ext) externalOrigins.add(o);
      if (sig.ext.length) detected.add("external-scripts");
      if (sig.realtime) detected.add("realtime-detected");
      if (sig.forms > 0) { detected.add("forms-or-calc"); formsTotal += sig.forms; }
      if (sig.search) detected.add("search-present");
      if (sig.locale) detected.add("multi-locale");
      if (sig.consent) detected.add("consent-privacy");
      if (sig.serviceWorker) detected.add("service-worker");
      if (sig.stepper) detected.add("multistep-flows");
      if (sig.editable) detected.add("editable-content");
      if (sig.sourcemapHint) detected.add("sourcemaps-served");
      interactiveTotal += sig.interactive || 0;

      // Discover in-app links to widen the census denominator (same-origin only).
      try {
        const links: string[] = await page.evaluate((originArg: string) =>
          Array.from(document.querySelectorAll("a[href]"))
            .map((a: any) => { try { return new URL(a.href).origin === originArg ? new URL(a.href).pathname : ""; } catch { return ""; } })
            .filter(Boolean), baseOrigin);
        for (const p of links.slice(0, 200)) routes.add(p);
      } catch { /* link mining best-effort */ }
    } catch (e) {
      // a failed seed is recorded implicitly (not added to routes); recon continues.
    }
  }
  await context.close();
  await browser.close();

  mkdirSync(join(outDir, "recon"), { recursive: true });
  const signals = {
    roles: roles.length,
    detected: [...detected].sort(),
    note: "HEURISTIC recon (anon crawl). outbound-messaging / time-dependent are probe-only and not detected here.",
  };
  writeFileSync(join(outDir, "recon", "signals.json"), JSON.stringify(signals, null, 2));
  const census = {
    routes: [...routes].sort(),
    route_count: routes.size,
    forms_total: formsTotal,
    interactive_total: interactiveTotal,
    external_origins: [...externalOrigins].sort(),
    denominator_note: "completeness DENOMINATOR — coverage is measured against this surface set.",
  };
  writeFileSync(join(outDir, "surface-census.json"), JSON.stringify(census, null, 2));
  console.log(`recon: ${routes.size} route(s), ${detected.size} signal(s) [${signals.detected.join(", ")}] → ${join(outDir, "recon", "signals.json")}`);
  console.log(`next: bun select-layers.ts --signals ${join(outDir, "recon", "signals.json")} --benchmark 0.99 --out ${join(outDir, "recon", "selected-layers.json")}`);
}

async function main() {
  const a = parseArgs(process.argv.slice(2));
  if (!a.base || !a.out) {
    console.error("usage: bun capture.ts --base <url> --out <session-dir>/00-capture [--recon] [--layers <ids>] --roles anon,user --seed /,/dashboard");
    process.exit(1);
  }
  const roles = (a.roles || "anon").split(",").map((r) => r.trim()).filter(Boolean);
  const seeds = (a.seed || "/").split(",").map((s) => s.trim()).filter(Boolean);
  mkdirSync(a.out, { recursive: true });

  const pw = await loadPlaywright();

  // Recon-only mode: detect the app's shape, then exit (select-layers.ts runs next).
  if (a.recon) {
    await recon(pw, a.base, roles, seeds, a.out);
    return;
  }

  const want = makeWant(a.layers);
  const results = [];
  for (const role of roles) {
    const statePath = a[`state-${role}`];
    if (role !== "anon" && !statePath) {
      console.warn(`role '${role}' has no --state-${role} storage-state; capturing as anon view of those routes.`);
    }
    results.push(await captureRole(pw, a.base, role, seeds, a.out, statePath, want));
  }

  writeFileSync(
    join(a.out, "capture-manifest.json"),
    JSON.stringify(
      {
        base: a.base,
        roles,
        seeds,
        layers: a.layers && a.layers !== "true" ? a.layers.split(",").map((s) => s.trim()) : "default (all observational layers)",
        results,
        source_ref: a["source-ref"] || null, // pinned version fingerprint (caller supplies)
        epoch_note: "observation epoch set by orchestrator, not this script",
      },
      null,
      2,
    ),
  );
  console.log(`capture complete: ${roles.length} role(s), ${seeds.length} seed route(s) → ${a.out}`);
}

main();
