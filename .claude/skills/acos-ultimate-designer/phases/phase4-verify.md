# Phase 4 — Visual Verification + Wigum Loop

## Purpose
Mechanically verify every output page against the coffee-table visual checklist. Loop back to Phase 1 with specific fix instructions on any ERROR-severity defect. Ceiling: 5 default, 10 hard.

## Scripts Invoked
- `scripts/wigum-loop.py` — the master orchestrator. Internally invokes Phase 1 + Phase 2 + Phase 3 + `render-and-verify.sh` per iteration.
- `scripts/render-and-verify.sh` — renders output → 200 DPI PNGs via `render-doc-audit.py`, spawns a Task agent (model=opus HARDCODED), produces `visual-defects.yaml`.

## Bash Block

```bash
set -e
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE:-$0}")/.." && pwd)"
SESSION_DIR=".acos/ultimate-designer/sessions/{session_id}"
MANIFEST="$SESSION_DIR/manifest.yaml"
FORMAT="$(python3 -c "import yaml; m=yaml.safe_load(open('$MANIFEST')); print(m['inputs']['output_format'])")"
CEILING="$(python3 -c "import yaml; m=yaml.safe_load(open('$MANIFEST')); print(m['inputs'].get('iteration_ceiling') or 5)")"

python3 "$SKILL_DIR/scripts/wigum-loop.py" \
  --session-dir "$SESSION_DIR" \
  --format "$FORMAT" \
  --max-iterations "$CEILING" \
  --hard-ceiling 10

EXIT_CODE=$?
case $EXIT_CODE in
  0)
    echo "Wigum loop PASSED"
    ;;
  2)
    echo "Wigum loop hit HARD CEILING (10 iterations). Last-iteration output + aggregated defects saved to $SESSION_DIR. Review manually."
    exit 2
    ;;
  3)
    echo "Wigum loop needs a VISUAL REVIEWER AGENT (exit 3). render-and-verify.sh emitted a needs_agent sentinel. Spawn a Task(model='opus') using the agent-prompt.md in the latest visual-audit/iteration-NN/ to populate visual-defects.yaml, then resume: wigum-loop.py ... --resume-from-iteration <that iteration>."
    exit 3
    ;;
  4)
    echo "Wigum loop hit the SOFT MAX (--max-iterations) and the last iteration still FAILED (exit 4 — needs operator review). fix-instructions.yaml + last-iteration output saved to $SESSION_DIR. Re-run with a higher --max-iterations (up to the hard ceiling) and --resume-from-iteration <next> to continue, or review manually."
    exit 4
    ;;
  *)
    echo "Wigum loop FAILED with exit code $EXIT_CODE"
    exit $EXIT_CODE
    ;;
esac
```

## Visual Reviewer Model Pinning

The Task agent spawned by `render-and-verify.sh` is HARD-PINNED to `model: opus`. Rationale: sonnet misses subtle coffee-table defects (editorial spacing, italic accents, photo rhythm) — documented in the story file and the ADR layer.

Grep check: `grep "model='opus'" scripts/render-and-verify.sh` must return a literal string match, not a config reference.

## Wigum Loop Behavior

For each iteration `N in 1..max_iterations`:
1. Run Phase 1 (decompose → emit → QA) with any prior `fix-instructions.yaml`
2. Run Phase 2 (image fill)
3. Run Phase 3 (render to output format)
4. Run `render-and-verify.sh` → visual-defects.yaml
5. If verdict=PASS: copy output to session root, exit 0
6. If verdict=FAIL: classify defects, write `fix-instructions.yaml`, continue

**Severity escalation:** A (criterion,page) WARNING seen on 3 consecutive iterations escalates to ERROR on the 3rd. This prevents non-deterministic loop termination from LLM review variance.

**Soft max:** when the `--max-iterations` iteration still FAILS (and the hard ceiling is higher), wigum-loop.py STOPS and exits with code 4 ("soft max reached — needs operator review"), writing the latest `fix-instructions.yaml`. Re-run with a higher `--max-iterations` and `--resume-from-iteration N+1` to continue.

**Hard ceiling:** after the 10th (hard-ceiling) iteration fails, exit code 2 and a consolidated defects report.

## Defect Classification Routing

| Defect category | Target stage | Script re-run |
|---|---|---|
| page_rhythm | decomposer | `decompose-content.py --fix-context` |
| typography | emitter / template | `html-emit.py` with updated fix-context |
| palette | template (tokens.css) | `html-emit.py` |
| photo_quality | image matcher/fetcher | `fill-photo-slots.py` |
| logo | template | `html-emit.py` |
| cross_page_consistency | emitter | `html-emit.py` |
| brad_inherited | qa-gate + emitter | both |

## Outputs
- `{SESSION_DIR}/visual-audit/iteration-NN/` — per-iteration PNGs + `visual-defects.yaml`
- `{SESSION_DIR}/wigum.log` — iteration-by-iteration audit trail
- `{SESSION_DIR}/output.{pdf,pptx}` — final verified output on PASS
