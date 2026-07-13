#!/usr/bin/env bash
# Launch the Coronal Aging spatial viewer.
# Usage: ./run.sh [port]
set -e
cd "$(dirname "$0")"
PORT="${1:-8777}"
# Regenerate data bundle if missing.
if [ ! -f data/manifest.json ]; then
  echo "Data bundle missing — running export…"
  python3 export_data.py
fi
echo "Viewer at → http://localhost:${PORT}/index.html   (Ctrl-C to stop)"
python3 -m http.server "$PORT"
