#!/usr/bin/env bash
# One pass of the report loop. From this folder (e.g. week04-report/):
#   bash build.sh yourfile.csv
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

CSV="${1:-}"
if [[ -z "$CSV" ]]; then
  echo "usage: bash build.sh yourfile.csv" >&2
  exit 1
fi

if [[ ! -x .venv/bin/python && ! -x .venv/Scripts/python.exe ]]; then
  if command -v python3 >/dev/null 2>&1; then
    python3 -m venv .venv
  else
    py -3 -m venv .venv
  fi
fi

if [[ -x .venv/bin/python ]]; then
  PY=.venv/bin/python
else
  PY=.venv/Scripts/python.exe
fi

"$PY" -m pip install -q -r requirements.txt
"$PY" scripts/summarize.py --csv "$CSV" --out output --report README.md

if command -v typst >/dev/null 2>&1; then
  mkdir -p output
  typst compile main.typ output/main.pdf
  echo "wrote output/main.pdf"
else
  echo "typst not found. Numbers and the figure are written; the PDF is still required."
  echo "macOS: brew install typst"
  echo "Windows: winget install --id Typst.Typst"
  echo "Or a binary from https://github.com/typst/typst/releases"
  echo "Then: typst compile main.typ output/main.pdf"
fi
