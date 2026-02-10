#!/bin/bash
# ACOS RAG Querier — shell wrapper
# Activates the Python venv and invokes the querier module.
#
# Usage: bash .claude/scripts/rag-query.sh --query "search text" [--top-k 10] [--category X]
# Exit 0 = success, Exit 2 = failure (JSON error with "fallback": true on stdout)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_DIR="$SCRIPT_DIR/rag/.venv"

# Check venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo '{"error": "RAG venv not found. Run: bash .claude/scripts/rag/setup.sh", "results": [], "total_results": 0, "fallback": true}'
    exit 2
fi

# Activate venv and run from repo root
source "$VENV_DIR/bin/activate"
cd "$REPO_ROOT"
export PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}"
python3 -m rag.querier "$@"
