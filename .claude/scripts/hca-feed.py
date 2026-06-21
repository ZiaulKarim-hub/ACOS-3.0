#!/usr/bin/env python3
"""hca-feed.py — downstream trusted-input FEED / report / table FORMATS (SLICE-HCA-09, Demo 3).

Renders a VERIFIED deliverable (the report envelope from slice-08 `hca-deliver.build_report`,
or a single answer envelope from the slice-07 spine) into three downstream formats, EACH
carrying per-figure/per-value provenance + confidence so a downstream ACOS skill can consume
verified figures AND trace every one back to a cached Tier-1 raw API response:

  1. JSON dataset   — render_json(report)  : the data PLUS embedded per-value provenance +
                      confidence + gate verdict + completeness, structured for machine reads.
  2. CSV table      — render_csv(report)   : one row per figure, well-formed (stdlib `csv`,
                      quoted, no field corruption), round-trips with the JSON dataset.
  3. Trusted FEED   — render_feed(report)  : the dataset PLUS a `manifest` capturing, per
                      figure: raw_response_id + json_field_path provenance, confidence,
                      freshness, completeness, gate verdict, source counts, and a
                      generated_at + skill/version header. Validates against
                      schemas/feed-manifest.schema.json.

THE CONTRACT (hard gates — slice-09 acceptance = REJECT on fail):
  - EVERY emitted feed value carries a RESOLVABLE provenance pointer + a confidence. A figure
    that the report REFUSED is NEVER rendered as a value — it is surfaced verbatim in the
    feed's `refusals[]` so a downstream consumer MUST honor it (never silently dropped).
  - The manifest's `completeness` per figure is the REAL pagination-completeness gate result
    (figure.gate_verdict.pagination_complete + figure.complete), not a placeholder.
  - The manifest validates against feed-manifest.schema.json (a stdlib structural validator
    lives in this module — no third-party jsonschema dependency).

PII SAFETY (critical — slice-09 acceptance + the broader hca PII policy):
  Per-record tables / datasets can contain borrower PII. The renderers default to a
  PII-SAFE MODE (`pii_safe=True`): for any artifact written to the repo / evidence tree they
  emit ONLY portfolio-level aggregates / counts / field-NAMES — never borrower-level values.
  A report assembled from aggregate + count figures (the portfolio-summary report) is already
  aggregate-only and renders fully. Real per-record output, if ever produced (pii_safe=False),
  goes ONLY to the git-ignored runtime area (.acos/state/), never the tracked tree — and the
  module refuses to WRITE a non-PII-safe artifact anywhere under the repo's tracked dirs.

GROUND RULES (memory/decisions/2026-06-18-hca-build-ground-rules.md):
  - Python 3 stdlib ONLY — here specifically `json` + `csv` (+ io/os/datetime). No deps.
  - Subscription-only Claude: this module makes NO model call and reads NO API key.
  - Read-only: it serializes whatever the verified report carries; it never fetches, never
    mutates Tier-1, never writes the cache.

Slices 01-08 scripts are COMPOSE-ONLY here (their envelopes are consumed, never edited).
"""

from __future__ import annotations

import argparse
import csv
import datetime
import io
import json
import os
import sys
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Feed identity / schema version
# ---------------------------------------------------------------------------

SKILL = "acos-hypercore-ask"
FEED_SCHEMA_VERSION = "1.0"          # the feed/manifest contract version (feed-contract.md)
FEED_KIND = "hca-trusted-feed"

# Report/figure terminal states reused from hca-deliver (kept as literals so this module has
# no hard import dependency on the spine for pure serialization of an already-built report).
STATE_DELIVERED = "DELIVERED"


# ---------------------------------------------------------------------------
# Helpers — provenance + completeness extraction (per figure)
# ---------------------------------------------------------------------------

