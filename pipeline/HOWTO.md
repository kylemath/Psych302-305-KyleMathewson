# PSYCH 302 / 305 Canvas pipeline

Private instructor tool. Token lives in `Psych275_Instructor/pipeline/.env` (same Canvas account). This folder overrides the course id to **35483**.

```bash
cd /Users/kylemathewson/Teaching/PsychCompute302-305/pipeline
source /Users/kylemathewson/Teaching/Psych275_Instructor/pipeline/.venv/bin/activate
python studio_pipeline.py courses
python studio_pipeline.py week0-create
python studio_pipeline.py modules-create
# after students submit:
python studio_pipeline.py week0-pull
python studio_pipeline.py week0-grade          # complete/incomplete from parsed username
python studio_pipeline.py week1-pull           # harvest Week 1 Canvas links; does not grade
python studio_pipeline.py repos-mint           # dry-run plan (default)
python studio_pipeline.py repos-mint --apply   # create private repos + add collaborators
python studio_pipeline.py repos-sync           # dry-run: missing template files on existing repos
python studio_pipeline.py repos-sync --apply   # add missing files only; never overwrite or force-push
python studio_pipeline.py modules-create       # Canvas modules + weekly assignment bodies
```

`week0-pull` writes `out/week0_roster.json`: Canvas user ↔ GitHub username, Education status, repo consent.

`week0-grade` PUTs Canvas `complete` / `incomplete` only. Complete = parsed GitHub username present and non-empty. Do not invent points. Assignment is `pass_fail` and omitted from the final grade.

`repos-mint` copies `student_template/` (lab-notes, `report/`, `papers/`, project checklists, `.devcontainer`, short README). It never copies `pipeline/` or `.env`. Repos are `kylemath/psych302-305-<github_username>`, private. The student is added as a `push` collaborator (write, not admin); kylemath stays owner/admin. Mint only when the username parses **and** `repo_consent=yes`. Default is dry-run. Same-name repos are not overwritten and are never force-pushed; an existing repo only gets a collaborator check.

`repos-sync` is for repos that already exist (for example after a later template addition such as `report/`). Default is dry-run. `--apply` clones each existing consented repo, copies only files that are still missing, commits, and does a regular `git push`. It never overwrites a file the student already has and never force-pushes.

To the agent: **`plant week0`** means create (or confirm) the assignment and announcement. **`pull week0`** means harvest usernames. **`grade week0`** means complete/incomplete. **`pull week1`** means harvest the four GitHub links from Canvas (do not invent scores). **`mint repos`** means dry-run first, then `--apply` for eligible students only. **`sync repos`** means dry-run first, then `--apply` to add missing template files only.

Week 1 is due Tuesday 17:00. Do not post Week 1 grades before the due date. GitHub forks/PRs are evidence of work; Canvas paste is the official submission.
