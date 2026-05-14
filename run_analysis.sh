#!/bin/bash
# Full pipeline: extract Apple Music library → run analysis → output analysis.json
# Usage: ./run_analysis.sh [--skip-extract]
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ "$1" != "--skip-extract" ]]; then
  echo "Step 1: Extracting Apple Music library..."
  osascript -l JavaScript "$SCRIPT_DIR/extract_library.js"
else
  echo "Step 1: Skipping extraction (--skip-extract)"
fi

echo "Step 2: Running analysis..."
python3 "$SCRIPT_DIR/analyze_library.py"
