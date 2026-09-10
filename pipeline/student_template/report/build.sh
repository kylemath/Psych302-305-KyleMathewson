#!/usr/bin/env bash
# One pass of the report loop. From the report/ folder:
#   bash build.sh ../data/yourfile.csv
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

CSV="${1:-}"
if [[ -z "$CSV" ]]; then
  echo "usage: bash build.sh ../data/yourfile.csv" >&2
  exit 1
fi

if [[ -x .venv/bin/python ]]; then
  PY=.venv/bin/python
elif [[ -x .venv/Scripts/python.exe ]]; then
  PY=.venv/Scripts/python.exe
else
  PY=python3
fi

"$PY" scripts/summarize.py --csv "$CSV" --out output --report REPORT.md

if command -v pdflatex >/dev/null 2>&1; then
  mkdir -p output
  pdflatex -interaction=nonstopmode -halt-on-error -output-directory output main.tex
  echo "wrote output/main.pdf"
else
  echo "pdflatex not found. Markdown + .tex sources are enough for tonight."
fi
