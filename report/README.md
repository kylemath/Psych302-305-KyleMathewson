# Research report pipeline

Public copy of the Week 4 starter. The graded copy lives in your private
repo as `week04-report/`.

The loop is: edit prose or the script → run the script → compile the Typst
paper → read the PDF → change something → run again. Do not type a mean by
hand.

```
week04-report/
  README.md              # the lab note you paste on Canvas
  main.typ               # the paper you compile
  scripts/summarize.py   # reads a CSV, writes numbers and a figure
  requirements.txt       # matplotlib, installed only in .venv
  output/numbers.typ     # generated; do not edit
  output/figure.png      # generated; do not edit
  output/main.pdf        # compiled; this is the product
  build.sh               # one command for the loop
  sample-rt.csv          # first build only; then use your own CSV
```

## Run once

From `week04-report/` in the VS Code terminal:

```bash
python3 -m venv .venv
source .venv/bin/activate
bash build.sh sample-rt.csv
```

Windows (VS Code PowerShell):

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -3 -m pip install -r requirements.txt
py -3 scripts/summarize.py --csv sample-rt.csv --out output --report README.md
typst compile main.typ output/main.pdf
```

`summarize.py` needs matplotlib. Install it only in the local `.venv`
(`pip install -r requirements.txt`). Do not install packages on the system Python.

If `typst` is missing, install it
([workflow.html#typst](../workflow.html#typst)) and compile again. The PDF
is required.

## The loop

1. Write a prediction in `main.typ` *before* you look at the generated mean.
2. Run the script on **your** Week 2 or Week 3 CSV.
3. Open `output/main.pdf`. If n or the mean looks wrong, fix the CSV path or
   the exclusion rule in the script — do not edit `output/numbers.typ`.
4. Change one sentence of prose, or one line of the script.
5. Run again. Note what changed in the PDF.

Keep the week-4 files in `week04-report/`. Do not copy a second note into
`lab-notes/`.