def _figure_provenance(figure: dict) -> dict:
    """Project a figure's provenance into the feed's per-value provenance record.

    Handles both single-value provenance ({raw_response_id, json_field_path}) and aggregate
    provenance ({aggregate: true, contributing:[{raw_response_id, json_field_path}, ...]}).
    Returns a uniform record carrying enough to RE-RESOLVE the value into Tier-1.
    """
    prov = figure.get("provenance") or {}
    out = {
        "raw_response_id": prov.get("raw_response_id"),
        "json_field_path": prov.get("json_field_path"),
        "aggregate": bool(prov.get("aggregate")),
    }
    contributing = prov.get("contributing")
    if contributing:
        # Carry the per-source pointers (the binding dicts) so an aggregate is fully traceable;
        # keep ONLY the source pointers (no values) — pointers are not PII.
        out["contributing"] = [
            {"raw_response_id": c.get("raw_response_id"),
             "json_field_path": c.get("json_field_path")}
            for c in contributing if isinstance(c, dict)
        ]
        out["source_count"] = len(out["contributing"])
    else:
        out["source_count"] = 1 if (out["raw_response_id"] and out["json_field_path"]) else 0
    return out


def _figure_completeness(figure: dict) -> dict:
    """The REAL completeness proof for a figure: the pagination-completeness gate result +
    the figure's own complete flag (NOT a placeholder). Surfaces the gate verdict so a
    consumer can independently confirm the proof is real."""
    gv = figure.get("gate_verdict") or {}
    return {
        "complete": bool(figure.get("complete")),
        "pagination_complete": gv.get("pagination_complete"),
        "gate_outcome": gv.get("outcome"),
        "gate_tier": gv.get("tier"),
    }


def _figure_freshness(figure: dict) -> dict:
    """Freshness proof for a figure: the freshness gate result. (The numeric fetched_at lives
    in Tier-1 behind the provenance pointer — not re-emitted here to keep the feed PII-light.)"""
    gv = figure.get("gate_verdict") or {}
    return {"freshness_ok": gv.get("freshness_ok")}


def _figure_gate_summary(figure: dict) -> dict:
    """A compact gate-verdict summary for the manifest (per-gate booleans + outcome)."""
    gv = figure.get("gate_verdict") or {}
    return {
        "outcome": gv.get("outcome"),
        "tier": gv.get("tier"),
        "schema_ok": gv.get("schema_ok"),
        "pagination_complete": gv.get("pagination_complete"),
        "freshness_ok": gv.get("freshness_ok"),
        "reconciliation_ok": gv.get("reconciliation_ok"),
        "normalization_applied": gv.get("normalization_applied"),
        "schema_drift_ok": gv.get("schema_drift_ok"),
        "provenance_ok": gv.get("provenance_ok"),
        "failures": gv.get("failures") or [],
    }


# ---------------------------------------------------------------------------
# PII safety — a figure-level guard for what may be serialized to a tracked artifact
# ---------------------------------------------------------------------------

# Aggregate / portfolio-level figure tiers + provenance shapes that are SAFE to emit to the
# tracked tree. A figure is PII-safe when it is an aggregate/count (portfolio-level) OR its
# value is a non-PII scalar produced by the count/aggregate intents. Per-record (per-borrower)
# values are NOT pii-safe and are blocked from tracked artifacts.
def _figure_is_pii_safe(figure: dict) -> bool:
    """A figure is PII-safe to write to the tracked tree iff it is portfolio-level:

      - an AGGREGATE figure (provenance.aggregate == True) — a SUM/total over the portfolio, or
      - a COUNT figure (json_field_path resolves to a reported_total) — a portfolio count.

    A single-record lookup figure (per-borrower value) is NOT pii-safe: even a "status" field
    is borrower-level. Such figures are surfaced as field-NAMES + provenance only in pii-safe
    mode, never with the value.
    """
    prov = figure.get("provenance") or {}
    if prov.get("aggregate"):
        return True
    path = prov.get("json_field_path") or ""
    # portfolio count: the reported_total of a list response (no per-record value)
    if path.endswith("reported_total"):
        return True
    return False


