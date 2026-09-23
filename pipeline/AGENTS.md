# Agent notes

Course **35483** · Introduction to Computational Methods In Psychology · Fall 2026.

1. Read [HOWTO.md](HOWTO.md).
2. Reuse the Psych275 venv and Canvas token. Never copy the token into the student site or `student_template/`.
3. Week 0 form keys must stay stable. The pull parser depends on the labels in `templates/week0_form.txt`.
4. Rosters and `out/` stay here. Not on the public course pages.
5. `week0-grade` posts `complete` / `incomplete` only (username present). Do not invent a points scale.
5b. `week1-pull` harvests Canvas links. `week1-grade` posts the published 10-point Week 1 rubric after the Tuesday due date. Default dry-run.
5c. `week2-pull` harvests Canvas boxes and inspects private repos (`week02-rt/` or the older paths). `week2-grade` posts the published Week 2 exception rubric after the Tuesday due date. Default dry-run.
5d. `roster-pull` is the current class list. `repos-cleanup` archives (does not delete) private studio repos whose week0 owner is no longer enrolled. Default dry-run. Never archive `psych302-305-kylemath`. Unmatched names stay `review`.
5e. `week3-pull` harvests Canvas boxes and inspects each private `week03-inventory/` (items, structure, README, CSV). `week3-grade` posts the published Week 3 exception rubric after the Tuesday due date. Default dry-run. Late work is flagged for review, never auto-zeroed.
6. `repos-mint` defaults to dry-run. `--apply` creates `kylemath/psych302-305-<username>` from `student_template/` for username + `repo_consent=yes` only. Never copy `pipeline/` or `.env`. Never copy handbook teaching pages. Never force-push. If the repo already exists, skip create and only ensure the collaborator.
7. `repos-sync` defaults to dry-run. `--apply` adds missing `student_template/` files to existing repos only. Never overwrite. Never force-push. Do not replace student `rt.html` from the class site.
8. Week 4 starter is `student_template/week04-report/` (Python + Typst, not LaTeX). Do not sync student repos or rewrite the Canvas body until the instructor asks.
