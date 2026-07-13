#!/usr/bin/env bash
# Launch the Coronal Aging spatial viewer (macOS / Linux).
# Usage: ./run.sh [port] [--no-open]
# Windows users: double-click run.bat, or run `python serve.py`.
set -e
cd "$(dirname "$0")"
if command -v python3 >/dev/null 2>&1; then PY=python3
elif command -v python >/dev/null 2>&1; then PY=python
else echo "Python 3 not found on PATH." >&2; exit 1
fi
exec "$PY" serve.py "$@"
