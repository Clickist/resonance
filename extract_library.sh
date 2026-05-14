#!/bin/bash
# Re-extract Apple Music library to library.json
# Usage: ./extract_library.sh
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
osascript -l JavaScript "$SCRIPT_DIR/extract_library.js"
