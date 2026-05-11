"""Utility functions shared by all acos-dataroom scripts.

Hashing, deterministic IDs, run state, logging, path helpers.
Stdlib-only — no third-party dependencies in this module so every other
script can rely on it without import-order surprises.
"""

from __future__ import annotations

import datetime as _dt
import fnmatch
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "1.0"
SKILL_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = SKILL_DIR / "config.json"


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_config_cache: dict[str, Any] | None = None


def load_config() -> dict[str, Any]:
    """Load and cache config.json once per process."""
    global _config_cache
    if _config_cache is None:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            _config_cache = json.load(fh)
    return _config_cache


# ---------------------------------------------------------------------------
# Hashing & IDs
# ---------------------------------------------------------------------------

def sha256_file(path: Path, chunk_size: int = 65536) -> str:
    """SHA-256 hex digest of a file. Streams to handle large files."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def file_id_from_hash(sha256_hex: str, prefix: str = "f_") -> str:
    """Deterministic file_id from a SHA-256 hex digest. First 12 hex chars."""
    return f"{prefix}{sha256_hex[:12]}"


def short_hash(text: str, length: int = 8) -> str:
    """Short hash of a string — used for run IDs."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def make_run_id(source_path: str | Path, when: _dt.datetime | None = None) -> str:
    """Deterministic-ish run ID: timestamp + short hash of source path."""
    when = when or _dt.datetime.utcnow()
    return f"run_{when.strftime('%Y%m%d_%H%M%S')}_{short_hash(str(source_path))}"


# ---------------------------------------------------------------------------
# Run directory layout
# ---------------------------------------------------------------------------

def run_dir_layout(source: Path, run_id: str) -> dict[str, Path]:
    """Return canonical paths for a run's working artifacts."""
    cfg = load_config()
    output_subfolder = cfg.get("output_subfolder", "_acos_dataroom_output")
    base = source / output_subfolder / run_id
    subs = cfg.get("output_subdirectories", {})
    return {
        "base": base,
        "extraction": base / subs.get("extraction", "extraction"),
        "evidence": base / subs.get("evidence", "evidence"),
        "intermediate": base / subs.get("intermediate", "intermediate"),
        "logs": base / subs.get("logs", "logs"),
    }


def ensure_run_dirs(layout: dict[str, Path]) -> None:
    """mkdir -p every directory in the layout."""
    for p in layout.values():
        p.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def write_json(path: Path, data: Any, *, indent: int = 2) -> None:
    """Atomic JSON write — write to .partial then rename."""
    tmp = path.with_suffix(path.suffix + ".partial")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=indent, default=str, ensure_ascii=False)
    tmp.replace(path)


def read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Run state (resumability)
# ---------------------------------------------------------------------------

def write_run_state(layout: dict[str, Path], state: dict[str, Any]) -> None:
    state["updated_at"] = _dt.datetime.utcnow().isoformat() + "Z"
    write_json(layout["base"] / "run_state.json", state)


def read_run_state(layout: dict[str, Path]) -> dict[str, Any] | None:
    p = layout["base"] / "run_state.json"
    if not p.exists():
        return None
    return read_json(p)


def mark_phase_complete(
    layout: dict[str, Path],
    phase_name: str,
    *,
    state: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update run_state.json to record a phase completion."""
    state = state or read_run_state(layout) or {"phases": {}}
    state.setdefault("phases", {})
    state["phases"][phase_name] = {
        "completed_at": _dt.datetime.utcnow().isoformat() + "Z",
        **(extra or {}),
    }
    state["last_phase_completed"] = phase_name
    write_run_state(layout, state)
    return state


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def make_logger(layout: dict[str, Path], name: str = "acos_dataroom") -> logging.Logger:
    """Logger that writes both to console and to <run_dir>/logs/run_log.txt."""
    log_path = layout["logs"] / "run_log.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()  # Avoid duplicate handlers on re-init

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    return logger


def log_low_confidence(
    logger: logging.Logger,
    file_id: str,
    field: str,
    confidence: float,
    *,
    threshold: float = 0.85,
) -> None:
    """Emit a structured log line whenever a confidence value is below threshold."""
    if confidence < threshold:
        logger.warning(
            "LOW_CONFIDENCE | file_id=%s | field=%s | confidence=%.3f | threshold=%.3f",
            file_id,
            field,
            confidence,
            threshold,
        )


# ---------------------------------------------------------------------------
# File-system helpers
# ---------------------------------------------------------------------------

def is_system_file(name: str, patterns: Iterable[str]) -> bool:
    """Match a filename against config-supplied glob patterns (e.g. .DS_Store, ~$*)."""
    for pat in patterns:
        if fnmatch.fnmatch(name, pat):
            return True
    return False


def relative_to(path: Path, base: Path) -> str:
    """Return a relative POSIX-style path string. Falls back to str(path) on error."""
    try:
        return str(path.relative_to(base)).replace(os.sep, "/")
    except ValueError:
        return str(path)


def safe_open(path: Path, mode: str = "rb"):
    """Open with one retry — handles transient sync-lock failures on Dropbox/OneDrive."""
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            return open(path, mode)
        except (OSError, PermissionError) as exc:
            last_exc = exc
            import time as _time
            _time.sleep(1.0)
    raise RuntimeError(f"Could not open {path} after 3 attempts: {last_exc}")


# ---------------------------------------------------------------------------
# Sanitization
# ---------------------------------------------------------------------------

_SAFE_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")


def sanitize_segment(text: str, *, lowercase: bool = False, space_to: str = "_") -> str:
    """Sanitize a string for use as a filename segment."""
    if lowercase:
        text = text.lower()
    text = text.replace(" ", space_to)
    out = "".join(c if c in _SAFE_CHARS else "_" for c in text)
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_")