def _safe_figure_value(figure: dict, pii_safe: bool) -> Any:
    """Return the value to emit for a figure under the active PII mode.

    In pii_safe mode, a NON-portfolio (per-record) figure's value is REDACTED to None and the
    figure is flagged `pii_redacted: True`; only its label/unit/provenance-pointer/confidence
    are emitted. A portfolio-level (aggregate/count) figure emits its value normally.
    """
    if not pii_safe:
        return figure.get("value")
    if _figure_is_pii_safe(figure):
        return figure.get("value")
    return None  # redacted — per-record value never written to a tracked/PII-safe artifact


# ---------------------------------------------------------------------------
# JSON dataset
# ---------------------------------------------------------------------------

def render_dataset(report: dict, *, pii_safe: bool = True) -> dict:
    """Build the dataset object (the data + per-value provenance/confidence) for a report.

    Returns {kind, skill, schema_version, generated_at, title, pii_safe, state, rows:[...],
             refusals:[...]} where each row is one figure with its provenance + confidence +
             completeness + gate verdict. Refused figures are NOT rows — they are carried in
             refusals[] so a consumer MUST honor them (never silently dropped).
    """
    rows = []
    for fig in report.get("figures", []):
        redacted = pii_safe and not _figure_is_pii_safe(fig)
        rows.append({
            "label": fig.get("label"),
            "value": _safe_figure_value(fig, pii_safe),
            "unit": fig.get("unit"),
            "currency": fig.get("currency"),
            "confidence": fig.get("confidence"),
            "provenance": _figure_provenance(fig),
            "completeness": _figure_completeness(fig),
            "freshness": _figure_freshness(fig),
            "gate_verdict": _figure_gate_summary(fig),
            "tier": fig.get("tier"),
            "pii_redacted": redacted,
        })
    return {
        "kind": FEED_KIND + ":dataset",
        "skill": SKILL,
        "schema_version": FEED_SCHEMA_VERSION,
        "generated_at": report.get("generated_at") or _now_iso(),
        "title": report.get("title"),
        "pii_safe": bool(pii_safe),
        "state": report.get("state"),
        "rows": rows,
        "refusals": list(report.get("refusals") or []),
    }


def render_json(report: dict, *, pii_safe: bool = True, indent: int = 2) -> str:
    """Render a report to a JSON-dataset STRING (per-value provenance + confidence embedded)."""
    return json.dumps(render_dataset(report, pii_safe=pii_safe), indent=indent, default=str)


# ---------------------------------------------------------------------------
# CSV table — one row per figure; well-formed (stdlib csv, quoted, no corruption)
# ---------------------------------------------------------------------------

# The CSV column order IS the round-trip contract (parse_csv reads it back). Provenance is
# emitted as raw_response_id + json_field_path columns so a CSV row independently resolves to
# Tier-1; aggregates additionally carry source_count + an `aggregate` flag.
CSV_COLUMNS = [
    "label", "value", "unit", "currency", "confidence",
    "raw_response_id", "json_field_path", "aggregate", "source_count",
    "complete", "pagination_complete", "freshness_ok", "gate_outcome",
    "tier", "pii_redacted",
]


def _csv_row_for_figure(fig: dict, pii_safe: bool) -> dict:
    prov = _figure_provenance(fig)
    comp = _figure_completeness(fig)
    fresh = _figure_freshness(fig)
    redacted = pii_safe and not _figure_is_pii_safe(fig)
    return {
        "label": fig.get("label"),
        "value": _csv_scalar(_safe_figure_value(fig, pii_safe)),
        "unit": _csv_scalar(fig.get("unit")),
        "currency": _csv_scalar(fig.get("currency")),
        "confidence": _csv_scalar(fig.get("confidence")),
        "raw_response_id": _csv_scalar(prov.get("raw_response_id")),
        "json_field_path": _csv_scalar(prov.get("json_field_path")),
        "aggregate": "true" if prov.get("aggregate") else "false",
        "source_count": _csv_scalar(prov.get("source_count")),
        "complete": "true" if comp.get("complete") else "false",
        "pagination_complete": _csv_tribool(comp.get("pagination_complete")),
        "freshness_ok": _csv_tribool(fresh.get("freshness_ok")),
        "gate_outcome": _csv_scalar(comp.get("gate_outcome")),
        "tier": _csv_scalar(fig.get("tier")),
        "pii_redacted": "true" if redacted else "false",
    }


