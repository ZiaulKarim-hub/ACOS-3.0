"""ACOS RAG Querier — embed a query and search the vector database.

Usage:
    python3 -m rag.querier --query "search text" [--top-k 10] [--category X] [--min-score 0.3]
    echo '{"query": "text"}' | python3 -m rag.querier --stdin
"""

import argparse
import json
import sys
from collections import defaultdict

from . import db, embedder
from .models import SearchResult


def deduplicate(results: list[SearchResult], max_per_file: int = 3) -> list[SearchResult]:
    """Limit to max_per_file chunks per source file, keeping highest-scoring."""
    file_counts: dict[str, int] = defaultdict(int)
    deduped = []
    for r in results:
        if file_counts[r.path] < max_per_file:
            deduped.append(r)
            file_counts[r.path] += 1
    return deduped


def format_output(results: list[SearchResult]) -> dict:
    """Format results into the JSON structure expected by the memory-agent."""
    return {
        "results": [
            {
                "path": r.path,
                "relevance": r.score,
                "excerpt": r.excerpt,
                "section": r.section,
                "category": r.category,
                "file_modified": r.file_modified,
                "full_content_available": r.full_content_available,
            }
            for r in results
        ],
        "total_results": len(results),
    }


def format_error(message: str) -> dict:
    """Format an error response with fallback flag."""
    return {
        "error": message,
        "results": [],
        "total_results": 0,
        "fallback": True,
    }


def run_query(
    query: str,
    top_k: int = 10,
    category: str | None = None,
    min_score: float = 0.0,
) -> dict:
    """Execute a semantic search query.

    Returns the formatted JSON output dict.
    """
    # Check infrastructure
    if not embedder.is_ollama_available():
        return format_error("Ollama is not available or nomic-embed-text not installed")

    # Embed the query
    try:
        query_vector = embedder.embed_single(query)
    except embedder.EmbeddingError as e:
        return format_error(f"Embedding failed: {e}")

    # Search the database
    try:
        database = db.get_db()
        table = db.get_or_create_table(database)
        results = db.search(
            table,
            query_vector,
            top_k=top_k * 2,  # Over-fetch before dedup
            category=category,
            min_score=min_score,
        )
    except Exception as e:
        return format_error(f"Database search failed: {e}")

    # Deduplicate and limit
    results = deduplicate(results, max_per_file=3)[:top_k]

    return format_output(results)


def main():
    parser = argparse.ArgumentParser(description="ACOS RAG Querier")
    parser.add_argument("--query", type=str, help="Search query text")
    parser.add_argument("--top-k", type=int, default=10, help="Number of results")
    parser.add_argument("--category", type=str, default=None, help="Filter by category")
    parser.add_argument(
        "--min-score", type=float, default=0.0, help="Minimum relevance score"
    )
    parser.add_argument(
        "--stdin", action="store_true", help="Read JSON input from stdin"
    )
    args = parser.parse_args()

    # Get query from args or stdin
    if args.stdin:
        try:
            data = json.load(sys.stdin)
            query = data["query"]
            top_k = data.get("top_k", args.top_k)
            category = data.get("category", args.category)
            min_score = data.get("min_score", args.min_score)
        except (json.JSONDecodeError, KeyError) as e:
            print(json.dumps(format_error(f"Invalid stdin JSON: {e}")))
            sys.exit(2)
    elif args.query:
        query = args.query
        top_k = args.top_k
        category = args.category
        min_score = args.min_score
    else:
        print(json.dumps(format_error("No query provided. Use --query or --stdin")))
        sys.exit(2)

    result = run_query(query, top_k=top_k, category=category, min_score=min_score)
    print(json.dumps(result, indent=2))

    if result.get("fallback"):
        sys.exit(2)


if __name__ == "__main__":
    main()
