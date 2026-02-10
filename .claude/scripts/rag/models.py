"""Data models for the ACOS RAG system."""

import hashlib
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ChunkMetadata:
    """Metadata attached to each text chunk."""

    source_file: str
    source_dir: str
    file_type: str  # "md" or "yaml"
    section_header: str
    parent_header: str
    chunk_index: int
    total_chunks_in_file: int
    file_modified: str  # ISO 8601 timestamp
    char_count: int
    category: str  # e.g., "decision", "handoff", "source-of-truth"
    subcategory: str  # e.g., "slice-reviews", "architect-to-developer"


@dataclass
class Chunk:
    """A text chunk with metadata and a content-derived ID."""

    content: str
    metadata: ChunkMetadata
    chunk_id: str = field(init=False)

    def __post_init__(self):
        # Deterministic ID from source file + chunk index
        raw = f"{self.metadata.source_file}::{self.metadata.chunk_index}"
        self.chunk_id = hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass
class SearchResult:
    """A single search result returned by the querier."""

    path: str
    section: str
    excerpt: str
    score: float
    category: str
    file_modified: str
    full_content_available: bool = True
