# Agent notes

Course **35483** · Introduction to Computational Methods In Psychology · Fall 2026.

1. Read [HOWTO.md](HOWTO.md).
2. Reuse the Psych275 venv and Canvas token. Never copy the token into the student site or `student_template/`.
3. Week 0 form keys must stay stable. The pull parser depends on the labels in `templates/week0_form.txt`.
4. Rosters and `out/` stay here. Not on the public course pages.
5. `week0-grade` posts `complete` / `incomplete` only (username present). Do not invent a points scale.
5b. `week1-pull` harvests Canvas links only. Do not post Week 1 scores before the Tuesday due date.
6. `repos-mint` defaults to dry-run. `--apply` creates `kylemath/psych302-305-<username>` from `student_template/` for username + `repo_consent=yes` only. Never copy `pipeline/` or `.env`. Never force-push. If the repo already exists, skip create and only ensure the collaborator.
7. `repos-sync` defaults to dry-run. `--apply` adds missing `student_template/` files to existing repos only. Never overwrite. Never force-push.
