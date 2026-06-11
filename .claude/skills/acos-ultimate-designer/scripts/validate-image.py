#!/usr/bin/env python3
"""
validate-image.py — verify a file is actually a decodable image before the
Anthropic API or an HTML renderer ever sees it.

Why: HTTP downloaders that ignore status codes happily save server-issued
HTML error pages under .jpg filenames. Reading such a file as an image
returns HTTP 400 "Could not process image" from the Anthropic API, and
because the Read tool pins the bad bytes into conversation history, every
subsequent turn in that session is rejected with the same error. Validating
before downstream use is the only way to prevent the poisoned-history
failure mode.

Strategy (layered, cheapest first):
  1. File exists and is non-empty.
  2. First 16 bytes match a known image magic (JPEG/PNG/GIF/WebP).
     These four cover everything Anthropic's vision accepts.
  3. Optional Pillow `verify()` if Pillow is installed (catches truncated
     files, invalid markers). Skipped silently when Pillow is absent so
     the skill stays stdlib-only for projects that don't need it.

Usage (CLI):
    validate-image.py <path>                 # exit 0 valid, 1 invalid
    validate-image.py --json <path>          # emit {valid, reason, kind} JSON

Usage (importable):
    from validate_image import is_valid_image
    ok, reason, kind = is_valid_image(Path("foo.jpg"))
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


MIN_SIZE_BYTES = 256

MAGIC_TESTS = (
    ("jpeg", lambda b: b[:3] == b"\xff\xd8\xff"),
    ("png",  lambda b: b[:8] == b"\x89PNG\r\n\x1a\n"),
    ("gif",  lambda b: b[:6] in (b"GIF87a", b"GIF89a")),
    ("webp", lambda b: b[:4] == b"RIFF" and b[8:12] == b"WEBP"),
)


def is_valid_image(path: Path) -> tuple[bool, str, str]:
    """Return (valid, reason, kind). `kind` is jpeg|png|gif|webp|"" when invalid."""
    if not path.exists():
        return False, f"file does not exist: {path}", ""
    if not path.is_file():
        return False, f"not a regular file: {path}", ""
    try:
        size = path.stat().st_size
    except OSError as e:
        return False, f"stat failed: {e}", ""
    if size < MIN_SIZE_BYTES:
        return False, f"file too small ({size} bytes, min {MIN_SIZE_BYTES})", ""

    try:
        with open(path, "rb") as f:
            head = f.read(16)
    except OSError as e:
        return False, f"read failed: {e}", ""

    kind = ""
    for name, test in MAGIC_TESTS:
        if test(head):
            kind = name
            break
    if not kind:
        preview = head[:8].hex()
        return False, f"magic bytes do not match any supported image format (head={preview})", ""

    try:
        from PIL import Image  # type: ignore
    except ImportError:
        return True, f"magic-byte match ({kind}); Pillow unavailable for deep verify", kind

    try:
        with Image.open(path) as im:
            im.verify()
    except Exception as e:
        return False, f"Pillow verify failed ({kind}): {type(e).__name__}: {e}", kind

    return True, f"valid {kind}", kind


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", help="path to candidate image")
    ap.add_argument("--json", action="store_true", help="emit JSON on stdout")
    ap.add_argument("--quiet", action="store_true", help="suppress stderr on success")
    args = ap.parse_args()

    p = Path(args.path)
    valid, reason, kind = is_valid_image(p)

    if args.json:
        print(json.dumps({"valid": valid, "reason": reason, "kind": kind, "path": str(p)}))
    elif not valid:
        print(f"INVALID {p}: {reason}", file=sys.stderr)
    elif not args.quiet:
        print(f"ok {p}: {reason}", file=sys.stderr)

    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
