"""Section-aware chunking for markdown and YAML files."""

import os
import re
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from .models import Chunk, ChunkMetadata

# Chunk size targets (characters)
TARGET_SIZE = 1500
MAX_SIZE = 2000
MIN_SIZE = 100

# Files/dirs to exclude
EXCLUDE_PATTERNS = {".template.", ".gitkeep", ".index/"}


def should_index(filepath: str) -> bool:
    """Check whether a file should be indexed."""
    if any(pat in filepath for pat in EXCLUDE_PATTERNS):
        return False
    ext = Path(filepath).suffix.lower()
    if ext not in (".md", ".yaml", ".yml"):
        return False
    try:
        size = os.path.getsize(filepath)
        return size >= 50
    except OSError:
        return False


def derive_category(filepath: str) -> tuple[str, str]:
    """Derive category and subcategory from the file's directory path.

    Examples:
        memory/decisions/foo.md        -> ("decision", "")
        memory/reviews/slice-reviews/  -> ("review", "slice-reviews")
        memory/handoffs/               -> ("handoff", "")
        memory/source-of-truth/        -> ("source-of-truth", "")
        learning-curve/patterns/       -> ("learning", "patterns")
    """
    parts = Path(filepath).parts

    # Find the root directory (memory/ or learning-curve/)
    category = ""
    subcategory = ""

    for i, part in enumerate(parts):
        if part == "memory":
            if i + 1 < len(parts):
                raw = parts[i + 1]
                # Singularize common directory names
                cat_map = {
                    "decisions": "decision",
                    "reviews": "review",
                    "handoffs": "handoff",
                    "interviews": "interview",
                    "source-of-truth": "source-of-truth",
                    "code-rationale": "code-rationale",
                    "feedback-history": "feedback-history",
                    "agent-communications": "agent-communication",
                }
                category = cat_map.get(raw, raw)
            if i + 2 < len(parts) and not parts[i + 2].endswith(
                (".md", ".yaml", ".yml")
            ):
                subcategory = parts[i + 2]
            break
        elif part == "learning-curve":
            category = "learning"
            if i + 1 < len(parts) and not parts[i + 1].endswith(
                (".md", ".yaml", ".yml")
            ):
                subcategory = parts[i + 1]
            break

    return category, subcategory


def _get_file_modified(filepath: str) -> str:
    """Get file modification time as ISO 8601 string."""
    try:
        mtime = os.path.getmtime(filepath)
        return datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
    except OSError:
        return datetime.now(tz=timezone.utc).isoformat()


def _fence_run(line: str) -> tuple[Optional[str], int, bool]:
    """If `line` (a RAW, un-stripped line) is a code-fence marker, return
    (fence_char, run_length, has_info_string); otherwise (None, 0, False).

    Per CommonMark, a fence is a run of >= 3 backticks or tildes. The run length
    matters: a fence opened with N markers can only be closed by a run of the
    SAME char with length >= N. Tracking just the first 3 chars would let a
    shorter inner ``` line falsely close a 4+-backtick fence.

    Two further CommonMark rules are enforced here so callers can apply them:
      * Indentation: a fence may be indented 0-3 spaces only. A line indented
        with a tab or with 4+ leading spaces is indented code, NOT a fence.
      * Info string: only an OPENING fence may carry an info string. A CLOSING
        fence must contain only the fence run + optional trailing whitespace.
        `has_info_string` is True when non-whitespace follows the fence run, so
        a close candidate can be rejected by the caller.
    """
    if not line:
        return None, 0, False
    # Indentation must be 0-3 spaces and contain no tab (a tab => indented code).
    stripped = line.lstrip(" ")
    indent = len(line) - len(stripped)
    if indent > 3 or "\t" in line[:indent]:
        return None, 0, False
    if not stripped:
        return None, 0, False
    ch = stripped[0]
    if ch not in ("`", "~"):
        return None, 0, False
    run = len(stripped) - len(stripped.lstrip(ch))
    if run < 3:
        return None, 0, False
    # Anything non-whitespace after the fence run is an info string.
    has_info_string = bool(stripped[run:].strip())
    return ch, run, has_info_string


def _split_markdown_sections(content: str) -> list[tuple[str, str]]:
    """Split markdown into (header, body) sections at H2 boundaries.

    Returns a list of (section_header, section_content) tuples.
    Content before the first H2 gets header "".
    """
    sections = []
    current_header = ""
    current_lines: list[str] = []
    fence_char = ""
    fence_len = 0

    for line in content.split("\n"):
        # Track fenced-code-block state so a '## ' line inside a ``` or ~~~ fence
        # is treated as content, not a section header.
        ch, run, has_info = _fence_run(line)
        if not fence_char and ch is not None:
            fence_char = ch
            fence_len = run
            current_lines.append(line)
            continue
        if fence_char:
            current_lines.append(line)
            # Close only on the same fence char with run length >= the opener's,
            # and only when the close line carries NO info string (info strings
            # are permitted on the opener only).
            if ch == fence_char and run >= fence_len and not has_info:
                fence_char = ""
                fence_len = 0
            continue
        if line.startswith("## "):
            # Save previous section
            if current_lines:
                sections.append((current_header, "\n".join(current_lines)))
            current_header = line.lstrip("# ").strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    # Don't forget the last section
    if current_lines:
        sections.append((current_header, "\n".join(current_lines)))

    return sections


