#!/usr/bin/env python3
"""
wigum-loop.py — master orchestrator for acos-ultimate-designer.

Wraps Phase 1 + Phase 2 + Phase 3 + render-and-verify. On each iteration:
renders, reviews, and if FAIL classifies defects + writes fix-instructions.yaml
+ re-enters Phase 1. A (criterion,page) WARNING seen on 3 consecutive iterations
escalates to ERROR on the 3rd. Hard ceiling 10.

Usage:
    wigum-loop.py --session-dir <dir> --format pdf|pptx|both
                  [--max-iterations 5] [--hard-ceiling 10]
                  [--resume-from-iteration N]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: pyyaml required\n")
    sys.exit(1)


SKILL_ROOT = Path(__file__).resolve().parent.parent


DEFECT_ROUTING = {
    "page_rhythm":            ["decomposer"],
    "typography":             ["emitter", "template"],
    "palette":                ["emitter"],
    "photo_quality":          ["image_fill"],
    "logo":                   ["emitter"],
    "cross_page_consistency": ["emitter"],
    "brad_inherited":         ["emitter", "qa_gate"],
}


def log(session_dir: Path, msg: str) -> None:
    ts = dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}\n"
    sys.stderr.write(line)
    with open(session_dir / "wigum.log", "a") as f:
        f.write(line)


def run(cmd: list[str], cwd: Path | None = None) -> int:
    try:
        proc = subprocess.run(cmd, cwd=cwd, check=False)
        return proc.returncode
    except Exception as e:
        sys.stderr.write(f"run failed: {' '.join(cmd)}: {e}\n")
        return 127


def run_phase_1(session_dir: Path, session_manifest: dict, iteration: int) -> int:
    content_path = session_manifest["inputs"]["content_path"]
    fix_ctx = session_dir / "fix-instructions.yaml"
    cmd = ["python3", str(SKILL_ROOT / "scripts" / "decompose-content.py"),
           content_path, str(session_dir / "phase1" / "page-plan.yaml")]
    if fix_ctx.exists() and iteration > 1:
        cmd += ["--fix-context", str(fix_ctx)]
    rc = run(cmd)
    if rc != 0:
        return rc

    rc = run(["python3", str(SKILL_ROOT / "scripts" / "html-emit.py"),
              str(session_dir / "phase1" / "page-plan.yaml"),
              str(session_dir / "phase1" / "output.html"),
              "--tokens", str(SKILL_ROOT / "templates" / "tokens.css"),
              "--templates", str(SKILL_ROOT / "templates" / "page-templates")])
    if rc != 0:
        return rc

    rc = run(["python3", str(SKILL_ROOT / "scripts" / "html-qa-gate.py"),
              str(session_dir / "phase1" / "output.html"),
              str(session_dir / "phase1" / "qa-report.yaml"),
              "--force"])  # force so QA fail doesn't block loop; visual gate is authoritative
    shutil.copy(session_dir / "phase1" / "output.html", session_dir / "output.html")
    shutil.copy(session_dir / "phase1" / "page-plan.yaml", session_dir / "page-plan.yaml")
    return 0


def run_phase_2(session_dir: Path, session_manifest: dict) -> int:
    asset_dir = session_manifest["inputs"].get("asset_dir")
    if asset_dir and Path(asset_dir).is_dir():
        run(["python3", str(SKILL_ROOT / "scripts" / "bootstrap-manifest.py"),
             "--asset-dir", asset_dir])

    cmd = ["python3", str(SKILL_ROOT / "scripts" / "fill-photo-slots.py"),
           "--html", str(session_dir / "output.html"),
           "--session-dir", str(session_dir),
           "--output", str(session_dir / "output.html")]
    if asset_dir and Path(asset_dir).is_dir():
        cmd += ["--manifest", str(Path(asset_dir) / ".acos-ultimate-designer-manifest.yaml")]
    return run(cmd)


def run_phase_3(session_dir: Path, fmt: str) -> int:
    if fmt in ("pdf", "both"):
        rc = run(["bash", str(SKILL_ROOT / "scripts" / "render-pdf.sh"),
                  "--input", str(session_dir / "output.html"),
                  "--output", str(session_dir / "output.pdf")])
        if rc != 0 and fmt == "pdf":
            return rc
    if fmt in ("pptx", "both"):
        run(["python3", str(SKILL_ROOT / "scripts" / "emit-pptx-content.py"),
             "--page-plan", str(session_dir / "page-plan.yaml"),
             "--image-log", str(session_dir / "image-resolution.log"),
             "--output", str(session_dir / "phase3" / "pptx-content.yaml")])
        (session_dir / "phase3").mkdir(exist_ok=True)
        rc = run(["bash", str(SKILL_ROOT / "scripts" / "render-pptx.sh"),
                  "--content", str(session_dir / "phase3" / "pptx-content.yaml"),
                  "--template", str(SKILL_ROOT / "templates" / "template.pptx"),
                  "--design-spec", str(SKILL_ROOT / "templates" / "pptx-design-spec.yaml"),
                  "--output", str(session_dir / "output.pptx")])
        if rc != 0 and fmt == "pptx":
            return rc
    return 0


def run_verify(session_dir: Path, fmt: str, iteration: int) -> dict:
    primary_fmt = "pdf" if fmt in ("pdf", "both") else "pptx"
    run(["bash", str(SKILL_ROOT / "scripts" / "render-and-verify.sh"),
         "--session-dir", str(session_dir),
         "--iteration", str(iteration),
         "--format", primary_fmt])
    defects_file = session_dir / "visual-audit" / f"iteration-{iteration:02d}" / "visual-defects.yaml"
    if not defects_file.exists():
        return {"verdict": "fail", "criteria_results": [], "failed_items": ["render-and-verify did not produce defects file"]}
    return yaml.safe_load(defects_file.read_text()) or {"verdict": "fail"}


def classify_defects(defects: dict) -> dict:
    """Route each failed criterion to a target stage, build fix-instructions.yaml."""
    fixes: dict = {"fixes": [], "targets": set()}
    for r in defects.get("criteria_results") or []:
        if r.get("status") == "fail":
            cat = r.get("category") or r.get("id", "").split("-")[0]
            # map id prefix to category
            prefix_map = {"PR": "page_rhythm", "TY": "typography", "PA": "palette",
                          "PQ": "photo_quality", "LG": "logo", "CP": "cross_page_consistency", "BI": "brad_inherited"}
            if "-" in (r.get("id") or ""):
                cat = prefix_map.get(r["id"].split("-")[0], cat)
            targets = DEFECT_ROUTING.get(cat, ["emitter"])
            fixes["targets"].update(targets)
            # Compose a concrete fix action
            action = "regenerate"
            if cat == "page_rhythm" and "photo" in (r.get("fix_instruction", "").lower()):
                action = "insert_photo_break_after"
            elif cat == "typography" and "italic" in (r.get("fix_instruction", "").lower()):
                action = "set_italic_accent"
            fixes["fixes"].append({
                "criterion_id": r.get("id"),
                "page": r.get("page"),
                "category": cat,
                "action": action,
                "instruction": r.get("fix_instruction"),
                "value": r.get("value"),
            })
    fixes["targets"] = sorted(fixes["targets"])
    return fixes


def escalate_severity(session_dir: Path, defects: dict, iteration: int) -> dict:
    """WARNING-x2 → ERROR on iteration 3 for same (id, page)."""
    history_file = session_dir / "wigum-warning-history.yaml"
    history = {}
    if history_file.exists():
        history = yaml.safe_load(history_file.read_text()) or {}
    seen_this_iter = set()
    for r in defects.get("criteria_results") or []:
        if r.get("severity") == "WARNING" and r.get("status") == "fail":
            key = f"{r.get('id')}|{r.get('page')}"
            count = history.get(key, 0) + 1
            history[key] = count
            seen_this_iter.add(key)
            if count >= 3:
                r["severity"] = "ERROR"
                r["note"] = "escalated from WARNING after 3 iterations"
    # Reset counts for keys not seen this iteration
    for key in list(history.keys()):
        if key not in seen_this_iter:
            history[key] = 0
    history_file.write_text(yaml.safe_dump(history, sort_keys=False))
    return defects


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--session-dir", required=True)
    ap.add_argument("--format", required=True, choices=("pdf", "pptx", "both"))
    ap.add_argument("--max-iterations", type=int, default=5)
    ap.add_argument("--hard-ceiling", type=int, default=10)
    ap.add_argument("--resume-from-iteration", type=int, default=1)
    args = ap.parse_args()

    session_dir = Path(args.session_dir)
    if not (session_dir / "manifest.yaml").exists():
        sys.stderr.write(f"ERROR: session manifest not found at {session_dir}\n")
        return 1
    session_manifest = yaml.safe_load((session_dir / "manifest.yaml").read_text())

    for iteration in range(args.resume_from_iteration, args.hard_ceiling + 1):
        log(session_dir, f"===== Iteration {iteration} =====")

        rc = run_phase_1(session_dir, session_manifest, iteration)
        if rc != 0:
            log(session_dir, f"Phase 1 failed (exit {rc})")
            return rc
        rc = run_phase_2(session_dir, session_manifest)
        if rc != 0:
            log(session_dir, f"Phase 2 failed (exit {rc})")
            return rc
        rc = run_phase_3(session_dir, args.format)
        if rc != 0:
            log(session_dir, f"Phase 3 failed (exit {rc})")
            return rc

        defects = run_verify(session_dir, args.format, iteration)
        defects = escalate_severity(session_dir, defects, iteration)
        verdict = defects.get("verdict", "fail")
        log(session_dir, f"Iteration {iteration} verdict: {verdict}")

        if verdict == "pass":
            log(session_dir, f"PASS on iteration {iteration}. Finalizing.")
            return 0

        if verdict == "needs_agent":
            log(session_dir, f"Iteration {iteration} needs visual reviewer agent — prompt at "
                             f"visual-audit/iteration-{iteration:02d}/agent-prompt.md. Spawn a "
                             f"Task(model='opus') with that prompt, populate visual-defects.yaml, "
                             f"then resume with --resume-from-iteration {iteration}.")
            return 3

        # Write fix-instructions for this failed iteration before deciding whether
        # to stop at the soft max — so an operator resuming has the latest context.
        fixes = classify_defects(defects)
        (session_dir / "fix-instructions.yaml").write_text(yaml.safe_dump(fixes, sort_keys=False))
        log(session_dir, f"Wrote fix-instructions targeting: {fixes.get('targets')}")

        # Soft max is REAL: once iteration >= max_iterations and the iteration
        # still FAILED, stop and surface to the operator with exit code 4
        # ("soft max reached — needs operator review"). hard_ceiling remains the
        # absolute backstop (exit 2) for runs invoked with max_iterations >=
        # hard_ceiling.
        if iteration >= args.max_iterations and iteration < args.hard_ceiling:
            log(session_dir, f"SOFT MAX ({args.max_iterations}) reached and last iteration "
                             f"FAILED. Stopping. fix-instructions.yaml + last-iteration output "
                             f"saved to {session_dir}. Re-run with a higher --max-iterations "
                             f"(up to --hard-ceiling {args.hard_ceiling}) and "
                             f"--resume-from-iteration {iteration + 1} to continue, or review manually.")
            return 4

    log(session_dir, f"HARD CEILING ({args.hard_ceiling}) reached. Review manually.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