def render_csv(report: dict, *, pii_safe: bool = True) -> str:
    """Render a report to a CSV-table STRING. One row per DELIVERED figure; the header row is
    CSV_COLUMNS. stdlib `csv` with QUOTE_MINIMAL + '\\r\\n' line terminator (RFC-4180-ish),
    so embedded commas/quotes/newlines never corrupt a field. Round-trips with parse_csv."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, quoting=csv.QUOTE_MINIMAL,
                            lineterminator="\r\n", extrasaction="ignore")
    writer.writeheader()
    for fig in report.get("figures", []):
        writer.writerow(_csv_row_for_figure(fig, pii_safe))
    return buf.getvalue()


def parse_csv(text: str) -> list:
    """Parse a rendered CSV table back into a list of row dicts (the round-trip inverse of
    render_csv). Pure stdlib `csv`; preserves field text exactly (no coercion)."""
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


def _csv_scalar(value: Any) -> str:
    """Render a scalar for a CSV cell. None -> empty string; everything else -> str()."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _csv_tribool(value: Any) -> str:
    """Three-state boolean for CSV: True/False/None(unknown) -> 'true'/'false'/'' ."""
    if value is None:
        return ""
    return "true" if value else "false"


# ---------------------------------------------------------------------------
# Trusted FEED + manifest
# ---------------------------------------------------------------------------

def build_manifest(report: dict, *, pii_safe: bool = True) -> dict:
    """Build the feed MANIFEST: per-figure provenance + confidence + freshness + completeness
    + gate verdict + source counts, plus a generated_at + skill/version header and aggregate
    portfolio counts. Validates against schemas/feed-manifest.schema.json.

    The manifest is the trust contract: a downstream consumer reads it to (a) trace each value
    to Tier-1, (b) confirm the completeness proof is REAL (matches the pagination gate), and
    (c) honor refusals / confidence. NO borrower-level value lives in the manifest — only
    pointers, counts, field-NAMES, and gate booleans.
    """
    entries = []
    for fig in report.get("figures", []):
        prov = _figure_provenance(fig)
        entries.append({
            "label": fig.get("label"),
            "unit": fig.get("unit"),
            "currency": fig.get("currency"),
            "confidence": fig.get("confidence"),
            "provenance": prov,
            "source_count": prov.get("source_count"),
            "completeness": _figure_completeness(fig),
            "freshness": _figure_freshness(fig),
            "gate_verdict": _figure_gate_summary(fig),
            "tier": fig.get("tier"),
        })
    refusals = list(report.get("refusals") or [])
    meta = report.get("meta") or {}
    return {
        "kind": FEED_KIND + ":manifest",
        "skill": SKILL,
        "schema_version": FEED_SCHEMA_VERSION,
        "generated_at": report.get("generated_at") or _now_iso(),
        "title": report.get("title"),
        "state": report.get("state"),
        "pii_safe": bool(pii_safe),
        "figure_count": int(meta.get("figure_count", len(report.get("figures", [])) + len(refusals))),
        "delivered_count": len(report.get("figures", [])),
        "refused_count": len(refusals),
        "figures": entries,
        "refusals": refusals,
    }


def render_feed(report: dict, *, pii_safe: bool = True) -> dict:
    """Build the full trusted FEED object = {manifest, dataset}.

    The manifest is the trust header (provenance/confidence/freshness/completeness/gates per
    figure); the dataset is the data the consumer ingests. A downstream ACOS skill reads the
    manifest to validate trust, then ingests dataset.rows, honoring refusals + confidence.
    """
    return {
        "kind": FEED_KIND,
        "skill": SKILL,
        "schema_version": FEED_SCHEMA_VERSION,
        "generated_at": report.get("generated_at") or _now_iso(),
        "manifest": build_manifest(report, pii_safe=pii_safe),
        "dataset": render_dataset(report, pii_safe=pii_safe),
    }


