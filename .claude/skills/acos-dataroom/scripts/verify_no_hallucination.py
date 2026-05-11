"""No-hallucination verification for evidence bundles.

For every summary claim across all evidence bundles in a run directory,
verify the snippet appears in the source extraction text using layered
matching:

    Layer 1: Verbatim substring                   confidence 1.00 (label: verbatim)
    Layer 2: Whitespace-normalized                 confidence 0.97 (label: whitespace_normalized)
    Layer 3: Currency / punctuation stripped       confidence 0.92 (label: format_normalized)
    Layer 4: Token-set overlap with claim text     confidence 0.70-0.90 (label: paraphrase_likely)
    No match: confidence 0.00 (label: unverified)

A claim that fails all layers is flagged as a potential hallucination —
written to the run's `intermediate/hallucination_check.json` for review.

Inputs:
    <run_dir>/extraction/<file_id>/extraction.json  (source-of-truth text)
    <run_dir>/evidence/<file_id>.json               (claims to verify)

Outputs:
    <run_dir>/intermediate/hallucination_check.json — full per-claim audit
    <run_dir>/intermediate/qa_report.json — Pass #3 row updated with real numbers
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
import utils  # noqa: E402


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

_WS = re.compile(r"\s+")
_CURRENCY = re.compile(r"[\$£€¥,]")
_PUNCT = re.compile(r"[\(\)\[\]\{\}\.\;\:\!\?\"'`]")


def normalize_whitespace(s: str) -> str:
    return _WS.sub(" ", s).strip()


def strip_currency_and_punct(s: str) -> str:
    """Strip currency symbols, commas, decorative punctuation. Preserve digits and letters."""
    s = _CURRENCY.sub("", s)
    s = _PUNCT.sub(" ", s)
    return normalize_whitespace(s).lower()


def extract_tokens(s: str) -> set[str]:
    """Extract alphanumeric token set (lowercased)."""
    return set(re.findall(r"[A-Za-z0-9]{2,}", s.lower()))


def extract_numbers(s: str) -> list[str]:
    """Extract digit sequences (length >= 2). Strips formatting first.

    `$11,500,000` → ['11500000']. `loan 1` → ['1']  is dropped because length < 2.
    """
    stripped = _CURRENCY.sub("", s)  # remove $ and ,
    return [n for n in re.findall(r"\d+", stripped) if len(n) >= 2]


# ---------------------------------------------------------------------------
# Verification (layered)
# ---------------------------------------------------------------------------

def verify_claim(claim_text: str, snippet_text: str, source_text: str) -> dict[str, Any]:
    """Verify a single claim's snippet against source text.

    Returns a dict with status, confidence, layer that succeeded, and a brief
    explanation.
    """
    if not snippet_text or not source_text:
        return {
            "status": "unverified",
            "layer": "no_snippet_or_source",
            "confidence": 0.0,
            "explanation": "Empty snippet or no source text to match against.",
        }

    # Layer 1: verbatim
    if snippet_text in source_text:
        return {
            "status": "verified",
            "layer": "verbatim",
            "confidence": 1.00,
            "explanation": "Snippet appears verbatim in source.",
        }

    # Layer 2: whitespace-normalized
    norm_snip = normalize_whitespace(snippet_text)
    norm_src = normalize_whitespace(source_text)
    if norm_snip in norm_src:
        return {
            "status": "verified",
            "layer": "whitespace_normalized",
            "confidence": 0.97,
            "explanation": "Snippet appears after whitespace normalization.",
        }

    # Layer 3: currency / punctuation stripped (handles "$11,500,000" vs "11500000")
    stripped_snip = strip_currency_and_punct(snippet_text)
    stripped_src = strip_currency_and_punct(source_text)
    if stripped_snip and stripped_snip in stripped_src:
        return {
            "status": "verified",
            "layer": "format_normalized",
            "confidence": 0.92,
            "explanation": (
                "Snippet matches source after stripping currency symbols, commas, "
                "decorative punctuation, and casing. The values themselves are "
                "present in the source — only the formatting differs."
            ),
        }

    # Layer 4: token-set overlap between claim text and source text
    # (this layer compares the CLAIM, not the snippet, against the source — so
    # paraphrased claims that still contain the right tokens get caught.)
    claim_tokens = extract_tokens(claim_text or snippet_text)
    source_tokens = extract_tokens(source_text)

    if not claim_tokens:
        return {
            "status": "unverified",
            "layer": "no_tokens",
            "confidence": 0.0,
            "explanation": "Claim text contains no comparable tokens.",
        }

    overlap = claim_tokens & source_tokens
    overlap_ratio = len(overlap) / len(claim_tokens)
    missing_tokens = sorted(claim_tokens - source_tokens)

    # Numbers must match precisely — a claim with $11.5M when source has $1.5M is a fail
    claim_numbers = set(extract_numbers(claim_text or snippet_text))
    source_numbers = set(extract_numbers(source_text))
    missing_numbers = claim_numbers - source_numbers
    numbers_ok = not missing_numbers

    if overlap_ratio >= 0.80 and numbers_ok:
        confidence = 0.70 + 0.20 * overlap_ratio
        return {
            "status": "verified",
            "layer": "paraphrase_likely",
            "confidence": round(confidence, 2),
            "explanation": (
                f"Claim text appears to be a paraphrase of source. "
                f"{len(overlap)}/{len(claim_tokens)} tokens ({overlap_ratio:.0%}) match. "
                f"All numbers in claim present in source."
            ),
            "missing_tokens": missing_tokens[:10],
        }

    if not numbers_ok:
        return {
            "status": "unverified",
            "layer": "number_mismatch",
            "confidence": 0.0,
            "explanation": (
                f"Numbers in claim are not all present in source. "
                f"Missing numbers: {sorted(missing_numbers)[:5]}. "
                "This is a strong hallucination signal — values cited in the "
                "claim do not appear in the source text."
            ),
            "missing_numbers": sorted(missing_numbers),
        }

    return {
        "status": "unverified",
        "layer": "low_token_overlap",
        "confidence": round(overlap_ratio, 2),
        "explanation": (
            f"Only {len(overlap)}/{len(claim_tokens)} ({overlap_ratio:.0%}) of claim tokens "
            f"appear in source. Threshold is 80% for paraphrase acceptance."
        ),
        "missing_tokens": missing_tokens[:10],
    }


# ---------------------------------------------------------------------------
# Bundle / claim iteration
# ---------------------------------------------------------------------------

def verify_run(run_dir: Path) -> dict[str, Any]:
    evidence_dir = run_dir / "evidence"
    extraction_dir = run_dir / "extraction"
    classifications_path = run_dir / "intermediate" / "classifications.json"

    if not evidence_dir.is_dir():
        raise FileNotFoundError(f"No evidence directory at {evidence_dir}")

    # Build file_id -> file_name map
    classifications = (
        utils.read_json(classifications_path) if classifications_path.exists() else []
    )
    fid_to_name = {c.get("file_id"): c.get("file_name", "") for c in classifications}

    per_file_results: list[dict[str, Any]] = []
    total_claims = 0
    by_layer: dict[str, int] = {}
    unverified_claims: list[dict[str, Any]] = []

    for ev_path in sorted(evidence_dir.glob("*.json")):
        fid = ev_path.stem
        try:
            bundle = json.loads(ev_path.read_text())
        except json.JSONDecodeError as exc:
            per_file_results.append({
                "file_id": fid,
                "file_name": fid_to_name.get(fid, ""),
                "error": f"invalid JSON: {exc}",
                "claims": [],
            })
            continue

        # Load extraction text
        ext_path = extraction_dir / fid / "extraction.json"
        source_text = ""
        if ext_path.exists():
            try:
                ext = json.loads(ext_path.read_text())
                source_text = "\n".join((p.get("text") or "") for p in ext.get("pages", []))
            except Exception:  # noqa: BLE001
                pass
        # Also include vision_supplement extracted_text where present
        if ext_path.exists():
            try:
                ext = json.loads(ext_path.read_text())
                for p in ext.get("pages", []):
                    vs = p.get("vision_supplement", {})
                    if isinstance(vs, dict):
                        source_text += "\n" + (vs.get("extracted_text", "") or "")
            except Exception:  # noqa: BLE001
                pass

        claims = (bundle.get("summary", {}) or {}).get("claims", []) or []
        file_results: list[dict[str, Any]] = []

        for claim in claims:
            if not isinstance(claim, dict):
                continue
            claim_text = claim.get("claim", "")
            snippet = claim.get("snippet", {})
            snippet_text = snippet.get("text", "") if isinstance(snippet, dict) else str(snippet)
            page = snippet.get("page", "") if isinstance(snippet, dict) else ""

            verdict = verify_claim(claim_text, snippet_text, source_text)
            verdict["claim"] = claim_text
            verdict["snippet_preview"] = snippet_text[:120]
            verdict["page"] = page

            file_results.append(verdict)
            total_claims += 1
            by_layer[verdict["layer"]] = by_layer.get(verdict["layer"], 0) + 1

            if verdict["status"] == "unverified":
                unverified_claims.append({
                    "file_id": fid,
                    "file_name": fid_to_name.get(fid, ""),
                    **verdict,
                })

        per_file_results.append({
            "file_id": fid,
            "file_name": fid_to_name.get(fid, ""),
            "claims": file_results,
        })

    verified = total_claims - len(unverified_claims)
    return {
        "total_claims": total_claims,
        "verified_count": verified,
        "unverified_count": len(unverified_claims),
        "verified_pct": round(verified / total_claims * 100, 1) if total_claims else 0.0,
        "by_layer": by_layer,
        "per_file": per_file_results,
        "unverified": unverified_claims,
    }


def update_qa_report(run_dir: Path, result: dict[str, Any]) -> None:
    """Update Pass #3 in qa_report.json with real numbers from this verification."""
    qa_path = run_dir / "intermediate" / "qa_report.json"
    if not qa_path.exists():
        return
    qa = utils.read_json(qa_path)
    for row in qa:
        if str(row.get("pass_name", "")).lower().startswith("summary"):
            row["flagged_count"] = result["unverified_count"]
            row["total_checked"] = result["total_claims"]
            row["flagged_file_ids"] = ",".join(
                u["file_id"] for u in result["unverified"]
            )
            layer_summary = ", ".join(
                f"{name}={count}" for name, count in result["by_layer"].items()
            )
            row["notes"] = (
                f"Layered verification ({result['verified_pct']:.1f}% verified). "
                f"By layer: {layer_summary}. "
                f"See intermediate/hallucination_check.json for per-claim audit."
            )
            break
    utils.write_json(qa_path, qa)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify no-hallucination across all evidence bundles in a run."
    )
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--update-qa-report", action="store_true",
                        help="Update intermediate/qa_report.json Pass #3 with real numbers.")
    args = parser.parse_args(argv)

    if not args.run_dir.is_dir():
        print(f"Run directory not found: {args.run_dir}", file=sys.stderr)
        return 2

    result = verify_run(args.run_dir)

    out_path = args.run_dir / "intermediate" / "hallucination_check.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    utils.write_json(out_path, result)

    if args.update_qa_report:
        update_qa_report(args.run_dir, result)

    print(f"Total claims:        {result['total_claims']}")
    print(f"Verified:            {result['verified_count']} ({result['verified_pct']:.1f}%)")
    print(f"Unverified:          {result['unverified_count']}")
    print(f"By layer:")
    for layer, count in sorted(result["by_layer"].items(), key=lambda x: -x[1]):
        print(f"  {layer:30s} {count}")
    if result["unverified"]:
        print()
        print("Unverified claims (first 5):")
        for u in result["unverified"][:5]:
            print(f"  {u['file_name']}: {u['layer']}")
            print(f"    claim: {u['claim'][:80]}")
            print(f"    {u['explanation'][:200]}")
    print(f"\nFull audit: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
