# Week 7 · Methods: Stroop forward, Hedge backward

**Name:**
**Date of class:** 21 October 2026
**Lab page:** https://kylemath.github.io/Psych302-305-KyleMathewson/methods.html

This folder should end up with: your edited `rt.html` (now a Stroop task),
`stroop-week07.csv`, this README, and `output/numbers.md` from
`analyze_stroop.py`. Individual work.

---

# Part 1 · Forward: Methods first, then the task

Write and commit this Methods **before** you change `rt.html`. Use numbers.

## Participants
Who took part (you). Age group is enough. Do not name classmates.

## Materials
Words, ink colours, response keys, screen and page used (`week07-methods/rt.html`).

## Procedure
One trial, in order, with timings: fixation (ms), word (until response?),
gap between trials (ms). Number of trials per condition, practice trials,
and how the order was randomised.

## Data handling
Which trials count (correct only?), and the exclusion rule in ms
(for example RT < 150 ms or > 2500 ms). Where the CSV lives.

## Decisions I had to invent while coding
Every choice the code forced on you that your Methods above did not answer.
One line each. (Then go back and add them to the Methods.)

## My result
Congruent mean RT, incongruent mean RT, Stroop effect (ms), number of errors.
CSV columns must include `condition`, `rt`, and `correct`.

---

# Part 2 · Backward: from Hedge's result to Hedge's Methods

Hedge, C., Powell, G., & Sumner, P. (2018). The reliability paradox: Why
robust cognitive tasks do not produce reliable individual differences.
*Behavior Research Methods, 50*(3), 1166–1186.
https://doi.org/10.3758/s13428-017-0935-1

## My guess (write before opening their Methods)
From the abstract and result alone: who, how many, what the task looked like,
how many trials, how long between sessions, which trials were thrown out.

## What I missed
After reading their Stroop Methods: three details you got wrong or did not
think of, and whether each one could change the result.

## Reanalysis
Run `python3 analyze_stroop.py --mine stroop-week07.csv` and paste
`output/numbers.md` here. Then one sentence each:
- Is the group Stroop effect robust?
- Is a person's Stroop effect stable from session 1 to session 2?
- Run it again with `--rule course`. What changed, and what does that say about
  writing exclusion rules in a Methods section?

---

## Copilot / agent disclosure
- **Used tonight:** yes / no
- **What I asked** (one sentence):
- **What I kept:**
- **What I changed:**

If no assistant was available, write “no Copilot tonight” and stop. Do not purchase a plan.