def render_feed_json(report: dict, *, pii_safe: bool = True, indent: int = 2) -> str:
    return json.dumps(render_feed(report, pii_safe=pii_safe), indent=indent, default=str)


# ---------------------------------------------------------------------------
# Manifest schema validation (stdlib structural validator — no jsonschema dep)
# ---------------------------------------------------------------------------

def _skill_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))                 # .../.claude/scripts
    root = os.path.abspath(os.path.join(here, os.pardir, os.pardir))  # repo root
    return os.path.join(root, ".claude", "skills", "acos-hypercore-ask")


def _manifest_schema_path() -> str:
    return os.path.join(_skill_dir(), "schemas", "feed-manifest.schema.json")


def load_manifest_schema(path: Optional[str] = None) -> dict:
    with open(path or _manifest_schema_path(), "r", encoding="utf-8") as fh:
        return json.load(fh)


_JSON_TYPE = {
    "object": dict, "array": list, "string": str, "boolean": bool,
    "null": type(None),
}


def _type_ok(value: Any, type_name: str) -> bool:
    if type_name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    py = _JSON_TYPE.get(type_name)
    if py is None:
        return True
    if py is bool:
        return isinstance(value, bool)
    return isinstance(value, py)


def _validate(node: Any, schema: dict, path: str, errors: list) -> None:
    """A small recursive validator covering the JSON-Schema subset used by
    feed-manifest.schema.json: type, required, properties, items, enum. Sufficient to PROVE
    the manifest is structurally valid without a third-party dependency (ground rule: stdlib)."""
    if not isinstance(schema, dict):
        return
    types = schema.get("type")
    if types is not None:
        type_list = types if isinstance(types, list) else [types]
        if not any(_type_ok(node, t) for t in type_list):
            errors.append(f"{path}: expected type {types}, got {type(node).__name__}")
            return  # type mismatch -> deeper checks are meaningless
    if "enum" in schema and node not in schema["enum"]:
        errors.append(f"{path}: value {node!r} not in enum {schema['enum']}")
    if isinstance(node, dict):
        for req in schema.get("required", []):
            if req not in node:
                errors.append(f"{path}: missing required property {req!r}")
        props = schema.get("properties", {})
        for key, subschema in props.items():
            if key in node:
                _validate(node[key], subschema, f"{path}.{key}", errors)
    if isinstance(node, list) and "items" in schema:
        for i, el in enumerate(node):
            _validate(el, schema["items"], f"{path}[{i}]", errors)


def validate_manifest(manifest: dict, *, schema: Optional[dict] = None) -> dict:
    """Validate a manifest against feed-manifest.schema.json. Returns {ok, errors:[...]}.

    Uses the stdlib structural validator above (no jsonschema dependency). Also enforces the
    REAL-completeness-proof gate beyond pure structure: every figure's completeness MUST carry
    a pagination_complete boolean that is not a placeholder string (it is the gate result).
    """
    schema = schema or load_manifest_schema()
    errors = []
    _validate(manifest, schema, "$", errors)
    # Beyond structure: the completeness proof must be REAL (not a placeholder).
    for i, fig in enumerate(manifest.get("figures", [])):
        comp = fig.get("completeness") or {}
        pc = comp.get("pagination_complete")
        if not isinstance(pc, (bool, type(None))):
            errors.append(f"$.figures[{i}].completeness.pagination_complete: "
                          f"completeness proof must be the real gate boolean, got {pc!r}")
    return {"ok": not errors, "errors": errors}


# ---------------------------------------------------------------------------
# Writing artifacts (PII guard: non-pii-safe artifacts NEVER land in the tracked tree)
# ---------------------------------------------------------------------------

