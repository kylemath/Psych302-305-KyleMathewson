# PSYCH 302 / 305 Canvas pipeline

Private instructor tool. Token lives in `Psych275_Instructor/pipeline/.env` (same Canvas account). This folder overrides the course id to **35483**.

```bash
cd /Users/fulkanjou/Psych302-305-KyleMathewson/pipeline
# also valid: /Users/kylemathewson/Teaching/PsychCompute302-305/pipeline
source /Users/fulkanjou/Psych275_Instructor/pipeline/.venv/bin/activate
python studio_pipeline.py courses
python studio_pipeline.py week0-create
python studio_pipeline.py modules-create
# after students submit:
python studio_pipeline.py week0-pull
python studio_pipeline.py week0-grade          # complete/incomplete from parsed username
python studio_pipeline.py roster-pull          # current vs former Canvas enrollments
python studio_pipeline.py week1-pull           # harvest Week 1 Canvas links
python studio_pipeline.py week1-grade          # dry-run rubric scores from harvested links
python studio_pipeline.py week1-grade --apply  # PUT Week 1 scores (due date has passed)
python studio_pipeline.py week2-pull           # harvest Week 2 Canvas boxes + inspect private repos
python studio_pipeline.py week2-grade          # dry-run rubric scores (new week02-rt/ or old paths)
python studio_pipeline.py week2-grade --apply
python studio_pipeline.py week3-pull           # harvest Week 3 Canvas boxes + inspect week03-inventory/
python studio_pipeline.py week3-grade          # dry-run Week 3 exception rubric
python studio_pipeline.py week3-grade --apply
python studio_pipeline.py repos-mint           # dry-run plan (default)
python studio_pipeline.py repos-mint --apply   # create private repos + add collaborators
python studio_pipeline.py repos-sync           # dry-run: missing template files on existing repos
python studio_pipeline.py repos-sync --apply   # add missing files only; never overwrite or force-push
python studio_pipeline.py repos-replace --path README.md   # dry-run overwrite listed template files
python studio_pipeline.py repos-replace --path README.md --apply
python studio_pipeline.py repos-cleanup        # dry-run: archive repos whose week0 owner dropped
python studio_pipeline.py repos-cleanup --apply
python studio_pipeline.py modules-create       # Canvas modules + weekly assignment bodies
python studio_pipeline.py assignments-update   # rewrite weekly bodies only; no student email
python studio_pipeline.py assignments-update --from-week 3   # weeks 3+ and Canvas intro/schedule pages
python studio_pipeline.py assignments-update --notify-week 3   # same, email only Week 3
```

`week0-pull` writes `out/week0_roster.json`: Canvas user ↔ GitHub username, Education status, repo consent.

`roster-pull` writes `out/roster.json`: current vs former student enrollments. Use this as the class list. Former rows are the cleanup candidates.

`week0-grade` PUTs Canvas `complete` / `incomplete` only. Complete = parsed GitHub username present and non-empty. Do not invent points. Assignment is `pass_fail` and omitted from the final grade.

`week1-grade` / `week2-grade` PUT the published 10-point exception rubrics after the Tuesday due date. Default is dry-run. Week 1 checks that the four GitHub links open. Week 2 accepts `week02-rt/` or the older `lab-notes/` + `rt/` + `data/` paths. Do not invent a different scale. `--force` overwrites a score that is already posted.

`week3-grade` scores the Week 3 exception rubric from `week03-inventory/`: all ten `ITEMS` texts differ from the template (3; 5–9 rewritten is 2, 1–4 is 1), 5 domains × 2 items with one `reverse: 1` each plus `inventory.css` beside it (2), filled `README.md` + a CSV (2), prediction (1), tedium sentence (1), disclosure (1). Items moved into a local `<script src="inventory.js">` are followed. Late Canvas submissions, commits after the due date, and edits below `STOP EDITING HERE` are flagged `REVIEW`, not auto-deducted.

`repos-cleanup` archives (does not delete) `kylemath/psych302-305-<username>` when the week0 owner is no longer enrolled. Keeps the instructor demo. Default is dry-run. Unmatched repo names are `review`, never auto-archived.

`repos-mint` copies the whole `student_template/` tree (root README plus every `weekNN-*/` folder already in the template — currently `week02-rt/`, `week03-inventory/`, `week04-report/`, `week10-project/`). Per-student copies of a personalized page (for example `week03-inventory/inventory.html` + `inventory.css`) do go in the template; the live handbook page (`rt.html`, `inventory.html`) is the class demo only and is never itself copied. It never copies `pipeline/` or `.env`. Repos are `kylemath/psych302-305-<github_username>`, private. The student is added as a `push` collaborator (write, not admin); kylemath stays owner/admin. Mint only when the username parses **and** `repo_consent=yes`. Default is dry-run. Same-name repos are not overwritten and are never force-pushed.

**Do not** `repos-replace` teaching HTML into student repos. Instruments live on GitHub Pages. Student repos hold that week’s `README.md`, CSV, and any page the student wrote.

`repos-sync` is for repos that already exist. Default is dry-run. `--apply` clones each existing consented repo, copies only files that are still missing, commits, and does a regular `git push`. It never overwrites a file the student already has and never force-pushes. It will not delete leftover `lab-notes/` / `report/` folders from Weeks 0–2.

Instructor demo (Kyle as student): `kylemath/psych302-305-kylemath`, local clone `/Users/kylemathewson/Teaching/psych302-305-kylemath`. Maintain it the same way students maintain theirs.

To the agent: **`plant week0`** means create (or confirm) the assignment and announcement. **`pull week0`** means harvest usernames. **`grade week0`** means complete/incomplete. **`pull roster`** means current vs former enrollments. **`pull week1`** means harvest the four GitHub links from Canvas. **`pull week3`** means `week3-pull`. **`grade week1`** / **`grade week2`** / **`grade week3`** mean dry-run the published rubric, then `--apply` after the Tuesday due date (do not invent a scale). **`mint repos`** means dry-run first, then `--apply` for eligible students only. **`sync repos`** means dry-run first, then `--apply` to add missing template files only. **`cleanup repos`** means dry-run first, then `--apply` to archive dropped students’ private repos only.

Students work in **VS Code on their laptops** (GitHub Codespaces is not used). After a handbook push, rewrite Canvas weeklies from Week 3 onward with `assignments-update --from-week 3` (no student email unless `--notify-week`).