def _split_at_h3(content: str) -> list[tuple[str, str]]:
    """Further split a section at H3 boundaries."""
    sections = []
    current_header = ""
    current_lines: list[str] = []
    fence_char = ""
    fence_len = 0

    for line in content.split("\n"):
        # Track fenced-code-block state so a '### ' line inside a ``` or ~~~ fence
        # is treated as content, not a section header.
        ch, run, has_info = _fence_run(line)
        if not fence_char and ch is not None:
            fence_char = ch
            fence_len = run
            current_lines.append(line)
            continue
        if fence_char:
            current_lines.append(line)
            # Close only on the same fence char with run length >= the opener's,
            # and only when the close line carries NO info string (info strings
            # are permitted on the opener only).
            if ch == fence_char and run >= fence_len and not has_info:
                fence_char = ""
                fence_len = 0
            continue
        if line.startswith("### "):
            if current_lines:
                sections.append((current_header, "\n".join(current_lines)))
            current_header = line.lstrip("# ").strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_header, "\n".join(current_lines)))

    return sections


def _split_at_paragraphs(content: str, target: int = TARGET_SIZE) -> list[str]:
    """Split content at paragraph boundaries to fit within target size.

    A single paragraph longer than `target` is further split with
    _split_text_to_max (line/size-based) so a semantic cut happens here rather
    than being emitted whole and later blindly hard-cut mid-word by the
    _enforce_max_size safety net.
    """
    paragraphs = re.split(r"\n\n+", content)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        # An individual paragraph larger than target can't fit in any accumulator;
        # flush what we have and size-split this paragraph on its own.
        if len(para) > target:
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_len = 0
            chunks.extend(_split_text_to_max(para, target))
            continue

        para_len = len(para)
        if current_len + para_len > target and current:
            chunks.append("\n\n".join(current))
            current = [para]
            current_len = para_len
        else:
            current.append(para)
            current_len += para_len + 2  # +2 for \n\n

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def chunk_markdown(filepath: str, content: str) -> list[Chunk]:
    """Chunk a markdown file into sections.

    Strategy:
    1. Split at H2 headers
    2. Oversized sections: split at H3
    3. Still oversized: split at paragraphs
    4. Skip sections smaller than MIN_SIZE
    """
    category, subcategory = derive_category(filepath)
    file_modified = _get_file_modified(filepath)
    source_dir = str(Path(filepath).parent)

    raw_sections = _split_markdown_sections(content)

    # Expand oversized sections
    expanded: list[tuple[str, str, str]] = []  # (parent_header, header, content)
    for header, body in raw_sections:
        if len(body) <= MAX_SIZE:
            expanded.append(("", header, body))
        else:
            # Try H3 split
            sub_sections = _split_at_h3(body)
            for sub_header, sub_body in sub_sections:
                if len(sub_body) <= MAX_SIZE:
                    expanded.append((header, sub_header or header, sub_body))
                else:
                    # Paragraph split
                    para_chunks = _split_at_paragraphs(sub_body)
                    for i, pc in enumerate(para_chunks):
                        label = sub_header or header
                        if len(para_chunks) > 1:
                            label = f"{label} (part {i + 1})"
                        expanded.append((header, label, pc))

    # Filter small chunks and build Chunk objects
    chunks: list[Chunk] = []
    # First pass to count for total_chunks_in_file
    valid = [(p, h, c) for p, h, c in expanded if len(c.strip()) >= MIN_SIZE]

    for idx, (parent_header, header, body) in enumerate(valid):
        meta = ChunkMetadata(
            source_file=filepath,
            source_dir=source_dir,
            file_type="md",
            section_header=header,
            parent_header=parent_header,
            chunk_index=idx,
            total_chunks_in_file=len(valid),
            file_modified=file_modified,
            char_count=len(body),
            category=category,
            subcategory=subcategory,
        )
        chunks.append(Chunk(content=body, metadata=meta))

    return chunks


