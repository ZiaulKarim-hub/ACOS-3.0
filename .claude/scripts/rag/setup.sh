#!/bin/bash
# ACOS RAG Infrastructure Setup
# One-time bootstrap: creates venv, installs deps, checks Ollama, creates data dirs
# Run from repo root: bash .claude/scripts/rag/setup.sh
# Exit 0 = success, Exit 2 = failure

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"
VECTORDB_DIR="$REPO_ROOT/.acos/vectordb/lancedb"

echo "=== ACOS RAG Setup ==="
echo "Script dir: $SCRIPT_DIR"
echo "Repo root:  $REPO_ROOT"
echo ""

# Step 1: Create Python virtual environment
echo "--- Step 1: Python virtual environment ---"
if [ -d "$VENV_DIR" ]; then
    echo "  Venv already exists at $VENV_DIR"
else
    echo "  Creating venv at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    echo "  Venv created."
fi

# Activate venv
source "$VENV_DIR/bin/activate"
echo "  Python: $(python3 --version)"
echo ""

# Step 2: Install dependencies
echo "--- Step 2: Install dependencies ---"
pip install --quiet --upgrade pip
pip install --quiet -r "$REQUIREMENTS"
echo "  Dependencies installed."
echo ""

# Step 3: Verify key imports
echo "--- Step 3: Verify imports ---"
python3 -c "import lancedb; print(f'  lancedb {lancedb.__version__}')" || {
    echo "  ERROR: lancedb import failed."
    echo "  If this is a Python version issue, try: brew install python@3.12"
    exit 2
}
python3 -c "import ollama; print(f'  ollama client OK')" || {
    echo "  ERROR: ollama Python client import failed."
    exit 2
}
python3 -c "import pyarrow; print(f'  pyarrow {pyarrow.__version__}')" || {
    echo "  ERROR: pyarrow import failed."
    exit 2
}
echo ""

# Step 4: Check Ollama availability
echo "--- Step 4: Check Ollama ---"
if command -v ollama &>/dev/null; then
    echo "  Ollama binary: found ($(command -v ollama))"
else
    echo "  WARNING: Ollama not found in PATH."
    echo "  Install: brew install ollama"
    echo "  RAG will fall back to keyword search without it."
fi

# Check if Ollama server is running
if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "  Ollama server: running"

    # Check for nomic-embed-text model
    if curl -sf http://localhost:11434/api/tags | python3 -c "
import sys, json
data = json.load(sys.stdin)
models = [m['name'] for m in data.get('models', [])]
if any('nomic-embed-text' in m for m in models):
    print('  nomic-embed-text: installed')
else:
    print('  WARNING: nomic-embed-text not found.')
    print('  Run: ollama pull nomic-embed-text')
" 2>/dev/null; then
        true
    fi
else
    echo "  WARNING: Ollama server not running."
    echo "  Start: ollama serve"
    echo "  Then: ollama pull nomic-embed-text"
fi
echo ""

# Step 5: Create data directories
echo "--- Step 5: Data directories ---"
mkdir -p "$VECTORDB_DIR"
echo "  Created: $VECTORDB_DIR"
mkdir -p "$REPO_ROOT/.acos/vectordb"
echo ""

echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Ensure Ollama is running: ollama serve"
echo "  2. Pull embedding model: ollama pull nomic-embed-text"
echo "  3. Index memory files: bash .claude/scripts/rag-index.sh --full"
