#!/usr/bin/env python3
"""
fetch-image-fallback.py — Unsplash → Pexels image fetcher.

Reads UNSPLASH_ACCESS_KEY and PEXELS_API_KEY from env. On success, downloads
the top landscape-oriented result to cache dir and emits JSON metadata.

Usage:
    fetch-image-fallback.py --query "mountain sunset" --cache-dir <path>
                            [--orientation landscape] [--min-width 2000]
                            [--verbose]

Output (stdout, JSON):
    {"local_path": "...", "source": "unsplash"|"pexels", "photographer": "...",
     "photographer_url": "...", "image_url": "...", "query": "...",
     "attribution_string": "Photo by X on Unsplash"}
  OR on failure:
    {"action": "empty_slot", "reason": "no API keys / both failed"}
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import socket


USER_AGENT = "acos-ultimate-designer/0.1"
TIMEOUT_CONNECT = 30
TIMEOUT_READ = 60
ALLOWED_HOSTS = ("images.unsplash.com", "plus.unsplash.com", "images.pexels.com")


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_image", Path(__file__).resolve().parent / "validate-image.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.is_valid_image


is_valid_image = _load_validator()


def _get_json(url: str, headers: dict, timeout: int = 30) -> dict | None:
    req = Request(url, headers={**headers, "User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (URLError, HTTPError, socket.timeout, json.JSONDecodeError) as e:
        print(f"  [warn] API call failed: {e}", file=sys.stderr)
        return None


def _download(url: str, cache_dir: Path, query: str) -> Path | None:
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.hostname not in ALLOWED_HOSTS:
        # loosen: allow subdomains of the approved families
        ok = any(parsed.hostname and parsed.hostname.endswith(h.split(".", 1)[-1]) for h in ALLOWED_HOSTS)
        if not ok:
            print(f"  [warn] blocked host: {parsed.hostname}", file=sys.stderr)
            return None
    cache_key = hashlib.sha256((url + query).encode()).hexdigest()[:16]
    out = cache_dir / f"{cache_key}.jpg"
    if out.exists():
        return out
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=TIMEOUT_READ) as resp:
            out.write_bytes(resp.read())
    except (URLError, HTTPError, socket.timeout) as e:
        print(f"  [warn] download failed: {e}", file=sys.stderr)
        return None
    valid, reason, _kind = is_valid_image(out)
    if not valid:
        print(f"  [warn] downloaded non-image from {url}: {reason} — discarding", file=sys.stderr)
        try:
            out.unlink()
        except OSError:
            pass
        return None
    return out


def try_unsplash(query: str, cache_dir: Path, min_width: int) -> dict | None:
    key = os.environ.get("UNSPLASH_ACCESS_KEY")
    if not key:
        return None
    url = (f"https://api.unsplash.com/search/photos?"
           f"query={quote_plus(query)}&orientation=landscape&per_page=5")
    data = _get_json(url, {"Authorization": f"Client-ID {key}"})
    if not data or not data.get("results"):
        return None
    for r in data["results"]:
        if r.get("width", 0) < min_width:
            continue
        img_url = r["urls"].get("full") or r["urls"].get("raw")
        local = _download(img_url, cache_dir, query)
        if local:
            return {
                "local_path": str(local),
                "source": "unsplash",
                "photographer": r["user"]["name"],
                "photographer_url": r["user"]["links"]["html"],
                "image_url": r["links"]["html"],
                "query": query,
                "attribution_string": f'Photo by {r["user"]["name"]} on Unsplash',
            }
    return None


def try_pexels(query: str, cache_dir: Path, min_width: int) -> dict | None:
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return None
    url = (f"https://api.pexels.com/v1/search?"
           f"query={quote_plus(query)}&orientation=landscape&per_page=5")
    data = _get_json(url, {"Authorization": key})
    if not data or not data.get("photos"):
        return None
    for r in data["photos"]:
        if r.get("width", 0) < min_width:
            continue
        img_url = r["src"].get("original") or r["src"].get("large2x")
        local = _download(img_url, cache_dir, query)
        if local:
            return {
                "local_path": str(local),
                "source": "pexels",
                "photographer": r["photographer"],
                "photographer_url": r["photographer_url"],
                "image_url": r["url"],
                "query": query,
                "attribution_string": f'Photo by {r["photographer"]} on Pexels',
            }
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--query", required=True)
    ap.add_argument("--cache-dir", required=True)
    ap.add_argument("--orientation", default="landscape")
    ap.add_argument("--min-width", type=int, default=2000)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    if not os.environ.get("UNSPLASH_ACCESS_KEY") and not os.environ.get("PEXELS_API_KEY"):
        print(json.dumps({"action": "empty_slot", "reason": "no API keys (UNSPLASH_ACCESS_KEY + PEXELS_API_KEY both unset)"}))
        return 0

    result = try_unsplash(args.query, cache_dir, args.min_width)
    if not result:
        result = try_pexels(args.query, cache_dir, args.min_width)

    if result:
        print(json.dumps(result))
    else:
        print(json.dumps({"action": "empty_slot", "reason": "both providers returned no usable result"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
