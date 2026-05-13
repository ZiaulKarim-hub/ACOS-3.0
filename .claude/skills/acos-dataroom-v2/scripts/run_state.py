"""Run-state management for acos-dataroom-v2.

Provides atomic read/write/update of run_state.json plus helpers for
checkpoint logging and resumption.

CLI usage:
  python3 run_state.py init --run-dir <RUN_DIR> --source <SRC> --objective <STR>
  python3 run_state.py get --run-dir <RUN_DIR> --field <field>
  python3 run_state.py set --run-dir <RUN_DIR> --phase <phase> --checkpoint <chk>
  python3 run_state.py log --run-dir <RUN_DIR> --message <msg> [--phase <phase>]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from pathlib import Path
from typing import Any

SKILL_VERSION = "v2.0.0"


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _state_path(run_dir: Path) -> Path:
    return run_dir / "run_state.json"


def _log_path(run_dir: Path) -> Path:
    return run_dir / "logs" / "run_log.txt"


def init_run_state(run_dir: Path, source: str, objective: str) -> dict[str, Any]:
    """Initialize a fresh run_state.json for a new run."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "logs").mkdir(parents=True, exist_ok=True)

    state = {
        "run_id": run_dir.name,
        "source": str(source),
        "objective_brief": objective,
        "started_at": _now_iso(),
        "phase": "0_setup",
        "last_completed_checkpoint": None,
        "skill_version": SKILL_VERSION,
        "halt_report_path": None,
        "final_output_path": None,
    }
    write_state(run_dir, state)
    log(run_dir, f"Initialized run_state.json (source={source}, objective={objective!r})", phase="0_setup")
    return state


def read_state(run_dir: Path) -> dict[str, Any]:
    p = _state_path(Path(run_dir))
    if not p.exists():
        raise FileNotFoundError(f"run_state.json not found at {p}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_state(run_dir: Path, state: dict[str, Any]) -> None:
    p = _state_path(Path(run_dir))
    # Atomic write via tempfile rename
    tmp = p.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, p)


def set_phase(run_dir: Path, phase: str, checkpoint: str | None = None) -> None:
    """Update phase + optional last_completed_checkpoint."""
    state = read_state(run_dir)
    state["phase"] = phase
    if checkpoint is not None:
        state["last_completed_checkpoint"] = checkpoint
    state["last_updated_at"] = _now_iso()
    write_state(run_dir, state)
    log(run_dir, f"phase -> {phase}, checkpoint -> {checkpoint}", phase=phase)


def set_field(run_dir: Path, key: str, value: Any) -> None:
    state = read_state(run_dir)
    state[key] = value
    state["last_updated_at"] = _now_iso()
    write_state(run_dir, state)


def get_field(run_dir: Path, key: str) -> Any:
    state = read_state(run_dir)
    return state.get(key)


def log(run_dir: Path, message: str, phase: str | None = None) -> None:
    """Append a line to logs/run_log.txt. Best-effort — never raises."""
    try:
        p = _log_path(Path(run_dir))
        p.parent.mkdir(parents=True, exist_ok=True)
        ts = _now_iso()
        prefix = f"[{ts}]"
        if phase:
            prefix += f" [{phase}]"
        line = f"{prefix} {message}\n"
        with p.open("a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="acos-dataroom-v2 run-state helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("--run-dir", required=True, type=Path)
    p_init.add_argument("--source", required=True)
    p_init.add_argument("--objective", required=True)

    p_get = sub.add_parser("get")
    p_get.add_argument("--run-dir", required=True, type=Path)
    p_get.add_argument("--field", required=True)

    p_set = sub.add_parser("set")
    p_set.add_argument("--run-dir", required=True, type=Path)
    p_set.add_argument("--phase", required=True)
    p_set.add_argument("--checkpoint", default=None)

    p_setfield = sub.add_parser("setfield")
    p_setfield.add_argument("--run-dir", required=True, type=Path)
    p_setfield.add_argument("--key", required=True)
    p_setfield.add_argument("--value", required=True)

    p_log = sub.add_parser("log")
    p_log.add_argument("--run-dir", required=True, type=Path)
    p_log.add_argument("--message", required=True)
    p_log.add_argument("--phase", default=None)

    args = parser.parse_args(argv)

    if args.cmd == "init":
        state = init_run_state(args.run_dir, args.source, args.objective)
        print(json.dumps(state, indent=2))
    elif args.cmd == "get":
        val = get_field(args.run_dir, args.field)
        print(json.dumps(val) if val is not None else "")
    elif args.cmd == "set":
        set_phase(args.run_dir, args.phase, args.checkpoint)
        print(json.dumps(read_state(args.run_dir), indent=2))
    elif args.cmd == "setfield":
        # try parsing as JSON, fallback to string
        try:
            value = json.loads(args.value)
        except json.JSONDecodeError:
            value = args.value
        set_field(args.run_dir, args.key, value)
        print(json.dumps(read_state(args.run_dir), indent=2))
    elif args.cmd == "log":
        log(args.run_dir, args.message, phase=args.phase)
    else:
        parser.error(f"unknown cmd {args.cmd}")
    return 0


if __name__ == "__main__":
    sys.exit(cli_main())