def _repo_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, os.pardir, os.pardir))


# The only repo-relative dir that is git-ignored (runtime) and may hold real per-record data.
_RUNTIME_DIR = os.path.join(".acos", "state")


def _is_tracked_path(abspath: str) -> bool:
    """True when abspath is inside the repo but NOT under the git-ignored runtime dir.

    Anything under .acos/state/ is git-ignored runtime (safe for real per-record output);
    everything else inside the repo is the tracked tree (a non-pii-safe artifact must never
    be written there)."""
    root = _repo_root()
    abspath = os.path.abspath(abspath)
    if os.path.commonpath([root, abspath]) != root:
        return False  # outside the repo entirely (e.g. a test tmpdir) -> not "tracked"
    runtime = os.path.abspath(os.path.join(root, _RUNTIME_DIR))
    try:
        return os.path.commonpath([runtime, abspath]) != runtime
    except ValueError:
        return True


def write_artifact(text: str, dest_path: str, *, pii_safe: bool) -> str:
    """Write a rendered artifact to dest_path, enforcing the PII rule:

      - a PII-safe artifact (aggregate/counts/field-names only) may be written anywhere.
      - a NON-pii-safe artifact (may contain per-record borrower values) may ONLY be written
        under the git-ignored runtime area (.acos/state/), NEVER the tracked tree.

    Returns the absolute path written. Raises PermissionError on a policy violation (refusing
    to write per-record PII into the tracked repo).
    """
    abspath = os.path.abspath(dest_path)
    if not pii_safe and _is_tracked_path(abspath):
        raise PermissionError(
            "refusing to write a non-PII-safe artifact (may contain per-record borrower "
            f"values) into the tracked tree: {abspath}. Per-record output goes ONLY to the "
            f"git-ignored runtime area ({_RUNTIME_DIR}/).")
    os.makedirs(os.path.dirname(abspath) or ".", exist_ok=True)
    with open(abspath, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    return abspath


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# CLI — render a report envelope (from stdin or a file) to json|csv|feed.
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="acos-hypercore-ask feed/report/table renderer (Demo 3). Renders a "
                    "verified report envelope to a JSON dataset, a CSV table, or a trusted "
                    "FEED with a schema-valid per-figure-provenance manifest. PII-safe by "
                    "default (aggregates/counts/field-names only for tracked artifacts).")
    parser.add_argument("--format", choices=["json", "csv", "feed"], default="feed",
                        help="render format (default: feed = manifest + dataset)")
    parser.add_argument("--in", dest="infile", default="-",
                        help="report-envelope JSON file ('-' for stdin; default stdin)")
    parser.add_argument("--out", dest="outfile", default=None,
                        help="write to this path (PII guard enforced); default stdout")
    parser.add_argument("--allow-pii", action="store_true",
                        help="DISABLE pii-safe mode (per-record values; runtime area only)")
    parser.add_argument("--validate", action="store_true",
                        help="for --format feed: also validate the manifest + print result")
    args = parser.parse_args(argv)

    raw = sys.stdin.read() if args.infile == "-" else \
        open(args.infile, "r", encoding="utf-8").read()
    report = json.loads(raw)
    pii_safe = not args.allow_pii

    if args.format == "json":
        text = render_json(report, pii_safe=pii_safe)
    elif args.format == "csv":
        text = render_csv(report, pii_safe=pii_safe)
    else:
        feed = render_feed(report, pii_safe=pii_safe)
        if args.validate:
            res = validate_manifest(feed["manifest"])
            sys.stderr.write("manifest valid: " + json.dumps(res) + "\n")
            if not res["ok"]:
                return 2
        text = json.dumps(feed, indent=2, default=str)

    if args.outfile:
        path = write_artifact(text, args.outfile, pii_safe=pii_safe)
        sys.stderr.write(f"wrote {path}\n")
    else:
        sys.stdout.write(text if text.endswith("\n") else text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
