"""ACOS RAG Indexer — scan, chunk, embed, and store memory files.

Usage:
    python3 -m rag.indexer [--full] [--dry-run] [--stats]

Options:
    --full      Re-index all files (ignore mod-time cache)
    --dry-run   Show what would be indexed without making changes
    --stats     Show current index statistics and exit
"""

import argparse
import json
import os
import sys
from pathlib import Path

from . import chunker, db, embedder

# Directories to scan (relative to repo root)
SCAN_DIRS = ["memory", "learning-curve"]

BATCH_SIZE = 20


def discover_files(repo_root: str) -> list[str]:
    """Find all indexable files in the scan directories."""
    files = []
    for scan_dir in SCAN_DIRS:
        full_dir = os.path.join(repo_root, scan_dir)
        if not os.path.isdir(full_dir):
            continue
        for root, _dirs, filenames in os.walk(full_dir):
            for fname in filenames:
                filepath = os.path.join(root, fname)
                # Store as relative path from repo root
                relpath = os.path.relpath(filepath, repo_root)
                if chunker.should_index(relpath):
                    files.append(relpath)
    return sorted(files)


def get_file_modtimes(files: list[str], repo_root: str) -> dict[str, str]:
    """Get modification times for a list of files."""
    modtimes = {}
    for f in files:
        fullpath = os.path.join(repo_root, f)
        try:
            mtime = os.path.getmtime(fullpath)
            modtimes[f] = str(mtime)
        except OSError:
            pass
    return modtimes


def show_stats(repo_root: str) -> None:
    """Show current index statistics."""
    meta = db.load_index_meta()
    indexed_files = list(meta.keys())
    all_files = discover_files(repo_root)

    try:
        database = db.get_db()
        table = db.get_or_create_table(database)
        total_chunks = table.count_rows()
    except Exception as e:
        total_chunks = f"error: {e}"

    stats = {
        "indexed_files": len(indexed_files),
        "total_discoverable_files": len(all_files),
        "total_chunks": total_chunks,
        "indexed_file_list": indexed_files,
    }
    print(json.dumps(stats, indent=2))


def run_index(full: bool = False, dry_run: bool = False) -> dict:
    """Run the indexing pipeline.

    Returns a stats dict with results.
    """
    repo_root = os.getcwd()
    all_files = discover_files(repo_root)
    current_modtimes = get_file_modtimes(all_files, repo_root)

    # Load cached mod-times
    if full:
        cached_modtimes: dict = {}
    else:
        cached_modtimes = db.load_index_meta()

    # Determine which files need re-indexing
    files_to_index = []
    for f in all_files:
        if f not in cached_modtimes or cached_modtimes.get(f) != current_modtimes.get(f):
            files_to_index.append(f)

    # Determine deleted files (in cache but no longer on disk)
    files_to_remove = [f for f in cached_modtimes if f not in current_modtimes]

    stats = {
        "total_files_found": len(all_files),
        "files_to_index": len(files_to_index),
        "files_to_remove": len(files_to_remove),
        "chunks_created": 0,
        "errors": [],
    }

    if dry_run:
        stats["dry_run"] = True
        stats["would_index"] = files_to_index
        stats["would_remove"] = files_to_remove
        print(json.dumps(stats, indent=2))
        return stats

    if not files_to_index and not files_to_remove:
        stats["message"] = "Index is up to date"
        print(json.dumps(stats, indent=2))
        return stats

    # Check Ollama availability
    if not embedder.is_ollama_available():
        stats["errors"].append("Ollama is not available or nomic-embed-text not installed")
        print(json.dumps(stats, indent=2))
        sys.exit(2)

    # Open database
    database = db.get_db()
    table = db.get_or_create_table(database)

    # Remove chunks for deleted files
    if files_to_remove:
        db.delete_chunks_for_files(table, files_to_remove)
        for f in files_to_remove:
            cached_modtimes.pop(f, None)

    # Process files in batches
    total_chunks = 0
    for filepath in files_to_index:
        fullpath = os.path.join(repo_root, filepath)
        try:
            chunks = chunker.chunk_file(fullpath)
            if not chunks:
                # File passed should_index but produced no chunks
                cached_modtimes[filepath] = current_modtimes[filepath]
                continue

            # Embed in batches
            texts = [c.content for c in chunks]
            all_vectors = []
            for i in range(0, len(texts), BATCH_SIZE):
                batch = texts[i : i + BATCH_SIZE]
                vectors = embedder.embed_texts(batch)
                all_vectors.extend(vectors)

            # Upsert to DB
            inserted = db.upsert_chunks(table, chunks, all_vectors)
            total_chunks += inserted

            # Update cached modtime
            cached_modtimes[filepath] = current_modtimes[filepath]

        except embedder.EmbeddingError as e:
            stats["errors"].append(f"{filepath}: embedding error: {e}")
        except Exception as e:
            stats["errors"].append(f"{filepath}: {e}")

    # Save updated metadata
    db.save_index_meta(cached_modtimes)

    stats["chunks_created"] = total_chunks
    print(json.dumps(stats, indent=2))
    return stats


def main():
    parser = argparse.ArgumentParser(description="ACOS RAG Indexer")
    parser.add_argument("--full", action="store_true", help="Re-index all files")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be indexed"
    )
    parser.add_argument(
        "--stats", action="store_true", help="Show current index stats"
    )
    args = parser.parse_args()

    if args.stats:
        show_stats(os.getcwd())
        sys.exit(0)

    result = run_index(full=args.full, dry_run=args.dry_run)
    if result.get("errors"):
        sys.exit(2)


if __name__ == "__main__":
    main()
