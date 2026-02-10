"""LanceDB connection, upsert, and search for the ACOS RAG system."""

import json
import os
from pathlib import Path
from typing import Optional

import lancedb
import pyarrow as pa

from .embedder import EMBED_DIM
from .models import Chunk, SearchResult

# Paths
DEFAULT_DB_PATH = ".acos/vectordb/lancedb"
INDEX_META_PATH = ".acos/vectordb/index-meta.json"
TABLE_NAME = "memory_chunks"

# Schema for the LanceDB table
SCHEMA = pa.schema(
    [
        pa.field("chunk_id", pa.string()),
        pa.field("content", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), EMBED_DIM)),
        pa.field("source_file", pa.string()),
        pa.field("source_dir", pa.string()),
        pa.field("file_type", pa.string()),
        pa.field("section_header", pa.string()),
        pa.field("parent_header", pa.string()),
        pa.field("chunk_index", pa.int32()),
        pa.field("total_chunks_in_file", pa.int32()),
        pa.field("file_modified", pa.string()),
        pa.field("char_count", pa.int32()),
        pa.field("category", pa.string()),
        pa.field("subcategory", pa.string()),
    ]
)


def _resolve_path(path: str) -> str:
    """Resolve a path relative to the git repo root (cwd)."""
    return str(Path(path).resolve())


def get_db(db_path: str = DEFAULT_DB_PATH) -> lancedb.DBConnection:
    """Open or create the LanceDB database."""
    resolved = _resolve_path(db_path)
    os.makedirs(resolved, exist_ok=True)
    return lancedb.connect(resolved)


def get_or_create_table(
    db: lancedb.DBConnection,
) -> lancedb.table.Table:
    """Get the memory_chunks table, creating it if needed."""
    if TABLE_NAME in db.table_names():
        return db.open_table(TABLE_NAME)
    return db.create_table(TABLE_NAME, schema=SCHEMA)


def chunks_to_records(chunks: list[Chunk], vectors: list[list[float]]) -> list[dict]:
    """Convert Chunk objects + vectors into dicts suitable for LanceDB insert."""
    records = []
    for chunk, vector in zip(chunks, vectors):
        m = chunk.metadata
        records.append(
            {
                "chunk_id": chunk.chunk_id,
                "content": chunk.content,
                "vector": vector,
                "source_file": m.source_file,
                "source_dir": m.source_dir,
                "file_type": m.file_type,
                "section_header": m.section_header,
                "parent_header": m.parent_header,
                "chunk_index": m.chunk_index,
                "total_chunks_in_file": m.total_chunks_in_file,
                "file_modified": m.file_modified,
                "char_count": m.char_count,
                "category": m.category,
                "subcategory": m.subcategory,
            }
        )
    return records


def upsert_chunks(
    table: lancedb.table.Table,
    chunks: list[Chunk],
    vectors: list[list[float]],
) -> int:
    """Upsert chunks into the table.

    Deletes existing chunks for the same source files, then inserts new ones.
    Returns the number of chunks inserted.
    """
    if not chunks:
        return 0

    # Determine which source files are being updated
    source_files = list({c.metadata.source_file for c in chunks})

    # Delete old chunks for those files
    for sf in source_files:
        try:
            table.delete(f'source_file = "{sf}"')
        except Exception:
            pass  # Table might be empty or file not present

    # Insert new chunks
    records = chunks_to_records(chunks, vectors)
    table.add(records)
    return len(records)


def delete_chunks_for_files(
    table: lancedb.table.Table,
    filepaths: list[str],
) -> int:
    """Remove all chunks for the given source files. Returns count removed."""
    removed = 0
    for fp in filepaths:
        try:
            table.delete(f'source_file = "{fp}"')
            removed += 1
        except Exception:
            pass
    return removed


def search(
    table: lancedb.table.Table,
    query_vector: list[float],
    top_k: int = 10,
    category: Optional[str] = None,
    min_score: float = 0.0,
) -> list[SearchResult]:
    """Search the table by vector similarity.

    Returns SearchResult objects sorted by descending relevance.
    """
    query = table.search(query_vector).limit(top_k * 2)  # Over-fetch for filtering

    if category:
        query = query.where(f'category = "{category}"')

    results_table = query.to_arrow()

    if results_table.num_rows == 0:
        return []

    search_results = []
    for i in range(results_table.num_rows):
        # LanceDB returns _distance (L2); convert to similarity score
        # For normalized vectors, similarity ≈ 1 - (distance² / 2)
        distance = results_table.column("_distance")[i].as_py()
        score = max(0.0, 1.0 - distance / 2.0)

        if score < min_score:
            continue

        search_results.append(
            SearchResult(
                path=results_table.column("source_file")[i].as_py(),
                section=results_table.column("section_header")[i].as_py(),
                excerpt=results_table.column("content")[i].as_py()[:500],
                score=round(score, 4),
                category=results_table.column("category")[i].as_py(),
                file_modified=results_table.column("file_modified")[i].as_py(),
            )
        )

    # Sort by score descending, truncate to top_k
    search_results.sort(key=lambda r: r.score, reverse=True)
    return search_results[:top_k]


# --- Index metadata management ---


def load_index_meta(meta_path: str = INDEX_META_PATH) -> dict:
    """Load the index metadata (file mod-times tracking)."""
    resolved = _resolve_path(meta_path)
    if os.path.exists(resolved):
        with open(resolved, "r") as f:
            return json.load(f)
    return {}


def save_index_meta(meta: dict, meta_path: str = INDEX_META_PATH) -> None:
    """Save the index metadata."""
    resolved = _resolve_path(meta_path)
    os.makedirs(os.path.dirname(resolved), exist_ok=True)
    with open(resolved, "w") as f:
        json.dump(meta, f, indent=2)
