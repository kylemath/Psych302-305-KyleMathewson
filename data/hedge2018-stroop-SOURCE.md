# Hedge, Powell & Sumner (2018) Stroop data

## Source

Hedge, C., Powell, G., & Sumner, P. (2018). The reliability paradox: Why robust cognitive tasks do not produce reliable individual differences. *Behavior Research Methods, 50*, 1166–1186. https://doi.org/10.3758/s13428-017-0935-1

- Data: OSF project https://osf.io/cwzds/ (public, created 2017-06-07)
- License: none is listed on the OSF project. The data is publicly shared for reuse, and the authors' README encourages others to analyse it. Cite the paper above when you use it.
- Downloaded 2026-10-21 from `Data/RawData/Study1-Stroop/` (94 files) and `Data/RawData/Study2-Stroop/` (120 files). Each file is `StudyS_PnStroopK.csv`, one file per participant *n* per session *K*.

## Original raw format

The files have no header and six columns: block, trial, unused (always 0), condition (0 = congruent, 1 = neutral, 2 = incongruent), correct (1/0), and RT in **seconds**. There are 720 trials per file: 5 blocks × 144 trials, which is 240 per condition.

## Task (from the paper)

The ink colours were red, blue, green and yellow, answered on the Z, X, N and M keys. Neutral words were lot, ship, cross and advice. The ISI was 750 ms. Each person did two sessions about three weeks apart.

## Columns in `hedge2018-stroop.csv`

| column | meaning |
|---|---|
| study | 1 or 2 |
| participant | participant number as in the source file name (anonymous; unique only *within* a study) |
| session | 1 or 2 |
| block | 1–5 |
| trial | trial within block, 1–144 |
| condition | congruent / neutral / incongruent |
| rt_ms | reaction time in milliseconds (source seconds × 1000) |
| correct | 1 = correct, 0 = error |

**Every trial is kept. No exclusions or trimming have been applied.**

## Counts

| study | session | rows | participants |
|---|---|---|---|
| 1 | 1 | 33,840 | 47 |
| 1 | 2 | 33,840 | 47 |
| 2 | 1 | 43,200 | 60 |
| 2 | 2 | 43,200 | 60 |

There are 154,080 rows in total. Missing IDs are people who did not come back for session 2: Study 1 IDs 6, 17 and 37, and Study 2 IDs 28 and 56. 1,066 trials have RT < 100 ms.

The paper's exclusions, which students will apply themselves:
- Participants below 60% accuracy in either session are dropped. The README names Study 2 participants 25, 34 and 38 (all tasks) and 54 (Stroop only).
- RTs < 100 ms or more than 3 MAD from each person's median are trimmed.

## Sanity check: session 1 group mean RT (ms)

These are simple means over correct trials with RT > 100 ms. No other trimming was applied and no participants were excluded.

| condition | Study 1 | Study 2 | both |
|---|---|---|---|
| congruent | 641.0 | 638.3 | 639.5 |
| neutral | 670.8 | 670.8 | 670.8 |
| incongruent | 721.6 | 728.9 | 725.7 |
