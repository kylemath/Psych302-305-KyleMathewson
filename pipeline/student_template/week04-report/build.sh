#!/usr/bin/env bash
set -e

CSV="$1"

python3 -m pip install -r requirements.txt
python3 scripts/summarize.py --csv "$CSV" --out output

mkdir -p output
typst compile main.typ output/main.pdf

echo "Wrote output/main.pdf"