def chunk_yaml(filepath: str, content: str) -> list[Chunk]:
    """Chunk a YAML file at top-level keys.

    Strategy:
    1. Split at top-level keys
    2. Oversized keys: split at second-level keys
    """
    category, subcategory = derive_category(filepath)
    file_modified = _get_file_modified(filepath)
    source_dir = str(Path(filepath).parent)

    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError:
        # If YAML is invalid, treat the whole file as one chunk
        meta = ChunkMetadata(
            source_file=filepath,
            source_dir=source_dir,
            file_type="yaml",
            section_header="(full file)",
            parent_header="",
            chunk_index=0,
            total_chunks_in_file=1,
            file_modified=file_modified,
            char_count=len(content),
            category=category,
            subcategory=subcategory,
        )
        return [Chunk(content=content, metadata=meta)]

    if not isinstance(data, dict):
        # Non-dict YAML (list, scalar) → single chunk
        meta = ChunkMetadata(
            source_file=filepath,
            source_dir=source_dir,
            file_type="yaml",
            section_header="(full file)",
            parent_header="",
            chunk_index=0,
            total_chunks_in_file=1,
            file_modified=file_modified,
            char_count=len(content),
            category=category,
            subcategory=subcategory,
        )
        return [Chunk(content=content, metadata=meta)]

    # Split at top-level keys
    sections: list[tuple[str, str, str]] = []  # (parent, header, content)
    for key, value in data.items():
        section_text = yaml.dump({key: value}, default_flow_style=False, sort_keys=False)
        if len(section_text) <= MAX_SIZE:
            sections.append(("", str(key), section_text))
        elif isinstance(value, dict):
            # Split at second-level keys
            for sub_key, sub_value in value.items():
                sub_text = yaml.dump(
                    {sub_key: sub_value}, default_flow_style=False, sort_keys=False
                )
                sections.append((str(key), f"{key}.{sub_key}", sub_text))
        else:
            sections.append(("", str(key), section_text))

    # Build chunks
    valid = [(p, h, c) for p, h, c in sections if len(c.strip()) >= MIN_SIZE]
    chunks: list[Chunk] = []

    for idx, (parent, header, body) in enumerate(valid):
        meta = ChunkMetadata(
            source_file=filepath,
            source_dir=source_dir,
            file_type="yaml",
            section_header=header,
            parent_header=parent,
            chunk_index=idx,
            total_chunks_in_file=len(valid),
            file_modified=file_modified,
            char_count=len(body),
            category=category,
            subcategory=subcategory,
        )
        chunks.append(Chunk(content=body, metadata=meta))

    return chunks


def _split_text_to_max(text: str, size: int = MAX_SIZE) -> list[str]:
    """Split text into pieces each <= size chars, preferring line boundaries.

    A single line longer than `size` is hard-cut. This is the MAX-size safety-net
    splitter: it must NOT mutate content, so whitespace-only pieces are preserved
    (only the structural splitters drop empties). Truly empty ("") pieces — which
    carry no characters — are dropped, but any piece containing whitespace is kept
    so an oversized, largely-whitespace chunk doesn't silently lose that content.
    """
    if len(text) <= size:
        return [text]
    pieces: list[str] = []
    cur: list[str] = []
    cur_len = 0
    for ln in text.split("\n"):
        if len(ln) > size:
            # Flush, then hard-cut the over-long line.
            if cur:
                pieces.append("\n".join(cur))
                cur, cur_len = [], 0
            for i in range(0, len(ln), size):
                pieces.append(ln[i:i + size])
            continue
        if cur_len + len(ln) + 1 > size and cur:
            pieces.append("\n".join(cur))
            cur, cur_len = [ln], len(ln) + 1
        else:
            cur.append(ln)
            cur_len += len(ln) + 1
    if cur:
        pieces.append("\n".join(cur))
    # Preserve whitespace-only pieces (no content loss); drop only truly empty "".
    return [p for p in pieces if p != ""]


def _enforce_max_size(chunks: list[Chunk]) -> list[Chunk]:
    """Guarantee no chunk exceeds MAX_SIZE chars (the embedder's context bound).

    Any oversized chunk — from invalid YAML, non-dict YAML, or an oversized scalar /
    second-level value that the structural chunkers emit whole — is split at line
    boundaries. chunk_index and total_chunks_in_file are recomputed across the file.
    """
    expanded: list[tuple[str, ChunkMetadata]] = []
    for ch in chunks:
        if len(ch.content) <= MAX_SIZE:
            expanded.append((ch.content, ch.metadata))
            continue
        # _split_text_to_max preserves whitespace-only pieces to avoid SILENT
        # mid-content loss, but a piece that is ENTIRELY whitespace after .strip()
        # carries no content — embedding it wastes Ollama calls and pollutes the
        # index with empty vectors. Drop fully-empty-after-strip parts here while
        # keeping internal whitespace within content-bearing parts.
        parts = [p for p in _split_text_to_max(ch.content) if p.strip()]
        for j, part in enumerate(parts):
            hdr = ch.metadata.section_header
            hdr = f"{hdr} (part {j + 1})" if hdr else f"(part {j + 1})"
            expanded.append((part, replace(ch.metadata, section_header=hdr, char_count=len(part))))

    total = len(expanded)
    return [
        Chunk(content=content, metadata=replace(md, chunk_index=i, total_chunks_in_file=total))
        for i, (content, md) in enumerate(expanded)
    ]


def chunk_file(filepath: str) -> list[Chunk]:
    """Chunk a file based on its type. Returns empty list if not indexable."""
    if not should_index(filepath):
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return []

    ext = Path(filepath).suffix.lower()
    if ext == ".md":
        chunks = chunk_markdown(filepath, content)
    elif ext in (".yaml", ".yml"):
        chunks = chunk_yaml(filepath, content)
    else:
        return []

    # Final safety net: no chunk may exceed MAX_SIZE (would 400 the embedder).
    return _enforce_max_size(chunks)
