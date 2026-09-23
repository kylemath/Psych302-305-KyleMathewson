# Week 4 · research report

**Name:**
**Date of class:** 23 September 2026
**Tool / example:** Python analyzes the CSV and draws a figure; Typst compiles the PDF

This folder is a report pipeline, not a form. Write the prediction in
`main.typ` *before* you run the script. Do not type a mean by hand.

1. Install Typst if `typst --version` fails:
   https://kylemath.github.io/Psych302-305-KyleMathewson/workflow.html#typst
2. First build, to prove the tools work:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   bash build.sh sample-rt.csv
   ```

   Windows (PowerShell): `py -3 -m venv .venv`, then
   `.\.venv\Scripts\Activate.ps1`, then
   `py -3 -m pip install -r requirements.txt`, then
   `py -3 scripts/summarize.py --csv sample-rt.csv --out output --report README.md`
   and `typst compile main.typ output/main.pdf`.
3. Open `output/main.pdf`. The Results table and figure must come from the
   script (`output/numbers.typ` and `output/figure.png`), not a number you
   typed into `main.typ`.
4. Point the script at **your** Week 2 or Week 3 CSV
   (`../week02-rt/YOUR.csv` or `../week03-inventory/YOUR.csv`) and rebuild.
5. Change one thing (exclusion bounds, the figure, a second descriptive,
   or a sentence in `main.typ`). Rebuild. The PDF must change.
6. Finish this file.

## Prediction
What you wrote in `main.typ` before the first build on your own CSV.

## Results
<!-- begin generated -->
Run `bash build.sh YOURFILE.csv` from this folder. This block will be replaced.
<!-- end generated -->

## Limitation
One reason the generated number can lie. Include n.

## Iteration
What you changed after the first build, and what changed in the PDF.

## Copilot / agent disclosure
- **Used tonight:** yes / no
- **What I asked** (one sentence):
- **What I kept:**
- **What I changed:**

If no assistant was available, write “no Copilot tonight” and stop. Do not purchase a plan.
