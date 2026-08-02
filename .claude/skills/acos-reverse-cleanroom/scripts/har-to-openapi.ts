#!/usr/bin/env bun
/**
 * har-to-openapi.ts — infer an OpenAPI 3.1 contract skeleton from a captured HAR.
 *
 * HAR = HTTP Archive, the network log Playwright records in Phase 0. This turns
 * observed request/response traffic into a machine-readable API contract that
 * the intent extractors and rebuild proposers can reason over — WITHOUT the
 * original source. Path params are generalized (numeric / uuid segments → {id}).
 *
 * This is INFERENCE, not ground truth: it sees only endpoints that were exercised
 * during capture. Unexercised endpoints are invisible and must be marked gaps.
 *
 * Usage: bun har-to-openapi.ts <path/to/network.har> <out.openapi.json>
 */

import { readFileSync, writeFileSync } from "node:fs";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function generalize(pathname: string): string {
  return pathname
    .split("/")
    .map((seg) => {
      if (/^\d+$/.test(seg)) return "{id}";
      if (UUID.test(seg)) return "{uuid}";
      return seg;
    })
    .join("/");
}

function inferType(v: any): any {
  if (v === null) return { type: "null" };
  if (Array.isArray(v)) return { type: "array", items: v.length ? inferType(v[0]) : {} };
  switch (typeof v) {
    case "number": return { type: Number.isInteger(v) ? "integer" : "number" };
    case "boolean": return { type: "boolean" };
    case "object": {
      const props: any = {};
      for (const [k, val] of Object.entries(v)) props[k] = inferType(val);
      return { type: "object", properties: props };
    }
    default: return { type: "string" };
  }
}

function main() {
  const [harPath, outPath] = process.argv.slice(2);
  if (!harPath || !outPath) {
    console.error("usage: bun har-to-openapi.ts <network.har> <out.openapi.json>");
    process.exit(1);
  }
  const har = JSON.parse(readFileSync(harPath, "utf8"));
  const paths: any = {};
  let apiCalls = 0;

  for (const entry of har.log?.entries ?? []) {
    const req = entry.request;
    const res = entry.response;
    let u: URL;
    try { u = new URL(req.url); } catch { continue; }
    // Heuristic: treat XHR/fetch + JSON responses as API endpoints.
    const ct = (res.content?.mimeType || "").toLowerCase();
    const isApi = ct.includes("json") || /\/api\//.test(u.pathname);
    if (!isApi) continue;
    apiCalls++;

    const p = generalize(u.pathname);
    const method = (req.method || "GET").toLowerCase();
    paths[p] ??= {};
    if (paths[p][method]) continue; // first observation wins

    let requestSchema: any = undefined;
    if (req.postData?.text) {
      try { requestSchema = inferType(JSON.parse(req.postData.text)); } catch { /* non-json body */ }
    }
    let responseSchema: any = undefined;
    if (res.content?.text && ct.includes("json")) {
      try { responseSchema = inferType(JSON.parse(res.content.text)); } catch { /* skip */ }
    }

    paths[p][method] = {
      summary: `observed ${method.toUpperCase()} ${p}`,
      "x-observed-status": res.status,
      ...(requestSchema && {
        requestBody: { content: { "application/json": { schema: requestSchema } } },
      }),
      responses: {
        [String(res.status || 200)]: {
          description: "observed response",
          ...(responseSchema && { content: { "application/json": { schema: responseSchema } } }),
        },
      },
    };
  }

  const spec = {
    openapi: "3.1.0",
    info: { title: "Inferred contract (capture)", version: "0.0.0-observed" },
    "x-provenance": "INFERRED from HAR — only endpoints exercised during capture; unexercised endpoints are gaps.",
    paths,
  };
  writeFileSync(outPath, JSON.stringify(spec, null, 2));
  console.log(`OpenAPI skeleton: ${Object.keys(paths).length} path(s) from ${apiCalls} JSON/API call(s) → ${outPath}`);
}

main();
